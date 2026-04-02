<template>
  <div class="help-page" :class="{ 'is-capturing': isCapturingPdf }">
    <div class="help-bg" aria-hidden="true" />
    <div class="help-shell" ref="helpCaptureEl">
    <div class="help-header">
      <div class="help-title">
        <div class="help-title-badge">
          <el-icon class="help-title-icon"><QuestionFilled /></el-icon>
        </div>
        <div class="help-title-text">
          <h1>生産計画ベースライン管理</h1>
          <p>操作説明</p>
        </div>
      </div>
      <div class="help-actions">
        <el-button class="help-btn help-btn-print" type="default" plain @click="handlePrint">
          <el-icon class="help-btn-icon"><Printer /></el-icon>
          <span class="help-btn-text">印刷</span>
        </el-button>

        <el-button class="help-btn help-btn-pdf" type="primary" plain :loading="pdfSaving" @click="handlePdfSave">
          <el-icon class="help-btn-icon"><Document /></el-icon>
          <span class="help-btn-text">PDF保存</span>
        </el-button>
      </div>
    </div>

    <el-card class="help-card" shadow="never">
      <div v-if="loading" class="help-loading">
        <div class="help-spinner" />
        <span>読み込み中...</span>
      </div>
      <div v-else class="help-content" v-html="renderedHtml"></div>
    </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import MarkdownIt from 'markdown-it'
import { ElMessage } from 'element-plus'
import { Document, Printer, QuestionFilled } from '@element-plus/icons-vue'
import html2canvas from 'html2canvas'
import { jsPDF } from 'jspdf'

const loading = ref(true)
const renderedHtml = ref('')
const pdfSaving = ref(false)
const isCapturingPdf = ref(false)
const helpCaptureEl = ref<HTMLElement | null>(null)

const DOC_FILENAME = 'ppb_manual_ja.md'
// 部分浏览器对包含日文/中文的路径不稳定，使用 encodeURIComponent 规避编码问题
const DOC_URL = `/docs/${encodeURIComponent(DOC_FILENAME)}`

function sanitizeHtml(input: string): string {
  // 简易安全过滤：移除 script 标签以及 on* 事件属性，避免把任意 HTML 当成可信内容
  return input
    .replace(/<script[\s\S]*?>[\s\S]*?<\/script>/gi, '')
    .replace(/\son\w+="[^"]*"/gi, '')
    .replace(/\son\w+='[^']*'/gi, '')
    .replace(/<iframe[\s\S]*?>[\s\S]*?<\/iframe>/gi, '')
}

onMounted(async () => {
  try {
    const res = await fetch(DOC_URL)
    if (!res.ok) {
      throw new Error(`Failed to load help doc: ${res.status}`)
    }

    const mdText = await res.text()
    const md = new MarkdownIt({
      html: true,
      linkify: true,
      breaks: true,
      typographer: true,
    })

    // markdown 文件里的图片是相对路径（./images/...），这里统一改为绝对路径（/images/...）
    const normalizedMd = mdText.replace(/\.\/images\//g, '/images/')

    renderedHtml.value = sanitizeHtml(md.render(normalizedMd))
  } catch (e: any) {
    console.error(e)
    ElMessage.error(e?.message ?? '操作説明の読み込みに失敗しました')
    renderedHtml.value = '<p>操作説明の読み込みに失敗しました。</p>'
  } finally {
    loading.value = false
  }
})

function handlePrint() {
  window.print()
}

async function handlePdfSave() {
  if (loading.value) {
    ElMessage.warning('内容正在加载中…')
    return
  }
  if (!helpCaptureEl.value) {
    ElMessage.error('未找到可用于生成 PDF 的页面内容')
    return
  }

  try {
    pdfSaving.value = true
    isCapturingPdf.value = true

    // 等待 DOM/CSS（隐藏按钮/背景）完成
    await nextTick()
    await new Promise((r) => setTimeout(r, 200))

    const canvas = await html2canvas(helpCaptureEl.value, {
      scale: 2,
      useCORS: true,
      backgroundColor: '#ffffff',
      logging: false,
    })

    const imgData = canvas.toDataURL('image/jpeg', 0.92)
    const pdf = new jsPDF({ orientation: 'p', unit: 'mm', format: 'a4', compress: true })

    const pageWidth = pdf.internal.pageSize.getWidth()
    const pageHeight = pdf.internal.pageSize.getHeight()

    const imgWidthMm = pageWidth
    const imgHeightMm = (canvas.height / canvas.width) * imgWidthMm

    const MM_EPS = 0.8
    let heightLeft = imgHeightMm
    let position = 0

    // 先加第一页
    pdf.addImage(imgData, 'JPEG', 0, position, imgWidthMm, imgHeightMm, undefined, 'FAST')
    heightLeft -= pageHeight

    // 再按高度切多页
    while (heightLeft > MM_EPS) {
      position = heightLeft - imgHeightMm
      pdf.addPage()
      pdf.addImage(imgData, 'JPEG', 0, position, imgWidthMm, imgHeightMm, undefined, 'FAST')
      heightLeft -= pageHeight
    }

    const blob = pdf.output('blob')
    const fileName = '生産計画ベースライン管理_操作説明.pdf'
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = fileName
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)

    ElMessage.success('PDFの保存を開始しました')
  } catch (e: any) {
    console.error(e)
    ElMessage.error(e?.message ?? 'PDFの保存に失敗しました')
  } finally {
    isCapturingPdf.value = false
    pdfSaving.value = false
  }
}
</script>

<style scoped>
.help-page {
  min-height: calc(100vh - 60px);
  position: relative;
  padding: 22px 16px;
  background: linear-gradient(180deg, rgba(64,158,255,.06), rgba(255,255,255,0));
}

.help-bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(600px 240px at 20% 0%, rgba(64,158,255,.14), transparent 60%),
    radial-gradient(540px 220px at 90% 10%, rgba(59,130,246,.10), transparent 55%);
  pointer-events: none;
}

.help-shell {
  position: relative;
  max-width: 1120px;
  margin: 0 auto;
}

.help-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.help-title {
  display: flex;
  align-items: center;
  gap: 14px;
}

.help-title-badge {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(64,158,255,.10);
  border: 1px solid rgba(64,158,255,.18);
  box-shadow: 0 10px 30px rgba(64,158,255,.10);
}

.help-title-icon {
  color: #409eff;
  font-size: 20px;
}

.help-title-text h1 {
  margin: 0;
  font-size: 18px;
  font-weight: 750;
  letter-spacing: .2px;
}

.help-title-text p {
  margin: 3px 0 0;
  font-size: 13px;
  color: #64748b;
}

.help-actions {
  display: flex;
  gap: 12px;
}

.is-capturing .help-actions {
  display: none !important;
}

.is-capturing .help-bg {
  display: none !important;
}

.is-capturing .help-card {
  background: #ffffff !important;
  backdrop-filter: none !important;
  box-shadow: none !important;
  border-color: rgba(148, 163, 184, 0.18) !important;
}

.help-btn-icon {
  margin-right: 8px;
  font-size: 16px;
  vertical-align: -2px;
}

.help-btn-text {
  font-weight: 650;
}

:deep(.help-btn) {
  height: 36px;
  padding: 0 14px;
  border-radius: 12px;
  transition: all 0.18s ease;
  box-shadow: none !important;
}

/* 印刷：细边框 + 淡蓝 hover */
:deep(.help-btn-print) {
  background: rgba(255, 255, 255, 0.7) !important;
  border: 1px solid rgba(148, 163, 184, 0.45) !important;
  color: #0f172a !important;
}

:deep(.help-btn-print:hover) {
  background: rgba(64, 158, 255, 0.10) !important;
  border-color: rgba(64, 158, 255, 0.35) !important;
}

/* PDF保存：渐变主按钮 */
:deep(.help-btn-pdf) {
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.98), rgba(37, 99, 235, 0.96)) !important;
  border: 1px solid rgba(37, 99, 235, 0.45) !important;
  color: #ffffff !important;
}

:deep(.help-btn-pdf:hover) {
  filter: brightness(1.03);
  border-color: rgba(37, 99, 235, 0.6) !important;
}

.help-card {
  padding: 18px 18px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.86);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(148, 163, 184, 0.35);
}

.help-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 26px 10px;
  color: #475569;
  font-size: 14px;
}

.help-spinner {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid rgba(64,158,255,.25);
  border-top-color: rgba(64,158,255,.95);
  animation: help-spin 1s linear infinite;
}

@keyframes help-spin {
  to {
    transform: rotate(360deg);
  }
}

.help-content {
  line-height: 1.8;
  color: #0f172a;
  font-size: 14px;
}

:deep(.help-content p) {
  margin: 0 0 12px;
}

:deep(.help-content h1),
:deep(.help-content h2) {
  margin: 22px 0 10px;
  font-size: 18px;
  font-weight: 800;
  padding-left: 12px;
  border-left: 4px solid rgba(64,158,255,.9);
}

:deep(.help-content h3),
:deep(.help-content h4) {
  margin: 18px 0 8px;
  font-weight: 750;
  padding-left: 10px;
  border-left: 3px solid rgba(59,130,246,.55);
}

:deep(.help-content a) {
  color: #2563eb;
  text-decoration: none;
  border-bottom: 1px solid rgba(37,99,235,.18);
}

:deep(.help-content a:hover) {
  border-bottom-color: rgba(37,99,235,.55);
}

:deep(.help-content ul),
:deep(.help-content ol) {
  margin: 0 0 12px;
  padding-left: 22px;
}

:deep(.help-content li) {
  margin: 4px 0;
}

:deep(.help-content blockquote) {
  margin: 12px 0;
  padding: 12px 14px;
  border-left: 4px solid rgba(64,158,255,.85);
  background: rgba(64,158,255,.08);
  border-radius: 10px;
  color: #0b1220;
}

:deep(.help-content hr) {
  border: none;
  border-top: 1px solid rgba(148, 163, 184, .35);
  margin: 18px 0;
}

:deep(.help-content table) {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  overflow: hidden;
  border-radius: 12px;
}

:deep(.help-content th),
:deep(.help-content td) {
  border: 1px solid rgba(148, 163, 184, .35);
  padding: 10px 12px;
  text-align: left;
}

:deep(.help-content th) {
  background: rgba(64,158,255,.08);
  font-weight: 750;
}

:deep(.help-content pre) {
  background: #0b1220;
  color: #e5e7eb;
  padding: 14px;
  overflow: auto;
  border-radius: 12px;
  border: 1px solid rgba(148,163,184,.18);
}

:deep(.help-content pre code) {
  background: transparent !important;
  padding: 0 !important;
}

:deep(.help-content code) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
  background: rgba(59,130,246,.08);
  padding: 2px 6px;
  border-radius: 8px;
}

:deep(.help-content img) {
  max-width: 100%;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(2,6,23,.12);
  border: 1px solid rgba(148,163,184,.35);
}

@media print {
  .help-page {
    padding: 0 !important;
    background: #ffffff !important;
  }

  .help-bg,
  .help-actions {
    display: none !important;
  }

  .help-card {
    border: none !important;
    border-radius: 0 !important;
    background: #ffffff !important;
    box-shadow: none !important;
    backdrop-filter: none !important;
    padding: 0 !important;
  }

  .help-shell {
    max-width: none !important;
  }

  .help-content {
    font-size: 13px;
    color: #000000;
  }

  :deep(.help-content img) {
    box-shadow: none !important;
  }
}

</style>

