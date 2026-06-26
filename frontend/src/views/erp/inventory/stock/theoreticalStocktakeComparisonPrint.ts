import { buildPrintHtmlDocument, escapeHtml } from '@/utils/printWindow'
import type {
  ComparisonDetailRow,
  ComparisonKpi,
  ComparisonSummaryRow,
} from '@/api/inventoryComparison'

const STATUS_LABEL: Record<string, string> = {
  match: '一致',
  only_theoretical: '理論のみ',
  only_stocktake: '棚卸のみ',
  mismatch: '不一致',
}

function fmtNum(v: number | null | undefined): string {
  if (v == null) return '0'
  return Number(v).toLocaleString()
}

function fmtPct(v: number | null | undefined): string {
  if (v == null) return '-'
  return `${Number(v).toFixed(1)}%`
}

export interface TheoreticalStocktakePrintMeta {
  printedAt: string
  asOf: string
  processLabel: string
  productLabel: string
  onlyDiff: boolean
}

export interface TheoreticalStocktakeSummaryPrintInput extends TheoreticalStocktakePrintMeta {
  kpi: ComparisonKpi
  summaryRows: ComparisonSummaryRow[]
}

export interface TheoreticalStocktakeDetailPrintInput extends TheoreticalStocktakePrintMeta {
  detailRows: ComparisonDetailRow[]
  totalCount: number
}

const SUMMARY_STYLES = `
  @page { size: A4 landscape; margin: 10mm; }
  body { font-family: "Segoe UI", "Hiragino Sans", "Meiryo", sans-serif; font-size: 10px; color: #1e293b; margin: 0; padding: 12px; }
  h1 { font-size: 16px; margin: 0 0 4px; }
  .meta { color: #64748b; margin-bottom: 12px; font-size: 9px; line-height: 1.5; }
  .kpi-row { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; }
  .kpi { flex: 1; min-width: 120px; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px; background: #f8fafc; }
  .kpi-label { font-size: 8px; color: #64748b; }
  .kpi-value { font-size: 14px; font-weight: 700; margin-top: 2px; }
  h2 { font-size: 12px; margin: 14px 0 6px; border-bottom: 1px solid #cbd5e1; padding-bottom: 4px; }
  table { width: 100%; border-collapse: collapse; margin-bottom: 12px; }
  th, td { border: 1px solid #cbd5e1; padding: 4px 6px; text-align: right; }
  th { background: #f1f5f9; font-weight: 700; }
  th.left, td.left { text-align: left; }
  tr.neg td.diff { color: #b91c1c; }
  tr.pos td.diff { color: #15803d; }
  .footer { margin-top: 10px; font-size: 8px; color: #94a3b8; }
`

const DETAIL_STYLES = `
  @page { size: A4 landscape; margin: 8mm; }
  body { font-family: "Segoe UI", "Hiragino Sans", "Meiryo", sans-serif; font-size: 9px; color: #1e293b; margin: 0; padding: 10px; }
  h1 { font-size: 15px; margin: 0 0 4px; }
  .meta { color: #64748b; margin-bottom: 10px; font-size: 8px; line-height: 1.5; }
  .count-badge { display: inline-block; margin-left: 8px; font-size: 9px; font-weight: 700; color: #475569; }
  table { width: 100%; border-collapse: collapse; }
  thead { display: table-header-group; }
  th, td { border: 1px solid #cbd5e1; padding: 3px 5px; text-align: right; }
  th { background: #f1f5f9; font-weight: 700; font-size: 8px; }
  th.left, td.left { text-align: left; }
  tr { page-break-inside: avoid; }
  tr.neg td.diff { color: #b91c1c; }
  tr.pos td.diff { color: #15803d; }
  .status-match { color: #047857; }
  .status-mismatch { color: #b91c1c; font-weight: 700; }
  .status-partial { color: #b45309; }
  .footer { margin-top: 10px; font-size: 8px; color: #94a3b8; }
`

function buildMetaBlock(meta: TheoreticalStocktakePrintMeta): string {
  return `
    <p class="meta">
      対象日: ${escapeHtml(meta.asOf)}
      · 工程: ${escapeHtml(meta.processLabel)}
      · 製品: ${escapeHtml(meta.productLabel || '全製品')}
      · 差異のみ: ${meta.onlyDiff ? 'はい' : 'いいえ'}
      · 印刷日時: ${escapeHtml(meta.printedAt)}
    </p>
  `
}

/** サマリ報告書（工程別のみ） */
export function buildTheoreticalStocktakeComparisonPrintHtml(
  input: TheoreticalStocktakeSummaryPrintInput,
): string {
  const kpiHtml = `
    <div class="kpi-row">
      <div class="kpi"><div class="kpi-label">理論在庫合計</div><div class="kpi-value">${fmtNum(input.kpi.theoretical_qty_total)}</div></div>
      <div class="kpi"><div class="kpi-label">棚卸在庫合計</div><div class="kpi-value">${fmtNum(input.kpi.stocktake_qty_total)}</div></div>
      <div class="kpi"><div class="kpi-label">差異合計</div><div class="kpi-value">${fmtNum(input.kpi.diff_qty_total)}</div></div>
      <div class="kpi"><div class="kpi-label">一致率</div><div class="kpi-value">${fmtPct(input.kpi.match_rate)}</div></div>
      <div class="kpi"><div class="kpi-label">不一致件数</div><div class="kpi-value">${fmtNum(input.kpi.mismatch_count)}</div></div>
    </div>
  `

  const summaryHead = `
    <tr>
      <th class="left">工程</th>
      <th>理論</th>
      <th>棚卸</th>
      <th>差異</th>
      <th>差異率</th>
      <th>品目数</th>
      <th>一致</th>
      <th>不一致</th>
      <th>一致率</th>
    </tr>
  `
  const summaryBody = input.summaryRows
    .map((r) => {
      const cls = r.diff_qty > 0 ? 'pos' : r.diff_qty < 0 ? 'neg' : ''
      return `<tr class="${cls}">
        <td class="left">${escapeHtml(r.process_name)}</td>
        <td>${fmtNum(r.theoretical_qty)}</td>
        <td>${fmtNum(r.stocktake_qty)}</td>
        <td class="diff">${fmtNum(r.diff_qty)}</td>
        <td>${r.diff_rate != null ? `${r.diff_rate.toFixed(1)}%` : '-'}</td>
        <td>${fmtNum(r.item_count)}</td>
        <td>${fmtNum(r.matched_count)}</td>
        <td>${fmtNum(r.mismatch_count)}</td>
        <td>${fmtPct(r.match_rate)}</td>
      </tr>`
    })
    .join('')

  const body = `
    <h1>理論在庫 vs 棚卸在庫 比較（製品・全工程）</h1>
    ${buildMetaBlock(input)}
    ${kpiHtml}
    <h2>工程別サマリ</h2>
    <table><thead>${summaryHead}</thead><tbody>${summaryBody || '<tr><td colspan="9" class="left">データなし</td></tr>'}</tbody></table>
    <div class="footer">Smart-EMAPs · 理論在庫 vs 棚卸在庫比較（サマリ）</div>
  `

  return buildPrintHtmlDocument('理論在庫 vs 棚卸在庫比較', SUMMARY_STYLES, body)
}

/** 品目×工程明細（別印刷） */
export function buildTheoreticalStocktakeComparisonDetailPrintHtml(
  input: TheoreticalStocktakeDetailPrintInput,
): string {
  const detailHead = `
    <tr>
      <th class="left">製品CD</th>
      <th class="left">製品名</th>
      <th class="left">工程</th>
      <th>理論</th>
      <th>棚卸</th>
      <th>差異</th>
      <th class="left">状態</th>
    </tr>
  `
  const statusClass = (s: string) => {
    if (s === 'match') return 'status-match'
    if (s === 'mismatch') return 'status-mismatch'
    return 'status-partial'
  }
  const detailBody = input.detailRows
    .map((r) => {
      const cls = r.diff_qty > 0 ? 'pos' : r.diff_qty < 0 ? 'neg' : ''
      return `<tr class="${cls}">
        <td class="left">${escapeHtml(r.product_cd)}</td>
        <td class="left">${escapeHtml(r.product_name)}</td>
        <td class="left">${escapeHtml(r.process_name)}</td>
        <td>${fmtNum(r.theoretical_qty)}</td>
        <td>${fmtNum(r.stocktake_qty)}</td>
        <td class="diff">${fmtNum(r.diff_qty)}</td>
        <td class="left ${statusClass(r.status)}">${escapeHtml(STATUS_LABEL[r.status] ?? r.status)}</td>
      </tr>`
    })
    .join('')

  const body = `
    <h1>理論在庫 vs 棚卸在庫 比較 — 品目×工程明細</h1>
    ${buildMetaBlock(input)}
    <p class="count-badge">全 ${fmtNum(input.totalCount)} 件（本ページ ${fmtNum(input.detailRows.length)} 件）</p>
    <table>
      <thead>${detailHead}</thead>
      <tbody>${detailBody || '<tr><td colspan="7" class="left">データなし</td></tr>'}</tbody>
    </table>
    <div class="footer">Smart-EMAPs · 理論在庫 vs 棚卸在庫比較（品目×工程明細）</div>
  `

  return buildPrintHtmlDocument('品目×工程明細', DETAIL_STYLES, body)
}
