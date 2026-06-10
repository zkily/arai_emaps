<script setup lang="ts">
import UtilizationProcessAnalysis from './UtilizationProcessAnalysis.vue'

defineOptions({ name: 'MesPlatingUtilizationAnalysis' })
</script>

<template>
  <UtilizationProcessAnalysis
    process-name="メッキ工程"
    process-description="メッキ工程の稼働状況を分析"
  />
</template>
