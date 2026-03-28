"""
OCR service using RapidOCR (ONNX Runtime) as primary, pytesseract as fallback.
The engine is initialised once at module level and warmed at startup via get_engine().
No PyTorch dependency — onnxruntime is the only ML runtime required.
"""
import logging
from typing import Any

import numpy as np

from models.models import ExtractedFields
from utils.normalization import normalize_text, parse_fields
from utils.preprocessing import preprocess_for_ocr

logger = logging.getLogger(__name__)

_engine: Any = None  # RapidOCR instance


def get_engine() -> Any:
    global _engine
    if _engine is None:
        try:
            from rapidocr_onnxruntime import RapidOCR  # noqa: PLC0415
            logger.info("Initialising RapidOCR engine...")
            _engine = RapidOCR()
            logger.info("RapidOCR engine ready.")
        except Exception as exc:
            logger.error("Failed to initialise RapidOCR: %s", exc)
            _engine = None
    return _engine


def _run_rapidocr(img: np.ndarray, min_confidence: float = 0.4) -> tuple[str, float]:
    """
    Run RapidOCR on a preprocessed image.
    Returns (raw_text, avg_confidence).
    result format: list of [box_points, text, score] or None
    """
    engine = get_engine()
    if engine is None:
        return "", 0.0

    result, _ = engine(img)
    if not result:
        return "", 0.0

    filtered = [(text, score) for (_, text, score) in result if score >= min_confidence]
    if not filtered:
        return "", 0.0

    raw_text = " ".join(t for t, _ in filtered)
    avg_conf = sum(c for _, c in filtered) / len(filtered)
    return raw_text, avg_conf


def _try_tesseract(image_bytes: bytes) -> str:
    """Fallback to pytesseract if available."""
    try:
        import io  # noqa: PLC0415

        import pytesseract  # noqa: PLC0415
        from PIL import Image  # noqa: PLC0415

        img_pil = Image.open(io.BytesIO(image_bytes))
        return pytesseract.image_to_string(img_pil)
    except Exception:
        return ""


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
    front_arr = preprocess_for_ocr(front_bytes)
    back_arr = preprocess_for_ocr(back_bytes)

    front_raw, front_conf = _run_rapidocr(front_arr, min_confidence)
    back_raw, back_conf = _run_rapidocr(back_arr, min_confidence)

    # Tesseract fallback if RapidOCR returns nothing
    if not front_raw:
        front_raw = _try_tesseract(front_bytes)
        front_conf = 0.3 if front_raw else 0.0
    if not back_raw:
        back_raw = _try_tesseract(back_bytes)
        back_conf = 0.3 if back_raw else 0.0

    front_raw = normalize_text(front_raw)
    back_raw = normalize_text(back_raw)

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
