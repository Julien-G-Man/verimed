# CLAUDE.md — PharmaCheck

This file grounds Claude Code for implementation work on PharmaCheck. Read this before writing any code, generating any files, or making architectural decisions.

---

## What This Project Is

PharmaCheck is a mobile-friendly web app for medicine authenticity risk assessment. Users upload 3 images of a medicine package (front, back, barcode/QR). The backend extracts text and barcode data, matches it against a curated reference dataset, scores consistency using deterministic weighted rules, and returns a risk classification plus a plain-language explanation.

**The LLM is not the truth engine. It is only the explanation layer.**

All scoring is deterministic. The LLM generates the final user-facing paragraph only.

---

## Project Structure

```
pharmacheck/
├── frontend/                  — Next.js 14 app (App Router, TypeScript, Tailwind)
│   └── nextjs-app/
├── backend/                   — FastAPI application
│   ├── main.py
│   ├── models.py              — All Pydantic models
│   ├── routes/
│   │   └── verify.py          — POST /api/verify
│   ├── services/
│   │   ├── ocr_service.py
│   │   ├── barcode_service.py
│   │   ├── matcher_service.py
│   │   ├── scoring_service.py
│   │   └── explanation_service.py
│   ├── data/
│   │   ├── products.csv
│   │   ├── rules.json
│   │   └── reference_images/
│   └── utils/
│       ├── preprocessing.py
│       ├── normalization.py
│       └── regex_patterns.py
└── docs/
```

---

## Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| Frontend | Next.js 14, TypeScript, Tailwind CSS | App Router, mobile-first |
| Backend | FastAPI, Pydantic v2, Uvicorn | Python 3.11+ |
| Image processing | OpenCV (`opencv-python-headless`) | Not `opencv-python` (no GUI needed) |
| OCR | EasyOCR | Primary. Tesseract (`pytesseract`) as fallback |
| Barcode/QR | pyzbar | With OpenCV QRCodeDetector as fallback |
| Fuzzy matching | rapidfuzz | Use `fuzz.token_set_ratio` |
| Data | CSV + JSON + local image folder | No database for MVP |
| LLM | Anthropic Claude API (claude-haiku-3-5 or sonnet) | Single call, max_tokens=200 |

---

## Data Models

All Pydantic models live in `backend/models.py`. The canonical models are:

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
    ocr_confidence_front: float
    ocr_confidence_back: float

class BarcodeResult(BaseModel):
    decoded: bool
    code_type: str | None
    value: str | None
    raw_payload: str | None

class MatchResult(BaseModel):
    matched: bool
    product: dict | None          # ProductRecord as dict
    match_method: str             # "barcode_exact" | "fuzzy_name" | "none"
    match_confidence: float

class ScoringResult(BaseModel):
    raw_score: int
    normalized_score: float
    classification: str           # "low_risk" | "medium_risk" | "high_risk" | "cannot_verify"
    reasons: list[str]

class VerificationResult(BaseModel):
    request_id: str
    timestamp: str
    identified_product: str | None
    matched_product_id: str | None
    extraction: ExtractedFields
    barcode: BarcodeResult
    match: MatchResult
    scoring: ScoringResult
    risk_score: int
    classification: str
    reasons: list[str]
    explanation: str
    recommendation: str
```

---

## Core Pipeline (in order)

1. Validate 3 uploaded images (type, size, blur)
2. Preprocess with OpenCV (grayscale, denoise, sharpen, contrast)
3. OCR front + back with EasyOCR
4. Decode barcode/QR with pyzbar
5. Normalize and parse extracted text into structured fields
6. Match against `products.csv` (barcode exact first, fuzzy fallback)
7. Score consistency with weighted rules from `rules.json`
8. Call LLM for explanation (single call, max_tokens=200)
9. Return `VerificationResult`

---

## Key Implementation Rules

### OCR
- Initialize `easyocr.Reader(['en'])` once at module level — it is expensive
- Filter text blocks below `0.4` confidence
- Concatenate all remaining text into raw string before parsing
- Run `preprocess_for_ocr()` on both front and back before passing to EasyOCR

### Barcode
- Run `pyzbar.decode()` first
- If no result, try `cv2.QRCodeDetector().detectAndDecode()`
- Return `BarcodeResult(decoded=False)` if both fail — do not raise

### Matching
- Always try barcode exact match first (highest confidence)
- Use `rapidfuzz.process.extract()` with `fuzz.token_set_ratio`
- Cutoff: 60 (from `rules.json`)
- Pick top candidate only if score > threshold
- If no match: `MatchResult(matched=False, match_method="none", match_confidence=0.0)`

### Scoring
- Load weights and penalties from `rules.json` — never hardcode them in Python
- Clamp final score to `[0, 100]`
- Classification thresholds: low_risk ≥ 80, medium_risk ≥ 50, else high_risk
- If `matched=False`: always return `classification="cannot_verify"`, skip scoring

### LLM Explanation
- System prompt: "You are a medicine safety assistant. Summarize risk assessment results in 2–4 plain sentences. Never say a product is definitely real or definitely fake. Always advise consulting a pharmacist."
- User message: compact JSON with `risk_score`, `classification`, `reasons`, `identified_product`
- If LLM call fails for any reason: return a hardcoded fallback string based on classification
- Never let LLM failure break the overall response

### Data Loading
- Use `functools.lru_cache(maxsize=1)` on `load_products()` and `load_rules()`
- Call both during FastAPI `lifespan` startup event to warm cache
- products.csv multi-value fields (keywords, expected text) are pipe-separated strings → split on `|`

---

## Frontend Rules

- Use Next.js App Router (`/app` directory)
- Do not use pages router
- Do not use `<form>` tags — use `onClick` and `FormData` manually
- TypeScript strict mode on
- All types mirror Pydantic models from `backend/models.py` — keep them in `frontend/lib/types.ts`
- API calls go through `frontend/lib/api.ts` — no raw fetch calls in components
- Mobile-first: design at 390px width, then scale up
- Risk badge colors: green = low_risk, amber = medium_risk, red = high_risk, gray = cannot_verify

---

## `products.csv` Format

Columns (in order):
```
product_id, brand_name, generic_name, strength, dosage_form, manufacturer,
barcode, expected_keywords, expected_front_text, expected_back_text,
expiry_pattern, batch_pattern, reference_image_front, reference_image_back,
ghana_fda_listed, notes
```

Multi-value fields (`expected_keywords`, `expected_front_text`, `expected_back_text`) use `|` as separator.

---

## `rules.json` Format

```json
{
  "field_weights": { ... },
  "penalties": { ... },
  "classification_thresholds": { "low_risk": 80, "medium_risk": 50 },
  "matching": { "fuzzy_cutoff_score": 60, "fuzzy_confidence_threshold": 0.55 },
  "ocr": { "min_confidence": 0.4, "blur_variance_threshold": 100 },
  "required_keywords_by_product": { "drug_001": [...] },
  "regex_patterns": { "expiry_formats": [...], "batch_generic": "..." }
}
```

---

## API Contract

### `POST /api/verify`

**Request:** `multipart/form-data`
- `front_image`: image file
- `back_image`: image file  
- `barcode_image`: image file

**Response:** `VerificationResult` JSON (200)

**Error responses:**
- `422`: Missing image, invalid file type
- `400`: Image too blurry or unreadable
- `500`: Internal error (always return structured error, never expose stack traces)

### `GET /api/health`

**Response:** `{ "status": "ok" }`

---

## What NOT to Do

- Do not train any custom ML models — use existing OCR and barcode libraries
- Do not add a database — CSV/JSON is intentional for the MVP
- Do not make multiple LLM calls — one call per request, for explanation only
- Do not persist uploaded images — process in memory only
- Do not make LLM responsible for scoring logic — scoring is always deterministic Python
- Do not add authentication for the MVP
- Do not use `opencv-python` (has GUI deps) — use `opencv-python-headless`
- Do not call Ghana FDA registry live during demo — dataset is offline and curated

---

## Demo Cases

Always test against these three controlled cases before any demo:

| Case | Expected classification | Key signals |
|---|---|---|
| Genuine-looking product | `low_risk` | All fields match, barcode matches, keywords present |
| Suspicious product | `high_risk` | Barcode mismatch, missing keywords, manufacturer anomaly |
| Unknown product | `cannot_verify` | No product match in dataset |

The third case (cannot_verify) is as important as the other two in the pitch. Do not hide it.

---

## Environment Variables

```
ANTHROPIC_API_KEY=...        # Required for explanation_service
DATA_DIR=backend/data        # Path to CSV + JSON + reference images
MAX_IMAGE_SIZE_MB=10
OCR_MIN_CONFIDENCE=0.4
```

---

## Dependency Install

```bash
# Backend
pip install fastapi uvicorn python-multipart pydantic \
    opencv-python-headless easyocr pyzbar rapidfuzz \
    python-dotenv anthropic

# Frontend
npx create-next-app@latest nextjs-app --typescript --tailwind --app --no-src-dir
```

---

## Important Framing (for pitch, README, and UI copy)

**Use:**
> "An AI-powered medicine authenticity risk assessment tool that helps ordinary consumers detect suspicious products using OCR, barcode decoding, trusted reference data, and explainable scoring."

**Do not use:**
> "An AI model that tells if drugs are real or fake."

The system provides **risk assessment**, not **certification**. This framing must be consistent across UI copy, pitch, and documentation.