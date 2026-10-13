<template>
  <div class="rc-page rc-modern pb-std" v-loading="pageLoading">
    <div class="page-toolbar pb-hero pb-hero--page">
      <div class="page-toolbar-glow" aria-hidden="true" />
      <div class="pb-bubbles" aria-hidden="true" />
      <div class="toolbar-left">
        <div class="toolbar-brand">
          <div class="toolbar-icon-wrap">
            <el-icon class="toolbar-icon"><Document /></el-icon>
          </div>
          <div class="toolbar-text">
            <h1 class="toolbar-title pb-hero-title">報告センター</h1>
            <p class="toolbar-desc pb-hero-desc">生成・手動配信・定時配信・送信履歴を一画面で</p>
          </div>
        </div>
        <div class="rc-stat-chips">
          <div class="rc-chip rc-chip--defs">
            <span class="rc-chip__label">レポート</span>
            <b class="rc-chip__value">{{ definitions.length }}</b>
          </div>
          <div class="rc-chip rc-chip--sched">
            <span class="rc-chip__label">スケジュール</span>
            <b class="rc-chip__value">{{ schedules.length }}</b>
          </div>
          <div class="rc-chip rc-chip--logs">
            <span class="rc-chip__label">履歴</span>
            <b class="rc-chip__value">{{ logs.length }}</b>
          </div>
        </div>
      </div>
      <div class="toolbar-right toolbar-actions">
        <el-button class="tb-btn tb-btn-teal" :loading="pageLoading" @click="loadAll">
          <el-icon><Refresh /></el-icon>
          <span class="tb-label">更新</span>
        </el-button>
      </div>
    </div>

    <nav class="rc-tabs-bar" role="tablist" aria-label="報告センタータブ">
      <button
        v-for="tab in tabs"
        :key="tab.name"
        type="button"
        role="tab"
        class="rc-tab"
        :class="[`rc-tab--${tab.name}`, { 'rc-tab--active': activeTab === tab.name }]"
        :aria-selected="activeTab === tab.name"
        @click="activeTab = tab.name"
      >
        <span class="rc-tab__icon"><el-icon :size="15"><component :is="tab.icon" /></el-icon></span>
        <span>{{ tab.label }}</span>
        <span v-if="tab.name === 'schedule' && schedules.length" class="rc-tab__badge">{{ schedules.length }}</span>
        <span v-if="tab.name === 'logs' && logs.length" class="rc-tab__badge rc-tab__badge--muted">{{ logs.length }}</span>
      </button>
    </nav>

    <!-- 配信（手動） -->
    <section v-show="activeTab === 'send'" class="rc-shell rc-shell--send">
      <div class="rc-layout">
        <aside class="rc-list">
          <div class="rc-list__head">
            <span class="rc-list__label">レポート一覧</span>
            <span class="rc-list__count">{{ definitions.length }}</span>
          </div>
          <article
            v-for="d in definitions"
            :key="d.report_code"
            class="rc-def"
            :class="[
              `rc-def--cat-${categoryTone(d.category)}`,
              { 'rc-def--active': selected?.report_code === d.report_code },
            ]"
            @click="selectDefinition(d)"
          >
            <span class="rc-def__cat">{{ d.category }}</span>
            <h3 class="rc-def__name">{{ d.report_name }}</h3>
            <p class="rc-def__desc">{{ d.description || '—' }}</p>
          </article>
          <el-empty v-if="!definitions.length" description="レポート定義がありません" :image-size="48" />
        </aside>

        <div class="rc-detail" v-if="selected">
          <div class="rc-detail__head">
            <div>
              <span class="rc-detail__cat" :class="`rc-detail__cat--${categoryTone(selected.category)}`">
                {{ selected.category }}
              </span>
              <h2 class="rc-detail__title">{{ selected.report_name }}</h2>
            </div>
            <span class="rc-detail__code">{{ selected.report_code }}</span>
          </div>

          <div class="rc-toolbar">
            <div class="rc-form">
              <div v-for="field in selectedFields" :key="field.key" class="rc-field">
                <label class="rc-field__label">{{ field.label }}</label>
                <template v-if="field.type === 'date_range'">
                  <el-select v-model="paramState[field.key]" size="small" class="rc-field__control">
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
                    start-placeholder="開始"
                    end-placeholder="終了"
                    class="rc-field__control rc-field__control--range"
                  />
                </template>
                <template v-else-if="field.type === 'month'">
                  <el-select v-model="paramState[field.key]" size="small" class="rc-field__control">
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
                    class="rc-field__control"
                  />
                </template>
              </div>
            </div>
            <div class="rc-actions">
              <el-select v-model="sendFormat" size="small" class="rc-actions__format">
                <el-option label="Excel" value="xlsx" />
                <el-option label="PDF" value="pdf" />
                <el-option label="両方" value="both" />
              </el-select>
              <el-button class="tb-btn tb-btn-blue" size="small" :loading="previewLoading" @click="doPreview">
                <el-icon><View /></el-icon>
                <span class="tb-label">プレビュー</span>
              </el-button>
              <el-button class="tb-btn tb-btn-amber" size="small" @click="doDownload">
                <el-icon><Download /></el-icon>
                <span class="tb-label">DL</span>
              </el-button>
              <el-button
                class="tb-btn tb-btn-green"
                size="small"
                :loading="sendLoading"
                :disabled="!preview?.can_send"
                @click="doSend"
              >
                <el-icon><Promotion /></el-icon>
                <span class="tb-label">送信</span>
              </el-button>
            </div>
          </div>

          <div v-if="preview" class="rc-preview">
            <div class="rc-preview__meta">
              <div class="rc-stat rc-stat--period">
                <span class="rc-stat__label">対象期間</span>
                <b class="rc-stat__value">{{ preview.period_label }}</b>
              </div>
              <div class="rc-stat rc-stat--count">
                <span class="rc-stat__label">件数</span>
                <b class="rc-stat__value">{{ preview.record_count }}</b>
              </div>
              <div class="rc-stat rc-stat--fmt">
                <span class="rc-stat__label">形式</span>
                <b class="rc-stat__value">{{ preview.format }}</b>
              </div>
              <div class="rc-stat rc-stat--file rc-stat--wide">
                <span class="rc-stat__label">添付</span>
                <b class="rc-stat__value rc-stat__value--truncate">{{ preview.attachments.map((a) => a.filename).join(', ') || '—' }}</b>
              </div>
            </div>

            <div class="rc-preview__recipients">
              <div class="rc-tags">
                <span class="rc-tag rc-tag--mail">メール {{ preview.recipient_count }}</span>
                <span class="rc-tag rc-tag--line">LINE {{ preview.line_recipient_count }}</span>
                <span v-if="!preview.email_enabled && !preview.line_enabled" class="rc-tag rc-tag--warn">
                  通知イベント無効
                </span>
                <span v-else-if="!preview.can_send" class="rc-tag rc-tag--warn">
                  送信不可（設定を確認）
                </span>
                <span v-else class="rc-tag rc-tag--ok">送信可能</span>
              </div>
              <ul v-if="preview.recipients.length" class="rc-recipients">
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
        <div v-else class="rc-detail rc-detail--empty">
          <el-empty description="レポートを選択してください" :image-size="56" />
        </div>
      </div>
    </section>

    <!-- スケジュール -->
    <section v-show="activeTab === 'schedule'" class="rc-shell rc-shell--schedule">
      <div class="rc-panel__head">
        <div class="rc-panel__title-wrap">
          <span class="rc-panel__dot rc-panel__dot--sched" aria-hidden="true" />
          <div>
            <h2 class="rc-panel__title">定時配信スケジュール</h2>
            <p class="rc-panel__sub">自動送信の頻度・時刻・対象期間を管理</p>
          </div>
        </div>
        <el-button class="tb-btn tb-btn-blue" size="small" @click="openScheduleDialog()">
          <el-icon><Plus /></el-icon>
          <span class="tb-label">新規追加</span>
        </el-button>
      </div>
      <div class="rc-table-wrap">
      <el-table :data="schedules" size="small" class="rc-table rc-table--sched" stripe border>
        <el-table-column label="レポート" min-width="180">
          <template #default="{ row }">
            <div class="rc-cell-report">
              <span class="rc-cell-report__name">{{ definitionName(row.report_code) }}</span>
              <span class="rc-cell-report__code">{{ row.report_code }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="頻度" width="120">
          <template #default="{ row }">
            <span class="rc-pill rc-pill--freq">{{ scheduleTypeLabel(row) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="schedule_time" label="時刻" width="90" />
        <el-table-column label="形式" width="80">
          <template #default="{ row }">
            <span class="rc-pill rc-pill--fmt">{{ row.format || '既定' }}</span>
          </template>
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
            <el-button link type="primary" size="small" class="row-act act-edit" @click="openScheduleDialog(row)">編集</el-button>
            <el-button link type="danger" size="small" class="row-act act-delete" @click="removeSchedule(row)">削除</el-button>
          </template>
        </el-table-column>
      </el-table>
      </div>
    </section>

    <!-- 送信履歴 -->
    <section v-show="activeTab === 'logs'" class="rc-shell rc-shell--logs">
      <div class="rc-panel__head">
        <div class="rc-panel__title-wrap">
          <span class="rc-panel__dot rc-panel__dot--logs" aria-hidden="true" />
          <div>
            <h2 class="rc-panel__title">送信履歴</h2>
            <p class="rc-panel__sub">直近 100 件の配信結果</p>
          </div>
        </div>
        <el-button class="tb-btn tb-btn-amber" size="small" @click="loadLogs">
          <el-icon><Refresh /></el-icon>
          <span class="tb-label">更新</span>
        </el-button>
      </div>
      <div class="rc-table-wrap">
      <el-table :data="logs" size="small" class="rc-table rc-table--logs" stripe border>
        <el-table-column label="レポート" min-width="160">
          <template #default="{ row }">{{ definitionName(row.report_code) }}</template>
        </el-table-column>
        <el-table-column label="種別" width="100">
          <template #default="{ row }">
            <span class="rc-pill" :class="row.trigger_type === 'scheduled' ? 'rc-pill--auto' : 'rc-pill--manual'">
              {{ triggerLabel(row.trigger_type) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状態" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small" effect="light" round>
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="recipient_count" label="対象" width="70" />
        <el-table-column prop="success_count" label="成功" width="70" />
        <el-table-column prop="file_name" label="ファイル" min-width="160" />
        <el-table-column prop="message" label="メッセージ" min-width="180" />
        <el-table-column prop="created_at" label="日時" width="160" />
      </el-table>
      </div>
    </section>

    <!-- スケジュール編集ダイアログ -->
    <el-dialog
      v-model="scheduleDialog"
      width="480px"
      class="rc-dialog pb-std"
      align-center
      destroy-on-close
      :show-close="false"
    >
      <template #header>
        <div class="rc-dlg-header rc-dlg-header--blue">
          <div class="rc-dlg-icon-wrap">
            <el-icon class="rc-dlg-icon"><Plus /></el-icon>
          </div>
          <div class="rc-dlg-title-wrap">
            <span class="rc-dlg-title">{{ editingSchedule.id ? 'スケジュール編集' : 'スケジュール追加' }}</span>
            <span class="rc-dlg-subtitle">定時配信の頻度・時刻・対象期間</span>
          </div>
        </div>
      </template>
      <div class="rc-dlg-body">
      <el-form label-width="90px" class="rc-dlg-form">
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
      </div>
      <template #footer>
        <div class="rc-dlg-footer">
          <el-button class="rc-dlg-btn-cancel" @click="scheduleDialog = false">キャンセル</el-button>
          <el-button type="primary" class="rc-dlg-btn-submit rc-dlg-btn-submit--blue" :loading="savingSchedule" @click="saveSchedule">保存</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, Download, Plus, Promotion, Refresh, View } from '@element-plus/icons-vue'
import echarts from '@/utils/echarts'
import type { ECharts } from '@/utils/echarts'
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
const route = useRoute()
const initialTab = String(route.query.tab || '')
const activeTab = ref(tabs.some((t) => t.name === initialTab) ? initialTab : 'send')
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

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    success: '成功',
    partial: '一部成功',
    failed: '失敗',
    already_sent: '送信済',
    skipped_inactive: '無効',
    skipped_channels: 'チャネル無',
    no_recipients: '宛先無',
  }
  return map[status] || status
}

function triggerLabel(trigger: string): string {
  if (trigger === 'scheduled') return '定時'
  if (trigger === 'manual') return '手動'
  return trigger
}

function categoryTone(category: string): string {
  const c = (category || '').toUpperCase()
  if (c === 'MES') return 'mes'
  if (c === 'ERP') return 'erp'
  if (c === 'APS') return 'aps'
  return 'other'
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
  --rc-surface: #ffffff;
  --rc-border: #e0e7ff;
  --rc-text: #0f172a;
  --rc-muted: #64748b;
  --rc-primary: #6366f1;
  --rc-shadow: 0 1px 2px rgba(15, 23, 42, 0.04), 0 14px 32px -18px rgba(79, 70, 229, 0.3);
  --rc-radius: 14px;
  --rc-radius-sm: 12px;
  position: relative;
  width: 100%;
  box-sizing: border-box;
  min-height: 100vh;
  padding: 12px;
  color: var(--rc-text);
  background:
    radial-gradient(1100px 380px at 0% 0%, rgba(37, 99, 235, 0.1), transparent 60%),
    radial-gradient(900px 380px at 100% 0%, rgba(14, 165, 233, 0.07), transparent 60%),
    linear-gradient(160deg, #eff6ff 0%, #f0f9ff 45%, #f8fafc 100%);
}

/* ---------- タイトルバー（報告＝青系・他頁と分色） ---------- */
.rc-modern .page-toolbar {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  background: linear-gradient(125deg, #1e40af 0%, #2563eb 38%, #3b82f6 72%, #0ea5e9 100%);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 16px;
  margin-bottom: 10px;
  overflow: hidden;
  box-shadow:
    0 18px 36px -18px rgba(30, 64, 175, 0.55),
    0 4px 12px -6px rgba(37, 99, 235, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.page-toolbar-glow {
  position: absolute;
  inset: -40% -20% auto -10%;
  height: 120%;
  background: radial-gradient(ellipse 80% 55% at 18% 0%, rgba(255, 255, 255, 0.22), transparent 55%);
  pointer-events: none;
}

.toolbar-left {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 14px;
  flex: 1;
  min-width: 0;
  flex-wrap: wrap;
}

.toolbar-brand {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.toolbar-icon-wrap {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.3) 0%, rgba(255, 255, 255, 0.1) 100%);
  border: 1px solid rgba(255, 255, 255, 0.38);
  box-shadow:
    0 6px 14px -6px rgba(15, 23, 42, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.5),
    inset 0 -2px 0 rgba(15, 23, 42, 0.12);
}

.toolbar-icon { font-size: 20px; color: #fff; }

.toolbar-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.toolbar-title {
  margin: 0;
  font-weight: 800;
  letter-spacing: 0.02em;
  color: #fff;
}

.toolbar-desc {
  margin: 0;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.86);
}

.toolbar-right {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.rc-stat-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.rc-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border-radius: 12px;
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.24), rgba(255, 255, 255, 0.08));
  border: 1px solid rgba(255, 255, 255, 0.28);
  color: rgba(255, 255, 255, 0.92);
  font-size: 0.7rem;
  white-space: nowrap;
  box-shadow:
    0 3px 0 rgba(55, 48, 163, 0.35),
    0 10px 20px -10px rgba(0, 0, 0, 0.35);
  position: relative;
  overflow: hidden;
}

.rc-chip::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 3px;
}

.rc-chip--defs::before { background: #5eead4; }
.rc-chip--sched::before { background: #93c5fd; }
.rc-chip--logs::before { background: #fcd34d; }

.rc-chip__label { color: rgba(255, 255, 255, 0.78); }
.rc-chip__value {
  font-weight: 800;
  font-size: 0.9rem;
  color: #fff;
  font-variant-numeric: tabular-nums;
}

/* 白地カプセル */
.tb-btn {
  --tb-h: 32px;
  --k-rgb: 79 70 229;
  --k-fg: #4338ca;
  --k-fg-h: #3730a3;
  --k-bd: #c7d2fe;
  --k-bd-h: #a5b4fc;
  --k-tint: #e0e7ff;
  --k-tint-h: #c7d2fe;
  --k-ico: #6366f1;
  --el-button-text-color: var(--k-fg);
  --el-button-hover-text-color: var(--k-fg-h);
  --el-button-active-text-color: var(--k-fg-h);
  --el-button-border-color: var(--k-bd);
  --el-button-hover-border-color: var(--k-bd-h);
  --el-button-active-border-color: var(--k-bd-h);
  position: relative;
  height: var(--tb-h);
  min-height: var(--tb-h);
  padding: 0 15px 0 12px;
  border-radius: 999px;
  border: 1px solid var(--k-bd);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.03em;
  color: var(--k-fg);
  background: linear-gradient(135deg, #ffffff 0%, #ffffff 40%, var(--k-tint) 100%);
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease, background 0.2s ease;
}
.tb-btn :deep(.el-icon) {
  margin-right: 5px;
  font-size: 15px;
  color: var(--k-ico);
}
.tb-btn:hover,
.tb-btn:focus {
  border-color: var(--k-bd-h);
  color: var(--k-fg-h);
  background: linear-gradient(135deg, #ffffff 0%, var(--k-tint) 45%, var(--k-tint-h) 100%);
}
.tb-btn-blue {
  --k-rgb: 37 99 235; --k-fg: #1d4ed8; --k-fg-h: #1e40af;
  --k-bd: #93c5fd; --k-bd-h: #60a5fa; --k-tint: #dbeafe; --k-tint-h: #bfdbfe; --k-ico: #3b82f6;
}
.tb-btn-teal {
  --k-rgb: 13 148 136; --k-fg: #0f766e; --k-fg-h: #115e59;
  --k-bd: #5eead4; --k-bd-h: #2dd4bf; --k-tint: #ccfbf1; --k-tint-h: #99f6e4; --k-ico: #14b8a6;
}
.tb-btn-amber {
  --k-rgb: 217 119 6; --k-fg: #b45309; --k-fg-h: #92400e;
  --k-bd: #fcd34d; --k-bd-h: #fbbf24; --k-tint: #fef3c7; --k-tint-h: #fde68a; --k-ico: #f59e0b;
}
.tb-btn-indigo {
  --k-rgb: 79 70 229; --k-fg: #4338ca; --k-fg-h: #3730a3;
  --k-bd: #a5b4fc; --k-bd-h: #818cf8; --k-tint: #e0e7ff; --k-tint-h: #c7d2fe; --k-ico: #6366f1;
}
.tb-btn-green {
  --k-rgb: 5 150 105; --k-fg: #047857; --k-fg-h: #065f46;
  --k-bd: #6ee7b7; --k-bd-h: #34d399; --k-tint: #d1fae5; --k-tint-h: #a7f3d0; --k-ico: #10b981;
}

.rc-page.rc-modern.pb-std.pb-std .tb-btn.tb-btn.el-button.el-button:not(.is-link):not(.is-text):not(.is-disabled) {
  box-shadow:
    inset 0 1px 0 #fff,
    inset 0 -2px 0 rgb(var(--k-rgb) / 0.12),
    0 2px 6px -1px rgba(15, 23, 42, 0.2) !important;
}
.rc-page.rc-modern.pb-std.pb-std .tb-btn.tb-btn.el-button.el-button:not(.is-link):not(.is-text):not(.is-disabled):hover {
  box-shadow:
    inset 0 1px 0 #fff,
    inset 0 -2px 0 rgb(var(--k-rgb) / 0.16),
    0 4px 8px -2px rgba(15, 23, 42, 0.25),
    0 10px 22px -8px rgb(var(--k-rgb) / 0.55) !important;
}

/* ---------- Tab バー ---------- */
.rc-tabs-bar {
  position: relative;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 6px 10px 6px 16px;
  margin-bottom: 10px;
  overflow-x: auto;
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e0e7ff;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 10px 24px -16px rgba(79, 70, 229, 0.28);
}

.rc-tabs-bar::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  border-radius: 12px 0 0 12px;
  background: linear-gradient(180deg, #818cf8, #a855f7, #ec4899);
}

.rc-tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: none;
  background: transparent;
  padding: 7px 14px;
  border-radius: 999px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  color: var(--rc-muted);
  transition: background 0.18s, color 0.18s, box-shadow 0.18s;
  white-space: nowrap;
}

.rc-tab__icon { display: inline-flex; opacity: 0.85; }

.rc-tab:hover {
  color: #4338ca;
  background: #eef2ff;
}

.rc-tab--active {
  color: #fff !important;
  font-weight: 700;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.3),
    inset 0 -2px 0 rgba(67, 56, 202, 0.3),
    0 4px 10px -4px rgba(99, 102, 241, 0.55);
}

.rc-tab--send.rc-tab--active {
  background: linear-gradient(135deg, #2dd4bf, #0d9488);
}
.rc-tab--schedule.rc-tab--active {
  background: linear-gradient(135deg, #60a5fa, #2563eb);
}
.rc-tab--logs.rc-tab--active {
  background: linear-gradient(135deg, #fbbf24, #d97706);
}

.rc-tab--active .rc-tab__badge {
  background: rgba(255, 255, 255, 0.28);
  color: #fff;
}

.rc-tab__badge {
  min-width: 17px;
  height: 17px;
  padding: 0 5px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 800;
  line-height: 17px;
  text-align: center;
  color: #fff;
  background: #6366f1;
  font-variant-numeric: tabular-nums;
}

.rc-tab__badge--muted { background: #d97706; }

.rc-shell {
  position: relative;
  overflow: hidden;
  border-radius: var(--rc-radius);
  border: 1px solid #e0e7ff;
  background: #fff;
  box-shadow: var(--rc-shadow);
  padding: 12px;
}

.rc-shell::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
}

.rc-shell--send::before { background: linear-gradient(90deg, #14b8a6, #2dd4bf, #0d9488); }
.rc-shell--schedule::before { background: linear-gradient(90deg, #3b82f6, #60a5fa, #2563eb); }
.rc-shell--logs::before { background: linear-gradient(90deg, #f59e0b, #fbbf24, #d97706); }

.rc-shell--schedule .rc-table-wrap::before {
  background: linear-gradient(90deg, #3b82f6, #6366f1, #06b6d4);
}
.rc-shell--logs .rc-table-wrap::before {
  background: linear-gradient(90deg, #f59e0b, #f97316, #ec4899);
}

.rc-layout {
  display: grid;
  grid-template-columns: minmax(220px, 256px) minmax(0, 1fr);
  gap: 12px;
  align-items: start;
}

.rc-list {
  display: flex;
  flex-direction: column;
  gap: 7px;
  max-height: calc(100vh - 200px);
  overflow-y: auto;
  padding-right: 2px;
}

.rc-list__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 2px 4px 4px;
}

.rc-list__label {
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--rc-muted);
}

.rc-list__count {
  font-size: 10px;
  font-weight: 800;
  color: #0f766e;
  background: #ccfbf1;
  padding: 1px 7px;
  border-radius: 999px;
}

.rc-def {
  position: relative;
  border: 1px solid var(--rc-border);
  border-radius: var(--rc-radius-sm);
  padding: 9px 11px 9px 13px;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s, transform 0.12s, box-shadow 0.15s;
  background: #fafcfb;
}

.rc-def::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  bottom: 8px;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: #cbd5e1;
}

.rc-def:hover {
  border-color: #99f6e4;
  background: #fff;
  transform: translateY(-1px);
}

.rc-def--cat-mes::before { background: #14b8a6; }
.rc-def--cat-erp::before { background: #0ea5e9; }
.rc-def--cat-aps::before { background: #f59e0b; }
.rc-def--cat-other::before { background: #94a3b8; }
.rc-def--cat-mes .rc-def__cat { color: #0f766e; }
.rc-def--cat-erp .rc-def__cat { color: #0369a1; }
.rc-def--cat-aps .rc-def__cat { color: #b45309; }
.rc-def--cat-other .rc-def__cat { color: #64748b; }

.rc-def--active {
  border-color: #5eead4;
  background: linear-gradient(135deg, #f0fdfa 0%, #ecfeff 100%);
  box-shadow: 0 4px 14px rgba(13, 148, 136, 0.12);
}

.rc-def--active.rc-def--cat-erp {
  border-color: #7dd3fc;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  box-shadow: 0 4px 14px rgba(3, 105, 161, 0.1);
}

.rc-def--active.rc-def--cat-aps {
  border-color: #fcd34d;
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
  box-shadow: 0 4px 14px rgba(180, 83, 9, 0.1);
}

.rc-def__cat {
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.04em;
}

.rc-def__name {
  margin: 2px 0 0;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.3;
}

.rc-def__desc {
  margin: 3px 0 0;
  font-size: 11px;
  color: var(--rc-muted);
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.rc-detail {
  border: 1px solid #e0e7ff;
  border-radius: var(--rc-radius-sm);
  padding: 12px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  min-height: 280px;
}

.rc-detail--empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 320px;
}

.rc-detail__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #e0e7ff;
}

.rc-detail__cat {
  display: inline-block;
  font-size: 10px;
  font-weight: 800;
  padding: 2px 8px;
  border-radius: 999px;
  margin-bottom: 4px;
  background: #f1f5f9;
  color: #64748b;
}

.rc-detail__cat--mes { background: #ccfbf1; color: #0f766e; }
.rc-detail__cat--erp { background: #e0f2fe; color: #0369a1; }
.rc-detail__cat--aps { background: #fef3c7; color: #b45309; }

.rc-detail__title {
  margin: 0;
  font-size: 16px;
  font-weight: 800;
  line-height: 1.25;
}

.rc-detail__code {
  font-size: 10px;
  font-weight: 700;
  color: var(--rc-muted);
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  padding: 3px 8px;
  border-radius: 6px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  flex-shrink: 0;
}

.rc-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
  padding: 10px;
  border-radius: var(--rc-radius-sm);
  background: linear-gradient(180deg, #f0fdfa 0%, #f8fafc 100%);
  border: 1px solid #d5ebe6;
}

.rc-form {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  align-items: flex-end;
  flex: 1;
  min-width: 0;
}

.rc-field {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.rc-field__label {
  font-size: 11px;
  font-weight: 700;
  color: #475569;
  white-space: nowrap;
}

.rc-field__control { width: 140px; }
.rc-field__control--range { width: 220px; }

.rc-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.rc-actions__format { width: 96px; }

.rc-btn--send {
  --el-button-bg-color: #0f766e;
  --el-button-border-color: #0f766e;
  --el-button-hover-bg-color: #0d9488;
  --el-button-hover-border-color: #0d9488;
}

.rc-btn--sched {
  --el-button-bg-color: #0369a1;
  --el-button-border-color: #0369a1;
  --el-button-hover-bg-color: #0284c7;
  --el-button-hover-border-color: #0284c7;
}

.rc-preview {
  border-top: 1px solid #e6f2ef;
  padding-top: 10px;
}

.rc-preview__meta {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 10px;
}

.rc-stat {
  padding: 8px 10px;
  border-radius: 10px;
  background: #f8fafc;
  border: 1px solid #e8edf3;
  min-width: 0;
}

.rc-stat--period { background: #f0fdfa; border-color: #99f6e4; color: #0f766e; }
.rc-stat--count { background: #eff6ff; border-color: #bfdbfe; color: #1d4ed8; }
.rc-stat--fmt { background: #f5f3ff; border-color: #c4b5fd; color: #6d28d9; }
.rc-stat--file { background: #fffbeb; border-color: #fde68a; color: #b45309; }
.rc-stat--wide { grid-column: span 1; }

.rc-stat__label {
  display: block;
  font-size: 9px;
  font-weight: 700;
  color: var(--rc-muted);
  margin-bottom: 2px;
  letter-spacing: 0.03em;
}

.rc-stat__value {
  display: block;
  font-size: 12px;
  font-weight: 800;
  color: var(--rc-text);
  line-height: 1.25;
}

.rc-stat__value--truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rc-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.rc-tag {
  display: inline-flex;
  align-items: center;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 9px;
  border-radius: 999px;
  line-height: 1.4;
}

.rc-tag--mail {
  background: #e0f2fe;
  color: #0369a1;
  border: 1px solid #bae6fd;
}

.rc-tag--line {
  background: #ecfdf5;
  color: #047857;
  border: 1px solid #a7f3d0;
}

.rc-tag--warn {
  background: #fffbeb;
  color: #b45309;
  border: 1px solid #fde68a;
}

.rc-tag--ok {
  background: #ccfbf1;
  color: #0f766e;
  border: 1px solid #99f6e4;
}

.rc-recipients {
  margin: 6px 0 0;
  padding: 6px 8px 6px 22px;
  font-size: 11px;
  color: var(--rc-muted);
  background: #f8fafc;
  border-radius: 6px;
  border: 1px solid #eef2f7;
  max-height: 72px;
  overflow-y: auto;
}

.rc-recipients li {
  line-height: 1.45;
}

.rc-preview__summary {
  margin-top: 8px;
  font-size: 12px;
}

.rc-preview__summary :deep(table) {
  border-collapse: collapse;
}

.rc-preview__summary :deep(th),
.rc-preview__summary :deep(td) {
  border: 1px solid var(--rc-border);
  padding: 3px 6px;
}

/* 切断工程実績レポート A4 横向きプレビュー */
.rc-a4-preview {
  margin-top: 8px;
  display: flex;
  justify-content: center;
  padding: 8px;
  background: linear-gradient(145deg, #e8edf4 0%, #f1f5f9 100%);
  border-radius: var(--rc-radius-sm);
  border: 1px solid var(--rc-border);
}

.rc-a4-sheet {
  width: 100%;
  max-width: 680px;
  aspect-ratio: 210 / 297;
  max-height: 82vh;
  overflow-y: auto;
  background: #fff;
  border-radius: 4px;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.06),
    0 6px 20px rgba(15, 23, 42, 0.1);
  padding: 20px 24px 16px;
}

.rc-a4-sheet--landscape {
  max-width: min(100%, 1100px);
  aspect-ratio: 297 / 210;
  max-height: none;
  padding: 16px 22px 14px;
}

.rc-a4-sheet__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 2px solid #e2e8f0;
}

.rc-a4-sheet__title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: 0.02em;
  text-align: left;
  flex: 1;
  min-width: 0;
}

.rc-a4-sheet--landscape .rc-a4-sheet__title {
  font-size: 15px;
}

.rc-a4-sheet__period {
  margin: 0;
  font-size: 11px;
  color: #64748b;
  text-align: right;
  flex-shrink: 0;
  white-space: nowrap;
}

.rc-a4-section {
  margin-bottom: 8px;
}

.rc-a4-section:last-child {
  margin-bottom: 0;
}

.rc-a4-section__title {
  margin: 0 0 4px;
  font-size: 11px;
  font-weight: 600;
  color: #1e40af;
  line-height: 1.35;
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
  padding: 3px 6px;
  font-size: 9px;
  line-height: 1.4;
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
  height: 168px;
  width: 100%;
}

.rc-a4-sheet--landscape .rc-a4-chart {
  height: 188px;
}

.rc-a4-chart--bar {
  height: 188px;
}

.rc-a4-sheet--landscape .rc-a4-chart--bar {
  height: 188px;
}

.rc-a4-summary {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #e2e8f0;
}

.rc-a4-summary__heading {
  margin: 0 0 6px;
  font-size: 10px;
  font-weight: 600;
  color: #475569;
}

.rc-a4-summary__block {
  margin-bottom: 6px;
}

.rc-a4-summary__block:last-child {
  margin-bottom: 0;
}

.rc-a4-summary__block-title {
  display: block;
  font-size: 9px;
  font-weight: 600;
  color: #1e40af;
  margin-bottom: 4px;
}

.rc-a4-summary__grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 6px;
}

.rc-a4-summary__grid--inv {
  grid-template-columns: repeat(3, 1fr);
}

.rc-a4-summary__item {
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 6px 8px;
  text-align: center;
  min-width: 0;
}

.rc-a4-summary__label {
  display: block;
  font-size: 9px;
  color: #64748b;
  margin-bottom: 2px;
  line-height: 1.25;
}

.rc-a4-summary__value {
  display: block;
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.2;
}

.rc-a4-summary__value--pos {
  color: #059669;
}

.rc-a4-summary__value--neg {
  color: #dc2626;
}

.rc-a4-summary__sub {
  display: block;
  margin-top: 1px;
  font-size: 8px;
  font-weight: 500;
  color: #94a3b8;
}

.rc-preview__summary :deep(.cutting-report-summary .cr-header) {
  display: none;
}

.rc-preview__summary :deep(.cutting-report-summary .cr-kpi-row) {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
  margin-bottom: 8px;
}

.rc-preview__summary :deep(.cr-kpi) {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 6px 8px;
  text-align: center;
}

.rc-preview__summary :deep(.cr-kpi__label) {
  display: block;
  font-size: 10px;
  color: #64748b;
  margin-bottom: 2px;
}

.rc-preview__summary :deep(.cr-kpi b) {
  font-size: 13px;
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
  margin: 0 0 6px;
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
  padding: 4px 6px;
  border: 1px solid #cbd5e1;
}

.rc-preview__summary :deep(.cr-table td) {
  padding: 3px 6px;
  border: 1px solid #e2e8f0;
}

.rc-preview__summary :deep(.cr-table tfoot th) {
  background: #f8fafc;
}


.rc-panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.rc-panel__title-wrap {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.rc-panel__dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-top: 5px;
  flex-shrink: 0;
}

.rc-panel__dot--sched {
  background: #6366f1;
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.18);
}

.rc-panel__dot--logs {
  background: #f59e0b;
  box-shadow: 0 0 0 4px rgba(245, 158, 11, 0.18);
}

.rc-panel__title {
  margin: 0;
  font-size: 15px;
  font-weight: 800;
  line-height: 1.2;
  color: #1e293b;
}

.rc-panel__sub {
  margin: 2px 0 0;
  font-size: 11px;
  color: var(--rc-muted);
}

.rc-table-wrap {
  position: relative;
  overflow: auto;
  border-radius: 12px;
  border: 1px solid #e0e7ff;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 10px 22px -16px rgba(79, 70, 229, 0.25);
}

.rc-table-wrap::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  z-index: 2;
  background: linear-gradient(90deg, #6366f1, #a855f7, #ec4899);
}

.rc-table {
  width: 100%;
}

.rc-table :deep(.el-table__header th) {
  background: linear-gradient(180deg, #f5f3ff 0%, #eef2ff 100%) !important;
  color: #3730a3;
  font-size: 11px;
  font-weight: 700;
  padding: 7px 0;
  border-bottom: 1px solid #c7d2fe;
}

.rc-table--sched :deep(.el-table__header th) {
  background: linear-gradient(180deg, #eff6ff 0%, #e0f2fe 100%) !important;
  color: #1d4ed8;
}

.rc-table--logs :deep(.el-table__header th) {
  background: linear-gradient(180deg, #fffbeb 0%, #fef3c7 100%) !important;
  color: #b45309;
}

.rc-table :deep(.el-table__body td) {
  font-size: 12px;
  padding: 6px 0;
}

.rc-table :deep(.el-table__row:hover > td) {
  background: linear-gradient(90deg, rgba(99, 102, 241, 0.06) 0%, rgba(139, 92, 246, 0.04) 100%) !important;
}

.rc-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.rc-cell-report {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

.rc-cell-report__name {
  font-weight: 700;
  font-size: 12px;
  line-height: 1.3;
}

.rc-cell-report__code {
  display: inline-block;
  width: fit-content;
  margin-top: 2px;
  padding: 0 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  color: #4338ca;
  background: #eef2ff;
  box-shadow: inset 0 0 0 1px #e0e7ff;
  font-variant-numeric: tabular-nums;
}

.rc-pill {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  line-height: 1.4;
}

.rc-pill--freq {
  background: #eef2ff;
  color: #4338ca;
}

.rc-pill--fmt {
  background: #f1f5f9;
  color: #475569;
}

.rc-pill--auto {
  background: #e0f2fe;
  color: #0369a1;
}

.rc-pill--manual {
  background: #ccfbf1;
  color: #0f766e;
}

.row-act {
  --act: #6366f1;
  --act-to: #4f46e5;
  padding: 2px 10px !important;
  height: 22px;
  border-radius: 999px;
  font-weight: 700;
  color: var(--act) !important;
  background: color-mix(in srgb, var(--act) 9%, transparent);
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--act) 22%, transparent);
  transition:
    transform 0.18s cubic-bezier(0.2, 0.8, 0.2, 1),
    box-shadow 0.18s ease,
    background 0.18s ease,
    color 0.18s ease;
}

.row-act + .row-act { margin-left: 4px; }

.row-act:hover {
  color: #fff !important;
  background: linear-gradient(135deg, var(--act), var(--act-to));
  transform: translateY(-1px);
  box-shadow: 0 6px 12px -4px var(--act-to);
}

.row-act.act-edit { --act: #3b82f6; --act-to: #1d4ed8; }
.row-act.act-delete { --act: #f43f5e; --act-to: #be123c; }

/* ---------- ダイアログ ---------- */
.rc-dlg-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 20px 24px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.92) 0%, rgba(139, 92, 246, 0.95) 100%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.rc-dlg-header--blue {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.92) 0%, rgba(37, 99, 235, 0.95) 100%);
}

.rc-dlg-icon-wrap {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.rc-dlg-icon { font-size: 22px; color: #fff; }

.rc-dlg-title-wrap {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.rc-dlg-title {
  font-size: 16px;
  font-weight: 700;
  color: #fff;
  line-height: 1.3;
}

.rc-dlg-subtitle {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.88);
  font-weight: 500;
}

.rc-dlg-body { padding: 18px 24px 8px; }

.rc-dlg-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.rc-dlg-btn-cancel {
  border-radius: 10px;
  padding: 8px 18px;
  font-weight: 500;
  border: 1px solid rgba(0, 0, 0, 0.12);
  color: #475569;
}

.rc-dlg-btn-submit {
  border-radius: 10px;
  padding: 8px 20px;
  font-weight: 600;
  border: none !important;
  background: linear-gradient(135deg, #818cf8 0%, #6366f1 100%) !important;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
}

.rc-dlg-btn-submit--blue {
  background: linear-gradient(135deg, #60a5fa 0%, #2563eb 100%) !important;
  box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35);
}

.rc-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.rc-actions__format { width: 100px; }

.rc-modern .rc-actions__format :deep(.el-select__wrapper),
.rc-modern .rc-field__control :deep(.el-select__wrapper),
.rc-modern .rc-field__control :deep(.el-input__wrapper) {
  border-radius: 9px;
  background-color: #f8fafc;
  box-shadow:
    0 0 0 1px #dfe3f0 inset,
    0 1px 2px rgba(15, 23, 42, 0.05);
}

.rc-modern .rc-detail {
  border-color: #e0e7ff;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  border-radius: 12px;
}

.rc-modern .rc-detail__code {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  font-weight: 700;
  color: #4338ca;
  background: #eef2ff;
  box-shadow: inset 0 0 0 1px #e0e7ff;
}

@media (max-width: 960px) {
  .toolbar-left {
    flex-direction: column;
    align-items: flex-start;
  }

  .rc-layout {
    grid-template-columns: 1fr;
  }

  .rc-list {
    max-height: 200px;
  }

  .rc-preview__meta {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .rc-toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .rc-actions {
    justify-content: flex-end;
  }

  .rc-a4-summary__grid {
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  }
}

@media (max-width: 480px) {
  .rc-page { padding: 8px; }
  .rc-stat-chips { width: 100%; }
  .rc-chip { flex: 1; justify-content: center; }
  .rc-tab { padding: 6px 10px; font-size: 11px; }
  .rc-actions__format { width: 100%; }
}
</style>

<style>
.rc-dialog.el-dialog {
  border-radius: 16px;
  overflow: hidden;
  box-shadow:
    0 24px 64px rgba(0, 0, 0, 0.18),
    0 0 0 1px rgba(255, 255, 255, 0.5) inset;
}
.rc-dialog .el-dialog__header {
  padding: 0;
  margin: 0;
}
.rc-dialog .el-dialog__body {
  padding: 0;
  background: linear-gradient(180deg, #fafbff 0%, #f5f6fb 100%);
}
.rc-dialog .el-dialog__footer {
  padding: 14px 24px 20px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  background: #fff;
}
</style>

