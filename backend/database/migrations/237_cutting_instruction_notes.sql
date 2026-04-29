-- cutting instruction notes（メモ/TODO）
-- ページ（生産ロット一覧）右上の「メモ」アイコンで使用

CREATE TABLE IF NOT EXISTS `cutting_instruction_notes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `scope` varchar(50) NOT NULL DEFAULT 'cutting_instruction',
  `content` varchar(200) NOT NULL,
  `is_done` tinyint NOT NULL DEFAULT 0 COMMENT '0:未完了 1:完了',
  `created_by` varchar(50) NULL COMMENT '作成者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_scope_is_done_created_at` (`scope`, `is_done`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

