import cv2
import numpy as np


def _load_image(image_bytes: bytes) -> np.ndarray:
    arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image bytes")
    return img


def _resize_to_max_edge(img: np.ndarray, max_edge: int = 1600) -> np.ndarray:
    h, w = img.shape[:2]
    if max(h, w) <= max_edge:
        return img
    scale = max_edge / max(h, w)
    return cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)


def detect_blur(image_bytes: bytes, threshold: float = 100.0) -> tuple[bool, float]:
    img = _load_image(image_bytes)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    return variance < threshold, variance


def preprocess_for_ocr(image_bytes: bytes) -> np.ndarray:
    img = _load_image(image_bytes)
    img = _resize_to_max_edge(img, 1600)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    blurred = cv2.GaussianBlur(gray, (0, 0), 3)
    gray = cv2.addWeighted(gray, 1.5, blurred, -0.5, 0)
    if float(gray.mean()) < 80:
        _, gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return gray


def preprocess_for_barcode(image_bytes: bytes) -> np.ndarray:
    img = _load_image(image_bytes)
    h, w = img.shape[:2]
    target_w = 800
    scale = target_w / w
    img = cv2.resize(img, (target_w, int(h * scale)), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.fastNlMeansDenoising(gray, h=10)
    lap = cv2.Laplacian(gray, cv2.CV_64F)
    lap = np.clip(lap, 0, 255).astype(np.uint8)
    gray = cv2.addWeighted(gray, 1.0, lap, 0.5, 0)
    gray = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=11,
        C=2,
    )
    return gray
