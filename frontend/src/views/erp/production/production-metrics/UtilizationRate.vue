<template>
  <ProductionMetricPage :config="config" />
</template>

<script setup lang="ts">
import { markRaw } from 'vue'
import { Monitor } from '@element-plus/icons-vue'
import ProductionMetricPage from './components/ProductionMetricPage.vue'
import type { ProductionMetricConfig } from './types'

const config: ProductionMetricConfig = {
  title: '稼働率',
  description: '設備や工程の計画時間に対する実稼働状況を確認する生産指標ページ',
  icon: markRaw(Monitor),
  gradient: 'linear-gradient(135deg, #409eff, #36cfc9)',
  formula: '稼働率 = 実稼働時間 ÷ 計画稼働時間 × 100',
  note: '設備能力がどれだけ使われているかを見る指標です。生産計画、指示、実績を結びつけることで負荷の偏りや未稼働時間を把握できます。',
  summaryCards: [
    { label: '当月稼働率', value: '-- %', sub: '設備実績 API 接続後に算出' },
    { label: '実稼働時間', value: '-- h', sub: '実績または作業ログから集計' },
    { label: '計画稼働時間', value: '-- h', sub: '計画・カレンダーから集計' },
  ],
  analysisRows: [
    { axis: '設備別', content: '設備ごとの稼働率を比較して負荷偏りを可視化', source: 'machines / instruction_plans' },
    { axis: '工程別', content: '工程単位で計画負荷と実績負荷の差を見る', source: 'process_cd / machine_type' },
    { axis: '期間別', content: '日別・週別・月別の稼働率推移を確認', source: 'start_date / actual_datetime' },
  ],
  implementationMemos: [
    '計画稼働時間は設備カレンダー、指示計画、標準工数のどれを基準にするかを決める必要があります。',
    '実稼働時間は作業開始・終了ログがない場合、実績数量 × 標準サイクルタイムで近似できます。',
    '将来的に設備別ヒートマップ、低稼働設備一覧、工程別負荷グラフを追加できる構成にしています。',
  ],
}
</script>
