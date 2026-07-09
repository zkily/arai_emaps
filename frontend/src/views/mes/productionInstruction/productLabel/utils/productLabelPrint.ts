import QRCode from 'qrcode'
import { buildPrintHtmlDocument, escapeHtml, openPrintWindow } from '@/utils/printWindow'
import type { ProductLabelPreview } from '@/api/mes/productLabel'

export interface ProductLabelPrintInput {
  product_cd?: string
  label_product_name: string
  process_unit_qty: number | null
  remark?: string | null
  product_name_color: string
  route_description?: string
  top_row: {
    machine_1: string
    machine_2: string
    machine_3: string
    machine_4_fixed: string
  }
  process_slots: (string | null)[]
}

export interface ProductLabelPrintOptions {
  pages?: number
  copiesPerPage?: number
  /** 各ラベル左上に赤丸「初」マークを印字 */
  showInitialMark?: boolean
}

const PRINT_COLUMNS = 4
const TENAOSHI = '手直し'

/** A4 2列×3行：ラベル実線枠 + ラベル間虚線裁切線、裁断後中央揃え */
/** ページ外枠・ラベル間隔の追加分（96dpi px → mm、累計） */
const EXTRA_MARGIN_PX = 6
const EXTRA_MARGIN_MM = (EXTRA_MARGIN_PX / 96) * 25.4
const BASE_GUTTER_MM = 8
const BASE_PAGE_MARGIN_MM = 4
const GUTTER_MM = BASE_GUTTER_MM + EXTRA_MARGIN_MM
const PAGE_MARGIN_MM = BASE_PAGE_MARGIN_MM + EXTRA_MARGIN_MM
const A4_WIDTH_MM = 210
const A4_HEIGHT_MM = 297
const LABEL_COLS = 2
const LABEL_ROWS = 3
const LABEL_INNER_PAD_MM = 3
/** 横: P + W + G + W + P = 210 */
const LABEL_WIDTH_MM = (A4_WIDTH_MM - PAGE_MARGIN_MM * 2 - GUTTER_MM) / LABEL_COLS
/** 縦: P + H + G + H + G + H + P = 297 */
const LABEL_HEIGHT_MM =
  (A4_HEIGHT_MM - PAGE_MARGIN_MM * 2 - GUTTER_MM * (LABEL_ROWS - 1)) / LABEL_ROWS
const SHEET_WIDTH_MM = A4_WIDTH_MM - PAGE_MARGIN_MM * 2
const SHEET_HEIGHT_MM = A4_HEIGHT_MM - PAGE_MARGIN_MM * 2
const CUT_V_LEFT_MM = LABEL_WIDTH_MM + GUTTER_MM / 2
const CUT_H1_TOP_MM = LABEL_HEIGHT_MM + GUTTER_MM / 2
const CUT_H2_TOP_MM = LABEL_HEIGHT_MM * 2 + GUTTER_MM + GUTTER_MM / 2
const LABEL_MARK_SIZE_MM = 13 * 0.8
const LABEL_QR_SIZE_MM = LABEL_MARK_SIZE_MM * 0.85
const LABEL_QR_PX = Math.round(96 * 0.8 * 0.85)
const LABEL_PRODUCT_FONT_MAX = 50
const LABEL_PRODUCT_FONT_MIN = 14
const LABEL_PRODUCT_ROW_HEIGHT_PX = 55
const LABEL_PRODUCT_LINE_HEIGHT_SINGLE = 1.1
const LABEL_PRODUCT_LINE_HEIGHT_MULTI = 1.15
const LABEL_PRODUCT_SINGLE_LINE_FONT_MAX = Math.min(
  LABEL_PRODUCT_FONT_MAX,
  Math.floor(LABEL_PRODUCT_ROW_HEIGHT_PX / LABEL_PRODUCT_LINE_HEIGHT_SINGLE)
)
const LABEL_PRODUCT_MULTILINE_FONT_MAX = Math.min(
  LABEL_PRODUCT_FONT_MAX,
  Math.floor(LABEL_PRODUCT_ROW_HEIGHT_PX / (LABEL_PRODUCT_LINE_HEIGHT_MULTI * 2))
)
const LABEL_PRODUCT_INNER_WIDTH_PX =
  (LABEL_WIDTH_MM - LABEL_INNER_PAD_MM * 2) * (96 / 25.4)
const LABEL_PRODUCT_FONT_FAMILY =
  "'Yu Gothic UI', 'Yu Gothic', 'MS Gothic', 'Hiragino Sans', sans-serif"
/** canvas未使用時の概算係数 */
const LABEL_PRODUCT_CHAR_WIDTH_RATIO = 0.58
const LABEL_PRODUCT_WIDTH_FILL = 0.98
const LABEL_PRODUCT_MIN_FIT_FONT = 10

let measureCanvas: HTMLCanvasElement | null = null

function getMeasureContext(): CanvasRenderingContext2D | null {
  if (typeof document === 'undefined') {
    return null
  }
  if (!measureCanvas) {
    measureCanvas = document.createElement('canvas')
  }
  return measureCanvas.getContext('2d')
}

function measureProductNameWidthPx(text: string, fontSize: number): number {
  const ctx = getMeasureContext()
  if (!ctx) {
    return measureProductNameUnits(text) * fontSize * LABEL_PRODUCT_CHAR_WIDTH_RATIO
  }
  ctx.font = `800 ${fontSize}px ${LABEL_PRODUCT_FONT_FAMILY}`
  return ctx.measureText(text).width
}

function countWrappedLines(text: string, fontSize: number, maxWidth: number): number {
  const ctx = getMeasureContext()
  if (!ctx) {
    const units = measureProductNameUnits(text)
    const lineCapacity = maxWidth / (fontSize * LABEL_PRODUCT_CHAR_WIDTH_RATIO)
    return Math.ceil(units / lineCapacity)
  }
  ctx.font = `800 ${fontSize}px ${LABEL_PRODUCT_FONT_FAMILY}`
  let lines = 1
  let lineWidth = 0
  for (const ch of text) {
    const chWidth = ctx.measureText(ch).width
    if (lineWidth > 0 && lineWidth + chWidth > maxWidth) {
      lines += 1
      lineWidth = chWidth
    } else {
      lineWidth += chWidth
    }
  }
  return lines
}

/** 製品名の表示幅を全角1文字=1単位で概算（canvas不可時のフォールバック） */
function measureProductNameUnits(text: string): number {
  let units = 0
  for (const ch of text) {
    const code = ch.charCodeAt(0)
    if (code <= 0x007f) {
      units += 0.5
    } else if (ch === ' ' || ch === '\u3000') {
      units += 0.32
    } else {
      units += 1
    }
  }
  return Math.max(units, 1)
}

function textBlockHeight(fontSize: number, lines: number): number {
  const lineHeight =
    lines === 1 ? LABEL_PRODUCT_LINE_HEIGHT_SINGLE : LABEL_PRODUCT_LINE_HEIGHT_MULTI
  return fontSize * lineHeight * lines
}

function productNameFitsInLinesFallback(
  units: number,
  fontSize: number,
  lines: 1 | 2,
  innerWidthPx: number
): boolean {
  if (textBlockHeight(fontSize, lines) > LABEL_PRODUCT_ROW_HEIGHT_PX) {
    return false
  }
  const maxWidth = innerWidthPx * LABEL_PRODUCT_WIDTH_FILL
  const capacity = maxWidth / (fontSize * LABEL_PRODUCT_CHAR_WIDTH_RATIO)
  if (lines === 1) {
    return units <= capacity
  }
  const maxLineUnits = Math.ceil(units / 2)
  return maxLineUnits <= capacity && units <= capacity * 2
}

/** 行幅いっぱいに収まる最大フォントサイズを算出（最大2行） */
export function resolveLabelProductFontSize(rawName: string): {
  fontSize: number
  multiline: boolean
} {
  const text = (rawName || '').trim()
  if (!text) {
    return { fontSize: LABEL_PRODUCT_FONT_MAX, multiline: false }
  }

  const innerWidthPx = LABEL_PRODUCT_INNER_WIDTH_PX
  const maxWidth = innerWidthPx * LABEL_PRODUCT_WIDTH_FILL
  const units = measureProductNameUnits(text)
  const canMeasure = getMeasureContext() != null

  for (let size = LABEL_PRODUCT_SINGLE_LINE_FONT_MAX; size >= LABEL_PRODUCT_FONT_MIN; size -= 1) {
    const fits = canMeasure
      ? measureProductNameWidthPx(text, size) <= maxWidth
      : productNameFitsInLinesFallback(units, size, 1, innerWidthPx)
    if (fits) {
      return { fontSize: size, multiline: false }
    }
  }

  for (let size = LABEL_PRODUCT_MULTILINE_FONT_MAX; size >= LABEL_PRODUCT_MIN_FIT_FONT; size -= 1) {
    const lines = canMeasure ? countWrappedLines(text, size, maxWidth) : 2
    const fitsHeight = textBlockHeight(size, Math.min(lines, 2)) <= LABEL_PRODUCT_ROW_HEIGHT_PX
    const fitsWidth = canMeasure
      ? lines <= 2
      : productNameFitsInLinesFallback(units, size, 2, innerWidthPx)
    if (fitsHeight && fitsWidth) {
      return { fontSize: size, multiline: true }
    }
  }

  const fontSize = Math.max(
    LABEL_PRODUCT_MIN_FIT_FONT,
    Math.floor((maxWidth * 2) / (units * LABEL_PRODUCT_CHAR_WIDTH_RATIO))
  )
  return { fontSize, multiline: true }
}

/** 8枠データを正規化 */
export function normalizePrintSlots(slots?: (string | null)[] | null): (string | null)[] {
  const result: (string | null)[] = []
  for (let i = 0; i < 8; i++) {
    const v = slots?.[i]
    result.push(v != null && String(v).trim() ? String(v).trim() : null)
  }
  return result
}

/**
 * 参考レイアウトに合わせた印刷用グリッド
 * 上段：枠1〜3（成型設備）＋空欄
 * 下段：枠5（空欄可）｜枠4（手直し）｜枠5〜8の後工程（右寄せ・末尾2件を表示）
 */
export function buildPrintGridFromSlots(slots?: (string | null)[] | null): {
  topRow: string[]
  bottomRow: string[]
} {
  const s = normalizePrintSlots(slots)

  const topRow = [s[0] || '', s[1] || '', s[2] || '', '']

  const postMolding = s.slice(4, 8).filter((v) => v)
  const postTail = postMolding.slice(-2)

  const bottomRow = [
    s[4] || '',
    s[3] || TENAOSHI,
    postTail[0] || '',
    postTail[1] || '',
  ]

  return { topRow, bottomRow }
}

function buildGridCell(text: string): string {
  const label = escapeHtml(text || '')
  return `<td><div class="cell-header">${label}</div><div class="cell-body"></div></td>`
}

async function buildProductCdQrDataUrl(productCd?: string): Promise<string> {
  const cd = (productCd || '').trim()
  if (!cd) return ''
  try {
    return await QRCode.toDataURL(cd, {
      width: LABEL_QR_PX,
      margin: 0,
      errorCorrectionLevel: 'M',
    })
  } catch {
    return ''
  }
}

function buildOneLabelHtml(data: ProductLabelPrintInput, qrDataUrl = '', showInitialMark = false): string {
  const nameColor = escapeHtml(data.product_name_color || '#000000')
  const rawProductName = (data.label_product_name || '').trim()
  const { fontSize: productNameFontSize, multiline: productNameMultiline } =
    resolveLabelProductFontSize(rawProductName)
  const productName = escapeHtml(rawProductName)
  const productNameClass = productNameMultiline ? 'label-product is-multiline' : 'label-product'
  const productNameLineHeight = productNameMultiline
    ? LABEL_PRODUCT_LINE_HEIGHT_MULTI
    : LABEL_PRODUCT_LINE_HEIGHT_SINGLE
  const qty =
    data.process_unit_qty != null && data.process_unit_qty !== ('' as unknown as number)
      ? escapeHtml(String(data.process_unit_qty))
      : ''
  const remarkRaw = (data.remark || '').trim()
  const remarkHtml = remarkRaw
    ? `<div class="label-remark">${escapeHtml(remarkRaw)}</div>`
    : ''
  const bodyClass = remarkRaw ? 'label-body has-remark' : 'label-body'
  const routeLine = (data.route_description || '').trim()
    ? `<div class="label-route-line"><span class="label-route-label">工程ルート:</span>${escapeHtml((data.route_description || '').trim())}</div>`
    : ''

  const { topRow, bottomRow } = buildPrintGridFromSlots(data.process_slots)

  const topRowHtml = topRow.map((cell) => buildGridCell(cell)).join('')
  const bottomRowHtml = bottomRow.map((cell) => buildGridCell(cell)).join('')

  const qrHtml = qrDataUrl
    ? `<div class="label-qr"><img src="${qrDataUrl}" alt="製品CD QR" /></div>`
    : ''

  const initialMarkHtml = showInitialMark
    ? '<div class="label-initial-mark" aria-hidden="true">初</div>'
    : ''

  const cardClass = showInitialMark ? 'label-card has-initial-mark' : 'label-card'

  return `
    <div class="${cardClass}">
      ${initialMarkHtml}
      <div class="label-title-row">
        <div class="label-title">現品票</div>
        ${qrHtml}
      </div>
      <div class="label-product-row">
        <div class="${productNameClass}" style="color:${nameColor};font-size:${productNameFontSize}px;line-height:${productNameLineHeight}">${productName}</div>
      </div>
      <div class="${bodyClass}">
        ${remarkHtml}
        <div class="label-qty">
          <span class="label-qty-lbl">入数</span>
          <span class="label-qty-val">${qty}</span>
        </div>
      </div>
      <table class="route-grid">
        <tr class="route-row-top">${topRowHtml}</tr>
        <tr class="route-row-bottom">${bottomRowHtml}</tr>
      </table>
      ${routeLine}
    </div>
  `
}

function buildSheetCutGuidesHtml(): string {
  return `
    <div class="cut-guide cut-guide-v" aria-hidden="true"></div>
    <div class="cut-guide cut-guide-h cut-guide-h-1" aria-hidden="true"></div>
    <div class="cut-guide cut-guide-h cut-guide-h-2" aria-hidden="true"></div>
  `
}

const PRINT_STYLES = `
  @page { size: A4 portrait; margin: ${PAGE_MARGIN_MM}mm; }
  * { box-sizing: border-box; }
  html, body {
    margin: 0;
    padding: 0;
    font-family: 'Yu Gothic UI', 'Yu Gothic', 'MS Gothic', 'Hiragino Sans', sans-serif;
  }
  .sheet {
    position: relative;
    width: ${SHEET_WIDTH_MM}mm;
    height: ${SHEET_HEIGHT_MM}mm;
    display: grid;
    grid-template-columns: repeat(${LABEL_COLS}, ${LABEL_WIDTH_MM}mm);
    grid-template-rows: repeat(${LABEL_ROWS}, ${LABEL_HEIGHT_MM}mm);
    gap: ${GUTTER_MM}mm;
    page-break-after: always;
    page-break-inside: avoid;
  }
  .sheet:last-child { page-break-after: auto; }
  .cut-guide {
    position: absolute;
    pointer-events: none;
    z-index: 2;
  }
  .cut-guide-v {
    top: 0;
    bottom: 0;
    left: ${CUT_V_LEFT_MM}mm;
    width: 0;
    border-left: 0.6pt dashed #888;
  }
  .cut-guide-h {
    left: 0;
    right: 0;
    height: 0;
    border-top: 0.6pt dashed #888;
  }
  .cut-guide-h-1 { top: ${CUT_H1_TOP_MM}mm; }
  .cut-guide-h-2 { top: ${CUT_H2_TOP_MM}mm; }
  .label-card {
    position: relative;
    width: 100%;
    height: 100%;
    border: 1pt solid #111;
    padding: ${LABEL_INNER_PAD_MM}mm;
    margin: 0;
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow: hidden;
    background: #fff;
  }
  .label-initial-mark {
    position: absolute;
    top: 0;
    left: 0;
    width: ${LABEL_MARK_SIZE_MM}mm;
    height: ${LABEL_MARK_SIZE_MM}mm;
    border: 1.2pt solid #cc0000;
    border-radius: 50%;
    color: #cc0000;
    font-size: 20px;
    font-weight: 800;
    display: flex;
    align-items: center;
    justify-content: center;
    line-height: 1;
    background: #fff;
    z-index: 2;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  .label-card.has-initial-mark .label-title-row {
    padding-left: ${LABEL_MARK_SIZE_MM + 1}mm;
  }
  .label-title-row {
    position: relative;
    flex-shrink: 0;
    min-height: 8mm;
    padding-right: ${LABEL_QR_SIZE_MM + 1}mm;
    margin-bottom: 2px;
  }
  .label-title {
    text-align: center;
    font-size: 18px;
    font-weight: 700;
    text-decoration: underline;
    text-underline-offset: 2px;
    border: none;
    padding: 2px 0 0;
    margin: 0;
    letter-spacing: 0.12em;
    line-height: 1.2;
    width: 100%;
  }
  .label-product-row {
    flex-shrink: 0;
    width: 100%;
    margin-bottom: 2px;
    height: ${LABEL_PRODUCT_ROW_HEIGHT_PX}px;
    min-height: ${LABEL_PRODUCT_ROW_HEIGHT_PX}px;
    max-height: ${LABEL_PRODUCT_ROW_HEIGHT_PX}px;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
  }
  .label-qr {
    position: absolute;
    top: 0;
    right: 0;
    width: ${LABEL_QR_SIZE_MM}mm;
    height: ${LABEL_QR_SIZE_MM}mm;
    line-height: 0;
  }
  .label-qr img {
    display: block;
    width: 100%;
    height: 100%;
    object-fit: contain;
  }
  .label-body {
    display: flex;
    align-items: flex-end;
    justify-content: flex-end;
    margin-bottom: 4px;
    flex-shrink: 0;
    gap: 6px;
    width: 100%;
  }
  .label-body.has-remark {
    justify-content: space-between;
  }
  .label-remark {
    flex: 1 1 auto;
    min-width: 0;
    font-size: 14px;
    font-weight: 700;
    color: #111;
    line-height: 1.2;
    text-align: left;
    word-break: break-word;
    overflow-wrap: anywhere;
    padding-bottom: 1px;
  }
  .label-product {
    font-family: ${LABEL_PRODUCT_FONT_FAMILY};
    font-size: ${LABEL_PRODUCT_FONT_MAX}px;
    font-weight: 800;
    line-height: ${LABEL_PRODUCT_LINE_HEIGHT_SINGLE};
    width: 100%;
    max-width: 100%;
    max-height: ${LABEL_PRODUCT_ROW_HEIGHT_PX}px;
    text-align: center;
    white-space: nowrap;
    word-break: normal;
    overflow-wrap: normal;
    letter-spacing: 0;
    overflow: hidden;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  .label-product.is-multiline {
    line-height: ${LABEL_PRODUCT_LINE_HEIGHT_MULTI};
    max-height: ${LABEL_PRODUCT_ROW_HEIGHT_PX}px;
    overflow: hidden;
    white-space: normal;
    word-break: break-all;
    overflow-wrap: break-word;
  }
  .label-qty {
    display: flex;
    align-items: baseline;
    gap: 5px;
    white-space: nowrap;
    flex-shrink: 0;
    padding-bottom: 1px;
  }
  .label-route-line {
    width: 100%;
    text-align: left;
    font-size: 11px;
    font-weight: 700;
    color: #111;
    line-height: 1.2;
    word-break: break-word;
    flex-shrink: 0;
    margin-top: 2px;
    padding-top: 2px;
  }
  .label-route-label {
    margin-right: 4px;
    white-space: nowrap;
  }
  .label-qty-lbl {
    font-size: 20px;
    font-weight: 700;
    color: #111;
  }
  .label-qty-val {
    font-size: 20px;
    font-weight: 800;
    color: #111;
    line-height: 1;
  }
  .route-grid {
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
    margin-top: auto;
    border-top: 1px solid #111;
    border-bottom: 1px solid #111;
    flex: 1 1 auto;
    min-height: 0;
  }
  .route-grid td {
    border-left: 1px dotted #444;
    vertical-align: top;
    padding: 0;
    height: 50%;
  }
  .route-grid td:first-child { border-left: none; }
  .cell-header {
    text-align: center;
    font-size: 13px;
    font-weight: 700;
    padding: 2px 2px 3px;
    line-height: 1.2;
    min-height: 4.5mm;
    word-break: break-word;
    color: #111;
  }
  .cell-body {
    min-height: 8mm;
    border-top: none;
  }
  .route-row-top td {
    border-bottom: 1px solid #111;
  }
  .route-row-top .cell-header {
    font-size: 14px;
  }
  .route-row-bottom .cell-header {
    font-size: 13px;
  }
  @media print {
    .label-product-row {
      height: ${LABEL_PRODUCT_ROW_HEIGHT_PX}px !important;
      min-height: ${LABEL_PRODUCT_ROW_HEIGHT_PX}px !important;
      max-height: ${LABEL_PRODUCT_ROW_HEIGHT_PX}px !important;
    }
    .label-product {
      -webkit-print-color-adjust: exact !important;
      print-color-adjust: exact !important;
    }
    .label-qr img {
      -webkit-print-color-adjust: exact !important;
      print-color-adjust: exact !important;
    }
    .label-initial-mark {
      border-color: #cc0000 !important;
      color: #cc0000 !important;
      -webkit-print-color-adjust: exact !important;
      print-color-adjust: exact !important;
    }
    .label-card {
      border: 1pt solid #111 !important;
      width: 100% !important;
      height: 100% !important;
      padding: ${LABEL_INNER_PAD_MM}mm !important;
    }
    .route-grid {
      border-top: 1px solid #111 !important;
      border-bottom: 1px solid #111 !important;
    }
    .cut-guide-v {
      border-left: 0.6pt dashed #888 !important;
    }
    .cut-guide-h {
      border-top: 0.6pt dashed #888 !important;
    }
    .sheet {
      width: ${SHEET_WIDTH_MM}mm !important;
      height: ${SHEET_HEIGHT_MM}mm !important;
      gap: ${GUTTER_MM}mm !important;
    }
  }
`

export async function buildProductLabelPrintHtml(
  data: ProductLabelPrintInput,
  options: ProductLabelPrintOptions = {}
): Promise<string> {
  const pages = Math.max(1, options.pages ?? 1)
  const copiesPerPage = options.copiesPerPage ?? 6
  const showInitialMark = !!options.showInitialMark
  const qrDataUrl = await buildProductCdQrDataUrl(data.product_cd)
  const oneLabel = buildOneLabelHtml(data, qrDataUrl, showInitialMark)
  const labelsOnPage = Array.from({ length: copiesPerPage }, () => oneLabel).join('')
  const cutGuides = buildSheetCutGuidesHtml()
  const sheets = Array.from(
    { length: pages },
    () => `<div class="sheet">${labelsOnPage}${cutGuides}</div>`
  ).join('')
  return buildPrintHtmlDocument('現品票', PRINT_STYLES, sheets)
}

export async function printProductLabels(
  data: ProductLabelPrintInput,
  options: ProductLabelPrintOptions = {}
): Promise<void> {
  const html = await buildProductLabelPrintHtml(data, options)
  openPrintWindow(html, { autoPrint: true, autoClose: true, delayMs: 400 })
}

export function previewFromApiData(preview: ProductLabelPreview): ProductLabelPrintInput {
  return {
    product_cd: preview.product_cd,
    label_product_name: preview.label_product_name,
    process_unit_qty: preview.process_unit_qty,
    remark: preview.remark ?? null,
    product_name_color: preview.product_name_color || '#000000',
    route_description: preview.route_description || '',
    top_row: preview.top_row,
    process_slots: [...(preview.process_slots || [])],
  }
}
