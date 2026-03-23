import logging

import cv2
import numpy as np

from models import BarcodeResult
from utils.preprocessing import preprocess_for_barcode

logger = logging.getLogger(__name__)


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
    except Exception as exc:
        logger.debug("OpenCV QR failed: %s", exc)
    return None


def decode_barcode(barcode_bytes: bytes) -> BarcodeResult:
    try:
        processed = preprocess_for_barcode(barcode_bytes)
    except Exception as exc:
        logger.warning("Barcode preprocessing failed: %s", exc)
        processed = None

    if processed is not None:
        result = _decode_with_pyzbar(processed)
        if result:
            return result

    try:
        arr = np.frombuffer(barcode_bytes, np.uint8)
        raw_img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
        if raw_img is not None:
            result = _decode_with_pyzbar(raw_img)
            if result:
                return result
        raw_color = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if raw_color is not None:
            result = _decode_with_opencv_qr(raw_color)
            if result:
                return result
    except Exception as exc:
        logger.debug("Raw barcode decode failed: %s", exc)

    return BarcodeResult(decoded=False)
