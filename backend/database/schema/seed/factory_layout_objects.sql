-- SEED: factory_layout_objects
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

INSERT IGNORE INTO `factory_layout_objects` (`id`, `layout_id`, `object_type`, `x`, `y`, `width`, `height`, `label`, `ref_cd`, `z_index`, `rotation`, `locked`, `group_key`, `fill_color`, `border_color`, `opacity`, `child_layout_id`) VALUES
(1, 1, 'machine', 80, 80, 140, 90, '成形機 A', NULL, 20, 0, 0, NULL, NULL, NULL, 100, NULL),
(2, 1, 'machine', 280, 80, 140, 90, '溶接機 B', NULL, 20, 0, 0, NULL, NULL, NULL, 100, NULL),
(3, 1, 'machine', 480, 80, 140, 90, '検査台 C', NULL, 20, 0, 0, NULL, NULL, NULL, 100, NULL),
(4, 1, 'aisle', 60, 220, 760, 72, '主通路', NULL, 0, 0, 0, NULL, NULL, NULL, 100, NULL),
(5, 1, 'material_zone', 80, 360, 220, 130, '材料置き場', NULL, 10, 0, 0, NULL, NULL, NULL, 100, NULL);

SET FOREIGN_KEY_CHECKS = 1;
