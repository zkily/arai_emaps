<template>
  <div class="tlp-page tlm-modern">
    <header class="tlp-hero">
      <div class="page-header-fx" aria-hidden="true"><span class="fx-orb orb-a" /><span class="fx-orb orb-b" /><span class="fx-grid" /><span class="fx-sheen" /></div>
      <div class="tlp-hero-inner">
        <div class="tlp-title-row">
          <span class="tlp-title-icon">
            <el-icon :size="20"><EditPen /></el-icon>
          </span>
          <div class="tlp-title-block">
            <h1 class="tlp-title">各種表示印刷</h1>
            <p class="tlp-subtitle">{{ activeSubtitle }}</p>
          </div>
        </div>
        <div class="tlp-hero-side">
          <div class="tlp-badges">
            <span class="tlp-cmyk" aria-hidden="true"><i /><i /><i /><i /></span>
            <span class="tlp-badge">A5 横</span>
            <span class="tlp-badge tlp-badge--muted">{{ activeFontBadge }}</span>
          </div>
          <div class="tlp-stats" @mousemove="handleStatTilt" @mouseleave="resetStatTilt">
            <div class="tlp-stat tlp-stat--dest">
              <span class="tlp-stat-num">{{ destinationOptions.length }}</span>
              <span class="tlp-stat-lbl">納入先マスタ</span>
            </div>
            <div class="tlp-stat tlp-stat--filled">
              <span class="tlp-stat-num">{{ filledFieldCount }}<small>/3</small></span>
              <span class="tlp-stat-lbl">入力済</span>
            </div>
            <div class="tlp-stat tlp-stat--sheets">
              <span class="tlp-stat-num">{{ sheetCount }}</span>
              <span class="tlp-stat-lbl">印刷枚数</span>
            </div>
          </div>
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
      <el-tab-pane label="社内メッキ向け(新聞紙なし)" name="plating">
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
                  placeholder="例：社内メッキ向け(新聞紙なし)"
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
                    → {{ formatSheetLabel(1, safePlatingCopies) }}〜{{
                      formatSheetLabel(safePlatingCopies, safePlatingCopies)
                    }}
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
                <div class="a5-corner-note">{{ PLATING_TITLE_NOTE }}</div>
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
                  <span class="a5-text">{{ formatSheetLabel(1, safePlatingCopies) }}</span>
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
  PLATING_TITLE_NOTE,
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
    ? '社内メッキ向け(新聞紙なし)ラベルを A5 横で印刷します'
    : '社内表示用ラベルを A5 横で印刷します',
)

const activeFontBadge = computed(() => {
  if (activeTab.value === 'plating') {
    return `${PLATING_FONT_SIZE.title} / ${PLATING_FONT_SIZE.product} / ${PLATING_FONT_SIZE.sheetNo} px`
  }
  return `${FONT_SIZE.notice} / ${FONT_SIZE.destination} / ${FONT_SIZE.message} px`
})

const filledFieldCount = computed(() => {
  const fields =
    activeTab.value === 'plating'
      ? [platingTitle.value.trim(), platingProduct.value.trim(), safePlatingCopies.value]
      : [notice.value.trim(), destinationCd.value, message.value.trim()]
  return fields.filter(Boolean).length
})

const sheetCount = computed(() => (activeTab.value === 'plating' ? safePlatingCopies.value : 1))

// ヘッダー統計カードの3Dチルト（マウス追従）
function handleStatTilt(e: MouseEvent) {
  const item = (e.target as HTMLElement | null)?.closest<HTMLElement>('.tlp-stat')
  const host = e.currentTarget as HTMLElement
  host.querySelectorAll<HTMLElement>('.tlp-stat').forEach((el) => {
    if (el !== item) {
      el.style.removeProperty('--rx')
      el.style.removeProperty('--ry')
    }
  })
  if (!item) return
  const rect = item.getBoundingClientRect()
  const px = (e.clientX - rect.left) / rect.width
  const py = (e.clientY - rect.top) / rect.height
  item.style.setProperty('--rx', `${((0.5 - py) * 14).toFixed(2)}deg`)
  item.style.setProperty('--ry', `${((px - 0.5) * 14).toFixed(2)}deg`)
  item.style.setProperty('--mx', `${(px * 100).toFixed(1)}%`)
  item.style.setProperty('--my', `${(py * 100).toFixed(1)}%`)
}

function resetStatTilt(e: MouseEvent) {
  ;(e.currentTarget as HTMLElement).querySelectorAll<HTMLElement>('.tlp-stat').forEach((el) => {
    el.style.removeProperty('--rx')
    el.style.removeProperty('--ry')
  })
}

/** プレビューは縮小表示（実寸比） */
const previewNoticePx = `${Math.round(FONT_SIZE.notice * 0.42)}px`
const previewDestPx = `${Math.round(FONT_SIZE.destination * 0.42)}px`
const previewMessagePx = `${Math.round(FONT_SIZE.message * 0.42)}px`
const previewPlatingTitlePx = `${Math.round(PLATING_FONT_SIZE.title * 0.42)}px`
const previewPlatingProductPx = `${Math.round(PLATING_FONT_SIZE.product * 0.42)}px`
const previewPlatingSheetPx = `${Math.round(PLATING_FONT_SIZE.sheetNo * 0.42)}px`
const previewPlatingTitleNotePx = `${Math.max(9, Math.round(PLATING_FONT_SIZE.titleNote * 0.85))}px`

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
  position: relative;
  justify-content: center;
  gap: 18px;
  padding: 12px 8px;
}

.a5-corner-note {
  position: absolute;
  bottom: 6px;
  right: 8px;
  z-index: 1;
  color: #dc2626;
  font-size: v-bind(previewPlatingTitleNotePx);
  font-weight: 700;
  letter-spacing: 0.02em;
  white-space: nowrap;
  line-height: 1.2;
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

/* ============================================================
 * 页面美化：現代UI・3D動効・色分け（各種表示印刷 / インク：墨黒→プラム→マゼンタ→アンバー）
 * ============================================================ */
.tlm-modern {
  --hx-1: #111827;
  --hx-2: #581c87;
  --hx-3: #db2777;
  --hx-4: #f59e0b;
  --hx-deep: #831843;
  --hx-soft: #fdf2f8;
  --hx-line: rgba(219, 39, 119, 0.18);
}

.tlm-modern .tlp-hero {
  position: relative;
  overflow: hidden;
  padding: 16px 20px;
  border-radius: 16px;
  border: none;
  background: linear-gradient(125deg, var(--hx-1) 0%, var(--hx-2) 34%, var(--hx-3) 68%, var(--hx-4) 100%);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.18) inset,
    0 14px 32px -12px rgba(131, 24, 67, 0.6),
    0 2px 6px rgba(15, 23, 42, 0.08);
}

.tlm-modern .tlp-hero > :not(.page-header-fx) {
  position: relative;
  z-index: 1;
}

.tlm-modern .page-header-fx {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.tlm-modern .fx-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(22px);
  opacity: 0.55;
  animation: tlmOrbFloat 11s ease-in-out infinite;
}

.tlm-modern .orb-a {
  width: 180px;
  height: 180px;
  top: -70px;
  right: 22%;
  background: radial-gradient(circle, #f9a8d4 0%, transparent 70%);
}

.tlm-modern .orb-b {
  width: 150px;
  height: 150px;
  bottom: -70px;
  left: 26%;
  background: radial-gradient(circle, #67e8f9 0%, transparent 70%);
  animation-delay: -5s;
}

.tlm-modern .fx-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.08) 1px, transparent 1px);
  background-size: 22px 22px;
  mask-image: radial-gradient(ellipse 70% 90% at 70% 40%, #000 20%, transparent 75%);
}

.tlm-modern .fx-sheen {
  position: absolute;
  top: 0;
  bottom: 0;
  left: -40%;
  width: 30%;
  background: linear-gradient(100deg, transparent, rgba(255, 255, 255, 0.18), transparent);
  transform: skewX(-18deg);
  animation: tlmSheen 7s ease-in-out infinite;
}

@keyframes tlmOrbFloat {
  0%,
  100% {
    transform: translate(0, 0) scale(1);
  }
  50% {
    transform: translate(18px, 10px) scale(1.12);
  }
}

@keyframes tlmSheen {
  0% {
    left: -40%;
  }
  60%,
  100% {
    left: 130%;
  }
}

.tlm-modern .tlp-title-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.32), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.35);
  backdrop-filter: blur(6px);
  box-shadow:
    0 4px 0 rgba(17, 24, 39, 0.5),
    0 10px 18px -6px rgba(0, 0, 0, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.45);
}

.tlm-modern .tlp-title-icon :deep(svg) {
  animation: tlmPenWrite 2.8s ease-in-out infinite;
  transform-origin: 20% 80%;
}

@keyframes tlmPenWrite {
  0%,
  100% {
    transform: translate(0, 0) rotate(0deg);
  }
  25% {
    transform: translate(2px, -1px) rotate(-6deg);
  }
  50% {
    transform: translate(-1px, 1px) rotate(4deg);
  }
  75% {
    transform: translate(1px, 0) rotate(-3deg);
  }
}

.tlm-modern .tlp-title {
  color: #fff;
  font-size: 20px;
  text-shadow: 0 2px 8px rgba(17, 24, 39, 0.4);
}

.tlm-modern .tlp-subtitle {
  color: rgba(253, 242, 248, 0.88);
}

.tlm-modern .tlp-hero-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}

.tlm-modern .tlp-badge,
.tlm-modern .tlp-badge--muted {
  color: #fff;
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.26), rgba(255, 255, 255, 0.08));
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow:
    0 2px 0 rgba(17, 24, 39, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
}

.tlm-modern .tlp-cmyk {
  display: inline-flex;
  gap: 3px;
  padding: 5px 7px;
  border-radius: 999px;
  background: rgba(17, 24, 39, 0.3);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.2);
}

.tlm-modern .tlp-cmyk i {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  box-shadow: 0 1px 0 rgba(0, 0, 0, 0.3);
  animation: tlmInkDrop 2.4s ease-in-out infinite;
}

.tlm-modern .tlp-cmyk i:nth-child(1) {
  background: #06b6d4;
}

.tlm-modern .tlp-cmyk i:nth-child(2) {
  background: #ec4899;
  animation-delay: 0.2s;
}

.tlm-modern .tlp-cmyk i:nth-child(3) {
  background: #facc15;
  animation-delay: 0.4s;
}

.tlm-modern .tlp-cmyk i:nth-child(4) {
  background: #0f172a;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.4);
  animation-delay: 0.6s;
}

@keyframes tlmInkDrop {
  0%,
  100% {
    transform: translateY(0) scale(1);
  }
  40% {
    transform: translateY(-3px) scale(1.15);
  }
}

/* 統計カード */
.tlm-modern .tlp-stats {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
  perspective: 650px;
}

.tlm-modern .tlp-stat {
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 84px;
  padding: 9px 14px 8px;
  border-radius: 12px;
  color: #fff;
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.24), rgba(255, 255, 255, 0.08));
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow:
    0 4px 0 rgba(17, 24, 39, 0.4),
    0 12px 22px -10px rgba(0, 0, 0, 0.45),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
  transform-style: preserve-3d;
  transform: rotateX(var(--rx, 0deg)) rotateY(var(--ry, 0deg));
  transition:
    transform 0.18s ease,
    background 0.2s ease;
}

.tlm-modern .tlp-stat:hover {
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.32), rgba(255, 255, 255, 0.12));
}

.tlm-modern .tlp-stat::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--sc);
  box-shadow: 0 0 10px var(--sc);
}

.tlm-modern .tlp-stat::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at var(--mx, 50%) var(--my, 0%), rgba(255, 255, 255, 0.28), transparent 60%);
  opacity: 0;
  transition: opacity 0.2s ease;
  pointer-events: none;
}

.tlm-modern .tlp-stat:hover::after {
  opacity: 1;
}

.tlm-modern .tlp-stat-num {
  display: block;
  font-size: 22px;
  font-weight: 800;
  line-height: 1.1;
  font-variant-numeric: tabular-nums;
  transform: translateZ(14px);
  text-shadow: 0 2px 6px rgba(17, 24, 39, 0.45);
}

.tlm-modern .tlp-stat-num small {
  font-size: 12px;
  opacity: 0.75;
  margin-left: 1px;
}

.tlm-modern .tlp-stat-lbl {
  margin-top: 2px;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: rgba(253, 242, 248, 0.85);
}

.tlm-modern .tlp-stat--dest {
  --sc: #67e8f9;
}

.tlm-modern .tlp-stat--filled {
  --sc: #f9a8d4;
}

.tlm-modern .tlp-stat--sheets {
  --sc: #fde047;
}

/* タブ（色分け） */
.tlm-modern .tlp-tabs :deep(#tab-shipping) {
  --tc: #059669;
}

.tlm-modern .tlp-tabs :deep(#tab-plating) {
  --tc: #d97706;
}

.tlm-modern .tlp-tabs :deep(.el-tabs__item) {
  position: relative;
  padding: 0 16px;
  border-radius: 10px 10px 0 0;
  transition:
    color 0.2s ease,
    background 0.2s ease,
    transform 0.2s ease;
}

.tlm-modern .tlp-tabs :deep(.el-tabs__item:hover) {
  color: var(--tc);
  background: color-mix(in srgb, var(--tc) 8%, transparent);
  transform: translateY(-1px);
}

.tlm-modern .tlp-tabs :deep(.el-tabs__item.is-active) {
  color: var(--tc);
  background: linear-gradient(180deg, color-mix(in srgb, var(--tc) 12%, #fff), #fff);
  box-shadow: inset 0 3px 0 var(--tc);
}

.tlm-modern .tlp-tabs :deep(.el-tabs__active-bar) {
  background: linear-gradient(90deg, var(--hx-2), var(--hx-3), var(--hx-4));
}

/* パネル */
.tlm-modern .tlp-panel {
  --pc: #db2777;
  --pc-deep: #9d174d;
  position: relative;
  border-radius: 14px;
  border: 1px solid color-mix(in srgb, var(--pc) 22%, transparent);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 10px 26px -14px color-mix(in srgb, var(--pc) 55%, transparent),
    0 2px 6px rgba(15, 23, 42, 0.04);
}

.tlm-modern .tlp-panel--preview {
  --pc: #0891b2;
  --pc-deep: #155e75;
}

.tlm-modern .tlp-panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  z-index: 5;
  background: linear-gradient(90deg, var(--pc-deep), var(--pc));
}

.tlm-modern .tlp-panel-head {
  padding-top: 13px;
  background: linear-gradient(180deg, color-mix(in srgb, var(--pc) 7%, #fff) 0%, #fff 100%);
  border-bottom-color: color-mix(in srgb, var(--pc) 16%, transparent);
}

.tlm-modern .tlp-panel-title {
  color: var(--pc-deep);
}

.tlm-modern .tlp-step {
  color: #fff;
  border: none;
  background: linear-gradient(160deg, #f472b6, #db2777);
  box-shadow:
    0 2px 0 #9d174d,
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
}

.tlm-modern .tlp-px {
  padding: 0 7px;
  border-radius: 999px;
  color: #7c3aed;
  background: color-mix(in srgb, #7c3aed 10%, #fff);
  box-shadow: inset 0 0 0 1px rgba(124, 58, 237, 0.2);
}

.tlm-modern .tlp-copies-hint {
  color: #b45309;
}

.tlm-modern .tlp-fields :deep(.el-input__wrapper),
.tlm-modern .tlp-fields :deep(.el-select__wrapper) {
  transition: box-shadow 0.2s ease;
}

.tlm-modern .tlp-fields :deep(.el-input__wrapper.is-focus),
.tlm-modern .tlp-fields :deep(.el-select__wrapper.is-focused) {
  box-shadow:
    0 0 0 1px rgba(219, 39, 119, 0.55) inset,
    0 4px 12px -4px rgba(219, 39, 119, 0.35);
}

/* 立体ボタン（キーキャップ） */
.tlm-modern .tlp-btn {
  --k-edge: #047857;
  --k-glow: rgba(5, 150, 105, 0.5);
  transition:
    transform 0.12s ease,
    box-shadow 0.12s ease,
    filter 0.12s ease !important;
}

.tlm-modern .tlp-btn--print {
  box-shadow:
    0 3px 0 var(--k-edge),
    0 10px 18px -8px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
}

.tlm-modern .tlp-btn--print:not(:disabled):hover {
  transform: translateY(-2px);
  filter: brightness(1.06);
  background: linear-gradient(180deg, #34d399 0%, #10b981 50%, #059669 100%) !important;
  box-shadow:
    0 5px 0 var(--k-edge),
    0 14px 22px -8px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
}

.tlm-modern .tlp-btn--print:not(:disabled):active {
  transform: translateY(2px);
  box-shadow:
    0 1px 0 var(--k-edge),
    inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
}

.tlm-modern .tlp-btn--ghost {
  --k-edge: #cbd5e1;
  box-shadow:
    0 3px 0 var(--k-edge),
    inset 0 1px 0 rgba(255, 255, 255, 0.9) !important;
}

.tlm-modern .tlp-btn--ghost:hover {
  transform: translateY(-2px);
  color: var(--hx-deep) !important;
  box-shadow:
    0 5px 0 var(--k-edge),
    inset 0 1px 0 rgba(255, 255, 255, 0.9) !important;
}

.tlm-modern .tlp-btn--ghost:active {
  transform: translateY(2px);
  box-shadow: 0 1px 0 var(--k-edge) !important;
}

/* プレビュー（用紙の3D表現） */
.tlm-modern .tlp-preview-stage {
  perspective: 900px;
  background:
    radial-gradient(circle at 20% 10%, rgba(8, 145, 178, 0.1), transparent 40%),
    radial-gradient(circle at 90% 80%, rgba(219, 39, 119, 0.08), transparent 36%),
    repeating-linear-gradient(45deg, #f1f5f9 0 10px, #eef2f7 10px 20px);
}

.tlm-modern .a5-preview {
  transform: rotateX(4deg) translateY(0);
  transform-origin: 50% 100%;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.7) inset,
    0 18px 30px -12px rgba(15, 23, 42, 0.35),
    0 4px 0 #cbd5e1;
  transition:
    transform 0.35s ease,
    box-shadow 0.35s ease;
}

.tlm-modern .tlp-preview-stage:hover .a5-preview {
  transform: rotateX(0deg) translateY(-4px);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.7) inset,
    0 26px 40px -14px rgba(15, 23, 42, 0.4),
    0 6px 0 #cbd5e1;
}

@media (prefers-reduced-motion: reduce) {
  .tlm-modern .fx-orb,
  .tlm-modern .fx-sheen,
  .tlm-modern .tlp-title-icon :deep(svg),
  .tlm-modern .tlp-cmyk i {
    animation: none;
  }

  .tlm-modern .tlp-stat,
  .tlm-modern .a5-preview,
  .tlm-modern .tlp-preview-stage:hover .a5-preview {
    transform: none;
  }
}

@media (max-width: 860px) {
  .tlm-modern .tlp-hero-side {
    align-items: flex-start;
  }

  .tlm-modern .tlp-stats {
    justify-content: flex-start;
  }
}
</style>
