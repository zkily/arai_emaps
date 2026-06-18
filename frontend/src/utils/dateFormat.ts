/**
 * 日付・時刻フォーマットユーティリティ（日本標準時 JST = Asia/Tokyo 固定）
 * 表示ロケールは i18n に合わせて切り替え可能
 */

const JST_TIMEZONE = 'Asia/Tokyo'

/** 現在の JST 日付を YYYY-MM-DD で取得（サーバー/クライアントのタイムゾーンに依存しない） */
export function getJSTToday(): string {
  const formatter = new Intl.DateTimeFormat('en-CA', {
    timeZone: JST_TIMEZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
  return formatter.format(new Date()).replace(/\//g, '-')
}

/** 文字列を JST の Date として解釈（YYYY-MM-DD または ISO 想定） */
export function parseDateAsJST(dateStr: string | null | undefined): Date | null {
  if (!dateStr) return null
  const normalized = String(dateStr).trim()
  if (!normalized) return null
  if (/^\d{4}-\d{2}-\d{2}/.test(normalized)) {
    return new Date(normalized + (normalized.length === 10 ? 'T00:00:00+09:00' : ''))
  }
  const d = new Date(normalized)
  return isNaN(d.getTime()) ? null : d
}

/**
 * 日付をフォーマット（JST で解釈・表示、ロケールは引数で指定）
 * @param dateStr YYYY-MM-DD または ISO 文字列
 * @param locale 表示ロケール（例: 'ja-JP', 'en-US'）。未指定時は 'ja-JP'
 * @param options 追加の Intl オプション
 */
export function formatDateJST(
  dateStr: string | null | undefined,
  locale: string = 'ja-JP',
  options: Intl.DateTimeFormatOptions = {}
): string {
  const date = parseDateAsJST(dateStr)
  if (!date) return ''
  return date.toLocaleDateString(locale, {
    timeZone: JST_TIMEZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    ...options,
  })
}

/**
 * 日付を曜日付きでフォーマット（JST、ロケール対応）
 */
export function formatDateWithWeekdayJST(
  dateStr: string | null | undefined,
  locale: string = 'ja-JP'
): string {
  const date = parseDateAsJST(dateStr)
  if (!date) return ''
  return date.toLocaleDateString(locale, {
    timeZone: JST_TIMEZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    weekday: 'short',
  })
}

const JST_WEEKDAY_SHORT_TO_INDEX: Record<string, number> = {
  Sun: 0,
  Mon: 1,
  Tue: 2,
  Wed: 3,
  Thu: 4,
  Fri: 5,
  Sat: 6,
}

/** JST で曜日インデックス（0=日 … 6=土）を取得（ブラウザのローカル TZ に依存しない） */
export function getWeekdayIndexJST(dateStr: string | null | undefined): number {
  const date = parseDateAsJST(dateStr)
  if (!date) return -1
  const weekday = new Intl.DateTimeFormat('en-US', {
    timeZone: JST_TIMEZONE,
    weekday: 'short',
  })
    .formatToParts(date)
    .find((part) => part.type === 'weekday')?.value
  if (!weekday) return -1
  return JST_WEEKDAY_SHORT_TO_INDEX[weekday] ?? -1
}

/**
 * 日時をフォーマット（JST、ロケール対応）
 */
export function formatDateTimeJST(
  dateStr: string | Date | null | undefined,
  locale: string = 'ja-JP',
  options: Intl.DateTimeFormatOptions = {}
): string {
  if (dateStr == null) return ''
  const date = typeof dateStr === 'string' ? new Date(dateStr) : dateStr
  if (isNaN(date.getTime())) return ''
  return date.toLocaleString(locale, {
    timeZone: JST_TIMEZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: options.second ? '2-digit' : undefined,
    ...options,
  })
}

/** Date を JST 暦日で YYYY-MM-DD に変換 */
export function formatDateToYmdJST(date: Date): string {
  if (isNaN(date.getTime())) return ''
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: JST_TIMEZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
    .format(date)
    .replace(/\//g, '-')
}

/** YYYY-MM-DD に暦日で加算（JST、クライアント TZ に依存しない） */
export function shiftDateYmdJST(ymd: string, deltaDays: number): string {
  const base = (ymd ?? '').trim().slice(0, 10)
  if (!/^\d{4}-\d{2}-\d{2}$/.test(base)) return getJSTToday()
  const d = new Date(`${base}T12:00:00+09:00`)
  d.setDate(d.getDate() + deltaDays)
  return formatDateToYmdJST(d)
}

/** JST 曜日（0=日 … 6=土） */
export function getJSTDayOfWeek(ymdOrDate: string | Date): number {
  const d =
    typeof ymdOrDate === 'string'
      ? parseDateAsJST(ymdOrDate.slice(0, 10))
      : ymdOrDate
  if (!d || isNaN(d.getTime())) return 0
  const wd = new Intl.DateTimeFormat('en-US', {
    timeZone: JST_TIMEZONE,
    weekday: 'short',
  }).format(d)
  const map: Record<string, number> = {
    Sun: 0,
    Mon: 1,
    Tue: 2,
    Wed: 3,
    Thu: 4,
    Fri: 5,
    Sat: 6,
  }
  return map[wd] ?? 0
}

/** 翌平日（土日は翌月曜）— JST 暦日 */
export function nextWeekdayYmdJST(dateStr: string): string {
  let s = shiftDateYmdJST(dateStr, 1)
  let w = getJSTDayOfWeek(s)
  if (w === 0) s = shiftDateYmdJST(s, 1)
  else if (w === 6) s = shiftDateYmdJST(s, 2)
  return s
}

/** el-date-picker 用：JST 上で土日を無効化 */
export function isWeekendInJST(date: Date): boolean {
  const w = getJSTDayOfWeek(date)
  return w === 0 || w === 6
}

/** i18n の locale を Intl 用にマッピング（en -> en-US, ja -> ja-JP 等） */
export function localeForIntl(locale: string): string {
  const map: Record<string, string> = {
    ja: 'ja-JP',
    en: 'en-US',
    zh: 'zh-CN',
    vi: 'vi-VN',
  }
  return map[locale] || locale || 'ja-JP'
}
