<template>
  <el-drawer
    :model-value="visible"
    :title="t('formingDailyPlan.scenarioManage')"
    size="420px"
    append-to-body
    @update:model-value="emit('update:visible', $event)"
  >
    <div class="fdp-scenario">
      <el-button type="primary" size="small" @click="emit('create')">{{ t('formingDailyPlan.newScenario') }}</el-button>
      <el-table :data="scenarios" size="small" stripe class="fdp-scenario__table" @row-click="(row: FormingPlanScenario) => emit('select', row)">
        <el-table-column prop="name" :label="t('formingDailyPlan.scenarioName')" show-overflow-tooltip />
        <el-table-column prop="status" :label="t('formingDailyPlan.scenarioStatus')" width="72" />
        <el-table-column :label="t('formingDailyPlan.actions')" width="100">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click.stop="emit('apply', row)">{{ t('formingDailyPlan.apply') }}</el-button>
            <el-button link type="danger" size="small" @click.stop="emit('delete', row)">{{ t('formingDailyPlan.delete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { FormingPlanScenario } from '@/api/formingDailyPlan'

defineProps<{
  visible: boolean
  scenarios: FormingPlanScenario[]
}>()

const emit = defineEmits<{
  'update:visible': [v: boolean]
  create: []
  select: [row: FormingPlanScenario]
  apply: [row: FormingPlanScenario]
  delete: [row: FormingPlanScenario]
}>()

const { t } = useI18n()
</script>

<style scoped>
.fdp-scenario__table {
  margin-top: 10px;
}
</style>
