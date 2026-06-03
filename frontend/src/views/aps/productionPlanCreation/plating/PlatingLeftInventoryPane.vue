<template>
  <div class="left-inventory-pane">
    <div class="pane-head pane-head--left">
      <div class="pane-toolbar">
        <span v-if="!hideToolbarTitle" class="pane-title">メッキ前在庫</span>
        <div class="pane-control-group pane-control-group--date">
          <span class="pane-inline-label">基準日</span>
          <el-date-picker
            :model-value="inventoryDate"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="基準日"
            size="small"
            class="pp-date pp-date--pane"
            @update:model-value="emit('update:inventoryDate', $event)"
          />
          <el-button
            class="pane-nav-btn"
            size="small"
            circle
            :icon="ArrowLeft"
            title="前日"
            @click="emit('shiftDate', -1)"
          />
          <el-button
            class="pane-nav-btn"
            size="small"
            circle
            :icon="ArrowRight"
            title="翌日"
            @click="emit('shiftDate', 1)"
          />
        </div>
        <div class="pane-toolbar__end">
          <div class="pane-head-meta">
            <span class="pane-total-label">在庫合計</span>
            <span class="pane-total-value">{{ total }}</span>
          </div>
          <el-button
            v-if="showFloatAction"
            class="pane-float-btn"
            type="primary"
            plain
            size="small"
            :icon="Rank"
            title="浮動ウィンドウで表示"
            @click="emit('popOut')"
          >
            浮動
          </el-button>
        </div>
      </div>
    </div>
    <el-table
      ref="tableRef"
      v-loading="loading"
      class="pp-table pp-table--left"
      :data="rows"
      border
      stripe
      size="small"
      :height="tableHeight"
      empty-text="データがありません"
    >
      <el-table-column prop="product_name" label="製品名" min-width="120" show-overflow-tooltip />
      <el-table-column prop="plating_machine" label="メッキ治具" width="120" show-overflow-tooltip />
      <el-table-column prop="plating_efficiency" label="掛け数" width="88" align="right" show-overflow-tooltip>
        <template #default="{ row }">{{ formatKakeCell(row.plating_efficiency) }}</template>
      </el-table-column>
      <el-table-column prop="pre_plating_inventory" label="直前工程在庫" width="120" align="right" />
      <el-table-column label="必要治具本数" width="100" align="right">
        <template #default="{ row }">
          {{ calcRequiredJigCount(row) }}
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { TableInstance } from 'element-plus'
import { ArrowLeft, ArrowRight, Rank } from '@element-plus/icons-vue'

export interface LeftPaneRow {
  product_cd: string
  product_name: string
  plating_machine: string
  plating_efficiency: string
  pre_plating_prev_label: string
  pre_plating_inventory: number
}

const props = defineProps<{
  inventoryDate: string
  loading: boolean
  rows: LeftPaneRow[]
  total: number
  tableHeight: number
  showFloatAction?: boolean
  /** 浮動パネル内など、外枠にタイトルがある場合 */
  hideToolbarTitle?: boolean
  calcRequiredJigCount: (row: LeftPaneRow) => string | number
}>()

const emit = defineEmits<{
  'update:inventoryDate': [value: string]
  shiftDate: [delta: number]
  popOut: []
}>()

const tableRef = ref<TableInstance | null>(null)

function formatKakeCell(raw: string): string {
  if (!raw || raw === '—') return '—'
  const n = Number(raw)
  if (!Number.isFinite(n) || n <= 0) return '—'
  return String(Math.round(n))
}

defineExpose({ tableRef })
</script>

<style scoped>
.pane-head {
  margin-bottom: 8px;
}

.pane-head--left {
  padding: 6px 8px;
  border-radius: 10px;
  border: 1px solid color-mix(in oklab, var(--el-color-primary-light-5) 55%, var(--el-border-color-lighter));
  background: linear-gradient(
    165deg,
    color-mix(in oklab, var(--el-color-primary-light-9) 92%, #fff) 0%,
    color-mix(in oklab, var(--el-color-primary-light-9) 42%, var(--el-fill-color-blank)) 100%
  );
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.85) inset,
    0 2px 6px rgba(31, 56, 88, 0.07),
    0 1px 2px rgba(31, 56, 88, 0.04);
}

.pane-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 8px;
}

.pane-toolbar__end {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
  flex-shrink: 0;
}

.pane-title {
  flex-shrink: 0;
  margin: 0;
  padding: 2px 2px 2px 4px;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.02em;
  line-height: 1.2;
  white-space: nowrap;
  color: color-mix(in oklab, var(--el-color-primary) 82%, var(--el-text-color-primary));
  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.65);
}

.pane-control-group {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 6px 3px 8px;
  border-radius: 8px;
  border: 1px solid color-mix(in oklab, var(--el-border-color) 70%, var(--el-color-primary-light-7));
  background: linear-gradient(180deg, #fff 0%, var(--el-fill-color-blank) 100%);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 1px 3px rgba(31, 56, 88, 0.08);
}

.pane-inline-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
  line-height: 1;
}

.pp-date--pane {
  width: 124px;
}

.pp-date--pane :deep(.el-input__wrapper) {
  box-shadow: 0 1px 2px rgba(31, 56, 88, 0.06) inset;
}

.pane-nav-btn {
  flex-shrink: 0;
  border: 1px solid var(--el-border-color-lighter);
  background: linear-gradient(180deg, #fff 0%, var(--el-fill-color-light) 100%);
  box-shadow: 0 1px 2px rgba(31, 56, 88, 0.06);
}

.pane-nav-btn:hover {
  border-color: var(--el-color-primary-light-5);
  background: linear-gradient(180deg, #fff 0%, var(--el-color-primary-light-9) 100%);
}

.pane-head-meta {
  display: inline-flex;
  align-items: baseline;
  gap: 5px;
  padding: 3px 10px;
  border-radius: 999px;
  border: 1px solid color-mix(in oklab, var(--el-color-primary-light-5) 50%, var(--el-border-color-lighter));
  background: linear-gradient(180deg, #fff 0%, var(--el-color-primary-light-9) 120%);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 1px 3px rgba(31, 56, 88, 0.08);
}

.pane-total-label {
  font-size: 10px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.pane-total-value {
  font-size: 13px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--el-color-primary);
  line-height: 1.1;
}

.pane-float-btn {
  flex-shrink: 0;
  padding: 4px 8px;
  border-radius: 8px;
  font-weight: 600;
  box-shadow: 0 1px 2px rgba(31, 56, 88, 0.06);
}

.pane-float-btn:hover {
  box-shadow: 0 2px 6px rgba(31, 56, 88, 0.1);
}

.pp-table :deep(.el-table__cell) {
  padding-top: 4px;
  padding-bottom: 4px;
}

.pp-table :deep(.el-table__header .cell) {
  font-size: 12px;
  font-weight: 600;
}

.pp-table--left :deep(.el-table__header th) {
  background: color-mix(in oklab, var(--el-color-primary-light-9) 78%, var(--el-bg-color));
}

.pp-table--left :deep(.el-table__row:hover > td.el-table__cell) {
  background: color-mix(in oklab, var(--el-color-primary-light-9) 54%, transparent);
}

:deep(.table-row-draggable td) {
  cursor: grab;
}

:deep(.table-row-draggable:active td) {
  cursor: grabbing;
}
</style>
