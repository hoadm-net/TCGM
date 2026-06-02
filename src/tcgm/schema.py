"""Canonical in-memory schema for TCGM graph artifacts.

Four tables mirror the Parquet layout defined in docs/graph_schema.md:
  nodes       — all node types (Entity, Event, Episode, State)
  edges       — directed typed edges
  provenance  — source attribution for any node/edge
  queries     — benchmark questions + metadata
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------

@dataclass
class Node:
    node_id: str          # e.g. "lmev2:traj_0007:event:step_083"
    node_type: str        # Entity | Event | Episode | State
    label: str            # short human-readable label
    text: str             # raw text content (thought + action, goal, etc.)
    dataset: str          # "lmev2"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["metadata"] = json.dumps(d["metadata"])
        return d


# ---------------------------------------------------------------------------
# Edge
# ---------------------------------------------------------------------------

@dataclass
class Edge:
    src_id: str
    edge_type: str        # PART_OF | BEFORE | AFTER | INVOLVES | UPDATES | …
    dst_id: str
    start_time: Optional[str] = None   # ISO-8601 or None
    end_time: Optional[str] = None
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["metadata"] = json.dumps(d["metadata"])
        return d


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------

@dataclass
class ProvenanceRecord:
    target_id: str            # node_id or edge src_id+edge_type+dst_id
    source_dataset: str       # "lmev2"
    source_item_id: str       # trajectory id or question id
    source_unit_id: str       # state_index or step
    source_type: str          # "trajectory_state" | "question" | "trajectory"
    source_span: Optional[str] = None   # field name / char range
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------

@dataclass
class Query:
    query_id: str             # "lmev2:q:01307e07"
    question: str
    answer: str
    dataset: str              # "lmev2"
    question_type: str        # raw question_type from jsonl
    time_anchor: Optional[str] = None
    gold_evidence: Optional[str] = None   # JSON list of node_ids or null
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["metadata"] = json.dumps(d["metadata"])
        return d
