# Temporal Conversational Graph Memory for Long-Horizon QA

> Research project exploring a unified framework for **Temporal Graph Reasoning** over long-horizon conversations and knowledge graphs, with applications in multi-turn QA, episodic memory retrieval, and agent dialogue understanding.

---

## Research Direction

Modern LLM agents are increasingly deployed in long-horizon, conversational settings where facts evolve, contradict, and become stale over time. Existing approaches treat memory as flat text retrieval (RAG) or ignore temporal structure entirely. This project proposes a **Temporal Conversational Graph Memory** framework that structures conversational history and external knowledge as a dynamic temporal graph, enabling principled multi-hop and time-constrained reasoning for question answering.

**Core hypothesis:** Structuring conversational and factual memory as a temporal graph — rather than flat retrieval — enables more accurate, consistent, and interpretable QA over long-horizon interactions.

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
│  Temporal Subgraph   │   ← Query-driven retrieval with time constraints
│  Retriever           │      and multi-hop graph traversal
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

See [`docs/`](docs/) for detailed dataset documentation and the [`research_agenda.md`](docs/research_agenda.md) roadmap.

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
│   └── research_agenda.md
└── venv/
```

---

## Status

- [x] Dataset collection: LongMemEval-V2, LoCoMo
- [x] Dataset collection: TGB 2.0 (`tkgl-smallpedia` — 1.1M edges, 47k nodes)  ← `datasets/TGB-V2/`
- [x] Research questions and hypotheses finalized in `docs/research_agenda.md`
- [ ] Unified temporal graph schema design
- [ ] Dataset adapters (LongMemEval-V2 → graph, LoCoMo → graph, TGB → unified format)
- [ ] Baseline: flat RAG vs. temporal subgraph retrieval
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
