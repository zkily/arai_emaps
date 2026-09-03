<template>
  <div class="device-owner-qr">
    <header class="top-bar">
      <div class="top-bar__brand">
        <div class="top-bar__icon" aria-hidden="true">
          <el-icon :size="22"><Iphone /></el-icon>
        </div>
        <div class="top-bar__text">
          <h1 class="top-bar__title">Device Owner QR</h1>
          <p class="top-bar__desc">
            Android 平板の工場出荷用 QR（Provisioning）。ページを開くと自動生成します。
          </p>
        </div>
      </div>
      <el-button type="primary" :icon="Refresh" :loading="loading" @click="refreshAll">
        再生成
      </el-button>
    </header>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="14">
        <el-card shadow="hover" class="panel" v-loading="loading">
          <template #header>
            <div class="card-head">
              <span>配布設定</span>
              <el-tag size="small" :type="status?.has_apk ? 'success' : 'warning'" effect="plain">
                {{ status?.has_apk ? 'APK 登録済み' : 'APK 未登録' }}
              </el-tag>
            </div>
          </template>

          <el-form label-position="top" class="form">
            <el-form-item label="APK 公開 URL（Cloudflare Tunnel 等）">
              <el-input
                v-model="publicBaseUrl"
                placeholder="https://xxxx.trycloudflare.com/smart-emap.apk"
                clearable
                @change="onSettingsChanged"
              />
              <div class="hint">
                どちらでも可：
                <br />・フル URL：<code>https://….trycloudflare.com/smart-emap.apk</code>（静的トンネル）
                <br />・ベースのみ：<code>https://….trycloudflare.com</code>（自動で
                <code>/api/system/device-owner/apk/download</code> を付与）
              </div>
            </el-form-item>

            <el-form-item label="APK アップロード">
              <el-upload
                drag
                :auto-upload="false"
                :show-file-list="false"
                accept=".apk"
                :on-change="onApkSelected"
              >
                <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
                <div class="el-upload__text">APK をドラッグ、または <em>クリック</em></div>
              </el-upload>
              <div v-if="status?.has_apk" class="apk-meta">
                <div><strong>{{ status.filename }}</strong></div>
                <div>サイズ: {{ formatBytes(status.size_bytes) }}</div>
                <div>アップロード: {{ formatTime(status.uploaded_at) }}</div>
                <div class="mono">PACKAGE_CHECKSUM: {{ status.package_checksum }}</div>
              </div>
            </el-form-item>

            <el-form-item label="署名 checksum（任意・推奨）">
              <el-input
                v-model="signatureChecksum"
                placeholder="URL-safe Base64（apksigner の SHA-256）"
                clearable
                @change="onSettingsChanged"
              />
            </el-form-item>

            <div class="actions">
              <el-button type="primary" :loading="saving" @click="saveSettings">設定を保存</el-button>
              <el-button
                :disabled="!payload?.download_url"
                @click="copyText(payload?.download_url || '')"
              >
                ダウンロード URL をコピー
              </el-button>
            </div>
          </el-form>

          <el-alert
            v-if="payload?.warning"
            type="warning"
            :closable="false"
            show-icon
            class="warn"
            :title="payload.warning"
          />

          <el-alert type="info" :closable="false" show-icon class="tip">
            <template #title>この QR は「ダウンロード用リンク」ではありません</template>
            中身は Android Enterprise の <strong>Provisioning JSON</strong> です。普通のカメラで読むと
            <strong>文字列 / JSON テキスト</strong>に見えます（正常）。使い方：平板を初期化 →
            ようこそ画面を約 6 回タップ → QR スキャナが出たらこのコードをスキャン。ブラウザや通常の QR
            アプリでは Device Owner になりません。
          </el-alert>

          <el-alert type="info" :closable="false" show-icon class="tip">
            手順: ① APK アップロード ② Tunnel で APK を公開 ③ 上の URL を保存 → QR 自動更新 ④
            初期化セットアップでスキャン
          </el-alert>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="10">
        <el-card shadow="hover" class="panel qr-panel" v-loading="loading">
          <template #header>
            <div class="card-head">
              <span>開通 QR（自動生成）</span>
            </div>
          </template>

          <div v-if="qrDataUrl" class="qr-wrap">
            <img :src="qrDataUrl" alt="Device Owner Provisioning QR" class="qr-img" />
            <p class="qr-caption">
              初期化セットアップの QR スキャナ専用（通常アプリでは文字列になります）
            </p>
            <div class="qr-actions">
              <el-button type="primary" @click="downloadQrPng">QR 画像を保存</el-button>
              <el-button @click="copyText(payload?.qr_text || '')">JSON をコピー</el-button>
            </div>
            <details v-if="payload?.qr_text" class="json-preview">
              <summary>QR に埋め込まれた JSON を表示</summary>
              <pre>{{ prettyQrJson }}</pre>
            </details>
          </div>
          <el-empty v-else description="APK と公開 URL を設定すると QR が表示されます" />

          <div v-if="payload?.download_url" class="mono url-box">
            <div class="url-box__label">実際の APK ダウンロード先（QR JSON 内）</div>
            {{ payload.download_url }}
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { UploadFile } from 'element-plus'
import { Iphone, Refresh, UploadFilled } from '@element-plus/icons-vue'
import {
  getDeviceOwnerProvisioningPayload,
  getDeviceOwnerStatus,
  updateDeviceOwnerSettings,
  uploadDeviceOwnerApk,
  type DeviceOwnerProvisioningPayload,
  type DeviceOwnerStatus,
} from '@/api/system'

const loading = ref(false)
const saving = ref(false)
const uploading = ref(false)
const status = ref<DeviceOwnerStatus | null>(null)
const payload = ref<DeviceOwnerProvisioningPayload | null>(null)
const publicBaseUrl = ref('')
const signatureChecksum = ref('')
const qrDataUrl = ref('')

const prettyQrJson = computed(() => {
  if (!payload.value?.qr_json) return payload.value?.qr_text || ''
  try {
    return JSON.stringify(payload.value.qr_json, null, 2)
  } catch {
    return payload.value.qr_text || ''
  }
})

function formatBytes(n: number | null | undefined) {
  if (n == null) return '—'
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / (1024 * 1024)).toFixed(1)} MB`
}

function formatTime(iso: string | null | undefined) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

async function generateQr(text: string) {
  if (!text) {
    qrDataUrl.value = ''
    return
  }
  const QRCode = (await import('qrcode')).default
  qrDataUrl.value = await QRCode.toDataURL(text, {
    width: 360,
    margin: 2,
    errorCorrectionLevel: 'M',
    color: { dark: '#111827', light: '#ffffff' },
  })
}

async function refreshAll() {
  loading.value = true
  try {
    status.value = await getDeviceOwnerStatus()
    publicBaseUrl.value = status.value.public_base_url || publicBaseUrl.value || window.location.origin
    signatureChecksum.value = status.value.signature_checksum || ''

    const base = (publicBaseUrl.value || '').trim()
    payload.value = await getDeviceOwnerProvisioningPayload(base || undefined)
    await generateQr(payload.value.qr_text || '')
  } catch (e: unknown) {
    const msg =
      (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
      '状態の取得に失敗しました'
    ElMessage.error(String(msg))
    qrDataUrl.value = ''
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  saving.value = true
  try {
    status.value = await updateDeviceOwnerSettings({
      public_base_url: publicBaseUrl.value.trim(),
      signature_checksum: signatureChecksum.value.trim(),
    })
    ElMessage.success('設定を保存しました')
    await refreshAll()
  } catch (e: unknown) {
    const msg =
      (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '保存に失敗しました'
    ElMessage.error(String(msg))
  } finally {
    saving.value = false
  }
}

async function onSettingsChanged() {
  // 入力変更後すぐに QR を試し再生成（未保存の URL もクエリで反映）
  loading.value = true
  try {
    payload.value = await getDeviceOwnerProvisioningPayload(publicBaseUrl.value.trim() || undefined)
    await generateQr(payload.value.qr_text || '')
  } finally {
    loading.value = false
  }
}

async function onApkSelected(uploadFile: UploadFile) {
  const raw = uploadFile.raw
  if (!raw) return
  if (!raw.name.toLowerCase().endsWith('.apk')) {
    ElMessage.warning('APK ファイルを選択してください')
    return
  }
  uploading.value = true
  loading.value = true
  try {
    status.value = await uploadDeviceOwnerApk(raw)
    ElMessage.success('APK をアップロードしました')
    await refreshAll()
  } catch (e: unknown) {
    const msg =
      (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
      'アップロードに失敗しました'
    ElMessage.error(String(msg))
  } finally {
    uploading.value = false
    loading.value = false
  }
}

async function copyText(text: string) {
  if (!text) return
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('コピーしました')
  } catch {
    ElMessage.error('コピーに失敗しました')
  }
}

function downloadQrPng() {
  if (!qrDataUrl.value) return
  const a = document.createElement('a')
  a.href = qrDataUrl.value
  a.download = 'smart-emap-device-owner-qr.png'
  a.click()
}

onMounted(() => {
  refreshAll()
})
</script>

<style scoped>
.device-owner-qr {
  padding: 16px;
  min-height: 100%;
  background: linear-gradient(160deg, #f8fafc 0%, #eef2ff 100%);
}

.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
  padding: 16px 20px;
  border-radius: 14px;
  background: #0f172a;
  color: #f8fafc;
}

.top-bar__brand {
  display: flex;
  gap: 14px;
  align-items: center;
}

.top-bar__icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: rgba(99, 102, 241, 0.25);
  color: #c7d2fe;
}

.top-bar__title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 700;
}

.top-bar__desc {
  margin: 4px 0 0;
  font-size: 0.85rem;
  color: #cbd5e1;
}

.panel {
  margin-bottom: 16px;
  border-radius: 12px;
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-weight: 600;
}

.hint {
  margin-top: 6px;
  font-size: 12px;
  color: #64748b;
  line-height: 1.5;
}

.apk-meta {
  margin-top: 12px;
  padding: 12px;
  border-radius: 8px;
  background: #f1f5f9;
  font-size: 13px;
  line-height: 1.6;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  word-break: break-all;
  font-size: 12px;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.warn,
.tip {
  margin-top: 12px;
}

.qr-panel {
  text-align: center;
}

.qr-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.qr-img {
  width: min(360px, 100%);
  height: auto;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  background: #fff;
}

.qr-caption {
  margin: 0;
  color: #475569;
  font-size: 13px;
}

.qr-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.url-box {
  margin-top: 16px;
  padding: 10px;
  border-radius: 8px;
  background: #0f172a;
  color: #e2e8f0;
  text-align: left;
}

.url-box__label {
  margin-bottom: 6px;
  font-size: 11px;
  color: #94a3b8;
  font-family: inherit;
}

.json-preview {
  width: 100%;
  margin-top: 8px;
  text-align: left;
  font-size: 12px;
  color: #475569;
}

.json-preview pre {
  margin: 8px 0 0;
  padding: 10px;
  max-height: 220px;
  overflow: auto;
  border-radius: 8px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
