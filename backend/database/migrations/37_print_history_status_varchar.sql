-- print_history.status: ENUM 環境で「失敗」等が拒否される場合に VARCHAR へ統一
ALTER TABLE `print_history`
  MODIFY COLUMN `status` VARCHAR(20) NULL DEFAULT NULL;
