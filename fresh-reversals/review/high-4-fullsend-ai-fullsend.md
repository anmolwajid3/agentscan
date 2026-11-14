# fullsend-ai/fullsend (high)

Old ADR: `docs/ADRs/0076-slash-command-entity-context-separation.md`
New ADR: `docs/ADRs/0141-deterministic-filtered-entity-context-staging.md`

## Old ADR status line

Accepted

## New ADR

Deterministic filtered entity-context-snapshot staging

Date: 2026-09-07

## Commits

### 4238860065e0d9d2fa17136abc2acacebfba01c5 (after)

docs(#6407): specify stable entity context snapshots

Separate immutable record content from mutable thread state, move the byte-level contract into a normative v1 specification, and define cleanup outside retained run artifacts.

Signed-off-by: Barak Korren <bkorren@redhat.com>
Assisted-by: Codex (gpt-5.6-sol)

Changed files:

- docs/ADRs/0107-deterministic-filtered-entity-context-staging.md
- docs/normative/entity-context/v1/README.md
- docs/normative/entity-context/v1/check.schema.json
- docs/normative/entity-context/v1/commits.schema.json
- docs/normative/entity-context/v1/entity.schema.json
- docs/normative/entity-context/v1/index.schema.json
- docs/normative/entity-context/v1/thread-state.schema.json

### 2b2f6155a08cd82d33cc29805906d2942be61bf8 (after)

docs(#6407): make conversation context cache-stable

Include immutable attribution in each conversation record and define canonical whole-conversation and per-thread views whose normal reply path preserves the existing byte prefix.

Signed-off-by: Barak Korren <bkorren@redhat.com>
Assisted-by: Codex (gpt-5.6-sol)

Changed files:

- docs/ADRs/0107-deterministic-filtered-entity-context-staging.md
- docs/normative/entity-context/v1/README.md
- docs/normative/entity-context/v1/entity.schema.json
- docs/normative/entity-context/v1/index.schema.json
- docs/normative/entity-context/v1/thread-state.schema.json

### c84c43bf30be9d5664ce5288ab48531a4126391e (after)

docs(#6407): avoid duplicate conversation views

Store each attributed conversation record once, name records for chronological glob concatenation, and use lightweight thread order files for thread-specific assembly.

Signed-off-by: Barak Korren <bkorren@redhat.com>
Assisted-by: Codex (gpt-5.6-sol)

Changed files:

- docs/ADRs/0107-deterministic-filtered-entity-context-staging.md
- docs/normative/entity-context/v1/README.md
- docs/normative/entity-context/v1/index.schema.json
- docs/normative/entity-context/v1/thread-state.schema.json

### a62360964963401297ef235289d567908ddee3a3 (after)

docs(adr): clarify entity context history and caching

Define segmented projections and runtime cache boundaries so repeated agents can reuse stable prompt prefixes without overstating token savings.

Record review relationships, immutable agent-run lineage, richer commit history, collection profiles, and explicit source gaps. Document the required follow-up work for runtimes, forge adapters, and shipped agents.

Signed-off-by: Barak Korren <bkorren@redhat.com>
Assisted-by: Codex (gpt-5.6-sol)

Changed files:

- docs/ADRs/0107-deterministic-filtered-entity-context-staging.md
- docs/architecture.md
- docs/normative/entity-context/v1/README.md
- docs/normative/entity-context/v1/agent-runs.schema.json
- docs/normative/entity-context/v1/commits.schema.json
- docs/normative/entity-context/v1/index.schema.json
- docs/normative/entity-context/v1/reviews.schema.json
- docs/normative/entity-context/v1/thread-state.schema.json

### f8443018970e9ee32405515f61461ef4fa405487 (after)

docs(adr): separate entity and repository context

Limit staged entity context to forge state that cannot be reconstructed from Git. Remove diff, commit, and repository-topology materialization while retaining Git object IDs as review, thread, and agent-run relationship anchors.

Assign repository history provisioning and derived, filtered diff generation to Fullsend controllers.

Signed-off-by: Barak Korren <bkorren@redhat.com>
Assisted-by: Codex (gpt-5.6-sol)

Changed files:

- docs/ADRs/0107-deterministic-filtered-entity-context-staging.md
- docs/architecture.md
- docs/normative/entity-context/v1/README.md
- docs/normative/entity-context/v1/commits.schema.json
- docs/normative/entity-context/v1/entity.schema.json
- docs/normative/entity-context/v1/index.schema.json
- docs/normative/entity-context/v1/reviews.schema.json

### 5e0485538e95cb45643ed1a4495c1882aa968b83 (after)

docs(#6407): align entity context contract

Make v1 schema compatibility explicitly closed, align schema identifiers with the normative convention, and restore the filter-status definition flow.

Signed-off-by: Barak Korren <bkorren@redhat.com>
Assisted-by: Codex (gpt-5.6-sol)

Changed files:

- docs/normative/entity-context/v1/README.md
- docs/normative/entity-context/v1/agent-runs.schema.json
- docs/normative/entity-context/v1/check.schema.json
- docs/normative/entity-context/v1/entity.schema.json
- docs/normative/entity-context/v1/index.schema.json
- docs/normative/entity-context/v1/reviews.schema.json
- docs/normative/entity-context/v1/thread-state.schema.json

### 819d0ecf4832da5b3d3f24af9f95243a6b025148 (after)

docs(#6407): tighten entity context canonical bytes

Define omission semantics for optional JSON properties and constrain Git object IDs to supported digest widths.

Signed-off-by: Barak Korren <bkorren@redhat.com>
Assisted-by: Codex (gpt-5.6-sol)

Changed files:

- docs/normative/entity-context/v1/README.md
- docs/normative/entity-context/v1/agent-runs.schema.json
- docs/normative/entity-context/v1/check.schema.json
- docs/normative/entity-context/v1/reviews.schema.json

### f82d5a0b3e492e1c9127cdd0fd018080b3fae6d5 (after)

docs(#6407): address entity context review feedback

Separate immutable records from mutable actor authorization state, align the entity context vocabulary with normalized events, and tighten deterministic serialization and schema constraints.

Signed-off-by: Barak Korren <bkorren@redhat.com>
Assisted-by: Codex (gpt-5.6-sol)

Changed files:

- docs/ADRs/0076-slash-command-entity-context-separation.md
- docs/ADRs/0107-deterministic-filtered-entity-context-staging.md
- docs/normative/entity-context/v1/README.md
- docs/normative/entity-context/v1/actor-state.schema.json
- docs/normative/entity-context/v1/agent-runs.schema.json
- docs/normative/entity-context/v1/check.schema.json
- docs/normative/entity-context/v1/collection.schema.json
- docs/normative/entity-context/v1/common.schema.json
- docs/normative/entity-context/v1/entity.schema.json
- docs/normative/entity-context/v1/index.schema.json
- docs/normative/entity-context/v1/reviews.schema.json
- docs/normative/entity-context/v1/thread-state.schema.json
- docs/normative/normalized-event/v1/README.md

### 78e782a93bef1f74eff8166a7759e24b9f693128 (after)

docs(#6407): remove staged source URLs

Keep forge and record identifiers for provenance while omitting navigation URLs from the agent-visible entity-context contract. Align order/view filtering and required singleton structural failure semantics with the schemas.

Signed-off-by: Barak Korren <bkorren@redhat.com>
Assisted-by: Codex (gpt-5.6-sol)

Changed files:

- docs/normative/entity-context/v1/README.md
- docs/normative/entity-context/v1/agent-runs.schema.json
- docs/normative/entity-context/v1/check.schema.json
- docs/normative/entity-context/v1/common.schema.json
- docs/normative/entity-context/v1/entity.schema.json
- docs/normative/entity-context/v1/index.schema.json

### f3b18a4a85188ed7596462ce0ad46b26f829bcea (after)

docs(#6407): address entity context review comments

Require filtering metadata for emitted check logs, represent never-started GitHub startup failures without invented timestamps, and document the v1 ASCII structural path boundary.

Signed-off-by: Barak Korren <bkorren@redhat.com>
Assisted-by: Codex (gpt-5.6-sol)

Changed files:

- docs/normative/entity-context/v1/README.md
- docs/normative/entity-context/v1/check.schema.json
- docs/normative/entity-context/v1/index.schema.json

### b155f892c99fadbcff254f5bfcef082407617600 (after)

docs(#6407): close entity context review gaps

Make never-started checks schema-visible, fail closed for unusable entity gaps, reject percent-encoded structural paths, and disclose the accepted ADR 0076 annotation.

Signed-off-by: Barak Korren <bkorren@redhat.com>
Assisted-by: Codex (gpt-5.6-sol)

Changed files:

- docs/normative/entity-context/v1/README.md
- docs/normative/entity-context/v1/check.schema.json
- docs/normative/entity-context/v1/common.schema.json

### 6762d747cf6383872c6a2c5127b7decba19b8955 (after)

fix(#6407): normalize pre-start check outcomes

Represent completed skipped and cancelled checks without native start times as explicit never-started records, and define a source-derived completion fallback when terminal timestamps are absent.

Signed-off-by: Barak Korren <bkorren@redhat.com>
Assisted-by: Codex (gpt-5.6-sol)

Changed files:

- docs/normative/entity-context/v1/README.md
- docs/normative/entity-context/v1/check.schema.json
