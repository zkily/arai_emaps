import { onMounted } from 'vue'

/**
 * Safe wrapper for onMounted that catches errors
 */
export function safeOnMounted(fn: () => void | Promise<void>) {
  onMounted(async () => {
    try {
      await fn()
    } catch (e) {
      console.error('[safeOnMounted] Error:', e)
    }
  })
}
