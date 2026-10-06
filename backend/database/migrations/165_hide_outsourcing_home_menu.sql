-- 外注管理：外注ホーム（外注ダッシュボード）を廃止し、旧画面メニューも非表示にする
UPDATE menus SET is_active = 0
WHERE code IN (
    'ERP_OUTSOURCING_HOME',
    'ERP_OUTSOURCING_DASHBOARD',
    'ERP_OUTSOURCING_STOCK',
    'ERP_OUTSOURCING_WELDING_RECEIVING'
);
