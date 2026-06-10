<script setup lang="ts">
import { DataLine } from '@element-plus/icons-vue'
import ActualAnalysisPlaceholder from './ActualAnalysisPlaceholder.vue'

defineOptions({ name: 'MesProgressAnalysis' })
</script>

<template>
  <ActualAnalysisPlaceholder
    title="進捗分析"
    subtitle="計画対比の生産進捗を分析"
    :icon="DataLine"
    gradient="linear-gradient(135deg, #e6a23c, #ffc53d)"
  />
</template>
