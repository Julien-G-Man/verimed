import re
from .regex_patterns import (
    EXPIRY_PATTERNS,
    BATCH_PATTERNS,
    STRENGTH_PATTERN,
    DOSAGE_FORMS,
    MANUFACTURER_TRIGGERS,
)


def normalize_text(raw: str) -> str:
    # Normalize OCR output while preserving useful separators.
    text = raw.replace("\r", "\n")
    text = text.replace("\x0c", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_expiry(text: str) -> str | None:
    for pattern in EXPIRY_PATTERNS:
        m = pattern.search(text)
        if m:
            return m.group(1)
    return None


def extract_batch(text: str) -> str | None:
    for pattern in BATCH_PATTERNS:
        m = pattern.search(text)
        if m:
            return m.group(1).upper()
    return None


def extract_strength(text: str) -> str | None:
    m = STRENGTH_PATTERN.search(text)
    if m:
        return f"{m.group(1)}{m.group(2).lower()}"
    return None


def extract_dosage_form(text: str) -> str | None:
    lower = text.lower()
    for form in DOSAGE_FORMS:
        if form in lower:
            return form.capitalize()
    return None


def extract_manufacturer(text: str) -> str | None:
    lower = text.lower()
    for trigger in MANUFACTURER_TRIGGERS:
        idx = lower.find(trigger)
        if idx == -1:
            continue
        after = text[idx + len(trigger):idx + len(trigger) + 80]
        candidate = re.split(r"[.]", after)[0].strip(" :-")
        if len(candidate) > 3:
            return candidate
    return None


def extract_brand_name(front_text: str, known_brands: list[str] | None = None) -> str | None:
    if known_brands:
        lower = front_text.lower()
        for brand in known_brands:
            if brand.lower() in lower:
                return brand
    lines = [l.strip() for l in front_text.splitlines() if l.strip()]
    if lines:
        return lines[0]
    return None


def extract_keywords(text: str, keyword_list: list[str]) -> list[str]:
    lower = text.lower()
    return [kw for kw in keyword_list if kw.lower() in lower]


def parse_fields(
    front_text: str,
    back_text: str,
    known_brands: list[str] | None = None,
    keyword_list: list[str] | None = None,
) -> dict:
    combined = f"""{front_text}
    {back_text}"""
    return {
        "brand_name": extract_brand_name(front_text, known_brands),
        "generic_name": None,
        "strength": extract_strength(combined),
        "dosage_form": extract_dosage_form(combined),
        "manufacturer": extract_manufacturer(combined),
        "batch_number": extract_batch(combined),
        "expiry_date": extract_expiry(combined),
        "keywords_found": extract_keywords(combined, keyword_list or []),
    }
