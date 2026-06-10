<script setup lang="ts">
import { CircleCheck } from '@element-plus/icons-vue'
import ActualAnalysisPlaceholder from './ActualAnalysisPlaceholder.vue'

defineOptions({ name: 'MesQualityAnalysis' })
</script>

<template>
  <ActualAnalysisPlaceholder
    title="品質分析"
    subtitle="不良・検査実績に基づく品質指標を分析"
    :icon="CircleCheck"
    gradient="linear-gradient(135deg, #9254de, #b37feb)"
  />
</template>
