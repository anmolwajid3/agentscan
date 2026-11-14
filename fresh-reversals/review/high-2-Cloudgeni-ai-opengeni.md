# Cloudgeni-ai/opengeni (high)

Old ADR: `compute/docs/adr/0018-the-control-service-leases-and-fences.md`
New ADR: `compute/docs/adr/0015-placement-and-moves-between-hosts.md`

## Old ADR status line

Accepted, 2026-10-17. Implements [15](0015-placement-and-moves-between-hosts.md).

## New ADR

Placement and moving sandboxes between hosts

Status: Accepted, 2026-10-17. Built as [18](0018-the-control-service-leases-and-fences.md).

## Commits

### b7ef084ebd9d8aa94e06962f82799e9af914565a (same)

feat(compute): Opengeni compute, a Firecracker sandbox system, off by default (#4970)

compute/ is Opengeni compute, Opengeni's own Firecracker sandbox system: the host agent, decision core, control service, agent link, host identity, guest and images, the computeControl chart component (off by default), the GCP Terraform module, compute CI and release workflows, and an automated end-to-end suite on GCP. Nothing in Opengeni uses it until the compute sandbox backend is selected; Modal stays the default. Full history: tag archive/compute-2026-10.

Changed files:

- .github/workflows/compute-ci.yml
- .github/workflows/compute-release.yml
- compute/.cargo/config.toml
- compute/.dockerignore
- compute/ARCHITECTURE.toml
- compute/Cargo.lock
- compute/Cargo.toml
- compute/NOTICE
- compute/README.md
- compute/architecture-baseline.toml
- compute/ci/gate.sh
- compute/ci/smoke-agent.sh
- compute/ci/smoke-run.sh
- compute/conformance/e2b/.gitignore
- compute/conformance/e2b/README.md
- compute/conformance/e2b/adapter.mjs
- compute/conformance/e2b/check.mjs
- compute/conformance/e2b/package.json
- compute/conformance/e2b/resolve.cjs
- compute/conformance/e2b/run.sh
- compute/conformance/e2b/sdk.mjs
- compute/crates/archcheck/Cargo.toml
- compute/crates/archcheck/README.md
- compute/crates/archcheck/src/baseline.rs
- compute/crates/archcheck/src/baseline/tests.rs
- compute/crates/archcheck/src/config.rs
- compute/crates/archcheck/src/context.rs
- compute/crates/archcheck/src/finding.rs
- compute/crates/archcheck/src/git_base.rs
- compute/crates/archcheck/src/lib.rs
- compute/crates/archcheck/src/main.rs
- compute/crates/archcheck/src/report.rs
- compute/crates/archcheck/src/report/rdjson.rs
- compute/crates/archcheck/src/rules.rs
- compute/crates/archcheck/src/rules/file_size.rs
- compute/crates/archcheck/src/rules/pattern_ratchet.rs
- compute/crates/archcheck/src/rules/ratchet.rs
- compute/crates/archcheck/src/rules/ratchet/tests.rs
- compute/crates/archcheck/tests/cli.rs
- compute/crates/archcheck/tests/repository.rs

### cfde5ba1a883c27b85a2fba8b1590824da8999d9 (after)

fix(worker): Retry of an approval-resumed turn continues from durable history (#7766)

Changed files:

- apps/worker/test/open-suffix-human-retry-postgres.test.ts

### c0089e1c67b916267a7b495d192483986d4a5fea (after)

Agents legacy drop: drop slack_agents and bot_templates, organization access from the agent, one text (#7608)

Changed files:

- docs/migrations-expand-contract.md
- packages/db/drizzle/1437_agent_slack_installs_workspace_check.sql
- packages/db/drizzle/1438_agent_slack_installs_validate_workspace_check.sql
- packages/db/drizzle/1439_agent_slack_installs_workspace_not_null.sql
- packages/db/drizzle/1440_slack_agent_user_states_agent_user_uq_drop.sql
- packages/db/drizzle/1441_slack_agent_intro_posts_agent_channel_uq_drop.sql
- packages/db/drizzle/1442_slack_agents_drop_account_fks.sql
- packages/db/drizzle/1443_slack_agents_drop_connection_fk.sql
- packages/db/drizzle/1444_slack_agents_drop_workspace_fks.sql
- packages/db/drizzle/1445_slack_agents_drop.sql
- packages/db/drizzle/1446_bot_templates_drop.sql
- packages/db/drizzle/1447_agents_legacy_functions_drop.sql
- packages/db/drizzle/1448_agents_organization_access_backfill.sql
- packages/db/drizzle/1449_agent_revisions_content_bounds_check.sql
- packages/db/drizzle/1450_agent_revisions_validate_content_bounds_check.sql
- packages/db/drizzle/1451_agent_revisions_drop_bounds_check.sql
- packages/db/drizzle/1452_agent_revisions_first_message_backfill.sql
- packages/db/src/agents-schema.ts
- packages/db/src/bot-templates-schema.ts
- packages/db/src/schema.ts
- packages/db/test/migration-1380-agents-contract-postgres.test.ts
- packages/db/test/migration-1437-agents-legacy-drop-postgres.test.ts
- packages/db/test/migration-1448-agents-organization-access-postgres.test.ts
- packages/db/test/migration-1449-agents-first-message-postgres.test.ts

### 1d7e00791482f333fafde9c4a62bc08b67de618a (after)

Drop the retired Knowledge sync tables (#6921)

Changed files:

- packages/db/drizzle/1419_detach_knowledge_sync_from_managed_accounts.sql
- packages/db/drizzle/1420_detach_knowledge_sync_from_workspaces.sql
- packages/db/drizzle/1421_detach_knowledge_sync_from_files.sql
- packages/db/drizzle/1422_detach_knowledge_sync_from_connections.sql
- packages/db/drizzle/1423_detach_knowledge_sync_from_documents.sql
- packages/db/drizzle/1424_detach_knowledge_sync_from_scheduled_tasks.sql
- packages/db/drizzle/1425_detach_knowledge_sync_from_scheduled_task_runs.sql
- packages/db/drizzle/1426_detach_knowledge_sync_from_knowledge_sources.sql
- packages/db/drizzle/1427_detach_knowledge_sync_from_knowledge_source_objects.sql
- packages/db/drizzle/1428_detach_knowledge_sync_from_knowledge_document_versions.sql
- packages/db/drizzle/1429_detach_knowledge_sync_from_knowledge_sync_runs.sql
- packages/db/drizzle/1430_drop_knowledge_source_sync_tables.sql
- packages/db/test/migration-1226-merge-duplicate-personal-logins-postgres.test.ts
- packages/db/test/migration-1275-remove-knowledge-source-sync-rows-postgres.test.ts
- packages/db/test/migration-1362-merge-duplicate-personal-logins-across-oauth-clients-postgres.test.ts
- packages/db/test/migration-1430-drop-knowledge-source-sync-tables-postgres.test.ts

### f0cc559ec40c814b4c039824c75207c1400e85c9 (after)

fix(files): list a page of files at page cost and cancel abandoned listings (#7762)

Changed files:

- packages/db/test/file-list-postgres.test.ts

### 92a565089fd912a44474863e932c294048d80430 (after)

fix(worker): resume a turn within seconds after its worker shuts down (#7760)

Changed files:

- packages/db/test/subscription-core-codex-chat-postgres.test.ts

### 37c35ed9d7193adaee2c9276dc588c1c4908c4e2 (after)

fix(mcp): explain refused task-note calls and never echo raw database errors to tools (#7737)

Changed files:

- apps/api/test/task-note-tool-refusals-postgres.test.ts
- packages/db/test/task-notes-postgres.test.ts

### adc240951652a14adf03b3131927aa4219c32c32 (after)

fix(dynamics,sites): never drop a Business Central environment; fail Site publish visibly when bindings can't be read (#7744)

Changed files:

- apps/api/test/published-sites-postgres.test.ts

### 07ecbcc8241ad8df498d026fb2475b0de81a50bf (after)

fix: install block-scalar Skill descriptions and settle chat-route titles (#7743)

Changed files:

- apps/worker/test/session-title-custody-postgres.test.ts

### 6597d387ad0fa8c65bbdc21b85227a35db0ba89e (after)

db: index-backed Console session cost lookups (#7742)

Changed files:

- packages/db/test/console-postgres.test.ts

### 0d72a8bcba094273493d845900acb80b01e9bb90 (after)

db: count session history item JSON shape in linear time (#7735)

Changed files:

- packages/db/test/jsonb-shape-counts-postgres.test.ts

### 1f25da5ac616f50a1c8f35edaa788da0809c7274 (after)

db: measure approval run-state bounds in one linear pass before database work (#7734)

Changed files:

- packages/db/test/json-object-text-measurement-postgres.test.ts
