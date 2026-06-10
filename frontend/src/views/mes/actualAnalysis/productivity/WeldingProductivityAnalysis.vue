<script setup lang="ts">
import ProductivityProcessAnalysis from './ProductivityProcessAnalysis.vue'

defineOptions({ name: 'MesWeldingProductivityAnalysis' })
</script>

<template>
  <ProductivityProcessAnalysis
    process-name="溶接工程"
    process-description="溶接工程の生産性指標を分析"
  />
</template>
