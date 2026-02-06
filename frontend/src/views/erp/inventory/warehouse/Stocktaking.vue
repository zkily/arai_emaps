<template>
  <div class="stocktaking">
    <div class="page-header">
      <h2>棚卸管理</h2>
      <p class="subtitle">一斉棚卸/循環棚卸・棚卸票発行・実地棚卸入力・差異修正承認</p>
    </div>

    <!-- タブ切替 -->
    <el-tabs v-model="activeTab" type="border-card">
      <!-- 棚卸計画 -->
      <el-tab-pane label="棚卸計画" name="plan">
        <div class="toolbar">
          <el-button type="primary" @click="handleCreatePlan">
            <el-icon><Plus /></el-icon> 新規棚卸計画
          </el-button>
        </div>
        <el-table :data="planList" v-loading="loading" stripe border>
          <el-table-column prop="plan_no" label="計画番号" width="130" />
          <el-table-column prop="plan_date" label="棚卸日" width="110" />
          <el-table-column prop="type" label="種別" width="100">
            <template #default="{ row }">
              <el-tag :type="row.type === 'full' ? 'primary' : 'success'">
                {{ row.type === 'full' ? '一斉棚卸' : '循環棚卸' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="warehouse_name" label="対象倉庫" min-width="150" />
          <el-table-column prop="target_count" label="対象品目数" width="100" align="right" />
          <el-table-column prop="completed_count" label="完了数" width="80" align="right" />
          <el-table-column prop="status" label="ステータス" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button size="small" type="primary" link @click="handleViewPlan(row)">詳細</el-button>
              <el-button size="small" type="warning" link @click="handlePrintSheet(row)">棚卸票</el-button>
              <el-button size="small" type="success" link @click="handleStartCount(row)" v-if="row.status === 'planned'">開始</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 実地棚卸入力 -->
      <el-tab-pane label="実地棚卸入力" name="count">
        <el-card shadow="never" class="count-form-card">
          <el-form :inline="true" :model="countFilters">
            <el-form-item label="計画">
              <el-select v-model="countFilters.plan_no" placeholder="計画選択">
                <el-option v-for="p in activePlans" :key="p.plan_no" :label="p.plan_no" :value="p.plan_no" />
              </el-select>
            </el-form-item>
            <el-form-item label="ロケーション">
              <el-input v-model="countFilters.location" placeholder="ロケーション" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="loadCountItems">表示</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-table :data="countItems" stripe border>
          <el-table-column prop="location" label="ロケーション" width="120" fixed />
          <el-table-column prop="product_code" label="品番" width="120" />
          <el-table-column prop="product_name" label="品名" min-width="150" />
          <el-table-column prop="lot_no" label="ロット" width="120" />
          <el-table-column prop="book_quantity" label="帳簿数" width="90" align="right" />
          <el-table-column prop="actual_quantity" label="実数" width="100">
            <template #default="{ row }">
              <el-input-number v-model="row.actual_quantity" :min="0" size="small" controls-position="right" />
            </template>
          </el-table-column>
          <el-table-column prop="difference" label="差異" width="80" align="right">
            <template #default="{ row }">
              <span :class="getDiffClass(row)">{{ row.actual_quantity - row.book_quantity }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="remarks" label="備考" min-width="150">
            <template #default="{ row }">
              <el-input v-model="row.remarks" size="small" placeholder="備考" />
            </template>
          </el-table-column>
          <el-table-column label="確定" width="80" align="center">
            <template #default="{ row }">
              <el-checkbox v-model="row.confirmed" />
            </template>
          </el-table-column>
        </el-table>

        <div class="count-actions">
          <el-button type="primary" @click="handleSaveCount">一時保存</el-button>
          <el-button type="success" @click="handleConfirmCount">確定</el-button>
        </div>
      </el-tab-pane>

      <!-- 差異修正承認 -->
      <el-tab-pane label="差異修正承認" name="approval">
        <el-table :data="pendingApprovals" v-loading="loading" stripe border>
          <el-table-column prop="plan_no" label="計画番号" width="130" />
          <el-table-column prop="location" label="ロケーション" width="120" />
          <el-table-column prop="product_code" label="品番" width="120" />
          <el-table-column prop="product_name" label="品名" min-width="150" />
          <el-table-column prop="book_quantity" label="帳簿数" width="90" align="right" />
          <el-table-column prop="actual_quantity" label="実数" width="90" align="right" />
          <el-table-column prop="difference" label="差異" width="80" align="right">
            <template #default="{ row }">
              <span :class="getDiffClass(row)">{{ row.difference }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="difference_amount" label="差異金額" width="110" align="right">
            <template #default="{ row }">
              <span :class="row.difference_amount < 0 ? 'text-danger' : ''">
                ¥{{ row.difference_amount?.toLocaleString() }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="remarks" label="備考" min-width="150" show-overflow-tooltip />
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button size="small" type="success" @click="handleApprove(row)">承認</el-button>
              <el-button size="small" type="danger" @click="handleReject(row)">却下</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

const activeTab = ref('plan')
const loading = ref(false)
const planList = ref<any[]>([])
const activePlans = ref<any[]>([])
const countItems = ref<any[]>([])
const pendingApprovals = ref<any[]>([])

const countFilters = reactive({ plan_no: '', location: '' })

onMounted(() => { loadData() })

const loadData = async () => {
  // TODO: API呼び出し
}

const loadCountItems = () => {
  // TODO: API呼び出し
  ElMessage.info('棚卸対象を読み込みました')
}

const handleCreatePlan = () => { ElMessage.info('新規棚卸計画画面を開きます') }
const handleViewPlan = (row: any) => { ElMessage.info(`計画 ${row.plan_no} の詳細`) }
const handlePrintSheet = (row: any) => { ElMessage.info(`計画 ${row.plan_no} の棚卸票を発行します`) }
const handleStartCount = (row: any) => { ElMessage.success(`計画 ${row.plan_no} の棚卸を開始しました`) }
const handleSaveCount = () => { ElMessage.success('一時保存しました') }
const handleConfirmCount = () => { ElMessage.success('棚卸を確定しました') }
const handleApprove = async (row: any) => {
  await ElMessageBox.confirm('この差異を承認しますか？', '承認確認')
  ElMessage.success('承認しました')
}
const handleReject = async (row: any) => {
  await ElMessageBox.confirm('この差異を却下しますか？', '却下確認')
  ElMessage.warning('却下しました')
}

const getStatusType = (s: string) => ({ planned: 'info', in_progress: 'warning', completed: 'success', approved: 'primary' }[s] || 'info')
const getStatusLabel = (s: string) => ({ planned: '計画中', in_progress: '実施中', completed: '完了', approved: '承認済' }[s] || s)
const getDiffClass = (row: any) => {
  const diff = (row.actual_quantity ?? 0) - (row.book_quantity ?? 0)
  if (diff > 0) return 'text-success'
  if (diff < 0) return 'text-danger'
  return ''
}
</script>

<style scoped>
.stocktaking { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.toolbar { margin-bottom: 16px; }
.count-form-card { margin-bottom: 16px; }
.count-actions { margin-top: 16px; display: flex; gap: 12px; justify-content: flex-end; }
.text-success { color: #67c23a; font-weight: bold; }
.text-danger { color: #f56c6c; font-weight: bold; }
</style>
