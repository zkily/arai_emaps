<template>
  <div class="manual-home pb-std">
    <aside class="manual-sidebar">
      <div class="manual-sidebar__header">
        <el-icon class="manual-sidebar__logo" :size="22"><Notebook /></el-icon>
        <span class="manual-sidebar__title">{{ t('operationManual.homeTitle') }}</span>
      </div>
      <nav class="manual-sidebar__nav">
        <section
          v-for="group in manualNavGroups"
          :key="group.category"
          class="manual-sidebar__group"
        >
          <h3 class="manual-sidebar__group-title">
            {{ t(OPERATION_MANUAL_CATEGORY_I18N_KEY[group.category]) }}
          </h3>
          <div
            v-for="item in group.items"
            :key="item.slug"
            class="manual-sidebar__item"
            :class="{ 'manual-sidebar__item--active': item.slug === activeSlug }"
            @click="selectManual(item.slug)"
          >
            <el-icon :size="16"><Memo /></el-icon>
            <span class="manual-sidebar__item-text">{{ item.pageTitle }}</span>
            <span v-if="item.pdfFile" class="manual-sidebar__pdf-tag">PDF</span>
          </div>
        </section>
      </nav>
      <div class="manual-sidebar__footer">
        <el-button
          class="manual-sidebar__print-btn"
          size="small"
          @click="handlePrint"
        >
          <el-icon><Printer /></el-icon>
          <span>{{ t('operationManual.print') }}</span>
        </el-button>
      </div>
    </aside>

    <main class="manual-content" ref="manualScrollEl">
      <div v-if="loading" class="manual-content__loading">
        <div class="manual-content__spinner" />
        <span>{{ t('operationManual.loading') }}</span>
      </div>
      <div v-else-if="loadError" class="manual-content__error">
        <p>{{ loadError }}</p>
      </div>
      <div v-else-if="pdfUrl" class="manual-print-area manual-print-area--pdf">
        <div class="manual-content__header pb-hero pb-hero--page">
          <div class="manual-content__fx pb-bubbles" aria-hidden="true" />
          <div class="manual-content__title-badge">
            <el-icon :size="20"><QuestionFilled /></el-icon>
          </div>
          <div class="manual-content__copy">
            <h1 class="manual-content__title pb-hero-title">{{ currentTitle }}</h1>
            <p class="manual-content__subtitle pb-hero-desc">{{ t('operationManual.pdfSubtitle') }}</p>
          </div>
          <span class="manual-content__kind">PDF</span>
        </div>
        <iframe
          ref="pdfFrameEl"
          class="manual-pdf"
          :src="pdfUrl"
          :title="currentTitle"
        />
      </div>
      <div v-else class="manual-print-area">
        <div class="manual-content__header pb-hero pb-hero--page">
          <div class="manual-content__fx pb-bubbles" aria-hidden="true" />
          <div class="manual-content__title-badge">
            <el-icon :size="20"><QuestionFilled /></el-icon>
          </div>
          <div class="manual-content__copy">
            <h1 class="manual-content__title pb-hero-title">{{ currentTitle }}</h1>
            <p class="manual-content__subtitle pb-hero-desc">{{ t('operationManual.subtitle') }}</p>
          </div>
        </div>
        <div
          ref="helpContentEl"
          class="manual-content__body help-content"
          v-html="renderedHtml"
        />
      </div>

      <el-button
        v-show="showTocFab"
        class="manual-toc-fab"
        round
        :aria-label="t('operationManual.backToToc')"
        @click="scrollToToc"
      >
        <el-icon><Top /></el-icon>
        <span class="manual-toc-fab__label">{{ t('operationManual.backToToc') }}</span>
      </el-button>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Memo, Notebook, Printer, QuestionFilled, Top } from '@element-plus/icons-vue'
import {
  OPERATION_MANUALS,
  OPERATION_MANUAL_CATEGORY_I18N_KEY,
  getOperationManualBySlug,
  getOperationManualNavGroups,
} from '@/config/operationManuals'
import { runBrowserPrint } from '@/utils/manualPrintCapture'
import { getManualMarkdown, getManualPdfUrl, normalizeManualMarkdown } from '@/views/manual/manualAssets'
import {
  bindHelpContentAnchorNav,
  renderHelpMarkdown,
  scrollHelpToHash,
} from '@/utils/markdownHelpRender'

defineOptions({ name: 'ManualHome' })

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const manuals = OPERATION_MANUALS
const manualNavGroups = getOperationManualNavGroups()

const activeSlug = computed(() => String(route.params.slug ?? manuals[0]?.slug ?? ''))
const manual = computed(() => getOperationManualBySlug(activeSlug.value))
const currentTitle = computed(() => manual.value?.pageTitle ?? t('operationManual.unknownTitle'))

const loading = ref(true)
const loadError = ref('')
const renderedHtml = ref('')
const pdfUrl = ref('')
const manualScrollEl = ref<HTMLElement | null>(null)
const helpContentEl = ref<HTMLElement | null>(null)
const pdfFrameEl = ref<HTMLIFrameElement | null>(null)
let unbindAnchorNav: (() => void) | null = null

const showTocFab = computed(
  () => !loading.value && !loadError.value && Boolean(renderedHtml.value) && !pdfUrl.value,
)

const TOC_HEADING_IDS = ['目次', 'toc', 'table-of-contents', 'mokuji']

function scrollToToc(): void {
  const scrollEl = manualScrollEl.value
  const root = helpContentEl.value
  if (!scrollEl || !root) return

  let target: HTMLElement | null = null
  for (const id of TOC_HEADING_IDS) {
    const el = root.querySelector<HTMLElement>(`#${CSS.escape(id)}`)
    if (el) {
      target = el
      break
    }
  }
  if (!target) {
    target = root.querySelector<HTMLElement>('h2')
  }
  if (!target) return

  const scrollTop =
    scrollEl.scrollTop +
    target.getBoundingClientRect().top -
    scrollEl.getBoundingClientRect().top -
    12
  scrollEl.scrollTo({ top: Math.max(0, scrollTop), behavior: 'smooth' })
  history.replaceState(null, '', `#${encodeURIComponent(target.id || TOC_HEADING_IDS[0])}`)
}

function sanitizeHtml(input: string): string {
  return input
    .replace(/<script[\s\S]*?>[\s\S]*?<\/script>/gi, '')
    .replace(/\son\w+="[^"]*"/gi, '')
    .replace(/\son\w+='[^']*'/gi, '')
    .replace(/<iframe[\s\S]*?>[\s\S]*?<\/iframe>/gi, '')
}

function selectManual(slug: string) {
  router.replace({ params: { slug } })
}

async function loadDocument() {
  loading.value = true
  loadError.value = ''
  renderedHtml.value = ''
  pdfUrl.value = ''
  unbindAnchorNav?.()
  unbindAnchorNav = null

  const entry = manual.value
  if (!entry) {
    loadError.value = t('operationManual.notFound')
    loading.value = false
    return
  }

  try {
    if (entry.pdfFile) {
      const url = getManualPdfUrl(entry.pdfFile)
      if (!url) {
        throw new Error(`manual pdf not found: ${entry.pdfFile}`)
      }
      pdfUrl.value = url
      return
    }
    if (!entry.docFile) {
      throw new Error('manual source missing')
    }
    const mdText = getManualMarkdown(entry.docFile)
    if (!mdText) {
      throw new Error(`manual not found: ${entry.docFile}`)
    }
    renderedHtml.value = sanitizeHtml(
      renderHelpMarkdown(normalizeManualMarkdown(mdText)),
    )
  } catch (e: unknown) {
    console.error(e)
    loadError.value = t('operationManual.loadFailed')
    ElMessage.error(loadError.value)
  } finally {
    loading.value = false
  }
}

watch(
  () => [loading.value, renderedHtml.value] as const,
  async ([isLoading]) => {
    if (isLoading) return
    await nextTick()
    unbindAnchorNav?.()
    unbindAnchorNav = bindHelpContentAnchorNav(helpContentEl.value)
    scrollHelpToHash()
  },
  { flush: 'post' },
)

watch(activeSlug, () => {
  loadDocument()
  const el = document.querySelector('.manual-content')
  if (el) el.scrollTop = 0
})

onMounted(() => {
  if (!route.params.slug && manuals[0]) {
    router.replace({ params: { slug: manuals[0].slug } })
  }
  loadDocument()
})

onUnmounted(() => {
  unbindAnchorNav?.()
})

function handlePrint() {
  if (loading.value || loadError.value) {
    ElMessage.warning(t('operationManual.loading'))
    return
  }
  if (pdfUrl.value) {
    const frameWindow = pdfFrameEl.value?.contentWindow
    if (frameWindow) {
      frameWindow.focus()
      frameWindow.print()
      return
    }
    window.open(pdfUrl.value, '_blank', 'noopener,noreferrer')
    return
  }
  runBrowserPrint(manualScrollEl.value)
}
</script>

<style scoped lang="scss">
@use '@/styles/help-markdown-page.scss';

.manual-home {
  display: flex;
  height: 100vh;
  background: linear-gradient(180deg, #eef0ff 0%, #f6f7fb 220px, #f6f7fb 100%);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

/* ---------- サイドバー ---------- */
.manual-sidebar {
  width: 248px;
  min-width: 248px;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #1e1b4b 0%, #312e81 45%, #3730a3 100%);
  color: #e0e7ff;
  box-shadow: 2px 0 12px rgba(15, 23, 42, 0.16);
  z-index: 1;
}

.manual-sidebar__header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.manual-sidebar__logo {
  width: 30px;
  height: 30px;
  border-radius: 9px;
  color: #fff;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.24);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.25);
}

.manual-sidebar__title {
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: #fff;
}

.manual-sidebar__nav {
  flex: 1;
  overflow-y: auto;
  padding: 8px 8px 10px;
}

.manual-sidebar__group + .manual-sidebar__group {
  margin-top: 8px;
}

.manual-sidebar__group-title {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0 0 4px;
  padding: 4px 8px;
  font-size: 10.5px;
  font-weight: 800;
  letter-spacing: 0.08em;
  color: #c7d2fe;
}

.manual-sidebar__group-title::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #a5b4fc;
}

.manual-sidebar__item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  margin-bottom: 2px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 12.5px;
  line-height: 1.35;
  color: rgba(224, 231, 255, 0.88);
  border: 1px solid transparent;
  transition:
    background-color 0.15s ease,
    color 0.15s ease;
}

.manual-sidebar__item .el-icon {
  flex-shrink: 0;
  color: #a5b4fc;
}

.manual-sidebar__item:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.1);
}

.manual-sidebar__item--active,
.manual-sidebar__item--active:hover {
  color: #3730a3;
  font-weight: 700;
  background: #fff;
  border-color: #fff;
  box-shadow:
    inset 0 -2px 0 rgba(79, 70, 229, 0.16),
    0 3px 8px -4px rgba(15, 23, 42, 0.5);
}

.manual-sidebar__item--active .el-icon {
  color: #4f46e5;
}

.manual-sidebar__item-text {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.manual-sidebar__pdf-tag {
  flex-shrink: 0;
  padding: 0 6px;
  border-radius: 999px;
  font-size: 9.5px;
  font-weight: 800;
  line-height: 16px;
  letter-spacing: 0.04em;
  color: #92400e;
  background: #fde68a;
}

.manual-sidebar__footer {
  display: flex;
  gap: 8px;
  padding: 8px 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.manual-sidebar__footer .manual-sidebar__print-btn {
  --k-rgb: 79 70 229;
  flex: 1;
  height: 30px;
  border-radius: 999px;
  font-weight: 700;
  color: #3730a3;
  border: 1px solid #fff;
  background: linear-gradient(180deg, #ffffff 0%, #eef2ff 100%);
}

.manual-sidebar__footer .manual-sidebar__print-btn:hover,
.manual-sidebar__footer .manual-sidebar__print-btn:focus-visible {
  color: #312e81;
  border-color: #fff;
  background: linear-gradient(180deg, #ffffff 0%, #e0e7ff 100%);
}

.manual-sidebar__print-btn .el-icon {
  margin-right: 4px;
}

/* ---------- 本文 ---------- */
.manual-content {
  position: relative;
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  padding: 14px 18px;
  scroll-behavior: smooth;
}

.manual-content__loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 40px 10px;
  color: #475569;
  font-size: 14px;
}

.manual-content__spinner {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid rgba(79, 70, 229, 0.2);
  border-top-color: #4f46e5;
  animation: mc-spin 1s linear infinite;
}

@keyframes mc-spin {
  to {
    transform: rotate(360deg);
  }
}

.manual-content__error {
  padding: 32px 20px;
  text-align: center;
  color: #64748b;
}

.manual-content__header {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
  border-radius: 14px;
  color: #fff;
  background: linear-gradient(125deg, #312e81 0%, #4338ca 36%, #4f46e5 66%, #2563eb 100%);
  box-shadow: 0 8px 20px -12px rgba(49, 46, 129, 0.5);
}

.manual-content__title-badge {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

.manual-content__copy {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.manual-content__title {
  margin: 0;
  font-weight: 800;
  letter-spacing: 0.01em;
  color: #fff;
}

.manual-content__subtitle {
  margin: 0;
  color: rgba(224, 231, 255, 0.92);
}

.manual-content__kind {
  flex-shrink: 0;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.06em;
  color: #92400e;
  background: #fff;
  box-shadow: inset 0 -2px 0 rgba(217, 119, 6, 0.18);
}

.manual-content__body {
  position: relative;
  overflow: hidden;
  padding: 14px 20px 10px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #e0e7ff;
  box-shadow: 0 6px 18px -12px rgba(49, 46, 129, 0.25);
  line-height: 1.7;
  color: #1e293b;
  font-size: 14px;
}

.manual-content__body::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #4f46e5, #2563eb);
}

/* Markdown の余白をこのページだけ詰める */
.manual-content__body.help-content > :deep(:first-child) {
  margin-top: 0;
}

.manual-content__body.help-content :deep(p) {
  margin: 0 0 8px;
}

.manual-content__body.help-content :deep(h1),
.manual-content__body.help-content :deep(h2) {
  margin: 16px 0 8px;
  padding: 4px 10px;
  font-size: 16px;
  color: #312e81;
  border-left: 4px solid #4f46e5;
  border-radius: 0 8px 8px 0;
  background: linear-gradient(90deg, #eef2ff 0%, rgba(238, 242, 255, 0) 80%);
}

.manual-content__body.help-content :deep(h3),
.manual-content__body.help-content :deep(h4) {
  margin: 12px 0 6px;
  padding-left: 8px;
  font-size: 14px;
  color: #3730a3;
  border-left: 3px solid #a5b4fc;
}

.manual-content__body.help-content :deep(ul),
.manual-content__body.help-content :deep(ol) {
  margin: 0 0 8px;
  padding-left: 20px;
}

.manual-content__body.help-content :deep(li) {
  margin: 2px 0;
}

.manual-content__body.help-content :deep(li::marker) {
  color: #6366f1;
}

.manual-content__body.help-content :deep(blockquote) {
  margin: 8px 0;
  padding: 8px 12px;
  border-left: 4px solid #6366f1;
  background: #f5f7ff;
  border-radius: 8px;
}

.manual-content__body.help-content :deep(blockquote > :last-child) {
  margin-bottom: 0;
}

.manual-content__body.help-content :deep(hr) {
  margin: 12px 0;
  border-top-color: #e2e8f0;
}

.manual-content__body.help-content :deep(table) {
  margin: 8px 0 10px;
  border-radius: 8px;
}

.manual-content__body.help-content :deep(th),
.manual-content__body.help-content :deep(td) {
  padding: 6px 10px;
  border-color: #e2e8f0;
}

.manual-content__body.help-content :deep(th) {
  color: #312e81;
  background: #eef2ff;
}

.manual-content__body.help-content :deep(tr:nth-child(even) td) {
  background: #fafbff;
}

.manual-content__body.help-content :deep(img) {
  margin: 4px 0;
  border-radius: 8px;
  box-shadow: 0 4px 14px -6px rgba(2, 6, 23, 0.25);
}

.manual-content__body.help-content :deep(code) {
  color: #4338ca;
  background: #eef2ff;
  border-radius: 6px;
}

.manual-toc-fab {
  --k-rgb: 79 70 229;
  position: fixed;
  right: 28px;
  bottom: 22px;
  z-index: 20;
  height: 38px;
  padding: 0 16px;
  border-radius: 999px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: #fff;
  border: 1px solid #3730a3;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #6366f1, #4338ca);
}

.manual-toc-fab:hover,
.manual-toc-fab:focus-visible {
  color: #fff;
  border-color: #312e81;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.28) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #818cf8, #4f46e5);
}

.manual-toc-fab .el-icon {
  margin-right: 6px;
  font-size: 15px;
}

.manual-toc-fab__label {
  font-size: 12px;
}

.manual-print-area {
  width: 100%;
}

.manual-print-area--pdf {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 28px);
}

.manual-pdf {
  flex: 1;
  width: 100%;
  min-height: 0;
  border: 1px solid #e0e7ff;
  border-radius: 12px;
  background: #fff;
}

@media (max-width: 768px) {
  .manual-home {
    flex-direction: column;
  }
  .manual-sidebar {
    width: 100%;
    min-width: 0;
    max-height: 200px;
  }
  .manual-content {
    padding: 10px;
  }
  .manual-toc-fab {
    right: 16px;
    bottom: 16px;
    padding: 0 14px;
  }
}

@media print {
  .manual-toc-fab {
    display: none !important;
  }

  .manual-content__header {
    color: #0f172a !important;
    background: #fff !important;
    box-shadow: none !important;
    border-bottom: 2px solid #4f46e5;
    border-radius: 0 !important;
  }

  .manual-content__fx,
  .manual-content__kind {
    display: none !important;
  }

  .manual-content__title-badge {
    color: #4f46e5;
    background: #eef2ff;
    border-color: #c7d2fe;
  }

  .manual-content__title,
  .manual-content__subtitle {
    color: #0f172a !important;
  }

  .manual-content__body::before {
    display: none;
  }
}
</style>
