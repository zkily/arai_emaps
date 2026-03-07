<template>
  <div class="login-container">
    <div class="login-wrapper">
      <!-- Left Panel - Branding -->
      <div class="login-left">
        <div class="brand-section">
          <div class="brand-logo">
            <el-icon :size="40"><Management /></el-icon>
          </div>
          <h1 class="brand-title">Smart-EMAP</h1>
          <p class="brand-subtitle">生産管理システム (ERP+APS+MES)</p>
          <p class="brand-desc">製造業のDXを実現する次世代統合管理システム</p>
        </div>
        <div class="features-list">
          <div class="feature-item">
            <div class="feature-check">
              <el-icon><Check /></el-icon>
            </div>
            <span>ERP - 企業資源計画</span>
          </div>
          <div class="feature-item">
            <div class="feature-check">
              <el-icon><Check /></el-icon>
            </div>
            <span>APS - 先進的計画・スケジューリング</span>
          </div>
          <div class="feature-item">
            <div class="feature-check">
              <el-icon><Check /></el-icon>
            </div>
            <span>MES - 製造実行システム</span>
          </div>
        </div>
      </div>

      <!-- Right Panel - Login Form -->
      <div class="login-right">
        <div class="login-card">
          <div class="card-header">
            <h2>ログイン</h2>
            <p>アカウントにサインインしてください</p>
          </div>

          <el-form
            :model="loginForm"
            :rules="rules"
            ref="formRef"
            label-width="0"
            @submit.prevent="handleLogin"
            class="login-form"
          >
            <el-form-item prop="username">
              <el-input
                v-model="loginForm.username"
                placeholder="ユーザー名またはメールアドレス"
                size="large"
                :prefix-icon="User"
                clearable
                @keyup.enter="handleLogin"
              />
            </el-form-item>

            <el-form-item prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="パスワード"
                size="large"
                :prefix-icon="Lock"
                show-password
                clearable
                @keyup.enter="handleLogin"
              />
            </el-form-item>

            <div class="form-options">
              <el-checkbox v-model="rememberMe">ログイン状態を保持</el-checkbox>
              <el-link type="primary" underline="never" class="forgot-link">
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
              <span v-if="!loading">ログイン</span>
              <span v-else>ログイン中...</span>
            </el-button>
          </el-form>

          <div class="login-footer">
            <el-divider>
              <span class="divider-text">または</span>
            </el-divider>
            <div class="help-text">
              <p>アカウントをお持ちでない場合</p>
              <el-link type="primary" underline="never">
                システム管理者に連絡してください
              </el-link>
            </div>
          </div>
        </div>

        <div class="copyright">
          <p>&copy; 2026 Smart-EMAP. All rights reserved.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  User,
  Lock,
  Management,
  Check,
} from '@element-plus/icons-vue'
import { login } from '@/modules/auth/api'
import { useUserStore } from '@/modules/auth/stores/user'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const rememberMe = ref(false)

const REMEMBER_USERNAME_KEY = 'smart_emap_remember_username'
const REMEMBER_PASSWORD_KEY = 'smart_emap_remember_password'

const loginForm = reactive({
  username: '',
  password: '',
})

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

const handleLogin = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid: boolean) => {
    if (valid) {
      loading.value = true
      try {
        const response = await login({
          username: loginForm.username.trim(),
          password: loginForm.password,
        })

        if (!response?.user) {
          console.error('ログイン応答に user が含まれていません:', response)
          throw new Error('サーバーからの応答が不正です。しばらくしてから再試行してください。')
        }

        userStore.setToken(response.access_token, rememberMe.value)
        userStore.setUser(response.user, rememberMe.value)

        if (rememberMe.value) {
          localStorage.setItem(REMEMBER_USERNAME_KEY, loginForm.username.trim())
          localStorage.setItem(REMEMBER_PASSWORD_KEY, loginForm.password)
        } else {
          localStorage.removeItem(REMEMBER_USERNAME_KEY)
          localStorage.removeItem(REMEMBER_PASSWORD_KEY)
        }

        // WebSocket接続（エラーがあってもログインを続行）
        try {
          const { connectWebSocket } = await import('@/modules/websocket/utils')
          connectWebSocket()
        } catch (wsError) {
          console.warn('WebSocket接続に失敗しました:', wsError)
        }

        // 2 小时无操作自动登出，有操作则重置计时
        const { startInactivityCheck } = await import('@/utils/inactivity')
        startInactivityCheck()

        const displayName = response.user.username || loginForm.username.trim()
        ElMessage.success({
          message: `ようこそ、${displayName}さん`,
          duration: 2000,
        })

        const redirect = router.currentRoute.value.query.redirect as string
        router.push(redirect || '/dashboard')
      } catch (error: any) {
        console.error('ログインエラー:', error)
        
        let errorMessage = 'ログインに失敗しました。ユーザー名とパスワードを確認してください。'
        
        if (error?.response?.data?.detail) {
          errorMessage = error.response.data.detail
        } else if (error?.response?.data?.message) {
          errorMessage = error.response.data.message
        } else if (error?.message) {
          errorMessage = error.message
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
  const savedRememberMe = localStorage.getItem('smart_emap_remember_me')
  if (savedRememberMe === 'true') {
    rememberMe.value = true
    const savedUsername = localStorage.getItem(REMEMBER_USERNAME_KEY)
    const savedPassword = localStorage.getItem(REMEMBER_PASSWORD_KEY)
    if (savedUsername) loginForm.username = savedUsername
    if (savedPassword) loginForm.password = savedPassword
  }

  if (userStore.isAuthenticated) {
    const redirect = router.currentRoute.value.query.redirect as string
    router.push(redirect || '/dashboard')
  }
})
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 16px;
}

.login-wrapper {
  display: flex;
  max-width: 900px;
  width: 100%;
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

/* Left Panel */
.login-left {
  flex: 1;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 40px 36px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.brand-section {
  text-align: center;
}

.brand-logo {
  width: 72px;
  height: 72px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  backdrop-filter: blur(10px);
}

.brand-title {
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 8px;
}

.brand-subtitle {
  font-size: 14px;
  margin: 0 0 12px;
  opacity: 0.9;
}

.brand-desc {
  font-size: 13px;
  line-height: 1.6;
  opacity: 0.8;
  margin: 0;
}

.features-list {
  margin-top: 32px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  font-size: 14px;
}

.feature-check {
  width: 24px;
  height: 24px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

/* Right Panel */
.login-right {
  flex: 1;
  padding: 40px 36px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  background: #fafafa;
}

.login-card {
  background: white;
  border-radius: 12px;
  padding: 28px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.card-header {
  text-align: center;
  margin-bottom: 24px;
}

.card-header h2 {
  margin: 0 0 6px;
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
}

.card-header p {
  margin: 0;
  font-size: 13px;
  color: #64748b;
}

.login-form {
  margin-bottom: 20px;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 16px;
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.forgot-link {
  font-size: 13px;
}

.login-btn {
  width: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  font-weight: 600;
  height: 44px;
}

.login-btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.4);
}

.login-footer {
  margin-top: 16px;
}

.divider-text {
  color: #94a3b8;
  font-size: 12px;
}

.help-text {
  text-align: center;
  margin-top: 16px;
}

.help-text p {
  margin: 0 0 6px;
  color: #94a3b8;
  font-size: 13px;
}

.copyright {
  text-align: center;
  margin-top: 24px;
}

.copyright p {
  margin: 0;
  font-size: 11px;
  color: #94a3b8;
}

/* Responsive */
@media (max-width: 768px) {
  .login-wrapper {
    flex-direction: column;
  }

  .login-left {
    padding: 32px 24px;
  }

  .login-right {
    padding: 32px 24px;
  }

  .brand-title {
    font-size: 24px;
  }
}

/* Form Styles */
:deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px #e2e8f0 inset;
  transition: all 0.2s;
  border-radius: 8px;
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #cbd5e1 inset;
}

:deep(.el-input.is-focus .el-input__wrapper) {
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.3) inset;
}
</style>
