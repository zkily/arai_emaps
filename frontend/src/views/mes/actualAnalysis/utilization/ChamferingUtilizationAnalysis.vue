<script setup lang="ts">
import UtilizationProcessAnalysis from './UtilizationProcessAnalysis.vue'

defineOptions({ name: 'MesChamferingUtilizationAnalysis' })
</script>

<template>
  <UtilizationProcessAnalysis
    process-name="面取工程"
    process-description="面取工程の稼働状況を分析"
  />
</template>
