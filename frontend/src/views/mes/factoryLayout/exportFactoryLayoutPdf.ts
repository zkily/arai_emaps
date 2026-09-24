import html2canvas from 'html2canvas'
import { jsPDF } from 'jspdf'

export interface LayoutPdfLegendGroup {
  title: string
  items: { label: string; color: string }[]
}

function safeFileName(name: string) {
  const cleaned = name.replace(/[\\/:*?"<>|]/g, '_').trim()
  return cleaned || 'layout'
}

function stamp(date: Date) {
  const pad = (value: number) => String(value).padStart(2, '0')
  return `${date.getFullYear()}${pad(date.getMonth() + 1)}${pad(date.getDate())}_${pad(date.getHours())}${pad(date.getMinutes())}`
}

function formatStamp(date: Date) {
  const pad = (value: number) => String(value).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function loadImage(src: string) {
  return new Promise<HTMLImageElement>((resolve, reject) => {
    const image = new Image()
    image.onload = () => resolve(image)
    image.onerror = () => reject(new Error('layout image'))
    image.src = src
  })
}

async function rasterizeSvg(svg: SVGSVGElement, width: number, height: number) {
  const clone = svg.cloneNode(true) as SVGSVGElement
  clone.querySelectorAll('[data-pdf-omit]').forEach((node) => node.remove())
  clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
  clone.setAttribute('viewBox', `0 0 ${width} ${height}`)
  const scale = Math.min(2, 3200 / Math.max(width, height, 1))
  clone.setAttribute('width', String(Math.ceil(width * scale)))
  clone.setAttribute('height', String(Math.ceil(height * scale)))
  const markup = new XMLSerializer().serializeToString(clone)
  const url = URL.createObjectURL(new Blob([markup], { type: 'image/svg+xml;charset=utf-8' }))
  try {
    const image = await loadImage(url)
    const canvas = document.createElement('canvas')
    canvas.width = image.naturalWidth || Math.ceil(width * scale)
    canvas.height = image.naturalHeight || Math.ceil(height * scale)
    const context = canvas.getContext('2d')
    if (!context) throw new Error('canvas')
    context.fillStyle = '#f7f9fc'
    context.fillRect(0, 0, canvas.width, canvas.height)
    context.drawImage(image, 0, 0)
    return canvas.toDataURL('image/png')
  } finally {
    URL.revokeObjectURL(url)
  }
}

function legendHtml(groups: LayoutPdfLegendGroup[]) {
  return groups
    .map((group) => {
      const chips = group.items
        .map(
          (item) =>
            `<span style="display:inline-flex;align-items:center;gap:6px;padding:4px 8px;border:1px solid #e2e8f0;border-radius:999px;background:#f8fafc;font-size:12px;color:#334155;"><i style="width:8px;height:8px;border-radius:50%;background:${escapeHtml(item.color)};display:inline-block;"></i>${escapeHtml(item.label)}</span>`,
        )
        .join('')
      return `<div style="display:flex;flex-wrap:wrap;align-items:center;gap:6px;"><em style="font-style:normal;font-weight:700;color:#64748b;font-size:12px;margin-right:2px;">${escapeHtml(group.title)}</em>${chips}</div>`
    })
    .join('')
}

export async function exportFactoryLayoutPdf(options: {
  svg: SVGSVGElement
  canvasWidth: number
  canvasHeight: number
  title: string
  exportedAtLabel: string
  legend: LayoutPdfLegendGroup[]
}) {
  const now = new Date()
  const png = await rasterizeSvg(options.svg, options.canvasWidth, options.canvasHeight)
  const sheet = document.createElement('div')
  sheet.style.cssText = [
    'position:fixed',
    'left:-12000px',
    'top:0',
    'width:1200px',
    'box-sizing:border-box',
    'padding:28px',
    'background:#ffffff',
    'color:#0f172a',
    'font-family:"Segoe UI","Yu Gothic UI","Hiragino Sans","Noto Sans JP",Meiryo,sans-serif',
  ].join(';')
  sheet.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:flex-end;gap:16px;margin-bottom:14px;">
      <div>
        <div style="font-size:12px;letter-spacing:0.08em;color:#64748b;">工場レイアウト</div>
        <div style="font-size:22px;font-weight:700;line-height:1.3;">${escapeHtml(options.title)}</div>
      </div>
      <div style="font-size:12px;color:#64748b;white-space:nowrap;">${escapeHtml(options.exportedAtLabel)} ${formatStamp(now)}</div>
    </div>
    <img alt="" src="${png}" style="display:block;width:100%;height:auto;border:1px solid #e2e8f0;border-radius:12px;background:#f7f9fc;" />
    <div style="display:flex;flex-direction:column;gap:8px;margin-top:14px;">${legendHtml(options.legend)}</div>
  `
  document.body.appendChild(sheet)
  try {
    const image = sheet.querySelector('img')
    if (image && !image.complete) {
      await loadImage(png)
    }
    const captured = await html2canvas(sheet, {
      backgroundColor: '#ffffff',
      scale: 2,
      useCORS: true,
    })
    const landscape = options.canvasWidth >= options.canvasHeight
    const pdf = new jsPDF({
      orientation: landscape ? 'l' : 'p',
      unit: 'mm',
      format: 'a3',
      compress: true,
    })
    const pageW = pdf.internal.pageSize.getWidth()
    const pageH = pdf.internal.pageSize.getHeight()
    const margin = 8
    const maxW = pageW - margin * 2
    const maxH = pageH - margin * 2
    const ratio = Math.min(maxW / captured.width, maxH / captured.height)
    const drawW = captured.width * ratio
    const drawH = captured.height * ratio
    pdf.addImage(
      captured.toDataURL('image/jpeg', 0.92),
      'JPEG',
      (pageW - drawW) / 2,
      (pageH - drawH) / 2,
      drawW,
      drawH,
      undefined,
      'FAST',
    )
    pdf.save(`${safeFileName(options.title)}_${stamp(now)}.pdf`)
  } finally {
    sheet.remove()
  }
}

function escapeHtml(value: string) {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
}
