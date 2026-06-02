<template>
  <div class="allocation-calc">
    <div class="page-header">
      <h2>配賦計算</h2>
      <p class="subtitle">労務費・製造経費・光熱費の製品別配賦</p>
    </div>

    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="対象年月">
          <el-date-picker v-model="filters.targetMonth" type="month" placeholder="対象月" value-format="YYYY-MM" />
        </el-form-item>
        <el-form-item label="配賦基準">
          <el-select v-model="filters.basis" placeholder="全て" clearable>
            <el-option label="直接作業時間" value="direct_hours" />
            <el-option label="機械稼働時間" value="machine_hours" />
            <el-option label="生産数量" value="production_qty" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleCalculate"><el-icon><Cpu /></el-icon> 配賦計算実行</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table :data="allocationList" v-loading="loading" stripe border show-summary>
        <el-table-column prop="product_code" label="品番" width="120" fixed />
        <el-table-column prop="product_name" label="品名" min-width="150" show-overflow-tooltip />
        <el-table-column prop="direct_material" label="直接材料費" width="120" align="right">
          <template #default="{ row }">¥{{ row.direct_material?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="direct_labor" label="直接労務費" width="120" align="right">
          <template #default="{ row }">¥{{ row.direct_labor?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="overhead" label="製造間接費" width="120" align="right">
          <template #default="{ row }">¥{{ row.overhead?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="utility" label="光熱費配賦" width="110" align="right">
          <template #default="{ row }">¥{{ row.utility?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="total_cost" label="合計製造原価" width="130" align="right">
          <template #default="{ row }"><strong>¥{{ row.total_cost?.toLocaleString() }}</strong></template>
        </el-table-column>
        <el-table-column prop="allocation_rate" label="配賦率" width="90" align="right">
          <template #default="{ row }">{{ row.allocation_rate?.toFixed(2) }}%</template>
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
import { Cpu } from '@element-plus/icons-vue'

const loading = ref(false)
const allocationList = ref<any[]>([])
const filters = reactive({ targetMonth: '', basis: 'direct_hours' })

const handleCalculate = () => { ElMessage.info('配賦計算を実行します') }
const handleView = (row: any) => { ElMessage.info(`${row.product_code} の配賦詳細`) }
</script>

<style scoped>
.allocation-calc { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.filter-card { margin-bottom: 16px; }
</style>
