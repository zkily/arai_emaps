/**
 * 自動車ニュースティッカー API
 */
import request from '@/shared/api/request'

const BASE = '/api/system'

export interface AutoNewsItem {
  id: string
  title: string
  url: string
  source: string
  publishedAt: string
}

export interface AutoNewsResponse {
  date: string
  items: AutoNewsItem[]
  isFallback: boolean
  cached: boolean
  fetchedAt: string
  enabled: boolean
}

/** 本日（JST）の日本自動車ニュース一覧 */
export function getAutoNews(limit = 20) {
  return request.get<AutoNewsResponse>(`${BASE}/auto-news`, { params: { limit } })
}
