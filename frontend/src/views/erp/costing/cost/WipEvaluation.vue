<template>
  <div class="wip-evaluation">
    <div class="page-header">
      <h2>仕掛品(WIP)評価</h2>
      <p class="subtitle">月末時点の工程内在庫の評価額算出</p>
    </div>

    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="評価基準日">
          <el-date-picker v-model="filters.evaluationDate" type="date" placeholder="基準日" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="工程">
          <el-select v-model="filters.process_code" placeholder="全工程" clearable>
            <el-option v-for="p in processes" :key="p.cd" :label="p.name" :value="p.cd" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleEvaluate"><el-icon><DataAnalysis /></el-icon> WIP評価実行</el-button>
          <el-button @click="handleExport"><el-icon><Download /></el-icon> エクスポート</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table :data="wipList" v-loading="loading" stripe border show-summary>
        <el-table-column prop="order_no" label="生産オーダー" width="130" fixed />
        <el-table-column prop="product_code" label="品番" width="120" />
        <el-table-column prop="product_name" label="品名" min-width="150" show-overflow-tooltip />
        <el-table-column prop="process_name" label="現工程" width="100" />
        <el-table-column prop="progress" label="進捗率" width="100">
          <template #default="{ row }">
            <el-progress :percentage="row.progress" :stroke-width="8" />
          </template>
        </el-table-column>
        <el-table-column prop="wip_qty" label="仕掛数量" width="90" align="right" />
        <el-table-column prop="material_value" label="材料費" width="120" align="right">
          <template #default="{ row }">¥{{ row.material_value?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="labor_value" label="加工費" width="120" align="right">
          <template #default="{ row }">¥{{ row.labor_value?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="total_value" label="WIP評価額" width="130" align="right">
          <template #default="{ row }"><strong>¥{{ row.total_value?.toLocaleString() }}</strong></template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleView(row)">詳細</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { DataAnalysis, Download } from '@element-plus/icons-vue'

const loading = ref(false)
const wipList = ref<any[]>([])
const processes = ref<{ cd: string; name: string }[]>([])
const filters = reactive({ evaluationDate: '', process_code: '' })

const handleEvaluate = () => { ElMessage.info('WIP評価計算を実行します') }
const handleExport = () => { ElMessage.info('WIP評価結果をエクスポートします') }
const handleView = (row: any) => { ElMessage.info(`${row.order_no} のWIP詳細`) }
</script>

<style scoped>
.wip-evaluation { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.filter-card { margin-bottom: 16px; }
</style>
