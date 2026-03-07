-- ピッキング用リスト（shipping_items の当日以降を同期）
CREATE TABLE IF NOT EXISTS `picking_list` (
  `id` int NOT NULL AUTO_INCREMENT,
  `shipping_no_p` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `shipping_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `product_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `confirmed_boxes` int NOT NULL DEFAULT 0,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uk_shipping_product` (`shipping_no_p`, `product_cd`) USING BTREE,
  KEY `idx_shipping_no` (`shipping_no`),
  KEY `idx_product_cd` (`product_cd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin ROW_FORMAT=DYNAMIC;
