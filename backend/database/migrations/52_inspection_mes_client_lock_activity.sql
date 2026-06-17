-- 検査 MES：端末ロック最終アクティビティ（checkpoint TTL 用）
ALTER TABLE `inspection_management`
  ADD COLUMN `mes_client_lock_activity_at` datetime NULL DEFAULT NULL
    COMMENT 'MES端末ロック最終アクティビティ（checkpoint・ロック取得時更新）'
  AFTER `mes_client_instance_id`;
