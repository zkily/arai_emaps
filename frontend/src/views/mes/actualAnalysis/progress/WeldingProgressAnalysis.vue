<script setup lang="ts">
import ProgressProcessAnalysis from './ProgressProcessAnalysis.vue'

defineOptions({ name: 'MesWeldingProgressAnalysis' })
</script>

<template>
  <ProgressProcessAnalysis
    process-name="溶接工程"
    process-description="溶接工程の計画対比進捗を分析"
  />
</template>
