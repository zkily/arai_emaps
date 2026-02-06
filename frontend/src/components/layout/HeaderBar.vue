<template>
  <div class="header-bar">
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
      </div>
    </div>
    
    <div class="header-right">
      <!-- 语言切换 -->
      <el-dropdown trigger="click" @command="handleLocaleChange" class="lang-dropdown" popper-class="lang-dropdown-popper">
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

      <div class="header-action" @click="toggleFullscreen" :title="isFullscreen ? t('common.exitFullscreen') : t('common.fullscreen')">
        <el-icon :size="15">
          <FullScreen v-if="!isFullscreen" />
          <Aim v-else />
        </el-icon>
      </div>
      
      <div class="header-action notification-action">
        <el-badge :value="notificationCount" :hidden="notificationCount === 0" :max="99">
          <el-icon :size="15"><Bell /></el-icon>
        </el-badge>
      </div>
      
      <div class="header-divider"></div>
      
      <el-dropdown @command="handleCommand" trigger="click">
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
            <el-dropdown-item command="settings">
              <el-icon><Setting /></el-icon>
              {{ t('common.settings') }}
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
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/modules/auth/stores/user'
import { ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import 'dayjs/locale/ja'
import { useI18n } from 'vue-i18n'
import { setLocale, getLocale, type LocaleType } from '@/i18n'
import {
  FullScreen, Aim, Bell, User, Setting, SwitchButton, ArrowDown, Clock,
  Menu, Close, Promotion, Star
} from '@element-plus/icons-vue'

const { t } = useI18n()

const localeLabels: Record<LocaleType, string> = {
  en: 'EN',
  ja: 'JA',
  zh: 'ZH',
  vi: 'VI',
}
const currentLangLabel = computed(() => localeLabels[getLocale()] || 'EN')

function handleLocaleChange(locale: LocaleType) {
  setLocale(locale)
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
const notificationCount = ref(3)

let timer: number | null = null

onMounted(() => {
  timer = window.setInterval(() => {
    currentTime.value = dayjs().tz('Asia/Tokyo').format('MM/DD (ddd) HH:mm')
  }, 1000)
  
  document.addEventListener('fullscreenchange', handleFullscreenChange)
})

onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
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
      break
    case 'settings':
      break
  }
}
</script>

<style scoped>
.header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 42px;
  padding: 0 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 2px 12px rgba(102, 126, 234, 0.3);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 6px;
}

.menu-trigger {
  flex-shrink: 0;
  color: white;
}

.menu-trigger .el-icon {
  font-size: 20px;
}

.time-badge {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  background: rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  color: white;
  font-size: 11px;
  border: 1px solid rgba(255, 255, 255, 0.12);
}

.time-icon {
  font-size: 12px;
  opacity: 0.9;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.9; }
  50% { opacity: 0.6; }
}

.current-time {
  font-weight: 600;
  letter-spacing: 0.3px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 4px;
}

.header-action {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 30px;
  height: 30px;
  border-radius: 8px;
  cursor: pointer;
  color: rgba(255, 255, 255, 0.9);
  transition: all 0.2s ease;
  position: relative;
}

.header-action:hover {
  background: rgba(255, 255, 255, 0.18);
  color: white;
  transform: translateY(-1px);
}

.header-action:active {
  transform: translateY(0);
}

/* 语言切换：触发器 */
.lang-dropdown .lang-trigger {
  min-width: 62px;
  padding: 0 8px;
  gap: 4px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.lang-dropdown .lang-trigger:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.25);
}

.lang-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.dropdown-arrow {
  opacity: 0.7;
  margin-left: 2px;
}

.flag-emoji {
  font-size: 14px;
  margin-right: 6px;
}

.notification-action :deep(.el-badge__content) {
  height: 14px;
  line-height: 14px;
  padding: 0 4px;
  font-size: 9px;
  border: none;
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a5a 100%);
  box-shadow: 0 2px 6px rgba(238, 90, 90, 0.4);
}

.header-divider {
  width: 1px;
  height: 18px;
  background: rgba(255, 255, 255, 0.25);
  margin: 0 6px;
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 3px 8px 3px 3px;
  border-radius: 20px;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(10px);
  transition: all 0.2s ease;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.user-dropdown:hover {
  background: rgba(255, 255, 255, 0.22);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
}

.user-avatar {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: linear-gradient(135deg, #fff 0%, #f0f0f0 100%);
  color: #667eea;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 0px;
}

.username {
  font-size: 11px;
  font-weight: 600;
  color: white;
  line-height: 1.2;
}

.user-role {
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: 9px;
  color: rgba(255, 255, 255, 0.75);
  line-height: 1.2;
}

.user-role .el-icon {
  color: #ffd93d;
}

.dropdown-icon {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.7);
  margin-left: -2px;
}

:deep(.el-dropdown-menu__item) {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  padding: 8px 14px;
}

:deep(.el-dropdown-menu__item .el-icon) {
  font-size: 14px;
  color: #667eea;
}

/* Responsive */
@media (max-width: 768px) {
  .header-bar {
    padding: 0 8px;
    height: 40px;
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
    min-width: 30px;
    padding: 0;
  }
  .time-badge {
    padding: 3px 6px;
    font-size: 10px;
  }
  .header-divider {
    margin: 0 4px;
  }
}
</style>

<!-- 下拉菜单宽度（菜单渲染在 body，需单独样式） -->
<style>
.lang-dropdown-popper.el-dropdown__popper .el-dropdown-menu {
  min-width: 140px;
}
.lang-dropdown-popper .el-dropdown-menu__item {
  display: flex;
  align-items: center;
}
</style>
