<script setup lang="ts">
import QualityProcessAnalysis from './QualityProcessAnalysis.vue'

defineOptions({ name: 'MesFormingQualityAnalysis' })
</script>

<template>
  <QualityProcessAnalysis
    process-name="成型工程"
    process-description="成型工程の品質指標を分析"
  />
</template>
