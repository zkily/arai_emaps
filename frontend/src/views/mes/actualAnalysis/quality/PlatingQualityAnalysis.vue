<script setup lang="ts">
import QualityProcessAnalysis from './QualityProcessAnalysis.vue'

defineOptions({ name: 'MesPlatingQualityAnalysis' })
</script>

<template>
  <QualityProcessAnalysis
    process-name="メッキ工程"
    process-description="メッキ工程の品質指標を分析"
  />
</template>
