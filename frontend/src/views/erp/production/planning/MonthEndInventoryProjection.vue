<template>
  <div class="inventory-projection-page">
    <!-- ツールバー -->
    <el-card class="toolbar-card" shadow="never">
      <div class="toolbar">
        <div class="toolbar-left">
          <span class="page-title">月末在庫予測</span>
          <el-popover placement="bottom-start" :width="640" trigger="click">
            <template #reference>
              <button class="help-button" type="button" aria-label="計算ルールを表示">?</button>
            </template>
            <div class="help-content">
              <div class="help-title">
                <span class="help-title-icon">ƒ</span>
                <span>計算・表示ルール</span>
              </div>
              <p class="help-intro">
                基準日以前は実績在庫、翌日以降は下記の閉形式で予測します。生産数量は工程別の実績最終日以前は実績、翌日以降は計画（手動修正優先）です。当日より後の日付の実績は 0 として扱います。
                手動計画があり次工程移動が複数分岐する工程では、直近 30
                日の実績去向平均比（数量加重）で手動合計を各分岐へ配分します。
              </p>
              <div class="help-section help-section-inventory">
                <div class="help-subtitle">
                  <span class="help-subtitle-dot"></span>
                  工程在庫（予測区間）
                </div>
                <ul class="help-formula-list">
                <li>
                  <strong>切断</strong> = 繰越 + 切断生産 − 次工程使用（成型計画） + 前日在庫
                </li>
                <li>
                  <strong>成型</strong> = 繰越 + 成型生産 − 次工程使用（社内メッキ・外注メッキ・溶接・外注溶接・検査）
                  + 前日在庫
                </li>
                <li>
                  <strong>社内メッキ</strong> = 繰越 + 社内メッキ生産 − 次工程使用（溶接・検査） + 前日在庫
                </li>
                <li>
                  <strong>外注メッキ</strong> = 繰越 + 外注メッキ生産 − 次工程使用（検査・外注検査） +
                  前日在庫
                </li>
                <li>
                  <strong>溶接</strong> = 繰越 + 溶接生産 − 次工程使用（検査・社内メッキ・外注メッキ） +
                  前日在庫
                </li>
                <li>
                  <strong>外注溶接</strong> = 繰越 + 外注溶接生産 − 次工程使用（外注メッキ） + 前日在庫
                </li>
                <li>
                  <strong>検査</strong> = 繰越 + 検査生産 − 次工程使用（倉庫） + 前日在庫
                </li>
                <li>
                  <strong>倉庫</strong> = 繰越（検査・倉庫） + 検査生産 − 社内倉庫出荷 + 前日在庫
                </li>
                </ul>
                <p class="help-note">
                  基準日以前の倉庫在庫は社内倉庫在庫＋検査在庫（外注倉庫は含めず、社内倉庫ルート製品のみ）です。社内倉庫出荷／外注倉庫出荷は、それぞれルートに社内倉庫／外注倉庫を持つ製品の内示合計です。
                </p>
              </div>
              <div class="help-section help-section-trend">
                <div class="help-subtitle">
                  <span class="help-subtitle-dot"></span>
                  在庫推移（予測区間・前工程在庫起点）
                </div>
                <ul class="help-formula-list">
                <li>
                  <strong>成型在庫</strong> = 繰越（前工程） + 切断生産 − 成型生産 + 前日在庫
                </li>
                <li>
                  <strong>メッキ在庫</strong> = 繰越（前工程） + 成型の次工程移動（社内メッキ） +
                  溶接の次工程移動（社内メッキ） − 社内メッキ生産 + 前日在庫
                </li>
                <li>
                  <strong>溶接在庫</strong> = 繰越（前工程） + 成型の次工程移動（溶接） +
                  社内メッキの次工程移動（溶接） − 溶接生産 + 前日在庫
                </li>
                <li>
                  <strong>検査在庫</strong> = 繰越（前工程） + 社内メッキの次工程移動（検査） +
                  外注メッキの次工程移動（検査） + 成型の次工程移動（検査） +
                  溶接の次工程移動（検査） − 検査生産 + 前日在庫
                </li>
                </ul>
              </div>
              <p class="help-operation">
                計画行はダブルクリックで修正できます。次工程移動／次工程使用／在庫推移の親行をクリックすると内訳を開閉します。
              </p>
            </div>
          </el-popover>
          <el-tag v-if="summary" size="small" class="product-count-tag" effect="plain">
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

    <!-- KPI カード（検査は倉庫に含むため非表示） -->
    <div v-if="summary" class="kpi-row">
      <div
        v-for="g in kpiGroups"
        :key="g.key"
        class="kpi-card"
        :class="{ negative: g.month_end < 0 }"
        :style="{ '--group-color': GROUP_COLORS[g.key] || '#409eff' }"
        @click="openDetail(g)"
      >
        <div class="kpi-glow"></div>
        <div class="kpi-accent"></div>
        <div class="kpi-top">
          <span class="kpi-dot"></span>
          <div class="kpi-name">{{ g.name }}</div>
        </div>
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
                  'process-header': row.metric === 'header' || row.metric === 'trend_parent',
                  'process-metric':
                    row.metric !== 'header' &&
                    row.metric !== 'trend_parent' &&
                    row.key !== '__demand__',
                  'process-link':
                    row.metric === 'header' ||
                    row.metric === 'next_usage_parent' ||
                    row.metric === 'next_consume_parent' ||
                    row.metric === 'trend_parent',
                  'next-parent-label':
                    row.metric === 'next_usage_parent' ||
                    row.metric === 'next_consume_parent' ||
                    row.metric === 'trend_parent',
                  'next-child-label':
                    row.metric === 'next_usage_child' ||
                    row.metric === 'next_consume_child' ||
                    row.metric === 'trend_child',
                }"
              >
                <span
                  v-if="
                    row.metric === 'next_usage_parent' ||
                    row.metric === 'next_consume_parent' ||
                    row.metric === 'trend_parent'
                  "
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
              :class="matrixMetricClass(row, matrixRowTotal(row) < 0)"
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
              :class="[
                matrixMetricClass(row, (row.daily[ds] ?? 0) < 0),
                {
                  projected: isProjected(ds) && isInventoryMetric(row),
                  'plan-overridden': row.metric === 'plan' && row.overrides?.[ds] != null,
                },
              ]"
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
                  'process-header': row.metric === 'header' || row.metric === 'trend_parent',
                  'process-metric':
                    row.metric !== 'header' &&
                    row.metric !== 'trend_parent' &&
                    row.key !== '__demand__',
                  'process-link':
                    row.metric === 'header' ||
                    row.metric === 'next_usage_parent' ||
                    row.metric === 'next_consume_parent' ||
                    row.metric === 'trend_parent',
                  'next-parent-label':
                    row.metric === 'next_usage_parent' ||
                    row.metric === 'next_consume_parent' ||
                    row.metric === 'trend_parent',
                  'next-child-label':
                    row.metric === 'next_usage_child' ||
                    row.metric === 'next_consume_child' ||
                    row.metric === 'trend_child',
                }"
              >
                <span
                  v-if="
                    row.metric === 'next_usage_parent' ||
                    row.metric === 'next_consume_parent' ||
                    row.metric === 'trend_parent'
                  "
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
              :class="matrixMetricClass(row, matrixRowTotal(row) < 0)"
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
              :class="[
                matrixMetricClass(row, (row.daily[ym] ?? 0) < 0),
                {
                  projected: ym === targetMonth && isInventoryMetric(row),
                  'plan-overridden': row.metric === 'plan' && row.overrides?.[ym] != null,
                },
              ]"
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
        次工程移動が複数分岐する工程では、手動計画合計を直近 30
        日の実績去向の平均比（数量加重）で各分岐へ配分します。
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

type InventoryTrendRow = NonNullable<ProjectionSummaryData['inventory_trend_rows']>[number]

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

/** KPI カード用（検査は倉庫在庫に含むため除外） */
const kpiGroups = computed(() =>
  (summary.value?.groups || []).filter((g) => g.key !== 'inspection'),
)
const MONTHLY_RANGE = 6
const monthlyByYm = ref<Record<string, ProjectionGroup[]>>({})
const monthlyTrendByYm = ref<Record<string, InventoryTrendRow[]>>({})
const monthlyMonths = ref<string[]>([])

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

/** 工程グループ色（KPI・表アクセント・チャートで共通） */
const GROUP_COLORS: Record<string, string> = {
  cutting: '#4f6bd8',
  molding: '#4caf50',
  plating_inhouse: '#e6a23c',
  plating_outsource: '#f05656',
  welding_inhouse: '#3aa0c4',
  welding_outsource: '#f07a3a',
  inspection: '#2f9e78',
  warehouse: '#8b5bb5',
  inventory_trend: '#2563eb',
  __demand__: '#64748b',
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
    | 'trend_parent'
    | 'trend_child'
    | 'demand'
  daily: Record<string, number>
  expanded?: boolean
  branchKey?: string
  /** 計画行のみ: 手動修正が適用された日 → 手動値（セル強調用） */
  overrides?: Record<string, number>
  /** 展開親行の種別（move / consume / trend） */
  expandKind?: 'move' | 'consume' | 'trend'
}

function matrixRowId(row: MatrixRow): string {
  return `${row.key}:${row.metric}:${row.branchKey || ''}`
}

function isChartSelectable(row: MatrixRow): boolean {
  return row.metric !== 'header' && row.metric !== 'trend_parent'
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

/** 次工程移動／使用／在庫推移の展開状態（`${groupKey}:${kind}` → 開いているか） */
const nextExpandState = ref<Record<string, boolean>>({})

function expandKey(groupKey: string, kind: 'move' | 'consume' | 'trend'): string {
  return `${groupKey}:${kind}`
}

function sumDaily(daily: Record<string, number> | undefined | null): number {
  if (!daily) return 0
  return Object.values(daily).reduce((s, v) => s + (v || 0), 0)
}

function showsRowTotal(row: MatrixRow): boolean {
  return (
    row.metric !== 'header' &&
    row.metric !== 'inventory' &&
    row.metric !== 'trend_parent' &&
    row.metric !== 'trend_child'
  )
}

function matrixRowTotal(row: MatrixRow): number {
  if (!showsRowTotal(row)) return 0
  return sumDaily(row.daily)
}

function appendInventoryTrendRows(
  rows: MatrixRow[],
  trendRows: InventoryTrendRow[] | undefined | null,
): void {
  if (!trendRows?.length) return
  const trendKey = 'inventory_trend'
  const k = expandKey(trendKey, 'trend')
  const expanded = nextExpandState.value[k] ?? true
  rows.push({
    key: trendKey,
    name: '在庫推移',
    metric: 'trend_parent',
    daily: {},
    expanded,
    expandKind: 'trend',
  })
  if (!expanded) return
  for (const r of trendRows) {
    rows.push({
      key: r.key,
      name: `　${r.label}`,
      metric: 'trend_child',
      daily: r.daily || {},
      branchKey: r.key,
    })
  }
}

function buildMatrixRowsFromGroups(
  groups: ProjectionGroup[],
  trendRows?: InventoryTrendRow[] | null,
): MatrixRow[] {
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
  appendInventoryTrendRows(rows, trendRows)
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
  return buildMatrixRowsFromGroups(summary.value.groups, summary.value.inventory_trend_rows)
})

const monthlyMatrixRows = computed((): MatrixRow[] => {
  if (!monthlyMonths.value.length) return []
  const templateGroups =
    monthlyByYm.value[targetMonth.value] ||
    monthlyByYm.value[monthlyMonths.value[monthlyMonths.value.length - 1]] ||
    summary.value?.groups
  if (!templateGroups?.length) return []
  const templateTrend =
    monthlyTrendByYm.value[targetMonth.value] ||
    summary.value?.inventory_trend_rows ||
    monthlyTrendByYm.value[monthlyMonths.value[monthlyMonths.value.length - 1]]

  // 行構造は対象月（なければ最新月）を基準に作り、各月の値を daily[ym] に載せる
  const baseRows = buildMatrixRowsFromGroups(templateGroups, templateTrend)
  return baseRows.map((row) => {
    const daily: Record<string, number> = {}
    const overrides: Record<string, number> = {}
    for (const ym of monthlyMonths.value) {
      const groups = monthlyByYm.value[ym]
      if (!groups) {
        daily[ym] = 0
        continue
      }
      if (row.metric === 'trend_parent') {
        daily[ym] = 0
        continue
      }
      if (row.metric === 'trend_child') {
        const trend = monthlyTrendByYm.value[ym]?.find((r) => r.key === row.branchKey)
        daily[ym] = trend?.month_end ?? 0
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

function isInventoryMetric(row: MatrixRow): boolean {
  return row.metric === 'inventory' || row.metric === 'trend_child'
}

function isNextMetric(row: MatrixRow): boolean {
  return (
    row.metric === 'next_usage' ||
    row.metric === 'next_usage_parent' ||
    row.metric === 'next_usage_child' ||
    row.metric === 'next_consume_parent' ||
    row.metric === 'next_consume_child' ||
    row.metric === 'outsourced_shipment'
  )
}

/** 図例（在庫=青 / 計画=緑 / 実績=灰 / 次工程=橙）と数値色を揃える */
function matrixMetricClass(row: MatrixRow, isNegative = false): Record<string, boolean> {
  return {
    negative: isNegative,
    'metric-inventory': isInventoryMetric(row),
    'metric-plan': row.metric === 'plan',
    'metric-actual': row.metric === 'actual',
    'metric-next': isNextMetric(row),
  }
}

function matrixRowClass({ row }: { row: MatrixRow }): string {
  const classes = [`group-${row.key}`]
  if (row.metric === 'header') classes.push('group-header-row')
  if (isInventoryMetric(row)) classes.push('inventory-row')
  if (row.metric === 'plan') classes.push('plan-row')
  if (row.metric === 'actual') classes.push('actual-row')
  if (row.metric === 'next_usage' || row.metric === 'next_usage_parent') {
    classes.push('next-usage-row')
  }
  if (row.metric === 'next_usage_child') classes.push('next-usage-child-row')
  if (row.metric === 'next_consume_parent') classes.push('next-consume-row')
  if (row.metric === 'next_consume_child') classes.push('next-consume-child-row')
  if (row.metric === 'outsourced_shipment') classes.push('next-usage-row')
  if (row.metric === 'trend_parent') classes.push('trend-parent-row')
  return classes.join(' ')
}

function onMatrixRowClick(row: MatrixRow) {
  if (
    (row.metric !== 'next_usage_parent' &&
      row.metric !== 'next_consume_parent' &&
      row.metric !== 'trend_parent') ||
    !row.key ||
    !row.expandKind
  ) {
    return
  }
  const k = expandKey(row.key, row.expandKind)
  nextExpandState.value = {
    ...nextExpandState.value,
    [k]: !(nextExpandState.value[k] ?? row.metric === 'trend_parent'),
  }
}

function onMatrixRowDblClick(row: MatrixRow) {
  if (!row.key || row.key === '__demand__' || row.key === 'inventory_trend') return
  if (
    row.metric === 'next_usage_parent' ||
    row.metric === 'next_usage_child' ||
    row.metric === 'next_consume_parent' ||
    row.metric === 'next_consume_child' ||
    row.metric === 'trend_parent' ||
    row.metric === 'trend_child'
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
  if (!row.key || row.key === '__demand__' || row.key === 'inventory_trend') return
  if (
    row.metric === 'next_usage_parent' ||
    row.metric === 'next_usage_child' ||
    row.metric === 'next_consume_parent' ||
    row.metric === 'next_consume_child' ||
    row.metric === 'trend_parent' ||
    row.metric === 'trend_child'
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
        return [ym, res.data.groups, res.data.inventory_trend_rows || []] as const
      }),
    )
    const next: Record<string, ProjectionGroup[]> = {}
    const nextTrend: Record<string, InventoryTrendRow[]> = {}
    for (const [ym, groups, trend] of results) {
      next[ym] = groups
      nextTrend[ym] = trend
    }
    // 対象月は最新の summary を優先
    if (summary.value?.groups?.length) next[targetMonth.value] = summary.value.groups
    if (summary.value?.inventory_trend_rows?.length) {
      nextTrend[targetMonth.value] = summary.value.inventory_trend_rows
    }
    monthlyByYm.value = next
    monthlyTrendByYm.value = nextTrend
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
    // デフォルト: 在庫推移の子行（成型／メッキ／溶接／検査）
    const trendIds = rows
      .filter((row) => row.metric === 'trend_child')
      .map(matrixRowId)
      .slice(0, MATRIX_CHART_MAX_SERIES)
    selectedMatrixRowIds.value = trendIds.length
      ? trendIds
      : rows
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
    if (summary.value?.inventory_trend_rows?.length) {
      monthlyTrendByYm.value = {
        ...monthlyTrendByYm.value,
        [targetMonth.value]: summary.value.inventory_trend_rows,
      }
    }
    syncMatrixRowSelection()
    if (matrixTab.value === 'monthly') {
      await loadMonthlySummaries(force)
    }
    await nextTick()
    renderMatrixChart()
  } catch (e: any) {
    const msg = e?.response?.data?.detail || e?.message || '読み込みに失敗しました'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
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
  trend_child: '#2563eb',
  demand: '#ef4444',
}

function matrixSeriesColor(row: MatrixRow, index: number): string {
  // 在庫は図例どおり青系。複数行比較時は工程色で差を付ける
  if (isInventoryMetric(row)) {
    const selectedInv = selectedMatrixRows.value.filter(isInventoryMetric)
    if (selectedInv.length <= 1) return MATRIX_METRIC_COLORS.inventory || '#2563eb'
    return GROUP_COLORS[row.key] || MATRIX_METRIC_COLORS.inventory || '#2563eb'
  }
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
        width: row.metric === 'inventory' || row.metric === 'trend_child' ? 3.2 : 2.2,
        type: row.metric === 'actual' ? ('dashed' as const) : ('solid' as const),
        shadowColor: `${color}40`,
        shadowBlur: 8,
        shadowOffsetY: 3,
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
        seriesCount === 1 && (row.metric === 'inventory' || row.metric === 'trend_child')
          ? {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: `${color}38` },
                { offset: 1, color: `${color}03` },
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
  matrixChart?.dispose()
  matrixChart = null
})
</script>

<style scoped>
.inventory-projection-page {
  --surface: #ffffff;
  --ink: #152033;
  --muted: #64748b;
  --line: #e2e8f0;
  --plan: #16a34a;
  --actual: #64748b;
  --next: #d97706;
  --inv: #2563eb;
  --consume: #7c3aed;
  min-height: 100%;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background:
    radial-gradient(ellipse 55% 40% at 6% -8%, rgba(79, 107, 216, 0.14), transparent 55%),
    radial-gradient(ellipse 45% 35% at 96% 0%, rgba(139, 91, 181, 0.1), transparent 50%),
    radial-gradient(ellipse 40% 30% at 50% 100%, rgba(46, 158, 120, 0.06), transparent 45%),
    linear-gradient(180deg, #eef2f8 0%, #f5f7fb 48%, #f8fafc 100%);
}

:deep(.el-card) {
  border: 1px solid rgba(226, 232, 240, 0.95);
  border-radius: 16px;
  background: var(--surface);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 10px 28px rgba(15, 23, 42, 0.06),
    0 2px 6px rgba(15, 23, 42, 0.03);
}

:deep(.el-card__header) {
  padding: 15px 18px;
  border-bottom-color: #eef2f7;
  background: linear-gradient(180deg, #ffffff 0%, #fbfcfe 100%);
  border-radius: 16px 16px 0 0;
}

.toolbar-card {
  background:
    linear-gradient(125deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 251, 255, 0.96) 58%, rgba(245, 243, 255, 0.94) 100%);
  backdrop-filter: blur(8px);
}

:deep(.toolbar-card .el-card__body) {
  padding: 16px 18px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-title {
  font-size: 22px;
  font-weight: 780;
  letter-spacing: 0.03em;
  color: var(--ink);
  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.8);
}

.product-count-tag {
  border-color: #bfdbfe !important;
  background: linear-gradient(180deg, #eff6ff, #dbeafe) !important;
  color: #1d4ed8 !important;
  font-weight: 650;
  border-radius: 999px;
  box-shadow: 0 2px 6px rgba(37, 99, 235, 0.12);
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
  font-size: 12.5px;
  line-height: 1.65;
}

.help-content p {
  margin: 0 0 10px;
}

.help-content.compact p {
  margin: 0 0 6px;
}

.help-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid #dbeafe;
  font-size: 15px;
  font-weight: 750;
  color: #0f172a;
}

.help-title-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 25px;
  height: 25px;
  border-radius: 8px;
  background: linear-gradient(135deg, #2563eb, #4f46e5);
  color: #fff;
  font-family: Georgia, serif;
  font-size: 15px;
  font-weight: 700;
  box-shadow: 0 4px 10px rgba(37, 99, 235, 0.2);
}

.help-intro {
  padding: 9px 11px;
  border: 1px solid #dbeafe;
  border-radius: 9px;
  background: #eff6ff;
  color: #334155;
}

.help-section {
  margin-top: 11px;
  padding: 10px 11px 7px;
  border: 1px solid;
  border-radius: 10px;
}

.help-section-inventory {
  border-color: #d1fae5;
  background: #f0fdf4;
}

.help-section-trend {
  border-color: #ede9fe;
  background: #f5f3ff;
}

.help-subtitle {
  display: flex;
  align-items: center;
  gap: 7px;
  margin: 0 0 7px;
  font-size: 12.5px;
  font-weight: 750;
  color: #1e293b;
}

.help-subtitle-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.13);
}

.help-section-trend .help-subtitle-dot {
  background: #8b5cf6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.13);
}

.help-formula-list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.help-formula-list li {
  position: relative;
  margin-bottom: 5px;
  padding: 5px 8px 5px 11px;
  border-left: 3px solid #86efac;
  border-radius: 0 6px 6px 0;
  background: rgba(255, 255, 255, 0.72);
}

.help-section-trend .help-formula-list li {
  border-left-color: #c4b5fd;
}

.help-formula-list strong {
  display: inline-block;
  min-width: 74px;
  color: #047857;
}

.help-section-trend .help-formula-list strong {
  color: #6d28d9;
}

.help-note {
  margin: 8px 0 2px !important;
  padding: 7px 9px;
  border-radius: 7px;
  background: #ecfdf5;
  color: #047857;
  font-size: 11.5px;
}

.help-operation {
  margin: 11px 0 0 !important;
  padding: 8px 10px;
  border-left: 3px solid #f59e0b;
  border-radius: 0 7px 7px 0;
  background: #fffbeb;
  color: #92400e;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 12px;
  background: rgba(248, 250, 252, 0.85);
  border: 1px solid rgba(226, 232, 240, 0.9);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.toolbar-right .label {
  font-size: 12px;
  font-weight: 650;
  color: var(--muted);
}

.kpi-row {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 12px;
}

.kpi-card {
  position: relative;
  overflow: hidden;
  isolation: isolate;
  background:
    linear-gradient(165deg, color-mix(in srgb, var(--group-color) 8%, #fff) 0%, #fff 42%, #fff 100%);
  border: 1px solid color-mix(in srgb, var(--group-color) 22%, #e8edf5);
  border-radius: 14px;
  padding: 14px 14px 12px;
  cursor: pointer;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 8px 20px color-mix(in srgb, var(--group-color) 12%, transparent),
    0 3px 8px rgba(15, 23, 42, 0.04);
  transition:
    transform 0.2s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.2s ease,
    border-color 0.2s ease;
}

.kpi-glow {
  position: absolute;
  top: -40%;
  right: -20%;
  width: 70%;
  height: 90%;
  border-radius: 50%;
  background: radial-gradient(circle, color-mix(in srgb, var(--group-color) 28%, transparent), transparent 68%);
  pointer-events: none;
  z-index: 0;
}

.kpi-accent {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background: linear-gradient(
    90deg,
    var(--group-color),
    color-mix(in srgb, var(--group-color) 55%, #fff)
  );
  z-index: 1;
}

.kpi-accent::after {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  height: 100vh;
  background: var(--group-color);
  box-shadow: 2px 0 10px color-mix(in srgb, var(--group-color) 35%, transparent);
}

.kpi-top,
.kpi-value,
.kpi-sub {
  position: relative;
  z-index: 1;
}

.kpi-top {
  display: flex;
  align-items: center;
  gap: 7px;
}

.kpi-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--group-color);
  box-shadow:
    0 0 0 3px color-mix(in srgb, var(--group-color) 18%, transparent),
    0 2px 6px color-mix(in srgb, var(--group-color) 45%, transparent);
}

.kpi-card:hover {
  border-color: color-mix(in srgb, var(--group-color) 55%, #fff);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 16px 32px color-mix(in srgb, var(--group-color) 22%, transparent),
    0 6px 14px rgba(15, 23, 42, 0.08);
  transform: translateY(-4px) scale(1.01);
}

.kpi-card.negative {
  --group-color: #f56c6c;
  border-color: #fca5a5;
  background: linear-gradient(165deg, #fff5f5 0%, #fff 55%);
}

.kpi-name {
  font-size: 12px;
  color: color-mix(in srgb, var(--group-color) 35%, #64748b);
  font-weight: 700;
  letter-spacing: 0.02em;
}

.kpi-value {
  margin: 8px 0 8px;
  color: var(--ink);
  font-size: 23px;
  font-weight: 780;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.02em;
}

.kpi-card.negative .kpi-value {
  color: #dc2626;
}

.kpi-unit {
  font-size: 11px;
  font-weight: 500;
  color: #94a3b8;
  margin-left: 3px;
}

.kpi-sub {
  display: flex;
  justify-content: space-between;
  gap: 6px;
  font-size: 11px;
  color: #94a3b8;
  padding-top: 8px;
  border-top: 1px dashed color-mix(in srgb, var(--group-color) 18%, #e2e8f0);
}

.kpi-sub .warn {
  color: #d97706;
  font-weight: 700;
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
  color: var(--ink);
  font-size: 15px;
  font-weight: 750;
  letter-spacing: 0.02em;
}

.matrix-legend {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 8px;
  border-radius: 999px;
  background: #f8fafc;
  border: 1px solid #e8edf4;
  color: var(--muted);
  font-size: 11px;
  font-weight: 600;
}

.matrix-legend span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 2px 7px;
  border-radius: 999px;
}

.legend-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.9);
}

.legend-dot.inventory {
  background: var(--inv);
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.15);
}
.legend-dot.plan {
  background: var(--plan);
  box-shadow: 0 0 0 2px rgba(22, 163, 74, 0.15);
}
.legend-dot.actual {
  background: #94a3b8;
  box-shadow: 0 0 0 2px rgba(148, 163, 184, 0.2);
}
.legend-dot.next {
  background: var(--next);
  box-shadow: 0 0 0 2px rgba(217, 119, 6, 0.15);
}

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
  color: #64748b;
}

:deep(.matrix-tabs .el-tabs__item.is-active) {
  color: #1d4ed8;
  font-weight: 750;
}

:deep(.matrix-tabs .el-tabs__active-bar) {
  height: 3px;
  border-radius: 3px 3px 0 0;
  background: linear-gradient(90deg, #2563eb, #7c3aed);
}

:deep(.matrix-tabs .el-tabs__nav-wrap::after) {
  height: 1px;
  background-color: #e8edf4;
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
  color: #1d4ed8;
  cursor: pointer;
  font-weight: 700;
}

.process-link:hover {
  color: #2563eb;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.process-header {
  font-weight: 750;
  color: color-mix(in srgb, var(--row-accent, #334155) 75%, #0f172a);
}

.process-metric {
  color: #64748b;
  font-size: 12px;
}

.toolbar-right :deep(.el-button--primary) {
  border: none;
  background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);
  box-shadow: 0 6px 14px rgba(37, 99, 235, 0.28);
  font-weight: 700;
}

.toolbar-right :deep(.el-button--primary:hover) {
  background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%);
  box-shadow: 0 8px 18px rgba(37, 99, 235, 0.35);
  transform: translateY(-1px);
}

.projected {
  color: var(--inv);
  font-weight: 600;
}

.projected-header {
  color: var(--inv);
  background: linear-gradient(180deg, #eff6ff, #dbeafe) !important;
}

.negative {
  color: #dc2626;
  font-weight: 700;
}

.metric-inventory {
  color: var(--inv);
  font-weight: 600;
}

.metric-plan {
  color: var(--plan);
  font-weight: 600;
}

.plan-overridden {
  color: #b45309;
  font-weight: 750;
  background: linear-gradient(180deg, #fffbeb, #fef3c7);
  border-radius: 4px;
  padding: 1px 4px;
  box-shadow: inset 0 0 0 1px rgba(245, 158, 11, 0.25);
}

.plan-edit-hint {
  margin-bottom: 10px;
  padding: 9px 12px;
  background: linear-gradient(90deg, #f8fafc, #f1f5f9);
  border: 1px solid #e2e8f0;
  border-left: 3px solid #94a3b8;
  border-radius: 8px;
  color: #64748b;
  font-size: 12px;
  line-height: 1.7;
}

.metric-actual {
  color: var(--actual);
}

.metric-next {
  color: var(--next);
  font-weight: 600;
}

:deep(.group-header-row) {
  --row-accent: #64748b;
  background: linear-gradient(
    90deg,
    color-mix(in srgb, var(--row-accent) 14%, #fff),
    color-mix(in srgb, var(--row-accent) 4%, #fff) 55%,
    #fff 100%
  );
}

:deep(.group-header-row td) {
  border-top: 1px solid color-mix(in srgb, var(--row-accent) 22%, #e2e8f0);
  font-weight: 750;
}

:deep(.group-header-row td:first-child) {
  box-shadow:
    inset 5px 0 var(--row-accent),
    inset 0 -1px 0 color-mix(in srgb, var(--row-accent) 12%, transparent);
}

:deep(.inventory-row) {
  background: linear-gradient(90deg, #f0f7ff 0%, #f8fbff 40%, #fff 100%);
}

:deep(.inventory-row td:first-child) {
  box-shadow: inset 3px 0 color-mix(in srgb, var(--row-accent, var(--inv)) 70%, transparent);
}

:deep(.plan-row) {
  background: linear-gradient(90deg, #f3fbf4 0%, #f9fdf9 45%, #fff 100%);
}

:deep(.actual-row) {
  background: linear-gradient(90deg, #f8fafc 0%, #fcfcfd 50%, #fff 100%);
}

:deep(.next-usage-row) {
  background: linear-gradient(90deg, #fff7ed 0%, #fffaf3 50%, #fff 100%);
}

:deep(.next-usage-child-row) {
  background: #fffbf5;
}

:deep(.next-consume-row) {
  background: linear-gradient(90deg, #f5f3ff 0%, #faf8ff 50%, #fff 100%);
}

:deep(.next-consume-child-row) {
  background: #faf8ff;
}

:deep(.trend-parent-row) {
  background: linear-gradient(90deg, #dbeafe 0%, #eff6ff 45%, #f8fbff 100%);
  font-weight: 700;
}

:deep(.trend-parent-row td:first-child) {
  box-shadow: inset 5px 0 var(--inv);
}

:deep(.group-cutting) {
  --row-accent: #4f6bd8;
}
:deep(.group-molding) {
  --row-accent: #4caf50;
}
:deep(.group-plating_inhouse) {
  --row-accent: #e6a23c;
}
:deep(.group-plating_outsource) {
  --row-accent: #f05656;
}
:deep(.group-welding_inhouse) {
  --row-accent: #3aa0c4;
}
:deep(.group-welding_outsource) {
  --row-accent: #f07a3a;
}
:deep(.group-inspection) {
  --row-accent: #2f9e78;
}
:deep(.group-warehouse) {
  --row-accent: #8b5bb5;
}
:deep(.group-inventory_trend) {
  --row-accent: #2563eb;
}

.expand-icon {
  display: inline-block;
  width: 1em;
  margin-right: 2px;
  font-size: 10px;
  color: #d97706;
  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.8);
}

.next-parent-label {
  font-weight: 700;
}

.next-child-label {
  color: #64748b;
  font-size: 12px;
}

:deep(.el-table .cell) {
  padding: 0 6px;
}

:deep(.matrix-card .el-table) {
  --el-table-border-color: #e8edf4;
  --el-table-header-bg-color: #f1f5f9;
  --el-table-row-hover-bg-color: #eff6ff;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.8) inset;
}

:deep(.matrix-card .el-table th.el-table__cell) {
  height: 40px;
  color: #334155;
  font-weight: 700;
  background: linear-gradient(180deg, #f8fafc, #eef2f7) !important;
}

:deep(.matrix-card .el-table td.el-table__cell) {
  height: 34px;
}

.matrix-chart-panel {
  margin-top: 16px;
  padding: 16px 16px 8px;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  background:
    radial-gradient(ellipse 60% 50% at 10% 0%, rgba(37, 99, 235, 0.05), transparent 55%),
    linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 8px 22px rgba(15, 23, 42, 0.045);
}

.matrix-chart-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eef2f7;
}

.matrix-chart-title {
  color: var(--ink);
  font-size: 14px;
  font-weight: 750;
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

@media (max-width: 1100px) {
  .kpi-row {
    grid-template-columns: repeat(3, 1fr);
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
