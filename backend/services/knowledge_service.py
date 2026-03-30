"""
Keyword-based retrieval over the VeriMed platform knowledge base.

Usage:
    from services.knowledge_service import retrieve_platform_knowledge
    sections = retrieve_platform_knowledge("how does scoring work", top_k=2)
    # returns list of {"title": ..., "content": ...}
"""
import json
import logging
import os
import re
from functools import lru_cache

logger = logging.getLogger(__name__)

_KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "platform_knowledge.json")

# Words that carry no signal for matching
_STOP_WORDS = {
    "a", "an", "the", "is", "it", "in", "on", "of", "to", "do", "be",
    "and", "or", "for", "with", "this", "that", "are", "was", "has",
    "have", "i", "you", "we", "they", "my", "me", "can", "will", "what",
    "how", "why", "when", "where", "which", "who", "does", "did",
}


@lru_cache(maxsize=1)
def _load_knowledge() -> list[dict]:
    path = os.path.normpath(_KNOWLEDGE_PATH)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("sections", [])
    except Exception as exc:
        logger.error("Failed to load platform knowledge base: %s", exc)
        return []


def _tokenise(text: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return {t for t in tokens if t not in _STOP_WORDS}


def retrieve_platform_knowledge(query: str, top_k: int = 3) -> list[dict]:
    """
    Return up to `top_k` knowledge sections most relevant to `query`.
    Each returned item has keys: "title" and "content".
    Returns an empty list if the knowledge base is unavailable or no section scores > 0.
    """
    sections = _load_knowledge()
    if not sections:
        return []

    query_tokens = _tokenise(query)
    if not query_tokens:
        return []

    scored: list[tuple[int, dict]] = []
    for section in sections:
        section_keywords = set(section.get("keywords", []))
        # Also tokenise the title for additional signal
        title_tokens = _tokenise(section.get("title", ""))
        candidate_tokens = section_keywords | title_tokens
        score = len(query_tokens & candidate_tokens)
        if score > 0:
            scored.append((score, section))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [{"title": s["title"], "content": s["content"]} for _, s in scored[:top_k]]


def is_platform_question(query: str) -> bool:
    """
    Heuristic: return True when the query is likely asking about VeriMed itself
    rather than about the specific verification result in context.
    """
    platform_signals = {
        "verimed", "platform", "app", "application", "tool", "works", "work",
        "how", "what", "why", "score", "scoring", "risk", "classification",
        "dataset", "data", "privacy", "image", "upload", "ocr", "barcode",
        "limitation", "limitations", "assistant", "chat", "purpose", "overview",
        "about", "explain", "tell",
    }
    query_tokens = _tokenise(query)
    return bool(query_tokens & platform_signals)


def format_knowledge_context(sections: list[dict]) -> str:
    """Render retrieved sections as a compact block to inject into a system prompt."""
    if not sections:
        return ""
    parts = ["--- VeriMed Platform Knowledge ---"]
    for section in sections:
        parts.append(f"\n[{section['title']}]\n{section['content']}")
    parts.append("--- End of Platform Knowledge ---")
    return "\n".join(parts)
