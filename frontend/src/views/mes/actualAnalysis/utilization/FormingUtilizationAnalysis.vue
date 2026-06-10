<script setup lang="ts">
import UtilizationProcessAnalysis from './UtilizationProcessAnalysis.vue'

defineOptions({ name: 'MesFormingUtilizationAnalysis' })
</script>

<template>
  <UtilizationProcessAnalysis
    process-name="成型工程"
    process-description="成型工程の稼働状況を分析"
  />
</template>
