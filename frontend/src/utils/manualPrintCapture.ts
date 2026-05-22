import html2canvas from 'html2canvas'
import { jsPDF } from 'jspdf'

type StyleSnapshot = {
  el: HTMLElement
  overflow: string
  height: string
  maxHeight: string
  minHeight: string
}

/** キャプチャ／印刷用に overflow・高さ制限を一時解除（祖先まで） */
export function expandElementForFullCapture(root: HTMLElement): () => void {
  const snapshots: StyleSnapshot[] = []
  let node: HTMLElement | null = root
  while (node && node !== document.body) {
    snapshots.push({
      el: node,
      overflow: node.style.overflow,
      height: node.style.height,
      maxHeight: node.style.maxHeight,
      minHeight: node.style.minHeight,
    })
    node.style.overflow = 'visible'
    node.style.height = 'auto'
    node.style.maxHeight = 'none'
    node.style.minHeight = '0'
    node = node.parentElement
  }
  return () => {
    for (const s of snapshots) {
      s.el.style.overflow = s.overflow
      s.el.style.height = s.height
      s.el.style.maxHeight = s.maxHeight
      s.el.style.minHeight = s.minHeight
    }
  }
}

/** スクロール領域を含む要素全体を canvas 化（ビューポート截断を避ける） */
export async function captureFullElementToCanvas(
  root: HTMLElement,
  options?: { scale?: number; backgroundColor?: string },
): Promise<HTMLCanvasElement> {
  const restore = expandElementForFullCapture(root)
  root.scrollTop = 0
  root.scrollLeft = 0

  try {
    await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)))

    const width = Math.max(root.scrollWidth, root.clientWidth)
    const height = Math.max(root.scrollHeight, root.clientHeight)

    return await html2canvas(root, {
      scale: options?.scale ?? 2,
      useCORS: true,
      allowTaint: false,
      backgroundColor: options?.backgroundColor ?? '#ffffff',
      logging: false,
      width,
      height,
      windowWidth: width,
      windowHeight: height,
      scrollX: 0,
      scrollY: 0,
      x: 0,
      y: 0,
      onclone: (_doc, cloned) => {
        const el = cloned as HTMLElement
        el.style.overflow = 'visible'
        el.style.height = 'auto'
        el.style.maxHeight = 'none'
        el.style.minHeight = '0'
      },
    })
  } finally {
    restore()
  }
}

/** 印刷 @page と同じ A4 縦・余白（help-markdown-page.scss と揃える） */
export const MANUAL_PRINT_PAGE_MARGIN_MM = 6

export interface ManualPdfPageLayout {
  orientation: 'p' | 'l'
  format: 'a4'
  marginMm: number
}

export const MANUAL_PRINT_PDF_LAYOUT: ManualPdfPageLayout = {
  orientation: 'p',
  format: 'a4',
  marginMm: MANUAL_PRINT_PAGE_MARGIN_MM,
}

/** 縦長 canvas を A4 縦・余白付きで複数ページに分割して Blob 化 */
export function buildPdfBlobFromCanvas(
  canvas: HTMLCanvasElement,
  layout: ManualPdfPageLayout = MANUAL_PRINT_PDF_LAYOUT,
): Blob {
  const imgData = canvas.toDataURL('image/jpeg', 0.92)
  const pdf = new jsPDF({
    orientation: layout.orientation,
    unit: 'mm',
    format: layout.format,
    compress: true,
  })
  const pageWidth = pdf.internal.pageSize.getWidth()
  const pageHeight = pdf.internal.pageSize.getHeight()
  const margin = layout.marginMm
  const contentWidth = pageWidth - margin * 2
  const contentHeight = pageHeight - margin * 2
  const imgWidthMm = contentWidth
  const imgHeightMm = (canvas.height / canvas.width) * imgWidthMm

  let heightLeft = imgHeightMm
  let pageIndex = 0
  let positionY = margin

  pdf.addImage(imgData, 'JPEG', margin, positionY, imgWidthMm, imgHeightMm, undefined, 'FAST')
  heightLeft -= contentHeight

  while (heightLeft > 0.5) {
    pageIndex += 1
    pdf.addPage()
    positionY = margin - pageIndex * contentHeight
    pdf.addImage(imgData, 'JPEG', margin, positionY, imgWidthMm, imgHeightMm, undefined, 'FAST')
    heightLeft -= contentHeight
  }

  return pdf.output('blob')
}

export function downloadPdfBlob(blob: Blob, fileName: string): void {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = fileName
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

export const PRINT_BODY_CLASS = 'manual-print-active'

/** 印刷用スタイルを有効化（PDF キャプチャ時も同じ見た目にする） */
export function enablePrintLayoutStyles(): () => void {
  document.body.classList.add(PRINT_BODY_CLASS)
  return () => document.body.classList.remove(PRINT_BODY_CLASS)
}

/** ブラウザ印刷で全文が複数ページに出るよう body にクラスを付与 */
export function runBrowserPrint(scrollContainer?: HTMLElement | null): void {
  if (scrollContainer) {
    scrollContainer.scrollTop = 0
    scrollContainer.scrollLeft = 0
  }
  const cleanup = enablePrintLayoutStyles()
  window.addEventListener('afterprint', cleanup, { once: true })
  window.print()
  setTimeout(cleanup, 2000)
}
