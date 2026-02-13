-- 設備運行時間設定（成型指示画面の時間帯 17-19, 19-21, 6-8 用）

CREATE TABLE IF NOT EXISTS `machine_work_time_config` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `machine_cd` varchar(50) NOT NULL COMMENT '設備コード',
  `machine_name` varchar(100) DEFAULT NULL COMMENT '設備名',
  `time_slot_17_19` tinyint NOT NULL DEFAULT 0 COMMENT '17-19時 稼働(1)/非稼働(0)',
  `time_slot_19_21` tinyint NOT NULL DEFAULT 0 COMMENT '19-21時 稼働(1)/非稼働(0)',
  `time_slot_6_8` tinyint NOT NULL DEFAULT 0 COMMENT '6-8時 稼働(1)/非稼働(0)',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_machine_cd` (`machine_cd`),
  KEY `idx_machine_name` (`machine_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='設備運行時間設定';
