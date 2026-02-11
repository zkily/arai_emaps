-- 材料检收日志 (material_logs) 与 材料检验主数据 (material_inspection_master)
-- 供 BT-data 受信文件监视写入 Material_*.csv 使用
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- 材料检验主数据（Maruiti 等解析用）
-- ----------------------------
CREATE TABLE IF NOT EXISTS `material_inspection_master` (
  `id` int NOT NULL AUTO_INCREMENT,
  `inspection_cd` varchar(50) NOT NULL COMMENT '检验CD',
  `inspection_standard` varchar(200) DEFAULT NULL COMMENT '检验规格/标准名',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_inspection_cd` (`inspection_cd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='材料检验主数据';

-- ----------------------------
-- 材料日志 (BT-data 受信同步)
-- ----------------------------
DROP TABLE IF EXISTS `material_logs`;
CREATE TABLE `material_logs` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `item` varchar(100) NOT NULL COMMENT '项目/品种标识',
  `log_date` date NOT NULL COMMENT '日志日期',
  `log_time` varchar(20) DEFAULT NULL COMMENT '日志时间',
  `hd_no` varchar(50) DEFAULT NULL COMMENT 'HD No',
  `remarks` varchar(500) DEFAULT NULL,
  `material_cd` varchar(50) DEFAULT NULL,
  `material_name` varchar(200) DEFAULT NULL,
  `process_cd` varchar(50) DEFAULT NULL,
  `manufacture_no` varchar(100) DEFAULT NULL,
  `manufacture_date` date DEFAULT NULL,
  `pieces_per_bundle` int DEFAULT NULL,
  `length` varchar(50) DEFAULT NULL,
  `quantity` int DEFAULT NULL,
  `bundle_quantity` int DEFAULT NULL,
  `magnetic` tinyint DEFAULT 1,
  `appearance` tinyint DEFAULT 1,
  `outer_diameter1` decimal(12,4) DEFAULT NULL,
  `outer_diameter2` decimal(12,4) DEFAULT NULL,
  `supplier` varchar(200) DEFAULT NULL,
  `material_quality` varchar(100) DEFAULT NULL,
  `note` varchar(500) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_item` (`item`),
  KEY `idx_log_date` (`log_date`),
  KEY `idx_manufacture` (`manufacture_no`,`log_date`,`log_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='材料检收日志(BT-data受信)';

SET FOREIGN_KEY_CHECKS = 1;
