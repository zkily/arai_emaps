-- 工程別標準原価増分テーブル
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `product_process_unit_prices` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '製品CD',
  `route_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT 'ルートCD',
  `step_no` int NOT NULL COMMENT 'ステップ番号',
  `line_seq` int NOT NULL DEFAULT 1 COMMENT '行連番 (同ステップ内)',
  `line_type` varchar(30) NOT NULL DEFAULT 'process' COMMENT '種別 (material/process/other)',
  `description` varchar(200) DEFAULT NULL COMMENT '内容説明',
  `increment_unit_price` decimal(18,6) NOT NULL DEFAULT 0.000000 COMMENT '増分単価',
  `currency` varchar(10) NOT NULL DEFAULT 'JPY' COMMENT '通貨',
  `effective_from` date DEFAULT NULL COMMENT '有効開始日',
  `effective_to` date DEFAULT NULL COMMENT '有効終了日 (NULL=無期限)',
  `status` varchar(20) NOT NULL DEFAULT 'active' COMMENT '状態',
  `bom_line_id` int DEFAULT NULL COMMENT '参照BOM行ID (追跡用)',
  `remarks` text COMMENT '備考',
  `created_by` varchar(100) DEFAULT NULL COMMENT '作成者',
  `updated_by` varchar(100) DEFAULT NULL COMMENT '更新者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_price_product_route` (`product_cd`, `route_cd`),
  KEY `idx_price_effective` (`product_cd`, `route_cd`, `effective_from`, `effective_to`),
  KEY `idx_price_step` (`product_cd`, `route_cd`, `step_no`, `line_seq`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='工程別標準原価増分';
