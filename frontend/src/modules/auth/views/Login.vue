<template>
  <div class="login-container">
    <div class="login-wrapper">
      <!-- 左側：ロゴと説明 -->
      <div class="login-left">
        <div class="logo-section">
          <div class="logo-icon">
            <el-icon :size="60"><Management /></el-icon>
          </div>
          <h1 class="system-title">生産管理システム</h1>
          <p class="system-subtitle">Smart-EMAP (ERP+APS+MES)</p>
          <p class="system-description">
            製造業のデジタルトランスフォーメーションを実現する<br />
            次世代統合管理システム
          </p>
        </div>
        <div class="features-list">
          <div class="feature-item">
            <el-icon><Check /></el-icon>
            <span>ERP - 企業資源計画</span>
          </div>
          <div class="feature-item">
            <el-icon><Check /></el-icon>
            <span>APS - 先進的計画・スケジューリング</span>
          </div>
          <div class="feature-item">
            <el-icon><Check /></el-icon>
            <span>MES - 製造実行システム</span>
          </div>
        </div>
      </div>

      <!-- 右側：ログインフォーム -->
      <div class="login-right">
        <el-card class="login-card" shadow="never">
          <template #header>
            <div class="card-header">
              <h2>ログイン</h2>
              <p class="header-subtitle">アカウントにログインしてください</p>
            </div>
          </template>

          <el-form
            :model="loginForm"
            :rules="rules"
            ref="formRef"
            label-width="0"
            @submit.prevent="handleLogin"
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

            <el-form-item>
              <div class="form-options">
                <el-checkbox v-model="rememberMe">ログイン状態を保持</el-checkbox>
                <el-link type="primary" underline="never" class="forgot-link">
                  パスワードを忘れた場合
                </el-link>
              </div>
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                size="large"
                style="width: 100%"
                :loading="loading"
                @click="handleLogin"
                native-type="submit"
              >
                <span v-if="!loading">ログイン</span>
                <span v-else>ログイン中...</span>
              </el-button>
            </el-form-item>
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
        </el-card>

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
import { connectWebSocket } from '@/modules/websocket/utils'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const rememberMe = ref(false)

const loginForm = reactive({
  username: '',
  password: '',
})

// バリデーションルール
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

// ログイン処理
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

        // WebSocket接続を確立
        connectWebSocket()

        const displayName = response.user.username || loginForm.username.trim()
        ElMessage.success({
          message: `ようこそ、${displayName}さん`,
          duration: 2000,
        })

        // リダイレクト先を確認（ログイン前にアクセスしようとしたページ）
        const redirect = router.currentRoute.value.query.redirect as string
        router.push(redirect || '/dashboard')
      } catch (error: any) {
        console.error('ログインエラー:', error)
        
        // エラーメッセージの取得（優先順位: detail > message > デフォルト）
        let errorMessage = 'ログインに失敗しました。ユーザー名とパスワードを確認してください。'
        
        if (error?.response?.data?.detail) {
          // バックエンドから返された詳細エラーメッセージ
          errorMessage = error.response.data.detail
        } else if (error?.response?.data?.message) {
          errorMessage = error.response.data.message
        } else if (error?.message) {
          errorMessage = error.message
        }
        
        // エラーメッセージを表示
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

// ページ読み込み時に保存されたログイン情報を復元
onMounted(() => {
  const savedRememberMe = localStorage.getItem('smart_emap_remember_me')
  if (savedRememberMe === 'true') {
    rememberMe.value = true
  }

  // 既にログインしている場合はダッシュボードにリダイレクト
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
  padding: 20px;
}

.login-wrapper {
  display: flex;
  max-width: 1200px;
  width: 100%;
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

/* 左側パネル */
.login-left {
  flex: 1;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 60px 50px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.logo-section {
  text-align: center;
}

.logo-icon {
  margin-bottom: 20px;
  opacity: 0.9;
}

.system-title {
  font-size: 32px;
  font-weight: bold;
  margin: 0 0 10px 0;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
}

.system-subtitle {
  font-size: 18px;
  margin: 0 0 20px 0;
  opacity: 0.9;
}

.system-description {
  font-size: 14px;
  line-height: 1.8;
  opacity: 0.8;
  margin: 0;
}

.features-list {
  margin-top: 40px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  font-size: 16px;
}

.feature-item .el-icon {
  font-size: 20px;
}

/* 右側パネル */
.login-right {
  flex: 1;
  padding: 60px 50px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  background: #fafafa;
}

.login-card {
  background: white;
  border: none;
}

.login-card :deep(.el-card__header) {
  border-bottom: 1px solid #e4e7ed;
  padding: 30px 30px 20px;
}

.login-card :deep(.el-card__body) {
  padding: 30px;
}

.card-header {
  text-align: center;
}

.card-header h2 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 28px;
  font-weight: 600;
}

.header-subtitle {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.forgot-link {
  font-size: 14px;
}

.login-footer {
  margin-top: 20px;
}

.divider-text {
  color: #909399;
  font-size: 12px;
  padding: 0 10px;
}

.help-text {
  text-align: center;
  margin-top: 20px;
}

.help-text p {
  margin: 0 0 8px 0;
  color: #909399;
  font-size: 14px;
}

.copyright {
  text-align: center;
  margin-top: 30px;
  color: #909399;
  font-size: 12px;
}

.copyright p {
  margin: 0;
}

/* レスポンシブデザイン */
@media (max-width: 768px) {
  .login-wrapper {
    flex-direction: column;
  }

  .login-left {
    padding: 40px 30px;
  }

  .login-right {
    padding: 40px 30px;
  }

  .system-title {
    font-size: 24px;
  }

  .system-subtitle {
    font-size: 16px;
  }
}

/* フォーム要素のスタイル */
:deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px #dcdfe6 inset;
  transition: all 0.3s;
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #c0c4cc inset;
}

:deep(.el-input.is-focus .el-input__wrapper) {
  box-shadow: 0 0 0 1px #409eff inset;
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  font-weight: 500;
  transition: all 0.3s;
}

:deep(.el-button--primary:hover) {
  opacity: 0.9;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}
</style>

