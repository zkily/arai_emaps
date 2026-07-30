<template>
  <div class="inventory-projection-page">
    <!-- ツールバー -->
    <el-card class="toolbar-card" shadow="never">
      <div class="toolbar">
        <div class="toolbar-left">
          <span class="page-title">月末在庫予測</span>
          <el-popover placement="bottom-start" :width="560" trigger="click">
            <template #reference>
              <button class="help-button" type="button" aria-label="計算ルールを表示">?</button>
            </template>
            <div class="help-content">
              <div class="help-title">計算・表示ルール</div>
              <p>
                基準日以前は実績在庫、翌日以降は「繰越 + 生産数量 −
                下流工程生産」で予測します（倉庫は出荷を差し引き）。
              </p>
              <p>
                社内メッキ在庫・検査在庫は、製品ルート上の前工程在庫の合計です。
                倉庫在庫は社内倉庫在庫＋検査在庫です（外注倉庫は含めず、社内倉庫ルート製品のみ）。
                予測区間の出庫は社内倉庫出荷（内示）のみ差し引きます。
                外注メッキ在庫（予測）は「繰越＋外注溶接生産＋成型次工程移動（外注メッキ）−外注メッキ生産＋前日在庫」です。
                社内倉庫出荷／外注倉庫出荷は、それぞれルートに社内倉庫／外注倉庫を持つ製品の内示合計です。
              </p>
              <p>
                生産数量は工程別の実績最終日以前は実績、翌日以降は計画（手動修正優先）を採用します。
                当日より後の日付は、実績データがあっても実績 0 として扱います。
              </p>
              <p>
                計画行はダブルクリックで修正できます。成型・社内／外注メッキの次工程移動、および成型の次工程使用は親行をクリックすると内訳を開閉します。
              </p>
              <div v-if="branchSummary" class="help-meta">{{ branchSummary }}</div>
              <div v-if="cutoffSummary" class="help-meta">実績最終日: {{ cutoffSummary }}</div>
            </div>
          </el-popover>
          <el-tag v-if="summary" size="small" type="info">
            対象製品 {{ summary.product_count }} 件
          </el-tag>
        </div>
        <div class="toolbar-right">
          <span class="label">対象月</span>
          <el-date-picker
            v-model="targetMonth"
            type="month"
            format="YYYY-MM"
            value-format="YYYY-MM"
            :clearable="false"
            style="width: 130px"
          />
          <span class="label">基準日</span>
          <el-date-picker
            v-model="baseDate"
            type="date"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            :clearable="false"
            style="width: 150px"
          />
          <el-button type="primary" :loading="loading" @click="load(true)">再計算</el-button>
        </div>
      </div>
    </el-card>

    <!-- KPI カード -->
    <div v-if="summary" class="kpi-row">
      <div
        v-for="g in summary.groups"
        :key="g.key"
        class="kpi-card"
        :class="{ negative: g.month_end < 0 }"
        :style="{ '--group-color': GROUP_COLORS[g.key] || '#409eff' }"
        @click="openDetail(g)"
      >
        <div class="kpi-accent"></div>
        <div class="kpi-name">{{ g.name }}</div>
        <div class="kpi-value">
          {{ formatQty(g.month_end) }}
          <span class="kpi-unit">本</span>
        </div>
        <div class="kpi-sub">
          <span>月末予測</span>
          <span v-if="g.days_of_supply != null" :class="{ warn: g.days_of_supply < 3 }">
            在庫日数 {{ g.days_of_supply }}日
          </span>
          <span v-else>在庫日数 —</span>
        </div>
      </div>
    </div>

    <!-- 推移チャート -->
    <el-card v-loading="loading" class="chart-card" shadow="never">
      <template #header>
        <div class="card-header">
          <div class="card-title-wrap">
            <span class="card-title">工程別在庫推移（日別）</span>
            <el-popover placement="bottom" :width="330" trigger="click">
              <template #reference>
                <button class="help-button small" type="button" aria-label="グラフ説明を表示">
                  ?
                </button>
              </template>
              実線は日別在庫、青い網掛け範囲は予測期間です。
              <span v-if="summary">予測開始日: {{ summary.projection_start }}</span>
            </el-popover>
          </div>
          <span class="header-chip">全工程</span>
        </div>
      </template>
      <div ref="chartRef" class="chart-container"></div>
    </el-card>

    <!-- 在庫マトリクス（日別 / 月別） -->
    <el-card v-loading="loading || monthlyLoading" class="matrix-card" shadow="never">
      <template #header>
        <div class="card-header">
          <div class="card-title-wrap">
            <span class="card-title">在庫マトリクス</span>
            <el-popover placement="bottom" :width="430" trigger="click">
              <template #reference>
                <button class="help-button small" type="button" aria-label="マトリクス説明を表示">
                  ?
                </button>
              </template>
              <div class="help-content compact">
                <p>日別：対象月の日次推移を表示</p>
                <p>月別：対象月を含む直近 {{ MONTHLY_RANGE }} か月の月末在庫／月合計を表示</p>
                <p>工程行をダブルクリック：製品別明細を表示</p>
                <p>日別の計画行をダブルクリック：日別計画を手動修正</p>
                <p>次工程移動／使用の親行をクリック：内訳を開閉</p>
                <p>行頭のチェック：下の折れ線グラフに追加／削除</p>
              </div>
            </el-popover>
          </div>
          <div class="matrix-legend">
            <span>
              <i class="legend-dot inventory"></i>
              在庫
            </span>
            <span>
              <i class="legend-dot plan"></i>
              計画
            </span>
            <span>
              <i class="legend-dot actual"></i>
              実績
            </span>
            <span>
              <i class="legend-dot next"></i>
              次工程
            </span>
          </div>
        </div>
      </template>

      <el-tabs v-model="matrixTab" class="matrix-tabs" @tab-change="onMatrixTabChange">
        <el-tab-pane label="日別在庫マトリクス" name="daily" />
        <el-tab-pane label="月別在庫マトリクス" name="monthly" />
      </el-tabs>

      <!-- 日別 -->
      <el-table
        v-if="matrixTab === 'daily' && summary"
        :data="matrixRows"
        border
        size="small"
        :max-height="560"
        :row-class-name="matrixRowClass"
        @row-click="onMatrixRowClick"
        @row-dblclick="onMatrixRowDblClick"
      >
        <el-table-column prop="name" label="工程" width="250" fixed="left">
          <template #default="{ row }">
            <div class="matrix-name-cell">
              <el-checkbox
                v-if="isChartSelectable(row)"
                :model-value="isMatrixRowSelected(row)"
                class="chart-row-checkbox"
                title="折れ線グラフに表示"
                @click.stop
                @change="toggleMatrixChartRow(row)"
              />
              <span v-else class="checkbox-placeholder"></span>
              <span
                :class="{
                  'process-header': row.metric === 'header',
                  'process-metric': row.metric !== 'header' && row.key !== '__demand__',
                  'process-link':
                    row.metric === 'header' ||
                    row.metric === 'next_usage_parent' ||
                    row.metric === 'next_consume_parent',
                  'next-parent-label':
                    row.metric === 'next_usage_parent' || row.metric === 'next_consume_parent',
                  'next-child-label':
                    row.metric === 'next_usage_child' || row.metric === 'next_consume_child',
                }"
              >
                <span
                  v-if="row.metric === 'next_usage_parent' || row.metric === 'next_consume_parent'"
                  class="expand-icon"
                >
                  {{ row.expanded ? '▼' : '▶' }}
                </span>
                {{ row.name }}
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="合計" width="100" align="right" fixed="left">
          <template #default="{ row }">
            <span
              v-if="showsRowTotal(row)"
              class="row-total"
              :class="{
                negative: matrixRowTotal(row) < 0,
                'metric-plan': row.metric === 'plan',
                'metric-actual': row.metric === 'actual',
                'metric-next':
                  row.metric === 'next_usage' ||
                  row.metric === 'next_usage_parent' ||
                  row.metric === 'next_usage_child' ||
                  row.metric === 'next_consume_parent' ||
                  row.metric === 'next_consume_child' ||
                  row.metric === 'outsourced_shipment',
              }"
            >
              {{ formatQty(matrixRowTotal(row)) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column
          v-for="ds in summary.dates"
          :key="ds"
          :label="dayLabel(ds)"
          :min-width="72"
          align="right"
        >
          <template #header>
            <span :class="{ 'projected-header': isProjected(ds) }">{{ dayLabel(ds) }}</span>
          </template>
          <template #default="{ row }">
            <span
              v-if="row.metric !== 'header'"
              :class="{
                projected: isProjected(ds) && row.metric === 'inventory',
                negative: (row.daily[ds] ?? 0) < 0,
                'metric-plan': row.metric === 'plan',
                'metric-actual': row.metric === 'actual',
                'metric-next':
                  row.metric === 'next_usage' ||
                  row.metric === 'next_usage_parent' ||
                  row.metric === 'next_usage_child' ||
                  row.metric === 'next_consume_parent' ||
                  row.metric === 'next_consume_child' ||
                  row.metric === 'outsourced_shipment',
                'plan-overridden': row.metric === 'plan' && row.overrides?.[ds] != null,
              }"
            >
              {{ formatQty(row.daily[ds] ?? 0) }}
            </span>
          </template>
        </el-table-column>
      </el-table>

      <!-- 月別 -->
      <el-table
        v-else-if="matrixTab === 'monthly' && monthlyMonths.length"
        :data="monthlyMatrixRows"
        border
        size="small"
        :max-height="560"
        :row-class-name="matrixRowClass"
        @row-click="onMatrixRowClick"
        @row-dblclick="onMonthlyMatrixRowDblClick"
      >
        <el-table-column prop="name" label="工程" width="250" fixed="left">
          <template #default="{ row }">
            <div class="matrix-name-cell">
              <el-checkbox
                v-if="isChartSelectable(row)"
                :model-value="isMatrixRowSelected(row)"
                class="chart-row-checkbox"
                title="折れ線グラフに表示"
                @click.stop
                @change="toggleMatrixChartRow(row)"
              />
              <span v-else class="checkbox-placeholder"></span>
              <span
                :class="{
                  'process-header': row.metric === 'header',
                  'process-metric': row.metric !== 'header' && row.key !== '__demand__',
                  'process-link':
                    row.metric === 'header' ||
                    row.metric === 'next_usage_parent' ||
                    row.metric === 'next_consume_parent',
                  'next-parent-label':
                    row.metric === 'next_usage_parent' || row.metric === 'next_consume_parent',
                  'next-child-label':
                    row.metric === 'next_usage_child' || row.metric === 'next_consume_child',
                }"
              >
                <span
                  v-if="row.metric === 'next_usage_parent' || row.metric === 'next_consume_parent'"
                  class="expand-icon"
                >
                  {{ row.expanded ? '▼' : '▶' }}
                </span>
                {{ row.name }}
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="合計" width="100" align="right" fixed="left">
          <template #default="{ row }">
            <span
              v-if="showsRowTotal(row)"
              class="row-total"
              :class="{
                negative: matrixRowTotal(row) < 0,
                'metric-plan': row.metric === 'plan',
                'metric-actual': row.metric === 'actual',
                'metric-next':
                  row.metric === 'next_usage' ||
                  row.metric === 'next_usage_parent' ||
                  row.metric === 'next_usage_child' ||
                  row.metric === 'next_consume_parent' ||
                  row.metric === 'next_consume_child' ||
                  row.metric === 'outsourced_shipment',
              }"
            >
              {{ formatQty(matrixRowTotal(row)) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column
          v-for="ym in monthlyMonths"
          :key="ym"
          :label="monthLabel(ym)"
          :min-width="110"
          align="right"
        >
          <template #header>
            <span :class="{ 'projected-header': ym === targetMonth }">{{ monthLabel(ym) }}</span>
          </template>
          <template #default="{ row }">
            <span
              v-if="row.metric !== 'header'"
              :class="{
                projected: ym === targetMonth && row.metric === 'inventory',
                negative: (row.daily[ym] ?? 0) < 0,
                'metric-plan': row.metric === 'plan',
                'metric-actual': row.metric === 'actual',
                'metric-next':
                  row.metric === 'next_usage' ||
                  row.metric === 'next_usage_parent' ||
                  row.metric === 'next_usage_child' ||
                  row.metric === 'next_consume_parent' ||
                  row.metric === 'next_consume_child' ||
                  row.metric === 'outsourced_shipment',
                'plan-overridden': row.metric === 'plan' && row.overrides?.[ym] != null,
              }"
            >
              {{ formatQty(row.daily[ym] ?? 0) }}
            </span>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-else-if="!loading && !monthlyLoading" description="データがありません" />

      <div v-if="summary || monthlyMonths.length" class="matrix-chart-panel">
        <div class="matrix-chart-toolbar">
          <div>
            <div class="matrix-chart-title">
              {{ matrixTab === 'monthly' ? '選択行の月別推移' : '選択行の日別推移' }}
            </div>
            <div class="matrix-chart-subtitle">
              行頭のチェックで比較するデータを選択（最大
              {{ MATRIX_CHART_MAX_SERIES }} 行）／単位：千本
              <template v-if="matrixTab === 'monthly'">
                ／在庫は月末値、計画・実績・次工程は月合計
              </template>
            </div>
          </div>
          <div class="matrix-chart-actions">
            <el-tag type="primary" effect="plain">{{ selectedMatrixRows.length }} 行選択中</el-tag>
            <el-button
              size="small"
              :disabled="selectedMatrixRows.length === 0"
              @click="clearMatrixChartRows"
            >
              選択解除
            </el-button>
          </div>
        </div>
        <div
          v-if="selectedMatrixRows.length"
          ref="matrixChartRef"
          class="matrix-chart-container"
        ></div>
        <el-empty
          v-else
          :image-size="58"
          description="マトリクスの行を選択すると折れ線グラフを表示します"
        />
      </div>
    </el-card>

    <!-- 製品別明細ダイアログ -->
    <el-dialog
      v-model="detailVisible"
      :title="`${detailGroupName} — 製品別在庫推移`"
      width="90%"
      top="5vh"
    >
      <el-table v-loading="detailLoading" :data="detailRows" border size="small" :max-height="560">
        <el-table-column prop="product_cd" label="品番" width="130" fixed="left" />
        <el-table-column
          prop="product_name"
          label="品名"
          width="160"
          fixed="left"
          show-overflow-tooltip
        />
        <el-table-column label="次工程" width="110" fixed="left">
          <template #default="{ row }">
            {{ nextProcessLabel(row) }}
          </template>
        </el-table-column>
        <el-table-column label="月末予測" width="100" align="right" fixed="left">
          <template #default="{ row }">
            <span :class="{ negative: row.month_end < 0 }">{{ formatQty(row.month_end) }}</span>
          </template>
        </el-table-column>
        <el-table-column
          v-for="ds in detailDates"
          :key="ds"
          :label="dayLabel(ds)"
          :min-width="72"
          align="right"
        >
          <template #default="{ row }">
            <span :class="{ projected: isProjected(ds), negative: (row.by_date[ds] ?? 0) < 0 }">
              {{ formatQty(row.by_date[ds] ?? 0) }}
            </span>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 計画合計 手動修正ダイアログ -->
    <el-dialog
      v-model="planEditVisible"
      :title="`${planEditGroupName}計画 — 日別合計の手動修正`"
      width="680px"
      top="5vh"
    >
      <div class="plan-edit-hint">
        手動値は当日の生計画構成比で製品別に比例配分されます。修正はこの工程の計画のみに適用され、他工程（下流を含む）の計画は自動計画のままです。
        実績最終日以前の日は実績が採用されるため手動値は反映されません。生計画合計が 0
        の日は比例配分できないため手動値は無効です。 本画面専用の修正で、production_summarys
        は変更しません。
      </div>
      <el-table :data="planEditRows" border size="small" :max-height="480">
        <el-table-column label="日付" width="110">
          <template #default="{ row }">
            <span :class="{ 'projected-header': isProjected(row.ds) }">{{ row.ds.slice(5) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="自動計画" width="110" align="right">
          <template #default="{ row }">
            {{ formatQty(row.auto) }}
          </template>
        </el-table-column>
        <el-table-column label="手動値" width="170" align="center">
          <template #default="{ row }">
            <el-input-number
              v-model="row.manual"
              :min="0"
              :step="100"
              :controls="false"
              size="small"
              placeholder="—"
              style="width: 140px"
            />
          </template>
        </el-table-column>
        <el-table-column label="採用値" align="right">
          <template #default="{ row }">
            <span :class="{ 'plan-overridden': row.manual != null && row.auto > 0 }">
              {{ formatQty(row.manual != null && row.auto > 0 ? row.manual : row.auto) }}
            </span>
            <el-tag v-if="row.manual != null && row.auto <= 0" size="small" type="warning">
              無効
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="" width="70" align="center">
          <template #default="{ row }">
            <el-button
              v-if="row.manual != null"
              link
              type="danger"
              size="small"
              @click="row.manual = null"
            >
              クリア
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="planEditVisible = false">キャンセル</el-button>
        <el-button type="primary" :loading="planEditSaving" @click="savePlanEdits">
          保存して再計算
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import {
  fetchProjectionDetail,
  fetchProjectionSummary,
  savePlanOverrides,
  type PlanOverrideItem,
  type ProjectionDetailRow,
  type ProjectionGroup,
  type ProjectionSummaryData,
} from '@/api/erp/inventoryProjection'

function todayIso(): string {
  const d = new Date()
  const m = `${d.getMonth() + 1}`.padStart(2, '0')
  const day = `${d.getDate()}`.padStart(2, '0')
  return `${d.getFullYear()}-${m}-${day}`
}

const targetMonth = ref(todayIso().slice(0, 7))
const baseDate = ref(todayIso())
const loading = ref(false)
const monthlyLoading = ref(false)
const summary = ref<ProjectionSummaryData | null>(null)
const matrixTab = ref<'daily' | 'monthly'>('daily')
const MONTHLY_RANGE = 6
const monthlyByYm = ref<Record<string, ProjectionGroup[]>>({})
const monthlyMonths = ref<string[]>([])

const chartRef = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null
const matrixChartRef = ref<HTMLDivElement | null>(null)
let matrixChart: echarts.ECharts | null = null
const MATRIX_CHART_MAX_SERIES = 8
const selectedMatrixRowIds = ref<string[]>([])

const detailVisible = ref(false)
const detailLoading = ref(false)
const detailGroupName = ref('')
const detailGroupKey = ref('')
const detailRows = ref<ProjectionDetailRow[]>([])
const detailDates = ref<string[]>([])

const GROUP_COLORS: Record<string, string> = {
  cutting: '#5470c6',
  molding: '#91cc75',
  plating_inhouse: '#fac858',
  plating_outsource: '#ee6666',
  welding_inhouse: '#73c0de',
  welding_outsource: '#fc8452',
  inspection: '#3ba272',
  warehouse: '#9a60b4',
}

const PROCESS_KEY_LABELS: Record<string, string> = {
  cutting: '切断',
  chamfering: '面取',
  molding: '成型',
  plating: '社内メッキ',
  outsourced_plating: '外注メッキ',
  welding: '溶接',
  outsourced_welding: '外注溶接',
  inspection: '検査',
  warehouse: '倉庫',
  outsourced_warehouse: '外注倉庫',
  pre_welding_inspection: '溶接前検査',
  pre_inspection: '外注支給前',
  pre_outsourcing: '外注検査前',
}

interface MatrixRow {
  key: string
  name: string
  metric:
    | 'header'
    | 'inventory'
    | 'plan'
    | 'actual'
    | 'next_usage'
    | 'next_usage_parent'
    | 'next_usage_child'
    | 'next_consume_parent'
    | 'next_consume_child'
    | 'outsourced_shipment'
    | 'demand'
  daily: Record<string, number>
  expanded?: boolean
  branchKey?: string
  /** 計画行のみ: 手動修正が適用された日 → 手動値（セル強調用） */
  overrides?: Record<string, number>
  /** 展開親行の種別（move / consume） */
  expandKind?: 'move' | 'consume'
}

function matrixRowId(row: MatrixRow): string {
  return `${row.key}:${row.metric}:${row.branchKey || ''}`
}

function isChartSelectable(row: MatrixRow): boolean {
  return row.metric !== 'header'
}

function isMatrixRowSelected(row: MatrixRow): boolean {
  return selectedMatrixRowIds.value.includes(matrixRowId(row))
}

function toggleMatrixChartRow(row: MatrixRow) {
  const id = matrixRowId(row)
  if (selectedMatrixRowIds.value.includes(id)) {
    selectedMatrixRowIds.value = selectedMatrixRowIds.value.filter((x) => x !== id)
    return
  }
  if (selectedMatrixRowIds.value.length >= MATRIX_CHART_MAX_SERIES) {
    ElMessage.warning(`折れ線グラフは最大 ${MATRIX_CHART_MAX_SERIES} 行まで選択できます`)
    return
  }
  selectedMatrixRowIds.value = [...selectedMatrixRowIds.value, id]
}

function clearMatrixChartRows() {
  selectedMatrixRowIds.value = []
}

/** 次工程移動／使用の展開状態（`${groupKey}:${kind}` → 開いているか） */
const nextExpandState = ref<Record<string, boolean>>({})

function expandKey(groupKey: string, kind: 'move' | 'consume'): string {
  return `${groupKey}:${kind}`
}

function sumDaily(daily: Record<string, number> | undefined | null): number {
  if (!daily) return 0
  return Object.values(daily).reduce((s, v) => s + (v || 0), 0)
}

function showsRowTotal(row: MatrixRow): boolean {
  return row.metric !== 'header' && row.metric !== 'inventory'
}

function matrixRowTotal(row: MatrixRow): number {
  if (!showsRowTotal(row)) return 0
  return sumDaily(row.daily)
}

function buildMatrixRowsFromGroups(groups: ProjectionGroup[]): MatrixRow[] {
  const rows: MatrixRow[] = []
  for (const g of groups) {
    rows.push({
      key: g.key,
      name: g.name,
      metric: 'header',
      daily: {},
    })
    rows.push({
      key: g.key,
      name: `　${g.name}在庫`,
      metric: 'inventory',
      daily: g.daily,
    })
    if (g.key !== 'warehouse') {
      const hasOverride = Object.keys(g.plan_override_daily || {}).length > 0
      rows.push({
        key: g.key,
        name: `　${g.name}計画${hasOverride ? '（手修正あり）' : ''}`,
        metric: 'plan',
        daily: g.plan_daily || {},
        overrides: g.plan_override_daily || {},
      })
      rows.push({
        key: g.key,
        name: `　${g.name}実績`,
        metric: 'actual',
        daily: g.actual_daily || {},
      })
    }
    if (g.next_usage_rows && g.next_usage_rows.length > 0) {
      const moveKey = expandKey(g.key, 'move')
      const expanded = !!nextExpandState.value[moveKey]
      rows.push({
        key: g.key,
        name: `　${g.next_usage_label || '次工程移動'}`,
        metric: 'next_usage_parent',
        daily: g.next_usage_daily || {},
        expanded,
        expandKind: 'move',
      })
      if (expanded) {
        for (const r of g.next_usage_rows) {
          rows.push({
            key: g.key,
            name: `　　${r.label}`,
            metric: 'next_usage_child',
            daily: r.daily || {},
            branchKey: r.key,
          })
        }
      }
    } else {
      rows.push({
        key: g.key,
        name: `　${g.next_usage_label || '次工程移動'}`,
        metric: 'next_usage',
        daily: g.next_usage_daily || {},
      })
    }
    if (g.key === 'warehouse' && g.outsourced_warehouse_shipment_daily) {
      rows.push({
        key: g.key,
        name: '　外注倉庫出荷',
        metric: 'outsourced_shipment',
        daily: g.outsourced_warehouse_shipment_daily,
        branchKey: 'outsourced_warehouse',
      })
    }
    if (g.next_consume_rows && g.next_consume_rows.length > 0) {
      const consumeKey = expandKey(g.key, 'consume')
      const expanded = !!nextExpandState.value[consumeKey]
      rows.push({
        key: g.key,
        name: `　${g.next_consume_label || '次工程使用'}`,
        metric: 'next_consume_parent',
        daily: g.next_consume_daily || {},
        expanded,
        expandKind: 'consume',
      })
      if (expanded) {
        for (const r of g.next_consume_rows) {
          rows.push({
            key: g.key,
            name: `　　${r.label}`,
            metric: 'next_consume_child',
            daily: r.daily || {},
            branchKey: r.key,
          })
        }
      }
    }
  }
  return rows
}

function listYearMonthsEndingAt(endYm: string, count: number): string[] {
  const [y0, m0] = endYm.split('-').map(Number)
  const out: string[] = []
  let y = y0
  let m = m0
  for (let i = 0; i < count; i++) {
    out.unshift(`${y}-${`${m}`.padStart(2, '0')}`)
    m -= 1
    if (m < 1) {
      m = 12
      y -= 1
    }
  }
  return out
}

function monthLabel(ym: string): string {
  const [y, m] = ym.split('-')
  return `${y}/${Number(m)}`
}

function monthEndBaseDate(ym: string): string {
  const [y, m] = ym.split('-').map(Number)
  const last = new Date(y, m, 0)
  const mm = `${last.getMonth() + 1}`.padStart(2, '0')
  const dd = `${last.getDate()}`.padStart(2, '0')
  return `${last.getFullYear()}-${mm}-${dd}`
}

const matrixRows = computed((): MatrixRow[] => {
  if (!summary.value) return []
  return buildMatrixRowsFromGroups(summary.value.groups)
})

const monthlyMatrixRows = computed((): MatrixRow[] => {
  if (!monthlyMonths.value.length) return []
  const templateGroups =
    monthlyByYm.value[targetMonth.value] ||
    monthlyByYm.value[monthlyMonths.value[monthlyMonths.value.length - 1]] ||
    summary.value?.groups
  if (!templateGroups?.length) return []

  // 行構造は対象月（なければ最新月）を基準に作り、各月の値を daily[ym] に載せる
  const baseRows = buildMatrixRowsFromGroups(templateGroups)
  return baseRows.map((row) => {
    const daily: Record<string, number> = {}
    const overrides: Record<string, number> = {}
    for (const ym of monthlyMonths.value) {
      const groups = monthlyByYm.value[ym]
      if (!groups) {
        daily[ym] = 0
        continue
      }
      const g = groups.find((x) => x.key === row.key)
      if (!g) {
        daily[ym] = 0
        continue
      }
      if (row.metric === 'header') {
        daily[ym] = 0
      } else if (row.metric === 'inventory') {
        daily[ym] = g.month_end ?? 0
      } else if (row.metric === 'outsourced_shipment') {
        daily[ym] = sumDaily(g.outsourced_warehouse_shipment_daily)
      } else if (row.metric === 'plan') {
        daily[ym] = sumDaily(g.plan_daily)
        const ov = sumDaily(g.plan_override_daily)
        if (ov > 0) overrides[ym] = ov
      } else if (row.metric === 'actual') {
        daily[ym] = sumDaily(g.actual_daily)
      } else if (row.metric === 'next_usage' || row.metric === 'next_usage_parent') {
        daily[ym] = sumDaily(g.next_usage_daily)
      } else if (row.metric === 'next_usage_child') {
        const child = g.next_usage_rows?.find((r) => r.key === row.branchKey)
        daily[ym] = sumDaily(child?.daily)
      } else if (row.metric === 'next_consume_parent') {
        daily[ym] = sumDaily(g.next_consume_daily)
      } else if (row.metric === 'next_consume_child') {
        const child = g.next_consume_rows?.find((r) => r.key === row.branchKey)
        daily[ym] = sumDaily(child?.daily)
      } else {
        daily[ym] = 0
      }
    }
    return {
      ...row,
      daily,
      overrides: Object.keys(overrides).length ? overrides : undefined,
    }
  })
})

const activeMatrixRows = computed(() =>
  matrixTab.value === 'monthly' ? monthlyMatrixRows.value : matrixRows.value,
)

const selectedMatrixRows = computed(() => {
  const selected = new Set(selectedMatrixRowIds.value)
  return activeMatrixRows.value.filter((row) => selected.has(matrixRowId(row)))
})

const chartCategories = computed(() =>
  matrixTab.value === 'monthly' ? monthlyMonths.value : summary.value?.dates || [],
)

const branchSummary = computed(() => {
  const stats = summary.value?.route_branch_stats
  if (!stats) return ''
  const fmt = (m: Record<string, number>) =>
    Object.entries(m)
      .sort((a, b) => b[1] - a[1])
      .map(([k, n]) => `${PROCESS_KEY_LABELS[k] || k} ${n}件`)
      .join(' / ')
  const parts: string[] = []
  if (Object.keys(stats.molding_next || {}).length) {
    parts.push(`成型の次工程: ${fmt(stats.molding_next)}`)
  }
  if (Object.keys(stats.plating_next || {}).length) {
    parts.push(`社内メッキの次工程: ${fmt(stats.plating_next)}`)
  }
  return parts.join('　｜　')
})

const cutoffSummary = computed(() => {
  const cutoff = summary.value?.actual_cutoff
  if (!cutoff) return ''
  return Object.entries(cutoff)
    .map(([k, ds]) => `${PROCESS_KEY_LABELS[k] || k} ${ds.slice(5)}`)
    .join(' / ')
})

function nextProcessLabel(row: ProjectionDetailRow): string {
  // 明細ダイアログは工程グループ単位なので、該当グループの下流を優先表示
  if (detailGroupKey.value === 'molding' && row.molding_next) {
    return PROCESS_KEY_LABELS[row.molding_next] || row.molding_next
  }
  if (detailGroupKey.value === 'plating_inhouse' && row.plating_next) {
    return PROCESS_KEY_LABELS[row.plating_next] || row.plating_next
  }
  if (row.molding_next) return PROCESS_KEY_LABELS[row.molding_next] || row.molding_next
  if (row.plating_next) return PROCESS_KEY_LABELS[row.plating_next] || row.plating_next
  return '—'
}

function isProjected(ds: string): boolean {
  return !!summary.value && ds >= summary.value.projection_start
}

function dayLabel(ds: string): string {
  return `${Number(ds.slice(8, 10))}日`
}

function formatQty(v: number): string {
  return (v ?? 0).toLocaleString()
}

function matrixRowClass({ row }: { row: MatrixRow }): string {
  const classes = [`group-${row.key}`]
  if (row.metric === 'header') classes.push('group-header-row')
  if (row.metric === 'inventory') classes.push('inventory-row')
  if (row.metric === 'plan') classes.push('plan-row')
  if (row.metric === 'actual') classes.push('actual-row')
  if (row.metric === 'next_usage' || row.metric === 'next_usage_parent') {
    classes.push('next-usage-row')
  }
  if (row.metric === 'next_usage_child') classes.push('next-usage-child-row')
  if (row.metric === 'next_consume_parent') classes.push('next-consume-row')
  if (row.metric === 'next_consume_child') classes.push('next-consume-child-row')
  if (row.metric === 'outsourced_shipment') classes.push('next-usage-row')
  return classes.join(' ')
}

function onMatrixRowClick(row: MatrixRow) {
  if (
    (row.metric !== 'next_usage_parent' && row.metric !== 'next_consume_parent') ||
    !row.key ||
    !row.expandKind
  ) {
    return
  }
  const k = expandKey(row.key, row.expandKind)
  nextExpandState.value = {
    ...nextExpandState.value,
    [k]: !nextExpandState.value[k],
  }
}

function onMatrixRowDblClick(row: MatrixRow) {
  if (!row.key || row.key === '__demand__') return
  if (
    row.metric === 'next_usage_parent' ||
    row.metric === 'next_usage_child' ||
    row.metric === 'next_consume_parent' ||
    row.metric === 'next_consume_child'
  ) {
    return
  }
  const g = summary.value?.groups.find((x) => x.key === row.key)
  if (!g) return
  if (row.metric === 'plan' && g.process_key) {
    openPlanEditor(g)
    return
  }
  openDetail(g)
}

function onMonthlyMatrixRowDblClick(row: MatrixRow) {
  if (!row.key || row.key === '__demand__') return
  if (
    row.metric === 'next_usage_parent' ||
    row.metric === 'next_usage_child' ||
    row.metric === 'next_consume_parent' ||
    row.metric === 'next_consume_child'
  ) {
    return
  }
  // 月別では計画手動修正はせず、製品別明細のみ（対象月）
  const g =
    summary.value?.groups.find((x) => x.key === row.key) ||
    monthlyByYm.value[targetMonth.value]?.find((x) => x.key === row.key)
  if (!g) return
  openDetail(g)
}

/** 計画合計 手動修正ダイアログ */
interface PlanEditRow {
  ds: string
  auto: number
  manual: number | null
}

const planEditVisible = ref(false)
const planEditSaving = ref(false)
const planEditGroupName = ref('')
const planEditProcessKey = ref('')
const planEditRows = ref<PlanEditRow[]>([])
let planEditOriginal: Record<string, number | null> = {}

function openPlanEditor(g: ProjectionGroup) {
  if (!summary.value || !g.process_key) return
  planEditGroupName.value = g.name
  planEditProcessKey.value = g.process_key
  const autoDaily = g.plan_auto_daily || {}
  const overrideDaily = g.plan_override_daily || {}
  planEditOriginal = {}
  planEditRows.value = summary.value.dates.map((ds) => {
    const manual = overrideDaily[ds] != null ? overrideDaily[ds] : null
    planEditOriginal[ds] = manual
    return { ds, auto: autoDaily[ds] ?? 0, manual }
  })
  planEditVisible.value = true
}

async function savePlanEdits() {
  const items: PlanOverrideItem[] = []
  for (const r of planEditRows.value) {
    const before = planEditOriginal[r.ds] ?? null
    const after = r.manual ?? null
    if (before === after) continue
    items.push({ plan_date: r.ds, process_key: planEditProcessKey.value, qty: after })
  }
  if (items.length === 0) {
    planEditVisible.value = false
    return
  }
  planEditSaving.value = true
  try {
    await savePlanOverrides(items)
    planEditVisible.value = false
    ElMessage.success('計画手動修正を保存しました')
    await load(true)
  } catch (e: any) {
    const msg = e?.response?.data?.detail || e?.message || '保存に失敗しました'
    ElMessage.error(msg)
  } finally {
    planEditSaving.value = false
  }
}

async function loadMonthlySummaries(force = false) {
  const months = listYearMonthsEndingAt(targetMonth.value, MONTHLY_RANGE)
  monthlyMonths.value = months
  monthlyLoading.value = true
  try {
    const results = await Promise.all(
      months.map(async (ym) => {
        const res = await fetchProjectionSummary({
          year_month: ym,
          base_date: ym === targetMonth.value ? baseDate.value : monthEndBaseDate(ym),
          force: force && ym === targetMonth.value,
        })
        return [ym, res.data.groups] as const
      }),
    )
    const next: Record<string, ProjectionGroup[]> = {}
    for (const [ym, groups] of results) next[ym] = groups
    // 対象月は最新の summary を優先
    if (summary.value?.groups?.length) next[targetMonth.value] = summary.value.groups
    monthlyByYm.value = next
  } catch (e: any) {
    const msg = e?.response?.data?.detail || e?.message || '月別データの読み込みに失敗しました'
    ElMessage.error(msg)
  } finally {
    monthlyLoading.value = false
  }
}

async function onMatrixTabChange(name: string | number) {
  if (name === 'monthly') {
    await loadMonthlySummaries(false)
  }
  syncMatrixRowSelection()
  await nextTick()
  // tab切替でチャートDOMが再生成されることがあるため一旦破棄して再描画
  matrixChart?.dispose()
  matrixChart = null
  renderMatrixChart()
}

function syncMatrixRowSelection() {
  const rows = activeMatrixRows.value
  const validIds = new Set(rows.filter(isChartSelectable).map(matrixRowId))
  selectedMatrixRowIds.value = selectedMatrixRowIds.value.filter((id) => validIds.has(id))
  if (selectedMatrixRowIds.value.length === 0) {
    selectedMatrixRowIds.value = rows
      .filter((row) => row.metric === 'inventory')
      .slice(0, 3)
      .map(matrixRowId)
  }
}

async function load(force = false) {
  loading.value = true
  try {
    const res = await fetchProjectionSummary({
      year_month: targetMonth.value,
      base_date: baseDate.value,
      force,
    })
    summary.value = res.data
    if (summary.value?.groups?.length) {
      monthlyByYm.value = {
        ...monthlyByYm.value,
        [targetMonth.value]: summary.value.groups,
      }
    }
    syncMatrixRowSelection()
    if (matrixTab.value === 'monthly') {
      await loadMonthlySummaries(force)
    }
    await nextTick()
    renderChart()
    renderMatrixChart()
  } catch (e: any) {
    const msg = e?.response?.data?.detail || e?.message || '読み込みに失敗しました'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

function renderChart() {
  if (!chartRef.value || !summary.value) return
  if (!chart) {
    chart = echarts.init(chartRef.value)
  }
  const s = summary.value
  const projStartIdx = s.dates.findIndex((d) => d >= s.projection_start)
  const series = s.groups.map((g) => ({
    name: g.name,
    type: 'line' as const,
    smooth: false,
    symbol: 'circle',
    symbolSize: 4,
    data: s.dates.map((ds) => g.daily[ds] ?? 0),
    itemStyle: { color: GROUP_COLORS[g.key] },
    lineStyle: { color: GROUP_COLORS[g.key], width: 2 },
  }))
  const markArea =
    projStartIdx >= 0
      ? {
          silent: true,
          itemStyle: { color: 'rgba(64, 158, 255, 0.07)' },
          data: [[{ xAxis: s.dates[projStartIdx] }, { xAxis: s.dates[s.dates.length - 1] }]],
        }
      : undefined
  if (series.length > 0 && markArea) {
    ;(series[0] as any).markArea = markArea
    ;(series[0] as any).markLine = {
      silent: true,
      symbol: 'none',
      lineStyle: { color: '#909399', type: 'dashed' },
      label: { formatter: '基準日', position: 'insideEndTop' },
      data: [{ xAxis: s.base_date }],
    }
  }
  chart.setOption(
    {
      tooltip: {
        trigger: 'axis',
        valueFormatter: (v: number) => (v ?? 0).toLocaleString() + ' 本',
      },
      legend: { top: 0, type: 'scroll' },
      grid: { left: 70, right: 24, top: 36, bottom: 28 },
      xAxis: {
        type: 'category',
        data: s.dates,
        axisLabel: {
          formatter: (v: string) => `${Number(v.slice(8, 10))}`,
        },
      },
      yAxis: {
        type: 'value',
        name: '在庫（本）',
        axisLabel: { formatter: (v: number) => v.toLocaleString() },
      },
      series,
    },
    true,
  )
}

const MATRIX_METRIC_COLORS: Partial<Record<MatrixRow['metric'], string>> = {
  inventory: '#2563eb',
  plan: '#16a34a',
  actual: '#64748b',
  next_usage: '#f59e0b',
  next_usage_parent: '#f59e0b',
  next_usage_child: '#fb923c',
  next_consume_parent: '#8b5cf6',
  next_consume_child: '#a78bfa',
  outsourced_shipment: '#c026d3',
  demand: '#ef4444',
}

function matrixSeriesColor(row: MatrixRow, index: number): string {
  const groupColor = GROUP_COLORS[row.key]
  if (row.metric === 'inventory' && groupColor) return groupColor
  const base = MATRIX_METRIC_COLORS[row.metric]
  if (base) return base
  const fallback = ['#2563eb', '#16a34a', '#f59e0b', '#8b5cf6', '#0891b2', '#e11d48']
  return fallback[index % fallback.length]
}

function toSenbon(v: number): number {
  return Math.round(((v ?? 0) / 1000) * 10) / 10
}

function formatSenbon(v: number): string {
  const n = Number(v ?? 0)
  return Number.isInteger(n)
    ? n.toLocaleString()
    : n.toLocaleString(undefined, { maximumFractionDigits: 1 })
}

function renderMatrixChart() {
  const categories = chartCategories.value
  if (!categories.length || selectedMatrixRows.value.length === 0) {
    matrixChart?.dispose()
    matrixChart = null
    return
  }
  if (!matrixChartRef.value) return
  if (!matrixChart) matrixChart = echarts.init(matrixChartRef.value)

  const isMonthly = matrixTab.value === 'monthly'
  const s = summary.value
  const projStartIdx = !isMonthly && s ? s.dates.findIndex((d) => d >= s.projection_start) : -1
  const seriesCount = selectedMatrixRows.value.length
  const series = selectedMatrixRows.value.map((row, index) => {
    const color = matrixSeriesColor(row, index)
    return {
      name: row.name.trim(),
      type: 'line' as const,
      smooth: 0.18,
      symbol: 'circle',
      symbolSize: 6,
      showSymbol: true,
      emphasis: { focus: 'series' as const, showSymbol: true },
      data: categories.map((key) => toSenbon(row.daily[key] ?? 0)),
      itemStyle: { color },
      lineStyle: {
        color,
        width: row.metric === 'inventory' ? 3 : 2,
        type: row.metric === 'actual' ? ('dashed' as const) : ('solid' as const),
      },
      label: {
        show: true,
        position: 'top',
        distance: 4,
        color,
        fontSize: seriesCount > 4 ? 9 : 10,
        fontWeight: 600,
        formatter: (params: { value?: number }) => formatSenbon(Number(params.value ?? 0)),
      },
      areaStyle:
        seriesCount === 1 && row.metric === 'inventory'
          ? {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: `${color}30` },
                { offset: 1, color: `${color}02` },
              ]),
            }
          : undefined,
    }
  })
  if (series.length && !isMonthly && s && projStartIdx >= 0) {
    ;(series[0] as any).markArea = {
      silent: true,
      itemStyle: { color: 'rgba(37, 99, 235, 0.045)' },
      data: [[{ xAxis: s.dates[projStartIdx] }, { xAxis: s.dates[s.dates.length - 1] }]],
    }
    ;(series[0] as any).markLine = {
      silent: true,
      symbol: 'none',
      lineStyle: { color: '#94a3b8', type: 'dashed' },
      label: { formatter: '基準日', color: '#64748b' },
      data: [{ xAxis: s.base_date }],
    }
  }
  matrixChart.setOption(
    {
      animationDuration: 420,
      color: series.map((item) => item.itemStyle.color),
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(15, 23, 42, 0.94)',
        borderWidth: 0,
        textStyle: { color: '#f8fafc' },
        valueFormatter: (v: number) => `${formatSenbon(Number(v ?? 0))} 千本`,
      },
      legend: {
        top: 0,
        type: 'scroll',
        textStyle: { color: '#475569' },
      },
      grid: { left: 72, right: 28, top: 52, bottom: 42 },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: categories,
        axisLine: { lineStyle: { color: '#cbd5e1' } },
        axisTick: { show: false },
        axisLabel: {
          color: '#64748b',
          formatter: (v: string) => (isMonthly ? monthLabel(v) : `${Number(v.slice(8, 10))}日`),
        },
      },
      yAxis: {
        type: 'value',
        name: '数量（千本）',
        nameTextStyle: { color: '#64748b' },
        splitLine: { lineStyle: { color: '#e2e8f0', type: 'dashed' } },
        axisLabel: { color: '#64748b', formatter: (v: number) => formatSenbon(v) },
      },
      dataZoom:
        !isMonthly && categories.length > 20
          ? [{ type: 'inside' }, { type: 'slider', height: 14, bottom: 4 }]
          : [],
      series,
    },
    true,
  )
}

async function openDetail(g: ProjectionGroup | { key: string; name: string }) {
  if (g.key === '__demand__') return
  detailGroupName.value = (g as any).name
  detailGroupKey.value = g.key
  detailVisible.value = true
  detailLoading.value = true
  try {
    const res = await fetchProjectionDetail({
      year_month: targetMonth.value,
      process_key: g.key,
      base_date: baseDate.value,
    })
    detailRows.value = res.data.rows
    detailDates.value = res.data.dates
  } catch (e: any) {
    const msg = e?.response?.data?.detail || e?.message || '明細の読み込みに失敗しました'
    ElMessage.error(msg)
    detailRows.value = []
  } finally {
    detailLoading.value = false
  }
}

function onResize() {
  chart?.resize()
  matrixChart?.resize()
}

watch([targetMonth, baseDate], () => {
  load()
})

watch(
  [selectedMatrixRowIds, matrixRows],
  async () => {
    await nextTick()
    renderMatrixChart()
  },
  { deep: true },
)

onMounted(() => {
  window.addEventListener('resize', onResize)
  load()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  chart?.dispose()
  chart = null
  matrixChart?.dispose()
  matrixChart = null
})
</script>

<style scoped>
.inventory-projection-page {
  min-height: 100%;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background:
    radial-gradient(circle at 8% 0%, rgba(59, 130, 246, 0.09), transparent 28%),
    radial-gradient(circle at 92% 6%, rgba(139, 92, 246, 0.07), transparent 25%), #f6f8fc;
}

:deep(.el-card) {
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 14px;
  box-shadow: 0 8px 26px rgba(15, 23, 42, 0.055);
}

:deep(.el-card__header) {
  padding: 15px 18px;
  border-bottom-color: #eef2f7;
}

.toolbar-card {
  background: linear-gradient(115deg, #ffffff 0%, #f8fbff 62%, #f5f3ff 100%);
}

:deep(.toolbar-card .el-card__body) {
  padding: 16px 18px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.page-title {
  font-size: 21px;
  font-weight: 750;
  letter-spacing: 0.02em;
  color: #172033;
}

.help-button {
  width: 25px;
  height: 25px;
  padding: 0;
  border: 1px solid #bfdbfe;
  border-radius: 50%;
  background: #eff6ff;
  color: #2563eb;
  font-size: 14px;
  font-weight: 750;
  line-height: 23px;
  cursor: pointer;
  transition: all 0.18s ease;
}

.help-button:hover {
  color: #fff;
  border-color: #2563eb;
  background: #2563eb;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.28);
  transform: translateY(-1px);
}

.help-button.small {
  width: 21px;
  height: 21px;
  font-size: 12px;
  line-height: 19px;
}

.help-content {
  color: #475569;
  font-size: 13px;
  line-height: 1.7;
}

.help-content p {
  margin: 5px 0;
}

.help-content.compact p {
  margin: 2px 0;
}

.help-title {
  margin-bottom: 7px;
  color: #172033;
  font-size: 14px;
  font-weight: 700;
}

.help-meta {
  margin-top: 8px;
  padding: 7px 9px;
  border-radius: 7px;
  background: #f1f5f9;
  color: #64748b;
  font-size: 12px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar-right .label {
  font-size: 13px;
  color: #606266;
}

.kpi-row {
  display: grid;
  grid-template-columns: repeat(8, minmax(0, 1fr));
  gap: 12px;
}

.kpi-card {
  position: relative;
  overflow: hidden;
  background: #fff;
  border: 1px solid #e8edf5;
  border-radius: 13px;
  padding: 14px 14px 12px;
  cursor: pointer;
  box-shadow: 0 5px 18px rgba(15, 23, 42, 0.045);
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease,
    border-color 0.18s ease;
}

.kpi-accent {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 4px;
  background: var(--group-color);
}

.kpi-card:hover {
  border-color: color-mix(in srgb, var(--group-color) 45%, #fff);
  box-shadow: 0 11px 24px rgba(15, 23, 42, 0.1);
  transform: translateY(-3px);
}

.kpi-card.negative {
  border-color: #f56c6c;
  background: #fef0f0;
}

.kpi-name {
  font-size: 12px;
  color: #64748b;
  font-weight: 650;
}

.kpi-value {
  margin: 5px 0 7px;
  color: #172033;
  font-size: 22px;
  font-weight: 750;
  font-variant-numeric: tabular-nums;
}

.kpi-card.negative .kpi-value {
  color: #f56c6c;
}

.kpi-unit {
  font-size: 11px;
  font-weight: 400;
  color: #909399;
  margin-left: 2px;
}

.kpi-sub {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #909399;
}

.kpi-sub .warn {
  color: #e6a23c;
  font-weight: 600;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.card-title-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-title {
  color: #172033;
  font-size: 15px;
  font-weight: 700;
}

.header-chip {
  padding: 4px 9px;
  border: 1px solid #dbeafe;
  border-radius: 999px;
  background: #eff6ff;
  color: #2563eb;
  font-size: 11px;
  font-weight: 650;
}

.matrix-legend {
  display: flex;
  align-items: center;
  gap: 13px;
  color: #64748b;
  font-size: 11px;
}

.matrix-legend span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.legend-dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
}

.legend-dot.inventory {
  background: #2563eb;
}
.legend-dot.plan {
  background: #16a34a;
}
.legend-dot.actual {
  background: #94a3b8;
}
.legend-dot.next {
  background: #f59e0b;
}

.chart-card,
.matrix-card {
  background: rgba(255, 255, 255, 0.98);
}

.matrix-tabs {
  margin-bottom: 10px;
}

:deep(.matrix-tabs .el-tabs__header) {
  margin-bottom: 12px;
}

:deep(.matrix-tabs .el-tabs__item) {
  font-weight: 650;
}

:deep(.matrix-tabs .el-tabs__nav-wrap::after) {
  height: 1px;
  background-color: #e8edf4;
}

.chart-container {
  width: 100%;
  height: 370px;
}

.matrix-name-cell {
  display: flex;
  align-items: center;
  min-width: 0;
}

.chart-row-checkbox {
  flex: 0 0 auto;
  margin-right: 7px;
}

.checkbox-placeholder {
  display: inline-block;
  flex: 0 0 21px;
}

.row-total {
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.process-link {
  color: #409eff;
  cursor: pointer;
  font-weight: 600;
}

.process-header {
  font-weight: 700;
}

.process-metric {
  color: #606266;
  font-size: 12px;
}

.projected {
  color: #409eff;
}

.projected-header {
  color: #409eff;
}

.negative {
  color: #f56c6c;
  font-weight: 600;
}

.metric-plan {
  color: #16a34a;
  font-weight: 550;
}

.plan-overridden {
  color: #e6a23c;
  font-weight: 700;
  background: #fdf6ec;
  border-radius: 2px;
  padding: 0 2px;
}

.plan-edit-hint {
  margin-bottom: 10px;
  padding: 8px 10px;
  background: #f4f4f5;
  border-radius: 4px;
  color: #909399;
  font-size: 12px;
  line-height: 1.7;
}

.metric-actual {
  color: #64748b;
}

.metric-next {
  color: #d97706;
}

:deep(.group-header-row) {
  --row-accent: #64748b;
  background: linear-gradient(90deg, color-mix(in srgb, var(--row-accent) 10%, #fff), #fff 65%);
}

:deep(.group-header-row td) {
  border-top: 1px solid color-mix(in srgb, var(--row-accent) 16%, #e2e8f0);
  font-weight: 700;
}

:deep(.group-header-row td:first-child) {
  box-shadow: inset 4px 0 var(--row-accent);
}

:deep(.inventory-row) {
  background: #fbfdff;
}

:deep(.plan-row) {
  background: #fbfefb;
}

:deep(.actual-row) {
  background: #fcfcfd;
}

:deep(.next-usage-row) {
  background: #fff8ec;
}

:deep(.next-usage-child-row) {
  background: #fffbf5;
}

:deep(.next-consume-row) {
  background: #f4f1ff;
}

:deep(.next-consume-child-row) {
  background: #faf8ff;
}

:deep(.group-cutting) {
  --row-accent: #5470c6;
}
:deep(.group-molding) {
  --row-accent: #91cc75;
}
:deep(.group-plating_inhouse) {
  --row-accent: #d89b17;
}
:deep(.group-plating_outsource) {
  --row-accent: #ee6666;
}
:deep(.group-welding_inhouse) {
  --row-accent: #35a4c6;
}
:deep(.group-welding_outsource) {
  --row-accent: #fc8452;
}
:deep(.group-inspection) {
  --row-accent: #3ba272;
}
:deep(.group-warehouse) {
  --row-accent: #9a60b4;
}

.expand-icon {
  display: inline-block;
  width: 1em;
  margin-right: 2px;
  font-size: 10px;
  color: #e6a23c;
}

.next-parent-label {
  font-weight: 600;
}

.next-child-label {
  color: #909399;
  font-size: 12px;
}

:deep(.el-table .cell) {
  padding: 0 6px;
}

:deep(.matrix-card .el-table) {
  --el-table-border-color: #e8edf4;
  --el-table-header-bg-color: #f8fafc;
  --el-table-row-hover-bg-color: #eff6ff;
  border-radius: 9px;
}

:deep(.matrix-card .el-table th.el-table__cell) {
  height: 40px;
  color: #475569;
  font-weight: 650;
}

:deep(.matrix-card .el-table td.el-table__cell) {
  height: 34px;
}

.matrix-chart-panel {
  margin-top: 16px;
  padding: 16px 16px 8px;
  border: 1px solid #e5eaf2;
  border-radius: 12px;
  background: linear-gradient(180deg, #fff 0%, #fbfdff 100%);
}

.matrix-chart-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.matrix-chart-title {
  color: #172033;
  font-size: 14px;
  font-weight: 700;
}

.matrix-chart-subtitle {
  margin-top: 3px;
  color: #94a3b8;
  font-size: 11px;
}

.matrix-chart-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.matrix-chart-container {
  width: 100%;
  height: 360px;
}

@media (max-width: 1400px) {
  .kpi-row {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 900px) {
  .inventory-projection-page {
    padding: 10px;
  }

  .toolbar-right,
  .matrix-chart-toolbar {
    align-items: flex-start;
  }

  .toolbar-right {
    flex-wrap: wrap;
  }

  .kpi-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .matrix-legend {
    display: none;
  }
}
</style>
