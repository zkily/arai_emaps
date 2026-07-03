<template>
  <div class="lfa-page">
    <header class="lfa-page__header">
      <div class="lfa-page__brand">
        <div class="lfa-page__icon" aria-hidden="true">
          <el-icon :size="20"><Calendar /></el-icon>
        </div>
        <div class="lfa-page__text">
          <h1 class="lfa-page__title">内示帰属管理</h1>
          <p class="lfa-page__meta">管理コードと出荷需要日（内示）の対応関係</p>
        </div>
      </div>
      <div class="lfa-page__stats">
        <span class="lfa-stat">
          <span class="lfa-stat__label">件数</span>
          <span class="lfa-stat__value">{{ filteredRows.length }}</span>
        </span>
        <span class="lfa-stat lfa-stat--done">
          <span class="lfa-stat__label">成型完了</span>
          <span class="lfa-stat__value">{{ moldingDoneCount }}</span>
        </span>
      </div>
    </header>

    <div class="lfa-page__body">
      <div class="lfa-toolbar">
        <span class="lfa-toolbar__label">絞り込み</span>
        <el-form :model="filter" inline size="small" class="lfa-filter-form">
          <el-form-item label="表示期間">
            <el-date-picker
              v-model="filter.period"
              type="daterange"
              range-separator="~"
              start-placeholder="開始日"
              end-placeholder="終了日"
              value-format="YYYY-MM-DD"
              class="lfa-date-range"
              @change="onFilterChange"
            />
          </el-form-item>
          <el-form-item label="計算開始日">
            <el-date-picker
              v-model="filter.recomputeStartDate"
              type="date"
              placeholder="開始日"
              value-format="YYYY-MM-DD"
              class="lfa-recompute-date"
            />
          </el-form-item>
          <el-form-item label="製品名">
            <el-select
              v-model="filter.product_name"
              placeholder="全部"
              clearable
              filterable
              class="lfa-product-select"
              popper-class="data-management-product-select-dropdown"
              @change="onFilterChange"
            >
              <el-option label="（全部）" value="" />
              <el-option v-for="name in productNameOptions" :key="name" :label="name" :value="name" />
            </el-select>
          </el-form-item>
          <el-form-item label="納入先">
            <el-select
              v-model="filter.destination_cd"
              placeholder="全部"
              clearable
              filterable
              class="lfa-dest-select"
              @change="onFilterChange"
            >
              <el-option label="（全部）" value="" />
              <el-option
                v-for="opt in destinationOptions"
                :key="opt.cd"
                :label="opt.name || opt.cd"
                :value="opt.cd"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="成型完了">
            <el-select
              v-model="filter.molding_completed"
              placeholder="全部"
              clearable
              class="lfa-molding-select"
              @change="onFilterChange"
            >
              <el-option label="（全部）" value="" />
              <el-option label="完了" value="done" />
              <el-option label="未完了" value="pending" />
            </el-select>
          </el-form-item>
          <el-form-item label="工程">
            <el-select
              v-model="filter.process_key"
              clearable
              placeholder="全部"
              class="lfa-process-select"
              @change="onFilterChange"
            >
              <el-option label="（全部）" value="" />
              <el-option label="成型" value="molding" />
              <el-option label="切断" value="cutting" />
              <el-option label="面取" value="chamfering" />
              <el-option label="メッキ" value="plating" />
              <el-option label="溶接" value="welding" />
              <el-option label="検査" value="inspection" />
            </el-select>
          </el-form-item>
          <el-form-item class="lfa-filter-actions">
            <el-button type="primary" :loading="loading" @click="loadList">検索</el-button>
            <el-button
              v-if="canEdit"
              :loading="recomputeLoading"
              @click="recompute"
            >再計算</el-button>
            <el-button @click="resetFilter">リセット</el-button>
          </el-form-item>
        </el-form>
        <el-alert
          v-if="!loading && filteredRows.length === 0"
          type="info"
          :closable="false"
          show-icon
          class="lfa-empty-hint"
          title="データがありません。「再計算」で指定開始日以降の帰属データを生成してください（全品番は数分かかることがあります）。"
        />
      </div>

      <div class="lfa-table-wrap">
        <el-table
          v-loading="loading || recomputeLoading"
          :data="pageRows"
          size="small"
          border
          stripe
          height="calc(100vh - 340px)"
          class="lfa-table"
          empty-text="該当データがありません"
        >
          <el-table-column prop="management_code" label="管理コード" min-width="180" show-overflow-tooltip fixed="left" />
          <el-table-column prop="molding_completed" label="成型完了" width="88" align="center">
            <template #default="{ row }">
              <el-tag :type="row.molding_completed ? 'success' : 'info'" size="small" effect="plain">
                {{ row.molding_completed ? '完了' : '未完了' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="current_process_label" label="現工程" width="96" align="center">
            <template #default="{ row }">
              <span v-if="row.molding_completed">—</span>
              <span v-else>{{ row.current_process_label || lotProcessLabel(row.current_process_key) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="product_cd" label="製品CD" min-width="100" show-overflow-tooltip />
          <el-table-column prop="product_name" label="製品名" min-width="140" show-overflow-tooltip>
            <template #default="{ row }">{{ row.product_name || '—' }}</template>
          </el-table-column>
          <el-table-column prop="destination_name" label="納入先名" min-width="120" show-overflow-tooltip>
            <template #default="{ row }">{{ row.destination_name || '—' }}</template>
          </el-table-column>
          <el-table-column prop="demand_product_cd" label="需要品番" min-width="100" show-overflow-tooltip>
            <template #default="{ row }">{{ row.demand_product_cd || '—' }}</template>
          </el-table-column>
          <el-table-column prop="forecast_attribution_date" label="内示帰属日" width="108" align="center">
            <template #default="{ row }">{{ formatAttributionDate(row.forecast_attribution_date) }}</template>
          </el-table-column>
          <el-table-column prop="attributed_qty" label="帰属数" width="80" align="right" />
          <el-table-column prop="source_date" label="工程日" width="100" align="center">
            <template #default="{ row }">{{ formatAttributionDate(row.source_date) }}</template>
          </el-table-column>
          <el-table-column prop="process_key" label="工程" width="72" align="center">
            <template #default="{ row }">{{ processLabel(row.process_key) }}</template>
          </el-table-column>
          <el-table-column prop="attribution_mode" label="区分" width="72" align="center">
            <template #default="{ row }">{{ modeLabel(row.attribution_mode) }}</template>
          </el-table-column>
          <el-table-column prop="method" label="方式" width="100" align="center">
            <template #default="{ row }">{{ methodLabel(row.method) }}</template>
          </el-table-column>
          <el-table-column prop="confidence" label="信頼度" width="80" align="center">
            <template #default="{ row }">
              <el-tag
                v-if="row.confidence && row.confidence !== 'HIGH'"
                :type="row.confidence === 'OVERFLOW' ? 'warning' : 'info'"
                size="small"
                effect="plain"
              >{{ row.confidence }}</el-tag>
              <span v-else>—</span>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="lfa-footer">
        <span class="lfa-footer__total">計 {{ filteredRows.length }} 件</span>
        <el-pagination
          v-model:current-page="pagination.currentPage"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[50, 100, 200]"
          :total="filteredRows.length"
          size="small"
          layout="total, sizes, prev, pager, next"
          background
          @size-change="pagination.currentPage = 1"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { Calendar } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import {
  getLotForecastAttribution,
  recomputeLotForecastAttribution,
  type LotForecastAttributionRow,
} from '@/api/lotForecastAttribution'
import { getDestinationOptions } from '@/api/master/destinationMaster'
import { useMesOperationPermission } from '@/composables/useMesOperationPermission'
import { guardMesOperation } from '@/utils/mesOperationGuard'

const { canEdit } = useMesOperationPermission()

const loading = ref(false)
const recomputeLoading = ref(false)
const rawList = ref<LotForecastAttributionRow[]>([])
const destinationOptions = ref<{ cd: string; name: string }[]>([])

const filter = reactive({
  period: [] as string[],
  recomputeStartDate: '' as string,
  product_name: '',
  destination_cd: '',
  molding_completed: '' as '' | 'done' | 'pending',
  process_key: 'molding',
})

const pagination = reactive({ currentPage: 1, pageSize: 100 })

const productNameOptions = computed(() => {
  const set = new Set<string>()
  rawList.value.forEach((row) => {
    const name = String(row.product_name ?? '').trim()
    if (name) set.add(name)
  })
  return Array.from(set).sort((a, b) => a.localeCompare(b, 'ja'))
})

const filteredRows = computed(() => {
  let rows = rawList.value.filter((r) => String(r.management_code ?? '').trim().length > 0)
  const productName = filter.product_name.trim()
  if (productName) {
    rows = rows.filter((r) => String(r.product_name ?? '').trim() === productName)
  }
  const destCd = filter.destination_cd.trim()
  if (destCd) {
    rows = rows.filter((r) => String(r.destination_cd ?? '').trim() === destCd)
  }
  if (filter.molding_completed === 'done') {
    rows = rows.filter((r) => Boolean(r.molding_completed))
  } else if (filter.molding_completed === 'pending') {
    rows = rows.filter((r) => !r.molding_completed)
  }
  return rows
})

const moldingDoneCount = computed(() => filteredRows.value.filter((r) => Boolean(r.molding_completed)).length)

const pageRows = computed(() => {
  const start = (pagination.currentPage - 1) * pagination.pageSize
  return filteredRows.value.slice(start, start + pagination.pageSize)
})

function processLabel(key?: string | null): string {
  const map: Record<string, string> = {
    molding: '成型',
    cutting: '切断',
    chamfering: '面取',
    plating: 'メッキ',
    welding: '溶接',
    inspection: '検査',
  }
  return map[String(key ?? '')] || String(key ?? '—')
}

function methodLabel(method?: string | null): string {
  const map: Record<string, string> = {
    FIFO_DEMAND: 'FIFO',
    FIFO_OVERFLOW: '需要超過',
    CHAIN_INHERIT: '継承',
    INVENTORY_PEG: '在庫充当',
    NO_DEMAND: '内示なし',
  }
  return map[String(method ?? '')] || String(method ?? '—')
}

function modeLabel(mode?: string | null): string {
  if (mode === 'PLAN') return '計画'
  if (mode === 'ACTUAL') return '実績'
  return String(mode ?? '—')
}

function lotProcessLabel(key?: string | null): string {
  const map: Record<string, string> = {
    batch: '生産ロット',
    cutting: '切断',
    chamfering: '面取',
    chamfering_pending: '面取待ち',
    molding_pending: '成型待ち',
    molding: '成型',
    molding_completed: '成型完了',
    unknown: '不明',
  }
  return map[String(key ?? '')] || String(key ?? '—')
}

function formatAttributionDate(value?: string | null): string {
  if (!value) return '—'
  return String(value).slice(0, 10)
}

function initFilterPeriod() {
  const today = dayjs()
  const fiscalYear = today.month() >= 6 ? today.year() : today.year() - 1
  const start = dayjs(`${fiscalYear}-07-01`)
  const end = start.add(3, 'month').subtract(1, 'day')
  filter.period = [start.format('YYYY-MM-DD'), end.format('YYYY-MM-DD')]
  if (!filter.recomputeStartDate) {
    filter.recomputeStartDate = start.format('YYYY-MM-DD')
  }
}

function onFilterChange() {
  pagination.currentPage = 1
}

async function loadDestinationOptions() {
  try {
    destinationOptions.value = await getDestinationOptions()
  } catch {
    destinationOptions.value = []
  }
}

async function loadList() {
  if (!filter.period?.length || filter.period.length < 2) {
    initFilterPeriod()
  }
  const [startDate, endDate] = filter.period
  loading.value = true
  try {
    const params: Record<string, string | boolean> = {
      start_date: startDate,
      end_date: endDate,
      prefer_actual: true,
    }
    if (filter.process_key) {
      params.process_key = filter.process_key
    }
    const res = await getLotForecastAttribution(params)
    rawList.value = res.data ?? []
    pagination.currentPage = 1
  } catch (e) {
    console.error('内示帰属一覧の取得に失敗:', e)
    ElMessage.error('内示帰属一覧の取得に失敗しました')
    rawList.value = []
  } finally {
    loading.value = false
  }
}

function resetFilter() {
  filter.product_name = ''
  filter.destination_cd = ''
  filter.molding_completed = ''
  filter.process_key = 'molding'
  initFilterPeriod()
  filter.recomputeStartDate = filter.period[0] || ''
  pagination.currentPage = 1
  loadList()
}

async function recompute() {
  if (!guardMesOperation(canEdit)) return
  if (!filter.recomputeStartDate) {
    initFilterPeriod()
  }
  const startDate = filter.recomputeStartDate || filter.period?.[0]
  if (!startDate) {
    ElMessage.warning('計算開始日を指定してください')
    return
  }
  try {
    await ElMessageBox.confirm(
      `${startDate} 以降の管理コード帰属を再計算します。よろしいですか？`,
      '内示帰属の再計算',
      { type: 'warning', confirmButtonText: '再計算', cancelButtonText: 'キャンセル' },
    )
  } catch {
    return
  }
  recomputeLoading.value = true
  ElMessage.info('内示帰属を再計算しています。完了までお待ちください…')
  try {
    const res = await recomputeLotForecastAttribution({
      startDate,
      modes: ['PLAN', 'ACTUAL'],
    })
    const inserted = res.data?.inserted ?? 0
    ElMessage.success(`再計算が完了しました（${inserted} 件）`)
    await loadList()
  } catch (e: unknown) {
    const err = e as { code?: string; message?: string; response?: { data?: { detail?: string } } }
    const isTimeout =
      err.code === 'ECONNABORTED' || String(err.message || '').toLowerCase().includes('timeout')
    const msg = isTimeout
      ? '再計算がタイムアウトしました。しばらく待ってから再試行してください。'
      : err.response?.data?.detail ?? err.message ?? '再計算に失敗しました'
    console.error('内示帰属の再計算に失敗:', e)
    ElMessage.error(String(msg))
  } finally {
    recomputeLoading.value = false
  }
}

onMounted(async () => {
  initFilterPeriod()
  await loadDestinationOptions()
  await loadList()
})
</script>

<style scoped>
.lfa-page {
  min-height: 100%;
  padding: 16px 20px 20px;
  background: #fafaf9;
}
.lfa-page__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 16px;
  padding: 14px 18px;
  border: 1px solid #fde68a;
  border-radius: 12px;
  background: linear-gradient(180deg, #fffbeb 0%, #ffffff 100%);
  box-shadow: 0 1px 3px rgb(180 83 9 / 8%);
}
.lfa-page__brand {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}
.lfa-page__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  color: #fff;
  flex-shrink: 0;
}
.lfa-page__text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.lfa-page__title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: #92400e;
}
.lfa-page__meta {
  margin: 0;
  font-size: 13px;
  color: #78716c;
}
.lfa-page__stats {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.lfa-stat {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  min-width: 64px;
  padding: 6px 12px;
  border-radius: 8px;
  background: #fff;
  border: 1px solid #fde68a;
}
.lfa-stat--done {
  border-color: #bbf7d0;
  background: #f0fdf4;
}
.lfa-stat__label {
  font-size: 11px;
  color: #78716c;
}
.lfa-stat__value {
  font-size: 16px;
  font-weight: 700;
  color: #b45309;
  line-height: 1.2;
}
.lfa-stat--done .lfa-stat__value {
  color: #15803d;
}
.lfa-page__body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.lfa-toolbar {
  padding: 12px 14px;
  border: 1px solid #fde68a;
  border-radius: 10px;
  background: linear-gradient(180deg, #fffbeb 0%, #ffffff 100%);
  box-shadow: 0 1px 2px rgb(180 83 9 / 6%);
}
.lfa-toolbar__label {
  display: block;
  margin-bottom: 8px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: #b45309;
  text-transform: uppercase;
}
.lfa-filter-form :deep(.el-form-item) {
  margin-bottom: 6px;
  margin-right: 10px;
}
.lfa-filter-form :deep(.el-form-item__label) {
  color: #57534e;
  font-weight: 500;
}
.lfa-date-range {
  width: 260px !important;
}
.lfa-recompute-date {
  width: 150px !important;
}
.lfa-product-select {
  width: 200px;
}
.lfa-dest-select {
  width: 180px;
}
.lfa-molding-select,
.lfa-process-select {
  width: 120px;
}
.lfa-filter-actions :deep(.el-form-item__content) {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.lfa-empty-hint {
  margin-top: 10px;
  margin-bottom: 0;
}
.lfa-table-wrap {
  border: 1px solid #e7e5e4;
  border-radius: 10px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 1px 3px rgb(0 0 0 / 4%);
}
.lfa-table :deep(.el-table__header th) {
  background: #fffbeb !important;
  color: #78350f;
  font-weight: 600;
}
.lfa-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.lfa-footer__total {
  font-size: 13px;
  font-weight: 600;
  color: #b45309;
}
</style>
