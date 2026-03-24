"""
LLM explanation service — one call per request, max_tokens=200.
If the LLM call fails for any reason, a hardcoded fallback is returned.
The LLM is NEVER responsible for scoring — only for producing plain-language summaries.
"""
import json
import logging

from services.llm_client import complete as llm_complete

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a medicine safety assistant. "
    "Summarize risk assessment results in 2–4 plain sentences. "
    "Never say a product is definitely real or definitely fake. "
    "Always advise consulting a pharmacist or healthcare professional."
)

FALLBACK_EXPLANATIONS = {
    "low_risk": (
        "The scanned packaging shows strong consistency with the reference data for this product. "
        "The barcode, text fields, and key identifiers all appear to match. "
        "While this is a positive sign, no verification tool can guarantee authenticity. "
        "Consult a pharmacist if you have any doubts."
    ),
    "medium_risk": (
        "Some aspects of the packaging are consistent with the expected product, "
        "but there are a number of discrepancies that could not be explained. "
        "Exercise caution and consult a pharmacist before using this medicine."
    ),
    "high_risk": (
        "Significant inconsistencies were detected in the packaging. "
        "This product could not be reliably matched to any verified reference data, "
        "or key identifiers were mismatched. "
        "Do not use this medicine without first consulting a pharmacist or healthcare professional."
    ),
    "cannot_verify": (
        "This product could not be matched against any entry in the reference dataset. "
        "This does not confirm the product is counterfeit, but it cannot be verified as genuine. "
        "Please consult a pharmacist before use."
    ),
}

RECOMMENDATIONS = {
    "low_risk": "This product appears consistent with reference data. Verify with a pharmacist if uncertain.",
    "medium_risk": "Consult a pharmacist before use — several signals require further verification.",
    "high_risk": "Do not use this medicine. Seek advice from a pharmacist or healthcare provider immediately.",
    "cannot_verify": "This product cannot be verified. Consult a pharmacist before use.",
}


FOLLOW_UP_SYSTEM_PROMPT = (
    "You are a medicine safety assistant answering follow-up questions about a previous risk assessment. "
    "Use only the provided assessment context and chat history. "
    "Be transparent about uncertainty, never claim a medicine is definitely real or definitely fake, "
    "and always include a short pharmacist-safety reminder."
)


def _build_user_message(result_data: dict) -> str:
    payload = {
        "identified_product": result_data.get("identified_product"),
        "risk_score": result_data.get("risk_score"),
        "classification": result_data.get("classification"),
        "reasons": result_data.get("reasons", []),
    }
    return json.dumps(payload, ensure_ascii=False)


def generate_explanation(result_data: dict) -> tuple[str, str]:
    """
    Generate a plain-language explanation via the LLM client (NVIDIA → Anthropic).
    Returns (explanation_text, recommendation_text).
    Falls back to hardcoded strings if all LLM providers fail.
    """
    classification = result_data.get("classification", "cannot_verify")
    recommendation = RECOMMENDATIONS.get(classification, RECOMMENDATIONS["cannot_verify"])

    try:
        user_msg = _build_user_message(result_data)
        explanation = llm_complete(SYSTEM_PROMPT, user_msg, max_tokens=200)
        return explanation, recommendation
    except Exception as exc:
        logger.error("LLM explanation call failed: %s — using fallback.", exc)
        return FALLBACK_EXPLANATIONS.get(classification, FALLBACK_EXPLANATIONS["cannot_verify"]), recommendation


def generate_follow_up_answer(verification_summary: dict, history: list[dict], user_message: str) -> str:
    payload = {
        "verification": verification_summary,
        "history": history[-8:],
        "user_message": user_message,
    }
    try:
        return llm_complete(
            FOLLOW_UP_SYSTEM_PROMPT,
            json.dumps(payload, ensure_ascii=False),
            max_tokens=220,
        )
    except Exception as exc:
        logger.error("LLM follow-up call failed: %s — using fallback.", exc)
        classification = verification_summary.get("classification", "cannot_verify")
        fallback = FALLBACK_EXPLANATIONS.get(classification, FALLBACK_EXPLANATIONS["cannot_verify"])
        return f"{fallback} Please consult a pharmacist for personalized advice."
