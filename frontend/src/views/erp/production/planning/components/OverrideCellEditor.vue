<template>
  <el-dialog
    :model-value="visible"
    :title="t('formingDailyPlan.overrideTitle')"
    width="360px"
    append-to-body
    @update:model-value="emit('update:visible', $event)"
  >
    <el-form label-width="80px" size="small">
      <el-form-item :label="t('formingDailyPlan.colProduct')">
        <span>{{ productCd }}</span>
      </el-form-item>
      <el-form-item :label="t('formingDailyPlan.colProcess')">
        <span>{{ processLabel(processKey) }}</span>
      </el-form-item>
      <el-form-item :label="t('formingDailyPlan.colDate')">
        <span>{{ date }}</span>
      </el-form-item>
      <el-form-item :label="t('formingDailyPlan.overrideQty')">
        <el-input-number v-model="localValue" :min="0" :step="1" :disabled="readonly" controls-position="right" class="w-full" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button size="small" @click="emit('update:visible', false)">{{ t('common.cancel') }}</el-button>
      <el-button v-if="!readonly" size="small" type="warning" plain @click="clearOverride">{{ t('formingDailyPlan.clearOverride') }}</el-button>
      <el-button v-if="!readonly" size="small" type="primary" @click="save">{{ t('common.confirm') }}</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { processLabel } from './formingDailyPlanConstants'

const props = defineProps<{
  visible: boolean
  productCd: string
  processKey: string
  date: string
  value: number
  readonly?: boolean
}>()

const emit = defineEmits<{
  'update:visible': [v: boolean]
  save: [payload: { value: number | null }]
}>()

const { t } = useI18n()
const localValue = ref(props.value)

watch(() => props.value, (v) => { localValue.value = v })
watch(() => props.visible, (v) => { if (v) localValue.value = props.value })

function save() {
  emit('save', { value: localValue.value })
  emit('update:visible', false)
}

function clearOverride() {
  emit('save', { value: null })
  emit('update:visible', false)
}
</script>

<style scoped>
.w-full { width: 100%; }
</style>
