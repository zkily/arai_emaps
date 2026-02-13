<template>
  <div class="surface-instruction">
    <div class="page-header">
      <h2>面取指示</h2>
      <p class="subtitle">面取工程の指示書発行・進捗管理</p>
    </div>
    <el-card shadow="never">
      <p class="placeholder-text">面取指示の機能はここに実装します。</p>
    </el-card>
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: 'SurfaceInstruction' })
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
.page-header h2 { margin: 0 0 4px 0; font-size: 18px; }
.subtitle { margin: 0; color: var(--el-text-color-secondary); font-size: 13px; }
.placeholder-text { margin: 0; color: var(--el-text-color-secondary); }
</style>
