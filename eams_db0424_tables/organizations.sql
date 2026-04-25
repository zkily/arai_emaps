SET NAMES utf8mb4;

CREATE TABLE `organizations`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '組織コード（一意）',
  `name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '組織名',
  `type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '種類（company:会社, site:拠点, department:部門, line:ライン）',
  `parent_id` int NULL DEFAULT NULL COMMENT '親組織ID',
  `manager_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '責任者名',
  `location` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '所在地',
  `phone` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '電話番号',
  `email` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'メールアドレス',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '説明',
  `sort_order` int NULL DEFAULT 0 COMMENT '表示順序',
  `is_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '有効フラグ',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `code`(`code` ASC) USING BTREE,
  INDEX `idx_organizations_parent`(`parent_id` ASC) USING BTREE,
  INDEX `idx_organizations_type`(`type` ASC) USING BTREE,
  CONSTRAINT `fk_organizations_parent` FOREIGN KEY (`parent_id`) REFERENCES `organizations` (`id`) ON DELETE SET NULL ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 28 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '組織テーブル（会社、拠点、部門、ライン）' ROW_FORMAT = Dynamic;
INSERT INTO `organizations` VALUES (1, 'COMP001', '日鉄物産荒井オートモーティブ(株)', 'company', NULL, NULL, NULL, NULL, NULL, NULL, 1, 1, '2026-02-05 14:00:55', '2026-02-06 10:38:01');
INSERT INTO `organizations` VALUES (2, 'SITE001', '本社', 'site', 1, NULL, NULL, NULL, NULL, NULL, 1, 1, '2026-02-05 14:00:55', '2026-02-05 14:00:55');
INSERT INTO `organizations` VALUES (19, 'DEPT001', '製造部', 'department', 2, '早川部長', '愛知県愛西市須依町2189', '090-8464-2175', 'hayakawa@arais.co.jp', NULL, 0, 1, '2026-02-05 15:08:04', '2026-02-05 15:09:30');
INSERT INTO `organizations` VALUES (21, 'DEPT002', '生産管理部', 'department', 2, '篠田部長', NULL, '080-4213-5838', 'shinoda@arais.co.jp', NULL, 0, 1, '2026-02-05 16:00:56', '2026-02-05 16:00:56');
INSERT INTO `organizations` VALUES (22, 'SEC001', '加工課', 'section', 19, '渡辺課長', NULL, '080-6929-1946', 'watanabe@arais.co.jp', NULL, 0, 1, '2026-02-05 16:09:23', '2026-02-05 16:09:23');
INSERT INTO `organizations` VALUES (23, 'DEPT003', '生産技術部', 'department', 2, NULL, NULL, NULL, NULL, NULL, 0, 1, '2026-02-06 10:38:48', '2026-02-06 10:39:01');
INSERT INTO `organizations` VALUES (24, 'DEPT004', '品質保証部', 'department', 2, '内山部長', NULL, NULL, NULL, NULL, 0, 1, '2026-02-06 10:39:50', '2026-02-06 10:39:50');
INSERT INTO `organizations` VALUES (25, 'DEPT005', '営業部', 'department', 2, '野村部長', NULL, NULL, NULL, NULL, 0, 1, '2026-02-06 10:40:22', '2026-02-06 10:40:22');
INSERT INTO `organizations` VALUES (26, 'DEPT006', '管理部', 'department', 2, '上田部長', NULL, NULL, NULL, NULL, 0, 1, '2026-02-06 10:40:47', '2026-02-06 10:40:47');
INSERT INTO `organizations` VALUES (27, 'DEPT007', '技術部', 'department', 2, '松下部長', NULL, NULL, NULL, NULL, 0, 1, '2026-04-23 09:11:51', '2026-04-23 09:12:17');
