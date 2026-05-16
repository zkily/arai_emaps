-- MES 切断実績収集：バーコード/QR 読取値
SET NAMES utf8mb4;

ALTER TABLE `cutting_management`
  ADD COLUMN `mes_scanned_code` VARCHAR(512) NULL DEFAULT NULL
    COMMENT 'MES切断実績・バーコード/QR読取' AFTER `mes_operator_user_id`;
