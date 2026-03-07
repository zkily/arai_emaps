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
