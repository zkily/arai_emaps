<template>
  <div class="actual-analysis-page">
    <header class="actual-analysis-hero">
      <div class="actual-analysis-hero__left">
        <div class="actual-analysis-hero__icon" :style="{ background: gradient }">
          <el-icon :size="22"><component :is="icon" /></el-icon>
        </div>
        <div class="actual-analysis-hero__text">
          <h1 class="actual-analysis-hero__title">{{ title }}</h1>
          <p v-if="subtitle" class="actual-analysis-hero__meta">{{ subtitle }}</p>
        </div>
      </div>
    </header>

    <el-card class="actual-analysis-card" shadow="never">
      <el-empty :description="emptyText" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import type { Component } from 'vue'

defineProps<{
  title: string
  subtitle?: string
  icon: Component
  gradient?: string
  emptyText?: string
}>()
</script>

<style scoped>
.actual-analysis-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 4px 0 24px;
}

.actual-analysis-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.actual-analysis-hero__left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.actual-analysis-hero__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  color: #fff;
}

.actual-analysis-hero__title {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  line-height: 1.3;
}

.actual-analysis-hero__meta {
  margin: 4px 0 0;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.actual-analysis-card {
  min-height: 360px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.actual-analysis-card :deep(.el-card__body) {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 320px;
}
</style>
