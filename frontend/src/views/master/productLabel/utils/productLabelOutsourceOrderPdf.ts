import html2canvas from 'html2canvas'
import { jsPDF } from 'jspdf'
import {
  buildMixedProductLabelSheetDocuments,
  getProductLabelA4Layout,
  mmToLabelPrintPx,
  type ProductLabelPrintInput,
} from '@/views/mes/productionInstruction/productLabel/utils/productLabelPrint'

export interface LabelEmailAttachmentPayload {
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

function injectPdfCaptureStyles(html: string): string {
  const layout = getProductLabelA4Layout()
  const captureCss = `
    html, body {
      width: ${layout.a4WidthMm}mm !important;
      height: ${layout.a4HeightMm}mm !important;
      margin: 0 !important;
      padding: 0 !important;
      background: #fff !important;
      overflow: hidden !important;
    }
    body.pdf-capture-page {
      box-sizing: border-box !important;
      padding: ${layout.pageMarginMm}mm !important;
    }
    body.pdf-capture-page .sheet {
      width: ${layout.sheetWidthMm}mm !important;
      height: ${layout.sheetHeightMm}mm !important;
      margin: 0 !important;
      box-sizing: border-box !important;
    }
  `
  let next = html
  if (next.includes('</head>')) {
    next = next.replace('</head>', `<style id="plc-pdf-capture">${captureCss}</style></head>`)
  }
  next = next.replace('<body>', '<body class="pdf-capture-page">')
  return next
}

function applyCapturePixelLayout(doc: Document): HTMLElement {
  const layout = getProductLabelA4Layout()
  const body = doc.body
  const sheet = doc.querySelector('.sheet') as HTMLElement | null
  if (!sheet) {
    throw new Error('ラベルシートの生成に失敗しました')
  }

  const pageWidthPx = mmToLabelPrintPx(layout.a4WidthMm)
  const pageHeightPx = mmToLabelPrintPx(layout.a4HeightMm)
  const marginPx = mmToLabelPrintPx(layout.pageMarginMm)
  const sheetWidthPx = mmToLabelPrintPx(layout.sheetWidthMm)
  const sheetHeightPx = mmToLabelPrintPx(layout.sheetHeightMm)

  doc.documentElement.style.width = `${pageWidthPx}px`
  doc.documentElement.style.height = `${pageHeightPx}px`
  doc.documentElement.style.margin = '0'
  doc.documentElement.style.padding = '0'
  doc.documentElement.style.background = '#fff'

  body.style.width = `${pageWidthPx}px`
  body.style.height = `${pageHeightPx}px`
  body.style.margin = '0'
  body.style.padding = `${marginPx}px`
  body.style.boxSizing = 'border-box'
  body.style.background = '#fff'
  body.style.overflow = 'hidden'

  sheet.style.width = `${sheetWidthPx}px`
  sheet.style.height = `${sheetHeightPx}px`
  sheet.style.margin = '0'
  sheet.style.boxSizing = 'border-box'

  return body
}

async function htmlDocumentToA4PdfBlob(html: string): Promise<Blob> {
  const layout = getProductLabelA4Layout()
  const pageWidthPx = mmToLabelPrintPx(layout.a4WidthMm)
  const pageHeightPx = mmToLabelPrintPx(layout.a4HeightMm)

  const iframe = document.createElement('iframe')
  iframe.style.cssText = `position:fixed;left:-12000px;top:0;width:${pageWidthPx}px;height:${pageHeightPx}px;border:0;visibility:hidden`
  document.body.appendChild(iframe)

  try {
    const doc = iframe.contentDocument
    if (!doc) {
      throw new Error('印刷プレビューの生成に失敗しました')
    }
    doc.open()
    doc.write(injectPdfCaptureStyles(html))
    doc.close()
    await new Promise<void>((resolve) => setTimeout(resolve, 350))
    await waitForImages(doc)

    const captureRoot = applyCapturePixelLayout(doc)
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

    const pdf = new jsPDF({ orientation: 'p', unit: 'mm', format: 'a4', compress: true })
    const pageW = pdf.internal.pageSize.getWidth()
    const pageH = pdf.internal.pageSize.getHeight()
    const imgData = canvas.toDataURL('image/png')
    pdf.addImage(imgData, 'PNG', 0, 0, pageW, pageH, undefined, 'FAST')
    return pdf.output('blob')
  } finally {
    iframe.remove()
  }
}

/** 外注注文メール用：製品ごと1ラベル、1PDFあたり最大6品種（印刷プレビューと同一余白） */
export async function buildLabelEmailAttachments(
  items: ProductLabelPrintInput[]
): Promise<LabelEmailAttachmentPayload[]> {
  if (items.length === 0) return []

  const docs = await buildMixedProductLabelSheetDocuments(items)
  const attachments: LabelEmailAttachmentPayload[] = []

  for (let i = 0; i < docs.length; i += 1) {
    const pdfBlob = await htmlDocumentToA4PdfBlob(docs[i])
    attachments.push({
      filename: `現品票_${String(i + 1).padStart(2, '0')}.pdf`,
      mime_type: 'application/pdf',
      content_base64: await blobToBase64(pdfBlob),
    })
  }

  return attachments
}
