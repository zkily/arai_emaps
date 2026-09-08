/**
 * テキストラベル印刷（A5 横）
 * 1行目: 注意文言 18px / 2行目: 納入先 24px / 3行目: 自由テキスト 36px（改行なし）
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

/** 各行の固定フォントサイズ（px） */
export const FONT_SIZE = {
  notice: 36,
  destination: 60,
  message: 78,
} as const

export interface TextLabelPrintData {
  notice: string
  destinationName: string
  message: string
}

const PAGE_MARGIN_MM = 8

const PRINT_STYLES = `
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
  .row-text {
    display: inline-block;
    white-space: nowrap;
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
