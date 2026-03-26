import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from limiter import limiter
from models.models import VerificationResult
from services.barcode_service import decode_barcode
from services.explanation_service import generate_explanation
from services.matcher_service import load_products, match_product
from services.ocr_service import extract_fields
from services.scoring_service import load_rules, score
from config import settings
from utils.preprocessing import detect_blur

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
MAX_IMAGE_SIZE_BYTES = settings.max_image_size_mb * 1024 * 1024


async def _read_and_validate(upload: UploadFile, field_name: str) -> bytes:
    content_type = (upload.content_type or "").lower().split(";")[0].strip()
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"{field_name}: unsupported file type. Use JPEG, PNG, or WEBP.",
        )
    data = await upload.read()
    if len(data) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=422,
            detail=f"{field_name}: file too large ({len(data) // 1024}KB). Maximum is 10MB.",
        )
    return data


@router.post("/verify", response_model=VerificationResult)
@limiter.limit("10/minute")
async def verify(
    request: Request,
    front_image: UploadFile = File(...),
    back_image: UploadFile = File(...),
    barcode_image: UploadFile = File(...),
):
    request_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    # 1. Read & validate
    try:
        front_bytes = await _read_and_validate(front_image, "front_image")
        back_bytes = await _read_and_validate(back_image, "back_image")
        barcode_bytes = await _read_and_validate(barcode_image, "barcode_image")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[%s] File validation error: %s", request_id, exc)
        raise HTTPException(status_code=422, detail="Could not read uploaded images.")

    # 2. Blur detection
    rules = load_rules()
    blur_threshold = rules.get("ocr", {}).get("blur_variance_threshold", 100)
    min_conf = rules.get("ocr", {}).get("min_confidence", 0.4)

    for label, img_bytes in [("front_image", front_bytes), ("back_image", back_bytes)]:
        is_blurry, variance = detect_blur(img_bytes, threshold=blur_threshold)
        if is_blurry:
            logger.warning(
                "[%s] Blur validation failed for %s (variance=%.2f, threshold=%s)",
                request_id,
                label,
                variance,
                blur_threshold,
            )
            raise HTTPException(
                status_code=400,
                detail=f"{label} is too blurry (variance={variance:.1f}). Please retake the photo.",
            )

    # 3. Gather keywords for OCR scan
    products = load_products()
    all_keywords = list({kw for p in products for kw in p.expected_keywords})
    all_brands = [p.brand_name for p in products]

    # 4. OCR extraction
    try:
        extraction = extract_fields(
            front_bytes=front_bytes,
            back_bytes=back_bytes,
            min_confidence=min_conf,
            known_brands=all_brands,
            keyword_list=all_keywords,
        )
    except Exception as exc:
        logger.error("[%s] OCR failed: %s", request_id, exc)
        raise HTTPException(status_code=500, detail="OCR extraction failed. Please try again.")

    # 5. Barcode decoding
    try:
        barcode_result = decode_barcode(barcode_bytes)
    except Exception as exc:
        logger.error("[%s] Barcode decode error: %s", request_id, exc)
        from models.models import BarcodeResult
        barcode_result = BarcodeResult(decoded=False)

    # 6. Product matching
    fuzzy_cutoff = rules.get("matching", {}).get("fuzzy_cutoff_score", 60)
    fuzzy_threshold = rules.get("matching", {}).get("fuzzy_confidence_threshold", 0.55)
    try:
        match_result = match_product(
            fields=extraction,
            barcode=barcode_result,
            fuzzy_cutoff=fuzzy_cutoff,
            fuzzy_confidence_threshold=fuzzy_threshold,
        )
    except Exception as exc:
        logger.error("[%s] Matching failed: %s", request_id, exc)
        from models.models import MatchResult
        match_result = MatchResult(matched=False, match_method="none", match_confidence=0.0)

    # 7. Scoring
    try:
        scoring_result = score(
            fields=extraction,
            barcode=barcode_result,
            match=match_result,
            rules=rules,
        )
    except Exception as exc:
        logger.error("[%s] Scoring failed: %s", request_id, exc)
        from models.models import ScoringResult
        scoring_result = ScoringResult(
            raw_score=0,
            normalized_score=0.0,
            classification="cannot_verify",
            reasons=["Scoring error."],
        )

    identified_product = None
    matched_product_id = None
    if match_result.matched and match_result.product:
        p = match_result.product
        identified_product = f"{p.brand_name} {p.strength} {p.dosage_form}".strip()
        matched_product_id = p.product_id

    if match_result.matched and match_result.product and not extraction.generic_name:
        extraction.generic_name = match_result.product.generic_name

    # 8. LLM explanation
    result_data = {
        "identified_product": identified_product,
        "risk_score": scoring_result.raw_score,
        "classification": scoring_result.classification,
        "reasons": scoring_result.reasons,
    }
    try:
        explanation, recommendation = generate_explanation(result_data)
    except Exception as exc:
        logger.error("[%s] Explanation error: %s", request_id, exc)
        explanation = "Risk assessment complete. Consult a pharmacist before use."
        recommendation = "Consult a pharmacist before use."

    # 9. Assemble response
    return VerificationResult(
        request_id=request_id,
        timestamp=timestamp,
        identified_product=identified_product,
        matched_product_id=matched_product_id,
        extraction=extraction,
        barcode=barcode_result,
        match=match_result,
        scoring=scoring_result,
        risk_score=scoring_result.raw_score,
        classification=scoring_result.classification,
        reasons=scoring_result.reasons,
        explanation=explanation,
        recommendation=recommendation,
    )
