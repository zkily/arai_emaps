-- ============================================================
-- Add MES production instruction submenu entries
-- ============================================================

-- Ensure MES production instruction parent exists under MES.
INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'MES_PRODUCTION_INSTRUCTION', '生産指示', mes.id, NULL, 'Document', 1
FROM menus mes
WHERE mes.code = 'MES'
LIMIT 1;

-- Ensure cutting instruction menu exists.
INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'MES_CUTTING_INSTRUCTION', '切断・面取指示', p.id, '/mes/instruction/cutting', 'Operation', 1
FROM menus p
WHERE p.code = 'MES_PRODUCTION_INSTRUCTION'
LIMIT 1;

-- Ensure forming instruction menu exists (align under parent).
INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'MES_FORMING_INSTRUCTION', '成型指示', p.id, '/mes/instruction/forming', 'Document', 2
FROM menus p
WHERE p.code = 'MES_PRODUCTION_INSTRUCTION'
LIMIT 1;

-- Ensure welding instruction menu exists.
INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'MES_WELDING_INSTRUCTION', '溶接指示', p.id, '/mes/instruction/welding', 'Connection', 3
FROM menus p
WHERE p.code = 'MES_PRODUCTION_INSTRUCTION'
LIMIT 1;

-- Ensure plating instruction menu exists.
INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'MES_PLATING_INSTRUCTION', 'メッキ指示', p.id, '/mes/instruction/plating', 'Operation', 4
FROM menus p
WHERE p.code = 'MES_PRODUCTION_INSTRUCTION'
LIMIT 1;

-- Normalize parent/path/sort/name for MES instruction menus.
UPDATE menus c
JOIN menus p ON p.code = 'MES_PRODUCTION_INSTRUCTION'
SET
  c.parent_id = p.id,
  c.name = CASE c.code
    WHEN 'MES_CUTTING_INSTRUCTION' THEN '切断・面取指示'
    WHEN 'MES_FORMING_INSTRUCTION' THEN '成型指示'
    WHEN 'MES_WELDING_INSTRUCTION' THEN '溶接指示'
    WHEN 'MES_PLATING_INSTRUCTION' THEN 'メッキ指示'
    ELSE c.name
  END,
  c.path = CASE c.code
    WHEN 'MES_CUTTING_INSTRUCTION' THEN '/mes/instruction/cutting'
    WHEN 'MES_FORMING_INSTRUCTION' THEN '/mes/instruction/forming'
    WHEN 'MES_WELDING_INSTRUCTION' THEN '/mes/instruction/welding'
    WHEN 'MES_PLATING_INSTRUCTION' THEN '/mes/instruction/plating'
    ELSE c.path
  END,
  c.sort_order = CASE c.code
    WHEN 'MES_CUTTING_INSTRUCTION' THEN 1
    WHEN 'MES_FORMING_INSTRUCTION' THEN 2
    WHEN 'MES_WELDING_INSTRUCTION' THEN 3
    WHEN 'MES_PLATING_INSTRUCTION' THEN 4
    ELSE c.sort_order
  END
WHERE c.code IN (
  'MES_CUTTING_INSTRUCTION',
  'MES_FORMING_INSTRUCTION',
  'MES_WELDING_INSTRUCTION',
  'MES_PLATING_INSTRUCTION'
);

-- Grant new MES instruction menus to roles that already have MES instruction scope.
INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT DISTINCT src.role_id, dst.id
FROM role_menu_permissions src
JOIN menus src_menu ON src_menu.id = src.menu_id
JOIN menus dst ON dst.code IN (
  'MES_CUTTING_INSTRUCTION',
  'MES_WELDING_INSTRUCTION',
  'MES_PLATING_INSTRUCTION'
)
WHERE src_menu.code IN ('MES_PRODUCTION_INSTRUCTION', 'MES_FORMING_INSTRUCTION');
