"""
OCR service with environment-aware engine selection.

  RapidOCR (ONNX Runtime) — used when rapidocr_onnxruntime is installed.
    Higher accuracy, ~300MB RAM. Install via requirements-dev.txt.
    Recommended for local development and demos.

  Tesseract — used in production / when RapidOCR is not installed.
    C binary, zero Python-side model memory, safe on 512MB Render instances.
    Installed via system package (tesseract-ocr) + pytesseract wrapper.

The engine is selected once at import time by checking whether
rapidocr_onnxruntime is importable. No env var or config needed.
"""
import logging
from typing import Any

import numpy as np
from PIL import Image

from models.models import ExtractedFields
from utils.normalization import normalize_text, parse_fields
from utils.preprocessing import preprocess_for_ocr

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Engine detection — runs once at module import
# ---------------------------------------------------------------------------

def _detect_engine() -> str:
    try:
        import rapidocr_onnxruntime  # noqa: F401
        return "rapidocr"
    except ImportError:
        return "tesseract"


ENGINE = _detect_engine()
logger.info("OCR engine selected: %s", ENGINE)

_rapidocr_instance: Any = None


def get_engine() -> Any:
    """Return the RapidOCR instance, initialising it on first call."""
    global _rapidocr_instance
    if _rapidocr_instance is None:
        from rapidocr_onnxruntime import RapidOCR  # noqa: PLC0415
        logger.info("Initialising RapidOCR engine...")
        _rapidocr_instance = RapidOCR()
        logger.info("RapidOCR engine ready.")
    return _rapidocr_instance


# ---------------------------------------------------------------------------
# Engine implementations
# ---------------------------------------------------------------------------

def _run_rapidocr(img: np.ndarray, min_confidence: float = 0.4) -> tuple[str, float]:
    """
    Run RapidOCR on a preprocessed image.
    result format: list of [box_points, text, score] or None
    """
    engine = get_engine()
    result, _ = engine(img)
    if not result:
        return "", 0.0

    filtered = [(text, score) for (_, text, score) in result if score >= min_confidence]
    if not filtered:
        return "", 0.0

    raw_text = " ".join(t for t, _ in filtered)
    avg_conf = sum(c for _, c in filtered) / len(filtered)
    return raw_text, avg_conf


def _run_tesseract(img: np.ndarray, min_confidence: float = 0.4) -> tuple[str, float]:
    """
    Run Tesseract via pytesseract.image_to_data() for per-word confidence filtering.
    Tesseract confidence is 0–100 int; normalised to 0.0–1.0 here.
    """
    import pytesseract
    from pytesseract import Output

    pil_img = Image.fromarray(img)
    data = pytesseract.image_to_data(pil_img, output_type=Output.DICT)

    words: list[str] = []
    confidences: list[float] = []

    for text, conf in zip(data["text"], data["conf"]):
        conf_int = int(conf)
        if conf_int < 0:
            # -1 = no confidence data (whitespace / empty block)
            continue
        conf_norm = conf_int / 100.0
        if conf_norm < min_confidence:
            continue
        word = text.strip()
        if word:
            words.append(word)
            confidences.append(conf_norm)

    if not words:
        return "", 0.0

    return " ".join(words), sum(confidences) / len(confidences)


def _run_ocr(img: np.ndarray, min_confidence: float = 0.4) -> tuple[str, float]:
    """Dispatch to the active engine with a graceful error boundary."""
    try:
        if ENGINE == "rapidocr":
            return _run_rapidocr(img, min_confidence)
        return _run_tesseract(img, min_confidence)
    except Exception as exc:
        logger.error("OCR failed (%s): %s", ENGINE, exc)
        return "", 0.0


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
    front_arr = preprocess_for_ocr(front_bytes)
    back_arr = preprocess_for_ocr(back_bytes)

    front_raw, front_conf = _run_ocr(front_arr, min_confidence)
    back_raw, back_conf = _run_ocr(back_arr, min_confidence)

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
