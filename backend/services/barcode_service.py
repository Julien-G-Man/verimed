import logging

import cv2
import numpy as np

from models.models import BarcodeResult
from utils.preprocessing import preprocess_for_barcode

logger = logging.getLogger(__name__)


def _image_variants_for_decoding(raw_color: np.ndarray, preprocessed: np.ndarray | None) -> list[np.ndarray]:
    """Build multiple variants to improve decode success for both barcode and QR."""
    variants: list[np.ndarray] = []

    if preprocessed is not None:
        variants.append(preprocessed)
        variants.append(cv2.bitwise_not(preprocessed))

    gray = cv2.cvtColor(raw_color, cv2.COLOR_BGR2GRAY)
    variants.append(gray)

    # Add contrast-enhanced and binarized variants for difficult QR/barcode captures.
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    variants.append(enhanced)

    _, otsu = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variants.append(otsu)
    variants.append(cv2.bitwise_not(otsu))

    return variants


def _decode_with_pyzbar(img: np.ndarray) -> BarcodeResult | None:
    try:
        from pyzbar.pyzbar import decode
        results = decode(img)
        if not results:
            return None
        best = results[0]
        value = best.data.decode("utf-8", errors="replace")
        return BarcodeResult(decoded=True, code_type=best.type, value=value, raw_payload=value)
    except Exception as exc:
        logger.debug("pyzbar failed: %s", exc)
        return None


def _decode_with_opencv_qr(img: np.ndarray) -> BarcodeResult | None:
    try:
        detector = cv2.QRCodeDetector()
        data, _, _ = detector.detectAndDecode(img)
        if data:
            return BarcodeResult(decoded=True, code_type="QRCODE", value=data, raw_payload=data)

        ok, decoded_list, _, _ = detector.detectAndDecodeMulti(img)
        if ok and decoded_list:
            for item in decoded_list:
                if item:
                    return BarcodeResult(decoded=True, code_type="QRCODE", value=item, raw_payload=item)
    except Exception as exc:
        logger.debug("OpenCV QR failed: %s", exc)
    return None


def decode_barcode(barcode_bytes: bytes) -> BarcodeResult:
    arr = np.frombuffer(barcode_bytes, np.uint8)
    raw_color = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if raw_color is None:
        logger.warning("Could not decode barcode/QR image bytes.")
        return BarcodeResult(decoded=False)

    try:
        processed = preprocess_for_barcode(barcode_bytes)
    except Exception as exc:
        logger.warning("Barcode preprocessing failed: %s", exc)
        processed = None

    variants = _image_variants_for_decoding(raw_color, processed)

    # Try pyzbar first (handles many 1D and 2D codes including QR), then OpenCV QR fallback.
    for img in variants:
        result = _decode_with_pyzbar(img)
        if result:
            logger.info("Decoded code with pyzbar: type=%s", result.code_type)
            return result

    for img in variants:
        result = _decode_with_opencv_qr(img)
        if result:
            logger.info("Decoded code with OpenCV QR detector.")
            return result

    logger.info("No barcode/QR code decoded from uploaded image.")
    return BarcodeResult(decoded=False)
