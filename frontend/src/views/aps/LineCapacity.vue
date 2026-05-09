<template>
  <div class="capacity-page" :class="{ 'capacity-page--embed': embed }">
    <el-card :shadow="embed ? 'never' : 'hover'" class="capacity-card" :body-style="{ padding: embed ? '8px 10px' : '10px 12px' }">
      <template #header>
        <div v-if="embed" class="card-head card-head--embed card-head--with-actions">
          <div class="card-head__main">
            <h3 class="card-head__title">設備稼働設定</h3>
            <p class="card-head__desc card-head__desc--embed">
              表示中ライン・ガント期間の時間帯を編集します（保存で反映）。
            </p>
          </div>
          <div v-if="daySlots.length > 0" class="card-head__actions">
            <el-button type="success" size="small" :loading="saving" @click="saveAll">一括保存</el-button>
          </div>
        </div>
        <div v-else class="card-head card-head--with-actions">
          <div class="card-head__main">
            <h3 class="card-head__title">設備稼働設定</h3>
            <p class="card-head__desc">
              日別の稼働時間帯を設定します。「休憩」にした行は稼働合計・排産から除外（稼働帯との重複分のみ差引）。
            </p>
          </div>
          <div v-if="daySlots.length > 0" class="card-head__actions">
            <el-button type="success" size="small" :loading="saving" @click="saveAll">一括保存</el-button>
          </div>
        </div>
      </template>

      <template v-if="!embed">
      <el-form class="toolbar toolbar--filter-bar" :inline="true" label-position="left" size="small">
        <el-form-item label="工程" class="toolbar__item">
          <el-select
            v-model="selectedProcessCd"
            clearable
            filterable
            placeholder="全工程"
            class="toolbar__select"
            @change="onProcessFilterChange"
          >
            <el-option
              v-for="p in processOptions"
              :key="p.process_cd"
              :label="processOptionLabel(p)"
              :value="p.process_cd"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="設備" class="toolbar__item">
          <el-select v-model="selectedLineId" placeholder="選択" class="toolbar__select">
            <el-option
              v-for="line in lines"
              :key="line.id"
              :value="line.id"
              :label="lineOptionLabel(line)"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="期間" class="toolbar__item toolbar__item--range">
          <div class="toolbar__range-block">
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="〜"
              start-placeholder="開始"
              end-placeholder="終了"
              value-format="YYYY-MM-DD"
              class="toolbar__daterange"
            />
            <div class="toolbar__quick-months">
              <el-button type="primary" plain class="toolbar__quick-month-btn" size="small" @click="applyThisMonthRange">
                今月
              </el-button>
              <el-button type="success" plain class="toolbar__quick-month-btn" size="small" @click="applyNextMonthRange">
                次月
              </el-button>
            </div>
          </div>
        </el-form-item>
        <el-form-item label="土日表示" class="toolbar__item toolbar__item--week">
          <div class="toolbar__week-toggles">
            <span class="toolbar__week-toggle">
              <span class="toolbar__week-toggle-label">土曜</span>
              <el-switch v-model="showSaturday" size="small" />
            </span>
            <span class="toolbar__week-toggle">
              <span class="toolbar__week-toggle-label">日曜</span>
              <el-switch v-model="showSunday" size="small" />
            </span>
          </div>
        </el-form-item>
      </el-form>

      <div v-if="daySlots.length > 0" class="bulk-apply-panel">
        <div class="bulk-apply-panel__head">
          <span class="bulk-apply-panel__title">一括時間帯</span>
          <span class="bulk-apply-panel__hint">
            表示中 <strong>{{ displayDaySlots.length }}</strong> 日に同一プリセットを適用（反映には「一括保存」）
          </span>
        </div>
        <div class="bulk-apply-panel__actions">
          <el-button type="info" size="small" plain @click="batchApplyPreset('4h')">4H</el-button>
          <el-button type="success" size="small" plain @click="batchApplyPreset('8h')">8H</el-button>
          <el-button type="primary" size="small" plain @click="batchApplyPreset('16h')">16H</el-button>
          <el-button type="warning" size="small" plain @click="batchApplyPreset('20h')">20H</el-button>
          <el-button plain class="lcap-preset--22h" size="small" @click="batchApplyPreset('22h')">22H</el-button>
          <el-button plain class="lcap-preset--24h" size="small" @click="batchApplyPreset('24h')">24H</el-button>
          <el-button type="danger" size="small" plain @click="batchApplyPreset('clear')">全日削除</el-button>
        </div>
      </div>
      </template>
      <div v-else class="toolbar toolbar--embed">
        <span class="toolbar-embed__line">{{ embedLineLabel }}</span>
        <span class="toolbar-embed__range">{{ presetDateRange?.[0] }} 〜 {{ presetDateRange?.[1] }}</span>
        <el-button type="primary" size="small" :loading="loading" @click="loadData">再取得</el-button>
      </div>

      <div v-loading="loading" class="calendar-grid-scroll">
        <div class="calendar-grid">
          <div v-if="daySlots.length === 0 && !loading" class="empty">
            {{ embed ? '設備と期間を選んで「再取得」してください' : '設備と期間を選択すると自動で読み込みます' }}
          </div>
          <div
            v-else-if="displayDaySlots.length === 0 && !loading && daySlots.length > 0"
            class="empty"
          >
            この条件では表示する日がありません（土曜・日曜の表示をオンにするか、期間を変更してください）
          </div>
          <div
            v-for="day in displayDaySlots"
            :key="day.work_date"
            class="day-card"
            :class="{
              'day-card--weekend': isWeekend(day.work_date),
              'day-card--slots-collapsed': slotsCollapsedByDate[day.work_date],
            }"
          >
            <div class="day-card__top">
            <div class="day-card__meta">
              <span class="day-card__date">{{ formatDate(day.work_date) }}</span>
              <span class="day-card__wd">({{ getWeekday(day.work_date) }})</span>
              <el-button
                v-if="slotsCollapsedByDate[day.work_date]"
                link
                type="primary"
                size="small"
                class="day-card__expand-slots"
                @click="showSlotsEditor(day)"
              >
                詳細
              </el-button>
              <span
                class="day-card__tag"
                :class="{ 'day-card__tag--zero': calcProductiveHours(day) <= 0 }"
              >{{ calcProductiveHours(day).toFixed(1) }}h</span>
            </div>
            <div class="day-card__actions">
              <el-button
                type="info"
                size="small"
                plain
                title="稼働 08:00–12:00、休憩 10:00–10:10"
                @click="apply4HShift(day)"
              >
                4H
              </el-button>
              <el-button
                type="success"
                size="small"
                plain
                title="稼働 08:00–12:00 / 13:00–17:00、休憩 10:00–10:10 / 15:00–15:10"
                @click="apply8HShift(day)"
              >
                8H
              </el-button>
              <el-button
                type="primary"
                size="small"
                plain
                title="稼働 08:00–12:00 / 13:00–17:00 / 21:00–00:00 / 01:00–06:00、休憩 10:00–10:10 / 15:00–15:10 / 01:00–01:10 / 04:00–04:10"
                @click="applyStandardShift(day)"
              >
                16H
              </el-button>
              <el-button
                type="warning"
                size="small"
                plain
                title="稼働 08:00–12:00 / 13:00–17:00 / 17:00–19:00 / 21:00–00:00 / 01:00–08:00、休憩 10:00–10:10 / 15:00–15:10 / 01:00–01:10 / 04:00–04:10"
                @click="apply20HShift(day)"
              >
                20H
              </el-button>
              <el-button
                plain
                class="lcap-preset--22h"
                size="small"
                title="稼働 08:00–12:00 / 13:00–00:00 / 01:00–08:00、休憩 10:00–10:10 / 15:00–15:10 / 01:00–01:10 / 04:00–04:10"
                @click="apply22HShift(day)"
              >
                22H
              </el-button>
              <el-button
                plain
                class="lcap-preset--24h"
                size="small"
                title="稼働 08:00–08:00（当日08:00〜翌08:00／保存時は 08:00–00:00 と 00:00–08:00 の2行）、休憩 10:00–10:10 / 15:00–15:10 / 01:00–01:10 / 04:00–04:10"
                @click="apply24HCalendarShift(day)"
              >
                24H
              </el-button>
              <el-button
                type="danger"
                size="small"
                plain
                :disabled="day.editSlots.length === 0"
                title="この日の時間帯をすべて削除（保存でDB反映）"
                @click="clearAllSlots(day)"
              >
                削除
              </el-button>
            </div>
          </div>
          <div v-if="!slotsCollapsedByDate[day.work_date]" class="slots-list">
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
          </div>
        </div>
        </div>
      </div>

    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import dayjs from 'dayjs'
import { ElMessage } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'
import {
  fetchLines,
  fetchLineCapacitySlots,
  batchUpsertLineCapacitySlots,
  type ProductionLine,
  type DaySlotsOut,
} from '@/api/aps'
import { fetchProcesses } from '@/api/master/processMaster'
import type { ProcessItem } from '@/types/master'

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

/** 設備稼働設定で選べる工程のみ（切断・面取・成型・溶接）— `processes.process_cd` と一致 */
const LINE_CAPACITY_PROCESS_ORDER = ['KT01', 'KT02', 'KT04', 'KT07'] as const
const LINE_CAPACITY_PROCESS_SET = new Set<string>(LINE_CAPACITY_PROCESS_ORDER)

const processOptions = ref<ProcessItem[]>([])
/** 空＝全工程（fetchLines は processCd 無し） */
const selectedProcessCd = ref<string | undefined>(undefined)

const lines = ref<ProductionLine[]>([])
const selectedLineId = ref<number | null>(null)
const dateRange = ref<[string, string] | null>(null)
const loading = ref(false)
const saving = ref(false)
const daySlots = ref<DayEdit[]>([])
/** 時間帯行を畳む（プリセット・再取得・保存後の再読込いずれでも true／work_date → true） */
const slotsCollapsedByDate = ref<Record<string, boolean>>({})

/** 一覧に土曜・日曜を出すか（既定 OFF＝土日は非表示） */
const showSaturday = ref(false)
const showSunday = ref(false)

const displayDaySlots = computed(() => {
  if (embed.value) return daySlots.value
  return daySlots.value.filter((day) => {
    const wd = new Date(day.work_date).getDay()
    if (wd === 6 && !showSaturday.value) return false
    if (wd === 0 && !showSunday.value) return false
    return true
  })
})

function collapseSlotsEditor(day: DayEdit) {
  slotsCollapsedByDate.value = { ...slotsCollapsedByDate.value, [day.work_date]: true }
}

function showSlotsEditor(day: DayEdit) {
  const next = { ...slotsCollapsedByDate.value }
  delete next[day.work_date]
  slotsCollapsedByDate.value = next
}

const embedLineLabel = computed(() => {
  if (props.presetLineId == null) return '—'
  const ln = lines.value.find(l => l.id === props.presetLineId)
  if (!ln) return `ID ${props.presetLineId}`
  return lineOptionLabel(ln)
})

/** プルダウン表示：工程名のみ（空のときは CD フォールバック） */
function processOptionLabel(p: ProcessItem): string {
  const nm = (p.process_name || '').trim()
  const cd = (p.process_cd || '').trim()
  return nm || cd || '—'
}

/** プルダウン表示：設備名のみ（空のときは ラインコード フォールバック） */
function lineOptionLabel(line: ProductionLine): string {
  const name = (line.line_name || '').trim()
  return name || (line.line_code || '').trim() || '—'
}

async function loadLinesByProcess() {
  const pc = (selectedProcessCd.value || '').trim()
  lines.value = await fetchLines(pc || undefined)
}

async function onProcessFilterChange() {
  const prevLineId = selectedLineId.value
  await loadLinesByProcess()
  if (selectedLineId.value != null && !lines.value.some(l => l.id === selectedLineId.value)) {
    selectedLineId.value = lines.value[0]?.id ?? null
  }
  const lid = selectedLineId.value
  const dr = dateRange.value
  /** 工程だけ変わり設備 ID が同一のままのときは watch が動かないため明示取得 */
  if (lid != null && dr?.[0] && dr?.[1] && lid === prevLineId) {
    void loadData()
  }
}

function applyThisMonthRange() {
  const d = dayjs()
  dateRange.value = [d.startOf('month').format('YYYY-MM-DD'), d.endOf('month').format('YYYY-MM-DD')]
}

/** 来月：現在の期間の開始月の翌月にずらす（未選択時は「今月」の翌月） */
function applyNextMonthRange() {
  const anchor = dateRange.value?.[0] ? dayjs(dateRange.value[0]) : dayjs()
  const d = anchor.add(1, 'month')
  dateRange.value = [d.startOf('month').format('YYYY-MM-DD'), d.endOf('month').format('YYYY-MM-DD')]
}

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
    slotsCollapsedByDate.value = Object.fromEntries(daySlots.value.map(d => [d.work_date, true]))
  } catch (e: any) {
    ElMessage.error(e?.message || '取得に失敗しました')
  } finally {
    loading.value = false
  }
}

/** 非 embed：設備・期間が揃ったら自動取得（取得ボタン廃止） */
watch(
  () =>
    [
      embed.value,
      selectedLineId.value,
      dateRange.value?.[0],
      dateRange.value?.[1],
    ] as const,
  ([em]) => {
    if (em) return
    const lid = selectedLineId.value
    const dr = dateRange.value
    if (lid == null || !dr?.[0] || !dr?.[1]) return
    void loadData()
  },
)

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
    const res = await fetchProcesses({ page: 1, pageSize: 5000 })
    const raw = (res?.data ?? res) as { list?: ProcessItem[] }
    const list = Array.isArray(raw.list) ? raw.list : []
    const filtered = list.filter((p) => LINE_CAPACITY_PROCESS_SET.has((p.process_cd || '').trim()))
    const rank = (cd: string) => {
      const i = LINE_CAPACITY_PROCESS_ORDER.indexOf(cd as (typeof LINE_CAPACITY_PROCESS_ORDER)[number])
      return i === -1 ? LINE_CAPACITY_PROCESS_ORDER.length : i
    }
    processOptions.value = [...filtered].sort(
      (a, b) => rank((a.process_cd || '').trim()) - rank((b.process_cd || '').trim()),
    )
    if (
      selectedProcessCd.value != null
      && !LINE_CAPACITY_PROCESS_SET.has(String(selectedProcessCd.value).trim())
    ) {
      selectedProcessCd.value = undefined
    }
  } catch {
    processOptions.value = []
  }
  try {
    await loadLinesByProcess()
  } catch {
    lines.value = []
  }
})

const STANDARD_SHIFT_SLOTS: EditSlot[] = [
  { start_time: '08:00:00', end_time: '12:00:00', is_rest: false },
  { start_time: '13:00:00', end_time: '17:00:00', is_rest: false },
  { start_time: '21:00:00', end_time: '00:00:00', is_rest: false },
  { start_time: '01:00:00', end_time: '06:00:00', is_rest: false },
]

/** 20H：昼直＋残業2h＋夜跨ぎ＋早番 */
const SHIFT_20H_WORK_SLOTS: EditSlot[] = [
  { start_time: '08:00:00', end_time: '12:00:00', is_rest: false },
  { start_time: '13:00:00', end_time: '17:00:00', is_rest: false },
  { start_time: '17:00:00', end_time: '19:00:00', is_rest: false },
  { start_time: '21:00:00', end_time: '00:00:00', is_rest: false },
  { start_time: '01:00:00', end_time: '08:00:00', is_rest: false },
]

/** 22H プリセット（昼帯 13:00–翌00:00、早番 01:00–08:00） */
const SHIFT_22H_WORK_SLOTS: EditSlot[] = [
  { start_time: '08:00:00', end_time: '12:00:00', is_rest: false },
  { start_time: '13:00:00', end_time: '00:00:00', is_rest: false },
  { start_time: '01:00:00', end_time: '08:00:00', is_rest: false },
]

/** 24H（カレンダー日あたり）：08:00〜翌08:00 を API 都合で夜跨ぎ2行に分割（全日稼働） */
const SHIFT_24H_DAY_WORK_SLOTS: EditSlot[] = [
  { start_time: '08:00:00', end_time: '00:00:00', is_rest: false },
  { start_time: '00:00:00', end_time: '08:00:00', is_rest: false },
]

/** 4H：午前帯のみ＋10分休憩 */
const SHIFT_4H_SLOTS: EditSlot[] = [
  { start_time: '08:00:00', end_time: '12:00:00', is_rest: false },
  { start_time: '10:00:00', end_time: '10:10:00', is_rest: true },
]

/** 8H：昼間2直＋各直10分休憩 */
const SHIFT_8H_SLOTS: EditSlot[] = [
  { start_time: '08:00:00', end_time: '12:00:00', is_rest: false },
  { start_time: '13:00:00', end_time: '17:00:00', is_rest: false },
  { start_time: '10:00:00', end_time: '10:10:00', is_rest: true },
  { start_time: '15:00:00', end_time: '15:10:00', is_rest: true },
]

/** 毎日固定の短い休憩（16H・20H・22H・24H のプリセットで使用） */
const FIXED_DAILY_BREAK_SLOTS: EditSlot[] = [
  { start_time: '10:00:00', end_time: '10:10:00', is_rest: true },
  { start_time: '15:00:00', end_time: '15:10:00', is_rest: true },
  { start_time: '01:00:00', end_time: '01:10:00', is_rest: true },
  { start_time: '04:00:00', end_time: '04:10:00', is_rest: true },
]

function applyStandardShift(day: DayEdit) {
  day.editSlots = [
    ...STANDARD_SHIFT_SLOTS.map(s => ({ ...s })),
    ...FIXED_DAILY_BREAK_SLOTS.map(s => ({ ...s })),
  ]
  collapseSlotsEditor(day)
}

function apply20HShift(day: DayEdit) {
  day.editSlots = [
    ...SHIFT_20H_WORK_SLOTS.map(s => ({ ...s })),
    ...FIXED_DAILY_BREAK_SLOTS.map(s => ({ ...s })),
  ]
  collapseSlotsEditor(day)
}

function apply22HShift(day: DayEdit) {
  day.editSlots = [
    ...SHIFT_22H_WORK_SLOTS.map(s => ({ ...s })),
    ...FIXED_DAILY_BREAK_SLOTS.map(s => ({ ...s })),
  ]
  collapseSlotsEditor(day)
}

function apply24HCalendarShift(day: DayEdit) {
  day.editSlots = [
    ...SHIFT_24H_DAY_WORK_SLOTS.map(s => ({ ...s })),
    ...FIXED_DAILY_BREAK_SLOTS.map(s => ({ ...s })),
  ]
  collapseSlotsEditor(day)
}

function apply4HShift(day: DayEdit) {
  day.editSlots = SHIFT_4H_SLOTS.map(s => ({ ...s }))
  collapseSlotsEditor(day)
}

function apply8HShift(day: DayEdit) {
  day.editSlots = SHIFT_8H_SLOTS.map(s => ({ ...s }))
  collapseSlotsEditor(day)
}

function removeSlot(day: DayEdit, idx: number) {
  day.editSlots.splice(idx, 1)
}

function clearAllSlots(day: DayEdit) {
  day.editSlots = []
  showSlotsEditor(day)
}

/** 一覧グリッドと同じ「表示中日」（土日フィルター込み）へプリセット一括適用 */
function batchApplyPreset(key: '4h' | '8h' | '16h' | '20h' | '22h' | '24h' | 'clear') {
  const days = displayDaySlots.value
  if (days.length === 0) {
    ElMessage.warning('表示中の日がありません')
    return
  }
  if (key === 'clear') {
    for (const day of days) {
      clearAllSlots(day)
    }
    ElMessage.success(`${days.length} 日の時間帯をクリアしました`)
    return
  }
  const runners: Record<'4h' | '8h' | '16h' | '20h' | '22h' | '24h', (d: DayEdit) => void> = {
    '4h': apply4HShift,
    '8h': apply8HShift,
    '16h': applyStandardShift,
    '20h': apply20HShift,
    '22h': apply22HShift,
    '24h': apply24HCalendarShift,
  }
  const run = runners[key]
  for (const day of days) {
    run(day)
  }
  ElMessage.success(`${days.length} 日に適用しました（保存で反映）`)
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

.card-head--with-actions {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.card-head__main {
  flex: 1;
  min-width: 0;
}

.card-head__actions {
  flex-shrink: 0;
  padding-top: 1px;
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

.toolbar.toolbar--filter-bar {
  margin: 0 0 14px;
  padding: 12px 14px 14px;
  border-radius: 10px;
  border: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-blank);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  gap: 10px 14px;
  align-items: flex-end;
}

.bulk-apply-panel {
  margin: 0 0 14px;
  padding: 10px 14px 12px;
  border-radius: 10px;
  border: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-light);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.bulk-apply-panel__head {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 8px 12px;
  margin-bottom: 8px;
}

.bulk-apply-panel__title {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.bulk-apply-panel__hint {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  line-height: 1.4;
}

.bulk-apply-panel__hint strong {
  font-variant-numeric: tabular-nums;
  color: var(--el-color-primary);
}

.bulk-apply-panel__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 8px;
  align-items: center;
}

.bulk-apply-panel__actions :deep(.el-button) {
  padding: 5px 10px;
  margin: 0;
  font-size: 11px;
}

.toolbar :deep(.el-form-item) {
  margin-bottom: 0;
  margin-right: 10px;
}

.toolbar :deep(.el-form-item__label) {
  padding-right: 6px;
  font-size: 12px;
  font-weight: 500;
  color: var(--el-text-color-regular);
}

.toolbar__select {
  width: 90px;
}

.toolbar__item--range :deep(.el-form-item__content) {
  width: auto;
  max-width: none;
}

.toolbar__range-block {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.toolbar__quick-months {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.toolbar__quick-month-btn {
  padding: 5px 11px;
  font-weight: 500;
  border-radius: 6px;
}

.toolbar__daterange {
  width: 210px;
  max-width: 210px;
  --el-date-editor-width: 210px;
  box-sizing: border-box;
}

.toolbar__daterange :deep(.el-date-editor),
.toolbar__daterange :deep(.el-date-editor.el-input__wrapper) {
  width: 210px !important;
  max-width: 210px;
  box-sizing: border-box;
}

/* 22H：琥珀（20H の警告橙と差別化）／24H：プライマリ青（4H の info と差別化） */
.lcap-preset--22h.el-button.is-plain {
  --el-button-bg-color: transparent;
  --el-button-border-color: #d97706;
  --el-button-text-color: #d97706;
  --el-button-hover-bg-color: rgba(217, 119, 6, 0.12);
  --el-button-hover-border-color: #b45309;
  --el-button-hover-text-color: #b45309;
}

.lcap-preset--24h.el-button.is-plain {
  --el-button-bg-color: transparent;
  --el-button-border-color: var(--el-color-primary);
  --el-button-text-color: var(--el-color-primary);
  --el-button-hover-bg-color: var(--el-color-primary-light-9);
  --el-button-hover-border-color: var(--el-color-primary-dark-2);
  --el-button-hover-text-color: var(--el-color-primary-dark-2);
}

.toolbar__week-toggles {
  display: inline-flex;
  align-items: center;
  gap: 10px 14px;
  flex-wrap: wrap;
}

.toolbar__week-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.toolbar__week-toggle-label {
  font-size: 12px;
  color: var(--el-text-color-regular);
  white-space: nowrap;
}

/* 日別カード領域：高さ固定＋縦スクロール（カード本体は内側で伸長） */
.calendar-grid-scroll {
  max-height: min(62vh, 720px);
  min-height: 140px;
  overflow-x: hidden;
  overflow-y: auto;
  box-sizing: border-box;
  width: 100%;
  scrollbar-gutter: stable;
}

.capacity-page--embed .calendar-grid-scroll {
  max-height: min(52vh, 560px);
}

/* デフォルト4列（狭い画面では段組みを減らす） */
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  align-items: stretch;
  min-height: 80px;
  width: 100%;
  max-width: min(1400px, 100%);
  margin: 0 auto;
  box-sizing: border-box;
}

@media (max-width: 1100px) {
  .calendar-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 520px) {
  .calendar-grid {
    grid-template-columns: 1fr;
  }
}

.capacity-page--embed .calendar-grid {
  max-width: none;
  margin: 0;
  width: 100%;
  /* 嵌入对话框内は日カードを窗体幅いっぱいに（4列だと極細になるため） */
  grid-template-columns: minmax(0, 1fr);
}

.capacity-page--embed .day-card {
  border-radius: 8px;
  border-color: var(--el-border-color-light);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.capacity-page--embed .day-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
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

.day-card--weekend .day-card__date,
.day-card--weekend .day-card__wd {
  color: var(--el-color-danger);
}

.day-card--slots-collapsed .day-card__top {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
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

.day-card__expand-slots {
  padding: 0 4px;
  font-size: 12px;
}

.day-card__tag {
  margin-left: auto;
  font-variant-numeric: tabular-nums;
  font-size: 12px;
  font-weight: 700;
  color: #000000;
}

.day-card__tag--zero {
  color: #ececec;
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
