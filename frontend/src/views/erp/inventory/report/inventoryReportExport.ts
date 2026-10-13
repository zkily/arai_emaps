/**
 * 在庫報告：印刷 / Excel / PDF
 * 出力内容は画面表示（KPIカード・差異表・大量廃棄明細）と同一構成。
 */
import html2canvas from 'html2canvas'
import { jsPDF } from 'jspdf'
import { downloadExcelMultiSheet, type ExcelSheetAoa } from '@/utils/excelExport'
import { escapeHtml } from '@/utils/printWindow'
import type { MonthlyReportKpi, QuarterlyReportPayload } from '@/api/inventoryReport'
import {
  RPT_TARGET_CLOSING_PRODUCT_SEN,
  RPT_TARGET_SCRAP_RATE_PERCENT,
} from './inventoryReportTargets'

const PDF_PAGE_WIDTH_PX = 794
const PDF_BLOCK_GAP_MM = 2.5

export interface DiffProcessAvgRow {
  process_cd: string
  process_name: string
  month_count: number
  theoretical_qty: number
  stocktake_qty: number
  diff_qty: number
  diff_rate: number | null
  match_rate: number
}

export interface BulkCategoryRow {
  name: string
  count: number
  quantity: number
}

/** 画面上の各チャート（getDataURL） */
export interface InventoryReportChartImages {
  inventory?: string
  wip?: string
  product?: string
  scrapRate?: string
  scrapQty?: string
  match?: string
  bulkDetail?: string
  diff?: string
}

export interface InventoryReportExportInput {
  payload: QuarterlyReportPayload
  monthlyKpis: MonthlyReportKpi[]
  diffByProcessAvg: DiffProcessAvgRow[]
  bulkCategories: BulkCategoryRow[]
  chartImages?: InventoryReportChartImages
}

function toSen(v: number | null | undefined): number {
  if (v == null || Number.isNaN(Number(v))) return 0
  return Math.round((Number(v) / 1000) * 10) / 10
}

function fmtInt(v: number | null | undefined): string {
  if (v == null || Number.isNaN(Number(v))) return '0'
  return Number(v).toLocaleString('ja-JP')
}

function fmtSen(v: number | null | undefined): string {
  return toSen(v).toLocaleString('ja-JP', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 1,
  })
}

function fmtSignedSen(v: number | null | undefined): string {
  const n = toSen(v)
  const s = Math.abs(n).toLocaleString('ja-JP', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 1,
  })
  if (n > 0) return `+${s}`
  if (n < 0) return `-${s}`
  return s
}

function fmtPct(v: number | null | undefined): string {
  if (v == null || Number.isNaN(Number(v))) return '—'
  return `${Number(v).toLocaleString('ja-JP', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}%`
}

function excelNum(v: number | null | undefined): number | string {
  return v == null || Number.isNaN(Number(v)) ? '' : Number(v)
}

function excelSen(v: number | null | undefined): number | string {
  if (v == null || Number.isNaN(Number(v))) return ''
  return toSen(v)
}

function fileStamp(d = new Date()): string {
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}_${p(d.getHours())}${p(d.getMinutes())}`
}

function safeLabel(label: string): string {
  return String(label || '在庫報告').replace(/[\\/:*?"<>|]/g, '_')
}

function localeNow(): string {
  return new Date().toLocaleString('ja-JP')
}

function diffClass(v: number): string {
  if (v > 0) return 'up'
  if (v < 0) return 'down'
  return ''
}

const REPORT_STYLES = `
  @page { size: A4 portrait; margin: 11mm 10mm; }
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 0;
    font-family: "Yu Gothic UI", "Yu Gothic", "Hiragino Sans", "Meiryo", sans-serif;
    font-size: 10.5px; color: #0f172a; background: #fff;
    -webkit-print-color-adjust: exact; print-color-adjust: exact;
  }
  .doc { padding: 2px 0 6px; }
  .head {
    display: flex; justify-content: space-between; align-items: flex-end; gap: 12px;
    margin-bottom: 12px; padding: 12px 14px; border-radius: 12px;
    background: linear-gradient(125deg, #4f46e5 0%, #6d28d9 40%, #9333ea 75%, #a855f7 100%);
    color: #fff;
  }
  .head .brand {
    display: inline-block; margin-bottom: 6px; padding: 2px 9px; border-radius: 999px;
    font-size: 9.5px; font-weight: 700;
    background: rgba(255,255,255,0.18); border: 1px solid rgba(255,255,255,0.28);
  }
  .head h1 { margin: 0 0 3px; font-size: 18px; font-weight: 800; letter-spacing: 0.02em; }
  .head .sub { margin: 0; font-size: 10.5px; opacity: 0.9; }
  .head .meta {
    min-width: 150px; text-align: right; font-size: 10px; line-height: 1.65;
    padding: 8px 10px; border-radius: 9px;
    background: rgba(255,255,255,0.14); border: 1px solid rgba(255,255,255,0.22);
  }
  section.block {
    margin-bottom: 12px; padding: 10px 10px 8px;
    border: 1px solid #e0e7ff; border-radius: 10px; background: #fff;
    break-inside: avoid;
    page-break-inside: avoid;
  }
  section.block h2 {
    margin: 0 0 8px; padding: 3px 0 3px 10px;
    font-size: 12px; font-weight: 800; color: #3730a3;
    border-left: 4px solid #6366f1; border-radius: 0 6px 6px 0;
    background: linear-gradient(90deg, #eef2ff, #fafaff);
  }
  section.block h2.amber { color: #92400e; border-left-color: #f59e0b; background: linear-gradient(90deg, #fffbeb, #fffdf8); }
  section.block h2.teal { color: #115e59; border-left-color: #14b8a6; background: linear-gradient(90deg, #f0fdfa, #f8fffe); }
  section.block h2.rose { color: #9f1239; border-left-color: #f43f5e; background: linear-gradient(90deg, #fff1f2, #fffafa); }
  section.block .hint { margin: -4px 0 8px; font-size: 9.5px; color: #64748b; }
  .month-grid {
    display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 6px; margin-bottom: 8px;
  }
  .month-cell {
    border: 1px solid #e2e8f0; border-radius: 8px; padding: 6px 8px;
    background: linear-gradient(180deg, #fafbff, #f8fafc);
  }
  .month-cell .m { font-size: 9.5px; font-weight: 700; color: #64748b; }
  .month-cell .v { margin-top: 2px; font-size: 13px; font-weight: 800; font-variant-numeric: tabular-nums; color: #0f172a; }
  .month-cell .s { margin-top: 1px; font-size: 9px; color: #94a3b8; line-height: 1.35; }
  table { width: 100%; border-collapse: collapse; }
  th, td { border: 1px solid #c7d2fe; padding: 3px 6px; }
  th { background: linear-gradient(180deg, #f5f3ff, #eef2ff); color: #3730a3; font-weight: 700; font-size: 9.5px; }
  td { font-size: 10px; }
  td.r, th.r { text-align: right; font-variant-numeric: tabular-nums; }
  td.c, th.c { text-align: center; }
  td.up { color: #dc2626; font-weight: 700; }
  td.down { color: #2563eb; font-weight: 700; }
  tbody tr:nth-child(even) { background: #f8fafc; }
  figure.chart {
    margin: 8px 0 0; border: 1px solid #e0e7ff; border-radius: 8px; padding: 4px;
    background: #fff; break-inside: avoid;
  }
  figure.chart figcaption { font-size: 9.5px; font-weight: 700; color: #4338ca; padding: 1px 3px 3px; }
  figure.chart img { width: 100%; height: auto; display: block; }
  .chip {
    display: inline-block; padding: 1px 7px; border-radius: 999px;
    font-size: 9.5px; font-weight: 700; background: #e0e7ff; color: #3730a3;
  }
  .chip.danger { background: #fee2e2; color: #b91c1c; }
  .chip.warn { background: #fef3c7; color: #b45309; }
  .chip.ok { background: #d1fae5; color: #047857; }
  ul.ideas { margin: 0; padding-left: 18px; color: #475569; }
  ul.ideas li { margin: 2px 0; line-height: 1.5; }
  footer.doc {
    margin-top: 10px; padding-top: 6px; border-top: 1px solid #c7d2fe;
    color: #94a3b8; font-size: 9px; display: flex; justify-content: space-between;
  }
`

function chartFigure(src: string | undefined, title: string): string {
  if (!src) return ''
  return `<figure class="chart">
    <figcaption>${escapeHtml(title)}</figcaption>
    <img src="${src}" alt="${escapeHtml(title)}" />
  </figure>`
}

function monthCells(
  rows: MonthlyReportKpi[],
  valueFn: (m: MonthlyReportKpi) => string,
  subFn?: (m: MonthlyReportKpi) => string,
): string {
  if (!rows.length) return '<div class="month-cell"><div class="m">—</div><div class="v">0</div></div>'
  return rows
    .map(
      (m) => `<div class="month-cell">
        <div class="m">${escapeHtml(m.month_label)}</div>
        <div class="v">${valueFn(m)}</div>
        ${subFn ? `<div class="s">${subFn(m)}</div>` : ''}
      </div>`,
    )
    .join('')
}

function waitForImages(root: Document | ParentNode): Promise<void> {
  const imgs =
    root instanceof Document
      ? Array.from(root.images)
      : Array.from((root as ParentNode).querySelectorAll('img'))
  if (!imgs.length) return Promise.resolve()
  return Promise.all(
    imgs.map(
      (img) =>
        new Promise<void>((resolve) => {
          if (img.complete && img.naturalWidth > 0) return resolve()
          img.onload = () => resolve()
          img.onerror = () => resolve()
        }),
    ),
  ).then(() => undefined)
}

/** 画面と同じ構成の報告書 HTML（印刷・PDF 共通） */
export function buildInventoryReportHtml(input: InventoryReportExportInput): string {
  const p = input.payload
  const months = input.monthlyKpis
  const charts = input.chartImages || {}
  const exportedAt = localeNow()

  const bulkCatCells = input.bulkCategories.length
    ? input.bulkCategories
        .map(
          (c) => `<div class="month-cell">
            <div class="m">${escapeHtml(c.name)}</div>
            <div class="v">${fmtInt(c.quantity)}</div>
            <div class="s">${fmtInt(c.count)}件</div>
          </div>`,
        )
        .join('')
    : `<div class="month-cell"><div class="m">—</div><div class="v">0</div><div class="s">対象期間なし</div></div>`

  const diffRows = input.diffByProcessAvg
    .map(
      (r) => `<tr>
        <td>${escapeHtml(r.process_name)}</td>
        <td class="c">${escapeHtml(r.process_cd)}</td>
        <td class="c">${r.month_count}</td>
        <td class="r">${fmtSen(r.theoretical_qty)}</td>
        <td class="r">${fmtSen(r.stocktake_qty)}</td>
        <td class="r ${diffClass(r.diff_qty)}">${fmtSignedSen(r.diff_qty)}</td>
        <td class="r">${r.diff_rate == null ? '—' : fmtPct(r.diff_rate)}</td>
      </tr>`,
    )
    .join('')

  return `<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8" />
<title>${escapeHtml(p.label)} 在庫報告書</title>
<style>${REPORT_STYLES}</style>
</head>
<body>
  <div class="doc">
    <header class="head">
      <div>
        <span class="brand">Smart-EMAPs ／ 在庫管理</span>
        <h1>在庫報告管理</h1>
        <p class="sub">${escapeHtml(p.label)}　単位：千本（廃棄本数・在庫）／本（大量廃棄等）</p>
      </div>
      <div class="meta">
        対象：${escapeHtml(p.period?.start || '—')} 〜 ${escapeHtml(p.period?.end || '—')}<br />
        集計：${escapeHtml(p.generated_at || '—')}<br />
        出力：${escapeHtml(exportedAt)}
      </div>
    </header>

    <section class="block pdf-kpi-block">
      <h2 class="teal">月末在庫（仕掛品・製品）</h2>
      <div class="month-grid">
        ${monthCells(
          months,
          (m) => `計 ${fmtSen(m.closing_total_qty)}`,
          (m) => `仕掛 ${fmtSen(m.closing_wip_qty)} / 製品 ${fmtSen(m.closing_product_qty)}　千本`,
        )}
      </div>
      ${chartFigure(charts.inventory, '月末在庫（仕掛品・製品）')}
    </section>

    <section class="block pdf-kpi-block">
      <h2 class="teal">期末仕掛品</h2>
      <div class="month-grid">
        ${monthCells(months, (m) => fmtSen(m.closing_wip_qty), () => '千本')}
      </div>
      ${chartFigure(charts.wip, '期末仕掛品')}
    </section>

    <section class="block pdf-kpi-block">
      <h2 class="teal">期末製品 <small style="font-weight:700;color:#64748b">目安 ${RPT_TARGET_CLOSING_PRODUCT_SEN}千本</small></h2>
      <div class="month-grid">
        ${monthCells(months, (m) => fmtSen(m.closing_product_qty), () => '千本')}
      </div>
      ${chartFigure(charts.product, '期末製品')}
    </section>

    <section class="block pdf-kpi-block">
      <h2 class="rose">廃棄率 <small style="font-weight:700;color:#64748b">目安 ${RPT_TARGET_SCRAP_RATE_PERCENT}%</small></h2>
      <div class="month-grid">
        ${monthCells(months, (m) => fmtPct(m.quality_loss_rate_percent), () => '連乗損失率')}
      </div>
      ${chartFigure(charts.scrapRate, '廃棄率')}
    </section>

    <section class="block pdf-kpi-block">
      <h2 class="rose">廃棄本数</h2>
      <div class="month-grid">
        ${monthCells(months, (m) => fmtSen(m.loss_qty), () => '千本・不良+廃棄')}
      </div>
      ${chartFigure(charts.scrapQty, '廃棄本数')}
    </section>

    <section class="block pdf-kpi-block">
      <h2>棚卸一致率</h2>
      <div class="month-grid">
        ${monthCells(
          months,
          (m) => fmtPct(m.match_rate),
          (m) => `差異 |Σ| ${fmtInt(m.diff_abs)}`,
        )}
      </div>
      ${chartFigure(charts.match, '棚卸一致率')}
    </section>

    <section class="block">
      <h2>理論在庫 vs 棚卸差異（工程別）</h2>
      <p class="hint">対象期間の月平均・単位：千本（検査は倉庫へ合算／切断・面取は差異なし／右軸＝差異率）</p>
      ${chartFigure(charts.diff, '棚卸差異（工程別・期間平均）')}
      <table style="margin-top:8px">
        <thead><tr>
          <th>工程</th><th class="c">工程CD</th><th class="c">対象月数</th>
          <th class="r">理論在庫(平均・千)</th><th class="r">棚卸在庫(平均・千)</th>
          <th class="r">差異(平均・千)</th><th class="r">差異率%(平均)</th>
        </tr></thead>
        <tbody>${diffRows || '<tr><td colspan="7" class="c">データなし</td></tr>'}</tbody>
      </table>
    </section>

    <section class="block pdf-kpi-block">
      <h2 class="amber">大量廃棄・保留品・大量不良（対象期間）</h2>
      ${
        chartFigure(charts.bulkDetail, '大量廃棄・保留品・大量不良') ||
        '<p class="hint">グラフデータがありません</p>'
      }
    </section>

    <footer class="doc">
      <span>Smart-EMAPs 在庫報告管理</span>
      <span>${escapeHtml(p.label)}</span>
    </footer>
  </div>
</body>
</html>`
}

async function openHtmlInHiddenFrame(html: string): Promise<{
  iframe: HTMLIFrameElement
  doc: Document
  win: Window
}> {
  const iframe = document.createElement('iframe')
  iframe.setAttribute('title', 'inventory-report-export')
  iframe.style.cssText =
    'position:fixed;right:0;bottom:0;width:0;height:0;border:0;opacity:0;pointer-events:none'
  document.body.appendChild(iframe)
  const doc = iframe.contentDocument
  const win = iframe.contentWindow
  if (!doc || !win) {
    iframe.remove()
    throw new Error('出力用フレームの作成に失敗しました')
  }
  doc.open()
  doc.write(html)
  doc.close()
  if (doc.fonts?.ready) {
    try {
      await doc.fonts.ready
    } catch {
      /* ignore */
    }
  }
  await waitForImages(doc)
  await new Promise<void>((r) => requestAnimationFrame(() => requestAnimationFrame(() => r())))
  return { iframe, doc, win }
}

export async function printInventoryReport(input: InventoryReportExportInput): Promise<void> {
  const html = buildInventoryReportHtml(input)
  const { iframe, win } = await openHtmlInHiddenFrame(html)
  try {
    await new Promise<void>((resolve) => {
      window.setTimeout(() => {
        try {
          win.focus()
          win.print()
        } finally {
          resolve()
        }
      }, 120)
    })
  } finally {
    window.setTimeout(() => {
      if (iframe.parentNode) iframe.parentNode.removeChild(iframe)
    }, 1200)
  }
}

/** Excel：画面に表示している表・数値と同じ項目 */
export function buildInventoryReportExcelSheets(input: InventoryReportExportInput): ExcelSheetAoa[] {
  const p = input.payload
  const months = input.monthlyKpis

  const inventoryAoa: (string | number)[][] = [
    ['月', '期末合計(千本)', '期末仕掛品(千本)', '期末製品(千本)'],
    ...months.map((m) => [
      m.month_label,
      excelSen(m.closing_total_qty),
      excelSen(m.closing_wip_qty),
      excelSen(m.closing_product_qty),
    ]),
  ]

  const kpiAoa: (string | number)[][] = [
    [
      '月',
      '期末仕掛品(千本)',
      '期末製品(千本)',
      '廃棄率(%)',
      '廃棄本数(千本)',
      '棚卸一致率(%)',
      '差異絶対値',
    ],
    ...months.map((m) => [
      m.month_label,
      excelSen(m.closing_wip_qty),
      excelSen(m.closing_product_qty),
      excelNum(m.quality_loss_rate_percent),
      excelSen(m.loss_qty ?? 0),
      excelNum(m.match_rate),
      excelNum(m.diff_abs),
    ]),
  ]

  const bulkCatAoa: (string | number)[][] = [
    ['区分', '件数', '本数'],
    ...(input.bulkCategories.length
      ? input.bulkCategories.map((r) => [r.name, excelNum(r.count), excelNum(r.quantity)])
      : [['（対象期間なし）', 0, 0]]),
  ]

  const diffAoa: (string | number)[][] = [
    [
      '工程',
      '工程CD',
      '対象月数',
      '理論在庫(平均・千本)',
      '棚卸在庫(平均・千本)',
      '差異(平均・千本)',
      '差異率%(平均)',
    ],
    ...input.diffByProcessAvg.map((r) => [
      r.process_name || '',
      r.process_cd || '',
      excelNum(r.month_count),
      excelSen(r.theoretical_qty),
      excelSen(r.stocktake_qty),
      excelSen(r.diff_qty),
      excelNum(r.diff_rate),
    ]),
  ]

  const bulkDetailAoa: (string | number)[][] = [
    ['発生日', '区分', '工程', '製品', '本数', '状態'],
    ...(p.bulk_disposal?.items || []).map((r) => [
      String(r.occurred_date ?? ''),
      String(r.report_category ?? ''),
      String(r.process_name ?? ''),
      String(r.product_name ?? ''),
      excelNum(Number(r.quantity)),
      String(r.handling_status ?? ''),
    ]),
  ]

  return [
    { name: '月末在庫', aoa: inventoryAoa },
    { name: '月別KPI', aoa: kpiAoa },
    { name: '大量廃棄区分', aoa: bulkCatAoa },
    { name: '棚卸差異', aoa: diffAoa },
    { name: '大量廃棄明細', aoa: bulkDetailAoa },
  ]
}

export async function exportInventoryReportExcel(input: InventoryReportExportInput): Promise<string> {
  const label = safeLabel(input.payload.label)
  const filename = `在庫報告_${label}_${fileStamp()}.xlsx`
  await downloadExcelMultiSheet(buildInventoryReportExcelSheets(input), filename)
  return filename
}

type PdfBlockBand = {
  /** ルート相対・px（レイアウト時） */
  top: number
  bottom: number
  /** KPI カードなど：ページ途中で切らない */
  keepTogether: boolean
}

function measurePdfBlocks(root: HTMLElement): PdfBlockBand[] {
  const rootTop = root.getBoundingClientRect().top
  const nodes = [
    root.querySelector('.head'),
    ...Array.from(root.querySelectorAll('section.block')),
    root.querySelector('footer.doc'),
  ].filter((el): el is HTMLElement => el instanceof HTMLElement)

  return nodes.map((el) => {
    const rect = el.getBoundingClientRect()
    return {
      top: Math.max(0, Math.round(rect.top - rootTop)),
      bottom: Math.max(1, Math.round(rect.bottom - rootTop)),
      keepTogether: el.classList.contains('pdf-kpi-block') || el.classList.contains('head'),
    }
  })
}

/** ブロック境界でページを組み、KPI カードを途中分割しない */
function buildPdfPageBands(blocks: PdfBlockBand[], pageContentPx: number): Array<{ top: number; bottom: number }> {
  if (!blocks.length) return [{ top: 0, bottom: pageContentPx }]
  const pages: Array<{ top: number; bottom: number }> = []
  let pageTop = blocks[0]!.top
  let pageBottom = pageTop

  const flush = () => {
    if (pageBottom > pageTop) pages.push({ top: pageTop, bottom: pageBottom })
  }

  for (const block of blocks) {
    const blockH = Math.max(1, block.bottom - block.top)
    const wouldEnd = Math.max(pageBottom, block.bottom)
    const used = wouldEnd - pageTop

    if (used <= pageContentPx || pageBottom <= pageTop) {
      pageBottom = Math.max(pageBottom, block.bottom)
      continue
    }

    // 現在ページを確定してから次ブロックへ
    flush()
    pageTop = block.top
    pageBottom = block.bottom

    // 1 ブロックが 1 ページを超える（長い表など）→ 強制スライス
    if (!block.keepTogether && blockH > pageContentPx) {
      let sliceTop = block.top
      while (sliceTop < block.bottom - 1) {
        const sliceBottom = Math.min(block.bottom, sliceTop + pageContentPx)
        pages.push({ top: sliceTop, bottom: sliceBottom })
        sliceTop = sliceBottom
      }
      pageTop = block.bottom
      pageBottom = block.bottom
    }
  }
  flush()
  return pages.length ? pages : [{ top: 0, bottom: pageContentPx }]
}

function sliceCanvasBand(
  source: HTMLCanvasElement,
  topPx: number,
  bottomPx: number,
  layoutWidthPx: number,
): HTMLCanvasElement {
  const scaleX = source.width / Math.max(1, layoutWidthPx)
  const sy = Math.max(0, Math.floor(topPx * scaleX))
  const ey = Math.min(source.height, Math.ceil(bottomPx * scaleX))
  const sh = Math.max(1, ey - sy)
  const out = document.createElement('canvas')
  out.width = source.width
  out.height = sh
  const ctx = out.getContext('2d')
  if (!ctx) throw new Error('PDFの生成に失敗しました')
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, out.width, out.height)
  ctx.drawImage(source, 0, sy, source.width, sh, 0, 0, out.width, sh)
  return out
}

/**
 * PDF 出力：全文を一度キャプチャし、KPI カード境界で改ページする。
 * （iframe を画面外に飛ばしてセグメント単位キャプチャすると空白 PDF になるブラウザがある）
 */
export async function exportInventoryReportPdf(input: InventoryReportExportInput): Promise<string> {
  const html = buildInventoryReportHtml(input)
  const parsed = new DOMParser().parseFromString(html, 'text/html')
  const sourceDoc = parsed.querySelector('.doc')
  if (!sourceDoc) throw new Error('PDFの生成に失敗しました')

  // ビューポート内・不可視で描画（大きく負の left だと html2canvas が空白になる）
  const host = document.createElement('div')
  host.setAttribute('data-inventory-report-pdf', '1')
  host.style.cssText = [
    'position:fixed',
    'left:0',
    'top:0',
    `width:${PDF_PAGE_WIDTH_PX}px`,
    'max-height:1px',
    'overflow:hidden',
    'opacity:0',
    'pointer-events:none',
    'z-index:-1',
  ].join(';')

  const mount = document.createElement('div')
  mount.style.cssText = `width:${PDF_PAGE_WIDTH_PX}px;background:#fff;box-sizing:border-box;`
  parsed.querySelectorAll('style').forEach((styleEl) => {
    mount.appendChild(document.importNode(styleEl, true))
  })
  const root = document.importNode(sourceDoc, true) as HTMLElement
  mount.appendChild(root)
  host.appendChild(mount)
  document.body.appendChild(host)

  try {
    if (document.fonts?.ready) {
      try {
        await document.fonts.ready
      } catch {
        /* ignore */
      }
    }
    await waitForImages(mount)
    const imgs = Array.from(mount.querySelectorAll('img'))
    await Promise.all(
      imgs.map(async (img) => {
        try {
          if (typeof img.decode === 'function') await img.decode()
        } catch {
          /* ignore */
        }
      }),
    )
    await new Promise<void>((r) => requestAnimationFrame(() => requestAnimationFrame(() => r())))

    // 一時的に高さ制限を外して実寸を測る（capture 用）
    host.style.maxHeight = 'none'
    host.style.height = 'auto'
    host.style.overflow = 'visible'

    const layoutWidth = Math.max(root.scrollWidth, PDF_PAGE_WIDTH_PX)
    const layoutHeight = Math.max(root.scrollHeight, root.offsetHeight, 200)
    if (layoutHeight < 40) throw new Error('PDFの生成に失敗しました（内容が空です）')

    const fullCanvas = await html2canvas(root, {
      scale: 2,
      useCORS: true,
      allowTaint: true,
      backgroundColor: '#ffffff',
      logging: false,
      width: layoutWidth,
      height: layoutHeight,
      windowWidth: layoutWidth,
      windowHeight: layoutHeight,
      scrollX: -window.scrollX,
      scrollY: -window.scrollY,
      x: 0,
      y: 0,
      onclone: (_doc, cloned) => {
        const el = cloned as HTMLElement
        el.style.overflow = 'visible'
        el.style.height = 'auto'
        el.style.maxHeight = 'none'
      },
    })

    if (!fullCanvas.width || !fullCanvas.height) {
      throw new Error('PDFの生成に失敗しました（キャプチャ失敗）')
    }

    const pdf = new jsPDF({ orientation: 'p', unit: 'mm', format: 'a4', compress: true })
    const pageWidth = pdf.internal.pageSize.getWidth()
    const pageHeight = pdf.internal.pageSize.getHeight()
    const margin = 8
    const contentWidthMm = pageWidth - margin * 2
    const contentHeightMm = pageHeight - margin * 2
    const pxPerMm = layoutWidth / contentWidthMm
    const pageContentPx = Math.floor(contentHeightMm * pxPerMm)

    const blocks = measurePdfBlocks(root)
    const bands = buildPdfPageBands(
      blocks.length
        ? blocks
        : [{ top: 0, bottom: layoutHeight, keepTogether: false }],
      pageContentPx,
    )

    bands.forEach((band, index) => {
      if (index > 0) pdf.addPage()
      const slice = sliceCanvasBand(fullCanvas, band.top, band.bottom, layoutWidth)
      const imgData = slice.toDataURL('image/jpeg', 0.92)
      let drawW = contentWidthMm
      let drawH = (slice.height / slice.width) * drawW
      // KPI など keepTogether で 1 ページを超える場合は縮小して収める
      if (drawH > contentHeightMm) {
        const scale = contentHeightMm / drawH
        drawW *= scale
        drawH = contentHeightMm
      }
      pdf.addImage(imgData, 'JPEG', margin, margin, drawW, drawH, undefined, 'FAST')
    })

    const label = safeLabel(input.payload.label)
    const filename = `在庫報告_${label}_${fileStamp()}.pdf`
    pdf.save(filename)
    return filename
  } finally {
    host.remove()
  }
}
