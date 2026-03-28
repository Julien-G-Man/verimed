# Architecture — VeriMed

## Overview

VeriMed is a pipeline-based web application. The core idea is simple: extract signals from images, compare them against trusted reference data, score consistency deterministically, then use an LLM only to produce a human-readable explanation.

The LLM is **not** the truth engine. It is the communication layer.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│                     FRONTEND                        │
│  Next.js (mobile-first)                             │
│  - Image upload UI (3 slots: front, back, barcode)  │
│  - Progress / loading state                         │
│  - Result card: risk level, reasons, explanation    │
│  - Extracted fields preview                         │
│  - Embedded follow-up assistant panel               │
└───────────────────┬─────────────────────────────────┘
                    │ HTTP multipart/form-data
                    ▼
┌─────────────────────────────────────────────────────┐
│                     BACKEND                         │
│  FastAPI                                            │
│                                                     │
│  POST /api/verify                                   │
│  ├── image_validator        (validate inputs)       │
│  ├── preprocessing.py       (OpenCV pipeline)       │
│  ├── ocr_service.py         (EasyOCR/Tesseract)     │
│  ├── barcode_service.py     (pyzbar)                │
│  ├── matcher_service.py     (CSV + rapidfuzz)       │
│  ├── scoring_service.py     (weighted rules)        │
│  └── explanation_service.py (LLM call)              │
│  ├── conversation.py        (/api/conversations)    │
│  └── conversation_service.py (SQLite/Postgres persistence) │
│                                                     │
│  Returns: VerificationResult JSON                   │
└───────────────────┬─────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│                    DATA LAYER                       │
│  data/fda_ghana_drugs_500.csv (primary registry data)│
│  data/products.csv        (legacy curated fallback) │
│  data/rules.json          (scoring weights/rules)   │
│  data/verimed.sqlite3     (local conversation persistence)│
│  data/reference_images/   (1 front + 1 back/drug)   │
└─────────────────────────────────────────────────────┘
```

---

## Follow-up Assistant (Implemented)

The follow-up assistant is implemented as a contextual helper, not as a standalone primary chatbot flow.

- Placement: embedded beside verification results in `/verify`
- Scope: answers only follow-up questions about the current verification result
- Context used by backend: full `VerificationResult` snapshot + recent conversation history
- Persistence: SQLite locally (`backend/data/verimed.sqlite3`) or Postgres in production (`DATABASE_URL`)

### Assistant API Endpoints

- `POST /api/conversations` — create conversation from a verification result snapshot
- `GET /api/conversations/{conversation_id}` — fetch conversation history and stored verification context
- `POST /api/conversations/{conversation_id}/messages` — add user message and get assistant response
- `GET /api/conversations` — list conversation summaries
- `DELETE /api/conversations/history` — clear all conversation history

---

## Request/Response Lifecycle

```
Client uploads 3 images
        │
        ▼
[1] Validation
    - Check all 3 images present
    - Check file type (JPEG/PNG/WEBP)
    - Check file size (< 10MB each)
    - Blur detection (Laplacian variance threshold)
        │
        ▼
[2] Preprocessing (OpenCV per image)
    - Resize to standard dimensions
    - Grayscale for OCR images
    - Denoise (fastNlMeansDenoising)
    - Contrast normalization (CLAHE)
    - Sharpen (unsharp mask)
    - Crop likely text regions (front/back)
    - Crop likely code region (barcode image)
        │
        ├──────────────────────────┐
        ▼                          ▼
[3a] OCR Extraction           [3b] Barcode Decoding
     EasyOCR on front              pyzbar on barcode image
     EasyOCR on back               Returns: { type, value, raw }
     Returns: structured text      Falls back to QR reader if needed
     blocks with confidence
        │                          │
        └──────────────┬───────────┘
                       ▼
[4] Text Normalization + Field Parsing
    - Normalize whitespace, case
    - Regex extract: expiry date, batch number
    - Extract: brand name, strength, dosage form
    - Extract: manufacturer string
    - Extract: expected keywords
        │
        ▼
[5] Candidate Matching (matcher_service)
    - Load fda_ghana_drugs_500.csv as primary dataset (cached at startup)
    - Fallback to products.csv when needed
    - If barcode decoded: attempt direct barcode lookup first
    - If barcode match: shortlist to that product
    - If no barcode match: fuzzy match brand_name, generic_name
    - Compute match confidence per candidate
    - Select top candidate (or mark "no reliable match")
        │
        ▼
[6] Consistency Scoring (scoring_service)
    - Compare extracted fields to matched product record
    - Apply weights from rules.json
    - Accumulate score (0–100 scale)
    - Collect list of positive signals and failure reasons
    - Classify: low_risk / medium_risk / high_risk / cannot_verify
        │
        ▼
[7] Explanation (explanation_service)
    - Serialize verification summary to structured prompt
    - Single LLM call via NVIDIA OpenAI-compatible API, with Anthropic fallback
    - Returns 2–4 sentence user-facing explanation
    - Append recommended action
        │
        ▼
[8] Response Assembly
    - Return full VerificationResult JSON to frontend
```

### Dataset Source Disclaimer

The primary drug registry dataset in this project was obtained from the Ghana FDA Product Registry page:
https://fdaghana.gov.gh/programmes/product-registry/

This dataset is used for reference-based risk assessment and does not represent regulatory certification by Ghana FDA.

---

## Data Models

### Input Model

```python
# Pydantic model for the incoming verification request
class VerificationRequest(BaseModel):
    # All three images are required; sent as multipart/form-data
    # Not a Pydantic model — handled as FastAPI File() params
    pass

# FastAPI route signature:
# async def verify(
#     front_image: UploadFile = File(...),
#     back_image: UploadFile = File(...),
#     barcode_image: UploadFile = File(...)
# )
```

### Extraction Model

```python
class ExtractedFields(BaseModel):
    brand_name: str | None
    generic_name: str | None
    strength: str | None
    dosage_form: str | None
    manufacturer: str | None
    batch_number: str | None
    expiry_date: str | None
    keywords_found: list[str]
    raw_front_text: str
    raw_back_text: str
    ocr_confidence_front: float   # 0.0–1.0 average confidence
    ocr_confidence_back: float

class BarcodeResult(BaseModel):
    decoded: bool
    code_type: str | None         # e.g. "EAN13", "QR_CODE", "CODE128"
    value: str | None
    raw_payload: str | None
```

### Product Record (from CSV)

```python
class ProductRecord(BaseModel):
    product_id: str
    brand_name: str
    generic_name: str
    strength: str
    dosage_form: str
    manufacturer: str
    barcode: str | None
    expected_keywords: list[str]
    expected_front_text: list[str]
    expected_back_text: list[str]
    expiry_pattern: str           # regex string
    batch_pattern: str            # regex string
    reference_image_front: str    # filename in reference_images/
    reference_image_back: str
    ghana_fda_listed: bool        # manual verification flag
    notes: str | None
```

### Match Result

```python
class MatchResult(BaseModel):
    matched: bool
    product: ProductRecord | None
    match_method: str             # "barcode_exact" | "fuzzy_name" | "none"
    match_confidence: float       # 0.0–1.0
```

### Scoring Result

```python
class ScoringSignal(BaseModel):
    field: str
    passed: bool
    weight: int
    contribution: int
    reason: str

class ScoringResult(BaseModel):
    raw_score: int
    unclamped_score: int
    normalized_score: float       # 0.0–1.0 (raw_score / 100)
    classification: str           # "low_risk" | "medium_risk" | "high_risk" | "cannot_verify"
    signals: list[ScoringSignal]
    total_contribution: int
    reasons: list[str]
```

### Final Verification Result

```python
class VerificationResult(BaseModel):
    # Meta
    request_id: str               # UUID
    timestamp: str                # ISO 8601

    # Identity
    identified_product: str | None
    matched_product_id: str | None

    # Extracted signals
    extraction: ExtractedFields
    barcode: BarcodeResult

    # Matching
    match: MatchResult

    # Scoring
    scoring: ScoringResult

    # Output
    risk_score: int               # 0–100
    classification: str
    reasons: list[str]
    explanation: str              # LLM-generated, user-facing
    recommendation: str           # e.g. "Consult a pharmacist before use"
```

---

## Service Contracts

### `ocr_service.py`

```
Input:  preprocessed image (numpy array or bytes)
Output: ExtractedFields (partial — fills OCR-derived fields)

Internal steps:
  1. Run EasyOCR reader.readtext() on image
  2. Filter low-confidence text blocks (< 0.4 threshold)
  3. Concatenate text into raw string
  4. Pass raw string through field parsers (normalization.py)
  5. Return structured ExtractedFields
```

### `barcode_service.py`

```
Input:  barcode/QR image (numpy array or bytes)
Output: BarcodeResult

Internal steps:
  1. pyzbar.decode() on image
  2. If no result: attempt QR-specific decode with OpenCV QRCodeDetector
  3. Return first successful decode or decoded=False
```

### `matcher_service.py`

```
Input:  ExtractedFields, BarcodeResult
Output: MatchResult

Internal steps:
  1. Load products list (CSV → list[ProductRecord]) — cached via lru_cache and warmed at startup
  2. If barcode decoded and barcode.value is not None:
       - Expand barcode value into candidates via utils.normalization.barcode_candidates()
       - Attempt exact match on products[*].barcode
       - If match found: return match_method="barcode_exact", confidence=1.0
  3. Build candidate list via rapidfuzz.process.extract():
       - Query: extracted brand_name + generic_name
       - Corpus: products[*].brand_name + generic_name
       - scorer: fuzz.token_set_ratio
       - cutoff: 60
  4. Score each candidate for keyword overlap
  5. Return top candidate if confidence > 0.55, else matched=False

FDA dataset notes:
  - Products loaded from fda_ghana_drugs_500.csv have generic_name="" (empty) — no
    separate generic name in the registry; avoids double-counting in scoring
  - Manufacturer strings in the FDA CSV are full postal addresses; these are truncated
    to company name only (split at " - " or first comma) during load
```

### `scoring_service.py`

```
Input:  ExtractedFields, BarcodeResult, MatchResult, rules (dict from rules.json)
Output: ScoringResult

Internal steps:
  1. If not matched: return classification="cannot_verify", score=0
  2. For each scoring rule in rules["field_weights"]:
       - Evaluate condition against extracted vs product fields
       - Accumulate score delta
       - Append ScoringSignal
       - generic_name signal is skipped when product.generic_name is empty
         (FDA dataset products have no separate generic name; avoids double-counting
         brand_name and generic_name as +30 when they are the same string)
  3. Apply penalty rules from rules["penalties"]
       - keyword_missing penalty is applied once per product match,
         not once per missing keyword, to prevent unbounded penalty stacking
  4. Clamp final score to [0, 100]
  5. Classify by threshold bands
  6. Return ScoringResult (normalized_score = raw_score / 100.0)
```

### `explanation_service.py`

```
Input:  VerificationResult (without explanation field populated)
Output: str (the explanation text)

Internal steps:
  1. Build structured prompt:
       - System: "You are a medicine safety assistant. Summarize risk assessment results in 2–4 plain sentences. Never say a product is definitely real or definitely fake. Always advise consulting a pharmacist."
       - User: JSON dump of risk_score, classification, reasons, identified_product
  2. Single LLM API call (max_tokens=200)
  3. Return response text
  4. If LLM call fails: return fallback static text based on classification
```

---

## Preprocessing Pipeline (OpenCV)

```python
def preprocess_for_ocr(image: np.ndarray) -> np.ndarray:
    # 1. Resize: limit longest edge to 1600px (maintains aspect ratio)
    # 2. Convert to grayscale
    # 3. CLAHE contrast normalization (clipLimit=2.0, tileGridSize=(8,8))
    # 4. Gaussian blur to reduce noise (3x3 kernel)
    # 5. Unsharp masking for edge sharpening
    # 6. Threshold if image is mostly dark (Otsu binarization)
    return processed_image

def preprocess_for_barcode(image: np.ndarray) -> np.ndarray:
    # 1. Resize to fixed width 800px
    # 2. Grayscale
    # 3. Denoise (fastNlMeansDenoising, h=10)
    # 4. Sharpen aggressively (Laplacian-based)
    # 5. Threshold (adaptive)
    return processed_image
```

---

## Scoring Weights (default)

| Signal | Delta |
|---|---|
| Product name match | +20 |
| Generic name match | +10 |
| Strength match | +15 |
| Dosage form match | +10 |
| Manufacturer match | +15 |
| Barcode decoded successfully | +10 |
| Barcode matches dataset record | +20 |
| Expiry detected and valid format | +10 |
| Batch number detected and valid | +5 |
| Critical keyword(s) missing | −10 (single deduction regardless of how many are missing) |
| Spelling anomaly detected in brand name | −15 |
| Manufacturer string missing entirely | −15 |
| Barcode decoded but does NOT match record | −25 |
| No product match found | −20 |

All weights are overridable via `rules.json`.

---

## Frontend Component Map

```
/app
  /page.tsx                      — Landing / home
  /verify/page.tsx               — Main verification flow + follow-up assistant

components/
  ImageUploadZone.tsx            — Drag/drop or tap-to-upload for each image slot
  RealtimeCameraPreview.tsx      — Live camera stream with per-frame detection overlay
                                   Shows detected drug name + confidence in top-right corner;
                                   "Scanning…" pulse when camera is live but no match yet
  UploadProgress.tsx             — Loading state during API call
  ResultCard.tsx                 — Risk level badge, score, explanation
  ExtractedFieldsPanel.tsx       — Collapsible: shows what OCR found
  ReasonsPanel.tsx               — Bullet list of scoring signals
  FollowUpChat.tsx               — Embedded assistant panel (result-adjacent, not standalone)
  Navbar.tsx                     — Top navigation bar

lib/
  api.ts                         — Typed fetch wrappers for all backend endpoints
  types.ts                       — TypeScript mirrors of Pydantic models
```

---

## API Endpoints

### `POST /api/verify`

| Field | Type | Description |
|---|---|---|
| `front_image` | `File` | Front of medicine packaging |
| `back_image` | `File` | Back of medicine packaging |
| `barcode_image` | `File` | Close-up of barcode or QR code |

**Response:** `VerificationResult` (see Data Models above)

**Error responses:**

| Code | Reason |
|---|---|
| 422 | Missing image(s) or invalid file type |
| 400 | Image too blurry / unreadable |
| 500 | Internal extraction or scoring failure |

### `GET /health`

Returns `{ "status": "ok" }`. Used by frontend to check backend is live.

---

## Security Notes (Hackathon MVP)

- Images are processed in memory and not persisted to disk
- No user authentication required for MVP
- No PII collected
- Rate limiting is enforced with FastAPI `slowapi`
- Limits: `/api/verify` → 10/min, `POST /api/conversations` → 30/min, `POST /api/conversations/{id}/messages` → 20/min, `/api/realtime/detect` → 30/min
- Never log raw image data

---

## Known Limitations

- OCR accuracy degrades on glossy packaging, rotated text, or compressed images
- pyzbar requires the barcode to be well-lit and minimal skew
- Fuzzy matching can produce false positives if two products share similar names
- LLM explanation may hallucinate if the prompt is ambiguous — the prompt must be tightly structured
- Dataset coverage is the ceiling for detection quality; products not in the dataset return "cannot verify"
- Cloned packaging (visually identical fake) may score as low risk if all text and barcode are copied correctly
