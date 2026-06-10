<script setup lang="ts">
import { DataLine } from '@element-plus/icons-vue'
import ActualAnalysisPlaceholder from '../ActualAnalysisPlaceholder.vue'

defineProps<{
  processName: string
  processDescription: string
}>()

defineOptions({ name: 'ProgressProcessAnalysis' })
</script>

<template>
  <ActualAnalysisPlaceholder
    :title="`${processName} — 進捗分析`"
    :subtitle="processDescription"
    :icon="DataLine"
    gradient="linear-gradient(135deg, #e6a23c, #ffc53d)"
  />
</template>
