<template>
  <div class="iiws">
    <div class="iiws__bg" aria-hidden="true">
      <div class="iiws__orb iiws__orb--1" />
      <div class="iiws__orb iiws__orb--2" />
    </div>

    <header class="iiws-hero">
      <div class="iiws-hero__main">
        <div class="iiws-hero__icon">
          <el-icon :size="18"><Clock /></el-icon>
        </div>
        <div class="iiws-hero__text">
          <div class="iiws-hero__eyebrow">マスタ · 検査 · 仕上課</div>
          <h1 class="iiws-hero__title">検査員所定工時管理</h1>
        </div>
      </div>
      <div class="iiws-hero__chips">
        <span class="iiws-chip iiws-chip--sky">登録 <strong>{{ items.length }}</strong></span>
        <span class="iiws-chip">検査員 <strong>{{ uniqueInspectorCount }}</strong></span>
        <span class="iiws-chip iiws-chip--muted">未設定 {{ defaultHours }}h/日</span>
      </div>
      <div class="iiws-hero__actions">
        <div class="iiws-hero__filter">
          <el-icon class="iiws-hero__filter-ico"><Filter /></el-icon>
          <el-select
            v-model="filterInspectorId"
            placeholder="検査員"
            clearable
            filterable
            size="small"
            class="iiws-filter-select"
            @change="loadItems"
          >
            <el-option v-for="u in inspectorOptions" :key="u.id" :label="inspectorLabel(u)" :value="u.id" />
          </el-select>
        </div>
        <el-button class="iiws-btn-refresh" :icon="Refresh" :loading="loading" size="small" round @click="loadItems">
          更新
        </el-button>
      </div>
    </header>

    <div class="iiws-priority">
      <span class="iiws-priority__label">優先順</span>
      <span class="iiws-priority__step iiws-priority__step--1">指定日期</span>
      <el-icon class="iiws-priority__arrow"><ArrowRight /></el-icon>
      <span class="iiws-priority__step">指定时间</span>
      <el-icon class="iiws-priority__arrow"><ArrowRight /></el-icon>
      <span class="iiws-priority__step iiws-priority__step--def">デフォルト {{ defaultHours }}h</span>
      <span class="iiws-priority__hint">所定時間は勤務時間帯から自動計算</span>
    </div>

    <section class="iiws-card iiws-card--rise" v-loading="loading">
      <div v-if="canCreate" class="iiws-form">
        <div class="iiws-form__head">
          <span class="iiws-form__title"><el-icon><Plus /></el-icon>新規登録</span>
          <div class="iiws-mode-toggle">
            <button
              v-for="opt in ruleKindOptions"
              :key="opt.value"
              type="button"
              class="iiws-mode-toggle__btn"
              :class="{ 'is-active': newRuleKind === opt.value, [`is-${opt.value}`]: true }"
              @click="newRuleKind = opt.value"
            >
              {{ opt.label }}
            </button>
          </div>
        </div>

        <div class="iiws-form__toolbar">
          <div class="iiws-ctrl iiws-ctrl--inspector">
            <label class="iiws-ctrl__label">検査員</label>
            <div class="iiws-ctrl__shell">
              <el-select
                v-model="newInspectorIds"
                placeholder="複数選択可"
                filterable
                multiple
                collapse-tags
                collapse-tags-tooltip
                size="small"
                class="iiws-ctrl__input iiws-ctrl__input--select"
              >
                <el-option v-for="u in inspectorOptions" :key="u.id" :label="inspectorLabel(u)" :value="u.id" />
              </el-select>
              <div class="iiws-ctrl__actions">
                <button type="button" class="iiws-ctrl__link" @click="selectAllInspectors">全選択</button>
                <span class="iiws-ctrl__sep" />
                <button type="button" class="iiws-ctrl__link iiws-ctrl__link--muted" :disabled="!newInspectorIds.length" @click="clearInspectors">
                  クリア
                </button>
                <transition name="iiws-badge">
                  <span v-if="newInspectorIds.length" class="iiws-ctrl__badge">{{ newInspectorIds.length }}名</span>
                </transition>
              </div>
            </div>
          </div>

          <div class="iiws-ctrl iiws-ctrl--target">
            <label class="iiws-ctrl__label">{{ newRuleKind === 'date' ? '対象日' : '曜日' }}</label>
            <div class="iiws-ctrl__shell">
              <transition name="iiws-fade" mode="out-in">
                <el-date-picker
                  v-if="newRuleKind === 'date'"
                  key="date"
                  v-model="newDate"
                  type="date"
                  value-format="YYYY-MM-DD"
                  placeholder="日付"
                  size="small"
                  class="iiws-ctrl__input"
                />
                <el-select v-else key="weekday" v-model="newWeekday" size="small" class="iiws-ctrl__input" placeholder="曜日">
                  <el-option v-for="w in weekdayOptions" :key="w.value" :label="w.label" :value="w.value" />
                </el-select>
              </transition>
            </div>
          </div>

          <div class="iiws-ctrl iiws-ctrl--time">
            <label class="iiws-ctrl__label">勤務時間</label>
            <div class="iiws-ctrl__shell">
              <el-time-picker
                v-model="newTimeRange"
                is-range
                range-separator="～"
                start-placeholder="開始"
                end-placeholder="終了"
                format="HH:mm"
                value-format="HH:mm"
                size="small"
                class="iiws-ctrl__input iiws-ctrl__input--time"
              />
            </div>
          </div>

          <div class="iiws-ctrl iiws-ctrl--hours">
            <label class="iiws-ctrl__label">所定</label>
            <div class="iiws-hours iiws-ctrl__shell iiws-ctrl__shell--hours" :class="{ 'is-live': previewHours > 0 }">
              <transition name="iiws-hours-pop" mode="out-in">
                <strong :key="previewHours">{{ previewHours.toFixed(1) }}</strong>
              </transition>
              <span class="iiws-hours__unit">h</span>
            </div>
          </div>

          <div class="iiws-ctrl iiws-ctrl--note">
            <label class="iiws-ctrl__label">備考</label>
            <div class="iiws-ctrl__shell">
              <el-input v-model="newNote" placeholder="任意" size="small" class="iiws-ctrl__input" clearable />
            </div>
          </div>

          <div class="iiws-ctrl iiws-ctrl--submit">
            <label class="iiws-ctrl__label iiws-ctrl__label--ghost">操作</label>
            <el-button
              type="primary"
              size="small"
              class="iiws-submit"
              :loading="saving"
              :disabled="!canSubmit"
              @click="addEntry"
            >
              {{ addButtonLabel }}
            </el-button>
          </div>
        </div>

        <p class="iiws-form__hint">
          <el-icon><InfoFilled /></el-icon>
          <template v-if="newRuleKind === 'date'">特定日付の勤務時間帯（最優先）。複数検査員を一括登録できます。</template>
          <template v-else>曜日ごとの繰り返し設定（例：土曜 08:00～12:00）。複数検査員を一括登録できます。</template>
        </p>
      </div>

      <div v-if="canCreate" class="iiws-split">
        <span class="iiws-split__shine" />
      </div>

      <div class="iiws-table-area">
        <div class="iiws-table-head">
          <span class="iiws-table-head__title">登録一覧</span>
          <div class="iiws-table-head__tags">
            <span v-if="dateRuleCount" class="iiws-mini-tag iiws-mini-tag--date">日期 {{ dateRuleCount }}</span>
            <span v-if="timeRuleCount" class="iiws-mini-tag iiws-mini-tag--time">时间 {{ timeRuleCount }}</span>
          </div>
        </div>
        <div class="iiws-table-shell">
          <el-table
            :data="items"
            size="small"
            stripe
            class="iiws-table"
            empty-text="登録なし（未設定時は 7.6h/日）"
            :max-height="tableMaxHeight"
            :row-class-name="tableRowClass"
          >
            <el-table-column prop="inspector_name" label="検査員" min-width="100" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="iiws-name">{{ row.inspector_name || '—' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="モード" width="92" align="center">
              <template #default="{ row }">
                <span class="iiws-mode" :class="row.rule_kind === 'date' ? 'iiws-mode--date' : 'iiws-mode--time'">
                  {{ row.rule_kind_label || (row.rule_kind === 'date' ? '指定日期' : '指定时间') }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="対象" min-width="100">
              <template #default="{ row }">
                <span class="iiws-target">{{ row.target_label || row.schedule_date || row.weekday_label || '—' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="勤務時間" min-width="120">
              <template #default="{ row }">
                <span class="iiws-range">{{ row.time_range_label || '—' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="所定" width="72" align="center">
              <template #default="{ row }">
                <span class="iiws-hours-pill">{{ row.scheduled_hours.toFixed(1) }}<small>h</small></span>
              </template>
            </el-table-column>
            <el-table-column prop="note" label="備考" min-width="100" show-overflow-tooltip />
            <el-table-column v-if="canDelete" label="" width="44" align="center" fixed="right">
              <template #default="{ row }">
                <el-button link type="danger" size="small" class="iiws-del" :loading="row._deleting" @click="removeEntry(row)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </section>

    <footer class="iiws-foot">
      <router-link to="/mes/actual-analysis/utilization/inspection" class="iiws-foot__link">
        <el-icon><Link /></el-icon>稼働率分析へ
      </router-link>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ArrowRight, Clock, Delete, Filter, InfoFilled, Link, Plus, Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  batchCreateInspectionInspectorWorkSchedules,
  deleteInspectionInspectorWorkSchedule,
  fetchInspectionInspectorWorkScheduleDefaults,
  fetchInspectionInspectorWorkScheduleRuleKinds,
  fetchInspectionInspectorWorkSchedules,
  fetchInspectionInspectorWorkScheduleWeekdays,
  hoursFromTimeRange,
  type InspectionInspectorWorkScheduleItem,
  type InspectorWorkScheduleRuleKind,
} from '@/api/master/inspectionInspectorWorkSchedule'
import { getOrganizations, getUsers, type PaginatedUserResponse, type UserListItem } from '@/api/system'
import { useMasterOperationPermission } from '@/composables/useMasterOperationPermission'
import { guardMasterOperation } from '@/utils/masterOperationGuard'

defineOptions({ name: 'MasterInspectionInspectorWorkSchedule' })

/** 検査員候補は仕上課所属のみ */
const INSPECTION_SECTION_NAME = '仕上課'

type RowEx = InspectionInspectorWorkScheduleItem & { _deleting?: boolean }

const { canCreate, canDelete } = useMasterOperationPermission()

const loading = ref(false)
const saving = ref(false)
const defaultHours = ref(7.6)
const defaultStart = ref('08:00')
const defaultEnd = ref('15:36')
const items = ref<RowEx[]>([])
const inspectorOptions = ref<UserListItem[]>([])
const weekdayOptions = ref<{ value: number; label: string }[]>([])
const ruleKindOptions = ref<Array<{ label: string; value: InspectorWorkScheduleRuleKind }>>([
  { label: '指定日期', value: 'date' },
  { label: '指定时间', value: 'time' },
])
const filterInspectorId = ref<number | undefined>(undefined)
const newInspectorIds = ref<number[]>([])
const newRuleKind = ref<InspectorWorkScheduleRuleKind>('date')
const newWeekday = ref<number>(5)
const newDate = ref('')
const newTimeRange = ref<[string, string]>(['08:00', '15:36'])
const newNote = ref('')

const tableMaxHeight = 520

const previewHours = computed(() => hoursFromTimeRange(newTimeRange.value?.[0], newTimeRange.value?.[1]))

const dateRuleCount = computed(() => items.value.filter((r) => r.rule_kind === 'date').length)
const timeRuleCount = computed(() => items.value.filter((r) => r.rule_kind === 'time').length)
const uniqueInspectorCount = computed(() => new Set(items.value.map((r) => r.inspector_user_id)).size)

const canSubmit = computed(() => {
  if (!newInspectorIds.value.length) return false
  if (previewHours.value <= 0) return false
  if (newRuleKind.value === 'date' && !newDate.value) return false
  if (newRuleKind.value === 'time' && newWeekday.value == null) return false
  return true
})

const addButtonLabel = computed(() => {
  const n = newInspectorIds.value.length
  if (n > 1) return `一括追加（${n}名）`
  return '追加'
})

watch(newRuleKind, (kind) => {
  if (kind === 'time' && newWeekday.value == null) newWeekday.value = 5
})

function inspectorLabel(u: UserListItem): string {
  return (u.full_name || u.username || `ID:${u.id}`).trim()
}

function isShiageSectionUser(u: UserListItem): boolean {
  return (u.section || '').trim() === INSPECTION_SECTION_NAME
}

async function resolveShiageSectionId(): Promise<number | undefined> {
  try {
    const orgs = await getOrganizations()
    const section = (orgs ?? []).find((o) => o.type === 'section' && o.name === INSPECTION_SECTION_NAME)
    return section?.id
  } catch {
    return undefined
  }
}

async function loadInspectors() {
  try {
    const sectionId = await resolveShiageSectionId()
    const res = (await getUsers({
      page: 1,
      page_size: 500,
      status: 'active',
      section_id: sectionId,
    })) as unknown as PaginatedUserResponse
    let list = res.items ?? []
    list = list.filter(isShiageSectionUser)
    inspectorOptions.value = list
    const allowed = new Set(list.map((u) => u.id))
    newInspectorIds.value = newInspectorIds.value.filter((id) => allowed.has(id))
    if (filterInspectorId.value != null && !allowed.has(filterInspectorId.value)) {
      filterInspectorId.value = undefined
      await loadItems()
    }
  } catch {
    inspectorOptions.value = []
    newInspectorIds.value = []
  }
}

async function loadMeta() {
  try {
    const [wd, kinds, defs] = await Promise.all([
      fetchInspectionInspectorWorkScheduleWeekdays(),
      fetchInspectionInspectorWorkScheduleRuleKinds(),
      fetchInspectionInspectorWorkScheduleDefaults(),
    ])
    weekdayOptions.value = wd ?? []
    if (kinds?.length) {
      ruleKindOptions.value = kinds.map((k) => ({ label: k.label, value: k.value }))
    }
    defaultHours.value = defs?.data?.default_scheduled_hours ?? 7.6
    defaultStart.value = defs?.data?.default_work_start_time ?? '08:00'
    defaultEnd.value = defs?.data?.default_work_end_time ?? '15:36'
    newTimeRange.value = [defaultStart.value, defaultEnd.value]
  } catch {
    weekdayOptions.value = [
      { value: 5, label: '土曜' },
      { value: 6, label: '日曜' },
    ]
  }
}

async function loadItems() {
  loading.value = true
  try {
    const res = await fetchInspectionInspectorWorkSchedules({
      inspector_user_id: filterInspectorId.value,
    })
    items.value = res?.data?.items ?? []
  } catch (e: unknown) {
    items.value = []
    ElMessage.error(e instanceof Error ? e.message : '一覧の取得に失敗しました')
  } finally {
    loading.value = false
  }
}

function selectAllInspectors() {
  newInspectorIds.value = inspectorOptions.value.map((u) => u.id)
}

function clearInspectors() {
  newInspectorIds.value = []
}

function tableRowClass({ rowIndex }: { rowIndex: number }) {
  return `iiws-row iiws-row--${rowIndex % 2 === 0 ? 'even' : 'odd'}`
}

function isDuplicateRule(row: RowEx, inspectorId: number): boolean {
  if (row.inspector_user_id !== inspectorId) return false
  if (newRuleKind.value === 'date') {
    return row.rule_kind === 'date' && row.schedule_date === newDate.value
  }
  return row.rule_kind === 'time' && row.weekday === newWeekday.value
}

function findDuplicateInspectorIds(): number[] {
  const selected = new Set(newInspectorIds.value)
  const dupes = new Set<number>()
  for (const row of items.value) {
    if (!selected.has(row.inspector_user_id)) continue
    if (isDuplicateRule(row, row.inspector_user_id)) dupes.add(row.inspector_user_id)
  }
  return [...dupes]
}

function formatInspectorNameList(names: string[]): string {
  if (!names.length) return ''
  if (names.length <= 4) return names.join('、')
  return `${names.slice(0, 4).join('、')} 他${names.length - 4}名`
}

function duplicateNamesFromIds(ids: number[]): string[] {
  return ids.map((id) => {
    const u = inspectorOptions.value.find((o) => o.id === id)
    return u ? inspectorLabel(u) : `ID:${id}`
  })
}

function notifyBatchResult(
  created: number,
  skipped: number,
  failed: number,
  skippedNames: string[] = [],
) {
  const dupLabel = formatInspectorNameList(skippedNames)

  if (created > 0 && skipped > 0) {
    ElMessage.success(`新規 ${created} 件を登録しました`)
    ElMessage.warning(
      dupLabel
        ? `重複データ ${skipped} 件は登録しませんでした：${dupLabel}`
        : `重複データ ${skipped} 件は登録しませんでした`,
    )
    return
  }

  if (created > 0) {
    if (failed > 0) {
      ElMessage.warning(`登録 ${created} 件（無効ユーザー ${failed} 件は除外）`)
    } else {
      ElMessage.success(created === 1 ? '登録しました' : `登録しました（${created} 件）`)
    }
    return
  }

  if (skipped > 0) {
    ElMessage.warning(
      dupLabel
        ? `すべて重複のため登録されませんでした：${dupLabel}`
        : 'すべて重複のため登録されませんでした',
    )
    return
  }

  ElMessage.error('登録できませんでした')
}

async function addEntry() {
  if (!guardMasterOperation(canCreate)) return
  if (!canSubmit.value || !newInspectorIds.value.length) return
  const [start, end] = newTimeRange.value ?? []
  const payload = {
    rule_kind: newRuleKind.value,
    schedule_date: newRuleKind.value === 'date' ? newDate.value : undefined,
    weekday: newRuleKind.value === 'time' ? newWeekday.value : undefined,
    work_start_time: start,
    work_end_time: end,
    scheduled_hours: previewHours.value,
    note: newNote.value || undefined,
  }

  const localDupes = findDuplicateInspectorIds()
  const allLocalDupes =
    localDupes.length > 0 &&
    localDupes.length === newInspectorIds.value.length &&
    !filterInspectorId.value
  if (allLocalDupes) {
    const names = duplicateNamesFromIds(localDupes)
    ElMessage.warning(`すべて重複のため登録されませんでした：${formatInspectorNameList(names)}`)
    return
  }

  saving.value = true
  try {
    const res = await batchCreateInspectionInspectorWorkSchedules({
      inspector_user_ids: newInspectorIds.value,
      ...payload,
    })
    if (!res?.success) {
      ElMessage.error(res?.message || '登録に失敗しました')
      return
    }
    const created = res.created ?? 0
    const skipped = res.skipped ?? 0
    const failed = res.failed ?? 0
    const skippedNames = res.skipped_inspector_names ?? []

    notifyBatchResult(created, skipped, failed, skippedNames)

    if (created > 0) {
      newNote.value = ''
      await loadItems()
    }
  } catch (e: unknown) {
    ElMessage.error(e instanceof Error ? e.message : '登録に失敗しました')
  } finally {
    saving.value = false
  }
}

async function removeEntry(row: RowEx) {
  if (!guardMasterOperation(canDelete)) return
  try {
    await ElMessageBox.confirm('このルールを削除しますか？', '確認', { type: 'warning' })
  } catch {
    return
  }
  row._deleting = true
  try {
    await deleteInspectionInspectorWorkSchedule(row.id)
    ElMessage.success('削除しました')
    await loadItems()
  } catch (e: unknown) {
    ElMessage.error(e instanceof Error ? e.message : '削除に失敗しました')
  } finally {
    row._deleting = false
  }
}

onMounted(async () => {
  await Promise.all([loadInspectors(), loadMeta()])
  await loadItems()
})
</script>

<style scoped>
.iiws {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px 10px 12px;
  min-height: 0;
}

.iiws__bg {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  z-index: 0;
}

.iiws__orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(48px);
  opacity: 0.45;
}

.iiws__orb--1 {
  width: 220px;
  height: 220px;
  top: -60px;
  right: 8%;
  background: radial-gradient(circle, rgba(56, 189, 248, 0.35), transparent 70%);
}

.iiws__orb--2 {
  width: 180px;
  height: 180px;
  bottom: 10%;
  left: -40px;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.2), transparent 70%);
}

.iiws-hero,
.iiws-priority,
.iiws-card,
.iiws-foot {
  position: relative;
  z-index: 1;
}

.iiws-hero {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  padding: 8px 12px;
  border-radius: 12px;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 55%, #f0f9ff 100%);
  border: 1px solid rgba(148, 163, 184, 0.28);
  box-shadow: 0 2px 12px rgba(15, 23, 42, 0.05);
}

.iiws-hero__main {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.iiws-hero__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  color: #fff;
  background: linear-gradient(145deg, #38bdf8, #0284c7);
  box-shadow: 0 4px 12px rgba(2, 132, 199, 0.28);
  flex-shrink: 0;
}

.iiws-hero__eyebrow {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #0284c7;
  line-height: 1.2;
}

.iiws-hero__title {
  margin: 0;
  font-size: 15px;
  font-weight: 800;
  color: #0f172a;
  line-height: 1.25;
}

.iiws-hero__chips {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  flex: 1;
}

.iiws-chip {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  color: #475569;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  white-space: nowrap;
}

.iiws-chip strong {
  font-weight: 800;
  color: #0f172a;
}

.iiws-chip--sky {
  color: #0369a1;
  background: #e0f2fe;
  border-color: #bae6fd;
}

.iiws-chip--muted {
  color: #64748b;
  background: transparent;
  border-color: #e2e8f0;
}

.iiws-hero__actions {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
}

.iiws-hero__filter {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 6px 2px 8px;
  border-radius: 8px;
  background: #fff;
  border: 1px solid #e2e8f0;
}

.iiws-hero__filter-ico {
  font-size: 13px;
  color: #94a3b8;
}

.iiws-filter-select {
  width: 148px;
}

.iiws-filter-select :deep(.el-select__wrapper) {
  box-shadow: none !important;
  background: transparent;
  padding-left: 0;
}

.iiws-btn-refresh {
  --el-button-bg-color: #fff;
}

.iiws-priority {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  padding: 5px 10px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid #e2e8f0;
  font-size: 11px;
}

.iiws-priority__label {
  font-weight: 700;
  color: #64748b;
  margin-right: 2px;
}

.iiws-priority__step {
  padding: 2px 8px;
  border-radius: 6px;
  font-weight: 600;
  color: #334155;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.iiws-priority__step--1 {
  color: #b45309;
  background: #fffbeb;
  border-color: #fde68a;
}

.iiws-priority__step--def {
  color: #0369a1;
  background: #f0f9ff;
  border-color: #bae6fd;
}

.iiws-priority__arrow {
  font-size: 10px;
  color: #cbd5e1;
}

.iiws-priority__hint {
  margin-left: auto;
  color: #94a3b8;
  font-size: 10px;
}

.iiws-card {
  border-radius: 14px;
  background: linear-gradient(165deg, #ffffff 0%, #f8fafc 48%, #f1f5f9 100%);
  border: 1px solid rgba(148, 163, 184, 0.35);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 8px 24px rgba(15, 23, 42, 0.07),
    0 2px 6px rgba(15, 23, 42, 0.04);
  overflow: hidden;
}

.iiws-card--rise {
  animation: iiws-rise 0.45s cubic-bezier(0.22, 1, 0.36, 1) both;
}

@keyframes iiws-rise {
  from {
    opacity: 0;
    transform: translateY(10px) scale(0.995);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.iiws-form {
  padding: 10px 12px 8px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.92) 0%, rgba(248, 250, 252, 0.6) 100%),
    radial-gradient(ellipse 80% 60% at 10% 0%, rgba(56, 189, 248, 0.06), transparent 55%);
}

.iiws-form__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
}

.iiws-form__title {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  font-weight: 800;
  color: #1e293b;
  letter-spacing: 0.01em;
}

.iiws-form__title .el-icon {
  font-size: 14px;
  color: #0284c7;
  filter: drop-shadow(0 1px 2px rgba(2, 132, 199, 0.25));
}

.iiws-mode-toggle {
  display: inline-flex;
  padding: 3px;
  border-radius: 10px;
  background: linear-gradient(180deg, #e2e8f0, #f1f5f9);
  border: 1px solid #cbd5e1;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.06) inset,
    0 2px 6px rgba(15, 23, 42, 0.04);
}

.iiws-mode-toggle__btn {
  border: none;
  background: transparent;
  padding: 4px 14px;
  border-radius: 7px;
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
  cursor: pointer;
  transition: all 0.22s cubic-bezier(0.22, 1, 0.36, 1);
  white-space: nowrap;
}

.iiws-mode-toggle__btn:hover:not(.is-active) {
  color: #334155;
  background: rgba(255, 255, 255, 0.55);
}

.iiws-mode-toggle__btn.is-active {
  color: #fff;
  box-shadow:
    0 2px 8px rgba(15, 23, 42, 0.12),
    0 1px 0 rgba(255, 255, 255, 0.25) inset;
  transform: translateY(-1px);
}

.iiws-mode-toggle__btn.is-active.is-date {
  background: linear-gradient(145deg, #fbbf24, #d97706);
}

.iiws-mode-toggle__btn.is-active.is-time {
  background: linear-gradient(145deg, #38bdf8, #0284c7);
}

.iiws-form__toolbar {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  flex-wrap: wrap;
}

.iiws-ctrl {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.iiws-ctrl--inspector {
  flex: 2.4 1 220px;
}

.iiws-ctrl--target {
  flex: 1 1 128px;
}

.iiws-ctrl--time {
  flex: 1.3 1 200px;
}

.iiws-ctrl--hours {
  flex: 0 0 76px;
}

.iiws-ctrl--note {
  flex: 1 1 120px;
}

.iiws-ctrl--submit {
  flex: 0 0 92px;
}

.iiws-ctrl__label {
  font-size: 10px;
  font-weight: 800;
  color: #94a3b8;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  line-height: 1;
  padding-left: 2px;
}

.iiws-ctrl__label--ghost {
  visibility: hidden;
}

.iiws-ctrl__shell {
  display: flex;
  align-items: center;
  min-height: 32px;
  height: 32px;
  padding: 0 2px;
  border-radius: 10px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  border: 1px solid #dbe3ee;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 2px 6px rgba(15, 23, 42, 0.05),
    0 1px 2px rgba(15, 23, 42, 0.04);
  transition:
    border-color 0.2s ease,
    box-shadow 0.25s ease,
    transform 0.2s ease;
}

.iiws-ctrl__shell:hover {
  border-color: #93c5fd;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 4px 14px rgba(56, 189, 248, 0.1);
}

.iiws-ctrl__shell:focus-within {
  border-color: #38bdf8;
  box-shadow:
    0 0 0 3px rgba(56, 189, 248, 0.14),
    0 4px 16px rgba(2, 132, 199, 0.12),
    0 1px 0 rgba(255, 255, 255, 0.95) inset;
  transform: translateY(-1px);
}

.iiws-ctrl--inspector .iiws-ctrl__shell {
  padding-right: 6px;
  gap: 4px;
}

.iiws-ctrl__shell--hours {
  justify-content: center;
  gap: 2px;
  padding: 0 10px;
  background: linear-gradient(145deg, #e0f2fe 0%, #f0f9ff 55%, #ffffff 100%);
  border-color: #7dd3fc;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 3px 10px rgba(2, 132, 199, 0.14);
}

.iiws-ctrl__shell--hours.is-live {
  animation: iiws-hours-glow 2.4s ease-in-out infinite;
}

@keyframes iiws-hours-glow {
  0%,
  100% {
    box-shadow:
      0 1px 0 rgba(255, 255, 255, 0.9) inset,
      0 3px 10px rgba(2, 132, 199, 0.14);
  }
  50% {
    box-shadow:
      0 1px 0 rgba(255, 255, 255, 0.9) inset,
      0 4px 16px rgba(2, 132, 199, 0.22);
  }
}

.iiws-ctrl__input {
  flex: 1;
  min-width: 0;
  width: 100%;
}

.iiws-ctrl__input :deep(.el-input__wrapper),
.iiws-ctrl__input :deep(.el-select__wrapper) {
  min-height: 28px !important;
  height: 28px !important;
  box-shadow: none !important;
  background: transparent !important;
  border: none !important;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
}

.iiws-ctrl__input--select {
  flex: 1;
  min-width: 0;
}

.iiws-ctrl__input--time {
  width: 100%;
}

.iiws-ctrl__input--time :deep(.el-range-editor) {
  width: 100% !important;
  box-shadow: none !important;
  background: transparent !important;
  border: none !important;
  padding: 0 4px !important;
}

.iiws-ctrl__actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
  padding-left: 4px;
  border-left: 1px solid #e2e8f0;
}

.iiws-ctrl__link {
  border: none;
  background: none;
  padding: 2px 4px;
  font-size: 10px;
  font-weight: 700;
  color: #0284c7;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.15s ease, color 0.15s ease;
}

.iiws-ctrl__link:hover:not(:disabled) {
  background: #e0f2fe;
}

.iiws-ctrl__link--muted {
  color: #94a3b8;
}

.iiws-ctrl__link:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.iiws-ctrl__sep {
  width: 1px;
  height: 12px;
  background: #e2e8f0;
}

.iiws-ctrl__badge {
  font-size: 10px;
  font-weight: 800;
  color: #0369a1;
  padding: 2px 7px;
  border-radius: 999px;
  background: linear-gradient(180deg, #fff, #e0f2fe);
  border: 1px solid #bae6fd;
  box-shadow: 0 1px 3px rgba(2, 132, 199, 0.12);
}

.iiws-hours {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 1px;
  width: 100%;
}

.iiws-hours strong {
  font-size: 15px;
  font-weight: 900;
  color: #0369a1;
  font-variant-numeric: tabular-nums;
  line-height: 1;
  min-width: 2.4em;
  text-align: center;
}

.iiws-hours__unit {
  font-size: 10px;
  font-weight: 800;
  color: #0284c7;
}

.iiws-hours-pop-enter-active,
.iiws-hours-pop-leave-active {
  transition: all 0.22s cubic-bezier(0.22, 1, 0.36, 1);
}

.iiws-hours-pop-enter-from {
  opacity: 0;
  transform: translateY(4px) scale(0.9);
}

.iiws-hours-pop-leave-to {
  opacity: 0;
  transform: translateY(-4px) scale(1.05);
}

.iiws-badge-enter-active,
.iiws-badge-leave-active {
  transition: all 0.2s ease;
}

.iiws-badge-enter-from,
.iiws-badge-leave-to {
  opacity: 0;
  transform: scale(0.85);
}

.iiws-fade-enter-active,
.iiws-fade-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.iiws-fade-enter-from,
.iiws-fade-leave-to {
  opacity: 0;
  transform: translateX(6px);
}

.iiws-submit {
  width: 100%;
  height: 32px !important;
  font-weight: 800;
  border-radius: 10px !important;
  border: none !important;
  background: linear-gradient(145deg, #38bdf8, #0284c7) !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.25) inset,
    0 4px 14px rgba(2, 132, 199, 0.35) !important;
  transition: transform 0.2s ease, box-shadow 0.2s ease !important;
}

.iiws-submit:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.25) inset,
    0 6px 20px rgba(2, 132, 199, 0.42) !important;
}

.iiws-submit:active:not(:disabled) {
  transform: translateY(0);
}

.iiws-form__hint {
  display: flex;
  align-items: center;
  gap: 5px;
  margin: 7px 0 0;
  padding: 5px 8px;
  border-radius: 8px;
  font-size: 10px;
  color: #64748b;
  line-height: 1.35;
  background: rgba(241, 245, 249, 0.7);
  border: 1px solid rgba(226, 232, 240, 0.8);
}

.iiws-form__hint .el-icon {
  font-size: 12px;
  color: #94a3b8;
  flex-shrink: 0;
}

.iiws-split {
  position: relative;
  height: 1px;
  margin: 0 12px;
  background: linear-gradient(90deg, transparent, #cbd5e1 15%, #cbd5e1 85%, transparent);
}

.iiws-split__shine {
  position: absolute;
  top: -1px;
  left: 20%;
  width: 30%;
  height: 3px;
  border-radius: 2px;
  background: linear-gradient(90deg, transparent, rgba(56, 189, 248, 0.35), transparent);
  animation: iiws-shine 3s ease-in-out infinite;
}

@keyframes iiws-shine {
  0%,
  100% {
    opacity: 0.3;
    transform: translateX(-20%);
  }
  50% {
    opacity: 1;
    transform: translateX(120%);
  }
}

.iiws-table-area {
  padding: 8px 10px 10px;
}

.iiws-table-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
  padding: 0 4px;
}

.iiws-table-head__title {
  font-size: 12px;
  font-weight: 800;
  color: #334155;
}

.iiws-table-head__tags {
  display: flex;
  gap: 5px;
}

.iiws-mini-tag {
  font-size: 10px;
  font-weight: 800;
  padding: 2px 8px;
  border-radius: 999px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
}

.iiws-mini-tag--date {
  color: #b45309;
  background: linear-gradient(180deg, #fffbeb, #fef3c7);
  border: 1px solid #fde68a;
}

.iiws-mini-tag--time {
  color: #0369a1;
  background: linear-gradient(180deg, #f0f9ff, #e0f2fe);
  border: 1px solid #bae6fd;
}

.iiws-table-shell {
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
  background: #fff;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 4px 16px rgba(15, 23, 42, 0.05);
}

.iiws-table {
  --el-table-border-color: #eef2f6;
}

.iiws-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.iiws-table :deep(.el-table__header th) {
  font-size: 11px;
  font-weight: 800;
  color: #64748b;
  letter-spacing: 0.03em;
  background: linear-gradient(180deg, #f8fafc, #f1f5f9) !important;
  padding: 6px 0;
  border-bottom: 1px solid #e2e8f0 !important;
}

.iiws-table :deep(.el-table__body td) {
  padding: 5px 0;
  font-size: 12px;
  border-bottom-color: #f1f5f9 !important;
}

.iiws-table :deep(.el-table__row) {
  transition: background 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
}

.iiws-table :deep(.iiws-row:hover > td) {
  background: linear-gradient(90deg, #f0f9ff, #f8fafc) !important;
}

.iiws-table :deep(.iiws-row:hover) {
  transform: scale(1.002);
}

.iiws-name {
  font-weight: 700;
  color: #1e293b;
}

.iiws-mode {
  display: inline-block;
  font-size: 10px;
  font-weight: 800;
  padding: 3px 8px;
  border-radius: 7px;
  line-height: 1.2;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
  transition: transform 0.15s ease;
}

.iiws-table :deep(.iiws-row:hover) .iiws-mode {
  transform: translateY(-1px);
}

.iiws-mode--date {
  color: #b45309;
  background: linear-gradient(180deg, #fffbeb, #fef3c7);
  border: 1px solid #fde68a;
}

.iiws-mode--time {
  color: #0369a1;
  background: linear-gradient(180deg, #f0f9ff, #e0f2fe);
  border: 1px solid #bae6fd;
}

.iiws-target {
  font-weight: 700;
  color: #334155;
  font-variant-numeric: tabular-nums;
}

.iiws-range {
  font-variant-numeric: tabular-nums;
  color: #475569;
  font-weight: 500;
}

.iiws-hours-pill {
  display: inline-flex;
  align-items: baseline;
  justify-content: center;
  min-width: 48px;
  padding: 3px 8px;
  border-radius: 8px;
  font-weight: 900;
  font-variant-numeric: tabular-nums;
  font-size: 12px;
  color: #0369a1;
  background: linear-gradient(180deg, #e0f2fe, #f0f9ff);
  border: 1px solid #bae6fd;
  box-shadow: 0 1px 4px rgba(2, 132, 199, 0.12);
}

.iiws-hours-pill small {
  font-size: 9px;
  font-weight: 700;
  margin-left: 1px;
}

.iiws-del {
  padding: 2px;
  transition: transform 0.15s ease;
}

.iiws-del:hover {
  transform: scale(1.15);
}

.iiws-foot {
  display: flex;
  justify-content: flex-end;
  padding: 0 2px;
}

.iiws-foot__link {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
  font-weight: 600;
  color: #2563eb;
  text-decoration: none;
}

.iiws-foot__link:hover {
  color: #1d4ed8;
  text-decoration: underline;
}

@media (max-width: 1200px) {
  .iiws-form__toolbar {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    align-items: end;
  }

  .iiws-ctrl--inspector {
    grid-column: 1 / -1;
  }

  .iiws-ctrl--submit {
    grid-column: 1 / -1;
  }

  .iiws-ctrl--hours {
    flex: none;
  }
}

@media (max-width: 720px) {
  .iiws-hero__chips {
    width: 100%;
    order: 3;
  }

  .iiws-hero__actions {
    width: 100%;
    margin-left: 0;
  }

  .iiws-priority__hint {
    width: 100%;
    margin-left: 0;
  }

  .iiws-form__toolbar {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
