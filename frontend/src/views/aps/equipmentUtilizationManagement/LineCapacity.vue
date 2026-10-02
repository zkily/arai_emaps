<template>
  <div class="capacity-page" :class="{ 'capacity-page--embed': embed, 'lc-modern': !embed }">
    <el-card
      :shadow="embed ? 'never' : 'hover'"
      class="capacity-card"
      :body-style="{ padding: embed ? '6px 8px' : '8px 10px' }"
    >
      <template #header>
        <div v-if="embed" class="card-head card-head--embed card-head--with-actions">
          <div class="card-head__main">
            <h3 class="card-head__title">
              <span class="card-head__title-inner">
                <el-icon class="card-head__title-icon"><Setting /></el-icon>
                設備稼働設定
              </span>
            </h3>
            <p class="card-head__desc card-head__desc--embed">
              表示中ライン・ガント期間の時間帯を編集します（保存で反映）。技術使用・保全は通常生産不可として指示画面にも表示されます。
            </p>
          </div>
          <div v-if="daySlots.length > 0" class="card-head__actions">
            <el-button
              type="success"
              size="small"
              class="lcap-btn-save"
              :icon="CircleCheck"
              :loading="saving"
              :disabled="!canEdit"
              @click="saveAll"
            >
              一括保存
            </el-button>
          </div>
        </div>
        <div v-else class="card-head card-head--with-actions">
          <div class="card-head__fx" aria-hidden="true">
            <span class="fx-orb orb-a" />
            <span class="fx-orb orb-b" />
            <span class="fx-grid" />
            <span class="fx-sheen" />
          </div>
          <div class="card-head__main">
            <h3 class="card-head__title">
              <span class="card-head__title-inner">
                <el-icon class="card-head__title-icon"><Setting /></el-icon>
                設備稼働設定
              </span>
            </h3>
            <p class="card-head__desc">
              日別の稼働時間帯を設定します。「休憩・技術使用・保全」は稼働合計・排産から除外（稼働帯との重複分のみ差引）。技術使用・保全は成型指示にも表示されます。
            </p>
            <div class="card-head__chips">
              <span v-if="selectedLineLabel" class="card-head__chip">
                <el-icon><Monitor /></el-icon>
                {{ selectedLineLabel }}
              </span>
              <span v-if="dateRange?.[0]" class="card-head__chip">
                <el-icon><Calendar /></el-icon>
                {{ dateRange[0] }} 〜 {{ dateRange[1] }}
              </span>
              <span v-if="daySlots.length > 0" class="card-head__chip">
                <el-icon><Clock /></el-icon>
                表示 {{ displayDaySlots.length }} 日
              </span>
              <span v-if="daySlots.length > 0" class="card-head__chip card-head__chip--strong">
                <el-icon><Timer /></el-icon>
                稼働合計 {{ totalProductiveHours.toFixed(1) }}h
              </span>
            </div>
          </div>
          <div v-if="daySlots.length > 0" class="card-head__actions">
            <el-button
              type="success"
              size="small"
              class="lcap-btn-save"
              :icon="CircleCheck"
              :loading="saving"
              :disabled="!canEdit"
              @click="saveAll"
            >
              一括保存
            </el-button>
          </div>
        </div>
      </template>

      <template v-if="!embed">
      <el-form class="toolbar toolbar--filter-bar" :inline="true" label-position="left" size="small">
        <el-form-item class="toolbar__item">
          <template #label>
            <span class="toolbar__lbl"><el-icon><Operation /></el-icon>工程</span>
          </template>
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
        <el-form-item class="toolbar__item">
          <template #label>
            <span class="toolbar__lbl"><el-icon><Monitor /></el-icon>設備</span>
          </template>
          <el-select v-model="selectedLineId" placeholder="選択" class="toolbar__select">
            <el-option
              v-for="line in lines"
              :key="line.id"
              :value="line.id"
              :label="lineOptionLabel(line)"
            />
          </el-select>
        </el-form-item>
        <el-form-item class="toolbar__item toolbar__item--range">
          <template #label>
            <span class="toolbar__lbl"><el-icon><Calendar /></el-icon>期間</span>
          </template>
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
              <el-button
                type="primary"
                plain
                class="toolbar__quick-month-btn lcap-btn-month-this"
                size="small"
                :icon="Calendar"
                @click="applyThisMonthRange"
              >
                今月
              </el-button>
              <el-button
                type="success"
                plain
                class="toolbar__quick-month-btn lcap-btn-month-next"
                size="small"
                :icon="Calendar"
                @click="applyNextMonthRange"
              >
                次月
              </el-button>
            </div>
          </div>
        </el-form-item>
        <el-form-item class="toolbar__item toolbar__item--week">
          <template #label>
            <span class="toolbar__lbl"><el-icon><Sunny /></el-icon>土日表示</span>
          </template>
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
          <span class="bulk-apply-panel__title">
            <el-icon class="bulk-apply-panel__title-icon"><Clock /></el-icon>
            一括時間帯
          </span>
          <span class="bulk-apply-panel__hint">
            表示中 <strong>{{ displayDaySlots.length }}</strong> 日に同一プリセットを適用（反映には「一括保存」）
          </span>
        </div>
        <div class="bulk-apply-panel__actions">
          <el-button
            v-for="preset in shiftPresetButtons"
            :key="preset.key"
            :type="preset.btnType || undefined"
            size="small"
            plain
            :class="preset.btnClass"
            :title="preset.title"
            @click="batchApplyPreset(preset.key)"
          >
            {{ preset.label }}
          </el-button>
          <el-button
            type="danger"
            size="small"
            plain
            class="lcap-btn-bulk-clear"
            :icon="Delete"
            @click="batchApplyPreset('clear')"
          >
            全日削除
          </el-button>
        </div>
      </div>
      </template>
      <div v-else class="toolbar toolbar--embed">
        <span class="toolbar-embed__line">
          <el-icon class="toolbar-embed__ico"><Monitor /></el-icon>
          {{ embedLineLabel }}
        </span>
        <span class="toolbar-embed__range">
          <el-icon class="toolbar-embed__ico toolbar-embed__ico--muted"><Calendar /></el-icon>
          {{ presetDateRange?.[0] }} 〜 {{ presetDateRange?.[1] }}
        </span>
        <el-button type="primary" size="small" class="lcap-btn-refresh" :icon="Refresh" :loading="loading" @click="loadData">
          再取得
        </el-button>
      </div>

      <div v-loading="loading" class="calendar-grid-scroll">
        <div class="calendar-grid">
          <div v-if="daySlots.length === 0 && !loading" class="empty">
            <el-icon class="empty__icon"><Calendar /></el-icon>
            <p class="empty__text">
              {{ embed ? '設備と期間を選んで「再取得」してください' : '設備と期間を選択すると自動で読み込みます' }}
            </p>
          </div>
          <div
            v-else-if="displayDaySlots.length === 0 && !loading && daySlots.length > 0"
            class="empty empty--hint"
          >
            <el-icon class="empty__icon"><Sunny /></el-icon>
            <p class="empty__text">
              この条件では表示する日がありません（土曜・日曜の表示をオンにするか、期間を変更してください）
            </p>
          </div>
          <div
            v-for="day in displayDaySlots"
            :key="day.work_date"
            class="day-card"
            :class="[
              `day-card--h-${dayHoursTone(day)}`,
              {
                'day-card--weekend': isWeekend(day.work_date),
                'day-card--slots-collapsed': slotsCollapsedByDate[day.work_date],
              },
            ]"
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
              >
                <el-icon class="day-card__tag-icon"><Timer /></el-icon>
                {{ calcProductiveHours(day).toFixed(1) }}h
              </span>
              <span
                v-if="dayOccupancyBadge(day)"
                class="day-card__occ"
                :class="`day-card__occ--${dayOccupancyBadge(day)}`"
                :title="dayOccupancyTitle(day)"
              >
                {{ dayOccupancyBadge(day) === 'tech' ? '技術' : dayOccupancyBadge(day) === 'maintenance' ? '保全' : '占用' }}
              </span>
            </div>
            <div class="day-card__actions">
              <el-button
                v-for="preset in shiftPresetButtons"
                :key="preset.key"
                :type="preset.btnType || undefined"
                size="small"
                plain
                :class="preset.btnClass"
                :title="preset.title"
                @click="applyShiftPreset(day, preset.key)"
              >
                {{ preset.label }}
              </el-button>
              <el-button
                type="danger"
                size="small"
                plain
                class="lcap-btn-day-clear"
                :disabled="day.editSlots.length === 0"
                :icon="Delete"
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
              :class="slotRowClass(slot)"
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
                <el-select
                  v-model="slot.slot_type"
                  size="small"
                  class="slot-row__type"
                  @change="onSlotTypeChange(slot)"
                >
                  <el-option
                    v-for="opt in SLOT_TYPE_OPTIONS"
                    :key="opt.value"
                    :label="opt.label"
                    :value="opt.value"
                  />
                </el-select>
                <el-input
                  v-if="slot.slot_type === 'tech' || slot.slot_type === 'maintenance'"
                  v-model="slot.note"
                  size="small"
                  maxlength="255"
                  clearable
                  placeholder="用途メモ"
                  class="slot-row__note"
                />
                <el-button type="danger" size="small" link class="slot-row__del" @click="removeSlot(day, idx)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
            <div class="slots-list__add">
              <el-button size="small" plain type="primary" @click="addSlot(day, 'work')">稼働帯を追加</el-button>
              <el-button size="small" plain @click="addSlot(day, 'rest')">休憩を追加</el-button>
              <el-button size="small" plain type="warning" @click="addSlot(day, 'tech')">技術使用を追加</el-button>
              <el-button size="small" plain type="info" @click="addSlot(day, 'maintenance')">保全を追加</el-button>
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
import {
  Delete,
  Setting,
  Operation,
  Monitor,
  Calendar,
  Sunny,
  Clock,
  CircleCheck,
  Refresh,
  Timer,
} from '@element-plus/icons-vue'
import {
  fetchLines,
  fetchLineCapacitySlots,
  batchUpsertLineCapacitySlots,
  type ProductionLine,
  type DaySlotsOut,
  type LineCapacitySlotType,
} from '@/api/aps'
import { fetchProcesses } from '@/api/master/processMaster'
import type { ProcessItem } from '@/types/master'
import { useApsOperationPermission } from '@/composables/useApsOperationPermission'
import { guardApsOperation } from '@/utils/apsOperationGuard'

const { canEdit } = useApsOperationPermission()

const SLOT_TYPE_OPTIONS: { value: LineCapacitySlotType; label: string }[] = [
  { value: 'work', label: '稼働' },
  { value: 'rest', label: '休憩' },
  { value: 'tech', label: '技術使用' },
  { value: 'maintenance', label: '保全' },
]

function normalizeSlotType(raw?: string | null, isRest?: boolean): LineCapacitySlotType {
  const st = (raw || '').trim().toLowerCase()
  if (st === 'rest' || st === 'tech' || st === 'maintenance') return st
  if (isRest) return 'rest'
  return 'work'
}

function isNonProductiveSlotType(slotType: LineCapacitySlotType): boolean {
  return slotType === 'rest' || slotType === 'tech' || slotType === 'maintenance'
}

interface EditSlot {
  start_time: string
  end_time: string
  is_rest?: boolean
  slot_type: LineCapacitySlotType
  note?: string
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
    /** embed 時の工程 CD（溶接 KT07 / 成型 KT04 等。ショートカット切替用） */
    presetProcessCd?: string | null
  }>(),
  {
    embed: false,
    presetLineId: null,
    presetDateRange: null,
    presetProcessCd: null,
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
const WELDING_PROCESS_CD = 'KT07'

type ShiftPresetKey = '2h' | '8h' | '9h' | '10h' | '12h' | '14h' | '16h' | '20h' | '22h' | '24h'

interface ShiftPresetButton {
  key: ShiftPresetKey
  label: string
  btnType: '' | 'info' | 'success' | 'primary' | 'warning'
  btnClass?: string
  title: string
}

/** 22H：成型・溶接（溶接SP 含む）共通（昼 08:00–21:00、夜 21:00–08:00） */
const SHIFT_PRESET_22H_BUTTON: ShiftPresetButton = {
  key: '22h',
  label: '22H',
  btnType: '',
  btnClass: 'lcap-preset--22h',
  title:
    '稼働 08:00–21:00 / 21:00–08:00、休憩 10:00–10:10 / 15:00–15:10 / 12:00–13:00 / 23:00–23:10 / 01:00–02:00 / 04:00–04:10 / 17:00–17:10 / 06:00–06:10 / 19:00–19:10（金曜は 16:30–17:00 も休憩）',
}

const FORMING_SHIFT_PRESET_BUTTONS: ShiftPresetButton[] = [
  {
    key: '2h',
    label: '2H',
    btnType: 'info',
    title: '稼働 15:10–17:00（金曜は 16:30–17:00 も休憩）',
  },
  {
    key: '8h',
    label: '8H',
    btnType: 'success',
    title: '稼働 08:00–17:00、休憩 10:00–10:10 / 15:00–15:10 / 12:00–13:10（金曜は 16:30–17:00 も休憩）',
  },
  {
    key: '14h',
    label: '14H',
    btnType: 'primary',
    title:
      '稼働 08:00–12:00 / 15:00–17:00 / 21:00–06:00、休憩 10:00–10:10 / 15:00–15:10 / 23:00–23:10 / 01:00–02:00 / 04:00–04:10（金曜は 16:30–17:00 も休憩）',
  },
  {
    key: '16h',
    label: '16H',
    btnType: 'primary',
    title:
      '稼働 08:00–17:00 / 21:00–06:00、休憩 10:00–10:10 / 15:00–15:10 / 12:00–13:00 / 23:00–23:10 / 01:00–02:00 / 04:00–04:10（金曜は 16:30–17:00 も休憩）',
  },
  {
    key: '20h',
    label: '20H',
    btnType: 'warning',
    title:
      '稼働 08:00–19:00 / 21:00–08:00、休憩 10:00–10:10 / 15:00–15:10 / 12:00–13:00 / 23:00–23:10 / 01:00–02:00 / 04:00–04:10 / 17:00–17:10 / 06:00–06:10（金曜は 16:30–17:00 も休憩）',
  },
  SHIFT_PRESET_22H_BUTTON,
  {
    key: '24h',
    label: '24H',
    btnType: '',
    btnClass: 'lcap-preset--24h',
    title:
      '稼働 08:00–21:00 / 21:00–08:00、休憩 10:00–10:10 / 15:00–15:10 / 23:00–23:10 / 04:00–04:10 / 17:00–17:10 / 06:00–06:10 / 19:00–19:10（金曜は 16:30–17:00 も休憩）',
  },
]

const WELDING_SHIFT_PRESET_BUTTONS: ShiftPresetButton[] = [
  {
    key: '8h',
    label: '8H',
    btnType: 'success',
    title: '稼働 08:00–17:00、休憩 10:00–10:10 / 15:00–15:10 / 12:00–13:10（金曜は 16:30–17:00 も休憩）',
  },
  {
    key: '9h',
    label: '9H',
    btnType: 'success',
    title: '稼働 08:00–12:00 / 13:00–18:00、休憩 10:00–10:10 / 15:00–15:10 / 17:00–17:10',
  },
  {
    key: '10h',
    label: '10H',
    btnType: 'primary',
    title: '稼働 08:00–12:00 / 13:00–19:00、休憩 10:00–10:10 / 15:00–15:10 / 17:00–17:10',
  },
  {
    key: '12h',
    label: '12H',
    btnType: 'primary',
    title: '稼働 08:00–12:00 / 13:00–21:00、休憩 10:00–10:10 / 15:00–15:10 / 17:00–17:10',
  },
  {
    key: '16h',
    label: '16H',
    btnType: 'primary',
    title:
      '稼働 08:00–17:00 / 21:00–06:00、休憩 10:00–10:10 / 15:00–15:10 / 12:00–13:00 / 23:00–23:10 / 01:00–02:00 / 04:00–04:10（金曜は 16:30–17:00 も休憩）',
  },
  {
    key: '20h',
    label: '20H',
    btnType: 'warning',
    title:
      '稼働 08:00–19:00 / 21:00–08:00、休憩 10:00–10:10 / 15:00–15:10 / 12:00–13:00 / 23:00–23:10 / 01:00–02:00 / 04:00–04:10 / 17:00–17:10 / 06:00–06:10（金曜は 16:30–17:00 も休憩）',
  },
  SHIFT_PRESET_22H_BUTTON,
]

const processOptions = ref<ProcessItem[]>([])
/** 空＝全工程（fetchLines は processCd 無し） */
const selectedProcessCd = ref<string | undefined>(undefined)

const effectiveProcessCd = computed(() => {
  const preset = (props.presetProcessCd || '').trim()
  if (preset) return preset
  return (selectedProcessCd.value || '').trim()
})

const isWeldingProcess = computed(() => effectiveProcessCd.value === WELDING_PROCESS_CD)

const shiftPresetButtons = computed(() =>
  isWeldingProcess.value ? WELDING_SHIFT_PRESET_BUTTONS : FORMING_SHIFT_PRESET_BUTTONS,
)

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

/** ヘッダーチップ用：選択中設備名 */
const selectedLineLabel = computed(() => {
  const ln = lines.value.find((l) => l.id === selectedLineId.value)
  return ln ? lineOptionLabel(ln) : ''
})

/** ヘッダーチップ用：表示中日の稼働合計（h） */
const totalProductiveHours = computed(() =>
  displayDaySlots.value.reduce((acc, day) => acc + calcProductiveHours(day), 0),
)

/** 日カードの色分け（稼働時間帯の長さ） */
function dayHoursTone(day: DayEdit): 'zero' | 'short' | 'mid' | 'long' | 'full' {
  const h = calcProductiveHours(day)
  if (h <= 0) return 'zero'
  if (h <= 8.5) return 'short'
  if (h <= 17) return 'mid'
  if (h <= 22) return 'long'
  return 'full'
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
        ? d.slots.map(s => {
          const slot_type = normalizeSlotType(s.slot_type, Boolean(s.is_rest))
          return {
            start_time: s.start_time,
            end_time: s.end_time,
            is_rest: isNonProductiveSlotType(slot_type),
            slot_type,
            note: (s.note || '').toString(),
          }
        })
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

/** 16H：昼 08:00–17:00、夜 21:00–06:00（夜帯は 1 行。終了 < 開始は当日深夜〜翌朝） */
const SHIFT_16H_SLOTS: EditSlot[] = [
  { start_time: '08:00:00', end_time: '17:00:00', is_rest: false, slot_type: 'work' },
  { start_time: '21:00:00', end_time: '06:00:00', is_rest: false, slot_type: 'work' },
  { start_time: '10:00:00', end_time: '10:10:00', is_rest: true, slot_type: 'rest' },
  { start_time: '15:00:00', end_time: '15:10:00', is_rest: true, slot_type: 'rest' },
  { start_time: '12:00:00', end_time: '13:00:00', is_rest: true, slot_type: 'rest' },
  { start_time: '23:00:00', end_time: '23:10:00', is_rest: true, slot_type: 'rest' },
  { start_time: '01:00:00', end_time: '02:00:00', is_rest: true, slot_type: 'rest' },
  { start_time: '04:00:00', end_time: '04:10:00', is_rest: true, slot_type: 'rest' },
]

/** 20H：昼 08:00–19:00、夜 21:00–08:00 */
const SHIFT_20H_SLOTS: EditSlot[] = [
  { start_time: '08:00:00', end_time: '19:00:00', is_rest: false, slot_type: 'work' },
  { start_time: '21:00:00', end_time: '08:00:00', is_rest: false, slot_type: 'work' },
  { start_time: '10:00:00', end_time: '10:10:00', is_rest: true, slot_type: 'rest' },
  { start_time: '15:00:00', end_time: '15:10:00', is_rest: true, slot_type: 'rest' },
  { start_time: '12:00:00', end_time: '13:00:00', is_rest: true, slot_type: 'rest' },
  { start_time: '23:00:00', end_time: '23:10:00', is_rest: true, slot_type: 'rest' },
  { start_time: '01:00:00', end_time: '02:00:00', is_rest: true, slot_type: 'rest' },
  { start_time: '04:00:00', end_time: '04:10:00', is_rest: true, slot_type: 'rest' },
  { start_time: '17:00:00', end_time: '17:10:00', is_rest: true, slot_type: 'rest' },
  { start_time: '06:00:00', end_time: '06:10:00', is_rest: true, slot_type: 'rest' },
]

/** 22H：昼 08:00–21:00、夜 21:00–08:00 */
const SHIFT_22H_SLOTS: EditSlot[] = [
  { start_time: '08:00:00', end_time: '21:00:00', is_rest: false, slot_type: 'work' },
  { start_time: '21:00:00', end_time: '08:00:00', is_rest: false, slot_type: 'work' },
  { start_time: '10:00:00', end_time: '10:10:00', is_rest: true, slot_type: 'rest' },
  { start_time: '15:00:00', end_time: '15:10:00', is_rest: true, slot_type: 'rest' },
  { start_time: '12:00:00', end_time: '13:00:00', is_rest: true, slot_type: 'rest' },
  { start_time: '23:00:00', end_time: '23:10:00', is_rest: true, slot_type: 'rest' },
  { start_time: '01:00:00', end_time: '02:00:00', is_rest: true, slot_type: 'rest' },
  { start_time: '04:00:00', end_time: '04:10:00', is_rest: true, slot_type: 'rest' },
  { start_time: '17:00:00', end_time: '17:10:00', is_rest: true, slot_type: 'rest' },
  { start_time: '06:00:00', end_time: '06:10:00', is_rest: true, slot_type: 'rest' },
  { start_time: '19:00:00', end_time: '19:10:00', is_rest: true, slot_type: 'rest' },
]

/** 24H：08:00〜翌08:00（昼 08:00–21:00、夜 21:00–08:00）。昼休憩・深夜食事なし */
const SHIFT_24H_SLOTS: EditSlot[] = [
  { start_time: '08:00:00', end_time: '21:00:00', is_rest: false, slot_type: 'work' },
  { start_time: '21:00:00', end_time: '08:00:00', is_rest: false, slot_type: 'work' },
  { start_time: '10:00:00', end_time: '10:10:00', is_rest: true, slot_type: 'rest' },
  { start_time: '15:00:00', end_time: '15:10:00', is_rest: true, slot_type: 'rest' },
  { start_time: '23:00:00', end_time: '23:10:00', is_rest: true, slot_type: 'rest' },
  { start_time: '04:00:00', end_time: '04:10:00', is_rest: true, slot_type: 'rest' },
  { start_time: '17:00:00', end_time: '17:10:00', is_rest: true, slot_type: 'rest' },
  { start_time: '06:00:00', end_time: '06:10:00', is_rest: true, slot_type: 'rest' },
  { start_time: '19:00:00', end_time: '19:10:00', is_rest: true, slot_type: 'rest' },
]

/** 2H：午後短時間 */
const SHIFT_2H_SLOTS: EditSlot[] = [
  { start_time: '15:10:00', end_time: '17:00:00', is_rest: false, slot_type: 'work' },
]

/** 14H：午前・午後・夜。午後開始と同時に 15:00–15:10 休憩 */
const SHIFT_14H_SLOTS: EditSlot[] = [
  { start_time: '08:00:00', end_time: '12:00:00', is_rest: false, slot_type: 'work' },
  { start_time: '15:00:00', end_time: '17:00:00', is_rest: false, slot_type: 'work' },
  { start_time: '21:00:00', end_time: '06:00:00', is_rest: false, slot_type: 'work' },
  { start_time: '10:00:00', end_time: '10:10:00', is_rest: true, slot_type: 'rest' },
  { start_time: '15:00:00', end_time: '15:10:00', is_rest: true, slot_type: 'rest' },
  { start_time: '23:00:00', end_time: '23:10:00', is_rest: true, slot_type: 'rest' },
  { start_time: '01:00:00', end_time: '02:00:00', is_rest: true, slot_type: 'rest' },
  { start_time: '04:00:00', end_time: '04:10:00', is_rest: true, slot_type: 'rest' },
]

/** 8H：08:00–17:00。昼休憩は 12:00–13:10 */
const SHIFT_8H_SLOTS: EditSlot[] = [
  { start_time: '08:00:00', end_time: '17:00:00', is_rest: false, slot_type: 'work' },
  { start_time: '10:00:00', end_time: '10:10:00', is_rest: true, slot_type: 'rest' },
  { start_time: '15:00:00', end_time: '15:10:00', is_rest: true, slot_type: 'rest' },
  { start_time: '12:00:00', end_time: '13:10:00', is_rest: true, slot_type: 'rest' },
]

/** 金曜のみ追加する休憩（2H / 8H / 14H / 16H / 20H / 22H / 24H） */
const FRIDAY_BREAK_SLOT: EditSlot = {
  start_time: '16:30:00',
  end_time: '17:00:00',
  is_rest: true,
  slot_type: 'rest',
}

/** 溶接 9H/10H/12H の短い休憩 */
const WELDING_DAY_BREAK_SLOTS: EditSlot[] = [
  { start_time: '10:00:00', end_time: '10:10:00', is_rest: true, slot_type: 'rest' },
  { start_time: '15:00:00', end_time: '15:10:00', is_rest: true, slot_type: 'rest' },
]

/** 溶接 9H/10H/12H の休憩（上記 + 17:00） */
const WELDING_EXTENDED_BREAK_SLOTS: EditSlot[] = [
  ...WELDING_DAY_BREAK_SLOTS,
  { start_time: '17:00:00', end_time: '17:10:00', is_rest: true, slot_type: 'rest' },
]

/** 溶接 9H：午後1時間延長 */
const SHIFT_9H_WELDING_WORK_SLOTS: EditSlot[] = [
  { start_time: '08:00:00', end_time: '12:00:00', is_rest: false, slot_type: 'work' },
  { start_time: '13:00:00', end_time: '18:00:00', is_rest: false, slot_type: 'work' },
]

/** 溶接 10H */
const SHIFT_10H_WELDING_WORK_SLOTS: EditSlot[] = [
  { start_time: '08:00:00', end_time: '12:00:00', is_rest: false, slot_type: 'work' },
  { start_time: '13:00:00', end_time: '19:00:00', is_rest: false, slot_type: 'work' },
]

/** 溶接 12H */
const SHIFT_12H_WELDING_WORK_SLOTS: EditSlot[] = [
  { start_time: '08:00:00', end_time: '12:00:00', is_rest: false, slot_type: 'work' },
  { start_time: '13:00:00', end_time: '21:00:00', is_rest: false, slot_type: 'work' },
]

function isFridayWorkDate(workDate: string): boolean {
  return new Date(workDate).getDay() === 5
}

/** プリセット適用。withFridayBreak のとき金曜だけ 16:30–17:00 を休憩に足す */
function applyPresetSlots(day: DayEdit, slots: readonly EditSlot[], withFridayBreak = false) {
  const next = slots.map(s => ({ ...s }))
  if (withFridayBreak && isFridayWorkDate(day.work_date)) {
    next.push({ ...FRIDAY_BREAK_SLOT })
  }
  day.editSlots = next
  collapseSlotsEditor(day)
}

function apply16HShift(day: DayEdit) {
  applyPresetSlots(day, SHIFT_16H_SLOTS, true)
}

function apply20HShift(day: DayEdit) {
  applyPresetSlots(day, SHIFT_20H_SLOTS, true)
}

function apply22HShift(day: DayEdit) {
  applyPresetSlots(day, SHIFT_22H_SLOTS, true)
}

function apply24HCalendarShift(day: DayEdit) {
  applyPresetSlots(day, SHIFT_24H_SLOTS, true)
}

function apply2HShift(day: DayEdit) {
  applyPresetSlots(day, SHIFT_2H_SLOTS, true)
}

function apply14HShift(day: DayEdit) {
  applyPresetSlots(day, SHIFT_14H_SLOTS, true)
}

function apply8HShift(day: DayEdit) {
  applyPresetSlots(day, SHIFT_8H_SLOTS, true)
}

function applyWeldingDayShift(day: DayEdit, workSlots: EditSlot[], breakSlots: EditSlot[]) {
  day.editSlots = [
    ...workSlots.map(s => ({ ...s })),
    ...breakSlots.map(s => ({ ...s })),
  ]
  collapseSlotsEditor(day)
}

function apply9HShift(day: DayEdit) {
  applyWeldingDayShift(day, SHIFT_9H_WELDING_WORK_SLOTS, WELDING_EXTENDED_BREAK_SLOTS)
}

function apply10HShift(day: DayEdit) {
  applyWeldingDayShift(day, SHIFT_10H_WELDING_WORK_SLOTS, WELDING_EXTENDED_BREAK_SLOTS)
}

function apply12HShift(day: DayEdit) {
  applyWeldingDayShift(day, SHIFT_12H_WELDING_WORK_SLOTS, WELDING_EXTENDED_BREAK_SLOTS)
}

const SHIFT_PRESET_RUNNERS: Record<ShiftPresetKey, (d: DayEdit) => void> = {
  '2h': apply2HShift,
  '8h': apply8HShift,
  '9h': apply9HShift,
  '10h': apply10HShift,
  '12h': apply12HShift,
  '14h': apply14HShift,
  '16h': apply16HShift,
  '20h': apply20HShift,
  '22h': apply22HShift,
  '24h': apply24HCalendarShift,
}

function applyShiftPreset(day: DayEdit, key: ShiftPresetKey) {
  SHIFT_PRESET_RUNNERS[key](day)
}

function removeSlot(day: DayEdit, idx: number) {
  day.editSlots.splice(idx, 1)
}

function addSlot(day: DayEdit, slotType: LineCapacitySlotType = 'work') {
  day.editSlots.push({
    start_time: '08:00:00',
    end_time: '09:00:00',
    slot_type: slotType,
    is_rest: isNonProductiveSlotType(slotType),
    note: '',
  })
  showSlotsEditor(day)
}

function onSlotTypeChange(slot: EditSlot) {
  slot.slot_type = normalizeSlotType(slot.slot_type, Boolean(slot.is_rest))
  slot.is_rest = isNonProductiveSlotType(slot.slot_type)
  if (slot.slot_type === 'work' || slot.slot_type === 'rest') {
    slot.note = ''
  }
}

function slotRowClass(slot: EditSlot): Record<string, boolean> {
  const st = normalizeSlotType(slot.slot_type, Boolean(slot.is_rest))
  return {
    'slot-row--rest': st === 'rest',
    'slot-row--tech': st === 'tech',
    'slot-row--maintenance': st === 'maintenance',
  }
}

function dayOccupancyBadge(day: DayEdit): 'tech' | 'maintenance' | 'mixed' | '' {
  let hasTech = false
  let hasMaint = false
  for (const slot of day.editSlots || []) {
    const st = normalizeSlotType(slot.slot_type, Boolean(slot.is_rest))
    if (st === 'tech') hasTech = true
    if (st === 'maintenance') hasMaint = true
  }
  if (hasTech && hasMaint) return 'mixed'
  if (hasTech) return 'tech'
  if (hasMaint) return 'maintenance'
  return ''
}

function dayOccupancyTitle(day: DayEdit): string {
  const parts: string[] = []
  for (const slot of day.editSlots || []) {
    const st = normalizeSlotType(slot.slot_type, Boolean(slot.is_rest))
    if (st !== 'tech' && st !== 'maintenance') continue
    const label = st === 'tech' ? '技術使用' : '保全'
    const note = (slot.note || '').trim()
    const range = `${(slot.start_time || '').slice(0, 5)}–${(slot.end_time || '').slice(0, 5)}`
    parts.push(note ? `${label} ${range} ${note}` : `${label} ${range}`)
  }
  return parts.join(' / ')
}

function clearAllSlots(day: DayEdit) {
  day.editSlots = []
  showSlotsEditor(day)
}

/** 一覧グリッドと同じ「表示中日」（土日フィルター込み）へプリセット一括適用 */
function batchApplyPreset(key: ShiftPresetKey | 'clear') {
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
  const run = SHIFT_PRESET_RUNNERS[key]
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

/** 非稼働（休憩・技術使用・保全）帯を差し引いた実稼働時間（h）— バックエンド engine と同趣旨 */
function calcProductiveHours(day: DayEdit): number {
  const workRaw: [number, number][] = []
  const restRaw: [number, number][] = []
  for (const slot of day.editSlots) {
    if (!slot.start_time || !slot.end_time) continue
    const parts = expandSlotToMinuteParts(slot.start_time, slot.end_time)
    const st = normalizeSlotType(slot.slot_type, Boolean(slot.is_rest))
    if (isNonProductiveSlotType(st)) restRaw.push(...parts)
    else workRaw.push(...parts)
  }
  const workM = mergeMinuteIntervals(workRaw)
  const restM = mergeMinuteIntervals(restRaw)
  const productive = subtractRestFromWork(workM, restM)
  return productive.reduce((acc, [sm, em]) => acc + (em - sm) / 60, 0)
}

async function saveAll() {
  if (!guardApsOperation(canEdit)) return
  if (!selectedLineId.value) return
  saving.value = true
  try {
    const days = daySlots.value.map(d => ({
      line_id: selectedLineId.value!,
      work_date: d.work_date,
      slots: d.editSlots
        .filter(s => s.start_time && s.end_time)
        .map((s, idx) => {
          const slot_type = normalizeSlotType(s.slot_type, Boolean(s.is_rest))
          return {
            start_time: s.start_time,
            end_time: s.end_time,
            sort_order: idx,
            is_rest: isNonProductiveSlotType(slot_type),
            slot_type,
            note: (s.note || '').trim() || null,
          }
        }),
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
  padding: 6px 8px 10px;
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
  gap: 6px 10px;
  margin: 0 0 6px;
  padding: 6px 8px 8px;
  border-bottom: 1px solid var(--el-border-color-extra-light);
  font-size: 12px;
  border-radius: 8px;
  background: var(--el-fill-color-lighter);
}

.toolbar-embed__line {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.toolbar-embed__range {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--el-text-color-secondary);
  font-variant-numeric: tabular-nums;
}

.toolbar-embed__ico {
  font-size: 14px;
  color: var(--el-color-primary);
}

.toolbar-embed__ico--muted {
  color: var(--el-text-color-secondary);
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
  padding: 6px 10px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  border-left: 3px solid var(--el-color-primary);
  background: linear-gradient(
    105deg,
    var(--el-color-primary-light-9) 0%,
    var(--el-fill-color-blank) 42%,
    var(--el-bg-color) 100%
  );
}

.capacity-card :deep(.el-card__body) {
  min-width: 0;
}

.card-head__title {
  margin: 0 0 2px;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.35;
  color: var(--el-text-color-primary);
  letter-spacing: 0.02em;
}

.card-head__title-inner {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.card-head__title-icon {
  font-size: 18px;
  color: var(--el-color-primary);
}

.card-head__desc {
  margin: 0;
  font-size: 11px;
  line-height: 1.4;
  color: var(--el-text-color-secondary);
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 0 4px;
  margin: 0 0 6px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--el-border-color-extra-light);
}

.toolbar.toolbar--filter-bar {
  margin: 0 0 10px;
  padding: 8px 10px 10px;
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
  background: linear-gradient(180deg, var(--el-fill-color-blank) 0%, var(--el-fill-color-lighter) 100%);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  gap: 8px 10px;
  align-items: flex-end;
}

.toolbar__lbl {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
  color: var(--el-text-color-regular);
}

.toolbar__lbl .el-icon {
  font-size: 14px;
  color: var(--el-color-primary);
}

.bulk-apply-panel {
  margin: 0 0 10px;
  padding: 8px 10px 9px;
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
  background: linear-gradient(
    135deg,
    var(--el-color-warning-light-9) 0%,
    var(--el-fill-color-light) 55%,
    var(--el-bg-color) 100%
  );
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.bulk-apply-panel__head {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 6px 10px;
  margin-bottom: 6px;
}

.bulk-apply-panel__title {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.bulk-apply-panel__title-icon {
  font-size: 15px;
  color: var(--el-color-warning);
}

.bulk-apply-panel__hint {
  font-size: 10px;
  color: var(--el-text-color-secondary);
  line-height: 1.35;
}

.bulk-apply-panel__hint strong {
  font-variant-numeric: tabular-nums;
  color: var(--el-color-primary);
}

.bulk-apply-panel__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 6px;
  align-items: center;
}

.bulk-apply-panel__actions :deep(.el-button) {
  padding: 4px 8px;
  margin: 0;
  font-size: 11px;
  border-radius: 6px;
}

/* 一括保存：緑を強調 */
.lcap-btn-save.el-button--success:not(.is-loading) {
  font-weight: 600;
  box-shadow: 0 1px 3px rgba(103, 194, 58, 0.35);
}

.lcap-btn-save.el-button--success:hover:not(.is-disabled) {
  box-shadow: 0 2px 6px rgba(103, 194, 58, 0.45);
}

/* 再取得：プライマリをやや立体感 */
.lcap-btn-refresh.el-button--primary:not(.is-loading) {
  font-weight: 600;
  box-shadow: 0 1px 3px rgba(64, 158, 255, 0.35);
}

.lcap-btn-refresh.el-button--primary:hover:not(.is-disabled) {
  box-shadow: 0 2px 6px rgba(64, 158, 255, 0.45);
}

/* 今月／次月：色の役割をはっきり */
.lcap-btn-month-this.is-plain {
  --el-button-bg-color: var(--el-color-primary-light-9);
}

.lcap-btn-month-next.is-plain {
  --el-button-bg-color: var(--el-color-success-light-9);
}

/* 全日削除：危険操作として枠を強める */
.lcap-btn-bulk-clear.is-plain {
  font-weight: 600;
  --el-button-border-color: var(--el-color-danger-light-5);
}

/* 日別「削除」 */
.lcap-btn-day-clear.is-plain:not(.is-disabled) {
  font-weight: 600;
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

/* 22H：琥珀（20H の警告橙と差別化）／24H：プライマリ青（2H の info と差別化） */
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
  gap: 6px;
  align-items: stretch;
  min-height: 72px;
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
  border-radius: 8px;
  padding: 5px 6px 5px;
  background: var(--el-bg-color);
  transition: border-color 0.15s, box-shadow 0.15s;
  /* grid 子项默认 min-width:auto 会按内容撑破列宽 */
  min-width: 0;
  max-width: 100%;
  box-sizing: border-box;
}

.day-card:hover {
  border-color: var(--el-color-primary-light-5);
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.12);
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
  gap: 3px;
  margin-bottom: 3px;
  padding-bottom: 3px;
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
  display: inline-flex;
  align-items: center;
  gap: 3px;
  margin-left: auto;
  padding: 1px 6px;
  border-radius: 999px;
  font-variant-numeric: tabular-nums;
  font-size: 11px;
  font-weight: 700;
  color: var(--el-color-success-dark-2);
  background: var(--el-color-success-light-9);
  border: 1px solid var(--el-color-success-light-7);
}

.day-card__tag-icon {
  font-size: 12px;
}

.day-card__tag--zero {
  color: var(--el-text-color-placeholder);
  background: var(--el-fill-color);
  border-color: var(--el-border-color-lighter);
}

.day-card__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 3px;
}

.day-card__actions :deep(.el-button) {
  padding: 3px 6px;
  margin: 0;
  font-size: 11px;
  border-radius: 6px;
}

/* プリセット列：種類ごとにトーンを固定（plain の見え方を安定） */
.day-card__actions :deep(.el-button--info.is-plain) {
  --el-button-bg-color: var(--el-fill-color-light);
}

.day-card__actions :deep(.el-button--success.is-plain) {
  --el-button-bg-color: var(--el-color-success-light-9);
}

.day-card__actions :deep(.el-button--primary.is-plain) {
  --el-button-bg-color: var(--el-color-primary-light-9);
}

.day-card__actions :deep(.el-button--warning.is-plain) {
  --el-button-bg-color: var(--el-color-warning-light-9);
}

.day-card__actions :deep(.el-button--danger.is-plain:not(.is-disabled)) {
  --el-button-bg-color: var(--el-color-danger-light-9);
}

.slots-list {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
  max-width: 100%;
}

.slot-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 5px;
  padding: 2px 3px;
  border-radius: 6px;
  min-width: 0;
  max-width: 100%;
  box-sizing: border-box;
}

.slot-row--rest {
  background: linear-gradient(90deg, var(--el-color-warning-light-9) 0%, var(--el-fill-color-light) 100%);
  border: 1px dashed var(--el-border-color-lighter);
}

.slot-row--tech {
  background: linear-gradient(90deg, #fff4e5 0%, var(--el-fill-color-light) 100%);
  border: 1px solid #f5a62355;
}

.slot-row--maintenance {
  background: linear-gradient(90deg, var(--el-color-info-light-9) 0%, var(--el-fill-color-light) 100%);
  border: 1px dashed var(--el-color-info-light-5);
}

.slots-list__add {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
  padding: 2px 0 0;
}

.slot-row__type {
  width: 96px;
  flex-shrink: 0;
}

.slot-row__note {
  width: 100%;
  flex: 1 1 100%;
  min-width: 0;
  max-width: 100%;
  margin-left: 0;
}

.day-card__occ {
  display: inline-flex;
  align-items: center;
  margin-left: 4px;
  padding: 0 5px;
  border-radius: 4px;
  font-size: 10px;
  line-height: 1.5;
  font-weight: 600;
}

.day-card__occ--tech {
  background: #fff4e5;
  color: #b45309;
  border: 1px solid #f5a62355;
}

.day-card__occ--maintenance {
  background: var(--el-color-info-light-9);
  color: var(--el-color-info);
  border: 1px dashed var(--el-color-info-light-5);
}

.day-card__occ--mixed {
  background: #fff7ed;
  color: #9a3412;
  border: 1px solid #fdba74;
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
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  text-align: center;
  padding: 14px 10px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  border-radius: 8px;
  border: 1px dashed var(--el-border-color-lighter);
  background: var(--el-fill-color-lighter);
}

.empty__icon {
  font-size: 28px;
  color: var(--el-color-primary-light-3);
}

.empty--hint .empty__icon {
  color: var(--el-color-warning);
}

.empty__text {
  margin: 0;
  max-width: 420px;
  line-height: 1.45;
}

/* 页面美化：現代UI・3D動効・色分け（設備稼働設定 / APS blue→indigo→violet・単独画面のみ） */
.lc-modern {
  --lc-c1: #1d4ed8;
  --lc-c2: #4f46e5;
  --lc-c3: #7c3aed;
  padding: 8px 10px 12px;
}
.lc-modern .capacity-card {
  border: 1px solid color-mix(in srgb, var(--lc-c2) 16%, var(--el-border-color-lighter));
  border-radius: 14px;
  box-shadow:
    0 14px 30px -22px rgba(55, 48, 163, 0.5),
    0 1px 3px rgba(15, 23, 42, 0.05);
}

/* ---- Hero ヘッダー ---- */
.lc-modern .capacity-card :deep(.el-card__header) {
  position: relative;
  overflow: hidden;
  padding: 12px 16px;
  border-bottom: none;
  border-left: none;
  color: #fff;
  background: linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 30%, #4f46e5 64%, #7c3aed 100%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.18);
}
.lc-modern .card-head__fx {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}
.lc-modern .fx-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(2px);
  animation: lcOrbFloat 9s ease-in-out infinite;
}
.lc-modern .orb-a {
  width: 190px;
  height: 190px;
  top: -90px;
  right: 16%;
  background: radial-gradient(circle at 35% 35%, rgba(255, 255, 255, 0.3), rgba(165, 180, 252, 0) 70%);
}
.lc-modern .orb-b {
  width: 130px;
  height: 130px;
  bottom: -70px;
  left: 34%;
  background: radial-gradient(circle at 40% 40%, rgba(196, 181, 253, 0.4), rgba(196, 181, 253, 0) 70%);
  animation-delay: -4s;
}
.lc-modern .fx-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.07) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.07) 1px, transparent 1px);
  background-size: 22px 22px;
  mask-image: linear-gradient(90deg, transparent 0%, #000 45%, transparent 100%);
}
.lc-modern .fx-sheen {
  position: absolute;
  inset: 0;
  background: linear-gradient(110deg, transparent 30%, rgba(255, 255, 255, 0.16) 48%, transparent 62%);
  background-size: 250% 100%;
  animation: lcSheen 6s ease-in-out infinite;
}
.lc-modern .card-head__main,
.lc-modern .card-head__actions {
  position: relative;
  z-index: 1;
}
.lc-modern .card-head--with-actions {
  align-items: center;
}
.lc-modern .card-head__title {
  font-size: 17px;
  font-weight: 800;
  color: #fff;
  text-shadow: 0 2px 6px rgba(30, 27, 75, 0.35);
}
.lc-modern .card-head__title-inner {
  gap: 10px;
}
.lc-modern .card-head__title-icon {
  width: 34px;
  height: 34px;
  font-size: 19px;
  color: #fff;
  border-radius: 10px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.34), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.38);
  box-shadow:
    0 8px 16px -6px rgba(30, 27, 75, 0.55),
    inset 0 -3px 0 rgba(30, 27, 75, 0.25),
    inset 0 1px 0 rgba(255, 255, 255, 0.45);
  animation: lcIconFloat 4.5s ease-in-out infinite;
}
.lc-modern .card-head__desc {
  margin-top: 4px;
  color: rgba(255, 255, 255, 0.84);
}
.lc-modern .card-head__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}
.lc-modern .card-head__chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  font-variant-numeric: tabular-nums;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(6px);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2);
}
.lc-modern .card-head__chip--strong {
  background: rgba(255, 255, 255, 0.26);
  border-color: rgba(255, 255, 255, 0.5);
}

/* ---- 3D キーキャップボタン ---- */
.lc-modern .lcap-btn-save.el-button--success,
.lc-modern .toolbar__quick-month-btn,
.lc-modern .bulk-apply-panel__actions :deep(.el-button),
.lc-modern .slots-list__add :deep(.el-button) {
  --k-edge: #3730a3;
  --k-glow: rgba(79, 70, 229, 0.45);
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease,
    filter 0.15s ease;
  box-shadow:
    0 3px 0 var(--k-edge),
    0 10px 18px -10px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
}
.lc-modern .lcap-btn-save:not(.is-disabled):hover,
.lc-modern .toolbar__quick-month-btn:not(.is-disabled):hover,
.lc-modern .bulk-apply-panel__actions :deep(.el-button:not(.is-disabled):hover),
.lc-modern .slots-list__add :deep(.el-button:not(.is-disabled):hover) {
  transform: translateY(-2px);
  filter: brightness(1.04);
  box-shadow:
    0 5px 0 var(--k-edge),
    0 14px 22px -10px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
}
.lc-modern .lcap-btn-save:not(.is-disabled):active,
.lc-modern .toolbar__quick-month-btn:not(.is-disabled):active,
.lc-modern .bulk-apply-panel__actions :deep(.el-button:not(.is-disabled):active),
.lc-modern .slots-list__add :deep(.el-button:not(.is-disabled):active) {
  transform: translateY(2px);
  box-shadow:
    0 1px 0 var(--k-edge),
    0 4px 8px -6px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
}
.lc-modern .lcap-btn-save.is-disabled {
  box-shadow: none;
}
.lc-modern .lcap-btn-save.el-button--success {
  --k-edge: #15803d;
  --k-glow: rgba(22, 163, 74, 0.55);
  border: none;
  font-weight: 700;
  background: linear-gradient(180deg, #4ade80, #16a34a);
}
.lc-modern .bulk-apply-panel__actions :deep(.el-button--primary),
.lc-modern .slots-list__add :deep(.el-button--primary),
.lc-modern .lcap-btn-month-this {
  --k-edge: #93c5fd;
  --k-glow: rgba(37, 99, 235, 0.35);
}
.lc-modern .bulk-apply-panel__actions :deep(.el-button--success),
.lc-modern .lcap-btn-month-next {
  --k-edge: #86efac;
  --k-glow: rgba(22, 163, 74, 0.35);
}
.lc-modern .bulk-apply-panel__actions :deep(.el-button--warning),
.lc-modern .slots-list__add :deep(.el-button--warning) {
  --k-edge: #fcd34d;
  --k-glow: rgba(217, 119, 6, 0.35);
}
.lc-modern .bulk-apply-panel__actions :deep(.el-button--info),
.lc-modern .slots-list__add :deep(.el-button--info) {
  --k-edge: #cbd5e1;
  --k-glow: rgba(100, 116, 139, 0.3);
}
.lc-modern .bulk-apply-panel__actions :deep(.el-button--danger) {
  --k-edge: #fca5a5;
  --k-glow: rgba(239, 68, 68, 0.35);
}
.lc-modern .bulk-apply-panel__actions :deep(.lcap-preset--22h) {
  --k-edge: #fbbf24;
  --k-glow: rgba(217, 119, 6, 0.35);
}
.lc-modern .bulk-apply-panel__actions :deep(.lcap-preset--24h) {
  --k-edge: #a5b4fc;
  --k-glow: rgba(79, 70, 229, 0.35);
}
.lc-modern .slots-list__add :deep(.el-button:not(.el-button--primary):not(.el-button--warning):not(.el-button--info)) {
  --k-edge: #e2e8f0;
  --k-glow: rgba(100, 116, 139, 0.25);
}

/* ---- ツールバー・一括パネル ---- */
.lc-modern .toolbar.toolbar--filter-bar,
.lc-modern .bulk-apply-panel {
  position: relative;
  overflow: hidden;
  border-radius: 12px;
  border-color: color-mix(in srgb, var(--lc-c2) 14%, var(--el-border-color-lighter));
  box-shadow: 0 10px 20px -18px rgba(55, 48, 163, 0.5);
}
.lc-modern .toolbar.toolbar--filter-bar {
  padding-top: 11px;
  background: linear-gradient(105deg, color-mix(in srgb, var(--lc-c2) 6%, #fff) 0%, #fff 60%);
}
.lc-modern .toolbar.toolbar--filter-bar::before,
.lc-modern .bulk-apply-panel::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 3px;
}
.lc-modern .toolbar.toolbar--filter-bar::before {
  background: linear-gradient(90deg, var(--lc-c1), var(--lc-c2), var(--lc-c3));
}
.lc-modern .bulk-apply-panel {
  padding-top: 11px;
  background: linear-gradient(105deg, #fffbeb 0%, #fff 60%);
}
.lc-modern .bulk-apply-panel::before {
  background: linear-gradient(90deg, #f59e0b, #f97316, #ef4444);
}
.lc-modern .toolbar__lbl {
  font-weight: 600;
  color: var(--el-text-color-primary);
}
.lc-modern .toolbar__lbl .el-icon {
  width: 20px;
  height: 20px;
  border-radius: 6px;
  color: #fff;
  font-size: 12px;
  background: linear-gradient(135deg, var(--lc-c1), var(--lc-c3));
  box-shadow: 0 3px 8px -3px rgba(79, 70, 229, 0.6);
}
.lc-modern .bulk-apply-panel__title-icon {
  width: 22px;
  height: 22px;
  border-radius: 7px;
  color: #fff;
  font-size: 13px;
  background: linear-gradient(135deg, #f59e0b, #ea580c);
  box-shadow: 0 3px 8px -3px rgba(234, 88, 12, 0.6);
}
.lc-modern .toolbar :deep(.el-input__wrapper),
.lc-modern .toolbar :deep(.el-select__wrapper) {
  border-radius: 8px;
  transition: box-shadow 0.2s ease;
}
.lc-modern .toolbar :deep(.el-input__wrapper:hover),
.lc-modern .toolbar :deep(.el-select__wrapper:hover) {
  box-shadow:
    0 0 0 1px color-mix(in srgb, var(--lc-c2) 45%, transparent) inset,
    0 4px 10px -6px rgba(79, 70, 229, 0.5);
}

/* ---- 日カード：稼働時間で色分け＋浮上 ---- */
.lc-modern .calendar-grid {
  gap: 8px;
  padding: 2px 2px 6px;
}
.lc-modern .calendar-grid-scroll::-webkit-scrollbar {
  width: 8px;
}
.lc-modern .calendar-grid-scroll::-webkit-scrollbar-thumb {
  border-radius: 8px;
  background: linear-gradient(180deg, #818cf8, #6d28d9);
}
.lc-modern .calendar-grid-scroll::-webkit-scrollbar-track {
  background: color-mix(in srgb, var(--lc-c2) 6%, #fff);
}
.lc-modern .day-card {
  --dc: #94a3b8;
  position: relative;
  overflow: hidden;
  padding: 8px 8px 6px;
  border-radius: 12px;
  border-color: color-mix(in srgb, var(--dc) 26%, var(--el-border-color-lighter));
  background: linear-gradient(170deg, color-mix(in srgb, var(--dc) 7%, #fff) 0%, #fff 45%);
  box-shadow:
    0 2px 0 color-mix(in srgb, var(--dc) 22%, #e2e8f0),
    0 8px 16px -14px color-mix(in srgb, var(--dc) 70%, transparent);
  transition:
    transform 0.18s ease,
    box-shadow 0.2s ease,
    border-color 0.2s ease;
  animation: lcCardIn 0.35s ease-out backwards;
}
.lc-modern .day-card::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--dc), color-mix(in srgb, var(--dc) 40%, #fff));
}
.lc-modern .day-card:hover {
  transform: translateY(-2px);
  border-color: color-mix(in srgb, var(--dc) 50%, var(--el-border-color-lighter));
  box-shadow:
    0 4px 0 color-mix(in srgb, var(--dc) 30%, #e2e8f0),
    0 14px 24px -14px color-mix(in srgb, var(--dc) 80%, transparent);
}
.lc-modern .day-card--h-zero {
  --dc: #94a3b8;
}
.lc-modern .day-card--h-short {
  --dc: #0ea5e9;
}
.lc-modern .day-card--h-mid {
  --dc: #2563eb;
}
.lc-modern .day-card--h-long {
  --dc: #d97706;
}
.lc-modern .day-card--h-full {
  --dc: #7c3aed;
}
.lc-modern .day-card--weekend {
  background: linear-gradient(170deg, #fff1f2 0%, #fff 45%);
}
.lc-modern .day-card__date {
  font-size: 14px;
  font-weight: 800;
  color: var(--el-text-color-primary);
}
.lc-modern .day-card__tag {
  color: #fff;
  border: none;
  background: linear-gradient(135deg, color-mix(in srgb, var(--dc) 70%, #fff), var(--dc));
  box-shadow:
    0 2px 0 color-mix(in srgb, var(--dc) 60%, #0f172a),
    0 4px 8px -4px color-mix(in srgb, var(--dc) 70%, transparent);
}
.lc-modern .day-card__tag--zero {
  color: var(--el-text-color-secondary);
  background: var(--el-fill-color);
  box-shadow: 0 2px 0 var(--el-border-color-lighter);
}

/* ---- 時間帯行：種別の左バー ---- */
.lc-modern .slot-row {
  padding: 3px 4px 3px 7px;
  box-shadow: inset 3px 0 0 #3b82f6;
  transition: background 0.15s ease;
}
.lc-modern .slot-row:hover {
  background-color: color-mix(in srgb, var(--lc-c2) 5%, transparent);
}
.lc-modern .slot-row--rest {
  box-shadow: inset 3px 0 0 #f59e0b;
}
.lc-modern .slot-row--tech {
  box-shadow: inset 3px 0 0 #ea580c;
}
.lc-modern .slot-row--maintenance {
  box-shadow: inset 3px 0 0 #64748b;
}

/* ---- 空状態 ---- */
.lc-modern .empty {
  border-radius: 12px;
  background: linear-gradient(180deg, color-mix(in srgb, var(--lc-c2) 5%, #fff), #fff);
}
.lc-modern .empty__icon {
  width: 56px;
  height: 56px;
  font-size: 30px;
  color: #fff;
  border-radius: 16px;
  background: linear-gradient(145deg, #818cf8, #6d28d9);
  box-shadow:
    0 12px 20px -10px rgba(79, 70, 229, 0.7),
    inset 0 -3px 0 rgba(30, 27, 75, 0.25);
  animation: lcIconFloat 4.5s ease-in-out infinite;
}
.lc-modern .empty--hint .empty__icon {
  color: #fff;
  background: linear-gradient(145deg, #fbbf24, #ea580c);
}
.lc-modern :deep(.el-loading-spinner .path) {
  stroke: var(--lc-c2);
}

@keyframes lcOrbFloat {
  0%,
  100% {
    transform: translate3d(0, 0, 0);
  }
  50% {
    transform: translate3d(-18px, 12px, 0);
  }
}
@keyframes lcSheen {
  0% {
    background-position: 130% 0;
  }
  100% {
    background-position: -30% 0;
  }
}
@keyframes lcIconFloat {
  0%,
  100% {
    transform: perspective(300px) rotateX(10deg) rotateY(-14deg) translateY(0);
  }
  50% {
    transform: perspective(300px) rotateX(-4deg) rotateY(12deg) translateY(-2px);
  }
}
@keyframes lcCardIn {
  from {
    opacity: 0;
    transform: translate3d(0, 8px, 0);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .lc-modern .fx-orb,
  .lc-modern .fx-sheen,
  .lc-modern .card-head__title-icon,
  .lc-modern .empty__icon,
  .lc-modern .day-card {
    animation: none;
  }
  .lc-modern .day-card:hover {
    transform: none;
  }
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
