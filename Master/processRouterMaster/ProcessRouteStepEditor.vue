<template>
  <div class="route-step-editor">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <el-button type="default" icon="ArrowLeft" @click="router.back()" class="back-btn">戻る</el-button>
          <h1 class="main-title">
            🛠️ ルートステップ編集
            <span class="route-info">{{ routeInfo?.route_name ?? '' }}（{{ routeInfo?.route_cd ?? '' }}）</span>
          </h1>
        </div>
        <div class="header-buttons">
          <el-button type="primary" icon="Plus" @click="handleAddStep" class="add-btn">ステップ追加</el-button>
          <el-button type="success" icon="DocumentChecked" :loading="saving" @click="handleSaveOrder" class="save-btn">
            💾 順序保存
          </el-button>
        </div>
      </div>
    </div>

    <!-- 表格卡片 -->
    <el-card class="table-card">
      <el-table :data="stepList" border stripe highlight-current-row class="modern-table">
        <el-table-column label="🔢 順番" prop="step_no" width="80" align="center" />
        <el-table-column label="🏭 工程" prop="process_name" />
        <el-table-column label="📉 歩留（%）" prop="yield_percent" width="120" align="right"
          :formatter="formatYieldPercent" />
        <el-table-column label="⏱️ 標準サイクル(s)" prop="cycle_sec" width="160" align="right" />
        <el-table-column label="📝 補足説明" prop="remarks" />
        <el-table-column label="操作" width="180" align="center">
          <template #default="{ row }">
            <div class="action-buttons-table">
              <el-button size="small" type="primary" icon="Edit" @click="handleEdit(row)">編集</el-button>
              <el-button size="small" type="danger" icon="Delete" @click="handleDelete(row)">削除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 📦 ステップ编辑ダイアログ -->
    <RouteStepDialog v-model:visible="showStepDialog" :route-cd="routeCd" :mode="stepDialogMode"
      :initial-data="stepInitialData" @saved="fetchData" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { getRouteInfo, getRouteSteps, deleteRouteStep, updateStepOrder } from '@/api/master/processRouterMaster'
import type { RouteStepItem, RouteInfo } from '@/types/master'
import RouteStepDialog from './ProcessRouteStepDialog.vue'

const route = useRoute()
const router = useRouter()
const routeCd = String(route.params.route_cd ?? '')
const routeInfo = ref<RouteInfo | null>(null)
const stepList = ref<RouteStepItem[]>([])

const showStepDialog = ref(false)
const stepDialogMode = ref<'add' | 'edit'>('add')
const stepInitialData = ref<Partial<RouteStepItem> | undefined>(undefined)

// ⭐⭐ 追加：歩留フォーマット関数 ⭐⭐
const formatYieldPercent = (row: RouteStepItem) => {
  if (row.yield_percent == null) return ''
  return Number(row.yield_percent).toFixed(2)
}

const fetchData = async () => {
  try {
    routeInfo.value = await getRouteInfo(routeCd)
    stepList.value = await getRouteSteps(routeCd)
  } catch (err: unknown) {
    let msg = 'データ取得失敗'
    if (typeof err === 'object' && err !== null) {
      const e = err as { message?: string }
      msg = e.message || msg
    }
    console.error('RouteStepEditor fetchData error:', err)
    ElMessage.error(msg)
  }
}

const handleAddStep = () => {
  stepDialogMode.value = 'add'
  stepInitialData.value = undefined
  showStepDialog.value = true
}

const handleEdit = (row: RouteStepItem) => {
  stepDialogMode.value = 'edit'
  stepInitialData.value = { ...row }
  showStepDialog.value = true
}

const handleDelete = async (row: RouteStepItem) => {
  try {
    await ElMessageBox.confirm('このステップを削除してもよろしいですか？', '⚠️ 確認', { type: 'warning' })
    await deleteRouteStep(routeCd, row.id!)
    ElMessage.success('✅ 削除成功')
    fetchData()
  } catch {
    // キャンセル等は無視
  }
}

const saving = ref(false)

const handleSaveOrder = async () => {
  saving.value = true
  try {
    const orderData = stepList.value.map(s => ({ id: s.id, step_no: s.step_no }))
    await updateStepOrder(routeCd, orderData)
    ElMessage.success('順序を保存しました')
    fetchData()
  } catch (err: unknown) {
    let msg = '保存失敗'
    if (typeof err === 'object' && err !== null) {
      const e = err as { message?: string }
      msg = e.message || msg
    }
    ElMessage.error(msg)
  } finally {
    saving.value = false
  }
}

onMounted(fetchData)
</script>

<style scoped>
.route-step-editor {
  padding: 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: 100vh;
}

.page-header {
  background: white;
  border-radius: 20px;
  padding: 32px;
  margin-bottom: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

.title-section {
  display: flex;
  align-items: center;
  gap: 18px;
}

.back-btn {
  border-radius: 8px;
  font-weight: 500;
}

.main-title {
  font-size: 2rem;
  font-weight: 700;
  margin: 0;
  color: #2c3e50;
  display: flex;
  align-items: center;
  gap: 12px;
}

.route-info {
  font-size: 1.1rem;
  color: #2980b9;
  margin-left: 10px;
  font-weight: 500;
}

.header-buttons {
  display: flex;
  gap: 12px;
}

.add-btn {
  background: linear-gradient(135deg, #27ae60 0%, #2980b9 100%);
  border: none;
  border-radius: 12px;
  padding: 10px 20px;
  font-weight: 600;
  box-shadow: 0 4px 15px rgba(41, 128, 185, 0.18);
  transition: all 0.3s;
  color: #fff;
}

.add-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(41, 128, 185, 0.23);
}

.save-btn {
  border-radius: 12px;
  font-weight: 600;
}

.table-card {
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: none;
  margin-bottom: 16px;
}

.modern-table {
  border-radius: 12px;
  overflow: hidden;
}

.action-buttons-table {
  display: flex;
  gap: 8px;
  justify-content: center;
}

@media (max-width:1200px) {
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 20px;
  }

  .header-buttons {
    align-self: stretch;
    justify-content: flex-end;
  }
}

@media (max-width:768px) {
  .route-step-editor {
    padding: 12px;
  }

  .page-header {
    padding: 18px 10px;
  }

  .main-title {
    font-size: 1.5rem;
  }

  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .header-buttons {
    width: 100%;
    justify-content: stretch;
    gap: 10px;
  }

  .add-btn,
  .save-btn {
    width: 100%;
    min-width: 0;
    padding: 10px 0;
  }
}

@media (max-width:480px) {
  .main-title {
    font-size: 1.2rem;
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}

@media (prefers-color-scheme: dark) {
  .route-step-editor {
    background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
  }

  .page-header,
  .table-card {
    background: rgba(45, 55, 72, 0.88);
    color: #e2e8f0;
    border: 1px solid rgba(255, 255, 255, 0.12);
  }

  .main-title {
    color: #e2e8f0;
  }
}

.table-card,
.page-header {
  animation: fadeInUp 0.6s;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

:deep(.el-table th) {
  background-color: #f8fafc;
  color: #2d3748;
  font-weight: 600;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background-color: #f7fafc;
}

:deep(.el-tag) {
  border-radius: 12px;
  font-weight: 500;
}
</style>
