<template>
  <div class="edi-import-page">
    <div class="dynamic-background">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="noise-overlay"></div>
    </div>

    <div class="glass-header animate-in">
      <div class="header-content">
        <div class="header-left">
          <div class="header-icon">
            <el-icon size="26"><Upload /></el-icon>
          </div>
          <div class="header-text">
            <h1 class="header-title">EDI取込</h1>
            <div class="header-subtitle">Electronic Data Interchange Import</div>
          </div>
        </div>
      </div>
    </div>

    <div class="content-area">
      <div class="upload-section glass-card animate-in" style="animation-delay: 0.1s">
        <div class="upload-inner">
          <el-upload
            class="upload-zone"
            drag
            action=""
            :auto-upload="false"
            :on-change="handleFileChange"
            accept=".csv,.xlsx,.xls,.txt,.edi"
          >
            <div class="upload-content">
              <el-icon size="48" class="upload-icon"><Upload /></el-icon>
              <div class="upload-text">EDIファイルをドラッグ＆ドロップ</div>
              <div class="upload-hint">CSV, Excel, EDIファイルに対応 (.csv, .xlsx, .xls, .txt, .edi)</div>
            </div>
          </el-upload>
        </div>
      </div>

      <div class="options-section glass-card animate-in" style="animation-delay: 0.15s">
        <h3 class="section-label">取込設定</h3>
        <div class="options-grid">
          <div class="option-item">
            <label>データ種別</label>
            <el-select v-model="importType" placeholder="選択してください" size="small">
              <el-option label="受注データ" value="order" />
              <el-option label="内示データ" value="forecast" />
              <el-option label="出荷指示" value="shipping" />
            </el-select>
          </div>
          <div class="option-item">
            <label>重複処理</label>
            <el-select v-model="duplicateAction" placeholder="選択" size="small">
              <el-option label="スキップ" value="skip" />
              <el-option label="上書き" value="overwrite" />
              <el-option label="エラー" value="error" />
            </el-select>
          </div>
          <div class="option-item">
            <label>文字コード</label>
            <el-select v-model="encoding" placeholder="選択" size="small">
              <el-option label="UTF-8" value="utf8" />
              <el-option label="Shift-JIS" value="sjis" />
              <el-option label="EUC-JP" value="eucjp" />
            </el-select>
          </div>
        </div>
        <div class="action-row">
          <el-button type="primary" :disabled="!selectedFile" :loading="importing" @click="handleImport">
            取込実行
          </el-button>
          <el-button @click="resetForm">リセット</el-button>
        </div>
      </div>

      <div v-if="importResult" class="result-section glass-card animate-in" style="animation-delay: 0.2s">
        <h3 class="section-label">取込結果</h3>
        <div class="result-stats">
          <div class="result-stat success">
            <span class="result-num">{{ importResult.success }}</span>
            <span class="result-lbl">成功</span>
          </div>
          <div class="result-stat error">
            <span class="result-num">{{ importResult.errors }}</span>
            <span class="result-lbl">エラー</span>
          </div>
          <div class="result-stat skip">
            <span class="result-num">{{ importResult.skipped }}</span>
            <span class="result-lbl">スキップ</span>
          </div>
        </div>
        <div v-if="importResult.errorDetails.length" class="error-list">
          <div v-for="(err, i) in importResult.errorDetails" :key="i" class="error-item">
            <span class="error-line">行{{ err.line }}:</span>
            <span class="error-msg">{{ err.message }}</span>
          </div>
        </div>
      </div>

      <div class="history-section glass-card animate-in" style="animation-delay: 0.25s">
        <h3 class="section-label">取込履歴</h3>
        <el-table :data="history" class="dark-table" size="small" :header-cell-style="tableHeaderStyle" :cell-style="tableCellStyle">
          <el-table-column prop="imported_at" label="取込日時" width="160" />
          <el-table-column prop="filename" label="ファイル名" min-width="180" show-overflow-tooltip />
          <el-table-column prop="type" label="種別" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="row.type === 'order' ? 'primary' : row.type === 'forecast' ? 'warning' : 'success'">
                {{ row.type === 'order' ? '受注' : row.type === 'forecast' ? '内示' : '出荷' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="total" label="件数" width="80" align="center" />
          <el-table-column prop="success_count" label="成功" width="80" align="center" />
          <el-table-column prop="error_count" label="エラー" width="80" align="center" />
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Upload } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const importType = ref('order')
const duplicateAction = ref('skip')
const encoding = ref('utf8')
const selectedFile = ref<File | null>(null)
const importing = ref(false)
const importResult = ref<{ success: number; errors: number; skipped: number; errorDetails: { line: number; message: string }[] } | null>(null)

const history = ref<any[]>([])

const tableHeaderStyle = { background: 'linear-gradient(135deg, #3b82f6, #6366f1)', color: '#fff', fontWeight: '600', fontSize: '12px', padding: '6px 10px' }
const tableCellStyle = { padding: '5px 8px', fontSize: '12px', background: 'rgba(255,255,255,0.03)', color: 'rgba(255,255,255,0.85)', borderColor: 'rgba(255,255,255,0.06)' }

function handleFileChange(file: any) {
  selectedFile.value = file.raw
}

async function handleImport() {
  if (!selectedFile.value) return
  importing.value = true
  try {
    await new Promise(r => setTimeout(r, 1500))
    importResult.value = { success: 0, errors: 0, skipped: 0, errorDetails: [] }
    ElMessage.info('EDI取込機能は準備中です')
  } catch {
    ElMessage.error('取込に失敗しました')
  } finally {
    importing.value = false
  }
}

function resetForm() {
  selectedFile.value = null
  importResult.value = null
  importType.value = 'order'
  duplicateAction.value = 'skip'
  encoding.value = 'utf8'
}
</script>

<style scoped>
.edi-import-page { position: relative; min-height: 100vh; padding: 16px; overflow: hidden; }
.dynamic-background { position: fixed; inset: 0; z-index: 0; background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%); }
.gradient-orb { position: absolute; border-radius: 50%; filter: blur(80px); opacity: 0.4; animation: float 20s ease-in-out infinite; }
.orb-1 { width: 350px; height: 350px; top: -80px; left: -80px; background: radial-gradient(circle, #3b82f6, transparent); }
.orb-2 { width: 300px; height: 300px; bottom: -50px; right: -50px; background: radial-gradient(circle, #8b5cf6, transparent); animation-delay: -10s; }
.noise-overlay { position: absolute; inset: 0; opacity: 0.03; }
@keyframes float { 0%,100%{transform:translate(0,0) scale(1)} 50%{transform:translate(20px,-20px) scale(1.03)} }

.glass-header { position: relative; z-index: 1; background: rgba(255,255,255,0.08); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.12); border-radius: 16px; padding: 14px 20px; margin-bottom: 14px; }
.header-content { display: flex; align-items: center; }
.header-left { display: flex; align-items: center; gap: 12px; }
.header-icon { width: 44px; height: 44px; background: linear-gradient(135deg, #3b82f6, #8b5cf6); border-radius: 12px; display: flex; align-items: center; justify-content: center; color: #fff; }
.header-title { font-size: 1.4rem; font-weight: 700; color: #fff; margin: 0; }
.header-subtitle { font-size: 0.75rem; color: rgba(255,255,255,0.5); margin-top: 2px; }

.content-area { position: relative; z-index: 1; display: flex; flex-direction: column; gap: 12px; }
.glass-card { background: rgba(255,255,255,0.06); backdrop-filter: blur(16px); border: 1px solid rgba(255,255,255,0.1); border-radius: 14px; padding: 16px; }

.upload-section { text-align: center; }
.upload-zone { width: 100%; }
:deep(.el-upload-dragger) { background: rgba(255,255,255,0.04); border: 2px dashed rgba(255,255,255,0.15); border-radius: 12px; padding: 30px 20px; transition: all 0.3s; }
:deep(.el-upload-dragger:hover) { border-color: rgba(59,130,246,0.5); background: rgba(59,130,246,0.05); }
.upload-icon { color: rgba(255,255,255,0.4); margin-bottom: 8px; }
.upload-text { font-size: 0.95rem; color: rgba(255,255,255,0.8); font-weight: 500; }
.upload-hint { font-size: 0.75rem; color: rgba(255,255,255,0.4); margin-top: 6px; }

.section-label { font-size: 0.9rem; font-weight: 600; color: rgba(255,255,255,0.9); margin: 0 0 12px; }
.options-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; margin-bottom: 14px; }
.option-item label { display: block; font-size: 0.72rem; color: rgba(255,255,255,0.5); margin-bottom: 4px; }
.action-row { display: flex; gap: 8px; }

.result-stats { display: flex; gap: 16px; margin-bottom: 12px; }
.result-stat { display: flex; flex-direction: column; align-items: center; padding: 10px 20px; border-radius: 10px; }
.result-stat.success { background: rgba(16,185,129,0.15); }
.result-stat.error { background: rgba(239,68,68,0.15); }
.result-stat.skip { background: rgba(245,158,11,0.15); }
.result-num { font-size: 1.5rem; font-weight: 700; color: #fff; }
.result-lbl { font-size: 0.7rem; color: rgba(255,255,255,0.6); }
.error-list { max-height: 150px; overflow-y: auto; }
.error-item { padding: 4px 0; font-size: 0.78rem; color: rgba(255,255,255,0.7); }
.error-line { color: #ef4444; font-weight: 600; margin-right: 6px; }

.dark-table { width: 100%; }
:deep(.el-table) { background: transparent; --el-table-bg-color: transparent; --el-table-tr-bg-color: transparent; --el-table-border-color: rgba(255,255,255,0.06); --el-table-header-bg-color: transparent; --el-table-row-hover-bg-color: rgba(255,255,255,0.05); }
:deep(.el-table th), :deep(.el-table td) { border-color: rgba(255,255,255,0.06); }
:deep(.el-table__empty-text) { color: rgba(255,255,255,0.4); }

.animate-in { animation: slideIn 0.5s ease forwards; opacity: 0; transform: translateY(12px); }
@keyframes slideIn { to { opacity: 1; transform: translateY(0); } }

@media (max-width: 768px) { .edi-import-page { padding: 10px; } .options-grid { grid-template-columns: 1fr; } }
</style>
