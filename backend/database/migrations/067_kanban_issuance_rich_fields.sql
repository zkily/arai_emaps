-- カンバン発行：切断現品票に必要な全フィールドを kanban_issuance に追加
SET NAMES utf8mb4;

ALTER TABLE `kanban_issuance`
  ADD COLUMN `product_cd`              varchar(50)  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '製品CD'        AFTER `status`,
  ADD COLUMN `product_name`            varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '製品名'        AFTER `product_cd`,
  ADD COLUMN `production_line`         varchar(50)  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'ライン'         AFTER `product_name`,
  ADD COLUMN `cutting_machine`         varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '切断機'         AFTER `production_line`,
  ADD COLUMN `material_name`           varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '原材料'         AFTER `cutting_machine`,
  ADD COLUMN `standard_specification`  varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '規格'           AFTER `material_name`,
  ADD COLUMN `management_code`         varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '管理コード'     AFTER `standard_specification`,
  ADD COLUMN `start_date`              date         NULL DEFAULT NULL COMMENT '成型期間（開始）'                                                AFTER `management_code`,
  ADD COLUMN `end_date`                date         NULL DEFAULT NULL COMMENT '成型期間（終了）'                                                AFTER `start_date`,
  ADD COLUMN `planned_quantity`        int          NULL DEFAULT NULL COMMENT '計画数（成型計画数）'                                             AFTER `end_date`,
  ADD COLUMN `production_lot_size`     int          NULL DEFAULT NULL COMMENT '生産ロット数（成型ロット）'                                       AFTER `planned_quantity`,
  ADD COLUMN `actual_production_quantity` int       NULL DEFAULT NULL COMMENT '生産数（ロット本数）'                                             AFTER `production_lot_size`,
  ADD COLUMN `take_count`              int          NULL DEFAULT NULL COMMENT '取数'                                                            AFTER `actual_production_quantity`,
  ADD COLUMN `cutting_length`          decimal(10,2) NULL DEFAULT NULL COMMENT '切断長'                                                         AFTER `take_count`,
  ADD COLUMN `chamfering_length`       decimal(10,2) NULL DEFAULT NULL COMMENT '面取長'                                                         AFTER `cutting_length`,
  ADD COLUMN `developed_length`        decimal(10,2) NULL DEFAULT NULL COMMENT '展開長'                                                         AFTER `chamfering_length`,
  ADD COLUMN `has_chamfering_process`  tinyint(1)   NULL DEFAULT 0    COMMENT '面取工程あり'                                                    AFTER `developed_length`,
  ADD COLUMN `lot_number`              varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'ロットNo.'      AFTER `has_chamfering_process`,
  ADD COLUMN `production_day`          date         NULL DEFAULT NULL COMMENT '生産日'                                                          AFTER `lot_number`;
