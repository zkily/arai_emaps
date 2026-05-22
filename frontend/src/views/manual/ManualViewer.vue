<template>
  <div class="help-page help-page--standalone">
    <div class="help-bg" aria-hidden="true" />
    <div class="help-shell">
      <div class="help-header">
        <div class="help-title">
          <div class="help-title-badge">
            <el-icon class="help-title-icon"><QuestionFilled /></el-icon>
          </div>
          <div class="help-title-text">
            <h1>{{ pageTitle }}</h1>
            <p>{{ t('operationManual.subtitle') }}</p>
          </div>
        </div>
        <div class="help-actions">
          <el-button class="help-btn help-btn-print" type="default" plain @click="handlePrint">
            <el-icon class="help-btn-icon"><Printer /></el-icon>
            <span>{{ t('operationManual.print') }}</span>
          </el-button>
        </div>
      </div>

      <el-card class="help-card" shadow="never">
        <div v-if="loading" class="help-loading">
          <div class="help-spinner" />
          <span>{{ t('operationManual.loading') }}</span>
        </div>
        <div v-else-if="loadError" class="help-content">
          <p>{{ loadError }}</p>
        </div>
        <div v-else ref="helpContentEl" class="help-content" v-html="renderedHtml" />
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Printer, QuestionFilled } from '@element-plus/icons-vue'
import { getOperationManualBySlug } from '@/config/operationManuals'
import { runBrowserPrint } from '@/utils/manualPrintCapture'
import { getManualMarkdown, normalizeManualMarkdown } from '@/views/manual/manualAssets'
import {
  bindHelpContentAnchorNav,
  renderHelpMarkdown,
  scrollHelpToHash,
} from '@/utils/markdownHelpRender'

defineOptions({ name: 'ManualViewer' })

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const slug = computed(() => String(route.params.slug ?? ''))
const manual = computed(() => getOperationManualBySlug(slug.value))
const pageTitle = computed(() => manual.value?.pageTitle ?? t('operationManual.unknownTitle'))

const loading = ref(true)
const loadError = ref('')
const renderedHtml = ref('')
const helpContentEl = ref<HTMLElement | null>(null)
let unbindAnchorNav: (() => void) | null = null

function sanitizeHtml(input: string): string {
  return input
    .replace(/<script[\s\S]*?>[\s\S]*?<\/script>/gi, '')
    .replace(/\son\w+="[^"]*"/gi, '')
    .replace(/\son\w+='[^']*'/gi, '')
    .replace(/<iframe[\s\S]*?>[\s\S]*?<\/iframe>/gi, '')
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

watch(slug, () => {
  if (!manual.value) {
    ElMessage.warning(t('operationManual.notFound'))
    router.replace('/dashboard')
    return
  }
  loadDocument()
})

onMounted(() => {
  if (!manual.value) {
    ElMessage.warning(t('operationManual.notFound'))
    router.replace('/dashboard')
    return
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
  runBrowserPrint(document.documentElement)
}
</script>

<style scoped lang="scss">
@use '@/styles/help-markdown-page.scss';

.help-page--standalone {
  min-height: 100vh;
}

:deep(.help-btn) {
  height: 36px;
  padding: 0 14px;
  border-radius: 12px;
}

.help-btn-icon {
  margin-right: 6px;
  vertical-align: -2px;
}
</style>
