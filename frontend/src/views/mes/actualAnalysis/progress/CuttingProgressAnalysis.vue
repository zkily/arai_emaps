<script setup lang="ts">
import ProgressProcessAnalysis from './ProgressProcessAnalysis.vue'

defineOptions({ name: 'MesCuttingProgressAnalysis' })
</script>

<template>
  <ProgressProcessAnalysis
    process-name="切断工程"
    process-description="切断工程の計画対比進捗を分析"
  />
</template>
