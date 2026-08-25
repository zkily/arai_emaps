-- 設備×製品の期間指定能率（成型計画作成などで日別上限に反映。未指定時は従来の equipment_efficiency）
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS equipment_efficiency_period_override (
  id INT NOT NULL AUTO_INCREMENT,
  machine_cd VARCHAR(50) NOT NULL COMMENT '設備CD',
  machines_name VARCHAR(100) NULL COMMENT '設備名（表示用）',
  product_cd VARCHAR(50) NOT NULL COMMENT '製品CD',
  product_name VARCHAR(100) NULL COMMENT '製品名（表示用）',
  efficiency_rate DECIMAL(10, 1) NOT NULL COMMENT '能率（本/H）',
  period_from DATE NOT NULL COMMENT '適用開始日（含む）',
  period_to DATE NOT NULL COMMENT '適用終了日（含む）',
  status INT NULL DEFAULT 1 COMMENT '1=有効 0=無効',
  remarks TEXT NULL,
  created_at DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_ee_period_ov_machine (machine_cd),
  KEY idx_ee_period_ov_product (product_cd),
  KEY idx_ee_period_ov_period (machine_cd, product_cd, period_from, period_to)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='設備能率の期間指定（製品+設備+期間）';
