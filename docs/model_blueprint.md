# Model Blueprint: TCGM

This document translates the research agenda into a concrete method roadmap. The core objective is to make **retrieval over temporal conversational graphs learnable**, while keeping graph construction interpretable and reproducible.

---

## Core Position

TCGM should not be framed as only a graph engineering pipeline.

The intended contribution is:

- a **symbolic temporal graph representation** for long-horizon memory
- a **learnable retrieval mechanism** over that graph
- an evaluation across dialogue, agent memory, and temporal KG settings

The graph is the substrate. The retrieval policy is the main model contribution.

---

## System Decomposition

### 1. Symbolic Graph Builder

Responsibility:

- convert each dataset into a unified temporal graph
- preserve timestamps, order, typed relations, and provenance

This layer should remain mostly deterministic so errors are debuggable.

### 2. Seed Scorer

Responsibility:

- map a question to candidate event, entity, and state nodes

This is the first learnable retrieval module. It should rank likely starting points for graph traversal.

### 3. Temporal GNN Expander

Responsibility:

- expand from seed nodes into a question-specific subgraph
- use topology, relation types, and time constraints jointly

This is the core Phase 2 contribution.

### 4. Path / Evidence Scorer

Responsibility:

- score candidate paths or evidence chains inside the retrieved subgraph
- prefer time-consistent, relation-aware, compact evidence

This is a natural Phase 3 extension.

### 5. Answerer

Responsibility:

- generate or select the final answer from the retrieved subgraph
- return evidence alongside the answer

---

## Phase Plan

## Phase 1 — Symbolic Baseline

### Objective

Create a reliable lower bound before adding learning.

### Components

- unified temporal graph schema
- dataset adapters
- symbolic retriever
- flat RAG baseline
- evaluation for answer quality and evidence quality

### Retrieval Style

- temporal filtering
- typed-edge neighborhood expansion
- heuristic subgraph ranking

### Success Criteria

- graph baseline is competitive with or better than flat retrieval on time-sensitive queries
- retrieved evidence is inspectable and provenance-preserving

---

## Phase 2 — Learnable Retriever

### Objective

Turn graph retrieval into the main model contribution.

### Components

- query encoder
- node encoder
- learnable seed scorer
- query-conditioned temporal GNN expansion

### Training Signals

- answer supervision
- evidence node supervision
- temporal consistency loss
- compactness regularization

### Why This Phase Matters

This is the point where TCGM stops being only a symbolic pipeline and becomes a model that learns how to use topology and time.

---

## Phase 3 — Advanced Reasoning

### Objective

Increase novelty and strengthen analysis.

### Option A: Path Scorer

- learn to score reasoning paths or evidence chains
- useful for explainability and ablations

### Option B: RL Fine-Tuning

- learn multi-step traversal and stopping decisions
- use dense rewards, not only final-answer rewards

### Example Reward Terms

- answer correctness
- evidence recall
- temporal consistency
- retrieval efficiency

### Expected Outcome

Phase 3 should test whether learned reasoning on top of learned retrieval gives gains beyond Phase 2, or whether most value already comes from better subgraph retrieval.

---

## Recommended First Model

If implementation bandwidth is limited, the first publishable model should be:

- symbolic graph builder
- learnable seed scorer
- query-conditioned temporal GNN expander
- LLM or classifier answerer

This is the best balance between novelty, feasibility, and interpretability.

---

## Key Ablations

- no temporal features
- no relation types
- no provenance features
- heuristic seeds instead of learned seeds
- heuristic expansion instead of temporal GNN expansion
- Phase 2 without Phase 3 refinement

These ablations are necessary to show that gains come from **learned temporal graph retrieval**, not only from storing data in graph form.

---

## Benchmark Roles

### LoCoMo

- stress-test temporal conversational retrieval
- useful for cross-session recall and ordering questions

### LongMemEval-V2

- stress-test workflow and dynamic state retrieval
- useful for accuracy-latency analysis

### TGB 2.0

- isolate the temporal multi-relational reasoning core
- useful for testing whether learned retrieval exploits topology without language noise

---

## Summary

The research path should remain disciplined:

1. prove the graph representation helps
2. learn how to retrieve over the graph
3. learn how to reason over retrieved paths

This sequence keeps TCGM scientifically grounded while preserving a clear path to a real model contribution.