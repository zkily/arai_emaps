<template>
  <div class="molding-instruction-container" :class="{ 'is-compact': compact }">
    <!-- コンパクトヘッダー -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-info">
          <div class="title-wrapper">
            <el-icon class="title-icon"><Document /></el-icon>
            <h1 class="page-title">成型指示書発行管理</h1>
          </div>
          <span class="page-subtitle">生産計画データ管理・指示発行システム</span>
        </div>
        <div class="page-header-actions">
          <div class="header-stats">
            <div class="header-stat-item">
              <div class="stat-icon total-icon">
                <el-icon><TrendCharts /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ formatNumber(planStats.totalQuantity) }}</div>
                <div class="stat-label">計画生産数</div>
              </div>
            </div>
            <div class="header-stat-item">
              <div class="stat-icon machine-icon">
                <el-icon><Monitor /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ planStats.machineCount }}</div>
                <div class="stat-label">稼働設備</div>
              </div>
            </div>
          </div>
          <el-button
            :icon="Refresh"
            size="small"
            type="info"
            class="action-btn refresh-btn"
            @click="refreshPlanData"
          >
            データ更新
          </el-button>
        </div>
      </div>
    </div>

    <!-- 上部：成型計画データテーブルエリア -->
    <div class="plan-section">
      <el-card class="section-card">
        <!-- コンパクト検索バー -->
        <div class="search-bar">
          <div class="search-controls">
            <div class="date-control">
              <span class="filter-label">生産日</span>
              <el-date-picker
                v-model="planSelectedDate"
                type="date"
                placeholder="生産日"
                format="MM/DD"
                value-format="YYYY-MM-DD"
                size="small"
                class="compact-date-picker"
                @change="searchPlans"
              />
              <div class="date-buttons">
                <el-button size="small" class="date-btn prev" @click="setDateRange(-1)"
                  >前日</el-button
                >
                <el-button size="small" class="date-btn today" @click="setDateRange(0)"
                  >今日</el-button
                >
                <el-button size="small" class="date-btn next" @click="setDateRange(1)"
                  >翌日</el-button
                >
              </div>
            </div>
            <el-select
              v-model="planSearchForm.machineName"
              placeholder="設備選択"
              clearable
              size="small"
              class="machine-select"
              @change="searchPlans"
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
              size="small"
              class="keyword-input"
              @input="searchPlans"
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
                :icon="Download"
                size="small"
                type="success"
                class="print-btn instruction-btn"
                @click="printInstructions"
              >
                指示書発行
              </el-button>
            </el-tooltip>
            <el-tooltip content="プレビューで編集してから印刷" placement="top">
              <el-button
                size="small"
                type="primary"
                class="print-btn"
                :loading="printingSetupSchedule"
                @click="openSetupSchedulePreview"
              >
                段取表プレビュー
              </el-button>
            </el-tooltip>
            <el-tooltip content="編集せずにそのまま印刷" placement="top">
              <el-button
                :icon="Printer"
                size="small"
                type="primary"
                class="print-btn"
                :loading="printingSetupSchedule"
                @click="printSetupSchedule"
              >
              段取表印刷
              </el-button>
            </el-tooltip>
            <el-button
              v-if="showWorkTimeConfig"
              data-work-time-config-button
              size="small"
              type="info"
              class="print-btn"
              @click="openWorkTimeConfigDialog"
            >
              設備運行時間設定
            </el-button>
            <div class="forming-notes-btn-wrap">
              <el-button
                type="default"
                size="small"
                class="forming-notes-toolbar-btn"
                title="メモ（TODO）"
                @click="openFormingInstructionNotesDialog"
              >
                <span class="notes-badge-wrap">
                  <el-icon><Memo /></el-icon>
                  <span v-if="formingInstructionNotesCount > 0" class="notes-count-badge">
                    {{ formingInstructionNotesCount }}
                  </span>
                </span>
              </el-button>
            </div>
          </div>
        </div>

        <el-table
          v-loading="planLoading"
          :data="planData"
          :style="{ width: '100%' }"
          max-height="245"
          :default-sort="{ prop: 'plan_date', order: 'ascending' }"
          size="small"
          class="compact-table"
          :row-class-name="tableRowClassName"
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
            align="center"
            width="120"
            sortable
            :sort-orders="['ascending', 'descending']"
          />
          <el-table-column prop="product_cd" label="製品CD" align="center" width="100" />
          <el-table-column prop="product_name" label="製品名" width="140" />
          <el-table-column
            prop="operator"
            label="生産順位"
            width="110"
            align="center"
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
              <!-- 调试：显示原始值 -->
              <!-- <div>原始值: {{ JSON.stringify(row.efficiency_rate) }}</div> -->
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
              <!-- 调试：显示原始值 -->
              <!-- <div>原始值: {{ JSON.stringify(row.setup_time) }}</div> -->
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
                :placeholder="
                  isHighlightProduct(row.product_name) ? '新聞紙をかける' : '備考を入力'
                "
                clearable
                @input="handleRemarksInput(row)"
                @blur="saveRemarks(row)"
                @keyup.enter="saveRemarks(row)"
              />
            </template>
          </el-table-column>
        </el-table>

      </el-card>
    </div>

    <!-- 日別計画・実績生産数（同一APIレコードを plan_date で集計） -->
    <div class="plan-qty-chart-section">
      <el-card class="section-card">
        <template #header>
          <div class="card-header">
            <div class="section-title plan-qty-chart-title-row">
              <el-icon size="20"><TrendCharts /></el-icon>
              <span>日別計画・実績生産数</span>
              <span class="plan-qty-chart-sub">計画・実績を日付ごとに合計表示</span>
            </div>
            <div class="header-actions plan-qty-chart-actions">
              <el-date-picker
                v-model="planQtyChartDateRange"
                type="daterange"
                range-separator="〜"
                start-placeholder="開始日"
                end-placeholder="終了日"
                format="MM/DD"
                value-format="YYYY-MM-DD"
                size="small"
                class="compact-date-picker"
                @change="loadPlanQtyChartData"
              />
              <div class="month-buttons">
                <el-button size="small" class="month-btn prev" @click="setPlanQtyChartMonth(-1)"
                  >前月</el-button
                >
                <el-button size="small" class="month-btn current" @click="setPlanQtyChartMonth(0)"
                  >今月</el-button
                >
                <el-button size="small" class="month-btn next" @click="setPlanQtyChartMonth(1)"
                  >翌月</el-button
                >
              </div>
            </div>
          </div>
        </template>

        <div v-loading="planQtyChartLoading" class="plan-qty-chart-body">
          <el-empty
            v-if="!planQtyChartLoading && !planQtyChartHasData"
            description="該当期間に計画・実績の数量がありません"
            class="plan-qty-chart-empty"
          />
          <div v-show="planQtyChartHasData" ref="planQtyChartEl" class="plan-qty-chart-canvas" />
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
          <el-button type="primary" :icon="Download" @click="printInstructions">
            印刷実行
          </el-button>
          <el-button @click="printPreviewVisible = false"> 閉じる </el-button>
        </div>
        <div class="print-preview-body" v-html="printPreviewContent"></div>
      </div>
    </el-dialog>

    <!-- 段取予定プレビュー（編集してから印刷） -->
    <el-dialog
      v-model="setupSchedulePreviewVisible"
      title="段取予定プレビュー（編集可）"
      width="75%"
      top="2vh"
      :close-on-click-modal="false"
      destroy-on-close
      class="setup-schedule-preview-dialog"
    >
      <div class="setup-preview-body">
        <div v-if="setupSchedulePreviewMeta" class="setup-preview-header">
          <span class="setup-preview-meta setup-preview-date">
            <span class="setup-preview-meta-label">生産日</span>
            <span class="setup-preview-meta-value">{{ setupSchedulePreviewMeta.productionDate }}</span>
          </span>
          <span class="setup-preview-meta setup-preview-total">
            <span class="setup-preview-meta-label">生産計画合計数</span>
            <span class="setup-preview-meta-value">{{ setupSchedulePreviewMeta.totalQuantity?.toLocaleString('ja-JP') }}</span>
          </span>
        </div>
        <el-table
          :data="setupSchedulePreviewTableRows"
          border
          size="small"
          max-height="62vh"
          class="setup-preview-table"
          stripe
        >
          <el-table-column label="生産残数" width="92" align="center">
            <template #default="{ row }">
              <el-input v-model="row.totalPlanQuantity" size="small" type="number" placeholder="" class="setup-preview-input" />
            </template>
          </el-table-column>
          <el-table-column prop="line" label="ライン" width="70" show-overflow-tooltip />
          <el-table-column label="予定稼働(H)" width="92" align="center">
            <template #default="{ row }">
              <div class="planned-hours-chip" :class="plannedHoursLevelClass(row.plannedWorkingHours)">
                {{ formatPlannedWorkingHours(row.plannedWorkingHours) }}
              </div>
            </template>
          </el-table-column>
          <el-table-column label="操業度(進捗)" width="72" align="center" class-name="op-progress-col">
            <template #default="{ row }">
              <el-input
                v-model="row.operationVariance"
                size="small"
                placeholder=""
                class="setup-preview-input"
                @blur="formatOperationVarianceToOneDecimal(row)"
              />
            </template>
          </el-table-column>
          <el-table-column label="生産品種" width="108" align="center">
            <template #default="{ row }">
              <el-input v-model="row.productName" size="small" placeholder="" class="setup-preview-input" />
            </template>
          </el-table-column>
          <el-table-column label="能率" width="90" align="center">
            <template #default="{ row }">
              <el-input v-model="row.efficiency" size="small" placeholder="" class="setup-preview-input" />
            </template>
          </el-table-column>
          <el-table-column label="当日計画数" width="88" align="center">
            <template #default="{ row }">
              <el-input v-model="row.planQuantity" size="small" type="number" placeholder="" class="setup-preview-input setup-preview-plan-quantity" />
            </template>
          </el-table-column>
          <el-table-column label="残生産時間" width="88" align="center">
            <template #default="{ row }">
              <el-input v-model="row.setupAfterHours" size="small" placeholder="" class="setup-preview-input" />
            </template>
          </el-table-column>
          <el-table-column label="" width="42" align="center" class-name="preview-arrow-col" label-class-name="preview-arrow-col">
            <template #default="{ row }">
              <span v-if="hasNextProduct(row.nextProductName)" class="next-arrow-indicator">→</span>
            </template>
          </el-table-column>
          <el-table-column label="次生産品種" width="130" align="center">
            <template #default="{ row }">
              <el-input v-model="row.nextProductName" size="small" placeholder="" class="setup-preview-input" />
            </template>
          </el-table-column>
          <el-table-column label="次品種計画数" width="92" align="center">
            <template #default="{ row }">
              <el-input v-model="row.nextQuantity" size="small" type="number" placeholder="" class="setup-preview-input" />
            </template>
          </el-table-column>
          <el-table-column label="備考" min-width="200" align="center">
            <template #default="{ row }">
              <el-input v-model="row.remarks" size="small" type="textarea" :rows="1" placeholder="" class="setup-preview-input setup-preview-remarks" />
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <div class="setup-preview-footer">
          <el-button type="primary" size="default" :icon="Printer" @click="printFromSetupSchedulePreview">印刷</el-button>
          <el-button @click="setupSchedulePreviewVisible = false">閉じる</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 設備運行時間設定弹窗 -->
    <el-dialog
      v-if="showWorkTimeConfig"
      v-model="workTimeConfigDialogVisible"
      data-work-time-config-dialog
      title="設備運行時間設定"
      width="760px"
      :close-on-click-modal="false"
      class="work-time-dialog"
    >
      <div v-loading="workTimeConfigLoading" class="work-time-dialog__body">
        <div class="work-time-dialog__toolbar">
          <div>
            <h3 class="work-time-dialog__subtitle">稼働時間帯を設定する設備を管理</h3>
            <p class="work-time-dialog__hint">
              チェックを入れた時間帯は設備が稼働中として扱われます
            </p>
          </div>
          <el-button type="primary" :icon="Plus" size="small" @click="openAddWorkTimeConfigDialog">
            設備追加
          </el-button>
        </div>

        <el-table
          :data="workTimeConfigData"
          border
          :style="{ width: '100%' }"
          size="small"
          class="work-time-table"
          max-height="420"
        >
          <el-table-column
            prop="machine_cd"
            label="設備CD"
            width="100"
            fixed="left"
            show-overflow-tooltip
          />
          <el-table-column
            prop="machine_name"
            label="設備名"
            min-width="100"
            fixed="left"
            show-overflow-tooltip
          />
          <el-table-column label="17-19時" align="center" width="100">
            <template #default="{ row }">
              <el-checkbox
                v-model="row.time_slot_17_19"
                @change="handleTimeSlotChange(row, '17_19')"
              />
            </template>
          </el-table-column>
          <el-table-column label="19-21時" align="center" width="100">
            <template #default="{ row }">
              <el-checkbox
                v-model="row.time_slot_19_21"
                @change="handleTimeSlotChange(row, '19_21')"
              />
            </template>
          </el-table-column>
          <el-table-column label="6-8時" align="center" width="100">
            <template #default="{ row }">
              <el-checkbox v-model="row.time_slot_6_8" @change="handleTimeSlotChange(row, '6_8')" />
            </template>
          </el-table-column>
          <el-table-column label="操作" align="center" width="120" fixed="right">
            <template #default="{ row }">
              <el-button type="danger" link size="small" @click="deleteWorkTimeConfig(row)">
                削除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <div class="dialog-footer work-time-dialog__footer">
          <el-button @click="workTimeConfigDialogVisible = false">閉じる</el-button>
          <el-button type="primary" :loading="savingWorkTimeConfig" @click="saveWorkTimeConfig">
            一括保存
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 添加/编辑設備運行時間設定弹窗 -->
    <el-dialog
      v-if="showWorkTimeConfig"
      v-model="workTimeConfigFormDialogVisible"
      data-work-time-config-form-dialog
      :title="workTimeConfigForm.id ? '設備運行時間設定編集' : '設備運行時間設定追加'"
      width="420px"
      :close-on-click-modal="false"
      class="work-time-form-dialog"
    >
      <el-form
        ref="workTimeConfigFormRef"
        :model="workTimeConfigForm"
        :rules="workTimeConfigFormRules"
        label-width="110px"
        class="work-time-form"
      >
        <el-form-item label="設備コード" prop="machine_cd">
          <el-select
            v-model="workTimeConfigForm.machine_cd"
            placeholder="設備コードを選択"
            :disabled="!!workTimeConfigForm.id"
            filterable
            class="work-time-form__select"
            @change="handleMachineCdChange"
          >
            <el-option
              v-for="machine in machineOptionsForWorkTime"
              :key="machine.machine_cd"
              :label="`${machine.machine_cd} - ${machine.machine_name}`"
              :value="machine.machine_cd"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="設備名" prop="machine_name">
          <el-input v-model="workTimeConfigForm.machine_name" placeholder="設備名" disabled />
        </el-form-item>
        <el-form-item label="運行時間帯">
          <el-checkbox-group v-model="workTimeConfigForm.timeSlots">
            <el-checkbox label="17_19">17-19</el-checkbox>
            <el-checkbox label="19_21">19-21</el-checkbox>
            <el-checkbox label="6_8">6-8</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer work-time-form-dialog__footer">
          <el-button @click="workTimeConfigFormDialogVisible = false">キャンセル</el-button>
          <el-button
            type="primary"
            :loading="savingWorkTimeConfigForm"
            @click="saveWorkTimeConfigForm"
          >
            保存
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- メモ（TODO）確認ダイアログ（切断指示ページと同機能・成型用 scope） -->
    <el-dialog
      v-model="formingInstructionNotesDialogVisible"
      title="メモ（TODO）"
      width="520px"
      class="forming-instruction-notes-dialog"
      :close-on-click-modal="false"
      :destroy-on-close="true"
      :show-close="false"
    >
      <div class="cutting-notes-dialog-body">
        <div class="cutting-notes-add">
          <el-input
            v-model="formingInstructionNotesNewContent"
            type="textarea"
            :rows="2"
            size="small"
            maxlength="200"
            class="cutting-notes-input"
            placeholder="簡単なメモを入力（短文）"
          />
          <div class="cutting-notes-add-actions">
            <span class="cutting-notes-char-count">{{ formingInstructionNotesNewContent.length }}/200</span>
            <el-button
              type="primary"
              size="small"
              class="cutting-notes-add-btn"
              :loading="formingInstructionNotesSaving"
              @click="addFormingInstructionNote"
            >
              追加
            </el-button>
          </div>
        </div>

        <el-scrollbar v-loading="formingInstructionNotesLoading" max-height="320" class="cutting-notes-scrollbar">
          <div
            v-if="!formingInstructionNotesLoading && !formingInstructionNotesList.length"
            class="cutting-notes-empty"
          >
            未登録
          </div>

          <div v-for="n in formingInstructionNotesList" :key="n.id" class="cutting-notes-row">
            <el-checkbox
              :model-value="n.is_done === 1"
              size="small"
              @change="(val) => toggleFormingInstructionNoteDone(n, val)"
            />
            <div
              class="cutting-notes-row-content"
              :class="{ 'cutting-notes-row-content--done': n.is_done === 1 }"
            >
              {{ n.content }}
            </div>
            <el-button
              v-if="n.id != null"
              type="text"
              size="small"
              class="cutting-notes-delete-btn"
              :disabled="formingInstructionNotesSaving"
              @click="deleteFormingInstructionNote(n)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </el-scrollbar>
      </div>

      <template #footer>
        <div class="cutting-notes-dialog-footer">
          <el-button size="small" @click="formingInstructionNotesDialogVisible = false">閉じる</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: 'FormingInstruction' })

/** 開発環境のみ詳細ログ（本番では無出力。no-console 許可の info を使用） */
function formingDevLog(...args: unknown[]) {
  if (import.meta.env.DEV) console.info('[FormingInstruction]', ...args)
}
import { ref, reactive, onMounted, onUnmounted, computed, nextTick } from 'vue'
import * as echarts from 'echarts'
/** ERP/MES いずれの画面でも MES 由来 API を利用し、挙動を統一する */
const planDataApiPath = computed(() => '/api/mes/forming-plan-data')
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import {
  Plus,
  Search,
  Refresh,
  Download,
  Document,
  TrendCharts,
  Monitor,
  Printer,
  Memo,
  Delete,
} from '@element-plus/icons-vue'
import request from '@/shared/api/request'
import {
  fetchLines,
  fetchSchedulingGrid,
  type ScheduleGridRow,
  type SchedulingGridResponse,
} from '@/api/aps'

const props = defineProps<{
  /** MES ルートでは設備運行時間設定 UI を非表示にします */
  showWorkTimeConfig?: boolean
  /** MES ルートでレイアウトをさらにコンパクトにします */
  compact?: boolean
}>()

// 表示制御用のフラグ（テンプレートで直接参照）
const showWorkTimeConfig = props.showWorkTimeConfig !== false
const compact = props.compact === true

/** API 响应类型（request 拦截器返回 response.data） */
interface ApiResponse<T = any> {
  success?: boolean
  data?: T
  message?: string
  list?: unknown[]
  records?: unknown[]
  [key: string]: unknown
}

interface HeaderStats {
  total: number
  pending: number
  inProgress: number
  completed: number
}

interface PlanHeaderStats {
  totalQuantity: number
  machineCount: number
}

interface SelectOption {
  label: string
  value: string
}

interface PlanRecord {
  id?: number | string
  plan_date?: string
  machine_name?: string
  product_name?: string
  product_cd?: string
  process_name?: string
  quantity?: number | string
  actual_production?: number | string
  actual_qty?: number | string
  operator?: number | string
  remarks?: string
  [key: string]: any
}

// 計画検索フォーム
const planSearchForm = reactive({
  dateRange: [] as string[],
  machineName: '',
  keyword: '',
})

// 单日选择（内部仍保持 [startDate, endDate] 结构以兼容既有逻辑）
const planSelectedDate = computed<string>({
  get: () => (planSearchForm.dateRange.length > 0 ? planSearchForm.dateRange[0] : ''),
  set: (value) => {
    if (!value) {
      planSearchForm.dateRange = []
      return
    }
    planSearchForm.dateRange = [value, value]
  },
})

// 指示検索フォーム
const searchForm = reactive({
  instructionNo: '',
  productName: '',
  status: '',
  dateRange: [],
})

// 統計データ
const stats = ref<HeaderStats>({
  total: 0,
  pending: 0,
  inProgress: 0,
  completed: 0,
})

// 計画生産数統計データ
const planStats = ref<PlanHeaderStats>({
  totalQuantity: 0,
  machineCount: 0,
})

// 計画ページネーション
const planPagination = reactive({
  currentPage: 1,
  pageSize: 30,
  total: 0,
})

// 指示ページネーション
const pagination = reactive({
  currentPage: 1,
  pageSize: 20,
  total: 0,
})

// 計画テーブルデータ
const planData = ref<PlanRecord[]>([])
const allFilteredPlanData = ref<PlanRecord[]>([]) // 存储所有过滤后的数据
const planLoading = ref(false)

// 備考保存的防抖定时器Map
const remarksSaveTimers = new Map<string, NodeJS.Timeout>()

// 日別計画・実績チャート（旧マトリックスと同API：quantity / actual_production を日別集計）
const planQtyChartDateRange = ref<string[]>([])
const planQtyChartLoading = ref(false)
const planQtyChartRecords = ref<PlanRecord[]>([])
const planQtyChartEl = ref<HTMLDivElement | null>(null)
let planQtyChartInstance: echarts.ECharts | null = null

// ========================================
// 二次元テーブル関連
// ========================================

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
const printingSetupSchedule = ref(false)
// 段取予定プレビュー（編集してから印刷）
const setupSchedulePreviewVisible = ref(false)
const setupSchedulePreviewMeta = ref<{ productionDate: string; totalQuantity: number; currentDateTime: string } | null>(null)
const setupSchedulePreviewTableRows = ref<any[]>([])

// 設備運行時間設定
const workTimeConfigDialogVisible = ref(false)
const workTimeConfigLoading = ref(false)
const savingWorkTimeConfig = ref(false)
const workTimeConfigData = ref<any[]>([])
const workTimeConfigFormDialogVisible = ref(false)
const savingWorkTimeConfigForm = ref(false)
const workTimeConfigFormRef = ref<FormInstance>()
const machineOptionsForWorkTime = ref<any[]>([]) // 設備下拉框选项
const workTimeConfigForm = reactive({
  id: null as number | null,
  machine_cd: '',
  machine_name: '',
  timeSlots: [] as string[],
})

const isApiSuccess = (res: any): boolean => {
  if (res && typeof res === 'object' && 'success' in res) {
    return !!res.success
  }
  return true
}

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
  productCd: [{ required: true, message: '製品コードを入力してください', trigger: 'blur' }],
  quantity: [{ required: true, message: '数量を入力してください', trigger: 'blur' }],
  machineName: [{ required: true, message: 'ライン名を入力してください', trigger: 'blur' }],
  operator: [{ required: true, message: '生産順位を入力してください', trigger: 'blur' }],
  planDate: [{ required: true, message: '生産日を選択してください', trigger: 'change' }],
  assignedTo: [{ required: true, message: '担当者を選択してください', trigger: 'change' }],
  priority: [{ required: true, message: '優先度を選択してください', trigger: 'change' }],
}

// 設備運行時間設定フォームバリデーションルール
const workTimeConfigFormRules = {
  machine_cd: [{ required: true, message: '設備コードを選択してください', trigger: 'change' }],
  machine_name: [{ required: true, message: '設備名を入力してください', trigger: 'blur' }],
}

// オプションデータ
const userOptions = ref([
  { label: '田中太郎', value: 'tanaka' },
  { label: '佐藤花子', value: 'sato' },
  { label: '鈴木一郎', value: 'suzuki' },
  { label: '高橋美咲', value: 'takahashi' },
])

// 設備オプションデータ
const machineOptions = ref<SelectOption[]>([])

// 計算プロパティ
const dialogTitle = computed(() => (isEdit.value ? '成型指示編集' : '新規成型指示作成'))

const getSelectedDateRange = (): [string, string] | null => {
  if (planSearchForm.dateRange && planSearchForm.dateRange.length >= 1) {
    const startDate = planSearchForm.dateRange[0]
    const endDate = planSearchForm.dateRange[1] || startDate
    return [startDate, endDate]
  }
  return null
}

const getSelectedBaseDate = () => {
  const selectedRange = getSelectedDateRange()
  return selectedRange ? selectedRange[0] : JapanDateUtils.getTodayString()
}

const buildPlanDataQueryParams = (overrides: Record<string, unknown> = {}) => {
  const params: Record<string, unknown> = {
    processName: '成型',
    page: 1,
    limit: 10000,
  }
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
  return { ...params, ...overrides }
}

const calculatePlanStatsFromData = (data: PlanRecord[]) => {
  const totalQuantity = data.reduce(
    (sum: number, item: PlanRecord) => sum + (parseInt(String(item.quantity ?? ''), 10) || 0),
    0,
  )
  const machinesWithProduction = new Set(
    data
      .filter((item: PlanRecord) => parseInt(String(item.quantity ?? ''), 10) > 0)
      .map((item: PlanRecord) => item.machine_name)
      .filter((name): name is string => Boolean(name)),
  )
  planStats.value = {
    totalQuantity,
    machineCount: machinesWithProduction.size,
  }
}

const parsePlanDataList = (result: ApiResponse | unknown[] | unknown): unknown[] => {
  if (Array.isArray(result)) return result as unknown[]
  if (result && Array.isArray((result as ApiResponse).data)) return (result as ApiResponse).data as unknown[]
  if (result && Array.isArray((result as ApiResponse).list)) return (result as ApiResponse).list as unknown[]
  if (result && (result as ApiResponse).data && Array.isArray((result as ApiResponse).data?.list)) {
    return (result as ApiResponse).data?.list as unknown[]
  }
  if (result && (result as ApiResponse).data && Array.isArray((result as ApiResponse).data?.data)) {
    return (result as ApiResponse).data?.data as unknown[]
  }
  if (result && (result as ApiResponse).data && Array.isArray((result as ApiResponse).data?.records)) {
    return (result as ApiResponse).data?.records as unknown[]
  }
  return []
}

// 初始化搜索表单默认值
const initializeSearchForm = () => {
  // 生産日をデフォルトで当日に設定（日本時区を使用）
  const todayStr = JapanDateUtils.getTodayString() // YYYY-MM-DD格式
  planSearchForm.dateRange = [todayStr, todayStr]

  // 設備名はデフォルトで空（すべての設備を表示）
  planSearchForm.machineName = ''

  // 关键词默认为空
  planSearchForm.keyword = ''
}

// 日付範囲を設定（現在選択されている日付からの日数）
const setDateRange = (daysOffset: number) => {
  let targetDate: Date

  if (planSearchForm.dateRange && planSearchForm.dateRange.length > 0) {
    // 現在選択されている開始日を基準に計算（日本時区を使用）
    const baseDateStr = planSearchForm.dateRange[0]
    const parts = JapanDateUtils.getDateParts(baseDateStr)
    targetDate = new Date(parseInt(parts.year), parseInt(parts.month) - 1, parseInt(parts.day))
    targetDate.setDate(targetDate.getDate() + daysOffset)
  } else {
    // 日付が選択されていない場合、今日を基準に計算（日本時区を使用）
    targetDate = JapanDateUtils.getCurrentDate()
    targetDate.setDate(targetDate.getDate() + daysOffset)
  }

  const dateStr = JapanDateUtils.getDateString(targetDate) // YYYY-MM-DD形式
  planSearchForm.dateRange = [dateStr, dateStr]

  // 自動的に検索を実行
  searchPlans()
}

// 設備データを読み込み
const loadMachineOptions = async () => {
  try {
    const result = (await request.get('/api/master/machines', {
      params: {
        machine_type: '成型',
      },
    })) as ApiResponse

    // request 拦截器返回 response.data；/api/master/machines 返回 { list, total } 或 { data: { list, total } }
    const list: any[] = Array.isArray(result) ? result : (result?.list ?? (result?.data as any)?.list ?? [])
    machineOptions.value = list
      .map((machine: any) => ({
        label: machine.machine_name,
        value: machine.machine_name,
      }))
      .sort((a, b) => a.label.localeCompare(b.label)) // 設備名で昇順ソート
  } catch (error) {
    console.error('設備データの読み込みに失敗:', error)
    ElMessage.error('設備データの読み込みに失敗しました')
  }
}

// 計画データを読み込み
// 默认排序：生産日升序 -> 生産順位升序（数值优先）
const sortByPlanDateAndOperatorAsc = (a: PlanRecord, b: PlanRecord) => {
  const dateA = String(a?.plan_date || '')
  const dateB = String(b?.plan_date || '')
  if (dateA !== dateB) return dateA.localeCompare(dateB)

  const opA = a?.operator != null && a.operator !== '' ? Number(a.operator) : NaN
  const opB = b?.operator != null && b.operator !== '' ? Number(b.operator) : NaN
  if (!Number.isNaN(opA) && !Number.isNaN(opB)) return opA - opB

  return String(a?.operator || '').localeCompare(String(b?.operator || ''))
}

const loadPlanData = async () => {
  planLoading.value = true
  try {
    const params = buildPlanDataQueryParams()
    const result = (await request.get(planDataApiPath.value, { params })) as ApiResponse

    if (result.success) {
      const records = Array.isArray(result?.data?.records) ? result.data.records : []
      // 过滤掉製品名为空值的数据，以及計画生産数小于等于0的数据
      const filteredData = records
        .filter((item: any) => item.product_name && item.product_name.trim() !== '' && item.quantity > 0)
        .sort(sortByPlanDateAndOperatorAsc)

      // 存储所有过滤后的数据
      allFilteredPlanData.value = filteredData
      calculatePlanStatsFromData(filteredData)

      // 更新分页总数（基于过滤后的数据）
      planPagination.total = filteredData.length

      // 前端分页：根据当前页码和每页数量切片数据
      updatePlanDataPagination()

    } else {
      throw new Error(result.message as string || 'データの取得に失敗しました')
    }
  } catch (error) {
    console.error('計画データの読み込みに失敗:', error)
    ElMessage.error('計画データの読み込みに失敗しました')
    planData.value = []
    allFilteredPlanData.value = []
    planPagination.total = 0
    calculatePlanStatsFromData([])
  } finally {
    planLoading.value = false
  }
}

// 指示リストを読み込み
const loadInstructions = async () => {
  loading.value = true
  try {
    // 这里应该调用实际的API来获取成型指示数据
    // 目前使用模拟数据
    await new Promise((resolve) => setTimeout(resolve, 1000))

    // 模拟数据
    const mockInstructions = [
      {
        id: 1,
        instructionNo: 'MOLD-20240115-001',
        productName: '成型部品A',
        productCd: 'MP001',
        quantity: 100,
        machineName: '成型機1号',
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
        productName: '成型部品B',
        productCd: 'MP002',
        quantity: 50,
        machineName: '成型機2号',
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
        productName: '成型部品C',
        productCd: 'MP003',
        quantity: 75,
        machineName: '成型機1号',
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

    // 更新日別指示日期
    updateDailyInstructionDates()
    loadStats()
  } catch (error) {
    console.error('指示リストの読み込みに失敗:', error)
    ElMessage.error('データの読み込みに失敗しました')
  } finally {
    loading.value = false
  }
}

// 更新日別指示日期
const updateDailyInstructionDates = () => {
  const dates = [...new Set(instructions.value.map((item) => item.planDate))].sort()
  dailyInstructionDates.value = dates
  if (dates.length > 0 && !activeTab.value) {
    activeTab.value = dates[0]
  }
}

// 根据日期获取指示数据
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
const loadStats = () => {
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

// 計画生産数統計を再計算（既に取得済みの筛选数据を再利用）
const calculatePlanStats = () => {
  calculatePlanStatsFromData(allFilteredPlanData.value)
}

// 获取行的唯一标识
const getRowKey = (row: any): string => {
  if (row.id) {
    return `id_${row.id}`
  }
  return `${row.plan_date}_${row.machine_name}_${row.product_cd}_${row.process_name || '成型'}`
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
      updateData.process_name = row.process_name || '成型'
    }

    // スケジュール由来データに備考列が無いため API 更新なし（画面入力のみ）
    if (planDataApiPath.value === '/api/mes/forming-plan-data') {
      return
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
            (item.process_name || '成型') === (row.process_name || '成型')
          )
        }
      })
      if (index !== -1) {
        planData.value[index].remarks = row.remarks
      }
    } else {
      ElMessage.error((result.message as string) || '備考の保存に失敗しました')
    }
  } catch (error: unknown) {
    console.error('備考保存失败:', error)
    ElMessage.error('備考の保存に失敗しました: ' + (error instanceof Error ? error.message : '未知のエラー'))
  }
}

// 計画検索
const searchPlans = () => {
  planPagination.currentPage = 1
  loadPlanData()
}

// 計画検索をリセット
const resetPlanSearch = () => {
  // 重置为默认值
  initializeSearchForm()
  searchPlans()
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
  const now = JapanDateUtils.getCurrentDate()
  const parts = JapanDateUtils.getDateParts(now)
  const year = parts.year
  const month = parts.month
  const day = parts.day
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

    ElMessage.success(isEdit.value ? '成型指示を更新しました' : '成型指示を作成しました')
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

// 更新計画データ的分页显示
const updatePlanDataPagination = () => {
  const start = (planPagination.currentPage - 1) * planPagination.pageSize
  const end = start + planPagination.pageSize
  planData.value = allFilteredPlanData.value.slice(start, end)
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
}

// 指示書を印刷
const printInstructions = async () => {
  try {
    // 获取要生成指示書的设备列表（每台设备都生成一页）
    const machineList = await getFormingMachineNamesForPrint()
    if (machineList.length === 0) {
      ElMessage.warning('印刷対象の設備がありません')
      return
    }

    // 获取完整的期间数据（可能为空，无数据时表格显示「生産計画停止」）
    const fullPlanData = await getFullPlanDataForPrint()

    // 各設備の印刷コンテンツを生成
    const printContents = await Promise.all(
      machineList.map(async (machineName) => {
        return await generatePrintContent(fullPlanData, machineName)
      }),
    )

    // すべての設備のコンテンツを1つのドキュメントに結合
    const combinedContent = printContents.join('<div style="page-break-before: always;"></div>')

    // プレビューウィンドウコンテナを作成（先に表示し、QRコードの読み込みを待つ）
    const previewContainer = document.createElement('div')
    previewContainer.style.position = 'fixed'
    previewContainer.style.top = '0'
    previewContainer.style.left = '0'
    previewContainer.style.width = '100%'
    previewContainer.style.height = '100%'
    previewContainer.style.backgroundColor = 'rgba(0, 0, 0, 0.5)'
    previewContainer.style.zIndex = '10000'
    previewContainer.style.display = 'flex'
    previewContainer.style.alignItems = 'center'
    previewContainer.style.justifyContent = 'center'

    // 閉じるボタンを作成
    const closeButton = document.createElement('button')
    closeButton.textContent = '×'
    closeButton.style.position = 'absolute'
    closeButton.style.top = '20px'
    closeButton.style.right = '20px'
    closeButton.style.width = '40px'
    closeButton.style.height = '40px'
    closeButton.style.borderRadius = '50%'
    closeButton.style.border = 'none'
    closeButton.style.backgroundColor = '#ef4444'
    closeButton.style.color = 'white'
    closeButton.style.fontSize = '24px'
    closeButton.style.cursor = 'pointer'
    closeButton.style.zIndex = '10001'
    closeButton.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.3)'
    closeButton.onmouseover = () => {
      closeButton.style.backgroundColor = '#dc2626'
      closeButton.style.transform = 'scale(1.1)'
    }
    closeButton.onmouseout = () => {
      closeButton.style.backgroundColor = '#ef4444'
      closeButton.style.transform = 'scale(1)'
    }
    closeButton.onclick = () => {
      document.body.removeChild(previewContainer)
      hasPrinted = true // 自動印刷を防止
    }

    // 読み込みヒントを作成
    const loadingText = document.createElement('div')
    loadingText.textContent = 'QRコード読み込み中...'
    loadingText.style.position = 'absolute'
    loadingText.style.top = '20px'
    loadingText.style.left = '50%'
    loadingText.style.transform = 'translateX(-50%)'
    loadingText.style.color = '#3b82f6'
    loadingText.style.fontSize = '16px'
    loadingText.style.fontWeight = '600'
    loadingText.style.zIndex = '10001'
    loadingText.style.backgroundColor = 'rgba(255, 255, 255, 0.9)'
    loadingText.style.padding = '8px 16px'
    loadingText.style.borderRadius = '8px'
    loadingText.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.2)'

    // iframeを作成
    const iframe = document.createElement('iframe')
    iframe.style.width = '90%'
    iframe.style.height = '85%'
    iframe.style.border = '2px solid #3b82f6'
    iframe.style.borderRadius = '8px'
    iframe.style.boxShadow = '0 8px 32px rgba(0, 0, 0, 0.3)'
    iframe.style.backgroundColor = '#fff'

    previewContainer.appendChild(iframe)
    previewContainer.appendChild(closeButton)
    previewContainer.appendChild(loadingText)
    document.body.appendChild(previewContainer)

    const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document
    if (!iframeDoc) {
      ElMessage.error('印刷機能の初期化に失敗しました')
      if (document.body.contains(previewContainer)) {
        document.body.removeChild(previewContainer)
      }
      return
    }

    iframeDoc.open()
    iframeDoc.write(combinedContent)
    iframeDoc.close()

    // すべての画像（特にQRコード）の読み込み完了を待つ
    const waitForImages = (): Promise<void> => {
      return new Promise((resolve) => {
        const images = iframeDoc.querySelectorAll('img')
        if (images.length === 0) {
          resolve()
          return
        }

        let loadedCount = 0
        const totalImages = images.length

        const checkComplete = () => {
          loadedCount++
          if (loadedCount === totalImages) {
            formingDevLog('すべての画像（QRコード含む）の読み込みが完了しました')
            // ヒントを更新、自動印刷を開始
            if (loadingText.parentNode) {
              loadingText.textContent = '読み込み完了、印刷ダイアログを開いています...'
              loadingText.style.color = '#10b981'
            }
            resolve()
          } else {
            // 読み込みヒントを更新
            if (loadingText.parentNode) {
              loadingText.textContent = `QRコード読み込み中... (${loadedCount}/${totalImages})`
            }
          }
        }

        images.forEach((img) => {
          if (img.complete) {
            checkComplete()
          } else {
            img.onload = checkComplete
            img.onerror = () => {
              console.warn('画像の読み込みに失敗しました:', img.src)
              checkComplete() // 失敗しても続行
            }
          }
        })
      })
    }

    // 防止重复打印的标志
    let hasPrinted = false

    // 打印函数
    const doPrint = () => {
      if (hasPrinted) return
      hasPrinted = true

      try {
        const iframeWindow = iframe.contentWindow
        if (iframeWindow && iframeDoc.body) {
          // 隐藏预览窗口容器
          if (previewContainer.parentNode) {
            previewContainer.style.display = 'none'
          }

          // 直接印刷を呼び出し、ブラウザが自動的に@pageスタイルを適用（A4縦向き）
          iframeWindow.focus()
          iframeWindow.print()

          // 印刷完了後、プレビューコンテナを削除
          setTimeout(() => {
            if (document.body.contains(previewContainer)) {
              document.body.removeChild(previewContainer)
            }
          }, 1000)
        }
      } catch (error) {
        console.error('印刷実行エラー:', error)
        ElMessage.error('印刷の実行に失敗しました')
        if (document.body.contains(previewContainer)) {
          document.body.removeChild(previewContainer)
        }
      }
    }

    // iframeの読み込み完了を待つ
    iframe.onload = async () => {
      try {
        // すべての画像の読み込み完了を待つ
        await waitForImages()
        // 読み込み完了後、自動的に印刷ダイアログに移動
        formingDevLog(
          'すべての画像（QRコード含む）の読み込みが完了し、自動的に印刷ダイアログに移動します',
        )
        // レンダリング完了を確保するため、少し追加で待機
        setTimeout(doPrint, 500)
      } catch (error) {
        console.error('画像の読み込み待機に失敗しました:', error)
        if (loadingText.parentNode) {
          loadingText.textContent = '一部の画像の読み込みに失敗しましたが、印刷は可能です'
          loadingText.style.color = '#f59e0b'
        }
        // 一部が失敗しても印刷を試みる
        setTimeout(doPrint, 500)
      }
    }

    // onloadがトリガーされない場合も、画像の読み込み後に自動印刷を試みる
    setTimeout(async () => {
      if (!hasPrinted) {
        try {
          await waitForImages()
          formingDevLog(
            'すべての画像（QRコード含む）の読み込みが完了し、自動的に印刷ダイアログに移動します',
          )
          setTimeout(doPrint, 500)
        } catch (error) {
          console.error('画像の読み込み待機に失敗しました:', error)
          if (loadingText.parentNode) {
            loadingText.textContent = '一部の画像の読み込みに失敗しましたが、印刷は可能です'
            loadingText.style.color = '#f59e0b'
          }
          // 失敗しても印刷を試みる
          doPrint()
        }
      }
    }, 2000)
  } catch (error) {
    console.error('印刷に失敗しました:', error)
    ElMessage.error('印刷に失敗しました')
  }
}

// 按设备分组数据
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

// 智能算法：计算扩展的日期范围
const calculateSmartDateRange = async () => {
  try {
    if (!planSearchForm.dateRange || planSearchForm.dateRange.length === 0) {
      return { startDate: '', endDate: '' }
    }

    // 获取基准日期（搜索条件的开始日期）
    const baseDate = new Date(planSearchForm.dateRange[0])
    const dates = []

    // 智能计算日期范围
    const baseDayOfWeek = baseDate.getDay() // 0=周日, 1=周一, ..., 6=周六

    // 计算前一天 - 特殊处理星期一
    const prevDate = new Date(baseDate)
    if (baseDayOfWeek === 1) {
      // 如果基准日是星期一，前一天跳到上周五
      prevDate.setDate(baseDate.getDate() - 3) // 周一 - 3天 = 周五
    } else {
      // 其他情况正常减1天
      prevDate.setDate(baseDate.getDate() - 1)
    }
    dates.push(prevDate)

    // 当天
    dates.push(new Date(baseDate))

    // 计算后续日期 - 特殊处理星期五和星期六
    if (baseDayOfWeek === 5) {
      // 如果基准日是星期五，添加下周一和下周二
      const nextMonday = new Date(baseDate)
      nextMonday.setDate(baseDate.getDate() + 3) // 周五 + 3天 = 周一
      dates.push(nextMonday)

      const nextTuesday = new Date(baseDate)
      nextTuesday.setDate(baseDate.getDate() + 4) // 周五 + 4天 = 周二
      dates.push(nextTuesday)
    } else if (baseDayOfWeek === 6) {
      // 如果基准日是星期六，添加下周一、下周二、下周三
      const nextMonday = new Date(baseDate)
      nextMonday.setDate(baseDate.getDate() + 2) // 周六 + 2天 = 周一
      dates.push(nextMonday)

      const nextTuesday = new Date(baseDate)
      nextTuesday.setDate(baseDate.getDate() + 3) // 周六 + 3天 = 周二
      dates.push(nextTuesday)

      const nextWednesday = new Date(baseDate)
      nextWednesday.setDate(baseDate.getDate() + 4) // 周六 + 4天 = 周三
      dates.push(nextWednesday)
    } else {
      // 其他情况正常加1天
      const nextDate = new Date(baseDate)
      nextDate.setDate(baseDate.getDate() + 1)
      dates.push(nextDate)
    }

    // 智能过滤日期：避开星期六日，除非有生产计划
    const validDates = []

    for (const date of dates) {
      const dayOfWeek = date.getDay()
      const isWeekend = dayOfWeek === 0 || dayOfWeek === 6 // 0=周日, 6=周六
      const dateStr = date.toISOString().split('T')[0]

      if (!isWeekend) {
        // 工作日直接加入
        validDates.push(dateStr)
      } else {
        // 周末需要检查是否有生产计划数据
        try {
          const result = (await request.get(planDataApiPath.value, {
            params: {
              startDate: dateStr,
              endDate: dateStr,
              machineName: planSearchForm.machineName || '',
              processName: '成型',
              page: 1,
              limit: 1000,
            },
          })) as ApiResponse

          // 解析返回的数据
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

          // 检查是否有生产计划数大于0的数据
          const hasProductionData = planData.some(
            (item: any) => item.quantity && parseFloat(item.quantity) > 0,
          )

          if (hasProductionData) {
            validDates.push(dateStr)
            formingDevLog(`周末 ${dateStr} 有生产计划，已加入范围`)
          } else {
            formingDevLog(`周末 ${dateStr} 无生产计划，已跳过`)
          }
        } catch (error) {
          console.error(`检查周末 ${dateStr} 生产数据失败:`, error)
          // 如果检查失败，为了安全起见，不加入该日期
        }
      }
    }

    // 排序并返回范围
    validDates.sort()
    const startDate = validDates[0] || ''
    const endDate = validDates[validDates.length - 1] || ''

    formingDevLog('智能日期范围:', {
      startDate,
      endDate,
      validDates,
      baseDayOfWeek: baseDayOfWeek,
      isMonday: baseDayOfWeek === 1,
      isFriday: baseDayOfWeek === 5,
      baseDate: planSearchForm.dateRange[0],
      weekDayName: ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][baseDayOfWeek],
    })

    // 如果基准日是星期六，确保包含星期一以后的数据
    if (baseDayOfWeek === 6) {
      formingDevLog('基准日是星期六，需要确保包含星期一以后的数据')
    }
    return { startDate, endDate }
  } catch (error) {
    console.error('计算智能日期范围失败:', error)
    // 如果智能算法失败，回退到原始日期范围
    const selectedRange = getSelectedDateRange()
    if (selectedRange) {
      const [startDate, endDate] = selectedRange
      return { startDate, endDate }
    }
    return { startDate: '', endDate: '' }
  }
}

/** 成型生産指示書の印刷対象外（仮設備・他用途など） */
const isExcludedFormingInstructionPrintMachine = (name: string) => {
  const n = (name || '').trim()
  return n === '成型他'
}

// 获取要生成成型生産指示書的设备列表：指定设备时只返回该设备，未指定时返回所有成型设备
const getFormingMachineNamesForPrint = async (): Promise<string[]> => {
  if (planSearchForm.machineName) {
    if (isExcludedFormingInstructionPrintMachine(planSearchForm.machineName)) {
      return []
    }
    return [planSearchForm.machineName]
  }
  try {
    const result = (await request.get('/api/master/machines', {
      params: { machine_type: '成型' },
    })) as ApiResponse
    const list: any[] = Array.isArray(result)
      ? result
      : (result?.list ?? (result?.data as any)?.list ?? [])
    return list
      .map((m: any) => m.machine_name)
      .filter(Boolean)
      .filter((name: string) => !isExcludedFormingInstructionPrintMachine(name))
      .sort((a: string, b: string) => a.localeCompare(b))
  } catch (error) {
    console.error('获取成型设备列表失败:', error)
    return []
  }
}

// 获取完整的期间数据用于打印
const getFullPlanDataForPrint = async () => {
  try {
    // 使用智能算法计算日期范围
    const { startDate, endDate } = await calculateSmartDateRange()

    if (!startDate || !endDate) {
      console.warn('无法确定日期范围')
      return []
    }

    const params = buildPlanDataQueryParams({ startDate, endDate })
    const result = (await request.get(planDataApiPath.value, {
      params,
    })) as ApiResponse

    formingDevLog('API返回结果:', result)

    const parsedList = parsePlanDataList(result)
    if (parsedList.length === 0) {
      console.warn('API返回的数据格式不是数组:', result)
      formingDevLog('尝试访问 result.data:', result.data)
    }
    return parsedList
  } catch (error) {
    console.error('获取完整计划数据失败:', error)
    return []
  }
}

// 指示書印刷プレビューを表示
const showPrintPreview = async () => {
  try {
    // 获取要生成指示書的设备列表（每台设备都生成一页）
    const machineList = await getFormingMachineNamesForPrint()
    if (machineList.length === 0) {
      ElMessage.warning('印刷対象の設備がありません')
      return
    }

    // 获取完整的期间数据（可能为空，无数据时表格显示「生産計画停止」）
    const fullPlanData = await getFullPlanDataForPrint()

    // 为每台设备生成预览内容
    const previewContents = await Promise.all(
      machineList.map(async (machineName) => {
        return await generatePrintContent(fullPlanData, machineName)
      }),
    )

    // 合并所有设备的内容
    const combinedPreviewContent = previewContents.join(
      '<div style="page-break-before: always; margin: 20px 0; border-top: 2px solid #ccc;"></div>',
    )
    printPreviewContent.value = combinedPreviewContent
    printPreviewVisible.value = true
  } catch (error) {
    console.error('预览失败:', error)
    ElMessage.error('プレビューの生成に失敗しました')
  }
}

// 设备CD缓存
const machineCdCache = new Map<string, string>()

// 生成二维码
const generateQRCode = (data: string): string => {
  // 如果数据为空，返回一个默认的占位符
  if (!data || data.trim() === '') {
    formingDevLog('产品CD为空，使用默认占位符')
    return 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjQwIiBoZWlnaHQ9IjQwIiBmaWxsPSIjRjVGNUY1Ii8+Cjx0ZXh0IHg9IjIwIiB5PSIyMCIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXNpemU9IjEwIiBmaWxsPSIjOTk5IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+TkE8L3RleHQ+Cjwvc3ZnPgo='
  }

  // 使用在线二维码生成API（提高像素并增加留白，提升可识别性）
  const qrCodeUrl = `https://api.qrserver.com/v1/create-qr-code/?size=120x120&qzone=2&format=png&data=${encodeURIComponent(
    data,
  )}`
  formingDevLog('製品CDのQRコードを生成、製品CD:', data, 'QRコードURL:', qrCodeUrl)
  return qrCodeUrl
}

// 获取设备CD
const getMachineCd = async (machineName: string) => {
  try {
    if (!machineName || machineName === '未指定設備') {
      return '未指定'
    }

    // 检查缓存
    if (machineCdCache.has(machineName)) {
      formingDevLog('从缓存获取设备CD:', machineName, '->', machineCdCache.get(machineName))
      return machineCdCache.get(machineName)!
    }

    formingDevLog('正在查询设备CD，设备名:', machineName)

    const result = (await request.get('/api/master/machines', {
      params: {
        keyword: machineName,
        pageSize: 100,
      },
    })) as ApiResponse | unknown[]

    formingDevLog('设备查询结果:', result)

    const list: any[] = Array.isArray(result) ? result : (result?.list ?? (result?.data as any)?.list ?? [])
    if (list.length > 0) {
      // 精确匹配设备名
      const matchedMachine = list.find((machine: any) => machine.machine_name === machineName)

      if (matchedMachine?.machine_cd) {
        formingDevLog('找到匹配的设备CD:', matchedMachine.machine_cd)
        // 缓存结果
        machineCdCache.set(machineName, matchedMachine.machine_cd)
        return matchedMachine.machine_cd
      }

      // 如果没有精确匹配，使用第一个结果
      const first = list[0]
      if (first?.machine_cd) {
        formingDevLog('使用第一个结果的设备CD:', first.machine_cd)
        machineCdCache.set(machineName, first.machine_cd)
        return first.machine_cd
      }
    }

    formingDevLog('未找到设备CD，设备名:', machineName)
    // 缓存未找到的结果
    machineCdCache.set(machineName, '未指定')
    return '未指定'
  } catch (error) {
    console.error('获取设备CD失败:', error)
    // 缓存错误结果
    machineCdCache.set(machineName, '未指定')
    return '未指定'
  }
}

// 生成打印内容
const generatePrintContent = async (planData: any[], machineName?: string) => {
  // 使用日本时区获取当前日期
  const currentDate = JapanDateUtils.formatDate(JapanDateUtils.getTodayString())

  // 只显示筛选的基准日，不使用智能算法扩展的日期范围
  // 使用筛选条件的基准日（开始日期）
  const today = JapanDateUtils.formatDate(getSelectedBaseDate())

  // 获取设备CD
  const machineCd = machineName ? await getMachineCd(machineName) : '未指定'

  return `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>成型生産指示書 - ${machineName || '全設備'}</title>
      <style>
        @page {
          size: A5 landscape;
          margin: 8mm;
          /* 打印详细设定 */
          marks: none; /* 不显示裁剪标记 */
          bleed: 0mm; /* 无出血 */
          /* 单面打印 */
          page-break-after: auto;
        }

        /* 打印媒体查询 - 确保打印样式正确应用 */
        @media print {
          @page {
            size: A5 landscape;
            margin: 8mm;
            marks: none;
            bleed: 0mm;
          }

          /* 确保打印时不显示背景色（除非需要） */
          * {
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
          }
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

        .shift-table .shift-time {
          width: 12%;
        }

        .shift-table .product-name {
          width: 12%;
        }

        .shift-table .production-qty {
          width: 17%;
        }

        .shift-table .recorder {
          width: 9%;
        }

        .shift-table .remarks {
          width: 10%;
        }

        .shift-table .notch {
          width: 8%;
        }

        .shift-table .bending {
          width: 8%;
        }

        .shift-table .chamfering {
          width: 8%;
        }

        .shift-table .setup {
          width: 8%;
        }

        .shift-table .yellow-box {
          width: 8%;
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

        /* 指定生産品種行：浅黄色背景 */
        .product-highlight-row td {
          background-color: #fffde7 !important;
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
            <div class="print-title">成型生産指示書</div>
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
                <th class="remarks">備考</th>
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
                  .sort(sortByPlanDateAndOperatorAsc)
                  .slice(0, 4) // 只显示前4行数据

                // 如果没有数据，在表格里显示「生産計画停止」
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
                    formingDevLog('产品数据验证:', {
                      product_cd: plan.product_cd,
                      product_name: plan.product_name,
                      plan_date: plan.plan_date,
                      machine_name: plan.machine_name,
                    })

                    const highlightClass = isHighlightProduct(plan.product_name)
                      ? 'product-highlight-row'
                      : ''
                    const rowClass = [isBaseDate ? 'highlighted-row' : '', highlightClass]
                      .filter(Boolean)
                      .join(' ')
                    return `
                        <tr class="${rowClass}">
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
                          <td>${plan.remarks ? plan.remarks : isHighlightProduct(plan.product_name) ? '新聞紙をかける' : ''}</td>
                        </tr>
                      `
                  })
                  .join('')
              })()}
            </tbody>
        </table>
        </div>

        <!-- 勤務時間帯表格 -->
        <div class="shift-table-container">
          <div class="section-divider">
            <span class="section-title">記入項目</span>
          </div>
          <table class="shift-table">
            <thead>
              <tr>
                <th class="shift-time">勤務時間帯</th>
                <th class="product-name">製品名</th>
                <th class="production-qty">生産数</th>
                <th class="recorder">記入者</th>
                <th class="remarks">備考</th>
                <th class="notch">切欠き</th>
                <th class="bending">曲げ</th>
                <th class="chamfering">面取</th>
                <th class="setup">段取調整</th>
                <th class="yellow-box">黄箱</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>15:00--17:00</td>
                <td></td>
                <td>---</td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
              </tr>
              <tr>
                <td>17:00--19:00</td>
                <td></td>
                <td>---</td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
              </tr>
              <tr>
                <td>19:00--21:00</td>
                <td></td>
                <td>---</td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
              </tr>
              <tr>
                <td>21:00--06:00</td>
                <td></td>
                <td>---</td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
              </tr>
              <tr>
                <td>06:00--08:00</td>
                <td></td>
                <td>---</td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
              </tr>
              <tr>
                <td>08:00--15:00</td>
                <td></td>
                <td>---</td>
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

          <!-- 底部时间范围行 -->
          <div class="time-ranges-row">
            <span><span class="time-text">15:00~15:10</span> <span class="checkbox">☐</span></span>
            <span><span class="time-text">17:00~17:10</span> <span class="checkbox">☐</span></span>
            <span><span class="time-text">21:00~21:10</span> <span class="checkbox">☐</span></span>
            <span><span class="time-text">23:00~23:10</span> <span class="checkbox">☐</span></span>
            <span><span class="time-text">01:00~02:00</span> <span class="checkbox">☐</span></span>
            <span><span class="time-text">04:00~04:10</span> <span class="checkbox">☐</span></span>
            <span><span class="time-text">06:00~06:10</span> <span class="checkbox">☐</span></span>
            <span><span class="time-text">10:00~10:10</span> <span class="checkbox">☐</span></span>
            <span><span class="time-text">12:00~13:00</span> <span class="checkbox">☐</span></span>
          </div>
        </div>
      </div>
    </body>
    </html>
  `
}

// 成型生産指示書：指定生産品種行使用浅黄色背景
const HIGHLIGHT_PRODUCT_NAMES = new Set([
  '900B FR',
  '900B RR',
  '900B 対米',
  '410D CTR',
  '410D FR1',
  '410D FR2',
  '410D RR',
])
const isHighlightProduct = (name: string | null | undefined): boolean => {
  if (!name || typeof name !== 'string') return false
  const trimmed = name.trim()
  return HIGHLIGHT_PRODUCT_NAMES.has(trimmed)
}

// 表格行类名：指定生産品種行浅黄色背景
const tableRowClassName = ({ row }: { row: { product_name?: string } }) => {
  return isHighlightProduct(row?.product_name) ? 'product-highlight-row' : ''
}

// 能率数据缓存（设备名+产品名 -> efficiency_rate）
const efficiencyCache = new Map<string, number>()

// 获取设备能率数据并建立缓存
const loadEfficiencyData = async () => {
  try {
    // 清空缓存
    efficiencyCache.clear()

    // 获取所有能率数据（不分页，获取全部）
    const result = (await request.get('/api/master/equipment-efficiency', {
      params: {
        page: 1,
        limit: 10000,
      },
    })) as ApiResponse

    const dataList = (result.data as { list?: unknown[] })?.list
    if (result.success && Array.isArray(dataList)) {
      // 建立映射表：machines_name + product_name -> efficiency_rate
      dataList.forEach((item: any) => {
        if (item.machines_name && item.product_name) {
          const key = `${item.machines_name}|${item.product_name}`
          const efficiencyRate = parseFloat(item.efficiency_rate) || 0
          efficiencyCache.set(key, efficiencyRate)
        }
      })
      formingDevLog('能率データの読み込み成功、合計', efficiencyCache.size, '件のレコード')
    } else {
      console.warn('能率数据格式不正确:', result)
    }
  } catch (error) {
    console.error('获取能率数据失败:', error)
    // 如果获取失败，清空缓存，使用默认计算方式
    efficiencyCache.clear()
  }
}

// 根据设备名和产品名获取能率
const getEfficiencyRate = (machineName: string, productName: string): number | null => {
  if (!machineName || !productName) {
    return null
  }
  const key = `${machineName}|${productName}`
  return efficiencyCache.has(key) ? efficiencyCache.get(key)! : null
}

// ========================================
// 段取予定表印刷関連
// ========================================

/**
 * 段取予定表を印刷
 * 生産計画データを取得し、段取予定表を生成して印刷する
 */
const printSetupSchedule = async () => {
  printingSetupSchedule.value = true
  try {
    // 能率データを事前にロード
    await loadEfficiencyData()

    // 期間内の全データを取得
    const fullPlanData = await getFullPlanDataForPrint()

    if (fullPlanData.length === 0) {
      ElMessage.warning('印刷する計画データがありません')
      printingSetupSchedule.value = false
      return
    }

    // 生成数据并构建打印用HTML
    const data = await generateSetupScheduleContent(fullPlanData)
    const printContent = buildSetupSchedulePrintHtml(data)

    // 使用隐藏的iframe进行直接打印（A4横向，单面）
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

    // 防止重复打印的标志
    let hasPrinted = false

    // 打印函数
    const doPrint = () => {
      if (hasPrinted) return
      hasPrinted = true

      try {
        const iframeWindow = iframe.contentWindow
        if (iframeWindow && iframeDoc.body) {
          // 直接调用打印，浏览器会自动应用@page样式（A4横向）
          iframeWindow.focus()
          iframeWindow.print()

          // 打印完成后移除iframe
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

    // 等待内容加载完成后直接打印
    iframe.onload = () => {
      setTimeout(doPrint, 500)
    }

    // 如果onload没有触发，也尝试打印（某些浏览器可能不会触发onload）
    setTimeout(doPrint, 1500)
  } catch (error) {
    console.error('段取予定表印刷失败:', error)
    ElMessage.error('段取予定表の印刷に失敗しました')
    printingSetupSchedule.value = false
  }
}

/** 段取予定をプレビュー（編集可能）。編集後に印刷できる */
const openSetupSchedulePreview = async () => {
  printingSetupSchedule.value = true
  try {
    await loadEfficiencyData()
    const fullPlanData = await getFullPlanDataForPrint()
    if (fullPlanData.length === 0) {
      ElMessage.warning('印刷する計画データがありません')
      printingSetupSchedule.value = false
      return
    }
    const data = await generateSetupScheduleContent(fullPlanData)
    setupSchedulePreviewMeta.value = {
      productionDate: data.productionDate,
      totalQuantity: data.totalQuantity,
      currentDateTime: data.currentDateTime,
    }
    setupSchedulePreviewTableRows.value = JSON.parse(JSON.stringify(data.tableRows))
    setupSchedulePreviewVisible.value = true
  } catch (e) {
    console.error(e)
    ElMessage.error('プレビューの読み込みに失敗しました')
  } finally {
    printingSetupSchedule.value = false
  }
}

/** 操業度(進捗)：プレビュー編集後の表示を整数に揃える */
const formatOperationVarianceToOneDecimal = (row: { operationVariance?: string | number }) => {
  const v = row.operationVariance
  if (v === undefined || v === null || v === '') return
  const n = Number(v)
  if (!isNaN(n) && Number.isFinite(n)) row.operationVariance = String(Math.round(n))
}

const formatPlannedWorkingHours = (v: unknown): string => {
  const n = Number(v)
  if (!Number.isFinite(n) || n === 0) return ''
  return n.toFixed(1)
}

const plannedHoursLevelClass = (v: unknown): string => {
  const n = Number(v)
  if (!Number.isFinite(n) || n === 0) return 'planned-hours-empty'
  if (n < 8) return 'planned-hours-low'
  if (n < 16) return 'planned-hours-mid'
  if (n < 22.5) return 'planned-hours-high'
  return 'planned-hours-very-high'
}

const hasNextProduct = (name: unknown): boolean => {
  const s = (name ?? '').toString().trim()
  return s !== ''
}

/** プレビューダイアログから印刷（編集後のデータで印刷） */
const printFromSetupSchedulePreview = () => {
  const meta = setupSchedulePreviewMeta.value
  if (!meta || !setupSchedulePreviewTableRows.value.length) {
    ElMessage.warning('印刷するデータがありません')
    return
  }
  const printContent = buildSetupSchedulePrintHtml({
    ...meta,
    tableRows: setupSchedulePreviewTableRows.value,
  })
  const iframe = document.createElement('iframe')
  iframe.style.cssText = 'position:fixed;right:0;bottom:0;width:0;height:0;border:0;visibility:hidden'
  document.body.appendChild(iframe)
  const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document
  if (!iframeDoc) {
    document.body.removeChild(iframe)
    return
  }
  iframeDoc.open()
  iframeDoc.write(printContent)
  iframeDoc.close()
  try {
    iframe.contentWindow?.focus()
    iframe.contentWindow?.print()
  } catch (e) {
    console.error(e)
    ElMessage.error('印刷の実行に失敗しました')
  }
  setTimeout(() => {
    if (document.body.contains(iframe)) document.body.removeChild(iframe)
  }, 1000)
}

// ==================== 工具函数和缓存 ====================

// 日期工具类（日本时区）
class JapanDateUtils {
  // 格式化日期为 YYYY-MM-DD
  static normalizeDate(dateStr: string): string {
    return dateStr.split(' ')[0].split('T')[0]
  }

  // 获取日本时区的日期组件
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

  // 获取日本时区的日期字符串（YYYY-MM-DD格式）
  static getDateString(dateInput?: string | Date): string {
    const parts = this.getDateParts(dateInput)
    return `${parts.year}-${parts.month}-${parts.day}`
  }

  // 获取星期几（带缓存，日本时区）
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

  // 判断是否是星期日
  static isSunday(dateInput: string | Date): boolean {
    return this.getDayOfWeek(dateInput) === 0
  }

  // 判断是否是星期六
  static isSaturday(dateInput: string | Date): boolean {
    return this.getDayOfWeek(dateInput) === 6
  }

  // 计算下一个星期一（从星期六）
  static getNextMonday(dateStr: string): string {
    const [year, month, day] = dateStr.split('-').map(Number)
    const date = new Date(year, month - 1, day)
    date.setDate(date.getDate() + 2) // 星期六+2天=星期一
    const result = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
    formingDevLog(`计算下一个星期一: ${dateStr} (星期六) -> ${result} (星期一)`)
    return result
  }

  // 获取当前日本时区的日期对象
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
    // 格式: "MM/DD/YYYY, HH:MM:SS"
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

  // 获取当前日本时区的日期字符串（YYYY-MM-DD格式）
  static getTodayString(): string {
    return this.getDateString()
  }

  // 获取当前日本时区的日期时间
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

  // 格式化日期为 YYYY/MM/DD
  static formatDate(dateStr: string, separator: string = '/'): string {
    const parts = this.getDateParts(dateStr)
    return `${parts.year}${separator}${parts.month}${separator}${parts.day}`
  }
}

// 产品排序工具类
class ProductSortUtils {
  // 标准化operator
  private static normalizeOperator(operator: any): string {
    return (operator || '').toString().trim()
  }

  // 比较两个operator
  private static compareOperators(operatorA: string, operatorB: string): number {
    // 如果都为空，保持原顺序
    if (operatorA === '' && operatorB === '') return 0
    // 如果A为空，B不为空，A排在后面
    if (operatorA === '') return 1
    // 如果B为空，A不为空，B排在后面
    if (operatorB === '') return -1

    // 尝试转换为数字比较
    const numA = Number(operatorA)
    const numB = Number(operatorB)

    // 如果都是数字，按数字比较
    if (!isNaN(numA) && !isNaN(numB)) {
      return numA - numB
    }

    // 否则按字符串比较
    return operatorA.localeCompare(operatorB, 'ja')
  }

  // 按operator排序产品
  static sortByOperator(products: any[]): any[] {
    return [...products].sort((a, b) => {
      const operatorA = this.normalizeOperator(a.operator)
      const operatorB = this.normalizeOperator(b.operator)
      return this.compareOperators(operatorA, operatorB)
    })
  }
}

// 数据索引工具类（用于优化查找性能）
class DataIndexUtils {
  // 构建日期索引
  static buildDateIndex(data: any[]): Map<string, any[]> {
    const index = new Map<string, any[]>()

    data.forEach((item) => {
      const date = JapanDateUtils.normalizeDate(item.plan_date || '')
      if (!index.has(date)) {
        index.set(date, [])
      }
      index.get(date)!.push(item)
    })

    // 对每个日期的产品按operator排序
    index.forEach((products, date) => {
      const validProducts = products.filter((p) => parseInt(p.quantity) > 0)
      if (validProducts.length > 0) {
        index.set(date, ProductSortUtils.sortByOperator(validProducts))
      }
    })

    return index
  }

  // 查找指定日期的有效产品（quantity > 0, 非星期日）
  static findValidProducts(dateIndex: Map<string, any[]>, date: string): any[] {
    const products = dateIndex.get(date) || []
    const dayOfWeek = JapanDateUtils.getDayOfWeek(date)

    formingDevLog(`查找日期 ${date} 的有效产品: 星期${dayOfWeek}, 原始产品数量: ${products.length}`)

    // 排除星期日，quantity已经在构建索引时过滤了
    if (dayOfWeek === 0) {
      formingDevLog(`日期 ${date} 是星期日，返回空数组`)
      return []
    }

    const validProducts = products.filter((p) => parseInt(p.quantity) > 0)
    formingDevLog(`日期 ${date} 的有效产品数量: ${validProducts.length}`)
    return validProducts
  }

  // 查找指定日期之后的有效日期列表（排除星期日）
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
        // 排除星期日 (0) 和星期六 (6)
        return dayOfWeek !== 0 && dayOfWeek !== 6
      })
      .sort()

    formingDevLog(
      `查找有效日期: startDate=${startDate}, excludeStartDate=${excludeStartDate}, 找到的日期:`,
      dates,
    )
    return dates
  }
}

// ==================== 设备运行时间工具函数 ====================

// 设备运行时间缓存（machine_cd + date -> work times）
const machineWorkTimesCache = new Map<string, any[]>()

// 获取设备运行时间段（单个设备单个日期）
const getMachineWorkTimes = async (machineCd: string, date: string): Promise<any[]> => {
  try {
    if (!machineCd || !date) {
      return []
    }

    // 检查缓存
    const cacheKey = `${machineCd}|${date}`
    if (machineWorkTimesCache.has(cacheKey)) {
      return machineWorkTimesCache.get(cacheKey)!
    }

    const result = (await request.get('/api/schedule', {
      params: {
        machine_cd: machineCd,
        from_date: date,
        to_date: date,
        limit: 100,
      },
    })) as ApiResponse

    if (result.success && Array.isArray((result.data as { list?: unknown[] })?.list)) {
      const workTimes = ((result.data as { list?: any[] })?.list ?? []).map((item: any) => ({
        start_time: item.start_time,
        end_time: item.end_time,
      }))
      machineWorkTimesCache.set(cacheKey, workTimes)
      return workTimes
    }

    return []
  } catch (error) {
    console.error('获取设备运行时间失败:', error)
    return []
  }
}

// 批量获取设备运行时间（优化：减少API调用）
const batchGetMachineWorkTimes = async (
  machineCds: string[],
  dates: string[],
): Promise<Map<string, Map<string, any[]>>> => {
  const result = new Map<string, Map<string, any[]>>()

  // 去重
  const uniqueMachineCds = [...new Set(machineCds.filter((cd) => cd))]
  const uniqueDates = [...new Set(dates.filter((d) => d))]

  if (uniqueMachineCds.length === 0 || uniqueDates.length === 0) {
    return result
  }

  // 计算日期范围
  const dateRange = {
    min: uniqueDates[0],
    max: uniqueDates[uniqueDates.length - 1],
  }

  // 为每个设备批量获取日期范围内的运行时间
  const fetchPromises = uniqueMachineCds.map(async (machineCd) => {
    const dateMap = new Map<string, any[]>()
    const deviceNeedFetch: string[] = [] // 该设备需要获取的日期

    // 检查缓存中已有的数据
    for (const date of uniqueDates) {
      const cacheKey = `${machineCd}|${date}`
      if (machineWorkTimesCache.has(cacheKey)) {
        dateMap.set(date, machineWorkTimesCache.get(cacheKey)!)
      } else {
        deviceNeedFetch.push(date)
      }
    }

    // 如果有需要获取的数据，批量请求（按日期范围）
    if (deviceNeedFetch.length > 0) {
      try {
        const fetchResult = (await request.get('/api/schedule', {
          params: {
            machine_cd: machineCd,
            from_date: dateRange.min,
            to_date: dateRange.max,
            limit: 1000, // 增加限制以获取更多数据
          },
        })) as ApiResponse

        const dataList = (fetchResult.data as { list?: any[] })?.list ?? []
        if (fetchResult.success && Array.isArray(dataList)) {
          // 按日期分组
          const workTimesByDate = new Map<string, any[]>()
          dataList.forEach((item: any) => {
            const itemDate = item.plan_date || item.date || ''
            if (itemDate) {
              const normalizedDate = JapanDateUtils.normalizeDate(itemDate)
              if (!workTimesByDate.has(normalizedDate)) {
                workTimesByDate.set(normalizedDate, [])
              }
              workTimesByDate.get(normalizedDate)!.push({
                start_time: item.start_time,
                end_time: item.end_time,
              })
            }
          })

          // 更新缓存和结果
          workTimesByDate.forEach((workTimes: any[], date: string) => {
            const cacheKey = `${machineCd}|${date}`
            machineWorkTimesCache.set(cacheKey, workTimes)
            dateMap.set(date, workTimes)
          })
        }
      } catch (error) {
        console.error(`批量获取设备 ${machineCd} 运行时间失败:`, error)
      }
    }

    result.set(machineCd, dateMap)
  })

  await Promise.all(fetchPromises)
  return result
}

// 判断时间点是否在运行时间段内
const isInWorkTime = (time: Date, workTimes: any[]): boolean => {
  if (!workTimes || workTimes.length === 0) {
    // 如果没有运行时间配置，默认全天运行
    return true
  }

  const currentHour = time.getHours()
  const currentMinute = time.getMinutes()
  const currentTimeMinutes = currentHour * 60 + currentMinute

  for (const workTime of workTimes) {
    const [startHour, startMinute] = workTime.start_time.split(':').map(Number)
    const [endHour, endMinute] = workTime.end_time.split(':').map(Number)
    const startTimeMinutes = startHour * 60 + startMinute
    const endTimeMinutes = endHour * 60 + endMinute

    if (startTimeMinutes <= endTimeMinutes) {
      // 不跨天的情况（如 08:00 - 17:00）
      if (currentTimeMinutes >= startTimeMinutes && currentTimeMinutes < endTimeMinutes) {
        return true
      }
    } else {
      // 跨天的情况（如 21:00 - 06:00）
      if (currentTimeMinutes >= startTimeMinutes || currentTimeMinutes < endTimeMinutes) {
        return true
      }
    }
  }

  return false
}

// 获取下一个运行时间段的开始时间
const getNextWorkTimeStart = (time: Date, workTimes: any[]): Date | null => {
  if (!workTimes || workTimes.length === 0) {
    return null
  }

  const currentHour = time.getHours()
  const currentMinute = time.getMinutes()
  const currentTimeMinutes = currentHour * 60 + currentMinute

  // 按开始时间排序
  const sortedWorkTimes = [...workTimes].sort((a, b) => {
    const [aHour, aMinute] = a.start_time.split(':').map(Number)
    const [bHour, bMinute] = b.start_time.split(':').map(Number)
    return aHour * 60 + aMinute - (bHour * 60 + bMinute)
  })

  // 查找下一个运行时间段
  for (const workTime of sortedWorkTimes) {
    const [startHour, startMinute] = workTime.start_time.split(':').map(Number)
    const startTimeMinutes = startHour * 60 + startMinute

    if (startTimeMinutes > currentTimeMinutes) {
      // 找到下一个运行时间段（当天）
      const nextTime = new Date(time)
      nextTime.setHours(startHour, startMinute, 0, 0)
      return nextTime
    }
  }

  // 如果当天没有下一个运行时间段，返回第二天第一个运行时间段的开始
  if (sortedWorkTimes.length > 0) {
    const firstWorkTime = sortedWorkTimes[0]
    const [startHour, startMinute] = firstWorkTime.start_time.split(':').map(Number)
    const nextTime = new Date(time)
    nextTime.setDate(nextTime.getDate() + 1)
    nextTime.setHours(startHour, startMinute, 0, 0)
    return nextTime
  }

  return null
}

// 计算在指定时间段内设备不运行的时间（小时）
// 从起始时间开始，累加指定小时数（只计算运行时间），返回不运行的时间总和
// 优化：支持传入预加载的运行时间数据，避免重复API调用
const calculateNonWorkTime = async (
  startDate: string, // YYYY-MM-DD
  startTime: string, // HH:mm
  workHours: number, // 需要累加的运行时间（小时）
  machineCd: string,
  preloadedWorkTimes?: Map<string, any[]>, // 预加载的运行时间数据（可选）
): Promise<number> => {
  // 如果没有设备代码，返回0（假设全天运行）
  if (!machineCd) {
    return 0
  }

  // 创建起始时间
  let currentTime = new Date(`${startDate}T${startTime}:00`)
  let totalNonWorkTime = 0 // 不运行时间总和（小时）

  // 获取设备运行时间（可能需要获取多天的数据，因为可能跨天）
  const workTimesMap = new Map<string, any[]>()

  // 获取起始日期和可能需要的后续日期的运行时间
  const datesToCheck: string[] = [startDate]
  // 预估最多需要检查的天数（假设最多累加1000小时，即约42天）
  const maxDays = Math.ceil(workHours / 24) + 1
  for (let i = 1; i <= maxDays; i++) {
    const nextDate = new Date(startDate)
    nextDate.setDate(nextDate.getDate() + i)
    datesToCheck.push(nextDate.toISOString().split('T')[0])
  }

  // 如果提供了预加载数据，优先使用
  if (preloadedWorkTimes) {
    datesToCheck.forEach((date) => {
      const workTimes = preloadedWorkTimes.get(date)
      if (workTimes && workTimes.length > 0) {
        workTimesMap.set(date, workTimes)
      }
    })
  } else {
    // 如果没有预加载数据，逐个获取（保持向后兼容）
    for (const date of datesToCheck) {
      const workTimes = await getMachineWorkTimes(machineCd, date)
      if (workTimes.length > 0) {
        workTimesMap.set(date, workTimes)
      }
    }
  }

  // 如果没有运行时间配置，默认全天运行，不运行时间为0
  if (workTimesMap.size === 0) {
    return 0
  }

  // 累加运行时间，同时计算不运行的时间
  let remainingWorkHours = workHours
  const maxIterations = 10000 // 防止无限循环
  let iterations = 0

  while (remainingWorkHours > 0 && iterations < maxIterations) {
    iterations++

    // 获取当前日期字符串
    const currentDateStr = currentTime.toISOString().split('T')[0]
    const currentHour = currentTime.getHours()
    const currentMinute = currentTime.getMinutes()
    const currentTimeMinutes = currentHour * 60 + currentMinute

    // 获取当前日期的运行时间
    const workTimes = workTimesMap.get(currentDateStr) || []

    // 如果没有运行时间配置，默认全天运行
    if (workTimes.length === 0) {
      // 直接累加剩余运行时间，没有不运行时间
      currentTime.setTime(currentTime.getTime() + remainingWorkHours * 60 * 60 * 1000)
      remainingWorkHours = 0
      break
    }

    // 查找当前时间所在的运行时间段
    let currentWorkTime: any = null
    for (const workTime of workTimes) {
      const [startHour, startMinute] = workTime.start_time.split(':').map(Number)
      const [endHour, endMinute] = workTime.end_time.split(':').map(Number)
      const startTimeMinutes = startHour * 60 + startMinute
      const endTimeMinutes = endHour * 60 + endMinute

      let isInRange = false
      if (startTimeMinutes <= endTimeMinutes) {
        // 不跨天的情况
        isInRange = currentTimeMinutes >= startTimeMinutes && currentTimeMinutes < endTimeMinutes
      } else {
        // 跨天的情况
        isInRange = currentTimeMinutes >= startTimeMinutes || currentTimeMinutes < endTimeMinutes
      }

      if (isInRange) {
        currentWorkTime = workTime
        break
      }
    }

    if (currentWorkTime) {
      // 当前在运行时间段内
      const [startHour, startMinute] = currentWorkTime.start_time.split(':').map(Number)
      const [endHour, endMinute] = currentWorkTime.end_time.split(':').map(Number)
      const startTimeMinutes = startHour * 60 + startMinute
      const endTimeMinutes = endHour * 60 + endMinute

      // 计算到运行时间段结束还有多少分钟
      let minutesToEnd: number
      if (startTimeMinutes <= endTimeMinutes) {
        // 不跨天
        minutesToEnd = endTimeMinutes - currentTimeMinutes
      } else {
        // 跨天
        if (currentTimeMinutes >= startTimeMinutes) {
          // 在当天部分
          minutesToEnd = 24 * 60 - currentTimeMinutes + endTimeMinutes
        } else {
          // 在第二天部分
          minutesToEnd = endTimeMinutes - currentTimeMinutes
        }
      }

      const hoursToEnd = minutesToEnd / 60

      if (remainingWorkHours <= hoursToEnd) {
        // 剩余运行时间不足一个运行时间段，直接累加
        currentTime.setTime(currentTime.getTime() + remainingWorkHours * 60 * 60 * 1000)
        remainingWorkHours = 0
        break
      } else {
        // 累加到运行时间段结束
        currentTime.setTime(currentTime.getTime() + minutesToEnd * 60 * 1000)
        remainingWorkHours -= hoursToEnd
      }
    } else {
      // 当前不在运行时间段内，需要跳到下一个运行时间段的开始
      const nextWorkTimeStart = getNextWorkTimeStart(currentTime, workTimes)

      if (nextWorkTimeStart) {
        // 计算到下一个运行时间段开始的不运行时间
        const nonWorkMinutes = (nextWorkTimeStart.getTime() - currentTime.getTime()) / (60 * 1000)
        const nonWorkHours = nonWorkMinutes / 60
        totalNonWorkTime += nonWorkHours

        // 跳转到下一个运行时间段开始
        currentTime = nextWorkTimeStart
      } else {
        // 当天没有更多运行时间段，跳到下一天
        const nextDay = new Date(currentTime)
        nextDay.setDate(nextDay.getDate() + 1)
        nextDay.setHours(0, 0, 0, 0)

        // 计算到第二天0点的不运行时间
        const nonWorkMinutes = (nextDay.getTime() - currentTime.getTime()) / (60 * 1000)
        const nonWorkHours = nonWorkMinutes / 60
        totalNonWorkTime += nonWorkHours

        currentTime = nextDay
      }
    }
  }

  return totalNonWorkTime
}

const getPreviousWorkingDate = (dateStr: string): string => {
  const date = new Date(`${dateStr}T12:00:00`)
  for (let i = 0; i < 7; i++) {
    date.setDate(date.getDate() - 1)
    const day = date.getDay()
    if (day !== 0 && day !== 6) {
      return date.toISOString().split('T')[0]
    }
  }
  return dateStr
}

const getBaselineStartDate = (
  dateStr: string,
  machineData: any[],
  dateIndex: Map<string, any[]>,
  allPlanData?: any[], // 新增参数：所有设备的计划数据
): string => {
  const baseDate = new Date(`${dateStr}T12:00:00`)

  // 如果指定日是星期一，检查前一周星期五和星期六的生产情况
  if (baseDate.getDay() === 1) {
    const friday = new Date(baseDate)
    friday.setDate(baseDate.getDate() - 3) // 回到前一周星期五
    const fridayStr = friday.toISOString().split('T')[0]

    const saturday = new Date(baseDate)
    saturday.setDate(baseDate.getDate() - 2) // 回到前一周星期六
    const saturdayStr = saturday.toISOString().split('T')[0]

    formingDevLog(
      `检查星期一 ${dateStr} 的前一周星期五 ${fridayStr} 和星期六 ${saturdayStr} 的生产情况`,
    )

    // 检查星期五的生产情况
    let hasFridayProduction = false
    let isFridayProductionStop = false

    if (allPlanData && allPlanData.length > 0) {
      // 使用所有设备的数据检查前一周星期五的生产情况
      const fridayProducts = allPlanData.filter((item: any) => {
        const itemDate = JapanDateUtils.normalizeDate(item.plan_date || '')
        return itemDate === fridayStr
      })

      // 检查星期五是否有有效的生产数据（数量 > 0）
      hasFridayProduction = fridayProducts.some((product: any) => {
        const quantity = parseInt(product.quantity) || 0
        return quantity > 0
      })

      // 检查星期五是否是'生产停止'（没有生产数据或数量为0）
      isFridayProductionStop = !hasFridayProduction

      formingDevLog(
        `前一周星期五 ${fridayStr} 生产情况:`,
        `有生产=${hasFridayProduction}, 生产停止=${isFridayProductionStop}`,
        '产品数据:',
        fridayProducts.length > 0 ? `找到${fridayProducts.length}条记录` : '无数据',
      )
    } else {
      // 回退到单设备检查（兼容性）
      const fridayProducts = DataIndexUtils.findValidProducts(dateIndex, fridayStr)
      hasFridayProduction = fridayProducts.some((product: any) => {
        const quantity = parseInt(product.quantity) || 0
        return quantity > 0
      })
      isFridayProductionStop = !hasFridayProduction

      formingDevLog(
        `前一周星期五 ${fridayStr} 生产情况（单设备检查）:`,
        `有生产=${hasFridayProduction}, 生产停止=${isFridayProductionStop}`,
        '产品数据:',
        fridayProducts,
      )
    }

    // 检查星期六的生产情况
    let hasSaturdayProduction = false

    if (allPlanData && allPlanData.length > 0) {
      // 使用所有设备的数据检查前一周星期六是否有生产
      const saturdayProducts = allPlanData.filter((item: any) => {
        const itemDate = JapanDateUtils.normalizeDate(item.plan_date || '')
        return itemDate === saturdayStr
      })

      hasSaturdayProduction = saturdayProducts.some((product: any) => {
        const quantity = parseInt(product.quantity) || 0
        return quantity > 0
      })

      formingDevLog(
        `前一周星期六 ${saturdayStr} 有生产（检查所有设备）:`,
        hasSaturdayProduction,
        '产品数据:',
        saturdayProducts.length > 0 ? `找到${saturdayProducts.length}条记录` : '无数据',
      )
    } else {
      // 回退到单设备检查（兼容性）
      const saturdayProducts = DataIndexUtils.findValidProducts(dateIndex, saturdayStr)
      hasSaturdayProduction = saturdayProducts.some((product: any) => {
        const quantity = parseInt(product.quantity) || 0
        return quantity > 0
      })

      formingDevLog(
        `前一周星期六 ${saturdayStr} 有生产（单设备检查）:`,
        hasSaturdayProduction,
        '产品数据:',
        saturdayProducts,
      )
    }

    // 新增逻辑：如果星期五是'生产停止'且星期六没有生产数据，则使用星期五作为基准日期
    if (isFridayProductionStop && !hasSaturdayProduction) {
      formingDevLog(
        `星期五是生产停止且星期六没有生产数据，基准日期设为星期五: ${fridayStr}，开始时间为15:00`,
      )
      return fridayStr
    }

    // 原有逻辑：如果星期六有生产，使用星期六作为基准日期
    if (hasSaturdayProduction) {
      formingDevLog(`星期一且前一周星期六有生产，基准日期设为星期六: ${saturdayStr}`)
      return saturdayStr
    }
  }

  // 其他情况使用前一个工作日
  const previousWorkingDate = getPreviousWorkingDate(dateStr)
  formingDevLog(`使用前一个工作日作为基准: ${previousWorkingDate}`)
  return previousWorkingDate
}

// 设备运行时间段配置缓存
const workTimeConfigCache = new Map<string, any>()

// 根据设备运行时间配置调整段取開始時間（使用设备名称查询）
const adjustSetupTimeByWorkConfig = async (setupTime: Date, machineName: string): Promise<Date> => {
  if (!machineName) {
    formingDevLog('设备名称为空，跳过时间调整')
    return setupTime
  }

  try {
    formingDevLog(`开始获取设备 ${machineName} 的运行时间配置`)

    // 获取设备运行时间配置
    let workConfig = workTimeConfigCache.get(machineName)
    formingDevLog(`从缓存中获取设备 ${machineName} 配置:`, workConfig)

    if (!workConfig) {
      formingDevLog(`缓存中没有设备 ${machineName} 的配置，开始从API获取`)
      const response = (await request.get(`/api/machine-work-time-config/work-time-config`)) as ApiResponse | unknown[]
      formingDevLog(`API响应:`, response)

      // 处理不同的响应格式
      const configs: any[] = Array.isArray(response)
        ? (response as any[])
        : Array.isArray((response as ApiResponse)?.data)
          ? ((response as ApiResponse).data as any[])
          : []
      formingDevLog(`解析后的配置数据:`, configs)

      if (configs.length > 0) {
        formingDevLog(`获取到 ${configs.length} 条设备配置数据`)
        // 缓存所有配置（使用machine_name作为key）
        configs.forEach((config: any) => {
          formingDevLog(`缓存设备配置: ${config.machine_name}`, config)
          workTimeConfigCache.set(config.machine_name, config)
        })
        workConfig = workTimeConfigCache.get(machineName)
        formingDevLog(`重新从缓存获取设备 ${machineName} 配置:`, workConfig)
      } else {
        formingDevLog(`没有获取到任何设备配置数据`)
      }
    }

    if (!workConfig) {
      formingDevLog(`未找到设备 ${machineName} 的运行时间配置，跳过时间调整`)
      formingDevLog(`当前缓存中的所有设备:`, Array.from(workTimeConfigCache.keys()))
      return setupTime
    }

    formingDevLog(`设备 ${machineName} 的运行时间配置:`, workConfig)

    const adjustedTime = new Date(setupTime)
    let currentHour = adjustedTime.getHours()
    let currentMinute = adjustedTime.getMinutes()
    let currentTimeInMinutes = currentHour * 60 + currentMinute

    formingDevLog(
      `原始段取開始時間: ${adjustedTime.toLocaleString('ja-JP')} (${currentHour}:${String(currentMinute).padStart(2, '0')})`,
    )

    // 定义时间段（以分钟为单位，便于比较）
    const timeSlots = [
      {
        name: 'time_slot_17_19',
        start: 17 * 60, // 17:00 = 1020分钟
        end: 19 * 60, // 19:00 = 1140分钟
        isRunning: workConfig.time_slot_17_19 === 1,
        adjustHours: 2,
      },
      {
        name: 'time_slot_19_21',
        start: 19 * 60, // 19:00 = 1140分钟
        end: 21 * 60, // 21:00 = 1260分钟
        isRunning: workConfig.time_slot_19_21 === 1,
        adjustHours: 2,
      },
      {
        name: 'time_slot_6_8',
        start: 6 * 60, // 06:00 = 360分钟
        end: 8 * 60, // 08:00 = 480分钟
        isRunning: workConfig.time_slot_6_8 === 1,
        adjustHours: 2,
      },
    ]

    // 重新设计调整逻辑：累计计算需要跳过的不运行时间段
    currentHour = adjustedTime.getHours()
    currentMinute = adjustedTime.getMinutes()
    currentTimeInMinutes = currentHour * 60 + currentMinute

    formingDevLog(
      `开始检查时间 ${currentHour}:${String(currentMinute).padStart(2, '0')} 需要跳过的不运行时间段`,
    )
    formingDevLog(
      `设备运行配置: 17-19=${workConfig.time_slot_17_19}, 19-21=${workConfig.time_slot_19_21}, 6-8=${workConfig.time_slot_6_8}`,
    )

    let totalAdjustmentHours = 0

    // 检查每个时间段，如果当前时间经过了该时间段且该时间段不运行，则累加调整时间
    for (const slot of timeSlots) {
      let shouldAdjust = false

      if (slot.name === 'time_slot_6_8') {
        // 6-8时间段：如果当前时间在6:00-8:00之间，且不运行
        shouldAdjust =
          currentTimeInMinutes >= slot.start && currentTimeInMinutes < slot.end && !slot.isRunning
      } else if (slot.name === 'time_slot_17_19') {
        // 17-19时间段：如果当前时间 >= 17:00，且不运行
        shouldAdjust = currentTimeInMinutes >= slot.start && !slot.isRunning
      } else if (slot.name === 'time_slot_19_21') {
        // 19-21时间段：如果当前时间 >= 19:00，且不运行
        shouldAdjust = currentTimeInMinutes >= slot.start && !slot.isRunning
      }

      if (shouldAdjust) {
        totalAdjustmentHours += slot.adjustHours
        formingDevLog(
          `时间经过了 ${slot.name} 时间段且设备不运行，累加调整 +${slot.adjustHours} 小时（总计: ${totalAdjustmentHours} 小时）`,
        )
      }
    }

    if (totalAdjustmentHours > 0) {
      formingDevLog(`总共需要调整 ${totalAdjustmentHours} 小时`)
      adjustedTime.setHours(adjustedTime.getHours() + totalAdjustmentHours)

      const newHour = adjustedTime.getHours()
      const newMinute = adjustedTime.getMinutes()
      formingDevLog(
        `调整后时间: ${adjustedTime.toLocaleString('ja-JP')} (${newHour}:${String(newMinute).padStart(2, '0')})`,
      )
    } else {
      formingDevLog('无需调整时间')
    }

    const finalHour = adjustedTime.getHours()
    const finalMinute = adjustedTime.getMinutes()
    formingDevLog(
      `最终段取開始時間: ${adjustedTime.toLocaleString('ja-JP')} (${finalHour}:${String(finalMinute).padStart(2, '0')})`,
    )

    formingDevLog(`返回调整后的时间对象:`, adjustedTime)
    formingDevLog(
      `返回时间的详细信息: 年=${adjustedTime.getFullYear()}, 月=${adjustedTime.getMonth() + 1}, 日=${adjustedTime.getDate()}, 时=${adjustedTime.getHours()}, 分=${adjustedTime.getMinutes()}, 秒=${adjustedTime.getSeconds()}`,
    )

    return adjustedTime
  } catch (error) {
    console.error('调整段取開始時間时出错:', error)
    return setupTime
  }
}

// 获取设备运行时间段配置（使用设备名称查询）
const getWorkTimeConfig = async (machineName: string): Promise<any | null> => {
  formingDevLog(`[getWorkTimeConfig] 开始获取设备 ${machineName} 的配置`)

  if (!machineName) {
    formingDevLog(`[getWorkTimeConfig] 设备名称为空，返回null`)
    return null
  }

  // 检查缓存
  if (workTimeConfigCache.has(machineName)) {
    const cachedConfig = workTimeConfigCache.get(machineName)
    formingDevLog(`[getWorkTimeConfig] 从缓存中获取设备 ${machineName} 的配置:`, cachedConfig)
    return cachedConfig
  }

  try {
    formingDevLog(`[getWorkTimeConfig] 从API获取配置...`)
    const result = (await request.get('/api/machine-work-time-config/work-time-config')) as ApiResponse | unknown[]
    formingDevLog(`[getWorkTimeConfig] API返回结果:`, result)

    const configs: any[] = Array.isArray(result) ? (result as any[]) : Array.isArray((result as ApiResponse)?.data) ? ((result as ApiResponse).data as any[]) : []
    formingDevLog(`[getWorkTimeConfig] 解析后的配置列表 (共${configs.length}条):`, configs)

    // 列出所有设备的machine_name，便于对比
    const allMachineNames = configs.map((item: any) => item.machine_name)
    formingDevLog(`[getWorkTimeConfig] 所有可用的设备名称:`, allMachineNames)
    formingDevLog(`[getWorkTimeConfig] 正在查找的设备名称: "${machineName}"`)

    const config = configs.find((item: any) => item.machine_name === machineName)
    formingDevLog(`[getWorkTimeConfig] 查找设备 ${machineName} 的配置:`, config)

    if (config) {
      // 兼容多种数据格式：1/0, true/false, "1"/"0"
      const configData = {
        time_slot_17_19:
          config.time_slot_17_19 === 1 ||
          config.time_slot_17_19 === true ||
          config.time_slot_17_19 === '1',
        time_slot_19_21:
          config.time_slot_19_21 === 1 ||
          config.time_slot_19_21 === true ||
          config.time_slot_19_21 === '1',
        time_slot_6_8:
          config.time_slot_6_8 === 1 ||
          config.time_slot_6_8 === true ||
          config.time_slot_6_8 === '1',
      }
      formingDevLog(`[getWorkTimeConfig] 原始配置:`, {
        time_slot_17_19: config.time_slot_17_19,
        time_slot_19_21: config.time_slot_19_21,
        time_slot_6_8: config.time_slot_6_8,
      })
      formingDevLog(`[getWorkTimeConfig] 转换后的配置数据:`, configData)
      workTimeConfigCache.set(machineName, configData)
      return configData
    } else {
      formingDevLog(`[getWorkTimeConfig] 未找到设备 ${machineName} 的配置`)
    }
  } catch (error) {
    console.error('[getWorkTimeConfig] 获取设备运行时间段配置失败:', error)
  }

  return null
}

// 根据配置生成运行时间段列表
const getWorkTimeSlots = (config: any): Array<{ start: number; end: number }> => {
  const slots: Array<{ start: number; end: number }> = []

  if (config.time_slot_17_19) {
    slots.push({ start: 17 * 60, end: 19 * 60 }) // 17:00 - 19:00
  }
  if (config.time_slot_19_21) {
    slots.push({ start: 19 * 60, end: 21 * 60 }) // 19:00 - 21:00
  }
  if (config.time_slot_6_8) {
    slots.push({ start: 6 * 60, end: 8 * 60 }) // 6:00 - 8:00
  }

  return slots.sort((a, b) => a.start - b.start)
}

// 累加小时数，考虑设备运行时间段配置
// 新算法：先累加运行时间，然后检查经过了哪些不运行时间段，累加这些不运行时间
// 返回：起始时间 + 运行时间 + 经过的不运行时间
const addHoursWithWorkTimes = async (
  startDate: string, // YYYY-MM-DD
  startTime: string, // HH:mm
  workHours: number, // 需要累加的运行时间（小时）
  machineName: string, // 设备名称（ライン）
  preloadedWorkTimes?: Map<string, any[]>, // 预加载的运行时间数据（已废弃，保留以兼容）
  allPlanData?: any[], // 所有设备的生产数据，用于检查星期六是否有生产
): Promise<Date> => {
  formingDevLog(`\n========== 开始计算段取開始時間 ==========`)
  formingDevLog(`起始时间: ${startDate} ${startTime}`)
  formingDevLog(`需要累加的运行时间: ${workHours} 小时`)
  formingDevLog(`设备名称: ${machineName}`)

  // 创建起始时间
  let resultTime = new Date(`${startDate}T${startTime}:00`)

  // 如果没有设备名称，直接累加小时数
  if (!machineName) {
    resultTime.setTime(resultTime.getTime() + workHours * 60 * 60 * 1000)
    formingDevLog(`没有设备名称，直接累加 ${workHours} 小时`)
    formingDevLog(`最终时间: ${resultTime.toLocaleString('ja-JP')}`)
    return resultTime
  }

  // 获取设备运行时间段配置（使用设备名称查询machine_work_time_config表）
  const config = await getWorkTimeConfig(machineName)

  // 如果没有配置，直接累加小时数
  if (!config) {
    resultTime.setTime(resultTime.getTime() + workHours * 60 * 60 * 1000)
    formingDevLog(`没有找到设备配置，直接累加 ${workHours} 小时`)
    formingDevLog(`最终时间: ${resultTime.toLocaleString('ja-JP')}`)
    return resultTime
  }

  formingDevLog(
    `设备配置: 17-19=${config.time_slot_17_19 ? '○' : '×'}, 19-21=${config.time_slot_19_21 ? '○' : '×'}, 6-8=${config.time_slot_6_8 ? '○' : '×'}`,
  )

  // 第一步：先直接累加运行时间
  const intermediateTime = new Date(resultTime.getTime() + workHours * 60 * 60 * 1000)
  formingDevLog(
    `第一步：累加 ${workHours} 小时后 = ${intermediateTime.toLocaleString('ja-JP')} (${intermediateTime.getHours()}:${String(intermediateTime.getMinutes()).padStart(2, '0')})`,
  )

  // 第二步：检查从起始时间到中间时间，经过了哪些不运行时间段
  // 定义不运行时间段
  const nonWorkSlots = []
  if (!config.time_slot_17_19) {
    nonWorkSlots.push({ name: '17-19', start: 17, end: 19, hours: 2 })
  }
  if (!config.time_slot_19_21) {
    nonWorkSlots.push({ name: '19-21', start: 19, end: 21, hours: 2 })
  }
  if (!config.time_slot_6_8) {
    nonWorkSlots.push({ name: '6-8', start: 6, end: 8, hours: 2 })
  }

  formingDevLog(`\n第二步：检查经过的不运行时间段`)
  formingDevLog(`不运行时间段列表:`, nonWorkSlots.map((s) => s.name).join(', '))

  let totalAdjustmentHours = 0
  const startHour = resultTime.getHours()
  const endHour = intermediateTime.getHours()
  const startDay = resultTime.getDate()
  const endDay = intermediateTime.getDate()

  formingDevLog(
    `起始时间: ${startDay}日 ${startHour}:${String(resultTime.getMinutes()).padStart(2, '0')}`,
  )
  formingDevLog(
    `中间时间: ${endDay}日 ${endHour}:${String(intermediateTime.getMinutes()).padStart(2, '0')}`,
  )

  // 检查每个不运行时间段
  for (const slot of nonWorkSlots) {
    let crossed = false

    if (startDay === endDay) {
      // 同一天内
      // 检查是否经过了该时间段的任何部分
      // 条件：起始时间 < 时间段结束 AND 结束时间 > 时间段开始
      if (startHour < slot.end && endHour > slot.start) {
        crossed = true
      }
    } else {
      // 跨天了
      // 检查起始日是否经过该时间段（从起始时间到24:00）
      if (startHour < slot.end) {
        crossed = true
      }
      // 检查结束日是否经过该时间段（从0:00到结束时间）
      if (!crossed && endHour > slot.start) {
        crossed = true
      }
      // 如果跨了多天（超过1天），中间的完整天都会经过所有时间段
      if (!crossed && endDay - startDay > 1) {
        crossed = true
      }
    }

    if (crossed) {
      totalAdjustmentHours += slot.hours
      formingDevLog(`  ✓ 经过了 ${slot.name} 时间段（不运行），需要加 ${slot.hours} 小时`)
    } else {
      formingDevLog(`  - 未经过 ${slot.name} 时间段`)
    }
  }

  formingDevLog(`\n第三步：累加不运行时间`)
  formingDevLog(`总共需要加上的不运行时间: ${totalAdjustmentHours} 小时`)

  // 第三步：在中间时间基础上累加不运行时间
  resultTime = new Date(intermediateTime.getTime() + totalAdjustmentHours * 60 * 60 * 1000)
  formingDevLog(
    `第三步结果: ${resultTime.toLocaleString('ja-JP')} (${resultTime.getHours()}:${String(resultTime.getMinutes()).padStart(2, '0')})`,
  )

  // 第三步之二：检查是否经过了没有生产数据的星期六，如果是则跳过星期六6:00到星期一8:00的时间段
  formingDevLog(`\n第三步之二：检查是否经过没有生产数据的星期六`)
  let saturdayAdjustmentHours = 0
  if (allPlanData && allPlanData.length > 0) {
    // 遍历从起始时间到当前结果时间之间的所有日期
    const checkDate = new Date(`${startDate}T12:00:00`)
    const endCheckDate = new Date(resultTime)

    while (checkDate <= endCheckDate) {
      const dayOfWeek = checkDate.getDay()

      // 如果是星期六
      if (dayOfWeek === 6) {
        const saturdayStr = checkDate.toISOString().split('T')[0]
        formingDevLog(`  检查星期六 ${saturdayStr} 是否有生产数据`)

        // 检查该星期六是否有生产数据
        const saturdayProducts = allPlanData.filter((item: any) => {
          const itemDate = JapanDateUtils.normalizeDate(item.plan_date || '')
          return itemDate === saturdayStr
        })

        const hasSaturdayProduction = saturdayProducts.some((product: any) => {
          const quantity = parseInt(product.quantity) || 0
          return quantity > 0
        })

        formingDevLog(
          `  星期六 ${saturdayStr} ${hasSaturdayProduction ? '有生产数据' : '没有生产数据'}`,
        )

        // 如果星期六没有生产数据，需要跳过星期六6:00到星期一8:00的时间段（50小时）
        if (!hasSaturdayProduction) {
          // 检查结果时间是否经过了这个星期六的6:00
          const saturdaySixAM = new Date(`${saturdayStr}T06:00:00`)
          const mondayEightAM = new Date(saturdaySixAM.getTime() + 50 * 60 * 60 * 1000) // 星期六6:00 + 50小时 = 星期一8:00

          // 如果起始时间在星期六6:00之前，且结果时间在星期六6:00之后，说明经过了这个时间段
          const startDateTime = new Date(`${startDate}T${startTime}:00`)
          if (startDateTime < saturdaySixAM && resultTime >= saturdaySixAM) {
            saturdayAdjustmentHours += 50
            formingDevLog(
              `  ✓ 经过了星期六 ${saturdayStr} 6:00-星期一8:00时间段（无生产），需要加 50 小时`,
            )
          }
        }
      }

      // 检查下一天
      checkDate.setDate(checkDate.getDate() + 1)
    }

    if (saturdayAdjustmentHours > 0) {
      resultTime = new Date(resultTime.getTime() + saturdayAdjustmentHours * 60 * 60 * 1000)
      formingDevLog(
        `  累加星期六无生产时间段 ${saturdayAdjustmentHours} 小时后: ${resultTime.toLocaleString('ja-JP')} (${resultTime.getHours()}:${String(resultTime.getMinutes()).padStart(2, '0')})`,
      )
    } else {
      formingDevLog(`  - 未经过需要跳过的星期六时间段`)
    }
  } else {
    formingDevLog(`  没有生产数据，跳过星期六检查`)
  }

  // 第四步：检查最终时间是否落在不运行时间段内，如果是则跳过该时间段
  // 使用循环检查，因为跳过后可能又落在另一个不运行时间段内
  formingDevLog(`\n第四步：检查最终时间是否落在不运行时间段内`)
  let additionalAdjustment = 0
  const maxIterations = 10 // 防止无限循环
  let iteration = 0

  while (iteration < maxIterations) {
    iteration++
    const currentHour = resultTime.getHours()
    const currentMinute = resultTime.getMinutes()
    formingDevLog(
      `  检查 (第${iteration}次): ${currentHour}:${String(currentMinute).padStart(2, '0')}`,
    )

    let foundSlot = false
    for (const slot of nonWorkSlots) {
      // 检查当前时间是否在该不运行时间段内
      if (currentHour >= slot.start && currentHour < slot.end) {
        formingDevLog(
          `    ✓ 时间落在 ${slot.name} 不运行时间段内 (${slot.start}:00-${slot.end}:00)，跳过 ${slot.hours} 小时`,
        )
        additionalAdjustment += slot.hours
        resultTime = new Date(resultTime.getTime() + slot.hours * 60 * 60 * 1000)
        foundSlot = true
        break // 跳过这个时间段后，重新检查
      }
    }

    if (!foundSlot) {
      formingDevLog(`    - 时间不在任何不运行时间段内`)
      break // 没有找到不运行时间段，退出循环
    }
  }

  if (additionalAdjustment > 0) {
    formingDevLog(
      `  最终调整后: ${resultTime.toLocaleString('ja-JP')} (${resultTime.getHours()}:${String(resultTime.getMinutes()).padStart(2, '0')})`,
    )
  } else {
    formingDevLog(`  - 无需调整`)
  }

  formingDevLog(`\n最终计算结果:`)
  formingDevLog(`  起始时间: ${startDate} ${startTime}`)
  formingDevLog(`  + 运行时间: ${workHours} 小时`)
  formingDevLog(`  + 经过的不运行时间: ${totalAdjustmentHours} 小时`)
  formingDevLog(`  + 星期六无生产时间段: ${saturdayAdjustmentHours} 小时`)
  formingDevLog(`  + 最终时间调整: ${additionalAdjustment} 小时`)
  formingDevLog(
    `  = 最终时间: ${resultTime.toLocaleString('ja-JP')} (${resultTime.getHours()}:${String(resultTime.getMinutes()).padStart(2, '0')})`,
  )
  formingDevLog(`========== 计算完成 ==========\n`)

  return resultTime
}

/** FormingPlanningList 設備操業度タブと同一の APS process_cd（成型） */
const FORMING_APS_PROCESS_CD = 'KT04'

function monthRangeFromYmUtil(ym: string): [string, string] | null {
  const t = (ym || '').trim()
  const m = t.match(/^(\d{4})-(\d{2})/)
  if (!m) return null
  const y = Number(m[1])
  const mo = Number(m[2])
  if (!Number.isFinite(y) || mo < 1 || mo > 12) return null
  const sd = `${y}-${String(mo).padStart(2, '0')}-01`
  const last = new Date(y, mo, 0).getDate()
  const ed = `${y}-${String(mo).padStart(2, '0')}-${String(last).padStart(2, '0')}`
  return [sd, ed]
}

type ScheduleGridRowWithLine = ScheduleGridRow & { line_id: number; lineLabel: string }

function flattenSchedulingGridToRows(
  grid: SchedulingGridResponse,
  lineNameById: Map<number, string>,
): ScheduleGridRowWithLine[] {
  const flat: ScheduleGridRowWithLine[] = []
  for (const block of grid.blocks || []) {
    const label =
      lineNameById.get(block.line_id) ||
      String((block as { line_name?: string }).line_name || '').trim() ||
      block.line_code ||
      `ID ${block.line_id}`
    for (const r of block.rows || []) {
      flat.push({ ...r, line_id: block.line_id, lineLabel: label })
    }
  }
  return flat
}

function lineLastActualDayInMonthForUtil(
  monthDates: string[],
  rows: ScheduleGridRowWithLine[],
): Map<number, string | null> {
  const lastBy = new Map<number, string | null>()
  const lineIds = new Set(rows.map((r) => r.line_id))
  for (const lid of lineIds) lastBy.set(lid, null)
  for (const d of monthDates) {
    const daySum = new Map<number, number>()
    for (const row of rows) {
      const lid = row.line_id
      daySum.set(lid, (daySum.get(lid) ?? 0) + Number(row.actual_daily?.[d] ?? 0))
    }
    for (const [lid, v] of daySum) {
      if (v > 0) lastBy.set(lid, d)
    }
  }
  return lastBy
}

/**
 * 生産日が属する暦月について、設備名 → 操業度差異(H)。
 * FormingPlanningList の utilizationRows.diffHours（行別日次差を能率換算し設備合算）と同一。
 */
async function loadUtilizationDiffHoursByLineNameForMonth(
  productionDateSlash: string,
): Promise<Map<string, number>> {
  const out = new Map<string, number>()
  const parts = productionDateSlash.split('/').filter(Boolean)
  if (parts.length < 2) return out
  const y = parts[0].trim()
  const mo = parts[1].trim().padStart(2, '0')
  const ym = `${y}-${mo}`
  const range = monthRangeFromYmUtil(ym)
  if (!range) return out
  const [sd, ed] = range
  try {
    const [grid, lines] = await Promise.all([
      fetchSchedulingGrid(sd, ed, undefined, FORMING_APS_PROCESS_CD),
      fetchLines(FORMING_APS_PROCESS_CD),
    ])
    const monthDates = [...(Array.isArray(grid.dates) ? grid.dates : [])].sort((a, b) =>
      a.localeCompare(b),
    )
    if (monthDates.length === 0) return out

    const lineNameById = new Map<number, string>()
    for (const line of lines || []) {
      const name = String(line.line_name || '').trim()
      const code = String(line.line_code || '').trim()
      lineNameById.set(line.id, name || code || `ID ${line.id}`)
    }
    const rows = flattenSchedulingGridToRows(grid, lineNameById)
    const lastActualByLine = lineLastActualDayInMonthForUtil(monthDates, rows)

    const byLineId = new Map<number, number>()
    for (const row of rows) {
      const lineId = row.line_id
      const rate = Number(row.efficiency_rate ?? 0)
      const endDay = lastActualByLine.get(lineId)
      const diffDates =
        endDay == null || endDay === '' ? ([] as string[]) : monthDates.filter((d) => d <= endDay)
      const diffQtyRow = diffDates.reduce((sum, d) => {
        const p = Number(row.daily?.[d] ?? 0)
        const a = Number(row.actual_daily?.[d] ?? 0)
        return sum + (a - p)
      }, 0)
      const diffHoursRow = rate > 0 ? diffQtyRow / rate : 0
      byLineId.set(lineId, (byLineId.get(lineId) ?? 0) + diffHoursRow)
    }

    const labelByLineId = new Map<number, string>()
    for (const r of rows) {
      if (!labelByLineId.has(r.line_id)) labelByLineId.set(r.line_id, r.lineLabel)
    }
    for (const [lineId, hours] of byLineId) {
      const label = labelByLineId.get(lineId) || ''
      if (label) out.set(label, hours)
    }
  } catch (e) {
    console.error('APS grid 操業度差異(H)の取得に失敗:', e)
  }
  return out
}

// ==================== 主函数 ====================

// 生成段取予定表打印内容
const generateSetupScheduleContent = async (planData: any[]) => {
  // 使用工具类获取当前日期时间
  const currentDateTime = JapanDateUtils.getCurrentDateTime()

  // 获取生产日（与筛选日期一致，使用日本时区）
  const productionDate = JapanDateUtils.formatDate(getSelectedBaseDate())

  // 按设备分组数据
  const groupedByMachine = groupDataByMachine(planData)

  // 获取所有设备列表
  const machines = Object.keys(groupedByMachine).sort()

  // ========== 优化：批量预加载数据 ==========
  // 1. 预加载能率数据（如果还未加载）
  if (efficiencyCache.size === 0) {
    formingDevLog('预加载能率数据...')
    await loadEfficiencyData()
  }

  // 2. 预加载用于「総計画数 / 実績 / 生産残数」的数据
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

  // MES 路由：直接使用 production_schedules + schedule_details 由来数据
  // ERP 路由：沿用 production_plan_schedules（月文件）数据
  let productionPlanSchedulesData: any[] = []
  if (planDataApiPath.value === '/api/mes/forming-plan-data') {
    productionPlanSchedulesData = Array.isArray(planData) ? planData : []
    formingDevLog(
      'MES ルート: production_schedules 由来データを使用、记录数:',
      productionPlanSchedulesData.length,
    )
  } else if (monthFilter) {
    try {
      formingDevLog('production_plan_schedules データを読み込み中、月フィルター:', monthFilter)
      const result = (await request.get('/api/processing-status', {
        params: {
          fileName: monthFilter, // 使用月份筛选 file_name 字段（例如："1月"匹配"加工計画(1月).xlsm"）
          limit: 100000, // 设置一个较大的值以获取所有数据
        },
      })) as ApiResponse

      if (result.success && result.data) {
        productionPlanSchedulesData = Array.isArray(result.data) ? result.data : []
        formingDevLog(
          '成功加载 production_plan_schedules 数据，记录数:',
          productionPlanSchedulesData.length,
        )
      }
    } catch (error) {
      console.error('加载 production_plan_schedules 数据失败:', error)
    }
  }

  // 操業度（MES）：FormingPlanningList「操業度差異(H)」と同一（APS scheduling/grid、日次差×能率・最終実績日まで）
  const productionPlanRateMap = new Map<string, string | number>()
  if (planDataApiPath.value === '/api/mes/forming-plan-data') {
    const diffMap = await loadUtilizationDiffHoursByLineNameForMonth(productionDate)
    for (const [name, hours] of diffMap) {
      productionPlanRateMap.set(name, hours)
    }
  } else if (monthFilter) {
    // ERP 路由维持既有逻辑
    try {
      const rateResult = (await request.get('/api/operation-rate', {
        params: { fileName: monthFilter, limit: 10000 },
      })) as ApiResponse
      if (rateResult.success && rateResult.data && Array.isArray(rateResult.data)) {
        ;(rateResult.data as any[]).forEach((item: any) => {
          const name = (item.machine_name || '').toString().trim()
          if (name && !productionPlanRateMap.has(name)) {
            const v = item.operation_variance
            productionPlanRateMap.set(name, v !== null && v !== undefined ? v : '')
          }
        })
      }
    } catch (e) {
      console.error('加载 production_plan_rate 操業度数据失败:', e)
    }
  }

  // 创建映射表，key: machine_name + product_name + production_order(operator)
  const productionPlanSchedulesMap = new Map<string, any>()
  const mesPlannedDedupByKey = new Map<string, Set<string>>()
  productionPlanSchedulesData.forEach((item) => {
    // MES データは operator、ERP データは production_order を主に使用
    const productionOrder = (item.production_order ?? item.operator ?? '').toString().trim()
    const key = `${item.machine_name}|${item.product_name}|${productionOrder}`
    const plannedQuantity = parseInt(item.planned_quantity ?? item.quantity ?? item.planned_qty) || 0
    const plannedOutputQuantity = parseInt(item.planned_output_qty) || 0
    const actualProduction = parseInt(item.actual_production ?? item.actual_qty) || 0
    const defectQuantity = parseInt(item.defect_qty) || 0
    const upstreamDefectQuantity = parseInt(item.upstream_defect_qty_total) || 0
    // 如果同一个 machine_name + product_name + production_order 有多条记录，累加数量
    if (productionPlanSchedulesMap.has(key)) {
      const existing = productionPlanSchedulesMap.get(key)
      if (planDataApiPath.value === '/api/mes/forming-plan-data') {
        const scheduleId = (item.schedule_id ?? '').toString().trim()
        const dedupSet = mesPlannedDedupByKey.get(key) || new Set<string>()
        if (scheduleId && !dedupSet.has(scheduleId)) {
          existing.planned_quantity =
            (parseInt(existing.planned_quantity) || 0) + (plannedOutputQuantity || plannedQuantity)
          dedupSet.add(scheduleId)
          mesPlannedDedupByKey.set(key, dedupSet)
        }
      } else {
        existing.planned_quantity = (parseInt(existing.planned_quantity) || 0) + plannedQuantity
      }
      existing.actual_production = (parseInt(existing.actual_production) || 0) + actualProduction
      existing.defect_qty = (parseInt(existing.defect_qty) || 0) + defectQuantity
      existing.upstream_defect_qty_total =
        (parseInt(existing.upstream_defect_qty_total) || 0) + upstreamDefectQuantity
    } else {
      const initialPlannedQuantity =
        planDataApiPath.value === '/api/mes/forming-plan-data'
          ? (plannedOutputQuantity || plannedQuantity)
          : plannedQuantity
      productionPlanSchedulesMap.set(key, {
        planned_quantity: initialPlannedQuantity,
        actual_production: actualProduction,
        defect_qty: defectQuantity,
        upstream_defect_qty_total: upstreamDefectQuantity,
        production_order: productionOrder,
      })
      if (planDataApiPath.value === '/api/mes/forming-plan-data') {
        const scheduleId = (item.schedule_id ?? '').toString().trim()
        const dedupSet = new Set<string>()
        if (scheduleId) dedupSet.add(scheduleId)
        mesPlannedDedupByKey.set(key, dedupSet)
      }
    }
  })

  // 3. 设备运行时间预加载已移除（不再需要计算不运行时间）
  // ========== 预加载完成 ==========

  // 将生产日期转换为 YYYY-MM-DD 格式用于比较
  const filterDateForTotal = productionDate.replace(/\//g, '-')

  // 读取予定稼働(H)：line_capacities.available_hours（work_date = 生産日）
  const plannedWorkHoursMap = new Map<string, number>()
  try {
    const machinesResult = (await request.get('/api/master/machines', {
      params: { machine_type: '成型' },
    })) as ApiResponse
    const machineList: any[] = Array.isArray(machinesResult)
      ? machinesResult
      : ((machinesResult?.list ?? (machinesResult?.data as any)?.list ?? []) as any[])
    const machineIdByName = new Map<string, number>()
    machineList.forEach((m: any) => {
      const name = (m.machine_name || '').toString().trim()
      const id = Number(m.id)
      if (name && Number.isFinite(id) && id > 0) {
        machineIdByName.set(name, id)
      }
    })

    await Promise.all(
      machines.map(async (machineName) => {
        const lineId = machineIdByName.get(machineName)
        if (!lineId) return
        try {
          const capRes = (await request.get('/api/aps/line-capacities', {
            params: {
              lineId,
              startDate: filterDateForTotal,
              endDate: filterDateForTotal,
            },
          })) as ApiResponse
          const capList: any[] = Array.isArray(capRes)
            ? capRes
            : ((capRes?.list ?? (capRes?.data as any)?.list ?? capRes?.data ?? []) as any[])
          const dayCap = capList.find(
            (c: any) => JapanDateUtils.normalizeDate(c?.work_date) === filterDateForTotal,
          )
          const hours = Number(dayCap?.available_hours ?? 0)
          if (Number.isFinite(hours)) {
            plannedWorkHoursMap.set(machineName, hours)
          }
        } catch (e) {
          console.error(`予定稼働(H) 读取失败: ${machineName}`, e)
        }
      }),
    )
  } catch (e) {
    console.error('予定稼働(H) 设备基础数据读取失败:', e)
  }

  // 计算生产计划合计数（只统计指定生产日所有产品的生产数合计）
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

  // 辅助函数：计算下一个有效日期（考虑周末逻辑）
  const getNextValidDate = (baseDate: string, nextDate: string, quantity: number): string => {
    const date = new Date(nextDate)
    const dayOfWeek = date.getDay() // 0=周日, 1=周一, ..., 6=周六

    // 如果是周末（周六=6，周日=0）
    if (dayOfWeek === 0 || dayOfWeek === 6) {
      // 如果生产計画 <= 0，跳到下一个星期一
      if (quantity <= 0) {
        const daysToAdd = dayOfWeek === 0 ? 1 : 2 // 周日+1天到周一，周六+2天到周一
        date.setDate(date.getDate() + daysToAdd)
        return date.toISOString().split('T')[0]
      }
      // 如果生产計画 > 0，使用这个日期
      return nextDate
    }

    // 如果不是周末，直接返回
    return nextDate
  }

  // 生成表格行数据（异步处理，因为需要获取设备运行时间）
  const tableRowsPromises = machines.map(async (machineName, index) => {
    const machineData = groupedByMachine[machineName]

    // 使用已转换的筛选日期
    const filterDate = filterDateForTotal

    // 构建日期索引（优化查找性能）
    const dateIndex = DataIndexUtils.buildDateIndex(machineData)

    // 调试：显示索引中的所有日期
    const allDatesInIndex = Array.from(dateIndex.keys()).sort()
    formingDevLog(`设备 ${machineName} 的数据索引中包含的日期:`, allDatesInIndex)

    // 获取当前产品（使用索引优化）- 读取指定生产日的数据
    const currentProducts = DataIndexUtils.findValidProducts(dateIndex, filterDate)
    const currentProduct = currentProducts.length > 0 ? currentProducts[0] : {}

    // 从currentProduct中获取machine_cd（读取production_plan_updates表的machine_cd字段）
    const machineCdFromData = (currentProduct as any)?.machine_cd || ''
    formingDevLog(
      `[設備CD] 设备名称: ${machineName}, 从当前产品数据中获取的machine_cd: ${machineCdFromData}`,
    )

    // 获取当前生产数量 - 读取指定生产日的数据
    let currentQuantity = 0
    if (currentProduct && (currentProduct as any).plan_date) {
      const normalizedCurrentDate = JapanDateUtils.normalizeDate((currentProduct as any).plan_date)
      if (normalizedCurrentDate === filterDate) {
        currentQuantity = parseInt((currentProduct as any).quantity) || 0
      }
    }

    // 作業時間計算（生産計画データに基づく）
    // 簡易処理：標準作業時間を想定、実際の生産計画により計算可能
    // 生産数が0より大きい場合、作業時間は最小1時間、最大24時間
    const workTime =
      currentQuantity > 0 ? Math.min(24, Math.max(1, Math.floor(currentQuantity / 200) || 1)) : 0

    // 生産停止判定（フィルター日に該当データがない、または数量が0の場合）
    const isProductionStop =
      !(currentProduct as any).plan_date ||
      currentQuantity === 0 ||
      !(currentProduct as any).product_name

    // 能率計算（1時間あたりの生産能力）
    // 取得優先順位：
    //   1. production_plan_updates テーブルの efficiency_rate フィールド
    //   2. equipment_efficiency テーブル（設備名+製品名で検索）
    //   3. 簡易計算（表示用）
    const currentProductName = isProductionStop ? '' : (currentProduct as any).product_name || ''
    let efficiency = ''
    let efficiencyRateNum: number | null = null // 後続計算用に能率数値を保存

    if (currentProductName && !isProductionStop) {
      // 現在製品の efficiency_rate フィールドから優先的に読み取り
      const efficiencyRate = (currentProduct as any).efficiency_rate

      // 能率値の検証と解析
      if (
        efficiencyRate !== null &&
        efficiencyRate !== undefined &&
        efficiencyRate !== '' &&
        parseFloat(efficiencyRate) > 0
      ) {
        efficiencyRateNum = parseFloat(efficiencyRate)
        efficiency = formatEfficiencyRate(efficiencyRate)
      } else {
        // 如果 production_plan_updates 表中没有能率，从 equipment_efficiency 表获取
        const cachedEfficiencyRate = getEfficiencyRate(machineName, currentProductName)
        if (cachedEfficiencyRate !== null && cachedEfficiencyRate > 0) {
          efficiencyRateNum = cachedEfficiencyRate
          efficiency = formatEfficiencyRate(cachedEfficiencyRate)
        } else {
          // 如果都没找到能率数据，使用简化计算作为后备方案（仅用于显示）
          if (currentQuantity > 0 && workTime > 0) {
            const hourlyRate = Math.round(currentQuantity / workTime)
            efficiency = `${hourlyRate}`
            // 注意：简化计算的能率不保存到 efficiencyRateNum，因为不准确
          } else if (currentQuantity > 0) {
            // 假设标准8小时工作制
            const standardHourlyRate = Math.round(currentQuantity / 8)
            efficiency = `${standardHourlyRate}`
            // 注意：简化计算的能率不保存到 efficiencyRateNum，因为不准确
          }
        }
      }
    }

    // 生产开始时间（默认15:00）
    const startTime = '15:00'

    // 获取下一个生产品种（优化版：使用索引和工具类）
    let nextProduct = null
    let nextValidDate = ''

    // 查找下一个产品的核心函数
    // 新逻辑：次生産品種和次生産品種見込数读取指定生产日下一日的数据
    // 如果下一日是星期六且有数据就读取星期六，如果没有数据就读取星期一
    const findNextProduct = (): { product: any | null; date: string } => {
      formingDevLog(`开始查找下一个产品，当前筛选日期: ${filterDate}`)

      const dayOfWeek = JapanDateUtils.getDayOfWeek(filterDate)

      // 1. 先检查同一指定生产日是否有多个不同产品
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
          formingDevLog(`在同一天找到下一个产品`)
          return { product: sameDayProducts[currentProductIndex + 1], date: filterDate }
        }
      }

      // 2. 计算指定生产日的下一日
      const nextDate = new Date(filterDate)
      nextDate.setDate(nextDate.getDate() + 1)
      const nextDateStr = nextDate.toISOString().split('T')[0]
      const nextDayOfWeek = nextDate.getDay() // 0=周日, 1=周一, ..., 6=周六

      formingDevLog(`指定生产日的下一日: ${nextDateStr}, 星期: ${nextDayOfWeek}`)

      // 3. 如果下一日是星期六 (6)
      if (nextDayOfWeek === 6) {
        formingDevLog(`下一日是星期六，先检查星期六是否有数据`)

        // 先检查星期六是否有数据
        const saturdayProducts = DataIndexUtils.findValidProducts(dateIndex, nextDateStr)
        if (saturdayProducts.length > 0) {
          formingDevLog(`星期六有数据，使用星期六的数据:`, saturdayProducts[0])
          return { product: saturdayProducts[0], date: nextDateStr }
        }

        // 星期六没有数据，读取星期一的数据
        const mondayDate = new Date(nextDateStr)
        mondayDate.setDate(mondayDate.getDate() + 2) // 星期六 + 2天 = 星期一
        const mondayDateStr = mondayDate.toISOString().split('T')[0]
        formingDevLog(`星期六没有数据，读取星期一的数据: ${mondayDateStr}`)

        const mondayProducts = DataIndexUtils.findValidProducts(dateIndex, mondayDateStr)
        if (mondayProducts.length > 0) {
          formingDevLog(`星期一有数据:`, mondayProducts[0])
          return { product: mondayProducts[0], date: mondayDateStr }
        }
      }
      // 4. 如果下一日是星期日 (0)
      else if (nextDayOfWeek === 0) {
        formingDevLog(`下一日是星期日，读取星期一的数据`)

        // 星期日的下一天就是星期一
        const mondayDate = new Date(nextDateStr)
        mondayDate.setDate(mondayDate.getDate() + 1) // 星期日 + 1天 = 星期一
        const mondayDateStr = mondayDate.toISOString().split('T')[0]
        formingDevLog(`读取星期一的数据: ${mondayDateStr}`)

        const mondayProducts = DataIndexUtils.findValidProducts(dateIndex, mondayDateStr)
        if (mondayProducts.length > 0) {
          formingDevLog(`星期一有数据:`, mondayProducts[0])
          return { product: mondayProducts[0], date: mondayDateStr }
        }
      }
      // 5. 如果下一日是工作日 (星期一到星期五)
      else {
        formingDevLog(`下一日是工作日，直接读取下一日的数据`)

        const nextDayProducts = DataIndexUtils.findValidProducts(dateIndex, nextDateStr)
        if (nextDayProducts.length > 0) {
          formingDevLog(`下一日有数据:`, nextDayProducts[0])
          return { product: nextDayProducts[0], date: nextDateStr }
        }
      }

      formingDevLog(`没有找到下一个产品`)
      return { product: null, date: '' }
    }

    const nextProductResult = findNextProduct()
    nextProduct = nextProductResult.product
    nextValidDate = nextProductResult.date

    const nextProductName = nextProduct ? (nextProduct as any).product_name || '' : ''
    const nextQuantity = nextProduct ? parseInt((nextProduct as any).quantity) || 0 : 0

    formingDevLog(
      `查找结果: nextProduct=${!!nextProduct}, nextValidDate=${nextValidDate}, nextProductName=${nextProductName}, nextQuantity=${nextQuantity}`,
    )

    // 時間後段取予定（如果有下一个计划，用当前产品的生産計画数除以当前产品的能率，保留1位小数）
    // 计算公式：生産計画数（本） / 能率（本/h） = 所需时间（小时）
    // 注意：使用上面已经获取的 efficiencyRateNum（已从 production_plan_updates 或 equipment_efficiency 表获取）
    let setupAfterHours: string | number = ''
    if (nextProduct && !isProductionStop) {
      // 验证生产数量
      const validQuantity = currentQuantity > 0

      // 如果有有效的能率值（已从上面获取）和生产数量，则计算：生産計画数 / 能率
      if (efficiencyRateNum !== null && efficiencyRateNum > 0 && validQuantity) {
        const calculatedHours = currentQuantity / efficiencyRateNum
        // 确保计算结果为正数且合理（大于0且小于等于1000小时）
        if (calculatedHours > 0 && calculatedHours <= 1000) {
          setupAfterHours = parseFloat(calculatedHours.toFixed(1))
        } else {
          // 计算结果不合理，保持为空
          setupAfterHours = ''
        }
      } else {
        // 如果没有能率或生产数量，保持为空
        setupAfterHours = ''
      }
    }

    // 获取设备的machine_cd（仅用于表格显示）
    // 使用从currentProduct获取的machine_cd（读取production_plan_updates表的machine_cd字段）
    const currentMachineCd = machineCdFromData || ''

    // 调试：输出当前产品的完整信息
    formingDevLog(`[时间配置] 当前产品完整信息:`, currentProduct)
    formingDevLog(`[时间配置] 设备名称: ${machineName}, 设备代码（仅用于显示）: ${currentMachineCd}`)
    formingDevLog(
      `[时间配置] machine_cd来源: ${machineCdFromData ? 'currentProduct (production_plan_updates表)' : '未找到'}`,
    )
    formingDevLog(
      `[时间配置] 注意：时间段配置使用设备名称(${machineName})查询machine_work_time_config表`,
    )

    // 段取予測時間の計算
    // 時間後段取に値がある場合：前日15:00 + 時間後段取時間（運転時間）+ 設備非稼働時間
    // 設備運転時間帯設定（17-19, 19-21, 6-8）に基づき、運転時間帯内の時間のみ計算し、非稼働時間帯をスキップ
    // 例：11/6の開始時間は11/5の15:00
    let setupPredictedTime = ''

    // 時間後段取にデータがある場合、計算を実行
    if (setupAfterHours !== '' && typeof setupAfterHours === 'number' && setupAfterHours > 0) {
      // 前営業日の日付を計算（各日の開始時間は前営業日の15:00）
      const prevDateStr = getBaselineStartDate(filterDate, machineData, dateIndex, planData)

      // 設備運転時間帯設定を考慮した時间计算関数を使用
      // addHoursWithWorkTimes 会：
      // 1. 从 machine_work_time_config 表获取设备运行时间段配置（17-19, 19-21, 6-8）
      // 2. 累加指定的小时数（只计算运行时间段内的时间）
      // 3. 计算在累加过程中遇到的不运行时间段
      // 4. 检查是否经过没有生产数据的星期六，如果是则跳过星期六6:00到星期一8:00
      // 5. 返回：起始时间 + 运行时间 + 不运行时间
      const calculatedTime = await addHoursWithWorkTimes(
        prevDateStr, // 前一天的日期 YYYY-MM-DD（每天的开始时间是前一天的15:00）
        '15:00', // 起始时间（前一天的15:00）
        setupAfterHours, // 需要累加的时间（小时）
        machineName, // 设备名称（ライン），用于查询machine_work_time_config表
        undefined, // 预加载的运行时间数据（已废弃）
        planData, // 所有设备的生产数据，用于检查星期六是否有生产
      )

      // addHoursWithWorkTimes 已经包含了所有不运行时间段的计算，直接使用结果
      const finalAdjustedTime = calculatedTime
      formingDevLog(`最终段取開始時間:`, finalAdjustedTime)

      // 格式化日期时间：YYYY/MM/DD HH:mm:ss
      const year = finalAdjustedTime.getFullYear()
      const month = String(finalAdjustedTime.getMonth() + 1).padStart(2, '0')
      const day = String(finalAdjustedTime.getDate()).padStart(2, '0')
      const hours = String(finalAdjustedTime.getHours()).padStart(2, '0')
      const minutes = String(finalAdjustedTime.getMinutes()).padStart(2, '0')
      const seconds = String(finalAdjustedTime.getSeconds()).padStart(2, '0')

      formingDevLog(`格式化后的时间字符串: ${year}/${month}/${day} ${hours}:${minutes}:${seconds}`)
      setupPredictedTime = `${year}/${month}/${day} ${hours}:${minutes}:${seconds}`
      formingDevLog(`设置的 setupPredictedTime:`, setupPredictedTime)
    } else {
      // 如果没有時間後段取数据，检查特殊条件：当生産品種是'生产停止'且次生産品種有数据且不是'生产停止'时，显示下一日15:00
      // 注意：这里需要先判断isProductionStop和nextProductName，但finalNextProductName在后面才设置
      // 所以先用nextProductName判断（如果nextProductName为空或'生产停止'，finalNextProductName也会是空或'生产停止'）
      const shouldUseSpecialCondition =
        isProductionStop && nextProductName !== '' && nextProductName !== '生产停止'

      formingDevLog('特殊条件检查:', {
        isProductionStop,
        nextProductName,
        shouldUseSpecialCondition,
        setupAfterHours,
      })

      if (shouldUseSpecialCondition) {
        // 检查指定日是否是星期五
        const isFilterDateFriday = JapanDateUtils.getDayOfWeek(filterDate) === 5

        // 检查指定日是否是星期六
        const isFilterDateSaturday = JapanDateUtils.isSaturday(filterDate)

        if (isFilterDateFriday) {
          // 特殊处理：如果指定日是星期五，且生産品種是'生产停止'，次生産品種有生产产品
          // 检查星期六是否有生产数据
          const saturday = new Date(filterDate + 'T12:00:00')
          saturday.setDate(saturday.getDate() + 1) // 下一天（星期六）
          const saturdayStr = saturday.toISOString().split('T')[0]

          formingDevLog(`检查星期五 ${filterDate} 的下一天星期六 ${saturdayStr} 是否有生产数据`)

          let hasSaturdayProduction = false

          if (planData && planData.length > 0) {
            // 使用所有设备的数据检查星期六是否有生产
            const saturdayProducts = planData.filter((item: any) => {
              const itemDate = JapanDateUtils.normalizeDate(item.plan_date || '')
              return itemDate === saturdayStr
            })

            hasSaturdayProduction = saturdayProducts.some((product: any) => {
              const quantity = parseInt(product.quantity) || 0
              return quantity > 0
            })

            formingDevLog(
              `星期六 ${saturdayStr} 有生产数据:`,
              hasSaturdayProduction,
              '产品数据:',
              saturdayProducts.length > 0 ? `找到${saturdayProducts.length}条记录` : '无数据',
            )
          }

          // 如果星期六没有生产数据，使用星期五当天15:00
          if (!hasSaturdayProduction) {
            const targetDate = new Date(filterDate + 'T15:00:00')
            formingDevLog(
              `星期五特殊情况 - 星期六没有生产数据，使用星期五当天15:00，设备名称: ${machineName}`,
            )

            const year = targetDate.getFullYear()
            const month = String(targetDate.getMonth() + 1).padStart(2, '0')
            const day = String(targetDate.getDate()).padStart(2, '0')
            const hours = String(targetDate.getHours()).padStart(2, '0')
            const minutes = String(targetDate.getMinutes()).padStart(2, '0')
            const seconds = String(targetDate.getSeconds()).padStart(2, '0')
            setupPredictedTime = `${year}/${month}/${day} ${hours}:${minutes}:${seconds}`
            formingDevLog(
              '指定日是星期五且星期六无生产数据，使用星期五当天15:00，设置setupPredictedTime为:',
              setupPredictedTime,
            )
          } else {
            // 星期六有生产数据，使用正常逻辑（下一日15:00）
            const targetDate = new Date(filterDate + 'T15:00:00')
            targetDate.setDate(targetDate.getDate() + 1) // 星期六
            const year = targetDate.getFullYear()
            const month = String(targetDate.getMonth() + 1).padStart(2, '0')
            const day = String(targetDate.getDate()).padStart(2, '0')
            const hours = String(targetDate.getHours()).padStart(2, '0')
            const minutes = String(targetDate.getMinutes()).padStart(2, '0')
            const seconds = String(targetDate.getSeconds()).padStart(2, '0')
            setupPredictedTime = `${year}/${month}/${day} ${hours}:${minutes}:${seconds}`
            formingDevLog(
              '指定日是星期五且星期六有生产数据，使用星期六15:00，设置setupPredictedTime为:',
              setupPredictedTime,
            )
          }
        } else if (isFilterDateSaturday) {
          // 特殊处理：如果指定日是星期六，且生産品種是'生产停止'，次生産品種有生产产品
          // 段取開始時間应该是：指定日（星期六）当天 15:00
          // 例如：如果指定日是11/8（星期六），那么段取開始時間应该是11/8（星期六）15:00

          // 使用指定日（星期六）当天 15:00（无需额外调整，因为没有累加运行时间）
          const targetDate = new Date(filterDate + 'T15:00:00')
          formingDevLog(`星期六特殊情况 - 使用当天15:00，设备名称: ${machineName}`)

          const year = targetDate.getFullYear()
          const month = String(targetDate.getMonth() + 1).padStart(2, '0')
          const day = String(targetDate.getDate()).padStart(2, '0')
          const hours = String(targetDate.getHours()).padStart(2, '0')
          const minutes = String(targetDate.getMinutes()).padStart(2, '0')
          const seconds = String(targetDate.getSeconds()).padStart(2, '0')
          setupPredictedTime = `${year}/${month}/${day} ${hours}:${minutes}:${seconds}`
          formingDevLog(
            '指定日是星期六，使用当天（星期六）15:00，设置setupPredictedTime为:',
            setupPredictedTime,
          )
        } else {
          // 非星期六的情况：需要考虑星期一+前周六有生产的特殊情况
          let targetDate: Date

          // 检查是否是星期一且前一周星期六有生产的情况
          const baseDate = getBaselineStartDate(filterDate, machineData, dateIndex, planData)
          const isSpecialMondayCase = baseDate !== getPreviousWorkingDate(filterDate)

          if (isSpecialMondayCase) {
            // 星期一且前一周星期六有生产，使用星期六15:00作为基准
            targetDate = new Date(baseDate + 'T15:00:00')
            formingDevLog(`星期一特殊情况：使用前一周星期六 ${baseDate} 15:00 作为段取開始時間`)
          } else {
            // 其他情况：计算下一日15:00
            targetDate = new Date(filterDate + 'T15:00:00')
            targetDate.setDate(targetDate.getDate() + 1)
            let targetDateStr = targetDate.toISOString().split('T')[0]

            // 检查下一日是否是星期天，或者是否有数据
            const dayOfWeek = JapanDateUtils.getDayOfWeek(targetDateStr)
            const isSunday = dayOfWeek === 0

            // 如果下一日是星期天，或者没有数据，查找下一个有数据的日期
            if (isSunday || !DataIndexUtils.findValidProducts(dateIndex, targetDateStr).length) {
              // 从下一日开始查找有效日期（排除星期天）
              const validDates = DataIndexUtils.findValidDatesAfter(
                dateIndex,
                targetDateStr,
                false, // 包含起始日期
              )

              if (validDates.length > 0) {
                // 找到第一个有效日期
                targetDateStr = validDates[0]
                targetDate = new Date(targetDateStr + 'T15:00:00')
                formingDevLog('下一日是星期天或无数据，跳到下一个有数据的日期:', targetDateStr)
              } else {
                // 如果找不到有效日期，使用原来的下一日（即使它是星期天）
                formingDevLog('未找到有效日期，使用原下一日:', targetDateStr)
              }
            }
          }

          // 无需额外调整（因为这里是直接设置15:00，没有累加运行时间）
          formingDevLog(`非星期六特殊情况 - 使用计算出的日期15:00，设备名称: ${machineName}`)

          // 格式化日期时间：YYYY/MM/DD HH:mm:ss
          const year = targetDate.getFullYear()
          const month = String(targetDate.getMonth() + 1).padStart(2, '0')
          const day = String(targetDate.getDate()).padStart(2, '0')
          const hours = String(targetDate.getHours()).padStart(2, '0')
          const minutes = String(targetDate.getMinutes()).padStart(2, '0')
          const seconds = String(targetDate.getSeconds()).padStart(2, '0')
          setupPredictedTime = `${year}/${month}/${day} ${hours}:${minutes}:${seconds}`
          formingDevLog('使用特殊条件，设置setupPredictedTime为:', setupPredictedTime)
        }
      } else if (nextProduct && (nextProduct as any).plan_date) {
        // 如果不满足特殊条件，使用原来的逻辑：优先使用实际计划的日期
        const setupDate = JapanDateUtils.normalizeDate((nextProduct as any).plan_date)
        if (setupDate) {
          setupPredictedTime = `${setupDate.replace(/-/g, '/')} 6:00:01`
          formingDevLog(
            '使用原逻辑（nextProduct日期），设置setupPredictedTime为:',
            setupPredictedTime,
          )
        }
      } else if (nextValidDate) {
        // 如果没有实际计划但有计算出的有效日期，使用有效日期
        setupPredictedTime = `${nextValidDate.replace(/-/g, '/')} 6:00:01`
        formingDevLog('使用原逻辑（nextValidDate），设置setupPredictedTime为:', setupPredictedTime)
      }
    }

    // 判断段替後生産品種和生産品種是否一致
    // 注意：isProductionStop 和 currentProductName 已经在上面定义过了
    const isSameProduct =
      currentProductName && nextProductName && currentProductName.trim() === nextProductName.trim()

    // 判断下一个产品的日期是否是周末（星期六或星期日），以及是否是星期日（使用日本时区）
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

    formingDevLog(
      `下一个产品日期判断: nextProductDateStr=${nextProductDateStr}, isNextDateWeekend=${isNextDateWeekend}, isNextDateSunday=${isNextDateSunday}`,
    )

    // 如果产品名一致，或者日期是星期日，清空相关字段
    // 特殊情况：如果指定日是星期五或星期六，且生产品种是'生产停止'，次生产品种有数据，使用指定日当天15:00（不受isSameProduct影响）
    const isFilterDateFridayCheck = JapanDateUtils.getDayOfWeek(filterDate) === 5
    const isFilterDateSaturdayCheck = JapanDateUtils.isSaturday(filterDate)
    const isWeekendSpecialCase =
      (isFilterDateFridayCheck || isFilterDateSaturdayCheck) &&
      isProductionStop &&
      nextProductName !== '' &&
      nextProductName !== '生产停止'

    const finalSetupAfterHours = isSameProduct || isNextDateSunday ? '' : setupAfterHours
    let finalSetupPredictedTime = ''

    formingDevLog(`最终处理逻辑检查:`)
    formingDevLog(`  isSameProduct: ${isSameProduct}`)
    formingDevLog(`  isNextDateSunday: ${isNextDateSunday}`)
    formingDevLog(`  isFilterDateFriday: ${isFilterDateFridayCheck}`)
    formingDevLog(`  isFilterDateSaturday: ${isFilterDateSaturdayCheck}`)
    formingDevLog(`  isWeekendSpecialCase: ${isWeekendSpecialCase}`)
    formingDevLog(`  setupPredictedTime: ${setupPredictedTime}`)

    if (isWeekendSpecialCase && setupPredictedTime) {
      // 星期五或星期六特殊情况：使用指定日当天15:00（不受isSameProduct影响）
      finalSetupPredictedTime = setupPredictedTime
      formingDevLog(
        `  使用星期五/星期六特殊情况，finalSetupPredictedTime: ${finalSetupPredictedTime}`,
      )
    } else {
      // 其他情况：如果产品名一致，或者日期是星期日，清空
      finalSetupPredictedTime = isSameProduct || isNextDateSunday ? '' : setupPredictedTime
      formingDevLog(`  使用普通逻辑，finalSetupPredictedTime: ${finalSetupPredictedTime}`)
    }
    // 如果产品名一致，或者日期是星期日，清空次生産品種；如果没有生产产品，显示'生产停止'
    let finalNextProductName = ''
    formingDevLog(
      `决定次生産品種: isSameProduct=${isSameProduct}, isNextDateSunday=${isNextDateSunday}, isNextDateWeekend=${isNextDateWeekend}, nextProductName='${nextProductName}'`,
    )

    if (isSameProduct || isNextDateSunday) {
      // 如果日期是星期日，不显示任何数据
      formingDevLog(`因为产品相同或下一个日期是星期日，清空次生産品種`)
      finalNextProductName = ''
    } else if (isNextDateWeekend) {
      // 如果下一个产品的日期是周末（星期六或星期日，但星期日已被排除）
      // 这里只处理星期六的情况
      formingDevLog(`下一个产品日期是周末，检查是否有产品名`)
      if (nextProductName && nextProductName.trim() !== '') {
        // 有数据，显示数据
        formingDevLog(`有产品名，显示: ${nextProductName}`)
        finalNextProductName = nextProductName
      } else {
        // 没有数据，显示'生产停止'
        formingDevLog(`没有产品名，显示生产停止`)
        finalNextProductName = '生产停止'
      }
    } else if (!nextProductName || nextProductName.trim() === '') {
      // 不是周末，但没有生产产品，显示'生产停止'
      formingDevLog(`不是周末但没有产品名，显示生产停止`)
      finalNextProductName = '生产停止'
    } else {
      // 不是周末，有生产产品，显示产品名称
      formingDevLog(`不是周末且有产品名，显示: ${nextProductName}`)
      finalNextProductName = nextProductName
    }

    formingDevLog(`最终次生産品種: '${finalNextProductName}'`)

    // 判断次生産見込数：如果和指定生产日是同一天，显示数据；如果不是同一天，不显示数据；如果是星期日，不显示数据
    let finalNextQuantity: number | '' = ''
    if (isSameProduct || isNextDateSunday) {
      finalNextQuantity = ''
    } else if (nextProduct && (nextProduct as any).plan_date) {
      // 获取下一个产品的生产日期
      const nextProductPlanDate = JapanDateUtils.normalizeDate((nextProduct as any).plan_date)
      // 如果和指定生产日是同一天，显示数据
      if (nextProductPlanDate === filterDate) {
        finalNextQuantity = nextQuantity || ''
      } else {
        // 如果不是同一天，不显示数据
        finalNextQuantity = ''
      }
    } else if (nextValidDate && nextValidDate === filterDate) {
      // 如果有效日期和指定生产日是同一天，显示数据
      finalNextQuantity = nextQuantity || ''
    } else {
      // 其他情况，不显示数据
      finalNextQuantity = ''
    }

    // 如果生産品種是'生産停止'，根据次生産品種的情况调整段取予測時間
    // 注意：如果時間後段取有数据，已经计算出了setupPredictedTime，优先使用计算出的时间
    // 注意：如果满足特殊条件（生产停止+次生产品种有数据），setupPredictedTime已经在上面设置为下一日15:00，这里不再覆盖
    if (isProductionStop && (!setupPredictedTime || setupPredictedTime === '')) {
      // 使用原始nextProductName判断，而不是finalNextProductName（因为可能被isSameProduct清空）
      // 如果次生産品種没有生产产品，段取予測時間不显示
      if (!nextProductName || nextProductName.trim() === '') {
        finalSetupPredictedTime = ''
      } else {
        // 如果次生産品種有生产产品，段取予測時間显示该产品生产日+'15:00:00'
        // 但特殊条件已经在上面处理了（下一日15:00），所以这里只在没有设置setupPredictedTime时才执行
        if (nextProduct && (nextProduct as any).plan_date) {
          const nextProductDate = JapanDateUtils.normalizeDate((nextProduct as any).plan_date)
          if (nextProductDate) {
            finalSetupPredictedTime = `${nextProductDate.replace(/-/g, '/')} 15:00:00`
          }
        } else if (nextValidDate) {
          // 如果没有实际计划但有计算出的有效日期，使用有效日期
          finalSetupPredictedTime = `${nextValidDate.replace(/-/g, '/')} 15:00:00`
        }
      }
    }

    // 如果次生産品種字段显示'生产停止'或为空，段取予測時間不显示
    // 但如果時間後段取有数据且已计算出时间，则保留计算出的时间
    if (
      (finalNextProductName === '生产停止' || finalNextProductName === '') &&
      (!setupPredictedTime || setupPredictedTime === '')
    ) {
      finalSetupPredictedTime = ''
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
        const defectQty = scheduleData.defect_qty || 0
        const upstreamDefectQty = scheduleData.upstream_defect_qty_total || 0
        remainingProduction = Math.max(
          0,
          totalPlanQuantity - actualProduction - defectQty - upstreamDefectQty,
        )
        formingDevLog(
          `[生産計画数] 设备: ${machineName}, 产品: ${currentProductName}, 順位: ${currentOperator} (转换为数字: ${operatorAsNumber}), 計画数: ${totalPlanQuantity}, 実績数: ${actualProduction}, 不良数: ${defectQty}, 前工程不良: ${upstreamDefectQty}, 生産残数: ${remainingProduction}`,
        )
      } else {
        formingDevLog(
          `[生産計画数] 未找到匹配数据，设备: ${machineName}, 产品: ${currentProductName}, 順位: ${currentOperator} (转换为数字: ${operatorAsNumber}), 查找key: ${scheduleKey}`,
        )
      }
    }

    // 備考字段逻辑：如果当日生产数据有3个产品，把第3个产品名写入備考字段
    let remarksText = ''
    formingDevLog(
      `[備考] 检查当日产品数量，设备: ${machineName}, 当日产品数: ${currentProducts.length}`,
    )

    if (currentProducts.length >= 3) {
      // 获取第3个产品（索引为2）
      const thirdProduct = currentProducts[2]
      const thirdProductName = (thirdProduct as any)?.product_name || ''

      if (thirdProductName && thirdProductName.trim() !== '') {
        remarksText = `次生産品種：${thirdProductName}`
        formingDevLog(`[備考] 当日有3个或以上产品，第3个产品名: ${thirdProductName}`)
      }
    } else {
      formingDevLog(`[備考] 当日产品数少于3个，不填写備考`)
    }

    // 获取operator字段（順位）
    const operator = isProductionStop
      ? ''
      : ((currentProduct as any)?.operator || '').toString().trim()

    // 操業度：設備操業度の操業度差異(H)と同値（表示は整数）
    const rawOp = productionPlanRateMap.get(machineName)
    let operationVariance: string = ''
    if (rawOp !== undefined && rawOp !== null && rawOp !== '') {
      const n = Number(rawOp)
      operationVariance = isNaN(n) ? String(rawOp) : String(Math.round(n))
    }
    const plannedWorkingHours = plannedWorkHoursMap.get(machineName)

    // 行データを返却
    return {
      workTime: workTime || '',
      machineCd: currentMachineCd,
      line: machineName,
      plannedWorkingHours:
        plannedWorkingHours !== undefined && plannedWorkingHours !== null
          ? Number(plannedWorkingHours).toFixed(1)
          : '',
      operationVariance,
      operator: operator,
      startTime,
      productName: isProductionStop ? '生産停止' : currentProductName,
      totalPlanQuantity: isProductionStop ? '' : totalPlanQuantity,
      actualProduction: isProductionStop ? '' : actualProduction,
      remainingProduction: isProductionStop ? '' : remainingProduction,
      efficiency: isProductionStop ? '' : efficiency,
      planQuantity: isProductionStop ? '' : currentQuantity,
      setupAfterHours: finalSetupAfterHours,
      setupPredictedTime: finalSetupPredictedTime,
      nextProductName: finalNextProductName,
      nextQuantity: finalNextQuantity,
      remarks: remarksText,
    }
  })

  // 全ての非同期処理の完了を待機
  const tableRows = await Promise.all(tableRowsPromises)

  return { tableRows, productionDate, totalQuantity, currentDateTime }
}

/** 段取予定表の印刷用HTMLをデータから生成（プレビュー編集後の印刷に使用） */
const buildSetupSchedulePrintHtml = (data: {
  tableRows: any[]
  productionDate: string
  totalQuantity: number
  currentDateTime: string
}) => {
  const { tableRows, productionDate, totalQuantity, currentDateTime } = data
  return `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>成型生産計画段替予定表</title>
      <style>
        @page {
          size: A4 landscape;
          margin: 12mm;
          /* 打印详细设定 */
          marks: none; /* 不显示裁剪标记 */
          bleed: 0mm; /* 无出血 */
          /* 单面打印 */
          page-break-after: auto;
        }

        /* 打印媒体查询 - 确保打印样式正确应用 */
        @media print {
          @page {
            size: A4 landscape;
            margin: 12mm;
            marks: none;
            bleed: 0mm;
          }

          /* 确保打印时不显示背景色（除非需要） */
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

        @media print {
          html, body {
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
          }
        }

        .print-container {
          width: 100%;
          height: 100%;
          position: relative;
          min-height: 100vh;
          display: flex;
          flex-direction: column;
        }

        .table-wrapper {
          flex: 1;
          overflow: hidden;
        }

        .print-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 6px;
          padding-bottom: 3px;
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

        .print-operation-note {
          position: absolute;
          bottom: 3mm;
          left: 8mm;
          font-size: 11px;
          color: #000;
          text-align: left;
        }

        .print-footer-note {
          position: absolute;
          bottom: 3mm;
          right: 8mm;
          font-size: 11px;
          color: #ff0000;
          text-align: right;
        }

        .main-table {
          width: 100%;
          border-collapse: collapse;
          border: 2px solid #000;
          font-size: 10px;
        }

        .main-table th,
        .main-table td {
          border: 1px solid #000;
          padding: 2px 2px;
          text-align: center;
          vertical-align: middle;
          color: #000 !important;
        }

        /* 表格外边框粗体 */
        /* 表头第一行的上边框 */
        .main-table thead tr:first-child th {
          border-top: 2px solid #000 !important;
        }

        /* 表头第一列的左边框 */
        .main-table thead tr th:first-child {
          border-left: 2px solid #000 !important;
        }

        /* 表头最后一列的右边框 */
        .main-table thead tr th:last-child {
          border-right: 2px solid #000 !important;
        }

        /* 表体最后一行的下边框 */
        .main-table tbody tr:last-child td {
          border-bottom: 2px solid #000 !important;
        }

        /* 表体第一列的左边框 */
        .main-table tbody tr td:first-child {
          border-left: 2px solid #000 !important;
        }

        /* 表体最后一列的右边框 */
        .main-table tbody tr td:last-child {
          border-right: 2px solid #000 !important;
        }

        .main-table th {
          background-color: #f0f0f0;
          font-weight: bold;
          font-size: 10px;
          height: 20px;
          line-height: 1.1;
        }

        .main-table thead tr:first-child th[colspan] {
          font-size: 9px;
          font-weight: 600;
          padding: 3px 2px;
          background-color: #e8e8e8;
        }

        .main-table .bold-border-col {
          border-left: 2px solid #000 !important;
          border-right: 2px solid #000 !important;
        }

        .main-table thead tr:first-child th.bold-border-col {
          border-top: 2px solid #000 !important;
        }

        .main-table thead tr:last-child th.bold-border-col:first-child {
          border-top: 2px solid #000 !important;
        }

        .main-table td {
          font-size: 10px;
          height: 19px;
          line-height: 1.5;
        }

        .main-table th {
          font-weight: 400 !important;
        }

        .main-table th.plan-quantity-header {
          font-weight: 400 !important;
        }

        /* 确保表格内所有文字都是纯黑色 */
        .main-table th,
        .main-table td,
        .main-table th *,
        .main-table td * {
          color: #000 !important;
        }

        .main-table .reference-date-red {
          color: #e00 !important;
        }

        .numeric-cell {
          text-align: right;
          padding-right: 8px;
        }

        .main-table .blank-col {
          border: none !important;
          border-top: none !important;
          border-bottom: none !important;
          border-left: none !important;
          border-right: none !important;
          background-color: transparent !important;
          padding: 0 !important;
        }

        /* ライン字段左侧粗边框 */
        .main-table .line-col {
          border-left: 2px solid #000 !important;
        }

        /* 参考列表头上边框粗体 */
        .main-table thead tr:last-child th.reference-col {
          border-top: 2px solid #000 !important;
        }

        /* 操業度：負数は赤表示 */
        .main-table .operation-negative {
          color: #e00 !important;
        }

        /* 操業度(進捗)：显示约3个字符宽 */
        .main-table .op-progress-col {
          width: 7ch;
          min-width: 7ch;
          max-width: 7ch;
        }

        .main-table .planned-hours {
          text-align: center;
          font-weight: 600;
          border-radius: 3px;
        }

        /* 当日計画数を予定稼働(H)と同じく太字表示（印刷HTML用） */
        .main-table td.plan-quantity-cell {
          font-weight: 700;
          text-align: center;
        }
        .main-table .planned-hours-low {
          background: #fdeaea;
        }
        .main-table .planned-hours-mid {
          background: #fff6db;
        }
        .main-table .planned-hours-high {
          background: #e8f7ec;
        }
        .main-table .planned-hours-very-high {
          background: #cfeecf;
        }
        .main-table .next-arrow-cell {
          text-align: center;
          font-size: 13px;
          font-weight: 900;
          border-top: none !important;
          border-bottom: none !important;
        }

      </style>
    </head>
    <body>
      <div class="print-container">
        <!-- 头部区域 -->
        <div class="print-header">
          <div class="header-left">
            <div class="print-title">成型生産計画段替予定表</div>
          </div>
          <div class="print-center-section">
            <div class="print-production-date-wrapper">
              <div class="print-production-date">生産日: ${productionDate}</div>
              <div class="print-aggregation-time">集計時間:前日15:00~当日15:00</div>
            </div>
          </div>
          <div class="header-right">
            <div class="print-date-time">${currentDateTime}</div>
            <div class="print-total">生産計画合計数 ${totalQuantity.toLocaleString('ja-JP')}</div>
          </div>
        </div>

        <!-- 主要表格 -->
        <div class="table-wrapper">
        <table class="main-table">
          <thead>
            <tr>
              <th colspan="1" class="bold-border-col" style="width: 8%; border-bottom: none;"><span class="reference-date-red">${currentDateTime.split(' ')[0]}</span>までの実績(算出)</th>
              <th rowspan="2" class="blank-col" style="width: 3%;"> </th>
              <th rowspan="2" class="line-col" style="width: 7%;">ライン</th>
              <th rowspan="2" style="width: 8%;">予定稼働(H)</th>
              <th rowspan="2" style="width: 7%;">操業度(進捗)</th>
              <th rowspan="2" style="width: 12%;">生産品種</th>
              <th rowspan="2" style="width: 7%;">能率(本/h)</th>
              <th rowspan="2" class="plan-quantity-header" style="width: 7%;">当日計画数</th>
              <th rowspan="2" style="width: 6%;">残生産時間</th>
              <th rowspan="2" class="blank-col" style="width: 6%;"> </th>
              <th rowspan="2" style="width: 9%;">次生産品種</th>
              <th rowspan="2" style="width: 8%;">次品種計画数</th>
              <th rowspan="2" style="width: 15%;">備考</th>
            </tr>
            <tr>
              <th class="bold-border-col reference-col" style="width: 8%;">生産残数(参考)</th>
            </tr>
          </thead>
          <tbody>
            ${tableRows
              .map((row) => {
                return `
              <tr>
                <td class="numeric-cell bold-border-col">${row.totalPlanQuantity ? row.totalPlanQuantity.toLocaleString('ja-JP') : ''}</td>
                <td class="blank-col"> </td>
                <td class="line-col">${row.line}</td>
                <td class="${(() => { const n = Number(row.plannedWorkingHours); if (!Number.isFinite(n)) return 'planned-hours planned-hours-empty'; if (n === 0) return 'planned-hours planned-hours-empty'; if (n < 8) return 'planned-hours planned-hours-low'; if (n < 16) return 'planned-hours planned-hours-mid'; if (n < 22.5) return 'planned-hours planned-hours-high'; return 'planned-hours planned-hours-very-high'; })()}">${(() => { const v = Number(row.plannedWorkingHours); return Number.isFinite(v) && v !== 0 ? v.toFixed(1) : ''; })()}</td>
                <td class="op-progress-col ${(() => { const v = row.operationVariance; if (v === undefined || v === null || v === '') return 'numeric-cell'; const n = Number(v); return isNaN(n) ? 'numeric-cell' : (n < 0 ? 'numeric-cell operation-negative' : 'numeric-cell'); })()}">${(() => { const v = row.operationVariance; if (v === undefined || v === null || v === '') return ''; const n = Number(v); return isNaN(n) ? String(v) : String(Math.round(n)); })()}</td>
                <td>${row.productName}</td>
                <td class="numeric-cell">${row.efficiency || ''}</td>
                <td class="numeric-cell plan-quantity-cell">${row.planQuantity ? row.planQuantity.toLocaleString('ja-JP') : ''}</td>
                <td class="numeric-cell">${row.setupAfterHours || ''}</td>
                <td class="next-arrow-cell">${row.nextProductName && String(row.nextProductName).trim() !== '' ? '&rarr;' : ''}</td>
                <td>${row.nextProductName || ''}</td>
                <td class="numeric-cell">${(() => { const v = row.nextQuantity; if (v == null || v === '') return ''; const n = Number(v); return isNaN(n) ? '' : n.toLocaleString('ja-JP'); })()}</td>
                <td>${row.remarks || ''}</td>
              </tr>
            `
              })
              .join('')}
          </tbody>
        </table>
        </div>


        <!-- フッター注釈 -->
        <div class="print-footer-note">

        </div>
      </div>
    </body>
    </html>
  `
}

// 計画データを更新
const refreshPlanData = () => {
  loadPlanData()
}

// 加载設備下拉框选项
const loadMachineOptionsForWorkTime = async () => {
  try {
    const result = (await request.get('/api/machine-work-time-config/machines')) as ApiResponse | unknown[]
    const data: any[] = Array.isArray(result) ? (result as any[]) : Array.isArray((result as ApiResponse)?.data) ? ((result as ApiResponse).data as any[]) : []
    machineOptionsForWorkTime.value = data.map((item: any) => ({
      machine_cd: item.machine_cd,
      machine_name: item.machine_name || item.machine_cd || '',
    }))
  } catch (error: unknown) {
    console.error('加载設備选项失败:', error)
  }
}

// 处理設備コード选择变化
const handleMachineCdChange = (machineCd: string) => {
  const selectedMachine = machineOptionsForWorkTime.value.find((m) => m.machine_cd === machineCd)
  if (selectedMachine) {
    workTimeConfigForm.machine_name = selectedMachine.machine_name
  } else {
    workTimeConfigForm.machine_name = ''
  }
}

// 打开設備運行時間設定弹窗
const openWorkTimeConfigDialog = async () => {
  workTimeConfigDialogVisible.value = true
  await loadMachineOptionsForWorkTime()
  await loadWorkTimeConfig()
}

// 加载設備運行時間設定数据
const loadWorkTimeConfig = async () => {
  try {
    workTimeConfigLoading.value = true

    // 获取已保存的配置（machine_work_time_config 表）
    const configResult = (await request.get('/api/machine-work-time-config/work-time-config')) as ApiResponse | unknown[]
    const configs: any[] = Array.isArray(configResult)
      ? (configResult as any[])
      : Array.isArray((configResult as ApiResponse)?.data)
        ? ((configResult as ApiResponse).data as any[])
        : []
    workTimeConfigData.value = configs.map((item: any) => ({
      id: item.id,
      machine_cd: item.machine_cd,
      machine_name: item.machine_name,
      time_slot_17_19: item.time_slot_17_19 === 1,
      time_slot_19_21: item.time_slot_19_21 === 1,
      time_slot_6_8: item.time_slot_6_8 === 1,
    }))
  } catch (error: unknown) {
    console.error('加载設備運行時間設定失败:', error)
    ElMessage.error(error instanceof Error ? error.message : '設定の読み込みに失敗しました')
  } finally {
    workTimeConfigLoading.value = false
  }
}

// 处理时间段勾选变化
const handleTimeSlotChange = (row: any, slot: string) => {
  // 可以在这里添加实时保存或其他逻辑
  formingDevLog(
    `设备 ${row.machine_name} 的 ${slot} 时间段已${row[`time_slot_${slot}`] ? '勾选' : '取消'}`,
  )
}

// 保存設備運行時間設定（批量保存）
const saveWorkTimeConfig = async () => {
  try {
    savingWorkTimeConfig.value = true

    // 准备保存的数据
    const configs = workTimeConfigData.value.map((item) => ({
      machine_cd: item.machine_cd,
      machine_name: item.machine_name,
      time_slot_17_19: item.time_slot_17_19,
      time_slot_19_21: item.time_slot_19_21,
      time_slot_6_8: item.time_slot_6_8,
    }))

    const result = (await request.post('/api/machine-work-time-config/work-time-config', {
      configs,
    })) as ApiResponse

    if (isApiSuccess(result)) {
      const count = (result.data as { count?: number })?.count ?? configs.length
      ElMessage.success({
        message: `保存成功：${count} 件の設備運行時間設定を更新しました`,
        duration: 3000,
      })
      // 刷新数据
      await loadWorkTimeConfig()
      // 清空缓存
      workTimeConfigCache.clear()
    } else {
      throw new Error((result.message as string) || '保存失敗')
    }
  } catch (error: unknown) {
    console.error('保存設備運行時間設定失败:', error)
    ElMessage.error(error instanceof Error ? error.message : '保存失敗')
  } finally {
    savingWorkTimeConfig.value = false
  }
}

// 打开添加設備運行時間設定弹窗
const openAddWorkTimeConfigDialog = async () => {
  workTimeConfigForm.id = null
  workTimeConfigForm.machine_cd = ''
  workTimeConfigForm.machine_name = ''
  workTimeConfigForm.timeSlots = []
  // 确保设备列表已加载
  if (machineOptionsForWorkTime.value.length === 0) {
    await loadMachineOptionsForWorkTime()
  }
  workTimeConfigFormDialogVisible.value = true
}

// 打开编辑設備運行時間設定弹窗
// 保存設備運行時間設定表单（单个添加或更新）
const saveWorkTimeConfigForm = async () => {
  if (!workTimeConfigFormRef.value) return

  try {
    await workTimeConfigFormRef.value.validate()
  } catch (error) {
    return
  }

  try {
    savingWorkTimeConfigForm.value = true

    const timeSlot17_19 = workTimeConfigForm.timeSlots.includes('17_19')
    const timeSlot19_21 = workTimeConfigForm.timeSlots.includes('19_21')
    const timeSlot6_8 = workTimeConfigForm.timeSlots.includes('6_8')

    // 始终以追加方式保存
    const result = (await request.post('/api/machine-work-time-config/work-time-config/single', {
      machine_cd: workTimeConfigForm.machine_cd,
      machine_name: workTimeConfigForm.machine_name,
      time_slot_17_19: timeSlot17_19,
      time_slot_19_21: timeSlot19_21,
      time_slot_6_8: timeSlot6_8,
    })) as ApiResponse

    if (isApiSuccess(result)) {
      ElMessage.success('追加成功')
      workTimeConfigFormDialogVisible.value = false
      // 刷新数据
      await loadWorkTimeConfig()
      // 清空缓存
      workTimeConfigCache.clear()
    } else {
      throw new Error((result.message as string) || '追加失敗')
    }
  } catch (error: unknown) {
    console.error('保存設備運行時間設定表单失败:', error)
    ElMessage.error(error instanceof Error ? error.message : '保存失敗')
  } finally {
    savingWorkTimeConfigForm.value = false
  }
}

// 删除設備運行時間設定
const deleteWorkTimeConfig = async (row: any) => {
  if (!row.id) {
    ElMessage.warning('削除できません：このレコードにIDがありません')
    return
  }

  try {
    await ElMessageBox.confirm(
      `設備 "${row.machine_name}" の運行時間設定を削除しますか？`,
      '削除確認',
      {
        confirmButtonText: '削除',
        cancelButtonText: 'キャンセル',
        type: 'warning',
      },
    )

    const result = (await request.delete(`/api/machine-work-time-config/work-time-config/${row.id}`)) as ApiResponse

    if (isApiSuccess(result)) {
      ElMessage.success('削除成功')
      // 刷新数据
      await loadWorkTimeConfig()
      // 清空缓存
      workTimeConfigCache.clear()
    } else {
      throw new Error((result.message as string) || '削除失敗')
    }
  } catch (error: unknown) {
    if (error !== 'cancel') {
      console.error('削除設備運行時間設定失败:', error)
      ElMessage.error(error instanceof Error ? error.message : '削除失敗')
    }
  }
}

// 日別計画・実績チャート（plan_date ごとに quantity / actual を合計）
const planQtyChartDates = computed(() => {
  if (!planQtyChartDateRange.value || planQtyChartDateRange.value.length !== 2) return [] as string[]
  const [start, end] = planQtyChartDateRange.value
  const dates: string[] = []
  const dStart = new Date(start)
  const dEnd = new Date(end)
  for (let d = new Date(dStart); d <= dEnd; d.setDate(d.getDate() + 1)) {
    dates.push(d.toISOString().split('T')[0])
  }
  return dates
})

const planQtyDailyTotals = computed(() => {
  const totals: Record<string, number> = {}
  planQtyChartRecords.value.forEach((x) => {
    if (!x?.plan_date) return
    const name = (x.product_name ?? '').trim()
    if (!name) return
    const q = parseFloat(String(x.quantity ?? 0)) || 0
    if (q <= 0) return
    totals[x.plan_date] = (totals[x.plan_date] || 0) + q
  })
  return totals
})

/** schedule_details.actual_qty（API では actual_production / actual_qty）を日別に合計 */
const planQtyDailyActualTotals = computed(() => {
  const totals: Record<string, number> = {}
  planQtyChartRecords.value.forEach((x) => {
    if (!x?.plan_date) return
    const name = (x.product_name ?? '').trim()
    if (!name) return
    const a = parseFloat(String(x.actual_production ?? x.actual_qty ?? 0)) || 0
    if (a <= 0) return
    totals[x.plan_date] = (totals[x.plan_date] || 0) + a
  })
  return totals
})

const planQtyChartHasData = computed(() => {
  for (const d of planQtyChartDates.value) {
    if ((planQtyDailyTotals.value[d] || 0) > 0 || (planQtyDailyActualTotals.value[d] || 0) > 0)
      return true
  }
  return false
})

function jstCalendarNow(): Date {
  return new Date(new Date().toLocaleString('en-US', { timeZone: 'Asia/Tokyo' }))
}

function formatYmd(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function formatPlanQtyChartAxisDate(dateStr: string) {
  try {
    const date = new Date(dateStr + 'T00:00:00')
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${month}/${day}`
  } catch {
    return dateStr
  }
}

function getPlanQtyChartTodayStr() {
  return formatYmd(jstCalendarNow())
}

function onPlanQtyChartResize() {
  planQtyChartInstance?.resize()
}

function disposePlanQtyChart() {
  window.removeEventListener('resize', onPlanQtyChartResize)
  if (planQtyChartInstance) {
    planQtyChartInstance.dispose()
    planQtyChartInstance = null
  }
}

function barDatumPlan(date: string, todayStr: string, v: number, radiusBar: [number, number, number, number]) {
  let color: echarts.graphic.LinearGradient
  if (date < todayStr) {
    color = new echarts.graphic.LinearGradient(0, 0, 0, 1, [
      { offset: 0, color: '#bae6fd' },
      { offset: 1, color: '#0284c7' },
    ])
  } else if (date === todayStr) {
    color = new echarts.graphic.LinearGradient(0, 0, 0, 1, [
      { offset: 0, color: '#6ee7b7' },
      { offset: 0.55, color: '#34d399' },
      { offset: 1, color: '#047857' },
    ])
  } else {
    color = new echarts.graphic.LinearGradient(0, 0, 0, 1, [
      { offset: 0, color: '#f1f5f9' },
      { offset: 1, color: '#94a3b8' },
    ])
  }
  return {
    value: v,
    itemStyle: {
      color,
      borderRadius: radiusBar,
      shadowBlur: date === todayStr ? 14 : 8,
      shadowColor: date === todayStr ? 'rgba(4, 120, 87, 0.28)' : 'rgba(2, 132, 199, 0.18)',
      shadowOffsetY: 2,
    },
  }
}

function barDatumActual(date: string, todayStr: string, v: number, radiusBar: [number, number, number, number]) {
  let color: echarts.graphic.LinearGradient
  if (date < todayStr) {
    color = new echarts.graphic.LinearGradient(0, 0, 0, 1, [
      { offset: 0, color: '#fde68a' },
      { offset: 1, color: '#d97706' },
    ])
  } else if (date === todayStr) {
    color = new echarts.graphic.LinearGradient(0, 0, 0, 1, [
      { offset: 0, color: '#fcd34d' },
      { offset: 0.55, color: '#f59e0b' },
      { offset: 1, color: '#b45309' },
    ])
  } else {
    color = new echarts.graphic.LinearGradient(0, 0, 0, 1, [
      { offset: 0, color: '#fef3c7' },
      { offset: 1, color: '#d6d3d1' },
    ])
  }
  return {
    value: v,
    itemStyle: {
      color,
      borderRadius: radiusBar,
      shadowBlur: date === todayStr ? 12 : 6,
      shadowColor: date === todayStr ? 'rgba(180, 83, 9, 0.28)' : 'rgba(217, 119, 6, 0.15)',
      shadowOffsetY: 2,
    },
  }
}

function updatePlanQtyChart() {
  const el = planQtyChartEl.value
  const dates = planQtyChartDates.value
  const totals = planQtyDailyTotals.value
  const actualTotals = planQtyDailyActualTotals.value
  if (!el || dates.length === 0) {
    disposePlanQtyChart()
    return
  }
  const planValues = dates.map((d) => totals[d] || 0)
  const actualValues = dates.map((d) => actualTotals[d] || 0)
  if (!planValues.some((v) => v > 0) && !actualValues.some((v) => v > 0)) {
    disposePlanQtyChart()
    return
  }

  if (!planQtyChartInstance) {
    planQtyChartInstance = echarts.init(el)
    window.addEventListener('resize', onPlanQtyChartResize)
  }

  const cats = dates.map((d) => formatPlanQtyChartAxisDate(d))
  const todayStr = getPlanQtyChartTodayStr()
  const todayIdx = dates.indexOf(todayStr)

  const radiusBar: [number, number, number, number] = [6, 6, 0, 0]
  const planBarData = dates.map((date, idx) =>
    barDatumPlan(date, todayStr, planValues[idx], radiusBar),
  )
  const actualBarData = dates.map((date, idx) =>
    barDatumActual(date, todayStr, actualValues[idx], radiusBar),
  )

  const labelFmt = (params: unknown) => {
    const p = params as { value?: unknown; data?: { value?: unknown } }
    const v =
      typeof p.data === 'object' && p.data != null && typeof p.data.value === 'number'
        ? p.data.value
        : typeof p.value === 'number'
          ? p.value
          : 0
    if (v === 0) return ''
    return v.toLocaleString('ja-JP')
  }

  planQtyChartInstance.setOption(
    {
      backgroundColor: 'transparent',
      animationDuration: 560,
      textStyle: { fontFamily: 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif' },
      legend: {
        top: 6,
        left: 'center',
        itemWidth: 12,
        itemHeight: 12,
        textStyle: { fontSize: 11, color: '#64748b', fontWeight: 600 },
        data: ['計画生産数', '実績生産数'],
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(14, 165, 233, 0.06)' } },
        backgroundColor: 'rgba(15, 23, 42, 0.88)',
        borderWidth: 0,
        borderRadius: 10,
        padding: [10, 14],
        textStyle: { color: '#f8fafc', fontSize: 12 },
        formatter: (params: unknown) => {
          const list = Array.isArray(params) ? params : [params]
          const first = list[0] as { dataIndex?: number } | undefined
          const idx = first?.dataIndex ?? 0
          const rawDate = dates[idx]
          if (!rawDate) return ''
          const pv = planValues[idx] ?? 0
          const av = actualValues[idx] ?? 0
          const ps = Number(pv).toLocaleString('ja-JP')
          const as = Number(av).toLocaleString('ja-JP')
          return `<div style="font-weight:600;margin-bottom:6px">${rawDate}</div>` +
            `<div style="opacity:.95;margin-bottom:2px">計画生産数: ${ps}</div>` +
            `<div style="opacity:.95">実績生産数: ${as}</div>`
        },
      },
      grid: { left: 52, right: 18, top: 52, bottom: dates.length > 14 ? 52 : 44, containLabel: false },
      xAxis: {
        type: 'category',
        data: cats,
        axisLine: { lineStyle: { color: '#e2e8f0', width: 1 } },
        axisTick: { show: false },
        axisLabel: {
          fontSize: 10,
          rotate: dates.length > 14 ? 40 : 0,
          color: '#64748b',
          margin: 10,
          fontWeight: 500,
        },
      },
      yAxis: {
        type: 'value',
        name: '数量',
        nameGap: 8,
        nameTextStyle: { fontSize: 11, color: '#94a3b8', fontWeight: 500 },
        axisLabel: { fontSize: 10, color: '#94a3b8' },
        splitLine: { lineStyle: { type: 'dashed', color: '#e8ecf1', width: 1 } },
        axisLine: { show: false },
        minInterval: 1,
      },
      series: [
        {
          name: '計画生産数',
          type: 'bar',
          barMaxWidth: 22,
          barGap: '12%',
          data: planBarData,
          label: {
            show: true,
            position: 'top',
            distance: 4,
            fontSize: 8,
            fontWeight: 500,
            color: '#475569',
            formatter: labelFmt,
          },
          emphasis: {
            focus: 'series',
            itemStyle: { shadowBlur: 16, shadowColor: 'rgba(14, 165, 233, 0.35)' },
          },
          markLine:
            todayIdx >= 0
              ? {
                  symbol: 'none',
                  lineStyle: { color: 'rgba(245, 158, 11, 0.92)', type: 'dashed', width: 1.5 },
                  label: {
                    formatter: '今日',
                    color: '#c2410c',
                    fontSize: 10,
                    fontWeight: 600,
                    padding: [2, 8],
                    borderRadius: 6,
                    backgroundColor: 'rgba(254, 243, 199, 0.95)',
                  },
                  data: [{ xAxis: todayIdx }],
                }
              : undefined,
        },
        {
          name: '実績生産数',
          type: 'bar',
          barMaxWidth: 22,
          data: actualBarData,
          label: {
            show: true,
            position: 'top',
            distance: 4,
            fontSize: 8,
            fontWeight: 500,
            color: '#92400e',
            formatter: labelFmt,
          },
          emphasis: {
            focus: 'series',
            itemStyle: { shadowBlur: 14, shadowColor: 'rgba(217, 119, 6, 0.38)' },
          },
        },
      ],
    },
    true,
  )
  requestAnimationFrame(() => planQtyChartInstance?.resize())
}

const loadPlanQtyChartData = async () => {
  if (!planQtyChartDateRange.value || planQtyChartDateRange.value.length !== 2) return
  planQtyChartLoading.value = true
  try {
    const params = {
      startDate: planQtyChartDateRange.value[0],
      endDate: planQtyChartDateRange.value[1],
      processName: '成型',
      page: 1,
      limit: 10000,
    }
    const result = (await request.get(planDataApiPath.value, { params })) as ApiResponse
    if (result.success) {
      const records = (result.data as { records?: unknown[] })?.records ?? []
      planQtyChartRecords.value = records.filter(
        (item: any) => item.product_name && String(item.product_name).trim() !== '',
      ) as PlanRecord[]
    } else {
      planQtyChartRecords.value = []
    }
  } catch (e) {
    console.error('日別計画チャートの読み込みに失敗:', e)
    planQtyChartRecords.value = []
  } finally {
    planQtyChartLoading.value = false
    await nextTick()
    updatePlanQtyChart()
  }
}

const setPlanQtyChartMonth = (monthOffset: number) => {
  const now = jstCalendarNow()
  const targetDate = new Date(now.getFullYear(), now.getMonth() + monthOffset, 1)
  const firstDay = new Date(targetDate.getFullYear(), targetDate.getMonth(), 1)
  const lastDay = new Date(targetDate.getFullYear(), targetDate.getMonth() + 1, 0)
  planQtyChartDateRange.value = [formatYmd(firstDay), formatYmd(lastDay)]
  loadPlanQtyChartData()
}

const setDefaultPlanQtyChartRange = () => {
  const now = jstCalendarNow()
  const start = new Date(now)
  start.setDate(start.getDate() - 2)
  const end = new Date(now)
  end.setDate(end.getDate() + 30)
  planQtyChartDateRange.value = [formatYmd(start), formatYmd(end)]
  loadPlanQtyChartData()
}

// 数字格式化（简化版）
const formatNumber = (val: number | string) => {
  const n = typeof val === 'string' ? Number(val) : val
  if (!isFinite(n as number)) return '0'
  return (n as number).toLocaleString('ja-JP')
}

// 能率格式化（显示为"XX"）
const formatEfficiencyRate = (val: number | string) => {
  const n = typeof val === 'string' ? Number(val) : val
  if (!isFinite(n as number)) return '-'
  const formatted = (n as number).toFixed(1)
  return formatted.endsWith('.0') ? `${Math.round(n as number)}` : `${formatted}`
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

// ─────────────────────────────────────────────
// メモ（TODO）— cutting と同一 UX、API は forming-instruction-notes（scope: forming_instruction）
// ─────────────────────────────────────────────
interface FormingInstructionNote {
  id?: number
  content?: string | null
  is_done?: number | boolean
  created_at?: string | null
  updated_at?: string | null
}

const formingInstructionNotesDialogVisible = ref(false)
const formingInstructionNotesLoading = ref(false)
const formingInstructionNotesSaving = ref(false)
const formingInstructionNotesList = ref<FormingInstructionNote[]>([])
const formingInstructionNotesNewContent = ref('')

const formingInstructionNotesCount = computed(() => formingInstructionNotesList.value.length)

async function loadFormingInstructionNotes() {
  formingInstructionNotesLoading.value = true
  try {
    const res = await request.get('/api/plan/forming-instruction-notes', { params: { limit: 200 } })

    formingInstructionNotesList.value = (res as any)?.success
      ? (((res as any).data?.list ?? []) as FormingInstructionNote[])
      : []
  } catch (e) {
    console.error('メモ（TODO）の取得に失敗:', e)
    ElMessage.error('メモ（TODO）の取得に失敗しました')
    formingInstructionNotesList.value = []
  } finally {
    formingInstructionNotesLoading.value = false
  }
}

function openFormingInstructionNotesDialog() {
  formingInstructionNotesDialogVisible.value = true
  formingInstructionNotesNewContent.value = ''
  loadFormingInstructionNotes()
}

async function addFormingInstructionNote() {
  const content = formingInstructionNotesNewContent.value.trim()
  if (!content) {
    ElMessage.warning('内容を入力してください')
    return
  }
  try {
    formingInstructionNotesSaving.value = true
    await request.post('/api/plan/forming-instruction-notes', { content })
    formingInstructionNotesNewContent.value = ''
    await loadFormingInstructionNotes()
    ElMessage.success('追加しました')
  } catch (e) {
    console.error('メモ（TODO）の追加に失敗:', e)
    ElMessage.error('追加に失敗しました')
  } finally {
    formingInstructionNotesSaving.value = false
  }
}

async function toggleFormingInstructionNoteDone(note: FormingInstructionNote, checked: unknown) {
  if (!note.id) return
  const is_done =
    checked === true || checked === 1 || checked === '1' || checked === 'true' ? 1 : 0
  try {
    formingInstructionNotesSaving.value = true
    await request.patch(`/api/plan/forming-instruction-notes/${note.id}`, { is_done })
    note.is_done = is_done
  } catch (e) {
    console.error('メモ（TODO）の更新に失敗:', e)
    ElMessage.error('更新に失敗しました')
    await loadFormingInstructionNotes()
  } finally {
    formingInstructionNotesSaving.value = false
  }
}

async function deleteFormingInstructionNote(note: FormingInstructionNote) {
  if (!note.id) return
  try {
    await ElMessageBox.confirm('このメモを削除しますか？', '削除確認', { type: 'warning' })
    formingInstructionNotesSaving.value = true
    await request.delete(`/api/plan/forming-instruction-notes/${note.id}`)
    await loadFormingInstructionNotes()
    ElMessage.success('削除しました')
  } catch (e) {
    if ((e as { message?: string; name?: string })?.message?.includes('cancel')) return
    if ((e as { name?: string })?.name === 'MessageBox') return
    console.error('メモ（TODO）の削除に失敗:', e)
    ElMessage.error('削除に失敗しました')
  } finally {
    formingInstructionNotesSaving.value = false
  }
}

// ページ初期化
onMounted(() => {
  // 先初始化搜索表单默认值
  initializeSearchForm()
  // 然后加载数据
  loadMachineOptions()
  loadPlanData()
  loadInstructions()
  loadFormingInstructionNotes()
  // 日別計画チャート：当日往前2天 ～ 往后30天（JST）
  setDefaultPlanQtyChartRange()
})

onUnmounted(() => {
  disposePlanQtyChart()
})
</script>

<style scoped>
.molding-instruction-container {
  padding: 4px 6px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  min-height: calc(100vh - 8px);
  position: relative;
  animation: fadeIn 0.6s ease-out;
}

.molding-instruction-container.is-compact {
  padding: 0;
}

.molding-instruction-container.is-compact .page-header {
  padding: 8px 12px;
  margin-bottom: 0;
}

.molding-instruction-container.is-compact .plan-section {
  margin-bottom: 8px;
}

.molding-instruction-container.is-compact .search-bar {
  padding: 6px 10px;
}

.molding-instruction-container.is-compact .stats-grid {
  gap: 10px;
  padding: 0;
}

.molding-instruction-container.is-compact .stat-item {
  padding: 3px 12px;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.molding-instruction-container::before {
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
  margin-bottom: 4px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 0.98) 100%);
  backdrop-filter: blur(10px);
  padding: 8px 14px;
  border-radius: 10px;
  box-shadow:
    0 2px 8px rgba(0, 0, 0, 0.06),
    0 1px 3px rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(226, 232, 240, 0.5);
  position: relative;
  overflow: hidden;
}

.page-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%);
  background-size: 200% 100%;
  animation: gradientShift 3s ease infinite;
}

@keyframes gradientShift {
  0%,
  100% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  position: relative;
  z-index: 1;
}

.header-info {
  flex: 1;
  min-width: 0;
}

.page-header-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.header-stats {
  display: flex;
  align-items: center;
  gap: 6px;
}

.header-stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(226, 232, 240, 0.7);
  border-radius: 8px;
  min-width: 124px;
}

.header-stat-item .stat-icon {
  width: 24px;
  height: 24px;
  font-size: 12px;
  border-radius: 6px;
}

.header-stat-item .stat-value {
  font-size: 13px;
  margin-bottom: 1px;
}

.header-stat-item .stat-label {
  font-size: 9px;
}

.title-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 4px;
}

.title-icon {
  font-size: 20px;
  color: #3b82f6;
  animation: iconPulse 2s ease-in-out infinite;
}

@keyframes iconPulse {
  0%,
  100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.05);
    opacity: 0.8;
  }
}

.page-title {
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(135deg, #1e293b 0%, #3b82f6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
  line-height: 1.3;
  letter-spacing: -0.5px;
}

.page-subtitle {
  font-size: 11px;
  color: #64748b;
  font-weight: 500;
  margin-top: 2px;
  letter-spacing: 0.2px;
}

/* 计划区域样式 */
.plan-section {
  margin-bottom: 10px;
  animation: sectionFadeIn 0.8s ease-out 0.1s both;
}

@keyframes sectionFadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.section-card {
  border-radius: 12px;
  box-shadow:
    0 2px 10px rgba(15, 23, 42, 0.08),
    0 1px 4px rgba(15, 23, 42, 0.06);
  border: 1px solid rgba(226, 232, 240, 0.4);
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(10px);
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  animation: slideInUp 0.8s ease-out;
}

.section-card:hover {
  transform: translateY(-1px);
  box-shadow:
    0 6px 18px rgba(15, 23, 42, 0.12),
    0 2px 8px rgba(15, 23, 42, 0.08);
}

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* コンパクト統計グリッド */
.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  padding: 2px 0;
  margin: 0;
  animation: fadeInScale 1s ease-out 0.2s both;
}

@keyframes fadeInScale {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 12px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 250, 252, 0.95) 100%);
  border-radius: 10px;
  border: 1px solid rgba(226, 232, 240, 0.3);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.stat-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  transition: left 0.5s ease;
}

.stat-item:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.1);
  border-color: rgba(148, 163, 184, 0.6);
  background: linear-gradient(135deg, rgba(255, 255, 255, 1) 0%, rgba(248, 250, 252, 1) 100%);
}

.stat-item:hover::before {
  left: 100%;
}

.stat-icon {
  width: 32px;
  height: 32px;
  border-radius: 7px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 14px;
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
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.1;
  margin-bottom: 2px;
}

.stat-label {
  font-size: 10px;
  color: #64748b;
  font-weight: 500;
}

/* コンパクト検索バー */
.search-bar {
  padding: 8px 12px;
  background: linear-gradient(135deg, rgba(248, 250, 252, 0.95) 0%, rgba(241, 245, 249, 0.95) 100%);
  border-top: 1px solid rgba(226, 232, 240, 0.3);
  backdrop-filter: blur(10px);
  animation: searchBarSlide 0.6s ease-out 0.3s both;
}

@keyframes searchBarSlide {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.search-controls {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.forming-notes-btn-wrap {
  margin-left: auto;
  display: flex;
  align-items: center;
}

.forming-notes-toolbar-btn {
  margin: 0 !important;
  height: 28px !important;
  min-width: 36px;
  padding: 0 10px !important;
  border-radius: 7px !important;
  background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%) !important;
  border-color: #ddd6fe !important;
  color: #5b21b6 !important;
  box-shadow: 0 1px 2px rgba(88, 28, 135, 0.08) !important;
}

.forming-notes-toolbar-btn:hover {
  background: linear-gradient(135deg, #ede9fe 0%, #ddd6fe 100%) !important;
  border-color: #a78bfa !important;
  color: #4c1d95 !important;
}

.notes-badge-wrap {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.notes-count-badge {
  position: absolute;
  top: -7px;
  right: -8px;
  padding: 0;
  border-radius: 0;
  background: transparent;
  border: none;
  box-shadow: none;
  color: #ef4444;
  font-size: 12px;
  font-weight: 900;
  line-height: 1;
  text-align: center;
}

.forming-instruction-notes-dialog :deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid #ddd6fe;
  box-shadow: 0 24px 48px -20px rgba(76, 29, 149, 0.45);
}

.forming-instruction-notes-dialog :deep(.el-dialog__header) {
  margin-right: 0;
  padding: 12px 16px 10px;
  border-bottom: 1px solid #ede9fe;
  background: linear-gradient(135deg, #f5f3ff 0%, #eef2ff 55%, #ecfeff 100%);
}

.forming-instruction-notes-dialog :deep(.el-dialog__title) {
  font-size: 14px;
  font-weight: 700;
  color: #5b21b6;
}

.forming-instruction-notes-dialog :deep(.el-dialog__body) {
  padding: 12px 16px 8px;
}

.forming-instruction-notes-dialog :deep(.el-dialog__footer) {
  padding: 8px 16px 14px;
}

.cutting-notes-dialog-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.cutting-notes-add {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.cutting-notes-input :deep(.el-textarea__inner) {
  border-radius: 10px;
  border: 1px solid #e9d5ff;
  font-size: 12px;
}

.cutting-notes-input :deep(.el-textarea__inner:focus) {
  box-shadow: 0 0 0 1px #c4b5fd inset;
}

.cutting-notes-add-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.cutting-notes-char-count {
  font-size: 11px;
  color: #94a3b8;
}

.cutting-notes-add-btn {
  border-radius: 8px !important;
}

.cutting-notes-scrollbar {
  border-radius: 10px;
}

.cutting-notes-empty {
  padding: 24px 12px;
  text-align: center;
  font-size: 12px;
  color: #94a3b8;
}

.cutting-notes-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 6px;
  border-radius: 8px;
  border: 1px solid #f3e8ff;
  margin-bottom: 6px;
  background: #faf5ff;
}

.cutting-notes-row:hover {
  border-color: #e9d5ff;
}

.cutting-notes-row-content {
  flex: 1;
  min-width: 0;
  font-size: 12px;
  line-height: 1.45;
  color: #334155;
  word-break: break-word;
}

.cutting-notes-row-content--done {
  text-decoration: line-through;
  color: #94a3b8;
}

.cutting-notes-row :deep(.el-checkbox__inner) {
  border-radius: 4px;
}

.cutting-notes-delete-btn {
  flex-shrink: 0;
  padding: 4px !important;
  color: #64748b !important;
}

.cutting-notes-delete-btn:hover {
  color: #ef4444 !important;
}

.cutting-notes-dialog-footer {
  display: flex;
  justify-content: flex-end;
}

/* 成型計画データテーブルエリア：按钮统一现代化 */
.plan-section .search-controls .date-btn,
.plan-section .search-controls .print-btn {
  border: 1px solid rgba(255, 255, 255, 0.28);
  box-shadow:
    0 6px 14px rgba(15, 23, 42, 0.16),
    inset 0 1px 0 rgba(255, 255, 255, 0.28);
  letter-spacing: 0.2px;
}

.plan-section .search-controls :deep(.el-input__wrapper),
.plan-section .search-controls :deep(.el-select__wrapper),
.plan-section .search-controls :deep(.el-date-editor.el-input__wrapper),
.plan-section .search-controls :deep(.el-date-editor .el-input__wrapper) {
  min-height: 34px;
  height: 34px;
}

.plan-section .search-controls .date-btn,
.plan-section .search-controls .print-btn {
  min-height: 34px;
}

.plan-section .search-controls .date-btn {
  border-radius: 9px;
  padding: 6px 12px;
  font-size: 11px;
  font-weight: 700;
  line-height: 1.2;
}

.plan-section .search-controls .print-btn {
  border-radius: 9px;
  font-weight: 700;
}

.plan-section .search-controls .date-btn.prev {
  background: linear-gradient(145deg, #f97373 0%, #dc2626 100%);
}

.plan-section .search-controls .date-btn.today {
  background: linear-gradient(145deg, #60a5fa 0%, #2563eb 100%);
}

.plan-section .search-controls .date-btn.next {
  background: linear-gradient(145deg, #34d399 0%, #059669 100%);
}

.plan-section .search-controls .print-btn.instruction-btn {
  background: linear-gradient(145deg, #22c55e 0%, #15803d 100%);
}

.plan-section .search-controls .print-btn[type='primary'] {
  background: linear-gradient(145deg, #6366f1 0%, #4338ca 100%);
}

.plan-section .search-controls .print-btn[type='info'] {
  background: linear-gradient(145deg, #64748b 0%, #334155 100%);
}

.plan-section .search-controls .date-btn:hover,
.plan-section .search-controls .print-btn:hover {
  transform: translateY(-2px);
  box-shadow:
    0 10px 20px rgba(15, 23, 42, 0.22),
    inset 0 1px 0 rgba(255, 255, 255, 0.32);
}

.plan-section .search-controls .date-btn:active,
.plan-section .search-controls .print-btn:active {
  transform: translateY(0) scale(0.98);
  box-shadow:
    0 3px 8px rgba(15, 23, 42, 0.16),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.date-control {
  display: flex;
  align-items: center;
  gap: 6px;
}

.filter-label {
  display: inline-flex;
  align-items: center;
  height: 34px;
  padding: 0 2px;
  font-size: 12px;
  font-weight: 700;
  color: #334155;
  line-height: 34px;
  white-space: nowrap;
}

.plan-section .date-control :deep(.el-date-editor.el-input),
.plan-section .date-control :deep(.el-date-editor.el-input__wrapper) {
  height: 34px;
}

.compact-date-picker {
  width: 120px;
  border-radius: 10px;
  transition: all 0.3s ease;
}

.plan-section .date-control .compact-date-picker {
  width: 72px;
}

.plan-section .date-control :deep(.compact-date-picker.el-date-editor.el-input) {
  width: 90px !important;
  min-width: 90px !important;
  flex: none !important;
}

.compact-date-picker:focus-within {
  transform: scale(1.02);
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.15);
}

.date-buttons {
  display: flex;
  gap: 2px;
}

.date-btn {
  padding: 4px 10px;
  font-size: 10px;
  border-radius: 8px;
  border: none;
  font-weight: 600;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  position: relative;
  overflow: hidden;
}

.date-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.5s ease;
}

.date-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.date-btn:hover::before {
  left: 100%;
}

.date-btn:active {
  transform: translateY(0) scale(0.95);
  transition: all 0.1s ease;
}

.date-btn.prev {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
}

.date-btn.today {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
}

.date-btn.next {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.machine-select {
  width: 128px;
  border-radius: 10px;
  transition: all 0.3s ease;
}

.machine-select:focus-within {
  transform: scale(1.02);
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.15);
}

.keyword-input {
  width: 168px;
  border-radius: 10px;
  transition: all 0.3s ease;
}

.keyword-input:focus-within {
  transform: scale(1.02);
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.15);
}

/* 按钮颜色区分 */
.print-btn {
  border: none;
  border-radius: 8px;
  padding: 6px 12px;
  font-weight: 600;
  font-size: 11px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: relative;
  overflow: hidden;
}

.print-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.5s ease;
}

.print-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.print-btn:hover::before {
  left: 100%;
}

.print-btn:active {
  transform: translateY(0) scale(0.98);
  transition: all 0.1s ease;
}

/* 段取予定プレビュー（編集可）ダイアログ - 紧凑现代UI */
.setup-schedule-preview-dialog.el-dialog {
  --setup-preview-radius: 8px;
  --setup-preview-gap: 6px;
}
.setup-schedule-preview-dialog .el-dialog__header {
  padding: 10px 14px 8px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  margin-right: 0;
}
.setup-schedule-preview-dialog .el-dialog__body {
  padding: 10px 14px 12px;
  max-height: calc(90vh - 100px);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.setup-schedule-preview-dialog .el-dialog__footer {
  padding: 8px 14px 10px;
  border-top: 1px solid var(--el-border-color-lighter);
}
.setup-preview-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 0;
  flex: 1;
}
.setup-schedule-preview-dialog .setup-preview-header {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 16px;
  margin-bottom: 0;
  padding: 6px 10px;
  font-size: 12px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: var(--setup-preview-radius);
  flex-shrink: 0;
}
.setup-schedule-preview-dialog .setup-preview-meta {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.setup-schedule-preview-dialog .setup-preview-meta-label {
  color: var(--el-text-color-secondary);
  font-weight: 500;
}
.setup-schedule-preview-dialog .setup-preview-meta-value {
  color: var(--el-text-color-primary);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.setup-schedule-preview-dialog .setup-preview-table {
  font-size: 12px;
  color: #000;
  flex: 1;
  min-height: 0;
  border-radius: var(--setup-preview-radius);
  overflow: hidden;
  border: 1px solid var(--el-border-color-lighter);
}
.setup-schedule-preview-dialog .setup-preview-table .el-table__inner-wrapper::before {
  display: none;
}
.setup-schedule-preview-dialog .setup-preview-table .el-table th.el-table__cell {
  padding: 5px 6px;
  font-size: 11px;
  font-weight: 400;
  background: var(--el-fill-color-light);
  color: #000;
}
.setup-schedule-preview-dialog .setup-preview-table .el-table td.el-table__cell {
  padding: 2px 6px;
  color: #000;
}
.setup-schedule-preview-dialog .setup-preview-table .el-table .el-input__wrapper {
  padding: 0 6px;
  min-height: 24px;
  box-shadow: 0 0 0 1px var(--el-border-color) inset;
  border-radius: 4px;
}
.setup-schedule-preview-dialog .setup-preview-table .el-table .el-input__inner {
  height: 22px;
  font-size: 12px;
  color: #000;
}
.setup-schedule-preview-dialog .setup-preview-table .el-table .setup-preview-plan-quantity :deep(.el-input__inner) {
  font-weight: 700 !important;
  text-align: center;
  height: 24px;
  line-height: 24px;
}

/* 兜底：确保 scoped 下也能命中 el-input 内部 input */
.setup-schedule-preview-dialog :deep(.setup-preview-plan-quantity .el-input__inner) {
  font-weight: 700 !important;
  text-align: center;
  height: 24px;
  line-height: 24px;
}

.setup-schedule-preview-dialog .setup-preview-table .el-table th.op-progress-col,
.setup-schedule-preview-dialog .setup-preview-table .el-table td.op-progress-col {
  width: 3ch !important;
  min-width: 3ch !important;
  max-width: 3ch !important;
}
.setup-schedule-preview-dialog .setup-preview-table .el-table .el-textarea__inner {
  padding: 2px 6px;
  font-size: 12px;
  min-height: 24px;
  line-height: 1.35;
  color: #000;
}
.setup-schedule-preview-dialog .planned-hours-chip {
  height: 24px;
  line-height: 24px;
  border-radius: 4px;
  text-align: center;
  font-weight: 600;
}
.setup-schedule-preview-dialog .planned-hours-chip.planned-hours-empty {
  background: #f5f7fa;
}
.setup-schedule-preview-dialog .planned-hours-chip.planned-hours-low {
  background: #fdeaea;
}
.setup-schedule-preview-dialog .planned-hours-chip.planned-hours-mid {
  background: #fff6db;
}
.setup-schedule-preview-dialog .planned-hours-chip.planned-hours-high {
  background: #e8f7ec;
}
.setup-schedule-preview-dialog .planned-hours-chip.planned-hours-very-high {
  background: #cfeecf;
}
.setup-schedule-preview-dialog .next-arrow-indicator {
  display: inline-block;
  font-size: 14px;
  font-weight: 700;
  color: #2563eb;
}
.setup-schedule-preview-dialog .setup-preview-table .el-table th.preview-arrow-col,
.setup-schedule-preview-dialog .setup-preview-table .el-table td.preview-arrow-col {
  border-top: none !important;
  border-bottom: none !important;
}
.setup-schedule-preview-dialog .setup-preview-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

/* 指示書発行按钮 - 绿色 */
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

/* 信息操作按钮 - 灰色（設備運行時間設定） */
.print-btn[type='info'] {
  background: linear-gradient(135deg, #64748b 0%, #475569 100%);
  color: white;
}

.month-buttons {
  display: flex;
  gap: 3px;
  margin-left: 6px;
}

.month-btn {
  padding: 4px 10px;
  font-size: 11px;
  border-radius: 6px;
  border: none;
  font-weight: 500;
  transition: all 0.2s ease;
  min-width: 42px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.month-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
}

.month-btn.prev {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
}

.month-btn.current {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  font-weight: 600;
}

.month-btn.next {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

/* 日別計画・実績チャート */
.plan-qty-chart-section {
  margin-bottom: 12px;
}

.plan-qty-chart-title-row {
  flex-wrap: wrap;
  gap: 4px;
}

.plan-qty-chart-sub {
  font-size: 11px;
  font-weight: 500;
  color: #64748b;
  margin-left: 8px;
}

.plan-qty-chart-actions {
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.plan-qty-chart-body {
  min-height: 320px;
  position: relative;
}

.plan-qty-chart-empty {
  padding: 48px 16px;
}

.plan-qty-chart-canvas {
  width: 100%;
  height: 340px;
}

.plan-qty-chart-section .month-btn {
  border: 1px solid rgba(255, 255, 255, 0.28);
  box-shadow:
    0 7px 16px rgba(15, 23, 42, 0.16),
    inset 0 1px 0 rgba(255, 255, 255, 0.32);
  letter-spacing: 0.2px;
  border-radius: 9px;
  font-weight: 600;
}

.plan-qty-chart-section .month-btn.prev {
  background: linear-gradient(145deg, #fb7185 0%, #dc2626 100%);
}

.plan-qty-chart-section .month-btn.current {
  background: linear-gradient(145deg, #60a5fa 0%, #2563eb 100%);
}

.plan-qty-chart-section .month-btn.next {
  background: linear-gradient(145deg, #34d399 0%, #059669 100%);
}

.plan-qty-chart-section .month-btn:hover {
  transform: translateY(-2px);
  box-shadow:
    0 10px 22px rgba(15, 23, 42, 0.22),
    inset 0 1px 0 rgba(255, 255, 255, 0.34);
}

.plan-qty-chart-section .month-btn:active {
  transform: translateY(0) scale(0.98);
  box-shadow:
    0 3px 9px rgba(15, 23, 42, 0.16),
    inset 0 1px 0 rgba(255, 255, 255, 0.22);
}

/* 操作按钮通用样式 */
.action-btn {
  border: none;
  border-radius: 8px;
  padding: 6px 12px;
  font-weight: 600;
  font-size: 11px;
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
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.action-btn:hover::before {
  left: 100%;
}

.action-btn:active {
  transform: translateY(0) scale(0.98);
  transition: all 0.1s ease;
}

/* 更新按钮 - 橙色（能率・段取時間更新） */
.action-btn.update-btn {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
}

/* 刷新按钮 - 灰色（データ更新） */
.action-btn.refresh-btn {
  background: linear-gradient(135deg, #64748b 0%, #475569 100%);
  color: white;
}

.export-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border: none;
  border-radius: 7px;
  padding: 6px 14px;
  font-weight: 500;
  font-size: 12px;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
}

.export-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}

.print-btn {
  border: none;
  border-radius: 7px;
  padding: 6px 14px;
  font-weight: 500;
  font-size: 12px;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
}

.print-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}

/* 成功操作按钮 - 绿色（Excel出力） */
.export-btn[type='success'] {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
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
  font-size: 20px;
  font-weight: 600;
  color: #1e293b;
  letter-spacing: -0.2px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: linear-gradient(135deg, rgba(248, 250, 252, 0.95) 0%, rgba(241, 245, 249, 0.95) 100%);
  border-bottom: 1px solid rgba(226, 232, 240, 0.5);
}

.header-actions {
  display: flex;
  gap: 6px;
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
  padding: 20px;
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
  font-size: 12px;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(15, 23, 42, 0.08);
  border: 1px solid rgba(226, 232, 240, 0.3);
  transition: all 0.3s ease;
  animation: tableSlideIn 0.8s ease-out;
}

.compact-table:hover {
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.12);
}

@keyframes tableSlideIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.compact-table :deep(.el-table__header) {
  font-size: 11px;
  font-weight: 600;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  color: #475569;
}

.compact-table :deep(.el-table__header th) {
  padding: 6px 8px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.5);
}

.compact-table :deep(.el-table__body) {
  font-size: 12px;
}

.compact-table :deep(.el-table__row) {
  height: 34px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.compact-table :deep(.el-table__row:hover) {
  background: linear-gradient(135deg, rgba(248, 250, 252, 0.95) 0%, rgba(241, 245, 249, 0.95) 100%);
  box-shadow: 0 1px 6px rgba(15, 23, 42, 0.08);
}

.compact-table :deep(.el-table td) {
  padding: 5px 8px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.3);
  font-weight: 400;
  transition: all 0.2s ease;
}

/* 指定生産品種行：浅黄色背景（画面テーブル） */
.compact-table :deep(.el-table__row.product-highlight-row td) {
  background-color: #fffde7 !important;
}

.compact-table :deep(.el-table th) {
  padding: 6px 6px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 1px solid rgba(226, 232, 240, 0.6);
  color: #475569;
  font-weight: 600;
  font-size: 11px;
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
  padding: 20px 16px;
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
  padding: 10px 14px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%);
  border-bottom: 1px solid rgba(226, 232, 240, 0.2);
  position: relative;
}

.header-actions {
  display: flex;
  gap: 6px;
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
  padding: 8px 10px;
  display: flex;
  justify-content: flex-end;
  background: rgba(248, 250, 252, 0.5);
  border-top: 1px solid rgba(226, 232, 240, 0.5);
  margin-top: 0;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 数字居中 */
.numeric-cell {
  text-align: center;
}

.main-table td.plan-quantity-cell {
  font-weight: 600 !important;
}

.plan-quantity-cell {
  font-weight: 600 !important;
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

.section-card :deep(.el-card__body) {
  padding: 8px 10px 10px;
}

.section-card :deep(.el-card__header) {
  padding: 0;
  border-bottom: none;
}

.search-controls :deep(.el-input__wrapper),
.search-controls :deep(.el-select__wrapper),
.search-controls :deep(.el-date-editor.el-input__wrapper),
.search-controls :deep(.el-date-editor .el-input__wrapper) {
  min-height: 30px;
  border-radius: 8px;
}

.search-controls :deep(.el-input__inner),
.search-controls :deep(.el-select__selected-item),
.search-controls :deep(.el-range-input) {
  font-size: 12px;
}

.compact-table :deep(.el-input__wrapper) {
  min-height: 28px;
  padding: 0 8px;
}

.compact-table :deep(.el-input__inner) {
  font-size: 12px;
}

/* レスポンシブデザイン */
@media (max-width: 1200px) {
  .molding-instruction-container {
    padding: 6px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
    gap: 8px;
  }

  .search-controls {
    flex-direction: row;
    align-items: center;
    gap: 8px;
  }

  .date-control {
    justify-content: space-between;
  }

  .compact-date-picker {
    width: auto;
    flex: 1;
  }

  .plan-section .date-control :deep(.compact-date-picker.el-date-editor.el-input) {
    width: 72px !important;
    min-width: 72px !important;
    flex: none !important;
  }
}

@media (max-width: 768px) {
  .molding-instruction-container {
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

  .page-header-actions {
    gap: 5px;
    flex-wrap: wrap;
    justify-content: flex-end;
  }

  .header-stats {
    width: 100%;
    justify-content: flex-end;
  }

  .header-stat-item {
    min-width: 112px;
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
    gap: 5px;
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
    height: 30px;
  }

  .compact-table :deep(.el-table td) {
    padding: 3px 5px;
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
  .molding-instruction-container {
    padding: 2px;
  }

  .page-header {
    padding: 6px 8px;
  }

  .header-content {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .page-header-actions {
    justify-content: flex-end;
    flex-wrap: wrap;
  }

  .header-stats {
    width: 100%;
    justify-content: space-between;
  }

  .header-stat-item {
    flex: 1;
    min-width: 0;
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
  padding: 20px;
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

.print-preview-body :deep(.shift-table .shift-time) {
  width: 12%;
}

.print-preview-body :deep(.shift-table .product-name) {
  width: 15%;
}

.print-preview-body :deep(.shift-table .production-qty) {
  width: 8%;
}

.print-preview-body :deep(.shift-table .recorder) {
  width: 8%;
}

.print-preview-body :deep(.shift-table .remarks) {
  width: 12%;
}

.print-preview-body :deep(.shift-table .notch) {
  width: 8%;
}

.print-preview-body :deep(.shift-table .bending) {
  width: 8%;
}

.print-preview-body :deep(.shift-table .chamfering) {
  width: 8%;
}

.print-preview-body :deep(.shift-table .setup) {
  width: 10%;
}

.print-preview-body :deep(.shift-table .yellow-box) {
  width: 11%;
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

.print-preview-body :deep(.product-highlight-row td) {
  background-color: #fffde7 !important;
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
  padding: 20px;
  font-family:
    -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
}

.dialog-footer {
  text-align: right;
}

.work-time-dialog :deep(.el-dialog__body) {
  padding: 12px 16px;
}

.work-time-dialog__body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.work-time-dialog__toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-radius: 10px;
  background: linear-gradient(145deg, #eef3ff, #f8fbff);
  border: 1px solid #e0e7ff;
  box-shadow: 0 1px 6px rgba(64, 158, 255, 0.12);
}

.work-time-dialog__subtitle {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.work-time-dialog__hint {
  margin: 4px 0 0;
  font-size: 12px;
  color: #6b7280;
}

.work-time-table :deep(.el-checkbox) {
  --el-checkbox-font-size: 13px;
}

.work-time-table :deep(.el-table__cell) {
  padding: 4px 6px;
}

.work-time-dialog__footer {
  padding: 10px 0;
}

.work-time-form-dialog :deep(.el-dialog__body) {
  padding: 12px 16px 6px;
}

.work-time-form :deep(.el-form-item) {
  margin-bottom: 12px;
}

.work-time-form__select {
  width: 100%;
}

.work-time-form-dialog__footer {
  padding: 6px 0 2px;
}
</style>
