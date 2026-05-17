<script setup lang="ts">
import {
  computed,
  nextTick,
  onMounted,
  onUnmounted,
  reactive,
  ref,
  watch,
  type ComponentPublicInstance,
} from 'vue'
import Sortable from 'sortablejs'
import type { SortableEvent } from 'sortablejs'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  RefreshRight,
  VideoPause,
  VideoPlay,
  CircleCheck,
  DataLine,
  Calendar,
  Edit,
  Camera,
  User,
  Clock,
  InfoFilled,
  RefreshLeft,
  SetUp,
  Rank,
  ArrowLeft,
  ArrowRight,
} from '@element-plus/icons-vue'
import MesBarcodeScanDialog from './MesBarcodeScanDialog.vue'
import ScanRegisteredHint from './ScanRegisteredHint.vue'
import {
  fetchCuttingManagementList,
  patchCuttingManagement,
  reorderCuttingManagement,
  splitCuttingManagementToNextDay,
  type CuttingManagementListRow,
  type PatchCuttingManagementBody,
} from '@/api/cuttingManagement'
import { fetchCuttingPlanningMachines, type CuttingPlanningMachine } from '@/api/cuttingPlanning'
import { getUsers, type PaginatedUserResponse, type UserListItem } from '@/api/system'
import { setLocale, type LocaleType } from '@/i18n'
import { formatDateTimeJST, getJSTToday, localeForIntl } from '@/utils/dateFormat'
import {
  applyPersistedSessionsForScope,
  flushPauseSlice,
  freezePausedAccumMs,
  hydratePlanSessionFromRow,
  loadCuttingActualPersist,
  makePersistScopeKey,
  reconcileInProgressTimer,
  saveCuttingActualPersist,
  serializePlanSessions,
} from './cuttingActualPersist'
import {
  flushOfflinePatchQueue,
  getOfflineQueueCount,
  isNetworkOrServerDownError,
  enqueueOfflinePatch,
} from './cuttingActualOfflineSync'

defineOptions({ name: 'CuttingActualDataCollection' })

const { t, locale } = useI18n()

/** 計画1件ごとの画面状態（MES 実績の一部は cutting_management に同期） */
interface PlanSession {
  activeAccumMs: number
  runningSliceStart: number | null
  pausedAccumMs: number
  pauseSliceStart: number | null
  wallStart: number | null
  wallEnd: number | null
  operatorUserId: number | null
  setupTimeMin: number | undefined
}

function emptySession(): PlanSession {
  return {
    activeAccumMs: 0,
    runningSliceStart: null,
    pausedAccumMs: 0,
    pauseSliceStart: null,
    wallStart: null,
    wallEnd: null,
    operatorUserId: null,
    setupTimeMin: undefined,
  }
}

/** 生産日（YYYY-MM-DD） */
const productionDay = ref(getJSTToday())

function shiftProductionDay(deltaDays: number): void {
  const base = (productionDay.value ?? '').trim().slice(0, 10)
  const anchor = /^\d{4}-\d{2}-\d{2}$/.test(base) ? base : getJSTToday()
  productionDay.value = shiftDateYmd(anchor, deltaDays)
}

function setProductionDayToday(): void {
  productionDay.value = getJSTToday()
}

const selectedMachineId = ref<number | null>(null)
/** タブレット/スマホでは filterable オフ（タップでソフトキーボードを出さない） */
const machineSelectFilterable = ref(true)
let machineSelectTouchMq: MediaQueryList | null = null

function syncMachineSelectFilterable(): void {
  if (typeof window === 'undefined') return
  machineSelectFilterable.value = !window.matchMedia('(hover: none) and (pointer: coarse)').matches
}

function onMachineSelectVisibleChange(): void {
  if (machineSelectFilterable.value) return
  nextTick(() => {
    const ae = document.activeElement
    if (ae instanceof HTMLInputElement) ae.blur()
  })
}

const hideCompleted = ref(true)
const localeUi = ref<LocaleType>((locale.value as LocaleType) || 'ja')

const machines = ref<CuttingPlanningMachine[]>([])
const managementRows = ref<CuttingManagementListRow[]>([])
const operators = ref<UserListItem[]>([])

const loadingMachines = ref(false)
const loadingPlans = ref(false)
const loadingUsers = ref(false)

type CuttingMgmtRow = CuttingManagementListRow & { id: number }

const sessions = reactive<Record<number, PlanSession>>({})
const tickNow = ref(Date.now())
let tickTimer: ReturnType<typeof setInterval> | null = null
let persistTimer: ReturnType<typeof setTimeout> | null = null
let runningPersistTimer: ReturnType<typeof setInterval> | null = null
let mesSyncTimer: ReturnType<typeof setInterval> | null = null
let mesSyncInFlight = false
/** 自端末で操作直後はサーバー同期で上書きしない（ミリ秒） */
const localMesEchoUntil = new Map<number, number>()
const MES_SYNC_INTERVAL_MS = 4000
/** マウント時の設備・生産日復元中は watch で空 sessions を永続化しない */
const skipScopeSessionReset = ref(false)

const isBrowserOffline = ref(typeof navigator !== 'undefined' ? !navigator.onLine : false)
const offlineQueueCount = ref(0)
let flushingOfflineQueue = false

function refreshOfflineQueueCount(): void {
  offlineQueueCount.value = getOfflineQueueCount()
}

function currentScopeKey(): string {
  return makePersistScopeKey((productionDay.value ?? '').trim(), selectedMachineId.value)
}

/** PATCH：失敗時はオフラインキューへ。計測はローカルで継続 */
async function patchWithOfflineSync(
  planId: number,
  body: PatchCuttingManagementBody,
  options?: { silentQueue?: boolean },
): Promise<boolean> {
  if (!navigator.onLine) {
    enqueueOfflinePatch(currentScopeKey(), planId, body)
    refreshOfflineQueueCount()
    if (!options?.silentQueue) {
      ElMessage.warning(t('mesCuttingActual.offlineQueued'))
    }
    return false
  }
  try {
    const res = await patchCuttingManagement(planId, body)
    if (res && res.success === false) {
      if (!options?.silentQueue) {
        ElMessage.warning(res.message || t('mesCuttingActual.saveFailed'))
      }
      return false
    }
    return true
  } catch (e: unknown) {
    if (isNetworkOrServerDownError(e)) {
      enqueueOfflinePatch(currentScopeKey(), planId, body)
      refreshOfflineQueueCount()
      if (!options?.silentQueue) {
        ElMessage.warning(t('mesCuttingActual.offlineQueued'))
      }
      return false
    }
    throw e
  }
}

async function tryFlushOfflineQueue(options?: { reloadAfter?: boolean }): Promise<void> {
  if (flushingOfflineQueue || !navigator.onLine) return
  if (getOfflineQueueCount() === 0) return
  flushingOfflineQueue = true
  try {
    const { ok, fail } = await flushOfflinePatchQueue(patchCuttingManagement)
    refreshOfflineQueueCount()
    if (ok > 0) {
      ElMessage.success(t('mesCuttingActual.offlineSyncOk', { n: ok }))
      if (options?.reloadAfter && selectedMachineId.value != null) {
        await loadPlans()
      }
    }
    if (fail > 0) {
      ElMessage.warning(t('mesCuttingActual.offlineSyncPartial'))
    }
  } finally {
    flushingOfflineQueue = false
  }
}

function onBrowserOnline(): void {
  isBrowserOffline.value = false
  void tryFlushOfflineQueue({ reloadAfter: true })
}

function onBrowserOffline(): void {
  isBrowserOffline.value = true
}

/** 切替前に旧 scope へ保存するため、引数で日付・設備 ID を指定可能 */
function flushPersistToStorage(
  scopeMachineId: number | null = selectedMachineId.value,
  scopeDay: string = (productionDay.value ?? '').trim(),
): void {
  try {
    const canSaveSessions = scopeMachineId != null && /^\d{4}-\d{2}-\d{2}$/.test(scopeDay)
    saveCuttingActualPersist({
      productionDay: scopeDay,
      selectedMachineId: scopeMachineId,
      hideCompleted: hideCompleted.value,
      sessions: canSaveSessions ? serializePlanSessions(sessions) : {},
    })
  } catch (e) {
    console.warn(e)
  }
}

function schedulePersistToStorage(): void {
  if (persistTimer) clearTimeout(persistTimer)
  persistTimer = setTimeout(flushPersistToStorage, 350)
}

function clearSessions() {
  for (const k of Object.keys(sessions)) {
    delete sessions[Number(k)]
  }
}

watch(productionDay, async (newDay, oldDay) => {
  if (skipScopeSessionReset.value) return
  if (newDay === oldDay) return
  const prevMachine = selectedMachineId.value
  if (oldDay && prevMachine != null) {
    flushPersistToStorage(prevMachine, String(oldDay).trim())
  }
  managementRows.value = []
  clearSessions()
  if (selectedMachineId.value != null) {
    await loadPlans()
  }
})

watch(selectedMachineId, async (newId, oldId) => {
  if (skipScopeSessionReset.value) return
  if (newId === oldId) return
  const day = (productionDay.value ?? '').trim()
  if (oldId != null && day) {
    flushPersistToStorage(oldId, day)
  }
  managementRows.value = []
  clearSessions()
  if (newId != null) {
    await loadPlans()
  }
})

watch(hideCompleted, schedulePersistToStorage)

watch(sessions, schedulePersistToStorage, { deep: true })

watch(localeUi, (v) => setLocale(v))

watch(
  () => locale.value,
  (v) => {
    if (v === 'en' || v === 'ja' || v === 'zh' || v === 'vi') localeUi.value = v
  },
)

const intlLocale = computed(() => localeForIntl(locale.value))

const showOfflineAlert = computed(() => isBrowserOffline.value || offlineQueueCount.value > 0)

const offlineAlertText = computed(() => {
  if (isBrowserOffline.value) return t('mesCuttingActual.offlineBanner')
  return t('mesCuttingActual.offlinePendingSync', { n: offlineQueueCount.value })
})

const selectedMachineName = computed((): string | null => {
  const id = selectedMachineId.value
  if (id == null) return null
  const m = machines.value.find((x) => x.id === id)
  const name = (m?.machine_name ?? '').trim()
  return name || null
})

/** 設備名またはコードに「外注」を含むものは本画面の選択肢から除外 */
function cuttingMachineHasGaichu(m: CuttingPlanningMachine): boolean {
  const name = m.machine_name ?? ''
  const cd = m.machine_cd ?? ''
  return name.includes('外注') || cd.includes('外注')
}

/** 切断設備プルダウン用（外注除外・API 生データは machines をそのまま保持） */
const cuttingMachinesForSelect = computed(() => machines.value.filter((m) => !cuttingMachineHasGaichu(m)))

watch(cuttingMachinesForSelect, (list) => {
  const id = selectedMachineId.value
  if (id != null && !list.some((x) => x.id === id)) selectedMachineId.value = null
})

/** API の production_day を YYYY-MM-DD に正規化（欠損は '—'） */
function normalizeProductionDayKey(val: string | null | undefined): string {
  if (val == null || String(val).trim() === '') return '—'
  const s = String(val).trim()
  if (/^\d{4}-\d{2}-\d{2}/.test(s)) return s.slice(0, 10)
  return s.slice(0, 10) || '—'
}

/** グループ見出し用の日付表示 */
function formatGroupDayLabel(dayKey: string): string {
  if (dayKey === '—') return t('mesCuttingActual.noProductionDay')
  const m = dayKey.match(/^(\d{4})-(\d{2})-(\d{2})$/)
  if (!m) return dayKey
  const d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]))
  try {
    return new Intl.DateTimeFormat(intlLocale.value, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      weekday: 'short',
    }).format(d)
  } catch {
    return dayKey
  }
}

/** 材料名（品名と同じ行に表示） */
function productMaterialNameText(row: { material_name?: string | null }): string {
  return (row.material_name ?? '').trim()
}

function rowRemarksText(row: { remarks?: string | null }): string {
  return (row.remarks ?? '').trim()
}

/** 管理コードの末尾5文字を「コード」付きで表示 */
function formatMgmtCodeShort(code: string | null | undefined): string {
  const s = (code ?? '').trim()
  if (!s) return ''
  const tail = s.length <= 5 ? s : s.slice(-5)
  return t('mesCuttingActual.mgmtCodeShort', { code: tail })
}

/** 生産日ごとのグループ表示（loadPlans は production_day で絞り込み済み） */
const visibleRowsByDay = computed(() => {
  let rows = managementRows.value.filter((r): r is CuttingMgmtRow => r.id != null)
  if (hideCompleted.value) {
    rows = rows.filter((r) => Number(r.production_completed_check ?? 0) !== 1)
  }
  rows.sort((a, b) => {
    const da = normalizeProductionDayKey(a.production_day)
    const db = normalizeProductionDayKey(b.production_day)
    if (da !== db) return da.localeCompare(db)
    return (a.production_sequence ?? 0) - (b.production_sequence ?? 0)
  })
  const groups = new Map<string, CuttingMgmtRow[]>()
  for (const r of rows) {
    const k = normalizeProductionDayKey(r.production_day)
    if (!groups.has(k)) groups.set(k, [])
    groups.get(k)!.push(r)
  }
  const keys = [...groups.keys()].sort((x, y) => {
    if (x === '—') return 1
    if (y === '—') return -1
    return x.localeCompare(y)
  })
  const anchor = productionDay.value?.slice(0, 10) ?? ''
  return keys.map((dayKey) => ({
    dayKey,
    rows: groups.get(dayKey)!,
    isAnchorDay: Boolean(anchor && dayKey === anchor),
  }))
})

const planSortables = new Map<string, Sortable>()
const planDayListRefs = new Map<string, HTMLElement>()
const planReorderSaving = ref(false)

function setPlanDayListRef(dayKey: string, el: Element | ComponentPublicInstance | null): void {
  let node: HTMLElement | null = null
  if (el instanceof HTMLElement) {
    node = el
  } else if (el && typeof el === 'object' && '$el' in el) {
    const root = (el as ComponentPublicInstance).$el
    if (root instanceof HTMLElement) node = root
  }
  if (node) planDayListRefs.set(dayKey, node)
  else planDayListRefs.delete(dayKey)
}

function destroyPlanSortables(): void {
  for (const s of planSortables.values()) s.destroy()
  planSortables.clear()
}

function canInitPlanSortable(grp: { dayKey: string; rows: CuttingMgmtRow[] }): boolean {
  if (planReorderSaving.value || loadingPlans.value) return false
  if (selectedMachineId.value == null || !selectedMachineName.value) return false
  if (grp.rows.length <= 1 || grp.dayKey === '—') return false
  return true
}

function initPlanSortables(): void {
  destroyPlanSortables()
  for (const grp of visibleRowsByDay.value) {
    if (!canInitPlanSortable(grp)) continue
    const el = planDayListRefs.get(grp.dayKey)
    if (!el) continue
    const sortable = Sortable.create(el, {
      animation: 150,
      handle: '.plan-row-card__drag-handle',
      draggable: '.plan-row-card',
      ghostClass: 'plan-row-card--ghost',
      chosenClass: 'plan-row-card--chosen',
      delay: 120,
      delayOnTouchOnly: true,
      onEnd: (evt) => void onPlanCardSortEnd(grp.dayKey, evt),
    })
    planSortables.set(grp.dayKey, sortable)
  }
}

function applyLocalProductionSequence(orderedRows: CuttingMgmtRow[]): void {
  for (let i = 0; i < orderedRows.length; i++) {
    const seq = i + 1
    orderedRows[i].production_sequence = seq
    const id = orderedRows[i].id
    if (id == null) continue
    const inList = managementRows.value.find((r) => r.id === id)
    if (inList) inList.production_sequence = seq
  }
}

async function onPlanCardSortEnd(dayKey: string, evt: SortableEvent): Promise<void> {
  if (evt.oldIndex == null || evt.newIndex == null || evt.oldIndex === evt.newIndex) return
  const grp = visibleRowsByDay.value.find((g) => g.dayKey === dayKey)
  if (!grp) return
  const machine = selectedMachineName.value?.trim()
  if (!machine) return
  if (!navigator.onLine) {
    ElMessage.warning(t('mesCuttingActual.needOnlineForEdit'))
    await loadPlans()
    return
  }

  const reordered = [...grp.rows]
  const [moved] = reordered.splice(evt.oldIndex, 1)
  if (!moved) {
    await loadPlans()
    return
  }
  reordered.splice(evt.newIndex, 0, moved)
  const orderedIds = reordered.map((r) => r.id).filter((id): id is number => id != null)
  if (orderedIds.length === 0) return

  applyLocalProductionSequence(reordered)
  planReorderSaving.value = true
  destroyPlanSortables()
  try {
    const res = await reorderCuttingManagement({ cutting_machine: machine, ordered_ids: orderedIds })
    if (res && res.success === false) {
      throw new Error(res.message || 'reorder failed')
    }
    ElMessage.success(t('mesCuttingActual.reorderSaved'))
  } catch (e: unknown) {
    console.error(e)
    ElMessage.error(t('mesCuttingActual.reorderFailed'))
    await loadPlans()
  } finally {
    planReorderSaving.value = false
    nextTick(() => initPlanSortables())
  }
}

watch(
  () =>
    [
      loadingPlans.value,
      selectedMachineId.value,
      ...visibleRowsByDay.value.map((g) => `${g.dayKey}:${g.rows.map((r) => r.id).join(',')}`),
    ].join('|'),
  () => {
    nextTick(() => initPlanSortables())
  },
)

function ensureSession(planId: number): PlanSession {
  if (!sessions[planId]) sessions[planId] = emptySession()
  return sessions[planId]
}

function reapplyLocalSessionsForCurrentScope(): boolean {
  const dayStr = (productionDay.value ?? '').trim()
  if (!/^\d{4}-\d{2}-\d{2}$/.test(dayStr) || selectedMachineId.value == null) return false
  const rowIds = managementRows.value
    .map((r) => r.id)
    .filter((id): id is number => id != null)
  if (rowIds.length === 0) return false
  return applyPersistedSessionsForScope(dayStr, selectedMachineId.value, rowIds, ensureSession)
}

type TagType = 'primary' | 'success' | 'info' | 'warning' | 'danger'

function isCuttingRowConfirmed(row: CuttingMgmtRow): boolean {
  return Number(row.production_completed_check ?? 0) === 1
}

function isCuttingRowMesEnded(row: CuttingMgmtRow): boolean {
  const endedAt = row.mes_production_ended_at
  return endedAt != null && String(endedAt).trim() !== ''
}

function isCuttingRowSessionEnded(row: CuttingMgmtRow): boolean {
  if (row.id == null) return false
  return ensureSession(row.id).wallEnd != null
}

/** 終了済（画面 or DB）または実績確定済 — 表示・計画数ラベル用 */
function isCuttingRowConfirmedForDisplay(row: CuttingMgmtRow): boolean {
  return isCuttingRowConfirmed(row) || isCuttingRowSessionEnded(row) || isCuttingRowMesEnded(row)
}

function statusTagType(row: CuttingMgmtRow): TagType {
  if (isCuttingRowConfirmedForDisplay(row)) return 'success'
  return 'warning'
}

function statusText(row: CuttingMgmtRow): string {
  if (isCuttingRowConfirmedForDisplay(row)) return t('mesCuttingActual.cmConfirmed')
  return t('mesCuttingActual.cmPending')
}

function canScanBarcodeForRow(row: CuttingMgmtRow): boolean {
  return !isCuttingRowConfirmedForDisplay(row) && row.id != null
}

function rowHasScanRegistration(row: CuttingMgmtRow): boolean {
  return Boolean((row.mes_scanned_code ?? '').trim())
}

/** 読取コードが当該行の管理コードと一致（末尾一致含む） */
function scanCodeMatchesManagementCode(
  scanned: string,
  managementCode: string | null | undefined,
): boolean {
  const a = (scanned ?? '').trim()
  const b = (managementCode ?? '').trim()
  if (!a || !b) return false
  if (a === b) return true
  if (b.endsWith(a) || a.endsWith(b)) return true
  const tailA = a.length <= 5 ? a : a.slice(-5)
  const tailB = b.length <= 5 ? b : b.slice(-5)
  return tailA.length >= 3 && tailA === tailB
}

function openBarcodeScanDialog(row: CuttingMgmtRow): void {
  if (!canScanBarcodeForRow(row)) return
  barcodeScanTargetRow.value = row
  barcodeScanDialogVisible.value = true
}

function barcodeScanProductLabel(row: CuttingMgmtRow | null): string {
  if (!row) return ''
  const name = (row.product_name || '').trim()
  const cd = (row.product_cd || '').trim()
  if (name && cd) return `${name} (${cd})`
  return name || cd || '—'
}

async function onBarcodeScanned(code: string): Promise<void> {
  const row = barcodeScanTargetRow.value
  if (row?.id == null) return
  const trimmed = code.trim().slice(0, 512)
  if (!trimmed) return
  const prev = (row.mes_scanned_code ?? '').trim()
  barcodeScanSaving.value = true
  try {
    const ok = await patchWithOfflineSync(row.id, { mes_scanned_code: trimmed })
    row.mes_scanned_code = trimmed
    const inList = managementRows.value.find((r) => r.id === row.id)
    if (inList) inList.mes_scanned_code = trimmed
    if (ok) {
      const resolved = scanCodeMatchesManagementCode(trimmed, row.management_code)
      const replaced = Boolean(prev && prev !== trimmed)
      if (replaced) {
        ElMessage.success(
          resolved ? t('mesCuttingActual.scanReplacedRegistered') : t('mesCuttingActual.scanReplaced'),
        )
      } else {
        ElMessage.success(
          resolved ? t('mesCuttingActual.scanRegistered') : t('mesCuttingActual.scanSaved'),
        )
      }
    }
  } catch (e: unknown) {
    console.error(e)
    ElMessage.error(t('mesCuttingActual.saveFailed'))
  } finally {
    barcodeScanSaving.value = false
    barcodeScanTargetRow.value = null
  }
}

interface ConfirmedEditDraft {
  operatorUserId: number | null
  setupTimeMin: number | undefined
  actualQty: number | null
  wallStart: Date | null
  wallEnd: Date | null
  pausedAccumSec: number
  savedWallStart: number | null
  savedWallEnd: number | null
  savedPausedAccumMs: number
  savedActiveAccumMs: number
}

const confirmedEditDialogVisible = ref(false)
const confirmedEditRow = ref<CuttingMgmtRow | null>(null)
const confirmedEditPlanId = ref<number | null>(null)
const confirmedEditForm = ref<ConfirmedEditDraft | null>(null)
const confirmedEditSaving = ref(false)
const confirmedEditClearing = ref(false)

/** MES 実績フィールドを DB 上でクリアする PATCH 本文（負数は NULL クリア） */
function buildClearMesFieldsPatchBody(): PatchCuttingManagementBody {
  return {
    production_completed_check: false,
    mes_production_started_at: '',
    mes_production_ended_at: '',
    mes_net_production_sec: -1,
    mes_paused_accum_sec: -1,
    mes_production_is_paused: -1,
    mes_setup_time_min: -1,
    mes_operator_user_id: 0,
    mes_scanned_code: '',
  }
}

function resetLocalSessionAfterMesClear(planId: number): void {
  const sess = sessions[planId]
  if (!sess) return
  Object.assign(sess, emptySession())
}

const barcodeScanDialogVisible = ref(false)
const barcodeScanTargetRow = ref<CuttingMgmtRow | null>(null)
const barcodeScanSaving = ref(false)

const confirmedEditElapsedPreview = computed(() => {
  const draft = confirmedEditForm.value
  if (!draft) return '00:00:00'
  return formatElapsed(confirmedEditElapsedMs(draft))
})

function confirmedEditElapsedMs(draft: ConfirmedEditDraft): number {
  const ws = draft.wallStart?.getTime()
  const we = draft.wallEnd?.getTime()
  if (ws == null || we == null || !Number.isFinite(ws) || !Number.isFinite(we)) return 0
  const pauseMs = Math.max(0, Math.round(draft.pausedAccumSec)) * 1000
  return Math.max(0, we - ws - pauseMs)
}

function applyConfirmedEditTimerToSession(planId: number, draft: ConfirmedEditDraft): void {
  const sess = ensureSession(planId)
  const ws = draft.wallStart?.getTime()
  const we = draft.wallEnd?.getTime()
  if (ws == null || !Number.isFinite(ws) || we == null || !Number.isFinite(we)) return
  const pauseMs = Math.max(0, Math.round(draft.pausedAccumSec)) * 1000
  sess.wallStart = ws
  sess.wallEnd = we
  sess.runningSliceStart = null
  sess.pauseSliceStart = null
  sess.pausedAccumMs = pauseMs
  sess.activeAccumMs = Math.max(0, we - ws - pauseMs)
}

function restoreConfirmedEditSessionFromDraft(planId: number, draft: ConfirmedEditDraft): void {
  const sess = ensureSession(planId)
  sess.operatorUserId = draft.operatorUserId
  sess.setupTimeMin = draft.setupTimeMin
  sess.wallStart = draft.savedWallStart
  sess.wallEnd = draft.savedWallEnd
  sess.pausedAccumMs = draft.savedPausedAccumMs
  sess.activeAccumMs = draft.savedActiveAccumMs
}

function clearConfirmedEditState(): void {
  confirmedEditDialogVisible.value = false
  confirmedEditRow.value = null
  confirmedEditPlanId.value = null
  confirmedEditForm.value = null
  confirmedEditSaving.value = false
  confirmedEditClearing.value = false
}

function openConfirmedEditDialog(row: CuttingMgmtRow): void {
  const id = row.id
  if (id == null || !isCuttingRowConfirmed(row)) return
  const sess = ensureSession(id)
  confirmedEditRow.value = row
  confirmedEditPlanId.value = id
  confirmedEditForm.value = {
    operatorUserId: sess.operatorUserId,
    setupTimeMin: sess.setupTimeMin,
    actualQty:
      row.actual_production_quantity != null && Number.isFinite(Number(row.actual_production_quantity))
        ? Math.round(Number(row.actual_production_quantity))
        : null,
    wallStart: sess.wallStart != null ? new Date(sess.wallStart) : null,
    wallEnd: sess.wallEnd != null ? new Date(sess.wallEnd) : null,
    pausedAccumSec: pausedAccumSeconds(sess),
    savedWallStart: sess.wallStart,
    savedWallEnd: sess.wallEnd,
    savedPausedAccumMs: sess.pausedAccumMs ?? 0,
    savedActiveAccumMs: sess.activeAccumMs,
  }
  confirmedEditDialogVisible.value = true
}

function closeConfirmedEditDialog(): void {
  const planId = confirmedEditPlanId.value
  const draft = confirmedEditForm.value
  if (planId != null && draft) {
    restoreConfirmedEditSessionFromDraft(planId, draft)
  }
  clearConfirmedEditState()
}

async function submitConfirmedEdit(): Promise<void> {
  const row = confirmedEditRow.value
  const planId = confirmedEditPlanId.value
  const draft = confirmedEditForm.value
  if (!row || planId == null || !draft) return
  if (!navigator.onLine) {
    ElMessage.warning(t('mesCuttingActual.needOnlineForEdit'))
    return
  }

  if (draft.actualQty != null && (!Number.isFinite(draft.actualQty) || draft.actualQty < 0)) {
    ElMessage.warning(t('mesCuttingActual.qtyInvalid'))
    return
  }

  const ws = draft.wallStart?.getTime()
  const we = draft.wallEnd?.getTime()
  if (ws == null || !Number.isFinite(ws) || we == null || !Number.isFinite(we)) {
    ElMessage.warning(t('mesCuttingActual.editTimeRequired'))
    return
  }
  if (we < ws) {
    ElMessage.warning(t('mesCuttingActual.editTimeOrder'))
    return
  }
  const wallSec = (we - ws) / 1000
  const pauseSec = Math.max(0, Math.round(draft.pausedAccumSec))
  if (!Number.isFinite(pauseSec) || pauseSec > wallSec) {
    ElMessage.warning(t('mesCuttingActual.editPauseTooLong'))
    return
  }

  applyConfirmedEditTimerToSession(planId, draft)
  const sess = ensureSession(planId)
  sess.operatorUserId = draft.operatorUserId
  sess.setupTimeMin = draft.setupTimeMin

  const body: PatchCuttingManagementBody = {
    mes_production_started_at: new Date(ws).toISOString(),
    mes_production_ended_at: new Date(we).toISOString(),
    mes_paused_accum_sec: pauseSec,
    mes_net_production_sec: Math.max(0, Math.round(wallSec - pauseSec)),
  }

  if (draft.operatorUserId != null && draft.operatorUserId > 0) {
    body.mes_operator_user_id = draft.operatorUserId
  }
  if (draft.setupTimeMin !== undefined && draft.setupTimeMin !== null && Number.isFinite(Number(draft.setupTimeMin))) {
    body.mes_setup_time_min = Math.max(0, Math.round(Number(draft.setupTimeMin)))
  }

  const oldActual = Math.round(Number(row.actual_production_quantity ?? 0))
  const roundedNew =
    draft.actualQty != null && Number.isFinite(draft.actualQty)
      ? Math.max(0, Math.round(draft.actualQty))
      : oldActual
  if (roundedNew !== oldActual) {
    body.actual_production_quantity = roundedNew
    const oldDefect = Number(row.defect_qty ?? 0)
    body.defect_qty = Math.max(0, Math.round(oldDefect + (roundedNew - oldActual)))
  }

  confirmedEditSaving.value = true
  try {
    const ok = await patchWithOfflineSync(planId, body)
    if (!ok) return
    ElMessage.success(t('mesCuttingActual.confirmedEditSaved'))
    clearConfirmedEditState()
    flushPersistToStorage()
    await loadPlans()
  } catch (e: unknown) {
    console.error(e)
    ElMessage.error(t('mesCuttingActual.saveFailed'))
  } finally {
    confirmedEditSaving.value = false
  }
}

async function clearConfirmedMesAndSave(): Promise<void> {
  const row = confirmedEditRow.value
  const planId = confirmedEditPlanId.value
  if (!row || planId == null) return
  if (!navigator.onLine) {
    ElMessage.warning(t('mesCuttingActual.needOnlineForEdit'))
    return
  }
  try {
    await ElMessageBox.confirm(
      t('mesCuttingActual.clearMesConfirmMessage'),
      t('mesCuttingActual.clearMesConfirmTitle'),
      {
        type: 'warning',
        confirmButtonText: t('mesCuttingActual.btnClearMesActual'),
        cancelButtonText: t('common.cancel'),
      },
    )
  } catch {
    return
  }

  resetLocalSessionAfterMesClear(planId)
  confirmedEditClearing.value = true
  try {
    const ok = await patchWithOfflineSync(planId, buildClearMesFieldsPatchBody())
    if (!ok) return
    ElMessage.success(t('mesCuttingActual.clearMesSaved'))
    clearConfirmedEditState()
    flushPersistToStorage()
    await loadPlans()
  } catch (e: unknown) {
    console.error(e)
    ElMessage.error(t('mesCuttingActual.saveFailed'))
  } finally {
    confirmedEditClearing.value = false
  }
}

/** 未終了・未確定→計画数、終了済 or 実績確定済→実績数（いずれも actual_production_quantity） */
function rowQtyChipLabel(row: CuttingMgmtRow): string {
  return isCuttingRowConfirmedForDisplay(row) ? t('mesCuttingActual.actualQty') : t('mesCuttingActual.plannedQty')
}

function rowQtyChipValue(row: CuttingMgmtRow): string | number {
  const raw = row.actual_production_quantity
  if (raw == null) return '—'
  return raw
}

/** 計測中の区間を activeAccumMs に合算 */
function flushRunningSlice(sess: PlanSession, now = Date.now()): void {
  if (sess.runningSliceStart != null) {
    sess.activeAccumMs += now - sess.runningSliceStart
    sess.runningSliceStart = null
  }
}

function netProductionSeconds(sess: PlanSession): number {
  return Math.max(0, Math.round(sess.activeAccumMs / 1000))
}

function pausedAccumSeconds(sess: PlanSession): number {
  if (sess.wallEnd != null) {
    return Math.max(0, Math.round((sess.pausedAccumMs ?? 0) / 1000))
  }
  return Math.max(0, Math.round(pausedAccumMs(sess) / 1000))
}

function formatElapsed(ms: number): string {
  const s = Math.max(0, Math.floor(ms / 1000))
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
}

/** 未終了: 開始日時〜現在の壁時計差（内部用） */
function elapsedMs(sess: PlanSession): number {
  if (sess.wallEnd != null) {
    if (sess.activeAccumMs > 0) return sess.activeAccumMs
    if (sess.wallStart != null) return Math.max(0, sess.wallEnd - sess.wallStart)
    return 0
  }
  if (sess.wallStart == null) return 0
  return Math.max(0, tickNow.value - sess.wallStart)
}

/** 稼働計測の画面表示：稼働中は净生産、一時停止中は表示のみ停止（裏で停止累計・DBは継続） */
function operationDisplayMs(sess: PlanSession, now = tickNow.value): number {
  if (sess.wallStart == null) return 0
  if (sess.wallEnd != null) {
    if (sess.activeAccumMs > 0) return sess.activeAccumMs
    return Math.max(0, sess.wallEnd - sess.wallStart)
  }
  return netProductionMs(sess, now)
}

function netProductionMs(sess: PlanSession, now = tickNow.value): number {
  let net = sess.activeAccumMs
  if (sess.runningSliceStart != null) {
    net += now - sess.runningSliceStart
  }
  return Math.max(0, net)
}

/** 一時停止〜再開の累計（ローカル保持 + 現在停止区間） */
function pausedAccumMs(sess: PlanSession): number {
  if (sess.wallStart == null) return 0
  const now = tickNow.value
  let ms = sess.pausedAccumMs ?? 0
  if (sess.pauseSliceStart != null) {
    ms += Math.max(0, now - sess.pauseSliceStart)
  }
  if (ms > 0 || sess.pauseSliceStart != null) {
    return ms
  }
  const wallSpan =
    sess.wallEnd != null
      ? Math.max(0, sess.wallEnd - sess.wallStart)
      : Math.max(0, now - sess.wallStart)
  return Math.max(0, wallSpan - Math.min(netProductionMs(sess, now), wallSpan))
}

function timerPhase(sess: PlanSession): 'idle' | 'running' | 'paused' | 'ended' {
  if (sess.wallEnd != null) return 'ended'
  if (sess.wallStart == null) return 'idle'
  if (sess.pauseSliceStart != null) return 'paused'
  if (sess.runningSliceStart != null) return 'running'
  return 'paused'
}

function timerPhaseLabel(sess: PlanSession): string {
  const ph = timerPhase(sess)
  if (ph === 'idle') return t('mesCuttingActual.timerIdle')
  if (ph === 'running') return t('mesCuttingActual.timerRunning')
  if (ph === 'paused') return t('mesCuttingActual.timerPaused')
  return t('mesCuttingActual.timerEnded')
}

function markLocalMesEcho(planId: number): void {
  localMesEchoUntil.set(planId, Date.now() + 2800)
}

function isLocalMesEchoGuarded(planId: number): boolean {
  const until = localMesEchoUntil.get(planId) ?? 0
  if (Date.now() < until) return true
  if (until > 0) localMesEchoUntil.delete(planId)
  return false
}

function mesTimerCheckpointBody(
  planId: number,
): Pick<
  PatchCuttingManagementBody,
  'mes_net_production_sec' | 'mes_paused_accum_sec' | 'mes_production_is_paused'
> {
  const s = ensureSession(planId)
  return {
    mes_net_production_sec: netProductionSeconds(s),
    mes_paused_accum_sec: pausedAccumSeconds(s),
    mes_production_is_paused: isTimerPaused(s) ? 1 : 0,
  }
}

/** 一時停止/再開・稼働中：净生産・停止累計・稼働/停止フラグを DB に保存（多端末同期用） */
async function persistMesTimerCheckpoints(planId: number): Promise<void> {
  const s = ensureSession(planId)
  const now = Date.now()
  if (s.runningSliceStart != null) {
    flushRunningSlice(s, now)
    if (s.wallEnd == null && s.pauseSliceStart == null) {
      s.runningSliceStart = now
    }
  } else if (s.pauseSliceStart != null) {
    flushPauseSlice(s, now)
    if (s.wallEnd == null) {
      s.pauseSliceStart = now
    }
  }
  try {
    await patchWithOfflineSync(planId, mesTimerCheckpointBody(planId), { silentQueue: true })
  } catch (e: unknown) {
    console.error(e)
  }
}

/** 生産終了時にサーバーへ書く MES 時刻・净生産秒・停止累計・段取・作業者（先にタイマー確定） */
function mesEndTrackingPatchBody(planId: number): Pick<
  PatchCuttingManagementBody,
  | 'mes_production_ended_at'
  | 'mes_net_production_sec'
  | 'mes_paused_accum_sec'
  | 'mes_setup_time_min'
  | 'mes_operator_user_id'
> {
  finalizeProductionTimer(planId)
  const s = ensureSession(planId)
  const body: Pick<
    PatchCuttingManagementBody,
    | 'mes_production_ended_at'
    | 'mes_net_production_sec'
    | 'mes_paused_accum_sec'
    | 'mes_setup_time_min'
    | 'mes_operator_user_id'
  > = {
    mes_production_ended_at:
      s.wallEnd != null ? new Date(s.wallEnd).toISOString() : new Date().toISOString(),
    mes_net_production_sec: netProductionSeconds(s),
    mes_paused_accum_sec: pausedAccumSeconds(s),
  }
  const st = s.setupTimeMin
  if (st !== undefined && st !== null && Number.isFinite(Number(st))) {
    body.mes_setup_time_min = Math.max(0, Math.round(Number(st)))
  }
  if (s.operatorUserId != null && s.operatorUserId > 0) {
    body.mes_operator_user_id = s.operatorUserId
  }
  return body
}

function isRowMesProductionActive(row: CuttingMgmtRow): boolean {
  if (row.id != null && sessions[row.id]) {
    const sess = sessions[row.id]
    if (sess.wallStart != null && sess.wallEnd == null) return true
  }
  const started = row.mes_production_started_at
  if (started == null || !String(started).trim()) return false
  const ended = row.mes_production_ended_at
  return ended == null || !String(ended).trim()
}

/** 同一設備（現在の一覧）で他に生産中の行 */
function findOtherActiveProductionRow(excludePlanId: number): CuttingMgmtRow | null {
  for (const row of managementRows.value) {
    if (row.id == null || row.id === excludePlanId) continue
    const mgmt = row as CuttingMgmtRow
    if (isRowMesProductionActive(mgmt)) return mgmt
  }
  return null
}

function rowProductionShortLabel(row: CuttingMgmtRow): string {
  const seq = row.production_sequence
  const name = (row.product_name || row.product_cd || '').trim()
  const seqPart = seq != null ? `#${seq}` : ''
  if (name && seqPart) return `${seqPart} ${name}`
  return name || seqPart || `#${row.id ?? ''}`
}

async function onStart(planId: number) {
  const s = ensureSession(planId)
  if (s.wallEnd != null) return
  const now = Date.now()
  if (s.wallStart == null) {
    const other = findOtherActiveProductionRow(planId)
    if (other) {
      ElMessage.warning(
        t('mesCuttingActual.singleMachineProductionOnly', {
          label: rowProductionShortLabel(other),
        }),
      )
      return
    }
    markLocalMesEcho(planId)
    let allowLocalStart = false
    try {
      const ok = await patchWithOfflineSync(planId, {
        mes_production_started_at: new Date(now).toISOString(),
        mes_production_is_paused: 0,
      })
      allowLocalStart = ok || !navigator.onLine
      if (!allowLocalStart) return
    } catch (e: unknown) {
      const status =
        e && typeof e === 'object' && 'response' in e
          ? (e as { response?: { status?: number; data?: { detail?: string } } }).response?.status
          : undefined
      const detail =
        e && typeof e === 'object' && 'response' in e
          ? (e as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined
      if (status === 409 && typeof detail === 'string' && detail.trim()) {
        ElMessage.warning(detail.trim())
      } else {
        ElMessage.error(
          typeof detail === 'string' && detail.trim() ? detail.trim() : t('mesCuttingActual.saveFailed'),
        )
      }
      void syncMesStateFromServer()
      return
    }
    s.wallStart = now
    s.activeAccumMs = 0
    s.pausedAccumMs = 0
    s.pauseSliceStart = null
    s.runningSliceStart = now
    flushPersistToStorage()
    return
  }
  if (s.runningSliceStart == null) {
    s.runningSliceStart = now
    markLocalMesEcho(planId)
    void persistMesTimerCheckpoints(planId)
  }
  flushPersistToStorage()
}

function onPause(planId: number | undefined | null) {
  if (planId == null || !Number.isFinite(planId)) return
  const s = ensureSession(planId)
  if (s.wallEnd != null || s.runningSliceStart == null) return
  const now = Date.now()
  flushRunningSlice(s, now)
  s.pauseSliceStart = now
  markLocalMesEcho(planId)
  void persistMesTimerCheckpoints(planId)
  flushPersistToStorage()
}

function onResume(planId: number | undefined | null) {
  if (planId == null || !Number.isFinite(planId)) return
  const s = ensureSession(planId)
  if (s.wallEnd != null || s.wallStart == null || s.runningSliceStart != null) return
  const now = Date.now()
  flushPauseSlice(s, now)
  s.runningSliceStart = now
  markLocalMesEcho(planId)
  void persistMesTimerCheckpoints(planId)
  flushPersistToStorage()
}

function isTimerRunning(sess: PlanSession): boolean {
  return sess.runningSliceStart != null
}

/** 生産開始済み・未終了（計測中または一時停止中） */
function isProductionInProgress(sess: PlanSession): boolean {
  return sess.wallStart != null && sess.wallEnd == null
}

function isTimerPaused(sess: PlanSession): boolean {
  return isProductionInProgress(sess) && sess.runningSliceStart == null
}

function canStartTimer(sess: PlanSession, planId: number): boolean {
  if (sess.wallEnd != null || sess.wallStart != null) return false
  return findOtherActiveProductionRow(planId) == null
}

/** 稼働計測中のみ生産終了可（一時停止中は不可） */
function canEndProduction(sess: PlanSession): boolean {
  return isTimerRunning(sess)
}

/** 未開始のみ切断機変更可（生産中・終了済・実績確定済は不可） */
function canChangeMachine(row: CuttingMgmtRow): boolean {
  if (row.id == null) return false
  if (isCuttingRowConfirmedForDisplay(row)) return false
  if (isRowMesProductionActive(row)) return false
  return true
}

function machineNameById(machineId: number | null): string | null {
  if (machineId == null) return null
  const m = machines.value.find((x) => x.id === machineId)
  const name = (m?.machine_name ?? '').trim()
  return name || null
}

function sortedRowIdsBySequence(rows: CuttingManagementListRow[]): number[] {
  return [...rows]
    .filter((r): r is CuttingManagementListRow & { id: number } => r.id != null)
    .sort((a, b) => (a.production_sequence ?? 0) - (b.production_sequence ?? 0))
    .map((r) => r.id)
}

async function reorderMachineRowsForDay(machineName: string, productionDay: string): Promise<void> {
  const cm = machineName.trim()
  if (!cm || !/^\d{4}-\d{2}-\d{2}$/.test(productionDay)) return
  const res = await fetchCuttingManagementList({
    production_day: productionDay,
    cutting_machine: cm,
    limit: 2000,
  })
  const ids = sortedRowIdsBySequence(res.data ?? [])
  if (ids.length === 0) return
  const reorderRes = await reorderCuttingManagement({ cutting_machine: cm, ordered_ids: ids })
  if (reorderRes && reorderRes.success === false) {
    throw new Error(reorderRes.message || 'reorder failed')
  }
}

async function reorderAfterMachineMove(params: {
  rowId: number
  sourceMachine: string
  targetMachine: string
  productionDay: string
}): Promise<void> {
  const source = params.sourceMachine.trim()
  const target = params.targetMachine.trim()
  const day = params.productionDay.trim()
  if (!source || !target || !day) return

  if (source !== target) {
    await reorderMachineRowsForDay(source, day)
  }

  const targetRes = await fetchCuttingManagementList({
    production_day: day,
    cutting_machine: target,
    limit: 2000,
  })
  let targetIds = sortedRowIdsBySequence(targetRes.data ?? [])
  targetIds = targetIds.filter((id) => id !== params.rowId)
  targetIds.push(params.rowId)
  if (targetIds.length === 0) return
  const reorderRes = await reorderCuttingManagement({
    cutting_machine: target,
    ordered_ids: targetIds,
  })
  if (reorderRes && reorderRes.success === false) {
    throw new Error(reorderRes.message || 'reorder failed')
  }
}

function canPauseTimer(sess: PlanSession): boolean {
  return isTimerRunning(sess)
}

function canResumeTimer(sess: PlanSession): boolean {
  return isTimerPaused(sess)
}

/** split API が参照する「現在の指示本数」（actual_production_quantity） */
function splitBaselineQty(row: CuttingMgmtRow): number {
  const n = Number(row.actual_production_quantity ?? 0)
  return Number.isFinite(n) && n >= 0 ? Math.floor(n) : 0
}

/** 不良数 = 生産終了時の確認本数 − 確定前の actual_production_quantity */
function computedDefectQty(row: CuttingMgmtRow, confirmedQty: number): number {
  const instructionQty = splitBaselineQty(row)
  const confirmed = Math.round(Number(confirmedQty))
  if (!Number.isFinite(confirmed)) return 0
  return confirmed - instructionQty
}

function plannedHintQty(row: CuttingMgmtRow): number {
  const n = Number(row.actual_production_quantity ?? 0)
  return Number.isFinite(n) && n >= 0 ? Math.floor(n) : 0
}

/** 生産終了ダイアログ（実績本数・満了／順延） */
const endDialogVisible = ref(false)
const endDialogRow = ref<CuttingMgmtRow | null>(null)
const endDialogPlanId = ref<number | null>(null)
const endDialogQty = ref('')
const endDialogSubmitting = ref(false)
/** 順延先の生産日（YYYY-MM-DD） */
const endDialogDeferDay = ref('')
/** 同一生産日・同設備で当該行より後の計画も同じ日へ順延 */
const endDialogDeferSubsequent = ref(false)

function shiftDateYmd(dateStr: string, deltaDays: number): string {
  const d = new Date(`${dateStr.slice(0, 10)}T12:00:00`)
  d.setDate(d.getDate() + deltaDays)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

/** 翌平日（土日は翌月曜） */
function nextWeekdayFromProductionDay(dateStr: string): string {
  let s = shiftDateYmd(dateStr, 1)
  const d = new Date(`${s}T12:00:00`)
  const w = d.getDay()
  if (w === 0) d.setDate(d.getDate() + 1)
  else if (w === 6) d.setDate(d.getDate() + 2)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function disabledWeekendDeferDate(date: Date): boolean {
  const w = date.getDay()
  return w === 0 || w === 6
}

const endDialogDeferRemainder = computed(() => {
  const baseline = endDialogBaseline.value
  const qty = parseEndDialogQty()
  if (qty == null || baseline <= 0) return 0
  return Math.max(0, baseline - qty)
})

const endDialogSubsequentDeferRows = computed((): CuttingMgmtRow[] => {
  const row = endDialogRow.value
  if (!row || row.id == null) return []
  const dayKey = normalizeProductionDayKey(row.production_day ?? productionDay.value)
  if (dayKey === '—') return []
  const machine = (row.cutting_machine ?? selectedMachineName.value ?? '').trim()
  if (!machine) return []
  const currentSeq = row.production_sequence ?? 0
  return managementRows.value
    .filter((r): r is CuttingMgmtRow => {
      if (r.id == null || r.id === row.id) return false
      if (normalizeProductionDayKey(r.production_day) !== dayKey) return false
      if ((r.cutting_machine ?? '').trim() !== machine) return false
      if ((r.production_sequence ?? 0) <= currentSeq) return false
      if (Number(r.production_completed_check ?? 0) === 1) return false
      const total = Number(r.actual_production_quantity ?? 0)
      return Number.isFinite(total) && total > 0
    })
    .sort((a, b) => (a.production_sequence ?? 0) - (b.production_sequence ?? 0))
})

const endDialogSubsequentDeferCount = computed(() => endDialogSubsequentDeferRows.value.length)

const changeMachineDialogVisible = ref(false)
const changeMachineRow = ref<CuttingMgmtRow | null>(null)
const changeMachineTargetId = ref<number | null>(null)
const changeMachineSubmitting = ref(false)

const changeMachineCurrentName = computed((): string => {
  const row = changeMachineRow.value
  if (!row) return '—'
  return (row.cutting_machine ?? '').trim() || '—'
})

function openChangeMachineDialog(row: CuttingMgmtRow): void {
  if (!canChangeMachine(row) || row.id == null) return
  changeMachineRow.value = row
  const currentName = (row.cutting_machine ?? '').trim()
  const matched = cuttingMachinesForSelect.value.find(
    (m) => (m.machine_name ?? '').trim() === currentName,
  )
  changeMachineTargetId.value = matched?.id ?? selectedMachineId.value
  changeMachineDialogVisible.value = true
}

function closeChangeMachineDialog(): void {
  changeMachineDialogVisible.value = false
  changeMachineRow.value = null
  changeMachineTargetId.value = null
  changeMachineSubmitting.value = false
}

async function submitChangeMachine(): Promise<void> {
  const row = changeMachineRow.value
  if (!row || row.id == null) return
  if (!canChangeMachine(row)) {
    ElMessage.warning(t('mesCuttingActual.changeMachineForbidden'))
    return
  }
  if (!navigator.onLine) {
    ElMessage.warning(t('mesCuttingActual.needOnlineForEdit'))
    return
  }
  const targetName = machineNameById(changeMachineTargetId.value)
  if (!targetName) {
    ElMessage.warning(t('mesCuttingActual.emptyMachineName'))
    return
  }
  const sourceName = (row.cutting_machine ?? '').trim() || selectedMachineName.value || ''
  if (!sourceName) {
    ElMessage.warning(t('mesCuttingActual.emptyMachineName'))
    return
  }
  if (targetName === sourceName) {
    ElMessage.warning(t('mesCuttingActual.changeMachineSame'))
    return
  }
  const dayStr = normalizeProductionDayKey(row.production_day ?? productionDay.value)
  if (dayStr === '—' || !/^\d{4}-\d{2}-\d{2}$/.test(dayStr)) {
    ElMessage.warning(t('mesCuttingActual.invalidProductionDay'))
    return
  }

  changeMachineSubmitting.value = true
  try {
    const ok = await patchWithOfflineSync(row.id, { cutting_machine: targetName })
    if (!ok) return
    await reorderAfterMachineMove({
      rowId: row.id,
      sourceMachine: sourceName,
      targetMachine: targetName,
      productionDay: dayStr,
    })
    ElMessage.success(t('mesCuttingActual.changeMachineSaved', { machine: targetName }))
    closeChangeMachineDialog()
    flushPersistToStorage()
    await loadPlans()
  } catch (e: unknown) {
    console.error(e)
    ElMessage.error(t('mesCuttingActual.saveFailed'))
  } finally {
    changeMachineSubmitting.value = false
  }
}

const endDialogBaseline = computed(() => (endDialogRow.value ? splitBaselineQty(endDialogRow.value) : 0))

const endDialogOperatorLabel = computed(() => {
  const planId = endDialogPlanId.value
  if (planId == null) return ''
  const uid = ensureSession(planId).operatorUserId
  if (uid == null) return ''
  const u = operators.value.find((o) => o.id === uid)
  return (u?.full_name || u?.username || '').trim()
})

const endDialogHasOperator = computed(() => endDialogOperatorLabel.value.length > 0)

const endDialogSetupTimeLabel = computed(() => {
  const planId = endDialogPlanId.value
  if (planId == null) return ''
  const st = ensureSession(planId).setupTimeMin
  if (st === undefined || st === null || !Number.isFinite(Number(st))) return ''
  return String(Math.max(0, Math.round(Number(st))))
})

const endDialogHasSetupTime = computed(() => endDialogSetupTimeLabel.value.length > 0)

const endDialogMetaIncomplete = computed(() => !endDialogHasOperator.value || !endDialogHasSetupTime.value)

function parseEndDialogQty(): number | null {
  const raw = (endDialogQty.value ?? '').trim()
  if (!raw) return null
  const n = Math.round(Number(raw))
  if (!Number.isFinite(n) || n < 0) return null
  return n
}
function finalizeProductionTimer(planId: number) {
  const s = ensureSession(planId)
  if (s.wallEnd != null) return
  const now = Date.now()
  flushRunningSlice(s, now)
  s.wallEnd = now
  freezePausedAccumMs(s, now)
}

function openProductionEndDialog(row: CuttingMgmtRow) {
  const s = ensureSession(row.id)
  if (s.wallStart == null || s.wallEnd != null) return
  endDialogRow.value = row
  endDialogPlanId.value = row.id
  const baseline = splitBaselineQty(row)
  const planned = plannedHintQty(row)
  endDialogQty.value = baseline > 0 ? String(baseline) : planned > 0 ? String(planned) : ''
  const daySrc = normalizeProductionDayKey(row.production_day ?? productionDay.value)
  endDialogDeferDay.value =
    daySrc !== '—' && /^\d{4}-\d{2}-\d{2}$/.test(daySrc)
      ? nextWeekdayFromProductionDay(daySrc)
      : nextWeekdayFromProductionDay((productionDay.value ?? '').trim())
  endDialogDeferSubsequent.value = endDialogSubsequentDeferCount.value > 0
  endDialogVisible.value = true
}

function closeProductionEndDialog() {
  endDialogVisible.value = false
  endDialogRow.value = null
  endDialogPlanId.value = null
  endDialogQty.value = ''
  endDialogDeferDay.value = ''
  endDialogDeferSubsequent.value = false
  endDialogSubmitting.value = false
}

async function deferSingleRowToNextDay(
  row: CuttingMgmtRow,
  todayQty: number,
  nextDay: string,
  options?: { mesPlanId?: number | null },
): Promise<void> {
  if (row.id == null) return
  const planId = options?.mesPlanId
  if (planId != null) {
    markLocalMesEcho(planId)
    const mesPatch: PatchCuttingManagementBody = {
      defect_qty: computedDefectQty(row, todayQty),
      ...mesEndTrackingPatchBody(planId),
    }
    const preOk = await patchWithOfflineSync(row.id, mesPatch)
    if (!preOk) throw new Error('mes patch failed')
  }
  const res = await splitCuttingManagementToNextDay(row.id, {
    today_quantity: todayQty,
    next_day: nextDay,
  })
  if (res && res.success === false) {
    throw new Error(res.message || 'split failed')
  }
  await patchCuttingManagement(row.id, { production_completed_check: true })
}

/** 後続計画は split せず生産日のみ変更（数量・行はそのまま） */
async function moveSubsequentRowsProductionDay(rows: CuttingMgmtRow[], targetDay: string): Promise<void> {
  for (const subRow of rows) {
    if (subRow.id == null) continue
    const res = await patchCuttingManagement(subRow.id, { production_day: targetDay })
    if (res && res.success === false) {
      throw new Error(res.message || 'production_day update failed')
    }
  }
}

/** 順延先：当該品の残り行 → 後続行（元順）→ 既存計画（元順） */
async function reorderTargetDayAfterDefer(
  machineName: string,
  targetDay: string,
  currentRow: CuttingMgmtRow,
  subsequentIds: number[],
): Promise<void> {
  const cm = machineName.trim()
  if (!cm || !/^\d{4}-\d{2}-\d{2}$/.test(targetDay)) return

  const res = await fetchCuttingManagementList({
    production_day: targetDay,
    cutting_machine: cm,
    limit: 2000,
  })
  const all = (res.data ?? []).filter((r): r is CuttingManagementListRow & { id: number } => r.id != null)
  if (all.length === 0) return

  const subsequentSet = new Set(subsequentIds)
  const currentId = currentRow.id
  const mgmt = (currentRow.management_code ?? '').trim()
  const sameProduct = (r: CuttingManagementListRow): boolean => {
    if ((r.product_cd ?? '').trim() !== (currentRow.product_cd ?? '').trim()) return false
    if (!mgmt) return true
    return (r.management_code ?? '').trim() === mgmt
  }

  const remainderCandidates = all.filter(
    (r) =>
      r.id !== currentId &&
      !subsequentSet.has(r.id) &&
      sameProduct(r) &&
      Number(r.production_completed_check ?? 0) === 0,
  )
  const remainderId =
    remainderCandidates.length > 0
      ? [...remainderCandidates].sort((a, b) => b.id - a.id)[0]!.id
      : null

  const subsequentOrdered = subsequentIds.filter((id) => all.some((r) => r.id === id))
  const used = new Set<number>([
    ...(remainderId != null ? [remainderId] : []),
    ...subsequentOrdered,
  ])
  const rest = all
    .filter((r) => !used.has(r.id))
    .sort((a, b) => (a.production_sequence ?? 0) - (b.production_sequence ?? 0))
    .map((r) => r.id)

  const orderedIds: number[] = [
    ...(remainderId != null ? [remainderId] : []),
    ...subsequentOrdered,
    ...rest,
  ]
  if (orderedIds.length === 0) {
    await reorderMachineRowsForDay(cm, targetDay)
    return
  }

  const reorderRes = await reorderCuttingManagement({ cutting_machine: cm, ordered_ids: orderedIds })
  if (reorderRes && reorderRes.success === false) {
    throw new Error(reorderRes.message || 'reorder failed')
  }
}

/** 順延後：元の生産日を詰め、順延先は残り→後続→既存の順で production_sequence を振り直す */
async function reorderAfterProductionDefer(
  currentRow: CuttingMgmtRow,
  targetDay: string,
  subsequentRows: CuttingMgmtRow[],
): Promise<void> {
  const machine = (currentRow.cutting_machine ?? selectedMachineName.value ?? '').trim()
  if (!machine) return
  const sourceDay = normalizeProductionDayKey(currentRow.production_day ?? productionDay.value)
  const subsequentIds = subsequentRows
    .map((r) => r.id)
    .filter((id): id is number => id != null)

  if (sourceDay !== '—' && /^\d{4}-\d{2}-\d{2}$/.test(sourceDay) && sourceDay !== targetDay) {
    await reorderMachineRowsForDay(machine, sourceDay)
  }
  await reorderTargetDayAfterDefer(machine, targetDay, currentRow, subsequentIds)
}

async function submitProductionEndFullBaseline() {
  const row = endDialogRow.value
  const planId = endDialogPlanId.value
  if (!row || planId == null) return
  if (!navigator.onLine) {
    ElMessage.warning(t('mesCuttingActual.needOnlineForEnd'))
    return
  }
  const baseline = splitBaselineQty(row)
  if (baseline <= 0) {
    ElMessage.warning(t('mesCuttingActual.splitBaselineZero'))
    return
  }
  endDialogSubmitting.value = true
  try {
    markLocalMesEcho(planId)
    const body: PatchCuttingManagementBody = {
      actual_production_quantity: baseline,
      production_completed_check: true,
      defect_qty: computedDefectQty(row, baseline),
      ...mesEndTrackingPatchBody(planId),
    }
    const ok = await patchWithOfflineSync(row.id, body)
    if (!ok) {
      endDialogSubmitting.value = false
      return
    }
    ElMessage.success(t('mesCuttingActual.completeSaved'))
    closeProductionEndDialog()
    await loadPlans()
  } catch (e: unknown) {
    console.error(e)
    ElMessage.error(t('mesCuttingActual.saveFailed'))
  } finally {
    endDialogSubmitting.value = false
  }
}

async function submitProductionEndDefer() {
  const row = endDialogRow.value
  const planId = endDialogPlanId.value
  if (!row || planId == null) return
  if (!navigator.onLine) {
    ElMessage.warning(t('mesCuttingActual.needOnlineForEnd'))
    return
  }
  const baseline = splitBaselineQty(row)
  const qty = parseEndDialogQty()
  if (qty == null) {
    ElMessage.warning(t('mesCuttingActual.qtyInvalid'))
    return
  }
  if (baseline <= 0) {
    ElMessage.warning(t('mesCuttingActual.splitBaselineZero'))
    return
  }
  if (qty >= baseline) {
    ElMessage.warning(t('mesCuttingActual.deferQtyMustBeLess'))
    return
  }
  const nextDay = (endDialogDeferDay.value ?? '').trim().slice(0, 10)
  if (!/^\d{4}-\d{2}-\d{2}$/.test(nextDay)) {
    ElMessage.warning(t('mesCuttingActual.deferNextDayRequired'))
    return
  }

  const subsequent = endDialogDeferSubsequent.value ? [...endDialogSubsequentDeferRows.value] : []
  const subsequentCount = subsequent.length

  try {
    await ElMessageBox.confirm(
      subsequentCount > 0
        ? t('mesCuttingActual.deferConfirmWithFollowing', {
            date: nextDay,
            n: subsequentCount,
            remainder: endDialogDeferRemainder.value,
          })
        : t('mesCuttingActual.deferConfirmMessage', {
            date: nextDay,
            remainder: endDialogDeferRemainder.value,
          }),
      t('mesCuttingActual.deferConfirmTitle'),
      {
        type: 'warning',
        confirmButtonText: t('mesCuttingActual.btnDeferConfirm'),
        cancelButtonText: t('common.cancel'),
      },
    )
  } catch {
    return
  }

  endDialogSubmitting.value = true
  try {
    if (subsequent.length > 0) {
      await moveSubsequentRowsProductionDay(subsequent, nextDay)
    }
    await deferSingleRowToNextDay(row, qty, nextDay, { mesPlanId: planId })
    await reorderAfterProductionDefer(row, nextDay, subsequent)
    ElMessage.success(
      subsequentCount > 0
        ? t('mesCuttingActual.deferSavedWithFollowing', { n: subsequentCount + 1, date: nextDay })
        : t('mesCuttingActual.deferSavedWithDate', { date: nextDay }),
    )
    closeProductionEndDialog()
    await loadPlans()
  } catch (e: unknown) {
    console.error(e)
    const msg =
      (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail ??
      (e as { message?: string })?.message
    ElMessage.error(msg ? String(msg) : t('mesCuttingActual.saveFailed'))
    await loadPlans()
  } finally {
    endDialogSubmitting.value = false
  }
}

async function submitProductionEndZeroBaseline() {
  const row = endDialogRow.value
  const planId = endDialogPlanId.value
  if (!row || planId == null) return
  if (!navigator.onLine) {
    ElMessage.warning(t('mesCuttingActual.needOnlineForEnd'))
    return
  }
  if (splitBaselineQty(row) > 0) return
  const qty = parseEndDialogQty()
  if (qty == null) {
    ElMessage.warning(t('mesCuttingActual.qtyInvalid'))
    return
  }
  endDialogSubmitting.value = true
  try {
    markLocalMesEcho(planId)
    const body: PatchCuttingManagementBody = {
      actual_production_quantity: qty,
      production_completed_check: true,
      defect_qty: computedDefectQty(row, qty),
      ...mesEndTrackingPatchBody(planId),
    }
    const ok = await patchWithOfflineSync(row.id, body)
    if (!ok) {
      endDialogSubmitting.value = false
      return
    }
    ElMessage.success(t('mesCuttingActual.completeSaved'))
    closeProductionEndDialog()
    await loadPlans()
  } catch (e: unknown) {
    console.error(e)
    ElMessage.error(t('mesCuttingActual.saveFailed'))
  } finally {
    endDialogSubmitting.value = false
  }
}

function formatWall(ts: number | null): string {
  if (ts == null) return '—'
  return formatDateTimeJST(new Date(ts), intlLocale.value, { second: '2-digit' })
}

async function loadMachines() {
  loadingMachines.value = true
  try {
    machines.value = await fetchCuttingPlanningMachines()
  } catch (e: unknown) {
    console.error(e)
    ElMessage.error(t('mesCuttingActual.loadMachinesFailed'))
  } finally {
    loadingMachines.value = false
  }
}

async function loadOperators() {
  loadingUsers.value = true
  try {
    const res = (await getUsers({ page: 1, page_size: 500, status: 'active' })) as unknown as PaginatedUserResponse
    operators.value = res.items ?? []
  } catch (e: unknown) {
    console.error(e)
    ElMessage.error(t('mesCuttingActual.loadUsersFailed'))
  } finally {
    loadingUsers.value = false
  }
}

/** 同一設備・生産日を開く他端末と表示を揃える（DB 正） */
async function syncMesStateFromServer(): Promise<void> {
  if (mesSyncInFlight || loadingPlans.value) return
  if (typeof document !== 'undefined' && document.visibilityState === 'hidden') return
  if (!navigator.onLine || selectedMachineId.value == null) return
  const cuttingMachine = selectedMachineName.value
  if (!cuttingMachine) return
  const dayStr = (productionDay.value ?? '').trim()
  if (!/^\d{4}-\d{2}-\d{2}$/.test(dayStr)) return
  if (managementRows.value.length === 0) return

  mesSyncInFlight = true
  try {
    const res = await fetchCuttingManagementList({
      production_day: dayStr,
      cutting_machine: cuttingMachine,
      limit: 2000,
    })
    if (!res.success || !res.data?.length) return

    const byId = new Map(res.data.map((r) => [r.id, r]))
    for (const row of managementRows.value) {
      if (row.id == null) continue
      const fresh = byId.get(row.id)
      if (!fresh) continue

      // 備考は他端末・計画画面の更新を常に反映（MES 操作のエコーガード対象外）
      row.remarks = fresh.remarks

      if (isLocalMesEchoGuarded(row.id)) continue

      row.mes_production_started_at = fresh.mes_production_started_at
      row.mes_production_ended_at = fresh.mes_production_ended_at
      row.mes_net_production_sec = fresh.mes_net_production_sec
      row.mes_paused_accum_sec = fresh.mes_paused_accum_sec
      row.mes_production_is_paused = fresh.mes_production_is_paused
      row.mes_setup_time_min = fresh.mes_setup_time_min
      row.mes_operator_user_id = fresh.mes_operator_user_id
      row.mes_scanned_code = fresh.mes_scanned_code
      row.production_completed_check = fresh.production_completed_check
      row.actual_production_quantity = fresh.actual_production_quantity
      row.defect_qty = fresh.defect_qty

      const sess = ensureSession(row.id)
      hydratePlanSessionFromRow(sess, fresh)
      if (sess.wallStart != null && sess.wallEnd == null) {
        reconcileInProgressTimer(sess)
      }
      if (fresh.mes_operator_user_id != null && Number.isFinite(Number(fresh.mes_operator_user_id))) {
        sess.operatorUserId = Number(fresh.mes_operator_user_id)
      }
      if (fresh.mes_setup_time_min != null && Number.isFinite(Number(fresh.mes_setup_time_min))) {
        sess.setupTimeMin = Math.max(0, Math.round(Number(fresh.mes_setup_time_min)))
      }
    }
  } catch {
    /* ネットワーク揺らぎ時は次回ポーリングで再試行 */
  } finally {
    mesSyncInFlight = false
  }
}

async function loadPlans() {
  if (selectedMachineId.value == null) {
    ElMessage.warning(t('mesCuttingActual.emptySelectMachine'))
    return
  }
  const cuttingMachine = selectedMachineName.value
  if (!cuttingMachine) {
    ElMessage.warning(t('mesCuttingActual.emptyMachineName'))
    return
  }
  loadingPlans.value = true
  try {
    const dayStr = (productionDay.value ?? '').trim()
    if (!/^\d{4}-\d{2}-\d{2}$/.test(dayStr)) {
      ElMessage.warning(t('mesCuttingActual.invalidProductionDay'))
      managementRows.value = []
      clearSessions()
      return
    }
    const res = await fetchCuttingManagementList({
      production_day: dayStr,
      cutting_machine: cuttingMachine,
      limit: 2000,
    })
    if (!res.success) {
      ElMessage.error(res.message || t('mesCuttingActual.loadPlansFailed'))
      if (managementRows.value.length === 0) {
        managementRows.value = []
        clearSessions()
      } else {
        reapplyLocalSessionsForCurrentScope()
        ElMessage.warning(t('mesCuttingActual.offlineListCached'))
      }
      return
    }
    const rows = res.data ?? []
    clearConfirmedEditState()
    clearSessions()
    managementRows.value = rows
    for (const r of rows) {
      if (r.id == null) continue
      const sess: PlanSession = {
        ...emptySession(),
        operatorUserId:
          r.mes_operator_user_id != null && Number.isFinite(Number(r.mes_operator_user_id))
            ? Number(r.mes_operator_user_id)
            : null,
        setupTimeMin:
          r.mes_setup_time_min != null && Number.isFinite(Number(r.mes_setup_time_min))
            ? Math.round(Number(r.mes_setup_time_min))
            : undefined,
      }
      hydratePlanSessionFromRow(sess, r)
      if (sess.wallStart != null && sess.wallEnd == null) {
        reconcileInProgressTimer(sess)
      }
      sessions[r.id] = sess
    }
    const rowIds = rows.map((r) => r.id).filter((id): id is number => id != null)
    const restored = applyPersistedSessionsForScope(
      dayStr,
      selectedMachineId.value,
      rowIds,
      ensureSession,
    )
    if (restored) {
      ElMessage.info(t('mesCuttingActual.stateRestored'))
    }
    flushPersistToStorage()
    void tryFlushOfflineQueue()
  } catch (e: unknown) {
    console.error(e)
    const detail =
      e &&
      typeof e === 'object' &&
      'response' in e &&
      (e as { response?: { data?: { detail?: string } } }).response?.data?.detail
    ElMessage.error(
      typeof detail === 'string' && detail.trim() ? detail : t('mesCuttingActual.loadPlansFailed'),
    )
    if (managementRows.value.length > 0) {
      reapplyLocalSessionsForCurrentScope()
      ElMessage.warning(t('mesCuttingActual.offlineListCached'))
    } else {
      managementRows.value = []
      clearSessions()
    }
  } finally {
    loadingPlans.value = false
    nextTick(() => initPlanSortables())
  }
}

/** タイトル行の言語アイコン切替（glyph は画面スペース優先の略記） */
const localeIconOptions: { value: LocaleType; label: string; glyph: string }[] = [
  { value: 'ja', label: '日本語', glyph: 'JP' },
  { value: 'en', label: 'English', glyph: 'EN' },
  { value: 'zh', label: '中文', glyph: '中' },
  { value: 'vi', label: 'Tiếng Việt', glyph: 'VI' },
]

function restorePageFiltersFromPersist(): void {
  const blob = loadCuttingActualPersist()
  if (!blob) return
  if (blob.productionDay && /^\d{4}-\d{2}-\d{2}$/.test(blob.productionDay)) {
    productionDay.value = blob.productionDay
  }
  hideCompleted.value = blob.hideCompleted
}

function onPageHidePersist(): void {
  flushPersistToStorage()
}

function onVisibilityChangePersist(): void {
  if (document.visibilityState === 'hidden') {
    onPageHidePersist()
  } else {
    isBrowserOffline.value = !navigator.onLine
    void tryFlushOfflineQueue({ reloadAfter: true })
    void syncMesStateFromServer()
  }
}

onMounted(async () => {
  syncMachineSelectFilterable()
  if (typeof window !== 'undefined') {
    machineSelectTouchMq = window.matchMedia('(hover: none) and (pointer: coarse)')
    machineSelectTouchMq.addEventListener('change', syncMachineSelectFilterable)
  }
  skipScopeSessionReset.value = true
  restorePageFiltersFromPersist()
  tickTimer = setInterval(() => {
    tickNow.value = Date.now()
  }, 1000)
  await Promise.all([loadMachines(), loadOperators()])
  const blob = loadCuttingActualPersist()
  const machineId = blob?.selectedMachineId
  if (
    machineId != null &&
    cuttingMachinesForSelect.value.some((m) => m.id === machineId)
  ) {
    selectedMachineId.value = machineId
    await loadPlans()
  }
  skipScopeSessionReset.value = false
  refreshOfflineQueueCount()
  window.addEventListener('online', onBrowserOnline)
  window.addEventListener('offline', onBrowserOffline)
  window.addEventListener('pagehide', onPageHidePersist)
  window.addEventListener('beforeunload', onPageHidePersist)
  document.addEventListener('visibilitychange', onVisibilityChangePersist)
  void tryFlushOfflineQueue({ reloadAfter: true })
  runningPersistTimer = setInterval(() => {
    const inProgress = Object.values(sessions).some(
      (s) => s.wallEnd == null && s.wallStart != null,
    )
    if (inProgress) flushPersistToStorage()
    for (const [planId, s] of Object.entries(sessions)) {
      if (s.wallEnd == null && s.wallStart != null) {
        void persistMesTimerCheckpoints(Number(planId))
      }
    }
  }, 5000)
  mesSyncTimer = setInterval(() => {
    void syncMesStateFromServer()
  }, MES_SYNC_INTERVAL_MS)
})

onUnmounted(() => {
  destroyPlanSortables()
  machineSelectTouchMq?.removeEventListener('change', syncMachineSelectFilterable)
  machineSelectTouchMq = null
  onPageHidePersist()
  window.removeEventListener('online', onBrowserOnline)
  window.removeEventListener('offline', onBrowserOffline)
  window.removeEventListener('pagehide', onPageHidePersist)
  window.removeEventListener('beforeunload', onPageHidePersist)
  document.removeEventListener('visibilitychange', onVisibilityChangePersist)
  if (tickTimer) clearInterval(tickTimer)
  if (persistTimer) clearTimeout(persistTimer)
  if (runningPersistTimer) clearInterval(runningPersistTimer)
  if (mesSyncTimer) clearInterval(mesSyncTimer)
})
</script>

<template>
  <div class="cutting-actual-page">
    <header class="page-head">
      <div class="page-head-row">
        <div class="page-head-main">
          <h1 class="page-title">
            <span class="page-title__icon" aria-hidden="true">
              <el-icon><DataLine /></el-icon>
            </span>
            <span class="page-title__text">{{ t('mesCuttingActual.title') }}</span>
          </h1>
        </div>
        <div
          class="page-head-locale"
          role="radiogroup"
          :aria-label="t('mesCuttingActual.localeInline')"
        >
          <el-tooltip
            v-for="opt in localeIconOptions"
            :key="opt.value"
            :content="opt.label"
            placement="bottom"
          >
            <button
              type="button"
              role="radio"
              class="locale-glyph-btn"
              :class="{ 'locale-glyph-btn--active': localeUi === opt.value }"
              :aria-label="opt.label"
              :aria-checked="localeUi === opt.value"
              @click="localeUi = opt.value"
            >
              <span class="locale-glyph-btn__glyph" aria-hidden="true">{{ opt.glyph }}</span>
            </button>
          </el-tooltip>
        </div>
      </div>
    </header>

    <el-card shadow="never" class="toolbar-card" role="region" :aria-label="t('mesCuttingActual.title')">
      <div class="toolbar-layout">
        <div class="toolbar-field-row toolbar-field-row--day">
          <span class="toolbar-field-row__icon" aria-hidden="true">
            <el-icon><Calendar /></el-icon>
          </span>
          <span class="toolbar-field-row__label">{{ t('mesCuttingActual.productionDay') }}</span>
          <div class="toolbar-day-wrap">
            <el-date-picker
              v-model="productionDay"
              type="date"
              value-format="YYYY-MM-DD"
              :editable="false"
              teleported
              class="toolbar-control toolbar-day-picker"
            />
            <div class="toolbar-day-shortcuts">
              <el-tooltip :content="t('mesCuttingActual.dayPrev')" placement="top">
                <el-button
                  type="default"
                  size="small"
                  circle
                  :icon="ArrowLeft"
                  :aria-label="t('mesCuttingActual.dayPrev')"
                  @click="shiftProductionDay(-1)"
                />
              </el-tooltip>
              <el-button
                type="default"
                size="small"
                plain
                class="toolbar-day-today-btn"
                @click="setProductionDayToday"
              >
                {{ t('mesCuttingActual.dayToday') }}
              </el-button>
              <el-tooltip :content="t('mesCuttingActual.dayNext')" placement="top">
                <el-button
                  type="default"
                  size="small"
                  circle
                  :icon="ArrowRight"
                  :aria-label="t('mesCuttingActual.dayNext')"
                  @click="shiftProductionDay(1)"
                />
              </el-tooltip>
            </div>
          </div>
        </div>

        <div class="toolbar-field-row toolbar-field-row--machine">
          <span class="toolbar-field-row__icon toolbar-field-row__icon--machine" aria-hidden="true">
            <el-icon><SetUp /></el-icon>
          </span>
          <span class="toolbar-field-row__label">{{ t('mesCuttingActual.machine') }}</span>
          <div class="toolbar-machine-wrap">
            <el-select
              v-model="selectedMachineId"
              :filterable="machineSelectFilterable"
            clearable
            teleported
            :placeholder="t('mesCuttingActual.machinePlaceholder')"
            :loading="loadingMachines"
            class="toolbar-control toolbar-machine-select"
            :class="{ 'toolbar-machine-select--chosen': selectedMachineId != null }"
            @visible-change="onMachineSelectVisibleChange"
          >
            <el-option
              v-for="m in cuttingMachinesForSelect"
              :key="m.id"
              :label="(m.machine_name || '').trim() || m.machine_cd"
              :value="m.id"
            />
            </el-select>
          </div>
        </div>

        <div
          class="toolbar-field-row toolbar-field-row--switch toolbar-filter-switch"
          :class="{ 'toolbar-filter-switch--active': hideCompleted }"
        >
          <span class="toolbar-field-row__label toolbar-filter-switch__text">{{
            t('mesCuttingActual.hideCompleted')
          }}</span>
          <el-switch
            v-model="hideCompleted"
            class="toolbar-filter-switch__control"
            inline-prompt
            :active-text="t('mesCuttingActual.filterSwitchOn')"
            :inactive-text="t('mesCuttingActual.filterSwitchOff')"
          />
        </div>

        <el-button
          class="toolbar-control toolbar-load-btn"
          type="primary"
          :loading="loadingPlans"
          :disabled="!selectedMachineId"
          @click="loadPlans"
        >
          <el-icon class="btn-ico"><RefreshRight /></el-icon>
          {{ t('mesCuttingActual.loadPlans') }}
        </el-button>
      </div>
    </el-card>

    <div v-if="showOfflineAlert" class="offline-strip" role="status">
      <span class="offline-strip__dot" aria-hidden="true" />
      {{ offlineAlertText }}
    </div>

    <div v-loading="loadingPlans" class="plan-board">
      <template v-if="!selectedMachineId">
        <el-empty :description="t('mesCuttingActual.emptySelectMachine')" />
      </template>
      <template v-else-if="!loadingPlans && visibleRowsByDay.length === 0">
        <el-empty :description="t('mesCuttingActual.emptyNoPlans')" />
      </template>
      <div v-else class="plan-list">
        <section
          v-for="grp in visibleRowsByDay"
          :key="grp.dayKey"
          class="plan-day-group"
          :class="{ 'plan-day-group--anchor': grp.isAnchorDay }"
        >
          <header class="plan-day-group__head">
            <div class="plan-day-group__title-row">
              <span class="plan-day-group__date-bold">{{ formatGroupDayLabel(grp.dayKey) }}</span>
              <el-tag v-if="grp.isAnchorDay" size="small" effect="dark" type="primary" class="plan-day-group__badge">
                {{ t('mesCuttingActual.anchorDayBadge') }}
              </el-tag>
            </div>
            <span class="plan-day-group__count">{{ grp.rows.length }} {{ t('mesCuttingActual.planLinesSuffix') }}</span>
          </header>

          <div
            :ref="(el) => setPlanDayListRef(grp.dayKey, el)"
            class="plan-day-group__cards"
          >
          <el-card
            v-for="row in grp.rows"
            :key="row.id"
            shadow="hover"
            class="plan-row-card"
            :class="{ 'plan-row-card--confirmed': isCuttingRowConfirmedForDisplay(row) }"
          >
          <div class="plan-row">
            <div class="plan-row__head">
              <span
                class="plan-row-card__drag-handle"
                :title="t('mesCuttingActual.dragToReorder')"
                aria-hidden="true"
              >
                <el-icon :size="16"><Rank /></el-icon>
              </span>
              <span class="plan-seq-pill">{{ t('mesCuttingActual.seq') }} {{ row.production_sequence ?? '—' }}</span>
              <el-tag :type="statusTagType(row)" size="small" effect="plain">{{ statusText(row) }}</el-tag>
              <el-button
                v-if="canScanBarcodeForRow(row)"
                link
                type="primary"
                size="small"
                class="plan-status-action-btn"
                :loading="barcodeScanSaving && barcodeScanTargetRow?.id === row.id"
                @click="openBarcodeScanDialog(row)"
              >
                <el-icon><Camera /></el-icon>
                {{ t('mesCuttingActual.btnScanCode') }}
              </el-button>
              <div
                v-if="
                  (canScanBarcodeForRow(row) && rowHasScanRegistration(row)) ||
                  rowRemarksText(row)
                "
                class="plan-row-scan-remarks-cluster"
              >
                <ScanRegisteredHint
                  v-if="canScanBarcodeForRow(row) && rowHasScanRegistration(row)"
                  :scanned-code="(row.mes_scanned_code ?? '').trim()"
                  :management-code="row.management_code"
                />
                <span
                  v-if="rowRemarksText(row)"
                  class="plan-row-remarks"
                  :title="rowRemarksText(row)"
                >{{ rowRemarksText(row) }}</span>
              </div>
              <el-button
                v-if="isCuttingRowConfirmed(row)"
                link
                type="primary"
                size="small"
                class="plan-status-action-btn"
                @click="openConfirmedEditDialog(row)"
              >
                <el-icon><Edit /></el-icon>
                {{ t('mesCuttingActual.btnEditConfirmed') }}
              </el-button>
            </div>

            <div class="plan-row__meta">
              <div class="plan-meta-primary">
                <span class="plan-product-name" :title="row.product_name || ''">{{
                  row.product_name || '—'
                }}</span>
                <span
                  v-if="productMaterialNameText(row)"
                  class="plan-product-material"
                  :title="productMaterialNameText(row)"
                >
                  {{ productMaterialNameText(row) }}
                </span>
              </div>
              <div class="plan-meta-chips">
                <span
                  class="plan-chip plan-chip--qty"
                  :class="{ 'plan-chip--qty-actual': isCuttingRowConfirmedForDisplay(row) }"
                >
                  <span class="plan-chip__label">{{ rowQtyChipLabel(row) }}</span>
                  <span class="plan-chip__value">{{ rowQtyChipValue(row) }}</span>
                </span>
                <span v-if="formatMgmtCodeShort(row.management_code)" class="plan-chip plan-chip--code">
                  {{ formatMgmtCodeShort(row.management_code) }}
                </span>
                <div class="plan-meta-field plan-meta-field--operator">
                  <span class="plan-meta-field__label">
                    <el-icon class="plan-meta-field__icon" aria-hidden="true"><User /></el-icon>
                    {{ t('mesCuttingActual.operator') }}
                  </span>
                  <el-select
                    v-model="ensureSession(row.id).operatorUserId"
                    filterable
                    clearable
                    teleported
                    :disabled="isCuttingRowConfirmedForDisplay(row)"
                    :placeholder="t('mesCuttingActual.operatorPlaceholder')"
                    :loading="loadingUsers"
                    class="plan-field__control plan-field__control--operator"
                  >
                    <el-option
                      v-for="u in operators"
                      :key="u.id"
                      :label="u.full_name || u.username"
                      :value="u.id"
                    />
                  </el-select>
                </div>
                <div class="plan-meta-field plan-meta-field--setup">
                  <span class="plan-meta-field__label">
                    <el-icon class="plan-meta-field__icon" aria-hidden="true"><Clock /></el-icon>
                    {{ t('mesCuttingActual.setupTime') }}
                    <span class="plan-meta-field__unit">（{{ t('mesCuttingActual.setupTimeUnit') }}）</span>
                  </span>
                  <el-input-number
                    v-model="ensureSession(row.id).setupTimeMin"
                    :min="0"
                    :step="1"
                    :precision="0"
                    :disabled="isCuttingRowConfirmedForDisplay(row)"
                    class="plan-field__number plan-field__number--setup"
                  />
                </div>
              </div>
            </div>

            <div class="plan-row__ops">
            <div class="plan-row__timer">
              <div
                class="timer-compact"
                :class="`timer-compact--${timerPhase(ensureSession(row.id))}`"
              >
                <div class="timer-compact__top">
                  <span class="timer-compact__label">
                    <el-icon class="timer-compact__label-icon" aria-hidden="true"><Clock /></el-icon>
                    {{ t('mesCuttingActual.elapsed') }}
                  </span>
                  <span class="timer-compact__phase">{{ timerPhaseLabel(ensureSession(row.id)) }}</span>
                </div>
                <div class="timer-compact__readout-row">
                  <div
                    class="timer-compact__readout"
                    :class="{
                      'timer-compact__readout--display-frozen':
                        timerPhase(ensureSession(row.id)) === 'paused',
                    }"
                  >{{ formatElapsed(operationDisplayMs(ensureSession(row.id))) }}</div>
                  <div
                    v-if="ensureSession(row.id).wallStart != null"
                    class="timer-compact__pause-side"
                  >
                    <span class="timer-compact__pause-label">{{ t('mesCuttingActual.pausedAccum') }}</span>
                    <span class="timer-compact__pause-value">{{
                      formatElapsed(pausedAccumMs(ensureSession(row.id)))
                    }}</span>
                  </div>
                </div>
                <div class="timer-compact__walls">
                  <span>{{ formatWall(ensureSession(row.id).wallStart) }}</span>
                  <span class="timer-compact__sep">→</span>
                  <span>{{ formatWall(ensureSession(row.id).wallEnd) }}</span>
                </div>
              </div>
            </div>
            <div class="plan-row__actions">
              <el-button
                class="plan-act-btn plan-act-btn--start"
                :class="{
                  'plan-act-btn--start--locked': isProductionInProgress(ensureSession(row.id)),
                }"
                :disabled="!canStartTimer(ensureSession(row.id), row.id)"
                @click="onStart(row.id)"
              >
                <el-icon><VideoPlay /></el-icon>
                {{ t('mesCuttingActual.btnStart') }}
              </el-button>
              <el-button
                v-if="canPauseTimer(ensureSession(row.id))"
                class="plan-act-btn plan-act-btn--pause"
                @click="onPause(row.id!)"
              >
                <el-icon><VideoPause /></el-icon>
                {{ t('mesCuttingActual.btnPause') }}
              </el-button>
              <el-button
                v-else-if="canResumeTimer(ensureSession(row.id))"
                class="plan-act-btn plan-act-btn--resume"
                @click="onResume(row.id!)"
              >
                <el-icon><VideoPlay /></el-icon>
                {{ t('mesCuttingActual.btnResume') }}
              </el-button>
              <el-button v-else class="plan-act-btn plan-act-btn--pause" disabled>
                <el-icon><VideoPause /></el-icon>
                {{ t('mesCuttingActual.btnPause') }}
              </el-button>
              <el-button
                class="plan-act-btn plan-act-btn--end"
                :disabled="!canEndProduction(ensureSession(row.id))"
                @click="openProductionEndDialog(row)"
              >
                <el-icon><CircleCheck /></el-icon>
                {{ t('mesCuttingActual.btnEnd') }}
              </el-button>
              <el-button
                v-if="canChangeMachine(row)"
                class="plan-act-btn plan-act-btn--machine"
                @click="openChangeMachineDialog(row)"
              >
                <el-icon><SetUp /></el-icon>
                {{ t('mesCuttingActual.btnChangeMachine') }}
              </el-button>
            </div>
            </div>

          </div>
        </el-card>
          </div>
        </section>
      </div>
    </div>

    <el-dialog
      v-model="endDialogVisible"
      :title="t('mesCuttingActual.endDialogTitle')"
      width="480px"
      append-to-body
      destroy-on-close
      align-center
      class="production-end-dialog"
    >
      <div v-if="endDialogRow" class="end-dialog-body">
        <p class="end-dialog-product">{{ endDialogRow.product_cd }} · {{ endDialogRow.product_name }}</p>
        <el-alert
          v-if="endDialogBaseline <= 0"
          class="end-dialog-warn"
          type="warning"
          :closable="false"
          show-icon
          :title="t('mesCuttingActual.endDialogBaselineZero')"
        />
        <el-alert
          v-if="endDialogMetaIncomplete"
          class="end-dialog-warn"
          type="warning"
          :closable="false"
          show-icon
          :title="t('mesCuttingActual.endDialogMetaMissingHint')"
        />
        <div class="end-dialog-meta">
          <div class="end-dialog-meta-item">
            <span class="end-dialog-meta-label">{{ t('mesCuttingActual.operator') }}</span>
            <span v-if="endDialogHasOperator" class="end-dialog-meta-value">{{ endDialogOperatorLabel }}</span>
            <span v-else class="end-dialog-meta-missing">{{ t('mesCuttingActual.endDialogOperatorMissing') }}</span>
          </div>
          <div class="end-dialog-meta-item">
            <span class="end-dialog-meta-label">{{ t('mesCuttingActual.setupTime') }}</span>
            <span v-if="endDialogHasSetupTime" class="end-dialog-meta-value">
              {{ endDialogSetupTimeLabel }} {{ t('mesCuttingActual.setupTimeUnit') }}
            </span>
            <span v-else class="end-dialog-meta-missing">{{ t('mesCuttingActual.endDialogSetupTimeMissing') }}</span>
          </div>
        </div>
        <div class="end-dialog-field">
          <span class="end-dialog-label">{{ t('mesCuttingActual.endDialogQtyLabel') }}</span>
          <el-input
            v-model="endDialogQty"
            class="end-dialog-input"
            inputmode="numeric"
            :placeholder="t('mesCuttingActual.endDialogQtyPlaceholder')"
            clearable
            @keyup.enter="endDialogBaseline > 0 ? submitProductionEndDefer() : submitProductionEndZeroBaseline()"
          />
        </div>
        <div v-if="endDialogBaseline > 0" class="end-dialog-defer-settings">
          <div class="end-dialog-field">
            <span class="end-dialog-label">{{ t('mesCuttingActual.deferNextDayLabel') }}</span>
            <el-date-picker
              v-model="endDialogDeferDay"
              type="date"
              value-format="YYYY-MM-DD"
              :editable="false"
              teleported
              size="small"
              class="end-dialog-defer-day"
              :disabled-date="disabledWeekendDeferDate"
            />
          </div>
          <p v-if="endDialogDeferRemainder > 0" class="end-dialog-defer-remainder">
            {{ t('mesCuttingActual.deferRemainderHint', { n: endDialogDeferRemainder }) }}
          </p>
          <el-checkbox
            v-if="endDialogSubsequentDeferCount > 0"
            v-model="endDialogDeferSubsequent"
            class="end-dialog-defer-subsequent"
          >
            {{ t('mesCuttingActual.deferSubsequentLabel', { n: endDialogSubsequentDeferCount }) }}
          </el-checkbox>
        </div>
        <div class="end-dialog-actions">
          <el-button
            v-if="endDialogBaseline > 0"
            class="end-dialog-btn end-dialog-btn--full"
            type="success"
            :loading="endDialogSubmitting"
            @click="submitProductionEndFullBaseline"
          >
            {{ t('mesCuttingActual.btnCompleteFull', { n: endDialogBaseline }) }}
          </el-button>
          <el-button
            v-if="endDialogBaseline > 0"
            class="end-dialog-btn end-dialog-btn--defer"
            type="warning"
            :loading="endDialogSubmitting"
            @click="submitProductionEndDefer"
          >
            {{ t('mesCuttingActual.btnDeferConfirm') }}
          </el-button>
          <el-button
            v-if="endDialogBaseline <= 0"
            class="end-dialog-btn end-dialog-btn--full"
            type="primary"
            :loading="endDialogSubmitting"
            @click="submitProductionEndZeroBaseline"
          >
            {{ t('mesCuttingActual.btnCompleteWithInput') }}
          </el-button>
          <el-button class="end-dialog-btn end-dialog-btn--cancel" :disabled="endDialogSubmitting" @click="closeProductionEndDialog">
            {{ t('common.cancel') }}
          </el-button>
        </div>
      </div>
    </el-dialog>
    <el-dialog
      v-model="changeMachineDialogVisible"
      width="460px"
      append-to-body
      destroy-on-close
      align-center
      class="change-machine-dialog"
      @close="closeChangeMachineDialog"
    >
      <template #header>
        <div class="change-machine-header">
          <div class="change-machine-header__main">
            <span class="change-machine-header__icon" aria-hidden="true">
              <el-icon :size="18"><SetUp /></el-icon>
            </span>
            <span class="change-machine-header__text">
              <span class="change-machine-header__title">{{
                t('mesCuttingActual.changeMachineDialogTitle')
              }}</span>
              <span class="change-machine-header__sub">{{
                t('mesCuttingActual.changeMachineDialogSub')
              }}</span>
            </span>
          </div>
        </div>
      </template>
      <div v-if="changeMachineRow" class="change-machine-body">
        <div class="change-machine-hero">
          <span
            v-if="formatMgmtCodeShort(changeMachineRow.management_code)"
            class="change-machine-hero__code"
          >
            {{ formatMgmtCodeShort(changeMachineRow.management_code) }}
          </span>
          <span class="change-machine-hero__product">
            <strong>{{ changeMachineRow.product_cd }}</strong>
            <span class="change-machine-hero__sep">·</span>
            {{ changeMachineRow.product_name }}
          </span>
        </div>
        <div class="change-machine-flow">
          <div class="change-machine-card change-machine-card--current">
            <span class="change-machine-card__label">{{
              t('mesCuttingActual.changeMachineCurrent')
            }}</span>
            <span class="change-machine-card__value">{{ changeMachineCurrentName }}</span>
          </div>
          <span class="change-machine-flow__arrow" aria-hidden="true">
            <el-icon :size="20"><ArrowRight /></el-icon>
          </span>
          <div class="change-machine-card change-machine-card--target">
            <span class="change-machine-card__label">{{
              t('mesCuttingActual.changeMachineTarget')
            }}</span>
            <el-select
              v-model="changeMachineTargetId"
              :filterable="machineSelectFilterable"
              teleported
              size="default"
              class="change-machine-select"
              :class="{ 'change-machine-select--chosen': changeMachineTargetId != null }"
              :placeholder="t('mesCuttingActual.machinePlaceholder')"
              :loading="loadingMachines"
              @visible-change="onMachineSelectVisibleChange"
            >
              <el-option
                v-for="m in cuttingMachinesForSelect"
                :key="m.id"
                :label="(m.machine_name || '').trim() || m.machine_cd"
                :value="m.id"
              />
            </el-select>
          </div>
        </div>
        <p class="change-machine-hint">{{ t('mesCuttingActual.changeMachineDialogHint') }}</p>
        <div class="change-machine-actions">
          <el-button
            class="change-machine-actions__submit"
            type="primary"
            :loading="changeMachineSubmitting"
            @click="submitChangeMachine"
          >
            {{ t('mesCuttingActual.btnChangeMachineSave') }}
          </el-button>
          <el-button
            class="change-machine-actions__cancel"
            :disabled="changeMachineSubmitting"
            @click="closeChangeMachineDialog"
          >
            {{ t('common.cancel') }}
          </el-button>
        </div>
      </div>
    </el-dialog>
    <el-dialog
      v-model="confirmedEditDialogVisible"
      width="500px"
      append-to-body
      destroy-on-close
      align-center
      class="confirmed-edit-dialog"
      @close="closeConfirmedEditDialog"
    >
      <template #header>
        <div class="confirmed-edit-header">
          <div class="confirmed-edit-header__main">
            <span class="confirmed-edit-header__icon" aria-hidden="true">
              <el-icon :size="18"><Edit /></el-icon>
            </span>
            <span class="confirmed-edit-header__text">
              <span class="confirmed-edit-header__title">{{
                t('mesCuttingActual.confirmedEditDialogTitle')
              }}</span>
              <span class="confirmed-edit-header__sub">{{ t('mesCuttingActual.cmConfirmed') }}</span>
            </span>
          </div>
          <el-button
            v-if="confirmedEditRow"
            class="confirmed-edit-header__clear"
            size="small"
            :loading="confirmedEditClearing"
            :disabled="confirmedEditSaving || confirmedEditClearing"
            @click="clearConfirmedMesAndSave"
          >
            <el-icon class="confirmed-edit-header__clear-icon"><RefreshLeft /></el-icon>
            {{ t('mesCuttingActual.btnClearMesActual') }}
          </el-button>
        </div>
      </template>
      <div v-if="confirmedEditRow && confirmedEditForm" class="confirmed-edit-body">
        <div class="confirmed-edit-hero">
          <span class="confirmed-edit-badge">{{ t('mesCuttingActual.cmConfirmed') }}</span>
          <span
            v-if="formatMgmtCodeShort(confirmedEditRow.management_code)"
            class="confirmed-edit-hero__code"
          >
            {{ formatMgmtCodeShort(confirmedEditRow.management_code) }}
          </span>
          <span class="confirmed-edit-hero__product">
            <strong>{{ confirmedEditRow.product_cd }}</strong>
            <span class="confirmed-edit-hero__sep">·</span>
            {{ confirmedEditRow.product_name }}
          </span>
        </div>
        <el-form label-position="top" size="small" class="confirmed-edit-form">
          <section class="confirmed-edit-section confirmed-edit-section--people">
            <h4 class="confirmed-edit-section__title">
              <el-icon :size="14"><User /></el-icon>
              {{ t('mesCuttingActual.operator') }} / {{ t('mesCuttingActual.actualQty') }}
            </h4>
            <el-form-item :label="t('mesCuttingActual.operator')" class="confirmed-edit-form-item">
            <el-select
              v-model="confirmedEditForm.operatorUserId"
              filterable
              clearable
              size="small"
              :placeholder="t('mesCuttingActual.operatorPlaceholder')"
              :loading="loadingUsers"
              class="confirmed-edit-full"
            >
              <el-option
                v-for="u in operators"
                :key="u.id"
                :label="u.full_name || u.username"
                :value="u.id"
              />
            </el-select>
          </el-form-item>
          <div class="confirmed-edit-form-row">
            <el-form-item :label="t('mesCuttingActual.actualQty')" class="confirmed-edit-form-item">
              <el-input-number
                v-model="confirmedEditForm.actualQty"
                size="small"
                :min="0"
                :step="1"
                :precision="0"
                controls-position="right"
                class="confirmed-edit-full"
              />
            </el-form-item>
            <el-form-item
              :label="`${t('mesCuttingActual.setupTime')}（${t('mesCuttingActual.setupTimeUnit')}）`"
              class="confirmed-edit-form-item"
            >
              <el-input-number
                v-model="confirmedEditForm.setupTimeMin"
                size="small"
                :min="0"
                :step="1"
                :precision="0"
                controls-position="right"
                class="confirmed-edit-full"
              />
            </el-form-item>
          </div>
          </section>
          <section class="confirmed-edit-section confirmed-edit-section--time">
            <h4 class="confirmed-edit-section__title">
              <el-icon :size="14"><Clock /></el-icon>
              {{ t('mesCuttingActual.productionStart') }} / {{ t('mesCuttingActual.elapsed') }}
            </h4>
            <div class="confirmed-edit-form-row">
          <el-form-item :label="t('mesCuttingActual.productionStart')" class="confirmed-edit-form-item">
            <el-date-picker
              v-model="confirmedEditForm.wallStart"
              type="datetime"
              size="small"
              :editable="false"
              teleported
              format="YYYY/MM/DD HH:mm"
              class="confirmed-edit-full"
            />
          </el-form-item>
          <el-form-item :label="t('mesCuttingActual.productionEnd')" class="confirmed-edit-form-item">
            <el-date-picker
              v-model="confirmedEditForm.wallEnd"
              type="datetime"
              size="small"
              :editable="false"
              teleported
              format="YYYY/MM/DD HH:mm"
              class="confirmed-edit-full"
            />
          </el-form-item>
            </div>
            <div class="confirmed-edit-form-row confirmed-edit-form-row--metrics">
            <el-form-item
              :label="`${t('mesCuttingActual.pausedAccum')}（${t('mesCuttingActual.pausedAccumUnit')}）`"
              class="confirmed-edit-form-item"
            >
              <el-input-number
                v-model="confirmedEditForm.pausedAccumSec"
                size="small"
                :min="0"
                :step="1"
                :precision="0"
                controls-position="right"
                class="confirmed-edit-full"
              />
            </el-form-item>
            <el-form-item :label="t('mesCuttingActual.elapsed')" class="confirmed-edit-form-item">
              <div class="confirmed-edit-elapsed" role="status">
                <span class="confirmed-edit-elapsed__value">{{ confirmedEditElapsedPreview }}</span>
              </div>
            </el-form-item>
            </div>
          </section>
          <div class="confirmed-edit-hint" role="note">
            <el-icon class="confirmed-edit-hint__icon" :size="14"><InfoFilled /></el-icon>
            <span>{{ t('mesCuttingActual.confirmedEditPauseHint') }}</span>
          </div>
        </el-form>
      </div>
      <template #footer>
        <div class="confirmed-edit-footer">
          <el-button
            class="confirmed-edit-btn confirmed-edit-btn--cancel"
            size="small"
            :disabled="confirmedEditSaving || confirmedEditClearing"
            @click="closeConfirmedEditDialog"
          >
            {{ t('common.cancel') }}
          </el-button>
          <el-button
            class="confirmed-edit-btn confirmed-edit-btn--save"
            type="primary"
            size="small"
            :loading="confirmedEditSaving"
            :disabled="confirmedEditClearing"
            @click="submitConfirmedEdit"
          >
            {{ t('mesCuttingActual.btnSaveConfirmed') }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <MesBarcodeScanDialog
      v-model="barcodeScanDialogVisible"
      :product-label="barcodeScanProductLabel(barcodeScanTargetRow)"
      :existing-scanned-code="
        barcodeScanTargetRow?.mes_scanned_code
          ? String(barcodeScanTargetRow.mes_scanned_code).trim()
          : ''
      "
      :management-code="barcodeScanTargetRow?.management_code ?? null"
      @scanned="onBarcodeScanned"
    />

  </div>
</template>

<style scoped>
.cutting-actual-page {
  --ca-radius: 10px;
  --ca-gap: 8px;
  padding: 10px 12px 16px;
  padding-bottom: max(16px, env(safe-area-inset-bottom, 0px));
  max-width: min(1680px, 100%);
  margin: 0 auto;
  box-sizing: border-box;
  background: var(--el-bg-color-page);
}

.page-head {
  margin-bottom: 8px;
}

.page-head-row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px 16px;
}

.page-head-main {
  flex: 1 1 240px;
  min-width: 0;
}

.page-head-locale {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.locale-glyph-btn {
  width: 36px;
  height: 36px;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  border: 1px solid var(--el-border-color);
  background: var(--el-fill-color-blank);
  color: var(--el-text-color-regular);
  cursor: pointer;
  transition:
    background 0.15s ease,
    border-color 0.15s ease,
    color 0.15s ease,
    box-shadow 0.15s ease;
}

.locale-glyph-btn:hover {
  border-color: var(--el-color-primary-light-5);
  color: var(--el-color-primary);
  background: var(--el-fill-color-light);
}

.locale-glyph-btn--active {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  font-weight: 700;
  box-shadow: 0 0 0 1px var(--el-color-primary-light-7);
}

.locale-glyph-btn__glyph {
  font-size: 0.95rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  line-height: 1;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  font-size: 1.2rem;
  font-weight: 700;
  letter-spacing: 0.01em;
  line-height: 1.25;
}

.page-title__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 38px;
  height: 38px;
  border-radius: 10px;
  color: #fff;
  background: linear-gradient(
    135deg,
    var(--el-color-primary) 0%,
    #38bdf8 48%,
    var(--el-color-success) 100%
  );
  box-shadow:
    0 4px 14px rgba(64, 158, 255, 0.28),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

.page-head:hover .page-title__icon {
  transform: translateY(-1px) scale(1.03);
  box-shadow:
    0 6px 18px rgba(64, 158, 255, 0.34),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
}

.page-title__icon .el-icon {
  font-size: 20px;
}

.page-title__text {
  color: var(--el-text-color-primary);
}

.offline-strip {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  padding: 6px 10px;
  border-radius: 8px;
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--el-color-warning-dark-2);
  background: var(--el-color-warning-light-9);
  border: 1px solid var(--el-color-warning-light-5);
}

.offline-strip__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--el-color-warning);
  flex-shrink: 0;
  animation: offline-pulse 1.4s ease-in-out infinite;
}

@keyframes offline-pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.35;
  }
}

.toolbar-card {
  --toolbar-h: 36px;
  --toolbar-day-picker-w: 150px;
  --toolbar-machine-select-w: 115px;
  --toolbar-machine-gap: 6px;
  --toolbar-day-gap: 5px;
  --toolbar-day-shortcut-size: 28px;
  --toolbar-day-today-min-w: 36px;
  border-radius: var(--ca-radius);
  border: 1px solid var(--el-border-color-lighter);
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.04);
}

.toolbar-card :deep(.el-card__body) {
  padding: 10px 12px;
}

.toolbar-layout {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px 12px;
}

.toolbar-field-row {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex: 0 0 auto;
  min-height: var(--toolbar-h);
}

.toolbar-field-row__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: var(--toolbar-h);
  height: var(--toolbar-h);
  border-radius: 8px;
  font-size: 16px;
  color: #fff;
  background: linear-gradient(135deg, var(--el-color-primary) 0%, #38bdf8 100%);
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.28);
}

.toolbar-field-row__label {
  flex-shrink: 0;
  font-size: 0.8125rem;
  font-weight: 600;
  line-height: 1;
  color: var(--el-text-color-regular);
  white-space: nowrap;
}

.toolbar-field-row--day {
  flex: 0 1 auto;
  max-width: max-content;
  padding: 0 8px 0 0;
  gap: 6px;
  border-radius: 10px;
  border: 1px solid var(--el-color-primary-light-7);
  background: linear-gradient(
    165deg,
    var(--el-color-primary-light-9) 0%,
    var(--el-fill-color-blank) 55%,
    var(--el-fill-color-light) 100%
  );
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.75);
}

.toolbar-field-row--day .toolbar-field-row__icon {
  margin-left: -1px;
  border-radius: 9px 0 0 9px;
}

.toolbar-field-row--day .toolbar-field-row__label {
  color: var(--el-color-primary-dark-2);
}

.toolbar-control :deep(.el-input__wrapper),
.toolbar-control :deep(.el-select__wrapper) {
  min-height: var(--toolbar-h);
  height: var(--toolbar-h);
  box-sizing: border-box;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
}

.toolbar-control :deep(.el-input__inner) {
  height: calc(var(--toolbar-h) - 2px);
  line-height: calc(var(--toolbar-h) - 2px);
}

.toolbar-day-wrap {
  display: inline-flex;
  align-items: center;
  gap: var(--toolbar-day-gap);
  flex: 0 0 auto;
  max-width: calc(
    var(--toolbar-day-picker-w) + var(--toolbar-day-shortcut-size) * 2 +
      var(--toolbar-day-today-min-w) + var(--toolbar-day-gap) * 3
  );
}

.toolbar-day-shortcuts {
  display: inline-flex;
  align-items: center;
  gap: var(--toolbar-day-gap);
  flex-shrink: 0;
}

.toolbar-day-shortcuts :deep(.el-button.is-circle) {
  width: var(--toolbar-day-shortcut-size);
  height: var(--toolbar-day-shortcut-size);
  padding: 0;
}

.toolbar-day-today-btn {
  min-width: var(--toolbar-day-today-min-w);
  height: var(--toolbar-day-shortcut-size);
  padding: 0 6px;
  font-size: 0.75rem;
  font-weight: 600;
}

.toolbar-day-picker.el-date-editor {
  --el-date-editor-width: var(--toolbar-day-picker-w);
  width: var(--toolbar-day-picker-w) !important;
  max-width: var(--toolbar-day-picker-w);
  flex: 0 0 var(--toolbar-day-picker-w);
}

.toolbar-day-picker :deep(.el-input__wrapper),
.toolbar-day-picker :deep(.el-input__inner) {
  width: 100%;
}

.toolbar-field-row--machine {
  flex: 0 1 auto;
  max-width: max-content;
  gap: var(--toolbar-machine-gap);
  padding: 0 8px 0 0;
  border-radius: 10px;
  border: 1px solid var(--el-color-warning-light-7);
  background: linear-gradient(
    165deg,
    var(--el-color-warning-light-9) 0%,
    var(--el-fill-color-blank) 55%,
    #fff7ed 100%
  );
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.8),
    0 1px 4px rgba(234, 88, 12, 0.06);
}

.toolbar-field-row--machine .toolbar-field-row__icon--machine {
  margin-left: -1px;
  border-radius: 9px 0 0 9px;
  background: linear-gradient(135deg, #f59e0b 0%, #ea580c 100%);
  box-shadow: 0 2px 8px rgba(234, 88, 12, 0.3);
}

.toolbar-field-row--machine .toolbar-field-row__label {
  color: #9a3412;
}

.toolbar-machine-wrap {
  display: inline-flex;
  flex: 0 0 auto;
  max-width: var(--toolbar-machine-select-w);
}

.toolbar-field-row--switch.toolbar-filter-switch {
  padding: 0 10px;
  border-radius: 999px;
  border: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-blank);
  transition:
    border-color 0.2s ease,
    background 0.2s ease,
    box-shadow 0.2s ease;
}

.toolbar-filter-switch--active {
  border-color: var(--el-color-success-light-5);
  background: linear-gradient(180deg, var(--el-color-success-light-9) 0%, var(--el-fill-color-blank) 100%);
  box-shadow: 0 0 0 1px var(--el-color-success-light-7);
}

.toolbar-filter-switch--active .toolbar-filter-switch__text {
  color: var(--el-color-success-dark-2);
}

.toolbar-filter-switch__control {
  --el-switch-on-color: var(--el-color-success);
  --el-switch-off-color: var(--el-border-color);
}

.toolbar-filter-switch__control :deep(.el-switch__core) {
  min-width: 44px;
  height: 22px;
  border-radius: 11px;
}

.toolbar-filter-switch__control :deep(.el-switch__inner) {
  font-size: 10px;
  font-weight: 700;
}

.toolbar-load-btn {
  height: var(--toolbar-h);
  min-height: var(--toolbar-h);
  padding: 0 14px;
  font-weight: 600;
  border-radius: 8px;
  border: none;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.25);
}

.toolbar-load-btn:not(.is-disabled) {
  background: linear-gradient(180deg, #79bbff 0%, var(--el-color-primary) 100%);
}

.full-width-control {
  width: 100%;
}

.toolbar-machine-select {
  width: var(--toolbar-machine-select-w) !important;
  max-width: var(--toolbar-machine-select-w);
  flex: 0 0 var(--toolbar-machine-select-w);
}

.toolbar-machine-select :deep(.el-select__wrapper),
.toolbar-machine-select :deep(.el-input__wrapper) {
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  background: var(--el-fill-color-blank);
  border: 1px solid var(--el-color-warning-light-5);
  box-shadow: 0 1px 2px rgba(234, 88, 12, 0.06);
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    background 0.2s ease;
}

.toolbar-machine-select :deep(.el-select__wrapper:hover) {
  border-color: var(--el-color-warning);
}

.toolbar-machine-select :deep(.el-select__wrapper.is-focused) {
  border-color: var(--el-color-warning);
  box-shadow: 0 0 0 2px var(--el-color-warning-light-8);
}

.toolbar-machine-select :deep(.el-select__selected-item),
.toolbar-machine-select :deep(.el-select__placeholder) {
  font-weight: 600;
}

.toolbar-machine-select--chosen :deep(.el-select__wrapper) {
  background: linear-gradient(180deg, #fffbeb 0%, var(--el-fill-color-blank) 100%);
  border-color: var(--el-color-warning);
}

.toolbar-machine-select--chosen :deep(.el-select__selected-item) {
  color: #9a3412;
}

.toolbar-machine-select :deep(.el-select__caret) {
  color: var(--el-color-warning);
}

/* タッチ端末: 検索用 input を出さずキーボードを抑止 */
@media (hover: none) and (pointer: coarse) {
  .toolbar-machine-select :deep(.el-select__input) {
    display: none !important;
  }
}

.btn-ico {
  margin-right: 4px;
  vertical-align: middle;
}

.plan-board {
  margin-top: 8px;
  min-height: 80px;
}

.plan-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.plan-day-group {
  border-radius: var(--ca-radius);
  padding: 0;
  background: var(--el-fill-color-blank);
  border: 1px solid var(--el-border-color-lighter);
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
}

.plan-day-group--anchor {
  border-color: var(--el-color-primary-light-5);
  box-shadow: 0 0 0 1px var(--el-color-primary-light-7);
}

.plan-day-group__head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 6px 12px;
  padding: 6px 10px;
  background: linear-gradient(180deg, var(--el-fill-color-light) 0%, var(--el-fill-color-blank) 100%);
  border-bottom: 1px solid var(--el-border-color-lighter);
  position: sticky;
  top: 0;
  z-index: 3;
}

.plan-day-group--anchor .plan-day-group__head {
  background: linear-gradient(
    180deg,
    var(--el-color-primary-light-9) 0%,
    var(--el-fill-color-blank) 100%
  );
}

.plan-day-group__title-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
  min-width: 0;
}

.plan-day-group__date-bold {
  font-size: clamp(0.95rem, 2.2vw, 1.05rem);
  font-weight: 700;
  color: var(--el-text-color-primary);
  line-height: 1.3;
}

.plan-day-group__badge {
  flex-shrink: 0;
}

.plan-day-group__count {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--el-text-color-secondary);
}

.plan-day-group__cards {
  display: flex;
  flex-direction: column;
}

.plan-day-group .plan-row-card {
  margin: 0 8px 8px;
  border-radius: 8px;
}

.plan-day-group .plan-row-card:first-of-type {
  margin-top: 8px;
}

.plan-row-card__drag-handle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  padding: 2px 4px;
  margin: -2px 0;
  border-radius: 6px;
  color: var(--el-text-color-secondary);
  cursor: grab;
  touch-action: none;
  user-select: none;
}

.plan-row-card__drag-handle:active {
  cursor: grabbing;
}

.plan-row-card--ghost {
  opacity: 0.42;
}

.plan-row-card--chosen {
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.12);
}

.plan-row-card {
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
  border-left: 3px solid var(--el-color-warning);
  transition:
    border-color 0.15s ease,
    box-shadow 0.15s ease;
}

.plan-row-card:hover {
  border-color: var(--el-border-color);
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
}

.plan-row-card--confirmed {
  border-left-color: var(--el-color-success);
  opacity: 0.92;
}

.plan-row-card :deep(.el-card__body) {
  padding: 10px 12px;
}

.plan-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.plan-row__head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 8px;
}

.plan-row-scan-remarks-cluster {
  display: inline-flex;
  align-items: center;
  gap: 130px;
  min-width: 0;
  flex: 0 1 auto;
  max-width: 100%;
}

.plan-row-remarks {
  flex: 0 1 auto;
  min-width: 0;
  max-width: min(28rem, 100%);
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--el-color-danger);
  line-height: 1.35;
  background: var(--el-color-danger-light-9);
  border: 1px solid var(--el-color-danger-light-5);
  box-shadow: 0 0 0 1px rgba(245, 108, 108, 0.15);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.plan-row__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: stretch;
  gap: 8px 10px;
  padding: 8px 10px;
  border-radius: 10px;
  background: linear-gradient(
    165deg,
    var(--el-fill-color-blank) 0%,
    var(--el-color-primary-light-9) 42%,
    var(--el-fill-color-light) 100%
  );
  border: 1px solid var(--el-color-primary-light-8);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.85);
}

.plan-row-card--confirmed .plan-row__meta {
  background: linear-gradient(165deg, var(--el-fill-color-blank) 0%, var(--el-color-success-light-9) 100%);
  border-color: var(--el-color-success-light-7);
}

.plan-meta-primary {
  display: inline-flex;
  flex-direction: row;
  flex-wrap: nowrap;
  align-items: center;
  gap: 8px;
  flex: 0 1 auto;
  width: fit-content;
  max-width: min(100%, 28rem);
  min-width: 0;
  padding: 5px 10px;
  border-radius: 8px;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border: 1px solid #93c5fd;
}

.plan-row-card--confirmed .plan-meta-primary {
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
  border-color: #86efac;
}

.plan-meta-chips {
  --plan-meta-control-h: 32px;
  --plan-meta-block-h: calc(var(--plan-meta-control-h) + 10px);
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  flex: 1 1 auto;
  min-width: 0;
}

.plan-meta-chips > .plan-chip,
.plan-meta-chips > .plan-meta-field {
  box-sizing: border-box;
  min-height: var(--plan-meta-block-h);
  height: var(--plan-meta-block-h);
}

.plan-row__ops {
  --plan-run-block-height: 5.25rem;
  --plan-act-btn-width: 6.25rem;
  box-sizing: border-box;
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  gap: 8px;
  height: var(--plan-run-block-height);
  max-height: var(--plan-run-block-height);
  overflow: hidden;
}

.plan-row__ops .plan-row__timer {
  flex: 0 0 auto;
  height: var(--plan-run-block-height);
  max-height: var(--plan-run-block-height);
  overflow: hidden;
}

.plan-row__ops .plan-row__actions {
  flex: 0 0 auto;
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  gap: 6px;
  height: var(--plan-run-block-height);
  max-height: var(--plan-run-block-height);
  overflow: hidden;
}

.plan-status-action-btn {
  padding: 0 4px;
  height: 22px;
  font-size: 0.75rem;
  font-weight: 600;
}

.plan-status-action-btn .el-icon {
  margin-right: 2px;
  font-size: 0.85rem;
}

.plan-seq-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2rem;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  background: var(--el-fill-color-light);
  color: #000;
  border: 1px solid var(--el-border-color-lighter);
}

.plan-field--inline {
  --plan-field-control-width: 108px;
  display: grid;
  grid-template-columns: 7.5rem var(--plan-field-control-width);
  column-gap: 6px;
  align-items: center;
  flex: 0 0 auto;
  width: calc(7.5rem + var(--plan-field-control-width) + 6px);
  max-width: 100%;
}

.plan-meta-field {
  --plan-meta-control-w: 108px;
  display: grid;
  grid-template-columns: auto var(--plan-meta-control-w);
  column-gap: 8px;
  align-items: center;
  min-width: 0;
  padding: 0 8px;
  border-radius: 8px;
  border: 1px solid transparent;
  flex: 0 1 auto;
  width: fit-content;
  max-width: 100%;
}

.plan-meta-field--operator {
  --plan-meta-control-w: 108px;
  background: linear-gradient(180deg, #f5f3ff 0%, #ede9fe 100%);
  border-color: #c4b5fd;
}

.plan-meta-field--setup {
  --plan-meta-control-w: 118px;
  background: linear-gradient(180deg, #fffbeb 0%, #fef3c7 100%);
  border-color: #fcd34d;
}

.plan-meta-field__label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.03em;
  line-height: 1.2;
  white-space: nowrap;
}

.plan-meta-field--operator .plan-meta-field__label {
  color: #5b21b6;
}

.plan-meta-field--setup .plan-meta-field__label {
  color: #b45309;
}

.plan-meta-field__icon {
  font-size: 0.9rem;
}

.plan-meta-field__unit {
  font-weight: 600;
  opacity: 0.85;
}

.plan-meta-field .plan-field__control--operator,
.plan-meta-field .plan-field__number--setup,
.plan-meta-field .plan-field__number--setup :deep(.el-input-number) {
  width: var(--plan-meta-control-w);
  max-width: 100%;
  justify-self: start;
}

.plan-meta-field--operator :deep(.el-select__wrapper) {
  min-height: var(--plan-meta-control-h);
  height: var(--plan-meta-control-h);
  background: rgba(255, 255, 255, 0.92);
  border-color: #c4b5fd;
  box-shadow: 0 1px 2px rgba(91, 33, 182, 0.08);
}

.plan-meta-field--operator :deep(.el-select__wrapper:hover) {
  border-color: #8b5cf6;
}

.plan-meta-field--setup :deep(.el-input-number__decrease),
.plan-meta-field--setup :deep(.el-input-number__increase) {
  background: rgba(255, 255, 255, 0.75);
  border-color: #fcd34d;
  color: #b45309;
}

.plan-meta-field--setup :deep(.el-input-number) {
  height: var(--plan-meta-control-h);
  line-height: var(--plan-meta-control-h);
}

.plan-meta-field--setup :deep(.el-input__wrapper) {
  min-height: var(--plan-meta-control-h);
  height: var(--plan-meta-control-h);
  background: rgba(255, 255, 255, 0.92);
  border-color: #fcd34d;
  box-shadow: 0 1px 2px rgba(180, 83, 9, 0.08);
}

.plan-field--inline .plan-field__label {
  display: block;
  margin-bottom: 0;
  white-space: nowrap;
  text-align: right;
  justify-self: end;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--el-text-color-regular);
}

.plan-field__control--operator,
.plan-field__number--setup,
.plan-field__number--setup :deep(.el-input-number) {
  width: var(--plan-field-control-width, 152px);
  justify-self: start;
}

.plan-field__number--setup :deep(.el-input-number__decrease),
.plan-field__number--setup :deep(.el-input-number__increase) {
  width: 34px;
  flex-shrink: 0;
  font-size: 14px;
}

.plan-field__number--setup :deep(.el-input__wrapper) {
  width: 100%;
  padding-left: 6px;
  padding-right: 6px;
}

.plan-field__number--setup :deep(.el-input__inner) {
  text-align: center;
}

.plan-product-name {
  flex: 0 1 auto;
  min-width: 0;
  max-width: 11rem;
  font-size: 0.95rem;
  font-weight: 800;
  line-height: 1.3;
  letter-spacing: 0.01em;
  color: #1e3a8a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.plan-row-card--confirmed .plan-product-name {
  color: #166534;
}

.plan-product-material {
  display: inline-flex;
  align-items: center;
  flex: 0 1 auto;
  min-width: 0;
  max-width: 14rem;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  line-height: 1.3;
  color: #0f766e;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid #5eead4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.plan-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  max-width: 100%;
  padding: 0 10px;
  border-radius: 8px;
  line-height: 1.25;
  border: 1px solid transparent;
}

.plan-chip__label {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  opacity: 0.9;
}

.plan-chip__value {
  font-size: 0.92rem;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

.plan-chip--qty {
  background: linear-gradient(180deg, #dbeafe 0%, #bfdbfe 100%);
  border-color: #60a5fa;
  color: #1e40af;
}

.plan-chip--qty .plan-chip__label {
  color: #1d4ed8;
}

.plan-chip--qty .plan-chip__value {
  color: #1e3a8a;
}

.plan-chip--qty-actual {
  background: linear-gradient(180deg, #dcfce7 0%, #bbf7d0 100%);
  border-color: #4ade80;
  color: #166534;
}

.plan-chip--qty-actual .plan-chip__label {
  color: #15803d;
}

.plan-chip--qty-actual .plan-chip__value {
  color: #14532d;
}

.plan-chip--code {
  background: linear-gradient(180deg, #f3e8ff 0%, #e9d5ff 100%);
  border-color: #c084fc;
  font-size: 0.8rem;
  font-weight: 700;
  color: #6b21a8;
  letter-spacing: 0.02em;
}

/* legacy aliases */
.plan-chip--accent {
  background: linear-gradient(180deg, #dbeafe 0%, #bfdbfe 100%);
  border-color: #60a5fa;
  color: #1e40af;
  font-weight: 600;
}

.plan-chip--muted {
  background: linear-gradient(180deg, #f3e8ff 0%, #e9d5ff 100%);
  border-color: #c084fc;
  color: #6b21a8;
}

.plan-row__timer {
  flex-shrink: 0;
}

.timer-compact {
  box-sizing: border-box;
  width: 15.5rem;
  min-width: 15.5rem;
  max-width: 15.5rem;
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid var(--el-border-color-lighter);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.75),
    0 1px 4px rgba(15, 23, 42, 0.06);
  overflow: hidden;
}

.plan-row__ops .timer-compact {
  height: 100%;
  max-height: var(--plan-run-block-height);
  padding: 6px 8px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  overflow: hidden;
}

.plan-row__ops .timer-compact__readout-row {
  margin: 1px 0;
}

.plan-row__ops .timer-compact__readout {
  font-size: 1.1rem;
  line-height: 1.05;
}

.plan-row__ops .timer-compact__pause-value {
  font-size: 0.88rem;
  line-height: 1.05;
}

.plan-row__ops .timer-compact__walls {
  font-size: 0.68rem;
  line-height: 1.1;
}

.timer-compact--idle {
  background: linear-gradient(165deg, #f8fafc 0%, #e2e8f0 100%);
  border-color: #cbd5e1;
}

.timer-compact--running {
  background: linear-gradient(165deg, #ecfdf5 0%, #d1fae5 55%, #f0fdf4 100%);
  border-color: #6ee7b7;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.85),
    0 0 0 1px rgba(16, 185, 129, 0.12),
    0 2px 8px rgba(16, 185, 129, 0.12);
}

.timer-compact--paused {
  background: linear-gradient(165deg, #fffbeb 0%, #fef3c7 55%, #fff7ed 100%);
  border-color: #fbbf24;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.85),
    0 0 0 1px rgba(245, 158, 11, 0.15);
}

.timer-compact--ended {
  background: linear-gradient(165deg, #eff6ff 0%, #dbeafe 55%, #f8fafc 100%);
  border-color: #93c5fd;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.85),
    0 0 0 1px rgba(59, 130, 246, 0.1);
}

.timer-compact__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  min-height: 0;
}

.timer-compact__label {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #64748b;
  white-space: nowrap;
}

.timer-compact__label-icon {
  font-size: 0.82rem;
}

.timer-compact--running .timer-compact__label {
  color: #047857;
}

.timer-compact--paused .timer-compact__label {
  color: #b45309;
}

.timer-compact--ended .timer-compact__label {
  color: #1d4ed8;
}

.timer-compact__phase {
  flex-shrink: 0;
  padding: 1px 7px;
  border-radius: 999px;
  font-size: 0.65rem;
  font-weight: 700;
  line-height: 1.35;
  letter-spacing: 0.02em;
  border: 1px solid transparent;
}

.timer-compact--idle .timer-compact__phase {
  color: #475569;
  background: rgba(255, 255, 255, 0.75);
  border-color: #cbd5e1;
}

.timer-compact--running .timer-compact__phase {
  color: #065f46;
  background: rgba(255, 255, 255, 0.8);
  border-color: #6ee7b7;
}

.timer-compact--paused .timer-compact__phase {
  color: #92400e;
  background: rgba(255, 255, 255, 0.82);
  border-color: #fcd34d;
}

.timer-compact--ended .timer-compact__phase {
  color: #1e40af;
  background: rgba(255, 255, 255, 0.82);
  border-color: #93c5fd;
}

.timer-compact__readout-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 6px;
  margin: 2px 0;
}

.timer-compact__readout {
  font-variant-numeric: tabular-nums;
  font-size: clamp(1.2rem, 3vw, 1.5rem);
  font-weight: 800;
  margin: 0;
  line-height: 1.1;
  flex: 1 1 auto;
  min-width: 0;
  color: #0f172a;
}

.timer-compact--running .timer-compact__readout {
  color: #047857;
}

.timer-compact--ended .timer-compact__readout {
  color: #1e3a8a;
}

.timer-compact__readout--display-frozen {
  color: #b45309;
  letter-spacing: 0.02em;
}

.timer-compact__pause-side {
  flex: 0 0 auto;
  text-align: right;
  line-height: 1.15;
  max-width: 46%;
  padding: 1px 5px;
  border-radius: 5px;
  background: rgba(255, 255, 255, 0.55);
}

.timer-compact__pause-label {
  display: block;
  font-size: 0.58rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: #78716c;
  white-space: nowrap;
}

.timer-compact__pause-value {
  display: block;
  font-variant-numeric: tabular-nums;
  font-size: clamp(0.92rem, 2.4vw, 1.1rem);
  font-weight: 700;
  color: #57534e;
}

.timer-compact--paused .timer-compact__pause-label,
.timer-compact--paused .timer-compact__pause-value {
  color: #b45309;
}

.timer-compact__walls {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  justify-content: center;
  gap: 4px 6px;
  font-size: 0.72rem;
  font-variant-numeric: tabular-nums;
  color: #64748b;
  white-space: nowrap;
  padding-top: 2px;
  border-top: 1px dashed rgba(100, 116, 139, 0.25);
}

.timer-compact--running .timer-compact__walls {
  color: #047857;
  border-top-color: rgba(4, 120, 87, 0.2);
}

.timer-compact--paused .timer-compact__walls {
  color: #b45309;
  border-top-color: rgba(180, 83, 9, 0.25);
}

.timer-compact--ended .timer-compact__walls {
  color: #1d4ed8;
  border-top-color: rgba(29, 78, 216, 0.2);
}

.timer-compact__walls > span:not(.timer-compact__sep) {
  flex-shrink: 0;
}

.timer-compact__sep {
  opacity: 0.5;
  flex-shrink: 0;
  color: inherit;
}

.plan-row__actions {
  display: flex;
  flex-wrap: nowrap;
  gap: 6px;
  align-items: stretch;
}

.plan-act-btn {
  margin: 0 !important;
  padding: 0 6px;
  font-size: 0.78rem;
  font-weight: 600;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.08);
  white-space: nowrap;
}

.plan-row__ops .plan-act-btn {
  box-sizing: border-box;
  width: var(--plan-act-btn-width, 6.25rem);
  min-width: var(--plan-act-btn-width, 6.25rem);
  max-width: var(--plan-act-btn-width, 6.25rem);
  height: var(--plan-run-block-height);
  min-height: unset;
  max-height: var(--plan-run-block-height);
  flex: 0 0 var(--plan-act-btn-width, 6.25rem);
  line-height: 1.15;
}

.plan-row__ops .plan-act-btn :deep(span) {
  line-height: 1.15;
}

.plan-act-btn :deep(.el-icon) {
  margin-right: 3px;
  font-size: 1rem;
}

.plan-act-btn--start:not(.is-disabled):not(.plan-act-btn--start--locked) {
  --el-button-bg-color: var(--el-color-success);
  --el-button-border-color: var(--el-color-success);
  --el-button-hover-bg-color: #3ecf7a;
  --el-button-hover-border-color: #3ecf7a;
  --el-button-active-bg-color: #529b2e;
  --el-button-active-border-color: #529b2e;
  --el-button-text-color: #fff;
  background: linear-gradient(180deg, #4cd787 0%, var(--el-color-success) 100%);
  color: #fff;
}

.plan-act-btn--start.plan-act-btn--start--locked.is-disabled {
  opacity: 1;
  cursor: not-allowed;
  --el-button-disabled-bg-color: var(--el-fill-color);
  --el-button-disabled-border-color: var(--el-border-color);
  --el-button-disabled-text-color: var(--el-text-color-placeholder);
  background: var(--el-fill-color);
  color: var(--el-text-color-placeholder);
  border: 1px solid var(--el-border-color-lighter);
  box-shadow: none;
}

.plan-act-btn--pause:not(.is-disabled) {
  --el-button-bg-color: var(--el-color-warning);
  --el-button-border-color: var(--el-color-warning);
  --el-button-text-color: #5c3d00;
  background: linear-gradient(180deg, #ffd06a 0%, var(--el-color-warning) 100%);
  color: #5c3d00;
}

.plan-act-btn--resume:not(.is-disabled) {
  --el-button-bg-color: var(--el-color-primary);
  --el-button-border-color: var(--el-color-primary);
  --el-button-text-color: #fff;
  background: linear-gradient(180deg, #79bbff 0%, var(--el-color-primary) 100%);
  color: #fff;
}

.plan-act-btn--end:not(.is-disabled) {
  --el-button-bg-color: var(--el-color-danger);
  --el-button-border-color: var(--el-color-danger);
  --el-button-text-color: #fff;
  background: linear-gradient(180deg, #f89898 0%, var(--el-color-danger) 100%);
  color: #fff;
}

.plan-act-btn--machine:not(.is-disabled) {
  --el-button-bg-color: #d3d1d1;
  --el-button-border-color: #d4d2d2;
  --el-button-hover-bg-color: #c9c7c7;
  --el-button-hover-border-color: #bebebe;
  --el-button-text-color: #fff;
  background: linear-gradient(180deg, #cfcfcf 0%, #c4c3c3 100%);
  color: #fff;
}

.change-machine-dialog :deep(.el-dialog) {
  max-width: 94vw;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 16px 48px rgba(15, 23, 42, 0.2);
}

.change-machine-dialog :deep(.el-dialog__header) {
  padding: 0;
  margin: 0;
  border-bottom: none;
}

.change-machine-dialog :deep(.el-dialog__headerbtn) {
  top: 10px;
  right: 10px;
  z-index: 3;
  width: 28px;
  height: 28px;
}

.change-machine-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: rgba(255, 255, 255, 0.92);
}

.change-machine-dialog :deep(.el-dialog__headerbtn:hover .el-dialog__close) {
  color: #fff;
}

.change-machine-dialog :deep(.el-dialog__body) {
  padding: 0 16px 16px;
}

.change-machine-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 14px 44px 14px 16px;
  background: linear-gradient(135deg, #ea580c 0%, #f59e0b 48%, #fbbf24 100%);
  color: #fff;
}

.change-machine-header__main {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.change-machine-header__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.22);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.35);
}

.change-machine-header__text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.change-machine-header__title {
  font-size: 1rem;
  font-weight: 700;
  line-height: 1.25;
  letter-spacing: 0.02em;
}

.change-machine-header__sub {
  font-size: 0.72rem;
  font-weight: 500;
  line-height: 1.3;
  opacity: 0.92;
}

.change-machine-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.change-machine-hero {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 10px;
  padding: 10px 12px;
  border-radius: 10px;
  background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%);
  border: 1px solid #fdba74;
}

.change-machine-hero__code {
  flex-shrink: 0;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #9a3412;
  background: rgba(255, 255, 255, 0.75);
  border: 1px solid #fed7aa;
}

.change-machine-hero__product {
  font-size: 0.88rem;
  line-height: 1.35;
  color: var(--el-text-color-primary);
  word-break: break-word;
}

.change-machine-hero__product strong {
  font-weight: 700;
}

.change-machine-hero__sep {
  margin: 0 4px;
  opacity: 0.45;
}

.change-machine-flow {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 8px;
  align-items: stretch;
}

.change-machine-flow__arrow {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #ea580c;
  opacity: 0.85;
}

.change-machine-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid var(--el-border-color-lighter);
}

.change-machine-card--current {
  background: linear-gradient(180deg, var(--el-fill-color-light) 0%, var(--el-fill-color-blank) 100%);
}

.change-machine-card--target {
  background: linear-gradient(180deg, #fffbeb 0%, var(--el-fill-color-blank) 100%);
  border-color: #fcd34d;
}

.change-machine-card__label {
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--el-text-color-secondary);
}

.change-machine-card--target .change-machine-card__label {
  color: #b45309;
}

.change-machine-card__value {
  font-size: 0.95rem;
  font-weight: 700;
  line-height: 1.3;
  color: var(--el-text-color-primary);
  word-break: break-word;
}

.change-machine-select {
  width: 100%;
}

.change-machine-select :deep(.el-select__wrapper) {
  min-height: 40px;
  background: var(--el-fill-color-blank);
  border: 1px solid var(--el-color-warning-light-5);
  box-shadow: 0 1px 2px rgba(234, 88, 12, 0.06);
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.change-machine-select :deep(.el-select__wrapper:hover) {
  border-color: var(--el-color-warning);
}

.change-machine-select :deep(.el-select__wrapper.is-focused) {
  border-color: var(--el-color-warning);
  box-shadow: 0 0 0 2px var(--el-color-warning-light-8);
}

.change-machine-select--chosen :deep(.el-select__wrapper) {
  background: linear-gradient(180deg, #fffbeb 0%, var(--el-fill-color-blank) 100%);
  border-color: var(--el-color-warning);
}

.change-machine-select--chosen :deep(.el-select__selected-item) {
  font-weight: 700;
  color: #9a3412;
}

.change-machine-select :deep(.el-select__caret) {
  color: var(--el-color-warning);
}

.change-machine-hint {
  margin: 0;
  padding: 8px 10px;
  font-size: 0.75rem;
  line-height: 1.4;
  color: #92400e;
  border-radius: 8px;
  background: #fffbeb;
  border: 1px dashed #fcd34d;
}

.change-machine-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-top: 2px;
}

.change-machine-actions__submit,
.change-machine-actions__cancel {
  min-height: 42px;
  margin: 0 !important;
  font-weight: 600;
  border-radius: 8px;
}

.change-machine-actions__submit:not(.is-disabled) {
  border: none;
  background: linear-gradient(180deg, #fbbf24 0%, #ea580c 100%);
  color: #fff;
  box-shadow: 0 2px 10px rgba(234, 88, 12, 0.28);
}

.change-machine-actions__submit:not(.is-disabled):hover {
  background: linear-gradient(180deg, #fcd34d 0%, #c2410c 100%);
}

.change-machine-actions__cancel {
  border: 1px solid var(--el-border-color);
  background: var(--el-fill-color-blank);
  color: var(--el-text-color-regular);
}

@media (max-width: 420px) {
  .change-machine-flow {
    grid-template-columns: 1fr;
  }

  .change-machine-flow__arrow {
    transform: rotate(90deg);
  }

  .change-machine-actions {
    grid-template-columns: 1fr;
  }
}

.plan-act-btn.is-disabled {
  box-shadow: none;
  opacity: 0.55;
}

.plan-row__fields {
  display: grid;
  gap: 12px;
  grid-template-columns: 1fr;
  padding-top: 4px;
  border-top: 1px dashed var(--el-border-color-lighter);
  margin-top: 2px;
}

@media (min-width: 560px) {
  .plan-row__fields:not(.plan-row__fields--stack) {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.plan-field__label {
  display: block;
  font-size: 0.78rem;
  font-weight: 600;
  margin-bottom: 6px;
  color: var(--el-text-color-regular);
}

.plan-field__control {
  width: 100%;
}

.plan-field__number {
  width: 100%;
}

.plan-field__number :deep(.el-input-number) {
  width: 100%;
}

.plan-field__number :deep(.el-input__wrapper) {
  width: 100%;
}

.production-end-dialog :deep(.el-dialog) {
  max-width: 94vw;
}

.end-dialog-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.end-dialog-product {
  margin: 0;
  font-weight: 700;
  font-size: 0.95rem;
  line-height: 1.35;
  word-break: break-word;
  color: var(--el-text-color-primary);
}

.end-dialog-warn {
  margin: 0;
}

.end-dialog-warn :deep(.el-alert__content) {
  padding: 0;
}

.end-dialog-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.end-dialog-label {
  font-weight: 600;
  font-size: 0.84rem;
  color: var(--el-text-color-regular);
}

.end-dialog-meta {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.end-dialog-meta-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  padding: 8px 10px;
  border-radius: 8px;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color-lighter);
}

.end-dialog-meta-label {
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: var(--el-text-color-secondary);
}

.end-dialog-meta-value {
  font-size: 0.92rem;
  font-weight: 700;
  color: var(--el-text-color-primary);
  word-break: break-word;
}

.end-dialog-meta-missing {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--el-color-warning-dark-2);
}

.end-dialog-input {
  width: 100%;
}

.end-dialog-input :deep(.el-input__wrapper) {
  min-height: 40px;
  padding: 0 12px;
  border-radius: 8px;
  background: var(--el-fill-color-blank);
  box-shadow:
    inset 0 1px 2px rgba(15, 23, 42, 0.04),
    0 0 0 1px var(--el-border-color-lighter);
  transition:
    box-shadow 0.2s ease,
    background 0.2s ease;
}

.end-dialog-input :deep(.el-input__wrapper:hover) {
  box-shadow:
    inset 0 1px 2px rgba(15, 23, 42, 0.04),
    0 0 0 1px var(--el-border-color);
}

.end-dialog-input :deep(.el-input__wrapper.is-focus) {
  background: #fff;
  box-shadow:
    inset 0 1px 2px rgba(15, 23, 42, 0.03),
    0 0 0 1px var(--el-color-primary-light-5),
    0 0 0 3px var(--el-color-primary-light-9);
}

.end-dialog-input :deep(.el-input__inner) {
  font-size: 1rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  text-align: left;
}

@media (max-width: 420px) {
  .end-dialog-meta {
    grid-template-columns: 1fr;
  }
}

.end-dialog-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-top: 4px;
}

.end-dialog-btn {
  min-height: 40px;
  margin: 0 !important;
  font-weight: 600;
  border-radius: 8px;
  border: none;
}

.end-dialog-btn--full:not(.is-disabled) {
  background: linear-gradient(180deg, #3ecf7a 0%, var(--el-color-success) 100%);
  color: #fff;
}

.end-dialog-btn--defer:not(.is-disabled) {
  background: linear-gradient(180deg, #ffc857 0%, var(--el-color-warning) 100%);
  color: #5c3d00;
}

.end-dialog-defer-settings {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 8px;
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
  border: 1px solid #fcd34d;
}

.end-dialog-defer-day {
  width: 100%;
}

.end-dialog-defer-day :deep(.el-input__wrapper) {
  width: 100%;
}

.end-dialog-defer-remainder {
  margin: 0;
  font-size: 0.75rem;
  line-height: 1.35;
  color: #92400e;
}

.end-dialog-defer-subsequent {
  height: auto;
  line-height: 1.35;
  white-space: normal;
}

.end-dialog-defer-subsequent :deep(.el-checkbox__label) {
  font-size: 0.78rem;
  line-height: 1.35;
  color: var(--el-text-color-regular);
}

.end-dialog-btn--cancel {
  grid-column: 1 / -1;
}

.production-end-dialog :deep(.el-dialog__header) {
  padding: 12px 14px 8px;
  margin-right: 0;
}

.production-end-dialog :deep(.el-dialog__body) {
  padding: 8px 14px 14px;
}

.production-end-dialog :deep(.el-dialog__title) {
  font-size: 1rem;
  font-weight: 700;
}

.confirmed-edit-dialog :deep(.el-dialog) {
  max-width: 94vw;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 16px 48px rgba(15, 23, 42, 0.2);
}

.confirmed-edit-dialog :deep(.el-dialog__header) {
  padding: 0;
  margin: 0;
  border-bottom: none;
}

.confirmed-edit-dialog :deep(.el-dialog__headerbtn) {
  top: 10px;
  right: 10px;
  z-index: 3;
  width: 28px;
  height: 28px;
}

.confirmed-edit-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: rgba(255, 255, 255, 0.92);
}

.confirmed-edit-dialog :deep(.el-dialog__headerbtn:hover .el-dialog__close) {
  color: #fff;
}

.confirmed-edit-dialog :deep(.el-dialog__body) {
  padding: 8px 12px 6px;
}

.confirmed-edit-dialog :deep(.el-dialog__footer) {
  padding: 6px 12px 10px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.confirmed-edit-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 9px 40px 9px 12px;
  background: linear-gradient(135deg, #4338ca 0%, #6366f1 52%, #818cf8 100%);
  color: #fff;
}

.confirmed-edit-header__main {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex: 1 1 auto;
}

.confirmed-edit-header__clear {
  flex-shrink: 0;
  margin: 0 !important;
  border: 1px solid rgba(255, 255, 255, 0.45) !important;
  background: rgba(255, 255, 255, 0.14) !important;
  color: #fff !important;
  font-weight: 600;
  border-radius: 7px;
}

.confirmed-edit-header__clear:hover:not(.is-disabled) {
  background: rgba(254, 226, 226, 0.28) !important;
  border-color: #fecaca !important;
  color: #fff !important;
}

.confirmed-edit-header__clear-icon {
  margin-right: 4px;
}

.confirmed-edit-header__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  border-radius: 9px;
  background: rgba(255, 255, 255, 0.18);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.25);
}

.confirmed-edit-header__text {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

.confirmed-edit-header__title {
  font-size: 0.95rem;
  font-weight: 700;
  line-height: 1.25;
  letter-spacing: 0.01em;
}

.confirmed-edit-header__sub {
  font-size: 0.68rem;
  font-weight: 600;
  opacity: 0.88;
  letter-spacing: 0.04em;
}

.confirmed-edit-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.confirmed-edit-hero {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 8px;
  margin: 0;
  padding: 7px 9px;
  border-radius: 8px;
  background: linear-gradient(135deg, #eef2ff 0%, #f8fafc 100%);
  border: 1px solid #c7d2fe;
}

.confirmed-edit-badge {
  flex-shrink: 0;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 0.66rem;
  font-weight: 700;
  letter-spacing: 0.03em;
  color: #fff;
  background: linear-gradient(135deg, #059669 0%, #10b981 100%);
  box-shadow: 0 1px 4px rgba(16, 185, 129, 0.35);
}

.confirmed-edit-hero__code {
  flex-shrink: 0;
  padding: 2px 7px;
  border-radius: 6px;
  font-size: 0.7rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: #4338ca;
  background: rgba(99, 102, 241, 0.12);
  border: 1px solid rgba(99, 102, 241, 0.28);
}

.confirmed-edit-hero__product {
  flex: 1 1 140px;
  min-width: 0;
  font-size: 0.82rem;
  line-height: 1.35;
  color: var(--el-text-color-primary);
  word-break: break-word;
}

.confirmed-edit-hero__product strong {
  font-weight: 700;
  color: #312e81;
}

.confirmed-edit-hero__sep {
  margin: 0 4px;
  color: var(--el-text-color-placeholder);
}

.confirmed-edit-form {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.confirmed-edit-section {
  padding: 7px 9px 4px;
  border-radius: 8px;
  border: 1px solid transparent;
}

.confirmed-edit-section--people {
  background: linear-gradient(180deg, #faf5ff 0%, #fff 100%);
  border-color: #e9d5ff;
}

.confirmed-edit-section--time {
  background: linear-gradient(180deg, #eff6ff 0%, #fff 100%);
  border-color: #bfdbfe;
}

.confirmed-edit-section__title {
  display: flex;
  align-items: center;
  gap: 5px;
  margin: 0 0 4px;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.confirmed-edit-section--people .confirmed-edit-section__title {
  color: #7c3aed;
}

.confirmed-edit-section--time .confirmed-edit-section__title {
  color: #2563eb;
}

.confirmed-edit-form :deep(.confirmed-edit-form-item) {
  margin-bottom: 6px;
}

.confirmed-edit-form :deep(.confirmed-edit-form-item .el-form-item__label) {
  padding-bottom: 2px;
  font-size: 0.74rem;
  font-weight: 600;
  line-height: 1.2;
  color: var(--el-text-color-regular);
}

.confirmed-edit-form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 8px;
}

.confirmed-edit-full {
  width: 100%;
}

.confirmed-edit-form :deep(.el-input-number) {
  width: 100%;
}

.confirmed-edit-elapsed {
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 30px;
  padding: 5px 8px;
  border-radius: 8px;
  background: linear-gradient(135deg, #dbeafe 0%, #eff6ff 100%);
  border: 1px solid #93c5fd;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.65);
}

.confirmed-edit-elapsed__value {
  font-variant-numeric: tabular-nums;
  font-size: 1.05rem;
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: 0.04em;
  color: #1d4ed8;
}

.confirmed-edit-hint {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin: 0;
  padding: 6px 8px;
  border-radius: 7px;
  font-size: 0.72rem;
  line-height: 1.4;
  color: #92400e;
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
  border: 1px solid #fcd34d;
}

.confirmed-edit-hint__icon {
  flex-shrink: 0;
  margin-top: 1px;
  color: #d97706;
}

.confirmed-edit-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.confirmed-edit-btn {
  min-width: 88px;
  margin: 0 !important;
  font-weight: 600;
  border-radius: 8px;
}

.confirmed-edit-btn--save:not(.is-disabled) {
  border: none;
  background: linear-gradient(180deg, #6366f1 0%, #4f46e5 100%);
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.35);
}

.confirmed-edit-btn--save:not(.is-disabled):hover {
  background: linear-gradient(180deg, #818cf8 0%, #6366f1 100%);
}

.confirmed-edit-btn--cancel {
  border-color: var(--el-border-color);
}

@media (max-width: 480px) {
  .confirmed-edit-form-row,
  .confirmed-edit-form-row--metrics {
    grid-template-columns: 1fr;
  }
}
</style>
