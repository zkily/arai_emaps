<script setup lang="ts">
import CostProcessAnalysis from './CostProcessAnalysis.vue'

defineOptions({ name: 'MesWeldingCostAnalysis' })
</script>

<template>
  <CostProcessAnalysis
    process-name="溶接工程"
    process-description="溶接工程のコスト・原価を分析"
  />
</template>
