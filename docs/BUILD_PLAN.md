# Build Plan — PharmaCheck

## Goal

Ship a working MVP in 24–48 hours. This document defines the build order, what "done" means for each phase, team roles, and a compressed 24-hour sprint schedule.

---

## Build Philosophy

- Build the pipeline first, UI second
- Always have a working end-to-end path, even with hardcoded/mock data
- Test with real medicine images as early as possible — OCR quality determines everything
- Do not polish anything until the core pipeline works

---

## Phases

### Phase 0 — Environment Setup (1–2 hours)

**Goal:** Everyone can run the project locally before writing a single feature.

Backend:
```bash
python -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn python-multipart pydantic \
    opencv-python-headless easyocr pyzbar rapidfuzz \
    python-dotenv anthropic
```

Frontend:
```bash
npx create-next-app@latest frontend --ts --tailwind --app
```

Milestone: `uvicorn main:app --reload` starts, `/api/health` returns `{ "status": "ok" }`

---

### Phase 1 — Dataset (2–4 hours)

**Goal:** `products.csv` and `rules.json` exist with at least 6 real products. Reference images collected.

Steps:
1. Choose 6–8 medicines from the recommended list
2. Physically photograph (or find clean product images)
3. Decode barcodes with phone scanner app or pyzbar test script
4. Fill each row in `products.csv`
5. Confirm Ghana FDA listing where possible
6. Set keyword lists and regex patterns in `rules.json`
7. Prepare 3 demo cases: one likely genuine, one suspicious, one unverifiable

Milestone: `python -c "from services.matcher_service import load_products; print(len(load_products()))"` prints 6+

---

### Phase 2 — Extraction Pipeline (3–4 hours)

**Goal:** Uploading 3 images returns structured extracted fields.

Steps:

1. `utils/preprocessing.py`
   - `preprocess_for_ocr(image_bytes) -> np.ndarray`
   - `preprocess_for_barcode(image_bytes) -> np.ndarray`

2. `services/ocr_service.py`
   - Initialize EasyOCR reader once at module level (`reader = easyocr.Reader(['en'])`)
   - `extract_fields(front_bytes, back_bytes) -> ExtractedFields`

3. `services/barcode_service.py`
   - `decode_barcode(barcode_bytes) -> BarcodeResult`

4. `routes/verify.py`
   - `POST /api/verify` receives 3 files
   - Runs preprocessing → OCR → barcode decode
   - Returns `ExtractedFields` + `BarcodeResult` as JSON (scoring not needed yet)

Test with: curl command uploading 3 real images and checking the returned text fields.

Milestone: Uploading Panadol images returns `brand_name: "Panadol"`, `strength: "500mg"`, barcode decoded.

---

### Phase 3 — Matching + Scoring (2–3 hours)

**Goal:** Extracted fields are matched to a product and scored.

Steps:

1. `services/matcher_service.py`
   - `load_products()` — CSV loader with caching
   - `match_product(fields: ExtractedFields, barcode: BarcodeResult) -> MatchResult`
   - Barcode exact match first, fuzzy match fallback

2. `services/scoring_service.py`
   - `load_rules()` — JSON loader with caching
   - `score(fields, barcode, match, rules) -> ScoringResult`
   - Implement weighted scoring loop

3. Update `POST /api/verify` to run full pipeline and return `VerificationResult` (no explanation yet)

Milestone: Submitting a genuine-looking product returns `classification: "low_risk"`, submitting with wrong barcode returns `classification: "high_risk"`.

---

### Phase 4 — Explanation Layer (1 hour)

**Goal:** The result card shows a human-readable explanation.

Steps:

1. `services/explanation_service.py`
   - `generate_explanation(result: VerificationResult) -> str`
   - Build tight prompt: system role + structured JSON input
   - Single LLM call, max_tokens=200
   - Fallback string if LLM fails

2. Plug into `POST /api/verify` as final step

Milestone: Submitting images returns a paragraph of natural language that accurately summarizes the risk.

---

### Phase 5 — Frontend (3–4 hours)

**Goal:** A clean, mobile-first UI that walks through upload → result.

Pages:
- `/` — Hero with "Verify a Medicine" CTA
- `/verify` — 3-slot upload form + submit → result card

Components to build in order:
1. `ImageUploadZone` — tap/drag per slot, preview thumbnail
2. `UploadProgress` — loading state during API call
3. `ResultCard` — risk badge (color-coded), score, explanation, recommendation
4. `ExtractedFieldsPanel` — collapsible, shows what OCR found
5. `ReasonsPanel` — positive and negative signals

Risk badge colors:
- Low risk → green
- Medium risk → amber
- High risk → red
- Cannot verify → gray

Milestone: Full mobile flow works: upload 3 images, see risk card with score and explanation.

---

### Phase 6 — Demo Polish (1–2 hours)

**Goal:** Three controlled demo cases always work perfectly.

Steps:
1. Prepare demo image sets (front + back + barcode for each case)
2. Test all 3 scenarios end-to-end at least 3 times each
3. Add loading skeleton to prevent layout shift
4. Handle error states gracefully (bad image, API error)
5. Ensure UI looks good on a phone screen
6. Take 3 screenshots of each outcome for pitch slide

---

## Team Roles

| Role | Responsibilities |
|---|---|
| **Backend lead** | Preprocessing, OCR, barcode, scoring engine |
| **Data lead** | Dataset collection, products.csv, rules.json, reference images |
| **Frontend lead** | Next.js UI, upload flow, result card, mobile styling |
| **Integration + LLM** | explanation_service.py, API types alignment, end-to-end testing |

If the team is 2–3 people, backend lead handles both backend and integration; data lead doubles as frontend support.

---

## 24-Hour Sprint Schedule

```
Hour 0–2:    Environment setup + project skeleton
Hour 2–5:    Dataset collection (all hands — photograph products now)
Hour 5–8:    OCR service + barcode service working
Hour 8–10:   Matcher + scoring working end-to-end
Hour 10–11:  Explanation layer
Hour 11–15:  Frontend (upload flow + result card)
Hour 15–18:  Integration + end-to-end testing
Hour 18–20:  Demo case preparation + controlled testing
Hour 20–22:  Polish: error states, loading states, mobile UX
Hour 22–24:  Screenshot capture, pitch narrative, rehearsal
```

---

## Definition of Done (MVP)

The MVP is complete when:

- [ ] Uploading images of a known product returns its correct name
- [ ] Uploading images with a wrong barcode returns `high_risk`
- [ ] Uploading an unknown product returns `cannot_verify`
- [ ] The explanation is readable and accurate for all 3 cases
- [ ] The UI works on a mobile screen without horizontal scrolling
- [ ] The 3 demo cases are documented with their image sets

---

## Fallback Strategies

| Risk | Mitigation |
|---|---|
| EasyOCR is too slow | Switch to Tesseract (`pytesseract`) — faster, slightly less accurate |
| pyzbar fails on device | Use `opencv` QRCodeDetector + ZBar CLI as backup |
| LLM API key not available | Use static fallback strings keyed to classification type |
| Dataset too small | Demo with 3 products only — quality over quantity |
| Frontend not ready | Demo via Swagger UI at `/docs` — judges understand MVPs |
| Image quality too low | Brief judges upfront: "image quality affects OCR accuracy" |

---

## Pitch Talking Points

1. **The problem is real.** Substandard medicines kill people. Consumers have no tool for fast, accessible verification.

2. **We are honest about limitations.** This is a risk assessment tool, not a regulatory certification system. The system can say "cannot verify" — that is a feature, not a bug.

3. **The LLM is not the logic.** The scoring is deterministic and explainable. The LLM is only the communicator. Judges who push back on "AI" claims can be shown the scoring engine directly.

4. **The dataset is the product.** If we expand to 200 curated products with Ghana FDA verification, this becomes genuinely useful in the real market.

5. **Extension paths are clear.** Manufacturer integration, regulator API access, crowd-sourced verification, mobile app — all logical next steps.