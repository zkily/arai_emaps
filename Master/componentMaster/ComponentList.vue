<template>
  <div class="component-list-page">
    <!-- 🛠️ ヘッダー -->
    <div class="header">
      <h2 class="title">🔩 部品マスタ一覧</h2>
      <el-button type="primary" icon="Plus" @click="handleAdd">新規追加</el-button>
    </div>

    <!-- 🔍 フィルター -->
    <el-card shadow="always" class="filter-card">
      <el-form :inline="true" :model="filters" class="filter-form" @submit.prevent>
        <el-form-item label="キーワード">
          <el-input v-model="filters.keyword" placeholder="部品コード / 名称" clearable @keyup.enter="fetchList" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="Search" @click="fetchList">検索</el-button>
          <el-button icon="Refresh" @click="clearFilter">クリア</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 📋 部品一覧 -->
    <el-card shadow="never" class="table-card">
      <el-table :data="dataList" border stripe highlight-current-row :loading="loading" style="width: 100%">
        <el-table-column label="部品CD" prop="component_cd" width="80" align="center" />
        <el-table-column label="部品名称" prop="component_name" />
        <el-table-column label="仕様/型" prop="spec_model" />
        <el-table-column label="調達区分" prop="procurement_type" width="100" align="center" />
        <el-table-column label="仕入先" prop="supplier_name" />
        <el-table-column label="単価" prop="unit_price" width="100" align="center" />
        <el-table-column label="操作" width="170" fixed="right" align="center">
          <template #default="scope">
            <el-button size="small" type="primary" icon="Edit" @click="handleEdit(scope.row)">編集</el-button>
            <el-button size="small" type="danger" icon="Delete" @click="handleDelete(scope.row)">削除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- ✅ ページネーション -->
    <div class="pagination-container">
      <el-pagination size="small" background v-model:current-page="pagination.currentPage"
        v-model:page-size="pagination.pageSize" :total="pagination.total" :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper" @current-change="fetchList" @size-change="fetchList" />
    </div>

    <!-- ✅ 編集ダイアログ -->
    <ComponentEditDialog v-model:visible="editDialogVisible" :editData="editData" @saved="fetchList" />
  </div>
</template>

<script setup lang="ts">
// 原封不动保留你的逻辑代码
import { ref, reactive, onMounted } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Plus, Search, Refresh, Edit, Delete } from '@element-plus/icons-vue'
import request from '@/utils/request'
import ComponentEditDialog from './ComponentEditDialog.vue'

const filters = reactive({ keyword: '' })
const dataList = ref<any[]>([])
const pagination = reactive({ currentPage: 1, pageSize: 20, total: 0 })
const loading = ref(false)

const editDialogVisible = ref(false)
const editData = ref<any>(null)

const fetchList = async () => {
  loading.value = true
  try {
    const res = await request.get('/api/master/components', {
      params: {
        keyword: filters.keyword,
        page: pagination.currentPage,
        pageSize: pagination.pageSize
      }
    })
    dataList.value = res.list ?? res.data ?? res
    pagination.total = res.total ?? 0
  } catch (e) {
    ElMessage.error('部品一覧取得に失敗しました')
  } finally {
    loading.value = false
  }
}

const clearFilter = () => {
  filters.keyword = ''
  fetchList()
}

const handleAdd = () => {
  editData.value = null
  editDialogVisible.value = true
}

const handleEdit = (row: any) => {
  editData.value = { ...row }
  editDialogVisible.value = true
}

const handleDelete = (row: any) => {
  ElMessageBox.confirm('この部品を削除しますか？', '確認', { type: 'warning' })
    .then(async () => {
      await request.delete(`/api/master/components/${row.id}`)
      ElMessage.success('削除しました')
      fetchList()
    })
    .catch(() => { })
}

onMounted(() => {
  fetchList()
})
</script>

<style scoped>
.component-list-page {
  padding: 20px;
  background-color: #f5f7fa;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.title {
  font-size: 20px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-card {
  margin-bottom: 15px;
  padding: 15px;
}

.table-card {
  margin-bottom: 15px;
}

.pagination-container {
  text-align: center;
  margin-top: 15px;
}
</style>
