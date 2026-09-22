<template>
  <div class="uevents-page">
    <div class="uevents-orb uevents-orb--indigo" aria-hidden="true" />
    <div class="uevents-orb uevents-orb--violet" aria-hidden="true" />
    <div class="uevents-orb uevents-orb--cyan" aria-hidden="true" />

    <header class="uevents-hero">
      <div class="uevents-hero__left">
        <div class="uevents-hero__icon">
          <el-icon :size="18"><Calendar /></el-icon>
        </div>
        <div>
          <div class="uevents-hero__eyebrow">{{ t('common.userEventPageTitle') }}</div>
          <h1 class="uevents-hero__title">{{ periodLabel }}</h1>
        </div>
      </div>
      <div class="uevents-hero__stats">
        <div class="uevents-stat">
          <span class="uevents-stat__num">{{ todayCount }}</span>
          <span class="uevents-stat__label">{{ t('common.userEventStatToday') }}</span>
        </div>
        <div class="uevents-stat uevents-stat--accent">
          <span class="uevents-stat__num">{{ weekCount }}</span>
          <span class="uevents-stat__label">{{ t('common.userEventStatWeek') }}</span>
        </div>
        <div class="uevents-stat uevents-stat--warn">
          <span class="uevents-stat__num">{{ remindCount }}</span>
          <span class="uevents-stat__label">{{ t('common.userEventStatRemind') }}</span>
        </div>
      </div>
    </header>

    <div class="uevents-shell">
      <aside class="uevents-sidebar">
        <el-button type="primary" class="uevents-sidebar__create" :icon="Plus" @click="openCreate()">
          {{ t('common.userEventNew') }}
        </el-button>

        <section class="uevents-mini">
          <div class="uevents-mini__nav">
            <button type="button" class="uevents-mini__btn" @click="shiftSidebarMonth(-1)">
              <el-icon :size="12"><ArrowLeft /></el-icon>
            </button>
            <span class="uevents-mini__label">{{ sidebarMonthLabel }}</span>
            <button type="button" class="uevents-mini__btn" @click="shiftSidebarMonth(1)">
              <el-icon :size="12"><ArrowRight /></el-icon>
            </button>
          </div>
          <div class="uevents-mini__weekdays">
            <span v-for="(w, i) in weekdayHeaders" :key="i" class="uevents-mini__wd">{{ w.slice(0, 1) }}</span>
          </div>
          <div class="uevents-mini__grid">
            <button
              v-for="(cell, idx) in sidebarCells"
              :key="idx"
              type="button"
              class="uevents-mini__day"
              :class="miniDayClass(cell)"
              :disabled="!cell.inMonth"
              @click="cell.inMonth && pickDate(cell.date)"
            >
              <template v-if="cell.inMonth">{{ cell.day }}</template>
            </button>
          </div>
        </section>

        <section class="uevents-upcoming">
          <div class="uevents-upcoming__head">
            <el-icon :size="14"><Clock /></el-icon>
            {{ t('common.userEventUpcoming') }}
          </div>
          <div v-if="!upcomingList.length" class="uevents-upcoming__empty">
            {{ t('common.userEventUpcomingEmpty') }}
          </div>
          <button
            v-for="ev in upcomingList"
            :key="`${ev.id}-${ev.occurrence_date || ev.start_at}`"
            type="button"
            class="uevents-upcoming__item"
            @click="openEdit(ev)"
          >
            <span class="uevents-upcoming__dot" :class="`is-${ev.color}`" />
            <span class="uevents-upcoming__text">
              <span class="uevents-upcoming__title">{{ ev.title }}</span>
              <span class="uevents-upcoming__time">{{ formatUpcoming(ev) }}</span>
            </span>
          </button>
        </section>

        <p class="uevents-sidebar__hint">{{ t('common.userEventDragHint') }}</p>
      </aside>

      <main class="uevents-main">
        <div class="uevents-toolbar">
          <el-button size="small" round @click="goToday">{{ t('common.userMemoToday') }}</el-button>
          <div class="uevents-toolbar__nav">
            <button type="button" class="uevents-toolbar__nav-btn" @click="shiftPeriod(-1)">
              <el-icon :size="14"><ArrowLeft /></el-icon>
            </button>
            <el-date-picker
              v-model="toolbarMonth"
              type="month"
              value-format="YYYY-MM"
              :format="monthPickerFormat"
              :clearable="false"
              :editable="false"
              class="uevents-toolbar__month-picker"
              :title="t('common.userEventPickMonth')"
            />
            <button type="button" class="uevents-toolbar__nav-btn" @click="shiftPeriod(1)">
              <el-icon :size="14"><ArrowRight /></el-icon>
            </button>
            <span class="uevents-toolbar__workday-total" :title="t('common.userEventWorkdayTotalHint')">
              {{ t('common.userEventWorkdayTotal', { n: monthWorkdayCount }) }}
            </span>
          </div>
          <el-radio-group v-model="viewMode" size="small" class="uevents-view-switch">
            <el-radio-button value="month">{{ t('common.userEventViewMonth') }}</el-radio-button>
            <el-radio-button value="week">{{ t('common.userEventViewWeek') }}</el-radio-button>
            <el-radio-button value="day">{{ t('common.userEventViewDay') }}</el-radio-button>
          </el-radio-group>
          <el-radio-group v-model="listFilter" size="small" class="uevents-filter-switch">
            <el-radio-button value="all">{{ t('common.userEventFilterAll') }}</el-radio-button>
            <el-radio-button value="mine">{{ t('common.userEventFilterMine') }}</el-radio-button>
          </el-radio-group>
          <span class="uevents-scope-chip" :title="scopeHintFull">{{ scopeHintShort }}</span>
        </div>

        <div v-loading="loading" class="uevents-body">
          <section v-if="viewMode === 'month'" class="uevents-month">
            <div class="uevents-month__weekdays">
              <span
                v-for="(w, idx) in weekdayHeaders"
                :key="w"
                class="uevents-month__wd"
                :class="{ 'is-sun': idx === 0, 'is-sat': idx === 6 }"
              >{{ w }}</span>
            </div>
            <div class="uevents-month__grid">
              <div
                v-for="(cell, idx) in monthCells"
                :key="idx"
                class="uevents-month__cell"
                :class="[
                  monthCellClass(cell),
                  cell.inMonth && idx % 7 === 0 ? 'is-sun-col' : '',
                  cell.inMonth && idx % 7 === 6 ? 'is-sat-col' : '',
                  { 'is-drop-target': dropTargetDate === cell.date },
                ]"
                @click="onMonthCellClick(cell)"
                @dragover.prevent="onMonthDragOver(cell)"
                @dragleave="onMonthDragLeave(cell)"
                @drop.prevent="onMonthDrop(cell)"
              >
                <template v-if="cell.inMonth">
                  <div class="uevents-month__cell-head">
                    <div class="uevents-month__day-wrap">
                      <span class="uevents-month__day">{{ cell.day }}</span>
                      <span v-if="isCompanyWorkday(cell.date)" class="uevents-month__workday">
                        {{ t('common.userEventWorkday') }}
                      </span>
                    </div>
                    <button
                      type="button"
                      class="uevents-month__add"
                      @click.stop="openCreate(cell.date)"
                    >
                      <el-icon :size="12"><Plus /></el-icon>
                    </button>
                  </div>
                  <div class="uevents-month__events">
                    <button
                      v-for="ev in cell.events.slice(0, 4)"
                      :key="eventKey(ev)"
                      type="button"
                      :draggable="!!ev.is_owner"
                      class="uevents-chip"
                      :class="[
                        `uevents-chip--${ev.color}`,
                        {
                          'is-dragging': draggingKey === eventKey(ev),
                          'is-shared': !ev.is_owner,
                          'is-private': ev.visibility === 'self',
                        },
                      ]"
                      @click.stop="openEdit(ev)"
                      @dragstart="ev.is_owner && onMonthDragStart(ev, $event)"
                      @dragend="onDragEnd"
                    >
                      <el-icon v-if="ev.visibility === 'self'" class="uevents-chip__bell" :size="10"><Lock /></el-icon>
                      <el-icon v-else-if="ev.visibility === 'all'" class="uevents-chip__bell" :size="10"><OfficeBuilding /></el-icon>
                      <el-icon v-else-if="!ev.is_owner" class="uevents-chip__bell" :size="10"><Share /></el-icon>
                      <el-icon v-if="ev.remind_offset_minutes != null" class="uevents-chip__bell" :size="10"><Bell /></el-icon>
                      <el-icon v-if="ev.recurrence_rule" class="uevents-chip__repeat" :size="10"><RefreshRight /></el-icon>
                      <span v-if="!ev.all_day" class="uevents-chip__time">{{ formatEventTime(ev) }}</span>
                      <span class="uevents-chip__title">{{ ev.title }}</span>
                    </button>
                    <span v-if="cell.events.length > 4" class="uevents-month__more">
                      +{{ cell.events.length - 4 }}
                    </span>
                  </div>
                </template>
              </div>
            </div>
          </section>

          <section v-else class="uevents-time" :style="{ '--uevents-cols': String(timeColumns.length) }">
            <div class="uevents-time__allday">
              <div class="uevents-time__corner">{{ t('common.userMemoAllDay') }}</div>
              <div
                v-for="col in timeColumns"
                :key="`allday-${col.key}`"
                class="uevents-time__allday-col"
                :class="{ 'is-today': col.isToday, 'is-drop-target': dropTargetDate === col.date }"
                @dragover.prevent="dropTargetDate = col.date"
                @drop.prevent="onAllDayDrop(col)"
              >
                <div v-if="viewMode === 'week'" class="uevents-time__col-head">
                  <span class="uevents-time__col-wd">{{ col.weekday }}</span>
                  <div class="uevents-time__col-day-row">
                    <span class="uevents-time__col-day" :class="{ 'is-today': col.isToday }">{{ col.day }}</span>
                    <span v-if="isCompanyWorkday(col.date)" class="uevents-time__workday">
                      {{ t('common.userEventWorkday') }}
                    </span>
                  </div>
                </div>
                <button
                  v-for="ev in col.allDayEvents"
                  :key="eventKey(ev)"
                  type="button"
                  :draggable="!!ev.is_owner"
                  class="uevents-chip uevents-chip--block"
                  :class="`uevents-chip--${ev.color}`"
                  @click="openEdit(ev)"
                  @dragstart="ev.is_owner && onMonthDragStart(ev, $event)"
                  @dragend="onDragEnd"
                >
                  <el-icon v-if="ev.visibility === 'self'" :size="10"><Lock /></el-icon>
                  {{ ev.title }}
                </button>
              </div>
            </div>

            <div ref="timeScrollRef" class="uevents-time__scroll">
              <div class="uevents-time__hours">
                <div v-for="h in hourLabels" :key="h" class="uevents-time__hour">{{ h }}</div>
              </div>
              <div class="uevents-time__cols">
                <div
                  v-for="col in timeColumns"
                  :key="col.key"
                  class="uevents-time__col"
                  :class="{ 'is-today': col.isToday, 'is-drop-target': dropTargetDate === col.date }"
                  @click="onTimeColClick(col, $event)"
                  @dragover.prevent="dropTargetDate = col.date"
                  @drop.prevent="onTimedDrop(col, $event)"
                >
                  <div
                    v-if="col.isToday && nowLineTop != null"
                    class="uevents-now-line"
                    :style="{ top: `${nowLineTop}px` }"
                  />
                  <div v-for="h in HOURS" :key="h" class="uevents-time__slot" />
                  <button
                    v-for="block in col.timedBlocks"
                    :key="eventKey(block.ev)"
                    type="button"
                    class="uevents-block"
                    :class="[
                      `uevents-block--${block.ev.color}`,
                      { 'is-dragging': pointerDrag?.key === eventKey(block.ev) },
                    ]"
                    :style="blockStyle(block)"
                    @click.stop="openEdit(block.ev)"
                    @mousedown.prevent="block.ev.is_owner && startPointerDrag(block.ev, col.date, $event)"
                  >
                    <span class="uevents-block__title">
                      <el-icon v-if="block.ev.visibility === 'self'" :size="10"><Lock /></el-icon>
                      {{ block.ev.title }}
                    </span>
                    <span class="uevents-block__time">{{ formatEventRange(block.ev) }}</span>
                  </button>
                </div>
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>

    <UserEventFormDialog
      v-model="dialogVisible"
      :editing="editingEvent"
      :initial-date="dialogInitialDate"
      :initial-hour="dialogInitialHour"
      :submitting="submitting"
      :deleting="deleting"
      :readonly="dialogReadonly"
      @submit="onFormSubmit"
      @delete="confirmDelete"
    />

    <el-dialog
      v-model="scopeDialogVisible"
      :title="t('common.userEventRecurrenceScopeTitle')"
      width="420px"
      append-to-body
      align-center
      destroy-on-close
      @closed="onScopeDialogClosed"
    >
      <p class="uevents-scope-dialog__hint">{{ t('common.userEventRecurrenceScopeHint') }}</p>
      <div class="uevents-scope-dialog__actions">
        <el-button @click="resolveScopeDialog('this')">{{ t('common.userEventRecurrenceThis') }}</el-button>
        <el-button @click="resolveScopeDialog('following')">{{ t('common.userEventRecurrenceFollowing') }}</el-button>
        <el-button type="primary" @click="resolveScopeDialog('all')">{{ t('common.userEventRecurrenceAll') }}</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import {
  Calendar,
  ArrowLeft,
  ArrowRight,
  Plus,
  Bell,
  RefreshRight,
  Clock,
  Lock,
  Share,
  OfficeBuilding,
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import dayjs from 'dayjs'
import UserEventFormDialog from '@/components/account/UserEventFormDialog.vue'
import {
  createUserEvent,
  deleteUserEvent,
  eventDurationMinutes,
  getUserEvents,
  isRecurringOccurrence,
  rescheduleUserEvent,
  updateUserEvent,
  type UserEventCreatePayload,
  type UserEventEditScope,
  type UserEventItem,
  type UserEventViewerScope,
} from '@/api/auth/events'
import { useUserEvents } from '@/composables/useUserEvents'
import {
  fetchCompanyWorkCalendar,
  type CompanyWorkCalendarItem,
} from '@/api/master/companyWorkCalendar'

type ViewMode = 'month' | 'week' | 'day'

const HOURS = Array.from({ length: 17 }, (_, i) => i + 6)
const HOUR_PX = 52
const SNAP_MIN = 15

const { t, locale } = useI18n()
const userEvents = useUserEvents()

const viewMode = ref<ViewMode>('month')
const listFilter = ref<'all' | 'mine'>('all')
const viewerScope = ref<UserEventViewerScope>('department')
const anchorDate = ref(dayjs().format('YYYY-MM-DD'))
const sidebarMonth = ref(dayjs().format('YYYY-MM'))
const events = ref<UserEventItem[]>([])
const workCalendarByDate = ref<Map<string, CompanyWorkCalendarItem>>(new Map())
const loading = ref(false)
const submitting = ref(false)
const deleting = ref(false)
const timeScrollRef = ref<HTMLElement | null>(null)
const suppressClickUntil = ref(0)

const dialogVisible = ref(false)
const editingEvent = ref<UserEventItem | null>(null)
const dialogInitialDate = ref<string>()
const dialogInitialHour = ref<number>()
const dialogReadonly = ref(false)

const scopeDialogVisible = ref(false)
let scopeDialogResolver: ((v: UserEventEditScope | null) => void) | null = null

const scopeHintShort = computed(() => {
  if (viewerScope.value === 'all') return t('common.userEventScopeChipAll')
  if (viewerScope.value === 'department') return t('common.userEventScopeChipDepartment')
  return t('common.userEventScopeChipSelf')
})
const scopeHintFull = computed(() => {
  if (viewerScope.value === 'all') return t('common.userEventScopeAll')
  if (viewerScope.value === 'department') return t('common.userEventScopeDepartment')
  return t('common.userEventScopeSelf')
})

const visibleEvents = computed(() => {
  if (listFilter.value === 'mine') return events.value.filter((ev) => ev.is_owner)
  return events.value
})

const dragEv = ref<UserEventItem | null>(null)
const draggingKey = ref('')
const dropTargetDate = ref('')

type PointerDrag = {
  key: string
  ev: UserEventItem
  colDate: string
  startY: number
  deltaMin: number
}
const pointerDrag = ref<PointerDrag | null>(null)

const weekdayHeaders = computed(() => {
  const loc = locale.value
  if (loc === 'en') return ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
  if (loc === 'vi') return ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7']
  if (loc === 'zh') return ['日', '一', '二', '三', '四', '五', '六']
  return ['日', '月', '火', '水', '木', '金', '土']
})

const periodLabel = computed(() => {
  const d = dayjs(anchorDate.value)
  const loc = locale.value
  if (viewMode.value === 'month') {
    if (loc === 'en') return d.format('MMMM YYYY')
    if (loc === 'vi') return `Tháng ${d.format('M/YYYY')}`
    return d.format('YYYY年M月')
  }
  if (viewMode.value === 'week') {
    const start = d.startOf('week')
    const end = start.add(6, 'day')
    if (loc === 'en') return `${start.format('MMM D')} – ${end.format('MMM D, YYYY')}`
    return `${start.format('M/D')} – ${end.format('M/D')}`
  }
  if (loc === 'en') return d.format('dddd, MMMM D, YYYY')
  if (loc === 'vi') return d.format('DD/MM/YYYY')
  return d.format('YYYY年M月D日')
})

const monthPickerFormat = computed(() => {
  const loc = locale.value
  if (loc === 'en') return 'MMMM YYYY'
  if (loc === 'vi') return 'MM/YYYY'
  return 'YYYY年M月'
})

const toolbarMonth = computed({
  get: () => dayjs(anchorDate.value).format('YYYY-MM'),
  set: (ym: string | null) => {
    if (!ym || !/^\d{4}-\d{2}$/.test(ym)) return
    const prevDay = dayjs(anchorDate.value).date()
    const dim = dayjs(`${ym}-01`).daysInMonth()
    const day = Math.min(prevDay, dim)
    anchorDate.value = `${ym}-${String(day).padStart(2, '0')}`
    sidebarMonth.value = ym
  },
})

/** 表示中の月の会社合計稼働日数 */
const monthWorkdayCount = computed(() => {
  const start = dayjs(anchorDate.value).startOf('month')
  const days = start.daysInMonth()
  let n = 0
  for (let d = 1; d <= days; d++) {
    if (isCompanyWorkday(start.date(d).format('YYYY-MM-DD'))) n += 1
  }
  return n
})

const sidebarMonthLabel = computed(() => {
  const d = dayjs(`${sidebarMonth.value}-01`)
  const loc = locale.value
  if (loc === 'en') return d.format('MMM YYYY')
  return d.format('YYYY年M月')
})

const fetchRange = computed(() => {
  const d = dayjs(anchorDate.value)
  if (viewMode.value === 'month') {
    const start = d.startOf('month').startOf('week')
    const end = d.endOf('month').endOf('week')
    return { from: start.format('YYYY-MM-DD'), to: end.format('YYYY-MM-DD') }
  }
  if (viewMode.value === 'week') {
    const start = d.startOf('week')
    return { from: start.format('YYYY-MM-DD'), to: start.add(6, 'day').format('YYYY-MM-DD') }
  }
  return { from: d.format('YYYY-MM-DD'), to: d.format('YYYY-MM-DD') }
})

function eventKey(ev: UserEventItem) {
  return `${ev.id}:${ev.occurrence_date || ev.start_at}`
}

function eventsOnDate(date: string): UserEventItem[] {
  const dayStart = dayjs(date).startOf('day')
  const dayEnd = dayjs(date).endOf('day')
  return visibleEvents.value.filter((ev) => {
    const start = dayjs(ev.start_at)
    const end = dayjs(ev.end_at)
    return start.isBefore(dayEnd) && end.isAfter(dayStart)
  })
}

type MonthCell = { inMonth: boolean; day: number; date: string; events: UserEventItem[] }

function buildMonthCells(ym: string): MonthCell[] {
  const base = dayjs(`${ym}-01`)
  const daysInMonth = base.daysInMonth()
  const startPad = base.day()
  const cells: MonthCell[] = []
  for (let i = 0; i < startPad; i++) cells.push({ inMonth: false, day: 0, date: '', events: [] })
  for (let d = 1; d <= daysInMonth; d++) {
    const date = base.date(d).format('YYYY-MM-DD')
    cells.push({ inMonth: true, day: d, date, events: eventsOnDate(date) })
  }
  while (cells.length % 7 !== 0) cells.push({ inMonth: false, day: 0, date: '', events: [] })
  return cells
}

const monthCells = computed(() => buildMonthCells(dayjs(anchorDate.value).format('YYYY-MM')))
const sidebarCells = computed(() => buildMonthCells(sidebarMonth.value))

const todayStr = computed(() => dayjs().format('YYYY-MM-DD'))
const todayCount = computed(() => userEvents.todayCount.value)
const weekCount = computed(() => userEvents.weekCount.value)
const remindCount = computed(() => userEvents.badgeCount.value)

const upcomingList = computed(() => {
  const now = dayjs()
  return [...visibleEvents.value]
    .filter((ev) => dayjs(ev.end_at).isAfter(now))
    .sort((a, b) => a.start_at.localeCompare(b.start_at))
    .slice(0, 6)
})

type TimeColumn = {
  key: string
  date: string
  day: number
  weekday: string
  isToday: boolean
  allDayEvents: UserEventItem[]
  timedBlocks: { ev: UserEventItem; top: number; height: number }[]
}

const hourLabels = computed(() => HOURS.map((h) => `${String(h).padStart(2, '0')}:00`))

const timeColumns = computed((): TimeColumn[] => {
  const d = dayjs(anchorDate.value)
  const dates =
    viewMode.value === 'day'
      ? [d.format('YYYY-MM-DD')]
      : Array.from({ length: 7 }, (_, i) => d.startOf('week').add(i, 'day').format('YYYY-MM-DD'))
  const wd = weekdayHeaders.value
  const today = todayStr.value

  return dates.map((date) => {
    const dj = dayjs(date)
    const dayEvents = eventsOnDate(date)
    const timedBlocks = dayEvents
      .filter((ev) => !ev.all_day)
      .map((ev) => {
        const start = dayjs(ev.start_at)
        const end = dayjs(ev.end_at)
        const startMin = Math.max(0, start.diff(dj.startOf('day'), 'minute') - 6 * 60)
        const endMin = Math.min(17 * 60, end.diff(dj.startOf('day'), 'minute') - 6 * 60)
        return {
          ev,
          top: (startMin / 60) * HOUR_PX,
          height: Math.max(((endMin - startMin) / 60) * HOUR_PX, 24),
        }
      })

    return {
      key: date,
      date,
      day: dj.date(),
      weekday: wd[dj.day()],
      isToday: date === today,
      allDayEvents: dayEvents.filter((ev) => ev.all_day),
      timedBlocks,
    }
  })
})

const nowLineTop = computed(() => {
  const now = dayjs()
  const min = now.diff(now.startOf('day'), 'minute') - 6 * 60
  if (min < 0 || min > 17 * 60) return null
  return (min / 60) * HOUR_PX
})

function monthCellClass(cell: MonthCell) {
  if (!cell.inMonth) return 'is-outside'
  return { 'is-today': cell.date === todayStr.value, 'has-events': cell.events.length > 0 }
}

function miniDayClass(cell: MonthCell) {
  if (!cell.inMonth) return 'is-outside'
  return {
    'is-today': cell.date === todayStr.value,
    'is-selected': cell.date === anchorDate.value,
    'has-events': cell.events.length > 0,
  }
}

function blockStyle(block: { top: number; height: number; ev: UserEventItem }) {
  const drag = pointerDrag.value
  if (drag && drag.key === eventKey(block.ev)) {
    const extraTop = (drag.deltaMin / 60) * HOUR_PX
    return { top: `${block.top + extraTop}px`, height: `${block.height}px` }
  }
  return { top: `${block.top}px`, height: `${block.height}px` }
}

async function loadEvents() {
  loading.value = true
  try {
    const { from, to } = fetchRange.value
    const [res] = await Promise.all([
      getUserEvents(from, to),
      loadWorkCalendar(from, to),
    ])
    events.value = res.list ?? []
    viewerScope.value = res.viewer_scope || 'department'
    void userEvents.refreshUpcoming()
  } catch {
    ElMessage.error(t('common.userEventLoadFailed'))
  } finally {
    loading.value = false
  }
}

async function loadWorkCalendar(from: string, to: string) {
  try {
    const monthStart = dayjs(anchorDate.value).startOf('month').format('YYYY-MM-DD')
    const monthEnd = dayjs(anchorDate.value).endOf('month').format('YYYY-MM-DD')
    const start_date = from < monthStart ? from : monthStart
    const end_date = to > monthEnd ? to : monthEnd
    const res = await fetchCompanyWorkCalendar({ start_date, end_date })
    const map = new Map<string, CompanyWorkCalendarItem>()
    for (const item of res.data?.items ?? []) {
      map.set(item.calendar_date, item)
    }
    workCalendarByDate.value = map
  } catch {
    workCalendarByDate.value = new Map()
  }
}

/** 会社稼働カレンダーと同じ規則：例外登録があればそれに従い、なければ月〜金=稼働 */
function isCompanyWorkday(date: string): boolean {
  if (!date) return false
  const entry = workCalendarByDate.value.get(date)
  if (entry) return !!entry.is_scheduled
  const dow = dayjs(date).day()
  return dow !== 0 && dow !== 6
}

function goToday() {
  anchorDate.value = todayStr.value
  sidebarMonth.value = dayjs().format('YYYY-MM')
}

function pickDate(date: string) {
  anchorDate.value = date
  sidebarMonth.value = date.slice(0, 7)
}

function shiftPeriod(delta: number) {
  const d = dayjs(anchorDate.value)
  if (viewMode.value === 'month') anchorDate.value = d.add(delta, 'month').format('YYYY-MM-DD')
  else if (viewMode.value === 'week') anchorDate.value = d.add(delta * 7, 'day').format('YYYY-MM-DD')
  else anchorDate.value = d.add(delta, 'day').format('YYYY-MM-DD')
  sidebarMonth.value = anchorDate.value.slice(0, 7)
}

function shiftSidebarMonth(delta: number) {
  sidebarMonth.value = dayjs(`${sidebarMonth.value}-01`).add(delta, 'month').format('YYYY-MM')
}

function openCreate(date?: string, hour?: number) {
  editingEvent.value = null
  dialogReadonly.value = false
  dialogInitialDate.value = date || anchorDate.value
  dialogInitialHour.value = hour
  dialogVisible.value = true
}

function openEdit(ev: UserEventItem) {
  if (pointerDrag.value) return
  if (Date.now() < suppressClickUntil.value) return
  editingEvent.value = ev
  dialogReadonly.value = !ev.is_owner
  dialogInitialDate.value = undefined
  dialogInitialHour.value = undefined
  dialogVisible.value = true
}

function askEditScope(ev: UserEventItem): Promise<UserEventEditScope | null> {
  if (!isRecurringOccurrence(ev)) return Promise.resolve('all')
  return new Promise((resolve) => {
    scopeDialogResolver = resolve
    scopeDialogVisible.value = true
  })
}

function resolveScopeDialog(scope: UserEventEditScope) {
  const resolver = scopeDialogResolver
  scopeDialogResolver = null
  scopeDialogVisible.value = false
  resolver?.(scope)
}

function onScopeDialogClosed() {
  if (!scopeDialogResolver) return
  const resolver = scopeDialogResolver
  scopeDialogResolver = null
  resolver(null)
}

function onMonthCellClick(cell: MonthCell) {
  if (!cell.inMonth || dragEv.value) return
  pickDate(cell.date)
  viewMode.value = 'day'
}

function onTimeColClick(col: TimeColumn, e: MouseEvent) {
  if (pointerDrag.value) return
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
  const y = e.clientY - rect.top
  const hour = 6 + Math.floor(y / HOUR_PX)
  openCreate(col.date, Math.min(Math.max(hour, 6), 22))
}

function formatEventTime(ev: UserEventItem) {
  return dayjs(ev.start_at).format('HH:mm')
}

function formatEventRange(ev: UserEventItem) {
  return `${dayjs(ev.start_at).format('HH:mm')} – ${dayjs(ev.end_at).format('HH:mm')}`
}

function formatUpcoming(ev: UserEventItem) {
  const start = dayjs(ev.start_at)
  if (ev.all_day) return start.format('M/D') + ' · ' + t('common.userMemoAllDay')
  return start.format('M/D HH:mm')
}

function buildReschedulePayload(ev: UserEventItem, start: dayjs.Dayjs, end: dayjs.Dayjs) {
  if (ev.all_day) {
    return { start_at: start.format('YYYY-MM-DD'), end_at: end.format('YYYY-MM-DD') }
  }
  return {
    start_at: start.format('YYYY-MM-DD HH:mm'),
    end_at: end.format('YYYY-MM-DD HH:mm'),
  }
}

async function applyReschedule(ev: UserEventItem, payload: { start_at: string; end_at: string }) {
  const scope = await askEditScope(ev)
  if (!scope) return
  try {
    await rescheduleUserEvent(ev.id, {
      ...payload,
      edit_scope: scope,
      occurrence_date: ev.occurrence_date,
    })
    ElMessage.success(t('common.userEventRescheduleOk'))
    await loadEvents()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || t('common.userEventSaveFailed'))
  }
}

async function moveEventToDate(ev: UserEventItem, targetDate: string) {
  const start = dayjs(ev.start_at)
  const end = dayjs(ev.end_at)
  const delta = dayjs(targetDate).diff(start.startOf('day'), 'day')
  if (delta === 0) return
  await applyReschedule(ev, buildReschedulePayload(ev, start.add(delta, 'day'), end.add(delta, 'day')))
}

function onMonthDragStart(ev: UserEventItem, e: DragEvent) {
  if (!ev.is_owner) return
  dragEv.value = ev
  draggingKey.value = eventKey(ev)
  e.dataTransfer?.setData('text/plain', eventKey(ev))
  e.dataTransfer!.effectAllowed = 'move'
}

function onMonthDragOver(cell: MonthCell) {
  if (!cell.inMonth || !dragEv.value) return
  dropTargetDate.value = cell.date
}

function onMonthDragLeave(cell: MonthCell) {
  if (dropTargetDate.value === cell.date) dropTargetDate.value = ''
}

async function onMonthDrop(cell: MonthCell) {
  const ev = dragEv.value
  onDragEnd()
  suppressClickUntil.value = Date.now() + 400
  if (!ev || !cell.inMonth) return
  await moveEventToDate(ev, cell.date)
}

async function onAllDayDrop(col: TimeColumn) {
  const ev = dragEv.value
  onDragEnd()
  suppressClickUntil.value = Date.now() + 400
  if (!ev) return
  await moveEventToDate(ev, col.date)
}

async function onTimedDrop(col: TimeColumn, e: DragEvent) {
  const ev = dragEv.value
  onDragEnd()
  suppressClickUntil.value = Date.now() + 400
  if (!ev || ev.all_day) {
    if (ev) await moveEventToDate(ev, col.date)
    return
  }
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
  const y = e.clientY - rect.top
  const minutes = Math.round((y / HOUR_PX) * 60 / SNAP_MIN) * SNAP_MIN
  const start = dayjs(col.date).startOf('day').add(6 * 60 + minutes, 'minute')
  const end = start.add(eventDurationMinutes(ev), 'minute')
  await applyReschedule(ev, buildReschedulePayload(ev, start, end))
}

function onDragEnd() {
  dragEv.value = null
  draggingKey.value = ''
  dropTargetDate.value = ''
}

function startPointerDrag(ev: UserEventItem, colDate: string, e: MouseEvent) {
  if (!ev.is_owner) return
  pointerDrag.value = {
    key: eventKey(ev),
    ev,
    colDate,
    startY: e.clientY,
    deltaMin: 0,
  }
  document.addEventListener('mousemove', onPointerMove)
  document.addEventListener('mouseup', onPointerUp)
}

function onPointerMove(e: MouseEvent) {
  const drag = pointerDrag.value
  if (!drag) return
  const deltaPx = e.clientY - drag.startY
  const rawMin = Math.round(((deltaPx / HOUR_PX) * 60) / SNAP_MIN) * SNAP_MIN
  drag.deltaMin = rawMin
}

async function onPointerUp() {
  document.removeEventListener('mousemove', onPointerMove)
  document.removeEventListener('mouseup', onPointerUp)
  const drag = pointerDrag.value
  pointerDrag.value = null
  if (!drag || drag.deltaMin === 0) return

  suppressClickUntil.value = Date.now() + 400
  const ev = drag.ev
  const start = dayjs(ev.start_at).add(drag.deltaMin, 'minute')
  const end = dayjs(ev.end_at).add(drag.deltaMin, 'minute')
  await applyReschedule(ev, buildReschedulePayload(ev, start, end))
}

async function onFormSubmit(payload: UserEventCreatePayload) {
  submitting.value = true
  try {
    if (editingEvent.value) {
      const scope = await askEditScope(editingEvent.value)
      if (!scope) return
      await updateUserEvent(editingEvent.value.id, {
        ...payload,
        edit_scope: scope,
        occurrence_date: editingEvent.value.occurrence_date,
      })
      ElMessage.success(t('common.userEventUpdateOk'))
    } else {
      await createUserEvent(payload)
      ElMessage.success(t('common.userEventCreateOk'))
    }
    dialogVisible.value = false
    await loadEvents()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || t('common.userEventSaveFailed'))
  } finally {
    submitting.value = false
  }
}

async function confirmDelete() {
  if (!editingEvent.value) return
  const ev = editingEvent.value
  let scope: UserEventEditScope = 'all'
  if (isRecurringOccurrence(ev)) {
    const picked = await askEditScope(ev)
    if (!picked) return
    scope = picked
  } else {
    try {
      await ElMessageBox.confirm(t('common.userEventDeleteConfirm'), t('common.confirm'), {
        type: 'warning',
        confirmButtonText: t('common.userMemoDelete'),
        cancelButtonText: t('common.cancel'),
      })
    } catch {
      return
    }
  }
  deleting.value = true
  try {
    await deleteUserEvent(ev.id, {
      edit_scope: scope,
      occurrence_date: ev.occurrence_date,
    })
    ElMessage.success(t('common.userEventDeleteOk'))
    dialogVisible.value = false
    await loadEvents()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || t('common.userEventDeleteFailed'))
  } finally {
    deleting.value = false
  }
}

watch([viewMode, anchorDate], () => loadEvents())
watch(anchorDate, (v) => {
  sidebarMonth.value = v.slice(0, 7)
})

onMounted(() => {
  loadEvents()
  if (timeScrollRef.value && nowLineTop.value != null) {
    timeScrollRef.value.scrollTop = Math.max(0, nowLineTop.value - 120)
  }
})

onUnmounted(() => {
  document.removeEventListener('mousemove', onPointerMove)
  document.removeEventListener('mouseup', onPointerUp)
})
</script>

<style scoped>
.uevents-page {
  --ue-ink: #0f172a;
  --ue-muted: #64748b;
  --ue-accent: #0d9488;
  --ue-accent-deep: #0f766e;
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: calc(100vh - 100px);
  padding: 6px 4px 22px;
  overflow: hidden;
  background:
    radial-gradient(1200px 480px at 12% -10%, rgba(45, 212, 191, 0.14), transparent 55%),
    radial-gradient(900px 420px at 92% 8%, rgba(14, 165, 233, 0.12), transparent 50%),
    radial-gradient(700px 360px at 70% 100%, rgba(251, 191, 36, 0.08), transparent 45%);
}

.uevents-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(72px);
  opacity: 0.35;
  pointer-events: none;
  z-index: 0;
}

.uevents-orb--indigo {
  width: 260px;
  height: 260px;
  background: #5eead4;
  top: -90px;
  right: 8%;
}

.uevents-orb--violet {
  width: 200px;
  height: 200px;
  background: #7dd3fc;
  bottom: 8%;
  left: -50px;
}

.uevents-orb--cyan {
  width: 160px;
  height: 160px;
  background: #fde68a;
  top: 42%;
  right: -40px;
}

.uevents-hero,
.uevents-shell {
  position: relative;
  z-index: 1;
}

.uevents-hero {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-start;
  gap: 20px;
  padding: 10px 14px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.94) 0%, rgba(240, 253, 250, 0.9) 55%, rgba(224, 242, 254, 0.88) 100%);
  border: 1px solid rgba(153, 246, 228, 0.55);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.8) inset,
    0 8px 24px rgba(15, 118, 110, 0.07);
  backdrop-filter: blur(14px);
}

.uevents-hero__left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.uevents-hero__icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(145deg, #2dd4bf, #0d9488 55%, #0369a1);
  color: #fff;
  box-shadow: 0 6px 16px rgba(13, 148, 136, 0.28);
  flex-shrink: 0;
}

.uevents-hero__eyebrow {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--ue-accent-deep);
  text-transform: uppercase;
  line-height: 1.2;
}

.uevents-hero__title {
  margin: 1px 0 0;
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--ue-ink);
  letter-spacing: -0.03em;
  line-height: 1.25;
}

.uevents-hero__sub {
  margin: 5px 0 0;
  font-size: 12px;
  color: var(--ue-muted);
  line-height: 1.45;
}

.uevents-hero__stats {
  display: flex;
  gap: 8px;
}

.uevents-stat {
  min-width: 64px;
  padding: 6px 12px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(226, 232, 240, 0.9);
  text-align: center;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
}

.uevents-stat--accent {
  background: linear-gradient(145deg, #ecfeff, #ccfbf1);
  border-color: #99f6e4;
}

.uevents-stat--warn {
  background: linear-gradient(145deg, #fffbeb, #fef3c7);
  border-color: #fde68a;
}

.uevents-stat__num {
  display: block;
  font-size: 1.1rem;
  font-weight: 800;
  color: var(--ue-ink);
  font-variant-numeric: tabular-nums;
  line-height: 1.2;
}

.uevents-stat--accent .uevents-stat__num { color: #0f766e; }
.uevents-stat--warn .uevents-stat__num { color: #b45309; }

.uevents-stat__label {
  font-size: 10px;
  color: var(--ue-muted);
  font-weight: 600;
}

.uevents-shell {
  display: grid;
  grid-template-columns: 248px 1fr;
  gap: 14px;
  min-height: 0;
  flex: 1;
}

.uevents-sidebar {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(226, 232, 240, 0.95);
  box-shadow: 0 8px 28px rgba(15, 23, 42, 0.05);
  backdrop-filter: blur(12px);
}

.uevents-sidebar__create {
  width: 100%;
  height: 40px;
  border-radius: 12px;
  font-weight: 700;
  border: none;
  background: linear-gradient(135deg, #14b8a6, #0d9488 50%, #0369a1) !important;
  box-shadow: 0 8px 18px rgba(13, 148, 136, 0.28);
}

.uevents-mini__nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.uevents-mini__label {
  font-size: 13px;
  font-weight: 750;
  color: #134e4a;
}

.uevents-mini__btn {
  width: 28px;
  height: 28px;
  border: 1px solid #e2e8f0;
  border-radius: 9px;
  background: #fff;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  transition: all 0.15s ease;
}

.uevents-mini__btn:hover {
  border-color: #99f6e4;
  color: #0f766e;
  background: #f0fdfa;
}

.uevents-mini__weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  margin-bottom: 4px;
}

.uevents-mini__wd {
  text-align: center;
  font-size: 10px;
  font-weight: 700;
  color: #94a3b8;
}

.uevents-mini__wd:first-child { color: #f43f5e; }
.uevents-mini__wd:last-child { color: #0284c7; }

.uevents-mini__grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 3px;
}

.uevents-mini__day {
  aspect-ratio: 1;
  border: none;
  border-radius: 9px;
  background: transparent;
  font-size: 11px;
  font-weight: 650;
  color: #334155;
  cursor: pointer;
  position: relative;
  transition: background 0.12s ease, color 0.12s ease;
}

.uevents-mini__day.is-outside {
  visibility: hidden;
  pointer-events: none;
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}

.uevents-mini__day:not(.is-outside):hover {
  background: #f0fdfa;
  color: #0f766e;
}

.uevents-mini__day.is-today {
  background: linear-gradient(145deg, #14b8a6, #0d9488);
  color: #fff;
  box-shadow: 0 4px 12px rgba(13, 148, 136, 0.3);
}

.uevents-mini__day.is-selected:not(.is-today) {
  background: #ccfbf1;
  color: #115e59;
}

.uevents-mini__day.has-events:not(.is-today)::after {
  content: '';
  position: absolute;
  bottom: 3px;
  left: 50%;
  transform: translateX(-50%);
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #0d9488;
}

.uevents-upcoming {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

.uevents-upcoming__head {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 750;
  color: #64748b;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.uevents-upcoming__empty {
  font-size: 12px;
  color: #94a3b8;
  padding: 10px 0;
}

.uevents-upcoming__item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  width: 100%;
  border: 1px solid transparent;
  background: transparent;
  padding: 9px 10px;
  border-radius: 12px;
  cursor: pointer;
  text-align: left;
  transition: all 0.15s ease;
}

.uevents-upcoming__item:hover {
  background: #f8fafc;
  border-color: #e2e8f0;
}

.uevents-upcoming__dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  margin-top: 5px;
  flex-shrink: 0;
  box-shadow: 0 0 0 3px rgba(148, 163, 184, 0.12);
}

.uevents-upcoming__dot.is-blue { background: #2563eb; }
.uevents-upcoming__dot.is-green { background: #16a34a; }
.uevents-upcoming__dot.is-amber { background: #d97706; }
.uevents-upcoming__dot.is-rose { background: #e11d48; }
.uevents-upcoming__dot.is-slate { background: #475569; }
.uevents-upcoming__dot.is-violet { background: #7c3aed; }
.uevents-upcoming__dot.is-cyan { background: #0891b2; }

.uevents-upcoming__text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.uevents-upcoming__title {
  font-size: 12px;
  font-weight: 650;
  color: var(--ue-ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.uevents-upcoming__time {
  font-size: 10px;
  color: #94a3b8;
}

.uevents-sidebar__hint {
  margin: 0;
  font-size: 10px;
  color: #94a3b8;
  line-height: 1.45;
  padding-top: 4px;
  border-top: 1px dashed #e2e8f0;
}

.uevents-main {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
}

.uevents-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(226, 232, 240, 0.95);
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
}

.uevents-toolbar__nav {
  display: flex;
  align-items: center;
  gap: 6px;
}

.uevents-toolbar__month-picker {
  width: auto !important;
}

.uevents-toolbar__month-picker :deep(.el-input__wrapper) {
  box-shadow: none !important;
  background: transparent;
  padding: 0 4px;
  cursor: pointer;
}

.uevents-toolbar__month-picker :deep(.el-input__wrapper:hover),
.uevents-toolbar__month-picker :deep(.el-input__wrapper.is-focus) {
  box-shadow: none !important;
  background: #f0fdfa;
  border-radius: 8px;
}

.uevents-toolbar__month-picker :deep(.el-input__prefix) {
  display: none;
}

.uevents-toolbar__month-picker :deep(.el-input__inner) {
  width: 7.5em;
  padding: 0;
  text-align: center;
  font-size: 13px;
  font-weight: 750;
  color: #0f172a;
  letter-spacing: -0.02em;
  cursor: pointer;
  height: 32px;
  line-height: 32px;
}

.uevents-toolbar__month-picker :deep(.el-input__suffix) {
  display: none;
}

.uevents-toolbar__workday-total {
  display: inline-flex;
  align-items: center;
  height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  color: #0f766e;
  background: rgba(204, 251, 241, 0.9);
  border: 1px solid rgba(153, 246, 228, 0.95);
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}

.uevents-toolbar__nav-btn {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #fff;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #475569;
  transition: all 0.15s ease;
}

.uevents-toolbar__nav-btn:hover {
  border-color: #99f6e4;
  color: #0f766e;
  background: #f0fdfa;
}

.uevents-view-switch {
  margin-left: auto;
}

.uevents-filter-switch {
  margin-left: 0;
}

.uevents-view-switch :deep(.el-radio-button__inner),
.uevents-filter-switch :deep(.el-radio-button__inner) {
  padding: 7px 12px;
  font-weight: 650;
}

.uevents-view-switch :deep(.el-radio-button:first-child .el-radio-button__inner),
.uevents-filter-switch :deep(.el-radio-button:first-child .el-radio-button__inner) {
  border-radius: 10px 0 0 10px;
}

.uevents-view-switch :deep(.el-radio-button:last-child .el-radio-button__inner),
.uevents-filter-switch :deep(.el-radio-button:last-child .el-radio-button__inner) {
  border-radius: 0 10px 10px 0;
}

.uevents-view-switch :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner),
.uevents-filter-switch :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(135deg, #14b8a6, #0d9488);
  border-color: #0d9488;
  box-shadow: 0 4px 12px rgba(13, 148, 136, 0.25);
}

.uevents-scope-chip {
  display: inline-flex;
  align-items: center;
  height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  color: #0f766e;
  background: rgba(204, 251, 241, 0.85);
  border: 1px solid rgba(153, 246, 228, 0.9);
  white-space: nowrap;
}

.uevents-scope-dialog__hint {
  margin: 0 0 16px;
  font-size: 13px;
  color: #64748b;
  line-height: 1.5;
}

.uevents-scope-dialog__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}

.uevents-chip__owner {
  opacity: 0.95;
  font-weight: 750;
  margin-right: 2px;
  flex-shrink: 0;
}

.uevents-body {
  flex: 1;
  border-radius: 18px;
  border: 1px solid rgba(226, 232, 240, 0.95);
  background: rgba(255, 255, 255, 0.55);
  overflow: hidden;
  box-shadow: 0 10px 32px rgba(15, 23, 42, 0.05);
}

.uevents-month {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: transparent;
}

.uevents-month__weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 6px;
  padding: 10px 10px 6px;
  background: transparent;
  border-bottom: none;
}

.uevents-month__wd {
  padding: 8px 4px;
  text-align: center;
  font-size: 11px;
  font-weight: 750;
  color: #64748b;
  letter-spacing: 0.04em;
}

.uevents-month__wd.is-sun { color: #e11d48; }
.uevents-month__wd.is-sat { color: #0284c7; }

.uevents-month__grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 6px;
  flex: 1;
  min-height: 540px;
  padding: 0 10px 10px;
  background: transparent;
}

/* 当月日期单元格 */
.uevents-month__cell {
  min-height: 104px;
  border: none;
  border-radius: 14px;
  padding: 7px;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.8) inset, 0 1px 3px rgba(15, 23, 42, 0.04);
  outline: 1px solid rgba(226, 232, 240, 0.85);
  transition: transform 0.12s ease, background 0.12s ease, box-shadow 0.12s ease, outline-color 0.12s ease;
}

.uevents-month__cell:hover {
  background: #fff;
  outline-color: #99f6e4;
  box-shadow: 0 8px 20px rgba(13, 148, 136, 0.08);
  transform: translateY(-1px);
}

/* 非当月空白格：无边框、无背景 */
.uevents-month__cell.is-outside {
  background: transparent !important;
  border: none !important;
  outline: none !important;
  box-shadow: none !important;
  cursor: default;
  pointer-events: none;
  min-height: 0;
  padding: 0;
  transform: none !important;
}

.uevents-month__cell.is-outside:hover {
  background: transparent !important;
  box-shadow: none !important;
  transform: none !important;
}

.uevents-month__cell.is-sun-col:not(.is-outside) {
  background: linear-gradient(180deg, rgba(255, 241, 242, 0.8) 0%, rgba(255, 255, 255, 0.96) 42%);
}

.uevents-month__cell.is-sat-col:not(.is-outside) {
  background: linear-gradient(180deg, rgba(240, 249, 255, 0.85) 0%, rgba(255, 255, 255, 0.96) 42%);
}

.uevents-month__cell.is-today {
  background: linear-gradient(180deg, #ecfeff 0%, #ffffff 55%) !important;
  outline-color: #5eead4;
  box-shadow: 0 0 0 2px rgba(45, 212, 191, 0.25), 0 8px 22px rgba(13, 148, 136, 0.1);
}

.uevents-month__cell.is-drop-target:not(.is-outside) {
  background: #f0fdfa !important;
  outline: 2px solid #14b8a6;
  box-shadow: 0 0 0 4px rgba(45, 212, 191, 0.18);
}

.uevents-month__cell-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 5px;
  gap: 4px;
}

.uevents-month__day-wrap {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  min-width: 0;
}

.uevents-month__day {
  font-size: 12px;
  font-weight: 750;
  color: #334155;
  width: 26px;
  height: 26px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 9px;
  font-variant-numeric: tabular-nums;
  flex-shrink: 0;
}

.uevents-month__workday {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: #0f766e;
  background: rgba(204, 251, 241, 0.85);
  border: 1px solid rgba(153, 246, 228, 0.9);
  border-radius: 999px;
  padding: 1px 5px;
  line-height: 1.35;
  white-space: nowrap;
}

.is-sun-col .uevents-month__day { color: #e11d48; }
.is-sat-col .uevents-month__day { color: #0284c7; }

.is-today .uevents-month__day {
  background: linear-gradient(145deg, #14b8a6, #0d9488);
  color: #fff !important;
  box-shadow: 0 4px 12px rgba(13, 148, 136, 0.35);
}

.uevents-month__add {
  opacity: 0;
  width: 22px;
  height: 22px;
  border: none;
  border-radius: 7px;
  background: #f0fdfa;
  color: #0f766e;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.uevents-month__cell:hover .uevents-month__add {
  opacity: 1;
}

.uevents-month__add:hover {
  background: #ccfbf1;
}

.uevents-month__events {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.uevents-month__more {
  font-size: 10px;
  color: #0f766e;
  font-weight: 700;
  padding-left: 4px;
}

.uevents-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  width: 100%;
  text-align: left;
  border: none;
  border-radius: 7px;
  padding: 3px 7px 3px 8px;
  font-size: 11px;
  line-height: 1.35;
  cursor: grab;
  overflow: hidden;
  white-space: nowrap;
  border-left: 3px solid transparent;
  transition: transform 0.12s ease, opacity 0.12s ease;
}

.uevents-chip__title {
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}

.uevents-chip:active { cursor: grabbing; }
.uevents-chip.is-dragging { opacity: 0.4; transform: scale(0.98); }
.uevents-chip--block { margin-bottom: 2px; }

.uevents-chip__time {
  font-variant-numeric: tabular-nums;
  flex-shrink: 0;
  font-weight: 700;
  opacity: 0.85;
}

.uevents-chip__bell,
.uevents-chip__repeat {
  flex-shrink: 0;
  opacity: 0.85;
}

.uevents-chip--blue { background: #eff6ff; color: #1d4ed8; border-left-color: #3b82f6; }
.uevents-chip--green { background: #f0fdf4; color: #15803d; border-left-color: #22c55e; }
.uevents-chip--amber { background: #fffbeb; color: #b45309; border-left-color: #f59e0b; }
.uevents-chip--rose { background: #fff1f2; color: #be123c; border-left-color: #f43f5e; }
.uevents-chip--slate { background: #f8fafc; color: #334155; border-left-color: #64748b; }
.uevents-chip--violet { background: #f5f3ff; color: #6d28d9; border-left-color: #8b5cf6; }
.uevents-chip--cyan { background: #ecfeff; color: #0e7490; border-left-color: #06b6d4; }

.uevents-chip.is-private {
  border-left-style: dashed;
}

.uevents-time {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.uevents-time__allday {
  display: grid;
  grid-template-columns: 56px repeat(var(--uevents-cols, 7), 1fr);
  border-bottom: 1px solid #e2e8f0;
  min-height: 56px;
  background: rgba(248, 250, 252, 0.65);
}

.uevents-time__corner {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 9px;
  font-weight: 750;
  color: #94a3b8;
  border-right: 1px solid #e2e8f0;
  text-transform: uppercase;
}

.uevents-time__allday-col {
  border-right: 1px solid #f1f5f9;
  padding: 6px;
  min-width: 0;
}

.uevents-time__allday-col.is-today,
.uevents-time__col.is-today {
  background: rgba(240, 253, 250, 0.55);
}

.uevents-time__allday-col.is-drop-target,
.uevents-time__col.is-drop-target {
  box-shadow: inset 0 0 0 2px #14b8a6;
}

.uevents-time__col-head {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  margin-bottom: 4px;
}

.uevents-time__col-wd {
  font-size: 10px;
  color: #94a3b8;
  font-weight: 700;
}

.uevents-time__col-day-row {
  display: inline-flex;
  align-items: center;
  gap: 3px;
}

.uevents-time__col-day {
  font-size: 14px;
  font-weight: 750;
  color: #334155;
}

.uevents-time__workday {
  font-size: 8px;
  font-weight: 700;
  color: #0f766e;
  background: rgba(204, 251, 241, 0.9);
  border-radius: 999px;
  padding: 1px 4px;
  line-height: 1.3;
  white-space: nowrap;
}

.uevents-time__col-day.is-today {
  width: 28px;
  height: 28px;
  border-radius: 10px;
  background: linear-gradient(145deg, #14b8a6, #0d9488);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(13, 148, 136, 0.3);
}

.uevents-time__scroll {
  display: flex;
  flex: 1;
  overflow: auto;
  max-height: calc(100vh - 320px);
}

.uevents-time__hours {
  width: 56px;
  flex-shrink: 0;
  border-right: 1px solid #e2e8f0;
  background: rgba(248, 250, 252, 0.7);
}

.uevents-time__hour {
  height: 52px;
  font-size: 10px;
  color: #94a3b8;
  text-align: right;
  padding: 4px 8px 0 0;
  font-variant-numeric: tabular-nums;
  font-weight: 600;
}

.uevents-time__cols {
  display: grid;
  grid-template-columns: repeat(var(--uevents-cols, 7), 1fr);
  flex: 1;
  min-width: 0;
}

.uevents-time__col {
  position: relative;
  border-right: 1px solid #f1f5f9;
  min-height: calc(17 * 52px);
}

.uevents-time__slot {
  height: 52px;
  border-bottom: 1px solid #f1f5f9;
}

.uevents-now-line {
  position: absolute;
  left: 0;
  right: 0;
  height: 2px;
  background: #f43f5e;
  z-index: 2;
  pointer-events: none;
}

.uevents-now-line::before {
  content: '';
  position: absolute;
  left: -4px;
  top: -4px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #f43f5e;
  box-shadow: 0 0 0 3px rgba(244, 63, 94, 0.2);
}

.uevents-block {
  position: absolute;
  left: 3px;
  right: 3px;
  border: none;
  border-radius: 10px;
  padding: 6px 8px;
  text-align: left;
  color: #fff;
  cursor: grab;
  overflow: hidden;
  z-index: 1;
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.14);
  transition: box-shadow 0.15s ease, transform 0.12s ease;
}

.uevents-block:hover {
  box-shadow: 0 10px 22px rgba(15, 23, 42, 0.2);
  z-index: 3;
  transform: translateY(-1px);
}

.uevents-block.is-dragging {
  cursor: grabbing;
  opacity: 0.88;
  z-index: 5;
  box-shadow: 0 14px 28px rgba(13, 148, 136, 0.28);
}

.uevents-block__title {
  display: block;
  font-size: 11px;
  font-weight: 750;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.uevents-block__time {
  display: block;
  font-size: 10px;
  opacity: 0.92;
  font-variant-numeric: tabular-nums;
}

.uevents-block--blue { background: linear-gradient(145deg, #60a5fa, #2563eb); }
.uevents-block--green { background: linear-gradient(145deg, #4ade80, #16a34a); }
.uevents-block--amber { background: linear-gradient(145deg, #fbbf24, #d97706); }
.uevents-block--rose { background: linear-gradient(145deg, #fb7185, #e11d48); }
.uevents-block--slate { background: linear-gradient(145deg, #94a3b8, #475569); }
.uevents-block--violet { background: linear-gradient(145deg, #a78bfa, #7c3aed); }
.uevents-block--cyan { background: linear-gradient(145deg, #22d3ee, #0891b2); }

@media (max-width: 960px) {
  .uevents-shell {
    grid-template-columns: 1fr;
  }

  .uevents-sidebar {
    order: 2;
  }

  .uevents-hero__stats {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
