import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from config import settings
from models import RealtimeDetectionResponse
from services.realtime_cv_service import detect_products_in_frame

router = APIRouter()

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
MAX_IMAGE_SIZE_BYTES = settings.max_image_size_mb * 1024 * 1024


async def _read_frame(upload: UploadFile) -> bytes:
    content_type = (upload.content_type or "").lower().split(";")[0].strip()
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=422,
            detail="frame_image: unsupported file type. Use JPEG, PNG, or WEBP.",
        )

    frame_bytes = await upload.read()
    if len(frame_bytes) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=422,
            detail=f"frame_image: file too large ({len(frame_bytes) // 1024}KB). Maximum is 10MB.",
        )
    return frame_bytes


@router.post("/realtime/detect", response_model=RealtimeDetectionResponse)
async def realtime_detect(
    frame_image: UploadFile = File(...),
    side: str = Form("front"),
    top_k: int = Form(3),
):
    request_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    frame_bytes = await _read_frame(frame_image)
    top_k = max(1, min(top_k, 5))

    try:
        detection = detect_products_in_frame(
            frame_bytes=frame_bytes,
            side=side,
            top_k=top_k,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception:
        raise HTTPException(status_code=500, detail="Realtime CV detection failed.")

    return detection.model_copy(
        update={
            "request_id": request_id,
            "timestamp": timestamp,
        }
    )
