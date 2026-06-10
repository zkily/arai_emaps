<script setup lang="ts">
import { CircleCheck } from '@element-plus/icons-vue'
import ActualAnalysisPlaceholder from '../ActualAnalysisPlaceholder.vue'

defineProps<{
  processName: string
  processDescription: string
}>()

defineOptions({ name: 'QualityProcessAnalysis' })
</script>

<template>
  <ActualAnalysisPlaceholder
    :title="`${processName} — 品質分析`"
    :subtitle="processDescription"
    :icon="CircleCheck"
    gradient="linear-gradient(135deg, #9254de, #b37feb)"
  />
</template>
