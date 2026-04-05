<template>
  <div class="material-consumption">
    <header class="page-head">
      <div class="page-head__title">
        <span class="page-head__icon" aria-hidden="true">
          <el-icon><TrendCharts /></el-icon>
        </span>
        <h1 class="page-head__text">材料消費実績</h1>
      </div>
      <el-tooltip content="再取得" placement="bottom">
        <el-button :icon="Refresh" circle plain type="primary" class="page-head__refresh" @click="refreshAll" />
      </el-tooltip>
    </header>

    <el-card class="panel panel--filter" shadow="hover" :body-style="{ padding: '10px 14px' }">
      <el-form :inline="true" :model="filters" class="filter-form" size="small" @keyup.enter.prevent="handleSearch">
        <el-form-item label="材料" class="filter-form__item">
          <el-select
            v-model="filters.material_cd"
            class="material-select"
            placeholder="選択"
            clearable
            filterable
            :filter-method="filterMaterialOption"
            :loading="materialOptionsLoading"
            default-first-option
            @clear="materialFilterKeyword = ''"
          >
            <el-option
              v-for="m in materialOptionsFiltered"
              :key="m.material_cd"
              :label="materialOptionLabel(m)"
              :value="m.material_cd"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="期間" class="filter-form__item">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            range-separator="〜"
            start-placeholder="開始"
            end-placeholder="終了"
            value-format="YYYY-MM-DD"
            unlink-panels
            class="filter-form__daterange"
          />
        </el-form-item>
        <el-form-item class="filter-form__actions">
          <el-button type="primary" :icon="Search" @click="handleSearch">検索</el-button>
          <el-button :icon="RefreshLeft" @click="handleReset">リセット</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-row :gutter="10" class="chart-grid">
      <el-col :xs="24" :lg="12">
        <el-card class="panel panel--chart" shadow="hover" :body-style="{ padding: '8px 10px 6px' }">
          <template #header>
            <div class="panel__header">
              <el-icon class="panel__header-icon"><Histogram /></el-icon>
              <span>日別使用数</span>
            </div>
          </template>
          <div ref="dateChartRef" class="chart-host" />
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="12">
        <el-card class="panel panel--chart" shadow="hover" :body-style="{ padding: '8px 10px 6px' }">
          <template #header>
            <div class="panel__header">
              <el-icon class="panel__header-icon"><PieChart /></el-icon>
              <span>材料別（上位）</span>
            </div>
          </template>
          <div ref="materialChartRef" class="chart-host" />
        </el-card>
      </el-col>
    </el-row>

    <el-card class="panel" shadow="hover" :body-style="{ padding: '0 0 10px' }">
      <template #header>
        <div class="panel__header panel__header--spread">
          <div class="panel__header">
            <el-icon class="panel__header-icon"><List /></el-icon>
            <span>レコード</span>
            <el-tag v-if="pagination.total" type="info" effect="plain" size="small" class="panel__count">
              {{ pagination.total.toLocaleString() }} 件
            </el-tag>
          </div>
        </div>
      </template>
      <div class="table-wrap">
        <el-table
          :data="recordList"
          v-loading="loading"
          size="small"
          stripe
          border
          class="data-table"
          :header-cell-style="tableHeaderStyle"
        >
          <el-table-column prop="usage_date" label="使用日" width="108" fixed />
          <el-table-column prop="material_cd" label="材料CD" width="112" />
          <el-table-column prop="material_name" label="材料名" min-width="140" show-overflow-tooltip />
          <el-table-column prop="usage_count" label="使用数" width="92" align="right">
            <template #default="{ row }">
              {{ formatQty(row.usage_count) }}
            </template>
          </el-table-column>
          <el-table-column prop="source" label="来源" width="130" show-overflow-tooltip />
          <el-table-column prop="management_code" label="管理コード" width="128" show-overflow-tooltip />
          <el-table-column prop="reflected" label="反映" width="72" align="center">
            <template #default="{ row }">
              <el-tag :type="row.reflected ? 'success' : 'warning'" size="small" effect="plain">
                {{ row.reflected ? '済' : '未' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="作成日時" width="158" show-overflow-tooltip />
          <el-table-column label="" width="72" fixed="right" align="center">
            <template #default="{ row }">
              <el-button size="small" type="primary" link @click="openDetail(row)">詳細</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div class="pagination-bar">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          background
          size="small"
          @size-change="pagination.page = 1"
        />
      </div>
    </el-card>

    <el-dialog
      v-model="detailVisible"
      title="詳細"
      width="480px"
      destroy-on-close
      class="detail-dialog"
      align-center
    >
      <el-descriptions v-if="detailRow" :column="1" border size="small">
        <el-descriptions-item label="ID">{{ detailRow.id }}</el-descriptions-item>
        <el-descriptions-item label="使用日">{{ detailRow.usage_date ?? '—' }}</el-descriptions-item>
        <el-descriptions-item label="材料CD">{{ detailRow.material_cd }}</el-descriptions-item>
        <el-descriptions-item label="材料名">{{ detailRow.material_name }}</el-descriptions-item>
        <el-descriptions-item label="使用数">{{ formatQty(detailRow.usage_count) }}</el-descriptions-item>
        <el-descriptions-item label="来源">{{ detailRow.source }}</el-descriptions-item>
        <el-descriptions-item label="管理コード">{{ detailRow.management_code || '—' }}</el-descriptions-item>
        <el-descriptions-item label="複数コード">{{ detailRow.management_codes || '—' }}</el-descriptions-item>
        <el-descriptions-item label="反映済">{{ detailRow.reflected ? 'はい' : 'いいえ' }}</el-descriptions-item>
        <el-descriptions-item label="作成">{{ detailRow.created_at ?? '—' }}</el-descriptions-item>
        <el-descriptions-item label="更新">{{ detailRow.updated_at ?? '—' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, RefreshLeft, TrendCharts, Histogram, PieChart, List } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import dayjs from 'dayjs'

import {
  getMaterialUsageRecords,
  getMaterialUsageRecordsChartSummary,
  type MaterialUsageRecordItem,
} from '@/api/material'
import { getMaterialList } from '@/api/master/materialMaster'
import type { Material } from '@/types/master'

const chartAxisMuted = '#94a3b8'
const chartPrimary = '#3b82f6'
const chartAccent = '#10b981'
const chartTooltipBg = 'rgba(15, 23, 42, 0.92)'

const tableHeaderStyle = {
  background: 'var(--mc-table-header-bg)',
  color: 'var(--mc-table-header-color)',
  fontWeight: '600',
  fontSize: '12px',
}

const loading = ref(false)
const recordList = ref<MaterialUsageRecordItem[]>([])

const materialOptionsLoading = ref(false)
const materialOptions = ref<Material[]>([])
const materialFilterKeyword = ref('')

const defaultRange = (): [string, string] => {
  const end = dayjs()
  const start = end.subtract(29, 'day')
  return [start.format('YYYY-MM-DD'), end.format('YYYY-MM-DD')]
}

const filters = reactive({
  material_cd: '' as string,
  dateRange: defaultRange() as string[] | null,
})

function materialOptionLabel(m: Material): string {
  const cd = m.material_cd ?? ''
  const name = m.material_name ?? ''
  return name ? `${cd}　${name}` : cd
}

const materialOptionsFiltered = computed(() => {
  const kw = materialFilterKeyword.value.trim().toLowerCase()
  if (!kw) return materialOptions.value
  return materialOptions.value.filter((m) => {
    const cd = (m.material_cd ?? '').toLowerCase()
    const name = (m.material_name ?? '').toLowerCase()
    return cd.includes(kw) || name.includes(kw)
  })
})

function filterMaterialOption(val: string) {
  materialFilterKeyword.value = val
}

async function loadMaterialOptions() {
  materialOptionsLoading.value = true
  try {
    const res = await getMaterialList({ page: 1, pageSize: 5000 })
    const list = res?.data?.list ?? (res as { list?: Material[] })?.list ?? []
    materialOptions.value = Array.isArray(list) ? list : []
  } catch (e) {
    console.error(e)
    materialOptions.value = []
    ElMessage.error('材料マスタの取得に失敗しました')
  } finally {
    materialOptionsLoading.value = false
  }
}

const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const dateChartRef = ref<HTMLElement | null>(null)
const materialChartRef = ref<HTMLElement | null>(null)
let dateChart: echarts.ECharts | null = null
let materialChart: echarts.ECharts | null = null

const detailVisible = ref(false)
const detailRow = ref<MaterialUsageRecordItem | null>(null)

function formatQty(v: unknown): string {
  if (v == null || v === '') return '—'
  const n = Number(v)
  if (!Number.isFinite(n)) return String(v)
  return n.toLocaleString(undefined, { maximumFractionDigits: 4 })
}

function listQueryParams() {
  const q: Record<string, string | number | boolean> = {
    page: pagination.page,
    page_size: pagination.pageSize,
  }
  if (filters.material_cd.trim()) q.material_cd = filters.material_cd.trim()
  if (filters.dateRange?.length === 2) {
    q.date_from = filters.dateRange[0]
    q.date_to = filters.dateRange[1]
  }
  return q
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getMaterialUsageRecords(listQueryParams() as Parameters<typeof getMaterialUsageRecords>[0])
    if (res?.success === false) {
      recordList.value = []
      pagination.total = 0
      return
    }
    const data = res?.data
    recordList.value = data?.list ?? []
    pagination.total = data?.total ?? 0
  } catch (e) {
    console.error(e)
    recordList.value = []
    pagination.total = 0
    ElMessage.error('一覧の取得に失敗しました')
  } finally {
    loading.value = false
  }
}

async function fetchCharts() {
  try {
    const params = { ...listQueryParams() }
    delete params.page
    delete params.page_size
    const res = await getMaterialUsageRecordsChartSummary(params)
    if (res?.success === false || !res?.data) {
      renderDateChart([])
      renderMaterialChart([])
      return
    }
    renderDateChart(res.data.by_date ?? [])
    renderMaterialChart(res.data.by_material ?? [])
  } catch (e) {
    console.error(e)
    renderDateChart([])
    renderMaterialChart([])
  }
}

function baseChartTextStyle() {
  return {
    color: chartAxisMuted,
    fontSize: 11,
  }
}

function renderDateChart(rows: Array<{ usage_date: string | null; total: number }>) {
  const el = dateChartRef.value
  if (!el) return
  if (!dateChart) dateChart = echarts.init(el, null, { renderer: 'canvas' })
  const x = rows.map((r) => r.usage_date ?? '')
  const y = rows.map((r) => r.total)
  dateChart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: chartTooltipBg,
      borderWidth: 0,
      textStyle: { color: '#f1f5f9', fontSize: 12 },
    },
    grid: {
      left: 48,
      right: 12,
      top: 14,
      bottom: x.length > 14 ? 20 : 12,
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: x,
      axisLine: { lineStyle: { color: chartAxisMuted } },
      axisLabel: {
        ...baseChartTextStyle(),
        fontSize: 10,
        rotate: x.length > 14 ? 32 : 0,
        interval: 0,
        hideOverlap: false,
        margin: 10,
      },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.2)', type: 'dashed' } },
      axisLabel: baseChartTextStyle(),
    },
    series: [
      {
        type: 'bar',
        data: y,
        barMaxWidth: 22,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#60a5fa' },
            { offset: 1, color: chartPrimary },
          ]),
          borderRadius: [4, 4, 0, 0],
        },
      },
    ],
  })
  dateChart.resize()
}

function renderMaterialChart(
  rows: Array<{ material_cd: string; material_name: string; total: number }>,
) {
  const el = materialChartRef.value
  if (!el) return
  if (!materialChart) materialChart = echarts.init(el, null, { renderer: 'canvas' })
  const labels = rows.map((r) => {
    const name = r.material_name || r.material_cd
    return name.length > 16 ? `${name.slice(0, 16)}…` : name
  })
  const values = rows.map((r) => r.total)
  materialChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: chartTooltipBg,
      borderWidth: 0,
      textStyle: { color: '#f1f5f9', fontSize: 12 },
      formatter: (items: unknown) => {
        const arr = items as { dataIndex: number; value: number }[]
        if (!arr?.length) return ''
        const i = arr[0].dataIndex
        const row = rows[i]
        if (!row) return ''
        return `${row.material_cd} ${row.material_name}<br/>${formatQty(row.total)}`
      },
    },
    grid: { left: 6, right: 36, top: 6, bottom: 6, containLabel: true },
    xAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.2)', type: 'dashed' } },
      axisLabel: baseChartTextStyle(),
    },
    yAxis: {
      type: 'category',
      data: labels,
      inverse: true,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { ...baseChartTextStyle(), width: 108, overflow: 'truncate' },
    },
    series: [
      {
        type: 'bar',
        data: values,
        barMaxWidth: 18,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#34d399' },
            { offset: 1, color: chartAccent },
          ]),
          borderRadius: [0, 4, 4, 0],
        },
      },
    ],
  })
  materialChart.resize()
}

function disposeCharts() {
  dateChart?.dispose()
  materialChart?.dispose()
  dateChart = null
  materialChart = null
}

function onResize() {
  dateChart?.resize()
  materialChart?.resize()
}

async function refreshAll() {
  pagination.page = 1
  await Promise.all([fetchCharts(), fetchList()])
}

const handleSearch = () => {
  pagination.page = 1
  Promise.all([fetchCharts(), fetchList()])
}

const handleReset = () => {
  filters.material_cd = ''
  materialFilterKeyword.value = ''
  filters.dateRange = defaultRange()
  pagination.page = 1
  Promise.all([fetchCharts(), fetchList()])
}

function openDetail(row: MaterialUsageRecordItem) {
  detailRow.value = row
  detailVisible.value = true
}

watch(
  () => [pagination.page, pagination.pageSize] as const,
  () => {
    fetchList()
  },
)

onMounted(async () => {
  window.addEventListener('resize', onResize)
  await nextTick()
  await loadMaterialOptions()
  await Promise.all([fetchCharts(), fetchList()])
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  disposeCharts()
})
</script>

<style scoped>
.material-consumption {
  --mc-surface: #ffffff;
  --mc-page-bg: linear-gradient(160deg, #f1f5f9 0%, #e8eef5 45%, #f8fafc 100%);
  --mc-border: rgba(15, 23, 42, 0.06);
  --mc-shadow: 0 1px 2px rgba(15, 23, 42, 0.04), 0 4px 16px rgba(15, 23, 42, 0.06);
  --mc-table-header-bg: #f8fafc;
  --mc-table-header-color: #475569;

  min-height: 100%;
  padding: 12px 14px 14px;
  box-sizing: border-box;
  background: var(--mc-page-bg);
}

.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  padding: 2px 2px 0;
}

.page-head__title {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.page-head__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #fff;
  font-size: 18px;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.35);
}

.page-head__text {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #0f172a;
  line-height: 1.2;
}

.page-head__refresh {
  flex-shrink: 0;
}

.panel {
  border-radius: 12px;
  border: 1px solid var(--mc-border);
  box-shadow: var(--mc-shadow) !important;
  background: var(--mc-surface);
  margin-bottom: 10px;
}

.panel--filter {
  margin-bottom: 10px;
}

.panel--filter :deep(.el-card__header) {
  display: none;
}

.panel--chart :deep(.el-card__header) {
  padding: 8px 12px;
  border-bottom: 1px solid var(--mc-border);
}

.panel :deep(.el-card__header) {
  padding: 10px 14px;
  border-bottom: 1px solid var(--mc-border);
}

.panel__header {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #334155;
}

.panel__header--spread {
  width: 100%;
  justify-content: space-between;
}

.panel__header-icon {
  font-size: 16px;
  color: #64748b;
}

.panel__count {
  margin-left: 4px;
  font-weight: 500;
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 0;
  margin-right: 14px;
}

.filter-form__actions {
  margin-right: 0 !important;
}

.filter-form__actions :deep(.el-button + .el-button) {
  margin-left: 8px;
}

.material-select {
  width: min(360px, 72vw);
}

.filter-form__daterange {
  width: 240px;
}

@media (min-width: 900px) {
  .filter-form__daterange {
    width: 260px;
  }
}

.chart-grid {
  margin-bottom: 0 !important;
}

.chart-grid > .el-col {
  margin-bottom: 10px;
}

.chart-host {
  width: 100%;
  height: 268px;
  min-height: 268px;
}

.table-wrap {
  padding: 0 10px;
}

.data-table {
  width: 100%;
}

.data-table :deep(.el-table__cell) {
  padding: 6px 8px;
  font-size: 12px;
}

.pagination-bar {
  display: flex;
  justify-content: flex-end;
  padding: 8px 12px 0;
}
</style>

<style>
/* 詳細ダイアログ：角丸・余白（Teleport 先のため非 scoped） */
.detail-dialog.el-dialog {
  border-radius: 14px;
  overflow: hidden;
}
.detail-dialog .el-dialog__header {
  padding: 12px 16px 8px;
  margin: 0;
}
.detail-dialog .el-dialog__body {
  padding: 8px 16px 16px;
}
</style>
