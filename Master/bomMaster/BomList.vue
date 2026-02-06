<template>
  <div class="bom-list-container">
    <!-- フィルタ -->
    <el-form :inline="true" :model="filters" class="filter-form" @submit.prevent>
      <el-form-item label="製品CD">
        <el-input v-model="filters.product_cd" placeholder="製品CD" clearable />
      </el-form-item>
      <el-form-item label="製品名">
        <el-input v-model="filters.product_name" placeholder="製品名" clearable />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="fetchList">検索</el-button>
        <el-button icon="RefreshRight" @click="resetFilters">リセット</el-button>
      </el-form-item>
    </el-form>

    <!-- データテーブル -->
    <div class="table-container">
      <el-table :data="bomList" border stripe highlight-current-row v-loading="loading" @row-click="handleViewTree">
        <el-table-column label="製品CD" prop="product_cd" width="120" sortable />
        <el-table-column label="製品名" prop="product_name" min-width="150" sortable />
        <el-table-column label="部品CD" prop="component_cd" width="120" sortable />
        <el-table-column label="部品名" prop="component_name" min-width="150" sortable />
        <el-table-column label="数量" prop="quantity" width="80" sortable align="right">
          <template #default="{ row }">
            {{ formatNumber(row.quantity) }}
          </template>
        </el-table-column>
        <el-table-column label="単価" prop="unit_price" width="100" sortable align="right">
          <template #default="{ row }">
            ¥{{ formatYen(row.unit_price) }}
          </template>
        </el-table-column>
        <el-table-column label="備考" prop="note" min-width="150" show-overflow-tooltip />
        <el-table-column label="操作" width="200" align="center" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-tooltip content="編集" placement="top">
                <el-button size="small" type="primary" :icon="Edit" @click.stop="handleEdit(row)" />
              </el-tooltip>
              <el-tooltip content="削除" placement="top">
                <el-button size="small" type="danger" :icon="Delete" @click.stop="handleDelete(row)" />
              </el-tooltip>
              <el-tooltip content="BOM展開" placement="top">
                <el-button size="small" type="info" :icon="View" @click.stop="handleViewTree(row)" />
              </el-tooltip>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- ページネーション -->
    <div class="pagination-container">
      <el-pagination v-if="totalCount > 0" layout="total, sizes, prev, pager, next, jumper" v-model:page-size="pageSize"
        v-model:current-page="currentPage" :total="totalCount" :page-sizes="[10, 20, 50, 100]"
        @size-change="handleSizeChange" @current-change="handleCurrentChange" />
    </div>

    <!-- BOM編集ダイアログ -->
    <BomEditDialog v-model:visible="showDialog" :mode="editMode" :initial-data="selectedRow" @saved="fetchList" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, inject } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { fetchBomList, deleteBomItem } from '@/api/master'
import BomEditDialog from './BomEditDialog.vue'
// @ts-ignore
import type { BomItem } from '@/types/master'
import { Edit, Delete, View } from '@element-plus/icons-vue'

// 筛选条件
const filters = ref({
  product_cd: '',
  product_name: ''
})

// データ関連
const bomList = ref<BomItem[]>([])
const loading = ref(false)
const totalCount = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// ダイアログ関連
const showDialog = ref(false)
const editMode = ref<'add' | 'edit'>('add')
const selectedRow = ref<BomItem | null>(null)

// 親コンポーネントのメソッドを探す
interface BomMasterPage {
  showBomTree: (product: { product_id: number; product_name: string }) => void
}
const parentComponent = inject<BomMasterPage | null>('bomMasterPage', null)

// データ取得
const fetchList = async () => {
  loading.value = true
  try {
    const res = await fetchBomList({
      ...filters.value,
      page: currentPage.value,
      pageSize: pageSize.value
    })
    bomList.value = Array.isArray(res) ? res : []
    totalCount.value = bomList.value.length // 実際の実装ではAPIからの総件数を使用
  } catch (e) {
    ElMessage.error('構成一覧の取得に失敗しました')
  } finally {
    loading.value = false
  }
}

// フィルタリセット
const resetFilters = () => {
  filters.value = {
    product_cd: '',
    product_name: ''
  }
  fetchList()
}

// ページネーション処理
const handleSizeChange = (val: number) => {
  pageSize.value = val
  fetchList()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  fetchList()
}

// 新規追加
const handleAdd = () => {
  editMode.value = 'add'
  selectedRow.value = null
  showDialog.value = true
}

// 編集
const handleEdit = (row: BomItem) => {
  editMode.value = 'edit'
  selectedRow.value = { ...row }
  showDialog.value = true
}

// 削除
const handleDelete = async (row: BomItem) => {
  try {
    await ElMessageBox.confirm('この構成を削除してもよろしいですか？', '確認', {
      confirmButtonText: '削除',
      cancelButtonText: 'キャンセル',
      type: 'warning'
    })

    loading.value = true
    await deleteBomItem(row.id!)
    ElMessage.success('削除しました')
    fetchList()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('削除に失敗しました')
    }
  } finally {
    loading.value = false
  }
}

// BOMツリー表示
const handleViewTree = (row: BomItem) => {
  // 親コンポーネントのメソッドを呼び出す
  if (parentComponent && typeof parentComponent.showBomTree === 'function') {
    parentComponent.showBomTree({
      product_id: row.product_id,
      product_name: row.product_name || ''
    })
  } else {
    // 親コンポーネントが見つからない場合の代替処理
    ElMessage.info('製品ID: ' + row.product_id)
  }
}

// フォーマット関数
const formatYen = (val: any) => {
  const num = Number(val)
  return isNaN(num) ? '0.00' : num.toFixed(2)
}

const formatNumber = (val: any) => {
  const num = Number(val)
  return isNaN(num) ? '0' : num.toString()
}

// コンポーネント初期化時にデータを取得
onMounted(fetchList)

// 親コンポーネントから呼び出せるようにメソッドを公開
defineExpose({
  handleAdd,
  fetchList
})
</script>

<style scoped>
.bom-list-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.filter-form {
  padding: 12px;
  background-color: #f9f9f9;
  border-radius: 4px;
}

.table-container {
  width: 100%;
  overflow-x: auto;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  padding: 12px 0;
}

:deep(.el-table__row) {
  cursor: pointer;
}

:deep(.el-table__row:hover) {
  background-color: #f5f7fa;
}
</style>
