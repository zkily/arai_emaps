import { computed, toValue, type MaybeRefOrGetter } from 'vue'
import { useRouter, type RouteLocationRaw, type Router } from 'vue-router'
import { markMenuTabHandoff } from '@/modules/auth/sessionSync'

/** タブバーへドラッグできる絶対 URL */
export function toMenuAbsoluteHref(router: Router, to: RouteLocationRaw): string {
  if (!to) return ''
  if (typeof to === 'string' && !to) return ''
  const resolved = router.resolve(to)
  if (typeof window === 'undefined') return resolved.href
  return new URL(resolved.href, window.location.origin).href
}

export function useMenuHref(path: MaybeRefOrGetter<string | null | undefined>) {
  const router = useRouter()
  const href = computed(() => toMenuAbsoluteHref(router, toValue(path) || ''))
  return { href }
}

/** 通常左クリックは SPA 遷移のまま。修飾クリック・中クリックはブラウザに任せる */
export function onMenuLinkClick(event: MouseEvent) {
  const openInBrowser =
    event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0
  if (openInBrowser) {
    markMenuTabHandoff()
    event.stopPropagation()
    return
  }
  event.preventDefault()
}

export function onMenuLinkDragStart(event: DragEvent, href: string) {
  if (!href || !event.dataTransfer) return
  markMenuTabHandoff()
  event.dataTransfer.setData('text/uri-list', href)
  event.dataTransfer.setData('text/plain', href)
  event.dataTransfer.effectAllowed = 'copyLink'
  event.stopPropagation()
}
