-- 出荷印刷記録テーブル
CREATE TABLE IF NOT EXISTS `shipping_records` (
  `id` int NOT NULL AUTO_INCREMENT,
  `shipping_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '出荷番号（例：20250611-D001-007）',
  `status` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `shipping_no`(`shipping_no` ASC) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin ROW_FORMAT=DYNAMIC;
