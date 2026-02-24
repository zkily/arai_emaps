<template>
  <div class="outsourcing-products-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="main-title">
            <el-icon class="title-icon">
              <OfficeBuilding />
            </el-icon>
            外注工程製品管理
          </h1>
          <p class="subtitle">外注工程ごとの製品情報を管理します</p>
        </div>
        <div class="header-stats">
          <div class="stat-card">
            <div class="stat-number">{{ stats.total || 0 }}</div>
            <div class="stat-label">総登録数</div>
          </div>
          <div class="stat-card stat-card-active">
            <div class="stat-number">{{ stats.active || 0 }}</div>
            <div class="stat-label">有効</div>
          </div>
          <div class="stat-card stat-card-suppliers">
            <div class="stat-number">{{ stats.suppliers || 0 }}</div>
            <div class="stat-label">外注先数</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 工程タブ -->
    <div class="process-tabs-section">
      <el-tabs
        v-model="activeProcessType"
        type="card"
        class="process-tabs"
        @tab-change="handleTabChange"
      >
        <el-tab-pane label="全て" name="all">
          <template #label>
            <div class="tab-label">
              <el-icon><Grid /></el-icon>
              <span>全て</span>
              <el-badge :value="getProcessCount('all')" class="tab-badge" />
            </div>
          </template>
        </el-tab-pane>
        <el-tab-pane label="外注切断" name="cutting">
          <template #label>
            <div class="tab-label">
              <el-icon><Scissor /></el-icon>
              <span>外注切断</span>
              <el-badge :value="getProcessCount('cutting')" class="tab-badge" />
            </div>
          </template>
        </el-tab-pane>
        <el-tab-pane label="外注成型" name="forming">
          <template #label>
            <div class="tab-label">
              <el-icon><Box /></el-icon>
              <span>外注成型</span>
              <el-badge :value="getProcessCount('forming')" class="tab-badge" />
            </div>
          </template>
        </el-tab-pane>
        <el-tab-pane label="外注メッキ" name="plating">
          <template #label>
            <div class="tab-label">
              <el-icon><Coin /></el-icon>
              <span>外注メッキ</span>
              <el-badge :value="getProcessCount('plating')" class="tab-badge" />
            </div>
          </template>
        </el-tab-pane>
        <el-tab-pane label="外注溶接" name="welding">
          <template #label>
            <div class="tab-label">
              <el-icon><Connection /></el-icon>
              <span>外注溶接</span>
              <el-badge :value="getProcessCount('welding')" class="tab-badge" />
            </div>
          </template>
        </el-tab-pane>
        <el-tab-pane label="外注検査" name="inspection">
          <template #label>
            <div class="tab-label">
              <el-icon><View /></el-icon>
              <span>外注検査</span>
              <el-badge :value="getProcessCount('inspection')" class="tab-badge" />
            </div>
          </template>
        </el-tab-pane>
        <el-tab-pane label="外注加工" name="processing">
          <template #label>
            <div class="tab-label">
              <el-icon><Tools /></el-icon>
              <span>外注加工</span>
              <el-badge :value="getProcessCount('processing')" class="tab-badge" />
            </div>
          </template>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 功能操作区域 -->
    <div class="action-section">
      <div class="filter-header">
        <div class="filter-title">
          <el-icon class="filter-icon"><Filter /></el-icon>
          <span>検索・絞り込み</span>
        </div>
        <div class="filter-actions">
          <el-button text @click="clearFilters" :icon="Refresh" class="clear-btn">
            クリア
          </el-button>
          <el-button type="primary" @click="handleSearch" :icon="Search" class="search-btn">
            検索
          </el-button>
          <el-button type="success" @click="handleAdd" :icon="Plus" class="add-btn">
            新規登録
          </el-button>
        </div>
      </div>

      <div class="filters-grid">
        <div class="filter-item">
          <label class="filter-label">
            <el-icon><Search /></el-icon>
            キーワード
          </label>
          <el-input
            v-model="filters.keyword"
            placeholder="外注先/品番/品名で検索"
            clearable
            @clear="handleSearch"
            @keyup.enter="handleSearch"
            class="filter-input"
          />
        </div>
        <div class="filter-item">
          <label class="filter-label">
            <el-icon><OfficeBuilding /></el-icon>
            外注先コード
          </label>
          <el-input
            v-model="filters.supplierCd"
            placeholder="外注先コードで検索"
            clearable
            @clear="handleSearch"
            @keyup.enter="handleSearch"
            class="filter-input"
          />
        </div>
        <div class="filter-item">
          <label class="filter-label">
            <el-icon><Tickets /></el-icon>
            品番
          </label>
          <el-input
            v-model="filters.productCd"
            placeholder="品番で検索"
            clearable
            @clear="handleSearch"
            @keyup.enter="handleSearch"
            class="filter-input"
          />
        </div>
        <div class="filter-item">
          <label class="filter-label">
            <el-icon><CircleCheck /></el-icon>
            状態
          </label>
          <el-select
            v-model="filters.isActive"
            placeholder="すべて"
            clearable
            class="filter-select"
          >
            <el-option label="すべて" value="all" />
            <el-option label="有効" value="true" />
            <el-option label="無効" value="false" />
          </el-select>
        </div>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="table-section">
      <el-card class="table-card" shadow="never">
        <el-table
          :data="tableData"
          v-loading="loading"
          stripe
          border
          :empty-text="'データがありません'"
          height="calc(100vh - 400px)"
          :row-style="{ height: '42px' }"
          size="default"
        >
          <el-table-column
            prop="process_type_name"
            label="工程種別"
            width="100"
            align="center"
            fixed="left"
          >
            <template #default="{ row }">
              <el-tag :type="getProcessTypeColor(row.process_type)" size="small" effect="plain">
                {{ row.process_type_name }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            prop="supplier_cd"
            label="外注先CD"
            width="90"
            align="center"
            show-overflow-tooltip
          />
          <el-table-column
            prop="supplier_name"
            label="外注先名"
            width="140"
            show-overflow-tooltip
          />
          <el-table-column
            prop="product_cd"
            label="製品CD"
            width="90"
            align="center"
            show-overflow-tooltip
          />
          <el-table-column prop="product_name" label="品名" min-width="140" show-overflow-tooltip />
          <el-table-column prop="specification" label="規格" width="100" show-overflow-tooltip />
          <el-table-column prop="unit_price" label="単価" width="70" align="right">
            <template #default="{ row }">
              <span class="price-text">{{ formatPrice(row.unit_price) }}</span>
            </template>
          </el-table-column>
          <el-table-column
            prop="delivery_lead_time"
            label="納入リードタイム"
            width="140"
            align="center"
          >
            <template #default="{ row }">
              <span class="lead-time">{{ row.delivery_lead_time || '-' }}日</span>
            </template>
          </el-table-column>
          <el-table-column
            prop="delivery_location"
            label="納入場所"
            width="130"
            align="center"
            show-overflow-tooltip
          />
          <el-table-column prop="category" label="区分" width="120" align="center" />
          <el-table-column
            prop="content"
            label="内容"
            width="120"
            align="center"
            show-overflow-tooltip
          />
          <el-table-column prop="is_active" label="状態" width="70" align="center">
            <template #default="{ row }">
              <el-tag
                :type="row.is_active ? 'success' : 'info'"
                size="small"
                effect="plain"
                class="status-tag"
              >
                {{ row.is_active ? '有効' : '無効' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160" align="center" fixed="right">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button
                  type="primary"
                  size="small"
                  @click="handleEdit(row)"
                  class="action-btn-edit"
                  :icon="Edit"
                >
                  編集
                </el-button>
                <el-button
                  :type="row.is_active ? 'warning' : 'success'"
                  size="small"
                  @click="handleToggleStatus(row)"
                  class="action-btn-toggle"
                >
                  {{ row.is_active ? '無効' : '有効' }}
                </el-button>
                <el-button
                  type="danger"
                  size="small"
                  @click="handleDelete(row)"
                  class="action-btn-delete"
                  :icon="Delete"
                />
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 分页组件 -->
    <div class="pagination-section">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :page-sizes="[20, 50, 100, 200]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
        class="pagination"
      />
    </div>

    <!-- 编辑/新增对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '外注工程製品編集' : '外注工程製品登録'"
      width="1176px"
      :close-on-click-modal="false"
      class="modern-dialog"
      destroy-on-close
      top="3vh"
    >
      <template #header>
        <div class="modern-header">
          <div class="header-left">
            <div class="header-icon-wrapper">
              <el-icon class="header-icon"><OfficeBuilding /></el-icon>
            </div>
            <div class="header-content">
              <h3 class="header-title">{{ isEdit ? '外注工程製品編集' : '外注工程製品登録' }}</h3>
              <p class="header-subtitle">
                外注工程の製品情報を{{ isEdit ? '編集' : '登録' }}します
              </p>
            </div>
          </div>
          <div class="header-status">
            <el-tag :type="isEdit ? 'warning' : 'success'" size="small">
              {{ isEdit ? '編集モード' : '新規登録' }}
            </el-tag>
          </div>
        </div>
      </template>

      <div class="modern-content">
        <el-form
          ref="formRef"
          :model="formData"
          :rules="formRules"
          label-width="auto"
          label-position="left"
          class="modern-form"
          size="default"
        >
          <!-- 工程種別 - 特別セクション -->
          <div class="process-card">
            <div class="process-header">
              <el-icon class="process-icon"><Tools /></el-icon>
              <span class="process-title">工程種別選択</span>
            </div>
            <el-form-item prop="process_type" class="process-select-item">
              <el-select
                v-model="formData.process_type"
                placeholder="工程種別を選択してください"
                size="default"
                :disabled="isEdit"
                class="process-select"
              >
                <el-option label="外注切断" value="cutting">
                  <div class="option-content">
                    <el-icon><Scissor /></el-icon>
                    <span>外注切断</span>
                  </div>
                </el-option>
                <el-option label="外注成型" value="forming">
                  <div class="option-content">
                    <el-icon><Box /></el-icon>
                    <span>外注成型</span>
                  </div>
                </el-option>
                <el-option label="外注メッキ" value="plating">
                  <div class="option-content">
                    <el-icon><Coin /></el-icon>
                    <span>外注メッキ</span>
                  </div>
                </el-option>
                <el-option label="外注溶接" value="welding">
                  <div class="option-content">
                    <el-icon><Connection /></el-icon>
                    <span>外注溶接</span>
                  </div>
                </el-option>
                <el-option label="外注検査" value="inspection">
                  <div class="option-content">
                    <el-icon><View /></el-icon>
                    <span>外注検査</span>
                  </div>
                </el-option>
                <el-option label="外注加工" value="processing">
                  <div class="option-content">
                    <el-icon><Tools /></el-icon>
                    <span>外注加工</span>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
          </div>

          <!-- メインフォーム -->
          <div class="form-grid">
            <!-- 基本情報 -->
            <div class="form-card">
              <div class="card-header">
                <el-icon class="card-icon"><Grid /></el-icon>
                <span class="card-title">基本情報</span>
              </div>
              <div class="card-content">
                <div class="form-row">
                  <div class="form-col">
                    <el-form-item label="外注先" prop="supplier_cd">
                      <el-select
                        v-model="formData.supplier_cd"
                        placeholder="外注先を選択"
                        :disabled="isEdit"
                        filterable
                        clearable
                        @change="handleSupplierChange"
                        :loading="suppliersLoading"
                        class="full-width"
                      >
                        <el-option
                          v-for="supplier in suppliersList"
                          :key="supplier.supplier_cd"
                          :label="`${supplier.supplier_cd} - ${supplier.supplier_name}`"
                          :value="supplier.supplier_cd"
                        />
                      </el-select>
                    </el-form-item>
                  </div>
                  <div class="form-col">
                    <el-form-item label="外注先名" prop="supplier_name">
                      <el-input v-model="formData.supplier_name" placeholder="自動入力" clearable />
                    </el-form-item>
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-col">
                    <el-form-item label="製品CD" prop="product_cd">
                      <el-select
                        v-model="formData.product_cd"
                        placeholder="製品を選択"
                        :disabled="isEdit"
                        filterable
                        clearable
                        @change="handleProductChange"
                        :loading="productsLoading"
                        class="full-width"
                      >
                        <el-option
                          v-for="product in productsList"
                          :key="product.cd"
                          :label="`${product.cd} - ${product.name}`"
                          :value="product.cd"
                        />
                      </el-select>
                    </el-form-item>
                  </div>
                  <div class="form-col">
                    <el-form-item label="品名" prop="product_name">
                      <el-input v-model="formData.product_name" placeholder="自動入力" clearable />
                    </el-form-item>
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-col full">
                    <el-form-item label="規格" prop="specification">
                      <el-input
                        v-model="formData.specification"
                        placeholder="規格を入力"
                        clearable
                      />
                    </el-form-item>
                  </div>
                </div>
              </div>
            </div>

            <!-- 取引情報 -->
            <div class="form-card">
              <div class="card-header">
                <el-icon class="card-icon"><Coin /></el-icon>
                <span class="card-title">取引情報</span>
              </div>
              <div class="card-content">
                <div class="form-row">
                  <div class="form-col">
                    <el-form-item label="単価" prop="unit_price">
                      <el-input-number
                        v-model="formData.unit_price"
                        :min="0"
                        :precision="2"
                        :controls="false"
                        placeholder="0.00"
                        class="full-width"
                      />
                    </el-form-item>
                  </div>
                  <div class="form-col">
                    <el-form-item label="リードタイム" prop="delivery_lead_time">
                      <div class="input-with-unit">
                        <el-input-number
                          v-model="formData.delivery_lead_time"
                          :min="0"
                          :max="365"
                          :precision="0"
                          :controls="false"
                          class="full-width"
                        />
                        <span class="unit-badge">日</span>
                      </div>
                    </el-form-item>
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-col">
                    <el-form-item label="納入場所" prop="delivery_location">
                      <el-select
                        v-model="formData.delivery_location"
                        placeholder="選択"
                        clearable
                        class="full-width"
                      >
                        <el-option label="仕上倉庫ヤード下" value="仕上倉庫ヤード下" />
                        <el-option label="引き取り" value="引き取り" />
                        <el-option label="その他" value="その他" />
                      </el-select>
                    </el-form-item>
                  </div>
                  <div class="form-col">
                    <el-form-item label="区分" prop="category">
                      <el-select
                        v-model="formData.category"
                        placeholder="選択"
                        clearable
                        class="full-width"
                      >
                        <el-option label="ステー無償支給" value="ステー無償支給" />
                        <el-option label="ステー有償支給" value="ステー有償支給" />
                        <el-option label="材料無償支給" value="材料無償支給" />
                        <el-option label="材料有償支給" value="材料有償支給" />
                      </el-select>
                    </el-form-item>
                  </div>
                </div>
              </div>
            </div>

            <!-- その他情報 -->
            <div class="form-card full-width">
              <div class="card-header">
                <el-icon class="card-icon"><Tickets /></el-icon>
                <span class="card-title">その他情報</span>
              </div>
              <div class="card-content">
                <div class="form-row">
                  <div class="form-col">
                    <el-form-item label="内容" prop="content">
                      <el-select
                        v-model="formData.content"
                        placeholder="内容を選択"
                        clearable
                        class="full-width"
                      >
                        <el-option label="メッキ塗装" value="メッキ塗装" />
                        <el-option label="ブラケット溶接" value="ブラケット溶接" />
                        <el-option label="ステー加工" value="ステー加工" />
                        <el-option label="部品加工" value="部品加工" />
                      </el-select>
                    </el-form-item>
                  </div>
                  <div class="form-col">
                    <el-form-item label="備考" prop="remarks">
                      <el-input
                        v-model="formData.remarks"
                        placeholder="備考を入力"
                        clearable
                        :maxlength="200"
                        show-word-limit
                      />
                    </el-form-item>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-form>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false" size="default">キャンセル</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting" size="default">
            <el-icon v-if="!submitting"><Check /></el-icon>
            {{ isEdit ? '更新' : '登録' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus'
import {
  Filter,
  Refresh,
  Search,
  Plus,
  Edit,
  Delete,
  Check,
  Grid,
  Scissor,
  Box,
  Coin,
  Connection,
  View,
  Tools,
  OfficeBuilding,
  Tickets,
  CircleCheck,
} from '@element-plus/icons-vue'
import {
  getProcessProducts,
  getProcessProductStats,
  createProcessProduct,
  updateProcessProduct,
  deleteProcessProduct,
  toggleProcessProductStatus,
  getSuppliers,
  type OutsourcingProcessProduct,
} from '@/api/outsourcing'
import { getProductOptions } from '@/api/options'

// 状态
const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const tableData = ref<OutsourcingProcessProduct[]>([])
const formRef = ref<FormInstance>()
const activeProcessType = ref('all')

// 下拉框数据
const suppliersList = ref<Array<{ supplier_cd: string; supplier_name?: string }>>([])
const suppliersLoading = ref(false)
const productsList = ref<Array<{ cd: string; name: string }>>([])
const productsLoading = ref(false)

// 统计数据
const stats = ref({
  total: 0,
  active: 0,
  suppliers: 0,
})

// 工程统计
const processStats = ref<Record<string, number>>({})

// 筛选表单
const filters = reactive({
  keyword: '',
  supplierCd: '',
  productCd: '',
  isActive: 'all',
})

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 50,
  total: 0,
})

// 编辑表单
const formData = reactive<Partial<OutsourcingProcessProduct>>({
  process_type: undefined,
  supplier_cd: '',
  supplier_name: '',
  product_cd: '',
  product_name: '',
  specification: '',
  unit_price: 0,
  delivery_lead_time: 3,
  delivery_location: '仕上倉庫ヤード下',
  category: '',
  content: '',
  remarks: '',
})

// 表单验证规则
const formRules: FormRules = {
  process_type: [{ required: true, message: '工程種別を選択してください', trigger: 'change' }],
  supplier_cd: [
    { required: true, message: '外注先コードを入力してください', trigger: 'blur' },
    { max: 20, message: '外注先コードは20文字以内で入力してください', trigger: 'blur' },
  ],
  product_cd: [
    { required: true, message: '品番を入力してください', trigger: 'blur' },
    { max: 50, message: '品番は50文字以内で入力してください', trigger: 'blur' },
  ],
  supplier_name: [
    { max: 100, message: '外注先名は100文字以内で入力してください', trigger: 'blur' },
  ],
  product_name: [{ max: 200, message: '品名は200文字以内で入力してください', trigger: 'blur' }],
}

// 方法
const fetchData = async () => {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      page: pagination.page,
      pageSize: pagination.pageSize,
      isActive: filters.isActive,
    }

    if (activeProcessType.value !== 'all') {
      params.processType = activeProcessType.value
    }
    if (filters.keyword) {
      params.keyword = filters.keyword
    }
    if (filters.supplierCd) {
      params.supplierCd = filters.supplierCd
    }
    if (filters.productCd) {
      params.productCd = filters.productCd
    }

    const res = await getProcessProducts(params)

    if (res?.success) {
      tableData.value = Array.isArray(res.data) ? res.data : []
      if (res.pagination) {
        pagination.total = res.pagination.total || 0
        pagination.page = res.pagination.page || pagination.page
        pagination.pageSize = res.pagination.pageSize || pagination.pageSize
      } else {
        pagination.total = res.data?.length || 0
      }
    } else if (res?.data?.success) {
      const data = res.data as { data?: OutsourcingProcessProduct[]; pagination?: { total: number; page: number; pageSize: number } }
      tableData.value = Array.isArray(data.data) ? data.data : []
      if (data.pagination) {
        pagination.total = data.pagination.total || 0
        pagination.page = data.pagination.page || pagination.page
        pagination.pageSize = data.pagination.pageSize || pagination.pageSize
      } else {
        pagination.total = data.data?.length || 0
      }
    } else {
      tableData.value = []
      pagination.total = 0
    }

    await fetchStats()
  } catch (error) {
    console.error('データ取得エラー:', error)
    ElMessage.error('データの取得に失敗しました')
    tableData.value = []
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    const res = await getProcessProductStats()

    if (res?.success) {
      const data = res.data || {}
      stats.value = {
        total: data.total?.total_count ?? data.total_count ?? tableData.value.length ?? 0,
        active:
          data.total?.active_count ??
          data.active_count ??
          tableData.value.filter((item) => item.is_active).length ??
          0,
        suppliers:
          data.total?.supplier_count ??
          data.supplier_count ??
          new Set(tableData.value.map((item) => item.supplier_cd)).size ??
          0,
      }

      const byProcess = data.byProcessType || data.by_process_type || []
      processStats.value = {}
      byProcess.forEach((item: { process_type: string; total_count: number }) => {
        processStats.value[item.process_type] = item.total_count || 0
      })
    } else if (res?.data?.success) {
      const inner = (res as { data: { data?: unknown; total?: { total_count: number; active_count: number; supplier_count: number }; byProcessType?: Array<{ process_type: string; total_count: number }> } }).data
      const data = inner.data || inner
      stats.value = {
        total: (data as { total?: { total_count: number } }).total?.total_count ?? 0,
        active: (data as { total?: { active_count: number } }).total?.active_count ?? 0,
        suppliers: (data as { total?: { supplier_count: number } }).total?.supplier_count ?? 0,
      }
      const byProcess = (data as { byProcessType?: Array<{ process_type: string; total_count: number }> }).byProcessType || []
      processStats.value = {}
      byProcess.forEach((item) => {
        processStats.value[item.process_type] = item.total_count || 0
      })
    } else {
      const uniqueSuppliers = new Set(tableData.value.map((item) => item.supplier_cd))
      stats.value = {
        total: tableData.value.length,
        active: tableData.value.filter((item) => item.is_active).length,
        suppliers: uniqueSuppliers.size,
      }
      processStats.value = {}
      tableData.value.forEach((item) => {
        const type = item.process_type || ''
        processStats.value[type] = (processStats.value[type] || 0) + 1
      })
    }
  } catch (error) {
    console.error('統計取得エラー:', error)
    const uniqueSuppliers = new Set(tableData.value.map((item) => item.supplier_cd))
    stats.value = {
      total: tableData.value.length,
      active: tableData.value.filter((item) => item.is_active).length,
      suppliers: uniqueSuppliers.size,
    }
  }
}

const fetchSuppliers = async () => {
  suppliersLoading.value = true
  try {
    const res = await getSuppliers({ isActive: true })
    if (res?.success || (res as { data?: { success?: boolean } }).data?.success) {
      const data = res.data || res
      suppliersList.value = Array.isArray(data) ? data : (data as { data?: unknown[] }).data || []
    } else if (Array.isArray(res)) {
      suppliersList.value = res
    } else {
      suppliersList.value = []
    }
  } catch (error) {
    console.error('外注先リスト取得エラー:', error)
    suppliersList.value = []
  } finally {
    suppliersLoading.value = false
  }
}

const fetchProducts = async () => {
  productsLoading.value = true
  try {
    const products = await getProductOptions()
    productsList.value = products || []
  } catch (error) {
    console.error('製品リスト取得エラー:', error)
    productsList.value = []
  } finally {
    productsLoading.value = false
  }
}

const handleSupplierChange = (supplierCd: string) => {
  if (supplierCd) {
    const supplier = suppliersList.value.find((s) => s.supplier_cd === supplierCd)
    if (supplier) {
      formData.supplier_name = supplier.supplier_name || ''
    }
  } else {
    formData.supplier_name = ''
  }
}

const handleProductChange = (productCd: string) => {
  if (productCd) {
    const product = productsList.value.find((p) => p.cd === productCd)
    if (product) {
      formData.product_name = product.name || ''
    }
  } else {
    formData.product_name = ''
  }
}

const getProcessCount = (type: string) => {
  if (type === 'all') {
    return stats.value.total
  }
  return processStats.value[type] || 0
}

const handleTabChange = () => {
  pagination.page = 1
  fetchData()
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const clearFilters = () => {
  filters.keyword = ''
  filters.supplierCd = ''
  filters.productCd = ''
  filters.isActive = 'all'
  pagination.page = 1
  fetchData()
}

const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.page = 1
  fetchData()
}

const handlePageChange = (page: number) => {
  pagination.page = page
  fetchData()
}

const handleAdd = () => {
  isEdit.value = false
  resetForm()
  if (activeProcessType.value !== 'all') {
    formData.process_type = activeProcessType.value
  }
  fetchSuppliers()
  fetchProducts()
  dialogVisible.value = true
}

const handleEdit = (row: OutsourcingProcessProduct) => {
  isEdit.value = true
  Object.assign(formData, row)
  fetchSuppliers()
  fetchProducts()
  dialogVisible.value = true
}

const handleToggleStatus = async (row: OutsourcingProcessProduct) => {
  if (row.id == null) return
  const action = row.is_active ? '無効化' : '有効化'
  try {
    await ElMessageBox.confirm(
      `「${row.product_name || row.product_cd}」を${action}しますか？`,
      '確認',
      { type: 'warning' },
    )
    await toggleProcessProductStatus(row.id)
    ElMessage.success(`${action}しました`)
    fetchData()
    fetchStats()
  } catch (error: unknown) {
    if (error !== 'cancel') {
      ElMessage.error(`${action}に失敗しました`)
    }
  }
}

const handleDelete = async (row: OutsourcingProcessProduct) => {
  if (row.id == null) return
  try {
    await ElMessageBox.confirm(
      `「${row.product_name || row.product_cd}」を削除しますか？`,
      '削除確認',
      { type: 'warning', confirmButtonText: '削除', confirmButtonClass: 'el-button--danger' },
    )
    await deleteProcessProduct(row.id)
    ElMessage.success('削除しました')
    fetchData()
    fetchStats()
  } catch (error: unknown) {
    if (error !== 'cancel') {
      ElMessage.error('削除に失敗しました')
    }
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      if (isEdit.value && formData.id != null) {
        await updateProcessProduct(formData.id, formData)
        ElMessage.success('更新しました')
      } else {
        await createProcessProduct(formData)
        ElMessage.success('登録しました')
      }
      dialogVisible.value = false
      fetchData()
      fetchStats()
    } catch (error: unknown) {
      const err = error as { response?: { data?: { message?: string } } }
      const errorMessage =
        err?.response?.data?.message ||
        (isEdit.value ? '更新に失敗しました' : '登録に失敗しました')
      ElMessage.error(errorMessage)
    } finally {
      submitting.value = false
    }
  })
}

const resetForm = () => {
  formData.id = undefined
  formData.process_type = undefined
  formData.supplier_cd = ''
  formData.supplier_name = ''
  formData.product_cd = ''
  formData.product_name = ''
  formData.specification = ''
  formData.unit_price = 0
  formData.delivery_lead_time = 3
  formData.delivery_location = '仕上倉庫ヤード下'
  formData.category = ''
  formData.content = ''
  formData.remarks = ''
}

const getProcessTypeColor = (
  type: string,
): 'primary' | 'success' | 'warning' | 'danger' | 'info' => {
  const colors: Record<string, 'primary' | 'success' | 'warning' | 'danger' | 'info'> = {
    cutting: 'primary',
    forming: 'success',
    plating: 'warning',
    welding: 'danger',
    inspection: 'info',
    processing: 'primary',
  }
  return colors[type] || 'info'
}

const formatPrice = (price: number | undefined) => {
  if (price === undefined || price === null) return '-'
  return `¥${price.toLocaleString('ja-JP', { minimumFractionDigits: 2 })}`
}

onMounted(() => {
  fetchData()
  fetchStats()
})
</script>

<style scoped lang="scss">
.outsourcing-products-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  padding: 12px 16px;
  font-family: 'Hiragino Sans', 'Hiragino Kaku Gothic ProN', 'Noto Sans JP', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  font-size: 14px;
  line-height: 1.5;
  color: #1e293b;
}

.page-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 12px;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.25);
  position: relative;
  overflow: hidden;
}

.page-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, transparent 100%);
  pointer-events: none;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  position: relative;
  z-index: 1;
}

.title-section {
  flex: 1;
  color: white;
}

.main-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 1.35rem;
  font-weight: 700;
  margin: 0 0 4px 0;
  color: #fff;
  letter-spacing: 0.02em;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.title-icon {
  font-size: 1.5rem;
  opacity: 0.95;
}

.subtitle {
  font-size: 0.8125rem;
  color: rgba(255, 255, 255, 0.92);
  margin: 0;
  font-weight: 500;
  letter-spacing: 0.02em;
}

.header-stats {
  display: flex;
  gap: 8px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(10px);
  border-radius: 8px;
  padding: 8px 12px;
  text-align: center;
  min-width: 70px;
  border: 1px solid rgba(255, 255, 255, 0.25);
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.stat-card:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
}

.stat-card-active {
  background: rgba(16, 185, 129, 0.25);
  border-color: rgba(16, 185, 129, 0.4);
}

.stat-card-suppliers {
  background: rgba(59, 130, 246, 0.25);
  border-color: rgba(59, 130, 246, 0.4);
}

.stat-number {
  font-size: 1.25rem;
  font-weight: 700;
  color: #fff;
  margin-bottom: 2px;
  line-height: 1.3;
  letter-spacing: 0.02em;
}

.stat-label {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.98);
  font-weight: 600;
  letter-spacing: 0.04em;
}

.process-tabs-section {
  margin-bottom: 12px;
}

.process-tabs {
  :deep(.el-tabs__header) {
    margin: 0;
    background: #fff;
    border-radius: 10px;
    padding: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
    border: 1px solid #e2e8f0;
  }

  :deep(.el-tabs__nav-wrap::after) {
    display: none;
  }

  :deep(.el-tabs__item) {
    font-size: 0.8125rem;
    font-weight: 600;
    padding: 8px 14px;
    border-radius: 8px;
    margin-right: 4px;
    color: #475569;
    transition: all 0.2s ease;
    height: auto;
    line-height: 1.45;
    letter-spacing: 0.02em;
  }

  :deep(.el-tabs__item:hover) {
    color: #667eea;
    background: rgba(102, 126, 234, 0.08);
  }

  :deep(.el-tabs__item.is-active) {
    color: white;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    font-weight: 600;
  }

  :deep(.el-tabs__content) {
    display: none;
  }
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 6px;
}

.tab-badge {
  :deep(.el-badge__content) {
    background: rgba(102, 126, 234, 0.2);
    color: #667eea;
    border: none;
    font-size: 0.75rem;
    font-weight: 600;
    height: 20px;
    line-height: 20px;
    padding: 0 6px;
    letter-spacing: 0.02em;
  }
}

.process-tabs :deep(.el-tabs__item.is-active) .tab-badge :deep(.el-badge__content) {
  background: rgba(255, 255, 255, 0.25);
  color: white;
}

.action-section {
  background: #fff;
  border-radius: 10px;
  padding: 14px 18px;
  margin-bottom: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
  border: 1px solid #e2e8f0;
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.filter-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9375rem;
  font-weight: 600;
  color: #1e293b;
  letter-spacing: 0.02em;
}

.filter-icon {
  font-size: 1.125rem;
  color: #667eea;
}

.filter-actions {
  display: flex;
  gap: 6px;
}

.filters-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.filter-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8125rem;
  font-weight: 600;
  color: #475569;
  letter-spacing: 0.02em;
}

.filter-input,
.filter-select {
  width: 100%;
}

.filter-input :deep(.el-input__wrapper),
.filter-select :deep(.el-select__wrapper) {
  font-size: 0.875rem;
  padding: 6px 12px;
}
.filter-input :deep(.el-input__inner) {
  font-size: 0.875rem;
  color: #334155;
}

.table-section {
  margin-bottom: 12px;
}

.table-card :deep(.el-table__empty-text) {
  font-size: 0.9375rem;
  color: #64748b;
  font-weight: 500;
}

.table-card {
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.table-card :deep(.el-card__body) {
  padding: 0;
}

.table-card :deep(.el-table th) {
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  color: #1e293b;
  font-weight: 600;
  padding: 10px 12px;
  border-bottom: 2px solid #e2e8f0;
  font-size: 0.8125rem;
  height: 44px;
  letter-spacing: 0.02em;
}

.table-card :deep(.el-table td) {
  padding: 8px 12px;
  border-bottom: 1px solid #f1f5f9;
  font-size: 0.8125rem;
  height: 42px;
  color: #334155;
  letter-spacing: 0.01em;
}

.table-card :deep(.el-table--small) .el-table__cell {
  padding: 8px 12px;
}

.table-card :deep(.el-tag) {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 3px 10px;
  height: 22px;
  line-height: 16px;
  letter-spacing: 0.02em;
}

.price-text {
  font-weight: 600;
  color: #047857;
  font-size: 0.875rem;
  letter-spacing: 0.02em;
}

.lead-time {
  font-weight: 600;
  color: #2563eb;
  font-size: 0.875rem;
  letter-spacing: 0.02em;
}

.status-tag {
  font-size: 0.75rem !important;
  font-weight: 600 !important;
  padding: 3px 8px !important;
  height: 22px !important;
  line-height: 16px !important;
  letter-spacing: 0.02em;
}

.action-buttons {
  display: flex;
  gap: 2px;
  justify-content: center;
  align-items: center;
}

.action-btn-edit,
.action-btn-toggle,
.action-btn-delete {
  padding: 5px 10px;
  font-size: 0.8125rem;
  font-weight: 500;
  height: 28px;
  min-height: 28px;
  letter-spacing: 0.02em;
}

.action-btn-edit :deep(.el-icon),
.action-btn-delete :deep(.el-icon) {
  font-size: 14px;
}

.pagination-section {
  background: #fff;
  border-radius: 10px;
  padding: 12px 18px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
  border: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
}

.pagination-section :deep(.el-pagination) {
  font-size: 0.875rem;
  font-weight: 500;
}

.modern-dialog {
  :deep(.el-dialog) {
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.2);
  }

  :deep(.el-dialog__header) {
    padding: 0;
    border-bottom: none;
    background: transparent;
  }

  :deep(.el-dialog__headerbtn) {
    top: 16px;
    right: 16px;
    width: 28px;
    height: 28px;
    border-radius: 6px;
    background: rgba(255, 255, 255, 0.15);
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
  }

  :deep(.el-dialog__headerbtn:hover) {
    background: rgba(255, 255, 255, 0.25);
    transform: scale(1.05);
  }

  :deep(.el-dialog__body) {
    padding: 0;
    max-height: 82vh;
    overflow-y: auto;
  }

  :deep(.el-dialog__footer) {
    padding: 12px 20px;
    border-top: 1px solid #e5e7eb;
    background: linear-gradient(180deg, #fafbfc 0%, #f8fafc 100%);
  }
}

.modern-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow: hidden;
}

.modern-header .header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
  z-index: 1;
}

.modern-header .header-icon-wrapper {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.modern-header .header-icon {
  font-size: 20px;
  color: white;
}

.modern-header .header-content {
  color: white;
}

.modern-header .header-title {
  font-size: 1.125rem;
  font-weight: 700;
  margin: 0 0 4px 0;
  letter-spacing: 0.02em;
  line-height: 1.4;
  color: #fff;
}

.modern-header .header-subtitle {
  font-size: 0.8125rem;
  margin: 0;
  opacity: 0.92;
  font-weight: 500;
  line-height: 1.3;
  color: rgba(255, 255, 255, 0.95);
}

.modern-content {
  padding: 16px 20px;
  background: #f8fafc;
  min-height: auto;
}

.process-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 10px;
  padding: 14px 16px;
  margin-bottom: 16px;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.25);
  position: relative;
  overflow: hidden;
}

.process-card .process-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  position: relative;
  z-index: 1;
}

.process-card .process-icon {
  font-size: 18px;
  color: white;
}

.process-card .process-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: white;
  letter-spacing: 0.025em;
}

.process-card .process-select-item {
  margin-bottom: 0;
  position: relative;
  z-index: 1;
}

.process-card .process-select-item :deep(.el-form-item__label) {
  display: none;
}

.process-card .process-select :deep(.el-select__wrapper) {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  font-size: 0.9rem;
  height: 40px;
}

.option-content {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  font-size: 0.9rem;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.form-card {
  background: white;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
  overflow: hidden;
}

.form-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.form-card.full-width {
  grid-column: 1 / -1;
}

.form-card .card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 1px solid #e5e7eb;
}

.form-card .card-icon {
  font-size: 16px;
  color: #667eea;
}

.form-card .card-title {
  font-size: 0.9375rem;
  font-weight: 600;
  color: #1e293b;
  letter-spacing: 0.03em;
}

.form-card .card-content {
  padding: 14px;
}

.form-row {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.form-row:last-child {
  margin-bottom: 0;
}

.form-col {
  flex: 1;
}

.form-col.full {
  flex: 1 1 100%;
}

.modern-form :deep(.el-form-item) {
  margin-bottom: 0;
  display: flex;
  align-items: center;
  flex-direction: row;
}

.modern-form :deep(.form-row .el-form-item) {
  margin-bottom: 0;
}

.modern-form :deep(.el-form-item__label) {
  font-weight: 600;
  color: #1e293b;
  font-size: 0.875rem;
  margin-bottom: 0;
  margin-right: 8px;
  line-height: 1.4;
  padding-bottom: 0;
  padding-top: 0;
  white-space: nowrap;
  flex-shrink: 0;
  height: auto;
  letter-spacing: 0.02em;
}

.modern-form :deep(.el-form-item__content) {
  flex: 1;
  margin-left: 0;
  line-height: 1;
}

.modern-form :deep(.el-form-item__error) {
  font-size: 0.75rem;
  padding-top: 4px;
  color: #dc2626;
}

.modern-form :deep(.el-input .el-input__wrapper),
.modern-form :deep(.el-select .el-select__wrapper),
.modern-form :deep(.el-input-number .el-input__wrapper) {
  border-radius: 8px;
  border: 1.5px solid #e2e8f0;
  transition: all 0.2s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  min-height: 36px;
  font-size: 0.875rem;
  color: #334155;
}

.modern-form .full-width {
  width: 100%;
}

.input-with-unit {
  position: relative;
  width: 100%;
}

.input-with-unit .unit-badge {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  background: #667eea;
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 600;
  pointer-events: none;
  z-index: 10;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.filter-actions :deep(.el-button--primary) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  box-shadow: 0 2px 6px rgba(102, 126, 234, 0.3);
}

.filter-actions :deep(.el-button--success) {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border: none;
  box-shadow: 0 2px 6px rgba(16, 185, 129, 0.3);
}

@media (max-width: 1200px) {
  .filters-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    align-items: flex-start;
  }

  .header-stats {
    width: 100%;
    justify-content: space-between;
  }

  .filters-grid {
    grid-template-columns: 1fr;
  }

  .filter-actions {
    flex-wrap: wrap;
  }
}

.table-card :deep(.el-table__body-wrapper)::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.table-card :deep(.el-table__body-wrapper)::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.table-card :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}
</style>
