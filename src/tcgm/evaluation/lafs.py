"""Latency-adjusted frontier score utilities for LongMemEval-V2 style evaluation."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class Point:
    name: str
    acc: float
    latency: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


T_MIN = 1.0
T_MAX = 200.0
FLOOR_ACC = 0.0


FIXED_FRONTIER_POINTS: dict[str, list[Point]] = {
    "small": [
        Point("RAG: query -> slice + notes", acc=51.0, latency=0.2),
        Point("Codex", acc=69.9, latency=177.2),
        Point("AgentRunbook-R", acc=58.6, latency=26.9),
        Point("AgentRunbook-C", acc=74.9, latency=108.3),
    ],
    "medium": [
        Point("RAG: query -> slice + notes", acc=45.9, latency=0.3),
        Point("Codex", acc=68.7, latency=185.8),
        Point("AgentRunbook-R", acc=57.0, latency=25.8),
        Point("AgentRunbook-C", acc=70.1, latency=139.9),
    ],
}


def pareto_frontier(points: list[Point]) -> list[Point]:
    if not points:
        return []
    sorted_points = sorted(points, key=lambda point: (point.latency, -point.acc))
    frontier: list[Point] = []
    best_acc = -float("inf")
    for point in sorted_points:
        if point.latency <= 0:
            raise ValueError(f"Latency must be positive, got {point.latency} for {point.name}.")
        if point.acc > best_acc:
            frontier.append(point)
            best_acc = point.acc
    return frontier


def best_acc_under_budget(points: list[Point], budget: float, floor_acc: float = FLOOR_ACC) -> float:
    valid = [point.acc for point in points if point.latency <= budget]
    return max(valid) if valid else floor_acc


def lafs(
    points: list[Point],
    t_min: float = T_MIN,
    t_max: float = T_MAX,
    floor_acc: float = FLOOR_ACC,
) -> float:
    if t_min <= 0 or t_max <= 0 or t_min >= t_max:
        raise ValueError("Require 0 < t_min < t_max.")
    frontier = pareto_frontier(points)
    breakpoints = {t_min, t_max}
    for point in frontier:
        if t_min < point.latency < t_max:
            breakpoints.add(point.latency)
    denom = math.log(t_max / t_min)
    area = 0.0
    ordered = sorted(breakpoints)
    for left, right in zip(ordered[:-1], ordered[1:]):
        acc = best_acc_under_budget(frontier, left, floor_acc=floor_acc)
        area += acc * math.log(right / left)
    return area / denom


def lafs_gain_for_submission(
    fixed_points: list[Point],
    submission_points: list[Point],
    t_min: float = T_MIN,
    t_max: float = T_MAX,
    floor_acc: float = FLOOR_ACC,
) -> float:
    return lafs(fixed_points + submission_points, t_min, t_max, floor_acc) - lafs(
        fixed_points,
        t_min,
        t_max,
        floor_acc,
    )


def lafs_summary_for_submission(
    tier: str,
    submission_points: list[Point],
    t_min: float = T_MIN,
    t_max: float = T_MAX,
    floor_acc: float = FLOOR_ACC,
) -> dict[str, Any]:
    if tier not in FIXED_FRONTIER_POINTS:
        supported = ", ".join(sorted(FIXED_FRONTIER_POINTS))
        raise ValueError(f"Unsupported tier {tier!r}; expected one of: {supported}")
    reference_points = FIXED_FRONTIER_POINTS[tier]
    reference_lafs = lafs(reference_points, t_min, t_max, floor_acc)
    submission_lafs = lafs(reference_points + submission_points, t_min, t_max, floor_acc)
    return {
        "tier": tier,
        "t_min_seconds": t_min,
        "t_max_seconds": t_max,
        "floor_accuracy": floor_acc,
        "accuracy_unit": "percentage_points",
        "reference_lafs": reference_lafs,
        "submission_lafs": submission_lafs,
        "lafs_gain": submission_lafs - reference_lafs,
        "reference_frontier": [point.to_dict() for point in pareto_frontier(reference_points)],
        "submission_frontier": [
            point.to_dict() for point in pareto_frontier(reference_points + submission_points)
        ],
    }


def format_points(points: Iterable[Point]) -> str:
    return ", ".join(f"{point.acc:g} @ {point.latency:g}s" for point in points)
