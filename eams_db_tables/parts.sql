SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Table structure for parts
-- ----------------------------
DROP TABLE IF EXISTS `parts`;
CREATE TABLE `parts`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `part_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '部品CD（BOMの子品目CDと同一可）',
  `part_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '部品名',
  `category` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL COMMENT '分类',
  `kind` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT 'N' COMMENT '種別 T/N/F',
  `settlement_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT '有償支給' COMMENT '決済種類',
  `uom` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT '個' COMMENT '単位',
  `unit_price` decimal(18, 2) NOT NULL DEFAULT 0.00 COMMENT '単価（原通貨）',
  `material_unit_price` decimal(18, 2) NOT NULL DEFAULT 0.00 COMMENT '部品材料単価（原通貨）',
  `total_unit_price` decimal(18, 2) GENERATED ALWAYS AS ((`unit_price` + `material_unit_price`)) STORED COMMENT '総単価（単価+部品材料単価）' NULL,
  `currency` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT 'JPY' COMMENT '通貨コード',
  `exchange_rate` decimal(18, 2) NOT NULL DEFAULT 1.00 COMMENT '基準通貨JPY換算：1原通貨当たり円（JPY時は1）',
  `supplier_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL COMMENT '主仕入先CD',
  `status` tinyint NOT NULL DEFAULT 1 COMMENT '1=有効 0=無効',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL COMMENT '備考',
  `created_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `updated_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uq_parts_part_cd`(`part_cd` ASC) USING BTREE,
  INDEX `idx_parts_status`(`status` ASC) USING BTREE,
  INDEX `idx_parts_kind`(`kind` ASC) USING BTREE,
  INDEX `idx_parts_settlement_type`(`settlement_type` ASC) USING BTREE,
  CONSTRAINT `chk_parts_kind` CHECK (`kind` in (_utf8mb4'T',_utf8mb4'N',_utf8mb4'F')),
  CONSTRAINT `chk_parts_settlement_type` CHECK (`settlement_type` in (_utf8mb4'有償支給',_utf8mb4'無償支給',_utf8mb4'自給',_utf8mb4'その他'))
) ENGINE = InnoDB AUTO_INCREMENT = 41 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin COMMENT = '部品マスタ' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of parts
-- ----------------------------
INSERT INTO `parts` VALUES (1, 'K0001', '480L CTR パッチ大', 'プレート', 'T', '有償支給', '個', 25.10, 0.00, DEFAULT, 'JPY', 1.00, '110', 1, NULL, NULL, NULL, '2026-04-09 11:32:55', '2026-04-23 16:18:45');
INSERT INTO `parts` VALUES (2, 'K0002', '480L CTR パッチ小', 'プレート', 'T', '有償支給', '個', 11.50, 0.00, DEFAULT, 'JPY', 1.00, '110', 1, NULL, NULL, NULL, '2026-04-09 11:32:55', '2026-04-23 16:18:46');
INSERT INTO `parts` VALUES (3, 'K0003', '400A RR アーチ', 'アーチ', 'T', '自給', '個', 25.63, 0.00, DEFAULT, 'JPY', 1.00, '109', 1, 'オバラ自給 寸法変更品', NULL, NULL, '2026-04-09 11:32:55', '2026-04-23 16:18:46');
INSERT INTO `parts` VALUES (4, 'K0004', '480L CTR 丸棒', 'その他', 'T', '自給', '本', 150.81, 0.00, DEFAULT, 'JPY', 1.00, '128', 0, NULL, NULL, 'zkily', '2026-04-09 11:32:55', '2026-04-29 14:29:10');
INSERT INTO `parts` VALUES (5, 'K0008', '141A CTR ブラケット', 'ブラケット', 'T', '自給', '個', 44.31, 0.00, DEFAULT, 'JPY', 1.00, '110', 0, NULL, NULL, 'zkily', '2026-04-09 11:32:55', '2026-04-29 14:28:51');
INSERT INTO `parts` VALUES (6, 'K0019', '668A アーチ', 'アーチ', 'T', 'その他', '本', 0.00, 27.71, DEFAULT, 'JPY', 1.00, '139', 1, '12.0x2.00xL 　  H590H', NULL, NULL, '2026-04-09 11:32:55', '2026-04-23 16:18:47');
INSERT INTO `parts` VALUES (7, 'K0028', 'TKR ブラケット', 'ブラケット', 'F', '自給', '個', 24.82, 0.00, DEFAULT, 'JPY', 1.00, '127', 0, '共栄工業自給→名古屋帯鋼の材料を使う', NULL, 'zkily', '2026-04-09 11:32:55', '2026-04-29 14:29:56');
INSERT INTO `parts` VALUES (8, 'K0029', 'TTA ブラケット', 'ブラケット', 'F', '自給', '個', 24.75, 0.00, DEFAULT, 'JPY', 1.00, '127', 0, '共栄工業自給→名古屋帯鋼の材料を使う', NULL, 'zkily', '2026-04-09 11:32:55', '2026-04-29 14:30:00');
INSERT INTO `parts` VALUES (9, 'K0035', 'X61G 3RD A', 'アーチ　大', 'N', '自給', '個', 38.96, 0.00, DEFAULT, 'JPY', 1.00, '109', 0, 'オバラ自給', NULL, 'zkily', '2026-04-09 11:32:55', '2026-04-29 14:30:03');
INSERT INTO `parts` VALUES (10, 'K0036', 'X61G 3RD B', 'アーチ　小', 'N', '自給', '個', 30.91, 0.00, DEFAULT, 'JPY', 1.00, '109', 0, 'オバラ自給', NULL, 'zkily', '2026-04-09 11:32:55', '2026-04-29 14:30:07');
INSERT INTO `parts` VALUES (11, 'K0042', 'FE-7 丸棒', 'その他', 'F', '有償支給', '個', 101.00, 0.00, DEFAULT, 'JPY', 1.00, '126', 0, '丸棒', NULL, 'zkily', '2026-04-09 11:32:55', '2026-04-29 14:29:41');
INSERT INTO `parts` VALUES (12, 'K0052', '720A SD メカ', 'メカ', 'T', '自給', '個', 2.22, 0.00, DEFAULT, 'USD', 156.56, '129', 1, 'ドル建て　＄2.22　　為替レート128', NULL, 'zkily', '2026-04-09 11:32:55', '2026-04-21 14:25:03');
INSERT INTO `parts` VALUES (13, 'K0065', '668A ブラケット', 'ブラケット', 'T', '有償支給', '個', 13.20, 12.00, DEFAULT, 'JPY', 1.00, '110', 1, 'SPCC　1.2*198*C　＠90/KG  110g/個 小山へ', NULL, NULL, '2026-04-09 11:32:55', '2026-04-23 16:18:50');
INSERT INTO `parts` VALUES (14, 'K0066', '141A CTR アーチ', 'アーチ', 'T', 'その他', '本', 0.00, 13.52, DEFAULT, 'JPY', 1.00, '139', 0, '12.0x1.40x5380  STKM15A　切断長152cm　社内生産', NULL, 'zkily', '2026-04-09 11:32:55', '2026-04-29 14:28:47');
INSERT INTO `parts` VALUES (15, 'K0070', '240A SD メカ', 'メカ', 'T', '自給', '個', 2.20, 0.00, DEFAULT, 'USD', 156.56, '129', 1, '470SDと同じメカを使う　為替レート128', NULL, 'zkily', '2026-04-09 11:32:55', '2026-04-21 14:24:29');
INSERT INTO `parts` VALUES (16, 'K0072', 'FE-7 アーチ', 'アーチ', 'F', '有償支給', '個', 6.25, 0.00, DEFAULT, 'JPY', 1.00, '110', 1, 'T2.0*W144*C小山へ　 @81/Kg 　0.02728Kg/本', NULL, NULL, '2026-04-09 11:32:55', '2026-04-23 16:18:51');
INSERT INTO `parts` VALUES (17, 'K0077', '400A SD メカ', 'メカ', 'T', '自給', '個', 2.20, 0.00, DEFAULT, 'USD', 156.56, '129', 1, 'ドル建て　＄2.2　為替レート128', NULL, 'zkily', '2026-04-09 11:32:55', '2026-04-21 14:24:48');
INSERT INTO `parts` VALUES (18, 'K0078', '5A45 FR プレート', 'プレート', 'N', '自給', '個', 17.73, 0.00, DEFAULT, 'JPY', 1.00, '127', 1, NULL, NULL, NULL, '2026-04-09 11:32:55', '2026-04-23 16:18:52');
INSERT INTO `parts` VALUES (19, 'K0079', 'GC7 アーチ', 'アーチ', 'N', '自給', '個', 51.72, 0.00, DEFAULT, 'JPY', 1.00, '109', 1, 'オバラ自給 AF877100', NULL, NULL, '2026-04-09 11:32:55', '2026-04-23 16:18:52');
INSERT INTO `parts` VALUES (20, 'K0080', 'B13B FR BRKT LWR', 'アーチ', 'N', '有償支給', '個', 27.62, 0.00, DEFAULT, 'JPY', 1.00, '112', 1, '　', NULL, 'zkily', '2026-04-09 11:32:55', '2026-04-20 16:58:04');
INSERT INTO `parts` VALUES (21, 'K0081', 'B13B FR BRKT UPR', 'アーチ', 'N', '有償支給', '個', 48.03, 0.00, DEFAULT, 'JPY', 1.00, '112', 1, NULL, NULL, 'zkily', '2026-04-09 11:32:55', '2026-04-20 16:56:27');
INSERT INTO `parts` VALUES (22, 'K0086', '670B 3RD SIDE WIRE', 'アーチ', 'T', '自給', '個', 32.37, 0.00, DEFAULT, 'JPY', 1.00, '109', 1, 'オバラ自給 71943-X7V04', NULL, NULL, '2026-04-09 11:32:55', '2026-04-23 16:18:54');
INSERT INTO `parts` VALUES (23, 'K0087', '670B 3RD CTR パッチA', 'ブラケット', 'T', '有償支給', '個', 23.90, 0.00, DEFAULT, 'JPY', 1.00, '136', 1, NULL, NULL, NULL, '2026-04-09 11:32:55', '2026-04-23 16:18:54');
INSERT INTO `parts` VALUES (24, 'K0088', '670B 3RD CTR パッチB', 'その他', 'T', '有償支給', '個', 23.90, 0.00, DEFAULT, 'JPY', 1.00, '136', 1, NULL, NULL, NULL, '2026-04-09 11:32:55', '2026-04-23 16:18:54');
INSERT INTO `parts` VALUES (25, 'K0089', '400A SD テストピース', 'メカ', 'T', '自給', '個', 0.10, 0.00, DEFAULT, 'USD', 156.56, '129', 1, 'ドル建て　＄0.1　為替レート128', NULL, 'zkily', '2026-04-09 11:32:55', '2026-04-21 14:24:47');
INSERT INTO `parts` VALUES (26, 'K0090', '453A CTR アーチ', 'アーチ', 'T', '自給', '個', 18.44, 0.00, DEFAULT, 'JPY', 1.00, '121', 1, 'ｱｰﾁで出荷 10X2.0X3000 切断長58　長尺材@236/本', NULL, NULL, '2026-04-09 11:32:55', '2026-04-23 16:18:56');
INSERT INTO `parts` VALUES (27, 'K0091', '840B 3RD アーチ', 'アーチ', 'T', '自給', '個', 48.87, 0.00, DEFAULT, 'JPY', 1.00, '109', 1, 'オバラ自給 71943-X1R00-A', NULL, NULL, '2026-04-09 11:32:55', '2026-04-23 16:18:56');
INSERT INTO `parts` VALUES (28, 'K0093', '900B CTR ブラケット', 'ブラケット', 'T', '有償支給', '個', 21.11, 0.00, DEFAULT, 'JPY', 1.00, '112', 1, NULL, NULL, NULL, '2026-04-09 11:32:55', '2026-04-23 16:18:57');
INSERT INTO `parts` VALUES (29, 'K0094', '3VOA プレート', 'プレート', 'F', '有償支給', '個', 12.12, 0.00, DEFAULT, 'JPY', 1.00, '136', 1, NULL, NULL, NULL, '2026-04-09 11:32:55', '2026-04-23 16:18:57');
INSERT INTO `parts` VALUES (30, 'K0095', '300D RR アーチ', 'アーチ', 'T', '自給', '個', 28.17, 0.00, DEFAULT, 'JPY', 1.00, '109', 1, 'オバラ自給 71943-X1001', NULL, NULL, '2026-04-09 11:32:55', '2026-04-23 16:18:58');
INSERT INTO `parts` VALUES (31, 'K0096', 'IW187 材料', 'その他', 'F', '有償支給', '個', 18.00, 19.10, DEFAULT, 'JPY', 1.00, '110', 0, '名古屋帯鋼材料＠105/Kg 　181.67g/本', NULL, 'zkily', '2026-04-09 11:32:55', '2026-04-29 14:29:48');
INSERT INTO `parts` VALUES (32, 'K0097', 'IW187 ﾌｨｰﾙﾄﾞ　大', 'その他', 'F', '自給', '個', 4.66, 0.00, DEFAULT, 'JPY', 1.00, '128', 1, NULL, NULL, 'zkily', '2026-04-09 11:32:55', '2026-04-29 15:15:08');
INSERT INTO `parts` VALUES (33, 'K0098', '840B 2ND CTR　アーチ', 'アーチ', 'T', '有償支給', '個', 12.10, 8.71, DEFAULT, 'JPY', 1.00, '121', 1, '立松　一本33取', NULL, NULL, '2026-04-09 11:32:55', '2026-04-23 16:18:59');
INSERT INTO `parts` VALUES (34, 'K0099', '3VOA オモリ', 'その他', 'F', '自給', '個', 414.48, 0.00, DEFAULT, 'JPY', 1.00, '104', 1, NULL, NULL, NULL, '2026-04-09 11:32:55', '2026-04-23 16:19:11');
INSERT INTO `parts` VALUES (35, 'K0101', 'IW187 ﾃｰﾌﾟ25x5 小', 'その他', 'F', '自給', '個', 2.57, 0.00, DEFAULT, 'JPY', 1.00, '128', 1, '＠2.57x2枚', NULL, NULL, '2026-04-09 11:32:55', '2026-04-23 16:19:04');
INSERT INTO `parts` VALUES (36, 'K0102', '091D CTR アーチ', 'アーチ', 'T', '有償支給', '個', 12.10, 8.71, DEFAULT, 'JPY', 1.00, '121', 1, '立松　一本33取', NULL, 'zkily', '2026-04-09 11:32:55', '2026-04-23 16:19:04');
INSERT INTO `parts` VALUES (37, 'K0103', 'CH2 アーチ', 'アーチ', 'N', '自給', '個', 6.39, 0.00, DEFAULT, 'JPY', 1.00, '109', 1, 'オバラ自給', NULL, NULL, '2026-04-09 11:32:55', '2026-04-23 16:19:05');
INSERT INTO `parts` VALUES (38, 'K0104', '3BV ブラケット', 'ブラケット', 'F', '自給', '個', 25.16, 0.00, DEFAULT, 'JPY', 1.00, '127', 0, '共栄工業自給→名古屋帯鋼の材料を使う', NULL, 'zkily', '2026-04-09 11:32:55', '2026-04-29 14:28:56');
INSERT INTO `parts` VALUES (39, 'K0105', 'P13C SPK  LWR', 'アーチ', 'N', '有償支給', '個', 56.95, 0.00, DEFAULT, 'JPY', 1.00, '112', 1, NULL, 'zkily', 'zkily', '2026-04-09 15:43:05', '2026-04-09 15:47:14');
INSERT INTO `parts` VALUES (40, 'K0106', 'P13C SPK UPR', 'アーチ', 'N', '有償支給', '個', 47.21, 0.00, DEFAULT, 'JPY', 1.00, '112', 1, NULL, 'zkily', 'zkily', '2026-04-09 15:43:40', '2026-04-09 15:47:05');

-- ----------------------------
SET FOREIGN_KEY_CHECKS = 1;
