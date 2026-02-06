<template>
  <div class="returns-list">
    <div class="page-header">
      <h2>返品管理 (RMA)</h2>
      <p class="subtitle">返品受付番号発行・受入検査指示・代替品出荷/返金処理</p>
    </div>

    <!-- 検索フィルター -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="RMA番号">
          <el-input v-model="filters.rma_no" placeholder="RMA番号" clearable />
        </el-form-item>
        <el-form-item label="顧客">
          <el-select v-model="filters.customer_code" placeholder="全て" clearable filterable>
            <el-option v-for="c in customers" :key="c.cd" :label="c.name" :value="c.cd" />
          </el-select>
        </el-form-item>
        <el-form-item label="ステータス">
          <el-select v-model="filters.status" placeholder="全て" clearable>
            <el-option label="受付待ち" value="pending" />
            <el-option label="検査中" value="inspecting" />
            <el-option label="処理待ち" value="processing" />
            <el-option label="完了" value="completed" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon> 検索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- ツールバー -->
    <div class="toolbar">
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon> 新規返品受付
      </el-button>
    </div>

    <!-- 返品一覧 -->
    <el-card shadow="never">
      <el-table :data="returnsList" v-loading="loading" stripe border>
        <el-table-column prop="rma_no" label="RMA番号" width="130" fixed />
        <el-table-column prop="request_date" label="受付日" width="110" />
        <el-table-column prop="order_no" label="元受注番号" width="130" />
        <el-table-column prop="customer_name" label="顧客名" min-width="150" />
        <el-table-column prop="product_code" label="品番" width="120" />
        <el-table-column prop="product_name" label="品名" min-width="150" show-overflow-tooltip />
        <el-table-column prop="quantity" label="返品数" width="80" align="right" />
        <el-table-column prop="reason" label="返品理由" width="120" />
        <el-table-column prop="status" label="ステータス" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="resolution" label="対応内容" width="100" align="center">
          <template #default="{ row }">
            <span v-if="row.resolution === 'replacement'">代替品出荷</span>
            <span v-else-if="row.resolution === 'refund'">返金</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleView(row)">詳細</el-button>
            <el-button size="small" type="warning" link @click="handleInspection(row)" v-if="row.status === 'pending'">検査指示</el-button>
            <el-button size="small" type="success" link @click="handleProcess(row)" v-if="row.status === 'processing'">処理</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize"
          :total="pagination.total" :page-sizes="[20, 50, 100]" layout="total, sizes, prev, pager, next" background />
      </div>
    </el-card>

    <!-- 新規返品ダイアログ -->
    <el-dialog v-model="createDialogVisible" title="新規返品受付" width="600px">
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="元受注番号" required>
          <el-input v-model="createForm.order_no" placeholder="受注番号を入力" />
        </el-form-item>
        <el-form-item label="顧客">
          <el-input v-model="createForm.customer_name" disabled />
        </el-form-item>
        <el-form-item label="品番">
          <el-select v-model="createForm.product_code" placeholder="品番選択" filterable>
            <el-option v-for="p in products" :key="p.cd" :label="`${p.cd} - ${p.name}`" :value="p.cd" />
          </el-select>
        </el-form-item>
        <el-form-item label="返品数量" required>
          <el-input-number v-model="createForm.quantity" :min="1" />
        </el-form-item>
        <el-form-item label="返品理由" required>
          <el-select v-model="createForm.reason" placeholder="理由選択">
            <el-option label="不良品" value="defective" />
            <el-option label="誤配送" value="wrong_delivery" />
            <el-option label="数量相違" value="quantity_mismatch" />
            <el-option label="その他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="備考">
          <el-input v-model="createForm.remarks" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">キャンセル</el-button>
        <el-button type="primary" @click="submitCreate">登録</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Plus } from '@element-plus/icons-vue'

const loading = ref(false)
const returnsList = ref<any[]>([])
const customers = ref<{ cd: string; name: string }[]>([])
const products = ref<{ cd: string; name: string }[]>([])
const createDialogVisible = ref(false)

const filters = reactive({ rma_no: '', customer_code: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const createForm = reactive({ order_no: '', customer_name: '', product_code: '', quantity: 1, reason: '', remarks: '' })

onMounted(() => { loadData() })

const loadData = async () => {
  loading.value = true
  try { returnsList.value = [] } finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; loadData() }
const handleCreate = () => { Object.assign(createForm, { order_no: '', customer_name: '', product_code: '', quantity: 1, reason: '', remarks: '' }); createDialogVisible.value = true }
const submitCreate = () => { ElMessage.success('返品受付を登録しました'); createDialogVisible.value = false; loadData() }
const handleView = (row: any) => { ElMessage.info(`RMA ${row.rma_no} の詳細`) }
const handleInspection = (row: any) => { ElMessage.success(`RMA ${row.rma_no} に検査指示を出しました`) }
const handleProcess = (row: any) => { ElMessage.info(`RMA ${row.rma_no} の処理画面を開きます`) }

const getStatusType = (s: string) => ({ pending: 'warning', inspecting: 'info', processing: 'primary', completed: 'success' }[s] || 'info')
const getStatusLabel = (s: string) => ({ pending: '受付待ち', inspecting: '検査中', processing: '処理待ち', completed: '完了' }[s] || s)
</script>

<style scoped>
.returns-list { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.filter-card { margin-bottom: 16px; }
.toolbar { margin-bottom: 16px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
