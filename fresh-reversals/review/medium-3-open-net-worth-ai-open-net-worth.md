# open-net-worth-ai/open-net-worth (medium)

Old ADR: `docs/adr/2026-08-21-activated-skills-stay-active-until-removed.md`
New ADR: `docs/adr/2026-08-22-skills-are-session-context-not-active-modes.md`

## Old ADR status line

Superseded

## New ADR

Skills are session context, not active modes



## Commits

### c3043fdc45ae2ca18fe9d964d9a1e4122f8382eb (same)

Open Net Worth — initial commit

Changed files:

- .agents/skills/skill-creator/references/schemas.md
- .claude/skills/skill-creator/references/schemas.md
- Dockerfile
- backend/ai/tools/_txn_schema.py
- backend/ai/tools/schema_from_model.py
- backend/api/setup.py
- backend/db/alembic/versions/202608071952_money_core_schema.py
- backend/db/alembic/versions/202608081119_planning_schema.py
- backend/db/alembic/versions/202608082245_investments_schema.py
- backend/db/alembic/versions/202608090721_logs_schema.py
- backend/db/alembic/versions/202608090943_configs_schema.py
- backend/db/alembic/versions/202608092049_misc_and_checkpoints_schema.py
- backend/db/alembic/versions/202608110400_profile_schema.py
- backend/db/alembic/versions/202608110402_wave5b_logs_schema.py
- backend/db/alembic/versions/202608110404_wave5c_schema.py
- backend/db/alembic/versions/202608110406_wave5d1_schema.py
- backend/db/alembic/versions/202608110408_wave5d2a_schema.py
- backend/db/alembic/versions/202608110410_wave5d2b_schema.py
- backend/db/alembic/versions/202608110412_wave5e_schema.py
- backend/db/alembic/versions/202608110414_wave5f_schema.py
- backend/db/alembic/versions/202608110416_wave5f_cache_state_schema.py
- backend/db/migrate.py
- backend/scripts/_migration_io.py
- backend/scripts/purge_migration_trail.py
- backend/services/setup.py
- desktop/package.json
- docker-compose.yml
- docs-site/package.json
- docs/adr/2026-07-13-account-id-opaque-backfill-migration.md
- docs/adr/2026-07-19-derive-tool-schemas-from-models.md
- docs/adr/2026-08-01-migrations-write-the-new-fact-before-deleting-the-old.md
- docs/adr/2026-08-07-fail-closed-alembic-migrations-with-verified-backup.md
- docs/adr/2026-08-16-phase6-migration-diagnostics-and-turn-routing-logs.md
- docs/adr/2026-08-22-external-mcp-confirm-migrates-onto-generic-resolve.md
- docs/adr/2026-08-24-the-instance-lock-precedes-the-migration.md
- docs/adr/2026-09-03-live-instance-migrations-require-an-opt-in.md
- docs/adr/2026-10-03-external-mcp-discovery-gate-validates-against-discovered-schema.md
- frontend/package.json
- frontend/src/components/tabs/automations/AutomationTriggerFields.migratedRule.test.tsx
- package.json
