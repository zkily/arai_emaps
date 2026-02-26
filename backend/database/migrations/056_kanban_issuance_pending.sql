-- カンバン発行：待発行（pending）対応（status に pending を許容、デフォルト変更）
SET NAMES utf8mb4;

ALTER TABLE `kanban_issuance`
  MODIFY COLUMN `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'pending'
  COMMENT '状態（pending=待発行 / issued=発行済 / completed=完了）';
