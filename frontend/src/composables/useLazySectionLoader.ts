import { onMounted, onUnmounted, nextTick, type Ref } from 'vue'

export interface LazySectionConfig {
  target: Ref<HTMLElement | null | undefined>
  onEnter: () => void
}

export interface UseLazySectionLoaderOptions {
  /** ビューポート外でも先読みする余白（例: 200px 手前で発火） */
  rootMargin?: string
  threshold?: number
}

/**
 * 複数セクションを IntersectionObserver で監視し、初回表示時に一度だけ onEnter を実行する。
 */
export function useLazySectionLoader(
  sections: LazySectionConfig[],
  options: UseLazySectionLoaderOptions = {},
) {
  const loaded = new WeakSet<LazySectionConfig>()
  let observer: IntersectionObserver | null = null

  onMounted(() => {
    observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue
          const config = sections.find((s) => s.target.value === entry.target)
          if (!config || loaded.has(config)) continue
          loaded.add(config)
          config.onEnter()
          observer?.unobserve(entry.target)
        }
      },
      {
        root: null,
        rootMargin: options.rootMargin ?? '240px 0px',
        threshold: options.threshold ?? 0,
      },
    )

    nextTick(() => {
      for (const { target } of sections) {
        if (target.value) observer?.observe(target.value)
      }
    })
  })

  onUnmounted(() => {
    observer?.disconnect()
    observer = null
  })
}
