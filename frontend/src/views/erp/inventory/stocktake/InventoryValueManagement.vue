<template>
  <div class="inventory-value-management">
    <!-- ページヘッダー -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <div class="header-icon">
            <Operation class="icon" />
          </div>
          <div class="header-text">
            <h1 class="page-title">棚卸金額管理</h1>
            <p class="page-description">在庫金額の照会・分析（実在庫・サマリを自動反映）</p>
          </div>
        </div>
        <div class="header-actions">
          <el-button
            v-if="activeTab === 'material'"
            size="small"
            class="header-action-btn header-action-btn--material"
            @click="openMaterialStockInput"
          >
            <el-icon class="btn-icon"><Printer /></el-icon>
            材料棚卸入力
          </el-button>
          <el-button
            v-if="activeTab === 'component'"
            size="small"
            class="header-action-btn header-action-btn--component"
            @click="openPartStockPrint"
          >
            <el-icon class="btn-icon"><Printer /></el-icon>
            部品棚卸印刷
          </el-button>
          <el-button
            v-if="activeTab === 'product'"
            size="small"
            class="header-action-btn header-action-btn--product-count"
            @click="openProductCountDialog"
          >
            <el-icon class="btn-icon"><Printer /></el-icon>
            製品本数棚卸
          </el-button>
          <el-button
            v-if="activeTab === 'product'"
            size="small"
            class="header-action-btn header-action-btn--product-amount"
            @click="openProductAmountDialog"
          >
            <el-icon class="btn-icon"><Printer /></el-icon>
            製品金額棚卸
          </el-button>
          <el-button
            size="small"
            class="header-action-btn header-action-btn--report"
            @click="openMonthlyReport"
          >
            <el-icon class="btn-icon"><Document /></el-icon>
            棚卸報告書
          </el-button>
          <el-button size="small" class="header-action-btn header-action-btn--bom" @click="goToBom">
            <span class="header-action-btn__dot header-action-btn__dot--bom" aria-hidden="true" />
            BOM管理
          </el-button>
          <el-button size="small" class="header-action-btn header-action-btn--cost" @click="goToUnitPrice">
            <span class="header-action-btn__dot header-action-btn__dot--cost" aria-hidden="true" />
            原価管理
          </el-button>
          <el-badge :value="visibleErrors.length" :hidden="visibleErrors.length === 0" class="error-badge">
            <el-button
              size="small"
              :loading="errorsLoading"
              class="header-action-btn header-action-btn--alert"
              @click="openErrorDialog"
            >
              <el-icon class="btn-icon"><WarningFilled /></el-icon>
              設定不備
            </el-button>
          </el-badge>
        </div>
      </div>
    </div>

    <!-- 期間・集計範囲・製品絞込 -->
    <div class="filter-container">
      <div class="filter-row filter-row--main">
        <div class="filter-period-inline">
          <span class="filter-inline-label">期間選択</span>
          <el-date-picker
            v-model="selectedMonth"
            type="month"
            size="small"
            placeholder="月を選択"
            format="YYYY-MM"
            value-format="YYYY-MM"
            class="date-picker"
            @change="handleMonthChange"
          />
          <el-input
            class="range-input"
            size="small"
            :readonly="true"
            :model-value="dateRangeDisplay"
            placeholder="対象月を選択"
          />
        </div>
        <el-select
          v-model="filterProductCd"
          class="product-filter-select"
          size="small"
          filterable
          clearable
          placeholder="製品で絞込"
        >
          <el-option
            v-for="opt in productFilterOptions"
            :key="opt.value"
            :label="opt.label"
            :value="opt.value"
          />
        </el-select>
        <div class="filter-actions">
          <el-button type="primary" size="small" :loading="loading" class="search-btn" @click="searchData">
            <Search class="btn-icon" />
            検索
          </el-button>
          <el-button size="small" class="clear-btn" @click="clearFilters">
            <RefreshLeft class="btn-icon" />
            クリア
          </el-button>
        </div>
      </div>
    </div>

    <!-- 金額 KPI（合計・製品は API；材料・部品は stock-panel 金額合計を優先） -->
    <div class="kpi-strip">
      <div class="kpi-grid">
        <div class="kpi-tile kpi-tile--total">
          <div class="kpi-tile__glow" aria-hidden="true" />
          <div class="kpi-tile__body">
            <span class="kpi-tile__tag">合計</span>
            <div class="kpi-tile__value">
              ¥{{ formatNumber(statistics.total?.total_amount || 0) }}
            </div>
            <p class="kpi-tile__desc">棚卸金額合計</p>
          </div>
        </div>
        <div class="kpi-tile kpi-tile--material">
          <div class="kpi-tile__glow" aria-hidden="true" />
          <div class="kpi-tile__body">
            <span class="kpi-tile__tag">材料</span>
            <div class="kpi-tile__value">
              ¥{{ formatNumber(displayMaterialKpiAmount) }}
            </div>
            <p class="kpi-tile__desc">材料金額</p>
          </div>
        </div>
        <div class="kpi-tile kpi-tile--component">
          <div class="kpi-tile__glow" aria-hidden="true" />
          <div class="kpi-tile__body">
            <span class="kpi-tile__tag">部品</span>
            <div class="kpi-tile__value">
              ¥{{ formatNumber(displayComponentKpiAmount) }}
            </div>
            <p class="kpi-tile__desc">部品金額</p>
          </div>
        </div>
        <div class="kpi-tile kpi-tile--product">
          <div class="kpi-tile__glow" aria-hidden="true" />
          <div class="kpi-tile__body">
            <span class="kpi-tile__tag">製品</span>
            <div class="kpi-tile__value">
              ¥{{ formatNumber(statistics.total?.stay_amount || 0) }}
            </div>
            <p class="kpi-tile__desc">製品金額</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 材料 / 部品 / 製品タブ -->
    <div class="content-tabs">
      <el-card class="tab-card" shadow="never">
        <el-tabs v-model="activeTab" type="card" class="custom-tabs">
          <el-tab-pane name="material">
            <template #label>
              <span class="iv-tab-label">
                <el-icon class="iv-tab-label__icon" aria-hidden="true"><Box /></el-icon>
                <span class="iv-tab-label__text">材料</span>
              </span>
            </template>
            <InventoryValueTable
              ref="materialTableRef"
              :date-range="dateRange"
              :product-cd-filter="filterProductCd"
              item-type="材料"
              @data-updated="onMaterialStockDataUpdated"
            />
          </el-tab-pane>

          <el-tab-pane name="component">
            <template #label>
              <span class="iv-tab-label">
                <el-icon class="iv-tab-label__icon" aria-hidden="true"><Files /></el-icon>
                <span class="iv-tab-label__text">部品</span>
              </span>
            </template>
            <InventoryValueTable
              ref="componentTableRef"
              :date-range="dateRange"
              :product-cd-filter="filterProductCd"
              item-type="部品"
              @data-updated="onComponentStockDataUpdated"
            />
          </el-tab-pane>

          <el-tab-pane name="product">
            <template #label>
              <span class="iv-tab-label">
                <el-icon class="iv-tab-label__icon" aria-hidden="true"><Goods /></el-icon>
                <span class="iv-tab-label__text">製品</span>
              </span>
            </template>
            <InventoryValueTable
              ref="productTableRef"
              :date-range="dateRange"
              :product-cd-filter="filterProductCd"
              item-type="製品"
            />
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>

    <el-dialog
      v-model="showErrorDialog"
      width="min(96vw, 920px)"
      class="error-dialog"
      align-center
      destroy-on-close
      :close-on-click-modal="false"
    >
      <template #header>
        <div class="error-dialog__header">
          <div class="error-dialog__header-row">
            <span class="error-dialog__title">未定価・設定不備一覧</span>
            <span v-if="visibleErrors.length" class="error-dialog__count">{{ visibleErrors.length }}件</span>
          </div>
          <p class="error-dialog__hint">計算バッチで検出されたルート・単価・マスタ関連の不備です。</p>
        </div>
      </template>
      <div v-loading="errorsLoading" class="error-dialog-body">
        <el-table
          v-if="visibleErrors.length"
          class="error-table"
          :data="visibleErrors"
          size="small"
          :max-height="errorTableMaxHeight"
          border
          stripe
        >
          <el-table-column label="分類" width="108" align="center">
            <template #default="{ row }">
              <el-tag :type="errorTagType(row.error_code)" size="small" effect="light">
                {{ errorLabel(row.error_code) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="product_cd" label="製品コード" width="108" show-overflow-tooltip />
          <el-table-column prop="product_name" label="製品名" min-width="128" show-overflow-tooltip>
            <template #default="{ row }">
              {{ row.product_name || '—' }}
            </template>
          </el-table-column>
          <el-table-column prop="process_cd" label="工程コード" width="88" show-overflow-tooltip>
            <template #default="{ row }">
              {{ row.process_cd || '—' }}
            </template>
          </el-table-column>
          <el-table-column prop="process_name" label="工程名" min-width="100" show-overflow-tooltip>
            <template #default="{ row }">
              {{ row.process_name || '—' }}
            </template>
          </el-table-column>
          <el-table-column prop="error_message" label="詳細" min-width="220" show-overflow-tooltip />
        </el-table>
        <el-empty
          v-else
          class="error-empty"
          :description="errorEmptyDescription"
          :image-size="72"
        />
      </div>
      <template #footer>
        <div class="error-dialog__footer">
          <el-button type="primary" plain @click="showErrorDialog = false">閉じる</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog
      v-model="showProductCountDialog"
      width="min(96vw, 1180px)"
      class="product-count-dialog"
      align-center
      destroy-on-close
      :close-on-click-modal="false"
    >
      <template #header>
        <div class="product-count-dialog__header">
          <div class="product-count-dialog__header-row">
            <span class="product-count-dialog__title">製品本数棚卸一覧</span>
            <span v-if="productCountAsOf" class="product-count-dialog__date-chip">対象日 {{ productCountAsOf }}</span>
            <span v-if="hasNegativeProductCount" class="product-count-dialog__alert-chip">
              負数データあり（{{ negativeProductCountCells }}件）
            </span>
          </div>
          <p class="product-count-dialog__hint">製品CD・製品名と各工程の在庫数量（本数）を一覧表示します。</p>
          <div class="product-count-dialog__merge-controls">
            <el-date-picker
              v-model="shipmentDate"
              type="date"
              size="small"
              value-format="YYYY-MM-DD"
              placeholder="出荷日を選択"
              class="product-count-dialog__date-select"
              @change="onShipmentControlChange"
            />
            <el-select
              v-model="shipmentDestCds"
              placeholder="納入先を選択（複数可）"
              size="small"
              filterable
              multiple
              collapse-tags
              collapse-tags-tooltip
              clearable
              class="product-count-dialog__dest-select"
              @change="onShipmentControlChange"
            >
              <el-option
                v-for="d in destinationList"
                :key="d.destination_cd"
                :label="`${d.destination_cd} - ${d.destination_name}`"
                :value="d.destination_cd"
              />
            </el-select>
            <el-switch
              v-model="shipmentMergeEnabled"
              size="small"
              active-text="出荷数並入"
              :disabled="!shipmentDate || !shipmentDestCds.length"
              @change="onShipmentControlChange"
            />
            <span v-if="shipmentMergeEnabled && shipmentDestCds.length" class="product-count-dialog__merge-hint">
              {{ shipmentDate }}・{{ shipmentDestCds.length }}納入先の出荷数を倉庫に加算中
            </span>
          </div>
        </div>
      </template>
      <div v-loading="productCountLoading || shipmentLoading" class="product-count-dialog__body">
        <el-table
          v-if="displayProductCountRows.length"
          class="product-count-table"
          :data="displayProductCountRows"
          size="small"
          :max-height="productCountTableMaxHeight"
          border
          stripe
          show-summary
          :summary-method="productCountSummaryMethod"
        >
          <el-table-column prop="product_cd" label="製品CD" width="110" fixed="left" show-overflow-tooltip />
          <el-table-column prop="product_name" label="製品名" width="150" fixed="left" show-overflow-tooltip />
          <el-table-column prop="kind" label="分類" width="84" fixed="left" align="center" show-overflow-tooltip>
            <template #default="{ row }">
              {{ row.kind || '—' }}
            </template>
          </el-table-column>
          <el-table-column
            v-for="proc in productCountProcesses"
            :key="proc.process_cd"
            :label="proc.process_name"
            :prop="`qty_${proc.process_cd}`"
            width="92"
            align="right"
          >
            <template #default="{ row }">
              {{ formatNumber(row[`qty_${proc.process_cd}`] as number, 0) }}
            </template>
          </el-table-column>
        </el-table>
        <div v-if="displayProductCountRows.length" class="product-count-summary-strip">
          <span>製品数 <strong>{{ formatNumber(displayProductCountRows.length, 0) }}</strong></span>
          <span>製品合計 <strong>{{ formatNumber(productCountGrandTotal, 0) }}</strong></span>
        </div>
        <el-empty
          v-if="!displayProductCountRows.length && !productCountLoading && !shipmentLoading"
          class="product-count-empty"
          description="表示対象の製品データがありません。"
          :image-size="72"
        />
      </div>
      <template #footer>
        <div class="product-count-dialog__footer">
          <el-button size="small" @click="showProductCountDialog = false">閉じる</el-button>
          <div class="product-count-dialog__actions">
            <el-switch
              v-model="printIncludeKindCount"
              size="small"
              active-text="分類を印刷"
              inactive-text="通常印刷"
            />
            <el-button
              type="success"
              size="small"
              plain
              :disabled="productCountLoading || shipmentLoading || !displayProductCountRows.length"
              @click="exportProductCountData"
            >
              エクスポート
            </el-button>
            <el-button
              type="primary"
              size="small"
              :disabled="productCountLoading || shipmentLoading || !displayProductCountRows.length"
              @click="printProductCountData"
            >
              印刷
            </el-button>
          </div>
        </div>
      </template>
    </el-dialog>

    <!-- 棚卸金額報告書（月次） -->
    <el-dialog
      v-model="showMonthlyReportDialog"
      width="min(96vw, 1180px)"
      class="monthly-report-dialog"
      align-center
      destroy-on-close
      :close-on-click-modal="false"
    >
      <template #header>
        <div class="monthly-report-dialog__header">
          <div class="monthly-report-dialog__header-row">
            <span class="monthly-report-dialog__title">棚卸統合報告書</span>
            <span v-if="monthlyReportData?.meta" class="product-count-dialog__date-chip">
              {{ monthlyReportData.meta.month_label }} ({{ monthlyReportData.meta.as_of }})
            </span>
          </div>
          <p class="product-count-dialog__hint">
            総括・分類別の製品本数・金額に、出荷確定本数を並入して再集計できます（部品集計は対象外）。
          </p>
          <div class="product-count-dialog__merge-controls">
            <el-date-picker
              v-model="monthlyReportShipmentDate"
              type="date"
              size="small"
              value-format="YYYY-MM-DD"
              placeholder="出荷日を選択"
              class="product-count-dialog__date-select"
              @change="onMonthlyReportShipmentControlChange"
            />
            <el-select
              v-model="monthlyReportShipmentDestCds"
              placeholder="納入先を選択（複数可）"
              size="small"
              filterable
              multiple
              collapse-tags
              collapse-tags-tooltip
              clearable
              class="product-count-dialog__dest-select"
              @change="onMonthlyReportShipmentControlChange"
            >
              <el-option
                v-for="d in destinationList"
                :key="d.destination_cd"
                :label="`${d.destination_cd} - ${d.destination_name}`"
                :value="d.destination_cd"
              />
            </el-select>
            <el-switch
              v-model="monthlyReportShipmentMergeEnabled"
              size="small"
              active-text="出荷数並入"
              :disabled="!monthlyReportShipmentDate || !monthlyReportShipmentDestCds.length"
              @change="onMonthlyReportShipmentControlChange"
            />
            <span
              v-if="monthlyReportShipmentMergeEnabled && monthlyReportShipmentDestCds.length"
              class="product-count-dialog__merge-hint"
            >
              {{ monthlyReportShipmentDate }}・{{ monthlyReportShipmentDestCds.length }}納入先の出荷を製品側に加算中
            </span>
          </div>
        </div>
      </template>
      <div v-loading="monthlyReportLoading" class="monthly-report-dialog__body">
        <MonthlyInventoryReportPrint
          v-if="monthlyReportData"
          ref="monthlyReportRef"
          :data="monthlyReportData"
        />
        <el-empty
          v-if="!monthlyReportData && !monthlyReportLoading"
          description="報告書データがありません。"
          :image-size="72"
        />
      </div>
      <template #footer>
        <div class="product-count-dialog__footer">
          <el-button size="small" @click="showMonthlyReportDialog = false">閉じる</el-button>
          <el-button
            type="primary"
            size="small"
            :disabled="monthlyReportLoading || !monthlyReportData"
            @click="printMonthlyReport"
          >
            印刷
          </el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog
      v-model="showProductAmountDialog"
      width="min(96vw, 1180px)"
      class="product-count-dialog"
      align-center
      destroy-on-close
      :close-on-click-modal="false"
    >
      <template #header>
        <div class="product-count-dialog__header">
          <div class="product-count-dialog__header-row">
            <span class="product-count-dialog__title">製品金額棚卸一覧</span>
            <span v-if="productAmountAsOf" class="product-count-dialog__date-chip">対象日 {{ productAmountAsOf }}</span>
          </div>
          <p class="product-count-dialog__hint">製品CD・製品名と各工程の在庫金額（数量×単価）を一覧表示します。</p>
          <div class="product-count-dialog__merge-controls">
            <el-date-picker
              v-model="shipmentAmountDate"
              type="date"
              size="small"
              value-format="YYYY-MM-DD"
              placeholder="出荷日を選択"
              class="product-count-dialog__date-select"
              @change="onShipmentAmountControlChange"
            />
            <el-select
              v-model="shipmentAmountDestCds"
              placeholder="納入先を選択（複数可）"
              size="small"
              filterable
              multiple
              collapse-tags
              collapse-tags-tooltip
              clearable
              class="product-count-dialog__dest-select"
              @change="onShipmentAmountControlChange"
            >
              <el-option
                v-for="d in destinationList"
                :key="d.destination_cd"
                :label="`${d.destination_cd} - ${d.destination_name}`"
                :value="d.destination_cd"
              />
            </el-select>
            <el-switch
              v-model="shipmentAmountMergeEnabled"
              size="small"
              active-text="出荷数並入"
              :disabled="!shipmentAmountDate || !shipmentAmountDestCds.length"
              @change="onShipmentAmountControlChange"
            />
            <span v-if="shipmentAmountMergeEnabled && shipmentAmountDestCds.length" class="product-count-dialog__merge-hint">
              {{ shipmentAmountDate }}・{{ shipmentAmountDestCds.length }}納入先の出荷金額を倉庫に加算中
            </span>
          </div>
        </div>
      </template>
      <div v-loading="productAmountLoading || shipmentAmountLoading" class="product-count-dialog__body">
        <el-table
          v-if="displayProductAmountRows.length"
          class="product-count-table"
          :data="displayProductAmountRows"
          size="small"
          :max-height="productCountTableMaxHeight"
          border
          stripe
          show-summary
          :summary-method="productAmountSummaryMethod"
        >
          <el-table-column prop="product_cd" label="製品CD" width="110" fixed="left" show-overflow-tooltip />
          <el-table-column prop="product_name" label="製品名" width="150" fixed="left" show-overflow-tooltip />
          <el-table-column prop="kind" label="分類" width="84" fixed="left" align="center" show-overflow-tooltip>
            <template #default="{ row }">
              {{ row.kind || '—' }}
            </template>
          </el-table-column>
          <el-table-column
            v-for="proc in productAmountProcesses"
            :key="proc.process_cd"
            :label="proc.process_name"
            :prop="`amt_${proc.process_cd}`"
            width="108"
            align="right"
          >
            <template #default="{ row }">
              {{ formatNumber(row[`amt_${proc.process_cd}`] as number, 0) }}
            </template>
          </el-table-column>
        </el-table>
        <div v-if="displayProductAmountRows.length" class="product-count-summary-strip">
          <span>製品数 <strong>{{ formatNumber(displayProductAmountRows.length, 0) }}</strong></span>
          <span>製品合計 <strong>{{ formatNumber(productAmountGrandTotal, 0) }}</strong></span>
        </div>
        <el-empty
          v-if="!displayProductAmountRows.length && !productAmountLoading && !shipmentAmountLoading"
          class="product-count-empty"
          description="表示対象の製品データがありません。"
          :image-size="72"
        />
      </div>
      <template #footer>
        <div class="product-count-dialog__footer">
          <el-button size="small" @click="showProductAmountDialog = false">閉じる</el-button>
          <div class="product-count-dialog__actions">
            <el-switch
              v-model="printIncludeKindAmount"
              size="small"
              active-text="分類を印刷"
              inactive-text="通常印刷"
            />
            <el-button
              type="success"
              size="small"
              plain
              :disabled="productAmountLoading || shipmentAmountLoading || !displayProductAmountRows.length"
              @click="exportProductAmountData"
            >
              エクスポート
            </el-button>
            <el-button
              type="primary"
              size="small"
              :disabled="productAmountLoading || shipmentAmountLoading || !displayProductAmountRows.length"
              @click="printProductAmountData"
            >
              印刷
            </el-button>
          </div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as XLSX from 'xlsx'
import { useRouter } from 'vue-router'
import {
  Operation,
  Search,
  RefreshLeft,
  WarningFilled,
  Printer,
  Box,
  Files,
  Goods,
  Document,
} from '@element-plus/icons-vue'
import { inventoryValueApi, type InventoryValueParams, type MonthlyInventoryReportData } from '@/api/inventoryValue'
import { getProductList } from '@/api/master/productMaster'
import InventoryValueTable from './components/InventoryValueTable.vue'
import MonthlyInventoryReportPrint from './components/MonthlyInventoryReportPrint.vue'

const router = useRouter()

interface StatisticsData {
  total: {
    total_amount: number
    material_amount: number
    component_amount: number
    stay_amount: number
  }
  byType: any[]
  byProcess: any[]
}

interface CalcError {
  product_cd: string
  product_name?: string | null
  process_cd: string | null
  process_name?: string | null
  item_type: string | null
  error_code: string
  error_message: string
}

interface ProductCountProcess {
  process_cd: string
  process_name: string
  source_codes: string[]
}

interface ProductCountRow {
  product_cd: string
  product_name: string
  kind?: string
  [key: string]: string | number | undefined
}

interface ProductAmountRow {
  product_cd: string
  product_name: string
  kind?: string
  [key: string]: string | number | undefined
}

const loading = ref(false)
const activeTab = ref('material')

const materialTableRef = ref()
const componentTableRef = ref()
const productTableRef = ref()

const dateRange = ref<string[]>([])
const selectedMonth = ref('')
/** 製品マスタに基づく CD 絞込（材料／部品／製品タブの stock-panel に渡す） */
const filterProductCd = ref('')
const productFilterOptions = ref<{ value: string; label: string }[]>([])

const dateRangeDisplay = computed(() => {
  if (dateRange.value?.length === 2) {
    return `集計範囲: ${dateRange.value[0]} ～ ${dateRange.value[1]}`
  }
  return ''
})
const errors = ref<CalcError[]>([])
const showErrorDialog = ref(false)
const errorsLoading = ref(false)
const showProductCountDialog = ref(false)
const productCountLoading = ref(false)
const baseProductCountRows = ref<ProductCountRow[]>([])
const productCountProcesses = ref<ProductCountProcess[]>([])
const productCountAsOf = ref('')
const showProductAmountDialog = ref(false)
const productAmountLoading = ref(false)
const baseProductAmountRows = ref<ProductAmountRow[]>([])
const productAmountProcesses = ref<ProductCountProcess[]>([])
const productAmountAsOf = ref('')
const printIncludeKindCount = ref(false)
const printIncludeKindAmount = ref(false)
const shipmentAmountDate = ref('')
const shipmentAmountDestCds = ref<string[]>([])
const shipmentAmountMergeEnabled = ref(false)
const shipmentAmountLoading = ref(false)
const shipmentAmountByProductCd = ref<Record<string, number>>({})

interface DestinationItem {
  destination_cd: string
  destination_name: string
}
const destinationList = ref<DestinationItem[]>([])
/** 出荷数並入の納入先初期選択（製品棚卸・統合報告書で共通） */
const DEFAULT_SHIPMENT_DEST_CDS = [
  'N12', 'N13', 'N17', 'N18', 'N20', 'N21',
  'N24', 'N30', 'N36', 'N38', 'N39', 'N42',
  'N43', 'N44', 'N48', 'N50',
]
const shipmentDate = ref('')
const shipmentDestCds = ref<string[]>([])
const shipmentMergeEnabled = ref(false)
const shipmentLoading = ref(false)
const shipmentByProductCd = ref<Record<string, number>>({})

const displayProductCountRows = computed<ProductCountRow[]>(() => {
  const base = baseProductCountRows.value
  if (!shipmentMergeEnabled.value || !shipmentDate.value || !shipmentDestCds.value.length) {
    return applyZeroFilter(base)
  }
  const shipMap = shipmentByProductCd.value
  const merged = base.map((row) => {
    const cd = String(row.product_cd ?? '').trim()
    const shipQty = shipMap[cd] ?? 0
    if (shipQty === 0) return row
    const newRow = { ...row }
    newRow.qty_all = (Number(row.qty_all) || 0) + shipQty
    newRow.qty_PRODUCT_TOTAL =
      (Number(newRow.qty_KT09) || 0) + (Number(newRow.qty_all) || 0) + (Number(newRow.qty_KT10) || 0)
    return newRow
  })
  return applyZeroFilter(merged)
})

const displayProductAmountRows = computed<ProductAmountRow[]>(() => {
  const base = baseProductAmountRows.value
  if (!shipmentAmountMergeEnabled.value || !shipmentAmountDate.value || !shipmentAmountDestCds.value.length) {
    return applyZeroAmountFilter(base)
  }
  const shipMap = shipmentAmountByProductCd.value
  const merged = base.map((row) => {
    const cd = String(row.product_cd ?? '').trim()
    const shipQty = shipMap[cd] ?? 0
    if (shipQty === 0) return row
    const newRow = { ...row }
    const upAll = Number(row.up_all) || 0
    newRow.amt_all = (Number(row.amt_all) || 0) + shipQty * upAll
    newRow.amt_PRODUCT_TOTAL =
      (Number(newRow.amt_KT09) || 0) + (Number(newRow.amt_all) || 0) + (Number(newRow.amt_KT10) || 0)
    return newRow
  })
  return applyZeroAmountFilter(merged)
})

function applyZeroFilter(rows: ProductCountRow[]): ProductCountRow[] {
  return rows.filter((row) => {
    const wip = Number(row.qty_WIP_TOTAL) || 0
    const warehouse = Number(row.qty_all) || 0
    const outsourcedWarehouse = Number(row.qty_KT10) || 0
    return !(wip === 0 && warehouse === 0 && outsourcedWarehouse === 0)
  })
}

function applyZeroAmountFilter(rows: ProductAmountRow[]): ProductAmountRow[] {
  return rows.filter((row) => {
    const wip = Number(row.amt_WIP_TOTAL) || 0
    const warehouse = Number(row.amt_all) || 0
    const outsourcedWarehouse = Number(row.amt_KT10) || 0
    return !(wip === 0 && warehouse === 0 && outsourcedWarehouse === 0)
  })
}

function groupRowsByKind<T extends { kind?: string; product_name?: string; product_cd?: string }>(rows: T[]) {
  const groups = new Map<string, T[]>()
  for (const row of rows) {
    const key = String(row.kind ?? '').trim() || '—'
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key)!.push(row)
  }
  return [...groups.entries()]
    .sort((a, b) => a[0].localeCompare(b[0], 'ja', { sensitivity: 'base' }))
    .map(([kind, list]) => ({
      kind,
      rows: [...list].sort((a, b) =>
        String(a.product_name ?? a.product_cd ?? '').localeCompare(
          String(b.product_name ?? b.product_cd ?? ''),
          'ja',
          { sensitivity: 'base' },
        ),
      ),
    }))
}

const errorEmptyDescription =
  '計算バッチで検出された不備はありません。本画面は実在庫データを表示します。単価・BOM・工程の設定は原価管理・BOM管理からご確認ください。'

const statistics = ref<StatisticsData>({
  total: {
    total_amount: 0,
    material_amount: 0,
    component_amount: 0,
    stay_amount: 0,
  },
  byType: [],
  byProcess: [],
})

/** 材料タブ：material_stock の金額列合計（stock-panel の sum_total_value）。未取得時は null */
const materialStockPanelSum = ref<number | null>(null)
/** 部品タブ：part_stock の金額合計（stock-panel の sum_total_value）。未取得時は null */
const componentStockPanelSum = ref<number | null>(null)

const displayMaterialKpiAmount = computed(() => {
  if (materialStockPanelSum.value !== null && !Number.isNaN(materialStockPanelSum.value)) {
    return materialStockPanelSum.value
  }
  return statistics.value.total.material_amount ?? 0
})

const displayComponentKpiAmount = computed(() => {
  if (componentStockPanelSum.value !== null && !Number.isNaN(componentStockPanelSum.value)) {
    return componentStockPanelSum.value
  }
  return statistics.value.total.component_amount ?? 0
})

function onMaterialStockDataUpdated(payload: { total?: number; data?: unknown[]; sumTotalValue?: number }) {
  if (typeof payload.sumTotalValue === 'number' && !Number.isNaN(payload.sumTotalValue)) {
    materialStockPanelSum.value = payload.sumTotalValue
  } else {
    materialStockPanelSum.value = null
  }
}

function onComponentStockDataUpdated(payload: { total?: number; data?: unknown[]; sumTotalValue?: number }) {
  if (typeof payload.sumTotalValue === 'number' && !Number.isNaN(payload.sumTotalValue)) {
    componentStockPanelSum.value = payload.sumTotalValue
  } else {
    componentStockPanelSum.value = null
  }
}

const currentDateRange = computed(() => {
  if (dateRange.value && dateRange.value.length === 2) {
    return {
      startDate: dateRange.value[0],
      endDate: dateRange.value[1],
    }
  }
  return { startDate: '', endDate: '' }
})

const formatNumber = (value: number | string | undefined, decimals = 0): string => {
  if (!value && value !== 0) return '0'
  return Number(value).toLocaleString('ja-JP', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

const errorTagType = (code: string) => {
  if (code === 'NO_ROUTE') return 'danger'
  if (code === 'NO_STEP' || code === 'NO_PART') return 'warning'
  return 'info'
}

const errorLabel = (code: string) => {
  const map: Record<string, string> = {
    NO_ROUTE: 'ルート未設定',
    NO_STEP: 'ステップ不明',
    NO_PRICE: '単価未設定',
    NO_PART: '部品マスタなし',
  }
  return map[code] || code
}

/** 一覧に出さない行：KT18／製品名に「加工」「アーチ」を含むもの */
function shouldShowInventoryErrorRow(row: CalcError): boolean {
  if (String(row.process_cd ?? '').trim().toUpperCase() === 'KT18') return false
  const name = String(row.product_name ?? '')
  if (name.includes('加工') || name.includes('アーチ')) return false
  return true
}

const visibleErrors = computed(() => errors.value.filter(shouldShowInventoryErrorRow))

const errorTableMaxHeight = computed(() => {
  if (typeof window === 'undefined') return 400
  return Math.min(Math.round(window.innerHeight * 0.46), 432)
})

const productCountTableMaxHeight = computed(() => {
  if (typeof window === 'undefined') return 460
  return Math.min(Math.round(window.innerHeight * 0.56), 560)
})

const productCountColumnTotals = computed<Record<string, number>>(() => {
  const totals: Record<string, number> = {}
  for (const proc of productCountProcesses.value) {
    const key = `qty_${proc.process_cd}`
    totals[key] = displayProductCountRows.value.reduce((sum, row) => sum + (Number(row[key]) || 0), 0)
  }
  return totals
})

const productCountGrandTotal = computed(() => {
  const totals = productCountColumnTotals.value
  return (Number(totals.qty_WIP_TOTAL) || 0) + (Number(totals.qty_PRODUCT_TOTAL) || 0)
})

const negativeProductCountCells = computed(() => {
  let count = 0
  for (const row of displayProductCountRows.value) {
    for (const proc of productCountProcesses.value) {
      const key = `qty_${proc.process_cd}`
      if ((Number(row[key]) || 0) < 0) count += 1
    }
  }
  return count
})

const hasNegativeProductCount = computed(() => negativeProductCountCells.value > 0)

const productAmountColumnTotals = computed<Record<string, number>>(() => {
  const totals: Record<string, number> = {}
  for (const proc of productAmountProcesses.value) {
    const key = `amt_${proc.process_cd}`
    totals[key] = displayProductAmountRows.value.reduce((sum, row) => sum + (Number(row[key]) || 0), 0)
  }
  return totals
})

const productAmountGrandTotal = computed(() => {
  const totals = productAmountColumnTotals.value
  return (Number(totals.amt_WIP_TOTAL) || 0) + (Number(totals.amt_PRODUCT_TOTAL) || 0)
})

function productAmountSummaryMethod(param: { columns: Array<{ property?: string }>; data: ProductAmountRow[] }) {
  const { columns, data } = param
  return columns.map((col, idx) => {
    if (idx === 0) return '合計'
    if (idx === 1) return `${formatNumber(data.length, 0)}品目`
    const prop = String(col.property ?? '')
    if (prop.startsWith('amt_')) {
      return formatNumber(productAmountColumnTotals.value[prop] ?? 0, 0)
    }
    return ''
  })
}

function productCountSummaryMethod(param: { columns: Array<{ property?: string }>; data: ProductCountRow[] }) {
  const { columns, data } = param
  return columns.map((col, idx) => {
    if (idx === 0) return '合計'
    if (idx === 1) return `${formatNumber(data.length, 0)}品目`
    const prop = String(col.property ?? '')
    if (prop.startsWith('qty_')) {
      return formatNumber(productCountColumnTotals.value[prop] ?? 0, 0)
    }
    return ''
  })
}

const PRODUCT_COUNT_PROCESS_SPECS: ProductCountProcess[] = [
  { process_cd: 'KT01', process_name: '切断', source_codes: ['KT01'] },
  { process_cd: 'KT02', process_name: '面取', source_codes: ['KT02'] },
  { process_cd: 'KT04', process_name: '成型', source_codes: ['KT04'] },
  { process_cd: 'KT05', process_name: 'メッキ', source_codes: ['KT05'] },
  { process_cd: 'KT06', process_name: '外注メッキ', source_codes: ['KT06', 'KT16'] },
  { process_cd: 'KT07', process_name: '溶接', source_codes: ['KT07'] },
  { process_cd: 'KT08', process_name: '外注溶接', source_codes: ['KT08', 'KT17'] },
  { process_cd: 'KT11', process_name: '溶接前検査', source_codes: ['KT11'] },
  { process_cd: 'WIP_TOTAL', process_name: '仕掛品合計', source_codes: [] },
  { process_cd: 'KT09', process_name: '検査', source_codes: ['KT09'] },
  { process_cd: 'all', process_name: '倉庫', source_codes: ['all'] },
  { process_cd: 'KT10', process_name: '外注倉庫', source_codes: ['KT10', 'KT15'] },
  { process_cd: 'PRODUCT_TOTAL', process_name: '製品合計', source_codes: [] },
]

const PRODUCT_COUNT_WIP_SOURCE_CODES = ['KT01', 'KT02', 'KT04', 'KT05', 'KT06', 'KT07', 'KT08', 'KT11'] as const

function escapeHtml(text: unknown): string {
  return String(text ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

const pad2 = (value: number): string => String(value).padStart(2, '0')

const toDateString = (value: Date): string => {
  const y = value.getFullYear()
  const m = pad2(value.getMonth() + 1)
  const d = pad2(value.getDate())
  return `${y}-${m}-${d}`
}

const getMonthRange = (month: string): [string, string] => {
  const [yearText, monthText] = month.split('-')
  const year = Number(yearText)
  const monthIndex = Number(monthText) - 1
  if (!year || monthIndex < 0 || monthIndex > 11) {
    return ['', '']
  }
  const firstDay = new Date(year, monthIndex, 1)
  const lastDay = new Date(year, monthIndex + 1, 0)
  return [toDateString(firstDay), toDateString(lastDay)]
}

const loadStatistics = async () => {
  try {
    const params: InventoryValueParams = {
      ...currentDateRange.value,
    }
    const response = await inventoryValueApi.getInventoryValueSummary(params)
    const raw = response.data as Partial<StatisticsData> | undefined
    if (raw?.total) {
      statistics.value = {
        total: {
          total_amount: Number(raw.total.total_amount) || 0,
          material_amount: Number(raw.total.material_amount) || 0,
          component_amount: Number(raw.total.component_amount) || 0,
          stay_amount: Number(raw.total.stay_amount) || 0,
        },
        byType: raw.byType ?? [],
        byProcess: raw.byProcess ?? [],
      }
    } else {
      statistics.value = {
        total: {
          total_amount: 0,
          material_amount: 0,
          component_amount: 0,
          stay_amount: 0,
        },
        byType: [],
        byProcess: [],
      }
    }
  } catch (error) {
    console.error('統計データ取得失敗:', error)
  }
}

const loadErrors = async () => {
  try {
    const response = await inventoryValueApi.getErrors()
    errors.value = ((response as any)?.data ?? []) as CalcError[]
  } catch {
    errors.value = []
  }
}

/** 設定不備：クリック時に最新のエラー一覧を取得してから表示 */
async function openErrorDialog() {
  errorsLoading.value = true
  try {
    await loadErrors()
    showErrorDialog.value = true
  } finally {
    errorsLoading.value = false
  }
}

const handleMonthChange = (value?: string) => {
  if (!value) {
    dateRange.value = []
    searchData()
    return
  }
  dateRange.value = getMonthRange(value)
  searchData()
}

const searchData = () => {
  loadStatistics()
  loadErrors()
  refreshCurrentTable()
}

const clearFilters = () => {
  const now = new Date()
  selectedMonth.value = `${now.getFullYear()}-${pad2(now.getMonth() + 1)}`
  dateRange.value = getMonthRange(selectedMonth.value)
  filterProductCd.value = ''
  searchData()
}

async function loadProductFilterOptions() {
  try {
    const res = await getProductList({ page: 1, pageSize: 5000 })
    const raw = res.data?.list ?? res.list ?? []
    const opts: { value: string; label: string }[] = []
    for (const row of raw as { product_cd?: string; product_name?: string }[]) {
      const cd = String(row.product_cd ?? '').trim()
      if (!cd) continue
      const name = String(row.product_name ?? '').trim()
      opts.push({
        value: cd,
        label: name ? `${cd} ${name}` : cd,
      })
    }
    opts.sort((a, b) => a.value.localeCompare(b.value, 'ja', { sensitivity: 'base' }))
    productFilterOptions.value = opts
  } catch {
    productFilterOptions.value = []
  }
}

const refreshCurrentTable = () => {
  /** 材料・部品 KPI は各タブの stock-panel 金額合計のため、常に再取得 */
  materialTableRef.value?.refreshTable()
  componentTableRef.value?.refreshTable()
  if (activeTab.value === 'product') {
    productTableRef.value?.refreshTable()
  }
}

function openMaterialStockInput() {
  const inst = materialTableRef.value as { openMaterialPrintDialog?: () => void | Promise<void> } | undefined
  if (inst?.openMaterialPrintDialog) {
    void inst.openMaterialPrintDialog()
  }
}

function openPartStockPrint() {
  const inst = componentTableRef.value as { openPartPrintDialog?: () => void | Promise<void> } | undefined
  if (inst?.openPartPrintDialog) {
    void inst.openPartPrintDialog()
  }
}

async function loadDestinations() {
  if (destinationList.value.length) return
  try {
    const res = await inventoryValueApi.getDestinations()
    destinationList.value = res.data.list ?? []
  } catch {
    destinationList.value = []
  }
}

async function fetchShipmentUnits() {
  if (!shipmentDate.value || !shipmentDestCds.value.length) {
    shipmentByProductCd.value = {}
    return
  }
  shipmentLoading.value = true
  try {
    const res = await inventoryValueApi.getShipmentUnits({
      date: shipmentDate.value,
      destination_cds: shipmentDestCds.value,
    })
    const map: Record<string, number> = {}
    for (const item of res.data.list) {
      const cd = String(item.product_cd ?? '').trim()
      if (cd) map[cd] = (map[cd] ?? 0) + (Number(item.confirmed_units_sum) || 0)
    }
    shipmentByProductCd.value = map
  } catch {
    shipmentByProductCd.value = {}
  } finally {
    shipmentLoading.value = false
  }
}

async function onShipmentControlChange() {
  if (!shipmentDate.value || !shipmentDestCds.value.length) {
    if (shipmentMergeEnabled.value) {
      shipmentMergeEnabled.value = false
      ElMessage.warning('出荷日と納入先を選択してからスイッチをONにしてください')
    }
    shipmentByProductCd.value = {}
    return
  }
  if (!shipmentMergeEnabled.value) return
  await fetchShipmentUnits()
}

async function fetchShipmentAmountUnits() {
  if (!shipmentAmountDate.value || !shipmentAmountDestCds.value.length) {
    shipmentAmountByProductCd.value = {}
    return
  }
  shipmentAmountLoading.value = true
  try {
    const res = await inventoryValueApi.getShipmentUnits({
      date: shipmentAmountDate.value,
      destination_cds: shipmentAmountDestCds.value,
    })
    const map: Record<string, number> = {}
    for (const item of res.data.list) {
      const cd = String(item.product_cd ?? '').trim()
      if (cd) map[cd] = (map[cd] ?? 0) + (Number(item.confirmed_units_sum) || 0)
    }
    shipmentAmountByProductCd.value = map
  } catch {
    shipmentAmountByProductCd.value = {}
  } finally {
    shipmentAmountLoading.value = false
  }
}

async function onShipmentAmountControlChange() {
  if (!shipmentAmountDate.value || !shipmentAmountDestCds.value.length) {
    if (shipmentAmountMergeEnabled.value) {
      shipmentAmountMergeEnabled.value = false
      ElMessage.warning('出荷日と納入先を選択してからスイッチをONにしてください')
    }
    shipmentAmountByProductCd.value = {}
    return
  }
  if (!shipmentAmountMergeEnabled.value) return
  await fetchShipmentAmountUnits()
}

async function openProductCountDialog() {
  const endDate = dateRange.value?.[1]
  if (!endDate) {
    ElMessage.warning('対象月（月末日）を選択してください')
    return
  }
  showProductCountDialog.value = true
  productCountLoading.value = true
  baseProductCountRows.value = []
  shipmentByProductCd.value = {}
  shipmentMergeEnabled.value = false
  shipmentDate.value = String(endDate).slice(0, 10)
  productCountAsOf.value = String(endDate).slice(0, 10)
  await loadDestinations()
  shipmentDestCds.value = [...DEFAULT_SHIPMENT_DEST_CDS]
  try {
    productCountProcesses.value = PRODUCT_COUNT_PROCESS_SPECS

    const results = await Promise.all(
      productCountProcesses.value.map(async (proc) => {
        const merged: any[] = []
        if (!proc.source_codes.length) return { proc, list: merged }
        for (const sourceCode of proc.source_codes) {
          let page = 1
          const limit = 500
          let total = 0
          for (let guard = 0; guard < 500; guard += 1) {
            const resp = await inventoryValueApi.getStockPanel({
              tab: 'product',
              as_of: productCountAsOf.value,
              process_cd: sourceCode === 'all' ? undefined : sourceCode,
              page,
              limit,
              sort_by: 'product_cd',
              sort_order: 'asc',
            })
            const inner = (resp as { data?: { list?: any[]; total?: number } })?.data ?? {}
            let list = (inner.list ?? []).filter((r: any) => String(r.product_cd ?? '').trim().length > 0)
            // 倉庫列は production_summarys.warehouse_inventory のみを対象とする
            if (sourceCode === 'all') {
              list = list.filter((r: any) => String(r.inventory_column ?? '') === 'warehouse_inventory')
            }
            total = Number(inner.total ?? 0)
            merged.push(...list)
            if (!(inner.list ?? []).length || (inner.list ?? []).length < limit || merged.length >= total) break
            page += 1
          }
        }
        return { proc, list: merged }
      }),
    )

    const byProduct = new Map<string, ProductCountRow>()
    for (const { proc, list } of results) {
      for (const r of list) {
        const cd = String(r.product_cd ?? '').trim()
        if (!cd) continue
        const name = String(r.product_name ?? '').trim() || cd
        const kind = String(r.kind ?? '').trim() || undefined
        if (!byProduct.has(cd)) {
          byProduct.set(cd, { product_cd: cd, product_name: name, kind })
        }
        const row = byProduct.get(cd)!
        if (!row.kind && kind) row.kind = kind
        const qtyKey = `qty_${proc.process_cd}`
        row[qtyKey] = (Number(row[qtyKey] ?? 0) || 0) + (Number(r.quantity) || 0)
      }
    }

    const rows = [...byProduct.values()].sort((a, b) => {
      const na = String(a.product_name ?? '').trim()
      const nb = String(b.product_name ?? '').trim()
      const byName = na.localeCompare(nb, 'ja', { sensitivity: 'base' })
      if (byName !== 0) return byName
      return String(a.product_cd).localeCompare(String(b.product_cd), 'ja', { sensitivity: 'base' })
    })
    for (const row of rows) {
      for (const proc of productCountProcesses.value) {
        const qtyKey = `qty_${proc.process_cd}`
        row[qtyKey] = Number(row[qtyKey] ?? 0)
      }
      row.qty_WIP_TOTAL = PRODUCT_COUNT_WIP_SOURCE_CODES.reduce(
        (sum, code) => sum + (Number(row[`qty_${code}`]) || 0),
        0,
      )
      row.qty_PRODUCT_TOTAL =
        (Number(row.qty_KT09) || 0) + (Number(row.qty_all) || 0) + (Number(row.qty_KT10) || 0)
    }
    baseProductCountRows.value = rows
    if (!displayProductCountRows.value.length) ElMessage.info('この条件ではデータがありません')
  } catch (e) {
    console.error(e)
    ElMessage.error('製品本数棚卸データの取得に失敗しました')
    showProductCountDialog.value = false
  } finally {
    productCountLoading.value = false
  }
}

async function openProductAmountDialog() {
  const endDate = dateRange.value?.[1]
  if (!endDate) {
    ElMessage.warning('対象月（月末日）を選択してください')
    return
  }
  showProductAmountDialog.value = true
  productAmountLoading.value = true
  baseProductAmountRows.value = []
  shipmentAmountByProductCd.value = {}
  shipmentAmountMergeEnabled.value = false
  shipmentAmountDate.value = String(endDate).slice(0, 10)
  productAmountAsOf.value = String(endDate).slice(0, 10)
  await loadDestinations()
  shipmentAmountDestCds.value = [...DEFAULT_SHIPMENT_DEST_CDS]
  try {
    productAmountProcesses.value = PRODUCT_COUNT_PROCESS_SPECS
    const results = await Promise.all(
      productAmountProcesses.value.map(async (proc) => {
        const merged: any[] = []
        if (!proc.source_codes.length) return { proc, list: merged }
        for (const sourceCode of proc.source_codes) {
          let page = 1
          const limit = 500
          let total = 0
          for (let guard = 0; guard < 500; guard += 1) {
            const resp = await inventoryValueApi.getStockPanel({
              tab: 'product',
              as_of: productAmountAsOf.value,
              process_cd: sourceCode === 'all' ? undefined : sourceCode,
              page,
              limit,
              sort_by: 'product_cd',
              sort_order: 'asc',
            })
            const inner = (resp as { data?: { list?: any[]; total?: number } })?.data ?? {}
            let list = (inner.list ?? []).filter((r: any) => String(r.product_cd ?? '').trim().length > 0)
            // 倉庫列は production_summarys.warehouse_inventory のみを対象とする
            if (sourceCode === 'all') {
              list = list.filter((r: any) => String(r.inventory_column ?? '') === 'warehouse_inventory')
            }
            total = Number(inner.total ?? 0)
            merged.push(...list)
            if (!(inner.list ?? []).length || (inner.list ?? []).length < limit || merged.length >= total) break
            page += 1
          }
        }
        return { proc, list: merged }
      }),
    )

    const byProduct = new Map<string, ProductAmountRow>()
    for (const { proc, list } of results) {
      for (const r of list) {
        const cd = String(r.product_cd ?? '').trim()
        if (!cd) continue
        const name = String(r.product_name ?? '').trim() || cd
        const kind = String(r.kind ?? '').trim() || undefined
        if (!byProduct.has(cd)) byProduct.set(cd, { product_cd: cd, product_name: name, kind })
        const row = byProduct.get(cd)!
        if (!row.kind && kind) row.kind = kind
        const amtKey = `amt_${proc.process_cd}`
        const amount =
          Number(r.total_value) || ((Number(r.quantity) || 0) * (Number(r.unit_price) || 0))
        row[amtKey] = (Number(row[amtKey] ?? 0) || 0) + amount
        if (proc.process_cd === 'all') {
          row.up_all = Number(r.unit_price) || Number(row.up_all) || 0
        }
      }
    }

    const rows = [...byProduct.values()].sort((a, b) => {
      const na = String(a.product_name ?? '').trim()
      const nb = String(b.product_name ?? '').trim()
      const byName = na.localeCompare(nb, 'ja', { sensitivity: 'base' })
      if (byName !== 0) return byName
      return String(a.product_cd).localeCompare(String(b.product_cd), 'ja', { sensitivity: 'base' })
    })
    for (const row of rows) {
      for (const proc of productAmountProcesses.value) {
        const amtKey = `amt_${proc.process_cd}`
        row[amtKey] = Number(row[amtKey] ?? 0)
      }
      row.amt_WIP_TOTAL = PRODUCT_COUNT_WIP_SOURCE_CODES.reduce(
        (sum, code) => sum + (Number(row[`amt_${code}`]) || 0),
        0,
      )
      row.amt_PRODUCT_TOTAL =
        (Number(row.amt_KT09) || 0) + (Number(row.amt_all) || 0) + (Number(row.amt_KT10) || 0)
    }
    baseProductAmountRows.value = rows
    if (!displayProductAmountRows.value.length) ElMessage.info('この条件ではデータがありません')
  } catch (e) {
    console.error(e)
    ElMessage.error('製品金額棚卸データの取得に失敗しました')
    showProductAmountDialog.value = false
  } finally {
    productAmountLoading.value = false
  }
}

function buildProductCountPrintHtml(): string {
  const rows = displayProductCountRows.value
  const asOf = escapeHtml(productCountAsOf.value)
  const mergeLabel = shipmentMergeEnabled.value && shipmentDate.value && shipmentDestCds.value.length
    ? `　※ 出荷数並入（${escapeHtml(shipmentDate.value)} / ${escapeHtml(shipmentDestCds.value.join(', '))}）`
    : ''
  const headerCells = productCountProcesses.value
    .map((p) => `<th>${escapeHtml(p.process_name)}</th>`)
    .join('')
  const bodyRows = rows
    .map((row) => {
      const qtyCells = productCountProcesses.value
        .map((p) => `<td class="num">${formatNumber(Number(row[`qty_${p.process_cd}`] ?? 0), 0)}</td>`)
        .join('')
      return `<tr><td>${escapeHtml(row.product_name)}</td>${qtyCells}</tr>`
    })
    .join('')
  const totalCells = productCountProcesses.value
    .map((p) => {
      const total = rows.reduce(
        (sum, row) => sum + (Number(row[`qty_${p.process_cd}`] ?? 0) || 0),
        0,
      )
      return `<td class="num total-cell">${formatNumber(total, 0)}</td>`
    })
    .join('')
  const totalRow = `<tr class="total-row"><td class="total-label">合計</td>${totalCells}</tr>`
  return `<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8" /><title>製品本数棚卸</title><style>
    @page { size: A4 landscape; margin: 8mm; }
    * { box-sizing: border-box; }
    body { margin: 0; font-family: 'Yu Gothic UI','Meiryo',sans-serif; font-size: 11px; color: #1f2937; }
    .page { padding: 8px; }
    h1 { margin: 0 0 4px; font-size: 16px; }
    .meta { margin: 0 0 8px; color: #64748b; }
    table { width: 100%; border-collapse: collapse; table-layout: fixed; }
    th, td { border: 1px solid #cbd5e1; padding: 4px 6px; }
    thead th { background: #f1f5f9; font-weight: 700; text-align: center; }
    td { overflow-wrap: anywhere; }
    td.num { text-align: right; font-variant-numeric: tabular-nums; }
    tbody tr:nth-child(even) { background: #f8fafc; }
    tr.total-row td {
      background: linear-gradient(180deg, #eff6ff, #dbeafe) !important;
      color: #1e3a8a;
      font-weight: 800;
    }
    td.total-label { text-align: left; }
    .kind-title { margin: 10px 0 6px; color: #334155; font-weight: 700; font-size: 12px; }
    .group-block:first-of-type .kind-title { margin-top: 0; }
    td.total-cell { font-variant-numeric: tabular-nums; }
  </style></head><body><div class="page"><h1>製品本数棚卸</h1><p class="meta">対象日: ${asOf}${mergeLabel}</p>
  ${
    printIncludeKindCount.value
      ? groupRowsByKind(rows).map((grp) => {
          const grpBody = grp.rows
            .map((row) => {
              const qtyCells = productCountProcesses.value
                .map((p) => `<td class="num">${formatNumber(Number(row[`qty_${p.process_cd}`] ?? 0), 0)}</td>`)
                .join('')
              return `<tr><td>${escapeHtml(row.product_name)}</td>${qtyCells}</tr>`
            })
            .join('')
          const grpTotals = productCountProcesses.value
            .map((p) => {
              const v = grp.rows.reduce(
                (sum, row) => sum + (Number(row[`qty_${p.process_cd}`] ?? 0) || 0),
                0,
              )
              return `<td class="num total-cell">${formatNumber(v, 0)}</td>`
            })
            .join('')
          return `<div class="group-block"><div class="kind-title">分類：${escapeHtml(grp.kind)}</div><table><thead><tr><th style="width:150px">製品名</th>${headerCells}</tr></thead><tbody>${grpBody}<tr class="total-row"><td class="total-label">合計</td>${grpTotals}</tr></tbody></table></div>`
        }).join('')
      : `<table><thead><tr><th style="width:150px">製品名</th>${headerCells}</tr></thead><tbody>${bodyRows}${totalRow}</tbody></table>`
  }
  </div></body></html>`
}

function buildProductAmountPrintHtml(): string {
  const rows = displayProductAmountRows.value
  const asOf = escapeHtml(productAmountAsOf.value)
  const mergeLabel = shipmentAmountMergeEnabled.value && shipmentAmountDate.value && shipmentAmountDestCds.value.length
    ? `　※ 出荷数並入（${escapeHtml(shipmentAmountDate.value)} / ${escapeHtml(shipmentAmountDestCds.value.join(', '))}）`
    : ''
  const headerCells = productAmountProcesses.value.map((p) => `<th>${escapeHtml(p.process_name)}</th>`).join('')
  const bodyRows = rows
    .map((row) => {
      const amtCells = productAmountProcesses.value
        .map((p) => `<td class="num">${formatNumber(Number(row[`amt_${p.process_cd}`] ?? 0), 0)}</td>`)
        .join('')
      return `<tr><td>${escapeHtml(row.product_name)}</td>${amtCells}</tr>`
    })
    .join('')
  const totalCells = productAmountProcesses.value
    .map((p) => `<td class="num total-cell">${formatNumber(productAmountColumnTotals.value[`amt_${p.process_cd}`] ?? 0, 0)}</td>`)
    .join('')
  const totalRow = `<tr class="total-row"><td class="total-label">合計</td>${totalCells}</tr>`
  return `<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8" /><title>製品金額棚卸</title><style>
    @page { size: A4 landscape; margin: 8mm; }
    * { box-sizing: border-box; }
    body { margin: 0; font-family: 'Yu Gothic UI','Meiryo',sans-serif; font-size: 11px; color: #1f2937; }
    .page { padding: 8px; }
    h1 { margin: 0 0 4px; font-size: 16px; }
    .meta { margin: 0 0 8px; color: #64748b; }
    table { width: 100%; border-collapse: collapse; table-layout: fixed; }
    th, td { border: 1px solid #cbd5e1; padding: 4px 6px; }
    thead th { background: #f1f5f9; font-weight: 700; text-align: center; }
    td { overflow-wrap: anywhere; }
    td.num { text-align: right; font-variant-numeric: tabular-nums; }
    tbody tr:nth-child(even) { background: #f8fafc; }
    tr.total-row td { background: linear-gradient(180deg, #eff6ff, #dbeafe) !important; color: #1e3a8a; font-weight: 800; }
    .kind-title { margin: 10px 0 6px; color: #334155; font-weight: 700; font-size: 12px; }
    .group-block:first-of-type .kind-title { margin-top: 0; }
  </style></head><body><div class="page"><h1>製品金額棚卸</h1><p class="meta">対象日: ${asOf}${mergeLabel}</p>
  ${
    printIncludeKindAmount.value
      ? groupRowsByKind(rows).map((grp) => {
          const grpBody = grp.rows
            .map((row) => {
              const amtCells = productAmountProcesses.value
                .map((p) => `<td class="num">${formatNumber(Number(row[`amt_${p.process_cd}`] ?? 0), 0)}</td>`)
                .join('')
              return `<tr><td>${escapeHtml(row.product_name)}</td>${amtCells}</tr>`
            })
            .join('')
          const grpTotals = productAmountProcesses.value
            .map((p) => {
              const v = grp.rows.reduce(
                (sum, row) => sum + (Number(row[`amt_${p.process_cd}`] ?? 0) || 0),
                0,
              )
              return `<td class="num total-cell">${formatNumber(v, 0)}</td>`
            })
            .join('')
          return `<div class="group-block"><div class="kind-title">分類：${escapeHtml(grp.kind)}</div><table><thead><tr><th style="width:150px">製品名</th>${headerCells}</tr></thead><tbody>${grpBody}<tr class="total-row"><td class="total-label">合計</td>${grpTotals}</tr></tbody></table></div>`
        }).join('')
      : `<table><thead><tr><th style="width:150px">製品名</th>${headerCells}</tr></thead><tbody>${bodyRows}${totalRow}</tbody></table>`
  }
  </div></body></html>`
}

async function printProductCountData() {
  if (!displayProductCountRows.value.length) return
  const iframe = document.createElement('iframe')
  iframe.style.cssText =
    'position:fixed;left:-12000px;top:0;width:297mm;min-height:210mm;border:0;opacity:0;pointer-events:none'
  document.body.appendChild(iframe)
  const doc = iframe.contentDocument
  if (!doc) {
    iframe.remove()
    ElMessage.error('印刷の準備に失敗しました')
    return
  }
  doc.open()
  doc.write(buildProductCountPrintHtml())
  doc.close()
  await new Promise((r) => setTimeout(r, 220))
  const win = iframe.contentWindow
  const cleanup = () => {
    if (iframe.parentNode) iframe.remove()
  }
  if (!win) {
    cleanup()
    return
  }
  win.addEventListener('afterprint', cleanup, { once: true })
  setTimeout(cleanup, 120_000)
  win.focus()
  win.print()
}

async function printProductAmountData() {
  if (!displayProductAmountRows.value.length) return
  const iframe = document.createElement('iframe')
  iframe.style.cssText =
    'position:fixed;left:-12000px;top:0;width:297mm;min-height:210mm;border:0;opacity:0;pointer-events:none'
  document.body.appendChild(iframe)
  const doc = iframe.contentDocument
  if (!doc) {
    iframe.remove()
    ElMessage.error('印刷の準備に失敗しました')
    return
  }
  doc.open()
  doc.write(buildProductAmountPrintHtml())
  doc.close()
  await new Promise((r) => setTimeout(r, 220))
  const win = iframe.contentWindow
  const cleanup = () => { if (iframe.parentNode) iframe.remove() }
  if (!win) {
    cleanup()
    return
  }
  win.addEventListener('afterprint', cleanup, { once: true })
  setTimeout(cleanup, 120_000)
  win.focus()
  win.print()
}

function exportProductCountData() {
  if (!displayProductCountRows.value.length) {
    ElMessage.warning('エクスポートするデータがありません')
    return
  }
  try {
    const rows = displayProductCountRows.value.map((row) => {
      const out: Record<string, string | number> = {
        製品CD: row.product_cd,
        製品名: row.product_name,
      }
      for (const proc of productCountProcesses.value) {
        out[proc.process_name] = Number(row[`qty_${proc.process_cd}`] ?? 0)
      }
      return out
    })
    const ws = XLSX.utils.json_to_sheet(rows)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, '製品本数棚卸')
    const d = productCountAsOf.value.replace(/[^\d-]/g, '') || 'export'
    XLSX.writeFile(wb, `製品本数棚卸_${d}.xlsx`)
    ElMessage.success('エクスポートしました')
  } catch (e) {
    console.error(e)
    ElMessage.error('エクスポートに失敗しました')
  }
}

function exportProductAmountData() {
  if (!displayProductAmountRows.value.length) {
    ElMessage.warning('エクスポートするデータがありません')
    return
  }
  try {
    const rows = displayProductAmountRows.value.map((row) => {
      const out: Record<string, string | number> = { 製品CD: row.product_cd, 製品名: row.product_name }
      for (const proc of productAmountProcesses.value) {
        out[proc.process_name] = Number(row[`amt_${proc.process_cd}`] ?? 0)
      }
      return out
    })
    const ws = XLSX.utils.json_to_sheet(rows)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, '製品金額棚卸')
    const d = productAmountAsOf.value.replace(/[^\d-]/g, '') || 'export'
    XLSX.writeFile(wb, `製品金額棚卸_${d}.xlsx`)
    ElMessage.success('エクスポートしました')
  } catch (e) {
    console.error(e)
    ElMessage.error('エクスポートに失敗しました')
  }
}

// ---------- 棚卸金額報告書（月次） ----------
const showMonthlyReportDialog = ref(false)
const monthlyReportLoading = ref(false)
const monthlyReportData = ref<MonthlyInventoryReportData | null>(null)
const monthlyReportRef = ref<InstanceType<typeof MonthlyInventoryReportPrint> | null>(null)
const monthlyReportShipmentDate = ref('')
const monthlyReportShipmentDestCds = ref<string[]>([])
const monthlyReportShipmentMergeEnabled = ref(false)

async function fetchMonthlyReportData() {
  const endDate = dateRange.value?.[1]
  if (!endDate) {
    ElMessage.warning('対象月（月末日）を選択してください')
    return
  }
  monthlyReportLoading.value = true
  try {
    const merge =
      monthlyReportShipmentMergeEnabled.value
      && Boolean(monthlyReportShipmentDate.value)
      && monthlyReportShipmentDestCds.value.length > 0
    const res = await inventoryValueApi.getMonthlyInventoryReport({
      as_of: String(endDate).slice(0, 10),
      shipment_merge: merge,
      shipment_date: merge ? monthlyReportShipmentDate.value : undefined,
      destination_cds: merge ? monthlyReportShipmentDestCds.value : undefined,
    })
    if (res.success && res.data) {
      monthlyReportData.value = res.data
    } else {
      ElMessage.error('報告書データの取得に失敗しました')
    }
  } catch {
    ElMessage.error('報告書データの取得に失敗しました')
  } finally {
    monthlyReportLoading.value = false
  }
}

async function onMonthlyReportShipmentControlChange() {
  if (!monthlyReportShipmentDate.value || !monthlyReportShipmentDestCds.value.length) {
    if (monthlyReportShipmentMergeEnabled.value) {
      monthlyReportShipmentMergeEnabled.value = false
      ElMessage.warning('出荷日と納入先を選択してからスイッチをONにしてください')
    }
  }
  await fetchMonthlyReportData()
}

async function openMonthlyReport() {
  const endDate = dateRange.value?.[1]
  if (!endDate) {
    ElMessage.warning('対象月（月末日）を選択してください')
    return
  }
  showMonthlyReportDialog.value = true
  monthlyReportData.value = null
  monthlyReportShipmentMergeEnabled.value = false
  monthlyReportShipmentDate.value = String(endDate).slice(0, 10)
  await loadDestinations()
  monthlyReportShipmentDestCds.value = [...DEFAULT_SHIPMENT_DEST_CDS]
  await fetchMonthlyReportData()
}

function printMonthlyReport() {
  const el = monthlyReportRef.value?.$el as HTMLElement | undefined
  if (!el) return
  const printWindow = window.open('', '_blank')
  if (!printWindow) {
    ElMessage.warning('ポップアップがブロックされました。許可してください。')
    return
  }
  const html = el.innerHTML
  printWindow.document.write(`<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8" />
<title>棚卸統合報告書</title>
<style>
@page { size: A4 portrait; margin: 10mm 8mm; }
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Meiryo', 'Yu Gothic', 'Hiragino Kaku Gothic ProN', sans-serif;
  font-size: 10px;
  color: #0f172a;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
.mir-page {
  width: 100%;
  max-width: 188mm;
  margin: 0 auto;
  padding: 0;
}
.mir-header { text-align: center; margin-bottom: 5px; }
.mir-title { font-size: 16px; font-weight: 700; letter-spacing: 2px; color: #0b3a67; }
.mir-subtitle { font-size: 10px; color: #5f6f85; margin-top: 2px; }
.mir-meta {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 4px 10px;
  font-size: 9px;
  color: #3f4f68;
  margin-bottom: 7px;
  padding: 4px 6px;
  background: #eef5ff;
  border: 1px solid #d6e5f7;
  border-radius: 6px;
}
.mir-section {
  margin-bottom: 7px;
  border: 1px solid #d7e2ef;
  border-radius: 6px;
  overflow: hidden;
  background: #fff;
  page-break-inside: avoid;
}
.mir-section-title {
  font-size: 10px;
  font-weight: 700;
  color: #0c4a7d;
  background: linear-gradient(90deg, #e8f3ff 0%, #f4f9ff 100%);
  padding: 4px 8px;
  border-left: 3px solid #2b79c2;
  border-bottom: 1px solid #d7e2ef;
}
table { width: 100%; border-collapse: collapse; font-size: 10.5px; font-variant-numeric: tabular-nums; }
th, td { border: 1px solid #d8e1ec; padding: 5px 7px; }
th { background: #f3f8fd; font-weight: 600; text-align: center; white-space: nowrap; color: #334155; font-size: 10px; }
td { text-align: right; background: #fff; }
td.left { text-align: left; }
td.center { text-align: center; }
tr.total-row { background: #edf6ff; font-weight: 700; }
tr.total-row td {
  border-top: 2px solid #3d86cc;
  background: #edf6ff;
  color: #0f3f6e;
}
.mir-footer { text-align: right; font-size: 8px; color: #6b7f95; margin-top: 4px; }
</style>
</head>
<body onload="window.print();window.close();">${html}</body>
</html>`)
  printWindow.document.close()
}

const goToBom = () => { router.push('/master/bom/product-bom') }
const goToUnitPrice = () => { router.push('/master/bom/product-unit-price') }

watch(
  () => (dateRange.value?.length === 2 ? `${dateRange.value[0]}|${dateRange.value[1]}` : ''),
  () => {
    materialStockPanelSum.value = null
    componentStockPanelSum.value = null
  },
)

onMounted(() => {
  const now = new Date()
  selectedMonth.value = `${now.getFullYear()}-${pad2(now.getMonth() + 1)}`
  dateRange.value = getMonthRange(selectedMonth.value)
  void loadProductFilterOptions()
  searchData()
})
</script>

<style scoped>
.inventory-value-management {
  --ivm-surface: rgba(255, 255, 255, 0.92);
  --ivm-border: rgba(15, 23, 42, 0.08);
  --ivm-accent: #0ea5e9;
  --ivm-muted: #64748b;
  --kpi-total: #6366f1;
  --kpi-total-deep: #4338ca;
  --kpi-material: #0ea5e9;
  --kpi-material-deep: #0369a1;
  --kpi-component: #10b981;
  --kpi-component-deep: #047857;
  --kpi-product: #f59e0b;
  --kpi-product-deep: #b45309;
  min-height: 100vh;
  background: linear-gradient(165deg, #f8fafc 0%, #f1f5f9 45%, #e8edf3 100%);
  padding: 10px;
  box-sizing: border-box;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.page-header {
  margin-bottom: 8px;
  padding: 10px 14px;
  background: linear-gradient(165deg, rgba(255, 255, 255, 0.96) 0%, rgba(248, 250, 252, 0.92) 100%);
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.85) inset,
    0 6px 22px rgba(15, 23, 42, 0.06);
  backdrop-filter: blur(12px);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-icon {
  width: 32px;
  height: 32px;
  background: linear-gradient(145deg, #0ea5e9, #0284c7);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.25);
  flex-shrink: 0;
}

.header-icon .icon {
  font-size: 16px;
}

.header-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.page-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
  line-height: 1.25;
  letter-spacing: -0.02em;
}

.page-description {
  font-size: 11px;
  color: var(--ivm-muted);
  margin: 0;
  line-height: 1.3;
  font-weight: 500;
}

.header-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  justify-content: flex-end;
}

.header-action-btn {
  font-weight: 700 !important;
  font-size: 12px !important;
  letter-spacing: 0.03em;
  border-radius: 11px !important;
  padding: 8px 16px !important;
  line-height: 1.3 !important;
  border-width: 1px !important;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
  transition:
    transform 0.22s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.28s ease,
    border-color 0.22s ease,
    background 0.22s ease,
    color 0.22s ease !important;
}

.header-action-btn :deep(.el-button__content) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.header-action-btn:hover {
  transform: translateY(-2px);
}

.header-action-btn:active {
  transform: translateY(0);
}

.header-action-btn .btn-icon {
  font-size: 15px;
}

.header-action-btn__dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.header-action-btn__dot--bom {
  background: linear-gradient(135deg, #a5b4fc, #6366f1);
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.22);
}

.header-action-btn__dot--cost {
  background: linear-gradient(135deg, #5eead4, #0d9488);
  box-shadow: 0 0 0 2px rgba(13, 148, 136, 0.2);
}

/* 材料タブ：印刷・入力 */
.header-action-btn--material {
  color: #075985 !important;
  background: linear-gradient(165deg, rgba(255, 255, 255, 0.98), rgba(224, 242, 254, 0.65)) !important;
  border-color: rgba(14, 165, 233, 0.42) !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 4px 14px rgba(14, 165, 233, 0.2);
}

.header-action-btn--material:hover {
  color: #0c4a6e !important;
  border-color: rgba(2, 132, 199, 0.55) !important;
  background: linear-gradient(165deg, #fff, rgba(186, 230, 253, 0.85)) !important;
  box-shadow:
    0 1px 0 #fff inset,
    0 10px 26px rgba(14, 165, 233, 0.28);
}

/* 部品タブ：印刷 */
.header-action-btn--component {
  color: #065f46 !important;
  background: linear-gradient(165deg, rgba(255, 255, 255, 0.98), rgba(209, 250, 229, 0.65)) !important;
  border-color: rgba(16, 185, 129, 0.4) !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 4px 14px rgba(16, 185, 129, 0.18);
}

.header-action-btn--component:hover {
  color: #064e3b !important;
  border-color: rgba(5, 150, 105, 0.55) !important;
  background: linear-gradient(165deg, #fff, rgba(167, 243, 208, 0.88)) !important;
  box-shadow:
    0 1px 0 #fff inset,
    0 10px 26px rgba(16, 185, 129, 0.26);
}

/* 製品：本数棚卸（バイオレット系） */
.header-action-btn--product-count {
  color: #5b21b6 !important;
  background: linear-gradient(165deg, rgba(255, 255, 255, 0.98), rgba(237, 233, 254, 0.75)) !important;
  border-color: rgba(139, 92, 246, 0.42) !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.92) inset,
    0 4px 14px rgba(139, 92, 246, 0.2);
}

.header-action-btn--product-count:hover {
  color: #4c1d95 !important;
  border-color: rgba(124, 58, 237, 0.55) !important;
  background: linear-gradient(165deg, #fff, rgba(221, 214, 254, 0.92)) !important;
  box-shadow:
    0 1px 0 #fff inset,
    0 10px 26px rgba(139, 92, 246, 0.28);
}

/* 製品：金額棚卸（アンバー系） */
.header-action-btn--product-amount {
  color: #9a3412 !important;
  background: linear-gradient(165deg, rgba(255, 255, 255, 0.98), rgba(254, 243, 199, 0.72)) !important;
  border-color: rgba(245, 158, 11, 0.48) !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 4px 14px rgba(245, 158, 11, 0.22);
}

.header-action-btn--product-amount:hover {
  color: #7c2d12 !important;
  border-color: rgba(217, 119, 6, 0.58) !important;
  background: linear-gradient(165deg, #fff, rgba(253, 230, 138, 0.88)) !important;
  box-shadow:
    0 1px 0 #fff inset,
    0 10px 26px rgba(245, 158, 11, 0.3);
}

/* BOM */
.header-action-btn--bom {
  color: #3730a3 !important;
  background: linear-gradient(165deg, rgba(255, 255, 255, 0.98), rgba(224, 231, 255, 0.55)) !important;
  border-color: rgba(99, 102, 241, 0.35) !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.88) inset,
    0 3px 12px rgba(99, 102, 241, 0.12);
}

.header-action-btn--bom:hover {
  color: #312e81 !important;
  border-color: rgba(79, 70, 229, 0.5) !important;
  background: linear-gradient(165deg, #fff, rgba(199, 210, 254, 0.75)) !important;
  box-shadow:
    0 1px 0 #fff inset,
    0 10px 24px rgba(99, 102, 241, 0.22);
}

/* 原価 */
.header-action-btn--cost {
  color: #134e4a !important;
  background: linear-gradient(165deg, rgba(255, 255, 255, 0.98), rgba(204, 251, 241, 0.5)) !important;
  border-color: rgba(20, 184, 166, 0.38) !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.88) inset,
    0 3px 12px rgba(13, 148, 136, 0.12);
}

.header-action-btn--cost:hover {
  color: #0f766e !important;
  border-color: rgba(15, 118, 110, 0.52) !important;
  background: linear-gradient(165deg, #fff, rgba(153, 246, 228, 0.72)) !important;
  box-shadow:
    0 1px 0 #fff inset,
    0 10px 24px rgba(13, 148, 136, 0.2);
}

/* 設定不備 */
.header-action-btn--report {
  color: #7c3aed !important;
  background: linear-gradient(165deg, rgba(255, 255, 255, 0.98), rgba(237, 233, 254, 0.65)) !important;
  border-color: rgba(139, 92, 246, 0.38) !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 4px 14px rgba(139, 92, 246, 0.15);
}

.header-action-btn--report:hover {
  color: #6d28d9 !important;
  border-color: rgba(124, 58, 237, 0.48) !important;
  background: linear-gradient(165deg, #fff, rgba(221, 214, 254, 0.85)) !important;
  box-shadow:
    0 1px 0 #fff inset,
    0 10px 26px rgba(139, 92, 246, 0.22);
}

.header-action-btn--alert {
  color: #9f1239 !important;
  background: linear-gradient(165deg, rgba(255, 255, 255, 0.98), rgba(254, 226, 226, 0.65)) !important;
  border-color: rgba(244, 63, 94, 0.38) !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 4px 14px rgba(244, 63, 94, 0.15);
}

.header-action-btn--alert:hover {
  color: #881337 !important;
  border-color: rgba(225, 29, 72, 0.48) !important;
  background: linear-gradient(165deg, #fff, rgba(254, 205, 211, 0.85)) !important;
  box-shadow:
    0 1px 0 #fff inset,
    0 10px 26px rgba(244, 63, 94, 0.22);
}

.error-badge :deep(.el-badge__content) {
  border: 2px solid rgba(255, 255, 255, 0.95);
  font-weight: 800;
  font-size: 10px;
  min-width: 18px;
  height: 18px;
  line-height: 14px;
  padding: 0 4px;
  box-shadow: 0 2px 10px rgba(244, 63, 94, 0.35);
  background: linear-gradient(135deg, #fb7185, #e11d48);
}

.error-dialog :deep(.el-dialog) {
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow:
    0 4px 6px -1px rgba(15, 23, 42, 0.06),
    0 20px 40px -12px rgba(15, 23, 42, 0.16);
}

.error-dialog :deep(.el-dialog__header) {
  padding: 0;
  margin: 0;
}

.error-dialog :deep(.el-dialog__headerbtn) {
  top: 12px;
  right: 12px;
}

.error-dialog :deep(.el-dialog__body) {
  padding: 8px 14px 10px;
}

.error-dialog :deep(.el-dialog__footer) {
  padding: 8px 14px 12px;
  border-top: 1px solid rgba(148, 163, 184, 0.22);
  background: linear-gradient(180deg, #fafbfc 0%, #fff 100%);
}

.error-dialog__header {
  padding: 12px 40px 10px 14px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.22);
  background: linear-gradient(180deg, #f8fafc 0%, #fff 100%);
}

.error-dialog__header-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.error-dialog__title {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: #0f172a;
}

.error-dialog__count {
  font-size: 12px;
  font-weight: 600;
  color: #b45309;
  background: rgba(245, 158, 11, 0.14);
  border: 1px solid rgba(245, 158, 11, 0.28);
  padding: 2px 10px;
  border-radius: 999px;
}

.error-dialog__hint {
  margin: 6px 0 0;
  font-size: 12px;
  line-height: 1.45;
  color: #64748b;
}

.error-dialog__footer {
  display: flex;
  justify-content: flex-end;
}

.error-dialog-body {
  min-height: 64px;
}

.error-table :deep(.el-table__header-wrapper th.el-table__cell) {
  padding: 6px 0;
  font-size: 12px;
  font-weight: 600;
  color: #334155;
  background: #f1f5f9 !important;
}

.error-table :deep(.el-table__body .el-table__cell) {
  padding: 5px 0;
  font-size: 12px;
}

.error-table :deep(.el-table__row) {
  transition: background 0.12s ease;
}

.error-empty {
  padding: 8px 4px 4px;
}

.error-empty :deep(.el-empty__description) {
  max-width: 480px;
  margin: 8px auto 0;
  line-height: 1.5;
  font-size: 12px;
  color: #64748b;
}

.error-empty :deep(.el-empty__image) {
  margin-bottom: 4px;
}

.product-count-dialog :deep(.el-dialog) {
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow:
    0 4px 6px -1px rgba(15, 23, 42, 0.06),
    0 20px 40px -12px rgba(15, 23, 42, 0.16);
}

.product-count-dialog :deep(.el-dialog__header) {
  margin: 0;
  padding: 0;
}

.product-count-dialog :deep(.el-dialog__body) {
  padding: 8px 14px 10px;
}

.product-count-dialog :deep(.el-dialog__footer) {
  padding: 8px 14px 12px;
  border-top: 1px solid rgba(148, 163, 184, 0.22);
  background: linear-gradient(180deg, #fafbfc 0%, #fff 100%);
}

.product-count-dialog__header {
  padding: 12px 40px 10px 14px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.22);
  background: linear-gradient(180deg, #f8fafc 0%, #fff 100%);
}

.product-count-dialog__header-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.product-count-dialog__title {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}

.product-count-dialog__date-chip {
  font-size: 12px;
  font-weight: 600;
  color: #0369a1;
  background: rgba(14, 165, 233, 0.14);
  border: 1px solid rgba(14, 165, 233, 0.28);
  padding: 2px 10px;
  border-radius: 999px;
}

.product-count-dialog__alert-chip {
  font-size: 12px;
  font-weight: 700;
  color: #b91c1c;
  background: rgba(239, 68, 68, 0.14);
  border: 1px solid rgba(239, 68, 68, 0.3);
  padding: 2px 10px;
  border-radius: 999px;
}

.product-count-dialog__hint {
  margin: 6px 0 0;
  font-size: 12px;
  color: #64748b;
  line-height: 1.45;
}

.product-count-dialog__merge-controls {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
  padding: 6px 10px;
  background: rgba(241, 245, 249, 0.85);
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 8px;
  flex-wrap: wrap;
}

.product-count-dialog__dest-select {
  width: 320px;
}

.product-count-dialog__date-select {
  width: 320px;
}

.product-count-dialog__merge-hint {
  font-size: 11px;
  font-weight: 600;
  color: #0369a1;
  background: rgba(14, 165, 233, 0.1);
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid rgba(14, 165, 233, 0.22);
}

.product-count-dialog__body {
  min-height: 72px;
  border-radius: 10px;
  background: linear-gradient(180deg, #fcfdff 0%, #f8fafc 100%);
  border: 1px solid rgba(148, 163, 184, 0.2);
  padding: 8px;
}

.product-count-table :deep(.el-table__header-wrapper th.el-table__cell) {
  padding: 5px 0;
  font-size: 11px;
  font-weight: 600;
  color: #334155;
  background: #f1f5f9 !important;
}

.product-count-table :deep(.el-table__body .el-table__cell) {
  padding: 4px 0;
  font-size: 11px;
}

.product-count-table :deep(.el-table__body tr:hover > td.el-table__cell) {
  background: rgba(14, 165, 233, 0.08) !important;
}

.product-count-table :deep(.el-table__footer-wrapper td.el-table__cell) {
  background: linear-gradient(180deg, #eaf2ff 0%, #f3f7ff 100%) !important;
  color: #1e3a8a;
  font-weight: 700;
  padding: 5px 0;
  font-size: 11px;
}

.product-count-summary-strip {
  display: flex;
  justify-content: flex-end;
  gap: 18px;
  margin-top: 7px;
  padding: 6px 10px;
  font-size: 12px;
  color: #475569;
  background: linear-gradient(90deg, rgba(241, 245, 249, 0.7), rgba(219, 234, 254, 0.65));
  border: 1px solid rgba(148, 163, 184, 0.24);
  border-radius: 8px;
}

.product-count-summary-strip strong {
  margin-left: 6px;
  color: #0f172a;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

.product-count-dialog__footer {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.product-count-dialog__actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.product-count-empty {
  padding: 8px 0 4px;
}

.monthly-report-dialog__header {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 8px;
}

.monthly-report-dialog__header-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.monthly-report-dialog__title {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}

.monthly-report-dialog__body {
  max-height: 76vh;
  overflow-y: auto;
  padding: 0;
}

.filter-container {
  margin-bottom: 8px;
  padding: 8px 12px;
  background: var(--ivm-surface);
  border-radius: 10px;
  border: 1px solid var(--ivm-border);
  box-shadow: 0 4px 20px rgba(15, 23, 42, 0.05);
}

.filter-row {
  display: flex;
  gap: 6px;
  align-items: center;
  flex-wrap: wrap;
}

.filter-row--main {
  gap: 10px;
  align-items: center;
}

.filter-period-inline {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  min-width: 0;
}

.filter-inline-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--ivm-muted);
  white-space: nowrap;
}

.date-picker {
  width: 140px;
  flex-shrink: 0;
}

.date-picker :deep(.el-input__wrapper) {
  border-radius: 6px;
  min-height: 30px;
}

.range-input {
  width: min(320px, 42vw);
  min-width: 200px;
  flex: 1 1 200px;
}

.range-input :deep(.el-input__wrapper) {
  border-radius: 6px;
  min-height: 30px;
  background: rgba(148, 163, 184, 0.1);
  box-shadow: none;
}

.range-input :deep(.el-input__inner) {
  color: #475569;
  font-size: 12px;
  font-weight: 500;
  cursor: default;
}

.product-filter-select {
  width: 260px;
  min-width: 180px;
  flex-shrink: 0;
}

.filter-actions {
  display: flex;
  gap: 6px;
  align-items: center;
  flex-wrap: wrap;
  margin-left: auto;
}

.search-btn,
.clear-btn {
  border-radius: 6px;
  font-weight: 600;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.search-btn {
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.25);
}

.clear-btn {
  color: #475569;
}

.btn-icon {
  font-size: 14px;
}

.kpi-strip {
  margin-bottom: 8px;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.kpi-tile {
  position: relative;
  border-radius: 12px;
  padding: 1px;
  background: linear-gradient(
    145deg,
    rgba(255, 255, 255, 0.95),
    rgba(248, 250, 252, 0.88)
  );
  border: 1px solid rgba(15, 23, 42, 0.06);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.8) inset,
    0 10px 28px -8px rgba(15, 23, 42, 0.12);
  overflow: hidden;
  transition:
    transform 0.22s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.22s ease,
    border-color 0.2s ease;
}

.kpi-tile:hover {
  transform: translateY(-2px);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.85) inset,
    0 18px 40px -12px rgba(15, 23, 42, 0.16);
}

.kpi-tile__glow {
  position: absolute;
  inset: -40% -20% auto;
  height: 70%;
  opacity: 0.22;
  pointer-events: none;
  filter: blur(28px);
  border-radius: 50%;
}

.kpi-tile--total .kpi-tile__glow {
  background: radial-gradient(circle at 30% 20%, var(--kpi-total), transparent 65%);
}

.kpi-tile--material .kpi-tile__glow {
  background: radial-gradient(circle at 30% 20%, var(--kpi-material), transparent 65%);
}

.kpi-tile--component .kpi-tile__glow {
  background: radial-gradient(circle at 30% 20%, var(--kpi-component), transparent 65%);
}

.kpi-tile--product .kpi-tile__glow {
  background: radial-gradient(circle at 30% 20%, var(--kpi-product), transparent 65%);
}

.kpi-tile__body {
  position: relative;
  z-index: 1;
  padding: 10px 12px 11px;
  border-radius: 11px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.72) 0%, rgba(255, 255, 255, 0.96) 42%);
  backdrop-filter: blur(12px);
}

.kpi-tile--total .kpi-tile__body {
  box-shadow: inset 0 2px 0 0 var(--kpi-total);
}

.kpi-tile--material .kpi-tile__body {
  box-shadow: inset 0 2px 0 0 var(--kpi-material);
}

.kpi-tile--component .kpi-tile__body {
  box-shadow: inset 0 2px 0 0 var(--kpi-component);
}

.kpi-tile--product .kpi-tile__body {
  box-shadow: inset 0 2px 0 0 var(--kpi-product);
}

.kpi-tile__tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #fff;
  margin-bottom: 6px;
}

.kpi-tile--total .kpi-tile__tag {
  background: linear-gradient(120deg, var(--kpi-total), var(--kpi-total-deep));
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
}

.kpi-tile--material .kpi-tile__tag {
  background: linear-gradient(120deg, var(--kpi-material), var(--kpi-material-deep));
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.3);
}

.kpi-tile--component .kpi-tile__tag {
  background: linear-gradient(120deg, var(--kpi-component), var(--kpi-component-deep));
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.28);
}

.kpi-tile--product .kpi-tile__tag {
  background: linear-gradient(120deg, var(--kpi-product), var(--kpi-product-deep));
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.28);
}

.kpi-tile__value {
  font-size: clamp(1rem, 1.9vw, 1.25rem);
  font-weight: 800;
  letter-spacing: -0.03em;
  color: #0f172a;
  line-height: 1.12;
  font-variant-numeric: tabular-nums;
  margin: 0 0 4px;
}

.kpi-tile__desc {
  margin: 0;
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  letter-spacing: 0.01em;
  line-height: 1.25;
}

.content-tabs {
  --iv-tab-gap: 12px;
  margin-top: 0;
}

.tab-card {
  background: linear-gradient(165deg, rgba(255, 255, 255, 0.97) 0%, rgba(248, 250, 252, 0.94) 100%);
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 14px;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 12px 32px rgba(15, 23, 42, 0.06);
  transition:
    box-shadow 0.4s cubic-bezier(0.22, 1, 0.36, 1),
    border-color 0.35s ease,
    transform 0.45s cubic-bezier(0.22, 1, 0.36, 1);
}

.tab-card:hover {
  border-color: rgba(14, 165, 233, 0.2);
  box-shadow:
    0 4px 16px rgba(15, 23, 42, 0.07),
    0 0 0 1px rgba(14, 165, 233, 0.06) inset;
}

.tab-card :deep(.el-card__body) {
  padding: var(--iv-tab-gap);
}

.custom-tabs {
  border: none;
  background: transparent;
}

.custom-tabs :deep(.el-tabs__header) {
  margin: 0 0 var(--iv-tab-gap);
  padding: var(--iv-tab-gap);
  background: linear-gradient(145deg, rgba(241, 245, 249, 0.95) 0%, rgba(226, 232, 240, 0.55) 100%);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 12px;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.8) inset;
}

.custom-tabs :deep(.el-tabs__nav-wrap) {
  padding: 0;
}

.custom-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.custom-tabs :deep(.el-tabs__nav) {
  display: flex;
  width: 100%;
  gap: var(--iv-tab-gap);
}

.custom-tabs :deep(.el-tabs__item) {
  flex: 1 1 0;
  min-width: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  color: #64748b;
  font-weight: 700;
  font-size: 13px;
  letter-spacing: 0.02em;
  padding: 10px var(--iv-tab-gap);
  margin: 0;
  line-height: 1.35;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(148, 163, 184, 0.18);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  transition:
    color 0.3s cubic-bezier(0.22, 1, 0.36, 1),
    background 0.3s cubic-bezier(0.22, 1, 0.36, 1),
    border-color 0.3s ease,
    box-shadow 0.35s cubic-bezier(0.22, 1, 0.36, 1),
    transform 0.28s cubic-bezier(0.22, 1, 0.36, 1);
}

.custom-tabs :deep(.el-tabs__item:not(.is-active):hover) {
  color: #0f172a;
  background: rgba(255, 255, 255, 0.92);
  border-color: rgba(14, 165, 233, 0.28);
  box-shadow: 0 4px 14px rgba(14, 165, 233, 0.12);
  transform: translateY(-1px);
}

.custom-tabs :deep(#tab-material.is-active) {
  color: #fff;
  background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 55%, #0369a1 100%);
  border-color: transparent;
  box-shadow:
    0 6px 20px rgba(14, 165, 233, 0.38),
    0 0 0 1px rgba(255, 255, 255, 0.2) inset;
  animation: iv-tab-active-glow 2.8s ease-in-out infinite;
}

.custom-tabs :deep(#tab-component.is-active) {
  color: #fff;
  background: linear-gradient(135deg, #34d399 0%, #10b981 50%, #047857 100%);
  border-color: transparent;
  box-shadow:
    0 6px 20px rgba(16, 185, 129, 0.35),
    0 0 0 1px rgba(255, 255, 255, 0.2) inset;
  animation: iv-tab-active-glow-emerald 2.8s ease-in-out infinite;
}

.custom-tabs :deep(#tab-product.is-active) {
  color: #fff;
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 45%, #d97706 100%);
  border-color: transparent;
  box-shadow:
    0 6px 20px rgba(245, 158, 11, 0.38),
    0 0 0 1px rgba(255, 255, 255, 0.22) inset;
  animation: iv-tab-active-glow-amber 2.8s ease-in-out infinite;
}

.custom-tabs :deep(#tab-material:not(.is-active):hover) {
  color: #0369a1;
  background: rgba(14, 165, 233, 0.1);
}

.custom-tabs :deep(#tab-component:not(.is-active):hover) {
  color: #047857;
  background: rgba(16, 185, 129, 0.1);
}

.custom-tabs :deep(#tab-product:not(.is-active):hover) {
  color: #b45309;
  background: rgba(251, 191, 36, 0.14);
}

.custom-tabs :deep(.el-tabs__active-bar) {
  display: none;
}

.custom-tabs :deep(.el-tabs__content) {
  padding: 0;
  margin-top: 0;
  animation: iv-tab-content-fade 0.4s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.iv-tab-label {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-width: 0;
}

.iv-tab-label__icon {
  font-size: 16px;
  flex-shrink: 0;
  transition: transform 0.3s cubic-bezier(0.22, 1, 0.36, 1);
}

.iv-tab-label__text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.custom-tabs :deep(.el-tabs__item:not(.is-active):hover) .iv-tab-label__icon {
  transform: scale(1.1) rotate(-3deg);
}

.custom-tabs :deep(.el-tabs__item.is-active) .iv-tab-label__icon {
  transform: scale(1.06);
}

@keyframes iv-tab-active-glow {
  0%,
  100% {
    box-shadow:
      0 6px 20px rgba(14, 165, 233, 0.38),
      0 0 0 1px rgba(255, 255, 255, 0.2) inset;
  }
  50% {
    box-shadow:
      0 8px 28px rgba(14, 165, 233, 0.48),
      0 0 0 1px rgba(255, 255, 255, 0.28) inset;
  }
}

@keyframes iv-tab-active-glow-emerald {
  0%,
  100% {
    box-shadow:
      0 6px 20px rgba(16, 185, 129, 0.35),
      0 0 0 1px rgba(255, 255, 255, 0.2) inset;
  }
  50% {
    box-shadow:
      0 8px 28px rgba(16, 185, 129, 0.48),
      0 0 0 1px rgba(255, 255, 255, 0.28) inset;
  }
}

@keyframes iv-tab-active-glow-amber {
  0%,
  100% {
    box-shadow:
      0 6px 20px rgba(245, 158, 11, 0.38),
      0 0 0 1px rgba(255, 255, 255, 0.22) inset;
  }
  50% {
    box-shadow:
      0 8px 28px rgba(245, 158, 11, 0.52),
      0 0 0 1px rgba(255, 255, 255, 0.3) inset;
  }
}

@keyframes iv-tab-content-fade {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .tab-card,
  .custom-tabs :deep(.el-tabs__item),
  .custom-tabs :deep(.el-tabs__content),
  .iv-tab-label__icon,
  .header-action-btn {
    animation: none !important;
    transition: none !important;
  }

  .custom-tabs :deep(.el-tabs__item:not(.is-active):hover) {
    transform: none;
  }

  .header-action-btn:hover,
  .header-action-btn:active {
    transform: none;
  }
}

@media (max-width: 1200px) {
  .kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .inventory-value-management {
    padding: 8px;
  }

  .header-content {
    gap: 8px;
  }

  .filter-row--main {
    gap: 8px;
  }

  .filter-period-inline {
    width: 100%;
  }

  .date-picker {
    width: 140px;
  }

  .range-input {
    width: 100%;
    min-width: 0;
    flex: 1 1 auto;
  }

  .product-filter-select {
    width: 100%;
  }

  .filter-actions {
    margin-left: 0;
    width: 100%;
    justify-content: flex-start;
  }

  .kpi-grid {
    grid-template-columns: 1fr;
    gap: 8px;
  }

  .page-title {
    font-size: 1rem;
  }

  .kpi-tile__value {
    font-size: 1.15rem;
  }

  .custom-tabs :deep(.el-tabs__content) {
    padding: 0;
  }
}

@media (max-width: 480px) {
  .inventory-value-management {
    padding: 8px;
  }

  .header-icon {
    width: 32px;
    height: 32px;
  }

  .kpi-tile__body {
    padding: 9px 11px;
  }

  .kpi-tile__value {
    font-size: 1.05rem;
  }

  .custom-tabs :deep(.el-tabs__nav) {
    flex-direction: column;
    gap: 8px;
  }

  .custom-tabs :deep(.el-tabs__item) {
    flex: none;
    width: 100%;
    padding: 10px 12px;
    font-size: 12px;
  }

  .iv-tab-label__icon {
    font-size: 15px;
  }
}
</style>
