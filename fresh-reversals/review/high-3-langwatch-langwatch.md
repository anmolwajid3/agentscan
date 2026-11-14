# langwatch/langwatch (high)

Old ADR: `dev/docs/adr/101-lwql-clickhouse-access-model-ownership.md`
New ADR: `dev/docs/adr/159-the-app-owns-the-lwql-access-model.md`

## Old ADR status line

** Superseded by [ADR-159](./159-the-app-owns-the-lwql-access-model.md)

## New ADR

ADR-159: The app owns the LangWatchQL access model — one definition, two emitters, delivered to every pod

**Date:** 2026-09-22 (updated 2026-09-23, tasks#889)

## Commits

### a0e8401f6aa2983178febc024f59af84cee4958d (same)

feat(lwql): the app always owns the LangWatchQL access model — remove LWQL_SELF_PROVISION, delete the chart's rendered LWQL path, supersede ADR-101 (#8258) (#8261)

* docs(adr): ADR-141 — the app owns the LangWatchQL access model; supersede ADR-101 (#8258)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01CanFrV78S4Nr2EqFp7RmdD

* feat(clickhouse-serverless): delete the rendered LWQL access model (#8258)

The app self-provisions the LangWatchQL user, profile, row policies and
named collection via SQL DDL on every boot (ADR-141). Remove lwql.go, its
embedded catalog/SQL templates and parity tests, the LWQL config fields,
and the subchart's LWQL secret env/mount. The default user keeps
access_management + named_collection_control and t

Changed files:

- .github/workflows/langwatch-chart.yml
- charts/clickhouse-serverless/README.md
- charts/clickhouse-serverless/templates/_helpers.tpl
- charts/clickhouse-serverless/templates/statefulset.yaml
- charts/clickhouse-serverless/values.yaml
- charts/langwatch/README.md
- charts/langwatch/examples/overlays/clickhouse-external.yaml
- charts/langwatch/examples/overlays/postgres-external.yaml
- charts/langwatch/examples/values-hosted-prod.yaml
- charts/langwatch/examples/values-scalable-prod.yaml
- charts/langwatch/templates/NOTES.txt
- charts/langwatch/templates/_helpers.tpl
- charts/langwatch/templates/app/deployment.yaml
- charts/langwatch/templates/app/secrets.yaml
- charts/langwatch/templates/clickhouse/lwql-access-render.yaml
- charts/langwatch/templates/clickhouse/url-secret.yaml
- charts/langwatch/templates/lwql-passwords-secret.yaml
- charts/langwatch/tests/connect-env.sh
- charts/langwatch/tests/e2e-overlays.sh
- charts/langwatch/tests/e2e.sh
- charts/langwatch/tests/lwql-connection-env.sh
- charts/langwatch/tests/lwql-secret-parity.sh
- charts/langwatch/tests/values-e2e-replicas.yaml
- charts/langwatch/tests/values-e2e.yaml
- charts/langwatch/values.yaml
- dev/docs/adr/101-lwql-clickhouse-access-model-ownership.md
- dev/docs/adr/136-lwql-app-functions-identity-udfs.md
- dev/docs/adr/136-lwql-postgres-catalog-derived-opt-out.md
- dev/docs/adr/142-the-app-owns-the-lwql-access-model.md
- dev/docs/adr/README.md
- infra/clickhouse-serverless/README.md
- infra/clickhouse-serverless/internal/config/config.go
- infra/clickhouse-serverless/internal/config/validate.go
- infra/clickhouse-serverless/internal/render/access.go
- infra/clickhouse-serverless/internal/render/lwql.go
- infra/clickhouse-serverless/internal/render/lwqlKeyMapSelfFilter.sql
- infra/clickhouse-serverless/internal/render/lwqlTenantPredicate.sql
- infra/clickhouse-serverless/internal/render/lwql_catalog.json
- infra/clickhouse-serverless/internal/render/lwql_sourcecolumns_test.go
- infra/clickhouse-serverless/internal/render/lwql_tenantcolumn_test.go

### 2bb91e7911dedce20c0fec19b3a8b29d2c6913a2 (after)

fix(observability): record HTTP duration, bridge gateway metrics over OTLP, bind fleet gauges and read backup age cluster-wide (#8981)

Changed files:

- modules/ops/process/src/repositories/redis/redis.process-fleet-readings.repository.ts

### d391834af0a20044ca3514e2f764cfc7f6842dc4 (after)

fix(ksuid): write the timestamp big-endian so ids sort and match Go and Python (#9577)

Changed files:

- modules/authz/process/src/migrations/legacy-import.authz-grant.migration.ts
- modules/evaluation/contract/package.json
- modules/identity/contract/package.json
- modules/insight/contract/package.json
- packages/clickhouse-migrations/migrations/00130_trace_id_layout.sql
- packages/clickhouse-migrations/migrations/00131_evaluation_runs_id_layout.sql

### 82e552f5c077cf0f589c100cfc3f55927b2e84f6 (after)

fix(model-provider): send each model's output token limit under the name it takes (#9080)

Changed files:

- infra/docker/Dockerfile.go-services

### 6e59382257a939295f754e8b9944091637d69c20 (after)

fix(dataset): close the #9351 review follow-ups and answer added rows with their stored ids (#9532)

Changed files:

- modules/dataset/process/src/services/__tests__/dataset-upsert.postgres-columns.unit.test.ts

### 1959838a062d0ae0dd2f9c48fe67bfa135c74a68 (after)

feat(clickhouse-serverless): per-user caps in access.yaml (#9533)

* feat(clickhouse-serverless): per-user caps in access.yaml

A user may carry caps, its own maxima for six query limits. Each renders in
the user's own profile as the value and a constraint from a floor of at
least 1 to the cap, so the user cannot raise it. A cap may only tighten its
tier: one above the limit rendered for the default profile or the tier is
refused naming the user, at startup and in the sidecar, which keeps the
users already in force. Files without caps render exactly as before.

* test(clickhouse-serverless): build the golden password hash from sha("pw"), not a literal

* chore(secrets): ignore the caps test's old golden hash in this PR's history

* fix(clickhouse-serverless): refuse a fractional cap and a 

Changed files:

- .gitleaksignore
- dev/docs/adr/198-clickhouse-serverless-access-tiers-rolling-passwords-and-token-logins.md
- infra/clickhouse-serverless/README.md
- infra/clickhouse-serverless/internal/access/caps.go
- infra/clickhouse-serverless/internal/access/caps_test.go
- infra/clickhouse-serverless/internal/access/extras.go
- infra/clickhouse-serverless/internal/access/file.go
- infra/clickhouse-serverless/internal/access/plan.go
- infra/clickhouse-serverless/internal/access/sync.go
- infra/clickhouse-serverless/internal/render/tiers_test.go
- infra/clickhouse-serverless/tests/accesse2e/access_e2e_test.go
- specs/clickhouse/serverless-access.feature

### 707db81837e4d3a8205177469ffa231c19aceaa7 (after)

feat(braids): show one project's matching spans in another project's traces (#8946)

Changed files:

- modules/api-key/process/src/repositories/redis/redis.signing-key-usage.repository.ts
- modules/authz/process/src/repositories/redis/__tests__/redis.authz-epoch.repository.unit.test.ts
- modules/authz/process/src/repositories/redis/redis.authz-epoch.repository.ts

### 667a837e2319570c3263b0a48093bf7d46aa2c15 (after)

fix(analytics): make stock dashboard widgets run within LWQL limits (#9507)

Changed files:

- modules/gateway/process/src/repositories/clickhouse/__tests__/support/goose-migration-replay.ts
- modules/trace/process/src/services/trace-evaluation-outcomes-migration.service.ts
- packages/clickhouse-migrations/migrations/00128_stock_widget_light_columns.sql
- packages/clickhouse-migrations/migrations/00129_trace_evaluation_analytics.sql
- packages/clickhouse-migrations/src/__tests__/ttl-reconciler.unit.test.ts
- packages/clickhouse-migrations/src/goose.migration-runner.ts
- packages/clickhouse-migrations/src/ttl.reconciler.ts

### b26728c7c31762a6834977a7e05b6b1ca8f9c011 (after)

fix(clickhouse-serverless): elect the backup runner when system.clusters repeats a replica (#9530)

ClickHouse 26.8 can list each replica of a cluster twice in
system.clusters. The sidecar counted positions by row, so on a
three-replica cluster it saw six and placed clickhouse-2 at position 4,
which clusterAllReplicas never reports. No replica elected itself and no
backup ran.

Replicas() now counts one position per (shard_num, replica_num), the
numbering clusterAllReplicas uses. A test serves the duplicated rows and
fails on the old code with total 6, self 4.

Changed files:

- infra/clickhouse-serverless/internal/backup/sql.go
- infra/clickhouse-serverless/internal/backup/store.go
- infra/clickhouse-serverless/internal/backup/store_test.go

### 7f72e809899adbdaa0505def37978591573f08a6 (after)

chore(go): bump the toolchain to go1.27.4 for GO-2026-6859 (#9493)

Changed files:

- cmd/go.mod
- infra/clickhouse-serverless/Dockerfile
- infra/clickhouse-serverless/go.mod
- infra/docker/Dockerfile
- infra/docker/Dockerfile.go-services
- infra/docker/Dockerfile.langyagent
- pkg/go.mod
- services/go.mod
- tools/go.mod

### 718c4331849ff2fad82eec738a73d29bc822e540 (after)

fix(clickhouse): untangle the two 00125 migrations (rename to 00126, repair 00127) (#9494)

Changed files:

- packages/clickhouse-migrations/migrations/00126_trace_analytics_metadata_columns.sql
- packages/clickhouse-migrations/migrations/00127_repair_experiment_runs_concurrency.sql
- packages/clickhouse-migrations/src/__tests__/trace-analytics-metadata-columns.integration.test.ts

### 40d7ac7a47229c00a228dd02fd534827279ca4c3 (after)

fix(ci): publish langwatch-clickhouse-serverless to the artifacts ECR again (#9492)

fix(ci): publish langwatch-clickhouse-serverless to the artifacts ECR again, now its repository exists

Changed files:

- .github/workflows/publish-docker-ecr.yml
- specs/ci/publish-ecr-images.feature
