"""Offline evaluation harness for the email classifier.

Runs the classifier(s) over a hand-labeled dataset and reports how well each
does at (a) the binary "is this job-related?" decision and (b) inferring the
application status. Lets us quantify the heuristic baseline and measure any lift
from the LLM instead of eyeballing it.

Usage (from the ``backend`` directory)::

    python -m eval.evaluate                 # heuristic baseline
    python -m eval.evaluate --model llm      # LLM (needs ANTHROPIC_API_KEY)
    python -m eval.evaluate --model both     # compare side by side
"""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Callable
from typing import Any

from app import classifier, llm

DATASET_PATH = os.path.join(os.path.dirname(__file__), "dataset.jsonl")

Predict = Callable[[dict[str, Any]], dict[str, Any]]


def load_dataset(path: str = DATASET_PATH) -> list[dict[str, Any]]:
    """Load the labeled examples from a JSONL file."""
    rows: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def evaluate_predictions(rows: list[dict[str, Any]], predict: Predict) -> dict[str, float]:
    """Score a prediction function against the gold labels.

    Returns binary is_job_related metrics plus status accuracy (measured only on
    truly job-related emails, where a status label is meaningful).
    """
    tp = fp = fn = tn = 0
    status_total = status_correct = 0

    for row in rows:
        pred = predict(row)
        gold_job = bool(row["is_job_related"])
        pred_job = bool(pred["is_job_related"])

        if gold_job and pred_job:
            tp += 1
        elif gold_job and not pred_job:
            fn += 1
        elif not gold_job and pred_job:
            fp += 1
        else:
            tn += 1

        if gold_job:
            status_total += 1
            gold_status = row["status"] or "none"
            pred_status = pred.get("detected_status") or "none"
            if gold_status == pred_status:
                status_correct += 1

    n = len(rows) or 1
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {
        "n": len(rows),
        "job_accuracy": (tp + tn) / n,
        "job_precision": precision,
        "job_recall": recall,
        "job_f1": f1,
        "status_accuracy": status_correct / status_total if status_total else 0.0,
    }


def heuristic_predict(row: dict[str, Any]) -> dict[str, Any]:
    return classifier.classify(row["subject"], row["sender"], row["snippet"])


def llm_predict(row: dict[str, Any]) -> dict[str, Any]:
    return llm.classify_email(row["subject"], row["sender"], row["snippet"])


def _format_report(name: str, metrics: dict[str, float]) -> str:
    return (
        f"\n{name}  (n={metrics['n']})\n"
        f"  is_job_related  acc={metrics['job_accuracy']:.3f}  "
        f"P={metrics['job_precision']:.3f}  R={metrics['job_recall']:.3f}  "
        f"F1={metrics['job_f1']:.3f}\n"
        f"  status          acc={metrics['status_accuracy']:.3f}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the email classifier.")
    parser.add_argument(
        "--model",
        choices=["heuristic", "llm", "both"],
        default="heuristic",
        help="Which classifier to evaluate (default: heuristic).",
    )
    parser.add_argument("--dataset", default=DATASET_PATH, help="Path to a JSONL dataset.")
    args = parser.parse_args()

    rows = load_dataset(args.dataset)

    if args.model in ("heuristic", "both"):
        print(_format_report("Heuristic", evaluate_predictions(rows, heuristic_predict)))
    if args.model in ("llm", "both"):
        print(_format_report("LLM", evaluate_predictions(rows, llm_predict)))
    print()


if __name__ == "__main__":
    main()
