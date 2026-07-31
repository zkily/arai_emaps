-- 出荷パレット数：日付×納入先セルの手動修正（ダブルクリック編集）
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `shipping_pallet_count_overrides` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `shipping_date` date NOT NULL COMMENT '積込日',
  `destination_cd` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '納入先CD',
  `qty` int NOT NULL DEFAULT 0 COMMENT '手動パレット数（表示値）',
  `updated_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '更新者',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_spco_date_dest` (`shipping_date`, `destination_cd`),
  KEY `idx_spco_date` (`shipping_date`)
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '出荷パレット数 セル手動修正' ROW_FORMAT = Dynamic;
