/**
 * テキストラベル印刷（A5 横）
 * - 出荷表示: 1行目 注意文言 / 2行目 納入先 / 3行目 自由テキスト
 * - 社内メッキ向け: 1行目 見出し / 2行目 品番等 / 3行目 N 枚目
 */
import {
  buildPrintHtmlDocument,
  escapeHtml,
  openPrintWindow,
  PRINT_POPUP_BLOCKED_MSG,
} from '@/utils/printWindow'

export { PRINT_POPUP_BLOCKED_MSG }

export const DEFAULT_NOTICE = '社内表示用　出荷の際は外してください'
export const DEFAULT_MESSAGE = '出荷OK'

export const DEFAULT_PLATING_TITLE = '社内メッキ向け'
export const DEFAULT_PLATING_PRODUCT = '164B FR'
export const DEFAULT_PLATING_COPIES = 1

/** 各行の固定フォントサイズ（px）— 出荷表示 */
export const FONT_SIZE = {
  notice: 36,
  destination: 60,
  message: 78,
} as const

/** 各行の固定フォントサイズ（px）— 社内メッキ向け */
export const PLATING_FONT_SIZE = {
  title: 48,
  product: 72,
  sheetNo: 48,
} as const

export interface TextLabelPrintData {
  notice: string
  destinationName: string
  message: string
}

export interface PlatingLabelPrintData {
  title: string
  productText: string
  /** 印刷枚数（1〜）。各枚に「N 枚目」を付与 */
  copies: number
}

const PAGE_MARGIN_MM = 8

const SHARED_PAGE_STYLES = `
  @page {
    size: A5 landscape;
    margin: ${PAGE_MARGIN_MM}mm;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body {
    width: 100%;
    height: 100%;
    background: #fff;
    color: #111;
    font-family: "Yu Gothic", "YuGothic", "Meiryo", "Hiragino Kaku Gothic ProN", "MS PGothic", sans-serif;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  .sheet {
    width: 100%;
    height: calc(148mm - ${PAGE_MARGIN_MM * 2}mm);
    display: flex;
    flex-direction: column;
    page-break-after: always;
    break-after: page;
  }
  .sheet:last-child {
    page-break-after: auto;
    break-after: auto;
  }
  .row {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    overflow: hidden;
    text-align: center;
    font-weight: 800;
    letter-spacing: 0.04em;
    white-space: nowrap;
    line-height: 1.2;
    padding: 2mm 2mm;
  }
  .row-text {
    display: inline-block;
    white-space: nowrap;
  }
`

const PRINT_STYLES = `
  ${SHARED_PAGE_STYLES}
  .row-notice {
    flex: 0 0 22%;
    border-bottom: 1.5px solid #9ca3af;
    font-size: ${FONT_SIZE.notice}px;
  }
  .row-destination {
    flex: 0 0 30%;
    border-bottom: 1.5px solid #9ca3af;
    font-size: ${FONT_SIZE.destination}px;
  }
  .row-message {
    flex: 1 1 auto;
    min-height: 0;
    font-size: ${FONT_SIZE.message}px;
  }
`

const PLATING_PRINT_STYLES = `
  ${SHARED_PAGE_STYLES}
  .sheet {
    justify-content: center;
    gap: 10mm;
  }
  .row {
    flex: 0 0 auto;
    padding: 0 4mm;
  }
  .row-title {
    font-size: ${PLATING_FONT_SIZE.title}px;
  }
  .row-product {
    font-size: ${PLATING_FONT_SIZE.product}px;
  }
  .row-sheet-no {
    font-size: ${PLATING_FONT_SIZE.sheetNo}px;
  }
`

export function buildTextLabelPrintHtml(data: TextLabelPrintData): string {
  const notice = (data.notice || '').trim() || '　'
  const destination = (data.destinationName || '').trim() || '　'
  const message = (data.message || '').trim() || '　'

  const body = `
    <section class="sheet">
      <div class="row row-notice">
        <span class="row-text">${escapeHtml(notice)}</span>
      </div>
      <div class="row row-destination">
        <span class="row-text">${escapeHtml(destination)}</span>
      </div>
      <div class="row row-message">
        <span class="row-text">${escapeHtml(message)}</span>
      </div>
    </section>
  `

  return buildPrintHtmlDocument('テキストラベル印刷', PRINT_STYLES, body)
}

export function printTextLabel(data: TextLabelPrintData): Window | null {
  const html = buildTextLabelPrintHtml(data)
  return openPrintWindow(html, { autoPrint: true, autoClose: true, delayMs: 350 })
}

export function formatSheetLabel(index: number): string {
  return `${index} 枚目`
}

export function buildPlatingLabelPrintHtml(data: PlatingLabelPrintData): string {
  const title = (data.title || '').trim() || '　'
  const product = (data.productText || '').trim() || '　'
  const copies = Math.max(1, Math.floor(Number(data.copies) || 1))

  const sheets = Array.from({ length: copies }, (_, i) => {
    const sheetNo = formatSheetLabel(i + 1)
    return `
    <section class="sheet">
      <div class="row row-title">
        <span class="row-text">${escapeHtml(title)}</span>
      </div>
      <div class="row row-product">
        <span class="row-text">${escapeHtml(product)}</span>
      </div>
      <div class="row row-sheet-no">
        <span class="row-text">${escapeHtml(sheetNo)}</span>
      </div>
    </section>`
  }).join('\n')

  return buildPrintHtmlDocument('社内メッキ向けラベル印刷', PLATING_PRINT_STYLES, sheets)
}

export function printPlatingLabel(data: PlatingLabelPrintData): Window | null {
  const html = buildPlatingLabelPrintHtml(data)
  return openPrintWindow(html, { autoPrint: true, autoClose: true, delayMs: 350 })
}
