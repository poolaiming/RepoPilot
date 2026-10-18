"""Run the fixed, offline retrieval baseline: python -m app.evaluation."""
from __future__ import annotations

import json
from pathlib import Path

from app.services.search import extract_queries, _search_repository


FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures"
THRESHOLDS = {"recall_at_5": 0.9, "mrr_at_5": 0.8, "no_result_accuracy": 1.0}


def evaluate() -> dict:
    cases = json.loads((FIXTURES / "retrieval.json").read_text(encoding="utf-8"))
    root = FIXTURES / "retrieval_repo"
    details = []
    for case in cases:
        queries = extract_queries(case["question"])
        results = _search_repository(root, queries, 5)
        paths = [Path(item["file_path"]).relative_to(root).as_posix() for item in results]
        expected = set(case["expected"])
        hits = expected.intersection(paths)
        rank = next((i for i, path in enumerate(paths, 1) if path in expected), None)
        details.append({
            "id": case["id"], "queries": queries, "files": paths,
            "recall": len(hits) / len(expected) if expected else None,
            "reciprocal_rank": 1 / rank if rank else 0,
            "no_result_correct": not paths if not expected else None,
        })
    positive = [item for item in details if item["recall"] is not None]
    negative = [item for item in details if item["no_result_correct"] is not None]
    metrics = {
        "recall_at_5": sum(item["recall"] for item in positive) / len(positive),
        "mrr_at_5": sum(item["reciprocal_rank"] for item in positive) / len(positive),
        "no_result_accuracy": sum(item["no_result_correct"] for item in negative) / len(negative),
    }
    return {
        "suite": "offline-retrieval-v1", "case_count": len(cases),
        "metrics": metrics, "thresholds": THRESHOLDS,
        "passed": all(metrics[key] >= minimum for key, minimum in THRESHOLDS.items()),
        "cases": details,
    }


def main() -> int:
    result = evaluate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
