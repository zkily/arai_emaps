<template>
  <div class="depreciation">
    <div class="page-header">
      <h2>減価償却計算</h2>
      <p class="subtitle">定額法/定率法自動計算・製造原価への連携</p>
    </div>

    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="対象年月">
          <el-date-picker v-model="filters.targetMonth" type="month" placeholder="対象月" value-format="YYYY-MM" />
        </el-form-item>
        <el-form-item label="償却方法">
          <el-select v-model="filters.method" placeholder="全て" clearable>
            <el-option label="定額法" value="straight_line" />
            <el-option label="定率法" value="declining_balance" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleCalculate"><el-icon><Cpu /></el-icon> 償却計算実行</el-button>
          <el-button @click="handleExport"><el-icon><Download /></el-icon> エクスポート</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table :data="depreciationList" v-loading="loading" stripe border show-summary>
        <el-table-column prop="asset_no" label="資産番号" width="120" fixed />
        <el-table-column prop="name" label="設備名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="acquisition_cost" label="取得価額" width="130" align="right">
          <template #default="{ row }">¥{{ row.acquisition_cost?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="accumulated" label="償却累計額" width="130" align="right">
          <template #default="{ row }">¥{{ row.accumulated?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="this_month" label="当月償却額" width="120" align="right">
          <template #default="{ row }">¥{{ row.this_month?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="book_value" label="帳簿価額" width="130" align="right">
          <template #default="{ row }"><strong>¥{{ row.book_value?.toLocaleString() }}</strong></template>
        </el-table-column>
        <el-table-column prop="method" label="償却方法" width="90" align="center">
          <template #default="{ row }">{{ row.method === 'straight_line' ? '定額法' : '定率法' }}</template>
        </el-table-column>
        <el-table-column prop="remaining_years" label="残存年数" width="90" align="right" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Cpu, Download } from '@element-plus/icons-vue'

const loading = ref(false)
const depreciationList = ref<any[]>([])
const filters = reactive({ targetMonth: '', method: '' })

const handleCalculate = () => { ElMessage.info('減価償却計算を実行します') }
const handleExport = () => { ElMessage.info('償却明細をエクスポートします') }
</script>

<style scoped>
.depreciation { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.filter-card { margin-bottom: 16px; }
</style>
