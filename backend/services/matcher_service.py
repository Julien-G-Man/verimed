import csv
import logging
import os
from functools import lru_cache

from rapidfuzz import fuzz, process

from config import settings
from models import BarcodeResult, ExtractedFields, MatchResult, ProductRecord

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def load_products() -> tuple:
    csv_path = os.path.join(settings.data_dir, "products.csv")
    products: list[ProductRecord] = []
    try:
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
    except FileNotFoundError:
        logger.error("products.csv not found at %s", csv_path)
    except Exception as exc:
        logger.error("Failed to load products.csv: %s", exc)
    logger.info("Loaded %d products.", len(products))
    return tuple(products)


def _barcode_exact_match(barcode_value: str, products: tuple) -> ProductRecord | None:
    for p in products:
        if p.barcode and p.barcode.strip() == barcode_value.strip():
            return p
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
