<template>
  <div class="inventory-carryover-history">
    <!-- 筛选区 -->
    <el-card class="filter-card" shadow="hover">
      <div class="filter-header">
        <div class="filter-title">
          <el-icon><ZoomIn /></el-icon>
          繰越履歴検索
        </div>
      </div>
      <div class="filter-content">
        <div class="filter-row">
          <div class="filter-item">
            <label class="filter-label">繰越月份</label>
            <el-date-picker
              v-model="filterParams.carryoverMonth"
              type="month"
              placeholder="繰越月份を選択"
              format="YYYY-MM"
              value-format="YYYY-MM"
              class="filter-input"
              clearable
            />
          </div>
          <div class="filter-item">
            <label class="filter-label">工程</label>
            <el-select
              v-model="filterParams.process_cd"
              placeholder="工程を選択"
              class="filter-input"
              clearable
              filterable
              :loading="processLoading"
            >
              <el-option
                v-for="process in processOptions"
                :key="process.value"
                :label="process.label"
                :value="process.value"
              />
            </el-select>
          </div>
          <div class="filter-item">
            <label class="filter-label">製品名/コード</label>
            <el-input
              v-model="filterParams.product_cd"
              placeholder="製品名またはコードを入力"
              class="filter-input"
              clearable
            />
          </div>
          <div class="filter-item">
            <label class="filter-label">取引種別</label>
            <el-select
              v-model="filterParams.transaction_type"
              placeholder="取引種別を選択"
              class="filter-input"
              clearable
            >
              <el-option label="初期" value="初期" />
              <el-option label="入庫" value="入庫" />
              <el-option label="出庫" value="出庫" />
              <el-option label="調整" value="調整" />
              <el-option label="棚卸" value="棚卸" />
            </el-select>
          </div>
          <div class="filter-actions">
            <el-button @click="clearFilters" class="clear-btn">
              <el-icon><Refresh /></el-icon>
              クリア
            </el-button>
            <el-button type="primary" @click="handleSearch" class="search-btn" :loading="loading">
              <el-icon><Search /></el-icon>
              検索
            </el-button>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 数据列表区 -->
    <el-card class="data-card" shadow="hover">
      <div class="data-header">
        <div class="data-title">
          <el-icon><Document /></el-icon>
          繰越履歴リスト
          <span class="data-count" v-if="total > 0">({{ total }}件)</span>
        </div>
        <div class="data-actions">
          <el-button @click="handleAdd" type="primary" class="add-btn">
            <el-icon><Plus /></el-icon>
            新規追加
          </el-button>
          <el-button @click="handleExport" class="export-btn" :loading="exportLoading">
            <el-icon><Download /></el-icon>
            エクスポート
          </el-button>
        </div>
      </div>

      <div class="table-container">
        <el-table
          :data="historyData"
          v-loading="loading"
          stripe
          highlight-current-row
          class="history-table modern-table"
          @sort-change="handleSortChange"
        >
          <el-table-column prop="target_cd" label="製品コード" width="130" align="center">
            <template #header>
              <div class="table-header">
                <div class="header-left">
                  <el-icon><Box /></el-icon>
                  <span>製品CD</span>
                </div>
                <div class="header-right"></div>
              </div>
            </template>
            <template #default="{ row }">
              <div class="product-code">{{ row.target_cd }}</div>
            </template>
          </el-table-column>
          <el-table-column prop="product_name" label="品名" min-width="130" show-overflow-tooltip>
            <template #header>
              <div class="table-header">
                <div class="header-left">
                  <el-icon><Document /></el-icon>
                  <span>製品名</span>
                </div>
                <div class="header-right">
                  <el-icon
                    class="sort-icon"
                    :class="{
                      'sort-active': sortConfig.prop === 'product_name',
                      'sort-asc':
                        sortConfig.prop === 'product_name' && sortConfig.order === 'ascending',
                      'sort-desc':
                        sortConfig.prop === 'product_name' && sortConfig.order === 'descending',
                    }"
                    @click="handleCustomSort('product_name')"
                  >
                    <Sort />
                  </el-icon>
                </div>
              </div>
            </template>
            <template #default="{ row }">
              <div class="product-name">{{ row.product_name }}</div>
            </template>
          </el-table-column>
          <el-table-column prop="stock_type" label="在庫種別" width="120" align="center">
            <template #header>
              <div class="table-header">
                <div class="header-left">
                  <el-icon><Collection /></el-icon>
                  <span>在庫種別</span>
                </div>
                <div class="header-right"></div>
              </div>
            </template>
            <template #default="{ row }">
              <el-tag
                :type="getStockTypeTagType(row.stock_type)"
                size="small"
                class="stock-type-tag"
              >
                {{ row.stock_type }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="location_cd" label="保管場所" width="120" align="center">
            <template #header>
              <div class="table-header">
                <div class="header-left">
                  <el-icon><Location /></el-icon>
                  <span>保管場所</span>
                </div>
                <div class="header-right"></div>
              </div>
            </template>
            <template #default="{ row }">
              <el-tag type="info" size="small" class="location-tag">{{ row.location_cd }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="process_cd" label="工程CD" width="120" align="center">
            <template #header>
              <div class="table-header">
                <div class="header-left">
                  <el-icon><Setting /></el-icon>
                  <span>工程CD</span>
                </div>
                <div class="header-right"></div>
              </div>
            </template>
            <template #default="{ row }">
              <div class="process-code">{{ row.process_cd }}</div>
            </template>
          </el-table-column>
          <el-table-column prop="transaction_type" label="取引種別" width="120" align="center">
            <template #header>
              <div class="table-header">
                <div class="header-left">
                  <el-icon><Operation /></el-icon>
                  <span>取引種別</span>
                </div>
                <div class="header-right"></div>
              </div>
            </template>
            <template #default="{ row }">
              <el-tag
                :type="getTransactionTypeTagType(row.transaction_type || '初期')"
                size="small"
                class="transaction-tag"
              >
                {{ row.transaction_type || '初期' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="quantity" label="数量" width="130" align="center">
            <template #header>
              <div class="table-header">
                <div class="header-left">
                  <el-icon><Operation /></el-icon>
                  <span>数量</span>
                </div>
                <div class="header-right"></div>
              </div>
            </template>
            <template #default="{ row }">
              <div class="quantity-value">{{ formatNumber(row.quantity) }}</div>
            </template>
          </el-table-column>
          <el-table-column prop="unit" label="単位" width="100" align="center">
            <template #header>
              <div class="table-header">
                <div class="header-left">
                  <el-icon><ScaleToOriginal /></el-icon>
                  <span>単位</span>
                </div>
                <div class="header-right"></div>
              </div>
            </template>
            <template #default="{ row }">
              <div class="unit-value">{{ row.unit }}</div>
            </template>
          </el-table-column>
          <el-table-column prop="transaction_time" label="繰越日時" width="180" align="center">
            <template #header>
              <div class="table-header">
                <div class="header-left">
                  <el-icon><Calendar /></el-icon>
                  <span>繰越日時</span>
                </div>
                <div class="header-right"></div>
              </div>
            </template>
            <template #default="{ row }">
              <div class="time-value">{{ formatDateTime(row.transaction_time) }}</div>
            </template>
          </el-table-column>
          <el-table-column label="操作" fixed="right" width="150" align="center">
            <template #header>
              <div class="table-header">
                <div class="header-left">
                  <el-icon><Tools /></el-icon>
                  <span>操作</span>
                </div>
                <div class="header-right"></div>
              </div>
            </template>
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button
                  size="small"
                  type="primary"
                  link
                  @click="handleEdit(row)"
                  class="edit-btn"
                >
                  <el-icon><Edit /></el-icon>
                  編集
                </el-button>
                <el-button
                  size="small"
                  type="danger"
                  link
                  @click="handleDelete(row)"
                  class="delete-btn"
                >
                  <el-icon><Delete /></el-icon>
                  削除
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 分页 -->
      <div class="pagination-container" v-if="total > 0">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 空数据状态 -->
    <el-empty
      v-if="!loading && historyData.length === 0"
      description="繰越履歴データが見つかりません"
      :image-size="120"
      class="empty-state"
    />

    <!-- 添加/编辑对话框 -->
    <InventoryCarryoverEditDialog
      v-model="editDialogVisible"
      :editData="currentEditData"
      @save="handleSaveRecord"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ZoomIn,
  Refresh,
  Search,
  Document,
  Plus,
  Download,
  Edit,
  Delete,
  Operation,
  Box,
  Collection,
  Location,
  Setting,
  ScaleToOriginal,
  Calendar,
  Tools,
  Sort,
} from '@element-plus/icons-vue'
import {
  getCarryoverHistory,
  deleteCarryoverRecord,
  addCarryoverRecord,
  updateCarryoverRecord,
  exportCarryoverHistory,
} from '@/api/inventoryCarryover'
import { fetchProcesses } from '@/api/master/processMaster'
import InventoryCarryoverEditDialog from './InventoryCarryoverEditDialog.vue'

// 定义 Emits
const emit = defineEmits(['refresh'])

// 响应式数据
const loading = ref(false)
const exportLoading = ref(false)
const historyData = ref([])
const total = ref(0)
const editDialogVisible = ref(false)
const currentEditData = ref<any>(null)

// 筛选参数
const filterParams = reactive({
  carryoverMonth: '',
  process_cd: '',
  product_cd: '',
  transaction_type: '初期', // 默认筛选初期类型
})

// 分页参数
const pagination = reactive({
  page: 1,
  pageSize: 20,
})

// 排序参数
const sortParams = reactive({
  sortBy: 'transaction_time',
  sortOrder: 'desc',
})

// 排序状态管理
const sortConfig = ref({
  prop: '',
  order: '' as 'ascending' | 'descending' | '',
})

// 工程选项
const processOptions = ref<Array<{ value: string; label: string }>>([])
const processLoading = ref(false)

// 加载工程数据
const loadProcessOptions = async () => {
  processLoading.value = true
  try {
    const response = await fetchProcesses({
      page: 1,
      pageSize: 1000, // 获取所有工程数据
    })

    if (response && response.list && Array.isArray(response.list)) {
      processOptions.value = response.list.map((process: any) => ({
        value: process.process_cd,
        label: `${process.process_cd} - ${process.process_name}`,
      }))
    } else {
      console.error('工程データ取得エラー:', response)
      ElMessage.error('工程データの取得に失敗しました')
    }
  } catch (error) {
    console.error('工程データ取得エラー:', error)
    ElMessage.error('工程データの取得に失敗しました')
  } finally {
    processLoading.value = false
  }
}

// 获取在庫種別标签类型
const getStockTypeTagType = (stockType: string) => {
  const typeMap: Record<string, 'warning' | 'success' | 'primary' | 'info'> = {
    材料: 'warning',
    部品: 'success',
    製品: 'primary',
    代掛品: 'info',
  }
  return typeMap[stockType] || 'info'
}

// 获取取引種別标签类型
const getTransactionTypeTagType = (transactionType: string) => {
  const typeMap: Record<string, 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
    初期: 'primary',
    入庫: 'success',
    出庫: 'warning',
    調整: 'info',
    棚卸: 'danger',
  }
  return typeMap[transactionType] || 'info'
}

// 格式化数字
const formatNumber = (num: number) => {
  return num?.toLocaleString() || '0'
}

// 格式化日期时间
const formatDateTime = (dateTime: string) => {
  if (!dateTime) return ''
  return new Date(dateTime).toLocaleString('ja-JP')
}

// 清除筛选条件
const clearFilters = () => {
  filterParams.carryoverMonth = ''
  filterParams.process_cd = ''
  filterParams.product_cd = ''
  filterParams.transaction_type = '初期' // 保持默认值为初期
  pagination.page = 1
  loadHistoryData()
}

// 执行搜索
const handleSearch = () => {
  pagination.page = 1
  loadHistoryData()
}

// 加载历史数据
const loadHistoryData = async () => {
  loading.value = true
  try {
    const params = {
      ...filterParams,
      page: pagination.page,
      pageSize: pagination.pageSize,
      sortBy: sortParams.sortBy,
      sortOrder: sortParams.sortOrder,
    }

    const response = await getCarryoverHistory(params)

    // responseは拦截器によって処理され、成功時は直接dataが返される
    if (response && response.list) {
      historyData.value = response.list
      total.value = response.total
    } else {
      ElMessage.error('データ取得に失敗しました')
    }
  } catch (error) {
    console.error('履歴データ取得エラー:', error)
    ElMessage.error('履歴データ取得に失敗しました')
  } finally {
    loading.value = false
  }
}

// 处理排序变化
const handleSortChange = ({ prop, order }: any) => {
  if (prop && order) {
    sortParams.sortBy = prop
    sortParams.sortOrder = order === 'ascending' ? 'asc' : 'desc'
    loadHistoryData()
  }
}

// 自定义排序处理
const handleCustomSort = (prop: string) => {
  if (sortConfig.value.prop === prop) {
    // 如果点击的是当前排序列，切换排序顺序
    if (sortConfig.value.order === 'ascending') {
      sortConfig.value.order = 'descending'
    } else if (sortConfig.value.order === 'descending') {
      sortConfig.value.order = ''
      sortConfig.value.prop = ''
    } else {
      sortConfig.value.order = 'ascending'
    }
  } else {
    // 如果点击的是新列，设置为升序
    sortConfig.value.prop = prop
    sortConfig.value.order = 'ascending'
  }

  // 更新排序参数并重新加载数据
  if (sortConfig.value.prop && sortConfig.value.order) {
    sortParams.sortBy = sortConfig.value.prop
    sortParams.sortOrder = sortConfig.value.order === 'ascending' ? 'asc' : 'desc'
  } else {
    // 重置为默认排序
    sortParams.sortBy = 'transaction_time'
    sortParams.sortOrder = 'desc'
  }

  pagination.page = 1
  loadHistoryData()
}

// 处理页面大小变化
const handleSizeChange = (pageSize: number) => {
  pagination.pageSize = pageSize
  pagination.page = 1
  loadHistoryData()
}

// 处理当前页变化
const handleCurrentChange = (page: number) => {
  pagination.page = page
  loadHistoryData()
}

// 处理添加
const handleAdd = () => {
  currentEditData.value = null
  editDialogVisible.value = true
}

// 处理编辑
const handleEdit = (row: any) => {
  currentEditData.value = { ...row }
  editDialogVisible.value = true
}

// 处理删除
const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `製品コード「${row.target_cd}」の繰越記録を削除しますか？`,
      '削除確認',
      {
        confirmButtonText: '削除',
        cancelButtonText: 'キャンセル',
        type: 'warning',
      },
    )

    const response = await deleteCarryoverRecord(row.id)

    // responseは拦截器によって処理され、成功時は成功メッセージが返される
    if (response) {
      ElMessage.success('繰越記録を削除しました')
      await loadHistoryData()
      emit('refresh')
    } else {
      ElMessage.error('削除に失敗しました')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('削除エラー:', error)
      ElMessage.error('削除に失敗しました')
    }
  }
}

// 处理保存记录
const handleSaveRecord = async (data: any) => {
  try {
    const response = currentEditData.value
      ? await updateCarryoverRecord(currentEditData.value.id, data)
      : await addCarryoverRecord(data)

    // responseは拦截器によって処理され、成功時は成功メッセージが返される
    if (response) {
      ElMessage.success(currentEditData.value ? '更新しました' : '追加しました')
      editDialogVisible.value = false
      await loadHistoryData()
      emit('refresh')
    } else {
      ElMessage.error('保存に失敗しました')
    }
  } catch (error) {
    console.error('保存エラー:', error)
    ElMessage.error('保存に失敗しました')
  }
}

// 处理导出
const handleExport = async () => {
  exportLoading.value = true
  try {
    const params = {
      ...filterParams,
      sortBy: sortParams.sortBy,
      sortOrder: sortParams.sortOrder,
    }

    const response = await exportCarryoverHistory(params)

    // 创建下载链接
    const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `繰越履歴_${new Date().toISOString().slice(0, 10)}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('エクスポートが完了しました')
  } catch (error) {
    console.error('エクスポートエラー:', error)
    ElMessage.error('エクスポートに失敗しました')
  } finally {
    exportLoading.value = false
  }
}

// 组件挂载
onMounted(() => {
  loadProcessOptions()
  loadHistoryData()
})
</script>

<style lang="scss" scoped>
.inventory-carryover-history {
  .filter-card,
  .data-card {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(25px);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 20px;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
    }

    :deep(.el-card__body) {
      padding: 1.5rem;
    }
  }

  .filter-header {
    .filter-title {
      display: flex;
      align-items: center;
      gap: 0.8rem;
      font-size: 1.2rem;
      font-weight: 600;
      color: #333;
      margin-bottom: 1.2rem;

      .el-icon {
        color: #667eea;
        font-size: 1.3rem;
      }
    }
  }

  .filter-content {
    .filter-row {
      display: flex;
      align-items: end;
      gap: 1.5rem;
      flex-wrap: wrap;

      .filter-item {
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
        min-width: 180px;

        .filter-label {
          font-size: 0.85rem;
          font-weight: 600;
          color: #333;
        }

        .filter-input {
          width: 100%;
        }
      }

      .filter-actions {
        display: flex;
        gap: 0.8rem;

        .clear-btn {
          background: linear-gradient(135deg, #f3f4f6, #e5e7eb);
          border: none;
          color: #6b7280;
          border-radius: 8px;
          font-weight: 600;
          transition: all 0.3s ease;

          &:hover {
            background: linear-gradient(135deg, #e5e7eb, #d1d5db);
            transform: translateY(-1px);
            color: #374151;
          }
        }

        .search-btn {
          background: linear-gradient(135deg, #667eea, #764ba2);
          border: none;
          box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
          border-radius: 8px;
          font-weight: 600;
          transition: all 0.3s ease;

          &:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
          }
        }
      }
    }
  }

  .data-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.2rem;
    padding-bottom: 0.8rem;
    border-bottom: 1px solid #eee;

    .data-title {
      display: flex;
      align-items: center;
      gap: 0.8rem;
      font-size: 1.2rem;
      font-weight: 600;
      color: #333;

      .el-icon {
        color: #667eea;
        font-size: 1.3rem;
      }

      .data-count {
        font-size: 0.9rem;
        color: #666;
        font-weight: 400;
      }
    }

    .data-actions {
      display: flex;
      gap: 0.8rem;

      .add-btn {
        background: linear-gradient(135deg, #10b981, #059669);
        border: none;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;

        &:hover {
          transform: translateY(-1px);
          box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
        }
      }

      .export-btn {
        background: linear-gradient(135deg, #f3f4f6, #e5e7eb);
        border: none;
        color: #6b7280;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;

        &:hover {
          background: linear-gradient(135deg, #e5e7eb, #d1d5db);
          transform: translateY(-1px);
          color: #374151;
        }
      }
    }
  }

  .table-container {
    :deep(.modern-table) {
      border-radius: 15px;
      overflow: hidden;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);

      .el-table__header {
        background: linear-gradient(135deg, #f8fafc, #f1f5f9);

        th {
          background: transparent !important;
          color: #334155;
          font-weight: 700;
          font-size: 0.85rem;
          padding: 0.8rem 0.6rem;
          border-bottom: 2px solid #e2e8f0;

          .table-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            width: 100%;

            .header-left {
              display: flex;
              align-items: center;
              gap: 0.4rem;

              .el-icon {
                color: #667eea;
                font-size: 0.9rem;
              }

              span {
                font-weight: 700;
              }
            }

            .header-right {
              display: flex;
              align-items: center;

              .sort-icon {
                color: #9ca3af;
                font-size: 0.8rem;
                cursor: pointer;
                transition: all 0.3s ease;

                &:hover {
                  color: #667eea;
                  transform: scale(1.1);
                }

                &.sort-active {
                  color: #667eea;
                }

                &.sort-asc {
                  color: #10b981;
                  transform: rotate(180deg);
                }

                &.sort-desc {
                  color: #ef4444;
                }
              }
            }
          }
        }
      }

      .el-table__body {
        tr {
          transition: all 0.3s ease;

          &:hover > td {
            background: linear-gradient(135deg, #f0f9ff, #e0f2fe) !important;
            transform: scale(1.005);
          }

          td {
            padding: 0.8rem 0.6rem;
            border-bottom: 1px solid #f1f5f9;
            transition: all 0.3s ease;

            .product-code {
              font-family: 'Monaco', 'Menlo', monospace;
              font-weight: 600;
              color: #1e40af;
              background: linear-gradient(135deg, #dbeafe, #bfdbfe);
              padding: 0.2rem 0.4rem;
              border-radius: 5px;
              font-size: 0.8rem;
            }

            .product-name {
              font-weight: 500;
              color: #374151;
            }

            .stock-type-tag,
            .location-tag,
            .transaction-tag {
              font-weight: 600;
              border-radius: 6px;
              padding: 0.2rem 0.6rem;
            }

            .process-code {
              font-family: 'Monaco', 'Menlo', monospace;
              font-weight: 600;
              color: #059669;
              background: linear-gradient(135deg, #d1fae5, #a7f3d0);
              padding: 0.2rem 0.4rem;
              border-radius: 5px;
              font-size: 0.8rem;
            }

            .quantity-value {
              font-weight: 700;
              color: #059669;
              font-size: 1rem;
              background: linear-gradient(135deg, #d1fae5, #a7f3d0);
              padding: 0.3rem 0.5rem;
              border-radius: 6px;
              display: inline-block;
            }

            .unit-value {
              font-weight: 600;
              color: #6b7280;
              background: #f3f4f6;
              padding: 0.2rem 0.4rem;
              border-radius: 5px;
              font-size: 0.85rem;
            }

            .time-value {
              font-size: 0.85rem;
              color: #666;
              font-weight: 500;
            }

            .action-buttons {
              display: flex;
              gap: 0.5rem;
              justify-content: center;

              .edit-btn {
                color: #3b82f6;
                font-weight: 600;
                transition: all 0.3s ease;

                &:hover {
                  color: #1d4ed8;
                  transform: scale(1.05);
                }
              }

              .delete-btn {
                color: #ef4444;
                font-weight: 600;
                transition: all 0.3s ease;

                &:hover {
                  color: #dc2626;
                  transform: scale(1.05);
                }
              }
            }
          }
        }
      }
    }
  }

  .pagination-container {
    margin-top: 1.5rem;
    display: flex;
    justify-content: center;
  }

  .empty-state {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(25px);
    border-radius: 20px;
    padding: 2.5rem 2rem;
    border: 1px solid rgba(255, 255, 255, 0.3);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    text-align: center;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .inventory-carryover-history {
    .filter-content .filter-row {
      flex-direction: column;
      align-items: stretch;
      gap: 1rem;

      .filter-item {
        min-width: auto;
      }

      .filter-actions {
        justify-content: center;
      }
    }

    .data-header {
      flex-direction: column;
      gap: 1rem;
      align-items: stretch;

      .data-actions {
        justify-content: center;
        flex-wrap: wrap;
      }
    }
  }
}
</style>
