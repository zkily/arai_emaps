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

            <div class="rc-preview__summary" v-html="preview.summary_html"></div>
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
              @change="(v: boolean) => toggleSchedule(row, v)"
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
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, Download, Plus, Promotion, Refresh, View } from '@element-plus/icons-vue'
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

function selectDefinition(d: ReportDefinition) {
  selected.value = d
  preview.value = null
  sendFormat.value = d.default_format === 'both' ? 'both' : (d.default_format || 'xlsx')
  Object.keys(paramState).forEach((k) => delete paramState[k])
  for (const field of d.parameter_schema?.fields || []) {
    paramState[field.key] = field.default || (field.presets ? field.presets[0] : '')
  }
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

async function doPreview() {
  if (!selected.value) return
  previewLoading.value = true
  try {
    preview.value = await previewReport(selected.value.report_code, buildParameters())
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
const scheduleDateRange = ref('yesterday')

function openScheduleDialog(row?: ReportSchedule) {
  if (row) {
    Object.assign(editingSchedule, row)
    weekdayValue.value = Number((row.schedule_config as { weekday?: number })?.weekday ?? 0)
    monthDayValue.value = Number((row.schedule_config as { day?: number })?.day ?? 1)
    scheduleTimeValue.value = row.schedule_time || '08:00:00'
    scheduleDateRange.value = String((row.parameters as { date_range?: string; month?: string })?.date_range
      ?? (row.parameters as { month?: string })?.month ?? 'yesterday')
  } else {
    Object.keys(editingSchedule).forEach((k) => delete (editingSchedule as Record<string, unknown>)[k])
    editingSchedule.report_code = definitions.value[0]?.report_code
    editingSchedule.schedule_type = 'daily'
    editingSchedule.format = null
    editingSchedule.is_active = true
    weekdayValue.value = 0
    monthDayValue.value = 1
    scheduleTimeValue.value = '08:00:00'
    scheduleDateRange.value = 'yesterday'
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
  if (definitions.value.length && !selected.value) selectDefinition(definitions.value[0])
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

onMounted(loadAll)
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
