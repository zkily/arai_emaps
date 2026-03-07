<template>
  <div class="plan-baseline-root">
  <div class="plan-baseline-page">
    <!-- 紧凑型页面头部 -->
    <div class="page-header">
      <div class="title-wrapper">
        <div class="title-icon-wrapper">
          <el-icon class="title-icon"><TrendCharts /></el-icon>
        </div>
        <div class="title-content">
          <h2>生産計画ベースライン管理</h2>
          <p>月次計画を固定化し、現行計画・実績と比較して推移を把握します</p>
        </div>
      </div>
      <el-button
        type="primary"
        :icon="Refresh"
        @click="loadComparison"
        :loading="tableLoading"
        size="default"
      >
        再取得
      </el-button>
    </div>

    <!-- 合并的操作区域 -->
    <el-card class="action-card" shadow="hover">
      <div class="action-content">
        <div class="action-section generate-section">
          <div class="section-header">
            <div class="section-icon generate-icon-bg">
              <el-icon><DocumentAdd /></el-icon>
            </div>
            <div class="section-title">
              <h3>ベースライン生成</h3>
              <span class="section-desc">計画を固定化して比較基準を作成</span>
            </div>
          </div>
          <div class="section-controls">
            <el-date-picker
              v-model="queryForm.baselineMonth"
              type="month"
              value-format="YYYY-MM-DD"
              placeholder="基準月"
              size="default"
              style="width: 140px"
            />
            <el-select
              v-model="queryForm.processName"
              clearable
              placeholder="全工程"
              size="default"
              style="width: 130px"
            >
              <el-option
                v-for="item in processOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
            <el-button
              type="success"
              :icon="DocumentAdd"
              @click="handleGenerate"
              :loading="generating"
              size="default"
            >
              生成
            </el-button>
            <el-button
              type="danger"
              plain
              :icon="Delete"
              @click="handleDeleteBaseline"
              :loading="deleting"
              size="default"
            >
              削除
            </el-button>
            <el-button
              type="warning"
              plain
              :icon="EditPen"
              @click="openAdjustmentDialog"
              size="default"
            >
              計画を修正
            </el-button>
          </div>
        </div>
        <div class="action-divider"></div>
        <div class="action-section filter-section">
          <div class="section-header">
            <div class="section-icon filter-icon-bg">
              <el-icon><Search /></el-icon>
            </div>
            <div class="section-title">
              <h3>比較条件</h3>
              <span class="section-desc">対象月と工程を指定して比較</span>
            </div>
          </div>
          <div class="section-controls">
            <el-date-picker
              v-model="queryForm.baselineMonth"
              type="month"
              value-format="YYYY-MM-DD"
              placeholder="対象月"
              size="default"
              style="width: 140px"
            />
            <el-select
              v-model="queryForm.processName"
              clearable
              placeholder="工程"
              size="default"
              style="width: 130px"
            >
              <el-option
                v-for="item in processOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
            <el-button
              type="primary"
              :icon="Search"
              @click="loadComparison"
              :loading="tableLoading"
              size="default"
            >
              検索
            </el-button>
            <el-button :icon="Refresh" @click="resetForm" size="default">クリア</el-button>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 紧凑型摘要卡片 -->
    <div class="summary-row">
      <div
        class="summary-card"
        v-for="(card, index) in summaryCards"
        :key="card.label"
        :style="{ animationDelay: `${index * 0.05}s` }"
      >
        <div class="summary-card-inner">
          <div class="summary-label">{{ card.label }}</div>
          <div
            class="summary-value"
            :class="{ negative: card.isNegative, positive: !card.isNegative && card.value !== '-' }"
          >
            {{ card.value }}
          </div>
          <div v-if="card.description" class="summary-desc">{{ card.description }}</div>
        </div>
      </div>
    </div>

    <!-- 紧凑型表格卡片 -->
    <el-card shadow="hover" class="table-card">
      <template #header>
        <div class="card-header">
          <div class="card-header-left">
            <el-icon class="card-header-icon"><Setting /></el-icon>
            <span class="card-title">ベースライン比較一覧</span>
            <el-tag
              v-if="comparisonResult?.baselineMonth"
              type="info"
              size="small"
              class="month-tag"
            >
              {{ dayjs(comparisonResult.baselineMonth).format('YYYY年MM月') }}
            </el-tag>
          </div>
          <div class="card-header-right">
            <el-tag v-if="totalItemsCount > 0" type="primary" size="small" class="count-tag">
              総件数: {{ totalItemsCount }}
            </el-tag>
          </div>
        </div>
      </template>
      <el-tabs v-model="activeTab" type="border-card" v-loading="tableLoading">
        <el-tab-pane
          v-for="process in processTabs"
          :key="process.name"
          :label="process.label"
          :name="process.name"
        >
          <template #label>
            <span class="tab-label">
              <el-icon class="tab-icon"><Setting /></el-icon>
              {{ process.label }}
              <el-tag size="small" type="info" class="tab-count">{{ process.count }}</el-tag>
            </span>
          </template>
          <el-table
            :data="process.items"
            border
            stripe
            height="450"
            style="width: 100%"
            empty-text="データがありません"
            class="comparison-table"
          >
            <el-table-column prop="plan_date" label="日付" width="135" fixed="left">
              <template #default="{ row }">
                <div class="date-cell-wrapper">
                  <el-icon class="date-icon"><Calendar /></el-icon>
                  <span class="date-cell">{{ formatDate(row.plan_date) }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="基準計画" width="120" align="right">
              <template #header>
                <div class="column-header">
                  <span>基準計画</span>
                  <el-tooltip
                    content="ベースライン生成時に固定化された計画値"
                    placement="top"
                    effect="dark"
                  >
                    <el-icon class="help-icon"><QuestionFilled /></el-icon>
                  </el-tooltip>
                </div>
              </template>
              <template #default="{ row }">
                <div class="number-cell baseline-plan">
                  <span class="number-value">{{ formatNumber(row.baseline_plan) }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="現行計画" width="120" align="right">
              <template #header>
                <div class="column-header">
                  <span>現行計画</span>
                  <el-tooltip
                    content="production_plan_updates から当月の日次 quantity を再集計"
                    placement="top"
                    effect="dark"
                  >
                    <el-icon class="help-icon"><QuestionFilled /></el-icon>
                  </el-tooltip>
                </div>
              </template>
              <template #default="{ row }">
                <div class="number-cell current-plan">
                  <span class="number-value">{{ formatNumber(row.current_plan) }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="計画差異" width="120" align="right">
              <template #header>
                <div class="column-header">
                  <span>計画差異</span>
                  <el-tooltip content="現行計画 - 基準計画" placement="top" effect="dark">
                    <el-icon class="help-icon"><QuestionFilled /></el-icon>
                  </el-tooltip>
                </div>
              </template>
              <template #default="{ row }">
                <div class="number-cell diff-cell" :class="getDiffClass(row.plan_diff)">
                  <el-icon v-if="row.plan_diff > 0" class="trend-icon trend-up"
                    ><ArrowUp
                  /></el-icon>
                  <el-icon v-else-if="row.plan_diff < 0" class="trend-icon trend-down"
                    ><ArrowDown
                  /></el-icon>
                  <span class="number-value">{{ formatNumber(row.plan_diff) }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="現行実績合計" width="140" align="right">
              <template #header>
                <div class="column-header">
                  <span>現行実績合計</span>
                  <el-tooltip
                    content="stock_transaction_logs から当月の日次実績を再集計"
                    placement="top"
                    effect="dark"
                  >
                    <el-icon class="help-icon"><QuestionFilled /></el-icon>
                  </el-tooltip>
                </div>
              </template>
              <template #default="{ row }">
                <div
                  class="number-cell actual-cell"
                  v-if="row.current_actual !== null && row.current_actual !== undefined"
                >
                  <span class="number-value">{{ formatNumber(row.current_actual) }}</span>
                </div>
                <div class="number-cell" v-else>
                  <span class="number-value" style="color: #94a3b8">-</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="計画対実績差" width="140" align="right">
              <template #header>
                <div class="column-header">
                  <span>計画対実績差</span>
                  <el-tooltip content="ベースライン計画 - 現行実績" placement="top" effect="dark">
                    <el-icon class="help-icon"><QuestionFilled /></el-icon>
                  </el-tooltip>
                </div>
              </template>
              <template #default="{ row }">
                <div
                  class="number-cell diff-cell"
                  :class="getDiffClass(row.actual_diff)"
                  v-if="row.actual_diff !== null && row.actual_diff !== undefined"
                >
                  <el-icon v-if="row.actual_diff > 0" class="trend-icon trend-up"
                    ><ArrowUp
                  /></el-icon>
                  <el-icon v-else-if="row.actual_diff < 0" class="trend-icon trend-down"
                    ><ArrowDown
                  /></el-icon>
                  <span class="number-value">{{ formatNumber(row.actual_diff) }}</span>
                </div>
                <div class="number-cell" v-else>
                  <span class="number-value" style="color: #94a3b8">-</span>
                </div>
              </template>
            </el-table-column>
          </el-table>
          <div class="tab-total-wrapper" v-if="processTotals.get(process.name)">
            <div class="tab-total-header">
              <el-icon class="total-icon"><DataAnalysis /></el-icon>
              <span class="tab-total-label">合計</span>
            </div>
            <div class="tab-total-grid">
              <div class="total-item current-plan-item">
                <div class="total-item-header">
                  <el-icon class="total-item-icon"><Document /></el-icon>
                  <span class="total-item-label">現行計画</span>
                </div>
                <div class="total-item-value">
                  {{ formatNumber(processTotals.get(process.name)?.currentPlan) }}
                </div>
              </div>
              <div
                class="total-item plan-diff-item"
                :class="getDiffClass(processTotals.get(process.name)?.planDiff)"
              >
                <div class="total-item-header">
                  <el-icon class="total-item-icon"><TrendCharts /></el-icon>
                  <span class="total-item-label">計画差異</span>
                </div>
                <div class="total-item-value">
                  <el-icon
                    v-if="(processTotals.get(process.name)?.planDiff || 0) > 0"
                    class="total-trend-icon trend-up"
                    ><ArrowUp
                  /></el-icon>
                  <el-icon
                    v-else-if="(processTotals.get(process.name)?.planDiff || 0) < 0"
                    class="total-trend-icon trend-down"
                    ><ArrowDown
                  /></el-icon>
                  {{ formatNumber(processTotals.get(process.name)?.planDiff) }}
                </div>
              </div>
              <div class="total-item actual-item">
                <div class="total-item-header">
                  <el-icon class="total-item-icon"><CircleCheck /></el-icon>
                  <span class="total-item-label">現行実績</span>
                </div>
                <div class="total-item-value">
                  {{ formatNumber(processTotals.get(process.name)?.currentActual) }}
                </div>
              </div>
              <div
                class="total-item actual-diff-item"
                :class="getDiffClass(processTotals.get(process.name)?.actualDiff)"
              >
                <div class="total-item-header">
                  <el-icon class="total-item-icon"><DataLine /></el-icon>
                  <span class="total-item-label">計画対実績差</span>
                </div>
                <div class="total-item-value">
                  <el-icon
                    v-if="(processTotals.get(process.name)?.actualDiff || 0) > 0"
                    class="total-trend-icon trend-up"
                    ><ArrowUp
                  /></el-icon>
                  <el-icon
                    v-else-if="(processTotals.get(process.name)?.actualDiff || 0) < 0"
                    class="total-trend-icon trend-down"
                    ><ArrowDown
                  /></el-icon>
                  {{ formatNumber(processTotals.get(process.name)?.actualDiff) }}
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>
        <el-tab-pane v-if="processTabs.length === 0" label="データなし" name="empty">
          <el-empty description="データがありません" />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>

  <el-dialog
    v-model="adjustmentDialogVisible"
    class="baseline-adjust-dialog"
    destroy-on-close
    align-center
  >
    <template #header>
      <div class="adjustment-header">
        <div>
          <div class="adjustment-title">ベースライン計画修正</div>
          <p class="adjustment-desc">
            基準月の計画値をまとめて再調整。工程で絞り込んで素早く保存できます。
          </p>
        </div>
        <el-tag v-if="adjustmentForm.baselineMonth" size="large" effect="plain">
          {{ dayjs(adjustmentForm.baselineMonth).format('YYYY年MM月') }}
        </el-tag>
      </div>
    </template>

    <div class="adjustment-toolbar">
      <div class="toolbar-left">
        <el-date-picker
          v-model="adjustmentForm.baselineMonth"
          type="month"
          value-format="YYYY-MM-DD"
          placeholder="基準月"
          class="toolbar-month"
        />
        <el-select
          v-model="adjustmentForm.processName"
          clearable
          placeholder="全工程"
          class="toolbar-process"
        >
          <el-option
            v-for="item in processOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
      </div>
      <div class="toolbar-right">
        <el-button type="primary" :icon="Search" @click="loadAdjustmentRecords">
          データ取得
        </el-button>
        <el-button :icon="Refresh" @click="resetAdjustmentForm">リセット</el-button>
      </div>
    </div>

    <el-table
      v-loading="adjustmentLoading"
      :data="adjustmentItems"
      class="adjustment-table"
      height="480"
      size="small"
      border
      empty-text="該当するデータがありません"
    >
      <el-table-column prop="plan_date" label="日付" width="120" align="center">
        <template #default="{ row }">
          <div class="adjustment-date">{{ formatDate(row.plan_date) }}</div>
        </template>
      </el-table-column>
      <el-table-column prop="process_name" label="工程" width="140">
        <template #default="{ row }">
          <el-tag size="small" type="info" effect="plain">
            {{ row.process_name || '未指定' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="基準計画" min-width="260">
        <template #default="{ row, $index }">
          <div class="plan-editor">
            <div class="plan-editor-current">
              現在値 <strong>{{ formatNumber(row.plan_quantity) }}</strong>
            </div>
            <el-input-number
              v-model="row.tempPlanQuantity"
              :min="0"
              :max="100000000"
              :step="1"
              :controls="false"
              size="small"
              class="plan-input"
              :ref="(el) => setPlanInputRef(el, $index)"
              @keydown="handlePlanInputKeydown($event, $index)"
            />
          </div>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="140" fixed="right" align="center">
        <template #default="{ row }">
          <el-button
            type="primary"
            plain
            size="small"
            :loading="row.saving"
            @click="handleUpdatePlanQuantity(row)"
          >
            保存
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <template #footer>
      <div class="adjustment-footer">
        <el-button type="primary" :icon="DocumentAdd" @click="handleBatchSave">
          変更を一括保存
        </el-button>
        <el-button @click="adjustmentDialogVisible = false">閉じる</el-button>
      </div>
    </template>
  </el-dialog>
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: 'ProductionPlanBaselineManagement' })
import { reactive, ref, computed, onMounted, watch, nextTick } from 'vue'
import dayjs from 'dayjs'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  TrendCharts,
  Refresh,
  Search,
  DocumentAdd,
  Setting,
  Delete,
  QuestionFilled,
  Calendar,
  ArrowUp,
  ArrowDown,
  DataAnalysis,
  Document,
  CircleCheck,
  DataLine,
  EditPen,
} from '@element-plus/icons-vue'
import {
  generatePlanBaseline,
  fetchPlanBaselineComparison,
  deletePlanBaseline,
  fetchPlanBaselineRecords,
  updatePlanBaselinePlanQuantity,
  type PlanBaselineComparisonItem,
  type PlanBaselineComparisonResult,
  type PlanBaselineRecord,
} from '@/api/planBaseline'

const today = dayjs().startOf('month').format('YYYY-MM-DD')

const queryForm = reactive({
  baselineMonth: today,
  processName: '',
})

interface PlanBaselineAdjustmentItem extends PlanBaselineRecord {
  tempPlanQuantity: number
  saving?: boolean
}

const processOptions = [
  { label: '全工程', value: '' },
  { label: '切断', value: '切断' },
  { label: '面取', value: '面取' },
  { label: '成型', value: '成型' },
  { label: 'メッキ', value: 'メッキ' },
  { label: '外注メッキ', value: '外注メッキ' },
  { label: '溶接', value: '溶接' },
  { label: '外注溶接', value: '外注溶接' },
  { label: '検査', value: '検査' },
]

const generating = ref(false)
const deleting = ref(false)
const tableLoading = ref(false)
const comparisonResult = ref<PlanBaselineComparisonResult | null>(null)
const comparisonItems = ref<PlanBaselineComparisonItem[]>([])
const activeTab = ref('all')

const adjustmentDialogVisible = ref(false)
const adjustmentLoading = ref(false)
const adjustmentItems = ref<PlanBaselineAdjustmentItem[]>([])
const planInputRefs = ref<(HTMLInputElement | null)[]>([])
const adjustmentForm = reactive({
  baselineMonth: queryForm.baselineMonth,
  processName: '',
})

// 工程別にデータをグループ化
const processTabs = computed(() => {
  if (comparisonItems.value.length === 0) {
    return []
  }

  // 工程名でグループ化
  const processMap = new Map<string, PlanBaselineComparisonItem[]>()

  comparisonItems.value.forEach((item) => {
    const processName = item.process_name || '未指定'
    if (!processMap.has(processName)) {
      processMap.set(processName, [])
    }
    processMap.get(processName)!.push(item)
  })

  // 各工程のデータを日付順にソート
  const tabs = Array.from(processMap.entries()).map(([processName, items]) => {
    const sortedItems = [...items].sort(
      (a, b) => dayjs(a.plan_date).valueOf() - dayjs(b.plan_date).valueOf(),
    )
    return {
      name: processName,
      label: processName,
      count: sortedItems.length,
      items: sortedItems,
    }
  })

  // 工程名でソート
  tabs.sort((a, b) => a.label.localeCompare(b.label, 'ja'))

  return tabs
})

// データが更新されたら最初のタブをアクティブに
const updateActiveTab = () => {
  if (processTabs.value.length > 0) {
    const currentTabExists = processTabs.value.find((t) => t.name === activeTab.value)
    if (!currentTabExists) {
      activeTab.value = processTabs.value[0].name
    }
  }
}

const totalItemsCount = computed(() => {
  return comparisonItems.value.length
})

const processTotals = computed(() => {
  const totals = new Map<
    string,
    {
      currentPlan: number
      planDiff: number
      currentActual: number
      actualDiff: number
    }
  >()
  type TabTotals = { currentPlan: number; planDiff: number; currentActual: number; actualDiff: number }
  const initial: TabTotals = { currentPlan: 0, planDiff: 0, currentActual: 0, actualDiff: 0 }
  processTabs.value.forEach((tab) => {
    const aggregate = tab.items.reduce<TabTotals>(
      (acc, item) => {
        acc.currentPlan += Number(item.current_plan ?? 0)
        acc.planDiff += Number(item.plan_diff ?? 0)
        if (item.current_actual != null) acc.currentActual += Number(item.current_actual)
        if (item.actual_diff != null) acc.actualDiff += Number(item.actual_diff)
        return acc
      },
      { ...initial },
    )
    totals.set(tab.name, aggregate)
  })
  return totals
})

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return dayjs(dateStr).format('YYYY-MM-DD')
}

const summaryCards = computed(() => {
  const summary = comparisonResult.value?.summary

  if (!summary) {
    return [
      { label: '基準計画合計', value: '-', isNegative: false, description: 'ベースライン計画合計' },
      { label: '現行計画合計', value: '-', isNegative: false, description: '最新計画合計' },
      {
        label: '計画差異',
        value: '-',
        isNegative: false,
        description: '現行計画 - ベースライン計画',
      },
      {
        label: '現行実績合計',
        value: '-',
        isNegative: false,
        description: '最新実績合計',
      },
      {
        label: '計画対実績差',
        value: '-',
        isNegative: false,
        description: 'ベースライン計画 - 現行実績',
      },
      {
        label: '計画達成率',
        value: '-',
        isNegative: false,
        description: '現行実績 ÷ 現行計画',
      },
      {
        label: '達成率差異',
        value: '-',
        isNegative: false,
        description: '計画対実績差 ÷ 基準計画合計',
      },
    ]
  }

  const currentPlanTotal = summary.currentPlanTotal ?? 0
  const currentActualTotal = summary.currentActualTotal ?? 0
  const baselinePlanTotal = summary.baselinePlanTotal ?? 0
  const planDifference = summary.planDifference ?? 0
  const actualDifference = summary.actualDifference ?? 0

  const planAchievement =
    currentPlanTotal === 0 ? null : (currentActualTotal / currentPlanTotal) * 100

  const achievementDifference =
    baselinePlanTotal === 0 ? null : (actualDifference / baselinePlanTotal) * 100

  return [
    {
      label: '基準計画合計',
      value: formatNumber(summary.baselinePlanTotal),
      isNegative: baselinePlanTotal < 0,
      description: 'ベースライン計画合計',
    },
    {
      label: '現行計画合計',
      value: formatNumber(summary.currentPlanTotal),
      isNegative: currentPlanTotal < 0,
      description: '最新計画合計',
    },
    {
      label: '計画差異',
      value: formatNumber(summary.planDifference),
      isNegative: planDifference < 0,
      description: '現行計画 - ベースライン計画',
    },
    {
      label: '現行実績合計',
      value: summary.currentActualTotal === null ? '-' : formatNumber(summary.currentActualTotal),
      isNegative: false,
      description: '最新実績合計',
    },
    {
      label: '計画対実績差',
      value: summary.actualDifference == null ? '-' : formatNumber(summary.actualDifference),
      isNegative: actualDifference !== 0 && actualDifference < 0,
      description: 'ベースライン計画 - 現行実績',
    },
    {
      label: '計画達成率',
      value: planAchievement === null ? '-' : `${planAchievement.toFixed(1)}%`,
      isNegative: planAchievement !== null && planAchievement < 100,
      description: '現行実績 ÷ 現行計画',
    },
    {
      label: '達成率差異',
      value: achievementDifference === null ? '-' : `${achievementDifference.toFixed(2)}%`,
      isNegative: achievementDifference !== null && achievementDifference < 0,
      description: '計画対実績差 ÷ 基準計画合計',
    },
  ]
})

const formatNumber = (value: number | string | null | undefined) => {
  if (value === null || value === undefined || value === '') return '-'
  const num = Number(value)
  if (Number.isNaN(num)) return String(value)
  return num.toLocaleString('ja-JP')
}

const openAdjustmentDialog = () => {
  adjustmentForm.baselineMonth = queryForm.baselineMonth
  adjustmentForm.processName = queryForm.processName || ''
  adjustmentItems.value = []
  planInputRefs.value = []
  adjustmentDialogVisible.value = true
  nextTick(() => {
    loadAdjustmentRecords()
  })
}

const resetAdjustmentForm = () => {
  adjustmentForm.baselineMonth = queryForm.baselineMonth
  adjustmentForm.processName = ''
  adjustmentItems.value = []
  planInputRefs.value = []
}

const loadAdjustmentRecords = async () => {
  if (!adjustmentForm.baselineMonth) {
    ElMessage.warning('基準月を選択してください')
    return
  }
  adjustmentLoading.value = true
  try {
    const records = await fetchPlanBaselineRecords({
      baselineMonth: adjustmentForm.baselineMonth,
      processName: adjustmentForm.processName || undefined,
    })
    adjustmentItems.value = records.map((record) => ({
      ...record,
      plan_date: record.plan_date ? dayjs(record.plan_date).format('YYYY-MM-DD') : record.plan_date,
      process_name: record.process_name || '',
      tempPlanQuantity: Number(record.plan_quantity ?? 0),
      saving: false,
    }))
    if (records.length === 0) {
      ElMessage.info('該当データがありません')
    }
    planInputRefs.value = []
  } catch (error: any) {
    ElMessage.error(error?.message || 'ベースラインデータの取得に失敗しました')
  } finally {
    adjustmentLoading.value = false
  }
}

const handleUpdatePlanQuantity = async (row: PlanBaselineAdjustmentItem) => {
  const planQuantity = Number(row.tempPlanQuantity)
  if (Number.isNaN(planQuantity)) {
    ElMessage.warning('数値を入力してください')
    return
  }
  if (!adjustmentForm.baselineMonth) {
    ElMessage.warning('基準月を選択してください')
    return
  }
  row.saving = true
  try {
    await updatePlanBaselinePlanQuantity({
      baselineMonth: adjustmentForm.baselineMonth,
      planDate: row.plan_date,
      processName: row.process_name || undefined,
      planQuantity,
    })
    row.plan_quantity = planQuantity
    ElMessage.success('修正しました')
  } catch (error: any) {
    ElMessage.error(error?.message || '修正に失敗しました')
  } finally {
    row.saving = false
  }
}

const handleBatchSave = async () => {
  if (adjustmentItems.value.length === 0) {
    ElMessage.warning('修正対象のデータがありません')
    return
  }

  const modifiedRows = adjustmentItems.value.filter(
    (item) => Number(item.tempPlanQuantity) !== Number(item.plan_quantity),
  )

  if (modifiedRows.length === 0) {
    ElMessage.info('変更された項目がありません')
    return
  }

  if (!adjustmentForm.baselineMonth) {
    ElMessage.warning('基準月を選択してください')
    return
  }

  try {
    for (const row of modifiedRows) {
      await handleUpdatePlanQuantity(row)
    }
    ElMessage.success('一括で保存しました')
  } catch (error) {
    // handleUpdatePlanQuantity 内でメッセージ済み
  }
}

const setPlanInputRef = (el: any, index: number) => {
  if (!el) return
  nextTick(() => {
    const inputEl = el.$el?.querySelector('input')
    planInputRefs.value[index] = (inputEl as HTMLInputElement) || null
  })
}

const focusPlanInput = (index: number) => {
  if (index < 0 || index >= planInputRefs.value.length) return
  const inputEl = planInputRefs.value[index]
  if (inputEl) {
    inputEl.focus()
    if (typeof inputEl.select === 'function') {
      inputEl.select()
    }
  }
}

const handlePlanInputKeydown = (event: KeyboardEvent, index: number) => {
  const key = event.key
  let targetIndex: number | null = null
  if (key === 'ArrowDown' || key === 'Enter') {
    targetIndex = Math.min(index + 1, adjustmentItems.value.length - 1)
  } else if (key === 'ArrowUp') {
    targetIndex = Math.max(index - 1, 0)
  } else if (key === 'ArrowRight') {
    targetIndex = Math.min(index + 1, adjustmentItems.value.length - 1)
  } else if (key === 'ArrowLeft') {
    targetIndex = Math.max(index - 1, 0)
  }

  if (targetIndex !== null && targetIndex !== index) {
    event.preventDefault()
    focusPlanInput(targetIndex)
  }
}

const getDiffClass = (value: number | string | null | undefined) => {
  if (value === null || value === undefined || value === '') return ''
  const num = Number(value)
  if (Number.isNaN(num)) return ''
  if (num > 0) return 'diff-positive'
  if (num < 0) return 'diff-negative'
  return 'diff-zero'
}

const loadComparison = async () => {
  tableLoading.value = true
  try {
    const data = await fetchPlanBaselineComparison({
      baselineMonth: queryForm.baselineMonth,
      processName: queryForm.processName || undefined,
    })
    comparisonResult.value = data
    comparisonItems.value = data?.items ?? []
  } catch (error: any) {
    ElMessage.error(error?.message || '比較データの取得に失敗しました')
  } finally {
    tableLoading.value = false
  }
}

const handleGenerate = async () => {
  try {
    await ElMessageBox.confirm(
      '対象月のベースラインを再生成します。既存データは上書きされますがよろしいですか？',
      '確認',
      {
        type: 'warning',
        confirmButtonText: '生成',
        cancelButtonText: 'キャンセル',
      },
    )
  } catch {
    return
  }

  generating.value = true
  try {
    await generatePlanBaseline({
      baselineMonth: queryForm.baselineMonth,
      processName: queryForm.processName || undefined,
    })
    ElMessage.success('ベースラインを生成しました')
    await loadComparison()
  } catch (error: any) {
    ElMessage.error(error?.message || 'ベースライン生成に失敗しました')
  } finally {
    generating.value = false
  }
}

const handleDeleteBaseline = async () => {
  if (!queryForm.baselineMonth) {
    ElMessage.warning('対象月を選択してください')
    return
  }
  const confirmMessage = queryForm.processName
    ? `基準月「${dayjs(queryForm.baselineMonth).format('YYYY年MM月')}」の「${queryForm.processName}」ベースラインを削除します。よろしいですか？`
    : `基準月「${dayjs(queryForm.baselineMonth).format('YYYY年MM月')}」の全工程ベースラインを削除します。よろしいですか？`
  try {
    await ElMessageBox.confirm(confirmMessage, '確認', {
      type: 'warning',
      confirmButtonText: '削除',
      cancelButtonText: 'キャンセル',
    })
  } catch {
    return
  }

  deleting.value = true
  try {
    await deletePlanBaseline({
      baselineMonth: queryForm.baselineMonth,
      processName: queryForm.processName || undefined,
    })
    ElMessage.success('ベースラインを削除しました')
    await loadComparison()
  } catch (error: any) {
    ElMessage.error(error?.message || 'ベースライン削除に失敗しました')
  } finally {
    deleting.value = false
  }
}

const resetForm = () => {
  queryForm.baselineMonth = today
  queryForm.processName = ''
  loadComparison()
}

// タブが更新されたらアクティブタブを調整
watch(
  processTabs,
  () => {
    updateActiveTab()
  },
  { immediate: true },
)

onMounted(() => {
  loadComparison()
})
</script>

<style scoped>
/* 页面基础样式 */
.plan-baseline-root {
  display: block;
  width: 100%;
}

.plan-baseline-page {
  padding: 10px;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  min-height: 100vh;
}

/* 紧凑型页面头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border-radius: 8px;
  color: white;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.2);
  animation: slideDown 0.4s ease-out;
}

.title-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon-wrapper {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  backdrop-filter: blur(10px);
}

.title-icon {
  font-size: 24px;
  color: white;
}

.title-content h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: white;
  line-height: 1.2;
}

.title-content p {
  margin: 2px 0 0;
  color: rgba(255, 255, 255, 0.85);
  font-size: 12px;
  line-height: 1.3;
}

/* 合并的操作卡片 */
.action-card {
  margin-bottom: 12px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  background: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  animation: fadeInUp 0.5s ease-out;
  transition: box-shadow 0.3s ease;
}

.action-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.action-content {
  display: flex;
  gap: 16px;
  padding: 4px;
  align-items: flex-start;
}

.action-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.action-divider {
  width: 1px;
  background: linear-gradient(180deg, transparent, #e2e8f0, transparent);
  margin: 0 4px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 4px;
}

.section-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  font-size: 16px;
  color: white;
  flex-shrink: 0;
}

.generate-icon-bg {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.filter-icon-bg {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
}

.section-title h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.2;
}

.section-desc {
  display: block;
  font-size: 11px;
  color: #64748b;
  margin-top: 2px;
}

.section-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

/* 紧凑型摘要卡片 */
.summary-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}

.summary-card {
  background: white;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  animation: fadeInScale 0.5s ease-out backwards;
  position: relative;
}

.summary-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.3s ease;
}

.summary-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15);
  border-color: #c7d2fe;
}

.summary-card:hover::before {
  transform: scaleX(1);
}

.summary-card-inner {
  padding: 10px 12px;
}

.summary-label {
  font-size: 11px;
  color: #64748b;
  margin-bottom: 6px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.summary-value {
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.2;
  transition: color 0.3s ease;
}

.summary-value.negative {
  color: #ef4444;
}

.summary-value.positive {
  color: #10b981;
}

.summary-desc {
  margin-top: 4px;
  font-size: 10px;
  color: #94a3b8;
  line-height: 1.3;
}

/* 表格卡片 */
.table-card {
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  background: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  margin-bottom: 12px;
  animation: fadeInUp 0.6s ease-out;
  transition: box-shadow 0.3s ease;
}

.table-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.card-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-header-icon {
  font-size: 18px;
  color: #6366f1;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
}

.month-tag {
  margin-left: 4px;
}

.card-header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.count-tag {
  font-weight: 500;
}

.baseline-adjust-dialog :deep(.el-dialog__body) {
  padding: 16px 20px 12px;
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 80%);
}

.adjustment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e2e8f0;
}

.adjustment-title {
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 4px;
}

.adjustment-desc {
  margin: 0;
  color: #64748b;
  font-size: 12px;
}

.adjustment-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 16px 0;
  padding: 10px 14px;
  background: rgba(148, 163, 184, 0.08);
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.toolbar-left {
  display: flex;
  gap: 12px;
  align-items: center;
}

.toolbar-right {
  display: flex;
  gap: 10px;
}

.toolbar-month,
.toolbar-process {
  width: 170px;
}

.adjustment-table {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 6px 24px rgba(15, 23, 42, 0.08);
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.adjustment-table :deep(.el-table__header th) {
  background: linear-gradient(90deg, #eef2ff 0%, #f8fafc 100%);
  color: #1e293b;
  font-weight: 600;
  border-bottom: 1px solid rgba(148, 163, 184, 0.3);
}

.adjustment-table :deep(.el-table__row) {
  transition: background 0.2s ease;
}

.adjustment-table :deep(.el-table__row:hover > td) {
  background: rgba(99, 102, 241, 0.08);
}

.plan-editor {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 6px 10px;
  background: rgba(237, 242, 247, 0.7);
  border-radius: 8px;
}

.plan-editor-current {
  font-size: 12px;
  color: #475569;
}

.plan-input {
  display: flex;
  align-items: center;
}

.plan-input :deep(.el-input-number__increase),
.plan-input :deep(.el-input-number__decrease) {
  display: none;
}

.plan-input :deep(.el-input-number) {
  width: 140px;
}

.plan-input :deep(.el-input__inner) {
  text-align: right;
}

.adjustment-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 8px 0;
}

.adjustment-footer .el-button:first-child {
  font-weight: 600;
}

/* 标签页样式 */
:deep(.el-tabs__header) {
  margin: 0 0 12px 0;
  border-bottom: 2px solid #e2e8f0;
}

:deep(.el-tabs__item) {
  padding: 10px 16px;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.3s ease;
}

:deep(.el-tabs__item.is-active) {
  color: #6366f1;
  font-weight: 600;
}

:deep(.el-tabs__active-bar) {
  background-color: #6366f1;
  height: 2px;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 6px;
}

.tab-icon {
  font-size: 14px;
  color: #6366f1;
}

.tab-count {
  margin-left: 4px;
  font-size: 11px;
}

/* 合計区域美化 */
.tab-total-wrapper {
  margin-top: 12px;
  padding: 14px 16px;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
  animation: fadeInUp 0.5s ease-out;
}

.tab-total-wrapper:hover {
  border-color: #c7d2fe;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.1);
  transform: translateY(-1px);
}

.tab-total-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 2px solid #e2e8f0;
}

.total-icon {
  font-size: 18px;
  color: #6366f1;
}

.tab-total-label {
  font-weight: 700;
  color: #1e293b;
  font-size: 15px;
  letter-spacing: 0.5px;
}

.tab-total-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.total-item {
  padding: 12px 14px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.total-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.3s ease;
}

.total-item:hover {
  border-color: #c7d2fe;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.1);
  transform: translateY(-2px);
}

.total-item:hover::before {
  transform: scaleX(1);
}

.total-item-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.total-item-icon {
  font-size: 14px;
  color: #6366f1;
}

.total-item-label {
  font-size: 11px;
  color: #64748b;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.total-item-value {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 6px;
  line-height: 1.2;
}

/* 不同指标的颜色区分 */
.current-plan-item .total-item-icon {
  color: #3b82f6;
}

.current-plan-item::before {
  background: linear-gradient(90deg, #3b82f6, #2563eb);
}

.current-plan-item .total-item-value {
  color: #3b82f6;
}

.plan-diff-item.diff-positive .total-item-icon {
  color: #10b981;
}

.plan-diff-item.diff-positive::before {
  background: linear-gradient(90deg, #10b981, #059669);
}

.plan-diff-item.diff-positive .total-item-value {
  color: #10b981;
}

.plan-diff-item.diff-negative .total-item-icon {
  color: #ef4444;
}

.plan-diff-item.diff-negative::before {
  background: linear-gradient(90deg, #ef4444, #dc2626);
}

.plan-diff-item.diff-negative .total-item-value {
  color: #ef4444;
}

.actual-item .total-item-icon {
  color: #10b981;
}

.actual-item::before {
  background: linear-gradient(90deg, #10b981, #059669);
}

.actual-item .total-item-value {
  color: #10b981;
}

.actual-diff-item.diff-positive .total-item-icon {
  color: #10b981;
}

.actual-diff-item.diff-positive::before {
  background: linear-gradient(90deg, #10b981, #059669);
}

.actual-diff-item.diff-positive .total-item-value {
  color: #10b981;
}

.actual-diff-item.diff-negative .total-item-icon {
  color: #ef4444;
}

.actual-diff-item.diff-negative::before {
  background: linear-gradient(90deg, #ef4444, #dc2626);
}

.actual-diff-item.diff-negative .total-item-value {
  color: #ef4444;
}

.total-trend-icon {
  font-size: 14px;
  font-weight: 600;
}

.total-trend-icon.trend-up {
  color: #10b981;
}

.total-trend-icon.trend-down {
  color: #ef4444;
}

/* 日期单元格样式 */
.date-cell-wrapper {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 0;
}

.date-icon {
  font-size: 12px;
  color: #6366f1;
  opacity: 0.7;
}

.date-cell {
  font-weight: 500;
  color: #334155;
  font-size: 12px;
}

.negative-number {
  color: #ef4444;
  font-weight: 600;
}

/* 表格样式优化 */
:deep(.comparison-table) {
  font-size: 12px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

:deep(.comparison-table .el-table__inner-wrapper::before) {
  display: none;
}

:deep(.comparison-table .el-table__border-column-patch) {
  display: none;
}

:deep(.comparison-table .el-table__header-wrapper) {
  border-radius: 8px 8px 0 0;
}

:deep(.comparison-table .el-table__header th) {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
  font-weight: 600;
  font-size: 11px;
  padding: 6px 10px;
  border: none;
  text-align: center;
}

:deep(.comparison-table .el-table__header th:first-child) {
  border-radius: 8px 0 0 0;
}

:deep(.comparison-table .el-table__header th .cell) {
  color: white;
  font-weight: 600;
}

:deep(.comparison-table .el-table__body td) {
  padding: 6px 10px;
  border-color: #e2e8f0;
  transition: all 0.2s ease;
}

:deep(.comparison-table .el-table__row) {
  transition: all 0.2s ease;
}

:deep(.comparison-table .el-table__row:hover > td) {
  background-color: #f0f4ff !important;
  transform: scale(1.01);
}

:deep(.comparison-table .el-table__row--striped td) {
  background-color: #fafbfc;
}

:deep(.comparison-table .el-table__row--striped:hover > td) {
  background-color: #eef2ff !important;
}

:deep(.comparison-table .el-table__fixed-left-patch) {
  background-color: transparent;
}

:deep(.comparison-table .el-table__fixed) {
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.05);
}

:deep(.comparison-table .el-table__fixed-left) {
  background-color: white;
}

:deep(.comparison-table .el-table__fixed-left .el-table__header th) {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
}

:deep(.comparison-table .el-table__fixed-left .el-table__body td) {
  background-color: white;
}

:deep(.comparison-table .el-table__fixed-left .el-table__row:hover > td) {
  background-color: #f0f4ff !important;
}

:deep(.comparison-table .el-table__fixed-left .el-table__row--striped td) {
  background-color: #fafbfc;
}

:deep(.comparison-table .el-table__fixed-left .el-table__row--striped:hover > td) {
  background-color: #eef2ff !important;
}

/* 数值单元格样式 */
.number-cell {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
  padding: 3px 6px;
  border-radius: 4px;
  transition: all 0.2s ease;
  min-height: 20px;
}

.number-cell:hover {
  background-color: rgba(99, 102, 241, 0.05);
}

.number-value {
  font-weight: 600;
  font-size: 12px;
  color: #1e293b;
  letter-spacing: 0.2px;
}

.baseline-plan .number-value {
  color: #6366f1;
}

.current-plan .number-value {
  color: #3b82f6;
}

.actual-cell .number-value {
  color: #10b981;
}

.diff-cell.diff-positive {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.05) 100%);
}

.diff-cell.diff-positive .number-value {
  color: #10b981;
}

.diff-cell.diff-negative {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.05) 100%);
}

.diff-cell.diff-negative .number-value {
  color: #ef4444;
}

.diff-cell.diff-zero {
  background: rgba(148, 163, 184, 0.05);
}

.diff-cell.diff-zero .number-value {
  color: #64748b;
}

.trend-icon {
  font-size: 12px;
  font-weight: 600;
}

.trend-icon.trend-up {
  color: #10b981;
  animation: pulseUp 2s ease-in-out infinite;
}

.trend-icon.trend-down {
  color: #ef4444;
  animation: pulseDown 2s ease-in-out infinite;
}

@keyframes pulseUp {
  0%,
  100% {
    opacity: 1;
    transform: translateY(0);
  }
  50% {
    opacity: 0.7;
    transform: translateY(-2px);
  }
}

@keyframes pulseDown {
  0%,
  100% {
    opacity: 1;
    transform: translateY(0);
  }
  50% {
    opacity: 0.7;
    transform: translateY(2px);
  }
}

/* 表格列头样式 */
.column-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
}

.column-header span {
  color: white;
  font-weight: 600;
}

.help-icon {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
  cursor: help;
  transition: all 0.2s ease;
}

.help-icon:hover {
  color: white;
  transform: scale(1.1);
}

/* 动画关键帧 */
@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(15px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
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

/* 响应式设计 */
@media (max-width: 1200px) {
  .action-content {
    flex-direction: column;
  }

  .action-divider {
    width: 100%;
    height: 1px;
    background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
    margin: 8px 0;
  }

  .section-controls {
    width: 100%;
  }

  .section-controls > * {
    flex: 1;
    min-width: 0;
  }

  .summary-row {
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  }

  .tab-total-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .plan-baseline-page {
    padding: 8px;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .summary-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .tab-total-grid {
    grid-template-columns: 1fr;
  }

  .tab-total-wrapper {
    padding: 12px;
  }

  .total-item {
    padding: 10px 12px;
  }

  .total-item-value {
    font-size: 16px;
  }
}
</style>
