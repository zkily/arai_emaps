-- 出荷明細テーブル（出荷構成表）
CREATE TABLE IF NOT EXISTS `shipping_items` (
  `id` int NOT NULL AUTO_INCREMENT,
  `shipping_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '出荷番号',
  `shipping_date` date NOT NULL COMMENT '出荷日',
  `delivery_date` date NULL DEFAULT NULL COMMENT '納入日',
  `destination_cd` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '納入先コード',
  `destination_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL COMMENT '納入先名',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '製品コード',
  `product_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL COMMENT '製品名',
  `product_alias` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL COMMENT '製品別名/納入日など追加情報',
  `box_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL COMMENT '箱種',
  `confirmed_boxes` int NOT NULL DEFAULT 0 COMMENT '箱数',
  `confirmed_units` int NOT NULL DEFAULT 0 COMMENT '出荷数量',
  `unit` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT '本' COMMENT '単位',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT '未発行' COMMENT '状態（未発行/発行済/出荷済/キャンセル）',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL COMMENT '備考',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '登録日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  `shipping_no_p` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `product_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  PRIMARY KEY (`id`, `shipping_no_p`) USING BTREE,
  UNIQUE INDEX `uq_shipping_no_p`(`shipping_no_p` ASC) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='出荷管理' ROW_FORMAT=DYNAMIC;
