<script setup lang="ts">
import UtilizationProcessAnalysis from './UtilizationProcessAnalysis.vue'

defineOptions({ name: 'MesWeldingUtilizationAnalysis' })
</script>

<template>
  <UtilizationProcessAnalysis
    process-name="溶接工程"
    process-description="溶接工程の稼働状況を分析"
  />
</template>
