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
 * 印刷ダイアログを閉じたあと（印刷・キャンセルいずれも）プレビュー window を閉じるスクリプトを HTML に注入。
 * afterprint / matchMedia(print) / focus / visibilitychange の複合フォールバック。
 */
function appendAutoClosePrintScript(html: string): string {
  const snippet = `<script>(function(){
var closed=0;
function closePreview(){if(closed)return;closed=1;setTimeout(function(){try{window.close()}catch(e){}},120);}
var printEngaged=0;
var sawBlur=0;
function markEngaged(){printEngaged=1;}
window.addEventListener("beforeprint",markEngaged);
window.addEventListener("afterprint",closePreview);
window.onafterprint=closePreview;
window.addEventListener("blur",function(){if(printEngaged)sawBlur=1;});
window.addEventListener("focus",function(){
  if(!printEngaged||closed||!sawBlur)return;
  setTimeout(closePreview,220);
});
try{
  var mq=window.matchMedia("print");
  var wasPrinting=0;
  var onMq=function(){
    if(mq.matches)wasPrinting=1;
    else if(wasPrinting&&printEngaged)closePreview();
  };
  if(mq.addEventListener)mq.addEventListener("change",onMq);
  else if(mq.addListener)mq.addListener(onMq);
}catch(e){}
document.addEventListener("visibilitychange",function(){
  if(!printEngaged||closed)return;
  if(document.visibilityState==="visible"&&sawBlur)setTimeout(closePreview,320);
});
window.__markPrintEngaged=markEngaged;
})();<\/script>`
  if (/<\/body>\s*<\/html>/i.test(html)) {
    return html.replace(/<\/body>\s*<\/html>/i, `${snippet}</body></html>`)
  }
  if (/<\/body>/i.test(html)) {
    return html.replace(/<\/body>/i, `${snippet}</body>`)
  }
  return html + snippet
}

/** 親ウィンドウ側：印刷プレビューを印刷／キャンセル後に閉じる */
function bindPrintPreviewAutoClose(printWin: Window) {
  let closed = false
  let printEngaged = false
  let pollId: ReturnType<typeof setInterval> | null = null

  const closeWin = () => {
    if (closed) return
    closed = true
    if (pollId != null) {
      window.clearInterval(pollId)
      pollId = null
    }
    window.setTimeout(() => {
      try {
        if (!printWin.closed) printWin.close()
      } catch {
        /* ignore */
      }
    }, 120)
  }

  const markEngaged = () => {
    printEngaged = true
  }

  try {
    printWin.addEventListener('beforeprint', markEngaged)
    printWin.addEventListener('afterprint', closeWin)
    printWin.onafterprint = closeWin
    let sawBlur = false
    printWin.addEventListener('blur', () => {
      if (printEngaged) sawBlur = true
    })
    printWin.addEventListener('focus', () => {
      if (!printEngaged || closed || !sawBlur) return
      window.setTimeout(closeWin, 220)
    })
  } catch {
    /* ignore */
  }

  return {
    notifyPrintCalled() {
      markEngaged()
      try {
        const pw = printWin as Window & { __markPrintEngaged?: () => void }
        pw.__markPrintEngaged?.()
      } catch {
        /* ignore */
      }

      if (pollId != null) window.clearInterval(pollId)
      let sawBlur = false
      let ticks = 0
      pollId = window.setInterval(() => {
        ticks += 1
        if (closed || printWin.closed) {
          if (pollId != null) window.clearInterval(pollId)
          pollId = null
          return
        }
        if (!printEngaged) return
        try {
          const focused = !!printWin.document.hasFocus?.()
          if (!focused) {
            sawBlur = true
          } else if (sawBlur) {
            closeWin()
          }
        } catch {
          /* ignore */
        }
        if (ticks > 240) {
          window.clearInterval(pollId!)
          pollId = null
        }
      }, 250)
    },
  }
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

  const autoCloseCtl = autoClose ? bindPrintPreviewAutoClose(w) : null

  if (autoPrint) {
    let printScheduled = false
    const runPrint = () => {
      if (printScheduled) return
      printScheduled = true
      try {
        w.focus()
        w.print()
        autoCloseCtl?.notifyPrintCalled()
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
