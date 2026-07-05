<template>
  <div ref="printRootRef" class="scheduling-page">
    <div class="plan-hd">
      <h2 class="plan-hd-title">
        <span class="plan-hd-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" focusable="false">
            <path
              d="M7 2a1 1 0 0 1 1 1v1h8V3a1 1 0 1 1 2 0v1h1a3 3 0 0 1 3 3v3H2V7a3 3 0 0 1 3-3h1V3a1 1 0 0 1 1-1ZM2 12h20v5a3 3 0 0 1-3 3H5a3 3 0 0 1-3-3v-5Zm6 3a1 1 0 0 0 0 2h2a1 1 0 0 0 0-2H8Zm5 0a1 1 0 1 0 0 2h3a1 1 0 1 0 0-2h-3Z"
            />
          </svg>
        </span>
        <span class="plan-hd-text-wrap">
          <span class="plan-hd-title-text">生産スケジューリングボード</span>
          <span class="plan-hd-sub">工程・ライン・期間で絞り込み、日別の計画と実績をマトリクスで確認。</span>
        </span>
      </h2>
    </div>

    <div class="plan-card filter-card">
      <el-form :inline="true" :model="searchForm" class="filter-form compact-form">
        <el-form-item label="工程">
          <el-select
            v-model="searchForm.processCd"
            clearable
            filterable
            placeholder="全工程"
            style="width: 90px"
            @change="handleProcessChange"
          >
            <el-option
              v-for="p in processOptions"
              :key="p.process_cd"
              :label="String(p.process_name || '').trim() || p.process_cd"
              :value="p.process_cd"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="ライン">
          <el-select
            v-model="searchForm.lineId"
            clearable
            filterable
            placeholder="全ライン"
            style="width: 100px"
          >
            <el-option
              v-for="line in lines"
              :key="line.id"
              :value="line.id"
              :label="String(line.line_name || '').trim() || line.line_code"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="期間" required>
          <el-date-picker
            v-model="searchForm.dateRange"
            type="daterange"
            unlink-panels
            range-separator="~"
            start-placeholder="開始日"
            end-placeholder="終了日"
            value-format="YYYY-MM-DD"
            format="YYYY-MM-DD"
            style="width: 280px"
          />
        </el-form-item>
        <el-form-item label="製品">
          <el-select
            v-model="searchForm.itemName"
            clearable
            filterable
            placeholder="全製品"
            style="width: 220px"
          >
            <el-option v-for="name in schedulingProductOptions" :key="name" :label="name" :value="name" />
          </el-select>
        </el-form-item>
      </el-form>
    </div>

    <div class="stat-grid">
      <div class="stat-card stat-card--lines">
        <span class="stat-card__glow" aria-hidden="true" />
        <span class="stat-card__shine" aria-hidden="true" />
        <span class="stat-label">ライン数</span>
        <span class="stat-value">{{ lineCount }}</span>
      </div>
      <div class="stat-card stat-card--plan">
        <span class="stat-card__glow" aria-hidden="true" />
        <span class="stat-card__shine" aria-hidden="true" />
        <span class="stat-label">生産計画合計</span>
        <span class="stat-value">{{ formatQty(overallPlannedOutputTotal) }}</span>
      </div>
      <div class="stat-card stat-card--efficiency">
        <span class="stat-card__glow" aria-hidden="true" />
        <span class="stat-card__shine" aria-hidden="true" />
        <span class="stat-label">能率(本/H)平均</span>
        <span class="stat-value">{{ formatEfficiency(avgEfficiencyRate) }}</span>
      </div>
      <div class="stat-card stat-card--hours">
        <span class="stat-card__glow" aria-hidden="true" />
        <span class="stat-card__shine" aria-hidden="true" />
        <span class="stat-label">所要生産時間</span>
        <span class="stat-value">{{ formatHours(requiredProductionHours) }}</span>
      </div>
    </div>

    <div class="plan-card result-card" v-loading="loading">
      <div class="result-head">
        <div class="result-title">
          <span class="result-title-feature">{{ matrixTitleFeatureLabel }}</span>
          <span class="result-title-sep" aria-hidden="true">・</span>
          <span class="result-title-main">スケジューリングマトリクス</span>
          <div class="sc-matrix-legend" aria-label="マトリクスセル背景の凡例">
            <span class="sc-legend-item">
              <span class="sc-legend-swatch sc-legend-swatch--actual" aria-hidden="true" />
              <span class="sc-legend-text">実績</span>
            </span>
            <span class="sc-legend-sep" aria-hidden="true">｜</span>
            <span class="sc-legend-item">
              <span class="sc-legend-swatch sc-legend-swatch--cm" aria-hidden="true" />
              <span class="sc-legend-text">切断指示済</span>
            </span>
            <span class="sc-legend-sep" aria-hidden="true">｜</span>
            <span class="sc-legend-item sc-legend-item--plan-toggle">
              <span class="sc-legend-swatch sc-legend-swatch--plan" aria-hidden="true" />
              <span class="sc-legend-text">計画</span>
              <el-tooltip
                :content="
                  matrixPlanExtendMode
                    ? '表示：5日前以前＝実績、それ以降（当日含む）＝計画'
                    : '表示：当日以前＝実績、当日以降＝計画（当日は実績があれば実績）'
                "
                placement="top"
              >
                <el-switch
                  v-model="matrixPlanExtendMode"
                  class="sc-legend-mode-switch"
                  size="small"
                  inline-prompt
                  active-text="拡張"
                  inactive-text="標準"
                  aria-label="マトリクス表示モード切替"
                />
              </el-tooltip>
            </span>
          </div>
        </div>
        <div class="result-head-actions">
          <div class="sc-range-selection-ui result-note sc-range-hint">
            範囲合計：マウスでドラッグして日付セルを選択（{{ rangeSelectionHint }}）
            <template v-if="rangeSelectionSummary">
              <span class="sc-range-sep">｜</span>
              <span class="sc-range-sum-line">
                <span class="sc-range-sum">合計 {{ formatQty(rangeSelectionSummary.itemSum) }}</span>
                <button type="button" class="sc-range-clear-btn" @click.stop="clearMatrixRangeSelection">解除</button>
              </span>
            </template>
            <template v-else-if="matrixRangeDragging">
              <span class="sc-range-sep">｜</span>
              <span class="sc-range-wait">選択中…</span>
            </template>
          </div>
          <div class="result-note result-note--chip">期間：{{ displayDateRangeText }}</div>
          <el-button class="print-btn" size="small" @click="handlePrint">
            <span class="print-btn__content">
              <svg class="print-btn__icon" viewBox="0 0 24 24" focusable="false" aria-hidden="true">
                <path
                  d="M7 2a2 2 0 0 0-2 2v3h14V4a2 2 0 0 0-2-2H7Zm12 7H5a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7a2 2 0 0 0-2-2Zm-2 9H7v-5h10v5Z"
                />
              </svg>
              <span>印刷</span>
            </span>
          </el-button>
        </div>
      </div>

      <el-empty v-if="!loading && gridDates.length === 0" description="期間を指定して検索してください" />

      <div
        v-else
        class="matrix-table-wrapper modern-scroll"
        :class="{ 'is-range-dragging': matrixRangeDragging }"
      >
        <table class="matrix-table">
          <thead>
            <tr>
              <th class="sc-sticky-col sc-line-col">ライン</th>
              <th class="sc-sticky-col sc-order-col">順位</th>
              <th class="sc-sticky-col sc-item-col">製品</th>
              <th class="sc-sticky-col sc-eff-col numeric-cell">能率(本/H)</th>
              <th class="sc-sticky-col sc-total-col numeric-cell">生産計画</th>
              <th
                v-for="col in dateColumnMeta"
                :key="col.date"
                class="date-col"
                :class="{ 'is-weekend': col.isWeekend, 'is-today': col.isToday }"
              >
                <div class="date-header">
                  <div class="date-text">{{ col.dateText }}</div>
                  <div class="weekday-text">{{ col.weekday }}</div>
                </div>
              </th>
            </tr>
          </thead>
          <tbody v-for="section in matrixSections" :key="section.key" class="sc-line-section">
            <tr
              v-for="row in section.rows"
              :key="row.key"
              :class="[
                row.type === 'group' ? 'sc-group-header-row' : 'sc-item-row',
                row.type === 'item' && row.material_shortage ? 'sc-material-shortage-row' : '',
              ]"
            >
              <td class="sc-sticky-col sc-line-col">
                <div class="sc-line-cell">
                  <span class="sc-line-code">{{ row.type === 'group' ? row.line_name : '' }}</span>
                </div>
              </td>
              <td class="sc-sticky-col sc-order-col numeric-cell">
                {{ row.type === 'item' ? (row.order_no ?? '-') : '' }}
              </td>
              <td class="sc-sticky-col sc-item-col">
                <div class="sc-item-cell">
                  <div class="sc-item-name">{{ row.type === 'item' ? row.item_name : '' }}</div>
                  <div v-if="row.type === 'item' && row.material_shortage" class="sc-flag">資材不足</div>
                </div>
              </td>
              <td class="sc-sticky-col sc-eff-col numeric-cell">
                {{ formatEfficiency(row.type === 'item' ? row.efficiency_rate : row.avg_efficiency) }}
              </td>
              <td class="sc-sticky-col sc-total-col numeric-cell">
                {{ formatQty(row.type === 'item' ? row.planned_output_qty : row.sum_planned_output_qty) }}
              </td>
              <td
                v-for="date in gridDates"
                :key="`${row.key}-${date}`"
                class="numeric-cell data-cell sc-selectable-cell"
                :class="getMatrixCellClasses(row, date)"
                :style="getMatrixCellStyle(row, date)"
                :title="getMatrixCellNativeTitle(row, date)"
                role="button"
                tabindex="0"
                @mousedown.prevent="onMatrixDateCellMouseDown(row, date, $event)"
                @mouseenter="onMatrixCellMouseEnter(row, date, $event)"
                @mouseleave="onMatrixCellMouseLeave"
              >
                <span v-if="row.type === 'item' && getMatrixCellDisplayValue(row, date)">
                  {{ getMatrixCellDisplayText(row, date) }}
                </span>
              </td>
            </tr>
          </tbody>
          <tfoot>
            <tr class="sc-total-footer-row">
              <td class="sc-sticky-col sc-line-col">合計</td>
              <td class="sc-sticky-col sc-order-col" />
              <td class="sc-sticky-col sc-item-col" />
              <td class="sc-sticky-col sc-eff-col" />
              <td class="sc-sticky-col sc-total-col numeric-cell">{{ formatQty(overallPlannedOutputTotal) }}</td>
              <td v-for="date in gridDates" :key="`total-${date}`" class="numeric-cell">
                {{ formatQty(overallDailyTotals[date] || 0) }}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>

    <Teleport to="body">
      <div
        v-if="attribTooltip.visible"
        class="sc-attrib-tooltip"
        :style="{ left: `${attribTooltip.x}px`, top: `${attribTooltip.y}px` }"
        @mouseenter="onAttribTooltipMouseEnter"
        @mouseleave="onMatrixCellMouseLeave"
      >
        <div class="sc-attrib-tooltip__head">
          <span class="sc-attrib-tooltip__title">内示帰属</span>
          <span v-if="attribTooltip.managementCode" class="sc-attrib-tooltip__code sc-attrib-tooltip__code--head">
            {{ attribTooltip.managementCode }}
          </span>
        </div>
        <div v-if="attribTooltip.loading" class="sc-attrib-tooltip__loading">読込中…</div>
        <div v-else-if="!attribTooltip.rows.length" class="sc-attrib-tooltip__empty">帰属データなし</div>
        <table v-else class="sc-attrib-tooltip__table">
          <thead>
            <tr>
              <th>製品名</th>
              <th>納入先</th>
              <th>出荷日</th>
              <th>帰属数</th>
              <th>生産日</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(ar, idx) in attribTooltip.rows" :key="`${ar.management_code}-${ar.destination_cd}-${idx}`">
              <td>{{ ar.product_name || ar.product_cd || '—' }}</td>
              <td>{{ ar.destination_name || '—' }}</td>
              <td class="sc-attrib-tooltip__ship">{{ formatAttribDate(ar.forecast_attribution_date) }}</td>
              <td class="sc-attrib-tooltip__num">{{ formatQty(ar.attributed_qty ?? 0) }}</td>
              <td>{{ formatAttribDate(ar.source_date) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import dayjs from 'dayjs'
import { computed, onMounted, onUnmounted, reactive, ref, shallowRef, watch } from 'vue'
import { fetchProcesses } from '@/api/master/processMaster'
import type { ProcessItem } from '@/types/master'
import {
  fetchLines,
  fetchSchedulingGrid,
  type DailyManagementCodeAlloc,
  type DailyUpstreamTintSeg,
  type LineGridBlock,
  type ProductionLine,
  type ScheduleGridRow,
  type SchedulingGridResponse,
} from '@/api/aps'
import {
  lookupAttributionByManagementCode,
  type LotForecastAttributionRow,
} from '@/api/lotForecastAttribution'
import { useApsOperationPermission } from '@/composables/useApsOperationPermission'
import { guardApsOperation } from '@/utils/apsOperationGuard'

const { canExport } = useApsOperationPermission()

type MatrixGroupRow = {
  key: string
  type: 'group'
  line_id: number
  line_code: string
  line_name: string
  utilization_rate?: number | null
  sum_planned_output_qty: number
  daily_totals: Record<string, number>
  sum_adjust_qty: number
  sum_setup_time: number
  avg_efficiency?: number | null
}

type MatrixItemRow = {
  key: string
  type: 'item'
  line_id: number
  line_code: string
  line_name: string
  order_no?: number | null
  item_name: string
  material_shortage: boolean
  adjust_qty: number
  material_date?: string | null
  setup_time: number
  efficiency_rate: number
  planned_output_qty: number
  completion_rate?: number | null
  due_date?: string | null
  daily: Record<string, number>
  /** schedule_details.actual_qty 日別（実績） */
  actual_daily?: Record<string, number>
  /** aps_batch_plans がある日セル：ロット別上流状態をスライス按分で合成（背景は inline style） */
  has_aps_batch_plans?: boolean
  daily_upstream_tint?: Record<string, DailyUpstreamTintSeg>
  /** 日別管理コード（buildMatrixRows で事前解決） */
  management_code_by_date?: Record<string, string>
  daily_management_codes?: Record<string, DailyManagementCodeAlloc[]>
}

type MatrixRow = MatrixGroupRow | MatrixItemRow

const processOptions = ref<ProcessItem[]>([])
const lines = ref<ProductionLine[]>([])
const grid = shallowRef<SchedulingGridResponse | null>(null)
const loading = ref(false)
const printRootRef = ref<HTMLElement | null>(null)
/** false=標準（当日以前実績）、true=拡張（5日前以前実績・それ以降計画） */
const matrixPlanExtendMode = ref(false)

const searchForm = reactive<{
  processCd: string
  dateRange: [string, string]
  lineId: number | null
  itemName: string | null
}>({
  processCd: 'KT04',
  dateRange: [dayjs().subtract(1, 'day').format('YYYY-MM-DD'), dayjs().add(30, 'day').format('YYYY-MM-DD')],
  lineId: null,
  itemName: null,
})

const gridDates = computed(() => grid.value?.dates ?? [])

const lineNameById = computed(() => {
  const m = new Map<number, string>()
  for (const line of lines.value) {
    m.set(line.id, String(line.line_name || '').trim() || line.line_code)
  }
  return m
})

const dateColumnMeta = computed(() =>
  gridDates.value.map((date) => ({
    date,
    dateText: formatMatrixDate(date),
    weekday: getWeekdayLabel(date),
    isWeekend: isWeekend(date),
    isToday: isToday(date),
  })),
)

const visibleBlocks = computed(() => (grid.value?.blocks ?? []).filter((b) => !isIgnoredLine(resolveLineName(b.line_id, b.line_code))))

/** 当前网格中的品名（忽略已隐藏ライン），供製品下拉使用 */
const schedulingProductOptions = computed(() => {
  const names = new Set<string>()
  for (const b of visibleBlocks.value) {
    for (const r of b.rows ?? []) {
      const n = String(r.item_name || '').trim()
      if (n) names.add(n)
    }
  }
  return [...names].sort((a, b) => a.localeCompare(b, 'ja'))
})

/** 按製品筛选后的块；并重算日计与合計以便矩阵与统计一致 */
const displayBlocks = computed<LineGridBlock[]>(() => {
  const blocks = visibleBlocks.value
  const dates = gridDates.value
  const needle = (searchForm.itemName || '').trim()
  if (!needle) return blocks

  const out: LineGridBlock[] = []
  for (const block of blocks) {
    const rows = (block.rows ?? []).filter((r) => String(r.item_name || '').trim() === needle)
    if (!rows.length) continue

    const daily_totals: Record<string, number> = {}
    for (const d of dates) daily_totals[d] = 0
    let sum_planned_output_qty = 0
    let sum_planned_process_qty = 0
    for (const r of rows) {
      sum_planned_output_qty += Number(r.planned_output_qty ?? 0)
      sum_planned_process_qty += Number(r.planned_process_qty ?? 0)
      for (const d of dates) {
        daily_totals[d] =
          (daily_totals[d] ?? 0) +
          matrixCellDisplayQty((r.daily ?? {}) as Record<string, number>, (r.actual_daily ?? {}) as Record<string, number>, d)
      }
    }
    out.push({
      ...block,
      rows,
      daily_totals,
      sum_planned_output_qty,
      sum_planned_process_qty,
    })
  }
  return out
})

const matrixRows = computed<MatrixRow[]>(() => {
  if (!grid.value) return []
  return buildMatrixRows(displayBlocks.value)
})
const matrixSections = computed(() => {
  const sections: Array<{ key: string; rows: MatrixRow[] }> = []
  let currentRows: MatrixRow[] = []
  let currentKey = ''

  matrixRows.value.forEach((row) => {
    if (row.type === 'group') {
      if (currentRows.length) sections.push({ key: currentKey, rows: currentRows })
      currentKey = row.key
      currentRows = [row]
      return
    }
    if (currentRows.length === 0) {
      currentKey = row.key
    }
    currentRows.push(row)
  })

  if (currentRows.length) sections.push({ key: currentKey, rows: currentRows })
  return sections
})

/** マトリクス行キー → 表示順インデックス（範囲選択用） */
const matrixRowIndexByKey = computed(() => {
  const m = new Map<string, number>()
  matrixRows.value.forEach((r, i) => m.set(r.key, i))
  return m
})

type MatrixCellRenderEntry = {
  displayValue: number
  displayText: string
  toneClass: string
  upstreamStyle?: Record<string, string>
  title: string
}

/** 日付セルの表示情報を一括計算（再レンダリング時の重複計算を削減） */
const matrixCellRenderCache = computed(() => {
  void matrixPlanExtendMode.value
  const cache = new Map<string, MatrixCellRenderEntry>()
  const dates = gridDates.value
  const rows = matrixRows.value
  for (const row of rows) {
    for (const date of dates) {
      const displayValue = getCellDisplayValue(row, date)
      cache.set(`${row.key}-${date}`, {
        displayValue,
        displayText: displayValue ? formatQty(displayValue) : '',
        toneClass: getCellToneClass(row, date, displayValue),
        upstreamStyle: getCellUpstreamStyle(row, date),
        title: getCellTitle(row, date, displayValue),
      })
    }
  }
  return cache
})

function getMatrixCellEntry(row: MatrixRow, date: string): MatrixCellRenderEntry | undefined {
  return matrixCellRenderCache.value.get(`${row.key}-${date}`)
}

function getMatrixCellDisplayValue(row: MatrixRow, date: string): number {
  return getMatrixCellEntry(row, date)?.displayValue ?? 0
}

function getMatrixCellDisplayText(row: MatrixRow, date: string): string {
  return getMatrixCellEntry(row, date)?.displayText ?? ''
}

function getMatrixCellStyle(row: MatrixRow, date: string): Record<string, string> | undefined {
  return getMatrixCellEntry(row, date)?.upstreamStyle
}

function getMatrixCellTitle(row: MatrixRow, date: string): string {
  return getMatrixCellEntry(row, date)?.title ?? ''
}

function getMatrixCellNativeTitle(row: MatrixRow, date: string): string {
  if (row.type === 'item' && getCellManagementCode(row, date)) return ''
  return getMatrixCellTitle(row, date)
}

const attribTooltip = reactive({
  visible: false,
  x: 0,
  y: 0,
  loading: false,
  managementCode: '',
  rows: [] as LotForecastAttributionRow[],
})
const ATTRIB_HOVER_DELAY_MS = 180
const attribCache = new Map<string, LotForecastAttributionRow[]>()
const attribInflight = new Map<string, Promise<LotForecastAttributionRow[]>>()
let attribHoverTimer: ReturnType<typeof setTimeout> | null = null
let attribHideTimer: ReturnType<typeof setTimeout> | null = null
let attribFetchToken = 0
let attribTooltipHovered = false

function buildManagementCodeByDate(
  daily: Record<string, DailyManagementCodeAlloc[]> | undefined,
): Record<string, string> {
  const out: Record<string, string> = {}
  if (!daily) return out
  for (const [date, list] of Object.entries(daily)) {
    const mc = String(list[0]?.management_code ?? '').trim()
    if (mc) out[date] = mc
  }
  return out
}

function getCellManagementCode(row: MatrixRow, date: string): string {
  if (row.type !== 'item') return ''
  return String(row.management_code_by_date?.[date] ?? '').trim()
}

async function fetchAttributionRows(managementCode: string): Promise<LotForecastAttributionRow[]> {
  const cached = attribCache.get(managementCode)
  if (cached) return cached

  const inflight = attribInflight.get(managementCode)
  if (inflight) return inflight

  const task = lookupAttributionByManagementCode(managementCode, 'molding')
    .then((res) => {
      const rows = res.data ?? []
      attribCache.set(managementCode, rows)
      return rows
    })
    .finally(() => {
      attribInflight.delete(managementCode)
    })
  attribInflight.set(managementCode, task)
  return task
}

function formatAttribDate(value?: string | null): string {
  if (!value) return '—'
  return String(value).slice(0, 10)
}

function positionAttribTooltip(ev: MouseEvent) {
  const pad = 12
  const width = 520
  const height = 280
  let x = ev.clientX + 14
  let y = ev.clientY + 14
  if (x + width > window.innerWidth - pad) x = ev.clientX - width - 14
  if (y + height > window.innerHeight - pad) y = Math.max(pad, ev.clientY - height - 8)
  attribTooltip.x = Math.max(pad, x)
  attribTooltip.y = Math.max(pad, y)
}

function hideAttribTooltip() {
  attribTooltip.visible = false
  attribTooltip.loading = false
  attribTooltip.managementCode = ''
  attribTooltip.rows = []
}

function onAttribTooltipMouseEnter() {
  attribTooltipHovered = true
  if (attribHideTimer) {
    clearTimeout(attribHideTimer)
    attribHideTimer = null
  }
}

async function loadAttribTooltip(managementCode: string, ev: MouseEvent) {
  const token = ++attribFetchToken
  attribTooltip.visible = true
  attribTooltip.managementCode = managementCode
  positionAttribTooltip(ev)

  const cached = attribCache.get(managementCode)
  if (cached) {
    attribTooltip.loading = false
    attribTooltip.rows = cached
    return
  }

  attribTooltip.loading = true
  attribTooltip.rows = []
  try {
    const rows = await fetchAttributionRows(managementCode)
    if (token !== attribFetchToken) return
    attribTooltip.rows = rows
  } catch (e) {
    console.error('内示帰属の取得に失敗:', e)
    if (token === attribFetchToken) attribTooltip.rows = []
  } finally {
    if (token === attribFetchToken) attribTooltip.loading = false
  }
}

function onMatrixCellMouseEnter(row: MatrixRow, date: string, ev: MouseEvent) {
  onMatrixDateCellMouseEnter(row, date)
  if (attribHideTimer) {
    clearTimeout(attribHideTimer)
    attribHideTimer = null
  }
  if (row.type !== 'item') return
  const managementCode = getCellManagementCode(row, date)
  if (!managementCode) {
    if (!attribTooltipHovered) hideAttribTooltip()
    return
  }
  if (attribHoverTimer) clearTimeout(attribHoverTimer)
  if (attribCache.has(managementCode)) {
    void loadAttribTooltip(managementCode, ev)
    return
  }
  attribHoverTimer = setTimeout(() => {
    void loadAttribTooltip(managementCode, ev)
  }, ATTRIB_HOVER_DELAY_MS)
}

function onMatrixCellMouseLeave() {
  if (attribHoverTimer) {
    clearTimeout(attribHoverTimer)
    attribHoverTimer = null
  }
  attribTooltipHovered = false
  attribHideTimer = setTimeout(() => {
    hideAttribTooltip()
  }, 180)
}

function getMatrixCellClasses(row: MatrixRow, date: string): string | string[] {
  const tone = getMatrixCellEntry(row, date)?.toneClass ?? ''
  const extra: string[] = []
  if (isMatrixCellInRangeSelection(row, date)) extra.push('sc-range-selected')
  if (isMatrixRangeAnchorCell(row, date)) extra.push('sc-range-anchor')
  if (row.type === 'item' && getCellManagementCode(row, date)) {
    extra.push('sc-cell-has-attrib')
  }
  if (!extra.length) return tone
  if (!tone) return extra
  return [tone, ...extra]
}

type MatrixRangeCell = { rowKey: string; date: string }
const matrixRangeStart = ref<MatrixRangeCell | null>(null)
const matrixRangeEnd = ref<MatrixRangeCell | null>(null)
const matrixRangeDragging = ref(false)

const matrixRangeAnchor = computed(() => matrixRangeStart.value)

const rangeSelectionHint = 'Esc 解除可'

const matrixRangeBounds = computed(() => {
  const s = matrixRangeStart.value
  const e = matrixRangeEnd.value
  if (!s) return null
  const dates = gridDates.value
  const rows = matrixRowIndexByKey.value
  const ri0 = rows.get(s.rowKey)
  const di0 = dates.indexOf(s.date)
  if (ri0 == null || ri0 < 0 || di0 < 0) return null
  if (!e) return { rmin: ri0, rmax: ri0, dmin: di0, dmax: di0 }
  const ri1 = rows.get(e.rowKey)
  const di1 = dates.indexOf(e.date)
  if (ri1 == null || ri1 < 0 || di1 < 0) return null
  return {
    rmin: Math.min(ri0, ri1),
    rmax: Math.max(ri0, ri1),
    dmin: Math.min(di0, di1),
    dmax: Math.max(di0, di1),
  }
})

/** 品目行のみ合算（ライン合計行を混ぜると二重計上になるため） */
const rangeSelectionSummary = computed(() => {
  const b = matrixRangeBounds.value
  const e = matrixRangeEnd.value
  if (!b || !e) return null
  const dates = gridDates.value
  const rows = matrixRows.value
  let itemSum = 0
  let itemCells = 0
  for (let ri = b.rmin; ri <= b.rmax; ri++) {
    const row = rows[ri]
    if (!row || row.type !== 'item') continue
    for (let di = b.dmin; di <= b.dmax; di++) {
      const date = dates[di]
      if (!date) continue
      itemCells += 1
      itemSum += getMatrixCellDisplayValue(row, date)
    }
  }
  return { itemSum, itemCells }
})

function clearMatrixRangeSelection() {
  matrixRangeStart.value = null
  matrixRangeEnd.value = null
  matrixRangeDragging.value = false
}

function onMatrixDateCellMouseDown(row: MatrixRow, date: string, ev: MouseEvent) {
  if (ev.button !== 0) return
  const pos: MatrixRangeCell = { rowKey: row.key, date }
  matrixRangeStart.value = pos
  matrixRangeEnd.value = pos
  matrixRangeDragging.value = true
}

function onMatrixDateCellMouseEnter(row: MatrixRow, date: string) {
  if (!matrixRangeDragging.value) return
  matrixRangeEnd.value = { rowKey: row.key, date }
}

function onMatrixRangeMouseUp() {
  matrixRangeDragging.value = false
}

function isMatrixCellInRangeSelection(row: MatrixRow, date: string): boolean {
  const b = matrixRangeBounds.value
  if (!b) return false
  const ri = matrixRowIndexByKey.value.get(row.key)
  const di = gridDates.value.indexOf(date)
  if (ri == null || ri < 0 || di < 0) return false
  return ri >= b.rmin && ri <= b.rmax && di >= b.dmin && di <= b.dmax
}

function isMatrixRangeAnchorCell(row: MatrixRow, date: string): boolean {
  const s = matrixRangeStart.value
  const e = matrixRangeEnd.value
  if (!s) return false
  const hit = (p: MatrixRangeCell) => p.rowKey === row.key && p.date === date
  if (hit(s)) return true
  if (e && hit(e)) return true
  return false
}

function onMatrixRangeEscape(ev: KeyboardEvent) {
  if (ev.key !== 'Escape') return
  if (!matrixRangeStart.value) return
  clearMatrixRangeSelection()
}

const lineCount = computed(() => displayBlocks.value.length)

const overallPlannedOutputTotal = computed(() =>
  displayBlocks.value.reduce(
    (acc, b) =>
      acc +
      (b.rows ?? []).reduce(
        (rowAcc, r) =>
          rowAcc +
          gridDates.value.reduce((dateAcc, date) => dateAcc + Number((r.daily ?? {})[date] ?? 0), 0),
        0,
      ),
    0,
  ),
)

const avgEfficiencyRate = computed(() => {
  const blocks = displayBlocks.value
  let weightedSum = 0
  let weightedDenom = 0
  for (const block of blocks) {
    for (const row of block.rows ?? []) {
      const rate = Number(row.efficiency_rate ?? row.efficiency ?? 0)
      const qty = Number(row.planned_process_qty ?? 0)
      if (!Number.isFinite(rate) || !Number.isFinite(qty) || qty <= 0) continue
      weightedSum += rate * qty
      weightedDenom += qty
    }
  }
  if (weightedDenom <= 0) return null
  return weightedSum / weightedDenom
})

const requiredProductionHours = computed(() => {
  const totalQty = Number(overallPlannedOutputTotal.value ?? 0)
  const avgRate = Number(avgEfficiencyRate.value ?? 0)
  if (!Number.isFinite(totalQty) || !Number.isFinite(avgRate) || avgRate <= 0) return null
  return totalQty / avgRate
})

const overallDailyTotals = computed(() => {
  const totals: Record<string, number> = {}
  for (const date of gridDates.value) totals[date] = 0
  for (const block of displayBlocks.value) {
    for (const r of block.rows ?? []) {
      for (const date of gridDates.value) {
        totals[date] += matrixCellDisplayQty(
          (r.daily ?? {}) as Record<string, number>,
          (r.actual_daily ?? {}) as Record<string, number>,
          date,
        )
      }
    }
  }
  return totals
})

const displayDateRangeText = computed(() => {
  const [s, e] = searchForm.dateRange || []
  if (!s || !e) return '-'
  return `${s} ~ ${e}`
})

/** 見出し前段：筛选「工程」と同じ表示名（印刷も result-card 内のため同様に反映） */
const matrixTitleFeatureLabel = computed(() => {
  const cd = (searchForm.processCd || '').trim()
  if (!cd) return '全工程'
  const p = processOptions.value.find((x) => String(x.process_cd || '').trim() === cd)
  const name = String(p?.process_name || '').trim()
  return name || cd
})

function formatQty(v: number) {
  const n = Number(v ?? 0)
  if (!Number.isFinite(n)) return '-'
  return n.toLocaleString()
}

function formatEfficiency(v?: number | null) {
  if (v == null || !Number.isFinite(v)) return '-'
  return v.toFixed(1)
}

function formatHours(v?: number | null) {
  if (v == null || !Number.isFinite(v)) return '-'
  return `${v.toFixed(1)}H`
}

function formatMatrixDate(iso: string) {
  return dayjs(iso).format('MM/DD')
}

function getWeekdayLabel(iso: string) {
  return ['日', '月', '火', '水', '木', '金', '土'][dayjs(iso).day()]
}

function isWeekend(iso: string) {
  const d = dayjs(iso).day()
  return d === 0 || d === 6
}

function isToday(iso: string) {
  return iso === dayjs().format('YYYY-MM-DD')
}

function matrixTodayStr() {
  return dayjs().format('YYYY-MM-DD')
}

/** 実績表示の境界日（この日以前は実績側） */
function matrixActualBoundaryStr() {
  const todayStr = matrixTodayStr()
  if (!matrixPlanExtendMode.value) return todayStr
  return dayjs(todayStr).subtract(5, 'day').format('YYYY-MM-DD')
}

function matrixCellDisplayMode(dateIso: string, actualQty: number): 'actual' | 'plan' {
  const todayStr = matrixTodayStr()
  const boundary = matrixActualBoundaryStr()
  if (matrixPlanExtendMode.value) {
    return dateIso <= boundary ? 'actual' : 'plan'
  }
  if (dateIso < todayStr) return 'actual'
  if (dateIso > todayStr) return 'plan'
  return actualQty > 0 ? 'actual' : 'plan'
}

/** マトリクス日セル：標準=過去実績・当日実績優先・未来計画／拡張=5日前以前実績・以降計画 */
function matrixCellDisplayQty(
  plannedDaily: Record<string, number>,
  actualDaily: Record<string, number> | undefined,
  dateIso: string,
): number {
  const planned = Number(plannedDaily?.[dateIso] ?? 0)
  const actual = Number(actualDaily?.[dateIso] ?? 0)
  return matrixCellDisplayMode(dateIso, actual) === 'actual' ? actual : planned
}

/** 計画本数を表示しているか（上流色分けは計画に対してのみ適用） */
function plannedUpstreamTintActiveForItem(row: MatrixRow, dateIso: string): boolean {
  if (row.type !== 'item') return false
  const actual = Number(row.actual_daily?.[dateIso] ?? 0)
  return matrixCellDisplayMode(dateIso, actual) === 'plan'
}

/** 実績かつ本数>0 のセルのみ浅黄 */
function cellShowsActualDisplay(row: MatrixRow, date: string): boolean {
  if (row.type !== 'item') return false
  const v = getCellDisplayValue(row, date) || 0
  if (v <= 0) return false
  const actual = Number(row.actual_daily?.[date] ?? 0)
  return matrixCellDisplayMode(date, actual) === 'actual'
}

function rowHasPeriodData(r: ScheduleGridRow, dates: string[]): boolean {
  const daily = r.daily ?? {}
  const actual = r.actual_daily ?? {}
  for (const date of dates) {
    if (Number(daily[date] ?? 0) > 0 || Number(actual[date] ?? 0) > 0) return true
  }
  return false
}

function buildMatrixRows(blocks: LineGridBlock[]): MatrixRow[] {
  const rows: MatrixRow[] = []
  const dates = gridDates.value
  blocks.forEach((block: LineGridBlock, blockIndex) => {
    const periodRows = (block.rows ?? []).filter((r) => rowHasPeriodData(r, dates))
    if (!periodRows.length) return

    const groupDisplayTotals: Record<string, number> = {}
    for (const d of dates) groupDisplayTotals[d] = 0
    for (const r of periodRows) {
      for (const d of dates) {
        groupDisplayTotals[d] += matrixCellDisplayQty(
          (r.daily ?? {}) as Record<string, number>,
          (r.actual_daily ?? {}) as Record<string, number>,
          d,
        )
      }
    }

    const lineName = resolveLineName(block.line_id, block.line_code)
    const groupRow: MatrixGroupRow = {
      key: `group-${block.line_id}-${blockIndex}`,
      type: 'group',
      line_id: block.line_id,
      line_code: block.line_code,
      line_name: lineName,
      utilization_rate: null,
      sum_planned_output_qty: block.sum_planned_output_qty ?? 0,
      daily_totals: groupDisplayTotals,
      sum_adjust_qty: 0,
      sum_setup_time: 0,
      avg_efficiency: null,
    }
    rows.push(groupRow)

    let effWeightedSum = 0
    let effWeightedDenom = 0
    let adjustSum = 0
    let setupSum = 0

    periodRows.forEach((r: ScheduleGridRow) => {
      const adjustQty = r.prev_month_carryover ?? 0
      const setupTime = r.setup_time ?? 0
      const efficiencyRate = Number(r.efficiency_rate ?? r.efficiency ?? 0)
      const plannedProcess = r.planned_process_qty ?? 0

      adjustSum += adjustQty
      setupSum += setupTime
      effWeightedSum += efficiencyRate * plannedProcess
      effWeightedDenom += plannedProcess

      rows.push({
        key: `item-${block.line_id}-${r.id}`,
        type: 'item',
        line_id: block.line_id,
        line_code: block.line_code,
        line_name: lineName,
        order_no: r.order_no ?? null,
        item_name: r.item_name,
        material_shortage: !!r.material_shortage,
        adjust_qty: adjustQty,
        material_date: r.material_date ?? null,
        setup_time: setupTime,
        efficiency_rate: efficiencyRate,
        planned_output_qty: r.planned_output_qty ?? 0,
        completion_rate: r.completion_rate ?? null,
        due_date: r.due_date ?? null,
        daily: r.daily ?? {},
        actual_daily: r.actual_daily ?? {},
        has_aps_batch_plans: !!r.has_aps_batch_plans,
        daily_upstream_tint: r.daily_upstream_tint ?? {},
        management_code_by_date: buildManagementCodeByDate(r.daily_management_codes),
        daily_management_codes: r.daily_management_codes ?? {},
      })
    })

    groupRow.sum_adjust_qty = adjustSum
    groupRow.sum_setup_time = setupSum
    groupRow.avg_efficiency = effWeightedDenom > 0 ? effWeightedSum / effWeightedDenom : null
    const availableHours = Object.values(block.calendar ?? {}).reduce((acc, h) => acc + Number(h || 0), 0)
    let plannedHours = 0
    for (const r of periodRows) {
      const qty = Number(r.planned_output_qty ?? 0)
      const rate = Number(r.efficiency_rate ?? r.efficiency ?? 0)
      if (!Number.isFinite(qty) || !Number.isFinite(rate) || rate <= 0) continue
      plannedHours += qty / rate
    }
    groupRow.utilization_rate = availableHours > 0 ? (plannedHours / availableHours) * 100 : null
  })
  return rows
}

function resolveLineName(lineId: number, fallbackCode: string) {
  return lineNameById.value.get(lineId) || fallbackCode
}

function isIgnoredLine(lineName: string) {
  const normalized = lineName.trim()
  return normalized === '成型他' || normalized === 'FM-026'
}

function getCellDisplayValue(row: MatrixRow, date: string): number {
  if (row.type === 'group') return row.daily_totals?.[date] ?? 0
  if (row.type !== 'item') return 0
  return matrixCellDisplayQty(row.daily ?? {}, row.actual_daily, date)
}

function cellUsesUpstreamTintBackground(row: MatrixRow, date: string): boolean {
  if (row.type !== 'item' || row.material_shortage) return false
  if (!row.has_aps_batch_plans) return false
  if (!plannedUpstreamTintActiveForItem(row, date)) return false
  const planned = Number(row.daily?.[date] ?? 0)
  if (planned <= 0) return false
  const seg = row.daily_upstream_tint?.[date]
  if (!seg) return false
  const t = Number(seg.in_cutting ?? 0) + Number(seg.in_instruction ?? 0) + Number(seg.only_planned ?? 0)
  return t > 0
}

function getCellUpstreamStyle(row: MatrixRow, date: string): Record<string, string> | undefined {
  if (!cellUsesUpstreamTintBackground(row, date)) return undefined
  if (row.type !== 'item') return undefined
  const seg = row.daily_upstream_tint?.[date]
  if (!seg) return undefined
  const a = Number(seg.in_cutting ?? 0)
  const b = Number(seg.in_instruction ?? 0)
  const c = Number(seg.only_planned ?? 0)
  const g = b + c
  const t = a + g
  if (t <= 0) return undefined
  const red = 'rgba(254, 202, 202, 0.82)'
  const green = 'rgba(187, 247, 208, 0.62)'
  if (a === t) return { background: red }
  if (a === 0) return { background: green }
  const p1 = (a / t) * 100
  return {
    background: `linear-gradient(to right, ${red} 0%, ${red} ${p1}%, ${green} ${p1}%, ${green} 100%)`,
  }
}

function getCellTitle(row: MatrixRow, date: string, displayValue?: number): string {
  const disp = (displayValue ?? getCellDisplayValue(row, date)) || 0
  if (row.type === 'group') {
    if (!disp) return `${date}: ライン合計なし`
    return `${date}: ライン合計 ${disp}`
  }
  const planned = Number(row.daily?.[date] ?? 0)
  const actual = Number(row.actual_daily?.[date] ?? 0)
  const modeLabel = matrixCellDisplayMode(date, actual) === 'actual' ? '実績' : '計画'
  const seg = row.daily_upstream_tint?.[date]
  const tintSum = seg
    ? Number(seg.in_cutting ?? 0) + Number(seg.in_instruction ?? 0) + Number(seg.only_planned ?? 0)
    : 0
  const cutHint =
    tintSum > 0 && planned > 0 && plannedUpstreamTintActiveForItem(row, date)
      ? ` / CM:${seg!.in_cutting} 指示:${seg!.in_instruction} 計画:${seg!.only_planned}`
      : ''
  if (!disp) return `${date}: ${row.item_name} / —（${modeLabel}）計${planned} 実${actual}${cutHint}`
  return `${date}: ${row.item_name} / ${disp}（${modeLabel}・計${planned}/実${actual}）${cutHint}`
}

function getCellToneClass(row: MatrixRow, date: string, displayValue?: number): string {
  const v = (displayValue ?? getCellDisplayValue(row, date)) || 0
  const dueMatch = row.type === 'item' && row.due_date ? row.due_date === date : false
  const upstreamBg = cellUsesUpstreamTintBackground(row, date)

  if (row.type === 'group') return ''
  if (row.type === 'item' && row.material_shortage) {
    if (!v) return dueMatch ? 'cell-due' : ''
    return dueMatch ? 'tone-shortage cell-due' : 'tone-shortage'
  }
  if (row.type === 'item' && cellShowsActualDisplay(row, date) && !upstreamBg) {
    return dueMatch ? 'sc-cell-actual cell-due' : 'sc-cell-actual'
  }
  if (!v) return dueMatch ? 'cell-due' : ''
  if (upstreamBg) return dueMatch ? 'cell-due' : ''

  const rate = row.completion_rate
  if (rate != null && Number.isFinite(rate)) {
    if (rate >= 80) return dueMatch ? 'tone-high cell-due' : 'tone-high'
    if (rate >= 50) return dueMatch ? 'tone-mid cell-due' : 'tone-mid'
    return dueMatch ? 'tone-low cell-due' : 'tone-low'
  }
  return dueMatch ? 'tone-active cell-due' : 'tone-active'
}

function handlePrint() {
  if (!guardApsOperation(canExport)) return
  const root = printRootRef.value
  if (!root) return

  const printTarget = root.querySelector('.result-card') as HTMLElement | null
  if (!printTarget) return

  const styleTags = Array.from(document.querySelectorAll('style, link[rel="stylesheet"]'))
    .map((el) => el.outerHTML)
    .join('\n')

  const win = window.open('', '_blank')
  if (!win) return

  win.document.open()
  win.document.write(`
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8" />
        <title>Scheduling Print</title>
        ${styleTags}
        <style>
          @page { size: A3 landscape; margin: 8mm; }
          html, body { margin: 0; padding: 0; }
          * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
          .matrix-table-wrapper { height: auto !important; max-height: none !important; overflow: visible !important; }
          .result-card { border: none !important; box-shadow: none !important; padding: 0 !important; margin: 0 !important; }
          .result-head-actions .el-button { display: none !important; }
          .sc-range-selection-ui { display: none !important; }
          tfoot { display: table-row-group !important; }
          .sc-total-footer-row td { position: static !important; bottom: auto !important; }
          .sc-line-section { break-inside: avoid; page-break-inside: avoid; }
          .sc-line-section tr { break-inside: avoid; page-break-inside: avoid; }
        </style>
      </head>
      <body>
        ${printTarget.outerHTML}
      </body>
    </html>
  `)
  win.document.close()
  win.focus()
  win.print()
}

async function loadProcessOptions() {
  try {
    const res = await fetchProcesses({ page: 1, pageSize: 500 })
    const data = (res?.data ?? res) as { list?: ProcessItem[] }
    processOptions.value = Array.isArray(data.list) ? data.list : []
    const hasDefault = processOptions.value.some((p) => (p.process_cd || '').trim() === 'KT04')
    if (!hasDefault && processOptions.value.length) {
      searchForm.processCd = processOptions.value[0].process_cd || ''
    }
  } catch {
    processOptions.value = []
  }
}

async function loadLines() {
  lines.value = await fetchLines((searchForm.processCd || '').trim() || undefined)
  lines.value = lines.value.filter((x) => !isIgnoredLine(String(x.line_name || '').trim() || x.line_code))
  if (searchForm.lineId && !lines.value.some((x) => x.id === searchForm.lineId)) {
    searchForm.lineId = null
  }
}

function clearAttribCache() {
  attribCache.clear()
  attribInflight.clear()
}

async function loadGrid() {
  const [startDate, endDate] = searchForm.dateRange
  if (!startDate || !endDate) return
  loading.value = true
  try {
    grid.value = await fetchSchedulingGrid(
      startDate,
      endDate,
      searchForm.lineId ?? undefined,
      (searchForm.processCd || '').trim() || undefined,
    )
    clearAttribCache()
    clearMatrixRangeSelection()
  } finally {
    loading.value = false
  }
}

async function handleProcessChange() {
  await Promise.all([loadLines(), loadGrid()])
}

let autoLoadTimer: ReturnType<typeof setTimeout> | null = null
function scheduleAutoLoad() {
  if (autoLoadTimer) clearTimeout(autoLoadTimer)
  autoLoadTimer = setTimeout(() => {
    void loadGrid()
  }, 240)
}

onMounted(async () => {
  window.addEventListener('keydown', onMatrixRangeEscape)
  window.addEventListener('mouseup', onMatrixRangeMouseUp)
  await loadProcessOptions()
  await Promise.all([loadLines(), loadGrid()])
})

onUnmounted(() => {
  window.removeEventListener('keydown', onMatrixRangeEscape)
  window.removeEventListener('mouseup', onMatrixRangeMouseUp)
})

watch(
  () => searchForm.lineId,
  () => {
    scheduleAutoLoad()
  },
)

watch(
  () => searchForm.dateRange,
  () => {
    scheduleAutoLoad()
  },
  { deep: true },
)

watch(matrixRows, () => {
  clearMatrixRangeSelection()
})

watch(
  () => grid.value,
  () => {
    const sel = (searchForm.itemName || '').trim()
    if (!sel) return
    if (!schedulingProductOptions.value.includes(sel)) {
      searchForm.itemName = null
    }
  },
)
</script>

<style scoped>
.scheduling-page {
  padding: 10px 12px 12px;
  background:
    radial-gradient(circle at 10% -20%, rgba(59, 130, 246, 0.1), transparent 35%),
    radial-gradient(circle at 110% -30%, rgba(16, 185, 129, 0.08), transparent 30%),
    #f3f6fb;
  min-height: 100%;
}

.plan-hd {
  margin-bottom: 8px;
  padding: 4px 2px 2px;
}

.plan-hd-title {
  margin: 0;
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 18px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: 0.2px;
  line-height: 1.1;
  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.55);
}

.plan-hd-text-wrap {
  display: inline-flex;
  align-items: flex-end;
  flex-wrap: wrap;
  gap: 8px 12px;
}

.plan-hd-title-text {
  flex-shrink: 0;
  line-height: 1.1;
}

.plan-hd-icon {
  width: 26px;
  height: 26px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
  box-shadow:
    0 6px 14px rgba(37, 99, 235, 0.24),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
}

.plan-hd-icon svg {
  width: 15px;
  height: 15px;
  fill: #fff;
}

.plan-hd-sub {
  font-weight: 400;
  color: #5f6f86;
  font-size: 12px;
  line-height: 1.1;
}

.plan-card {
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(3px);
  padding: 10px 12px;
  margin-bottom: 8px;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 8px 20px rgba(15, 23, 42, 0.04);
}

.filter-card {
  padding: 7px 10px;
  border-color: rgba(191, 219, 254, 0.75);
  background:
    linear-gradient(135deg, rgba(239, 246, 255, 0.82) 0%, rgba(250, 245, 255, 0.76) 100%),
    rgba(255, 255, 255, 0.95);
  box-shadow:
    0 10px 22px rgba(37, 99, 235, 0.07),
    inset 0 1px 0 rgba(255, 255, 255, 0.74);
}

.filter-form :deep(.el-form-item__label) {
  font-size: 12px;
  font-weight: 600;
  color: #1e3a8a;
  padding-right: 5px;
  line-height: 30px;
}

.compact-form {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  row-gap: 2px;
  column-gap: 6px;
}

.compact-form :deep(.el-form-item) {
  margin-bottom: 2px;
  margin-right: 0;
}

.compact-form :deep(.el-input__wrapper),
.compact-form :deep(.el-select__wrapper) {
  border-radius: 10px;
  min-height: 32px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
  transition: box-shadow 0.18s ease, border-color 0.18s ease;
}

.compact-form :deep(.el-input__wrapper:hover),
.compact-form :deep(.el-select__wrapper:hover) {
  box-shadow: 0 4px 10px rgba(37, 99, 235, 0.12);
}

.compact-form :deep(.el-input__wrapper.is-focus),
.compact-form :deep(.el-select__wrapper.is-focused) {
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.18);
}

.compact-form :deep(.el-input__inner),
.compact-form :deep(.el-select__selected-item),
.compact-form :deep(.el-range-input) {
  font-size: 12px;
}

.compact-form :deep(.el-button) {
  border-radius: 8px;
  font-weight: 600;
  padding: 8px 14px;
}

.stat-grid {
  display: flex;
  flex-wrap: nowrap;
  gap: 12px;
  margin-bottom: 10px;
}

.stat-card {
  position: relative;
  overflow: hidden;
  flex: 1 1 0;
  min-width: 0;
  border-radius: 16px;
  padding: 12px 14px 13px;
  display: flex;
  flex-direction: column;
  gap: 5px;
  backdrop-filter: blur(14px) saturate(1.35);
  -webkit-backdrop-filter: blur(14px) saturate(1.35);
  border: 1px solid rgba(255, 255, 255, 0.52);
  background:
    linear-gradient(155deg, rgba(255, 255, 255, 0.62) 0%, rgba(255, 255, 255, 0.28) 55%, rgba(255, 255, 255, 0.14) 100%);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.75) inset,
    0 -1px 0 rgba(15, 23, 42, 0.04) inset,
    0 12px 28px rgba(15, 23, 42, 0.1),
    0 4px 10px rgba(15, 23, 42, 0.06);
  transition:
    transform 0.22s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.22s ease,
    border-color 0.22s ease;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  border-radius: 16px 16px 0 0;
  opacity: 0.92;
}

.stat-card__glow {
  position: absolute;
  top: -28px;
  right: -18px;
  width: 88px;
  height: 88px;
  border-radius: 50%;
  filter: blur(22px);
  opacity: 0.55;
  pointer-events: none;
}

.stat-card__shine {
  position: absolute;
  top: 0;
  left: 0;
  width: 55%;
  height: 100%;
  background: linear-gradient(105deg, rgba(255, 255, 255, 0.42) 0%, rgba(255, 255, 255, 0.08) 45%, transparent 70%);
  pointer-events: none;
}

.stat-card:hover {
  transform: translateY(-3px) scale(1.01);
  border-color: rgba(255, 255, 255, 0.72);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.82) inset,
    0 -1px 0 rgba(15, 23, 42, 0.05) inset,
    0 18px 36px rgba(15, 23, 42, 0.14),
    0 6px 14px rgba(15, 23, 42, 0.08);
}

.stat-card--lines {
  --stat-accent: #2563eb;
  --stat-accent-soft: rgba(37, 99, 235, 0.18);
  --stat-value-color: #1e3a8a;
  --stat-label-color: #3b5f9a;
}

.stat-card--lines::before {
  background: linear-gradient(90deg, #60a5fa 0%, #2563eb 55%, #1d4ed8 100%);
}

.stat-card--lines .stat-card__glow {
  background: radial-gradient(circle, rgba(59, 130, 246, 0.75) 0%, transparent 70%);
}

.stat-card--plan {
  --stat-accent: #059669;
  --stat-accent-soft: rgba(5, 150, 105, 0.18);
  --stat-value-color: #065f46;
  --stat-label-color: #2f6f5c;
}

.stat-card--plan::before {
  background: linear-gradient(90deg, #34d399 0%, #059669 55%, #047857 100%);
}

.stat-card--plan .stat-card__glow {
  background: radial-gradient(circle, rgba(16, 185, 129, 0.72) 0%, transparent 70%);
}

.stat-card--efficiency {
  --stat-accent: #d97706;
  --stat-accent-soft: rgba(217, 119, 6, 0.2);
  --stat-value-color: #92400e;
  --stat-label-color: #9a5f1a;
}

.stat-card--efficiency::before {
  background: linear-gradient(90deg, #fbbf24 0%, #d97706 55%, #b45309 100%);
}

.stat-card--efficiency .stat-card__glow {
  background: radial-gradient(circle, rgba(245, 158, 11, 0.75) 0%, transparent 70%);
}

.stat-card--hours {
  --stat-accent: #7c3aed;
  --stat-accent-soft: rgba(124, 58, 237, 0.2);
  --stat-value-color: #5b21b6;
  --stat-label-color: #6d4a9e;
}

.stat-card--hours::before {
  background: linear-gradient(90deg, #a78bfa 0%, #7c3aed 55%, #6d28d9 100%);
}

.stat-card--hours .stat-card__glow {
  background: radial-gradient(circle, rgba(139, 92, 246, 0.75) 0%, transparent 70%);
}

.stat-label {
  position: relative;
  z-index: 1;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.25px;
  color: var(--stat-label-color, #5b6b82);
}

.stat-value {
  position: relative;
  z-index: 1;
  font-size: clamp(16px, 1.6vw, 22px);
  font-weight: 800;
  color: var(--stat-value-color, #0b1220);
  line-height: 1.1;
  letter-spacing: 0.2px;
  text-shadow:
    0 1px 0 rgba(255, 255, 255, 0.65),
    0 2px 8px var(--stat-accent-soft, rgba(15, 23, 42, 0.08));
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stat-value--warn {
  color: #dc2626;
}

.result-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 8px;
  gap: 10px;
}

.result-head-actions {
  --result-chip-h: 22px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
  padding-top: 2px;
}

.sc-range-selection-ui {
  max-width: min(520px, 100%);
  line-height: 1.35;
  font-size: 11px;
}

.sc-range-hint {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 6px;
}

.sc-range-sep {
  color: #cbd5e1;
  font-weight: 400;
}

.sc-range-sum-line {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
}

.sc-range-sum {
  font-weight: 800;
  color: #1e40af;
}

.sc-range-wait {
  font-weight: 700;
  color: #b45309;
}

.sc-range-clear-btn {
  margin: 0;
  padding: 0;
  border: none;
  background: none;
  font: inherit;
  font-weight: 800;
  color: #dc2626;
  cursor: pointer;
  line-height: 1.35;
}

.sc-range-clear-btn:hover {
  color: #b91c1c;
}

.matrix-table-wrapper.is-range-dragging {
  user-select: none;
  cursor: cell;
}

.matrix-table-wrapper.is-range-dragging .sc-selectable-cell {
  cursor: cell;
}

.sc-selectable-cell {
  cursor: cell;
}

.sc-selectable-cell:focus-visible {
  outline: 2px solid #2563eb;
  outline-offset: -2px;
  z-index: 1;
}

.sc-range-selected {
  box-shadow: inset 0 0 0 999px rgba(59, 130, 246, 0.2) !important;
}

.sc-range-anchor {
  outline: 2px solid #2563eb !important;
  outline-offset: -3px;
  z-index: 1;
}

.print-btn.el-button {
  position: relative;
  overflow: hidden;
  box-sizing: border-box;
  border: 1px solid rgba(255, 255, 255, 0.62) !important;
  border-radius: 999px !important;
  padding: 0 11px !important;
  height: var(--result-chip-h) !important;
  min-height: var(--result-chip-h) !important;
  font-size: 11px !important;
  line-height: 1 !important;
  color: #1e3a8a !important;
  font-weight: 800;
  letter-spacing: 0.2px;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.78) 0%, rgba(224, 242, 254, 0.52) 48%, rgba(199, 210, 254, 0.42) 100%) !important;
  backdrop-filter: blur(14px) saturate(1.35);
  -webkit-backdrop-filter: blur(14px) saturate(1.35);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.85) inset,
    0 -1px 0 rgba(37, 99, 235, 0.08) inset,
    0 10px 24px rgba(37, 99, 235, 0.18),
    0 4px 10px rgba(15, 23, 42, 0.08);
  transition:
    transform 0.22s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.22s ease,
    border-color 0.22s ease,
    background 0.22s ease;
}

.print-btn.el-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, #60a5fa 0%, #6366f1 55%, #8b5cf6 100%);
  opacity: 0.95;
  pointer-events: none;
}

.print-btn.el-button::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 58%;
  height: 100%;
  background: linear-gradient(105deg, rgba(255, 255, 255, 0.55) 0%, rgba(255, 255, 255, 0.1) 45%, transparent 72%);
  pointer-events: none;
}

.print-btn__content {
  position: relative;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  line-height: 1;
}

.print-btn__icon {
  width: 12px;
  height: 12px;
  fill: currentColor;
  filter: drop-shadow(0 1px 0 rgba(255, 255, 255, 0.55));
}

.print-btn.el-button:hover {
  transform: translateY(-1px);
  border-color: rgba(255, 255, 255, 0.82) !important;
  color: #1d4ed8 !important;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.88) 0%, rgba(219, 234, 254, 0.62) 48%, rgba(199, 210, 254, 0.5) 100%) !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.92) inset,
    0 -1px 0 rgba(37, 99, 235, 0.1) inset,
    0 16px 32px rgba(37, 99, 235, 0.24),
    0 6px 14px rgba(15, 23, 42, 0.1);
}

.print-btn.el-button:active {
  transform: translateY(0) scale(0.98);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.72) inset,
    0 2px 8px rgba(37, 99, 235, 0.16),
    0 1px 4px rgba(15, 23, 42, 0.08);
}

.print-btn.el-button.is-disabled,
.print-btn.el-button.is-disabled:hover,
.print-btn.el-button.is-disabled:active {
  transform: none;
  opacity: 0.55;
  box-shadow: none;
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
}

.result-title {
  display: flex;
  flex-direction: row;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px 10px;
  font-size: 14px;
  font-weight: 800;
  color: #0f172a;
}

.sc-matrix-legend {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 8px;
  margin-left: 4px;
  padding-left: 10px;
  border-left: 1px solid #e2e8f0;
  font-size: 10px;
  font-weight: 600;
  color: #475569;
  line-height: 1.35;
}

.sc-legend-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.sc-legend-text {
  font-weight: 600;
  color: #475569;
}

.sc-legend-sep {
  color: #cbd5e1;
  font-weight: 400;
  user-select: none;
}

.sc-legend-swatch {
  display: inline-block;
  width: 14px;
  height: 10px;
  border-radius: 3px;
  border: 1px solid rgba(15, 23, 42, 0.12);
  flex-shrink: 0;
}

.sc-legend-swatch--actual {
  background: rgba(254, 249, 195, 0.88);
}

.sc-legend-swatch--cm {
  background: rgba(254, 202, 202, 0.82);
}

.sc-legend-swatch--plan {
  background: rgba(187, 247, 208, 0.62);
}

.sc-legend-item--plan-toggle {
  gap: 6px;
}

.sc-legend-mode-switch {
  margin-left: 2px;
  --el-switch-on-color: #16a34a;
  --el-switch-off-color: #94a3b8;
}

.result-title-feature {
  color: #1d4ed8;
  font-weight: 800;
}

.result-title-sep {
  color: #94a3b8;
  font-weight: 600;
  user-select: none;
}

.result-title-main {
  font-weight: 800;
  color: #0f172a;
}

.result-note {
  font-size: 11px;
  color: #64748b;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  padding: 2px 8px;
  border-radius: 999px;
}

.result-note--chip {
  display: inline-flex;
  align-items: center;
  height: var(--result-chip-h);
  padding: 0 10px;
  line-height: 1;
  box-sizing: border-box;
}

.matrix-table-wrapper {
  height: 620px;
  overflow: auto;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #fff;
}

.modern-scroll {
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.matrix-table {
  width: max-content;
  min-width: 100%;
  border-collapse: collapse;
  font-size: 11px;
}

.matrix-table th,
.matrix-table td {
  border: 1px solid #e6edf5;
  padding: 3px 5px;
  white-space: nowrap;
}

.matrix-table thead th {
  background: linear-gradient(180deg, #f8fbff 0%, #eef4fb 100%);
  font-weight: 700;
  color: #42526a;
  position: sticky;
  top: 0;
  z-index: 3;
  box-shadow: 0 1px 0 #dbe5f1;
}

.sc-sticky-col {
  position: sticky;
  left: 0;
  background: #fff;
  z-index: 2;
}

.matrix-table thead .sc-sticky-col {
  z-index: 4;
}

.sc-line-col {
  width: 50px;
  min-width: 50px;
  left: 0;
}

.sc-order-col {
  width: 50px;
  min-width: 50px;
  left: 50px;
}

.sc-item-col {
  width: 120px;
  min-width: 120px;
  left: 100px;
}

.sc-eff-col {
  width: 66px;
  min-width: 66px;
  left: 220px;
}

.sc-total-col {
  width: 90px;
  min-width: 90px;
  left: 286px;
}

.numeric-cell {
  text-align: center;
}

.date-col {
  min-width: 40px;
}

.date-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  line-height: 1.1;
}

.date-text {
  font-size: 10px;
  font-weight: 650;
}

.weekday-text {
  font-size: 9px;
  color: #6b7a90;
}

.sc-group-header-row {
  font-weight: 700;
  border-top: 2px solid #bfdbfe;
}

.sc-group-header-row .sc-line-code {
  font-weight: 800;
  color: #1e3a8a;
}

.sc-item-row:nth-child(2n) {
  background: #fcfdff;
}

.sc-item-row:hover {
  background: #f1f7ff;
}

.sc-line-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-height: 18px;
}

.sc-rate {
  color: #1d4ed8;
  font-size: 10px;
  font-weight: 700;
}

.sc-item-name {
  max-width: 170px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sc-flag {
  color: #dc2626;
  font-size: 9px;
  font-weight: 700;
}

/** 実績表示セル（過去日・当日に実績あり）：浅黄 */
.sc-cell-actual {
  background: rgba(254, 249, 195, 0.88);
}

.tone-active {
  background: rgba(187, 247, 208, 0.5);
}

.tone-high {
  background: rgba(34, 197, 94, 0.22);
}

.tone-mid {
  background: rgba(245, 158, 11, 0.18);
}

.tone-low {
  background: rgba(239, 68, 68, 0.18);
}

.tone-shortage {
  background: rgba(239, 68, 68, 0.26);
}

.cell-due {
  outline: 1px solid #f59e0b;
  outline-offset: -2px;
}

.matrix-table thead th.is-weekend .date-text,
.matrix-table thead th.is-weekend .weekday-text {
  color: #dc2626;
}

.matrix-table thead th.is-today {
  background: linear-gradient(180deg, #fff3d4 0%, #ffeab0 100%);
}

.sc-total-footer-row td {
  background: #f3f8ff;
  font-weight: 700;
  position: sticky;
  bottom: 0;
  z-index: 3;
  box-shadow: 0 -1px 0 #dbe5f1;
}

.sc-total-footer-row .sc-sticky-col {
  z-index: 4;
}

@media (max-width: 540px) {
  .stat-grid {
    flex-wrap: wrap;
  }

  .stat-card {
    flex: 1 1 calc(50% - 6px);
    min-width: calc(50% - 6px);
  }
}

@media (max-width: 540px) {
  .stat-grid {
    gap: 10px;
  }

  .stat-card {
    flex: 1 1 100%;
    min-width: 100%;
    padding: 11px 13px 12px;
  }

  .stat-value {
    font-size: 20px;
    white-space: normal;
  }
}

.sc-attrib-tooltip {
  position: fixed;
  z-index: 9999;
  width: min(520px, calc(100vw - 24px));
  max-height: min(320px, calc(100vh - 24px));
  overflow: auto;
  padding: 10px 12px 12px;
  border-radius: 10px;
  border: 1px solid #cbd5e1;
  background: #fff;
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.18);
  pointer-events: auto;
}

.sc-attrib-tooltip__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid #e2e8f0;
}

.sc-attrib-tooltip__title {
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
}

.sc-attrib-tooltip__meta {
  font-size: 11px;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sc-attrib-tooltip__loading,
.sc-attrib-tooltip__empty {
  font-size: 12px;
  color: #64748b;
  padding: 8px 2px;
}

.sc-attrib-tooltip__table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
}

.sc-attrib-tooltip__table th,
.sc-attrib-tooltip__table td {
  padding: 4px 6px;
  border-bottom: 1px solid #f1f5f9;
  text-align: left;
  white-space: nowrap;
}

.sc-attrib-tooltip__table th {
  color: #475569;
  font-weight: 600;
  background: #f8fafc;
}

.sc-attrib-tooltip__ship {
  color: #0369a1;
  font-weight: 600;
}

.sc-attrib-tooltip__num {
  text-align: right;
  font-variant-numeric: tabular-nums;
  font-weight: 600;
}

.sc-attrib-pill {
  display: inline-block;
  padding: 1px 6px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 600;
}

.sc-attrib-pill.is-done {
  background: #dcfce7;
  color: #15803d;
}

.sc-attrib-pill.is-pending {
  background: #f1f5f9;
  color: #64748b;
}

.sc-attrib-tooltip__code--head {
  font-size: 11px;
  margin-left: auto;
}

.sc-attrib-tooltip__code {
  font-size: 10px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  color: #475569;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  padding: 1px 5px;
}

.matrix-table td.sc-cell-has-attrib {
  cursor: help;
}
</style>

