-- 設備ごとの APS 順次再計算アンカー日（成型計画等で保存し、replan-sequence で優先使用）
CREATE TABLE IF NOT EXISTS aps_line_replan_anchors (
  line_id INT NOT NULL COMMENT 'machines.id',
  anchor_date DATE NOT NULL COMMENT '順次再計算の開始暦日（日本日付想定）',
  updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (line_id),
  CONSTRAINT fk_aps_line_replan_anchors_machine FOREIGN KEY (line_id) REFERENCES machines (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='設備別再計算アンカー日';
