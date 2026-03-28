# CLAUDE.md — VeriMed

This file grounds Claude Code for implementation work on VeriMed. Read this before writing any code, generating any files, or making architectural decisions.

---

## What This Project Is

VeriMed is a mobile-friendly web app for medicine authenticity risk assessment. Users upload 3 images of a medicine package (front, back, barcode/QR). The backend extracts text and barcode data, matches it against a curated reference dataset, scores consistency using deterministic weighted rules, and returns a risk classification plus a plain-language explanation.

The app also includes an embedded follow-up assistant panel beside verification results (in `/verify`) so users can ask contextual questions about the exact result they are viewing.

**The LLM is not the truth engine. It is only the explanation layer.**

All scoring is deterministic. The LLM generates the final user-facing paragraph only.

---

## Project Structure

```
verimed/
├── frontend/                  — Next.js 14 app (App Router, TypeScript, Tailwind)
│   └── nextjs-app/
├── backend/                   — FastAPI application
│   ├── main.py
│   ├── config.py              — Settings via pydantic-settings
│   ├── limiter.py             — slowapi Limiter instance (shared across routes)
│   ├── run.py                 — Uvicorn entry point
│   ├── models/
│   │   └── models.py          — All Pydantic models
│   ├── routes/
│   │   ├── verify.py          — POST /api/verify
│   │   ├── conversation.py    — Conversation endpoints
│   │   └── realtime_detect.py — POST /api/realtime/detect
│   ├── services/
│   │   ├── ocr_service.py
│   │   ├── barcode_service.py
│   │   ├── matcher_service.py
│   │   ├── scoring_service.py
│   │   ├── explanation_service.py
│   │   ├── llm_client.py
│   │   ├── realtime_cv_service.py
│   │   └── conversation_service.py
│   ├── data/
│   │   ├── fda_ghana_drugs_500.csv
│   │   ├── products.csv
│   │   ├── rules.json
│   │   ├── verimed.sqlite3
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
| Data | CSV + JSON + SQLite (local) / Postgres (production) + local image folder | SQLite locally; Postgres (Neon) in production via `DATABASE_URL` |
| LLM | NVIDIA OpenAI-compatible API + Anthropic Claude fallback | Single call per explanation/follow-up turn |
| Rate limiting | slowapi | 10/min verify, 30/min conversations + realtime, 20/min follow-up messages |
| Logging | python-json-logger | JSON format in production (when `PORT` env is set), human-readable locally |

---

## Data Models

All Pydantic models live in `backend/models/models.py`. The canonical models are:

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
    unclamped_score: int
    normalized_score: float
    classification: str           # "low_risk" | "medium_risk" | "high_risk" | "cannot_verify"
    signals: list[dict]
    total_contribution: int
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

class ConversationMessage(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: str

class ConversationCreateRequest(BaseModel):
    verification: VerificationResult

class ConversationCreateResponse(BaseModel):
    conversation_id: str
    request_id: str
    created_at: str
    verification: VerificationResult
    messages: list[ConversationMessage]

class FollowUpMessageRequest(BaseModel):
    message: str

class ConversationResponse(BaseModel):
    conversation_id: str
    request_id: str
    created_at: str
    verification: VerificationResult
    messages: list[ConversationMessage]
```

---

## Core Pipeline (in order)

1. Validate 3 uploaded images (type, size, blur)
2. Preprocess with OpenCV (grayscale, denoise, sharpen, contrast)
3. OCR front + back with EasyOCR
4. Decode barcode/QR with pyzbar
5. Normalize and parse extracted text into structured fields
6. Match against `fda_ghana_drugs_500.csv` (primary) with `products.csv` fallback
7. Score consistency with weighted rules from `rules.json`
8. Call LLM for explanation (single call, max_tokens=200)
9. Return `VerificationResult`
10. Optional follow-up assistant uses stored `VerificationResult` + chat history for contextual Q&A

---

## Key Implementation Rules

### OCR
- Engine is selected automatically at import time: RapidOCR (ONNX Runtime) if `rapidocr_onnxruntime` is installed, else Tesseract
- **RapidOCR** (`requirements-dev.txt`): ~300MB ONNX models, higher accuracy — recommended for local dev and demos
- **Tesseract** (`requirements.txt`): C binary, zero Python-side model memory — used in production (fits Render 512MB free tier)
- Install with `pip install -r requirements-dev.txt` for dev; production installs only `requirements.txt`
- Tesseract uses `pytesseract.image_to_data()` for per-word confidence (0–100 int → normalised to 0.0–1.0)
- Filter words below `0.4` confidence; concatenate remaining words into raw string before parsing
- Run `preprocess_for_ocr()` on both front and back before passing to either engine
- `extract_fields()` is synchronous and CPU-heavy; call it via `asyncio.to_thread()` inside the async route handler — never call it directly in an `async def` or it blocks the event loop
- RapidOCR is warmed at startup via the FastAPI `lifespan` event when `ENGINE == "rapidocr"` — no warmup needed for Tesseract

### Barcode
- Run `pyzbar.decode()` first
- If no result, try `cv2.QRCodeDetector().detectAndDecode()`
- Return `BarcodeResult(decoded=False)` if both fail — do not raise

### Matching
- Always try barcode exact match first (highest confidence)
- Barcode candidate expansion lives in `utils/normalization.barcode_candidates()` — shared by both `matcher_service` and `scoring_service`; do not duplicate it
- Use `rapidfuzz.process.extract()` with `fuzz.token_set_ratio`
- Cutoff: 60 (from `rules.json`)
- Pick top candidate only if score > threshold
- If no match: `MatchResult(matched=False, match_method="none", match_confidence=0.0)`
- FDA products are loaded with `generic_name=""` and manufacturer truncated to company name only (split at ` - ` or first comma) — do not change this without updating scoring logic

### Scoring
- Load weights and penalties from `rules.json` — never hardcode them in Python
- Clamp final score to `[0, 100]`
- `normalized_score` = `raw_score / 100.0` — range is 0.0–1.0, not 0–100
- Classification thresholds: low_risk ≥ 80, medium_risk ≥ 50, else high_risk
- If `matched=False`: always return `classification="cannot_verify"`, skip scoring
- Skip the `generic_name` scoring signal when `product.generic_name` is empty — FDA dataset products have `generic_name=""` because the registry has no INN column; scoring it would double-count the brand name (+30 instead of +20)
- `critical_keyword_missing` penalty is a single deduction applied once per match — do not loop per missing keyword or the penalty becomes unbounded

### LLM Explanation
- System prompt: "You are a medicine safety assistant. Summarize risk assessment results in 2–4 plain sentences. Never say a product is definitely real or definitely fake. Always advise consulting a pharmacist."
- User message: compact JSON with `risk_score`, `classification`, `reasons`, `identified_product`
- If LLM call fails for any reason: return a hardcoded fallback string based on classification
- Never let LLM failure break the overall response

### Follow-up Assistant
- Assistant is contextual and embedded in `/verify`; it is not a standalone primary chatbot flow
- Conversation context is persisted in SQLite locally (`backend/data/verimed.sqlite3`) or Postgres in production (via `DATABASE_URL`)
- `conversation_service.py` auto-detects which backend to use — no code changes needed when switching
- Follow-up responses use full stored `VerificationResult` plus recent conversation history
- Allow markdown-style responses (tables/code/list formatting) in assistant output

### Rate Limiting
- All rate limits are applied via `@limiter.limit(...)` decorator from `backend/limiter.py`
- `request: Request` must be the first parameter of any rate-limited endpoint
- Limits: `/api/verify` → 10/min, `/api/conversations` POST → 30/min, `/api/conversations/{id}/messages` → 20/min, `/api/realtime/detect` → 60/min
- The realtime endpoint is polled by the frontend camera every 2 000 ms (~30/min per user). The limit is set to 60/min to give headroom for network jitter and multiple tabs.

### Data Loading
- Use `functools.lru_cache(maxsize=1)` on `load_products()` and `load_rules()`
- Call both during FastAPI `lifespan` startup event to warm cache
- products.csv multi-value fields (keywords, expected text) are pipe-separated strings → split on `|`
- Primary dataset source is `fda_ghana_drugs_500.csv` (Ghana FDA registry extract)

---

## Frontend Rules

- Use Next.js App Router (`/app` directory)
- Do not use pages router
- Do not use `<form>` tags — use `onClick` and `FormData` manually
- TypeScript strict mode on
- All types mirror Pydantic models from `backend/models/models.py` — keep them in `frontend/lib/types.ts`
- API calls go through `frontend/lib/api.ts` — no raw fetch calls in components
- Mobile-first: design at 390px width, then scale up
- Risk badge colors: green = low_risk, amber = medium_risk, red = high_risk, gray = cannot_verify
- Follow-up assistant must remain in `/verify` results layout (right panel on desktop, stacked on mobile)

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

## Primary Dataset Source

- Primary dataset file: `backend/data/fda_ghana_drugs_500.csv`
- Source URL: https://fdaghana.gov.gh/programmes/product-registry/
- Use as reference data for risk assessment only (not regulatory certification).

---

## `rules.json` Format

```json
{
  "field_weights": { ... },
  "fallback_field_weights": {
    "strength_detected_without_reference": 7,
    "dosage_form_detected_without_reference": 5,
    "manufacturer_detected_without_reference": 7
  },
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

### `GET /health`

**Response:** `{ "status": "ok" }`

### Conversation Endpoints

- `POST /api/conversations` — create conversation from a `VerificationResult`
- `GET /api/conversations` — list conversation summaries
- `GET /api/conversations/{conversation_id}` — get conversation history + verification snapshot
- `POST /api/conversations/{conversation_id}/messages` — send follow-up message and get updated conversation
- `DELETE /api/conversations/history` — clear persisted conversation history

### Realtime Detection

- `POST /api/realtime/detect` — multipart: `frame_image` (UploadFile) + `side` (str, default `"front"`) + `top_k` (int, default `3`, max `5`) → `RealtimeDetectionResponse`

---

## What NOT to Do

- Do not train any custom ML models — use existing OCR and barcode libraries
- Do not add external production databases for MVP (SQLite conversation persistence is already implemented and acceptable)
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
NVIDIA_OPENAI_API_KEY=...    # Optional primary LLM provider
NVIDIA_OPENAI_API_URL=...    # Optional override for NVIDIA OpenAI-compatible endpoint
NVIDIA_OPENAI_MODEL=...      # Optional model ID
DATA_DIR=backend/data        # Path to CSV + JSON + reference images
SQLITE_DB_PATH=data/verimed.sqlite3
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