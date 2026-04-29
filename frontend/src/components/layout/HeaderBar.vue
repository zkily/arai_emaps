<template>
  <div class="header-bar">
    <div class="header-bar__mesh" aria-hidden="true" />
    <div class="header-bar__shine" aria-hidden="true" />
    <div class="header-bar__inner">
      <div class="header-left">
        <div
          v-if="isMobile"
          class="header-action menu-trigger"
          :title="t('common.menu')"
          @click="$emit('toggle-sidebar')"
        >
          <el-icon :size="20">
            <component :is="sidebarOpen ? Close : Menu" />
          </el-icon>
        </div>
        <div class="time-badge">
          <el-icon class="time-icon"><Clock /></el-icon>
          <span class="current-time">{{ currentTime }}</span>
          <span
            class="weather-inline"
            :title="t('common.headerWeatherNagoyaHint')"
            role="status"
            :aria-label="weatherAria"
          >
            <span class="weather-divider" aria-hidden="true" />
            <span class="weather-emoji" aria-hidden="true">{{ weatherEmoji }}</span>
            <span class="weather-temp">{{ weatherTemp }}</span>
          </span>
        </div>
      </div>

      <div class="header-right">
        <!-- 语言切换 -->
        <el-dropdown trigger="click" @command="handleLocaleChange" class="lang-dropdown" popper-class="header-dropdown-popper">
          <div class="header-action lang-trigger" :title="t('common.language')">
            <el-icon :size="15"><Promotion /></el-icon>
            <span class="lang-label">{{ currentLangLabel }}</span>
            <el-icon class="dropdown-arrow" :size="10"><ArrowDown /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="en">
                <span class="flag-emoji">🇺🇸</span> English
              </el-dropdown-item>
              <el-dropdown-item command="ja">
                <span class="flag-emoji">🇯🇵</span> 日本語
              </el-dropdown-item>
              <el-dropdown-item command="zh">
                <span class="flag-emoji">🇨🇳</span> 中文
              </el-dropdown-item>
              <el-dropdown-item command="vi">
                <span class="flag-emoji">🇻🇳</span> Tiếng Việt
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <div
          class="header-action header-action--icon"
          @click="toggleFullscreen"
          :title="isFullscreen ? t('common.exitFullscreen') : t('common.fullscreen')"
        >
          <el-icon :size="16">
            <FullScreen v-if="!isFullscreen" />
            <Aim v-else />
          </el-icon>
        </div>

        <el-popover
          v-model:visible="notifPopoverVisible"
          placement="bottom-end"
          :width="notifPopoverWidth"
          trigger="click"
          popper-class="header-notif-popper"
          @show="onNotifPopoverShow"
        >
          <template #reference>
            <div
              class="header-action header-action--icon header-action--notif"
              :title="t('common.headerNotifBellTitle')"
              role="button"
              tabindex="0"
              :aria-label="t('common.headerNotifBellTitle')"
            >
              <span
                class="header-notif-bell-core"
                :class="{ 'header-notif-bell-core--swing': pickingAlertActive }"
                aria-hidden="true"
              >
                <el-icon class="header-notif-bell-icon" :size="16"><Bell /></el-icon>
              </span>
              <span
                v-if="pickingAlertActive"
                class="header-notif-badge"
                :aria-label="`${notifCount}${t('common.headerNotifTitle')}`"
              >{{ notifCountDisplay }}</span>
            </div>
          </template>
          <div class="header-notif-panel">
            <div class="header-notif-panel__title">{{ t('common.headerNotifTitle') }}</div>
            <div
              v-if="pickingIncompleteAlert"
              class="header-notif-item"
              role="button"
              tabindex="0"
              @click="gotoPickingProgress"
              @keydown.enter.prevent="gotoPickingProgress"
            >
              <div class="header-notif-item__row">
                <el-icon class="header-notif-item__icon" :size="18"><Warning /></el-icon>
                <div class="header-notif-item__text">
                  <span class="header-notif-item__label">{{ t('shipping.titlePicking') }}</span>
                  <p class="header-notif-item__desc">{{ pickingIncompleteDescription }}</p>
                </div>
              </div>
              <span class="header-notif-item__link">{{ t('common.headerNotifOpenPicking') }} →</span>
            </div>
            <div v-else class="header-notif-empty">{{ t('common.headerNotifEmpty') }}</div>
          </div>
        </el-popover>

        <div class="header-divider" aria-hidden="true" />

        <el-dropdown @command="handleCommand" trigger="click" popper-class="header-dropdown-popper">
          <div class="user-dropdown">
            <div class="user-avatar">
              <el-icon v-if="!userStore.user?.username" :size="14"><User /></el-icon>
              <span v-else>{{ userStore.user?.username?.charAt(0).toUpperCase() }}</span>
            </div>
            <div class="user-details">
              <span class="username">{{ userStore.user?.username || t('common.guest') }}</span>
              <span class="user-role">
                <el-icon :size="9"><Star /></el-icon>
                {{ t('common.admin') }}
              </span>
            </div>
            <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu class="user-menu">
              <el-dropdown-item command="profile">
                <el-icon><User /></el-icon>
                {{ t('common.profile') }}
              </el-dropdown-item>
              <el-dropdown-item command="logout" divided>
                <el-icon><SwitchButton /></el-icon>
                {{ t('common.logout') }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <el-dialog
      v-model="profileDialogVisible"
      :title="t('common.profile')"
      width="400px"
      append-to-body
      destroy-on-close
      align-center
      class="header-profile-dialog"
    >
      <UserProfilePanel v-if="profileDialogVisible" presentation="dialog" />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { getPickingNewProgress } from '@/api/shipping/picking'
import { parseTodayOverviewFromPickingProgressResponse } from '@/utils/shippingPickingNewProgressParse'
import type { ShippingPickingTodayOverview } from '@/utils/shippingPickingNewProgressParse'
import UserProfilePanel from '@/components/account/UserProfilePanel.vue'
import { useUserStore } from '@/modules/auth/stores/user'
import { ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import 'dayjs/locale/ja'
import { useI18n } from 'vue-i18n'
import { setLocale, type LocaleType } from '@/i18n'
import {
  FullScreen, Aim, User, SwitchButton, ArrowDown, Clock,
  Menu, Close, Promotion, Star, Bell, Warning
} from '@element-plus/icons-vue'

const { t, locale } = useI18n()

const localeLabels: Record<LocaleType, string> = {
  en: 'EN',
  ja: 'JA',
  zh: 'ZH',
  vi: 'VI',
}
const currentLangLabel = computed(() => localeLabels[locale.value as LocaleType] || 'EN')

function handleLocaleChange(newLocale: LocaleType) {
  setLocale(newLocale)
}

defineProps<{
  isMobile: boolean
  sidebarOpen: boolean
}>()

defineEmits<{
  (e: 'toggle-sidebar'): void
}>()

const router = useRouter()
const userStore = useUserStore()

const currentTime = ref(dayjs().tz('Asia/Tokyo').format('MM/DD (ddd) HH:mm'))
const isFullscreen = ref(false)
const profileDialogVisible = ref(false)

const notifPopoverVisible = ref(false)
const notifPopoverWidth = computed(() => (typeof window !== 'undefined' ? Math.min(320, Math.round(window.innerWidth * 0.92)) : 320))

const PICKING_ALERT_POLL_MS = 5 * 60 * 1000
const pickingOverview = ref<ShippingPickingTodayOverview | null>(null)

const pickingIncompleteAlert = computed(() => {
  const o = pickingOverview.value
  if (!o || o.total_today <= 0) return null
  if (o.today_completion_rate >= 100) return null
  return o
})

const pickingAlertActive = computed(() => pickingIncompleteAlert.value != null)
const notifCount = computed(() => (pickingIncompleteAlert.value ? 1 : 0))
const notifCountDisplay = computed(() => (notifCount.value > 99 ? '99+' : String(notifCount.value)))

const pickingIncompleteDescription = computed(() => {
  const o = pickingIncompleteAlert.value
  if (!o) return ''
  return t('common.headerNotifPickingIncompleteBody', {
    rate: o.today_completion_rate,
    pending: o.pending_today,
    completed: o.completed_today,
    total: o.total_today,
  })
})

async function fetchPickingAlertOverview() {
  try {
    const raw = await getPickingNewProgress()
    const overview = parseTodayOverviewFromPickingProgressResponse(raw)
    pickingOverview.value = overview
  } catch {
    /* 静默失败，保留上次数据或空列表 */
  }
}

function onNotifPopoverShow() {
  void fetchPickingAlertOverview()
}

function gotoPickingProgress() {
  notifPopoverVisible.value = false
  router.push({ path: '/erp/shipping/picking', query: { tab: 'progress' } })
}

/** 名古屋市中心付近（Open-Meteo 無料 API、キー不要） */
const NAGOYA_LAT = 35.1815
const NAGOYA_LON = 136.9066
const WEATHER_REFRESH_MS = 15 * 60 * 1000

const weatherTemp = ref<string>('--')
const weatherEmoji = ref('🌤️')
const weatherAria = ref('')

function wmoWeatherCodeToEmoji(code: number): string {
  if (code === 0) return '☀️'
  if (code <= 3) return '⛅'
  if (code <= 48) return '🌫️'
  if (code <= 57) return '🌦️'
  if (code <= 67) return '🌧️'
  if (code <= 77) return '❄️'
  if (code <= 82) return '🌧️'
  if (code <= 86) return '❄️'
  if (code <= 99) return '⛈️'
  return '🌤️'
}

async function fetchHeaderWeather() {
  try {
    const params = new URLSearchParams({
      latitude: String(NAGOYA_LAT),
      longitude: String(NAGOYA_LON),
      current: 'temperature_2m,weather_code',
      timezone: 'Asia/Tokyo',
    })
    const res = await fetch(`https://api.open-meteo.com/v1/forecast?${params}`)
    if (!res.ok) throw new Error('weather http')
    const data = (await res.json()) as {
      current?: { temperature_2m?: number; weather_code?: number }
    }
    const tempC = data.current?.temperature_2m
    const code = data.current?.weather_code
    if (typeof tempC !== 'number') throw new Error('weather data')
    weatherTemp.value = `${Math.round(tempC)}°C`
    weatherEmoji.value = wmoWeatherCodeToEmoji(typeof code === 'number' ? code : 0)
    weatherAria.value = `${t('common.headerWeatherNagoya')}: ${weatherTemp.value}`
  } catch {
    weatherTemp.value = '--'
    weatherEmoji.value = '🌤️'
    weatherAria.value = t('common.headerWeatherUnavailable')
  }
}

let timer: number | null = null
let weatherTimer: number | null = null
let pickingPollTimer: number | null = null

onMounted(() => {
  timer = window.setInterval(() => {
    currentTime.value = dayjs().tz('Asia/Tokyo').format('MM/DD (ddd) HH:mm')
  }, 1000)

  void fetchHeaderWeather()
  weatherTimer = window.setInterval(() => {
    void fetchHeaderWeather()
  }, WEATHER_REFRESH_MS)

  void fetchPickingAlertOverview()
  pickingPollTimer = window.setInterval(() => {
    void fetchPickingAlertOverview()
  }, PICKING_ALERT_POLL_MS)

  document.addEventListener('fullscreenchange', handleFullscreenChange)
})

onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
  }
  if (weatherTimer) {
    clearInterval(weatherTimer)
  }
  if (pickingPollTimer) {
    clearInterval(pickingPollTimer)
  }
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
})

const handleFullscreenChange = () => {
  isFullscreen.value = !!document.fullscreenElement
}

const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
}

const handleCommand = async (command: string) => {
  switch (command) {
    case 'logout':
      try {
        await ElMessageBox.confirm(
          t('common.logoutConfirm'),
          t('common.confirm'),
          {
            confirmButtonText: t('common.logout'),
            cancelButtonText: t('common.cancel'),
            type: 'warning',
          }
        )
        const { stopInactivityCheck } = await import('@/utils/inactivity')
        await userStore.logout()
        stopInactivityCheck()
        router.push('/login')
      } catch {
        // キャンセル
      }
      break
    case 'profile':
      profileDialogVisible.value = true
      break
  }
}
</script>

<style scoped>
/* 顶栏统一设计变量：玻璃面、描边、圆角、动效 */
.header-bar {
  --hdr-radius: 12px;
  --hdr-radius-pill: 999px;
  --hdr-glass: rgba(15, 23, 42, 0.28);
  --hdr-glass-strong: rgba(15, 23, 42, 0.38);
  --hdr-glass-hover: rgba(255, 255, 255, 0.12);
  --hdr-border: rgba(226, 232, 255, 0.2);
  --hdr-border-hover: rgba(238, 242, 255, 0.42);
  --hdr-inset: inset 0 1px 0 rgba(255, 255, 255, 0.16);
  --hdr-blur: blur(16px);
  --hdr-text: #f8fafc;
  --hdr-text-muted: rgba(248, 250, 252, 0.88);
  --hdr-accent: #c7d2fe;
  --hdr-accent-bright: #e0e7ff;
  --hdr-shadow-raised: 0 4px 14px rgba(15, 23, 42, 0.22);
  --hdr-ease: cubic-bezier(0.22, 1, 0.36, 1);

  position: relative;
  display: flex;
  align-items: stretch;
  min-height: 48px;
  padding: 0;
  overflow: hidden;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  background: linear-gradient(
    122deg,
    #1e1b4b 0%,
    #312e81 18%,
    #4338ca 42%,
    #5b21b6 72%,
    #4c1d95 100%
  );
  box-shadow:
    var(--hdr-inset),
    0 10px 36px -10px rgba(15, 23, 42, 0.55);
  -webkit-font-smoothing: antialiased;
}

.header-bar__mesh {
  pointer-events: none;
  position: absolute;
  inset: 0;
  opacity: 0.55;
  background:
    radial-gradient(ellipse 90% 70% at 8% 0%, rgba(255, 255, 255, 0.2) 0%, transparent 52%),
    radial-gradient(ellipse 60% 55% at 96% 100%, rgba(167, 139, 250, 0.28) 0%, transparent 48%),
    radial-gradient(ellipse 50% 40% at 50% 120%, rgba(99, 102, 241, 0.15) 0%, transparent 45%);
}

.header-bar__shine {
  pointer-events: none;
  position: absolute;
  top: -58%;
  right: -18%;
  width: 44%;
  height: 200%;
  background: linear-gradient(
    128deg,
    transparent 0%,
    rgba(255, 255, 255, 0.05) 44%,
    rgba(255, 255, 255, 0.11) 50%,
    rgba(255, 255, 255, 0.04) 56%,
    transparent 100%
  );
  transform: rotate(-17deg);
}

.header-bar__inner {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex: 1;
  min-width: 0;
  padding: 0 20px;
  gap: 14px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.menu-trigger {
  flex-shrink: 0;
  color: var(--hdr-text);
  border-radius: var(--hdr-radius);
  border: 1px solid var(--hdr-border);
  background: var(--hdr-glass);
  backdrop-filter: var(--hdr-blur);
  -webkit-backdrop-filter: var(--hdr-blur);
  box-shadow: var(--hdr-inset), 0 2px 10px rgba(15, 23, 42, 0.12);
  transition:
    background 0.22s var(--hdr-ease),
    border-color 0.22s var(--hdr-ease),
    box-shadow 0.22s ease,
    transform 0.22s var(--hdr-ease);
}

.menu-trigger:hover {
  background: var(--hdr-glass-hover);
  border-color: var(--hdr-border-hover);
  transform: translateY(-1px);
  box-shadow: var(--hdr-inset), var(--hdr-shadow-raised);
}

.menu-trigger:active {
  transform: translateY(0);
}

.menu-trigger .el-icon {
  font-size: 20px;
}

.time-badge {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 7px 16px;
  background: var(--hdr-glass-strong);
  backdrop-filter: var(--hdr-blur);
  -webkit-backdrop-filter: var(--hdr-blur);
  border-radius: var(--hdr-radius-pill);
  color: var(--hdr-text);
  font-size: 11.5px;
  border: 1px solid var(--hdr-border);
  box-shadow: var(--hdr-inset), 0 2px 12px rgba(15, 23, 42, 0.14);
}

.time-icon {
  font-size: 14px;
  opacity: 0.95;
  color: var(--hdr-accent);
}

.current-time {
  font-weight: 600;
  letter-spacing: 0.04em;
  font-variant-numeric: tabular-nums;
  color: var(--hdr-text);
}

.weather-inline {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-left: 2px;
  flex-shrink: 0;
}

.weather-divider {
  width: 1px;
  height: 15px;
  margin-right: 1px;
  background: linear-gradient(
    180deg,
    transparent 0%,
    rgba(255, 255, 255, 0.32) 50%,
    transparent 100%
  );
}

.weather-emoji {
  font-size: 13px;
  line-height: 1;
}

.weather-temp {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.02em;
  color: var(--hdr-accent-bright);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.header-action {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 36px;
  height: 36px;
  border-radius: var(--hdr-radius);
  cursor: pointer;
  color: var(--hdr-text-muted);
  transition:
    background 0.22s var(--hdr-ease),
    border-color 0.22s var(--hdr-ease),
    transform 0.22s var(--hdr-ease),
    box-shadow 0.22s ease,
    color 0.2s ease;
}

.header-action--icon {
  border: 1px solid var(--hdr-border);
  background: var(--hdr-glass);
  backdrop-filter: var(--hdr-blur);
  -webkit-backdrop-filter: var(--hdr-blur);
  box-shadow: var(--hdr-inset), 0 2px 10px rgba(15, 23, 42, 0.1);
}

.header-action--icon:hover {
  background: var(--hdr-glass-hover);
  border-color: var(--hdr-border-hover);
  color: #fff;
  transform: translateY(-1px);
  box-shadow: var(--hdr-inset), var(--hdr-shadow-raised);
}

.header-action:active {
  transform: translateY(0);
}

.header-action--notif {
  position: relative;
  background: linear-gradient(
    155deg,
    rgba(255, 255, 255, 0.14) 0%,
    rgba(99, 102, 241, 0.22) 45%,
    rgba(15, 23, 42, 0.32) 100%
  );
  border-color: rgba(199, 210, 254, 0.38);
  box-shadow:
    var(--hdr-inset),
    0 4px 16px rgba(15, 23, 42, 0.2);
}

.header-action--notif:hover {
  background: linear-gradient(
    155deg,
    rgba(255, 255, 255, 0.2) 0%,
    rgba(129, 140, 248, 0.28) 48%,
    rgba(30, 27, 75, 0.35) 100%
  );
  border-color: var(--hdr-border-hover);
  color: #fff;
  transform: translateY(-1px);
  box-shadow: var(--hdr-inset), var(--hdr-shadow-raised);
}

@keyframes header-bell-swing {
  0%,
  78% {
    transform: rotate(0deg);
  }
  82% {
    transform: rotate(-9deg);
  }
  86% {
    transform: rotate(9deg);
  }
  90% {
    transform: rotate(-5deg);
  }
  94% {
    transform: rotate(5deg);
  }
  98%,
  100% {
    transform: rotate(0deg);
  }
}

.header-notif-bell-core {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: radial-gradient(
    120% 120% at 30% 20%,
    rgba(255, 255, 255, 0.45) 0%,
    rgba(199, 210, 254, 0.2) 52%,
    rgba(99, 102, 241, 0.12) 100%
  );
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.35);
}

.header-notif-bell-core--swing {
  transform-origin: 50% 8%;
  animation: header-bell-swing 3.6s ease-in-out infinite;
}

@media (prefers-reduced-motion: reduce) {
  .header-notif-bell-core--swing {
    animation: none;
  }
}

.header-notif-bell-icon {
  color: #f8fafc;
  filter: drop-shadow(0 1px 1px rgba(15, 23, 42, 0.35));
}

.header-action--notif:hover .header-notif-bell-core {
  background: radial-gradient(
    120% 120% at 30% 20%,
    rgba(255, 255, 255, 0.55) 0%,
    rgba(224, 231, 255, 0.35) 50%,
    rgba(129, 140, 248, 0.22) 100%
  );
}

.header-notif-badge {
  position: absolute;
  top: -4px;
  right: -5px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(180deg, #fda4af 0%, #f43f5e 48%, #e11d48 100%);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  line-height: 1;
  letter-spacing: 0.01em;
  border: 1px solid rgba(255, 255, 255, 0.85);
  box-shadow:
    0 4px 12px rgba(244, 63, 94, 0.45),
    0 0 0 2px rgba(15, 23, 42, 0.45);
  pointer-events: none;
}

/* 语言切换 */
.lang-dropdown .lang-trigger {
  min-width: 76px;
  height: 36px;
  padding: 0 12px;
  gap: 7px;
  border-radius: var(--hdr-radius);
  background: var(--hdr-glass);
  backdrop-filter: var(--hdr-blur);
  -webkit-backdrop-filter: var(--hdr-blur);
  border: 1px solid var(--hdr-border);
  box-shadow: var(--hdr-inset), 0 2px 10px rgba(15, 23, 42, 0.1);
  transition:
    background 0.22s var(--hdr-ease),
    border-color 0.22s var(--hdr-ease),
    transform 0.22s var(--hdr-ease),
    box-shadow 0.22s ease;
}

.lang-dropdown .lang-trigger:hover {
  background: var(--hdr-glass-hover);
  border-color: var(--hdr-border-hover);
  transform: translateY(-1px);
  box-shadow: var(--hdr-inset), var(--hdr-shadow-raised);
}

.lang-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
  color: var(--hdr-text);
}

.lang-dropdown .lang-trigger .el-icon {
  color: var(--hdr-accent);
}

.dropdown-arrow {
  opacity: 0.85;
  margin-left: 1px;
  color: rgba(248, 250, 252, 0.75);
}

.flag-emoji {
  font-size: 14px;
  margin-right: 6px;
}

.header-divider {
  width: 1px;
  height: 24px;
  background: linear-gradient(
    180deg,
    transparent 0%,
    rgba(255, 255, 255, 0.22) 22%,
    rgba(255, 255, 255, 0.38) 50%,
    rgba(255, 255, 255, 0.22) 78%,
    transparent 100%
  );
  margin: 0 2px 0 8px;
  flex-shrink: 0;
  box-shadow: 1px 0 0 rgba(15, 23, 42, 0.12);
}

/* 用户区域 */
.user-dropdown {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 172px;
  padding: 5px 14px 5px 6px;
  border-radius: var(--hdr-radius-pill);
  cursor: pointer;
  background: var(--hdr-glass-strong);
  backdrop-filter: var(--hdr-blur);
  -webkit-backdrop-filter: var(--hdr-blur);
  transition:
    background 0.22s var(--hdr-ease),
    border-color 0.22s var(--hdr-ease),
    transform 0.22s var(--hdr-ease),
    box-shadow 0.22s ease;
  border: 1px solid var(--hdr-border);
  box-shadow: var(--hdr-inset), 0 2px 12px rgba(15, 23, 42, 0.12);
}

.user-dropdown:hover {
  background: var(--hdr-glass-hover);
  border-color: var(--hdr-border-hover);
  transform: translateY(-1px);
  box-shadow: var(--hdr-inset), var(--hdr-shadow-raised);
}

.user-avatar {
  width: 30px;
  height: 30px;
  flex-shrink: 0;
  border-radius: 50%;
  background: linear-gradient(150deg, #ffffff 0%, #e0e7ff 48%, #a5b4fc 100%);
  color: #3730a3;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 800;
  box-shadow:
    0 0 0 2px rgba(255, 255, 255, 0.45),
    0 3px 10px rgba(15, 23, 42, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 0;
  min-width: 0;
  flex: 1;
}

.username {
  font-size: 12px;
  font-weight: 600;
  color: var(--hdr-text);
  line-height: 1.2;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-role {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 10px;
  color: rgba(248, 250, 252, 0.78);
  line-height: 1.2;
}

.user-role .el-icon {
  color: #fde68a;
  flex-shrink: 0;
}

.dropdown-icon {
  font-size: 10px;
  color: rgba(248, 250, 252, 0.72);
  margin-left: 2px;
  flex-shrink: 0;
}

/* Responsive */
@media (max-width: 768px) {
  .header-bar__inner {
    padding: 0 12px;
    gap: 10px;
  }

  .header-bar {
    min-height: 46px;
  }
  .user-dropdown {
    min-width: auto;
    padding: 4px;
  }
  .user-details {
    display: none;
  }
  .lang-label {
    display: none;
  }
  .dropdown-arrow {
    display: none;
  }
  .lang-dropdown .lang-trigger {
    min-width: 36px;
    width: 36px;
    padding: 0;
    justify-content: center;
  }
  .time-badge {
    padding: 5px 10px;
    font-size: 10px;
    gap: 6px;
  }
  .weather-emoji {
    font-size: 11px;
  }
  .weather-divider {
    height: 12px;
  }
  .header-divider {
    margin: 0 2px;
    height: 20px;
  }
}
</style>

<!-- 下拉菜单宽度（菜单渲染在 body，需单独样式） -->
<style>
.header-dropdown-popper.el-dropdown__popper {
  border-radius: 14px !important;
  border: 1px solid rgba(199, 210, 254, 0.55) !important;
  box-shadow:
    0 20px 44px -14px rgba(30, 27, 75, 0.35),
    0 0 0 1px rgba(255, 255, 255, 0.75) inset !important;
  overflow: hidden;
  padding: 6px 0 !important;
  background: linear-gradient(168deg, #ffffff 0%, #f8fafc 45%, #f1f5ff 100%) !important;
}

.header-dropdown-popper.el-dropdown__popper .el-dropdown-menu {
  min-width: 180px;
  padding: 0;
  background: transparent;
  box-shadow: none;
}

.header-dropdown-popper .el-dropdown-menu__item {
  display: flex;
  align-items: center;
  margin: 2px 8px;
  border-radius: 10px;
  font-size: 13px;
  transition: background 0.18s ease, color 0.18s ease;
}

.header-dropdown-popper .el-dropdown-menu__item:not(.is-disabled):hover {
  background: linear-gradient(90deg, rgba(99, 102, 241, 0.12) 0%, rgba(129, 140, 248, 0.06) 100%);
  color: #4338ca;
}

.header-dropdown-popper .el-dropdown-menu__item .el-icon {
  font-size: 15px;
  color: #6366f1;
}

/* ヘッダ通知 Popover（teleport 先でも効くようグローバル） */
.header-notif-popper.el-popover.el-popper {
  padding: 0;
  border-radius: 14px;
  border: 1px solid rgba(199, 210, 254, 0.55);
  box-shadow:
    0 20px 44px -14px rgba(30, 27, 75, 0.35),
    0 0 0 1px rgba(255, 255, 255, 0.75) inset;
  overflow: hidden;
  background: linear-gradient(168deg, #ffffff 0%, #f8fafc 45%, #f1f5ff 100%);
}

.header-notif-panel {
  padding: 14px 16px 16px;
  max-width: 100%;
}

.header-notif-panel__title {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #64748b;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.25);
}

.header-notif-item {
  cursor: pointer;
  padding: 12px 14px;
  border-radius: 12px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 250, 252, 0.98) 100%);
  border: 1px solid rgba(251, 191, 36, 0.38);
  box-shadow:
    0 2px 12px rgba(251, 146, 60, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
  transition:
    background 0.2s ease,
    border-color 0.2s ease,
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

.header-notif-item:hover {
  background: #fff;
  border-color: rgba(245, 158, 11, 0.55);
  transform: translateY(-1px);
  box-shadow:
    0 6px 18px rgba(245, 158, 11, 0.14),
    inset 0 1px 0 rgba(255, 255, 255, 1);
}

.header-notif-item:focus-visible {
  outline: 2px solid #6366f1;
  outline-offset: 2px;
}

.header-notif-item__row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.header-notif-item__icon {
  flex-shrink: 0;
  color: #d97706;
  margin-top: 1px;
}

.header-notif-item__label {
  display: block;
  font-size: 12px;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 5px;
  letter-spacing: 0.01em;
}

.header-notif-item__desc {
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
  color: #475569;
}

.header-notif-item__link {
  display: inline-block;
  margin-top: 11px;
  font-size: 11px;
  font-weight: 600;
  color: #4f46e5;
  letter-spacing: 0.02em;
}

.header-notif-empty {
  font-size: 12px;
  color: #64748b;
  line-height: 1.55;
  padding: 8px 4px 6px;
}

.header-profile-dialog.el-dialog {
  border-radius: 16px;
  overflow: hidden;
  padding: 0;
  background: #f1f5f9;
  box-shadow:
    0 25px 50px -12px rgba(15, 23, 42, 0.38),
    0 0 0 1px rgba(255, 255, 255, 0.06) inset;
}

.header-profile-dialog .el-dialog__header {
  margin: 0;
  padding: 4px 8px 0;
  border-bottom: none;
  background: transparent;
}

.header-profile-dialog .el-dialog__headerbtn {
  top: 4px;
  right: 6px;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  transition: background 0.2s ease;
}

.header-profile-dialog .el-dialog__headerbtn:hover {
  background: rgba(15, 23, 42, 0.06);
}

.header-profile-dialog .el-dialog__title {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.header-profile-dialog .el-dialog__body {
  padding: 0;
  max-height: min(78vh, 620px);
  overflow-x: hidden;
  overflow-y: auto;
  background: transparent;
}
</style>
