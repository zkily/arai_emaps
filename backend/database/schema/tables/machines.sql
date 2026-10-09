-- TABLE: machines
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `machines` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '设备ID',
  `machine_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '设备CD',
  `machine_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '设备名称',
  `machine_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT '设备种类（例：切断、焊接、检査等）',
  `default_work_hours` decimal(4,2) DEFAULT NULL COMMENT '基準稼働時間（時間）',
  `is_active` tinyint(1) DEFAULT '1' COMMENT '有効フラグ',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT 'active' COMMENT '状态（active/inactive/maintenance）',
  `use_in_cpsat` tinyint(1) NOT NULL DEFAULT '1' COMMENT 'CP-SAT自動排程に参加するか',
  `available_from` time DEFAULT '08:00:00' COMMENT '可用开始时间',
  `available_to` time DEFAULT '17:00:00' COMMENT '可用结束时间',
  `calendar_id` int DEFAULT NULL COMMENT '所属カレンダーID（处理休假）',
  `efficiency` decimal(5,2) DEFAULT '100.00' COMMENT '效率（基准为100）',
  `available_qty` int DEFAULT '0' COMMENT '可用数量',
  `note` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin COMMENT '备注',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `machine_cd` (`machine_cd`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin ROW_FORMAT=DYNAMIC COMMENT='設備マスタ';

SET FOREIGN_KEY_CHECKS = 1;
