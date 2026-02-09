<template>
  <div class="bom-explore">
    <div class="page-header">
      <h2>BOM展開</h2>
      <p class="subtitle">正展開（構成部品検索）・逆展開（使用先検索）</p>
    </div>

    <el-card class="search-card" shadow="never">
      <div class="explore-mode">
        <el-radio-group v-model="exploreMode" size="large">
          <el-radio-button value="forward">正展開（構成部品検索）</el-radio-button>
          <el-radio-button value="backward">逆展開（使用先検索）</el-radio-button>
        </el-radio-group>
      </div>
      <el-form :inline="true" :model="filters" class="mt-16">
        <el-form-item :label="exploreMode === 'forward' ? '親品番' : '子品番'">
          <el-input v-model="filters.product_code" placeholder="品番を入力" clearable style="width: 250px;" />
        </el-form-item>
        <el-form-item label="BOM版数">
          <el-input-number v-model="filters.bom_version" :min="1" />
        </el-form-item>
        <el-form-item label="基準日">
          <el-date-picker v-model="filters.effectiveDate" type="date" placeholder="基準日" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleExplore"><el-icon><Search /></el-icon> 展開実行</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" class="result-card">
      <div class="section-header">展開結果</div>
      <el-table :data="exploreResult" v-loading="loading" stripe border default-expand-all row-key="id" :tree-props="{ children: 'children' }">
        <el-table-column prop="level" label="レベル" width="80" align="center" />
        <el-table-column prop="product_code" label="品番" width="130" />
        <el-table-column prop="product_name" label="品名" min-width="200" show-overflow-tooltip />
        <el-table-column prop="quantity_per" label="員数" width="80" align="right" />
        <el-table-column prop="unit" label="単位" width="70" align="center" />
        <el-table-column prop="lead_time" label="L/T(日)" width="80" align="right" />
        <el-table-column prop="supply_type" label="調達区分" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.supply_type === 'make' ? 'primary' : 'success'" size="small">
              {{ row.supply_type === 'make' ? '製造' : '購入' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="bom_version" label="BOM版数" width="90" align="center" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'

const loading = ref(false)
const exploreMode = ref('forward')
const exploreResult = ref<any[]>([])
const filters = reactive({ product_code: '', bom_version: 1, effectiveDate: '' })

const handleExplore = async () => {
  if (!filters.product_code) { ElMessage.warning('品番を入力してください'); return }
  loading.value = true
  try {
    exploreResult.value = []
    ElMessage.info(`${filters.product_code} の${exploreMode.value === 'forward' ? '正展開' : '逆展開'}を実行します`)
  } finally { loading.value = false }
}
</script>

<style scoped>
.bom-explore { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.search-card { margin-bottom: 16px; }
.result-card { margin-top: 16px; }
.explore-mode { margin-bottom: 16px; }
.section-header { font-size: 16px; font-weight: 600; color: #303133; margin-bottom: 16px; }
.mt-16 { margin-top: 16px; }
</style>
