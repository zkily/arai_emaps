<template>
  <span
    v-if="showBar"
    class="auto-news-inline"
    role="region"
    aria-label="本日の自動車ニュース"
  >
    <span class="auto-news-inline__divider" aria-hidden="true" />
    <span class="auto-news-inline__label" title="自動車ニュース">
      <span aria-hidden="true">🚗</span>
      <span class="auto-news-inline__label-text">自動車</span>
      <span v-if="isFallback" class="auto-news-inline__fallback">直近</span>
    </span>

    <span v-if="loading && !items.length" class="auto-news-inline__status">…</span>

    <span
      v-else-if="items.length"
      class="auto-news-inline__viewport"
      @mouseenter="paused = true"
      @mouseleave="paused = false"
      @focusin="paused = true"
      @focusout="paused = false"
    >
      <span
        :key="scrollKey"
        class="auto-news-inline__track"
        :class="{ 'auto-news-inline__track--paused': paused }"
        :style="trackStyle"
      >
        <span
          v-for="copy in 2"
          :key="copy"
          class="auto-news-inline__group"
          :aria-hidden="copy === 2 ? 'true' : undefined"
        >
          <button
            v-for="item in items"
            :key="`${copy}-${item.id}`"
            type="button"
            class="auto-news-inline__item"
            :title="item.title"
            @click="openNews(item.url)"
            @keydown.enter.prevent="openNews(item.url)"
          >
            <span class="auto-news-inline__source">[{{ sourceLabel(item.source) }}]</span>
            <span class="auto-news-inline__title">{{ item.title }}</span>
            <span class="auto-news-inline__sep" aria-hidden="true">·</span>
          </button>
        </span>
      </span>
    </span>
  </span>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { abbreviateSource, useAutoNewsTicker } from '@/composables/useAutoNewsTicker'

const { items, loading, isFallback, visible, openNews } = useAutoNewsTicker()
const paused = ref(false)
const scrollKey = ref(0)

const showBar = computed(() => visible.value || (loading.value && !items.value.length))

/** 件数に応じて横スクロール周期（秒）— 長めに設定して読みやすく */
const scrollDurationSec = computed(() => {
  const n = items.value.length
  const totalChars = items.value.reduce((sum, i) => sum + i.title.length + i.source.length, 0)
  const base = 140 + Math.min(totalChars / 1.8, 280)
  if (n <= 2) return Math.max(base, 170)
  if (n <= 6) return Math.max(base, 200)
  return Math.max(base, 240)
})

const trackStyle = computed(() => ({
  '--news-scroll-duration': `${scrollDurationSec.value}s`,
}))

/** ニュース更新時にアニメーションを先頭から再開 */
watch(
  items,
  () => {
    scrollKey.value += 1
  },
  { deep: true },
)

function sourceLabel(source: string) {
  return abbreviateSource(source)
}
</script>

<style scoped>
.auto-news-inline {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  max-width: min(260px, 30vw);
  flex-shrink: 1;
}

.auto-news-inline__divider {
  width: 1px;
  height: 15px;
  flex-shrink: 0;
  background: linear-gradient(
    180deg,
    transparent 0%,
    rgba(255, 255, 255, 0.32) 50%,
    transparent 100%
  );
}

.auto-news-inline__label {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  flex-shrink: 0;
  font-size: 11px;
  line-height: 1;
}

.auto-news-inline__label-text {
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--hdr-accent, #c7d2fe);
}

.auto-news-inline__fallback {
  font-size: 8px;
  font-weight: 600;
  padding: 1px 4px;
  border-radius: 999px;
  color: #312e81;
  background: #c7d2fe;
}

.auto-news-inline__status {
  font-size: 11px;
  opacity: 0.7;
}

.auto-news-inline__viewport {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  mask-image: linear-gradient(90deg, transparent 0, #000 6px, #000 calc(100% - 6px), transparent 100%);
}

.auto-news-inline__track {
  display: inline-flex;
  width: max-content;
  animation: news-marquee var(--news-scroll-duration, 180s) linear infinite;
}

.auto-news-inline__track--paused {
  animation-play-state: paused;
}

.auto-news-inline__group {
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;
}

.auto-news-inline__item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 0;
  padding-right: 12px;
  border: none;
  background: transparent;
  color: inherit;
  font: inherit;
  white-space: nowrap;
  cursor: pointer;
  flex-shrink: 0;
}

.auto-news-inline__item:hover .auto-news-inline__title,
.auto-news-inline__item:focus-visible .auto-news-inline__title {
  color: #fff;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.auto-news-inline__item:focus-visible {
  outline: none;
}

.auto-news-inline__source {
  flex-shrink: 0;
  font-size: 9.5px;
  font-weight: 600;
  color: var(--hdr-accent, #c7d2fe);
}

.auto-news-inline__title {
  font-size: 11px;
  font-weight: 500;
  color: var(--hdr-text-muted, rgba(248, 250, 252, 0.88));
  transition: color 0.15s ease;
}

.auto-news-inline__sep {
  margin-left: 2px;
  color: rgba(255, 255, 255, 0.35);
}

@keyframes news-marquee {
  0% {
    transform: translateX(0);
  }
  100% {
    transform: translateX(-50%);
  }
}

@media (max-width: 767px) {
  .auto-news-inline {
    max-width: min(150px, 36vw);
    gap: 4px;
  }

  .auto-news-inline__label-text {
    display: none;
  }

  .auto-news-inline__divider {
    height: 12px;
  }

  .auto-news-inline__title {
    font-size: 10px;
  }
}
</style>
