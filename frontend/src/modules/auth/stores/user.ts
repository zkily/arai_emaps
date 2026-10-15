import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { disconnectWebSocket } from '@/modules/websocket/utils'
import * as authApi from '@/modules/auth/api'
import {
  broadcastClearSession,
  broadcastForceLogout,
  clearMenuTabHandoff,
  ensureCrossTabSession,
  startSessionSync,
} from '@/modules/auth/sessionSync'
import { useSidebarShortcutsStore } from '@/stores/sidebarShortcuts'

export interface OperationPermission {
  module: string
  can_create: boolean
  can_edit: boolean
  can_delete: boolean
  can_export: boolean
  can_approve: boolean
}

export interface User {
  id: number
  username: string
  email: string
  full_name?: string
  role: string
  role_name?: string | null
  permissions: string[]
  menu_codes?: string[]
  operation_permissions?: OperationPermission[]
  is_super_admin?: boolean
  data_scope?: string
  is_active?: boolean
  department_id?: number | null
  department_name?: string | null
}

// ストレージキー
const TOKEN_KEY = 'smart_emap_token'
const USER_KEY = 'smart_emap_user'
const REMEMBER_ME_KEY = 'smart_emap_remember_me'

const OTHER_DEVICE_LOGOUT_MESSAGE =
  'このアカウントは他のデバイスでログインされています。再度ログインしてください。'

export const useUserStore = defineStore(
  'user',
  () => {
    const user = ref<User | null>(null)
    const token = ref<string>('')
    let authExitInProgress = false

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
          if (savedToken) {
            void useSidebarShortcutsStore().load()
          }
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

      void useSidebarShortcutsStore().load()
    }

    const setToken = (tokenValue: string, rememberMe: boolean = false) => {
      token.value = tokenValue
      const storage = rememberMe ? localStorage : sessionStorage
      storage.setItem(TOKEN_KEY, tokenValue)
    }

    /** ストレージ・メモリのみクリア（Broadcast しない） */
    const wipeLocalAuth = () => {
      user.value = null
      token.value = ''
      useSidebarShortcutsStore().reset()
      try {
        disconnectWebSocket()
      } catch {
        /* ignore */
      }
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
      sessionStorage.removeItem(TOKEN_KEY)
      sessionStorage.removeItem(USER_KEY)
      clearMenuTabHandoff()
    }

    /** ローカルのみクリア（API を呼ばない）。401 / トークン期限切れ時に使用 */
    const clearLocalSession = () => {
      wipeLocalAuth()
      broadcastClearSession()
    }

    const goLoginSoon = (delayMs = 1500) => {
      window.setTimeout(() => {
        window.location.href = '/login'
      }, delayMs)
    }

    /**
     * 他デバイスでログインされたとき：提示 → 全タブへ通知 → セッション破棄 → ログインへ
     */
    const forceLogoutOtherDevice = (message?: string) => {
      if (authExitInProgress) return
      authExitInProgress = true
      const msg =
        typeof message === 'string' && message.trim()
          ? message.trim()
          : OTHER_DEVICE_LOGOUT_MESSAGE
      ElMessage.error({
        message: msg,
        duration: 5000,
        showClose: true,
      })
      broadcastForceLogout(msg)
      wipeLocalAuth()
      goLoginSoon(1500)
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

    const refreshUser = async () => {
      const data = await authApi.getUserInfo()
      const rememberMe = localStorage.getItem(REMEMBER_ME_KEY) === 'true'
      setUser(data, rememberMe)
      return data
    }

    // 初期化
    initFromStorage()
    startSessionSync({
      getSession: () => {
        if (!token.value || !user.value) return null
        return {
          token: token.value,
          user: JSON.parse(JSON.stringify(user.value)) as User,
          rememberMe: localStorage.getItem(REMEMBER_ME_KEY) === 'true',
        }
      },
      applySession: ({ token: tokenValue, user: userData, rememberMe }) => {
        setToken(tokenValue, rememberMe)
        setUser(userData as User, rememberMe)
      },
      clearSession: () => {
        if (authExitInProgress) return
        authExitInProgress = true
        wipeLocalAuth()
        window.location.href = '/login'
      },
      forceLogout: (message) => {
        if (authExitInProgress) return
        authExitInProgress = true
        ElMessage.error({
          message: message || OTHER_DEVICE_LOGOUT_MESSAGE,
          duration: 5000,
          showClose: true,
        })
        wipeLocalAuth()
        goLoginSoon(1500)
      },
    })

    return {
      user,
      token,
      isAuthenticated,
      setUser,
      setToken,
      logout,
      clearLocalSession,
      forceLogoutOtherDevice,
      hasPermission,
      refreshUser,
      initFromStorage,
      ensureCrossTabSession,
    }
  }
)
