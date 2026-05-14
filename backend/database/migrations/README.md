# Migrations（数据库迁移）

## 当前结构（编号约定）

- **`../init/01_init.sql`**：最先执行，仅创建 `users` 表及可选开发用管理员（`004` 等迁移依赖 `users` 已存在）。
- **`02_baseline_full_schema.sql`**：全量基线（由原 `002`～`260` 共 159 个脚本按序合并），供**新库**一次性执行（含 `DELIMITER` 的触发器/存储过程，需用 `mysql` 客户端执行）。
- **增量迁移**：今后新 DDL/DML 请使用 **`03_`、`04_`…** 递增前缀的新 `.sql` 文件（勿随意改写已发布的 `02_` 大文件，除非团队约定整库重建并协调所有环境）。

## 新库一条命令

在仓库根目录配置 `backend/.env` 的 `DB_*` 后执行：

```bash
py scripts/bootstrap_full_database.py
```

脚本会执行 `01_init.sql`，再按数字顺序执行 `migrations` 下全部 `NNN_*.sql`（即 `02_` 基线，以及将来追加的 `03_` 等）。

可选：`--dry-run`、`--drop-database`（会删库）。详见仓库根目录 `README.md`。

## 已上线数据库

- **不要**对已有库再整文件执行 `02_baseline_full_schema.sql`（会与触发器/过程等重复定义）。
- 继续只执行**新增**的增量文件（如 `03_xxx.sql`），或按备份/运维流程处理。

## 设计备忘：046 / 047 溶接受入触发器

以下是对 `outsourcing_welding_receivings` 上 **good_qty / 受入** 相关触发器校验时的结论摘要（逻辑已并入 `02_baseline_full_schema.sql` 对应段落）。

- **订单 status**：用「受入数合计与注文数」判定受入完；入庫数归 0 时是否回到 `ordered` 需与业务确认。
- **outsourcing_welding_stock 与 NULL welding_type**：唯一键下 NULL 易导致重复行或重复扣减；实现上宜用「先 UPDATE，未命中再 INSERT」、减少时 `LIMIT 1` 等策略。
- **supplier_cd 长度**：若 `outsourcing_stock_transactions.supplier_cd` 与受入表长度不一致，需统一或限制业务代码长度。

## 基线维护说明

- 日常变更请通过 **`03_` 及更大编号** 的增量 SQL 提交。
- 若必须从历史 git 中恢复旧版分散迁移再合并，可在本地用脚本或手工拼接生成新的 `02_` 基线文件（仓库内不附带合并脚本）。

## 后续可选改进

- 增加 `schema_migrations` 表记录已执行版本，避免人工漏跑。
