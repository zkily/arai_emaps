<template>
  <div class="product-list-sidebar">
    <el-card shadow="always" class="product-card">
      <template #header>
        <div class="header-bar">
          📋 製品一覧
        </div>
      </template>

      <!-- 🔍 検索 -->
      <el-input v-model="keyword" placeholder="製品CD・名称検索" clearable size="small" style="margin-bottom: 10px"
        @clear="resetSearch" @keyup.enter="handleSearch">
        <template #append>
          <el-button icon="Search" @click="handleSearch"></el-button>
        </template>
      </el-input>

      <!-- 📋 製品リスト -->
      <div class="table-wrapper">
        <el-table :data="products" highlight-current-row size="small" class="product-table" @row-click="handleClick">
          <el-table-column prop="product_cd" label="製品CD" width="100" />
          <el-table-column prop="product_name" label="製品名" />
        </el-table>
      </div>

      <!-- 📄 ページネーション -->
      <div class="pagination-wrapper">
        <el-pagination :current-page="currentPage" :page-size="pageSize" :total="total"
          layout="prev, pager, next, total" @current-change="handlePageChange" />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import request from '@/utils/request'

const emit = defineEmits<{
  (e: 'select', productCd: string): void
}>()

interface Product {
  product_cd: string
  product_name: string
}
const products = ref<Product[]>([])
const keyword = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const loadProducts = async () => {
  const result = await request.get('/api/master/products', {
    params: {
      page: currentPage.value,
      pageSize: pageSize.value,
      keyword: keyword.value
    }
  })
  products.value = result.data?.list ?? result.list ?? []
  total.value = result.data?.total ?? result.total ?? 0
}

onMounted(() => loadProducts())

const handlePageChange = (page: number) => {
  currentPage.value = page
  loadProducts()
}

const handleSearch = () => {
  currentPage.value = 1
  loadProducts()
}

const resetSearch = () => {
  keyword.value = ''
  currentPage.value = 1
  loadProducts()
}

const handleClick = (row: Product) => {
  emit('select', row.product_cd)
}
</script>

<style scoped>
.product-list-sidebar {
  display: flex;
  flex-direction: column;
  height: 100vh;
  /* ✅ 确保整屏高度 */
  padding: 5px;
}

.product-card {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
}

.header-bar {
  display: flex;
  align-items: center;
  font-weight: bold;
}

.table-wrapper {
  flex: 1;
  overflow: auto;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  padding: 5px 0;
}

.product-table .el-table__cell {
  padding: 8px 6px;
  font-size: 14px;
}
</style>
