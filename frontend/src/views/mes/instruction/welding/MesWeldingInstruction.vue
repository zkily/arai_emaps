<script setup lang="ts">
import WeldingInstruction from '../../../erp/production/instruction/welding/WeldingInstruction.vue'

/**
 * MES 溶接指示：
 * UI は ERP 溶接指示を再利用する。
 */
defineOptions({ name: 'MesWeldingInstruction' })
</script>

<template>
  <div class="mes-welding-instruction">
    <WeldingInstruction />
  </div>
</template>

<style scoped>
.mes-welding-instruction :deep(.instruction-page) {
  padding: 0;
}
</style>
