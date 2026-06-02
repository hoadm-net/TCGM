"""Aggregate per-question metrics into experiment-level summaries."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Optional, Sequence

from tcgm.evaluation.answer_metrics import AnswerScore
from tcgm.evaluation.retrieval_metrics import (
    mean_reciprocal_rank,
    precision_recall_f1,
    provenance_correctness,
    seed_node_recall,
    subgraph_node_recall,
)


def _avg(values: Iterable[Optional[float]]) -> Optional[float]:
    present = [value for value in values if value is not None]
    if not present:
        return None
    return sum(present) / len(present)


def _sum(values: Iterable[Optional[float]]) -> Optional[float]:
    present = [value for value in values if value is not None]
    if not present:
        return None
    return sum(present)


@dataclass(frozen=True)
class QuestionMetricRecord:
    question_id: str
    question_type: str
    answer_score: AnswerScore
    answered_unknown: bool = False
    latency_seconds: Optional[float] = None
    retrieval_latency_seconds: Optional[float] = None
    post_query_latency_seconds: Optional[float] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    memory_context_original_tokens: Optional[int] = None
    memory_context_final_tokens: Optional[int] = None
    memory_context_truncated: bool = False
    gold_seed_ids: tuple[str, ...] = field(default_factory=tuple)
    predicted_seed_ids: tuple[str, ...] = field(default_factory=tuple)
    gold_subgraph_ids: tuple[str, ...] = field(default_factory=tuple)
    predicted_subgraph_ids: tuple[str, ...] = field(default_factory=tuple)
    gold_evidence_ids: tuple[str, ...] = field(default_factory=tuple)
    predicted_evidence_ids: tuple[str, ...] = field(default_factory=tuple)
    nodes_visited: Optional[int] = None
    hops_expanded: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["answer_score"] = self.answer_score.to_dict()
        return payload


def classify_question_type(question_type: str) -> tuple[str, bool]:
    if question_type == "errors-gotchas":
        return "gotchas", False
    if question_type.endswith("-abs"):
        raw = question_type[:-4]
        if raw.startswith("static"):
            return "static", True
        if raw.startswith("dynamic"):
            return "dynamic", True
        if raw.startswith("procedure"):
            return "procedure", True
    if question_type.startswith("static"):
        return "static", False
    if question_type.startswith("dynamic"):
        return "dynamic", False
    if question_type.startswith("procedure"):
        return "procedure", False
    return question_type, False


def _breakdown(records: Sequence[QuestionMetricRecord]) -> dict[str, Any]:
    count = len(records)
    if count == 0:
        return {"count": 0, "pct_correct": None, "pct_answered_wrong": None, "pct_unknown": None}
    correct = sum(record.answer_score.correct for record in records)
    unknown = sum(record.answered_unknown for record in records)
    wrong_answered = count - correct - unknown
    return {
        "count": count,
        "pct_correct": correct / count,
        "pct_answered_wrong": wrong_answered / count,
        "pct_unknown": unknown / count,
    }


def aggregate_question_metrics(records: Sequence[QuestionMetricRecord]) -> dict[str, Any]:
    count_all = len(records)
    non_abs = [record for record in records if not classify_question_type(record.question_type)[1]]
    abs_only = [record for record in records if classify_question_type(record.question_type)[1]]
    overall_correct = sum(record.answer_score.correct for record in records)
    overall_non_abs_correct = sum(record.answer_score.correct for record in non_abs)
    overall_abs_correct = sum(record.answer_score.correct for record in abs_only)

    non_abstention_by_category: dict[str, Any] = {}
    abstention_by_category: dict[str, Any] = {}
    combined_abstention_by_category: dict[str, Any] = {}
    for family in ("static", "dynamic", "procedure", "gotchas"):
        family_records = [
            record for record in non_abs if classify_question_type(record.question_type)[0] == family
        ]
        if family_records:
            non_abstention_by_category[family] = _breakdown(family_records)
    for family in ("static", "dynamic", "procedure"):
        family_records = [
            record for record in abs_only if classify_question_type(record.question_type)[0] == family
        ]
        if family_records:
            abstention_by_category[f"{family}-abs"] = _breakdown(family_records)
            combined_abstention_by_category[family] = _breakdown(
                [
                    record
                    for record in records
                    if classify_question_type(record.question_type)[0] == family
                ]
            )

    seed_recalls = [
        seed_node_recall(record.predicted_seed_ids, record.gold_seed_ids)
        for record in records
        if record.gold_seed_ids
    ]
    subgraph_recalls = [
        subgraph_node_recall(record.predicted_subgraph_ids, record.gold_subgraph_ids)
        for record in records
        if record.gold_subgraph_ids
    ]
    evidence_overlaps = [
        precision_recall_f1(record.predicted_evidence_ids, record.gold_evidence_ids)
        for record in records
        if record.gold_evidence_ids
    ]
    evidence_mrr = [
        mean_reciprocal_rank(record.predicted_evidence_ids, record.gold_evidence_ids)
        for record in records
        if record.gold_evidence_ids
    ]
    provenance_scores = [
        provenance_correctness(record.predicted_evidence_ids, record.gold_evidence_ids)
        for record in records
        if record.gold_evidence_ids
    ]

    total_prompt_tokens = _sum(record.prompt_tokens for record in records)
    total_completion_tokens = _sum(record.completion_tokens for record in records)
    total_tokens = _sum(record.total_tokens for record in records)
    if total_tokens is None and total_prompt_tokens is not None and total_completion_tokens is not None:
        total_tokens = total_prompt_tokens + total_completion_tokens

    return {
        "overall": {
            "overall_full_set": (overall_correct / count_all) if count_all else None,
            "overall_non_abstention_only": (
                overall_non_abs_correct / len(non_abs) if non_abs else None
            ),
            "overall_abstention_only": (
                overall_abs_correct / len(abs_only) if abs_only else None
            ),
            "count_all_questions": count_all,
            "count_non_abstention": len(non_abs),
            "count_abstention": len(abs_only),
        },
        "abstention_overall": _breakdown(abs_only),
        "non_abstention_by_category": non_abstention_by_category,
        "abstention_by_category": abstention_by_category,
        "combined_abstention_by_category": combined_abstention_by_category,
        "metric_coverage": {
            "llm_judge_questions": sum(record.answer_score.used_llm_judge for record in records),
            "heuristic_llm_questions": sum(
                record.answer_score.used_heuristic_fallback for record in records
            ),
        },
        "tokens": {
            "prompt_tokens": total_prompt_tokens,
            "completion_tokens": total_completion_tokens,
            "total_tokens": total_tokens,
            "avg_prompt_tokens": _avg(record.prompt_tokens for record in records),
            "avg_completion_tokens": _avg(record.completion_tokens for record in records),
            "avg_total_tokens": _avg(record.total_tokens for record in records),
        },
        "memory_context": {
            "avg_original_tokens": _avg(
                record.memory_context_original_tokens for record in records
            ),
            "avg_final_tokens": _avg(record.memory_context_final_tokens for record in records),
            "num_truncated_sequences": sum(
                int(record.memory_context_truncated) for record in records
            ),
        },
        "memory_query": {
            "avg_seconds": _avg(record.retrieval_latency_seconds for record in records),
            "max_seconds": max(
                [record.retrieval_latency_seconds for record in records if record.retrieval_latency_seconds is not None],
                default=None,
            ),
            "total_seconds": _sum(record.retrieval_latency_seconds for record in records),
        },
        "memory_post_query": {
            "avg_seconds": _avg(record.post_query_latency_seconds for record in records),
            "max_seconds": max(
                [record.post_query_latency_seconds for record in records if record.post_query_latency_seconds is not None],
                default=None,
            ),
            "total_seconds": _sum(record.post_query_latency_seconds for record in records),
        },
        "end_to_end": {
            "avg_seconds": _avg(record.latency_seconds for record in records),
            "max_seconds": max(
                [record.latency_seconds for record in records if record.latency_seconds is not None],
                default=None,
            ),
            "total_seconds": _sum(record.latency_seconds for record in records),
        },
        "retrieval": {
            "seed_node_recall": _avg(seed_recalls),
            "subgraph_node_recall": _avg(subgraph_recalls),
            "avg_subgraph_size": _avg(
                len(record.predicted_subgraph_ids) for record in records if record.predicted_subgraph_ids
            ),
            "avg_hops_expanded": _avg(record.hops_expanded for record in records),
            "avg_nodes_visited": _avg(record.nodes_visited for record in records),
        },
        "evidence": {
            "precision": _avg(overlap.precision for overlap in evidence_overlaps),
            "recall": _avg(overlap.recall for overlap in evidence_overlaps),
            "f1": _avg(overlap.f1 for overlap in evidence_overlaps),
            "mrr": _avg(evidence_mrr),
            "provenance_correctness": _avg(provenance_scores),
        },
    }
