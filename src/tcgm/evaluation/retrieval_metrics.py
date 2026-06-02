"""Retrieval-, evidence-, and ranking-oriented metrics for TCGM."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, Sequence


def _unique_preserve_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def _safe_div(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


@dataclass(frozen=True)
class OverlapMetrics:
    precision: float
    recall: float
    f1: float
    predicted_count: int
    gold_count: int
    overlap_count: int

    def to_dict(self) -> dict:
        return asdict(self)


def precision_recall_f1(
    predicted_ids: Iterable[str],
    gold_ids: Iterable[str],
) -> OverlapMetrics:
    predicted = set(_unique_preserve_order(predicted_ids))
    gold = set(_unique_preserve_order(gold_ids))
    overlap = predicted & gold
    precision = _safe_div(len(overlap), len(predicted))
    recall = _safe_div(len(overlap), len(gold))
    f1 = _safe_div(2 * precision * recall, precision + recall) if (precision + recall) else 0.0
    return OverlapMetrics(
        precision=precision,
        recall=recall,
        f1=f1,
        predicted_count=len(predicted),
        gold_count=len(gold),
        overlap_count=len(overlap),
    )


def recall_at_k(ranked_ids: Sequence[str], gold_ids: Iterable[str], k: int) -> float:
    return precision_recall_f1(ranked_ids[:k], gold_ids).recall


def precision_at_k(ranked_ids: Sequence[str], gold_ids: Iterable[str], k: int) -> float:
    return precision_recall_f1(ranked_ids[:k], gold_ids).precision


def hits_at_k(ranked_ids: Sequence[str], gold_ids: Iterable[str], k: int) -> float:
    gold = set(gold_ids)
    if not gold:
        return 0.0
    return float(any(node_id in gold for node_id in ranked_ids[:k]))


def mean_reciprocal_rank(ranked_ids: Sequence[str], gold_ids: Iterable[str]) -> float:
    gold = set(gold_ids)
    if not gold:
        return 0.0
    for index, node_id in enumerate(ranked_ids, start=1):
        if node_id in gold:
            return 1.0 / index
    return 0.0


def provenance_correctness(predicted_targets: Iterable[str], gold_targets: Iterable[str]) -> float:
    return precision_recall_f1(predicted_targets, gold_targets).precision


def seed_node_recall(predicted_seed_ids: Iterable[str], gold_seed_ids: Iterable[str]) -> float:
    return precision_recall_f1(predicted_seed_ids, gold_seed_ids).recall


def subgraph_node_recall(predicted_subgraph_ids: Iterable[str], gold_subgraph_ids: Iterable[str]) -> float:
    return precision_recall_f1(predicted_subgraph_ids, gold_subgraph_ids).recall
