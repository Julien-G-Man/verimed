import re

EXPIRY_PATTERNS: list[re.Pattern] = [
    re.compile(r"\bEXP(?:IRY)?[.]?\s*(?:DATE)?[.]?\s*(\d{2}/\d{4})\b", re.IGNORECASE),
    re.compile(r"\bEXP(?:IRY)?[.]?\s*(?:DATE)?[.]?\s*(\d{2}/\d{2})\b", re.IGNORECASE),
    re.compile(r"\bBB[DE]?[.]?\s*(\d{2}/\d{4})\b", re.IGNORECASE),
    re.compile(r"\b(\d{2}/\d{4})\b"),
    re.compile(r"\b(\d{2}/\d{2})\b"),
    re.compile(r"\b([A-Z]{3}[.]?\s?\d{4})\b"),
]

BATCH_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b(?:BATCH|LOT|LOT\s*NO[.]?|BATCH\s*NO[.]?)\s*[:\-]?\s*([A-Z0-9\-]{4,12})\b", re.IGNORECASE),
    re.compile(r"\b([A-Z]{1,3}\d{4,8})\b"),
]

STRENGTH_PATTERN = re.compile(
    r"\b(\d+(?:[.]\d+)?)\s*(mg|mcg|g|ml|iu|%|units?)\b", re.IGNORECASE
)

DOSAGE_FORMS = [
    "tablet", "tablets", "capsule", "capsules", "syrup", "suspension",
    "sachet", "sachets", "inhaler", "injection", "cream", "ointment",
    "drops", "suppository", "gel", "patch",
]

MANUFACTURER_TRIGGERS = [
    "manufactured by", "mfd by", "mfg by", "marketed by",
    "distributed by", "product of", "made by",
]
