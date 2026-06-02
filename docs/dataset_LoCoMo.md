# Dataset: LoCoMo

- **Role in project:** Robustness A — long conversational memory
- **Source:** https://github.com/snap-research/locomo
- **Paper:** [arXiv:2402.17753](https://arxiv.org/abs/2402.17753) (ACL 2024)
- **License:** See repo LICENSE.txt
- **Local path:** `datasets/LoCoMo/data/locomo10.json`

---

## Overview

LoCoMo is a high-quality benchmark for evaluating **very long-term conversational memory** in LLM agents. It consists of 10 carefully curated multi-session conversations between two speakers, spanning weeks to months of simulated social interaction, annotated for:

- **Question answering** over the full conversation history
- **Event summarization** per speaker per session
- **Multimodal dialog generation** (images referenced via URLs)

---

## Statistics

| Property | Value |
|----------|-------|
| Conversations | 10 |
| Sessions per conversation | Multiple, ordered with timestamps |
| Turns per conversation | ~500–600 average |
| QA pairs | ~300 per conversation |
| Domains | Social, personal life, daily events |
| Release | March 2024 (ACL 2024) |

---

## Data Structure

```
datasets/LoCoMo/
├── README.MD
├── LICENSE.txt
└── data/
    ├── locomo10.json          # Main dataset file (2.7MB)
    ├── msc_personas_all.json  # Persona pool for generation
    └── multimodal_dialog/     # Example agent persona configs
```

### `locomo10.json` schema (per sample)
```json
{
  "sample_id": "...",
  "speaker_a": "Alice",
  "speaker_b": "Bob",
  "conversation": {
    "session_1": [...],
    "session_1_date_time": "2023-01-05 14:30:00",
    "session_2": [...],
    "session_2_date_time": "2023-01-19 10:00:00",
    ...
  },
  "observation": {
    "session_1_observation": "...",
    ...
  },
  "session_summary": {
    "session_1_summary": "...",
    ...
  },
  "event_summary": {
    "events_session_1": [...],
    ...
  },
  "qa": [
    {
      "question": "...",
      "answer": "...",
      "category": "single_hop | multi_hop | ...",
      "evidence": ["dia_id_1", "dia_id_2"]
    }
  ]
}
```

### Turn schema
```json
{
  "speaker": "Alice",
  "dia_id": "d_001",
  "text": "...",
  "img_url": "...",         // optional
  "blip_caption": "...",    // optional
  "search_query": "..."     // optional
}
```

---

## QA Categories

| Category | Description |
|----------|-------------|
| `single_hop` | Answer found in a single session/turn |
| `multi_hop` | Answer requires connecting events across sessions |
| `temporal` | Requires temporal ordering or dating of events |
| `adversarial` | Tests robustness against confounding context |

---

## Why This Dataset for TCGM

LoCoMo is the best available benchmark for testing **conversational temporal graph memory** because:

1. **Sessions have explicit timestamps** — `session_<n>_date_time` fields provide wall-clock anchors, enabling true temporal graph construction.
2. **Multi-session, long-horizon** — conversations span weeks/months; facts mentioned early affect later sessions, requiring persistent memory across time.
3. **Event summaries are annotated** — ground-truth `events_session_<n>` annotations let us evaluate whether the graph builder correctly identifies and links events.
4. **Both speakers are tracked** — dual-speaker graph with separate entity timelines for each speaker, their states, and their shared interactions.

---

## Graph Mapping Strategy for TCGM

| Conversation element | Graph element |
|---------------------|--------------|
| Speaker (A, B) | **Entity node** (persistent across sessions) |
| Session | **Episode node** with timestamp |
| Utterance / turn | **Event node**, linked to speaker and episode |
| Named entity in turn | **Entity node** (person, place, object) |
| Cross-session reference | **Temporal edge** (e.g., "remember when...") |
| QA evidence dia_ids | **Provenance edges** from question to supporting turns |

Session timestamps allow edges to be stamped with real time intervals, making the LoCoMo graph a genuine **temporal knowledge graph** extracted from dialogue.

---

## Evaluation Metrics

- **Exact Match (EM)** and **F1** over QA pairs
- **Event coverage** — fraction of ground-truth events captured by the graph builder (custom metric for TCGM)
- **Memory recall@k** — fraction of QA evidence turns retrieved in top-k subgraph results
