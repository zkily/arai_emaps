# 触发器验证：good_qty 变更 → 订单/在庫/履歴更新

## 假定
- 该触发器为 **AFTER UPDATE** 挂载在 **`outsourcing_welding_receivings`** 上。

---

## 正确之处

1. **good_qty_diff 计算**：`COALESCE(NEW.good_qty,0) - COALESCE(OLD.good_qty,0)` 正确处理 NULL。
2. **订单 received_qty 更新**：`received_qty = GREATEST(0, received_qty + good_qty_diff)` 与「良品变化量」一致。
3. **订单 status 逻辑**：用「新入庫数」与 `quantity` 比较，决定 `completed` / `partial`，方向正确。
4. **outsourcing_welding_orders** 存在 `received_qty`、`status`、`quantity`，列名与用法匹配。
5. **outsourcing_welding_stock** 存在 `product_cd, product_name, supplier_cd, welding_type, received_qty, last_receive_date`，唯一键为 `(product_cd, supplier_cd, welding_type)`。
6. **outsourcing_stock_transactions** 存在 `transaction_date, transaction_type, process_type, product_cd, product_name, supplier_cd, related_no, quantity, operator`，与 INSERT 列一致。

---

## 问题与修正

### 1. 订单 status：入庫数归 0 时仍可能为 completed（业务逻辑）

当「新入庫数」= 0 时使用 `ELSE status`，若原状态为 `completed`，会一直保持 `completed`。

**建议**：入庫数归 0 时改回「未完了」状态，例如：

```sql
status = CASE
    WHEN received_qty + good_qty_diff >= quantity THEN 'completed'
    WHEN received_qty + good_qty_diff > 0 THEN 'partial'
    ELSE 'ordered'   -- 原 ELSE status
END
```

若业务要求「归 0 也不改状态」则保留 `ELSE status`。

---

### 2. outsourcing_welding_stock 与 NULL welding_type（重要）

唯一键为 `(product_cd, supplier_cd, welding_type)`。在 MySQL 中，**唯一键中 NULL 与 NULL 不视为相同**，因此：

- **INSERT ... ON DUPLICATE KEY UPDATE**：当 `welding_type` 为 NULL 时，可能不会命中已有行，会插入多行「同一 product_cd + supplier_cd + NULL」。
- **减少时的 UPDATE**：`WHERE ... AND (welding_type = NEW.welding_type OR (welding_type IS NULL AND NEW.welding_type IS NULL))` 可能匹配多行，导致多行都被减去同一 `good_qty_diff`，在庫被重复扣减。

**建议**：

- **增加时**：不用 ON DUPLICATE KEY，改为「先 UPDATE，若未更新到行再 INSERT」；或业务上保证同一 (product_cd, supplier_cd) 下 NULL 只有一行。
- **减少时**：只更新一行，例如加 `ORDER BY id LIMIT 1`（或按业务指定「唯一」的一行）。

---

### 3. supplier_cd 长度不一致

- `outsourcing_stock_transactions.supplier_cd` = **varchar(10)**
- `outsourcing_welding_receivings.supplier_cd` = **varchar(20)**

若受入表中有超过 10 位的外注先代码，写入履歴表会被截断或报错（取决于 sql_mode）。

**建议**：统一为 varchar(20)，或保证业务上外注先代码不超过 10 位。

---

### 4. 冗余条件

「入庫履歴を記録」的 `IF good_qty_diff != 0 THEN` 与外层已相同，可删除该内层 IF，直接 INSERT。

---

## 修正后的触发器（建议版）

见同目录下 `046_welding_receiving_good_qty_trigger.sql`（如存在），或以下逻辑要点：

- 使用 `CASE` 在「新入庫数 <= 0」时设 `status = 'ordered'`（按需保留或改回 `ELSE status`）。
- 在庫更新：增加时用「先 UPDATE，未命中再 INSERT」避免 NULL welding_type 下重复行；减少时 UPDATE 加 `ORDER BY id LIMIT 1`。
- 去掉入庫履歴前的重复 `IF good_qty_diff != 0`。
- 若迁移允许，将 `outsourcing_stock_transactions.supplier_cd` 改为 varchar(20)。
