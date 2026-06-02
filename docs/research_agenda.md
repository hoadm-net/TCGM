# Research Agenda: TCGM

This document records the current research framing for **Temporal Conversational Graph Memory for Long-Horizon QA**. It is intended to serve as the project's working compass for model design, experiments, and ablations.

---

## Problem Framing

The project studies whether long-horizon memory can be represented more effectively as a **multi-relational temporal graph** rather than as flat retrieved text. The target setting includes:

- long conversational histories
- agent trajectories with evolving interface state and workflows
- temporal knowledge graphs with typed edges and timestamps

The core claim is not that graph memory always beats RAG, but that it should help most when questions require:

- temporal disambiguation
- cross-session evidence aggregation
- multi-hop relational reasoning
- explicit provenance and interpretability

---

## Related-Work Gaps

Current literature points to four gaps that motivate TCGM:

1. **Long-term dialogue and agent memory benchmarks exist, but memory structure is still weak.**
   LoCoMo and LongMemEval-V2 show that long-range recall, temporal consistency, workflow understanding, and premise tracking remain difficult.

2. **Graph-based retrieval improves structured reasoning, but often ignores temporal dynamics.**
   Systems such as GraphRAG and HippoRAG show the value of graph-structured retrieval, but they do not directly target evolving entity states, stale facts, or time-constrained QA.

3. **Temporal KG methods are strong on time-aware reasoning, but operate on clean structured graphs.**
   TLogic and TGB 2.0 emphasize temporal consistency, relation-aware reasoning, and scalability, but they are far from noisy conversational and agent-memory settings.

4. **There is little evidence that one temporal memory framework can transfer across heterogeneous sources.**
   Most prior work is benchmark-specific. TCGM asks whether a shared temporal graph schema can bridge dialogue, agent trajectories, and temporal KG data.

---

## Research Questions

### RQ1

Can a temporal conversational graph memory outperform flat-text retrieval baselines on long-horizon QA that requires cross-session or time-constrained reasoning?

### RQ2

What graph schema best unifies dialogue turns, events, entity states, and external temporal knowledge while preserving both retrieval efficiency and answer faithfulness?

### RQ3

Can a unified temporal graph memory framework transfer across heterogeneous benchmarks such as long conversations, agent trajectories, and temporal knowledge graphs?

### RQ4

What is the accuracy-latency tradeoff of temporal graph retrieval compared with hierarchical memory and standard RAG baselines?

---

## Research Hypotheses

### H1. Temporal structure matters.

Explicit modeling of timestamps, event order, and state transitions as graph structure will outperform flat-text RAG on questions requiring temporal disambiguation or cross-session evidence aggregation.

### H2. Relation-aware retrieval matters.

Retrieval over a multi-relational temporal graph will improve evidence precision and answer consistency compared with chunk-similarity retrieval, especially for multi-hop and entity-state tracking questions.

### H3. Unified graph memory transfers better.

A unified graph schema shared across dialogue, agent trajectories, and temporal KG data will generalize better across benchmarks than dataset-specific memory modules.

### H4. Explainable temporal reasoning can stay competitive.

Lightweight temporal graph reasoning modules, such as temporal subgraph retrieval plus rule/path-based aggregation, can approach or exceed stronger black-box memory baselines while providing better provenance and interpretability.

---

## Benchmark Alignment

### LongMemEval-V2

- Best for testing **H1** and **H4**
- Focus: workflow knowledge, dynamic state tracking, premise awareness
- Main question: can temporal graph memory improve the accuracy-latency frontier over flat retrieval or coding-agent memory baselines?

### LoCoMo

- Best for testing **H1** and **H2**
- Focus: cross-session recall, speaker state tracking, temporal ordering
- Main question: can graph retrieval recover temporally relevant conversational evidence more precisely than chunk retrieval?

### TGB 2.0

- Best for testing **H2** and part of **H3**
- Focus: temporal multi-relational reasoning in a clean structured setting
- Main question: does the temporal graph reasoning core remain competitive when language parsing noise is removed?

---

## Design Principles for the First Prototype

1. Start with a **minimal unified schema**: entity nodes, event nodes, episode/session nodes, typed edges, timestamps, provenance.
2. Keep the first retriever simple: temporal filtering plus relation-aware neighborhood expansion.
3. Compare against strong simple baselines, not just weak strawmen.
4. Measure both final answer quality and evidence quality.
5. Preserve explainability: every retrieved answer context should map back to graph nodes and source evidence.

---

## Immediate Experimental Priorities

1. Define the unified temporal graph schema.
2. Build dataset adapters for LongMemEval-V2 and LoCoMo first.
3. Establish flat RAG and simple graph-retrieval baselines.
4. Add temporal and provenance-focused evaluation.
5. Use TGB 2.0 to isolate whether failures come from temporal reasoning or upstream graph construction.