<template>
  <div class="access-denied">
    <el-card shadow="hover" class="access-denied-card">
      <h1>アクセス権限がありません</h1>
      <p>このページを表示する権限がありません。管理者にお問い合わせください。</p>
      <el-button type="primary" @click="goHome">ダッシュボードへ戻る</el-button>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

function goHome() {
  router.push('/dashboard')
}
</script>

<style scoped>
.access-denied {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  padding: 24px;
}

.access-denied-card {
  max-width: 480px;
  text-align: center;
}

.access-denied-card h1 {
  margin: 0 0 12px;
  font-size: 20px;
}

.access-denied-card p {
  margin: 0 0 20px;
  color: var(--el-text-color-secondary);
  line-height: 1.6;
}
</style>
