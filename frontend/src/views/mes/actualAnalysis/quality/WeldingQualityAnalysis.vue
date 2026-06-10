<script setup lang="ts">
import QualityProcessAnalysis from './QualityProcessAnalysis.vue'

defineOptions({ name: 'MesWeldingQualityAnalysis' })
</script>

<template>
  <QualityProcessAnalysis
    process-name="溶接工程"
    process-description="溶接工程の品質指標を分析"
  />
</template>
