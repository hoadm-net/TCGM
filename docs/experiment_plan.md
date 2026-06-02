# Experiment Plan: TCGM

This document turns the TCGM roadmap into an executable experimental program. It is organized by the three project phases and is designed to keep the work focused on a real model contribution rather than a purely symbolic pipeline.

---

## Experimental Goals

The experiment plan should answer four high-level questions:

1. does temporal graph structure help over flat retrieval?
2. does learnable retrieval help over symbolic graph traversal?
3. do path scoring or RL-style refinements add value beyond a learned retriever?
4. do gains transfer across dialogue, agent memory, and temporal KG benchmarks?

---

## Benchmarks and Roles

### LongMemEval-V2

- primary benchmark
- best for dynamic state tracking, workflow retrieval, premise awareness, and accuracy-latency tradeoffs

### LoCoMo

- robustness benchmark for cross-session conversational memory
- best for temporal ordering, long-range entity tracking, and evidence aggregation

### TGB 2.0

- robustness benchmark for temporal graph reasoning core
- best for isolating topology and temporal reasoning from language parsing noise

---

## Metrics

## Final Answer Metrics

- answer accuracy
- exact match and F1 where applicable
- MRR / Hits@k for TGB-style link prediction tasks

## Evidence Metrics

- evidence recall@k
- evidence precision@k
- provenance correctness

## Retrieval Metrics

- seed node recall
- subgraph node recall
- subgraph size
- average hops expanded

## Efficiency Metrics

- end-to-end latency
- retrieval latency
- number of nodes visited
- token budget passed to the answerer

---

## Phase 1 — Symbolic Lower Bound

## Objective

Establish strong, debuggable baselines.

## Systems to Compare

1. `Flat RAG`
   chunk retrieval without graph structure

2. `Temporal Graph Retrieval (Symbolic)`
   heuristic seed selection + temporal filtering + typed-edge expansion

3. `Temporal Graph Retrieval (No Time)`
   same as above but without temporal constraints

4. `Temporal Graph Retrieval (No Relation Types)`
   same as above but relation types collapsed

## Key Questions

- does graph structure help before any learning?
- which question categories benefit from time-aware retrieval?
- where do symbolic methods fail?

## Deliverables

- clean baseline table for all three benchmarks
- failure analysis by question type
- evidence quality analysis

---

## Phase 2 — Core Learnable Retriever

## Objective

Make retrieval the central learned component.

## Target Model

- learnable query encoder
- node encoder
- seed scorer
- query-conditioned temporal GNN expansion
- answerer over retrieved subgraph

## Training Signals

### Supervision

- answer supervision
- evidence node supervision when available
- weak supervision from labeled answers when gold paths are absent

### Auxiliary Objectives

- temporal consistency loss
- compactness regularization
- contrastive ranking for positive vs hard negative nodes

## Comparisons

1. `Phase 1 symbolic retriever`
2. `Learned seeds + symbolic expansion`
3. `Learned seeds + learned expansion`
4. `Flat RAG`

## Key Questions

- does learning improve seed selection?
- does query-conditioned expansion exploit topology better than heuristics?
- are gains consistent across all three benchmark families?

## Deliverables

- main model results
- ablations isolating seeds vs expansion
- retrieval visualization or qualitative evidence traces

---

## Phase 3 — Stronger Reasoning Layer

## Objective

Test whether added reasoning modules improve on top of learned retrieval.

## Candidate Extensions

### Option A: Path Scorer

- score candidate paths or evidence chains
- encourage compact, relation-aware, time-consistent reasoning traces

### Option B: RL Fine-Tuning

- fine-tune expansion and stopping policy with dense rewards
- optimize for answer quality, evidence quality, temporal consistency, and efficiency jointly

## Example Reward Terms

- final answer correctness
- evidence recall
- temporal consistency
- traversal efficiency
- compactness of retrieved subgraph

## Key Questions

- does path-level learning help beyond learned subgraph retrieval?
- does RL improve retrieval policy or only increase variance?
- is Phase 3 worth the added complexity on each benchmark?

## Deliverables

- comparison against Phase 2
- cost-benefit analysis of added complexity
- stronger ablation suite

---

## Core Ablations

The following ablations should be preserved across phases when possible.

1. `No time`
2. `No relation types`
3. `No provenance features`
4. `No state nodes`
5. `Heuristic seeds`
6. `Heuristic expansion`
7. `No path scorer / no RL refinement`

These ablations are necessary to prove that gains come from learned temporal graph retrieval rather than dataset-specific preprocessing.

---

## Cross-Benchmark Transfer Plan

To test H3 directly, include at least one transfer setting.

### Recommended Strategy

1. pretrain retrieval components on TGB 2.0 or mixed graph tasks
2. fine-tune on LoCoMo or LongMemEval-V2
3. compare against training from scratch

### Question to Answer

Does temporal multi-relational structure learned in a clean graph domain transfer to noisy conversational and agent-memory domains?

---

## Error Analysis Template

Every main experiment should categorize failures into:

- seed miss
- wrong temporal disambiguation
- wrong relation expansion
- stale state selection
- insufficient evidence despite correct retrieval neighborhood
- answerer failure despite correct evidence

This split is important because it separates graph construction problems from retrieval policy problems and answer-generation problems.

---

## Near-Term Execution Order

1. finalize `graph_schema.md`
2. implement dataset adapters for LoCoMo and LongMemEval-V2
3. run Phase 1 flat RAG and symbolic graph baselines
4. define supervision targets for Phase 2 retriever training
5. implement learned seed scorer before full temporal GNN expansion

This order keeps the project on a controlled path from lower bound to core contribution.