<script setup lang="ts">
import ProductivityProcessAnalysis from './ProductivityProcessAnalysis.vue'

defineOptions({ name: 'MesPlatingProductivityAnalysis' })
</script>

<template>
  <ProductivityProcessAnalysis
    process-name="メッキ工程"
    process-description="メッキ工程の生産性指標を分析"
  />
</template>
