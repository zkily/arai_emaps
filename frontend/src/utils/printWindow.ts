/** 印刷用ポップアップがブロックされた際のメッセージ */
export const PRINT_POPUP_BLOCKED_MSG =
  'ポップアップがブロックされています。印刷用ウィンドウを許可してください。'

export function escapeHtml(s: string): string {
  const div = document.createElement('div')
  div.textContent = s
  return div.innerHTML
}

export interface OpenPrintWindowOptions {
  autoPrint?: boolean
  autoClose?: boolean
  delayMs?: number
  windowFeatures?: string
}

/** HTML ドキュメント文字列を組み立てる */
export function buildPrintHtmlDocument(title: string, styles: string, body: string): string {
  return `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>${escapeHtml(title)}</title><style>${styles}</style></head><body>${body}</body></html>`
}

/**
 * 新規ウィンドウで HTML を開き、必要に応じて印刷する。
 * @returns 開けた Window、ブロック時は null
 */
export function openPrintWindow(html: string, options: OpenPrintWindowOptions = {}): Window | null {
  const {
    autoPrint = true,
    autoClose = true,
    delayMs = 300,
    windowFeatures = '',
  } = options

  const w = windowFeatures
    ? window.open('', '_blank', windowFeatures)
    : window.open('', '_blank')
  if (!w) return null

  w.document.write(html)
  w.document.close()
  w.focus()

  if (autoPrint) {
    const runPrint = () => {
      w.print()
      if (autoClose) {
        w.onafterprint = () => w.close()
      }
    }
    setTimeout(runPrint, delayMs)
  }

  return w
}

/** 在庫数表示：0 または未設定は空文字 */
export function formatStockDisplay(value: number | null | undefined): string | number {
  if (value == null || Number(value) === 0) return ''
  return value
}
