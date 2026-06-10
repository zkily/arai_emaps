<template>
  <div
    v-show="visible"
    ref="panelRef"
    class="ai-assistant-panel"
    :class="{ 'ai-assistant-panel--dragging': dragging }"
    :style="panelStyle"
    @mousedown="onPanelFocus"
  >
    <div class="ai-assistant-panel__head" @mousedown="onDragStart">
      <el-icon class="ai-assistant-panel__grip" :size="14"><Rank /></el-icon>
      <span class="ai-assistant-panel__title">{{ t('aiAssistant.title') }}</span>
      <span class="ai-assistant-panel__status" :class="statusClass">{{ statusLabel }}</span>
      <div class="ai-assistant-panel__actions" @mousedown.stop>
        <el-button
          type="info"
          text
          size="small"
          circle
          :icon="Close"
          :title="t('common.cancel')"
          @click="onClose"
        />
      </div>
    </div>

    <div ref="messagesRef" class="ai-assistant-panel__messages">
      <div v-if="displayMessages.length === 0" class="ai-assistant-panel__empty">
        {{ t('aiAssistant.emptyHint') }}
      </div>
      <div
        v-for="(msg, idx) in displayMessages"
        :key="idx"
        class="ai-assistant-panel__msg"
        :class="`ai-assistant-panel__msg--${msg.role}`"
      >
        <div class="ai-assistant-panel__bubble">{{ msg.content }}</div>
      </div>
      <div v-if="statusText" class="ai-assistant-panel__status-line">{{ statusText }}</div>
    </div>

    <div class="ai-assistant-panel__input" @mousedown.stop>
      <el-input
        v-model="inputText"
        type="textarea"
        :rows="2"
        :placeholder="t('aiAssistant.inputPlaceholder')"
        :disabled="sending"
        resize="none"
        @keydown.enter.exact.prevent="sendMessage"
      />
      <el-button
        type="primary"
        :loading="sending"
        :disabled="!canSend"
        @click="sendMessage"
      >
        {{ t('aiAssistant.send') }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Close, Rank } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import { getAiHealth, streamChat, type AiChatMessage } from '@/api/ai'

const props = withDefaults(
  defineProps<{
    visible: boolean
    width?: number
    initialX?: number
    initialY?: number
    zIndex?: number
    boundary?: HTMLElement | null
  }>(),
  {
    width: 420,
    initialX: 24,
    initialY: 96,
    zIndex: 200,
    boundary: null,
  },
)

const emit = defineEmits<{
  'update:visible': [value: boolean]
  close: []
}>()

const { t } = useI18n()

const panelRef = ref<HTMLElement | null>(null)
const messagesRef = ref<HTMLElement | null>(null)
const posX = ref(props.initialX)
const posY = ref(props.initialY)
const stackZ = ref(props.zIndex)
const dragging = ref(false)

const inputText = ref('')
const sending = ref(false)
const statusText = ref('')
const healthStatus = ref<'unknown' | 'ok' | 'offline' | 'model_missing' | 'disabled'>('unknown')
const healthModel = ref('')

const messages = ref<AiChatMessage[]>([])
const displayMessages = computed(() => messages.value.filter((m) => m.role !== 'system'))

let dragPointerOffsetX = 0
let dragPointerOffsetY = 0
let abortController: AbortController | null = null

const panelStyle = computed(() => ({
  left: `${posX.value}px`,
  top: `${posY.value}px`,
  width: `${props.width}px`,
  zIndex: String(stackZ.value),
}))

const canSend = computed(() => inputText.value.trim().length > 0 && !sending.value)

const statusClass = computed(() => `ai-assistant-panel__status--${healthStatus.value}`)

const statusLabel = computed(() => {
  if (healthStatus.value === 'ok') {
    return healthModel.value || t('aiAssistant.statusOnline')
  }
  if (healthStatus.value === 'model_missing') return t('aiAssistant.statusModelMissing')
  if (healthStatus.value === 'disabled') return t('aiAssistant.statusDisabled')
  if (healthStatus.value === 'offline') return t('aiAssistant.statusOffline')
  return t('aiAssistant.statusChecking')
})

watch(
  () => props.visible,
  (v) => {
    if (v) {
      refreshHealth()
      onPanelFocus()
    }
  },
)

watch(
  () => props.initialX,
  (v) => {
    if (!dragging.value && v != null) posX.value = v
  },
)
watch(
  () => props.initialY,
  (v) => {
    if (!dragging.value && v != null) posY.value = v
  },
)

function clampPosition(x: number, y: number): { x: number; y: number } {
  const boundary = props.boundary
  const panel = panelRef.value
  if (!boundary || !panel) return { x, y }
  const maxX = Math.max(0, boundary.clientWidth - panel.offsetWidth)
  const maxY = Math.max(0, boundary.clientHeight - panel.offsetHeight)
  return {
    x: Math.min(Math.max(0, x), maxX),
    y: Math.min(Math.max(0, y), maxY),
  }
}

function positionFromClient(clientX: number, clientY: number): { x: number; y: number } {
  const boundary = props.boundary
  if (!boundary) return { x: clientX, y: clientY }
  const b = boundary.getBoundingClientRect()
  return clampPosition(
    clientX - b.left - dragPointerOffsetX,
    clientY - b.top - dragPointerOffsetY,
  )
}

function onPanelFocus() {
  stackZ.value = props.zIndex + 1
}

function onDragStart(e: MouseEvent) {
  if (e.button !== 0) return
  const t = e.target as HTMLElement
  if (t.closest('button, .el-button, input, textarea, .el-input, .el-textarea')) return
  const head = (e.currentTarget as HTMLElement).getBoundingClientRect()
  dragPointerOffsetX = e.clientX - head.left
  dragPointerOffsetY = e.clientY - head.top
  dragging.value = true
  onPanelFocus()
  document.addEventListener('mousemove', onDragMove)
  document.addEventListener('mouseup', onDragEnd)
  e.preventDefault()
}

function onDragMove(e: MouseEvent) {
  if (!dragging.value) return
  const next = positionFromClient(e.clientX, e.clientY)
  posX.value = next.x
  posY.value = next.y
}

function onDragEnd() {
  dragging.value = false
  document.removeEventListener('mousemove', onDragMove)
  document.removeEventListener('mouseup', onDragEnd)
}

function onClose() {
  abortController?.abort()
  abortController = null
  emit('update:visible', false)
  emit('close')
}

async function refreshHealth() {
  healthStatus.value = 'unknown'
  try {
    const h = await getAiHealth()
    healthModel.value = h.model || ''
    if (!h.enabled || h.status === 'disabled') {
      healthStatus.value = 'disabled'
    } else if (h.status === 'ok' && h.model_ready) {
      healthStatus.value = 'ok'
    } else if (h.status === 'model_missing') {
      healthStatus.value = 'model_missing'
    } else {
      healthStatus.value = 'offline'
    }
  } catch {
    healthStatus.value = 'offline'
  }
}

async function scrollToBottom() {
  await nextTick()
  const el = messagesRef.value
  if (el) el.scrollTop = el.scrollHeight
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || sending.value) return

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  sending.value = true
  statusText.value = ''

  const assistantIdx = messages.value.length
  messages.value.push({ role: 'assistant', content: '' })
  await scrollToBottom()

  abortController?.abort()
  abortController = new AbortController()

  const payload = messages.value.slice(0, assistantIdx)

  try {
    await streamChat(
      payload,
      {
        onToken: (token) => {
          const msg = messages.value[assistantIdx]
          if (msg) msg.content += token
          scrollToBottom()
        },
        onStatus: (s) => {
          statusText.value = s
        },
        onError: (err) => {
          const msg = messages.value[assistantIdx]
          if (msg && !msg.content) {
            msg.content = t('aiAssistant.errorPrefix', { msg: err })
          }
        },
      },
      abortController.signal,
    )
  } catch (e) {
    const err = e instanceof Error ? e.message : String(e)
    const msg = messages.value[assistantIdx]
    if (msg && !msg.content) {
      msg.content = t('aiAssistant.errorPrefix', { msg: err })
    }
  } finally {
    sending.value = false
    statusText.value = ''
    abortController = null
    await scrollToBottom()
  }
}

onMounted(() => {
  if (props.visible) refreshHealth()
})

onBeforeUnmount(() => {
  document.removeEventListener('mousemove', onDragMove)
  document.removeEventListener('mouseup', onDragEnd)
  abortController?.abort()
})
</script>

<style scoped>
.ai-assistant-panel {
  position: absolute;
  display: flex;
  flex-direction: column;
  height: min(72vh, 560px);
  border-radius: 14px;
  border: 1px solid color-mix(in oklab, var(--el-border-color) 85%, var(--el-color-primary-light-7));
  background: var(--el-bg-color);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.6) inset,
    0 12px 32px rgba(31, 50, 81, 0.16),
    0 4px 12px rgba(31, 50, 81, 0.08);
  overflow: hidden;
  box-sizing: border-box;
}

.ai-assistant-panel--dragging {
  user-select: none;
  cursor: grabbing;
}

.ai-assistant-panel__head {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  border-bottom: 1px solid color-mix(in oklab, var(--el-border-color) 80%, transparent);
  background: linear-gradient(180deg, var(--el-fill-color-blank) 0%, var(--el-fill-color-light) 100%);
  cursor: grab;
  flex-shrink: 0;
}

.ai-assistant-panel__head:active {
  cursor: grabbing;
}

.ai-assistant-panel__grip {
  color: var(--el-text-color-secondary);
  flex-shrink: 0;
}

.ai-assistant-panel__title {
  font-size: 13px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  flex-shrink: 0;
}

.ai-assistant-panel__status {
  flex: 1;
  min-width: 0;
  font-size: 11px;
  text-align: right;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--el-text-color-secondary);
}

.ai-assistant-panel__status--ok {
  color: var(--el-color-success);
}

.ai-assistant-panel__status--offline,
.ai-assistant-panel__status--model_missing {
  color: var(--el-color-warning);
}

.ai-assistant-panel__actions {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.ai-assistant-panel__messages {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ai-assistant-panel__empty {
  color: var(--el-text-color-secondary);
  font-size: 13px;
  line-height: 1.5;
  text-align: center;
  margin: auto;
  padding: 16px;
}

.ai-assistant-panel__msg {
  display: flex;
}

.ai-assistant-panel__msg--user {
  justify-content: flex-end;
}

.ai-assistant-panel__msg--assistant {
  justify-content: flex-start;
}

.ai-assistant-panel__bubble {
  max-width: 88%;
  padding: 8px 12px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.55;
  white-space: pre-wrap;
  word-break: break-word;
}

.ai-assistant-panel__msg--user .ai-assistant-panel__bubble {
  background: var(--el-color-primary);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.ai-assistant-panel__msg--assistant .ai-assistant-panel__bubble {
  background: var(--el-fill-color-light);
  color: var(--el-text-color-primary);
  border-bottom-left-radius: 4px;
}

.ai-assistant-panel__status-line {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  text-align: center;
}

.ai-assistant-panel__input {
  flex-shrink: 0;
  display: flex;
  gap: 8px;
  align-items: flex-end;
  padding: 10px 12px 12px;
  border-top: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-blank);
}

.ai-assistant-panel__input :deep(.el-textarea) {
  flex: 1;
}
</style>
