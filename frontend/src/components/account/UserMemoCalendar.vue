<template>
  <div class="umemo-cal">
    <div class="umemo-cal__nav">
      <button
        type="button"
        class="umemo-cal__nav-btn"
        :aria-label="t('common.userMemoPrevMonth')"
        @click="emit('shift-month', -1)"
      >
        <el-icon :size="14"><ArrowLeft /></el-icon>
      </button>
      <span class="umemo-cal__label">{{ monthLabel }}</span>
      <button
        type="button"
        class="umemo-cal__nav-btn"
        :aria-label="t('common.userMemoNextMonth')"
        @click="emit('shift-month', 1)"
      >
        <el-icon :size="14"><ArrowRight /></el-icon>
      </button>
      <button type="button" class="umemo-cal__today" @click="goToday">
        {{ t('common.userMemoToday') }}
      </button>
    </div>

    <div class="umemo-cal__weekdays">
      <span
        v-for="(w, idx) in weekdayHeaders"
        :key="`${w}-${idx}`"
        class="umemo-cal__wd"
        :class="{ 'is-sun': idx === 0, 'is-sat': idx === 6 }"
      >{{ w }}</span>
    </div>

    <div class="umemo-cal__grid">
      <button
        v-for="(cell, idx) in calendarCells"
        :key="idx"
        type="button"
        class="umemo-cal__cell"
        :class="cellClass(cell)"
        :disabled="!cell.inMonth"
        @click="cell.inMonth && emit('select-date', cell.date)"
      >
        <template v-if="cell.inMonth">
          <span class="umemo-cal__num">{{ cell.day }}</span>
          <span v-if="cell.dots.length" class="umemo-cal__dots">
            <i
              v-for="(dot, dotIdx) in cell.dots.slice(0, 3)"
              :key="dotIdx"
              class="umemo-cal__dot"
              :class="`umemo-cal__dot--${dot}`"
            />
          </span>
        </template>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import dayjs from 'dayjs'
import type { UserMemoItem } from '@/api/auth/memos'

const props = defineProps<{
  monthValue: string
  selectedDate: string
  datesWithMemos: Map<string, UserMemoItem[]>
}>()

const emit = defineEmits<{
  'select-date': [date: string]
  'shift-month': [delta: number]
}>()

const { t, locale } = useI18n()

type CalCell = {
  inMonth: boolean
  day: number
  date: string
  dots: string[]
}

const weekdayHeaders = computed(() => {
  const loc = locale.value
  if (loc === 'en') return ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
  if (loc === 'vi') return ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7']
  return ['日', '月', '火', '水', '木', '金', '土']
})

const monthLabel = computed(() => {
  const d = dayjs(`${props.monthValue}-01`)
  const loc = locale.value
  if (loc === 'en') return d.format('MMMM YYYY')
  if (loc === 'ja') return d.format('YYYY年M月')
  if (loc === 'vi') return `Tháng ${d.format('M/YYYY')}`
  return d.format('YYYY年M月')
})

const calendarCells = computed((): CalCell[] => {
  const ym = props.monthValue
  if (!ym || !/^\d{4}-\d{2}$/.test(ym)) return []
  const base = dayjs(`${ym}-01`)
  const daysInMonth = base.daysInMonth()
  const startPad = base.day()
  const cells: CalCell[] = []

  for (let i = 0; i < startPad; i++) {
    cells.push({ inMonth: false, day: 0, date: '', dots: [] })
  }
  for (let d = 1; d <= daysInMonth; d++) {
    const date = base.date(d).format('YYYY-MM-DD')
    const memos = props.datesWithMemos.get(date) ?? []
    const dots = [...new Set(memos.map((m) => m.color || 'blue'))]
    cells.push({ inMonth: true, day: d, date, dots })
  }
  while (cells.length % 7 !== 0) {
    cells.push({ inMonth: false, day: 0, date: '', dots: [] })
  }
  return cells
})

function cellClass(cell: CalCell) {
  if (!cell.inMonth) return 'is-outside'
  const today = dayjs().format('YYYY-MM-DD')
  return {
    'is-today': cell.date === today,
    'is-selected': cell.date === props.selectedDate,
    'has-memo': cell.dots.length > 0,
  }
}

function goToday() {
  const today = dayjs().format('YYYY-MM-DD')
  emit('select-date', today)
}
</script>

<style scoped>
.umemo-cal {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.umemo-cal__nav {
  display: flex;
  align-items: center;
  gap: 6px;
}

.umemo-cal__nav-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  border-radius: 8px;
  background: #fff;
  color: #475569;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, transform 0.15s, color 0.15s;
}

.umemo-cal__nav-btn:hover {
  background: #f0fdfa;
  border-color: rgba(13, 148, 136, 0.35);
  color: #0f766e;
  transform: translateY(-1px);
}

.umemo-cal__label {
  flex: 1;
  text-align: center;
  font-weight: 700;
  font-size: 15px;
  letter-spacing: -0.01em;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
}

.umemo-cal__today {
  margin-left: 2px;
  height: 30px;
  padding: 0 12px;
  border: none;
  border-radius: 999px;
  background: linear-gradient(135deg, #0f766e 0%, #14b8a6 100%);
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 4px 10px -4px rgba(13, 148, 136, 0.55);
  transition: transform 0.15s, box-shadow 0.15s, filter 0.15s;
}

.umemo-cal__today:hover {
  transform: translateY(-1px);
  filter: brightness(1.05);
  box-shadow: 0 6px 14px -4px rgba(13, 148, 136, 0.6);
}

.umemo-cal__weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
  padding: 0 2px;
}

.umemo-cal__wd {
  text-align: center;
  font-size: 11px;
  font-weight: 600;
  color: #94a3b8;
  padding: 2px 0 4px;
  letter-spacing: 0.02em;
}

.umemo-cal__wd.is-sun {
  color: #f43f5e;
}

.umemo-cal__wd.is-sat {
  color: #0284c7;
}

.umemo-cal__grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
}

.umemo-cal__cell {
  aspect-ratio: 1;
  min-height: 42px;
  border: 1px solid transparent;
  border-radius: 10px;
  background: transparent;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  padding: 2px;
  transition: background 0.15s, border-color 0.15s, box-shadow 0.15s, transform 0.15s;
}

.umemo-cal__cell:hover:not(:disabled) {
  background: rgba(15, 118, 110, 0.06);
  transform: translateY(-1px);
}

.umemo-cal__cell.is-outside {
  visibility: hidden;
  pointer-events: none;
}

.umemo-cal__cell.is-today .umemo-cal__num {
  color: #0f766e;
  font-weight: 800;
}

.umemo-cal__cell.is-today:not(.is-selected) {
  box-shadow: inset 0 0 0 1.5px rgba(13, 148, 136, 0.45);
}

.umemo-cal__cell.is-selected {
  border-color: transparent;
  background: linear-gradient(145deg, #0f766e 0%, #14b8a6 100%);
  box-shadow: 0 6px 14px -6px rgba(13, 148, 136, 0.55);
}

.umemo-cal__cell.is-selected .umemo-cal__num {
  color: #fff;
  font-weight: 700;
}

.umemo-cal__cell.is-selected .umemo-cal__dot {
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.55);
}

.umemo-cal__num {
  font-size: 13px;
  line-height: 1.2;
  color: #334155;
  font-variant-numeric: tabular-nums;
}

.umemo-cal__dots {
  display: flex;
  gap: 3px;
  height: 5px;
  align-items: center;
}

.umemo-cal__dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  display: block;
}

.umemo-cal__dot--blue { background: #3b82f6; }
.umemo-cal__dot--green { background: #22c55e; }
.umemo-cal__dot--amber { background: #f59e0b; }
.umemo-cal__dot--rose { background: #f43f5e; }
.umemo-cal__dot--slate { background: #64748b; }

.umemo-cal__cell.is-selected .umemo-cal__dot--blue,
.umemo-cal__cell.is-selected .umemo-cal__dot--green,
.umemo-cal__cell.is-selected .umemo-cal__dot--amber,
.umemo-cal__cell.is-selected .umemo-cal__dot--rose,
.umemo-cal__cell.is-selected .umemo-cal__dot--slate {
  background: #fff;
}
</style>
