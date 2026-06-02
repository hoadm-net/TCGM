# Graph Schema: TCGM

This document defines the initial unified graph schema for **Temporal Conversational Graph Memory (TCGM)**. The design target is a schema that is:

- expressive enough for dialogue, agent trajectories, and temporal KG data
- simple enough to support a strong Phase 1 symbolic baseline
- structured enough to support Phase 2 and Phase 3 learnable retrieval

---

## Design Goals

The schema should support five core needs:

1. represent long-horizon memory as a temporal multi-relational graph
2. preserve provenance so evidence can be traced back to source data
3. make state changes explicit rather than burying them inside text chunks
4. support time-aware and relation-aware retrieval
5. remain compatible with learnable node scoring, graph expansion, and path scoring

---

## Canonical Node Types

### 1. `Entity`

Persistent objects that can participate in events or hold states.

Examples:

- speakers in LoCoMo
- UI elements, pages, or tools in LongMemEval-V2
- entities in TGB 2.0 temporal knowledge graphs

Suggested fields:

- `node_id`
- `node_type = Entity`
- `entity_type`
- `canonical_name`
- `aliases`
- `dataset`
- `metadata`

### 2. `Event`

The central unit of memory. Events capture what happened, when it happened, and which entities were involved.

Examples:

- a dialogue turn
- a session-level summarized event
- an agent action or observation change
- a temporal KG fact treated as an atomic event

Suggested fields:

- `node_id`
- `node_type = Event`
- `event_type`
- `text`
- `start_time`
- `end_time`
- `time_granularity`
- `order_index`
- `dataset`
- `metadata`

### 3. `Episode`

Higher-level containers that organize events into longer segments.

Examples:

- conversation session in LoCoMo
- trajectory in LongMemEval-V2
- document or time bucket if needed for TGB-based grouping

Suggested fields:

- `node_id`
- `node_type = Episode`
- `episode_type`
- `label`
- `start_time`
- `end_time`
- `dataset`
- `metadata`

### 4. `State`

Represents persistent or semi-persistent facts that can be created, updated, invalidated, or temporally constrained.

Examples:

- speaker preferences or plans in LoCoMo
- interface affordances or environment gotchas in LongMemEval-V2
- active relation state inferred from temporal KG facts

Suggested fields:

- `node_id`
- `node_type = State`
- `state_type`
- `text`
- `start_time`
- `end_time`
- `status`
- `dataset`
- `metadata`

---

## Canonical Edge Types

### Structural Edges

- `PART_OF`: `Event -> Episode`
- `HAS_STATE`: `Entity -> State`
- `SUPPORTED_BY`: `Event/State -> provenance source`

### Participation Edges

- `INVOLVES`: `Event -> Entity`
- `MENTIONS`: `Event -> Entity/State`

### Temporal and Causal Edges

- `BEFORE`: `Event -> Event`
- `AFTER`: optional inverse of `BEFORE`
- `CAUSES` or `ENABLES`: `Event -> Event`
- `UPDATES`: `Event -> State`
- `SUPERSEDES`: `State -> State`

### Retrieval-Oriented Edges

- `REFERS_TO`: optional query-to-node edge used in training or analysis
- `EVIDENCE_FOR`: optional link from answer-supporting nodes to labeled questions

---

## Temporal Representation

The initial schema should use **valid time** rather than full bi-temporal modeling.

Each event or state can carry:

- `start_time`
- `end_time`
- `time_granularity`
- `order_index`

### Rules

1. If exact timestamps exist, use them.
2. If only relative order exists, use `order_index`.
3. If a fact spans a duration, use an interval.
4. If an event is atomic, set `start_time = end_time`.

This is sufficient for Phase 1 symbolic retrieval and Phase 2 temporal graph learning.

---

## Provenance Requirements

Every retrievable event or state should preserve a pointer to source evidence.

Minimum provenance fields:

- `source_dataset`
- `source_item_id`
- `source_turn_id` or `source_step_id` when available
- `source_span` or offsets when available
- `confidence`

Provenance is mandatory because it supports:

- answer faithfulness
- evidence-level evaluation
- interpretability
- error analysis

---

## Dataset Mapping

## LoCoMo

### Mapping

- `Episode`: session
- `Event`: dialogue turn and optionally event-summary item
- `Entity`: speakers, people, places, objects
- `State`: persona facts, preferences, plans, relations

### Temporal Signals

- `session_date_time`
- turn order inside session

### Phase 1 Recommendation

Start with turn-level events, then compare against a summary-event variant.

---

## LongMemEval-V2

### Mapping

- `Episode`: trajectory
- `Event`: agent action, observation change, failure, workflow step
- `Entity`: pages, tools, interface objects, environment concepts
- `State`: workflow rules, affordances, dynamic state, premise constraints

### Useful Event Subtypes

- `ActionEvent`
- `ObservationEvent`
- `FailureEvent`
- `StrategyEvent`

### Phase 1 Recommendation

Represent each step as an event and separately induce states from repeated observations or workflow annotations.

---

## TGB 2.0

### Mapping

- `Entity`: native TKG entities
- `Event` or typed temporal edge: fact `(src, rel, dst, t)`
- `State`: optional, only if persistent fact abstraction is needed later

### Phase 1 Recommendation

Keep TGB close to its native temporal multi-relational structure. The unified interface matters more than forcing the exact same storage representation used for dialogue data.

---

## Canonical Storage Format

The schema should serialize cleanly into four tables.

### `nodes`

- `node_id`
- `node_type`
- `label`
- `text`
- `dataset`
- `metadata`

### `edges`

- `src_id`
- `edge_type`
- `dst_id`
- `start_time`
- `end_time`
- `weight`
- `metadata`

### `provenance`

- `target_id`
- `source_id`
- `source_type`
- `offset`
- `confidence`

### `queries`

- `query_id`
- `question`
- `answer`
- `time_anchor`
- `gold_evidence`

---

## Retrieval Implications

The schema is designed so retrieval can progress across phases.

### Phase 1

- heuristic seed selection
- symbolic temporal filtering
- typed-edge neighborhood expansion

### Phase 2

- learnable seed scorer over `Entity`, `Event`, and `State`
- query-conditioned temporal GNN expansion over typed edges

### Phase 3

- path scoring or RL-based traversal and stopping decisions

This means the schema is not only a data format. It is also the interface between symbolic memory construction and learnable retrieval.

---

## Open Questions

The current schema draft intentionally leaves a few decisions open:

1. whether `State` nodes should always be explicit or induced only for selected datasets
2. whether TGB facts should be materialized as event nodes or kept as temporal edges only
3. how aggressively entity canonicalization should merge aliases in noisy dialogue data
4. whether causal edges should be induced early or deferred to later stages

These questions should be resolved with small ablations during Phase 1, not by prematurely expanding schema complexity.