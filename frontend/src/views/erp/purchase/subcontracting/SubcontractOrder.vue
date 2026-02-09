<template>
  <div class="subcontract-order">
    <div class="page-header">
      <h2>外注加工指示</h2>
      <p class="subtitle">外注加工指示書発行・進捗管理・加工費単価管理</p>
    </div>

    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="指示番号">
          <el-input v-model="filters.order_no" placeholder="指示番号" clearable />
        </el-form-item>
        <el-form-item label="外注先">
          <el-select v-model="filters.supplier_code" placeholder="外注先選択" clearable filterable>
            <el-option v-for="s in suppliers" :key="s.cd" :label="s.name" :value="s.cd" />
          </el-select>
        </el-form-item>
        <el-form-item label="ステータス">
          <el-select v-model="filters.status" placeholder="全て" clearable>
            <el-option label="作成中" value="draft" />
            <el-option label="発行済" value="issued" />
            <el-option label="加工中" value="processing" />
            <el-option label="完了" value="completed" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon> 検索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="toolbar">
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon> 新規加工指示
      </el-button>
      <el-button @click="handlePriceMaster">
        <el-icon><Money /></el-icon> 加工費単価マスタ
      </el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="orderList" v-loading="loading" stripe border>
        <el-table-column prop="order_no" label="指示番号" width="130" fixed />
        <el-table-column prop="supplier_name" label="外注先" min-width="130" />
        <el-table-column prop="product_code" label="品番" width="120" />
        <el-table-column prop="product_name" label="品名" min-width="150" show-overflow-tooltip />
        <el-table-column prop="process_name" label="加工工程" width="120" />
        <el-table-column prop="quantity" label="数量" width="80" align="right" />
        <el-table-column prop="unit_price" label="加工費単価" width="110" align="right">
          <template #default="{ row }">¥{{ row.unit_price?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="supply_type" label="支給区分" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.supply_type === 'paid' ? 'warning' : 'info'" size="small">
              {{ row.supply_type === 'paid' ? '有償支給' : '無償支給' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="due_date" label="納期" width="110" />
        <el-table-column prop="status" label="ステータス" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleView(row)">詳細</el-button>
            <el-button size="small" type="success" link @click="handleIssue(row)" v-if="row.status === 'draft'">発行</el-button>
            <el-button size="small" type="warning" link @click="handlePrint(row)">指示書印刷</el-button>
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
import { Search, Plus, Money } from '@element-plus/icons-vue'

const loading = ref(false)
const orderList = ref<any[]>([])
const suppliers = ref<{ cd: string; name: string }[]>([])
const filters = reactive({ order_no: '', supplier_code: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

onMounted(() => { loadData() })

const loadData = async () => {
  loading.value = true
  try { orderList.value = [] } finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; loadData() }
const handleCreate = () => { ElMessage.info('新規外注加工指示画面を開きます') }
const handlePriceMaster = () => { ElMessage.info('加工費単価マスタ画面を開きます') }
const handleView = (row: any) => { ElMessage.info(`指示 ${row.order_no} の詳細`) }
const handleIssue = (row: any) => { ElMessage.success(`指示 ${row.order_no} を発行しました`) }
const handlePrint = (row: any) => { ElMessage.info(`指示書 ${row.order_no} を印刷します`) }
const getStatusType = (s: string) => ({ draft: 'info', issued: 'primary', processing: 'warning', completed: 'success' }[s] || 'info')
const getStatusLabel = (s: string) => ({ draft: '作成中', issued: '発行済', processing: '加工中', completed: '完了' }[s] || s)
</script>

<style scoped>
.subcontract-order { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.filter-card { margin-bottom: 16px; }
.toolbar { margin-bottom: 16px; display: flex; gap: 12px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
