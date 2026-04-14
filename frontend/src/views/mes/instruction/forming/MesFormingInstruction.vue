<script setup lang="ts">
import FormingInstruction from '../../../erp/production/instruction/forming/FormingInstruction.vue'

/**
 * MES 成型指示：UI は ERP 成型指示と同一コンポーネント。
 * データはルート meta.useApsSchedulePlanData により production_schedules + schedule_details を参照。
 */
defineOptions({ name: 'MesFormingInstruction' })
</script>
<template>
  <FormingInstruction />
</template>
