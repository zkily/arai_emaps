import request from '@/shared/api/request'
import { useUserStore } from '@/modules/auth/stores/user'

export interface AiChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
}

export interface AiHealthResponse {
  status: string
  enabled: boolean
  ollama_url?: string
  model?: string
  model_ready: boolean
  models_available?: string[]
  error?: string
}

function getApiBase(): string {
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL
  }
  if (import.meta.env.DEV) {
    return ''
  }
  if (typeof window !== 'undefined' && (window as unknown as { __API_BASE__?: string }).__API_BASE__) {
    return (window as unknown as { __API_BASE__: string }).__API_BASE__
  }
  return ''
}

export function getAiHealth(): Promise<AiHealthResponse> {
  return request.get('/api/ai/health') as Promise<AiHealthResponse>
}

export async function streamChat(
  messages: AiChatMessage[],
  handlers: {
    onToken: (token: string) => void
    onStatus?: (status: string) => void
    onDone?: () => void
    onError?: (message: string) => void
  },
  signal?: AbortSignal,
): Promise<void> {
  const userStore = useUserStore()
  const token = userStore.token
  const base = getApiBase()
  const url = `${base}/api/ai/chat/stream`

  const resp = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ messages }),
    signal,
  })

  if (!resp.ok) {
    let detail = resp.statusText
    try {
      const errBody = await resp.json()
      detail = errBody?.detail || detail
    } catch {
      /* ignore */
    }
    handlers.onError?.(detail || 'Request failed')
    return
  }

  const reader = resp.body?.getReader()
  if (!reader) {
    handlers.onError?.('No response body')
    return
  }

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const parts = buffer.split('\n\n')
    buffer = parts.pop() || ''

    for (const part of parts) {
      const line = part.trim()
      if (!line.startsWith('data:')) continue
      const jsonStr = line.slice(5).trim()
      if (!jsonStr) continue
      try {
        const evt = JSON.parse(jsonStr) as { type: string; content?: string }
        if (evt.type === 'token' && evt.content) {
          handlers.onToken(evt.content)
        } else if (evt.type === 'status' && evt.content) {
          handlers.onStatus?.(evt.content)
        } else if (evt.type === 'error' && evt.content) {
          handlers.onError?.(evt.content)
        } else if (evt.type === 'done') {
          handlers.onDone?.()
        }
      } catch {
        /* skip malformed chunk */
      }
    }
  }

  handlers.onDone?.()
}
