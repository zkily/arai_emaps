<script setup lang="ts">
defineOptions({ name: 'WeldingActualDataCollection' })
</script>

<template>
  <div class="mes-actual-data-collection-page">
    <el-card shadow="never">
      <template #header>
        <span>溶接実績収集</span>
      </template>
      <el-empty description="準備中" />
    </el-card>
  </div>
</template>

<style scoped>
.mes-actual-data-collection-page {
  padding: 16px;
}
</style>
