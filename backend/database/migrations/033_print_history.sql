-- 印刷履歴（出荷報告・カレンダー等）
CREATE TABLE IF NOT EXISTS `print_history` (
  `id` int NOT NULL AUTO_INCREMENT,
  `report_type` varchar(50) NOT NULL,
  `report_title` varchar(200) DEFAULT NULL,
  `filters` json DEFAULT NULL,
  `record_count` int DEFAULT 0,
  `status` varchar(20) DEFAULT NULL,
  `error_message` text,
  `user_name` varchar(100) DEFAULT NULL,
  `printed_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_report_type` (`report_type`),
  KEY `idx_printed_at` (`printed_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;
