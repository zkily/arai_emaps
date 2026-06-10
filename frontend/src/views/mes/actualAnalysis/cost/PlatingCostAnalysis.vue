<script setup lang="ts">
import CostProcessAnalysis from './CostProcessAnalysis.vue'

defineOptions({ name: 'MesPlatingCostAnalysis' })
</script>

<template>
  <CostProcessAnalysis
    process-name="メッキ工程"
    process-description="メッキ工程のコスト・原価を分析"
  />
</template>
