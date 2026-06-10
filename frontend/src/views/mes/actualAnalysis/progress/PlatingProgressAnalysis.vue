<script setup lang="ts">
import ProgressProcessAnalysis from './ProgressProcessAnalysis.vue'

defineOptions({ name: 'MesPlatingProgressAnalysis' })
</script>

<template>
  <ProgressProcessAnalysis
    process-name="メッキ工程"
    process-description="メッキ工程の計画対比進捗を分析"
  />
</template>
