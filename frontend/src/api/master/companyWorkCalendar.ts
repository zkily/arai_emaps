import request from '@/utils/request'

export interface CompanyWorkCalendarItem {
  id: number
  calendar_date: string
  day_type: string
  day_type_label?: string
  is_scheduled: boolean
  name?: string | null
  note?: string | null
}

export interface CompanyWorkCalendarListData {
  start_date: string
  end_date: string
  items: CompanyWorkCalendarItem[]
  scheduled_workday_count: number
  total_days: number
}

export interface CompanyWorkCalendarDayType {
  value: string
  label: string
}

export function fetchCompanyWorkCalendarDayTypes(): Promise<CompanyWorkCalendarDayType[]> {
  return request.get('/api/master/company-work-calendar/day-types') as Promise<CompanyWorkCalendarDayType[]>
}

export function fetchCompanyWorkCalendar(params: {
  start_date: string
  end_date: string
}): Promise<{ success?: boolean; data?: CompanyWorkCalendarListData }> {
  return request.get('/api/master/company-work-calendar', { params }) as Promise<{
    success?: boolean
    data?: CompanyWorkCalendarListData
  }>
}

export function createCompanyWorkCalendarEntry(body: {
  calendar_date: string
  day_type?: string
  is_scheduled?: boolean
  name?: string
  note?: string
}): Promise<{ success?: boolean; data?: CompanyWorkCalendarItem }> {
  return request.post('/api/master/company-work-calendar', body) as Promise<{
    success?: boolean
    data?: CompanyWorkCalendarItem
  }>
}

export function batchCreateCompanyWorkCalendar(body: {
  dates: string[]
  day_type: string
  is_scheduled?: boolean
  name?: string
  note?: string
}): Promise<{ success?: boolean; created?: number; skipped?: number }> {
  return request.post('/api/master/company-work-calendar/batch', body) as Promise<{
    success?: boolean
    created?: number
    skipped?: number
  }>
}

export function deleteCompanyWorkCalendarEntry(id: number): Promise<{ success?: boolean; message?: string }> {
  return request.delete(`/api/master/company-work-calendar/${id}`) as Promise<{ success?: boolean; message?: string }>
}

export function resolveCompanyWorkdays(params: {
  start_date: string
  end_date: string
  extra_workdays?: string
  extra_holidays?: string
}): Promise<{
  success?: boolean
  data?: {
    scheduled_workday_count: number
    company_extra_workdays: string[]
    company_holidays: string[]
  }
}> {
  return request.get('/api/master/company-work-calendar/resolve', { params }) as Promise<{
    success?: boolean
    data?: {
      scheduled_workday_count: number
      company_extra_workdays: string[]
      company_holidays: string[]
    }
  }>
}

/** YYYY-MM → 当月起止日 */
export function yearMonthDateRange(ym: string): { start_date: string; end_date: string } | null {
  const trimmed = ym.trim()
  if (!/^\d{4}-\d{2}$/.test(trimmed)) return null
  const [y, m] = trimmed.split('-').map(Number)
  const lastDay = new Date(y, m, 0).getDate()
  const mm = String(m).padStart(2, '0')
  return {
    start_date: `${y}-${mm}-01`,
    end_date: `${y}-${mm}-${String(lastDay).padStart(2, '0')}`,
  }
}

/** 月〜金のみ（API 失敗時のフォールバック） */
export function calcWeekdayFallbackForMonth(ym: string): number {
  const range = yearMonthDateRange(ym)
  if (!range) return 20
  const [y, m] = range.start_date.split('-').map(Number)
  const daysInMonth = new Date(y, m, 0).getDate()
  let count = 0
  for (let d = 1; d <= daysInMonth; d++) {
    const dow = new Date(y, m - 1, d).getDay()
    if (dow !== 0 && dow !== 6) count++
  }
  return Math.max(1, count)
}

/** 会社稼働カレンダーに基づく月間稼働日数（生産計画向け） */
export async function fetchScheduledWorkdaysForMonth(ym: string): Promise<number> {
  const fallback = calcWeekdayFallbackForMonth(ym)
  const range = yearMonthDateRange(ym)
  if (!range) return fallback
  try {
    const res = await fetchCompanyWorkCalendar(range)
    const count = res?.data?.scheduled_workday_count
    if (typeof count === 'number' && count >= 1) return count
  } catch {
    /* API 失敗時は月〜金 */
  }
  return fallback
}

/** ISO 日付が属する月の稼働日数 */
export async function fetchScheduledWorkdaysForDateIso(dateIso: string): Promise<number> {
  const date = (dateIso || '').trim().slice(0, 10)
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) return 20
  return fetchScheduledWorkdaysForMonth(date.slice(0, 7))
}
