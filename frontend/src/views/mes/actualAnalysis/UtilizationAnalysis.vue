<script setup lang="ts">
import { Monitor } from '@element-plus/icons-vue'
import ActualAnalysisPlaceholder from './ActualAnalysisPlaceholder.vue'

defineOptions({ name: 'MesUtilizationAnalysis' })
</script>

<template>
  <ActualAnalysisPlaceholder
    title="稼働率分析"
    subtitle="設備・工程別の稼働状況を分析"
    :icon="Monitor"
    gradient="linear-gradient(135deg, #67c23a, #95de64)"
  />
</template>
