<template>
  <div class="lot-traceability">
    <div class="page-header">
      <h2>ロット・トレーサビリティ</h2>
      <p class="subtitle">正展開（製品→材料）・逆展開（材料→製品）追跡</p>
    </div>

    <el-card class="search-card" shadow="never">
      <div class="trace-mode">
        <el-radio-group v-model="traceMode" size="large">
          <el-radio-button value="forward">正展開（製品→材料）</el-radio-button>
          <el-radio-button value="backward">逆展開（材料→製品）</el-radio-button>
        </el-radio-group>
      </div>
      <el-form :inline="true" :model="filters" class="mt-16">
        <el-form-item :label="traceMode === 'forward' ? '製品ロット番号' : '材料ロット番号'">
          <el-input v-model="filters.lot_no" placeholder="ロット番号を入力" clearable style="width: 250px;" />
        </el-form-item>
        <el-form-item label="品番">
          <el-input v-model="filters.product_code" placeholder="品番" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleTrace"><el-icon><Search /></el-icon> 追跡実行</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 追跡結果 -->
    <el-card shadow="never" class="result-card" v-if="traceResult.length > 0">
      <div class="section-header">追跡結果</div>
      <el-table :data="traceResult" v-loading="loading" stripe border default-expand-all row-key="id">
        <el-table-column prop="lot_no" label="ロット番号" width="150" />
        <el-table-column prop="product_code" label="品番" width="120" />
        <el-table-column prop="product_name" label="品名" min-width="150" show-overflow-tooltip />
        <el-table-column prop="quantity" label="数量" width="80" align="right" />
        <el-table-column prop="warehouse_name" label="倉庫" width="100" />
        <el-table-column prop="process_name" label="工程" width="100" />
        <el-table-column prop="direction" label="区分" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.direction === 'in' ? 'success' : 'warning'" size="small">
              {{ row.direction === 'in' ? '入庫' : '出庫' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="transaction_date" label="日時" width="150" />
        <el-table-column prop="supplier_name" label="仕入先/出荷先" min-width="120" />
      </el-table>
    </el-card>

    <!-- 空状態 -->
    <el-card shadow="never" class="result-card" v-else>
      <el-empty description="ロット番号を入力して追跡を実行してください" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'

const loading = ref(false)
const traceMode = ref('forward')
const traceResult = ref<any[]>([])
const filters = reactive({ lot_no: '', product_code: '' })

const handleTrace = async () => {
  if (!filters.lot_no) { ElMessage.warning('ロット番号を入力してください'); return }
  loading.value = true
  try {
    // TODO: API call
    traceResult.value = []
    ElMessage.info(`ロット ${filters.lot_no} の${traceMode.value === 'forward' ? '正展開' : '逆展開'}を実行します`)
  } finally { loading.value = false }
}
</script>

<style scoped>
.lot-traceability { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.search-card { margin-bottom: 16px; }
.result-card { margin-top: 16px; }
.trace-mode { margin-bottom: 16px; }
.section-header { font-size: 16px; font-weight: 600; color: #303133; margin-bottom: 16px; }
.mt-16 { margin-top: 16px; }
</style>
