/**
 * WebSocket 工具类
 * 用于实时通信，包括单设备登录检测
 */
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

let ws: WebSocket | null = null
let reconnectTimer: number | null = null
let reconnectAttempts = 0
const maxReconnectAttempts = 5
const reconnectDelay = 3000 // 3秒

/**
 * WebSocket接続を確立
 */
export function connectWebSocket() {
  const userStore = useUserStore()
  
  // トークンがない場合は接続しない
  if (!userStore.token) {
    return
  }
  
  // 既に接続されている場合はスキップ
  if (ws && ws.readyState === WebSocket.OPEN) {
    return
  }
  
  // WebSocket URLを構築
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  const wsUrl = `${protocol}//${host}/ws?token=${encodeURIComponent(userStore.token)}`
  
  console.log('[WebSocket] Connecting to:', wsUrl.replace(userStore.token, 'token=***'))
  
  try {
    ws = new WebSocket(wsUrl)
    
    ws.onopen = () => {
      console.log('[WebSocket] Connected')
      reconnectAttempts = 0
    }
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        handleWebSocketMessage(data)
      } catch (e) {
        console.error('[WebSocket] Failed to parse message:', e)
      }
    }
    
    ws.onerror = (error) => {
      console.error('[WebSocket] Error:', error)
    }
    
    ws.onclose = () => {
      console.log('[WebSocket] Disconnected')
      ws = null
      
      // 自動再接続（ログイン中の場合のみ）
      if (userStore.isAuthenticated && reconnectAttempts < maxReconnectAttempts) {
        reconnectAttempts++
        console.log(`[WebSocket] Reconnecting in ${reconnectDelay}ms (attempt ${reconnectAttempts}/${maxReconnectAttempts})...`)
        reconnectTimer = window.setTimeout(() => {
          connectWebSocket()
        }, reconnectDelay)
      }
    }
  } catch (error) {
    console.error('[WebSocket] Connection failed:', error)
  }
}

/**
 * WebSocketメッセージを処理
 */
function handleWebSocketMessage(data: any) {
  console.log('[WebSocket] Received message:', data)
  
  switch (data.type) {
    case 'connected':
      console.log('[WebSocket]', data.message)
      break
      
    case 'force_logout':
      // 他のデバイスでログインされた場合
      console.warn('[WebSocket] Force logout:', data.message)
      
      // エラーメッセージを表示（長めの表示時間でユーザーに確認してもらう）
      ElMessage.error({
        message: data.message || 'このアカウントは他のデバイスでログインされています。再度ログインしてください。',
        duration: 3000,
        showClose: true,
      })
      
      setTimeout(() => {
        const userStore = useUserStore()
        userStore.clearLocalSession()
        window.location.href = '/login'
      }, 1500)
      break
      
    case 'pong':
      // 接続維持の応答
      break
      
    default:
      console.log('[WebSocket] Unknown message type:', data.type)
  }
}

/**
 * WebSocket接続を切断
 */
export function disconnectWebSocket() {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
  
  if (ws) {
    ws.close()
    ws = null
  }
  
  reconnectAttempts = 0
  console.log('[WebSocket] Disconnected')
}

/**
 * WebSocket接続状態を取得
 */
export function isWebSocketConnected(): boolean {
  return ws !== null && ws.readyState === WebSocket.OPEN
}

