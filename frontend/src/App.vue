<template>
  <div id="app">
    <el-config-provider :locale="elementLocale">
      <router-view />
    </el-config-provider>
  </div>
</template>

<script setup lang="ts">
import { computed, watch, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElConfigProvider } from 'element-plus'
import en from 'element-plus/dist/locale/en.js'
import ja from 'element-plus/dist/locale/ja.js'
import zhCn from 'element-plus/dist/locale/zh-cn.js'
import vi from 'element-plus/dist/locale/vi.js'
import dayjs from 'dayjs'
import { useUserStore } from '@/modules/auth/stores/user'
import type { LocaleType } from '@/i18n'

const { locale } = useI18n()
const dayjsLocaleMap: Record<string, string> = { en: 'en', ja: 'ja', zh: 'zh-cn', vi: 'vi' }
const elLocaleMap: Record<string, typeof ja> = { en, ja, zh: zhCn, vi }

const elementLocale = computed(() => elLocaleMap[locale.value as LocaleType] || ja)

watch(locale, (val) => {
  const dayjsLocale = dayjsLocaleMap[val as LocaleType]
  if (dayjsLocale) dayjs.locale(dayjsLocale)
}, { immediate: true })
import { getUserInfo } from '@/modules/auth/api'
import { ElMessage } from 'element-plus'
import { connectWebSocket, disconnectWebSocket } from '@/modules/websocket/utils'
import { startInactivityCheck, stopInactivityCheck } from '@/utils/inactivity'

const userStore = useUserStore()

// WebSocket接続とトークン検証
onMounted(async () => {
  console.log('Smart-EMAP システム起動')
  
  // ログインしている場合
  if (userStore.isAuthenticated) {
    // WebSocket接続を確立（リアルタイム通知用）
    connectWebSocket()
    
    // すぐにトークンの有効性をチェック
    // ページ読み込み時にすぐチェック
    try {
      console.log('[SINGLE_DEVICE] Checking token validity on page load...')
      await getUserInfo()
      console.log('[SINGLE_DEVICE] Token is valid')
      // 2 小时无操作自动登出，有操作则重置计时
      startInactivityCheck()
    } catch (error: any) {
      console.error('[SINGLE_DEVICE] Token check failed:', error)
      // 他のデバイスでログインされた場合
      if (error?.response?.status === 401) {
        const errorDetail = error?.response?.data?.detail || ''
        const isForceLogout = error?.response?.headers?.['x-force-logout'] === 'true'
        const isOtherDeviceLogin = errorDetail.includes('他のデバイス') ||
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
          ElMessage.error('トークンの有効期限が切れました。再度ログインしてください。')
          userStore.clearLocalSession()
          window.location.href = '/login'
        }
        return
      }
    }
    
    // フォールバック：60秒ごとにトークンの有効性をチェック（WebSocketが失敗した場合のバックアップ）
    // WebSocketが正常に動作している場合は、このチェックは主に接続確認のため
    let checkInterval: number | null = null
    
    const startFallbackCheck = () => {
      if (checkInterval) return
      
      checkInterval = window.setInterval(async () => {
        // ページが非表示の場合はスキップ
        if (document.hidden || !userStore.isAuthenticated) {
          return
        }
        
        try {
          // /api/auth/me を呼び出してトークンの有効性をチェック
          await getUserInfo()
        } catch (error: any) {
          // 他のデバイスでログインされた場合（WebSocketが失敗した場合のフォールバック）
          if (error?.response?.status === 401) {
            const errorDetail = error?.response?.data?.detail || ''
            const isForceLogout = error?.response?.headers?.['x-force-logout'] === 'true'
            const isOtherDeviceLogin = errorDetail.includes('他のデバイス') || 
                                       errorDetail.includes('他のデバイスでログイン') ||
                                       isForceLogout
            
            if (isOtherDeviceLogin) {
              if (checkInterval) {
                clearInterval(checkInterval)
                checkInterval = null
              }
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
              if (checkInterval) {
                clearInterval(checkInterval)
                checkInterval = null
              }
              ElMessage.error('トークンの有効期限が切れました。再度ログインしてください。')
              userStore.clearLocalSession()
              window.location.href = '/login'
            }
          }
        }
      }, 60 * 1000) // 60秒ごと（WebSocketのフォールバック）
    }
    
    // ページの可視性変更を監視
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // ページが非表示になったらチェックを停止
        if (checkInterval) {
          clearInterval(checkInterval)
          checkInterval = null
        }
      } else {
        // ページが表示されたらチェックを開始
        startFallbackCheck()
        // WebSocket接続を再確立
        if (userStore.isAuthenticated) {
          connectWebSocket()
        }
      }
    }
    
    document.addEventListener('visibilitychange', handleVisibilityChange)
    
    // 初期チェックを開始
    startFallbackCheck()
    
    // コンポーネントがアンマウントされたときにクリア
    return () => {
      if (checkInterval) {
        clearInterval(checkInterval)
        checkInterval = null
      }
      disconnectWebSocket()
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }
})

onUnmounted(() => {
  stopInactivityCheck()
  disconnectWebSocket()
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  font-family: 'Yu Gothic', '游ゴシック', 'YuGothic', 'Meiryo', 'Hiragino Sans', sans-serif;
}

html,
body,
#app {
  height: 100%;
  font-family: 'Yu Gothic', '游ゴシック', 'YuGothic', 'Meiryo', 'Hiragino Sans', sans-serif;
}

#app {
  background-color: #f0f2f5;
}
</style>

