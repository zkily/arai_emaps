<template>
  <div class="inventory-table">
    <el-table
      :data="data"
      border
      stripe
      size="small"
      highlight-current-row
      class="data-table"
      v-loading="loading"
      element-loading-spinner="el-icon-loading"
      element-loading-background="rgba(0, 0, 0, 0.8)"
      :default-sort="currentSort"
      table-layout="auto"
      @sort-change="handleSortChange"
    >
      <el-table-column label="項目" prop="item" width="100" align="center">
        <template #default="scope">
          <el-tag :type="getItemTypeColor(scope.row.item)" effect="light" class="item-type-tag">
            {{ scope.row.item }}
          </el-tag>
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

      <el-table-column label="工程名" prop="process_name" width="90" align="center">
        <template #default="scope">
          <el-tag :type="getProcessTypeColor(scope.row.process_cd)" size="small">
            {{ scope.row.process_name || scope.row.process_cd }}
          </el-tag>
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
            {{ scope.row.quantity }}
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

// 获取項目类型颜色
const getItemTypeColor = (type: string): 'success' | 'warning' | 'info' | 'primary' | 'danger' => {
  switch (type) {
    case '材料棚卸':
      return 'success'
    case '部品棚卸':
      return 'warning'
    case '製品棚卸':
      return 'primary'
    default:
      return 'info'
  }
}

// 获取工程CD颜色
const getProcessTypeColor = (
  processCd: string,
): 'success' | 'warning' | 'info' | 'primary' | 'danger' => {
  switch (processCd) {
    case '13':
      return 'success'
    case '14':
      return 'warning'
    case '15':
      return 'primary'
    case '16':
      return 'danger'
    default:
      return 'info'
  }
}

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
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.data-table :deep(.el-table__header) {
  background: #f8fafc;
}

.data-table :deep(.el-table__header th) {
  background: transparent !important;
  color: #334155;
  font-weight: 600;
  border-bottom: 1px solid rgba(15, 23, 42, 0.1);
  padding: 6px 8px;
  font-size: 12px;
}

.data-table :deep(.el-table__row) {
  transition: background-color 0.15s ease;
}

.data-table :deep(.el-table__row:hover) {
  background-color: rgba(14, 165, 233, 0.06);
}

.data-table :deep(.el-table__cell) {
  padding: 5px 8px;
  font-size: 12px;
  line-height: 1.35;
}

.data-table :deep(.el-table__body .el-table__row) {
  height: 34px;
}

.item-type-tag {
  font-weight: 600;
  border-radius: 5px;
  padding: 2px 6px;
  font-size: 11px;
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
  font-weight: 700;
  font-size: 12px;
}

.total-quantity-cell.normal-stock {
  color: #67c23a;
}

.total-quantity-cell.low-stock {
  color: #e6a23c;
}

.total-quantity-cell.out-of-stock {
  color: #f56c6c;
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
  margin-top: 8px;
  display: flex;
  justify-content: flex-end;
  padding: 2px 0 0;
}

.custom-pagination {
  font-size: 12px;
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
