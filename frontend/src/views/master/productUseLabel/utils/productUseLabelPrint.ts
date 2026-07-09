import QRCode from 'qrcode'
import { buildPrintHtmlDocument, escapeHtml, openPrintWindow } from '@/utils/printWindow'

export interface ProductUseLabelPrintInput {
  product_cd?: string
  use_label_product_name: string
  unit_qty?: number | null
  part_no?: string | null
  destination_name?: string | null
  paper_color?: string | null
  product_name_color?: string | null
  back_no_1?: string | null
  back_no_2?: string | null
  back_no_3?: string | null
  barcode_no?: string | null
}

export interface ProductUseLabelPrintOptions {
  pages?: number
  copiesPerPage?: number
}

const DEFAULT_MANUFACTURER_LINES = ['日鉄物産荒井', 'オートモーティブ(株)']

const PAPER_BG: Record<string, string> = {
  白: '#ffffff',
  黄: '#fff59d',
  ピンク: '#f8bbd0',
  緑: '#c8e6c9',
  青: '#bbdefb',
  オレンジ: '#ffe0b2',
}

/** ページ外枠余白の縮小率（40%減 → 現行値の60%） */
const PAGE_MARGIN_FACTOR = 0.6
const EXTRA_MARGIN_PX = 1
const EXTRA_MARGIN_MM = ((EXTRA_MARGIN_PX / 96) * 25.4) * PAGE_MARGIN_FACTOR
const BASE_PAGE_MARGIN_MM = 4 * PAGE_MARGIN_FACTOR
/** ページ外枠＝裁断後ラベル外周余白（GUTTER の半分と一致） */
const PAGE_MARGIN_MM = BASE_PAGE_MARGIN_MM + EXTRA_MARGIN_MM
/** ラベル間隔（裁断虚線は中央。裁断後の余白 = GUTTER/2 = PAGE_MARGIN） */
const GUTTER_MM = PAGE_MARGIN_MM * 2
const B4_WIDTH_MM = 353
const B4_HEIGHT_MM = 250
const INNER_WIDTH_MM = B4_WIDTH_MM - PAGE_MARGIN_MM * 2
const INNER_HEIGHT_MM = B4_HEIGHT_MM - PAGE_MARGIN_MM * 2

const STANDARD_COLS = 5
const STANDARD_ROWS = 4
const INOAC_COLS = 4
const INOAC_ROWS = 4

/** 標準ラベル（4×5）1枚の高さ mm */
const STD_LABEL_HEIGHT_MM =
  (INNER_HEIGHT_MM - GUTTER_MM * (STANDARD_ROWS - 1)) / STANDARD_ROWS
/** 入数行・メーカー行：固定高（mm） */
const STD_QTY_ROW_MM = 9
const STD_MFG_ROW_MM = 11.5
const STD_TOP_ROW_MM = Number((STD_LABEL_HEIGHT_MM * 0.22).toFixed(2))
const STD_NAME_ROW_MM = Number(
  (STD_LABEL_HEIGHT_MM - STD_TOP_ROW_MM - STD_QTY_ROW_MM - STD_MFG_ROW_MM).toFixed(2)
)
const STD_STAMP_CELL_MM = STD_QTY_ROW_MM + STD_MFG_ROW_MM
/** メーカー行：标题・内容上余白（mm） */
const STD_MFG_LBL_PADDING_TOP_MM = 2.5
const STD_MFG_INNER_PADDING_TOP_MM = 1.1

const FONT =
  "'Yu Gothic UI', 'Yu Gothic', 'MS Gothic', 'Hiragino Sans', sans-serif"

export function isInoacDestination(destination?: string | null): boolean {
  const raw = (destination || '').trim()
  if (!raw) return false
  const compact = raw.replace(/\s/g, '').replace(/　/g, '').toUpperCase()
  if (
    compact.includes('N05') &&
    (compact.includes('東北INOAC') ||
      compact.includes('東北イノアック') ||
      compact.includes('INOAC'))
  ) {
    return true
  }
  if (compact.includes('東北INOAC小牛田') || compact.includes('東北イノアック小牛田')) {
    return true
  }
  return false
}

function getLayout(inoac: boolean) {
  const cols = inoac ? INOAC_COLS : STANDARD_COLS
  const rows = inoac ? INOAC_ROWS : STANDARD_ROWS
  const labelWidthMm = (INNER_WIDTH_MM - GUTTER_MM * (cols - 1)) / cols
  const labelHeightMm = (INNER_HEIGHT_MM - GUTTER_MM * (rows - 1)) / rows
  return {
    cols,
    rows,
    perPage: cols * rows,
    labelWidthMm,
    labelHeightMm,
    innerWidthMm: INNER_WIDTH_MM,
    innerHeightMm: INNER_HEIGHT_MM,
    sheetWidthMm: B4_WIDTH_MM,
    sheetHeightMm: B4_HEIGHT_MM,
  }
}

export function getProductUseLabelB4Layout(inoac = false) {
  return {
    b4WidthMm: B4_WIDTH_MM,
    b4HeightMm: B4_HEIGHT_MM,
    pageMarginMm: PAGE_MARGIN_MM,
    gutterMm: GUTTER_MM,
    innerWidthMm: INNER_WIDTH_MM,
    innerHeightMm: INNER_HEIGHT_MM,
    ...getLayout(inoac),
  }
}

function paperBackground(color?: string | null): string {
  return PAPER_BG[color || '白'] || PAPER_BG['白']
}

function nameColor(hex?: string | null): string {
  const v = (hex || '#000000').trim()
  return /^#[0-9a-f]{3,8}$/i.test(v) ? v : '#000000'
}

async function makeQrDataUrl(text: string, px: number): Promise<string> {
  const cd = (text || '').trim() || '-'
  try {
    return await QRCode.toDataURL(cd, {
      width: px,
      margin: 0,
      errorCorrectionLevel: 'M',
    })
  } catch {
    return ''
  }
}

function simpleBarcodeSvg(text: string, widthPx: number, heightPx: number): string {
  const raw = (text || '0').trim()
  let x = 0
  const rects: string[] = []
  for (let i = 0; i < raw.length; i++) {
    const barW = (raw.charCodeAt(i) % 3) + 1
    if (i % 2 === 0) {
      rects.push(`<rect x="${x}" y="0" width="${barW}" height="${heightPx}" fill="#000"/>`)
    }
    x += barW + 1
  }
  const viewW = Math.max(x, 20)
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${widthPx}" height="${heightPx}" viewBox="0 0 ${viewW} ${heightPx}" preserveAspectRatio="none">${rects.join('')}</svg>`
}


async function buildStandardLabelHtml(
  input: ProductUseLabelPrintInput,
  wMm: number,
  hMm: number
): Promise<string> {
  const qrPx = Math.round(((hMm * 0.22) / 25.4) * 96)
  const qrSrc = await makeQrDataUrl(input.product_cd || input.part_no || '', qrPx)
  const bg = paperBackground(input.paper_color)
  const pColor = nameColor(input.product_name_color)
  const productName = escapeHtml(input.use_label_product_name || '')
  const back1 = escapeHtml(input.back_no_1 || '')
  const back2 = escapeHtml(input.back_no_2 || '')
  const partNo = escapeHtml(input.part_no || '')
  const qty = input.unit_qty != null ? escapeHtml(String(input.unit_qty)) : ''
  const mfg = DEFAULT_MANUFACTURER_LINES.map(
    (line) => `<div class="pul-mfg-line">${escapeHtml(line)}</div>`
  ).join('')

  return `<div class="pul-label pul-label--std" style="background:${bg}">
    <table class="pul-std-table" cellspacing="0" cellpadding="0">
      <tr class="pul-std-row-top">
        <td class="pul-std-lbl">背番</td>
        <td class="pul-std-back">
          <div class="pul-back-line">${back1 || '&nbsp;'}</div>
          <div class="pul-back-line">${back2 || partNo || '&nbsp;'}</div>
        </td>
        <td class="pul-std-qr">${qrSrc ? `<img src="${qrSrc}" alt="QR"/>` : ''}</td>
      </tr>
      <tr class="pul-std-row-name">
        <td class="pul-std-lbl">品名</td>
        <td colspan="2" class="pul-std-product" style="color:${pColor}">${productName || '&nbsp;'}</td>
      </tr>
      <tr class="pul-std-row-qty" style="height:${STD_QTY_ROW_MM}mm">
        <td class="pul-std-lbl">入数</td>
        <td class="pul-std-qty">${qty || '&nbsp;'}</td>
        <td class="pul-std-stamp" rowspan="2" style="height:${STD_STAMP_CELL_MM}mm">
          <div class="pul-stamp-lbl">合格印</div>
        </td>
      </tr>
      <tr class="pul-std-row-mfg" style="height:${STD_MFG_ROW_MM}mm">
        <td class="pul-std-lbl">メーカー</td>
        <td class="pul-std-mfg"><div class="pul-mfg-inner">${mfg}</div></td>
      </tr>
    </table>
  </div>`
}

async function buildInoacLabelHtml(
  input: ProductUseLabelPrintInput,
  wMm: number,
  hMm: number
): Promise<string> {
  const qrPx = Math.round(((wMm * 0.2) / 25.4) * 96)
  const qrSrc = await makeQrDataUrl(input.product_cd || '', qrPx)
  const bg = paperBackground(input.paper_color)
  const pColor = nameColor(input.product_name_color)
  const productName = escapeHtml(input.use_label_product_name || '')
  const partNo = escapeHtml(input.part_no || '')
  const dest = escapeHtml(input.destination_name || '')
  const qty = input.unit_qty != null ? `${escapeHtml(String(input.unit_qty))} 本` : ''
  const barcode = escapeHtml(input.barcode_no || '')
  const mfg = DEFAULT_MANUFACTURER_LINES.map(escapeHtml).join(' ')
  const barW = Math.round(((wMm * 0.22) / 25.4) * 96)
  const barH = Math.round(((hMm * 0.12) / 25.4) * 96)
  const barcodeSvg = simpleBarcodeSvg(input.barcode_no || '', barW, barH)

  const historyCells = [1, 2, 3, 4, 5]
    .map(
      (n) =>
        `<td class="pul-inoac-hist-cell"><div class="pul-inoac-hist-num">${n}</div><div class="pul-inoac-hist-blank"></div></td>`
    )
    .join('')

  return `<div class="pul-label pul-label--inoac" style="background:${bg}">
    <table class="pul-inoac-table" cellspacing="0" cellpadding="0">
      <tr class="pul-inoac-head">
        <td class="pul-inoac-qr-cell">
          <div class="pul-inoac-mini">工場用 QRコード</div>
          ${qrSrc ? `<img class="pul-inoac-qr" src="${qrSrc}" alt="QR"/>` : ''}
        </td>
        <td class="pul-inoac-name-cell">
          <div class="pul-inoac-mini">&lt; 品名 &gt;</div>
          <div class="pul-inoac-product" style="color:${pColor}">${productName || '&nbsp;'}</div>
        </td>
        <td class="pul-inoac-bar-cell">
          <div class="pul-inoac-mini">品番用 バーコード</div>
          <div class="pul-inoac-barcode-no">${barcode || '&nbsp;'}</div>
          <div class="pul-inoac-barcode">${barcodeSvg}</div>
        </td>
      </tr>
      <tr>
        <td colspan="2" class="pul-inoac-kv"><span class="pul-k">品番</span><span class="pul-v">${partNo || '&nbsp;'}</span></td>
        <td class="pul-inoac-kv"><span class="pul-k">収容数</span><span class="pul-v">${qty || '&nbsp;'}</span></td>
      </tr>
      <tr>
        <td colspan="2" class="pul-inoac-kv"><span class="pul-k">納入先</span><span class="pul-v pul-v-sm">${dest || '&nbsp;'}</span></td>
        <td class="pul-inoac-kv"><span class="pul-k">メーカー</span><span class="pul-v pul-v-sm">${mfg}</span></td>
      </tr>
      <tr>
        <td colspan="3" class="pul-inoac-hist-wrap">
          <div class="pul-inoac-mini pul-inoac-hist-title">&lt; 加工履歴 &gt;</div>
          <table class="pul-inoac-hist" cellspacing="0" cellpadding="0"><tr>${historyCells}</tr></table>
        </td>
      </tr>
    </table>
  </div>`
}

async function buildLabelHtml(
  input: ProductUseLabelPrintInput,
  _wMm: number,
  _hMm: number
): Promise<string> {
  if (isInoacDestination(input.destination_name)) {
    return buildInoacLabelHtml(input, _wMm, _hMm)
  }
  return buildStandardLabelHtml(input, _wMm, _hMm)
}

function buildSheetCutGuidesHtml(
  cols: number,
  rows: number,
  labelWidthMm: number,
  labelHeightMm: number,
  gutterMm: number
): string {
  const parts: string[] = []
  for (let c = 1; c < cols; c++) {
    const left = c * labelWidthMm + (c - 0.5) * gutterMm
    parts.push(
      `<div class="pul-cut-guide pul-cut-guide-v" style="left:${left}mm" aria-hidden="true"></div>`
    )
  }
  for (let r = 1; r < rows; r++) {
    const top = r * labelHeightMm + (r - 0.5) * gutterMm
    parts.push(
      `<div class="pul-cut-guide pul-cut-guide-h" style="top:${top}mm" aria-hidden="true"></div>`
    )
  }
  return parts.join('')
}

function buildPrintStyles(inoac: boolean): string {
  const layout = getLayout(inoac)
  return `
  @page { size: B4 landscape; margin: 0; }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; font-family: ${FONT}; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .pul-sheet {
    width: ${B4_WIDTH_MM}mm;
    height: ${B4_HEIGHT_MM}mm;
    padding: ${PAGE_MARGIN_MM}mm;
    page-break-after: always;
    break-after: page;
    page-break-inside: avoid;
  }
  .pul-sheet:last-child { page-break-after: auto; break-after: auto; }
  .pul-sheet-inner {
    position: relative;
    width: ${layout.innerWidthMm}mm;
    height: ${layout.innerHeightMm}mm;
    display: grid;
    grid-template-columns: repeat(${layout.cols}, ${layout.labelWidthMm}mm);
    grid-template-rows: repeat(${layout.rows}, ${layout.labelHeightMm}mm);
    gap: ${GUTTER_MM}mm;
  }
  .pul-cut-guide {
    position: absolute;
    pointer-events: none;
    z-index: 2;
  }
  .pul-cut-guide-v {
    top: 0;
    bottom: 0;
    width: 0;
    border-left: 0.6pt dashed #888;
  }
  .pul-cut-guide-h {
    left: 0;
    right: 0;
    height: 0;
    border-top: 0.6pt dashed #888;
  }
  .pul-label {
    width: 100%;
    height: 100%;
    border: 1pt solid #111;
    overflow: hidden;
    font-size: 8pt;
    line-height: 1.2;
    margin: 0;
    min-height: 0;
  }
  .pul-label--empty {
    border: none;
    background: transparent !important;
    visibility: hidden;
  }
  table { width: 100%; height: 100%; border-collapse: collapse; table-layout: fixed; }
  td { border: 1px solid #000; vertical-align: middle; padding: 1mm 1.2mm; }
  .pul-std-table { width: 100%; height: 100%; table-layout: fixed; border-collapse: collapse; }
  .pul-std-lbl { width: 12mm; font-size: 7pt; text-align: center; background: #fff; }
  .pul-std-row-top { height: ${STD_TOP_ROW_MM}mm; }
  .pul-std-row-name { height: ${STD_NAME_ROW_MM}mm; }
  .pul-std-row-qty {
    height: ${STD_QTY_ROW_MM}mm;
    max-height: ${STD_QTY_ROW_MM}mm;
  }
  .pul-std-row-mfg {
    height: ${STD_MFG_ROW_MM}mm;
    max-height: ${STD_MFG_ROW_MM}mm;
  }
  .pul-std-row-qty td:not(.pul-std-stamp) {
    height: ${STD_QTY_ROW_MM}mm;
    max-height: ${STD_QTY_ROW_MM}mm;
    overflow: hidden;
    line-height: 1.2;
  }
  .pul-std-row-mfg td {
    height: ${STD_MFG_ROW_MM}mm;
    max-height: ${STD_MFG_ROW_MM}mm;
    overflow: hidden;
    line-height: 1.25;
    text-align: center;
    vertical-align: middle;
    font-size: 8pt;
    padding: 0 1.2mm;
    box-sizing: border-box;
  }
  .pul-std-row-mfg td.pul-std-mfg {
    padding: 0;
    vertical-align: middle;
    overflow: visible;
  }
  .pul-std-row-mfg .pul-std-lbl {
    padding: ${STD_MFG_LBL_PADDING_TOP_MM}mm 1.2mm 0.4mm;
    vertical-align: top;
    box-sizing: border-box;
  }
  .pul-mfg-inner {
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    align-items: center;
    width: 100%;
    height: ${STD_MFG_ROW_MM}mm;
    box-sizing: border-box;
    padding: ${STD_MFG_INNER_PADDING_TOP_MM}mm 1.2mm 0.4mm;
    font-size: 8pt;
    line-height: 1.2;
    text-align: center;
  }
  .pul-std-stamp {
    width: 16mm;
    height: ${STD_STAMP_CELL_MM}mm;
    max-height: ${STD_STAMP_CELL_MM}mm;
    text-align: left;
    padding: 0.5mm;
    vertical-align: top;
  }
  .pul-std-back { font-size: 8pt; font-weight: 600; }
  .pul-back-line { line-height: 1.25; }
  .pul-std-qr { width: 18mm; text-align: center; padding: 0.5mm; }
  .pul-std-qr img { width: 100%; height: auto; max-height: 14mm; display: block; margin: 0 auto; }
  .pul-std-product { font-size: 14pt; font-weight: 800; text-align: center; }
  .pul-std-qty { font-size: 16pt; font-weight: 800; text-align: center; }
  .pul-stamp-lbl { font-size: 6.5pt; margin: 0; text-align: left; line-height: 1.2; }
  .pul-mfg-line { line-height: 1.2; text-align: center; width: 100%; }
  .pul-inoac-mini { font-size: 6pt; text-align: center; line-height: 1.1; margin-bottom: 0.5mm; }
  .pul-inoac-head { height: 34%; }
  .pul-inoac-qr-cell { width: 22%; text-align: center; }
  .pul-inoac-qr { width: 90%; max-height: 14mm; display: block; margin: 0 auto; }
  .pul-inoac-name-cell { text-align: center; }
  .pul-inoac-product { font-size: 13pt; font-weight: 800; line-height: 1.15; }
  .pul-inoac-bar-cell { width: 28%; text-align: center; }
  .pul-inoac-barcode-no { font-size: 8pt; font-weight: 700; margin-bottom: 0.5mm; }
  .pul-inoac-barcode { height: 8mm; overflow: hidden; }
  .pul-inoac-barcode svg { width: 100%; height: 100%; display: block; }
  .pul-inoac-kv { font-size: 7pt; }
  .pul-k { font-weight: 700; margin-right: 1.5mm; }
  .pul-v { font-weight: 600; }
  .pul-v-sm { font-size: 6.5pt; }
  .pul-inoac-hist-wrap { padding: 0.8mm 1mm 1mm; vertical-align: top; }
  .pul-inoac-hist-title { margin-bottom: 0.5mm; }
  .pul-inoac-hist { width: 100%; }
  .pul-inoac-hist td { text-align: center; padding: 0; height: 7mm; }
  .pul-inoac-hist-num { font-size: 7pt; font-weight: 700; border-bottom: 1px solid #000; line-height: 1.2; }
  .pul-inoac-hist-blank { height: 3.5mm; }
  `
}

async function buildSheetsHtml(
  inputs: ProductUseLabelPrintInput[],
  options?: ProductUseLabelPrintOptions
): Promise<string> {
  if (!inputs.length) return ''

  const grouped: { inoac: boolean; items: ProductUseLabelPrintInput[] }[] = []
  for (const item of inputs) {
    const inoac = isInoacDestination(item.destination_name)
    const last = grouped[grouped.length - 1]
    if (last && last.inoac === inoac) {
      last.items.push(item)
    } else {
      grouped.push({ inoac, items: [item] })
    }
  }

  const sheets: string[] = []
  for (const group of grouped) {
    const layout = getLayout(group.inoac)
    const perPage = layout.perPage
    const pages = Math.max(1, options?.pages ?? 1)
    const copiesPerPage = Math.max(1, options?.copiesPerPage ?? 1)

    const expanded: ProductUseLabelPrintInput[] = []
    for (const item of group.items) {
      for (let c = 0; c < copiesPerPage; c++) {
        expanded.push(item)
      }
    }

    for (let p = 0; p < pages; p++) {
      for (let i = 0; i < expanded.length; i += perPage) {
        const chunk = expanded.slice(i, i + perPage)
        const labelHtmls = await Promise.all(
          chunk.map((item) =>
            buildLabelHtml(item, layout.labelWidthMm, layout.labelHeightMm)
          )
        )
        while (labelHtmls.length < perPage) {
          labelHtmls.push(`<div class="pul-label pul-label--empty" aria-hidden="true"></div>`)
        }
        const cutGuides = buildSheetCutGuidesHtml(
          layout.cols,
          layout.rows,
          layout.labelWidthMm,
          layout.labelHeightMm,
          GUTTER_MM
        )
        sheets.push(
          `<div class="pul-sheet"><div class="pul-sheet-inner">${labelHtmls.join('')}${cutGuides}</div></div>`
        )
      }
    }
  }

  return sheets.join('')
}

export async function buildProductUseLabelPrintHtml(
  inputs: ProductUseLabelPrintInput | ProductUseLabelPrintInput[],
  options?: ProductUseLabelPrintOptions
): Promise<string> {
  const list = Array.isArray(inputs) ? inputs : [inputs]
  const inoac = list.some((i) => isInoacDestination(i.destination_name))
  const std = list.some((i) => !isInoacDestination(i.destination_name))
  const styles =
    inoac && std
      ? buildPrintStyles(false) + buildPrintStyles(true)
      : buildPrintStyles(inoac || false)
  const body = await buildSheetsHtml(list, options)
  return buildPrintHtmlDocument('製品用ラベル', styles, body)
}

export async function printProductUseLabels(
  inputs: ProductUseLabelPrintInput | ProductUseLabelPrintInput[],
  options?: ProductUseLabelPrintOptions
): Promise<void> {
  const html = await buildProductUseLabelPrintHtml(inputs, options)
  openPrintWindow(html, { autoPrint: true, autoClose: true, delayMs: 450 })
}

export function configToPrintInput(row: {
  product_cd?: string
  use_label_product_name?: string | null
  unit_qty?: number | null
  part_no?: string | null
  destination_name?: string | null
  paper_color?: string | null
  product_name_color?: string | null
  back_no_1?: string | null
  back_no_2?: string | null
  back_no_3?: string | null
  barcode_no?: string | null
}): ProductUseLabelPrintInput {
  return {
    product_cd: row.product_cd,
    use_label_product_name: row.use_label_product_name || row.product_cd || '',
    unit_qty: row.unit_qty,
    part_no: row.part_no,
    destination_name: row.destination_name,
    paper_color: row.paper_color,
    product_name_color: row.product_name_color,
    back_no_1: row.back_no_1,
    back_no_2: row.back_no_2,
    back_no_3: row.back_no_3,
    barcode_no: row.barcode_no,
  }
}
