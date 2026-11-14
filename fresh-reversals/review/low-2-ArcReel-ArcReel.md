# ArcReel/ArcReel (low)

Old ADR: `docs/adr/0009-declarative-model-pricing.md`
New ADR: `docs/adr/0099-model-catalog-shared-entries-per-model.md`

## Old ADR status line

superseded by ADR-0099

## New ADR

模型目录按模型建共用条目，渠道价差只用倍率，出厂快照、官方同步与用户修改三层合成

> 本 ADR 原先规定内置供应商的默认模型在全局与项目都没有默认模型设置时用于自动挑选。这一条已修订：官方数据里的默认模型只作推荐，运行时解析不读它，见「规则」中推荐模型与升级固化两条。

## Commits

### 2964330aad829d2d9f73dd147e9751a00914dc4a (before)

fix(data-root): 数据库、用户记忆与运行时状态改用无前缀位置

Changed files:

- scripts/migrate_sqlite_to_orm.py
- tests/integration/lib/db/test_db_engine_legacy_sqlite.py

### e00e28b87ed5d0682de614d6988eee193d614682 (before)

refactor: 按映射表把核心库与应用服务层搬入领域包

Changed files:

- scripts/migrate_sqlite_to_orm.py

### 2761e6913211d77bbc61800e411437977e33a95a (before)

chore(tests): 定向测试选择含不存在路径时在收集前报错 (#2424)

Changed files:

- tests/integration/test_pytest_selection_guard.py

### 8881cf5babe7f9c9c688ffbcb055bb0435c364d7 (before)

ci(ruff): B/C4/PIE/RET/PERF/RUF 六族进闸门，异常链与可变类属性等存量清零

Changed files:

- scripts/migrate_sqlite_to_orm.py

### 735ed2c3acc78c6a3957ef6b03c18743bfa461b6 (before)

refactor(tasks): 删除任务事件表的只写不读死代码链 (#1448)

Changed files:

- scripts/migrate_sqlite_to_orm.py

### c0425418c0df1a4d88c703994fea099c55d1f97b (before)

feat: env-driven runtime configuration and graceful fallbacks (#515)

Changed files:

- scripts/migrate_sqlite_to_orm.py
