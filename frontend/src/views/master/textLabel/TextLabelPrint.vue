<template>
  <div class="tlp-page">
    <header class="tlp-hero">
      <div class="tlp-hero-inner">
        <div class="tlp-title-row">
          <span class="tlp-title-icon">
            <el-icon :size="20"><EditPen /></el-icon>
          </span>
          <div class="tlp-title-block">
            <h1 class="tlp-title">テキストラベル印刷</h1>
            <p class="tlp-subtitle">{{ activeSubtitle }}</p>
          </div>
        </div>
        <div class="tlp-badges">
          <span class="tlp-badge">A5 横</span>
          <span class="tlp-badge tlp-badge--muted">{{ activeFontBadge }}</span>
        </div>
      </div>
    </header>

    <el-tabs v-model="activeTab" class="tlp-tabs">
      <!-- 出荷表示（既存） -->
      <el-tab-pane label="出荷表示" name="shipping">
        <div class="tlp-body">
          <section class="tlp-panel tlp-panel--form">
            <div class="tlp-panel-head">
              <span class="tlp-panel-title">入力</span>
              <span class="tlp-panel-hint">3行構成・改行なし</span>
            </div>

            <div class="tlp-fields">
              <div class="tlp-field">
                <div class="tlp-field-label-row">
                  <label class="tlp-field-label">
                    <span class="tlp-step">1</span>
                    注意文言
                  </label>
                  <span class="tlp-px">{{ FONT_SIZE.notice }}px</span>
                </div>
                <el-input
                  v-model="notice"
                  placeholder="例：社内表示用　出荷の際は外してください"
                  maxlength="60"
                  clearable
                  show-word-limit
                />
              </div>

              <div class="tlp-field">
                <div class="tlp-field-label-row">
                  <label class="tlp-field-label">
                    <span class="tlp-step">2</span>
                    納入先
                  </label>
                  <span class="tlp-px">{{ FONT_SIZE.destination }}px</span>
                </div>
                <el-select
                  v-model="destinationCd"
                  filterable
                  clearable
                  placeholder="納入先を選択"
                  class="tlp-select"
                  :loading="loadingDestinations"
                  popper-class="destination-select-popper"
                >
                  <el-option
                    v-for="d in destinationOptions"
                    :key="d.cd"
                    :label="`${d.cd} | ${d.name}`"
                    :value="d.cd"
                  />
                </el-select>
              </div>

              <div class="tlp-field">
                <div class="tlp-field-label-row">
                  <label class="tlp-field-label">
                    <span class="tlp-step">3</span>
                    印刷テキスト
                  </label>
                  <span class="tlp-px">{{ FONT_SIZE.message }}px</span>
                </div>
                <el-input
                  v-model="message"
                  placeholder="例：出荷OK"
                  maxlength="40"
                  clearable
                  show-word-limit
                  @keyup.enter="handlePrintShipping"
                />
              </div>
            </div>

            <div class="tlp-actions">
              <el-button
                class="tlp-btn tlp-btn--print"
                :icon="Printer"
                :loading="printing"
                @click="handlePrintShipping"
              >
                印刷
              </el-button>
              <el-button class="tlp-btn tlp-btn--ghost" @click="resetShippingForm">クリア</el-button>
            </div>
          </section>

          <section class="tlp-panel tlp-panel--preview">
            <div class="tlp-panel-head">
              <span class="tlp-panel-title">プレビュー</span>
              <span class="tlp-panel-hint">実寸比 A5 横</span>
            </div>

            <div class="tlp-preview-stage">
              <div class="a5-preview" aria-hidden="true">
                <div class="a5-row a5-row--notice">
                  <span class="a5-text" :class="{ 'is-placeholder': !notice.trim() }">
                    {{ notice.trim() || '注意文言' }}
                  </span>
                </div>
                <div class="a5-row a5-row--dest">
                  <span class="a5-text" :class="{ 'is-placeholder': !selectedDestinationName }">
                    {{ selectedDestinationName || '納入先' }}
                  </span>
                </div>
                <div class="a5-row a5-row--msg">
                  <span class="a5-text" :class="{ 'is-placeholder': !message.trim() }">
                    {{ message.trim() || '印刷テキスト' }}
                  </span>
                </div>
              </div>
            </div>
          </section>
        </div>
      </el-tab-pane>

      <!-- 社内メッキ向け（新規） -->
      <el-tab-pane label="社内メッキ向け" name="plating">
        <div class="tlp-body">
          <section class="tlp-panel tlp-panel--form">
            <div class="tlp-panel-head">
              <span class="tlp-panel-title">入力</span>
              <span class="tlp-panel-hint">枚数分「N 枚目」を印刷</span>
            </div>

            <div class="tlp-fields">
              <div class="tlp-field">
                <div class="tlp-field-label-row">
                  <label class="tlp-field-label">
                    <span class="tlp-step">1</span>
                    見出し
                  </label>
                  <span class="tlp-px">{{ PLATING_FONT_SIZE.title }}px</span>
                </div>
                <el-input
                  v-model="platingTitle"
                  placeholder="例：社内メッキ向け"
                  maxlength="40"
                  clearable
                  show-word-limit
                />
              </div>

              <div class="tlp-field">
                <div class="tlp-field-label-row">
                  <label class="tlp-field-label">
                    <span class="tlp-step">2</span>
                    品番・テキスト
                  </label>
                  <span class="tlp-px">{{ PLATING_FONT_SIZE.product }}px</span>
                </div>
                <el-input
                  v-model="platingProduct"
                  placeholder="例：164B FR"
                  maxlength="40"
                  clearable
                  show-word-limit
                  @keyup.enter="handlePrintPlating"
                />
              </div>

              <div class="tlp-field">
                <div class="tlp-field-label-row">
                  <label class="tlp-field-label">
                    <span class="tlp-step">3</span>
                    印刷枚数
                  </label>
                  <span class="tlp-px">{{ PLATING_FONT_SIZE.sheetNo }}px</span>
                </div>
                <div class="tlp-copies-row">
                  <el-input-number
                    v-model="platingCopies"
                    :min="1"
                    :max="99"
                    :step="1"
                    controls-position="right"
                    class="tlp-copies"
                  />
                  <span class="tlp-copies-hint">
                    → {{ formatSheetLabel(1) }}〜{{ formatSheetLabel(safePlatingCopies) }}
                  </span>
                </div>
              </div>
            </div>

            <div class="tlp-actions">
              <el-button
                class="tlp-btn tlp-btn--print"
                :icon="Printer"
                :loading="printing"
                @click="handlePrintPlating"
              >
                印刷
              </el-button>
              <el-button class="tlp-btn tlp-btn--ghost" @click="resetPlatingForm">クリア</el-button>
            </div>
          </section>

          <section class="tlp-panel tlp-panel--preview">
            <div class="tlp-panel-head">
              <span class="tlp-panel-title">プレビュー</span>
              <span class="tlp-panel-hint">1枚目のイメージ</span>
            </div>

            <div class="tlp-preview-stage">
              <div class="a5-preview a5-preview--plating" aria-hidden="true">
                <div class="a5-row a5-row--plating-title">
                  <span class="a5-text" :class="{ 'is-placeholder': !platingTitle.trim() }">
                    {{ platingTitle.trim() || '見出し' }}
                  </span>
                </div>
                <div class="a5-row a5-row--plating-product">
                  <span class="a5-text" :class="{ 'is-placeholder': !platingProduct.trim() }">
                    {{ platingProduct.trim() || '品番・テキスト' }}
                  </span>
                </div>
                <div class="a5-row a5-row--plating-sheet">
                  <span class="a5-text">{{ formatSheetLabel(1) }}</span>
                </div>
              </div>
            </div>
          </section>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { EditPen, Printer } from '@element-plus/icons-vue'
import { getDestinationOptions } from '@/api/master/destinationMaster'
import {
  DEFAULT_MESSAGE,
  DEFAULT_NOTICE,
  DEFAULT_PLATING_COPIES,
  DEFAULT_PLATING_PRODUCT,
  DEFAULT_PLATING_TITLE,
  FONT_SIZE,
  PLATING_FONT_SIZE,
  PRINT_POPUP_BLOCKED_MSG,
  formatSheetLabel,
  printPlatingLabel,
  printTextLabel,
} from './utils/textLabelPrint'

type TabName = 'shipping' | 'plating'

const activeTab = ref<TabName>('shipping')

const notice = ref(DEFAULT_NOTICE)
const destinationCd = ref('')
const message = ref(DEFAULT_MESSAGE)
const destinationOptions = ref<{ cd: string; name: string }[]>([])
const loadingDestinations = ref(false)
const printing = ref(false)

const platingTitle = ref(DEFAULT_PLATING_TITLE)
const platingProduct = ref(DEFAULT_PLATING_PRODUCT)
const platingCopies = ref(DEFAULT_PLATING_COPIES)

const selectedDestinationName = computed(() => {
  const hit = destinationOptions.value.find((d) => d.cd === destinationCd.value)
  return hit?.name || ''
})

const safePlatingCopies = computed(() => {
  const n = Math.floor(Number(platingCopies.value) || 1)
  return Math.min(99, Math.max(1, n))
})

const activeSubtitle = computed(() =>
  activeTab.value === 'plating'
    ? '社内メッキ向けラベルを A5 横で印刷します'
    : '社内表示用ラベルを A5 横で印刷します',
)

const activeFontBadge = computed(() => {
  if (activeTab.value === 'plating') {
    return `${PLATING_FONT_SIZE.title} / ${PLATING_FONT_SIZE.product} / ${PLATING_FONT_SIZE.sheetNo} px`
  }
  return `${FONT_SIZE.notice} / ${FONT_SIZE.destination} / ${FONT_SIZE.message} px`
})

/** プレビューは縮小表示（実寸比） */
const previewNoticePx = `${Math.round(FONT_SIZE.notice * 0.42)}px`
const previewDestPx = `${Math.round(FONT_SIZE.destination * 0.42)}px`
const previewMessagePx = `${Math.round(FONT_SIZE.message * 0.42)}px`
const previewPlatingTitlePx = `${Math.round(PLATING_FONT_SIZE.title * 0.42)}px`
const previewPlatingProductPx = `${Math.round(PLATING_FONT_SIZE.product * 0.42)}px`
const previewPlatingSheetPx = `${Math.round(PLATING_FONT_SIZE.sheetNo * 0.42)}px`

async function loadDestinations() {
  loadingDestinations.value = true
  try {
    destinationOptions.value = await getDestinationOptions()
  } catch {
    ElMessage.error('納入先の取得に失敗しました')
  } finally {
    loadingDestinations.value = false
  }
}

function resetShippingForm() {
  notice.value = DEFAULT_NOTICE
  destinationCd.value = ''
  message.value = DEFAULT_MESSAGE
}

function resetPlatingForm() {
  platingTitle.value = DEFAULT_PLATING_TITLE
  platingProduct.value = DEFAULT_PLATING_PRODUCT
  platingCopies.value = DEFAULT_PLATING_COPIES
}

async function handlePrintShipping() {
  const noticeText = notice.value.trim()
  if (!noticeText) {
    ElMessage.warning('注意文言を入力してください')
    return
  }
  if (!destinationCd.value) {
    ElMessage.warning('納入先を選択してください')
    return
  }
  const text = message.value.trim()
  if (!text) {
    ElMessage.warning('印刷テキストを入力してください')
    return
  }
  printing.value = true
  try {
    const win = printTextLabel({
      notice: noticeText,
      destinationName: selectedDestinationName.value,
      message: text,
    })
    if (!win) {
      ElMessage.error(PRINT_POPUP_BLOCKED_MSG)
    }
  } finally {
    printing.value = false
  }
}

async function handlePrintPlating() {
  const title = platingTitle.value.trim()
  if (!title) {
    ElMessage.warning('見出しを入力してください')
    return
  }
  const product = platingProduct.value.trim()
  if (!product) {
    ElMessage.warning('品番・テキストを入力してください')
    return
  }
  const copies = safePlatingCopies.value
  platingCopies.value = copies

  printing.value = true
  try {
    const win = printPlatingLabel({
      title,
      productText: product,
      copies,
    })
    if (!win) {
      ElMessage.error(PRINT_POPUP_BLOCKED_MSG)
    }
  } finally {
    printing.value = false
  }
}

onMounted(() => {
  loadDestinations()
})
</script>

<style scoped>
.tlp-page {
  --tlp-ink: #0f172a;
  --tlp-muted: #64748b;
  --tlp-line: #e2e8f0;
  --tlp-surface: #ffffff;
  --tlp-stage: #f1f5f9;
  --tlp-teal: #0d9488;
  --tlp-teal-soft: #f0fdfa;
  --tlp-teal-line: #99f6e4;

  padding: 12px 16px 20px;
  max-width: 1080px;
  color: var(--tlp-ink);
}

.tlp-hero {
  margin-bottom: 12px;
  padding: 12px 14px;
  border-radius: 12px;
  background:
    linear-gradient(135deg, rgba(240, 253, 250, 0.95) 0%, rgba(255, 255, 255, 0.92) 55%, rgba(248, 250, 252, 0.98) 100%),
    var(--tlp-surface);
  border: 1px solid var(--tlp-line);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.tlp-hero-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.tlp-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.tlp-title-icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  color: #fff;
  background: linear-gradient(160deg, #2dd4bf 0%, #0d9488 100%);
  box-shadow: 0 4px 10px rgba(13, 148, 136, 0.28);
}

.tlp-title {
  margin: 0;
  font-size: 18px;
  font-weight: 800;
  letter-spacing: 0.02em;
  line-height: 1.25;
}

.tlp-subtitle {
  margin: 2px 0 0;
  font-size: 12px;
  color: var(--tlp-muted);
  line-height: 1.35;
}

.tlp-badges {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.tlp-badge {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  color: #0f766e;
  background: var(--tlp-teal-soft);
  border: 1px solid var(--tlp-teal-line);
}

.tlp-badge--muted {
  color: #475569;
  background: #f8fafc;
  border-color: var(--tlp-line);
  font-variant-numeric: tabular-nums;
}

.tlp-tabs {
  --el-tabs-header-height: 40px;
}

.tlp-tabs :deep(.el-tabs__header) {
  margin-bottom: 12px;
}

.tlp-tabs :deep(.el-tabs__nav-wrap::after) {
  height: 1px;
  background-color: var(--tlp-line);
}

.tlp-tabs :deep(.el-tabs__item) {
  font-weight: 700;
  font-size: 13px;
  color: var(--tlp-muted);
}

.tlp-tabs :deep(.el-tabs__item.is-active) {
  color: #0f766e;
}

.tlp-tabs :deep(.el-tabs__active-bar) {
  background-color: var(--tlp-teal);
  height: 3px;
  border-radius: 2px 2px 0 0;
}

.tlp-tabs :deep(.el-tabs__content) {
  overflow: visible;
}

.tlp-body {
  display: grid;
  grid-template-columns: minmax(280px, 1fr) minmax(300px, 1.05fr);
  gap: 12px;
  align-items: start;
}

.tlp-panel {
  background: var(--tlp-surface);
  border: 1px solid var(--tlp-line);
  border-radius: 12px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
  overflow: hidden;
}

.tlp-panel-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--tlp-line);
  background: linear-gradient(180deg, #fafbfc 0%, #fff 100%);
}

.tlp-panel-title {
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.04em;
}

.tlp-panel-hint {
  font-size: 11px;
  color: var(--tlp-muted);
}

.tlp-fields {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px 14px 4px;
}

.tlp-field-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
}

.tlp-field-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 700;
  color: #334155;
}

.tlp-step {
  display: inline-grid;
  place-items: center;
  width: 18px;
  height: 18px;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 800;
  color: #0f766e;
  background: var(--tlp-teal-soft);
  border: 1px solid var(--tlp-teal-line);
}

.tlp-px {
  font-size: 11px;
  font-weight: 700;
  color: #94a3b8;
  font-variant-numeric: tabular-nums;
}

.tlp-select {
  width: 100%;
}

.tlp-copies-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.tlp-copies {
  width: 140px;
}

.tlp-copies-hint {
  font-size: 12px;
  font-weight: 700;
  color: #0f766e;
  font-variant-numeric: tabular-nums;
}

.tlp-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px 14px;
}

.tlp-btn {
  border-radius: 8px !important;
  font-weight: 700 !important;
}

.tlp-btn--print {
  color: #fff !important;
  background: linear-gradient(180deg, #34d399 0%, #10b981 50%, #059669 100%) !important;
  border: none !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.3) inset,
    0 2px 0 #047857,
    0 4px 10px rgba(5, 150, 105, 0.28) !important;
}

.tlp-btn--print:active {
  transform: translateY(1px);
}

.tlp-btn--ghost {
  color: #475569 !important;
  background: #f8fafc !important;
  border: 1px solid var(--tlp-line) !important;
}

.tlp-preview-stage {
  padding: 12px;
  background:
    radial-gradient(circle at 20% 10%, rgba(45, 212, 191, 0.08), transparent 40%),
    radial-gradient(circle at 90% 80%, rgba(14, 165, 233, 0.06), transparent 36%),
    var(--tlp-stage);
}

.a5-preview {
  width: min(100%, 480px);
  aspect-ratio: 210 / 148;
  margin: 0 auto;
  border: 2px solid #0f172a;
  border-radius: 2px;
  background: #fff;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.7) inset,
    0 10px 28px rgba(15, 23, 42, 0.12);
}

.a5-preview--plating {
  justify-content: center;
  gap: 18px;
  padding: 12px 8px;
}

.a5-row {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 0;
  overflow: hidden;
  text-align: center;
  font-weight: 800;
  letter-spacing: 0.04em;
  white-space: nowrap;
  line-height: 1.2;
  padding: 4px 8px;
  color: #111;
}

.a5-row--notice {
  flex: 0 0 22%;
  border-bottom: 1.5px solid #9ca3af;
  font-size: v-bind(previewNoticePx);
}

.a5-row--dest {
  flex: 0 0 30%;
  border-bottom: 1.5px solid #9ca3af;
  font-size: v-bind(previewDestPx);
}

.a5-row--msg {
  flex: 1 1 auto;
  font-size: v-bind(previewMessagePx);
}

.a5-row--plating-title {
  flex: 0 0 auto;
  font-size: v-bind(previewPlatingTitlePx);
}

.a5-row--plating-product {
  flex: 0 0 auto;
  font-size: v-bind(previewPlatingProductPx);
}

.a5-row--plating-sheet {
  flex: 0 0 auto;
  font-size: v-bind(previewPlatingSheetPx);
}

.a5-text {
  display: inline-block;
  white-space: nowrap;
  color: #111;
}

.a5-text.is-placeholder {
  color: #94a3b8;
}

@media (max-width: 860px) {
  .tlp-body {
    grid-template-columns: 1fr;
  }

  .a5-preview {
    width: min(100%, 520px);
  }
}
</style>
