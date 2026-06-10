<script setup lang="ts">
import ProductivityProcessAnalysis from './ProductivityProcessAnalysis.vue'

defineOptions({ name: 'MesCuttingProductivityAnalysis' })
</script>

<template>
  <ProductivityProcessAnalysis
    process-name="切断工程"
    process-description="切断工程の生産性指標を分析"
  />
</template>
