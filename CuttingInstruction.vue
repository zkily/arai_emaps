<template>
  <div class="cutting-instruction-container">
    <div class="page-header">
      <div class="header-left">
        <div class="header-title">
          <h1>切断指示管理</h1>
          <p>生産バッチの読み込みと切断指示の作成・管理・追跡を行います</p>
        </div>
      </div>
    </div>

    <!-- 上部：生産バッチテーブルエリア -->
    <div class="plan-section">
      <el-card class="section-card">
        <template #header>
          <div class="card-header">
            <div class="section-title">
              <el-icon size="20"><Calendar /></el-icon>
              <span>生産バッチ一覧</span>
            </div>
            <div class="header-actions">
              <el-button type="default" :icon="Refresh" @click="loadPlans">更新</el-button>
            </div>
          </div>
        </template>

        <!-- 計画検索フィルター・生産月バッチ生成 -->
        <div class="search-section">
          <el-form :model="planSearchForm" inline>
            <el-form-item label="生産月">
              <el-select
                v-model="selectedScheduleMonth"
                placeholder="月を選択（計画ファイル）"
                clearable
                style="width: 180px"
              >
                <el-option
                  v-for="m in scheduleMonths"
                  :key="m.value"
                  :label="m.label"
                  :value="m.value"
                />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                :loading="generateFromScheduleLoading"
                :disabled="!selectedScheduleMonth"
                @click="generateFromSchedule"
              >
                指定月でバッチ生成
              </el-button>
            </el-form-item>
            <el-form-item label="製品名">
              <el-input
                v-model="planSearchForm.productName"
                placeholder="製品名を入力"
                clearable
                style="width: 200px"
              />
            </el-form-item>
            <el-form-item label="設備">
              <el-select
                v-model="planSearchForm.equipment"
                placeholder="設備を選択"
                clearable
                style="width: 200px"
              >
                <el-option
                  v-for="machine in machineOptions"
                  :key="machine.machine_cd"
                  :label="machine.machine_name"
                  :value="machine.machine_cd"
                />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="default" @click="searchPlans">検索</el-button>
            </el-form-item>
          </el-form>
        </div>

        <el-table :data="plans" v-loading="planLoading" :style="{ width: '100%' }" max-height="400">
          <el-table-column prop="equipment" label="設備" width="100" align="center" />
          <el-table-column prop="generationOrder" label="生成順序" width="100" align="center" />
          <el-table-column prop="productName" label="製品名" width="200" />
          <el-table-column prop="quantity" label="数量" width="100" align="center" />
          <el-table-column prop="productionBatch" label="生産バッチ" width="100" align="center" />
          <el-table-column prop="plannedDate" label="計画日" width="120" />
        </el-table>

        <div class="pagination-container">
          <el-pagination
            v-model:current-page="planPagination.currentPage"
            v-model:page-size="planPagination.pageSize"
            :page-sizes="[10, 20, 50]"
            :total="planPagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handlePlanSizeChange"
            @current-change="handlePlanCurrentChange"
          />
        </div>
      </el-card>
    </div>

    <!-- 下部：切断指示管理テーブルエリア -->
    <div class="instruction-section">
      <el-card class="section-card">
        <template #header>
          <div class="card-header">
            <div class="section-title">
              <el-icon size="20"><Document /></el-icon>
              <span>切断指示一覧</span>
            </div>
            <div class="header-actions">
              <el-button type="primary" @click="showCreateDialog" :icon="Plus">
                新規切断指示
              </el-button>
              <el-button @click="exportData" :icon="Download"> エクスポート </el-button>
              <el-button @click="refreshData" :icon="Refresh"> 更新 </el-button>
            </div>
          </div>
        </template>

        <!-- 指示検索フィルター -->
        <div class="search-section">
          <el-form :model="searchForm" inline>
            <el-form-item label="指示番号">
              <el-input
                v-model="searchForm.instructionNo"
                placeholder="指示番号を入力"
                clearable
                style="width: 200px"
              />
            </el-form-item>
            <el-form-item label="材料">
              <el-input
                v-model="searchForm.material"
                placeholder="材料名を入力"
                clearable
                style="width: 200px"
              />
            </el-form-item>
            <el-form-item label="状態">
              <el-select
                v-model="searchForm.status"
                placeholder="状態を選択"
                clearable
                style="width: 150px"
              >
                <el-option label="未開始" value="pending" />
                <el-option label="進行中" value="inProgress" />
                <el-option label="完了" value="completed" />
                <el-option label="取消" value="cancelled" />
              </el-select>
            </el-form-item>
            <el-form-item label="作成日">
              <el-date-picker
                v-model="searchForm.dateRange"
                type="daterange"
                range-separator="〜"
                start-placeholder="開始日"
                end-placeholder="終了日"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="searchInstructions" :icon="Search">
                検索
              </el-button>
              <el-button @click="resetSearch" :icon="Refresh"> リセット </el-button>
            </el-form-item>
          </el-form>
        </div>

        <!-- 統計カード -->
        <div class="stats-section">
          <el-row :gutter="16">
            <el-col :span="6">
              <el-card class="stat-card">
                <div class="stat-content">
                  <div class="stat-icon total">
                    <el-icon size="24"><Document /></el-icon>
                  </div>
                  <div class="stat-info">
                    <div class="stat-number">{{ stats.total }}</div>
                    <div class="stat-label">総指示数</div>
                  </div>
                </div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card class="stat-card">
                <div class="stat-content">
                  <div class="stat-icon pending">
                    <el-icon size="24"><Clock /></el-icon>
                  </div>
                  <div class="stat-info">
                    <div class="stat-number">{{ stats.pending }}</div>
                    <div class="stat-label">未開始</div>
                  </div>
                </div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card class="stat-card">
                <div class="stat-content">
                  <div class="stat-icon progress">
                    <el-icon size="24"><Refresh /></el-icon>
                  </div>
                  <div class="stat-info">
                    <div class="stat-number">{{ stats.inProgress }}</div>
                    <div class="stat-label">進行中</div>
                  </div>
                </div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card class="stat-card">
                <div class="stat-content">
                  <div class="stat-icon completed">
                    <el-icon size="24"><Check /></el-icon>
                  </div>
                  <div class="stat-info">
                    <div class="stat-number">{{ stats.completed }}</div>
                    <div class="stat-label">完了</div>
                  </div>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </div>

        <el-table
          :data="instructions"
          v-loading="loading"
          :style="{ width: '100%' }"
          @selection-change="handleSelectionChange"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column prop="instructionNo" label="指示番号" width="150" fixed="left">
            <template #default="scope">
              <el-link @click="viewInstruction(scope.row)" type="primary">
                {{ scope.row.instructionNo }}
              </el-link>
            </template>
          </el-table-column>
          <el-table-column prop="material" label="材料" width="200" />
          <el-table-column prop="dimensions" label="寸法" width="150" />
          <el-table-column prop="quantity" label="数量" width="100" align="center" />
          <el-table-column prop="unit" label="単位" width="80" align="center" />
          <el-table-column prop="priority" label="優先度" width="100" align="center">
            <template #default="scope">
              <el-tag :type="getPriorityTagType(scope.row.priority)">
                {{ getPriorityLabel(scope.row.priority) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状態" width="100" align="center">
            <template #default="scope">
              <el-tag :type="getStatusTagType(scope.row.status)">
                {{ getStatusLabel(scope.row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="assignedTo" label="担当者" width="120" />
          <el-table-column prop="plannedStartDate" label="計画開始日" width="120" />
          <el-table-column prop="plannedEndDate" label="計画終了日" width="120" />
          <el-table-column prop="createdAt" label="作成日時" width="160" />
          <el-table-column label="操作" width="250" fixed="right">
            <template #default="scope">
              <el-button size="small" type="info" @click="handleViewDetail(scope.row)">
                詳細
              </el-button>
              <el-button size="small" @click="editInstruction(scope.row)"> 編集 </el-button>
              <el-button
                size="small"
                type="success"
                @click="startInstruction(scope.row)"
                v-if="scope.row.status === 'pending'"
              >
                開始
              </el-button>
              <el-button
                size="small"
                type="warning"
                @click="completeInstruction(scope.row)"
                v-if="scope.row.status === 'inProgress'"
              >
                完了
              </el-button>
              <el-button size="small" type="danger" @click="deleteInstruction(scope.row)">
                削除
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-container">
          <el-pagination
            v-model:current-page="pagination.currentPage"
            v-model:page-size="pagination.pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="pagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </el-card>
    </div>

    <!-- 作成/編集ダイアログ -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="800px"
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="120px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="指示番号" prop="instructionNo">
              <el-input v-model="form.instructionNo" placeholder="自動生成" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="優先度" prop="priority">
              <el-select v-model="form.priority" placeholder="優先度を選択">
                <el-option label="高" value="high" />
                <el-option label="中" value="medium" />
                <el-option label="低" value="low" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="材料" prop="material">
              <el-select v-model="form.material" placeholder="材料を選択" filterable allow-create>
                <el-option
                  v-for="material in materialOptions"
                  :key="material.value"
                  :label="material.label"
                  :value="material.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="寸法" prop="dimensions">
              <el-input v-model="form.dimensions" placeholder="例: 1000x500x3mm" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="数量" prop="quantity">
              <el-input-number v-model="form.quantity" :min="1" :max="9999" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="単位" prop="unit">
              <el-select v-model="form.unit" placeholder="単位を選択">
                <el-option label="個" value="pcs" />
                <el-option label="kg" value="kg" />
                <el-option label="m" value="m" />
                <el-option label="m²" value="m2" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="担当者" prop="assignedTo">
              <el-select v-model="form.assignedTo" placeholder="担当者を選択">
                <el-option
                  v-for="user in userOptions"
                  :key="user.value"
                  :label="user.label"
                  :value="user.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="計画開始日" prop="plannedStartDate">
              <el-date-picker
                v-model="form.plannedStartDate"
                type="date"
                placeholder="開始日を選択"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="計画終了日" prop="plannedEndDate">
              <el-date-picker
                v-model="form.plannedEndDate"
                type="date"
                placeholder="終了日を選択"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="備考" prop="remarks">
          <el-input
            v-model="form.remarks"
            type="textarea"
            :rows="3"
            placeholder="備考を入力してください"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm" :loading="submitting">
            {{ isEdit ? '更新' : '作成' }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 切断指示詳細ダイアログ -->
    <CuttingInstructionDialog
      v-model="cuttingDialogVisible"
      :instruction-data="selectedInstructionData"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import {
  Plus,
  Search,
  Refresh,
  Download,
  Document,
  Clock,
  Check,
  Calendar,
} from '@element-plus/icons-vue'
import CuttingInstructionDialog from './CuttingInstructionDialog.vue'

// 計画検索フォーム
const planSearchForm = reactive({
  productName: '',
  equipment: '',
})

// 指示検索フォーム
const searchForm = reactive({
  instructionNo: '',
  material: '',
  status: '',
  dateRange: [],
})

// 統計データ
const stats = ref({
  total: 0,
  pending: 0,
  inProgress: 0,
  completed: 0,
})

// 計画ページネーション
const planPagination = reactive({
  currentPage: 1,
  pageSize: 20,
  total: 0,
})

// 指示ページネーション
const pagination = reactive({
  currentPage: 1,
  pageSize: 20,
  total: 0,
})

// 計画テーブルデータ
const plans = ref<any[]>([])
const planLoading = ref(false)
const selectedPlans = ref<any[]>([])

// 生産月（production_plan_schedules.file_name から取得）
const scheduleMonths = ref<{ value: string; label: string }[]>([])
const selectedScheduleMonth = ref('')
const generateFromScheduleLoading = ref(false)

// 指示テーブルデータ
const instructions = ref<any[]>([])
const loading = ref(false)
const selectedRows = ref<any[]>([])

// ダイアログ
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref<FormInstance>()
const submitting = ref(false)

// 切断指示詳細ダイアログ
const cuttingDialogVisible = ref(false)
const selectedInstructionData = ref(null)

// フォームデータ
const form = reactive({
  instructionNo: '',
  material: '',
  dimensions: '',
  quantity: 1,
  unit: 'pcs',
  priority: 'medium',
  assignedTo: '',
  plannedStartDate: '',
  plannedEndDate: '',
  remarks: '',
})

// フォームバリデーションルール
const formRules = {
  material: [{ required: true, message: '材料を選択してください', trigger: 'change' }],
  dimensions: [{ required: true, message: '寸法を入力してください', trigger: 'blur' }],
  quantity: [{ required: true, message: '数量を入力してください', trigger: 'blur' }],
  unit: [{ required: true, message: '単位を選択してください', trigger: 'change' }],
  priority: [{ required: true, message: '優先度を選択してください', trigger: 'change' }],
  assignedTo: [{ required: true, message: '担当者を選択してください', trigger: 'change' }],
  plannedStartDate: [
    { required: true, message: '計画開始日を選択してください', trigger: 'change' },
  ],
  plannedEndDate: [{ required: true, message: '計画終了日を選択してください', trigger: 'change' }],
}

// オプションデータ
const materialOptions = ref([
  { label: 'SUS304', value: 'SUS304' },
  { label: 'SUS316', value: 'SUS316' },
  { label: 'AL6061', value: 'AL6061' },
  { label: 'AL7075', value: 'AL7075' },
  { label: 'SPCC', value: 'SPCC' },
  { label: 'SPHC', value: 'SPHC' },
])

const userOptions = ref([
  { label: '田中太郎', value: 'tanaka' },
  { label: '佐藤花子', value: 'sato' },
  { label: '鈴木一郎', value: 'suzuki' },
  { label: '高橋美咲', value: 'takahashi' },
])

// 設備オプション
const machineOptions = ref<any[]>([])

// 設備データを読み込み
const loadMachineOptions = async () => {
  try {
    // 直接machines表からmachine_type='成型'の設備を取得
    const response = await fetch('/api/plan/machines/all?machine_type=成型')
    const result = await response.json()

    if (result.success) {
      machineOptions.value = result.data
    }
  } catch (error) {
    console.error('設備データの読み込みに失敗:', error)
    // エラーの場合は空の配列を設定
    machineOptions.value = []
  }
}

// 計算プロパティ
const dialogTitle = computed(() => (isEdit.value ? '切断指示編集' : '新規切断指示作成'))

// 作成ダイアログを表示
const showCreateDialog = () => {
  isEdit.value = false
  resetForm()
  generateInstructionNo()
  dialogVisible.value = true
}

// フォームをリセット
const resetForm = () => {
  Object.assign(form, {
    instructionNo: '',
    material: '',
    dimensions: '',
    quantity: 1,
    unit: 'pcs',
    priority: 'medium',
    assignedTo: '',
    plannedStartDate: '',
    plannedEndDate: '',
    remarks: '',
  })
  formRef.value?.clearValidate()
}

// 指示番号を生成
const generateInstructionNo = () => {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  const random = Math.floor(Math.random() * 1000)
    .toString()
    .padStart(3, '0')
  form.instructionNo = `CUT-${year}${month}${day}-${random}`
}

// フォームを送信
const submitForm = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    submitting.value = true

    // ここでAPIを呼び出してデータを保存する必要があります
    await new Promise((resolve) => setTimeout(resolve, 1000)) // API呼び出しをシミュレート

    ElMessage.success(isEdit.value ? '切断指示を更新しました' : '切断指示を作成しました')
    dialogVisible.value = false
    loadInstructions()
    loadStats()
  } catch (error) {
    console.error('フォームバリデーション失敗:', error)
  } finally {
    submitting.value = false
  }
}

// 指示を検索
const searchInstructions = () => {
  pagination.currentPage = 1
  loadInstructions()
}

// 計画検索をリセット
const resetPlanSearch = () => {
  Object.assign(planSearchForm, {
    productName: '',
    equipment: '',
  })
  searchPlans()
}

// 指示検索をリセット
const resetSearch = () => {
  Object.assign(searchForm, {
    instructionNo: '',
    material: '',
    status: '',
    dateRange: [],
  })
  searchInstructions()
}

// 指示詳細を表示
const viewInstruction = (instruction: any) => {
  ElMessage.info(`指示詳細を表示: ${instruction.instructionNo}`)
}

// 切断指示詳細を表示
const handleViewDetail = (instruction: any) => {
  selectedInstructionData.value = instruction
  cuttingDialogVisible.value = true
}

// 指示を編集
const editInstruction = (instruction: any) => {
  isEdit.value = true
  Object.assign(form, instruction)
  dialogVisible.value = true
}

// 指示を開始
const startInstruction = async (instruction: any) => {
  try {
    await ElMessageBox.confirm(`指示 ${instruction.instructionNo} を開始しますか？`, '確認', {
      confirmButtonText: '開始',
      cancelButtonText: '取消',
      type: 'warning',
    })

    // ここでAPIを呼び出して状態を更新する必要があります
    instruction.status = 'inProgress'
    ElMessage.success('指示を開始しました')
    loadStats()
  } catch {
    // ユーザーがキャンセル
  }
}

// 指示を完了
const completeInstruction = async (instruction: any) => {
  try {
    await ElMessageBox.confirm(`指示 ${instruction.instructionNo} を完了しますか？`, '確認', {
      confirmButtonText: '完了',
      cancelButtonText: '取消',
      type: 'success',
    })

    // ここでAPIを呼び出して状態を更新する必要があります
    instruction.status = 'completed'
    ElMessage.success('指示を完了しました')
    loadStats()
  } catch {
    // ユーザーがキャンセル
  }
}

// 指示を削除
const deleteInstruction = async (instruction: any) => {
  try {
    await ElMessageBox.confirm(`指示 ${instruction.instructionNo} を削除しますか？`, '確認', {
      confirmButtonText: '削除',
      cancelButtonText: '取消',
      type: 'error',
    })

    // ここでAPIを呼び出してデータを削除する必要があります
    const index = instructions.value.findIndex(
      (item) => item.instructionNo === instruction.instructionNo,
    )
    if (index > -1) {
      instructions.value.splice(index, 1)
    }

    ElMessage.success('指示を削除しました')
    loadStats()
  } catch {
    // ユーザーがキャンセル
  }
}

// 計画選択変更
const handlePlanSelectionChange = (selection: any[]) => {
  selectedPlans.value = selection
}

// 指示選択変更
const handleSelectionChange = (selection: any[]) => {
  selectedRows.value = selection
}

// 計画ページサイズ変更
const handlePlanSizeChange = (size: number) => {
  planPagination.pageSize = size
  loadPlans()
}

// 計画現在ページ変更
const handlePlanCurrentChange = (page: number) => {
  planPagination.currentPage = page
  loadPlans()
}

// 指示ページサイズ変更
const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  loadInstructions()
}

// 指示現在ページ変更
const handleCurrentChange = (page: number) => {
  pagination.currentPage = page
  loadInstructions()
}

// データをエクスポート
const exportData = () => {
  ElMessage.info('データをエクスポートしています...')
}

// データを更新
const refreshData = () => {
  loadInstructions()
  loadStats()
}

// 優先度タグスタイルを取得
const getPriorityTagType = (
  priority: string,
): 'primary' | 'success' | 'warning' | 'info' | 'danger' => {
  const priorityMap: Record<string, 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
    high: 'danger',
    medium: 'warning',
    low: 'success',
  }
  return priorityMap[priority] || 'info'
}

// 優先度タグテキストを取得
const getPriorityLabel = (priority: string) => {
  const priorityMap: Record<string, string> = {
    high: '高',
    medium: '中',
    low: '低',
  }
  return priorityMap[priority] || priority
}

// 状態タグスタイルを取得
const getStatusTagType = (
  status: string,
): 'primary' | 'success' | 'warning' | 'info' | 'danger' => {
  const statusMap: Record<string, 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
    pending: 'warning',
    inProgress: 'primary',
    completed: 'success',
    cancelled: 'danger',
  }
  return statusMap[status] || 'info'
}

// 状態タグテキストを取得
const getStatusLabel = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: '未開始',
    inProgress: '進行中',
    completed: '完了',
    cancelled: '取消',
  }
  return statusMap[status] || status
}

// 計画状態タグスタイルを取得
const getPlanStatusTagType = (
  status: string,
): 'primary' | 'success' | 'warning' | 'info' | 'danger' => {
  const statusMap: Record<string, 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
    draft: 'info',
    confirmed: 'primary',
    inProgress: 'warning',
    completed: 'success',
    cancelled: 'danger',
  }
  return statusMap[status] || 'info'
}

// 計画状態タグテキストを取得
const getPlanStatusLabel = (status: string) => {
  const statusMap: Record<string, string> = {
    draft: '草案',
    confirmed: '確定',
    inProgress: '進行中',
    completed: '完了',
    cancelled: '取消',
  }
  return statusMap[status] || status
}

// バッチ状態を計画状態にマッピング
const mapBatchStatusToPlanStatus = (batchStatus: string) => {
  const statusMap: Record<string, string> = {
    未開始: 'draft',
    作業中: 'inProgress',
    生産中: 'inProgress',
    完了: 'completed',
    取消済: 'cancelled',
    ロック済: 'confirmed',
  }
  return statusMap[batchStatus] || 'draft'
}

// バッチ状態に基づいて優先度を決定
const getPriorityFromStatus = (status: string) => {
  const priorityMap: Record<string, string> = {
    未開始: 'medium',
    作業中: 'high',
    生産中: 'high',
    完了: 'low',
    取消済: 'low',
    ロック済: 'high',
  }
  return priorityMap[status] || 'medium'
}

// バッチ番号からフィールド情報を抽出
const extractBatchInfo = (batchNo: string) => {
  if (!batchNo || batchNo.length < 19) {
    return {
      equipment: '',
      generationOrder: '',
      productionBatch: '',
    }
  }

  // 設備：第10位から6文字を抽出（インデックス9-14）
  const equipment = batchNo.substring(9, 15)

  // 生成順序：第16位から最後から4番目まで（インデックス15から最後から4番目まで）
  const generationOrder = batchNo.substring(15, batchNo.length - 4)

  // 生産バッチ：最後の3文字
  const productionBatch = batchNo.substring(batchNo.length - 3)

  return {
    equipment,
    generationOrder,
    productionBatch,
  }
}

// 指示リストを読み込み
const loadInstructions = async () => {
  loading.value = true
  try {
    // ここでAPIを呼び出してデータを取得する必要があります
    await new Promise((resolve) => setTimeout(resolve, 1000)) // API呼び出しをシミュレート

    // モックデータ
    instructions.value = [
      {
        instructionNo: 'CUT-20240115-001',
        material: 'SUS304',
        dimensions: '1000x500x3mm',
        quantity: 50,
        unit: 'pcs',
        priority: 'high',
        status: 'pending',
        assignedTo: '田中太郎',
        plannedStartDate: '2024-01-16',
        plannedEndDate: '2024-01-18',
        createdAt: '2024-01-15 09:30:00',
      },
      {
        instructionNo: 'CUT-20240115-002',
        material: 'AL6061',
        dimensions: '800x400x5mm',
        quantity: 30,
        unit: 'pcs',
        priority: 'medium',
        status: 'inProgress',
        assignedTo: '佐藤花子',
        plannedStartDate: '2024-01-15',
        plannedEndDate: '2024-01-17',
        createdAt: '2024-01-15 08:15:00',
      },
      {
        instructionNo: 'CUT-20240114-001',
        material: 'SPCC',
        dimensions: '1200x600x2mm',
        quantity: 25,
        unit: 'pcs',
        priority: 'low',
        status: 'completed',
        assignedTo: '鈴木一郎',
        plannedStartDate: '2024-01-14',
        plannedEndDate: '2024-01-16',
        createdAt: '2024-01-14 14:20:00',
      },
    ]

    pagination.total = instructions.value.length
  } catch (error) {
    console.error('指示リストの読み込みに失敗:', error)
    ElMessage.error('データの読み込みに失敗しました')
  } finally {
    loading.value = false
  }
}

// 統計データを読み込み
const loadStats = async () => {
  try {
    // ここでAPIを呼び出して統計データを取得する必要があります
    stats.value = {
      total: instructions.value.length,
      pending: instructions.value.filter((item) => item.status === 'pending').length,
      inProgress: instructions.value.filter((item) => item.status === 'inProgress').length,
      completed: instructions.value.filter((item) => item.status === 'completed').length,
    }
  } catch (error) {
    console.error('統計データの読み込みに失敗:', error)
  }
}

// 計画を検索
const searchPlans = () => {
  planPagination.currentPage = 1
  loadPlans()
}

// 計画月一覧を取得（file_name に含まれる月）
const loadScheduleMonths = async () => {
  try {
    const response = await fetch('/api/plan/batch/schedule-months')
    const result = await response.json()
    if (result.success && Array.isArray(result.data)) {
      scheduleMonths.value = result.data
    } else {
      scheduleMonths.value = []
    }
  } catch (e) {
    console.error('計画月一覧の取得に失敗:', e)
    scheduleMonths.value = []
  }
}

// 指定月で production_plan_schedules から production_batches を生成
const generateFromSchedule = async () => {
  if (!selectedScheduleMonth.value) {
    ElMessage.warning('生産月を選択してください')
    return
  }
  try {
    await ElMessageBox.confirm(
      `「${scheduleMonths.value.find((m) => m.value === selectedScheduleMonth.value)?.label ?? selectedScheduleMonth.value}」の計画から生産バッチを生成しますか？同一月の既存バッチ（計画由来）は上書きされます。`,
      'バッチ生成の確認',
      { confirmButtonText: '生成', cancelButtonText: '取消', type: 'warning' },
    )
  } catch {
    return
  }
  generateFromScheduleLoading.value = true
  try {
    const response = await fetch('/api/plan/batch/generate-from-schedule', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ month: selectedScheduleMonth.value }),
    })
    const result = await response.json()
    if (result.success) {
      ElMessage.success(result.message || '生産バッチを生成しました')
      loadPlans()
    } else {
      ElMessage.error(result.message || 'バッチ生成に失敗しました')
    }
  } catch (e) {
    console.error('バッチ生成に失敗:', e)
    ElMessage.error('バッチ生成に失敗しました')
  } finally {
    generateFromScheduleLoading.value = false
  }
}

// 計画詳細を表示
const viewPlanDetail = (plan: any) => {
  ElMessage.info(`バッチ詳細を表示: ${plan.planNo}`)
}

// 計画を読み込み
const loadPlans = async () => {
  planLoading.value = true
  try {
    // クエリパラメータを構築
    const params = new URLSearchParams()

    if (planSearchForm.productName) {
      params.append('product_name', planSearchForm.productName)
    }
    if (planSearchForm.equipment) {
      params.append('equipment', planSearchForm.equipment)
    }

    // APIを呼び出してバッチデータを取得
    const response = await fetch(`/api/plan/batch/list?${params.toString()}`)
    const result = await response.json()

    if (result.success) {
      // バッチデータを計画データ形式に変換
      plans.value = result.data.map((batch: any) => {
        const batchInfo = extractBatchInfo(batch.batch_no)
        return {
          planNo: batch.batch_no,
          productName: batch.product_name || batch.product_cd,
          material: batch.product_cd,
          dimensions: '', // バッチテーブルにサイズ情報がないため、後で製品テーブルから取得可能
          quantity: batch.planned_qty,
          unit: 'pcs', // デフォルト単位
          priority: getPriorityFromStatus(batch.status),
          status: mapBatchStatusToPlanStatus(batch.status),
          plannedDate: batch.from_date,
          createdAt: batch.created_at,
          batchId: batch.id,
          actualOutputQty: batch.actual_output_qty,
          batchType: batch.batch_type,
          toDate: batch.to_date,
          isLocked: batch.is_locked,
          // 新規フィールド
          equipment: batchInfo.equipment,
          generationOrder: batchInfo.generationOrder,
          productionBatch: batchInfo.productionBatch,
        }
      })

      planPagination.total = plans.value.length
    } else {
      throw new Error(result.message || 'データの取得に失敗しました')
    }
  } catch (error) {
    console.error('計画リストの読み込みに失敗:', error)
    ElMessage.error('計画データの読み込みに失敗しました')
    plans.value = []
    planPagination.total = 0
  } finally {
    planLoading.value = false
  }
}

// 指示を生成
const generateInstructions = async () => {
  if (selectedPlans.value.length === 0) {
    ElMessage.warning('指示を生成するバッチを選択してください')
    return
  }

  try {
    await ElMessageBox.confirm(
      `選択された ${selectedPlans.value.length} 件のバッチから切断指示を生成しますか？`,
      '確認',
      {
        confirmButtonText: '生成',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )

    // ここでAPIを呼び出して指示を生成する必要があります
    await new Promise((resolve) => setTimeout(resolve, 2000)) // API呼び出しをシミュレート

    ElMessage.success('切断指示を生成しました')
    loadInstructions()
    loadStats()
  } catch {
    // ユーザーがキャンセル
  }
}

// ページ初期化
onMounted(() => {
  loadMachineOptions()
  loadScheduleMonths()
  loadPlans()
  loadInstructions()
  loadStats()
})
</script>

<style scoped>
.cutting-instruction-container {
  padding: 24px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-title h1 {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 4px 0;
}

.header-title p {
  font-size: 14px;
  color: #606266;
  margin: 0;
}

/* 计划区域样式 */
.plan-section {
  margin-bottom: 24px;
}

.plan-section .section-card {
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

/* 指示区域样式 */
.instruction-section .section-card {
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.search-section {
  margin-bottom: 16px;
}

.stats-section {
  margin-bottom: 16px;
}

.stat-card {
  border-radius: 12px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-icon.total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.pending {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon.progress {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon.completed {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-info {
  flex: 1;
}

.stat-number {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #606266;
  margin-top: 4px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .cutting-instruction-container {
    padding: 16px;
  }

  .page-header {
    padding: 16px;
  }

  .header-title h1 {
    font-size: 20px;
  }
}

@media (max-width: 768px) {
  .cutting-instruction-container {
    padding: 12px;
  }

  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }

  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .section-title {
    font-size: 14px;
  }

  .header-actions {
    flex-wrap: wrap;
  }
}
</style>
