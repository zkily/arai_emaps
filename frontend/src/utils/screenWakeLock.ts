/**
 * Screen Wake Lock API：検査・MES 作業中の画面消灯・省電力スリープを抑止
 * @see https://developer.mozilla.org/en-US/docs/Web/API/Screen_Wake_Lock_API
 */

let wakeLock: WakeLockSentinel | null = null
let wantActive = false
let visibilityHandler: (() => void) | null = null

export function isScreenWakeLockSupported(): boolean {
  return typeof navigator !== 'undefined' && 'wakeLock' in navigator
}

export async function requestScreenWakeLock(): Promise<boolean> {
  if (!isScreenWakeLockSupported() || typeof document === 'undefined') return false
  if (document.visibilityState !== 'visible') return false
  wantActive = true
  try {
    if (wakeLock && !wakeLock.released) return true
    wakeLock = await navigator.wakeLock.request('screen')
    wakeLock.addEventListener('release', () => {
      wakeLock = null
      if (wantActive && document.visibilityState === 'visible') {
        void requestScreenWakeLock()
      }
    })
    return true
  } catch {
    wakeLock = null
    return false
  }
}

export async function releaseScreenWakeLock(): Promise<void> {
  wantActive = false
  const lock = wakeLock
  wakeLock = null
  if (!lock || lock.released) return
  try {
    await lock.release()
  } catch {
    /* ignore */
  }
}

/** wantActive に応じて Wake Lock を取得／解放 */
export async function syncScreenWakeLock(active: boolean): Promise<void> {
  if (active) await requestScreenWakeLock()
  else await releaseScreenWakeLock()
}

/** タブ復帰時に再取得（OS が hidden 時にロックを解放するため） */
export function bindScreenWakeLockVisibilityRecovery(): void {
  if (visibilityHandler != null || typeof document === 'undefined') return
  visibilityHandler = () => {
    if (document.visibilityState === 'visible' && wantActive) {
      void requestScreenWakeLock()
    }
  }
  document.addEventListener('visibilitychange', visibilityHandler)
}

export function unbindScreenWakeLockVisibilityRecovery(): void {
  if (visibilityHandler == null || typeof document === 'undefined') return
  document.removeEventListener('visibilitychange', visibilityHandler)
  visibilityHandler = null
}
