# VeriMed — AI-Powered Medicine Authenticity Risk Assessment

> **Disclaimer:** VeriMed is an early-warning assistant for consumers and vendors. It does not replace pharmacists, manufacturers, or regulators. A result from this tool is never medical or legal certification.

---

## What Is This?

VeriMed is a mobile-friendly web application that helps users assess whether a medicine is likely **genuine**, **suspicious**, or **unverifiable** — by analyzing uploaded product images and comparing extracted details against a trusted reference dataset.

This is **not** a universal counterfeit detector. It is a **reference-based authenticity risk assessment tool**.

The distinction matters:
- Barcodes alone do not prove authenticity
- Cloned packaging is possible
- The FDA NDC directory is a product listing system, not a counterfeit-proof verification system
- GS1 GTINs identify products, not guarantee authenticity

What VeriMed *does* provide:
- Likely product identification from packaging
- Structured consistency check across multiple signals
- Weighted risk score with reasons
- Plain-language explanation
- Recommended next action for the user

---

## The Problem

Counterfeit and substandard medicines are dangerous. Ordinary consumers cannot reliably interpret packaging details, barcodes, batch numbers, expiry formatting, or manufacturer claims. This tool bridges that gap with a fast, accessible, explainable assessment.

---

## Target Audience (MVP)

- Consumers buying medicines from local pharmacies or open markets
- Pharmacy vendors doing quick spot-checks
- Hackathon demo judges evaluating feasibility and social impact

---

## MVP Scope

**In scope:**
- Medicines only
- Web app, mobile-first
- 3 required user-uploaded images: front pack, back pack, barcode/QR close-up
- Small curated reference dataset (~10–20 medicines)
- OCR + barcode decoding + rule-based scoring
- One LLM call for natural-language explanation

**Out of scope (v1):**
- Universal counterfeit detection
- Deep custom model training
- Food products
- Manufacturer or regulator integration
- Pharmacy-grade certification
- Offline mobile app

---

## User Flow

```
1. User opens the web app
2. User selects "Verify Medicine"
3. User uploads 3 images: front, back, barcode/QR
4. Backend extracts text and code data
5. System matches signals against the reference dataset
6. Rule engine computes a credibility/risk score
7. LLM converts the structured result into a plain-language explanation
8. UI displays: identified product, extracted details, risk level, reasons, recommendation
```

---

## Tech Stack (Summary)

| Layer | Technology |
|---|---|
| Frontend | Next.js, Tailwind CSS |
| Backend | FastAPI, Pydantic, Uvicorn |
| Image processing | OpenCV |
| OCR | EasyOCR (preferred) or Tesseract |
| Barcode/QR | pyzbar |
| Fuzzy matching | rapidfuzz |
| Data | CSV + JSON + local image folder |
| Explanation | Single LLM API call (Claude or OpenAI) |

---

## Project Structure

```
verimed/
├── frontend/
│   └── nextjs-app/
├── backend/
│   ├── main.py
│   ├── routes/
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
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DATA_MODEL.md
│   ├── BUILD_PLAN.md
│   └── CLAUDE.md
└── README.md
```

---

## Risk Classification

| Score | Classification |
|---|---|
| 80–100 | ✅ Low risk — likely consistent |
| 50–79 | ⚠️ Medium risk — caution advised |
| < 50 | 🚨 High risk — suspicious |
| No match | ❓ Cannot verify |

---

## Demo Scenarios

The system is built around three controlled demo cases:

1. **Likely genuine** — all fields align, barcode matches, expected keywords present
2. **Suspicious** — barcode mismatch, misspelling detected, manufacturer inconsistency
3. **Cannot verify** — unknown product, poor image quality, incomplete extraction

The third outcome is as important as the first two. A system that knows what it doesn't know is more trustworthy than one that always gives an answer.

---

## Pitch Statement

> *"We built an AI-powered medicine authenticity risk assessment tool that helps ordinary consumers detect suspicious products using OCR, barcode decoding, trusted reference data, and explainable scoring."*

---

## Documentation

- [`ARCHITECTURE.md`](./docs/ARCHITECTURE.md) — Full system design, pipeline, data flow, component models
- [`DATA_MODEL.md`](./docs/DATA_MODEL.md) — CSV schema, JSON rules format, dataset strategy
- [`BUILD_PLAN.md`](./docs/BUILD_PLAN.md) — Phased execution plan, team roles, 24-hour sprint guide
- [`CLAUDE.md`](./docs/CLAUDE.md) — Context file for Claude Code to assist with implementation