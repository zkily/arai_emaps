<template>
  <div class="login-container">
    <div class="login-wrapper">
      <!-- Left Panel - Branding (3D) -->
      <div class="login-left">
        <div class="left-scene" aria-hidden="true">
          <div class="scene-gradient"></div>
          <div class="scene-grid"></div>
          <div class="orb orb-a"></div>
          <div class="orb orb-b"></div>
          <div class="orb orb-c"></div>
          <div class="shape-cube">
            <div class="cube-face cube-top"></div>
            <div class="cube-face cube-front"></div>
            <div class="cube-face cube-right"></div>
          </div>
          <div class="shape-ring"></div>
          <div class="shape-diamond"></div>
        </div>

        <div class="left-content">
          <div class="brand-section">
            <div class="logo-stage">
              <div class="logo-orbit"></div>
              <div class="logo-3d">
                <div class="logo-shine"></div>
                <el-icon :size="44"><Management /></el-icon>
              </div>
            </div>
            <h1 class="brand-title">
              <span class="title-main">Smart-EMAP</span>
            </h1>
            <p class="brand-subtitle">生産管理システム</p>
            <div class="brand-badges">
              <span class="module-badge erp">ERP</span>
              <span class="module-badge aps">APS</span>
              <span class="module-badge mes">MES</span>
            </div>
            <p class="brand-desc">製造業のDXを実現する次世代統合管理システム</p>
          </div>

          <div class="features-list">
            <div
              v-for="(feat, i) in features"
              :key="feat.key"
              class="feature-card"
              :class="feat.key"
              :style="{ '--delay': `${i * 0.12}s` }"
            >
              <div class="feature-icon-wrap">
                <div class="feature-icon-3d">
                  <el-icon :size="20"><component :is="feat.icon" /></el-icon>
                </div>
              </div>
              <div class="feature-body">
                <span class="feature-tag">{{ feat.tag }}</span>
                <span class="feature-label">{{ feat.label }}</span>
              </div>
              <el-icon class="feature-arrow"><ArrowRight /></el-icon>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Panel - Login Form -->
      <div class="login-right">
        <div class="right-scene" aria-hidden="true">
          <div class="right-blob blob-1"></div>
          <div class="right-blob blob-2"></div>
          <div class="right-blob blob-3"></div>
          <div class="right-dots"></div>
        </div>

        <div class="right-content">
          <div class="login-card">
            <div class="card-accent"></div>
            <div class="card-glow"></div>

            <div class="card-header">
              <div class="header-icon-wrap">
                <el-icon :size="22"><UserFilled /></el-icon>
              </div>
              <h2 class="card-title">ログイン</h2>
              <!-- <p class="card-subtitle">アカウントにサインインしてください</p> -->
            </div>

          <el-form
            :model="loginForm"
            :rules="rules"
            ref="formRef"
            label-width="0"
            @submit.prevent="handleLogin"
            class="login-form"
          >
            <div class="form-field">
              <label class="field-label">ユーザー名</label>
              <el-form-item prop="username">
                <el-input
                  v-model="loginForm.username"
                  placeholder="ユーザー名またはメールアドレス"
                  size="large"
                  :prefix-icon="User"
                  clearable
                  class="form-input"
                  @keyup.enter="handleLogin"
                />
              </el-form-item>
            </div>

            <div class="form-field">
              <label class="field-label">パスワード</label>
              <el-form-item prop="password">
                <el-input
                  v-model="loginForm.password"
                  type="password"
                  placeholder="パスワードを入力"
                  size="large"
                  :prefix-icon="Lock"
                  show-password
                  clearable
                  class="form-input"
                  @keyup.enter="handleLogin"
                />
              </el-form-item>
            </div>

            <div class="form-options">
              <el-checkbox v-model="rememberMe" class="remember-checkbox">
                ログイン状態を保持
              </el-checkbox>
              <el-link
                type="primary"
                underline="never"
                class="forgot-link"
                @click="handleForgotPassword"
              >
                パスワードを忘れた場合
              </el-link>
            </div>

            <el-button
              type="primary"
              size="large"
              class="login-btn"
              :loading="loading"
              @click="handleLogin"
              native-type="submit"
            >
              <span class="btn-text">
                <template v-if="!loading">ログイン</template>
                <template v-else>ログイン中...</template>
              </span>
              <el-icon v-if="!loading" class="btn-arrow"><ArrowRight /></el-icon>
            </el-button>
          </el-form>

          <div class="login-footer">
            <div class="footer-divider">
              <span class="divider-line"></span>
              <span class="divider-text">または</span>
              <span class="divider-line"></span>
            </div>
            <div
              class="help-card"
              role="button"
              tabindex="0"
              @click="handleContactAdmin"
              @keyup.enter="handleContactAdmin"
            >
              <div class="help-icon">
                <el-icon :size="18"><Service /></el-icon>
              </div>
              <div class="help-body">
                <p class="help-title">アカウントをお持ちでない場合</p>
                <span class="help-action">システム管理者に連絡してください</span>
              </div>
              <el-icon class="help-arrow"><ArrowRight /></el-icon>
            </div>
          </div>
          </div>

          <div class="copyright">
            <p>&copy; 2026 Smart-EMAP. All rights reserved.</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted, watch, type Component } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  User,
  Lock,
  Management,
  ArrowRight,
  OfficeBuilding,
  Calendar,
  Monitor,
  UserFilled,
  Service,
} from '@element-plus/icons-vue'
import { login } from '@/modules/auth/api'
import { useUserStore } from '@/modules/auth/stores/user'
import type { FormInstance, FormRules } from 'element-plus'

const features: { key: string; tag: string; label: string; icon: Component }[] = [
  { key: 'erp', tag: 'ERP', label: '企業資源計画', icon: OfficeBuilding },
  { key: 'aps', tag: 'APS', label: '先進的計画・スケジューリング', icon: Calendar },
  { key: 'mes', tag: 'MES', label: '製造実行システム', icon: Monitor },
]

const router = useRouter()
const userStore = useUserStore()

const formRef = ref<FormInstance>()
const loading = ref(false)

const REMEMBER_ME_KEY = 'smart_emap_remember_me'
const REMEMBER_USERNAME_KEY = 'smart_emap_remember_username'
const REMEMBER_PASSWORD_KEY = 'smart_emap_remember_password'

const rememberMe = ref(localStorage.getItem(REMEMBER_ME_KEY) === 'true')

watch(rememberMe, (checked) => {
  if (checked) {
    localStorage.setItem(REMEMBER_ME_KEY, 'true')
  } else {
    localStorage.removeItem(REMEMBER_ME_KEY)
    localStorage.removeItem(REMEMBER_USERNAME_KEY)
    localStorage.removeItem(REMEMBER_PASSWORD_KEY)
  }
})

const loginForm = reactive({
  username: rememberMe.value ? localStorage.getItem(REMEMBER_USERNAME_KEY) || '' : '',
  password: rememberMe.value ? localStorage.getItem(REMEMBER_PASSWORD_KEY) || '' : '',
})

/** FastAPI の error.response.data.detail（文字列 or バリデーション配列）を表示用に整形 */
function formatApiDetail(data: unknown): string | undefined {
  if (!data || typeof data !== 'object') return undefined
  const detail = (data as { detail?: unknown }).detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((x) =>
        typeof x === 'object' && x && 'msg' in (x as object)
          ? String((x as { msg?: unknown }).msg)
          : JSON.stringify(x),
      )
      .join('；')
  }
  return undefined
}

const rules: FormRules = {
  username: [
    { required: true, message: 'ユーザー名またはメールアドレスを入力してください', trigger: 'blur' },
    { min: 3, message: 'ユーザー名は3文字以上である必要があります', trigger: 'blur' },
  ],
  password: [
    { required: true, message: 'パスワードを入力してください', trigger: 'blur' },
    { min: 6, message: 'パスワードは6文字以上である必要があります', trigger: 'blur' },
  ],
}

const handleForgotPassword = () => {
  ElMessageBox.alert('システム管理者に連絡してください', 'パスワードを忘れた場合', {
    confirmButtonText: 'OK',
    type: 'info',
  })
}

const handleContactAdmin = () => {
  ElMessageBox.alert('システム管理者に連絡してください', 'お問い合わせ', {
    confirmButtonText: 'OK',
    type: 'info',
  })
}

const handleLogin = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid: boolean) => {
    if (valid) {
      loading.value = true
      try {
        const identifierRaw = loginForm.username.trim()
        const identifier = identifierRaw.includes('@')
          ? identifierRaw.toLowerCase()
          : identifierRaw

        const response = await login({
          username: identifier,
          password: loginForm.password,
        })

        if (!response?.user) {
          console.error('ログイン応答に user が含まれていません:', response)
          throw new Error('サーバーからの応答が不正です。しばらくしてから再試行してください。')
        }

        userStore.setToken(response.access_token, rememberMe.value)
        userStore.setUser(response.user, rememberMe.value)

        if (rememberMe.value) {
          localStorage.setItem(REMEMBER_USERNAME_KEY, identifier)
          localStorage.setItem(REMEMBER_PASSWORD_KEY, loginForm.password)
        } else {
          localStorage.removeItem(REMEMBER_USERNAME_KEY)
          localStorage.removeItem(REMEMBER_PASSWORD_KEY)
        }

        try {
          const { connectWebSocket } = await import('@/modules/websocket/utils')
          connectWebSocket()
        } catch (wsError) {
          console.warn('WebSocket接続に失敗しました:', wsError)
        }

        const { startInactivityCheck } = await import('@/utils/inactivity')
        startInactivityCheck()

        const displayName = response.user.username || identifier
        ElMessage.success({
          message: `ようこそ、${displayName}さん`,
          duration: 2000,
        })

        router.push('/dashboard')
      } catch (error: unknown) {
        console.error('ログインエラー:', error)

        let errorMessage = 'ログインに失敗しました。ユーザー名とパスワードを確認してください。'

        const ax = error as { response?: { data?: unknown; status?: number }; message?: string }
        const fromDetail = ax.response?.data ? formatApiDetail(ax.response.data) : undefined
        if (fromDetail) {
          errorMessage = fromDetail
        } else if (ax.response?.data && typeof ax.response.data === 'object') {
          const msg = (ax.response.data as { message?: unknown }).message
          if (typeof msg === 'string') errorMessage = msg
        } else if (ax.response?.status === 401) {
          errorMessage =
            '認証に失敗しました（401）。DB にユーザーが存在するか、パスワードが正しいか、API（例: http://localhost:8005）が起動しているか確認してください。'
        } else if (ax.message) {
          errorMessage = ax.message
        }

        ElMessage.error({
          message: errorMessage,
          duration: 3000,
        })
      } finally {
        loading.value = false
      }
    }
  })
}

onMounted(() => {
  if (userStore.isAuthenticated) {
    router.push('/dashboard')
  }
})
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #4c5fd5 0%, #6b3fa0 50%, #764ba2 100%);
  padding: 16px;
}

.login-wrapper {
  display: flex;
  max-width: 960px;
  width: 100%;
  background: white;
  border-radius: 20px;
  box-shadow:
    0 25px 80px rgba(0, 0, 0, 0.35),
    0 0 0 1px rgba(255, 255, 255, 0.08) inset;
  overflow: hidden;
}

/* ========== Left Panel 3D ========== */
.login-left {
  flex: 1;
  position: relative;
  min-height: 520px;
  padding: 40px 32px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  overflow: hidden;
  background: linear-gradient(145deg, #1a1040 0%, #2d1b69 35%, #4c2a85 70%, #5b3d9e 100%);
  color: white;
  perspective: 1200px;
}

.left-scene {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.scene-gradient {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 80% 60% at 20% 20%, rgba(120, 180, 255, 0.25) 0%, transparent 55%),
    radial-gradient(ellipse 70% 50% at 85% 75%, rgba(200, 120, 255, 0.2) 0%, transparent 50%),
    radial-gradient(circle at 50% 100%, rgba(102, 126, 234, 0.35) 0%, transparent 45%);
}

.scene-grid {
  position: absolute;
  left: -20%;
  right: -20%;
  bottom: -5%;
  height: 55%;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.06) 1px, transparent 1px);
  background-size: 32px 32px;
  transform: perspective(400px) rotateX(68deg);
  transform-origin: center bottom;
  mask-image: linear-gradient(to top, black 0%, transparent 85%);
  animation: gridPulse 8s ease-in-out infinite;
}

@keyframes gridPulse {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 0.85; }
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(40px);
  animation: orbFloat 12s ease-in-out infinite;
}

.orb-a {
  width: 180px;
  height: 180px;
  top: 8%;
  left: -10%;
  background: rgba(99, 179, 237, 0.45);
  animation-delay: 0s;
}

.orb-b {
  width: 140px;
  height: 140px;
  top: 45%;
  right: -5%;
  background: rgba(167, 139, 250, 0.5);
  animation-delay: -4s;
}

.orb-c {
  width: 100px;
  height: 100px;
  bottom: 15%;
  left: 30%;
  background: rgba(244, 114, 182, 0.35);
  animation-delay: -7s;
}

@keyframes orbFloat {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(12px, -18px) scale(1.05); }
  66% { transform: translate(-8px, 10px) scale(0.95); }
}

.shape-cube {
  position: absolute;
  top: 18%;
  right: 12%;
  width: 48px;
  height: 48px;
  transform-style: preserve-3d;
  transform: rotateX(-18deg) rotateY(35deg);
  animation: cubeSpin 18s linear infinite;
}

.cube-face {
  position: absolute;
  width: 48px;
  height: 48px;
  border: 1px solid rgba(255, 255, 255, 0.35);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.15), rgba(255, 255, 255, 0.03));
  backdrop-filter: blur(4px);
}

.cube-front {
  transform: translateZ(24px);
}

.cube-right {
  transform: rotateY(90deg) translateZ(24px);
}

.cube-top {
  transform: rotateX(90deg) translateZ(24px);
}

@keyframes cubeSpin {
  from { transform: rotateX(-18deg) rotateY(0deg); }
  to { transform: rotateX(-18deg) rotateY(360deg); }
}

.shape-ring {
  position: absolute;
  bottom: 22%;
  right: 8%;
  width: 72px;
  height: 72px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  box-shadow:
    0 0 30px rgba(167, 139, 250, 0.3),
    inset 0 0 20px rgba(255, 255, 255, 0.05);
  animation: ringPulse 6s ease-in-out infinite;
}

@keyframes ringPulse {
  0%, 100% { transform: scale(1) rotate(0deg); opacity: 0.6; }
  50% { transform: scale(1.08) rotate(180deg); opacity: 1; }
}

.shape-diamond {
  position: absolute;
  top: 55%;
  left: 8%;
  width: 28px;
  height: 28px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.4), rgba(167, 139, 250, 0.3));
  transform: rotate(45deg);
  box-shadow: 0 8px 24px rgba(167, 139, 250, 0.4);
  animation: diamondBob 5s ease-in-out infinite;
}

@keyframes diamondBob {
  0%, 100% { transform: rotate(45deg) translateY(0); }
  50% { transform: rotate(45deg) translateY(-12px); }
}

.left-content {
  position: relative;
  z-index: 1;
}

.brand-section {
  text-align: center;
  margin-bottom: 28px;
}

.logo-stage {
  position: relative;
  width: 100px;
  height: 100px;
  margin: 0 auto 20px;
  perspective: 600px;
}

.logo-orbit {
  position: absolute;
  inset: -8px;
  border-radius: 28px;
  border: 1px dashed rgba(255, 255, 255, 0.25);
  animation: orbitSpin 20s linear infinite;
}

@keyframes orbitSpin {
  from { transform: rotateZ(0deg); }
  to { transform: rotateZ(360deg); }
}

.logo-3d {
  position: relative;
  width: 88px;
  height: 88px;
  margin: 6px auto;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 22px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.22), rgba(255, 255, 255, 0.06));
  border: 1px solid rgba(255, 255, 255, 0.35);
  box-shadow:
    0 20px 40px rgba(0, 0, 0, 0.35),
    0 0 0 1px rgba(255, 255, 255, 0.1) inset,
    0 1px 0 rgba(255, 255, 255, 0.4) inset;
  transform: rotateX(8deg) rotateY(-6deg);
  transform-style: preserve-3d;
  animation: logoFloat 6s ease-in-out infinite;
}

.logo-shine {
  position: absolute;
  top: 4px;
  left: 8px;
  right: 8px;
  height: 40%;
  border-radius: 16px 16px 50% 50%;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.35), transparent);
  pointer-events: none;
}

@keyframes logoFloat {
  0%, 100% { transform: rotateX(8deg) rotateY(-6deg) translateY(0); }
  50% { transform: rotateX(12deg) rotateY(6deg) translateY(-6px); }
}

.brand-title {
  margin: 0 0 8px;
}

.title-main {
  font-size: 30px;
  font-weight: 800;
  letter-spacing: 0.02em;
  background: linear-gradient(180deg, #fff 0%, rgba(255, 255, 255, 0.75) 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0 4px 24px rgba(167, 139, 250, 0.5);
  filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.3));
}

.brand-subtitle {
  font-size: 15px;
  font-weight: 500;
  margin: 0 0 12px;
  opacity: 0.92;
  letter-spacing: 0.04em;
}

.brand-badges {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-bottom: 14px;
}

.module-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 20px;
  letter-spacing: 0.06em;
  transform: translateZ(0);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.module-badge.erp {
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  border: 1px solid rgba(147, 197, 253, 0.5);
}

.module-badge.aps {
  background: linear-gradient(135deg, #8b5cf6, #6d28d9);
  border: 1px solid rgba(196, 181, 253, 0.5);
}

.module-badge.mes {
  background: linear-gradient(135deg, #06b6d4, #0891b2);
  border: 1px solid rgba(103, 232, 249, 0.5);
}

.brand-desc {
  font-size: 12px;
  line-height: 1.65;
  opacity: 0.78;
  margin: 0;
  max-width: 280px;
  margin-left: auto;
  margin-right: auto;
}

.features-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.feature-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 14px;
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.12) 0%,
    rgba(255, 255, 255, 0.04) 100%
  );
  border: 1px solid rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(12px);
  box-shadow:
    0 8px 24px rgba(0, 0, 0, 0.2),
    0 1px 0 rgba(255, 255, 255, 0.15) inset;
  transform: translateZ(0) perspective(800px) rotateX(0deg);
  transition:
    transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1),
    box-shadow 0.35s ease,
    border-color 0.35s ease;
  animation: cardSlideIn 0.7s cubic-bezier(0.22, 1, 0.36, 1) backwards;
  animation-delay: var(--delay, 0s);
}

@keyframes cardSlideIn {
  from {
    opacity: 0;
    transform: translateX(-20px) translateZ(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0) translateZ(0);
  }
}

.feature-card:hover {
  transform: translateX(6px) translateZ(12px) rotateX(-2deg);
  border-color: rgba(255, 255, 255, 0.35);
  box-shadow:
    0 16px 40px rgba(0, 0, 0, 0.3),
    0 0 24px rgba(167, 139, 250, 0.15);
}

.feature-icon-wrap {
  flex-shrink: 0;
  perspective: 200px;
}

.feature-icon-3d {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  transform: rotateY(-8deg);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.25);
}

.feature-card.erp .feature-icon-3d {
  background: linear-gradient(145deg, #60a5fa, #2563eb);
}

.feature-card.aps .feature-icon-3d {
  background: linear-gradient(145deg, #a78bfa, #7c3aed);
}

.feature-card.mes .feature-icon-3d {
  background: linear-gradient(145deg, #22d3ee, #0891b2);
}

.feature-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.feature-tag {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  opacity: 0.85;
}

.feature-label {
  font-size: 13px;
  font-weight: 500;
  line-height: 1.35;
}

.feature-arrow {
  flex-shrink: 0;
  opacity: 0.4;
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.feature-card:hover .feature-arrow {
  opacity: 1;
  transform: translateX(4px);
}

@media (prefers-reduced-motion: reduce) {
  .orb,
  .shape-cube,
  .shape-ring,
  .shape-diamond,
  .logo-orbit,
  .logo-3d,
  .scene-grid,
  .feature-card,
  .right-blob,
  .login-card {
    animation: none;
  }
}

/* ========== Right Panel ========== */
.login-right {
  flex: 1;
  position: relative;
  padding: 40px 36px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  overflow: hidden;
  background: linear-gradient(160deg, #f8f9ff 0%, #f1f5f9 45%, #eef2ff 100%);
}

.right-scene {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.right-blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(50px);
  animation: rightBlobFloat 14s ease-in-out infinite;
}

.blob-1 {
  width: 220px;
  height: 220px;
  top: -8%;
  right: -12%;
  background: rgba(102, 126, 234, 0.18);
}

.blob-2 {
  width: 160px;
  height: 160px;
  bottom: 10%;
  left: -8%;
  background: rgba(118, 75, 162, 0.14);
  animation-delay: -5s;
}

.blob-3 {
  width: 100px;
  height: 100px;
  top: 40%;
  right: 20%;
  background: rgba(56, 189, 248, 0.12);
  animation-delay: -9s;
}

@keyframes rightBlobFloat {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(-10px, 14px); }
}

.right-dots {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(rgba(102, 126, 234, 0.12) 1px, transparent 1px);
  background-size: 24px 24px;
  mask-image: radial-gradient(ellipse 80% 70% at 50% 50%, black 20%, transparent 75%);
  opacity: 0.6;
}

.right-content {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 380px;
  margin: 0 auto;
}

.login-card {
  position: relative;
  background: rgba(255, 255, 255, 0.88);
  border-radius: 20px;
  padding: 32px 28px 24px;
  border: 1px solid rgba(255, 255, 255, 0.9);
  box-shadow:
    0 24px 48px rgba(102, 126, 234, 0.12),
    0 8px 24px rgba(15, 23, 42, 0.06),
    0 0 0 1px rgba(102, 126, 234, 0.06);
  backdrop-filter: blur(20px);
  animation: cardFadeUp 0.65s cubic-bezier(0.22, 1, 0.36, 1) backwards;
}

@keyframes cardFadeUp {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.card-accent {
  position: absolute;
  top: 0;
  left: 24px;
  right: 24px;
  height: 3px;
  border-radius: 0 0 4px 4px;
  background: linear-gradient(90deg, #667eea, #a78bfa, #764ba2);
}

.card-glow {
  position: absolute;
  top: -40px;
  left: 50%;
  width: 200px;
  height: 80px;
  transform: translateX(-50%);
  background: radial-gradient(ellipse, rgba(102, 126, 234, 0.2), transparent 70%);
  pointer-events: none;
}

.card-header {
  text-align: center;
  margin-bottom: 28px;
}

.header-icon-wrap {
  width: 52px;
  height: 52px;
  margin: 0 auto 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  background: linear-gradient(145deg, #667eea, #764ba2);
  color: white;
  box-shadow:
    0 12px 24px rgba(102, 126, 234, 0.35),
    0 0 0 1px rgba(255, 255, 255, 0.2) inset;
  transform: perspective(400px) rotateX(6deg);
}

.card-title {
  margin: 0 0 6px;
  font-size: 26px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.02em;
}

.card-subtitle {
  margin: 0;
  font-size: 13px;
  color: #64748b;
  line-height: 1.5;
}

.login-form {
  margin-bottom: 8px;
}

.form-field {
  margin-bottom: 4px;
}

.field-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 6px;
  letter-spacing: 0.02em;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.login-form :deep(.el-form-item__error) {
  padding-top: 4px;
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 18px 0 22px;
  flex-wrap: wrap;
  gap: 8px;
}

.remember-checkbox :deep(.el-checkbox__label) {
  font-size: 13px;
  color: #475569;
}

.forgot-link {
  font-size: 13px;
  font-weight: 500;
}

.login-btn {
  width: 100%;
  height: 48px;
  border: none;
  border-radius: 12px;
  font-weight: 700;
  font-size: 15px;
  letter-spacing: 0.04em;
  background: linear-gradient(135deg, #5b6fd6 0%, #667eea 40%, #764ba2 100%);
  box-shadow:
    0 8px 24px rgba(102, 126, 234, 0.4),
    0 2px 0 rgba(255, 255, 255, 0.15) inset;
  transition:
    transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1),
    box-shadow 0.25s ease;
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow:
    0 14px 32px rgba(102, 126, 234, 0.45),
    0 2px 0 rgba(255, 255, 255, 0.2) inset;
}

.login-btn:active:not(:disabled) {
  transform: translateY(0);
}

.login-btn .btn-text {
  margin-right: 4px;
}

.login-btn .btn-arrow {
  transition: transform 0.25s ease;
}

.login-btn:hover:not(:disabled) .btn-arrow {
  transform: translateX(4px);
}

.login-footer {
  margin-top: 20px;
}

.footer-divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.divider-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
}

.divider-text {
  color: #94a3b8;
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.08em;
  white-space: nowrap;
}

.help-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 14px;
  cursor: pointer;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.06), rgba(118, 75, 162, 0.04));
  border: 1px solid rgba(102, 126, 234, 0.12);
  transition:
    transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1),
    box-shadow 0.3s ease,
    border-color 0.3s ease;
}

.help-card:hover {
  transform: translateY(-2px);
  border-color: rgba(102, 126, 234, 0.25);
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.12);
}

.help-card:focus-visible {
  outline: 2px solid #667eea;
  outline-offset: 2px;
}

.help-icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: linear-gradient(145deg, #667eea, #764ba2);
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.help-body {
  flex: 1;
  min-width: 0;
  text-align: left;
}

.help-title {
  margin: 0 0 4px;
  font-size: 12px;
  color: #64748b;
}

.help-action {
  font-size: 13px;
  font-weight: 600;
  color: #667eea;
}

.help-arrow {
  flex-shrink: 0;
  color: #94a3b8;
  transition: transform 0.25s ease, color 0.25s ease;
}

.help-card:hover .help-arrow {
  color: #667eea;
  transform: translateX(4px);
}

.copyright {
  text-align: center;
  margin-top: 20px;
}

.copyright p {
  margin: 0;
  font-size: 11px;
  color: #94a3b8;
  letter-spacing: 0.02em;
}

@media (max-width: 768px) {
  .login-wrapper {
    flex-direction: column;
  }

  .login-left {
    min-height: auto;
    padding: 32px 24px;
  }

  .login-right {
    padding: 32px 20px;
  }

  .right-content {
    max-width: 100%;
  }

  .login-card {
    padding: 24px 20px 20px;
  }

  .title-main {
    font-size: 24px;
  }

  .shape-cube,
  .shape-ring {
    display: none;
  }
}

.login-right :deep(.form-input .el-input__wrapper) {
  padding: 4px 12px;
  min-height: 46px;
  border-radius: 12px;
  background: rgba(248, 250, 252, 0.9);
  box-shadow:
    0 0 0 1px #e2e8f0 inset,
    0 2px 4px rgba(15, 23, 42, 0.02);
  transition:
    box-shadow 0.25s ease,
    background 0.25s ease,
    transform 0.25s ease;
}

.login-right :deep(.form-input .el-input__wrapper:hover) {
  background: #fff;
  box-shadow:
    0 0 0 1px #cbd5e1 inset,
    0 4px 12px rgba(102, 126, 234, 0.06);
}

.login-right :deep(.form-input.is-focus .el-input__wrapper) {
  background: #fff;
  transform: translateY(-1px);
  box-shadow:
    0 0 0 2px rgba(102, 126, 234, 0.35),
    0 8px 20px rgba(102, 126, 234, 0.12);
}

.login-right :deep(.el-input__prefix .el-icon) {
  color: #94a3b8;
  transition: color 0.2s ease;
}

.login-right :deep(.form-input.is-focus .el-input__prefix .el-icon) {
  color: #667eea;
}
</style>
