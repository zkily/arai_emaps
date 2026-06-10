<script setup lang="ts">
import { Coin } from '@element-plus/icons-vue'
import ActualAnalysisPlaceholder from '../ActualAnalysisPlaceholder.vue'

defineProps<{
  processName: string
  processDescription: string
}>()

defineOptions({ name: 'CostProcessAnalysis' })
</script>

<template>
  <ActualAnalysisPlaceholder
    :title="`${processName} — コスト分析`"
    :subtitle="processDescription"
    :icon="Coin"
    gradient="linear-gradient(135deg, #f56c6c, #ff7875)"
  />
</template>
