<script setup lang="ts">
import QualityProcessAnalysis from './QualityProcessAnalysis.vue'

defineOptions({ name: 'MesCuttingQualityAnalysis' })
</script>

<template>
  <QualityProcessAnalysis
    process-name="切断工程"
    process-description="切断工程の品質指標を分析"
  />
</template>
