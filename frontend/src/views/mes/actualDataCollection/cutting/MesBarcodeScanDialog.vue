<script setup lang="ts">
import { nextTick, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Camera, Switch } from '@element-plus/icons-vue'
import { Html5Qrcode, Html5QrcodeSupportedFormats } from 'html5-qrcode'

const SCANNER_ELEMENT_ID = 'mes-cut-barcode-scanner-region'

const props = defineProps<{
  modelValue: boolean
  productLabel?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  scanned: [code: string]
}>()

const { t } = useI18n()

const scanning = ref(false)
const starting = ref(false)
const useFrontCamera = ref(true)
let html5Qr: Html5Qrcode | null = null

const supportedFormats = [
  Html5QrcodeSupportedFormats.QR_CODE,
  Html5QrcodeSupportedFormats.AZTEC,
  Html5QrcodeSupportedFormats.CODABAR,
  Html5QrcodeSupportedFormats.CODE_39,
  Html5QrcodeSupportedFormats.CODE_93,
  Html5QrcodeSupportedFormats.CODE_128,
  Html5QrcodeSupportedFormats.DATA_MATRIX,
  Html5QrcodeSupportedFormats.EAN_13,
  Html5QrcodeSupportedFormats.EAN_8,
  Html5QrcodeSupportedFormats.ITF,
  Html5QrcodeSupportedFormats.PDF_417,
  Html5QrcodeSupportedFormats.UPC_A,
  Html5QrcodeSupportedFormats.UPC_E,
]

async function stopScanner(): Promise<void> {
  scanning.value = false
  if (!html5Qr) return
  try {
    if (html5Qr.isScanning) {
      await html5Qr.stop()
    }
    html5Qr.clear()
  } catch {
    /* ignore teardown races */
  }
  html5Qr = null
}

function closeDialog(): void {
  emit('update:modelValue', false)
}

async function onDetected(text: string): Promise<void> {
  const code = text.trim()
  if (!code) return
  await stopScanner()
  emit('scanned', code)
  closeDialog()
}

async function startScanner(): Promise<void> {
  if (starting.value || scanning.value) return
  starting.value = true
  try {
    await stopScanner()
    await nextTick()
    html5Qr = new Html5Qrcode(SCANNER_ELEMENT_ID, { verbose: false, formatsToSupport: supportedFormats })
    const constraints: MediaTrackConstraints = {
      facingMode: useFrontCamera.value ? 'user' : 'environment',
    }
    await html5Qr.start(
      constraints,
      {
        fps: 12,
        qrbox: (viewfinderWidth, viewfinderHeight) => {
          const w = Math.min(viewfinderWidth * 0.88, 320)
          const h = Math.min(viewfinderHeight * 0.42, 160)
          return { width: Math.floor(w), height: Math.floor(h) }
        },
        aspectRatio: 1.777,
      },
      (decoded) => {
        void onDetected(decoded)
      },
      () => {
        /* per-frame miss */
      },
    )
    scanning.value = true
  } catch (e: unknown) {
    console.error(e)
    ElMessage.error(t('mesCuttingActual.scanCameraFailed'))
    await stopScanner()
  } finally {
    starting.value = false
  }
}

async function toggleCamera(): Promise<void> {
  useFrontCamera.value = !useFrontCamera.value
  if (props.modelValue) {
    await startScanner()
  }
}

watch(
  () => props.modelValue,
  async (open) => {
    if (open) {
      await nextTick()
      await startScanner()
    } else {
      await stopScanner()
    }
  },
)

onUnmounted(() => {
  void stopScanner()
})
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    class="mes-barcode-scan-dialog"
    :title="t('mesCuttingActual.scanDialogTitle')"
    width="min(96vw, 420px)"
    align-center
    destroy-on-close
    :close-on-click-modal="false"
    @update:model-value="emit('update:modelValue', $event)"
    @closed="void stopScanner()"
  >
    <p v-if="productLabel" class="mes-barcode-scan-dialog__product">{{ productLabel }}</p>
    <p class="mes-barcode-scan-dialog__hint">{{ t('mesCuttingActual.scanDialogHint') }}</p>
    <div :id="SCANNER_ELEMENT_ID" class="mes-barcode-scan-dialog__viewport" />
    <div class="mes-barcode-scan-dialog__actions">
      <el-button :loading="starting" :disabled="scanning && starting" @click="toggleCamera">
        <el-icon><Switch /></el-icon>
        {{
          useFrontCamera
            ? t('mesCuttingActual.scanUseRearCamera')
            : t('mesCuttingActual.scanUseFrontCamera')
        }}
      </el-button>
      <el-button v-if="!scanning" type="primary" :loading="starting" @click="startScanner">
        <el-icon><Camera /></el-icon>
        {{ t('mesCuttingActual.scanRetryCamera') }}
      </el-button>
    </div>
    <template #footer>
      <el-button @click="closeDialog">{{ t('mesCuttingActual.btnCancelEdit') }}</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.mes-barcode-scan-dialog__product {
  margin: 0 0 6px;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--el-text-color-primary);
  line-height: 1.35;
}

.mes-barcode-scan-dialog__hint {
  margin: 0 0 10px;
  font-size: 0.78rem;
  color: var(--el-text-color-secondary);
  line-height: 1.4;
}

.mes-barcode-scan-dialog__viewport {
  width: 100%;
  min-height: 240px;
  border-radius: 8px;
  overflow: hidden;
  background: #111;
}

.mes-barcode-scan-dialog__viewport :deep(video) {
  border-radius: 8px;
}

.mes-barcode-scan-dialog__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}
</style>
