<template>
  <div class="product-master-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="main-title">
            <el-icon class="title-icon">
              <Box />
            </el-icon>
            {{ t('master.product.title') }}
          </h1>
          <p class="subtitle">{{ t('master.product.subtitle') }}</p>
        </div>
        <div class="header-stats">
          <div class="stat-card">
            <div class="stat-number">{{ allProducts?.length || 0 }}</div>
            <div class="stat-label">{{ t('master.product.totalProducts') }}</div>
          </div>
          <div class="stat-card" v-for="(count, type) in productTypeStats" :key="type">
            <div class="stat-number">{{ count }}</div>
            <div class="stat-label">{{ type }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 功能操作区域 -->
    <div class="action-section">
      <!-- 筛选标题 -->
      <div class="filter-header">
        <div class="filter-title">
          <el-icon class="filter-icon">
            <Filter />
          </el-icon>
          <span>{{ t('master.product.searchFilter') }}</span>
          <div class="filter-inline-summary" v-if="productList.length || hasActiveFilters">
            <div class="summary-text">
              <el-icon class="summary-icon">
                <InfoFilled />
              </el-icon>
              <span>{{ t('master.product.showingCount', { n: productList.length }) }}</span>
            </div>
            <div class="active-filters" v-if="hasActiveFilters">
              <el-tag
                v-if="filters.keyword"
                closable
                @close="handleClearFilter('keyword')"
                type="primary"
                size="small"
              >
                {{ t('master.product.searchLabel') }}: {{ filters.keyword }}
              </el-tag>
              <el-tag
                v-if="filters.category"
                closable
                @close="handleClearFilter('category')"
                type="warning"
                size="small"
              >
                {{ t('master.product.categoryLabel') }}: {{ filters.category }}
              </el-tag>
              <el-tag
                v-if="filters.location_cd"
                closable
                @close="handleClearFilter('location_cd')"
                type="info"
                size="small"
              >
                {{ t('master.product.locationLabel') }}: {{ filters.location_cd }}
              </el-tag>
            </div>
          </div>
        </div>
        <div class="filter-actions">
          <el-button text @click="handleReset" :icon="Refresh" class="clear-btn">
            {{ t('master.product.reset') }}
          </el-button>
          <el-button
            type="info"
            @click="handleColumnSelector"
            :icon="Setting"
            class="column-selector-btn"
          >
            {{ t('master.product.columnSettings') }}
          </el-button>
          <el-button type="success" @click="handleExport" :icon="Download" class="export-btn">
            {{ t('master.product.export') }}
          </el-button>
          <el-button
            type="success"
            @click="exportToCSV"
            :icon="Download"
            :disabled="productList.length === 0"
            class="export-csv-btn"
          >
            CSV出力
          </el-button>
          <el-button
            type="warning"
            @click="generateAndPrintQRCodes"
            :icon="Printer"
            class="qr-code-btn"
          >
            QRコード印刷
          </el-button>
          <el-button type="primary" @click="handleAdd" :icon="Plus" class="add-product-btn">
            製品追加
          </el-button>
        </div>
      </div>

      <!-- 筛选内容 -->
      <div class="filters-grid">
        <el-row :gutter="16">
          <el-col :lg="6" :md="12">
            <!-- 搜索关键词 -->
            <el-form-item label="🔍 キーワード">
              <el-input
                v-model="filters.keyword"
                placeholder="製品名 / 品番 / 別名"
                clearable
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <!-- 类别 -->
          <el-col :lg="6" :md="12">
            <el-form-item label="📁 カテゴリ">
              <el-select
                v-model="filters.category"
                clearable
                placeholder="選択"
                style="min-width: 100px; width: 100%"
              >
                <el-option label="一般" value="一般" />
                <el-option label="一般溶接" value="一般溶接" />
                <el-option label="メカ溶接" value="メカ溶接" />
                <el-option label="自動車" value="自動車" />
                <el-option label="その他" value="その他" />
              </el-select>
            </el-form-item>
          </el-col>
          <!-- 状态 -->
          <el-col :lg="6" :md="12">
            <el-form-item label="🔖 状態">
              <el-select
                v-model="filters.status"
                clearable
                placeholder="選択"
                style="min-width: 100px; width: 100%"
              >
                <el-option label="現行" value="active" />
                <el-option label="終息" value="inactive" />
              </el-select>
            </el-form-item>
          </el-col>
          <!-- 产品种别 -->
          <el-col :lg="6" :md="12">
            <el-form-item label="🏷️ 製品種別">
              <el-select
                v-model="filters.product_type"
                clearable
                placeholder="選択"
                style="min-width: 100px; width: 100%"
              >
                <el-option label="量産品" value="量産品" />
                <el-option label="試作品" value="試作品" />
                <el-option label="補給品" value="補給品" />
                <el-option label="その他" value="その他" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <!-- 产品CD -->
        <el-row :gutter="16">
          <el-col :lg="6" :md="12">
            <el-form-item label="🆔 製品CD">
              <el-select
                v-model="filters.product_cd"
                filterable
                clearable
                placeholder="選択"
                style="width: 100%"
              >
                <el-option
                  v-for="item in productCdOptions"
                  :key="item.cd"
                  :label="`${item.cd}｜${item.name}`"
                  :value="item.cd"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <!-- 材料CD -->
          <el-col :lg="6" :md="12">
            <el-form-item label="🧱 材料CD">
              <el-select
                v-model="filters.material_cd"
                filterable
                clearable
                placeholder="選択"
                style="width: 100%"
              >
                <el-option
                  v-for="item in materialOptions"
                  :key="item.cd"
                  :label="`${item.cd}｜${item.name}`"
                  :value="item.cd"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <!-- 工程ルートCD -->
          <el-col :lg="6" :md="12">
            <el-form-item label="🛠️ 工程ルートCD">
              <el-select
                v-model="filters.route_cd"
                filterable
                clearable
                placeholder="選択"
                style="width: 100%"
              >
                <el-option
                  v-for="item in routeOptions"
                  :key="item.cd"
                  :label="`${item.cd}｜${item.name}`"
                  :value="item.cd"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <!-- 保管場所CD -->
          <el-col :lg="6" :md="12">
            <el-form-item label="🏢 保管場所CD">
              <el-select
                v-model="filters.location_cd"
                filterable
                clearable
                placeholder="選択"
                style="width: 100%"
              >
                <el-option
                  v-for="item in locationOptions"
                  :key="item.cd"
                  :label="`${item.cd}｜${item.name}`"
                  :value="item.cd"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </div>

      <!-- 筛选结果摘要 -->
    </div>

    <!-- 数据表格 -->
    <el-table
      :data="productList"
      v-loading="loading"
      stripe
      border
      highlight-current-row
      :style="{ width: '100%' }"
      height="600"
      :header-cell-style="{ background: '#f5f7fa', fontWeight: 'bold' }"
      :cell-style="{ padding: '4px 8px' }"
      :default-sort="{ prop: 'product_name', order: 'ascending' }"
      :scrollbar-always-on="true"
    >
      <el-table-column fixed prop="product_cd" label="製品CD" min-width="85" />
      <el-table-column prop="product_name" label="製品名称" min-width="155" />
      <el-table-column
        prop="part_number"
        label="品番"
        min-width="120"
        align="center"
        v-show="visibleColumns.part_number"
      >
        <template #default="{ row }">
          {{ row.part_number || '—' }}
        </template>
      </el-table-column>
      <el-table-column label="納入先CD" min-width="120">
        <template #default="{ row }">
          {{ row.destination_cd || '—' }}
        </template>
      </el-table-column>
      <el-table-column
        prop="product_type"
        label="製品種別"
        width="100"
        v-show="visibleColumns.product_type"
      />
      <el-table-column
        prop="category"
        label="カテゴリ"
        min-width="101"
        align="center"
        v-show="visibleColumns.category"
      />
      <el-table-column
        prop="box_type"
        label="箱種"
        min-width="101"
        align="center"
        v-show="visibleColumns.box_type"
      />
      <el-table-column
        prop="unit_per_box"
        label="入数"
        width="70"
        align="center"
        v-show="visibleColumns.unit_per_box"
      />
      <el-table-column
        prop="process_count"
        label="工程数"
        width="68"
        align="center"
        v-show="visibleColumns.process_count"
      />
      <el-table-column
        prop="location_cd"
        label="保管場所"
        min-width="120"
        align="center"
        v-show="visibleColumns.location_cd"
      >
        <template #default="{ row }">
          {{ row.location_cd || '—' }}
        </template>
      </el-table-column>
      <el-table-column
        prop="start_use_date"
        label="使用開始日"
        width="120"
        align="center"
        v-show="visibleColumns.start_use_date"
      >
        <template #default="{ row }">
          {{ row.start_use_date ? formatJapanDate(row.start_use_date) : '—' }}
        </template>
      </el-table-column>
      <el-table-column
        prop="status"
        label="状態"
        width="90"
        align="center"
        v-show="visibleColumns.status"
      >
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
            {{ row.status === 'active' ? '現行' : '終息' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        prop="vehicle_model"
        label="対応車種"
        min-width="120"
        align="center"
        v-show="visibleColumns.vehicle_model"
      >
        <template #default="{ row }">
          {{ row.vehicle_model || '—' }}
        </template>
      </el-table-column>
      <el-table-column
        prop="dimensions"
        label="サイズ"
        min-width="120"
        align="center"
        v-show="visibleColumns.dimensions"
      >
        <template #default="{ row }">
          {{ row.dimensions || '—' }}
        </template>
      </el-table-column>
      <el-table-column
        prop="weight"
        label="重量(kg)"
        width="100"
        align="center"
        v-show="visibleColumns.weight"
      >
        <template #default="{ row }">
          {{ row.weight ? row.weight.toFixed(2) : '—' }}
        </template>
      </el-table-column>
      <el-table-column
        prop="lead_time"
        label="リードタイム"
        width="100"
        align="center"
        v-show="visibleColumns.lead_time"
      >
        <template #default="{ row }">
          {{ row.lead_time ? `${row.lead_time}日` : '—' }}
        </template>
      </el-table-column>
      <el-table-column
        prop="lot_size"
        label="ロットサイズ"
        width="100"
        align="center"
        v-show="visibleColumns.lot_size"
      >
        <template #default="{ row }">
          {{ row.lot_size || '—' }}
        </template>
      </el-table-column>
      <el-table-column
        prop="priority"
        label="優先度"
        width="80"
        align="center"
        v-show="visibleColumns.priority"
      >
        <template #default="{ row }">
          <el-tag
            :type="row.priority === 1 ? 'danger' : row.priority === 2 ? 'warning' : 'info'"
            size="small"
          >
            {{ row.priority === 1 ? '高' : row.priority === 2 ? '中' : '低' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        prop="cut_length"
        label="切断長さ(mm)"
        width="120"
        align="center"
        v-show="visibleColumns.cut_length"
      >
        <template #default="{ row }">
          {{ row.cut_length ? row.cut_length.toFixed(2) : '—' }}
        </template>
      </el-table-column>
      <el-table-column
        prop="chamfer_length"
        label="面取り長さ(mm)"
        width="130"
        align="center"
        v-show="visibleColumns.chamfer_length"
      >
        <template #default="{ row }">
          {{ row.chamfer_length ? row.chamfer_length.toFixed(2) : '—' }}
        </template>
      </el-table-column>
      <el-table-column
        prop="developed_length"
        label="展開長さ(mm)"
        width="130"
        align="center"
        v-show="visibleColumns.developed_length"
      >
        <template #default="{ row }">
          {{ row.developed_length ? row.developed_length.toFixed(2) : '—' }}
        </template>
      </el-table-column>
      <el-table-column
        prop="take_count"
        label="取り数"
        width="80"
        align="center"
        v-show="visibleColumns.take_count"
      >
        <template #default="{ row }">
          {{ row.take_count || '—' }}
        </template>
      </el-table-column>
      <el-table-column
        prop="scrap_length"
        label="端材長さ(mm)"
        width="130"
        align="center"
        v-show="visibleColumns.scrap_length"
      >
        <template #default="{ row }">
          {{ row.scrap_length ? row.scrap_length.toFixed(2) : '—' }}
        </template>
      </el-table-column>
      <el-table-column
        prop="safety_days"
        label="安全在庫日数"
        width="120"
        align="center"
        v-show="visibleColumns.safety_days"
      >
        <template #default="{ row }">
          {{ row.safety_days ? `${row.safety_days}日` : '—' }}
        </template>
      </el-table-column>
      <el-table-column
        prop="unit_price"
        label="販売単価"
        width="100"
        align="center"
        v-show="visibleColumns.unit_price"
      >
        <template #default="{ row }">
          {{ row.unit_price ? `¥${row.unit_price.toFixed(2)}` : '—' }}
        </template>
      </el-table-column>
      <el-table-column
        prop="product_alias"
        label="別名"
        min-width="120"
        align="center"
        v-show="visibleColumns.product_alias"
      >
        <template #default="{ row }">
          {{ row.product_alias || '—' }}
        </template>
      </el-table-column>
      <el-table-column
        prop="is_multistage"
        label="多段階工程"
        width="120"
        align="center"
        v-show="visibleColumns.is_multistage"
      >
        <template #default="{ row }">
          <el-tag :type="row.is_multistage ? 'success' : 'info'" size="small">
            {{ row.is_multistage ? '多段階' : '単段階' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        prop="note"
        label="備考"
        min-width="150"
        align="center"
        v-show="visibleColumns.note"
        show-overflow-tooltip
      >
        <template #default="{ row }">
          {{ row.note || '—' }}
        </template>
      </el-table-column>
      <el-table-column
        prop="created_at"
        label="作成日時"
        width="150"
        align="center"
        v-show="visibleColumns.created_at"
      >
        <template #default="{ row }">
          {{ row.created_at ? formatDateTime(row.created_at) : '—' }}
        </template>
      </el-table-column>
      <el-table-column
        prop="updated_at"
        label="更新日時"
        width="150"
        align="center"
        v-show="visibleColumns.updated_at"
      >
        <template #default="{ row }">
          {{ row.updated_at ? formatDateTime(row.updated_at) : '—' }}
        </template>
      </el-table-column>
      <el-table-column fixed="right" label="操作" width="180" align="center">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="handleEdit(row)">
            <el-icon>
              <Edit />
            </el-icon>
            編集
          </el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">
            <el-icon>
              <Delete />
            </el-icon>
            削除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <el-pagination
      v-model:current-page="pagination.page"
      :page-size="pagination.pageSize"
      :total="pagination.total"
      layout="prev, pager, next"
      class="pagination"
      @current-change="fetchList"
    />

    <!-- 编辑弹窗 -->
    <ProductEditDialog
      v-model:visible="dialogVisible"
      :editData="selectedRow"
      @saved="handleSaved"
    />

    <!-- 列选择对话框 -->
    <el-dialog
      v-model="columnSelectorVisible"
      title="列表示設定"
      width="480px"
      :close-on-click-modal="false"
      class="column-selector-dialog"
    >
      <div class="column-selector">
        <div class="column-selector-header">
          <div class="header-label">表示する列を素早く切り替え</div>
          <div class="header-actions">
            <el-button size="small" @click="selectAllColumns" plain>すべて選択</el-button>
            <el-button size="small" @click="deselectAllColumns" plain>すべて解除</el-button>
          </div>
        </div>
        <div class="column-list">
          <el-checkbox
            v-for="(column, key) in columnOptions"
            :key="key"
            v-model="visibleColumns[key]"
            :label="column.label"
            class="column-checkbox"
          />
        </div>
      </div>
      <template #footer>
        <el-button @click="columnSelectorVisible = false">キャンセル</el-button>
        <el-button type="primary" @click="saveColumnSettings">保存</el-button>
      </template>
    </el-dialog>

    <!-- 製品種別选择对话框 -->
    <el-dialog
      v-model="productTypeSelectorVisible"
      title="製品種別選択"
      width="500px"
      :close-on-click-modal="false"
    >
      <div class="product-type-selector">
        <div class="selector-label">印刷する製品種別を選択してください：</div>
        <el-checkbox-group v-model="selectedProductTypes" class="product-type-checkbox-group">
          <el-checkbox label="量産品" />
          <el-checkbox label="試作品" />
          <el-checkbox label="補給品" />
          <el-checkbox label="その他" />
        </el-checkbox-group>
      </div>
      <template #footer>
        <el-button @click="productTypeSelectorVisible = false">キャンセル</el-button>
        <el-button type="primary" @click="confirmProductTypeSelection">確定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
/**
 * 製品マスタ一覧
 * 功能：
 * - 筛选+分页+CRUD
 * - 支持导出Excel
 */
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Box,
  Filter,
  Refresh,
  Download,
  Plus,
  InfoFilled,
  Edit,
  Delete,
  Setting,
  Printer,
} from '@element-plus/icons-vue'
import { getProductList, deleteProduct, exportProductToCSV } from '@/api/master/productMaster'
import { getProductMasterOptions, getMaterialOptions, getRouteOptions } from '@/api/options'
import ProductEditDialog from './ProductEditDialog.vue'
import type { Product, OptionItem } from '@/types/master'
import * as XLSX from 'xlsx'

const { t } = useI18n()

// 筛选条件
const filters = reactive({
  keyword: '',
  category: '',
  product_cd: '',
  product_type: '',
  material_cd: '',
  route_cd: '',
  location_cd: '',
  status: '',
})

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 50,
  total: 0,
})

// 数据
const productList = ref<Product[]>([])
const allProducts = ref<Product[]>([]) // 新增：用于统计全部产品
const productCdOptions = ref<OptionItem[]>([])
const materialOptions = ref<OptionItem[]>([])
const routeOptions = ref<OptionItem[]>([])
const locationOptions = ref<OptionItem[]>([
  { cd: '製品倉庫', name: '製品倉庫' },
  { cd: '外注倉庫', name: '外注倉庫' },
  { cd: '仮設倉庫', name: '仮設倉庫' },
  { cd: '部品倉庫', name: '部品倉庫' },
  { cd: '材料置場', name: '材料置場' },
  { cd: '仕上倉庫', name: '仕上倉庫' },
  { cd: '工程中間在庫', name: '工程中間在庫' },
  { cd: 'メッキ倉庫', name: 'メッキ倉庫' },
])
const loading = ref(false)
const dialogVisible = ref(false)
const selectedRow = ref<Product | null>(null)
const columnSelectorVisible = ref(false)
const productTypeSelectorVisible = ref(false)
const selectedProductTypes = ref<string[]>([])

// 列显示控制
const visibleColumns = ref({
  part_number: true,
  product_type: true,
  category: true,
  box_type: true,
  unit_per_box: true,
  process_count: true,
  location_cd: true,
  start_use_date: true,
  status: true,
  vehicle_model: false,
  dimensions: false,
  weight: false,
  lead_time: false,
  lot_size: false,
  priority: false,
  cut_length: false,
  chamfer_length: false,
  developed_length: false,
  take_count: false,
  scrap_length: false,
  safety_days: false,
  unit_price: false,
  product_alias: false,
  is_multistage: false,
  note: false,
  created_at: false,
  updated_at: false,
})

// 列选项配置
const columnOptions = {
  part_number: { label: '品番' },
  product_type: { label: '製品種別' },
  category: { label: 'カテゴリ' },
  box_type: { label: '箱種' },
  unit_per_box: { label: '入数' },
  process_count: { label: '工程数' },
  location_cd: { label: '保管場所' },
  start_use_date: { label: '使用開始日' },
  status: { label: '状態' },
  vehicle_model: { label: '対応車種' },
  dimensions: { label: 'サイズ' },
  weight: { label: '重量(kg)' },
  lead_time: { label: 'リードタイム' },
  lot_size: { label: 'ロットサイズ' },
  priority: { label: '優先度' },
  cut_length: { label: '切断長さ(mm)' },
  chamfer_length: { label: '面取り長さ(mm)' },
  developed_length: { label: '展開長さ(mm)' },
  take_count: { label: '取り数' },
  scrap_length: { label: '端材長さ(mm)' },
  safety_days: { label: '安全在庫日数' },
  unit_price: { label: '販売単価' },
  product_alias: { label: '別名' },
  is_multistage: { label: '多段階工程' },
  note: { label: '備考' },
  created_at: { label: '作成日時' },
  updated_at: { label: '更新日時' },
}

// 各製品種別件数统计
const productTypeStats = computed(() => {
  const stats: Record<string, number> = {
    量産品: 0,
    試作品: 0,
    補給品: 0,
    その他: 0,
  }
  if (allProducts.value) {
    allProducts.value.forEach((p) => {
      const type = p.product_type as string
      if (type && Object.prototype.hasOwnProperty.call(stats, type)) {
        stats[type]++
      } else {
        stats['その他']++
      }
    })
  }
  return stats
})

const hasActiveFilters = computed(() => {
  return (
    filters.keyword ||
    filters.category ||
    filters.product_cd ||
    filters.product_type ||
    filters.material_cd ||
    filters.route_cd ||
    filters.location_cd ||
    filters.status
  )
})

// 获取列表
const fetchList = async () => {
  loading.value = true
  try {
    const params = {
      ...filters,
      page: pagination.page,
      pageSize: pagination.pageSize,
    }
    const response = await getProductList(params)

    // 处理API响应结构 {success: true, data: {list: [], total: number}}
    if (response.success && response.data) {
      productList.value = response.data.list || []
      pagination.total = response.data.total || 0
    } else {
      // 兼容直接返回数据的情况
      productList.value = response.list || []
      pagination.total = response.total || 0
    }
  } catch (e) {
    console.error('製品一覧取得失敗', e)

    // 根据错误类型显示不同的消息
    if (e instanceof Error) {
      if (e.message.includes('Network Error') || e.message.includes('timeout')) {
        ElMessage.warning('ネットワーク接続に問題があります。後でもう一度お試しください。')
      } else if (e.message.includes('401') || e.message.includes('Unauthorized')) {
        ElMessage.error('認証に失敗しました。再度ログインしてください。')
      } else {
        ElMessage.error('製品一覧取得失敗')
      }
    } else {
      ElMessage.error('製品一覧取得失敗')
    }

    productList.value = []
    pagination.total = 0
  } finally {
    loading.value = false
  }
}

const FILTER_DEBOUNCE_MS = 400
let filterChangeTimer: ReturnType<typeof setTimeout> | null = null

watch(
  filters,
  () => {
    if (filterChangeTimer) {
      clearTimeout(filterChangeTimer)
    }
    filterChangeTimer = setTimeout(() => {
      pagination.page = 1
      fetchList()
    }, FILTER_DEBOUNCE_MS)
  },
  { deep: true },
)

// 新增
const handleAdd = () => {
  selectedRow.value = null
  dialogVisible.value = true
}

// 编辑
const handleEdit = (row: Product) => {
  selectedRow.value = { ...row }
  dialogVisible.value = true
}

// 处理保存成功
const handleSaved = () => {
  // 重置到第一页并刷新列表
  pagination.page = 1
  fetchList()
}

// 重置
const handleReset = () => {
  Object.assign(filters, {
    keyword: '',
    category: '',
    product_cd: '',
    product_type: '',
    material_cd: '',
    route_cd: '',
    location_cd: '',
    status: '',
  })
  pagination.page = 1
}

// 清除单个筛选条件
const handleClearFilter = (filterKey: keyof typeof filters) => {
  filters[filterKey] = ''
}

// 格式化日本时区日期
const formatJapanDate = (dateValue: string | Date) => {
  try {
    let date: Date
    if (dateValue instanceof Date) {
      date = dateValue
    } else {
      date = new Date(dateValue)
    }
    // 使用日本时区
    const japanDate = new Date(date.getTime() + 9 * 60 * 60 * 1000)
    return japanDate.toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    })
  } catch (error) {
    console.error('日期格式化错误:', error)
    return dateValue instanceof Date ? dateValue.toISOString().split('T')[0] : dateValue
  }
}

// 格式化日期时间
const formatDateTime = (dateString: string) => {
  try {
    const date = new Date(dateString)
    return date.toLocaleString('ja-JP', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch (error) {
    console.error('日期时间格式化错误:', error)
    return dateString
  }
}

// 削除
const handleDelete = async (row: Product) => {
  const confirmed = await ElMessageBox.confirm(
    `本当に製品「${row.product_name}」を削除しますか？`,
    '削除確認',
    {
      confirmButtonText: '削除',
      cancelButtonText: 'キャンセル',
      type: 'warning',
    },
  ).catch(() => false)

  if (!confirmed) return

  try {
    await deleteProduct(row.id!)
    ElMessage.success('削除しました')
    fetchList()
  } catch (e) {
    console.error('削除失敗', e)
    ElMessage.error('削除に失敗しました')
  }
}

// 列选择器相关函数
const handleColumnSelector = () => {
  columnSelectorVisible.value = true
}

const selectAllColumns = () => {
  Object.keys(visibleColumns.value).forEach((key) => {
    ;(visibleColumns.value as any)[key] = true
  })
}

const deselectAllColumns = () => {
  Object.keys(visibleColumns.value).forEach((key) => {
    ;(visibleColumns.value as any)[key] = false
  })
}

const saveColumnSettings = () => {
  // 保存到localStorage
  localStorage.setItem('productList_visibleColumns', JSON.stringify(visibleColumns.value))
  columnSelectorVisible.value = false
  ElMessage.success('列表示設定を保存しました')
}

// 打开製品種別选择弹窗
const generateAndPrintQRCodes = () => {
  // 获取所有产品的製品CD（优先使用 allProducts，如果没有则使用 productList）
  const productsToUse = allProducts.value.length > 0 ? allProducts.value : productList.value

  if (productsToUse.length === 0) {
    ElMessage.warning('印刷する製品がありません')
    return
  }

  // 重置选择
  selectedProductTypes.value = []
  // 显示选择弹窗
  productTypeSelectorVisible.value = true
}

// 确认製品種別选择并生成打印页面
const confirmProductTypeSelection = async () => {
  if (selectedProductTypes.value.length === 0) {
    ElMessage.warning('製品種別を選択してください')
    return
  }

  productTypeSelectorVisible.value = false
  await doGenerateAndPrintQRCodes()
}

// 实际生成并打印所有製品CD的二维码
const doGenerateAndPrintQRCodes = async () => {
  // 获取所有产品的製品CD（优先使用 allProducts，如果没有则使用 productList）
  let productsToUse = allProducts.value.length > 0 ? allProducts.value : productList.value

  // 根据选择的製品種別过滤
  if (selectedProductTypes.value.length > 0) {
    productsToUse = productsToUse.filter((product) =>
      selectedProductTypes.value.includes(product.product_type || ''),
    )
  }

  if (productsToUse.length === 0) {
    ElMessage.warning('選択した製品種別に該当する製品がありません')
    return
  }

  try {
    let QRCode: typeof import('qrcode')
    try {
      QRCode = await import('qrcode')
    } catch {
      ElMessage.error(
        'QRコードライブラリが見つかりません。以下のコマンドでインストールしてください: npm install qrcode',
      )
      return
    }

    // 创建打印窗口内容
    const printWindow = window.open('', '_blank')
    if (!printWindow) {
      ElMessage.error('ポップアップがブロックされました。ブラウザの設定を確認してください')
      return
    }

    // 按製品名排序
    const sortedProducts = [...productsToUse].sort((a, b) => {
      const nameA = a.product_name || ''
      const nameB = b.product_name || ''
      return nameA.localeCompare(nameB, 'ja')
    })

    // 生成所有二维码（只包含製品CD最后一位为1的产品）
    const qrCodes: Array<{ dataUrl: string; product_cd: string; product_name: string }> = []
    for (const product of sortedProducts) {
      if (product.product_cd) {
        // 过滤条件：製品CD最后一位必须是1
        const lastChar = product.product_cd.slice(-1)
        if (lastChar !== '1') {
          continue // 跳过製品CD最后一位不是1的产品
        }

        try {
          const qrDataUrl = await QRCode.toDataURL(product.product_cd, {
            width: 95,
            margin: 2,
            color: {
              dark: '#000000',
              light: '#FFFFFF',
            },
          })
          qrCodes.push({
            dataUrl: qrDataUrl,
            product_cd: product.product_cd,
            product_name: product.product_name || '',
          })
        } catch (error) {
          console.error(`QRコード生成エラー (${product.product_cd}):`, error)
        }
      }
    }

    if (qrCodes.length === 0) {
      printWindow.close()
      ElMessage.error('QRコードの生成に失敗しました')
      return
    }

    // 创建打印HTML（A3纸横向布局，每行10个二维码，每页90个）
    const qrCodesPerRow = 10
    const qrCodesPerPage = 90 // A3横向可以放90个二维码（每行10个，共9行）
    // 计算实际需要的页数，确保不会生成空白页
    const totalPages = qrCodes.length > 0 ? Math.ceil(qrCodes.length / qrCodesPerPage) : 0

    let html = `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <title>製品QRコード印刷</title>
        <style>
          @page {
            size: A3 landscape;
            margin: 0;
          }
          body {
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
          }
          .page {
            width: 420mm;
            height: 297mm;
            padding: 12mm;
            margin: 0;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
          }
          .page:not(:last-child) {
            page-break-after: always;
          }
          .page:last-child {
            page-break-after: avoid;
          }
          .qr-grid {
            display: grid;
            grid-template-columns: repeat(${qrCodesPerRow}, 1fr);
            grid-template-rows: repeat(9, 1fr);
            gap: 1.5mm;
            width: 100%;
            height: 100%;
            align-content: start;
          }
          .qr-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 1mm;
            border: 1px solid #ddd;
            border-radius: 2px;
            page-break-inside: avoid;
            box-sizing: border-box;
          }
          .qr-code {
            width: 70px;
            height: 70px;
            margin-bottom: 2px;
            flex-shrink: 0;
          }
          .qr-product-name {
            font-size: 12px;
            font-weight: bold;
            text-align: center;
            color: #000;
            word-break: break-all;
            line-height: 1.3;
            margin-top: 2px;
            padding: 0 2px;
          }
          @media print {
            body {
              margin: 0;
              padding: 0;
            }
            .page {
              margin: 0;
              padding: 12mm;
            }
          }
        </style>
      </head>
      <body>
    `

    // 生成每一页（纵向填充）
    const qrCodesPerColumn = 9 // 每列9个（纵向）
    for (let page = 0; page < totalPages; page++) {
      const startIndex = page * qrCodesPerPage
      const endIndex = Math.min(startIndex + qrCodesPerPage, qrCodes.length)

      // 如果这一页没有内容，跳过
      if (startIndex >= qrCodes.length || endIndex <= startIndex) {
        break
      }

      // 获取这一页的二维码数据（已经按製品名排序）
      const pageQRCodes = qrCodes.slice(startIndex, endIndex)

      // 如果这一页没有数据，跳过（防止空白页）
      if (pageQRCodes.length === 0) {
        break
      }

      html += `<div class="page">`
      html += `<div class="qr-grid">`

      // 纵向填充：第1列从上到下，然后第2列从上到下，以此类推
      // 对于索引 i（在 pageQRCodes 中的位置）：
      // 列 = Math.floor(i / 9)
      // 行 = i % 9
      for (let i = 0; i < pageQRCodes.length; i++) {
        const { dataUrl, product_name } = pageQRCodes[i]
        // 计算在网格中的位置（纵向填充）
        const col = Math.floor(i / qrCodesPerColumn) // 列索引（0-9）
        const row = i % qrCodesPerColumn // 行索引（0-8）
        const gridColumn = col + 1 // CSS Grid 列从1开始
        const gridRow = row + 1 // CSS Grid 行从1开始

        html += `
          <div class="qr-item" style="grid-column: ${gridColumn}; grid-row: ${gridRow};">
            <img src="${dataUrl}" alt="QRコード" class="qr-code" />
            ${product_name ? `<div class="qr-product-name">${product_name}</div>` : ''}
          </div>
        `
      }

      html += `</div></div>`
    }

    html += `
      </body>
      </html>
    `

    // 写入打印窗口
    printWindow.document.write(html)
    printWindow.document.close()

    // 等待内容加载完成后打印
    printWindow.onload = () => {
      setTimeout(() => {
        let isClosed = false
        let fallbackTimeout: ReturnType<typeof setTimeout> | null = null

        // 关闭窗口的函数
        const closeWindow = () => {
          if (!isClosed) {
            isClosed = true
            // 清除备用定时器
            if (fallbackTimeout) {
              clearTimeout(fallbackTimeout)
              fallbackTimeout = null
            }
            // 延迟关闭，确保打印对话框已经完全关闭
            setTimeout(() => {
              try {
                printWindow.close()
              } catch (error) {
                console.error('窗口关闭エラー:', error)
              }
            }, 100)
          }
        }

        // 监听 afterprint 事件（打印对话框关闭后触发，无论是打印还是取消）
        printWindow.addEventListener('afterprint', closeWindow)

        // 监听窗口焦点变化（当打印对话框关闭，窗口重新获得焦点时）
        let focusTimeout: ReturnType<typeof setTimeout> | null = null
        printWindow.addEventListener('focus', () => {
          // 延迟关闭，确保打印对话框已经完全关闭
          if (focusTimeout) {
            clearTimeout(focusTimeout)
          }
          focusTimeout = setTimeout(() => {
            closeWindow()
          }, 300)
        })

        // 备用方案：如果 afterprint 事件不触发，使用定时器（5秒后自动关闭）
        fallbackTimeout = setTimeout(() => {
          if (!isClosed) {
            closeWindow()
          }
        }, 5000)

        // 开始打印
        printWindow.print()
      }, 250)
    }

    ElMessage.success(`${qrCodes.length}件のQRコードを生成しました`)
  } catch (error) {
    console.error('QRコード生成エラー:', error)
    ElMessage.error('QRコードの生成に失敗しました')
  }
}

// 导出Excel
const handleExport = () => {
  const exportData = productList.value.map((item) => {
    const data: any = {
      製品CD: item.product_cd,
      製品名称: item.product_name,
    }

    // 根据可见列动态添加字段
    if (visibleColumns.value.part_number) {
      data.品番 = item.part_number || ''
    }
    if (visibleColumns.value.product_type) {
      data.製品種別 = item.product_type
    }
    if (visibleColumns.value.category) {
      data.カテゴリ = item.category
    }
    if (visibleColumns.value.box_type) {
      data.箱種 = item.box_type
    }
    if (visibleColumns.value.unit_per_box) {
      data.入数 = item.unit_per_box
    }
    if (visibleColumns.value.process_count) {
      data.工程数 = item.process_count
    }
    if (visibleColumns.value.location_cd) {
      data.保管場所 = item.location_cd || ''
    }
    if (visibleColumns.value.start_use_date) {
      data.使用開始日 = item.start_use_date ? formatJapanDate(item.start_use_date) : ''
    }
    if (visibleColumns.value.status) {
      data.状態 = item.status
    }
    if (visibleColumns.value.vehicle_model) {
      data.対応車種 = item.vehicle_model || ''
    }
    if (visibleColumns.value.dimensions) {
      data.サイズ = item.dimensions || ''
    }
    if (visibleColumns.value.weight) {
      data.重量 = item.weight ? item.weight.toFixed(2) : ''
    }
    if (visibleColumns.value.lead_time) {
      data.リードタイム = item.lead_time ? `${item.lead_time}日` : ''
    }
    if (visibleColumns.value.lot_size) {
      data.ロットサイズ = item.lot_size || ''
    }
    if (visibleColumns.value.priority) {
      data.優先度 = item.priority === 1 ? '高' : item.priority === 2 ? '中' : '低'
    }
    if (visibleColumns.value.cut_length) {
      data.切断長さ = item.cut_length ? item.cut_length.toFixed(2) : ''
    }
    if (visibleColumns.value.chamfer_length) {
      data.面取り長さ = item.chamfer_length ? item.chamfer_length.toFixed(2) : ''
    }
    if (visibleColumns.value.developed_length) {
      data.展開長さ = item.developed_length ? item.developed_length.toFixed(2) : ''
    }
    if (visibleColumns.value.take_count) {
      data.取り数 = item.take_count || ''
    }
    if (visibleColumns.value.scrap_length) {
      data.端材長さ = item.scrap_length ? item.scrap_length.toFixed(2) : ''
    }
    if (visibleColumns.value.safety_days) {
      data.安全在庫日数 = item.safety_days ? `${item.safety_days}日` : ''
    }
    if (visibleColumns.value.unit_price) {
      data.販売単価 = item.unit_price ? item.unit_price.toFixed(2) : ''
    }
    if (visibleColumns.value.product_alias) {
      data.別名 = (item as any).product_alias || ''
    }
    if (visibleColumns.value.is_multistage) {
      data.多段階工程 = item.is_multistage ? '多段階' : '単段階'
    }
    if (visibleColumns.value.note) {
      data.備考 = item.note || ''
    }
    if (visibleColumns.value.created_at) {
      data.作成日時 = item.created_at ? formatDateTime(item.created_at) : ''
    }
    if (visibleColumns.value.updated_at) {
      data.更新日時 = item.updated_at ? formatDateTime(item.updated_at) : ''
    }

    return data
  })

  const worksheet = XLSX.utils.json_to_sheet(exportData)
  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(workbook, worksheet, '製品マスタ')
  XLSX.writeFile(workbook, '製品マスタ一覧.xlsx')
}

// 导出CSV文件
const exportToCSV = async () => {
  try {
    loading.value = true

    // 获取所有分页数据（不分页）
    const allDataResponse = await getProductList({
      ...filters,
      page: 1,
      pageSize: 10000,
    })

    let allProductsData: Product[] = []
    if (allDataResponse.success && allDataResponse.data) {
      allProductsData = allDataResponse.data.list || []
    } else {
      allProductsData = allDataResponse.list || []
    }

    if (allProductsData.length === 0) {
      ElMessage.warning('出力する製品がありません')
      return
    }

    // 准备导出数据：只包含製品CD、製品名、入数
    const exportData = allProductsData.map((product) => ({
      product_cd: product.product_cd || '',
      product_name: product.product_name || '',
      unit_per_box: product.unit_per_box != null ? Number(product.unit_per_box) : undefined,
    }))

    // 调用后端API导出CSV
    await exportProductToCSV(exportData)

    ElMessage.success(`${exportData.length}件のデータをCSVファイルに出力しました`)
  } catch (error) {
    console.error('CSV出力エラー:', error)
    ElMessage.error('CSVファイルの出力に失敗しました')
  } finally {
    loading.value = false
  }
}

// 初始化
onMounted(async () => {
  try {
    // 从localStorage加载列显示设置
    const savedColumns = localStorage.getItem('productList_visibleColumns')
    if (savedColumns) {
      try {
        const parsedColumns = JSON.parse(savedColumns)
        Object.assign(visibleColumns.value, parsedColumns)
      } catch (error) {
        console.warn('列表示設定の読み込みに失敗しました:', error)
      }
    }

    // 先设置预设的location选项，确保基本功能可用
    const presetLocationOptions = [
      { cd: '製品倉庫', name: '製品倉庫' },
      { cd: '外注倉庫', name: '外注倉庫' },
      { cd: '仮設倉庫', name: '仮設倉庫' },
      { cd: '部品倉庫', name: '部品倉庫' },
      { cd: '材料置場', name: '材料置場' },
      { cd: '仕上倉庫', name: '仕上倉庫' },
      { cd: '工程中間在庫', name: '工程中間在庫' },
      { cd: 'メッキ倉庫', name: 'メッキ倉庫' },
    ]
    locationOptions.value = presetLocationOptions

    // 尝试获取产品列表
    try {
      await fetchList()
    } catch (error) {
      console.warn('製品一覧取得失敗:', error)
      // 不显示错误消息，继续执行其他初始化
    }

    // 尝试获取全部产品数据用于统计
    try {
      const allDataResponse = await getProductList({ page: 1, pageSize: 10000 })
      if (allDataResponse.success && allDataResponse.data) {
        allProducts.value = allDataResponse.data.list || []
      } else {
        allProducts.value = allDataResponse.list || []
      }
    } catch (error) {
      console.warn('全製品データ取得失敗:', error)
      allProducts.value = []
    }

    try {
      const productOptions = await getProductMasterOptions()
      productCdOptions.value = productOptions || []
    } catch (error) {
      console.warn('製品オプション取得失敗:', error)
      productCdOptions.value = []
    }

    try {
      const materialOpts = await getMaterialOptions()
      materialOptions.value = materialOpts || []
    } catch (error) {
      console.warn('材料オプション取得失敗:', error)
      materialOptions.value = []
    }

    try {
      const routeOpts = await getRouteOptions()
      routeOptions.value = routeOpts || []
    } catch (error) {
      console.warn('工程ルートオプション取得失敗:', error)
      routeOptions.value = []
    }

    // 直接使用预设的location选项，不需要从API获取
    locationOptions.value = presetLocationOptions

    console.log('初期化完了')
  } catch (error) {
    console.error('初期化エラー', error)
    // 只在真正严重的错误时才显示错误消息
    if (error instanceof Error && error.message && !error.message.includes('Network Error')) {
      ElMessage.error('データ読み込み中にエラーが発生しました')
    }
  }
})
</script>

<style scoped>
.product-master-container {
  padding: 6px;
  background: linear-gradient(135deg, #f0f4f8 0%, #e2e8f0 100%);
  min-height: 100vh;
}

/* 页面头部 */
.page-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 10px 16px;
  margin-bottom: 6px;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.25);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.title-section {
  flex: 1;
}

.main-title {
  font-size: 1.35rem;
  font-weight: 700;
  margin: 0 0 2px;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  font-size: 1.3rem;
  color: rgba(255, 255, 255, 0.9);
}

.subtitle {
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
  font-size: 0.8rem;
}

.header-stats {
  display: flex;
  gap: 8px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(10px);
  color: white;
  padding: 6px 12px;
  border-radius: 10px;
  text-align: center;
  min-width: 70px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  transition: all 0.2s ease;
}

.stat-card:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateY(-1px);
}

.stat-number {
  font-size: 1.4rem;
  font-weight: 700;
  line-height: 1;
}

.stat-label {
  font-size: 0.7rem;
  opacity: 0.9;
  margin-top: 2px;
  white-space: nowrap;
}

/* 操作区域 */
.action-section {
  background: white;
  border-radius: 10px;
  padding: 0;
  margin-bottom: 6px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.filter-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 1px solid #e2e8f0;
}

.filter-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.95rem;
  font-weight: 600;
  color: #334155;
  flex-wrap: wrap;
}

.filter-icon {
  font-size: 1rem;
  color: #667eea;
}

.filter-actions {
  display: flex;
  gap: 6px;
  align-items: center;
  flex-wrap: wrap;
}

.clear-btn {
  color: #64748b;
  transition: all 0.2s ease;
  padding: 6px 10px !important;
  font-size: 12px !important;
}

.clear-btn:hover {
  color: #667eea;
}

.export-btn,
.export-csv-btn,
.column-selector-btn,
.add-product-btn,
.qr-code-btn {
  border: none;
  border-radius: 8px;
  padding: 7px 12px !important;
  font-weight: 600;
  font-size: 12px !important;
  transition: all 0.2s ease;
}

.export-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.25);
}

.export-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.35);
}

.export-csv-btn {
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
  box-shadow: 0 2px 8px rgba(6, 182, 212, 0.25);
  color: white;
}

.export-csv-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(6, 182, 212, 0.35);
}

.export-csv-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.column-selector-btn {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.25);
}

.column-selector-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.35);
}

.add-product-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.25);
}

.add-product-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.35);
}

.qr-code-btn {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.25);
}

.qr-code-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.35);
}

.filters-grid {
  padding: 10px 14px;
  background: white;
}

.filters-grid :deep(.el-form-item) {
  margin-bottom: 8px;
}

.filters-grid :deep(.el-form-item__label) {
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  padding-bottom: 2px;
}

.filters-grid :deep(.el-input__wrapper),
.filters-grid :deep(.el-select .el-input__wrapper) {
  border-radius: 6px;
  box-shadow: 0 0 0 1px #e2e8f0;
}

.filters-grid :deep(.el-input__wrapper:hover),
.filters-grid :deep(.el-select .el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #667eea;
}

.summary-text {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-bottom: 0;
  font-size: 0.8rem;
  color: #64748b;
  font-weight: 500;
}

.summary-icon {
  color: #667eea;
  font-size: 14px;
}

.active-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.active-filters :deep(.el-tag) {
  border-radius: 4px;
  font-size: 11px;
  padding: 0 6px;
  height: 22px;
}

/* 表格样式优化 */
:deep(.el-table) {
  border-radius: 8px;
  overflow: hidden;
  font-size: 12px;
}

:deep(.el-table .el-table__header th) {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%) !important;
  font-weight: 600;
  color: #334155;
  font-size: 12px;
  padding: 6px 8px !important;
}

:deep(.el-table .el-table__cell) {
  padding: 4px 6px !important;
}

:deep(.el-table .cell) {
  line-height: 1.5;
}

:deep(.el-table .el-button--small) {
  padding: 4px 8px;
  font-size: 11px;
  border-radius: 5px;
}

.filter-inline-summary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-left: 12px;
  border-left: 1px solid #e2e8f0;
  flex-wrap: wrap;
}

.filter-inline-summary .summary-text {
  margin-bottom: 0;
}

.pagination {
  margin-top: 8px;
  text-align: center;
}

.pagination :deep(.el-pager li) {
  border-radius: 6px;
  font-size: 12px;
  min-width: 28px;
  height: 28px;
  line-height: 28px;
}

.pagination :deep(.el-pager li.is-active) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .header-stats {
    align-self: stretch;
    justify-content: flex-start;
    flex-wrap: wrap;
  }
}

@media (max-width: 768px) {
  .product-master-container {
    padding: 4px;
  }

  .page-header {
    padding: 8px 12px;
    border-radius: 10px;
  }

  .main-title {
    font-size: 1.15rem;
  }

  .filter-header {
    flex-direction: column;
    gap: 10px;
    align-items: stretch;
    padding: 10px 12px;
  }

  .filter-actions {
    justify-content: flex-start;
  }

  .stat-card {
    min-width: 60px;
    padding: 5px 8px;
  }
  
  .stat-number {
    font-size: 1.1rem;
  }
}

/* 动画效果 */
.page-header,
.action-section {
  animation: fadeIn 0.4s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 列选择器样式 */
.column-selector-dialog :deep(.el-dialog__body) {
  padding: 10px 16px 14px;
}

.column-selector {
  padding: 4px 0;
}

.column-selector-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e2e8f0;
}

.column-selector-header .header-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #334155;
}

.column-selector-header .header-actions {
  display: flex;
  gap: 6px;
}

.column-selector-header .el-button {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 11px;
}

.column-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 6px;
  max-height: 240px;
  overflow-y: auto;
  padding-right: 4px;
}

.column-checkbox {
  display: flex;
  align-items: center;
  padding: 5px 8px;
  border-radius: 5px;
  border: 1px solid #e2e8f0;
  background-color: #fafbfc;
  transition: all 0.15s ease;
}

.column-checkbox:hover {
  background-color: #f1f5f9;
  border-color: #667eea;
}

.column-checkbox :deep(.el-checkbox__label) {
  font-size: 12px;
  color: #334155;
}

/* 製品種別选择器样式 */
.product-type-selector {
  padding: 6px 0;
}

.selector-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #334155;
  margin-bottom: 12px;
}

.product-type-checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.product-type-checkbox-group :deep(.el-checkbox) {
  font-size: 13px;
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
  background-color: #fafbfc;
  transition: all 0.15s ease;
}

.product-type-checkbox-group :deep(.el-checkbox:hover) {
  background-color: #f1f5f9;
  border-color: #667eea;
}

.product-type-checkbox-group :deep(.el-checkbox.is-checked) {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.08) 100%);
  border-color: #667eea;
}
</style>
