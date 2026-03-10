-- cutting_management に使用材料の material_usage_record 反映状態を保持するカラムを追加
-- 使用数反映実行後は '反映済'、未反映は '未反映'
SET NAMES utf8mb4;

ALTER TABLE `cutting_management`
  ADD COLUMN `material_usage_reflected` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '未反映'
    COMMENT '使用材料が material_usage_record に反映済みか（反映済/未反映）'
    AFTER `production_completed_check`;
