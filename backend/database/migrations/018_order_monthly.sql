-- 月別受注テーブル（受注管理）
-- order_id は BEFORE INSERT トリガーで自動採番

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TRIGGER IF EXISTS `trg_order_monthly_before_insert`;
DROP TABLE IF EXISTS `order_monthly`;

CREATE TABLE `order_monthly` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '月订单ID',
  `destination_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '納入先CD',
  `destination_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '納入先名',
  `year` int NOT NULL COMMENT '年',
  `month` int NOT NULL COMMENT '月',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '製品CD',
  `product_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '製品名',
  `product_alias` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '製品別名',
  `product_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '量産品' COMMENT '製品種別（量産品/試作品/補給品/その他）',
  `forecast_units` int NULL DEFAULT 0 COMMENT '内示本数',
  `forecast_total_units` int NULL DEFAULT 0 COMMENT '日内示合計',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  `order_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '受注ID',
  `forecast_diff` int NULL DEFAULT 0 COMMENT '内示差異（日内示合計-内示本数 ）',
  PRIMARY KEY (`id`, `order_id`) USING BTREE,
  UNIQUE INDEX `uq_order_monthly_order_id`(`order_id` ASC) USING BTREE,
  INDEX `idx_order_monthly_destination`(`destination_cd` ASC, `year` ASC, `month` ASC) USING BTREE,
  INDEX `idx_order_monthly_product`(`product_cd` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '月別受注テーブル' ROW_FORMAT = DYNAMIC;

DELIMITER ;;
CREATE TRIGGER `trg_order_monthly_before_insert` BEFORE INSERT ON `order_monthly` FOR EACH ROW BEGIN
  DECLARE typeSuffix CHAR(1);

  SET typeSuffix = CASE NEW.product_type
    WHEN '試作品' THEN '1'
    WHEN '別注品' THEN '2'
    WHEN '補給品' THEN '3'
    WHEN 'サンプル品' THEN '4'
    WHEN '代替品' THEN '5'
    WHEN '返却品' THEN '6'
    WHEN 'その他' THEN '7'
    ELSE '0'
  END;

  SET NEW.order_id = CONCAT(
    NEW.year,
    LPAD(NEW.month, 2, '0'),
    NEW.destination_cd,
    NEW.product_cd,
    typeSuffix
  );
END;;
DELIMITER ;

SET FOREIGN_KEY_CHECKS = 1;
