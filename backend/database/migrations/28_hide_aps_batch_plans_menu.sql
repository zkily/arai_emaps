-- APSロット計画：サイドバー非表示（成型計画「生産進捗」で代替）。ページ/API は残す。
UPDATE menus SET is_active = 0 WHERE code = 'APS_BATCH_PLANS';
