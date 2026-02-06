<template>
  <LineChart :labels="labels" :data="data" label="平均単価 (¥)" />
</template>

<script setup lang="ts">
import { ref, defineExpose } from 'vue'
import LineChart from './LineChart.vue'

const labels = ref<string[]>([])
const data = ref<number[]>([])

interface ChartDataRow {
  ym: string
  avg_unit_price?: number
}

const setData = (rows: ChartDataRow[]) => {
  labels.value = rows.map(r => r.ym)
  data.value = rows.map(r => Number(r.avg_unit_price ?? 0))
}

defineExpose({ setData })
</script>
