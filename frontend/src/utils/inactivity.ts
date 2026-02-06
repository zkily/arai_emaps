/**
 * 无操作超时：超过指定时间无操作则自动登出，有操作则重置计时（滑动窗口）
 */
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/modules/auth/stores/user'

/** 无操作超时时间：2 小时 */
const INACTIVITY_TIMEOUT_MS = 2 * 60 * 60 * 1000

/** 检查间隔：1 分钟 */
const CHECK_INTERVAL_MS = 60 * 1000

/** 最后一次活动时间（任何操作或 API 请求会更新） */
let lastActivityAt = 0

let checkTimer: ReturnType<typeof setInterval> | null = null
let boundTouch: () => void

const events = ['mousedown', 'mousemove', 'keydown', 'scroll', 'touchstart', 'click']

/** 记录一次活动，重置无操作计时 */
export function touchActivity(): void {
  lastActivityAt = Date.now()
}

/** 开始无操作检测（仅登录后调用） */
export function startInactivityCheck(): void {
  touchActivity()
  if (checkTimer != null) return

  boundTouch = () => touchActivity()
  events.forEach((ev) => window.addEventListener(ev, boundTouch, { passive: true }))

  checkTimer = window.setInterval(() => {
    const userStore = useUserStore()
    if (!userStore.isAuthenticated) {
      stopInactivityCheck()
      return
    }
    // 标签页不可见时不登出，等用户回到页面再判断
    if (document.hidden) return
    if (Date.now() - lastActivityAt >= INACTIVITY_TIMEOUT_MS) {
      stopInactivityCheck()
      ElMessage.warning('2時間操作がありませんでした。セキュリティのためログアウトします。')
      userStore.clearLocalSession()
      window.location.href = '/login'
    }
  }, CHECK_INTERVAL_MS)
}

/** 停止无操作检测（登出或页面卸载时调用） */
export function stopInactivityCheck(): void {
  if (checkTimer != null) {
    clearInterval(checkTimer)
    checkTimer = null
  }
  if (typeof boundTouch === 'function') {
    events.forEach((ev) => window.removeEventListener(ev, boundTouch))
  }
}
