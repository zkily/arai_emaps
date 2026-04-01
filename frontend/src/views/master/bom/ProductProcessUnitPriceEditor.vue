<template>
  <div class="price-editor">
    <!-- ヘッダー -->
    <div class="page-header">
      <div class="header-left">
        <h2>工程別標準原価管理</h2>
        <span class="subtitle">製品・ルート別の増分単価を登録し、累計単価を確認</span>
      </div>
    </div>

    <!-- 検索 -->
    <el-card class="search-card" shadow="never">
      <el-form :inline="true" class="search-form">
        <el-form-item label="製品CD">
          <el-select
            v-model="filterProductCd"
            filterable
            clearable
            placeholder="製品を選択"
            style="width: 260px"
            :loading="productsLoading"
            @change="onFilterProductChange"
          >
            <el-option
              v-for="p in productOptions"
              :key="p.product_cd"
              :label="`${p.product_cd} — ${p.product_name || ''}`"
              :value="p.product_cd"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="ルートCD">
          <el-input v-model="filterRouteCd" placeholder="ルートCD" clearable style="width: 150px" @keyup.enter="loadPrices" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="loadPrices">検索</el-button>
          <el-button @click="resetFilter">クリア</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="main-content">
      <!-- 左: 単価行一覧 -->
      <el-card class="list-card" shadow="never">
        <template #header>
          <div style="display:flex;justify-content:space-between;align-items:center">
            <span>単価行一覧（{{ priceTotal }}件）</span>
            <el-button type="primary" size="small" :icon="Plus" @click="openCreateDialog">新規追加</el-button>
          </div>
        </template>
        <el-table :data="prices" v-loading="loading" size="small" border highlight-current-row style="width: 100%">
          <el-table-column prop="product_cd" label="製品CD" width="120" />
          <el-table-column prop="route_cd" label="ルートCD" width="100" />
          <el-table-column prop="step_no" label="ステップ" width="80" align="center" />
          <el-table-column prop="line_seq" label="行番" width="60" align="center" />
          <el-table-column prop="line_type" label="種別" width="90">
            <template #default="{ row }">
              <el-tag :type="getTagType(row.line_type)" size="small">
                {{ lineTypeLabel[row.line_type] || row.line_type }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="内容" min-width="150" />
          <el-table-column prop="increment_unit_price" label="増分単価" width="120" align="right">
            <template #default="{ row }">
              {{ formatPrice(row.increment_unit_price) }}
            </template>
          </el-table-column>
          <el-table-column prop="effective_from" label="有効開始" width="105" />
          <el-table-column prop="effective_to" label="有効終了" width="105" />
          <el-table-column prop="status" label="状態" width="70">
            <template #default="{ row }">
              <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
                {{ row.status === 'active' ? '有効' : '無効' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="openEditDialog(row)">編集</el-button>
              <el-popconfirm title="削除しますか？" @confirm="handleDelete(row.id)">
                <template #reference>
                  <el-button link type="danger" size="small">削除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
        <div class="pagination-wrap">
          <el-pagination
            size="small"
            layout="total, prev, pager, next"
            :total="priceTotal"
            :page-size="pageSize"
            v-model:current-page="currentPage"
            @current-change="loadPrices"
          />
        </div>
      </el-card>

      <!-- 右: 累計プレビュー -->
      <el-card class="cumulative-card" shadow="never">
        <template #header>
          <div style="display:flex;justify-content:space-between;align-items:center">
            <span>累計単価プレビュー</span>
            <el-button type="primary" size="small" @click="loadCumulative" :disabled="!filterProductCd || !filterRouteCd">
              再計算
            </el-button>
          </div>
        </template>
        <div v-if="!cumulativeData.length" class="empty-tree">
          <el-empty description="製品CDとルートCDを指定して検索してください" />
        </div>
        <el-table v-else :data="cumulativeData" size="small" border style="width: 100%">
          <el-table-column prop="step_no" label="ステップ" width="80" align="center" />
          <el-table-column prop="line_seq" label="行番" width="60" align="center" />
          <el-table-column prop="line_type" label="種別" width="90">
            <template #default="{ row }">
              <el-tag :type="getTagType(row.line_type)" size="small">
                {{ lineTypeLabel[row.line_type] || row.line_type }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="内容" min-width="120" />
          <el-table-column prop="increment_unit_price" label="増分" width="100" align="right">
            <template #default="{ row }">{{ formatPrice(row.increment_unit_price) }}</template>
          </el-table-column>
          <el-table-column prop="cumulative_unit_price" label="累計単価" width="120" align="right">
            <template #default="{ row }">
              <strong>{{ formatPrice(row.cumulative_unit_price) }}</strong>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 新規/編集ダイアログ -->
    <el-dialog v-model="dialogVisible" :title="isEditing ? '単価行編集' : '新規単価行'" width="600px" destroy-on-close>
      <el-form :model="form" label-width="110px" size="small">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="製品CD" required>
              <el-select
                v-model="form.product_cd"
                filterable
                clearable
                placeholder="製品を選択"
                style="width: 100%"
                :loading="productsLoading"
                @change="onFormProductChange"
              >
                <el-option
                  v-for="p in productOptions"
                  :key="p.product_cd"
                  :label="`${p.product_cd} — ${p.product_name || ''}`"
                  :value="p.product_cd"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="ルートCD" required>
              <el-input v-model="form.route_cd" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="ステップ" required>
              <el-input-number v-model="form.step_no" :min="1" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="行番">
              <el-input-number v-model="form.line_seq" :min="1" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="種別">
              <el-select v-model="form.line_type" style="width: 100%">
                <el-option label="材料費" value="material" />
                <el-option label="加工費" value="process" />
                <el-option label="その他" value="other" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="内容">
          <el-input v-model="form.description" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="増分単価" required>
              <el-input-number v-model="form.increment_unit_price" :min="0" :precision="6" :step="0.01" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="通貨">
              <el-input v-model="form.currency" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="有効開始">
              <el-date-picker v-model="form.effective_from" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="有効終了">
              <el-date-picker v-model="form.effective_to" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="備考">
          <el-input v-model="form.remarks" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">キャンセル</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import {
  getUnitPrices,
  createUnitPrice,
  updateUnitPrice,
  deleteUnitPrice,
  getCumulativePrices,
  type UnitPriceRow,
  type UnitPricePayload,
} from '@/api/master/productProcessUnitPrice'
import { getProductList } from '@/api/master/productMaster'
import type { Product } from '@/types/master'

type TagType = 'primary' | 'success' | 'warning' | 'info' | 'danger'

const lineTypeLabel: Record<string, string> = { material: '材料費', process: '加工費', other: 'その他' }
const lineTypeTag: Record<string, TagType> = { material: 'warning', process: 'success', other: 'info' }

function getTagType(lineType: string): TagType {
  return lineTypeTag[lineType] ?? 'info'
}

function extractProductList(response: unknown): Product[] {
  const r = response as Record<string, unknown> | null | undefined
  if (!r) return []
  if (Array.isArray(r)) return r as Product[]
  if (Array.isArray(r.data)) return r.data as Product[]
  if (Array.isArray(r.list)) return r.list as Product[]
  const data = r.data as Record<string, unknown> | undefined
  if (data && Array.isArray(data.list)) return data.list as Product[]
  if (data && Array.isArray(data.data)) return data.data as Product[]
  return []
}

const productOptions = ref<Product[]>([])
const productsLoading = ref(false)

const filterProductCd = ref('')
const filterRouteCd = ref('')
const currentPage = ref(1)
const pageSize = 50
const priceTotal = ref(0)
const prices = ref<UnitPriceRow[]>([])
const loading = ref(false)

const cumulativeData = ref<UnitPriceRow[]>([])

const dialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)

const form = reactive<UnitPricePayload>({
  product_cd: '',
  route_cd: '',
  step_no: 1,
  line_seq: 1,
  line_type: 'process',
  description: '',
  increment_unit_price: 0,
  currency: 'JPY',
  effective_from: null,
  effective_to: null,
  status: 'active',
  bom_line_id: null,
  remarks: null,
})

function formatPrice(v: number | undefined | null) {
  if (v == null) return '—'
  return v.toLocaleString('ja-JP', { minimumFractionDigits: 2, maximumFractionDigits: 6 })
}

function routeFromProduct(product_cd: string): string {
  if (!product_cd) return ''
  const p = productOptions.value.find((x) => x.product_cd === product_cd)
  return (p?.route_cd && String(p.route_cd).trim()) || ''
}

async function loadProducts() {
  productsLoading.value = true
  try {
    const res = await getProductList({ page: 1, pageSize: 10000, status: 'active' })
    const list = extractProductList(res)
    productOptions.value = list
      .filter((p) => p.product_cd)
      .sort((a, b) => String(a.product_cd).localeCompare(String(b.product_cd), 'ja'))
  } catch {
    productOptions.value = []
    ElMessage.error('製品マスタの取得に失敗しました')
  } finally {
    productsLoading.value = false
  }
}

function onFilterProductChange(cd: string) {
  const route = routeFromProduct(cd)
  if (route && !filterRouteCd.value) filterRouteCd.value = route
  loadPrices()
}

function onFormProductChange(cd: string) {
  const route = routeFromProduct(cd)
  if (route && !isEditing.value) form.route_cd = route
}

/** 編集時：マスタに無い製品CDでもドロップダウンで表示できるよう補完 */
function ensureProductOption(product_cd: string | undefined, route_cd?: string | null) {
  if (!product_cd) return
  if (productOptions.value.some((x) => x.product_cd === product_cd)) return
  productOptions.value = [
    ...productOptions.value,
    {
      product_cd,
      product_name: '（マスタ未登録または非active）',
      route_cd: route_cd ?? undefined,
    },
  ]
}

async function loadPrices() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: currentPage.value, limit: pageSize }
    if (filterProductCd.value) params.product_cd = filterProductCd.value
    if (filterRouteCd.value) params.route_cd = filterRouteCd.value
    const res = await getUnitPrices(params)
    const d = (res as any)?.data ?? res
    prices.value = d?.list ?? []
    priceTotal.value = d?.total ?? 0
  } catch {
    ElMessage.error('単価行の取得に失敗しました')
  } finally {
    loading.value = false
  }
  if (filterProductCd.value && filterRouteCd.value) loadCumulative()
}

async function loadCumulative() {
  if (!filterProductCd.value || !filterRouteCd.value) return
  try {
    const res = await getCumulativePrices({
      product_cd: filterProductCd.value,
      route_cd: filterRouteCd.value,
    })
    const d = (res as any)?.data ?? res
    cumulativeData.value = Array.isArray(d) ? d : []
  } catch {
    cumulativeData.value = []
  }
}

function resetFilter() {
  filterProductCd.value = ''
  filterRouteCd.value = ''
  currentPage.value = 1
  cumulativeData.value = []
  loadPrices()
}

function openCreateDialog() {
  isEditing.value = false
  editingId.value = null
  Object.assign(form, {
    product_cd: filterProductCd.value || '',
    route_cd: filterRouteCd.value || '',
    step_no: 1,
    line_seq: 1,
    line_type: 'process',
    description: '',
    increment_unit_price: 0,
    currency: 'JPY',
    effective_from: null,
    effective_to: null,
    status: 'active',
    bom_line_id: null,
    remarks: null,
  })
  dialogVisible.value = true
}

function openEditDialog(row: UnitPriceRow) {
  isEditing.value = true
  editingId.value = row.id
  ensureProductOption(row.product_cd, row.route_cd)
  Object.assign(form, {
    product_cd: row.product_cd,
    route_cd: row.route_cd,
    step_no: row.step_no,
    line_seq: row.line_seq ?? 1,
    line_type: row.line_type,
    description: row.description,
    increment_unit_price: row.increment_unit_price,
    currency: row.currency ?? 'JPY',
    effective_from: row.effective_from,
    effective_to: row.effective_to,
    status: row.status ?? 'active',
    bom_line_id: row.bom_line_id,
    remarks: row.remarks,
  })
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.product_cd || !form.route_cd) {
    ElMessage.warning('製品CDとルートCDは必須です')
    return
  }
  saving.value = true
  try {
    if (isEditing.value && editingId.value) {
      await updateUnitPrice(editingId.value, { ...form })
      ElMessage.success('更新しました')
    } else {
      await createUnitPrice({ ...form })
      ElMessage.success('作成しました')
    }
    dialogVisible.value = false
    loadPrices()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存に失敗しました')
  } finally {
    saving.value = false
  }
}

async function handleDelete(id: number) {
  try {
    await deleteUnitPrice(id)
    ElMessage.success('削除しました')
    loadPrices()
  } catch {
    ElMessage.error('削除に失敗しました')
  }
}

onMounted(async () => {
  await loadProducts()
  loadPrices()
})
</script>

<style scoped>
.price-editor {
  padding: 16px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.page-header h2 {
  margin: 0;
  font-size: 18px;
}
.subtitle {
  color: #909399;
  font-size: 13px;
  margin-left: 12px;
}
.search-card {
  margin-bottom: 12px;
}
.search-card :deep(.el-card__body) {
  padding: 12px 16px;
}
.search-form .el-form-item {
  margin-bottom: 0;
}
.main-content {
  display: flex;
  gap: 12px;
}
.list-card {
  flex: 1;
  min-width: 0;
}
.cumulative-card {
  flex: 0 0 480px;
}
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}
.empty-tree {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}
</style>
