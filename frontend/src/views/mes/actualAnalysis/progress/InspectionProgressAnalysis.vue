<script setup lang="ts">
import ProgressProcessAnalysis from './ProgressProcessAnalysis.vue'

defineOptions({ name: 'MesInspectionProgressAnalysis' })
</script>

<template>
  <ProgressProcessAnalysis
    process-name="検査工程"
    process-description="検査工程の計画対比進捗を分析"
  />
</template>
