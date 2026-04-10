<template>
  <div class="component-requirements">
    <header class="page-head">
      <div class="page-head-main">
        <div class="page-icon" aria-hidden="true">
          <el-icon :size="18"><Box /></el-icon>
        </div>
        <div class="page-head-text">
          <h1 class="page-title">{{ t('productionRequirements.componentTitle') }}</h1>
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
          {{ t('productionRequirements.componentKinds') }}
          <em>{{ summary.total_component_kinds }}</em>
        </span>
        <span class="chip chip--qty">
          {{ t('productionRequirements.totalRequiredQty') }}
          <em>{{ formatQty(summary.total_required_qty) }}</em>
        </span>
      </div>

      <section class="panel">
        <div class="panel-head">
          <span class="panel-mark" />
          <span class="panel-title">{{ t('productionRequirements.componentTitle') }}</span>
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
            :empty-text="hasSearched ? t('productionRequirements.noData') : t('productionRequirements.placeholder')"
          >
            <el-table-column prop="component_cd" :label="t('productionRequirements.colComponentCd')" width="80" show-overflow-tooltip align="center" />
            <el-table-column prop="component_name" :label="t('productionRequirements.colComponentName')" width="220" show-overflow-tooltip sortable />
            <el-table-column prop="component_uom" :label="t('productionRequirements.colUom')" width="60" align="center"/>
            <el-table-column prop="source_lot_count" :label="t('productionRequirements.colSourceLots')" width="100" align="right">
              <template #default="{ row }">
                {{ (row.source_lot_count ?? 0).toLocaleString() }}
              </template>
            </el-table-column>
            <el-table-column prop="required_qty" :label="t('productionRequirements.colRequiredQty')" width="120" align="right">
              <template #default="{ row }">
                {{ formatQty(row.required_qty) }}
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
            <span class="panel-title">{{ t('productionRequirements.componentDailyMatrixTitle') }}</span>
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
            :empty-text="t('productionRequirements.noData')"
          >
            <el-table-column prop="component_cd" :label="t('productionRequirements.colComponentCd')" fixed width="80" />
            <el-table-column prop="component_name" :label="t('productionRequirements.colComponentName')" fixed width="160" sortable/>
            <el-table-column prop="component_uom" :label="t('productionRequirements.colUom')" fixed width="55" align="center" />
            <el-table-column :label="t('productionRequirements.totalRequiredQty')" fixed width="90" align="right">
              <template #default="{ row }">
                {{ formatQty(row.row_total ?? 0) }}
              </template>
            </el-table-column>
            <el-table-column
              v-for="d in dailyDates"
              :key="d"
              min-width="80"
              align="right"
              label-class-name="matrix-day-col"
              class-name="matrix-day-col"
            >
              <template #header>
                <span :title="d">{{ shortDateLabel(d) }}</span>
              </template>
              <template #default="{ row }">
                <span>{{ formatQtyCell(row, d) }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </section>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Box, Calendar, DArrowLeft, DArrowRight, Printer } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import dayjs from 'dayjs'
import { ElMessage } from 'element-plus'
import {
  fetchComponentRequirementsSummary,
  type ComponentRequirementsSummaryItem,
  type ComponentRequirementsDailyMatrixRow,
  type ComponentRequirementsSummaryMeta,
} from '@/api/productionSchedule'

const { t } = useI18n()

const dateRange = ref<[string, string] | null>(null)
const loading = ref(false)
const hasSearched = ref(false)
const items = ref<ComponentRequirementsSummaryItem[]>([])
const summary = ref<ComponentRequirementsSummaryMeta | null>(null)
const dailyDates = ref<string[]>([])
const matrixRows = ref<ComponentRequirementsDailyMatrixRow[]>([])
const SUMMARY_TABLE_MAX_H = 320
const MATRIX_TABLE_MAX_H = 380

function initDefaultRange() {
  dateRange.value = [dayjs().startOf('month').format('YYYY-MM-DD'), dayjs().endOf('month').format('YYYY-MM-DD')]
}

function applyQuickMonth(offsetMonths: -1 | 0 | 1) {
  const base = dayjs().add(offsetMonths, 'month')
  dateRange.value = [base.startOf('month').format('YYYY-MM-DD'), base.endOf('month').format('YYYY-MM-DD')]
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

function qtyFor(row: ComponentRequirementsDailyMatrixRow, d: string): number {
  const v = row.by_date?.[d]
  if (v == null || Number.isNaN(v)) return 0
  return v
}

function formatQtyCell(row: ComponentRequirementsDailyMatrixRow, d: string) {
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

/** A4 横向・部品別日次矩阵を印刷（部品名・所要量合計・日別列） */
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
  const lblName = t('productionRequirements.colComponentName')
  const lblTotal = t('productionRequirements.totalRequiredQty')
  const title = t('productionRequirements.componentDailyMatrixTitle')
  const period =
    summary.value != null ? `${summary.value.date_start} — ${summary.value.date_end}` : ''

  const rows = [...matrixRows.value].sort((a, b) => {
    const ca = a.component_cd ?? ''
    const cb = b.component_cd ?? ''
    const c0 = ca.localeCompare(cb, undefined, { sensitivity: 'base', numeric: true })
    if (c0 !== 0) return c0
    return (a.component_name ?? '').localeCompare(b.component_name ?? '', undefined, {
      sensitivity: 'base',
      numeric: true,
    })
  })

  const dateThs = dates
    .map((d) => `<th class="col-day">${escapeHtml(shortDateLabel(d))}</th>`)
    .join('')
  const thead = `<thead><tr>
      <th class="col-nm">${escapeHtml(lblName)}</th>
      <th class="col-tot">${escapeHtml(lblTotal)}</th>
      ${dateThs}
    </tr></thead>`

  const bodyRows = rows
    .map((row) => {
      const tds = dates
        .map((d) => {
          const cell = formatQtyCell(row, d)
          return `<td class="td-num td-day">${escapeHtml(cell)}</td>`
        })
        .join('')
      return `<tr>
          <td>${escapeHtml(row.component_name ?? '')}</td>
          <td class="td-num">${escapeHtml(formatQty(row.row_total ?? 0))}</td>
          ${tds}
        </tr>`
    })
    .join('')

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
    .col-day {
      font-size: 6.5pt;
      padding: 0.6mm 0.35mm !important;
      line-height: 1.62;
      min-width: 5ch;
      box-sizing: border-box;
    }
    .print-tbl td.td-day {
      min-width: 5ch;
      box-sizing: border-box;
    }
    .td-num, .col-tot { text-align: right; font-variant-numeric: tabular-nums; }
    .col-nm { width: 16%; }
    .col-tot { width: 5%; }
  `

  const bodyHtml = `
      <section class="print-mfg">
        <header class="print-doc-hdr">
          <h1>${escapeHtml(title)}</h1>
          <p class="print-doc-meta">${escapeHtml(period)}</p>
        </header>
        <div class="print-tbl-wrap">
          <table class="print-tbl">
            ${thead}
            <tbody>${bodyRows}</tbody>
          </table>
        </div>
      </section>`

  const html = `<!DOCTYPE html><html lang="ja"><head>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1"/>
    <title>${escapeHtml(title)}</title>
    <style>${styles}</style>
  </head><body>${bodyHtml}</body></html>`

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
  if (!range || !range[0] || !range[1]) {
    ElMessage.warning(t('productionRequirements.selectPeriod'))
    return
  }
  loading.value = true
  hasSearched.value = true
  try {
    const res = await fetchComponentRequirementsSummary({ date_start: range[0], date_end: range[1] })
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
    ElMessage.error(ax?.response?.data?.detail || t('productionRequirements.loadFailed'))
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
.component-requirements {
  --mr-bg: #eef1f6;
  --mr-card: #ffffff;
  --mr-border: #e2e6ee;
  --mr-text: #1a1d26;
  --mr-accent: linear-gradient(135deg, #3b82f6 0%, #6366f1 55%, #0d9488 100%);
  --mr-radius: 10px;
  --mr-shadow: 0 1px 3px rgba(15, 23, 42, 0.06), 0 4px 20px rgba(15, 23, 42, 0.04);

  min-height: calc(100vh - 100px);
  padding: 8px 10px 12px;
  background: var(--mr-bg);
}
.page-head {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}
.page-head-main {
  display: flex;
  align-items: center;
  gap: 10px;
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
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.35);
}
.page-title {
  margin: 0;
  font-size: 18px;
  font-weight: 800;
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
.control-left {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.ctl-label {
  font-size: 12px;
  font-weight: 600;
  color: #374151;
}
.month-quick {
  display: inline-flex;
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
  border: none;
  background: transparent;
  font-size: 12px;
  font-weight: 700;
  color: #3730a3;
  cursor: pointer;
}
.month-quick__btn:disabled {
  opacity: 0.48;
  cursor: not-allowed;
}
.month-quick__btn + .month-quick__btn {
  box-shadow: inset 1px 0 0 rgba(99, 102, 241, 0.22);
}
.month-quick__icon {
  font-size: 13px;
  color: #6366f1;
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
.btn-run {
  border: none;
  background: linear-gradient(135deg, #2563eb 0%, #4f46e5 50%, #0891b2 100%);
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.35);
}
.stat-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  margin-bottom: 8px;
}
.chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 11px;
  font-size: 12px;
  border-radius: 999px;
  border: 1px solid transparent;
}
.chip em {
  font-style: normal;
  font-weight: 800;
}
.chip--range {
  color: #1e40af;
  background: linear-gradient(180deg, #eff6ff 0%, #dbeafe 100%);
  border-color: #93c5fd;
}
.chip--kinds {
  color: #5b21b6;
  background: linear-gradient(180deg, #f5f3ff 0%, #ede9fe 100%);
  border-color: #c4b5fd;
}
.chip--qty {
  color: #065f46;
  background: linear-gradient(180deg, #ecfdf5 0%, #d1fae5 100%);
  border-color: #6ee7b7;
}
.omit-alert {
  margin-top: 8px;
}
.panel {
  margin-top: 4px;
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
.panel--matrix {
  margin-top: 10px;
  padding: 10px 10px 0;
  border-radius: 10px;
  border: 1px solid #c7d2fe;
  background: linear-gradient(165deg, rgba(238, 242, 255, 0.65) 0%, rgba(255, 255, 255, 0.9) 48%, rgba(240, 253, 250, 0.5) 100%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
}
.table-frame--matrix {
  overflow-x: auto;
  border-color: #c7d2fe;
  background: rgba(255, 255, 255, 0.85);
}
.tbl-matrix {
  min-width: max-content;
}
:deep(.tbl .el-table__header th) {
  font-size: 11px;
  font-weight: 600;
  color: #374151;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%) !important;
}
:deep(.tbl .el-table__body td) {
  font-size: 12px;
  padding: 4px 0;
}
:deep(.tbl .el-table__cell) {
  padding: 4px 8px;
}
:deep(.tbl-matrix th.matrix-day-col),
:deep(.tbl-matrix td.matrix-day-col) {
  min-width: 5ch;
  font-variant-numeric: tabular-nums;
}
</style>
