-- 成型指示書発行管理：備考に「新聞紙をかける」を表示する対象製品
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `mes_forming_newspaper_products` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `product_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品名',
  `updated_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '更新者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_mes_forming_newspaper_products_name` (`product_name`)
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '成型指示 新聞紙をかける対象製品' ROW_FORMAT = Dynamic;

INSERT IGNORE INTO `mes_forming_newspaper_products` (`product_name`) VALUES
  ('900B FR'),
  ('900B RR'),
  ('900B 対米'),
  ('410D CTR'),
  ('410D FR1'),
  ('410D FR2'),
  ('410D RR');
