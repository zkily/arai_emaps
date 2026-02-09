-- ================================================================
-- 月別受注テーブル 新スキーマ適用
-- order_monthly: 納入先・製品・内示中心の設計、order_id トリガー生成
-- Version: 016
-- ================================================================

SET FOREIGN_KEY_CHECKS = 0;

-- 日別受注の外部キー依存のため先に削除（必要に応じてデータ退避後に実行）
DROP TABLE IF EXISTS `order_daily`;

DROP TRIGGER IF EXISTS `trg_order_monthly_before_insert`;
DROP TABLE IF EXISTS `order_monthly`;

-- ================================================================
-- 月別受注テーブル (新スキーマ)
-- ================================================================
CREATE TABLE `order_monthly` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '月別受注ID',
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
  `order_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '' COMMENT '受注ID（トリガーで上書き）',
  `forecast_diff` int NULL DEFAULT 0 COMMENT '内示差異（日内示合計-内示本数 ）',
  PRIMARY KEY (`id`, `order_id`) USING BTREE,
  UNIQUE INDEX `uq_order_monthly_order_id`(`order_id` ASC) USING BTREE,
  INDEX `idx_order_monthly_destination`(`destination_cd` ASC, `year` ASC, `month` ASC) USING BTREE,
  INDEX `idx_order_monthly_product`(`product_cd` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '月別受注テーブル' ROW_FORMAT = DYNAMIC;

-- ================================================================
-- トリガー: INSERT 時に order_id を自動生成
-- ================================================================
DROP TRIGGER IF EXISTS `trg_order_monthly_before_insert`;
delimiter ;;
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
delimiter ;

-- ================================================================
-- 日別受注テーブル 再作成（order_monthly.id への FK）
-- ================================================================
CREATE TABLE IF NOT EXISTS `order_daily` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT 'ID',
  `monthly_order_id` INT DEFAULT NULL COMMENT '月別受注ID',
  `year` INT NOT NULL COMMENT '年',
  `month` INT NOT NULL COMMENT '月',
  `day` INT NOT NULL COMMENT '日',
  `order_date` DATE NOT NULL COMMENT '受注日',
  `customer_code` VARCHAR(50) NOT NULL COMMENT '顧客コード',
  `customer_name` VARCHAR(200) DEFAULT NULL COMMENT '顧客名',
  `product_code` VARCHAR(100) NOT NULL COMMENT '品番',
  `product_name` VARCHAR(300) DEFAULT NULL COMMENT '品名',
  `destination_code` VARCHAR(50) DEFAULT NULL COMMENT '納入先コード',
  `destination_name` VARCHAR(200) DEFAULT NULL COMMENT '納入先名',
  `confirmed_boxes` INT DEFAULT 0 COMMENT '確定箱数',
  `confirmed_units` INT DEFAULT 0 COMMENT '確定本数',
  `forecast_units` INT DEFAULT 0 COMMENT '内示本数',
  `shipped_boxes` INT DEFAULT 0 COMMENT '出荷箱数',
  `shipped_units` INT DEFAULT 0 COMMENT '出荷本数',
  `shipping_status` VARCHAR(20) DEFAULT '未出荷' COMMENT '出荷状態（出荷済/未出荷）',
  `confirmation_status` VARCHAR(20) DEFAULT '未確認' COMMENT '確認状態（確認済/未確認）',
  `is_shipped` BOOLEAN DEFAULT FALSE COMMENT '出荷済フラグ',
  `is_confirmed` BOOLEAN DEFAULT FALSE COMMENT '確認済フラグ',
  `unit_price` DECIMAL(10, 2) DEFAULT NULL COMMENT '単価',
  `total_amount` DECIMAL(15, 2) DEFAULT NULL COMMENT '合計金額',
  `remarks` TEXT DEFAULT NULL COMMENT '備考',
  `is_active` BOOLEAN DEFAULT TRUE COMMENT '有効フラグ',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  `created_by` VARCHAR(100) DEFAULT NULL COMMENT '作成者',
  `updated_by` VARCHAR(100) DEFAULT NULL COMMENT '更新者',
  INDEX `idx_monthly_order_id` (`monthly_order_id`),
  INDEX `idx_year_month_day` (`year`, `month`, `day`),
  INDEX `idx_order_date` (`order_date`),
  INDEX `idx_customer_code` (`customer_code`),
  INDEX `idx_product_code` (`product_code`),
  INDEX `idx_destination_code` (`destination_code`),
  INDEX `idx_shipping_status` (`shipping_status`),
  INDEX `idx_confirmation_status` (`confirmation_status`),
  INDEX `idx_is_shipped` (`is_shipped`),
  INDEX `idx_is_confirmed` (`is_confirmed`),
  INDEX `idx_is_active` (`is_active`),
  INDEX `idx_created_at` (`created_at`),
  FOREIGN KEY (`monthly_order_id`) REFERENCES `order_monthly` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='日別受注管理';

SET FOREIGN_KEY_CHECKS = 1;
