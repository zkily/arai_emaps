import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import dayjs from 'dayjs'
import { ElMessage } from 'element-plus'
import { ArrowLeft, ArrowRight, Printer } from '@element-plus/icons-vue'
import {
  fetchPlatingBoardView,
  type PlatingBoardCardOut,
  type PlatingBoardDateMemoOut,
  type PlatingDraftLayoutOut,
  type PlatingDraftOut,
} from '@/api/platingPlanning'

export type PlatingInputBoardMode = 'planning' | 'instruction'

const TZ_JP = 'Asia/Tokyo'

function todayYmdJapan(): string {
  return dayjs().tz(TZ_JP).format('YYYY-MM-DD')
}

function addDaysYmdJapan(isoYmd: string, days: number): string {
  return dayjs.tz(isoYmd, TZ_JP).add(days, 'day').format('YYYY-MM-DD')
}

function shiftYmdJapan(isoYmd: string | undefined | null, days: number): string {
  const base = (isoYmd || '').trim() || todayYmdJapan()
  return addDaysYmdJapan(base, days)
}

function dominantWorkDateFromItems(items: { work_date: string }[]): string {
  const counts = new Map<string, number>()
  for (const it of items) {
    const d = (it.work_date || '').trim()
    if (!d) continue
    counts.set(d, (counts.get(d) || 0) + 1)
  }
  if (counts.size === 0) return todayYmdJapan()
  let best = ''
  let bestC = -1
  for (const [d, c] of counts) {
    if (c > bestC || (c === bestC && d < best)) {
      best = d
      bestC = c
    }
  }
  return best || todayYmdJapan()
}

const DEFAULT_JIGS_PER_LAP = 129
const loadingDraft = ref(false)
const currentDraftId = ref<number | null>(null)
const draftWorkDate = ref(todayYmdJapan())
const syncingDraftWorkDateFromLoad = ref(false)
const boardDateMemosByYmd = ref<Record<string, string>>({})

function canPersistBoard(): boolean {
  return false
}
async function flushBoardPersist(): Promise<void> {}
function scheduleInitBoardLapSortables(): void {}

type BoardMark = 'standard' | 'manual' | 'rush'

interface ScheduleCard {
  id: string
  product_cd: string
  product_name: string
  plating_machine: string
  kake: number
  qty: number
  slots: number
  /** ボード表示用の周目（レイアウト上の周番号。読込時は persist と揃える） */
  lap_no: number
  /** API 保存時の元 lap_no（draft 内） */
  persist_lap_no?: number
  /** aps_plating_plan_board_cards.lap_work_date（表示期間フィルタの基準） */
  lap_work_date?: string
  lap_start_time?: string | null
  lap_end_time?: string | null
  /** 他 plan_date の draft から読み込んだ行 */
  source_draft_id?: number
  turn_seq: number
  colorIdx: number
  boardMark: BoardMark
  /** 数量非表示（無くなり次第）；表示は「無くなり次第」とし合計には実数を加算 */
  untilDepleted?: boolean
  /** ボード上の製品名・数量を赤字で強調表示 */
  forceRedText?: boolean
}

const scheduleCards = ref<ScheduleCard[]>([])
const standardPositions = ref(new Map<string, { lap_no: number; turn_seq: number }>())
/** API から③ボードを復元する／読込でボードを空にするとき、deep watch による不要な自動保存を抑止 */
const isBoardHydratingFromApi = ref(false)
/** 空枠補完・一括同期中は watch による自動保存・Sortable 再初期化を抑止 */
let suppressScheduleSideEffects = 0
function withSuppressedScheduleSideEffects<T>(fn: () => T): T {
  suppressScheduleSideEffects += 1
  try {
    return fn()
  } finally {
    suppressScheduleSideEffects -= 1
  }
}

/** ①ボード既定表示：本日のみ（JST） */
function defaultBoardFilterRange(): { from: string; to: string } {
  const today = todayYmdJapan()
  return { from: today, to: today }
}

const boardFilterFrom = ref(defaultBoardFilterRange().from)
const boardFilterTo = ref(defaultBoardFilterRange().to)
const boardPeriodFilterLoading = ref(false)
/** メッキ投入ボードのデータ取得中（初回・期間変更・作業日変更） */
const boardTableLoading = computed(() => loadingDraft.value || boardPeriodFilterLoading.value)

const boardViewRange = computed(() => {
  let from = (boardFilterFrom.value || '').trim().slice(0, 10)
  let to = (boardFilterTo.value || '').trim().slice(0, 10)
  if (!from || !to) return defaultBoardFilterRange()
  if (from > to) {
    const t = from
    from = to
    to = t
  }
  return { from, to }
})

const boardFilterDateRange = computed({
  get(): [string, string] {
    const { from, to } = boardViewRange.value
    return [from, to]
  },
  set(v: [string, string] | null | undefined) {
    if (!v || v.length < 2) return
    boardFilterFrom.value = String(v[0] || '').slice(0, 10)
    boardFilterTo.value = String(v[1] || '').slice(0, 10)
  },
})

const boardViewRangeLabel = computed(() => {
  const { from, to } = boardViewRange.value
  return `${formatBoardDateLabel(from)}〜${formatBoardDateLabel(to)}`
})

let boardViewRangeReloadTimer: ReturnType<typeof setTimeout> | null = null
let boardViewRangeReady = false
/** setBoardViewRangeToday 等で即時再取得する際、watch による二重読込を抑止 */
let skipBoardViewRangeWatchOnce = false

function cancelBoardViewRangeReload() {
  if (boardViewRangeReloadTimer != null) {
    clearTimeout(boardViewRangeReloadTimer)
    boardViewRangeReloadTimer = null
  }
}

/** 表示期間変更時にボードデータを自動再取得（反映ボタン不要） */
async function reloadBoardForViewRange() {
  const { from, to } = boardViewRange.value
  boardFilterFrom.value = from
  boardFilterTo.value = to
  boardPeriodFilterLoading.value = true
  try {
    await loadLatestDraft({ autoMode: true, autoSyncWorkDate: false })
  } finally {
    boardPeriodFilterLoading.value = false
  }
}

function scheduleBoardViewRangeReload() {
  if (!boardViewRangeReady) return
  cancelBoardViewRangeReload()
  boardViewRangeReloadTimer = setTimeout(() => {
    boardViewRangeReloadTimer = null
    void reloadBoardForViewRange()
  }, 280)
}

function shiftBoardViewRange(days: number) {
  const { from, to } = boardViewRange.value
  boardFilterFrom.value = shiftYmdJapan(from, days)
  boardFilterTo.value = shiftYmdJapan(to, days)
}

/** 表示期間の開始・終了をともに本日（JST）にし、データを自動再取得 */
async function setBoardViewRangeToday() {
  cancelBoardViewRangeReload()
  const today = todayYmdJapan()
  skipBoardViewRangeWatchOnce = true
  boardFilterFrom.value = today
  boardFilterTo.value = today
  if (draftWorkDate.value !== today) {
    syncingDraftWorkDateFromLoad.value = true
    draftWorkDate.value = today
    await nextTick()
    syncingDraftWorkDateFromLoad.value = false
  }
  if (!boardViewRangeReady) return
  await reloadBoardForViewRange()
}

function onBoardViewRangeChange(v: [string, string] | null | undefined) {
  if (!v || v.length < 2 || !v[0] || !v[1]) return
  boardFilterFrom.value = String(v[0]).slice(0, 10)
  boardFilterTo.value = String(v[1]).slice(0, 10)
}

function enumerateYmdRange(from: string, to: string): string[] {
  const out: string[] = []
  let d = from
  while (d <= to) {
    out.push(d)
    if (d === to) break
    d = addDaysYmdJapan(d, 1)
  }
  return out
}

function isYmdInBoardView(ymd: string | null | undefined): boolean {
  const d = (ymd || '').trim().slice(0, 10)
  if (!d) return false
  const { from, to } = boardViewRange.value
  return d >= from && d <= to
}

function boardCardLapWorkDate(bc: { lap_work_date?: string | null }): string {
  return String(bc.lap_work_date ?? '').slice(0, 10)
}

/** 表示期間内の board_cards から周目番号集合を構築（lap_work_date のみ基準） */
function boardLapNosInViewFromCards(
  boardCards: Array<{ lap_no: number; persist_lap_no?: number; lap_work_date?: string | null }>,
): Set<number> {
  const set = new Set<number>()
  for (const bc of boardCards) {
    const wd = boardCardLapWorkDate(bc)
    if (!wd || !isYmdInBoardView(wd)) continue
    const persist = Math.max(1, Math.floor(Number(bc.persist_lap_no ?? bc.lap_no) || 0))
    set.add(persist)
  }
  return set
}

function boardLapNosInViewFromScheduleCards(): Set<number> {
  const set = new Set<number>()
  for (const c of scheduleCards.value) {
    const wd = (c.lap_work_date || '').slice(0, 10)
    if (!wd || !isYmdInBoardView(wd)) continue
    set.add(c.lap_no)
    if (c.persist_lap_no) set.add(c.persist_lap_no)
  }
  return set
}

/** 表示期間内に board_cards（qty>0）が存在する周目のみ */
function boardLapNosWithBoardDataInView(): Set<number> {
  const set = new Set<number>()
  for (const c of scheduleCards.value) {
    if (c.qty <= 0) continue
    const wd = (c.lap_work_date || '').slice(0, 10)
    if (!wd || !isYmdInBoardView(wd)) continue
    set.add(c.lap_no)
  }
  return set
}

/** layout_blocks から表示期間内の周目番号を構築（カード未配置でもレイアウト行を表示） */
function boardLapNosFromLayoutBlocksInView(): Set<number> {
  const set = new Set<number>()
  for (const block of layoutBlocks.value) {
    const rows = buildLapScheduleRows(
      block.plan_date,
      block.start_time,
      block.minutes_per_lap,
      block.lap_count,
    )
    for (let i = 0; i < rows.length; i += 1) {
      const row = rows[i]!
      if (!isYmdInBoardView(row.work_date)) continue
      set.add(block.base_lap_no + i)
    }
  }
  return set
}

const jigsPerLap = ref(DEFAULT_JIGS_PER_LAP)
const minutesPerLap = ref(100)

/** ①ボード：追加レイアウトで積み上げる周目ブロック */
interface BoardLayoutBlock {
  plan_date: string
  start_time: string
  minutes_per_lap: number
  jigs_per_lap: number
  lap_count: number
  base_lap_no: number
}

const templateDialogVisible = ref(false)
const tplFormPlanDate = ref(todayYmdJapan())
const tplFormStartTime = ref('08:00')
const tplFormMinutesPerLap = ref(100)
const tplFormJigsPerLap = ref(DEFAULT_JIGS_PER_LAP)
const tplFormMaxLaps = ref(1)
const layoutBoardReady = ref(false)
const layoutBlocks = ref<BoardLayoutBlock[]>([])
const layoutPlanDate = ref(todayYmdJapan())
const layoutStartTime = ref('08:00')
const layoutMinutesPerLap = ref(100)
const layoutJigsPerLap = ref(DEFAULT_JIGS_PER_LAP)
const layoutMaxLaps = ref(1)

const DEFAULT_BOARD_START_TIME = '08:00'

function normalizeBoardStartTimeHm(v: string | null | undefined): string {
  const s = String(v ?? '').trim()
  const m = s.match(/^(\d{1,2}):(\d{2})$/)
  if (!m) return DEFAULT_BOARD_START_TIME
  const h = Math.min(23, Math.max(0, Number(m[1])))
  const min = Math.min(59, Math.max(0, Number(m[2])))
  return `${String(h).padStart(2, '0')}:${String(min).padStart(2, '0')}`
}

interface LapScheduleSlot {
  lap_no: number
  work_date: string
  work_date_label: string
  start: string
  end: string
}

function formatBoardDateLabel(ymd: string): string {
  const d = dayjs.tz(ymd, 'YYYY-MM-DD', TZ_JP)
  if (!d.isValid()) return ymd
  return d.format('M/D（ddd）')
}

function buildLapScheduleRows(
  planDate: string,
  startTime: string,
  minutesPerSegment: number,
  lapCount: number,
): LapScheduleSlot[] {
  const d = (planDate || '').trim()
  const t = normalizeBoardStartTimeHm(startTime)
  const cycle = Math.max(1, Math.floor(Number(minutesPerSegment) || 1))
  const laps = Math.max(1, Math.floor(Number(lapCount) || 1))
  if (!d) return []
  const base = dayjs.tz(`${d} ${t}`, 'YYYY-MM-DD HH:mm', TZ_JP)
  if (!base.isValid()) return []
  return Array.from({ length: laps }, (_, i) => {
    const lapNo = i + 1
    const startDt = base.add((lapNo - 1) * cycle, 'minute')
    const endDt = startDt.add(cycle, 'minute')
    const workDate = startDt.format('YYYY-MM-DD')
    return {
      lap_no: lapNo,
      work_date: workDate,
      work_date_label: formatBoardDateLabel(workDate),
      start: startDt.format('HH:mm'),
      end: endDt.format('HH:mm'),
    }
  })
}

function buildGlobalLapScheduleInner(): LapScheduleSlot[] {
  if (!layoutBoardReady.value) return []

  const lapNosWithData = boardLapNosWithBoardDataInView()
  const targetLapNos = new Set<number>([
    ...boardLapNosFromLayoutBlocksInView(),
    ...lapNosWithData,
    ...boardLapNosInViewFromScheduleCards(),
  ])
  if (targetLapNos.size === 0) return []

  const lapDateMap = buildBoardLapWorkDateMap()
  const lapTimesMap = buildBoardLapTimesMap()
  const layoutSlotByLap = new Map<number, LapScheduleSlot>()
  for (const block of layoutBlocksInBoardView()) {
    const rows = buildLapScheduleRows(
      block.plan_date,
      block.start_time,
      block.minutes_per_lap,
      block.lap_count,
    )
    for (const r of rows) {
      const lapNo = block.base_lap_no + r.lap_no - 1
      if (!targetLapNos.has(lapNo)) continue
      layoutSlotByLap.set(lapNo, { ...r, lap_no: lapNo })
    }
  }

  const sortMap = new Map<number, LapScheduleSlot>()
  for (const ln of targetLapNos) {
    const layout = layoutSlotByLap.get(ln)
    const wd = (lapDateMap.get(ln) || layout?.work_date || '').slice(0, 10)
    if (!wd || !isYmdInBoardView(wd)) continue
    const times = lapTimesMap.get(ln)
    const start =
      times?.start ||
      layout?.start ||
      normalizeBoardStartTimeHm(scheduleCards.value.find((c) => c.lap_no === ln)?.lap_start_time)
    const end =
      times?.end ||
      layout?.end ||
      normalizeBoardStartTimeHm(scheduleCards.value.find((c) => c.lap_no === ln)?.lap_end_time)
    sortMap.set(ln, {
      lap_no: ln,
      work_date: wd,
      work_date_label: formatBoardDateLabel(wd),
      start: start || '08:00',
      end: end || start || '09:00',
    })
  }
  const result: LapScheduleSlot[] = []
  for (const ln of [...sortMap.keys()].sort((a, b) => compareLapNoForBoardSort(a, b, sortMap))) {
    const slot = sortMap.get(ln)
    if (slot) result.push(slot)
  }
  return result
}

/** 周次スケジュール（layout + board_cards）— 同一 tick 内の重複計算を抑止 */
const globalLapSchedule = computed(() => buildGlobalLapScheduleInner())

function currentLayoutLapSchedule(): LapScheduleSlot[] {
  return globalLapSchedule.value
}

/** 計画日（lap_work_date）ごとに 1 から振り直した表示用周番号 */
const lapDisplayNoMap = computed(() => {
  const map = new Map<number, number>()
  const schedule = globalLapSchedule.value
  const scheduleByLap = new Map(schedule.map((s) => [s.lap_no, s]))
  const byDate = new Map<string, number[]>()
  for (const s of schedule) {
    const list = byDate.get(s.work_date) ?? []
    list.push(s.lap_no)
    byDate.set(s.work_date, list)
  }
  for (const laps of byDate.values()) {
    const sorted = [...laps].sort((a, b) => compareLapNoForBoardSort(a, b, scheduleByLap))
    sorted.forEach((lapNo, idx) => map.set(lapNo, idx + 1))
  }
  return map
})

function lapDisplayNo(lapNo: number): number {
  return lapDisplayNoMap.value.get(lapNo) ?? lapNo
}

type BoardCardWithDisplayLap = PlatingBoardCardOut & { persist_lap_no: number }

function layoutBlockCoversAnyLap(block: { base_lap_no: number; lap_count: number }, lapNos: Set<number>): boolean {
  const start = Math.max(1, Math.floor(Number(block.base_lap_no) || 1))
  const end = start + Math.max(1, Math.floor(Number(block.lap_count) || 1)) - 1
  for (let ln = start; ln <= end; ln += 1) {
    if (lapNos.has(ln)) return true
  }
  return false
}

function buildBoardLapWorkDateMap(): Map<number, string> {
  const map = new Map<number, string>()
  for (const c of scheduleCards.value) {
    const wd = (c.lap_work_date || '').slice(0, 10)
    if (!wd || !isYmdInBoardView(wd)) continue
    map.set(c.lap_no, wd)
  }
  return map
}

/** board_cards の lap_start_time / lap_end_time（周目ラベル表示用） */
function buildBoardLapTimesMap(): Map<number, { start: string; end: string }> {
  const map = new Map<number, { start: string; end: string }>()
  for (const c of scheduleCards.value) {
    if (map.has(c.lap_no)) continue
    const st = String(c.lap_start_time ?? '').trim()
    const en = String(c.lap_end_time ?? '').trim()
    if (!st && !en) continue
    map.set(c.lap_no, {
      start: st ? normalizeBoardStartTimeHm(st) : '',
      end: en ? normalizeBoardStartTimeHm(en) : '',
    })
  }
  return map
}

function lapScheduleMetaForCard(lapNo: number): {
  lap_work_date?: string
  lap_start_time?: string | null
  lap_end_time?: string | null
} {
  const times = buildBoardLapTimesMap().get(lapNo)
  const slot = currentLayoutLapSchedule().find((s) => s.lap_no === lapNo)
  const card = scheduleCards.value.find((c) => c.lap_no === lapNo)
  const wd = (card?.lap_work_date || slot?.work_date || '').slice(0, 10)
  return {
    lap_work_date: wd || undefined,
    lap_start_time: times?.start || slot?.start || card?.lap_start_time || null,
    lap_end_time: times?.end || slot?.end || card?.lap_end_time || null,
  }
}

function isLapNoInBoardView(lapNo: number, scheduleByLap?: Map<number, LapScheduleSlot>): boolean {
  const fromCard = scheduleCards.value.find((c) => c.lap_no === lapNo)?.lap_work_date
  const wd = (fromCard || scheduleByLap?.get(lapNo)?.work_date || '').slice(0, 10)
  if (!wd) {
    if (layoutBoardReady.value) return false
    return true
  }
  return isYmdInBoardView(wd)
}

function layoutBlocksInBoardView(): BoardLayoutBlock[] {
  const lapNos = new Set<number>([
    ...boardLapNosInViewFromScheduleCards(),
    ...boardLapNosFromLayoutBlocksInView(),
  ])
  if (lapNos.size === 0) return []
  return layoutBlocks.value.filter((b) => layoutBlockCoversAnyLap(b, lapNos))
}

function recomputeLayoutMaxLapsFromSchedule() {
  const sched = globalLapSchedule.value
  if (sched.length > 0) {
    layoutMaxLaps.value = Math.max(...sched.map((s) => s.lap_no))
  }
}

function applyLayoutHeaderFromFirstBlock() {
  const first = [...layoutBlocks.value].sort((a, b) => a.base_lap_no - b.base_lap_no)[0]
  if (!first) return
  layoutPlanDate.value = first.plan_date
  layoutStartTime.value = normalizeBoardStartTimeHm(first.start_time)
  layoutMinutesPerLap.value = first.minutes_per_lap
  layoutJigsPerLap.value = first.jigs_per_lap
}

function inferLayoutBlocksFromBoard(
  rawBoard: Array<{
    lap_no: number
    persist_lap_no?: number
    lap_work_date?: string | null
    lap_start_time?: string | null
    lap_end_time?: string | null
  }>,
  header: {
    plan_date: string
    board_start_time: string
    minutes_per_lap: number
    jigs_per_lap: number
    max_laps: number
  },
): BoardLayoutBlock[] {
  const lapMeta = new Map<number, { wd: string; start: string }>()
  for (const bc of rawBoard) {
    const ln = Math.max(1, Math.floor(Number(bc.persist_lap_no ?? bc.lap_no) || 0))
    if (lapMeta.has(ln)) continue
    const wd = String(bc.lap_work_date || '').slice(0, 10)
    if (!wd || !isYmdInBoardView(wd)) continue
    const start = normalizeBoardStartTimeHm(bc.lap_start_time || header.board_start_time)
    lapMeta.set(ln, { wd, start })
  }
  const lapNos = [...lapMeta.keys()].sort((a, b) => a - b)
  if (lapNos.length === 0) return []

  const blocks: BoardLayoutBlock[] = []
  let idx = 0
  while (idx < lapNos.length) {
    const startLap = lapNos[idx]!
    const meta = lapMeta.get(startLap)!
    let j = idx
    while (j + 1 < lapNos.length) {
      const cur = lapNos[j]!
      const nextLap = lapNos[j + 1]!
      const nextMeta = lapMeta.get(nextLap)!
      if (nextLap !== cur + 1 || nextMeta.wd !== meta.wd) break
      j += 1
    }
    const endLap = lapNos[j]!
    blocks.push({
      plan_date: meta.wd,
      start_time: normalizeBoardStartTimeHm(meta.start),
      minutes_per_lap: header.minutes_per_lap,
      jigs_per_lap: header.jigs_per_lap,
      lap_count: endLap - startLap + 1,
      base_lap_no: startLap,
    })
    idx = j + 1
  }
  return blocks
}

function lapTimeRangeLabel(lapNo: number): string {
  const times = buildBoardLapTimesMap().get(lapNo)
  if (times?.start && times?.end) return `${times.start}–${times.end}`
  if (times?.start) return `${times.start}–`
  if (times?.end) return `–${times.end}`
  const row = currentLayoutLapSchedule().find((r) => r.lap_no === lapNo)
  return row?.start && row?.end ? `${row.start}–${row.end}` : ''
}

function syncScheduleCardLapTimesFromLayout() {
  const byLap = new Map(globalLapSchedule.value.map((s) => [s.lap_no, s]))
  withSuppressedScheduleSideEffects(() => {
    scheduleCards.value = scheduleCards.value.map((c) => {
      const s = byLap.get(c.lap_no)
      if (!s) return c
      return {
        ...c,
        lap_work_date: s.work_date,
        lap_start_time: s.start,
        lap_end_time: s.end,
      }
    })
  })
}

function num(v: unknown): number {
  if (v === null || v === undefined || v === '') return 0
  const n = Number(v)
  return Number.isFinite(n) ? n : 0
}

function getBoardDateMemo(ymd: string): string {
  return String(boardDateMemosByYmd.value[ymd] ?? '').trim()
}

function applyBoardDateMemosFromDraft(memos: PlatingBoardDateMemoOut[], merge = false) {
  const next = merge ? { ...boardDateMemosByYmd.value } : {}
  for (const row of memos) {
    const d = String(row.lap_work_date ?? '').slice(0, 10)
    if (!d) continue
    next[d] = String(row.memo ?? '')
  }
  boardDateMemosByYmd.value = next
}

function lapScheduleStartHmForSort(lapNo: number, scheduleByLap: Map<number, LapScheduleSlot>): string {
  const slot = scheduleByLap.get(lapNo)
  const card = scheduleCards.value.find((c) => c.lap_no === lapNo)
  return normalizeBoardStartTimeHm(card?.lap_start_time || slot?.start || '99:99')
}

/** ボード表示：作業日 → 開始時刻 → 周目番号 */
function compareLapNoForBoardSort(
  lapA: number,
  lapB: number,
  scheduleByLap: Map<number, LapScheduleSlot>,
): number {
  const cardWd = (lapNo: number) =>
    scheduleCards.value.find((c) => c.lap_no === lapNo)?.lap_work_date?.slice(0, 10) ?? ''
  const da = cardWd(lapA) || (scheduleByLap.get(lapA)?.work_date ?? '')
  const db = cardWd(lapB) || (scheduleByLap.get(lapB)?.work_date ?? '')
  if (da !== db) return da.localeCompare(db)
  const ta = lapScheduleStartHmForSort(lapA, scheduleByLap)
  const tb = lapScheduleStartHmForSort(lapB, scheduleByLap)
  if (ta !== tb) return ta.localeCompare(tb)
  return lapA - lapB
}

/** 読込時：保存 lap_no をボード行に復元（空き周目を飛ばしても 1→5 のまま）。同一作業日で他 draft と番号が衝突する場合のみずらす */
function assignDisplayLapNumbers(boards: PlatingBoardCardOut[]): BoardCardWithDisplayLap[] {
  const sorted = [...boards].sort((a, b) => {
    const da = boardCardLapWorkDate(a)
    const db = boardCardLapWorkDate(b)
    if (da !== db) return da.localeCompare(db)
    if (a.lap_no !== b.lap_no) return a.lap_no - b.lap_no
    if (a.turn_seq !== b.turn_seq) return a.turn_seq - b.turn_seq
    return (a.id ?? 0) - (b.id ?? 0)
  })
  const lapKeyToNo = new Map<string, number>()
  const usedLapOnDate = new Map<string, Set<number>>()
  return sorted.map((bc) => {
    const persist_lap_no = Math.max(1, Math.floor(Number(bc.lap_no) || 0))
    const wd = boardCardLapWorkDate(bc)
    const key = `${bc.draft_id}-${wd}-${persist_lap_no}`
    if (!lapKeyToNo.has(key)) {
      const taken = usedLapOnDate.get(wd) ?? new Set<number>()
      let lapNo = persist_lap_no
      while (taken.has(lapNo)) lapNo += 1
      taken.add(lapNo)
      usedLapOnDate.set(wd, taken)
      lapKeyToNo.set(key, lapNo)
    }
    return { ...bc, persist_lap_no, lap_no: lapKeyToNo.get(key)! }
  })
}


/** 表示期間内のボード行＋レイアウトブロックを集約（board_cards は lap_work_date で SQL 期間フィルタ） */
async function loadBoardAcrossViewRange(): Promise<{
  boardCards: BoardCardWithDisplayLap[]
  primary: PlatingDraftOut | null
  layoutBlocks: PlatingDraftLayoutOut[]
  boardDateMemos: PlatingBoardDateMemoOut[]
}> {
  const { from, to } = boardViewRange.value
  const preferredDraftId = currentDraftId.value ? Number(currentDraftId.value) : undefined
  const view = await fetchPlatingBoardView({
    boardFrom: from,
    boardTo: to,
    preferredDraftId: preferredDraftId && preferredDraftId > 0 ? preferredDraftId : undefined,
  })
  return {
    boardCards: assignDisplayLapNumbers(view.board_cards || []),
    primary: view.primary ?? null,
    layoutBlocks: view.layout_blocks || [],
    boardDateMemos: view.board_date_memos || [],
  }
}

/** 集約 layout_blocks：表示期間は board_cards.lap_work_date、または layout の計画日で判定 */
function layoutBlockHasLapsInBoardView(block: {
  plan_date?: string | null
  start_time?: string | null
  minutes_per_lap?: number | null
  lap_count?: number | null
}): boolean {
  const pd = String(block.plan_date || '').slice(0, 10)
  if (!pd) return false
  const rows = buildLapScheduleRows(
    pd,
    block.start_time ?? '',
    Math.max(1, Math.floor(Number(block.minutes_per_lap) || 1)),
    Math.max(1, Math.floor(Number(block.lap_count) || 1)),
  )
  return rows.some((r) => isYmdInBoardView(r.work_date))
}

function normalizeLayoutBlocksForView(
  blocks: PlatingDraftLayoutOut[],
  boardCards: BoardCardWithDisplayLap[] = [],
): BoardLayoutBlock[] {
  if (blocks.length === 0) return []
  const lapNosInView = boardCards.length > 0 ? boardLapNosInViewFromCards(boardCards) : new Set<number>()
  const dedup = new Map<string, PlatingDraftLayoutOut>()
  for (const b of blocks) {
    const baseLap = Math.max(1, Math.floor(Number(b.base_lap_no) || 1))
    const lapCount = Math.max(1, Math.floor(Number(b.lap_count) || 1))
    const coveredByCards =
      lapNosInView.size > 0 &&
      layoutBlockCoversAnyLap({ base_lap_no: baseLap, lap_count: lapCount }, lapNosInView)
    const coveredByDate = layoutBlockHasLapsInBoardView(b)
    if (!coveredByCards && !coveredByDate) continue
    const pd = String(b.plan_date || '').slice(0, 10)
    if (!pd) continue
    const start = normalizeBoardStartTimeHm(b.start_time)
    const key = `${pd}|${start}|${b.minutes_per_lap}|${b.jigs_per_lap}|${b.lap_count}|${b.base_lap_no}`
    if (!dedup.has(key)) dedup.set(key, b)
  }
  const sorted = [...dedup.values()].sort((a, b) => {
    const pa = String(a.plan_date || '').slice(0, 10)
    const pb = String(b.plan_date || '').slice(0, 10)
    if (pa !== pb) return pa.localeCompare(pb)
    const sa = normalizeBoardStartTimeHm(a.start_time)
    const sb = normalizeBoardStartTimeHm(b.start_time)
    if (sa !== sb) return sa.localeCompare(sb)
    return (a.base_lap_no || 0) - (b.base_lap_no || 0)
  })
  return sorted.map((b) => {
    const lapCount = Math.max(1, Math.floor(Number(b.lap_count) || 1))
    const block: BoardLayoutBlock = {
      plan_date: String(b.plan_date || '').slice(0, 10),
      start_time: normalizeBoardStartTimeHm(b.start_time),
      minutes_per_lap: Math.max(1, Math.floor(Number(b.minutes_per_lap) || 1)),
      jigs_per_lap: Math.max(1, Math.floor(Number(b.jigs_per_lap) || 1)),
      lap_count: lapCount,
      base_lap_no: Math.max(1, Math.floor(Number(b.base_lap_no) || 1)),
    }
    return block
  })
}

type LoadLatestDraftOpts = { autoMode?: boolean; autoSyncWorkDate?: boolean }

async function loadLatestDraft(opts?: boolean | LoadLatestDraftOpts) {
  let autoMode = false
  let autoSyncWorkDate = false
  if (typeof opts === 'boolean') {
    autoMode = opts
    autoSyncWorkDate = opts
  } else if (opts) {
    autoMode = opts.autoMode ?? false
    autoSyncWorkDate = opts.autoSyncWorkDate ?? false
  }
  const planDateForDraft = draftWorkDate.value || todayYmdJapan()
  loadingDraft.value = true
  try {
    const {
      boardCards: mergedBoard,
      primary,
      layoutBlocks: mergedLayoutBlocks,
      boardDateMemos: mergedBoardDateMemos,
    } = await loadBoardAcrossViewRange()
    if (!primary) {
      currentDraftId.value = null
      scheduleCards.value = []
      standardPositions.value = new Map()
      layoutBoardReady.value = false
      layoutBlocks.value = []
      boardDateMemosByYmd.value = {}
      if (!autoMode) ElMessage.warning('表示期間内の計画データはありません')
      return
    }

    const display = primary
    applyBoardDateMemosFromDraft(
      mergedBoardDateMemos.length > 0 ? mergedBoardDateMemos : display.board_date_memos || [],
      true,
    )
    const planKey = String(display.plan_date || planDateForDraft).slice(0, 10)
    const boardDates = mergedBoard
      .map((bc) => ({ work_date: boardCardLapWorkDate(bc) }))
      .filter((it) => Boolean(it.work_date))

    let wd = draftWorkDate.value || planDateForDraft
    if (autoSyncWorkDate && boardDates.length > 0) {
      const hasMatch = boardDates.some((it) => it.work_date === wd)
      if (!hasMatch) {
        wd = dominantWorkDateFromItems(boardDates)
      }
    }
    if (wd !== draftWorkDate.value) {
      syncingDraftWorkDateFromLoad.value = true
      draftWorkDate.value = wd
      await nextTick()
      syncingDraftWorkDateFromLoad.value = false
    }

    currentDraftId.value = display.id

    if (mergedBoard.length > 0) {
      const wdCounts = new Map<string, number>()
      for (const bc of mergedBoard) {
        const wd = boardCardLapWorkDate(bc)
        if (!isYmdInBoardView(wd)) continue
        wdCounts.set(wd, (wdCounts.get(wd) ?? 0) + 1)
      }
      const dominantWd = [...wdCounts.entries()].sort((a, b) => b[1] - a[1])[0]?.[0]
      if (dominantWd) layoutPlanDate.value = dominantWd
    }

    isBoardHydratingFromApi.value = true
    let boardStaleSlotsPruned = false
    try {
      const jp = Math.max(1, Math.floor(Number(display.jigs_per_lap) || 0))
      const mp = Math.max(1, Math.floor(Number(display.minutes_per_lap) || 100))
      if (jp > 0) jigsPerLap.value = jp
      minutesPerLap.value = mp
      layoutMinutesPerLap.value = mp
      const rawBoard = mergedBoard
      const persistedBlocks = normalizeLayoutBlocksForView(mergedLayoutBlocks || [], rawBoard)
      let nextBlocks: BoardLayoutBlock[] = persistedBlocks
      if (nextBlocks.length === 0 && rawBoard.length > 0) {
        const legacyPlan = boardCardLapWorkDate(rawBoard[0]!) || todayYmdJapan()
        nextBlocks = inferLayoutBlocksFromBoard(rawBoard, {
          plan_date: legacyPlan,
          board_start_time: normalizeBoardStartTimeHm(display.board_start_time),
          minutes_per_lap: mp,
          jigs_per_lap: jp > 0 ? jp : layoutJigsPerLap.value,
          max_laps: Math.max(1, Math.floor(Number(display.max_laps) || 0)),
        })
      }
      layoutBlocks.value = nextBlocks
      layoutBoardReady.value = layoutBlocks.value.length > 0
      if (layoutBoardReady.value) {
        layoutJigsPerLap.value = layoutBlocks.value[0]!.jigs_per_lap
        applyLayoutHeaderFromFirstBlock()
        recomputeLayoutMaxLapsFromSchedule()
        const maxFromCards = rawBoard.length > 0 ? Math.max(...rawBoard.map((b) => b.lap_no)) : 0
        if (maxFromCards > layoutMaxLaps.value) layoutMaxLaps.value = maxFromCards
      } else {
        layoutBlocks.value = []
      }
      const hasLayout = layoutBoardReady.value
      if (rawBoard.length > 0) {
        const scheduleByLap = new Map(currentLayoutLapSchedule().map((s) => [s.lap_no, s]))
        scheduleCards.value = rawBoard
          .slice()
          .sort(
            (a, b) =>
              compareLapNoForBoardSort(a.lap_no, b.lap_no, scheduleByLap) ||
              a.turn_seq - b.turn_seq ||
              (a.id ?? 0) - (b.id ?? 0),
          )
          .map((bc, idx) => {
            const mk: BoardMark =
              bc.board_mark === 'rush' || bc.board_mark === 'manual' ? bc.board_mark : 'standard'
            const id = (bc.stable_key || '').trim() || `db-${bc.draft_id}-${bc.id}-${idx}`
            return {
              id,
              product_cd: bc.product_cd,
              product_name: bc.product_name,
              plating_machine: bc.plating_machine,
              kake: Number(bc.kake) || 0,
              qty: Number(bc.qty) || 0,
              slots: Number(bc.slots) || 0,
              lap_no: Number(bc.lap_no) || 0,
              persist_lap_no: Number(bc.persist_lap_no) || Number(bc.lap_no) || 0,
              lap_work_date: boardCardLapWorkDate(bc),
              lap_start_time: bc.lap_start_time ?? null,
              lap_end_time: bc.lap_end_time ?? null,
              source_draft_id: bc.draft_id,
              turn_seq: bc.turn_seq,
              colorIdx: idx,
              boardMark: mk,
              untilDepleted: !!bc.until_depleted,
              forceRedText: !!bc.text_red,
            }
          })
        standardPositions.value = new Map(
          scheduleCards.value
            .filter((c) => c.boardMark === 'standard')
            .map((c) => [c.id, { lap_no: c.lap_no, turn_seq: c.turn_seq }]),
        )
        withSuppressedScheduleSideEffects(() => {
          boardStaleSlotsPruned = pruneStaleEmptySlots()
          ensureBoardCardSkeletonsForLayout()
          syncScheduleCardLapTimesFromLayout()
        })
      } else if (!hasLayout) {
        scheduleCards.value = []
        standardPositions.value = new Map()
        layoutBoardReady.value = false
      } else {
        scheduleCards.value = []
        standardPositions.value = new Map()
        withSuppressedScheduleSideEffects(() => {
          ensureBoardCardSkeletonsForLayout()
          syncScheduleCardLapTimesFromLayout()
        })
      }
    } finally {
      void nextTick(() => {
        setTimeout(() => {
          isBoardHydratingFromApi.value = false
          scheduleInitBoardLapSortables()
          if (boardStaleSlotsPruned && canPersistBoard()) {
            void flushBoardPersist()
          }
        }, 0)
      })
    }

    if (!autoMode) ElMessage.success(`計画（ID ${display.id}）を読み込みました`)
  } catch (e) {
    console.error(e)
    if (!autoMode) ElMessage.error('計画の読み込みに失敗しました')
  } finally {
    loadingDraft.value = false
  }
}

function isJigProductCd(productCd: string): boolean {
  return String(productCd || '').startsWith('__jig__')
}

/** レイアウト空枠（board_cards に qty=0 で永続化） */
function isEmptySlotProductCd(productCd: string): boolean {
  return String(productCd || '').startsWith('__slot__')
}

function shouldPersistBoardCard(c: ScheduleCard): boolean {
  return c.qty > 0 || isEmptySlotProductCd(c.product_cd)
}

function createEmptySlotScheduleCard(lapNo: number, turnSeq: number, slot?: LapScheduleSlot): ScheduleCard {
  const persistLap = lapNo
  return {
    id: `slot-${persistLap}-${turnSeq}-${Date.now()}-${Math.random().toString(36).slice(2, 5)}`,
    product_cd: `__slot__${persistLap}-${turnSeq}`,
    product_name: '空き',
    plating_machine: '—',
    kake: 1,
    qty: 0,
    slots: 0,
    lap_no: lapNo,
    persist_lap_no: persistLap,
    lap_work_date: slot?.work_date,
    lap_start_time: slot?.start ?? null,
    lap_end_time: slot?.end ?? null,
    turn_seq: turnSeq,
    colorIdx: 0,
    boardMark: 'standard',
  }
}

/** レイアウト上の各周×列に board_cards 用の空枠行を揃える（追加レイアウト直後・保存前） */
function pruneStaleEmptySlots(): boolean {
  const occupied = new Set<string>()
  for (const c of scheduleCards.value) {
    if (c.qty > 0) occupied.add(`${c.lap_no}:${c.turn_seq}`)
  }
  const before = scheduleCards.value.length
  withSuppressedScheduleSideEffects(() => {
    scheduleCards.value = scheduleCards.value.filter((c) => {
      if (!isEmptySlotProductCd(c.product_cd) || c.qty > 0) return true
      return !occupied.has(`${c.lap_no}:${c.turn_seq}`)
    })
  })
  return scheduleCards.value.length !== before
}

function ensureBoardCardSkeletonsForLayout() {
  if (!layoutBoardReady.value || layoutBlocks.value.length === 0) return
  pruneStaleEmptySlots()
  const jigs = Math.max(1, Math.floor(layoutJigsPerLap.value || 1))
  const schedule = currentLayoutLapSchedule()
  if (schedule.length === 0) return
  const newCards: ScheduleCard[] = []
  for (const slot of schedule) {
    const lapNo = slot.lap_no
    for (let turn = 1; turn <= jigs; turn += 1) {
      const hasOccupied = scheduleCards.value.some(
        (c) => c.lap_no === lapNo && c.turn_seq === turn && c.qty > 0,
      )
      if (hasOccupied) continue
      const hasSkeleton = scheduleCards.value.some(
        (c) => c.lap_no === lapNo && c.turn_seq === turn && isEmptySlotProductCd(c.product_cd),
      )
      if (hasSkeleton) continue
      newCards.push(createEmptySlotScheduleCard(lapNo, turn, slot))
    }
  }
  if (newCards.length > 0) {
    withSuppressedScheduleSideEffects(() => {
      scheduleCards.value = [...scheduleCards.value, ...newCards]
    })
  }
}

function getMergedSegCards(ms: LapMergedSegment): ScheduleCard[] {
  const ids = new Set(ms.cardIds)
  return scheduleCards.value.filter((c) => ids.has(c.id) && c.qty > 0)
}

function formatQtyDisplay(n: number): string {
  const v = Number(n)
  if (!Number.isFinite(v)) return '0'
  return Number.isInteger(v) ? String(v) : v.toFixed(2)
}

/** 同一治具ブロック（当該周・連続する plating_machine）の枠数（結合表示の span より tail 列を含む） */
function jigBlockFrameCount(ms: LapMergedSegment, lapNo: number): number {
  const cards = getMergedSegCards(ms)
  if (cards.length === 0) return Math.max(1, Math.floor(Number(ms.span) || 0))
  return findJigBlockCardIds(cards[0].id, lapNo).length
}

/** 治具ブロック内の当該製品が占有する枠数 */
function countProductFramesInJigBlock(lapNo: number, anchorCardId: string, productCd: string): number {
  const blockIds = new Set(findJigBlockCardIds(anchorCardId, lapNo))
  return scheduleCards.value.filter(
    (c) =>
      blockIds.has(c.id) &&
      c.qty > 0 &&
      c.lap_no === lapNo &&
      c.product_cd === productCd &&
      !isJigProductCd(c.product_cd),
  ).length
}

function formatProductNameWithProductionQty(name: string, productionQty: number): string {
  const n = String(name || '').trim()
  if (!n) return ''
  if (!Number.isFinite(productionQty) || productionQty <= 0) return n
  return `${n} (${formatQtyDisplay(productionQty)})`
}

interface JigBlockProductCalcPart {
  productName: string
  qtyLabel: string
  displayText: string
  untilDepleted: boolean
  forceRedText: boolean
}

/** 治具ブロック内の製品表示（出現順・品番ごとに集計） */
function buildJigBlockProductCalcParts(ms: LapMergedSegment, lapNo: number): JigBlockProductCalcPart[] | null {
  const cards = getMergedSegCards(ms)
  const anchor = cards[0]
  if (!anchor) return null
  const blockIds = new Set(findJigBlockCardIds(anchor.id, lapNo))
  if (blockIds.size === 0) return null

  const blockCards = scheduleCards.value
    .filter((c) => blockIds.has(c.id) && c.qty > 0 && c.lap_no === lapNo && !isJigProductCd(c.product_cd))
    .sort((a, b) => a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
  if (blockCards.length === 0) return null

  const order: string[] = []
  const nameByCd = new Map<string, string>()
  const qtyByCd = new Map<string, number>()
  const depletedByCd = new Map<string, boolean>()
  const redByCd = new Map<string, boolean>()
  for (const c of blockCards) {
    if (!nameByCd.has(c.product_cd)) {
      order.push(c.product_cd)
      nameByCd.set(c.product_cd, String(c.product_name || c.product_cd || '').trim())
      depletedByCd.set(c.product_cd, true)
      redByCd.set(c.product_cd, true)
    }
    qtyByCd.set(c.product_cd, (qtyByCd.get(c.product_cd) ?? 0) + cardProductProductionQty(c))
    if (!c.untilDepleted) depletedByCd.set(c.product_cd, false)
    if (!c.forceRedText) redByCd.set(c.product_cd, false)
  }
  const parts: JigBlockProductCalcPart[] = order
    .map((cd) => {
      const name = nameByCd.get(cd)
      if (!name) return null
      const untilDepleted = !!depletedByCd.get(cd)
      const forceRedText = !!redByCd.get(cd)
      const qtyLabel = untilDepleted ? '無くなり次第' : formatQtyDisplay(qtyByCd.get(cd) ?? 0)
      const displayText = untilDepleted ? `${name} (${qtyLabel})` : formatProductNameWithProductionQty(name, qtyByCd.get(cd) ?? 0)
      if (!displayText) return null
      return { productName: name, qtyLabel, displayText, untilDepleted, forceRedText }
    })
    .filter((p): p is JigBlockProductCalcPart => p != null)
  return parts.length > 0 ? parts : null
}

/** 治具枠に製品割当後：製品名 (生産数)（単一製品） */
function formatJigBlockProductCalc(ms: LapMergedSegment, lapNo: number): string | null {
  const parts = buildJigBlockProductCalcParts(ms, lapNo)
  if (!parts || parts.length === 0) return null
  return parts.length === 1 ? parts[0].displayText : null
}

/** 合并块内多个产品：按块内出现顺序去重、「製品名 (生産数)」を "/" で連結 */
function formatJigBlockProductsCalc(ms: LapMergedSegment, lapNo: number): string | null {
  const parts = buildJigBlockProductCalcParts(ms, lapNo)
  if (!parts || parts.length <= 1) return null
  return parts.map((p) => p.displayText).join(' / ')
}

/** 治具ブロック表示幅（治具名・画面1行・印刷の製品名／数量行を個別に評価） */
function estimateJigBlockLayoutNeedCh(ms: LapMergedSegment, lapNo: number): number {
  const jig = formatPlatingBoardLabel(ms.plating_machine, jigBlockFrameCount(ms, lapNo))
  const jigNeedCh = estimateTextWidthCh(jig, 0.98, 1.6)
  const parts = buildJigBlockProductCalcParts(ms, lapNo)
  if (!parts || parts.length === 0) return jigNeedCh

  const sep = ' / '
  const prodNamesLine = parts.map((p) => p.productName).join(sep)
  const prodQtyLine = parts.map((p) => p.qtyLabel).join(sep)
  const displayLine =
    parts.length === 1 ? parts[0].displayText : parts.map((p) => p.displayText).join(sep)

  const screenLineCh = estimateTextWidthCh(displayLine, 1, 1.6)
  const printNameCh = estimateTextWidthCh(prodNamesLine, 0.92, 1.8)
  const printQtyCh = estimateTextWidthCh(prodQtyLine, 0.88, 1.5)
  const longestNameCh = Math.max(
    MIN_LAP_COL_CH,
    ...parts.map((p) => estimateTextWidthCh(p.productName, 1, 1.2)),
  )

  return Math.max(jigNeedCh, screenLineCh, printNameCh, printQtyCh, longestNameCh) + 0.4
}

/** 印刷用：治具ブロック 4 層（治具名・治具数・製品名・製品数） */
function buildJigBlockPrintStackHtml(ms: LapMergedSegment, lapNo: number): string {
  const jigName = escapeHtmlForPrint(String(ms.plating_machine || '').trim() || '—')
  const frames = jigBlockFrameCount(ms, lapNo)
  const jigQty = escapeHtmlForPrint(`(${Math.max(0, Math.floor(Number(frames) || 0))})`)
  const parts = buildJigBlockProductCalcParts(ms, lapNo)

  const prodNameInner =
    parts && parts.length > 0
      ? parts
          .map((part, idx) => {
            const sep = idx > 0 ? '<span class="lap-print-prod-sep"> / </span>' : ''
            const extra =
              part.untilDepleted
                ? 'lap-print-prod--depleted'
                : part.forceRedText
                  ? 'lap-print-prod--force-red'
                  : idx >= 1
                    ? 'lap-print-prod--alt'
                    : ''
            const cls =
              idx >= 1 && !part.forceRedText && !part.untilDepleted
                ? 'lap-print-prod lap-print-prod--alt'
                : extra
                  ? `lap-print-prod lap-print-prod--name ${extra}`
                  : 'lap-print-prod lap-print-prod--name'
            return `${sep}<span class="${cls}">${escapeHtmlForPrint(part.productName)}</span>`
          })
          .join('')
      : ''
  const prodQtyInner =
    parts && parts.length > 0
      ? parts
          .map((part, idx) => {
            const sep = idx > 0 ? '<span class="lap-print-prod-sep"> / </span>' : ''
            const extra = part.untilDepleted
              ? 'lap-print-prod--depleted'
              : part.forceRedText
                ? 'lap-print-prod--force-red'
                : idx >= 1
                  ? 'lap-print-prod--alt'
                  : ''
            const cls = `lap-print-prod lap-print-prod--qty${extra ? ` ${extra}` : ''}`
            return `${sep}<span class="${cls}">${escapeHtmlForPrint(part.qtyLabel)}</span>`
          })
          .join('')
      : ''

  return [
    `<div class="lap-print-layer lap-print-layer--jig-name lap-print-layer--right">${jigName}</div>`,
    `<div class="lap-print-layer lap-print-layer--jig-qty lap-print-layer--right">${jigQty}</div>`,
    `<div class="lap-print-layer lap-print-layer--prod-name lap-print-layer--left">${prodNameInner || '&nbsp;'}</div>`,
    `<div class="lap-print-layer lap-print-layer--prod-qty lap-print-layer--left">${prodQtyInner || '&nbsp;'}</div>`,
  ].join('')
}

function boardMergedSegTitle(ms: LapMergedSegment, lapNo: number): string {
  const frames = jigBlockFrameCount(ms, lapNo)
  const startCol = Math.max(1, Math.floor(Number(ms.startCol) || 1))
  const endCol = Math.min(
    lapBoardColCount.value,
    Math.max(startCol, startCol + Math.max(1, Math.floor(Number(ms.span) || 1)) - 1),
  )
  const colLabel = startCol === endCol ? `第${startCol}列` : `第${startCol}列〜第${endCol}列`
  const base = `${ms.plating_machine}・${frames}本`
  const calc = formatJigBlockProductsCalc(ms, lapNo) ?? formatJigBlockProductCalc(ms, lapNo)
  const hints = [
    `位置: ${colLabel}`,
  ]
  if (!isJigProductCd(ms.product_cd)) {
    return calc ? `${base}・${calc}・${hints.join('・')}` : `${base}・${hints.join('・')}`
  }
  return calc ? `${base}・${calc}・${hints.join('・')}` : `${base}・${hints.join('・')}`
}

function boardTailCardTitle(tc: ScheduleCard): string {
  const colNo = lapBoardColCount.value
  const colLabel = colNo > 0 ? `第${colNo}列` : ''
  const base = `${tc.plating_machine}・治具1本`
  return colLabel
    ? `${base}・位置: ${colLabel}・ダブルクリックで本数変更・削除`
    : `${base}・ダブルクリックで本数変更・削除`
}

/** 当該周で連続する同一メッキ治具（plating_machine）ブロックのカード ID（製品割当後もブロック全体） */
function findJigBlockCardIds(cardId: string, lapNo: number): string[] {
  const sorted = scheduleCards.value
    .filter((c) => c.qty > 0 && c.lap_no === lapNo)
    .sort((a, b) => a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
  const idx = sorted.findIndex((c) => c.id === cardId)
  if (idx < 0) return []
  const mk = normalizeMachineKey(sorted[idx].plating_machine)
  if (!mk) return [sorted[idx].id]
  let start = idx
  let end = idx
  while (start > 0 && normalizeMachineKey(sorted[start - 1].plating_machine) === mk) start -= 1
  while (end < sorted.length - 1 && normalizeMachineKey(sorted[end + 1].plating_machine) === mk) end += 1
  return sorted.slice(start, end + 1).map((c) => c.id)
}

/** 1日あたりの分数（稼働 UI は廃止。投入計算・API の daily_minutes は互換のため 600 固定） */
const PLATING_DAY_MINUTES = 600

const boardLapsPerDay = computed(() => {
  const cycle = layoutBoardReady.value ? layoutMinutesPerLap.value : minutesPerLap.value
  if (cycle <= 0) return 0
  return Math.floor(PLATING_DAY_MINUTES / cycle)
})

function normalizeMachineKey(v: string): string {
  return String(v || '').trim().toLowerCase()
}

/** 同一品番は常に同じ sched-color（在庫/見込リスト等での識別用） */
function schedColorIndexForProductCd(productCd: string): number {
  const s = String(productCd ?? '').trim()
  if (!s) return 0
  let h = 0
  for (let i = 0; i < s.length; i += 1) {
    h = (h * 31 + s.charCodeAt(i)) | 0
  }
  return Math.abs(h) % 24
}

/** ボード表示用：同一メッキ治具は常に同じ色（24色） */
function schedColorIndexForPlatingMachine(machine: string): number {
  const s = normalizeMachineKey(machine)
  if (!s) return 0
  let h = 0
  for (let i = 0; i < s.length; i += 1) {
    h = (h * 33 + s.charCodeAt(i)) | 0
  }
  return Math.abs(h) % 24
}

interface LapBarSegment {
  key: string
  product_cd: string
  product_name: string
  plating_machine: string
  slotCount: number
  widthPct: number
  boardMark: BoardMark
}

interface LapGridCell {
  segments: LapBarSegment[]
}

interface LapMergedSegment {
  key: string
  startCol: number
  span: number
  product_cd: string
  product_name: string
  plating_machine: string
  boardMark: BoardMark
  cardIds: string[]
  slotCount: number
}

interface LapGridRow {
  lap_no: number
  /** 同一計画日内の表示用周番（1 始まり） */
  lap_display_no: number
  cells: LapGridCell[]
  /** null＝未割当の空枠（列セル表示）／配列＝左側列の横結合バー */
  mergedLeft: LapMergedSegment[] | null
  /** 最終列に積まれる枠（横結合しない） */
  mergedTail: ScheduleCard[] | null
}

type LapBoardDisplayItem =
  | { kind: 'date'; key: string; work_date: string; dateLabel: string }
  | { kind: 'lap'; key: string; row: LapGridRow }

/** 1周あたりの治具本数＝列数（レイアウト確定後は layout を優先） */
const lapBoardColCount = computed(() => {
  const j = Math.floor(Number(layoutBoardReady.value ? layoutJigsPerLap.value : jigsPerLap.value) || 0)
  return Math.max(1, Math.min(300, j > 0 ? j : 1))
})

/** 列幅：空列・ヘッダー用の下限（ch）、内容に応じて拡張 */
const MIN_LAP_COL_CH = 0.7
/** 製品セル等の单列上限（ch） */
const MAX_LAP_COL_CH = 22
/** メッキ治具が占める单列上限（ch） */
const MAX_LAP_JIG_COL_CH = 6
/** メッキ治具ブロック全体の上限（標準 15 列分の 50%） */
const MAX_LAP_JIG_BLOCK_TOTAL_CH = MAX_LAP_JIG_COL_CH * 7.5

const lapLabelColWidth = '76px'
const COMPACT_LAP_HEADER_THRESHOLD = 12

/** ③ボード表示：「製品名 (本数)」例 5A54 (5) — 括弧内は当該表示ブロックのメッキ治具本数 */
function formatPlatingBoardLabel(productName: string, jigUnits: number): string {
  const name = String(productName ?? '').trim() || '空'
  const n = Math.max(0, Math.floor(Number(jigUnits) || 0))
  return `${name} (${n})`
}

function splitColumnNumberDigits(value: number): string[] {
  const n = Math.max(1, Math.floor(Number(value) || 1))
  return String(n).split('')
}

const useCompactLapHeader = computed(() => lapBoardColCount.value >= COMPACT_LAP_HEADER_THRESHOLD)

function buildCompactHeaderMarks(colCount: number): number[] {
  const n = Math.max(1, Math.floor(Number(colCount) || 1))
  const marks = new Set<number>([1])
  for (let m = 10; m < n; m += 10) marks.add(m)
  marks.add(n)
  return Array.from(marks).sort((a, b) => a - b)
}

function compactHeaderMarkItems(colCount: number, widths: number[]): Array<{ value: number; leftPct: number }> {
  const marks = buildCompactHeaderMarks(colCount)
  const n = Math.max(1, Math.floor(Number(colCount) || 1))
  const padded =
    widths.length >= n
      ? widths.slice(0, n)
      : [...widths, ...Array.from({ length: n - widths.length }, (_, i) => lapColHeaderWidthCh(widths.length + i + 1))]
  const total = padded.reduce((a, b) => a + b, 0) || 1
  return marks.map((m) => {
    const idx = Math.max(1, Math.min(n, m))
    const before = padded.slice(0, idx - 1).reduce((a, b) => a + b, 0)
    const center = before + (padded[idx - 1] ?? 0) / 2
    return { value: m, leftPct: (center / total) * 100 }
  })
}

const compactLapHeaderMarkItems = computed(() =>
  compactHeaderMarkItems(lapBoardColCount.value, lapBoardColumnWidthsCh.value),
)

function buildCompactHeaderMarksHtml(colCount: number, widths: number[]): string {
  return compactHeaderMarkItems(colCount, widths)
    .map((m) => `<span class="lap-col-head-range-mark" style="left:${m.leftPct}%">${m.value}</span>`)
    .join('')
}

/** 列幅（ch）に応じて表頭に縦表示できる桁数（狭い列は下位桁のみ） */
function columnHeaderMaxVisibleDigits(widthCh: number): number {
  return Math.max(1, Math.floor((widthCh + 0.18) / 0.62))
}

function visibleHeaderDigits(colNo: number, widthCh: number): string[] {
  const all = splitColumnNumberDigits(colNo)
  const maxVis = columnHeaderMaxVisibleDigits(widthCh)
  return all.length <= maxVis ? all : all.slice(-maxVis)
}

function buildLapColumnHeadHtml(colNo: number, widthCh: number): string {
  const digits = visibleHeaderDigits(colNo, widthCh)
  const truncated = digits.length < splitColumnNumberDigits(colNo).length
  const title = truncated ? ` title="${colNo}"` : ''
  const inner = digits.map((d) => `<span class="lap-col-head-digit">${d}</span>`).join('')
  const cls = truncated ? ' lap-col-head--truncated' : ''
  return `<div class="lap-col-head${cls}"${title}><span class="lap-col-head-digits">${inner}</span></div>`
}

/** 1枚＝1セグメント（枠単位の削除・ドラッグ・枠色） */
function cardsToDisplaySegments(cards: ScheduleCard[]): LapBarSegment[] {
  const filtered = cards.filter((c) => c.qty > 0)
  const total = filtered.length || 1
  return filtered.map((c) => ({
    key: c.id,
    product_cd: c.product_cd,
    product_name: c.product_name || '空',
    plating_machine: c.plating_machine || '—',
    slotCount: 1,
    widthPct: (1 / total) * 100,
    boardMark: c.boardMark ?? 'standard',
  }))
}

/**
 * turn_seq（1 始まり）を列番号に対応させて配置。
 * - turn_seq 1〜(n-1) → 各列 1 枚
 * - turn_seq >= n → 最終列に集約（レイアウト超過分）
 */
function binCardsIntoColumns(cards: ScheduleCard[], colCount: number): ScheduleCard[][] {
  const n = Math.max(1, colCount)
  const sorted = [...cards]
    .filter((c) => c.qty > 0)
    .sort((a, b) => a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
  const bins: ScheduleCard[][] = Array.from({ length: n }, () => [])
  for (const c of sorted) {
    const turn = Math.max(0, Math.floor(Number(c.turn_seq) || 0))
    if (turn < 1) {
      bins[n - 1].push(c)
      continue
    }
    if (turn < n) {
      bins[turn - 1].push(c)
    } else {
      bins[n - 1].push(c)
    }
  }
  return bins
}

/** ③ボード治具ブロック結合：同一メッキ治具（machine）なら製品が違っても横結合表示 */
function mergeKeyForScheduleCard(c: ScheduleCard): string {
  return `${normalizeMachineKey(c.plating_machine)}`
}

function boardMarkRank(m: BoardMark): number {
  if (m === 'rush') return 3
  if (m === 'manual') return 2
  return 1
}

function maxBoardMark(a: BoardMark, b: BoardMark): BoardMark {
  return boardMarkRank(a) >= boardMarkRank(b) ? a : b
}

/** 全列を対象に隣接かつ同一メッキ治具なら横結合（最終列も含む。尾列のみの別治具は縦積み） */
function buildMergedLeftSegments(cards: ScheduleCard[], lapNo: number, n: number): LapMergedSegment[] {
  if (n <= 0) return []
  const bins = binCardsIntoColumns(cards, n)
  const colRep: (ScheduleCard | undefined)[] = bins.map((bin) => bin[0])

  const out: LapMergedSegment[] = []
  let i = 0
  while (i < n) {
    if (!colRep[i]) {
      i += 1
      continue
    }
    const mk = mergeKeyForScheduleCard(colRep[i]!)
    let j = i
    let bm: BoardMark = colRep[i]!.boardMark ?? 'standard'
    while (j + 1 < n && colRep[j + 1] && mergeKeyForScheduleCard(colRep[j + 1]!) === mk) {
      j += 1
      bm = maxBoardMark(bm, colRep[j]!.boardMark ?? 'standard')
    }
    const slice: ScheduleCard[] = []
    const cardIds: string[] = []
    for (let k = i; k <= j; k += 1) {
      for (const c of bins[k]) {
        slice.push(c)
        cardIds.push(c.id)
      }
    }
    out.push({
      key: `mg-${lapNo}-L-${i}-${cardIds.join('|')}`,
      startCol: i + 1,
      span: j - i + 1,
      product_cd: slice[0].product_cd,
      product_name: slice[0].product_name || '空',
      plating_machine: slice[0].plating_machine || '—',
      boardMark: bm,
      cardIds,
      slotCount: slice.reduce((s, c) => s + c.qty, 0),
    })
    i = j + 1
  }
  return out
}

function lapNoWorkDateInBoard(lapNo: number, scheduleByLap: Map<number, LapScheduleSlot>): string {
  const fromSchedule = scheduleByLap.get(lapNo)?.work_date
  const fromCard = scheduleCards.value.find((c) => c.lap_no === lapNo)?.lap_work_date
  return (fromSchedule || fromCard || '').slice(0, 10)
}

function collectLapNumbersForBoardGrid(scheduleByLap: Map<number, LapScheduleSlot>): number[] {
  const schedule = currentLayoutLapSchedule()
  const lapNosWithData = boardLapNosWithBoardDataInView()
  const lapNosFromCards = boardLapNosInViewFromScheduleCards()
  const inViewScheduleLaps = schedule
    .filter((s) => isYmdInBoardView(s.work_date))
    .map((s) => s.lap_no)

  if (layoutBoardReady.value) {
    const lapSet = new Set<number>([...inViewScheduleLaps, ...lapNosWithData, ...lapNosFromCards])
    let lapNumbers = [...lapSet].filter((ln) => isYmdInBoardView(lapNoWorkDateInBoard(ln, scheduleByLap)))
    if (lapNumbers.length === 0) return []
    if (scheduleByLap.size > 0) {
      lapNumbers.sort((a, b) => compareLapNoForBoardSort(a, b, scheduleByLap))
    } else {
      lapNumbers.sort((a, b) => a - b)
    }
    return lapNumbers
  }

  let lapNumbers = [...lapNosWithData].sort((a, b) => a - b)
  return lapNumbers.filter((ln) => lapNosWithData.has(ln))
}

const lapGridRows = computed<LapGridRow[]>(() => {
  const n = lapBoardColCount.value
  const byLap = new Map<number, ScheduleCard[]>()
  for (const c of scheduleCards.value) {
    if (c.qty <= 0) continue
    const arr = byLap.get(c.lap_no) ?? []
    arr.push(c)
    byLap.set(c.lap_no, arr)
  }

  const schedule = currentLayoutLapSchedule()
  const scheduleByLap = new Map(schedule.map((s) => [s.lap_no, s]))

  let lapNumbers = collectLapNumbersForBoardGrid(scheduleByLap)

  if (!layoutBoardReady.value) {
    lapNumbers = lapNumbers.filter((ln) => (byLap.get(ln)?.length ?? 0) > 0)
  }
  if (lapNumbers.length === 0) return []

  return lapNumbers.map((lapNo) => {
    const cards = (byLap.get(lapNo) ?? []).sort((a, b) => a.turn_seq - b.turn_seq || a.id.localeCompare(b.id))
    const bins = binCardsIntoColumns(cards, n)
    const cells: LapGridCell[] = bins.map((bin) => ({
      segments: cardsToDisplaySegments(bin),
    }))
    const mergedLeft = cards.length > 0 ? buildMergedLeftSegments(cards, lapNo, n) : null
    const idsInMerged = new Set((mergedLeft ?? []).flatMap((s) => s.cardIds))
    const mergedTail =
      cards.length > 0 ? cards.filter((c) => !idsInMerged.has(c.id)) : null
    const tailOnly = mergedTail != null && mergedTail.length > 0 ? mergedTail : null
    return {
      lap_no: lapNo,
      lap_display_no: lapDisplayNo(lapNo),
      cells,
      mergedLeft,
      mergedTail: tailOnly,
    }
  })
})

/** 表示文字列のおおよその幅（ch）。CJK は 1 字 ≒ 1ch、ASCII は狭め */
function estimateTextWidthCh(text: string, fontScale = 1, padCh = 1.5): number {
  let ch = 0
  for (const c of String(text ?? '')) {
    ch += c.charCodeAt(0) > 0xff ? 1.08 : 0.58
  }
  return Math.ceil(ch * fontScale) + padCh
}

/** 列ヘッダー数字（縦並び）用の最小幅 */
function lapColHeaderWidthCh(colIndex: number): number {
  if (useCompactLapHeader.value) return MIN_LAP_COL_CH
  const digitCount = splitColumnNumberDigits(colIndex).length
  return Math.max(MIN_LAP_COL_CH, 0.62 + digitCount * 0.42)
}

function formatLapBoardGridColumns(widthsCh: number[]): string {
  return widthsCh
    .map((w) => {
      const wch = Math.max(MIN_LAP_COL_CH, Math.min(MAX_LAP_COL_CH, w))
      return `minmax(${wch.toFixed(1)}ch, ${wch.toFixed(1)}ch)`
    })
    .join(' ')
}

/** 治具ブロック／製品ラベルに必要な幅を列へ配分（同一列は最大値を採用） */
function computeLapBoardColumnWidthsCh(rows: LapGridRow[], colCount: number): number[] {
  const widths = Array.from({ length: colCount }, (_, i) => lapColHeaderWidthCh(i + 1))

  const applySpanNeed = (
    startCol: number,
    span: number,
    needTotalCh: number,
    opts?: { maxTotalCh?: number; maxPerColCh?: number },
  ) => {
    const start = Math.max(0, startCol - 1)
    const spanN = Math.max(1, Math.min(span, colCount - start))
    if (spanN <= 0) return
    let need = Math.max(MIN_LAP_COL_CH, needTotalCh)
    if (opts?.maxTotalCh != null) need = Math.min(need, opts.maxTotalCh)
    const current = widths.slice(start, start + spanN).reduce((a, b) => a + b, 0)
    if (need <= current + 0.02) return

    let perColCap = opts?.maxPerColCh ?? MAX_LAP_COL_CH
    const minPerCol = need / spanN
    if (opts?.maxTotalCh == null && minPerCol > perColCap) {
      perColCap = minPerCol
    }

    const targetPerCol = need / spanN
    for (let i = 0; i < spanN; i++) {
      widths[start + i] = Math.min(perColCap, Math.max(widths[start + i], targetPerCol))
    }
    if (opts?.maxTotalCh == null) {
      let sum = widths.slice(start, start + spanN).reduce((a, b) => a + b, 0)
      if (sum < need - 0.02) {
        const bump = (need - sum) / spanN
        for (let i = 0; i < spanN; i++) {
          widths[start + i] += bump
        }
      }
    }
  }

  for (const row of rows) {
    if (row.mergedLeft) {
      for (const ms of row.mergedLeft) {
        const needCh = estimateJigBlockLayoutNeedCh(ms, row.lap_no)
        const hasProducts = (buildJigBlockProductCalcParts(ms, row.lap_no)?.length ?? 0) > 0
        if (hasProducts) {
          applySpanNeed(ms.startCol, ms.span, needCh)
        } else {
          applySpanNeed(ms.startCol, ms.span, needCh, {
            maxTotalCh: MAX_LAP_JIG_BLOCK_TOTAL_CH,
            maxPerColCh: MAX_LAP_JIG_COL_CH,
          })
        }
      }
    }
    if (row.mergedTail) {
      for (const tc of row.mergedTail) {
        applySpanNeed(
          colCount,
          1,
          estimateTextWidthCh(formatPlatingBoardLabel(tc.product_name, 1), 1, 1.0),
        )
      }
    }
    if (!row.mergedLeft) {
      row.cells.forEach((cell, ci) => {
        for (const seg of cell.segments) {
          applySpanNeed(ci + 1, 1, estimateTextWidthCh(formatPlatingBoardLabel(seg.product_name, 1), 1, 1.0))
        }
      })
    }
  }

  for (let i = 0; i < colCount; i++) {
    if (useCompactLapHeader.value) break
    const no = i + 1
    const vis = visibleHeaderDigits(no, widths[i])
    const headerMin = Math.max(MIN_LAP_COL_CH, vis.length * 0.62 + 0.18)
    widths[i] = Math.max(headerMin, widths[i])
  }
  return widths
}

const lapBoardColumnWidthsCh = computed(() =>
  computeLapBoardColumnWidthsCh(lapGridRows.value, lapBoardColCount.value),
)

const lapColumnHeaders = computed(() => {
  const widths = lapBoardColumnWidthsCh.value
  const colCount = lapBoardColCount.value
  return Array.from({ length: colCount }, (_, i) => {
    const no = i + 1
    const w = widths[i] ?? lapColHeaderWidthCh(no)
    const digits = visibleHeaderDigits(no, w)
    const fullLen = splitColumnNumberDigits(no).length
    return { i: no, digits, truncated: digits.length < fullLen }
  })
})

/** 右側本数列は横スクロール、周列は各行で sticky 固定（列幅は製品名で自動調整） */
const lapBoardColsGridStyle = computed(() => ({
  gridTemplateColumns: formatLapBoardGridColumns(lapBoardColumnWidthsCh.value),
}))

/** 印刷：周列幅 + 本数列の合計 ch（A3 横向いっぱいに近づける） */
/** 画面周列 76px の 90% */
const PRINT_RAIL_COL_W = 'calc(76px * 0.9)'
const PRINT_BOARD_COLS_BUDGET_CH = 118

/** 画面列幅の比率を保ちつつ印刷幅へスケール */
function scaleWidthsToPrintBudget(screenWidths: number[], budgetCh: number): number[] {
  if (screenWidths.length === 0) return []
  const total = screenWidths.reduce((a, b) => a + b, 0) || 1
  const factor = budgetCh / total
  return screenWidths.map((w) => Math.max(0.28, w * factor))
}

/** 周目列：日付が変わる直前に日付区切り行を挿入 */
const lapBoardDisplayRows = computed<LapBoardDisplayItem[]>(() => {
  const laps = lapGridRows.value
  if (laps.length === 0) return []
  const schedule = currentLayoutLapSchedule()
  const scheduleByLap = new Map(schedule.map((s) => [s.lap_no, s]))
  const out: LapBoardDisplayItem[] = []
  let prevDate = ''
  for (const row of laps) {
    const slot = scheduleByLap.get(row.lap_no)
    const wd = slot?.work_date ?? layoutPlanDate.value
    if (wd && wd !== prevDate) {
      out.push({
        kind: 'date',
        key: `date-${wd}-${row.lap_no}`,
        work_date: wd,
        dateLabel: slot?.work_date_label ?? formatBoardDateLabel(wd),
      })
      prevDate = wd
    }
    out.push({ kind: 'lap', key: `lap-${row.lap_no}`, row })
  }
  return out
})

function refreshMarksAgainstStandardPositions() {
  const pos = standardPositions.value
  scheduleCards.value = scheduleCards.value.map((c) => {
    if (c.boardMark === 'rush') return c
    const sp = pos.get(c.id)
    if (!sp) return { ...c, boardMark: 'manual' as BoardMark }
    if (sp.lap_no === c.lap_no && sp.turn_seq === c.turn_seq) return { ...c, boardMark: 'standard' as BoardMark }
    return { ...c, boardMark: 'manual' as BoardMark }
  })
}

interface PrintScheduleRange {
  startDate: string
  startLapDisplay: number
  endDate: string
  endLapDisplay: number
}

const printScheduleDialogVisible = ref(false)
const printStartDate = ref('')
const printStartLap = ref(1)
const printEndDate = ref('')
const printEndLap = ref(1)

function printRangeSortKey(workDate: string, lapDisplay: number): number {
  const d = String(workDate || '').slice(0, 10).replace(/-/g, '')
  const n = Math.max(1, Math.floor(Number(lapDisplay) || 1))
  return Number(d || '0') * 10000 + n
}

function normalizePrintScheduleRange(range: PrintScheduleRange): PrintScheduleRange {
  const a = printRangeSortKey(range.startDate, range.startLapDisplay)
  const b = printRangeSortKey(range.endDate, range.endLapDisplay)
  if (a <= b) return range
  return {
    startDate: range.endDate,
    startLapDisplay: range.endLapDisplay,
    endDate: range.startDate,
    endLapDisplay: range.startLapDisplay,
  }
}

function isLapInPrintScheduleRange(lapNo: number, range: PrintScheduleRange): boolean {
  const scheduleByLap = new Map(currentLayoutLapSchedule().map((s) => [s.lap_no, s]))
  const slot = scheduleByLap.get(lapNo)
  const wd = slot?.work_date ?? layoutPlanDate.value
  const display = lapDisplayNo(lapNo)
  const key = printRangeSortKey(wd, display)
  const norm = normalizePrintScheduleRange(range)
  const lo = printRangeSortKey(norm.startDate, norm.startLapDisplay)
  const hi = printRangeSortKey(norm.endDate, norm.endLapDisplay)
  return key >= lo && key <= hi
}

function printLapOptionsForDate(ymd: string): Array<{ value: number; label: string }> {
  const d = String(ymd || '').slice(0, 10)
  if (!d) return []
  return currentLayoutLapSchedule()
    .filter((s) => s.work_date === d)
    .sort((a, b) => a.lap_no - b.lap_no)
    .map((s) => {
      const no = lapDisplayNo(s.lap_no)
      return {
        value: no,
        label: `第${no}周目（${s.start}〜${s.end}）`,
      }
    })
}

const printScheduleAvailableDates = computed(() => {
  const set = new Set<string>()
  for (const s of currentLayoutLapSchedule()) {
    if (s.work_date) set.add(s.work_date)
  }
  return [...set].sort()
})

function printScheduleDateDisabled(date: Date): boolean {
  const ymd = dayjs(date).format('YYYY-MM-DD')
  const avail = printScheduleAvailableDates.value
  if (avail.length === 0) return false
  return !avail.includes(ymd)
}

const printStartLapOptions = computed(() => printLapOptionsForDate(printStartDate.value))
const printEndLapOptions = computed(() => printLapOptionsForDate(printEndDate.value))

const printRangePreviewLabel = computed(() => {
  if (!printStartDate.value || !printEndDate.value) return ''
  const norm = normalizePrintScheduleRange({
    startDate: printStartDate.value,
    startLapDisplay: printStartLap.value,
    endDate: printEndDate.value,
    endLapDisplay: printEndLap.value,
  })
  return `印刷範囲：${formatBoardDateLabel(norm.startDate)} 第${norm.startLapDisplay}周目 〜 ${formatBoardDateLabel(norm.endDate)} 第${norm.endLapDisplay}周目`
})

function syncPrintLapToDateOptions() {
  const startOpts = printStartLapOptions.value
  if (startOpts.length > 0 && !startOpts.some((o) => o.value === printStartLap.value)) {
    printStartLap.value = startOpts[0].value
  }
  const endOpts = printEndLapOptions.value
  if (endOpts.length > 0 && !endOpts.some((o) => o.value === printEndLap.value)) {
    printEndLap.value = endOpts[endOpts.length - 1].value
  }
}

function onPrintScheduleDialogOpened() {
  syncPrintLapToDateOptions()
}

function openPrintScheduleDialog() {
  if (!layoutBoardReady.value) {
    ElMessage.warning('先に「追加レイアウト」で周目を追加してください')
    return
  }
  const schedule = currentLayoutLapSchedule()
  if (schedule.length === 0) {
    ElMessage.warning('印刷対象の周目がありません')
    return
  }
  const { from, to } = boardViewRange.value
  printStartDate.value = from
  printEndDate.value = to
  const startSlots = schedule.filter((s) => s.work_date === from).sort((a, b) => a.lap_no - b.lap_no)
  const endSlots = schedule.filter((s) => s.work_date === to).sort((a, b) => a.lap_no - b.lap_no)
  printStartLap.value = startSlots.length > 0 ? lapDisplayNo(startSlots[0].lap_no) : 1
  printEndLap.value = endSlots.length > 0 ? lapDisplayNo(endSlots[endSlots.length - 1].lap_no) : 1
  printScheduleDialogVisible.value = true
  nextTick(() => syncPrintLapToDateOptions())
}

function buildLapBoardDisplayRowsForPrint(range: PrintScheduleRange): LapBoardDisplayItem[] {
  const norm = normalizePrintScheduleRange(range)
  const schedule = currentLayoutLapSchedule()
  const scheduleByLap = new Map(schedule.map((s) => [s.lap_no, s]))
  const laps = lapGridRows.value.filter((row) => isLapInPrintScheduleRange(row.lap_no, norm))
  if (laps.length === 0) return []
  const out: LapBoardDisplayItem[] = []
  let prevDate = ''
  for (const row of laps) {
    const slot = scheduleByLap.get(row.lap_no)
    const wd = slot?.work_date ?? layoutPlanDate.value
    if (wd && wd !== prevDate) {
      out.push({
        kind: 'date',
        key: `date-${wd}-${row.lap_no}`,
        work_date: wd,
        dateLabel: slot?.work_date_label ?? formatBoardDateLabel(wd),
      })
      prevDate = wd
    }
    out.push({ kind: 'lap', key: `lap-${row.lap_no}`, row })
  }
  return out
}

function hasPrintableScheduleInRange(range: PrintScheduleRange): boolean {
  const norm = normalizePrintScheduleRange(range)
  return scheduleCards.value.some((c) => num(c.qty) > 0 && isLapInPrintScheduleRange(c.lap_no, norm))
}

function totalProductionQtyForPrintRange(range: PrintScheduleRange): number {
  const norm = normalizePrintScheduleRange(range)
  return scheduleCards.value.reduce((sum, c) => {
    if (num(c.qty) <= 0 || !isLapInPrintScheduleRange(c.lap_no, norm)) return sum
    return sum + cardProductProductionQty(c)
  }, 0)
}

function confirmPrintSchedule() {
  if (!printStartDate.value || !printEndDate.value) {
    ElMessage.warning('開始日と終了日を指定してください')
    return
  }
  const range = normalizePrintScheduleRange({
    startDate: printStartDate.value,
    startLapDisplay: Math.max(1, Math.floor(Number(printStartLap.value) || 1)),
    endDate: printEndDate.value,
    endLapDisplay: Math.max(1, Math.floor(Number(printEndLap.value) || 1)),
  })
  const displayRows = buildLapBoardDisplayRowsForPrint(range)
  if (displayRows.length === 0) {
    ElMessage.warning('選択期間に表示する周目がありません')
    return
  }
  if (!hasPrintableScheduleInRange(range)) {
    ElMessage.warning('選択期間に印刷できる割当データがありません')
    return
  }
  printScheduleDialogVisible.value = false
  executePrintScheduleBoard(displayRows, range)
}

watch([printStartDate, printEndDate], () => {
  if (!printScheduleDialogVisible.value) return
  syncPrintLapToDateOptions()
})

function escapeHtmlForPrint(s: string): string {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

/** A3 横向（420×297mm）・印刷余白（上下 1cm、左右 0.7cm） */
const PRINT_A3_PAGE_W_MM = 420
const PRINT_A3_PAGE_H_MM = 297
/** 印刷余白：左右 4mm、上 0.3cm（3mm）、下 0 */
const PRINT_A3_PAD_X_MM = 4
const PRINT_A3_PAD_TOP_MM = 3
const PRINT_A3_PAD_BOTTOM_MM = 0
/** 印刷ボード行高（基準比：97% × 95% × 97% ≈ 89.4%） */
const PRINT_ROW_HEIGHT_MUL = 0.97 * 0.95 * 0.97

/** 印刷ページ内に収めて 1 ページ化（上揃え・列幅比率は維持、はみ出し時はフォント縮小→transform） */
function fitPrintBoardToOnePage(win: Window): void {
  const doc = win.document
  const page = doc.querySelector<HTMLElement>('.print-page')
  const root = doc.querySelector<HTMLElement>('.print-fit-root')
  if (!page || !root) return

  const clearFit = () => {
    root.style.transform = ''
    root.style.width = ''
    root.style.height = ''
  }

  const pageW = page.clientWidth
  const pageH = page.clientHeight
  if (pageW < 1 || pageH < 1) return

  clearFit()
  let fontMul = 1
  root.style.setProperty('--print-font-mul', '1')

  const measure = () => ({ w: root.scrollWidth, h: root.scrollHeight })
  let { w: contentW, h: contentH } = measure()
  if (contentW < 1 || contentH < 1) return

  const minFontMul = 0.48
  for (let i = 0; i < 28 && (contentW > pageW || contentH > pageH) && fontMul > minFontMul; i++) {
    const ratio = Math.min(pageW / contentW, pageH / contentH) * 0.97
    fontMul = Math.max(minFontMul, fontMul * ratio)
    root.style.setProperty('--print-font-mul', String(fontMul))
    clearFit()
    ;({ w: contentW, h: contentH } = measure())
  }

  let scale = Math.min(pageW / contentW, pageH / contentH)
  const scaleFillW = pageW / contentW
  if (scaleFillW > scale && scaleFillW * contentH <= pageH * 0.995) {
    scale = scaleFillW
  }
  const scaledW = contentW * scale
  const offsetX = Math.max(0, (pageW - scaledW) / 2)
  const offsetY = 0

  root.style.transformOrigin = 'top left'
  root.style.transform = `translate(${offsetX}px, ${offsetY}px) scale(${scale})`
  root.style.width = `${contentW}px`
  root.style.height = `${contentH}px`
}


function boardMarkSegClass(m: BoardMark, merged: boolean): string {
  if (m === 'manual') return merged ? 'lap-merged-seg--manual' : 'lap-segment--manual'
  if (m === 'rush') return merged ? 'lap-merged-seg--rush' : 'lap-segment--rush'
  return ''
}

function buildLapBoardRowGridPrintHtml(row: LapGridRow, n: number, gridCols: string): string {
  if (row.mergedLeft != null) {
    const leftSegs = row.mergedLeft
      .map((ms) => {
        const inner = buildJigBlockPrintStackHtml(ms, row.lap_no)
        return `<div class="lap-merged-seg lap-merged-seg--print-jig" style="grid-column:${ms.startCol} / span ${ms.span};grid-row:1"><div class="lap-merged-label-stack lap-merged-label-stack--print-4">${inner}</div></div>`
      })
      .join('')
    let tailHtml = ''
    const tail = row.mergedTail
    if (tail != null && tail.length > 0) {
      const items = tail
        .map((tc) => {
          const ci = schedColorIndexForPlatingMachine(tc.plating_machine)
          const mk = boardMarkSegClass(tc.boardMark, true)
          return `<div class="lap-merged-tail-item sched-color-${ci} ${mk}"><span class="lap-merged-text">${escapeHtmlForPrint(
            formatPlatingBoardLabel(tc.product_name, 1),
          )}</span></div>`
        })
        .join('')
      tailHtml = `<div class="lap-merged-tail" style="grid-column:${n} / span 1;grid-row:1">${items}</div>`
    }
    return `<div class="lap-merged-host" style="${gridCols}">${leftSegs}${tailHtml}</div>`
  }

  const cells = row.cells
    .map((cell) => {
      const segs = cell.segments
        .map((seg) => {
          const ci = schedColorIndexForPlatingMachine(seg.plating_machine)
          const mk = boardMarkSegClass(seg.boardMark, false)
          return `<div class="lap-segment lap-segment--cell sched-color-${ci} ${mk}" style="flex:${seg.slotCount}"><span class="lap-segment-text">${escapeHtmlForPrint(
            formatPlatingBoardLabel(seg.product_name, 1),
          )}</span></div>`
        })
        .join('')
      const empty = cell.segments.length === 0 ? ' lap-col--empty' : ''
      return `<div class="lap-col${empty}"><div class="lap-track lap-track--grid">${segs}</div></div>`
    })
    .join('')
  return cells
}

/** 画面と同じ lap-board-layout 構造で印刷 HTML を組み立てる */
function buildPrintBoardLayoutHtml(displayRows: LapBoardDisplayItem[], n: number, colWidths: number[]): string {
  const cols = formatLapBoardGridColumns(colWidths)
  const gridCols = `grid-template-columns:${cols}`

  const headCols = useCompactLapHeader.value
    ? `<div class="lap-col-head-range">${buildCompactHeaderMarksHtml(n, colWidths)}</div>`
    : Array.from({ length: n }, (_, i) => {
        const no = i + 1
        const w = colWidths[i] ?? lapColHeaderWidthCh(no)
        return buildLapColumnHeadHtml(no, w)
      }).join('')

  const headRow = `<div class="lap-board-row lap-board-row--head">
    <div class="lap-rail-cell lap-rail-head">周</div>
    <div class="lap-board-grid lap-board-head" style="${gridCols}">${headCols}</div>
  </div>`

  const body = displayRows
    .map((item) => {
      if (item.kind === 'date') {
        const memo = getBoardDateMemo(item.work_date)
        const memoHtml = memo
          ? `<span class="lap-date-memo-text">${escapeHtmlForPrint(memo)}</span>`
          : ''
        return `<div class="lap-board-row lap-board-row--date">
          <div class="lap-rail-cell lap-rail-date">${escapeHtmlForPrint(item.dateLabel)}</div>
          <div class="lap-board-grid lap-board-date-row lap-date-scroll-row" style="${gridCols}">
            <div class="lap-date-band-scroll lap-date-memo-zone">${memoHtml}</div>
          </div>
        </div>`
      }
      const row = item.row
      const timeLbl = lapTimeRangeLabel(row.lap_no)
      const lapNoHtml = `<span class="lap-label-no">第${row.lap_display_no}周目</span>`
      const timeHtml = timeLbl ? `<span class="lap-label-time">${escapeHtmlForPrint(timeLbl)}</span>` : ''
      return `<div class="lap-board-row lap-board-row--lap">
        <div class="lap-rail-cell lap-rail-lap">${lapNoHtml}${timeHtml}</div>
        <div class="lap-board-grid lap-board-body-row lap-board-body-row--lap" style="${gridCols}">
          ${buildLapBoardRowGridPrintHtml(row, n, gridCols)}
        </div>
      </div>`
    })
    .join('')

  return `<div class="lap-board-layout">${headRow}${body}</div>`
}

function formatPrintScheduleRangeLabel(range: PrintScheduleRange): string {
  const norm = normalizePrintScheduleRange(range)
  return `${formatBoardDateLabel(norm.startDate)} 第${norm.startLapDisplay}周目 〜 ${formatBoardDateLabel(norm.endDate)} 第${norm.endLapDisplay}周目`
}

function executePrintScheduleBoard(displayRows: LapBoardDisplayItem[], range: PrintScheduleRange) {
  const workDate = draftWorkDate.value || '—'
  const printedAt = dayjs().tz(TZ_JP).format('YYYY-MM-DD HH:mm:ss')
  const productionTotalLabel = `生産数合計：${formatQtyDisplay(totalProductionQtyForPrintRange(range))}`

  const n = lapBoardColCount.value
  const printColWidths = scaleWidthsToPrintBudget(lapBoardColumnWidthsCh.value.slice(0, n), PRINT_BOARD_COLS_BUDGET_CH)
  const boardLayoutHtml = buildPrintBoardLayoutHtml(displayRows, n, printColWidths)

  const innerW = PRINT_A3_PAGE_W_MM - PRINT_A3_PAD_X_MM * 2
  const innerH = PRINT_A3_PAGE_H_MM - PRINT_A3_PAD_TOP_MM - PRINT_A3_PAD_BOTTOM_MM

  const html = `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8"/>
  <title>メッキ投入スケジュール ${escapeHtmlForPrint(workDate)}</title>
  <style>
    html {
      -webkit-print-color-adjust: exact; print-color-adjust: exact;
      --print-row-mul: ${PRINT_ROW_HEIGHT_MUL};
    }
    * { box-sizing: border-box; }
    html, body {
      margin: 0; padding: 0; width: ${PRINT_A3_PAGE_W_MM}mm; height: ${PRINT_A3_PAGE_H_MM}mm;
      overflow: hidden; background: #fff;
    }
    body {
      font-family: 'Segoe UI', 'Hiragino Sans', Meiryo, sans-serif;
      color: #303133;
      font-size: calc(8pt * var(--print-font-mul, 1));
    }
    .print-page {
      width: ${innerW}mm; height: ${innerH}mm;
      margin: ${PRINT_A3_PAD_TOP_MM}mm ${PRINT_A3_PAD_X_MM}mm ${PRINT_A3_PAD_BOTTOM_MM}mm;
      overflow: hidden;
      position: relative;
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      justify-content: flex-start;
    }
    .print-fit-root { display: block; width: max-content; max-width: none; flex-shrink: 0; }
    .print-header-block {
      margin-bottom: 2mm;
      display: flex;
      flex-wrap: wrap;
      align-items: baseline;
      justify-content: space-between;
      gap: 4px 10px;
      width: 100%;
    }
    .print-title {
      margin: 0; font-size: 11pt; font-weight: 700; color: #303133; line-height: 1.2;
      flex-shrink: 0;
    }
    .print-meta {
      margin: 0; font-size: 7pt; color: #606266; line-height: 1.25;
      display: flex; flex-wrap: wrap; justify-content: flex-end; align-items: baseline;
      gap: 0 10px; flex: 1 1 auto; text-align: right;
    }
    .print-meta span { display: inline-block; white-space: nowrap; }
    .lap-board { padding: 0; border: 1px solid #d9deea; border-radius: 6px; background: #fff; }
    .lap-board,
    .lap-board * {
      font-weight: 400 !important;
    }
    .lap-board-layout { display: flex; flex-direction: column; width: max-content; }
    .lap-board-row {
      display: grid; grid-template-columns: ${PRINT_RAIL_COL_W} max-content;
      align-items: stretch; border-bottom: 1px solid #ebeef5;
    }
    .lap-board-row:last-child { border-bottom: none; }
    .lap-rail-cell {
      display: flex; flex-direction: column; align-items: flex-end; justify-content: center;
      gap: 1px; padding: 2px 4px; border-right: 1px solid #ebeef5; background: #fff;
    }
    .lap-rail-head {
      align-items: center; justify-content: center;
      font-size: calc(7pt * var(--print-font-mul, 1)); font-weight: 400;
      color: #606266; background: #f5f7fa;
    }
    .lap-rail-date {
      font-size: calc(9pt * var(--print-font-mul, 1)); font-weight: 400; color: #1f5fd6;
      background: color-mix(in oklab, #ecf5ff 90%, #fff);
    }
    .lap-rail-lap {
      font-size: calc(8pt * var(--print-font-mul, 1)); font-weight: 400; color: #606266;
    }
    .lap-label-no { white-space: nowrap; }
    .lap-label-time {
      font-size: calc(7pt * var(--print-font-mul, 1)); font-weight: 400; color: #1f5fd6; white-space: nowrap;
    }
    .lap-board-grid {
      display: grid; align-items: stretch; gap: 0; width: max-content; box-sizing: border-box;
    }
    .lap-board-head { background: #f5f7fa; min-height: calc(18px * var(--print-font-mul, 1) * var(--print-row-mul, 0.894)); }
    .lap-board-body-row--lap { min-height: calc(24px * var(--print-font-mul, 1) * var(--print-row-mul, 0.894)); background: #fff; }
    .lap-board-date-row,
    .lap-date-scroll-row {
      background: color-mix(in oklab, #ecf5ff 85%, #fff);
      min-height: calc(20px * var(--print-font-mul, 1) * var(--print-row-mul, 0.894));
    }
    .lap-date-band-scroll {
      grid-column: 1 / -1; min-height: calc(20px * var(--print-font-mul, 1) * var(--print-row-mul, 0.894));
      background: color-mix(in oklab, #ecf5ff 55%, #fff);
    }
    .lap-col-head {
      display: flex; flex-direction: column; align-items: center; justify-content: center;
      gap: 0; line-height: 1; padding: 1px 1px;
      font-size: calc(6pt * var(--print-font-mul, 1)); font-weight: 400; color: #909399;
      border-right: 1px solid #ebeef5; background: #f5f7fa;
    }
    .lap-col-head-range {
      grid-column: 1 / -1;
      position: relative;
      display: block;
      font-size: calc(6pt * var(--print-font-mul, 1));
      font-weight: 400;
      color: #1f5fd6;
      line-height: 1;
      padding: 1px 3px;
      border-right: none;
      background: #f5f7fa;
      min-height: calc(18px * var(--print-font-mul, 1) * var(--print-row-mul, 0.894));
      border-top: 1px solid #cddfff;
    }
    .lap-col-head-range-mark {
      position: absolute;
      top: 50%;
      transform: translate(-50%, -50%);
      display: inline-block;
      min-width: 1ch;
      text-align: center;
      white-space: nowrap;
      text-shadow: 0 1px 0 rgba(255, 255, 255, 0.75);
    }
    .lap-col-head-digits { display: inline-flex; flex-direction: column; align-items: center; justify-content: center; gap: 0; }
    .lap-col-head-digit { font-size: calc(6pt * var(--print-font-mul, 1)); font-weight: 400; font-variant-numeric: tabular-nums; line-height: 1; color: #1f5fd6; }
    .lap-board-grid > *:last-child { border-right: none; }
    .lap-merged-host {
      grid-column: 1 / -1; display: grid; align-items: stretch; min-height: calc(30px * var(--print-font-mul, 1) * var(--print-row-mul, 0.894));
      box-sizing: border-box; overflow: hidden;
    }
    .lap-merged-seg,
    .lap-merged-seg--print-jig,
    .lap-merged-host .lap-merged-seg {
      position: relative; min-width: 0; max-width: 100%;
      padding: 2px 3px; margin: 1px 0; box-sizing: border-box;
      border: 0.5pt solid #000 !important;
      border-radius: 2px;
      overflow: hidden;
      background: #fff !important;
      box-shadow: none !important;
      outline: none !important;
    }
    .lap-merged-seg--manual,
    .lap-merged-seg--rush,
    .lap-merged-seg--print-jig.lap-merged-seg--manual,
    .lap-merged-seg--print-jig.lap-merged-seg--rush {
      outline: none !important;
      border: 0.5pt solid #000 !important;
      background: #fff !important;
    }
    .lap-merged-label-stack {
      position: absolute; top: 1px; right: 2px; left: 2px; bottom: 1px;
      display: flex; flex-direction: column; align-items: stretch; gap: 1px; overflow: hidden;
      pointer-events: none;
    }
    .lap-merged-label-stack--print-4 {
      justify-content: flex-start;
      gap: 0;
    }
    .lap-print-layer {
      line-height: 1.12;
      font-weight: 400;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: clip;
      padding: 0 2px;
      box-sizing: border-box;
      width: 100%;
      font-size: calc(4.5pt * var(--print-font-mul, 1));
    }
    .lap-print-layer--right {
      text-align: right;
      align-self: flex-end;
      color: #000;
    }
    .lap-print-layer--left {
      text-align: left;
      align-self: flex-start;
      color: #1f5fd6;
    }
    .lap-print-layer--jig-name {
      font-size: calc(4pt * var(--print-font-mul, 1));
    }
    .lap-print-layer--jig-qty {
      font-size: calc(4pt * var(--print-font-mul, 1));
    }
    .lap-print-layer--prod-name {
      font-size: calc(5pt * var(--print-font-mul, 1));
    }
    .lap-print-layer--prod-qty {
      font-size: calc(4pt * var(--print-font-mul, 1));
    }
    .lap-print-prod--alt {
      color: #cf1322 !important;
      font-weight: 400 !important;
    }
    .lap-print-prod--depleted {
      color: #cf1322 !important;
      font-weight: 600 !important;
    }
    .lap-print-prod--force-red {
      color: #cf1322 !important;
      font-weight: 700 !important;
    }
    .lap-print-prod-sep {
      color: #303133;
      font-weight: 400;
    }
    .lap-merged-text { line-height: 1.15; font-weight: 400; color: #303133; font-size: calc(5pt * var(--print-font-mul, 1)); }
    .lap-merged-tail {
      display: flex; flex-direction: column; gap: 1px; min-width: 0; max-width: 100%; padding: 1px;
      box-sizing: border-box; border-left: 1px solid #ebeef5; overflow: hidden;
    }
    .lap-merged-tail-item {
      position: relative; flex: 0 0 auto; min-width: 0; max-width: 100%; min-height: 16px;
      padding: 1px 2px; border-radius: 3px; border: 0.5px solid rgba(48,67,96,0.2); box-sizing: border-box; overflow: hidden;
    }
    .lap-merged-tail-item .lap-merged-text { display: block; width: 100%; box-sizing: border-box; }
    .lap-col {
      min-width: 0; max-width: 100%; border-right: 1px solid #ebeef5; padding: 1px;
      display: flex; flex-direction: column; box-sizing: border-box; overflow: hidden;
    }
    .lap-col--empty .lap-track--grid { opacity: 0.55; }
    .sched-color-0 { background: #dbe8d4; }
    .sched-color-1 { background: #c9dce8; }
    .sched-color-2 { background: #edd9c8; }
    .sched-color-3 { background: #d4cce8; }
    .sched-color-4 { background: #c9e4df; }
    .sched-color-5 { background: #e5d9b8; }
    .sched-color-6 { background: #cdd5e0; }
    .sched-color-7 { background: #e0cfcf; }
    .sched-color-8 { background: #d7e7f8; }
    .sched-color-9 { background: #d8f0e2; }
    .sched-color-10 { background: #f8e3d4; }
    .sched-color-11 { background: #e6dcf8; }
    .sched-color-12 { background: #d6ecef; }
    .sched-color-13 { background: #f2e6c9; }
    .sched-color-14 { background: #d8dbe9; }
    .sched-color-15 { background: #f0dadd; }
    .sched-color-16 { background: #d4eaf0; }
    .sched-color-17 { background: #e2edd4; }
    .sched-color-18 { background: #f3dfcf; }
    .sched-color-19 { background: #ddd5ee; }
    .sched-color-20 { background: #cfe8e2; }
    .sched-color-21 { background: #ece2bf; }
    .sched-color-22 { background: #d3d9e6; }
    .sched-color-23 { background: #ebd8d8; }
    .lap-track--grid {
      flex: 1; display: flex; flex-direction: column; min-height: 12px; gap: 1px;
      border-radius: 3px; overflow: hidden; background: #f5f7fa;
    }
    .lap-segment--cell {
      position: relative; min-width: 0; max-width: 100%; min-height: 16px; padding: 1px 2px; border-radius: 2px; overflow: hidden;
    }
    .lap-segment--manual { outline: 2px solid #fa8c16; outline-offset: -1px; z-index: 1; }
    .lap-segment--rush { outline: 2px solid #cf1322; outline-offset: -1px; z-index: 1; }
    .lap-segment-text {
      display: block; font-size: calc(5pt * var(--print-font-mul, 1)); line-height: 1.15;
      text-align: right; white-space: nowrap; overflow: hidden; text-overflow: clip;
      font-weight: 400; box-sizing: border-box;
    }
    @media print {
      @page { size: A3 landscape; margin: ${PRINT_A3_PAD_TOP_MM}mm ${PRINT_A3_PAD_X_MM}mm ${PRINT_A3_PAD_BOTTOM_MM}mm; }
      html, body {
        margin: 0 !important; padding: 0 !important;
        width: ${PRINT_A3_PAGE_W_MM}mm !important; height: ${PRINT_A3_PAGE_H_MM}mm !important;
        overflow: hidden !important;
      }
      * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
      .print-page {
        width: ${innerW}mm !important; height: ${innerH}mm !important;
        margin: ${PRINT_A3_PAD_TOP_MM}mm ${PRINT_A3_PAD_X_MM}mm ${PRINT_A3_PAD_BOTTOM_MM}mm !important; overflow: hidden !important;
        page-break-after: avoid; page-break-inside: avoid;
      }
      .print-fit-root, .print-board-target, .lap-board, .lap-board-layout, .lap-board-grid {
        page-break-inside: avoid;
      }
      .lap-merged-host .lap-merged-seg,
      .lap-merged-seg--print-jig {
        border: 0.5pt solid #000 !important;
        outline: none !important;
        background: #fff !important;
        box-shadow: none !important;
      }
      .lap-board,
      .lap-board * {
        font-weight: 400 !important;
      }
    }
  </style>
</head>
<body>
  <div class="print-page">
    <div class="print-fit-root">
      <div class="print-header-block">
        <h1 class="print-title">メッキ投入ボード</h1>
        <div class="print-meta">
          <span>作業日：${escapeHtmlForPrint(workDate)}</span>
          <span>印刷日時：${escapeHtmlForPrint(printedAt)}</span>
          <span>${escapeHtmlForPrint(productionTotalLabel)}</span>
        </div>
      </div>
      <div class="print-board-target">
        <div class="lap-board">${boardLayoutHtml}</div>
      </div>
    </div>
  </div>
</body>
</html>`

  /**
   * window.open + document.write は環境によって印刷プレビューが真っ白になることがある。
   * 実寸の離屏 iframe に書き込み、load／readyState 後に print する。
   */
  const iframe = document.createElement('iframe')
  iframe.setAttribute('aria-hidden', 'true')
  iframe.title = 'メッキ投入スケジュール印刷'
  iframe.style.cssText = [
    'position:fixed',
    'left:-20000px',
    'top:0',
    `width:${PRINT_A3_PAGE_W_MM}mm`,
    `height:${PRINT_A3_PAGE_H_MM}mm`,
    'border:0',
    'opacity:0',
    'pointer-events:none',
    'z-index:-1',
  ].join(';')

  document.body.appendChild(iframe)

  const doc = iframe.contentDocument
  const win = iframe.contentWindow
  if (!doc || !win) {
    iframe.remove()
    ElMessage.error('印刷の準備に失敗しました')
    return
  }

  const removeIframe = () => {
    try {
      iframe.remove()
    } catch {
      /* ignore */
    }
  }

  let printed = false
  const doPrint = () => {
    if (printed) return
    printed = true
    try {
      fitPrintBoardToOnePage(win)
      win.focus()
      win.print()
    } catch {
      /* ignore */
    }
    win.addEventListener('afterprint', removeIframe, { once: true })
    window.setTimeout(removeIframe, 4000)
  }

  const schedulePrint = () => {
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        window.setTimeout(doPrint, 50)
      })
    })
  }

  /** write の前に登録しないと load を取りこぼす場合がある */
  iframe.addEventListener('load', schedulePrint, { once: true })

  doc.open()
  doc.write(html)
  doc.close()

  if (doc.readyState === 'complete') {
    window.setTimeout(schedulePrint, 0)
  }
  window.setTimeout(() => {
    if (!printed) schedulePrint()
  }, 400)
}

/** 製品枠の生産数量（qty × 掛け数）。治具のみ枠は 0 */
function cardProductProductionQty(c: ScheduleCard): number {
  if (isJigProductCd(c.product_cd) || isEmptySlotProductCd(c.product_cd)) return 0
  const q = Math.max(0, Math.floor(num(c.qty)))
  const k = c.kake > 0 ? c.kake : 1
  return q * k
}

const kpi = computed(() => {
  const jigs = layoutBoardReady.value ? layoutJigsPerLap.value : jigsPerLap.value
  const cycle = minutesPerLap.value
  const scheduleByLap = new Map(currentLayoutLapSchedule().map((s) => [s.lap_no, s]))
  const visibleLapSet = new Set(lapGridRows.value.map((r) => r.lap_no))
  const visibleCards = scheduleCards.value.filter(
    (c) => c.qty > 0 && visibleLapSet.has(c.lap_no) && isLapNoInBoardView(c.lap_no, scheduleByLap),
  )
  const totalProductQty = visibleCards.reduce((s, c) => s + cardProductProductionQty(c), 0)
  if (jigs <= 0 || cycle <= 0) {
    return { totalSlots: 0, usedSlots: 0, remainSlots: 0, utilizationPct: '—', estimatedMinutes: 0, totalProductQty }
  }
  const lapsPerDay = Math.floor(PLATING_DAY_MINUTES / cycle)
  const visibleLapCount = lapGridRows.value.length
  const totalSlots =
    layoutBoardReady.value && visibleLapCount > 0
      ? visibleLapCount * jigs
      : layoutBoardReady.value && layoutMaxLaps.value > 0
        ? layoutMaxLaps.value * jigs
        : lapsPerDay * jigs
  const usedSlots = visibleCards.length
  const remainSlots = Math.max(totalSlots - usedSlots, 0)
  /** 充填率＝使用中の枠数 / 総治具数（数量ではなく枠ベースで算出） */
  const utilizationPct = totalSlots > 0 ? ((usedSlots / totalSlots) * 100).toFixed(1) : '—'
  const usedLaps = jigs > 0 ? Math.ceil(usedSlots / jigs) : 0
  const estimatedMinutes = usedLaps * cycle
  return { totalSlots, usedSlots, remainSlots, utilizationPct, estimatedMinutes, totalProductQty }
})

async function reloadBoardView() {
  await loadLatestDraft({ autoMode: true, autoSyncWorkDate: false })
}

export function usePlatingInputBoard(mode: PlatingInputBoardMode = 'instruction') {
  const readonly = mode === 'instruction'

  onMounted(() => {
    boardViewRangeReady = true
    void reloadBoardView()
  })

  onBeforeUnmount(() => {
    cancelBoardViewRangeReload()
  })

  watch(
    [boardFilterFrom, boardFilterTo],
    () => {
      if (skipBoardViewRangeWatchOnce) {
        skipBoardViewRangeWatchOnce = false
        return
      }
      scheduleBoardViewRangeReload()
    },
  )

  return {
    readonly,
    ArrowLeft,
    ArrowRight,
    Printer,
    boardFilterDateRange,
    boardPeriodFilterLoading,
    boardTableLoading,
    boardViewRangeLabel,
    onBoardViewRangeChange,
    shiftBoardViewRange,
    setBoardViewRangeToday,
    layoutBoardReady,
    kpi,
    lapBoardDisplayRows,
    lapBoardColsGridStyle,
    lapColumnHeaders,
    useCompactLapHeader,
    compactLapHeaderMarkItems,
    lapBoardColCount,
    schedColorIndexForPlatingMachine,
    formatPlatingBoardLabel,
    buildJigBlockProductCalcParts,
    boardMergedSegTitle,
    boardTailCardTitle,
    lapTimeRangeLabel,
    getBoardDateMemo,
    jigBlockFrameCount,
    openPrintScheduleDialog,
    printScheduleDialogVisible,
    printStartDate,
    printEndDate,
    printStartLap,
    printEndLap,
    printStartLapOptions,
    printEndLapOptions,
    printScheduleDateDisabled,
    printRangePreviewLabel,
    onPrintScheduleDialogOpened,
    confirmPrintSchedule,
    reloadBoardView,
  }
}
