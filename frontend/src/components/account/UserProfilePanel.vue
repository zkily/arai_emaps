<template>
  <div
    class="user-profile-panel"
    :class="{ 'user-profile-panel--dialog': isDialog }"
  >
    <!-- 弹窗内：顶部渐变与头像 -->
    <div v-if="isDialog" class="user-profile-panel__hero">
      <div class="user-profile-panel__hero-mesh" />
      <div class="user-profile-panel__hero-shine" />
      <div class="user-profile-panel__hero-row">
        <div class="user-profile-panel__avatar" aria-hidden="true">
          <span>{{ avatarLetter }}</span>
        </div>
        <div class="user-profile-panel__hero-text">
          <p class="user-profile-panel__hero-name">
            {{ displayUser?.username || '—' }}
          </p>
          <p class="user-profile-panel__hero-sub">
            {{ roleDisplay }}
            <template v-if="departmentDisplay !== '—'">
              <span class="user-profile-panel__hero-dot">·</span>
              {{ departmentDisplay }}
            </template>
          </p>
        </div>
      </div>
    </div>

    <div class="user-profile-panel__sheet">
      <div class="user-profile-panel__sheet-head">
        <span v-if="isDialog" class="user-profile-panel__sheet-title">{{ t('profilePage.desc') }}</span>
        <div v-else class="user-profile-panel__sheet-spacer" />
        <el-button
          type="primary"
          plain
          size="small"
          round
          :loading="loading"
          class="user-profile-panel__refresh"
          :class="{ 'user-profile-panel__refresh--dialog': isDialog }"
          @click="refreshFromServer"
        >
          <el-icon class="el-icon--left"><Refresh /></el-icon>
          {{ t('profilePage.refresh') }}
        </el-button>
      </div>

      <div class="user-profile-panel__fields">
        <div class="user-profile-panel__field">
          <div class="user-profile-panel__field-icon" aria-hidden="true">
            <el-icon><UserIcon /></el-icon>
          </div>
          <div class="user-profile-panel__field-body">
            <span class="user-profile-panel__field-label">{{ t('profilePage.username') }}</span>
            <span class="user-profile-panel__field-value">{{ displayUser?.username || '—' }}</span>
          </div>
        </div>
        <div class="user-profile-panel__field">
          <div class="user-profile-panel__field-icon" aria-hidden="true">
            <el-icon><Message /></el-icon>
          </div>
          <div class="user-profile-panel__field-body">
            <span class="user-profile-panel__field-label">{{ t('profilePage.email') }}</span>
            <span class="user-profile-panel__field-value user-profile-panel__field-value--muted">{{ displayUser?.email || '—' }}</span>
          </div>
        </div>
        <div class="user-profile-panel__field">
          <div class="user-profile-panel__field-icon" aria-hidden="true">
            <el-icon><Document /></el-icon>
          </div>
          <div class="user-profile-panel__field-body">
            <span class="user-profile-panel__field-label">{{ t('profilePage.fullName') }}</span>
            <span class="user-profile-panel__field-value">{{ displayUser?.full_name || '—' }}</span>
          </div>
        </div>
        <div class="user-profile-panel__field">
          <div class="user-profile-panel__field-icon" aria-hidden="true">
            <el-icon><CollectionTag /></el-icon>
          </div>
          <div class="user-profile-panel__field-body">
            <span class="user-profile-panel__field-label">{{ t('profilePage.role') }}</span>
            <span class="user-profile-panel__field-value">{{ roleDisplay }}</span>
          </div>
        </div>
        <div class="user-profile-panel__field">
          <div class="user-profile-panel__field-icon" aria-hidden="true">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="user-profile-panel__field-body">
            <span class="user-profile-panel__field-label">{{ t('profilePage.status') }}</span>
            <span class="user-profile-panel__field-value">
              <span
                class="user-profile-panel__status-pill"
                :class="displayUser?.is_active !== false ? 'is-on' : 'is-off'"
              >
                {{ displayUser?.is_active !== false ? t('profilePage.active') : t('profilePage.inactive') }}
              </span>
            </span>
          </div>
        </div>
        <div class="user-profile-panel__field user-profile-panel__field--last">
          <div class="user-profile-panel__field-icon" aria-hidden="true">
            <el-icon><OfficeBuilding /></el-icon>
          </div>
          <div class="user-profile-panel__field-body">
            <span class="user-profile-panel__field-label">{{ t('profilePage.departmentName') }}</span>
            <span class="user-profile-panel__field-value">{{ departmentDisplay }}</span>
          </div>
        </div>
      </div>

      <div class="user-profile-panel__hint">
        <el-icon class="user-profile-panel__hint-icon"><InfoFilled /></el-icon>
        <p class="user-profile-panel__hint-text">{{ t('profilePage.hint') }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import {
  Refresh,
  User as UserIcon,
  Message,
  Document,
  CollectionTag,
  CircleCheck,
  OfficeBuilding,
  InfoFilled,
} from '@element-plus/icons-vue'
import { getUserInfo } from '@/modules/auth/api'
import { useUserStore } from '@/modules/auth/stores/user'
import type { User } from '@/modules/auth/stores/user'
import { builtinRoleDisplayName } from '@/utils/builtinRoleDisplayName'

const props = withDefaults(
  defineProps<{
    fetchOnMount?: boolean
    /** dialog：带头图渐变；standalone：仅内容卡片（独立页用） */
    presentation?: 'standalone' | 'dialog'
  }>(),
  { fetchOnMount: true, presentation: 'standalone' }
)

const { t } = useI18n()
const userStore = useUserStore()

const isDialog = computed(() => props.presentation === 'dialog')

const loading = ref(false)
const serverUser = ref<User | null>(null)

const displayUser = computed(() => serverUser.value ?? userStore.user)

const avatarLetter = computed(() => {
  const u = displayUser.value?.username?.trim()
  return u ? u.charAt(0).toUpperCase() : '?'
})

const departmentDisplay = computed(() => {
  const u = displayUser.value
  if (!u) return '—'
  const name = u.department_name?.trim()
  return name || '—'
})

const roleDisplay = computed(() => builtinRoleDisplayName(displayUser.value?.role, t))

function rememberMeFlag(): boolean {
  return localStorage.getItem('smart_emap_remember_me') === 'true'
}

async function refreshFromServer() {
  loading.value = true
  try {
    const data = await getUserInfo()
    serverUser.value = data
    userStore.setUser(data, rememberMeFlag())
    ElMessage.success(t('profilePage.refreshed'))
  } catch {
    ElMessage.error(t('profilePage.refreshFailed'))
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (props.fetchOnMount) {
    void refreshFromServer()
  }
})
</script>

<style scoped>
.user-profile-panel {
  --upp-indigo: #4f46e5;
  --upp-violet: #7c3aed;
  --upp-slate: #0f172a;
  --upp-muted: #64748b;
  --upp-line: rgba(15, 23, 42, 0.08);
}

.user-profile-panel--dialog .user-profile-panel__sheet {
  margin: 0;
  border-radius: 0 0 16px 16px;
  border-top: none;
  box-shadow: none;
  padding: 10px 12px 8px;
}

.user-profile-panel--dialog .user-profile-panel__hero {
  padding: 12px 14px 10px;
  border-radius: 16px 16px 0 0;
}

.user-profile-panel--dialog .user-profile-panel__hero-row {
  gap: 10px;
}

.user-profile-panel--dialog .user-profile-panel__avatar {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  font-size: 1.1rem;
}

.user-profile-panel--dialog .user-profile-panel__hero-name {
  margin: 0 0 3px;
  font-size: 1.05rem;
}

.user-profile-panel--dialog .user-profile-panel__hero-sub {
  font-size: 11.5px;
  line-height: 1.35;
}

.user-profile-panel--dialog .user-profile-panel__sheet-head {
  margin-bottom: 8px;
  padding-bottom: 8px;
  gap: 8px;
}

.user-profile-panel--dialog .user-profile-panel__sheet-title {
  font-size: 11px;
  line-height: 1.4;
  max-width: 70%;
}

.user-profile-panel--dialog .user-profile-panel__fields {
  gap: 0;
}

.user-profile-panel--dialog .user-profile-panel__field {
  padding: 5px 4px;
  gap: 8px;
  margin: 0 -2px;
  border-radius: 10px;
}

.user-profile-panel--dialog .user-profile-panel__field--last {
  margin-bottom: 0;
}

.user-profile-panel--dialog .user-profile-panel__field-icon {
  width: 32px;
  height: 32px;
  border-radius: 9px;
}

.user-profile-panel--dialog .user-profile-panel__field-icon .el-icon {
  font-size: 15px;
}

.user-profile-panel--dialog .user-profile-panel__field-body {
  gap: 1px;
}

.user-profile-panel--dialog .user-profile-panel__field-label {
  font-size: 10px;
}

.user-profile-panel--dialog .user-profile-panel__field-value {
  font-size: 13px;
  line-height: 1.3;
}

.user-profile-panel--dialog .user-profile-panel__status-pill {
  padding: 2px 8px;
  font-size: 11px;
}

.user-profile-panel--dialog .user-profile-panel__hint {
  margin-top: 8px;
  padding: 8px 10px;
  gap: 8px;
  border-radius: 10px;
}

.user-profile-panel--dialog .user-profile-panel__hint-icon {
  font-size: 14px;
}

.user-profile-panel--dialog .user-profile-panel__hint-text {
  font-size: 11.5px;
  line-height: 1.45;
}

.user-profile-panel__hero {
  position: relative;
  overflow: hidden;
  margin: 0;
  padding: 22px 20px 20px;
  border-radius: 16px 16px 0 0;
  background: linear-gradient(
    125deg,
    #312e81 0%,
    #4338ca 38%,
    #6366f1 72%,
    #6d28d9 100%
  );
  color: #fff;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.12);
}

.user-profile-panel__hero-mesh {
  pointer-events: none;
  position: absolute;
  inset: 0;
  opacity: 0.45;
  background:
    radial-gradient(ellipse 90% 70% at 0% 0%, rgba(255, 255, 255, 0.2) 0%, transparent 55%),
    radial-gradient(ellipse 60% 50% at 100% 100%, rgba(167, 139, 250, 0.35) 0%, transparent 50%);
}

.user-profile-panel__hero-shine {
  pointer-events: none;
  position: absolute;
  top: -40%;
  right: -15%;
  width: 55%;
  height: 160%;
  background: linear-gradient(
    118deg,
    transparent 0%,
    rgba(255, 255, 255, 0.07) 45%,
    rgba(255, 255, 255, 0.14) 50%,
    rgba(255, 255, 255, 0.05) 55%,
    transparent 100%
  );
  transform: rotate(-16deg);
}

.user-profile-panel__hero-row {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-profile-panel__avatar {
  width: 56px;
  height: 56px;
  flex-shrink: 0;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.35rem;
  font-weight: 800;
  letter-spacing: 0.02em;
  color: #3730a3;
  background: linear-gradient(145deg, #ffffff 0%, #e0e7ff 55%, #c7d2fe 100%);
  box-shadow:
    0 0 0 2px rgba(255, 255, 255, 0.45),
    0 10px 28px rgba(15, 23, 42, 0.25),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.user-profile-panel__hero-text {
  min-width: 0;
  flex: 1;
}

.user-profile-panel__hero-name {
  margin: 0 0 6px;
  font-size: 1.2rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  line-height: 1.25;
  text-shadow: 0 1px 2px rgba(15, 23, 42, 0.15);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-profile-panel__hero-sub {
  margin: 0;
  font-size: 12.5px;
  font-weight: 500;
  line-height: 1.45;
  color: rgba(255, 255, 255, 0.88);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.user-profile-panel__hero-dot {
  margin: 0 0.25em;
  opacity: 0.75;
}

.user-profile-panel__sheet {
  position: relative;
  z-index: 2;
  margin-top: 0;
  padding: 18px 18px 16px;
  background: #fff;
  border: 1px solid var(--upp-line);
  border-radius: 16px;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.8) inset,
    0 18px 40px -24px rgba(15, 23, 42, 0.18);
}

.user-profile-panel:not(.user-profile-panel--dialog) .user-profile-panel__sheet {
  border-radius: 18px;
}

.user-profile-panel__sheet-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(99, 102, 241, 0.1);
}

.user-profile-panel__sheet-title {
  font-size: 12px;
  line-height: 1.55;
  color: var(--upp-muted);
  max-width: 62%;
}

.user-profile-panel__sheet-spacer {
  flex: 1;
  min-width: 0;
}

.user-profile-panel__refresh {
  flex-shrink: 0;
  font-weight: 600;
  border-color: rgba(99, 102, 241, 0.45);
  color: var(--upp-indigo);
  background: rgba(99, 102, 241, 0.06);
}

.user-profile-panel__refresh:hover {
  border-color: var(--upp-indigo);
  background: rgba(99, 102, 241, 0.12);
  color: #4338ca;
}

.user-profile-panel__refresh--dialog {
  padding: 4px 11px;
  font-size: 12px;
  height: 28px;
}

.user-profile-panel__fields {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-profile-panel__field {
  display: flex;
  align-items: stretch;
  gap: 12px;
  padding: 11px 10px;
  margin: 0 -6px;
  border-radius: 12px;
  transition: background 0.18s ease;
}

.user-profile-panel__field:hover {
  background: rgba(99, 102, 241, 0.05);
}

.user-profile-panel__field--last {
  margin-bottom: 4px;
}

.user-profile-panel__field-icon {
  width: 38px;
  height: 38px;
  flex-shrink: 0;
  border-radius: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--upp-indigo);
  background: linear-gradient(145deg, rgba(99, 102, 241, 0.12) 0%, rgba(124, 58, 237, 0.08) 100%);
  border: 1px solid rgba(99, 102, 241, 0.15);
}

.user-profile-panel__field-icon .el-icon {
  font-size: 18px;
}

.user-profile-panel__field-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
  justify-content: center;
}

.user-profile-panel__field-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #94a3b8;
}

.user-profile-panel__field-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--upp-slate);
  line-height: 1.35;
  word-break: break-word;
}

.user-profile-panel__field-value--muted {
  font-weight: 500;
  color: #475569;
}

.user-profile-panel__status-pill {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.user-profile-panel__status-pill.is-on {
  color: #047857;
  background: rgba(16, 185, 129, 0.14);
  border: 1px solid rgba(16, 185, 129, 0.28);
}

.user-profile-panel__status-pill.is-off {
  color: #64748b;
  background: rgba(148, 163, 184, 0.18);
  border: 1px solid rgba(148, 163, 184, 0.35);
}

.user-profile-panel__hint {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  margin-top: 14px;
  padding: 12px 14px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.07) 0%, rgba(124, 58, 237, 0.05) 100%);
  border: 1px solid rgba(99, 102, 241, 0.14);
}

.user-profile-panel__hint-icon {
  flex-shrink: 0;
  margin-top: 1px;
  font-size: 16px;
  color: var(--upp-indigo);
}

.user-profile-panel__hint-text {
  margin: 0;
  font-size: 12.5px;
  line-height: 1.55;
  color: #475569;
}
</style>
