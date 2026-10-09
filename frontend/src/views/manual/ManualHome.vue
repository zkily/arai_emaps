<template>
  <div class="manual-home pb-std">
    <aside class="manual-sidebar">
      <div class="manual-sidebar__bubbles" aria-hidden="true">
        <span v-for="n in 9" :key="n" class="manual-sidebar__bubble" />
      </div>
      <div class="manual-sidebar__header">
        <el-icon class="manual-sidebar__logo" :size="18"><Notebook /></el-icon>
        <span class="manual-sidebar__title">{{ t('operationManual.homeTitle') }}</span>
      </div>
      <div class="manual-sidebar__filter">
        <el-input
          v-model="filterKeyword"
          size="small"
          clearable
          :prefix-icon="Search"
          :placeholder="t('operationManual.filterPlaceholder')"
        />
      </div>
      <el-scrollbar class="manual-sidebar__scroll">
        <nav class="manual-sidebar__nav">
          <div
            v-for="section in filteredSections"
            :key="section.category"
            class="manual-sidebar__section"
            :class="`manual-sidebar__section--${section.category}`"
          >
            <ManualMenuTreeItem
              :node="section.node"
              :active-slug="activeSlug"
              :collapsed-keys="filterKeyword.trim() ? [] : collapsedKeys"
              @select="selectManual"
              @toggle="toggleFolder"
            />
          </div>
          <p v-if="!filteredSections.length" class="manual-sidebar__empty">
            {{ t('operationManual.filterEmpty') }}
          </p>
        </nav>
      </el-scrollbar>
      <div class="manual-sidebar__footer">
        <el-button
          class="manual-sidebar__print-btn"
          size="small"
          :disabled="!activeSlug"
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
      <div v-else-if="!activeSlug" class="manual-welcome">
        <div class="manual-content__header pb-hero pb-hero--page">
          <div class="manual-content__fx pb-bubbles" aria-hidden="true" />
          <div class="manual-content__title-badge">
            <el-icon :size="20"><Notebook /></el-icon>
          </div>
          <div class="manual-content__copy">
            <h1 class="manual-content__title pb-hero-title">{{ t('operationManual.homeTitle') }}</h1>
            <p class="manual-content__subtitle pb-hero-desc">
              {{ t('operationManual.welcomeSubtitle') }}
            </p>
          </div>
        </div>
        <div class="mw-stats">
          <div v-for="stat in welcomeStats" :key="stat.key" class="mw-stat" :class="`mw-stat--${stat.key}`">
            <div class="mw-stat__icon">
              <el-icon :size="20"><component :is="stat.icon" /></el-icon>
            </div>
            <div class="mw-stat__body">
              <div class="mw-stat__value">
                {{ stat.value }}<span class="mw-stat__unit">{{ stat.unit }}</span>
              </div>
              <div class="mw-stat__label">{{ stat.label }}</div>
            </div>
          </div>
        </div>

        <section class="mw-section">
          <h2 class="mw-section__title">{{ t('operationManual.welcomeStepsTitle') }}</h2>
          <div class="mw-steps">
            <div v-for="(step, index) in welcomeSteps" :key="step.key" class="mw-step">
              <span class="mw-step__no">{{ index + 1 }}</span>
              <div class="mw-step__icon">
                <el-icon :size="22"><component :is="step.icon" /></el-icon>
              </div>
              <h3 class="mw-step__title">{{ step.title }}</h3>
              <p class="mw-step__desc">{{ step.desc }}</p>
            </div>
          </div>
        </section>

        <section class="mw-section">
          <h2 class="mw-section__title">{{ t('operationManual.welcomeCategoriesTitle') }}</h2>
          <div class="mw-cats">
            <div
              v-for="section in welcomeSections"
              :key="section.category"
              class="mw-cat"
              :class="`mw-cat--${section.category}`"
            >
              <div class="mw-cat__head">
                <span class="mw-cat__name">{{ section.name }}</span>
                <span class="mw-cat__count">
                  {{ section.items.length }}{{ t('operationManual.welcomeItemsUnit') }}
                </span>
              </div>
              <ul class="mw-cat__list">
                <li
                  v-for="item in section.items"
                  :key="item.manual.slug"
                  class="mw-cat__item"
                  role="button"
                  tabindex="0"
                  @click="selectManual(item.manual.slug)"
                  @keydown.enter.prevent="selectManual(item.manual.slug)"
                >
                  <div class="mw-cat__item-main">
                    <span class="mw-cat__item-title">{{ item.manual.pageTitle }}</span>
                    <span v-if="item.path" class="mw-cat__item-path">{{ item.path }}</span>
                  </div>
                  <span v-if="item.manual.pdfFile" class="mw-cat__item-pdf">PDF</span>
                  <el-icon class="mw-cat__item-arrow"><ArrowRight /></el-icon>
                </li>
              </ul>
            </div>
          </div>
        </section>
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
import { ArrowRight, Notebook, Printer, QuestionFilled, Search, Top } from '@element-plus/icons-vue'
import {
  OPERATION_MANUAL_CATEGORY_I18N_KEY,
  type OperationManualCategory,
  type OperationManualEntry,
  type OperationManualTreeNode,
  getOperationManualBySlug,
  getOperationManualNavGroups,
  toOperationManualLeafNode,
} from '@/config/operationManuals'
import ManualMenuTreeItem from '@/views/manual/ManualMenuTreeItem.vue'
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
const { t, te } = useI18n()

const manualNavGroups = getOperationManualNavGroups()

/** 未選択（slug なし）のときは案内のみ表示する */
const activeSlug = computed(() => String(route.params.slug ?? ''))
const manual = computed(() => getOperationManualBySlug(activeSlug.value))
const currentTitle = computed(() => manual.value?.pageTitle ?? t('operationManual.unknownTitle'))

interface ManualSidebarSection {
  category: OperationManualCategory
  node: OperationManualTreeNode
}

const filterKeyword = ref('')
/** 閉じているフォルダのキー（既定は空＝全展開。絞り込み中は無視して全展開） */
const collapsedKeys = ref<string[]>([])

function toggleFolder(key: string) {
  collapsedKeys.value = collapsedKeys.value.includes(key)
    ? collapsedKeys.value.filter((k) => k !== key)
    : [...collapsedKeys.value, key]
}

/** フォルダ名を menu.<CODE> の翻訳に置き換える */
function localizeTree(nodes: OperationManualTreeNode[]): OperationManualTreeNode[] {
  return nodes.map((node) => {
    const key = `menu.${node.menuCode ?? ''}`
    return {
      ...node,
      name: node.menuCode && te(key) ? t(key) : node.name,
      children: localizeTree(node.children),
    }
  })
}

const sidebarSections = computed<ManualSidebarSection[]>(() =>
  manualNavGroups.map((group, index) => ({
    category: group.category,
    node: {
      key: `category:${group.category}`,
      name: t(OPERATION_MANUAL_CATEGORY_I18N_KEY[group.category]),
      sortOrder: index,
      children: localizeTree(group.tree ?? group.items.map(toOperationManualLeafNode)),
    },
  })),
)

/** 分類名・親メニュー名・マニュアル名・slug のいずれかに一致するものを残す（親が一致したら配下は全件） */
function filterTreeNode(
  node: OperationManualTreeNode,
  keyword: string,
  ancestorMatched: boolean,
): OperationManualTreeNode | null {
  if (node.manual) {
    const hit =
      ancestorMatched ||
      node.manual.pageTitle.toLowerCase().includes(keyword) ||
      node.manual.slug.toLowerCase().includes(keyword)
    return hit ? node : null
  }
  const selfMatched = ancestorMatched || node.name.toLowerCase().includes(keyword)
  const children = node.children
    .map((child) => filterTreeNode(child, keyword, selfMatched))
    .filter((child): child is OperationManualTreeNode => child !== null)
  return children.length ? { ...node, children } : null
}

const filteredSections = computed<ManualSidebarSection[]>(() => {
  const keyword = filterKeyword.value.trim().toLowerCase()
  if (!keyword) return sidebarSections.value
  return sidebarSections.value.flatMap((section) => {
    const node = filterTreeNode(section.node, keyword, false)
    return node ? [{ ...section, node }] : []
  })
})

interface WelcomeManualItem {
  manual: OperationManualEntry
  /** 親メニューのパンくず（ページ操作関連のみ） */
  path: string
}

function collectWelcomeItems(nodes: OperationManualTreeNode[], trail: string[]): WelcomeManualItem[] {
  return nodes.flatMap((node) =>
    node.manual
      ? [{ manual: node.manual, path: trail.join(' › ') }]
      : collectWelcomeItems(node.children, [...trail, node.name]),
  )
}

const welcomeSections = computed(() =>
  sidebarSections.value.map((section) => ({
    category: section.category,
    name: section.node.name,
    items: collectWelcomeItems(section.node.children, []),
  })),
)

const welcomeStats = computed(() => {
  const items = welcomeSections.value.flatMap((s) => s.items)
  const unit = t('operationManual.welcomeItemsUnit')
  return [
    { key: 'total', icon: 'Reading', value: items.length, unit, label: t('operationManual.welcomeStatTotal') },
    {
      key: 'pdf',
      icon: 'Document',
      value: items.filter((i) => i.manual.pdfFile).length,
      unit,
      label: t('operationManual.welcomeStatPdf'),
    },
    {
      key: 'category',
      icon: 'Files',
      value: welcomeSections.value.length,
      unit: '',
      label: t('operationManual.welcomeStatCategory'),
    },
  ]
})

const welcomeSteps = computed(() => [
  {
    key: 'select',
    icon: 'Pointer',
    title: t('operationManual.welcomeStepSelect'),
    desc: t('operationManual.welcomeSelect'),
  },
  {
    key: 'filter',
    icon: 'Search',
    title: t('operationManual.welcomeStepFilter'),
    desc: t('operationManual.welcomeFilter'),
  },
  {
    key: 'print',
    icon: 'Printer',
    title: t('operationManual.welcomeStepPrint'),
    desc: t('operationManual.welcomePdf'),
  },
])

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

  if (!activeSlug.value) {
    loading.value = false
    return
  }

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

/* ---------- サイドバー（淡色＋バブル装飾） ---------- */
.manual-sidebar {
  position: relative;
  overflow: hidden;
  width: 260px;
  min-width: 260px;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #f5f3ff 0%, #eef2ff 45%, #ecfeff 100%);
  border-right: 1px solid #e0e7ff;
  box-shadow: 4px 0 18px -10px rgba(79, 70, 229, 0.28);
  z-index: 1;
}

.manual-sidebar > :not(.manual-sidebar__bubbles) {
  position: relative;
  z-index: 1;
}

/* バブル装飾 */
.manual-sidebar__bubbles {
  position: absolute;
  inset: 0;
  z-index: 0;
  overflow: hidden;
  pointer-events: none;
}

.manual-sidebar__bubble {
  position: absolute;
  border-radius: 50%;
  background: radial-gradient(
    circle at 30% 30%,
    rgba(255, 255, 255, 0.95) 0%,
    rgba(var(--bb-rgb, 165, 180, 252), 0.35) 45%,
    rgba(var(--bb-rgb, 165, 180, 252), 0.12) 100%
  );
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.7),
    0 6px 16px -8px rgba(var(--bb-rgb, 165, 180, 252), 0.6);
  animation: manual-bubble-float 14s ease-in-out infinite;
}

.manual-sidebar__bubble:nth-child(1) {
  --bb-rgb: 196, 181, 253;
  width: 120px;
  height: 120px;
  top: -36px;
  right: -40px;
}
.manual-sidebar__bubble:nth-child(2) {
  --bb-rgb: 165, 180, 252;
  width: 46px;
  height: 46px;
  top: 120px;
  left: 14px;
  animation-delay: -3s;
  animation-duration: 11s;
}
.manual-sidebar__bubble:nth-child(3) {
  --bb-rgb: 103, 232, 249;
  width: 22px;
  height: 22px;
  top: 210px;
  right: 30px;
  animation-delay: -6s;
  animation-duration: 9s;
}
.manual-sidebar__bubble:nth-child(4) {
  --bb-rgb: 249, 168, 212;
  width: 70px;
  height: 70px;
  top: 38%;
  right: -18px;
  animation-delay: -2s;
  animation-duration: 16s;
}
.manual-sidebar__bubble:nth-child(5) {
  --bb-rgb: 196, 181, 253;
  width: 16px;
  height: 16px;
  top: 48%;
  left: 36px;
  animation-delay: -8s;
  animation-duration: 10s;
}
.manual-sidebar__bubble:nth-child(6) {
  --bb-rgb: 134, 239, 172;
  width: 34px;
  height: 34px;
  top: 62%;
  left: -8px;
  animation-delay: -5s;
  animation-duration: 13s;
}
.manual-sidebar__bubble:nth-child(7) {
  --bb-rgb: 103, 232, 249;
  width: 96px;
  height: 96px;
  bottom: 60px;
  left: -34px;
  animation-delay: -9s;
  animation-duration: 18s;
}
.manual-sidebar__bubble:nth-child(8) {
  --bb-rgb: 253, 230, 138;
  width: 26px;
  height: 26px;
  bottom: 140px;
  right: 44px;
  animation-delay: -4s;
  animation-duration: 12s;
}
.manual-sidebar__bubble:nth-child(9) {
  --bb-rgb: 165, 180, 252;
  width: 58px;
  height: 58px;
  bottom: -16px;
  right: 20px;
  animation-delay: -7s;
  animation-duration: 15s;
}

@keyframes manual-bubble-float {
  0%,
  100% {
    transform: translate(0, 0) scale(1);
  }
  33% {
    transform: translate(6px, -14px) scale(1.04);
  }
  66% {
    transform: translate(-6px, -6px) scale(0.97);
  }
}

@media (prefers-reduced-motion: reduce) {
  .manual-sidebar__bubble {
    animation: none;
  }
}

.manual-sidebar__header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  height: 48px;
  flex-shrink: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.85) 0%, rgba(238, 242, 255, 0.6) 100%);
  backdrop-filter: blur(4px);
}

.manual-sidebar__header::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 2px;
  background: linear-gradient(90deg, #a855f7, #f43f5e, #06b6d4, #f59e0b, #10b981, #60a5fa);
  opacity: 0.6;
  pointer-events: none;
}

.manual-sidebar__logo {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  color: #fff;
  background: linear-gradient(135deg, #818cf8 0%, #a78bfa 100%);
  box-shadow: 0 4px 12px rgba(129, 140, 248, 0.45);
}

.manual-sidebar__title {
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: #312e81;
  white-space: nowrap;
}

.manual-sidebar__filter {
  flex-shrink: 0;
  padding: 10px 10px 4px;
}

.manual-sidebar__filter :deep(.el-input__wrapper) {
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.85);
  box-shadow:
    inset 0 0 0 1px #c7d2fe,
    0 2px 8px -4px rgba(79, 70, 229, 0.25);
}

.manual-sidebar__filter :deep(.el-input__wrapper.is-focus) {
  box-shadow:
    inset 0 0 0 1px #818cf8,
    0 0 0 3px rgba(129, 140, 248, 0.18);
}

.manual-sidebar__filter :deep(.el-input__inner) {
  color: #1e293b;
}

.manual-sidebar__filter :deep(.el-input__inner::placeholder) {
  color: #94a3b8;
}

.manual-sidebar__filter :deep(.el-input__prefix),
.manual-sidebar__filter :deep(.el-input__suffix) {
  color: #818cf8;
}

.manual-sidebar__scroll {
  flex: 1;
  overflow: hidden;
}

.manual-sidebar__scroll :deep(.el-scrollbar__bar.is-vertical) {
  width: 4px;
  right: 2px;
}

.manual-sidebar__scroll :deep(.el-scrollbar__thumb) {
  background: rgba(99, 102, 241, 0.25);
  border-radius: 2px;
}

.manual-sidebar__nav {
  padding: 6px 8px 10px;
}

.manual-sidebar__section + .manual-sidebar__section {
  margin-top: 6px;
}

/* 分類ごとのアクセントカラー（ManualMenuTreeItem が --sc / --sc-rgb を参照。案内ページの分類カードと同色） */
.manual-sidebar__section--pageOperation {
  --sc: #a855f7;
  --sc-rgb: 168, 85, 247;
}
.manual-sidebar__section--planning {
  --sc: #f43f5e;
  --sc-rgb: 244, 63, 94;
}
.manual-sidebar__section--instructionActual {
  --sc: #d97706;
  --sc-rgb: 217, 119, 6;
}
.manual-sidebar__section--mes {
  --sc: #0891b2;
  --sc-rgb: 8, 145, 178;
}

.manual-sidebar__empty {
  margin: 16px 0;
  text-align: center;
  font-size: 12px;
  color: #64748b;
}

.manual-sidebar__footer {
  display: flex;
  padding: 8px 10px;
  border-top: 1px solid rgba(199, 210, 254, 0.7);
  background: rgba(255, 255, 255, 0.55);
  backdrop-filter: blur(4px);
}

.manual-sidebar__footer .manual-sidebar__print-btn {
  flex: 1;
  height: 30px;
  border-radius: 999px;
  font-weight: 700;
  color: #4338ca;
  border: 1px solid #c7d2fe;
  background: linear-gradient(180deg, #ffffff 0%, #eef2ff 100%);
}

.manual-sidebar__footer .manual-sidebar__print-btn:hover,
.manual-sidebar__footer .manual-sidebar__print-btn:focus-visible {
  color: #312e81;
  border-color: #a5b4fc;
  background: linear-gradient(180deg, #ffffff 0%, #e0e7ff 100%);
}

.manual-sidebar__footer .manual-sidebar__print-btn.is-disabled {
  color: #a5b4fc;
  border-color: #e0e7ff;
  background: rgba(255, 255, 255, 0.6);
}

.manual-sidebar__print-btn span {
  margin-left: 4px;
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

/* ---------- 未選択時の案内ページ ---------- */
.manual-welcome {
  max-width: 1280px;
}

/* 統計 */
.mw-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}

.mw-stat {
  --mw-rgb: 99, 102, 241;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 14px;
  background: #fff;
  border: 1px solid rgba(var(--mw-rgb), 0.18);
  box-shadow: 0 8px 20px -14px rgba(var(--mw-rgb), 0.55);
}

.mw-stat::after {
  content: '';
  position: absolute;
  right: -28px;
  top: -28px;
  width: 96px;
  height: 96px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(var(--mw-rgb), 0.16) 0%, rgba(var(--mw-rgb), 0) 70%);
  pointer-events: none;
}

.mw-stat--pdf {
  --mw-rgb: 217, 119, 6;
}

.mw-stat--category {
  --mw-rgb: 16, 185, 129;
}

.mw-stat__icon {
  flex-shrink: 0;
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.25) 0%, rgba(255, 255, 255, 0) 55%),
    rgb(var(--mw-rgb));
  box-shadow: 0 6px 14px -6px rgba(var(--mw-rgb), 0.8);
}

.mw-stat__value {
  font-size: 24px;
  font-weight: 800;
  line-height: 1.1;
  color: #0f172a;
}

.mw-stat__unit {
  margin-left: 2px;
  font-size: 12px;
  font-weight: 700;
  color: #64748b;
}

.mw-stat__label {
  margin-top: 2px;
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
}

/* セクション見出し */
.mw-section + .mw-section {
  margin-top: 20px;
}

.mw-section__title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 10px;
  font-size: 15px;
  font-weight: 800;
  color: #312e81;
}

.mw-section__title::before {
  content: '';
  width: 4px;
  height: 16px;
  border-radius: 4px;
  background: linear-gradient(180deg, #6366f1, #2563eb);
}

/* ご利用の流れ */
.mw-steps {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.mw-step {
  position: relative;
  padding: 16px 16px 14px;
  border-radius: 14px;
  background: linear-gradient(180deg, #ffffff 0%, #f8faff 100%);
  border: 1px solid #e0e7ff;
  box-shadow: 0 6px 18px -14px rgba(49, 46, 129, 0.45);
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease;
}

.mw-step:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 24px -14px rgba(49, 46, 129, 0.5);
}

.mw-step__no {
  position: absolute;
  top: 12px;
  right: 14px;
  font-size: 28px;
  font-weight: 900;
  line-height: 1;
  color: rgba(99, 102, 241, 0.14);
}

.mw-step__icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 10px;
  color: #4f46e5;
  background: #eef2ff;
  box-shadow: inset 0 0 0 1px #c7d2fe;
}

.mw-step__title {
  margin: 0 0 4px;
  font-size: 14px;
  font-weight: 800;
  color: #1e293b;
}

.mw-step__desc {
  margin: 0;
  font-size: 12.5px;
  line-height: 1.65;
  color: #475569;
}

/* 分類別一覧（左メニューの分類色と合わせる） */
.mw-cats {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 12px;
  align-items: start;
}

.mw-cat {
  --mw-rgb: 99, 102, 241;
  overflow: hidden;
  border-radius: 14px;
  background: #fff;
  border: 1px solid rgba(var(--mw-rgb), 0.22);
  box-shadow: 0 8px 20px -16px rgba(var(--mw-rgb), 0.7);
}

.mw-cat--pageOperation {
  --mw-rgb: 168, 85, 247;
}
.mw-cat--planning {
  --mw-rgb: 244, 63, 94;
}
.mw-cat--instructionActual {
  --mw-rgb: 217, 119, 6;
}
.mw-cat--mes {
  --mw-rgb: 8, 145, 178;
}

.mw-cat__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 10px 14px;
  border-top: 3px solid rgb(var(--mw-rgb));
  background: linear-gradient(90deg, rgba(var(--mw-rgb), 0.12) 0%, rgba(var(--mw-rgb), 0.02) 100%);
}

.mw-cat__name {
  font-size: 14px;
  font-weight: 800;
  color: rgb(var(--mw-rgb));
}

.mw-cat__count {
  flex-shrink: 0;
  padding: 1px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
  color: #fff;
  background: rgb(var(--mw-rgb));
}

.mw-cat__list {
  margin: 0;
  padding: 6px;
  list-style: none;
}

.mw-cat__item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 10px;
  border-radius: 10px;
  cursor: pointer;
  outline: none;
  transition:
    background-color 0.15s ease,
    transform 0.15s ease;
}

.mw-cat__item + .mw-cat__item {
  margin-top: 2px;
}

.mw-cat__item:hover,
.mw-cat__item:focus-visible {
  background: rgba(var(--mw-rgb), 0.08);
  transform: translateX(2px);
}

.mw-cat__item-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.mw-cat__item-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  font-weight: 700;
  color: #1e293b;
}

.mw-cat__item-path {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 11px;
  color: #94a3b8;
}

.mw-cat__item-pdf {
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

.mw-cat__item-arrow {
  flex-shrink: 0;
  font-size: 12px;
  color: #cbd5e1;
  transition: color 0.15s ease;
}

.mw-cat__item:hover .mw-cat__item-arrow {
  color: rgb(var(--mw-rgb));
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
    max-height: 260px;
  }
  .manual-content {
    padding: 10px;
  }
  .mw-stats,
  .mw-steps {
    grid-template-columns: minmax(0, 1fr);
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
