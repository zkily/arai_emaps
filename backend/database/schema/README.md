# Schema（按对象拆分的最终结构）

本目录是数据库**最终结构**的快照：每张表、每个触发器 / 存储过程 / 事件、每张表的初始数据各一个文件，
便于按表查阅和代码评审。与 `../migrations/`（按时间顺序的增量历史）互为补充。

## 目录

| 目录 | 内容 |
| --- | --- |
| `tables/` | `CREATE TABLE IF NOT EXISTS`（含索引、外键；文件内关闭 `FOREIGN_KEY_CHECKS`，执行顺序无关） |
| `views/` | `CREATE OR REPLACE VIEW`（当前无有效视图） |
| `functions/` `procedures/` | `DROP ... IF EXISTS` + `CREATE`（`DELIMITER $$`） |
| `triggers/` | 同上，文件头注释标明所属表 |
| `events/` | 同上 |
| `seed/` | 初始数据，`INSERT IGNORE`（`users` 的开发管理员由 `../init/01_init.sql` 投入，不在此处） |

## 用法

新库（空库）一键建库：

```bash
py scripts/bootstrap_full_database.py --from-schema
py scripts/bootstrap_full_database.py --from-schema --db-name eams_check --drop-database   # 临时校验库
```

执行顺序：`tables → views → functions → procedures → triggers → events → seed → init/01_init.sql`。

**已上线数据库不要整目录执行**：表文件是 `IF NOT EXISTS`，不会给已有表补列；已有库仍按 `../migrations/` 的增量文件升级。

## 维护方式（自动同步）

结构变更照旧在 `../migrations/` 追加增量 SQL（已上线库靠它升级），本目录自动跟随：

```bash
py scripts/sync_schema_from_migrations.py            # 同步新增迁移
py scripts/sync_schema_from_migrations.py --check    # 只检查（不连库），有未同步迁移时退出码 1
py scripts/sync_schema_from_migrations.py --force    # 没有新迁移也重建导出（统一格式）
py scripts/sync_schema_from_migrations.py --mark-only  # 只登记为已同步，不改 schema/
```

- `synced_migrations.txt` 记录已反映到本目录的迁移；脚本对未登记的迁移：用本目录建临时库
  `eams_schema_sync` → 执行新迁移 → 重新导出 → 登记 → 删除临时库。不会改动 `DB_NAME` 指向的库。
- 结果：已有表加列/改列 → 该表的 `tables/<表名>.sql` 被更新；新表 → 新文件；新触发器、过程、初始数据同理。
- **git pre-commit hook**（`.githooks/pre-commit`）：提交中包含未同步的迁移时自动执行同步，并把 `schema/`
  的变更加入本次提交。每个克隆需执行一次 `git config core.hooksPath .githooks` 启用；
  需要本机有 MySQL 客户端与 `pymysql`。跳过：`git commit --no-verify`。
- 已登记的迁移若再被修改，不会被重新同步：请新增一个迁移来修正。

## 生成来源（初版）

`02_baseline_full_schema.sql` 在空库上无法完整执行（存在只适用于旧库的改名语句等，共 28 处报错），
因此初版按以下方式生成，并用 `--from-schema` 重建后与来源库逐表、逐列、逐索引、逐外键比对一致：

- 以 `01_init.sql` + 全部 migrations（`mysql --force`）构建的临时库为基础；
- 从开发库 `eams_db` 补入迁移中从未定义、但代码在用的对象：
  `production_summarys`、`production_plan_excel`、`inventory_logs` 表，
  `lot_forecast_attribution_archive.archived_at`、`material_logs.updated_at`、`material_inspection_master.updated_at`、
  `lot_forecast_attribution.idx_lfa_is_current`，
  以及 `sp_rebuild_and_recalc_production_plan_excel`、`sp_rebuild_production_plan_excel_all`、`sp_recalc_junban_full`、
  `evt_production_plan_excel_nightly_rebuild`；
- 排除：残留的临时过程 `_tmp_backfill_welding_order_no`，以及已失效（引用不存在的列）且代码未使用的视图
  `v_customer_order_stats`、`v_order_daily_summary`、`v_order_monthly_summary`。
