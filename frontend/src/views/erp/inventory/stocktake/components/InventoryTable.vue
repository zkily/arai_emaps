<template>
  <div class="inventory-table">
    <el-table
      :data="data"
      border
      stripe
      highlight-current-row
      class="data-table"
      v-loading="loading"
      element-loading-spinner="el-icon-loading"
      element-loading-background="rgba(0, 0, 0, 0.8)"
      :default-sort="currentSort"
      :sort-method="null"
      table-layout="auto"
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
        width="120"
        align="center"
        sortable
        @sort-change="handleProductCdSort"
      >
        <template #default="scope">
          <div class="product-cd">{{ scope.row.product_cd }}</div>
        </template>
      </el-table-column>

      <el-table-column
        label="製品名"
        prop="product_name"
        min-width="160"
        sortable
        @sort-change="handleProductNameSort"
      >
        <template #default="scope">
          <div class="product-name-cell">
            <span class="product-name">{{ scope.row.product_name }}</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="工程名" prop="process_name" width="120" align="center">
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
        sortable
        @sort-change="handleDateSort"
      >
        <template #default="scope">
          <div class="date-cell">{{ formatDate(scope.row.log_date) }}</div>
        </template>
      </el-table-column>

      <el-table-column label="時間" prop="log_time" width="100" align="center">
        <template #default="scope">
          <div class="time-cell">{{ formatTime(scope.row.log_time) }}</div>
        </template>
      </el-table-column>

      <el-table-column label="入数" prop="pack_qty" width="80" align="center">
        <template #default="scope">
          <div class="quantity-per-case-cell">{{ scope.row.pack_qty || '-' }}</div>
        </template>
      </el-table-column>

      <el-table-column label="ケース数" prop="case_qty" width="100" align="center">
        <template #default="scope">
          <div class="case-count-cell">{{ scope.row.case_qty || '-' }}</div>
        </template>
      </el-table-column>

      <el-table-column
        label="数量"
        prop="quantity"
        width="100"
        align="center"
        sortable
        @sort-change="handleQuantitySort"
      >
        <template #default="scope">
          <div class="total-quantity-cell" :class="getQuantityClass(scope.row)">
            {{ scope.row.quantity }}
          </div>
        </template>
      </el-table-column>

      <el-table-column label="作業者" prop="worker_name" width="100" align="center">
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

      <el-table-column label="操作" width="120" align="center" fixed="right">
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
  (e: 'sort', field: string): void
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

// 格式化时间
const formatTime = (val: string) => dayjs(val, 'HH:mm:ss').format('HH:mm')

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

// 排序处理函数 - 强制服务端排序
const handleProductNameSort = (sortInfo: any) => {
  // 阻止默认的客户端排序行为
  if (sortInfo) {
    emit('sort', 'product_name')
  }
}

const handleProductCdSort = (sortInfo: any) => {
  // 阻止默认的客户端排序行为
  if (sortInfo) {
    emit('sort', 'product_cd')
  }
}

const handleQuantitySort = (sortInfo: any) => {
  // 阻止默认的客户端排序行为
  if (sortInfo) {
    emit('sort', 'quantity')
  }
}

const handleDateSort = (sortInfo: any) => {
  // 阻止默认的客户端排序行为
  if (sortInfo) {
    emit('sort', 'log_date')
  }
}

const handleDelete = (row: any) => {
  emit('delete', row)
}
</script>

<style scoped>
.inventory-table {
  width: 100%;
}

/* 数据表格样式 */
.data-table {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.data-table :deep(.el-table__header) {
  background: linear-gradient(135deg, #f8f9fa, #e9ecef);
}

.data-table :deep(.el-table__header th) {
  background: transparent;
  color: #2c3e50;
  font-weight: 600;
  border-bottom: 2px solid #667eea;
}

.data-table :deep(.el-table__row) {
  transition: all 0.3s ease;
}

.data-table :deep(.el-table__row:hover) {
  background-color: rgba(102, 126, 234, 0.05);
  transform: scale(1.001);
}

/* 表格单元格样式 */
.item-type-tag {
  font-weight: 600;
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 12px;
}

.product-cd,
.hd-no-cell,
.quantity-per-case-cell,
.case-count-cell,
.time-cell {
  font-weight: 500;
  color: #2c3e50;
}

.product-name-cell {
  padding: 0 8px;
}

.product-name {
  color: #2c3e50;
  font-weight: 500;
}

.date-cell {
  font-weight: 500;
  color: #2c3e50;
}

.total-quantity-cell {
  font-weight: 700;
  font-size: 14px;
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
  font-size: 13px;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.datetime-cell {
  font-weight: 500;
  color: #2c3e50;
  font-size: 13px;
}

.edit-button,
.delete-button {
  border-radius: 6px;
  padding: 4px 12px;
  font-size: 12px;
  transition: all 0.3s ease;
}

.edit-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.delete-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(245, 108, 108, 0.3);
}

/* 分页样式 */
.pagination-wrapper {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
  padding: 16px 0;
}

.custom-pagination {
  border-radius: 8px;
}

.custom-pagination :deep(.el-pagination__jump) {
  margin-left: 16px;
}

.custom-pagination :deep(.btn-next),
.custom-pagination :deep(.btn-prev) {
  border-radius: 6px;
  transition: all 0.3s ease;
}

.custom-pagination :deep(.btn-next:hover),
.custom-pagination :deep(.btn-prev:hover) {
  transform: translateY(-1px);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .data-table {
    font-size: 13px;
  }

  .item-type-tag {
    font-size: 11px;
    padding: 3px 6px;
  }

  .edit-button,
  .delete-button {
    font-size: 11px;
    padding: 3px 8px;
  }
}

@media (max-width: 768px) {
  .data-table {
    font-size: 12px;
  }

  .pagination-wrapper {
    justify-content: center;
  }

  .custom-pagination :deep(.el-pagination__sizes) {
    display: none;
  }
}

@media (max-width: 480px) {
  .data-table {
    font-size: 11px;
  }

  .item-type-tag {
    font-size: 10px;
    padding: 2px 4px;
  }

  .edit-button,
  .delete-button {
    font-size: 10px;
    padding: 2px 6px;
  }

  .remarks-cell {
    max-width: 100px;
  }
}
</style>
