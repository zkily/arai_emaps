<template>
  <div class="planning-page">
    <!-- ─── Page Header ─── -->
    <div class="plan-hd">
      <h2 class="plan-hd-title">成型生産計画</h2>
      <p class="plan-hd-sub">基準開始月・工程・設備の順で指定し、品目と数量を登録。ライン上で順次つなげてガントを表示します。</p>
    </div>

    <!-- ─── Filter Bar ─── -->
    <div class="plan-card">
      <div class="setup-bar">
        <el-form :inline="true" label-position="left">
          <el-form-item label="基準開始月">
            <el-date-picker
              v-model="anchorMonth"
              type="month"
              value-format="YYYY-MM"
              placeholder="先頭計画の着手月"
              style="width: 120px"
            />
          </el-form-item>
          <el-form-item label="工程" required>
            <el-select
              v-model="selectedProcessCd"
              filterable
              clearable
              placeholder="先に工程を選択"
              style="width: 160px"
              :loading="loadingProcesses"
              @change="onProcessChange"
            >
              <el-option
                v-for="p in processOptions"
                :key="p.process_cd"
                :value="p.process_cd"
                :label="`${p.process_cd} — ${p.process_name}`"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="ライン">
            <el-select
              v-model="selectedLineId"
              placeholder="ラインを選択"
              style="width: 180px"
              :disabled="!selectedProcessCd"
              :loading="loadingLines"
              @change="onLineChange"
            >
              <el-option
                v-for="line in lines"
                :key="line.id"
                :value="line.id"
                :label="productionLineOptionLabel(line)"
              />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="loadingSchedules" @click="loadSchedules">
              計画を取得
            </el-button>
          </el-form-item>
        </el-form>
        <p
          v-if="selectedProcessCd && !loadingLines && lines.length === 0"
          class="ee-empty-hint"
        >
          この工程に該当する設備がありません（設備マスタの「種別」が工程名または工程CDと一致する行がAPS対象である必要があります）。
        </p>
      </div>
    </div>

    <!-- ─── Add Plan ─── -->
    <div v-if="selectedLineId" class="plan-card add-section">
      <div class="plan-sec-hd">計画追加</div>
      <div class="add-plan-block">
        <el-form :inline="true" :model="newEntry" label-position="left" class="add-form">
          <el-form-item label="製品名" required>
            <el-select
              v-model="selectedEeId"
              filterable
              clearable
              placeholder="製品を選択"
              style="width: 250px"
              :loading="loadingEeProducts"
              @change="onEeProductChange"
            >
              <el-option
                v-for="row in eeProducts"
                :key="row.id"
                :value="row.id"
                :label="eeOptionLabel(row)"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="入力方式">
            <el-radio-group v-model="addQtyMode" size="small">
              <el-radio-button label="batch">バッチ数</el-radio-button>
              <el-radio-button label="piece">本数</el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item :label="addQtyMode === 'batch' ? 'バッチ数' : '本数'" required>
            <el-input
              v-model="plannedQtyInput"
              clearable
              :placeholder="addQtyMode === 'batch' ? 'バッチ数' : '本数'"
              style="width: 90px"
              maxlength="6"
            />
          </el-form-item>
          <el-form-item v-if="addQtySummary" label-width="0">
            <span class="batch-summary">{{ addQtySummary }}</span>
          </el-form-item>
          <el-form-item label-width="0">
            <el-button
              type="success"
              :loading="adding"
              :disabled="!canAddQty"
              @click="addSchedule"
            >追加</el-button>
          </el-form-item>
        </el-form>

        <div v-if="eeStatsDisplay" class="ee-stats-below">
          <div class="ee-stat-row">
            <span class="ee-stat-label">能率</span>
            <span class="ee-readonly">{{ eeStatsDisplay.efficiency_rate }}</span>
            <span class="ee-readonly-unit">本/H</span>
          </div>
          <div class="ee-stat-row">
            <span class="ee-stat-label">段取</span>
            <span class="ee-readonly">{{ eeStatsDisplay.step_time ?? '—' }}</span>
            <span class="ee-readonly-unit">分</span>
          </div>
          <div class="ee-stat-row">
            <span class="ee-stat-label">ロットサイズ</span>
            <span class="ee-readonly">{{ eeStatsDisplay.lot_size ?? '—' }}</span>
            <span class="ee-readonly-unit">本/批</span>
          </div>
          <div class="ee-stat-row">
            <span class="ee-stat-label">最大日産</span>
            <span class="ee-readonly">{{ eeStatsDisplay.maxDaily }}</span>
            <span class="ee-readonly-unit">個/日（⌊能率×{{ EE_DAILY_HOURS_MAX }}⌋）</span>
          </div>
        </div>
      </div>
      <p v-if="selectedLineId && !loadingEeProducts && eeProducts.length === 0" class="ee-empty-hint">
        この設備に紐づく設備能率（equipment_efficiency）の製品がありません。
      </p>
    </div>

    <!-- ─── Empty State ─── -->
    <div
      v-if="selectedLineId && schedulesFetched && !loadingSchedules && schedules.length === 0"
      class="plan-card schedule-empty"
    >
      <el-empty description="計画データがありません" />
    </div>

    <!-- ─── Schedule List ─── -->
    <div v-if="schedules.length > 0" class="plan-card schedule-section">
      <div class="plan-sec-hd">
        計画一覧
        <span class="plan-sec-badge">{{ schedules.length }}</span>
        <span class="plan-sec-sub">行をドラッグして順序を変更</span>
      </div>
      <el-table
        ref="scheduleTableRef"
        :data="sortedSchedules"
        border
        stripe
        size="small"
        class="schedule-table schedule-table-draggable"
        row-key="id"
      >
        <el-table-column
          label="順位"
          width="64"
          align="center"
        >
          <template #header>
            <span class="schedule-order-head" title="行をドラッグして順序を変更">順位</span>
          </template>
          <template #default="{ row }">
            <span class="order-num schedule-drag-hint">{{ row.order_no ?? '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="item_name" label="製品名" width="130" />
        <!-- <el-table-column prop="product_cd" label="製品CD" width="110" /> -->
        <el-table-column label="入力数" width="150" align="center">
          <template #default="{ row }">
            <div class="qty-cell">
              <el-input
                v-model="plannedQtyDrafts[row.id]"
                clearable
                size="small"
                style="width: 60px"
                maxlength="6"
                :placeholder="(row.lot_size_snapshot ?? 0) > 0 ? 'バッチ数' : '本数'"
              />
              <el-button
                type="primary"
                size="small"
                :loading="savingScheduleId === row.id"
                @click="savePlannedQty(row)"
              >
                保存
              </el-button>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="合計(本)" width="100" align="right">
          <template #default="{ row }">
            <span class="total-qty-cell">{{ row.planned_process_qty?.toLocaleString() ?? '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="daily_capacity" label="標準日産能力" width="110" align="right" />
        <el-table-column prop="setup_time" label="段取（分）" width="98" align="right" />
        <el-table-column prop="start_date" label="開始日" width="100" align="center"/>
        <el-table-column prop="end_date" label="終了日" width="100" align="center"/>
        <el-table-column label="状態" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusLabelJa(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" align="center">
          <template #default="{ row }">
            <el-button type="danger" size="small" text @click="removeSchedule(row.id)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="action-bar">
        <el-button type="warning" size="large" :loading="replanning" @click="replanAll">
          ライン順で再計算
        </el-button>
      </div>
    </div>

    <!-- ─── Gantt ─── -->
    <div v-if="ganttDates.length > 0" class="plan-card gantt-section">
      <el-tabs v-model="activeGanttTab" class="gantt-tabs">
        <el-tab-pane label="ガント（日別）" name="daily">
          <div class="gantt-scroll">
            <table class="gantt-table">
              <thead>
                <tr>
                  <th class="gantt-sticky gantt-sticky-line">ライン</th>
                  <th class="gantt-sticky gantt-sticky-order">順位</th>
                  <th class="gantt-sticky gantt-sticky-name">品名</th>
                  <th class="gantt-sticky gantt-sticky-eff">能率</th>
                  <th class="gantt-sticky gantt-sticky-planned">計画数</th>
                  <th
                    v-for="d in ganttDates"
                    :key="d"
                    class="gantt-date-col"
                    :class="{ 'is-weekend': isWeekend(d), 'is-today': isToday(d) }"
                  >
                    <div class="gantt-date-text">{{ d.slice(5) }}</div>
                    <div class="gantt-wd-text">{{ getWeekday(d) }}</div>
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(row, idx) in ganttRows"
                  :key="row.id"
                  :class="['gantt-row', `gantt-rc-${idx % 10}`]"
                >
                  <td class="gantt-sticky gantt-sticky-line">{{ selectedLineDisplayName }}</td>
                  <td class="gantt-sticky gantt-sticky-order">{{ row.order_no ?? '—' }}</td>
                  <td class="gantt-sticky gantt-sticky-name gantt-name">{{ row.item_name }}</td>
                  <td class="gantt-sticky gantt-sticky-eff">{{ formatEfficiencyRatePiecesPerH(row.efficiency_rate) }}</td>
                  <td class="gantt-sticky gantt-sticky-planned">{{ row.planned_process_qty }}</td>
                  <td
                    v-for="d in ganttDates"
                    :key="d"
                    class="gantt-cell"
                    :class="ganttCellClass(row, d)"
                    :title="ganttCellTitle(row, d)"
                  >
                    <span v-if="(row.daily[d] || 0) > 0" class="gantt-qty">{{ row.daily[d] }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </el-tab-pane>
        <el-tab-pane label="ガント（時間別）" name="hourly">
          <p v-if="hourlyColumns.length > 0" class="hourly-toolbar-hint">
            各セルは当該時間区間の計画個数（再計算で <code>schedule_slice_allocations</code> を更新）。非稼働帯は列がありません。
          </p>
          <div v-if="hourlyColumns.length === 0" class="gantt-hourly-placeholder">
            <el-empty description="時間帯別データがありません">
              <template #default>
                <p class="hourly-hint">
                  DB マイグレーション <code>099_schedule_slice_allocations.sql</code> 適用後、「ライン順で再計算」を実行すると、稼働時間帯に按分した計画が表示されます。
                </p>
              </template>
            </el-empty>
          </div>
          <div v-else class="gantt-scroll">
            <table class="gantt-table gantt-hourly-table">
              <thead>
                <tr>
                  <th class="gantt-sticky gantt-sticky-line">設備名</th>
                  <th class="gantt-sticky gantt-sticky-order">順位</th>
                  <th class="gantt-sticky gantt-sticky-name">品名</th>
                  <th class="gantt-sticky gantt-sticky-eff">能率</th>
                  <th class="gantt-sticky gantt-sticky-planned">計画数</th>
                  <th
                    v-for="col in hourlyColumns"
                    :key="col.key"
                    class="gantt-hour-col"
                    :class="{ 'is-today': col.work_date === todayIso }"
                  >
                    <div class="gantt-hour-date">{{ col.work_date.slice(5) }}</div>
                    <div class="gantt-hour-range">{{ formatHm(col.period_start) }}–{{ formatHm(col.period_end) }}</div>
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(row, idx) in hourlyRows"
                  :key="row.schedule_id"
                  :class="['gantt-row', `gantt-rc-${idx % 10}`]"
                >
                  <td class="gantt-sticky gantt-sticky-line">{{ selectedLineDisplayName }}</td>
                  <td class="gantt-sticky gantt-sticky-order">{{ row.order_no ?? '—' }}</td>
                  <td class="gantt-sticky gantt-sticky-name gantt-name">{{ row.item_name }}</td>
                  <td class="gantt-sticky gantt-sticky-eff">{{ formatEfficiencyRatePiecesPerH(row.efficiency_rate) }}</td>
                  <td class="gantt-sticky gantt-sticky-planned">{{ row.planned_process_qty ?? 0 }}</td>
                  <td
                    v-for="col in hourlyColumns"
                    :key="col.key"
                    class="gantt-cell gantt-hour-cell"
                    :class="{ 'gantt-active': (row.slice_qty[col.key] || 0) > 0 }"
                    :title="hourlyCellTitle(row, col)"
                  >
                    <span v-if="(row.slice_qty[col.key] || 0) > 0" class="gantt-qty">{{ row.slice_qty[col.key] }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'
import Sortable from 'sortablejs'
import type { SortableEvent } from 'sortablejs'
import {
  fetchLines,
  fetchSchedules,
  createSchedule,
  updateSchedule,
  deleteSchedule,
  replanLineSequence,
  fetchSchedulingGrid,
  fetchSchedulingHourlyGrid,
  fetchEquipmentEfficiencyProducts,
  productionLineOptionLabel,
  type ProductionLine,
  type ScheduleOut,
  type ScheduleGridRow,
  type HourlyGridColumn,
  type HourlyGridRow,
  type EquipmentEfficiencyProduct,
} from '@/api/aps'
import { fetchProcesses } from '@/api/master/processMaster'
import type { ProcessItem } from '@/types/master'

function firstDayOfMonthIso(month: string): string {
  return `${month}-01`
}

const lines = ref<ProductionLine[]>([])
const selectedLineId = ref<number | null>(null)
const selectedProcessCd = ref<string>('KT04')
const processOptions = ref<ProcessItem[]>([])
const loadingProcesses = ref(false)
const loadingLines = ref(false)
const DEFAULT_ANCHOR_MONTH = '2026-04'
const anchorMonth = ref<string>(DEFAULT_ANCHOR_MONTH)
const anchorDate = ref<string>(firstDayOfMonthIso(DEFAULT_ANCHOR_MONTH))
const loadingSchedules = ref(false)
const adding = ref(false)
const replanning = ref(false)
const savingScheduleId = ref<number | null>(null)
const reordering = ref(false)
const schedules = ref<ScheduleOut[]>([])
/** 計画数（一覧）編集用：把 input 値当作文字暂存（保存时再转整数） */
const plannedQtyDrafts = ref<Record<number, string>>({})
/** el-table インスタンス（行ドラッグ用） */
const scheduleTableRef = ref<{ $el?: HTMLElement } | null>(null)
let scheduleSortable: Sortable | null = null
const eeProducts = ref<EquipmentEfficiencyProduct[]>([])
const loadingEeProducts = ref(false)
/** equipment_efficiency.id */
const selectedEeId = ref<number | null>(null)

/** 計画追加：バッチ数（テキスト入力→追加時に整数化） */
const plannedQtyInput = ref('')
const addQtyMode = ref<'batch' | 'piece'>('batch')

/** 計画追加：バッチ数→合計本数を表示 */
const addQtySummary = computed(() => {
  const qtyNum = parseInt((plannedQtyInput.value || '').trim(), 10)
  if (!Number.isFinite(qtyNum) || qtyNum < 1) return ''
  if (addQtyMode.value === 'piece') {
    return `追加予定: ${qtyNum.toLocaleString()} 本`
  }
  const lotSize = eeStatsDisplay.value?.lot_size
  if (lotSize == null || lotSize <= 0) return ''
  const total = qtyNum * lotSize
  return `${lotSize.toLocaleString()} × ${qtyNum} = ${total.toLocaleString()} 本`
})

/** 計画追加 ボタン有効判定 */
const canAddQty = computed(() => {
  if (selectedEeId.value == null || !newEntry.value.item_name) return false
  const qtyNum = parseInt((plannedQtyInput.value || '').trim(), 10)
  if (!Number.isFinite(qtyNum) || qtyNum < 1) return false
  if (addQtyMode.value === 'piece') return true
  const lotSize = eeStatsDisplay.value?.lot_size
  return lotSize != null && lotSize > 0
})

const newEntry = ref({
  item_name: '',
  product_cd: '',
  daily_capacity: 0,
  setup_time: 0,
})

/** 設備能率マスタ由来の標準/最大稼働時間（日） */
const EE_DAILY_HOURS_STANDARD = 15.3
const EE_DAILY_HOURS_MAX = 23.3

/** 選択中の EE 行：表示用能率・段取・最大日産 */
const eeStatsDisplay = computed(() => {
  if (selectedEeId.value == null) return null
  const row = eeProducts.value.find((r) => r.id === selectedEeId.value)
  if (!row) return null
  const rate = Number(row.efficiency_rate) || 0
  const st = row.step_time
  const maxDaily = rate > 0 ? Math.floor(rate * EE_DAILY_HOURS_MAX) : 0
  const lotSize = row.lot_size
  return {
    efficiency_rate: rate,
    step_time: st != null ? st : null,
    maxDaily,
    lot_size: lotSize != null && Number.isFinite(Number(lotSize)) ? Number(lotSize) : null,
  }
})

const ganttDates = ref<string[]>([])
const ganttRows = ref<ScheduleGridRow[]>([])
const hourlyColumns = ref<HourlyGridColumn[]>([])
const hourlyRows = ref<HourlyGridRow[]>([])
/** ガント表示タブ：daily | hourly */
const activeGanttTab = ref('daily')
/** 計画を取得 API を一度でも成功で呼んだか（空配列含む） */
const schedulesFetched = ref(false)

watch(anchorMonth, (v) => {
  if (!v) return
  anchorDate.value = firstDayOfMonthIso(v)
})

/** order_no → id 安定ソート（一覧・移動用） */
const sortedSchedules = computed(() => {
  return [...schedules.value].sort((a, b) => {
    const oa = a.order_no ?? 1_000_000 + a.id
    const ob = b.order_no ?? 1_000_000 + b.id
    if (oa !== ob) return oa - ob
    return a.id - b.id
  })
})

/** ガント左列：現在選択設備の表示名 */
const selectedLineDisplayName = computed(() => {
  if (selectedLineId.value == null) return '—'
  const ln = lines.value.find((l) => l.id === selectedLineId.value)
  if (!ln) return '—'
  const name = ln.line_name?.trim()
  if (name) return name
  return (ln.line_code?.trim() || String(ln.id))
})

function destroyScheduleSortable() {
  scheduleSortable?.destroy()
  scheduleSortable = null
}

function initScheduleSortable() {
  destroyScheduleSortable()
  if (sortedSchedules.value.length < 2) return
  nextTick(() => {
    const root = scheduleTableRef.value?.$el
    const tbody = root?.querySelector?.('.el-table__body-wrapper tbody') as HTMLElement | undefined | null
    if (!tbody) return
    scheduleSortable = Sortable.create(tbody, {
      animation: 180,
      ghostClass: 'schedule-sortable-ghost',
      dragClass: 'schedule-sortable-drag',
      filter:
        'input, textarea, button, .el-input-number, .el-input, .el-button, .el-select, .el-tag, a',
      // 仅禁止拖拽启动，不阻断输入框的点击/键入
      preventOnFilter: false,
      onEnd: (evt: SortableEvent) => {
        const o = evt.oldIndex
        const n = evt.newIndex
        if (o === undefined || n === undefined || o === n) return
        void persistScheduleOrderAfterDrag(o, n)
      },
    })
  })
}

async function persistScheduleOrderAfterDrag(oldIndex: number, newIndex: number) {
  if (!selectedLineId.value || reordering.value) return
  scheduleSortable?.option('disabled', true)
  const list = sortedSchedules.value.map((s) => s)
  const [moved] = list.splice(oldIndex, 1)
  list.splice(newIndex, 0, moved)
  reordering.value = true
  try {
    await Promise.all(
      list.map((s, i) => updateSchedule(s.id, { order_no: i + 1, run_immediately: false })),
    )
    await replanLineSequence(selectedLineId.value, anchorDate.value || undefined)
    await loadSchedules()
    ElMessage.success('生産順を更新しました')
  } catch (e: unknown) {
    ElMessage.error(formatApiError(e))
    await loadSchedules()
  } finally {
    reordering.value = false
    scheduleSortable?.option('disabled', false)
  }
}

async function loadProcessOptions() {
  loadingProcesses.value = true
  try {
    const res = await fetchProcesses({ page: 1, pageSize: 5000 })
    const list = res.list ?? res.data?.list ?? []
    processOptions.value = Array.isArray(list) ? list : []
  } catch {
    processOptions.value = []
  } finally {
    loadingProcesses.value = false
    // 默认工程：KT04（如果不存在则保持未选择状态）
    const exists = processOptions.value.some((p) => (p.process_cd || '').trim() === 'KT04')
    if (!exists) {
      selectedProcessCd.value = ''
      return
    }
    // 触发加载设备列表
    void onProcessChange()
  }
}

async function onProcessChange() {
  selectedLineId.value = null
  schedules.value = []
  schedulesFetched.value = false
  ganttDates.value = []
  ganttRows.value = []
  hourlyColumns.value = []
  hourlyRows.value = []
  eeProducts.value = []
  selectedEeId.value = null
  lines.value = []
  const cd = (selectedProcessCd.value || '').trim()
  if (!cd) return
  loadingLines.value = true
  try {
    lines.value = await fetchLines(cd)
  } catch {
    lines.value = []
    ElMessage.error('設備一覧の取得に失敗しました')
  } finally {
    loadingLines.value = false
  }
}

onMounted(() => {
  loadProcessOptions()
})

onBeforeUnmount(() => {
  destroyScheduleSortable()
})

function formatApiError(e: unknown): string {
  const err = e as {
    response?: { data?: { detail?: string | { msg?: string }[]; message?: string } }
    message?: string
  }
  const d = err?.response?.data?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d)) {
    const parts = d.map((x) => (typeof x === 'object' && x?.msg ? x.msg : String(x))).filter(Boolean)
    if (parts.length) return parts.join('；')
  }
  return err?.response?.data?.message || err?.message || 'エラーが発生しました'
}

function eeOptionLabel(row: EquipmentEfficiencyProduct): string {
  const name = row.product_name?.trim() || ''
  const cd = row.product_cd?.trim() || ''
  if (name && cd) return `${name}（${cd}）`
  return name || cd || `ID:${row.id}`
}

async function loadEeProducts() {
  selectedEeId.value = null
  plannedQtyInput.value = ''
  newEntry.value.item_name = ''
  newEntry.value.product_cd = ''
  newEntry.value.daily_capacity = 0
  newEntry.value.setup_time = 0
  if (!selectedLineId.value) {
    eeProducts.value = []
    return
  }
  loadingEeProducts.value = true
  try {
    eeProducts.value = await fetchEquipmentEfficiencyProducts(selectedLineId.value)
  } catch {
    eeProducts.value = []
  } finally {
    loadingEeProducts.value = false
  }
}

function onEeProductChange(id: number | string | null | undefined) {
  if (id === '' || id === null || id === undefined) {
    plannedQtyInput.value = ''
    newEntry.value.item_name = ''
    newEntry.value.product_cd = ''
    newEntry.value.daily_capacity = 0
    newEntry.value.setup_time = 0
    return
  }
  const nid = Number(id)
  const row = eeProducts.value.find((r) => r.id === nid)
  if (!row) return
  newEntry.value.item_name = (row.product_name?.trim() || row.product_cd || '').trim()
  newEntry.value.product_cd = row.product_cd?.trim() || ''
  newEntry.value.setup_time = row.step_time ?? 0
  const rate = Number(row.efficiency_rate) || 0
  newEntry.value.daily_capacity = rate > 0 ? Math.floor(rate * EE_DAILY_HOURS_STANDARD) : 0
}

async function onLineChange() {
  schedules.value = []
  schedulesFetched.value = false
  ganttDates.value = []
  ganttRows.value = []
  hourlyColumns.value = []
  hourlyRows.value = []
  await loadEeProducts()
}

async function loadSchedules() {
  if (!(selectedProcessCd.value || '').trim()) {
    ElMessage.warning('工程を選択してください')
    return
  }
  if (!selectedLineId.value) {
    ElMessage.warning('設備を選択してください')
    return
  }
  loadingSchedules.value = true
  try {
    const data = await fetchSchedules({ lineId: selectedLineId.value })
    schedules.value = Array.isArray(data) ? data : []
    plannedQtyDrafts.value = Object.fromEntries(
      schedules.value.map((s) => [
        s.id,
        String(s.planned_batch_count > 0 ? s.planned_batch_count : s.planned_process_qty ?? ''),
      ]),
    )
    schedulesFetched.value = true
    await loadGantt()
  } catch (e: unknown) {
    schedules.value = []
    schedulesFetched.value = false
    ganttDates.value = []
    ganttRows.value = []
    hourlyColumns.value = []
    hourlyRows.value = []
    ElMessage.error(formatApiError(e))
  } finally {
    loadingSchedules.value = false
    initScheduleSortable()
  }
}

async function addSchedule() {
  if (!(selectedProcessCd.value || '').trim()) {
    ElMessage.warning('工程を選択してください')
    return
  }
  if (!selectedLineId.value || selectedEeId.value == null || !newEntry.value.item_name) {
    ElMessage.warning('設備と品名（設備能率マスタ）を選択してください')
    return
  }
  if (newEntry.value.daily_capacity <= 0) {
    ElMessage.warning('日産能力を入力してください（0 より大きい値）')
    return
  }
  const rawQty = (plannedQtyInput.value || '').trim().replace(/[,，]/g, '')
  if (!rawQty) {
    ElMessage.warning(addQtyMode.value === 'batch' ? 'バッチ数を入力してください' : '本数を入力してください')
    return
  }
  const qtyInputNum = parseInt(rawQty, 10)
  if (!Number.isFinite(qtyInputNum) || qtyInputNum < 1) {
    ElMessage.warning(addQtyMode.value === 'batch' ? 'バッチ数は 1 以上の整数を入力してください' : '本数は 1 以上の整数を入力してください')
    return
  }
  adding.value = true
  try {
    const nextOrder = schedules.value.length > 0
      ? Math.max(...schedules.value.map(s => s.order_no ?? 0)) + 1
      : 1

    const payload: Parameters<typeof createSchedule>[0] = {
      line_id: selectedLineId.value,
      order_no: nextOrder,
      item_name: newEntry.value.item_name,
      product_cd: newEntry.value.product_cd || undefined,
      daily_capacity: newEntry.value.daily_capacity,
      setup_time: newEntry.value.setup_time,
      start_date: schedules.value.length === 0 ? (anchorDate.value || undefined) : undefined,
      run_immediately: false,
    }
    if (addQtyMode.value === 'batch') {
      const lotSize = eeStatsDisplay.value?.lot_size
      if (lotSize == null || lotSize <= 0) {
        ElMessage.warning('ロットサイズが未設定です。製品マスタで lot_size を登録してください。')
        return
      }
      const plannedTotalQty = qtyInputNum * lotSize
      payload.planned_batch_count = qtyInputNum
      payload.lot_size_snapshot = lotSize
      payload.planned_process_qty = plannedTotalQty
    } else {
      payload.planned_process_qty = qtyInputNum
      payload.planned_batch_count = 0
    }
    await createSchedule(payload)

    selectedEeId.value = null
    plannedQtyInput.value = ''
    newEntry.value.item_name = ''
    newEntry.value.product_cd = ''
    newEntry.value.daily_capacity = 0
    newEntry.value.setup_time = 0

    await loadSchedules()
    ElMessage.success('追加しました')
  } catch (e: unknown) {
    ElMessage.error(formatApiError(e) || '追加に失敗しました')
  } finally {
    adding.value = false
  }
}

async function removeSchedule(id: number) {
  try {
    await ElMessageBox.confirm('この計画を削除しますか？', '確認', {
      type: 'warning',
      confirmButtonText: '削除',
      cancelButtonText: 'キャンセル',
    })
    await deleteSchedule(id)
    await loadSchedules()
    ElMessage.success('削除しました')
  } catch { /* cancel */ }
}

async function savePlannedQty(row: ScheduleOut) {
  const draft = plannedQtyDrafts.value[row.id] ?? ''
  const raw = draft.trim().replace(/[,，]/g, '')
  const val = parseInt(raw, 10)
  if (!Number.isFinite(val) || val < 1) {
    const hasBatch = (row.lot_size_snapshot ?? 0) > 0
    ElMessage.warning(hasBatch ? 'バッチ数は 1 以上の整数を入力してください' : '本数は 1 以上の整数を入力してください')
    return
  }
  if (!selectedLineId.value) return
  savingScheduleId.value = row.id
  try {
    const hasBatch = (row.lot_size_snapshot ?? 0) > 0
    if (hasBatch) {
      await updateSchedule(row.id, {
        planned_batch_count: val,
        run_immediately: false,
      })
    } else {
      await updateSchedule(row.id, {
        planned_process_qty: val,
        run_immediately: false,
      })
    }
    await replanLineSequence(selectedLineId.value, anchorDate.value || undefined)
    await loadSchedules()
    ElMessage.success('計画を更新しました')
  } catch (e: unknown) {
    ElMessage.error(formatApiError(e))
    await loadSchedules()
  } finally {
    savingScheduleId.value = null
  }
}

async function replanAll() {
  if (!(selectedProcessCd.value || '').trim() || !selectedLineId.value) return
  replanning.value = true
  try {
    await replanLineSequence(selectedLineId.value, anchorDate.value || undefined)
    await loadSchedules()
    ElMessage.success('順次再計算が完了しました')
  } catch (e: unknown) {
    ElMessage.error(formatApiError(e) || '再計算に失敗しました')
  } finally {
    replanning.value = false
  }
}

const todayIso = computed(() => new Date().toISOString().slice(0, 10))

/** equipment_efficiency.efficiency_rate（本/H） */
function formatEfficiencyRatePiecesPerH(v: number | null | undefined): string {
  if (v == null || Number.isNaN(Number(v))) return '—'
  const n = Number(v)
  const s = n % 1 === 0 ? String(Math.round(n)) : n.toFixed(1)
  return `${s}本/H`
}

function formatHm(t: string): string {
  if (!t) return ''
  const parts = t.split(':')
  return parts.length >= 2 ? `${parts[0]}:${parts[1]}` : t
}

function hourlyCellTitle(row: HourlyGridRow, col: HourlyGridColumn): string {
  const q = row.slice_qty[col.key] || 0
  if (q <= 0) return ''
  return `${row.item_name}: ${q}個（${col.work_date} ${formatHm(col.period_start)}–${formatHm(col.period_end)}）`
}

async function loadGantt() {
  hourlyColumns.value = []
  hourlyRows.value = []
  if (!selectedLineId.value || schedules.value.length === 0) {
    ganttDates.value = []
    ganttRows.value = []
    return
  }
  const startDates = schedules.value.map(s => s.start_date).filter(Boolean) as string[]
  const endDates = schedules.value.map(s => s.end_date).filter(Boolean) as string[]
  if (startDates.length === 0) return

  const sd = startDates.sort()[0]
  const edRaw = endDates.sort().pop() || sd
  const ed = addDays(edRaw, 3)

  try {
    const grid = await fetchSchedulingGrid(sd, ed, selectedLineId.value)
    ganttDates.value = grid.dates
    ganttRows.value = grid.blocks.length > 0 ? grid.blocks[0].rows : []
    activeGanttTab.value = 'daily'
    try {
      const hg = await fetchSchedulingHourlyGrid(sd, ed, selectedLineId.value)
      hourlyColumns.value = Array.isArray(hg.columns) ? hg.columns : []
      hourlyRows.value = Array.isArray(hg.rows) ? hg.rows : []
    } catch {
      hourlyColumns.value = []
      hourlyRows.value = []
    }
  } catch {
    ganttDates.value = []
    ganttRows.value = []
    hourlyColumns.value = []
    hourlyRows.value = []
  }
}

function addDays(dateStr: string, n: number): string {
  const d = new Date(dateStr)
  d.setDate(d.getDate() + n)
  return d.toISOString().slice(0, 10)
}

function statusType(s: string): 'success' | 'warning' | 'info' {
  if (s === 'COMPLETED') return 'success'
  if (s === 'IN_PROGRESS') return 'warning'
  return 'info'
}

/** 一覧の状態表示（API の英語コード → 日本語） */
function statusLabelJa(s: string): string {
  const map: Record<string, string> = {
    PLANNING: '計画中',
    IN_PROGRESS: '進行中',
    COMPLETED: '完了',
  }
  return map[s] ?? s
}

function isWeekend(d: string): boolean {
  const day = new Date(d).getDay()
  return day === 0 || day === 6
}

function isToday(d: string): boolean {
  return d === new Date().toISOString().slice(0, 10)
}

function getWeekday(d: string): string {
  const wd = ['日', '月', '火', '水', '木', '金', '土']
  return wd[new Date(d).getDay()]
}

function ganttCellClass(row: ScheduleGridRow, d: string): Record<string, boolean> {
  const qty = row.daily[d] || 0
  const inRange = row.start_date && row.end_date && d >= row.start_date && d <= row.end_date
  return {
    'gantt-active': qty > 0,
    'gantt-range': !!inRange && qty === 0,
    'is-weekend': isWeekend(d),
    'is-today': isToday(d),
  }
}

function ganttCellTitle(row: ScheduleGridRow, d: string): string {
  const qty = row.daily[d] || 0
  if (qty > 0) return `${row.item_name}: ${qty}個`
  return ''
}
</script>

<style scoped>
/* ─── Page Shell ─── */
.planning-page {
  padding: 16px 20px;
  background: #f0f2f5;
  min-height: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* ─── Page Header ─── */
.plan-hd {
  display: flex;
  align-items: baseline;
  gap: 12px;
  padding: 4px 2px 0;
}
.plan-hd-title {
  font-size: 18px;
  font-weight: 700;
  color: #1f2329;
  margin: 0;
  letter-spacing: 0.3px;
}
.plan-hd-sub {
  font-size: 12px;
  color: #8f959e;
  margin: 0;
}

/* ─── Section Cards ─── */
.plan-card {
  background: #fff;
  border-radius: 10px;
  padding: 14px 16px;
  box-shadow: 0 1px 3px rgba(0, 21, 41, 0.06), 0 4px 12px rgba(0, 21, 41, 0.04);
}

/* ─── Section Heading ─── */
.plan-sec-hd {
  font-size: 13px;
  font-weight: 700;
  color: #1f2329;
  margin: 0 0 10px;
  padding-left: 9px;
  border-left: 3px solid #409eff;
  display: flex;
  align-items: center;
  gap: 8px;
  line-height: 1.3;
}
.plan-sec-badge {
  font-size: 11px;
  font-weight: 600;
  background: #409eff;
  color: #fff;
  padding: 1px 7px;
  border-radius: 10px;
  line-height: 18px;
}
.plan-sec-sub {
  font-size: 11px;
  color: #b0b8c4;
  font-weight: 400;
  margin-left: auto;
}

/* ─── Setup Bar ─── */
.setup-bar :deep(.el-form--inline .el-form-item) {
  margin-bottom: 0;
}

/* ─── Add Section ─── */
.add-form { flex-wrap: wrap; }
.add-plan-block { margin-bottom: 2px; }
.ee-stats-below {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  margin: 6px 0 2px;
  padding: 5px 12px;
  background: linear-gradient(135deg, #f8faff 0%, #f2f6ff 100%);
  border-radius: 8px;
  border: 1px solid #dbeafe;
}
.ee-stat-row {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  padding: 3px 14px 3px 0;
  border-right: 1px solid #dbeafe;
  line-height: 1.6;
}
.ee-stat-row:last-child { border-right: none; padding-right: 0; }
.ee-stat-row:not(:first-child) { padding-left: 14px; }
.ee-stat-label { color: #6b7280; white-space: nowrap; }
.ee-readonly { font-weight: 700; color: #1f2329; font-variant-numeric: tabular-nums; }
.ee-readonly-unit { color: #9ca3af; font-size: 11px; }
.ee-empty-hint { margin: 4px 0 0; font-size: 12px; color: #e6a23c; }
.batch-summary {
  font-size: 12px;
  font-weight: 600;
  color: #409eff;
  white-space: nowrap;
}
.total-qty-cell {
  font-size: 12px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

/* ─── Schedule List ─── */
.schedule-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 120px;
}
.schedule-table { width: 100%; }
.schedule-table :deep(.el-table__header th),
.schedule-table :deep(.el-table__cell){
  padding: 6px 6px;
}
.schedule-table :deep(.el-table__body-wrapper tbody td){
  height: 34px;
}
.schedule-table-draggable :deep(.el-table__body-wrapper tbody tr) { cursor: grab; }
.schedule-table-draggable :deep(.el-table__body-wrapper tbody tr:active) { cursor: grabbing; }
.schedule-sortable-ghost { opacity: 0.5; background: #ecf5ff !important; }
.schedule-sortable-drag { opacity: 0.98; }
.schedule-order-head { cursor: help; }
.schedule-drag-hint { font-size: 13px; font-weight: 600; }
.order-num { font-size: 13px; font-weight: 600; }
.qty-cell {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
}
.action-bar { margin-top: 12px; text-align: center; }

/* ─── Gantt Section ─── */
.gantt-tabs :deep(.el-tabs__content) { padding: 0; }
.gantt-tabs :deep(.el-tabs__header) { margin-bottom: 10px; }
.hourly-toolbar-hint {
  margin: 0 0 8px;
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}
.gantt-hourly-placeholder {
  min-height: 180px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.hourly-hint {
  max-width: 480px;
  font-size: 12px;
  color: #606266;
  line-height: 1.55;
  margin: 0 auto;
  text-align: center;
}

/* ─── Gantt Table ─── */
.gantt-scroll { overflow-x: auto; }
.gantt-table {
  border-collapse: collapse;
  font-size: 12px;
  white-space: nowrap;
}
.gantt-table th,
.gantt-table td {
  border: 1px solid #e8ecf0;
  padding: 0 4px;
  text-align: center;
  height: 26px;
  vertical-align: middle;
}
.gantt-table thead th {
  background: #f5f7fb;
  font-weight: 600;
  color: #4b5563;
  font-size: 11px;
}

/* ─── Sticky Columns ─── */
.gantt-sticky {
  position: sticky;
  background: #fafbfc;
  background-color: #fafbfc !important;
  z-index: 100;
  text-align: left;
  border-right: 0 !important; /* 避免 border-collapse + sticky 造成底色透出 */
  box-sizing: border-box;
  background-clip: padding-box;
  overflow: hidden;
  box-shadow: inset -1px 0 0 #e8ecf0, 2px 0 0 #fafbfc; /* 外阴影补齐边界缝隙 */
}
.gantt-table thead .gantt-sticky {
  background: #edf1f7 !important;
  background-color: #edf1f7 !important;
  z-index: 110;
  border-right: 0 !important;
  box-shadow: inset -1px 0 0 #e8ecf0, 2px 0 0 #edf1f7;
}
.gantt-sticky-line {
  left: 0;
  width: 80px;
  min-width: 80px;
  max-width: 80px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.gantt-sticky-order {
  left: 80px;
  width: 44px;
  min-width: 44px;
  max-width: 44px;
  text-align: center;
}
.gantt-sticky-planned {
  left: 326px;
  width: 56px;
  min-width: 56px;
  max-width: 56px;
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.gantt-sticky-eff {
  left: 256px;
  width: 70px;
  min-width: 70px;
  max-width: 70px;
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.gantt-sticky-name {
  left: 124px;
  width: 132px;
  min-width: 132px;
  max-width: 132px;
  text-align: left;
  padding-left: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.gantt-name { font-weight: 600; }

/* ─── Date Columns ─── */
.gantt-date-col { min-width: 42px; }
.gantt-date-text { font-size: 11px; font-weight: 600; }
.gantt-wd-text   { font-size: 9px; color: #9ca3af; margin-top: 1px; }

/* Saturday/Sunday header */
.gantt-date-col.is-weekend .gantt-date-text,
.gantt-date-col.is-weekend .gantt-wd-text {
  color: #ef4444;
  font-weight: 700;
}

.gantt-date-col.is-weekend {
  background: transparent;
}

/* Today header */
.gantt-date-col.is-today {
  background: #fffbeb;
}

/* ─── Data Cells ─── */
.gantt-cell { min-width: 42px; height: 26px; transition: background 0.12s; }
.gantt-qty  { font-size: 11px; font-weight: 600; line-height: 1; }
.gantt-cell.is-weekend:not(.gantt-active) { background: transparent; }
.gantt-cell.is-today { background: #fffbeb; box-shadow: none; }
.gantt-cell.gantt-range { background: #f0f5ff; }

/* ─── Hourly Columns ─── */
.gantt-hour-col { min-width: 52px; vertical-align: bottom; padding-bottom: 3px; }
.gantt-hour-date  { font-size: 10px; color: #6b7280; font-weight: 600; }
.gantt-hour-range { font-size: 9px; color: #9ca3af; }
.gantt-hour-cell  { min-width: 52px; }
.gantt-hour-col.is-today { background: #fffbeb; box-shadow: none; }

/* ─── Per-Row Color Palette (10 colors) ─── */
/* 0 · Blue */
.gantt-rc-0 td.gantt-active { background: #3b82f6; color: #fff; }
.gantt-rc-0 td.gantt-range  { background: #eff6ff; }
.gantt-rc-0 td.gantt-active.is-weekend { background: #60a5fa; }
/* 1 · Emerald */
.gantt-rc-1 td.gantt-active { background: #10b981; color: #fff; }
.gantt-rc-1 td.gantt-range  { background: #ecfdf5; }
.gantt-rc-1 td.gantt-active.is-weekend { background: #34d399; }
/* 2 · Violet */
.gantt-rc-2 td.gantt-active { background: #8b5cf6; color: #fff; }
.gantt-rc-2 td.gantt-range  { background: #f5f3ff; }
.gantt-rc-2 td.gantt-active.is-weekend { background: #a78bfa; }
/* 3 · Amber */
.gantt-rc-3 td.gantt-active { background: #f59e0b; color: #fff; }
.gantt-rc-3 td.gantt-range  { background: #fffbeb; }
.gantt-rc-3 td.gantt-active.is-weekend { background: #fbbf24; }
/* 4 · Pink */
.gantt-rc-4 td.gantt-active { background: #ec4899; color: #fff; }
.gantt-rc-4 td.gantt-range  { background: #fdf2f8; }
.gantt-rc-4 td.gantt-active.is-weekend { background: #f472b6; }
/* 5 · Sky */
.gantt-rc-5 td.gantt-active { background: #0ea5e9; color: #fff; }
.gantt-rc-5 td.gantt-range  { background: #f0f9ff; }
.gantt-rc-5 td.gantt-active.is-weekend { background: #38bdf8; }
/* 6 · Rose */
.gantt-rc-6 td.gantt-active { background: #f43f5e; color: #fff; }
.gantt-rc-6 td.gantt-range  { background: #fff1f2; }
.gantt-rc-6 td.gantt-active.is-weekend { background: #fb7185; }
/* 7 · Lime */
.gantt-rc-7 td.gantt-active { background: #84cc16; color: #fff; }
.gantt-rc-7 td.gantt-range  { background: #f7fee7; }
.gantt-rc-7 td.gantt-active.is-weekend { background: #a3e635; }
/* 8 · Indigo */
.gantt-rc-8 td.gantt-active { background: #6366f1; color: #fff; }
.gantt-rc-8 td.gantt-range  { background: #eef2ff; }
.gantt-rc-8 td.gantt-active.is-weekend { background: #818cf8; }
/* 9 · Teal */
.gantt-rc-9 td.gantt-active { background: #14b8a6; color: #fff; }
.gantt-rc-9 td.gantt-range  { background: #f0fdfa; }
.gantt-rc-9 td.gantt-active.is-weekend { background: #2dd4bf; }
</style>
