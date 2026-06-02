# Dataset: TGB 2.0

- **Role in project:** Robustness B — temporal graph core
- **Source:** https://github.com/shenyangHuang/TGB
- **Website:** https://tgb.complexdatalab.com/
- **Paper:** [NeurIPS 2024 Datasets & Benchmarks](https://openreview.net/forum?id=EADRzNJFn1)
- **License:** MIT (code); see TGB website for individual dataset licenses
- **Local path:** `datasets/TGB/`

---

## Overview

Temporal Graph Benchmark 2.0 (TGB 2.0) is a benchmarking framework for evaluating machine learning on **Temporal Knowledge Graphs (TKGs)** and **Temporal Heterogeneous Graphs (THGs)**. It extends the original TGB (NeurIPS 2023) with 8 new large-scale, multi-relational datasets spanning 5 domains, with up to 53 million edges.

For TCGM, TGB 2.0 provides a **pure temporal graph reasoning** evaluation environment — no text, no dialogue, just structured entities, typed relations, and timestamps — allowing us to isolate and evaluate the core temporal graph reasoning capability of the framework independently of language understanding.

---

## TGB 2.0 Dataset Groups

| Prefix | Type | Description |
|--------|------|-------------|
| `tkgl-*` | Temporal Knowledge Graph | Multi-relational, typed edges with timestamps |
| `thgl-*` | Temporal Heterogeneous Graph | Multiple node/edge types with timestamps |
| `tgbl-*` | Temporal Homogeneous Graph (link) | Single-relation dynamic link prediction (TGB 1.0) |
| `tgbn-*` | Temporal Homogeneous Graph (node) | Node property prediction |

---

## Selected Datasets for TCGM

### Primary: `tkgl-smallpedia`

| Property | Value |
|----------|-------|
| Type | Temporal Knowledge Graph |
| Source | Wikidata (small subset) |
| Scale | Small (prototyping) |
| Task | Temporal link prediction |
| Use in TCGM | Prototype graph reasoning pipeline, debug schema |

### Scale-up: `tkgl-icews`

| Property | Value |
|----------|-------|
| Type | Temporal Knowledge Graph |
| Source | ICEWS (political event database) |
| Scale | Large |
| Task | Temporal link prediction |
| Use in TCGM | Stress-test temporal event reasoning at scale |

---

## Installation

TGB uses `py-tgb`, a pip package that auto-downloads datasets on first use:

```bash
pip install py-tgb
```

Loading a dataset:
```python
from tgb.linkproppred.dataset import LinkPropPredDataset

dataset = LinkPropPredDataset(name="tkgl-smallpedia", root="datasets/TGB/", verbose=True)
data = dataset.full_data
```

---

## Data Format

After auto-download, each dataset expands to:
```
datasets/TGB/
└── tkgl-smallpedia/
    ├── tkgl-smallpedia_edgelist.csv     # (src, dst, rel, ts) edges
    ├── tkgl-smallpedia_ns_test.pkl      # Negative samples (test)
    ├── tkgl-smallpedia_ns_val.pkl       # Negative samples (val)
    └── tkgl-smallpedia_meta.json        # Dataset metadata
```

### Edge list schema
```
src_id, dst_id, relation_type, timestamp
```

- `src_id`, `dst_id`: integer node IDs (mapped to entity names via metadata)
- `relation_type`: integer relation type ID
- `timestamp`: Unix timestamp or integer time step

---

## Task: Temporal Link Prediction

Given a query `(subject, relation, ?, t)`, predict the correct object entity at time `t`. Evaluated using **MRR** (Mean Reciprocal Rank) with a filtered evaluation protocol (corrupted negatives).

This is the TKG analog of:
> "Who was the president of France in January 2020?"

---

## Why This Dataset for TCGM

TGB 2.0 validates the **temporal graph core** of the TCGM framework in isolation:

1. **Pure graph structure** — no language ambiguity; all reasoning must come from graph topology + temporal constraints.
2. **Standard benchmark with leaderboard** — results are directly comparable to established temporal graph learning methods (TGN, TLogic, RE-GCN, RecurrencyBaseline, etc.).
3. **Multi-relational** — typed edges are critical; leveraging relation types is shown to be essential for high performance in TGB 2.0 experiments.
4. **Scalable progression** — `tkgl-smallpedia` for fast iteration, `tkgl-icews` for production-level stress testing.

---

## Graph Mapping Strategy for TCGM

TGB datasets are already in temporal graph format. The adapter work is minimal:

| TGB element | TCGM graph element |
|-------------|-------------------|
| `(src, rel, dst, t)` edge | **Temporal edge** with typed relation and timestamp |
| `src`, `dst` node IDs | **Entity nodes** |
| `relation_type` | **Relation label** (edge type) |
| `timestamp` | **Temporal attribute** on edge |

The main contribution here is unifying this schema with the LoCoMo and LongMemEval-V2 adapters into a single TCGM graph store.

---

## Evaluation Metrics

| Metric | Description |
|--------|-------------|
| **MRR** | Mean Reciprocal Rank — primary metric |
| **Hits@1** | Fraction of queries where correct entity is rank 1 |
| **Hits@10** | Fraction of queries where correct entity is in top 10 |

Evaluation uses **filtered** negative sampling (1-vs-q strategy per edge type).

---

## Baselines on `tkgl-smallpedia` (from TGB 2.0 paper)

| Method | MRR |
|--------|-----|
| RecurrencyBaseline (train) | Best simple heuristic |
| TLogic | Rule-based temporal reasoning |
| RE-GCN | GNN-based |
| TGN | Memory-augmented GNN |
| **TCGM (ours)** | *TBD* |

---

## Citation

```bibtex
@article{huang2024tgb2,
  title={TGB 2.0: A Benchmark for Learning on Temporal Knowledge Graphs and Heterogeneous Graphs},
  author={Gastinger, Julia and Huang, Shenyang and Galkin, Mikhail and Loghmani, Erfan and
          Parviz, Ali and Poursafaei, Farimah and Danovitch, Jacob and Rossi, Emanuele and
          Koutis, Ioannis and Stuckenschmidt, Heiner and Rabbany, Reihaneh and Rabusseau, Guillaume},
  journal={Advances in Neural Information Processing Systems},
  year={2024}
}
```
