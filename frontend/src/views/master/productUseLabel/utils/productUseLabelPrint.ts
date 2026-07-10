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

/**
 * B4 ページ外枠余白（mm）。@page margin は 0、.pul-sheet padding で制御。
 * ラベル間隔 GUTTER：裁断虚線は中央 → 裁断後ラベル外周余白 = LABEL_MARGIN_MM
 */
const PAGE_MARGIN_MM = 5
const PAGE_MARGIN_LEFT_MM = Number((PAGE_MARGIN_MM + 0.1).toFixed(1))
const LABEL_MARGIN_MM = 3
const GUTTER_MM = LABEL_MARGIN_MM * 2
/** ラベル枠線：外枠 1pt / 内部区切り 0.8pt（外枠は .pul-label-frame 実 DOM） */
const LABEL_INNER_BORDER_PT = 0.8
const LABEL_OUTER_BORDER_PT = 1
const LABEL_BORDER_COLOR = '#111'
const LABEL_INNER_BORDER_CSS = `${LABEL_INNER_BORDER_PT}pt solid ${LABEL_BORDER_COLOR}`
/** 印刷向け外枠（実 DOM・四辺を 1pt 塗りつぶし） */
const LABEL_FRAME_HTML =
  '<div class="pul-label-frame" aria-hidden="true">' +
  '<span class="pul-label-frame-edge pul-label-frame-edge--t"></span>' +
  '<span class="pul-label-frame-edge pul-label-frame-edge--r"></span>' +
  '<span class="pul-label-frame-edge pul-label-frame-edge--b"></span>' +
  '<span class="pul-label-frame-edge pul-label-frame-edge--l"></span>' +
  '</div>'
/** B4 用紙（横向：364×257mm） */
const B4_WIDTH_MM = 364
const B4_HEIGHT_MM = 257
const INNER_WIDTH_MM = B4_WIDTH_MM - PAGE_MARGIN_LEFT_MM - PAGE_MARGIN_MM
const INNER_HEIGHT_MM = B4_HEIGHT_MM - PAGE_MARGIN_MM * 2

const STANDARD_COLS = 5
const STANDARD_ROWS = 4
const INOAC_COLS = 4
const INOAC_KV_ROW_EXTRA_PX = 3
const INOAC_HIST_BLANK_EXTRA_PX = 25
const INOAC_HEAD_BODY_ROW_EXTRA_PX = 20
/** 加工履歴上部に溜まっていた余白を QR 行へ寄せる（ラベル高さに対する比率） */
const INOAC_HEAD_BODY_ABSORB_RATIO = 0.11
/** INOAC 品名（製品用製品名）：基準30px・1行内で自動縮小 */
const INOAC_PRODUCT_FONT_BASE = 30
const INOAC_PRODUCT_FONT_MIN = 8
const INOAC_PRODUCT_NAME_COL_RATIO = 0.5
const INOAC_PRODUCT_CELL_PAD_H_MM = 0.3
const INOAC_PRODUCT_LINE_HEIGHT = 1.1
const INOAC_PRODUCT_LINE_HEIGHT_TRIM_PX = 1
const INOAC_PRODUCT_WIDTH_FILL = 0.96
const INOAC_ROWS = 4

/** 標準ラベル（4×5）1枚の高さ mm */
const STD_LABEL_HEIGHT_MM =
  (INNER_HEIGHT_MM - GUTTER_MM * (STANDARD_ROWS - 1)) / STANDARD_ROWS
/** 標準ラベル行高：上半区66%・下半区34% */
const STD_UPPER_ROW_MM = Number(((STD_LABEL_HEIGHT_MM * 0.66) / 2).toFixed(2))
const STD_LOWER_PAIR_MM = Number((STD_LABEL_HEIGHT_MM * 0.34).toFixed(2))
/** 下半区内：入数44% / メーカー56%（两行厂商名不被裁切） */
const STD_QTY_ROW_MM = Number((STD_LOWER_PAIR_MM * 0.44).toFixed(2))
const STD_MFG_ROW_MM = Number((STD_LOWER_PAIR_MM - STD_QTY_ROW_MM).toFixed(2))
const STD_TOP_ROW_MM = STD_UPPER_ROW_MM
const STD_TOP_HALF_ROW_MM = Number((STD_TOP_ROW_MM / 2).toFixed(2))
const STD_NAME_ROW_MM = STD_UPPER_ROW_MM
const STD_STAMP_CELL_MM = Number((STD_QTY_ROW_MM + STD_MFG_ROW_MM).toFixed(2))
/** メーカー行：标题・内容上余白（mm） */
const STD_MFG_LBL_PADDING_TOP_MM = 2.5
const STD_MFG_INNER_PADDING_TOP_MM = 0.5
const STD_MFG_INNER_PADDING_BOTTOM_MM = 0.2

const FONT =
  "'Yu Gothic UI', 'Yu Gothic', 'MS Gothic', 'Hiragino Sans', sans-serif"

/** QRコード表示サイズ（基準14mm × 0.8 × 0.9 = 10.08mm、正方形） */
const QR_SIZE_SCALE = 0.72
const STD_QR_SIZE_MM = Number((14 * QR_SIZE_SCALE).toFixed(2))
const INOAC_QR_SIZE_MM = Number((14 * QR_SIZE_SCALE).toFixed(2))

function qrRenderPx(sizeMm: number): number {
  return Math.round((sizeMm / 25.4) * 96)
}
/** 品名（製品用製品名）フォント：基準30px・行高固定内で長さに応じて縮小 */
const STD_PRODUCT_LBL_COL_MM = 12
const STD_PRODUCT_CELL_PAD_H_MM = 1.2
const STD_PRODUCT_FONT_MAX = 30
const STD_PRODUCT_FONT_MIN = 10
const STD_PRODUCT_FONT_MIN_FIT = 8
const STD_PRODUCT_LINE_HEIGHT_SINGLE = 1.05
const STD_PRODUCT_LINE_HEIGHT_MULTI = 1.1
const STD_PRODUCT_LINE_HEIGHT_TRIM_PX = 2
/** 背番/品番（上下分割）行高 */
const STD_TOP_SPLIT_LINE_HEIGHT_BACK = 1.2
const STD_TOP_SPLIT_LINE_HEIGHT_PART = 1.1
const STD_TOP_SPLIT_LINE_HEIGHT_TRIM_PX = 1
/** 入数行 */
const STD_QTY_LINE_HEIGHT = 1.2
const STD_QTY_LINE_HEIGHT_TRIM_PX = 2
/** メーカー行 */
const STD_MFG_LINE_HEIGHT = 1.2
const STD_MFG_LBL_LINE_HEIGHT = 1.25
const STD_MFG_LINE_HEIGHT_ADD_PX = 2
const STD_PRODUCT_CHAR_WIDTH_RATIO = 0.58
const STD_PRODUCT_WIDTH_FILL = 0.98

let pulMeasureCanvas: HTMLCanvasElement | null = null

function getPulMeasureContext(): CanvasRenderingContext2D | null {
  if (typeof document === 'undefined') {
    return null
  }
  if (!pulMeasureCanvas) {
    pulMeasureCanvas = document.createElement('canvas')
  }
  return pulMeasureCanvas.getContext('2d')
}

function measurePulProductNameUnits(text: string): number {
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

function stdProductNameInnerWidthPx(labelWidthMm: number): number {
  const innerMm =
    labelWidthMm - STD_PRODUCT_LBL_COL_MM - STD_PRODUCT_CELL_PAD_H_MM * 2
  return Math.max(innerMm, 1) * (96 / 25.4)
}

function stdProductNameRowHeightPx(): number {
  return STD_NAME_ROW_MM * (96 / 25.4)
}

function measurePulProductNameWidthPx(text: string, fontSize: number): number {
  const ctx = getPulMeasureContext()
  if (!ctx) {
    return measurePulProductNameUnits(text) * fontSize * STD_PRODUCT_CHAR_WIDTH_RATIO
  }
  ctx.font = `800 ${fontSize}px ${FONT}`
  return ctx.measureText(text).width
}

function countPulProductNameLines(text: string, fontSize: number, maxWidth: number): number {
  const ctx = getPulMeasureContext()
  if (!ctx) {
    const units = measurePulProductNameUnits(text)
    const lineCapacity = maxWidth / (fontSize * STD_PRODUCT_CHAR_WIDTH_RATIO)
    return Math.ceil(units / lineCapacity)
  }
  ctx.font = `800 ${fontSize}px ${FONT}`
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

function pulProductTextHeightPx(fontSize: number, lines: number): number {
  const lineHeight =
    lines === 1 ? STD_PRODUCT_LINE_HEIGHT_SINGLE : STD_PRODUCT_LINE_HEIGHT_MULTI
  const lineHeightPx = fontSize * lineHeight - STD_PRODUCT_LINE_HEIGHT_TRIM_PX
  return lineHeightPx * lines
}

function formatStdProductLineHeightCss(lhRatio: number): string {
  return `calc(${lhRatio}em - ${STD_PRODUCT_LINE_HEIGHT_TRIM_PX}px)`
}

function pulProductNameFitsFallback(
  units: number,
  fontSize: number,
  lines: 1 | 2,
  innerWidthPx: number
): boolean {
  const rowHeightPx = stdProductNameRowHeightPx()
  if (pulProductTextHeightPx(fontSize, lines) > rowHeightPx) {
    return false
  }
  const maxWidth = innerWidthPx * STD_PRODUCT_WIDTH_FILL
  const capacity = maxWidth / (fontSize * STD_PRODUCT_CHAR_WIDTH_RATIO)
  if (lines === 1) {
    return units <= capacity
  }
  const maxLineUnits = Math.ceil(units / 2)
  return maxLineUnits <= capacity && units <= capacity * 2
}

function resolveStdProductNameFontSize(
  rawName: string,
  labelWidthMm: number
): { fontSize: number; multiline: boolean; lineHeight: number } {
  const text = (rawName || '').trim()
  const rowHeightPx = stdProductNameRowHeightPx()
  const singleLineFontMax = Math.min(
    STD_PRODUCT_FONT_MAX,
    Math.floor(
      (rowHeightPx + STD_PRODUCT_LINE_HEIGHT_TRIM_PX) / STD_PRODUCT_LINE_HEIGHT_SINGLE
    )
  )
  const multilineFontMax = Math.min(
    STD_PRODUCT_FONT_MAX,
    Math.floor(
      (rowHeightPx / 2 + STD_PRODUCT_LINE_HEIGHT_TRIM_PX) / STD_PRODUCT_LINE_HEIGHT_MULTI
    )
  )

  if (!text) {
    return {
      fontSize: STD_PRODUCT_FONT_MAX,
      multiline: false,
      lineHeight: STD_PRODUCT_LINE_HEIGHT_SINGLE,
    }
  }

  const innerWidthPx = stdProductNameInnerWidthPx(labelWidthMm)
  const maxWidth = innerWidthPx * STD_PRODUCT_WIDTH_FILL
  const units = measurePulProductNameUnits(text)
  const canMeasure = getPulMeasureContext() != null

  for (let size = singleLineFontMax; size >= STD_PRODUCT_FONT_MIN; size -= 1) {
    const fitsWidth = canMeasure
      ? measurePulProductNameWidthPx(text, size) <= maxWidth
      : pulProductNameFitsFallback(units, size, 1, innerWidthPx)
    const fitsHeight = pulProductTextHeightPx(size, 1) <= rowHeightPx
    if (fitsWidth && fitsHeight) {
      return { fontSize: size, multiline: false, lineHeight: STD_PRODUCT_LINE_HEIGHT_SINGLE }
    }
  }

  for (let size = multilineFontMax; size >= STD_PRODUCT_FONT_MIN_FIT; size -= 1) {
    const lines = canMeasure ? countPulProductNameLines(text, size, maxWidth) : 2
    const lineCount = Math.min(lines, 2)
    const fitsHeight = pulProductTextHeightPx(size, lineCount) <= rowHeightPx
    const fitsWidth = canMeasure
      ? lineCount <= 2
      : pulProductNameFitsFallback(units, size, 2, innerWidthPx)
    if (fitsHeight && fitsWidth) {
      return { fontSize: size, multiline: true, lineHeight: STD_PRODUCT_LINE_HEIGHT_MULTI }
    }
  }

  const fontSize = Math.max(
    STD_PRODUCT_FONT_MIN_FIT,
    Math.floor((maxWidth * 2) / (units * STD_PRODUCT_CHAR_WIDTH_RATIO))
  )
  return { fontSize, multiline: true, lineHeight: STD_PRODUCT_LINE_HEIGHT_MULTI }
}

function inoacProductNameInnerWidthPx(labelWidthMm: number): number {
  const innerMm =
    labelWidthMm * INOAC_PRODUCT_NAME_COL_RATIO - INOAC_PRODUCT_CELL_PAD_H_MM * 2
  return Math.max(innerMm, 1) * (96 / 25.4)
}

function inoacHeadBodyRowHeightPx(labelHeightMm: number): number {
  const absorbMm = labelHeightMm * INOAC_HEAD_BODY_ABSORB_RATIO
  const bodyMm = INOAC_QR_SIZE_MM + absorbMm
  return bodyMm * (96 / 25.4) + INOAC_HEAD_BODY_ROW_EXTRA_PX
}

function inoacProductTextHeightPx(fontSize: number): number {
  return fontSize * INOAC_PRODUCT_LINE_HEIGHT - INOAC_PRODUCT_LINE_HEIGHT_TRIM_PX
}

function formatInoacProductLineHeightCss(lhRatio: number): string {
  return `calc(${lhRatio}em - ${INOAC_PRODUCT_LINE_HEIGHT_TRIM_PX}px)`
}

function resolveInoacProductNameFontSize(
  rawName: string,
  labelWidthMm: number,
  labelHeightMm: number
): { fontSize: number; lineHeight: number } {
  const text = (rawName || '').trim()
  const rowHeightPx = inoacHeadBodyRowHeightPx(labelHeightMm)
  const usableHeightPx = Math.max(rowHeightPx - INOAC_HEAD_BODY_ROW_EXTRA_PX, 1)
  const singleLineFontMax = Math.min(
    INOAC_PRODUCT_FONT_BASE,
    Math.floor(
      (usableHeightPx + INOAC_PRODUCT_LINE_HEIGHT_TRIM_PX) / INOAC_PRODUCT_LINE_HEIGHT
    )
  )

  if (!text) {
    return { fontSize: INOAC_PRODUCT_FONT_BASE, lineHeight: INOAC_PRODUCT_LINE_HEIGHT }
  }

  const innerWidthPx = inoacProductNameInnerWidthPx(labelWidthMm)
  const maxWidth = innerWidthPx * INOAC_PRODUCT_WIDTH_FILL
  const units = measurePulProductNameUnits(text)
  const canMeasure = getPulMeasureContext() != null

  for (let size = singleLineFontMax; size >= INOAC_PRODUCT_FONT_MIN; size -= 1) {
    const fitsWidth = canMeasure
      ? measurePulProductNameWidthPx(text, size) <= maxWidth
      : units * size * STD_PRODUCT_CHAR_WIDTH_RATIO <= maxWidth
    const fitsHeight = inoacProductTextHeightPx(size) <= usableHeightPx
    if (fitsWidth && fitsHeight) {
      return { fontSize: size, lineHeight: INOAC_PRODUCT_LINE_HEIGHT }
    }
  }

  const fontSize = Math.max(
    INOAC_PRODUCT_FONT_MIN,
    Math.floor(maxWidth / (units * STD_PRODUCT_CHAR_WIDTH_RATIO))
  )
  return { fontSize, lineHeight: INOAC_PRODUCT_LINE_HEIGHT }
}

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

/** INOAC ラベル納入先表示：（株）東北INOAC小牛田 → 末尾に「工場」を付与 */
function formatInoacDestinationDisplay(destination?: string | null): string {
  const raw = (destination || '').trim()
  if (!raw) return ''
  const compact = raw.replace(/\s/g, '').replace(/　/g, '')
  const isKogata =
    compact.includes('東北INOAC小牛田') || compact.includes('東北イノアック小牛田')
  if (isKogata && !compact.endsWith('工場')) {
    return `${raw}工場`
  }
  return raw
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
    pageMarginLeftMm: PAGE_MARGIN_LEFT_MM,
    labelMarginMm: LABEL_MARGIN_MM,
    gutterMm: GUTTER_MM,
    innerWidthMm: INNER_WIDTH_MM,
    innerHeightMm: INNER_HEIGHT_MM,
    ...getLayout(inoac),
  }
}

function nameColor(hex?: string | null): string {
  const v = (hex || '#000000').trim()
  return /^#[0-9a-f]{3,8}$/i.test(v) ? v : '#000000'
}

/** QR用製品CD：末尾が「1」でなければ最終桁を「1」に置換（例: ABC123 → ABC121） */
function normalizeProductCdForQr(productCd?: string | null): string {
  const s = (productCd || '').trim()
  if (!s) return ''
  if (s.endsWith('1')) return s
  return s.slice(0, -1) + '1'
}

function resolveQrEncodeText(input: ProductUseLabelPrintInput): string {
  const normalizedCd = normalizeProductCdForQr(input.product_cd)
  if (normalizedCd) return normalizedCd
  return (input.part_no || '').trim()
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

/** Code 39（* 始止）— INOAC 背番バーコード用 */
const CODE39_PATTERNS: Record<string, string> = {
  '0': 'nnnwwnnnn',
  '1': 'wnnwnnnnw',
  '2': 'nnwwnnnnw',
  '3': 'wnnwwnnnn',
  '4': 'nnnwwnnnw',
  '5': 'wnnwwnnnn',
  '6': 'nnwwwnnnn',
  '7': 'nnnnwwnnw',
  '8': 'wnnnwwnnn',
  '9': 'nnwnwwnnn',
  A: 'wnnnnwnnw',
  B: 'nnwnnnwnw',
  C: 'wnwnnnwnn',
  D: 'nnnnwnwnw',
  E: 'wnnnwnnnn',
  F: 'nnnnnwwnw',
  G: 'nnnwnwnnw',
  H: 'wnnwnwnnn',
  I: 'nnwwnwnnn',
  J: 'nnnnwwnwn',
  K: 'wnnnnnwnw',
  L: 'nnwnnwwnn',
  M: 'wnwnnwwnn',
  N: 'nnnnnwwnn',
  O: 'wnnnnwnnn',
  P: 'nnwnnnwnn',
  Q: 'wnwnnnnnw',
  R: 'nnnnwnnnw',
  S: 'wnnwnnnnn',
  T: 'nnnwnnnnw',
  U: 'nnnnnnwwn',
  V: 'wnnnnnnwn',
  W: 'nnwnnnnwn',
  X: 'wnnnnnnwn',
  Y: 'wnnnnnwnn',
  Z: 'nnnnwnnwn',
  '-': 'nnnnnnwnn',
  '.': 'wnnnnnnwn',
  ' ': 'nnwnnnnwn',
  $: 'nnnwnnnwn',
  '/': 'nwnnnnwnn',
  '+': 'nnnnnwnwn',
  '%': 'nnnwnwnnn',
  '*': 'nwnnwnwnn',
}

function normalizeCode39Payload(raw?: string | null): string {
  let s = (raw || '').trim().toUpperCase()
  if (s.startsWith('*') && s.endsWith('*') && s.length >= 2) {
    s = s.slice(1, -1)
  }
  return s.replace(/[^0-9A-Z\-.\s$/+%]/g, '')
}

function formatCode39HumanReadable(payload: string): string {
  if (!payload) return ''
  return `* ${payload.split('').join(' ')} *`
}

function encodeCode39Modules(encoded: string): number[] {
  const modules: number[] = []
  const chars = encoded.toUpperCase().split('')
  chars.forEach((ch, idx) => {
    const pattern = CODE39_PATTERNS[ch]
    if (!pattern) return
    if (idx > 0) {
      modules.push(0)
    }
    let isBar = true
    for (const p of pattern) {
      const w = p === 'n' ? 1 : 3
      for (let i = 0; i < w; i++) {
        modules.push(isBar ? 1 : 0)
      }
      isBar = !isBar
    }
  })
  return modules
}

function generateCode39BarcodeSvg(
  raw: string | null | undefined,
  widthPx: number,
  barHeightPx: number
): { svg: string; humanReadable: string; payload: string } {
  const payload = normalizeCode39Payload(raw)
  if (!payload) {
    return { svg: '', humanReadable: '', payload: '' }
  }

  const encoded = `*${payload}*`
  const modules = encodeCode39Modules(encoded)
  if (!modules.length) {
    return { svg: '', humanReadable: '', payload }
  }

  const moduleW = Math.max(0.8, widthPx / modules.length)
  const viewW = modules.length * moduleW
  let x = 0
  const rects: string[] = []
  for (const mod of modules) {
    if (mod === 1) {
      rects.push(`<rect x="${x.toFixed(2)}" y="0" width="${moduleW.toFixed(2)}" height="${barHeightPx}" fill="#000"/>`)
    }
    x += moduleW
  }

  const svg =
    `<svg xmlns="http://www.w3.org/2000/svg" width="${widthPx}" height="${barHeightPx}" ` +
    `viewBox="0 0 ${viewW.toFixed(2)} ${barHeightPx}" preserveAspectRatio="none">${rects.join('')}</svg>`

  return { svg, humanReadable: formatCode39HumanReadable(payload), payload }
}

function inoacBarcodeDisplayText(input: ProductUseLabelPrintInput, payload: string): string {
  const back1 = (input.back_no_1 || '').trim()
  if (back1) return back1
  if (!payload) return ''
  if (payload.endsWith('I') && payload.length > 1) return payload.slice(0, -1)
  return payload
}


function hasBackNumberData(input: ProductUseLabelPrintInput): boolean {
  return [input.back_no_1, input.back_no_2, input.back_no_3].some(
    (v) => (v || '').trim() !== ''
  )
}

function buildStdTopRowHtml(
  input: ProductUseLabelPrintInput,
  qrCellHtml: string
): string {
  const back1 = escapeHtml((input.back_no_1 || '').trim())
  const back2 = escapeHtml((input.back_no_2 || '').trim())
  const back3 = escapeHtml((input.back_no_3 || '').trim())
  const partNo = escapeHtml((input.part_no || '').trim())

  if (!hasBackNumberData(input)) {
    return `<tr class="pul-std-row-top pul-std-row-top--part-only" style="height:${STD_TOP_ROW_MM}mm">
        <td class="pul-std-lbl">品番</td>
        <td class="pul-std-back pul-std-back--part-only">
          <div class="pul-back-part-val">${partNo || '&nbsp;'}</div>
        </td>
        ${qrCellHtml}
      </tr>`
  }

  const backValues = [back1, back2, back3].filter(Boolean).join('｜')
  return `<tr class="pul-std-row-top pul-std-row-top--dual" style="height:${STD_TOP_ROW_MM}mm">
        <td class="pul-std-lbl pul-std-lbl--split">
          <div class="pul-std-split-half">背番</div>
          <div class="pul-std-split-half">品番</div>
        </td>
        <td class="pul-std-back pul-std-back--split">
          <div class="pul-std-split-half pul-std-split-val">${backValues || '&nbsp;'}</div>
          <div class="pul-std-split-half pul-std-split-val">${partNo || '&nbsp;'}</div>
        </td>
        ${qrCellHtml}
      </tr>`
}


async function buildStandardLabelHtml(
  input: ProductUseLabelPrintInput,
  wMm: number,
  hMm: number
): Promise<string> {
  const qrPx = qrRenderPx(STD_QR_SIZE_MM)
  const qrSrc = await makeQrDataUrl(resolveQrEncodeText(input), qrPx)
  const pColor = nameColor(input.product_name_color)
  const rawProductName = (input.use_label_product_name || '').trim()
  const productName = escapeHtml(rawProductName)
  const { fontSize: productFontSize, multiline: productMultiline, lineHeight: productLh } =
    resolveStdProductNameFontSize(rawProductName, wMm)
  const productNameClass = productMultiline
    ? 'pul-std-product is-multiline'
    : 'pul-std-product'
  const productLineHeightCss = formatStdProductLineHeightCss(productLh)
  const qrCellHtml = `<td class="pul-std-qr">${qrSrc ? `<img src="${qrSrc}" alt="QR"/>` : ''}</td>`
  const topRowHtml = buildStdTopRowHtml(input, qrCellHtml)
  const qty = input.unit_qty != null ? escapeHtml(String(input.unit_qty)) : ''
  const mfg = DEFAULT_MANUFACTURER_LINES.map(
    (line) => `<div class="pul-mfg-line">${escapeHtml(line)}</div>`
  ).join('')

  return `<div class="pul-label pul-label--std">
    ${LABEL_FRAME_HTML}
    <table class="pul-std-table" cellspacing="0" cellpadding="0">
      ${topRowHtml}
      <tr class="pul-std-row-name" style="height:${STD_NAME_ROW_MM}mm">
        <td class="pul-std-lbl">品名</td>
        <td colspan="2" class="${productNameClass}" style="color:${pColor};font-size:${productFontSize}px;line-height:${productLineHeightCss}"><div class="pul-std-product-inner">${productName || '&nbsp;'}</div></td>
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
  const qrPx = qrRenderPx(INOAC_QR_SIZE_MM)
  const qrSrc = await makeQrDataUrl(normalizeProductCdForQr(input.product_cd), qrPx)
  const pColor = nameColor(input.product_name_color)
  const rawProductName = (input.use_label_product_name || '').trim()
  const productName = escapeHtml(rawProductName)
  const { fontSize: productFontSize, lineHeight: productLh } = resolveInoacProductNameFontSize(
    rawProductName,
    wMm,
    hMm
  )
  const productLineHeightCss = formatInoacProductLineHeightCss(productLh)
  const partNo = escapeHtml(input.part_no || '')
  const dest = escapeHtml(formatInoacDestinationDisplay(input.destination_name))
  const qtyNum = input.unit_qty != null ? escapeHtml(String(input.unit_qty)) : ''
  const qtyHtml = qtyNum
    ? `<span class="pul-inoac-qty-num">${qtyNum}</span><span class="pul-inoac-qty-unit">本</span>`
    : '&nbsp;'
  const mfgHtml = DEFAULT_MANUFACTURER_LINES.map(
    (line) => `<div class="pul-inoac-mfg-line">${escapeHtml(line)}</div>`
  ).join('')
  const barW = Math.round(((wMm * 0.22) / 25.4) * 96)
  const barH = Math.round(((hMm * 0.1) / 25.4) * 96)
  const barcodeData = generateCode39BarcodeSvg(input.barcode_no, barW, barH)
  const barcodeDisplay = escapeHtml(inoacBarcodeDisplayText(input, barcodeData.payload))
  const barcodeHuman = escapeHtml(barcodeData.humanReadable)

  const historyNumCells = [1, 2, 3, 4, 5]
    .map((n) => `<td class="pul-inoac-hist-num-cell">${n}</td>`)
    .join('')
  const historyBlankCells = [1, 2, 3, 4, 5]
    .map(() => `<td class="pul-inoac-hist-blank-cell">&nbsp;</td>`)
    .join('')

  return `<div class="pul-label pul-label--inoac">
    ${LABEL_FRAME_HTML}
    <table class="pul-inoac-table" cellspacing="0" cellpadding="0">
      <colgroup>
        <col style="width:14%" />
        <col style="width:36%" />
        <col style="width:14%" />
        <col style="width:36%" />
      </colgroup>
      <tr class="pul-inoac-head">
        <td colspan="4" class="pul-inoac-head-wrap">
          <table class="pul-inoac-head-table" cellspacing="0" cellpadding="0">
            <colgroup>
              <col style="width:22%" />
              <col style="width:50%" />
              <col style="width:28%" />
            </colgroup>
            <tr class="pul-inoac-head-lbl-row">
              <td class="pul-inoac-head-lbl-cell">工場用 QRコード</td>
              <td class="pul-inoac-head-lbl-cell">&lt; 品名 &gt;</td>
              <td class="pul-inoac-head-lbl-cell pul-inoac-head-lbl-cell--back">背番号 ${barcodeDisplay || '&nbsp;'}</td>
            </tr>
            <tr class="pul-inoac-head-body-row">
              <td class="pul-inoac-head-body-cell pul-inoac-head-body-cell--qr">
                <div class="pul-inoac-qr-wrap">${qrSrc ? `<img class="pul-inoac-qr" src="${qrSrc}" alt="QR"/>` : ''}</div>
              </td>
              <td class="pul-inoac-head-body-cell pul-inoac-head-body-cell--name">
                <div class="pul-inoac-product" style="color:${pColor};font-size:${productFontSize}px;line-height:${productLineHeightCss}">${productName || '&nbsp;'}</div>
              </td>
              <td class="pul-inoac-head-body-cell pul-inoac-head-body-cell--bar">
                <div class="pul-inoac-barcode">${barcodeData.svg}</div>
                <div class="pul-inoac-barcode-hr">${barcodeHuman || '&nbsp;'}</div>
              </td>
            </tr>
          </table>
        </td>
      </tr>
      <tr class="pul-inoac-row-part">
        <td class="pul-inoac-kv-lbl">品番</td>
        <td class="pul-inoac-kv-val pul-inoac-part-val">${partNo || '&nbsp;'}</td>
        <td class="pul-inoac-kv-lbl">収容数</td>
        <td class="pul-inoac-kv-val pul-inoac-qty-val">${qtyHtml}</td>
      </tr>
      <tr class="pul-inoac-row-dest">
        <td class="pul-inoac-kv-lbl">納入先</td>
        <td class="pul-inoac-kv-val pul-inoac-dest-val">${dest || '&nbsp;'}</td>
        <td class="pul-inoac-kv-lbl">メーカー</td>
        <td class="pul-inoac-kv-val pul-inoac-mfg-val">${mfgHtml || '&nbsp;'}</td>
      </tr>
      <tr class="pul-inoac-hist-block-row">
        <td colspan="4" class="pul-inoac-hist-block-wrap">
          <table class="pul-inoac-hist" cellspacing="0" cellpadding="0">
            <colgroup>
              <col style="width:20%" />
              <col style="width:20%" />
              <col style="width:20%" />
              <col style="width:20%" />
              <col style="width:20%" />
            </colgroup>
            <tr class="pul-inoac-hist-title-row">
              <td colspan="5" class="pul-inoac-hist-title-cell">&lt; 加工履歴 &gt;</td>
            </tr>
            <tr class="pul-inoac-hist-num-row">${historyNumCells}</tr>
            <tr class="pul-inoac-hist-blank-row">${historyBlankCells}</tr>
          </table>
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
  const inoacHeadBodyAbsorbMm = inoac
    ? Number((layout.labelHeightMm * INOAC_HEAD_BODY_ABSORB_RATIO).toFixed(2))
    : 0
  return `
  @page { size: ${B4_WIDTH_MM}mm ${B4_HEIGHT_MM}mm; margin: 0; }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; font-family: ${FONT}; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .pul-sheet {
    width: ${B4_WIDTH_MM}mm;
    height: ${B4_HEIGHT_MM}mm;
    padding: ${PAGE_MARGIN_MM}mm ${PAGE_MARGIN_MM}mm ${PAGE_MARGIN_MM}mm ${PAGE_MARGIN_LEFT_MM}mm;
    margin: 0;
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
  @media print {
    @page { size: ${B4_WIDTH_MM}mm ${B4_HEIGHT_MM}mm; margin: 0 !important; }
    html, body { margin: 0 !important; padding: 0 !important; }
    .pul-sheet {
      width: ${B4_WIDTH_MM}mm !important;
      height: ${B4_HEIGHT_MM}mm !important;
      padding: ${PAGE_MARGIN_MM}mm ${PAGE_MARGIN_MM}mm ${PAGE_MARGIN_MM}mm ${PAGE_MARGIN_LEFT_MM}mm !important;
      margin: 0 !important;
    }
    .pul-sheet-inner {
      width: ${layout.innerWidthMm}mm !important;
      height: ${layout.innerHeightMm}mm !important;
      gap: ${GUTTER_MM}mm !important;
    }
    .pul-label-frame,
    .pul-label-frame-edge {
      -webkit-print-color-adjust: exact !important;
      print-color-adjust: exact !important;
    }
    .pul-label {
      border: none !important;
      box-shadow: none !important;
    }
    .pul-label--empty {
      border: none !important;
      box-shadow: none !important;
    }
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
    position: relative;
    width: 100%;
    height: 100%;
    border: none;
    box-shadow: none;
    box-sizing: border-box;
    overflow: hidden;
    font-size: 8pt;
    line-height: 1.2;
    margin: 0;
    min-height: 0;
    background: #fff;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  .pul-label:not(.pul-label--empty) .pul-label-frame {
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 5;
  }
  .pul-label-frame-edge {
    position: absolute;
    background-color: ${LABEL_BORDER_COLOR};
  }
  .pul-label-frame-edge--t {
    left: 0;
    top: 0;
    width: 100%;
    height: ${LABEL_OUTER_BORDER_PT}pt;
  }
  .pul-label-frame-edge--r {
    right: 0;
    top: 0;
    width: ${LABEL_OUTER_BORDER_PT}pt;
    height: 100%;
  }
  .pul-label-frame-edge--b {
    left: 0;
    bottom: 0;
    width: 100%;
    height: ${LABEL_OUTER_BORDER_PT}pt;
  }
  .pul-label-frame-edge--l {
    left: 0;
    top: 0;
    width: ${LABEL_OUTER_BORDER_PT}pt;
    height: 100%;
  }
  .pul-label--empty {
    border: none;
    box-shadow: none;
    background: transparent !important;
    visibility: hidden;
  }
  .pul-label .pul-std-table,
  .pul-label .pul-inoac-table {
    width: 100%;
    height: 100%;
    border-collapse: separate;
    border-spacing: 0;
    table-layout: fixed;
  }
  .pul-label .pul-std-table td,
  .pul-label .pul-inoac-table td {
    border: none;
    border-right: ${LABEL_INNER_BORDER_CSS};
    border-bottom: ${LABEL_INNER_BORDER_CSS};
    border-left: none;
    vertical-align: middle;
    padding: 1mm 1.2mm;
  }
  .pul-label .pul-std-table td:last-child,
  .pul-label .pul-inoac-table td:last-child {
    border-right: none;
  }
  .pul-label .pul-std-table td.pul-std-mfg {
    border-right: ${LABEL_INNER_BORDER_CSS};
  }
  .pul-label .pul-std-table tr:last-child td,
  .pul-label .pul-inoac-table > tbody > tr:last-child > td,
  .pul-label .pul-inoac-table > tr:last-child > td {
    border-bottom: none;
  }
  .pul-label .pul-inoac-hist td {
    border: ${LABEL_INNER_BORDER_CSS};
    padding: 0;
    margin: 0;
  }
  .pul-std-lbl { width: 12mm; font-size: 7pt; text-align: center; background: #fff; }
  .pul-std-row-top {
    height: ${STD_TOP_ROW_MM}mm;
    max-height: ${STD_TOP_ROW_MM}mm;
  }
  .pul-std-row-name {
    height: ${STD_NAME_ROW_MM}mm;
    max-height: ${STD_NAME_ROW_MM}mm;
  }
  .pul-std-row-top td {
    height: ${STD_TOP_ROW_MM}mm;
    max-height: ${STD_TOP_ROW_MM}mm;
    overflow: hidden;
  }
  .pul-std-row-name td {
    height: ${STD_NAME_ROW_MM}mm;
    max-height: ${STD_NAME_ROW_MM}mm;
    overflow: hidden;
  }
  .pul-label .pul-std-table tr.pul-std-row-name > td {
    padding-top: max(0px, calc(1mm - 1px));
    padding-bottom: max(0px, calc(1mm - 1px));
  }
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
    line-height: calc(${STD_QTY_LINE_HEIGHT}em - ${STD_QTY_LINE_HEIGHT_TRIM_PX}px);
  }
  .pul-std-row-mfg td {
    height: ${STD_MFG_ROW_MM}mm;
    max-height: ${STD_MFG_ROW_MM}mm;
    line-height: calc(${STD_MFG_LBL_LINE_HEIGHT}em + ${STD_MFG_LINE_HEIGHT_ADD_PX}px);
    text-align: center;
    vertical-align: middle;
    font-size: 8pt;
    padding: 0 1.2mm;
    box-sizing: border-box;
  }
  .pul-std-row-mfg td.pul-std-lbl {
    overflow: hidden;
  }
  .pul-std-row-mfg td.pul-std-mfg {
    padding: 0;
    vertical-align: top;
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
    max-height: ${STD_MFG_ROW_MM}mm;
    box-sizing: border-box;
    padding: ${STD_MFG_INNER_PADDING_TOP_MM}mm 1.2mm ${STD_MFG_INNER_PADDING_BOTTOM_MM}mm;
    font-size: 8pt;
    line-height: calc(${STD_MFG_LINE_HEIGHT}em + ${STD_MFG_LINE_HEIGHT_ADD_PX}px);
    text-align: center;
    overflow: visible;
  }
  .pul-label .pul-std-table td.pul-std-stamp {
    position: relative;
    vertical-align: top;
    text-align: left;
    padding: 0;
    height: ${STD_STAMP_CELL_MM}mm;
    max-height: ${STD_STAMP_CELL_MM}mm;
    width: 16mm;
    border-right: none;
  }
  .pul-stamp-lbl {
    position: absolute;
    top: 0.3mm;
    left: 0.3mm;
    font-size: 6.5pt;
    margin: 0;
    padding: 0;
    text-align: left;
    line-height: 1.2;
  }
  .pul-std-back--part-only {
    padding: 0 1.2mm;
    vertical-align: middle;
    text-align: center;
  }
  .pul-back-part-val {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
    font-size: 16px;
    font-weight: 600;
    text-align: center;
    line-height: 1.2;
  }
  .pul-label .pul-std-table tr.pul-std-row-top--dual td.pul-std-lbl--split,
  .pul-label .pul-std-table tr.pul-std-row-top--dual td.pul-std-back--split {
    padding-top: calc(1mm - 1px);
    padding-bottom: calc(1mm - 1px);
    padding-left: 0;
    padding-right: 0;
    vertical-align: top;
  }
  .pul-std-split-half {
    height: ${STD_TOP_HALF_ROW_MM}mm;
    max-height: ${STD_TOP_HALF_ROW_MM}mm;
    display: flex;
    align-items: center;
    justify-content: center;
    box-sizing: border-box;
    overflow: hidden;
    padding-top: 0;
    padding-bottom: 0;
  }
  .pul-std-lbl--split .pul-std-split-half {
    font-size: 7pt;
    text-align: center;
    line-height: calc(${STD_TOP_SPLIT_LINE_HEIGHT_BACK}em - ${STD_TOP_SPLIT_LINE_HEIGHT_TRIM_PX}px);
  }
  .pul-std-lbl--split .pul-std-split-half:first-child,
  .pul-std-back--split .pul-std-split-half:first-child {
    border-bottom: ${LABEL_INNER_BORDER_CSS};
  }
  .pul-std-back--split .pul-std-split-val {
    font-size: 10pt;
    font-weight: 600;
    line-height: calc(${STD_TOP_SPLIT_LINE_HEIGHT_BACK}em - ${STD_TOP_SPLIT_LINE_HEIGHT_TRIM_PX}px);
    padding: 0 1.2mm;
    text-align: center;
  }
  .pul-std-back--split .pul-std-split-val:last-child {
    line-height: calc(${STD_TOP_SPLIT_LINE_HEIGHT_PART}em - ${STD_TOP_SPLIT_LINE_HEIGHT_TRIM_PX}px);
  }
  .pul-std-qr { width: 18mm; text-align: center; padding: 0.5mm; vertical-align: middle; }
  .pul-std-qr img {
    width: ${STD_QR_SIZE_MM}mm;
    height: ${STD_QR_SIZE_MM}mm;
    min-width: ${STD_QR_SIZE_MM}mm;
    min-height: ${STD_QR_SIZE_MM}mm;
    max-width: ${STD_QR_SIZE_MM}mm;
    max-height: ${STD_QR_SIZE_MM}mm;
    aspect-ratio: 1 / 1;
    object-fit: contain;
    display: block;
    margin: 0 auto;
  }
  .pul-label .pul-std-row-name td.pul-std-product {
    padding: 0 ${STD_PRODUCT_CELL_PAD_H_MM}mm;
    vertical-align: middle;
    text-align: center;
    overflow: hidden;
    font-weight: 800;
  }
  .pul-label .pul-std-row-name .pul-std-product-inner {
    margin-top: -1px;
    margin-bottom: -1px;
  }
  .pul-std-product-inner {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
    font-weight: inherit;
    line-height: inherit;
    overflow: hidden;
  }
  .pul-std-product.is-multiline .pul-std-product-inner {
    white-space: normal;
    word-break: break-all;
  }
  .pul-std-product:not(.is-multiline) .pul-std-product-inner {
    white-space: nowrap;
  }
  .pul-std-qty { font-size: 16pt; font-weight: 800; text-align: center; }
  .pul-mfg-line { line-height: calc(${STD_MFG_LINE_HEIGHT}em + ${STD_MFG_LINE_HEIGHT_ADD_PX}px); text-align: center; width: 100%; }
  .pul-inoac-mini { font-size: 6pt; text-align: center; line-height: 1; margin: 0; }
  .pul-inoac-head {
    height: auto;
  }
  .pul-label .pul-inoac-table td.pul-inoac-head-wrap {
    padding: 0 0.5mm;
    margin: 0;
    vertical-align: top;
    height: auto;
  }
  .pul-inoac-head-wrap {
    padding: 0 0.5mm;
    margin: 0;
    vertical-align: top;
    height: auto;
  }
  .pul-inoac-head-table {
    width: 100%;
    height: auto;
    border-collapse: collapse;
    table-layout: fixed;
    margin: 0;
  }
  .pul-inoac-head-table td {
    border: none;
    padding: 0;
    margin: 0;
  }
  .pul-inoac-head-lbl-row td {
    font-size: 6pt;
    font-weight: 600;
    line-height: 1;
    text-align: center;
    vertical-align: middle;
    padding: 0 0.3mm;
    margin: 0;
    white-space: nowrap;
  }
  .pul-inoac-head-body-row td {
    vertical-align: top;
    text-align: center;
    padding: calc(${INOAC_HEAD_BODY_ROW_EXTRA_PX / 2}px) 0.3mm;
    margin: 0;
    min-height: calc(${INOAC_QR_SIZE_MM}mm + ${inoacHeadBodyAbsorbMm}mm + ${INOAC_HEAD_BODY_ROW_EXTRA_PX}px);
    height: auto;
    line-height: 1;
  }
  .pul-inoac-head-body-cell--qr {
    vertical-align: top;
    padding: calc(${INOAC_HEAD_BODY_ROW_EXTRA_PX / 2}px) 0.3mm;
    margin: 0;
    line-height: 0;
    font-size: 0;
  }
  .pul-inoac-qr-wrap {
    margin: 0;
    padding: 0;
    line-height: 0;
    font-size: 0;
    text-align: center;
  }
  .pul-inoac-head-body-cell--name {
    vertical-align: top;
    line-height: 1.1;
    font-size: inherit;
    padding: calc(${INOAC_HEAD_BODY_ROW_EXTRA_PX / 2}px) 0.3mm;
  }
  .pul-inoac-head-body-cell--bar {
    vertical-align: top;
    padding: calc(${INOAC_HEAD_BODY_ROW_EXTRA_PX / 2}px) 0.3mm;
    margin: 0;
  }
  .pul-inoac-qr {
    width: ${INOAC_QR_SIZE_MM}mm;
    height: ${INOAC_QR_SIZE_MM}mm;
    min-width: ${INOAC_QR_SIZE_MM}mm;
    min-height: ${INOAC_QR_SIZE_MM}mm;
    max-width: ${INOAC_QR_SIZE_MM}mm;
    max-height: ${INOAC_QR_SIZE_MM}mm;
    aspect-ratio: 1 / 1;
    object-fit: contain;
    display: block;
    margin: 0 auto;
    padding: 0;
    flex-shrink: 0;
  }
  .pul-inoac-product {
    font-weight: 800;
    width: 100%;
    margin: 0;
    white-space: nowrap;
    overflow: hidden;
    text-align: center;
  }
  .pul-inoac-barcode { height: 6.5mm; overflow: hidden; margin: 0; }
  .pul-inoac-barcode svg { width: 100%; height: 100%; display: block; margin: 0; }
  .pul-inoac-barcode-hr {
    font-size: 6pt;
    font-weight: 600;
    letter-spacing: 0.06em;
    margin: 0;
    line-height: 1;
    white-space: nowrap;
  }
  .pul-inoac-row-part,
  .pul-inoac-row-dest {
    height: auto;
  }
  .pul-inoac-hist-block-row {
    height: 100%;
  }
  .pul-label .pul-inoac-table tr.pul-inoac-hist-block-row > td {
    height: 100%;
    padding: 0;
    vertical-align: top;
  }
  .pul-inoac-row-part td,
  .pul-inoac-row-dest td {
    vertical-align: middle;
    margin: 0;
    padding: 0;
  }
  .pul-inoac-kv-lbl {
    font-size: 6.5pt;
    font-weight: 700;
    line-height: 1.1;
    text-align: center;
    vertical-align: middle;
    margin: 0;
    padding: 0.2mm 0.3mm;
    white-space: nowrap;
  }
  .pul-inoac-kv-val {
    font-weight: 700;
    text-align: center;
    vertical-align: middle;
    line-height: 1.12;
    margin: 0;
    padding: 0.2mm 0.4mm;
  }
  .pul-inoac-row-part .pul-inoac-kv-lbl,
  .pul-inoac-row-dest .pul-inoac-kv-lbl {
    padding: calc(0.2mm + ${INOAC_KV_ROW_EXTRA_PX / 2}px) 0.3mm;
  }
  .pul-inoac-row-part .pul-inoac-kv-val,
  .pul-inoac-row-dest .pul-inoac-kv-val {
    padding: calc(0.2mm + ${INOAC_KV_ROW_EXTRA_PX / 2}px) 0.4mm;
  }
  .pul-inoac-part-val {
    font-size: 9pt;
    font-weight: 800;
    letter-spacing: 0.01em;
  }
  .pul-inoac-qty-val {
    display: flex;
    align-items: baseline;
    justify-content: center;
    gap: 0.5mm;
    line-height: 1;
  }
  .pul-inoac-qty-num { font-size: 13pt; font-weight: 800; }
  .pul-inoac-qty-unit { font-size: 7.5pt; font-weight: 700; }
  .pul-inoac-dest-val {
    font-size: 6.5pt;
    font-weight: 700;
    word-break: break-all;
    line-height: 1.15;
  }
  .pul-inoac-mfg-val { font-size: 6.5pt; font-weight: 700; line-height: 1.15; }
  .pul-inoac-mfg-line { margin: 0; padding: 0; text-align: center; }
  .pul-inoac-hist-block-wrap {
    height: 100%;
    padding: 0;
    vertical-align: top;
  }
  .pul-inoac-hist {
    width: 100%;
    height: 100%;
    border-collapse: collapse;
    table-layout: fixed;
  }
  .pul-inoac-hist-title-row,
  .pul-inoac-hist-num-row {
    height: auto;
  }
  .pul-inoac-hist-blank-row {
    height: 100%;
  }
  .pul-inoac-hist-title-cell {
    font-size: 6pt;
    font-weight: 600;
    line-height: 1.1;
    text-align: center;
    vertical-align: middle;
    height: 3.5mm;
    padding: 0.2mm 0;
  }
  .pul-inoac-hist-num-cell {
    font-size: 7pt;
    font-weight: 700;
    line-height: 1.1;
    text-align: center;
    vertical-align: middle;
    height: 3.5mm;
    padding: 0.2mm 0;
  }
  .pul-inoac-hist-blank-cell {
    height: 100%;
    min-height: calc(8.5mm + ${INOAC_HIST_BLANK_EXTRA_PX}px);
    vertical-align: top;
    line-height: 1;
    font-size: 0;
  }
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
