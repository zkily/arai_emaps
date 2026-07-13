import html2canvas from 'html2canvas'
import { jsPDF } from 'jspdf'
import { mmToLabelPrintPx } from '@/views/mes/productionInstruction/productLabel/utils/productLabelPrint'
import {
  buildMixedProductUseLabelSheetDocuments,
  getProductUseLabelB4Layout,
  isInoacDestination,
  type ProductUseLabelPrintInput,
} from '@/views/master/productUseLabel/utils/productUseLabelPrint'

export interface UseLabelEmailAttachmentPayload {
  filename: string
  mime_type: string
  content_base64: string
}

const CAPTURE_SCALE = 2

function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const result = String(reader.result || '')
      const base64 = result.includes(',') ? result.split(',')[1] : result
      resolve(base64)
    }
    reader.onerror = () => reject(reader.error)
    reader.readAsDataURL(blob)
  })
}

async function waitForImages(doc: Document): Promise<void> {
  const images = Array.from(doc.images)
  await Promise.all(
    images.map(
      (img) =>
        new Promise<void>((resolve) => {
          if (img.complete) {
            resolve()
            return
          }
          img.onload = () => resolve()
          img.onerror = () => resolve()
        })
    )
  )
}

function injectPdfCaptureStyles(html: string, inoac: boolean): string {
  const layout = getProductUseLabelB4Layout(inoac)
  const captureCss = `
    html, body {
      width: ${layout.b4WidthMm}mm !important;
      height: ${layout.b4HeightMm}mm !important;
      margin: 0 !important;
      padding: 0 !important;
      background: #fff !important;
      overflow: hidden !important;
    }
    body.pdf-capture-page .pul-sheet {
      width: ${layout.b4WidthMm}mm !important;
      height: ${layout.b4HeightMm}mm !important;
      margin: 0 !important;
      box-sizing: border-box !important;
    }
    body.pdf-capture-page .pul-sheet-inner {
      width: ${layout.innerWidthMm}mm !important;
      height: ${layout.innerHeightMm}mm !important;
    }
  `
  let next = html
  if (next.includes('</head>')) {
    next = next.replace('</head>', `<style id="pul-pdf-capture">${captureCss}</style></head>`)
  }
  next = next.replace('<body>', '<body class="pdf-capture-page">')
  return next
}

function applyCapturePixelLayout(doc: Document, inoac: boolean): HTMLElement {
  const layout = getProductUseLabelB4Layout(inoac)
  const body = doc.body
  const sheet = doc.querySelector('.pul-sheet') as HTMLElement | null
  if (!sheet) {
    throw new Error('ラベルシートの生成に失敗しました')
  }

  const pageWidthPx = mmToLabelPrintPx(layout.b4WidthMm)
  const pageHeightPx = mmToLabelPrintPx(layout.b4HeightMm)

  doc.documentElement.style.width = `${pageWidthPx}px`
  doc.documentElement.style.height = `${pageHeightPx}px`
  doc.documentElement.style.margin = '0'
  doc.documentElement.style.padding = '0'
  doc.documentElement.style.background = '#fff'

  body.style.width = `${pageWidthPx}px`
  body.style.height = `${pageHeightPx}px`
  body.style.margin = '0'
  body.style.padding = '0'
  body.style.boxSizing = 'border-box'
  body.style.background = '#fff'
  body.style.overflow = 'hidden'

  sheet.style.width = `${pageWidthPx}px`
  sheet.style.height = `${pageHeightPx}px`
  sheet.style.margin = '0'
  sheet.style.boxSizing = 'border-box'

  return body
}

async function htmlDocumentToB4PdfBlob(html: string, inoac: boolean): Promise<Blob> {
  const layout = getProductUseLabelB4Layout(inoac)
  const pageWidthPx = mmToLabelPrintPx(layout.b4WidthMm)
  const pageHeightPx = mmToLabelPrintPx(layout.b4HeightMm)

  const iframe = document.createElement('iframe')
  iframe.style.cssText = `position:fixed;left:-12000px;top:0;width:${pageWidthPx}px;height:${pageHeightPx}px;border:0;visibility:hidden`
  document.body.appendChild(iframe)

  try {
    const doc = iframe.contentDocument
    if (!doc) {
      throw new Error('印刷プレビューの生成に失敗しました')
    }
    doc.open()
    doc.write(injectPdfCaptureStyles(html, inoac))
    doc.close()
    await new Promise<void>((resolve) => setTimeout(resolve, 400))
    await waitForImages(doc)

    const captureRoot = applyCapturePixelLayout(doc, inoac)
    await new Promise<void>((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)))

    const canvas = await html2canvas(captureRoot, {
      scale: CAPTURE_SCALE,
      useCORS: true,
      allowTaint: false,
      backgroundColor: '#ffffff',
      logging: false,
      width: pageWidthPx,
      height: pageHeightPx,
      windowWidth: pageWidthPx,
      windowHeight: pageHeightPx,
      scrollX: 0,
      scrollY: 0,
      x: 0,
      y: 0,
    })

    const pdf = new jsPDF({
      orientation: 'landscape',
      unit: 'mm',
      format: [layout.b4HeightMm, layout.b4WidthMm],
      compress: true,
    })
    const pageW = pdf.internal.pageSize.getWidth()
    const pageH = pdf.internal.pageSize.getHeight()
    const imgData = canvas.toDataURL('image/png')
    pdf.addImage(imgData, 'PNG', 0, 0, pageW, pageH, undefined, 'FAST')
    return pdf.output('blob')
  } finally {
    iframe.remove()
  }
}

/** 外注注文メール用：製品ごと1ラベル、B4横向PDF（通常4×5 / INOAC 4×4） */
export async function buildUseLabelEmailAttachments(
  items: ProductUseLabelPrintInput[]
): Promise<UseLabelEmailAttachmentPayload[]> {
  if (items.length === 0) return []

  const docs = await buildMixedProductUseLabelSheetDocuments(items)
  const attachments: UseLabelEmailAttachmentPayload[] = []

  for (let i = 0; i < docs.length; i += 1) {
    const inoac = docs[i].includes('pul-inoac')
    const pdfBlob = await htmlDocumentToB4PdfBlob(docs[i], inoac)
    attachments.push({
      filename: `製品用ラベル_${String(i + 1).padStart(2, '0')}.pdf`,
      mime_type: 'application/pdf',
      content_base64: await blobToBase64(pdfBlob),
    })
  }

  return attachments
}

/** 外注注文PDF枚数の概算（レイアウト混在時） */
export function estimateUseLabelPdfPages(
  items: Pick<ProductUseLabelPrintInput, 'destination_name'>[]
): number {
  if (!items.length) return 0
  let std = 0
  let inoac = 0
  for (const item of items) {
    if (isInoacDestination(item.destination_name)) inoac += 1
    else std += 1
  }
  return Math.ceil(std / 20) + Math.ceil(inoac / 16)
}
