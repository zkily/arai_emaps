<template>
  <div class="welding-plan-list-page">
    <div class="plan-hd">
      <h2 class="plan-hd-title">
        <span class="plan-hd-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" focusable="false">
            <path
              d="M7 2a1 1 0 0 1 1 1v1h8V3a1 1 0 1 1 2 0v1h1a3 3 0 0 1 3 3v3H2V7a3 3 0 0 1 3-3h1V3a1 1 0 0 1 1-1ZM2 12h20v5a3 3 0 0 1-3 3H5a3 3 0 0 1-3-3v-5Zm6 3a1 1 0 0 0 0 2h2a1 1 0 0 0 0-2H8Zm5 0a1 1 0 1 0 0 2h3a1 1 0 1 0 0-2h-3Z"
            />
          </svg>
        </span>
        溶接計画一覧
      </h2>
      <p class="plan-hd-sub">
        工程・期間を指定し、対象期間に重なる APS 製造指示を<strong>日別ガント</strong>で表示します（計画／実績／残）。
      </p>
    </div>

    <div class="plan-card filter-card">
      <el-form :inline="true" label-position="left" class="filter-form">
        <el-form-item label="期間" required>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            unlink-panels
            range-separator="~"
            start-placeholder="開始日"
            end-placeholder="終了日"
            value-format="YYYY-MM-DD"
            format="YYYY-MM-DD"
            style="width: 280px"
          />
        </el-form-item>
        <el-form-item label="工程" required>
          <el-select
            v-model="selectedProcessCd"
            filterable
            clearable
            placeholder="工程を選択"
            style="width: 200px"
            :loading="loadingProcesses"
          >
            <el-option
              v-for="p in processOptions"
              :key="p.process_cd"
              :value="p.process_cd"
              :label="`${p.process_cd} — ${p.process_name}`"
            />
          </el-select>
        </el-form-item>
        <el-form-item label-width="0">
          <el-button type="primary" :loading="loading" :disabled="!canSearch" @click="onSearchClick">
            検索
          </el-button>
        </el-form-item>
      </el-form>
      <div v-if="canSearch" class="welding-replan-toolbar">
        <el-button
          type="warning"
          size="small"
          class="welding-replan-toolbar__primary"
          :loading="bulkReplanning"
          :disabled="loading || bulkReplanning"
          @click="replanAllLinesForProcess"
        >
          溶接ライン順で再計算
        </el-button>
        <el-button
          size="small"
          :disabled="!preReplanGridSnapshot || loading || bulkReplanning"
          @click="restorePreReplanGrid"
        >
          再計算前の表示に戻す
        </el-button>
        <span v-if="preReplanGridSnapshot" class="welding-replan-toolbar__note">
          画面上の一覧のみ再計算直前の取得結果に戻します（DB は既に更新済み）。最新データは「検索」で再取得してください。
        </span>
      </div>
    </div>

    <div v-if="searched" v-loading="loading" class="plan-card result-card">
      <el-tabs v-model="activeResultTab" class="result-tabs">
        <el-tab-pane label="ガント（日別）" name="gantt">
          <div class="gantt-legend-bar">
            <span class="legend-item"><span class="legend-dot legend-dot--plan" />計画</span>
            <span class="legend-item"><span class="legend-dot legend-dot--actual" />実績</span>
            <span class="legend-item"><span class="legend-dot legend-dot--remain" />残</span>
            <el-button
              size="small"
              class="gantt-print-btn"
              :icon="Printer"
              :disabled="loading || ganttRows.length === 0"
              @click="handleGanttPrint"
            >
              印刷
            </el-button>
            <span class="gantt-range-note">表示期間：{{ displayRangeText }}</span>
          </div>

          <el-empty
            v-if="!loading && ganttRows.length === 0"
            description="条件に一致する計画がありません"
          />

          <div v-else class="gantt-scroll list-gantt-scroll">
            <table class="gantt-table list-gantt-table">
              <thead>
                <tr>
                  <th class="gantt-sticky gantt-sticky-line">設備</th>
                  <th class="gantt-sticky gantt-sticky-order">順位</th>
                  <th class="gantt-sticky gantt-sticky-name">品名</th>
                  <th class="gantt-sticky gantt-sticky-eff">能率</th>
                  <th class="gantt-sticky gantt-sticky-planned">計画数</th>
                  <th class="gantt-sticky gantt-sticky-actual">実績数</th>
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
              <tbody v-for="group in ganttGroups" :key="group.lineLabel">
                <tr class="gantt-group-row">
                  <td
                    class="gantt-sticky gantt-sticky-line gantt-group-cell gantt-group-line"
                    :title="group.lineLabel"
                  >
                    {{ group.lineLabel }}
                  </td>
                  <td class="gantt-sticky gantt-sticky-order gantt-group-cell" />
                  <td class="gantt-sticky gantt-sticky-name gantt-group-cell" />
                  <td class="gantt-sticky gantt-sticky-eff gantt-group-cell gantt-group-num">
                    {{ formatGroupEfficiency(group.avgEfficiencyRate) }}
                  </td>
                  <td class="gantt-sticky gantt-sticky-planned gantt-group-cell gantt-group-num">
                    {{ formatNum(group.plannedTotal) }}
                  </td>
                  <td class="gantt-sticky gantt-sticky-actual gantt-group-cell gantt-group-num">
                    {{ formatNum(group.actualTotal) }}
                  </td>
                  <td
                    v-for="d in ganttDates"
                    :key="`grp-${group.lineLabel}-${d}`"
                    class="gantt-cell gantt-group-date-cell"
                  />
                </tr>
                <tr
                  v-for="(row, gIdx) in group.rows"
                  :key="row.id"
                  :class="['gantt-row', gIdx % 2 === 1 ? 'gantt-row--alt' : 'gantt-row--base']"
                >
                  <td class="gantt-sticky gantt-sticky-line gantt-line-empty" />
                  <td class="gantt-sticky gantt-sticky-order">{{ row.order_no ?? '—' }}</td>
                  <td class="gantt-sticky gantt-sticky-name gantt-name">{{ row.item_name }}</td>
                  <td class="gantt-sticky gantt-sticky-eff">{{ formatEfficiencyRatePiecesPerH(row.efficiency_rate) }}</td>
                  <td class="gantt-sticky gantt-sticky-planned">{{ row.planned_process_qty }}</td>
                  <td class="gantt-sticky gantt-sticky-actual">{{ periodActualForRow(row).toLocaleString() }}</td>
                  <td
                    v-for="d in ganttDates"
                    :key="d"
                    class="gantt-cell"
                    :class="{ 'gantt-cell--tone': ganttCellHasSoftTone(row, d) }"
                    :title="ganttCellTitle(row, d)"
                    :aria-label="ganttCellHasAnyMarker(row, d) ? ganttCellTitle(row, d) : undefined"
                  >
                    <div v-if="ganttCellHasAnyMarker(row, d)" class="gantt-cell-markers">
                      <span v-if="ganttDayQty(row.daily?.[d]) !== 0" class="gantt-seg gantt-seg--plan">
                        <span class="gantt-dot gantt-dot--plan" role="presentation" />
                        <span class="gantt-seg-val">{{ ganttDayQty(row.daily?.[d]) }}</span>
                      </span>
                      <span v-if="ganttDayQty(row.actual_daily?.[d]) !== 0" class="gantt-seg gantt-seg--actual">
                        <span class="gantt-dot gantt-dot--actual" role="presentation" />
                        <span class="gantt-seg-val">{{ ganttDayQty(row.actual_daily?.[d]) }}</span>
                      </span>
                      <span v-if="shouldShowGanttRemain(row, d)" class="gantt-seg gantt-seg--remain">
                        <span class="gantt-dot gantt-dot--remain" role="presentation" />
                        <span class="gantt-seg-val">{{ ganttDayQty(row.remaining_daily?.[d]) }}</span>
                      </span>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </el-tab-pane>

        <el-tab-pane label="一覧（表）" name="table">
          <div class="plan-sec-hd plan-sec-hd--inner">
            溶接工程生産スケジュール一覧
            <span class="plan-sec-badge">{{ filteredTableRows.length }}</span>
            <span v-if="tableTabFiltersActive && tableRows.length > 0" class="plan-sec-sub table-filter-hint">
              全 {{ tableRows.length }} 件中
            </span>
          </div>
          <!-- <p class="table-range-note">
            当工程の<strong>全設備・全製造指示</strong>を表示します。実績・不良・残の日次合計は検索期間ではなく、システム上の広い明細取得範囲で集計します（{{ tableGridRangeNote }}）。
          </p> -->

          <div v-if="tableRows.length > 0" class="table-filter-toolbar-card">
            <div class="table-tab-filter-bar">
              <div class="table-filter-field table-filter-field--line">
                <span class="table-filter-field__lead" title="設備で絞込">
                  <el-icon class="table-filter-field__icon"><OfficeBuilding /></el-icon>
                  <span class="table-filter-field__label">設備</span>
                </span>
                <el-select
                  v-model="tableFilterLineId"
                  clearable
                  filterable
                  placeholder="すべて"
                  class="table-tab-filter-select"
                >
                  <el-option
                    v-for="opt in tableLineFilterOptions"
                    :key="opt.id"
                    :label="opt.label"
                    :value="opt.id"
                  />
                </el-select>
              </div>
              <div class="table-filter-field table-filter-field--product">
                <span class="table-filter-field__lead" title="製品で絞込">
                  <el-icon class="table-filter-field__icon"><Goods /></el-icon>
                  <span class="table-filter-field__label">製品</span>
                </span>
                <el-select
                  v-model="tableFilterProductKey"
                  clearable
                  filterable
                  placeholder="すべて"
                  class="table-tab-filter-select table-tab-filter-select--product"
                >
                  <el-option
                    v-for="opt in tableProductFilterOptions"
                    :key="opt.value"
                    :label="opt.label"
                    :value="opt.value"
                  />
                </el-select>
              </div>
              <div class="table-filter-toolbar-divider" aria-hidden="true" />
              <div class="table-filter-status-cluster">
                <span class="table-filter-status-cluster__title" title="一覧に表示する状態">
                  <el-icon class="table-filter-status-cluster__title-icon"><Switch /></el-icon>
                  状態
                </span>
                <div class="table-filter-pill" :class="{ 'table-filter-pill--on': tableShowStatusDone }">
                  <span class="table-filter-pill__text">生産済</span>
                  <el-switch
                    v-model="tableShowStatusDone"
                    size="small"
                    inline-prompt
                    class="table-filter-switch"
                    :active-text="'表示'"
                    :inactive-text="'隠す'"
                  />
                </div>
                <div class="table-filter-pill" :class="{ 'table-filter-pill--on': tableShowStatusPending }">
                  <span class="table-filter-pill__text">準備中</span>
                  <el-switch
                    v-model="tableShowStatusPending"
                    size="small"
                    inline-prompt
                    class="table-filter-switch"
                    :active-text="'表示'"
                    :inactive-text="'隠す'"
                  />
                </div>
              </div>
              <div class="table-filter-bar-spacer" aria-hidden="true" />
              <el-button
                type="primary"
                plain
                size="small"
                class="table-filter-print-btn"
                :icon="Printer"
                :disabled="loading || filteredTableRows.length === 0"
                @click="handleTableListPrint"
              >
                印刷
              </el-button>
            </div>
          </div>

          <el-empty
            v-if="!loading && tableRows.length === 0"
            description="条件に一致する計画がありません"
            class="schedule-empty"
          />
          <el-empty
            v-else-if="!loading && filteredTableRows.length === 0"
            description="絞込み条件に一致する計画がありません"
            class="schedule-empty"
          />

          <div v-else-if="!loading" class="schedule-table-group-list">
            <section
              v-for="group in tableGroups"
              :key="group.lineLabel"
              class="schedule-table-wrap schedule-table-group"
            >
              <div class="schedule-group-title">{{ group.lineLabel }}</div>
              <el-table
                :data="group.rows"
                border
                size="small"
                row-key="id"
                class="schedule-list-table nest-table--polish"
                empty-text=" "
                :row-class-name="scheduleTableRowClassName"
              >
                <el-table-column prop="order_no" label="順位" width="72" align="center" />
                <el-table-column :label="'製品名'" width="160" show-overflow-tooltip>
                  <template #default="{ row }">
                    <span class="product-name-cell">{{ row.item_name || '—' }}</span>
                  </template>
                </el-table-column>
                <el-table-column :label="'開始'" width="110" align="center">
                  <template #default="{ row }">
                    <span class="date-cell">{{ effectiveScheduleDateSpan(row).start || '—' }}</span>
                  </template>
                </el-table-column>
                <el-table-column :label="'終了'" width="110" align="center">
                  <template #default="{ row }">
                    <span class="date-cell">{{ effectiveScheduleDateSpan(row).end || '—' }}</span>
                  </template>
                </el-table-column>
                <el-table-column :label="'計画'" width="92" align="right">
                  <template #default="{ row }">
                    <span class="qty-cell">{{ formatNum(row.planned_process_qty) }}</span>
                  </template>
                </el-table-column>
                <el-table-column :label="'実績'" width="92" align="right">
                  <template #default="{ row }">
                    <span class="qty-cell qty-cell--actual">{{ formatNum(tableActual(row)) }}</span>
                  </template>
                </el-table-column>
                <el-table-column :label="'不良'" width="88" align="right">
                  <template #default="{ row }">
                    <span class="qty-cell qty-cell--defect">{{ formatNum(tableDefect(row)) }}</span>
                  </template>
                </el-table-column>
                <el-table-column :label="'前工程不良'" width="100" align="right">
                  <template #default="{ row }">
                    <span class="qty-cell qty-cell--upstream">{{ formatNum(tableUpstreamDefect(row)) }}</span>
                  </template>
                </el-table-column>
                <el-table-column :label="'残'" width="92" align="right">
                  <template #default="{ row }">
                    <span class="qty-cell">{{ formatNum(tableRemaining(row)) }}</span>
                  </template>
                </el-table-column>
                <el-table-column :label="'進捗'" width="92" align="right">
                  <template #default="{ row }">
                    <span class="qty-cell">{{ tableProgress(row) }}</span>
                  </template>
                </el-table-column>
                <el-table-column :label="'状態'" width="124" align="center">
                  <template #default="{ row }">
                    <div class="status-lamp-cell">
                      <span
                        class="status-lamp-dot"
                        :class="{
                          'status-lamp-dot--done': tableStatusKind(row) === 'done',
                          'status-lamp-dot--ongoing': tableStatusKind(row) === 'ongoing',
                          'status-lamp-dot--pending': tableStatusKind(row) === 'pending',
                        }"
                        :title="tableStatusLabel(row)"
                      />
                      <span class="status-lamp-label">{{ tableStatusLabel(row) }}</span>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
            </section>
          </div>
        </el-tab-pane>

        <el-tab-pane label="設備操業度" name="utilization">
          <div class="plan-sec-hd plan-sec-hd--inner util-sec-hd">
            <span>設備操業度（月次）</span>
            <span class="plan-sec-badge">{{ utilizationRows.length }}</span>
            <div
              class="util-month-surface"
              :class="{
                'util-month-surface--disabled':
                  !(selectedProcessCd || '').trim() || loadingUtilizationMonth,
              }"
            >
              <el-icon class="util-month-surface__icon"><Calendar /></el-icon>
              <div class="util-month-surface__main util-month-surface__main--row">
                <span class="util-month-surface__kicker">集計月</span>
                <el-date-picker
                  v-model="utilizationMonth"
                  type="month"
                  value-format="YYYY-MM"
                  format="YYYY年MM月"
                  placeholder="月を選択"
                  class="util-month-picker"
                  :disabled="!(selectedProcessCd || '').trim() || loadingUtilizationMonth"
                  :clearable="false"
                  teleported
                />
              </div>
            </div>
            <span class="util-hd-spacer" />
            <el-button
              size="small"
              type="warning"
              plain
              class="util-print-btn"
              :disabled="loadingUtilizationMonth || utilizationRows.length === 0"
              @click="handleUtilizationPrint"
            >
              印刷
            </el-button>
          </div>
          <div class="util-note">
            <span class="util-note-chip">対象：{{ utilizationMonthLabelJp }}</span>
            <span class="util-note-chip util-note-chip--formula">操業度＝各時間÷理論稼働</span>
            <span class="util-note-chip util-note-chip--formula">差異工時＝上記期間の Σ((実績−計画)/能率)</span>
          </div>

          <el-empty
            v-if="!loadingUtilizationMonth && !(selectedProcessCd || '').trim()"
            description="先に工程を選択してください（上部の工程）"
            class="schedule-empty"
          />
          <el-empty
            v-else-if="!loadingUtilizationMonth && utilizationRows.length === 0"
            description="集計対象データがありません"
            class="schedule-empty"
          />
          <div v-else v-loading="loadingUtilizationMonth" class="schedule-table-wrap util-table-wrap">
            <el-table
              :data="utilizationRows"
              border
              stripe
              size="small"
              class="schedule-list-table nest-table--polish util-table util-table--modern"
            >
              <el-table-column prop="lineLabel" label="設備" width="65" show-overflow-tooltip />
              <el-table-column prop="scheduleCount" label="指示数" width="75" align="center" />
              <el-table-column width="105" align="right">
                <template #header>
                  <span
                    class="util-col-head"
                    title="集計月の暦日すべてについて、line_capacities.available_hours を日別に合算した理論値。未登録日は設備の default_work_hours。計画/実績の集計日とは独立（整月の分母）。"
                  >
                    理論稼働(H)
                  </span>
                </template>
                <template #default="{ row }"><span class="util-num">{{ formatHours(row.availableHours) }}</span></template>
              </el-table-column>
              <el-table-column label="計画数" width="80" align="right">
                <template #default="{ row }"><span class="util-num">{{ formatNum(row.plannedQty) }}</span></template>
              </el-table-column>
              <el-table-column label="実績数" width="80" align="right">
                <template #default="{ row }"><span class="util-num util-num--actual">{{ formatNum(row.actualQty) }}</span></template>
              </el-table-column>
              <el-table-column label="計画時間(H)" width="110" align="right">
                <template #default="{ row }"><span class="util-num">{{ formatHours(row.plannedHours) }}</span></template>
              </el-table-column>
              <el-table-column label="実績時間(H)" width="110" align="right">
                <template #default="{ row }"><span class="util-num util-num--actual">{{ formatHours(row.actualHours) }}</span></template>
              </el-table-column>
              <el-table-column label="計画操業度" width="100" align="right">
                <template #default="{ row }"><span class="util-num">{{ formatPercent(row.planUtilizationPct) }}</span></template>
              </el-table-column>
              <el-table-column label="実績操業度" width="100" align="right">
                <template #default="{ row }"><span class="util-num util-num--actual">{{ formatPercent(row.actualUtilizationPct) }}</span></template>
              </el-table-column>
              <el-table-column width="120" align="right">
                <template #header>
                  <span
                    class="util-col-head"
                    title="当該設備で集計月内に実績があった最終日までの日別 (実績−計画) を、各指示の能率で工時換算して合算。"
                  >
                    操業度差異(H)
                  </span>
                </template>
                <template #default="{ row }"><span class="util-num" :class="{ 'util-num--negative': row.diffHours < 0 }">{{ formatHours(row.diffHours) }}</span></template>
              </el-table-column>
              <el-table-column label="差異操業度(%)" width="130" align="right">
                <template #default="{ row }"><span class="util-num" :class="{ 'util-num--negative': row.diffUtilizationPct < 0 }">{{ formatPercent(row.diffUtilizationPct) }}</span></template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Calendar, Goods, OfficeBuilding, Printer, Switch } from '@element-plus/icons-vue'
import {
  fetchLines,
  fetchSchedulingGrid,
  replanLineSequence,
  type ScheduleGridRow,
  type SchedulingGridResponse,
} from '@/api/aps'
import { fetchProcesses } from '@/api/master/processMaster'
import type { ProcessItem } from '@/types/master'

defineOptions({ name: 'WeldingPlanningList' })

type GanttListRow = ScheduleGridRow & {
  lineLabel: string
  line_id: number
  /** グリッド拡張時用（現行 API に無い場合もある） */
  product_cd?: string | null
}

/** 一覧再計算前の画面状態（DB 巻き戻しは行わない） */
interface PreReplanGridSnapshot {
  tableRows: GanttListRow[]
  tableGanttDates: string[]
  ganttRows: GanttListRow[]
  ganttDates: string[]
  lineCalendarHoursMap: Record<number, Record<string, number>>
  lineDefaultHoursMap: Record<number, number>
}

const preReplanGridSnapshot = ref<PreReplanGridSnapshot | null>(null)
const bulkReplanning = ref(false)

/** 再計算 API のクエリ用アンカー（DB の aps_line_replan_anchors があればサーバ側で優先） */
function formatYmdInJapan(d: Date): string {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Tokyo',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(d)
}

const replanFallbackAnchorDate = computed(() => formatYmdInJapan(new Date()))

function clonePreReplanSnapshot(): PreReplanGridSnapshot {
  return JSON.parse(
    JSON.stringify({
      tableRows: tableRows.value,
      tableGanttDates: tableGanttDates.value,
      ganttRows: ganttRows.value,
      ganttDates: ganttDates.value,
      lineCalendarHoursMap: lineCalendarHoursMap.value,
      lineDefaultHoursMap: lineDefaultHoursMap.value,
    }),
  ) as PreReplanGridSnapshot
}

function offsetDateIso(offsetDays: number): string {
  const d = new Date()
  d.setHours(0, 0, 0, 0)
  d.setDate(d.getDate() + offsetDays)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${dd}`
}

const dateRange = ref<[string, string]>([offsetDateIso(-1), offsetDateIso(30)])
/** 設備操業度タブ専用：集計月（検索期間とは独立） */
function formatYmInJapan(d = new Date()): string {
  return new Intl.DateTimeFormat('sv-SE', {
    timeZone: 'Asia/Tokyo',
    year: 'numeric',
    month: '2-digit',
  })
    .format(d)
    .slice(0, 7)
}
const utilizationMonth = ref<string>(formatYmInJapan())
/** 集計月の日次グリッド（fetchSchedulingGrid の dates / rows） */
const utilizationMonthDates = ref<string[]>([])
const utilizationMonthRows = ref<GanttListRow[]>([])
const utilizationLineCalendarMap = ref<Record<number, Record<string, number>>>({})
const utilizationLineDefaultHoursMap = ref<Record<number, number>>({})
const loadingUtilizationMonth = ref(false)
const selectedProcessCd = ref<string>('')
const processOptions = ref<ProcessItem[]>([])
const loadingProcesses = ref(false)
/** 一覧（表）用：工程内の全設備の全指示（日次集計は tableGanttDates の広い範囲） */
const tableRows = ref<GanttListRow[]>([])
/** 一覧（表）のみ：設備で絞込（null / undefined＝すべて） */
const tableFilterLineId = ref<number | null>(null)
/** 一覧（表）のみ：製品で絞込（空＝すべて。値は product_cd 優先、無ければ品名、無ければ id:） */
const tableFilterProductKey = ref<string>('')
/** 一覧（表）のみ：状態「生産済」行を表示（既定 OFF＝非表示） */
const tableShowStatusDone = ref(false)
/** 一覧（表）のみ：状態「準備中」行を表示（既定 ON） */
const tableShowStatusPending = ref(true)
/** 一覧（表）の実績・不良・残など日次マップの合計に使う日付列（検索期間より広い取得結果） */
const tableGanttDates = ref<string[]>([])
const loading = ref(false)
const searched = ref(false)
const activeResultTab = ref<'gantt' | 'table' | 'utilization'>('gantt')
const ganttDates = ref<string[]>([])
const ganttRows = ref<GanttListRow[]>([])
const lineCalendarHoursMap = ref<Record<number, Record<string, number>>>({})
const lineDefaultHoursMap = ref<Record<number, number>>({})

/** 一覧用 grid の明細取得範囲（サーバ負荷のため過大にしない） */
const TABLE_GRID_PAST_YEARS = 10
const TABLE_GRID_FUTURE_YEARS = 5

const tableGridRangeNote = ref('—')

function ymdFromLocalDate(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

/** YYYY-MM から暦月の [月初, 月末] ISO 日付 */
function monthRangeFromYm(ym: string): [string, string] | null {
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

/** 一覧（表）の日次明細を検索期間外まで含めて集計するための grid 用期間 */
function buildTableGridRange(): [string, string] {
  const n = new Date()
  n.setHours(0, 0, 0, 0)
  const start = new Date(n.getFullYear() - TABLE_GRID_PAST_YEARS, n.getMonth(), n.getDate())
  const end = new Date(n.getFullYear() + TABLE_GRID_FUTURE_YEARS, n.getMonth(), n.getDate())
  return [ymdFromLocalDate(start), ymdFromLocalDate(end)]
}

function flattenGridToRows(grid: SchedulingGridResponse, lineNameById: Map<number, string>): GanttListRow[] {
  const flat: GanttListRow[] = []
  for (const block of grid.blocks || []) {
    const label =
      lineNameById.get(block.line_id) ||
      String((block as { line_name?: string }).line_name || '').trim() ||
      block.line_code ||
      `ID ${block.line_id}`
    for (const r of block.rows || []) {
      flat.push({ ...r, lineLabel: label, line_id: block.line_id })
    }
  }
  return flat
}

/** 設備操業度：集計月の日次グリッドを取得（検索期間のガントとは独立） */
async function loadUtilizationMonthGrid() {
  const pc = (selectedProcessCd.value || '').trim()
  if (!pc) {
    utilizationMonthDates.value = []
    utilizationMonthRows.value = []
    utilizationLineCalendarMap.value = {}
    utilizationLineDefaultHoursMap.value = {}
    return
  }
  const range = monthRangeFromYm(utilizationMonth.value)
  if (!range) {
    utilizationMonthDates.value = []
    utilizationMonthRows.value = []
    utilizationLineCalendarMap.value = {}
    utilizationLineDefaultHoursMap.value = {}
    return
  }
  const [sd, ed] = range
  loadingUtilizationMonth.value = true
  try {
    const [grid, lines] = await Promise.all([
      fetchSchedulingGrid(sd, ed, undefined, pc),
      fetchLines(pc),
    ])
    utilizationMonthDates.value = Array.isArray(grid.dates) ? grid.dates : []
    const lineNameById = new Map<number, string>()
    for (const line of lines || []) {
      const name = String(line.line_name || '').trim()
      const code = String(line.line_code || '').trim()
      lineNameById.set(line.id, name || code || `ID ${line.id}`)
    }
    const flat = flattenGridToRows(grid, lineNameById)
    flat.sort(compareByLineThenOrder)
    utilizationMonthRows.value = flat
    const calendarMap: Record<number, Record<string, number>> = {}
    const defaultMap: Record<number, number> = {}
    for (const block of grid.blocks || []) {
      calendarMap[block.line_id] = block.calendar || {}
      defaultMap[block.line_id] = Number(block.default_work_hours ?? 0)
    }
    utilizationLineCalendarMap.value = calendarMap
    utilizationLineDefaultHoursMap.value = defaultMap
  } catch {
    utilizationMonthDates.value = []
    utilizationMonthRows.value = []
    utilizationLineCalendarMap.value = {}
    utilizationLineDefaultHoursMap.value = {}
  } finally {
    loadingUtilizationMonth.value = false
  }
}

const canSearch = computed(
  () =>
    !!(
      Array.isArray(dateRange.value) &&
      dateRange.value[0] &&
      dateRange.value[1] &&
      (selectedProcessCd.value || '').trim()
    ),
)

const displayRangeText = computed(() => {
  const [startDate, endDate] = dateRange.value || []
  if (!startDate || !endDate) return '—'
  return `${startDate} 〜 ${endDate}`
})

function tableProductRowKey(row: GanttListRow): string {
  const cd = (row.product_cd || '').trim()
  const name = (row.item_name || '').trim()
  return cd || name || `id:${row.id}`
}

const tableLineFilterOptions = computed(() => {
  const byId = new Map<number, string>()
  for (const r of tableRows.value) {
    if (!byId.has(r.line_id)) {
      byId.set(r.line_id, (r.lineLabel || '').trim() || `ID ${r.line_id}`)
    }
  }
  return [...byId.entries()]
    .sort((a, b) => a[1].localeCompare(b[1], 'ja'))
    .map(([id, label]) => ({ id, label }))
})

const tableProductFilterOptions = computed(() => {
  const labels = new Map<string, string>()
  for (const r of tableRows.value) {
    const key = tableProductRowKey(r)
    if (!labels.has(key)) {
      const cd = (r.product_cd || '').trim()
      const name = (r.item_name || '').trim()
      const label = cd && name ? `${name}（${cd}）` : name || cd || key
      labels.set(key, label)
    }
  }
  return [...labels.entries()]
    .sort((a, b) => a[1].localeCompare(b[1], 'ja'))
    .map(([value, label]) => ({ value, label }))
})

const filteredTableRows = computed(() => {
  const lineId = tableFilterLineId.value
  const prodKey = (tableFilterProductKey.value || '').trim()
  const showDone = tableShowStatusDone.value
  const showPending = tableShowStatusPending.value
  return tableRows.value.filter((row) => {
    if (lineId != null && row.line_id !== lineId) return false
    if (prodKey && tableProductRowKey(row) !== prodKey) return false
    const kind = tableStatusKind(row)
    if (kind === 'done' && !showDone) return false
    if (kind === 'pending' && !showPending) return false
    return true
  })
})

const tableTabFiltersActive = computed(
  () =>
    tableFilterLineId.value != null ||
    (tableFilterProductKey.value || '').trim() !== '' ||
    tableShowStatusDone.value ||
    !tableShowStatusPending.value,
)

const tableGroups = computed(() => {
  const groups: Array<{ lineLabel: string; rows: GanttListRow[] }> = []
  for (const row of filteredTableRows.value) {
    const lineLabel = row.lineLabel || `ID ${row.line_id}`
    const last = groups[groups.length - 1]
    if (!last || last.lineLabel !== lineLabel) {
      groups.push({ lineLabel, rows: [row] })
    } else {
      last.rows.push(row)
    }
  }
  return groups
})

const ganttGroups = computed(() => {
  const groups: Array<{
    lineLabel: string
    rows: GanttListRow[]
    plannedTotal: number
    actualTotal: number
    avgEfficiencyRate: number | null
  }> = []
  for (const row of ganttRows.value) {
    const lineLabel = (row.lineLabel || '').trim() || `ID ${row.line_id}`
    const last = groups[groups.length - 1]
    if (!last || last.lineLabel !== lineLabel) {
      groups.push({
        lineLabel,
        rows: [row],
        plannedTotal: Number(row.planned_process_qty ?? 0),
        actualTotal: Number(periodActualForRow(row) ?? 0),
        avgEfficiencyRate: null,
      })
    } else {
      last.rows.push(row)
      last.plannedTotal += Number(row.planned_process_qty ?? 0)
      last.actualTotal += Number(periodActualForRow(row) ?? 0)
    }
  }

  for (const group of groups) {
    let weightedSum = 0
    let weightedDenom = 0
    for (const row of group.rows) {
      const rate = Number(row.efficiency_rate ?? 0)
      const qty = Number(row.planned_process_qty ?? 0)
      if (!Number.isFinite(rate) || !Number.isFinite(qty) || rate <= 0 || qty <= 0) continue
      weightedSum += rate * qty
      weightedDenom += qty
    }
    group.avgEfficiencyRate = weightedDenom > 0 ? weightedSum / weightedDenom : null
  }
  return groups
})

/** 集計月の暦日すべて（計画・実績の合算・理論稼働の分母用。グリッド＝当該月全日） */
const utilizationMonthFullDates = computed(() =>
  [...utilizationMonthDates.value].sort((a, b) => a.localeCompare(b)),
)

/** 設備別：集計月内で「その日の実績合計が正になる」最終日（ISO）。月内に実績なしは null */
function lineLastActualDayInMonth(monthDates: string[], rows: GanttListRow[]): Map<number, string | null> {
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

const utilizationMonthLabelJp = computed(() => {
  const ym = (utilizationMonth.value || '').trim()
  const p = ym.match(/^(\d{4})-(\d{2})$/)
  if (!p) return '—'
  return `${Number(p[1])}年${Number(p[2])}月`
})

interface LineUtilizationRow {
  lineId: number
  lineLabel: string
  scheduleCount: number
  availableHours: number
  plannedQty: number
  actualQty: number
  plannedHours: number
  actualHours: number
  diffQty: number
  diffHours: number
  diffUtilizationPct: number
  planUtilizationPct: number
  actualUtilizationPct: number
}

const utilizationRows = computed<LineUtilizationRow[]>(() => {
  const monthDates = utilizationMonthFullDates.value
  if (monthDates.length === 0) return []

  const rows = utilizationMonthRows.value
  const lastActualByLine = lineLastActualDayInMonth(monthDates, rows)

  const map = new Map<number, LineUtilizationRow>()
  for (const row of rows) {
    const lineId = row.line_id
    const plannedQty = monthDates.reduce((sum, d) => sum + Number(row.daily?.[d] ?? 0), 0)
    const actualQty = monthDates.reduce((sum, d) => sum + Number(row.actual_daily?.[d] ?? 0), 0)
    const rate = Number(row.efficiency_rate ?? 0)
    const plannedHours = rate > 0 ? plannedQty / rate : 0
    const actualHours = rate > 0 ? actualQty / rate : 0
    const endDay = lastActualByLine.get(lineId)
    const diffDates =
      endDay == null || endDay === '' ? ([] as string[]) : monthDates.filter((d) => d <= endDay)
    const diffQtyRow = diffDates.reduce((sum, d) => {
      const p = Number(row.daily?.[d] ?? 0)
      const a = Number(row.actual_daily?.[d] ?? 0)
      return sum + (a - p)
    }, 0)
    const diffHoursRow = rate > 0 ? diffQtyRow / rate : 0
    const item = map.get(lineId) ?? {
      lineId,
      lineLabel: row.lineLabel || `ID ${lineId}`,
      scheduleCount: 0,
      availableHours: 0,
      plannedQty: 0,
      actualQty: 0,
      plannedHours: 0,
      actualHours: 0,
      diffQty: 0,
      diffHours: 0,
      diffUtilizationPct: 0,
      planUtilizationPct: 0,
      actualUtilizationPct: 0,
    }
    item.scheduleCount += 1
    item.plannedQty += plannedQty
    item.actualQty += actualQty
    item.plannedHours += plannedHours
    item.actualHours += actualHours
    item.diffQty += diffQtyRow
    item.diffHours += diffHoursRow
    map.set(lineId, item)
  }
  const result = Array.from(map.values())
  for (const r of result) {
    const calMap = utilizationLineCalendarMap.value[r.lineId] || {}
    const fallback = Number(utilizationLineDefaultHoursMap.value[r.lineId] ?? 0)
    const avail = monthDates.reduce((sum, d) => {
      const h = Number(calMap[d] ?? fallback)
      return sum + (Number.isFinite(h) ? h : 0)
    }, 0)
    r.availableHours = avail
    r.planUtilizationPct = avail > 0 ? (r.plannedHours / avail) * 100 : 0
    r.actualUtilizationPct = avail > 0 ? (r.actualHours / avail) * 100 : 0
    r.diffUtilizationPct = avail > 0 ? (r.diffHours / avail) * 100 : 0
  }
  result.sort((a, b) => a.lineLabel.localeCompare(b.lineLabel, 'ja'))
  return result
})

onMounted(() => {
  void loadProcessOptions()
})

watch([utilizationMonth, selectedProcessCd], () => {
  void loadUtilizationMonthGrid()
})

async function loadProcessOptions() {
  loadingProcesses.value = true
  try {
    const res = await fetchProcesses({ page: 1, pageSize: 5000 })
    const list = res.list ?? res.data?.list ?? []
    processOptions.value = Array.isArray(list) ? list : []
    const hasDefault = processOptions.value.some((p) => (p.process_cd || '').trim() === 'KT07')
    if (hasDefault) {
      selectedProcessCd.value = 'KT07'
    } else if (processOptions.value.length === 1) {
      selectedProcessCd.value = (processOptions.value[0].process_cd || '').trim()
    }
  } catch {
    processOptions.value = []
    ElMessage.error('工程一覧の取得に失敗しました')
  } finally {
    loadingProcesses.value = false
  }
}

/** 設備表示名 → 順位 → id の昇順（一覧・ガント共通） */
function compareByLineThenOrder(a: GanttListRow, b: GanttListRow): number {
  const lineCmp = (a.lineLabel || '').localeCompare(b.lineLabel || '', 'ja')
  if (lineCmp !== 0) return lineCmp
  const oa = a.order_no ?? 1_000_000 + a.id
  const ob = b.order_no ?? 1_000_000 + b.id
  if (oa !== ob) return oa - ob
  return a.id - b.id
}

function scheduleTableRowClassName({
  rowIndex,
}: {
  row: GanttListRow
  rowIndex: number
}): string {
  const parts: string[] = []
  if (rowIndex % 2 === 1) parts.push('schedule-row--alt')
  return parts.join(' ')
}

function formatNum(v: number | null | undefined): string {
  return Number(v ?? 0).toLocaleString()
}

function formatHours(v: number | null | undefined): string {
  const n = Number(v ?? 0)
  return Number.isFinite(n) ? n.toFixed(1) : '0.0'
}

function formatPercent(v: number | null | undefined): string {
  const n = Number(v ?? 0)
  if (!Number.isFinite(n)) return '0.0%'
  return `${n.toFixed(1)}%`
}

function escHtml(s: string): string {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

/** 日別セル値を数値化（文字列・欠損でも表示判定がブレないようにする） */
function ganttDayQty(v: unknown): number {
  const n = Number(v)
  return Number.isFinite(n) ? n : 0
}

function selectedProcessLabel(): string {
  const cd = (selectedProcessCd.value || '').trim()
  if (!cd) return '—'
  const p = processOptions.value.find((x) => (x.process_cd || '').trim() === cd)
  const nm = (p?.process_name || '').trim()
  return nm ? `${cd} — ${nm}` : cd
}

function buildUtilizationPrintHtml(): string {
  const title = '設備操業度（月次）'
  const printedAt = new Date().toLocaleString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
  const rowsHtml = utilizationRows.value
    .map((r) => {
      const negHours = r.diffHours < 0 ? 'neg' : ''
      const negPct = r.diffUtilizationPct < 0 ? 'neg' : ''
      return `<tr>
        <td class="left">${escHtml(r.lineLabel)}</td>
        <td class="num">${escHtml(String(r.scheduleCount))}</td>
        <td class="num">${escHtml(formatHours(r.availableHours))}</td>
        <td class="num">${escHtml(formatNum(r.plannedQty))}</td>
        <td class="num">${escHtml(formatNum(r.actualQty))}</td>
        <td class="num">${escHtml(formatHours(r.plannedHours))}</td>
        <td class="num">${escHtml(formatHours(r.actualHours))}</td>
        <td class="num">${escHtml(formatPercent(r.planUtilizationPct))}</td>
        <td class="num">${escHtml(formatPercent(r.actualUtilizationPct))}</td>
        <td class="num ${negHours}">${escHtml(formatHours(r.diffHours))}</td>
        <td class="num ${negPct}">${escHtml(formatPercent(r.diffUtilizationPct))}</td>
      </tr>`
    })
    .join('')

  return `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <title>${escHtml(title)}</title>
  <style>
    html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    body { margin: 16px; color: #0f172a; font: 12px/1.4 "Segoe UI", "Yu Gothic UI", Meiryo, sans-serif; }
    .hd { margin-bottom: 10px; }
    .tt { font-size: 18px; font-weight: 700; }
    .meta { margin-top: 4px; color: #475569; }
    table { width: 100%; border-collapse: collapse; table-layout: fixed; }
    th, td { border: 1px solid #cbd5e1; padding: 6px 8px; }
    th { background: #eff6ff; font-weight: 700; }
    .left { text-align: left; }
    .num { text-align: right; font-variant-numeric: tabular-nums; }
    .neg { color: #dc2626; font-weight: 700; }
    tbody tr:nth-child(odd) { background: #f8fafc; }
    @media print { @page { size: A4 landscape; margin: 10mm; } }
  </style>
</head>
<body>
  <div class="hd">
    <div class="tt">${escHtml(title)}</div>
    <div class="meta">集計月：<strong>${escHtml(utilizationMonthLabelJp.value)}</strong>（${escHtml(utilizationMonth.value || '—')}）　工程：${escHtml(selectedProcessLabel())}　印刷日時：${escHtml(printedAt)}</div>
  </div>
  <table>
    <thead>
      <tr>
        <th class="left">設備</th>
        <th class="num">製造指示数</th>
        <th class="num">理論稼働(H)</th>
        <th class="num">計画数</th>
        <th class="num">実績数</th>
        <th class="num">計画時間(H)</th>
        <th class="num">実績時間(H)</th>
        <th class="num">計画操業度</th>
        <th class="num">実績操業度</th>
        <th class="num">操業度差異(H)</th>
        <th class="num">差異操業度(%)</th>
      </tr>
    </thead>
    <tbody>${rowsHtml}</tbody>
  </table>
</body>
</html>`
}

function buildGanttPrintHtml(): string {
  const title = '溶接計画一覧（ガント日別）'
  const printedAt = new Date().toLocaleString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
  const dateCols = ganttDates.value
    .map((d) => `<th class="date-col">${escHtml(d.slice(5))}</th>`)
    .join('')
  const emptyDateCells = ganttDates.value.map(() => '<td></td>').join('')
  const rowsHtml = ganttGroups.value
    .map((group) => {
      const lineLabel = group.lineLabel
      const lineRows = group.rows
      const groupHeader = `<tr class="group-row">
        <td class="left line-col">${escHtml(lineLabel)}</td>
        <td></td>
        <td></td>
        <td class="num eff-col">${escHtml(formatGroupEfficiency(group.avgEfficiencyRate))}</td>
        <td class="num planned-col">${escHtml(formatNum(group.plannedTotal))}</td>
        <td class="num act-col">${escHtml(formatNum(group.actualTotal))}</td>
        ${emptyDateCells}
      </tr>`
      const body = lineRows
        .map((row) => {
          const cells = ganttDates.value
            .map((d) => {
              const p = ganttDayQty(row.daily?.[d])
              const a = ganttDayQty(row.actual_daily?.[d])
              const showRemain = shouldShowGanttRemain(row, d)
              const r = showRemain ? ganttDayQty(row.remaining_daily?.[d]) : 0
              if (p === 0 && a === 0 && r === 0) return '<td></td>'
              const chunks: string[] = []
              if (p !== 0) chunks.push(`${p}`)
              if (a !== 0) chunks.push(`${a}`)
              if (r !== 0) chunks.push(`${r}`)
              return `<td class="num cell-data">${escHtml(chunks.join(' / '))}</td>`
            })
            .join('')
          return `<tr>
            <td class="line-col"></td>
            <td class="num indent-col order-col">${escHtml(String(row.order_no ?? '—'))}</td>
            <td class="left name-col indent-col">${escHtml(row.item_name || '—')}</td>
            <td class="num eff-col">${escHtml(formatEfficiencyRatePiecesPerH(row.efficiency_rate))}</td>
            <td class="num indent-col planned-col">${escHtml(formatNum(row.planned_process_qty))}</td>
            <td class="num act-col">${escHtml(formatNum(periodActualForRow(row)))}</td>
            ${cells}
          </tr>`
        })
        .join('')
      return `<tbody class="group-block">${groupHeader}${body}</tbody>`
    })
    .join('')

  return `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <title>${escHtml(title)}</title>
  <style>
    html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    body { margin: 8px; color: #0f172a; font: 10px/1.35 "Segoe UI", "Yu Gothic UI", Meiryo, sans-serif; background: #f8fafc; }
    .hd { margin-bottom: 8px; padding: 8px 10px; border: 1px solid #dbe5f1; border-radius: 8px; background: linear-gradient(180deg, #f8fbff 0%, #eef5ff 100%); }
    .tt { font-size: 16px; font-weight: 800; color: #1e3a8a; }
    .meta { margin-top: 3px; color: #475569; font-size: 10px; }
    table { width: 100%; border-collapse: collapse; table-layout: fixed; }
    th, td { border: 1px solid #cbd5e1; padding: 3px 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    th { background: linear-gradient(180deg, #eaf3ff 0%, #dceafe 100%); font-weight: 800; color: #334155; }
    .left { text-align: left; }
    .num { text-align: right; font-variant-numeric: tabular-nums; font-family: Consolas, "Courier New", monospace; }
    .date-col { font-size: 9px; }
    .group-block { break-inside: avoid; page-break-inside: avoid; }
    .name-col { color: #0f172a; font-weight: 700; width: 110px; max-width: 110px; }
    .line-col { font-weight: 800; width: 80px; max-width: 80px; white-space: normal; }
    .order-col { width: calc(2ch + 10px); max-width: calc(2ch + 10px); }
    .eff-col { width: calc(6ch + 12px); max-width: calc(6ch + 12px); }
    .planned-col { width: calc(5ch + 20px); max-width: calc(5ch + 20px); }
    .act-col { width: calc(5ch + 20px); max-width: calc(5ch + 20px); }
    .indent-col { padding-left: 10px; }
    .cell-data { font-size: 9px; }
    .group-row td { background: #e2e8f0; color: #1e293b; font-weight: 800; text-align: left; border-top: 2px solid #94a3b8; }
    tbody tr:nth-child(odd) { background: #fcfdff; }
    tbody tr:nth-child(even) { background: #f7fbff; }
    @media print { @page { size: A3 landscape; margin: 8mm; } }
  </style>
</head>
<body>
  <div class="hd">
    <div class="tt">${escHtml(title)}</div>
    <div class="meta">期間：${escHtml(displayRangeText.value)}　工程：${escHtml(selectedProcessLabel())}　表示期間：${escHtml(displayRangeText.value)}　印刷日時：${escHtml(printedAt)}</div>
  </div>
  <table>
    <thead>
      <tr>
        <th class="left line-col">設備</th>
        <th class="num order-col">順位</th>
        <th class="left name-col">品名</th>
        <th class="num eff-col">能率</th>
        <th class="num planned-col">計画数</th>
        <th class="num act-col">実績数</th>
        ${dateCols}
      </tr>
    </thead>
    ${rowsHtml}
  </table>
</body>
</html>`
}

function handleGanttPrint() {
  if (ganttRows.value.length === 0 || ganttDates.value.length === 0) {
    ElMessage.warning('印刷対象のガントデータがありません')
    return
  }
  const w = window.open('', '_blank')
  if (!w) {
    ElMessage.error('ポップアップがブロックされました')
    return
  }
  w.document.write(buildGanttPrintHtml())
  w.document.close()
  w.onload = () => {
    w.print()
    setTimeout(() => w.close(), 400)
  }
}

/** 一覧（表）タブ：現在の絞込結果を A4 縦で印刷 */
function buildTableListPrintHtml(): string {
  const title = '溶接計画一覧（表・絞込結果）'
  const printedAt = new Date().toLocaleString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
  const lineId = tableFilterLineId.value
  const lineLabel =
    lineId != null
      ? tableLineFilterOptions.value.find((x) => x.id === lineId)?.label ?? `ID ${lineId}`
      : 'すべて'
  const pk = (tableFilterProductKey.value || '').trim()
  const productLabel = pk
    ? tableProductFilterOptions.value.find((x) => x.value === pk)?.label ?? pk
    : 'すべて'
  const statusLine = `生産済: ${tableShowStatusDone.value ? '表示' : '非表示'}　準備中: ${tableShowStatusPending.value ? '表示' : '非表示'}`

  const sectionsHtml = tableGroups.value
    .map((group) => {
      const body = group.rows
        .map((row) => {
          const span = effectiveScheduleDateSpan(row)
          return `<tr>
            <td class="num">${escHtml(String(row.order_no ?? '—'))}</td>
            <td class="left name">${escHtml(row.item_name || '—')}</td>
            <td class="cen">${escHtml(span.start || '—')}</td>
            <td class="cen">${escHtml(span.end || '—')}</td>
            <td class="num">${escHtml(formatNum(row.planned_process_qty))}</td>
            <td class="num">${escHtml(formatNum(tableActual(row)))}</td>
            <td class="num">${escHtml(formatNum(tableDefect(row)))}</td>
            <td class="num">${escHtml(formatNum(tableUpstreamDefect(row)))}</td>
            <td class="num">${escHtml(formatNum(tableRemaining(row)))}</td>
            <td class="num">${escHtml(tableProgress(row))}</td>
            <td class="cen">${escHtml(tableStatusLabel(row))}</td>
          </tr>`
        })
        .join('')
      return `<section class="print-sec">
        <div class="grp-title">${escHtml(group.lineLabel)}</div>
        <table>
          <thead>
            <tr>
              <th class="num">順位</th>
              <th class="left name">製品名</th>
              <th class="cen">開始</th>
              <th class="cen">終了</th>
              <th class="num">計画</th>
              <th class="num">実績</th>
              <th class="num">不良</th>
              <th class="num">前工程不良</th>
              <th class="num">残</th>
              <th class="num">進捗</th>
              <th class="cen">状態</th>
            </tr>
          </thead>
          <tbody>${body}</tbody>
        </table>
      </section>`
    })
    .join('')

  return `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <title>${escHtml(title)}</title>
  <style>
    html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    body {
      margin: 0;
      padding: 10px 12px 14px;
      color: #0f172a;
      font: 9.5px/1.35 "Segoe UI", "Yu Gothic UI", Meiryo, sans-serif;
      background: #fff;
    }
    .hd {
      margin-bottom: 10px;
      padding: 10px 12px;
      border: 1px solid #dbe5f1;
      border-radius: 8px;
      background: linear-gradient(180deg, #f8fbff 0%, #eef5ff 100%);
    }
    .tt { font-size: 14px; font-weight: 800; color: #1e3a8a; }
    .meta { margin-top: 4px; color: #475569; font-size: 8.5px; line-height: 1.55; }
    .meta strong { color: #334155; font-weight: 700; }
    .print-sec { margin-bottom: 12px; break-inside: avoid; page-break-inside: avoid; }
    .grp-title {
      font-size: 10px;
      font-weight: 800;
      color: #1e293b;
      margin: 0 0 4px 2px;
      padding: 3px 0;
      border-bottom: 2px solid #94a3b8;
    }
    table { width: 100%; border-collapse: collapse; table-layout: fixed; }
    th, td {
      border: 1px solid #cbd5e1;
      padding: 3px 4px;
      word-wrap: break-word;
      overflow-wrap: anywhere;
    }
    th {
      background: linear-gradient(180deg, #eaf3ff 0%, #dceafe 100%);
      font-weight: 800;
      color: #334155;
      font-size: 8.5px;
    }
    tbody tr:nth-child(odd) { background: #fcfdff; }
    tbody tr:nth-child(even) { background: #f7fbff; }
    .left { text-align: left; }
    .num { text-align: right; font-variant-numeric: tabular-nums; font-family: Consolas, "Courier New", monospace; }
    .cen { text-align: center; }
    th.num, td.num { width: 6.5%; }
    th.cen, td.cen { width: 8%; }
    th.name, td.name { width: 18%; }
    @media print {
      @page { size: A4 portrait; margin: 10mm; }
      body { padding: 0; }
    }
  </style>
</head>
<body>
  <div class="hd">
    <div class="tt">${escHtml(title)}</div>
    <div class="meta">
      期間：<strong>${escHtml(displayRangeText.value)}</strong>
      　工程：<strong>${escHtml(selectedProcessLabel())}</strong>
     
      絞込：<strong>設備 ${escHtml(lineLabel)}</strong> ／ <strong>製品 ${escHtml(productLabel)}</strong>
      　${escHtml(statusLine)}<br />
      件数：<strong>${tableGroups.value.reduce((n, g) => n + g.rows.length, 0)}</strong> 件
      　印刷日時：${escHtml(printedAt)}
    </div>
  </div>
  ${sectionsHtml}
</body>
</html>`
}

function handleTableListPrint() {
  if (filteredTableRows.value.length === 0) {
    ElMessage.warning('印刷対象の行がありません（絞込みを確認してください）')
    return
  }
  const w = window.open('', '_blank')
  if (!w) {
    ElMessage.error('ポップアップがブロックされました')
    return
  }
  w.document.write(buildTableListPrintHtml())
  w.document.close()
  w.onload = () => {
    w.print()
    setTimeout(() => w.close(), 400)
  }
}

function handleUtilizationPrint() {
  if (utilizationRows.value.length === 0) {
    ElMessage.warning('印刷対象データがありません')
    return
  }
  const w = window.open('', '_blank')
  if (!w) {
    ElMessage.error('ポップアップがブロックされました')
    return
  }
  w.document.write(buildUtilizationPrintHtml())
  w.document.close()
  w.onload = () => {
    w.print()
    setTimeout(() => w.close(), 400)
  }
}

/** 日次グリッド行からセルに値がある暦日（スライスと明細の表示根拠と揃える） */
function isoDatesWithGridActivity(gr: ScheduleGridRow): string[] {
  const keys = new Set<string>()
  const maps: (Record<string, number> | undefined)[] = [
    gr.daily,
    gr.actual_daily,
    gr.defect_daily,
    gr.upstream_defect_daily,
    gr.remaining_daily,
  ]
  for (const mp of maps) {
    if (!mp) continue
    for (const [d, v] of Object.entries(mp)) {
      if (Number(v || 0) !== 0) keys.add(d)
    }
  }
  return [...keys].sort()
}

/**
 * 一覧の開始・終了および状態判定用。
 * production_schedules の期日が日次明細・スライスとずれる場合があるため、非ゼロ日の min/max を優先する。
 */
function effectiveScheduleDateSpan(row: GanttListRow): { start: string | null; end: string | null } {
  const dates = isoDatesWithGridActivity(row)
  if (dates.length === 0) {
    return { start: row.start_date ?? null, end: row.end_date ?? null }
  }
  return { start: dates[0] ?? null, end: dates[dates.length - 1] ?? null }
}

function tableActual(row: GanttListRow): number {
  return periodActualForRow(row, tableGanttDates.value)
}

/** 不良：schedule_details.defect_qty の期間合計（API の defect_qty_sum） */
function tableDefect(row: GanttListRow): number {
  const v = row.defect_qty_sum
  if (v != null && Number.isFinite(Number(v))) return Math.max(0, Number(v))
  return periodDefectForRow(row, tableGanttDates.value)
}

/** 前工程不良：WeldingPlanning と同様 aps_batch_plans.upstream_defect_qty の当指示合計 */
function tableUpstreamDefect(row: GanttListRow): number {
  const v = row.upstream_defect_qty_total
  if (v != null && Number.isFinite(Number(v))) return Math.max(0, Number(v))
  return periodUpstreamDefectForRow(row, tableGanttDates.value)
}

function tableRemaining(row: GanttListRow): number {
  const remainByDaily = periodRemainingForRow(row, tableGanttDates.value)
  if (remainByDaily > 0) return remainByDaily
  const planned = Number(row.planned_process_qty ?? 0)
  const remain = planned - tableActual(row)
  return remain > 0 ? remain : 0
}

function tableProgress(row: GanttListRow): string {
  const planned = Number(row.planned_process_qty ?? 0)
  if (planned <= 0) return '0%'
  const pct = (tableActual(row) / planned) * 100
  return `${Math.round(Math.max(0, Math.min(999, pct)))}%`
}

function parseLocalDay(v: string | undefined | null): Date | null {
  if (v == null || v === '') return null
  const part = String(v).trim().slice(0, 10)
  const m = part.match(/^(\d{4})-(\d{1,2})-(\d{1,2})/)
  if (!m) return null
  const y = parseInt(m[1], 10)
  const mo = parseInt(m[2], 10) - 1
  const d = parseInt(m[3], 10)
  const dt = new Date(y, mo, d)
  if (Number.isNaN(dt.getTime()) || dt.getFullYear() !== y || dt.getMonth() !== mo || dt.getDate() !== d) {
    return null
  }
  return dt
}

function todayLocalStart(): Date {
  const n = new Date()
  return new Date(n.getFullYear(), n.getMonth(), n.getDate())
}

function tableStatusKind(row: GanttListRow): 'done' | 'ongoing' | 'pending' {
  const today = todayLocalStart()
  const span = effectiveScheduleDateSpan(row)
  const start = parseLocalDay(span.start)
  const end = parseLocalDay(span.end)
  if (end && end < today) return 'done'
  if (start && end && start <= today && today <= end) return 'ongoing'
  return 'pending'
}

function tableStatusLabel(row: GanttListRow): string {
  const map: Record<'done' | 'ongoing' | 'pending', string> = {
    done: '生産済',
    ongoing: '生産中',
    pending: '準備中',
  }
  return map[tableStatusKind(row)]
}

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

function onSearchClick() {
  void loadSchedules()
}

async function loadSchedules(options?: { clearReplanSnapshot?: boolean }) {
  const clearReplanSnapshot = options?.clearReplanSnapshot !== false
  if (!canSearch.value) {
    ElMessage.warning('期間と工程を選択してください')
    return
  }
  const [sd, ed] = dateRange.value || []
  if (!sd || !ed) {
    ElMessage.warning('期間を入力してください')
    return
  }
  if (sd > ed) {
    ElMessage.warning('期間の開始日は終了日以前にしてください')
    return
  }
  loading.value = true
  searched.value = true
  tableFilterLineId.value = null
  tableFilterProductKey.value = ''
  tableShowStatusDone.value = false
  tableShowStatusPending.value = true
  ganttDates.value = []
  ganttRows.value = []
  tableRows.value = []
  tableGanttDates.value = []
  lineCalendarHoursMap.value = {}
  lineDefaultHoursMap.value = {}
  try {
    const pc = (selectedProcessCd.value || '').trim()
    const [grid, lines] = await Promise.all([
      fetchSchedulingGrid(sd, ed, undefined, pc),
      fetchLines(pc || undefined),
    ])
    ganttDates.value = Array.isArray(grid.dates) ? grid.dates : []
    const lineNameById = new Map<number, string>()
    for (const line of lines || []) {
      const name = String(line.line_name || '').trim()
      const code = String(line.line_code || '').trim()
      lineNameById.set(line.id, name || code || `ID ${line.id}`)
    }
    const calendarMap: Record<number, Record<string, number>> = {}
    const defaultMap: Record<number, number> = {}
    for (const block of grid.blocks || []) {
      calendarMap[block.line_id] = block.calendar || {}
      defaultMap[block.line_id] = Number(block.default_work_hours ?? 0)
    }
    lineCalendarHoursMap.value = calendarMap
    lineDefaultHoursMap.value = defaultMap

    const flat = flattenGridToRows(grid, lineNameById)
    flat.sort(compareByLineThenOrder)
    ganttRows.value = flat

    const [wideStart, wideEnd] = buildTableGridRange()
    tableGridRangeNote.value = `${wideStart} 〜 ${wideEnd}`
    try {
      const wideGrid = await fetchSchedulingGrid(wideStart, wideEnd, undefined, pc)
      tableGanttDates.value = Array.isArray(wideGrid.dates) ? wideGrid.dates : []
      const wideFlat = flattenGridToRows(wideGrid, lineNameById)
      wideFlat.sort(compareByLineThenOrder)
      tableRows.value = wideFlat
    } catch {
      tableGanttDates.value = [...ganttDates.value]
      tableRows.value = [...flat]
    }
    if (clearReplanSnapshot) preReplanGridSnapshot.value = null
    await loadUtilizationMonthGrid()
  } catch (e: unknown) {
    tableRows.value = []
    tableGanttDates.value = []
    ganttDates.value = []
    ganttRows.value = []
    lineCalendarHoursMap.value = {}
    lineDefaultHoursMap.value = {}
    ElMessage.error(String((e as { message?: string })?.message || e))
  } finally {
    loading.value = false
  }
}

function restorePreReplanGrid() {
  const snap = preReplanGridSnapshot.value
  if (!snap) {
    ElMessage.warning('戻せるスナップショットがありません')
    return
  }
  const legacy = snap as PreReplanGridSnapshot & { rows?: GanttListRow[] }
  const restoredTableRows = snap.tableRows ?? legacy.rows ?? snap.ganttRows
  const restoredTableDates = snap.tableGanttDates ?? snap.ganttDates
  tableRows.value = JSON.parse(JSON.stringify(restoredTableRows)) as GanttListRow[]
  tableGanttDates.value = [...restoredTableDates]
  ganttRows.value = JSON.parse(JSON.stringify(snap.ganttRows)) as GanttListRow[]
  ganttDates.value = [...snap.ganttDates]
  lineCalendarHoursMap.value = JSON.parse(JSON.stringify(snap.lineCalendarHoursMap))
  lineDefaultHoursMap.value = JSON.parse(JSON.stringify(snap.lineDefaultHoursMap))
  tableFilterLineId.value = null
  tableFilterProductKey.value = ''
  tableShowStatusDone.value = false
  tableShowStatusPending.value = true
  void loadUtilizationMonthGrid()
  ElMessage.success('再計算前に取得した一覧表示に戻しました（サーバの計画は変わりません）')
}

async function replanAllLinesForProcess() {
  if (!canSearch.value) {
    ElMessage.warning('期間と工程を選択してください')
    return
  }
  const pc = (selectedProcessCd.value || '').trim()
  if (!pc) return
  try {
    await ElMessageBox.confirm(
      `工程「${pc}」の全設備をラインコード順に順次再計算します。実行しますか？`,
      '全設備ライン順で再計算',
      { type: 'warning', confirmButtonText: '実行', cancelButtonText: 'キャンセル' },
    )
  } catch {
    return
  }
  bulkReplanning.value = true
  try {
    const rawLines = await fetchLines(pc)
    const lines = (Array.isArray(rawLines) ? rawLines : []).filter((l) => l.is_active !== false)
    lines.sort((a, b) => (a.line_code || '').localeCompare(b.line_code || '', 'ja'))
    if (lines.length === 0) {
      ElMessage.warning('対象工程に有効な設備がありません')
      return
    }
    if (tableRows.value.length > 0 || ganttRows.value.length > 0) {
      preReplanGridSnapshot.value = clonePreReplanSnapshot()
    }
    const anchor = replanFallbackAnchorDate.value
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i]
      await replanLineSequence(line.id, anchor)
    }
    await loadSchedules({ clearReplanSnapshot: false })
    ElMessage.success(`全 ${lines.length} 設備の順次再計算が完了しました`)
  } catch (e: unknown) {
    ElMessage.error(formatApiError(e) || '再計算に失敗しました')
    try {
      await loadSchedules({ clearReplanSnapshot: false })
    } catch {
      /* 一覧取得失敗は無視 */
    }
  } finally {
    bulkReplanning.value = false
  }
}

function formatEfficiencyRatePiecesPerH(v: number | null | undefined): string {
  if (v == null || Number.isNaN(Number(v))) return '—'
  const n = Number(v)
  const s = n % 1 === 0 ? String(Math.round(n)) : n.toFixed(1)
  return `${s}本/H`
}

function formatGroupEfficiency(v: number | null | undefined): string {
  if (v == null || !Number.isFinite(Number(v))) return '—'
  return `${Number(v).toFixed(1)}本/H`
}

const todayIso = computed(() => new Date().toISOString().slice(0, 10))

function isWeekend(d: string): boolean {
  const day = new Date(d).getDay()
  return day === 0 || day === 6
}

function isToday(d: string): boolean {
  return d === todayIso.value
}

function getWeekday(d: string): string {
  const wd = ['日', '月', '火', '水', '木', '金', '土']
  return wd[new Date(d).getDay()]
}

/** 列日付が本日より前（当日は含めない） */
function isPastGanttDate(d: string): boolean {
  return d < todayIso.value
}

/** 当日に実績がある列、または日付が本日より前の列：ガントセルに淡色背景 */
function ganttCellHasSoftTone(row: ScheduleGridRow, d: string): boolean {
  if (ganttDayQty(row.actual_daily?.[d]) !== 0) return true
  if (isPastGanttDate(d)) return true
  return false
}

/**
 * 残の表示ルール：
 * - 当日実績あり → 残も表示対象（残>0 かつトグルON のとき）
 * - 当日実績なし → 本日以降の日付では残を出さない／過去日のみ残を出す（計画未着手・遅れの把握用）
 */
function shouldShowGanttRemain(row: ScheduleGridRow, d: string): boolean {
  const r = ganttDayQty(row.remaining_daily?.[d])
  if (r === 0) return false
  const a = ganttDayQty(row.actual_daily?.[d])
  if (a !== 0) return true
  return isPastGanttDate(d)
}

function ganttCellHasAnyMarker(row: ScheduleGridRow, d: string): boolean {
  const p = ganttDayQty(row.daily?.[d])
  const a = ganttDayQty(row.actual_daily?.[d])
  if (p !== 0 || a !== 0) return true
  return shouldShowGanttRemain(row, d)
}

function ganttCellTitle(row: ScheduleGridRow, d: string): string {
  const planned = ganttDayQty(row.daily?.[d])
  const actual = ganttDayQty(row.actual_daily?.[d])
  const remain = ganttDayQty(row.remaining_daily?.[d])
  if (!ganttCellHasAnyMarker(row, d)) return ''
  const parts: string[] = []
  if (planned !== 0) parts.push(`計画 ${planned}`)
  if (actual !== 0) parts.push(`実績 ${actual}`)
  if (shouldShowGanttRemain(row, d)) parts.push(`残 ${remain}`)
  if (parts.length === 0) return ''
  return `${row.item_name}: ${parts.join(' / ')}`
}

function periodActualForRow(row: ScheduleGridRow, datesOverride?: string[]): number {
  const m = row.actual_daily || {}
  const dates1 =
    datesOverride && datesOverride.length > 0
      ? datesOverride
      : ganttDates.value.length > 0
        ? ganttDates.value
        : Object.keys(m)
  return dates1.reduce((sum, d) => sum + Number(m[d] || 0), 0)
}

/** ガント表示期間内の不良合計（defect_daily の期間合計） */
function periodDefectForRow(row: ScheduleGridRow, datesOverride?: string[]): number {
  const m = row.defect_daily || {}
  const dates1 =
    datesOverride && datesOverride.length > 0
      ? datesOverride
      : ganttDates.value.length > 0
        ? ganttDates.value
        : Object.keys(m)
  return dates1.reduce((sum, d) => sum + Number(m[d] || 0), 0)
}

/** ガント表示期間内の前工程不良合計（upstream_defect_daily の期間合計） */
function periodUpstreamDefectForRow(row: ScheduleGridRow, datesOverride?: string[]): number {
  const m = row.upstream_defect_daily || {}
  const dates1 =
    datesOverride && datesOverride.length > 0
      ? datesOverride
      : ganttDates.value.length > 0
        ? ganttDates.value
        : Object.keys(m)
  return dates1.reduce((sum, d) => sum + Number(m[d] || 0), 0)
}

/** ガント表示期間内の残合計（remaining_daily と一致） */
function periodRemainingForRow(row: ScheduleGridRow, datesOverride?: string[]): number {
  const m = row.remaining_daily || {}
  const dates1 =
    datesOverride && datesOverride.length > 0
      ? datesOverride
      : ganttDates.value.length > 0
        ? ganttDates.value
        : Object.keys(m)
  return dates1.reduce((sum, d) => sum + Number(m[d] || 0), 0)
}
</script>

<style scoped>
.welding-plan-list-page {
  --font-sans: inherit;
  --font-mono: inherit;
  --fs-xs: 10.5px;
  --fs-s: 11.5px;
  --fs-base: 13px;
  --c-text-h: #0b1220;
  --c-text-m: #445063;
  --c-text-s: #6b778a;
  --c-border: #dbe3ee;
  --c-border-l: #e9eef6;
  --c-surface: #ffffff;
  --c-bg: #f4f7fb;
  --c-accent: #3b82f6;
  --c-accent-2: #7c3aed;
  --c-success: #10b981;
  --c-warn: #f59e0b;
  /* 左 sticky 列幅（設備列は .list-gantt-table 内で指定） */
  --gl-order: 44px;
  --gl-name: 110px;
  --gl-eff: 70px;
  --gl-plan: 56px;
  --gl-act: var(--gl-plan);

  padding: 10px 12px 12px;
  background:
    radial-gradient(circle at 10% -20%, rgba(59, 130, 246, 0.1), transparent 35%),
    radial-gradient(circle at 110% -30%, rgba(16, 185, 129, 0.08), transparent 30%),
    #f3f6fb;
  min-height: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-family: inherit;
  font-size: var(--fs-base);
  color: var(--c-text-m);
  -webkit-font-smoothing: antialiased;
}

.plan-hd {
  margin-bottom: 0;
  padding: 4px 2px 2px;
}
.plan-hd-title {
  margin: 0;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: 0.2px;
  line-height: 1.1;
  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.55);
}
.plan-hd-icon {
  width: 26px;
  height: 26px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
  box-shadow:
    0 6px 14px rgba(37, 99, 235, 0.24),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
}
.plan-hd-icon svg {
  width: 15px;
  height: 15px;
  fill: #fff;
}
.plan-hd-sub {
  margin: 5px 0 0 34px;
  color: var(--c-text-s);
  font-size: var(--fs-s);
  line-height: 1.45;
  max-width: 980px;
}
.plan-hd-sub strong {
  font-weight: 600;
  color: #4f5f79;
}

.plan-card {
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(3px);
  padding: 10px 12px;
  margin-bottom: 0;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 8px 20px rgba(15, 23, 42, 0.04);
}

.filter-card {
  padding: 7px 10px;
  border-color: rgba(191, 219, 254, 0.75);
  background:
    linear-gradient(135deg, rgba(239, 246, 255, 0.82) 0%, rgba(250, 245, 255, 0.76) 100%),
    rgba(255, 255, 255, 0.95);
  box-shadow:
    0 10px 22px rgba(37, 99, 235, 0.07),
    inset 0 1px 0 rgba(255, 255, 255, 0.74);
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 2px;
  margin-right: 6px;
}
.filter-form :deep(.el-form-item__label) {
  font-size: 12px;
  font-weight: 600;
  color: #1e3a8a;
  padding-right: 5px;
  line-height: 30px;
}
.filter-form :deep(.el-input__wrapper),
.filter-form :deep(.el-select__wrapper) {
  border-radius: 10px;
  min-height: 32px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
  transition: box-shadow 0.18s ease, border-color 0.18s ease;
}
.filter-form :deep(.el-input__wrapper:hover),
.filter-form :deep(.el-select__wrapper:hover) {
  box-shadow: 0 4px 10px rgba(37, 99, 235, 0.12);
}
.filter-form :deep(.el-input__wrapper.is-focus),
.filter-form :deep(.el-select__wrapper.is-focused) {
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.18);
}
.filter-form :deep(.el-button) {
  border-radius: 999px;
  border: none;
  color: #fff;
  font-weight: 700;
  letter-spacing: 0.2px;
  background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
  box-shadow:
    0 8px 18px rgba(37, 99, 235, 0.28),
    0 2px 4px rgba(124, 58, 237, 0.22),
    inset 0 1px 0 rgba(255, 255, 255, 0.34);
  padding-left: 14px;
  padding-right: 14px;
}

.welding-replan-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid rgba(191, 219, 254, 0.55);
}
.welding-replan-toolbar__primary {
  border-radius: 999px;
  font-weight: 700;
}
.welding-replan-toolbar__note {
  flex: 1 1 240px;
  font-size: 12px;
  line-height: 1.45;
  color: #475569;
}

.result-card {
  padding: 10px 10px 12px;
}

.result-tabs :deep(.el-tabs__content) {
  padding-top: 8px;
}
.result-tabs :deep(.el-tabs__header) {
  margin-bottom: 0;
}
.result-tabs :deep(.el-tabs__item) {
  font-weight: 800;
  font-size: var(--fs-base);
  color: #334155;
}
.result-tabs :deep(.el-tabs__active-bar) {
  height: 3px;
  border-radius: 3px;
  background: linear-gradient(90deg, #2563eb 0%, #7c3aed 100%);
}

.gantt-legend-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px 12px;
  margin-bottom: 8px;
  padding: 6px 10px;
  font-size: var(--fs-s);
  color: var(--c-text-m);
  background: linear-gradient(180deg, #f8fbff 0%, #f2f7ff 100%);
  border-radius: 10px;
  border: 1px solid var(--c-border-l);
}
.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  white-space: nowrap;
  font-weight: 700;
}
.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 4px;
  display: inline-block;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.18);
}
.legend-dot--plan {
  background: linear-gradient(135deg, #60a5fa, #2563eb);
}
.legend-dot--actual {
  background: linear-gradient(135deg, #10b981, #059669);
}
.legend-dot--remain {
  background: linear-gradient(135deg, #a78bfa, #7c3aed);
}
.gantt-range-note {
  margin-left: auto;
  font-size: var(--fs-xs);
  font-family: var(--font-mono);
  color: var(--c-text-s);
}
.gantt-print-btn {
  margin-left: 12px;
  flex-shrink: 0;
  border-radius: 999px !important;
  padding: 0 16px 0 14px !important;
  min-height: 30px !important;
  font-weight: 700 !important;
  font-size: 12.5px !important;
  letter-spacing: 0.04em;
  color: #334155 !important;
  border: 1px solid rgba(148, 163, 184, 0.55) !important;
  background: linear-gradient(165deg, #ffffff 0%, #f8fafc 42%, #eef2f7 100%) !important;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.06),
    0 6px 16px -6px rgba(37, 99, 235, 0.18),
    inset 0 1px 0 rgba(255, 255, 255, 0.92);
  transition:
    transform 0.18s ease,
    box-shadow 0.22s ease,
    border-color 0.2s ease,
    color 0.2s ease,
    background 0.2s ease;
}

.gantt-print-btn:hover:not(.is-disabled) {
  color: #1e3a8a !important;
  border-color: rgba(59, 130, 246, 0.5) !important;
  background: linear-gradient(165deg, #ffffff 0%, #f0f7ff 45%, #e8effc 100%) !important;
  box-shadow:
    0 2px 4px rgba(15, 23, 42, 0.07),
    0 10px 24px -8px rgba(37, 99, 235, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 1);
  transform: translateY(-1px);
}

.gantt-print-btn:active:not(.is-disabled) {
  transform: translateY(0);
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.08),
    inset 0 1px 2px rgba(15, 23, 42, 0.06);
}

.gantt-print-btn.is-disabled,
.gantt-print-btn.is-disabled:hover {
  opacity: 0.48 !important;
  transform: none !important;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04) !important;
}

.gantt-print-btn :deep(.el-icon) {
  font-size: 15px;
  color: #64748b;
  transition: color 0.2s ease;
}

.gantt-print-btn:hover:not(.is-disabled) :deep(.el-icon) {
  color: #2563eb;
}

.plan-sec-hd {
  font-size: var(--fs-base);
  font-weight: 700;
  color: var(--c-text-h);
  margin: 0 0 12px;
  padding-left: 9px;
  border-left: 3px solid var(--c-accent);
  display: flex;
  align-items: center;
  gap: 8px;
  line-height: 1.3;
}
.plan-sec-hd--inner {
  margin-top: 4px;
}

.table-range-note {
  margin: -2px 0 12px;
  padding-left: 9px;
  font-size: var(--fs-xs);
  color: var(--c-text-s);
  line-height: 1.5;
  max-width: 960px;
}
.table-range-note strong {
  font-weight: 700;
  color: #475569;
}

.table-filter-hint {
  font-size: var(--fs-xs);
  font-weight: 500;
  color: var(--c-text-s);
}

/* ── 一覧（表）絞込ツールバー（カード＋同行レイアウト） ── */
.table-filter-toolbar-card {
  margin: 0 0 14px;
  padding: 0;
  border-radius: 14px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.92) 0%, rgba(248, 250, 252, 0.98) 48%, rgba(241, 245, 249, 0.95) 100%);
  border: 1px solid rgba(148, 163, 184, 0.35);
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 10px 28px -8px rgba(15, 23, 42, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.table-tab-filter-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px 16px;
  padding: 12px 14px 12px 12px;
}

.table-filter-field {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.table-filter-field__lead {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  flex-shrink: 0;
  padding: 4px 0 4px 4px;
}

.table-filter-field__icon {
  font-size: 16px;
  color: var(--c-accent);
  opacity: 0.92;
}

.table-filter-field__label {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: #475569;
  text-transform: uppercase;
  white-space: nowrap;
}

.table-tab-filter-select {
  width: min(220px, 100%);
}

.table-tab-filter-select--product {
  width: min(260px, 100%);
}

.table-filter-toolbar-divider {
  width: 1px;
  height: 32px;
  flex-shrink: 0;
  align-self: center;
  border-radius: 1px;
  background: linear-gradient(180deg, transparent, rgba(148, 163, 184, 0.45) 15%, rgba(148, 163, 184, 0.45) 85%, transparent);
}

.table-filter-status-cluster {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
  min-width: 0;
}

.table-filter-status-cluster__title {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: #475569;
  text-transform: uppercase;
  white-space: nowrap;
  margin-right: 2px;
}

.table-filter-status-cluster__title-icon {
  font-size: 15px;
  color: var(--c-accent-2);
  opacity: 0.9;
}

.table-filter-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 5px 12px 5px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(226, 232, 240, 0.95);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
  transition:
    border-color 0.18s ease,
    box-shadow 0.18s ease,
    background 0.18s ease;
}

.table-filter-pill:hover {
  border-color: rgba(148, 163, 184, 0.55);
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.06);
}

.table-filter-pill--on {
  background: linear-gradient(135deg, rgba(219, 234, 254, 0.65) 0%, rgba(237, 233, 254, 0.55) 100%);
  border-color: rgba(59, 130, 246, 0.35);
  box-shadow:
    0 1px 2px rgba(37, 99, 235, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.65);
}

.table-filter-pill__text {
  font-size: 12px;
  font-weight: 700;
  color: #334155;
  white-space: nowrap;
}

.table-filter-toolbar-card :deep(.el-select) {
  --el-select-border-color-hover: rgba(59, 130, 246, 0.45);
}

.table-filter-toolbar-card :deep(.el-select .el-select__wrapper) {
  min-height: 36px;
  border-radius: 10px;
  padding-left: 10px;
  padding-right: 8px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(203, 213, 225, 0.85);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  transition:
    border-color 0.16s ease,
    box-shadow 0.16s ease;
}

.table-filter-toolbar-card :deep(.el-select .el-select__wrapper.is-hovering),
.table-filter-toolbar-card :deep(.el-select .el-select__wrapper.is-focused) {
  border-color: rgba(59, 130, 246, 0.55);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.12);
}

.table-filter-toolbar-card :deep(.el-select .el-select__placeholder) {
  color: #94a3b8;
  font-weight: 500;
}

.table-filter-switch :deep(.el-switch__core) {
  border: 1px solid rgba(203, 213, 225, 0.9);
}

.table-filter-switch.is-checked :deep(.el-switch__core) {
  border-color: rgba(59, 130, 246, 0.45);
}

.table-filter-bar-spacer {
  flex: 1 1 32px;
  min-width: 4px;
}

.table-filter-print-btn {
  flex-shrink: 0;
  border-radius: 10px;
  font-weight: 700;
  box-shadow: 0 1px 3px rgba(37, 99, 235, 0.12);
}

.table-filter-print-btn:not(:disabled):hover {
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.18);
}

.plan-sec-badge {
  font-size: var(--fs-xs);
  font-weight: 600;
  background: linear-gradient(90deg, var(--c-accent) 0%, var(--c-accent-2) 100%);
  color: #fff;
  padding: 1px 7px;
  border-radius: 10px;
  line-height: 18px;
}

.line-cell {
  font-size: var(--fs-s);
  font-weight: 700;
  color: var(--c-text-h);
  letter-spacing: 0.01em;
}

.product-name-cell {
  color: var(--c-accent);
  font-weight: 600;
}

.qty-cell {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-weight: 800;
  font-size: var(--fs-s);
  color: var(--c-text-h);
}
.qty-cell--actual {
  color: #059669;
}

.qty-cell--defect {
  color: #c2410c;
}

.qty-cell--upstream {
  color: #6d28d9;
}

.date-cell {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-size: var(--fs-s);
  font-weight: 700;
  color: var(--c-text-m);
}

.schedule-empty :deep(.el-empty__description) {
  color: var(--c-text-s);
  font-size: var(--fs-s);
}

.util-note {
  margin: 6px 0 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.util-sec-hd {
  margin-bottom: 10px;
  flex-wrap: wrap;
  row-gap: 8px;
}
/* 集計月：カード風コントロール */
.util-month-surface {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  margin-left: 6px;
  padding: 6px 12px 6px 8px;
  border-radius: 14px;
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.95) 0%,
    rgba(248, 250, 252, 0.98) 45%,
    rgba(241, 245, 249, 0.92) 100%
  );
  border: 1px solid rgba(148, 163, 184, 0.38);
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.05),
    0 10px 24px -12px rgba(30, 64, 175, 0.18),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}
.util-month-surface:not(.util-month-surface--disabled):hover {
  border-color: rgba(59, 130, 246, 0.45);
  box-shadow:
    0 2px 4px rgba(15, 23, 42, 0.06),
    0 14px 32px -10px rgba(37, 99, 235, 0.22),
    inset 0 1px 0 rgba(255, 255, 255, 0.95);
  transform: translateY(-1px);
}
.util-month-surface--disabled {
  opacity: 0.52;
  pointer-events: none;
  filter: saturate(0.85);
}
.util-month-surface__icon {
  flex-shrink: 0;
  font-size: 22px;
  padding: 4px;
  border-radius: 10px;
  color: #2563eb;
  background: linear-gradient(145deg, rgba(219, 234, 254, 0.9) 0%, rgba(237, 233, 254, 0.75) 100%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.75);
}
.util-month-surface__main {
  min-width: 0;
}
.util-month-surface__main--row {
  display: inline-flex;
  flex-direction: row;
  align-items: center;
  gap: 10px;
}
.util-month-surface__kicker {
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.06em;
  color: #475569;
  line-height: 1;
  white-space: nowrap;
}
.util-month-picker {
  width: min(172px, 46vw);
}
.util-month-picker :deep(.el-input__wrapper) {
  border-radius: 10px;
  min-height: 32px;
  padding-left: 10px;
  padding-right: 8px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(203, 213, 225, 0.65);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}
.util-month-picker :deep(.el-input__wrapper:hover) {
  border-color: rgba(59, 130, 246, 0.4);
}
.util-month-picker :deep(.el-input__wrapper.is-focus) {
  border-color: rgba(59, 130, 246, 0.55);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.14);
}
.util-month-picker :deep(.el-input__inner) {
  font-size: 13px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  color: #0f172a;
  letter-spacing: 0.02em;
}
.util-month-picker :deep(.el-input__prefix),
.util-month-picker :deep(.el-input__suffix) {
  color: #64748b;
}
.util-month-picker :deep(.el-input__suffix .el-icon) {
  font-size: 14px;
}
.util-hd-spacer {
  margin-left: auto;
}
.util-print-btn {
  border-radius: 9px;
  font-weight: 700;
  padding: 6px 12px;
}
.util-note-chip {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  color: #475569;
  background: linear-gradient(180deg, #f8fbff 0%, #edf3fb 100%);
  border: 1px solid #d7e2f0;
}
.util-note-chip--formula {
  color: #1d4ed8;
  background: linear-gradient(180deg, #eef4ff 0%, #e0ebff 100%);
  border-color: #c7d8ff;
}
.util-table-wrap {
  position: relative;
  border-radius: 16px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: linear-gradient(165deg, rgba(255, 255, 255, 0.97) 0%, rgba(248, 250, 252, 0.99) 40%, rgba(241, 245, 249, 0.96) 100%);
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 16px 40px -20px rgba(30, 64, 175, 0.22),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
  overflow: hidden;
}
.util-table-wrap::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  pointer-events: none;
  background: radial-gradient(80% 50% at 0% 0%, rgba(59, 130, 246, 0.06), transparent 55%);
  z-index: 0;
}
.util-table-wrap :deep(.el-table) {
  position: relative;
  z-index: 1;
  --el-table-border-color: rgba(226, 232, 240, 0.95);
  --el-table-header-bg-color: transparent;
  background: transparent;
}
.util-table--modern :deep(.el-table__inner-wrapper) {
  border-radius: 0 0 15px 15px;
}
.util-table--modern :deep(.el-table__header-wrapper th.el-table__cell) {
  background: linear-gradient(180deg, #f0f6ff 0%, #e2ecfb 100%) !important;
  color: #0f172a !important;
  font-weight: 800 !important;
  font-size: 11px !important;
  letter-spacing: 0.04em !important;
  border-bottom: 1px solid rgba(148, 163, 184, 0.45) !important;
  padding: 10px 10px !important;
  box-shadow: inset 0 -1px 0 rgba(255, 255, 255, 0.65);
}
.util-table--modern :deep(.el-table__body td.el-table__cell) {
  padding: 9px 11px !important;
  font-size: 12px !important;
  color: #334155 !important;
  border-color: rgba(241, 245, 249, 0.98) !important;
  background: rgba(255, 255, 255, 0.55) !important;
  transition: background 0.15s ease, color 0.15s ease;
}
.util-table--modern :deep(.el-table__body tr.el-table__row--striped td.el-table__cell) {
  background: rgba(248, 250, 252, 0.92) !important;
}
.util-table--modern :deep(.el-table__body tr:hover > td.el-table__cell) {
  background: linear-gradient(90deg, rgba(219, 234, 254, 0.55) 0%, rgba(237, 233, 254, 0.35) 100%) !important;
}
.util-table--modern :deep(.el-table__body tr.el-table__row--striped:hover > td.el-table__cell) {
  background: linear-gradient(90deg, rgba(191, 219, 254, 0.5) 0%, rgba(221, 214, 254, 0.35) 100%) !important;
}
.util-table--modern :deep(.el-table__body td.el-table__cell:first-child) {
  font-weight: 800;
  color: #1e293b !important;
}
.util-table--modern :deep(.el-table__body .el-table__row:last-child td.el-table__cell) {
  border-bottom: none;
}
.util-table--modern :deep(.el-table__border-bottom-patch) {
  display: none;
}
.util-num {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-weight: 800;
  color: #0f172a;
}
.util-num--actual {
  color: #047857;
}
.util-num--negative {
  color: #dc2626;
}

/* 一覧（表）：ガントと揃えた浅色・区切り・ヘッダー */
.schedule-table-wrap {
  border-radius: 12px;
  border: 1px solid var(--c-border-l);
  overflow: hidden;
  background: linear-gradient(180deg, #f5f9ff 0%, #fafcfe 55%, #f8fafc 100%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.85);
}
.schedule-table-group-list {
  display: grid;
  gap: 10px;
}
.schedule-table-group {
  padding-top: 0;
}
.schedule-group-title {
  padding: 9px 12px;
  font-size: var(--fs-s);
  font-weight: 800;
  letter-spacing: 0.02em;
  color: var(--c-text-h);
  background: linear-gradient(180deg, #edf3fb 0%, #e6eef9 100%);
  border-bottom: 1px solid #d4deeb;
}

.schedule-list-table {
  width: 100%;
  font-size: var(--fs-s);
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
  --el-table-header-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-border-color: #e2e8f0;
  --el-table-row-hover-bg-color: #e8f0fe;
}

.nest-table--polish {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 12px 32px -24px rgba(15, 23, 42, 0.25);
  --el-table-border-color: color-mix(in srgb, var(--el-border-color) 88%, var(--el-color-primary));
}

.schedule-list-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.schedule-list-table :deep(.el-table__header-wrapper th.el-table__cell) {
  background: linear-gradient(180deg, var(--el-fill-color-lighter) 0%, var(--el-fill-color-blank) 100%) !important;
  color: var(--el-text-color-primary) !important;
  font-weight: 700;
  font-size: var(--fs-s);
  letter-spacing: 0.04em;
  border-bottom: 1px solid var(--el-border-color-lighter) !important;
  padding: 8px 10px;
}

.schedule-list-table :deep(.el-table__body td.el-table__cell) {
  padding: 7px 10px;
  border-color: #e2e8f0 !important;
  color: #334155;
  background: #fafcfe !important;
}

.schedule-list-table :deep(.el-table__body tr.schedule-row--alt > td.el-table__cell) {
  background: #f3f6fb !important;
}

.schedule-list-table :deep(.el-table__body tr:hover > td.el-table__cell) {
  background: color-mix(in srgb, var(--el-color-primary) 4%, var(--el-fill-color-blank)) !important;
}

.schedule-list-table :deep(.el-table__body tr.schedule-row--alt:hover > td.el-table__cell) {
  background: #dbe7fd !important;
}

.status-lamp-cell {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex-wrap: nowrap;
}
.status-lamp-dot {
  display: inline-block;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow:
    0 0 0 1px rgba(0, 0, 0, 0.1) inset,
    0 1px 2px rgba(0, 0, 0, 0.06);
}
.status-lamp-dot--done {
  background: var(--el-text-color-placeholder);
}
.status-lamp-dot--ongoing {
  background: var(--el-color-success);
}
.status-lamp-dot--pending {
  background: var(--el-color-warning);
}
.status-lamp-label {
  font-size: var(--fs-s);
  color: var(--el-text-color-regular);
  font-weight: 500;
}

/* ── Gantt（日別）：对齐 Scheduling.vue 表格风格 ── */
.list-gantt-scroll {
  max-height: 620px;
  overflow: auto;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #fff;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.list-gantt-table {
  --gl-line: 80px;
  --gl-name: 110px;
  --gl-plan: 56px;
  --gl-act: var(--gl-plan);
  table-layout: fixed;
  width: max-content;
  min-width: 100%;
  border-collapse: collapse;
  font-size: var(--fs-s);
  line-height: 1.35;
  color: var(--c-text-m);
}

.list-gantt-table th,
.list-gantt-table td {
  border: 1px solid #e6edf5;
  padding: 3px 5px;
  white-space: nowrap;
  box-sizing: border-box;
}

.list-gantt-table thead th {
  position: sticky;
  top: 0;
  z-index: 3;
  background: linear-gradient(180deg, #f8fbff 0%, #eef4fb 100%);
  font-weight: 700;
  color: var(--c-text-m);
  box-shadow: 0 1px 0 #dbe5f1;
}

.list-gantt-table thead th.gantt-sticky-eff,
.list-gantt-table thead th.gantt-sticky-planned,
.list-gantt-table thead th.gantt-sticky-actual {
  text-align: right;
}

.list-gantt-table tbody tr.gantt-row--base td.gantt-cell,
.list-gantt-table tbody tr.gantt-row--alt td.gantt-cell {
  background: #fff;
}

.list-gantt-table tbody td {
  color: var(--c-text-h);
  font-weight: 400;
}

.list-gantt-table tbody tr.gantt-row--alt td {
  background: #fcfdff;
}

.list-gantt-table tbody tr:hover td {
  background: #f1f7ff;
}

/* 実績あり or 過去日の日別セル：極めて薄いグレー（行の白指定より優先） */
.list-gantt-table tbody tr.gantt-row--base td.gantt-cell.gantt-cell--tone,
.list-gantt-table tbody tr.gantt-row--alt td.gantt-cell.gantt-cell--tone {
  background-color: #f5f5f5;
}

.list-gantt-table tbody tr:hover td.gantt-cell.gantt-cell--tone {
  background-color: #e8ecf2;
}

.list-gantt-table tbody tr.gantt-row--group-start td {
  border-top: 2px solid #bfdbfe;
}

.gantt-group-row td {
  background: #e2e8f0;
  color: var(--c-text-h);
  font-weight: 700;
  border-top: 2px solid #94a3b8;
}

/* グループ行：列クラス（能率・計画・実績は右寄せ）を上書きしない */
.gantt-group-row .gantt-sticky-line,
.gantt-group-row .gantt-sticky-name {
  text-align: left;
}

.gantt-group-row .gantt-sticky-order {
  text-align: center;
}

.gantt-group-row .gantt-sticky-eff,
.gantt-group-row .gantt-sticky-planned,
.gantt-group-row .gantt-sticky-actual {
  text-align: right;
}

.list-gantt-table tbody tr.gantt-group-row .gantt-sticky {
  background: #e2e8f0 !important;
}

.list-gantt-table tbody tr.gantt-group-row:hover .gantt-sticky {
  background: #d8dee8 !important;
}

.gantt-group-cell {
  vertical-align: middle;
}

.gantt-group-line {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.25;
  font-weight: 800;
}

.gantt-group-num {
  font-variant-numeric: tabular-nums;
  font-family: var(--font-mono);
  font-weight: 700;
}

.gantt-group-date-cell {
  background: #e2e8f0;
  padding: 0;
}

.gantt-sticky {
  position: sticky;
  left: 0;
  background: #fff;
  z-index: 2;
}

.list-gantt-table thead .gantt-sticky {
  z-index: 4;
}

.gantt-sticky-line {
  left: 0;
  width: var(--gl-line);
  min-width: var(--gl-line);
  max-width: var(--gl-line);
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 500;
  color: var(--c-text-h);
}

.gantt-line-empty {
  color: transparent;
}

.gantt-sticky-order {
  left: var(--gl-line);
  width: var(--gl-order);
  min-width: var(--gl-order);
  max-width: var(--gl-order);
  text-align: center;
}

.gantt-sticky-name {
  left: calc(var(--gl-line) + var(--gl-order));
  width: var(--gl-name);
  min-width: var(--gl-name);
  max-width: var(--gl-name);
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--c-text-h);
  font-weight: 400;
}

.gantt-sticky-eff {
  left: calc(var(--gl-line) + var(--gl-order) + var(--gl-name));
  width: var(--gl-eff);
  min-width: var(--gl-eff);
  max-width: var(--gl-eff);
  text-align: right;
  color: var(--c-text-h);
  font-weight: 400;
}

.gantt-sticky-planned {
  left: calc(var(--gl-line) + var(--gl-order) + var(--gl-name) + var(--gl-eff));
  width: var(--gl-plan);
  min-width: var(--gl-plan);
  max-width: var(--gl-plan);
  text-align: right;
  color: var(--c-text-h);
  font-weight: 400;
}

.gantt-sticky-actual {
  left: calc(var(--gl-line) + var(--gl-order) + var(--gl-name) + var(--gl-eff) + var(--gl-plan));
  width: var(--gl-act);
  min-width: var(--gl-act);
  max-width: var(--gl-act);
  text-align: right;
  color: var(--c-text-h);
  font-weight: 400;
}

.gantt-name {
  font-weight: 400;
  color: var(--c-text-h);
}

.gantt-date-col {
  min-width: 54px;
  width: 54px;
}

.gantt-date-text {
  font-size: var(--fs-xs);
  font-weight: 650;
}

.gantt-wd-text {
  font-size: var(--fs-xs);
  color: var(--c-text-s);
}

.list-gantt-table thead .gantt-date-col.is-weekend .gantt-date-text,
.list-gantt-table thead .gantt-date-col.is-weekend .gantt-wd-text {
  color: #dc2626;
}

.list-gantt-table thead .gantt-date-col.is-today {
  background: linear-gradient(180deg, #fff3d4 0%, #ffeab0 100%);
}

.gantt-cell {
  width: 54px;
  min-width: 54px;
  max-width: 54px;
  text-align: left;
  padding: 2px 4px;
  vertical-align: middle;
}

.gantt-cell-markers {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  gap: 2px;
  min-height: 12px;
  width: 100%;
}

.gantt-seg {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  line-height: 1.15;
  max-width: 100%;
}

.gantt-seg-val {
  font-size: var(--fs-xs);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  font-family: var(--font-mono);
  color: var(--c-text-h);
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}

.gantt-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 0 0 1px rgba(15, 23, 42, 0.12);
}

.gantt-dot--plan {
  background: linear-gradient(135deg, #60a5fa, #2563eb);
}

.gantt-dot--actual {
  background: linear-gradient(135deg, #10b981, #059669);
}

.gantt-dot--remain {
  background: linear-gradient(135deg, #a78bfa, #7c3aed);
}

.list-gantt-table tbody tr:hover .gantt-sticky {
  background: #f1f7ff !important;
}
</style>
