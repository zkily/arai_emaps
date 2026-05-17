-- MES 切断実績：稼働/一時停止（多端末同期用）
ALTER TABLE `cutting_management`
  ADD COLUMN `mes_production_is_paused` TINYINT(1) NULL DEFAULT NULL
    COMMENT 'MES稼働計測:1=一時停止中,0=稼働中,NULL=未開始/終了済'
    AFTER `mes_paused_accum_sec`;
