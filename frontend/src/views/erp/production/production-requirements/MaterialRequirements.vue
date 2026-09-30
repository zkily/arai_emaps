<template>
  <div class="material-requirements mr-modern">
    <header class="page-head">
      <div class="page-head-fx" aria-hidden="true">
        <span class="fx-orb orb-a" />
        <span class="fx-orb orb-b" />
        <span class="fx-grid" />
        <span class="fx-sheen" />
      </div>
      <div class="page-head-main">
        <div class="page-icon" aria-hidden="true">
          <el-icon :size="18"><Box /></el-icon>
        </div>
        <div class="page-head-text">
          <h1 class="page-title">{{ t('productionRequirements.materialTitle') }}</h1>
        </div>
      </div>
      <div class="page-head-chips">
        <span class="page-head-chip">
          <el-icon><Calendar /></el-icon>
          {{ headerPeriodText }}
        </span>
        <span v-if="summary" class="page-head-chip">
          <el-icon><Collection /></el-icon>
          {{ summary.total_material_kinds }}種
        </span>
      </div>
    </header>

    <el-card class="shell-card" shadow="hover">
      <div class="control-strip">
        <div class="control-left">
          <span class="ctl-label">{{ t('productionRequirements.periodLabel') }}</span>
          <div
            class="month-quick"
            role="group"
            :aria-label="t('productionRequirements.periodQuickAria')"
          >
            <button
              type="button"
              class="month-quick__btn month-quick__btn--first"
              :disabled="loading"
              @click="applyQuickMonth(-1)"
            >
              <el-icon class="month-quick__icon"><DArrowLeft /></el-icon>
              <span>{{ t('productionRequirements.quickPrevMonth') }}</span>
            </button>
            <button
              type="button"
              class="month-quick__btn month-quick__btn--mid"
              :disabled="loading"
              @click="applyQuickMonth(0)"
            >
              <el-icon class="month-quick__icon"><Calendar /></el-icon>
              <span>{{ t('productionRequirements.quickThisMonth') }}</span>
            </button>
            <button
              type="button"
              class="month-quick__btn month-quick__btn--last"
              :disabled="loading"
              @click="applyQuickMonth(1)"
            >
              <span>{{ t('productionRequirements.quickNextMonth') }}</span>
              <el-icon class="month-quick__icon"><DArrowRight /></el-icon>
            </button>
          </div>
          <div class="ctl-picker-wrap">
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="—"
              :start-placeholder="t('productionRequirements.periodStart')"
              :end-placeholder="t('productionRequirements.periodEnd')"
              value-format="YYYY-MM-DD"
              unlink-panels
              :disabled="loading"
              size="small"
              class="ctl-picker"
            />
          </div>
          <el-button type="primary" size="small" :loading="loading" class="btn-run" @click="runSummary">
            {{ t('productionRequirements.searchBtn') }}
          </el-button>
        </div>
      </div>

      <div v-if="summary" class="kpi-strip" @mousemove="handleKpiTilt" @mouseleave="resetKpiTilt">
        <div class="kpi-card kpi-card--range">
          <div class="kpi-card__icon"><el-icon><Calendar /></el-icon></div>
          <div class="kpi-card__body">
            <span class="kpi-card__label">{{ t('productionRequirements.periodLabel') }}</span>
            <span class="kpi-card__value kpi-card__value--mono">{{ summary.date_start }} — {{ summary.date_end }}</span>
          </div>
        </div>
        <div class="kpi-card kpi-card--kinds">
          <div class="kpi-card__icon"><el-icon><Collection /></el-icon></div>
          <div class="kpi-card__body">
            <span class="kpi-card__label">{{ t('productionRequirements.summaryKinds') }}</span>
            <span class="kpi-card__value">{{ summary.total_material_kinds }}</span>
          </div>
        </div>
        <div class="kpi-card kpi-card--pieces">
          <div class="kpi-card__icon"><el-icon><Histogram /></el-icon></div>
          <div class="kpi-card__body">
            <span class="kpi-card__label">{{ t('productionRequirements.summaryTotalPieces') }}</span>
            <span class="kpi-card__value">{{ (summary.total_piece_count ?? 0).toLocaleString() }}</span>
          </div>
        </div>
        <div class="kpi-card kpi-card--days">
          <div class="kpi-card__icon"><el-icon><Timer /></el-icon></div>
          <div class="kpi-card__body">
            <span class="kpi-card__label">日数</span>
            <span class="kpi-card__value">{{ periodDays }}</span>
          </div>
        </div>
      </div>

      <section class="panel">
        <div class="panel-head">
          <span class="panel-mark" />
          <span class="panel-title">{{ t('productionRequirements.materialTitle') }}</span>
        </div>
        <div class="table-frame">
          <el-table
            v-loading="loading"
            :data="items"
            stripe
            border
            size="small"
            class="tbl tbl-summary"
            :max-height="SUMMARY_TABLE_MAX_H"
            :empty-text="hasSearched ? '' : t('productionRequirements.placeholder')"
            :default-sort="{ prop: 'material_manufacturer', order: 'ascending' }"
          >
            <el-table-column prop="material_manufacturer" :label="t('productionRequirements.colMaker')" width="108" show-overflow-tooltip sortable />
            <el-table-column prop="material_name" :label="t('productionRequirements.colMaterialName')" width="132" show-overflow-tooltip sortable />
            <el-table-column prop="standard_specification" :label="t('productionRequirements.colSpec')" width="112" show-overflow-tooltip sortable />
            <el-table-column prop="piece_count" :label="t('productionRequirements.colPieceCount')" width="88" align="right">
              <template #default="{ row }">
                <div class="piece-cell">
                  <span class="piece-cell__bar" :style="{ width: `${piecePct(row.piece_count)}%` }" />
                  <span class="piece-cell__num">{{ (row.piece_count ?? 0).toLocaleString() }}</span>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </section>

      <el-alert
        v-if="hasSearched && summary?.daily_matrix_omitted"
        type="warning"
        :closable="false"
        show-icon
        class="omit-alert"
        :title="t('productionRequirements.dailyMatrixOmitted', { max: summary?.daily_matrix_max_days ?? 186 })"
      />

      <section v-if="hasSearched && dailyDates.length > 0" class="panel panel--matrix">
        <div class="panel-head panel-head--with-action">
          <div class="panel-head-left">
            <span class="panel-mark panel-mark--accent" />
            <span class="panel-title">{{ t('productionRequirements.dailyMatrixTitle') }}</span>
          </div>
          <el-button size="small" class="btn-print" @click="printDailyMatrix">
            <el-icon class="btn-print__icon"><Printer /></el-icon>
            <span class="btn-print__text">{{ t('productionRequirements.printMatrix') }}</span>
          </el-button>
        </div>
        <div class="table-frame table-frame--matrix">
          <el-table
            v-loading="loading"
            :data="matrixRows"
            border
            stripe
            size="small"
            class="tbl tbl-matrix"
            :max-height="MATRIX_TABLE_MAX_H"
            :empty-text="''"
            :default-sort="{ prop: 'material_name', order: 'ascending' }"
          >
            <el-table-column
              prop="material_manufacturer"
              :label="t('productionRequirements.colMaker')"
              fixed
              width="110"
              show-overflow-tooltip
              sortable
            />
            <el-table-column
              prop="material_name"
              :label="t('productionRequirements.colMaterialName')"
              fixed
              width="120"
              show-overflow-tooltip
              sortable
            />
            <el-table-column
              prop="standard_specification"
              :label="t('productionRequirements.colSpec')"
              fixed
              width="92"
              show-overflow-tooltip
              sortable
            />
            <el-table-column
              v-for="d in dailyDates"
              :key="d"
              width="55"
              align="right"
              label-class-name="matrix-day-col-head"
            >
              <template #header>
                <span class="day-head" :title="d">{{ shortDateLabel(d) }}</span>
              </template>
              <template #default="{ row }">
                <span class="qty-heat" :class="`qty-heat--${heatLevelCell(row, d)}`">{{ formatQtyCell(row, d) }}</span>
              </template>
            </el-table-column>
            <el-table-column
              :label="t('productionRequirements.rowTotal')"
              fixed="right"
              width="100"
              align="right"
            >
              <template #default="{ row }">
                {{ (row.row_total ?? 0).toLocaleString() }}
              </template>
            </el-table-column>
          </el-table>
        </div>
      </section>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  Box,
  Calendar,
  DArrowLeft,
  DArrowRight,
  Printer,
  Collection,
  Histogram,
  Timer,
} from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import {
  fetchMaterialRequirementsSummary,
  type MaterialRequirementsSummaryItem,
  type MaterialRequirementsSummaryMeta,
  type MaterialRequirementsDailyMatrixRow,
} from '@/api/productionSchedule'
import { useApsOperationPermission } from '@/composables/useApsOperationPermission'
import { guardApsOperation } from '@/utils/apsOperationGuard'

const { canCreate, canEdit, canDelete, canExport, canApprove } = useApsOperationPermission()


/** 汇总表表体最大高度（px），超出出现纵向滚动条 */
const SUMMARY_TABLE_MAX_H = 320
/** 日别矩阵表体最大高度（px） */
const MATRIX_TABLE_MAX_H = 380

const { t } = useI18n()

const dateRange = ref<[string, string] | null>(null)
const loading = ref(false)
const items = ref<MaterialRequirementsSummaryItem[]>([])
const summary = ref<MaterialRequirementsSummaryMeta | null>(null)
const hasSearched = ref(false)
const dailyDates = ref<string[]>([])
const matrixRows = ref<MaterialRequirementsDailyMatrixRow[]>([])

const headerPeriodText = computed(() => {
  const r = dateRange.value
  if (!r || !r[0]) return '—'
  return r[0] === r[1] ? r[0] : `${r[0]} 〜 ${r[1]}`
})

const periodDays = computed(() => {
  const s = summary.value
  if (!s?.date_start || !s?.date_end) return 0
  return dayjs(s.date_end).diff(dayjs(s.date_start), 'day') + 1
})

const maxPieceCount = computed(() =>
  items.value.reduce((m, r) => Math.max(m, Number(r.piece_count) || 0), 0)
)

function piecePct(n: number | null | undefined): number {
  const max = maxPieceCount.value
  const v = Number(n) || 0
  return max > 0 ? Math.max(0, Math.min(100, (v / max) * 100)) : 0
}

const matrixMax = computed(() => {
  let m = 0
  for (const row of matrixRows.value) {
    for (const v of Object.values(row.by_date ?? {})) {
      const n = Number(v) || 0
      if (n > m) m = n
    }
  }
  return m
})

/** 日別セルのヒートレベル（0=空・1〜4=期間内最大値に対する比率） */
function heatLevel(v: number): 0 | 1 | 2 | 3 | 4 {
  const max = matrixMax.value
  if (!v || max <= 0) return 0
  const r = v / max
  if (r >= 0.75) return 4
  if (r >= 0.5) return 3
  if (r >= 0.25) return 2
  return 1
}

function heatLevelCell(row: { by_date?: Record<string, number | null | undefined> }, d: string) {
  return heatLevel(Number(row.by_date?.[d]) || 0)
}

// KPI カードの3Dチルト（マウス追従）
function handleKpiTilt(e: MouseEvent) {
  const item = (e.target as HTMLElement | null)?.closest<HTMLElement>('.kpi-card')
  const host = e.currentTarget as HTMLElement
  host.querySelectorAll<HTMLElement>('.kpi-card').forEach((el) => {
    if (el !== item) {
      el.style.removeProperty('--rx')
      el.style.removeProperty('--ry')
    }
  })
  if (!item) return
  const rect = item.getBoundingClientRect()
  const px = (e.clientX - rect.left) / rect.width
  const py = (e.clientY - rect.top) / rect.height
  item.style.setProperty('--rx', `${((0.5 - py) * 12).toFixed(2)}deg`)
  item.style.setProperty('--ry', `${((px - 0.5) * 12).toFixed(2)}deg`)
  item.style.setProperty('--mx', `${(px * 100).toFixed(1)}%`)
  item.style.setProperty('--my', `${(py * 100).toFixed(1)}%`)
}

function resetKpiTilt(e: MouseEvent) {
  ;(e.currentTarget as HTMLElement).querySelectorAll<HTMLElement>('.kpi-card').forEach((el) => {
    el.style.removeProperty('--rx')
    el.style.removeProperty('--ry')
  })
}

function initDefaultRange() {
  const start = dayjs().startOf('month').format('YYYY-MM-DD')
  const end = dayjs().format('YYYY-MM-DD')
  dateRange.value = [start, end]
}

/** 将集计期间设为相对当月的整月：-1 前月、0 今月、1 翌月 */
function applyQuickMonth(offsetMonths: -1 | 0 | 1) {
  if (!guardApsOperation(canEdit)) return

  const base = dayjs().add(offsetMonths, 'month')
  const start = base.startOf('month').format('YYYY-MM-DD')
  const end = base.endOf('month').format('YYYY-MM-DD')
  dateRange.value = [start, end]
}

function formatQty(n: number) {
  if (n == null || Number.isNaN(n)) return '0'
  if (Number.isInteger(n)) return n.toLocaleString()
  return n.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 4 })
}

function shortDateLabel(iso: string) {
  if (!iso || iso.length < 10) return iso
  return iso.slice(5, 10)
}

function qtyFor(row: MaterialRequirementsDailyMatrixRow, d: string): number {
  const v = row.by_date?.[d]
  if (v == null || Number.isNaN(v)) return 0
  return v
}

function formatQtyCell(row: MaterialRequirementsDailyMatrixRow, d: string) {
  const v = qtyFor(row, d)
  if (v === 0) return ''
  return formatQty(v)
}

function escapeHtml(text: string | null | undefined): string {
  if (text == null) return ''
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

/** A4 横向・メーカーごとに改ページ・材料名昇順で印刷 */
function printDailyMatrix() {
  if (!guardApsOperation(canExport)) return

  if (!dailyDates.value.length) {
    ElMessage.warning(t('productionRequirements.printEmpty'))
    return
  }
  if (!matrixRows.value.length) {
    ElMessage.warning(t('productionRequirements.printEmpty'))
    return
  }

  const dates = [...dailyDates.value]
  const lblMaker = t('productionRequirements.colMaker')
  const lblName = t('productionRequirements.colMaterialName')
  const lblTotal = t('productionRequirements.rowTotal')
  const title = t('productionRequirements.dailyMatrixTitle')
  const period =
    summary.value != null ? `${summary.value.date_start} — ${summary.value.date_end}` : ''

  const dayOnlyLabel = (iso: string) => {
    if (!iso || iso.length < 10) return iso
    return String(Number(iso.slice(8, 10)))
  }

  const byMaker = new Map<string, MaterialRequirementsDailyMatrixRow[]>()
  for (const row of matrixRows.value) {
    const m = row.material_manufacturer ?? ''
    if (!byMaker.has(m)) byMaker.set(m, [])
    byMaker.get(m)!.push(row)
  }
  const makers = Array.from(byMaker.keys()).sort((a, b) =>
    a.localeCompare(b, undefined, { sensitivity: 'base', numeric: true }),
  )

  const buildHeader = () => {
    const dayThs = dates
      .map((d) => `<th class="col-day">${escapeHtml(dayOnlyLabel(d))}</th>`)
      .join('')
    return `<thead><tr>
      <th class="col-nm">${escapeHtml(lblName)}</th>
      ${dayThs}
      <th class="col-tot">${escapeHtml(lblTotal)}</th>
    </tr></thead>`
  }

  const sections: string[] = []
  for (let mi = 0; mi < makers.length; mi++) {
    const maker = makers[mi]
    const rows = [...(byMaker.get(maker) ?? [])].sort((a, b) => {
      const na = a.material_name ?? ''
      const nb = b.material_name ?? ''
      const c = na.localeCompare(nb, undefined, { sensitivity: 'base', numeric: true })
      if (c !== 0) return c
      return (a.standard_specification ?? '').localeCompare(b.standard_specification ?? '', undefined, {
        sensitivity: 'base',
        numeric: true,
      })
    })

    const bodyRows = rows
      .map((row) => {
        const tds = dates
          .map((d) => {
            const cell = formatQtyCell(row, d)
            return `<td class="td-num col-day">${escapeHtml(cell)}</td>`
          })
          .join('')
        return `<tr>
          <td class="col-nm">${escapeHtml(row.material_name ?? '')}</td>
          ${tds}
          <td class="td-num col-tot">${escapeHtml((row.row_total ?? 0).toLocaleString())}</td>
        </tr>`
      })
      .join('')

    const pageBreak = mi < makers.length - 1 ? 'page-break-after: always; break-after: page;' : ''
    sections.push(`
      <section class="print-mfg" style="${pageBreak}">
        <header class="print-doc-hdr">
          <h1>${escapeHtml(title)}</h1>
          <p class="print-doc-meta">${escapeHtml(period)}　／　${escapeHtml(lblMaker)}：<strong>${escapeHtml(maker || '—')}</strong></p>
        </header>
        <div class="print-tbl-wrap">
          <table class="print-tbl">
            ${buildHeader()}
            <tbody>${bodyRows}</tbody>
          </table>
        </div>
      </section>
    `)
  }

  const styles = `
    @page { size: A4 landscape; margin: 10mm; }
    * { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; }
    body {
      font-family: 'Yu Gothic', 'YuGothic', 'Hiragino Sans', 'Hiragino Kaku Gothic ProN', Meiryo, sans-serif;
      color: #1a1a1a;
      background: #fff;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }
    .print-mfg { padding: 0; }
    .print-doc-hdr {
      margin: 0 0 5mm 0;
      padding: 0 0 3.5mm 0;
      border-bottom: 1.25pt solid #1a1a1a;
    }
    .print-doc-hdr h1 {
      font-family: 'Yu Mincho', 'YuMincho', 'Hiragino Mincho ProN', 'MS PMincho', serif;
      font-size: 16pt;
      margin: 0 0 2.5mm 0;
      font-weight: 600;
      letter-spacing: 0.12em;
      color: #1a1a1a;
      line-height: 1.3;
    }
    .print-doc-meta {
      font-size: 10.5pt;
      margin: 0;
      color: #444;
      padding: 0;
      background: none;
      border: none;
      border-radius: 0;
      display: block;
      line-height: 1.5;
      letter-spacing: 0.04em;
    }
    .print-doc-meta strong { color: #1a1a1a; font-weight: 700; }
    .print-tbl-wrap {
      border-radius: 0;
      overflow: visible;
      border: none;
      background: #fff;
    }
    .print-tbl {
      width: 100%;
      border-collapse: collapse;
      table-layout: fixed;
      font-size: 9.5pt;
      border-top: 1.25pt solid #1a1a1a;
      border-bottom: 1.25pt solid #1a1a1a;
    }
    .print-tbl th, .print-tbl td {
      border: none;
      border-bottom: 0.5pt solid #c8c8c8;
      padding: 1.6mm 0.8mm;
      line-height: 1.35;
      vertical-align: middle;
      word-wrap: break-word;
      overflow-wrap: anywhere;
      color: #1a1a1a;
    }
    .print-tbl tbody tr:nth-child(even) { background: transparent; }
    .print-tbl tbody tr:last-child td { border-bottom: none; }
    .print-tbl th {
      background: #f5f5f5;
      color: #1a1a1a;
      font-weight: 700;
      text-align: center;
      border-bottom: 0.75pt solid #1a1a1a;
      padding: 1.4mm 0.5mm;
      letter-spacing: 0.04em;
    }
    .col-day {
      font-size: 8.5pt;
      padding: 1.2mm 0.3mm !important;
      line-height: 1.25;
      font-weight: 600;
      text-align: center;
      width: ${Math.max(1.8, Math.min(3.2, 72 / Math.max(dates.length, 1))).toFixed(2)}%;
    }
    .td-num {
      text-align: right;
      font-variant-numeric: tabular-nums;
      font-feature-settings: 'tnum';
    }
    .td-num.col-day {
      text-align: center;
      font-weight: 500;
      padding: 1.4mm 0.3mm !important;
    }
    .col-nm {
      width: 18%;
      text-align: left;
      padding-left: 2mm !important;
      padding-right: 2mm !important;
    }
    .col-tot {
      width: 5.5%;
      text-align: right;
      font-variant-numeric: tabular-nums;
      font-feature-settings: 'tnum';
    }
    th.col-tot { text-align: center; }
  `

  const html = `<!DOCTYPE html><html lang="ja"><head>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1"/>
    <title>${escapeHtml(title)}</title>
    <style>${styles}</style>
  </head><body>${sections.join('')}</body></html>`

  const w = window.open('', '_blank')
  if (!w) {
    ElMessage.warning(t('productionRequirements.printPopupBlocked'))
    return
  }
  w.document.open()
  w.document.write(html)
  w.document.close()
  w.focus()
  setTimeout(() => {
    w.print()
    setTimeout(() => w.close(), 400)
  }, 150)
}

async function runSummary() {
  if (!guardApsOperation(canEdit)) return

  const range = dateRange.value
  if (!range || range.length !== 2 || !range[0] || !range[1]) {
    ElMessage.warning(t('productionRequirements.selectPeriod'))
    return
  }
  loading.value = true
  hasSearched.value = true
  try {
    const res = await fetchMaterialRequirementsSummary({
      date_start: range[0],
      date_end: range[1],
    })
    if (res?.success && res.data) {
      items.value = res.data.items ?? []
      summary.value = res.data.summary ?? null
      const dm = res.data.daily_matrix
      dailyDates.value = dm?.dates ?? []
      matrixRows.value = dm?.rows ?? []
    } else {
      items.value = []
      summary.value = null
      dailyDates.value = []
      matrixRows.value = []
      ElMessage.warning(res?.message || t('productionRequirements.loadFailed'))
    }
  } catch (e: unknown) {
    items.value = []
    summary.value = null
    dailyDates.value = []
    matrixRows.value = []
    const ax = e as { response?: { data?: { detail?: string } } }
    const detail = ax?.response?.data?.detail
    ElMessage.error(typeof detail === 'string' ? detail : t('productionRequirements.loadFailed'))
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  initDefaultRange()
  void runSummary()
})
</script>

<style scoped>
.material-requirements {
  --mr-bg: #eef1f6;
  --mr-card: #ffffff;
  --mr-border: #e2e6ee;
  --mr-text: #1a1d26;
  --mr-muted: #6b7280;
  --mr-accent: linear-gradient(135deg, #3b82f6 0%, #6366f1 55%, #0d9488 100%);
  --mr-radius: 10px;
  --mr-shadow: 0 1px 3px rgba(15, 23, 42, 0.06), 0 4px 20px rgba(15, 23, 42, 0.04);

  min-height: calc(100vh - 100px);
  padding: 8px 10px 12px;
  background: var(--mr-bg);
  box-sizing: border-box;
}

.page-head {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  padding: 0 2px;
}

.page-head-main {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.page-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: var(--mr-accent);
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.35);
}

.page-head-text {
  min-width: 0;
}

.page-title {
  margin: 0;
  font-size: 18px;
  font-weight: 800;
  color: var(--mr-text);
  letter-spacing: -0.03em;
  line-height: 1.2;
  background: linear-gradient(105deg, #1e293b 0%, #3b82f6 45%, #0d9488 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.shell-card {
  border-radius: var(--mr-radius);
  border: 1px solid var(--mr-border);
  background: var(--mr-card);
  box-shadow: var(--mr-shadow);
}

.shell-card :deep(.el-card__body) {
  padding: 10px 12px 12px;
}

.control-strip {
  margin-bottom: 6px;
}

.btn-run {
  border: none;
  background: linear-gradient(135deg, #2563eb 0%, #4f46e5 50%, #0891b2 100%);
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.35);
}

.btn-run:hover {
  filter: brightness(1.06);
}

.control-left {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.ctl-label {
  font-size: 12px;
  font-weight: 600;
  color: #374151;
  flex-shrink: 0;
}

.month-quick {
  display: inline-flex;
  align-items: stretch;
  flex-shrink: 0;
  border-radius: 12px;
  overflow: hidden;
  background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%);
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.06),
    0 0 0 1px rgba(99, 102, 241, 0.22),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.month-quick__btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 6px 14px;
  margin: 0;
  border: none;
  background: transparent;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: #3730a3;
  cursor: pointer;
  transition:
    background 0.18s ease,
    color 0.18s ease,
    box-shadow 0.18s ease;
}

.month-quick__btn:hover:not(:disabled) {
  background: linear-gradient(180deg, rgba(238, 242, 255, 0.95) 0%, rgba(224, 231, 255, 0.85) 100%);
  color: #312e81;
}

.month-quick__btn:active:not(:disabled) {
  background: linear-gradient(180deg, #e0e7ff 0%, #c7d2fe 100%);
}

.month-quick__btn:focus-visible {
  outline: 2px solid #6366f1;
  outline-offset: 2px;
  z-index: 1;
}

.month-quick__btn:disabled {
  opacity: 0.48;
  cursor: not-allowed;
}

.month-quick__btn + .month-quick__btn {
  box-shadow: inset 1px 0 0 rgba(99, 102, 241, 0.22);
}

.month-quick__btn--first {
  padding-left: 12px;
}

.month-quick__btn--last {
  padding-right: 12px;
}

.month-quick__icon {
  font-size: 13px;
  flex-shrink: 0;
  color: #6366f1;
}

.month-quick__btn:hover:not(:disabled) .month-quick__icon {
  color: #4f46e5;
}

.ctl-picker-wrap {
  flex: 0 0 auto;
  width: 280px;
  max-width: 280px;
}
.ctl-picker-wrap :deep(.el-date-editor) {
  width: 100% !important;
  max-width: 100% !important;
  box-sizing: border-box;
}
.ctl-picker {
  width: 100%;
  max-width: 100%;
}

.stat-chips {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 8px;
  margin-bottom: 8px;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 11px;
  font-size: 11px;
  font-weight: 500;
  border-radius: 999px;
  line-height: 1.3;
  border: 1px solid transparent;
}

.chip em {
  font-style: normal;
  font-weight: 800;
}

.chip--range {
  font-variant-numeric: tabular-nums;
  font-family: ui-monospace, monospace;
  font-size: 10px;
  color: #1e40af;
  background: linear-gradient(180deg, #eff6ff 0%, #dbeafe 100%);
  border-color: #93c5fd;
}

.chip--range em {
  color: #1d4ed8;
}

.chip--kinds {
  color: #5b21b6;
  background: linear-gradient(180deg, #f5f3ff 0%, #ede9fe 100%);
  border-color: #c4b5fd;
}

.chip--kinds em {
  color: #4c1d95;
}

.chip--pieces {
  color: #065f46;
  background: linear-gradient(180deg, #ecfdf5 0%, #d1fae5 100%);
  border-color: #6ee7b7;
}

.chip--pieces em {
  color: #047857;
}

.panel {
  margin-top: 4px;
}

.panel--matrix {
  margin-top: 10px;
  padding: 10px 10px 0;
  border-radius: 10px;
  border: 1px solid #c7d2fe;
  background: linear-gradient(165deg, rgba(238, 242, 255, 0.65) 0%, rgba(255, 255, 255, 0.9) 48%, rgba(240, 253, 250, 0.5) 100%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.panel-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.panel-head--with-action {
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 8px 12px;
}

.panel-head-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.btn-print {
  flex-shrink: 0;
  height: auto !important;
  padding: 7px 18px !important;
  border: none !important;
  border-radius: 999px !important;
  font-weight: 700 !important;
  letter-spacing: 0.03em;
  color: #fff !important;
  background: linear-gradient(135deg, #4f46e5 0%, #6366f1 42%, #0d9488 100%) !important;
  box-shadow:
    0 2px 10px rgba(79, 70, 229, 0.38),
    inset 0 1px 0 rgba(255, 255, 255, 0.22);
  transition:
    filter 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.15s ease;
}

.btn-print:hover {
  filter: brightness(1.07);
  box-shadow:
    0 4px 16px rgba(79, 70, 229, 0.45),
    inset 0 1px 0 rgba(255, 255, 255, 0.28) !important;
}

.btn-print:active {
  transform: scale(0.98);
  filter: brightness(0.96);
}

.btn-print__icon {
  margin-right: 6px;
  font-size: 15px;
  vertical-align: middle;
}

.btn-print__text {
  vertical-align: middle;
}

.panel-mark {
  width: 3px;
  height: 14px;
  border-radius: 2px;
  background: linear-gradient(180deg, #3b82f6, #6366f1);
  flex-shrink: 0;
}

.panel-mark--accent {
  background: linear-gradient(180deg, #0d9488, #3b82f6);
}

.panel-title {
  font-size: 13px;
  font-weight: 700;
  color: #1f2937;
  letter-spacing: -0.01em;
}

.table-frame {
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e8ecf4;
  background: #fafbfc;
}

.table-frame--matrix {
  overflow-x: auto;
  border-color: #c7d2fe;
  background: rgba(255, 255, 255, 0.85);
}

.panel--matrix .panel-head {
  margin-bottom: 8px;
}

.panel--matrix .table-frame {
  margin-bottom: 2px;
}

.tbl :deep(.el-table__header th) {
  font-size: 11px;
  font-weight: 600;
  color: #374151;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%) !important;
}

.tbl :deep(.el-table__body td) {
  font-size: 12px;
  padding: 4px 0;
}

.tbl :deep(.el-table__cell) {
  padding: 4px 8px;
}

.tbl-summary :deep(.el-table__body-wrapper),
.tbl-matrix :deep(.el-table__body-wrapper) {
  scrollbar-width: thin;
  scrollbar-color: #c1c9d6 #f1f5f9;
}

.tbl-summary :deep(.el-table__body-wrapper)::-webkit-scrollbar,
.tbl-matrix :deep(.el-table__body-wrapper)::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.tbl-summary :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb,
.tbl-matrix :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb {
  background: #c1c9d6;
  border-radius: 4px;
}

.tbl-summary :deep(.el-table__header th) {
  background: linear-gradient(180deg, #f0fdf4 0%, #dcfce7 100%) !important;
  color: #14532d !important;
}

.tbl-matrix {
  min-width: max-content;
}

/* 日別表：左固定＝メーカー・材料名・規格 */
.tbl-matrix :deep(.el-table__fixed-left .el-table__header-wrapper th) {
  background: linear-gradient(180deg, #dbeafe 0%, #e0e7ff 100%) !important;
  color: #1e3a8a !important;
  font-weight: 700 !important;
}

.tbl-matrix :deep(.el-table__fixed-left .el-table__body-wrapper td) {
  background: linear-gradient(180deg, rgba(239, 246, 255, 0.5) 0%, rgba(255, 255, 255, 0.95) 100%) !important;
}

/* 日付列ヘッダ */
.tbl-matrix :deep(th.matrix-day-col-head) {
  padding: 2px 4px !important;
  font-size: 10px !important;
  background: linear-gradient(180deg, #fffbeb 0%, #fde68a 100%) !important;
  color: #92400e !important;
  font-weight: 700 !important;
}

/* 右固定：期間合計 */
.tbl-matrix :deep(.el-table__fixed-right .el-table__header-wrapper th) {
  background: linear-gradient(180deg, #d1fae5 0%, #a7f3d0 100%) !important;
  color: #065f46 !important;
  font-weight: 700 !important;
}

.tbl-matrix :deep(.el-table__fixed-right .el-table__body-wrapper td) {
  background: linear-gradient(180deg, rgba(236, 253, 245, 0.9) 0%, rgba(255, 255, 255, 0.98) 100%) !important;
  font-weight: 600;
  color: #047857;
}

.omit-alert {
  margin-top: 8px;
  padding: 6px 10px;
}

.omit-alert :deep(.el-alert__title) {
  font-size: 12px;
}

.day-head {
  cursor: default;
  font-variant-numeric: tabular-nums;
}

/* 页面美化：現代UI・3D動効・色分け（材料需要量 / 生産需要量 blue→indigo→teal） */
.material-requirements.mr-modern {
  background:
    radial-gradient(1000px 360px at 0% 0%, rgba(79, 70, 229, 0.09), transparent 60%),
    radial-gradient(900px 360px at 100% 0%, rgba(13, 148, 136, 0.09), transparent 60%),
    #f1f4f9;
}

/* ---------- Hero ヘッダー ---------- */
.mr-modern .page-head {
  position: relative;
  overflow: hidden;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 10px;
  padding: 12px 16px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: linear-gradient(120deg, #0f172a 0%, #1e3a8a 30%, #4f46e5 66%, #0d9488 100%);
  box-shadow:
    0 16px 32px -18px rgba(79, 70, 229, 0.6),
    inset 0 1px 0 rgba(255, 255, 255, 0.16);
}

.mr-modern .page-head-fx {
  position: absolute;
  inset: 0;
  z-index: 0;
  overflow: hidden;
  pointer-events: none;
}

.mr-modern .page-head-main,
.mr-modern .page-head-chips {
  position: relative;
  z-index: 1;
}

.mr-modern .page-head-fx .fx-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(24px);
  opacity: 0.6;
  animation: mrOrbFloat 10s ease-in-out infinite;
}

.mr-modern .page-head-fx .orb-a {
  width: 220px;
  height: 220px;
  top: -120px;
  right: 20%;
  background: radial-gradient(circle, #a5b4fc 0%, transparent 70%);
}

.mr-modern .page-head-fx .orb-b {
  width: 200px;
  height: 200px;
  bottom: -130px;
  left: 24%;
  background: radial-gradient(circle, #5eead4 0%, transparent 70%);
  animation-delay: -5s;
}

.mr-modern .page-head-fx .fx-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.07) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.07) 1px, transparent 1px);
  background-size: 22px 22px;
  mask-image: linear-gradient(90deg, transparent 0%, #000 30%, #000 70%, transparent 100%);
}

.mr-modern .page-head-fx .fx-sheen {
  position: absolute;
  top: 0;
  bottom: 0;
  left: -40%;
  width: 35%;
  background: linear-gradient(100deg, transparent 0%, rgba(255, 255, 255, 0.16) 50%, transparent 100%);
  animation: mrSheen 7s ease-in-out infinite;
}

.mr-modern .page-icon {
  width: 38px;
  height: 38px;
  border-radius: 11px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.32) 0%, rgba(255, 255, 255, 0.08) 100%);
  border: 1px solid rgba(255, 255, 255, 0.36);
  box-shadow:
    0 4px 0 rgba(15, 23, 42, 0.5),
    0 10px 20px -8px rgba(2, 6, 23, 0.55),
    inset 0 1px 0 rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(6px);
  animation: mrIconFloat 4.5s ease-in-out infinite;
}

.mr-modern .page-title {
  background: none;
  color: #fff;
  -webkit-text-fill-color: #fff;
  letter-spacing: 0.02em;
  text-shadow: 0 2px 10px rgba(2, 6, 23, 0.35);
}

.mr-modern .page-head-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.mr-modern .page-head-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  font-variant-numeric: tabular-nums;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.28);
  backdrop-filter: blur(6px);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

/* ---------- シェルカード・操作帯 ---------- */
.mr-modern .shell-card {
  position: relative;
  overflow: hidden;
  border-radius: 14px;
  border-color: rgba(199, 210, 254, 0.8);
  box-shadow:
    0 16px 32px -24px rgba(67, 56, 202, 0.5),
    0 1px 3px rgba(15, 23, 42, 0.05);
}

.mr-modern .shell-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  z-index: 2;
  background: linear-gradient(90deg, #1e3a8a 0%, #4f46e5 50%, #0d9488 100%);
}

.mr-modern .control-strip {
  margin-bottom: 10px;
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px dashed #c7d2fe;
  background: linear-gradient(110deg, rgba(238, 242, 255, 0.9) 0%, rgba(255, 255, 255, 0.9) 60%, rgba(240, 253, 250, 0.8) 100%);
}

.mr-modern .ctl-label {
  padding: 1px 10px;
  font-weight: 700;
  color: #3730a3;
  border-radius: 999px;
  background: linear-gradient(145deg, #eef2ff 0%, #e0e7ff 100%);
  box-shadow:
    0 2px 0 #c7d2fe,
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.mr-modern .ctl-picker-wrap :deep(.el-input__wrapper) {
  border-radius: 8px;
  transition: box-shadow 0.2s ease;
}

.mr-modern .ctl-picker-wrap :deep(.el-input__wrapper:hover) {
  box-shadow:
    0 0 0 1px rgba(79, 70, 229, 0.45) inset,
    0 4px 10px -6px rgba(79, 70, 229, 0.5);
}

/* ---------- 3D キーキャップボタン（色分け） ---------- */
.mr-modern .month-quick {
  gap: 6px;
  overflow: visible;
  background: none;
  box-shadow: none;
}

.mr-modern .month-quick__btn,
.mr-modern .btn-run {
  --k-from: #818cf8;
  --k-to: #4f46e5;
  --k-edge: #3730a3;
  --k-glow: rgba(79, 70, 229, 0.5);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.22);
  border-radius: 9px;
  background: linear-gradient(145deg, var(--k-from) 0%, var(--k-to) 100%);
  box-shadow:
    0 3px 0 var(--k-edge),
    0 10px 18px -8px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease,
    filter 0.15s ease;
}

.mr-modern .month-quick__btn:hover:not(:disabled),
.mr-modern .btn-run:hover:not(.is-disabled) {
  color: #fff;
  background: linear-gradient(145deg, var(--k-from) 0%, var(--k-to) 100%);
  filter: brightness(1.06);
  transform: translateY(-2px);
  box-shadow:
    0 5px 0 var(--k-edge),
    0 14px 22px -8px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.36);
}

.mr-modern .month-quick__btn:active:not(:disabled),
.mr-modern .btn-run:active:not(.is-disabled) {
  background: linear-gradient(145deg, var(--k-from) 0%, var(--k-to) 100%);
  transform: translateY(2px);
  box-shadow:
    0 1px 0 var(--k-edge),
    0 4px 8px -4px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.mr-modern .month-quick__btn:disabled {
  box-shadow: none;
}

.mr-modern .month-quick__btn--first {
  --k-from: #ffffff;
  --k-to: #e0e7ff;
  --k-edge: #a5b4fc;
  --k-glow: rgba(79, 70, 229, 0.3);
  color: #3730a3;
  border-color: #c7d2fe;
}

.mr-modern .month-quick__btn--first:hover:not(:disabled) {
  color: #312e81;
}

.mr-modern .month-quick__btn--last {
  --k-from: #2dd4bf;
  --k-to: #0d9488;
  --k-edge: #115e59;
  --k-glow: rgba(13, 148, 136, 0.5);
}

.mr-modern .month-quick__btn--mid .month-quick__icon,
.mr-modern .month-quick__btn--last .month-quick__icon,
.mr-modern .month-quick__btn--mid:hover:not(:disabled) .month-quick__icon,
.mr-modern .month-quick__btn--last:hover:not(:disabled) .month-quick__icon {
  color: #fff;
}

.mr-modern .btn-run {
  --k-from: #3b82f6;
  --k-to: #1d4ed8;
  --k-edge: #1e3a8a;
  --k-glow: rgba(37, 99, 235, 0.5);
  padding: 0 16px;
  font-weight: 700;
}

.mr-modern .btn-print {
  background: linear-gradient(145deg, #a78bfa 0%, #6d28d9 100%) !important;
  box-shadow:
    0 3px 0 #4c1d95,
    0 10px 18px -8px rgba(109, 40, 217, 0.55),
    inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
}

.mr-modern .btn-print:hover {
  transform: translateY(-2px);
  box-shadow:
    0 5px 0 #4c1d95,
    0 14px 22px -8px rgba(109, 40, 217, 0.6),
    inset 0 1px 0 rgba(255, 255, 255, 0.36) !important;
}

.mr-modern .btn-print:active {
  transform: translateY(2px);
  box-shadow:
    0 1px 0 #4c1d95,
    0 4px 8px -4px rgba(109, 40, 217, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
}

/* ---------- KPI カード（3D チルト・色分け） ---------- */
.mr-modern .kpi-strip {
  display: grid;
  grid-template-columns: 1.4fr repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 10px;
  perspective: 900px;
}

.mr-modern .kpi-card {
  --tc: #4f46e5;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid color-mix(in srgb, var(--tc) 24%, #e2e8f0);
  background: linear-gradient(160deg, color-mix(in srgb, var(--tc) 10%, #fff) 0%, #fff 70%);
  box-shadow:
    0 3px 0 color-mix(in srgb, var(--tc) 26%, #e2e8f0),
    0 12px 20px -16px color-mix(in srgb, var(--tc) 70%, transparent);
  transform: rotateX(var(--rx, 0deg)) rotateY(var(--ry, 0deg));
  transform-style: preserve-3d;
  transition:
    transform 0.18s ease-out,
    box-shadow 0.2s ease;
  animation: mrRise 0.4s ease-out backwards;
}

.mr-modern .kpi-card:nth-child(2) {
  animation-delay: 0.05s;
}

.mr-modern .kpi-card:nth-child(3) {
  animation-delay: 0.1s;
}

.mr-modern .kpi-card:nth-child(4) {
  animation-delay: 0.15s;
}

.mr-modern .kpi-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--tc), color-mix(in srgb, var(--tc) 40%, #fff));
}

.mr-modern .kpi-card::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.2s ease;
  background: radial-gradient(
    circle at var(--mx, 50%) var(--my, 50%),
    rgba(255, 255, 255, 0.75) 0%,
    transparent 60%
  );
}

.mr-modern .kpi-card:hover {
  box-shadow:
    0 5px 0 color-mix(in srgb, var(--tc) 34%, #e2e8f0),
    0 18px 28px -16px color-mix(in srgb, var(--tc) 80%, transparent);
}

.mr-modern .kpi-card:hover::after {
  opacity: 1;
}

.mr-modern .kpi-card--range {
  --tc: #2563eb;
}

.mr-modern .kpi-card--kinds {
  --tc: #7c3aed;
}

.mr-modern .kpi-card--pieces {
  --tc: #059669;
}

.mr-modern .kpi-card--days {
  --tc: #d97706;
}

.mr-modern .kpi-card__icon {
  width: 38px;
  height: 38px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 19px;
  color: #fff;
  border-radius: 11px;
  background: linear-gradient(145deg, color-mix(in srgb, var(--tc) 65%, #fff) 0%, var(--tc) 100%);
  box-shadow:
    0 3px 0 color-mix(in srgb, var(--tc) 70%, #0f172a),
    0 8px 14px -6px color-mix(in srgb, var(--tc) 80%, transparent),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
  transform: translateZ(18px);
}

.mr-modern .kpi-card__body {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.mr-modern .kpi-card__label {
  font-size: 11px;
  font-weight: 700;
  color: color-mix(in srgb, var(--tc) 70%, #334155);
}

.mr-modern .kpi-card__value {
  font-size: 20px;
  font-weight: 800;
  line-height: 1.2;
  color: #0f172a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-variant-numeric: tabular-nums;
  transform: translateZ(12px);
}

.mr-modern .kpi-card__value--mono {
  font-size: 14px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

/* ---------- パネル・テーブル ---------- */
.mr-modern .panel-mark {
  width: 22px;
  height: 22px;
  border-radius: 7px;
  background: linear-gradient(145deg, #86efac 0%, #16a34a 100%);
  box-shadow:
    0 2px 0 #14532d,
    0 6px 10px -5px rgba(22, 163, 74, 0.6);
}

.mr-modern .panel-mark--accent {
  background: linear-gradient(145deg, #5eead4 0%, #4f46e5 100%);
  box-shadow:
    0 2px 0 #312e81,
    0 6px 10px -5px rgba(79, 70, 229, 0.6);
}

.mr-modern .panel-title {
  font-size: 14px;
  font-weight: 800;
  color: #1e1b4b;
}

.mr-modern .table-frame {
  border-radius: 10px;
  border-color: #dcfce7;
  box-shadow: 0 10px 20px -18px rgba(22, 163, 74, 0.5);
}

.mr-modern .panel--matrix {
  border-radius: 12px;
  box-shadow:
    0 12px 24px -20px rgba(79, 70, 229, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.mr-modern .table-frame--matrix {
  border-color: #c7d2fe;
}

.mr-modern .tbl :deep(.el-table__body tr:hover > td.el-table__cell:first-child) {
  box-shadow: inset 3px 0 0 #4f46e5;
}

.mr-modern .tbl-summary :deep(.el-table__body tr:hover > td.el-table__cell:first-child) {
  box-shadow: inset 3px 0 0 #16a34a;
}

.mr-modern .piece-cell {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  min-height: 20px;
}

.mr-modern .piece-cell__bar {
  position: absolute;
  left: 0;
  top: 50%;
  height: 14px;
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(134, 239, 172, 0.35) 0%, rgba(22, 163, 74, 0.35) 100%);
  transform: translateY(-50%);
  transition: width 0.5s ease;
}

.mr-modern .piece-cell__num {
  position: relative;
  font-weight: 700;
  color: #14532d;
  font-variant-numeric: tabular-nums;
}

.mr-modern .qty-heat {
  display: inline-block;
  min-width: 100%;
  padding: 0 3px;
  text-align: right;
  font-variant-numeric: tabular-nums;
  border-radius: 5px;
}

.mr-modern .qty-heat--1 {
  color: #115e59;
  background: rgba(204, 251, 241, 0.6);
}

.mr-modern .qty-heat--2 {
  color: #115e59;
  font-weight: 600;
  background: rgba(153, 246, 228, 0.7);
}

.mr-modern .qty-heat--3 {
  color: #fff;
  font-weight: 700;
  background: rgba(20, 184, 166, 0.85);
}

.mr-modern .qty-heat--4 {
  color: #fff;
  font-weight: 800;
  background: linear-gradient(145deg, #4f46e5 0%, #0d9488 100%);
  box-shadow: 0 2px 6px -2px rgba(79, 70, 229, 0.6);
}

.mr-modern .omit-alert {
  border-radius: 10px;
}

@keyframes mrOrbFloat {
  0%,
  100% {
    transform: translate(0, 0) scale(1);
  }
  50% {
    transform: translate(24px, 12px) scale(1.12);
  }
}

@keyframes mrSheen {
  0%,
  60% {
    left: -40%;
  }
  100% {
    left: 130%;
  }
}

@keyframes mrIconFloat {
  0%,
  100% {
    transform: perspective(300px) rotateX(0deg) rotateY(0deg) translateY(0);
  }
  50% {
    transform: perspective(300px) rotateX(10deg) rotateY(-14deg) translateY(-2px);
  }
}

@keyframes mrRise {
  from {
    opacity: 0;
    translate: 0 8px;
  }
  to {
    opacity: 1;
    translate: 0 0;
  }
}

@media (max-width: 900px) {
  .mr-modern .kpi-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (prefers-reduced-motion: reduce) {
  .mr-modern .page-head-fx .fx-orb,
  .mr-modern .page-head-fx .fx-sheen,
  .mr-modern .page-icon,
  .mr-modern .kpi-card {
    animation: none;
  }

  .mr-modern .kpi-card {
    transform: none;
    transition: none;
  }
}
</style>
