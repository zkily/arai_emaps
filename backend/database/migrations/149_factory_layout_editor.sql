-- 工場レイアウト編集：回転・ロック・グループ
ALTER TABLE factory_layout_objects
  ADD COLUMN rotation INT NOT NULL DEFAULT 0 COMMENT '回転角 0/90/180/270',
  ADD COLUMN locked TINYINT(1) NOT NULL DEFAULT 0 COMMENT '1=ロック',
  ADD COLUMN group_key VARCHAR(36) NULL COMMENT '同一キーはグループ';
