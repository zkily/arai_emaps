<script setup lang="ts">
import { Odometer } from '@element-plus/icons-vue'
import ActualAnalysisPlaceholder from '../ActualAnalysisPlaceholder.vue'

defineProps<{
  processName: string
  processDescription: string
}>()

defineOptions({ name: 'UtilizationProcessAnalysis' })
</script>

<template>
  <ActualAnalysisPlaceholder
    :title="`${processName} — 稼働率分析`"
    :subtitle="processDescription"
    :icon="Odometer"
    gradient="linear-gradient(135deg, #67c23a, #95de64)"
  />
</template>
