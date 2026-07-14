import { buildPrintHtmlDocument, escapeHtml } from '@/utils/printWindow'
import type {
  DefectScrapComparisonKpi,
  DefectScrapComparisonMonthlyRow,
  DefectScrapComparisonSummaryRow,
} from '@/api/erp/defectScrapComparison'

function fmtNum(v: number | null | undefined): string {
  if (v == null) return '0'
  return Number(v).toLocaleString()
}

function fmtSigned(v: number | null | undefined): string {
  const n = Number(v ?? 0)
  if (n > 0) return `+${n.toLocaleString()}`
  return n.toLocaleString()
}

function fmtPct(v: number | null | undefined): string {
  if (v == null) return '-'
  return `${Number(v).toFixed(1)}%`
}

export interface DefectScrapPrintMeta {
  printedAt: string
  targetMonth: string
  dateRangeLabel: string
  processLabel: string
  productLabel: string
  onlyDiff: boolean
  chartRangeLabel: string
}

export interface DefectScrapPrintInput extends DefectScrapPrintMeta {
  kpi: DefectScrapComparisonKpi
  summaryRows: DefectScrapComparisonSummaryRow[]
  monthlyRows: DefectScrapComparisonMonthlyRow[]
}

const PRINT_STYLES = `
  @page { size: A4 landscape; margin: 10mm; }
  body {
    font-family: "Segoe UI", "Hiragino Sans", "Meiryo", sans-serif;
    font-size: 10px;
    color: #1e293b;
    margin: 0;
    padding: 12px;
  }
  h1 { font-size: 17px; margin: 0 0 4px; letter-spacing: -0.02em; }
  .subtitle { color: #64748b; font-size: 10px; margin: 0 0 10px; }
  .meta { color: #64748b; margin-bottom: 12px; font-size: 9px; line-height: 1.6; }
  .kpi-row { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; }
  .kpi {
    flex: 1;
    min-width: 120px;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 9px 10px;
    background: #f8fafc;
  }
  .kpi-summary { border-color: #bfdbfe; background: #eff6ff; }
  .kpi-source { border-color: #fed7aa; background: #fff7ed; }
  .kpi-diff { border-color: #fecaca; background: #fef2f2; }
  .kpi-match { border-color: #a7f3d0; background: #ecfdf5; }
  .kpi-label { font-size: 8px; color: #64748b; font-weight: 700; }
  .kpi-value { font-size: 15px; font-weight: 800; margin-top: 3px; font-variant-numeric: tabular-nums; }
  .kpi-summary .kpi-value { color: #1d4ed8; }
  .kpi-source .kpi-value { color: #c2410c; }
  .kpi-diff .kpi-value { color: #b91c1c; }
  .kpi-match .kpi-value { color: #047857; }
  .kpi-note { font-size: 8px; color: #94a3b8; margin-top: 3px; }
  h2 {
    font-size: 12px;
    margin: 14px 0 6px;
    border-bottom: 1px solid #cbd5e1;
    padding-bottom: 4px;
  }
  table { width: 100%; border-collapse: collapse; margin-bottom: 10px; }
  th, td { border: 1px solid #cbd5e1; padding: 5px 6px; text-align: right; }
  th { background: #f1f5f9; font-weight: 700; font-size: 9px; }
  th.left, td.left { text-align: left; }
  th.col-s, td.col-s { background: #eff6ff; color: #1d4ed8; }
  th.col-m, td.col-m { background: #fff7ed; color: #c2410c; }
  tr.neg td.diff { color: #b91c1c; font-weight: 700; }
  tr.pos td.diff { color: #1d4ed8; font-weight: 700; }
  .footer { margin-top: 12px; font-size: 8px; color: #94a3b8; line-height: 1.5; }
  .empty { color: #94a3b8; font-style: italic; padding: 8px 0; }
`

export function buildDefectScrapComparisonPrintHtml(input: DefectScrapPrintInput): string {
  const { kpi } = input
  const kpiHtml = `
    <div class="kpi-row">
      <div class="kpi kpi-summary">
        <div class="kpi-label">生産管理（不良+廃棄）</div>
        <div class="kpi-value">${fmtNum(kpi.summary_total)}</div>
      </div>
      <div class="kpi kpi-source">
        <div class="kpi-label">製造（不良+廃棄）</div>
        <div class="kpi-value">${fmtNum(kpi.source_total)}</div>
      </div>
      <div class="kpi kpi-diff">
        <div class="kpi-label">差異（製造 − 生産管理）</div>
        <div class="kpi-value">${fmtSigned(kpi.total_diff)}</div>
      </div>
      <div class="kpi kpi-match">
        <div class="kpi-label">一致率（数量ベース）</div>
        <div class="kpi-value">${fmtPct(kpi.match_rate)}</div>
        <div class="kpi-note">1 − |差異| / max(生産管理, 製造)</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">不一致件数</div>
        <div class="kpi-value">${fmtNum(kpi.mismatch_count)}</div>
      </div>
    </div>
  `

  const summaryRows = input.summaryRows
    .map((r) => {
      const diff = Number(r.total_diff || 0)
      const cls = diff > 0 ? 'pos' : diff < 0 ? 'neg' : ''
      return `
        <tr class="${cls}">
          <td class="left">${escapeHtml(r.process_name || r.process_cd)}</td>
          <td class="col-s">${fmtNum(r.summary_total)}</td>
          <td class="col-m">${fmtNum(r.source_total)}</td>
          <td class="diff">${fmtSigned(r.total_diff)}</td>
          <td>${fmtPct(r.match_rate)}</td>
          <td>${fmtNum(r.mismatch_count)}</td>
          <td class="left">${escapeHtml(r.source_note || '')}</td>
        </tr>
      `
    })
    .join('')

  const summaryTable = summaryRows
    ? `
    <h2>工程別サマリ</h2>
    <table>
      <thead>
        <tr>
          <th class="left">工程</th>
          <th class="col-s">生産管理</th>
          <th class="col-m">製造</th>
          <th>差異</th>
          <th>一致率</th>
          <th>不一致</th>
          <th class="left">備考</th>
        </tr>
      </thead>
      <tbody>${summaryRows}</tbody>
    </table>
  `
    : `<h2>工程別サマリ</h2><p class="empty">データなし</p>`

  const monthlyRows = input.monthlyRows
    .map((r) => {
      const diff = Number(r.total_diff || 0)
      const cls = diff > 0 ? 'pos' : diff < 0 ? 'neg' : ''
      return `
        <tr class="${cls}">
          <td class="left">${escapeHtml(r.year_month)}</td>
          <td class="col-s">${fmtNum(r.summary_total)}</td>
          <td class="col-m">${fmtNum(r.source_total)}</td>
          <td class="diff">${fmtSigned(r.total_diff)}</td>
          <td>${fmtPct(r.match_rate)}</td>
        </tr>
      `
    })
    .join('')

  const monthlyTable = monthlyRows
    ? `
    <h2>月次トレンド（${escapeHtml(input.chartRangeLabel || '-')}）</h2>
    <table>
      <thead>
        <tr>
          <th class="left">年月</th>
          <th class="col-s">生産管理</th>
          <th class="col-m">製造</th>
          <th>差異</th>
          <th>一致率</th>
        </tr>
      </thead>
      <tbody>${monthlyRows}</tbody>
    </table>
  `
    : ''

  const body = `
    <h1>不良・廃棄データ突合レポート</h1>
    <p class="subtitle">生産管理 × 製造 · 不良+廃棄合算</p>
    <p class="meta">
      対象月: ${escapeHtml(input.targetMonth)}（${escapeHtml(input.dateRangeLabel)}）
      · 工程: ${escapeHtml(input.processLabel)}
      · 製品: ${escapeHtml(input.productLabel || '全製品')}
      · 差異のみ: ${input.onlyDiff ? 'はい' : 'いいえ'}
      · 印刷日時: ${escapeHtml(input.printedAt)}
    </p>
    ${kpiHtml}
    ${summaryTable}
    ${monthlyTable}
    <p class="footer">
      一致率は数量ベース（1 − |製造−生産管理| / max(生産管理, 製造)）。
      メッキは日次合計。製造側データがない工程は製造=0。
    </p>
  `

  return buildPrintHtmlDocument('不良・廃棄データ突合レポート', PRINT_STYLES, body)
}
