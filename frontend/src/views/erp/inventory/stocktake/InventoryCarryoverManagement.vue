<template>
  <div class="inventory-carryover-management">
    <div class="page-ambient" aria-hidden="true" />

    <div class="page-shell">
      <!-- ヘッダー -->
      <header class="page-hero">
        <div class="hero-brand">
          <div class="hero-icon">
            <el-icon :size="22"><Share /></el-icon>
          </div>
          <div class="hero-text">
            <h1 class="hero-title">棚卸データ繰越管理</h1>
            <p class="hero-sub">特定月・工程の月末棚卸を翌月の期初在庫へ繰越</p>
          </div>
        </div>
        <div class="hero-tabs" role="tablist">
          <button
            type="button"
            class="hero-tab"
            :class="{ 'is-active': activeTab === 'carryover' }"
            @click="activeTab = 'carryover'"
          >
            <el-icon><Share /></el-icon>データ繰越
          </button>
          <button
            type="button"
            class="hero-tab"
            :class="{ 'is-active': activeTab === 'history' }"
            @click="activeTab = 'history'"
          >
            <el-icon><Collection /></el-icon>繰越履歴管理
          </button>
        </div>
      </header>

      <div v-if="activeTab === 'carryover'" class="carryover-content">
        <!-- 検索条件 + 一括繰越 -->
        <section class="panel toolbar-panel">
          <div class="toolbar-line">
            <div class="panel-title">
              <el-icon class="panel-title-icon"><Filter /></el-icon>
              <span>検索条件</span>
            </div>

            <div class="toolbar-field toolbar-field--month">
              <label class="field-label"><span class="field-dot field-dot--month" />棚卸月</label>
              <el-date-picker
                v-model="filterParams.month"
                type="month"
                placeholder="月を選択"
                format="YYYY-MM"
                value-format="YYYY-MM"
                size="small"
                class="field-control"
                clearable
                @change="handleMonthChange"
              />
            </div>

            <div class="month-hint" :class="{ 'is-ready': !!filterParams.month }">
              <el-icon class="month-hint-icon"><InfoFilled /></el-icon>
              <template v-if="filterParams.month">
                <span class="month-hint-chip month-hint-chip--from">
                  {{ filterParams.month }} 棚卸データ
                </span>
                <el-icon class="month-hint-arrow"><Right /></el-icon>
                <span class="month-hint-chip month-hint-chip--to">
                  {{ getNextMonth(filterParams.month) }} 期初在庫へ繰越
                </span>
              </template>
              <span v-else>選択した棚卸月のデータを、翌月の期初在庫へ繰越します</span>
            </div>

            <div class="toolbar-field toolbar-field--process">
              <label class="field-label"><span class="field-dot field-dot--process" />工程</label>
              <el-select
                v-model="filterParams.process_cd"
                placeholder="工程を選択"
                size="small"
                class="field-control"
                popper-class="carryover-option-popper"
                clearable
                filterable
                :loading="processLoading"
                @change="handleProcessChange"
              >
                <template #prefix>
                  <span
                    v-if="filterParams.process_cd"
                    class="opt-dot"
                    :style="{ background: getProcessColor(filterParams.process_cd).color }"
                  />
                </template>
                <el-option
                  v-for="process in processOptions"
                  :key="process.value"
                  :label="process.label"
                  :value="process.value"
                >
                  <div class="opt-row">
                    <span
                      class="opt-dot"
                      :style="{ background: getProcessColor(process.value).color }"
                    />
                    <span class="opt-name">{{ process.name }}</span>
                    <span class="opt-meta">{{ process.value }}</span>
                  </div>
                </el-option>
              </el-select>
            </div>

            <el-button size="small" :icon="Refresh" @click="clearFilters">クリア</el-button>

            <div class="toolbar-spacer" />

            <el-tooltip
              :disabled="!!filterParams.month"
              content="棚卸月を選択してください"
              placement="top"
            >
              <span>
                <el-button
                  class="btn-bulk"
                  :icon="Promotion"
                  :disabled="!filterParams.month || summaryLoading"
                  @click="openBulkDialog"
                >
                  全工程一括繰越
                  <span v-if="summaryPendingCount > 0" class="btn-bulk-count">
                    {{ summaryPendingCount.toLocaleString() }}
                  </span>
                </el-button>
              </span>
            </el-tooltip>
          </div>
        </section>

        <!-- 工程別サマリー -->
        <section v-if="filterParams.month" v-loading="summaryLoading" class="panel summary-panel">
          <div class="summary-head">
            <div class="summary-title">
              <span class="summary-title-bar" />
              工程別サマリー
              <span v-if="summary" class="summary-date">
                {{ summary.as_of_date }} 月末棚卸
                <el-icon><Right /></el-icon>
                {{ summary.target_date }} 期初在庫
              </span>
            </div>
            <div class="summary-stats">
              <span class="stat-pill stat-pill--indigo">
                対象 {{ summaryTotals.count.toLocaleString() }} 件
              </span>
              <span class="stat-pill stat-pill--emerald">
                数量 {{ summaryTotals.qty.toLocaleString() }}
              </span>
              <span class="stat-pill stat-pill--slate">
                繰越済 {{ summaryTotals.carried.toLocaleString() }} 件
              </span>
              <el-button
                text
                size="small"
                :icon="Refresh"
                :loading="summaryLoading"
                @click="loadSummary"
              >
                更新
              </el-button>
            </div>
          </div>

          <div class="process-grid">
            <button
              v-for="p in summary?.processes ?? []"
              :key="p.process_cd"
              type="button"
              class="process-tile"
              :class="{
                'is-active': filterParams.process_cd === p.process_cd,
                'is-empty': p.count === 0,
              }"
              :style="{ '--accent': getProcessColor(p.process_cd).color }"
              @click="selectProcessFromTile(p.process_cd)"
            >
              <div class="tile-head">
                <span class="tile-dot" />
                <span class="tile-name">{{ p.process_name || p.process_cd }}</span>
                <span class="tile-status" :class="`tile-status--${getStatus(p).key}`">
                  {{ getStatus(p).label }}
                </span>
              </div>
              <div class="tile-metrics">
                <span class="tile-metric">
                  <span class="tile-metric-key">件数</span>
                  <span class="tile-metric-val">{{ p.count.toLocaleString() }}</span>
                </span>
                <span class="tile-metric">
                  <span class="tile-metric-key">数量</span>
                  <span class="tile-metric-val tile-metric-val--qty">
                    {{ p.total_quantity.toLocaleString() }}
                  </span>
                </span>
              </div>
              <div class="tile-progress">
                <span
                  class="tile-progress-bar"
                  :style="{ width: `${getCarriedRatio(p)}%` }"
                />
              </div>
              <div class="tile-foot">
                <span>{{ p.process_cd }}</span>
                <span>繰越済 {{ p.carried_count.toLocaleString() }}</span>
              </div>
            </button>
          </div>
        </section>

        <!-- 明細 -->
        <section
          v-if="carryoverSearched && carryoverTotal > 0"
          class="panel data-panel"
          :style="{ '--accent': getProcessColor(filterParams.process_cd).color }"
        >
          <div class="data-header">
            <div class="data-title">
              <span class="data-title-bar" />
              <h3>棚卸データ明細</h3>
              <span class="process-chip">
                <span class="process-chip-dot" />
                {{ currentProcessLabel }}
              </span>
              <span class="data-count">{{ carryoverTotal.toLocaleString() }} 件</span>
              <span v-if="selectedData.length" class="data-selected">
                選択中 {{ selectedData.length.toLocaleString() }} 件
              </span>
            </div>
            <div class="data-actions">
              <el-button
                size="small"
                :icon="Check"
                :loading="selectAllLoading"
                :disabled="loading"
                @click="selectAll"
              >
                全選択（検索結果全件）
              </el-button>
              <el-button size="small" :icon="Close" @click="deselectAll">全解除</el-button>
              <el-button
                size="small"
                class="btn-carryover"
                :icon="Share"
                :disabled="selectedData.length === 0"
                :loading="carryoverLoading"
                @click="handleCarryover"
              >
                選択分を繰越 ({{ selectedData.length }})
              </el-button>
            </div>
          </div>

          <el-table
            ref="carryoverTableRef"
            v-loading="loading"
            row-key="product_cd"
            :data="inventoryData"
            stripe
            size="small"
            highlight-current-row
            class="data-table"
            @selection-change="handleSelectionChange"
          >
            <el-table-column type="selection" width="48" align="center" />
            <el-table-column prop="product_cd" label="製品CD" width="130" align="center">
              <template #default="{ row }">
                <span class="product-code">{{ row.product_cd }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="product_name" min-width="220" show-overflow-tooltip>
              <template #header>
                <span class="sortable-header" @click="handleCustomSort('product_name')">
                  製品名
                  <el-icon
                    class="sort-icon"
                    :class="{
                      'sort-asc':
                        sortConfig.prop === 'product_name' && sortConfig.order === 'ascending',
                      'sort-desc':
                        sortConfig.prop === 'product_name' && sortConfig.order === 'descending',
                    }"
                  >
                    <Sort />
                  </el-icon>
                </span>
              </template>
              <template #default="{ row }">
                <span class="product-name">{{ row.product_name }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="item" label="項目" width="110" align="center">
              <template #default="{ row }">
                <span class="color-pill" :style="itemPillStyle(row.item)">{{ row.item }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="total_quantity" label="合計数量" width="140" align="right">
              <template #default="{ row }">
                <span class="quantity-value">{{ formatNumber(row.total_quantity) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="unit" label="単位" width="90" align="center">
              <template #default="{ row }">
                <span class="unit-value">{{ row.unit }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="location_cd" label="保管場所" min-width="140" align="center">
              <template #default="{ row }">
                <span class="location-tag">
                  <el-icon><Location /></el-icon>{{ row.location_cd }}
                </span>
              </template>
            </el-table-column>
          </el-table>

          <div class="table-footer">
            <div class="sum-row">
              <span class="sum-label">合計数量（全件）</span>
              <span class="sum-value">{{ formatNumber(totalQuantitySum) }}</span>
            </div>
            <el-pagination
              :current-page="carryoverPage"
              :page-size="carryoverPageSize"
              :total="carryoverTotal"
              :disabled="loading"
              layout="total, prev, pager, next"
              background
              @current-change="handleCarryoverPageChange"
            />
          </div>
        </section>

        <!-- 空状態 -->
        <section
          v-else-if="carryoverSearched && carryoverTotal === 0 && !loading"
          class="panel empty-panel"
        >
          <el-empty :image-size="72" description="検索条件に一致するデータが見つかりません" />
        </section>

        <section v-else-if="!filterParams.month" class="panel guide-panel">
          <div class="guide-icon"><el-icon :size="26"><Calendar /></el-icon></div>
          <div class="guide-text">
            <h3>棚卸月を選択してください</h3>
            <p>
              月を選ぶと工程別の繰越対象が表示されます。工程カードをクリックすると明細を確認でき、
              「全工程一括繰越」で全工程をまとめて繰越できます。
            </p>
          </div>
        </section>
      </div>

      <!-- 繰越履歴管理 -->
      <div v-if="activeTab === 'history'" class="history-content">
        <InventoryCarryoverHistory @refresh="refreshHistoryData" />
      </div>
    </div>

    <!-- 一括繰越ダイアログ -->
    <el-dialog
      v-model="bulkDialogVisible"
      :title="bulkResult ? '一括繰越 結果' : '全工程一括繰越'"
      width="680px"
      class="bulk-dialog"
      :close-on-click-modal="!bulkLoading"
      :show-close="!bulkLoading"
      append-to-body
    >
      <template v-if="!bulkResult">
        <div class="bulk-banner">
          <el-icon :size="20"><Promotion /></el-icon>
          <div>
            <strong>{{ filterParams.month }}</strong> の全工程の月末棚卸を
            <strong>{{ summary?.target_date }}</strong> の期初在庫として登録します。
          </div>
        </div>
        <el-table :data="summary?.processes ?? []" size="small" class="bulk-table" max-height="340">
          <el-table-column label="工程" min-width="150">
            <template #default="{ row }">
              <span
                class="color-pill"
                :style="pillStyle(getProcessColor(row.process_cd))"
              >
                <span class="pill-dot" />{{ row.process_name || row.process_cd }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="件数" width="90" align="right">
            <template #default="{ row }">{{ row.count.toLocaleString() }}</template>
          </el-table-column>
          <el-table-column label="数量" width="120" align="right">
            <template #default="{ row }">{{ row.total_quantity.toLocaleString() }}</template>
          </el-table-column>
          <el-table-column label="状態" width="100" align="center">
            <template #default="{ row }">
              <span class="tile-status" :class="`tile-status--${getStatus(row).key}`">
                {{ getStatus(row).label }}
              </span>
            </template>
          </el-table-column>
        </el-table>
        <div class="bulk-options">
          <el-checkbox v-model="skipExisting">繰越済みのデータはスキップする（重複登録防止）</el-checkbox>
          <span class="bulk-total">
            合計 <strong>{{ summaryTotals.count.toLocaleString() }}</strong> 件 / 数量
            <strong>{{ summaryTotals.qty.toLocaleString() }}</strong>
          </span>
        </div>
      </template>

      <template v-else>
        <div class="bulk-result-head">
          <div class="result-card result-card--success">
            <span class="result-key">登録</span>
            <span class="result-val">{{ bulkResult.successCount.toLocaleString() }}</span>
          </div>
          <div class="result-card result-card--qty">
            <span class="result-key">数量</span>
            <span class="result-val">{{ bulkResult.totalQuantity.toLocaleString() }}</span>
          </div>
          <div class="result-card result-card--existing">
            <span class="result-key">既存スキップ</span>
            <span class="result-val">{{ bulkResult.existingCount.toLocaleString() }}</span>
          </div>
          <div class="result-card result-card--skip">
            <span class="result-key">その他スキップ</span>
            <span class="result-val">{{ bulkResult.skippedCount.toLocaleString() }}</span>
          </div>
        </div>
        <el-table :data="bulkResult.processes" size="small" class="bulk-table" max-height="320">
          <el-table-column label="工程" min-width="150">
            <template #default="{ row }">
              <span
                class="color-pill"
                :style="pillStyle(getProcessColor(row.process_cd))"
              >
                <span class="pill-dot" />{{ row.process_name || row.process_cd }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="登録" width="80" align="right" prop="successCount" />
          <el-table-column label="数量" width="110" align="right">
            <template #default="{ row }">{{ row.quantity.toLocaleString() }}</template>
          </el-table-column>
          <el-table-column label="既存" width="80" align="right" prop="existingCount" />
          <el-table-column label="スキップ" width="90" align="right" prop="skippedCount" />
        </el-table>
      </template>

      <template #footer>
        <template v-if="!bulkResult">
          <el-button :disabled="bulkLoading" @click="bulkDialogVisible = false">キャンセル</el-button>
          <el-button
            class="btn-bulk"
            :icon="Promotion"
            :loading="bulkLoading"
            :disabled="summaryTotals.count === 0"
            @click="executeBulkCarryover"
          >
            一括繰越を実行
          </el-button>
        </template>
        <el-button v-else type="primary" @click="bulkDialogVisible = false">閉じる</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Share,
  Collection,
  Filter,
  Refresh,
  Check,
  Close,
  Calendar,
  Location,
  Sort,
  Promotion,
  Right,
  InfoFilled,
} from '@element-plus/icons-vue'
import {
  getCarryoverData,
  executeCarryover,
  getCarryoverSummary,
  executeCarryoverAll,
  type CarryoverSummaryPayload,
  type CarryoverProcessSummary,
  type CarryoverExecuteAllResult,
} from '@/api/inventoryCarryover'
import { fetchProcesses } from '@/api/master/processMaster'
import InventoryCarryoverHistory from './components/InventoryCarryoverHistory.vue'
import { getProcessColor, type ColorToken } from './components/inventoryColors'
import { useInventoryOperationPermission } from '@/composables/useInventoryOperationPermission'
import { guardInventoryOperation } from '@/utils/inventoryOperationGuard'

const { canEdit } = useInventoryOperationPermission()

// 响应式数据
const activeTab = ref('carryover')
const loading = ref(false)
const carryoverLoading = ref(false)
const inventoryData = ref<any[]>([])
const selectedData = ref<any[]>([])
const carryoverPage = ref(1)
const carryoverPageSize = 20
const carryoverTotal = ref(0)
const totalQuantitySum = ref(0)
const carryoverSearched = ref(false)
const carryoverTableRef = ref<any>(null)
const syncingTableSelection = ref(false)
const selectAllLoading = ref(false)

// 筛选参数
const filterParams = reactive({
  month: '',
  process_cd: '',
})

// 工程选项
const processOptions = ref<Array<{ value: string; label: string; name: string }>>([])
const processLoading = ref(false)

// 排序状态管理
const sortConfig = ref({
  prop: '',
  order: '' as 'ascending' | 'descending' | '',
})

// 工程別サマリー・一括繰越
const summary = ref<CarryoverSummaryPayload | null>(null)
const summaryLoading = ref(false)
const bulkDialogVisible = ref(false)
const bulkLoading = ref(false)
const bulkResult = ref<CarryoverExecuteAllResult | null>(null)
const skipExisting = ref(true)

const summaryTotals = computed(() => {
  const list = summary.value?.processes ?? []
  return list.reduce(
    (acc, p) => ({
      count: acc.count + p.count,
      qty: acc.qty + p.total_quantity,
      carried: acc.carried + p.carried_count,
    }),
    { count: 0, qty: 0, carried: 0 },
  )
})

const summaryPendingCount = computed(() =>
  (summary.value?.processes ?? []).reduce(
    (s, p) => s + Math.max(p.count - p.carried_count, 0),
    0,
  ),
)

const currentProcessLabel = computed(() => {
  const opt = processOptions.value.find((o) => o.value === filterParams.process_cd)
  return opt ? opt.label : filterParams.process_cd
})

const pillStyle = (c: ColorToken) => ({
  color: c.color,
  background: c.bg,
  borderColor: c.border,
})

const ITEM_PILL_COLORS: Record<string, ColorToken> = {
  材料: { color: '#d97706', bg: '#d9770614', border: '#d9770640' },
  部品: { color: '#059669', bg: '#05966914', border: '#05966940' },
  製品: { color: '#4f46e5', bg: '#4f46e514', border: '#4f46e540' },
}
const itemPillStyle = (item: string) =>
  pillStyle(ITEM_PILL_COLORS[item] ?? { color: '#64748b', bg: '#64748b14', border: '#64748b40' })

const getStatus = (p: CarryoverProcessSummary) => {
  if (p.count === 0) return { key: 'none', label: '対象なし' }
  if (p.carried_count >= p.count) return { key: 'done', label: '繰越済' }
  if (p.carried_count > 0) return { key: 'partial', label: '一部繰越' }
  return { key: 'pending', label: '未繰越' }
}

const getCarriedRatio = (p: CarryoverProcessSummary) =>
  p.count > 0 ? Math.min(100, Math.round((p.carried_count / p.count) * 100)) : 0

// 加载工程数据
const loadProcessOptions = async () => {
  processLoading.value = true
  try {
    const response = await fetchProcesses({
      page: 1,
      pageSize: 1000, // 获取所有工程数据
    })

    if (response && response.list && Array.isArray(response.list)) {
      processOptions.value = response.list.map((process: any) => ({
        value: process.process_cd,
        name: process.process_name,
        label: `${process.process_cd} - ${process.process_name}`,
      }))
    } else {
      console.error('工程データ取得エラー:', response)
      ElMessage.error('工程データの取得に失敗しました')
    }
  } catch (error) {
    console.error('工程データ取得エラー:', error)
    ElMessage.error('工程データの取得に失敗しました')
  } finally {
    processLoading.value = false
  }
}

const loadSummary = async () => {
  if (!filterParams.month) {
    summary.value = null
    return
  }
  summaryLoading.value = true
  try {
    summary.value = await getCarryoverSummary(filterParams.month)
  } catch (error) {
    console.error('サマリー取得エラー:', error)
    summary.value = null
    ElMessage.error('工程別サマリーの取得に失敗しました')
  } finally {
    summaryLoading.value = false
  }
}

// 格式化数字
const formatNumber = (num: number) => {
  return num?.toLocaleString() || '0'
}

// 自定义排序处理
const handleCustomSort = (prop: string) => {
  if (sortConfig.value.prop === prop) {
    // 如果点击的是当前排序列，切换排序顺序
    if (sortConfig.value.order === 'ascending') {
      sortConfig.value.order = 'descending'
    } else if (sortConfig.value.order === 'descending') {
      sortConfig.value.order = ''
      sortConfig.value.prop = ''
    } else {
      sortConfig.value.order = 'ascending'
    }
  } else {
    // 如果点击的是新列，设置为升序
    sortConfig.value.prop = prop
    sortConfig.value.order = 'ascending'
  }

  // 对当前数据进行排序
  if (sortConfig.value.prop && sortConfig.value.order) {
    inventoryData.value.sort((a: any, b: any) => {
      const aVal = a[sortConfig.value.prop] || ''
      const bVal = b[sortConfig.value.prop] || ''

      if (sortConfig.value.order === 'ascending') {
        return aVal.localeCompare(bVal, 'ja')
      } else {
        return bVal.localeCompare(aVal, 'ja')
      }
    })
  } else {
    // 重置为原始顺序（可以重新搜索来恢复原始顺序）
    if (filterParams.month && filterParams.process_cd) {
      handleSearch()
    }
  }
}

const resetDetail = () => {
  inventoryData.value = []
  selectedData.value = []
  carryoverPage.value = 1
  carryoverTotal.value = 0
  totalQuantitySum.value = 0
  carryoverSearched.value = false
}

// 清除筛选条件
const clearFilters = () => {
  filterParams.month = ''
  filterParams.process_cd = ''
  summary.value = null
  resetDetail()
}

// 月・工程の変更で自動検索
const handleMonthChange = async () => {
  if (!filterParams.month) {
    summary.value = null
    resetDetail()
    return
  }
  loadSummary()
  if (filterParams.process_cd) await handleSearch()
}

const handleProcessChange = async () => {
  if (!filterParams.process_cd) {
    resetDetail()
    return
  }
  if (filterParams.month) await handleSearch()
}

const selectProcessFromTile = async (processCd: string) => {
  filterParams.process_cd = processCd
  await handleSearch()
}

/** 検索条件に一致する全行を API で取得（ページングを跨ぐ） */
const fetchAllFilteredRows = async () => {
  const out: any[] = []
  let page = 1
  const size = 500
  while (true) {
    const payload = await getCarryoverData({
      month: filterParams.month,
      process_cd: filterParams.process_cd,
      page,
      pageSize: size,
    })
    out.push(...payload.list)
    if (payload.list.length === 0 || out.length >= payload.total) break
    page += 1
  }
  return out
}

const syncTableSelectionFromSelectedData = () => {
  const table = carryoverTableRef.value as any
  if (!table) return
  const selectedCds = new Set(selectedData.value.map((r: any) => r.product_cd))
  syncingTableSelection.value = true
  inventoryData.value.forEach((row: any) => {
    table.toggleRowSelection(row, selectedCds.has(row.product_cd))
  })
  nextTick(() => {
    syncingTableSelection.value = false
  })
}

const loadCarryoverPage = async (page: number, resetSelection = false) => {
  if (!filterParams.month || !filterParams.process_cd) return
  loading.value = true
  try {
    const payload = await getCarryoverData({
      month: filterParams.month,
      process_cd: filterParams.process_cd,
      page,
      pageSize: carryoverPageSize,
    })
    inventoryData.value = payload.list
    carryoverTotal.value = payload.total
    totalQuantitySum.value = payload.total_quantity_sum
    carryoverPage.value = payload.page
    carryoverSearched.value = true
    if (resetSelection) {
      selectedData.value = []
    }
  } catch (error) {
    console.error('データ取得エラー:', error)
    ElMessage.error('データ取得に失敗しました')
  } finally {
    loading.value = false
    await nextTick()
    if (!resetSelection && inventoryData.value.length > 0 && selectedData.value.length > 0) {
      syncTableSelectionFromSelectedData()
    }
  }
}

const handleCarryoverPageChange = (page: number) => {
  loadCarryoverPage(page, false)
}

// 执行搜索
const handleSearch = async () => {
  if (!guardInventoryOperation(canEdit)) return

  if (!filterParams.month || !filterParams.process_cd) {
    ElMessage.warning('月と工程を選択してください')
    return
  }
  carryoverPage.value = 1
  await loadCarryoverPage(1, true)
}

// 全選択：現在の検索条件で取得できる全件を選択
const selectAll = async () => {
  if (!filterParams.month || !filterParams.process_cd) {
    ElMessage.warning('月と工程を選択してください')
    return
  }
  selectAllLoading.value = true
  try {
    const all = await fetchAllFilteredRows()
    selectedData.value = all
    await nextTick()
    syncTableSelectionFromSelectedData()
  } catch (error) {
    console.error('全件取得エラー:', error)
    ElMessage.error('全件取得に失敗しました')
  } finally {
    selectAllLoading.value = false
  }
}

// 全部取消选择
const deselectAll = () => {
  selectedData.value = []
  syncingTableSelection.value = true
  nextTick(() => {
    ;(carryoverTableRef.value as any)?.clearSelection()
    nextTick(() => {
      syncingTableSelection.value = false
    })
  })
}

// 当前页勾选变化时与其它页已选项合并（同一 product_cd 去重）
const handleSelectionChange = (selection: any[]) => {
  if (syncingTableSelection.value) return
  const pageCds = new Set(inventoryData.value.map((r: any) => r.product_cd))
  const kept = selectedData.value.filter((r: any) => !pageCds.has(r.product_cd))
  const map = new Map<string, any>()
  for (const r of kept) {
    if (r?.product_cd) map.set(r.product_cd, r)
  }
  for (const r of selection) {
    if (r?.product_cd) map.set(r.product_cd, r)
  }
  selectedData.value = Array.from(map.values())
}

// 执行繰越
const handleCarryover = async () => {
  if (!guardInventoryOperation(canEdit)) return

  if (selectedData.value.length === 0) {
    ElMessage.warning('繰越するデータを選択してください')
    return
  }

  try {
    await ElMessageBox.confirm(
      `選択された ${selectedData.value.length} 件のデータを ${getNextMonth(filterParams.month)} の期初在庫として繰越しますか？`,
      '繰越確認',
      {
        confirmButtonText: '繰越実行',
        cancelButtonText: 'キャンセル',
        type: 'warning',
      },
    )

    carryoverLoading.value = true

    const response = await executeCarryover({
      month: filterParams.month,
      process_cd: filterParams.process_cd,
      selectedData: selectedData.value,
    })

    // responseは拦截器によって処理され、成功時は直接dataが返される
    if (response && typeof response.successCount === 'number') {
      const skipped = response.skippedCount ?? 0
      let msg = `${response.successCount} 件のデータを繰越しました`
      if (skipped > 0) {
        msg += `（${skipped} 件スキップ：製品CDなしまたは数量0以下）`
      }
      ElMessage.success(msg)
      await Promise.all([handleSearch(), loadSummary()])
    } else {
      console.error('Carryover Response Error:', response)
      ElMessage.error('繰越処理に失敗しました')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('繰越処理エラー:', error)
      ElMessage.error('繰越処理に失敗しました')
    }
  } finally {
    carryoverLoading.value = false
  }
}

// 全工程一括繰越
const openBulkDialog = async () => {
  if (!guardInventoryOperation(canEdit)) return
  if (!filterParams.month) {
    ElMessage.warning('棚卸月を選択してください')
    return
  }
  bulkResult.value = null
  skipExisting.value = true
  await loadSummary()
  if (!summary.value) return
  bulkDialogVisible.value = true
}

const executeBulkCarryover = async () => {
  if (!guardInventoryOperation(canEdit)) return
  bulkLoading.value = true
  try {
    const res = await executeCarryoverAll({
      month: filterParams.month,
      skip_existing: skipExisting.value,
    })
    bulkResult.value = res
    ElMessage.success(`全工程一括繰越が完了しました（${res.successCount.toLocaleString()} 件登録）`)
    const tasks: Promise<unknown>[] = [loadSummary()]
    if (filterParams.process_cd) tasks.push(handleSearch())
    await Promise.all(tasks)
  } catch (error) {
    console.error('一括繰越エラー:', error)
    ElMessage.error('一括繰越に失敗しました')
  } finally {
    bulkLoading.value = false
  }
}

// 获取下个月
const getNextMonth = (month: string) => {
  if (!month) return ''
  const [y, m] = month.split('-').map(Number)
  const ny = m === 12 ? y + 1 : y
  const nm = m === 12 ? 1 : m + 1
  return `${ny}-${String(nm).padStart(2, '0')}`
}

// 刷新历史数据
const refreshHistoryData = () => {
  console.log('履歴データを更新')
}

// 组件挂载
onMounted(() => {
  loadProcessOptions()
})
</script>

<style lang="scss" scoped>
.inventory-carryover-management {
  --icm-surface: rgba(255, 255, 255, 0.94);
  --icm-border: rgba(15, 23, 42, 0.07);
  --icm-text: #0f172a;
  --icm-muted: #64748b;

  position: relative;
  min-height: 100%;
  background: linear-gradient(165deg, #f8fafc 0%, #f1f5f9 50%, #eef2f7 100%);
}

.page-ambient {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background:
    radial-gradient(ellipse 60% 45% at 8% -8%, rgba(124, 58, 237, 0.1), transparent 60%),
    radial-gradient(ellipse 50% 40% at 95% 10%, rgba(79, 70, 229, 0.1), transparent 55%),
    radial-gradient(ellipse 40% 35% at 60% 110%, rgba(16, 185, 129, 0.06), transparent 60%);
}

.page-shell {
  position: relative;
  z-index: 1;
  width: 100%;
  box-sizing: border-box;
  padding: 12px 14px 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* ===== ヘッダー ===== */
.page-hero {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding: 14px 18px;
  border-radius: 14px;
  color: #fff;
  background: linear-gradient(120deg, #6d28d9 0%, #4f46e5 45%, #0284c7 100%);
  box-shadow: 0 10px 30px -12px rgba(79, 70, 229, 0.55);

  &::after {
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
}

.hero-title {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 700;
  line-height: 1.25;
}

.hero-sub {
  margin: 3px 0 0;
  font-size: 12px;
  opacity: 0.85;
}

.hero-tabs {
  position: relative;
  z-index: 1;
  display: flex;
  gap: 4px;
  padding: 4px;
  border-radius: 11px;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.22);
}

.hero-tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: none;
  border-radius: 8px;
  font: inherit;
  font-size: 12.5px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
  background: transparent;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;

  &:hover {
    color: #fff;
    background: rgba(255, 255, 255, 0.12);
  }

  &.is-active {
    color: #4338ca;
    background: #fff;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.18);
  }
}

.carryover-content,
.history-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* ===== パネル共通 ===== */
.panel {
  background: var(--icm-surface);
  border: 1px solid var(--icm-border);
  border-radius: 12px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  backdrop-filter: blur(10px);
}

.toolbar-panel {
  padding: 10px 14px;
}

.toolbar-line {
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

.toolbar-field {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;

  &--month {
    width: 210px;
  }

  &--process {
    flex: 0 1 300px;
    min-width: 220px;
  }
}

.toolbar-spacer {
  flex: 1;
}

.month-hint {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 12px;
  color: #64748b;
  background: #f1f5f9;
  border: 1px dashed rgba(100, 116, 139, 0.3);

  &.is-ready {
    color: #3730a3;
    background: linear-gradient(135deg, rgba(219, 39, 119, 0.06), rgba(79, 70, 229, 0.08));
    border: 1px solid rgba(79, 70, 229, 0.2);
  }
}

.month-hint-icon {
  font-size: 14px;
  color: #6366f1;
}

.month-hint-arrow {
  font-size: 13px;
  color: #6366f1;
}

.month-hint-chip {
  padding: 1px 8px;
  border-radius: 999px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;

  &--from {
    color: #be185d;
    background: rgba(219, 39, 119, 0.1);
  }

  &--to {
    color: #047857;
    background: rgba(16, 185, 129, 0.12);
  }
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

  &--month {
    background: #db2777;
  }

  &--process {
    background: #2563eb;
  }
}

.field-control {
  flex: 1 1 auto;
  min-width: 0;
  width: auto !important;

  :deep(.el-input__wrapper),
  :deep(.el-select__wrapper) {
    border-radius: 8px;
    min-height: 32px;
  }
}

.opt-dot {
  flex-shrink: 0;
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.btn-bulk {
  height: 34px;
  padding: 0 16px;
  border: none;
  border-radius: 9px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, #7c3aed, #4f46e5);
  box-shadow: 0 6px 16px -6px rgba(79, 70, 229, 0.6);
  transition: filter 0.15s ease, transform 0.15s ease;

  &:hover:not(.is-disabled),
  &:focus:not(.is-disabled) {
    color: #fff;
    background: linear-gradient(135deg, #7c3aed, #4f46e5);
    filter: brightness(1.08);
    transform: translateY(-1px);
  }

  &.is-disabled,
  &.is-disabled:hover {
    color: #94a3b8;
    background: #e2e8f0;
    box-shadow: none;
  }
}

.btn-bulk-count {
  margin-left: 8px;
  padding: 0 7px;
  border-radius: 999px;
  font-size: 11px;
  line-height: 18px;
  color: #4f46e5;
  background: #fff;
}

/* ===== 工程別サマリー ===== */
.summary-panel {
  padding: 12px 14px 14px;
}

.summary-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}

.summary-title {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 14px;
  font-weight: 700;
  color: var(--icm-text);
}

.summary-title-bar {
  width: 4px;
  height: 16px;
  border-radius: 2px;
  background: linear-gradient(180deg, #7c3aed, #4f46e5);
}

.summary-date {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  color: #475569;
  background: #f1f5f9;
}

.summary-stats {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.stat-pill {
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.4;
  border: 1px solid transparent;
  font-variant-numeric: tabular-nums;

  &--indigo {
    color: #4338ca;
    background: rgba(79, 70, 229, 0.1);
    border-color: rgba(79, 70, 229, 0.22);
  }

  &--emerald {
    color: #047857;
    background: rgba(16, 185, 129, 0.1);
    border-color: rgba(16, 185, 129, 0.25);
  }

  &--slate {
    color: #475569;
    background: rgba(100, 116, 139, 0.1);
    border-color: rgba(100, 116, 139, 0.22);
  }
}

.process-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
  gap: 10px;
}

.process-tile {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 12px;
  text-align: left;
  font: inherit;
  cursor: pointer;
  border-radius: 11px;
  border: 1px solid var(--icm-border);
  background: #fff;
  overflow: hidden;
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease,
    border-color 0.18s ease;

  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    right: 0;
    height: 3px;
    background: var(--accent);
  }

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 22px -12px color-mix(in srgb, var(--accent) 60%, transparent);
  }

  &.is-active {
    border-color: color-mix(in srgb, var(--accent) 50%, transparent);
    background: linear-gradient(160deg, color-mix(in srgb, var(--accent) 8%, #fff), #fff 70%);
    box-shadow: 0 10px 22px -12px color-mix(in srgb, var(--accent) 65%, transparent);
  }

  &.is-empty {
    opacity: 0.6;
  }
}

.tile-head {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.tile-dot {
  flex-shrink: 0;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent);
}

.tile-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  font-weight: 700;
  color: var(--icm-text);
}

.tile-status {
  flex-shrink: 0;
  padding: 0 7px;
  border-radius: 999px;
  font-size: 10.5px;
  font-weight: 700;
  line-height: 18px;

  &--pending {
    color: #4338ca;
    background: rgba(79, 70, 229, 0.12);
  }

  &--partial {
    color: #b45309;
    background: rgba(245, 158, 11, 0.15);
  }

  &--done {
    color: #047857;
    background: rgba(16, 185, 129, 0.14);
  }

  &--none {
    color: #64748b;
    background: rgba(100, 116, 139, 0.12);
  }
}

.tile-metrics {
  display: flex;
  align-items: baseline;
  gap: 14px;
}

.tile-metric {
  display: inline-flex;
  align-items: baseline;
  gap: 5px;
}

.tile-metric-key {
  font-size: 11px;
  font-weight: 600;
  color: var(--icm-muted);
}

.tile-metric-val {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--icm-text);
  font-variant-numeric: tabular-nums;

  &--qty {
    color: var(--accent);
  }
}

.tile-progress {
  height: 4px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.06);
  overflow: hidden;
}

.tile-progress-bar {
  display: block;
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #10b981, #059669);
  transition: width 0.3s ease;
}

.tile-foot {
  display: flex;
  justify-content: space-between;
  font-size: 10.5px;
  color: #94a3b8;
  font-variant-numeric: tabular-nums;
}

/* ===== 明細 ===== */
.data-panel {
  padding: 12px 14px;
}

.data-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}

.data-title {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;

  h3 {
    margin: 0;
    font-size: 14px;
    font-weight: 700;
    color: var(--icm-text);
  }
}

.data-title-bar {
  width: 4px;
  height: 16px;
  border-radius: 2px;
  background: var(--accent);
}

.process-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  color: var(--accent);
  background: color-mix(in srgb, var(--accent) 10%, transparent);
  border: 1px solid color-mix(in srgb, var(--accent) 28%, transparent);
}

.process-chip-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
}

.data-count {
  padding: 2px 9px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  color: #fff;
  background: #334155;
}

.data-selected {
  padding: 2px 9px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  color: #047857;
  background: rgba(16, 185, 129, 0.12);
}

.data-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;

  .el-button + .el-button {
    margin-left: 0;
  }
}

.btn-carryover {
  border: none;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, #10b981, #059669);
  box-shadow: 0 4px 12px -4px rgba(5, 150, 105, 0.55);

  &:hover:not(.is-disabled),
  &:focus:not(.is-disabled) {
    color: #fff;
    background: linear-gradient(135deg, #10b981, #059669);
    filter: brightness(1.06);
  }

  &.is-disabled,
  &.is-disabled:hover {
    color: #94a3b8;
    background: #e2e8f0;
    box-shadow: none;
  }
}

.data-table {
  --el-table-row-hover-bg-color: rgba(79, 70, 229, 0.05);
  --el-table-border-color: rgba(15, 23, 42, 0.06);
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid rgba(15, 23, 42, 0.08);

  :deep(.el-table__header th.el-table__cell) {
    background: linear-gradient(180deg, #f8fafc, #f1f5f9) !important;
    color: #475569;
    font-weight: 700;
    font-size: 11.5px;
    padding: 8px 6px;
  }

  :deep(.el-table__row--striped td.el-table__cell) {
    background: #fafbfd;
  }

  :deep(.el-table__cell) {
    padding: 6px 6px;
    font-size: 12px;
  }
}

.sortable-header {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  user-select: none;
}

.sort-icon {
  font-size: 12px;
  color: #94a3b8;

  &.sort-asc {
    color: #059669;
  }

  &.sort-desc {
    color: #dc2626;
  }
}

.product-code {
  font-family: ui-monospace, 'Cascadia Code', monospace;
  font-size: 11.5px;
  font-weight: 600;
  color: #3730a3;
  background: #eef2ff;
  padding: 1px 6px;
  border-radius: 5px;
}

.product-name {
  font-weight: 500;
  color: var(--icm-text);
}

.color-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 1px 8px;
  border-radius: 999px;
  border: 1px solid transparent;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.6;
  white-space: nowrap;
}

.pill-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.quantity-value {
  display: inline-block;
  min-width: 56px;
  padding: 1px 8px;
  border-radius: 6px;
  font-weight: 700;
  color: #047857;
  background: rgba(16, 185, 129, 0.1);
  font-variant-numeric: tabular-nums;
}

.unit-value {
  padding: 1px 6px;
  border-radius: 5px;
  font-size: 11px;
  font-weight: 600;
  color: var(--icm-muted);
  background: #f1f5f9;
}

.location-tag {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 1px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  color: #0369a1;
  background: rgba(14, 165, 233, 0.1);
}

.table-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;

  :deep(.el-pagination) {
    --el-color-primary: #4f46e5;
  }
}

.sum-row {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  border-radius: 8px;
  background: rgba(16, 185, 129, 0.08);
}

.sum-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--icm-muted);
}

.sum-value {
  font-size: 15px;
  font-weight: 700;
  color: #047857;
  font-variant-numeric: tabular-nums;
}

/* ===== 空・ガイド ===== */
.empty-panel {
  padding: 16px;
}

.guide-panel {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 20px;
  border-style: dashed;
  border-color: rgba(79, 70, 229, 0.25);
  background: linear-gradient(135deg, rgba(238, 242, 255, 0.8), rgba(255, 255, 255, 0.9));
}

.guide-icon {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  color: #4f46e5;
  background: rgba(79, 70, 229, 0.12);
}

.guide-text {
  h3 {
    margin: 0 0 4px;
    font-size: 14px;
    font-weight: 700;
    color: var(--icm-text);
  }

  p {
    margin: 0;
    font-size: 12px;
    color: var(--icm-muted);
    line-height: 1.6;
  }
}

/* ===== レスポンシブ ===== */
@media (max-width: 900px) {
  .panel-title {
    border-right: none;
    padding-right: 0;
  }

  .toolbar-spacer {
    display: none;
  }
}

@media (max-width: 768px) {
  .page-shell {
    padding: 8px;
  }

  .toolbar-field,
  .toolbar-field--month,
  .toolbar-field--process {
    flex: 1 1 100%;
    width: auto;
  }

  .data-header {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>

<style lang="scss">
.carryover-option-popper {
  .opt-row {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
  }

  .opt-dot {
    flex-shrink: 0;
    width: 8px;
    height: 8px;
    border-radius: 50%;
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
}

.bulk-dialog {
  border-radius: 14px;
  overflow: hidden;

  .el-dialog__header {
    padding: 14px 18px;
    margin: 0;
    border-bottom: 1px solid rgba(15, 23, 42, 0.06);
  }

  .el-dialog__title {
    font-weight: 700;
  }

  .bulk-banner {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    margin-bottom: 12px;
    border-radius: 10px;
    font-size: 13px;
    color: #3730a3;
    background: linear-gradient(135deg, rgba(124, 58, 237, 0.1), rgba(79, 70, 229, 0.08));
    border: 1px solid rgba(79, 70, 229, 0.2);
  }

  .bulk-table {
    border-radius: 8px;
    border: 1px solid rgba(15, 23, 42, 0.08);
  }

  .bulk-options {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 12px;
  }

  .bulk-total {
    font-size: 12px;
    color: #475569;

    strong {
      color: #4338ca;
    }
  }

  .bulk-result-head {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 8px;
    margin-bottom: 12px;
  }

  .result-card {
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding: 10px 12px;
    border-radius: 10px;
    border: 1px solid transparent;

    &--success {
      color: #047857;
      background: rgba(16, 185, 129, 0.1);
      border-color: rgba(16, 185, 129, 0.25);
    }

    &--qty {
      color: #4338ca;
      background: rgba(79, 70, 229, 0.08);
      border-color: rgba(79, 70, 229, 0.2);
    }

    &--existing {
      color: #b45309;
      background: rgba(245, 158, 11, 0.1);
      border-color: rgba(245, 158, 11, 0.25);
    }

    &--skip {
      color: #475569;
      background: rgba(100, 116, 139, 0.08);
      border-color: rgba(100, 116, 139, 0.2);
    }
  }

  .result-key {
    font-size: 11px;
    font-weight: 600;
    opacity: 0.85;
  }

  .result-val {
    font-size: 1.2rem;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
  }

  .color-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 1px 8px;
    border-radius: 999px;
    border: 1px solid transparent;
    font-size: 11px;
    font-weight: 600;
    line-height: 1.6;
  }

  .pill-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: currentColor;
  }

  .tile-status {
    padding: 0 7px;
    border-radius: 999px;
    font-size: 10.5px;
    font-weight: 700;
    line-height: 18px;

    &--pending {
      color: #4338ca;
      background: rgba(79, 70, 229, 0.12);
    }

    &--partial {
      color: #b45309;
      background: rgba(245, 158, 11, 0.15);
    }

    &--done {
      color: #047857;
      background: rgba(16, 185, 129, 0.14);
    }

    &--none {
      color: #64748b;
      background: rgba(100, 116, 139, 0.12);
    }
  }

  .btn-bulk {
    border: none;
    font-weight: 700;
    color: #fff;
    background: linear-gradient(135deg, #7c3aed, #4f46e5);

    &:hover:not(.is-disabled),
    &:focus:not(.is-disabled) {
      color: #fff;
      background: linear-gradient(135deg, #7c3aed, #4f46e5);
      filter: brightness(1.08);
    }

    &.is-disabled {
      color: #94a3b8;
      background: #e2e8f0;
    }
  }
}
</style>
