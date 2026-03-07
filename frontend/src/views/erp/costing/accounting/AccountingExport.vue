<template>
  <div class="accounting-export">
    <div class="page-header">
      <h2>会計ソフト出力</h2>
      <p class="subtitle">弥生会計・勘定奉行・freee等への仕訳データ出力</p>
    </div>

    <el-card class="filter-card" shadow="never">
      <el-form :model="exportConfig" label-width="140px">
        <el-form-item label="対象年月">
          <el-date-picker v-model="exportConfig.targetMonth" type="month" placeholder="対象月" value-format="YYYY-MM" />
        </el-form-item>
        <el-form-item label="出力先会計ソフト">
          <el-select v-model="exportConfig.software" placeholder="選択してください">
            <el-option label="弥生会計" value="yayoi" />
            <el-option label="勘定奉行" value="bugyo" />
            <el-option label="freee" value="freee" />
            <el-option label="マネーフォワード" value="moneyforward" />
            <el-option label="汎用CSV" value="generic_csv" />
          </el-select>
        </el-form-item>
        <el-form-item label="仕訳種別">
          <el-checkbox-group v-model="exportConfig.types">
            <el-checkbox value="sales">売上</el-checkbox>
            <el-checkbox value="purchase">仕入</el-checkbox>
            <el-checkbox value="transfer">在庫移動</el-checkbox>
            <el-checkbox value="manufacturing">製造振替</el-checkbox>
            <el-checkbox value="depreciation">減価償却</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="出力範囲">
          <el-radio-group v-model="exportConfig.range">
            <el-radio value="all">全仕訳</el-radio>
            <el-radio value="unposted">未転記のみ</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="action-area">
      <el-card shadow="never">
        <div class="preview-header">
          <span>出力プレビュー</span>
          <el-tag>{{ previewCount }}件</el-tag>
        </div>
        <el-table :data="previewData" v-loading="loading" stripe border max-height="400">
          <el-table-column prop="journal_date" label="仕訳日" width="110" />
          <el-table-column prop="debit_account" label="借方勘定" width="130" />
          <el-table-column prop="credit_account" label="貸方勘定" width="130" />
          <el-table-column prop="amount" label="金額" width="130" align="right">
            <template #default="{ row }">¥{{ row.amount?.toLocaleString() }}</template>
          </el-table-column>
          <el-table-column prop="description" label="摘要" min-width="200" show-overflow-tooltip />
        </el-table>
      </el-card>

      <div class="button-group">
        <el-button type="primary" size="large" @click="handlePreview">
          <el-icon><View /></el-icon> プレビュー
        </el-button>
        <el-button type="success" size="large" @click="handleExport" :disabled="previewData.length === 0">
          <el-icon><Download /></el-icon> ファイル出力
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { View, Download } from '@element-plus/icons-vue'

const loading = ref(false)
const previewData = ref<any[]>([])
const previewCount = ref(0)

const exportConfig = reactive({
  targetMonth: '',
  software: 'generic_csv',
  types: ['sales', 'purchase'],
  range: 'all',
})

const handlePreview = () => {
  if (!exportConfig.targetMonth) { ElMessage.warning('対象年月を選択してください'); return }
  ElMessage.info('プレビューデータを取得します')
  previewData.value = []
  previewCount.value = 0
}

const handleExport = () => {
  ElMessage.success(`${exportConfig.software} フォーマットでファイルを出力します`)
}
</script>

<style scoped>
.accounting-export { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.filter-card { margin-bottom: 16px; }
.action-area { margin-top: 16px; }
.preview-header { display: flex; align-items: center; gap: 8px; margin-bottom: 16px; font-size: 16px; font-weight: 600; color: #303133; }
.button-group { display: flex; gap: 16px; justify-content: center; margin-top: 24px; }
</style>
