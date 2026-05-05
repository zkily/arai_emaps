<script setup lang="ts">
import CuttingInstruction from '../../../erp/production/instruction/cutting/CuttingInstruction.vue'

/**
 * MES 切断・面取指示：
 * UI は ERP 切断・面取指示を再利用する。
 */
defineOptions({ name: 'MesCuttingInstruction' })
</script>

<template>
  <div class="mes-cutting-instruction">
    <CuttingInstruction />
  </div>
</template>

<style scoped>
.mes-cutting-instruction :deep(.instruction-page) {
  padding: 0;
}
</style>
