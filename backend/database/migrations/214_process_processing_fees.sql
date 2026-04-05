-- 工程加工費マスタ（工程＋加工方法ごとに加工費）
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `process_processing_fees` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `process_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '工程CD（processes.process_cd）',
  `method_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '加工方法コード',
  `method_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT '加工方法名称',
  `unit_price` decimal(18,4) NOT NULL DEFAULT 0.0000 COMMENT '加工費単価',
  `currency` varchar(10) NOT NULL DEFAULT 'JPY' COMMENT '通貨',
  `charge_uom` varchar(20) NOT NULL DEFAULT '式' COMMENT '課金単位（式/個/H 等）',
  `effective_from` date DEFAULT NULL COMMENT '有効開始',
  `effective_to` date DEFAULT NULL COMMENT '有効終了',
  `status` varchar(20) NOT NULL DEFAULT 'active' COMMENT '状態 active/historical',
  `remarks` text COMMENT '備考',
  `created_by` varchar(100) DEFAULT NULL,
  `updated_by` varchar(100) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_ppf_process` (`process_cd`),
  KEY `idx_ppf_process_method` (`process_cd`, `method_cd`),
  KEY `idx_ppf_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='工程加工費マスタ';
