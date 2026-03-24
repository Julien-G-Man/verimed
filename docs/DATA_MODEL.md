# Data Model — VeriMed

## Philosophy

The data layer is intentionally flat and file-based for the MVP. This means no database setup, no migrations, and no infrastructure overhead during a hackathon. The trade-off is acceptable because:

- The reference dataset is small (~10–20 products)
- Data is read-only at runtime (no writes to the dataset)
- Files are loaded into memory at startup and cached

If VeriMed grows beyond the hackathon, the data layer can be migrated to PostgreSQL with minimal changes to the service interfaces.

---

## File Overview

```
backend/data/
├── fda_ghana_drugs_500.csv — Primary Ghana FDA registry extract (current)
├── products.csv          — Reference product records
├── rules.json            — Scoring weights, regex patterns, thresholds
├── verimed.sqlite3       — Conversation persistence store
└── reference_images/
    ├── drug_001_front.jpg
    ├── drug_001_back.jpg
    ├── drug_002_front.jpg
    └── ...
```

## Dataset Source Disclaimer

The primary medicine registry dataset used by this project was obtained from the Ghana FDA Product Registry page:
https://fdaghana.gov.gh/programmes/product-registry/

The dataset is used as a reference input for risk assessment and should not be interpreted as formal regulatory certification.

---

## Conversation Persistence (Implemented)

Follow-up assistant conversations are persisted in SQLite at `backend/data/verimed.sqlite3`.

### Table: `conversations`

| Column | Type | Description |
|---|---|---|
| `id` | text (PK) | Conversation ID (UUID) |
| `request_id` | text | Verification request ID |
| `verification_json` | text | Full serialized `VerificationResult` snapshot |
| `created_at` | text | ISO 8601 timestamp |

### Table: `conversation_messages`

| Column | Type | Description |
|---|---|---|
| `id` | text (PK) | Message ID (UUID) |
| `conversation_id` | text (FK) | Parent conversation ID |
| `role` | text | `user` or `assistant` |
| `content` | text | Message content |
| `created_at` | text | ISO 8601 timestamp |

### Assistant-related Models

- `ConversationMessage`
- `ConversationCreateRequest`
- `ConversationCreateResponse`
- `FollowUpMessageRequest`
- `ConversationResponse`

These models are defined in backend models and mirror frontend TypeScript contracts.

---

## `products.csv` Schema

Each row represents one curated reference medicine.

| Column | Type | Required | Description |
|---|---|---|---|
| `product_id` | string | ✅ | Unique identifier, e.g. `drug_001` |
| `brand_name` | string | ✅ | Commercial product name, e.g. `Panadol` |
| `generic_name` | string | ✅ | INN/generic name, e.g. `Paracetamol` |
| `strength` | string | ✅ | Dosage strength, e.g. `500mg` |
| `dosage_form` | string | ✅ | Tablet / capsule / syrup / sachet / etc. |
| `manufacturer` | string | ✅ | Manufacturer name as printed on packaging |
| `barcode` | string | ✅ | EAN-13, GTIN, or NDC code; `null` if unknown |
| `expected_keywords` | string | ✅ | Pipe-separated list: `tablets\|store below 30°C\|keep out of reach` |
| `expected_front_text` | string | ✅ | Pipe-separated fragments expected on front |
| `expected_back_text` | string | ✅ | Pipe-separated fragments expected on back |
| `expiry_pattern` | string | ✅ | Regex for valid expiry format, e.g. `\d{2}/\d{4}` |
| `batch_pattern` | string | ✅ | Regex for valid batch number, e.g. `[A-Z]{2}\d{6}` |
| `reference_image_front` | string | ✅ | Filename in `reference_images/` |
| `reference_image_back` | string | ✅ | Filename in `reference_images/` |
| `ghana_fda_listed` | boolean | ✅ | `true` if manually confirmed on Ghana FDA registry |
| `notes` | string | ❌ | Optional human notes, not used in scoring |

### Example Row (CSV)

```csv
product_id,brand_name,generic_name,strength,dosage_form,manufacturer,barcode,expected_keywords,expected_front_text,expected_back_text,expiry_pattern,batch_pattern,reference_image_front,reference_image_back,ghana_fda_listed,notes
drug_001,Panadol,Paracetamol,500mg,Tablet,GSK Consumer Healthcare,6001067020077,tablets|paracetamol|store below 30°C|keep out of reach of children,Panadol|500mg|GSK,Paracetamol|dosage|adults|children,\d{2}/\d{4},[A-Z]{2}\d{6},drug_001_front.jpg,drug_001_back.jpg,true,Standard blister pack variant
```

### Loading in Python

```python
import csv
from functools import lru_cache

@lru_cache(maxsize=1)
def load_products() -> list[dict]:
    with open("data/products.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        products = []
        for row in reader:
            row["expected_keywords"] = row["expected_keywords"].split("|")
            row["expected_front_text"] = row["expected_front_text"].split("|")
            row["expected_back_text"] = row["expected_back_text"].split("|")
            row["ghana_fda_listed"] = row["ghana_fda_listed"].lower() == "true"
            products.append(row)
    return products
```

---

## `rules.json` Schema

Controls the scoring engine. All weights and thresholds can be tuned here without touching application code.

```json
{
  "field_weights": {
    "product_name_match": 20,
    "generic_name_match": 10,
    "strength_match": 15,
    "dosage_form_match": 10,
    "manufacturer_match": 15,
    "barcode_decoded": 10,
    "barcode_match": 20,
    "expiry_valid": 10,
    "batch_valid": 5
  },

  "penalties": {
    "critical_keyword_missing": -10,
    "spelling_anomaly": -15,
    "manufacturer_missing": -15,
    "barcode_mismatch": -25,
    "no_product_match": -20
  },

  "classification_thresholds": {
    "low_risk": 80,
    "medium_risk": 50
  },

  "matching": {
    "fuzzy_cutoff_score": 60,
    "fuzzy_confidence_threshold": 0.55,
    "barcode_exact_confidence": 1.0
  },

  "ocr": {
    "min_confidence": 0.4,
    "blur_variance_threshold": 100
  },

  "required_keywords_by_product": {
    "drug_001": ["Paracetamol", "tablets", "store below 30°C"],
    "drug_002": ["Amoxicillin", "capsules", "antibiotic"],
    "drug_003": ["Ibuprofen", "tablets"]
  },

  "regex_patterns": {
    "expiry_formats": [
      "\\d{2}/\\d{4}",
      "\\d{2}/\\d{2}",
      "EXP\\s?\\d{2}/\\d{4}",
      "[A-Z]{3}\\s?\\d{4}"
    ],
    "batch_generic": "[A-Z]{1,3}\\d{4,8}"
  }
}
```

---

## `reference_images/`

One front image and one back image per curated product. Used for:
- Fuzzy visual comparison (optional enhancement, not in MVP scoring)
- Demo display alongside result card
- Team reference during data collection

### Naming Convention

```
{product_id}_front.jpg
{product_id}_back.jpg
```

### Image Requirements

- Resolution: minimum 800×600px
- Format: JPEG or PNG
- Lighting: even, no harsh shadows
- Orientation: upright, no skew
- Barcode: visible but not the primary focus (barcode image is uploaded separately by user)

---

## Curated MVP Dataset — Recommended Medicines

Pick products that are:
- Common in the local market (Ghana/West Africa)
- Easy to photograph cleanly
- Widely available (team can acquire physical samples)
- Distinguishable by packaging

| # | Brand Name | Generic Name | Priority |
|---|---|---|---|
| 1 | Panadol | Paracetamol 500mg | High |
| 2 | Augmentin | Amoxicillin + Clavulanate | High |
| 3 | Brufen | Ibuprofen 400mg | High |
| 4 | ORS (WHO formula) | Oral Rehydration Salts | High |
| 5 | Vitamin C | Ascorbic Acid 200mg | Medium |
| 6 | Coartem | Artemether + Lumefantrine | High |
| 7 | Flagyl | Metronidazole 400mg | Medium |
| 8 | Ventolin | Salbutamol Inhaler | Medium |
| 9 | Piriton | Chlorphenamine 4mg | Low |
| 10 | Maalox | Aluminum/Magnesium Hydroxide | Low |

Start with the "High" priority items. 6–8 products is enough for a compelling demo.

---

## Dataset Sources

### Ghana FDA Product Registry

The Ghana Food and Drugs Authority maintains a public product registry at [https://fdaghana.gov.gh/programmes/product-registry/](https://fdaghana.gov.gh/programmes/product-registry/). Manually search each product to confirm it appears in the registry. Record the result in `ghana_fda_listed` column.

**Use for:**
- Confirming products are Ghana-market registered
- Demo narrative ("verified against Ghana FDA registry")
- Collecting manufacturer name as it appears on official records

**Do not use for:**
- Live API calls during demo (no stable public API, and unreliable connectivity)

### openFDA NDC Directory

Available at [open.fda.gov/data/ndc](https://open.fda.gov/data/ndc). Downloadable JSON/CSV containing structured drug metadata.

**Use for:**
- Barcode/NDC code reference
- Structured field naming conventions
- Manufacturer name normalization inspiration

**Note:** NDC is U.S.-specific. Use it for data structure and field inspiration, not as Ghana-market truth.

### GS1 Barcode Standards

GS1 defines the GTIN standard and "Verified by GS1" lookup. Use [gepir.gs1.org](https://gepir.gs1.org) for barcode lookups.

**Use for:**
- Validating barcode format against GS1 prefix rules
- Understanding what EAN-13 prefix implies (country of manufacture)
- Optional: company prefix lookup for manufacturer validation

---

## Data Collection Checklist (Per Product)

```
[ ] Product physically obtained or photographed
[ ] brand_name confirmed from packaging
[ ] generic_name confirmed from packaging
[ ] strength extracted from packaging
[ ] dosage_form confirmed
[ ] manufacturer string captured exactly as printed
[ ] barcode photographed + decoded (pyzbar or phone scanner app)
[ ] expected_keywords list built from visual scan of pack
[ ] expiry_pattern defined (what format is printed?)
[ ] batch_pattern defined (what format is printed?)
[ ] ghana_fda_listed confirmed via Ghana FDA website
[ ] Front reference image photographed (clean, even light, 800px+)
[ ] Back reference image photographed
[ ] Row added to products.csv
[ ] required_keywords entry added to rules.json
```

---

## Loading Rules at Startup

```python
import json
from functools import lru_cache

@lru_cache(maxsize=1)
def load_rules() -> dict:
    with open("data/rules.json", encoding="utf-8") as f:
        return json.load(f)
```

Both `load_products()` and `load_rules()` should be called during FastAPI startup (`lifespan` event) and cached in application state to avoid file I/O on every request.