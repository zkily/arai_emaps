<template>
  <div class="fdp-chart">
    <div class="fdp-chart__toolbar">
      <el-select v-model="localProduct" filterable size="small" class="fdp-chart__product" @change="render">
        <el-option v-for="p in products" :key="p.product_cd" :label="`${p.product_cd}`" :value="p.product_cd" />
      </el-select>
      <el-select v-model="localProcesses" multiple collapse-tags size="small" class="fdp-chart__process" @change="render">
        <el-option v-for="p in chartProcessOptions" :key="p.key" :label="p.label" :value="p.key" />
      </el-select>
      <el-radio-group v-model="mode" size="small" @change="render">
        <el-radio-button value="inventory">{{ t('formingDailyPlan.modeInventory') }}</el-radio-button>
        <el-radio-button value="trend">{{ t('formingDailyPlan.modeTrend') }}</el-radio-button>
      </el-radio-group>
      <el-checkbox v-model="showCompare" @change="render">{{ t('formingDailyPlan.showCompare') }}</el-checkbox>
    </div>
    <div ref="chartRef" class="fdp-chart__canvas" />
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts'
import type { FormingDailyPlanSummaryData } from '@/api/formingDailyPlan'
import { FORMING_PLAN_PROCESS_OPTIONS, processColor, processLabel } from './formingDailyPlanConstants'

const props = defineProps<{
  summary: FormingDailyPlanSummaryData | null
  products: { product_cd: string; product_name?: string }[]
}>()

const { t } = useI18n()
const chartRef = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null
const localProduct = ref('')
const localProcesses = ref<string[]>(['molding', 'plating', 'outsourced_plating', 'warehouse'])
const mode = ref<'inventory' | 'trend'>('inventory')
const showCompare = ref(true)

const chartProcessOptions = FORMING_PLAN_PROCESS_OPTIONS

watch(
  () => props.summary,
  () => {
    if (!localProduct.value && props.products.length) {
      localProduct.value = props.products[0].product_cd
    }
    render()
  },
  { deep: true }
)

watch(
  () => props.products,
  (list) => {
    if (!localProduct.value && list.length) localProduct.value = list[0].product_cd
  },
  { immediate: true }
)

function render() {
  if (!chartRef.value || !props.summary || !localProduct.value) return
  if (!chart) chart = echarts.init(chartRef.value)

  const dates = props.summary.dates
  const series: echarts.SeriesOption[] = []

  if (mode.value === 'inventory') {
    for (const pk of localProcesses.value) {
      const row = props.summary.inventory_matrix.rows.find(
        (r) => r.product_cd === localProduct.value && r.process_key === pk
      )
      if (!row) continue
      series.push({
        name: `${processLabel(pk)} (${t('formingDailyPlan.simulated')})`,
        type: 'line',
        smooth: true,
        data: dates.map((d) => row.by_date[d]?.simulated ?? 0),
        itemStyle: { color: processColor(pk) },
      })
      if (showCompare.value) {
        series.push({
          name: `${processLabel(pk)} (${t('formingDailyPlan.current')})`,
          type: 'line',
          smooth: true,
          lineStyle: { type: 'dashed' },
          data: dates.map((d) => row.by_date[d]?.current ?? 0),
          itemStyle: { color: processColor(pk), opacity: 0.5 },
        })
      }
    }
  } else {
    for (const pk of localProcesses.value) {
      const row = props.summary.trend_matrix?.rows.find(
        (r) => r.product_cd === localProduct.value && r.process_key === pk
      )
      if (!row) continue
      series.push({
        name: processLabel(pk),
        type: 'line',
        smooth: true,
        data: dates.map((d) => row.by_date[d] ?? 0),
        itemStyle: { color: processColor(pk) },
      })
    }
  }

  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { type: 'scroll', bottom: 0 },
    grid: { left: 48, right: 16, top: 24, bottom: 48 },
    xAxis: { type: 'category', data: dates.map((d) => d.slice(5)) },
    yAxis: { type: 'value' },
    series,
  }, true)
}

function onResize() {
  chart?.resize()
}

onMounted(() => {
  render()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  chart?.dispose()
  chart = null
})
</script>

<style scoped>
.fdp-chart__toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  margin-bottom: 6px;
  padding: 6px 8px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}
.fdp-chart__product { width: 148px; }
.fdp-chart__process { width: 180px; }
.fdp-chart__canvas {
  width: 100%;
  height: 320px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  background: #fff;
}
</style>
