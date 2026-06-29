<template>
  <div class="fdp-matrix">
    <div class="fdp-matrix__toolbar">
      <el-select
        v-model="localProduct"
        filterable
        clearable
        size="small"
        :placeholder="t('formingDailyPlan.filterProduct')"
        class="fdp-matrix__product"
        @change="emit('product-change', localProduct)"
      >
        <el-option v-for="p in products" :key="p.product_cd" :label="`${p.product_cd} ${p.product_name || ''}`" :value="p.product_cd" />
      </el-select>
      <el-select v-model="localProcesses" multiple collapse-tags size="small" :placeholder="t('formingDailyPlan.filterProcess')" class="fdp-matrix__process">
        <el-option v-for="p in processOptions" :key="p.key" :label="p.label" :value="p.key" />
      </el-select>
      <el-button size="small" type="success" plain :disabled="!rows.length" @click="emit('export')">
        {{ t('formingDailyPlan.exportExcel') }}
      </el-button>
    </div>
    <div class="table-frame">
      <el-table
        v-loading="loading"
        :data="filteredRows"
        stripe
        border
        size="small"
        class="fdp-matrix__table"
        :max-height="520"
        :empty-text="t('formingDailyPlan.noData')"
      >
        <el-table-column prop="product_cd" :label="t('formingDailyPlan.colProduct')" width="100" fixed show-overflow-tooltip />
        <el-table-column prop="process_key" :label="t('formingDailyPlan.colProcess')" width="80" fixed>
          <template #default="{ row }">
            <span class="fdp-matrix__proc">
              <i class="fdp-matrix__dot" :style="{ background: processColor(row.process_key) }" />
              {{ processLabel(row.process_key) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column v-for="d in dates" :key="d" :label="d.slice(5)" width="64" align="right">
          <template #default="{ row }">
            <span
              class="fdp-cell"
              :class="cellClass(row, d)"
              @click="onCellClick(row, d)"
            >
              {{ cellDisplay(row, d) }}
            </span>
          </template>
        </el-table-column>
      </el-table>
    </div>
    <OverrideCellEditor
      v-model:visible="editorVisible"
      :product-cd="editTarget.productCd"
      :process-key="editTarget.processKey"
      :date="editTarget.date"
      :value="editTarget.value"
      :readonly="editTarget.readonly"
      @save="onOverrideSave"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import type { DailyMatrixRow } from '@/api/formingDailyPlan'
import { FORMING_PLAN_PROCESS_OPTIONS, fmtFormingNumber, isMoldingReadonly, processColor, processLabel } from './formingDailyPlanConstants'
import OverrideCellEditor from './OverrideCellEditor.vue'

const props = defineProps<{
  loading?: boolean
  dates: string[]
  rows: DailyMatrixRow[]
  products: { product_cd: string; product_name?: string }[]
  selectedProduct?: string
  selectedProcesses?: string[]
}>()

const emit = defineEmits<{
  'product-change': [value: string | undefined]
  'override-save': [payload: { productCd: string; processKey: string; date: string; value: number | null }]
  export: []
}>()

const { t } = useI18n()
const localProduct = ref(props.selectedProduct)
const localProcesses = ref<string[]>(props.selectedProcesses ?? FORMING_PLAN_PROCESS_OPTIONS.map((p) => p.key))
const processOptions = FORMING_PLAN_PROCESS_OPTIONS.filter((p) => p.key !== 'warehouse')

watch(() => props.selectedProduct, (v) => { localProduct.value = v })

const filteredRows = computed(() => {
  let list = props.rows
  if (localProduct.value) {
    list = list.filter((r) => r.product_cd === localProduct.value)
  }
  if (localProcesses.value.length) {
    list = list.filter((r) => localProcesses.value.includes(r.process_key))
  }
  return list
})

const editorVisible = ref(false)
const editTarget = ref({ productCd: '', processKey: '', date: '', value: 0, readonly: false })

function cellDisplay(row: DailyMatrixRow, d: string) {
  const cell = row.by_date?.[d]
  if (!cell) return ''
  const v = cell.override_plan ?? cell.final_plan ?? cell.derived_plan ?? 0
  return fmtFormingNumber(v)
}

function cellClass(row: DailyMatrixRow, d: string) {
  const cell = row.by_date?.[d]
  const cls: string[] = []
  if (isMoldingReadonly(row.process_key)) cls.push('is-readonly')
  if (cell?.override_plan != null) cls.push('is-override')
  return cls
}

function onCellClick(row: DailyMatrixRow, d: string) {
  if (isMoldingReadonly(row.process_key)) return
  const cell = row.by_date?.[d]
  editTarget.value = {
    productCd: row.product_cd,
    processKey: row.process_key,
    date: d,
    value: cell?.override_plan ?? cell?.final_plan ?? cell?.derived_plan ?? 0,
    readonly: false,
  }
  editorVisible.value = true
}

function onOverrideSave(payload: { value: number | null }) {
  emit('override-save', {
    productCd: editTarget.value.productCd,
    processKey: editTarget.value.processKey,
    date: editTarget.value.date,
    value: payload.value,
  })
}
</script>

<style scoped>
.fdp-matrix__toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 6px;
  align-items: center;
  padding: 6px 8px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}
.fdp-matrix__product { width: 200px; }
.fdp-matrix__process { width: 168px; }
.fdp-matrix__table :deep(.el-table__header th) {
  background: #f1f5f9 !important;
  color: #475569;
  font-size: 11px;
  padding: 4px 0;
}
.fdp-matrix__table :deep(.el-table__cell) {
  padding: 2px 0;
  font-size: 11px;
}
.fdp-cell {
  cursor: pointer;
  display: block;
  font-variant-numeric: tabular-nums;
  padding: 1px 2px;
  border-radius: 3px;
}
.fdp-cell:hover:not(.is-readonly) {
  background: rgba(99, 102, 241, 0.08);
}
.fdp-cell.is-readonly {
  color: #94a3b8;
  cursor: default;
}
.fdp-cell.is-override {
  color: #4f46e5;
  font-weight: 700;
  background: rgba(99, 102, 241, 0.1);
}
.fdp-matrix__proc {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
}
.fdp-matrix__dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}
</style>
