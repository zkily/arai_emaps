<script setup lang="ts">
import { Coin } from '@element-plus/icons-vue'
import ActualAnalysisPlaceholder from './ActualAnalysisPlaceholder.vue'

defineOptions({ name: 'MesCostAnalysis' })
</script>

<template>
  <ActualAnalysisPlaceholder
    title="コスト分析"
    subtitle="工程・製品別の原価・コストを分析"
    :icon="Coin"
    gradient="linear-gradient(135deg, #f56c6c, #ff7875)"
  />
</template>
