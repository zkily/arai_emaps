-- ============================================================
-- Unify MES / ERP 「成型指示」 onto ERP route and single menu entry
-- ============================================================

-- Roles that only had MES forming gain ERP forming menu access.
INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT DISTINCT rmp.role_id, erp.id
FROM role_menu_permissions rmp
JOIN menus mes ON mes.id = rmp.menu_id AND mes.code = 'MES_FORMING_INSTRUCTION'
JOIN menus erp ON erp.code = 'ERP_PRODUCTION_INSTR_FORMING';

DELETE rmp FROM role_menu_permissions rmp
JOIN menus m ON m.id = rmp.menu_id AND m.code = 'MES_FORMING_INSTRUCTION';

DELETE FROM menus WHERE code = 'MES_FORMING_INSTRUCTION';

UPDATE menus SET sort_order = 2 WHERE code = 'MES_WELDING_INSTRUCTION';
UPDATE menus SET sort_order = 3 WHERE code = 'MES_PLATING_INSTRUCTION';
