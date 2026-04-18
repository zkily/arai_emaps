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

        <div class="header-divider" aria-hidden="true" />

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
import UserProfilePanel from '@/components/account/UserProfilePanel.vue'
import { useUserStore } from '@/modules/auth/stores/user'
import { ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import 'dayjs/locale/ja'
import { useI18n } from 'vue-i18n'
import { setLocale, type LocaleType } from '@/i18n'
import {
  FullScreen, Aim, User, SwitchButton, ArrowDown, Clock,
  Menu, Close, Promotion, Star
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
      profileDialogVisible.value = true
      break
  }
}
</script>

<style scoped>
.header-bar {
  position: relative;
  display: flex;
  align-items: stretch;
  min-height: 46px;
  padding: 0;
  overflow: hidden;
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
  background: linear-gradient(
    118deg,
    #312e81 0%,
    #4338ca 22%,
    #6366f1 52%,
    #6d28d9 88%,
    #5b21b6 100%
  );
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.12) inset,
    0 8px 32px -8px rgba(49, 46, 129, 0.55);
  -webkit-font-smoothing: antialiased;
}

.header-bar__mesh {
  pointer-events: none;
  position: absolute;
  inset: 0;
  opacity: 0.5;
  background:
    radial-gradient(ellipse 100% 80% at 0% 0%, rgba(255, 255, 255, 0.22) 0%, transparent 55%),
    radial-gradient(ellipse 70% 60% at 100% 100%, rgba(167, 139, 250, 0.35) 0%, transparent 50%);
}

.header-bar__shine {
  pointer-events: none;
  position: absolute;
  top: -60%;
  right: -20%;
  width: 45%;
  height: 200%;
  background: linear-gradient(
    125deg,
    transparent 0%,
    rgba(255, 255, 255, 0.06) 45%,
    rgba(255, 255, 255, 0.12) 50%,
    rgba(255, 255, 255, 0.04) 55%,
    transparent 100%
  );
  transform: rotate(-18deg);
}

.header-bar__inner {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex: 1;
  min-width: 0;
  padding: 0 18px;
  gap: 12px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.menu-trigger {
  flex-shrink: 0;
  color: #fff;
  border-radius: 11px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(15, 23, 42, 0.15);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.menu-trigger:hover {
  background: rgba(255, 255, 255, 0.14);
  border-color: rgba(255, 255, 255, 0.22);
}

.menu-trigger .el-icon {
  font-size: 20px;
}

.time-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  background: rgba(15, 23, 42, 0.22);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border-radius: 999px;
  color: #f8fafc;
  font-size: 11.5px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.14),
    0 2px 8px rgba(15, 23, 42, 0.12);
}

.time-icon {
  font-size: 13px;
  opacity: 0.95;
  color: #c7d2fe;
}

.current-time {
  font-weight: 600;
  letter-spacing: 0.04em;
  font-variant-numeric: tabular-nums;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.header-action {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 34px;
  height: 34px;
  border-radius: 10px;
  cursor: pointer;
  color: rgba(255, 255, 255, 0.94);
  transition:
    background 0.2s cubic-bezier(0.22, 1, 0.36, 1),
    transform 0.2s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.2s ease;
}

.header-action--icon {
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(15, 23, 42, 0.12);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.header-action--icon:hover {
  background: rgba(255, 255, 255, 0.16);
  border-color: rgba(255, 255, 255, 0.24);
  color: #fff;
  transform: translateY(-1px);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.12),
    0 4px 12px rgba(15, 23, 42, 0.15);
}

.header-action:active {
  transform: translateY(0);
}

/* 语言切换 */
.lang-dropdown .lang-trigger {
  min-width: 72px;
  height: 34px;
  padding: 0 12px;
  gap: 6px;
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.16);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.lang-dropdown .lang-trigger:hover {
  background: rgba(255, 255, 255, 0.14);
  border-color: rgba(255, 255, 255, 0.26);
  transform: translateY(-1px);
}

.lang-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
}

.dropdown-arrow {
  opacity: 0.8;
  margin-left: 2px;
}

.flag-emoji {
  font-size: 14px;
  margin-right: 6px;
}

.header-divider {
  width: 1px;
  height: 22px;
  background: linear-gradient(
    180deg,
    transparent 0%,
    rgba(255, 255, 255, 0.35) 50%,
    transparent 100%
  );
  margin: 0 4px 0 10px;
  flex-shrink: 0;
}

/* 用户区域：加宽显示，行高保持不变 */
.user-dropdown {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 168px;
  padding: 5px 14px 5px 5px;
  border-radius: 999px;
  cursor: pointer;
  background: rgba(15, 23, 42, 0.2);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  transition: all 0.22s cubic-bezier(0.22, 1, 0.36, 1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.12),
    0 2px 10px rgba(15, 23, 42, 0.12);
}

.user-dropdown:hover {
  background: rgba(255, 255, 255, 0.16);
  border-color: rgba(255, 255, 255, 0.32);
  transform: translateY(-1px);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.18),
    0 6px 20px rgba(15, 23, 42, 0.18);
}

.user-avatar {
  width: 30px;
  height: 30px;
  flex-shrink: 0;
  border-radius: 50%;
  background: linear-gradient(145deg, #ffffff 0%, #e0e7ff 55%, #c7d2fe 100%);
  color: #4338ca;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 800;
  box-shadow:
    0 0 0 2px rgba(255, 255, 255, 0.38),
    0 2px 8px rgba(15, 23, 42, 0.18),
    inset 0 1px 0 rgba(255, 255, 255, 0.85);
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
  color: #fff;
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
  color: rgba(255, 255, 255, 0.82);
  line-height: 1.2;
}

.user-role .el-icon {
  color: #fcd34d;
  flex-shrink: 0;
}

.dropdown-icon {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.75);
  margin-left: 2px;
  flex-shrink: 0;
}

:deep(.el-dropdown-menu__item) {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  padding: 9px 16px;
  border-radius: 8px;
  transition: all 0.2s ease;
}

:deep(.el-dropdown-menu__item:hover) {
  background: rgba(99, 102, 241, 0.08);
  color: #6366f1;
}

:deep(.el-dropdown-menu__item .el-icon) {
  font-size: 15px;
  color: #6366f1;
}

/* Responsive */
@media (max-width: 768px) {
  .header-bar__inner {
    padding: 0 12px;
  }

  .header-bar {
    min-height: 44px;
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
    min-width: 32px;
    padding: 0;
  }
  .time-badge {
    padding: 4px 8px;
    font-size: 10px;
  }
  .header-divider {
    margin: 0 4px;
    height: 18px;
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
