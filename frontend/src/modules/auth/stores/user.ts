import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { disconnectWebSocket } from '@/modules/websocket/utils'
import * as authApi from '@/modules/auth/api'

export interface User {
  id: number
  username: string
  email: string
  full_name?: string
  role: string
  permissions: string[]
  is_active?: boolean
  department_id?: number | null
}

// ストレージキー
const TOKEN_KEY = 'smart_emap_token'
const USER_KEY = 'smart_emap_user'
const REMEMBER_ME_KEY = 'smart_emap_remember_me'

// ストレージの取得（rememberMeに基づいてlocalStorageまたはsessionStorageを使用）
const getStorage = () => {
  const rememberMe = localStorage.getItem(REMEMBER_ME_KEY) === 'true'
  return rememberMe ? localStorage : sessionStorage
}

export const useUserStore = defineStore(
  'user',
  () => {
    const user = ref<User | null>(null)
    const token = ref<string>('')

    // 認証状態を計算プロパティとして定義
    const isAuthenticated = computed(() => {
      return !!(token.value && user.value)
    })

    // 初期化時にストレージから復元
    const initFromStorage = () => {
      // まず localStorage をチェック（rememberMe が true の場合）
      let storage = localStorage
      let savedToken = storage.getItem(TOKEN_KEY)
      let savedUser = storage.getItem(USER_KEY)
      
      // localStorage にない場合、sessionStorage をチェック
      if (!savedToken || !savedUser) {
        storage = sessionStorage
        savedToken = savedToken || storage.getItem(TOKEN_KEY)
        savedUser = savedUser || storage.getItem(USER_KEY)
      }
      
      if (savedToken) {
        token.value = savedToken
      }
      
      if (savedUser) {
        try {
          user.value = JSON.parse(savedUser)
        } catch (e) {
          console.error('ユーザー情報の復元に失敗しました:', e)
          user.value = null
          token.value = ''
        }
      }
    }

    const setUser = (userData: User, rememberMe: boolean = false) => {
      user.value = userData
      const storage = rememberMe ? localStorage : sessionStorage
      
      // ユーザー情報を保存
      storage.setItem(USER_KEY, JSON.stringify(userData))
      
      // rememberMeフラグを保存
      if (rememberMe) {
        localStorage.setItem(REMEMBER_ME_KEY, 'true')
      } else {
        localStorage.removeItem(REMEMBER_ME_KEY)
        // sessionStorageの場合は、localStorageからも削除
        if (localStorage.getItem(REMEMBER_ME_KEY)) {
          localStorage.removeItem(REMEMBER_ME_KEY)
        }
      }
    }

    const setToken = (tokenValue: string, rememberMe: boolean = false) => {
      token.value = tokenValue
      const storage = rememberMe ? localStorage : sessionStorage
      storage.setItem(TOKEN_KEY, tokenValue)
    }

    /** ローカルのみクリア（API を呼ばない）。401 / トークン期限切れ時に使用 */
    const clearLocalSession = () => {
      user.value = null
      token.value = ''
      try {
        disconnectWebSocket()
      } catch {
        /* ignore */
      }
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
      localStorage.removeItem(REMEMBER_ME_KEY)
      sessionStorage.removeItem(TOKEN_KEY)
      sessionStorage.removeItem(USER_KEY)
    }

    const logout = async () => {
      // 先にバックエンドのログアウトAPIを呼び、last_login_token をクリアする（現在のトークンで識別）
      try {
        if (token.value) {
          await authApi.logout()
        }
      } catch {
        // ネットワークエラーやトークン失効時もローカルはクリアする
      }
      clearLocalSession()
    }

    const hasPermission = (permission: string): boolean => {
      return user.value?.permissions.includes(permission) ?? false
    }

    // 初期化
    initFromStorage()

    return {
      user,
      token,
      isAuthenticated,
      setUser,
      setToken,
      logout,
      clearLocalSession,
      hasPermission,
      initFromStorage,
    }
  }
)

