import type {
  WeldingProductivityAnalysisData,
  WeldingProductivityOperatorRow,
  WeldingProductivityProductOperatorRanking,
  WeldingProductivityProductRow,
  WeldingProductivitySessionRow,
} from '@/api/weldingManagement'

export interface WeldingProductivityReportFilters {
  startDate: string
  endDate: string
  operatorLabel: string
  productLabel: string
  includeIncomplete: boolean
}

export type WeldingProductivityKpiTone = 'indigo' | 'sky' | 'amber' | 'emerald' | 'violet'

export interface WeldingProductivityKpiCardPrint {
  label: string
  value: string
  hint: string
  tone: WeldingProductivityKpiTone
}

export interface WeldingProductivityPrintCharts {
  daily: string | null
  operator: string | null
  product: string | null
}

export interface WeldingProductivityPrintChartsExtended extends WeldingProductivityPrintCharts {
  productRank?: string | null
}

export interface WeldingProductivityProductRankPrintContext {
  selected: WeldingProductivityProductOperatorRanking | null
  topOverview: WeldingProductivityProductOperatorRanking[]
  stats: {
    topEfficiency: number | null
    avgEfficiency: number | null
    operatorCount: number
  } | null
}

export interface WeldingProductivityReportContext {
  filters: WeldingProductivityReportFilters
  kpiCards: WeldingProductivityKpiCardPrint[]
  charts: WeldingProductivityPrintChartsExtended
  operatorRows: Array<WeldingProductivityOperatorRow & { avg_efficiency_per_hour?: number | null }>
  productRows: Array<WeldingProductivityProductRow & { avg_efficiency_per_hour?: number | null }>
  operatorSectionAvgEfficiency: number | null
  productSectionTotalQty: number
  productRank: WeldingProductivityProductRankPrintContext
}

export type WeldingProductivityPrintSection =
  | 'full'
  | 'daily'
  | 'operator'
  | 'product'
  | 'product-rank'

/** @deprecated use WeldingProductivityReportContext */
export type WeldingProductivityPrintPayload = WeldingProductivityReportContext

const UTF8_BOM = '\uFEFF'

function escHtml(value: unknown): string {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function escapeCsvCell(value: unknown): string {
  const text = value == null ? '' : String(value)
  if (/[",\n\r]/.test(text)) return `"${text.replace(/"/g, '""')}"`
  return text
}

function csvLine(cells: unknown[]): string {
  return cells.map(escapeCsvCell).join(',')
}

function fmtInt(value: number | null | undefined): string {
  const n = Number(value ?? 0)
  return Number.isFinite(n) ? n.toLocaleString('ja-JP') : '0'
}

function fmtPct(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return ''
  return `${value.toFixed(1)}%`
}

function fmtEfficiency(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return ''
  return String(Math.round(value))
}

function fmtDurationMin(min: number | null | undefined): string {
  const n = Number(min ?? 0)
  if (!Number.isFinite(n) || n <= 0) return ''
  const h = Math.floor(n / 60)
  const m = n % 60
  if (h > 0) return `${h}h${m}m`
  return `${m}m`
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

function reportFileBase(filters: WeldingProductivityReportFilters): string {
  return `溶接生産性分析_${filters.startDate}_${filters.endDate}`
}

function metaCsvLines(filters: WeldingProductivityReportFilters): string[] {
  return [
    csvLine(['# 溶接工程 — 生産性分析']),
    csvLine(['# 集計期間', `${filters.startDate} ～ ${filters.endDate}`]),
    csvLine(['# 溶接作業者', filters.operatorLabel]),
    csvLine(['# 製品', filters.productLabel]),
    csvLine(['# 未確定を含む', filters.includeIncomplete ? 'はい' : 'いいえ']),
    csvLine(['# 出力日時', printedAtJa()]),
    '',
  ]
}

export function downloadCsvFile(filename: string, content: string) {
  const blob = new Blob([UTF8_BOM + content], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.rel = 'noopener'
  document.body.appendChild(anchor)
  anchor.click()
  document.body.removeChild(anchor)
  URL.revokeObjectURL(url)
}

export function buildSessionsCsv(
  data: WeldingProductivityAnalysisData,
  filters: WeldingProductivityReportFilters,
): string {
  const lines = [
    ...metaCsvLines(filters),
    csvLine([
      '生産日',
      '溶接作業者',
      '設備',
      'CD',
      '製品名',
      '生産数',
      '不良数',
      '不良率',
      '能率(個/時)',
      '正味稼働(分)',
      '停止(分)',
      '状態',
    ]),
  ]
  for (const row of data.sessions) {
    lines.push(
      csvLine([
        row.production_day ?? '',
        row.operator_display_name ?? row.mes_operator_name ?? '',
        row.welding_machine ?? '',
        row.product_cd ?? '',
        row.product_name ?? '',
        row.actual_production_quantity ?? 0,
        row.defect_qty ?? 0,
        fmtPct(row.defect_rate_percent),
        fmtEfficiency(row.efficiency_per_hour),
        row.net_production_min ?? '',
        row.paused_min ?? '',
        row.is_completed ? '確定' : '未確定',
      ]),
    )
  }
  return lines.join('\r\n')
}

export function buildSummaryCsv(
  data: WeldingProductivityAnalysisData,
  filters: WeldingProductivityReportFilters,
  extras: {
    operatorRows: Array<WeldingProductivityOperatorRow & { avg_efficiency_per_hour?: number | null }>
    productRows: Array<WeldingProductivityProductRow & { avg_efficiency_per_hour?: number | null }>
    productRankTop: WeldingProductivityProductOperatorRanking[]
    defectLabel: (defectCd: string) => string
  },
): string {
  const lines = [...metaCsvLines(filters)]
  const s = data.summary

  lines.push(csvLine(['【サマリー】']))
  lines.push(
    csvLine([
      '確定セッション',
      '全セッション',
      '生産数合計',
      '不良数',
      '不良率',
      '総合能率(個/時)',
      '正味稼働(分)',
      '停止(分)',
    ]),
  )
  lines.push(
    csvLine([
      s.completed_session_count ?? 0,
      s.session_count ?? 0,
      s.sum_actual_qty ?? 0,
      s.sum_defect_qty ?? 0,
      fmtPct(s.defect_rate_percent),
      fmtEfficiency(s.efficiency_per_hour),
      s.sum_net_production_min ?? 0,
      s.sum_paused_min ?? 0,
    ]),
  )
  lines.push('')

  lines.push(csvLine(['【日別推移】']))
  lines.push(csvLine(['日付', '件数', '確定件数', '生産数', '不良数', '不良率', '能率(個/時)', '正味稼働(分)']))
  for (const row of data.daily) {
    lines.push(
      csvLine([
        row.day,
        row.session_count ?? 0,
        row.completed_session_count ?? 0,
        row.sum_actual_qty ?? 0,
        row.sum_defect_qty ?? 0,
        fmtPct(row.defect_rate_percent),
        fmtEfficiency(row.efficiency_per_hour),
        row.sum_net_production_min ?? 0,
      ]),
    )
  }
  lines.push('')

  lines.push(csvLine(['【溶接作業者別】']))
  lines.push(csvLine(['溶接作業者', '件数', '生産数', '不良率', '平均能率(個/時)', '正味稼働(分)']))
  for (const row of extras.operatorRows) {
    lines.push(
      csvLine([
        row.operator_name ?? '',
        row.session_count ?? 0,
        row.sum_actual_qty ?? 0,
        fmtPct(row.defect_rate_percent),
        fmtEfficiency(row.avg_efficiency_per_hour),
        row.sum_net_production_min ?? 0,
      ]),
    )
  }
  lines.push('')

  lines.push(csvLine(['【製品別】']))
  lines.push(csvLine(['CD', '製品名', '件数', '生産数', '不良率', '平均能率(個/時)']))
  for (const row of extras.productRows) {
    lines.push(
      csvLine([
        row.product_cd ?? '',
        row.product_name ?? '',
        row.session_count ?? 0,
        row.sum_actual_qty ?? 0,
        fmtPct(row.defect_rate_percent),
        fmtEfficiency(row.avg_efficiency_per_hour),
      ]),
    )
  }
  lines.push('')

  lines.push(csvLine(['【製品別 — 能率 TOP1】']))
  lines.push(csvLine(['CD', '製品名', 'TOP溶接作業者', '能率(個/時)', '対象人数', '生産数']))
  for (const row of extras.productRankTop) {
    lines.push(
      csvLine([
        row.product_cd,
        row.product_name ?? '',
        row.top_operator_name ?? '',
        fmtEfficiency(row.top_efficiency_per_hour),
        row.ranked_operator_count ?? 0,
        row.sum_actual_qty ?? 0,
      ]),
    )
  }
  lines.push('')

  lines.push(csvLine(['【不良内訳（KT07）】']))
  lines.push(csvLine(['不良CD', '不良名', '数量']))
  for (const row of data.defect_by_item) {
    lines.push(csvLine([row.defect_cd, extras.defectLabel(row.defect_cd), row.qty]))
  }

  return lines.join('\r\n')
}

function kpiCardHtml(card: WeldingProductivityKpiCardPrint): string {
  return `<div class="kpi-card kpi-card--${card.tone}">
    <div class="kpi-card__accent"></div>
    <div class="kpi-card__body">
      <div class="kpi-card__label">${escHtml(card.label)}</div>
      <div class="kpi-card__value">${escHtml(card.value)}</div>
      <div class="kpi-card__hint">${escHtml(card.hint)}</div>
    </div>
  </div>`
}

function rankBadgeHtml(rank: number): string {
  let cls = 'rank-badge'
  if (rank === 1) cls += ' rank-badge--gold'
  else if (rank === 2) cls += ' rank-badge--silver'
  else if (rank === 3) cls += ' rank-badge--bronze'
  return `<span class="${cls}">${escHtml(rank)}</span>`
}

function operatorRowRankHtml(index: number): string {
  let cls = 'row-rank'
  if (index === 0) cls += ' row-rank--gold'
  else if (index === 1) cls += ' row-rank--silver'
  else if (index === 2) cls += ' row-rank--bronze'
  return `<span class="${cls}">${escHtml(index + 1)}</span>`
}

function panelBadge(text: string, tone = 'soft'): string {
  return `<span class="panel-badge panel-badge--${tone}">${escHtml(text)}</span>`
}

function panelSection(
  title: string,
  options: {
    subtitle?: string
    titleInline?: string
    badges?: string
    theme: string
    chartSrc?: string | null
    chartAlt?: string
    tableHtml: string
    pageBreak?: boolean
    chartTall?: boolean
    /** グラフ領域を非表示（表のみのパネル向け） */
    hideChart?: boolean
    /** 単独印刷など、第1ページから自然に改ページしたい場合 */
    flowBreak?: boolean
  },
): string {
  const chartClass = options.chartTall ? 'chart-wrap chart-wrap--tall' : 'chart-wrap'
  const chartHtml = options.hideChart
    ? ''
    : options.chartSrc
      ? `<div class="${chartClass}"><img class="chart-img" src="${options.chartSrc}" alt="${escHtml(options.chartAlt ?? title)}" /></div>`
      : '<p class="chart-empty">グラフを表示できません</p>'

  const titleHtml = options.titleInline
    ? `<div class="panel__title-row">
        <span class="panel__title">${escHtml(title)}</span>
        <span class="panel__title-inline">${escHtml(options.titleInline)}</span>
      </div>`
    : `<div class="panel__title">${escHtml(title)}</div>
        ${options.subtitle ? `<div class="panel__subtitle">${escHtml(options.subtitle)}</div>` : ''}`

  const flowClass = options.flowBreak ? ' panel--flow' : ''
  return `<section class="panel panel--${options.theme}${options.pageBreak ? ' panel--break' : ''}${flowClass}">
    <div class="panel__head">
      <div class="panel__titles">${titleHtml}</div>
      ${options.badges ? `<div class="panel__badges">${options.badges}</div>` : ''}
    </div>
    ${chartHtml}
    ${options.tableHtml}
  </section>`
}

function tableHead(cells: string[]): string {
  return `<tr>${cells.map((c) => `<th>${escHtml(c)}</th>`).join('')}</tr>`
}

const PRINT_OPERATOR_TABLE_MAX = 5
function buildOperatorPrintTable(
  rows: Array<WeldingProductivityOperatorRow & { avg_efficiency_per_hour?: number | null }>,
  maxRows = 0,
): string {
  if (!rows.length) return '<p class="empty">データなし</p>'
  const display = maxRows > 0 ? rows.slice(0, maxRows) : rows
  const body = display
    .map(
      (row, index) => `<tr>
        <td class="center">${operatorRowRankHtml(index)}</td>
        <td>${escHtml(row.operator_name ?? '—')}</td>
        <td class="num">${escHtml(fmtInt(row.session_count))}</td>
        <td class="num">${escHtml(fmtInt(row.sum_actual_qty))}</td>
        <td class="num warn">${escHtml(fmtPct(row.defect_rate_percent))}</td>
        <td class="num"><span class="pill pill--operator">${escHtml(fmtEfficiency(row.avg_efficiency_per_hour))}</span></td>
      </tr>`,
    )
    .join('')
  const more =
    maxRows > 0 && rows.length > maxRows
      ? `<p class="table-more">… 他 ${rows.length - maxRows} 名</p>`
      : ''
  return `<table class="data data--operator data--compact">
    <thead>${tableHead(['#', '溶接作業者', '件', '生産', '不良率', '平均能率'])}</thead>
    <tbody>${body}</tbody>
  </table>${more}`
}

function buildProductPrintTable(
  rows: Array<WeldingProductivityProductRow & { avg_efficiency_per_hour?: number | null }>,
): string {
  if (!rows.length) return '<p class="empty">データなし</p>'
  const body = rows
    .map(
      (row) => `<tr>
        <td><span class="product-cd">${escHtml(row.product_cd ?? '')}</span></td>
        <td>${escHtml(row.product_name ?? '')}</td>
        <td class="num">${escHtml(fmtInt(row.session_count))}</td>
        <td class="num">${escHtml(fmtInt(row.sum_actual_qty))}</td>
        <td class="num warn">${escHtml(fmtPct(row.defect_rate_percent))}</td>
        <td class="num"><span class="pill pill--product">${escHtml(fmtEfficiency(row.avg_efficiency_per_hour))}</span></td>
      </tr>`,
    )
    .join('')
  return `<table class="data data--product">
    <thead>${tableHead(['CD', '製品名', '件', '生産', '不良率', '能率'])}</thead>
    <tbody>${body}</tbody>
  </table>`
}

function buildProductRankOperatorTable(rows: WeldingProductivityOperatorRow[]): string {
  if (!rows.length) return '<p class="empty">データなし</p>'
  const body = rows
    .map(
      (row) => `<tr>
        <td class="center">${rankBadgeHtml(row.rank ?? 0)}</td>
        <td>${escHtml(row.operator_name ?? '—')}</td>
        <td class="num">${escHtml(fmtInt(row.session_count))}</td>
        <td class="num">${escHtml(fmtInt(row.sum_actual_qty))}</td>
        <td class="num"><span class="pill pill--rank">${escHtml(fmtEfficiency(row.efficiency_per_hour))}</span></td>
        <td class="num warn">${escHtml(fmtPct(row.defect_rate_percent))}</td>
      </tr>`,
    )
    .join('')
  return `<table class="data data--rank">
    <thead>${tableHead(['順位', '溶接作業者', '件', '生産', '能率', '不良率'])}</thead>
    <tbody>${body}</tbody>
  </table>`
}

function buildProductRankOverviewTable(rows: WeldingProductivityProductOperatorRanking[]): string {
  if (!rows.length) return '<p class="empty">データなし</p>'
  const body = rows
    .map(
      (row) => `<tr>
        <td><span class="product-cd product-cd--rank">${escHtml(row.product_cd)}</span></td>
        <td>${escHtml(row.product_name ?? '')}</td>
        <td>${escHtml(row.top_operator_name ?? '—')}</td>
        <td class="num"><span class="pill pill--rank">${escHtml(fmtEfficiency(row.top_efficiency_per_hour))}</span></td>
        <td class="num">${escHtml(row.ranked_operator_count ?? 0)}</td>
        <td class="num">${escHtml(fmtInt(row.sum_actual_qty))}</td>
      </tr>`,
    )
    .join('')
  return `<table class="data data--rank-overview">
    <thead>${tableHead(['CD', '製品名', 'TOP溶接作業者', '能率', '対象人数', '生産'])}</thead>
    <tbody>${body}</tbody>
  </table>`
}

function buildProductRankHeroHtml(
  ranking: WeldingProductivityProductOperatorRanking,
  stats: WeldingProductivityProductRankPrintContext['stats'],
): string {
  return `<div class="rank-hero">
    <div class="rank-hero__main">
      <span class="rank-hero__cd">${escHtml(ranking.product_cd)}</span>
      <div class="rank-hero__name">${escHtml(ranking.product_name || '—')}</div>
    </div>
    <div class="rank-hero__stats">
      <div class="rank-hero__stat"><span class="rank-hero__stat-label">生産合計</span><span class="rank-hero__stat-val">${escHtml(fmtInt(ranking.sum_actual_qty))}</span></div>
      <div class="rank-hero__stat"><span class="rank-hero__stat-label">溶接作業者</span><span class="rank-hero__stat-val">${escHtml(stats?.operatorCount ?? ranking.ranked_operator_count ?? 0)}<small>名</small></span></div>
      <div class="rank-hero__stat rank-hero__stat--accent"><span class="rank-hero__stat-label">TOP能率</span><span class="rank-hero__stat-val">${escHtml(fmtEfficiency(stats?.topEfficiency ?? ranking.top_efficiency_per_hour))}<small>個/時</small></span></div>
      <div class="rank-hero__stat"><span class="rank-hero__stat-label">平均能率</span><span class="rank-hero__stat-val">${escHtml(fmtEfficiency(stats?.avgEfficiency ?? null))}<small>個/時</small></span></div>
    </div>
  </div>`
}

function buildMetaLineHtml(
  filters: WeldingProductivityReportFilters,
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
      <span><span class="meta-line__label">製品</span> ${escHtml(filters.productLabel)}</span>
      <span class="meta-line__sep">|</span>
      <span><span class="meta-line__label">未確定を含む</span> ${escHtml(filters.includeIncomplete ? 'はい' : 'いいえ')}</span>
    </div>`
}

type PrintOrientation = 'portrait' | 'landscape'

function getPrintStyles(mode: 'full' | 'section', orientation: PrintOrientation = 'portrait'): string {
  const compact = mode === 'full'
  const landscape = orientation === 'landscape'
  const chartTall = landscape ? '480px' : compact ? '96px' : '280px'
  const chartNormal = landscape ? '480px' : compact ? '82px' : '220px'
  const kpiMinH = compact ? '48px' : '58px'
  const pageRule = landscape
    ? '@page { size: A4 landscape; margin: 8mm 10mm; }'
    : '@page { size: A4 portrait; margin: 10mm 12mm; }'

  return `
    html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    ${pageRule}
    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: #0f172a;
      font: 10px/1.4 "Segoe UI", "Yu Gothic UI", "Hiragino Sans", Meiryo, sans-serif;
      background: #fff;
    }
    .hd {
      border-bottom: 2px solid #6366f1;
      padding-bottom: 10px;
      margin-bottom: 10px;
    }
    .hd__title { font-size: 17px; font-weight: 800; letter-spacing: -0.02em; }
    .hd__section { margin-top: 4px; font-size: 12px; font-weight: 700; color: #4338ca; }
    .hd__section-row {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 6px 14px;
      margin-top: 4px;
    }
    .hd__section-row .hd__section { margin-top: 0; flex-shrink: 0; }
    .hd__section-row .meta-line { margin-top: 0; flex: 1; min-width: 0; justify-content: flex-end; }
    .meta-line {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 2px 0;
      margin-top: 6px;
      font-size: 8.5px;
      line-height: 1.5;
      color: #475569;
    }
    .meta-line__label { font-weight: 700; color: #334155; }
    .meta-line__sep { margin: 0 8px; color: #cbd5e1; }
    .kpi-row {
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 5px;
      margin-bottom: 6px;
    }
    .kpi-card {
      position: relative;
      border-radius: 8px;
      padding: 6px 7px 5px;
      border: 1px solid transparent;
      overflow: hidden;
      min-height: ${kpiMinH};
    }
    .kpi-card__accent { position: absolute; top: 0; left: 0; right: 0; height: 3px; }
    .kpi-card__label { font-size: 7.5px; font-weight: 700; letter-spacing: 0.02em; }
    .kpi-card__value { margin-top: 3px; font-size: 15px; font-weight: 800; line-height: 1.1; }
    .kpi-card__hint { margin-top: 2px; font-size: 7px; font-weight: 600; }
    .kpi-card--indigo { background: linear-gradient(160deg, #fff 0%, #eef2ff 100%); border-color: rgba(99,102,241,.2); }
    .kpi-card--indigo .kpi-card__accent { background: linear-gradient(90deg, #6366f1, #818cf8); }
    .kpi-card--indigo .kpi-card__label { color: #6366f1; }
    .kpi-card--indigo .kpi-card__value { color: #4338ca; }
    .kpi-card--indigo .kpi-card__hint { color: #818cf8; }
    .kpi-card--sky { background: linear-gradient(160deg, #fff 0%, #e0f2fe 100%); border-color: rgba(14,165,233,.22); }
    .kpi-card--sky .kpi-card__accent { background: linear-gradient(90deg, #0ea5e9, #38bdf8); }
    .kpi-card--sky .kpi-card__label { color: #0284c7; }
    .kpi-card--sky .kpi-card__value { color: #0369a1; }
    .kpi-card--sky .kpi-card__hint { color: #38bdf8; }
    .kpi-card--amber { background: linear-gradient(160deg, #fff 0%, #ffedd5 100%); border-color: rgba(249,115,22,.22); }
    .kpi-card--amber .kpi-card__accent { background: linear-gradient(90deg, #f97316, #fb923c); }
    .kpi-card--amber .kpi-card__label { color: #ea580c; }
    .kpi-card--amber .kpi-card__value { color: #c2410c; }
    .kpi-card--amber .kpi-card__hint { color: #fb923c; }
    .kpi-card--emerald { background: linear-gradient(160deg, #fff 0%, #d1fae5 100%); border-color: rgba(16,185,129,.22); }
    .kpi-card--emerald .kpi-card__accent { background: linear-gradient(90deg, #10b981, #34d399); }
    .kpi-card--emerald .kpi-card__label { color: #059669; }
    .kpi-card--emerald .kpi-card__value { color: #047857; font-size: 16px; }
    .kpi-card--emerald .kpi-card__hint { color: #34d399; }
    .kpi-card--violet { background: linear-gradient(160deg, #fff 0%, #ede9fe 100%); border-color: rgba(124,58,237,.22); }
    .kpi-card--violet .kpi-card__accent { background: linear-gradient(90deg, #7c3aed, #a78bfa); }
    .kpi-card--violet .kpi-card__label { color: #7c3aed; }
    .kpi-card--violet .kpi-card__value { color: #6d28d9; }
    .kpi-card--violet .kpi-card__hint { color: #a78bfa; }
    .panel {
      margin-top: 6px;
      padding: 6px 8px 8px;
      border-radius: 8px;
      border: 1px solid #e2e8f0;
      background: #fff;
      break-inside: avoid-page;
      page-break-inside: avoid;
    }
    .panel--break { break-before: page; page-break-before: always; margin-top: 0; }
    .panel--flow {
      break-inside: auto;
      page-break-inside: auto;
      margin-top: 0;
    }
    .panel--flow .chart-wrap { break-inside: avoid; page-break-inside: avoid; }
    .panel--chart { border-color: rgba(226,232,240,.95); }
    .panel--operator { background: linear-gradient(165deg, #fff 0%, #f5f3ff 100%); border-color: rgba(99,102,241,.16); }
    .panel--product { background: linear-gradient(165deg, #fff 0%, #f0f9ff 100%); border-color: rgba(14,165,233,.16); }
    .panel--rank { background: linear-gradient(165deg, #fff 0%, #fffbeb 100%); border-color: rgba(245,158,11,.22); }
    .panel--weld-off { background: linear-gradient(165deg, #fff 0%, #f0fdf4 100%); border-color: rgba(16,185,129,.18); break-inside: auto; page-break-inside: auto; margin-top: 0; padding: 5px 6px 6px; }
    .panel--weld-on { background: linear-gradient(165deg, #fff 0%, #fff7ed 100%); border-color: rgba(249,115,22,.18); break-inside: auto; page-break-inside: auto; margin-top: 0; padding: 5px 6px 6px; }
    .panel__head { display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; margin-bottom: 6px; }
    .panel__title { font-size: 11px; font-weight: 800; color: #1e293b; }
    .panel__title-row { display: flex; align-items: baseline; flex-wrap: wrap; gap: 8px; }
    .panel__title-inline { font-size: 11px; font-weight: 700; color: #4338ca; }
    .panel__subtitle { margin-top: 1px; font-size: 8px; font-weight: 600; color: #64748b; }
    .print-page { break-inside: avoid-page; page-break-inside: avoid; }
    .print-page--break { break-before: page; page-break-before: always; margin-top: 0; }
    .print-page .hd { margin-bottom: 8px; }
    .print-page .panel { margin-top: 0; }
    .panel__badges { display: flex; flex-wrap: wrap; gap: 4px; justify-content: flex-end; }
    .panel-badge { display: inline-block; padding: 2px 7px; border-radius: 999px; font-size: 7.5px; font-weight: 700; white-space: nowrap; }
    .panel-badge--soft { color: #64748b; background: rgba(148,163,184,.14); }
    .panel-badge--chart { color: #6366f1; background: rgba(99,102,241,.1); }
    .panel-badge--operator { color: #4338ca; background: rgba(99,102,241,.12); border: 1px solid rgba(99,102,241,.18); }
    .panel-badge--product { color: #0369a1; background: rgba(14,165,233,.12); border: 1px solid rgba(14,165,233,.2); }
    .panel-badge--rank { color: #b45309; background: rgba(251,191,36,.18); border: 1px solid rgba(245,158,11,.28); }
    .panel-badge--weld-off { color: #047857; background: rgba(16,185,129,.12); border: 1px solid rgba(16,185,129,.2); }
    .panel-badge--weld-on { color: #c2410c; background: rgba(249,115,22,.12); border: 1px solid rgba(249,115,22,.22); }
    .chart-wrap { margin-bottom: 6px; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; background: linear-gradient(180deg, #fafbfc 0%, #fff 100%); }
    .chart-wrap--tall .chart-img { max-height: ${chartTall}; }
    .chart-img { display: block; width: 100%; height: auto; max-height: ${chartNormal}; object-fit: contain; }
    .chart-empty { margin: 0 0 6px; color: #94a3b8; font-size: 8px; }
    table.data { width: 100%; border-collapse: collapse; table-layout: fixed; margin-top: 4px; }
    table.data th, table.data td { border: 1px solid #cbd5e1; padding: 3px 4px; vertical-align: middle; word-break: break-word; }
    table.data th { font-size: 7.5px; font-weight: 700; }
    table.data td { font-size: 8px; }
    table.data--operator th { background: linear-gradient(180deg, #ede9fe, #e0e7ff); color: #4338ca; }
    table.data--product th { background: linear-gradient(180deg, #e0f2fe, #bae6fd); color: #0369a1; }
    table.data--rank th, table.data--rank-overview th { background: linear-gradient(180deg, #fef3c7, #fde68a); color: #92400e; }
    table.data--weld-off th { background: linear-gradient(180deg, #d1fae5, #a7f3d0); color: #047857; }
    table.data--weld-on th { background: linear-gradient(180deg, #ffedd5, #fed7aa); color: #c2410c; }
    table.data tbody tr:nth-child(even) { background: rgba(248,250,252,.85); }
    .data--compact th, .data--compact td { font-size: 6.5px; padding: 2px 3px; }
    .data--metrics-time th, .data--metrics-time td { padding: 1.8px 2.7px; line-height: 1.26; }
    .num { text-align: right; font-variant-numeric: tabular-nums; }
    .center { text-align: center; }
    .warn { color: #c2410c; font-weight: 700; }
    .product-cd { font-family: ui-monospace, monospace; font-size: 7.5px; font-weight: 700; color: #0369a1; }
    .product-cd--rank { color: #b45309; }
    .pill { display: inline-block; padding: 1px 5px; border-radius: 5px; font-size: 7.5px; font-weight: 700; }
    .pill--operator { color: #4338ca; background: rgba(99,102,241,.1); border: 1px solid rgba(99,102,241,.15); }
    .pill--product { color: #047857; background: rgba(16,185,129,.1); border: 1px solid rgba(16,185,129,.15); }
    .pill--rank { color: #b45309; background: rgba(251,191,36,.15); border: 1px solid rgba(245,158,11,.28); }
    .pill--weld-off { color: #047857; background: rgba(16,185,129,.12); border: 1px solid rgba(16,185,129,.2); }
    .pill--weld-on { color: #c2410c; background: rgba(249,115,22,.12); border: 1px solid rgba(249,115,22,.22); }
    .row-rank, .rank-badge { display: inline-flex; align-items: center; justify-content: center; min-width: 16px; height: 16px; padding: 0 3px; border-radius: 5px; font-size: 7.5px; font-weight: 700; color: #64748b; background: rgba(148,163,184,.15); }
    .row-rank--gold, .rank-badge--gold { color: #92400e; background: linear-gradient(135deg, #fde68a, #fcd34d); }
    .row-rank--silver, .rank-badge--silver { color: #475569; background: linear-gradient(135deg, #e2e8f0, #cbd5e1); }
    .row-rank--bronze, .rank-badge--bronze { color: #9a3412; background: linear-gradient(135deg, #fed7aa, #fdba74); }
    .weld-split { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-top: 6px; }
    .weld-split--section { grid-template-columns: 1fr; gap: 8px; }
    .table-more { margin: 2px 0 0; font-size: 6.5px; color: #94a3b8; text-align: right; }
    .rank-hero { display: flex; flex-wrap: wrap; gap: 8px; padding: 8px 10px; margin-bottom: 6px; border-radius: 8px; background: linear-gradient(135deg, #fffbeb, #fff); border: 1px solid rgba(251,191,36,.35); }
    .rank-hero__cd { display: inline-block; font-family: ui-monospace, monospace; font-size: 9px; font-weight: 800; color: #b45309; padding: 2px 8px; border-radius: 6px; background: #fff; border: 1px solid rgba(245,158,11,.25); }
    .rank-hero__name { margin-top: 4px; font-size: 12px; font-weight: 800; color: #1e293b; }
    .rank-hero__stats { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 6px; flex: 1; min-width: 240px; }
    .rank-hero__stat { padding: 5px 6px; border-radius: 6px; background: rgba(255,255,255,.8); border: 1px solid #e2e8f0; }
    .rank-hero__stat--accent { background: linear-gradient(135deg, #fef3c7, #fde68a); border-color: rgba(245,158,11,.35); }
    .rank-hero__stat-label { display: block; font-size: 7px; font-weight: 700; color: #94a3b8; }
    .rank-hero__stat-val { display: block; margin-top: 1px; font-size: 11px; font-weight: 800; color: #0f172a; }
    .rank-hero__stat-val small { font-size: 7px; font-weight: 600; color: #64748b; margin-left: 2px; }
    .sub-panel__title { margin: 8px 0 4px; font-size: 9px; font-weight: 700; color: #78350f; }
    .empty { margin: 0; color: #94a3b8; font-size: 8px; }
    table.data--metrics th { font-size: 7px; }
    table.data--metrics td { font-size: 7.5px; }
    table.data--metrics td.name { font-weight: 700; color: #334155; }
    table.data--metrics tr.row-total td {
      font-weight: 800;
      border-top: 2px dashed rgba(99, 102, 241, 0.45);
      background: rgba(238, 242, 255, 0.55) !important;
    }
    table.data--metrics tr.row-support td { background: #fff !important; }
    .pill--metric-eff { color: #4338ca; background: rgba(99,102,241,.1); border: 1px solid rgba(99,102,241,.15); }
    .num--good { color: #047857; font-weight: 700; }
    .ft { margin-top: 10px; padding-top: 6px; border-top: 1px solid #e2e8f0; font-size: 7.5px; color: #94a3b8; text-align: right; }
    @media print {
      body { margin: 0; }
      .panel { box-shadow: none; }
      table.data thead { display: table-header-group; }
      table.data tr { break-inside: avoid; page-break-inside: avoid; }
    }
  `
}

function buildPrintDocumentShell(
  filters: WeldingProductivityReportFilters,
  options: {
    sectionTitle?: string
    sectionMetaInline?: boolean
    mode?: 'full' | 'section'
    orientation?: PrintOrientation
    body: string
    includeKpi?: boolean
    kpiCards?: WeldingProductivityKpiCardPrint[]
  },
): string {
  const printedAt = printedAtJa()
  const mode = options.mode ?? 'section'
  const orientation = options.orientation ?? 'portrait'
  const kpiHtml =
    options.includeKpi && options.kpiCards?.length
      ? `<div class="kpi-row">${options.kpiCards.map(kpiCardHtml).join('')}</div>`
      : ''
  const metaHtml = buildMetaLineHtml(filters, printedAt)
  const sectionHtml = options.sectionTitle
    ? options.sectionMetaInline
      ? `<div class="hd__section-row">
    <div class="hd__section">${escHtml(options.sectionTitle)}</div>
    ${metaHtml}
  </div>`
      : `<div class="hd__section">${escHtml(options.sectionTitle)}</div>`
    : ''

  return `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <title>溶接工程 — 生産性分析${options.sectionTitle ? ` — ${options.sectionTitle}` : ''}</title>
  <style>${getPrintStyles(mode, orientation)}</style>
</head>
<body>
  <header class="hd">
    <div class="hd__title">溶接工程 — 生産性分析</div>
    ${sectionHtml}
    ${options.sectionMetaInline ? '' : metaHtml}
  </header>
  ${kpiHtml}
  ${options.body}
  <footer class="ft">Smart-EMAPs · 溶接生産性分析 · ${escHtml(printedAt)}</footer>
</body>
</html>`
}

function buildFullPrintBody(ctx: WeldingProductivityReportContext): string {
  const {
    charts,
    operatorRows,
    productRows,
    operatorSectionAvgEfficiency,
    productSectionTotalQty,
  } = ctx

  const operatorBadges = [
    panelBadge(`${operatorRows.length} 名`, 'soft'),
    operatorSectionAvgEfficiency != null
      ? panelBadge(`平均能率 ${fmtEfficiency(operatorSectionAvgEfficiency)} 個/時`, 'inspector')
      : '',
  ].join('')

  const productBadges = [
    panelBadge(`${productRows.length} 品目`, 'soft'),
    productSectionTotalQty > 0 ? panelBadge(`生産合計 ${fmtInt(productSectionTotalQty)}`, 'product') : '',
  ].join('')

  return `
  ${panelSection('日別推移', { theme: 'chart', badges: panelBadge('生産数 · 能率', 'chart'), chartSrc: charts.daily, chartAlt: '日別推移', chartTall: true, tableHtml: '' })}
  ${panelSection('溶接作業者別', { theme: 'operator', badges: operatorBadges, chartSrc: charts.operator, chartAlt: '溶接作業者別', tableHtml: buildOperatorPrintTable(operatorRows, PRINT_OPERATOR_TABLE_MAX) })}
  ${panelSection('製品別', { theme: 'product', badges: productBadges, chartSrc: charts.product, chartAlt: '製品別', tableHtml: buildProductPrintTable(productRows), pageBreak: true })}
  `
}

export function buildWeldingProductivityPrintHtml(ctx: WeldingProductivityReportContext): string {
  return buildPrintDocumentShell(ctx.filters, {
    mode: 'full',
    includeKpi: true,
    kpiCards: ctx.kpiCards,
    body: buildFullPrintBody(ctx),
  })
}

export function buildWeldingProductivitySectionPrintHtml(
  section: WeldingProductivityPrintSection,
  ctx: WeldingProductivityReportContext,
): string {
  const {
    charts,
    operatorRows,
    productRows,
    operatorSectionAvgEfficiency,
    productSectionTotalQty,
    productRank,
  } = ctx

  if (section === 'full') {
    return buildWeldingProductivityPrintHtml(ctx)
  }

  if (section === 'daily') {
    return buildPrintDocumentShell(ctx.filters, {
      sectionTitle: '日別推移',
      mode: 'section',
      orientation: 'landscape',
      body: panelSection('日別推移', {
        theme: 'chart',
        badges: panelBadge('生産数 · 能率', 'chart'),
        chartSrc: charts.daily,
        chartAlt: '日別推移',
        chartTall: true,
        tableHtml: '',
      }),
    })
  }

  if (section === 'operator') {
    const badges = [
      panelBadge(`${operatorRows.length} 名`, 'soft'),
      operatorSectionAvgEfficiency != null
        ? panelBadge(`平均能率 ${fmtEfficiency(operatorSectionAvgEfficiency)} 個/時`, 'inspector')
        : '',
    ].join('')
    return buildPrintDocumentShell(ctx.filters, {
      sectionTitle: '溶接作業者別',
      mode: 'section',
      body: panelSection('溶接作業者別', {
        theme: 'operator',
        badges,
        chartSrc: charts.operator,
        chartAlt: '溶接作業者別',
        tableHtml: buildOperatorPrintTable(operatorRows),
      }),
    })
  }

  if (section === 'product') {
    const badges = [
      panelBadge(`${productRows.length} 品目`, 'soft'),
      productSectionTotalQty > 0 ? panelBadge(`生産合計 ${fmtInt(productSectionTotalQty)}`, 'product') : '',
    ].join('')
    return buildPrintDocumentShell(ctx.filters, {
      sectionTitle: '製品別',
      mode: 'section',
      body: panelSection('製品別', {
        theme: 'product',
        badges,
        chartSrc: charts.product,
        chartAlt: '製品別',
        tableHtml: buildProductPrintTable(productRows),
        flowBreak: true,
      }),
    })
  }

  if (section === 'product-rank') {
    const selected = productRank.selected
    const selectedBody = selected
      ? `${buildProductRankHeroHtml(selected, productRank.stats)}
        ${panelSection('溶接作業者別能率', { theme: 'rank', badges: panelBadge(`${selected.operators.length} 名`, 'rank'), chartSrc: charts.productRank ?? null, chartAlt: '溶接作業者別能率', tableHtml: buildProductRankOperatorTable(selected.operators) })}`
      : '<p class="empty">対象製品がありません</p>'

    const overviewBody =
      productRank.topOverview.length > 0
        ? `<div class="sub-panel__title">全製品 · 能率 TOP1 一覧</div>${buildProductRankOverviewTable(productRank.topOverview)}`
        : ''

    return buildPrintDocumentShell(ctx.filters, {
      sectionTitle: '製品別 · 溶接作業者能率ランキング',
      mode: 'section',
      body: `${selectedBody}${overviewBody}`,
    })
  }

  return buildWeldingProductivityPrintHtml(ctx)
}

export interface WeldingProductivityDailyBatchItem {
  operatorUserId: number
  operatorLabel: string
  chartSrc: string | null
  dayCount: number
  sumActualQty: number
  avgEfficiencyPerHour: number | null
}

function buildDailyBatchPrintPageHeader(
  filters: WeldingProductivityReportFilters,
  printedAt: string,
): string {
  return `<header class="hd">
    <div class="hd__title">溶接工程 — 生産性分析</div>
    <div class="hd__section">日別推移（溶接作業者別）</div>
    ${buildMetaLineHtml(filters, printedAt, { compact: true })}
  </header>`
}

export function buildWeldingProductivityDailyBatchPrintHtml(
  filters: WeldingProductivityReportFilters,
  items: WeldingProductivityDailyBatchItem[],
): string {
  const printedAt = printedAtJa()
  const body = items
    .map((item, idx) => {
      const badges = [
        panelBadge(`${item.dayCount} 日`, 'soft'),
        item.sumActualQty > 0 ? panelBadge(`生産合計 ${fmtInt(item.sumActualQty)}`, 'product') : '',
        item.avgEfficiencyPerHour != null
          ? panelBadge(`平均能率 ${fmtEfficiency(item.avgEfficiencyPerHour)} 個/時`, 'inspector')
          : '',
      ].join('')
      const panel = panelSection('日別推移', {
        titleInline: item.operatorLabel,
        theme: 'chart',
        badges,
        chartSrc: item.chartSrc,
        chartAlt: `日別推移 — ${item.operatorLabel}`,
        chartTall: true,
        tableHtml: '',
        flowBreak: true,
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
  <title>溶接工程 — 生産性分析 — 日別推移（溶接作業者別）</title>
  <style>${getPrintStyles('section', 'landscape')}</style>
</head>
<body>
  ${body}
  <footer class="ft">Smart-EMAPs · 溶接生産性分析 · ${escHtml(printedAt)}</footer>
</body>
</html>`
}

export function printWeldingProductivityDailyBatch(
  filters: WeldingProductivityReportFilters,
  items: WeldingProductivityDailyBatchItem[],
) {
  openPrintDocument(buildWeldingProductivityDailyBatchPrintHtml(filters, items))
}

export interface WeldingProductivityOperatorProductBatchItem {
  operatorLabel: string
  productCount: number
  sessionCount: number
  sumActualQty: number
  avgEfficiencyPerHour: number | null
  productRows: Array<WeldingProductivityProductRow & { avg_efficiency_per_hour?: number | null }>
}

function buildOperatorProductBatchPageHeader(
  filters: WeldingProductivityReportFilters,
  printedAt: string,
): string {
  return `<header class="hd">
    <div class="hd__title">溶接工程 — 生産性分析</div>
    <div class="hd__section">溶接作業者別製品別</div>
    ${buildMetaLineHtml(filters, printedAt, { compact: true })}
  </header>`
}

export function buildWeldingProductivityOperatorProductBatchPrintHtml(
  filters: WeldingProductivityReportFilters,
  items: WeldingProductivityOperatorProductBatchItem[],
): string {
  const printedAt = printedAtJa()
  const body = items
    .map((item, idx) => {
      const badges = [
        panelBadge(`${item.productCount} 品目`, 'product'),
        panelBadge(`セッション ${fmtInt(item.sessionCount)}`, 'soft'),
        item.sumActualQty > 0 ? panelBadge(`生産合計 ${fmtInt(item.sumActualQty)}`, 'product') : '',
        item.avgEfficiencyPerHour != null
          ? panelBadge(`平均能率 ${fmtEfficiency(item.avgEfficiencyPerHour)} 個/時`, 'inspector')
          : '',
      ].join('')
      const panel = panelSection('生産製品一覧', {
        titleInline: item.operatorLabel,
        theme: 'operator',
        badges,
        hideChart: true,
        tableHtml: buildProductPrintTable(item.productRows),
        flowBreak: true,
      })
      return `<div class="print-page${idx > 0 ? ' print-page--break' : ''}">
        ${buildOperatorProductBatchPageHeader(filters, printedAt)}
        ${panel}
      </div>`
    })
    .join('')

  return `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <title>溶接工程 — 生産性分析 — 溶接作業者別製品別</title>
  <style>${getPrintStyles('section', 'portrait')}</style>
</head>
<body>
  ${body}
  <footer class="ft">Smart-EMAPs · 溶接生産性分析 · ${escHtml(printedAt)}</footer>
</body>
</html>`
}

export function printWeldingProductivityOperatorProductBatch(
  filters: WeldingProductivityReportFilters,
  items: WeldingProductivityOperatorProductBatchItem[],
) {
  openPrintDocument(buildWeldingProductivityOperatorProductBatchPrintHtml(filters, items))
}

export function printWeldingProductivityReport(payload: WeldingProductivityPrintPayload) {
  openPrintDocument(buildWeldingProductivityPrintHtml(payload))
}

export function printWeldingProductivitySection(
  section: WeldingProductivityPrintSection,
  ctx: WeldingProductivityReportContext,
) {
  openPrintDocument(buildWeldingProductivitySectionPrintHtml(section, ctx))
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

export function exportWeldingSessionsCsv(
  data: WeldingProductivityAnalysisData,
  filters: WeldingProductivityReportFilters,
) {
  const content = buildSessionsCsv(data, filters)
  downloadCsvFile(`${reportFileBase(filters)}_セッション.csv`, content)
}

export function exportWeldingSummaryCsv(
  data: WeldingProductivityAnalysisData,
  filters: WeldingProductivityReportFilters,
  extras: Parameters<typeof buildSummaryCsv>[2],
) {
  const content = buildSummaryCsv(data, filters, extras)
  downloadCsvFile(`${reportFileBase(filters)}_集計.csv`, content)
}