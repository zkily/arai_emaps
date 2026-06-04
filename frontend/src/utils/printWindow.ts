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

/** 印刷ダイアログを閉じたあと（印刷・キャンセルいずれも）プレビュー window を閉じるスクリプトを HTML に注入 */
function appendAutoClosePrintScript(html: string): string {
  const snippet =
    '<script>(function(){var done=0;function z(){if(done)return;done=1;setTimeout(function(){try{window.close()}catch(e){}},100);}' +
    'window.addEventListener("afterprint",z);window.onafterprint=z;' +
    'try{var mq=window.matchMedia("print");var saw=0;var q=function(){if(mq.matches)saw=1;else if(saw){z();mq.removeEventListener("change",q);}};' +
    '(mq.addEventListener?mq.addEventListener("change",q):mq.addListener(q));}catch(e){}' +
    'var bp=0;window.addEventListener("beforeprint",function(){bp=1});' +
    'document.addEventListener("visibilitychange",function(){if(done)return;if(bp&&document.visibilityState==="visible")setTimeout(z,500);});' +
    '})();<\\/script>'
  if (/<\/body>\s*<\/html>/i.test(html)) {
    return html.replace(/<\/body>\s*<\/html>/i, `${snippet}</body></html>`)
  }
  if (/<\/body>/i.test(html)) {
    return html.replace(/<\/body>/i, `${snippet}</body>`)
  }
  return html + snippet
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

  const htmlToWrite = autoClose ? appendAutoClosePrintScript(html) : html

  const w = windowFeatures
    ? window.open('', '_blank', windowFeatures)
    : window.open('', '_blank')
  if (!w) return null

  w.document.write(htmlToWrite)
  w.document.close()
  w.focus()

  if (autoClose) {
    let closed = false
    const closePopup = () => {
      if (closed) return
      closed = true
      window.setTimeout(() => {
        try {
          if (!w.closed) w.close()
        } catch {
          /* ignore */
        }
      }, 150)
    }
    w.addEventListener('afterprint', closePopup)
    w.onafterprint = closePopup
  }

  if (autoPrint) {
    let printScheduled = false
    const runPrint = () => {
      if (printScheduled) return
      printScheduled = true
      try {
        w.focus()
        w.print()
      } catch {
        /* ignore */
      }
    }

    window.setTimeout(runPrint, delayMs)
    w.addEventListener('load', () => window.setTimeout(runPrint, delayMs), { once: true })
  }

  return w
}

/** 在庫数表示：0 または未設定は空文字 */
export function formatStockDisplay(value: number | null | undefined): string | number {
  if (value == null || Number(value) === 0) return ''
  return value
}
