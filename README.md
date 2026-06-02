# Temporal Conversational Graph Memory for Long-Horizon QA

> Research project exploring a unified framework for **Temporal Graph Reasoning** over long-horizon conversations and knowledge graphs, with applications in multi-turn QA, episodic memory retrieval, and agent dialogue understanding.

---

## Research Direction

Modern LLM agents are increasingly deployed in long-horizon, conversational settings where facts evolve, contradict, and become stale over time. Existing approaches treat memory as flat text retrieval (RAG) or ignore temporal structure entirely. This project proposes a **Temporal Conversational Graph Memory** framework that structures conversational history and external knowledge as a dynamic temporal graph, enabling principled multi-hop and time-constrained reasoning for question answering.

**Core hypothesis:** Structuring conversational and factual memory as a temporal graph — and learning how to retrieve over that graph — enables more accurate, consistent, and interpretable QA over long-horizon interactions.

### Key Research Questions

1. Can a temporal graph memory representation outperform flat-text RAG on long-horizon conversational QA?
2. How should temporal events, entity states, and dialogue turns be unified in a single graph schema?
3. Can temporal subgraph retrieval + LLM reasoning generalize across heterogeneous data sources (agent trajectories, dialogues, knowledge graphs)?

---

## Framework Overview

```
Input (conversation / KG / agent trajectory)
        │
        ▼
┌─────────────────────┐
│  Temporal Graph      │   ← Entities, Relations, Events, Utterances
│  Builder             │      with timestamps / intervals / provenance
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Memory Manager      │   ← Merge, deduplicate, version, decay stale facts
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Learnable Temporal  │   ← Query-conditioned retrieval with time constraints,
│  Subgraph Retriever  │      relation-aware expansion, and multi-hop traversal
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  LLM Reasoner        │   ← Synthesis over retrieved subgraph context
└────────┬────────────┘
         │
         ▼
       Answer + Evidence
```

---

## Benchmarks

| # | Dataset | Role | Domain | Size | Year |
|---|---------|------|--------|------|------|
| 1 | [LongMemEval-V2](datasets/LongMemEval-V2/) | **Primary** — long-horizon memory QA | Web/Enterprise agent trajectories | 451 questions, up to 115M tokens | 2026 |
| 2 | [LoCoMo](datasets/LoCoMo/) | **Robustness A** — long conversational memory | Multi-session human dialogues | 10 conversations, ~5K+ turns | 2024 |
| 3 | [TGB 2.0](datasets/TGB-V2/) | **Robustness B** — temporal graph core | Temporal knowledge graphs | `tkgl-smallpedia` (prototype), `tkgl-icews` (scale) | 2024 |

See [`docs/`](docs/) for detailed dataset documentation, the [`research_agenda.md`](docs/research_agenda.md) roadmap, the [`model_blueprint.md`](docs/model_blueprint.md) phased method plan, the [`graph_schema.md`](docs/graph_schema.md) unified graph specification, the [`adapter_spec.md`](docs/adapter_spec.md) dataset adapter contract, and the [`experiment_plan.md`](docs/experiment_plan.md) experimental roadmap.

---

## Research Program

The project will advance in three phases so the work remains scientifically grounded while still building toward a learnable model.

### Phase 1 — Symbolic Lower Bound

- Build the unified temporal graph schema and dataset adapters
- Implement a non-learned retriever with temporal filtering and relation-aware expansion
- Establish clean lower-bound baselines against flat RAG

### Phase 2 — Core Model Contribution

- Add a **learnable seed scorer** that maps a question to relevant graph nodes
- Add **query-conditioned temporal GNN expansion** to retrieve task-specific subgraphs
- Train retrieval from QA and evidence supervision instead of relying only on hand-written rules

### Phase 3 — Stronger Reasoning and Ablations

- Add a learnable path scorer and/or RL fine-tuning for multi-hop traversal
- Study accuracy, evidence quality, interpretability, and efficiency tradeoffs
- Run ablations to isolate the value of time, topology, relation types, and learning signals

---

## Project Structure

```
TCGM/
├── README.md
├── datasets/
│   ├── LongMemEval-V2/     # Primary benchmark (2026)
│   ├── LoCoMo/             # Conversational memory benchmark
│   └── TGB-V2/             # Temporal Graph Benchmark 2.0
├── docs/
│   ├── dataset_LongMemEval-V2.md
│   ├── dataset_LoCoMo.md
│   ├── dataset_TGB.md
│   ├── graph_schema.md
│   ├── adapter_spec.md
│   ├── experiment_plan.md
│   ├── research_agenda.md
│   └── model_blueprint.md
└── venv/
```

---

## Status

- [x] Dataset collection: LongMemEval-V2, LoCoMo
- [x] Dataset collection: TGB 2.0 (`tkgl-smallpedia` — 1.1M edges, 47k nodes)  ← `datasets/TGB-V2/`
- [x] Research questions and hypotheses finalized in `docs/research_agenda.md`
- [x] Three-phase method roadmap finalized in `docs/model_blueprint.md`
- [x] Unified graph schema draft in `docs/graph_schema.md`
- [x] Dataset adapter specification draft in `docs/adapter_spec.md`
- [x] Experimental roadmap draft in `docs/experiment_plan.md`
- [ ] Unified temporal graph schema design
- [ ] Dataset adapters (LongMemEval-V2 → graph, LoCoMo → graph, TGB → unified format)
- [ ] Phase 1 baseline: flat RAG vs. symbolic temporal subgraph retrieval
- [ ] Phase 2 model: learnable seed scorer + temporal GNN expansion
- [ ] Phase 3 model: path scorer and/or RL fine-tuning
- [ ] Temporal graph memory manager (merge, version, decay)
- [ ] LLM reasoning module over subgraph context
- [ ] Evaluation pipeline

---

## Citation

If you use this work, please cite the benchmarks used:

```bibtex
@article{wu2026longmemevalv2,
  title={LongMemEval-V2: Evaluating Long-Term Agent Memory Toward Experienced Colleagues},
  author={Di Wu and Zixiang Ji and Asmi Kawatkar and Bryan Kwan and Jia-Chen Gu and Nanyun Peng and Kai-Wei Chang},
  year={2026}, eprint={2605.12493}
}

@article{maharana2024evaluating,
  title={Evaluating very long-term conversational memory of llm agents},
  author={Maharana, Adyasha and Lee, Dong-Ho and Tulyakov, Sergey and Bansal, Mohit and Barbieri, Francesco and Fang, Yuwei},
  journal={arXiv preprint arXiv:2402.17753}, year={2024}
}

@article{huang2024tgb2,
  title={TGB 2.0: A Benchmark for Learning on Temporal Knowledge Graphs and Heterogeneous Graphs},
  author={Gastinger, Julia and Huang, Shenyang and Galkin, Mikhail and others},
  journal={Advances in Neural Information Processing Systems}, year={2024}
}
```
