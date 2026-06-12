<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft,
  ArrowRight,
  Calendar,
  CircleCheck,
  Clock,
  Camera,
  DataLine,
  Edit,
  InfoFilled,
  Minus,
  Plus,
  Printer,
  RefreshLeft,
  User,
  VideoPause,
  VideoPlay,
  QuestionFilled,
} from '@element-plus/icons-vue'
import { setLocale, type LocaleType } from '@/i18n'
import { formatDateTimeJST, formatDateToYmdJST, localeForIntl } from '@/utils/dateFormat'
import { formatDurationMs, parseDefectsFromRow } from './inspectionActualPersist'
import MesBarcodeScanDialog from '../shared/MesBarcodeScanDialog.vue'
import { useInspectionMesCollection, type InspectionMgmtRow } from './useInspectionMesCollection'
import {
  inspectionDataSourceTagType,
  resolveInspectionDataSource,
} from './inspectionDataSource'
import { guardMesOperation } from '@/utils/mesOperationGuard'

defineOptions({ name: 'InspectionActualDataCollection' })

const { t, locale } = useI18n()
const mes = useInspectionMesCollection()
const {
  defectItems,
  defectItemGroups,
  loadingDefectItems,
  productionDay,
  loggedInInspectorLabel,
  canEditConfirmedHistoryRow,
  inspectorUserId,
  selectedProductCode,
  activePlanId,
  activeRow,
  inProgressRows,
  focusInProgressRow,
  resumeInProgressSession,
  canResumeSession,
  rowMesLockOwner,
  isPlanLocallyOperated,
  showSessionRecoveryAlert,
  inspectorNameById,
  products,
  completedRows,
  showPlanProductionCard,
  loadingProducts,
  loadingPlans,
  endDialogVisible,
  endDialogQty,
  endDialogSubmitting,
  defectTotal,
  canStart,
  canPause,
  canResume,
  canEnd,
  resumePulseActive,
  productSelectionLocked,
  canEditDefects,
  canCreate,
  canEdit,
  canDelete,
  canExport,
  showOfflineAlert,
  offlineAlertText,
  endDialogPreview,
  shiftProductionDay,
  setProductionDayToday,
  onStartProduction,
  onPauseProduction,
  onResumeProduction,
  openEndDialog,
  closeEndDialog,
  submitProductionEnd,
  defectCount,
  bumpDefect,
  defectItemLabel,
  defectRowsForRecord,
  productScanDialogVisible,
  canScanProduct,
  openProductScanDialog,
  onProductBarcodeScanned,
  workSession,
  formatElapsed,
  operationDisplayMs,
  rowWallElapsedSec,
  rowPausedAccumSec,
  pausedDisplay,
  timerPhase,
  timerPhaseLabel,
  formatWall,
  sessionWallStartTs,
  init,
  teardownLifecycle,
  confirmedEditDialogVisible,
  confirmedEditRow,
  confirmedEditForm,
  confirmedEditSaving,
  confirmedEditClearing,
  confirmedEditElapsedPreview,
  confirmedEditProductionDay,
  openConfirmedHistoryEdit,
  closeConfirmedHistoryEdit,
  submitConfirmedHistoryEdit,
  clearConfirmedHistoryMesAndSave,
  confirmedEditDefectCount,
  bumpConfirmedEditDefect,
} = mes

/** タブレット/スマホでは filterable オフ（タップでソフトキーボードを出さない） */
const touchSelectFilterable = ref(true)
let touchSelectMq: MediaQueryList | null = null

function syncTouchSelectFilterable(): void {
  if (typeof window === 'undefined') return
  touchSelectFilterable.value = !window.matchMedia('(hover: none) and (pointer: coarse)').matches
}

function onMesSelectVisibleChange(): void {
  if (touchSelectFilterable.value) return
  nextTick(() => {
    const ae = document.activeElement
    if (ae instanceof HTMLInputElement) ae.blur()
  })
}

const localeUi = ref<LocaleType>((locale.value as LocaleType) || 'ja')
watch(localeUi, (v) => setLocale(v))
watch(
  () => locale.value,
  (v) => {
    if (v === 'en' || v === 'ja' || v === 'zh' || v === 'vi') localeUi.value = v
  },
)
const intlLocale = computed(() => localeForIntl(localeUi.value))

const selectedProduct = computed(() => {
  const code = selectedProductCode.value
  if (!code) return null
  return products.value.find((p) => p.product_code === code) ?? null
})

const displayProductCd = computed(
  () => activeRow.value?.product_cd ?? selectedProduct.value?.product_code ?? '—',
)
const displayProductName = computed(
  () => activeRow.value?.product_name ?? selectedProduct.value?.product_name ?? '—',
)

const currentSession = computed(() => workSession())

const completedHistoryProductionQtyTotal = computed(() =>
  completedRows.value.reduce((sum, row) => {
    const qty = Number(row.actual_production_quantity ?? 0)
    return sum + (Number.isFinite(qty) ? Math.max(0, Math.round(qty)) : 0)
  }, 0),
)

function formatRecordTime(val: string | number | null | undefined): string {
  if (val == null) return '-'
  return formatDateTimeJST(typeof val === 'number' ? new Date(val) : val, intlLocale.value, {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatHistoryProductionDay(row: InspectionMgmtRow): string {
  const d = String(row.production_day ?? '').trim().slice(0, 10)
  if (/^\d{4}-\d{2}-\d{2}$/.test(d)) return d
  if (row.mes_production_started_at) {
    const fromStart = formatDateToYmdJST(new Date(row.mes_production_started_at))
    if (/^\d{4}-\d{2}-\d{2}$/.test(fromStart)) return fromStart
  }
  return '—'
}

function inspectorNameForUserId(userId: number | null | undefined): string {
  if (userId == null) return '-'
  return inspectorNameById(userId) || '-'
}

function dataSourceLabel(row: InspectionMgmtRow): string {
  const src = resolveInspectionDataSource(row)
  if (src === 'excel') return t('mesInspectionActual.dataSourceExcel')
  if (src === 'csv') return t('mesInspectionActual.dataSourceCsv')
  return t('mesInspectionActual.dataSourceMes')
}

function dataSourceTagType(row: InspectionMgmtRow) {
  return inspectionDataSourceTagType(resolveInspectionDataSource(row))
}

function formatDurationSec(sec: number | null | undefined): string {
  return formatDurationMs(Math.max(0, (sec ?? 0) * 1000))
}

/** 秒 → 分（整数・分単位表示） */
function formatSecondsAsMinutes(sec: number | null | undefined): string {
  const s = Math.max(0, sec ?? 0)
  return String(Math.round(s / 60))
}

function goHelpPage(): void {
  window.open('/mes/actualDataCollection/inspection/help', '_blank', 'noopener')
}

function historyDefectQty(row: InspectionMgmtRow): number {
  const stored = Number(row.defect_qty ?? 0)
  if (Number.isFinite(stored) && stored > 0) return Math.round(stored)
  return defectRowsForHistory(row).reduce((sum, d) => sum + d.qty, 0)
}

function defectRowsForHistory(rec: InspectionMgmtRow) {
  return defectRowsForRecord(parseDefectsFromRow(rec.mes_defect_by_item))
}

function formatDefectsCell(rec: InspectionMgmtRow): string {
  const rows = defectRowsForHistory(rec)
  if (!rows.length) return '—'
  return rows.map((r) => `${r.label} ${r.qty}`).join('、')
}

/** 不良率 = 不良数 ÷ 生産数（%・小数1位） */
function formatDefectRate(row: InspectionMgmtRow): string {
  const prod = Number(row.actual_production_quantity ?? 0)
  const defects = Number(row.defect_qty ?? 0)
  if (!Number.isFinite(prod) || prod <= 0) return '—'
  const pct = (Math.max(0, defects) / prod) * 100
  return `${pct.toFixed(1)}%`
}

/** 能率 = 生産数 ÷（稼働時間 − 一時停止）［時間単位・整数］ */
function formatEfficiencyRate(row: InspectionMgmtRow): string {
  const prod = Number(row.actual_production_quantity ?? 0)
  if (!Number.isFinite(prod) || prod <= 0) return '—'
  const netSec = Math.max(0, rowWallElapsedSec(row) - rowPausedAccumSec(row))
  if (netSec <= 0) return '—'
  const hours = netSec / 3600
  const rate = prod / hours
  if (!Number.isFinite(rate)) return '—'
  return String(Math.round(rate))
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function historyDefectCellForPrint(row: InspectionMgmtRow): string {
  const qty = historyDefectQty(row)
  if (qty <= 0) return '—'
  return String(qty)
}

function buildCompletedHistoryPrintHtml(rows: InspectionMgmtRow[]): string {
  const day = (productionDay.value ?? '').trim()
  const title = t('mesInspectionActual.historyTitle')
  const dayLabel = t('mesInspectionActual.productionDay')
  const printedLabel = t('mesInspectionActual.printedAt')
  const rowCountLabel = t('mesInspectionActual.printRowCount', { n: rows.length })

  const headers = [
    t('mesInspectionActual.productionDay'),
    t('mesInspectionActual.inspector'),
    t('mesInspectionActual.dataSource'),
    t('mesInspectionActual.productName'),
    t('mesInspectionActual.productionQty'),
    t('mesInspectionActual.defectQty'),
    t('mesInspectionActual.defectRate'),
    t('mesInspectionActual.efficiencyRate'),
    t('mesInspectionActual.productionStart'),
    t('mesInspectionActual.productionEnd'),
    t('mesInspectionActual.elapsedMinutes'),
    t('mesInspectionActual.pausedAccumMinutes'),
  ]

  const th = headers.map((h) => `<th>${escapeHtml(h)}</th>`).join('')
  const numericColIndexes = new Set([4, 5, 6, 7, 10, 11])
  const body = rows
    .map((row) => {
      const cells = [
        formatHistoryProductionDay(row),
        inspectorNameForUserId(row.mes_inspector_user_id),
        dataSourceLabel(row),
        row.product_name || '—',
        String(row.actual_production_quantity ?? 0),
        historyDefectCellForPrint(row),
        formatDefectRate(row),
        formatEfficiencyRate(row),
        formatRecordTime(row.mes_production_started_at),
        formatRecordTime(row.mes_production_ended_at),
        formatSecondsAsMinutes(rowWallElapsedSec(row)),
        formatSecondsAsMinutes(rowPausedAccumSec(row)),
      ]
      return `<tr>${cells
        .map((c, i) => {
          const cls = numericColIndexes.has(i) ? ' class="num"' : ''
          return `<td${cls}>${escapeHtml(c)}</td>`
        })
        .join('')}</tr>`
    })
    .join('')

  const printedAt = formatDateTimeJST(new Date(), intlLocale.value, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })

  return `<!DOCTYPE html>
<html lang="${String(locale.value)}">
<head>
  <meta charset="utf-8" />
  <title>${escapeHtml(title)}</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: "Segoe UI", "Hiragino Sans", "Yu Gothic UI", Meiryo, sans-serif; margin: 12mm; color: #111; font-size: 11px; }
    h1 { margin: 0 0 4px; font-size: 16px; }
    .meta { margin: 0 0 12px; color: #444; font-size: 11px; }
    table { width: 100%; border-collapse: collapse; }
    th, td { border: 1px solid #333; padding: 3px 4px; text-align: left; vertical-align: top; font-size: 10px; }
    th { background: #e8f5f3; font-weight: 700; }
    td.num { text-align: right; }
    @media print { body { margin: 8mm; } }
  </style>
</head>
<body>
  <h1>${escapeHtml(title)}</h1>
  <p class="meta">${escapeHtml(dayLabel)}: ${escapeHtml(day || '—')} &nbsp;|&nbsp; ${escapeHtml(printedLabel)}: ${escapeHtml(printedAt)} &nbsp;|&nbsp; ${escapeHtml(rowCountLabel)}</p>
  <table>
    <thead><tr>${th}</tr></thead>
    <tbody>${body}</tbody>
  </table>
</body>
</html>`
}

const historyPrintFrameRef = ref<HTMLIFrameElement | null>(null)

function runPrintOnWindow(win: Window): void {
  const trigger = () => {
    try {
      win.focus()
      win.print()
    } catch (e) {
      console.error(e)
      ElMessage.error(t('mesInspectionActual.printFailed'))
    }
  }
  if (win.document.readyState === 'complete') {
    setTimeout(trigger, 250)
  } else {
    win.addEventListener('load', () => setTimeout(trigger, 250), { once: true })
  }
}

function printCompletedHistoryTable(): void {
  if (!guardMesOperation(canExport)) return
  const rows = completedRows.value
  if (!rows.length) return

  const html = buildCompletedHistoryPrintHtml(rows)

  const iframe = historyPrintFrameRef.value
  const iframeWin = iframe?.contentWindow
  if (iframe && iframeWin) {
    const doc = iframe.contentDocument ?? iframeWin.document
    doc.open()
    doc.write(html)
    doc.close()
    runPrintOnWindow(iframeWin)
    return
  }

  const printWindow = window.open('about:blank', '_blank')
  if (!printWindow) {
    ElMessage.warning(t('mesInspectionActual.printBlocked'))
    return
  }
  printWindow.document.open()
  printWindow.document.write(html)
  printWindow.document.close()
  runPrintOnWindow(printWindow)
  printWindow.addEventListener(
    'afterprint',
    () => {
      try {
        printWindow.close()
      } catch {
        /* ignore */
      }
    },
    { once: true },
  )
}

const localeIconOptions: { value: LocaleType; label: string; glyph: string }[] = [
  { value: 'ja', label: 'JP', glyph: 'JP' },
  { value: 'en', label: 'EN', glyph: 'EN' },
  { value: 'zh', label: 'ZH', glyph: 'ZH' },
  { value: 'vi', label: 'VI', glyph: 'VI' },
]

onMounted(async () => {
  syncTouchSelectFilterable()
  if (typeof window !== 'undefined') {
    touchSelectMq = window.matchMedia('(hover: none) and (pointer: coarse)')
    touchSelectMq.addEventListener('change', syncTouchSelectFilterable)
  }
  await init()
})

onUnmounted(() => {
  touchSelectMq?.removeEventListener('change', syncTouchSelectFilterable)
  teardownLifecycle()
})
</script>


<template>

  <div class="inspection-actual-page">
    <header class="page-head">
      <div class="page-head-row">
        <div class="page-head-main">
          <h1 class="page-title">
            <span class="page-title__icon" aria-hidden="true">
              <el-icon><DataLine /></el-icon>
            </span>
            <span class="page-title__text">{{ t('mesInspectionActual.title') }}</span>
            <el-tooltip :content="t('mesInspectionActual.helpOpen')" placement="bottom">
              <button
                type="button"
                class="page-title__help"
                :aria-label="t('mesInspectionActual.helpOpen')"
                @click="goHelpPage"
              >
                <el-icon :size="18"><QuestionFilled /></el-icon>
              </button>
            </el-tooltip>
          </h1>
        </div>
        <div
          class="page-head-locale"
          role="radiogroup"
          :aria-label="t('mesInspectionActual.localeInline')"
        >
          <el-tooltip
            v-for="opt in localeIconOptions"
            :key="opt.value"
            :content="opt.label"
            placement="bottom"
          >
            <button
              type="button"
              role="radio"
              class="locale-glyph-btn"
              :class="{ 'locale-glyph-btn--active': localeUi === opt.value }"
              :aria-label="opt.label"
              :aria-checked="localeUi === opt.value"
              @click="localeUi = opt.value"
            >
              <span class="locale-glyph-btn__glyph" aria-hidden="true">{{ opt.glyph }}</span>
            </button>
          </el-tooltip>
        </div>
      </div>
    </header>

    <el-card shadow="never" class="toolbar-card" role="region" :aria-label="t('mesInspectionActual.title')">
      <div class="toolbar-layout">
        <div class="toolbar-field-row toolbar-field-row--day">
          <span class="toolbar-field-row__icon" aria-hidden="true">
            <el-icon><Calendar /></el-icon>
          </span>
          <span class="toolbar-field-row__label">{{ t('mesInspectionActual.productionDay') }}</span>
          <div class="toolbar-day-wrap">
            <el-date-picker
              v-model="productionDay"
              type="date"
              value-format="YYYY-MM-DD"
              :editable="false"
              teleported
              class="toolbar-control toolbar-day-picker"
            />
            <div class="toolbar-day-shortcuts">
              <el-tooltip :content="t('mesInspectionActual.dayPrev')" placement="top">
                <el-button
                  type="default"
                  size="small"
                  circle
                  :icon="ArrowLeft"
                  :aria-label="t('mesInspectionActual.dayPrev')"
                  @click="shiftProductionDay(-1)"
                />
              </el-tooltip>
              <el-button
                type="default"
                size="small"
                plain
                class="toolbar-day-today-btn"
                @click="setProductionDayToday"
              >
                {{ t('mesInspectionActual.dayToday') }}
              </el-button>
              <el-tooltip :content="t('mesInspectionActual.dayNext')" placement="top">
                <el-button
                  type="default"
                  size="small"
                  circle
                  :icon="ArrowRight"
                  :aria-label="t('mesInspectionActual.dayNext')"
                  @click="shiftProductionDay(1)"
                />
              </el-tooltip>
            </div>
          </div>
        </div>

        <div class="toolbar-field-row toolbar-field-row--inspector">
          <span class="toolbar-field-row__icon" aria-hidden="true">
            <el-icon><User /></el-icon>
          </span>
          <span class="toolbar-field-row__label">{{ t('mesInspectionActual.inspector') }}</span>
          <el-input
            :model-value="loggedInInspectorLabel"
            disabled
            class="toolbar-control toolbar-inspector-select"
            :placeholder="t('mesInspectionActual.inspectorPlaceholder')"
          />
        </div>

        <div class="toolbar-field-row toolbar-field-row--product">
          <span class="toolbar-field-row__icon toolbar-field-row__icon--machine" aria-hidden="true">
            <el-icon><DataLine /></el-icon>
          </span>
          <span class="toolbar-field-row__label">{{ t('mesInspectionActual.selectProduct') }}</span>
          <div class="toolbar-product-scan-wrap">
            <el-select
              v-model="selectedProductCode"
              :filterable="touchSelectFilterable"
              clearable
              teleported
              class="toolbar-control product-select-toolbar"
              :placeholder="t('mesInspectionActual.productPlaceholder')"
              :loading="loadingProducts"
              :disabled="productSelectionLocked"
              @visible-change="onMesSelectVisibleChange"
            >
              <el-option
                v-for="p in products"
                :key="p.product_code"
                :label="`${p.product_code} · ${p.product_name}`"
                :value="p.product_code"
              />
            </el-select>
            <el-button
              type="warning"
              plain
              class="toolbar-product-scan-btn"
              :disabled="!canScanProduct || loadingProducts"
              @click="openProductScanDialog"
            >
              <el-icon><Camera /></el-icon>
              {{ t('mesInspectionActual.btnScanCode') }}
            </el-button>
          </div>
        </div>
      </div>
    </el-card>

    <div
      v-if="inProgressRows.length > 0"
      class="in-progress-strip"
      role="region"
      :aria-label="t('mesInspectionActual.inProgressStripTitle')"
    >
      <span class="in-progress-strip__title">{{ t('mesInspectionActual.inProgressStripTitle') }}</span>
      <div class="in-progress-strip__chips">
        <div
          v-for="row in inProgressRows"
          :key="row.id"
          class="in-progress-chip-wrap"
          :class="{ 'in-progress-chip-wrap--active': row.id === activePlanId }"
        >
          <div class="in-progress-chip" role="button" tabindex="0" @click="focusInProgressRow(row)" @keyup.enter="focusInProgressRow(row)">
            <div class="in-progress-chip__top">
              <span class="in-progress-chip__product">{{
                row.product_name || row.product_cd || '—'
              }}</span>
              <el-button
                v-if="canResumeSession(row)"
                size="small"
                type="primary"
                plain
                class="in-progress-chip__resume-btn"
                @click.stop="resumeInProgressSession(row)"
              >
                {{ t('mesInspectionActual.btnResume') }}
              </el-button>
            </div>
            <span class="in-progress-chip__inspector">{{
              inspectorNameById(row.mes_inspector_user_id) || t('mesInspectionActual.inspectorMissing')
            }}</span>
            <span v-if="rowMesLockOwner(row) === 'other'" class="in-progress-chip__lock-hint">
              {{ t('mesInspectionActual.sessionLockedByOtherTerminalShort') }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showOfflineAlert" class="offline-strip" role="status">
      <span class="offline-strip__dot" aria-hidden="true" />
      {{ offlineAlertText }}
    </div>

    <div v-loading="loadingPlans" class="plan-board">
      <template v-if="!selectedProductCode">
        <el-empty :description="t('mesInspectionActual.emptySelectProduct')" />
      </template>
      <template v-else-if="showPlanProductionCard">
      <el-alert
        v-if="showSessionRecoveryAlert"
        type="info"
        :closable="false"
        show-icon
        class="session-recovery-alert"
      >
        <template #title>{{ t('mesInspectionActual.sessionRecoveryTitle') }}</template>
        <p class="session-recovery-alert__text">{{ t('mesInspectionActual.sessionRecoveryHint') }}</p>
        <el-button
          v-if="activeRow"
          type="primary"
          size="small"
          class="session-recovery-alert__btn"
          @click="resumeInProgressSession(activeRow)"
        >
          {{ t('mesInspectionActual.btnResumeSession') }}
        </el-button>
      </el-alert>
      <el-card shadow="hover" class="plan-row-card">
        <div class="plan-row">
          <div class="plan-row__head">
            <el-tag size="small" effect="plain" type="primary">{{ displayProductCd }}</el-tag>
            <el-tag
              v-if="currentSession"
              size="small"
              effect="plain"
              :type="
                timerPhase(currentSession) === 'running'
                  ? 'success'
                  : timerPhase(currentSession) === 'paused'
                    ? 'warning'
                    : 'info'
              "
            >
              {{ timerPhaseLabel(currentSession) }}
            </el-tag>
          </div>

          <div class="plan-row__meta">
            <div class="plan-meta-primary">
              <span class="plan-product-name" :title="displayProductName || ''">{{
                displayProductName || '—'
              }}</span>
            </div>
            <div class="plan-meta-chips">
              <span class="plan-chip plan-chip--qty">
                <span class="plan-chip__label">{{ t('mesInspectionActual.defectTotal') }}</span>
                <span class="plan-chip__value">{{ defectTotal }}</span>
              </span>
              <div class="plan-meta-field plan-meta-field--operator">
              <span class="plan-meta-field__label">
                <el-icon class="plan-meta-field__icon" aria-hidden="true"><User /></el-icon>
                {{ t('mesInspectionActual.inspector') }}
              </span>
              <el-input
                :model-value="loggedInInspectorLabel"
                disabled
                class="plan-field__control plan-field__control--operator"
                :placeholder="t('mesInspectionActual.inspectorPlaceholder')"
              />
              </div>
            </div>
          </div>

          <div class="plan-row__ops">
            <div class="plan-row__timer">
              <div
                class="timer-compact"
                :class="`timer-compact--${currentSession ? timerPhase(currentSession) : 'idle'}`"
              >
                <div class="timer-compact__top">
                  <span class="timer-compact__label">
                    <el-icon class="timer-compact__label-icon" aria-hidden="true"><Clock /></el-icon>
                    {{ t('mesInspectionActual.elapsed') }}
                  </span>
                  <span class="timer-compact__phase">{{
                    currentSession ? timerPhaseLabel(currentSession) : t('mesInspectionActual.timerIdle')
                  }}</span>
                </div>
                <div class="timer-compact__readout-row">
                  <div
                    class="timer-compact__readout"
                  >
                    {{ formatElapsed(currentSession ? operationDisplayMs(currentSession) : 0) }}
                  </div>
                  <div v-if="currentSession && sessionWallStartTs(currentSession) != null" class="timer-compact__pause-side">
                    <span class="timer-compact__pause-label">{{ t('mesInspectionActual.pausedAccum') }}</span>
                    <span class="timer-compact__pause-value">{{ pausedDisplay }}</span>
                  </div>
                </div>
                <div class="timer-compact__walls">
                  <span>{{
                    formatWall(currentSession ? sessionWallStartTs(currentSession) : null)
                  }}</span>
                  <span class="timer-compact__sep">→</span>
                  <span>{{ formatWall(currentSession?.wallEnd ?? null) }}</span>
                </div>
              </div>
            </div>
            <div class="plan-row__actions">
              <el-button
                class="plan-act-btn plan-act-btn--start"
                :disabled="!canStart"
                @click="onStartProduction"
              >
                <el-icon><VideoPlay /></el-icon>
                {{ t('mesInspectionActual.btnStart') }}
              </el-button>
              <el-button
                v-if="canPause"
                class="plan-act-btn plan-act-btn--pause"
                @click="onPauseProduction"
              >
                <el-icon><VideoPause /></el-icon>
                {{ t('mesInspectionActual.btnPause') }}
              </el-button>
              <el-button
                v-else-if="canResume"
                class="plan-act-btn plan-act-btn--resume"
                :class="{ 'plan-act-btn--resume-pulse': resumePulseActive }"
                :aria-label="
                  resumePulseActive
                    ? t('mesInspectionActual.btnResumePulseAria')
                    : t('mesInspectionActual.btnResume')
                "
                @click="onResumeProduction"
              >
                <el-icon><VideoPlay /></el-icon>
                {{ t('mesInspectionActual.btnResume') }}
              </el-button>
              <el-button v-else class="plan-act-btn plan-act-btn--pause" disabled>
                <el-icon><VideoPause /></el-icon>
                {{ t('mesInspectionActual.btnPause') }}
              </el-button>
              <el-button
                class="plan-act-btn plan-act-btn--end"
                :disabled="!canEnd"
                :title="canResume ? t('mesInspectionActual.endBlockedWhilePaused') : undefined"
                @click="openEndDialog"
              >
                <el-icon><CircleCheck /></el-icon>
                {{ t('mesInspectionActual.btnEnd') }}
              </el-button>
            </div>
          </div>

          <div class="defect-panel">
            <div class="defect-panel__head">
              <h3 class="defect-panel__title">{{ t('mesInspectionActual.defectByItem') }}</h3>
              <p class="defect-panel__hint">{{ t('mesInspectionActual.defectHint') }}</p>
            </div>
            <div v-loading="loadingDefectItems" class="defect-grid-by-process">
              <p v-if="!loadingDefectItems && defectItems.length === 0" class="defect-panel__empty">
                {{ t('mesInspectionActual.defectItemsEmpty') }}
              </p>
              <section
                v-for="group in defectItemGroups"
                :key="group.processCd"
                class="defect-process-group"
              >
                <header class="defect-process-group__head">
                  <span class="defect-process-group__label">{{
                    t('mesInspectionActual.attributableProcess')
                  }}</span>
                  <span class="defect-process-group__name">{{
                    group.processName || group.processCd || '—'
                  }}</span>
                </header>
                <div class="defect-grid">
                  <div
                    v-for="item in group.items"
                    :key="item.id"
                    class="defect-cell"
                    :class="{ 'defect-cell--active': defectCount(item.id) > 0 }"
                  >
                    <span class="defect-cell__label">{{ defectItemLabel(item) }}</span>
                    <div class="defect-stepper">
                      <el-button
                        class="defect-stepper__btn"
                        circle
                        :icon="Minus"
                        :disabled="defectCount(item.id) <= 0 || !canEditDefects"
                        @click="bumpDefect(item.id, -1)"
                      />
                      <span class="defect-stepper__val">{{ defectCount(item.id) }}</span>
                      <el-button
                        class="defect-stepper__btn"
                        circle
                        type="primary"
                        :icon="Plus"
                        :disabled="!canEditDefects"
                        @click="bumpDefect(item.id, 1)"
                      />
                    </div>
                  </div>
                </div>
              </section>
            </div>
          </div>
        </div>
      </el-card>
      </template>
    </div>

    <section v-if="completedRows.length > 0" class="inspection-history-section">
        <el-card shadow="never" class="inspection-history-table-card">
          <header class="inspection-history-table-card__head">
            <div class="inspection-history-table-card__title-row">
              <span class="inspection-history-table-card__icon" aria-hidden="true">
                <el-icon :size="16"><CircleCheck /></el-icon>
              </span>
              <h2 class="inspection-history-table-card__title">
                {{ t('mesInspectionActual.historyTitle') }}
              </h2>
              <span class="inspection-history-table-card__qty-total">
                <span class="inspection-history-table-card__qty-total-label">{{
                  t('mesInspectionActual.historyProductionQtyTotal')
                }}</span>
                <span class="inspection-history-table-card__qty-total-value">{{
                  completedHistoryProductionQtyTotal.toLocaleString()
                }}</span>
              </span>
            </div>
            <div class="inspection-history-table-card__actions">
              <span class="inspection-history-table-card__count">{{ completedRows.length }}</span>
              <el-button v-if="canExport" size="small" :icon="Printer" @click="printCompletedHistoryTable">
                {{ t('mesInspectionActual.btnPrintHistory') }}
              </el-button>
            </div>
          </header>
          <div class="inspection-history-table-wrap">
            <el-table
              :data="completedRows"
              stripe
              size="small"
              class="inspection-history-table inspection-history-table--compact"
              row-key="id"
              table-layout="fixed"
            >
              <el-table-column
                :label="t('mesInspectionActual.productionDay')"
                width="92"
                fixed="left"
                show-overflow-tooltip
              >
                <template #default="{ row }">
                  <span class="hist-cell-day">{{ formatHistoryProductionDay(row) }}</span>
                </template>
              </el-table-column>
              <el-table-column
                :label="t('mesInspectionActual.inspector')"
                width="88"
                show-overflow-tooltip
              >
                <template #default="{ row }">
                  <span class="hist-cell-inspector">
                    {{ inspectorNameForUserId(row.mes_inspector_user_id) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column
                :label="t('mesInspectionActual.dataSource')"
                width="72"
                align="center"
              >
                <template #default="{ row }">
                  <el-tag
                    :type="dataSourceTagType(row)"
                    size="small"
                    effect="light"
                    class="hist-cell-source-tag"
                  >
                    {{ dataSourceLabel(row) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column
                :label="t('mesInspectionActual.productName')"
                min-width="96"
                show-overflow-tooltip
              >
                <template #default="{ row }">
                  <span class="hist-cell-name">{{ row.product_name || '—' }}</span>
                </template>
              </el-table-column>
              <el-table-column
                :label="t('mesInspectionActual.productionQty')"
                width="68"
                align="right"
              >
                <template #default="{ row }">
                  <span class="hist-cell-qty">{{
                    (row.actual_production_quantity ?? 0).toLocaleString()
                  }}</span>
                </template>
              </el-table-column>
              <el-table-column
                :label="t('mesInspectionActual.defectQty')"
                width="56"
                align="right"
              >
                <template #default="{ row }">
                  <el-tooltip
                    v-if="historyDefectQty(row) > 0"
                    :content="formatDefectsCell(row)"
                    placement="top"
                    :show-after="200"
                  >
                    <span class="hist-cell-defect-qty">{{ historyDefectQty(row).toLocaleString() }}</span>
                  </el-tooltip>
                  <span v-else class="hist-cell-empty">—</span>
                </template>
              </el-table-column>
              <el-table-column
                :label="t('mesInspectionActual.defectRate')"
                width="68"
                align="right"
              >
                <template #default="{ row }">
                  <span class="hist-cell-rate">{{ formatDefectRate(row) }}</span>
                </template>
              </el-table-column>
              <el-table-column
                :label="t('mesInspectionActual.efficiencyRate')"
                width="56"
                align="right"
              >
                <template #default="{ row }">
                  <span class="hist-cell-efficiency">{{ formatEfficiencyRate(row) }}</span>
                </template>
              </el-table-column>
              <el-table-column
                :label="t('mesInspectionActual.productionStart')"
                width="112"
              >
                <template #default="{ row }">
                  <span class="hist-cell-time">{{ formatRecordTime(row.mes_production_started_at) }}</span>
                </template>
              </el-table-column>
              <el-table-column
                :label="t('mesInspectionActual.productionEnd')"
                width="112"
              >
                <template #default="{ row }">
                  <span class="hist-cell-time">{{ formatRecordTime(row.mes_production_ended_at) }}</span>
                </template>
              </el-table-column>
              <el-table-column
                :label="t('mesInspectionActual.elapsedMinutes')"
                width="72"
                align="right"
              >
                <template #default="{ row }">
                  <span class="hist-cell-duration hist-cell-duration--active">{{
                    formatSecondsAsMinutes(rowWallElapsedSec(row))
                  }}</span>
                </template>
              </el-table-column>
              <el-table-column
                :label="t('mesInspectionActual.pausedAccumMinutes')"
                width="72"
                align="right"
              >
                <template #default="{ row }">
                  <span
                    class="hist-cell-duration"
                    :class="{ 'hist-cell-duration--muted': !rowPausedAccumSec(row) }"
                  >
                    {{ formatSecondsAsMinutes(rowPausedAccumSec(row)) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column
                :label="t('mesInspectionActual.historyActions')"
                width="52"
                fixed="right"
                align="center"
              >
                <template #default="{ row }">
                  <el-tooltip
                    v-if="canEditConfirmedHistoryRow(row)"
                    :content="t('mesInspectionActual.btnEditConfirmed')"
                    placement="top"
                    :show-after="300"
                  >
                    <el-button
                      link
                      type="primary"
                      size="small"
                      class="hist-cell-action-btn"
                      :aria-label="t('mesInspectionActual.btnEditConfirmed')"
                      @click="openConfirmedHistoryEdit(row)"
                    >
                      <el-icon><Edit /></el-icon>
                    </el-button>
                  </el-tooltip>
                  <span v-else class="hist-cell-empty">—</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <iframe
            ref="historyPrintFrameRef"
            class="inspection-history-print-frame"
            title="print"
            tabindex="-1"
            aria-hidden="true"
          />
        </el-card>
    </section>

    <el-dialog
      v-model="endDialogVisible"
      width="min(96vw, 440px)"
      :show-close="true"
      append-to-body
      destroy-on-close
      align-center
      class="production-end-dialog"
      @close="closeEndDialog"
    >
      <template #header>
        <header class="end-dialog-header">
          <span class="end-dialog-header__icon" aria-hidden="true">
            <el-icon :size="20"><CircleCheck /></el-icon>
          </span>
          <div class="end-dialog-header__text">
            <h3 class="end-dialog-header__title">{{ t('mesInspectionActual.endDialogTitle') }}</h3>
            <p class="end-dialog-header__sub">{{ t('mesInspectionActual.endDialogIntro') }}</p>
          </div>
        </header>
      </template>

      <div v-if="endDialogPreview" class="end-dialog-body">
        <section class="end-dialog-product-card">
          <span class="end-dialog-product-card__cd">{{ displayProductCd }}</span>
          <span class="end-dialog-product-card__name">{{ displayProductName }}</span>
        </section>
        <div class="end-dialog-stats">
          <div class="end-dialog-stat">
            <span class="end-dialog-stat__label">{{ t('mesInspectionActual.inspector') }}</span>
            <span class="end-dialog-stat__value">{{ endDialogPreview.inspectorName }}</span>
          </div>
          <div class="end-dialog-stat">
            <span class="end-dialog-stat__label">{{ t('mesInspectionActual.productionStart') }}</span>
            <span class="end-dialog-stat__value">{{ formatRecordTime(endDialogPreview.wallStart) }}</span>
          </div>
          <div class="end-dialog-stat">
            <span class="end-dialog-stat__label">{{ t('mesInspectionActual.productionEnd') }}</span>
            <span class="end-dialog-stat__value">{{ formatRecordTime(endDialogPreview.wallEnd) }}</span>
          </div>
          <div class="end-dialog-stat">
            <span class="end-dialog-stat__label">{{ t('mesInspectionActual.elapsed') }}</span>
            <span class="end-dialog-stat__value">{{ formatDurationMs(endDialogPreview.activeMs) }}</span>
          </div>
          <div
            v-if="endDialogPreview.defectTotal > 0"
            class="end-dialog-stat end-dialog-stat--defect"
          >
            <span class="end-dialog-stat__label">{{ t('mesInspectionActual.defectTotal') }}</span>
            <span class="end-dialog-stat__value">{{ endDialogPreview.defectTotal }}</span>
          </div>
        </div>
        <section
          v-if="endDialogPreview.defectTotal > 0 && defectRowsForRecord(endDialogPreview.defects).length"
          class="end-dialog-defects"
        >
          <span class="end-dialog-defects__label">{{ t('mesInspectionActual.defectByItem') }}</span>
          <div class="end-dialog-defects__chips">
            <span
              v-for="row in defectRowsForRecord(endDialogPreview.defects)"
              :key="row.id"
              class="end-dialog-defect-chip"
            >
              <span class="end-dialog-defect-chip__name">{{ row.label }}</span>
              <strong class="end-dialog-defect-chip__qty">{{ row.qty }}</strong>
            </span>
          </div>
        </section>

        <section class="end-dialog-qty">
          <label class="end-dialog-qty__label" for="inspection-end-qty-input">
            {{ t('mesInspectionActual.productionQty') }}
          </label>
          <el-input
            id="inspection-end-qty-input"
            v-model="endDialogQty"
            class="end-dialog-qty__input"
            size="large"
            inputmode="numeric"
            :placeholder="t('mesInspectionActual.productionQtyPlaceholder')"
            clearable
            @keyup.enter="submitProductionEnd"
          />
        </section>
      </div>

      <template v-if="endDialogPreview" #footer>
        <div class="end-dialog-footer">
          <el-button
            class="end-dialog-footer__btn end-dialog-footer__btn--cancel"
            :disabled="endDialogSubmitting"
            @click="closeEndDialog"
          >
            {{ t('common.cancel') }}
          </el-button>
          <el-button
            class="end-dialog-footer__btn end-dialog-footer__btn--confirm"
            type="primary"
            :loading="endDialogSubmitting"
            @click="submitProductionEnd"
          >
            <el-icon class="end-dialog-footer__btn-icon"><CircleCheck /></el-icon>
            {{ t('mesInspectionActual.btnConfirmEnd') }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog
      v-model="confirmedEditDialogVisible"
      width="min(96vw, 520px)"
      append-to-body
      destroy-on-close
      align-center
      class="confirmed-edit-dialog"
      @close="closeConfirmedHistoryEdit"
    >
      <template #header>
        <div class="confirmed-edit-header">
          <div class="confirmed-edit-header__main">
            <span class="confirmed-edit-header__icon" aria-hidden="true">
              <el-icon :size="18"><Edit /></el-icon>
            </span>
            <span class="confirmed-edit-header__text">
              <span class="confirmed-edit-header__title">{{
                t('mesInspectionActual.confirmedEditDialogTitle')
              }}</span>
              <span class="confirmed-edit-header__sub">{{ t('mesInspectionActual.historyTitle') }}</span>
            </span>
          </div>
          <el-button
            v-if="confirmedEditRow && canDelete"
            class="confirmed-edit-header__clear"
            size="small"
            :loading="confirmedEditClearing"
            :disabled="confirmedEditSaving || confirmedEditClearing"
            @click="clearConfirmedHistoryMesAndSave"
          >
            <el-icon class="confirmed-edit-header__clear-icon"><RefreshLeft /></el-icon>
            {{ t('mesInspectionActual.btnClearMesActual') }}
          </el-button>
        </div>
      </template>
      <div v-if="confirmedEditRow && confirmedEditForm" class="confirmed-edit-body">
        <div class="confirmed-edit-hero">
          <span class="confirmed-edit-badge">{{ t('mesInspectionActual.historyTitle') }}</span>
          <span class="confirmed-edit-hero__product">
            <strong>{{ confirmedEditRow.product_cd || '—' }}</strong>
            <span class="confirmed-edit-hero__sep">·</span>
            {{ confirmedEditRow.product_name || '—' }}
          </span>
        </div>
        <el-form label-position="top" size="small" class="confirmed-edit-form">
          <section class="confirmed-edit-section confirmed-edit-section--people">
            <h4 class="confirmed-edit-section__title">
              <el-icon :size="14"><User /></el-icon>
              {{ t('mesInspectionActual.inspector') }} / {{ t('mesInspectionActual.productionQty') }}
            </h4>
            <div class="confirmed-edit-form-row">
              <el-form-item :label="t('mesInspectionActual.inspector')" class="confirmed-edit-form-item">
                <el-input
                  :model-value="loggedInInspectorLabel"
                  disabled
                  size="small"
                  class="confirmed-edit-full"
                />
              </el-form-item>
              <el-form-item :label="t('mesInspectionActual.productionQty')" class="confirmed-edit-form-item">
                <el-input-number
                  v-model="confirmedEditForm.actualQty"
                  size="small"
                  :min="0"
                  :step="1"
                  :precision="0"
                  controls-position="right"
                  class="confirmed-edit-full"
                />
              </el-form-item>
            </div>
          </section>
          <section class="confirmed-edit-section confirmed-edit-section--defects">
            <h4 class="confirmed-edit-section__title">
              {{ t('mesInspectionActual.defectByItem') }}
            </h4>
            <div v-loading="loadingDefectItems" class="confirmed-edit-defect-groups">
              <p v-if="!loadingDefectItems && defectItems.length === 0" class="defect-panel__empty">
                {{ t('mesInspectionActual.defectItemsEmpty') }}
              </p>
              <section
                v-for="group in defectItemGroups"
                :key="group.processCd"
                class="defect-process-group defect-process-group--edit"
              >
                <header class="defect-process-group__head">
                  <span class="defect-process-group__label">{{
                    t('mesInspectionActual.attributableProcess')
                  }}</span>
                  <span class="defect-process-group__name">{{
                    group.processName || group.processCd || '—'
                  }}</span>
                </header>
                <div class="confirmed-edit-defect-grid">
                  <div
                    v-for="item in group.items"
                    :key="item.id"
                    class="defect-cell defect-cell--compact"
                    :class="{ 'defect-cell--active': confirmedEditDefectCount(item.id) > 0 }"
                  >
                    <span class="defect-cell__label">{{ defectItemLabel(item) }}</span>
                    <div class="defect-stepper">
                      <el-button
                        class="defect-stepper__btn"
                        circle
                        :icon="Minus"
                        :disabled="confirmedEditDefectCount(item.id) <= 0"
                        @click="bumpConfirmedEditDefect(item.id, -1)"
                      />
                      <span class="defect-stepper__val">{{ confirmedEditDefectCount(item.id) }}</span>
                      <el-button
                        class="defect-stepper__btn"
                        circle
                        type="primary"
                        :icon="Plus"
                        @click="bumpConfirmedEditDefect(item.id, 1)"
                      />
                    </div>
                  </div>
                </div>
              </section>
            </div>
          </section>
          <section class="confirmed-edit-section confirmed-edit-section--time">
            <h4 class="confirmed-edit-section__title">
              <el-icon :size="14"><Clock /></el-icon>
              {{ t('mesInspectionActual.productionStart') }} / {{ t('mesInspectionActual.elapsed') }}
            </h4>
            <div class="confirmed-edit-form-row">
              <el-form-item :label="t('mesInspectionActual.productionStart')" class="confirmed-edit-form-item">
                <el-date-picker
                  v-model="confirmedEditForm.wallStart"
                  type="datetime"
                  size="small"
                  :editable="false"
                  teleported
                  format="YYYY/MM/DD HH:mm"
                  class="confirmed-edit-full"
                />
              </el-form-item>
              <el-form-item :label="t('mesInspectionActual.productionDay')" class="confirmed-edit-form-item">
                <el-input
                  :model-value="confirmedEditProductionDay"
                  disabled
                  size="small"
                  class="confirmed-edit-full confirmed-edit-production-day"
                />
              </el-form-item>
            </div>
            <div class="confirmed-edit-form-row">
              <el-form-item :label="t('mesInspectionActual.productionEnd')" class="confirmed-edit-form-item">
                <el-date-picker
                  v-model="confirmedEditForm.wallEnd"
                  type="datetime"
                  size="small"
                  :editable="false"
                  teleported
                  format="YYYY/MM/DD HH:mm"
                  class="confirmed-edit-full"
                />
              </el-form-item>
            </div>
            <div class="confirmed-edit-form-row confirmed-edit-form-row--metrics">
              <el-form-item
                :label="`${t('mesInspectionActual.pausedAccum')}（${t('mesInspectionActual.pausedAccumUnit')}）`"
                class="confirmed-edit-form-item"
              >
                <el-input-number
                  v-model="confirmedEditForm.pausedAccumSec"
                  size="small"
                  :min="0"
                  :step="1"
                  :precision="0"
                  controls-position="right"
                  class="confirmed-edit-full"
                />
              </el-form-item>
              <el-form-item :label="t('mesInspectionActual.elapsed')" class="confirmed-edit-form-item">
                <div class="confirmed-edit-elapsed" role="status">
                  <span class="confirmed-edit-elapsed__value">{{ confirmedEditElapsedPreview }}</span>
                </div>
              </el-form-item>
            </div>
          </section>
          <div class="confirmed-edit-hint" role="note">
            <el-icon class="confirmed-edit-hint__icon" :size="14"><InfoFilled /></el-icon>
            <span>{{ t('mesInspectionActual.confirmedEditPauseHint') }}</span>
          </div>
        </el-form>
      </div>
      <template #footer>
        <div class="confirmed-edit-footer">
          <el-button
            class="confirmed-edit-btn confirmed-edit-btn--cancel"
            size="small"
            :disabled="confirmedEditSaving || confirmedEditClearing"
            @click="closeConfirmedHistoryEdit"
          >
            {{ t('common.cancel') }}
          </el-button>
          <el-button
            class="confirmed-edit-btn confirmed-edit-btn--save"
            type="primary"
            size="small"
            :loading="confirmedEditSaving"
            :disabled="confirmedEditClearing"
            @click="submitConfirmedHistoryEdit"
          >
            {{ t('mesInspectionActual.btnSaveConfirmed') }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <MesBarcodeScanDialog
      v-model="productScanDialogVisible"
      locale-ns="mesInspectionActual"
      scanner-region-id="mes-insp-barcode-scanner-region"
      @scanned="onProductBarcodeScanned"
    />
  </div>
</template>

<style scoped>
.inspection-actual-page {
  --ca-radius: 10px;
  --ca-gap: 8px;
  padding: 10px 12px 16px;
  padding-bottom: max(16px, env(safe-area-inset-bottom, 0px));
  max-width: min(1680px, 100%);
  margin: 0 auto;
  box-sizing: border-box;
  background: var(--el-bg-color-page);
}

.page-head {
  margin-bottom: 8px;
}

.page-head-row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px 16px;
}

.page-head-main {
  flex: 1 1 240px;
  min-width: 0;
}

.page-head-locale {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.locale-glyph-btn {
  width: 36px;
  height: 36px;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  border: 1px solid var(--el-border-color);
  background: var(--el-fill-color-blank);
  color: var(--el-text-color-regular);
  cursor: pointer;
  transition:
    background 0.15s ease,
    border-color 0.15s ease,
    color 0.15s ease,
    box-shadow 0.15s ease;
}

.locale-glyph-btn:hover {
  border-color: var(--el-color-primary-light-5);
  color: var(--el-color-primary);
  background: var(--el-fill-color-light);
}

.locale-glyph-btn--active {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  font-weight: 700;
  box-shadow: 0 0 0 1px var(--el-color-primary-light-7);
}

.locale-glyph-btn__glyph {
  font-size: 0.95rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  line-height: 1;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  font-size: 1.2rem;
  font-weight: 700;
  letter-spacing: 0.01em;
  line-height: 1.25;
}

.page-title__help {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  margin-left: 2px;
  padding: 0;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  transition:
    color 0.15s ease,
    background 0.15s ease;
}

.page-title__help:hover {
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}

.page-title__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 38px;
  height: 38px;
  border-radius: 10px;
  color: #fff;
  background: linear-gradient(
    135deg,
    var(--el-color-primary) 0%,
    #38bdf8 48%,
    var(--el-color-success) 100%
  );
  box-shadow:
    0 4px 14px rgba(64, 158, 255, 0.28),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

.page-head:hover .page-title__icon {
  transform: translateY(-1px) scale(1.03);
  box-shadow:
    0 6px 18px rgba(64, 158, 255, 0.34),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
}

.page-title__icon .el-icon {
  font-size: 20px;
}

.page-title__text {
  color: var(--el-text-color-primary);
}

.in-progress-strip {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 10px;
  margin-bottom: 8px;
  padding: 8px 10px;
  border-radius: 8px;
  background: var(--el-color-success-light-9);
  border: 1px solid var(--el-color-success-light-5);
}

.in-progress-strip__title {
  flex: 0 0 auto;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--el-color-success-dark-2);
}

.in-progress-strip__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  min-width: 0;
  flex: 1 1 auto;
}

.in-progress-chip-wrap {
  display: inline-flex;
  flex-direction: column;
  padding: 4px;
  border-radius: 8px;
  border: 1px solid var(--el-color-success-light-3);
  background: #fff;
}

.in-progress-chip-wrap--active {
  border-color: var(--el-color-success);
  box-shadow: 0 0 0 1px var(--el-color-success);
}

.in-progress-chip {
  display: inline-flex;
  flex-direction: column;
  align-items: stretch;
  gap: 2px;
  padding: 2px 4px;
  min-width: 0;
  cursor: pointer;
  font: inherit;
  text-align: left;
  outline: none;
}

.in-progress-chip:focus-visible {
  border-radius: 4px;
  box-shadow: 0 0 0 2px var(--el-color-primary-light-5);
}

.in-progress-chip__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
  min-width: 0;
}

.in-progress-chip__resume-btn {
  flex-shrink: 0;
  margin: 0 !important;
  padding: 2px 8px !important;
  height: 24px !important;
  font-size: 0.72rem;
}

.in-progress-chip__product {
  flex: 1 1 auto;
  min-width: 0;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--el-text-color-primary);
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-recovery-alert {
  margin-bottom: 8px;
}

.session-recovery-alert__text {
  margin: 4px 0 8px;
  font-size: 0.8rem;
  line-height: 1.45;
}

.session-recovery-alert__btn {
  margin-top: 2px;
}

.in-progress-chip__inspector {
  font-size: 0.68rem;
  color: var(--el-text-color-secondary);
  line-height: 1.2;
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.in-progress-chip__lock-hint {
  font-size: 0.62rem;
  color: var(--el-color-warning-dark-2);
  line-height: 1.2;
}

.product-locked-alert {
  margin-bottom: 8px;
}

.offline-strip {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  padding: 6px 10px;
  border-radius: 8px;
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--el-color-warning-dark-2);
  background: var(--el-color-warning-light-9);
  border: 1px solid var(--el-color-warning-light-5);
}

.offline-strip__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--el-color-warning);
  flex-shrink: 0;
  animation: offline-pulse 1.4s ease-in-out infinite;
}

@keyframes offline-pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.35;
  }
}

.toolbar-card {
  --toolbar-h: 36px;
  --toolbar-day-picker-w: 150px;
  --toolbar-inspector-select-w: 110px;
  --toolbar-machine-select-w: 115px;
  --toolbar-machine-gap: 6px;
  --toolbar-day-gap: 5px;
  --toolbar-day-shortcut-size: 28px;
  --toolbar-day-today-min-w: 36px;
  border-radius: var(--ca-radius);
  border: 1px solid var(--el-border-color-lighter);
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.04);
}

.toolbar-card :deep(.el-card__body) {
  padding: 10px 12px;
}

.toolbar-layout {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px 12px;
}

.toolbar-field-row {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex: 0 0 auto;
  min-height: var(--toolbar-h);
}

.toolbar-field-row__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: var(--toolbar-h);
  height: var(--toolbar-h);
  border-radius: 8px;
  font-size: 16px;
  color: #fff;
  background: linear-gradient(135deg, var(--el-color-primary) 0%, #38bdf8 100%);
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.28);
}

.toolbar-field-row__label {
  flex-shrink: 0;
  font-size: 0.8125rem;
  font-weight: 600;
  line-height: 1;
  color: var(--el-text-color-regular);
  white-space: nowrap;
}

.toolbar-field-row--day {
  flex: 0 1 auto;
  max-width: max-content;
  padding: 0 8px 0 0;
  gap: 6px;
  border-radius: 10px;
  border: 1px solid var(--el-color-primary-light-7);
  background: linear-gradient(
    165deg,
    var(--el-color-primary-light-9) 0%,
    var(--el-fill-color-blank) 55%,
    var(--el-fill-color-light) 100%
  );
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.75);
}

.toolbar-field-row--day .toolbar-field-row__icon {
  margin-left: -1px;
  border-radius: 9px 0 0 9px;
}

.toolbar-field-row--day .toolbar-field-row__label {
  color: var(--el-color-primary-dark-2);
}

.toolbar-control :deep(.el-input__wrapper),
.toolbar-control :deep(.el-select__wrapper) {
  min-height: var(--toolbar-h);
  height: var(--toolbar-h);
  box-sizing: border-box;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
}

.toolbar-control :deep(.el-input__inner) {
  height: calc(var(--toolbar-h) - 2px);
  line-height: calc(var(--toolbar-h) - 2px);
}

.toolbar-day-wrap {
  display: inline-flex;
  align-items: center;
  gap: var(--toolbar-day-gap);
  flex: 0 0 auto;
  max-width: calc(
    var(--toolbar-day-picker-w) + var(--toolbar-day-shortcut-size) * 2 +
      var(--toolbar-day-today-min-w) + var(--toolbar-day-gap) * 3
  );
}

.toolbar-day-shortcuts {
  display: inline-flex;
  align-items: center;
  gap: var(--toolbar-day-gap);
  flex-shrink: 0;
}

.toolbar-day-shortcuts :deep(.el-button.is-circle) {
  width: var(--toolbar-day-shortcut-size);
  height: var(--toolbar-day-shortcut-size);
  padding: 0;
}

.toolbar-day-today-btn {
  min-width: var(--toolbar-day-today-min-w);
  height: var(--toolbar-day-shortcut-size);
  padding: 0 6px;
  font-size: 0.75rem;
  font-weight: 600;
}

.toolbar-day-picker.el-date-editor {
  --el-date-editor-width: var(--toolbar-day-picker-w);
  width: var(--toolbar-day-picker-w) !important;
  max-width: var(--toolbar-day-picker-w);
  flex: 0 0 var(--toolbar-day-picker-w);
}

.toolbar-day-picker :deep(.el-input__wrapper),
.toolbar-day-picker :deep(.el-input__inner) {
  width: 100%;
}

.toolbar-field-row--machine {
  flex: 0 1 auto;
  max-width: max-content;
  gap: var(--toolbar-machine-gap);
  padding: 0 8px 0 0;
  border-radius: 10px;
  border: 1px solid var(--el-color-warning-light-7);
  background: linear-gradient(
    165deg,
    var(--el-color-warning-light-9) 0%,
    var(--el-fill-color-blank) 55%,
    #fff7ed 100%
  );
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.8),
    0 1px 4px rgba(234, 88, 12, 0.06);
}

.toolbar-field-row--machine .toolbar-field-row__icon--machine {
  margin-left: -1px;
  border-radius: 9px 0 0 9px;
  background: linear-gradient(135deg, #f59e0b 0%, #ea580c 100%);
  box-shadow: 0 2px 8px rgba(234, 88, 12, 0.3);
}

.toolbar-field-row--machine .toolbar-field-row__label {
  color: #9a3412;
}

.toolbar-machine-wrap {
  display: inline-flex;
  flex: 0 0 auto;
  max-width: var(--toolbar-machine-select-w);
}

.toolbar-load-btn {
  height: var(--toolbar-h);
  min-height: var(--toolbar-h);
  padding: 0 14px;
  font-weight: 600;
  border-radius: 8px;
  border: none;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.25);
}

.toolbar-load-btn:not(.is-disabled) {
  background: linear-gradient(180deg, #79bbff 0%, var(--el-color-primary) 100%);
}

.full-width-control {
  width: 100%;
}

.toolbar-machine-select {
  width: var(--toolbar-machine-select-w) !important;
  max-width: var(--toolbar-machine-select-w);
  flex: 0 0 var(--toolbar-machine-select-w);
}

.toolbar-machine-select :deep(.el-select__wrapper),
.toolbar-machine-select :deep(.el-input__wrapper) {
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  background: var(--el-fill-color-blank);
  border: 1px solid var(--el-color-warning-light-5);
  box-shadow: 0 1px 2px rgba(234, 88, 12, 0.06);
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    background 0.2s ease;
}

.toolbar-machine-select :deep(.el-select__wrapper:hover) {
  border-color: var(--el-color-warning);
}

.toolbar-machine-select :deep(.el-select__wrapper.is-focused) {
  border-color: var(--el-color-warning);
  box-shadow: 0 0 0 2px var(--el-color-warning-light-8);
}

.toolbar-machine-select :deep(.el-select__selected-item),
.toolbar-machine-select :deep(.el-select__placeholder) {
  font-weight: 600;
}

.toolbar-machine-select--chosen :deep(.el-select__wrapper) {
  background: linear-gradient(180deg, #fffbeb 0%, var(--el-fill-color-blank) 100%);
  border-color: var(--el-color-warning);
}

.toolbar-machine-select--chosen :deep(.el-select__selected-item) {
  color: #9a3412;
}

.toolbar-machine-select :deep(.el-select__caret) {
  color: var(--el-color-warning);
}

/* タッチ端末: 検索用 input を出さずキーボードを抑止 */
@media (hover: none) and (pointer: coarse) {
  .toolbar-machine-select :deep(.el-select__input),
  .toolbar-inspector-select :deep(.el-select__input),
  .product-select-toolbar :deep(.el-select__input),
  .plan-field__control--operator :deep(.el-select__input) {
    display: none !important;
  }
}

.btn-ico {
  margin-right: 4px;
  vertical-align: middle;
}

.plan-board {
  margin-top: 8px;
  min-height: 80px;
}

.plan-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.plan-day-group {
  border-radius: var(--ca-radius);
  padding: 0;
  background: var(--el-fill-color-blank);
  border: 1px solid var(--el-border-color-lighter);
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
}

.plan-day-group--anchor {
  border-color: var(--el-color-primary-light-5);
  box-shadow: 0 0 0 1px var(--el-color-primary-light-7);
}

.plan-day-group__head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 6px 12px;
  padding: 6px 10px;
  background: linear-gradient(180deg, var(--el-fill-color-light) 0%, var(--el-fill-color-blank) 100%);
  border-bottom: 1px solid var(--el-border-color-lighter);
  position: sticky;
  top: 0;
  z-index: 3;
}

.plan-day-group--anchor .plan-day-group__head {
  background: linear-gradient(
    180deg,
    var(--el-color-primary-light-9) 0%,
    var(--el-fill-color-blank) 100%
  );
}

.plan-day-group__title-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
  min-width: 0;
}

.plan-day-group__date-bold {
  font-size: clamp(0.95rem, 2.2vw, 1.05rem);
  font-weight: 700;
  color: var(--el-text-color-primary);
  line-height: 1.3;
}

.plan-day-group__badge {
  flex-shrink: 0;
}

.plan-day-group__count {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--el-text-color-secondary);
}

.plan-day-group__cards {
  display: flex;
  flex-direction: column;
}

.plan-day-group .plan-row-card {
  margin: 0 8px 8px;
  border-radius: 8px;
}

.plan-day-group .plan-row-card:first-of-type {
  margin-top: 8px;
}

.plan-row-card__drag-handle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  padding: 2px 4px;
  margin: -2px 0;
  border-radius: 6px;
  color: var(--el-text-color-secondary);
  cursor: grab;
  touch-action: none;
  user-select: none;
}

.plan-row-card__drag-handle:active {
  cursor: grabbing;
}

.plan-row-card--ghost {
  opacity: 0.42;
}

.plan-row-card--chosen {
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.12);
}

.plan-row-card {
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
  border-left: 3px solid var(--el-color-warning);
  transition:
    border-color 0.15s ease,
    box-shadow 0.15s ease;
}

.plan-row-card:hover {
  border-color: var(--el-border-color);
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
}

.plan-row-card--confirmed {
  border-left-color: var(--el-color-success);
  opacity: 0.92;
}

.plan-row-card :deep(.el-card__body) {
  padding: 10px 12px;
}

.plan-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.plan-row__head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 8px;
}

.plan-row-scan-remarks-cluster {
  display: inline-flex;
  align-items: center;
  gap: 130px;
  min-width: 0;
  flex: 0 1 auto;
  max-width: 100%;
}

.plan-row-remarks {
  flex: 0 1 auto;
  min-width: 0;
  max-width: min(28rem, 100%);
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--el-color-danger);
  line-height: 1.35;
  background: var(--el-color-danger-light-9);
  border: 1px solid var(--el-color-danger-light-5);
  box-shadow: 0 0 0 1px rgba(245, 108, 108, 0.15);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.plan-row__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: stretch;
  gap: 8px 10px;
  padding: 8px 10px;
  border-radius: 10px;
  background: linear-gradient(
    165deg,
    var(--el-fill-color-blank) 0%,
    var(--el-color-primary-light-9) 42%,
    var(--el-fill-color-light) 100%
  );
  border: 1px solid var(--el-color-primary-light-8);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.85);
}

.plan-row-card--confirmed .plan-row__meta {
  background: linear-gradient(165deg, var(--el-fill-color-blank) 0%, var(--el-color-success-light-9) 100%);
  border-color: var(--el-color-success-light-7);
}

.plan-meta-primary {
  display: inline-flex;
  flex-direction: row;
  flex-wrap: nowrap;
  align-items: center;
  gap: 8px;
  flex: 0 1 auto;
  width: fit-content;
  max-width: min(100%, 28rem);
  min-width: 0;
  padding: 5px 10px;
  border-radius: 8px;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border: 1px solid #93c5fd;
}

.plan-row-card--confirmed .plan-meta-primary {
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
  border-color: #86efac;
}

.plan-meta-chips {
  --plan-meta-control-h: 32px;
  --plan-meta-block-h: calc(var(--plan-meta-control-h) + 10px);
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  flex: 1 1 auto;
  min-width: 0;
}

.plan-meta-chips > .plan-chip,
.plan-meta-chips > .plan-meta-field {
  box-sizing: border-box;
  min-height: var(--plan-meta-block-h);
  height: var(--plan-meta-block-h);
}

.plan-row__ops {
  --plan-run-block-height: 5.25rem;
  --plan-act-btn-width: 6.25rem;
  box-sizing: border-box;
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  gap: 8px;
  height: var(--plan-run-block-height);
  max-height: var(--plan-run-block-height);
  overflow: hidden;
}

.plan-row__ops .plan-row__timer {
  flex: 0 0 auto;
  height: var(--plan-run-block-height);
  max-height: var(--plan-run-block-height);
  overflow: hidden;
}

.plan-row__ops .plan-row__actions {
  flex: 0 0 auto;
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  gap: 6px;
  height: var(--plan-run-block-height);
  max-height: var(--plan-run-block-height);
  overflow: hidden;
}

.plan-status-action-btn {
  padding: 0 4px;
  height: 22px;
  font-size: 0.75rem;
  font-weight: 600;
}

.plan-status-action-btn .el-icon {
  margin-right: 2px;
  font-size: 0.85rem;
}

.plan-seq-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2rem;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  background: var(--el-fill-color-light);
  color: #000;
  border: 1px solid var(--el-border-color-lighter);
}

.plan-field--inline {
  --plan-field-control-width: 108px;
  display: grid;
  grid-template-columns: 7.5rem var(--plan-field-control-width);
  column-gap: 6px;
  align-items: center;
  flex: 0 0 auto;
  width: calc(7.5rem + var(--plan-field-control-width) + 6px);
  max-width: 100%;
}

.plan-meta-field {
  --plan-meta-control-w: 108px;
  display: grid;
  grid-template-columns: auto var(--plan-meta-control-w);
  column-gap: 8px;
  align-items: center;
  min-width: 0;
  padding: 0 8px;
  border-radius: 8px;
  border: 1px solid transparent;
  flex: 0 1 auto;
  width: fit-content;
  max-width: 100%;
}

.plan-meta-field--operator {
  --plan-meta-control-w: 108px;
  background: linear-gradient(180deg, #f5f3ff 0%, #ede9fe 100%);
  border-color: #c4b5fd;
}

.plan-meta-field--setup {
  --plan-meta-control-w: 118px;
  background: linear-gradient(180deg, #fffbeb 0%, #fef3c7 100%);
  border-color: #fcd34d;
}

.plan-meta-field__label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.03em;
  line-height: 1.2;
  white-space: nowrap;
}

.plan-meta-field--operator .plan-meta-field__label {
  color: #5b21b6;
}

.plan-meta-field--setup .plan-meta-field__label {
  color: #b45309;
}

.plan-meta-field__icon {
  font-size: 0.9rem;
}

.plan-meta-field__unit {
  font-weight: 600;
  opacity: 0.85;
}

.plan-meta-field .plan-field__control--operator,
.plan-meta-field .plan-field__number--setup,
.plan-meta-field .plan-field__number--setup :deep(.el-input-number) {
  width: var(--plan-meta-control-w);
  max-width: 100%;
  justify-self: start;
}

.plan-meta-field--operator :deep(.el-select__wrapper) {
  min-height: var(--plan-meta-control-h);
  height: var(--plan-meta-control-h);
  background: rgba(255, 255, 255, 0.92);
  border-color: #c4b5fd;
  box-shadow: 0 1px 2px rgba(91, 33, 182, 0.08);
}

.plan-meta-field--operator :deep(.el-select__wrapper:hover) {
  border-color: #8b5cf6;
}

.plan-meta-field--setup :deep(.el-input-number__decrease),
.plan-meta-field--setup :deep(.el-input-number__increase) {
  background: rgba(255, 255, 255, 0.75);
  border-color: #fcd34d;
  color: #b45309;
}

.plan-meta-field--setup :deep(.el-input-number) {
  height: var(--plan-meta-control-h);
  line-height: var(--plan-meta-control-h);
}

.plan-meta-field--setup :deep(.el-input__wrapper) {
  min-height: var(--plan-meta-control-h);
  height: var(--plan-meta-control-h);
  background: rgba(255, 255, 255, 0.92);
  border-color: #fcd34d;
  box-shadow: 0 1px 2px rgba(180, 83, 9, 0.08);
}

.plan-field--inline .plan-field__label {
  display: block;
  margin-bottom: 0;
  white-space: nowrap;
  text-align: right;
  justify-self: end;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--el-text-color-regular);
}

.plan-field__control--operator,
.plan-field__number--setup,
.plan-field__number--setup :deep(.el-input-number) {
  width: var(--plan-field-control-width, 152px);
  justify-self: start;
}

.plan-field__number--setup :deep(.el-input-number__decrease),
.plan-field__number--setup :deep(.el-input-number__increase) {
  width: 34px;
  flex-shrink: 0;
  font-size: 14px;
}

.plan-field__number--setup :deep(.el-input__wrapper) {
  width: 100%;
  padding-left: 6px;
  padding-right: 6px;
}

.plan-field__number--setup :deep(.el-input__inner) {
  text-align: center;
}

.plan-product-name {
  flex: 0 1 auto;
  min-width: 0;
  max-width: 11rem;
  font-size: 0.95rem;
  font-weight: 800;
  line-height: 1.3;
  letter-spacing: 0.01em;
  color: #1e3a8a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.plan-row-card--confirmed .plan-product-name {
  color: #166534;
}

.plan-product-material {
  display: inline-flex;
  align-items: center;
  flex: 0 1 auto;
  min-width: 0;
  max-width: 14rem;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  line-height: 1.3;
  color: #0f766e;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid #5eead4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.plan-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  max-width: 100%;
  padding: 0 10px;
  border-radius: 8px;
  line-height: 1.25;
  border: 1px solid transparent;
}

.plan-chip__label {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  opacity: 0.9;
}

.plan-chip__value {
  font-size: 0.92rem;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

.plan-chip--qty {
  background: linear-gradient(180deg, #dbeafe 0%, #bfdbfe 100%);
  border-color: #60a5fa;
  color: #1e40af;
}

.plan-chip--qty .plan-chip__label {
  color: #1d4ed8;
}

.plan-chip--qty .plan-chip__value {
  color: #1e3a8a;
}

.plan-chip--qty-actual {
  background: linear-gradient(180deg, #dcfce7 0%, #bbf7d0 100%);
  border-color: #4ade80;
  color: #166534;
}

.plan-chip--qty-actual .plan-chip__label {
  color: #15803d;
}

.plan-chip--qty-actual .plan-chip__value {
  color: #14532d;
}

.plan-chip--code {
  background: linear-gradient(180deg, #f3e8ff 0%, #e9d5ff 100%);
  border-color: #c084fc;
  font-size: 0.8rem;
  font-weight: 700;
  color: #6b21a8;
  letter-spacing: 0.02em;
}

/* legacy aliases */
.plan-chip--accent {
  background: linear-gradient(180deg, #dbeafe 0%, #bfdbfe 100%);
  border-color: #60a5fa;
  color: #1e40af;
  font-weight: 600;
}

.plan-chip--muted {
  background: linear-gradient(180deg, #f3e8ff 0%, #e9d5ff 100%);
  border-color: #c084fc;
  color: #6b21a8;
}

.plan-row__timer {
  flex-shrink: 0;
}

.timer-compact {
  box-sizing: border-box;
  width: 15.5rem;
  min-width: 15.5rem;
  max-width: 15.5rem;
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid var(--el-border-color-lighter);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.75),
    0 1px 4px rgba(15, 23, 42, 0.06);
  overflow: hidden;
}

.plan-row__ops .timer-compact {
  height: 100%;
  max-height: var(--plan-run-block-height);
  padding: 6px 8px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  overflow: hidden;
}

.plan-row__ops .timer-compact__readout-row {
  margin: 1px 0;
}

.plan-row__ops .timer-compact__readout {
  font-size: 1.1rem;
  line-height: 1.05;
}

.plan-row__ops .timer-compact__pause-value {
  font-size: 0.88rem;
  line-height: 1.05;
}

.plan-row__ops .timer-compact__walls {
  font-size: 0.68rem;
  line-height: 1.1;
}

.timer-compact--idle {
  background: linear-gradient(165deg, #f8fafc 0%, #e2e8f0 100%);
  border-color: #cbd5e1;
}

.timer-compact--running {
  background: linear-gradient(165deg, #ecfdf5 0%, #d1fae5 55%, #f0fdf4 100%);
  border-color: #6ee7b7;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.85),
    0 0 0 1px rgba(16, 185, 129, 0.12),
    0 2px 8px rgba(16, 185, 129, 0.12);
}

.timer-compact--paused {
  background: linear-gradient(165deg, #fffbeb 0%, #fef3c7 55%, #fff7ed 100%);
  border-color: #fbbf24;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.85),
    0 0 0 1px rgba(245, 158, 11, 0.15);
}

.timer-compact--ended {
  background: linear-gradient(165deg, #eff6ff 0%, #dbeafe 55%, #f8fafc 100%);
  border-color: #93c5fd;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.85),
    0 0 0 1px rgba(59, 130, 246, 0.1);
}

.timer-compact__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  min-height: 0;
}

.timer-compact__label {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #64748b;
  white-space: nowrap;
}

.timer-compact__label-icon {
  font-size: 0.82rem;
}

.timer-compact--running .timer-compact__label {
  color: #047857;
}

.timer-compact--paused .timer-compact__label {
  color: #b45309;
}

.timer-compact--ended .timer-compact__label {
  color: #1d4ed8;
}

.timer-compact__phase {
  flex-shrink: 0;
  padding: 1px 7px;
  border-radius: 999px;
  font-size: 0.65rem;
  font-weight: 700;
  line-height: 1.35;
  letter-spacing: 0.02em;
  border: 1px solid transparent;
}

.timer-compact--idle .timer-compact__phase {
  color: #475569;
  background: rgba(255, 255, 255, 0.75);
  border-color: #cbd5e1;
}

.timer-compact--running .timer-compact__phase {
  color: #065f46;
  background: rgba(255, 255, 255, 0.8);
  border-color: #6ee7b7;
}

.timer-compact--paused .timer-compact__phase {
  color: #92400e;
  background: rgba(255, 255, 255, 0.82);
  border-color: #fcd34d;
}

.timer-compact--ended .timer-compact__phase {
  color: #1e40af;
  background: rgba(255, 255, 255, 0.82);
  border-color: #93c5fd;
}

.timer-compact__readout-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 6px;
  margin: 2px 0;
}

.timer-compact__readout {
  font-variant-numeric: tabular-nums;
  font-size: clamp(1.2rem, 3vw, 1.5rem);
  font-weight: 800;
  margin: 0;
  line-height: 1.1;
  flex: 1 1 auto;
  min-width: 0;
  color: #0f172a;
}

.timer-compact--running .timer-compact__readout {
  color: #047857;
}

.timer-compact--ended .timer-compact__readout {
  color: #1e3a8a;
}

.timer-compact__readout--display-frozen {
  color: #b45309;
  letter-spacing: 0.02em;
}

.timer-compact__pause-side {
  flex: 0 0 auto;
  text-align: right;
  line-height: 1.15;
  max-width: 46%;
  padding: 1px 5px;
  border-radius: 5px;
  background: rgba(255, 255, 255, 0.55);
}

.timer-compact__pause-label {
  display: block;
  font-size: 0.58rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: #78716c;
  white-space: nowrap;
}

.timer-compact__pause-value {
  display: block;
  font-variant-numeric: tabular-nums;
  font-size: clamp(0.92rem, 2.4vw, 1.1rem);
  font-weight: 700;
  color: #57534e;
}

.timer-compact--paused .timer-compact__pause-label,
.timer-compact--paused .timer-compact__pause-value {
  color: #b45309;
}

.timer-compact__walls {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  justify-content: center;
  gap: 4px 6px;
  font-size: 0.72rem;
  font-variant-numeric: tabular-nums;
  color: #64748b;
  white-space: nowrap;
  padding-top: 2px;
  border-top: 1px dashed rgba(100, 116, 139, 0.25);
}

.timer-compact--running .timer-compact__walls {
  color: #047857;
  border-top-color: rgba(4, 120, 87, 0.2);
}

.timer-compact--paused .timer-compact__walls {
  color: #b45309;
  border-top-color: rgba(180, 83, 9, 0.25);
}

.timer-compact--ended .timer-compact__walls {
  color: #1d4ed8;
  border-top-color: rgba(29, 78, 216, 0.2);
}

.timer-compact__walls > span:not(.timer-compact__sep) {
  flex-shrink: 0;
}

.timer-compact__sep {
  opacity: 0.5;
  flex-shrink: 0;
  color: inherit;
}

.plan-row__actions {
  display: flex;
  flex-wrap: nowrap;
  gap: 6px;
  align-items: stretch;
}

.plan-act-btn {
  margin: 0 !important;
  padding: 0 6px;
  font-size: 0.78rem;
  font-weight: 600;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.08);
  white-space: nowrap;
}

.plan-row__ops .plan-act-btn {
  box-sizing: border-box;
  width: var(--plan-act-btn-width, 6.25rem);
  min-width: var(--plan-act-btn-width, 6.25rem);
  max-width: var(--plan-act-btn-width, 6.25rem);
  height: var(--plan-run-block-height);
  min-height: unset;
  max-height: var(--plan-run-block-height);
  flex: 0 0 var(--plan-act-btn-width, 6.25rem);
  line-height: 1.15;
}

.plan-row__ops .plan-act-btn :deep(span) {
  line-height: 1.15;
}

.plan-act-btn :deep(.el-icon) {
  margin-right: 3px;
  font-size: 1rem;
}

.plan-act-btn--start:not(.is-disabled):not(.plan-act-btn--start--locked) {
  --el-button-bg-color: var(--el-color-success);
  --el-button-border-color: var(--el-color-success);
  --el-button-hover-bg-color: #3ecf7a;
  --el-button-hover-border-color: #3ecf7a;
  --el-button-active-bg-color: #529b2e;
  --el-button-active-border-color: #529b2e;
  --el-button-text-color: #fff;
  background: linear-gradient(180deg, #4cd787 0%, var(--el-color-success) 100%);
  color: #fff;
}

.plan-act-btn--start.plan-act-btn--start--locked.is-disabled {
  opacity: 1;
  cursor: not-allowed;
  --el-button-disabled-bg-color: var(--el-fill-color);
  --el-button-disabled-border-color: var(--el-border-color);
  --el-button-disabled-text-color: var(--el-text-color-placeholder);
  background: var(--el-fill-color);
  color: var(--el-text-color-placeholder);
  border: 1px solid var(--el-border-color-lighter);
  box-shadow: none;
}

.plan-act-btn--pause:not(.is-disabled) {
  --el-button-bg-color: var(--el-color-warning);
  --el-button-border-color: var(--el-color-warning);
  --el-button-text-color: #5c3d00;
  background: linear-gradient(180deg, #ffd06a 0%, var(--el-color-warning) 100%);
  color: #5c3d00;
}

.plan-act-btn--resume:not(.is-disabled) {
  --el-button-bg-color: var(--el-color-primary);
  --el-button-border-color: var(--el-color-primary);
  --el-button-text-color: #fff;
  background: linear-gradient(180deg, #79bbff 0%, var(--el-color-primary) 100%);
  color: #fff;
}

.plan-act-btn--resume.plan-act-btn--resume-pulse:not(.is-disabled) {
  animation: mes-inspection-resume-pulse 0.85s ease-in-out infinite;
  transform-origin: center;
  z-index: 2;
  position: relative;
  font-weight: 800;
  letter-spacing: 0.02em;
  --el-button-border-color: var(--el-color-danger);
  border: 2px solid var(--el-color-danger) !important;
}

@keyframes mes-inspection-resume-pulse {
  0%,
  100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(245, 108, 108, 0.55);
    border-color: var(--el-color-danger);
  }
  50% {
    transform: scale(1.14);
    box-shadow:
      0 0 0 10px rgba(245, 108, 108, 0),
      0 0 0 3px rgba(245, 108, 108, 0.9);
    border-color: #ff4d4f;
  }
}

@media (prefers-reduced-motion: reduce) {
  .plan-act-btn--resume.plan-act-btn--resume-pulse:not(.is-disabled) {
    animation: none;
    transform: scale(1.08);
    border: 2px solid var(--el-color-danger) !important;
    box-shadow: 0 0 0 3px rgba(245, 108, 108, 0.55);
  }
}

.plan-act-btn--end:not(.is-disabled) {
  --el-button-bg-color: var(--el-color-danger);
  --el-button-border-color: var(--el-color-danger);
  --el-button-text-color: #fff;
  background: linear-gradient(180deg, #f89898 0%, var(--el-color-danger) 100%);
  color: #fff;
}

.plan-act-btn--machine:not(.is-disabled) {
  --el-button-bg-color: #d3d1d1;
  --el-button-border-color: #d4d2d2;
  --el-button-hover-bg-color: #c9c7c7;
  --el-button-hover-border-color: #bebebe;
  --el-button-text-color: #fff;
  background: linear-gradient(180deg, #cfcfcf 0%, #c4c3c3 100%);
  color: #fff;
}

.change-machine-dialog :deep(.el-dialog) {
  max-width: 94vw;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 16px 48px rgba(15, 23, 42, 0.2);
}

.change-machine-dialog :deep(.el-dialog__header) {
  padding: 0;
  margin: 0;
  border-bottom: none;
}

.change-machine-dialog :deep(.el-dialog__headerbtn) {
  top: 10px;
  right: 10px;
  z-index: 3;
  width: 28px;
  height: 28px;
}

.change-machine-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: rgba(255, 255, 255, 0.92);
}

.change-machine-dialog :deep(.el-dialog__headerbtn:hover .el-dialog__close) {
  color: #fff;
}

.change-machine-dialog :deep(.el-dialog__body) {
  padding: 0 16px 16px;
}

.change-machine-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 14px 44px 14px 16px;
  background: linear-gradient(135deg, #ea580c 0%, #f59e0b 48%, #fbbf24 100%);
  color: #fff;
}

.change-machine-header__main {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.change-machine-header__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.22);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.35);
}

.change-machine-header__text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.change-machine-header__title {
  font-size: 1rem;
  font-weight: 700;
  line-height: 1.25;
  letter-spacing: 0.02em;
}

.change-machine-header__sub {
  font-size: 0.72rem;
  font-weight: 500;
  line-height: 1.3;
  opacity: 0.92;
}

.change-machine-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.change-machine-hero {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 10px;
  padding: 10px 12px;
  border-radius: 10px;
  background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%);
  border: 1px solid #fdba74;
}

.change-machine-hero__code {
  flex-shrink: 0;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #9a3412;
  background: rgba(255, 255, 255, 0.75);
  border: 1px solid #fed7aa;
}

.change-machine-hero__product {
  font-size: 0.88rem;
  line-height: 1.35;
  color: var(--el-text-color-primary);
  word-break: break-word;
}

.change-machine-hero__product strong {
  font-weight: 700;
}

.change-machine-hero__sep {
  margin: 0 4px;
  opacity: 0.45;
}

.change-machine-flow {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 8px;
  align-items: stretch;
}

.change-machine-flow__arrow {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #ea580c;
  opacity: 0.85;
}

.change-machine-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid var(--el-border-color-lighter);
}

.change-machine-card--current {
  background: linear-gradient(180deg, var(--el-fill-color-light) 0%, var(--el-fill-color-blank) 100%);
}

.change-machine-card--target {
  background: linear-gradient(180deg, #fffbeb 0%, var(--el-fill-color-blank) 100%);
  border-color: #fcd34d;
}

.change-machine-card__label {
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--el-text-color-secondary);
}

.change-machine-card--target .change-machine-card__label {
  color: #b45309;
}

.change-machine-card__value {
  font-size: 0.95rem;
  font-weight: 700;
  line-height: 1.3;
  color: var(--el-text-color-primary);
  word-break: break-word;
}

.change-machine-select {
  width: 100%;
}

.change-machine-select :deep(.el-select__wrapper) {
  min-height: 40px;
  background: var(--el-fill-color-blank);
  border: 1px solid var(--el-color-warning-light-5);
  box-shadow: 0 1px 2px rgba(234, 88, 12, 0.06);
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.change-machine-select :deep(.el-select__wrapper:hover) {
  border-color: var(--el-color-warning);
}

.change-machine-select :deep(.el-select__wrapper.is-focused) {
  border-color: var(--el-color-warning);
  box-shadow: 0 0 0 2px var(--el-color-warning-light-8);
}

.change-machine-select--chosen :deep(.el-select__wrapper) {
  background: linear-gradient(180deg, #fffbeb 0%, var(--el-fill-color-blank) 100%);
  border-color: var(--el-color-warning);
}

.change-machine-select--chosen :deep(.el-select__selected-item) {
  font-weight: 700;
  color: #9a3412;
}

.change-machine-select :deep(.el-select__caret) {
  color: var(--el-color-warning);
}

.change-machine-hint {
  margin: 0;
  padding: 8px 10px;
  font-size: 0.75rem;
  line-height: 1.4;
  color: #92400e;
  border-radius: 8px;
  background: #fffbeb;
  border: 1px dashed #fcd34d;
}

.change-machine-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-top: 2px;
}

.change-machine-actions__submit,
.change-machine-actions__cancel {
  min-height: 42px;
  margin: 0 !important;
  font-weight: 600;
  border-radius: 8px;
}

.change-machine-actions__submit:not(.is-disabled) {
  border: none;
  background: linear-gradient(180deg, #fbbf24 0%, #ea580c 100%);
  color: #fff;
  box-shadow: 0 2px 10px rgba(234, 88, 12, 0.28);
}

.change-machine-actions__submit:not(.is-disabled):hover {
  background: linear-gradient(180deg, #fcd34d 0%, #c2410c 100%);
}

.change-machine-actions__cancel {
  border: 1px solid var(--el-border-color);
  background: var(--el-fill-color-blank);
  color: var(--el-text-color-regular);
}

@media (max-width: 420px) {
  .change-machine-flow {
    grid-template-columns: 1fr;
  }

  .change-machine-flow__arrow {
    transform: rotate(90deg);
  }

  .change-machine-actions {
    grid-template-columns: 1fr;
  }
}

.plan-act-btn.is-disabled {
  box-shadow: none;
  opacity: 0.55;
}

.plan-row__fields {
  display: grid;
  gap: 12px;
  grid-template-columns: 1fr;
  padding-top: 4px;
  border-top: 1px dashed var(--el-border-color-lighter);
  margin-top: 2px;
}

@media (min-width: 560px) {
  .plan-row__fields:not(.plan-row__fields--stack) {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.plan-field__label {
  display: block;
  font-size: 0.78rem;
  font-weight: 600;
  margin-bottom: 6px;
  color: var(--el-text-color-regular);
}

.plan-field__control {
  width: 100%;
}

.plan-field__number {
  width: 100%;
}

.plan-field__number :deep(.el-input-number) {
  width: 100%;
}

.plan-field__number :deep(.el-input__wrapper) {
  width: 100%;
}

.production-end-dialog :deep(.el-dialog) {
  max-width: 94vw;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 16px 48px rgba(15, 23, 42, 0.18);
}

.production-end-dialog :deep(.el-dialog__header) {
  padding: 0;
  margin: 0;
  border-bottom: none;
}

.production-end-dialog :deep(.el-dialog__headerbtn) {
  top: 10px;
  right: 10px;
  z-index: 3;
  width: 28px;
  height: 28px;
}

.production-end-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: rgba(255, 255, 255, 0.92);
}

.production-end-dialog :deep(.el-dialog__headerbtn:hover .el-dialog__close) {
  color: #fff;
}

.production-end-dialog :deep(.el-dialog__body) {
  padding: 8px 12px 6px;
}

.production-end-dialog :deep(.el-dialog__footer) {
  padding: 6px 12px 10px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.end-dialog-header {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 40px 10px 12px;
  background: linear-gradient(135deg, #047857 0%, #059669 48%, #34d399 100%);
  color: #fff;
}

.end-dialog-header__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.18);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.25);
}

.end-dialog-header__text {
  min-width: 0;
  flex: 1;
}

.end-dialog-header__title {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 700;
  line-height: 1.3;
  letter-spacing: 0.01em;
}

.end-dialog-header__sub {
  margin: 3px 0 0;
  font-size: 0.72rem;
  line-height: 1.35;
  opacity: 0.92;
}

.end-dialog-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.end-dialog-product-card {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px 10px;
  border-radius: 8px;
  background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 55%, var(--el-fill-color-blank) 100%);
  border: 1px solid #a7f3d0;
}

.end-dialog-product-card__cd {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #047857;
  font-variant-numeric: tabular-nums;
}

.end-dialog-product-card__name {
  font-size: 0.88rem;
  font-weight: 700;
  line-height: 1.3;
  color: var(--el-text-color-primary);
  word-break: break-word;
}

.end-dialog-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px;
}

@media (min-width: 400px) {
  .end-dialog-stats {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

.end-dialog-stat {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  padding: 6px 8px;
  border-radius: 7px;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color-lighter);
}

.end-dialog-stat--defect {
  background: linear-gradient(180deg, #fffbeb 0%, #fef3c7 100%);
  border-color: #fcd34d;
}

.end-dialog-stat__label {
  font-size: 0.65rem;
  font-weight: 600;
  line-height: 1.2;
  color: var(--el-text-color-secondary);
}

.end-dialog-stat__value {
  font-size: 0.8rem;
  font-weight: 700;
  line-height: 1.25;
  color: var(--el-text-color-primary);
  word-break: break-word;
  font-variant-numeric: tabular-nums;
}

.end-dialog-stat--defect .end-dialog-stat__value {
  color: #b45309;
}

.end-dialog-defects {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.end-dialog-defects__label {
  font-size: 0.68rem;
  font-weight: 600;
  color: var(--el-text-color-secondary);
}

.end-dialog-defects__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.end-dialog-defect-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  max-width: 100%;
  padding: 3px 8px;
  border-radius: 999px;
  background: #fffbeb;
  border: 1px solid #fde68a;
  font-size: 0.72rem;
  line-height: 1.2;
}

.end-dialog-defect-chip__name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 10rem;
  color: var(--el-text-color-regular);
}

.end-dialog-defect-chip__qty {
  font-weight: 800;
  color: #b45309;
  font-variant-numeric: tabular-nums;
}

.end-dialog-qty {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px 10px;
  border-radius: 8px;
  background: var(--el-fill-color-blank);
  border: 1px solid var(--el-border-color-lighter);
}

.end-dialog-qty__label {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--el-color-danger);
}

.end-dialog-qty__input {
  width: 100%;
}

.end-dialog-qty__input :deep(.el-input__wrapper) {
  min-height: 38px;
  padding: 0 10px;
  border-radius: 7px;
  background: rgba(245, 108, 108, 0.06);
  box-shadow: 0 0 0 1px var(--el-color-danger-light-5);
}

.end-dialog-qty__input :deep(.el-input__wrapper.is-focus) {
  box-shadow:
    0 0 0 1px var(--el-color-danger),
    0 0 0 3px var(--el-color-danger-light-8);
}

.end-dialog-qty__input :deep(.el-input__inner) {
  font-size: 1.05rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--el-color-danger);
  -webkit-text-fill-color: var(--el-color-danger);
}

.end-dialog-qty__input :deep(.el-input__inner::placeholder) {
  color: var(--el-color-danger-light-3);
  -webkit-text-fill-color: var(--el-color-danger-light-3);
}

.end-dialog-footer {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.end-dialog-footer__btn {
  min-height: 36px;
  margin: 0 !important;
  padding: 0 14px;
  font-weight: 600;
  border-radius: 8px;
}

.end-dialog-footer__btn-icon {
  margin-right: 4px;
}

.end-dialog-footer__btn--confirm:not(.is-disabled) {
  border: none;
  background: linear-gradient(180deg, #34d399 0%, #059669 100%);
  box-shadow: 0 2px 8px rgba(5, 150, 105, 0.35);
}

.end-dialog-footer__btn--cancel {
  flex: 0 0 auto;
}

.confirmed-edit-dialog :deep(.el-dialog) {
  max-width: 94vw;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 16px 48px rgba(15, 23, 42, 0.2);
}

.confirmed-edit-dialog :deep(.el-dialog__header) {
  padding: 0;
  margin: 0;
  border-bottom: none;
}

.confirmed-edit-dialog :deep(.el-dialog__headerbtn) {
  top: 10px;
  right: 10px;
  z-index: 3;
  width: 28px;
  height: 28px;
}

.confirmed-edit-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: rgba(255, 255, 255, 0.92);
}

.confirmed-edit-dialog :deep(.el-dialog__headerbtn:hover .el-dialog__close) {
  color: #fff;
}

.confirmed-edit-dialog :deep(.el-dialog__body) {
  padding: 8px 12px 6px;
}

.confirmed-edit-dialog :deep(.el-dialog__footer) {
  padding: 6px 12px 10px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.confirmed-edit-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 9px 40px 9px 12px;
  background: linear-gradient(135deg, #4338ca 0%, #6366f1 52%, #818cf8 100%);
  color: #fff;
}

.confirmed-edit-header__main {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex: 1 1 auto;
}

.confirmed-edit-header__clear {
  flex-shrink: 0;
  margin: 0 !important;
  border: 1px solid rgba(255, 255, 255, 0.45) !important;
  background: rgba(255, 255, 255, 0.14) !important;
  color: #fff !important;
  font-weight: 600;
  border-radius: 7px;
}

.confirmed-edit-header__clear:hover:not(.is-disabled) {
  background: rgba(254, 226, 226, 0.28) !important;
  border-color: #fecaca !important;
  color: #fff !important;
}

.confirmed-edit-header__clear-icon {
  margin-right: 4px;
}

.confirmed-edit-header__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  border-radius: 9px;
  background: rgba(255, 255, 255, 0.18);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.25);
}

.confirmed-edit-header__text {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

.confirmed-edit-header__title {
  font-size: 0.95rem;
  font-weight: 700;
  line-height: 1.25;
  letter-spacing: 0.01em;
}

.confirmed-edit-header__sub {
  font-size: 0.68rem;
  font-weight: 600;
  opacity: 0.88;
  letter-spacing: 0.04em;
}

.confirmed-edit-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.confirmed-edit-hero {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 8px;
  margin: 0;
  padding: 7px 9px;
  border-radius: 8px;
  background: linear-gradient(135deg, #eef2ff 0%, #f8fafc 100%);
  border: 1px solid #c7d2fe;
}

.confirmed-edit-badge {
  flex-shrink: 0;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 0.66rem;
  font-weight: 700;
  letter-spacing: 0.03em;
  color: #fff;
  background: linear-gradient(135deg, #059669 0%, #10b981 100%);
  box-shadow: 0 1px 4px rgba(16, 185, 129, 0.35);
}

.confirmed-edit-hero__code {
  flex-shrink: 0;
  padding: 2px 7px;
  border-radius: 6px;
  font-size: 0.7rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: #4338ca;
  background: rgba(99, 102, 241, 0.12);
  border: 1px solid rgba(99, 102, 241, 0.28);
}

.confirmed-edit-hero__product {
  flex: 1 1 140px;
  min-width: 0;
  font-size: 0.82rem;
  line-height: 1.35;
  color: var(--el-text-color-primary);
  word-break: break-word;
}

.confirmed-edit-hero__product strong {
  font-weight: 700;
  color: #312e81;
}

.confirmed-edit-hero__sep {
  margin: 0 4px;
  color: var(--el-text-color-placeholder);
}

.confirmed-edit-form {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.confirmed-edit-section {
  padding: 7px 9px 4px;
  border-radius: 8px;
  border: 1px solid transparent;
}

.confirmed-edit-section--people {
  background: linear-gradient(180deg, #faf5ff 0%, #fff 100%);
  border-color: #e9d5ff;
}

.confirmed-edit-section--time {
  background: linear-gradient(180deg, #eff6ff 0%, #fff 100%);
  border-color: #bfdbfe;
}

.confirmed-edit-section__title {
  display: flex;
  align-items: center;
  gap: 5px;
  margin: 0 0 4px;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.confirmed-edit-section--people .confirmed-edit-section__title {
  color: #7c3aed;
}

.confirmed-edit-section--time .confirmed-edit-section__title {
  color: #2563eb;
}

.confirmed-edit-section--defects {
  padding: 10px 12px;
  border-radius: 8px;
  background: #fafafa;
  border: 1px solid var(--el-border-color-lighter);
}

.confirmed-edit-defect-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 8px;
}

.defect-cell--compact {
  padding: 8px;
}

.defect-cell--compact .defect-cell__label {
  font-size: 11px;
  margin-bottom: 6px;
}

.confirmed-edit-form :deep(.confirmed-edit-form-item) {
  margin-bottom: 6px;
}

.confirmed-edit-form :deep(.confirmed-edit-form-item .el-form-item__label) {
  padding-bottom: 2px;
  font-size: 0.74rem;
  font-weight: 600;
  line-height: 1.2;
  color: var(--el-text-color-regular);
}

.confirmed-edit-form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 8px;
}

.confirmed-edit-full {
  width: 100%;
}

.confirmed-edit-form :deep(.el-input-number) {
  width: 100%;
}

.confirmed-edit-elapsed {
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 30px;
  padding: 5px 8px;
  border-radius: 8px;
  background: linear-gradient(135deg, #dbeafe 0%, #eff6ff 100%);
  border: 1px solid #93c5fd;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.65);
}

.confirmed-edit-elapsed__value {
  font-variant-numeric: tabular-nums;
  font-size: 1.05rem;
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: 0.04em;
  color: #1d4ed8;
}

.confirmed-edit-hint {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin: 0;
  padding: 6px 8px;
  border-radius: 7px;
  font-size: 0.72rem;
  line-height: 1.4;
  color: #92400e;
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
  border: 1px solid #fcd34d;
}

.confirmed-edit-hint__icon {
  flex-shrink: 0;
  margin-top: 1px;
  color: #d97706;
}

.confirmed-edit-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.confirmed-edit-btn {
  min-width: 88px;
  margin: 0 !important;
  font-weight: 600;
  border-radius: 8px;
}

.confirmed-edit-btn--save:not(.is-disabled) {
  border: none;
  background: linear-gradient(180deg, #6366f1 0%, #4f46e5 100%);
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.35);
}

.confirmed-edit-btn--save:not(.is-disabled):hover {
  background: linear-gradient(180deg, #818cf8 0%, #6366f1 100%);
}

.confirmed-edit-btn--cancel {
  border-color: var(--el-border-color);
}

@media (max-width: 480px) {
  .confirmed-edit-form-row,
  .confirmed-edit-form-row--metrics {
    grid-template-columns: 1fr;
  }
}


/* 検査：不良項目パネル（1行7項目・コンパクト） */
.defect-panel {
  margin-top: 6px;
  padding: 6px 6px 2px;
  border-radius: 6px;
  border: 1px solid var(--el-border-color-lighter);
  background: linear-gradient(180deg, var(--el-fill-color-blank) 0%, var(--el-fill-color-light) 100%);
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}
.defect-panel__head {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: 4px;
  margin-bottom: 4px;
}
.defect-panel__title {
  margin: 0;
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--el-text-color-primary);
}
.defect-panel__hint {
  margin: 0;
  font-size: 0.68rem;
  color: var(--el-text-color-secondary);
}
.defect-panel__empty {
  grid-column: 1 / -1;
  margin: 0;
  font-size: 0.75rem;
  color: var(--el-text-color-secondary);
  text-align: center;
  padding: 6px 0;
}
.defect-grid-by-process {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: min(100%, calc(7 * 118px + 6 * 4px));
}
.confirmed-edit-defect-groups {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.defect-process-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.defect-process-group__head {
  display: flex;
  align-items: baseline;
  gap: 6px;
  flex-wrap: wrap;
  padding: 2px 0 1px;
  border-bottom: 1px solid var(--el-border-color-extra-light);
}
.defect-process-group__label {
  flex-shrink: 0;
  font-size: 0.66rem;
  font-weight: 600;
  color: var(--el-text-color-secondary);
}
.defect-process-group__name {
  font-size: 0.74rem;
  font-weight: 800;
  color: #0f766e;
  line-height: 1.2;
}
.defect-process-group--edit .defect-process-group__head {
  margin-bottom: 2px;
}
.defect-grid {
  display: grid;
  grid-template-columns: repeat(7, 118px);
  gap: 4px;
  width: max-content;
  min-width: min(100%, calc(7 * 118px + 6 * 4px));
}
.defect-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  padding: 5px 6px;
  border-radius: 6px;
  border: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-blank);
}
.defect-cell--active {
  border-color: var(--el-color-warning-light-5);
  background: linear-gradient(180deg, #fffbeb 0%, #fef3c7 100%);
}
.defect-cell__label {
  font-size: 0.7rem;
  font-weight: 700;
  line-height: 1.25;
  min-height: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.defect-stepper {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 2px;
}
.defect-stepper__val {
  flex: 1;
  min-width: 0;
  text-align: center;
  font-size: 1.05rem;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}
.defect-stepper__btn {
  width: 30px !important;
  height: 30px !important;
  padding: 0 !important;
  flex-shrink: 0;
}
.defect-stepper__btn :deep(.el-icon) {
  font-size: 14px;
}
.toolbar-field-row--inspector .toolbar-inspector-select {
  width: min(var(--toolbar-inspector-select-w), 100%) !important;
  max-width: var(--toolbar-inspector-select-w);
  flex: 0 0 var(--toolbar-inspector-select-w);
}
.toolbar-field-row--inspector .toolbar-inspector-select :deep(.el-select__wrapper),
.toolbar-field-row--inspector .toolbar-inspector-select :deep(.el-input__wrapper) {
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}
.toolbar-product-scan-wrap {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex: 1 1 auto;
  min-width: 0;
}
.toolbar-field-row--product .product-select-toolbar {
  width: min(280px, 100%) !important;
  flex: 1 1 auto;
  min-width: 0;
}
.toolbar-product-scan-btn {
  height: var(--toolbar-h);
  min-height: var(--toolbar-h);
  padding: 0 10px;
  font-weight: 600;
  flex-shrink: 0;
}
.toolbar-product-scan-btn .el-icon {
  margin-right: 2px;
}
.toolbar-field-row--inspector {
  flex: 0 1 auto;
  max-width: calc(var(--toolbar-inspector-select-w) + var(--toolbar-h) + 5.5rem);
  gap: var(--toolbar-machine-gap, 6px);
  padding: 0 5px 0 0;
  border-radius: 10px;
  border: 1px solid #c4b5fd;
  background: linear-gradient(165deg, #f5f3ff 0%, var(--el-fill-color-blank) 55%, #ede9fe 100%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.75);
}
.toolbar-field-row--inspector .toolbar-field-row__icon {
  margin-left: -1px;
  border-radius: 9px 0 0 9px;
  background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%);
  box-shadow: 0 2px 8px rgba(109, 40, 217, 0.28);
}
.toolbar-field-row--inspector .toolbar-field-row__label { color: #5b21b6; }
.plan-row-card--confirmed { border-color: var(--el-color-success-light-5); }
.history-defects {
  list-style: none;
  margin: 8px 0 0;
  padding: 8px 10px;
  border-radius: 8px;
  background: var(--el-fill-color-light);
  font-size: 0.78rem;
}
.history-defects li { display: flex; justify-content: space-between; gap: 8px; padding: 2px 0; }

.inspection-history-section {
  --hist-accent: #0d9488;
  --hist-accent-soft: #ccfbf1;
  margin-top: 10px;
}

.inspection-history-print-frame {
  position: absolute;
  width: 0;
  height: 0;
  border: 0;
  padding: 0;
  margin: 0;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
}

.inspection-history-table-card {
  border-radius: var(--ca-radius, 10px);
  border: 1px solid var(--el-color-success-light-7);
  overflow: hidden;
  background: var(--el-fill-color-blank);
  box-shadow:
    0 1px 3px rgba(15, 23, 42, 0.05),
    0 4px 14px rgba(13, 148, 136, 0.06);
}

.inspection-history-table-card :deep(.el-card__body) {
  padding: 0;
}

.inspection-history-table-card__head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 6px 10px;
  padding: 6px 10px;
  border-bottom: 1px solid var(--el-color-success-light-7);
  background: linear-gradient(
    135deg,
    var(--el-color-success-light-9) 0%,
    #f0fdfa 48%,
    var(--el-fill-color-blank) 100%
  );
}

.inspection-history-table-card__title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.inspection-history-table-card__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  border-radius: 7px;
  color: var(--hist-accent);
  background: var(--hist-accent-soft);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.85);
}

.inspection-history-table-card__title {
  margin: 0;
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--el-text-color-primary);
  line-height: 1.25;
}

.inspection-history-table-card__qty-total {
  display: inline-flex;
  align-items: baseline;
  gap: 4px;
  flex-shrink: 0;
  margin-left: 2px;
  padding: 1px 8px;
  border-radius: 999px;
  font-size: 0.72rem;
  white-space: nowrap;
  background: var(--el-color-success-light-9);
  border: 1px solid var(--el-color-success-light-5);
}

.inspection-history-table-card__qty-total-label {
  color: var(--el-text-color-secondary);
  font-weight: 600;
}

.inspection-history-table-card__qty-total-value {
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  color: var(--el-color-success-dark-2);
}

.inspection-history-table-card__actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.inspection-history-table-card__count {
  flex-shrink: 0;
  min-width: 1.5rem;
  padding: 1px 7px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  text-align: center;
  color: var(--el-color-success-dark-2);
  background: var(--el-color-success-light-9);
  border: 1px solid var(--el-color-success-light-5);
  box-shadow: 0 1px 2px rgba(16, 185, 129, 0.1);
}

.inspection-history-table-wrap {
  width: 100%;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  padding: 0;
}

.inspection-history-table {
  width: 100%;
  min-width: 860px;
  --el-table-border-color: var(--el-border-color-extra-light);
  --el-table-header-bg-color: transparent;
  --el-table-row-hover-bg-color: #f0fdfa;
  --el-table-tr-bg-color: var(--el-fill-color-blank);
  --el-table-striped-bg-color: #f8fafc;
}

.inspection-history-table--compact :deep(.el-table__cell .cell) {
  padding-left: 4px;
  padding-right: 4px;
  line-height: 1.25;
}

.inspection-history-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.inspection-history-table :deep(.el-table__header-wrapper) {
  position: sticky;
  top: 0;
  z-index: 2;
}

.inspection-history-table :deep(.el-table__header th.el-table__cell) {
  padding: 4px 2px;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0;
  line-height: 1.2;
  color: #115e59;
  background: linear-gradient(180deg, #ecfdf5 0%, #f0fdfa 100%) !important;
  border-bottom: 1px solid var(--el-color-success-light-5) !important;
}

.inspection-history-table :deep(.el-table__body td.el-table__cell) {
  padding: 4px 2px;
  font-size: 0.74rem;
  border-bottom: 1px solid var(--el-border-color-extra-light);
  vertical-align: middle;
}

.inspection-history-table :deep(.el-table__row:hover > td.el-table__cell) {
  background: #f0fdfa !important;
}

.inspection-history-table :deep(.el-table__row--striped td.el-table__cell) {
  background: #f8fafc;
}

.inspection-history-table :deep(.el-table__fixed-left-patch) {
  background: linear-gradient(180deg, #ecfdf5 0%, #f0fdfa 100%);
}

.hist-cell-code {
  display: inline-block;
  max-width: 100%;
  padding: 2px 8px;
  border-radius: 6px;
  font-family: ui-monospace, 'Cascadia Code', monospace;
  font-size: 0.76rem;
  font-weight: 700;
  color: var(--hist-accent);
  background: var(--hist-accent-soft);
  border: 1px solid #99f6e4;
}

.hist-cell-day {
  display: inline-block;
  padding: 1px 5px;
  border-radius: 4px;
  font-variant-numeric: tabular-nums;
  font-size: 0.72rem;
  font-weight: 700;
  color: #0f766e;
  background: #ecfdf5;
  border: 1px solid #99f6e4;
  white-space: nowrap;
}

.hist-cell-name {
  font-weight: 600;
  font-size: 0.74rem;
  color: var(--el-text-color-primary);
  line-height: 1.2;
}

.hist-cell-inspector {
  display: inline-block;
  max-width: 100%;
  font-size: 0.72rem;
  color: var(--el-text-color-regular);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hist-cell-source-tag {
  font-size: 0.68rem;
}

.hist-cell-qty {
  display: inline-block;
  min-width: 1.8em;
  padding: 0 4px;
  border-radius: 4px;
  font-size: 0.76rem;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  color: var(--el-color-success-dark-2);
  background: var(--el-color-success-light-9);
}

.hist-cell-rate {
  font-variant-numeric: tabular-nums;
  font-size: 0.74rem;
  font-weight: 700;
  color: #b45309;
}

.hist-cell-efficiency {
  font-variant-numeric: tabular-nums;
  font-size: 0.74rem;
  font-weight: 700;
  color: #0369a1;
}

.hist-cell-defect-qty {
  font-variant-numeric: tabular-nums;
  font-size: 0.74rem;
  font-weight: 700;
  color: #b45309;
  cursor: default;
}

.hist-cell-time {
  font-variant-numeric: tabular-nums;
  font-size: 0.7rem;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.hist-cell-duration {
  font-variant-numeric: tabular-nums;
  font-size: 0.74rem;
  font-weight: 600;
  color: var(--el-text-color-regular);
}

.hist-cell-duration--active {
  font-weight: 700;
  color: var(--hist-accent);
}

.hist-cell-duration--muted {
  font-weight: 500;
  color: var(--el-text-color-placeholder);
}

.hist-cell-defects {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  max-width: 220px;
}

.hist-cell-defects__tag {
  margin: 0;
  border-radius: 6px;
  font-size: 0.72rem;
}

.hist-cell-defects__tag strong {
  font-weight: 800;
  margin-left: 2px;
}

.hist-cell-empty {
  color: var(--el-text-color-placeholder);
  font-size: 0.72rem;
}

.hist-cell-action-btn {
  padding: 0;
  min-height: 22px;
  height: 22px;
}

@media (max-width: 640px) {
  .inspection-history-table-card__head {
    padding: 5px 8px;
  }

  .inspection-history-table :deep(.el-table__header th.el-table__cell),
  .inspection-history-table :deep(.el-table__body td.el-table__cell) {
    padding: 3px 1px;
  }
}
</style>
