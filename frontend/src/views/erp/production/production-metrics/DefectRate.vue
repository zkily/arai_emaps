<template>
  <ProductionMetricPage :config="config" />
</template>

<script setup lang="ts">
import { markRaw } from 'vue'
import { Warning } from '@element-plus/icons-vue'
import ProductionMetricPage from './components/ProductionMetricPage.vue'
import type { ProductionMetricConfig } from './types'

const config: ProductionMetricConfig = {
  title: '不良率',
  description: '工程・製品別に不良数量の発生傾向を確認する品質系の生産指標ページ',
  icon: markRaw(Warning),
  gradient: 'linear-gradient(135deg, #e6a23c, #f7ba2a)',
  formula: '不良率 = 不良数 ÷ (良品実績数 + 不良数) × 100',
  note: '投入または完成実績に対して不良がどれだけ発生したかを見る指標です。工程別の不良率を追うことで品質異常の発生箇所を特定しやすくします。',
  summaryCards: [
    { label: '当月不良率', value: '-- %', sub: 'API 接続後に実績から算出' },
    { label: '不良数', value: '--', sub: 'stock_transaction_logs の不良数量' },
    { label: '良品実績数', value: '--', sub: '実績数量から集計' },
  ],
  analysisRows: [
    { axis: '工程別', content: '不良率が高い工程を抽出して重点改善対象を確認', source: 'stock_transaction_logs.process_cd' },
    { axis: '製品別', content: '製品ごとの不良傾向や特定品番の品質変動を確認', source: 'product_cd / product_name' },
    { axis: '日別推移', content: '不良率の急上昇日を検知して原因調査につなげる', source: 'transaction_time' },
  ],
  implementationMemos: [
    '不良数は在庫取引ログの transaction_type = 不良 を基本データにする想定です。',
    '分母に廃棄を含めるかどうかは廃棄率との定義分離に合わせて調整できます。',
    '将来的に不良理由別集計、工程別ランキング、製品別明細テーブルを追加できる構成にしています。',
  ],
}
</script>
