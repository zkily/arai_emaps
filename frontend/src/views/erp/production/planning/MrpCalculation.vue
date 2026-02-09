<template>
  <div class="mrp-calculation">
    <div class="page-header">
      <h2>MRP（所要量計算）</h2>
      <p class="subtitle">所要量展開・発注推奨・手配指示自動生成</p>
    </div>

    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="計算基準日">
          <el-date-picker v-model="filters.baseDate" type="date" placeholder="基準日" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="対象期間">
          <el-select v-model="filters.horizon" placeholder="期間選択">
            <el-option label="1ヶ月" value="1m" />
            <el-option label="3ヶ月" value="3m" />
            <el-option label="6ヶ月" value="6m" />
          </el-select>
        </el-form-item>
        <el-form-item label="品番">
          <el-input v-model="filters.product_code" placeholder="品番（空欄で全品）" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleRunMrp"><el-icon><Cpu /></el-icon> MRP実行</el-button>
          <el-button @click="handleSimulation"><el-icon><DataAnalysis /></el-icon> シミュレーション</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table :data="mrpResult" v-loading="loading" stripe border>
        <el-table-column prop="product_code" label="品番" width="120" fixed />
        <el-table-column prop="product_name" label="品名" min-width="150" show-overflow-tooltip />
        <el-table-column prop="gross_requirement" label="総所要量" width="100" align="right" />
        <el-table-column prop="scheduled_receipt" label="入庫予定" width="100" align="right" />
        <el-table-column prop="on_hand" label="手持在庫" width="100" align="right" />
        <el-table-column prop="net_requirement" label="正味所要量" width="110" align="right">
          <template #default="{ row }">
            <span :class="row.net_requirement > 0 ? 'text-danger' : ''">{{ row.net_requirement }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="planned_order" label="計画オーダー" width="110" align="right" />
        <el-table-column prop="action" label="推奨アクション" width="130" align="center">
          <template #default="{ row }">
            <el-tag :type="row.action === 'purchase' ? 'primary' : row.action === 'produce' ? 'success' : 'info'" size="small">
              {{ { purchase: '発注推奨', produce: '製造推奨', none: '不要' }[row.action] || row.action }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="required_date" label="必要日" width="110" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleDetail(row)">詳細</el-button>
            <el-button size="small" type="success" link @click="handleCreateOrder(row)" v-if="row.action !== 'none'">手配</el-button>
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
import { Cpu, DataAnalysis } from '@element-plus/icons-vue'

const loading = ref(false)
const mrpResult = ref<any[]>([])
const filters = reactive({ baseDate: '', horizon: '1m', product_code: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

onMounted(() => { /* 初期表示は空 */ })

const handleRunMrp = () => { ElMessage.info('MRP計算を実行します...') }
const handleSimulation = () => { ElMessage.info('シミュレーションモードで実行します') }
const handleDetail = (row: any) => { ElMessage.info(`${row.product_code} のMRP詳細`) }
const handleCreateOrder = (row: any) => { ElMessage.success(`${row.product_code} の手配指示を作成しました`) }
</script>

<style scoped>
.mrp-calculation { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.filter-card { margin-bottom: 16px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
.text-danger { color: #f56c6c; font-weight: bold; }
</style>
