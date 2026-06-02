# Dataset: LongMemEval-V2

- **Role in project:** Primary benchmark
- **Source:** https://github.com/xiaowu0162/LongMemEval-V2
- **HuggingFace:** `xiaowu0162/longmemeval-v2`
- **Paper:** [arXiv:2605.12493](https://arxiv.org/abs/2605.12493) (2026)
- **License:** Apache-2.0
- **Local path:** `datasets/LongMemEval-V2/data/longmemeval-v2/`

---

## Overview

LongMemEval-V2 evaluates whether memory systems can help agents acquire the experience needed to become **knowledgeable colleagues** in customized environments. The benchmark pairs manually curated questions with long histories of **multimodal web-agent trajectories**.

A memory system consumes the trajectory history and returns compact evidence for downstream question answering; evaluation targets both **answer accuracy** and **query latency**.

---

## Statistics

| Property | Value |
|----------|-------|
| Questions | 451 (manually curated) |
| Trajectories per haystack | up to 500 |
| Max tokens (largest haystack) | ~115M |
| Domains | Web, Enterprise |
| Leaderboard tiers | Small, Medium |

---

## Memory Abilities Tested

| Ability | Description |
|---------|-------------|
| **Static state recall** | Landmarks, page layouts, module affordances, subtle state differences |
| **Dynamic state tracking** | How states and actions change the environment over time |
| **Workflow knowledge** | Steps needed to complete recurring tasks in customized environments |
| **Environment gotchas** | Recognizing recurring local failure modes, avoiding environment-specific traps |
| **Premise awareness** | Detecting assumptions that are valid elsewhere but wrong in the current deployment |

---

## Why This Dataset for TCGM

LongMemEval-V2 is the **strongest primary benchmark** for this project because:

1. **Published 2026** — no saturated SoTA baselines yet, room to show improvement.
2. **Temporal structure is central** — trajectories are ordered sequences of agent steps with implicit event timelines and state transitions, making them natural candidates for temporal graph representation.
3. **Memory-intensive by design** — the benchmark explicitly tests a memory system's ability to retrieve and synthesize evidence from a massive, evolving history.
4. **Active leaderboard** — submissions are tracked, enabling direct comparison with other approaches.

The flat-text baseline (RAG over raw state slices) is already provided; the TCGM framework's temporal graph representation of trajectories is the natural upgrade.

---

## Data Format

```
data/longmemeval-v2/
├── questions.jsonl          # 451 questions with metadata
├── trajectories.jsonl       # Trajectory objects
├── haystacks/               # Per-question haystack configurations
├── screenshots/             # Symlinked screenshot directories
├── question_screenshots/    # Screenshots paired with questions
└── trajectory_screenshots/  # Raw screenshot archives (tar.gz)
```

### Question schema (simplified)
```json
{
  "question_id": "...",
  "question": "...",
  "answer": "...",
  "question_type": "static_state_recall | dynamic_state_tracking | ...",
  "domain": "web | enterprise",
  "haystack_ids": ["trajectory_id_1", ...]
}
```

### Trajectory schema (simplified)
```json
{
  "trajectory_id": "...",
  "task": "...",
  "steps": [
    {
      "step_id": 0,
      "action": "...",
      "observation": "...",
      "screenshot": "path/to/screenshot.png"
    }
  ]
}
```

---

## Evaluation Metrics

- **Answer accuracy** — exact match and LLM-judge scoring
- **Query latency** — LAFS (Latency-Adjusted F-score) — rewards both accuracy and speed
- Leaderboard uses **LAFS gain** over a fixed reference frontier (no_retrieval + AgentRunbook baselines)

---

## Graph Mapping Strategy for TCGM

| Trajectory element | Graph element |
|--------------------|--------------|
| Agent step (action + observation) | **Event node** with timestamp `t_i` |
| UI element / page state | **Entity node** (state snapshot) |
| Agent action | **Directed edge** (state transition) |
| Task goal | **Root node** (anchors the trajectory subgraph) |
| Question evidence | **Provenance edges** to relevant event nodes |

The temporal order of steps defines a **sequential event chain** — a natural DAG that encodes the dynamic state changes the benchmark explicitly tests.

---

## Baseline Comparison Plan

| Method | Memory type | Expected role |
|--------|-------------|---------------|
| `no_retrieval` | None | Lower bound |
| `rag_query_to_slice` | Flat RAG | Main baseline to beat |
| `agentrunbook_r` | Structured notes + RAG | Strong baseline |
| **TCGM (ours)** | Temporal graph memory | Proposed method |
