<template>
  <div class="edi-import" :class="{ 'edi-import-embedded': embedded }">
    <div v-if="!embedded" class="page-header">
      <h2>EDI取込</h2>
      <p class="subtitle">顧客フォーマット（CSV/XML）の受注データ自動取込</p>
    </div>
    <p v-else class="embedded-subtitle">顧客フォーマット（CSV/XML）の受注データ自動取込</p>

    <!-- アップロードエリア -->
    <el-card class="upload-card" shadow="never">
      <el-upload
        ref="uploadRef"
        class="upload-area"
        drag
        :auto-upload="false"
        :on-change="handleFileChange"
        :file-list="fileList"
        accept=".csv,.xml"
      >
        <el-icon class="upload-icon"><Upload /></el-icon>
        <div class="upload-text">ファイルをドラッグ＆ドロップ、またはクリックして選択</div>
        <template #tip>
          <div class="upload-tip">対応フォーマット: CSV, XML（最大10MB）</div>
        </template>
      </el-upload>

      <div class="upload-options">
        <el-form :inline="true" :model="importOptions">
          <el-form-item label="顧客">
            <el-select v-model="importOptions.customer_code" placeholder="顧客を選択" filterable>
              <el-option v-for="c in customers" :key="c.cd" :label="c.name" :value="c.cd" />
            </el-select>
          </el-form-item>
          <el-form-item label="フォーマット">
            <el-select v-model="importOptions.format" placeholder="フォーマット選択">
              <el-option label="標準CSV" value="standard_csv" />
              <el-option label="顧客A形式" value="customer_a" />
              <el-option label="顧客B形式(XML)" value="customer_b_xml" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleParse" :loading="parsing">
              <el-icon><DataAnalysis /></el-icon> 解析実行
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>

    <!-- 解析結果プレビュー -->
    <el-card v-if="parsedData.length > 0" shadow="never">
      <template #header>
        <div class="card-header">
          <span>解析結果プレビュー（{{ parsedData.length }}件）</span>
          <div>
            <el-button type="success" @click="handleImport" :loading="importing">
              <el-icon><Check /></el-icon> 取込実行
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="parsedData" stripe border max-height="400">
        <el-table-column type="index" label="No" width="60" />
        <el-table-column prop="order_date" label="受注日" width="110" />
        <el-table-column prop="customer_order_no" label="顧客注文番号" width="140" />
        <el-table-column prop="product_code" label="品番" width="120" />
        <el-table-column prop="product_name" label="品名" min-width="150" show-overflow-tooltip />
        <el-table-column prop="quantity" label="数量" width="90" align="right" />
        <el-table-column prop="unit_price" label="単価" width="100" align="right">
          <template #default="{ row }">¥{{ row.unit_price?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="delivery_date" label="納期" width="110" />
        <el-table-column prop="status" label="検証" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.valid ? 'success' : 'danger'">{{ row.valid ? 'OK' : 'エラー' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="error_message" label="エラー内容" min-width="200" show-overflow-tooltip />
      </el-table>
    </el-card>

    <!-- 取込履歴 -->
    <el-card shadow="never" class="history-card">
      <template #header>
        <span>取込履歴</span>
      </template>
      <el-table :data="importHistory" stripe size="small">
        <el-table-column prop="import_date" label="取込日時" width="160" />
        <el-table-column prop="file_name" label="ファイル名" min-width="200" />
        <el-table-column prop="customer_name" label="顧客" width="150" />
        <el-table-column prop="total_count" label="件数" width="80" align="right" />
        <el-table-column prop="success_count" label="成功" width="80" align="right">
          <template #default="{ row }">
            <span class="success-count">{{ row.success_count }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="error_count" label="エラー" width="80" align="right">
          <template #default="{ row }">
            <span :class="row.error_count > 0 ? 'error-count' : ''">{{ row.error_count }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="imported_by" label="実行者" width="120" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload, DataAnalysis, Check } from '@element-plus/icons-vue'
import type { UploadFile } from 'element-plus'

defineProps<{ embedded?: boolean }>()

const uploadRef = ref()
const fileList = ref<UploadFile[]>([])
const parsing = ref(false)
const importing = ref(false)
const parsedData = ref<any[]>([])
const importHistory = ref<any[]>([])
const customers = ref<{ cd: string; name: string }[]>([])

const importOptions = reactive({
  customer_code: '',
  format: 'standard_csv',
})

onMounted(() => {
  loadHistory()
})

const handleFileChange = (file: UploadFile) => {
  fileList.value = [file]
}

const handleParse = async () => {
  if (fileList.value.length === 0) {
    ElMessage.warning('ファイルを選択してください')
    return
  }
  parsing.value = true
  try {
    // TODO: API呼び出し - ファイル解析
    await new Promise(r => setTimeout(r, 1000))
    parsedData.value = [
      { order_date: '2026-02-05', customer_order_no: 'PO-001', product_code: 'PRD-001', product_name: '製品A', quantity: 100, unit_price: 1500, delivery_date: '2026-02-15', valid: true, error_message: '' },
      { order_date: '2026-02-05', customer_order_no: 'PO-002', product_code: 'PRD-999', product_name: '製品X', quantity: 50, unit_price: 2000, delivery_date: '2026-02-20', valid: false, error_message: '品番が存在しません' },
    ]
    ElMessage.success('解析完了')
  } catch (e) {
    ElMessage.error('解析に失敗しました')
  } finally {
    parsing.value = false
  }
}

const handleImport = async () => {
  const validItems = parsedData.value.filter(d => d.valid)
  if (validItems.length === 0) {
    ElMessage.warning('取込可能なデータがありません')
    return
  }
  importing.value = true
  try {
    // TODO: API呼び出し - データ取込
    await new Promise(r => setTimeout(r, 1500))
    ElMessage.success(`${validItems.length}件の受注を取込みました`)
    parsedData.value = []
    fileList.value = []
    loadHistory()
  } catch (e) {
    ElMessage.error('取込に失敗しました')
  } finally {
    importing.value = false
  }
}

const loadHistory = async () => {
  // TODO: API呼び出し
  importHistory.value = []
}
</script>

<style scoped>
.edi-import { padding: 20px; }
.edi-import-embedded { padding: 0 4px 8px; }
.edi-import-embedded .page-header { display: none; }
.embedded-subtitle { margin: 0 0 16px 0; color: #909399; font-size: 13px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.upload-card { margin-bottom: 20px; }
.upload-area { width: 100%; }
.upload-icon { font-size: 48px; color: #c0c4cc; }
.upload-text { color: #606266; margin-top: 8px; }
.upload-tip { color: #909399; font-size: 12px; margin-top: 8px; }
.upload-options { margin-top: 20px; padding-top: 20px; border-top: 1px solid #ebeef5; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.history-card { margin-top: 20px; }
.success-count { color: #67c23a; }
.error-count { color: #f56c6c; font-weight: bold; }
</style>
