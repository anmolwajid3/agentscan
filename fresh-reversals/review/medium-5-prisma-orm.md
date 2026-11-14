# prisma/orm (medium)

Old ADR: `docs/architecture docs/adrs/ADR 307 - No recovery resets or drops a database.md`
New ADR: `docs/architecture docs/adrs/ADR 123 - Drift Detection, Recovery & Reconciliation.md`

## Old ADR status line

** Accepted

## New ADR

ADR 123 — Drift Detection, Recovery & Reconciliation

**Status:** Accepted; its reset recoveries and its "auto-reset" development policy are superseded by [ADR 307 — No recovery resets or drops a database](ADR%20307%20-%20No%20recovery%20resets%20or%20drops%20a%20database.md).

## Commits

### 6dd32da533e601d13dcf038e9c26361386952278 (after)

Rename pslScalarTypeDescriptors to scalarTypeDescriptors

Changed files:

- packages/3-targets/6-adapters/postgres/src/core/control-mutation-defaults.ts
- packages/3-targets/6-adapters/postgres/src/exports/control.ts
- packages/3-targets/6-adapters/postgres/test/control-mutation-defaults.test.ts

### 3c219a28fb491d0bb9bb9f5c171e8ce856c8d9f1 (after)

fix: update defineConfig facades and README for framework-level contributions

Changed files:

- packages/3-extensions/postgres/src/config/define-config.ts
- packages/3-extensions/postgres/test/config/define-config.test.ts

### e02ad09ac7e77064fed87cd65e23ff8d395e3f35 (after)

fix(tests): update mock ContractSourceContext for enriched context fields

Changed files:

- packages/3-targets/6-adapters/postgres/test/control-mutation-defaults.test.ts

### 32ed28800547b07a19942cbb9673e4973f139f77 (after)

migrate Postgres adapter to ComponentMetadata fields

Changed files:

- packages/3-targets/6-adapters/postgres/src/core/control-mutation-defaults.ts
- packages/3-targets/6-adapters/postgres/src/exports/control.ts

### 1faa304cfbafe0cf35efc8929c7ce0619cae3e31 (after)

fix: address CodeRabbit review findings

Changed files:

- packages/3-extensions/postgres/src/config/define-config.ts

### 652c0661d773f1d808ed29d0be21481b8902b9bf (after)

fix(cli): address CodeRabbit review findings

Changed files:

- packages/3-extensions/postgres/src/config/define-config.ts
- packages/3-extensions/postgres/test/config/define-config.test.ts

### 7ce579b6f7b89c462e2f2f03d99c11eff5719c42 (after)

fix: resolve biome lint and type errors after rebase

Changed files:

- packages/3-extensions/postgres/src/config/define-config.ts

### 126f247c61f656ee695a82d84e69bd7b41322400 (after)

fix(cli): address code review findings F01-F08, AC8, AC10

Changed files:

- packages/3-extensions/postgres/test/config/define-config.test.ts

### f075e8bd4b5e560e4a006801ada3138889988d7d (after)

feat(postgres): add /config facade with simplified defineConfig

Changed files:

- packages/3-extensions/postgres/package.json
- packages/3-extensions/postgres/src/config/define-config.ts
- packages/3-extensions/postgres/src/exports/config.ts
- packages/3-extensions/postgres/test/config/define-config.test.ts
- packages/3-extensions/postgres/tsdown.config.ts

### 919033166fc41d499d0fc1f06323c41ee54b6567 (after)

test: cover resolver dataTransform + column-option branches

Changed files:

- packages/3-targets/3-targets/postgres/test/migrations/operation-resolver.integration.test.ts

### b2f3a4d0d9a0dedc71e5d49f0f1815286ff75cd4 (after)

feat: descriptor-based planner with migration strategies

Changed files:

- packages/3-targets/3-targets/postgres/src/core/migrations/descriptor-planner.ts
- packages/3-targets/3-targets/postgres/src/core/migrations/planner-strategies.ts
- packages/3-targets/3-targets/postgres/test/migrations/descriptor-planner.scenarios.test.ts

### 1ca042c7d5ae9c01f73d6b3dbafc9a918a7e0146 (after)

feat: core descriptor infrastructure for data migrations

Changed files:

- packages/1-framework/1-core/framework-components/src/control-migration-types.ts
- packages/1-framework/3-tooling/cli/package.json
- packages/1-framework/3-tooling/cli/src/commands/migration-new.ts
- packages/1-framework/3-tooling/cli/src/commands/migration-plan.ts
- packages/1-framework/3-tooling/cli/src/commands/migration-verify.ts
- packages/1-framework/3-tooling/cli/src/control-api/operations/migration-apply.ts
- packages/1-framework/3-tooling/migration/package.json
- packages/1-framework/3-tooling/migration/src/attestation.ts
- packages/1-framework/3-tooling/migration/src/errors.ts
- packages/1-framework/3-tooling/migration/src/exports/io.ts
- packages/1-framework/3-tooling/migration/src/exports/migration-ts.ts
- packages/1-framework/3-tooling/migration/src/exports/types.ts
- packages/1-framework/3-tooling/migration/src/io.ts
- packages/1-framework/3-tooling/migration/src/migration-ts.ts
- packages/1-framework/3-tooling/migration/src/types.ts
- packages/1-framework/3-tooling/migration/tsdown.config.ts
- packages/2-sql/4-lanes/sql-builder/package.json
- packages/2-sql/9-family/src/core/migrations/contract-to-schema-ir.ts
- packages/2-sql/9-family/src/core/migrations/descriptor-schemas.ts
- packages/2-sql/9-family/src/core/migrations/operation-descriptors.ts
- packages/2-sql/9-family/src/core/migrations/types.ts
- packages/2-sql/9-family/src/core/schema-verify/verify-helpers.ts
- packages/2-sql/9-family/test/contract-to-schema-ir.test.ts
- packages/3-targets/3-targets/postgres/package.json
- packages/3-targets/3-targets/postgres/src/core/migrations/operation-descriptors.ts
- packages/3-targets/3-targets/postgres/src/core/migrations/operation-resolver.ts
- packages/3-targets/3-targets/postgres/src/core/migrations/planner-reconciliation.ts
- packages/3-targets/3-targets/postgres/src/core/migrations/runner.ts
- packages/3-targets/3-targets/postgres/src/exports/migration-builders.ts
