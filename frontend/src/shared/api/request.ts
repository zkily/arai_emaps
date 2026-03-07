import axios, { AxiosInstance, AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/modules/auth/stores/user'
import { touchActivity } from '@/utils/inactivity'

// APIベースURLの取得
// 開発: 相対パスでViteプロキシ経由。本番: api-config.js で直叩きURLがあればそれを使用（高速）
function getBaseURL(): string {
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL
  }
  if (import.meta.env.DEV) {
    return ''
  }
  // 本番で /api-config.js 注入時は直叩き（プロキシ経由より速い）
  if (typeof window !== 'undefined' && (window as unknown as { __API_BASE__?: string }).__API_BASE__) {
    return (window as unknown as { __API_BASE__: string }).__API_BASE__
  }
  return ''
}

const baseURL = getBaseURL()

/** JWT の exp（秒）を取得。無効なら null */
function getTokenExp(token: string): number | null {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return typeof payload.exp === 'number' ? payload.exp : null
  } catch {
    return null
  }
}

/** トークンが期限切れなら true（余裕 0 秒） */
function isTokenExpired(token: string): boolean {
  const exp = getTokenExp(token)
  if (exp == null) return true
  return Math.floor(Date.now() / 1000) >= exp
}

// Axiosインスタンスの作成
const service: AxiosInstance = axios.create({
  baseURL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// リクエストインターセプター
service.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    const token = userStore.token
    if (token) {
      if (isTokenExpired(token)) {
        ElMessage.error('トークンの有効期限が切れました。再度ログインしてください。')
        userStore.clearLocalSession()
        window.location.href = '/login'
        return Promise.reject(new Error('Token expired'))
      }
      touchActivity() // 每次 API 请求视为操作，重置无操作计时
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    console.error('リクエストエラー:', error)
    return Promise.reject(error)
  }
)

// レスポンスインターセプター
service.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      const currentPath = window.location.pathname
      const isLoginPage = currentPath === '/login' || currentPath === '/'
      
      // ログインページでは、エラーメッセージを表示しない（Login.vueで処理するため）
      if (isLoginPage) {
        // エラーをそのまま返す（Login.vueで処理）
        return Promise.reject(error)
      }
      
      // ログインページ以外でのエラー処理
      const errorMessage = data?.detail || data?.message || 'エラーが発生しました。'
      
      switch (status) {
        case 401: {
          // トークン期限切れ・他デバイスログイン時はローカルのみクリアしてログインへ（API を呼ばない）
          const userStore = useUserStore()
          const isForceLogout = error.response?.headers?.['x-force-logout'] === 'true'
          const errorDetail = (data?.detail ?? '') as string
          const isOtherDeviceLogin =
            errorDetail.includes('他のデバイス') ||
            errorDetail.includes('他のデバイスでログイン') ||
            isForceLogout

          if (isOtherDeviceLogin) {
            ElMessage.error({
              message: 'このアカウントは他のデバイスでログインされています。再度ログインしてください。',
              duration: 3000,
              showClose: true,
            })
            setTimeout(() => {
              userStore.clearLocalSession()
              window.location.href = '/login'
            }, 1500)
          } else {
            // トークン期限切れまたは認証エラー → 自動でログアウトしてログインへ
            ElMessage.error('トークンの有効期限が切れました。再度ログインしてください。')
            userStore.clearLocalSession()
            window.location.href = '/login'
          }
          break
        }
        case 403:
          ElMessage.error(errorMessage || 'アクセス権限がありません。')
          break
        case 404:
          ElMessage.error(errorMessage || 'リソースが見つかりません。')
          break
        case 500:
          // 500 は呼び出し元の catch でメッセージ表示するため、ここでは表示しない（二重表示を防ぐ）
          break
        default:
          ElMessage.error(errorMessage)
      }
    } else {
      // ネットワークエラーの場合も、ログインページでは表示しない
      const currentPath = window.location.pathname
      const isLoginPage = currentPath === '/login' || currentPath === '/'
      if (!isLoginPage) {
        ElMessage.error('ネットワークエラーが発生しました。サーバーに接続できません。')
      }
    }
    return Promise.reject(error)
  }
)

export default service

