-- 切断→面取の参照整合性：切断指示削除時に面取指示を連動削除（API でカンバン・面取・切断の順で削除するため、本 FK は補助）
-- 運用: バッチへ戻す時は API move-from-cutting が ①カンバン ②面取 ③切断 の順で削除してから instruction_plans に挿入する
SET NAMES utf8mb4;

-- 既存の面取指示の cutting_management_id が cutting_management に存在する場合のみ FK を付与（孤立レコードがあると付与失敗）
ALTER TABLE `chamfering_management`
  ADD CONSTRAINT `fk_chamfering_cutting`
  FOREIGN KEY (`cutting_management_id`) REFERENCES `cutting_management` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT;
