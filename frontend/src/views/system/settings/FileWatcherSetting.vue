<template>
  <div class="file-watcher-setting">
    <header class="top-bar">
      <div class="top-bar__brand">
        <div class="top-bar__icon" aria-hidden="true">
          <el-icon :size="22"><Monitor /></el-icon>
        </div>
        <div class="top-bar__text">
          <h1 class="top-bar__title">ファイル監視設定</h1>
          <p class="top-bar__desc">
            BT-data 受信 CSV・ピッキングログ・Excel 計画の監視を切り替え
          </p>
        </div>
      </div>
      <el-button type="primary" :icon="Check" :loading="saving" class="top-bar__save" @click="handleSave">
        保存
      </el-button>
    </header>

    <el-card class="main-card" shadow="hover" v-loading="loading">
      <template #header>
        <div class="card-head">
          <span class="card-head__label">監視対象</span>
          <el-tag size="small" effect="plain" type="info">再起動不要で反映</el-tag>
        </div>
      </template>

      <div class="panels">
        <section class="panel">
          <div class="panel__head">
            <el-icon class="panel__head-icon" :size="18"><Box /></el-icon>
            <div class="panel__head-text">
              <h2 class="panel__title">在庫関連 CSV</h2>
              <span class="panel__target">stock_transaction_logs</span>
            </div>
          </div>
          <div class="panel__body">
            <template v-if="stockFiles.length">
              <div v-for="name in stockFiles" :key="name" class="file-row">
                <span class="file-name" :title="name">{{ name }}</span>
                <el-switch v-model="enabled[name]" size="small" />
              </div>
            </template>
            <p v-else class="empty-hint">定義されたファイルがありません</p>
          </div>
        </section>

        <section class="panel">
          <div class="panel__head">
            <el-icon class="panel__head-icon" :size="18"><CollectionTag /></el-icon>
            <div class="panel__head-text">
              <h2 class="panel__title">材料関連 CSV</h2>
              <span class="panel__target">material_logs</span>
            </div>
          </div>
          <div class="panel__body">
            <template v-if="materialFiles.length">
              <div v-for="name in materialFiles" :key="name" class="file-row">
                <span class="file-name" :title="name">{{ name }}</span>
                <el-switch v-model="enabled[name]" size="small" />
              </div>
            </template>
            <p v-else class="empty-hint">定義されたファイルがありません</p>
          </div>
        </section>

        <section class="panel">
          <div class="panel__head">
            <el-icon class="panel__head-icon" :size="18"><Van /></el-icon>
            <div class="panel__head-text">
              <h2 class="panel__title">ピッキングログ CSV</h2>
              <span class="panel__target">shipping_log</span>
            </div>
          </div>
          <div class="panel__body">
            <template v-if="pickingFiles.length">
              <div v-for="name in pickingFiles" :key="name" class="file-row">
                <span class="file-name" :title="name">{{ name }}</span>
                <el-switch v-model="enabled[name]" size="small" />
              </div>
            </template>
            <p v-else class="empty-hint">定義されたファイルがありません</p>
          </div>
        </section>

        <section class="panel panel--excel">
          <div class="panel__head">
            <el-icon class="panel__head-icon" :size="18"><Document /></el-icon>
            <div class="panel__head-text">
              <h2 class="panel__title">Excel 計画</h2>
              <span class="panel__target">加工・溶接 .xlsm → production_plan_*</span>
            </div>
          </div>
          <div class="panel__body">
            <div class="file-row file-row--single">
              <span class="file-name file-name--wrap">計画更新・加工状況・操業度の監視</span>
              <el-switch v-model="excelWatcherEnabled" size="small" />
            </div>
          </div>
        </section>
      </div>

      <el-alert type="info" :closable="false" show-icon class="tip">
        オフにしたファイル／Excel 監視は同期されません。設定は監視プロセスに即時反映されます。
      </el-alert>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Monitor, Check, Box, CollectionTag, Van, Document } from '@element-plus/icons-vue'
import { getFileWatcherSettings, updateFileWatcherSettings } from '@/api/system'

const loading = ref(false)
const saving = ref(false)
const stockFiles = ref<string[]>([])
const materialFiles = ref<string[]>([])
const pickingFiles = ref<string[]>([])
const excelWatcherEnabled = ref(true)
const enabled = ref<Record<string, boolean>>({})

async function load() {
  loading.value = true
  try {
    const res = await getFileWatcherSettings()
    stockFiles.value = res.stockFiles || []
    materialFiles.value = res.materialFiles || []
    pickingFiles.value = res.pickingFiles || []
    excelWatcherEnabled.value = res.excelWatcherEnabled !== false
    enabled.value = { ...(res.enabled || {}) }
  } catch (e) {
    ElMessage.error('取得に失敗しました')
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  saving.value = true
  try {
    await updateFileWatcherSettings({
      enabled: enabled.value,
      excelWatcherEnabled: excelWatcherEnabled.value,
    })
    ElMessage.success('保存しました')
  } catch (e) {
    ElMessage.error('保存に失敗しました')
    console.error(e)
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.file-watcher-setting {
  --fw-accent: #5b6ee8;
  --fw-accent-soft: color-mix(in srgb, var(--fw-accent) 14%, transparent);
  padding: 8px 12px 14px;
  max-width: 1100px;
  margin: 0 auto;
}

.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
  padding: 8px 2px 4px;
}

.top-bar__brand {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.top-bar__icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #5b6ee8 0%, #7c3aed 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 2px 8px color-mix(in srgb, #5b6ee8 35%, transparent);
}

.top-bar__text {
  min-width: 0;
}

.top-bar__title {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1.25;
  color: var(--el-text-color-primary);
}

.top-bar__desc {
  margin: 2px 0 0;
  font-size: 0.75rem;
  line-height: 1.35;
  color: var(--el-text-color-secondary);
}

.top-bar__save {
  flex-shrink: 0;
}

.main-card {
  border-radius: 12px;
  border: 1px solid var(--el-border-color-lighter);
}

.main-card :deep(.el-card__header) {
  padding: 8px 14px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.main-card :deep(.el-card__body) {
  padding: 12px 14px 14px;
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.card-head__label {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--el-text-color-regular);
}

.panels {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

@media (max-width: 768px) {
  .panels {
    grid-template-columns: 1fr;
  }
}

.panel {
  border-radius: 10px;
  border: 1px solid var(--el-border-color-lighter);
  background: linear-gradient(
    165deg,
    var(--el-bg-color) 0%,
    color-mix(in srgb, var(--el-fill-color-blank) 88%, var(--fw-accent-soft)) 100%
  );
  overflow: hidden;
  min-height: 0;
}

.panel--excel {
  grid-column: 1 / -1;
}

.panel__head {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 10px;
  border-bottom: 1px solid var(--el-border-color-extra-light);
  background: color-mix(in srgb, var(--el-fill-color-light) 65%, transparent);
}

.panel__head-icon {
  flex-shrink: 0;
  margin-top: 1px;
  color: var(--fw-accent);
}

.panel__head-text {
  min-width: 0;
}

.panel__title {
  margin: 0;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--el-text-color-primary);
  line-height: 1.3;
}

.panel__target {
  display: block;
  margin-top: 2px;
  font-size: 0.6875rem;
  font-family: ui-monospace, 'Cascadia Code', monospace;
  color: var(--el-text-color-secondary);
  word-break: break-all;
}

.panel__body {
  padding: 8px 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.file-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 6px 10px;
  border-radius: 8px;
  background: var(--el-fill-color-blank);
  border: 1px solid var(--el-border-color-extra-light);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.file-row:hover {
  border-color: color-mix(in srgb, var(--fw-accent) 28%, var(--el-border-color-lighter));
  box-shadow: 0 1px 4px color-mix(in srgb, var(--fw-accent) 8%, transparent);
}

.file-row--single {
  align-items: flex-start;
}

.file-name {
  font-family: ui-monospace, 'Cascadia Code', monospace;
  font-size: 0.75rem;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

.file-name--wrap {
  white-space: normal;
  line-height: 1.35;
}

.empty-hint {
  margin: 0;
  padding: 10px 8px;
  font-size: 0.75rem;
  color: var(--el-text-color-placeholder);
  text-align: center;
}

.tip {
  margin-top: 10px;
}

.tip :deep(.el-alert__content) {
  font-size: 0.75rem;
  line-height: 1.45;
}
</style>
