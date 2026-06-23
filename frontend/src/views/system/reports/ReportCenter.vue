<template>
  <div class="rc-page" v-loading="pageLoading">
    <header class="rc-top">
      <div class="rc-top__brand">
        <el-icon :size="18"><Document /></el-icon>
        <div>
          <h1 class="rc-top__title">報告センター</h1>
          <span class="rc-top__desc">各種レポートの生成・手動配信・定時配信・送信履歴</span>
        </div>
      </div>
      <el-button :icon="Refresh" circle size="small" :loading="pageLoading" @click="loadAll" />
    </header>

    <nav class="rc-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.name"
        type="button"
        class="rc-tab"
        :class="{ 'rc-tab--active': activeTab === tab.name }"
        @click="activeTab = tab.name"
      >
        <el-icon :size="14"><component :is="tab.icon" /></el-icon>
        {{ tab.label }}
      </button>
    </nav>

    <!-- 配信（手動） -->
    <section v-show="activeTab === 'send'" class="rc-panel">
      <div class="rc-layout">
        <aside class="rc-list">
          <article
            v-for="d in definitions"
            :key="d.report_code"
            class="rc-def"
            :class="{ 'rc-def--active': selected?.report_code === d.report_code }"
            @click="selectDefinition(d)"
          >
            <span class="rc-def__cat">{{ d.category }}</span>
            <h3 class="rc-def__name">{{ d.report_name }}</h3>
            <p class="rc-def__desc">{{ d.description || '—' }}</p>
          </article>
          <el-empty v-if="!definitions.length" description="レポート定義がありません" :image-size="60" />
        </aside>

        <div class="rc-detail" v-if="selected">
          <h2 class="rc-detail__title">{{ selected.report_name }}</h2>

          <div class="rc-form">
            <div v-for="field in selectedFields" :key="field.key" class="rc-field">
              <label class="rc-field__label">{{ field.label }}</label>
              <template v-if="field.type === 'date_range'">
                <el-select v-model="paramState[field.key]" size="small" style="width: 160px">
                  <el-option
                    v-for="p in field.presets || []"
                    :key="p"
                    :label="presetLabel(p)"
                    :value="p"
                  />
                </el-select>
                <el-date-picker
                  v-if="paramState[field.key] === 'custom'"
                  v-model="customRange"
                  type="daterange"
                  size="small"
                  value-format="YYYY-MM-DD"
                  range-separator="〜"
                  start-placeholder="開始日"
                  end-placeholder="終了日"
                  style="margin-left: 8px"
                />
              </template>
              <template v-else-if="field.type === 'month'">
                <el-select v-model="paramState[field.key]" size="small" style="width: 160px">
                  <el-option label="先月" value="last_month" />
                  <el-option label="今月" value="this_month" />
                  <el-option label="指定月" value="custom" />
                </el-select>
                <el-date-picker
                  v-if="paramState[field.key] === 'custom'"
                  v-model="customMonth"
                  type="month"
                  size="small"
                  value-format="YYYY-MM"
                  placeholder="基準月"
                  style="margin-left: 8px"
                />
              </template>
            </div>
          </div>

          <div class="rc-actions">
            <el-select v-model="sendFormat" size="small" style="width: 110px">
              <el-option label="Excel" value="xlsx" />
              <el-option label="PDF" value="pdf" />
              <el-option label="両方" value="both" />
            </el-select>
            <el-button :icon="View" size="small" :loading="previewLoading" @click="doPreview">プレビュー</el-button>
            <el-button :icon="Download" size="small" @click="doDownload">ダウンロード</el-button>
            <el-button
              type="primary"
              :icon="Promotion"
              size="small"
              :loading="sendLoading"
              :disabled="!preview?.can_send"
              @click="doSend"
            >
              送信
            </el-button>
          </div>

            <div v-if="preview" class="rc-preview">
            <div class="rc-preview__meta">
              <span>対象期間: <b>{{ preview.period_label }}</b></span>
              <span>件数: <b>{{ preview.record_count }}</b></span>
              <span>形式: <b>{{ preview.format }}</b></span>
              <span>添付: <b>{{ preview.attachments.map((a) => a.filename).join(', ') || '—' }}</b></span>
            </div>

            <div class="rc-preview__recipients">
              <div>
                <span class="rc-tag rc-tag--mail">メール {{ preview.recipient_count }} 名</span>
                <span class="rc-tag rc-tag--line">LINE {{ preview.line_recipient_count }} 名</span>
                <span v-if="!preview.email_enabled && !preview.line_enabled" class="rc-tag rc-tag--warn">
                  通知イベントが無効です（通知センターで有効化してください）
                </span>
                <span v-else-if="!preview.can_send" class="rc-tag rc-tag--warn">
                  送信できません（SMTP/LINE 設定・受信者を確認してください）
                </span>
              </div>
              <ul class="rc-recipients">
                <li v-for="r in preview.recipients" :key="r.email">{{ r.name }} &lt;{{ r.email }}&gt;</li>
              </ul>
            </div>

            <!-- 切断工程実績レポート: A4 横向きチャートプレビュー -->
            <div
              v-if="isCuttingReportPreview"
              class="rc-a4-preview"
            >
              <div class="rc-a4-sheet rc-a4-sheet--landscape">
                <header class="rc-a4-sheet__head">
                  <h3 class="rc-a4-sheet__title">切断工程実績レポート</h3>
                  <p class="rc-a4-sheet__period">対象期間: {{ preview.period_label }}</p>
                </header>

                <section class="rc-a4-section">
                  <h4 class="rc-a4-section__title">
                    切断済在庫推移（日次・単位: 千・レットライン在庫: {{ formatInventoryThousand(INVENTORY_LETTER_LINE) }}）
                  </h4>
                  <div class="rc-a4-chart-wrap">
                    <p v-if="inventoryLetterLineWarning" class="rc-a4-chart-comment">
                      {{ inventoryLetterLineWarning }}
                    </p>
                    <div ref="inventoryChartRef" class="rc-a4-chart" />
                  </div>
                </section>

                <section class="rc-a4-section">
                  <h4 class="rc-a4-section__title">
                    切断工程 計画 vs 実績（日次・単位: 千・計画&gt;実績は赤−／実績&gt;計画は青+）
                  </h4>
                  <div ref="planActualChartRef" class="rc-a4-chart rc-a4-chart--bar" />
                </section>

                <footer v-if="cuttingReportSummary" class="rc-a4-summary">
                  <h4 class="rc-a4-summary__heading">データサマリー（単位: 千）</h4>
                  <div class="rc-a4-summary__block">
                    <span class="rc-a4-summary__block-title">切断工程</span>
                    <div class="rc-a4-summary__grid">
                      <div class="rc-a4-summary__item">
                        <span class="rc-a4-summary__label">計画合計</span>
                        <b class="rc-a4-summary__value">{{ formatInventoryThousand(cuttingReportSummary.totalPlan) }}</b>
                      </div>
                      <div class="rc-a4-summary__item">
                        <span class="rc-a4-summary__label">実績合計</span>
                        <b class="rc-a4-summary__value">{{ formatInventoryThousand(cuttingReportSummary.totalActual) }}</b>
                      </div>
                      <div class="rc-a4-summary__item">
                        <span class="rc-a4-summary__label">計画残数</span>
                        <b
                          class="rc-a4-summary__value"
                          :class="cuttingReportSummary.planRemaining <= 0 ? 'rc-a4-summary__value--pos' : 'rc-a4-summary__value--neg'"
                        >{{ formatPlanRemainingThousand(cuttingReportSummary.planRemaining) }}</b>
                      </div>
                      <div class="rc-a4-summary__item">
                        <span class="rc-a4-summary__label">進捗率</span>
                        <b class="rc-a4-summary__value">{{ formatProgressRate(cuttingReportSummary.totalPlan, cuttingReportSummary.totalActual) }}</b>
                      </div>
                      <div class="rc-a4-summary__item">
                        <span class="rc-a4-summary__label">累計差異</span>
                        <b
                          class="rc-a4-summary__value"
                          :class="cuttingReportSummary.baselineActualDiff != null && cuttingReportSummary.baselineActualDiff >= 0 ? 'rc-a4-summary__value--pos' : cuttingReportSummary.baselineActualDiff != null ? 'rc-a4-summary__value--neg' : ''"
                        >
                          {{ formatBaselineActualDiff(cuttingReportSummary.baselineActualDiff) }}
                          <small
                            v-if="cuttingReportSummary.baselineDiffDateLabel"
                            class="rc-a4-summary__sub"
                          >（{{ cuttingReportSummary.baselineDiffDateLabel }}）</small>
                        </b>
                      </div>
                    </div>
                  </div>
                  <div class="rc-a4-summary__block">
                    <span class="rc-a4-summary__block-title">切断済在庫</span>
                    <div class="rc-a4-summary__grid rc-a4-summary__grid--inv">
                      <div class="rc-a4-summary__item">
                        <span class="rc-a4-summary__label">期末予測在庫</span>
                        <b class="rc-a4-summary__value">
                          {{ formatInventoryThousand(cuttingReportSummary.invLatest) }}
                          <small
                            v-if="cuttingReportSummary.invLatestDateLabel"
                            class="rc-a4-summary__sub"
                          >（{{ cuttingReportSummary.invLatestDateLabel }}）</small>
                        </b>
                      </div>
                      <div class="rc-a4-summary__item">
                        <span class="rc-a4-summary__label">期間ピーク</span>
                        <b class="rc-a4-summary__value">
                          {{ formatInventoryThousand(cuttingReportSummary.invPeak) }}
                          <small class="rc-a4-summary__sub">（{{ cuttingReportSummary.invPeakLabel }}）</small>
                        </b>
                      </div>
                      <div class="rc-a4-summary__item">
                        <span class="rc-a4-summary__label">期間平均</span>
                        <b class="rc-a4-summary__value">{{ formatInventoryThousand(cuttingReportSummary.invAvg) }}</b>
                      </div>
                    </div>
                  </div>
                </footer>
              </div>
            </div>

            <div v-else class="rc-preview__summary" v-html="preview.summary_html" />
          </div>
        </div>
        <el-empty v-else description="レポートを選択してください" />
      </div>
    </section>

    <!-- スケジュール -->
    <section v-show="activeTab === 'schedule'" class="rc-panel">
      <div class="rc-panel__head">
        <h2 class="rc-panel__title">定時配信スケジュール</h2>
        <el-button type="primary" :icon="Plus" size="small" @click="openScheduleDialog()">新規追加</el-button>
      </div>
      <el-table :data="schedules" size="small" border>
        <el-table-column label="レポート" min-width="160">
          <template #default="{ row }">{{ definitionName(row.report_code) }}</template>
        </el-table-column>
        <el-table-column label="頻度" width="120">
          <template #default="{ row }">{{ scheduleTypeLabel(row) }}</template>
        </el-table-column>
        <el-table-column prop="schedule_time" label="時刻" width="90" />
        <el-table-column label="形式" width="80">
          <template #default="{ row }">{{ row.format || '既定' }}</template>
        </el-table-column>
        <el-table-column label="有効" width="80">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_active"
              size="small"
              @change="(v) => onScheduleActiveChange(row, v)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="last_run_at" label="最終実行" width="160" />
        <el-table-column prop="next_run_at" label="次回予定" width="160" />
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openScheduleDialog(row)">編集</el-button>
            <el-button link type="danger" size="small" @click="removeSchedule(row)">削除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <!-- 送信履歴 -->
    <section v-show="activeTab === 'logs'" class="rc-panel">
      <div class="rc-panel__head">
        <h2 class="rc-panel__title">送信履歴</h2>
        <el-button :icon="Refresh" size="small" @click="loadLogs">更新</el-button>
      </div>
      <el-table :data="logs" size="small" border>
        <el-table-column label="レポート" min-width="160">
          <template #default="{ row }">{{ definitionName(row.report_code) }}</template>
        </el-table-column>
        <el-table-column prop="trigger_type" label="種別" width="90" />
        <el-table-column prop="status" label="状態" width="90">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="recipient_count" label="対象" width="70" />
        <el-table-column prop="success_count" label="成功" width="70" />
        <el-table-column prop="file_name" label="ファイル" min-width="160" />
        <el-table-column prop="message" label="メッセージ" min-width="180" />
        <el-table-column prop="created_at" label="日時" width="160" />
      </el-table>
    </section>

    <!-- スケジュール編集ダイアログ -->
    <el-dialog v-model="scheduleDialog" :title="editingSchedule.id ? 'スケジュール編集' : 'スケジュール追加'" width="460px">
      <el-form label-width="90px">
        <el-form-item label="レポート">
          <el-select v-model="editingSchedule.report_code" :disabled="!!editingSchedule.id" style="width: 100%">
            <el-option v-for="d in definitions" :key="d.report_code" :label="d.report_name" :value="d.report_code" />
          </el-select>
        </el-form-item>
        <el-form-item label="頻度">
          <el-select v-model="editingSchedule.schedule_type" style="width: 100%">
            <el-option label="毎日" value="daily" />
            <el-option label="毎週" value="weekly" />
            <el-option label="毎月" value="monthly" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="editingSchedule.schedule_type === 'weekly'" label="曜日">
          <el-select v-model="weekdayValue" style="width: 100%">
            <el-option v-for="(w, i) in weekdays" :key="i" :label="w" :value="i" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="editingSchedule.schedule_type === 'monthly'" label="実行日">
          <el-input-number v-model="monthDayValue" :min="1" :max="31" />
        </el-form-item>
        <el-form-item label="時刻">
          <el-time-picker v-model="scheduleTimeValue" format="HH:mm" value-format="HH:mm:ss" style="width: 100%" />
        </el-form-item>
        <el-form-item label="形式">
          <el-select v-model="editingSchedule.format" clearable placeholder="既定" style="width: 100%">
            <el-option label="Excel" value="xlsx" />
            <el-option label="PDF" value="pdf" />
            <el-option label="両方" value="both" />
          </el-select>
        </el-form-item>
        <el-form-item label="対象期間">
          <el-select v-model="scheduleDateRange" style="width: 100%">
            <el-option v-for="p in scheduleRangePresets" :key="p" :label="presetLabel(p)" :value="p" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="scheduleDialog = false">キャンセル</el-button>
        <el-button type="primary" :loading="savingSchedule" @click="saveSchedule">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, Download, Plus, Promotion, Refresh, View } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'
import {
  createReportSchedule,
  deleteReportSchedule,
  downloadReport,
  fetchReportDefinitions,
  fetchReportSchedules,
  fetchReportSendLogs,
  previewReport,
  sendReport,
  updateReportSchedule,
  type CuttingReportChartData,
  type ReportDefinition,
  type ReportParameterField,
  type ReportPreview,
  type ReportSchedule,
  type ReportSendLog,
} from '@/api/reports'

const tabs = [
  { name: 'send', label: '配信（手動）', icon: Promotion },
  { name: 'schedule', label: 'スケジュール', icon: Refresh },
  { name: 'logs', label: '送信履歴', icon: Document },
]
const activeTab = ref('send')
const pageLoading = ref(false)

const definitions = ref<ReportDefinition[]>([])
const selected = ref<ReportDefinition | null>(null)
const paramState = reactive<Record<string, string>>({})
const customRange = ref<[string, string] | null>(null)
const customMonth = ref<string | null>(null)

const preview = ref<ReportPreview | null>(null)
const previewLoading = ref(false)
const sendLoading = ref(false)
const sendFormat = ref('xlsx')

const inventoryChartRef = ref<HTMLDivElement | null>(null)
const planActualChartRef = ref<HTMLDivElement | null>(null)
let inventoryChart: ECharts | null = null
let planActualChart: ECharts | null = null

const CHART_PRIMARY = '#2563EB'
const CHART_ACCENT = '#10B981'
const CHART_AXIS = '#94A3B8'
const CHART_GRID = '#E2E8F0'
const INVENTORY_LETTER_LINE = 142000
const INVENTORY_UNIT_THOUSAND = 1000
const CUTTING_REPORT_CODE = 'CUTTING_DAILY_ACTUAL'
const CUTTING_DEFAULT_FORMAT = 'pdf'
const CUTTING_DEFAULT_DATE_RANGE = 'this_month'

function toInventoryThousand(value: number): number {
  return Math.round((value / INVENTORY_UNIT_THOUSAND) * 10) / 10
}

function formatInventoryThousand(value: number): string {
  const thousand = toInventoryThousand(value)
  return Number.isInteger(thousand) ? `${thousand}` : thousand.toFixed(1)
}

function formatPlanRemainingThousand(value: number): string {
  const thousand = toInventoryThousand(value)
  return Number.isInteger(thousand) ? `${thousand}` : thousand.toFixed(1)
}

function formatDiffThousand(value: number): string {
  const thousand = toInventoryThousand(value)
  const formatted = Number.isInteger(thousand) ? `${thousand}` : thousand.toFixed(1)
  if (value > 0) return `+${formatted}`
  return formatted
}

function formatChartDiffLabel(planThousand: number, actualThousand: number): string {
  const gap = Math.round((planThousand - actualThousand) * 10) / 10
  const absText = Number.isInteger(Math.abs(gap)) ? `${Math.abs(gap)}` : Math.abs(gap).toFixed(1)
  if (gap > 0) {
    // 計画 > 実績：赤・マイナス
    return `{diffNeg|-${absText}}`
  }
  if (gap < 0) {
    // 実績 > 計画：青・プラス
    return `{diffPos|+${absText}}`
  }
  return `{diffPos|0}`
}

const CHART_DIFF_LABEL_RICH = {
  diffPos: { color: '#1D4ED8', fontSize: 9, fontWeight: 600 as const },
  diffNeg: { color: '#DC2626', fontSize: 9, fontWeight: 600 as const },
}

function formatChartDiffTooltip(planRaw: number, actualRaw: number): string {
  const gapThousand = toInventoryThousand(planRaw - actualRaw)
  const absText = Number.isInteger(Math.abs(gapThousand))
    ? `${Math.abs(gapThousand)}`
    : Math.abs(gapThousand).toFixed(1)
  if (gapThousand > 0) return `-${absText}`
  if (gapThousand < 0) return `+${absText}`
  return '0'
}

function formatProgressRate(plan: number, actual: number): string {
  if (!plan) return '—'
  return `${(actual / plan * 100).toFixed(1)}%`
}

function formatBaselineActualDiff(value: number | null | undefined): string {
  if (value == null) return '—'
  return formatDiffThousand(value)
}

function formatSummaryDateLabel(iso: string | undefined): string {
  if (!iso) return ''
  const m = iso.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (!m) return iso
  return `${m[1]}-${m[2]}-${m[3]}`
}

function resolveBaselineDiffAsOfDate(periodEnd: string | undefined): string {
  if (!periodEnd) return ''
  const today = new Date()
  const todayIso = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
  return periodEnd <= todayIso ? periodEnd : todayIso
}

interface CuttingReportSummaryStats {
  totalPlan: number
  totalActual: number
  planRemaining: number
  baselineActualDiff: number | null
  baselineDiffDateLabel: string
  invLatest: number
  invLatestDateLabel: string
  invPeak: number
  invPeakLabel: string
  invAvg: number
}

function resolveTodayInventoryValue(
  days: string[] | undefined,
  labels: string[],
  values: number[],
): number | null {
  const now = new Date()
  const todayIso = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
  if (days?.length) {
    const idx = days.indexOf(todayIso)
    if (idx >= 0) return values[idx] ?? null
    return null
  }
  const mmdd = `${String(now.getMonth() + 1).padStart(2, '0')}/${String(now.getDate()).padStart(2, '0')}`
  const idx = labels.indexOf(mmdd)
  if (idx >= 0) return values[idx] ?? null
  return null
}

const inventoryLetterLineWarning = computed(() => {
  const data = preview.value?.chart_data
  if (!data) return null

  const { values, days, labels } = data.inventory_trend
  const todayInv = resolveTodayInventoryValue(days, labels, values)
  if (todayInv == null || todayInv >= INVENTORY_LETTER_LINE) return null

  const todayThousand = formatInventoryThousand(todayInv)
  const lineThousand = formatInventoryThousand(INVENTORY_LETTER_LINE)
  const gapThousand = formatInventoryThousand(INVENTORY_LETTER_LINE - todayInv)
  return `※ 本日在庫（${todayThousand}）がレットライン（${lineThousand}）を下回り、危険水域です（不足 ${gapThousand}）`
})

const cuttingReportSummary = computed<CuttingReportSummaryStats | null>(() => {
  const data = preview.value?.chart_data
  if (!data) return null

  const { plan, actual, labels } = data.plan_actual
  const { values, days } = data.inventory_trend
  const periodEnd = data.period_end

  const totalPlan = plan.reduce((sum, v) => sum + v, 0)
  const totalActual = actual.reduce((sum, v) => sum + v, 0)
  const planRemaining = totalPlan - totalActual

  let invPeak = 0
  let invPeakIdx = 0
  values.forEach((v, i) => {
    if (v > invPeak) {
      invPeak = v
      invPeakIdx = i
    }
  })
  const invSum = values.reduce((sum, v) => sum + v, 0)
  const invLatestIdx = Math.max(values.length - 1, 0)
  const invLatestDay = days?.[invLatestIdx] ?? periodEnd

  return {
    totalPlan,
    totalActual,
    planRemaining,
    baselineActualDiff: data.baseline_actual_diff ?? null,
    baselineDiffDateLabel: formatSummaryDateLabel(resolveBaselineDiffAsOfDate(periodEnd)),
    invLatest: values[values.length - 1] ?? 0,
    invLatestDateLabel: formatSummaryDateLabel(invLatestDay),
    invPeak,
    invPeakLabel: labels[invPeakIdx] ?? '—',
    invAvg: Math.round(invSum / Math.max(values.length, 1)),
  }
})

const isCuttingReportPreview = computed(
  () =>
  selected.value?.report_code === 'CUTTING_DAILY_ACTUAL' &&
  !!preview.value?.chart_data,
)

const schedules = ref<ReportSchedule[]>([])
const logs = ref<ReportSendLog[]>([])

const weekdays = ['月', '火', '水', '木', '金', '土', '日']
const scheduleRangePresets = ['yesterday', 'today', 'last_week', 'this_week', 'last_month', 'this_month']

const selectedFields = computed<ReportParameterField[]>(() => selected.value?.parameter_schema?.fields || [])

function presetLabel(p: string): string {
  const map: Record<string, string> = {
    yesterday: '昨日',
    today: '本日',
    last_week: '先週',
    this_week: '今週',
    last_month: '先月',
    this_month: '今月',
    custom: '指定',
  }
  return map[p] || p
}

function definitionName(code: string): string {
  return definitions.value.find((d) => d.report_code === code)?.report_name || code
}

function scheduleTypeLabel(row: ReportSchedule): string {
  if (row.schedule_type === 'daily') return '毎日'
  if (row.schedule_type === 'weekly') {
    const wd = Number((row.schedule_config as { weekday?: number })?.weekday ?? 0)
    return `毎週 ${weekdays[wd]}`
  }
  if (row.schedule_type === 'monthly') {
    const day = Number((row.schedule_config as { day?: number })?.day ?? 1)
    return `毎月 ${day}日`
  }
  return row.schedule_type
}

function statusTagType(status: string): 'success' | 'warning' | 'danger' | 'info' {
  if (status === 'success') return 'success'
  if (status === 'partial') return 'warning'
  if (status === 'failed') return 'danger'
  return 'info'
}

function defaultPeriodForDefinition(def?: ReportDefinition | null): string {
  if (def?.report_code === CUTTING_REPORT_CODE) return CUTTING_DEFAULT_DATE_RANGE
  const field = def?.parameter_schema?.fields?.[0]
  return field?.default || field?.presets?.[0] || 'yesterday'
}

function applyCuttingReportUiDefaults(d: ReportDefinition) {
  if (d.report_code !== CUTTING_REPORT_CODE) return
  sendFormat.value = CUTTING_DEFAULT_FORMAT
  paramState.date_range = CUTTING_DEFAULT_DATE_RANGE
}

function selectDefinition(d: ReportDefinition) {
  selected.value = d
  preview.value = null
  disposeCharts()
  sendFormat.value = d.report_code === CUTTING_REPORT_CODE
    ? CUTTING_DEFAULT_FORMAT
    : (d.default_format === 'both' ? 'both' : (d.default_format || 'xlsx'))
  Object.keys(paramState).forEach((k) => delete paramState[k])
  for (const field of d.parameter_schema?.fields || []) {
    if (d.report_code === CUTTING_REPORT_CODE && field.key === 'date_range') {
      paramState[field.key] = CUTTING_DEFAULT_DATE_RANGE
    } else {
      paramState[field.key] = field.default || (field.presets ? field.presets[0] : '')
    }
  }
  applyCuttingReportUiDefaults(d)
}

function buildParameters(): Record<string, unknown> {
  const params: Record<string, unknown> = {}
  for (const field of selectedFields.value) {
    const value = paramState[field.key]
    params[field.key] = value
    if (field.type === 'date_range' && value === 'custom' && customRange.value) {
      params.start_date = customRange.value[0]
      params.end_date = customRange.value[1]
    }
    if (field.type === 'month' && value === 'custom' && customMonth.value) {
      params[field.key] = customMonth.value
    }
  }
  return params
}

function disposeCharts() {
  inventoryChart?.dispose()
  planActualChart?.dispose()
  inventoryChart = null
  planActualChart = null
}

function resolveTodayInChart(days: string[] | undefined, labels: string[]): string | null {
  const now = new Date()
  const todayIso = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
  if (days?.length) {
    const idx = days.indexOf(todayIso)
    if (idx >= 0) return labels[idx] ?? null
    return null
  }
  const mmdd = `${String(now.getMonth() + 1).padStart(2, '0')}/${String(now.getDate()).padStart(2, '0')}`
  return labels.includes(mmdd) ? mmdd : null
}

function buildInventoryChartOption(data: CuttingReportChartData) {
  const { labels, values, days } = data.inventory_trend
  const valuesInThousand = values.map((v) => toInventoryThousand(v))
  const letterLineThousand = toInventoryThousand(INVENTORY_LETTER_LINE)
  const yMax = Math.max(...valuesInThousand, letterLineThousand, 1)
  const todayLabel = resolveTodayInChart(days, labels)

  const markLineData: Array<Record<string, unknown>> = [
    {
      yAxis: letterLineThousand,
      lineStyle: { color: '#DC2626', width: 1, type: 'dashed', opacity: 0.75 },
    },
  ]

  return {
    animation: true,
    animationDuration: 600,
    animationEasing: 'cubicOut' as const,
    grid: { left: 40, right: 18, top: 28, bottom: 32 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15, 23, 42, 0.92)',
      borderWidth: 0,
      textStyle: { color: '#f8fafc', fontSize: 11 },
      formatter: (params: { name: string; value: number; dataIndex: number }[]) => {
        const p = params[0]
        const raw = values[p.dataIndex] ?? 0
        return `${p.name}<br/>切断済在庫: <b>${formatInventoryThousand(raw)}</b>（${raw.toLocaleString()}）`
      },
    },
    xAxis: {
      type: 'category',
      data: labels,
      boundaryGap: false,
      axisLine: { lineStyle: { color: CHART_GRID } },
      axisTick: { show: false },
      axisLabel: { color: CHART_AXIS, fontSize: 10, margin: 8 },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: Math.ceil(yMax * 1.1),
      splitNumber: 5,
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: CHART_GRID, type: 'dashed' } },
      axisLabel: {
        color: CHART_AXIS,
        fontSize: 10,
        formatter: (v: number) => `${v}`,
      },
    },
    series: [
      {
        name: '切断済在庫',
        type: 'line',
        smooth: 0.35,
        symbol: 'circle',
        symbolSize: (val: number, params: { dataIndex: number }) =>
          todayLabel && labels[params.dataIndex] === todayLabel ? 8 : 5,
        lineStyle: { width: 2.5, color: CHART_PRIMARY, shadowColor: 'rgba(37,99,235,0.25)', shadowBlur: 6 },
        itemStyle: (params: { dataIndex: number }) => {
          const isToday = todayLabel && labels[params.dataIndex] === todayLabel
          return {
            color: isToday ? '#DC2626' : CHART_PRIMARY,
            borderWidth: 2,
            borderColor: '#fff',
          }
        },
        emphasis: {
          scale: true,
          itemStyle: { borderWidth: 2, shadowBlur: 8, shadowColor: 'rgba(220,38,38,0.25)' },
        },
        label: {
          show: true,
          position: 'top',
          distance: 4,
          fontSize: 9,
          fontWeight: 500,
          color: (params: { dataIndex: number }) =>
            todayLabel && labels[params.dataIndex] === todayLabel ? '#DC2626' : '#1E40AF',
          formatter: (p: { value: number }) => `${p.value}`,
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(37, 99, 235, 0.22)' },
            { offset: 0.6, color: 'rgba(37, 99, 235, 0.06)' },
            { offset: 1, color: 'rgba(37, 99, 235, 0)' },
          ]),
        },
        data: valuesInThousand,
        markLine: {
          silent: true,
          symbol: ['none', 'none'],
          label: { show: false },
          data: markLineData,
        },
      },
    ],
  }
}

function buildPlanActualChartOption(data: CuttingReportChartData) {
  const { labels, plan, actual } = data.plan_actual
  const planInThousand = plan.map((v) => toInventoryThousand(v))
  const actualInThousand = actual.map((v) => toInventoryThousand(v))
  const yMax = Math.max(...planInThousand, ...actualInThousand, 1)

  return {
    animation: true,
    animationDuration: 600,
    animationEasing: 'cubicOut' as const,
    legend: {
      data: ['計画', '実績'],
      top: 0,
      right: 8,
      itemWidth: 12,
      itemHeight: 8,
      textStyle: { color: CHART_AXIS, fontSize: 10 },
    },
    grid: { left: 40, right: 18, top: 42, bottom: labels.length > 12 ? 44 : 32 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15, 23, 42, 0.92)',
      borderWidth: 0,
      textStyle: { color: '#f8fafc', fontSize: 11 },
      axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(37,99,235,0.06)' } },
      formatter: (params: { seriesName: string; value: number; dataIndex: number }[]) => {
        const day = labels[params[0]?.dataIndex] ?? ''
        const idx = params[0]?.dataIndex ?? 0
        const rawPlan = plan[idx] ?? 0
        const rawActual = actual[idx] ?? 0
        const lines = params
          .filter((p) => p.seriesName === '計画' || p.seriesName === '実績')
          .map((p) => {
            const raw = p.seriesName === '計画' ? rawPlan : rawActual
            return `${p.seriesName}: <b>${formatInventoryThousand(raw)}</b>（${raw.toLocaleString()}）`
          })
        lines.push(`差異: <b>${formatChartDiffTooltip(rawPlan, rawActual)}</b>`)
        return `${day}<br/>${lines.join('<br/>')}`
      },
    },
    xAxis: {
      type: 'category',
      data: labels,
      axisLine: { lineStyle: { color: CHART_GRID } },
      axisTick: { show: false },
      axisLabel: {
        color: CHART_AXIS,
        fontSize: 10,
        margin: 8,
        rotate: labels.length > 12 ? 40 : 0,
      },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: Math.ceil(yMax * 1.15),
      splitNumber: 5,
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: CHART_GRID, type: 'dashed' } },
      axisLabel: { color: CHART_AXIS, fontSize: 10 },
    },
    series: [
      {
        name: '計画',
        type: 'bar',
        barGap: '30%',
        barMaxWidth: 20,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#93C5FD' },
            { offset: 1, color: '#3B82F6' },
          ]),
          borderRadius: [3, 3, 0, 0],
        },
        emphasis: { itemStyle: { color: '#2563EB' } },
        data: planInThousand,
      },
      {
        name: '実績',
        type: 'bar',
        barMaxWidth: 20,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#6EE7B7' },
            { offset: 1, color: '#10B981' },
          ]),
          borderRadius: [3, 3, 0, 0],
        },
        emphasis: { itemStyle: { color: '#059669' } },
        data: actualInThousand,
      },
      {
        name: '差異',
        type: 'scatter',
        symbolSize: 0,
        data: planInThousand.map((p, i) => {
          const top = Math.max(p, actualInThousand[i])
          return [labels[i], top > 0 ? top : 0.01]
        }),
        label: {
          show: true,
          position: 'top',
          distance: 6,
          formatter: (param: { dataIndex: number }) =>
            formatChartDiffLabel(planInThousand[param.dataIndex], actualInThousand[param.dataIndex]),
          rich: CHART_DIFF_LABEL_RICH,
        },
        tooltip: { show: false },
        z: 20,
      },
    ],
  }
}

async function renderCuttingCharts() {
  disposeCharts()
  if (!isCuttingReportPreview.value || !preview.value?.chart_data) return
  await nextTick()
  const data = preview.value.chart_data
  if (inventoryChartRef.value) {
    inventoryChart = echarts.init(inventoryChartRef.value)
    inventoryChart.setOption(buildInventoryChartOption(data))
  }
  if (planActualChartRef.value) {
    planActualChart = echarts.init(planActualChartRef.value)
    planActualChart.setOption(buildPlanActualChartOption(data))
  }
}

function handleChartResize() {
  inventoryChart?.resize()
  planActualChart?.resize()
}

async function doPreview() {
  if (!selected.value) return
  previewLoading.value = true
  disposeCharts()
  try {
    preview.value = await previewReport(selected.value.report_code, buildParameters())
    await renderCuttingCharts()
  } catch {
    // インターセプタでメッセージ表示済み
  } finally {
    previewLoading.value = false
  }
}

async function doDownload() {
  if (!selected.value) return
  try {
    await downloadReport(selected.value.report_code, buildParameters(), sendFormat.value)
  } catch {
    ElMessage.error('ダウンロードに失敗しました')
  }
}

async function doSend() {
  if (!selected.value) return
  try {
    await ElMessageBox.confirm('このレポートを受信者に送信します。よろしいですか？', '送信確認', {
      type: 'warning',
    })
  } catch {
    return
  }
  sendLoading.value = true
  try {
    const result = await sendReport(selected.value.report_code, buildParameters(), sendFormat.value)
    ElMessage.success(result.message || '送信しました')
    if (activeTab.value === 'logs') await loadLogs()
  } catch {
    // インターセプタでメッセージ表示済み
  } finally {
    sendLoading.value = false
  }
}

// ===== スケジュール =====
const scheduleDialog = ref(false)
const savingSchedule = ref(false)
const editingSchedule = reactive<Partial<ReportSchedule>>({})
const weekdayValue = ref(0)
const monthDayValue = ref(1)
const scheduleTimeValue = ref('08:00:00')
const scheduleDateRange = ref('this_month')

watch(
  () => editingSchedule.report_code,
  (code) => {
    if (!scheduleDialog.value || editingSchedule.id || !code) return
    const def = definitions.value.find((d) => d.report_code === code)
    scheduleDateRange.value = defaultPeriodForDefinition(def)
  },
)

function openScheduleDialog(row?: ReportSchedule) {
  if (row) {
    Object.assign(editingSchedule, row)
    weekdayValue.value = Number((row.schedule_config as { weekday?: number })?.weekday ?? 0)
    monthDayValue.value = Number((row.schedule_config as { day?: number })?.day ?? 1)
    scheduleTimeValue.value = row.schedule_time || '08:00:00'
    scheduleDateRange.value = String((row.parameters as { date_range?: string; month?: string })?.date_range
      ?? (row.parameters as { month?: string })?.month
      ?? defaultPeriodForDefinition(definitions.value.find((d) => d.report_code === row.report_code)))
  } else {
    Object.keys(editingSchedule).forEach((k) => delete (editingSchedule as Record<string, unknown>)[k])
    editingSchedule.report_code = definitions.value[0]?.report_code
    editingSchedule.schedule_type = 'daily'
    editingSchedule.format = null
    editingSchedule.is_active = true
    weekdayValue.value = 0
    monthDayValue.value = 1
    scheduleTimeValue.value = '08:00:00'
    const def = definitions.value.find((d) => d.report_code === editingSchedule.report_code)
      ?? definitions.value[0]
    scheduleDateRange.value = defaultPeriodForDefinition(def)
  }
  scheduleDialog.value = true
}

function buildScheduleConfig(): Record<string, unknown> | null {
  if (editingSchedule.schedule_type === 'weekly') return { weekday: weekdayValue.value }
  if (editingSchedule.schedule_type === 'monthly') return { day: monthDayValue.value }
  return null
}

function buildScheduleParameters(): Record<string, unknown> {
  const def = definitions.value.find((d) => d.report_code === editingSchedule.report_code)
  const field = def?.parameter_schema?.fields?.[0]
  if (field?.type === 'month') return { month: scheduleDateRange.value === 'custom' ? 'last_month' : scheduleDateRange.value }
  return { date_range: scheduleDateRange.value }
}

async function saveSchedule() {
  if (!editingSchedule.report_code) {
    ElMessage.warning('レポートを選択してください')
    return
  }
  savingSchedule.value = true
  const payload: Partial<ReportSchedule> = {
    report_code: editingSchedule.report_code,
    schedule_type: editingSchedule.schedule_type,
    schedule_time: scheduleTimeValue.value,
    schedule_config: buildScheduleConfig(),
    parameters: buildScheduleParameters(),
    format: editingSchedule.format || null,
    is_active: editingSchedule.is_active ?? true,
  }
  try {
    if (editingSchedule.id) {
      await updateReportSchedule(editingSchedule.id, payload)
    } else {
      await createReportSchedule(payload)
    }
    ElMessage.success('保存しました')
    scheduleDialog.value = false
    await loadSchedules()
  } catch {
    // インターセプタでメッセージ表示済み
  } finally {
    savingSchedule.value = false
  }
}

function onScheduleActiveChange(row: ReportSchedule, val: string | number | boolean) {
  void toggleSchedule(row, Boolean(val))
}

async function toggleSchedule(row: ReportSchedule, value: boolean) {
  try {
    await updateReportSchedule(row.id, { is_active: value })
  } catch {
    row.is_active = !value
  }
}

async function removeSchedule(row: ReportSchedule) {
  try {
    await ElMessageBox.confirm(`スケジュールを削除しますか？`, '削除確認', { type: 'warning' })
  } catch {
    return
  }
  await deleteReportSchedule(row.id)
  ElMessage.success('削除しました')
  await loadSchedules()
}

async function loadDefinitions() {
  definitions.value = await fetchReportDefinitions()
  if (definitions.value.length && !selected.value) {
    const cutting = definitions.value.find((d) => d.report_code === CUTTING_REPORT_CODE)
    selectDefinition(cutting ?? definitions.value[0])
  }
}

async function loadSchedules() {
  schedules.value = await fetchReportSchedules()
}

async function loadLogs() {
  const res = await fetchReportSendLogs({ page: 1, limit: 100 })
  logs.value = res.data
}

async function loadAll() {
  pageLoading.value = true
  try {
    await Promise.all([loadDefinitions(), loadSchedules(), loadLogs()])
  } finally {
    pageLoading.value = false
  }
}

onMounted(() => {
  loadAll()
  window.addEventListener('resize', handleChartResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleChartResize)
  disposeCharts()
})

watch(isCuttingReportPreview, (val) => {
  if (val) void renderCuttingCharts()
  else disposeCharts()
})
</script>

<style scoped>
.rc-page {
  padding: 16px;
}
.rc-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.rc-top__brand {
  display: flex;
  align-items: center;
  gap: 10px;
}
.rc-top__title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}
.rc-top__desc {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.rc-tabs {
  display: flex;
  gap: 4px;
  border-bottom: 1px solid var(--el-border-color);
  margin-bottom: 12px;
}
.rc-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  border: none;
  background: transparent;
  padding: 8px 14px;
  cursor: pointer;
  font-size: 13px;
  color: var(--el-text-color-regular);
  border-bottom: 2px solid transparent;
}
.rc-tab--active {
  color: var(--el-color-primary);
  border-bottom-color: var(--el-color-primary);
  font-weight: 600;
}
.rc-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 16px;
}
.rc-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 70vh;
  overflow-y: auto;
}
.rc-def {
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  padding: 10px 12px;
  cursor: pointer;
  transition: all 0.15s;
}
.rc-def:hover {
  border-color: var(--el-color-primary-light-5);
}
.rc-def--active {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}
.rc-def__cat {
  font-size: 11px;
  color: var(--el-color-primary);
  font-weight: 600;
}
.rc-def__name {
  margin: 2px 0;
  font-size: 14px;
}
.rc-def__desc {
  margin: 0;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.rc-detail {
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  padding: 16px;
}
.rc-detail__title {
  margin: 0 0 12px;
  font-size: 16px;
}
.rc-form {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 12px;
}
.rc-field {
  display: flex;
  align-items: center;
  gap: 8px;
}
.rc-field__label {
  font-size: 13px;
  color: var(--el-text-color-regular);
}
.rc-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
.rc-preview {
  border-top: 1px dashed var(--el-border-color);
  padding-top: 12px;
}
.rc-preview__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 13px;
  margin-bottom: 10px;
}
.rc-tag {
  display: inline-block;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 10px;
  margin-right: 6px;
}
.rc-tag--mail {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}
.rc-tag--line {
  background: #e8f6ec;
  color: #2f9e44;
}
.rc-tag--warn {
  background: var(--el-color-warning-light-9);
  color: var(--el-color-warning);
}
.rc-recipients {
  margin: 8px 0 0;
  padding-left: 18px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.rc-preview__summary {
  margin-top: 12px;
  font-size: 13px;
}
.rc-preview__summary :deep(table) {
  border-collapse: collapse;
}
.rc-preview__summary :deep(th),
.rc-preview__summary :deep(td) {
  border: 1px solid var(--el-border-color);
  padding: 4px 8px;
}

/* 切断工程実績レポート A4 横向きプレビュー */
.rc-a4-preview {
  margin-top: 16px;
  display: flex;
  justify-content: center;
  padding: 12px;
  background: linear-gradient(145deg, #e2e8f0 0%, #f1f5f9 100%);
  border-radius: 10px;
}
.rc-a4-sheet {
  width: 100%;
  max-width: 680px;
  aspect-ratio: 210 / 297;
  max-height: 88vh;
  overflow-y: auto;
  background: #fff;
  border-radius: 4px;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.06),
    0 8px 24px rgba(15, 23, 42, 0.12);
  padding: 28px 32px 24px;
}
.rc-a4-sheet--landscape {
  max-width: min(100%, 1100px);
  aspect-ratio: 297 / 210;
  max-height: none;
  padding: 20px 28px 18px;
}
.rc-a4-sheet__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 2px solid #e2e8f0;
}
.rc-a4-sheet--landscape .rc-a4-sheet__head {
  margin-bottom: 10px;
  padding-bottom: 8px;
}
.rc-a4-sheet__title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: 0.02em;
  text-align: left;
  flex: 1;
  min-width: 0;
}
.rc-a4-sheet--landscape .rc-a4-sheet__title {
  font-size: 16px;
}
.rc-a4-sheet__period {
  margin: 0;
  font-size: 12px;
  color: #64748b;
  text-align: right;
  flex-shrink: 0;
  white-space: nowrap;
}
.rc-a4-section {
  margin-bottom: 10px;
}
.rc-a4-section:last-child {
  margin-bottom: 0;
}
.rc-a4-section__title {
  margin: 0 0 6px;
  font-size: 12px;
  font-weight: 600;
  color: #1e40af;
}
.rc-a4-chart-wrap {
  position: relative;
}
.rc-a4-chart-comment {
  position: absolute;
  top: 2px;
  right: 4px;
  z-index: 2;
  max-width: 62%;
  margin: 0;
  padding: 4px 8px;
  font-size: 9px;
  line-height: 1.45;
  font-weight: 600;
  color: #b91c1c;
  text-align: right;
  background: rgba(254, 242, 242, 0.94);
  border: 1px solid #fecaca;
  border-radius: 4px;
  box-shadow: 0 1px 2px rgba(220, 38, 38, 0.08);
  pointer-events: none;
}
.rc-a4-chart {
  height: 180px;
  width: 100%;
}
.rc-a4-sheet--landscape .rc-a4-chart {
  height: 200px;
}
.rc-a4-chart--bar {
  height: 200px;
}
.rc-a4-sheet--landscape .rc-a4-chart--bar {
  height: 200px;
}

.rc-a4-summary {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid #e2e8f0;
}
.rc-a4-summary__heading {
  margin: 0 0 8px;
  font-size: 11px;
  font-weight: 600;
  color: #475569;
}
.rc-a4-summary__block {
  margin-bottom: 8px;
}
.rc-a4-summary__block:last-child {
  margin-bottom: 0;
}
.rc-a4-summary__block-title {
  display: block;
  font-size: 10px;
  font-weight: 600;
  color: #1e40af;
  margin-bottom: 6px;
}
.rc-a4-summary__grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 8px;
}
.rc-a4-summary__grid--inv {
  grid-template-columns: repeat(3, 1fr);
}
.rc-a4-summary__item {
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 8px 10px;
  text-align: center;
  min-width: 0;
}
.rc-a4-summary__label {
  display: block;
  font-size: 9px;
  color: #64748b;
  margin-bottom: 4px;
  line-height: 1.3;
}
.rc-a4-summary__value {
  display: block;
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.2;
}
.rc-a4-summary__value--sm {
  font-size: 12px;
  font-weight: 600;
}
.rc-a4-summary__value--pos {
  color: #059669;
}
.rc-a4-summary__value--neg {
  color: #dc2626;
}
.rc-a4-summary__sub {
  display: block;
  margin-top: 2px;
  font-size: 9px;
  font-weight: 500;
  color: #94a3b8;
}

/* summary_html 内スタイル（切断レポート・他レポート用） */
.rc-preview__summary :deep(.cutting-report-summary .cr-header) {
  display: none;
}
.rc-preview__summary :deep(.cutting-report-summary .cr-kpi-row) {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-bottom: 10px;
}
.rc-preview__summary :deep(.cr-kpi) {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 8px 10px;
  text-align: center;
}
.rc-preview__summary :deep(.cr-kpi__label) {
  display: block;
  font-size: 10px;
  color: #64748b;
  margin-bottom: 2px;
}
.rc-preview__summary :deep(.cr-kpi b) {
  font-size: 14px;
  color: #0f172a;
}
.rc-preview__summary :deep(.cr-kpi small) {
  display: block;
  font-size: 9px;
  color: #94a3b8;
}
.rc-preview__summary :deep(.cr-pos) {
  color: #059669;
}
.rc-preview__summary :deep(.cr-neg) {
  color: #dc2626;
}
.rc-preview__summary :deep(.cr-note) {
  font-size: 10px;
  color: #94a3b8;
  margin: 0 0 8px;
}
.rc-preview__summary :deep(.cr-table) {
  width: 100%;
  font-size: 10px;
  border-collapse: collapse;
}
.rc-preview__summary :deep(.cr-table th) {
  background: #e8eef7;
  color: #1e3a5f;
  font-weight: 600;
  padding: 5px 6px;
  border: 1px solid #cbd5e1;
}
.rc-preview__summary :deep(.cr-table td) {
  padding: 4px 6px;
  border: 1px solid #e2e8f0;
}
.rc-preview__summary :deep(.cr-table tfoot th) {
  background: #f8fafc;
}
.rc-panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.rc-panel__title {
  margin: 0;
  font-size: 15px;
}
</style>
