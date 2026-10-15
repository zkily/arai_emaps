<template>
  <div class="product-list-sidebar">
    <div class="page-header compact">
      <div class="header-content">
        <div class="title-section">
          <span class="title-icon-wrap" aria-hidden="true">
            <el-icon :size="18"><List /></el-icon>
          </span>
          <h2 class="sub-title">製品一覧</h2>
        </div>
      </div>
    </div>
    <div class="search-section compact">
      <el-input
        v-model="keyword"
        placeholder="製品CD・名称（入力で自動検索）"
        clearable
        size="small"
        class="search-input"
      >
        <template #prefix>
          <el-icon class="search-prefix-ico"><Search /></el-icon>
        </template>
      </el-input>
    </div>
    <div class="table-wrapper">
      <el-table
        :data="products"
        highlight-current-row
        size="small"
        class="product-table modern-table"
        height="100%"
        @row-click="handleClick"
      >
        <el-table-column prop="product_cd" label="製品CD" width="100" align="center">
          <template #default="{ row }">
            <span class="code-cell">{{ row.product_cd }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="product_name" label="製品名" min-width="120" show-overflow-tooltip />
      </el-table>
    </div>
    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[20, 50, 100]"
        layout="prev, pager, next"
        size="small"
        @current-change="handlePageChange"
        @size-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import { List, Search } from '@element-plus/icons-vue'
import request from '@/shared/api/request'

/** キーワード変更時の自動検索（連打時はまとめて 1 回） */
const KEYWORD_DEBOUNCE_MS = 320
let keywordDebounceTimer: ReturnType<typeof setTimeout> | null = null

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
      keyword: keyword.value || undefined,
    },
  })
  const data = result?.data ?? result
  products.value = data?.list ?? []
  total.value = data?.total ?? 0
}

onMounted(() => loadProducts())

watch(keyword, () => {
  if (keywordDebounceTimer) clearTimeout(keywordDebounceTimer)
  keywordDebounceTimer = setTimeout(() => {
    keywordDebounceTimer = null
    currentPage.value = 1
    loadProducts()
  }, KEYWORD_DEBOUNCE_MS)
})

onBeforeUnmount(() => {
  if (keywordDebounceTimer) clearTimeout(keywordDebounceTimer)
})

const handlePageChange = () => {
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
  height: 100%;
  min-height: 0;
  padding: 8px;
  background: #fff;
}

.page-header.compact {
  flex-shrink: 0;
  background: linear-gradient(125deg, #4c1d95 0%, #6d28d9 50%, #8b5cf6 100%);
  border-radius: 10px;
  padding: 8px 12px;
  margin-bottom: 8px;
}

.header-content {
  display: flex;
  align-items: center;
  min-width: 0;
}

.title-section {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.title-icon-wrap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.35);
  background: rgba(255, 255, 255, 0.18);
}

.sub-title {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 800;
  color: #fff;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.search-section.compact {
  flex-shrink: 0;
  margin-bottom: 8px;
}

.search-input {
  width: 100%;
}
.search-input :deep(.el-input__wrapper) {
  border-radius: 9px;
  background: #f8fafc;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
}
.search-input :deep(.el-input__wrapper.is-focus) {
  box-shadow:
    0 0 0 1px #8b5cf6 inset,
    0 0 0 3px rgba(139, 92, 246, 0.15);
}

.search-prefix-ico {
  color: #a78bfa;
}

.table-wrapper {
  flex: 1;
  overflow: hidden;
  min-height: 120px;
}

.code-cell {
  font-family: 'Consolas', 'Monaco', monospace;
  font-weight: 700;
  color: #6d28d9;
  font-size: 12px;
  padding: 1px 6px;
  border-radius: 6px;
  background: #f5f3ff;
  box-shadow: inset 0 0 0 1px #ddd6fe;
}

.pagination-wrapper {
  flex-shrink: 0;
  display: flex;
  justify-content: center;
  padding: 8px 0 2px;
}

.product-table :deep(.el-table__header th) {
  background: linear-gradient(180deg, #faf5ff 0%, #f5f3ff 100%) !important;
  color: #5b21b6 !important;
  font-weight: 700;
  font-size: 12px;
  border-bottom: 2px solid #c4b5fd !important;
}

.product-table :deep(.el-table__body tr:hover > td) {
  background: #faf5ff !important;
}

.product-table :deep(.el-table__body tr.current-row > td) {
  background: #ede9fe !important;
}

.product-table :deep(.el-table__cell) {
  padding: 6px 8px;
  font-size: 12px;
}

.pagination-wrapper :deep(.el-pager li.is-active) {
  background: linear-gradient(135deg, #8b5cf6, #6d28d9);
}
</style>
