"""
OCR service using EasyOCR (primary) with graceful fallback.
The Reader is initialized once at module level — it is expensive to load.
"""
import logging
import warnings
from typing import Any

import numpy as np

from models.models import ExtractedFields
from utils.normalization import normalize_text, parse_fields
from utils.preprocessing import preprocess_for_ocr

logger = logging.getLogger(__name__)

# EasyOCR may emit this warning on CPU-only environments via torch DataLoader.
# It does not affect correctness and can be safely suppressed to reduce log noise.
warnings.filterwarnings(
    "ignore",
    message=".*'pin_memory' argument is set as true but no accelerator is found.*",
    category=UserWarning,
)

# ---------------------------------------------------------------------------
# Module-level EasyOCR reader (loaded once on first import / startup warm-up)
# ---------------------------------------------------------------------------
_reader: Any = None  # easyocr.Reader instance


def get_reader():
    global _reader
    if _reader is None:
        try:
            import easyocr  # noqa: PLC0415
            logger.info("Initializing EasyOCR reader...")
            _reader = easyocr.Reader(["en"], gpu=False, verbose=False)
            logger.info("EasyOCR reader ready.")
        except Exception as exc:
            logger.error("Failed to initialize EasyOCR: %s", exc)
            _reader = None
    return _reader


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _run_easyocr(img: np.ndarray, min_confidence: float = 0.4) -> tuple[str, float]:
    """
    Run EasyOCR on a preprocessed image.
    Returns (raw_text, avg_confidence).
    """
    reader = get_reader()
    if reader is None:
        return "", 0.0

    results = reader.readtext(img, detail=1, paragraph=False)
    # results: list of ([bbox], text, confidence)
    filtered = [(text, conf) for (_, text, conf) in results if conf >= min_confidence]

    if not filtered:
        return "", 0.0

    raw_text = " ".join(t for t, _ in filtered)
    avg_conf = sum(c for _, c in filtered) / len(filtered)
    return raw_text, avg_conf


def _try_tesseract(image_bytes: bytes) -> str:
    """Fallback to pytesseract if available."""
    try:
        import pytesseract  # noqa: PLC0415
        from PIL import Image  # noqa: PLC0415
        import io  # noqa: PLC0415
        img_pil = Image.open(io.BytesIO(image_bytes))
        return pytesseract.image_to_string(img_pil)
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_fields(
    front_bytes: bytes,
    back_bytes: bytes,
    min_confidence: float = 0.4,
    known_brands: list[str] | None = None,
    keyword_list: list[str] | None = None,
) -> ExtractedFields:
    """
    Run OCR on front and back images, parse structured fields.
    """
    # Preprocess
    front_arr = preprocess_for_ocr(front_bytes)
    back_arr = preprocess_for_ocr(back_bytes)

    # OCR
    front_raw, front_conf = _run_easyocr(front_arr, min_confidence)
    back_raw, back_conf = _run_easyocr(back_arr, min_confidence)

    # Fallback if EasyOCR produced nothing
    if not front_raw:
        front_raw = _try_tesseract(front_bytes)
        front_conf = 0.3 if front_raw else 0.0
    if not back_raw:
        back_raw = _try_tesseract(back_bytes)
        back_conf = 0.3 if back_raw else 0.0

    front_raw = normalize_text(front_raw)
    back_raw = normalize_text(back_raw)

    # Parse structured fields
    parsed = parse_fields(
        front_text=front_raw,
        back_text=back_raw,
        known_brands=known_brands,
        keyword_list=keyword_list,
    )

    return ExtractedFields(
        brand_name=parsed["brand_name"],
        generic_name=parsed["generic_name"],
        strength=parsed["strength"],
        dosage_form=parsed["dosage_form"],
        manufacturer=parsed["manufacturer"],
        batch_number=parsed["batch_number"],
        expiry_date=parsed["expiry_date"],
        keywords_found=parsed["keywords_found"],
        raw_front_text=front_raw,
        raw_back_text=back_raw,
        ocr_confidence_front=round(front_conf, 3),
        ocr_confidence_back=round(back_conf, 3),
    )
