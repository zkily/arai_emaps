<script setup lang="ts">
import UtilizationProcessAnalysis from './UtilizationProcessAnalysis.vue'

defineOptions({ name: 'MesInspectionUtilizationAnalysis' })
</script>

<template>
  <UtilizationProcessAnalysis
    process-name="検査工程"
    process-description="検査工程の稼働状況を分析"
  />
</template>
