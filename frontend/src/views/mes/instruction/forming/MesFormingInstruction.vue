<script setup lang="ts">
import FormingInstruction from '../../../erp/production/instruction/forming/FormingInstruction.vue'

/**
 * MES 成型指示：UI は ERP 成型指示と同一コンポーネント。
 * データはルート meta.useApsSchedulePlanData により production_schedules + schedule_details を参照。
 */
defineOptions({ name: 'MesFormingInstruction' })
</script>
<template>
  <div class="mes-forming-instruction">
    <FormingInstruction />
  </div>
</template>

<style scoped>
.mes-forming-instruction :deep(.molding-instruction-container) {
  padding: 0;
}

.mes-forming-instruction :deep(.molding-instruction-container .page-header) {
  padding: 8px 12px;
  margin-bottom: 0;
}

.mes-forming-instruction :deep(.molding-instruction-container .plan-section) {
  margin-bottom: 8px;
}

.mes-forming-instruction :deep(.molding-instruction-container .search-bar) {
  padding: 6px 10px;
}

/* 移除：設備運行時間設定（入口按钮 + 弹窗） */
.mes-forming-instruction :deep([data-work-time-config-button]),
.mes-forming-instruction :deep([data-work-time-config-dialog]),
.mes-forming-instruction :deep([data-work-time-config-form-dialog]) {
  display: none !important;
}
</style>
