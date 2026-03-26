from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache

import cv2
import numpy as np

from config import settings
from models.models import DetectionBox, RealtimeDetection, RealtimeDetectionResponse
from services.matcher_service import load_products

logger = logging.getLogger(__name__)

SUPPORTED_SIDES = {"front", "back", "barcode", "qr", "qr/barcode", "qr-barcode"}


def _normalize_side(side: str) -> str:
    value = (side or "").lower().strip()
    if value in {"front", "back"}:
        return value
    if value in {"barcode", "qr", "qr/barcode", "qr-barcode"}:
        # Reuse back references when side is code-focused. This keeps endpoint
        # compatible while reference-template strategy stays front/back only.
        return "back"
    raise ValueError("side must be one of: front, back, barcode, qr, qr/barcode")


@dataclass(frozen=True)
class _Template:
    product_id: str
    product_label: str
    side: str
    width: int
    height: int
    keypoints: tuple
    descriptors: np.ndarray


_ORB = cv2.ORB_create(nfeatures=1200, fastThreshold=7)
_BF = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)


def _decode_image(image_bytes: bytes) -> np.ndarray:
    arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Invalid image payload")
    return img


def _preprocess_gray(img: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    return gray


def _make_label(brand: str, strength: str, dosage: str) -> str:
    return " ".join(part for part in [brand, strength, dosage] if part).strip()


@lru_cache(maxsize=1)
def load_reference_templates() -> tuple[_Template, ...]:
    templates: list[_Template] = []
    products = load_products()
    ref_dir = os.path.join(settings.data_dir, "reference_images")

    for product in products:
        for side in ("front", "back"):
            file_name = product.reference_image_front if side == "front" else product.reference_image_back
            if not file_name:
                continue

            path = os.path.join(ref_dir, file_name)
            if not os.path.exists(path):
                logger.debug("Reference image missing for %s (%s): %s", product.product_id, side, path)
                continue

            img = cv2.imread(path, cv2.IMREAD_COLOR)
            if img is None:
                logger.warning("Could not read reference image: %s", path)
                continue

            gray = _preprocess_gray(img)
            keypoints, descriptors = _ORB.detectAndCompute(gray, None)
            if descriptors is None or len(keypoints) < 12:
                logger.debug("Not enough features for reference image: %s", path)
                continue

            templates.append(
                _Template(
                    product_id=product.product_id,
                    product_label=_make_label(product.brand_name, product.strength, product.dosage_form),
                    side=side,
                    width=gray.shape[1],
                    height=gray.shape[0],
                    keypoints=tuple(keypoints),
                    descriptors=descriptors,
                )
            )

    logger.info("Loaded %d realtime CV reference templates", len(templates))
    return tuple(templates)


def _compute_iou(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    inter_w = max(0, inter_x2 - inter_x1)
    inter_h = max(0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h

    if inter_area == 0:
        return 0.0

    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)
    union = area_a + area_b - inter_area
    if union <= 0:
        return 0.0
    return inter_area / union


def _nms(detections: list[dict], iou_threshold: float = 0.35) -> list[dict]:
    kept: list[dict] = []
    for det in sorted(detections, key=lambda item: item["confidence"], reverse=True):
        box = det["rect"]
        should_keep = True
        for kept_item in kept:
            if _compute_iou(box, kept_item["rect"]) > iou_threshold:
                should_keep = False
                break
        if should_keep:
            kept.append(det)
    return kept


def detect_products_in_frame(
    frame_bytes: bytes,
    side: str = "front",
    top_k: int = 3,
    min_confidence: float = 0.35,
) -> RealtimeDetectionResponse:
    side = _normalize_side(side)

    frame = _decode_image(frame_bytes)
    frame_gray = _preprocess_gray(frame)
    frame_kp, frame_desc = _ORB.detectAndCompute(frame_gray, None)
    templates = load_reference_templates()

    if frame_desc is None or len(frame_kp) < 12:
        return RealtimeDetectionResponse(
            request_id="",
            timestamp=datetime.now(timezone.utc).isoformat(),
            side=side,
            detections=[],
            reference_templates_loaded=len(templates),
            message="Not enough frame features detected. Move closer and improve lighting.",
        )

    candidates: list[dict] = []

    for template in templates:
        if template.side != side:
            continue

        knn = _BF.knnMatch(template.descriptors, frame_desc, k=2)
        good = []
        for pair in knn:
            if len(pair) < 2:
                continue
            m, n = pair
            if m.distance < 0.75 * n.distance:
                good.append(m)

        if len(good) < 14:
            continue

        src_pts = np.float32([template.keypoints[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        dst_pts = np.float32([frame_kp[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

        homography, inlier_mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        if homography is None or inlier_mask is None:
            continue

        inliers = int(inlier_mask.ravel().sum())
        if inliers < 10:
            continue

        corners = np.float32(
            [[0, 0], [template.width - 1, 0], [template.width - 1, template.height - 1], [0, template.height - 1]]
        ).reshape(-1, 1, 2)
        projected = cv2.perspectiveTransform(corners, homography).reshape(-1, 2)

        xs = projected[:, 0]
        ys = projected[:, 1]

        x1 = int(max(0, np.floor(xs.min())))
        y1 = int(max(0, np.floor(ys.min())))
        x2 = int(min(frame.shape[1] - 1, np.ceil(xs.max())))
        y2 = int(min(frame.shape[0] - 1, np.ceil(ys.max())))

        if x2 <= x1 or y2 <= y1:
            continue

        inlier_ratio = inliers / max(1, len(good))
        confidence = min(0.99, (0.55 * min(1.0, len(good) / 80.0)) + (0.45 * inlier_ratio))

        if confidence < min_confidence:
            continue

        candidates.append(
            {
                "product_id": template.product_id,
                "product_label": template.product_label,
                "side": template.side,
                "confidence": round(float(confidence), 3),
                "good_matches": len(good),
                "inlier_matches": inliers,
                "rect": (x1, y1, x2, y2),
            }
        )

    suppressed = _nms(candidates)

    results: list[RealtimeDetection] = []
    for det in suppressed[:max(1, top_k)]:
        x1, y1, x2, y2 = det["rect"]
        results.append(
            RealtimeDetection(
                product_id=det["product_id"],
                product_label=det["product_label"],
                side=det["side"],
                confidence=det["confidence"],
                good_matches=det["good_matches"],
                inlier_matches=det["inlier_matches"],
                box=DetectionBox(x=x1, y=y1, width=x2 - x1, height=y2 - y1),
            )
        )

    message = "ok" if results else "No confident product detection in this frame yet."

    return RealtimeDetectionResponse(
        request_id="",
        timestamp=datetime.now(timezone.utc).isoformat(),
        side=side,
        detections=results,
        reference_templates_loaded=len(templates),
        message=message,
    )
