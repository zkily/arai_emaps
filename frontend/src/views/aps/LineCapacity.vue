<template>
  <div class="capacity-page" :class="{ 'capacity-page--embed': embed }">
    <el-card :shadow="embed ? 'never' : 'hover'" class="capacity-card" :body-style="{ padding: embed ? '8px 10px' : '10px 12px' }">
      <template #header>
        <div v-if="embed" class="card-head card-head--embed">
          <h3 class="card-head__title">設備稼働設定</h3>
          <p class="card-head__desc card-head__desc--embed">
            表示中ライン・ガント期間の時間帯を編集します（保存で反映）。
          </p>
        </div>
        <div v-else class="card-head">
          <h3 class="card-head__title">設備稼働設定</h3>
          <p class="card-head__desc">
            日別の稼働時間帯を設定します。「休憩」にした行は稼働合計・排産から除外（稼働帯との重複分のみ差引）。
          </p>
        </div>
      </template>

      <el-form v-if="!embed" class="toolbar" :inline="true" label-position="left" size="small">
        <el-form-item label="設備" class="toolbar__item">
          <el-select v-model="selectedLineId" placeholder="選択" class="toolbar__select" @change="loadData">
            <el-option
              v-for="line in lines"
              :key="line.id"
              :value="line.id"
              :label="productionLineOptionLabel(line)"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="期間" class="toolbar__item">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="〜"
            start-placeholder="開始"
            end-placeholder="終了"
            value-format="YYYY-MM-DD"
            class="toolbar__daterange"
            @change="loadData"
          />
        </el-form-item>
        <el-form-item class="toolbar__item toolbar__item--btn">
          <el-button type="primary" :loading="loading" @click="loadData">再取得</el-button>
        </el-form-item>
      </el-form>
      <div v-else class="toolbar toolbar--embed">
        <span class="toolbar-embed__line">{{ embedLineLabel }}</span>
        <span class="toolbar-embed__range">{{ presetDateRange?.[0] }} 〜 {{ presetDateRange?.[1] }}</span>
        <el-button type="primary" size="small" :loading="loading" @click="loadData">再取得</el-button>
      </div>

      <div v-loading="loading" class="calendar-grid">
        <div v-if="daySlots.length === 0 && !loading" class="empty">設備と期間を選んで「再取得」してください</div>
        <div
          v-for="day in daySlots"
          :key="day.work_date"
          class="day-card"
          :class="{ 'day-card--weekend': isWeekend(day.work_date) }"
        >
          <div class="day-card__top">
            <div class="day-card__meta">
              <span class="day-card__date">{{ formatDate(day.work_date) }}</span>
              <span class="day-card__wd">({{ getWeekday(day.work_date) }})</span>
              <el-tag size="small" effect="plain" :type="calcProductiveHours(day) > 0 ? 'success' : 'info'" class="day-card__tag">
                {{ calcProductiveHours(day).toFixed(1) }}h
              </el-tag>
            </div>
            <div class="day-card__actions">
              <el-button
                type="primary"
                size="small"
                plain
                title="08:00–12:00 / 13:00–17:00 / 21:00–00:00 / 01:00–06:00"
                @click="applyStandardShift(day)"
              >
                標準4帯
              </el-button>
              <el-button type="warning" size="small" plain title="17:00–19:00 / 06:00–08:00" @click="appendOvertimeSlots(day)">
                残業
              </el-button>
              <el-button
                type="info"
                size="small"
                plain
                title="12:00–13:00 / 00:00–01:00 を休憩として追加"
                @click="appendRestSlots(day)"
              >
                昼休憩
              </el-button>
              <el-button
                type="info"
                size="small"
                plain
                title="10:00–10:10 / 15:00–15:10 / 00:00–00:10 / 04:00–04:10"
                @click="appendFixedDailyBreaks(day)"
              >
                定刻休憩
              </el-button>
              <el-button type="success" size="small" plain title="全日24h（00:00–00:00）" @click="applyFullDay24h(day)">
                24h
              </el-button>
              <el-button
                type="danger"
                size="small"
                plain
                :disabled="day.editSlots.length === 0"
                title="この日の時間帯をすべて削除（保存でDB反映）"
                @click="clearAllSlots(day)"
              >
                時間帯全削除
              </el-button>
            </div>
          </div>
          <div class="slots-list">
            <div
              v-for="(slot, idx) in day.editSlots"
              :key="idx"
              class="slot-row"
              :class="{ 'slot-row--rest': slot.is_rest }"
            >
              <div class="slot-row__times">
                <el-time-picker
                  v-model="slot.start_time"
                  placeholder="開始"
                  format="HH:mm"
                  value-format="HH:mm:ss"
                  size="small"
                  popper-class="lcap-time-popper"
                  class="slot-row__time"
                />
                <span class="slot-row__tilde">〜</span>
                <el-time-picker
                  v-model="slot.end_time"
                  placeholder="終了"
                  format="HH:mm"
                  value-format="HH:mm:ss"
                  size="small"
                  popper-class="lcap-time-popper"
                  class="slot-row__time"
                />
              </div>
              <div class="slot-row__side">
                <el-checkbox v-model="slot.is_rest" size="small" class="slot-row__chk">休憩</el-checkbox>
                <el-button type="danger" size="small" link class="slot-row__del" @click="removeSlot(day, idx)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
            <el-button type="primary" size="small" link class="slots-list__add" @click="addSlot(day)">
              <el-icon><Plus /></el-icon>
              行を追加
            </el-button>
          </div>
          <div class="day-card__total">
            実稼働計 <span class="day-card__total-num">{{ calcProductiveHours(day).toFixed(1) }}</span> h
          </div>
        </div>
      </div>

      <div v-if="daySlots.length > 0" class="save-bar">
        <el-button type="success" :loading="saving" @click="saveAll">一括保存</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Plus } from '@element-plus/icons-vue'
import {
  fetchLines,
  fetchLineCapacitySlots,
  batchUpsertLineCapacitySlots,
  productionLineOptionLabel,
  type ProductionLine,
  type DaySlotsOut,
} from '@/api/aps'

interface EditSlot {
  start_time: string
  end_time: string
  is_rest?: boolean
}

interface DayEdit extends DaySlotsOut {
  editSlots: EditSlot[]
}

const props = withDefaults(
  defineProps<{
    /** 成型計画作成（FormingPlanning）等のダイアログ内で利用 */
    embed?: boolean
    presetLineId?: number | null
    presetDateRange?: [string, string] | null
  }>(),
  {
    embed: false,
    presetLineId: null,
    presetDateRange: null,
  },
)

const emit = defineEmits<{
  /** 時間帯を保存し DB に反映した後（親でガント等を再取得する用） */
  (e: 'saved'): void
}>()

const embed = computed(() => props.embed)

const lines = ref<ProductionLine[]>([])
const selectedLineId = ref<number | null>(null)
const dateRange = ref<[string, string] | null>(null)
const loading = ref(false)
const saving = ref(false)
const daySlots = ref<DayEdit[]>([])

const embedLineLabel = computed(() => {
  if (props.presetLineId == null) return '—'
  const ln = lines.value.find(l => l.id === props.presetLineId)
  if (!ln) return `ID ${props.presetLineId}`
  return productionLineOptionLabel(ln)
})

async function loadData() {
  if (!selectedLineId.value || !dateRange.value) return
  loading.value = true
  try {
    const data = await fetchLineCapacitySlots(selectedLineId.value, dateRange.value[0], dateRange.value[1])
    daySlots.value = data.map(d => ({
      ...d,
      editSlots: d.slots.length > 0
        ? d.slots.map(s => ({
          start_time: s.start_time,
          end_time: s.end_time,
          is_rest: Boolean(s.is_rest),
        }))
        : [],
    }))
  } catch (e: any) {
    ElMessage.error(e?.message || '取得に失敗しました')
  } finally {
    loading.value = false
  }
}

watch(
  () => [props.embed, props.presetLineId, props.presetDateRange] as const,
  ([em, lid, dr]) => {
    if (!em || lid == null || !dr?.[0] || !dr?.[1]) return
    selectedLineId.value = lid
    dateRange.value = [dr[0], dr[1]]
    void loadData()
  },
  { immediate: true },
)

onMounted(async () => {
  try {
    const data = await fetchLines()
    lines.value = data
  } catch { /* ignore */ }
})

const STANDARD_SHIFT_SLOTS: EditSlot[] = [
  { start_time: '08:00:00', end_time: '12:00:00', is_rest: false },
  { start_time: '13:00:00', end_time: '17:00:00', is_rest: false },
  { start_time: '21:00:00', end_time: '00:00:00', is_rest: false },
  { start_time: '01:00:00', end_time: '06:00:00', is_rest: false },
]

const OVERTIME_PRESET_SLOTS: EditSlot[] = [
  { start_time: '17:00:00', end_time: '19:00:00', is_rest: false },
  { start_time: '06:00:00', end_time: '08:00:00', is_rest: false },
]

/** 昼休み等（稼働から除く） */
const REST_PRESET_SLOTS: EditSlot[] = [
  { start_time: '12:00:00', end_time: '13:00:00', is_rest: true },
  { start_time: '00:00:00', end_time: '01:00:00', is_rest: true },
]

/** 毎日固定の短い休憩（稼働から除く） */
const FIXED_DAILY_BREAK_SLOTS: EditSlot[] = [
  { start_time: '10:00:00', end_time: '10:10:00', is_rest: true },
  { start_time: '15:00:00', end_time: '15:10:00', is_rest: true },
  { start_time: '00:00:00', end_time: '00:10:00', is_rest: true },
  { start_time: '04:00:00', end_time: '04:10:00', is_rest: true },
]

/** 開始・終了とも 00:00:00 の一致＝全日24h（API・engine と同じ約束） */
const FULL_DAY_24H_SLOT: EditSlot = { start_time: '00:00:00', end_time: '00:00:00', is_rest: false }

function applyStandardShift(day: DayEdit) {
  day.editSlots = STANDARD_SHIFT_SLOTS.map(s => ({ ...s }))
}

function appendOvertimeSlots(day: DayEdit) {
  for (const s of OVERTIME_PRESET_SLOTS) {
    day.editSlots.push({ ...s })
  }
}

function appendRestSlots(day: DayEdit) {
  for (const s of REST_PRESET_SLOTS) {
    day.editSlots.push({ ...s })
  }
}

function appendFixedDailyBreaks(day: DayEdit) {
  for (const s of FIXED_DAILY_BREAK_SLOTS) {
    day.editSlots.push({ ...s })
  }
}

function applyFullDay24h(day: DayEdit) {
  day.editSlots = [{ ...FULL_DAY_24H_SLOT }]
}

function addSlot(day: DayEdit) {
  day.editSlots.push({ start_time: '08:00:00', end_time: '17:00:00', is_rest: false })
}

function removeSlot(day: DayEdit, idx: number) {
  day.editSlots.splice(idx, 1)
}

async function clearAllSlots(day: DayEdit) {
  if (day.editSlots.length === 0) return
  try {
    await ElMessageBox.confirm(
      `${day.work_date} の時間帯をすべて削除しますか？（未保存の場合は画面のみクリア。DB反映は「一括保存」が必要です。）`,
      '時間帯の全削除',
      {
        type: 'warning',
        confirmButtonText: '削除する',
        cancelButtonText: 'キャンセル',
        distinguishCancelAndClose: true,
      },
    )
    day.editSlots = []
  } catch {
    /* キャンセル */
  }
}

function timeToMinutes(t: string): number {
  const p = t.split(':').map(Number)
  return Math.floor(p[0] * 60 + p[1] + (p[2] || 0) / 60)
}

function isMidnightWall(t: string): boolean {
  const p = t.split(':').map(Number)
  return p[0] === 0 && p[1] === 0 && (p[2] || 0) === 0
}

function expandSlotToMinuteParts(startTime: string, endTime: string): [number, number][] {
  const sm = timeToMinutes(startTime)
  const em = timeToMinutes(endTime)
  if (sm === em) {
    if (isMidnightWall(startTime) && isMidnightWall(endTime)) return [[0, 1440]]
    return []
  }
  if (em > sm) return [[sm, em]]
  const parts: [number, number][] = [[sm, 1440]]
  if (em > 0) parts.push([0, em])
  return parts
}

function mergeMinuteIntervals(intervals: [number, number][]): [number, number][] {
  if (intervals.length === 0) return []
  const sorted = [...intervals].sort((a, b) => a[0] - b[0])
  const out: [number, number][] = [[sorted[0][0], sorted[0][1]]]
  for (let i = 1; i < sorted.length; i++) {
    const [s, e] = sorted[i]
    const [ps, pe] = out[out.length - 1]
    if (s <= pe) out[out.length - 1] = [ps, Math.max(pe, e)]
    else out.push([s, e])
  }
  return out
}

function subtractRestFromWork(
  work: [number, number][],
  rest: [number, number][],
): [number, number][] {
  if (work.length === 0) return []
  if (rest.length === 0) return work
  const rSorted = [...rest].sort((a, b) => a[0] - b[0])
  const out: [number, number][] = []
  for (const [ws, we] of work) {
    let parts: [number, number][] = [[ws, we]]
    for (const [rs, re] of rSorted) {
      const newParts: [number, number][] = []
      for (const [a, b] of parts) {
        if (re <= a || rs >= b) newParts.push([a, b])
        else {
          if (a < rs) newParts.push([a, Math.min(rs, b)])
          if (re < b) newParts.push([Math.max(re, a), b])
        }
      }
      parts = newParts
    }
    out.push(...parts)
  }
  return mergeMinuteIntervals(out)
}

/** 非休憩帯を結合し、休憩帯を差し引いた実稼働時間（h）— バックエンド engine と同趣旨 */
function calcProductiveHours(day: DayEdit): number {
  const workRaw: [number, number][] = []
  const restRaw: [number, number][] = []
  for (const slot of day.editSlots) {
    if (!slot.start_time || !slot.end_time) continue
    const parts = expandSlotToMinuteParts(slot.start_time, slot.end_time)
    if (slot.is_rest) restRaw.push(...parts)
    else workRaw.push(...parts)
  }
  const workM = mergeMinuteIntervals(workRaw)
  const restM = mergeMinuteIntervals(restRaw)
  const productive = subtractRestFromWork(workM, restM)
  return productive.reduce((acc, [sm, em]) => acc + (em - sm) / 60, 0)
}

async function saveAll() {
  if (!selectedLineId.value) return
  saving.value = true
  try {
    const days = daySlots.value.map(d => ({
      line_id: selectedLineId.value!,
      work_date: d.work_date,
      slots: d.editSlots
        .filter(s => s.start_time && s.end_time)
        .map((s, idx) => ({
          start_time: s.start_time,
          end_time: s.end_time,
          sort_order: idx,
          is_rest: Boolean(s.is_rest),
        })),
    }))
    await batchUpsertLineCapacitySlots({ line_id: selectedLineId.value, days })
    ElMessage.success('保存しました')
    await loadData()
    emit('saved')
  } catch (e: any) {
    ElMessage.error(e?.message || '保存に失敗しました')
  } finally {
    saving.value = false
  }
}

function formatDate(d: string): string {
  return d.slice(5)
}

function getWeekday(d: string): string {
  const wd = ['日', '月', '火', '水', '木', '金', '土']
  return wd[new Date(d).getDay()]
}

function isWeekend(d: string): boolean {
  const day = new Date(d).getDay()
  return day === 0 || day === 6
}
</script>

<style scoped>
.capacity-page {
  padding: 8px 10px 12px;
  max-width: 1920px;
  margin: 0 auto;
}

.capacity-page--embed {
  padding: 0;
  max-width: none;
  margin: 0;
}

.toolbar--embed {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
  margin: 0 0 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--el-border-color-extra-light);
  font-size: 12px;
}

.toolbar-embed__line {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.toolbar-embed__range {
  color: var(--el-text-color-secondary);
  font-variant-numeric: tabular-nums;
}

.card-head--embed .card-head__title {
  margin-bottom: 0;
}

.card-head__desc--embed {
  margin-top: 4px;
  margin-bottom: 0;
}

.capacity-card :deep(.el-card__header) {
  padding: 8px 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.capacity-card :deep(.el-card__body) {
  min-width: 0;
}

.card-head__title {
  margin: 0 0 2px;
  font-size: 15px;
  font-weight: 600;
  line-height: 1.35;
  color: var(--el-text-color-primary);
  letter-spacing: 0.02em;
}

.card-head__desc {
  margin: 0;
  font-size: 11px;
  line-height: 1.45;
  color: var(--el-text-color-secondary);
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 0 4px;
  margin: 0 0 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--el-border-color-extra-light);
}

.toolbar :deep(.el-form-item) {
  margin-bottom: 0;
  margin-right: 10px;
}

.toolbar :deep(.el-form-item__label) {
  padding-right: 6px;
  font-size: 12px;
}

.toolbar__select {
  width: 220px;
}

.toolbar__daterange {
  width: 230px;
}

.toolbar__item--btn {
  margin-right: 0 !important;
}

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(270px, 1fr));
  gap: 8px;
  align-items: start;
  min-height: 120px;
}

.day-card {
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 4px;
  padding: 6px 8px 6px;
  background: var(--el-bg-color);
  transition: border-color 0.15s, box-shadow 0.15s;
  /* grid 子项默认 min-width:auto 会按内容撑破列宽 */
  min-width: 0;
  max-width: 100%;
  box-sizing: border-box;
}

.day-card:hover {
  border-color: var(--el-border-color);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.day-card--weekend {
  background: var(--el-fill-color-lighter);
}

.day-card__top {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 4px;
  padding-bottom: 4px;
  border-bottom: 1px solid var(--el-border-color-extra-light);
}

.day-card__meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px 6px;
}

.day-card__date {
  font-size: 13px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.day-card__wd {
  font-size: 11px;
  color: var(--el-text-color-secondary);
}

.day-card__tag {
  margin-left: auto;
  font-variant-numeric: tabular-nums;
}

.day-card__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 3px 4px;
}

.day-card__actions :deep(.el-button) {
  padding: 4px 7px;
  margin: 0;
  font-size: 11px;
}

.slots-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  max-width: 100%;
}

.slot-row {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  gap: 6px;
  padding: 3px 4px;
  border-radius: 3px;
  min-width: 0;
  max-width: 100%;
  box-sizing: border-box;
}

.slot-row--rest {
  background: var(--el-fill-color-light);
}

/* 開始 〜 終了（不换行；flex:1 仅吃剩余空间，避免把侧栏挤出卡片） */
.slot-row__times {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  gap: 4px 6px;
  flex: 1 1 0;
  min-width: 0;
}

/*
 * el-time-picker 根为 .el-date-editor，宽度来自 --el-date-editor-width（默认约 220px），
 * 只改 .el-input 无效，必须改变量 + .el-date-editor。
 */
.slot-row__time {
  --el-date-editor-width: 60px;
  width: 60px !important;
  max-width: 60px !important;
  min-width: 60px !important;
  flex-shrink: 0;
  box-sizing: border-box;
}

.slot-row__time :deep(.el-date-editor.el-input__wrapper),
.slot-row__time :deep(.el-date-editor) {
  width: 60px !important;
  max-width: 60px !important;
  min-width: 60px !important;
  box-sizing: border-box;
}

.slot-row__time :deep(.el-input__wrapper) {
  padding: 0 4px;
}

.slot-row__time :deep(.el-input__inner) {
  font-size: 12px;
  text-align: center;
}

/* 時計アイコンを隠して幅を実表示に寄せる（クリックは入力欄全体で可能） */
.slot-row__time :deep(.el-input__prefix) {
  display: none;
}

.slot-row__tilde {
  flex-shrink: 0;
  font-size: 11px;
  color: var(--el-text-color-secondary);
  padding: 0 1px;
  line-height: 1;
}

/* 休憩 + 削除：同一行右側 */
.slot-row__side {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 0 0 auto;
  margin-left: auto;
  flex-shrink: 0;
}

.slot-row__chk :deep(.el-checkbox__label) {
  padding-left: 4px;
  font-size: 11px;
}

.slot-row__del {
  padding: 4px;
  min-height: auto;
}

.slots-list__add {
  margin-top: 2px;
  padding: 2px 0;
  font-size: 12px;
  align-self: flex-start;
}

.day-card__total {
  margin-top: 4px;
  padding-top: 4px;
  border-top: 1px solid var(--el-border-color-extra-light);
  font-size: 11px;
  color: var(--el-text-color-secondary);
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.day-card__total-num {
  font-size: 12px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.save-bar {
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px solid var(--el-border-color-extra-light);
  text-align: center;
}

.empty {
  grid-column: 1 / -1;
  text-align: center;
  padding: 20px 12px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
</style>

<style>
/* teleported 弹出层：縮窄時間面板（Element Plus 默认 .el-time-panel 180px） */
.lcap-time-popper.el-picker__popper {
  width: auto !important;
  max-width: 128px;
}
.lcap-time-popper .el-time-panel {
  width: 118px !important;
  min-width: 118px !important;
  box-sizing: border-box;
}
.lcap-time-popper .el-time-panel__content {
  box-sizing: border-box;
}
/* 若仍显示秒列，面板需要更宽 */
.lcap-time-popper .el-time-panel__content.has-seconds {
  min-width: 168px;
}
.lcap-time-popper .el-time-panel:has(.has-seconds) {
  width: 168px !important;
  min-width: 168px !important;
  max-width: 180px;
}
</style>
