/**
 * 成型「ライン順で再計算」— 計画作成（単設備）と計画一覧（全設備）で共通の確認文・API 呼び出し。
 */
import { h, type VNode } from 'vue'
import {
  formatReplanSequenceSuccessMessage,
  replanLineSequence,
  type ReplanSequenceResponse,
} from '@/api/aps'

export { formatReplanSequenceSuccessMessage }

export const FORMING_REPLAN_MESSAGE_BOX_CLASS = 'forming-replan-messagebox'

const LEAD_PAST_AND_TODAY =
  '再計算時は、過去日（本日より前）の日別計画を固定します。さらに本日分は実績がある場合のみ固定し、実績がない場合は当日以降を設備稼働時間に合わせて再計算します。'

const LEAD_FORCED_START =
  '計画一覧で「開始日指定」が設定されている製品は、その指定日より前には開始せずに再計算されます。'

const LEAD_FUTURE_ANCHOR =
  'アンカー日が未来の場合でも、再計算は明日以降を連続で再作成します（空白期間は作りません）。'

function confirmShell(children: VNode[]): VNode {
  return h('div', { class: 'forming-replan-confirm' }, children)
}

/** 計画作成画面：選択中設備のライン順再計算確認文 */
export function buildSingleLineFormingReplanConfirmVNode(opts: {
  lineLabel: string
  lineCode?: string
  effectiveAnchorIso: string
  anchorFallbackLabel: string
  anchorFallbackIso: string
  todayIso: string
}): VNode {
  const nameBlockChildren = [h('div', { class: 'forming-replan-confirm__name' }, opts.lineLabel)]
  const code = (opts.lineCode || '').trim()
  if (code && code !== opts.lineLabel) {
    nameBlockChildren.push(h('div', { class: 'forming-replan-confirm__code' }, code))
  }
  return confirmShell([
    h('p', { class: 'forming-replan-confirm__lead' }, '選択中の設備について、順位どおりに再計算します。'),
    h('div', { class: 'forming-replan-confirm__name-block' }, nameBlockChildren),
    h('p', { class: 'forming-replan-confirm__lead' }, LEAD_PAST_AND_TODAY),
    h('p', { class: 'forming-replan-confirm__lead' }, LEAD_FORCED_START),
    h(
      'p',
      { class: 'forming-replan-confirm__lead' },
      `設備に保存済みの再計算アンカー日があれば最優先。未設定時は${opts.anchorFallbackLabel}（${opts.anchorFallbackIso || '—'}）と本日（${opts.todayIso}）の遅い方（${opts.effectiveAnchorIso}）を使用します。`,
    ),
    h('p', { class: 'forming-replan-confirm__q' }, '実行しますか？'),
  ])
}

/** 計画一覧画面：工程内全設備の順次再計算確認文 */
export function buildAllLinesFormingReplanConfirmVNode(opts: {
  processName: string
  processCode?: string
  effectiveAnchorIso: string
  anchorFallbackIso: string
  todayIso: string
}): VNode {
  const cd = (opts.processCode || '').trim()
  const name = (opts.processName || '').trim() || '—'
  const showCode = !!cd && name !== cd
  const nameBlockChildren = [h('div', { class: 'forming-replan-confirm__name' }, name)]
  if (showCode) nameBlockChildren.push(h('div', { class: 'forming-replan-confirm__code' }, cd))
  return confirmShell([
    h(
      'p',
      { class: 'forming-replan-confirm__lead' },
      '次の工程について、すべての有効設備をラインコード順に順次再計算します。',
    ),
    h('div', { class: 'forming-replan-confirm__name-block' }, nameBlockChildren),
    h('p', { class: 'forming-replan-confirm__lead' }, LEAD_PAST_AND_TODAY),
    h('p', { class: 'forming-replan-confirm__lead' }, LEAD_FORCED_START),
    h('p', { class: 'forming-replan-confirm__lead' }, LEAD_FUTURE_ANCHOR),
    h(
      'p',
      { class: 'forming-replan-confirm__lead' },
      `設備ごとに保存済みの再計算アンカー日があれば最優先。未設定時は検索期間の月初（${opts.anchorFallbackIso}）と本日（${opts.todayIso}）の遅い方（${opts.effectiveAnchorIso}）をフォールバックに使います。`,
    ),
    h('p', { class: 'forming-replan-confirm__q' }, '実行しますか？'),
  ])
}

/** 単設備 replan-sequence（instruction_plans 同期 ON・開発時 debug ON） */
export async function runFormingLineReplanSequence(
  lineId: number,
  anchorStartDate: string,
  includeDebug = import.meta.env.DEV,
): Promise<{ res: ReplanSequenceResponse; elapsedMs: number }> {
  const t0 = performance.now()
  const res = await replanLineSequence(lineId, anchorStartDate, true, includeDebug)
  return { res, elapsedMs: Math.round(performance.now() - t0) }
}

/** 全設備再計算完了時の集約メッセージ（formatReplanSequenceSuccessMessage と同形式） */
export function formatBulkFormingReplanSuccessMessage(opts: {
  lineCount: number
  totalElapsedMs: number
  skippedStep1Count: number
  totalScheduleCount?: number
}): string {
  const base = `全 ${opts.lineCount} 設備の順次再計算が完了しました`
  const summary: ReplanSequenceResponse = {
    message: base,
    data: {
      count: opts.totalScheduleCount,
      skipped_step1: opts.skippedStep1Count > 0 ? true : undefined,
    },
  }
  return formatReplanSequenceSuccessMessage(summary, opts.totalElapsedMs)
}
