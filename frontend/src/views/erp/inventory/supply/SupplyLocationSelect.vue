<template>
  <el-select
    :model-value="modelValue"
    filterable
    clearable
    placeholder="保管場所を選択"
    style="width: 100%"
    @update:model-value="(v: string | undefined) => emit('update:modelValue', v ?? '')"
  >
    <el-option v-for="item in options" :key="item.value" :label="item.label" :value="item.value" />
    <template v-if="canManage" #footer>
      <el-button text size="small" class="location-manage-btn" @click="emit('manage')">
        <el-icon><Setting /></el-icon>
        保管場所を追加・編集
      </el-button>
    </template>
  </el-select>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Setting } from '@element-plus/icons-vue'
import type { SupplyPartLocation } from '@/api/erp/supplyParts'

const props = defineProps<{
  modelValue: string
  locations: SupplyPartLocation[]
  keepValue?: string | null
  canManage?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  manage: []
}>()

const options = computed(() => {
  const list = props.locations
    .filter((item) => item.is_active)
    .map((item) => ({ value: item.name, label: item.name }))
  const keep = (props.keepValue || '').trim()
  if (keep && !list.some((item) => item.value === keep)) {
    list.unshift({ value: keep, label: `${keep}（使用停止）` })
  }
  return list
})
</script>

<style scoped>
.location-manage-btn {
  width: 100%;
  justify-content: flex-start;
  color: #0f766e;
  font-weight: 600;
}
.location-manage-btn .el-icon {
  margin-right: 4px;
}
</style>
