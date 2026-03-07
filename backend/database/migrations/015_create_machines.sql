SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for machines (設備マスタ)
-- ----------------------------
DROP TABLE IF EXISTS `machines`;
CREATE TABLE `machines` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '设备ID',
  `machine_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '设备CD',
  `machine_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '设备名称',
  `machine_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL COMMENT '设备种类（例：切断、焊接、检査等）',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT 'active' COMMENT '状态（active/inactive/maintenance）',
  `available_from` time NULL DEFAULT '08:00:00' COMMENT '可用开始时间',
  `available_to` time NULL DEFAULT '17:00:00' COMMENT '可用结束时间',
  `calendar_id` int NULL DEFAULT NULL COMMENT '所属カレンダーID（处理休假）',
  `efficiency` decimal(5, 2) NULL DEFAULT 100.00 COMMENT '效率（基准为100）',
  `note` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL COMMENT '备注',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `machine_cd`(`machine_cd` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin COMMENT = '設備マスタ' ROW_FORMAT = DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;
