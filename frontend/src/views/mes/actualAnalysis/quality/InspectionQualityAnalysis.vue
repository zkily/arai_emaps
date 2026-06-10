<script setup lang="ts">
import QualityProcessAnalysis from './QualityProcessAnalysis.vue'

defineOptions({ name: 'MesInspectionQualityAnalysis' })
</script>

<template>
  <QualityProcessAnalysis
    process-name="検査工程"
    process-description="検査工程の品質指標を分析"
  />
</template>
