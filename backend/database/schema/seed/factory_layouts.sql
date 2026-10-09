-- SEED: factory_layouts
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

INSERT IGNORE INTO `factory_layouts` (`id`, `name`, `canvas_width`, `canvas_height`, `grid_size`, `kind`, `parent_id`) VALUES
(1, 'サンプル工場', 1600, 900, 20, 'workshop', NULL);

SET FOREIGN_KEY_CHECKS = 1;
