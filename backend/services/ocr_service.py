"""
OCR service using Tesseract (pytesseract) as primary.
Tesseract is a C binary — no ML framework sits in Python memory,
keeping the process well within the 512MB Render free-tier limit.
Per-word confidence filtering is applied via image_to_data().
"""
import logging

import numpy as np
from PIL import Image

from models.models import ExtractedFields
from utils.normalization import normalize_text, parse_fields
from utils.preprocessing import preprocess_for_ocr

logger = logging.getLogger(__name__)


def _run_tesseract(img: np.ndarray, min_confidence: float = 0.4) -> tuple[str, float]:
    """
    Run Tesseract OCR on a preprocessed numpy image.
    Uses image_to_data() to filter per-word confidence scores.
    Returns (raw_text, avg_confidence) where confidence is 0.0–1.0.
    """
    try:
        import pytesseract
        from pytesseract import Output

        pil_img = Image.fromarray(img)
        data = pytesseract.image_to_data(pil_img, output_type=Output.DICT)

        words: list[str] = []
        confidences: list[float] = []

        for text, conf in zip(data["text"], data["conf"]):
            conf_int = int(conf)
            if conf_int < 0:
                # -1 means no confidence data (whitespace, empty block)
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

    except Exception as exc:
        logger.error("Tesseract OCR failed: %s", exc)
        return "", 0.0


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

    front_raw, front_conf = _run_tesseract(front_arr, min_confidence)
    back_raw, back_conf = _run_tesseract(back_arr, min_confidence)

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
