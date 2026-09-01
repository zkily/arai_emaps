import { buildPrintHtmlDocument, escapeHtml } from '@/utils/printWindow'

export interface PrintBucket {
  count: number
  quantity: number
  countAdj?: number
  quantityAdj?: number
}

export interface PrintMonthSummary {
  prodDataMgmt: PrintBucket
  auto: PrintBucket
  total: PrintBucket
  prodDataMgmtCountRatio: number
  prodDataMgmtQuantityRatio: number
  workingDays?: number
  standardWorkdays?: number
  workdayFactor?: number
}

export interface PrintProcessRow {
  processCd: string
  processName: string
  prodDataMgmt: PrintBucket
  auto: PrintBucket
  total: PrintBucket
  prodDataMgmtCountRatio: number
}

export interface PrintTrendRow {
  month: string
  workingDays?: number
  prodDataMgmtCount: number
  autoCount: number
  totalCount: number
  prodDataMgmtCountRatio: number
  prodDataMgmtQuantity: number
  autoQuantity: number
  totalQuantity: number
  prodDataMgmtQuantityRatio: number
  prodDataMgmtCountAdj?: number
  autoCountAdj?: number
  totalCountAdj?: number
  prodDataMgmtQuantityAdj?: number
}

export interface PrintKpiCard {
  label: string
  desc?: string
  countLabel?: string
  value: string
  unit?: string
  delta?: string
  sub?: string
  qtyLabel?: string
  qtyValue?: string
  qtyUnit?: string
  qtyDelta?: string
  qtySub?: string
}

export interface PrintProcessCompareRow {
  processCd: string
  processName: string
  current: PrintProcessRow
  compare: PrintProcessRow
  prodCountChange: number
  prodQtyChange: number
  autoCountChange: number
  prodCountAdjChange?: number
  prodQtyAdjChange?: number
}

export interface ManualEntryStatsPrintInput {
  printedAt: string
  month: string
  compareMonth: string
  trendMonths: number
  processLabel: string
  standardWorkdays?: number
  adjOnly?: boolean
  current: PrintMonthSummary
  compare: PrintMonthSummary
  monthOverMonth: {
    prodDataMgmtCountChange: number
    prodDataMgmtCountChangeRate: number | null
    prodDataMgmtQuantityChange: number
    prodDataMgmtQuantityChangeRate: number | null
    prodDataMgmtCountAdjChange?: number
    prodDataMgmtCountAdjChangeRate?: number | null
    prodDataMgmtQuantityAdjChange?: number
    prodDataMgmtQuantityAdjChangeRate?: number | null
    prodDataMgmtCountRatioChange: number
    prodDataMgmtQuantityRatioChange: number
    autoCountChange: number
    autoCountChangeRate: number | null
    autoQuantityChange: number
    autoQuantityChangeRate: number | null
    autoCountAdjChange?: number
    autoCountAdjChangeRate?: number | null
    autoQuantityAdjChange?: number
    autoQuantityAdjChangeRate?: number | null
  }
  kpiCards: PrintKpiCard[]
  byProcess: PrintProcessRow[]
  byProcessComparison: PrintProcessCompareRow[]
  byMonthTrend: PrintTrendRow[]
  chartImages: {
    monthCompare?: string
    qtyCompare?: string
    countTrend?: string
    qtyTrend?: string
    processCompare?: string
    process?: string
  }
  formatters: {
    fmtNum: (v?: number | null) => string
    fmtQty: (v?: number | null) => string
    fmtPct: (v?: number | null) => string
    fmtAdj?: (v?: number | null) => string
    fmtQtySen: (v?: number | null, withUnit?: boolean) => string
    fmtDelta: (change?: number | null, rate?: number | null) => string
    fmtQtyDelta: (change?: number | null, rate?: number | null) => string
    fmtPctPoint: (v?: number | null) => string
    fmtSignedNum: (v?: number | null) => string
    fmtSignedQty: (v?: number | null) => string
  }
}

const PRINT_STYLES = `
@page { size: A4 landscape; margin: 10mm 12mm; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: "Yu Gothic", "游ゴシック", "Meiryo", "メイリオ", sans-serif;
  font-size: 9pt;
  color: #111827;
  line-height: 1.45;
  background: #fff;
}
.report { width: 100%; }
.report-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  border-bottom: 2px solid #1e40af;
  padding-bottom: 8px;
  margin-bottom: 10px;
}
.report-title { font-size: 16pt; font-weight: 800; color: #1e3a8a; letter-spacing: 0.06em; }
.report-sub { font-size: 8.5pt; color: #4b5563; margin-top: 3px; }
.report-meta { text-align: right; font-size: 8pt; color: #6b7280; }
.report-meta div { margin-top: 2px; }
.cond-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 16px;
  padding: 6px 10px;
  margin-bottom: 10px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  font-size: 8.5pt;
}
.cond-bar span strong { color: #1e293b; margin-right: 4px; }
.section { margin-bottom: 10px; page-break-inside: avoid; }
.section-title {
  font-size: 10pt;
  font-weight: 800;
  color: #1e40af;
  border-left: 4px solid #3b82f6;
  padding-left: 8px;
  margin-bottom: 6px;
}
.kpi-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-bottom: 10px;
}
.kpi-box {
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  padding: 8px 10px;
  background: #fff;
}
.kpi-box-head {
  font-size: 8.5pt;
  font-weight: 800;
  color: #0f172a;
  margin-bottom: 1px;
}
.kpi-box-desc {
  font-size: 7pt;
  font-weight: 600;
  color: #94a3b8;
  margin-bottom: 5px;
}
.kpi-box-metric {
  padding: 4px 6px;
  margin-bottom: 4px;
  border: 1px solid #e2e8f0;
  border-radius: 3px;
  background: #f8fafc;
}
.kpi-box-metric:last-child { margin-bottom: 0; }
.kpi-box-metric-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 6px;
}
.kpi-box-metric-label {
  font-size: 7pt;
  font-weight: 700;
  color: #64748b;
}
.kpi-box-val { font-size: 11pt; font-weight: 800; color: #0f172a; text-align: right; }
.kpi-box-val small { font-size: 7pt; font-weight: 600; color: #94a3b8; margin-left: 2px; }
.kpi-box-delta { font-size: 7pt; color: #475569; margin-top: 2px; }
table.data {
  width: 100%;
  border-collapse: collapse;
  font-size: 8pt;
}
table.data th,
table.data td {
  border: 1px solid #94a3b8;
  padding: 4px 6px;
  text-align: center;
  vertical-align: middle;
}
table.data th {
  background: #e2e8f0;
  font-weight: 700;
  color: #1e293b;
}
table.data td.text-left { text-align: left; }
table.data td.num { text-align: right; font-variant-numeric: tabular-nums; }
table.data tr.subtotal td { background: #f1f5f9; font-weight: 700; }
table.data .group-head { background: #dbeafe; }
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-top: 4px;
}
.chart-box {
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  padding: 6px;
  page-break-inside: avoid;
}
.chart-box.wide { grid-column: 1 / -1; }
.chart-box-title {
  font-size: 8.5pt;
  font-weight: 700;
  color: #334155;
  margin-bottom: 4px;
  padding-bottom: 3px;
  border-bottom: 1px solid #e2e8f0;
}
.chart-box img { width: 100%; height: auto; display: block; }
.footnote {
  margin-top: 8px;
  font-size: 7pt;
  color: #6b7280;
  border-top: 1px solid #e5e7eb;
  padding-top: 5px;
  line-height: 1.5;
}
.footnote p {
  margin: 0 0 4px;
}
.footnote p:last-child {
  margin-bottom: 0;
}
.footnote--note {
  color: #475569;
  font-weight: 600;
}
@media print {
  .section { break-inside: avoid; }
  .chart-box { break-inside: avoid; }
}
`

function fmtAdjOf(input: ManualEntryStatsPrintInput, v?: number | null) {
  return input.formatters.fmtAdj ? input.formatters.fmtAdj(v) : input.formatters.fmtNum(v)
}

function adjCount(b?: PrintBucket | null) {
  if (!b) return 0
  return b.countAdj ?? b.count ?? 0
}

function adjQty(b?: PrintBucket | null) {
  if (!b) return 0
  return b.quantityAdj ?? b.quantity ?? 0
}

function th(text: string) {
  return `<th>${escapeHtml(text)}</th>`
}

function td(text: string, cls = '') {
  return `<td class="${cls}">${escapeHtml(text)}</td>`
}

function buildKpiSection(cards: PrintKpiCard[]): string {
  const items = cards
    .map((k) => {
      const countMetric = `<div class="kpi-box-metric">
        <div class="kpi-box-metric-row">
          <span class="kpi-box-metric-label">${escapeHtml(k.countLabel || '件数')}</span>
          <div class="kpi-box-val">${escapeHtml(k.value)}${k.unit ? `<small>${escapeHtml(k.unit)}</small>` : ''}</div>
        </div>
        ${k.delta ? `<div class="kpi-box-delta">${escapeHtml(k.delta)}</div>` : ''}
        ${k.sub ? `<div class="kpi-box-delta">${escapeHtml(k.sub)}</div>` : ''}
      </div>`
      const qtyMetric = k.qtyValue
        ? `<div class="kpi-box-metric">
        <div class="kpi-box-metric-row">
          <span class="kpi-box-metric-label">${escapeHtml(k.qtyLabel || '数量')}</span>
          <div class="kpi-box-val">${escapeHtml(k.qtyValue)}${k.qtyUnit ? `<small>${escapeHtml(k.qtyUnit)}</small>` : ''}</div>
        </div>
        ${k.qtyDelta ? `<div class="kpi-box-delta">${escapeHtml(k.qtyDelta)}</div>` : ''}
        ${k.qtySub ? `<div class="kpi-box-delta">${escapeHtml(k.qtySub)}</div>` : ''}
      </div>`
        : ''
      return `<div class="kpi-box">
        <div class="kpi-box-head">${escapeHtml(k.label)}</div>
        ${k.desc ? `<div class="kpi-box-desc">${escapeHtml(k.desc)}</div>` : ''}
        ${countMetric}
        ${qtyMetric}
      </div>`
    })
    .join('')
  return `<div class="section"><div class="section-title">主要指標（対象月）</div><div class="kpi-row">${items}</div></div>`
}

function buildMonthCompareTable(input: ManualEntryStatsPrintInput): string {
  const { current: cur, compare: cmp, month, compareMonth, formatters: f } = input
  const std = input.standardWorkdays || cur.standardWorkdays || 22
  const only = !!input.adjOnly
  const countRow = only
    ? `<tr>
          ${td(`件数（${std}日換算）`, 'text-left')}
          ${td(fmtAdjOf(input, adjCount(cur.prodDataMgmt)), 'num')}${td(fmtAdjOf(input, adjCount(cur.auto)), 'num')}${td(f.fmtPct(cur.prodDataMgmtCountRatio), 'num')}
          ${td(fmtAdjOf(input, adjCount(cmp.prodDataMgmt)), 'num')}${td(fmtAdjOf(input, adjCount(cmp.auto)), 'num')}${td(f.fmtPct(cmp.prodDataMgmtCountRatio), 'num')}
        </tr>`
    : `<tr>
          ${td('件数', 'text-left')}
          ${td(f.fmtNum(cur.prodDataMgmt.count), 'num')}${td(f.fmtNum(cur.auto.count), 'num')}${td(f.fmtPct(cur.prodDataMgmtCountRatio), 'num')}
          ${td(f.fmtNum(cmp.prodDataMgmt.count), 'num')}${td(f.fmtNum(cmp.auto.count), 'num')}${td(f.fmtPct(cmp.prodDataMgmtCountRatio), 'num')}
        </tr>
        <tr>
          ${td(`件数（${std}日換算）`, 'text-left')}
          ${td(fmtAdjOf(input, adjCount(cur.prodDataMgmt)), 'num')}${td(fmtAdjOf(input, adjCount(cur.auto)), 'num')}${td('—', 'num')}
          ${td(fmtAdjOf(input, adjCount(cmp.prodDataMgmt)), 'num')}${td(fmtAdjOf(input, adjCount(cmp.auto)), 'num')}${td('—', 'num')}
        </tr>`
  const qtyRow = only
    ? `<tr>
          ${td(`数量（${std}日換算）`, 'text-left')}
          ${td(f.fmtQty(adjQty(cur.prodDataMgmt)), 'num')}${td(f.fmtQty(adjQty(cur.auto)), 'num')}${td(f.fmtPct(cur.prodDataMgmtQuantityRatio), 'num')}
          ${td(f.fmtQty(adjQty(cmp.prodDataMgmt)), 'num')}${td(f.fmtQty(adjQty(cmp.auto)), 'num')}${td(f.fmtPct(cmp.prodDataMgmtQuantityRatio), 'num')}
        </tr>`
    : `<tr>
          ${td('数量', 'text-left')}
          ${td(f.fmtQty(cur.prodDataMgmt.quantity), 'num')}${td(f.fmtQty(cur.auto.quantity), 'num')}${td(f.fmtPct(cur.prodDataMgmtQuantityRatio), 'num')}
          ${td(f.fmtQty(cmp.prodDataMgmt.quantity), 'num')}${td(f.fmtQty(cmp.auto.quantity), 'num')}${td(f.fmtPct(cmp.prodDataMgmtQuantityRatio), 'num')}
        </tr>
        <tr>
          ${td(`数量（${std}日換算）`, 'text-left')}
          ${td(f.fmtQty(adjQty(cur.prodDataMgmt)), 'num')}${td(f.fmtQty(adjQty(cur.auto)), 'num')}${td('—', 'num')}
          ${td(f.fmtQty(adjQty(cmp.prodDataMgmt)), 'num')}${td(f.fmtQty(adjQty(cmp.auto)), 'num')}${td('—', 'num')}
        </tr>`
  return `<div class="section">
    <div class="section-title">月次比較${only ? `（${std}日換算）` : ''}</div>
    <table class="data">
      <thead>
        <tr>
          <th rowspan="2">区分</th>
          <th colspan="3">${escapeHtml(month)}（対象月・稼働日${cur.workingDays ?? '—'}日）</th>
          <th colspan="3">${escapeHtml(compareMonth)}（比較月・稼働日${cmp.workingDays ?? '—'}日）</th>
        </tr>
        <tr>
          ${th('実績修正件数')}${th('実績集計件数')}${th('修正比率')}
          ${th('実績修正件数')}${th('実績集計件数')}${th('修正比率')}
        </tr>
      </thead>
      <tbody>
        ${countRow}
        ${qtyRow}
        <tr class="subtotal">
          ${td(only ? `総計（${std}日換算）` : '総計', 'text-left')}
          ${td(only ? fmtAdjOf(input, adjCount(cur.total)) : f.fmtNum(cur.total.count), 'num')}${td('—')}${td('—')}
          ${td(only ? fmtAdjOf(input, adjCount(cmp.total)) : f.fmtNum(cmp.total.count), 'num')}${td('—')}${td('—')}
        </tr>
        <tr class="subtotal">
          ${td(only ? `総数量（${std}日換算）` : '総数量', 'text-left')}
          ${td(only ? f.fmtQty(adjQty(cur.total)) : f.fmtQty(cur.total.quantity), 'num')}${td('—')}${td('—')}
          ${td(only ? f.fmtQty(adjQty(cmp.total)) : f.fmtQty(cmp.total.quantity), 'num')}${td('—')}${td('—')}
        </tr>
      </tbody>
    </table>
  </div>`
}

function buildMomTable(input: ManualEntryStatsPrintInput): string {
  const m = input.monthOverMonth
  const f = input.formatters
  const std = input.standardWorkdays || input.current.standardWorkdays || 22
  return `<div class="section">
    <div class="section-title">前月比変動（${std}日換算）</div>
    <table class="data">
      <thead>
        <tr>
          <th>項目</th><th>件数変動</th><th>数量変動</th><th>比率変動</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          ${td('実績修正', 'text-left')}
          ${td(f.fmtDelta(m.prodDataMgmtCountAdjChange ?? m.prodDataMgmtCountChange, m.prodDataMgmtCountAdjChangeRate ?? m.prodDataMgmtCountChangeRate), 'num')}
          ${td(f.fmtQtyDelta(m.prodDataMgmtQuantityAdjChange ?? m.prodDataMgmtQuantityChange, m.prodDataMgmtQuantityAdjChangeRate ?? m.prodDataMgmtQuantityChangeRate), 'num')}
          ${td(f.fmtPctPoint(m.prodDataMgmtCountRatioChange), 'num')}
        </tr>
        <tr>
          ${td('実績集計', 'text-left')}
          ${td(f.fmtDelta(m.autoCountAdjChange ?? m.autoCountChange, m.autoCountAdjChangeRate ?? m.autoCountChangeRate), 'num')}
          ${td(f.fmtQtyDelta(m.autoQuantityAdjChange ?? m.autoQuantityChange, m.autoQuantityAdjChangeRate ?? m.autoQuantityChangeRate), 'num')}
          ${td('—', 'num')}
        </tr>
        <tr>
          ${td('数量比率（実績修正）', 'text-left')}
          ${td('—', 'num')}
          ${td('—', 'num')}
          ${td(f.fmtPctPoint(m.prodDataMgmtQuantityRatioChange), 'num')}
        </tr>
      </tbody>
    </table>
  </div>`
}

function buildTrendTable(input: ManualEntryStatsPrintInput): string {
  const f = input.formatters
  const std = input.standardWorkdays || input.current.standardWorkdays || 22
  const only = !!input.adjOnly
  const rows = input.byMonthTrend
    .map(
      (r) =>
        only
          ? `<tr>
        ${td(r.month, 'text-left')}
        ${td(String(r.workingDays ?? '—'), 'num')}
        ${td(fmtAdjOf(input, r.prodDataMgmtCountAdj ?? r.prodDataMgmtCount), 'num')}
        ${td(fmtAdjOf(input, r.autoCountAdj ?? r.autoCount), 'num')}
        ${td(fmtAdjOf(input, r.totalCountAdj ?? r.totalCount), 'num')}
        ${td(f.fmtPct(r.prodDataMgmtCountRatio), 'num')}
        ${td(f.fmtQty(r.prodDataMgmtQuantityAdj ?? r.prodDataMgmtQuantity), 'num')}
        ${td(f.fmtPct(r.prodDataMgmtQuantityRatio), 'num')}
      </tr>`
          : `<tr>
        ${td(r.month, 'text-left')}
        ${td(String(r.workingDays ?? '—'), 'num')}
        ${td(f.fmtNum(r.prodDataMgmtCount), 'num')}
        ${td(fmtAdjOf(input, r.prodDataMgmtCountAdj ?? r.prodDataMgmtCount), 'num')}
        ${td(f.fmtNum(r.autoCount), 'num')}
        ${td(f.fmtNum(r.totalCount), 'num')}
        ${td(f.fmtPct(r.prodDataMgmtCountRatio), 'num')}
        ${td(f.fmtQty(r.prodDataMgmtQuantity), 'num')}
        ${td(f.fmtQty(r.prodDataMgmtQuantityAdj ?? r.prodDataMgmtQuantity), 'num')}
        ${td(f.fmtPct(r.prodDataMgmtQuantityRatio), 'num')}
      </tr>`,
    )
    .join('')
  if (only) {
    return `<div class="section">
    <div class="section-title">月次推移（直近${input.trendMonths}ヶ月・${std}日換算）</div>
    <table class="data">
      <thead>
        <tr>
          <th rowspan="2">年月</th>
          <th rowspan="2">稼働日</th>
          <th colspan="4">件数（${std}日換算）</th>
          <th colspan="2">数量（${std}日換算）</th>
        </tr>
        <tr>
          ${th('実績修正')}${th('実績集計')}${th('総件数')}${th('修正比率')}
          ${th('実績修正')}${th('数量比率')}
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  </div>`
  }
  return `<div class="section">
    <div class="section-title">月次推移（直近${input.trendMonths}ヶ月）</div>
    <table class="data">
      <thead>
        <tr>
          <th rowspan="2">年月</th>
          <th rowspan="2">稼働日</th>
          <th colspan="5">件数</th>
          <th colspan="3">数量（絶対値合計）</th>
        </tr>
        <tr>
          ${th('実績修正')}${th(`${std}日換算`)}${th('実績集計')}${th('総件数')}${th('修正比率')}
          ${th('実績修正')}${th(`${std}日換算`)}${th('数量比率')}
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  </div>`
}

function buildProcessCompareTable(input: ManualEntryStatsPrintInput): string {
  const f = input.formatters
  const only = !!input.adjOnly
  const rows = input.byProcessComparison
    .map((r) =>
      only
        ? `<tr>
        ${td(r.processName, 'text-left')}
        ${td(fmtAdjOf(input, adjCount(r.current.prodDataMgmt)), 'num')}
        ${td(f.fmtQty(adjQty(r.current.prodDataMgmt)), 'num')}
        ${td(f.fmtPct(r.current.prodDataMgmtCountRatio), 'num')}
        ${td(fmtAdjOf(input, adjCount(r.compare.prodDataMgmt)), 'num')}
        ${td(f.fmtQty(adjQty(r.compare.prodDataMgmt)), 'num')}
        ${td(f.fmtPct(r.compare.prodDataMgmtCountRatio), 'num')}
        ${td(f.fmtSignedNum(r.prodCountAdjChange ?? r.prodCountChange), 'num')}
        ${td(f.fmtSignedQty(r.prodQtyAdjChange ?? r.prodQtyChange), 'num')}
        ${td(fmtAdjOf(input, adjCount(r.current.auto)), 'num')}
        ${td(fmtAdjOf(input, adjCount(r.compare.auto)), 'num')}
      </tr>`
        : `<tr>
        ${td(r.processName, 'text-left')}
        ${td(f.fmtNum(r.current.prodDataMgmt.count), 'num')}
        ${td(fmtAdjOf(input, adjCount(r.current.prodDataMgmt)), 'num')}
        ${td(f.fmtQty(r.current.prodDataMgmt.quantity), 'num')}
        ${td(f.fmtPct(r.current.prodDataMgmtCountRatio), 'num')}
        ${td(f.fmtNum(r.compare.prodDataMgmt.count), 'num')}
        ${td(fmtAdjOf(input, adjCount(r.compare.prodDataMgmt)), 'num')}
        ${td(f.fmtQty(r.compare.prodDataMgmt.quantity), 'num')}
        ${td(f.fmtPct(r.compare.prodDataMgmtCountRatio), 'num')}
        ${td(f.fmtSignedNum(r.prodCountAdjChange ?? r.prodCountChange), 'num')}
        ${td(f.fmtSignedQty(r.prodQtyAdjChange ?? r.prodQtyChange), 'num')}
        ${td(f.fmtNum(r.current.auto.count), 'num')}
        ${td(f.fmtNum(r.compare.auto.count), 'num')}
      </tr>`,
    )
    .join('')
  if (only) {
    return `<div class="section">
    <div class="section-title">工程別比較（${escapeHtml(input.compareMonth)} → ${escapeHtml(input.month)}・22日換算）</div>
    <table class="data">
      <thead>
        <tr>
          <th rowspan="2">工程</th>
          <th colspan="3" class="group-head">${escapeHtml(input.month)} 実績修正</th>
          <th colspan="3" class="group-head">${escapeHtml(input.compareMonth)} 実績修正</th>
          <th colspan="2" class="group-head">前月比(22日換算)</th>
          <th colspan="2" class="group-head">実績集計件数</th>
        </tr>
        <tr>
          ${th('件数')}${th('数量')}${th('比率')}
          ${th('件数')}${th('数量')}${th('比率')}
          ${th('件数')}${th('数量')}
          ${th(input.month)}${th(input.compareMonth)}
        </tr>
      </thead>
      <tbody>${rows || `<tr><td colspan="11">データなし</td></tr>`}</tbody>
    </table>
  </div>`
  }
  return `<div class="section">
    <div class="section-title">工程別比較（${escapeHtml(input.compareMonth)} → ${escapeHtml(input.month)}）</div>
    <table class="data">
      <thead>
        <tr>
          <th rowspan="2">工程</th>
          <th colspan="4" class="group-head">${escapeHtml(input.month)} 実績修正</th>
          <th colspan="4" class="group-head">${escapeHtml(input.compareMonth)} 実績修正</th>
          <th colspan="2" class="group-head">前月比(22日換算)</th>
          <th colspan="2" class="group-head">実績集計件数</th>
        </tr>
        <tr>
          ${th('件数')}${th('22日換算')}${th('数量')}${th('比率')}
          ${th('件数')}${th('22日換算')}${th('数量')}${th('比率')}
          ${th('件数')}${th('数量')}
          ${th(input.month)}${th(input.compareMonth)}
        </tr>
      </thead>
      <tbody>${rows || `<tr><td colspan="13">データなし</td></tr>`}</tbody>
    </table>
  </div>`
}

function buildProcessTable(input: ManualEntryStatsPrintInput): string {
  const f = input.formatters
  const only = !!input.adjOnly
  const rows = input.byProcess
    .map(
      (r) => `<tr>
        ${td(r.processName, 'text-left')}
        ${td(only ? fmtAdjOf(input, adjCount(r.prodDataMgmt)) : f.fmtNum(r.prodDataMgmt.count), 'num')}
        ${td(only ? f.fmtQty(adjQty(r.prodDataMgmt)) : f.fmtQty(r.prodDataMgmt.quantity), 'num')}
        ${td(f.fmtPct(r.prodDataMgmtCountRatio), 'num')}
        ${td(only ? fmtAdjOf(input, adjCount(r.auto)) : f.fmtNum(r.auto.count), 'num')}
        ${td(only ? f.fmtQty(adjQty(r.auto)) : f.fmtQty(r.auto.quantity), 'num')}
        ${td(only ? fmtAdjOf(input, adjCount(r.total)) : f.fmtNum(r.total.count), 'num')}
        ${td(only ? f.fmtQty(adjQty(r.total)) : f.fmtQty(r.total.quantity), 'num')}
      </tr>`,
    )
    .join('')
  return `<div class="section">
    <div class="section-title">工程別内訳（${escapeHtml(input.month)}${only ? '・22日換算' : ''}）</div>
    <table class="data">
      <thead>
        <tr>
          <th rowspan="2">工程</th>
          <th colspan="3" class="group-head">実績修正</th>
          <th colspan="2" class="group-head">実績集計</th>
          <th colspan="2" class="group-head">合計</th>
        </tr>
        <tr>
          ${th('件数')}${th('数量')}${th('比率')}
          ${th('件数')}${th('数量')}
          ${th('件数')}${th('数量')}
        </tr>
      </thead>
      <tbody>${rows || `<tr><td colspan="8">データなし</td></tr>`}</tbody>
    </table>
  </div>`
}

function buildChartsSection(images: ManualEntryStatsPrintInput['chartImages'], month: string): string {
  const items: string[] = []
  const push = (title: string, src: string | undefined, wide = false) => {
    if (!src) return
    items.push(
      `<div class="chart-box${wide ? ' wide' : ''}">
        <div class="chart-box-title">${escapeHtml(title)}</div>
        <img src="${src}" alt="${escapeHtml(title)}" />
      </div>`,
    )
  }
  push('月次比較（件数）', images.monthCompare)
  push('月次数量比較（単位：千）', images.qtyCompare)
  push('修正比率推移', images.countTrend)
  push('修正数量比率推移', images.qtyTrend)
  push('工程別比較', images.processCompare, true)
  push(`工程別内訳（${month}）`, images.process, true)
  if (!items.length) return ''
  return `<div class="section"><div class="section-title">グラフ</div><div class="charts-grid">${items.join('')}</div></div>`
}

export function buildManualEntryStatisticsPrintHtml(input: ManualEntryStatsPrintInput): string {
  const body = `<div class="report">
    <header class="report-header">
      <div>
        <div class="report-title">実績修正統計レポート</div>
        <div class="report-sub">実績修正 vs 実績集計の月次比較（手入力除外・稼働日22日換算・数量は絶対値合計）${input.adjOnly ? '　※22日換算のみ表示' : ''}</div>
      </div>
      <div class="report-meta">
        <div>出力日時：${escapeHtml(input.printedAt)}</div>
        <div>Smart-EMAPs / 在庫管理</div>
      </div>
    </header>
    <div class="cond-bar">
      <span><strong>対象月</strong>${escapeHtml(input.month)}（稼働日${input.current.workingDays ?? '—'}日）</span>
      <span><strong>比較月</strong>${escapeHtml(input.compareMonth)}（稼働日${input.compare.workingDays ?? '—'}日）</span>
      <span><strong>推移</strong>${input.trendMonths}ヶ月</span>
      <span><strong>工程</strong>${escapeHtml(input.processLabel)}</span>
      <span><strong>表示</strong>${input.adjOnly ? '22日換算のみ' : '実数＋換算'}</span>
      <span><strong>補正</strong>件数・数量 ×（標準${input.standardWorkdays || 22}日 ÷ 当月稼働日）</span>
      <span><strong>集計条件</strong>操作種別=実績 / 手入力除外 / 検査(KT09)はSD製品除外</span>
    </div>
    ${buildKpiSection(input.kpiCards)}
    <div class="two-col">
      ${buildMonthCompareTable(input)}
      ${buildMomTable(input)}
    </div>
    ${buildTrendTable(input)}
    ${buildProcessCompareTable(input)}
    ${buildProcessTable(input)}
    ${buildChartsSection(input.chartImages, input.month)}
    <div class="footnote">
      <p>※ 実績修正：source_file=生産データ管理。実績集計：上記以外（手入力を除く）。数量は各取引 quantity の絶対値を合計。</p>
      <p>※ 稼働日補正：補正値 = 実値 ×（標準稼働日22日 ÷ 当月稼働日）。月次比較・前月比は補正値を使用。修正比率は実数のまま（分子・分母が同じ係数で打ち消し合うため）。</p>
      <p class="footnote--note">※ 実績修正データは、前後工程の実績検証後に登録されたデータです。</p>
    </div>
  </div>`

  return buildPrintHtmlDocument('実績修正統計レポート', PRINT_STYLES, body)
}
