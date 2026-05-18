-- MES 検査実績：端末ロック（同一在産行の二重接続防止）
SET NAMES utf8mb4;

ALTER TABLE `inspection_management`
  ADD COLUMN `mes_client_instance_id` varchar(64) NULL DEFAULT NULL
    COMMENT 'MES操作端末ID（localStorage UUID）' AFTER `mes_inspector_user_id`;
