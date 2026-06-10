<script setup lang="ts">
import { TrendCharts } from '@element-plus/icons-vue'
import ActualAnalysisPlaceholder from '../ActualAnalysisPlaceholder.vue'

defineProps<{
  processName: string
  processDescription: string
}>()

defineOptions({ name: 'ProductivityProcessAnalysis' })
</script>

<template>
  <ActualAnalysisPlaceholder
    :title="`${processName} — 生産性分析`"
    :subtitle="processDescription"
    :icon="TrendCharts"
    gradient="linear-gradient(135deg, #409eff, #36cfc9)"
  />
</template>
