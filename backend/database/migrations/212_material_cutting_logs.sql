-- material_cutting_logs: materialCutting.csv の手動インポート先
CREATE TABLE IF NOT EXISTS material_cutting_logs (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    item            VARCHAR(100),
    log_date        DATE,
    log_time        TIME,
    hd_no           VARCHAR(255),
    operator_name   VARCHAR(100),
    material_cd     VARCHAR(255),
    management_code VARCHAR(255),
    raw_line        TEXT,
    source_file     VARCHAR(500),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_mcl_log_date (log_date),
    INDEX idx_mcl_hd_no (hd_no),
    INDEX idx_mcl_material_cd (material_cd),
    INDEX idx_mcl_management_code (management_code)
);
