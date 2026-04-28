<template>
  <ProductionMetricPage :config="config" />
</template>

<script setup lang="ts">
import { markRaw } from 'vue'
import { Delete } from '@element-plus/icons-vue'
import ProductionMetricPage from './components/ProductionMetricPage.vue'
import type { ProductionMetricConfig } from './types'

const config: ProductionMetricConfig = {
  title: '廃棄率',
  description: '工程・製品別に廃棄数量の発生傾向を確認する生産指標ページ',
  icon: markRaw(Delete),
  gradient: 'linear-gradient(135deg, #f56c6c, #ff7875)',
  formula: '廃棄率 = 廃棄数 ÷ (良品実績数 + 不良数 + 廃棄数) × 100',
  note: '生産実績に対して廃棄がどれだけ発生したかを見る指標です。工程別・製品別に見ることで材料ロスや設備条件の異常を追跡しやすくします。',
  summaryCards: [
    { label: '当月廃棄率', value: '-- %', sub: 'API 接続後に実績から算出' },
    { label: '廃棄数', value: '--', sub: 'stock_transaction_logs の廃棄数量' },
    { label: '対象実績数', value: '--', sub: '実績 + 不良 + 廃棄' },
  ],
  analysisRows: [
    { axis: '工程別', content: '切断・面取・成型・溶接・検査など工程単位で廃棄率を比較', source: 'stock_transaction_logs.process_cd' },
    { axis: '製品別', content: '廃棄率が高い製品や品番を抽出', source: 'product_cd / product_name' },
    { axis: '日別推移', content: '日次の廃棄率変動を見て突発的な異常日を確認', source: 'transaction_time' },
  ],
  implementationMemos: [
    '廃棄数は在庫取引ログの transaction_type = 廃棄 を基本データにする想定です。',
    '分母は同一期間・同一工程の実績、不良、廃棄の合計で統一すると工程間比較がしやすくなります。',
    '将来的に工程別ランキング、日別トレンド、製品別明細テーブルを追加できる構成にしています。',
  ],
}
</script>
