"""LongMemEval-V2 dataset adapter.

Maps the raw JSONL files (trajectories.jsonl + questions.jsonl + haystacks)
into the four canonical TCGM Parquet tables.

Mapping summary (see docs/adapter_spec.md §LongMemEval-V2):
  Episode  ← one per trajectory
  Event    ← one per state (state_index); subtype derived from action + thought
  Entity   ← one per unique URL (page entity)
  State    ← (Phase 1: skipped — no LLM; conservative rule will be added later)
  Query    ← one per question

Edges:
  PART_OF  : Event → Episode
  BEFORE   : Event[i] → Event[i+1] (within same trajectory)
  INVOLVES : Event → URL-Entity (when URL present)

IDs follow the adapter_spec convention:
  Episode  : lmev2:{traj_id}
  Event    : lmev2:{traj_id}:step:{state_index:04d}
  Entity   : lmev2:page:{url_hash8}
  Query    : lmev2:q:{question_id}
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Set

from tqdm import tqdm

from tcgm.schema import Edge, Node, ProvenanceRecord, Query
from tcgm.adapters.base import BaseAdapter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _url_hash(url: str) -> str:
    """8-character stable hash of a URL for entity ID generation."""
    return hashlib.sha256(url.encode()).hexdigest()[:8]


def _infer_event_subtype(action: Optional[object], thought: Optional[str]) -> str:
    """Classify a state into one of four event subtypes.

    ActionEvent    — agent performs a concrete browser/tool action
    ObservationEvent — initial state (no action) or pure observation
    FailureEvent   — action or thought signals an error / retry / failure
    StrategyEvent  — thought is long planning text without a concrete action
    """
    if action is None:
        return "ObservationEvent"

    action_str = str(action).lower() if action else ""
    thought_str = (thought or "").lower()

    failure_signals = ("error", "fail", "retry", "invalid", "incorrect", "wrong",
                       "could not", "unable", "not found", "no result")
    if any(s in action_str or s in thought_str for s in failure_signals):
        return "FailureEvent"

    # If thought is very long and action is sparse, treat as strategy
    if thought and len(thought) > 400 and len(action_str) < 80:
        return "StrategyEvent"

    return "ActionEvent"


def _action_text(action: Optional[object]) -> str:
    """Convert action field (may be dict or string) to flat text."""
    if action is None:
        return ""
    if isinstance(action, dict):
        return json.dumps(action)
    return str(action)


def _state_text(state: Dict) -> str:
    """Compose the canonical Event text from a trajectory state."""
    parts: List[str] = []
    thought = (state.get("thought") or "").strip()
    action_raw = state.get("action")
    action = _action_text(action_raw).strip()
    if thought:
        parts.append(f"[thought] {thought}")
    if action:
        parts.append(f"[action] {action}")
    return " ".join(parts) if parts else "[observation]"


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------

class LongMemEvalV2Adapter(BaseAdapter):
    """Convert LongMemEval-V2 raw data to canonical TCGM graph tables."""

    DATASET_TAG = "lmev2"

    # ------------------------------------------------------------------
    # Inputs
    # ------------------------------------------------------------------
    TRAJ_FILE = "trajectories.jsonl"
    QUEST_FILE = "questions.jsonl"
    HAYSTACK_SMALL = "haystacks/lme_v2_small.json"
    HAYSTACK_MEDIUM = "haystacks/lme_v2_medium.json"

    def __init__(self, data_root: Path, output_dir: Path) -> None:
        super().__init__(data_root, output_dir)
        # Shared entity registry: url -> node_id  (dedup across trajectories)
        self._url_entity_map: Dict[str, str] = {}

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(self) -> None:
        """Populate nodes / edges / provenance / queries."""
        traj_ids = self._build_trajectories()
        self._build_queries(traj_ids)

    # ------------------------------------------------------------------
    # Trajectories → Episodes + Events + Entities + Edges
    # ------------------------------------------------------------------

    def _build_trajectories(self) -> Set[str]:
        traj_path = self.data_root / self.TRAJ_FILE
        traj_ids: Set[str] = set()

        with open(traj_path, encoding="utf-8") as fh:
            lines = fh.readlines()

        for line in tqdm(lines, desc="Trajectories", unit="traj"):
            line = line.strip()
            if not line:
                continue
            traj = json.loads(line)
            traj_id: str = traj["id"]
            traj_ids.add(traj_id)

            # ---- Episode node ----------------------------------------
            episode_id = f"lmev2:{traj_id}"
            episode_node = Node(
                node_id=episode_id,
                node_type="Episode",
                label=f"traj:{traj_id}",
                text=traj.get("goal", ""),
                dataset=self.DATASET_TAG,
                metadata={
                    "domain": traj.get("domain"),
                    "environment": traj.get("environment"),
                    "outcome": traj.get("outcome"),
                    "start_url": traj.get("start_url"),
                    "traj_id": traj_id,
                },
            )
            self.nodes.append(episode_node)
            self.provenance.append(ProvenanceRecord(
                target_id=episode_id,
                source_dataset=self.DATASET_TAG,
                source_item_id=traj_id,
                source_unit_id="trajectory",
                source_type="trajectory",
                source_span=None,
                confidence=1.0,
            ))

            # ---- State nodes (Events) ---------------------------------
            states: List[Dict] = traj.get("states", [])
            prev_event_id: Optional[str] = None

            for state in states:
                si: int = state["state_index"]
                event_id = f"lmev2:{traj_id}:step:{si:04d}"
                subtype = _infer_event_subtype(state.get("action"), state.get("thought"))
                text = _state_text(state)

                event_node = Node(
                    node_id=event_id,
                    node_type="Event",
                    label=f"{traj_id}/step{si}",
                    text=text,
                    dataset=self.DATASET_TAG,
                    metadata={
                        "event_subtype": subtype,
                        "state_index": si,
                        "step": state.get("step"),
                        "url": state.get("url"),
                        "screenshot": state.get("screenshot"),
                        "traj_id": traj_id,
                        # Accessibility tree stored separately for space —
                        # reference only, not full text in metadata
                        "has_accessibility_tree": bool(state.get("accessibility_tree")),
                    },
                )
                self.nodes.append(event_node)

                self.provenance.append(ProvenanceRecord(
                    target_id=event_id,
                    source_dataset=self.DATASET_TAG,
                    source_item_id=traj_id,
                    source_unit_id=str(si),
                    source_type="trajectory_state",
                    source_span="thought,action",
                    confidence=1.0,
                ))

                # PART_OF: event → episode
                self.edges.append(Edge(
                    src_id=event_id,
                    edge_type="PART_OF",
                    dst_id=episode_id,
                ))

                # BEFORE: previous event → this event
                if prev_event_id is not None:
                    self.edges.append(Edge(
                        src_id=prev_event_id,
                        edge_type="BEFORE",
                        dst_id=event_id,
                        metadata={"order": si},
                    ))
                prev_event_id = event_id

                # INVOLVES: event → URL entity
                url: Optional[str] = state.get("url")
                if url:
                    entity_id = self._get_or_create_url_entity(url)
                    self.edges.append(Edge(
                        src_id=event_id,
                        edge_type="INVOLVES",
                        dst_id=entity_id,
                    ))

        return traj_ids

    # ------------------------------------------------------------------
    # URL Entity dedup
    # ------------------------------------------------------------------

    def _get_or_create_url_entity(self, url: str) -> str:
        if url in self._url_entity_map:
            return self._url_entity_map[url]

        entity_id = f"lmev2:page:{_url_hash(url)}"
        # There might be hash collisions across truly different URLs that share
        # 8-char prefix — store the full URL in metadata for disambiguation.
        if entity_id not in {n.node_id for n in self.nodes if n.node_type == "Entity"}:
            self.nodes.append(Node(
                node_id=entity_id,
                node_type="Entity",
                label=url[:80],
                text=url,
                dataset=self.DATASET_TAG,
                metadata={"entity_subtype": "page", "url": url},
            ))
        self._url_entity_map[url] = entity_id
        return entity_id

    # ------------------------------------------------------------------
    # Questions → Queries
    # ------------------------------------------------------------------

    def _build_queries(self, traj_ids: Set[str]) -> None:
        quest_path = self.data_root / self.QUEST_FILE
        hs_small_path = self.data_root / self.HAYSTACK_SMALL
        hs_medium_path = self.data_root / self.HAYSTACK_MEDIUM

        # Load haystacks — both are {question_id: [traj_id, ...]}
        haystack_small: Dict[str, List[str]] = {}
        haystack_medium: Dict[str, List[str]] = {}
        if hs_small_path.exists():
            with open(hs_small_path) as fh:
                haystack_small = json.load(fh)
        if hs_medium_path.exists():
            with open(hs_medium_path) as fh:
                haystack_medium = json.load(fh)

        with open(quest_path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                q = json.loads(line)
                qid: str = q["id"]
                query_id = f"lmev2:q:{qid}"

                # Haystack trajectory IDs (resolved to episode node IDs)
                hs_small_ids = [
                    f"lmev2:{tid}" for tid in haystack_small.get(qid, [])
                    if tid in traj_ids
                ]
                hs_medium_ids = [
                    f"lmev2:{tid}" for tid in haystack_medium.get(qid, [])
                    if tid in traj_ids
                ]

                self.queries.append(Query(
                    query_id=query_id,
                    question=q["question"],
                    answer=q["answer"],
                    dataset=self.DATASET_TAG,
                    question_type=q["question_type"],
                    time_anchor=None,
                    # Gold evidence not explicitly labeled — stored in metadata
                    gold_evidence=None,
                    metadata={
                        "raw_id": qid,
                        "domain": q.get("domain"),
                        "environment": q.get("environment"),
                        "eval_function": q.get("eval_function"),
                        "image": q.get("image"),
                        "haystack_small": hs_small_ids,
                        "haystack_medium": hs_medium_ids,
                    },
                ))

                self.provenance.append(ProvenanceRecord(
                    target_id=query_id,
                    source_dataset=self.DATASET_TAG,
                    source_item_id=qid,
                    source_unit_id="question",
                    source_type="question",
                    source_span=None,
                    confidence=1.0,
                ))

    # ------------------------------------------------------------------
    # Extended validation  (overrides BaseAdapter checks)
    # ------------------------------------------------------------------

    def validate(self) -> Dict:
        report = super().validate()

        # Check 1: every Event is in exactly one Episode
        event_episode_count: Dict[str, int] = {}
        for e in self.edges:
            if e.edge_type == "PART_OF":
                event_episode_count[e.src_id] = event_episode_count.get(e.src_id, 0) + 1
        events = [n for n in self.nodes if n.node_type == "Event"]
        missing = [n.node_id for n in events if event_episode_count.get(n.node_id, 0) != 1]
        if missing:
            report["errors"].append(
                f"{len(missing)} Event nodes not in exactly one Episode: {missing[:5]}…"
            )

        # Check 2: step order strictly increasing within each trajectory
        from collections import defaultdict
        traj_steps: Dict[str, List[int]] = defaultdict(list)
        for e in self.edges:
            if e.edge_type == "BEFORE":
                # src = step N, dst = step N+1
                # extract state_index from node_id
                src_parts = e.src_id.split(":")
                dst_parts = e.dst_id.split(":")
                if len(src_parts) == 4 and len(dst_parts) == 4:
                    try:
                        src_si = int(src_parts[3].replace("step", ""))
                        dst_si = int(dst_parts[3].replace("step", ""))
                        traj_id = src_parts[1]
                        traj_steps[traj_id].append((src_si, dst_si))
                    except ValueError:
                        pass

        out_of_order = []
        for traj_id, pairs in traj_steps.items():
            for src_si, dst_si in pairs:
                if dst_si != src_si + 1:
                    out_of_order.append(traj_id)
                    break
        if out_of_order:
            report["warnings"].append(
                f"{len(out_of_order)} trajectories have non-consecutive step BEFORE edges"
            )

        # Check 3: query metadata preserves raw question IDs
        missing_raw_id = [
            q.query_id for q in self.queries
            if "raw_id" not in q.metadata
        ]
        if missing_raw_id:
            report["errors"].append(
                f"{len(missing_raw_id)} queries missing raw_id in metadata"
            )

        # Check 4: node type distribution
        from collections import Counter
        type_dist = Counter(n.node_type for n in self.nodes)
        report["stats"]["node_type_distribution"] = dict(type_dist)
        report["stats"]["question_type_distribution"] = dict(
            Counter(q.question_type for q in self.queries)
        )

        report["ok"] = len(report["errors"]) == 0
        return report
