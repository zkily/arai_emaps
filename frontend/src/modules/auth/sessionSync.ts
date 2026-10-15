/**
 * 同一ブラウザ内の別タブへログイン状態を受け渡す。
 * rememberMe 未使用時は sessionStorage がタブ単位のため、新しいタブはここから復元する。
 * 他デバイスログイン時は FORCE_LOGOUT で全タブへ通知する。
 */

const CHANNEL_NAME = 'smart_emap_session'
const HANDOFF_KEY = 'smart_emap_tab_handoff'
const HANDOFF_TTL_MS = 15000
const REQUEST_TIMEOUT_MS = 800

/** ドラッグや修飾クリックで新規タブを開く直前に印を付ける（referrer が無い場合の手がかり） */
export function markMenuTabHandoff() {
  try {
    localStorage.setItem(HANDOFF_KEY, String(Date.now()))
  } catch {
    /* ignore */
  }
}

export function clearMenuTabHandoff() {
  try {
    localStorage.removeItem(HANDOFF_KEY)
  } catch {
    /* ignore */
  }
}

function consumeRecentMenuTabHandoff(): boolean {
  try {
    const raw = localStorage.getItem(HANDOFF_KEY)
    if (!raw) return false
    localStorage.removeItem(HANDOFF_KEY)
    const at = Number(raw)
    return Number.isFinite(at) && Date.now() - at < HANDOFF_TTL_MS
  } catch {
    return false
  }
}

export interface CrossTabSession {
  token: string
  user: unknown
  rememberMe: boolean
}

interface SessionHandlers {
  getSession: () => CrossTabSession | null
  applySession: (session: CrossTabSession) => void
  /** 他タブでの通常ログアウト */
  clearSession: () => void
  /** 他デバイスログインによる強制ログアウト */
  forceLogout: (message: string) => void
}

type RequestMessage = { type: 'REQUEST_SESSION'; requestId: string }
type SessionMessage = {
  type: 'SESSION'
  requestId: string
  token: string
  user: unknown
  rememberMe?: boolean
}
type ClearMessage = { type: 'CLEAR_SESSION' }
type ForceLogoutMessage = { type: 'FORCE_LOGOUT'; message: string }
type ChannelMessage = RequestMessage | SessionMessage | ClearMessage | ForceLogoutMessage

let channel: BroadcastChannel | null = null
let handlers: SessionHandlers | null = null
let applyingRemote = false
let inflight: Promise<void> | null = null
let attempted = false

function mayHavePeerSession(): boolean {
  if (typeof window === 'undefined') return false
  const handoff = consumeRecentMenuTabHandoff()
  return handoff || !!window.opener
}

function isChannelMessage(data: unknown): data is ChannelMessage {
  if (!data || typeof data !== 'object') return false
  const type = (data as { type?: unknown }).type
  return (
    type === 'REQUEST_SESSION' ||
    type === 'SESSION' ||
    type === 'CLEAR_SESSION' ||
    type === 'FORCE_LOGOUT'
  )
}

function onChannelMessage(event: MessageEvent) {
  if (!handlers || !channel || !isChannelMessage(event.data)) return
  const data = event.data

  if (data.type === 'REQUEST_SESSION') {
    const session = handlers.getSession()
    if (!session) return
    channel.postMessage({
      type: 'SESSION',
      requestId: data.requestId,
      token: session.token,
      user: session.user,
      rememberMe: session.rememberMe,
    } satisfies SessionMessage)
    return
  }

  if (data.type === 'CLEAR_SESSION') {
    if (applyingRemote) return
    applyingRemote = true
    try {
      handlers.clearSession()
    } finally {
      applyingRemote = false
    }
    return
  }

  if (data.type === 'FORCE_LOGOUT') {
    if (applyingRemote) return
    applyingRemote = true
    try {
      handlers.forceLogout(
        typeof data.message === 'string' && data.message
          ? data.message
          : 'このアカウントは他のデバイスでログインされています。再度ログインしてください。',
      )
    } finally {
      applyingRemote = false
    }
  }
}

export function startSessionSync(nextHandlers: SessionHandlers) {
  handlers = nextHandlers
  if (channel || typeof BroadcastChannel === 'undefined') return
  channel = new BroadcastChannel(CHANNEL_NAME)
  channel.addEventListener('message', onChannelMessage)
}

export function broadcastClearSession() {
  if (applyingRemote || !channel) return
  channel.postMessage({ type: 'CLEAR_SESSION' } satisfies ClearMessage)
}

export function broadcastForceLogout(message: string) {
  if (applyingRemote || !channel) return
  channel.postMessage({ type: 'FORCE_LOGOUT', message } satisfies ForceLogoutMessage)
}

function requestSessionFromPeers(): Promise<void> {
  return new Promise((resolve) => {
    if (!channel || !handlers) {
      resolve()
      return
    }

    const requestId = `${Date.now()}-${Math.random().toString(36).slice(2)}`
    let settled = false

    const finish = () => {
      if (settled) return
      settled = true
      window.clearTimeout(timer)
      channel?.removeEventListener('message', onReply)
      resolve()
    }

    const onReply = (event: MessageEvent) => {
      if (!isChannelMessage(event.data) || event.data.type !== 'SESSION') return
      if (event.data.requestId !== requestId) return
      if (typeof event.data.token !== 'string' || !event.data.token) return
      if (!event.data.user || typeof event.data.user !== 'object') return
      handlers?.applySession({
        token: event.data.token,
        user: event.data.user,
        rememberMe: event.data.rememberMe === true,
      })
      finish()
    }

    const timer = window.setTimeout(finish, REQUEST_TIMEOUT_MS)
    channel.addEventListener('message', onReply)
    channel.postMessage({ type: 'REQUEST_SESSION', requestId } satisfies RequestMessage)
  })
}

/** ローカルにセッションが無いときだけ、開いているタブへ問い合わせる */
export function ensureCrossTabSession(): Promise<void> {
  if (handlers?.getSession()) return Promise.resolve()
  if (inflight) return inflight
  if (attempted || !mayHavePeerSession()) {
    attempted = true
    return Promise.resolve()
  }
  attempted = true
  inflight = requestSessionFromPeers().finally(() => {
    inflight = null
  })
  return inflight
}
