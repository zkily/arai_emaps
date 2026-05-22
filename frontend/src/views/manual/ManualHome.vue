<template>
  <div class="manual-home">
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
          </div>
        </section>
      </nav>
      <div class="manual-sidebar__footer">
        <el-button
          class="manual-sidebar__print-btn"
          type="default"
          plain
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
      <div v-else class="manual-print-area">
        <div class="manual-content__header">
          <div class="manual-content__title-badge">
            <el-icon :size="20"><QuestionFilled /></el-icon>
          </div>
          <div>
            <h1 class="manual-content__title">{{ currentTitle }}</h1>
            <p class="manual-content__subtitle">{{ t('operationManual.subtitle') }}</p>
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
        type="primary"
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
import { getManualMarkdown, normalizeManualMarkdown } from '@/views/manual/manualAssets'
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
const manualScrollEl = ref<HTMLElement | null>(null)
const helpContentEl = ref<HTMLElement | null>(null)
let unbindAnchorNav: (() => void) | null = null

const showTocFab = computed(
  () => !loading.value && !loadError.value && Boolean(renderedHtml.value),
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
  unbindAnchorNav?.()
  unbindAnchorNav = null

  const entry = manual.value
  if (!entry) {
    loadError.value = t('operationManual.notFound')
    loading.value = false
    return
  }

  try {
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
  runBrowserPrint(manualScrollEl.value)
}
</script>

<style scoped lang="scss">
@use '@/styles/help-markdown-page.scss';

.manual-home {
  display: flex;
  height: 100vh;
  background: #f0f2f5;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.manual-sidebar {
  width: 280px;
  min-width: 280px;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #1e1b4b 0%, #312e81 40%, #3730a3 100%);
  color: #e0e7ff;
  box-shadow: 4px 0 24px rgba(15, 23, 42, 0.18);
  z-index: 1;
}

.manual-sidebar__header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 20px 18px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.manual-sidebar__logo {
  color: #a5b4fc;
}

.manual-sidebar__title {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #fff;
}

.manual-sidebar__nav {
  flex: 1;
  overflow-y: auto;
  padding: 12px 10px 16px;
}

.manual-sidebar__group + .manual-sidebar__group {
  margin-top: 14px;
}

.manual-sidebar__group-title {
  margin: 0 0 6px;
  padding: 0 8px 6px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: none;
  color: rgba(199, 210, 254, 0.75);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.manual-sidebar__item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  margin-bottom: 4px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.2s ease, color 0.2s ease, transform 0.15s ease;
  color: rgba(224, 231, 255, 0.85);
  font-size: 13.5px;
  line-height: 1.4;
}

.manual-sidebar__item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  transform: translateX(2px);
}

.manual-sidebar__item--active {
  background: rgba(99, 102, 241, 0.35);
  color: #fff;
  font-weight: 600;
  box-shadow: inset 0 0 0 1px rgba(165, 180, 252, 0.3);
}

.manual-sidebar__item--active:hover {
  background: rgba(99, 102, 241, 0.45);
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

.manual-sidebar__footer {
  padding: 14px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  gap: 8px;
}

.manual-sidebar__footer .el-button {
  flex: 1;
  border-radius: 8px;
}

.manual-content {
  position: relative;
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  padding: 28px 36px;
  scroll-behavior: smooth;
}

.manual-toc-fab {
  position: fixed;
  right: 36px;
  bottom: 28px;
  z-index: 20;
  height: 44px;
  padding: 0 18px;
  border-radius: 22px;
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.35), 0 2px 8px rgba(15, 23, 42, 0.12);
  font-weight: 600;
  letter-spacing: 0.02em;
}

.manual-toc-fab .el-icon {
  margin-right: 6px;
  font-size: 16px;
}

.manual-toc-fab__label {
  font-size: 13px;
}

@media (max-width: 768px) {
  .manual-toc-fab {
    right: 16px;
    bottom: 16px;
    padding: 0 14px;
  }

  .manual-toc-fab__label {
    font-size: 12px;
  }
}

@media print {
  .manual-toc-fab {
    display: none !important;
  }
}

.manual-content__loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 60px 10px;
  color: #475569;
  font-size: 14px;
}

.manual-content__spinner {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid rgba(64, 158, 255, 0.25);
  border-top-color: rgba(64, 158, 255, 0.95);
  animation: mc-spin 1s linear infinite;
}

@keyframes mc-spin {
  to { transform: rotate(360deg); }
}

.manual-content__error {
  padding: 40px 20px;
  text-align: center;
  color: #64748b;
}

.manual-content__header {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 20px;
}

.manual-content__title-badge {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(64, 158, 255, 0.1);
  border: 1px solid rgba(64, 158, 255, 0.18);
  color: #409eff;
  flex-shrink: 0;
}

.manual-content__title {
  margin: 0;
  font-size: 20px;
  font-weight: 750;
  color: #0f172a;
}

.manual-content__subtitle {
  margin: 3px 0 0;
  font-size: 13px;
  color: #64748b;
}

.manual-content__body {
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(148, 163, 184, 0.3);
  border-radius: 16px;
  padding: 24px 28px;
  line-height: 1.8;
  color: #0f172a;
  font-size: 14px;
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
    padding: 16px;
  }
}

.manual-print-area {
  width: 100%;
}
</style>
