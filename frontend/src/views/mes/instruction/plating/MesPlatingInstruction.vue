<script setup lang="ts">
import PlatingInstruction from '../../../erp/production/instruction/plating/PlatingInstruction.vue'

/**
 * MES メッキ指示：
 * UI は ERP メッキ指示を再利用する。
 */
defineOptions({ name: 'MesPlatingInstruction' })
</script>

<template>
  <div class="mes-plating-instruction">
    <PlatingInstruction />
  </div>
</template>

<style scoped>
.mes-plating-instruction :deep(.instruction-page) {
  padding: 0;
}
</style>
