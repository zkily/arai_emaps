<script setup lang="ts">
import CostProcessAnalysis from './CostProcessAnalysis.vue'

defineOptions({ name: 'MesInspectionCostAnalysis' })
</script>

<template>
  <CostProcessAnalysis
    process-name="検査工程"
    process-description="検査工程のコスト・原価を分析"
  />
</template>
