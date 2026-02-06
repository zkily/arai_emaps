<template>
  <div class="workflow-setting">
    <div class="page-header">
      <h2>ワークフロー設定</h2>
      <p class="subtitle">承認ルート定義（金額別、部門別）、代理承認設定</p>
    </div>

    <el-tabs v-model="activeTab" type="border-card">
      <!-- 承認ルート管理 -->
      <el-tab-pane label="承認ルート" name="routes">
        <div class="tab-actions">
          <el-button type="primary" :icon="Plus" @click="handleAddRoute">ルート追加</el-button>
        </div>
        <el-table :data="approvalRoutes" stripe border>
          <el-table-column prop="name" label="ルート名" min-width="150" />
          <el-table-column prop="type" label="種類" width="100">
            <template #default="{ row }">
              <el-tag :type="getRouteTypeTag(row.type)">{{ row.type }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="condition" label="適用条件" min-width="200" />
          <el-table-column label="承認ステップ" min-width="300">
            <template #default="{ row }">
              <div class="step-flow">
                <span v-for="(step, idx) in row.steps" :key="idx" class="step-item">
                  <el-tag size="small">{{ step }}</el-tag>
                  <el-icon v-if="Number(idx) < row.steps.length - 1" class="step-arrow"><ArrowRight /></el-icon>
                </span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="ステータス" width="100">
            <template #default="{ row }">
              <el-switch v-model="row.status" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button size="small" type="primary" link @click="handleEditRoute(row)">編集</el-button>
              <el-button size="small" type="danger" link @click="handleDeleteRoute(row)">削除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 代理承認設定 -->
      <el-tab-pane label="代理承認" name="delegation">
        <div class="tab-actions">
          <el-button type="primary" :icon="Plus" @click="handleAddDelegation">代理設定追加</el-button>
        </div>
        <el-table :data="delegations" stripe border>
          <el-table-column prop="delegator" label="委任者" min-width="120" />
          <el-table-column prop="delegate" label="代理者" min-width="120" />
          <el-table-column prop="start_date" label="開始日" width="120" />
          <el-table-column prop="end_date" label="終了日" width="120" />
          <el-table-column prop="scope" label="範囲" min-width="150" />
          <el-table-column prop="reason" label="理由" min-width="150" />
          <el-table-column prop="status" label="ステータス" width="100">
            <template #default="{ row }">
              <el-tag :type="getDelegationStatusType(row.status)">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button size="small" type="primary" link @click="handleEditDelegation(row)">編集</el-button>
              <el-button size="small" type="danger" link @click="handleDeleteDelegation(row)">削除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- ワークフロー定義 -->
      <el-tab-pane label="ワークフロー定義" name="definitions">
        <div class="tab-actions">
          <el-button type="primary" :icon="Plus" @click="handleAddWorkflow">ワークフロー追加</el-button>
        </div>
        <el-table :data="workflowDefinitions" stripe border>
          <el-table-column prop="code" label="コード" width="120" />
          <el-table-column prop="name" label="ワークフロー名" min-width="150" />
          <el-table-column prop="document_type" label="対象伝票" width="120" />
          <el-table-column prop="approval_route" label="承認ルート" min-width="150" />
          <el-table-column prop="timeout_days" label="期限（日）" width="100" align="center" />
          <el-table-column prop="escalation" label="エスカレーション" width="130">
            <template #default="{ row }">
              <el-tag v-if="row.escalation" type="warning" size="small">有効</el-tag>
              <el-tag v-else type="info" size="small">無効</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button size="small" type="primary" link @click="handleEditWorkflow(row)">編集</el-button>
              <el-button size="small" type="danger" link @click="handleDeleteWorkflow(row)">削除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, ArrowRight } from '@element-plus/icons-vue'

const activeTab = ref('routes')

const approvalRoutes = ref([
  { id: 1, name: '通常購買承認', type: '金額', condition: '10万円未満', steps: ['申請者', '課長', '部長'], status: true },
  { id: 2, name: '高額購買承認', type: '金額', condition: '10万円以上100万円未満', steps: ['申請者', '課長', '部長', '本部長'], status: true },
  { id: 3, name: '大規模購買承認', type: '金額', condition: '100万円以上', steps: ['申請者', '課長', '部長', '本部長', '経営層'], status: true },
  { id: 4, name: '営業部承認', type: '部門', condition: '営業部', steps: ['申請者', '営業課長', '営業部長'], status: true },
  { id: 5, name: '製造部承認', type: '部門', condition: '製造部', steps: ['申請者', '製造課長', '製造部長'], status: true },
])

const delegations = ref([
  { id: 1, delegator: '山田太郎', delegate: '鈴木花子', start_date: '2026-02-01', end_date: '2026-02-10', scope: '全承認', reason: '出張', status: '有効' },
  { id: 2, delegator: '佐藤一郎', delegate: '田中二郎', start_date: '2026-02-05', end_date: '2026-02-07', scope: '購買承認のみ', reason: '休暇', status: '有効' },
  { id: 3, delegator: '高橋三郎', delegate: '伊藤四郎', start_date: '2026-01-20', end_date: '2026-01-25', scope: '全承認', reason: '研修', status: '終了' },
])

const workflowDefinitions = ref([
  { id: 1, code: 'WF_PO', name: '購買発注承認', document_type: '発注書', approval_route: '通常購買承認', timeout_days: 3, escalation: true },
  { id: 2, code: 'WF_SO', name: '受注承認', document_type: '受注書', approval_route: '営業部承認', timeout_days: 2, escalation: true },
  { id: 3, code: 'WF_QT', name: '見積承認', document_type: '見積書', approval_route: '営業部承認', timeout_days: 1, escalation: false },
  { id: 4, code: 'WF_INV', name: '請求書承認', document_type: '請求書', approval_route: '通常購買承認', timeout_days: 5, escalation: true },
])

const getRouteTypeTag = (type: string) => {
  return type === '金額' ? 'warning' : 'primary'
}

const getDelegationStatusType = (status: string) => {
  return status === '有効' ? 'success' : 'info'
}

const handleAddRoute = () => ElMessage.info('承認ルート追加ダイアログを表示（TODO: 実装）')
const handleEditRoute = (row: any) => ElMessage.info(`ルート「${row.name}」を編集（TODO: 実装）`)
const handleDeleteRoute = async (row: any) => {
  await ElMessageBox.confirm(`ルート「${row.name}」を削除しますか？`, '確認', { type: 'warning' })
  ElMessage.success('削除しました（TODO: API呼び出し）')
}

const handleAddDelegation = () => ElMessage.info('代理設定追加ダイアログを表示（TODO: 実装）')
const handleEditDelegation = (_row?: unknown) => ElMessage.info('代理設定を編集（TODO: 実装）')
const handleDeleteDelegation = async (_row?: unknown) => {
  await ElMessageBox.confirm('この代理設定を削除しますか？', '確認', { type: 'warning' })
  ElMessage.success('削除しました（TODO: API呼び出し）')
}

const handleAddWorkflow = () => ElMessage.info('ワークフロー追加ダイアログを表示（TODO: 実装）')
const handleEditWorkflow = (row: any) => ElMessage.info(`ワークフロー「${row.name}」を編集（TODO: 実装）`)
const handleDeleteWorkflow = async (row: any) => {
  await ElMessageBox.confirm(`ワークフロー「${row.name}」を削除しますか？`, '確認', { type: 'warning' })
  ElMessage.success('削除しました（TODO: API呼び出し）')
}
</script>

<style scoped>
.workflow-setting {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: #303133;
}

.subtitle {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.tab-actions {
  margin-bottom: 16px;
}

.step-flow {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.step-arrow {
  color: #409eff;
  font-size: 14px;
}
</style>
