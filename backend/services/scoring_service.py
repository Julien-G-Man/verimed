"""
Deterministic weighted scoring service.
All weights and thresholds are loaded from rules.json — never hardcoded here.
"""
import json
import logging
import os
import re
from functools import lru_cache

from config import settings
from models import BarcodeResult, ExtractedFields, MatchResult, ScoringResult, ScoringSignal

logger = logging.getLogger(__name__)


_UNKNOWN_REF_VALUES = {"", "unknown", "none", "n/a", "na", "not available", "nil"}


def _barcode_candidates(value: str | None) -> set[str]:
    if not value:
        return set()

    raw = value.strip()
    if not raw:
        return set()

    candidates = {raw}
    digits_only = re.sub(r"\D", "", raw)
    if len(digits_only) >= 8:
        candidates.add(digits_only)

    for match in re.findall(r"\d{8,14}", raw):
        candidates.add(match)

    return candidates


def _barcode_match_detail(decoded_value: str | None, expected_value: str | None) -> tuple[bool, str | None, set[str]]:
    if not decoded_value or not expected_value:
        return False, None, set()

    expected = expected_value.strip()
    if not expected:
        return False, None, set()

    candidates = _barcode_candidates(decoded_value)
    if expected in candidates:
        return True, expected, candidates

    # Handles QR payloads where expected barcode appears inside a longer string.
    for candidate in candidates:
        if expected in candidate:
            return True, candidate, candidates

    return False, None, candidates


@lru_cache(maxsize=1)
def load_rules() -> dict:
    rules_path = os.path.join(settings.data_dir, "rules.json")
    try:
        with open(rules_path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("rules.json not found at %s", rules_path)
        return {}
    except Exception as exc:
        logger.error("Failed to load rules.json: %s", exc)
        return {}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _fuzzy_field_match(extracted: str | None, reference: str | None, threshold: int = 70) -> bool:
    """Loose string similarity check for field-level matching."""
    if not extracted or not reference:
        return False
    from rapidfuzz import fuzz  # noqa: PLC0415
    return fuzz.token_set_ratio(extracted.lower(), reference.lower()) >= threshold


def _regex_valid(value: str | None, pattern: str) -> bool:
    if not value or not pattern:
        return False
    try:
        return bool(re.search(pattern, value, re.IGNORECASE))
    except re.error:
        return False


def _classify(score: int, thresholds: dict) -> str:
    low = thresholds.get("low_risk", 80)
    mid = thresholds.get("medium_risk", 50)
    if score >= low:
        return "low_risk"
    if score >= mid:
        return "medium_risk"
    return "high_risk"


def _has_reference_value(value: str | None) -> bool:
    if value is None:
        return False
    normalized = value.strip().lower()
    return normalized not in _UNKNOWN_REF_VALUES


def _fallback_weight(rules: dict, key: str, default_weight: int) -> int:
    fallback = rules.get("fallback_field_weights", {})
    if key in fallback:
        return int(fallback[key])
    return max(0, default_weight // 2)


def _signal_contribution(signal: ScoringSignal) -> int:
    if signal.passed and signal.weight > 0:
        return signal.weight
    if (not signal.passed) and signal.weight < 0:
        return signal.weight
    return 0


def _finalize_signals(signals: list[ScoringSignal]) -> int:
    total = 0
    for signal in signals:
        signal.contribution = _signal_contribution(signal)
        total += signal.contribution
    return total


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def score(
    fields: ExtractedFields,
    barcode: BarcodeResult,
    match: MatchResult,
    rules: dict | None = None,
) -> ScoringResult:
    """
    Compute a deterministic risk score.
    If no product match: classification is always "cannot_verify".
    """
    if rules is None:
        rules = load_rules()

    weights = rules.get("field_weights", {})
    penalties = rules.get("penalties", {})
    thresholds = rules.get("classification_thresholds", {"low_risk": 80, "medium_risk": 50})
    required_kw = rules.get("required_keywords_by_product", {})

    signals: list[ScoringSignal] = []
    reasons: list[str] = []

    if not match.matched or match.product is None:
        reasons.append("No matching product found in the reference dataset.")
        total_contribution = _finalize_signals(signals)
        return ScoringResult(
            raw_score=0,
            unclamped_score=0,
            normalized_score=0.0,
            classification="cannot_verify",
            signals=signals,
            total_contribution=total_contribution,
            reasons=reasons,
        )

    product = match.product
    score_val = 0

    # --- Positive signals ---

    # Product / brand name
    w = weights.get("product_name_match", 20)
    combined = f"{fields.raw_front_text} {fields.raw_back_text}"
    passed = product.brand_name.lower() in combined.lower()
    signals.append(ScoringSignal(field="product_name", passed=passed, weight=w,
                                  reason=f"Brand name '{product.brand_name}' {'found' if passed else 'not found'} in OCR text"))
    if passed:
        score_val += w
    else:
        reasons.append(f"Brand name '{product.brand_name}' was not found in the extracted text.")

    # Generic name
    w = weights.get("generic_name_match", 10)
    passed = product.generic_name.lower() in combined.lower()
    signals.append(ScoringSignal(field="generic_name", passed=passed, weight=w,
                                  reason=f"Generic name '{product.generic_name}' {'found' if passed else 'not found'}"))
    if passed:
        score_val += w
    else:
        reasons.append(f"Generic name '{product.generic_name}' was not found in the extracted text.")

    # Strength
    w = weights.get("strength_match", 15)
    if _has_reference_value(product.strength):
        passed = _fuzzy_field_match(fields.strength, product.strength)
        signals.append(ScoringSignal(field="strength", passed=passed, weight=w,
                                      reason=f"Strength match: extracted='{fields.strength}', expected='{product.strength}'"))
        if passed:
            score_val += w
        else:
            reasons.append(f"Strength mismatch or not detected (expected '{product.strength}').")
    else:
        fallback_w = _fallback_weight(rules, "strength_detected_without_reference", w)
        detected = bool(fields.strength)
        signals.append(ScoringSignal(
            field="strength_observed",
            passed=detected,
            weight=fallback_w,
            reason="Strength detected from packaging text without reference baseline"
            if detected
            else "Strength not detected and reference baseline unavailable",
        ))
        if detected:
            score_val += fallback_w

    # Dosage form
    w = weights.get("dosage_form_match", 10)
    if _has_reference_value(product.dosage_form):
        passed = bool(fields.dosage_form and fields.dosage_form.lower() in product.dosage_form.lower())
        signals.append(ScoringSignal(field="dosage_form", passed=passed, weight=w,
                                      reason=f"Dosage form: extracted='{fields.dosage_form}', expected='{product.dosage_form}'"))
        if passed:
            score_val += w
    else:
        fallback_w = _fallback_weight(rules, "dosage_form_detected_without_reference", w)
        detected = bool(fields.dosage_form)
        signals.append(ScoringSignal(
            field="dosage_form_observed",
            passed=detected,
            weight=fallback_w,
            reason="Dosage form detected from packaging text without reference baseline"
            if detected
            else "Dosage form not detected and reference baseline unavailable",
        ))
        if detected:
            score_val += fallback_w

    # Manufacturer
    w = weights.get("manufacturer_match", 15)
    if _has_reference_value(product.manufacturer):
        passed = _fuzzy_field_match(fields.manufacturer, product.manufacturer, threshold=60)
        signals.append(ScoringSignal(field="manufacturer", passed=passed, weight=w,
                                      reason=f"Manufacturer: extracted='{fields.manufacturer}', expected='{product.manufacturer}'"))
        if passed:
            score_val += w
        else:
            if not fields.manufacturer:
                pen = penalties.get("manufacturer_missing", -15)
                score_val += pen
                reasons.append("Manufacturer information is missing from the packaging text.")
                signals.append(ScoringSignal(field="manufacturer_missing", passed=False, weight=pen,
                                              reason="Manufacturer string absent — penalty applied"))
            else:
                reasons.append(f"Manufacturer '{fields.manufacturer}' does not match expected '{product.manufacturer}'.")
    else:
        fallback_w = _fallback_weight(rules, "manufacturer_detected_without_reference", w)
        detected = bool(fields.manufacturer)
        signals.append(ScoringSignal(
            field="manufacturer_observed",
            passed=detected,
            weight=fallback_w,
            reason="Manufacturer detected from packaging text without reference baseline"
            if detected
            else "Manufacturer not detected and reference baseline unavailable",
        ))
        if detected:
            score_val += fallback_w

    # Barcode decoded
    w = weights.get("barcode_decoded", 10)
    passed = barcode.decoded
    signals.append(ScoringSignal(field="barcode_decoded", passed=passed, weight=w,
                                  reason="Barcode successfully decoded" if passed else "Barcode could not be decoded"))
    if passed:
        score_val += w

    # Barcode match vs mismatch
    if barcode.decoded and barcode.value:
        matched, matched_candidate, all_candidates = _barcode_match_detail(barcode.value, product.barcode)
        logger.debug(
            "Barcode scoring check: expected=%s matched=%s matched_candidate=%s candidates=%s",
            product.barcode,
            matched,
            matched_candidate,
            sorted(all_candidates),
        )
        if matched:
            w = weights.get("barcode_match", 20)
            score_val += w
            signals.append(ScoringSignal(field="barcode_match", passed=True, weight=w,
                                          reason="Decoded barcode matches the product record"))
        elif product.barcode:
            pen = penalties.get("barcode_mismatch", -25)
            score_val += pen
            reasons.append(f"Decoded barcode '{barcode.value}' does NOT match expected '{product.barcode}'.")
            signals.append(ScoringSignal(field="barcode_mismatch", passed=False, weight=pen,
                                          reason="Barcode mismatch — strong negative signal"))

    # Expiry date valid format
    w = weights.get("expiry_valid", 10)
    passed = _regex_valid(fields.expiry_date, product.expiry_pattern)
    signals.append(ScoringSignal(field="expiry_valid", passed=passed, weight=w,
                                  reason=f"Expiry '{fields.expiry_date}' {'matches' if passed else 'does not match'} expected pattern"))
    if passed:
        score_val += w
    else:
        reasons.append("Expiry date not found or does not match the expected format.")

    # Batch number valid format
    w = weights.get("batch_valid", 5)
    passed = _regex_valid(fields.batch_number, product.batch_pattern)
    signals.append(ScoringSignal(field="batch_valid", passed=passed, weight=w,
                                  reason=f"Batch '{fields.batch_number}' {'matches' if passed else 'does not match'} expected pattern"))
    if passed:
        score_val += w

    # --- Required keyword check ---
    req_kws = required_kw.get(product.product_id, product.expected_keywords)
    missing_kws = [kw for kw in req_kws if kw.lower() not in combined.lower()]
    if missing_kws:
        pen = penalties.get("critical_keyword_missing", -10)
        for kw in missing_kws:
            score_val += pen
            reasons.append(f"Required keyword '{kw}' missing from packaging text.")
            signals.append(ScoringSignal(field="keyword_missing", passed=False, weight=pen,
                                          reason=f"Keyword '{kw}' not found"))

    # --- Spelling anomaly heuristic ---
    # Simple check: if brand name appears with unexpected characters nearby
    brand_lower = product.brand_name.lower()
    front_lower = fields.raw_front_text.lower()
    if brand_lower in front_lower:
        idx = front_lower.find(brand_lower)
        context = fields.raw_front_text[max(0, idx - 5): idx + len(product.brand_name) + 5]
        anomaly = bool(re.search(r"[^\w\s\-\.]", context))
        if anomaly:
            pen = penalties.get("spelling_anomaly", -15)
            score_val += pen
            reasons.append("Possible spelling anomaly detected near brand name.")
            signals.append(ScoringSignal(field="spelling_anomaly", passed=False, weight=pen,
                                          reason="Suspicious characters near brand name"))

    # --- Clamp and classify ---
    unclamped_score = score_val
    score_val = max(0, min(100, score_val))
    classification = _classify(score_val, thresholds)
    total_contribution = _finalize_signals(signals)

    return ScoringResult(
        raw_score=score_val,
        unclamped_score=unclamped_score,
        normalized_score=float(score_val),
        classification=classification,
        signals=signals,
        total_contribution=total_contribution,
        reasons=reasons,
    )
