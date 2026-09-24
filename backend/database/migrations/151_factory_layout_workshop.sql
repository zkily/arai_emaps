-- 工場レイアウト：総図と车间の親子
ALTER TABLE factory_layouts
  ADD COLUMN kind VARCHAR(20) NOT NULL DEFAULT 'workshop' COMMENT 'site=総図 / workshop=车间',
  ADD COLUMN parent_id INT NULL COMMENT '親レイアウト';

ALTER TABLE factory_layouts
  ADD KEY idx_factory_layouts_parent (parent_id),
  ADD CONSTRAINT fk_factory_layouts_parent
    FOREIGN KEY (parent_id) REFERENCES factory_layouts (id) ON DELETE SET NULL;

ALTER TABLE factory_layout_objects
  ADD COLUMN child_layout_id INT NULL COMMENT 'このブロックが開く内部レイアウト';

ALTER TABLE factory_layout_objects
  ADD KEY idx_factory_layout_objects_child (child_layout_id),
  ADD CONSTRAINT fk_factory_layout_objects_child
    FOREIGN KEY (child_layout_id) REFERENCES factory_layouts (id) ON DELETE SET NULL;
