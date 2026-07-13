<template>
  <div class="lqm-page" :class="`lqm-page--${labelType}`">
    <header class="lqm-hero">
      <div class="lqm-hero-inner">
        <div class="lqm-title-row">
          <span class="lqm-title-icon"><el-icon :size="22"><DataAnalysis /></el-icon></span>
          <div>
            <div class="lqm-title-line">
              <h1 class="lqm-title">ラベル枚数管理</h1>
              <span class="lqm-type-pill">{{ labelTypeLabel }} · {{ monthsCount }}ヶ月</span>
            </div>
            <p class="lqm-subtitle">
              月末理論残＝月初＋発行済−必要枚数。印刷すると当月の発行済に枚数が加算されます。手改月初は再計算で上書きしません。
            </p>
          </div>
        </div>
        <div class="lqm-kpi">
          <div class="lqm-kpi-card"><span class="lqm-kpi-num">{{ kpi.total }}</span><span class="lqm-kpi-lbl">対象</span></div>
          <div class="lqm-kpi-card lqm-kpi-card--ok"><span class="lqm-kpi-num">{{ kpi.sufficient }}</span><span class="lqm-kpi-lbl">全月充足</span></div>
          <div class="lqm-kpi-card lqm-kpi-card--ng"><span class="lqm-kpi-num">{{ kpi.insufficient }}</span><span class="lqm-kpi-lbl">不足あり</span></div>
          <div class="lqm-kpi-card lqm-kpi-card--short"><span class="lqm-kpi-num">{{ formatNum(kpi.shortage_qty_sum) }}</span><span class="lqm-kpi-lbl">不足枚数Σ</span></div>
          <div class="lqm-kpi-card lqm-kpi-card--issue"><span class="lqm-kpi-num">{{ formatNum(kpi.issued_qty_sum || 0) }}</span><span class="lqm-kpi-lbl">発行済Σ</span></div>
          <div class="lqm-kpi-card"><span class="lqm-kpi-num">{{ formatNum(kpi.issue_qty_sum) }}</span><span class="lqm-kpi-lbl">発行予定紙Σ</span></div>
          <div class="lqm-kpi-card"><span class="lqm-kpi-num">{{ formatNum(kpi.closing_theory_sum || 0) }}</span><span class="lqm-kpi-lbl">期末理論Σ</span></div>
        </div>
      </div>
    </header>

    <section class="lqm-toolbar-card">
      <div class="lqm-toolbar">
        <div class="lqm-filters">
          <div class="lqm-filter-field">
            <label class="lqm-field-label">開始月</label>
            <el-date-picker
              v-model="startMonth"
              type="month"
              value-format="YYYY-MM"
              format="YYYY-MM"
              size="small"
              class="lqm-month"
              :clearable="false"
              @change="loadList"
            />
          </div>
          <el-radio-group v-model="monthsCount" size="small" class="lqm-type-tabs" @change="loadList">
            <el-radio-button :value="1">1ヶ月</el-radio-button>
            <el-radio-button :value="2">2ヶ月</el-radio-button>
            <el-radio-button :value="3">3ヶ月</el-radio-button>
          </el-radio-group>
          <el-radio-group v-model="labelType" size="small" class="lqm-type-tabs" @change="loadList">
            <el-radio-button value="molding">成型用</el-radio-button>
            <el-radio-button value="product_use">製品用</el-radio-button>
          </el-radio-group>
          <div class="lqm-filter-field lqm-filter-field--search">
            <label class="lqm-field-label">キーワード</label>
            <el-input
              v-model="filters.keyword"
              placeholder="製品CD・名称"
              clearable
              size="small"
              @clear="loadList"
              @keyup.enter="loadList"
            />
          </div>
          <div class="lqm-filter-field">
            <label class="lqm-field-label">判定</label>
            <el-select v-model="filters.sufficiency" size="small" class="lqm-filter" @change="loadList">
              <el-option label="すべて" value="all" />
              <el-option label="全月充足" value="sufficient" />
              <el-option label="不足あり" value="insufficient" />
            </el-select>
          </div>
        </div>
        <div class="lqm-toolbar-actions">
          <el-button size="small" class="lqm-btn lqm-btn--ghost" :icon="Refresh" :loading="loading" @click="loadList">
            再読込
          </el-button>
          <el-button
            v-if="canEdit"
            size="small"
            class="lqm-btn lqm-btn--teal"
            :loading="recalcLoading"
            @click="onRecalculate"
          >
            期間再計算
          </el-button>
          <el-button
            v-if="canEdit"
            size="small"
            class="lqm-btn lqm-btn--warn"
            :loading="filling"
            @click="onFillIssue"
          >
            紙枚数で埋める
          </el-button>
          <el-button
            v-if="canEdit"
            size="small"
            class="lqm-btn lqm-btn--primary"
            :icon="Check"
            :loading="saving"
            :disabled="!dirtyCount"
            @click="onSave"
          >
            一括保存{{ dirtyCount ? ` (${dirtyCount})` : '' }}
          </el-button>
        </div>
      </div>
    </section>

    <section class="lqm-table-wrap">
      <div class="lqm-result-bar">
        <span class="lqm-result-text">
          <strong>{{ list.length }}</strong> 件
          <span class="lqm-result-sep">|</span>
          {{ monthKeys.join(' / ') }}
          <template v-if="dirtyCount"> · 未保存 {{ dirtyCount }}</template>
        </span>
        <div class="lqm-legend">
          <span class="lqm-legend-item lqm-legend-item--stock">月初</span>
          <span class="lqm-legend-item lqm-legend-item--demand">需要/必要</span>
          <span class="lqm-legend-item lqm-legend-item--issue">発行済</span>
          <span class="lqm-legend-item lqm-legend-item--close">月末理論</span>
        </div>
      </div>

      <el-table
        v-loading="loading"
        :data="list"
        stripe
        size="small"
        border
        class="lqm-table"
        height="100%"
        :row-class-name="rowClassName"
      >
        <el-table-column prop="product_cd" label="製品CD" width="112" fixed="left">
          <template #default="{ row }"><span class="lqm-cd">{{ row.product_cd }}</span></template>
        </el-table-column>
        <el-table-column label="ラベル名" min-width="120" fixed="left" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="lqm-name">{{ row.label_product_name || row.master_product_name || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="入数" width="60" align="right" fixed="left">
          <template #default="{ row }">
            <span :class="{ 'lqm-cell-warn': row.unit_qty_missing }">
              {{ row.unit_qty_missing ? '未' : formatNum(row.unit_qty) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column
          v-for="(ym, mi) in monthKeys"
          :key="ym"
          :label="monthLabel(ym)"
          align="center"
          :class-name="`lqm-month-group lqm-month-group--${mi}`"
        >
          <el-table-column label="月初" width="108" align="right">
            <template #default="{ row }">
              <div class="lqm-open-cell">
                <el-input-number
                  :model-value="monthOf(row, ym)?.opening_stock ?? 0"
                  :min="-999999"
                  :step="1"
                  :controls="false"
                  size="small"
                  class="lqm-num lqm-num--stock"
                  :class="{ 'lqm-num--locked': monthOf(row, ym)?.opening_locked }"
                  :disabled="!canEdit"
                  @update:model-value="(v: number | undefined) => onOpeningChange(row, ym, v)"
                />
                <el-button
                  v-if="canEdit && monthOf(row, ym)?.opening_locked"
                  link
                  type="warning"
                  size="small"
                  class="lqm-unlock"
                  @click="unlockOpening(row, ym)"
                >
                  手動
                </el-button>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="需要" width="72" align="right">
            <template #default="{ row }">
              <span class="lqm-num-demand">{{ formatNum(monthOf(row, ym)?.demand_units) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="必要" width="72" align="right">
            <template #default="{ row }">
              <span v-if="monthOf(row, ym)?.required_qty == null" class="lqm-cell-warn">—</span>
              <span v-else class="lqm-num-demand">{{ formatNum(monthOf(row, ym)?.required_qty) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="発行予定紙" width="88" align="right">
            <template #default="{ row }">
              <el-input-number
                :model-value="monthOf(row, ym)?.issue_qty ?? 0"
                :min="0"
                :step="1"
                :controls="false"
                size="small"
                class="lqm-num lqm-num--issue"
                :disabled="!canEdit"
                @update:model-value="(v: number | undefined) => onIssueChange(row, ym, v)"
              />
            </template>
          </el-table-column>
          <el-table-column label="発行済" width="88" align="right">
            <template #default="{ row }">
              <el-input-number
                :model-value="monthOf(row, ym)?.issued_qty ?? 0"
                :min="0"
                :step="1"
                :controls="false"
                size="small"
                class="lqm-num lqm-num--issued"
                :disabled="!canEdit"
                @update:model-value="(v: number | undefined) => onIssuedChange(row, ym, v)"
              />
            </template>
          </el-table-column>
          <el-table-column label="月末理論" width="84" align="right">
            <template #default="{ row }">
              <span
                class="lqm-num-close"
                :class="{ 'lqm-num-close--neg': (monthOf(row, ym)?.closing_theory ?? 0) < 0 }"
              >
                {{ formatClosing(monthOf(row, ym)) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="判定" width="64" align="center">
            <template #default="{ row }">
              <span v-if="monthOf(row, ym)?.unit_qty_missing || row.unit_qty_missing" class="lqm-status lqm-status--warn">入数</span>
              <span v-else-if="monthOf(row, ym)?.is_sufficient" class="lqm-status lqm-status--ok">OK</span>
              <span v-else class="lqm-status lqm-status--ng">不足</span>
            </template>
          </el-table-column>
        </el-table-column>

        <el-table-column label="最終発行・印刷履歴" min-width="150" fixed="right">
          <template #default="{ row }">
            <el-input
              v-model="row.last_issue_history"
              size="small"
              maxlength="255"
              placeholder="例: 2026-07-01 印刷"
              :disabled="!canEdit"
              @input="markProductDirty(row)"
            />
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import dayjs from 'dayjs'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Check, DataAnalysis, Refresh } from '@element-plus/icons-vue'
import {
  calcClosingTheory,
  fetchLabelQuantityList,
  fillLabelQuantityIssueQty,
  recalculateLabelQuantity,
  saveLabelQuantityBatch,
  type LabelQuantityKpi,
  type LabelQuantityMonthSnap,
  type LabelQuantityRow,
  type LabelQuantityType,
} from '@/api/master/labelQuantity'
import { useMasterOperationPermission } from '@/composables/useMasterOperationPermission'
import { guardMasterOperation } from '@/utils/masterOperationGuard'

const { canEdit } = useMasterOperationPermission()

const startMonth = ref(dayjs().format('YYYY-MM'))
const monthsCount = ref(1)
const labelType = ref<LabelQuantityType>('molding')
const filters = reactive({ keyword: '', sufficiency: 'all' })
const loading = ref(false)
const saving = ref(false)
const filling = ref(false)
const recalcLoading = ref(false)
const list = ref<LabelQuantityRow[]>([])
const monthKeys = ref<string[]>([])
const safetyFactor = ref(1.1)
const labelsPerSheet = ref(6)
const dirtyKeys = ref<Set<string>>(new Set())

const kpi = reactive<LabelQuantityKpi>({
  total: 0,
  sufficient: 0,
  insufficient: 0,
  unit_qty_missing: 0,
  shortage_qty_sum: 0,
  issue_qty_sum: 0,
  issued_qty_sum: 0,
  opening_stock_sum: 0,
  required_qty_sum: 0,
  demand_units_sum: 0,
  closing_theory_sum: 0,
})

const dirtyCount = computed(() => dirtyKeys.value.size)
const labelTypeLabel = computed(() => (labelType.value === 'molding' ? '成型用' : '製品用'))

function formatNum(n: number | null | undefined) {
  if (n == null || Number.isNaN(Number(n))) return '—'
  return Number(n).toLocaleString()
}

function monthLabel(ym: string) {
  const [, m] = ym.split('-')
  return `${Number(m)}月`
}

function monthOf(row: LabelQuantityRow, ym: string): LabelQuantityMonthSnap | undefined {
  return (row.months || []).find((m) => m.year_month === ym)
}

function ensureMonth(row: LabelQuantityRow, ym: string): LabelQuantityMonthSnap {
  let m = monthOf(row, ym)
  if (!m) {
    m = {
      year_month: ym,
      demand_units: 0,
      opening_stock: 0,
      issue_qty: 0,
      issued_qty: 0,
      shortage_qty: 0,
      is_sufficient: false,
      opening_locked: false,
    }
    row.months = [...(row.months || []), m]
  }
  return m
}

function formatClosing(m?: LabelQuantityMonthSnap) {
  if (!m || m.closing_theory == null) return '—'
  return formatNum(m.closing_theory)
}

function refreshMonthDerived(row: LabelQuantityRow, ym: string) {
  const m = ensureMonth(row, ym)
  const required = m.required_qty
  m.shortage_qty =
    required == null ? 0 : Math.max(0, Number(required) - Number(m.opening_stock || 0))
  m.is_sufficient =
    !row.unit_qty_missing && required != null && Number(m.opening_stock || 0) >= Number(required)
  m.closing_theory = calcClosingTheory(m.opening_stock, m.issued_qty ?? 0, required)
  m.issue_labels = Math.max(0, Number(m.issue_qty) || 0) * labelsPerSheet.value
  // 後続月の未ロック月初を連鎖プレビュー
  cascadePreview(row)
  recomputeLocalKpi()
}

function cascadePreview(row: LabelQuantityRow) {
  const months = [...(row.months || [])].sort((a, b) => a.year_month.localeCompare(b.year_month))
  for (let i = 1; i < months.length; i++) {
    const prev = months[i - 1]
    const cur = months[i]
    if (!cur.opening_locked && prev.closing_theory != null) {
      cur.opening_stock = Number(prev.closing_theory)
      const required = cur.required_qty
      cur.shortage_qty =
        required == null ? 0 : Math.max(0, Number(required) - Number(cur.opening_stock || 0))
      cur.is_sufficient =
        !row.unit_qty_missing && required != null && Number(cur.opening_stock || 0) >= Number(required)
      cur.closing_theory = calcClosingTheory(cur.opening_stock, cur.issued_qty ?? 0, required)
    }
  }
  row.months = months
}

function markProductDirty(row: LabelQuantityRow) {
  dirtyKeys.value = new Set(dirtyKeys.value).add(row.product_cd)
}

function onOpeningChange(row: LabelQuantityRow, ym: string, v: number | undefined) {
  const m = ensureMonth(row, ym)
  m.opening_stock = Number(v) || 0
  m.opening_locked = true
  markProductDirty(row)
  refreshMonthDerived(row, ym)
}

function unlockOpening(row: LabelQuantityRow, ym: string) {
  const m = ensureMonth(row, ym)
  m.opening_locked = false
  markProductDirty(row)
  cascadePreview(row)
  recomputeLocalKpi()
}

function onIssueChange(row: LabelQuantityRow, ym: string, v: number | undefined) {
  const m = ensureMonth(row, ym)
  m.issue_qty = Math.max(0, Number(v) || 0)
  markProductDirty(row)
  refreshMonthDerived(row, ym)
}

function onIssuedChange(row: LabelQuantityRow, ym: string, v: number | undefined) {
  const m = ensureMonth(row, ym)
  m.issued_qty = Math.max(0, Number(v) || 0)
  markProductDirty(row)
  refreshMonthDerived(row, ym)
}

function recomputeLocalKpi() {
  const rows = list.value
  kpi.total = rows.length
  kpi.sufficient = rows.filter((r) => (r.months || []).every((m) => m.is_sufficient)).length
  kpi.insufficient = rows.length - kpi.sufficient
  kpi.unit_qty_missing = rows.filter((r) => r.unit_qty_missing).length
  const snaps = rows.flatMap((r) => r.months || [])
  kpi.shortage_qty_sum = snaps.reduce((s, m) => s + (Number(m.shortage_qty) || 0), 0)
  kpi.issue_qty_sum = snaps.reduce((s, m) => s + (Number(m.issue_qty) || 0), 0)
  kpi.issued_qty_sum = snaps.reduce((s, m) => s + (Number(m.issued_qty) || 0), 0)
  kpi.opening_stock_sum = snaps.reduce((s, m) => s + (Number(m.opening_stock) || 0), 0)
  kpi.required_qty_sum = snaps.reduce(
    (s, m) => s + (m.required_qty == null ? 0 : Number(m.required_qty)),
    0
  )
  kpi.demand_units_sum = snaps.reduce((s, m) => s + (Number(m.demand_units) || 0), 0)
  kpi.closing_theory_sum = snaps.reduce(
    (s, m) => s + (m.closing_theory == null ? 0 : Number(m.closing_theory)),
    0
  )
}

function normalizeRow(r: LabelQuantityRow): LabelQuantityRow {
  const months = (r.months && r.months.length
    ? r.months
    : [
        {
          year_month: r.year_month || startMonth.value,
          demand_units: r.demand_units || 0,
          required_qty: r.required_qty,
          opening_stock: r.opening_stock || 0,
          opening_locked: !!r.opening_locked,
          shortage_qty: r.shortage_qty || 0,
          issue_qty: r.issue_qty || 0,
          issued_qty: r.issued_qty || 0,
          closing_theory: r.closing_theory,
          is_sufficient: !!r.is_sufficient,
        },
      ]
  ).map((m) => ({
    ...m,
    opening_stock: Number(m.opening_stock) || 0,
    issue_qty: Number(m.issue_qty) || 0,
    issued_qty: Number(m.issued_qty) || 0,
    opening_locked: !!m.opening_locked,
  }))
  return {
    ...r,
    last_issue_history: r.last_issue_history ?? '',
    months,
  }
}

function applyResponse(data: {
  list?: LabelQuantityRow[]
  products?: LabelQuantityRow[]
  kpi?: LabelQuantityKpi
  safety_factor?: number
  labels_per_sheet?: number
  month_keys?: string[]
  start_month?: string
  months_count?: number
}) {
  const raw = data.products?.length ? data.products : data.list || []
  list.value = raw.map(normalizeRow)
  monthKeys.value = data.month_keys?.length
    ? data.month_keys
    : list.value[0]?.months?.map((m) => m.year_month) || [startMonth.value]
  if (data.kpi) Object.assign(kpi, data.kpi)
  if (data.safety_factor != null) safetyFactor.value = data.safety_factor
  if (data.labels_per_sheet != null) labelsPerSheet.value = data.labels_per_sheet
  if (data.months_count != null) monthsCount.value = data.months_count
  dirtyKeys.value = new Set()
  recomputeLocalKpi()
}

function rowClassName({ row }: { row: LabelQuantityRow }) {
  if (dirtyKeys.value.has(row.product_cd)) return 'lqm-row--dirty'
  if (row.unit_qty_missing) return 'lqm-row--warn'
  if ((row.months || []).some((m) => !m.is_sufficient)) return 'lqm-row--ng'
  return ''
}

/** 未保存があれば先に保存してから再読込（月初などの入力を消さない） */
async function loadList() {
  if (dirtyCount.value > 0 && canEdit.value) {
    const ok = await persistDirty({ silent: true })
    if (!ok) return
  }
  loading.value = true
  try {
    const res = await fetchLabelQuantityList({
      start_month: startMonth.value,
      months: monthsCount.value,
      label_type: labelType.value,
      keyword: filters.keyword || undefined,
      sufficiency: filters.sufficiency === 'all' ? undefined : filters.sufficiency,
    })
    applyResponse(res as any)
  } catch (e: any) {
    console.error(e)
    ElMessage.error(e?.response?.data?.detail || e?.message || '一覧の取得に失敗しました')
  } finally {
    loading.value = false
  }
}

async function persistDirty(opts?: { silent?: boolean }): Promise<boolean> {
  if (!guardMasterOperation(canEdit)) return false
  const dirty = list.value.filter((r) => dirtyKeys.value.has(r.product_cd))
  if (!dirty.length) {
    if (!opts?.silent) ElMessage.info('変更がありません')
    return true
  }
  const items = dirty.flatMap((r) =>
    (r.months || []).map((m) => ({
      product_cd: r.product_cd,
      year_month: m.year_month,
      opening_stock: Number(m.opening_stock) || 0,
      issue_qty: Math.max(0, Number(m.issue_qty) || 0),
      issued_qty: Math.max(0, Number(m.issued_qty) || 0),
      opening_locked: !!m.opening_locked,
      last_issue_history: r.last_issue_history || null,
    }))
  )
  saving.value = true
  try {
    const res = await saveLabelQuantityBatch({
      label_type: labelType.value,
      start_month: startMonth.value,
      months: monthsCount.value,
      items,
    })
    if (!opts?.silent) {
      ElMessage.success((res as any)?.message || '保存しました')
      applyResponse(res as any)
    } else {
      dirtyKeys.value = new Set()
      ElMessage.success('未保存の変更を保存して再読込します')
    }
    return true
  } catch (e: any) {
    console.error(e)
    ElMessage.error(e?.response?.data?.detail || e?.message || '保存に失敗しました')
    return false
  } finally {
    saving.value = false
  }
}

async function onSave() {
  await persistDirty()
}

async function onFillIssue() {
  if (!guardMasterOperation(canEdit)) return
  try {
    await ElMessageBox.confirm(
      `期間内の発行予定（紙枚数）を CEIL(max(0,必要−発行済)÷${labelsPerSheet.value}) で上書きします。続行しますか？`,
      '紙枚数で埋める',
      { type: 'warning', confirmButtonText: '実行', cancelButtonText: 'キャンセル' }
    )
  } catch {
    return
  }
  filling.value = true
  try {
    const res = await fillLabelQuantityIssueQty({
      start_month: startMonth.value,
      months: monthsCount.value,
      label_type: labelType.value,
    })
    ElMessage.success((res as any)?.message || '更新しました')
    applyResponse(res as any)
  } catch (e: any) {
    console.error(e)
    ElMessage.error(e?.response?.data?.detail || e?.message || '更新に失敗しました')
  } finally {
    filling.value = false
  }
}

async function onRecalculate() {
  if (!guardMasterOperation(canEdit)) return
  try {
    await ElMessageBox.confirm(
      '需要を再取得し、発行紙を更新、未ロック月初へ上月末理論残を書き込みます。手動ロック月初は保持されます。続行しますか？',
      '期間再計算',
      { type: 'warning', confirmButtonText: '実行', cancelButtonText: 'キャンセル' }
    )
  } catch {
    return
  }
  recalcLoading.value = true
  try {
    const res = await recalculateLabelQuantity({
      start_month: startMonth.value,
      months: monthsCount.value,
      label_type: labelType.value,
      fill_issue_qty: true,
    })
    ElMessage.success((res as any)?.message || '再計算しました')
    applyResponse(res as any)
  } catch (e: any) {
    console.error(e)
    ElMessage.error(e?.response?.data?.detail || e?.message || '再計算に失敗しました')
  } finally {
    recalcLoading.value = false
  }
}

onMounted(() => loadList())
</script>

<style scoped lang="scss">
.lqm-page {
  --lqm-accent: #4338ca;
  --lqm-accent-light: #6366f1;
  --lqm-accent-soft: #eef2ff;
  --lqm-hero-grad: linear-gradient(135deg, #312e81 0%, #4338ca 42%, #6366f1 72%, #818cf8 100%);
  display: flex;
  flex-direction: column;
  gap: 6px;
  height: 100%;
  min-height: 0;
  padding: 6px;
  box-sizing: border-box;
  background: linear-gradient(165deg, #f1f5f9 0%, #eef2ff 36%, #f8fafc 100%);
}
.lqm-page--molding {
  --lqm-accent: #0f766e;
  --lqm-accent-light: #14b8a6;
  --lqm-accent-soft: #ecfdf5;
  --lqm-hero-grad: linear-gradient(135deg, #134e4a 0%, #0f766e 42%, #14b8a6 72%, #2dd4bf 100%);
}
.lqm-hero {
  flex-shrink: 0;
  border-radius: 12px;
  padding: 10px 14px;
  background: var(--lqm-hero-grad);
  color: #fff;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.22) inset, 0 8px 22px rgba(67, 56, 202, 0.28);
}
.lqm-hero-inner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  justify-content: space-between;
}
.lqm-title-row {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}
.lqm-title-icon {
  width: 40px;
  height: 40px;
  border-radius: 11px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.28);
}
.lqm-title-line {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.lqm-title {
  margin: 0;
  font-size: 18px;
  font-weight: 800;
}
.lqm-type-pill {
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.3);
}
.lqm-subtitle {
  margin: 3px 0 0;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.84);
}
.lqm-kpi {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.lqm-kpi-card {
  min-width: 72px;
  padding: 6px 10px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.13);
  border: 1px solid rgba(255, 255, 255, 0.22);
  text-align: center;
}
.lqm-kpi-num {
  display: block;
  font-size: 16px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}
.lqm-kpi-lbl {
  font-size: 9px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.76);
}
.lqm-kpi-card--ok {
  background: rgba(34, 197, 94, 0.22);
}
.lqm-kpi-card--ng {
  background: rgba(239, 68, 68, 0.22);
}
.lqm-kpi-card--short {
  background: rgba(251, 146, 60, 0.22);
}
.lqm-kpi-card--issue {
  background: rgba(99, 102, 241, 0.25);
}
.lqm-toolbar-card {
  flex-shrink: 0;
  border-radius: 11px;
  background: #fff;
  border: 1px solid rgba(99, 102, 241, 0.1);
  box-shadow: 0 4px 14px rgba(67, 56, 202, 0.07);
}
.lqm-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 8px;
  padding: 8px 10px;
}
.lqm-filters {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 6px 8px;
  flex: 1;
}
.lqm-filter-field {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.lqm-filter-field--search {
  min-width: 140px;
  max-width: 200px;
  flex: 1;
}
.lqm-field-label {
  font-size: 10px;
  font-weight: 700;
  color: var(--lqm-accent);
}
.lqm-month {
  width: 118px;
}
.lqm-filter {
  width: 110px;
}
.lqm-type-tabs :deep(.el-radio-button__inner) {
  font-weight: 700;
  font-size: 12px;
  padding: 5px 10px;
}
.lqm-type-tabs :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(180deg, var(--lqm-accent-light), var(--lqm-accent));
  border-color: var(--lqm-accent);
  box-shadow: 0 3px 8px rgba(67, 56, 202, 0.25);
}
.lqm-toolbar-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-left: auto;
}
.lqm-btn {
  border-radius: 8px !important;
  font-weight: 700 !important;
  font-size: 12px !important;
}
.lqm-btn--ghost {
  background: linear-gradient(180deg, #fff, #f8fafc) !important;
  border: 1px solid #e2e8f0 !important;
  color: #475569 !important;
}
.lqm-btn--warn {
  color: #fff !important;
  background: linear-gradient(180deg, #fbbf24, #d97706) !important;
  border: none !important;
  box-shadow: 0 3px 0 #b45309, 0 5px 12px rgba(245, 158, 11, 0.35) !important;
}
.lqm-btn--teal {
  color: #fff !important;
  background: linear-gradient(180deg, #2dd4bf, #0f766e) !important;
  border: none !important;
  box-shadow: 0 3px 0 #115e59, 0 5px 12px rgba(15, 118, 110, 0.35) !important;
}
.lqm-btn--primary {
  color: #fff !important;
  background: linear-gradient(180deg, var(--lqm-accent-light), var(--lqm-accent)) !important;
  border: none !important;
  box-shadow: 0 3px 0 #312e81, 0 5px 14px rgba(67, 56, 202, 0.38) !important;
}
.lqm-table-wrap {
  flex: 1;
  min-height: 240px;
  display: flex;
  flex-direction: column;
  border-radius: 12px;
  background: #fff;
  border: 1px solid rgba(99, 102, 241, 0.1);
  box-shadow: 0 6px 20px rgba(67, 56, 202, 0.09);
  overflow: hidden;
}
.lqm-result-bar {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  padding: 6px 10px;
  border-bottom: 1px solid #e2e8f0;
  background: linear-gradient(180deg, #f8fafc, #f1f5f9);
}
.lqm-result-text {
  font-size: 11px;
  font-weight: 600;
  color: #475569;
}
.lqm-result-text strong {
  color: var(--lqm-accent);
  font-size: 13px;
}
.lqm-result-sep {
  margin: 0 6px;
  color: #cbd5e1;
}
.lqm-legend {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
}
.lqm-legend-item {
  padding: 1px 7px;
  border-radius: 999px;
  font-size: 9px;
  font-weight: 700;
  border: 1px solid transparent;
}
.lqm-legend-item--stock {
  background: #ecfdf5;
  color: #047857;
  border-color: #a7f3d0;
}
.lqm-legend-item--demand {
  background: #eef2ff;
  color: #4338ca;
  border-color: #c7d2fe;
}
.lqm-legend-item--issue {
  background: #fff7ed;
  color: #c2410c;
  border-color: #fed7aa;
}
.lqm-legend-item--close {
  background: #f0f9ff;
  color: #0369a1;
  border-color: #bae6fd;
}
.lqm-table {
  flex: 1;
  min-height: 0;
  padding: 0 4px 6px;
}
.lqm-table :deep(.el-table__cell) {
  padding: 3px 0;
  font-size: 11px;
}
.lqm-table :deep(.lqm-month-group--0 .el-table__cell),
.lqm-table :deep(th.lqm-month-group--0) {
  background: rgba(238, 242, 255, 0.35) !important;
}
.lqm-table :deep(.lqm-month-group--1 .el-table__cell),
.lqm-table :deep(th.lqm-month-group--1) {
  background: rgba(236, 253, 245, 0.35) !important;
}
.lqm-table :deep(.lqm-month-group--2 .el-table__cell),
.lqm-table :deep(th.lqm-month-group--2) {
  background: rgba(255, 247, 237, 0.4) !important;
}
.lqm-cd {
  font-family: ui-monospace, monospace;
  font-weight: 700;
  font-size: 11px;
}
.lqm-name {
  font-weight: 600;
}
.lqm-open-cell {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0;
}
.lqm-unlock {
  font-size: 10px !important;
  padding: 0 !important;
  height: auto !important;
}
.lqm-num {
  width: 78px;
}
.lqm-num :deep(.el-input__inner) {
  text-align: right;
  font-variant-numeric: tabular-nums;
  font-weight: 700;
}
.lqm-num--stock :deep(.el-input__inner) {
  color: #047857;
}
.lqm-num--locked :deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px #f59e0b inset !important;
  background: #fffbeb;
}
.lqm-num--issue :deep(.el-input__inner) {
  color: #c2410c;
}
.lqm-num--issued :deep(.el-input__inner) {
  color: #7c3aed;
}
.lqm-num-demand {
  font-weight: 700;
  color: #4338ca;
  font-variant-numeric: tabular-nums;
}
.lqm-num-close {
  font-weight: 800;
  color: #0369a1;
  font-variant-numeric: tabular-nums;
}
.lqm-num-close--neg {
  color: #dc2626;
}
.lqm-cell-warn {
  color: #b45309;
  font-weight: 700;
}
.lqm-status {
  display: inline-flex;
  min-width: 40px;
  justify-content: center;
  padding: 1px 6px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 800;
  border: 1px solid transparent;
}
.lqm-status--ok {
  background: #d1fae5;
  color: #047857;
  border-color: #6ee7b7;
}
.lqm-status--ng {
  background: #fecaca;
  color: #b91c1c;
  border-color: #fca5a5;
}
.lqm-status--warn {
  background: #fde68a;
  color: #b45309;
  border-color: #fcd34d;
}
:deep(.lqm-row--ng) > td {
  background: linear-gradient(90deg, #fff5f5 0%, #fff 35%) !important;
}
:deep(.lqm-row--warn) > td {
  background: linear-gradient(90deg, #fffbeb 0%, #fff 35%) !important;
}
:deep(.lqm-row--dirty) > td {
  box-shadow: inset 3px 0 0 var(--lqm-accent-light);
}
</style>
