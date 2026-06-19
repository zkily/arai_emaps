import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'
import type {
  WeldingUtilizationDailyOperatorRow,
  WeldingUtilizationDailyRow,
  WeldingUtilizationOperatorRow,
} from '@/api/weldingManagement'

export interface WeldingUtilizationReportFilters {
  startDate: string
  endDate: string
  operatorLabel: string
  includeIncomplete: boolean
}

export type WeldingUtilizationKpiTone = 'green' | 'blue' | 'indigo' | 'amber' | 'violet'

export interface WeldingUtilizationKpiCardPrint {
  label: string
  value: string
  hint: string
  tone: WeldingUtilizationKpiTone
}

export interface WeldingUtilizationPrintCharts {
  daily: string | null
  overtime: string | null
}

export interface WeldingUtilizationReportContext {
  filters: WeldingUtilizationReportFilters
  kpiCards: WeldingUtilizationKpiCardPrint[]
  charts: WeldingUtilizationPrintCharts
  operatorRows: WeldingUtilizationOperatorRow[]
  dailyDetailRows: WeldingUtilizationDailyOperatorRow[]
}

export type UtilizationDailyChartRow =
  | WeldingUtilizationDailyRow
  | WeldingUtilizationDailyOperatorRow

export interface UtilizationDailyBatchItem {
  operatorUserId: number | null
  operatorLabel: string
  chartSrc: string | null
  dayCount: number
  avgUtilizationPercent: number | null
  sumOvertimeMin: number
}

function escHtml(value: unknown): string {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function printedAtJa(): string {
  return new Date().toLocaleString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function fmtPct(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return '—'
  return `${value.toFixed(1)}%`
}

function fmtInt(value: number | null | undefined): string {
  const n = Number(value ?? 0)
  return Number.isFinite(n) ? n.toLocaleString('ja-JP') : '0'
}

function fmtDurationMin(min: number | null | undefined): string {
  const n = Number(min ?? 0)
  if (!Number.isFinite(n) || n <= 0) return '0m'
  const h = Math.floor(n / 60)
  const m = n % 60
  if (h > 0) return m > 0 ? `${h}h${m}m` : `${h}h`
  return `${m}m`
}

function minToChartHours(min?: number | null): number {
  if (min == null || min <= 0) return 0
  return Math.round((min / 60) * 10) / 10
}

export function overtimeMinFromUtilizationRow(
  d: { overtime_min?: number | null; sum_overtime_sec?: number | null },
): number {
  if (d.overtime_min != null && d.overtime_min > 0) return d.overtime_min
  const sec = d.sum_overtime_sec ?? 0
  return sec > 0 ? Math.round(sec / 60) : 0
}

function overtimeHoursFromRow(
  d: { overtime_min?: number | null; sum_overtime_sec?: number | null },
): number {
  return minToChartHours(overtimeMinFromUtilizationRow(d))
}

function secToHours(sec?: number | null): string {
  if (sec == null || sec <= 0) return '—'
  return (sec / 3600).toFixed(1)
}

export function buildUtilizationDailyChartOption(daily: UtilizationDailyChartRow[]): EChartsOption {
  return {
    animation: false,
    grid: { left: 52, right: 48, top: 48, bottom: 36 },
    legend: {
      data: ['稼働率', '正味(H)'],
      top: 4,
      textStyle: { color: '#64748b', fontSize: 11 },
    },
    xAxis: {
      type: 'category',
      data: daily.map((d) => d.day.slice(5)),
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: { color: '#64748b', fontSize: 10 },
    },
    yAxis: [
      {
        type: 'value',
        name: '%',
        max: 120,
        nameTextStyle: { color: '#94a3b8', fontSize: 10 },
        axisLabel: { color: '#64748b', fontSize: 10 },
        splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
      },
      {
        type: 'value',
        name: 'H',
        splitLine: { show: false },
        nameTextStyle: { color: '#94a3b8', fontSize: 10 },
        axisLabel: { color: '#64748b', fontSize: 10 },
      },
    ],
    series: [
      {
        name: '稼働率',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        data: daily.map((d) => d.utilization_percent ?? 0),
        itemStyle: { color: '#10b981' },
        lineStyle: { width: 2.5 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(16,185,129,0.28)' },
            { offset: 1, color: 'rgba(16,185,129,0.02)' },
          ]),
        },
        label: {
          show: true,
          position: 'top',
          formatter: (params: { value?: number | string }) => {
            const v = Number(params.value ?? 0)
            return v > 0 ? `${v}%` : ''
          },
          color: '#059669',
          fontSize: 10,
          fontWeight: 600,
        },
      },
      {
        name: '正味(H)',
        type: 'bar',
        yAxisIndex: 1,
        barMaxWidth: 18,
        data: daily.map((d) => minToChartHours(d.sum_net_production_min)),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#e0e7ff' },
            { offset: 1, color: '#c7d2fe' },
          ]),
          borderRadius: [4, 4, 0, 0],
        },
        label: {
          show: true,
          position: 'inside',
          verticalAlign: 'middle',
          formatter: (params: { value?: number | string }) => {
            const v = Number(params.value ?? 0)
            return v > 0 ? v.toFixed(1) : ''
          },
          color: '#ef4444',
          fontSize: 10,
          fontWeight: 600,
        },
      },
    ],
  }
}

export function buildUtilizationOvertimeChartOption(daily: UtilizationDailyChartRow[]): EChartsOption {
  return {
    animation: false,
    grid: { left: 48, right: 20, top: 44, bottom: 36 },
    legend: {
      data: ['残業(H)'],
      top: 4,
      textStyle: { color: '#64748b', fontSize: 11 },
    },
    xAxis: {
      type: 'category',
      data: daily.map((d) => d.day.slice(5)),
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: { color: '#64748b', fontSize: 10 },
    },
    yAxis: {
      type: 'value',
      name: 'H',
      min: 0,
      nameTextStyle: { color: '#94a3b8', fontSize: 10 },
      axisLabel: { color: '#64748b', fontSize: 10 },
      splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
    },
    series: [
      {
        name: '残業(H)',
        type: 'bar',
        barMaxWidth: 22,
        data: daily.map((d) => overtimeHoursFromRow(d)),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#fcd34d' },
            { offset: 1, color: '#f59e0b' },
          ]),
          borderRadius: [5, 5, 0, 0],
        },
        label: {
          show: true,
          position: 'top',
          formatter: (params: { value?: number | string }) => {
            const v = Number(params.value ?? 0)
            return v > 0 ? v.toFixed(1) : ''
          },
          color: '#b45309',
          fontSize: 10,
          fontWeight: 700,
        },
      },
    ],
  }
}

function waitForChartPaint(): Promise<void> {
  return new Promise((resolve) => {
    requestAnimationFrame(() => {
      requestAnimationFrame(() => resolve())
    })
  })
}

export async function captureUtilizationChartDataUrl(
  option: EChartsOption,
  size: { width: number; height: number } = { width: 960, height: 380 },
): Promise<string | null> {
  const el = document.createElement('div')
  el.style.cssText = `position:fixed;left:0;top:0;width:${size.width}px;height:${size.height}px;opacity:0;pointer-events:none;z-index:-1;overflow:hidden;`
  document.body.appendChild(el)
  let chart: echarts.ECharts | null = null
  try {
    chart = echarts.init(el)
    chart.setOption(option, { notMerge: true })
    chart.resize()
    await waitForChartPaint()
    const url = chart.getDataURL({
      type: 'png',
      pixelRatio: 2,
      backgroundColor: '#ffffff',
    })
    return url.startsWith('data:image') ? url : null
  } catch {
    return null
  } finally {
    chart?.dispose()
    el.remove()
  }
}

export async function captureUtilizationDailyChartDataUrl(
  daily: UtilizationDailyChartRow[],
): Promise<string | null> {
  if (!daily.length) return null
  return captureUtilizationChartDataUrl(buildUtilizationDailyChartOption(daily))
}

function buildMetaLineHtml(
  filters: WeldingUtilizationReportFilters,
  printedAt: string,
  options?: { compact?: boolean },
): string {
  if (options?.compact) {
    return `<div class="meta-line">
      <span><span class="meta-line__label">集計期間</span> ${escHtml(filters.startDate)} ～ ${escHtml(filters.endDate)}</span>
      <span class="meta-line__sep">|</span>
      <span><span class="meta-line__label">出力日時</span> ${escHtml(printedAt)}</span>
    </div>`
  }
  return `<div class="meta-line">
      <span><span class="meta-line__label">集計期間</span> ${escHtml(filters.startDate)} ～ ${escHtml(filters.endDate)}</span>
      <span class="meta-line__sep">|</span>
      <span><span class="meta-line__label">出力日時</span> ${escHtml(printedAt)}</span>
      <span class="meta-line__sep">|</span>
      <span><span class="meta-line__label">溶接作業者</span> ${escHtml(filters.operatorLabel)}</span>
      <span class="meta-line__sep">|</span>
      <span><span class="meta-line__label">未確定を含む</span> ${escHtml(filters.includeIncomplete ? 'はい' : 'いいえ')}</span>
    </div>`
}

function kpiCardHtml(card: WeldingUtilizationKpiCardPrint): string {
  return `<div class="kpi-card kpi-card--${card.tone}">
    <div class="kpi-card__accent"></div>
    <div class="kpi-card__body">
      <div class="kpi-card__label">${escHtml(card.label)}</div>
      <div class="kpi-card__value">${escHtml(card.value)}</div>
      <div class="kpi-card__hint">${escHtml(card.hint)}</div>
    </div>
  </div>`
}

function panelBadge(text: string, tone = 'soft'): string {
  return `<span class="panel-badge panel-badge--${tone}">${escHtml(text)}</span>`
}

function panelSection(
  title: string,
  options: {
    titleInline?: string
    badges?: string
    theme: string
    chartSrc?: string | null
    chartAlt?: string
    tableHtml?: string
    pageBreak?: boolean
    chartTall?: boolean
    flowBreak?: boolean
  },
): string {
  const chartClass = options.chartTall ? 'chart-wrap chart-wrap--tall' : 'chart-wrap'
  const chartHtml = options.chartSrc
    ? `<div class="${chartClass}"><img class="chart-img" src="${options.chartSrc}" alt="${escHtml(options.chartAlt ?? title)}" /></div>`
    : ''

  const titleHtml = options.titleInline
    ? `<div class="panel__title-row">
        <span class="panel__title">${escHtml(title)}</span>
        <span class="panel__title-inline">${escHtml(options.titleInline)}</span>
      </div>`
    : `<div class="panel__title">${escHtml(title)}</div>`

  const flowClass = options.flowBreak ? ' panel--flow' : ''
  return `<section class="panel panel--${options.theme}${options.pageBreak ? ' panel--break' : ''}${flowClass}">
    <div class="panel__head">
      <div class="panel__titles">${titleHtml}</div>
      ${options.badges ? `<div class="panel__badges">${options.badges}</div>` : ''}
    </div>
    ${chartHtml}
    ${options.tableHtml ?? ''}
  </section>`
}

function tableHead(cells: string[]): string {
  return `<tr>${cells.map((c) => `<th>${escHtml(c)}</th>`).join('')}</tr>`
}

const PRINT_OPERATOR_TABLE_MAX = 12
const PRINT_DAILY_TABLE_MAX = 16

function buildOperatorPrintTable(rows: WeldingUtilizationOperatorRow[], maxRows = 0): string {
  if (!rows.length) return '<p class="empty">データなし</p>'
  const display = maxRows > 0 ? rows.slice(0, maxRows) : rows
  const body = display
    .map(
      (row, index) => `<tr>
        <td class="center">${escHtml(index + 1)}</td>
        <td>${escHtml(row.operator_name ?? '—')}</td>
        <td class="num">${escHtml(`${row.scheduled_work_day_count ?? 0}/${row.work_day_count ?? 0}`)}</td>
        <td class="num">${escHtml(fmtInt(row.session_count))}</td>
        <td class="num">${escHtml(secToHours(row.sum_net_production_sec))}</td>
        <td class="num">${escHtml(secToHours(row.sum_regular_sec))}</td>
        <td class="num warn">${escHtml(secToHours(row.sum_overtime_sec))}</td>
        <td class="num"><span class="pill pill--util">${escHtml(fmtPct(row.utilization_percent))}</span></td>
        <td class="num">${escHtml(fmtPct(row.calendar_utilization_percent))}</td>
      </tr>`,
    )
    .join('')
  const more =
    maxRows > 0 && rows.length > maxRows
      ? `<p class="table-more">… 他 ${rows.length - maxRows} 名</p>`
      : ''
  return `<table class="data data--operator data--compact">
    <thead>${tableHead(['#', '溶接作業者', '出勤日', '件', '正味(h)', '所定内(h)', '残業(h)', '稼働率', 'ｶﾚﾝﾀﾞｰ'])}</thead>
    <tbody>${body}</tbody>
  </table>${more}`
}

function buildDailyDetailPrintTable(rows: WeldingUtilizationDailyOperatorRow[], maxRows = 0): string {
  if (!rows.length) return '<p class="empty">データなし</p>'
  const display = maxRows > 0 ? rows.slice(0, maxRows) : rows
  const body = display
    .map(
      (row) => `<tr>
        <td>${escHtml(row.day)}</td>
        <td>${escHtml(row.operator_name ?? '—')}</td>
        <td class="num">${escHtml(fmtInt(row.session_count))}</td>
        <td class="num">${escHtml(row.scheduled_hours != null ? row.scheduled_hours.toFixed(1) : '—')}</td>
        <td class="num">${escHtml(fmtDurationMin(row.sum_net_production_min))}</td>
        <td class="num">${escHtml(fmtDurationMin(row.regular_min))}</td>
        <td class="num warn">${escHtml(fmtDurationMin(row.overtime_min))}</td>
        <td class="num"><span class="pill pill--util">${escHtml(fmtPct(row.utilization_percent))}</span></td>
      </tr>`,
    )
    .join('')
  const more =
    maxRows > 0 && rows.length > maxRows ? `<p class="table-more">… 他 ${rows.length - maxRows} 行</p>` : ''
  return `<table class="data data--daily data--compact">
    <thead>${tableHead(['生産日', '溶接作業者', '件', '所定(h)', '正味', '所定内', '残業', '稼働率'])}</thead>
    <tbody>${body}</tbody>
  </table>${more}`
}

type PrintOrientation = 'portrait' | 'landscape'

function getPrintStyles(mode: 'full' | 'section', orientation: PrintOrientation = 'portrait'): string {
  const compact = mode === 'full'
  const landscape = orientation === 'landscape'
  const chartTall = landscape ? '480px' : compact ? '280px' : '280px'
  const chartNormal = landscape ? '480px' : compact ? '280px' : '220px'
  const kpiMinH = compact ? '48px' : '58px'
  const pageRule = landscape
    ? '@page { size: A4 landscape; margin: 8mm 10mm; }'
    : '@page { size: A4 portrait; margin: 10mm 12mm; }'

  return `
    html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    ${pageRule}
    * { box-sizing: border-box; }
    body { margin: 0; color: #0f172a; font: 10px/1.4 "Segoe UI", "Yu Gothic UI", "Hiragino Sans", Meiryo, sans-serif; background: #fff; }
    .hd { border-bottom: 2px solid #10b981; padding-bottom: 10px; margin-bottom: 10px; }
    .hd__title { font-size: 17px; font-weight: 800; letter-spacing: -0.02em; }
    .hd__section { margin-top: 4px; font-size: 12px; font-weight: 700; color: #047857; }
    .meta-line { display: flex; flex-wrap: wrap; align-items: center; gap: 2px 0; margin-top: 6px; font-size: 8.5px; line-height: 1.5; color: #475569; }
    .meta-line__label { font-weight: 700; color: #334155; }
    .meta-line__sep { margin: 0 8px; color: #cbd5e1; }
    .kpi-row { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 5px; margin-bottom: 6px; }
    .kpi-card { position: relative; border-radius: 8px; padding: 6px 7px 5px; border: 1px solid transparent; overflow: hidden; min-height: ${kpiMinH}; }
    .kpi-card__accent { position: absolute; top: 0; left: 0; right: 0; height: 3px; }
    .kpi-card__label { font-size: 7.5px; font-weight: 700; letter-spacing: 0.02em; }
    .kpi-card__value { margin-top: 3px; font-size: 15px; font-weight: 800; line-height: 1.1; }
    .kpi-card__hint { margin-top: 2px; font-size: 7px; font-weight: 600; }
    .kpi-card--green { background: linear-gradient(160deg, #fff 0%, #d1fae5 100%); border-color: rgba(16,185,129,.22); }
    .kpi-card--green .kpi-card__accent { background: linear-gradient(90deg, #10b981, #34d399); }
    .kpi-card--green .kpi-card__label { color: #059669; }
    .kpi-card--green .kpi-card__value { color: #047857; }
    .kpi-card--green .kpi-card__hint { color: #34d399; }
    .kpi-card--blue { background: linear-gradient(160deg, #fff 0%, #e0f2fe 100%); border-color: rgba(14,165,233,.22); }
    .kpi-card--blue .kpi-card__accent { background: linear-gradient(90deg, #0ea5e9, #38bdf8); }
    .kpi-card--blue .kpi-card__label { color: #0284c7; }
    .kpi-card--blue .kpi-card__value { color: #0369a1; }
    .kpi-card--blue .kpi-card__hint { color: #38bdf8; }
    .kpi-card--indigo { background: linear-gradient(160deg, #fff 0%, #eef2ff 100%); border-color: rgba(99,102,241,.2); }
    .kpi-card--indigo .kpi-card__accent { background: linear-gradient(90deg, #6366f1, #818cf8); }
    .kpi-card--indigo .kpi-card__label { color: #6366f1; }
    .kpi-card--indigo .kpi-card__value { color: #4338ca; }
    .kpi-card--indigo .kpi-card__hint { color: #818cf8; }
    .kpi-card--amber { background: linear-gradient(160deg, #fff 0%, #ffedd5 100%); border-color: rgba(249,115,22,.22); }
    .kpi-card--amber .kpi-card__accent { background: linear-gradient(90deg, #f97316, #fb923c); }
    .kpi-card--amber .kpi-card__label { color: #ea580c; }
    .kpi-card--amber .kpi-card__value { color: #c2410c; }
    .kpi-card--amber .kpi-card__hint { color: #fb923c; }
    .kpi-card--violet { background: linear-gradient(160deg, #fff 0%, #ede9fe 100%); border-color: rgba(124,58,237,.22); }
    .kpi-card--violet .kpi-card__accent { background: linear-gradient(90deg, #7c3aed, #a78bfa); }
    .kpi-card--violet .kpi-card__label { color: #7c3aed; }
    .kpi-card--violet .kpi-card__value { color: #6d28d9; }
    .kpi-card--violet .kpi-card__hint { color: #a78bfa; }
    .panel { margin-top: 6px; padding: 6px 8px 8px; border-radius: 8px; border: 1px solid #e2e8f0; background: #fff; break-inside: avoid-page; page-break-inside: avoid; }
    .panel--break { break-before: page; page-break-before: always; margin-top: 0; }
    .panel--flow { break-inside: auto; page-break-inside: auto; margin-top: 0; }
    .panel--flow .chart-wrap { break-inside: avoid; page-break-inside: avoid; }
    .panel--chart { border-color: rgba(16,185,129,.18); background: linear-gradient(165deg, #fff 0%, #f0fdf4 100%); }
    .panel--overtime { border-color: rgba(245,158,11,.2); background: linear-gradient(165deg, #fff 0%, #fffbeb 100%); }
    .panel--operator { background: linear-gradient(165deg, #fff 0%, #f5f3ff 100%); border-color: rgba(99,102,241,.16); }
    .panel--daily { background: linear-gradient(165deg, #fff 0%, #f8fafc 100%); border-color: rgba(148,163,184,.2); }
    .charts-stack {
      display: flex;
      flex-direction: column;
      gap: 6px;
      margin-top: 6px;
    }
    .charts-stack .panel {
      margin-top: 0;
      width: 100%;
    }
    .charts-stack .chart-wrap {
      width: 100%;
      min-height: ${compact ? '240px' : '200px'};
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .charts-stack .chart-wrap--tall .chart-img,
    .charts-stack .chart-img {
      width: 100%;
      max-height: ${chartTall};
      object-fit: contain;
      object-position: center center;
    }
    .tables-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 6px;
      margin-top: 6px;
      break-inside: avoid-page;
      page-break-inside: avoid;
    }
    .tables-row .panel {
      margin-top: 0;
      min-width: 0;
      break-inside: avoid;
      page-break-inside: avoid;
    }
    .panel__head { display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; margin-bottom: 6px; }
    .panel__title { font-size: 11px; font-weight: 800; color: #1e293b; }
    .panel__title-row { display: flex; align-items: baseline; flex-wrap: wrap; gap: 8px; }
    .panel__title-inline { font-size: 11px; font-weight: 700; color: #047857; }
    .print-page { break-inside: avoid-page; page-break-inside: avoid; }
    .print-page--break { break-before: page; page-break-before: always; margin-top: 0; }
    .print-page .hd { margin-bottom: 8px; }
    .print-page .panel { margin-top: 0; }
    .panel__badges { display: flex; flex-wrap: wrap; gap: 4px; justify-content: flex-end; }
    .panel-badge { display: inline-block; padding: 2px 7px; border-radius: 999px; font-size: 7.5px; font-weight: 700; white-space: nowrap; }
    .panel-badge--soft { color: #64748b; background: rgba(148,163,184,.14); }
    .panel-badge--chart { color: #047857; background: rgba(16,185,129,.12); border: 1px solid rgba(16,185,129,.18); }
    .panel-badge--overtime { color: #b45309; background: rgba(245,158,11,.14); border: 1px solid rgba(245,158,11,.22); }
    .panel-badge--inspector { color: #4338ca; background: rgba(99,102,241,.12); border: 1px solid rgba(99,102,241,.18); }
    .chart-wrap { margin-bottom: 6px; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; background: linear-gradient(180deg, #fafbfc 0%, #fff 100%); }
    .chart-wrap--tall .chart-img { max-height: ${chartTall}; width: 100%; }
    .chart-img { display: block; width: 100%; height: auto; max-height: ${chartNormal}; object-fit: contain; }
    table.data { width: 100%; border-collapse: collapse; table-layout: fixed; margin-top: 4px; }
    table.data th, table.data td { border: 1px solid #cbd5e1; padding: 3px 4px; vertical-align: middle; word-break: break-word; }
    table.data th { font-size: 7.5px; font-weight: 700; }
    table.data td { font-size: 8px; }
    table.data--operator th { background: linear-gradient(180deg, #ede9fe, #e0e7ff); color: #4338ca; }
    table.data--daily th { background: linear-gradient(180deg, #d1fae5, #a7f3d0); color: #047857; }
    table.data tbody tr:nth-child(even) { background: rgba(248,250,252,.85); }
    .data--compact th, .data--compact td { font-size: 6.5px; padding: 2px 3px; }
    .num { text-align: right; font-variant-numeric: tabular-nums; }
    .center { text-align: center; }
    .warn { color: #c2410c; font-weight: 700; }
    .pill { display: inline-block; padding: 1px 5px; border-radius: 5px; font-size: 7.5px; font-weight: 700; }
    .pill--util { color: #047857; background: rgba(16,185,129,.12); border: 1px solid rgba(16,185,129,.18); }
    .empty, .table-more { margin: 4px 0 0; font-size: 8px; color: #94a3b8; }
    .ft { margin-top: 10px; padding-top: 6px; border-top: 1px solid #e2e8f0; font-size: 7.5px; color: #94a3b8; text-align: right; }
    @media print { body { margin: 0; } .ft { position: fixed; bottom: 0; right: 0; left: 0; } }
  `
}

function buildPrintDocumentShell(
  filters: WeldingUtilizationReportFilters,
  options: {
    mode: 'full' | 'section'
    orientation?: PrintOrientation
    sectionTitle?: string
    includeKpi?: boolean
    kpiCards?: WeldingUtilizationKpiCardPrint[]
    body: string
  },
): string {
  const printedAt = printedAtJa()
  const kpiHtml =
    options.includeKpi && options.kpiCards?.length
      ? `<div class="kpi-row">${options.kpiCards.map(kpiCardHtml).join('')}</div>`
      : ''
  return `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <title>溶接工程 — 稼働率分析${options.sectionTitle ? ` — ${options.sectionTitle}` : ''}</title>
  <style>${getPrintStyles(options.mode, options.orientation ?? 'portrait')}</style>
</head>
<body>
  <header class="hd">
    <div class="hd__title">溶接工程 — 稼働率分析</div>
    ${options.sectionTitle ? `<div class="hd__section">${escHtml(options.sectionTitle)}</div>` : ''}
    ${buildMetaLineHtml(filters, printedAt)}
  </header>
  ${kpiHtml}
  ${options.body}
  <footer class="ft">Smart-EMAPs · 溶接稼働率分析 · ${escHtml(printedAt)}</footer>
</body>
</html>`
}

function buildFullPrintBody(ctx: WeldingUtilizationReportContext): string {
  const { charts, operatorRows, dailyDetailRows } = ctx
  const operatorBadges = [panelBadge(`${operatorRows.length} 名`, 'operator')].join('')
  const dailyBadges = [panelBadge(`${dailyDetailRows.length} 行`, 'soft')].join('')
  return `
  <div class="charts-stack">
    ${panelSection('日別稼働率推移', {
      theme: 'chart',
      badges: panelBadge('稼働率 · 正味(H)', 'chart'),
      chartSrc: charts.daily,
      chartAlt: '日別稼働率推移',
      chartTall: true,
      tableHtml: '',
    })}
    ${panelSection('日別残業推移', {
      theme: 'overtime',
      badges: panelBadge('残業(H)', 'overtime'),
      chartSrc: charts.overtime,
      chartAlt: '日別残業推移',
      chartTall: true,
      tableHtml: '',
    })}
  </div>
  <div class="tables-row">
    ${panelSection('溶接作業者別サマリ', {
      theme: 'operator',
      badges: operatorBadges,
      tableHtml: buildOperatorPrintTable(operatorRows, PRINT_OPERATOR_TABLE_MAX),
    })}
    ${panelSection('溶接作業者 × 日別明細', {
      theme: 'daily',
      badges: dailyBadges,
      tableHtml: buildDailyDetailPrintTable(dailyDetailRows, PRINT_DAILY_TABLE_MAX),
    })}
  </div>
  `
}

export function buildWeldingUtilizationPrintHtml(ctx: WeldingUtilizationReportContext): string {
  return buildPrintDocumentShell(ctx.filters, {
    mode: 'full',
    includeKpi: true,
    kpiCards: ctx.kpiCards,
    body: buildFullPrintBody(ctx),
  })
}

export function buildWeldingUtilizationDailyPrintHtml(ctx: WeldingUtilizationReportContext): string {
  return buildPrintDocumentShell(ctx.filters, {
    sectionTitle: '日別稼働率推移',
    mode: 'section',
    orientation: 'landscape',
    body: panelSection('日別稼働率推移', {
      titleInline: ctx.filters.operatorLabel,
      theme: 'chart',
      badges: panelBadge('稼働率 · 正味(H)', 'chart'),
      chartSrc: ctx.charts.daily,
      chartAlt: '日別稼働率推移',
      chartTall: true,
      flowBreak: true,
      tableHtml: '',
    }),
  })
}

function buildDailyBatchPrintPageHeader(
  filters: WeldingUtilizationReportFilters,
  printedAt: string,
): string {
  return `<header class="hd">
    <div class="hd__title">溶接工程 — 稼働率分析</div>
    <div class="hd__section">日別稼働率推移（溶接作業者別・一括）</div>
    ${buildMetaLineHtml(filters, printedAt, { compact: true })}
  </header>`
}

export function buildWeldingUtilizationDailyBatchPrintHtml(
  filters: WeldingUtilizationReportFilters,
  items: UtilizationDailyBatchItem[],
): string {
  const printedAt = printedAtJa()
  const body = items
    .map((item, idx) => {
      const badges = [
        panelBadge(`${item.dayCount} 日`, 'soft'),
        item.avgUtilizationPercent != null
          ? panelBadge(`平均稼働率 ${fmtPct(item.avgUtilizationPercent)}`, 'chart')
          : '',
        item.sumOvertimeMin > 0 ? panelBadge(`残業合計 ${fmtDurationMin(item.sumOvertimeMin)}`, 'overtime') : '',
      ].join('')
      const panel = panelSection('日別稼働率推移', {
        titleInline: item.operatorLabel,
        theme: 'chart',
        badges,
        chartSrc: item.chartSrc,
        chartAlt: `日別稼働率推移 — ${item.operatorLabel}`,
        chartTall: true,
        flowBreak: true,
        tableHtml: '',
      })
      return `<div class="print-page${idx > 0 ? ' print-page--break' : ''}">
        ${buildDailyBatchPrintPageHeader(filters, printedAt)}
        ${panel}
      </div>`
    })
    .join('')

  return `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <title>溶接工程 — 稼働率分析 — 日別稼働率推移（溶接作業者別）</title>
  <style>${getPrintStyles('section', 'landscape')}</style>
</head>
<body>
  ${body}
  <footer class="ft">Smart-EMAPs · 溶接稼働率分析 · ${escHtml(printedAt)}</footer>
</body>
</html>`
}

export function openPrintDocument(html: string) {
  const win = window.open('', '_blank')
  if (!win) {
    throw new Error('ポップアップがブロックされました。ブラウザの設定を確認してください。')
  }
  win.document.write(html)
  win.document.close()

  const triggerPrint = () => {
    win.focus()
    win.print()
    setTimeout(() => win.close(), 400)
  }

  win.onload = () => {
    const images = win.document.images
    if (!images.length) {
      triggerPrint()
      return
    }
    let pending = images.length
    const onImageReady = () => {
      pending -= 1
      if (pending <= 0) triggerPrint()
    }
    for (let i = 0; i < images.length; i += 1) {
      const img = images.item(i)
      if (!img) {
        onImageReady()
        continue
      }
      if (img.complete) onImageReady()
      else {
        img.onload = onImageReady
        img.onerror = onImageReady
      }
    }
  }
}

export function printWeldingUtilizationReport(ctx: WeldingUtilizationReportContext) {
  openPrintDocument(buildWeldingUtilizationPrintHtml(ctx))
}

export function printWeldingUtilizationDailySection(ctx: WeldingUtilizationReportContext) {
  openPrintDocument(buildWeldingUtilizationDailyPrintHtml(ctx))
}

export function printWeldingUtilizationDailyBatch(
  filters: WeldingUtilizationReportFilters,
  items: UtilizationDailyBatchItem[],
) {
  openPrintDocument(buildWeldingUtilizationDailyBatchPrintHtml(filters, items))
}

export function avgUtilizationPercent(daily: UtilizationDailyChartRow[]): number | null {
  const values = daily
    .map((d) => d.utilization_percent)
    .filter((v): v is number => v != null && Number.isFinite(v))
  if (!values.length) return null
  return Math.round((values.reduce((a, b) => a + b, 0) / values.length) * 10) / 10
}

export function sumOvertimeMinFromDaily(daily: UtilizationDailyChartRow[]): number {
  return daily.reduce((sum, d) => sum + overtimeMinFromUtilizationRow(d), 0)
}
