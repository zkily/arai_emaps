-- MES 検査実績収集：バーコード/QR 読取値
SET NAMES utf8mb4;

ALTER TABLE `inspection_management`
  ADD COLUMN `mes_scanned_code` VARCHAR(512) NULL DEFAULT NULL
    COMMENT 'MES検査実績・バーコード/QR読取' AFTER `mes_defect_by_item`;
