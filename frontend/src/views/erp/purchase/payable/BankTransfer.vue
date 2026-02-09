<template>
  <div class="bank-transfer">
    <div class="page-header">
      <h2>FBデータ作成</h2>
      <p class="subtitle">銀行振込データ(FB)作成・全銀フォーマット出力</p>
    </div>

    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="振込日">
          <el-date-picker v-model="filters.transferDate" type="date" placeholder="振込日" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="振込元口座">
          <el-select v-model="filters.account" placeholder="口座選択" clearable>
            <el-option label="三菱UFJ 普通 1234567" value="acc1" />
            <el-option label="みずほ 普通 7654321" value="acc2" />
          </el-select>
        </el-form-item>
        <el-form-item label="ステータス">
          <el-select v-model="filters.status" placeholder="全て" clearable>
            <el-option label="作成中" value="draft" />
            <el-option label="確定済" value="confirmed" />
            <el-option label="送信済" value="sent" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon> 検索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="toolbar">
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon> 新規FBデータ作成
      </el-button>
      <el-button type="success" @click="handleExportFb">
        <el-icon><Download /></el-icon> 全銀フォーマット出力
      </el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="transferList" v-loading="loading" stripe border>
        <el-table-column prop="batch_no" label="バッチ番号" width="130" fixed />
        <el-table-column prop="transfer_date" label="振込日" width="110" />
        <el-table-column prop="account_name" label="振込元口座" min-width="150" />
        <el-table-column prop="items_count" label="件数" width="70" align="right" />
        <el-table-column prop="total_amount" label="合計金額" width="140" align="right">
          <template #default="{ row }"><strong>¥{{ row.total_amount?.toLocaleString() }}</strong></template>
        </el-table-column>
        <el-table-column prop="status" label="ステータス" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="作成日" width="110" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleView(row)">詳細</el-button>
            <el-button size="small" type="success" link @click="handleConfirm(row)" v-if="row.status === 'draft'">確定</el-button>
            <el-button size="small" type="warning" link @click="handleDownload(row)" v-if="row.status === 'confirmed'">DL</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrapper">
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize"
          :total="pagination.total" :page-sizes="[20, 50, 100]" layout="total, sizes, prev, pager, next" background />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Plus, Download } from '@element-plus/icons-vue'

const loading = ref(false)
const transferList = ref<any[]>([])
const filters = reactive({ transferDate: '', account: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

onMounted(() => { loadData() })

const loadData = async () => {
  loading.value = true
  try { transferList.value = [] } finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; loadData() }
const handleCreate = () => { ElMessage.info('新規FBデータ作成画面を開きます') }
const handleExportFb = () => { ElMessage.info('全銀フォーマットを出力します') }
const handleView = (row: any) => { ElMessage.info(`バッチ ${row.batch_no} の詳細`) }
const handleConfirm = (row: any) => { ElMessage.success(`バッチ ${row.batch_no} を確定しました`) }
const handleDownload = (row: any) => { ElMessage.info(`バッチ ${row.batch_no} のFBデータをダウンロードします`) }
const getStatusType = (s: string) => ({ draft: 'info', confirmed: 'primary', sent: 'success' }[s] || 'info')
const getStatusLabel = (s: string) => ({ draft: '作成中', confirmed: '確定済', sent: '送信済' }[s] || s)
</script>

<style scoped>
.bank-transfer { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.filter-card { margin-bottom: 16px; }
.toolbar { margin-bottom: 16px; display: flex; gap: 12px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
