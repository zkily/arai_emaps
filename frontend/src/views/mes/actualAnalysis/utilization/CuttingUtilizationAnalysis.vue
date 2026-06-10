<script setup lang="ts">
import UtilizationProcessAnalysis from './UtilizationProcessAnalysis.vue'

defineOptions({ name: 'MesCuttingUtilizationAnalysis' })
</script>

<template>
  <UtilizationProcessAnalysis
    process-name="切断工程"
    process-description="切断工程の稼働状況を分析"
  />
</template>
