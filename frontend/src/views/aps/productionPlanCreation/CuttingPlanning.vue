<template>
  <div class="cutting-planning-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">切断計画作成</h2>
        <p class="page-subtitle">instruction_plans を元に切断機へ自動排産し、ガント・下発・進捗確認まで一括管理します。</p>
      </div>
    </div>

    <el-card shadow="hover" class="toolbar-card">
      <el-form :inline="true" label-position="left" class="toolbar-form">
        <el-form-item label="生産月">
          <el-date-picker
            v-model="productionMonth"
            type="month"
            value-format="YYYY-MM"
            style="width: 140px"
          />
        </el-form-item>
        <el-form-item label="切断機">
          <el-select
            v-model="selectedMachineId"
            clearable
            filterable
            placeholder="すべて"
            style="width: 220px"
          >
            <el-option
              v-for="machine in machines"
              :key="machine.id"
              :label="`${machine.machine_cd} — ${machine.machine_name}`"
              :value="machine.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状態">
          <el-select v-model="selectedStatus" clearable placeholder="すべて" style="width: 160px">
            <el-option label="未下発" value="PLANNED" />
            <el-option label="下発済" value="PUBLISHED" />
            <el-option label="進行中" value="IN_PROGRESS" />
            <el-option label="完了" value="COMPLETED" />
          </el-select>
        </el-form-item>
        <el-form-item label="キーワード">
          <el-input
            v-model="keyword"
            clearable
            placeholder="品番 / 品名 / 材料"
            style="width: 220px"
            @keyup.enter="loadList"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loadingList" @click="loadList">取得</el-button>
          <el-button :loading="syncingInstructions" @click="runSyncFromInstructions">指示取込</el-button>
          <el-button
            type="success"
            :disabled="!runId || selectedRows.length === 0"
            :loading="schedulingSelected"
            @click="runScheduleSelected"
          >
            選択を排産
          </el-button>
          <el-button :loading="autoScheduling" @click="runFullAutoSchedule">全件再排産</el-button>
          <el-button :disabled="!runId || selectedRows.length === 0" :loading="publishing" @click="publishSelected">
            選択下発
          </el-button>
          <el-button :disabled="!runId || listData.items.length === 0" :loading="publishing" @click="publishAll">
            一括下発
          </el-button>
          <el-button :disabled="!selectedMachineId" @click="openCapacityDialog">設備稼働設定</el-button>
          <el-button :loading="loadingReport" @click="openReportDialog">帳票</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="summary-grid">
      <el-card shadow="never" class="summary-card">
        <div class="summary-label">総件数</div>
        <div class="summary-value">{{ progressSummary.total_items }}</div>
      </el-card>
      <el-card shadow="never" class="summary-card">
        <div class="summary-label">生産数（合計）</div>
        <div class="summary-value">{{ progressSummary.total_instruction_production_quantity }}</div>
      </el-card>
      <el-card shadow="never" class="summary-card">
        <div class="summary-label">実績本数</div>
        <div class="summary-value">{{ progressSummary.total_actual_quantity }}</div>
      </el-card>
      <el-card shadow="never" class="summary-card">
        <div class="summary-label">完了済</div>
        <div class="summary-value">{{ progressSummary.completed_items }}</div>
      </el-card>
    </div>

    <el-card shadow="hover" class="list-card">
      <template #header>
        <div class="card-header">
          <div>
            <span class="card-title">切断計画一覧</span>
            <span class="card-subtitle" v-if="selectedMachineId">同一切断機内でドラッグ並び替え可能</span>
          </div>
          <div class="card-meta" v-if="listData.generated_at">生成: {{ formatDateTime(listData.generated_at) }}</div>
        </div>
      </template>

      <el-table
        ref="planTableRef"
        :data="listData.items"
        :height="PLAN_LIST_TABLE_HEIGHT"
        border
        stripe
        size="small"
        row-key="id"
        class="plan-table"
        @selection-change="onSelectionChange"
      >
        <el-table-column type="selection" width="44" />
        <el-table-column label="#" width="60" align="center">
          <template #default="{ row }">{{ row.sequence_no || '-' }}</template>
        </el-table-column>
        <el-table-column prop="planned_day" label="計画日" width="110" />
        <el-table-column prop="assigned_machine" label="切断機" width="140" show-overflow-tooltip />
        <el-table-column prop="product_cd" label="品番" width="120" show-overflow-tooltip />
        <el-table-column prop="product_name" label="品名" min-width="200" show-overflow-tooltip />
        <el-table-column prop="material_name" label="原材料" min-width="180" show-overflow-tooltip />
        <el-table-column prop="instruction_production_quantity" label="生産数" width="90" align="right" />
        <el-table-column prop="production_lot_size" label="ロット" width="80" align="right" />
        <el-table-column prop="estimated_minutes" label="見込分" width="90" align="right" />
        <el-table-column prop="actual_quantity" label="実績" width="80" align="right" />
        <el-table-column label="ロック" width="80" align="center">
          <template #default="{ row }">
            <el-switch
              :model-value="row.is_locked"
              :disabled="!runId || !row.id"
              @change="toggleLock(row, $event)"
            />
          </template>
        </el-table-column>
        <el-table-column label="状態" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="statusElTagType(row.completion_status, row.publish_status)" size="small">
              {{ statusLabel(row.completion_status, row.publish_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="管理コード" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">{{ row.source_management_code || '-' }}</template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card shadow="hover" class="gantt-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">切断ガント / 進捗</span>
          <div class="card-meta">
            <span>{{ ganttRange[0] }}</span>
            <span>〜</span>
            <span>{{ ganttRange[1] }}</span>
          </div>
        </div>
      </template>

      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="日次ガント" name="daily">
          <div v-loading="loadingDailyGantt">
            <div v-if="dailyGantt.blocks.length === 0" class="empty-tip">日次ガントのデータがありません</div>
            <div v-for="block in filteredDailyBlocks" :key="block.machine_id" class="gantt-block">
              <div class="gantt-block-title">{{ block.machine_name }}</div>
              <div class="gantt-scroll">
                <table class="gantt-table">
                  <thead>
                    <tr>
                      <th class="sticky-col">品目</th>
                      <th v-for="d in dailyGantt.dates" :key="d">{{ shortDate(d) }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="row in block.rows" :key="row.item_id">
                      <td class="sticky-col">{{ row.sequence_no }}. {{ row.product_name }}</td>
                      <td v-for="d in dailyGantt.dates" :key="`${row.item_id}_${d}`" :class="{ 'has-value': (row.daily[d] || 0) > 0 }">
                        {{ row.daily[d] || '' }}
                      </td>
                    </tr>
                    <tr class="total-row">
                      <td class="sticky-col">合計</td>
                      <td v-for="d in dailyGantt.dates" :key="`${block.machine_id}_${d}`">{{ block.daily_totals[d] || '' }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="時間帯ガント" name="hourly">
          <div v-loading="loadingHourlyGantt">
            <div v-if="hourlyGantt.columns.length === 0" class="empty-tip">時間帯ガントのデータがありません</div>
            <div v-else class="gantt-scroll">
              <table class="gantt-table">
                <thead>
                  <tr>
                    <th class="sticky-col">品目</th>
                    <th v-for="col in hourlyGantt.columns" :key="col.key">{{ shortDate(col.work_date) }} {{ shortTime(col.period_start) }}-{{ shortTime(col.period_end) }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in hourlyGantt.rows" :key="row.item_id">
                    <td class="sticky-col">{{ row.sequence_no }}. {{ row.product_name }}</td>
                    <td v-for="col in hourlyGantt.columns" :key="`${row.item_id}_${col.key}`" :class="{ 'has-value': (row.slice_qty[col.key] || 0) > 0 }">
                      {{ row.slice_qty[col.key] || '' }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="進捗" name="progress">
          <div v-loading="loadingProgress" class="progress-panel">
            <div class="progress-metrics">
              <div class="progress-metric">
                <span class="metric-label">未下発</span>
                <span class="metric-value">{{ progressSummary.planned_items }}</span>
              </div>
              <div class="progress-metric">
                <span class="metric-label">下発済</span>
                <span class="metric-value">{{ progressSummary.published_items }}</span>
              </div>
              <div class="progress-metric">
                <span class="metric-label">進行中</span>
                <span class="metric-value">{{ progressSummary.in_progress_items }}</span>
              </div>
              <div class="progress-metric">
                <span class="metric-label">完了</span>
                <span class="metric-value">{{ progressSummary.completed_items }}</span>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog v-model="capacityDialogVisible" title="設備稼働設定" width="1100px" destroy-on-close>
      <LineCapacity
        v-if="capacityDialogVisible && selectedMachineId"
        :embed="true"
        :preset-line-id="selectedMachineId"
        :preset-date-range="ganttRange"
      />
    </el-dialog>

    <el-dialog v-model="reportDialogVisible" title="切断計画帳票" width="1000px" destroy-on-close>
      <template #header>
        <div class="card-header">
          <span class="card-title">切断計画帳票</span>
          <el-button size="small" @click="printReport">印刷</el-button>
        </div>
      </template>
      <el-table :data="reportItems" border stripe size="small" v-loading="loadingReport">
        <el-table-column prop="machine_name" label="切断機" width="140" />
        <el-table-column prop="planned_day" label="計画日" width="110" />
        <el-table-column prop="sequence_no" label="#" width="60" />
        <el-table-column prop="product_cd" label="品番" width="120" />
        <el-table-column prop="product_name" label="品名" min-width="200" />
        <el-table-column prop="material_name" label="原材料" min-width="160" />
        <el-table-column prop="instruction_production_quantity" label="生産数" width="100" align="right" />
        <el-table-column prop="estimated_minutes" label="見込分" width="100" align="right" />
        <el-table-column prop="publish_status" label="下発" width="90" />
        <el-table-column prop="completion_status" label="完了" width="90" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: 'CuttingPlanning' })

import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import Sortable from 'sortablejs'
import type { SortableEvent } from 'sortablejs'
import LineCapacity from '../LineCapacity.vue'
import {
  autoScheduleCuttingPlans,
  scheduleCuttingPlanSelected,
  syncCuttingPlanFromInstructions,
  fetchCuttingPlanningGantt,
  fetchCuttingPlanningHourlyGantt,
  fetchCuttingPlanningList,
  fetchCuttingPlanningMachines,
  fetchCuttingPlanningProgress,
  fetchCuttingPlanningReport,
  lockCuttingPlanningItem,
  publishCuttingPlans,
  reorderCuttingPlans,
  type CuttingPlanningDailyBlock,
  type CuttingPlanningGanttResponse,
  type CuttingPlanningHourlyResponse,
  type CuttingPlanningItem,
  type CuttingPlanningListResponse,
  type CuttingPlanningReportItem,
  type CuttingPlanningSummary,
} from '@/api/cuttingPlanning'

function currentMonth(): string {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
}

function monthRange(month: string): [string, string] {
  const [y, m] = month.split('-').map(Number)
  const last = new Date(y, m, 0).getDate()
  return [`${month}-01`, `${month}-${String(last).padStart(2, '0')}`]
}

function shortDate(value: string) {
  return value.slice(5)
}

function shortTime(value: string) {
  return value.slice(0, 5)
}

function formatDateTime(value?: string | null) {
  if (!value) return '-'
  return value.replace('T', ' ').slice(0, 16)
}

function statusLabel(completionStatus?: string | null, publishStatus?: string | null) {
  if (completionStatus === 'COMPLETED') return '完了'
  if (completionStatus === 'IN_PROGRESS') return '進行中'
  if (publishStatus === 'PUBLISHED') return '下発済'
  return '未下発'
}

type ElTagType = 'primary' | 'success' | 'info' | 'warning' | 'danger'

/** ElTag の type は空文字不可。常に上記いずれかを返す */
function statusElTagType(
  completionStatus?: string | null,
  publishStatus?: string | null,
): ElTagType {
  if (completionStatus === 'COMPLETED') return 'success'
  if (completionStatus === 'IN_PROGRESS') return 'warning'
  if (completionStatus === 'UNSCHEDULED') return 'danger'
  if (publishStatus === 'PUBLISHED') return 'info'
  return 'primary'
}

const productionMonth = ref(currentMonth())
const selectedMachineId = ref<number | null>(null)
const selectedStatus = ref<string | null>(null)
const keyword = ref('')
const activeTab = ref('daily')
const machines = ref<CuttingPlanningListResponse['machines']>([])
const listData = ref<CuttingPlanningListResponse>({
  run_id: null,
  generated_at: null,
  published_at: null,
  machines: [],
  items: [],
  summary: {
    total_items: 0,
    planned_items: 0,
    published_items: 0,
    in_progress_items: 0,
    completed_items: 0,
    total_planned_quantity: 0,
    total_instruction_production_quantity: 0,
    total_actual_quantity: 0,
  },
})
const progressSummary = ref<CuttingPlanningSummary>(listData.value.summary)
const dailyGantt = ref<CuttingPlanningGanttResponse>({ dates: [], blocks: [] })
const hourlyGantt = ref<CuttingPlanningHourlyResponse>({ columns: [], rows: [] })
const reportItems = ref<CuttingPlanningReportItem[]>([])
const selectedRows = ref<CuttingPlanningItem[]>([])
/** 切断計画一覧：表本体の固定高さ（px）。行が多いときは表内で縦スクロール、ヘッダーは固定 */
const PLAN_LIST_TABLE_HEIGHT = 440

const planTableRef = ref<{ $el?: HTMLElement } | null>(null)
const capacityDialogVisible = ref(false)
const reportDialogVisible = ref(false)
const loadingList = ref(false)
const autoScheduling = ref(false)
const syncingInstructions = ref(false)
const schedulingSelected = ref(false)
const publishing = ref(false)
const loadingDailyGantt = ref(false)
const loadingHourlyGantt = ref(false)
const loadingProgress = ref(false)
const loadingReport = ref(false)
const ganttRange = ref<[string, string]>(monthRange(productionMonth.value))
let sortable: Sortable | null = null

const runId = computed(() => listData.value.run_id)
const filteredDailyBlocks = computed<CuttingPlanningDailyBlock[]>(() => {
  if (!selectedMachineId.value) return dailyGantt.value.blocks
  return dailyGantt.value.blocks.filter(block => block.machine_id === selectedMachineId.value)
})

function destroySortable() {
  sortable?.destroy()
  sortable = null
}

function onSelectionChange(rows: CuttingPlanningItem[]) {
  selectedRows.value = rows
}

async function loadMachines() {
  machines.value = await fetchCuttingPlanningMachines()
}

async function loadList() {
  loadingList.value = true
  try {
    const data = await fetchCuttingPlanningList({
      productionMonth: productionMonth.value,
      machineId: selectedMachineId.value,
      status: selectedStatus.value,
      keyword: keyword.value || null,
    })
    listData.value = data
    machines.value = data.machines.length > 0 ? data.machines : machines.value
    progressSummary.value = data.summary
    const plannedDates = data.items.map(item => item.planned_day).filter(Boolean) as string[]
    if (plannedDates.length > 0) {
      const sorted = [...plannedDates].sort()
      ganttRange.value = [sorted[0], sorted[sorted.length - 1]]
    } else {
      ganttRange.value = monthRange(productionMonth.value)
    }
    await nextTick()
    initSortable()
    await loadActiveTab()
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '切断計画一覧の取得に失敗しました')
  } finally {
    loadingList.value = false
  }
}

async function loadDailyGantt() {
  if (!productionMonth.value) return
  loadingDailyGantt.value = true
  try {
    dailyGantt.value = await fetchCuttingPlanningGantt({
      productionMonth: productionMonth.value,
      runId: runId.value,
      startDate: ganttRange.value[0],
      endDate: ganttRange.value[1],
    })
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '日次ガントの取得に失敗しました')
  } finally {
    loadingDailyGantt.value = false
  }
}

async function loadHourlyGantt() {
  if (!runId.value) {
    hourlyGantt.value = { columns: [], rows: [] }
    return
  }
  loadingHourlyGantt.value = true
  try {
    hourlyGantt.value = await fetchCuttingPlanningHourlyGantt({
      productionMonth: productionMonth.value,
      runId: runId.value,
      machineId: selectedMachineId.value,
    })
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '時間帯ガントの取得に失敗しました')
  } finally {
    loadingHourlyGantt.value = false
  }
}

async function loadProgress() {
  loadingProgress.value = true
  try {
    progressSummary.value = await fetchCuttingPlanningProgress({ productionMonth: productionMonth.value })
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '進捗の取得に失敗しました')
  } finally {
    loadingProgress.value = false
  }
}

async function loadActiveTab() {
  if (activeTab.value === 'daily') {
    await loadDailyGantt()
  } else if (activeTab.value === 'hourly') {
    await loadHourlyGantt()
  } else {
    await loadProgress()
  }
}

function handleTabChange() {
  void loadActiveTab()
}

async function runSyncFromInstructions() {
  syncingInstructions.value = true
  try {
    await syncCuttingPlanFromInstructions({ production_month: productionMonth.value })
    await loadList()
    ElMessage.success('instruction_plans を cutting_plan_items に取り込みました')
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '指示取込に失敗しました')
  } finally {
    syncingInstructions.value = false
  }
}

async function runScheduleSelected() {
  if (!runId.value || selectedRows.value.length === 0) return
  schedulingSelected.value = true
  try {
    await scheduleCuttingPlanSelected({
      production_month: productionMonth.value,
      run_id: runId.value,
      item_ids: selectedRows.value.map(row => Number(row.id)).filter(id => Number.isFinite(id) && id > 0),
      machine_ids: selectedMachineId.value ? [selectedMachineId.value] : null,
      start_date: ganttRange.value[0],
      horizon_days: 45,
    })
    selectedRows.value = []
    await loadList()
    ElMessage.success('選択行の排産を更新しました')
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '選択排産に失敗しました')
  } finally {
    schedulingSelected.value = false
  }
}

async function runFullAutoSchedule() {
  try {
    await ElMessageBox.confirm(
      '既存明細を削除し、instruction_plans から全件を再計算して上書きします（下発・ロックは保持設定に依存）。よろしいですか？',
      '全件再排産',
      { confirmButtonText: '実行', cancelButtonText: 'キャンセル', type: 'warning' },
    )
  } catch {
    return
  }
  autoScheduling.value = true
  try {
    await autoScheduleCuttingPlans({
      production_month: productionMonth.value,
      machine_ids: selectedMachineId.value ? [selectedMachineId.value] : null,
      start_date: ganttRange.value[0],
      horizon_days: 45,
      preserve_published: true,
    })
    await loadList()
    ElMessage.success('全件再排産が完了しました')
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '全件再排産に失敗しました')
  } finally {
    autoScheduling.value = false
  }
}

async function publishSelected() {
  if (!runId.value || selectedRows.value.length === 0) return
  publishing.value = true
  try {
    const res = await publishCuttingPlans({
      run_id: runId.value,
      item_ids: selectedRows.value.map(row => Number(row.id)).filter(Boolean),
      overwrite_existing: false,
    })
    selectedRows.value = []
    await loadList()
    ElMessage.success(`下発完了: ${res.published_count} 件`)
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '選択下発に失敗しました')
  } finally {
    publishing.value = false
  }
}

async function publishAll() {
  if (!runId.value) return
  try {
    await ElMessageBox.confirm('未下発の切断計画をすべて cutting_management に下発します。よろしいですか？', '確認', {
      confirmButtonText: '下発',
      cancelButtonText: 'キャンセル',
      type: 'warning',
    })
  } catch {
    return
  }
  publishing.value = true
  try {
    const res = await publishCuttingPlans({
      run_id: runId.value,
      overwrite_existing: false,
    })
    await loadList()
    ElMessage.success(`下発完了: ${res.published_count} 件`)
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '一括下発に失敗しました')
  } finally {
    publishing.value = false
  }
}

function openCapacityDialog() {
  if (!selectedMachineId.value) {
    ElMessage.warning('切断機を先に選択してください')
    return
  }
  capacityDialogVisible.value = true
}

async function openReportDialog() {
  loadingReport.value = true
  reportDialogVisible.value = true
  try {
    const data = await fetchCuttingPlanningReport({ productionMonth: productionMonth.value })
    reportItems.value = data.items
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '帳票の取得に失敗しました')
  } finally {
    loadingReport.value = false
  }
}

function printReport() {
  const rows = reportItems.value
    .map(item => `
      <tr>
        <td>${item.machine_name ?? ''}</td>
        <td>${item.planned_day ?? ''}</td>
        <td>${item.sequence_no}</td>
        <td>${item.product_cd}</td>
        <td>${item.product_name}</td>
        <td>${item.material_name ?? ''}</td>
        <td>${item.instruction_production_quantity ?? item.planned_quantity}</td>
        <td>${item.estimated_minutes}</td>
        <td>${item.publish_status}</td>
        <td>${item.completion_status}</td>
      </tr>
    `)
    .join('')
  const html = `<!DOCTYPE html><html><head><meta charset="UTF-8" /><title>切断計画帳票</title><style>
    body{font-family:Arial,sans-serif;padding:16px}
    table{width:100%;border-collapse:collapse;font-size:12px}
    th,td{border:1px solid #ccc;padding:6px 8px;text-align:left}
    th{background:#f5f5f5}
    h1{font-size:18px;margin:0 0 12px}
  </style></head><body><h1>切断計画帳票 ${productionMonth.value}</h1><table><thead><tr><th>切断機</th><th>計画日</th><th>#</th><th>品番</th><th>品名</th><th>原材料</th><th>生産数</th><th>見込分</th><th>下発</th><th>完了</th></tr></thead><tbody>${rows}</tbody></table></body></html>`
  const win = window.open('', '_blank', 'width=1200,height=800')
  if (!win) return
  win.document.write(html)
  win.document.close()
  win.focus()
  win.print()
}

function initSortable() {
  destroySortable()
  if (!selectedMachineId.value || !runId.value || listData.value.items.length <= 1 || !!selectedStatus.value || !!keyword.value) return
  const root = planTableRef.value?.$el
  const tbody = root?.querySelector('.el-table__body-wrapper tbody')
  if (!tbody) return
  sortable = Sortable.create(tbody as HTMLElement, {
    animation: 150,
    handle: 'tr',
    onEnd: (evt: SortableEvent) => {
      if (evt.oldIndex == null || evt.newIndex == null || evt.oldIndex === evt.newIndex) return
      const copied = [...listData.value.items]
      const [moved] = copied.splice(evt.oldIndex, 1)
      if (!moved) return
      copied.splice(evt.newIndex, 0, moved)
      listData.value = { ...listData.value, items: copied }
      void persistOrder()
    },
  })
}

async function persistOrder() {
  if (!runId.value || !selectedMachineId.value) return
  const orderedIds = listData.value.items
    .map(item => Number(item.id))
    .filter(id => Number.isFinite(id) && id > 0)
  if (orderedIds.length === 0) return
  try {
    const data = await reorderCuttingPlans({
      run_id: runId.value,
      machine_id: selectedMachineId.value,
      ordered_item_ids: orderedIds,
      horizon_days: 45,
    })
    listData.value = data
    await loadList()
    ElMessage.success('順序を更新しました')
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '並び替えに失敗しました')
  }
}

async function toggleLock(row: CuttingPlanningItem, value: string | number | boolean) {
  if (!runId.value || !row.id) return
  try {
    await lockCuttingPlanningItem({
      run_id: runId.value,
      item_id: Number(row.id),
      is_locked: Boolean(value),
    })
    await loadList()
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || 'ロック状態の更新に失敗しました')
  }
}

watch([selectedMachineId, selectedStatus], () => {
  void loadList()
})

watch(productionMonth, (value) => {
  ganttRange.value = monthRange(value)
  void loadList()
})

watch(keyword, () => {
  if (!keyword.value) {
    void loadList()
  }
})

onMounted(async () => {
  await loadMachines()
  await loadList()
})

onBeforeUnmount(() => {
  destroySortable()
})
</script>

<style scoped>
.cutting-planning-page {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
}

.page-subtitle {
  margin: 6px 0 0;
  color: #606266;
}

.toolbar-card,
.list-card,
.gantt-card {
  border-radius: 12px;
}

.toolbar-form {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 0;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.summary-card {
  border-radius: 12px;
}

.summary-label {
  color: #909399;
  font-size: 13px;
}

.summary-value {
  margin-top: 8px;
  font-size: 28px;
  font-weight: 700;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.card-title {
  font-weight: 700;
}

.card-subtitle,
.card-meta {
  color: #909399;
  font-size: 12px;
}

.plan-table :deep(.el-table__row) {
  cursor: move;
}

.gantt-block {
  margin-bottom: 20px;
}

.gantt-block-title {
  margin-bottom: 8px;
  font-weight: 700;
}

.gantt-scroll {
  overflow: auto;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.gantt-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 960px;
}

.gantt-table th,
.gantt-table td {
  border: 1px solid #ebeef5;
  padding: 6px 8px;
  text-align: center;
  white-space: nowrap;
  font-size: 12px;
}

.gantt-table th {
  background: #f8fafc;
}

.sticky-col {
  position: sticky;
  left: 0;
  background: #fff;
  z-index: 1;
  text-align: left !important;
  min-width: 180px;
}

.has-value {
  background: #ecf5ff;
  color: #409eff;
  font-weight: 600;
}

.total-row td {
  background: #f5f7fa;
  font-weight: 700;
}

.progress-panel {
  padding: 12px 0;
}

.progress-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.progress-metric {
  padding: 16px;
  border: 1px solid #ebeef5;
  border-radius: 10px;
  background: #fff;
}

.metric-label {
  display: block;
  color: #909399;
  font-size: 13px;
}

.metric-value {
  display: block;
  margin-top: 8px;
  font-size: 24px;
  font-weight: 700;
}

.empty-tip {
  padding: 24px 0;
  color: #909399;
  text-align: center;
}

@media (max-width: 1200px) {
  .summary-grid,
  .progress-metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
