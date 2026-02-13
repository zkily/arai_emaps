<template>
  <div class="welding-instruction-container">
    <!-- コンパクトヘッダー -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-info">
          <div class="title-wrapper">
            <el-icon class="title-icon"><Document /></el-icon>
            <h1 class="page-title">溶接指示管理</h1>
          </div>
          <span class="page-subtitle">生産計画データ管理・指示作成システム</span>
        </div>
      </div>
    </div>

    <!-- 上部：溶接計画データテーブルエリア -->
    <div class="plan-section">
      <el-card class="section-card">
        <template #header>
          <div class="card-header">
            <div class="section-title">
              <el-icon size="20"><Calendar /></el-icon>
              <span>溶接計画データ一覧</span>
            </div>
            <div class="header-actions">
              <el-button
                @click="showUpdateEfficiencyDialog"
                :icon="Refresh"
                size="small"
                type="warning"
                class="action-btn update-btn"
              >
                能率・段取時間更新
              </el-button>
              <el-button
                @click="refreshPlanData"
                :icon="Refresh"
                size="small"
                type="info"
                class="action-btn refresh-btn"
              >
                データ更新
              </el-button>
            </div>
          </div>
        </template>

        <!-- コンパクト統計カード -->
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-icon total-icon">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ formatNumber(planStats.totalQuantity) }}</div>
              <div class="stat-label">計画生産数</div>
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-icon machine-icon">
              <el-icon><Monitor /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ planStats.machineCount }}</div>
              <div class="stat-label">稼働設備</div>
            </div>
          </div>
        </div>

        <!-- コンパクト検索バー -->
        <div class="search-bar">
          <div class="search-controls">
            <div class="date-control">
              <el-date-picker
                v-model="planSearchForm.dateRange"
                type="daterange"
                range-separator="〜"
                start-placeholder="開始日"
                end-placeholder="終了日"
                format="MM/DD"
                value-format="YYYY-MM-DD"
                @change="searchPlans"
                size="small"
                class="compact-date-picker"
              />
              <div class="date-buttons">
                <el-button size="small" @click="setDateRange(-1)" class="date-btn prev"
                  >前日</el-button
                >
                <el-button size="small" @click="setDateRange(0)" class="date-btn today"
                  >今日</el-button
                >
                <el-button size="small" @click="setDateRange(1)" class="date-btn next"
                  >翌日</el-button
                >
              </div>
            </div>
            <el-select
              v-model="planSearchForm.machineName"
              placeholder="設備選択"
              clearable
              @change="searchPlans"
              size="small"
              class="machine-select"
            >
              <el-option
                v-for="machine in machineOptions"
                :key="machine.value"
                :label="machine.label"
                :value="machine.value"
              />
            </el-select>
            <el-input
              v-model="planSearchForm.keyword"
              placeholder="製品名・設備名検索"
              clearable
              @input="searchPlans"
              size="small"
              class="keyword-input"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-tooltip
              content="基本的には翌日の日付で設定してから発行してください"
              placement="top"
            >
              <el-button
                @click="printInstructions"
                :icon="Download"
                size="small"
                type="success"
                class="print-btn instruction-btn"
              >
                指示書発行
              </el-button>
            </el-tooltip>
            <el-tooltip
              content="基準日平均生産数の計算に使用する稼働日数を指定できます（空欄の場合は自動計算）"
              placement="top"
            >
              <el-input-number
                v-model="specifiedWorkingDays"
                :min="1"
                :max="31"
                :precision="0"
                placeholder="稼働日数"
                size="small"
                style="width: 120px"
                clearable
                controls-position="right"
              />
            </el-tooltip>
            <el-tooltip
              content="基本的には翌日の日付で設定してから発行してください"
              placement="top"
            >
              <el-button
                @click="printSetupSchedule"
                :icon="Printer"
                size="small"
                type="primary"
                class="print-btn"
                :loading="printingSetupSchedule"
              >
                段取予定発行
              </el-button>
            </el-tooltip>
          </div>
        </div>

        <el-table
          :data="planData"
          v-loading="planLoading"
          :style="{ width: '100%' }"
          max-height="500"
          :default-sort="{ prop: 'plan_date', order: 'ascending' }"
          size="small"
          class="compact-table"
        >
          <el-table-column
            prop="plan_date"
            label="生産日"
            width="100"
            align="center"
            sortable
            :sort-orders="['ascending', 'descending']"
          />
          <el-table-column prop="process_name" label="工程名" width="80" align="center" />
          <el-table-column
            prop="machine_name"
            label="設備名"
            width="120"
            sortable
            :sort-orders="['ascending', 'descending']"
          />
          <el-table-column prop="product_cd" label="製品CD" width="100" />
          <el-table-column prop="product_name" label="製品名" width="180" />
          <el-table-column
            prop="operator"
            label="生産順位"
            width="100"
            sortable
            :sort-orders="['ascending', 'descending']"
          />
          <el-table-column prop="quantity" label="計画生産数" width="100" align="center" />
          <el-table-column
            prop="efficiency_rate"
            label="能率"
            width="100"
            align="center"
            sortable
            :sort-orders="['ascending', 'descending']"
          >
            <template #default="{ row }">
              <span
                v-if="
                  row.efficiency_rate !== null &&
                  row.efficiency_rate !== undefined &&
                  row.efficiency_rate !== ''
                "
              >
                {{ formatEfficiencyRate(row.efficiency_rate) }}
              </span>
              <span v-else style="color: #9ca3af">-</span>
            </template>
          </el-table-column>
          <el-table-column
            prop="setup_time"
            label="段取時間"
            width="110"
            align="center"
            sortable
            :sort-orders="['ascending', 'descending']"
          >
            <template #default="{ row }">
              <span
                v-if="
                  row.setup_time !== null && row.setup_time !== undefined && row.setup_time !== ''
                "
              >
                {{ row.setup_time }}分
              </span>
              <span v-else style="color: #9ca3af">-</span>
            </template>
          </el-table-column>
          <el-table-column prop="remarks" label="備考" width="200" align="left">
            <template #default="{ row }">
              <el-input
                v-model="row.remarks"
                size="small"
                placeholder="備考を入力"
                @input="handleRemarksInput(row)"
                @blur="saveRemarks(row)"
                @keyup.enter="saveRemarks(row)"
                clearable
              />
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-container">
          <el-pagination
            v-model:current-page="planPagination.currentPage"
            v-model:page-size="planPagination.pageSize"
            :page-sizes="[20, 50, 100]"
            :total="planPagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handlePlanSizeChange"
            @current-change="handlePlanCurrentChange"
            small
          />
        </div>
      </el-card>
    </div>

    <!-- 生産計画マトリックス -->
    <div class="matrix-section">
      <el-card class="section-card">
        <template #header>
          <div class="card-header">
            <div class="section-title">
              <el-icon size="16"><Document /></el-icon>
              <span>生産計画マトリックス</span>
            </div>
            <div class="header-actions">
              <el-input
                v-model="matrixSearchKeyword"
                placeholder="設備名・製品名で検索"
                clearable
                @input="filterMatrixData"
                size="small"
                class="matrix-search-input"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
              <el-date-picker
                v-model="matrixDateRange"
                type="daterange"
                range-separator="〜"
                start-placeholder="開始日"
                end-placeholder="終了日"
                format="MM/DD"
                value-format="YYYY-MM-DD"
                size="small"
                @change="loadMatrixData"
                class="compact-date-picker"
              />
              <div class="month-buttons">
                <el-button size="small" @click="setMatrixMonth(-1)" class="month-btn prev"
                  >前月</el-button
                >
                <el-button size="small" @click="setMatrixMonth(0)" class="month-btn current"
                  >今月</el-button
                >
                <el-button size="small" @click="setMatrixMonth(1)" class="month-btn next"
                  >翌月</el-button
                >
              </div>
              <div class="matrix-controls">
                <el-button
                  @click="exportToExcel"
                  :icon="Download"
                  size="small"
                  type="success"
                  class="export-btn"
                >
                  Excel出力
                </el-button>
                <el-button
                  @click="printMatrix"
                  :icon="Printer"
                  size="small"
                  type="primary"
                  class="print-btn"
                >
                  印刷
                </el-button>
              </div>
            </div>
          </div>
        </template>

        <div class="matrix-table-wrapper">
          <table class="matrix-table">
            <thead>
              <tr>
                <th class="sticky-col machine-col">設備</th>
                <th class="sticky-col product-col">製品名</th>
                <th class="sticky-col operator-col">生産順位</th>
                <th class="sticky-col total-col">生産数(合計)</th>
                <th
                  v-for="date in matrixDates"
                  :key="date"
                  :class="{ 'is-weekend': isWeekend(date), 'is-today': isToday(date) }"
                >
                  <div class="date-header">
                    <div class="date-text">{{ formatMatrixDate(date) }}</div>
                    <div class="weekday-text">{{ getWeekdayLabel(date) }}</div>
                  </div>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="row in visibleMatrixRows"
                :key="row.key"
                :class="[
                  'matrix-row',
                  'machine-group-' + row.group,
                  {
                    'group-header': row.isGroupHeader,
                    'child-row': row.isChildRow,
                    'row-highlighted': hoveredRow === row.key,
                  },
                ]"
                :style="{ borderLeft: `3px solid ${getMachineColor(row.machine_name)}` }"
                @mouseenter="handleCellHover(row.key, '')"
                @mouseleave="handleCellLeave"
              >
                <td class="sticky-col machine-col">
                  <div class="machine-cell">
                    <el-icon
                      v-if="row.isGroupHeader"
                      @click="toggleMachineCollapse(row.machine_name)"
                      class="collapse-icon"
                      :class="{ collapsed: row.isCollapsed }"
                    >
                      <ArrowDown />
                    </el-icon>
                    <span
                      class="machine-name"
                      :class="{
                        'group-header-text': row.isGroupHeader,
                        'child-text': row.isChildRow,
                      }"
                      :style="{ color: getMachineColor(row.machine_name) }"
                    >
                      {{ row.machine_name }}
                    </span>
                  </div>
                </td>
                <td class="sticky-col product-col" :class="{ 'child-text': row.isChildRow }">
                  {{ row.product_name }}
                </td>
                <td
                  class="sticky-col operator-col numeric-cell"
                  :class="{ 'child-text': row.isChildRow }"
                >
                  {{ row.operator || '' }}
                </td>
                <td
                  class="sticky-col total-col numeric-cell"
                  :class="{ 'child-text': row.isChildRow }"
                >
                  {{ formatQty(row.totalQty) }}
                </td>
                <td
                  v-for="date in matrixDates"
                  :key="row.key + '-' + date"
                  class="numeric-cell data-cell"
                  :class="{
                    'col-highlighted': hoveredCol === date,
                    'cell-highlighted': hoveredRow === row.key && hoveredCol === date,
                    'is-today': isToday(date),
                  }"
                  @mouseenter="handleCellHover(row.key, date)"
                  @mouseleave="handleCellLeave"
                >
                  <span v-if="row.dateToQty[date]">{{ formatQty(row.dateToQty[date]) }}</span>
                  <span v-else class="cell-empty"></span>
                </td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="matrix-total-row">
                <td class="sticky-col machine-col">合計</td>
                <td class="sticky-col product-col"></td>
                <td class="sticky-col operator-col"></td>
                <td class="sticky-col total-col numeric-cell">{{ formatQty(matrixGrandTotal) }}</td>
                <td
                  v-for="date in matrixDates"
                  :key="'total-' + date"
                  class="numeric-cell"
                  :class="{ 'is-weekend': isWeekend(date), 'is-today': isToday(date) }"
                >
                  {{ formatQty(matrixColumnTotals[date] || 0) }}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </el-card>
    </div>

    <!-- 打印预览ダイアログ -->
    <el-dialog
      v-model="printPreviewVisible"
      title="指示書印刷プレビュー"
      width="90%"
      :close-on-click-modal="false"
      class="print-preview-dialog"
    >
      <div class="print-preview-content">
        <div class="print-preview-header">
          <el-button @click="printInstructions" type="primary" :icon="Download">
            印刷実行
          </el-button>
          <el-button @click="printPreviewVisible = false"> 閉じる </el-button>
        </div>
        <div class="print-preview-body" v-html="printPreviewContent"></div>
      </div>
    </el-dialog>

    <!-- 能率・段取時間更新ダイアログ -->
    <el-dialog
      v-model="updateEfficiencyDialogVisible"
      title="能率・段取時間更新"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="updateEfficiencyForm" label-width="120px">
        <el-form-item label="開始日" required>
          <el-date-picker
            v-model="updateEfficiencyForm.startDate"
            type="date"
            placeholder="開始日を選択"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item>
          <el-alert title="更新内容" type="info" :closable="false" show-icon>
            <template #default>
              <div style="font-size: 12px; line-height: 1.6">
                <p>
                  <strong>更新手順：</strong>
                </p>
                <p>
                  1.
                  <strong>machine_cd更新：</strong
                  >machines表のmachine_nameとproduction_plan_updates表のmachine_nameを結合し、machine_cdを更新します（空値またはNULLのレコードのみ更新）
                </p>
                <p>
                  2.
                  <strong>能率・段取時間更新：</strong
                  >equipment_efficiency表のmachine_cd、product_cdと結合し、能率（efficiency_rate）と段取時間（setup_time）を更新します（変更があるレコードのみ更新）
                </p>
                <p style="color: #67c23a; margin-top: 8px">
                  <strong
                    >✓
                    最適化：バッチ更新を使用し、更新が必要なレコードのみを更新して更新速度を向上</strong
                  >
                </p>
                <p style="color: #e6a23c; margin-top: 8px">
                  <strong>⚠ 注意：選択した開始日以降のすべてのデータが更新されます</strong>
                </p>
              </div>
            </template>
          </el-alert>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="updateEfficiencyDialogVisible = false">キャンセル</el-button>
          <el-button
            type="primary"
            @click="updateEfficiencyAndSetupTime"
            :loading="updatingEfficiency"
          >
            更新実行
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: 'WeldingInstruction' })
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import {
  Search,
  Refresh,
  Download,
  Document,
  Calendar,
  TrendCharts,
  Monitor,
  ArrowDown,
  Printer,
} from '@element-plus/icons-vue'
import request from '@/shared/api/request'
import { fetchPlanBaselineComparison } from '@/api/planBaseline'

/** API 响应类型（request 拦截器返回 response.data） */
interface ApiResponse<T = unknown> {
  success?: boolean
  data?: T
  message?: string
  list?: unknown[]
  records?: unknown[]
}

// 計画検索フォーム
const planSearchForm = reactive({
  dateRange: [] as string[],
  machineName: '',
  keyword: '',
})

// 指示検索フォーム
const searchForm = reactive({
  instructionNo: '',
  productName: '',
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

// 計画生産数統計データ
const planStats = ref({
  totalQuantity: 0,
  machineCount: 0,
})

type PlanComparisonSummary = {
  baselinePlanTotal: number | null
  currentPlanTotal: number | null
  planDifference: number | null
  currentActualTotal: number | null
  actualDifference: number | null
  planAchievementRatio: number | null
  baselineDailyAverage: number | null
  baselinePlanAchievementRatio: number | null
  currentPlanAchievementRatio: number | null
  achievementRatioDifference: number | null
  productionStatus: string | null
  lastActualDate: string | null
}

const createEmptyPlanComparisonSummary = (): PlanComparisonSummary => ({
  baselinePlanTotal: null,
  currentPlanTotal: null,
  planDifference: null,
  currentActualTotal: null,
  actualDifference: null,
  planAchievementRatio: null,
  baselineDailyAverage: null,
  baselinePlanAchievementRatio: null,
  currentPlanAchievementRatio: null,
  achievementRatioDifference: null,
  productionStatus: null,
  lastActualDate: null,
})

const weldingPlanComparisonSummary = ref<PlanComparisonSummary>(createEmptyPlanComparisonSummary())

// 計画ページネーション
const planPagination = reactive({
  currentPage: 1,
  pageSize: 50,
  total: 0,
})

// 指示ページネーション
const pagination = reactive({
  currentPage: 1,
  pageSize: 20,
  total: 0,
})

// 計画テーブルデータ
const planData = ref<any[]>([])
const planLoading = ref(false)

// マトリックステーブル 独立した日付とデータ
const matrixDateRange = ref<string[]>([])
const matrixData = ref<any[]>([])
const matrixLoading = ref(false)
const matrixSearchKeyword = ref('')
const filteredMatrixData = ref<any[]>([])

// マトリックステーブル拡張機能
const hoveredRow = ref<string | null>(null)
const hoveredCol = ref<string | null>(null)
const collapsedMachines = ref<Set<string>>(new Set())

// マトリックステーブル（旧の計画表から派生した計算は削除され、独立した日付とデータに変更）

// 指示テーブルデータ
const instructions = ref<any[]>([])
const loading = ref(false)
const selectedRows = ref<any[]>([])

// 日別指示管理
const activeTab = ref('')
const dailyInstructionDates = ref<string[]>([])

// ダイアログ
const dialogVisible = ref(false)
const detailDialogVisible = ref(false)
const printPreviewVisible = ref(false)
const isEdit = ref(false)
const formRef = ref<FormInstance>()
const submitting = ref(false)
const selectedInstruction = ref<any>(null)
const printPreviewContent = ref('')
const updatingEfficiency = ref(false)
const updateEfficiencyDialogVisible = ref(false)
const printingSetupSchedule = ref(false)

// 指定工作日天数（用于基准日平均生产数计算，null表示自动计算）
const specifiedWorkingDays = ref<number | null>(20)

const isApiSuccess = (res: any): boolean => {
  if (res && typeof res === 'object' && 'success' in res) {
    return !!res.success
  }
  return true
}

// 能率・段取時間更新フォーム
const updateEfficiencyForm = reactive({
  startDate: '',
})

// 備考保存タイマー
const remarksSaveTimers = new Map<string, NodeJS.Timeout>()

// フォームデータ
const form = reactive({
  instructionNo: '',
  productName: '',
  productCd: '',
  quantity: 1,
  machineName: '',
  operator: '',
  planDate: '',
  assignedTo: '',
  plannedStartTime: '',
  plannedEndTime: '',
  priority: 'medium',
  remarks: '',
})

// フォームバリデーションルール
const formRules = {
  productName: [{ required: true, message: '品名を入力してください', trigger: 'blur' }],
  productCd: [{ required: true, message: '产品代码を入力してください', trigger: 'blur' }],
  quantity: [{ required: true, message: '数量を入力してください', trigger: 'blur' }],
  machineName: [{ required: true, message: 'ライン名を入力してください', trigger: 'blur' }],
  operator: [{ required: true, message: '生産準を入力してください', trigger: 'blur' }],
  planDate: [{ required: true, message: '生産日を選択してください', trigger: 'change' }],
  assignedTo: [{ required: true, message: '担当者を選択してください', trigger: 'change' }],
  priority: [{ required: true, message: '優先度を選択してください', trigger: 'change' }],
}

// オプションデータ
const userOptions = ref([
  { label: '田中太郎', value: 'tanaka' },
  { label: '佐藤花子', value: 'sato' },
  { label: '鈴木一郎', value: 'suzuki' },
  { label: '高橋美咲', value: 'takahashi' },
])

// 設備オプションデータ
const machineOptions = ref<any[]>([])

// 計算プロパティ
const dialogTitle = computed(() => (isEdit.value ? '溶接指示編集' : '新規溶接指示作成'))

// 検索フォームのデフォルト値を初期化
const initializeSearchForm = () => {
  // 生産日を当日に設定（日本時区）
  const todayStr = JapanDateUtils.getTodayString()
  planSearchForm.dateRange = [todayStr, todayStr]

  // 設備名は空（全設備を表示）
  planSearchForm.machineName = ''

  // キーワードは空
  planSearchForm.keyword = ''
}

// 日付範囲を設定（現在選択している日付からの相対日数）
const setDateRange = (daysOffset: number) => {
  let targetDate: Date

  if (planSearchForm.dateRange && planSearchForm.dateRange.length > 0) {
    // 現在選択している開始日を基準に計算（日本時区）
    const baseDate = new Date(planSearchForm.dateRange[0] + 'T12:00:00')
    targetDate = new Date(baseDate)
    targetDate.setDate(targetDate.getDate() + daysOffset)
  } else {
    // 日付が選択されていない場合、今日を基準に計算（日本時区）
    targetDate = JapanDateUtils.getCurrentDate()
    targetDate.setDate(targetDate.getDate() + daysOffset)
  }

  const dateStr = JapanDateUtils.getDateString(targetDate)
  planSearchForm.dateRange = [dateStr, dateStr]

  // 自動的に検索を実行
  searchPlans()
}

// 設備データを読み込み
const loadMachineOptions = async () => {
  try {
    console.log('設備データを読み込み中...')
    const result = (await request.get('/api/master/machines', {
      params: { machine_type: '溶接' },
    })) as ApiResponse<{ list: any[] }>

    console.log('API応答結果:', result)

    const list = (result?.data?.list ?? result?.list ?? (Array.isArray(result) ? result : [])) as any[]
    if (list.length > 0) {
      machineOptions.value = list
        .map((machine: any) => ({
          label: machine.machine_name,
          value: machine.machine_name,
        }))
        .sort((a, b) => a.label.localeCompare(b.label))
      console.log('設備オプションの読み込み成功:', machineOptions.value)
    } else {
      machineOptions.value = []
      if (!result?.success) ElMessage.error('設備データの取得に失敗しました')
    }
  } catch (error) {
    console.error('設備データの読み込みに失敗:', error)
    ElMessage.error('設備データの読み込みに失敗しました')
  }
}

// 計画データを読み込み
const loadPlanData = async () => {
  planLoading.value = true
  try {
    const params: any = {}

    if (planSearchForm.dateRange && planSearchForm.dateRange.length === 2) {
      params.startDate = planSearchForm.dateRange[0]
      params.endDate = planSearchForm.dateRange[1]
    }
    if (planSearchForm.machineName) {
      params.machineName = planSearchForm.machineName
    }
    if (planSearchForm.keyword) {
      params.keyword = planSearchForm.keyword
    }
    // デフォルトで溶接関連のデータのみ表示
    params.processName = '溶接'

    // すべてのフィルタリングデータを取得（ページングなし）
    params.page = 1
    params.limit = 10000

    console.log('計画データクエリパラメータ:', params)
    const result = (await request.get('/api/excel-monitor/plan-data', { params })) as ApiResponse<{ records: any[] }>
    console.log('計画データAPI応答:', result)

    if (result.success && result.data) {
      const records = result.data.records ?? []
      const filteredData = records.filter((item: any) => {
        // 製品名が空の場合は除外
        if (!item.product_name || item.product_name.trim() === '') {
          return false
        }
        // 計画生産数が0以下の場合は除外
        const quantity = parseFloat(item.quantity) || 0
        if (quantity <= 0) {
          return false
        }
        return true
      })
      console.log('フィルタリング前のデータ数:', records.length)
      console.log('フィルタリング後のデータ数:', filteredData.length)
      console.log('キーワードフィルタリングパラメータ:', planSearchForm.keyword)

      planData.value = filteredData
      // 総数をフィルタリング後のデータ数に設定
      planPagination.total = filteredData.length
      // ページサイズを総数に設定して、すべてのフィルタリングデータを表示
      if (filteredData.length > 0) {
        planPagination.pageSize = filteredData.length
      } else {
        planPagination.pageSize = 50 // データがない場合、デフォルト50を維持
      }
      planPagination.currentPage = 1 // 最初のページにリセット

      console.log('最終的に読み込まれた計画データ:', planData.value)
    } else {
      throw new Error(result.message || 'データの取得に失敗しました')
    }
  } catch (error) {
    console.error('計画データの読み込みに失敗:', error)
    ElMessage.error('計画データの読み込みに失敗しました')
    planData.value = []
    planPagination.total = 0
  } finally {
    planLoading.value = false
  }
}

// 指示リストを読み込み
const loadInstructions = async () => {
  loading.value = true
  try {
    // ここで実際のAPIを呼び出して溶接指示データを取得する必要があります
    // 現在はモックデータを使用
    await new Promise((resolve) => setTimeout(resolve, 1000))

    // モックデータ
    const mockInstructions = [
      {
        id: 1,
        instructionNo: 'MOLD-20240115-001',
        productName: '溶接部品A',
        productCd: 'MP001',
        quantity: 100,
        machineName: '溶接機1号',
        operator: '田中太郎',
        planDate: '2024-01-15',
        assignedTo: '佐藤花子',
        plannedStartTime: '09:00',
        plannedEndTime: '17:00',
        priority: 'high',
        status: 'pending',
        remarks: '急ぎの注文',
        createdAt: '2024-01-15 08:30:00',
      },
      {
        id: 2,
        instructionNo: 'MOLD-20240115-002',
        productName: '溶接部品B',
        productCd: 'MP002',
        quantity: 50,
        machineName: '溶接機2号',
        operator: '鈴木一郎',
        planDate: '2024-01-15',
        assignedTo: '高橋美咲',
        plannedStartTime: '10:00',
        plannedEndTime: '16:00',
        priority: 'medium',
        status: 'inProgress',
        remarks: '',
        createdAt: '2024-01-15 09:15:00',
      },
      {
        id: 3,
        instructionNo: 'MOLD-20240116-001',
        productName: '溶接部品C',
        productCd: 'MP003',
        quantity: 75,
        machineName: '溶接機1号',
        operator: '田中太郎',
        planDate: '2024-01-16',
        assignedTo: '佐藤花子',
        plannedStartTime: '08:00',
        plannedEndTime: '18:00',
        priority: 'low',
        status: 'completed',
        remarks: '',
        createdAt: '2024-01-16 07:45:00',
      },
    ]

    instructions.value = mockInstructions
    pagination.total = mockInstructions.length

    // 日別指示日付を更新
    updateDailyInstructionDates()
  } catch (error) {
    console.error('指示リストの読み込みに失敗:', error)
    ElMessage.error('データの読み込みに失敗しました')
  } finally {
    loading.value = false
  }
}

// 日別指示日付を更新
const updateDailyInstructionDates = () => {
  const dates = [...new Set(instructions.value.map((item) => item.planDate))].sort()
  dailyInstructionDates.value = dates
  if (dates.length > 0 && !activeTab.value) {
    activeTab.value = dates[0]
  }
}

// 日付に基づいて指示データを取得
const getInstructionsByDate = (date: string) => {
  return instructions.value.filter((item) => item.planDate === date)
}

// 格式化日期标签
const formatDateLabel = (date: string) => {
  // 使用日本时区 (JST, UTC+9)
  const d = new Date(new Date(date).toLocaleString('en-US', { timeZone: 'Asia/Tokyo' }))
  const month = d.getMonth() + 1
  const day = d.getDate()
  const dayOfWeek = ['日', '月', '火', '水', '木', '金', '土'][d.getDay()]
  return `${month}/${day}(${dayOfWeek})`
}

// 統計データを読み込み
const loadStats = async () => {
  try {
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

// 計画生産数統計を計算（すべてのフィルタリングデータ、ページングなし）
const calculatePlanStats = async () => {
  try {
    // すべてのフィルタリングデータを取得（ページングなし）
    const params: any = {}

    if (planSearchForm.dateRange && planSearchForm.dateRange.length === 2) {
      params.startDate = planSearchForm.dateRange[0]
      params.endDate = planSearchForm.dateRange[1]
    }
    if (planSearchForm.machineName) {
      params.machineName = planSearchForm.machineName
    }
    if (planSearchForm.keyword) {
      params.keyword = planSearchForm.keyword
    }
    // デフォルトで溶接関連のデータのみ表示
    params.processName = '溶接'

    // 大きなlimit値を設定してすべてのデータを取得
    params.page = 1
    params.limit = 10000

    console.log('統計クエリパラメータ:', params)
    const result = (await request.get('/api/excel-monitor/plan-data', { params })) as ApiResponse<{ records: any[] }>

    if (result.success && result.data) {
      const records = result.data.records ?? []
      const allFilteredData = records.filter(
        (item: any) => item.product_name && item.product_name.trim() !== '',
      )

      // 計画生産数合計を計算
      const totalQuantity = allFilteredData.reduce((sum: number, item: any) => {
        return sum + (parseInt(item.quantity) || 0)
      }, 0)

      // 設備数を計算（生産数>0）
      const machinesWithProduction = new Set()
      allFilteredData.forEach((item: any) => {
        if (parseInt(item.quantity) > 0) {
          machinesWithProduction.add(item.machine_name)
        }
      })

      planStats.value = {
        totalQuantity,
        machineCount: machinesWithProduction.size,
      }

      console.log('すべてのフィルタリングデータ統計:', {
        総レコード数: allFilteredData.length,
        計画生産数合計: totalQuantity,
        設備数: machinesWithProduction.size,
        設備リスト: Array.from(machinesWithProduction),
      })
    }
  } catch (error) {
    console.error('計画生産数統計の計算に失敗:', error)
  }
}

const getBaselineMonthFromDate = (dateStr?: string) => {
  if (!dateStr) return ''
  const normalized = dateStr.split('T')[0]
  const [year, month] = normalized.split('-')
  if (!year || !month) return ''
  return `${year}-${month}-01`
}

type LoadComparisonSummaryOptions = {
  silent?: boolean
  baselineMonth?: string
  workingDays?: number | null // 指定工作日天数，如果提供则使用此值，否则自动计算
}

const loadWeldingPlanComparisonSummary = async (
  options: LoadComparisonSummaryOptions = {},
): Promise<PlanComparisonSummary | null> => {
  const { silent = true, baselineMonth } = options
  const baseDate = planSearchForm.dateRange?.[0] || JapanDateUtils.getTodayString()
  const targetBaselineMonth = baselineMonth || getBaselineMonthFromDate(baseDate)

  if (!targetBaselineMonth) {
    weldingPlanComparisonSummary.value = createEmptyPlanComparisonSummary()
    return null
  }

  try {
    const result = await fetchPlanBaselineComparison({
      baselineMonth: targetBaselineMonth,
      processName: '溶接',
    })

    if (result?.summary) {
      const summary = result.summary
      const items = result.items || []

      // 计算工作天数：优先使用指定的工作日天数，否则从items中统计不同的日期（排除周末）
      let workingDaysCount: number
      if (
        options.workingDays !== null &&
        options.workingDays !== undefined &&
        options.workingDays > 0
      ) {
        // 使用指定的工作日天数
        workingDaysCount = options.workingDays
        console.log('使用指定的工作日天数:', workingDaysCount)
      } else {
        // 自动计算：从items中统计不同的日期（排除周末）
        const workingDaysSet = new Set<string>()
        items.forEach((item: any) => {
          if (item.plan_date) {
            const dateStr = JapanDateUtils.normalizeDate(item.plan_date)
            const dayOfWeek = JapanDateUtils.getDayOfWeek(dateStr)
            // 排除周末（0=周日，6=周六）
            if (dayOfWeek !== 0 && dayOfWeek !== 6) {
              workingDaysSet.add(dateStr)
            }
          }
        })
        workingDaysCount = Math.max(1, workingDaysSet.size)
        console.log(
          '自动计算的工作日天数:',
          workingDaysCount,
          '统计的日期:',
          Array.from(workingDaysSet),
        )
      }

      const actualTotal = summary.currentActualTotal ?? 0
      // 現行計画達成率 = 現行実績 / 現行計画合計 × 100
      const currentPlanAchievement =
        summary.currentPlanTotal && summary.currentPlanTotal !== 0
          ? (actualTotal / summary.currentPlanTotal) * 100
          : null

      // 基準計画達成率 = 現行実績 / 基準計画合計 × 100
      const baselinePlanAchievement =
        summary.baselinePlanTotal && summary.baselinePlanTotal !== 0
          ? (actualTotal / summary.baselinePlanTotal) * 100
          : null

      // 基準日平均生産数 = 基準計画合計 / 稼働日
      const baselineDailyAverage =
        summary.baselinePlanTotal !== null &&
        summary.baselinePlanTotal !== undefined &&
        workingDaysCount > 0
          ? summary.baselinePlanTotal / workingDaysCount
          : null

      // 達成率差異 = 計画対実績差 / 基準計画合計 × 100%
      // 計画対実績差 = 現行実績 - 基準計画合計（API 定义）
      // 正数表示実績超过（生产快），负数表示実績不足（生产慢）
      const achievementRatioDifference =
        summary.actualDifference !== null &&
        summary.actualDifference !== undefined &&
        summary.baselinePlanTotal !== null &&
        summary.baselinePlanTotal !== undefined &&
        summary.baselinePlanTotal !== 0
          ? (summary.actualDifference / summary.baselinePlanTotal) * 100
          : null

      // 生产状态判定（与 API 計画対実績差 = 現行実績 - 基準計画 一致）
      // 達成率差異 > 5%: 実績超过计划 → 生産早い（快）
      // 達成率差異 < -5%: 実績不足计划 → 生産遅れ（慢）
      // 其他: 生産正常（正常）
      let productionStatus: string | null = null
      if (achievementRatioDifference !== null && achievementRatioDifference !== undefined) {
        if (achievementRatioDifference > 5) {
          productionStatus = '生産早い'
        } else if (achievementRatioDifference < -5) {
          productionStatus = '生産遅れ'
        } else {
          productionStatus = '生産正常'
        }
      }

      // 找到最后実績数大于0的日期
      let lastActualDate: string | null = null
      const itemsWithActual = items
        .filter(
          (item: any) =>
            item.current_actual !== null &&
            item.current_actual !== undefined &&
            item.current_actual > 0,
        )
        .sort((a: any, b: any) => {
          const dateA = new Date(a.plan_date).getTime()
          const dateB = new Date(b.plan_date).getTime()
          return dateB - dateA // 降序排列，最新的在前
        })

      if (itemsWithActual.length > 0 && itemsWithActual[0].plan_date) {
        lastActualDate = JapanDateUtils.formatDate(itemsWithActual[0].plan_date, '/')
      }

      const mapped: PlanComparisonSummary = {
        baselinePlanTotal:
          summary.baselinePlanTotal === null || summary.baselinePlanTotal === undefined
            ? null
            : summary.baselinePlanTotal,
        currentPlanTotal:
          summary.currentPlanTotal === null || summary.currentPlanTotal === undefined
            ? null
            : summary.currentPlanTotal,
        planDifference:
          summary.planDifference === null || summary.planDifference === undefined
            ? null
            : summary.planDifference,
        currentActualTotal:
          summary.currentActualTotal === null || summary.currentActualTotal === undefined
            ? null
            : summary.currentActualTotal,
        actualDifference:
          summary.actualDifference === null || summary.actualDifference === undefined
            ? null
            : summary.actualDifference,
        planAchievementRatio: currentPlanAchievement,
        baselineDailyAverage,
        baselinePlanAchievementRatio: baselinePlanAchievement,
        currentPlanAchievementRatio: currentPlanAchievement,
        achievementRatioDifference,
        productionStatus,
        lastActualDate,
      }
      weldingPlanComparisonSummary.value = mapped
      return mapped
    }

    weldingPlanComparisonSummary.value = createEmptyPlanComparisonSummary()
    return null
  } catch (error) {
    console.error('溶接ベースライン比較データの取得に失敗:', error)
    if (!silent) {
      ElMessage.error('溶接計画比較データの取得に失敗しました')
    }
    return null
  }
}

// 計画検索
const searchPlans = () => {
  planPagination.currentPage = 1
  loadPlanData()
  calculatePlanStats() // 同时更新统计
  loadWeldingPlanComparisonSummary({ silent: true, workingDays: specifiedWorkingDays.value })
}

// 計画検索をリセット
const resetPlanSearch = () => {
  // 重置为默认值
  initializeSearchForm()
  searchPlans()
  calculatePlanStats() // 同时更新统计
}

// 指示検索
const searchInstructions = () => {
  pagination.currentPage = 1
  loadInstructions()
}

// 指示検索をリセット
const resetSearch = () => {
  Object.assign(searchForm, {
    instructionNo: '',
    productName: '',
    status: '',
    dateRange: [],
  })
  searchInstructions()
}

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
    productName: '',
    productCd: '',
    quantity: 1,
    machineName: '',
    operator: '',
    planDate: '',
    assignedTo: '',
    plannedStartTime: '',
    plannedEndTime: '',
    priority: 'medium',
    remarks: '',
  })
  formRef.value?.clearValidate()
}

// 指示番号を生成
const generateInstructionNo = () => {
  // 使用日本时区 (JST, UTC+9)
  const now = new Date(new Date().toLocaleString('en-US', { timeZone: 'Asia/Tokyo' }))
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  const random = Math.floor(Math.random() * 1000)
    .toString()
    .padStart(3, '0')
  form.instructionNo = `MOLD-${year}${month}${day}-${random}`
}

// フォームを送信
const submitForm = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    submitting.value = true

    // ここでAPIを呼び出してデータを保存する必要があります
    await new Promise((resolve) => setTimeout(resolve, 1000))

    ElMessage.success(isEdit.value ? '溶接指示を更新しました' : '溶接指示を作成しました')
    dialogVisible.value = false
    loadInstructions()
    loadStats()
  } catch (error) {
    console.error('フォームバリデーション失敗:', error)
  } finally {
    submitting.value = false
  }
}

// 指示詳細を表示
const viewInstruction = (instruction: any) => {
  ElMessage.info(`指示詳細を表示: ${instruction.instructionNo}`)
}

// 指示詳細を表示
const handleViewDetail = (instruction: any) => {
  selectedInstruction.value = instruction
  detailDialogVisible.value = true
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

    const index = instructions.value.findIndex(
      (item) => item.instructionNo === instruction.instructionNo,
    )
    if (index > -1) {
      instructions.value.splice(index, 1)
    }

    ElMessage.success('指示を削除しました')
    loadStats()
    updateDailyInstructionDates()
  } catch {
    // ユーザーがキャンセル
  }
}

// 指示選択変更
const handleSelectionChange = (selection: any[]) => {
  selectedRows.value = selection
}

// 計画ページサイズ変更
const handlePlanSizeChange = (size: number) => {
  // 显示所有筛选数据，所以保持 pageSize 等于总数
  planPagination.pageSize = planPagination.total || size
  // 不需要重新加载数据，因为已经加载了所有数据
}

// 計画現在ページ変更
const handlePlanCurrentChange = (page: number) => {
  planPagination.currentPage = page
  // 不需要重新加载数据，因为已经加载了所有数据
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

// 指示書を印刷
const printInstructions = async () => {
  try {
    // 完全な期間データを取得（ページングデータではなく）
    const fullPlanData = await getFullPlanDataForPrint()

    if (fullPlanData.length === 0) {
      ElMessage.warning('印刷する計画データがありません')
      return
    }

    // 設備ごとにデータをグループ化
    const groupedByMachine = groupDataByMachine(fullPlanData)

    // 各設備の印刷内容を生成
    const printContents = await Promise.all(
      Object.keys(groupedByMachine).map(async (machineName) => {
        return await generatePrintContent(fullPlanData, machineName)
      }),
    )

    // 新しいウィンドウを開いて印刷
    const printWindow = window.open('', '_blank')
    if (printWindow) {
      // すべての設備の内容を1つのドキュメントに結合
      const combinedContent = printContents.join('<div style="page-break-before: always;"></div>')
      printWindow.document.write(combinedContent)
      printWindow.document.close()
      printWindow.focus()

      // コンテンツの読み込み完了を待ってから印刷
      printWindow.onload = () => {
        setTimeout(() => {
          printWindow.print()
          printWindow.close()
        }, 500)
      }
    }
  } catch (error) {
    console.error('印刷に失敗:', error)
    ElMessage.error('印刷に失敗しました')
  }
}

// 設備ごとにデータをグループ化
const groupDataByMachine = (data: any[]) => {
  const grouped: { [key: string]: any[] } = {}

  data.forEach((item) => {
    const machineName = item.machine_name || '未指定設備'
    if (!grouped[machineName]) {
      grouped[machineName] = []
    }
    grouped[machineName].push(item)
  })

  return grouped
}

// インテリジェントアルゴリズム：拡張された日付範囲を計算
const calculateSmartDateRange = async () => {
  try {
    if (!planSearchForm.dateRange || planSearchForm.dateRange.length === 0) {
      return { startDate: '', endDate: '' }
    }

    // 基準日を取得（検索条件の開始日、日本時区）
    const baseDateStr = planSearchForm.dateRange[0]
    const baseDate = new Date(baseDateStr + 'T12:00:00')
    const dates = []

    // インテリジェントに日付範囲を計算
    const baseDayOfWeek = baseDate.getDay() // 0=日曜日, 1=月曜日, ..., 6=土曜日

    // 前日を計算 - 月曜日の特別処理
    const prevDate = new Date(baseDate)
    if (baseDayOfWeek === 1) {
      // 基準日が月曜日の場合、前日を前週の金曜日にジャンプ
      prevDate.setDate(baseDate.getDate() - 3) // 月曜日 - 3日 = 金曜日
    } else {
      // その他の場合は通常通り1日減算
      prevDate.setDate(baseDate.getDate() - 1)
    }
    dates.push(prevDate)

    // 当日
    dates.push(new Date(baseDate))

    // 翌日を計算 - 金曜日の特別処理
    const nextDate = new Date(baseDate)
    if (baseDayOfWeek === 5) {
      // 基準日が金曜日の場合、翌日を翌週の月曜日にジャンプ
      nextDate.setDate(baseDate.getDate() + 3) // 金曜日 + 3日 = 月曜日
    } else {
      // その他の場合は通常通り1日加算
      nextDate.setDate(baseDate.getDate() + 1)
    }
    dates.push(nextDate)

    // インテリジェントに日付をフィルタリング：土日を避ける（生産計画がある場合を除く）
    const validDates = []

    for (const date of dates) {
      const dayOfWeek = date.getDay()
      const isWeekend = dayOfWeek === 0 || dayOfWeek === 6 // 0=日曜日, 6=土曜日
      const dateStr = JapanDateUtils.getDateString(date)

      if (!isWeekend) {
        // 平日は直接追加
        validDates.push(dateStr)
      } else {
        // 週末は生産計画データがあるかチェック
        try {
          const result = (await request.get('/api/excel-monitor/plan-data', {
            params: {
              startDate: dateStr,
              endDate: dateStr,
              machineName: planSearchForm.machineName || '',
              processName: '溶接',
              page: 1,
              limit: 1000,
            },
          })) as ApiResponse<{ records?: any[]; data?: any[]; list?: any[] }>

          // 返されたデータを解析
          let planData = []
          if (Array.isArray(result)) {
            planData = result
          } else if (result && Array.isArray(result.data)) {
            planData = result.data
          } else if (result && result.data && Array.isArray(result.data.list)) {
            planData = result.data.list
          } else if (result && result.data && Array.isArray(result.data.data)) {
            planData = result.data.data
          } else if (result && result.data && Array.isArray(result.data.records)) {
            planData = result.data.records
          }

          // 工程名が'成型'のデータをフィルタリング（溶接ページではこのフィルタリングは不要）
          const filteredPlanData = planData

          // 生産計画数が0より大きいデータがあるかチェック
          const hasProductionData = filteredPlanData.some(
            (item: any) => item.quantity && parseFloat(item.quantity) > 0,
          )

          if (hasProductionData) {
            validDates.push(dateStr)
            console.log(`週末 ${dateStr} に生産計画があり、範囲に追加しました`)
          } else {
            console.log(`週末 ${dateStr} に生産計画がなく、スキップしました`)
          }
        } catch (error) {
          console.error(`週末 ${dateStr} の生産データチェックに失敗:`, error)
          // チェックに失敗した場合、安全のため、この日付を追加しない
        }
      }
    }

    // ソートして範囲を返す
    validDates.sort()
    const startDate = validDates[0] || ''
    const endDate = validDates[validDates.length - 1] || ''

    console.log('インテリジェント日付範囲:', {
      startDate,
      endDate,
      validDates,
      baseDayOfWeek: baseDayOfWeek,
      isMonday: baseDayOfWeek === 1,
      isFriday: baseDayOfWeek === 5,
      baseDate: planSearchForm.dateRange[0],
      weekDayName: ['日', '月', '火', '水', '木', '金', '土'][baseDayOfWeek],
    })
    return { startDate, endDate }
  } catch (error) {
    console.error('インテリジェント日付範囲の計算に失敗:', error)
    // インテリジェントアルゴリズムが失敗した場合、元の日付範囲にフォールバック
    if (planSearchForm.dateRange && planSearchForm.dateRange.length >= 1) {
      const startDate = planSearchForm.dateRange[0]
      const endDate = planSearchForm.dateRange[1] || startDate
      return { startDate, endDate }
    }
    return { startDate: '', endDate: '' }
  }
}

// 印刷用の完全な期間データを取得
const getFullPlanDataForPrint = async () => {
  try {
    // インテリジェントアルゴリズムを使用して日付範囲を計算
    const { startDate, endDate } = await calculateSmartDateRange()

    if (!startDate || !endDate) {
      console.warn('日付範囲を確定できません')
      return []
    }

    const params: any = {
      startDate,
      endDate,
    }

    // 設備名フィルタリング
    if (planSearchForm.machineName) {
      params.machineName = planSearchForm.machineName
    }

    // キーワードフィルタリング
    if (planSearchForm.keyword) {
      params.keyword = planSearchForm.keyword
    }

    // デフォルトで溶接関連のデータのみ表示
    params.processName = '溶接'

    // 完全なデータを取得（ページングなし）
    const result = (await request.get('/api/excel-monitor/plan-data', {
      params: {
        ...params,
        page: 1,
        limit: 10000,
      },
    })) as ApiResponse<{ records: any[]; list?: any[]; data?: any[] }>

    console.log('API応答結果:', result)

    // 返されたデータが配列形式であることを確認
    let dataArray: any[] = []
    if (Array.isArray(result)) {
      dataArray = result
    } else if (result && Array.isArray(result.data)) {
      dataArray = result.data
    } else if (result && Array.isArray(result.list)) {
      dataArray = result.list
    } else if (result && result.data && Array.isArray(result.data.list)) {
      // {success: true, data: {list: [...]}} 形式を処理
      dataArray = result.data.list
    } else if (result && result.data && Array.isArray(result.data.data)) {
      // {success: true, data: {data: [...]}} 形式を処理
      dataArray = result.data.data
    } else if (result && result.data && Array.isArray(result.data.records)) {
      // {success: true, data: {records: [...]}} 形式を処理
      dataArray = result.data.records
    } else {
      console.warn('APIが返したデータ形式が配列ではありません:', result)
      console.log('result.dataにアクセスを試みます:', result.data)
      return []
    }

    // 製品名が空のデータをフィルタリング
    const filteredData = dataArray.filter(
      (item: any) => item.product_name && item.product_name.trim() !== '',
    )

    return filteredData
  } catch (error) {
    console.error('完全な計画データの取得に失敗:', error)
    return []
  }
}

// 指示書印刷プレビューを表示
const showPrintPreview = async () => {
  try {
    // 完全な期間データを取得（ページングデータではなく）
    const fullPlanData = await getFullPlanDataForPrint()

    if (fullPlanData.length === 0) {
      ElMessage.warning('印刷する計画データがありません')
      return
    }

    // 設備ごとにデータをグループ化
    const groupedByMachine = groupDataByMachine(fullPlanData)

    // 各設備のプレビュー内容を生成
    const previewContents = await Promise.all(
      Object.keys(groupedByMachine).map(async (machineName) => {
        // 完全なデータを渡し、generatePrintContent関数にフィルタリングを任せる
        return await generatePrintContent(fullPlanData, machineName)
      }),
    )

    // すべての設備の内容を結合
    const combinedPreviewContent = previewContents.join(
      '<div style="page-break-before: always; margin: 20px 0; border-top: 2px solid #ccc;"></div>',
    )
    printPreviewContent.value = combinedPreviewContent
    printPreviewVisible.value = true
  } catch (error) {
    console.error('プレビューに失敗:', error)
    ElMessage.error('プレビューの生成に失敗しました')
  }
}

// 設備CDキャッシュ
const machineCdCache = new Map<string, string>()

// QRコードを生成
const generateQRCode = (data: string): string => {
  // データが空の場合、デフォルトのプレースホルダーを返す
  if (!data || data.trim() === '') {
    console.log('製品CDが空です。デフォルトのプレースホルダーを使用します')
    return 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjQwIiBoZWlnaHQ9IjQwIiBmaWxsPSIjRjVGNUY1Ii8+Cjx0ZXh0IHg9IjIwIiB5PSIyMCIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXNpemU9IjEwIiBmaWxsPSIjOTk5IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+TkE8L3RleHQ+Cjwvc3ZnPgo='
  }

  // オンラインQRコード生成APIを使用（ピクセルを増やし、余白を追加して認識性を向上）
  const qrCodeUrl = `https://api.qrserver.com/v1/create-qr-code/?size=120x120&qzone=2&format=png&data=${encodeURIComponent(
    data,
  )}`
  console.log('製品CDのQRコードを生成、製品CD:', data, 'QRコードURL:', qrCodeUrl)
  return qrCodeUrl
}

// 設備CDを取得
const getMachineCd = async (machineName: string) => {
  try {
    if (!machineName || machineName === '未指定設備') {
      return '未指定'
    }

    // キャッシュをチェック
    if (machineCdCache.has(machineName)) {
      console.log('キャッシュから設備CDを取得:', machineName, '->', machineCdCache.get(machineName))
      return machineCdCache.get(machineName)!
    }

    console.log('設備CDをクエリ中、設備名:', machineName)

    const result = (await request.get('/api/master/machines', {
      params: {
        keyword: machineName,
        pageSize: 1000,
      },
    })) as ApiResponse<{ list: any[] }>

    console.log('設備クエリ結果:', result)

    const list = (result?.data?.list ?? result?.list ?? (Array.isArray(result) ? result : [])) as any[]
    if (list.length > 0) {
      const matchedMachine = list.find((machine: any) => machine.machine_name === machineName)

      if (matchedMachine && matchedMachine.machine_cd) {
        console.log('マッチした設備CDを見つけました:', matchedMachine.machine_cd)
        // 結果をキャッシュ
        machineCdCache.set(machineName, matchedMachine.machine_cd)
        return matchedMachine.machine_cd
      }

      // 正確なマッチがない場合、最初の結果を使用
      if (list[0].machine_cd) {
        console.log('最初の結果の設備CDを使用:', list[0].machine_cd)
        machineCdCache.set(machineName, list[0].machine_cd)
        return list[0].machine_cd
      }
    }

    console.log('設備CDが見つかりませんでした、設備名:', machineName)
    // 見つからなかった結果をキャッシュ
    machineCdCache.set(machineName, '未指定')
    return '未指定'
  } catch (error) {
    console.error('設備CDの取得に失敗:', error)
    // エラー結果をキャッシュ
    machineCdCache.set(machineName, '未指定')
    return '未指定'
  }
}

// 印刷内容を生成
const generatePrintContent = async (planData: any[], machineName?: string) => {
  const currentDate = new Date().toLocaleDateString('ja-JP')

  // フィルタリングされた基準日のみを表示（インテリジェントアルゴリズムで拡張された日付範囲は使用しない）
  let today = new Date().toLocaleDateString('ja-JP').replace(/\//g, '/')

  if (planSearchForm.dateRange && planSearchForm.dateRange.length >= 1) {
    // フィルタリング条件の基準日を使用（開始日、日本時区）
    const baseDateStr = planSearchForm.dateRange[0]
    const baseDate = new Date(baseDateStr + 'T12:00:00')
    today = baseDate.toLocaleDateString('ja-JP').replace(/\//g, '/')
  }

  // 設備CDを取得
  const machineCd = machineName ? await getMachineCd(machineName) : '未指定'

  return `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>溶接生産指示書 - ${machineName || '全設備'}</title>
      <style>
        @page {
          size: A5 landscape;
          margin: 8mm;
        }

        body {
          font-family: '遊ゴシック', BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
          font-size: 12px;
          line-height: 1.2;
          margin: 0;
          padding: 0;
          color: #000;
          -webkit-print-color-adjust: exact;
          print-color-adjust: exact;
        }

        @media print {
          html, body {
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
          }
        }

        .print-container {
          width: 100%;
          height: 100%;
        }

        .print-header {
          display: block;
          margin-bottom: 15px;
          padding-bottom: 5px;
          position: relative;
        }

        .print-header-top {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 10px;
        }

        .print-title {
          font-size: 20px;
          font-weight: bold;
          color: #000;
          flex: 0 0 auto;
        }

        .print-date-section {
          position: absolute;
          left: 50%;
          transform: translateX(-50%);
          text-align: center;
          font-size: 20px;
        }

        .print-date {
          font-weight: bold;
          font-size: 20px;
        }

        .print-date-sub {
          font-size: 10px;
          color: #000;
          margin-top: 2px;
        }

        .print-machine-section {
          text-align: center;
          font-size: 20px;
          flex: 0 0 auto;
          margin-left: auto;
          margin-right: 20px;
        }

        .print-subtitle {
          font-size: 20px;
          font-weight: bold;
          color: #000;
        }

        .print-process {
          font-size: 20px;
          color: #000;
          flex: 0 0 auto;
        }

        .qr-code-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 4px;
        }

        .qr-code-image {
          width: 33px;
          height: 33px;
          // border: 1px solid #000;
        }

        .qr-code-label {
          font-size: 10px;
          color: #000;
          text-align: center;
        }


        .main-table {
          width: 100%;
          border-collapse: collapse;
          border: none;
        }

        .main-table th,
        .main-table td {
          border: 0.8px solid #000;
          padding: 2px 3px;
          text-align: center;
          vertical-align: middle;
        }

        .main-table th {
          background-color: #f0f0f0;
          font-weight: bold;
          font-size: 10px;
          height: 12px;
        }

        .main-table td {
          font-size: 11px;
          height: 10px;
        }

        .main-table .product-cd {
          width: 10%;
        }

        .main-table .plan-date {
          width: 12%;
        }

        .main-table .priority {
          width: 8%;
        }

        .main-table .product-name {
          width: 18%;
        }

        .main-table .quantity {
          width: 12%;
        }

        .main-table .product-code {
          width: 12%;
        }



        .main-table .remarks {
          width: 20%;
        }

        .qr-code {
          width: 15px;
          height: 15px;
          // background-color: #000;
          display: inline-block;
          margin: 0 auto;
        }

        .product-cd-cell {
          text-align: center;
          vertical-align: middle;
        }

        .product-qr-container {
          display: flex;
          justify-content: center;
          align-items: center;
        }

        .product-qr-image {
          width: 25px;
          height: 25px;
          border: none;
        }

        /* 勤務時間帯表格样式 */
        .shift-table-container {
          position: fixed;
          bottom: 5px;
          left: 0;
          right: 0;
          width: 100%;
          page-break-inside: avoid;
          padding-top: 5px;
        }

        .section-divider {
          position: relative;
          text-align: center;
          margin-bottom: 5px;
        }

        .section-divider::before {
          content: '';
          position: absolute;
          top: 50%;
          left: 0;
          right: 0;
          height: 0.5px;
          background: #000;
          z-index: 1;
        }

        .section-title {
          background: white;
          padding: 0 10px;
          font-size: 10px;
          font-weight: bold;
          color: #000;
          position: relative;
          z-index: 2;
        }

        .shift-table {
          width: 100%;
          border-collapse: collapse;
          border: 0.5px solid #000;
          font-size: 9px;
        }

        .shift-table th,
        .shift-table td {
          border: 0.5px solid #000;
          padding: 2px 3px;
          text-align: center;
          vertical-align: middle;
        }

        .shift-table th {
          background-color: #f0f0f0;
          font-weight: normal;
          font-size: 11px;
          height: 25px;
        }

        .shift-table td {
          font-size: 11px;
          height: 30px;
        }

        .shift-table .worker {
          width: 8%;
        }

        .shift-table .shift-time {
          width: 14%;
        }

        .shift-table .stop-time {
          width: 8%;
        }

        .shift-table .product-name {
          width: 14%;
        }

        .shift-table .production-qty {
          width: 8%;
        }

        .shift-table .defect {
          width: 6%;
        }

        .shift-table .exchange {
          width: 6%;
        }

        .shift-table .transport {
          width: 6%;
        }

        .shift-table .cleaning {
          width: 6%;
        }

        .shift-table .preparation {
          width: 6%;
        }

        .shift-table .other {
          width: 6%;
        }

        .shift-table .ts {
          width: 6%;
        }

        .shift-table .sr {
          width: 6%;
        }

        /* 底部时间范围行样式 */
        .time-ranges-row {
          display: flex;
          justify-content: center;
          align-items: center;
          margin-top: 2px;
          padding: 2px 0;
          font-size: 9px;
          flex-wrap: nowrap;
        }

        .time-ranges-row span {
          flex: 0 0 auto;
          text-align: center;
          padding: 1px 2px;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 2px;
          white-space: nowrap;
        }

        .time-text {
          font-size: 9px;
          // font-weight: bold;
        }

        .checkbox {
          font-size: 12px;
          font-weight: bold;
          line-height: 1;
        }

        .highlighted-row {
          background-color: #f5f5f5;
        }

        .highlighted-row td {
          color: #dc3545;
          font-weight: bold;
        }

        .no-data-cell {
          text-align: center;
          vertical-align: middle;
          height: 120px;
          background-color: #f8f9fa;
        }

        .no-data-message {
          font-size: 24px;
          font-weight: bold;
          color: #6c757d;
          text-align: center;
          margin: 0;
          padding: 20px;
        }

      </style>
    </head>
    <body>
      <div class="print-container">
        <!-- 头部区域 -->
        <div class="print-header">
          <div class="print-header-top">
            <div class="print-title">溶接生産指示書</div>
            <div class="print-date-section">
              <div class="print-date">生産日 ${today}</div>
              <div class="print-date-sub">集計時間:前日15:00～当日15:00</div>
            </div>
            <div class="print-machine-section">
              ${machineName ? `<div class="print-subtitle">${machineName}</div>` : ''}
            </div>
            <div class="print-process">
              <div class="qr-code-container">
                <img src="${generateQRCode(machineCd || 'N/A')}" alt="設備CD: ${machineCd || 'N/A'}" class="qr-code-image" />
                <div class="qr-code-label">設備CD: ${machineCd || 'N/A'}</div>
              </div>
            </div>
          </div>

          <!-- 主要生产计划表格 -->
          <table class="main-table">
            <thead>
              <tr>
                <th class="product-cd">製品QR</th>
                <th class="plan-date">生産日</th>
                <th class="priority">生産順位</th>
                <th class="product-code">製品CD</th>
                <th class="product-name">生産品種</th>
                <th class="quantity">生産計画数</th>
                <th class="remarks">備考(参考)</th>
              </tr>
            </thead>
            <tbody>
              ${(() => {
                const filteredData = planData
                  .filter((plan) => {
                    // 只显示当前设备的数据
                    if (machineName && plan.machine_name !== machineName) {
                      return false
                    }

                    // 只显示生産計画数大于0的数据
                    if (!plan.quantity || parseFloat(plan.quantity) <= 0) {
                      return false
                    }

                    // 使用智能算法计算的日期范围进行过滤
                    // 注意：这里不需要再次过滤日期，因为getFullPlanDataForPrint已经使用了智能日期范围
                    return true
                  })
                  .slice(0, 4) // 只显示前4行数据

                // 如果没有数据，显示"生産停止"
                if (filteredData.length === 0) {
                  return `
                    <tr>
                      <td colspan="7" class="no-data-cell">
                        <div class="no-data-message">生産計画停止</div>
                      </td>
                    </tr>
                  `
                }

                // 有数据时显示正常内容
                return filteredData
                  .map((plan, index) => {
                    // 检查是否为基准日期
                    const isBaseDate =
                      planSearchForm.dateRange &&
                      planSearchForm.dateRange.length >= 1 &&
                      plan.plan_date === planSearchForm.dateRange[0]

                    // 调试信息：验证产品CD和产品名的对应关系
                    console.log('产品数据验证:', {
                      product_cd: plan.product_cd,
                      product_name: plan.product_name,
                      plan_date: plan.plan_date,
                      machine_name: plan.machine_name,
                    })

                    return `
                        <tr class="${isBaseDate ? 'highlighted-row' : ''}">
                          <td class="product-cd-cell">
                            <div class="product-qr-container">
                              <img src="${generateQRCode(plan.product_cd || 'N/A')}" alt="製品CD: ${plan.product_cd || 'N/A'}" class="product-qr-image" />
                            </div>
                          </td>
                          <td>${plan.plan_date || ''}</td>
                          <td>${plan.operator || ''}</td>
                          <td>${plan.product_cd || ''}</td>
                          <td>${plan.product_name || ''}</td>
                          <td>${plan.quantity || ''}</td>
                          <td>${plan.remarks || ''}</td>
                        </tr>
                      `
                  })
                  .join('')
              })()}
            </tbody>
        </table>
        </div>

        <!-- 作業時間帯表格 -->
        <div class="shift-table-container">
          <div class="section-divider">
            <span class="section-title">記入項目</span>
          </div>
          <table class="shift-table">
            <thead>
              <tr>
                <th class="worker">作業者</th>
                <th class="shift-time">作業時間帯</th>
                <th class="stop-time">停止(分)</th>
                <th class="product-name">製品名</th>
                <th class="production-qty">生産数</th>
                <th class="defect">不良</th>
                <th class="exchange">交換</th>
                <th class="transport">運搬</th>
                <th class="cleaning">清掃</th>
                <th class="preparation">準備</th>
                <th class="other">他</th>
                <th class="ts">TS</th>
                <th class="sr">SR</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td></td>
                <td>---</td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
              </tr>
              <tr>
                <td></td>
                <td>---</td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
              </tr>
              <tr>
                <td></td>
                <td>---</td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
              </tr>
              <tr>
                <td></td>
                <td>---</td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
              </tr>
              <tr>
                <td></td>
                <td>---</td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
              </tr>
              <tr>
                <td></td>
                <td>---</td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </body>
    </html>
  `
}

// 获取行键（用于備考保存）
const getRowKey = (row: any): string => {
  if (row.id) {
    return `id_${row.id}`
  }
  return `${row.plan_date}_${row.machine_name}_${row.product_cd}_${row.process_name || '溶接'}`
}

// 处理備考输入（防抖自动保存）
const handleRemarksInput = (row: any) => {
  const rowKey = getRowKey(row)

  // 清除之前的定时器
  if (remarksSaveTimers.has(rowKey)) {
    clearTimeout(remarksSaveTimers.get(rowKey)!)
  }

  // 设置新的定时器，1.5秒后自动保存
  const timer = setTimeout(() => {
    saveRemarks(row, false) // false表示静默保存，不显示成功消息
    remarksSaveTimers.delete(rowKey)
  }, 1500)

  remarksSaveTimers.set(rowKey, timer)
}

// 保存備考（remarks）
const saveRemarks = async (row: any, showSuccessMessage = true) => {
  try {
    // 清除该行的防抖定时器
    const rowKey = getRowKey(row)
    if (remarksSaveTimers.has(rowKey)) {
      clearTimeout(remarksSaveTimers.get(rowKey)!)
      remarksSaveTimers.delete(rowKey)
    }

    // 检查是否有必要的字段来标识记录
    if (!row.id && !row.plan_date && !row.machine_name && !row.product_cd) {
      console.warn('无法保存備考：缺少必要的标识字段')
      return
    }

    // 准备更新数据
    const updateData: any = {
      remarks: row.remarks || '',
    }

    // 如果有id，使用id更新
    if (row.id) {
      updateData.id = row.id
    } else {
      // 否则使用组合字段来标识记录
      updateData.plan_date = row.plan_date
      updateData.machine_name = row.machine_name
      updateData.product_cd = row.product_cd
      updateData.process_name = row.process_name || '溶接'
    }

    // 调用后端API更新remarks
    const result = (await request.put('/api/excel-monitor/plan-data/remarks', updateData)) as ApiResponse

    if (result.success) {
      if (showSuccessMessage) {
        ElMessage.success('備考を保存しました')
      }
      // 更新本地数据
      const index = planData.value.findIndex((item: any) => {
        if (row.id) {
          return item.id === row.id
        } else {
          return (
            item.plan_date === row.plan_date &&
            item.machine_name === row.machine_name &&
            item.product_cd === row.product_cd &&
            (item.process_name || '溶接') === (row.process_name || '溶接')
          )
        }
      })
      if (index !== -1) {
        planData.value[index].remarks = row.remarks
      }
    } else {
      ElMessage.error(result.message || '備考の保存に失敗しました')
    }
  } catch (error: any) {
    console.error('備考保存失败:', error)
    ElMessage.error('備考の保存に失敗しました: ' + (error.message || '未知のエラー'))
  }
}

// 格式化能率（显示为「○○本/h」）
const formatEfficiencyRate = (rate: number | string): string => {
  if (rate === null || rate === undefined || rate === '') return '-'
  const num = typeof rate === 'string' ? Number(rate) : rate
  if (!isFinite(num)) return '-'
  return `${formatNumber(num)}本/h`
}

// 显示能率・段取時間更新对话框
const showUpdateEfficiencyDialog = () => {
  updateEfficiencyForm.startDate = ''
  updateEfficiencyDialogVisible.value = true
}

// 更新能率・段取時間
const updateEfficiencyAndSetupTime = async () => {
  if (!updateEfficiencyForm.startDate) {
    ElMessage.warning('開始日を選択してください')
    return
  }

  try {
    updatingEfficiency.value = true

    const result = (await request.post('/api/excel-monitor/update-efficiency-and-setup-time', {
      startDate: updateEfficiencyForm.startDate,
      processName: '溶接',
    })) as ApiResponse

    if (isApiSuccess(result)) {
      ElMessage.success('能率・段取時間の更新が完了しました')
      updateEfficiencyDialogVisible.value = false
      // 刷新数据
      await loadPlanData()
      await calculatePlanStats()
    } else {
      throw new Error(result?.message || '更新失敗')
    }
  } catch (error: any) {
    console.error('能率・段取時間更新失败:', error)
    ElMessage.error(error.message || '更新に失敗しました')
  } finally {
    updatingEfficiency.value = false
  }
}

// 段取予定表印刷
const printSetupSchedule = async () => {
  printingSetupSchedule.value = true
  try {
    await loadEfficiencyData()

    const fullPlanData = await getFullPlanDataForPrint()

    if (fullPlanData.length === 0) {
      ElMessage.warning('印刷する計画データがありません')
      printingSetupSchedule.value = false
      return
    }

    const printContent = await generateSetupScheduleContent(fullPlanData)

    const iframe = document.createElement('iframe')
    iframe.style.position = 'fixed'
    iframe.style.right = '0'
    iframe.style.bottom = '0'
    iframe.style.width = '0'
    iframe.style.height = '0'
    iframe.style.border = '0'
    iframe.style.visibility = 'hidden'
    document.body.appendChild(iframe)

    const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document
    if (!iframeDoc) {
      ElMessage.error('印刷機能の初期化に失敗しました')
      document.body.removeChild(iframe)
      printingSetupSchedule.value = false
      return
    }

    iframeDoc.open()
    iframeDoc.write(printContent)
    iframeDoc.close()

    let hasPrinted = false
    const doPrint = () => {
      if (hasPrinted) return
      hasPrinted = true
      try {
        const iframeWindow = iframe.contentWindow
        if (iframeWindow && iframeDoc.body) {
          iframeWindow.focus()
          iframeWindow.print()
          setTimeout(() => {
            if (document.body.contains(iframe)) {
              document.body.removeChild(iframe)
            }
            printingSetupSchedule.value = false
          }, 1000)
        }
      } catch (error) {
        console.error('印刷実行エラー:', error)
        ElMessage.error('印刷の実行に失敗しました')
        if (document.body.contains(iframe)) {
          document.body.removeChild(iframe)
        }
        printingSetupSchedule.value = false
      }
    }

    iframe.onload = () => {
      setTimeout(doPrint, 500)
    }

    setTimeout(doPrint, 1500)
  } catch (error) {
    console.error('段取予定表印刷失败:', error)
    ElMessage.error('段取予定表の印刷に失敗しました')
    printingSetupSchedule.value = false
  }
}

// 計画データを更新
const refreshPlanData = () => {
  loadPlanData()
  calculatePlanStats() // 同时更新统计
  loadWeldingPlanComparisonSummary({ silent: true, workingDays: specifiedWorkingDays.value })
}

// 二维表（设备 × 生産日）派生数据
const matrixDates = computed(() => {
  if (!matrixDateRange.value || matrixDateRange.value.length !== 2) return [] as string[]
  const [start, end] = matrixDateRange.value
  const dates: string[] = []
  const dStart = new Date(start)
  const dEnd = new Date(end)
  for (let d = new Date(dStart); d <= dEnd; d.setDate(d.getDate() + 1)) {
    dates.push(d.toISOString().split('T')[0])
  }
  return dates
})

type MatrixRow = {
  key: string
  machine_name: string
  product_name: string
  operator: string
  totalQty: number
  dateToQty: Record<string, number>
  group: number
}

const matrixRows = computed<MatrixRow[]>(() => {
  const map = new Map<string, MatrixRow>()
  filteredMatrixData.value.forEach((x: any) => {
    if (!x || !x.machine_name || !x.product_name) return
    if (!x.quantity || parseFloat(x.quantity) <= 0) return
    const op = x.operator || ''
    const key = `${x.machine_name}|${x.product_cd || x.product_name}|${op}`
    if (!map.has(key)) {
      map.set(key, {
        key,
        machine_name: x.machine_name,
        product_name: x.product_name,
        operator: op,
        totalQty: 0,
        dateToQty: {},
        group: 0,
      })
    }
    const row = map.get(key)!
    const q = parseFloat(x.quantity) || 0
    row.totalQty += q
    if (x.plan_date) {
      row.dateToQty[x.plan_date] = (row.dateToQty[x.plan_date] || 0) + q
    }
  })
  // 排序：設備 -> 生産順位 -> 製品名（兜底）
  const sorted = Array.from(map.values()).sort((a, b) => {
    const m = a.machine_name.localeCompare(b.machine_name)
    if (m !== 0) return m

    // 生産順位优先，尽量按数值比较；为空的排在后面
    const ao = (a.operator ?? '').toString().trim()
    const bo = (b.operator ?? '').toString().trim()
    const an = ao === '' ? Number.POSITIVE_INFINITY : Number(ao)
    const bn = bo === '' ? Number.POSITIVE_INFINITY : Number(bo)

    if (!Number.isNaN(an) && !Number.isNaN(bn)) {
      if (an !== bn) return an - bn
    } else {
      const os = ao.localeCompare(bo, 'ja')
      if (os !== 0) return os
    }

    return a.product_name.localeCompare(b.product_name)
  })

  // 依設備分组着色：設備变化时递增分组索引
  let groupIndex = -1
  let lastMachine = ''
  sorted.forEach((row) => {
    if (row.machine_name !== lastMachine) {
      groupIndex = (groupIndex + 1) % 3 // 使用 3 组颜色循环
      lastMachine = row.machine_name
    }
    row.group = groupIndex
  })

  return sorted
})

// 支持折叠的矩阵行数据
const visibleMatrixRows = computed(() => {
  const allRows = matrixRows.value
  const result: any[] = []
  const machineGroups = new Map<string, any[]>()

  // 按设备分组
  allRows.forEach((row) => {
    if (!machineGroups.has(row.machine_name)) {
      machineGroups.set(row.machine_name, [])
    }
    machineGroups.get(row.machine_name)!.push(row)
  })

  // 为每个设备组添加行
  machineGroups.forEach((rows, machineName) => {
    // 添加设备组头部行
    const isCollapsed = isMachineCollapsed(machineName)
    const groupTotalQty = rows.reduce((sum, row) => sum + row.totalQty, 0)

    result.push({
      key: `machine-header-${machineName}`,
      machine_name: machineName,
      product_name: `${rows.length}件の製品`,
      operator: '',
      totalQty: groupTotalQty,
      dateToQty: rows.reduce(
        (acc, row) => {
          Object.entries(row.dateToQty).forEach(([date, qty]) => {
            acc[date] = (acc[date] || 0) + qty
          })
          return acc
        },
        {} as Record<string, number>,
      ),
      group: rows[0].group,
      isGroupHeader: true,
      isCollapsed,
      machineColor: getMachineColor(machineName),
    })

    // 如果未折叠，添加子行
    if (!isCollapsed) {
      rows.forEach((row) => {
        result.push({
          ...row,
          isGroupHeader: false,
          isChildRow: true,
        })
      })
    }
  })

  return result
})

// 加载二维表数据（独立于上方列表）
const loadMatrixData = async () => {
  if (!matrixDateRange.value || matrixDateRange.value.length !== 2) return
  matrixLoading.value = true
  try {
    const params: any = {
      startDate: matrixDateRange.value[0],
      endDate: matrixDateRange.value[1],
      processName: '溶接',
      page: 1,
      limit: 10000,
    }
    const result = (await request.get('/api/excel-monitor/plan-data', { params })) as ApiResponse<{ records: any[] }>
    if (result.success && result.data?.records) {
      const filtered = result.data.records.filter(
        (item: any) => item.product_name && item.product_name.trim() !== '',
      )
      matrixData.value = filtered
      filterMatrixData()
    } else {
      matrixData.value = []
      filteredMatrixData.value = []
    }
  } catch (e) {
    console.error('二维表データの読み込みに失敗:', e)
    matrixData.value = []
    filteredMatrixData.value = []
  } finally {
    matrixLoading.value = false
  }
}

// マトリックスデータ筛选
const filterMatrixData = () => {
  if (!matrixSearchKeyword.value || matrixSearchKeyword.value.trim() === '') {
    // 没有关键词时显示全部数据
    filteredMatrixData.value = matrixData.value
  } else {
    // 根据关键词筛选设备名和产品名
    const keyword = matrixSearchKeyword.value.toLowerCase().trim()
    filteredMatrixData.value = matrixData.value.filter((item: any) => {
      const machineName = (item.machine_name || '').toLowerCase()
      const productName = (item.product_name || '').toLowerCase()
      return machineName.includes(keyword) || productName.includes(keyword)
    })
  }
}

// 设置マトリックス月份（使用日本时区）
const setMatrixMonth = (monthOffset: number) => {
  // 使用日本时区 (JST, UTC+9)
  const now = new Date(new Date().toLocaleString('en-US', { timeZone: 'Asia/Tokyo' }))
  const targetDate = new Date(now.getFullYear(), now.getMonth() + monthOffset, 1)

  // 获取当月第一天和最后一天
  const firstDay = new Date(targetDate.getFullYear(), targetDate.getMonth(), 1)
  const lastDay = new Date(targetDate.getFullYear(), targetDate.getMonth() + 1, 0)

  // 格式化为YYYY-MM-DD格式
  const formatDate = (date: Date) => {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  }

  const startDate = formatDate(firstDay)
  const endDate = formatDate(lastDay)

  console.log(`设置月份范围: ${startDate} 到 ${endDate}`)

  matrixDateRange.value = [startDate, endDate]
  loadMatrixData()
}

// 列合计与总合计
const matrixColumnTotals = computed<Record<string, number>>(() => {
  const totals: Record<string, number> = {}
  matrixRows.value.forEach((row) => {
    Object.entries(row.dateToQty).forEach(([date, qty]) => {
      totals[date] = (totals[date] || 0) + (qty || 0)
    })
  })
  return totals
})

const matrixGrandTotal = computed(() => {
  return matrixRows.value.reduce((sum, r) => sum + (r.totalQty || 0), 0)
})

// 星期标签（JST）
const getWeekdayLabel = (date: string) => {
  try {
    // 统一到日本时区当天00:00，避免时区偏移
    const d = new Date(
      new Date(date + 'T00:00:00').toLocaleString('en-US', { timeZone: 'Asia/Tokyo' }),
    )
    return ['日', '月', '火', '水', '木', '金', '土'][d.getDay()]
  } catch {
    return ''
  }
}

// 是否为周末（JST）
const isWeekend = (date: string) => {
  try {
    const d = new Date(
      new Date(date + 'T00:00:00').toLocaleString('en-US', { timeZone: 'Asia/Tokyo' }),
    )
    const day = d.getDay()
    return day === 0 || day === 6
  } catch {
    return false
  }
}

// 是否为今天（JST）
const isToday = (date: string) => {
  try {
    const today = JapanDateUtils.getTodayString()
    const normalizedDate = JapanDateUtils.normalizeDate(date)
    return normalizedDate === today
  } catch {
    return false
  }
}

// 数字格式化（千位分隔）
const formatQty = (val: number | string) => {
  const n = typeof val === 'string' ? Number(val) : val
  if (!isFinite(n as number)) return ''
  return (n as number).toLocaleString('ja-JP')
}

// 数字格式化（简化版）
const formatNumber = (val: number | string) => {
  const n = typeof val === 'string' ? Number(val) : val
  if (!isFinite(n as number)) return '0'
  return (n as number).toLocaleString('ja-JP')
}

const formatPrintableNumber = (
  val: number | string,
  options: { suffix?: string; minimumFractionDigits?: number; maximumFractionDigits?: number } = {},
) => {
  if (val === null || val === undefined || val === '') return ''
  const num = typeof val === 'string' ? Number(val) : val
  if (typeof num !== 'number' || !isFinite(num)) {
    return `${val ?? ''}${options.suffix ?? ''}`
  }

  const hasFraction =
    options.minimumFractionDigits !== undefined || options.maximumFractionDigits !== undefined

  const formatted = num.toLocaleString('ja-JP', {
    minimumFractionDigits: hasFraction ? (options.minimumFractionDigits ?? 0) : undefined,
    maximumFractionDigits: hasFraction
      ? (options.maximumFractionDigits ?? options.minimumFractionDigits ?? 0)
      : undefined,
  })

  const content = `${formatted}${options.suffix ?? ''}`

  if (num < 0) {
    return `<span class="negative-number">${content}</span>`
  }
  return content
}

const formatPlanComparisonValue = (
  val: number | string | null | undefined,
  options: { suffix?: string; minimumFractionDigits?: number; maximumFractionDigits?: number } = {},
) => {
  if (val === null || val === undefined || val === '') {
    return '-'
  }
  return formatPrintableNumber(val as number | string, options)
}

// 日期格式化（MM-DD）
const formatMatrixDate = (dateStr: string) => {
  try {
    const date = new Date(dateStr + 'T00:00:00')
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${month}-${day}`
  } catch {
    return dateStr
  }
}

// 根据设备名称生成颜色
const getMachineColor = (machineName: string) => {
  if (!machineName) return '#64748b'

  // 预定义的颜色数组，使用现代化的颜色
  const colors = [
    '#3b82f6', // 蓝色
    '#ef4444', // 红色
    '#10b981', // 绿色
    '#f59e0b', // 橙色
    '#8b5cf6', // 紫色
    '#06b6d4', // 青色
    '#f97316', // 深橙色
    '#84cc16', // 青绿色
    '#ec4899', // 粉色
    '#6366f1', // 靛蓝色
    '#14b8a6', // 蓝绿色
    '#eab308', // 黄色
  ]

  // 使用设备名称的哈希值来选择颜色，确保相同设备总是相同颜色
  let hash = 0
  for (let i = 0; i < machineName.length; i++) {
    hash = machineName.charCodeAt(i) + ((hash << 5) - hash)
  }
  const index = Math.abs(hash) % colors.length
  return colors[index]
}

// 切换设备展开/折叠状态
const toggleMachineCollapse = (machineName: string) => {
  if (collapsedMachines.value.has(machineName)) {
    collapsedMachines.value.delete(machineName)
  } else {
    collapsedMachines.value.add(machineName)
  }
}

// 检查设备是否折叠
const isMachineCollapsed = (machineName: string) => {
  return collapsedMachines.value.has(machineName)
}

// 鼠标悬停处理
const handleCellHover = (rowKey: string, date: string) => {
  hoveredRow.value = rowKey
  hoveredCol.value = date
}

const handleCellLeave = () => {
  hoveredRow.value = null
  hoveredCol.value = null
}

// Excel导出功能
const exportToExcel = () => {
  try {
    // 准备导出数据
    const exportData = []

    // 添加表头
    const headers = [
      '設備',
      '製品名',
      '生産順位',
      '生産数(合計)',
      ...matrixDates.value.map((date) => formatMatrixDate(date)),
    ]
    exportData.push(headers)

    // 添加数据行
    matrixRows.value.forEach((row) => {
      const rowData = [
        row.machine_name,
        row.product_name,
        row.operator || '',
        row.totalQty,
        ...matrixDates.value.map((date) => row.dateToQty[date] || ''),
      ]
      exportData.push(rowData)
    })

    // 添加合计行
    const totalRow = [
      '合計',
      '',
      '',
      matrixGrandTotal.value,
      ...matrixDates.value.map((date) => matrixColumnTotals.value[date] || 0),
    ]
    exportData.push(totalRow)

    // 转换为CSV格式
    const csvContent = exportData.map((row) => row.map((cell) => `"${cell}"`).join(',')).join('\n')

    // 创建下载链接
    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute(
      'download',
      `生産計画マトリックス_${new Date().toISOString().split('T')[0]}.csv`,
    )
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    ElMessage.success('Excelファイルをダウンロードしました')
  } catch (error) {
    console.error('Excel导出失败:', error)
    ElMessage.error('Excelエクスポートに失敗しました')
  }
}

// マトリックス打印功能
const printMatrix = () => {
  try {
    // 生成打印内容
    const printContent = generateMatrixPrintContent()

    // 创建打印窗口
    const printWindow = window.open('', '_blank')
    if (printWindow) {
      printWindow.document.write(printContent)
      printWindow.document.close()
      printWindow.focus()

      // 等待内容加载完成后打印
      printWindow.onload = () => {
        setTimeout(() => {
          printWindow.print()
          printWindow.close()
        }, 500)
      }
    }

    ElMessage.success('印刷を開始しました')
  } catch (error) {
    console.error('打印失败:', error)
    ElMessage.error('印刷に失敗しました')
  }
}

// 生成マトリックス打印内容
const generateMatrixPrintContent = () => {
  const currentDate = new Date().toLocaleDateString('ja-JP')
  const dateRange =
    matrixDateRange.value.length === 2
      ? `${formatMatrixDate(matrixDateRange.value[0])} 〜 ${formatMatrixDate(matrixDateRange.value[1])}`
      : '全期間'

  return `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>生産計画マトリックス</title>
      <style>
        @page {
          size: A3 landscape;
          margin: 10mm;
        }

        body {
          font-family: 'Yu Gothic', 'Hiragino Sans', sans-serif;
          font-size: 10px;
          line-height: 1.2;
          margin: 0;
          padding: 0;
          color: #000;
          -webkit-print-color-adjust: exact;
          print-color-adjust: exact;
        }

        .print-header {
          text-align: center;
          margin-bottom: 15px;
          border-bottom: 2px solid #000;
          padding-bottom: 10px;
        }

        .print-title {
          font-size: 18px;
          font-weight: bold;
          margin-bottom: 5px;
        }

        .print-info {
          font-size: 12px;
          color: #666;
        }

        .matrix-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 9px;
        }

        .matrix-table th,
        .matrix-table td {
          border: 1px solid #000;
          padding: 3px 4px;
          text-align: center;
          vertical-align: middle;
        }

        .matrix-table th {
          background-color: #f0f0f0;
          font-weight: bold;
          font-size: 8px;
        }

        .sticky-col {
          background-color: #f8f9fa;
          font-weight: bold;
        }

        .group-header {
          background-color: #e3f2fd;
          font-weight: bold;
        }

        .child-row {
          background-color: #fafafa;
        }

        .numeric-cell {
          text-align: right;
        }

        .machine-name {
          font-weight: bold;
        }

        .total-row {
          background-color: #fff3e0;
          font-weight: bold;
          border-top: 2px solid #000;
        }

        .print-footer {
          margin-top: 15px;
          text-align: right;
          font-size: 10px;
          color: #666;
        }
      </style>
    </head>
    <body>
      <div class="print-header">
        <div class="print-title">生産計画マトリックス</div>
        <div class="print-info">
          期間: ${dateRange} | 印刷日時: ${currentDate}
        </div>
      </div>

      <table class="matrix-table">
        <thead>
          <tr>
            <th class="sticky-col">設備</th>
            <th class="sticky-col">製品名</th>
            <th class="sticky-col">生産順位</th>
            <th class="sticky-col">生産数(合計)</th>
            ${matrixDates.value
              .map(
                (date) =>
                  `<th>${formatMatrixDate(date)}<br><small>${getWeekdayLabel(date)}</small></th>`,
              )
              .join('')}
          </tr>
        </thead>
        <tbody>
          ${visibleMatrixRows.value
            .map(
              (row) => `
            <tr class="${row.isGroupHeader ? 'group-header' : row.isChildRow ? 'child-row' : ''}">
              <td class="sticky-col">
                ${row.isGroupHeader ? '▼ ' : row.isChildRow ? '　' : ''}${row.machine_name}
              </td>
              <td class="sticky-col">${row.product_name}</td>
              <td class="sticky-col">${row.operator || ''}</td>
              <td class="sticky-col numeric-cell">${formatQty(row.totalQty)}</td>
              ${matrixDates.value
                .map(
                  (date) =>
                    `<td class="numeric-cell">${row.dateToQty[date] ? formatQty(row.dateToQty[date]) : ''}</td>`,
                )
                .join('')}
            </tr>
          `,
            )
            .join('')}
        </tbody>
        <tfoot>
          <tr class="total-row">
            <td class="sticky-col">合計</td>
            <td class="sticky-col"></td>
            <td class="sticky-col"></td>
            <td class="sticky-col numeric-cell">${formatQty(matrixGrandTotal.value)}</td>
            ${matrixDates.value
              .map(
                (date) =>
                  `<td class="numeric-cell">${formatQty(matrixColumnTotals.value[date] || 0)}</td>`,
              )
              .join('')}
          </tr>
        </tfoot>
      </table>

      <div class="print-footer">
        Smart-EMAP 生産管理システム
      </div>
    </body>
    </html>
  `
}

// 能率数据缓存（设备名+产品名 -> efficiency_rate）
const efficiencyCache = new Map<string, number>()

// 获取设备能率数据并建立缓存
const loadEfficiencyData = async () => {
  try {
    efficiencyCache.clear()

    const result = (await request.get('/api/master/equipment-efficiency', {
      params: { page: 1, limit: 10000 },
    })) as ApiResponse<{ list: any[] }>

    if (result.success && Array.isArray(result.data?.list)) {
      efficiencyCache.clear()
      result.data.list.forEach((item: any) => {
        if (item.machines_name && item.product_name) {
          const key = `${item.machines_name}|${item.product_name}`
          const efficiencyRate = parseFloat(item.efficiency_rate) || 0
          efficiencyCache.set(key, efficiencyRate)
        }
      })
      console.log('能率データの読み込み成功, 件数:', efficiencyCache.size)
    } else {
      console.warn('能率データの形式が不正:', result)
    }
  } catch (error) {
    console.error('能率データの読み込みに失敗:', error)
    efficiencyCache.clear()
  }
}

// 根据设备名和产品名获取能率
const getEfficiencyRate = (machineName: string, productName: string): number | null => {
  if (!machineName || !productName) return null
  const key = `${machineName}|${productName}`
  return efficiencyCache.has(key) ? efficiencyCache.get(key)! : null
}

type OperationVarianceRow = {
  machine_name: string
  operation_variance: number | null
}

const getOperationVarianceRows = async (): Promise<OperationVarianceRow[]> => {
  try {
    const productionDate =
      (planSearchForm.dateRange && planSearchForm.dateRange[0]) || JapanDateUtils.getTodayString()

    // 同时准备不带前导零和带前导零的月份，避免 1 / 01 差异导致的匹配问题
    let monthNoPad = ''
    let monthPadded = ''
    if (productionDate) {
      try {
        const dateObj = new Date(productionDate + 'T00:00:00')
        if (!isNaN(dateObj.getTime())) {
          const monthNum = dateObj.getMonth() + 1
          monthNoPad = String(monthNum)
          monthPadded = String(monthNum).padStart(2, '0')
        }
      } catch (error) {
        console.warn('生产日解析失败，无法提取月份用于操業度差異查询:', error)
      }
    }

    const fetchVariance = async (fileMonth?: string) => {
      const params: Record<string, string> = {}
      if (fileMonth) params.fileName = `${fileMonth}月`
      return await request.get('/api/operation-rate', { params })
    }

    const parseRows = (res: any): any[] => {
      if (Array.isArray(res)) return res
      if (Array.isArray(res?.data)) return res.data
      if (Array.isArray(res?.data?.data)) return res.data.data
      return []
    }

    // 第一次尝试：不带前导零的月份（如 1）
    let res = await fetchVariance(monthNoPad || undefined)
    let rowsData = parseRows(res)

    // 如果没有数据，再用带前导零的月份（如 01）重试
    if ((!rowsData || rowsData.length === 0) && monthPadded && monthPadded !== monthNoPad) {
      console.log('操業度差異数据为空，使用前导零月份重试:', monthPadded)
      res = await fetchVariance(monthPadded)
      rowsData = parseRows(res)
    }

    console.log('操業度差異 raw response:', res)
    console.log('操業度差異 rowsData length:', rowsData.length)

    const rows = rowsData
      .filter((item) => item && item.machine_name)
      .map((item) => ({
        machine_name: item.machine_name,
        operation_variance:
          item.operation_variance === null || item.operation_variance === undefined
            ? null
            : Number(item.operation_variance),
      }))
      .filter((row) => row.machine_name.includes('溶接'))
      .sort((a, b) => a.machine_name.localeCompare(b.machine_name, 'ja'))
    console.log('操業度差異 rows after filtering:', rows)
    return rows
  } catch (error) {
    console.error('操業度データ取得失敗:', error)
    return []
  }
}

// ========================================
// 段取予定表印刷関連ユーティリティ
// ========================================

// 日期工具类（日本时区）
class JapanDateUtils {
  static normalizeDate(dateStr: string): string {
    return dateStr.split(' ')[0].split('T')[0]
  }

  static getDateParts(dateInput?: string | Date) {
    const date = dateInput
      ? typeof dateInput === 'string'
        ? new Date(dateInput)
        : dateInput
      : new Date()
    const formatter = new Intl.DateTimeFormat('ja-JP', {
      timeZone: 'Asia/Tokyo',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    })
    const parts = formatter.formatToParts(date)
    return {
      year: parts.find((p) => p.type === 'year')?.value || '',
      month: parts.find((p) => p.type === 'month')?.value || '',
      day: parts.find((p) => p.type === 'day')?.value || '',
    }
  }

  static getDateString(dateInput?: string | Date): string {
    const parts = this.getDateParts(dateInput)
    return `${parts.year}-${parts.month}-${parts.day}`
  }

  private static dayOfWeekCache = new Map<string, number>()
  static getDayOfWeek(dateInput: string | Date): number {
    const dateStr =
      typeof dateInput === 'string' ? this.normalizeDate(dateInput) : this.getDateString(dateInput)

    if (this.dayOfWeekCache.has(dateStr)) {
      return this.dayOfWeekCache.get(dateStr)!
    }

    const date = typeof dateInput === 'string' ? new Date(dateInput) : dateInput
    const formatter = new Intl.DateTimeFormat('en-US', {
      timeZone: 'Asia/Tokyo',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    })
    const formattedStr = formatter.format(date)
    const [month, day, year] = formattedStr.split('/')
    const japanDate = new Date(parseInt(year), parseInt(month) - 1, parseInt(day))
    const dayOfWeek = japanDate.getDay()

    this.dayOfWeekCache.set(dateStr, dayOfWeek)
    return dayOfWeek
  }

  static isSunday(dateInput: string | Date): boolean {
    return this.getDayOfWeek(dateInput) === 0
  }

  static isSaturday(dateInput: string | Date): boolean {
    return this.getDayOfWeek(dateInput) === 6
  }

  static getNextMonday(dateStr: string): string {
    const [year, month, day] = dateStr.split('-').map(Number)
    const date = new Date(year, month - 1, day)
    date.setDate(date.getDate() + 2)
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
  }

  static getCurrentDate(): Date {
    const now = new Date()
    const formatter = new Intl.DateTimeFormat('en-US', {
      timeZone: 'Asia/Tokyo',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    })
    const formattedStr = formatter.format(now)
    const [datePart, timePart] = formattedStr.split(', ')
    const [month, day, year] = datePart.split('/')
    const [hour, minute, second] = timePart.split(':')
    return new Date(
      parseInt(year),
      parseInt(month) - 1,
      parseInt(day),
      parseInt(hour),
      parseInt(minute),
      parseInt(second),
    )
  }

  static getTodayString(): string {
    return this.getDateString()
  }

  static getCurrentDateTime(): string {
    const now = new Date()
    const formatter = new Intl.DateTimeFormat('ja-JP', {
      timeZone: 'Asia/Tokyo',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    })
    const parts = formatter.formatToParts(now)
    const year = parts.find((p) => p.type === 'year')?.value || ''
    const month = parts.find((p) => p.type === 'month')?.value || ''
    const day = parts.find((p) => p.type === 'day')?.value || ''
    const hour = parts.find((p) => p.type === 'hour')?.value || ''
    const minute = parts.find((p) => p.type === 'minute')?.value || ''
    const second = parts.find((p) => p.type === 'second')?.value || ''
    return `${year}年${month}月${day}日 ${hour}:${minute}:${second}`
  }

  static formatDate(dateStr: string, separator: string = '/'): string {
    const parts = this.getDateParts(dateStr)
    return `${parts.year}${separator}${parts.month}${separator}${parts.day}`
  }
}

// 产品排序工具类
class ProductSortUtils {
  private static normalizeOperator(operator: any): string {
    return (operator || '').toString().trim()
  }

  private static compareOperators(operatorA: string, operatorB: string): number {
    if (operatorA === '' && operatorB === '') return 0
    if (operatorA === '') return 1
    if (operatorB === '') return -1

    const numA = Number(operatorA)
    const numB = Number(operatorB)

    if (!isNaN(numA) && !isNaN(numB)) {
      return numA - numB
    }

    return operatorA.localeCompare(operatorB, 'ja')
  }

  static sortByOperator(products: any[]): any[] {
    return [...products].sort((a, b) => {
      const operatorA = this.normalizeOperator(a.operator)
      const operatorB = this.normalizeOperator(b.operator)
      return this.compareOperators(operatorA, operatorB)
    })
  }
}

// 数据索引工具类
class DataIndexUtils {
  static buildDateIndex(data: any[]): Map<string, any[]> {
    const index = new Map<string, any[]>()

    data.forEach((item) => {
      const date = JapanDateUtils.normalizeDate(item.plan_date || '')
      if (!index.has(date)) {
        index.set(date, [])
      }
      index.get(date)!.push(item)
    })

    index.forEach((products, date) => {
      const validProducts = products.filter((p) => parseInt(p.quantity) > 0)
      if (validProducts.length > 0) {
        index.set(date, ProductSortUtils.sortByOperator(validProducts))
      }
    })

    return index
  }

  static findValidProducts(dateIndex: Map<string, any[]>, date: string): any[] {
    const products = dateIndex.get(date) || []
    const dayOfWeek = JapanDateUtils.getDayOfWeek(date)
    if (dayOfWeek === 0) return []
    return products.filter((p) => parseInt(p.quantity) > 0)
  }

  static findValidDatesAfter(
    dateIndex: Map<string, any[]>,
    startDate: string,
    excludeStartDate: boolean = false,
  ): string[] {
    const dates = Array.from(dateIndex.keys())
      .filter((date) => {
        if (excludeStartDate) {
          return date > startDate
        } else {
          return date >= startDate
        }
      })
      .filter((date) => {
        const dayOfWeek = JapanDateUtils.getDayOfWeek(date)
        return dayOfWeek !== 0 && dayOfWeek !== 6
      })
      .sort()
    return dates
  }
}

// 生成段取予定表打印内容
const generateSetupScheduleContent = async (planData: any[]) => {
  const currentDateTime = JapanDateUtils.getCurrentDateTime()

  let productionDate = ''
  if (planSearchForm.dateRange && planSearchForm.dateRange.length >= 1) {
    productionDate = JapanDateUtils.formatDate(planSearchForm.dateRange[0])
  } else {
    productionDate = JapanDateUtils.formatDate(JapanDateUtils.getTodayString())
  }

  const groupedByMachine = groupDataByMachine(planData)
  const machines = Object.keys(groupedByMachine).sort()

  if (efficiencyCache.size === 0) {
    await loadEfficiencyData()
  }

  // 从生产日期提取月份（例如：2025/11/10 → 11，2026/01/05 → 1）
  // 文件名格式为：加工計画(1月).xlsm，所以需要转换为不带前导零的数字
  let monthFilter = ''
  if (productionDate) {
    const dateParts = productionDate.split('/')
    if (dateParts.length >= 2) {
      const monthNum = parseInt(dateParts[1], 10) // 转换为数字，去掉前导零（例如：01 → 1）
      monthFilter = `${monthNum}月` // 格式化为"1月"、"2月"等格式，匹配文件名
    }
  }

  let productionPlanSchedulesData: any[] = []
  if (monthFilter) {
    try {
      const result = (await request.get('/api/processing-status', {
        params: { fileName: monthFilter, limit: 100000 },
      })) as ApiResponse<any[]>

      if (result.success && result.data) {
        productionPlanSchedulesData = result.data
      }
    } catch (error) {
      console.error('production_plan_schedules データの読み込みに失敗:', error)
    }
  }

  // 创建一个映射表，以便快速查找：key 为 machine_name + product_name + production_order
  const productionPlanSchedulesMap = new Map<string, any>()
  productionPlanSchedulesData.forEach((item) => {
    // 将 production_order 转换为字符串（确保一致性）
    const productionOrder = (item.production_order || '').toString().trim()
    const key = `${item.machine_name}|${item.product_name}|${productionOrder}`
    // 如果同一个 machine_name + product_name + production_order 有多条记录，累加数量
    if (productionPlanSchedulesMap.has(key)) {
      const existing = productionPlanSchedulesMap.get(key)
      existing.planned_quantity =
        (parseInt(existing.planned_quantity) || 0) + (parseInt(item.planned_quantity) || 0)
      existing.actual_production =
        (parseInt(existing.actual_production) || 0) + (parseInt(item.actual_production) || 0)
    } else {
      productionPlanSchedulesMap.set(key, {
        planned_quantity: parseInt(item.planned_quantity) || 0,
        actual_production: parseInt(item.actual_production) || 0,
        production_order: productionOrder,
      })
    }
  })

  const filterDateForTotal = productionDate.replace(/\//g, '-')

  const totalQuantity = planData.reduce((sum, item) => {
    const itemDate = item.plan_date || ''
    if (itemDate) {
      const normalizedItemDate = JapanDateUtils.normalizeDate(itemDate)
      if (normalizedItemDate === filterDateForTotal) {
        const quantity = parseInt(item.quantity) || 0
        return sum + quantity
      }
    }
    return sum
  }, 0)

  const operationVarianceRows = await getOperationVarianceRows()
  console.log('操業度差異 rows used for段取予定表:', operationVarianceRows.length)

  const baselineMonthForSummary = getBaselineMonthFromDate(planSearchForm.dateRange?.[0])
  const planComparisonSummaryForPrint =
    (await loadWeldingPlanComparisonSummary({
      silent: true,
      baselineMonth: baselineMonthForSummary || undefined,
      workingDays: specifiedWorkingDays.value,
    })) ||
    weldingPlanComparisonSummary.value ||
    createEmptyPlanComparisonSummary()

  const tableRowsPromises = machines.map(async (machineName) => {
    const machineData = groupedByMachine[machineName]
    const filterDate = filterDateForTotal
    const dateIndex = DataIndexUtils.buildDateIndex(machineData)
    const currentProducts = DataIndexUtils.findValidProducts(dateIndex, filterDate)
    const currentProduct = currentProducts.length > 0 ? currentProducts[0] : {}
    const machineCdFromData = (currentProduct as any)?.machine_cd || ''

    let currentQuantity = 0
    if (currentProduct && (currentProduct as any).plan_date) {
      const normalizedCurrentDate = JapanDateUtils.normalizeDate((currentProduct as any).plan_date)
      if (normalizedCurrentDate === filterDate) {
        currentQuantity = parseInt((currentProduct as any).quantity) || 0
      }
    }

    const workTime =
      currentQuantity > 0 ? Math.min(24, Math.max(1, Math.floor(currentQuantity / 200) || 1)) : 0

    const isProductionStop =
      !(currentProduct as any).plan_date ||
      currentQuantity === 0 ||
      !(currentProduct as any).product_name

    const currentProductName = isProductionStop ? '' : (currentProduct as any).product_name || ''
    let efficiency = ''
    let efficiencyRateNum: number | null = null

    if (currentProductName && !isProductionStop) {
      const efficiencyRate = (currentProduct as any).efficiency_rate
      if (
        efficiencyRate !== null &&
        efficiencyRate !== undefined &&
        efficiencyRate !== '' &&
        parseFloat(efficiencyRate) > 0
      ) {
        efficiencyRateNum = parseFloat(efficiencyRate)
        efficiency = formatEfficiencyRate(efficiencyRate)
      } else {
        const cachedEfficiencyRate = getEfficiencyRate(machineName, currentProductName)
        if (cachedEfficiencyRate !== null && cachedEfficiencyRate > 0) {
          efficiencyRateNum = cachedEfficiencyRate
          efficiency = formatEfficiencyRate(cachedEfficiencyRate)
        } else {
          if (currentQuantity > 0 && workTime > 0) {
            const hourlyRate = Math.round(currentQuantity / workTime)
            if (hourlyRate > 0) {
              efficiencyRateNum = hourlyRate
              efficiency = `${hourlyRate}本/h`
            }
          } else if (currentQuantity > 0) {
            const standardHourlyRate = Math.round(currentQuantity / 8)
            if (standardHourlyRate > 0) {
              efficiencyRateNum = standardHourlyRate
              efficiency = `${standardHourlyRate}本/h`
            }
          }
        }
      }
    }

    if (!efficiencyRateNum || efficiencyRateNum <= 0) {
      efficiencyRateNum = 100
      efficiency = formatEfficiencyRate(100)
    }

    const startTime = '15:00'

    let nextProduct = null
    let nextValidDate = ''

    const findNextProduct = (): { product: any | null; date: string } => {
      const sameDayProducts = currentProducts
      if (sameDayProducts.length > 1 && Object.keys(currentProduct).length > 0) {
        const currentProductIndex = sameDayProducts.findIndex((item: any) => {
          const itemProductName = item.product_name || ''
          const itemOperator = (item.operator || '').toString().trim()
          const currentProductName = (currentProduct as any).product_name || ''
          const currentOperator = ((currentProduct as any).operator || '').toString().trim()
          return itemProductName === currentProductName && itemOperator === currentOperator
        })

        if (currentProductIndex >= 0 && currentProductIndex < sameDayProducts.length - 1) {
          return { product: sameDayProducts[currentProductIndex + 1], date: filterDate }
        }
      }

      const nextDate = new Date(filterDate)
      nextDate.setDate(nextDate.getDate() + 1)
      const nextDateStr = nextDate.toISOString().split('T')[0]
      const nextDayOfWeek = nextDate.getDay()

      if (nextDayOfWeek === 6) {
        const saturdayProducts = DataIndexUtils.findValidProducts(dateIndex, nextDateStr)
        if (saturdayProducts.length > 0) {
          return { product: saturdayProducts[0], date: nextDateStr }
        }

        const mondayDate = new Date(nextDateStr)
        mondayDate.setDate(mondayDate.getDate() + 2)
        const mondayDateStr = mondayDate.toISOString().split('T')[0]

        const mondayProducts = DataIndexUtils.findValidProducts(dateIndex, mondayDateStr)
        if (mondayProducts.length > 0) {
          return { product: mondayProducts[0], date: mondayDateStr }
        }
      } else if (nextDayOfWeek === 0) {
        const mondayDate = new Date(nextDateStr)
        mondayDate.setDate(mondayDate.getDate() + 1)
        const mondayDateStr = mondayDate.toISOString().split('T')[0]

        const mondayProducts = DataIndexUtils.findValidProducts(dateIndex, mondayDateStr)
        if (mondayProducts.length > 0) {
          return { product: mondayProducts[0], date: mondayDateStr }
        }
      } else {
        const nextDayProducts = DataIndexUtils.findValidProducts(dateIndex, nextDateStr)
        if (nextDayProducts.length > 0) {
          return { product: nextDayProducts[0], date: nextDateStr }
        }
      }

      return { product: null, date: '' }
    }

    const nextProductResult = findNextProduct()
    nextProduct = nextProductResult.product
    nextValidDate = nextProductResult.date

    const nextProductName = nextProduct ? (nextProduct as any).product_name || '' : ''
    const nextQuantity = nextProduct ? parseInt((nextProduct as any).quantity) || 0 : 0

    const currentMachineCd = machineCdFromData || ''

    const isSameProduct =
      currentProductName && nextProductName && currentProductName.trim() === nextProductName.trim()

    let isNextDateWeekend = false
    let isNextDateSunday = false
    let nextProductDateStr = ''
    if (nextProduct && (nextProduct as any).plan_date) {
      nextProductDateStr = JapanDateUtils.normalizeDate((nextProduct as any).plan_date)
      if (nextProductDateStr) {
        isNextDateWeekend =
          JapanDateUtils.isSunday(nextProductDateStr) ||
          JapanDateUtils.isSaturday(nextProductDateStr)
        isNextDateSunday = JapanDateUtils.isSunday(nextProductDateStr)
      }
    } else if (nextValidDate) {
      nextProductDateStr = nextValidDate
      isNextDateWeekend =
        JapanDateUtils.isSunday(nextValidDate) || JapanDateUtils.isSaturday(nextValidDate)
      isNextDateSunday = JapanDateUtils.isSunday(nextValidDate)
    }

    let finalNextProductName = ''
    if (isSameProduct || isNextDateSunday) {
      finalNextProductName = ''
    } else if (isNextDateWeekend) {
      if (nextProductName && nextProductName.trim() !== '') {
        finalNextProductName = nextProductName
      } else {
        finalNextProductName = '生产停止'
      }
    } else if (!nextProductName || nextProductName.trim() === '') {
      finalNextProductName = '生产停止'
    } else {
      finalNextProductName = nextProductName
    }

    let finalNextQuantity: number | '' = ''
    if (isSameProduct || isNextDateSunday) {
      finalNextQuantity = ''
    } else if (nextProduct && (nextProduct as any).plan_date) {
      const nextProductPlanDate = JapanDateUtils.normalizeDate((nextProduct as any).plan_date)
      if (nextProductPlanDate === filterDate) {
        finalNextQuantity = nextQuantity || ''
      } else {
        finalNextQuantity = ''
      }
    } else if (nextValidDate && nextValidDate === filterDate) {
      finalNextQuantity = nextQuantity || ''
    } else {
      finalNextQuantity = ''
    }

    // 総計画数、実績、生産残数の取得
    // production_plan_schedules 表から取得（machine_name + product_name + production_order で連接）
    // 条件：生産品種对应的順位（operator转换为数字）= production_order
    let totalPlanQuantity = 0
    let actualProduction = 0
    let remainingProduction = 0

    if (!isProductionStop && currentProductName) {
      // 获取当前产品的順位（operator）
      const currentOperator = ((currentProduct as any)?.operator || '').toString().trim()

      // 将順位转换为数字（如果operator是数字字符串，直接转换；如果不是，尝试提取数字部分）
      let operatorAsNumber = ''
      if (currentOperator) {
        // 尝试直接转换为数字
        const numValue = Number(currentOperator)
        if (!isNaN(numValue) && isFinite(numValue)) {
          operatorAsNumber = numValue.toString()
        } else {
          // 如果不是纯数字，尝试提取数字部分
          const numMatch = currentOperator.match(/\d+/)
          if (numMatch) {
            operatorAsNumber = numMatch[0]
          }
        }
      }

      // 构建查找key：machine_name + product_name + production_order（production_order需要等于operator转换后的数字）
      const scheduleKey = `${machineName}|${currentProductName}|${operatorAsNumber}`
      const scheduleData = productionPlanSchedulesMap.get(scheduleKey)

      if (scheduleData) {
        totalPlanQuantity = scheduleData.planned_quantity || 0
        actualProduction = scheduleData.actual_production || 0
        remainingProduction = Math.max(0, totalPlanQuantity - actualProduction)
        console.log(
          `[生産計画数] 设备: ${machineName}, 产品: ${currentProductName}, 順位: ${currentOperator} (转换为数字: ${operatorAsNumber}), 総計画数: ${totalPlanQuantity}, 実績: ${actualProduction}, 生産残数: ${remainingProduction}`,
        )
      } else {
        console.log(
          `[生産計画数] 未找到匹配数据，设备: ${machineName}, 产品: ${currentProductName}, 順位: ${currentOperator} (转换为数字: ${operatorAsNumber}), 查找key: ${scheduleKey}`,
        )
      }
    }

    const requiredProductionTime =
      !isProductionStop && efficiencyRateNum && efficiencyRateNum > 0 && currentQuantity > 0
        ? (currentQuantity / efficiencyRateNum).toFixed(1)
        : ''

    let requiredStaffCount = 0
    let remarksText = ''
    if (requiredProductionTime) {
      const requiredHours = parseFloat(requiredProductionTime)
      if (!isNaN(requiredHours)) {
        if (requiredHours < 8) {
          remarksText = '一人体制'
          requiredStaffCount = 1
        } else if (requiredHours >= 8 && requiredHours <= 10) {
          remarksText = '一人残業体制'
          requiredStaffCount = 1
        } else if (requiredHours > 10) {
          remarksText = '二人体制'
          requiredStaffCount = 2
        }
      }
    }
    if (!remarksText && currentProducts.length >= 3) {
      const thirdProduct = currentProducts[2]
      const thirdProductName = (thirdProduct as any)?.product_name || ''
      if (thirdProductName && thirdProductName.trim() !== '') {
        remarksText = `次生産品種：${thirdProductName}`
      }
    }

    return {
      workTime: workTime || '',
      machineCd: currentMachineCd,
      line: machineName,
      startTime,
      productName: isProductionStop ? '生産停止' : currentProductName,
      totalPlanQuantity: isProductionStop ? '' : totalPlanQuantity,
      actualProduction: isProductionStop ? '' : actualProduction,
      remainingProduction: isProductionStop ? '' : remainingProduction,
      efficiency: isProductionStop ? '' : efficiency,
      planQuantity: isProductionStop ? '' : currentQuantity,
      requiredProductionTime,
      requiredStaffCount,
      nextProductName: finalNextProductName,
      nextQuantity: finalNextQuantity,
      remarks: remarksText,
    }
  })

  const tableRows = await Promise.all(tableRowsPromises)
  const totalRequiredStaff = tableRows.reduce((sum, row) => sum + (row.requiredStaffCount || 0), 0)

  return `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>溶接工程段取予定表</title>
      <style>
        @page {
          size: A4 landscape;
          margin: 12mm 12mm 8mm 12mm;
          marks: none;
          bleed: 0mm;
          page-break-after: auto;
        }

        @media print {
          @page {
            size: A4 landscape;
            margin: 12mm 12mm 8mm 12mm;
            marks: none;
            bleed: 0mm;
          }
          * {
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
          }
        }

        body {
          font-family: 'Yu Gothic', 'Hiragino Sans', sans-serif;
          font-size: 11px;
          line-height: 1.1;
          margin: 0;
          padding: 0;
          color: #000;
          -webkit-print-color-adjust: exact;
          print-color-adjust: exact;
        }

        .print-container {
          width: 100%;
          height: 100%;
          position: relative;
          min-height: 100vh;
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .table-wrapper {
          flex: 0 0 40%;
          min-height: 0;
          overflow: hidden;
          display: flex;
          flex-direction: column;
        }

        .lower-section {
          flex: 0 0 60%;
          min-height: 0;
          display: flex;
          gap: 6px;
          margin-top: 12px;
        }

        .panel {
          border: 2px solid #000;
          border-radius: 4px;
          padding: 6px;
          display: flex;
          flex-direction: column;
          background: #fff;
        }

        .panel-title {
          font-size: 12px;
          font-weight: bold;
          margin-bottom: 6px;
          text-align: left;
        }

        .bottom-left {
          flex: 4;
        }

        .bottom-right {
          flex: 6;
        }

        .note-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 11px;
        }

        .note-table th,
        .note-table td {
          border: 1px solid #000;
          padding: 6px;
          text-align: left;
          height: auto;
          line-height: 1.2;
        }

        .variance-table {
          font-size: 13px;
        }

        .variance-table th,
        .variance-table td {
          text-align: center;
        }

        .no-data-cell.small {
          font-size: 12px;
          height: 60px;
        }

        .memo-placeholder {
          flex: 1;
          border: 1px solid #000;
          padding: 12px;
          background: #f8fafc;
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .memo-grid {
          display: flex;
          gap: 6px;
          margin-bottom: 4px;
        }

        .memo-column {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .memo-block {
          border: 1px solid #000;
          padding: 7px 8px;
          background: #f3f4f6;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .memo-label {
          font-size: 12px;
          font-weight: 600;
        }

        .memo-value {
          font-size: 12px;
          font-weight: 700;
        }

        .memo-ratios {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .memo-ratio {
          display: flex;
          justify-content: space-between;
          align-items: center;
          border: 1px solid #000;
          padding: 7px 8px;
          background: #fff;
        }

        .memo-ratio-label {
          font-size: 12px;
          font-weight: 600;
        }

        .memo-ratio-value {
          font-size: 12px;
          font-weight: 700;
        }

        .negative-number {
          color: #c0392b;
          font-weight: 700;
        }

        .positive-difference {
          color: #27ae60;
          font-weight: 700;
        }

        .negative-difference {
          color: #e74c3c;
          font-weight: 700;
        }

        .print-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 4px;
          padding-bottom: 2px;
          position: relative;
        }

        .header-left {
          flex: 1;
          text-align: left;
        }

        .print-title {
          font-size: 16px;
          font-weight: bold;
          color: #000;
          line-height: 1.1;
        }

        .print-center-section {
          position: absolute;
          left: 50%;
          transform: translateX(-50%);
          text-align: center;
        }

        .print-production-date-wrapper {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 1px;
        }

        .print-production-date {
          font-size: 16px;
          font-weight: bold;
          color: #000;
          line-height: 1.1;
        }

        .print-aggregation-time {
          font-size: 9px;
          color: #000;
          line-height: 1.1;
        }

        .header-right {
          text-align: right;
          flex: 1;
        }

        .print-date-time {
          font-size: 9px;
          color: #000;
          margin-bottom: 2px;
        }

        .print-total {
          font-size: 14px;
          font-weight: bold;
          color: #000;
        }

        .print-footer {
          position: fixed;
          bottom: 2mm;
          left: 8mm;
          right: 8mm;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .print-footer-left {
          font-size: 9px;
          color: #000;
          text-align: left;
        }

        .print-footer-right {
          font-size: 9px;
          color: #000;
          text-align: right;
        }

        .main-table {
          width: 100%;
          border-collapse: collapse;
          border: 2px solid #000;
          font-size: 13px;
        }

        .main-table th,
        .main-table td {
          border: 1px solid #000;
          padding: 4px 4px;
          text-align: center;
          vertical-align: middle;
          color: #000 !important;
          font-size: 13px;
        }

        /* 表内数据行高更紧凑 */
        .main-table tbody tr,
        .main-table tbody tr td {
          height: 32px;
        }

        .main-table thead tr:first-child th {
          border-top: 2px solid #000 !important;
        }

        .main-table thead tr th:first-child {
          border-left: 2px solid #000 !important;
        }
      </style>
    </head>
    <body>
      <div class="print-container">
        <div class="print-header">
          <div class="header-left">
            <div class="print-title">溶接生産計画段取予定表</div>
          </div>
          <div class="print-center-section">
            <div class="print-production-date-wrapper">
              <div class="print-production-date">生産日: ${productionDate}</div>
            </div>
          </div>
          <div class="header-right">
            <div class="print-total">
              生産計画合計数 ${totalQuantity.toLocaleString('ja-JP')} ／ 必要人員合計(参考)
              ${totalRequiredStaff}人
            </div>
          </div>
        </div>

        <div class="table-wrapper">
        <table class="main-table">
          <thead>
              <tr>
                <th
                  colspan="3"
                  style="width: 20%; border: 2px solid #000; border-bottom: none;"
                >
                  ${planComparisonSummaryForPrint.lastActualDate || currentDateTime.split(' ')[0]}まで実績(参考)
                </th>
                <th rowspan="2" style="width: 1%; border: none;"></th>
                <th rowspan="2" style="width: 7%; border-left: 2px solid #000;">ライン</th>
              <th rowspan="2" style="width: 10%;">生産品種</th>
              <th rowspan="2" style="width: 6%;">能率</th>
              <th rowspan="2" style="width: 7%;">当日計画数</th>
              <th rowspan="2" style="width: 10%;">所要生産時間(h)</th>
              <th rowspan="2" style="width: 10%;">次生産品種</th>
              <th rowspan="2" style="width: 11%;">次生産品種計画数</th>
              <th rowspan="2" style="width: 9%;">備考(参考)</th>
            </tr>
            <tr>
                <th style="width: 6%;">総計画数</th>
                <th style="width: 5%;">実績</th>
                <th style="width: 6%; border-right: 2px solid #000;">生産残数</th>
            </tr>
          </thead>
          <tbody>
            ${tableRows
              .map((row) => {
                return `
              <tr>
                <td class="numeric-cell">${formatPrintableNumber(row.totalPlanQuantity)}</td>
                <td class="numeric-cell">${formatPrintableNumber(row.actualProduction)}</td>
                <td class="numeric-cell" style="border-right: 2px solid #000;">${formatPrintableNumber(row.remainingProduction)}</td>
                <td style="border: none;"></td>
                <td style="border-left: 2px solid #000;">${row.line}</td>
                <td>${row.productName}</td>
                <td class="numeric-cell">${row.efficiency || ''}</td>
                <td class="numeric-cell">${formatPrintableNumber(row.planQuantity)}</td>
                <td class="numeric-cell">${formatPrintableNumber(row.requiredProductionTime, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}</td>
                <td>${row.nextProductName || ''}</td>
                <td class="numeric-cell">${formatPrintableNumber(row.nextQuantity)}</td>
                <td>${row.remarks || ''}</td>
              </tr>
            `
              })
              .join('')}
          </tbody>
        </table>
        </div>

        <div class="lower-section">
          <div class="bottom-left panel">
            <div class="panel-title">操業度差異（溶接設備）</div>
            <table class="note-table variance-table">
              <thead>
                <tr>
                  <th>設備名</th>
                  <th>操業度差異</th>
                </tr>
              </thead>
              <tbody>
                ${
                  operationVarianceRows.length === 0
                    ? `
                      <tr>
                        <td colspan="2" class="no-data-cell small">データなし</td>
                      </tr>
                    `
                    : operationVarianceRows
                        .map(
                          (row) => `
                      <tr>
                        <td>${row.machine_name || ''}</td>
                        <td>${formatPrintableNumber(row.operation_variance ?? '')}</td>
                      </tr>
                    `,
                        )
                        .join('')
                }
              </tbody>
            </table>
          </div>
          <div class="bottom-right panel">
            <div class="panel-title">生産計画と実績比較${
              planComparisonSummaryForPrint.lastActualDate
                ? `（実績データ: ${planComparisonSummaryForPrint.lastActualDate}まで）`
                : ''
            }</div>
            <div class="memo-grid">
              <div class="memo-column">
                <div class="memo-block">
                  <div class="memo-label">基準計画合計:</div>
                  <div class="memo-value">${formatPlanComparisonValue(
                    planComparisonSummaryForPrint.baselinePlanTotal,
                    { suffix: ' 本' },
                  )}</div>
                </div>
                <div class="memo-block">
                  <div class="memo-label">現行計画合計:</div>
                  <div class="memo-value">${formatPlanComparisonValue(
                    planComparisonSummaryForPrint.currentPlanTotal,
                    { suffix: ' 本' },
                  )}</div>
                </div>
                <div class="memo-block">
                  <div class="memo-label">計画差異:</div>
                  <div class="memo-value">${formatPlanComparisonValue(
                    planComparisonSummaryForPrint.planDifference,
                    { suffix: ' 本' },
                  )}</div>
                </div>
              </div>
              <div class="memo-column">
                <div class="memo-block">
                  <div class="memo-label">基準日平均生産数:</div>
                  <div class="memo-value">${formatPlanComparisonValue(
                    planComparisonSummaryForPrint.baselineDailyAverage,
                    { suffix: '本/日', minimumFractionDigits: 0, maximumFractionDigits: 0 },
                  )}</div>
                </div>
                <div class="memo-block">
                  <div class="memo-label">現行実績合計:</div>
                  <div class="memo-value">${formatPlanComparisonValue(
                    planComparisonSummaryForPrint.currentActualTotal,
                    { suffix: ' 本' },
                  )}</div>
                </div>
                <div class="memo-block">
                  <div class="memo-label">計画対実績差:</div>
                  <div class="memo-value ${
                    planComparisonSummaryForPrint.actualDifference !== null &&
                    planComparisonSummaryForPrint.actualDifference !== undefined
                      ? planComparisonSummaryForPrint.actualDifference >= 0
                        ? 'positive-difference'
                        : 'negative-difference'
                      : ''
                  }">${formatPlanComparisonValue(planComparisonSummaryForPrint.actualDifference, {
                    suffix: ' 本',
                  })}</div>
                </div>
              </div>
            </div>
            <div class="memo-ratios">
              <div class="memo-ratio">
                <div class="memo-label">基準計画達成率:</div>
                <div class="memo-ratio-value">${formatPlanComparisonValue(
                  planComparisonSummaryForPrint.baselinePlanAchievementRatio,
                  {
                    suffix: '%',
                    minimumFractionDigits: 1,
                    maximumFractionDigits: 1,
                  },
                )}</div>
              </div>
              <div class="memo-ratio">
                <div class="memo-label">現行計画達成率:</div>
                <div class="memo-ratio-value">${formatPlanComparisonValue(
                  planComparisonSummaryForPrint.currentPlanAchievementRatio,
                  {
                    suffix: '%',
                    minimumFractionDigits: 1,
                    maximumFractionDigits: 1,
                  },
                )}</div>
              </div>
              <div class="memo-ratio">
                <div class="memo-label">達成率差異:</div>
                <div class="memo-ratio-value ${
                  planComparisonSummaryForPrint.achievementRatioDifference !== null &&
                  planComparisonSummaryForPrint.achievementRatioDifference !== undefined
                    ? planComparisonSummaryForPrint.achievementRatioDifference >= 0
                      ? 'positive-difference'
                      : 'negative-difference'
                    : ''
                }">${formatPlanComparisonValue(
                  planComparisonSummaryForPrint.achievementRatioDifference,
                  {
                    suffix: '%',
                    minimumFractionDigits: 1,
                    maximumFractionDigits: 1,
                  },
                )}</div>
              </div>
              <div class="memo-ratio">
                <div class="memo-label">生産状態:</div>
                <div class="memo-ratio-value ${
                  planComparisonSummaryForPrint.productionStatus === '生産遅れ'
                    ? 'negative-difference'
                    : planComparisonSummaryForPrint.productionStatus === '生産早い'
                      ? 'positive-difference'
                      : ''
                }">${planComparisonSummaryForPrint.productionStatus || '-'}</div>
              </div>
            </div>
          </div>
        </div>
        <div class="print-footer">
          <div class="print-footer-left">*** 集計時間:前日15:00~当日15:00</div>
          <div class="print-footer-right">${currentDateTime} 発行</div>
        </div>
      </div>
    </body>
    </html>
  `
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

// ページ初期化
onMounted(() => {
  // 先初始化搜索表单默认值
  initializeSearchForm()
  // 然后加载数据
  loadMachineOptions()
  loadPlanData()
  calculatePlanStats() // 加载统计
  loadWeldingPlanComparisonSummary({ silent: true, workingDays: specifiedWorkingDays.value })
  loadInstructions()
  loadStats()
  // 初始化二维表日期为当月，并加载
  setMatrixMonth(0) // 设置为当月
})
</script>

<style scoped>
.welding-instruction-container {
  padding: 6px;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  min-height: 100vh;
  position: relative;
}

.welding-instruction-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    radial-gradient(circle at 20% 80%, rgba(120, 119, 198, 0.03) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(255, 119, 198, 0.03) 0%, transparent 50%);
  pointer-events: none;
}

/* コンパクトヘッダー */
.page-header {
  margin-bottom: 8px;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(10px);
  padding: 10px 14px;
  border-radius: 10px;
  box-shadow:
    0 1px 4px rgba(0, 0, 0, 0.08),
    0 2px 8px rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(226, 232, 240, 0.9);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.back-btn {
  flex-shrink: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
  transition: all 0.3s ease;
}

.back-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.header-info {
  flex: 1;
  min-width: 0;
}

.page-title {
  font-size: 25px;
  font-weight: 700;
  color: #1a202c;
  margin: 0;
  line-height: 1.3;
  letter-spacing: -0.3px;
}

.page-subtitle {
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
  margin-top: 2px;
}

/* 计划区域样式 */
.plan-section {
  margin-bottom: 8px;
}

.section-card {
  border-radius: 10px;
  box-shadow:
    0 1px 4px rgba(0, 0, 0, 0.08),
    0 2px 8px rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(226, 232, 240, 0.9);
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(10px);
  overflow: hidden;
}

/* コンパクト統計グリッド */
.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  padding: 6px;
  margin: 0;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 4px 12px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 250, 252, 0.95) 100%);
  border-radius: 8px;
  border: 1px solid rgba(226, 232, 240, 0.7);
  transition: all 0.2s ease;
}

.stat-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  width: 32px;
  height: 32px;
  border-radius: 7px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 15px;
  flex-shrink: 0;
}

.total-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.machine-icon {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-content {
  flex: 1;
  min-width: 0;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: #1a202c;
  line-height: 1.1;
  margin-bottom: 1px;
}

.stat-label {
  font-size: 10px;
  color: #64748b;
  font-weight: 500;
}

/* コンパクト検索バー */
.search-bar {
  padding: 10px 14px;
  background: linear-gradient(135deg, rgba(248, 250, 252, 0.95) 0%, rgba(241, 245, 249, 0.95) 100%);
  border-top: 1px solid rgba(226, 232, 240, 0.7);
}

.search-controls {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.date-control {
  display: flex;
  align-items: center;
  gap: 8px;
}

.compact-date-picker {
  width: 200px;
  border-radius: 8px;
}

.date-buttons {
  display: flex;
  gap: 4px;
}

.date-btn {
  padding: 4px 8px;
  font-size: 11px;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
  background: white;
  color: #64748b;
  transition: all 0.2s ease;
}

.date-btn:hover {
  background: #f1f5f9;
  border-color: #cbd5e0;
  transform: translateY(-1px);
}

.date-btn.prev {
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  border-color: #fca5a5;
  color: #dc2626;
}

.date-btn.today {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  border-color: #93c5fd;
  color: #2563eb;
}

.date-btn.next {
  background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
  border-color: #86efac;
  color: #16a34a;
}

.machine-select {
  width: 140px;
  border-radius: 8px;
}

.keyword-input {
  width: 180px;
  border-radius: 8px;
}

.print-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 8px;
  padding: 6px 12px;
  font-weight: 500;
}

.matrix-search-input {
  width: 180px;
  border-radius: 8px;
}

.month-buttons {
  display: flex;
  gap: 4px;
  margin-left: 8px;
}

.month-btn {
  padding: 4px 8px;
  font-size: 11px;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
  background: white;
  color: #64748b;
  transition: all 0.2s ease;
  min-width: 40px;
}

.month-btn:hover {
  background: #f1f5f9;
  border-color: #cbd5e0;
  transform: translateY(-1px);
}

.month-btn.prev {
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  border-color: #fca5a5;
  color: #dc2626;
}

.month-btn.current {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  border-color: #93c5fd;
  color: #2563eb;
  font-weight: 600;
}

.month-btn.next {
  background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
  border-color: #86efac;
  color: #16a34a;
}

.matrix-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: 12px;
}

.export-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border: none;
  border-radius: 8px;
  padding: 6px 12px;
  font-weight: 500;
}

.print-btn {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  border: none;
  border-radius: 8px;
  padding: 6px 12px;
  font-weight: 500;
}

/* 設備名称样式 */
.machine-name {
  font-weight: 600;
  font-size: 12px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
}

.machine-name:hover {
  transform: scale(1.05);
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

/* 设备单元格样式 */
.machine-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}

.collapse-icon {
  cursor: pointer;
  transition: transform 0.3s ease;
  color: #64748b;
  font-size: 14px;
}

.collapse-icon:hover {
  color: #3b82f6;
}

.collapse-icon.collapsed {
  transform: rotate(-90deg);
}

/* 分组样式 */
.group-header {
  background: linear-gradient(135deg, rgba(248, 250, 252, 0.9) 0%, rgba(241, 245, 249, 0.9) 100%);
  font-weight: 600;
}

.group-header-text {
  font-weight: 700;
  font-size: 13px;
}

.child-row {
  background: rgba(255, 255, 255, 0.8);
}

.child-text {
  font-size: 11px;
  color: #64748b;
  padding-left: 16px;
}

/* 行列高亮样式 */
.row-highlighted {
  background: rgba(59, 130, 246, 0.1) !important;
  box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.2);
}

.col-highlighted {
  background: rgba(59, 130, 246, 0.05) !important;
}

.cell-highlighted {
  background: rgba(59, 130, 246, 0.2) !important;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.4);
  transform: scale(1.02);
  z-index: 10;
  position: relative;
}

.data-cell {
  transition: all 0.2s ease;
  cursor: pointer;
}

.data-cell:hover {
  transform: scale(1.05);
}

/* 指示区域样式 */
.instruction-section .section-card {
  border-radius: 24px;
  box-shadow: 0 25px 80px rgba(0, 0, 0, 0.12);
  border: none;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
  overflow: hidden;
  position: relative;
}

.instruction-section .section-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #f093fb 0%, #f5576c 50%, #f093fb 100%);
  background-size: 200% 100%;
  animation: shimmer 4s ease-in-out infinite;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #1a202c;
  letter-spacing: -0.2px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: linear-gradient(135deg, rgba(248, 250, 252, 0.95) 0%, rgba(241, 245, 249, 0.95) 100%);
  border-bottom: 1px solid rgba(226, 232, 240, 0.7);
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.search-section {
  margin-bottom: 20px;
}

.search-container {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.2);
  overflow: hidden;
  position: relative;
}

.search-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
}

.search-header {
  padding: 16px 20px 12px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.3);
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
}

.search-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #1a202c;
  letter-spacing: 0.2px;
}

.search-content {
  padding: 8px;
}

.search-actions {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.search-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 20px;
  margin-bottom: 0;
}

.search-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.search-label {
  font-size: 13px;
  font-weight: 600;
  color: #4a5568;
  letter-spacing: 0.2px;
  margin-bottom: 4px;
}

.date-picker-container {
  display: flex;
  flex-direction: row;
  gap: 8px;
  align-items: center;
}

.date-quick-buttons {
  display: flex;
  gap: 6px;
  justify-content: center;
}

.date-btn {
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
  border: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.date-btn.minus {
  background: linear-gradient(135deg, #e53e3e 0%, #c53030 100%);
  color: white;
}

.date-btn.today {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.date-btn.plus {
  background: linear-gradient(135deg, #38a169 0%, #2f855a 100%);
  color: white;
}

.date-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.modern-date-picker {
  flex: 1;
  min-width: 200px;
  border-radius: 10px;
  border: 1px solid rgba(226, 232, 240, 0.5);
  transition: all 0.3s ease;
}

.modern-select,
.modern-input {
  border-radius: 10px;
  border: 1px solid rgba(226, 232, 240, 0.5);
  transition: all 0.3s ease;
}

.modern-date-picker:focus,
.modern-select:focus,
.modern-input:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

/* コンパクトテーブル */
.compact-table {
  font-size: 11px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: none;
  border: 1px solid rgba(226, 232, 240, 0.7);
}

.compact-table :deep(.el-table__header) {
  font-size: 11px;
  font-weight: 600;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  color: #475569;
}

.compact-table :deep(.el-table__body) {
  font-size: 12px;
}

.compact-table :deep(.el-table__row) {
  height: 30px;
  transition: all 0.2s ease;
}

.compact-table :deep(.el-table__row:hover) {
  background: rgba(248, 250, 252, 0.8);
}

.compact-table :deep(.el-table td) {
  padding: 3px 6px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.5);
  font-weight: 400;
}

.compact-table :deep(.el-table th) {
  padding: 6px 6px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 1px solid rgba(226, 232, 240, 0.7);
  color: #475569;
  font-weight: 600;
  font-size: 10px;
}

.stats-section {
  margin-bottom: 16px;
}

.stat-card {
  border-radius: 20px;
  border: none;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.1);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px) scale(1.02);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.stat-card:hover::before {
  opacity: 1;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 16px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  position: relative;
  overflow: hidden;
}

.stat-icon::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(45deg, rgba(255, 255, 255, 0.2) 0%, transparent 100%);
  border-radius: 16px;
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

.stat-icon.plan-total {
  background: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%);
}

.stat-icon.machine-count {
  background: linear-gradient(135deg, #e67e22 0%, #d35400 100%);
}

.stat-info {
  flex: 1;
}

.stat-number {
  font-size: 24px;
  font-weight: 800;
  color: #1a202c;
  line-height: 1;
  margin-bottom: 4px;
  background: linear-gradient(135deg, #1a202c 0%, #4a5568 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.stat-label {
  font-size: 13px;
  color: #718096;
  font-weight: 500;
  letter-spacing: 0.3px;
}

.plan-stats-section {
  margin-bottom: 12px;
}

.plan-stat-card {
  border-radius: 16px;
  border: none;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  height: 90px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.plan-stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #9b59b6 0%, #e67e22 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.plan-stat-card:hover {
  transform: translateY(-3px) scale(1.02);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.plan-stat-card:hover::before {
  opacity: 1;
}

.plan-stat-content {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  height: 100%;
}

.plan-stat-icon {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  position: relative;
  overflow: hidden;
}

.plan-stat-icon::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(45deg, rgba(255, 255, 255, 0.2) 0%, transparent 100%);
  border-radius: 10px;
}

.plan-stat-icon.plan-total {
  background: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%);
}

.plan-stat-icon.machine-count {
  background: linear-gradient(135deg, #e67e22 0%, #d35400 100%);
}

.plan-stat-info {
  flex: 1;
  min-width: 0;
}

.plan-stat-number {
  font-size: 18px;
  font-weight: 800;
  color: #1a202c;
  line-height: 1;
  margin-bottom: 2px;
  background: linear-gradient(135deg, #1a202c 0%, #4a5568 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.plan-stat-label {
  font-size: 11px;
  color: #718096;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 500;
  letter-spacing: 0.2px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 24px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%);
  border-bottom: 1px solid rgba(226, 232, 240, 0.2);
  position: relative;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.card-header::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 24px;
  right: 24px;
  height: 2px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  border-radius: 1px;
}

.daily-instruction-section {
  margin-bottom: 16px;
}

.instruction-detail {
  padding: 16px 0;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 10px;
  padding: 0 14px 10px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* マトリックステーブル */
.matrix-section {
  margin-bottom: 8px;
}

.matrix-table-wrapper {
  width: 100%;
  height: 420px;
  max-height: 420px;
  overflow: auto;
  border-radius: 8px;
  border: 1px solid rgba(226, 232, 240, 0.7);
}

.matrix-table {
  width: max-content;
  min-width: 100%;
  border-collapse: collapse;
  background: #fff;
  font-size: 11px;
}

.matrix-table th,
.matrix-table td {
  border: 1px solid rgba(226, 232, 240, 0.6);
  padding: 3px 5px;
  vertical-align: middle;
  font-size: 10px;
}

.matrix-table thead th {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  font-weight: 600;
  white-space: nowrap;
  position: sticky;
  top: 0;
  z-index: 3;
  color: #475569;
}

.date-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  line-height: 1.1;
  gap: 1px;
}
.date-text {
  font-size: 10px;
  color: #475569;
  font-weight: 500;
}
.weekday-text {
  font-size: 9px;
  color: #64748b;
}

.sticky-col {
  position: sticky;
  left: 0;
  background: #fff;
  z-index: 2;
  white-space: nowrap;
  font-weight: 700;
}

/* 固定左侧四列宽度与偏移（与 sticky 一起使用） */
.machine-col {
  width: 70px;
  min-width: 70px;
  left: 0;
}
.product-col {
  width: 120px;
  min-width: 120px;
  left: 70px;
}
.operator-col {
  width: 70px;
  min-width: 70px;
  left: 190px;
}
.total-col {
  width: 100px;
  min-width: 100px;
  left: 260px;
}

/* 表体行固定行高 */
.matrix-table tbody tr {
  height: 26px;
  transition: background-color 0.2s ease;
}

.matrix-table tbody tr:hover {
  background-color: rgba(248, 250, 252, 0.8);
}

/* 交汇单元格（左侧吸附列的表头）层级更高，避免遮挡问题 */
.matrix-table thead .sticky-col {
  z-index: 4;
}

/* 合计行样式 */
.matrix-table tfoot td {
  background: #f7fafc !important;
  font-weight: 700;
  border-top: 2px solid #cbd5e0;
  position: sticky;
  bottom: 0;
  z-index: 3;
}
.matrix-total-row .sticky-col {
  background: #f7fafc !important;
  z-index: 5; /* 底部合计行与左侧吸附列交汇处提升层级 */
}

/* 依設備分组的行底色（柔和） */
.machine-group-0 {
  background-color: #fafafa;
}
.machine-group-1 {
  background-color: #f9fbff;
}
.machine-group-2 {
  background-color: #fbf9ff;
}

/* 让左侧吸附列继承行背景（仅限 tbody），表头和合计行保持原样 */
.matrix-table tbody .sticky-col {
  background: inherit;
}

/* 悬浮略微提升对比度 */
.matrix-row:hover td {
  filter: brightness(0.98);
}

/* 数字居中 */
.numeric-cell {
  text-align: center;
}

/* 周末日期表头与合计列显示为红色 */
.matrix-table thead th.is-weekend .date-text,
.matrix-table thead th.is-weekend .weekday-text,
.matrix-table tfoot td.is-weekend {
  color: #e53e3e;
}

/* 当天日期表头、表体和合计列显示为浅黄色背景 */
.matrix-table thead th.is-today {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%) !important;
}

.matrix-table thead th.is-today .date-text,
.matrix-table thead th.is-today .weekday-text {
  color: #92400e;
  font-weight: 700;
}

.matrix-table tbody td.is-today {
  background: linear-gradient(135deg, #fef9c3 0%, #fef08a 100%) !important;
  font-weight: 600;
}

.matrix-table tfoot td.is-today {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%) !important;
  color: #92400e;
  font-weight: 700;
}

.cell-items {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.cell-item {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: baseline;
}

.item-name {
  font-weight: 600;
  color: #2d3748;
}
.item-cd {
  color: #718096;
}
.item-qty {
  color: #4a5568;
}
.item-op {
  color: #a0aec0;
}

.cell-empty {
  color: #cbd5e0;
  text-align: center;
}

/* レスポンシブデザイン */
@media (max-width: 1200px) {
  .welding-instruction-container {
    padding: 6px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
    gap: 8px;
  }

  .search-controls {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .date-control {
    justify-content: space-between;
  }

  .compact-date-picker {
    width: auto;
    flex: 1;
  }
}

@media (max-width: 768px) {
  .welding-instruction-container {
    padding: 4px;
  }

  .page-header {
    margin-bottom: 8px;
    padding: 8px 12px;
  }

  .page-title {
    font-size: 16px;
  }

  .page-subtitle {
    font-size: 11px;
  }

  .stats-grid {
    padding: 12px;
    gap: 8px;
  }

  .stat-item {
    padding: 8px 12px;
  }

  .stat-icon {
    width: 28px;
    height: 28px;
    font-size: 14px;
  }

  .stat-value {
    font-size: 16px;
  }

  .stat-label {
    font-size: 10px;
  }

  .search-bar {
    padding: 8px 12px;
  }

  .search-controls {
    gap: 6px;
  }

  .date-control {
    flex-direction: column;
    align-items: stretch;
    gap: 6px;
  }

  .date-buttons {
    justify-content: space-between;
  }

  .date-btn {
    flex: 1;
    font-size: 10px;
    padding: 3px 6px;
  }

  .machine-select,
  .keyword-input {
    width: 100%;
  }

  .compact-table {
    font-size: 11px;
  }

  .compact-table :deep(.el-table__header) {
    font-size: 10px;
  }

  .compact-table :deep(.el-table__row) {
    height: 28px;
  }

  .compact-table :deep(.el-table td) {
    padding: 2px 4px;
  }

  .compact-table :deep(.el-table th) {
    padding: 6px 4px;
    font-size: 10px;
  }

  .section-title {
    font-size: 12px;
  }

  .card-header {
    padding: 8px 12px;
  }
}

@media (max-width: 480px) {
  .welding-instruction-container {
    padding: 2px;
  }

  .page-header {
    padding: 6px 8px;
  }

  .header-content {
    gap: 8px;
  }

  .page-title {
    font-size: 14px;
  }

  .page-subtitle {
    font-size: 10px;
  }

  .stats-grid {
    padding: 8px;
  }

  .stat-item {
    padding: 6px 8px;
    gap: 8px;
  }

  .stat-icon {
    width: 24px;
    height: 24px;
    font-size: 12px;
  }

  .stat-value {
    font-size: 14px;
  }

  .stat-label {
    font-size: 9px;
  }
}

/* 打印预览对话框样式 */
.print-preview-dialog :deep(.el-dialog__body) {
  padding: 0;
}

.print-preview-content {
  height: 80vh;
  display: flex;
  flex-direction: column;
  font-family: inherit; /* 继承父元素字体 */
}

.print-preview-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f8f9fa;
  font-family: inherit; /* 继承父元素字体 */
}

.print-preview-body {
  flex: 1;
  overflow: auto;
  padding: 8px;
  background: #fff;
  font-family: inherit; /* 继承父元素字体 */
}

/* 确保打印预览内容使用与主页面一致的字体样式 */
.print-preview-body :deep(.print-container) {
  font-family:
    -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
  font-size: 12px !important;
  line-height: 1.2 !important;
  color: #000 !important;
}

/* 标题包装器样式 */
.title-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  font-size: 20px;
  color: #667eea;
}

/* 操作按钮样式 */
.action-btn {
  border: none;
  border-radius: 10px;
  padding: 8px 16px;
  font-weight: 600;
  font-size: 12px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: relative;
  overflow: hidden;
}

.action-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.5s ease;
}

.action-btn:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.action-btn:hover::before {
  left: 100%;
}

.action-btn:active {
  transform: translateY(0) scale(0.98);
  transition: all 0.1s ease;
}

.action-btn.update-btn {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
}

.action-btn.refresh-btn {
  background: linear-gradient(135deg, #64748b 0%, #475569 100%);
  color: white;
}

.print-btn.instruction-btn,
.print-btn[type='success'] {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

/* 主要操作按钮 - 蓝色（段取予定発行） */
.print-btn[type='primary'] {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
}

.print-preview-body :deep(.print-header) {
  display: block;
  margin-bottom: 15px;
  padding-bottom: 8px;
  position: relative;
  font-family:
    -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
}

.print-preview-body :deep(.print-header-top) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.print-preview-body :deep(.print-title) {
  font-size: 20px !important;
  font-weight: bold;
  color: #000;
  flex: 0 0 auto;
  font-family:
    -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
}

.print-preview-body :deep(.print-machine-section) {
  text-align: center;
  font-size: 20px !important;
  flex: 0 0 auto;
  margin-left: auto;
  margin-right: 20px;
  font-family:
    -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
}

.print-preview-body :deep(.print-subtitle) {
  font-size: 20px !important;
  color: #000;
  font-family:
    -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
}

.print-preview-body :deep(.print-date) {
  font-size: 20px !important;
  font-weight: bold;
  font-family:
    -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
}

.print-preview-body :deep(.print-date-sub) {
  font-size: 10px !important;
  color: #000;
  margin-top: 2px;
  font-family:
    -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
}

.print-preview-body :deep(.print-date-section) {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  text-align: center;
  font-size: 20px !important;
  font-family:
    -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
}

.print-preview-body :deep(.print-process) {
  font-size: 20px !important;
  color: #000;
  flex: 0 0 auto;
  font-family:
    -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
}

.print-preview-body :deep(.qr-code-container) {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.print-preview-body :deep(.qr-code-image) {
  width: 40px;
  height: 40px;
  border: 1px solid #000;
}

.print-preview-body :deep(.qr-code-label) {
  font-size: 10px !important;
  color: #000;
  text-align: center;
  font-family:
    -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
}

.print-preview-body :deep(.main-table) {
  width: 100%;
  border-collapse: collapse;
  border: none;
  font-family:
    -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
}

.print-preview-body :deep(.main-table th),
.print-preview-body :deep(.main-table td) {
  border: 1px solid #000;
  padding: 3px 4px;
  text-align: center;
  vertical-align: middle;
  font-family:
    -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
}

.print-preview-body :deep(.main-table th) {
  background-color: #f0f0f0;
  font-weight: bold;
  font-size: 10px !important;
  height: 12px;
}

.print-preview-body :deep(.main-table td) {
  font-size: 11px !important;
  height: 10px;
}

.print-preview-body :deep(.main-table .priority) {
  width: 8%;
}

.print-preview-body :deep(.main-table .remarks) {
  width: 20%;
}

.print-preview-body :deep(.qr-code) {
  width: 16px;
  height: 16px;
  background-color: #000;
  display: inline-block;
  margin: 0 auto;
}

.print-preview-body :deep(.product-cd-cell) {
  text-align: center;
  vertical-align: middle;
}

.print-preview-body :deep(.product-qr-container) {
  display: flex;
  justify-content: center;
  align-items: center;
}

.print-preview-body :deep(.product-qr-image) {
  width: 25px !important;
  height: 25px !important;
  border: none;
}

/* 勤務時間帯表格预览样式 */
.print-preview-body :deep(.shift-table-container) {
  position: fixed;
  bottom: 20px;
  left: 0;
  right: 0;
  width: 100%;
  padding-top: 5px;
}

.print-preview-body :deep(.section-divider) {
  position: relative;
  text-align: center;
  margin-bottom: 5px;
}

.print-preview-body :deep(.section-divider::before) {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 0.5px;
  background: #000;
  z-index: 1;
}

.print-preview-body :deep(.section-title) {
  background: white;
  padding: 0 10px;
  font-size: 10px !important;
  font-weight: bold;
  color: #000;
  position: relative;
  z-index: 2;
  font-family:
    -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
}

.print-preview-body :deep(.shift-table) {
  width: 100%;
  border-collapse: collapse;
  border: 0.5px solid #000;
  font-size: 9px !important;
  font-family:
    -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
}

.print-preview-body :deep(.shift-table th),
.print-preview-body :deep(.shift-table td) {
  border: 0.5px solid #000;
  padding: 2px 3px;
  text-align: center;
  vertical-align: middle;
  font-family:
    -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
}

.print-preview-body :deep(.shift-table th) {
  background-color: #f0f0f0;
  font-weight: normal !important;
  font-size: 11px !important;
  height: 25px;
}

.print-preview-body :deep(.shift-table td) {
  font-size: 10px !important;
  height: 30px;
}

.print-preview-body :deep(.shift-table .worker) {
  width: 8%;
}

.print-preview-body :deep(.shift-table .shift-time) {
  width: 8%;
}

.print-preview-body :deep(.shift-table .stop-time) {
  width: 8%;
}

.print-preview-body :deep(.shift-table .product-name) {
  width: 10%;
}

.print-preview-body :deep(.shift-table .production-qty) {
  width: 8%;
}

.print-preview-body :deep(.shift-table .defect) {
  width: 7%;
}

.print-preview-body :deep(.shift-table .exchange) {
  width: 7%;
}

.print-preview-body :deep(.shift-table .transport) {
  width: 7%;
}

.print-preview-body :deep(.shift-table .cleaning) {
  width: 7%;
}

.print-preview-body :deep(.shift-table .preparation) {
  width: 7%;
}

.print-preview-body :deep(.shift-table .other) {
  width: 7%;
}

.print-preview-body :deep(.shift-table .ts) {
  width: 7%;
}

.print-preview-body :deep(.shift-table .sr) {
  width: 7%;
}

.print-preview-body :deep(.time-ranges-row) {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 5px;
  padding: 3px 0;
  font-size: 7px !important;
  flex-wrap: nowrap;
  font-family:
    -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
}

.print-preview-body :deep(.time-ranges-row span) {
  flex: 0 0 auto;
  text-align: center;
  padding: 1px 3px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
  white-space: nowrap;
}

.print-preview-body :deep(.time-text) {
  font-size: 8px !important;
  font-weight: bold;
}

.print-preview-body :deep(.checkbox) {
  font-size: 12px !important;
  font-weight: bold;
  line-height: 1;
}

.print-preview-body :deep(.highlighted-row) {
  background-color: #f5f5f5;
}

.print-preview-body :deep(.highlighted-row td) {
  color: #dc3545 !important;
  font-weight: bold;
}

.print-preview-body :deep(.no-data-cell) {
  text-align: center;
  vertical-align: middle;
  height: 120px;
  background-color: #f8f9fa;
}

.print-preview-body :deep(.no-data-message) {
  font-size: 24px !important;
  font-weight: bold;
  color: #6c757d;
  text-align: center;
  margin: 0;
  padding: 8px;
  font-family:
    -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
}
</style>
