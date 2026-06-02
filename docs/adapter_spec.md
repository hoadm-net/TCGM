# Adapter Specification: TCGM

This document defines the implementation contract for dataset adapters in TCGM. Its purpose is to ensure that adapters for LoCoMo, LongMemEval-V2, and TGB-V2 produce a common output format that is compatible with:

- the unified graph schema in `graph_schema.md`
- the Phase 1 symbolic baseline
- the Phase 2 learnable temporal graph retriever
- the Phase 3 path scorer or RL refinement

The adapter layer should remain mostly deterministic. Its job is to normalize heterogeneous raw datasets into a shared graph-ready representation, not to perform the main reasoning contribution.

---

## Adapter Responsibilities

Every dataset adapter must do five things.

1. Load raw dataset files.
2. Normalize time, identifiers, and provenance.
3. Emit canonical `nodes`, `edges`, `provenance`, and `queries` tables.
4. Preserve enough source information for evidence tracing.
5. Avoid irreversible transformations that would block later ablations.

Adapters should not:

- run the final retriever
- perform end-task answer generation
- rely on hidden dataset-specific heuristics that cannot be reproduced or turned off

---

## Canonical Output Contract

Each adapter must emit four artifacts.

## 1. `nodes`

Minimum columns:

- `node_id`
- `node_type`
- `label`
- `text`
- `dataset`
- `metadata`

Allowed `node_type` values for Phase 1:

- `Entity`
- `Event`
- `Episode`
- `State`

## 2. `edges`

Minimum columns:

- `src_id`
- `edge_type`
- `dst_id`
- `start_time`
- `end_time`
- `weight`
- `metadata`

Edge types should come from the shared schema whenever possible:

- `PART_OF`
- `INVOLVES`
- `MENTIONS`
- `BEFORE`
- `UPDATES`
- `HAS_STATE`
- `SUPPORTED_BY`
- optional dataset-specific subtypes stored in `metadata`

## 3. `provenance`

Minimum columns:

- `target_id`
- `source_dataset`
- `source_item_id`
- `source_unit_id`
- `source_type`
- `source_span`
- `confidence`

`source_unit_id` should resolve to the smallest useful unit available in the raw dataset.

Examples:

- dialogue turn id in LoCoMo
- trajectory step id in LongMemEval-V2
- temporal fact row id in TGB-V2

## 4. `queries`

Minimum columns:

- `query_id`
- `question`
- `answer`
- `dataset`
- `question_type`
- `time_anchor`
- `gold_evidence`
- `metadata`

If the raw dataset has no explicit `time_anchor`, adapters should set it to `null` and rely on later query parsing or order-aware retrieval.

---

## Global Adapter Rules

## Identifier Rules

All IDs must be deterministic and stable across reruns.

Recommended pattern:

- `locomo:sample_001:event:d_014`
- `lmev2:traj_0007:event:step_083`
- `tgbv2:tkgl-smallpedia:event:row_421881`

Do not use random UUIDs in adapter output.

## Time Rules

Every `Event`, `Episode`, and `State` should carry either:

- exact `start_time` and `end_time`, or
- a valid `order_index` in `metadata`

If exact timestamps do not exist, adapters must still encode a consistent local order.

## Provenance Rules

Every `Event` and `State` must have at least one provenance record.

If an adapter induces a `State` from multiple raw items, it should either:

- attach multiple provenance rows, or
- attach a compact provenance list inside `metadata`

## Reversibility Rules

Adapters should preserve enough raw fields in `metadata` to support later debugging and ablation.

Examples:

- raw speaker names
- raw relation ids
- raw session numbers
- raw timestamps before normalization
- raw step text or action payload

---

## LoCoMo Adapter

## Raw Inputs

Primary input:

- `datasets/LoCoMo/data/locomo10.json`

Optional supporting inputs:

- `datasets/LoCoMo/data/msc_personas_all.json`
- `datasets/LoCoMo/data/multimodal_dialog/`

## Primary Units

- conversation sample
- session
- dialogue turn
- event summary item
- QA pair

## Required Mapping

### `Episode`

Create one `Episode` node per session.

Required fields:

- session timestamp as `start_time`
- conversation/sample identifier
- session index in `metadata`

### `Event`

Phase 1 default:

- create one `Event` node per dialogue turn

Optional Phase 1 ablation:

- create one `Event` node per annotated event summary item

Required fields:

- speaker
- turn text
- session-local order
- global conversation order
- multimodal fields if present

### `Entity`

At minimum, create:

- speaker A entity
- speaker B entity

Optional extraction:

- people, places, and objects mentioned in turns or summaries

### `State`

Initial Phase 1 recommendation:

- keep explicit state creation conservative
- induce only high-confidence states such as preferences, relationships, and long-lived plans when easily recoverable from summaries or repeated mentions

## Required Edges

- `PART_OF`: turn event to session episode
- `INVOLVES`: turn event to speaker entity
- `BEFORE`: between adjacent turn events
- `MENTIONS`: from turn event to named entities if extraction is enabled

## Query Output

One `queries` row per QA pair.

Map:

- `question` from raw QA
- `answer` from raw QA
- `question_type` from category
- `gold_evidence` from `evidence` dia_ids

If `gold_evidence` references turn ids, adapters should resolve them to canonical event ids.

## Validation Checks

- every QA evidence id resolves to an event id
- every session has ordered events
- both speakers are represented as entities
- all turn events point to exactly one session episode

---

## LongMemEval-V2 Adapter

## Raw Inputs

Primary inputs:

- `datasets/LongMemEval-V2/data/longmemeval-v2/questions.jsonl`
- `datasets/LongMemEval-V2/data/longmemeval-v2/trajectories.jsonl`

Optional supporting assets:

- screenshots and haystack files for provenance linking

## Primary Units

- trajectory
- trajectory step
- question
- optional external artifacts such as screenshots

## Required Mapping

### `Episode`

Create one `Episode` node per trajectory.

Required fields:

- trajectory id
- trajectory-level metadata

### `Event`

Create one `Event` node per trajectory step.

Recommended event subtypes:

- `ActionEvent`
- `ObservationEvent`
- `FailureEvent`
- `StrategyEvent`

Required fields:

- step text or structured content
- step index
- available timestamp or local order
- trajectory id

### `Entity`

At minimum, create entities for:

- pages
- tools
- interface objects when clearly available
- environment concepts referenced in questions or step text

### `State`

This dataset is a priority for explicit state induction.

Adapters should expose candidate states for:

- interface affordances
- workflow preconditions
- dynamic environment status
- repeated gotchas or constraints

State induction should remain conservative and traceable to source steps.

## Required Edges

- `PART_OF`: step event to trajectory episode
- `BEFORE`: between adjacent steps
- `INVOLVES`: event to extracted entities
- `UPDATES`: event to induced state when a step changes or reveals a durable fact
- `SUPPORTED_BY`: event or state to raw step provenance

## Query Output

One `queries` row per question.

Required fields:

- question text
- answer
- question category or memory ability if available
- trajectory references or supporting identifiers in `gold_evidence` when recoverable

If gold evidence is not explicit, store `gold_evidence = null` and preserve raw linking fields in `metadata`.

## Validation Checks

- every step event belongs to exactly one trajectory episode
- step order is strictly increasing within a trajectory
- induced states have provenance
- query metadata preserves raw question identifiers and memory ability labels

---

## TGB-V2 Adapter

## Raw Inputs

Primary inputs under `datasets/TGB-V2/`:

- edgelist CSV
- negative sample files
- auxiliary metadata files

Initial Phase 1 target:

- `tkgl-smallpedia`

## Primary Units

- temporal fact row `(src, rel, dst, t)`
- dataset split metadata
- optional negative samples for evaluation

## Required Mapping

### `Entity`

Create one `Entity` node per unique source or destination node id.

Required fields:

- canonical entity id
- original raw node id in `metadata`

### `Event` or Edge-First Representation

Phase 1 recommendation:

- allow a hybrid representation
- facts may remain primarily in `edges`, but adapters should still expose canonical provenance rows and optional event ids when needed for unified evaluation

Minimum requirement:

- every raw fact must be representable as a retrievable temporal relation in the canonical output

### `Episode`

Optional in Phase 1.

If used, episodes can represent:

- coarse time buckets
- dataset partitions

Do not force episode creation unless it supports a concrete retrieval need.

### `State`

Optional in Phase 1.

State nodes are not required unless a later ablation tests persistent fact abstractions.

## Required Edges

At minimum, create canonical temporal edges with:

- source entity id
- relation type
- destination entity id
- timestamp as `start_time = end_time`

Store original relation id and raw row id in `metadata`.

## Query Output

TGB-V2 is not a natural language QA dataset, so `queries` must be normalized from link prediction format.

Recommended representation:

- `question` as a templated textual query or structured query object
- `answer` as target destination entity id
- `question_type = link_prediction`
- `time_anchor` from raw timestamp
- `gold_evidence` may point to the target fact id or remain null depending on evaluation protocol

The exact query serialization can evolve, but it must be deterministic and shared across experiments.

## Validation Checks

- every fact row maps to a valid temporal edge
- all referenced entities exist in `nodes`
- timestamps are normalized consistently
- query serialization is deterministic for reruns

---

## Shared Validation Suite

Every adapter should pass a shared validation routine.

Required checks:

1. no duplicate `node_id`
2. no edges referencing missing nodes
3. every event has provenance
4. every query has a stable `query_id`
5. time fields are parseable or explicitly null
6. all IDs are deterministic across reruns

Recommended report fields:

- number of nodes by type
- number of edges by type
- number of queries
- percentage of queries with gold evidence
- percentage of events with exact timestamps vs order-only timestamps

This report should be saved with adapter outputs for debugging and reproducibility.

---

## Output Layout

Recommended output layout per dataset:

```text
artifacts/
  adapters/
    locomo/
      nodes.parquet
      edges.parquet
      provenance.parquet
      queries.parquet
      validation.json
    longmemeval_v2/
      nodes.parquet
      edges.parquet
      provenance.parquet
      queries.parquet
      validation.json
    tgb_v2_tkgl_smallpedia/
      nodes.parquet
      edges.parquet
      provenance.parquet
      queries.parquet
      validation.json
```

Any equivalent layout is acceptable as long as it is deterministic and versionable.

---

## Phase Boundaries

To prevent scope creep, adapter responsibilities should be phased.

### Required in Phase 1

- canonical outputs
- time normalization
- provenance preservation
- conservative entity extraction
- conservative state induction

### Deferred to Phase 2+

- neural entity linking
- aggressive state induction
- learned temporal relation inference
- query-conditioned adapter behavior

Adapters should make these future extensions possible, but should not try to solve them upfront.