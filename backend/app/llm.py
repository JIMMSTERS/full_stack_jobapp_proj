"""LLM-backed email classifier with a deterministic heuristic fallback.

The LLM path calls Anthropic's Messages API and forces a structured tool call so
the model returns a strict JSON object (no free-text parsing). If the LLM is
disabled, unconfigured, or errors for any reason, ``smart_classify`` falls back
to the keyword heuristic in :mod:`app.classifier` so the feature degrades
gracefully and the app never hard-depends on an external service.

Only ``httpx`` is used (already a dependency) — no vendor SDK — which keeps the
surface small and easy to test by monkeypatching a single network function.
"""

from __future__ import annotations

import httpx

from app import classifier, config

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

VALID_STATUSES = {"applied", "interview", "offer", "rejected"}

# Tool schema that constrains the model to a strict, machine-readable output.
_CLASSIFY_TOOL = {
    "name": "record_email_classification",
    "description": "Record the structured classification of a single email.",
    "input_schema": {
        "type": "object",
        "properties": {
            "is_job_related": {
                "type": "boolean",
                "description": "True if the email concerns a job/internship application.",
            },
            "status": {
                "type": "string",
                "enum": ["applied", "interview", "offer", "rejected", "none"],
                "description": (
                    "The application stage this email indicates, or 'none' if the "
                    "email doesn't clearly signal a stage. Use 'rejected' for "
                    "declines, 'offer' for offers, 'interview' for screens/"
                    "assessments/scheduling, 'applied' for received-application "
                    "confirmations."
                ),
            },
            "company": {
                "type": "string",
                "description": "The hiring company's name, or empty string if unknown.",
            },
        },
        "required": ["is_job_related", "status", "company"],
    },
}

_SYSTEM_PROMPT = (
    "You classify emails for a job-application tracker. Decide whether an email "
    "is related to the recipient's job or internship applications, infer which "
    "application stage it represents, and extract the hiring company. Recruiting "
    "marketing blasts and job-board digests are NOT application-related. Always "
    "respond by calling the record_email_classification tool."
)


class LLMError(Exception):
    """Raised when the LLM call fails or returns an unusable response."""


def _user_content(subject: str, sender: str, snippet: str) -> str:
    return (
        f"From: {sender or '(unknown)'}\n"
        f"Subject: {subject or '(no subject)'}\n"
        f"Body preview: {snippet or '(none)'}"
    )


def _extract_tool_input(response_json: dict) -> dict:
    """Pull the tool-call arguments out of an Anthropic Messages response."""
    for block in response_json.get("content", []):
        if block.get("type") == "tool_use" and block.get("name") == _CLASSIFY_TOOL["name"]:
            payload = block.get("input")
            if isinstance(payload, dict):
                return payload
    raise LLMError("No tool_use block in LLM response")


def _normalize(payload: dict) -> dict:
    """Coerce raw tool output into the classifier's dict contract."""
    is_job_related = bool(payload.get("is_job_related"))
    raw_status = (payload.get("status") or "none").strip().lower()
    status = raw_status if raw_status in VALID_STATUSES else None
    company = (payload.get("company") or "").strip() or None
    return {
        "is_job_related": is_job_related,
        "detected_status": status if is_job_related else None,
        "company_guess": company if is_job_related else None,
    }


def _call_anthropic(subject: str, sender: str, snippet: str) -> dict:
    """Call the Anthropic API and return the raw tool-input dict.

    Isolated so tests can monkeypatch this single function to avoid network I/O.
    """
    headers = {
        "x-api-key": config.ANTHROPIC_API_KEY,
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json",
    }
    body = {
        "model": config.LLM_MODEL,
        "max_tokens": 256,
        "system": _SYSTEM_PROMPT,
        "tools": [_CLASSIFY_TOOL],
        "tool_choice": {"type": "tool", "name": _CLASSIFY_TOOL["name"]},
        "messages": [
            {"role": "user", "content": _user_content(subject, sender, snippet)}
        ],
    }
    try:
        response = httpx.post(
            ANTHROPIC_URL,
            headers=headers,
            json=body,
            timeout=config.LLM_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise LLMError(f"Anthropic request failed: {exc}") from exc

    return _extract_tool_input(response.json())


def classify_email(subject: str, sender: str, snippet: str = "") -> dict:
    """Classify one email with the LLM. Raises ``LLMError`` on failure."""
    raw = _call_anthropic(subject, sender, snippet)
    return _normalize(raw)


def llm_available() -> bool:
    """True when the LLM classifier is switched on and has an API key."""
    return bool(config.LLM_CLASSIFIER_ENABLED and config.ANTHROPIC_API_KEY)


def smart_classify(subject: str, sender: str, snippet: str = "") -> dict:
    """Classify an email, preferring the LLM and falling back to the heuristic.

    The returned dict matches :func:`app.classifier.classify` plus a ``source``
    key (``"llm"`` or ``"heuristic"``) so callers/UI can show provenance.
    """
    if llm_available():
        try:
            result = classify_email(subject, sender, snippet)
            result["source"] = "llm"
            return result
        except LLMError:
            pass  # fall through to the deterministic heuristic

    result = classifier.classify(subject, sender, snippet)
    result["source"] = "heuristic"
    return result
