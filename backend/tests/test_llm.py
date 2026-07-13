"""Tests for the LLM classifier orchestration and its heuristic fallback."""

import pytest

from app import classifier, config, llm


@pytest.fixture()
def llm_enabled(monkeypatch):
    """Turn the LLM path on with a dummy key (no real network calls)."""
    monkeypatch.setattr(config, "LLM_CLASSIFIER_ENABLED", True)
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "test-key")


SAMPLE = {
    "subject": "Next steps with Databricks",
    "sender": "Priya <priya@databricks.com>",
    "snippet": "We'd love to schedule a phone screen.",
}


def test_smart_classify_uses_heuristic_when_disabled():
    result = llm.smart_classify(**SAMPLE)
    assert result["source"] == "heuristic"
    # Matches the deterministic classifier output.
    baseline = classifier.classify(**SAMPLE)
    assert result["detected_status"] == baseline["detected_status"]
    assert result["is_job_related"] == baseline["is_job_related"]


def test_smart_classify_uses_llm_when_available(llm_enabled, monkeypatch):
    def fake_call(subject, sender, snippet):
        return {"is_job_related": True, "status": "offer", "company": "Acme"}

    monkeypatch.setattr(llm, "_call_anthropic", fake_call)
    result = llm.smart_classify(**SAMPLE)
    assert result["source"] == "llm"
    assert result["is_job_related"] is True
    assert result["detected_status"] == "offer"
    assert result["company_guess"] == "Acme"


def test_smart_classify_falls_back_when_llm_errors(llm_enabled, monkeypatch):
    def boom(subject, sender, snippet):
        raise llm.LLMError("upstream 500")

    monkeypatch.setattr(llm, "_call_anthropic", boom)
    result = llm.smart_classify(**SAMPLE)
    assert result["source"] == "heuristic"
    assert result["detected_status"] == "interview"


def test_normalize_blanks_status_and_company_for_non_job():
    out = llm._normalize({"is_job_related": False, "status": "offer", "company": "X"})
    assert out == {
        "is_job_related": False,
        "detected_status": None,
        "company_guess": None,
    }


def test_normalize_rejects_unknown_status():
    out = llm._normalize({"is_job_related": True, "status": "ghosted", "company": ""})
    assert out["detected_status"] is None
    assert out["company_guess"] is None


def test_extract_tool_input_reads_tool_use_block():
    response = {
        "content": [
            {"type": "text", "text": "ok"},
            {
                "type": "tool_use",
                "name": "record_email_classification",
                "input": {"is_job_related": True, "status": "applied", "company": "Y"},
            },
        ]
    }
    assert llm._extract_tool_input(response)["status"] == "applied"


def test_extract_tool_input_raises_without_tool_use():
    with pytest.raises(llm.LLMError):
        llm._extract_tool_input({"content": [{"type": "text", "text": "hi"}]})
