<script setup lang="ts">
import QualityProcessAnalysis from './QualityProcessAnalysis.vue'

defineOptions({ name: 'MesChamferingQualityAnalysis' })
</script>

<template>
  <QualityProcessAnalysis
    process-name="面取工程"
    process-description="面取工程の品質指標を分析"
  />
</template>
