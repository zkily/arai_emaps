<template>
  <div class="lfa-page">
    <header class="lfa-page__header">
      <div class="lfa-page__brand">
        <div class="lfa-page__icon" aria-hidden="true">
          <el-icon :size="20"><Calendar /></el-icon>
        </div>
        <div class="lfa-page__text">
          <h1 class="lfa-page__title">生産ロット進捗管理</h1>
          <p class="lfa-page__meta">管理コードと出荷需要日（内示）の対応関係</p>
        </div>
      </div>
      <div class="lfa-page__stats">
        <span class="lfa-stat">
          <span class="lfa-stat__label">件数</span>
          <span class="lfa-stat__value">{{ filteredRows.length }}</span>
        </span>
        <span class="lfa-stat lfa-stat--done">
          <span class="lfa-stat__label">切断完了</span>
          <span class="lfa-stat__value">{{ cuttingDoneCount }}</span>
        </span>
        <span class="lfa-stat lfa-stat--done">
          <span class="lfa-stat__label">成型完了</span>
          <span class="lfa-stat__value">{{ moldingDoneCount }}</span>
        </span>
      </div>
    </header>

    <div class="lfa-page__body">
      <div class="lfa-toolbar">
        <div class="lfa-toolbar__head">
          <span class="lfa-toolbar__label">絞り込み</span>
          <div class="lfa-toolbar__actions">
            <el-button type="primary" size="small" :loading="loading" @click="loadList">検索</el-button>
            <el-button
              v-if="canEdit"
              type="warning"
              size="small"
              plain
              :loading="recomputeLoading"
              @click="recompute"
            >再計算</el-button>
            <el-button size="small" @click="resetFilter">リセット</el-button>
          </div>
        </div>
        <div class="lfa-toolbar__grid">
          <div class="lfa-filter-group lfa-filter-group--period">
            <span class="lfa-filter-group__tag">期間</span>
            <el-form :model="filter" inline size="small" class="lfa-filter-form">
              <el-form-item label="表示">
                <el-date-picker
                  v-model="filter.period"
                  type="daterange"
                  range-separator="~"
                  start-placeholder="開始"
                  end-placeholder="終了"
                  value-format="YYYY-MM-DD"
                  class="lfa-date-range"
                  @change="onFilterChange"
                />
              </el-form-item>
              <el-form-item label="計算開始">
                <el-date-picker
                  v-model="filter.recomputeStartDate"
                  type="date"
                  placeholder="開始日"
                  value-format="YYYY-MM-DD"
                  class="lfa-recompute-date"
                />
              </el-form-item>
            </el-form>
          </div>
          <div class="lfa-filter-group lfa-filter-group--attrs">
            <span class="lfa-filter-group__tag">条件</span>
            <el-form :model="filter" inline size="small" class="lfa-filter-form">
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
              <el-form-item label="切断完了">
                <el-select
                  v-model="filter.cutting_completed"
                  placeholder="全部"
                  clearable
                  class="lfa-cutting-select"
                  @change="onFilterChange"
                >
                  <el-option label="（全部）" value="" />
                  <el-option label="完了" value="done" />
                  <el-option label="未完了" value="pending" />
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
            </el-form>
          </div>
        </div>
        <el-alert
          v-if="!loading && filteredRows.length === 0"
          type="info"
          :closable="false"
          show-icon
          class="lfa-empty-hint"
          title="データがありません。「再計算」で指定開始日以降の帰属データを生成してください（全品番は数分かかることがあります）。"
        />
      </div>

      <div class="lfa-table-panel">
        <div class="lfa-table-toolbar">
          <div class="lfa-table-toolbar__left">
            <span class="lfa-table-toolbar__title">一覧</span>
            <span class="lfa-table-toolbar__count">{{ filteredRows.length }} 件</span>
            <span v-if="cuttingDoneCount > 0" class="lfa-table-toolbar__chip lfa-table-toolbar__chip--cut">
              切断完了 {{ cuttingDoneCount }}
            </span>
            <span v-if="moldingDoneCount > 0" class="lfa-table-toolbar__chip lfa-table-toolbar__chip--mold">
              成型完了 {{ moldingDoneCount }}
            </span>
          </div>
        </div>
        <div class="lfa-table-wrap">
        <el-table
          v-loading="loading || recomputeLoading"
          :data="pageRows"
          size="small"
          border
          stripe
          height="calc(100vh - 388px)"
          class="lfa-table"
          :row-class-name="tableRowClassName"
          highlight-current-row
          empty-text="該当データがありません"
        >
          <el-table-column
            prop="destination_name"
            label="納入先名"
            width="148"
            show-overflow-tooltip
            fixed="left"
            class-name="lfa-col--dest"
          >
            <template #default="{ row }">
              <span class="lfa-cell-dest">{{ row.destination_name || '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="product_cd" label="製品CD" width="76" show-overflow-tooltip class-name="lfa-col--code">
            <template #default="{ row }">
              <span class="lfa-cell-code">{{ row.product_cd || '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="product_name" label="製品名" min-width="136" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="lfa-cell-product">{{ row.product_name || '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column
            prop="forecast_attribution_date"
            label="出荷日"
            width="104"
            align="center"
            header-align="center"
            class-name="lfa-col--ship"
          >
            <template #default="{ row }">
              <span class="lfa-cell-ship">{{ formatAttributionDate(row.forecast_attribution_date) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="demand_product_cd" label="内示品番" width="80" show-overflow-tooltip class-name="lfa-col--code">
            <template #default="{ row }">
              <span class="lfa-cell-code">{{ row.demand_product_cd || '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column
            prop="attributed_qty"
            label="帰属数"
            width="80"
            align="right"
            header-align="right"
            class-name="lfa-col--qty"
          >
            <template #default="{ row }">
              <span class="lfa-cell-qty">{{ formatQty(row.attributed_qty) }}</span>
            </template>
          </el-table-column>
          <el-table-column
            prop="source_date"
            label="生産日"
            width="100"
            align="center"
            header-align="center"
            class-name="lfa-col--date"
          >
            <template #default="{ row }">
              <span class="lfa-cell-date">{{ formatAttributionDate(row.source_date) }}</span>
            </template>
          </el-table-column>
          <el-table-column
            prop="management_code"
            label="管理コード"
            min-width="176"
            show-overflow-tooltip
            class-name="lfa-col--mgmt"
          >
            <template #default="{ row }">
              <span class="lfa-cell-mgmt">{{ row.management_code || '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column
            prop="cutting_completed"
            label="切断完了"
            width="96"
            align="center"
            header-align="center"
            fixed="right"
            class-name="lfa-col--status"
          >
            <template #default="{ row }">
              <button
                type="button"
                class="lfa-status-btn"
                :class="{ 'lfa-status-btn--editable': canEdit }"
                :disabled="!canEdit"
                @click="openStatusDialog(row)"
              >
                <span
                  class="lfa-pill"
                  :class="[
                    row.cutting_completed ? 'lfa-pill--done' : 'lfa-pill--pending',
                    row.cutting_completed_source === 'MANUAL' ? 'lfa-pill--manual' : '',
                  ]"
                >
                  {{ row.cutting_completed ? '完了' : '未完了' }}
                </span>
              </button>
            </template>
          </el-table-column>
          <el-table-column
            prop="molding_completed"
            label="成型完了"
            width="96"
            align="center"
            header-align="center"
            fixed="right"
            class-name="lfa-col--status"
          >
            <template #default="{ row }">
              <button
                type="button"
                class="lfa-status-btn"
                :class="{ 'lfa-status-btn--editable': canEdit }"
                :disabled="!canEdit"
                @click="openStatusDialog(row)"
              >
                <span
                  class="lfa-pill"
                  :class="[
                    row.molding_completed ? 'lfa-pill--done' : 'lfa-pill--pending',
                    row.molding_completed_source === 'MANUAL' ? 'lfa-pill--manual' : '',
                  ]"
                >
                  {{ row.molding_completed ? '完了' : '未完了' }}
                </span>
              </button>
            </template>
          </el-table-column>
        </el-table>
        </div>
      </div>

      <el-dialog
        v-model="statusDialogVisible"
        title="進捗状態の手動指定"
        width="440px"
        destroy-on-close
        class="lfa-status-dialog"
        @closed="resetStatusForm"
      >
        <el-form label-width="108px" size="small">
          <el-form-item label="管理コード">
            <span class="lfa-status-dialog__mc">{{ statusForm.management_code || '—' }}</span>
          </el-form-item>
          <el-form-item label="切断完了">
            <el-radio-group v-model="statusForm.cutting_mode">
              <el-radio-button value="auto">自動</el-radio-button>
              <el-radio-button value="done">完了</el-radio-button>
              <el-radio-button value="pending">未完了</el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="成型完了">
            <el-radio-group v-model="statusForm.molding_mode">
              <el-radio-button value="auto">自動</el-radio-button>
              <el-radio-button value="done">完了</el-radio-button>
              <el-radio-button value="pending">未完了</el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="備考">
            <el-input
              v-model="statusForm.remark"
              type="textarea"
              :rows="2"
              maxlength="500"
              show-word-limit
              placeholder="手動指定の理由など"
            />
          </el-form-item>
          <p class="lfa-status-dialog__hint">
            手動指定は内示帰属の再計算では変更されません。「全自動に戻す」で解除できます。
          </p>
        </el-form>
        <template #footer>
          <el-button size="small" @click="statusDialogVisible = false">キャンセル</el-button>
          <el-button
            v-if="statusForm.has_override"
            size="small"
            type="warning"
            plain
            :loading="statusSaving"
            @click="clearStatusOverride"
          >
            全自動に戻す
          </el-button>
          <el-button size="small" type="primary" :loading="statusSaving" @click="saveStatusOverride">
            保存
          </el-button>
        </template>
      </el-dialog>

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
  clearProcessStatusOverride,
  getLotForecastAttribution,
  recomputeLotForecastAttribution,
  saveProcessStatusOverride,
  type LotForecastAttributionRow,
  type ProcessStatusTriState,
} from '@/api/lotForecastAttribution'
import { getDestinationOptions } from '@/api/master/destinationMaster'
import { useMesOperationPermission } from '@/composables/useMesOperationPermission'
import { guardMesOperation } from '@/utils/mesOperationGuard'

const { canEdit } = useMesOperationPermission()

const loading = ref(false)
const recomputeLoading = ref(false)
const rawList = ref<LotForecastAttributionRow[]>([])
const destinationOptions = ref<{ cd: string; name: string }[]>([])
const statusDialogVisible = ref(false)
const statusSaving = ref(false)
const statusForm = reactive({
  management_code: '',
  aps_batch_plan_id: null as number | null,
  cutting_mode: 'auto' as ProcessStatusTriState,
  molding_mode: 'auto' as ProcessStatusTriState,
  remark: '',
  has_override: false,
})

const DEFAULT_PROCESS_KEY = 'molding'

const filter = reactive({
  period: [] as string[],
  recomputeStartDate: '' as string,
  product_name: '',
  destination_cd: '',
  cutting_completed: '' as '' | 'done' | 'pending',
  molding_completed: '' as '' | 'done' | 'pending',
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
  if (filter.cutting_completed === 'done') {
    rows = rows.filter((r) => Boolean(r.cutting_completed))
  } else if (filter.cutting_completed === 'pending') {
    rows = rows.filter((r) => !r.cutting_completed)
  }
  if (filter.molding_completed === 'done') {
    rows = rows.filter((r) => Boolean(r.molding_completed))
  } else if (filter.molding_completed === 'pending') {
    rows = rows.filter((r) => !r.molding_completed)
  }
  return rows
})

const cuttingDoneCount = computed(() => filteredRows.value.filter((r) => Boolean(r.cutting_completed)).length)
const moldingDoneCount = computed(() => filteredRows.value.filter((r) => Boolean(r.molding_completed)).length)

const pageRows = computed(() => {
  const start = (pagination.currentPage - 1) * pagination.pageSize
  return filteredRows.value.slice(start, start + pagination.pageSize)
})

function formatQty(value?: number | null): string {
  if (value == null || Number.isNaN(Number(value))) return '—'
  return Number(value).toLocaleString('ja-JP')
}

function tableRowClassName({ row }: { row: LotForecastAttributionRow }): string {
  if (row.status_override) return 'lfa-row--manual-override'
  if (row.molding_completed) return 'lfa-row--molding-done'
  if (!row.cutting_completed) return 'lfa-row--cutting-pending'
  return ''
}

function sourceToTriState(
  completed: boolean | undefined,
  source?: 'AUTO' | 'MANUAL',
): ProcessStatusTriState {
  if (source === 'MANUAL') return completed ? 'done' : 'pending'
  return 'auto'
}

function triStateToNullableBool(mode: ProcessStatusTriState): boolean | null {
  if (mode === 'auto') return null
  return mode === 'done'
}

function openStatusDialog(row: LotForecastAttributionRow) {
  if (!guardMesOperation(canEdit)) return
  const mc = String(row.management_code ?? '').trim()
  if (!mc) {
    ElMessage.warning('管理コードがありません')
    return
  }
  statusForm.management_code = mc
  statusForm.aps_batch_plan_id = row.aps_batch_plan_id ?? null
  statusForm.cutting_mode = sourceToTriState(row.cutting_completed, row.cutting_completed_source)
  statusForm.molding_mode = sourceToTriState(row.molding_completed, row.molding_completed_source)
  statusForm.remark = String(row.status_remark ?? '')
  statusForm.has_override = Boolean(row.status_override)
  statusDialogVisible.value = true
}

function resetStatusForm() {
  statusForm.management_code = ''
  statusForm.aps_batch_plan_id = null
  statusForm.cutting_mode = 'auto'
  statusForm.molding_mode = 'auto'
  statusForm.remark = ''
  statusForm.has_override = false
}

async function saveStatusOverride() {
  if (!guardMesOperation(canEdit)) return
  const mc = statusForm.management_code.trim()
  if (!mc) return
  statusSaving.value = true
  try {
    await saveProcessStatusOverride({
      management_code: mc,
      aps_batch_plan_id: statusForm.aps_batch_plan_id,
      cutting_completed: triStateToNullableBool(statusForm.cutting_mode),
      molding_completed: triStateToNullableBool(statusForm.molding_mode),
      remark: statusForm.remark.trim() || null,
    })
    ElMessage.success('進捗状態を保存しました')
    statusDialogVisible.value = false
    await loadList()
  } catch (e) {
    console.error('進捗状態の保存に失敗:', e)
    ElMessage.error('進捗状態の保存に失敗しました')
  } finally {
    statusSaving.value = false
  }
}

async function clearStatusOverride() {
  if (!guardMesOperation(canEdit)) return
  const mc = statusForm.management_code.trim()
  if (!mc) return
  try {
    await ElMessageBox.confirm(
      'この管理コードの手動指定を解除し、自動判定に戻します。よろしいですか？',
      '手動指定の解除',
      { type: 'warning', confirmButtonText: '解除', cancelButtonText: 'キャンセル' },
    )
  } catch {
    return
  }
  statusSaving.value = true
  try {
    await clearProcessStatusOverride(mc)
    ElMessage.success('自動判定に戻しました')
    statusDialogVisible.value = false
    await loadList()
  } catch (e) {
    console.error('手動指定の解除に失敗:', e)
    ElMessage.error('手動指定の解除に失敗しました')
  } finally {
    statusSaving.value = false
  }
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
      process_key: DEFAULT_PROCESS_KEY,
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
  filter.cutting_completed = ''
  filter.molding_completed = ''
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
  gap: 10px;
}
.lfa-toolbar {
  padding: 8px 10px 10px;
  border: 1px solid #e7e5e4;
  border-radius: 10px;
  background: #fff;
  box-shadow: 0 1px 2px rgb(0 0 0 / 4%);
}
.lfa-toolbar__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid #f5f5f4;
}
.lfa-toolbar__label {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #78716c;
}
.lfa-toolbar__actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}
.lfa-toolbar__grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: stretch;
}
.lfa-filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1 1 auto;
  min-width: 0;
  padding: 6px 10px;
  border-radius: 8px;
  border: 1px solid transparent;
}
.lfa-filter-group--period {
  flex: 0 1 auto;
  background: linear-gradient(180deg, #eff6ff 0%, #f8fafc 100%);
  border-color: #bfdbfe;
}
.lfa-filter-group--period .lfa-filter-group__tag {
  color: #1d4ed8;
  background: #dbeafe;
}
.lfa-filter-group--attrs {
  flex: 1 1 480px;
  background: linear-gradient(180deg, #fffbeb 0%, #fffef8 100%);
  border-color: #fde68a;
}
.lfa-filter-group--attrs .lfa-filter-group__tag {
  color: #b45309;
  background: #fef3c7;
}
.lfa-filter-group__tag {
  flex-shrink: 0;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
  line-height: 1.4;
}
.lfa-filter-form {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 2px 4px;
  min-width: 0;
}
.lfa-filter-form :deep(.el-form-item) {
  margin-bottom: 0;
  margin-right: 0;
}
.lfa-filter-form :deep(.el-form-item__label) {
  padding-right: 6px;
  color: #57534e;
  font-weight: 500;
  font-size: 12px;
}
.lfa-date-range {
  width: 228px !important;
}
.lfa-recompute-date {
  width: 132px !important;
}
.lfa-product-select {
  width: 168px;
}
.lfa-dest-select {
  width: 148px;
}
.lfa-cutting-select,
.lfa-molding-select {
  width: 108px;
}
.lfa-empty-hint {
  margin-top: 8px;
  margin-bottom: 0;
}
.lfa-table-panel {
  border: 1px solid #fde68a;
  border-radius: 10px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 1px 4px rgb(180 83 9 / 6%);
}
.lfa-table-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 12px;
  background: linear-gradient(180deg, #fffbeb 0%, #fffef8 100%);
  border-bottom: 1px solid #fde68a;
}
.lfa-table-toolbar__left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.lfa-table-toolbar__title {
  font-size: 13px;
  font-weight: 700;
  color: #92400e;
}
.lfa-table-toolbar__count {
  font-size: 12px;
  font-weight: 600;
  color: #b45309;
  padding: 2px 8px;
  border-radius: 999px;
  background: #fff;
  border: 1px solid #fde68a;
}
.lfa-table-toolbar__chip {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 999px;
  line-height: 1.4;
}
.lfa-table-toolbar__chip--cut {
  color: #1d4ed8;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
}
.lfa-table-toolbar__chip--mold {
  color: #15803d;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
}
.lfa-table-wrap {
  background: #fff;
}
.lfa-table {
  --el-table-border-color: #fde68a;
  --el-table-header-bg-color: #fffbeb;
  --el-table-tr-bg-color: #ffffff;
  --el-table-row-hover-bg-color: #fff7ed;
  --el-table-current-row-bg-color: #fef3c7;
}
.lfa-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}
.lfa-table :deep(th.el-table__cell) {
  font-size: 11px;
  font-weight: 700;
  padding: 8px 0;
  color: #92400e !important;
  background: #fffbeb !important;
  border-bottom: 2px solid #fcd34d !important;
}
.lfa-table :deep(td.el-table__cell) {
  padding: 7px 0;
  font-size: 12px;
  color: #44403c !important;
  border-color: #fef3c7 !important;
}
.lfa-table :deep(.el-table__body tr.el-table__row--striped td.el-table__cell) {
  background: #fffef8 !important;
}
.lfa-table :deep(.el-table__body tr:hover > td.el-table__cell) {
  background: #fff7ed !important;
}
.lfa-table :deep(.el-table__fixed-right-patch) {
  background: #fffbeb !important;
}
.lfa-table :deep(.el-table__fixed-left),
.lfa-table :deep(.el-table__fixed-right) {
  box-shadow: none;
}
.lfa-table :deep(.el-table__fixed-left::before),
.lfa-table :deep(.el-table__fixed-right::before) {
  background-color: #fde68a;
}
.lfa-table :deep(.lfa-row--molding-done td.el-table__cell) {
  background: #f0fdf4 !important;
}
.lfa-table :deep(.lfa-row--molding-done.el-table__row--striped td.el-table__cell) {
  background: #ecfdf5 !important;
}
.lfa-table :deep(.lfa-row--molding-done:hover td.el-table__cell) {
  background: #dcfce7 !important;
}
.lfa-table :deep(.lfa-row--cutting-pending td.el-table__cell) {
  background: #fffbeb !important;
}
.lfa-table :deep(.lfa-row--cutting-pending.el-table__row--striped td.el-table__cell) {
  background: #fef9c3 !important;
}
.lfa-table :deep(.lfa-row--cutting-pending:hover td.el-table__cell) {
  background: #fef3c7 !important;
}
.lfa-cell-dest {
  font-weight: 600;
  color: #1c1917;
}
.lfa-cell-product {
  font-weight: 500;
  color: #292524;
}
.lfa-cell-code,
.lfa-cell-mgmt {
  font-family: ui-monospace, 'Cascadia Code', Consolas, monospace;
  font-size: 11px;
  color: #57534e;
  letter-spacing: -0.02em;
}
.lfa-cell-mgmt {
  font-weight: 600;
  color: #44403c;
}
.lfa-cell-ship {
  display: inline-block;
  min-width: 84px;
  padding: 2px 6px;
  border-radius: 6px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: #b45309;
  background: #fff7ed;
  border: 1px solid #fed7aa;
}
.lfa-cell-date {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: #57534e;
}
.lfa-cell-qty {
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: #c2410c;
}
.lfa-pill {
  display: inline-block;
  min-width: 52px;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 700;
  line-height: 1.5;
  white-space: nowrap;
  text-align: center;
}
.lfa-pill--done {
  color: #15803d;
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
}
.lfa-pill--pending {
  color: #b45309;
  background: #fff7ed;
  border: 1px solid #fed7aa;
}
.lfa-pill--plan {
  color: #1d4ed8;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
}
.lfa-pill--actual {
  color: #7c3aed;
  background: #f5f3ff;
  border: 1px solid #ddd6fe;
}
.lfa-pill--muted {
  color: #78716c;
  background: #fafaf9;
  border: 1px solid #e7e5e4;
}
.lfa-pill--manual {
  box-shadow: inset 0 0 0 1px rgb(180 83 9 / 25%);
  position: relative;
}
.lfa-pill--manual::after {
  content: '手';
  position: absolute;
  top: -6px;
  right: -6px;
  min-width: 14px;
  height: 14px;
  padding: 0 3px;
  border-radius: 999px;
  font-size: 9px;
  font-weight: 800;
  line-height: 14px;
  color: #fff;
  background: #d97706;
}
.lfa-status-btn {
  border: none;
  background: transparent;
  padding: 0;
  cursor: default;
}
.lfa-status-btn--editable {
  cursor: pointer;
}
.lfa-status-btn--editable:hover .lfa-pill {
  filter: brightness(0.97);
  transform: translateY(-1px);
}
.lfa-status-btn:disabled {
  cursor: default;
}
.lfa-table :deep(.lfa-row--manual-override td.el-table__cell) {
  background: #fff7ed !important;
}
.lfa-table :deep(.lfa-row--manual-override.el-table__row--striped td.el-table__cell) {
  background: #ffedd5 !important;
}
.lfa-status-dialog__mc {
  font-family: ui-monospace, 'Cascadia Code', Consolas, monospace;
  font-size: 12px;
  font-weight: 600;
  color: #44403c;
  word-break: break-all;
}
.lfa-status-dialog__hint {
  margin: 0;
  padding: 8px 10px;
  border-radius: 8px;
  font-size: 12px;
  line-height: 1.5;
  color: #78716c;
  background: #fffbeb;
  border: 1px solid #fde68a;
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
