"""Score LongMemEval-V2 predictions into per-question and aggregated metrics.

Input format: JSONL, one object per question prediction.
Required field:
  - id

Recommended field:
  - prediction

Optional runtime / retrieval fields are passed through into the aggregate
summary when present:
  - model_response
  - latency_seconds
  - retrieval_latency_seconds
  - post_query_latency_seconds
  - prompt_tokens
  - completion_tokens
  - total_tokens
  - memory_context_original_tokens
  - memory_context_final_tokens
  - memory_context_truncated
  - gold_seed_ids / predicted_seed_ids
  - gold_subgraph_ids / predicted_subgraph_ids
  - gold_evidence_ids / predicted_evidence_ids
  - nodes_visited
  - hops_expanded
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from tcgm.evaluation import (
    LongMemEvalAnswerEvaluator,
    QuestionMetricRecord,
    aggregate_question_metrics,
)


DEFAULT_QUESTIONS = ROOT / "datasets" / "LongMemEval-V2" / "data" / "longmemeval-v2" / "questions.jsonl"
DEFAULT_OUTPUT = ROOT / "artifacts" / "evaluation" / "longmemeval_v2"


def _load_questions(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _load_predictions(path: Path) -> dict[str, dict]:
    with path.open(encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    return {row["id"]: row for row in rows}


def _tuple_of_strings(value) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    if isinstance(value, tuple):
        return tuple(str(item) for item in value)
    return (str(value),)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate LongMemEval-V2 predictions")
    parser.add_argument("predictions_path", type=Path, help="JSONL file containing predictions")
    parser.add_argument("--questions-path", type=Path, default=DEFAULT_QUESTIONS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--strict-llm-judge",
        action="store_true",
        help="Disable heuristic fallback for llm_* eval functions",
    )
    args = parser.parse_args()

    questions = _load_questions(args.questions_path)
    predictions = _load_predictions(args.predictions_path)
    evaluator = LongMemEvalAnswerEvaluator(
        allow_heuristic_llm_fallback=not args.strict_llm_judge,
    )

    records: list[QuestionMetricRecord] = []
    per_question_rows: list[dict] = []
    for question in questions:
        row = predictions.get(question["id"], {"id": question["id"], "prediction": ""})
        answer_score = evaluator.evaluate(
            question_item=question,
            prediction=row.get("prediction", ""),
            model_response=row.get("model_response"),
        )
        record = QuestionMetricRecord(
            question_id=question["id"],
            question_type=question["question_type"],
            answer_score=answer_score,
            answered_unknown=row.get("answered_unknown", False),
            latency_seconds=row.get("latency_seconds"),
            retrieval_latency_seconds=row.get("retrieval_latency_seconds"),
            post_query_latency_seconds=row.get("post_query_latency_seconds"),
            prompt_tokens=row.get("prompt_tokens"),
            completion_tokens=row.get("completion_tokens"),
            total_tokens=row.get("total_tokens"),
            memory_context_original_tokens=row.get("memory_context_original_tokens"),
            memory_context_final_tokens=row.get("memory_context_final_tokens"),
            memory_context_truncated=row.get("memory_context_truncated", False),
            gold_seed_ids=_tuple_of_strings(row.get("gold_seed_ids")),
            predicted_seed_ids=_tuple_of_strings(row.get("predicted_seed_ids")),
            gold_subgraph_ids=_tuple_of_strings(row.get("gold_subgraph_ids")),
            predicted_subgraph_ids=_tuple_of_strings(row.get("predicted_subgraph_ids")),
            gold_evidence_ids=_tuple_of_strings(row.get("gold_evidence_ids")),
            predicted_evidence_ids=_tuple_of_strings(row.get("predicted_evidence_ids")),
            nodes_visited=row.get("nodes_visited"),
            hops_expanded=row.get("hops_expanded"),
        )
        records.append(record)
        per_question_rows.append(record.to_dict())

    aggregated = aggregate_question_metrics(records)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    per_question_path = args.output_dir / "per_question.jsonl"
    aggregated_path = args.output_dir / "aggregated_metrics.json"

    with per_question_path.open("w", encoding="utf-8") as handle:
        for row in per_question_rows:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")
    aggregated_path.write_text(
        json.dumps(aggregated, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote per-question metrics to {per_question_path}")
    print(f"Wrote aggregated metrics to {aggregated_path}")


if __name__ == "__main__":
    main()