<template>
  <div class="dh">
    <div class="dh-orb dh-orb--rose" />
    <div class="dh-orb dh-orb--amber" />
    <div class="dh-orb dh-orb--indigo" />

    <header class="dh-hero">
      <div class="dh-hero__glow" />
      <div class="dh-hero__left">
        <div class="dh-hero__icon">
          <el-icon :size="22"><Calendar /></el-icon>
        </div>
        <div>
          <div class="dh-hero__eyebrow">マスタ · 納入先</div>
          <h1 class="dh-hero__title">納入先休日設定</h1>
          <p class="dh-hero__sub">複数の納入先をまとめて休日・臨時出勤を登録できます</p>
        </div>
      </div>
      <div class="dh-hero__stats">
        <div class="dh-stat dh-stat--dest">
          <span class="dh-stat__num">{{ selectedCds.length }}</span>
          <span class="dh-stat__label">選択中</span>
        </div>
        <div class="dh-stat dh-stat--holiday">
          <span class="dh-stat__num">{{ holidayList.length }}</span>
          <span class="dh-stat__label">休日</span>
        </div>
        <div class="dh-stat dh-stat--work">
          <span class="dh-stat__num">{{ workdayList.length }}</span>
          <span class="dh-stat__label">臨時出勤</span>
        </div>
      </div>
    </header>

    <section class="dh-panel dh-picker">
      <div class="dh-picker__head">
        <div class="dh-picker__title">
          <el-icon><Van /></el-icon>
          納入先
          <span class="dh-picker__count">{{ selectedCds.length }} / {{ destinationOptions.length }}</span>
        </div>
        <div class="dh-picker__actions">
          <el-button size="small" round :disabled="!destinationOptions.length" @click="selectAll">
            全選択
          </el-button>
          <el-button size="small" round :disabled="!selectedCds.length" @click="clearSelection">
            クリア
          </el-button>
          <el-button
            type="primary"
            size="small"
            round
            :icon="Refresh"
            :loading="loading"
            :disabled="!selectedCds.length"
            @click="fetchLists"
          >
            読み込み
          </el-button>
        </div>
      </div>

      <el-select
        v-model="selectedCds"
        multiple
        filterable
        collapse-tags
        collapse-tags-tooltip
        :max-collapse-tags="4"
        placeholder="納入先を選択（複数・全選択可）"
        class="dh-select"
        popper-class="destination-select-popper"
        :loading="optionsLoading"
        clearable
      >
        <el-option
          v-for="item in destinationOptions"
          :key="item.cd"
          :label="`${item.cd}｜${item.name}`"
          :value="item.cd"
        />
      </el-select>

      <div v-if="selectedCds.length" class="dh-chips">
        <button
          v-for="cd in selectedCds"
          :key="cd"
          type="button"
          class="dh-chip"
          @click="removeDest(cd)"
        >
          <span class="dh-chip__cd">{{ cd }}</span>
          <span class="dh-chip__name">{{ destName(cd) }}</span>
          <el-icon class="dh-chip__x"><Close /></el-icon>
        </button>
      </div>
      <p v-else class="dh-picker__hint">納入先を選ぶと、休日・臨時出勤の追加が選択中すべてに反映されます。</p>
    </section>

    <div class="dh-grid">
      <article class="dh-card dh-card--holiday">
        <div class="dh-card__shine" />
        <header class="dh-card__head">
          <div class="dh-card__badge">
            <el-icon><CircleCloseFilled /></el-icon>
          </div>
          <div>
            <h2>休日一覧</h2>
            <p>出荷停止日として扱う日付</p>
          </div>
          <span class="dh-card__count">{{ holidayList.length }}</span>
        </header>
        <div class="dh-card__body">
          <div class="dh-add">
            <el-date-picker
              v-model="newHolidayDates"
              type="dates"
              placeholder="休日を複数選択"
              value-format="YYYY-MM-DD"
              :disabled="!selectedCds.length"
              class="dh-dates"
            />
            <el-button
              v-if="canCreate"
              type="danger"
              :disabled="!selectedCds.length || !newHolidayDates.length"
              :loading="actionLoading"
              @click="addHoliday"
            >
              追加
            </el-button>
          </div>
          <el-table
            :data="holidayList"
            stripe
            empty-text="休日なし"
            class="dh-table"
            v-loading="loading"
            max-height="420"
          >
            <el-table-column v-if="selectedCds.length > 1" label="納入先" min-width="140">
              <template #default="{ row }">
                <div class="dh-dest-cell">
                  <span class="dh-dest-cell__cd">{{ row.destination_cd }}</span>
                  <span class="dh-dest-cell__name">{{ destName(row.destination_cd) }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="日付" min-width="120" align="center">
              <template #default="{ row }">
                <span class="dh-date">{{ formatDate(row.holiday_date) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="曜日" width="72" align="center">
              <template #default="{ row }">
                <span class="dh-wd" :class="weekdayClass(row.holiday_date)">{{ getWeekday(row.holiday_date) }}</span>
              </template>
            </el-table-column>
            <el-table-column v-if="canDelete" label="" width="56" align="center">
              <template #default="{ row }">
                <el-button
                  type="danger"
                  size="small"
                  circle
                  plain
                  :loading="(row as HolidayEx).deleting"
                  @click="deleteHoliday(row)"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </article>

      <article class="dh-card dh-card--work">
        <div class="dh-card__shine" />
        <header class="dh-card__head">
          <div class="dh-card__badge">
            <el-icon><Sunny /></el-icon>
          </div>
          <div>
            <h2>臨時出勤日</h2>
            <p>休日でも稼働させる日付</p>
          </div>
          <span class="dh-card__count">{{ workdayList.length }}</span>
        </header>
        <div class="dh-card__body">
          <div class="dh-add">
            <el-date-picker
              v-model="newWorkdayDate"
              type="date"
              placeholder="出勤日"
              value-format="YYYY-MM-DD"
              :disabled="!selectedCds.length"
              class="dh-date-one"
            />
            <el-input
              v-model="newWorkdayReason"
              placeholder="理由（任意）"
              :disabled="!selectedCds.length"
              class="dh-reason"
              clearable
            />
            <el-button
              v-if="canCreate"
              type="warning"
              :disabled="!selectedCds.length || !newWorkdayDate"
              :loading="workdayActionLoading"
              @click="addWorkday"
            >
              追加
            </el-button>
          </div>
          <el-table
            :data="workdayList"
            stripe
            empty-text="臨時出勤日なし"
            class="dh-table"
            v-loading="workdayLoading"
            max-height="420"
          >
            <el-table-column v-if="selectedCds.length > 1" label="納入先" min-width="140">
              <template #default="{ row }">
                <div class="dh-dest-cell">
                  <span class="dh-dest-cell__cd">{{ row.destination_cd }}</span>
                  <span class="dh-dest-cell__name">{{ destName(row.destination_cd) }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="日付" width="120" align="center">
              <template #default="{ row }">
                <span class="dh-date">{{ formatDate(row.work_date) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="曜日" width="64" align="center">
              <template #default="{ row }">
                <span class="dh-wd" :class="weekdayClass(row.work_date)">{{ getWeekday(row.work_date) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="理由" min-width="110" show-overflow-tooltip>
              <template #default="{ row }">{{ row.reason || '—' }}</template>
            </el-table-column>
            <el-table-column v-if="canDelete" label="" width="56" align="center">
              <template #default="{ row }">
                <el-button
                  type="danger"
                  size="small"
                  circle
                  plain
                  :loading="(row as WorkdayEx).deleting"
                  @click="deleteWorkday(row)"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </article>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Calendar, CircleCloseFilled, Close, Delete, Refresh, Sunny, Van } from '@element-plus/icons-vue'
import {
  addHolidayDate,
  addWorkdayDate,
  deleteHolidayDate,
  deleteWorkdayDate,
  getHolidaysByDest,
  getWorkdaysByDest,
} from '@/api/master/destinationMaster'
import { getDestinationMasterOptions } from '@/api/options'
import type { DestinationHolidayItem, DestinationWorkdayItem, OptionItem } from '@/types/master'
import { useMasterOperationPermission } from '@/composables/useMasterOperationPermission'
import { guardMasterOperation } from '@/utils/masterOperationGuard'

const { canCreate, canDelete } = useMasterOperationPermission()

type HolidayEx = DestinationHolidayItem & { deleting?: boolean }
type WorkdayEx = DestinationWorkdayItem & { deleting?: boolean }

const selectedCds = ref<string[]>([])
const destinationOptions = ref<OptionItem[]>([])
const optionsLoading = ref(false)
const holidayList = ref<HolidayEx[]>([])
const newHolidayDates = ref<string[]>([])
const loading = ref(false)
const actionLoading = ref(false)
const workdayList = ref<WorkdayEx[]>([])
const newWorkdayDate = ref('')
const newWorkdayReason = ref('')
const workdayLoading = ref(false)
const workdayActionLoading = ref(false)

const destMap = computed(() => {
  const m = new Map<string, string>()
  for (const d of destinationOptions.value) m.set(d.cd, d.name || d.cd)
  return m
})

function destName(cd: string) {
  return destMap.value.get(cd) || cd
}

function formatDate(dateStr: string) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getFullYear()}/${String(d.getMonth() + 1).padStart(2, '0')}/${String(d.getDate()).padStart(2, '0')}`
}

function getWeekday(dateStr: string) {
  if (!dateStr) return ''
  return ['日', '月', '火', '水', '木', '金', '土'][new Date(dateStr).getDay()]
}

function weekdayClass(dateStr: string) {
  if (!dateStr) return ''
  const d = new Date(dateStr).getDay()
  if (d === 0) return 'is-sun'
  if (d === 6) return 'is-sat'
  return 'is-wd'
}

function isAlreadyExists(error: unknown) {
  const e = error as { response?: { data?: { detail?: string } }; message?: string }
  const msg = String(e?.response?.data?.detail || e?.message || '')
  return msg.includes('既に登録')
}

function selectAll() {
  selectedCds.value = destinationOptions.value.map((d) => d.cd)
}

function clearSelection() {
  selectedCds.value = []
  holidayList.value = []
  workdayList.value = []
}

function removeDest(cd: string) {
  selectedCds.value = selectedCds.value.filter((x) => x !== cd)
}

async function confirmMulti(kind: string) {
  if (selectedCds.value.length <= 1) return true
  try {
    await ElMessageBox.confirm(
      `選択中の ${selectedCds.value.length} 件の納入先に${kind}を登録します。よろしいですか？`,
      '一括登録の確認',
      { type: 'warning', confirmButtonText: '登録する', cancelButtonText: 'キャンセル' },
    )
    return true
  } catch {
    return false
  }
}

async function fetchLists() {
  if (!selectedCds.value.length) {
    ElMessage.warning('納入先を選択してください')
    return
  }
  loading.value = true
  workdayLoading.value = true
  try {
    const holidays: HolidayEx[] = []
    const workdays: WorkdayEx[] = []
    const cds = [...selectedCds.value]
    const chunk = 8
    for (let i = 0; i < cds.length; i += chunk) {
      const part = cds.slice(i, i + chunk)
      const rows = await Promise.all(
        part.map(async (cd) => {
          const [h, w] = await Promise.all([getHolidaysByDest(cd), getWorkdaysByDest(cd)])
          return { h, w }
        }),
      )
      for (const r of rows) {
        holidays.push(...r.h.map((x) => ({ ...x, deleting: false })))
        workdays.push(...r.w.map((x) => ({ ...x, deleting: false })))
      }
    }
    holidays.sort((a, b) => String(a.holiday_date).localeCompare(String(b.holiday_date)) || a.destination_cd.localeCompare(b.destination_cd))
    workdays.sort((a, b) => String(a.work_date).localeCompare(String(b.work_date)) || a.destination_cd.localeCompare(b.destination_cd))
    holidayList.value = holidays
    workdayList.value = workdays
  } catch {
    ElMessage.error('読み込みに失敗しました')
    holidayList.value = []
    workdayList.value = []
  } finally {
    loading.value = false
    workdayLoading.value = false
  }
}

async function addHoliday() {
  if (!guardMasterOperation(canCreate)) return
  if (!selectedCds.value.length || !newHolidayDates.value.length) return
  if (!(await confirmMulti('休日'))) return
  actionLoading.value = true
  let ok = 0
  let skip = 0
  let fail = 0
  try {
    for (const cd of selectedCds.value) {
      for (const d of newHolidayDates.value) {
        try {
          await addHolidayDate(cd, d)
          ok += 1
        } catch (e) {
          if (isAlreadyExists(e)) skip += 1
          else fail += 1
        }
      }
    }
    if (fail) ElMessage.error(`休日追加：成功 ${ok} / 既存 ${skip} / 失敗 ${fail}`)
    else ElMessage.success(skip ? `休日を追加しました（新規 ${ok} / 既存スキップ ${skip}）` : '休日を追加しました')
    newHolidayDates.value = []
    await fetchLists()
  } finally {
    actionLoading.value = false
  }
}

async function deleteHoliday(row: HolidayEx) {
  if (!guardMasterOperation(canDelete)) return
  if (row.id == null) return
  row.deleting = true
  try {
    await deleteHolidayDate(row.id)
    ElMessage.success('削除しました')
    await fetchLists()
  } catch {
    ElMessage.error('削除に失敗しました')
  } finally {
    row.deleting = false
  }
}

async function addWorkday() {
  if (!guardMasterOperation(canCreate)) return
  if (!selectedCds.value.length || !newWorkdayDate.value) return
  if (!(await confirmMulti('臨時出勤日'))) return
  workdayActionLoading.value = true
  let ok = 0
  let skip = 0
  let fail = 0
  try {
    for (const cd of selectedCds.value) {
      try {
        await addWorkdayDate(cd, newWorkdayDate.value, newWorkdayReason.value || undefined)
        ok += 1
      } catch (e) {
        if (isAlreadyExists(e)) skip += 1
        else fail += 1
      }
    }
    if (fail) ElMessage.error(`臨時出勤追加：成功 ${ok} / 既存 ${skip} / 失敗 ${fail}`)
    else ElMessage.success(skip ? `臨時出勤日を追加しました（新規 ${ok} / 既存スキップ ${skip}）` : '臨時出勤日を追加しました')
    newWorkdayDate.value = ''
    newWorkdayReason.value = ''
    await fetchLists()
  } finally {
    workdayActionLoading.value = false
  }
}

async function deleteWorkday(row: WorkdayEx) {
  if (!guardMasterOperation(canDelete)) return
  if (row.id == null) return
  row.deleting = true
  try {
    await deleteWorkdayDate(row.id)
    ElMessage.success('削除しました')
    await fetchLists()
  } catch {
    ElMessage.error('削除に失敗しました')
  } finally {
    row.deleting = false
  }
}

watch(selectedCds, (cds) => {
  if (cds.length === 1) fetchLists()
  if (!cds.length) {
    holidayList.value = []
    workdayList.value = []
  }
})

onMounted(async () => {
  optionsLoading.value = true
  try {
    destinationOptions.value = await getDestinationMasterOptions()
  } catch {
    destinationOptions.value = []
  } finally {
    optionsLoading.value = false
  }
})
</script>

<style scoped>
.dh {
  --ink: #0f172a;
  --muted: #64748b;
  --line: rgba(148, 163, 184, 0.28);
  --holiday: #e11d48;
  --holiday-deep: #9f1239;
  --work: #d97706;
  --work-deep: #b45309;
  --dest: #4f46e5;
  position: relative;
  isolation: isolate;
  min-height: calc(100vh - 88px);
  padding: 18px 20px 32px;
  overflow: hidden;
  color: var(--ink);
  background:
    radial-gradient(1200px 480px at 8% -10%, rgba(244, 63, 94, 0.12), transparent 55%),
    radial-gradient(900px 420px at 96% 0%, rgba(245, 158, 11, 0.14), transparent 50%),
    linear-gradient(180deg, #f8fafc 0%, #eef2ff 48%, #f8fafc 100%);
}

.dh-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(2px);
  pointer-events: none;
  z-index: 0;
  animation: dh-float 9s ease-in-out infinite;
}
.dh-orb--rose {
  width: 220px;
  height: 220px;
  top: 40px;
  right: 8%;
  background: radial-gradient(circle, rgba(244, 63, 94, 0.28), transparent 70%);
}
.dh-orb--amber {
  width: 180px;
  height: 180px;
  bottom: 12%;
  left: 4%;
  background: radial-gradient(circle, rgba(251, 191, 36, 0.26), transparent 70%);
  animation-delay: -3s;
}
.dh-orb--indigo {
  width: 160px;
  height: 160px;
  top: 38%;
  right: -40px;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.22), transparent 70%);
  animation-delay: -5.5s;
}

@keyframes dh-float {
  0%,
  100% {
    transform: translate3d(0, 0, 0) scale(1);
  }
  50% {
    transform: translate3d(12px, -18px, 0) scale(1.08);
  }
}

.dh-hero,
.dh-panel,
.dh-card {
  position: relative;
  z-index: 1;
}

.dh-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
  padding: 18px 20px;
  border-radius: 22px;
  overflow: hidden;
  color: #fff;
  background: linear-gradient(135deg, #1e1b4b 0%, #4338ca 42%, #db2777 100%);
  box-shadow:
    0 18px 40px rgba(67, 56, 202, 0.28),
    inset 0 1px 0 rgba(255, 255, 255, 0.22);
  transform: perspective(900px) rotateX(2deg);
  animation: dh-hero-in 0.55s cubic-bezier(0.22, 1, 0.36, 1);
}

.dh-hero__glow {
  position: absolute;
  inset: -40% auto auto 20%;
  width: 240px;
  height: 240px;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.18), transparent 65%);
  pointer-events: none;
}

.dh-hero__left {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}
.dh-hero__icon {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  border-radius: 16px;
  background: linear-gradient(160deg, #fb7185, #e11d48);
  box-shadow: 0 10px 20px rgba(225, 29, 72, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.35);
}
.dh-hero__eyebrow {
  font-size: 11px;
  letter-spacing: 0.12em;
  opacity: 0.78;
  font-weight: 700;
}
.dh-hero__title {
  margin: 2px 0 0;
  font-size: 22px;
  font-weight: 800;
  letter-spacing: 0.02em;
}
.dh-hero__sub {
  margin: 4px 0 0;
  font-size: 12px;
  opacity: 0.82;
}

.dh-hero__stats {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.dh-stat {
  min-width: 84px;
  padding: 10px 14px;
  border-radius: 16px;
  text-align: center;
  background: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(10px);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.25);
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}
.dh-stat:hover {
  transform: translateY(-4px) scale(1.03);
  box-shadow: 0 10px 18px rgba(0, 0, 0, 0.16);
}
.dh-stat--holiday {
  background: rgba(244, 63, 94, 0.28);
}
.dh-stat--work {
  background: rgba(245, 158, 11, 0.32);
}
.dh-stat__num {
  display: block;
  font-size: 22px;
  font-weight: 800;
  line-height: 1.1;
}
.dh-stat__label {
  font-size: 11px;
  opacity: 0.88;
}

@keyframes dh-hero-in {
  from {
    opacity: 0;
    transform: perspective(900px) rotateX(8deg) translateY(16px);
  }
  to {
    opacity: 1;
    transform: perspective(900px) rotateX(2deg) translateY(0);
  }
}

.dh-picker {
  margin-bottom: 16px;
  padding: 14px 16px 16px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(255, 255, 255, 0.7);
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(16px);
}
.dh-picker__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}
.dh-picker__title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 800;
  color: #312e81;
}
.dh-picker__count {
  font-size: 12px;
  font-weight: 700;
  color: #6366f1;
  background: #eef2ff;
  padding: 2px 8px;
  border-radius: 999px;
}
.dh-picker__actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.dh-select {
  width: 100%;
}
.dh-picker__hint {
  margin: 10px 0 0;
  font-size: 12px;
  color: var(--muted);
}

.dh-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}
.dh-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: 260px;
  padding: 6px 10px;
  border: 0;
  border-radius: 999px;
  cursor: pointer;
  color: #312e81;
  background: linear-gradient(180deg, #fff 0%, #eef2ff 100%);
  box-shadow: 0 6px 14px rgba(79, 70, 229, 0.14), inset 0 1px 0 #fff;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}
.dh-chip:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 18px rgba(79, 70, 229, 0.2);
}
.dh-chip__cd {
  font-weight: 800;
  font-size: 11px;
}
.dh-chip__name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
}
.dh-chip__x {
  font-size: 12px;
  color: #818cf8;
}

.dh-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  perspective: 1200px;
}

.dh-card {
  border-radius: 22px;
  overflow: hidden;
  background: #fff;
  transform-style: preserve-3d;
  transition: transform 0.28s ease, box-shadow 0.28s ease;
  animation: dh-card-in 0.55s ease both;
}
.dh-card--holiday {
  box-shadow: 0 16px 36px rgba(225, 29, 72, 0.16);
  animation-delay: 0.05s;
}
.dh-card--work {
  box-shadow: 0 16px 36px rgba(217, 119, 6, 0.16);
  animation-delay: 0.12s;
}
.dh-card:hover {
  transform: translateY(-8px) rotateX(3deg);
}
.dh-card--holiday:hover {
  box-shadow: 0 24px 44px rgba(225, 29, 72, 0.24);
}
.dh-card--work:hover {
  box-shadow: 0 24px 44px rgba(217, 119, 6, 0.24);
}

@keyframes dh-card-in {
  from {
    opacity: 0;
    transform: translateY(18px) rotateX(8deg);
  }
  to {
    opacity: 1;
    transform: translateY(0) rotateX(0);
  }
}

.dh-card__shine {
  position: absolute;
  inset: 0 auto auto 0;
  width: 140px;
  height: 140px;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.5), transparent 70%);
  pointer-events: none;
}
.dh-card__head {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  color: #fff;
}
.dh-card--holiday .dh-card__head {
  background: linear-gradient(135deg, #fb7185 0%, #e11d48 55%, #9f1239 100%);
}
.dh-card--work .dh-card__head {
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 50%, #d97706 100%);
}
.dh-card__badge {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.2);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.4);
}
.dh-card__head h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 800;
}
.dh-card__head p {
  margin: 2px 0 0;
  font-size: 11px;
  opacity: 0.88;
}
.dh-card__count {
  margin-left: auto;
  min-width: 36px;
  height: 28px;
  padding: 0 10px;
  display: grid;
  place-items: center;
  border-radius: 999px;
  font-weight: 800;
  background: rgba(255, 255, 255, 0.2);
}
.dh-card__body {
  padding: 14px;
}

.dh-add {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.dh-dates {
  flex: 1;
  min-width: 180px;
}
.dh-date-one {
  width: 150px;
}
.dh-reason {
  flex: 1;
  min-width: 120px;
}

.dh-date {
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.dh-wd {
  display: inline-flex;
  min-width: 28px;
  height: 22px;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 800;
}
.dh-wd.is-sun {
  color: #be123c;
  background: #ffe4e6;
}
.dh-wd.is-sat {
  color: #1d4ed8;
  background: #dbeafe;
}
.dh-wd.is-wd {
  color: #334155;
  background: #f1f5f9;
}

.dh-dest-cell {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}
.dh-dest-cell__cd {
  font-size: 11px;
  font-weight: 800;
  color: #4f46e5;
}
.dh-dest-cell__name {
  font-size: 12px;
  color: #475569;
}

.dh-table {
  border-radius: 12px;
  overflow: hidden;
}

:deep(.dh-card--holiday .el-button--danger:not(.is-plain)) {
  box-shadow: 0 8px 16px rgba(225, 29, 72, 0.28);
}
:deep(.dh-card--work .el-button--warning) {
  color: #fff;
  box-shadow: 0 8px 16px rgba(217, 119, 6, 0.28);
}
:deep(.el-button) {
  font-weight: 700;
  transition: transform 0.16s ease, box-shadow 0.16s ease;
}
:deep(.el-button:not(.is-disabled):hover) {
  transform: translateY(-1px);
}
:deep(.el-button:not(.is-disabled):active) {
  transform: translateY(1px);
}

@media (max-width: 980px) {
  .dh-grid,
  .dh-hero {
    display: block;
  }
  .dh-hero {
    transform: none;
  }
  .dh-hero__stats {
    margin-top: 12px;
  }
  .dh-card:hover {
    transform: translateY(-4px);
  }
}
</style>
