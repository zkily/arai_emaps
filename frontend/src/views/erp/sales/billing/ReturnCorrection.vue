<template>
  <div class="return-correction">
    <div class="page-header">
      <h2>赤黒訂正処理</h2>
      <p class="subtitle">返品・値引き時の伝票修正（赤伝票/黒伝票）</p>
    </div>

    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="伝票番号">
          <el-input v-model="filters.slip_no" placeholder="伝票番号" clearable />
        </el-form-item>
        <el-form-item label="顧客">
          <el-select v-model="filters.customer_code" placeholder="顧客選択" clearable filterable>
            <el-option v-for="c in customers" :key="c.cd" :label="c.name" :value="c.cd" />
          </el-select>
        </el-form-item>
        <el-form-item label="種別">
          <el-select v-model="filters.type" placeholder="全て" clearable>
            <el-option label="返品（赤伝）" value="return" />
            <el-option label="値引き" value="discount" />
            <el-option label="数量訂正" value="qty_correction" />
            <el-option label="単価訂正" value="price_correction" />
          </el-select>
        </el-form-item>
        <el-form-item label="ステータス">
          <el-select v-model="filters.status" placeholder="全て" clearable>
            <el-option label="申請中" value="pending" />
            <el-option label="承認済" value="approved" />
            <el-option label="処理済" value="processed" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon> 検索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="toolbar">
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon> 新規訂正伝票作成
      </el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="correctionList" v-loading="loading" stripe border>
        <el-table-column prop="correction_no" label="訂正番号" width="130" fixed />
        <el-table-column prop="original_slip_no" label="元伝票番号" width="130" />
        <el-table-column prop="correction_type" label="訂正種別" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="row.correction_type === 'return' ? 'danger' : 'warning'" size="small">
              {{ { return: '返品（赤伝）', discount: '値引き', qty_correction: '数量訂正', price_correction: '単価訂正' }[row.correction_type] || row.correction_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="customer_name" label="顧客名" min-width="130" />
        <el-table-column prop="product_code" label="品番" width="120" />
        <el-table-column prop="original_amount" label="元金額" width="110" align="right">
          <template #default="{ row }">¥{{ row.original_amount?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="correction_amount" label="訂正金額" width="110" align="right">
          <template #default="{ row }">
            <span class="text-danger">¥{{ row.correction_amount?.toLocaleString() }}</span>
          </template>
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
            <el-button size="small" type="success" link @click="handleApprove(row)" v-if="row.status === 'pending'">承認</el-button>
            <el-button size="small" type="warning" link @click="handleProcess(row)" v-if="row.status === 'approved'">処理</el-button>
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
import { Search, Plus } from '@element-plus/icons-vue'

const loading = ref(false)
const correctionList = ref<any[]>([])
const customers = ref<{ cd: string; name: string }[]>([])
const filters = reactive({ slip_no: '', customer_code: '', type: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

onMounted(() => { loadData() })

const loadData = async () => {
  loading.value = true
  try { correctionList.value = [] } finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; loadData() }
const handleCreate = () => { ElMessage.info('新規訂正伝票作成画面を開きます') }
const handleView = (row: any) => { ElMessage.info(`訂正伝票 ${row.correction_no} の詳細`) }
const handleApprove = (row: any) => { ElMessage.success(`訂正伝票 ${row.correction_no} を承認しました`) }
const handleProcess = (row: any) => { ElMessage.success(`訂正伝票 ${row.correction_no} を処理しました`) }
const getStatusType = (s: string) => ({ pending: 'warning', approved: 'primary', processed: 'success' }[s] || 'info')
const getStatusLabel = (s: string) => ({ pending: '申請中', approved: '承認済', processed: '処理済' }[s] || s)
</script>

<style scoped>
.return-correction { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.filter-card { margin-bottom: 16px; }
.toolbar { margin-bottom: 16px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
.text-danger { color: #f56c6c; font-weight: bold; }
</style>
