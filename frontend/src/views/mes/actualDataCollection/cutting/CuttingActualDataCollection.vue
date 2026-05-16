<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import {
  RefreshRight,
  VideoPause,
  VideoPlay,
  CircleCheck,
  DataLine,
  Calendar,
  Edit,
  Camera,
} from '@element-plus/icons-vue'
import MesBarcodeScanDialog from './MesBarcodeScanDialog.vue'
import {
  fetchCuttingManagementList,
  patchCuttingManagement,
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

const selectedMachineId = ref<number | null>(null)
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
  barcodeScanSaving.value = true
  try {
    const ok = await patchWithOfflineSync(row.id, { mes_scanned_code: trimmed })
    row.mes_scanned_code = trimmed
    const inList = managementRows.value.find((r) => r.id === row.id)
    if (inList) inList.mes_scanned_code = trimmed
    if (ok) {
      ElMessage.success(t('mesCuttingActual.scanSaved'))
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

/** 一時停止/再開時：净生産秒・停止累計秒を DB にチェックポイント保存（稼働中は計測継続） */
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
    await patchWithOfflineSync(
      planId,
      {
        mes_net_production_sec: netProductionSeconds(s),
        mes_paused_accum_sec: pausedAccumSeconds(s),
      },
      { silentQueue: true },
    )
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

async function onStart(planId: number) {
  const s = ensureSession(planId)
  if (s.wallEnd != null) return
  const now = Date.now()
  if (s.wallStart == null) {
    s.wallStart = now
    s.activeAccumMs = 0
    s.pausedAccumMs = 0
    s.pauseSliceStart = null
    s.runningSliceStart = now
    await patchWithOfflineSync(planId, {
      mes_production_started_at: new Date(s.wallStart).toISOString(),
    })
    flushPersistToStorage()
    return
  }
  if (s.runningSliceStart == null) {
    s.runningSliceStart = now
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

function canStartTimer(sess: PlanSession): boolean {
  return sess.wallEnd == null && sess.wallStart == null
}

/** 稼働計測中のみ生産終了可（一時停止中は不可） */
function canEndProduction(sess: PlanSession): boolean {
  return isTimerRunning(sess)
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
  endDialogVisible.value = true
}

function closeProductionEndDialog() {
  endDialogVisible.value = false
  endDialogRow.value = null
  endDialogPlanId.value = null
  endDialogQty.value = ''
  endDialogSubmitting.value = false
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
  endDialogSubmitting.value = true
  try {
    const mesPatch: PatchCuttingManagementBody = {
      defect_qty: computedDefectQty(row, qty),
      ...mesEndTrackingPatchBody(planId),
    }
    const preOk = await patchWithOfflineSync(row.id, mesPatch)
    if (!preOk) return
    const res = await splitCuttingManagementToNextDay(row.id, { today_quantity: qty })
    if (res && res.success === false) {
      ElMessage.error(res.message || t('mesCuttingActual.saveFailed'))
      return
    }
    ElMessage.success(res.message || t('mesCuttingActual.deferSaved'))
    closeProductionEndDialog()
    await loadPlans()
  } catch (e: unknown) {
    console.error(e)
    const msg =
      (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail ??
      (e as { message?: string })?.message
    ElMessage.error(msg ? String(msg) : t('mesCuttingActual.saveFailed'))
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
  }
}

onMounted(async () => {
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
      if (s.wallEnd == null && s.pauseSliceStart != null) {
        void persistMesTimerCheckpoints(Number(planId))
      }
    }
  }, 5000)
})

onUnmounted(() => {
  onPageHidePersist()
  window.removeEventListener('online', onBrowserOnline)
  window.removeEventListener('offline', onBrowserOffline)
  window.removeEventListener('pagehide', onPageHidePersist)
  window.removeEventListener('beforeunload', onPageHidePersist)
  document.removeEventListener('visibilitychange', onVisibilityChangePersist)
  if (tickTimer) clearInterval(tickTimer)
  if (persistTimer) clearTimeout(persistTimer)
  if (runningPersistTimer) clearInterval(runningPersistTimer)
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
          <el-date-picker
            v-model="productionDay"
            type="date"
            value-format="YYYY-MM-DD"
            :editable="false"
            teleported
            class="toolbar-control toolbar-day-picker"
          />
        </div>

        <div class="toolbar-field-row toolbar-field-row--machine">
          <span class="toolbar-field-row__label">{{ t('mesCuttingActual.machine') }}</span>
          <el-select
            v-model="selectedMachineId"
            filterable
            clearable
            :placeholder="t('mesCuttingActual.machinePlaceholder')"
            :loading="loadingMachines"
            class="toolbar-control toolbar-machine-select"
          >
            <el-option
              v-for="m in cuttingMachinesForSelect"
              :key="m.id"
              :label="(m.machine_name || '').trim() || m.machine_cd"
              :value="m.id"
            />
          </el-select>
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

          <el-card
            v-for="row in grp.rows"
            :key="row.id"
            shadow="hover"
            class="plan-row-card"
            :class="{ 'plan-row-card--confirmed': isCuttingRowConfirmedForDisplay(row) }"
          >
          <div class="plan-row">
            <div class="plan-row__product">
              <div class="plan-row__badges">
                <span class="plan-seq-pill">{{ t('mesCuttingActual.seq') }} {{ row.production_sequence ?? '—' }}</span>
                <div class="plan-row__status">
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
              </div>
              <div class="plan-row__title-line">
                <div class="plan-row__line-main">
                  <span class="plan-product-name" :title="row.product_name || ''">{{ row.product_name || '—' }}</span>
                  <span
                    v-if="productMaterialNameText(row)"
                    class="plan-product-material"
                    :title="productMaterialNameText(row)"
                  >
                    {{ productMaterialNameText(row) }}
                  </span>
                </div>
                <div class="plan-field plan-field--inline">
                  <span class="plan-field__label">{{ t('mesCuttingActual.operator') }}</span>
                  <el-select
                    v-model="ensureSession(row.id).operatorUserId"
                    filterable
                    clearable
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
              </div>
              <div class="plan-row__chips">
                <div class="plan-row__line-main">
                  <span class="plan-chip plan-chip--accent">{{ rowQtyChipLabel(row) }} {{ rowQtyChipValue(row) }}</span>
                  <span v-if="formatMgmtCodeShort(row.management_code)" class="plan-chip plan-chip--muted">
                    {{ formatMgmtCodeShort(row.management_code) }}
                  </span>
                  <span
                    v-if="row.mes_scanned_code"
                    class="plan-chip plan-chip--scan"
                    :title="row.mes_scanned_code"
                  >
                    {{
                      t('mesCuttingActual.scannedCodeShort', {
                        code: formatMgmtCodeShort(row.mes_scanned_code) || row.mes_scanned_code,
                      })
                    }}
                  </span>
                </div>
                <div class="plan-field plan-field--inline">
                  <span class="plan-field__label">{{ t('mesCuttingActual.setupTime') }}（{{ t('mesCuttingActual.setupTimeUnit') }}）</span>
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

            <div class="plan-row__timer">
              <div
                class="timer-compact"
                :class="{ 'timer-compact--pause-active': timerPhase(ensureSession(row.id)) === 'paused' }"
              >
                <div class="timer-compact__top">
                  <span class="timer-compact__label">{{ t('mesCuttingActual.elapsed') }}</span>
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
                :disabled="!canStartTimer(ensureSession(row.id))"
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
            </div>

          </div>
        </el-card>
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
            {{ t('mesCuttingActual.btnDefer') }}
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
      v-model="confirmedEditDialogVisible"
      :title="t('mesCuttingActual.confirmedEditDialogTitle')"
      width="520px"
      append-to-body
      destroy-on-close
      align-center
      class="confirmed-edit-dialog"
      @close="closeConfirmedEditDialog"
    >
      <div v-if="confirmedEditRow && confirmedEditForm" class="confirmed-edit-body">
        <p class="confirmed-edit-product">
          {{ confirmedEditRow.product_cd }} · {{ confirmedEditRow.product_name }}
        </p>
        <el-form label-position="top" class="confirmed-edit-form">
          <el-form-item :label="t('mesCuttingActual.operator')">
            <el-select
              v-model="confirmedEditForm.operatorUserId"
              filterable
              clearable
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
            <el-form-item :label="t('mesCuttingActual.actualQty')">
              <el-input-number
                v-model="confirmedEditForm.actualQty"
                :min="0"
                :step="1"
                :precision="0"
                class="confirmed-edit-full"
              />
            </el-form-item>
            <el-form-item
              :label="`${t('mesCuttingActual.setupTime')}（${t('mesCuttingActual.setupTimeUnit')}）`"
            >
              <el-input-number
                v-model="confirmedEditForm.setupTimeMin"
                :min="0"
                :step="1"
                :precision="0"
                class="confirmed-edit-full"
              />
            </el-form-item>
          </div>
          <el-form-item :label="t('mesCuttingActual.productionStart')">
            <el-date-picker
              v-model="confirmedEditForm.wallStart"
              type="datetime"
              :editable="false"
              teleported
              format="YYYY/MM/DD HH:mm"
              class="confirmed-edit-full"
            />
          </el-form-item>
          <el-form-item :label="t('mesCuttingActual.productionEnd')">
            <el-date-picker
              v-model="confirmedEditForm.wallEnd"
              type="datetime"
              :editable="false"
              teleported
              format="YYYY/MM/DD HH:mm"
              class="confirmed-edit-full"
            />
          </el-form-item>
          <div class="confirmed-edit-form-row">
            <el-form-item :label="t('mesCuttingActual.pausedAccum')">
              <el-input-number
                v-model="confirmedEditForm.pausedAccumSec"
                :min="0"
                :step="1"
                :precision="0"
                class="confirmed-edit-full"
              />
            </el-form-item>
            <el-form-item :label="t('mesCuttingActual.elapsed')">
              <div class="confirmed-edit-elapsed">{{ confirmedEditElapsedPreview }}</div>
            </el-form-item>
          </div>
          <p class="confirmed-edit-hint">{{ t('mesCuttingActual.confirmedEditPauseHint') }}</p>
        </el-form>
      </div>
      <template #footer>
        <el-button :disabled="confirmedEditSaving" @click="closeConfirmedEditDialog">
          {{ t('common.cancel') }}
        </el-button>
        <el-button type="primary" :loading="confirmedEditSaving" @click="submitConfirmedEdit">
          {{ t('mesCuttingActual.btnSaveConfirmed') }}
        </el-button>
      </template>
    </el-dialog>

    <MesBarcodeScanDialog
      v-model="barcodeScanDialogVisible"
      :product-label="barcodeScanProductLabel(barcodeScanTargetRow)"
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
  padding: 0 10px 0 0;
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

.toolbar-day-picker {
  width: 148px;
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
  width: 180px;
}

.toolbar-machine-select :deep(.el-select__wrapper),
.toolbar-machine-select :deep(.el-input__wrapper) {
  width: 100%;
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

.plan-day-group .plan-row-card {
  margin: 0 8px 8px;
  border-radius: 8px;
}

.plan-day-group .plan-row-card:first-of-type {
  margin-top: 8px;
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
  display: grid;
  gap: 10px 12px;
  align-items: start;
  grid-template-columns: 1fr;
}

@media (min-width: 900px) {
  .plan-row {
    --plan-run-block-height: 5.25rem;
    grid-template-columns: minmax(380px, 1.5fr) max-content max-content;
    column-gap: 10px;
    grid-template-areas: 'product timer actions';
    align-items: stretch;
  }

  .plan-row__product {
    grid-area: product;
  }

  .plan-row__timer {
    grid-area: timer;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    align-self: stretch;
    justify-self: start;
  }

  .plan-row__actions {
    grid-area: actions;
    justify-self: start;
    margin-left: -4px;
    align-self: end;
    height: var(--plan-run-block-height);
  }

  .timer-compact {
    min-height: var(--plan-run-block-height);
    height: var(--plan-run-block-height);
    display: flex;
    flex-direction: column;
    justify-content: center;
  }

  .plan-act-btn {
    height: 100%;
    min-height: 0;
  }
}

@media (min-width: 1200px) {
  .plan-row {
    grid-template-columns: minmax(420px, 1.6fr) max-content max-content;
    column-gap: 10px;
    grid-template-areas: 'product timer actions';
    align-items: stretch;
  }
}

.plan-row__badges {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.plan-row__status {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
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

.plan-row__title-line,
.plan-row__chips {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 6px 10px;
  margin-bottom: 4px;
}

.plan-row__chips {
  margin-bottom: 0;
}

.plan-row__line-main {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 8px;
  flex: 1 1 auto;
  min-width: 0;
}

.plan-row__title-line .plan-row__line-main {
  align-items: baseline;
  gap: 8px 12px;
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
  margin-left: auto;
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
  font-size: 1.02rem;
  font-weight: 700;
  color: var(--el-text-color-primary);
  line-height: 1.35;
}

.plan-product-material {
  flex: 0 0 auto;
  font-size: 0.92rem;
  font-weight: 500;
  color: var(--el-text-color-regular);
  line-height: 1.35;
  white-space: nowrap;
}

.plan-chip {
  font-size: 0.75rem;
  padding: 3px 8px;
  border-radius: 6px;
  background: var(--el-fill-color-light);
  color: var(--el-text-color-regular);
  line-height: 1.3;
  max-width: 100%;
  word-break: break-word;
}

.plan-chip--accent {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary-dark-2);
  font-weight: 600;
}

.plan-chip--muted {
  color: var(--el-text-color-secondary);
}

.plan-chip--scan {
  max-width: 12rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--el-color-primary-dark-2);
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary-light-7);
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
  border-radius: 8px;
  background: linear-gradient(160deg, var(--el-fill-color-blank) 0%, var(--el-fill-color-light) 100%);
  border: 1px solid var(--el-border-color-lighter);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.6);
}

.timer-compact--pause-active {
  border-color: var(--el-color-warning);
  background: linear-gradient(160deg, var(--el-color-warning-light-9) 0%, var(--el-fill-color-blank) 100%);
}

.timer-compact--pause-active .timer-compact__phase {
  color: var(--el-color-warning-dark-2);
}

.timer-compact__top {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
}

.timer-compact__label {
  font-size: 0.68rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--el-text-color-secondary);
}

.timer-compact__phase {
  font-size: 0.72rem;
  color: var(--el-color-primary);
  font-weight: 600;
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
  font-weight: 700;
  margin: 0;
  line-height: 1.1;
  flex: 1 1 auto;
  min-width: 0;
}

.timer-compact__readout--display-frozen {
  color: var(--el-text-color-secondary);
  letter-spacing: 0.02em;
}

.timer-compact__pause-side {
  flex: 0 0 auto;
  text-align: right;
  line-height: 1.15;
  max-width: 46%;
}

.timer-compact__pause-label {
  display: block;
  font-size: 0.58rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.timer-compact__pause-value {
  display: block;
  font-variant-numeric: tabular-nums;
  font-size: clamp(0.92rem, 2.4vw, 1.1rem);
  font-weight: 600;
  color: var(--el-text-color-regular);
}

.timer-compact--pause-active .timer-compact__pause-value {
  color: var(--el-color-warning-dark-2);
}

.timer-compact__walls {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  justify-content: center;
  gap: 4px 6px;
  font-size: 0.72rem;
  font-variant-numeric: tabular-nums;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.timer-compact__walls > span:not(.timer-compact__sep) {
  flex-shrink: 0;
}

.timer-compact__sep {
  opacity: 0.45;
  flex-shrink: 0;
}

.plan-row__actions {
  display: grid;
  grid-template-columns: repeat(3, minmax(6.5rem, 1fr));
  gap: 6px;
  align-items: stretch;
  width: max-content;
  max-width: 100%;
}

.plan-act-btn {
  width: 100%;
  min-height: 38px;
  margin: 0 !important;
  padding: 0 8px;
  font-size: 0.82rem;
  font-weight: 600;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.08);
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

.confirmed-edit-dialog :deep(.el-dialog__header) {
  padding: 12px 14px 8px;
  margin-right: 0;
}

.confirmed-edit-dialog :deep(.el-dialog__body) {
  padding: 8px 14px 4px;
}

.confirmed-edit-dialog :deep(.el-dialog__title) {
  font-size: 1rem;
  font-weight: 700;
}

.confirmed-edit-product {
  margin: 0 0 12px;
  font-weight: 700;
  font-size: 0.95rem;
  line-height: 1.35;
  word-break: break-word;
  color: var(--el-text-color-primary);
}

.confirmed-edit-form :deep(.el-form-item) {
  margin-bottom: 10px;
}

.confirmed-edit-form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 12px;
}

.confirmed-edit-full {
  width: 100%;
}

.confirmed-edit-elapsed {
  box-sizing: border-box;
  width: 100%;
  min-height: 32px;
  margin: 2px 0;
  padding: 6px 10px;
  border-radius: 6px;
  font-variant-numeric: tabular-nums;
  font-size: 1.15rem;
  font-weight: 700;
  line-height: 1.2;
  color: var(--el-color-primary-dark-2);
  background: var(--el-color-primary-light-9);
  border: 1px solid var(--el-color-primary-light-7);
}

.confirmed-edit-hint {
  margin: 0;
  font-size: 0.75rem;
  color: var(--el-text-color-secondary);
  line-height: 1.4;
}

@media (max-width: 480px) {
  .confirmed-edit-form-row {
    grid-template-columns: 1fr;
  }
}
</style>
