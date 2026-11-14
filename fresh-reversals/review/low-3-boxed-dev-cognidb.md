# boxed-dev/cognidb (low)

Old ADR: `docs/adr/0010-major-release-scope-freeze.md`
New ADR: `docs/adr/0004-multi-statement-write-opt-in-only.md`

## Old ADR status line

** accepted for 3.x; item 5 superseded by 4.0.0 (see `CHANGELOG.md`)

## New ADR

Multi-statement: banned in read mode; second opt-in in write mode

**Status:** accepted

## Commits

### 754f9393e2c7d6745dfc261fb2ffa4bbaadaf508 (after)

feat: real intent-mode generation, dialect wiring, lazy drivers

Changed files:

- cognidb/drivers/mysql_driver.py
- cognidb/drivers/sqlite_driver.py
- tests/integration/test_mysql_integration.py

### 2141f96ab16929754c6bffcfa6f5d902197830e5 (after)

feat!: v4.0.0 security foundations — AST guard + parameterized-by-default

Changed files:

- cognidb/drivers/mysql_driver.py
- cognidb/drivers/sqlite_driver.py
- examples/sqlite_offline_demo.py
- tests/integration/test_sqlite_e2e.py

### 8d3005fce56a4a94505ad4d2473a027d22a8c4be (after)

release: CogniDB 3.0.1 go-live readiness

Changed files:

- examples/sqlite_offline_demo.py
- tests/integration/test_sqlite_e2e.py
- tests/unit/test_intent_sqlite_e2e.py

### 46eb8d7277eee3ca5b8da441b3d95bff774e4bae (before)

feat: deep SecureQueryPipeline + SQLite adapter (v2.0.1)

Changed files:

- cognidb/drivers/sqlite_driver.py
- tests/unit/test_sqlite_driver.py
