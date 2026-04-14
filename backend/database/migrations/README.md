# Migrations Folder Guide

本目录存放 MySQL 迁移脚本（以文件名前缀数字表示历史顺序）。

## 当前现状

- 文件以 `NNN_name.sql` 为主，按编号递增维护。
- `082_production_summarys_add_sw_plan.sql` 已重编号为 `087_production_summarys_add_sw_plan.sql`（消除与 `082_material_stock_sub_current_stock_trigger.sql` 的重复编号）。
- 存在跨阶段补丁：例如 `098_production_schedules_product_cd_if_missing.sql`（幂等补丁脚本）。
- 焊接受入触发器验证说明见 `backend/database/docs/046_welding_receiving_good_qty_trigger_verified.md`（可执行脚本仍在 `046_welding_receiving_good_qty_trigger.sql`）。

## 建议执行原则

- 老环境升级：按历史编号逐个执行（保持现有兼容性）。
- 新环境初始化：优先使用「合并基线迁移」（见 `200_unified_aps_schema.sql`），再执行其后的增量脚本。
- 任何新迁移必须：
  - 使用未占用的新编号（建议从当前最大编号继续）。
  - 优先写成幂等（`IF NOT EXISTS` / 信息架构检查）。
  - 明确注释「适用场景：全新库 / 老库升级 / 回滚补丁」。

## 业务分组（便于查找）

- `002` - `040`: 订单/主数据/ERP/系统基础表
- `041` - `073`: 焊接/电镀/切断/倒角/看板相关
- `074` - `086`: 材料管理与用量追踪（`087` 为 production_summarys 补丁，接在 086 之后）
- `091` - `106`: APS 排产相关（甘特、时段、批次、实绩同步）
- `215` 以降: 部品マスタ・購買・在庫など（`224_part_purchase_tables.sql` に部品在庫作成・廃止テーブル削除・列整合を統合）

## 本次整理产物

- 新增 `200_unified_aps_schema.sql`：
  - 将 APS 相关关键表结构合并为单一基线脚本（新库可一键执行）。
  - 保留触发器与索引定义，减少碎片化脚本串行执行成本。
  - 使用幂等写法，避免重复执行直接失败。

## 后续整理建议（可选）

- 为迁移执行器增加「已执行版本记录表」（例如 `schema_migrations`），避免人工漏跑。
