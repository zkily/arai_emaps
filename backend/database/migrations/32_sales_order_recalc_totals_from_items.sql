-- sales_order 合計金額を明細 amount から再計算（ヘッダー 0 の修復）
SET NAMES utf8mb4;

UPDATE sales_order so
INNER JOIN (
  SELECT order_id, COALESCE(SUM(amount), 0) AS line_sub
  FROM sales_order_item
  GROUP BY order_id
) agg ON agg.order_id = so.id
SET
  so.subtotal = agg.line_sub,
  so.tax_amount = agg.line_sub * COALESCE(so.tax_rate, 10) / 100,
  so.total_amount = agg.line_sub * (1 + COALESCE(so.tax_rate, 10) / 100)
WHERE COALESCE(so.total_amount, 0) = 0
  AND agg.line_sub > 0;
