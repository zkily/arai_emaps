<template>
  <div class="inventory-table">
    <el-table
      :data="data"
      stripe
      size="small"
      highlight-current-row
      class="data-table"
      v-loading="loading"
      element-loading-background="rgba(255, 255, 255, 0.7)"
      :default-sort="currentSort"
      :cell-style="getCellStyle"
      table-layout="auto"
      @sort-change="handleSortChange"
    >
      <template #empty>
        <el-empty description="該当する棚卸データがありません" :image-size="80" />
      </template>

      <el-table-column label="項目" prop="item" width="100" align="center">
        <template #default="scope">
          <span class="color-pill item-type-tag" :style="pillStyle(getItemColor(scope.row.item))">
            {{ scope.row.item }}
          </span>
        </template>
      </el-table-column>

      <el-table-column
        label="製品CD"
        prop="product_cd"
        width="90"
        align="center"
      >
        <template #default="scope">
          <div class="product-cd">{{ scope.row.product_cd }}</div>
        </template>
      </el-table-column>

      <el-table-column
        label="製品名"
        prop="product_name"
        min-width="180"
        sortable="custom"
      >
        <template #default="scope">
          <div class="product-name-cell">
            <span class="product-name">{{ scope.row.product_name }}</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="工程名" prop="process_name" min-width="100" align="center">
        <template #default="scope">
          <span
            class="color-pill process-pill"
            :style="pillStyle(getProcessColor(scope.row.process_cd))"
            :title="scope.row.process_cd"
          >
            <span class="pill-dot" />
            {{ scope.row.process_name || scope.row.process_cd }}
          </span>
        </template>
      </el-table-column>

      <el-table-column
        label="日付"
        prop="log_date"
        width="120"
        align="center"
        sortable="custom"
      >
        <template #default="scope">
          <div class="date-cell">{{ formatDate(scope.row.log_date) }}</div>
        </template>
      </el-table-column>

      <el-table-column label="時間" prop="log_time" width="100" align="center">
        <template #default="scope">
          <div class="time-cell">{{ formatLogTime(scope.row.log_time) }}</div>
        </template>
      </el-table-column>

      <el-table-column label="入数" prop="pack_qty" width="80" align="center">
        <template #default="scope">
          <div class="quantity-per-case-cell">{{ scope.row.pack_qty || '-' }}</div>
        </template>
      </el-table-column>

      <el-table-column label="箱数" prop="case_qty" width="80" align="center">
        <template #default="scope">
          <div class="case-count-cell">{{ scope.row.case_qty || '-' }}</div>
        </template>
      </el-table-column>

      <el-table-column
        label="数量"
        prop="quantity"
        width="90"
        align="center"
      >
        <template #default="scope">
          <div class="total-quantity-cell" :class="getQuantityClass(scope.row)">
            {{ Number(scope.row.quantity ?? 0).toLocaleString() }}
          </div>
        </template>
      </el-table-column>

      <el-table-column label="作業者" prop="worker_name" width="90" align="center">
        <template #default="scope">
          <div class="worker-name-cell">
            <span class="worker-name">{{ scope.row.worker_name || scope.row.remarks || '-' }}</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="更新日時" prop="updated_at" width="180" align="center">
        <template #default="scope">
          <div class="datetime-cell">{{ formatDateTime(scope.row.updated_at) }}</div>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="100" align="center" fixed="right">
        <template #default="scope">
          <el-button
            type="danger"
            size="small"
            plain
            :icon="Delete"
            class="delete-button"
            :loading="props.deletingId === scope.row.id"
            @click="handleDelete(scope.row)"
          >
            削除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination-wrapper">
      <el-pagination
        layout="total, sizes, prev, pager, next, jumper"
        :total="pagination.total"
        :page-size="pagination.pageSize"
        :current-page="pagination.page"
        :page-sizes="[10, 20, 50, 100]"
        @size-change="$emit('size-change', $event)"
        @current-change="$emit('page-change', $event)"
        background
        class="custom-pagination"
      />
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed } from 'vue'
import { Delete } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { getItemColor, getProcessColor, type ColorToken } from './inventoryColors'

// 定义props
interface Props {
  data: any[]
  loading: boolean
  pagination: {
    page: number
    pageSize: number
    total: number
  }
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
  deletingId?: number | null
}

// 定义emits
interface Emits {
  (e: 'page-change', page: number): void
  (e: 'size-change', size: number): void
  (e: 'sort', field: string, order: 'asc' | 'desc' | null): void
  (e: 'delete', row: any): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 计算当前排序状态
const currentSort = computed(() => {
  if (!props.sortBy) return undefined
  return {
    prop: props.sortBy,
    order: (props.sortOrder === 'asc' ? 'ascending' : 'descending') as 'ascending' | 'descending',
  }
})

// 格式化日期
const formatDate = (val: string) => dayjs(val).format('YYYY-MM-DD')

// 时间列仅展示 inventory_logs.log_time，显示为 HH:mm:ss。
const formatLogTime = (val: unknown) => {
  if (val === null || val === undefined) return '-'
  const raw = String(val).trim()
  if (!raw) return '-'

  // 兼容纯数字时间：秒数（如 48309）或 Excel 小数时间
  if (/^\d+(\.\d+)?$/.test(raw)) {
    const num = Number(raw)
    if (Number.isFinite(num) && num >= 0) {
      const toHms = (totalSeconds: number) => {
        const normalized = ((Math.floor(totalSeconds) % 86400) + 86400) % 86400
        const hh = String(Math.floor(normalized / 3600)).padStart(2, '0')
        const mm = String(Math.floor((normalized % 3600) / 60)).padStart(2, '0')
        const ss = String(normalized % 60).padStart(2, '0')
        return `${hh}:${mm}:${ss}`
      }

      // 1~86400 视为“秒”
      if (num >= 1 && num <= 86400) return toHms(num)
      // 0~1 视为“天的小数”（Excel 时间）
      if (num >= 0 && num < 1) return toHms(num * 86400)
      // >86400：若包含小数，取小数部分作为当天时间（Excel 日期时间）
      const fraction = num - Math.floor(num)
      if (fraction > 0) return toHms(fraction * 86400)
      return '00:00:00'
    }
  }

  // 兼容 "HH:mm:ss" / "HH:mm" / "YYYY-MM-DD HH:mm:ss" / "YYYY-MM-DDTHH:mm:ss"
  const timePart = raw.includes('T') ? raw.split('T').pop() || '' : raw.split(' ').pop() || raw
  const hhmmss = timePart.split('.')[0]

  if (/^\d{2}:\d{2}:\d{2}$/.test(hhmmss)) return hhmmss
  if (/^\d{2}:\d{2}$/.test(hhmmss)) return `${hhmmss}:00`

  let parsed = dayjs(hhmmss, 'HH:mm:ss', true)
  if (!parsed.isValid()) parsed = dayjs(hhmmss, 'HH:mm', true)
  return parsed.isValid() ? parsed.format('HH:mm:ss') : raw
}

// 格式化日期时间
const formatDateTime = (val: string) => dayjs(val).format('YYYY-MM-DD HH:mm:ss')

const pillStyle = (c: ColorToken) => ({
  color: c.color,
  background: c.bg,
  borderColor: c.border,
})

// 行左端に項目色のライン
const getCellStyle = ({ row, columnIndex }: { row: any; columnIndex: number }) =>
  columnIndex === 0 ? { boxShadow: `inset 3px 0 0 ${getItemColor(row.item).color}` } : {}

// 获取数量样式类
const getQuantityClass = (row: any): string => {
  if (row.quantity <= 0) return 'out-of-stock'
  if (row.quantity <= 10) return 'low-stock'
  return 'normal-stock'
}

// 排序处理（服务端全量排序，前端仅透传排序字段和方向）
const handleSortChange = (sortInfo: {
  prop?: string
  order?: 'ascending' | 'descending' | null
}) => {
  if (!sortInfo?.prop) return
  const order =
    sortInfo.order === 'ascending' ? 'asc' : sortInfo.order === 'descending' ? 'desc' : null
  emit('sort', sortInfo.prop, order)
}

const handleDelete = (row: any) => {
  emit('delete', row)
}
</script>

<style scoped>
.inventory-table {
  width: 100%;
}

.data-table {
  --el-table-row-hover-bg-color: rgba(79, 70, 229, 0.05);
  --el-table-current-row-bg-color: rgba(79, 70, 229, 0.08);
  --el-table-border-color: rgba(15, 23, 42, 0.06);
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.data-table :deep(.el-table__header th.el-table__cell) {
  background: linear-gradient(180deg, #f8fafc, #f1f5f9) !important;
  color: #475569;
  font-weight: 700;
  font-size: 11.5px;
  letter-spacing: 0.02em;
  border-bottom: 1px solid rgba(15, 23, 42, 0.1);
  padding: 8px 8px;
}

.data-table :deep(.el-table__row--striped td.el-table__cell) {
  background: #fafbfd;
}

.data-table :deep(.el-table__cell) {
  padding: 6px 8px;
  font-size: 12px;
  line-height: 1.35;
}

.data-table :deep(.el-table__body .el-table__row) {
  height: 36px;
}

.color-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid transparent;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.5;
  white-space: nowrap;
}

.pill-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.item-type-tag {
  border-radius: 6px;
}

.product-cd,
.hd-no-cell,
.quantity-per-case-cell,
.case-count-cell,
.time-cell {
  font-weight: 500;
  color: #334155;
}

.product-name-cell {
  padding: 0 4px;
}

.product-name {
  color: #0f172a;
  font-weight: 500;
}

.date-cell {
  font-weight: 500;
  color: #334155;
}

.total-quantity-cell {
  display: inline-block;
  min-width: 48px;
  padding: 1px 8px;
  border-radius: 6px;
  font-weight: 700;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.total-quantity-cell.normal-stock {
  color: #047857;
  background: rgba(16, 185, 129, 0.1);
}

.total-quantity-cell.low-stock {
  color: #b45309;
  background: rgba(245, 158, 11, 0.12);
}

.total-quantity-cell.out-of-stock {
  color: #dc2626;
  background: rgba(239, 68, 68, 0.1);
}

.remarks-cell {
  color: #606266;
  font-size: 12px;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.datetime-cell {
  font-weight: 500;
  color: #334155;
  font-size: 12px;
}

.delete-button {
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 600;
}

.delete-button:hover {
  box-shadow: 0 2px 8px rgba(245, 108, 108, 0.22);
}

.pagination-wrapper {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
  padding: 2px 0 0;
}

.custom-pagination {
  font-size: 12px;
  --el-color-primary: #4f46e5;
}

.custom-pagination :deep(.el-pagination__jump) {
  margin-left: 10px;
}

.custom-pagination :deep(.btn-next),
.custom-pagination :deep(.btn-prev) {
  min-width: 26px;
  height: 26px;
  border-radius: 6px;
}

.custom-pagination :deep(.el-pager li) {
  min-width: 26px;
  height: 26px;
  line-height: 26px;
  border-radius: 6px;
}

@media (max-width: 1200px) {
  .data-table {
    font-size: 12px;
  }

  .item-type-tag {
    font-size: 11px;
    padding: 2px 5px;
  }

  .delete-button {
    font-size: 11px;
    padding: 3px 8px;
  }
}

@media (max-width: 768px) {
  .pagination-wrapper {
    justify-content: center;
  }

  .custom-pagination :deep(.el-pagination__sizes) {
    display: none;
  }

  .data-table :deep(.el-table__cell) {
    padding: 4px 6px;
    font-size: 11px;
  }
}

@media (max-width: 480px) {
  .item-type-tag {
    font-size: 10px;
    padding: 1px 4px;
  }

  .delete-button {
    font-size: 10px;
    padding: 2px 6px;
  }

  .remarks-cell {
    max-width: 100px;
  }
}
</style>
