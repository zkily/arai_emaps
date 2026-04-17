-- production_plan_excel: 検索 生成列を「年月日 + 加工機後方2桁 + 順番」に修正（誤って 生産順番 を連結していた）
-- 依赖：表 production_plan_excel に列 日付、加工機、順番、検索 が存在すること。
-- 順番 が NULL の行（未重算など）は末尾を空文字にし、CONCAT 全体が NULL にならないようにする。

ALTER TABLE `production_plan_excel`
  MODIFY COLUMN `検索` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_ja_0900_as_cs
  GENERATED ALWAYS AS (
    concat(
      date_format(`日付`, '%Y%m%d'),
      right(`加工機`, 2),
      coalesce(cast(`順番` AS CHAR), '')
    )
  ) STORED NULL COMMENT '検索キー (自動生成: 年月日 + 加工機後方2桁 + 順番)';
