<template>
  <div class="redirect-container">
    <el-icon class="loading-icon" :size="48"><Loading /></el-icon>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Loading } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

onMounted(() => {
  const { params } = route
  const path = '/' + (params.path as string)
  router.replace(path)
})
</script>

<style scoped>
.redirect-container {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 200px;
}

.loading-icon {
  animation: rotate 1s linear infinite;
  color: #409eff;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
