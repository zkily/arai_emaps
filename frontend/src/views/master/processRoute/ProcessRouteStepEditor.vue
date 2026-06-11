<template>
  <div class="route-step-editor">
    <!-- Compact Header -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <el-button type="default" icon="ArrowLeft" @click="router.back()" class="back-btn" size="small">戻る</el-button>
          <div class="title-info">
            <h1 class="main-title">🛠️ ルートステップ編集</h1>
            <span class="route-badge">{{ routeInfo?.route_name ?? '' }} ({{ routeInfo?.route_cd ?? '' }})</span>
          </div>
        </div>
        <div class="header-buttons">
          <el-button v-if="canCreate" type="primary" icon="Plus" @click="handleAddStep" class="add-btn" size="small">➕ ステップ追加</el-button>
          <el-button v-if="canEdit" type="success" :loading="saving" @click="handleSaveOrder" class="save-btn" :disabled="!stepList.length" size="small">💾 順序保存</el-button>
        </div>
      </div>
    </div>

    <!-- Data Table -->
    <div class="table-section" v-if="routeCd">
      <el-table :data="stepList" border stripe highlight-current-row class="modern-table"
        :header-cell-style="{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: '#fff', fontWeight: '600', fontSize: '12px', padding: '6px 10px' }"
        :cell-style="{ padding: '5px 8px', fontSize: '12px' }">
        <el-table-column label="順番" prop="step_no" width="70" align="center">
          <template #default="{ row }"><span class="step-number">{{ row.step_no }}</span></template>
        </el-table-column>
        <el-table-column label="工程" prop="process_name" min-width="100">
          <template #default="{ row }"><span class="process-name">{{ row.process_name }}</span></template>
        </el-table-column>
        <el-table-column label="歩留率(%)" prop="yield_percent" width="90" align="right">
          <template #default="{ row }"><span class="number-cell">{{ row.yield_percent }}</span></template>
        </el-table-column>
        <el-table-column label="サイクル(s)" prop="cycle_sec" width="100" align="right">
          <template #default="{ row }"><span class="number-cell">{{ row.cycle_sec }}</span></template>
        </el-table-column>
        <el-table-column label="備考" prop="remarks" min-width="120" show-overflow-tooltip />
        <el-table-column v-if="canEdit || canDelete" label="操作" width="150" align="center" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button v-if="canEdit" size="small" type="primary" plain @click="handleEdit(row)" class="action-btn">✏️ 編集</el-button>
              <el-button v-if="canDelete" size="small" type="danger" plain @click="handleDelete(row)" class="action-btn">🗑️</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Footer Info -->
    <div class="footer-section" v-if="stepList.length">
      <div class="result-info"><el-icon>📊</el-icon><span>ステップ数: <strong>{{ stepList.length }}</strong></span></div>
    </div>

    <RouteStepDialog v-model:visible="showStepDialog" :route-cd="routeCd" :mode="stepDialogMode" :initial-data="stepInitialData" @saved="fetchData" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { getRouteInfo, getRouteSteps, deleteRouteStep, updateStepOrder } from '@/api/master/processRouterMaster'
import type { RouteStepItem, RouteItem } from '@/types/master'
import RouteStepDialog from './ProcessRouteStepDialog.vue'
import { useMasterOperationPermission } from '@/composables/useMasterOperationPermission'
import { guardMasterOperation } from '@/utils/masterOperationGuard'

const { canCreate, canEdit, canDelete } = useMasterOperationPermission()

const route = useRoute()
const router = useRouter()
const routeCd = String(route.params.route_cd ?? '')
const routeInfo = ref<RouteItem | null>(null)
const stepList = ref<RouteStepItem[]>([])
const showStepDialog = ref(false)
const stepDialogMode = ref<'add' | 'edit'>('add')
const stepInitialData = ref<Partial<RouteStepItem> | undefined>(undefined)
const saving = ref(false)

const fetchData = async () => {
  if (!routeCd) { stepList.value = []; return }
  try { routeInfo.value = await getRouteInfo(routeCd); stepList.value = await getRouteSteps(routeCd) }
  catch (e: unknown) { ElMessage.error((e && typeof e === 'object' && 'message' in e) ? String((e as { message: string }).message) : 'データ取得失敗') }
}

const handleAddStep = () => {
  if (!guardMasterOperation(canCreate)) return
  stepDialogMode.value = 'add'; stepInitialData.value = undefined; showStepDialog.value = true
}
const handleEdit = (row: RouteStepItem) => {
  if (!guardMasterOperation(canEdit)) return
  stepDialogMode.value = 'edit'; stepInitialData.value = { ...row }; showStepDialog.value = true
}

const handleDelete = async (row: RouteStepItem) => {
  if (!guardMasterOperation(canDelete)) return
  try { await ElMessageBox.confirm('ステップを削除しますか？', '確認', { type: 'warning' }); if (row.id == null) return; await deleteRouteStep(routeCd, row.id); ElMessage.success('削除成功'); fetchData() }
  catch { /* cancelled */ }
}

const handleSaveOrder = async () => {
  if (!guardMasterOperation(canEdit)) return
  if (!stepList.value.length) return; saving.value = true
  try { await updateStepOrder(routeCd, stepList.value.map(s => ({ id: s.id!, step_no: s.step_no }))); ElMessage.success('順序を保存'); fetchData() }
  catch (e: unknown) { ElMessage.error((e && typeof e === 'object' && 'message' in e) ? String((e as { message: string }).message) : '保存失敗') }
  finally { saving.value = false }
}

onMounted(async () => { if (!routeCd) { ElMessage.warning('ルート未指定'); router.replace('/master/process-route'); return }; await fetchData() })
</script>

<style scoped>
.route-step-editor { padding: 12px 16px; background: linear-gradient(135deg, #f0f4f8 0%, #d9e2ec 100%); min-height: 100vh; }

.page-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; padding: 12px 18px; margin-bottom: 12px; box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3); }
.header-content { display: flex; align-items: center; justify-content: space-between; gap: 14px; flex-wrap: wrap; }
.title-section { display: flex; align-items: center; gap: 14px; }
.back-btn { border-radius: 8px; font-weight: 500; background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.3); color: #fff; }
.back-btn:hover { background: rgba(255,255,255,0.25); }
.title-info { display: flex; flex-direction: column; gap: 2px; }
.main-title { font-size: 1.25rem; font-weight: 700; margin: 0; color: #fff; }
.route-badge { font-size: 0.8rem; color: rgba(255,255,255,0.85); background: rgba(255,255,255,0.15); padding: 2px 10px; border-radius: 12px; }
.header-buttons { display: flex; gap: 8px; }
.add-btn { background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.3); border-radius: 8px; font-weight: 600; color: #fff; }
.add-btn:hover { background: rgba(255,255,255,0.25); }
.save-btn { border-radius: 8px; font-weight: 600; }

.table-section { background: #fff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.06); overflow: hidden; margin-bottom: 12px; }
.modern-table { width: 100%; }
.step-number { font-weight: 700; color: #667eea; background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%); padding: 2px 10px; border-radius: 10px; font-size: 12px; }
.process-name { font-weight: 500; color: #1e293b; }
.number-cell { font-family: 'Consolas', monospace; font-weight: 500; color: #374151; }
.action-buttons { display: flex; gap: 4px; justify-content: center; }
.action-btn { padding: 3px 8px; font-size: 11px; border-radius: 6px; }

.footer-section { background: #fff; border-radius: 10px; padding: 8px 16px; display: flex; align-items: center; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
.result-info { display: flex; align-items: center; gap: 6px; color: #64748b; font-size: 0.85rem; }
.result-info strong { color: #667eea; font-weight: 700; }

@media (max-width: 768px) {
  .route-step-editor { padding: 8px; }
  .page-header { padding: 10px 12px; }
  .header-content { flex-direction: column; align-items: stretch; gap: 10px; }
  .title-section { flex-direction: column; align-items: flex-start; gap: 8px; }
  .header-buttons { width: 100%; }
  .header-buttons > * { flex: 1; }
  .main-title { font-size: 1.1rem; }
  .action-buttons { flex-direction: column; gap: 3px; }
  .action-btn { width: 100%; }
}

:deep(.el-table) { --el-table-border-color: #e2e8f0; --el-table-row-hover-bg-color: #f0f4ff; }
:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) { background-color: #fafbfc; }
</style>
