"""
Multi-provider LLM client.

Providers are tried in preference order: NVIDIA → Anthropic Claude.
Each provider raises on failure; if all fail, RuntimeError is raised.

Usage:
    from services.llm_client import complete
    text = complete(system_prompt, user_message, max_tokens=200)
"""
import logging

from config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Provider implementations
# ---------------------------------------------------------------------------

def _call_nvidia(system: str, user: str, max_tokens: int) -> str:
    if not settings.nvidia_openai_api_key:
        raise ValueError("NVIDIA_OPENAI_API_KEY not configured")

    import httpx  # noqa: PLC0415

    response = httpx.post(
        settings.nvidia_openai_api_url,
        headers={
            "Authorization": f"Bearer {settings.nvidia_openai_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": settings.nvidia_openai_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": max_tokens,
        },
        timeout=15.0,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def _call_anthropic(system: str, user: str, max_tokens: int) -> str:
    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY not configured")

    import anthropic  # noqa: PLC0415

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return message.content[0].text.strip()


# ---------------------------------------------------------------------------
# Provider registry — order = preference
# ---------------------------------------------------------------------------

_PROVIDERS: list[tuple[str, object]] = [
    ("nvidia", _call_nvidia),
    ("anthropic", _call_anthropic),
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def complete(system: str, user: str, max_tokens: int = 200) -> str:
    """
    Call LLM providers in preference order, returning the first success.
    Raises RuntimeError if every provider fails.
    """
    last_exc: Exception | None = None
    for name, fn in _PROVIDERS:
        try:
            result = fn(system, user, max_tokens)
            logger.info("LLM response received from provider '%s'", name)
            return result
        except Exception as exc:
            logger.warning("LLM provider '%s' failed: %s", name, exc)
            last_exc = exc

    raise RuntimeError(f"All LLM providers failed. Last error: {last_exc}") from last_exc
