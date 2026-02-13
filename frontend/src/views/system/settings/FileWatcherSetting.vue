<template>
  <div class="file-watcher-setting">
    <div class="page-header">
      <div class="header-content">
        <div class="header-icon">
          <el-icon :size="28"><Monitor /></el-icon>
        </div>
        <div class="header-text">
          <h1>ファイル監視設定</h1>
          <p class="subtitle">BT-data 受信 CSV・ピッキングログ・Excel 計画の監視対象を有効/無効にします</p>
        </div>
      </div>
    </div>

    <el-card class="settings-card" shadow="never" v-loading="loading">
      <template #header>
        <span>監視対象ファイル</span>
        <el-button type="primary" :icon="Check" @click="handleSave" :loading="saving" style="float: right">
          保存
        </el-button>
      </template>

      <div class="section">
        <h3 class="section-title">在庫関連 CSV（stock_transaction_logs へ同期）</h3>
        <div class="file-list">
          <div v-for="name in stockFiles" :key="name" class="file-row">
            <span class="file-name">{{ name }}</span>
            <el-switch v-model="enabled[name]" />
          </div>
        </div>
      </div>

      <div class="section">
        <h3 class="section-title">材料関連 CSV（material_logs へ同期）</h3>
        <div class="file-list">
          <div v-for="name in materialFiles" :key="name" class="file-row">
            <span class="file-name">{{ name }}</span>
            <el-switch v-model="enabled[name]" />
          </div>
        </div>
      </div>

      <div class="section">
        <h3 class="section-title">ピッキングログ CSV（shipping_log へ同期）</h3>
        <div class="file-list">
          <div v-for="name in pickingFiles" :key="name" class="file-row">
            <span class="file-name">{{ name }}</span>
            <el-switch v-model="enabled[name]" />
          </div>
        </div>
      </div>

      <div class="section">
        <h3 class="section-title">Excel 計画（加工・溶接 .xlsm → production_plan_*）</h3>
        <div class="file-row">
          <span class="file-name">計画更新・加工状況・操業度の監視</span>
          <el-switch v-model="excelWatcherEnabled" />
        </div>
      </div>

      <el-alert type="info" :closable="false" show-icon class="tip">
        オフにしたファイル／Excel 監視は対象外となり、更新されても同期されません。監視プロセスは再起動不要で設定を反映します。
      </el-alert>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Monitor, Check } from '@element-plus/icons-vue'
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
  padding: 0 16px 24px;
}
.page-header {
  margin-bottom: 20px;
}
.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}
.header-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}
.header-text h1 {
  margin: 0 0 4px 0;
  font-size: 1.5rem;
  font-weight: 600;
}
.subtitle {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 0.9rem;
}
.settings-card {
  max-width: 720px;
}
.section {
  margin-bottom: 24px;
}
.section:last-of-type {
  margin-bottom: 0;
}
.section-title {
  margin: 0 0 12px 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--el-text-color-primary);
}
.file-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.file-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
}
.file-name {
  font-family: ui-monospace, monospace;
  font-size: 0.9rem;
}
.tip {
  margin-top: 20px;
}
</style>
