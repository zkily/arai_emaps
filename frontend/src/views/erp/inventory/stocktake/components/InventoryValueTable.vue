<template>
  <div class="inventory-value-table">
    <!-- 表格工具栏 -->
    <div class="table-toolbar">
      <div class="toolbar-left">
        <el-button
          type="primary"
          @click="calculateInventoryValue"
          :loading="calculating"
          class="action-btn"
        >
          <Operation class="btn-icon" />
          金額計算実行
        </el-button>
        <el-button @click="refreshTable" :loading="loading" class="action-btn">
          <Refresh class="btn-icon" />
          更新
        </el-button>
        <el-button @click="exportData" :loading="exporting" class="action-btn">
          <Download class="btn-icon" />
          データ出力
        </el-button>
      </div>
      <div class="toolbar-right">
        <el-input
          v-model="searchKeyword"
          placeholder="コード・名称で検索"
          @input="handleSearch"
          clearable
          class="search-input"
        >
          <template #prefix>
            <Search class="search-icon" />
          </template>
        </el-input>
        <el-button @click="showColumnSettings = true" class="settings-btn">
          <Setting class="btn-icon" />
          列設定
        </el-button>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="table-container">
      <el-table
        ref="tableRef"
        :data="tableData"
        v-loading="loading"
        :height="tableHeight"
        :default-sort="{ prop: 'total_value', order: 'descending' }"
        @sort-change="handleSortChange"
        @selection-change="handleSelectionChange"
        @row-click="handleRowClick"
        class="value-table"
        stripe
        border
      >
        <!-- 选择列 -->
        <el-table-column
          type="selection"
          width="55"
          :selectable="(row) => row.item_type !== 'summary'"
          v-if="columnSettings.selection"
        />

        <!-- 序号列 -->
        <el-table-column
          type="index"
          label="No."
          width="60"
          :index="getRowIndex"
          v-if="columnSettings.index"
        />

        <!-- 项目类型 -->
        <el-table-column
          prop="item_type"
          label="項目タイプ"
          width="120"
          sortable="custom"
          v-if="columnSettings.item_type"
        >
          <template #default="{ row }">
            <el-tag
              :type="getItemTypeTagType(row.item_type)"
              :effect="row.item_type === 'summary' ? 'plain' : 'dark'"
              class="item-type-tag"
            >
              {{ getItemTypeLabel(row.item_type) }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 代码 -->
        <el-table-column
          prop="product_cd"
          label="コード"
          width="120"
          sortable="custom"
          v-if="columnSettings.product_cd"
        >
          <template #default="{ row }">
            <span class="code-text">{{ row.product_cd }}</span>
          </template>
        </el-table-column>

        <!-- 名称 -->
        <el-table-column
          prop="product_name"
          label="名称"
          min-width="150"
          sortable="custom"
          show-overflow-tooltip
          v-if="columnSettings.product_name"
        >
          <template #default="{ row }">
            <span class="name-text">{{ row.product_name || row.product_cd || '—' }}</span>
          </template>
        </el-table-column>

        <!-- 工程 -->
        <el-table-column
          prop="process_name"
          label="工程"
          width="120"
          sortable="custom"
          v-if="columnSettings.process_name"
        >
          <template #default="{ row }">
            <span v-if="row.process_name" class="process-text">
              {{ row.process_name }}
            </span>
            <span v-else class="no-data">-</span>
          </template>
        </el-table-column>

        <!-- 数量 -->
        <el-table-column
          prop="quantity"
          label="数量"
          width="100"
          align="right"
          sortable="custom"
          v-if="columnSettings.quantity"
        >
          <template #default="{ row }">
            <span class="quantity-text">
              {{ formatNumber(row.quantity, 3) }}
            </span>
          </template>
        </el-table-column>

        <!-- 单位 -->
        <el-table-column
          prop="unit"
          label="単位"
          width="80"
          align="center"
          v-if="columnSettings.unit"
        >
          <template #default="{ row }">
            <span class="unit-text">{{ row.unit || 'pcs' }}</span>
          </template>
        </el-table-column>

        <!-- 单价 -->
        <el-table-column
          prop="unit_price"
          label="単価"
          width="120"
          align="right"
          sortable="custom"
          v-if="columnSettings.unit_price"
        >
          <template #default="{ row }">
            <span class="price-text"> ¥{{ formatNumber(row.unit_price, 2) }} </span>
          </template>
        </el-table-column>

        <!-- 金额 -->
        <el-table-column
          prop="total_value"
          label="金額"
          width="140"
          align="right"
          sortable="custom"
          v-if="columnSettings.total_value"
        >
          <template #default="{ row }">
            <span
              class="value-text"
              :class="{
                'summary-value': row.item_type === 'summary',
                'high-value': row.total_value > 1000000,
                'medium-value': row.total_value > 100000 && row.total_value <= 1000000,
              }"
            >
              ¥{{ formatNumber(row.total_value) }}
            </span>
          </template>
        </el-table-column>

        <!-- 棚卸日 -->
        <el-table-column
          prop="inventory_date"
          label="棚卸日"
          width="120"
          sortable="custom"
          v-if="columnSettings.inventory_date"
        >
          <template #default="{ row }">
            <span class="date-text">
              {{ formatDate(row.inventory_date) }}
            </span>
          </template>
        </el-table-column>

        <!-- 更新日时 -->
        <el-table-column
          prop="updated_at"
          label="更新日時"
          width="140"
          sortable="custom"
          v-if="columnSettings.updated_at"
        >
          <template #default="{ row }">
            <span class="datetime-text">
              {{ formatDateTime(row.updated_at) }}
            </span>
          </template>
        </el-table-column>

        <!-- 操作列 -->
        <el-table-column label="操作" width="120" fixed="right" v-if="columnSettings.actions">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button
                size="small"
                type="primary"
                link
                @click="viewDetail(row)"
                v-if="row.item_type !== 'summary'"
              >
                <View class="btn-icon" />
                詳細
              </el-button>
              <el-button
                size="small"
                type="warning"
                link
                @click="editPrice(row)"
                v-if="row.item_type !== 'summary' && hasEditPermission"
              >
                <Edit class="btn-icon" />
                編集
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页 -->
    <div class="pagination-container">
      <div class="pagination-info">
        <span class="info-text">
          全{{ totalCount }}件中 {{ (currentPage - 1) * pageSize + 1 }} -
          {{ Math.min(currentPage * pageSize, totalCount) }}件を表示
        </span>
        <span class="selected-info" v-if="selectedRows.length > 0">
          {{ selectedRows.length }}件選択中
        </span>
      </div>
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[20, 50, 100, 200]"
        :total="totalCount"
        layout="sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        class="table-pagination"
      />
    </div>

    <!-- 列设置弹窗 -->
    <el-dialog
      v-model="showColumnSettings"
      title="列表示設定"
      width="500px"
      class="column-settings-dialog"
    >
      <div class="column-settings">
        <div class="settings-header">
          <span>表示する列を選択してください</span>
          <div class="settings-actions">
            <el-button size="small" @click="selectAllColumns">全選択</el-button>
            <el-button size="small" @click="resetColumnSettings">リセット</el-button>
          </div>
        </div>
        <div class="settings-content">
          <el-checkbox-group v-model="selectedColumns">
            <div class="column-item" v-for="(label, key) in columnLabels" :key="key">
              <el-checkbox :label="key">{{ label }}</el-checkbox>
            </div>
          </el-checkbox-group>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showColumnSettings = false">キャンセル</el-button>
          <el-button type="primary" @click="applyColumnSettings">適用</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 详情弹窗 -->
    <el-dialog
      v-model="showDetailDialog"
      :title="detailDialogTitle"
      width="800px"
      class="detail-dialog"
    >
      <div class="detail-content" v-loading="detailLoading">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="項目タイプ">
            <el-tag :type="getItemTypeTagType(detailData.item_type)">
              {{ getItemTypeLabel(detailData.item_type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="コード">
            {{ detailData.product_cd }}
          </el-descriptions-item>
          <el-descriptions-item label="名称">
            {{ detailData.product_name }}
          </el-descriptions-item>
          <el-descriptions-item label="工程">
            {{ detailData.process_name || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="数量">
            {{ formatNumber(detailData.quantity, 3) }} {{ detailData.unit || 'pcs' }}
          </el-descriptions-item>
          <el-descriptions-item label="単価">
            ¥{{ formatNumber(detailData.unit_price, 2) }}
          </el-descriptions-item>
          <el-descriptions-item label="金額">
            <span class="detail-value">¥{{ formatNumber(detailData.total_value) }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="棚卸日">
            {{ formatDate(detailData.inventory_date) }}
          </el-descriptions-item>
          <el-descriptions-item label="作成日時" :span="2">
            {{ formatDateTime(detailData.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="更新日時" :span="2">
            {{ formatDateTime(detailData.updated_at) }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showDetailDialog = false">閉じる</el-button>
          <el-button type="primary" @click="editPrice(detailData)" v-if="hasEditPermission">
            <Edit class="btn-icon" />
            単価編集
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 单价编辑弹窗 -->
    <el-dialog v-model="showEditDialog" title="単価編集" width="600px" class="edit-dialog">
      <div class="edit-content">
        <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="120px">
          <el-form-item label="項目タイプ">
            <el-tag :type="getItemTypeTagType(editForm.item_type)">
              {{ getItemTypeLabel(editForm.item_type) }}
            </el-tag>
          </el-form-item>
          <el-form-item label="コード">
            <span>{{ editForm.product_cd }}</span>
          </el-form-item>
          <el-form-item label="名称">
            <span>{{ editForm.product_name }}</span>
          </el-form-item>
          <el-form-item label="現在の単価">
            <span class="current-price">¥{{ formatNumber(editForm.current_price, 2) }}</span>
          </el-form-item>
          <el-form-item label="新しい単価" prop="new_price">
            <el-input-number
              v-model="editForm.new_price"
              :precision="2"
              :min="0"
              :max="9999999.99"
              controls-position="right"
              class="price-input"
            />
          </el-form-item>
          <el-form-item label="適用開始日" prop="effective_date">
            <el-date-picker
              v-model="editForm.effective_date"
              type="date"
              placeholder="適用開始日を選択"
              format="YYYY/MM/DD"
              value-format="YYYY-MM-DD"
              class="date-picker"
            />
          </el-form-item>
          <el-form-item label="変更理由" prop="reason">
            <el-input
              v-model="editForm.reason"
              type="textarea"
              :rows="3"
              placeholder="単価変更の理由を入力してください"
              maxlength="200"
              show-word-limit
            />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showEditDialog = false">キャンセル</el-button>
          <el-button type="primary" @click="savePrice" :loading="saving"> 保存 </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Operation, Refresh, Download, Search, Setting, View, Edit } from '@element-plus/icons-vue'
import { inventoryValueApi } from '@/api/inventoryValue'
import { getProcessList } from '@/api/master/processMaster'
import { useUserStore } from '@/stores/user'

// NOTE: inventoryValueApi は暫定プレースホルダ実装のため、厳密型を避ける。
type TableRow = any

interface EditForm {
  item_type: string
  product_cd: string
  product_name: string
  current_price: number
  new_price: number
  effective_date: string
  reason: string
}

// Props
interface Props {
  dateRange?: string[]
  itemType?: string
  processCode?: string
}

const props = withDefaults(defineProps<Props>(), {
  dateRange: () => [],
  itemType: 'all',
  processCode: 'all',
})

// Emits
interface Emits {
  'data-updated': [data: any]
  'selection-change': [selection: any]
}

const emit = defineEmits<Emits>()

// 用户权限
const userStore = useUserStore()
const hasEditPermission = computed(() => {
  return userStore.hasPermission('inventory_value_edit')
})

// 响应式数据
const loading = ref(false)
const calculating = ref(false)
const exporting = ref(false)
const saving = ref(false)
const detailLoading = ref(false)

const tableRef = ref<any>()
const editFormRef = ref<any>()

const tableData = ref<any[]>([])
const selectedRows = ref<any[]>([])
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(50)
const totalCount = ref(0)
const tableHeight = ref(600)

// 排序
const sortField = ref('total_value')
const sortOrder = ref('desc')

// 列设置
const showColumnSettings = ref(false)
const columnLabels = {
  selection: '選択',
  index: '番号',
  item_type: '項目タイプ',
  product_cd: 'コード',
  product_name: '名称',
  process_name: '工程',
  quantity: '数量',
  unit: '単位',
  unit_price: '単価',
  total_value: '金額',
  inventory_date: '棚卸日',
  updated_at: '更新日時',
  actions: '操作',
}

const selectedColumns = ref<string[]>(Object.keys(columnLabels))
const columnSettings = computed<Record<string, boolean>>(() => {
  const settings: Record<string, boolean> = {}
  Object.keys(columnLabels).forEach((key) => {
    settings[key] = selectedColumns.value.includes(key)
  })
  return settings
})

// 详情弹窗
const showDetailDialog = ref(false)
const detailDialogTitle = ref('')
const detailData = ref<TableRow>({})

// 编辑弹窗
const showEditDialog = ref(false)
const editForm = reactive<EditForm>({
  item_type: '',
  product_cd: '',
  product_name: '',
  current_price: 0,
  new_price: 0,
  effective_date: '',
  reason: '',
})

const editRules: any = {
  new_price: [
    { required: true, message: '新しい単価を入力してください', trigger: 'blur' },
    { type: 'number', min: 0, message: '単価は0以上で入力してください', trigger: 'blur' },
  ],
  effective_date: [{ required: true, message: '適用開始日を選択してください', trigger: 'change' }],
  reason: [
    { required: true, message: '変更理由を入力してください', trigger: 'blur' },
    { min: 5, message: '変更理由は5文字以上で入力してください', trigger: 'blur' },
  ],
}

// 方法
const formatNumber = (value: any, decimals = 0) => {
  if (!value && value !== 0) return '0'
  return Number(value).toLocaleString('ja-JP', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

const formatDate = (dateString: any) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('ja-JP')
}

const formatDateTime = (dateString: any) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('ja-JP')
}

const getItemTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    material: '材料',
    component: '部品',
    stay: 'ステー',
    summary: '合計',
  }
  return labels[type] || type
}

type TagType = 'primary' | 'success' | 'warning' | 'info' | 'danger'
const getItemTypeTagType = (type: string): TagType => {
  const types: Record<string, TagType> = {
    material: 'primary',
    component: 'success',
    stay: 'warning',
    summary: 'info',
  }
  return types[type] || 'info'
}

const getRowIndex = (index: number) => {
  return (currentPage.value - 1) * pageSize.value + index + 1
}

// 获取查询参数
/** エクスポート等プレースホルダ用（将来 API 連携時に利用） */
const getQueryParams = () => ({
  page: currentPage.value,
  pageSize: pageSize.value,
  sortField: sortField.value,
  sortOrder: sortOrder.value,
  keyword: searchKeyword.value,
  itemType: props.itemType,
  processCode: props.processCode,
  dateRange: props.dateRange,
})

let processNameByCd: Record<string, string> = {}

async function ensureProcessNameMap() {
  if (Object.keys(processNameByCd).length > 0) return
  try {
    const res = await getProcessList({ page: 1, pageSize: 5000 })
    const list = (res as { data?: { list?: { process_cd: string; process_name: string }[] }; list?: { process_cd: string; process_name: string }[] })
      .data?.list ?? (res as { list?: { process_cd: string; process_name: string }[] }).list ?? []
    processNameByCd = Object.fromEntries(list.map((p) => [p.process_cd, p.process_name]))
  } catch {
    processNameByCd = {}
  }
}

function sortRows(rows: any[], prop: string, order: string) {
  if (!prop || !rows.length) return rows
  const dir = order === 'asc' ? 1 : -1
  return [...rows].sort((a, b) => {
    let av: number | string = a[prop]
    let bv: number | string = b[prop]
    if (['total_value', 'quantity', 'unit_price'].includes(prop)) {
      av = Number(av) || 0
      bv = Number(bv) || 0
    } else {
      av = String(av ?? '')
      bv = String(bv ?? '')
    }
    if (av < bv) return -1 * dir
    if (av > bv) return 1 * dir
    return 0
  })
}

// 加载表格数据
const loadTableData = async () => {
  try {
    loading.value = true
    await ensureProcessNameMap()

    const kw = searchKeyword.value.trim().toLowerCase()
    const baseParams = {
      item_type: props.itemType && props.itemType !== 'all' ? props.itemType : undefined,
      process_cd: props.processCode,
    }

    if (kw) {
      const response = await inventoryValueApi.getValueList({
        ...baseParams,
        page: 1,
        limit: 500,
      })
      let rows = (response.data.list ?? []).map((row: any) => ({
        ...row,
        process_name: row.process_name ?? processNameByCd[row.process_cd] ?? row.process_cd ?? '',
      }))
      rows = rows.filter(
        (r) =>
          String(r.product_cd ?? '')
            .toLowerCase()
            .includes(kw) ||
          String(r.product_name ?? '')
            .toLowerCase()
            .includes(kw),
      )
      rows = sortRows(rows, sortField.value, sortOrder.value)
      totalCount.value = rows.length
      const start = (currentPage.value - 1) * pageSize.value
      tableData.value = rows.slice(start, start + pageSize.value)
    } else {
      const response = await inventoryValueApi.getValueList({
        ...baseParams,
        page: currentPage.value,
        limit: pageSize.value,
      })
      let rows = (response.data.list ?? []).map((row: any) => ({
        ...row,
        process_name: row.process_name ?? processNameByCd[row.process_cd] ?? row.process_cd ?? '',
      }))
      rows = sortRows(rows, sortField.value, sortOrder.value)
      tableData.value = rows
      totalCount.value = response.data.total ?? 0
    }

    emit('data-updated', {
      total: totalCount.value,
      data: tableData.value,
    })
  } catch (error) {
    console.error('表格数据加载失败:', error)
    ElMessage.error('データの読み込みに失敗しました')
  } finally {
    loading.value = false
  }
}

// 计算库存金额
const calculateInventoryValue = async () => {
  try {
    await ElMessageBox.confirm(
      '棚卸金額の計算を実行しますか？\n※この処理には時間がかかる場合があります。',
      '確認',
      {
        confirmButtonText: '実行',
        cancelButtonText: 'キャンセル',
        type: 'warning',
      },
    )

    calculating.value = true
    if (!props.dateRange || props.dateRange.length < 2) {
      ElMessage.warning('期間を選択してください')
      return
    }
    const res = await inventoryValueApi.calculateValue({
      start_date: props.dateRange[0],
      end_date: props.dateRange[1],
      process_cd: props.processCode === 'all' ? undefined : props.processCode,
    })
    if (!res?.success) {
      ElMessage.error((res as { message?: string })?.message || '金額計算に失敗しました')
      return
    }
    const d = res.data as { total_rows?: number; error_rows?: number; total_amount?: number } | undefined
    if (d) {
      ElMessage.success(
        `計算完了: ${d.total_rows ?? 0}件 / エラー${d.error_rows ?? 0}件 / 合計 ¥${formatNumber(d.total_amount ?? 0)}`,
      )
    } else {
      ElMessage.success('棚卸金額の計算が完了しました')
    }
    await loadTableData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('金额计算失败:', error)
      ElMessage.error('金額計算に失敗しました')
    }
  } finally {
    calculating.value = false
  }
}

// 刷新表格
const refreshTable = () => {
  loadTableData()
}

// 导出数据
const exportData = async () => {
  try {
    exporting.value = true
    const params = getQueryParams()
    const response = await inventoryValueApi.exportExcel(params)

    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.download = `棚卸金額一覧_${new Date().toISOString().slice(0, 10)}.xlsx`
    link.click()
    window.URL.revokeObjectURL(url)

    ElMessage.success('データの出力が完了しました')
  } catch (error) {
    console.error('数据导出失败:', error)
    ElMessage.error('データ出力に失敗しました')
  } finally {
    exporting.value = false
  }
}

// 搜索处理
let searchTimer: ReturnType<typeof setTimeout> | undefined = undefined
const handleSearch = () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    currentPage.value = 1
    loadTableData()
  }, 500)
}

// 排序处理
const handleSortChange = ({ prop, order }: any) => {
  sortField.value = prop
  sortOrder.value = order === 'ascending' ? 'asc' : 'desc'
  loadTableData()
}

// 选择处理
const handleSelectionChange = (selection: any) => {
  selectedRows.value = selection
  emit('selection-change', selection)
}

// 行点击处理
const handleRowClick = (row: any) => {
  if (row.item_type !== 'summary') {
    viewDetail(row)
  }
}

// 分页处理
const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadTableData()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  loadTableData()
}

// 列设置
const selectAllColumns = () => {
  selectedColumns.value = Object.keys(columnLabels)
}

const resetColumnSettings = () => {
  selectedColumns.value = [
    'item_type',
    'product_cd',
    'product_name',
    'process_name',
    'quantity',
    'unit_price',
    'total_value',
    'inventory_date',
    'actions',
  ]
}

const applyColumnSettings = () => {
  showColumnSettings.value = false
  // 保存到本地存储
  localStorage.setItem('inventory_value_columns', JSON.stringify(selectedColumns.value))
  ElMessage.success('列設定を保存しました')
}

// 查看详情
const viewDetail = async (row: any) => {
  try {
    detailLoading.value = true
    detailDialogTitle.value = `詳細情報 - ${row.product_name}`

    const response = await inventoryValueApi.getValueDetail(row.id)
    detailData.value = response.data

    showDetailDialog.value = true
  } catch (error) {
    console.error('详情加载失败:', error)
    ElMessage.error('詳細情報の読み込みに失敗しました')
  } finally {
    detailLoading.value = false
  }
}

// 编辑单价
const editPrice = (row: any) => {
  Object.assign(editForm, {
    item_type: row.item_type,
    product_cd: row.product_cd,
    product_name: row.product_name,
    current_price: row.unit_price,
    new_price: row.unit_price,
    effective_date: new Date().toISOString().slice(0, 10),
    reason: '',
  })

  showEditDialog.value = true
  showDetailDialog.value = false
}

// 保存单价
const savePrice = async () => {
  try {
    const valid = await editFormRef.value.validate()
    if (!valid) return

    saving.value = true

    const params = {
      itemType: editForm.item_type,
      productCode: editForm.product_cd,
      newPrice: editForm.new_price,
      effectiveDate: editForm.effective_date,
      reason: editForm.reason,
    }

    await inventoryValueApi.updatePrice(params)

    ElMessage.success('単価を更新しました')
    showEditDialog.value = false
    await loadTableData()
  } catch (error) {
    console.error('单价保存失败:', error)
    ElMessage.error('単価の更新に失敗しました')
  } finally {
    saving.value = false
  }
}

// 计算表格高度
const calculateTableHeight = () => {
  nextTick(() => {
    const windowHeight = window.innerHeight
    const headerHeight = 200 // 估算的头部高度
    const paginationHeight = 80 // 分页高度
    const margin = 100 // 边距

    tableHeight.value = windowHeight - headerHeight - paginationHeight - margin
  })
}

// 监听props变化
watch(
  () => [props.dateRange, props.itemType, props.processCode],
  () => {
    currentPage.value = 1
    loadTableData()
  },
  { deep: true },
)

// 生命周期
onMounted(() => {
  // 从本地存储恢复列设置
  const savedColumns = localStorage.getItem('inventory_value_columns')
  if (savedColumns) {
    selectedColumns.value = JSON.parse(savedColumns)
  } else {
    resetColumnSettings()
  }

  calculateTableHeight()
  loadTableData()

  window.addEventListener('resize', calculateTableHeight)
})

// 暴露方法给父组件
defineExpose({
  refreshTable,
  getSelectedRows: () => selectedRows.value,
  clearSelection: () => tableRef.value?.clearSelection(),
})
</script>

<style scoped>
.inventory-value-table {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 0;
}

/* 工具栏样式 */
.table-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 25px;
  margin-bottom: 24px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
}

.toolbar-left {
  display: flex;
  gap: 12px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.action-btn {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
  backdrop-filter: blur(10px);
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.3);
}

.search-input {
  width: 320px;
}

.search-input :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.8);
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

.search-input :deep(.el-input__wrapper:hover) {
  border-color: #667eea;
}

.search-input :deep(.el-input__wrapper.is-focus) {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.search-input :deep(.el-input__inner) {
  color: #374151;
}

.search-input :deep(.el-input__inner::placeholder) {
  color: #9ca3af;
}

.search-icon {
  color: rgba(255, 255, 255, 0.6);
}

.settings-btn {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
}

/* 表格样式 */
.table-container {
  flex: 1;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.value-table {
  background: transparent;
}

.value-table :deep(.el-table) {
  background: transparent;
}

.value-table :deep(.el-table__header-wrapper) {
  background: rgba(248, 250, 252, 0.8);
}

.value-table :deep(.el-table__header th) {
  background: transparent;
  color: #374151;
  font-weight: 600;
  border-bottom: 2px solid rgba(226, 232, 240, 0.5);
}

.value-table :deep(.el-table__body tr) {
  background: transparent;
}

.value-table :deep(.el-table__body tr:hover) {
  background: rgba(102, 126, 234, 0.05);
  cursor: pointer;
}

.value-table :deep(.el-table__body tr.el-table__row--striped) {
  background: rgba(248, 250, 252, 0.3);
}

.value-table :deep(.el-table__body td) {
  border-bottom: 1px solid rgba(226, 232, 240, 0.3);
  color: #374151;
}

/* 表格内容样式 */
.item-type-tag {
  font-weight: 500;
}

.code-text {
  font-family: 'Courier New', monospace;
  font-weight: 500;
}

.name-text {
  font-weight: 500;
}

.process-text {
  color: #f59e0b;
  font-weight: 500;
}

.quantity-text {
  font-family: 'Courier New', monospace;
  font-weight: 500;
}

.unit-text {
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
}

.price-text {
  font-family: 'Courier New', monospace;
  font-weight: 500;
  color: #10b981;
}

.value-text {
  font-family: 'Courier New', monospace;
  font-weight: 600;
  color: #3b82f6;
}

.value-text.summary-value {
  color: #f59e0b;
  font-size: 16px;
}

.value-text.high-value {
  color: #ef4444;
}

.value-text.medium-value {
  color: #f59e0b;
}

.date-text,
.datetime-text {
  font-family: 'Courier New', monospace;
  color: rgba(255, 255, 255, 0.8);
  font-size: 12px;
}

.no-data {
  color: rgba(255, 255, 255, 0.5);
  font-style: italic;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.btn-icon {
  font-size: 14px;
}

/* 分页样式 */
.pagination-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 0;
  margin-top: 20px;
  background: rgba(248, 250, 252, 0.8);
  border-radius: 16px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.pagination-info {
  display: flex;
  align-items: center;
  gap: 20px;
}

.info-text {
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
}

.selected-info {
  color: #3b82f6;
  font-weight: 500;
  font-size: 14px;
}

.table-pagination :deep(.el-pagination) {
  color: #374151;
  background: transparent;
}

.table-pagination :deep(.el-pagination .el-pager li) {
  background: rgba(255, 255, 255, 0.7);
  color: #374151;
  border: 1px solid rgba(226, 232, 240, 0.5);
  border-radius: 8px;
  margin: 0 2px;
  transition: all 0.3s ease;
}

.table-pagination :deep(.el-pagination .el-pager li:hover) {
  background: rgba(102, 126, 234, 0.1);
  border-color: #667eea;
}

.table-pagination :deep(.el-pagination .el-pager li.is-active) {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border-color: transparent;
}

/* 弹窗样式 */
.column-settings-dialog :deep(.el-dialog),
.detail-dialog :deep(.el-dialog),
.edit-dialog :deep(.el-dialog) {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.column-settings-dialog :deep(.el-dialog__header),
.detail-dialog :deep(.el-dialog__header),
.edit-dialog :deep(.el-dialog__header) {
  background: rgba(248, 250, 252, 0.8);
  border-bottom: 1px solid rgba(226, 232, 240, 0.5);
  padding: 20px 25px;
}

.column-settings-dialog :deep(.el-dialog__title),
.detail-dialog :deep(.el-dialog__title),
.edit-dialog :deep(.el-dialog__title) {
  color: #374151;
  font-weight: 600;
}

.column-settings-dialog :deep(.el-dialog__body),
.detail-dialog :deep(.el-dialog__body),
.edit-dialog :deep(.el-dialog__body) {
  padding: 25px;
  color: #374151;
}

/* 列设置内容 */
.column-settings {
  color: #374151;
}

.settings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.settings-actions {
  display: flex;
  gap: 10px;
}

.settings-content {
  max-height: 400px;
  overflow-y: auto;
}

.column-item {
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.column-item:last-child {
  border-bottom: none;
}

/* 详情内容 */
.detail-content {
  color: #374151;
}

.detail-content :deep(.el-descriptions) {
  background: transparent;
}

.detail-content :deep(.el-descriptions__header) {
  background: rgba(248, 250, 252, 0.8);
  color: #374151;
}

.detail-content :deep(.el-descriptions__body) {
  background: transparent;
}

.detail-content :deep(.el-descriptions__table) {
  border-color: rgba(226, 232, 240, 0.5);
}

.detail-content :deep(.el-descriptions__cell) {
  border-color: rgba(226, 232, 240, 0.3);
}

.detail-content :deep(.el-descriptions__label) {
  background: rgba(248, 250, 252, 0.8);
  color: #64748b;
  font-weight: 500;
}

.detail-content :deep(.el-descriptions__content) {
  background: rgba(255, 255, 255, 0.7);
  color: #374151;
}

.detail-value {
  font-size: 18px;
  font-weight: 600;
  color: #3b82f6;
}

/* 编辑表单 */
.edit-content {
  color: #374151;
}

.edit-content :deep(.el-form-item__label) {
  color: #374151;
}

.edit-content :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.8);
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.edit-content :deep(.el-input__wrapper:hover) {
  border-color: #667eea;
}

.edit-content :deep(.el-input__wrapper.is-focus) {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.edit-content :deep(.el-input__inner) {
  color: #374151;
}

.edit-content :deep(.el-textarea__inner) {
  background: rgba(255, 255, 255, 0.8);
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  color: #374151;
  transition: all 0.3s ease;
}

.edit-content :deep(.el-textarea__inner:hover) {
  border-color: #667eea;
}

.edit-content :deep(.el-textarea__inner:focus) {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.current-price {
  font-size: 16px;
  font-weight: 600;
  color: #10b981;
}

.price-input {
  width: 200px;
}

.date-picker {
  width: 200px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 20px 25px;
  background: rgba(248, 250, 252, 0.8);
  border-top: 1px solid rgba(226, 232, 240, 0.5);
  backdrop-filter: blur(10px);
}

/* Element Plus 组件样式覆盖 */
:deep(.el-button) {
  border-radius: 10px;
  font-weight: 500;
  transition: all 0.3s ease;
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
}

:deep(.el-button--primary:hover) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .table-toolbar {
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
  }

  .toolbar-left,
  .toolbar-right {
    justify-content: center;
  }

  .search-input {
    width: 280px;
  }
}

@media (max-width: 768px) {
  .table-toolbar {
    padding: 15px 20px;
  }

  .toolbar-left {
    flex-wrap: wrap;
  }

  .search-input {
    width: 150px;
  }

  .pagination-container {
    flex-direction: column;
    gap: 15px;
  }

  .pagination-info {
    flex-direction: column;
    gap: 10px;
    text-align: center;
  }
}

@media (max-width: 480px) {
  .table-toolbar {
    padding: 10px 15px;
  }

  .action-btn {
    padding: 8px 12px;
    font-size: 12px;
  }

  .search-input {
    width: 120px;
  }
}
</style>
