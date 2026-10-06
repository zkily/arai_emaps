<template>
  <div class="outsourcing-products-page opp-modern pb-std">
    <!-- 页面头部 -->
    <div class="page-header pb-hero pb-hero--page">
      <div class="head-fx pb-bubbles" aria-hidden="true" />
      <div class="header-content">
        <div class="title-section">
          <span class="title-icon-wrap" aria-hidden="true">
            <el-icon class="title-icon"><OfficeBuilding /></el-icon>
          </span>
          <div class="title-text">
            <h1 class="main-title pb-hero-title">外注工程製品管理</h1>
            <p class="subtitle pb-hero-desc">
              工程ごとに外注先・製品の単価・リードタイム・納入条件を登録し、有効／無効を管理
            </p>
          </div>
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

    <!-- 功能操作区域（自动筛选：外注先・キーワード・状態変更時に自動で一覧取得） -->
    <div class="action-section">
      <div class="filter-header">
        <div class="filter-title">
          <el-icon class="filter-icon"><Filter /></el-icon>
          <span>絞り込み</span>
        </div>
        <div class="filter-actions">
          <el-button type="success" @click="handleAdd" :icon="Plus" class="add-btn">
            新規登録
          </el-button>
        </div>
      </div>

      <div class="filters-grid">
        <div class="filter-item">
          <label class="filter-label">
            <el-icon><OfficeBuilding /></el-icon>
            外注先
          </label>
          <el-select
            v-model="filters.supplierCd"
            placeholder="外注先を選択"
            clearable
            filterable
            :loading="suppliersLoading"
            class="filter-select filter-select-supplier"
            value-key="supplier_cd"
            @change="onFilterChange"
          >
            <el-option
              v-for="s in suppliersList"
              :key="s.supplier_cd"
              :label="`${s.supplier_cd} ${s.supplier_name || ''}`.trim()"
              :value="s.supplier_cd"
            />
          </el-select>
        </div>
        <div class="filter-item">
          <label class="filter-label">
            <el-icon><Search /></el-icon>
            キーワード
          </label>
          <el-input
            v-model="filters.keyword"
            placeholder="品番・品名で検索"
            clearable
            @clear="onFilterChange"
            @keyup.enter="onFilterChange"
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
            @change="onFilterChange"
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
          height="calc(100vh - 340px)"
          :row-style="{ height: '32px' }"
          size="small"
          class="compact-table"
        >
          <el-table-column
            prop="process_type_name"
            label="工程種別"
            width="100"
            align="center"
            fixed="left"
          >
            <template #default="{ row }">
              <el-tag :type="getProcessTypeColor(row.process_type)" size="small" effect="plain" class="process-tag">
                {{ row.process_type_name }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            prop="supplier_cd"
            label="外注先CD"
            width="100"
            align="center"
            show-overflow-tooltip
          />
          <el-table-column
            prop="supplier_name"
            label="外注先名"
            width="130"
            align="center"
            show-overflow-tooltip
          />
          <el-table-column
            prop="product_cd"
            label="製品CD"
            width="88"
            align="center"
            show-overflow-tooltip
          />
          <el-table-column prop="product_name" label="品名" width="120" align="center" show-overflow-tooltip />
          <el-table-column prop="specification" label="規格" width="88" align="center" show-overflow-tooltip />
          <el-table-column prop="unit_price" label="単価" width="88" align="center">
            <template #default="{ row }">
              <span class="price-text">{{ formatPrice(row.unit_price) }}</span>
            </template>
          </el-table-column>
          <el-table-column
            prop="delivery_lead_time"
            label="納入リード"
            width="90"
            align="center"
          >
            <template #default="{ row }">
              <span class="lead-time">{{ row.delivery_lead_time ?? '-' }}日</span>
            </template>
          </el-table-column>
          <el-table-column
            prop="delivery_location"
            label="納入場所"
            width="130"
            align="center"
            show-overflow-tooltip
          />
          <el-table-column prop="category" label="区分" width="110" align="center" show-overflow-tooltip />
          <el-table-column prop="content" label="内容" width="88" align="center" show-overflow-tooltip />
          <el-table-column prop="is_active" label="状態" width="72" align="center">
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
          <el-table-column label="操作" width="180" align="center" fixed="right">
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
      class="modern-dialog opp-dialog pb-std"
      destroy-on-close
      top="3vh"
      :show-close="false"
    >
      <template #header>
        <div class="modern-header pb-hero" :class="isEdit ? 'is-edit' : 'is-new'">
          <div class="head-fx pb-bubbles" aria-hidden="true" />
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
            <span class="mode-badge" :class="isEdit ? 'edit' : 'new'">
              {{ isEdit ? '編集モード' : '新規登録' }}
            </span>
            <el-icon class="dh-close" @click="dialogVisible = false"><Close /></el-icon>
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
          <el-button class="dlg-btn" @click="dialogVisible = false" size="default">
            キャンセル
          </el-button>
          <el-button
            type="primary"
            class="dlg-btn dlg-btn--save"
            @click="handleSubmit"
            :loading="submitting"
            size="default"
          >
            <el-icon v-if="!submitting"><Check /></el-icon>
            {{ isEdit ? '更新' : '登録' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus'
import {
  Filter,
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
  CircleCheck,
  Close,
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
import { usePurchaseOperationPermission } from '@/composables/usePurchaseOperationPermission'
import { guardPurchaseOperation } from '@/utils/purchaseOperationGuard'

const { canCreate, canEdit, canDelete, canExport, canApprove } = usePurchaseOperationPermission()


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

// 筛选表单（外注先下拉来自 outsourcing_suppliers）
const filters = reactive({
  keyword: '',
  supplierCd: '',
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

    // request 拦截器已返回 response.data，故 raw 即为后端 body: { success, data, pagination }
    const raw = (await getProcessProducts(params)) as unknown as { success?: boolean; data?: OutsourcingProcessProduct[]; pagination?: { total: number; page: number; pageSize: number } }
    if (raw?.success) {
      tableData.value = Array.isArray(raw.data) ? raw.data : []
      if (raw.pagination) {
        pagination.total = raw.pagination.total ?? 0
        pagination.page = raw.pagination.page ?? pagination.page
        pagination.pageSize = raw.pagination.pageSize ?? pagination.pageSize
      } else {
        pagination.total = raw.data?.length ?? 0
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
    // request 拦截器已返回 response.data，raw 即为 body: { success, data: { total, byProcessType } }
    const raw = (await getProcessProductStats()) as unknown as { success?: boolean; data?: { total?: { total_count?: number; active_count?: number; supplier_count?: number }; byProcessType?: Array<{ process_type: string; total_count: number }> } }
    if (raw?.success && raw.data) {
      const d = raw.data
      const t = d.total
      stats.value = {
        total: t?.total_count ?? tableData.value.length ?? 0,
        active: t?.active_count ?? tableData.value.filter((item) => item.is_active).length ?? 0,
        suppliers: t?.supplier_count ?? new Set(tableData.value.map((item) => item.supplier_cd)).size ?? 0,
      }
      const byProcess = d.byProcessType || []
      processStats.value = {}
      byProcess.forEach((item: { process_type: string; total_count: number }) => {
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
    // request 拦截器已返回 response.data，raw 即为 body: { success, data: [...] }
    const raw = (await getSuppliers({ isActive: true })) as unknown as { success?: boolean; data?: Array<{ supplier_cd?: string; supplier_name?: string }> }
    const arr = Array.isArray(raw?.data) ? raw.data : []
    suppliersList.value = arr.map((s) => ({
      supplier_cd: s.supplier_cd ?? '',
      supplier_name: s.supplier_name,
    }))
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

/** 筛选条件变更时自动查询（外注先・状態选择、キーワード回车/清空时调用） */
const onFilterChange = () => {
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
  if (!guardPurchaseOperation(canEdit)) return

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
  if (!guardPurchaseOperation(canDelete)) return

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
  if (!guardPurchaseOperation(canEdit)) return

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

// キーワード输入防抖后自动筛选
let keywordTimer: ReturnType<typeof setTimeout> | null = null
watch(
  () => filters.keyword,
  () => {
    if (keywordTimer) clearTimeout(keywordTimer)
    keywordTimer = setTimeout(() => {
      pagination.page = 1
      fetchData()
      keywordTimer = null
    }, 350)
  },
)

onMounted(() => {
  fetchSuppliers()
  fetchData()
  fetchStats()
})
</script>

<style scoped lang="scss">
.outsourcing-products-page {
  min-height: 100vh;
  padding: 8px 12px;
  box-sizing: border-box;
  font-family:
    'Hiragino Sans', 'Hiragino Kaku Gothic ProN', 'Noto Sans JP', -apple-system,
    BlinkMacSystemFont, 'Segoe UI', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  font-size: 13px;
  line-height: 1.45;
  color: #1e293b;
  background: linear-gradient(180deg, #f3f1ff 0%, #f8fafc 32%, #f8fafc 100%);
}

/* ============================================================ */
/* 页面美化：现代 UI / 颜色区分（外注工程製品＝バイオレット系）      */
/* ============================================================ */

/* ---------- ヒーロー ---------- */
.page-header {
  position: relative;
  overflow: hidden;
  margin-bottom: 8px;
  border-radius: 14px;
  background: linear-gradient(125deg, #4c51bf 0%, #5a67d8 36%, #667eea 62%, #764ba2 100%);
  box-shadow:
    0 12px 28px -18px rgba(102, 126, 234, 0.65),
    0 1px 2px rgba(15, 23, 42, 0.06);
}

.header-content {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px 16px;
}

.title-section {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon-wrap {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: linear-gradient(150deg, rgba(255, 255, 255, 0.36), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.42);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(49, 46, 129, 0.3);
}

.title-icon {
  font-size: 20px;
  color: #fff;
}

.title-text {
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.main-title {
  margin: 0;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: #fff;
}

.subtitle {
  margin: 0;
  letter-spacing: 0.02em;
  color: rgba(255, 255, 255, 0.86);
}

/* 統計：濃色ヒーロー上の白カード（数字色で区別） */
.header-stats {
  display: flex;
  gap: 6px;
}

.stat-card {
  --sc: #5b21b6;
  min-width: 64px;
  padding: 5px 12px;
  text-align: center;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.9);
  background: linear-gradient(180deg, #ffffff 0%, #f3f1ff 100%);
  box-shadow:
    inset 0 1px 0 #ffffff,
    inset 0 -2px 0 rgba(148, 163, 184, 0.25),
    0 6px 14px -10px rgba(15, 23, 42, 0.45);
}

.stat-card-active {
  --sc: #047857;
}

.stat-card-suppliers {
  --sc: #1d4ed8;
}

.stat-number {
  margin: 0;
  font-size: 18px;
  font-weight: 800;
  line-height: 1.15;
  color: var(--sc);
  font-variant-numeric: tabular-nums;
}

.stat-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #64748b;
}

/* ---------- 工程タブ（セグメントピル） ---------- */
.process-tabs-section {
  margin-bottom: 8px;
}

.process-tabs {
  :deep(.el-tabs__header) {
    margin: 0;
    padding: 5px 6px;
    border-radius: 12px;
    border: 1px solid #e4e1fb;
    background: #fff;
    box-shadow:
      0 1px 2px rgba(15, 23, 42, 0.04),
      0 10px 24px -22px rgba(91, 33, 182, 0.45);
  }

  :deep(.el-tabs__nav-wrap::after) {
    display: none;
  }

  :deep(.el-tabs__nav) {
    gap: 4px;
    padding: 3px;
    border: none !important;
    border-radius: 10px;
    background: #f1eefe;
    box-shadow: inset 0 1px 2px rgba(76, 29, 149, 0.08);
  }

  :deep(.el-tabs__item) {
    height: auto;
    padding: 5px 12px !important;
    border: none !important;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 700;
    line-height: 1.4;
    letter-spacing: 0.02em;
    color: #6b5b95;
    transition:
      background-color 0.18s ease,
      color 0.18s ease,
      box-shadow 0.18s ease;
  }

  :deep(.el-tabs__item:hover) {
    color: #5b21b6;
  }

  :deep(.el-tabs__item.is-active) {
    color: #4c1d95;
    background: linear-gradient(180deg, #ffffff 0%, #faf8ff 100%);
    box-shadow:
      inset 0 1px 0 #ffffff,
      inset 0 -2px 0 #ddd6fe,
      0 2px 6px -2px rgba(91, 33, 182, 0.3);
  }

  :deep(.el-tabs__content) {
    display: none;
  }
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 4px;
}

.tab-badge {
  :deep(.el-badge__content) {
    height: 18px;
    padding: 0 6px;
    border: none;
    border-radius: 999px;
    font-size: 10.5px;
    font-weight: 700;
    line-height: 18px;
    color: #6d28d9;
    background: #ede9fe;
  }
}

.process-tabs :deep(.el-tabs__item.is-active) .tab-badge :deep(.el-badge__content) {
  color: #fff;
  background: linear-gradient(135deg, #8b5cf6, #6d28d9);
}

/* ---------- 絞り込みカード ---------- */
.action-section {
  position: relative;
  overflow: hidden;
  margin-bottom: 8px;
  padding: 11px 12px 10px;
  border-radius: 12px;
  border: 1px solid #e4e1fb;
  background: linear-gradient(180deg, #ffffff 0%, #faf9ff 100%);
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 10px 24px -20px rgba(91, 33, 182, 0.45);

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #667eea 0%, #8b5cf6 60%, #a78bfa 100%);
  }
}

.filter-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  margin-bottom: 8px;
}

.filter-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.02em;
  color: #4c1d95;
}

.filter-icon {
  width: 24px;
  height: 24px;
  padding: 5px;
  box-sizing: border-box;
  border-radius: 7px;
  font-size: 14px;
  color: #fff;
  background: linear-gradient(135deg, #a78bfa, #6d28d9);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(76, 29, 149, 0.3);
}

.filter-actions {
  display: flex;
  gap: 4px;
}

.add-btn {
  --k-rgb: 5 150 105;
  height: 30px;
  padding: 0 14px;
  border-radius: 8px;
  font-weight: 700;
  color: #fff;
  border: 1px solid #047857;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #34d399, #059669);

  &:hover,
  &:focus-visible {
    color: #fff;
    border-color: #065f46;
    background:
      linear-gradient(180deg, rgba(255, 255, 255, 0.26) 0%, rgba(255, 255, 255, 0) 52%),
      linear-gradient(135deg, #4ade80, #10b981);
  }
}

.filters-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px 10px;
}

.filter-item {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.filter-label {
  align-self: flex-start;
  height: 20px;
  padding: 0 9px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: #4c1d95;
  background: #f1eefe;
  box-shadow:
    inset 0 1px 0 #ffffff,
    inset 0 -1px 0 #ddd6fe;
}

.filter-input,
.filter-select {
  width: 100%;
}

/* 入力枠：枠線は wrapper の内側リングのみ（二重線にしない） */
.filter-input :deep(.el-input__wrapper),
.filter-select :deep(.el-select__wrapper) {
  height: 34px;
  min-height: 34px;
  padding: 0 10px;
  box-sizing: border-box;
  align-items: center;
  border-radius: 8px;
  font-size: 13px;
  background-color: #fff;
  box-shadow: 0 0 0 1px #dcd7f7 inset;
}

.filter-input :deep(.el-input__wrapper:hover),
.filter-select :deep(.el-select__wrapper:hover) {
  box-shadow: 0 0 0 1px #c4b5fd inset;
}

.filter-input :deep(.el-input__wrapper.is-focus),
.filter-select :deep(.el-select__wrapper.is-focused) {
  box-shadow:
    0 0 0 1px #7c3aed inset,
    0 0 0 3px rgba(124, 58, 237, 0.14);
}

.filter-input :deep(.el-input__inner) {
  font-size: 13px;
  color: #334155;
}

/* ---------- テーブル ---------- */
.table-section {
  margin-bottom: 8px;
}

.table-card {
  position: relative;
  overflow: hidden;
  border-radius: 12px;
  border: 1px solid #e4e1fb;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 10px 24px -20px rgba(91, 33, 182, 0.4);

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    z-index: 5;
    height: 3px;
    background: linear-gradient(90deg, #667eea 0%, #8b5cf6 60%, #a78bfa 100%);
  }
}

.table-card :deep(.el-card__body) {
  padding: 0;
}

.table-card :deep(.el-table) {
  --el-table-border-color: #ece9f8;
  --el-table-header-bg-color: #f5f3ff;
  --el-table-row-hover-bg-color: #f3f0ff;
  font-size: 12px;
}

.table-card :deep(.el-table__empty-text) {
  padding: 24px 0;
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
}

.table-card :deep(.el-table th.el-table__cell) {
  height: 34px;
  padding: 4px 6px;
  font-size: 11.5px;
  font-weight: 700;
  letter-spacing: 0.02em;
  text-align: center;
  color: #4c1d95;
  background: #f5f3ff !important;
  border-bottom: 1px solid #ddd6fe;
}

.table-card :deep(.el-table td.el-table__cell) {
  height: 32px;
  padding: 4px 6px;
  font-size: 12px;
  letter-spacing: 0.01em;
  text-align: center;
  color: #334155;
  border-bottom: 1px solid #f1eff9;
}

.table-card :deep(.el-table--small .el-table__cell) {
  padding: 4px 6px;
}

.table-card :deep(.el-table .cell) {
  padding-left: 6px;
  padding-right: 6px;
  text-align: center;
}

.table-card :deep(.el-table__row--striped) {
  --el-table-tr-bg-color: #fcfbff;
}

.table-card :deep(.el-table__body tr:hover > td) {
  background-color: #f3f0ff !important;
}

.table-card :deep(.el-tag.process-tag),
.table-card :deep(.el-tag.status-tag) {
  height: 18px;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 10.5px;
  font-weight: 700;
  line-height: 14px;
  letter-spacing: 0.02em;
}

.price-text {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: #047857;
  font-variant-numeric: tabular-nums;
}

.lead-time {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: #6d28d9;
  font-variant-numeric: tabular-nums;
}

.status-tag {
  height: 18px !important;
  padding: 2px 8px !important;
  font-size: 10.5px !important;
  font-weight: 700 !important;
  line-height: 14px !important;
  letter-spacing: 0.02em;
}

/* 行操作：淡色ピル（種類で色分け） */
.action-buttons {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 4px;

  .el-button + .el-button {
    margin-left: 0;
  }
}

.action-btn-edit,
.action-btn-toggle,
.action-btn-delete {
  --ab-fg: #4338ca;
  --ab-bd: #c7d2fe;
  --ab-bg: #eef2ff;
  --ab-hv: #a5b4fc;
  height: 24px;
  min-height: 24px;
  padding: 2px 9px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--ab-fg);
  border: 1px solid var(--ab-bd);
  background: linear-gradient(180deg, #ffffff 0%, var(--ab-bg) 100%);

  &:hover,
  &:focus-visible {
    color: var(--ab-fg);
    border-color: var(--ab-hv);
    background: #fff;
  }
}

.action-btn-edit {
  --k-rgb: 79 70 229;
}

.action-btn-toggle.el-button--warning {
  --k-rgb: 217 119 6;
  --ab-fg: #b45309;
  --ab-bd: #fde68a;
  --ab-bg: #fffbeb;
  --ab-hv: #fbbf24;
}

.action-btn-toggle.el-button--success {
  --k-rgb: 5 150 105;
  --ab-fg: #047857;
  --ab-bd: #a7f3d0;
  --ab-bg: #ecfdf5;
  --ab-hv: #34d399;
}

.action-btn-delete {
  --k-rgb: 225 29 72;
  --ab-fg: #be123c;
  --ab-bd: #fecdd3;
  --ab-bg: #fff1f2;
  --ab-hv: #fda4af;
  width: 26px;
  padding: 0;
}

.action-btn-edit :deep(.el-icon),
.action-btn-delete :deep(.el-icon) {
  font-size: 11px;
}

/* ---------- ページャー ---------- */
.pagination-section {
  display: flex;
  justify-content: flex-end;
  padding: 7px 12px;
  border-radius: 12px;
  border: 1px solid #e4e1fb;
  background: linear-gradient(180deg, #ffffff 0%, #faf9ff 100%);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.pagination-section :deep(.el-pagination) {
  font-size: 13px;
  font-weight: 500;
}

.pagination-section :deep(.el-pagination__total) {
  font-weight: 700;
  color: #5b21b6;
}

.pagination-section :deep(.el-pagination .el-pagination__sizes),
.pagination-section :deep(.el-pagination .el-pager),
.pagination-section :deep(.el-pagination .btn-prev),
.pagination-section :deep(.el-pagination .btn-next) {
  margin: 0 2px;
}

.pagination-section :deep(.el-pager li),
.pagination-section :deep(.btn-prev),
.pagination-section :deep(.btn-next) {
  min-width: 28px;
  height: 28px;
  margin: 0 2px;
  border-radius: 8px;
  color: #5b21b6;
  border: 1px solid #e4e1fb;
  background: linear-gradient(180deg, #ffffff 0%, #f7f5ff 100%);
}

.pagination-section :deep(.el-pager li:not(.is-active):hover) {
  border-color: #c4b5fd;
  background: #fff;
}

.pagination-section :deep(.el-pager li.is-active) {
  color: #fff;
  border-color: #6d28d9;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #8b5cf6, #6d28d9);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(76, 29, 149, 0.35),
    0 4px 10px -6px rgba(109, 40, 217, 0.7);
}

.pagination-section :deep(.btn-prev:disabled),
.pagination-section :deep(.btn-next:disabled) {
  color: #94a3b8;
  border-color: #d1d5db;
  background: #e5e7eb;
}

/* ---------- ダイアログ ---------- */
:global(.el-dialog.opp-dialog) {
  padding: 0;
  overflow: hidden;
  border-radius: 14px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 20px 60px rgba(15, 23, 42, 0.18);
}

:global(.el-dialog.opp-dialog .el-dialog__header) {
  padding: 0;
  margin: 0;
  border-bottom: none;
}

:global(.el-dialog.opp-dialog .el-dialog__body) {
  padding: 0;
  max-height: 78vh;
  overflow-y: auto;
}

:global(.el-dialog.opp-dialog .el-dialog__footer) {
  padding: 10px 16px 14px;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
}

.modern-header {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 18px;
  background: linear-gradient(125deg, #4c51bf 0%, #5a67d8 36%, #667eea 62%, #764ba2 100%);

  &.is-edit {
    background: linear-gradient(125deg, #b45309 0%, #d97706 45%, #f59e0b 100%);
  }
}

.modern-header .header-left {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.modern-header .header-icon-wrapper {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 11px;
  background: linear-gradient(150deg, rgba(255, 255, 255, 0.36), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.42);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(30, 27, 75, 0.25);
}

.modern-header .header-icon {
  font-size: 18px;
  color: #fff;
}

.modern-header .header-content {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.modern-header .header-title {
  margin: 0;
  font-size: 16px;
  font-weight: 800;
  line-height: 1.3;
  letter-spacing: 0.03em;
  color: #fff;
}

.modern-header .header-subtitle {
  margin: 0;
  font-size: 11px;
  line-height: 1.5;
  color: rgba(255, 255, 255, 0.86);
}

.modern-header .header-status {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.mode-badge {
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.04em;
  border: 1px solid rgba(255, 255, 255, 0.9);
  background: #fff;

  &.new {
    color: #047857;
  }

  &.edit {
    color: #b45309;
  }
}

.dh-close {
  flex-shrink: 0;
  width: 30px;
  height: 30px;
  padding: 6px;
  box-sizing: border-box;
  border-radius: 9px;
  font-size: 18px;
  color: #fff;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.25);
  transition:
    transform 0.2s ease,
    background 0.2s ease;

  &:hover {
    background: rgba(255, 255, 255, 0.3);
    transform: translateY(-1px);
  }
}

.modern-content {
  min-height: auto;
  padding: 12px 16px;
  background: #f8fafc;
}

/* 工程種別選択：淡色カード */
.process-card {
  position: relative;
  overflow: hidden;
  margin-bottom: 10px;
  padding: 11px 12px 10px;
  border-radius: 10px;
  border: 1px solid #ddd6fe;
  background: linear-gradient(180deg, #faf8ff 0%, #f3f0ff 100%);

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #667eea 0%, #8b5cf6 60%, #a78bfa 100%);
  }
}

.process-card .process-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.process-card .process-icon {
  width: 24px;
  height: 24px;
  padding: 5px;
  box-sizing: border-box;
  border-radius: 7px;
  font-size: 14px;
  color: #fff;
  background: linear-gradient(135deg, #a78bfa, #6d28d9);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(76, 29, 149, 0.3);
}

.process-card .process-title {
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.025em;
  color: #4c1d95;
}

.process-card .process-select-item {
  margin-bottom: 0;
}

.process-card .process-select-item :deep(.el-form-item__label) {
  display: none;
}

.process-card .process-select :deep(.el-select__wrapper) {
  min-height: 34px;
  border-radius: 8px;
  font-size: 13px;
  background: #fff;
}

.option-content {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.form-card {
  position: relative;
  overflow: hidden;
  border-radius: 10px;
  border: 1px solid #e4e1fb;
  background: #fff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.form-card.full-width {
  grid-column: 1 / -1;
}

.form-card .card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 10px;
  background: linear-gradient(180deg, #faf9ff 0%, #f5f3ff 100%);
  border-bottom: 1px solid #ece9f8;
}

.form-card .card-icon {
  width: 22px;
  height: 22px;
  padding: 4px;
  box-sizing: border-box;
  border-radius: 6px;
  font-size: 13px;
  color: #fff;
  background: linear-gradient(135deg, #818cf8, #6366f1);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(49, 46, 129, 0.3);
}

.form-card .card-title {
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.03em;
  color: #312e81;
}

.form-card .card-content {
  padding: 10px;
}

.form-row {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
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
  display: flex;
  flex-direction: row;
  align-items: center;
  margin-bottom: 0;
}

.modern-form :deep(.form-row .el-form-item) {
  margin-bottom: 0;
}

.modern-form :deep(.el-form-item__label) {
  flex-shrink: 0;
  height: auto;
  margin: 0 6px 0 0;
  padding: 0;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.35;
  white-space: nowrap;
  letter-spacing: 0.02em;
  color: #334155;
}

.modern-form :deep(.el-form-item__content) {
  flex: 1;
  margin-left: 0;
  line-height: 1;
}

.modern-form :deep(.el-form-item__error) {
  padding-top: 2px;
  font-size: 11px;
  color: #dc2626;
}

.modern-form :deep(.el-input__wrapper),
.modern-form :deep(.el-select__wrapper) {
  min-height: 32px;
  border-radius: 8px;
  font-size: 13px;
  color: #334155;
  box-shadow: 0 0 0 1px #dcd7f7 inset;
  transition: box-shadow 0.2s ease;
}

.modern-form :deep(.el-input__wrapper:hover),
.modern-form :deep(.el-select__wrapper:hover) {
  box-shadow: 0 0 0 1px #c4b5fd inset;
}

.modern-form :deep(.el-input__wrapper.is-focus),
.modern-form :deep(.el-select__wrapper.is-focused) {
  box-shadow:
    0 0 0 1px #7c3aed inset,
    0 0 0 3px rgba(124, 58, 237, 0.14);
}

.modern-form :deep(.el-select__wrapper.is-disabled),
.modern-form :deep(.el-input.is-disabled .el-input__wrapper) {
  background-color: #f1f5f9;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
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
  top: 50%;
  right: 8px;
  z-index: 10;
  padding: 2px 7px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  pointer-events: none;
  transform: translateY(-50%);
  color: #5b21b6;
  background: #ede9fe;
  box-shadow: inset 0 0 0 1px #ddd6fe;
}

/* ダイアログ下部ボタン */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;

  .dlg-btn {
    --k-rgb: 100 116 139;
    min-width: 88px;
    margin: 0;
    border-radius: 8px;
    font-weight: 700;
    color: #475569;
    border: 1px solid #cbd5e1;
    background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%);

    &:hover,
    &:focus-visible {
      color: #334155;
      border-color: #94a3b8;
      background: #fff;
    }
  }

  .dlg-btn--save {
    --k-rgb: 124 58 237;
    color: #fff;
    border-color: #6d28d9;
    background:
      linear-gradient(180deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0) 52%),
      linear-gradient(135deg, #8b5cf6, #6d28d9);

    &:hover,
    &:focus-visible {
      color: #fff;
      border-color: #5b21b6;
      background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.26) 0%, rgba(255, 255, 255, 0) 52%),
        linear-gradient(135deg, #9b70f8, #7c3aed);
    }
  }
}

/* ---------- レスポンシブ ---------- */
@media (max-width: 1200px) {
  .filters-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .form-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .outsourcing-products-page {
    padding: 6px 8px;
  }

  .header-content {
    flex-direction: column;
    align-items: flex-start;
  }

  .header-stats {
    width: 100%;
    justify-content: flex-start;
  }

  .filters-grid {
    grid-template-columns: 1fr;
    gap: 6px;
  }

  .filter-actions {
    flex-wrap: wrap;
  }

  .table-section .table-card :deep(.el-table th),
  .table-section .table-card :deep(.el-table td) {
    padding: 4px 8px;
    font-size: 11px;
  }

  :global(.el-dialog.opp-dialog) {
    width: 96% !important;
    margin: 2vh auto;
  }

  .modern-content {
    padding: 8px 10px;
  }

  .form-row {
    flex-direction: column;
    gap: 6px;
    margin-bottom: 8px;
  }
}

.table-card :deep(.el-table__body-wrapper)::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.table-card :deep(.el-table__body-wrapper)::-webkit-scrollbar-track {
  border-radius: 3px;
  background: #f5f3ff;
}

.table-card :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb {
  border-radius: 3px;
  background: #c4b5fd;
}
</style>
