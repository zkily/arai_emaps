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
        :header-cell-style="{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: '#fff',
          fontWeight: '600',
          fontSize: '12px',
          padding: '6px 8px',
        }"
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
        layout="prev, pager, next, total"
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
  padding: 8px;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.page-header.compact {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
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
  color: rgba(255, 255, 255, 0.95);
}

.sub-title {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: #fff;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.search-section.compact {
  margin-bottom: 8px;
}

.search-input {
  width: 100%;
}

.search-prefix-ico {
  color: #94a3b8;
}

.table-wrapper {
  flex: 1;
  overflow: auto;
  min-height: 120px;
}

.code-cell {
  font-family: 'Consolas', 'Monaco', monospace;
  font-weight: 600;
  color: #667eea;
  font-size: 12px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  padding: 8px 0;
}

.product-table :deep(.el-table__cell) {
  padding: 6px 8px;
  font-size: 12px;
}
</style>
