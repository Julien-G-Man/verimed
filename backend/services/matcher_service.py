import csv
import logging
import os
import re
from functools import lru_cache

from rapidfuzz import fuzz, process

from config import settings
from models import BarcodeResult, ExtractedFields, MatchResult, ProductRecord

logger = logging.getLogger(__name__)


FDA_PRIMARY_FILE = "fda_ghana_drugs_500.csv"
LEGACY_FILE = "products.csv"


_DOSAGE_HINTS: dict[str, str] = {
    "tablet": "Tablet",
    "tablets": "Tablet",
    "caplet": "Tablet",
    "caplets": "Tablet",
    "capsule": "Capsule",
    "capsules": "Capsule",
    "suspension": "Suspension",
    "syrup": "Syrup",
    "inhaler": "Inhaler",
    "injection": "Injection",
    "cream": "Cream",
    "ointment": "Ointment",
    "drops": "Drops",
}


def _infer_strength(name: str) -> str:
    match = re.search(r"(\d+(?:\.\d+)?\s?(?:mg|mcg|g|ml|iu|%))", name, re.IGNORECASE)
    return match.group(1).replace(" ", "") if match else ""


def _infer_dosage_form(name: str) -> str:
    lower = name.lower()
    for token, form in _DOSAGE_HINTS.items():
        if token in lower:
            return form
    return "Unknown"


def _keywords_from_name(name: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9\-]{2,}", name)
    seen: set[str] = set()
    keywords: list[str] = []
    for token in tokens:
        key = token.lower()
        if key in seen:
            continue
        seen.add(key)
        keywords.append(token)
        if len(keywords) >= 4:
            break
    return keywords


def _build_record_from_fda_row(row: dict, idx: int, default_batch_pattern: str, default_expiry_pattern: str) -> ProductRecord:
    product_name = (row.get("Product_Name") or "").strip()
    manufacturer = (row.get("Manufacturer") or "").strip()

    if not product_name:
        raise ValueError("Missing Product_Name")

    return ProductRecord(
        product_id=f"fda_gh_{idx:05d}",
        brand_name=product_name,
        generic_name=product_name,
        strength=_infer_strength(product_name),
        dosage_form=_infer_dosage_form(product_name),
        manufacturer=manufacturer or "Unknown",
        barcode=None,
        expected_keywords=_keywords_from_name(product_name),
        expected_front_text=[product_name],
        expected_back_text=[],
        expiry_pattern=default_expiry_pattern,
        batch_pattern=default_batch_pattern,
        reference_image_front="",
        reference_image_back="",
        ghana_fda_listed=True,
        notes=(row.get("Product_Category") or "").strip() or None,
    )


def _load_fda_products(csv_path: str) -> tuple[ProductRecord, ...]:
    products: list[ProductRecord] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, start=1):
            category = (row.get("Category") or "").strip().lower()
            if category and "drug" not in category:
                continue

            product_name = (row.get("Product_Name") or "").strip()
            if not product_name:
                continue

            record = _build_record_from_fda_row(
                row=row,
                idx=idx,
                default_batch_pattern=r"[A-Z0-9\-]{4,20}",
                default_expiry_pattern=r"\d{2}/\d{2,4}",
            )
            products.append(record)

    return tuple(products)


def _load_legacy_products(csv_path: str) -> tuple[ProductRecord, ...]:
    products: list[ProductRecord] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["expected_keywords"] = [k.strip() for k in row.get("expected_keywords", "").split("|") if k.strip()]
            row["expected_front_text"] = [t.strip() for t in row.get("expected_front_text", "").split("|") if t.strip()]
            row["expected_back_text"] = [t.strip() for t in row.get("expected_back_text", "").split("|") if t.strip()]
            row["ghana_fda_listed"] = row.get("ghana_fda_listed", "false").strip().lower() == "true"
            row["barcode"] = row.get("barcode") or None
            row["notes"] = row.get("notes") or None
            products.append(ProductRecord(**row))
    return tuple(products)


def _barcode_candidates(value: str | None) -> list[str]:
    """Return candidate barcode strings extracted from decoded barcode/QR payload."""
    if not value:
        return []

    raw = value.strip()
    if not raw:
        return []

    candidates = {raw}

    # Whole-payload digits (e.g., formatted barcode with separators)
    digits_only = re.sub(r"\D", "", raw)
    if len(digits_only) >= 8:
        candidates.add(digits_only)

    # Numeric segments found inside QR URLs or structured payloads.
    for match in re.findall(r"\d{8,14}", raw):
        candidates.add(match)

    # Keep stable order: longer candidates first.
    return sorted(candidates, key=len, reverse=True)


@lru_cache(maxsize=1)
def load_products() -> tuple:
    primary_path = os.path.join(settings.data_dir, FDA_PRIMARY_FILE)
    legacy_path = os.path.join(settings.data_dir, LEGACY_FILE)
    products: tuple[ProductRecord, ...] = ()
    try:
        if os.path.exists(primary_path):
            products = _load_fda_products(primary_path)
            logger.info("Using primary FDA dataset: %s", primary_path)
        elif os.path.exists(legacy_path):
            products = _load_legacy_products(legacy_path)
            logger.info("Using legacy products dataset: %s", legacy_path)
        else:
            logger.error("No products dataset found. Expected %s or %s", primary_path, legacy_path)
    except FileNotFoundError:
        logger.error("Products dataset not found.")
    except Exception as exc:
        logger.error("Failed to load products dataset: %s", exc)
    logger.info("Loaded %d products.", len(products))
    return products


def _barcode_exact_match(barcode_value: str, products: tuple) -> ProductRecord | None:
    candidates = _barcode_candidates(barcode_value)
    logger.debug("Barcode/QR candidates for matching: %s", candidates)
    for p in products:
        if not p.barcode:
            continue
        expected = p.barcode.strip()
        if expected in candidates:
            logger.debug(
                "Barcode exact match found: product_id=%s expected=%s matched_candidate=%s",
                p.product_id,
                expected,
                expected,
            )
            return p
        for candidate in candidates:
            if expected in candidate:
                logger.debug(
                    "Barcode embedded match found: product_id=%s expected=%s matched_candidate=%s",
                    p.product_id,
                    expected,
                    candidate,
                )
                return p
    logger.debug("No barcode/QR candidate matched any product barcode.")
    return None


def _keyword_overlap_score(combined_text: str, product: ProductRecord) -> float:
    if not product.expected_keywords:
        return 0.0
    lower = combined_text.lower()
    found = sum(1 for kw in product.expected_keywords if kw.lower() in lower)
    return found / len(product.expected_keywords)


def match_product(
    fields: ExtractedFields,
    barcode: BarcodeResult,
    fuzzy_cutoff: int = 60,
    fuzzy_confidence_threshold: float = 0.55,
) -> MatchResult:
    products = load_products()
    if not products:
        return MatchResult(matched=False, match_method="none", match_confidence=0.0)

    if barcode.decoded and barcode.value:
        logger.debug(
            "Decoded code available for matching: type=%s value=%s",
            barcode.code_type,
            barcode.value,
        )
        hit = _barcode_exact_match(barcode.value, products)
        if hit:
            return MatchResult(matched=True, product=hit, match_method="barcode_exact", match_confidence=1.0)

    combined_ocr = f"{fields.raw_front_text} {fields.raw_back_text}"
    query = " ".join(filter(None, [fields.brand_name, fields.generic_name, fields.strength]))
    if not query.strip():
        query = combined_ocr[:200]

    corpus = [f"{p.brand_name} {p.generic_name}" for p in products]
    matches = process.extract(
        query,
        corpus,
        scorer=fuzz.token_set_ratio,
        score_cutoff=fuzzy_cutoff,
        limit=5,
    )

    if not matches:
        return MatchResult(matched=False, match_method="none", match_confidence=0.0)

    best_text, best_score, best_idx = matches[0]
    candidate = products[best_idx]
    kw_score = _keyword_overlap_score(combined_ocr, candidate)
    blended = (best_score / 100.0) * 0.70 + kw_score * 0.30

    if blended < fuzzy_confidence_threshold:
        return MatchResult(matched=False, match_method="none", match_confidence=round(blended, 3))

    return MatchResult(
        matched=True,
        product=candidate,
        match_method="fuzzy_name",
        match_confidence=round(blended, 3),
    )
