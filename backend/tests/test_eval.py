"""Tests for the classifier evaluation harness and the labeled dataset."""

from eval import evaluate

VALID_STATUSES = {"applied", "interview", "offer", "rejected", None}


def test_dataset_is_well_formed():
    rows = evaluate.load_dataset()
    assert len(rows) >= 30
    for row in rows:
        assert set(row) >= {"subject", "sender", "snippet", "is_job_related", "status"}
        assert isinstance(row["is_job_related"], bool)
        assert row["status"] in VALID_STATUSES
        # A non-job email must not carry a status label.
        if not row["is_job_related"]:
            assert row["status"] is None


def test_heuristic_meets_baseline_on_dataset():
    rows = evaluate.load_dataset()
    metrics = evaluate.evaluate_predictions(rows, evaluate.heuristic_predict)
    # Guardrails so a regression in the heuristic is caught by CI.
    assert metrics["job_accuracy"] >= 0.80
    assert metrics["job_recall"] >= 0.90
    assert metrics["status_accuracy"] >= 0.85


def test_evaluate_predictions_math():
    rows = [
        {"is_job_related": True, "status": "offer", "subject": "", "sender": "", "snippet": ""},
        {"is_job_related": False, "status": None, "subject": "", "sender": "", "snippet": ""},
    ]

    def perfect(row):
        return {
            "is_job_related": row["is_job_related"],
            "detected_status": row["status"],
        }

    metrics = evaluate.evaluate_predictions(rows, perfect)
    assert metrics["job_accuracy"] == 1.0
    assert metrics["job_f1"] == 1.0
    assert metrics["status_accuracy"] == 1.0
