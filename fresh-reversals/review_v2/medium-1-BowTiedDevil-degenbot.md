# BowTiedDevil/degenbot (medium)

Old ADR: `docs/adr/ADR-011-auto-healed-alembic-retirement.md`
New ADR: `docs/adr/ADR-010-alembic-retention-and-rust-schema-cutover.md`
New ADR date: 2026-07-03T17:36:28-07:00
Partial: no

## Old ADR status line

implemented — folded into [ADR-052](ADR-052-db-auto-upgrade-alembic-retirement.md).**

## New ADR

ADR-010: Alembic Retention Through 0.6.x and Rust Schema Cutover

**Status: superseded — executed ahead of schedule by [ADR-052](ADR-052-db-auto-upgrade-alembic-retirement.md).** The retention posture this ADR established (Alembic retained through 0.6.x, retirement gated to a 0.7 release) was retired 2026-09-15, and the retirement then executed **while the tree was still on 0.6.x**. Every item on the "Forbidden-until-0.7 kill list" below has already been deleted: `src/degenbot/migrations/`, the `alembic`/`sqlalchemy` dependencies, `DatabaseSessionManager`, the

## Best commit

`bb7bf9061075a28e8708061f6545759e4e16b210` (same)

docs(adr): add ADR-010 Alembic retention + Rust schema cutover

commit title names ADR 10; commit title matches the new ADR: alembic, retention, rust, schema, cutover; changes configuration or schema named in the ADR: alembic, retention, rust, schema, cutover, alembic, cutover

Changed files:

- A docs/adr/ADR-010-alembic-retention-and-rust-schema-cutover.md

## Other candidates

b8dd7121c773 remove(alembic): retire the migration chain, its schemas, and its tests (ergo U7; a2b74619fd1e feat(rust): add RustOwned schema state + alembic→rust cutover; 73bc4bb14236 test(database): prove the Alembic→Rust cutover boundary end-to-end; 1b9623ff82de fix(config): unescape rustdoc backticks, add reasoned clippy expects in cutover ; 67452bf6fe0e fix(rust): bound tick retention to touched boundaries in apply; b6d16085a2ec refactor(aave): cutover analysis to Rust seam, delete Python core.py; ddedd51c0fa8 refactor(python): cutover exchange CLI to the Rust seams; 322180d7a90b perf: bypass unbounded delta retention walks
