-- 部品受入ログ (part_logs) — material_logs と同形

CREATE TABLE IF NOT EXISTS `part_logs` (
  `id`               bigint         NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `item`             varchar(100)   NOT NULL COMMENT '項目',
  `part_cd`          varchar(50)    NOT NULL COMMENT '部品CD',
  `part_name`        varchar(255)   NULL DEFAULT NULL COMMENT '部品名',
  `process_cd`       varchar(50)    NOT NULL COMMENT '工程CD',
  `log_date`         date           NOT NULL COMMENT '日付',
  `log_time`         time           NOT NULL COMMENT '時間',
  `hd_no`            varchar(50)    NULL DEFAULT NULL COMMENT 'HD番号',
  `pieces_per_bundle` int           NULL DEFAULT NULL COMMENT '1束あたりの本数',
  `quantity`         int            NULL DEFAULT NULL COMMENT '数量',
  `bundle_quantity`  int            NULL DEFAULT NULL COMMENT '束数量',
  `manufacture_no`   varchar(255)   NULL DEFAULT NULL COMMENT '製造番号',
  `manufacture_date` date           NULL DEFAULT NULL COMMENT '製造日',
  `length`           int            NULL DEFAULT NULL COMMENT '長さ(mm)',
  `outer_diameter1`  decimal(10,4)  NULL DEFAULT NULL COMMENT '外径1(mm)',
  `outer_diameter2`  decimal(10,4)  NULL DEFAULT NULL COMMENT '外径2(mm)',
  `magnetic`         varchar(1)     NULL DEFAULT NULL COMMENT '磁気',
  `appearance`       varchar(1)     NULL DEFAULT NULL COMMENT '外観',
  `supplier`         varchar(255)   NULL DEFAULT NULL COMMENT '仕入先',
  `part_quality`     varchar(100)   NULL DEFAULT NULL COMMENT '部品規格',
  `remarks`          text           NULL COMMENT '備考',
  `note`             varchar(255)   NULL DEFAULT NULL COMMENT 'メモ',
  `created_at`       timestamp      NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at`       timestamp      NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_part_cd`        (`part_cd`),
  KEY `idx_process_cd`     (`process_cd`),
  KEY `idx_log_date`       (`log_date`),
  KEY `idx_manufacture_no` (`manufacture_no`),
  KEY `idx_supplier`       (`supplier`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = '部品受入ログ';
