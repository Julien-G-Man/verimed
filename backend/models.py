from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel


class ExtractedFields(BaseModel):
    brand_name: str | None = None
    generic_name: str | None = None
    strength: str | None = None
    dosage_form: str | None = None
    manufacturer: str | None = None
    batch_number: str | None = None
    expiry_date: str | None = None
    keywords_found: list[str] = []
    raw_front_text: str = ""
    raw_back_text: str = ""
    ocr_confidence_front: float = 0.0
    ocr_confidence_back: float = 0.0


class BarcodeResult(BaseModel):
    decoded: bool = False
    code_type: str | None = None
    value: str | None = None
    raw_payload: str | None = None


class ProductRecord(BaseModel):
    product_id: str
    brand_name: str
    generic_name: str
    strength: str
    dosage_form: str
    manufacturer: str
    barcode: str | None = None
    expected_keywords: list[str] = []
    expected_front_text: list[str] = []
    expected_back_text: list[str] = []
    expiry_pattern: str = ""
    batch_pattern: str = ""
    reference_image_front: str = ""
    reference_image_back: str = ""
    ghana_fda_listed: bool = False
    notes: str | None = None


class MatchResult(BaseModel):
    matched: bool = False
    product: ProductRecord | None = None
    match_method: str = "none"
    match_confidence: float = 0.0


class ScoringSignal(BaseModel):
    field: str
    passed: bool
    weight: int
    contribution: int = 0
    reason: str


class ScoringResult(BaseModel):
    raw_score: int = 0
    unclamped_score: int = 0
    normalized_score: float = 0.0
    classification: str = "cannot_verify"
    signals: list[ScoringSignal] = []
    total_contribution: int = 0
    reasons: list[str] = []


class VerificationResult(BaseModel):
    request_id: str
    timestamp: str
    identified_product: str | None = None
    matched_product_id: str | None = None
    extraction: ExtractedFields
    barcode: BarcodeResult
    match: MatchResult
    scoring: ScoringResult
    risk_score: int = 0
    classification: str = "cannot_verify"
    reasons: list[str] = []
    explanation: str = ""
    recommendation: str = ""


class DetectionBox(BaseModel):
    x: int
    y: int
    width: int
    height: int


class RealtimeDetection(BaseModel):
    product_id: str
    product_label: str
    side: str
    confidence: float
    good_matches: int
    inlier_matches: int
    box: DetectionBox


class RealtimeDetectionResponse(BaseModel):
    request_id: str
    timestamp: str
    side: str
    detections: list[RealtimeDetection] = []
    reference_templates_loaded: int = 0
    message: str = ""


class ConversationMessage(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: str


class ConversationCreateRequest(BaseModel):
    verification: VerificationResult


class ConversationCreateResponse(BaseModel):
    conversation_id: str
    request_id: str
    created_at: str
    verification: VerificationResult
    messages: list[ConversationMessage]


class FollowUpMessageRequest(BaseModel):
    message: str


class ConversationResponse(BaseModel):
    conversation_id: str
    request_id: str
    created_at: str
    verification: VerificationResult
    messages: list[ConversationMessage]


class ConversationSummary(BaseModel):
    conversation_id: str
    request_id: str
    created_at: str
    identified_product: str | None = None
    classification: str = "cannot_verify"
    risk_score: int = 0


def new_message(role: str, content: str, conversation_id: str) -> ConversationMessage:
    return ConversationMessage(
        id=str(uuid4()),
        conversation_id=conversation_id,
        role=role,
        content=content,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
