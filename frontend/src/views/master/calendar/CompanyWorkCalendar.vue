<template>
  <div class="cwc cwc-modern pb-std">
    <header class="cwc-hero pb-hero pb-hero--page">
      <div class="page-header-fx pb-bubbles" aria-hidden="true" />
      <div class="cwc-hero__left">
        <div class="cwc-hero__icon"><el-icon :size="20"><Calendar /></el-icon></div>
        <div class="cwc-hero__text">
          <div class="cwc-hero__eyebrow">マスタ · カレンダー</div>
          <h1 class="cwc-hero__title pb-hero-title">会社稼働カレンダー</h1>
        </div>
        <span class="cwc-chip cwc-chip--muted cwc-hero__month">{{ monthLabel }}</span>
      </div>
      <div class="cwc-hero__stats" @mousemove="handleStatTilt" @mouseleave="resetStatTilt">
        <div class="stat-card stat-work">
          <span class="stat-num">{{ summary.scheduled }}<small>/{{ summary.total }}</small></span>
          <span class="stat-lbl">稼働日</span>
        </div>
        <div class="stat-card stat-off">
          <span class="stat-num">{{ offDayCount }}</span>
          <span class="stat-lbl">非稼働</span>
        </div>
        <div class="stat-card stat-reg">
          <span class="stat-num">{{ items.length }}</span>
          <span class="stat-lbl">登録</span>
        </div>
        <div class="stat-card stat-rate">
          <span class="stat-num">{{ workRate }}<small>%</small></span>
          <span class="stat-lbl">稼働率</span>
        </div>
      </div>
      <el-button :icon="Refresh" :loading="loading" size="small" round class="cwc-hero__refresh" @click="loadMonth">更新</el-button>
    </header>

    <div class="cwc-legend">
      <span v-for="leg in legendItems" :key="leg.key" class="cwc-legend__item">
        <i class="cwc-legend__dot" :class="`cwc-legend__dot--${leg.key}`" />
        {{ leg.label }}
      </span>
      <span class="cwc-legend__hint">未登録日は月〜金を通常稼働日</span>
    </div>

    <div class="cwc-toolbar cwc-panel">
      <div class="cwc-field">
        <span class="cwc-field__label">対象月</span>
        <el-date-picker v-model="monthValue" type="month" value-format="YYYY-MM" size="small" class="cwc-month" @change="loadMonth" />
      </div>
      <div class="cwc-toolbar__divider" />
      <el-date-picker v-model="newDates" type="dates" value-format="YYYY-MM-DD" placeholder="日付（複数）" size="small" class="cwc-dates" />
      <el-select v-model="newDayType" size="small" class="cwc-type">
        <el-option v-for="t in dayTypes" :key="t.value" :label="t.label" :value="t.value" />
      </el-select>
      <el-input v-model="newName" placeholder="名称" size="small" class="cwc-name" clearable />
      <el-button v-if="canCreate" type="primary" size="small" class="cwc-add-btn" :loading="saving" :disabled="!newDates.length" @click="addEntries">追加</el-button>
    </div>

    <div v-loading="loading" class="cwc-main">
      <section class="cwc-panel cwc-cal">
        <div class="cwc-panel__head">
          <span class="cwc-panel__title">{{ monthLabel }} カレンダー</span>
        </div>
        <div class="cwc-cal__weekdays">
          <span v-for="w in weekdayHeaders" :key="w" class="cwc-cal__wd" :class="{ 'is-sun': w === '日', 'is-sat': w === '土' }">{{ w }}</span>
        </div>
        <div class="cwc-cal__grid">
          <div
            v-for="(cell, idx) in calendarCells"
            :key="idx"
            class="cwc-cal__cell"
            :class="cellClass(cell)"
            :title="cellTitle(cell)"
          >
            <template v-if="cell.inMonth">
              <span class="cwc-cal__num">{{ cell.day }}</span>
              <span v-if="cell.entry?.name" class="cwc-cal__tag">{{ cell.entry.name }}</span>
            </template>
          </div>
        </div>
      </section>

      <section class="cwc-panel cwc-table-wrap">
        <div class="cwc-panel__head">
          <span class="cwc-panel__title">登録一覧</span>
          <span class="cwc-panel__badge">{{ items.length }} 件</span>
        </div>
        <el-table :data="items" size="small" stripe class="cwc-table" empty-text="登録なし（月〜金=稼働）" max-height="420">
          <el-table-column prop="calendar_date" label="日付" width="100" />
          <el-table-column label="曜" width="44" align="center">
            <template #default="{ row }">
              <span class="cwc-wd" :class="weekdayClass(row.calendar_date)">{{ weekdayLabel(row.calendar_date) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="区分" width="84" align="center">
            <template #default="{ row }">
              <el-tag :type="tagType(row.day_type)" size="small" effect="plain" :class="['cwc-type-tag', `cwc-type--${row.day_type}`]">{{ row.day_type_label || row.day_type }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="稼働" width="52" align="center">
            <template #default="{ row }">
              <span class="cwc-sched" :class="{ 'is-on': row.is_scheduled }">{{ row.is_scheduled ? '○' : '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="name" label="名称" min-width="88" show-overflow-tooltip />
          <el-table-column prop="note" label="備考" min-width="72" show-overflow-tooltip />
          <el-table-column v-if="canDelete" label="" width="48" align="center" fixed="right">
            <template #default="{ row }">
              <el-button link type="danger" size="small" :loading="row._deleting" @click="removeEntry(row)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </section>
    </div>

    <footer class="cwc-foot">
      <span class="cwc-foot__item">MES 検査稼働率分析</span>
      <span class="cwc-foot__sep">·</span>
      <span class="cwc-foot__item">分析画面の上書き指定可</span>
      <span class="cwc-foot__sep">·</span>
      <span class="cwc-foot__item">納入先休日は別管理</span>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Calendar, Refresh, Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  batchCreateCompanyWorkCalendar,
  deleteCompanyWorkCalendarEntry,
  fetchCompanyWorkCalendar,
  fetchCompanyWorkCalendarDayTypes,
  type CompanyWorkCalendarItem,
} from '@/api/master/companyWorkCalendar'
import { useMasterOperationPermission } from '@/composables/useMasterOperationPermission'
import { guardMasterOperation } from '@/utils/masterOperationGuard'

defineOptions({ name: 'MasterCompanyWorkCalendar' })

const { canCreate, canDelete } = useMasterOperationPermission()

type RowEx = CompanyWorkCalendarItem & { _deleting?: boolean }

type CalCell = {
  inMonth: boolean
  day: number
  date: string
  isScheduled: boolean
  isWeekend: boolean
  entry?: CompanyWorkCalendarItem
}

const weekdayHeaders = ['日', '月', '火', '水', '木', '金', '土'] as const

const loading = ref(false)
const saving = ref(false)
const monthValue = ref(new Date().toISOString().slice(0, 7))
const items = ref<RowEx[]>([])
const summary = ref({ scheduled: 0, total: 0 })
const dayTypes = ref<{ value: string; label: string }[]>([])
const newDates = ref<string[]>([])
const newDayType = ref('company_holiday')
const newName = ref('')

const legendItems = computed(() =>
  dayTypes.value.length
    ? dayTypes.value.map((t) => ({ key: t.value, label: t.label }))
    : [
        { key: 'national_holiday', label: '祝日' },
        { key: 'company_holiday', label: '会社休' },
        { key: 'paid_leave', label: '有給' },
        { key: 'extra_workday', label: '臨時出勤' },
      ],
)

const offDayCount = computed(() => Math.max(0, summary.value.total - summary.value.scheduled))
const workRate = computed(() =>
  summary.value.total ? Math.round((summary.value.scheduled / summary.value.total) * 100) : 0,
)

const todayStr = (() => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
})()

// ヘッダー統計カードの3Dチルト（マウス追従）
function handleStatTilt(e: MouseEvent) {
  const item = (e.target as HTMLElement | null)?.closest<HTMLElement>('.stat-card')
  const host = e.currentTarget as HTMLElement
  host.querySelectorAll<HTMLElement>('.stat-card').forEach((el) => {
    if (el !== item) {
      el.style.removeProperty('--rx')
      el.style.removeProperty('--ry')
    }
  })
  if (!item) return
  const rect = item.getBoundingClientRect()
  const px = (e.clientX - rect.left) / rect.width
  const py = (e.clientY - rect.top) / rect.height
  item.style.setProperty('--rx', `${((0.5 - py) * 14).toFixed(2)}deg`)
  item.style.setProperty('--ry', `${((px - 0.5) * 14).toFixed(2)}deg`)
  item.style.setProperty('--mx', `${(px * 100).toFixed(1)}%`)
  item.style.setProperty('--my', `${(py * 100).toFixed(1)}%`)
}

function resetStatTilt(e: MouseEvent) {
  ;(e.currentTarget as HTMLElement).querySelectorAll<HTMLElement>('.stat-card').forEach((el) => {
    el.style.removeProperty('--rx')
    el.style.removeProperty('--ry')
  })
}

const monthLabel = computed(() => {
  const [y, m] = (monthValue.value || '').split('-')
  if (!y || !m) return '—'
  return `${y}年${Number(m)}月`
})

const itemByDate = computed(() => {
  const map = new Map<string, CompanyWorkCalendarItem>()
  for (const it of items.value) map.set(it.calendar_date, it)
  return map
})

const calendarCells = computed((): CalCell[] => {
  const ym = monthValue.value
  if (!ym || !/^\d{4}-\d{2}$/.test(ym)) return []
  const [y, m] = ym.split('-').map(Number)
  const first = new Date(y, m - 1, 1)
  const daysInMonth = new Date(y, m, 0).getDate()
  const startPad = first.getDay()
  const cells: CalCell[] = []

  for (let i = 0; i < startPad; i++) {
    cells.push({ inMonth: false, day: 0, date: '', isScheduled: false, isWeekend: false })
  }
  for (let d = 1; d <= daysInMonth; d++) {
    const mm = String(m).padStart(2, '0')
    const dd = String(d).padStart(2, '0')
    const date = `${y}-${mm}-${dd}`
    const dow = new Date(y, m - 1, d).getDay()
    const isWeekend = dow === 0 || dow === 6
    const entry = itemByDate.value.get(date)
    const isScheduled = entry ? entry.is_scheduled : !isWeekend
    cells.push({ inMonth: true, day: d, date, isScheduled, isWeekend, entry })
  }
  while (cells.length % 7 !== 0) {
    cells.push({ inMonth: false, day: 0, date: '', isScheduled: false, isWeekend: false })
  }
  return cells
})

function monthRange(ym: string): [string, string] {
  const [y, m] = ym.split('-').map(Number)
  const last = new Date(y, m, 0).getDate()
  const mm = String(m).padStart(2, '0')
  return [`${y}-${mm}-01`, `${y}-${mm}-${String(last).padStart(2, '0')}`]
}

function tagType(dayType: string): '' | 'success' | 'warning' | 'info' | 'danger' {
  if (dayType === 'extra_workday') return 'warning'
  if (dayType === 'national_holiday') return 'danger'
  if (dayType === 'paid_leave') return 'info'
  if (dayType === 'company_holiday') return 'info'
  return ''
}

function weekdayLabel(dateStr: string): string {
  const d = new Date(dateStr)
  if (Number.isNaN(d.getTime())) return '—'
  return weekdayHeaders[d.getDay()]
}

function weekdayClass(dateStr: string): string {
  const d = new Date(dateStr)
  if (Number.isNaN(d.getTime())) return ''
  if (d.getDay() === 0) return 'is-sun'
  if (d.getDay() === 6) return 'is-sat'
  return ''
}

function cellClass(cell: CalCell): string[] {
  if (!cell.inMonth) return ['is-empty']
  const cls: string[] = []
  if (cell.isScheduled) cls.push('is-work')
  else cls.push('is-off')
  if (cell.entry?.day_type) cls.push(`has-type-${cell.entry.day_type}`)
  if (cell.isWeekend && !cell.entry) cls.push('is-default-weekend')
  if (cell.date === todayStr) cls.push('is-today')
  return cls
}

function cellTitle(cell: CalCell): string {
  if (!cell.inMonth) return ''
  const base = cell.isScheduled ? '通常稼働' : '非稼働'
  if (cell.entry?.day_type_label) return `${cell.date} · ${cell.entry.day_type_label} · ${base}`
  return `${cell.date} · ${base}`
}

async function loadMonth() {
  const ym = monthValue.value
  if (!ym) return
  const [start, end] = monthRange(ym)
  loading.value = true
  try {
    const res = await fetchCompanyWorkCalendar({ start_date: start, end_date: end })
    const data = res?.data
    items.value = (data?.items ?? []).map((x) => ({ ...x, _deleting: false }))
    summary.value = {
      scheduled: data?.scheduled_workday_count ?? 0,
      total: data?.total_days ?? 0,
    }
  } catch {
    items.value = []
    ElMessage.error('読み込みに失敗しました')
  } finally {
    loading.value = false
  }
}

async function addEntries() {
  if (!guardMasterOperation(canCreate)) return
  if (!newDates.value.length) return
  saving.value = true
  try {
    const res = await batchCreateCompanyWorkCalendar({
      dates: newDates.value,
      day_type: newDayType.value,
      name: newName.value.trim() || undefined,
    })
    ElMessage.success(`追加 ${res?.created ?? 0} 件（スキップ ${res?.skipped ?? 0}）`)
    newDates.value = []
    newName.value = ''
    await loadMonth()
  } catch {
    ElMessage.error('追加に失敗しました')
  } finally {
    saving.value = false
  }
}

async function removeEntry(row: RowEx) {
  if (!guardMasterOperation(canDelete)) return
  row._deleting = true
  try {
    await deleteCompanyWorkCalendarEntry(row.id)
    ElMessage.success('削除しました')
    await loadMonth()
  } catch {
    ElMessage.error('削除に失敗しました')
  } finally {
    row._deleting = false
  }
}

onMounted(async () => {
  try {
    dayTypes.value = await fetchCompanyWorkCalendarDayTypes()
  } catch {
    dayTypes.value = [
      { value: 'national_holiday', label: '祝日' },
      { value: 'company_holiday', label: '会社休' },
      { value: 'paid_leave', label: '有給' },
      { value: 'extra_workday', label: '臨時出勤' },
    ]
  }
  await loadMonth()
})
</script>

<style scoped>
.cwc {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 6px 8px 10px;
  min-height: 100%;
  box-sizing: border-box;
}

.cwc-hero {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  padding: 8px 12px;
  border-radius: 10px;
  background: linear-gradient(120deg, #fff 0%, #eff6ff 55%, #f8fafc 100%);
  border: 1px solid rgba(37, 99, 235, 0.14);
  box-shadow: 0 1px 10px rgba(37, 99, 235, 0.07);
}

.cwc-hero__left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.cwc-hero__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 9px;
  color: #fff;
  background: linear-gradient(145deg, #60a5fa, #2563eb);
  flex-shrink: 0;
}

.cwc-hero__eyebrow {
  font-size: 9px;
  font-weight: 700;
  color: #2563eb;
  letter-spacing: 0.05em;
  line-height: 1.2;
}

.cwc-hero__title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.25;
}

.cwc-hero__stats {
  display: flex;
  align-items: center;
  gap: 5px;
  flex-wrap: wrap;
}

.cwc-chip {
  font-size: 10px;
  color: #475569;
  padding: 3px 8px;
  border-radius: 999px;
  background: #f1f5f9;
  white-space: nowrap;
}

.cwc-chip strong {
  color: #1e293b;
  font-weight: 700;
}

.cwc-chip--primary {
  background: rgba(37, 99, 235, 0.1);
  color: #1d4ed8;
}

.cwc-chip--muted {
  background: transparent;
  border: 1px solid #e2e8f0;
}

.cwc-hero__refresh {
  margin-left: auto;
}

.cwc-legend {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  padding: 4px 8px;
  font-size: 10px;
  color: #64748b;
}

.cwc-legend__item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.cwc-legend__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  display: inline-block;
}

.cwc-legend__dot--national_holiday { background: #ef4444; }
.cwc-legend__dot--company_holiday { background: #64748b; }
.cwc-legend__dot--paid_leave { background: #8b5cf6; }
.cwc-legend__dot--extra_workday { background: #f97316; }

.cwc-legend__hint {
  margin-left: auto;
  font-size: 9px;
  color: #94a3b8;
}

.cwc-panel {
  border-radius: 9px;
  background: #fff;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 6px rgba(15, 23, 42, 0.04);
  padding: 8px 10px;
}

.cwc-toolbar {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.cwc-toolbar__divider {
  width: 1px;
  height: 22px;
  background: #e2e8f0;
  flex-shrink: 0;
}

.cwc-field {
  display: flex;
  align-items: center;
  gap: 5px;
}

.cwc-field__label {
  font-size: 10px;
  font-weight: 700;
  color: #64748b;
  white-space: nowrap;
}

.cwc-month { width: 118px !important; }
.cwc-dates { min-width: 160px !important; flex: 1; max-width: 240px; }
.cwc-type { width: 108px; }
.cwc-name { width: 120px; }

.cwc-main {
  display: grid;
  grid-template-columns: minmax(260px, 340px) 1fr;
  gap: 6px;
  align-items: start;
}

@media (max-width: 960px) {
  .cwc-main {
    grid-template-columns: 1fr;
  }
}

.cwc-panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.cwc-panel__title {
  font-size: 12px;
  font-weight: 700;
  color: #1e293b;
}

.cwc-panel__badge {
  font-size: 9px;
  font-weight: 600;
  color: #2563eb;
  padding: 1px 7px;
  border-radius: 999px;
  background: rgba(37, 99, 235, 0.1);
}

.cwc-cal__weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
  margin-bottom: 2px;
}

.cwc-cal__wd {
  text-align: center;
  font-size: 9px;
  font-weight: 700;
  color: #64748b;
  padding: 2px 0;
}

.cwc-cal__wd.is-sun { color: #ef4444; }
.cwc-cal__wd.is-sat { color: #2563eb; }

.cwc-cal__grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
}

.cwc-cal__cell {
  aspect-ratio: 1;
  min-height: 34px;
  border-radius: 5px;
  border: 1px solid transparent;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0;
  padding: 1px;
  font-size: 10px;
  line-height: 1.1;
}

.cwc-cal__cell.is-empty {
  background: transparent;
  border: none;
}

.cwc-cal__cell.is-work {
  background: #f0fdf4;
  border-color: #bbf7d0;
  color: #166534;
}

.cwc-cal__cell.is-off {
  background: #fef2f2;
  border-color: #fecaca;
  color: #991b1b;
}

.cwc-cal__cell.is-default-weekend {
  background: #f8fafc;
  border-color: #e2e8f0;
  color: #94a3b8;
}

.cwc-cal__cell.has-type-national_holiday { box-shadow: inset 0 0 0 2px #ef4444; }
.cwc-cal__cell.has-type-company_holiday { box-shadow: inset 0 0 0 2px #64748b; }
.cwc-cal__cell.has-type-paid_leave { box-shadow: inset 0 0 0 2px #8b5cf6; }
.cwc-cal__cell.has-type-extra_workday { box-shadow: inset 0 0 0 2px #f97316; }

.cwc-cal__num {
  font-weight: 700;
  font-size: 11px;
}

.cwc-cal__tag {
  font-size: 7px;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: inherit;
  opacity: 0.85;
}

.cwc-table :deep(.el-table__header th) {
  background: #f8fafc !important;
  font-size: 10px;
  padding: 4px 0;
}

.cwc-table :deep(.el-table__body td) {
  font-size: 11px;
  padding: 3px 0;
}

.cwc-wd.is-sun { color: #ef4444; font-weight: 600; }
.cwc-wd.is-sat { color: #2563eb; font-weight: 600; }

.cwc-sched {
  font-size: 11px;
  color: #94a3b8;
}

.cwc-sched.is-on {
  color: #16a34a;
  font-weight: 700;
}

.cwc-foot {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
  padding: 4px 8px;
  font-size: 9px;
  color: #94a3b8;
  border-top: 1px dashed #e2e8f0;
}

.cwc-foot__sep {
  opacity: 0.5;
}

/* ============================================================
 * 页面美化：現代UI・3D動効・色分け（会社稼働カレンダー / navy→royal→teal）
 * ============================================================ */
.cwc-modern {
  --hx-1: #0b1a3a;
  --hx-2: #1e3a8a;
  --hx-3: #2563eb;
  --hx-4: #0d9488;
  --hx-deep: #1e3a8a;
  --hx-soft: #eff6ff;
  --hx-line: rgba(37, 99, 235, 0.16);
  gap: 8px;
  padding: 8px 10px 12px;
  background:
    radial-gradient(1100px 340px at 8% -10%, rgba(37, 99, 235, 0.08), transparent 60%),
    radial-gradient(900px 300px at 100% 0%, rgba(13, 148, 136, 0.07), transparent 60%);
}

.cwc-modern .cwc-hero {
  position: relative;
  overflow: hidden;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 16px;
  border: none;
  background: linear-gradient(125deg, var(--hx-1) 0%, var(--hx-2) 38%, var(--hx-3) 72%, var(--hx-4) 100%);
  box-shadow:
    0 18px 36px -18px rgba(30, 58, 138, 0.6),
    0 6px 14px -6px rgba(13, 148, 136, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.18);
}

.cwc-modern .cwc-hero > :not(.page-header-fx) {
  position: relative;
  z-index: 1;
}

.cwc-modern .page-header-fx {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}

.cwc-modern .cwc-hero__icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.32), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.35);
  box-shadow:
    0 4px 0 rgba(11, 26, 58, 0.5),
    0 10px 18px -6px rgba(0, 0, 0, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
  animation: cwcIconFlip 6s ease-in-out infinite;
}

.cwc-modern .cwc-hero__eyebrow {
  font-size: 10px;
  color: #bfdbfe;
}

.cwc-modern .cwc-hero__title {
  font-size: 18px;
  font-weight: 800;
  color: #fff;
  text-shadow: 0 2px 10px rgba(11, 26, 58, 0.35);
}

.cwc-modern .cwc-hero__month {
  margin-left: 6px;
  font-size: 11px;
  font-weight: 700;
  color: #fff;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 2px 0 rgba(11, 26, 58, 0.35);
}

.cwc-modern .cwc-hero__stats {
  gap: 8px;
  perspective: 650px;
}

.cwc-modern .stat-card {
  --sc: #bfdbfe;
  position: relative;
  overflow: hidden;
  min-width: 70px;
  padding: 6px 12px 5px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.24), rgba(255, 255, 255, 0.08));
  border: 1px solid rgba(255, 255, 255, 0.28);
  backdrop-filter: blur(8px);
  box-shadow:
    0 3px 0 rgba(11, 26, 58, 0.4),
    0 10px 20px -10px rgba(0, 0, 0, 0.45);
  transform: rotateX(var(--rx, 0deg)) rotateY(var(--ry, 0deg));
  transform-style: preserve-3d;
  transition: transform 0.18s ease-out, box-shadow 0.25s ease;
}

.cwc-modern .stat-card::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 3px;
  background: var(--sc);
}

.cwc-modern .stat-card::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at var(--mx, 50%) var(--my, 50%), rgba(255, 255, 255, 0.35), transparent 60%);
  opacity: 0;
  transition: opacity 0.2s ease;
  pointer-events: none;
}

.cwc-modern .stat-card:hover::after {
  opacity: 1;
}

.cwc-modern .stat-card:hover {
  box-shadow:
    0 5px 0 rgba(11, 26, 58, 0.45),
    0 16px 26px -12px rgba(0, 0, 0, 0.5);
}

.cwc-modern .stat-work { --sc: #86efac; }
.cwc-modern .stat-off { --sc: #fca5a5; }
.cwc-modern .stat-reg { --sc: #c4b5fd; }
.cwc-modern .stat-rate { --sc: #5eead4; }

.cwc-modern .stat-num {
  font-size: 17px;
  font-weight: 800;
  color: #fff;
  line-height: 1.1;
  font-variant-numeric: tabular-nums;
  transform: translateZ(14px);
  text-shadow: 0 2px 6px rgba(11, 26, 58, 0.35);
}

.cwc-modern .stat-num small {
  font-size: 10px;
  font-weight: 700;
  opacity: 0.8;
  margin-left: 1px;
}

.cwc-modern .stat-lbl {
  font-size: 10px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.88);
  letter-spacing: 0.04em;
}

.cwc-modern .cwc-hero__refresh {
  color: #fff;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.35);
  box-shadow: 0 3px 0 rgba(11, 26, 58, 0.4);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.cwc-modern .cwc-hero__refresh:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.26);
  border-color: rgba(255, 255, 255, 0.5);
  transform: translateY(-2px);
  box-shadow: 0 5px 0 rgba(11, 26, 58, 0.45);
}

.cwc-modern .cwc-hero__refresh:active {
  transform: translateY(2px);
  box-shadow: 0 1px 0 rgba(11, 26, 58, 0.45);
}

.cwc-modern .cwc-legend {
  padding: 6px 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid var(--hx-line);
  box-shadow: 0 4px 12px -8px rgba(30, 58, 138, 0.3);
  font-size: 11px;
}

.cwc-modern .cwc-legend__item {
  padding: 2px 8px;
  border-radius: 999px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  font-weight: 600;
  color: #334155;
}

.cwc-modern .cwc-legend__dot {
  width: 8px;
  height: 8px;
  box-shadow: 0 0 0 3px rgba(148, 163, 184, 0.18);
  animation: cwcDotPulse 2.6s ease-in-out infinite;
}

.cwc-modern .cwc-legend__hint {
  font-size: 10px;
}

.cwc-modern .cwc-panel {
  position: relative;
  overflow: hidden;
  border-radius: 14px;
  border: 1px solid var(--hx-line);
  box-shadow:
    0 10px 24px -16px rgba(30, 58, 138, 0.35),
    0 2px 6px rgba(15, 23, 42, 0.04);
  padding-top: 11px;
}

.cwc-modern .cwc-panel::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 3px;
  z-index: 5;
  background: linear-gradient(90deg, var(--hx-2), var(--hx-3), var(--hx-4), #5eead4);
}

.cwc-modern .cwc-toolbar :deep(.el-input__wrapper),
.cwc-modern .cwc-toolbar :deep(.el-select__wrapper) {
  border-radius: 9px;
}

.cwc-modern .cwc-field__label {
  padding: 2px 8px;
  border-radius: 999px;
  color: var(--hx-deep);
  background: var(--hx-soft);
  border: 1px solid rgba(37, 99, 235, 0.18);
}

.cwc-modern .cwc-add-btn {
  --k-edge: #115e59;
  --k-glow: rgba(13, 148, 136, 0.5);
  border: none;
  border-radius: 9px;
  font-weight: 700;
  padding: 0 16px;
  background: linear-gradient(135deg, #2563eb, #0d9488);
  box-shadow:
    0 3px 0 var(--k-edge),
    0 10px 18px -8px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease;
}

.cwc-modern .cwc-add-btn:hover:not(.is-disabled) {
  transform: translateY(-2px);
  filter: brightness(1.06);
  background: linear-gradient(135deg, #2563eb, #0d9488);
  box-shadow:
    0 5px 0 var(--k-edge),
    0 14px 22px -8px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

.cwc-modern .cwc-add-btn:active:not(.is-disabled) {
  transform: translateY(2px);
  box-shadow: 0 1px 0 var(--k-edge);
}

.cwc-modern .cwc-add-btn.is-disabled {
  box-shadow: none;
  opacity: 0.55;
}

.cwc-modern .cwc-panel__title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12.5px;
  font-weight: 800;
  color: var(--hx-deep);
}

.cwc-modern .cwc-panel__title::before {
  content: '';
  width: 4px;
  height: 14px;
  border-radius: 2px;
  background: linear-gradient(180deg, var(--hx-3), var(--hx-4));
}

.cwc-modern .cwc-panel__badge {
  font-size: 10px;
  font-weight: 800;
  color: #fff;
  background: linear-gradient(135deg, var(--hx-3), var(--hx-4));
  box-shadow: 0 2px 0 var(--hx-deep);
}

.cwc-modern .cwc-cal__wd {
  font-size: 10px;
  border-radius: 6px;
  background: #f1f5f9;
}

.cwc-modern .cwc-cal__wd.is-sun {
  background: #fef2f2;
}

.cwc-modern .cwc-cal__wd.is-sat {
  background: #eff6ff;
}

.cwc-modern .cwc-cal__grid {
  gap: 3px;
  perspective: 800px;
}

.cwc-modern .cwc-cal__cell:not(.is-empty) {
  --edge: #e2e8f0;
  position: relative;
  border-radius: 7px;
  box-shadow:
    inset 0 0 0 2px var(--ring, transparent),
    0 2px 0 var(--edge);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.cwc-modern .cwc-cal__cell:not(.is-empty):hover {
  z-index: 2;
  transform: translateY(-3px) rotateX(10deg) scale(1.07);
  box-shadow:
    inset 0 0 0 2px var(--ring, transparent),
    0 4px 0 var(--edge),
    0 12px 18px -8px rgba(15, 23, 42, 0.35);
}

.cwc-modern .cwc-cal__cell.is-work {
  --edge: #86efac;
  background: linear-gradient(160deg, #f0fdf4, #dcfce7);
}

.cwc-modern .cwc-cal__cell.is-off {
  --edge: #fca5a5;
  background: linear-gradient(160deg, #fef2f2, #fee2e2);
}

.cwc-modern .cwc-cal__cell.is-default-weekend {
  --edge: #cbd5e1;
  background: linear-gradient(160deg, #f8fafc, #f1f5f9);
}

.cwc-modern .cwc-cal__cell.has-type-national_holiday { --ring: #ef4444; }
.cwc-modern .cwc-cal__cell.has-type-company_holiday { --ring: #64748b; }
.cwc-modern .cwc-cal__cell.has-type-paid_leave { --ring: #8b5cf6; }
.cwc-modern .cwc-cal__cell.has-type-extra_workday {
  --ring: #f97316;
  background: linear-gradient(160deg, #fff7ed, #ffedd5);
}

.cwc-modern .cwc-cal__cell.is-today::after {
  content: '';
  position: absolute;
  inset: -2px;
  border-radius: 9px;
  border: 2px solid var(--hx-3);
  pointer-events: none;
  animation: cwcTodayPulse 2s ease-in-out infinite;
}

.cwc-modern .cwc-cal__cell.is-today .cwc-cal__num {
  color: #fff;
  min-width: 18px;
  padding: 0 4px;
  border-radius: 999px;
  background: linear-gradient(135deg, var(--hx-3), var(--hx-4));
}

.cwc-modern .cwc-table :deep(.el-table__header-wrapper th.el-table__cell) {
  background: linear-gradient(180deg, #1e3a8a, #1d4ed8) !important;
  color: #fff !important;
  border-bottom: 2px solid #14b8a6 !important;
}

.cwc-modern .cwc-table :deep(.el-table__body tr:hover > td.el-table__cell:first-child) {
  box-shadow: inset 3px 0 0 var(--hx-3);
}

.cwc-modern .cwc-type-tag {
  --tt: #64748b;
  --el-tag-text-color: var(--tt);
  --el-tag-bg-color: color-mix(in srgb, var(--tt) 9%, #fff);
  --el-tag-border-color: color-mix(in srgb, var(--tt) 35%, #fff);
  font-weight: 700;
  border-radius: 999px;
}

.cwc-modern .cwc-type--national_holiday { --tt: #dc2626; }
.cwc-modern .cwc-type--company_holiday { --tt: #475569; }
.cwc-modern .cwc-type--paid_leave { --tt: #7c3aed; }
.cwc-modern .cwc-type--extra_workday { --tt: #ea580c; }

.cwc-modern .cwc-sched.is-on {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  color: #fff;
  background: linear-gradient(135deg, #22c55e, #16a34a);
  box-shadow: 0 2px 0 #15803d;
}

.cwc-modern .cwc-foot {
  border-top-color: var(--hx-line);
}

.cwc-modern .cwc-foot__item {
  padding: 1px 8px;
  border-radius: 999px;
  background: var(--hx-soft);
  color: var(--hx-deep);
}

@keyframes cwcIconFlip {
  0%,
  100% {
    transform: perspective(300px) rotateX(0deg) rotateY(0deg);
  }
  50% {
    transform: perspective(300px) rotateX(18deg) rotateY(-12deg);
  }
}

@keyframes cwcTodayPulse {
  0%,
  100% {
    opacity: 1;
    box-shadow: 0 0 0 0 rgba(37, 99, 235, 0.35);
  }
  50% {
    opacity: 0.7;
    box-shadow: 0 0 0 4px rgba(37, 99, 235, 0);
  }
}

@keyframes cwcDotPulse {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.25);
  }
}

@media (prefers-reduced-motion: reduce) {
  .cwc-modern .cwc-hero__icon,
  .cwc-modern .cwc-legend__dot,
  .cwc-modern .cwc-cal__cell.is-today::after {
    animation: none;
  }

  .cwc-modern .stat-card,
  .cwc-modern .cwc-cal__cell:not(.is-empty):hover {
    transform: none;
  }
}
</style>
