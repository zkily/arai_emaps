<template>
  <div class="inventory-container">
    <div class="page-ambient" aria-hidden="true" />

    <!-- ヘッダー -->
    <header class="page-hero">
      <div class="hero-inner">
        <div class="hero-brand">
          <div class="hero-icon">
            <el-icon :size="22"><Box /></el-icon>
          </div>
          <div class="hero-text">
            <h1 class="hero-title">棚卸リスト一覧</h1>
            <p class="hero-sub">材料・部品・ステー（工程別）・製品の棚卸データを一元管理</p>
          </div>
        </div>
        <div class="hero-actions">
          <el-button class="hero-btn hero-btn--ghost" :icon="Refresh" @click="handleSearch">
            再読込
          </el-button>
          <el-button
            class="hero-btn hero-btn--solid"
            :loading="loading"
            :icon="DocumentAdd"
            @click="handleImport"
          >
            棚卸データ取込
          </el-button>
        </div>
      </div>
    </header>

    <div class="content-container">
      <!-- KPI カード -->
      <section class="kpi-grid">
        <button
          v-for="card in kpiCards"
          :key="card.key"
          type="button"
          class="kpi-card"
          :class="{ 'is-active': activeTab === card.key, 'is-filtered': card.filtered }"
          :style="{ '--accent': card.color }"
          @click="activeTab = card.key"
        >
          <div class="kpi-icon">
            <el-icon :size="16"><component :is="card.icon" /></el-icon>
          </div>
          <span class="kpi-label">
            {{ card.label }}
            <span v-if="card.filtered" class="kpi-flag">絞込</span>
          </span>
          <span class="kpi-metric">
            <span class="kpi-metric-key">件数</span>
            <span class="kpi-value">{{ card.total.toLocaleString() }}</span>
            <span v-if="card.filtered" class="kpi-base">/ {{ card.baseTotal.toLocaleString() }}</span>
          </span>
          <span class="kpi-sep" />
          <span class="kpi-metric">
            <span class="kpi-metric-key">数量</span>
            <span class="kpi-value kpi-value--qty">{{ card.qty.toLocaleString() }}</span>
            <span v-if="card.filtered" class="kpi-base">/ {{ card.baseQty.toLocaleString() }}</span>
          </span>
        </button>
      </section>

      <!-- 検索条件 -->
      <section class="panel filter-panel">
        <div class="filter-line">
          <div class="panel-title">
            <el-icon class="panel-title-icon"><Filter /></el-icon>
            <span>検索条件</span>
            <span v-if="activeChips.length" class="panel-badge">{{ activeChips.length }}</span>
          </div>

          <div class="filter-field filter-field--process">
            <label class="field-label">
              <span class="field-dot field-dot--process" />工程
            </label>
            <el-select
              v-model="filters.processCd"
              placeholder="すべての工程"
              filterable
              clearable
              size="small"
              class="field-control"
              popper-class="inventory-option-popper"
              :loading="optionsLoading"
              @change="handleProcessChange"
            >
              <template #prefix>
                <span
                  v-if="filters.processCd"
                  class="opt-dot"
                  :style="{ background: getProcessColor(filters.processCd).color }"
                />
              </template>
              <el-option
                v-for="p in processOptions"
                :key="p.process_cd"
                :label="p.process_name || p.process_cd"
                :value="p.process_cd"
              >
                <div class="opt-row">
                  <span class="opt-dot" :style="{ background: getProcessColor(p.process_cd).color }" />
                  <span class="opt-name">{{ p.process_name || p.process_cd }}</span>
                  <span class="opt-meta">{{ p.process_cd }} · {{ p.cnt.toLocaleString() }}件</span>
                </div>
              </el-option>
            </el-select>
          </div>

          <div class="filter-field filter-field--product">
            <label class="field-label">
              <span class="field-dot field-dot--product" />製品名
            </label>
            <el-select-v2
              v-model="filters.productName"
              :options="productOptions"
              :props="productSelectProps"
              placeholder="すべての製品"
              filterable
              clearable
              size="small"
              class="field-control"
              popper-class="inventory-option-popper"
              :loading="productOptionsLoading"
              @change="handleProductChange"
            >
              <template #default="{ item }">
                <div class="opt-row">
                  <span class="opt-name">{{ item.product_name }}</span>
                  <span class="opt-meta">{{ item.product_cd }} · {{ item.cnt }}件</span>
                </div>
              </template>
            </el-select-v2>
          </div>

          <div class="filter-field filter-field--keyword">
            <label class="field-label"><span class="field-dot field-dot--keyword" />キーワード</label>
            <el-input
              v-model="filters.keyword"
              placeholder="製品CD・製品名"
              clearable
              size="small"
              class="field-control"
              :prefix-icon="Search"
              @input="handleKeywordInput"
              @keyup.enter="searchNow"
            />
          </div>

          <div class="filter-field filter-field--date">
            <label class="field-label"><span class="field-dot field-dot--date" />日付範囲</label>
            <el-date-picker
              v-model="filters.dateRange"
              type="daterange"
              range-separator="～"
              start-placeholder="開始日"
              end-placeholder="終了日"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              size="small"
              class="field-control"
              @change="handleDateRangeChange"
            />
          </div>

          <div class="filter-field filter-field--month">
            <label class="field-label"><span class="field-dot field-dot--month" />月選択</label>
            <el-date-picker
              v-model="filters.monthPicker"
              type="month"
              placeholder="月を選択"
              format="YYYY-MM"
              value-format="YYYY-MM"
              size="small"
              class="field-control"
              @change="handleMonthChange"
            />
          </div>

          <div class="filter-actions">
            <el-button size="small" :icon="RefreshLeft" @click="resetFilters">リセット</el-button>
          </div>
        </div>

        <transition name="fade">
          <div v-if="activeChips.length" class="chip-row">
            <span class="chip-row-label">適用中：</span>
            <span
              v-for="chip in activeChips"
              :key="chip.key"
              class="filter-chip"
              :style="{ '--chip': chip.color }"
            >
              <span class="filter-chip-key">{{ chip.label }}</span>
              <span class="filter-chip-val">{{ chip.value }}</span>
              <el-icon class="filter-chip-close" @click="removeChip(chip.key)"><Close /></el-icon>
            </span>
          </div>
        </transition>
      </section>

      <!-- タブ -->
      <section class="panel tab-panel">
        <el-tabs v-model="activeTab" class="custom-tabs">
          <el-tab-pane v-for="card in kpiCards" :key="card.key" :name="card.key">
            <template #label>
              <span class="tab-label" :style="{ '--accent': card.color }">
                <span class="tab-dot" />
                {{ card.label }}
                <span class="tab-count">{{ card.total.toLocaleString() }}</span>
              </span>
            </template>
          </el-tab-pane>
        </el-tabs>

        <div class="tab-content" :style="{ '--accent': currentCard.color }">
          <div class="tab-header">
            <div class="tab-header-top">
              <h3 class="tab-heading">
                <span class="tab-heading-bar" />
                {{ currentCard.label }}
              </h3>
              <div class="tab-stats">
                <span class="stat-pill">{{ currentCard.total.toLocaleString() }} 件</span>
                <span class="stat-pill stat-pill--qty">
                  計 {{ currentCard.qty.toLocaleString() }}
                </span>
              </div>
            </div>

            <div v-if="activeTab === 'stage'" class="stage-subtabs">
              <button
                v-for="s in STAGE_TABS"
                :key="s.value"
                type="button"
                class="stage-chip"
                :class="{ 'is-active': activeStageTab === s.value }"
                :style="{ '--chip': s.cd ? getProcessColor(s.cd).color : '#4f46e5' }"
                @click="handleStageTabChange(s.value)"
              >
                <span class="stage-chip-dot" />
                {{ s.label }}
              </button>
            </div>
          </div>

          <inventory-table
            v-if="activeTab === 'all'"
            :data="inventoryList"
            :loading="loading"
            :pagination="pagination"
            :sort-by="sortBy"
            :sort-order="sortOrder"
            :deleting-id="deletingId"
            @page-change="handlePageChange"
            @size-change="handleSizeChange"
            @sort="handleSort"
            @delete="handleDeleteRecord"
          />
          <inventory-table
            v-else-if="activeTab === 'material'"
            :data="materialList"
            :loading="materialLoading"
            :pagination="materialPagination"
            :sort-by="sortBy"
            :sort-order="sortOrder"
            :deleting-id="deletingId"
            @page-change="handleMaterialPageChange"
            @size-change="handleMaterialSizeChange"
            @sort="handleSort"
            @delete="handleDeleteRecord"
          />
          <inventory-table
            v-else-if="activeTab === 'component'"
            :data="componentList"
            :loading="componentLoading"
            :pagination="componentPagination"
            :sort-by="sortBy"
            :sort-order="sortOrder"
            :deleting-id="deletingId"
            @page-change="handleComponentPageChange"
            @size-change="handleComponentSizeChange"
            @sort="handleSort"
            @delete="handleDeleteRecord"
          />
          <inventory-table
            v-else
            :data="stageList"
            :loading="stageLoading"
            :pagination="stagePagination"
            :sort-by="sortBy"
            :sort-order="sortOrder"
            :deleting-id="deletingId"
            @page-change="handleStagePageChange"
            @size-change="handleStageSizeChange"
            @sort="handleSort"
            @delete="handleDeleteRecord"
          />
        </div>
      </section>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import dayjs from 'dayjs'
import { ElMessage, ElMessageBox } from 'element-plus'

import {
  getInventoryLogs,
  getInventoryLogOptions,
  importInventoryCSV,
  deleteInventoryLog,
  type InventoryLog,
  type InventoryProcessOption,
  type InventoryProductOption,
} from '@/api/inventory'

import {
  Box,
  DocumentAdd,
  Search,
  RefreshLeft,
  Refresh,
  Filter,
  Close,
  Grid,
  Coin,
  SetUp,
} from '@element-plus/icons-vue'

import InventoryTable from './components/InventoryTable.vue'
import { ITEM_COLORS, getProcessColor } from './components/inventoryColors'

// ステー子タブ（cd は配色用の工程CD）
const STAGE_TABS: { value: string; label: string; cd?: string }[] = [
  { value: 'all', label: '全て' },
  { value: 'cutting', label: '切断', cd: 'KT01' },
  { value: 'surface', label: '面取', cd: 'KT02' },
  { value: 'sw', label: 'SW', cd: 'KT03' },
  { value: 'forming', label: '成型', cd: 'KT04' },
  { value: 'plating', label: 'メッキ', cd: 'KT05' },
  { value: 'welding', label: '溶接', cd: 'KT07' },
  { value: 'inspection', label: '検査', cd: 'KT09' },
  { value: 'warehouse', label: '倉庫', cd: 'KT13' },
  { value: 'outsource_plating', label: '外注メッキ', cd: 'KT06' },
  { value: 'outsource_welding', label: '外注溶接', cd: 'KT08' },
  { value: 'pre_welding_inspection', label: '溶接前検査', cd: 'KT11' },
  { value: 'pre_outsource_inspection', label: '外注検査前', cd: 'KT10' },
  { value: 'pre_outsource_delivery', label: '外注支給前', cd: 'KT10' },
]

// Tab状态
const activeTab = ref('all')
const activeStageTab = ref('all')

// 加载状态
const loading = ref(false)
const materialLoading = ref(false)
const componentLoading = ref(false)
const stageLoading = ref(false)
const deletingId = ref<number | null>(null)

// 数据列表
const inventoryList = ref<any[]>([])
const materialList = ref<any[]>([])
const componentList = ref<any[]>([])
const stageList = ref<any[]>([])

// 数量合计
const inventoryTotalQuantity = ref(0)
const materialTotalQuantity = ref(0)
const componentTotalQuantity = ref(0)
const stageTotalQuantity = ref(0)

// 分页
const pagination = ref({
  page: 1,
  pageSize: 20,
  total: 0,
})

const materialPagination = ref({
  page: 1,
  pageSize: 20,
  total: 0,
})

const componentPagination = ref({
  page: 1,
  pageSize: 20,
  total: 0,
})

const stagePagination = ref({
  page: 1,
  pageSize: 20,
  total: 0,
})

// 筛选条件
const createDefaultFilters = () => ({
  keyword: '',
  dateRange: [] as string[],
  monthPicker: '',
  processCd: '' as string | undefined,
  productName: '' as string | undefined,
})
const filters = ref(createDefaultFilters())

// 下拉选项
const processOptions = ref<InventoryProcessOption[]>([])
const productOptions = ref<InventoryProductOption[]>([])
const optionsLoading = ref(false)
const productOptionsLoading = ref(false)
const productSelectProps = { value: 'product_name', label: 'product_name' }

// 排序条件
const sortBy = ref('log_date')
const sortOrder = ref<'asc' | 'desc'>('desc')

interface ApiError {
  response?: {
    data?: {
      message?: string
    }
  }
  message?: string
}

// 筛选前的全体件数・数量（KPI 对比用）
type KpiKey = 'all' | 'material' | 'component' | 'stage'
const baseTotals = ref<Record<KpiKey, { total: number; qty: number }>>({
  all: { total: 0, qty: 0 },
  material: { total: 0, qty: 0 },
  component: { total: 0, qty: 0 },
  stage: { total: 0, qty: 0 },
})

const stageBaseParams = () =>
  activeStageTab.value === 'all'
    ? { item: '製品棚卸' }
    : { stageType: activeStageTab.value }

const fetchBaseTotal = async (key: KpiKey, params: Record<string, string>) => {
  try {
    const res = await getInventoryLogs({ ...params, page: 1, pageSize: 1 })
    baseTotals.value[key] = {
      total: Number(res?.total ?? 0),
      qty: Number(res?.totalQuantity ?? 0),
    }
  } catch {
    baseTotals.value[key] = { total: 0, qty: 0 }
  }
}

const fetchBaseTotals = () =>
  Promise.all([
    fetchBaseTotal('all', {}),
    fetchBaseTotal('material', { item: '材料棚卸' }),
    fetchBaseTotal('component', { item: '部品棚卸' }),
    fetchBaseTotal('stage', stageBaseParams()),
  ])

const kpiCards = computed(() => {
  const filtered = activeChips.value.length > 0
  const stageLabel = STAGE_TABS.find((s) => s.value === activeStageTab.value)
  const base = baseTotals.value
  return [
    {
      key: 'all',
      label: '全て',
      icon: Grid,
      color: '#0284c7',
      total: pagination.value.total,
      qty: inventoryTotalQuantity.value,
      baseTotal: base.all.total,
      baseQty: base.all.qty,
      filtered,
    },
    {
      key: 'material',
      label: '材料',
      icon: Coin,
      color: ITEM_COLORS['材料棚卸'].color,
      total: materialPagination.value.total,
      qty: materialTotalQuantity.value,
      baseTotal: base.material.total,
      baseQty: base.material.qty,
      filtered,
    },
    {
      key: 'component',
      label: '部品',
      icon: SetUp,
      color: ITEM_COLORS['部品棚卸'].color,
      total: componentPagination.value.total,
      qty: componentTotalQuantity.value,
      baseTotal: base.component.total,
      baseQty: base.component.qty,
      filtered,
    },
    {
      key: 'stage',
      label:
        activeStageTab.value !== 'all' && stageLabel ? `ステー・${stageLabel.label}` : 'ステー',
      icon: Box,
      color: ITEM_COLORS['製品棚卸'].color,
      total: stagePagination.value.total,
      qty: stageTotalQuantity.value,
      baseTotal: base.stage.total,
      baseQty: base.stage.qty,
      filtered,
    },
  ]
})

const currentCard = computed(
  () => kpiCards.value.find((c) => c.key === activeTab.value) ?? kpiCards.value[0],
)

// 适用中的筛选条件标签
const activeChips = computed(() => {
  const f = filters.value
  const chips: { key: string; label: string; value: string; color: string }[] = []
  if (f.processCd) {
    const p = processOptions.value.find((o) => o.process_cd === f.processCd)
    chips.push({
      key: 'processCd',
      label: '工程',
      value: p?.process_name || f.processCd,
      color: getProcessColor(f.processCd).color,
    })
  }
  if (f.productName) {
    chips.push({ key: 'productName', label: '製品名', value: f.productName, color: '#4f46e5' })
  }
  if (f.keyword) {
    chips.push({ key: 'keyword', label: 'キーワード', value: f.keyword, color: '#0891b2' })
  }
  if (f.monthPicker) {
    chips.push({ key: 'month', label: '月', value: f.monthPicker, color: '#db2777' })
  } else if (f.dateRange?.length === 2) {
    chips.push({
      key: 'dateRange',
      label: '期間',
      value: `${f.dateRange[0]} ～ ${f.dateRange[1]}`,
      color: '#ea580c',
    })
  }
  return chips
})

// 格式化日期
const formatDate = (val: string) => dayjs(val).format('YYYY-MM-DD')

// 格式化时间
const formatTime = (val: string) => dayjs(val, 'HH:mm:ss').format('HH:mm')

// 获取工程・製品名下拉选项
const loadProcessOptions = async () => {
  optionsLoading.value = true
  try {
    const res = await getInventoryLogOptions({})
    processOptions.value = res.processes
  } finally {
    optionsLoading.value = false
  }
}

const loadProductOptions = async () => {
  productOptionsLoading.value = true
  try {
    const res = await getInventoryLogOptions({ processCd: filters.value.processCd || undefined })
    productOptions.value = res.products
    if (
      filters.value.productName &&
      !res.products.some((p) => p.product_name === filters.value.productName)
    ) {
      filters.value.productName = ''
    }
  } finally {
    productOptionsLoading.value = false
  }
}

const reloadOptions = () => Promise.all([loadProcessOptions(), loadProductOptions()])

// 获取所有数据
const fetchInventory = async () => {
  loading.value = true
  try {
    const response = await getInventoryLogs({
      ...filters.value,
      page: pagination.value.page,
      pageSize: pagination.value.pageSize,
      sortBy: sortBy.value,
      sortOrder: sortOrder.value,
    })

    // 由于request拦截器，response直接是data部分
    if (response && response.list) {
      inventoryList.value = response.list || []
      pagination.value.total = response.total || 0
      inventoryTotalQuantity.value = response.totalQuantity || 0
    } else {
      inventoryList.value = []
      pagination.value.total = 0
      inventoryTotalQuantity.value = 0
    }
  } catch (err) {
    console.error('棚卸データ取得に失敗しました', err)
    inventoryList.value = []
    pagination.value.total = 0
  } finally {
    loading.value = false
  }
}

// 获取材料数据
const fetchMaterial = async () => {
  materialLoading.value = true
  try {
    const response = await getInventoryLogs({
      ...filters.value,
      item: '材料棚卸',
      page: materialPagination.value.page,
      pageSize: materialPagination.value.pageSize,
      sortBy: sortBy.value,
      sortOrder: sortOrder.value,
    })

    // 由于request拦截器，response直接是data部分
    if (response && response.list) {
      materialList.value = response.list || []
      materialPagination.value.total = response.total || 0
      materialTotalQuantity.value = response.totalQuantity || 0
    } else {
      materialList.value = []
      materialPagination.value.total = 0
      materialTotalQuantity.value = 0
    }
  } catch (err) {
    console.error('材料データ取得に失敗しました', err)
    materialList.value = []
    materialPagination.value.total = 0
  } finally {
    materialLoading.value = false
  }
}

// 获取部品数据
const fetchComponent = async () => {
  componentLoading.value = true
  try {
    const response = await getInventoryLogs({
      ...filters.value,
      item: '部品棚卸',
      page: componentPagination.value.page,
      pageSize: componentPagination.value.pageSize,
      sortBy: sortBy.value,
      sortOrder: sortOrder.value,
    })

    // 由于request拦截器，response直接是data部分
    if (response && response.list) {
      componentList.value = response.list || []
      componentPagination.value.total = response.total || 0
      componentTotalQuantity.value = response.totalQuantity || 0
    } else {
      componentList.value = []
      componentPagination.value.total = 0
      componentTotalQuantity.value = 0
    }
  } catch (err) {
    console.error('部品データ取得に失敗しました', err)
    componentList.value = []
    componentPagination.value.total = 0
  } finally {
    componentLoading.value = false
  }
}

// 获取ステー数据
const fetchStage = async () => {
  stageLoading.value = true
  try {
    const params: any = {
      ...filters.value,
      page: stagePagination.value.page,
      pageSize: stagePagination.value.pageSize,
    }

    // 如果选择了"全て"，筛选項目字段为'製品棚卸'
    if (activeStageTab.value === 'all') {
      params.item = '製品棚卸'
    } else {
      // 如果选择了具体的ステー类型，筛选对应的工程CD
      params.stageType = activeStageTab.value
    }

    const response = await getInventoryLogs({
      ...params,
      sortBy: sortBy.value,
      sortOrder: sortOrder.value,
    })

    // 由于request拦截器，response直接是data部分
    if (response && response.list) {
      stageList.value = response.list || []
      stagePagination.value.total = response.total || 0
      stageTotalQuantity.value = response.totalQuantity || 0
    } else {
      stageList.value = []
      stagePagination.value.total = 0
      stageTotalQuantity.value = 0
    }
  } catch (err) {
    console.error('ステーデータ取得に失敗しました', err)
    stageList.value = []
    stagePagination.value.total = 0
  } finally {
    stageLoading.value = false
  }
}

const refreshAllTabs = () =>
  Promise.all([fetchInventory(), fetchMaterial(), fetchComponent(), fetchStage()])

const resetAllPages = () => {
  pagination.value.page = 1
  materialPagination.value.page = 1
  componentPagination.value.page = 1
  stagePagination.value.page = 1
}

// Tab切换时刷新当前Tab
const fetchByTab = (name: string) => {
  switch (name) {
    case 'all':
      return fetchInventory()
    case 'material':
      return fetchMaterial()
    case 'component':
      return fetchComponent()
    case 'stage':
      return fetchStage()
  }
}

watch(activeTab, (name) => fetchByTab(name))

// ステー子Tab切换处理
const handleStageTabChange = (value: string) => {
  if (activeStageTab.value === value) return
  activeStageTab.value = value
  stagePagination.value.page = 1
  fetchStage()
  fetchBaseTotal('stage', stageBaseParams())
}

// 排序处理（服务端全量排序）
const handleSort = (field: string, order: 'asc' | 'desc' | null) => {
  sortBy.value = field
  // Element Plus 第三次点击会回到 null，这里回退为降序，避免状态不明确
  sortOrder.value = order ?? 'desc'

  resetAllPages()
  refreshAllTabs()
}

// 月份选择处理
const handleMonthChange = (month: string) => {
  if (month) {
    const startDate = dayjs(`${month}-01`)
    const endDate = startDate.endOf('month')
    filters.value.dateRange = [startDate.format('YYYY-MM-DD'), endDate.format('YYYY-MM-DD')]
  } else {
    // 如果清空月份选择，也清空日期范围
    filters.value.dateRange = []
  }
  handleSearch()
}

// 手动修改日期范围时清除月选择，避免两个条件冲突
const handleDateRangeChange = (range: string[] | null) => {
  filters.value.dateRange = range ?? []
  filters.value.monthPicker = ''
  handleSearch()
}

// 搜索处理
const handleSearch = async () => {
  resetAllPages()
  await refreshAllTabs()
}

// 关键词输入防抖自动检索
let keywordTimer: ReturnType<typeof setTimeout> | null = null
const clearKeywordTimer = () => {
  if (keywordTimer) {
    clearTimeout(keywordTimer)
    keywordTimer = null
  }
}
const handleKeywordInput = () => {
  clearKeywordTimer()
  keywordTimer = setTimeout(() => {
    keywordTimer = null
    handleSearch()
  }, 400)
}
const searchNow = () => {
  clearKeywordTimer()
  handleSearch()
}
onBeforeUnmount(clearKeywordTimer)

// 工程变更：联动刷新製品名候选后检索
const handleProcessChange = async () => {
  await loadProductOptions()
  await handleSearch()
}

const handleProductChange = () => handleSearch()

const removeChip = async (key: string) => {
  clearKeywordTimer()
  switch (key) {
    case 'processCd':
      filters.value.processCd = ''
      await loadProductOptions()
      break
    case 'productName':
      filters.value.productName = ''
      break
    case 'keyword':
      filters.value.keyword = ''
      break
    case 'month':
    case 'dateRange':
      filters.value.monthPicker = ''
      filters.value.dateRange = []
      break
  }
  await handleSearch()
}

// 重置筛选
const resetFilters = async () => {
  clearKeywordTimer()
  filters.value = createDefaultFilters()
  resetAllPages()
  await Promise.all([refreshAllTabs(), loadProductOptions()])
}

// 数据导入
const handleImport = async () => {
  loading.value = true
  try {
    const response = await importInventoryCSV()

    if (response.data?.summary) {
      const { summary, fileDetails } = response.data
      let message = `✅ CSV取込が完了しました\n\n【合計】\n処理件数: ${summary.totalProcessed}件\n新規追加: ${summary.newRecords}件\n重複スキップ: ${summary.duplicates}件`

      // 显示各文件的详细信息
      if (fileDetails) {
        message += `\n\n【InventoryLog.csv】\n処理件数: ${fileDetails.inventoryLog.processed}件\n新規追加: ${fileDetails.inventoryLog.newRecords}件\n重複スキップ: ${fileDetails.inventoryLog.duplicates}件`
        if (!fileDetails.inventoryLog.exists) {
          message += '\n⚠️ ファイルが見つかりませんでした'
        }

        message += `\n\n【Partslog.csv】\n処理件数: ${fileDetails.partsLog.processed}件\n新規追加: ${fileDetails.partsLog.newRecords}件\n重複スキップ: ${fileDetails.partsLog.duplicates}件`
        if (!fileDetails.partsLog.exists) {
          message += '\n⚠️ ファイルが見つかりませんでした'
        }

        message += `\n\n【Materiallog.csv】\n処理件数: ${fileDetails.materialLog.processed}件\n新規追加: ${fileDetails.materialLog.newRecords}件\n重複スキップ: ${fileDetails.materialLog.duplicates}件`
        if (!fileDetails.materialLog.exists) {
          message += '\n⚠️ ファイルが見つかりませんでした'
        }
      }

      ElMessage.success(message)
    } else {
      ElMessage.success('✅ ' + (response.message ?? 'CSV取込が完了しました'))
    }

    await Promise.all([refreshAllTabs(), reloadOptions(), fetchBaseTotals()])
  } catch (err: unknown) {
    const apiError = err as ApiError
    const msg = apiError?.response?.data?.message || apiError?.message || 'CSV取込に失敗しました'
    ElMessage.error('❌ ' + msg)
  } finally {
    loading.value = false
  }
}

// 删除处理
const handleDeleteRecord = async (record: InventoryLog) => {
  try {
    await ElMessageBox.confirm(
      `選択した棚卸データを削除しますか？\n\n製品: ${record.product_name} (${record.product_cd})\n日付: ${formatDate(record.log_date)} ${formatTime(record.log_time)}\n数量: ${record.quantity}`,
      '削除確認',
      {
        confirmButtonText: '削除',
        cancelButtonText: 'キャンセル',
        type: 'warning',
        autofocus: false,
      },
    )
  } catch {
    return
  }

  try {
    deletingId.value = record.id
    await deleteInventoryLog(record.id)
    ElMessage.success('✅ 棚卸データを削除しました')
    await Promise.all([refreshAllTabs(), fetchBaseTotals()])
  } catch (err: unknown) {
    const apiError = err as ApiError
    const msg = apiError?.response?.data?.message || apiError?.message || '削除に失敗しました'
    ElMessage.error('❌ ' + msg)
  } finally {
    deletingId.value = null
  }
}

// 分页处理 - 全て
const handlePageChange = (newPage: number) => {
  pagination.value.page = newPage
  fetchInventory()
}

const handleSizeChange = (newSize: number) => {
  pagination.value.pageSize = newSize
  pagination.value.page = 1
  fetchInventory()
}

// 分页处理 - 材料
const handleMaterialPageChange = (newPage: number) => {
  materialPagination.value.page = newPage
  fetchMaterial()
}

const handleMaterialSizeChange = (newSize: number) => {
  materialPagination.value.pageSize = newSize
  materialPagination.value.page = 1
  fetchMaterial()
}

// 分页处理 - 部品
const handleComponentPageChange = (newPage: number) => {
  componentPagination.value.page = newPage
  fetchComponent()
}

const handleComponentSizeChange = (newSize: number) => {
  componentPagination.value.pageSize = newSize
  componentPagination.value.page = 1
  fetchComponent()
}

// 分页处理 - ステー
const handleStagePageChange = (newPage: number) => {
  stagePagination.value.page = newPage
  fetchStage()
}

const handleStageSizeChange = (newSize: number) => {
  stagePagination.value.pageSize = newSize
  stagePagination.value.page = 1
  fetchStage()
}

// 组件挂载时初始化数据
onMounted(async () => {
  await Promise.all([refreshAllTabs(), reloadOptions(), fetchBaseTotals()])
})
</script>

<style scoped>
.inventory-container {
  --il-surface: rgba(255, 255, 255, 0.94);
  --il-border: rgba(15, 23, 42, 0.07);
  --il-muted: #64748b;
  --il-text: #0f172a;
  position: relative;
  z-index: 0;
  padding: 12px 14px 18px;
  box-sizing: border-box;
  min-height: 100vh;
  background: linear-gradient(165deg, #f8fafc 0%, #f1f5f9 50%, #eef2f7 100%);
}

.page-ambient {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background:
    radial-gradient(ellipse 60% 45% at 8% -8%, rgba(79, 70, 229, 0.1), transparent 60%),
    radial-gradient(ellipse 50% 40% at 95% 10%, rgba(14, 165, 233, 0.1), transparent 55%),
    radial-gradient(ellipse 40% 35% at 60% 110%, rgba(16, 185, 129, 0.06), transparent 60%);
}

.page-hero,
.content-container {
  position: relative;
  z-index: 1;
  width: 100%;
}

/* ===== ヘッダー ===== */
.page-hero {
  margin-bottom: 12px;
}

.hero-inner {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  padding: 14px 18px;
  border-radius: 14px;
  color: #fff;
  background: linear-gradient(120deg, #4338ca 0%, #4f46e5 35%, #0284c7 100%);
  box-shadow: 0 10px 30px -12px rgba(67, 56, 202, 0.55);
}

.hero-inner::after {
  content: '';
  position: absolute;
  right: -60px;
  top: -80px;
  width: 260px;
  height: 260px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.18), transparent 70%);
  pointer-events: none;
}

.hero-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.hero-icon {
  flex-shrink: 0;
  width: 42px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.28);
  backdrop-filter: blur(6px);
}

.hero-title {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 700;
  letter-spacing: -0.01em;
  line-height: 1.25;
}

.hero-sub {
  margin: 3px 0 0;
  font-size: 12px;
  opacity: 0.85;
}

.hero-actions {
  position: relative;
  z-index: 1;
  display: flex;
  gap: 8px;
}

.hero-btn {
  border-radius: 9px;
  font-weight: 600;
  height: 32px;
}

.hero-btn--ghost {
  color: #fff;
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.35);
}

.hero-btn--ghost:hover,
.hero-btn--ghost:focus {
  color: #fff;
  background: rgba(255, 255, 255, 0.22);
  border-color: rgba(255, 255, 255, 0.5);
}

.hero-btn--solid {
  color: #4338ca;
  background: #fff;
  border-color: #fff;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.18);
}

.hero-btn--solid:hover,
.hero-btn--solid:focus {
  color: #3730a3;
  background: #eef2ff;
  border-color: #eef2ff;
}

.content-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* ===== KPI ===== */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.kpi-card {
  position: relative;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 10px;
  min-width: 0;
  padding: 8px 14px;
  white-space: nowrap;
  text-align: left;
  cursor: pointer;
  font: inherit;
  background: var(--il-surface);
  border: 1px solid var(--il-border);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease,
    border-color 0.18s ease;
}

.kpi-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: var(--accent);
  opacity: 0.85;
}

.kpi-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 24px -12px color-mix(in srgb, var(--accent) 55%, transparent);
}

.kpi-card.is-active {
  border-color: color-mix(in srgb, var(--accent) 45%, transparent);
  background: linear-gradient(
    135deg,
    color-mix(in srgb, var(--accent) 9%, #fff) 0%,
    #fff 70%
  );
  box-shadow: 0 10px 24px -12px color-mix(in srgb, var(--accent) 60%, transparent);
}

.kpi-icon {
  flex-shrink: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: var(--accent);
  background: color-mix(in srgb, var(--accent) 12%, transparent);
}

.kpi-card.is-active .kpi-icon {
  color: #fff;
  background: var(--accent);
}

.kpi-label {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 13px;
  font-weight: 700;
  color: var(--il-text);
  margin-right: auto;
}

.kpi-flag {
  flex-shrink: 0;
  padding: 0 5px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  line-height: 16px;
  color: var(--accent);
  background: color-mix(in srgb, var(--accent) 12%, transparent);
}

.kpi-card.is-filtered::before {
  width: 4px;
  background: repeating-linear-gradient(
    180deg,
    var(--accent) 0 6px,
    color-mix(in srgb, var(--accent) 35%, transparent) 6px 10px
  );
}

.kpi-base {
  font-size: 11px;
  font-weight: 600;
  color: #94a3b8;
  font-variant-numeric: tabular-nums;
}

.kpi-metric {
  display: inline-flex;
  align-items: baseline;
  gap: 5px;
}

.kpi-metric-key {
  font-size: 11px;
  font-weight: 600;
  color: var(--il-muted);
}

.kpi-value {
  font-size: 1.1rem;
  font-weight: 700;
  line-height: 1.2;
  color: var(--il-text);
  font-variant-numeric: tabular-nums;
}

.kpi-value--qty {
  color: var(--accent);
}

.kpi-sep {
  width: 1px;
  height: 16px;
  background: rgba(15, 23, 42, 0.1);
}

/* ===== パネル共通 ===== */
.panel {
  background: var(--il-surface);
  border: 1px solid var(--il-border);
  border-radius: 12px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  backdrop-filter: blur(10px);
}

.filter-panel {
  padding: 10px 14px;
}

.filter-line {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 14px;
}

.panel-title {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding-right: 14px;
  border-right: 1px solid rgba(15, 23, 42, 0.08);
  font-size: 13px;
  font-weight: 700;
  color: #1e293b;
}

.panel-title-icon {
  color: #4f46e5;
  font-size: 16px;
}

.panel-badge {
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 9px;
  font-size: 11px;
  color: #fff;
  background: #4f46e5;
}

.filter-actions {
  flex-shrink: 0;
  display: flex;
  gap: 6px;
  margin-left: auto;
}

.filter-actions .el-button + .el-button {
  margin-left: 0;
}

.filter-field {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.filter-field--process {
  flex: 1 1 170px;
  max-width: 240px;
}

.filter-field--product {
  flex: 2 1 240px;
  max-width: 420px;
}

.filter-field--keyword {
  flex: 1 1 170px;
  max-width: 240px;
}

.filter-field--date {
  flex: 0 0 auto;
  width: 290px;
}

.filter-field--month {
  flex: 0 0 auto;
  width: 170px;
}

.field-label {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  white-space: nowrap;
}

.field-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.field-dot--process {
  background: #2563eb;
}
.field-dot--product {
  background: #4f46e5;
}
.field-dot--keyword {
  background: #0891b2;
}
.field-dot--date {
  background: #ea580c;
}
.field-dot--month {
  background: #db2777;
}

.field-control {
  flex: 1 1 auto;
  min-width: 0;
  width: auto !important;
}

.field-control :deep(.el-input__wrapper),
.field-control :deep(.el-select__wrapper),
:deep(.field-control.el-range-editor) {
  border-radius: 8px;
  min-height: 32px;
}

.opt-row {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  min-width: 0;
}

.opt-dot {
  flex-shrink: 0;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.9);
}

.opt-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.opt-meta {
  flex-shrink: 0;
  font-size: 11px;
  color: #94a3b8;
}

.chip-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed rgba(15, 23, 42, 0.1);
}

.chip-row-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--il-muted);
}

.filter-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 2px 4px 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  color: var(--chip);
  background: color-mix(in srgb, var(--chip) 9%, #fff);
  border: 1px solid color-mix(in srgb, var(--chip) 28%, transparent);
}

.filter-chip-key {
  font-weight: 700;
}

.filter-chip-val {
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #334155;
}

.filter-chip-close {
  cursor: pointer;
  padding: 2px;
  border-radius: 50%;
  transition: background 0.15s ease;
}

.filter-chip-close:hover {
  background: color-mix(in srgb, var(--chip) 18%, transparent);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* ===== タブ ===== */
.tab-panel {
  padding: 10px 12px 12px;
}

.custom-tabs :deep(.el-tabs__header) {
  margin: 0 0 10px;
}

.custom-tabs :deep(.el-tabs__nav-wrap::after) {
  height: 1px;
  background: rgba(15, 23, 42, 0.08);
}

.custom-tabs :deep(.el-tabs__active-bar) {
  display: none;
}

.custom-tabs :deep(.el-tabs__content) {
  display: none;
}

.custom-tabs :deep(.el-tabs__item) {
  height: 38px;
  padding: 0 14px !important;
  font-weight: 600;
  color: var(--il-muted);
}

.tab-label {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 100%;
}

.tab-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent);
  opacity: 0.5;
}

.tab-count {
  padding: 0 6px;
  border-radius: 999px;
  font-size: 11px;
  line-height: 17px;
  color: var(--il-muted);
  background: rgba(100, 116, 139, 0.1);
  font-variant-numeric: tabular-nums;
}

.custom-tabs :deep(.el-tabs__item:hover) .tab-label,
.custom-tabs :deep(.el-tabs__item.is-active) .tab-label {
  color: var(--accent);
}

.custom-tabs :deep(.el-tabs__item.is-active) .tab-label::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: -1px;
  height: 3px;
  border-radius: 3px 3px 0 0;
  background: var(--accent);
}

.custom-tabs :deep(.el-tabs__item.is-active) .tab-dot {
  opacity: 1;
}

.custom-tabs :deep(.el-tabs__item.is-active) .tab-count {
  color: #fff;
  background: var(--accent);
}

.tab-content {
  min-height: 240px;
}

.tab-header {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 10px;
}

.tab-header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.tab-heading {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: var(--il-text);
}

.tab-heading-bar {
  width: 4px;
  height: 16px;
  border-radius: 2px;
  background: var(--accent);
}

.tab-stats {
  display: flex;
  gap: 6px;
  align-items: center;
  flex-wrap: wrap;
}

.stat-pill {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 999px;
  line-height: 1.4;
  color: var(--accent);
  background: color-mix(in srgb, var(--accent) 10%, transparent);
  border: 1px solid color-mix(in srgb, var(--accent) 25%, transparent);
  font-variant-numeric: tabular-nums;
}

.stat-pill--qty {
  color: #047857;
  background: rgba(16, 185, 129, 0.1);
  border-color: rgba(16, 185, 129, 0.25);
}

.stage-subtabs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 8px;
  border-radius: 10px;
  background: rgba(241, 245, 249, 0.7);
  border: 1px solid rgba(15, 23, 42, 0.05);
}

.stage-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  font: inherit;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.4;
  cursor: pointer;
  border-radius: 999px;
  color: #475569;
  background: #fff;
  border: 1px solid rgba(15, 23, 42, 0.1);
  transition:
    color 0.15s ease,
    background 0.15s ease,
    border-color 0.15s ease,
    box-shadow 0.15s ease;
}

.stage-chip-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--chip);
}

.stage-chip:hover {
  color: var(--chip);
  border-color: color-mix(in srgb, var(--chip) 45%, transparent);
  background: color-mix(in srgb, var(--chip) 6%, #fff);
}

.stage-chip.is-active {
  color: #fff;
  border-color: transparent;
  background: var(--chip);
  box-shadow: 0 4px 10px -4px color-mix(in srgb, var(--chip) 70%, transparent);
}

.stage-chip.is-active .stage-chip-dot {
  background: #fff;
}

/* ===== レスポンシブ ===== */
@media (max-width: 1100px) {
  .kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .panel-title {
    border-right: none;
    padding-right: 0;
  }
}

@media (max-width: 768px) {
  .inventory-container {
    padding: 8px;
  }

  .hero-inner {
    padding: 12px 14px;
  }

  .hero-title {
    font-size: 1.05rem;
  }

  .filter-field,
  .filter-field--date,
  .filter-field--month {
    flex: 1 1 100%;
    width: auto;
    max-width: none;
  }

  .field-label {
    width: 72px;
  }

  .stage-subtabs {
    flex-wrap: nowrap;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .stage-chip {
    white-space: nowrap;
  }
}

@media (max-width: 480px) {
  .kpi-grid {
    grid-template-columns: 1fr;
  }

  .hero-actions {
    width: 100%;
  }

  .hero-btn {
    flex: 1;
  }

  .kpi-card {
    flex-wrap: wrap;
  }
}
</style>

<style>
.inventory-option-popper .el-select-dropdown__item,
.inventory-option-popper .el-select-dropdown__option-item {
  display: flex;
  align-items: center;
}

.inventory-option-popper .opt-row {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  min-width: 0;
}

.inventory-option-popper .opt-dot {
  flex-shrink: 0;
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.inventory-option-popper .opt-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.inventory-option-popper .opt-meta {
  flex-shrink: 0;
  font-size: 11px;
  color: #94a3b8;
}
</style>
