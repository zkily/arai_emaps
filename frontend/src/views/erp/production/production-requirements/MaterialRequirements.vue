<template>
  <div class="material-requirements">
    <header class="page-head">
      <div class="page-head-main">
        <div class="page-icon" aria-hidden="true">
          <el-icon :size="18"><Box /></el-icon>
        </div>
        <div class="page-head-text">
          <h1 class="page-title">{{ t('productionRequirements.materialTitle') }}</h1>
        </div>
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

      <div v-if="summary" class="stat-chips">
        <span class="chip chip--range">{{ summary.date_start }} — {{ summary.date_end }}</span>
        <span class="chip chip--kinds">
          {{ t('productionRequirements.summaryKinds') }}
          <em>{{ summary.total_material_kinds }}</em>
        </span>
        <span class="chip chip--pieces">
          {{ t('productionRequirements.summaryTotalPieces') }}
          <em>{{ (summary.total_piece_count ?? 0).toLocaleString() }}</em>
        </span>
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
                {{ (row.piece_count ?? 0).toLocaleString() }}
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
                <span>{{ formatQtyCell(row, d) }}</span>
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
import { ref, onMounted } from 'vue'
import { Box, Calendar, DArrowLeft, DArrowRight, Printer } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import {
  fetchMaterialRequirementsSummary,
  type MaterialRequirementsSummaryItem,
  type MaterialRequirementsSummaryMeta,
  type MaterialRequirementsDailyMatrixRow,
} from '@/api/productionSchedule'

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

function initDefaultRange() {
  const start = dayjs().startOf('month').format('YYYY-MM-DD')
  const end = dayjs().format('YYYY-MM-DD')
  dateRange.value = [start, end]
}

/** 将集计期间设为相对当月的整月：-1 前月、0 今月、1 翌月 */
function applyQuickMonth(offsetMonths: -1 | 0 | 1) {
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
  const lblSpec = t('productionRequirements.colSpec')
  const lblTotal = t('productionRequirements.rowTotal')
  const title = t('productionRequirements.dailyMatrixTitle')
  const period =
    summary.value != null ? `${summary.value.date_start} — ${summary.value.date_end}` : ''

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
    const dateThs = dates
      .map((d) => `<th class="col-day">${escapeHtml(shortDateLabel(d))}</th>`)
      .join('')
    return `<thead><tr>
      <th class="col-mk">${escapeHtml(lblMaker)}</th>
      <th class="col-nm">${escapeHtml(lblName)}</th>
      <th class="col-sp">${escapeHtml(lblSpec)}</th>
      ${dateThs}
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
            return `<td class="td-num">${escapeHtml(cell)}</td>`
          })
          .join('')
        return `<tr>
          <td>${escapeHtml(row.material_manufacturer ?? '')}</td>
          <td>${escapeHtml(row.material_name ?? '')}</td>
          <td>${escapeHtml(row.standard_specification ?? '')}</td>
          ${tds}
          <td class="td-num">${escapeHtml((row.row_total ?? 0).toLocaleString())}</td>
        </tr>`
      })
      .join('')

    const pageBreak = mi < makers.length - 1 ? 'page-break-after: always; break-after: page;' : ''
    sections.push(`
      <section class="print-mfg" style="${pageBreak}">
        <header class="print-doc-hdr">
          <h1>${escapeHtml(title)}</h1>
          <p class="print-doc-meta">${escapeHtml(period)} &nbsp;|&nbsp; ${escapeHtml(lblMaker)}: <strong>${escapeHtml(maker || '—')}</strong></p>
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
    @page { size: A4 landscape; margin: 8mm; }
    * { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; }
    body {
      font-family: 'Segoe UI', 'Hiragino Sans', 'Hiragino Kaku Gothic ProN', 'Yu Gothic', Meiryo, sans-serif;
      color: #111;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }
    .print-mfg { padding: 0 0 3mm 0; }
    .print-doc-hdr {
      margin: 0 0 4mm 0;
      padding: 0 0 3mm 0;
      border-bottom: 0.75pt solid #94a3b8;
    }
    .print-doc-hdr h1 {
      font-size: 12.5pt;
      margin: 0 0 2.5mm 0;
      font-weight: 800;
      letter-spacing: -0.02em;
      color: #0f172a;
    }
    .print-doc-meta {
      font-size: 8.5pt;
      margin: 0;
      color: #475569;
      padding: 1.8mm 3mm;
      background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
      border: 0.5pt solid #cbd5e1;
      border-radius: 5pt;
      display: inline-block;
      line-height: 1.35;
    }
    .print-doc-meta strong { color: #1e293b; font-weight: 800; }
    .print-tbl-wrap {
      border-radius: 5pt;
      overflow: hidden;
      border: 0.55pt solid #94a3b8;
      background: #fff;
    }
    .print-tbl { width: 100%; border-collapse: collapse; table-layout: fixed; font-size: 7.25pt; }
    .print-tbl th, .print-tbl td {
      border: 0.45pt solid #cbd5e1;
      padding: 0.65mm 0.55mm;
      line-height: 1.78;
      vertical-align: middle;
      word-wrap: break-word;
      overflow-wrap: anywhere;
    }
    .print-tbl tbody tr:nth-child(even) { background: #f8fafc; }
    .print-tbl th {
      background: linear-gradient(180deg, #e8ecff 0%, #dbeafe 55%, #e0e7ff 100%);
      color: #1e293b;
      font-weight: 800;
      text-align: center;
      border-color: #a5b4fc;
      padding: 0.75mm 0.5mm;
    }
    .col-day { font-size: 6.5pt; padding: 0.6mm 0.35mm !important; line-height: 1.62; }
    .td-num, .col-tot { text-align: right; font-variant-numeric: tabular-nums; }
    .col-mk { width: 8%; }
    .col-nm { width: 12%; }
    .col-sp { width: 9%; }
    .col-tot { width: 5%; }
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

</style>
