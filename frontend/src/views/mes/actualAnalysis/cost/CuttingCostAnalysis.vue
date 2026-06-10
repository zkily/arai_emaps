<script setup lang="ts">
import CostProcessAnalysis from './CostProcessAnalysis.vue'

defineOptions({ name: 'MesCuttingCostAnalysis' })
</script>

<template>
  <CostProcessAnalysis
    process-name="切断工程"
    process-description="切断工程のコスト・原価を分析"
  />
</template>
