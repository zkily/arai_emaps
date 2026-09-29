<template>
  <div class="part-order-container">
    <!-- ページヘッダー -->
    <div class="page-header">
      <div class="header-left">
        <div class="title-section">
          <div class="title-icon">
            <el-icon><ShoppingCart /></el-icon>
          </div>
          <div class="title-text">
            <h1 class="main-title">部品在庫管理(発注・使用)</h1>
            <p class="subtitle">部品の在庫推移・使用実績・発注を一元管理</p>
          </div>
        </div>
      </div>
      <div class="header-actions">
        <el-button
          class="action-btn sync-btn"
          @click="handleSyncPartMaster"
          :loading="partMasterSyncLoading"
        >
          <el-icon><Refresh /></el-icon>
          部品マスタ更新
        </el-button>
        <el-button
          class="action-btn success-btn"
          @click="handleDataGeneration"
          :loading="dataGenerationLoading"
        >
          <el-icon><DocumentAdd /></el-icon>
          データ生成
        </el-button>
        <el-button
          class="action-btn warning-btn"
          @click="handleStockCalculation"
          :loading="stockCalculationLoading"
        >
          <el-icon><Operation /></el-icon>
          在庫計算
        </el-button>
      </div>
    </div>

    <!-- 統計カード -->
    <div class="stats-container">
      <div class="stats-grid">
        <!-- 第一行統計 -->
        <div class="stat-card primary">
          <div class="stat-icon">
            <el-icon><Goods /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ formatNumber(stats.totalParts) }}</div>
            <div class="stat-label">総部品種類数</div>
          </div>
        </div>

        <div class="stat-card info">
          <div class="stat-icon">
            <el-icon><Box /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value" :class="{ 'is-negative': isNegative(stats.totalCurrentStock) }">
              {{ formatNumber(stats.totalCurrentStock) }}<span class="unit">束</span>
            </div>
            <div class="stat-label">在庫数合計</div>
          </div>
        </div>

        <div class="stat-card warning">
          <div class="stat-icon">
            <el-icon><Coin /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">
              {{ formatCurrency(Number((stats.averageUnitPrice || 0).toFixed(2))) }}
            </div>
            <div class="stat-label">平均単価</div>
          </div>
        </div>

        <div class="stat-card success">
          <div class="stat-icon">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value" :class="{ 'is-negative': isNegative(stats.totalUsageQuantity) }">
              {{ formatNumber(stats.totalUsageQuantity) }}
            </div>
            <div class="stat-label">使用数合計</div>
          </div>
        </div>

        <!-- 第二行統計 -->
        <div class="stat-card order">
          <div class="stat-icon">
            <el-icon><ShoppingCart /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">
              {{ formatNumber(stats.totalOrderQuantity) }}
            </div>
            <div class="stat-label">注文本数</div>
          </div>
        </div>

        <div class="stat-card amount">
          <div class="stat-icon">
            <el-icon><Money /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value" :class="{ 'is-negative': isNegative(stats.totalOrderValue) }">
              {{ formatCurrency(stats.totalOrderValue || 0) }}
            </div>
            <div class="stat-label">参考注文金額</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 検索とフィルター区域 -->
    <div class="search-section">
      <div class="search-container">
        <div class="search-row">

          <div class="filter-item date-group">
            <span class="filter-label">
              <el-icon><Calendar /></el-icon>期間
            </span>
            <el-date-picker
              v-model="searchForm.dateRange"
              type="daterange"
              range-separator="~"
              start-placeholder="開始日"
              end-placeholder="終了日"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              @change="handleDateRangeSearch"
              class="filter-date-picker"
              size="small"
            />
            <div class="date-nav-group">
              <el-button size="small" class="date-nav-btn" @click="setDateRange(-1)">
                <el-icon><ArrowLeft /></el-icon>
              </el-button>
              <el-button size="small" class="date-nav-btn today-btn" @click="setDateRange(0)">今日</el-button>
              <el-button size="small" class="date-nav-btn" @click="setDateRange(1)">
                <el-icon><ArrowRight /></el-icon>
              </el-button>
            </div>
          </div>

          <!-- 部品 -->
          <div class="filter-item part-filter-item">
            <span class="filter-label">
              <el-icon><Search /></el-icon>部品
            </span>
            <el-select
              v-model="searchForm.part_cd"
              filterable
              remote
              clearable
              reserve-keyword
              placeholder="全て"
              :remote-method="remoteFetchParts"
              :loading="partSelectLoading"
              @visible-change="onPartSelectVisible"
              @change="handlePartFilterChange"
              class="filter-select part-code-select"
              size="small"
            >
              <el-option
                v-for="opt in partSelectOptions"
                :key="opt.value"
                :label="opt.label"
                :value="opt.value"
              />
            </el-select>
          </div>

          <!-- 仕入先 -->
          <div class="filter-item supplier-item">
            <span class="filter-label">
              <el-icon><User /></el-icon>仕入先
            </span>
            <el-select
              v-model="searchForm.supplier"
              placeholder="全て"
              clearable
              multiple
              collapse-tags
              collapse-tags-tooltip
              @change="handleSupplierSearch"
              class="filter-select"
              size="small"
            >
              <el-option
                v-for="supplier in supplierOptions"
                :key="supplier.value"
                :label="supplier.label"
                :value="supplier.value"
              />
            </el-select>
          </div>

        </div>
      </div>
    </div>


    <!-- 材料受注テーブル -->
    <div class="table-section">
      <div class="table-container" @keydown.enter="handleTableEnterNav">
        <div class="table-header">
          <div class="table-tabs">
            <div
              class="tab-item tab-item--initial"
              :class="{ active: activeTab === 'initial' }"
              @click="handleTabChange('initial')"
            >
              <el-icon><Box /></el-icon>
              <span>初期在庫管理</span>
            </div>
            <div
              class="tab-item tab-item--stock"
              :class="{ active: activeTab === 'stock' }"
              @click="handleTabChange('stock')"
            >
              <el-icon><DataLine /></el-icon>
              <span>部品日別在庫</span>
            </div>
            <div
              class="tab-item tab-item--usage"
              :class="{ active: activeTab === 'usage' }"
              @click="handleTabChange('usage')"
            >
              <el-icon><Operation /></el-icon>
              <span>部品使用管理</span>
            </div>
            <div
              class="tab-item tab-item--order"
              :class="{ active: activeTab === 'order' }"
              @click="handleTabChange('order')"
            >
              <el-icon><ShoppingCart /></el-icon>
              <span>部品注文</span>
            </div>
            <div
              class="tab-item tab-item--history"
              :class="{ active: activeTab === 'orderHistory' }"
              @click="handleTabChange('orderHistory')"
            >
              <el-icon><List /></el-icon>
              <span>部品注文履歴</span>
            </div>
          </div>
          <div class="table-hint" v-if="activeTab !== 'orderHistory'">
            <kbd>Enter</kbd> 次の行　<kbd>Shift</kbd>+<kbd>Enter</kbd> 前の行
          </div>
          <div class="table-actions" v-if="activeTab === 'order'">
            <el-badge
              :value="reorderBadge.count"
              :hidden="!reorderBadge.count"
              :type="reorderBadge.urgent ? 'danger' : 'warning'"
              class="reorder-badge"
            >
              <el-button @click="openReorderDialog" class="reorder-btn">
                <el-icon><Bell /></el-icon>
                発注提案
              </el-button>
            </el-badge>
            <el-button type="success" @click="handleAddManualOrder" class="add-btn">
              <el-icon><Plus /></el-icon>
              部品注文追加
            </el-button>
            <el-button type="primary" @click="handlePrintOrder" class="print-btn">
              <el-icon><Printer /></el-icon>
              注文書発行
            </el-button>
          </div>
          <div class="table-actions" v-if="activeTab === 'initial'">
            <el-button type="primary" @click="handleSetMonthStart" class="month-start-btn">
              <el-icon><Calendar /></el-icon>
              当月月初に設定
            </el-button>
          </div>
        </div>

        <!-- 部品日別在庫テーブル -->
        <div class="table-content" v-if="activeTab === 'stock'">
          <el-table
            v-loading="loading"
            :data="filteredTableData"
            border
            @cell-click="handleTableCellClick"
            class="modern-table"
            :default-sort="{ prop: 'part_name', order: 'ascending' }"
            height="calc(100vh - 280px)"
            :max-height="800"
          >
            <el-table-column prop="date" label="日付" width="110" align="center" sortable />
            <el-table-column
              prop="supplier_name"
              label="仕入先"
              width="150"
              show-overflow-tooltip
              sortable
            />
            <el-table-column prop="part_cd" label="部品CD" width="90" align="center" />
            <el-table-column
              prop="part_name"
              label="部品名"
              :sort-method="comparePartName"
              class-name="part-name-cell"
              width="180"
              show-overflow-tooltip
              sortable
            />

            <el-table-column
              prop="current_stock"
              label="現在在庫"
              width="100"
              align="center"
              class-name="current-stock-column"
            >
              <template #default="{ row }">
                <span :class="{ 'negative-number': row.current_stock < 0 }">{{
                  formatValue(row.current_stock)
                }}</span>
              </template>
            </el-table-column>
            <el-table-column
              label="使用数"
              width="100"
              align="center"
              class-name="usage-quantity-column"
            >
              <template #default="{ row }">
                <span
                  class="usage-quantity-readonly"
                  :class="{ 'negative-number': isNegative(row.usage_quantity) }"
                >{{ formatValue(row.usage_quantity) }}</span>
              </template>
            </el-table-column>
            <el-table-column
              label="手動使用数"
              width="140"
              align="center"
              class-name="usage-quantity-column"
            >
              <template #default="{ row }">
                <el-input-number
                  :key="`manual-usage-${row.id}`"
                  :model-value="emptyIfZero(row.manual_usage)"
                  :min="0"
                  :max="999999"
                  :precision="0"
                  :controls="false"
                  :value-on-clear="null"
                  size="small"
                  class="usage-quantity-input"
                  @change="(val) => handleManualUsageChange(row, val)"
                  @keydown.capture="preventNumberSpinnerKeys"
                  @wheel.prevent
                />
              </template>
            </el-table-column>
            <el-table-column
              label="使用計画"
              width="110"
              align="center"
              class-name="usage-quantity-column"
            >
              <template #default="{ row }">
                <span
                  class="usage-quantity-readonly"
                  :class="{ 'negative-number': isNegative(row.usage_plan_qty) }"
                >{{ formatValue(row.usage_plan_qty) }}</span>
              </template>
            </el-table-column>
            <el-table-column
              label="在庫推移"
              width="110"
              align="center"
              class-name="usage-quantity-column"
            >
              <template #default="{ row }">
                <span
                  class="usage-quantity-readonly"
                  :class="{ 'negative-number': isNegative(row.stock_trend) }"
                >{{ formatValue(row.stock_trend) }}</span>
              </template>
            </el-table-column>
            <el-table-column
              label="注文本数"
              width="140"
              align="center"
              class-name="order-quantity-column"
            >
              <template #default="{ row }">
                <el-input-number
                  :model-value="(row.order_quantity === 0 ? undefined : row.order_quantity)"
                  :min="0"
                  :max="999999"
                  :precision="0"
                  :controls="false"
                  size="small"
                  class="order-quantity-input"
                  @update:model-value="(val) => { row.order_quantity = val ?? 0; handleOrderQuantityChange(row); }"
                />
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 部品使用管理テーブル -->
        <div class="table-content" v-if="activeTab === 'usage'">
          <el-table
            v-loading="loading"
            :data="filteredTableData"
            border
            @cell-click="handleTableCellClick"
            class="modern-table"
            :default-sort="{ prop: 'part_name', order: 'ascending' }"
            height="calc(100vh - 280px)"
            :max-height="800"
          >
            <el-table-column prop="date" label="日付" width="120" align="center" sortable />
            <el-table-column
              prop="supplier_name"
              label="仕入先"
              width="150"
              show-overflow-tooltip
              sortable
              
            />
            <el-table-column prop="part_cd" label="部品CD" width="120" align="center" />
            <el-table-column
              prop="part_name"
              label="部品名"
              :sort-method="comparePartName"
              class-name="part-name-cell"
              width="180"
              show-overflow-tooltip
              sortable
              align="center"
              
            />
            <el-table-column
              prop="current_stock"
              label="現在在庫"
              width="120"
              align="center"
              class-name="current-stock-column"
            >
              <template #default="{ row }">
                <span :class="{ 'negative-number': row.current_stock < 0 }">{{
                  formatValue(row.current_stock)
                }}</span>
              </template>
            </el-table-column>
            <el-table-column
              label="使用数"
              width="100"
              align="center"
              class-name="usage-quantity-column"
            >
              <template #default="{ row }">
                <span
                  class="usage-quantity-readonly"
                  :class="{ 'negative-number': isNegative(row.usage_quantity) }"
                >{{ formatValue(row.usage_quantity) }}</span>
              </template>
            </el-table-column>
            <el-table-column
              label="手動使用数"
              width="140"
              align="center"
              class-name="usage-quantity-column"
            >
              <template #default="{ row }">
                <el-input-number
                  :key="`manual-usage-${row.id}`"
                  :model-value="emptyIfZero(row.manual_usage)"
                  :min="0"
                  :max="999999"
                  :precision="0"
                  :controls="false"
                  :value-on-clear="null"
                  size="small"
                  class="usage-quantity-input"
                  @change="(val) => handleManualUsageChange(row, val)"
                  @keydown.capture="preventNumberSpinnerKeys"
                  @wheel.prevent
                />
              </template>
            </el-table-column>
            <el-table-column
              label="使用計画"
              width="110"
              align="center"
              class-name="usage-quantity-column"
            >
              <template #default="{ row }">
                <span
                  class="usage-quantity-readonly"
                  :class="{ 'negative-number': isNegative(row.usage_plan_qty) }"
                >{{ formatValue(row.usage_plan_qty) }}</span>
              </template>
            </el-table-column>
            <el-table-column
              label="在庫推移"
              width="110"
              align="center"
              class-name="usage-quantity-column"
            >
              <template #default="{ row }">
                <span
                  class="usage-quantity-readonly"
                  :class="{ 'negative-number': isNegative(row.stock_trend) }"
                >{{ formatValue(row.stock_trend) }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 部品注文テーブル -->
        <div class="table-content" v-if="activeTab === 'order'">
          <el-table
            v-loading="loading"
            :data="filteredTableData"
            border
            @cell-click="handleTableCellClick"
            class="modern-table"
            :default-sort="{ prop: 'part_name', order: 'ascending' }"
            height="calc(100vh - 280px)"
            :max-height="800"
          >
            <el-table-column prop="date" label="日付" width="120" align="center" sortable />
            <el-table-column prop="part_cd" label="部品CD" width="120" align="center" />
            <el-table-column
              prop="part_name"
              label="部品名"
              :sort-method="comparePartName"
              class-name="part-name-cell"
              min-width="180"
              show-overflow-tooltip
              sortable
            />
            <el-table-column
              prop="supplier_name"
              label="仕入先"
              width="150"
              show-overflow-tooltip
            />
            <el-table-column prop="standard_spec" label="規格" width="150" show-overflow-tooltip />
            <el-table-column
              prop="current_stock"
              label="現在在庫"
              width="100"
              align="center"
              class-name="current-stock-column"
            >
              <template #default="{ row }">
                <span :class="{ 'negative-number': row.current_stock < 0 }">{{
                  formatValue(row.current_stock)
                }}</span>
              </template>
            </el-table-column>
            <el-table-column
              label="注文本数"
              width="140"
              align="center"
              class-name="order-quantity-column"
            >
              <template #default="{ row }">
                <el-input-number
                  :model-value="(row.order_quantity === 0 ? undefined : row.order_quantity)"
                  :min="0"
                  :max="999999"
                  :precision="0"
                  :controls="false"
                  size="small"
                  class="order-quantity-input"
                  @update:model-value="(val) => { row.order_quantity = val ?? 0; handleOrderQuantityChange(row); }"
                />
              </template>
            </el-table-column>
            <el-table-column label="注文金額" width="120" align="center">
              <template #default="{ row }">
                <span :class="{ 'negative-number': (row.order_amount || 0) < 0 }">{{
                  formatValue(Math.round(row.order_amount || 0))
                    ? '¥' + Math.round(row.order_amount || 0).toLocaleString('ja-JP')
                    : ''
                }}</span>
              </template>
            </el-table-column>
            <el-table-column label="備考" width="200">
              <template #default="{ row }">
                <el-input
                  v-model="row.remarks"
                  placeholder="備考を入力"
                  size="small"
                  @blur="handleRemarksChange(row)"
                />
              </template>
            </el-table-column>
            <el-table-column v-if="canDelete" label="操作" width="80" align="center">
              <template #default="{ row }">
                <el-button
                  v-if="(row.order_quantity || 0) > 0"
                  link
                  type="danger"
                  size="small"
                  class="cancel-order-btn"
                  @click="handleCancelOrder(row)"
                >
                  取消
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 部品注文履歴（期間・キーワードで注文数>0の material_stock のみ、参照専用） -->
        <div class="table-content" v-if="activeTab === 'orderHistory'">
          <el-table
            v-loading="loading"
            :data="filteredTableData"
            border
            @cell-click="handleTableCellClick"
            class="modern-table order-history-table"
            :default-sort="{ prop: 'part_name', order: 'ascending' }"
            height="calc(100vh - 280px)"
            :max-height="800"
            show-summary
            :summary-method="getOrderHistorySummaries"
          >
            <el-table-column prop="date" label="日付" width="120" align="center" sortable />
            <el-table-column prop="part_cd" label="部品CD" width="120" align="center" />
            <el-table-column
              prop="part_name"
              label="部品名"
              :sort-method="comparePartName"
              class-name="part-name-cell"
              min-width="180"
              show-overflow-tooltip
              sortable
            />
            <el-table-column
              prop="supplier_name"
              label="仕入先"
              width="150"
              show-overflow-tooltip
            />
            <el-table-column prop="standard_spec" label="規格" width="150" show-overflow-tooltip />
            <el-table-column
              prop="current_stock"
              label="現在在庫"
              width="100"
              align="center"
            >
              <template #default="{ row }">
                <span :class="{ 'negative-number': row.current_stock < 0 }">{{
                  formatValue(row.current_stock)
                }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="order_quantity" label="注文本数" width="110" align="center" sortable>
              <template #default="{ row }">
                <span :class="{ 'negative-number': isNegative(row.order_quantity) }">{{
                  formatValue(row.order_quantity)
                }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="order_amount" label="注文金額" width="120" align="center">
              <template #default="{ row }">
                <span :class="{ 'negative-number': (row.order_amount || 0) < 0 }">{{
                  formatValue(Math.round(row.order_amount || 0))
                    ? '¥' + Math.round(row.order_amount || 0).toLocaleString('ja-JP')
                    : ''
                }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="remarks" label="備考" min-width="160" show-overflow-tooltip />
          </el-table>
        </div>

        <!-- 初期在庫管理テーブル -->
        <div class="table-content" v-if="activeTab === 'initial'">
          <el-table
            v-loading="loading"
            :data="initialStockData"
            border
            @cell-click="handleTableCellClick"
            class="modern-table"
            :default-sort="{ prop: 'part_name', order: 'ascending' }"
            height="calc(100vh - 280px)"
            :max-height="800"
          >
            <el-table-column prop="date" label="日付" width="110" align="center" sortable />
            <el-table-column
              prop="supplier_name"
              label="仕入先"
              width="150"
              show-overflow-tooltip
              sortable
            />
            <el-table-column prop="part_cd" label="部品CD" width="80" align="center" />
            <el-table-column
              prop="part_name"
              label="部品名"
              :sort-method="comparePartName"
              class-name="part-name-cell"
              width="180"
              show-overflow-tooltip
              sortable
            />
            <el-table-column label="初期在庫" width="130" align="center">
              <template #default="{ row }">
                <el-input-number
                  v-model="row.initial_stock"
                  :min="0"
                  :precision="0"
                  :step="1"
                  :controls="false"
                  @change="handleInitialStockChange(row)"
                  :class="[
                    'initial-stock-input',
                    { 'positive-stock': (row.initial_stock || 0) > 0 },
                  ]"
                />
              </template>
            </el-table-column>
            <el-table-column label="調整数" width="130" align="center">
              <template #default="{ row }">
                <el-input-number
                  v-model="row.adjustment_quantity"
                  :precision="0"
                  :step="1"
                  :controls="false"
                  @change="handleAdjustmentQuantityChange(row)"
                  :class="[
                    'adjustment-quantity-input',
                    { 'is-negative': isNegative(row.adjustment_quantity) },
                  ]"
                />
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- ページネーション -->
        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.page_size"
            :page-sizes="[30, 50, 100, 200]"
            :total="pagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
            class="modern-pagination"
          />
        </div>
      </div>
    </div>

    <!-- データ生成日付選択ダイアログ -->
    <el-dialog
      v-model="dataGenerationDialogVisible"
      title="データ生成期間設定"
      width="450px"
      :close-on-click-modal="false"
      class="data-generation-dialog"
    >
      <div class="data-generation-content-compact">
        <div class="form-sections-compact">
          <div class="form-section-compact">
            <div class="section-header-compact">
              <el-icon class="section-icon"><Calendar /></el-icon>
              <span class="section-title">期間設定</span>
            </div>
            <div class="form-fields-compact">
              <div class="form-field-row">
                <label class="field-label">開始日</label>
                <el-date-picker
                  v-model="dataGenerationStartDate"
                  type="date"
                  placeholder="開始日を選択"
                  format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD"
                  class="form-input-compact date-picker-compact"
                  size="small"
                />
              </div>
              <div class="form-field-row">
                <label class="field-label">終了日</label>
                <el-date-picker
                  v-model="dataGenerationEndDate"
                  type="date"
                  placeholder="終了日を選択"
                  format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD"
                  class="form-input-compact date-picker-compact"
                  size="small"
                />
              </div>
            </div>
          </div>

          <div class="form-section-compact">
            <div class="section-header-compact">
              <el-icon class="section-icon"><InfoFilled /></el-icon>
              <span class="section-title">注意事項</span>
            </div>
            <div class="form-fields-compact">
              <ul class="info-list-compact">
                <li>既存のデータがある場合はスキップされます</li>
                <li>重複データは自動的に検出・スキップされます</li>
                <li>生成には時間がかかる場合があります</li>
                <li>期間が長いほど生成時間が長くなります</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer-compact">
          <el-button @click="dataGenerationDialogVisible = false" class="cancel-btn-compact">
            <el-icon><Close /></el-icon>
            キャンセル
          </el-button>
          <el-button
            type="primary"
            @click="confirmDataGeneration"
            class="confirm-btn-compact"
            :disabled="!dataGenerationStartDate || !dataGenerationEndDate"
          >
            <el-icon><DocumentAdd /></el-icon>
            生成実行
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 手入力部品注文ダイアログ -->
    <el-dialog
      v-model="manualOrderDialogVisible"
      title="部品注文追加"
      width="640px"
      :close-on-click-modal="false"
      class="manual-order-dialog manual-order-dialog--compact"
    >
      <div class="manual-order-content manual-order-content--compact">
        <div class="manual-order-header-compact">
          <div class="manual-order-header-compact__icon">
            <el-icon><Plus /></el-icon>
          </div>
          <div class="manual-order-header-compact__text">
            <h3>部品注文追加</h3>
            <p>新しい部品注文を手動で入力</p>
          </div>
        </div>

        <el-form
          :model="manualOrderForm"
          :rules="manualOrderRules"
          ref="manualOrderFormRef"
          label-position="top"
          label-width="auto"
          class="manual-order-form manual-order-form--compact"
        >
          <div class="manual-order-grid manual-order-grid--main">
            <el-form-item label="日付" prop="date" class="manual-order-field">
              <el-date-picker
                v-model="manualOrderForm.date"
                type="date"
                placeholder="日付を選択"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                class="manual-order-input"
                size="default"
              />
            </el-form-item>
            <el-form-item label="部品" prop="part_cd" class="manual-order-field manual-order-field--span2">
              <el-select
                v-model="manualOrderForm.part_cd"
                placeholder="部品を選択"
                filterable
                :loading="partSearchLoading"
                @change="handlePartChange"
                class="manual-order-input"
                size="default"
              >
                <el-option
                  v-for="material in partOptions"
                  :key="material.part_cd"
                  :label="`${material.part_cd} - ${material.part_name}`"
                  :value="material.part_cd"
                  :data-material="material"
                />
              </el-select>
            </el-form-item>
          </div>

          <div class="manual-order-grid manual-order-grid--order">
            <el-form-item label="注文本数" prop="order_quantity" class="manual-order-field">
              <el-input-number
                v-model="manualOrderForm.order_quantity"
                :min="0"
                :max="999999"
                :precision="0"
                :controls="false"
                placeholder="本数"
                class="manual-order-input"
                size="default"
              />
            </el-form-item>
            <el-form-item label="備考" class="manual-order-field manual-order-field--full">
              <el-input
                v-model="manualOrderForm.remarks"
                type="textarea"
                :rows="2"
                placeholder="備考（任意）"
                class="manual-order-input"
                size="default"
              />
            </el-form-item>
          </div>

          <div class="manual-order-detail" v-if="selectedPart">
            <div class="manual-order-detail__title">
              <el-icon><InfoFilled /></el-icon>
              <span>部品詳細</span>
              <span class="manual-order-detail__summary" v-if="calculatedAmount > 0">
                参考金額 {{ formatCurrency(calculatedAmount) }}
              </span>
            </div>
            <div class="manual-order-detail__grid">
              <div class="manual-order-detail__item">
                <span class="manual-order-detail__label">部品CD</span>
                <span class="manual-order-detail__value">{{ selectedPart.part_cd || '—' }}</span>
              </div>
              <div class="manual-order-detail__item">
                <span class="manual-order-detail__label">部品名</span>
                <span class="manual-order-detail__value">{{ selectedPart.part_name || '—' }}</span>
              </div>
              <div class="manual-order-detail__item">
                <span class="manual-order-detail__label">仕入先</span>
                <span class="manual-order-detail__value">{{ selectedPart.supplier_name || '—' }}</span>
              </div>
              <div class="manual-order-detail__item">
                <span class="manual-order-detail__label">規格</span>
                <span class="manual-order-detail__value">{{ selectedPart.standard_spec || '—' }}</span>
              </div>
              <div class="manual-order-detail__item">
                <span class="manual-order-detail__label">単価</span>
                <span class="manual-order-detail__value">{{ formatCurrency(selectedPart.unit_price || 0) }}</span>
              </div>
              <div class="manual-order-detail__item">
                <span class="manual-order-detail__label">束本数</span>
                <span class="manual-order-detail__value">{{ selectedPart.pieces_per_bundle ?? '—' }}</span>
              </div>
              <div class="manual-order-detail__item">
                <span class="manual-order-detail__label">単位</span>
                <span class="manual-order-detail__value">{{ selectedPart.unit || '—' }}</span>
              </div>
              <div class="manual-order-detail__item">
                <span class="manual-order-detail__label">リードタイム</span>
                <span class="manual-order-detail__value">{{ selectedPart.lead_time ?? '—' }}<template v-if="selectedPart.lead_time != null">日</template></span>
              </div>
            </div>
          </div>
        </el-form>
      </div>

      <template #footer>
        <div class="manual-order-footer manual-order-footer--compact">
          <el-button @click="handleCancelManualOrder" size="default" class="manual-order-btn manual-order-btn--cancel">
            <el-icon><Close /></el-icon>
            キャンセル
          </el-button>
          <el-button
            type="primary"
            @click="handleConfirmManualOrder"
            :loading="manualOrderLoading"
            size="default"
            class="manual-order-btn manual-order-btn--confirm"
          >
            <el-icon><Check /></el-icon>
            登録
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 印刷確認ダイアログ -->
    <el-dialog
      v-model="printConfirmDialogVisible"
      width="650px"
      :close-on-click-modal="false"
      :show-close="true"
      class="print-confirm-dialog"
    >
      <template #header>
        <div class="dialog-header-with-button">
          <span class="dialog-title">注文書印刷確認</span>
          <el-button
            type="primary"
            @click="confirmPrint"
            class="confirm-btn-header"
            size="small"
            :loading="printPdfSaving"
          >
            <el-icon><Printer /></el-icon>
            印刷実行
          </el-button>
        </div>
      </template>
      <div class="print-confirm-content-compact">
        <div class="form-sections-compact">
          <div class="form-section-compact">
            <div class="section-header-compact">
              <el-icon class="section-icon"><User /></el-icon>
              <span class="section-title">受注先情報</span>
            </div>
            <div class="form-fields-compact">
              <div class="form-field-row">
                <label class="field-label">受注先会社名</label>
                <el-input
                  v-model="printForm.recipientCompany"
                  placeholder="丸一鋼管株式会社 御中"
                  class="form-input-compact"
                  size="small"
                />
              </div>
              <div class="form-field-row">
                <label class="field-label">受注先担当者</label>
                <el-input
                  v-model="printForm.recipientPersons"
                  placeholder="鈴木様 村松様 只井様"
                  class="form-input-compact"
                  size="small"
                />
              </div>
            </div>
          </div>

          <div class="form-section-compact">
            <div class="section-header-compact">
              <el-icon class="section-icon"><EditPen /></el-icon>
              <span class="section-title">承認・発行情報</span>
            </div>
            <div class="form-fields-compact">
              <div class="form-field-row">
                <label class="field-label">承認者</label>
                <el-input
                  v-model="printForm.approver"
                  placeholder="篠田"
                  class="form-input-compact"
                  size="small"
                />
              </div>
              <div class="form-field-row">
                <label class="field-label">発行者</label>
                <el-input
                  v-model="printForm.issuer"
                  placeholder="趙"
                  class="form-input-compact"
                  size="small"
                />
              </div>
            </div>
          </div>

          <div class="form-section-compact">
            <div class="section-header-compact">
              <el-icon class="section-icon"><Box /></el-icon>
              <span class="section-title">備考・注意事項</span>
            </div>
            <div class="form-fields-compact">
              <div class="form-field-row">
                <label class="field-label">備考1</label>
                <el-input
                  v-model="printForm.note1"
                  type="textarea"
                  :rows="2"
                  placeholder="支払期日には法定税率による消費税額及び地方消費税分を加算して支払います。"
                  class="form-textarea-compact"
                  size="small"
                />
              </div>
              <div class="form-field-row">
                <label class="field-label">備考2</label>
                <el-input
                  v-model="printForm.note2"
                  type="textarea"
                  :rows="2"
                  placeholder="支払期日・支払方法・検査完了期日・有償支給原材料代金の決済期日及び方法については、令和8年7月1日の「支払方法等について」によります。"
                  class="form-textarea-compact"
                  size="small"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 発注提案ダイアログ -->
    <el-dialog
      v-model="reorderDialogVisible"
      title="発注提案"
      width="1100px"
      :close-on-click-modal="false"
      class="reorder-dialog"
    >
      <div class="reorder-toolbar">
        <div class="reorder-toolbar__field">
          <span class="reorder-toolbar__label">基準日</span>
          <el-date-picker
            v-model="reorderForm.baseDate"
            type="date"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            :clearable="false"
            size="small"
            style="width: 140px"
          />
        </div>
        <div class="reorder-toolbar__field">
          <span class="reorder-toolbar__label">見込日数（LT後）</span>
          <el-input-number
            v-model="reorderForm.horizonDays"
            :min="1"
            :max="180"
            :precision="0"
            size="small"
            controls-position="right"
            style="width: 100px"
          />
        </div>
        <el-button size="small" type="primary" :loading="reorderLoading" @click="loadReorderSuggestions()">
          <el-icon><Refresh /></el-icon>
          再計算
        </el-button>
        <div class="reorder-toolbar__summary">
          対象 <b>{{ reorderList.length }}</b> 件
          <span v-if="reorderBadge.urgent" class="reorder-toolbar__urgent">
            （緊急 {{ reorderBadge.urgent }} 件）
          </span>
        </div>
      </div>
      <p class="reorder-note">
        在庫推移が「基準日〜基準日＋リードタイム＋見込日数」の間に 0 未満となる部品を表示します。
        推奨注文数は欠品予定日の注文本数に加算されます（仕入先フィルターは一覧と共通）。
      </p>

      <el-table
        ref="reorderTableRef"
        v-loading="reorderLoading"
        :data="reorderList"
        row-key="target_row_id"
        max-height="460"
        class="reorder-table"
        @selection-change="(rows: any[]) => (reorderSelection = rows as ReorderRow[])"
      >
        <el-table-column type="selection" width="40" align="center" />
        <el-table-column label="部品" min-width="200">
          <template #default="{ row }">
            <div class="reorder-part" @click="openPartChart(row)">
              <span class="reorder-part__name">{{ row.part_name }}</span>
              <span class="reorder-part__cd">{{ row.part_cd }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="supplier_name" label="仕入先" width="130" show-overflow-tooltip />
        <el-table-column prop="lead_time" label="LT(日)" width="70" align="center" />
        <el-table-column label="基準日推移" width="95" align="right">
          <template #default="{ row }">
            <span :class="{ 'negative-number': row.base_stock_trend < 0 }">
              {{ formatNumber(row.base_stock_trend) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="shortage_date" label="欠品予定日" width="105" align="center" />
        <el-table-column label="最小推移" width="120" align="right">
          <template #default="{ row }">
            <span class="negative-number">{{ formatNumber(row.min_stock_trend) }}</span>
            <span class="reorder-sub">{{ row.min_stock_trend_date.slice(5) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="発注期限" width="125" align="center">
          <template #default="{ row }">
            <span :class="{ 'negative-number': row.urgent }">{{ row.order_deadline }}</span>
            <el-tag v-if="row.urgent" type="danger" size="small" effect="dark" class="reorder-tag">
              緊急
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="既存注文" width="80" align="right">
          <template #default="{ row }">{{ formatValue(row.target_order_quantity) }}</template>
        </el-table-column>
        <el-table-column label="推奨注文数" width="110" align="center">
          <template #default="{ row }">
            <el-input-number
              v-model="row.apply_quantity"
              :min="0"
              :max="999999"
              :precision="0"
              :controls="false"
              size="small"
              class="order-quantity-input"
            />
          </template>
        </el-table-column>
        <el-table-column label="参考金額" width="110" align="right">
          <template #default="{ row }">
            {{ formatCurrency(reorderAmount(row)) }}
          </template>
        </el-table-column>
      </el-table>

      <template #footer>
        <div class="reorder-footer">
          <span class="reorder-footer__total">
            選択 {{ reorderSelection.length }} 件 ／ 参考金額
            {{ formatCurrency(reorderSelection.reduce((s, r) => s + reorderAmount(r), 0)) }}
          </span>
          <el-button @click="reorderDialogVisible = false">閉じる</el-button>
          <el-button
            type="primary"
            :loading="reorderApplying"
            :disabled="!reorderSelection.length"
            @click="applyReorderSuggestions"
          >
            <el-icon><Check /></el-icon>
            選択した提案を注文に反映
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 部品在庫推移グラフ -->
    <el-drawer
      v-model="chartDrawerVisible"
      size="62%"
      class="part-chart-drawer"
      :title="chartPart ? `${chartPart.part_name}（${chartPart.part_cd}）` : '在庫推移'"
    >
      <div class="part-chart">
        <div class="part-chart__toolbar">
          <el-date-picker
            v-model="chartRange"
            type="daterange"
            range-separator="~"
            start-placeholder="開始日"
            end-placeholder="終了日"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            :clearable="false"
            size="small"
            style="width: 240px"
            @change="loadPartChart"
          />
          <el-radio-group v-model="chartPreset" size="small" @change="applyChartPreset">
            <el-radio-button label="short" value="short">前1週〜後2週</el-radio-button>
            <el-radio-button label="mid" value="mid">前2週〜後1ヶ月</el-radio-button>
            <el-radio-button label="long" value="long">前1ヶ月〜後3ヶ月</el-radio-button>
          </el-radio-group>
        </div>

        <div class="part-chart__kpis">
          <div class="part-chart__kpi">
            <span class="part-chart__kpi-label">仕入先</span>
            <span class="part-chart__kpi-value">{{ chartPart?.supplier_name || '—' }}</span>
          </div>
          <div class="part-chart__kpi">
            <span class="part-chart__kpi-label">リードタイム</span>
            <span class="part-chart__kpi-value">{{ chartKpis.leadTime }} 日</span>
          </div>
          <div class="part-chart__kpi">
            <span class="part-chart__kpi-label">期間内 最小在庫推移</span>
            <span class="part-chart__kpi-value" :class="{ 'negative-number': chartKpis.minTrend < 0 }">
              {{ formatNumber(chartKpis.minTrend) }}
              <small v-if="chartKpis.minTrendDate">（{{ chartKpis.minTrendDate }}）</small>
            </span>
          </div>
          <div class="part-chart__kpi">
            <span class="part-chart__kpi-label">欠品予定日</span>
            <span class="part-chart__kpi-value" :class="{ 'negative-number': !!chartKpis.shortageDate }">
              {{ chartKpis.shortageDate || 'なし' }}
            </span>
          </div>
          <div class="part-chart__kpi">
            <span class="part-chart__kpi-label">期間内 使用数／注文本数</span>
            <span class="part-chart__kpi-value">
              {{ formatNumber(chartKpis.totalUsage) }} ／ {{ formatNumber(chartKpis.totalOrder) }}
            </span>
          </div>
        </div>

        <div v-loading="chartLoading" class="part-chart__canvas">
          <ChartWrapper
            v-if="chartDays.length"
            :data="chartData"
            :options="chartOptions"
            height="420px"
          />
          <el-empty v-else-if="!chartLoading" description="期間内のデータがありません" />
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ShoppingCart,
  Refresh,
  Box,
  Money,
  Search,
  Operation,
  DocumentAdd,
  ArrowLeft,
  ArrowRight,
  Printer,
  User,
  EditPen,
  Close,
  Calendar,
  InfoFilled,
  Plus,
  Check,
  List,
  Goods,
  Coin,
  TrendCharts,
  DataLine,
  Bell,
} from '@element-plus/icons-vue'
import request from '@/utils/request'
import {
  syncPartStockFromMaster,
  getPartStockSupplierNames,
  getPartStockList,
  updatePartStock,
  createPartStock,
  saveMaruichiPartOrderPdf,
  cancelPartStockOrder,
  getPartReorderSuggestions,
} from '@/api/part'
import type { PartStockListSummary, PartReorderSuggestion } from '@/api/part'
import ChartWrapper from '@/components/ChartWrapper.vue'
import { getPartList } from '@/api/master/partMaster'
import html2canvas from 'html2canvas'
import { jsPDF } from 'jspdf'
import { MARUICHI_ORDER_SHEET_STYLES } from '@/utils/maruichiOrderSheetStyles'
import { calculatePartStock } from '@/api/partStockCalculation'
import { generatePartStockData } from '@/api/partDataGeneration'
import { updatePartQuantities } from '@/api/partStockUpdate'
import type { PartQuantityUpdate } from '@/api/partStockUpdate'
import { usePurchaseOperationPermission } from '@/composables/usePurchaseOperationPermission'
import { guardPurchaseOperation } from '@/utils/purchaseOperationGuard'

const { canCreate, canEdit, canDelete, canExport, canApprove } = usePurchaseOperationPermission()


// 定义类型接口
interface PartOrderItem {
  id: number
  part_cd: string
  part_name: string
  date: string
  /** parts.status（0 の行は一覧から除外） */
  part_master_status?: number
  current_stock: number
  unit: string
  unit_price: number
  supplier_cd: string
  supplier_name: string
  lead_time: number
  last_updated: string
  created_at: string
  pieces_per_bundle: number
  standard_spec: string
  remarks: string
  order_amount: number
  usage_quantity: number
  manual_usage: number
  usage_plan_qty: number
  stock_trend: number
  order_quantity: number
  order_bundle_quantity: number
  /** 旧材料 API 等との混在レスポンス互換 */
  material_name?: string
  material_cd?: string
}

interface SupplierOption {
  label: string
  value: string
}

interface PartMasterOption {
  part_cd: string
  part_name: string
  supplier_cd?: string
  supplier_name?: string
  category?: string
  uom?: string
  standard_spec?: string
  unit_price?: number
  pieces_per_bundle?: number
  unit?: string
  lead_time?: number
}

interface InitialStockItem {
  id: number
  date: string
  supplier_name: string
  part_cd: string
  part_name: string
  initial_stock: number
  adjustment_quantity: number
}

// 响应式数据
const loading = ref(false)
const stockCalculationLoading = ref(false)
const dataGenerationLoading = ref(false)
const dataGenerationStartDate = ref('')
const dataGenerationEndDate = ref('')
const dataGenerationDialogVisible = ref(false)
const printConfirmDialogVisible = ref(false)
const printPdfSaving = ref(false)
const manualOrderDialogVisible = ref(false)
const manualOrderLoading = ref(false)
const partSearchLoading = ref(false)
const partOptions = ref<PartMasterOption[]>([])
const selectedPart = ref<PartMasterOption | null>(null)
const manualOrderFormRef = ref()
const tableData = ref<PartOrderItem[]>([])
const lastSavedManualUsage = new Map<number, number>()
const initialStockData = ref<InitialStockItem[]>([])
/** 部品注文履歴タブ用（期間・キーワードで material_stock かつ注文数>0） */
const orderHistoryData = ref<PartOrderItem[]>([])
const activeTab = ref('stock') // デフォルトは部品日別在庫タブ
const partMasterSyncLoading = ref(false)

// 検索表单（默认日期为「日本时间」的当天）
const getTodayJapanStr = () => {
  const now = new Date()
  const japanTime = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Tokyo' }))
  const year = japanTime.getFullYear()
  const month = String(japanTime.getMonth() + 1).padStart(2, '0')
  const day = String(japanTime.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

/** 納入日（検索日付範囲の開始日＝画面の納入日）→ YYYYMMDD。共有フォルダの PDF ファイル名用 */
const getNonyuDateYmdForPdf = (): string | null => {
  const raw = searchForm.dateRange?.[0]?.trim() ?? ''
  const m = raw.match(/^(\d{4})-(\d{2})-(\d{2})$/)
  if (m) return `${m[1]}${m[2]}${m[3]}`
  return null
}

const searchForm = reactive({
  /** 空＝全件。部品マスタから選択（部品CD） */
  part_cd: '',
  dateRange: [getTodayJapanStr(), getTodayJapanStr()] as string[], // デフォルトは日本時間の当日
  supplier: [] as string[],
})

// 分页数据
const pagination = reactive({
  page: 1,
  page_size: 50,
  total: 0,
})

// 选项数据
const supplierOptions = ref<SupplierOption[]>([])
const partSelectOptions = ref<{ label: string; value: string }[]>([])
const partSelectLoading = ref(false)
let partSearchTimer: ReturnType<typeof setTimeout> | null = null

/** parts.status が 0 の行を除外（API 未付与の旧レスポンスはそのまま通す） */
const excludePartsStatusZero = (item: Record<string, unknown>): boolean => {
  const s = item.part_master_status ?? item.status
  if (s === undefined || s === null) return true
  return Number(s) !== 0
}

/** 一覧取得の共通クエリ（期間・部品・仕入先） */
const buildPartStockListParams = (extra?: { order_only?: boolean }): Record<string, unknown> => {
  const p: Record<string, unknown> = {
    page: pagination.page,
    pageSize: pagination.page_size,
  }
  const cd = searchForm.part_cd?.trim()
  if (cd) p.part_cd = cd
  if (searchForm.supplier && searchForm.supplier.length > 0) {
    p.suppliers = searchForm.supplier.join(',')
  }
  if (searchForm.dateRange && searchForm.dateRange.length === 2) {
    p.start_date = searchForm.dateRange[0]
    p.end_date = searchForm.dateRange[1]
  }
  if (extra?.order_only) p.order_only = true
  return p
}

// 打印表单数据
const printForm = reactive({
  recipientCompany: '丸一鋼管株式会社 御中',
  recipientPersons: '鈴木様 村松様 只井様',
  approver: '篠田',
  issuer: '趙',
  note1: '1.支払期日には法定税率による消費税額及び地方消費税分を加算して支払います。',
  note2:
    '2.支払期日・支払方法・検査完了期日・有償支給原材料代金の決済期日及び方法については、令和8年7月1日の「支払方法等について」によります。',
})

// 手入力部品注文フォームデータ
const manualOrderForm = reactive({
  date: '',
  part_cd: '',
  part_name: '',
  order_quantity: 0,
  unit: '',
  unit_price: 0,
  supplier_cd: '',
  supplier_name: '',
  standard_spec: '',
  pieces_per_bundle: 0,
  lead_time: 0,
  remarks: '',
})

// 手入力フォーム検証ルール
const manualOrderRules = {
  date: [{ required: true, message: '日付を選択してください', trigger: 'change' }],
  part_cd: [{ required: true, message: '部品を選択してください', trigger: 'change' }],
  order_quantity: [
    { required: true, message: '注文本数を入力してください', trigger: 'blur' },
    {
      type: 'number' as const,
      min: 0,
      message: '注文本数は0以上である必要があります',
      trigger: 'blur',
    },
  ],
}

// 計算プロパティ - 現在データは直接バックエンドからフィルタリングされ、ここでは表示用のみ
const filteredTableData = computed(() => {
  if (activeTab.value === 'initial') {
    return initialStockData.value
  }
  if (activeTab.value === 'orderHistory') {
    return orderHistoryData.value
  }
  return tableData.value
})

// 統計カード：サーバー側の全件集計 ＋ 表示中ページで編集された差分
interface PageSums {
  currentStock: number
  usage: number
  orderQty: number
  orderValue: number
}

const sumPageRows = (rows: Partial<PartOrderItem>[]): PageSums =>
  rows.reduce<PageSums>(
    (acc, row) => {
      const oq = Number(row.order_quantity) || 0
      acc.currentStock += Number(row.current_stock) || 0
      acc.usage += (Number(row.usage_quantity) || 0) + (Number(row.manual_usage) || 0)
      if (oq > 0) {
        acc.orderQty += oq
        acc.orderValue += Number(row.order_amount) || 0
      }
      return acc
    },
    { currentStock: 0, usage: 0, orderQty: 0, orderValue: 0 },
  )

const serverSummary = ref<PartStockListSummary | null>(null)
const pageBaseline = ref<PageSums>(sumPageRows([]))

const applyServerSummary = (summary: PartStockListSummary | undefined, rows: Partial<PartOrderItem>[]) => {
  serverSummary.value = summary ?? null
  pageBaseline.value = sumPageRows(rows)
}

const stats = computed(() => {
  const s = serverSummary.value
  const editable = ['stock', 'usage', 'order'].includes(activeTab.value)
  const live = editable ? sumPageRows(tableData.value) : pageBaseline.value
  const base = pageBaseline.value
  return {
    totalParts: s?.part_count ?? 0,
    totalCurrentStock: (s?.total_current_stock ?? 0) + live.currentStock - base.currentStock,
    averageUnitPrice: s?.avg_unit_price ?? 0,
    totalUsageQuantity: (s?.total_usage ?? 0) + live.usage - base.usage,
    totalOrderQuantity: (s?.total_order_quantity ?? 0) + live.orderQty - base.orderQty,
    totalOrderValue: (s?.total_order_amount ?? 0) + live.orderValue - base.orderValue,
  }
})

// 手入力：注文本数×梱本数×単価（参考金額）
const calculatedAmount = computed(() => {
  const q = manualOrderForm.order_quantity || 0
  const ppb = manualOrderForm.pieces_per_bundle || 1
  if (q <= 0) return 0
  return q * ppb * (manualOrderForm.unit_price || 0)
})

const mapPartStockRow = (item: any): PartOrderItem => {
  const usage_quantity = item.planned_usage || 0
  const manual_usage = Number(item.manual_usage) || 0
  const order_quantity = item.order_quantity || 0
  const ppb = Number(item.pieces_per_bundle) || 1
  let order_bundle_quantity = 0
  let order_amount = 0
  if (order_quantity > 0) {
    order_bundle_quantity = order_quantity * ppb
    order_amount = order_bundle_quantity * (Number(item.unit_price) || 0)
  }
  return {
    ...item,
    usage_quantity,
    manual_usage,
    usage_plan_qty: Number(item.usage_plan_qty) || 0,
    stock_trend: Number(item.stock_trend) || 0,
    order_quantity,
    order_bundle_quantity,
    order_amount,
  }
}

// 方法
const fetchData = async () => {
  try {
    loading.value = true
    const apiParams = buildPartStockListParams()
    console.log('发送到后端的参数:', apiParams)
    const result = await getPartStockList(apiParams)
    const list = (result as any)?.data?.list ?? []
    const total = (result as any)?.data?.total ?? 0

    if ((result as any)?.success !== false && list) {
      const filtered = list.filter((item: any) => excludePartsStatusZero(item))
      tableData.value = filtered.map((item: any) => mapPartStockRow(item))
      lastSavedManualUsage.clear()
      for (const row of tableData.value) {
        if (row.id) lastSavedManualUsage.set(row.id, Number(row.manual_usage) || 0)
      }
      pagination.total = total
      applyServerSummary((result as any)?.data?.summary, tableData.value)
    } else {
      ElMessage.error('データ取得に失敗しました')
    }
  } catch (error) {
    console.error('データ取得に失敗しました:', error)
    ElMessage.error('データ取得に失敗しました')
  } finally {
    loading.value = false
  }
}

/** 指定期間・条件で注文数>0の material_stock 一覧（部品注文履歴タブ） */
const fetchOrderHistory = async () => {
  if (!searchForm.dateRange || searchForm.dateRange.length !== 2) {
    orderHistoryData.value = []
    pagination.total = 0
    ElMessage.warning('期間を選択してください')
    return
  }
  try {
    loading.value = true
    const apiParams = buildPartStockListParams({ order_only: true })
    const result = await getPartStockList(apiParams)
    const list = (result as any)?.data?.list ?? []
    const total = (result as any)?.data?.total ?? 0
    if ((result as any)?.success !== false && list) {
      const filtered = list.filter((item: any) => excludePartsStatusZero(item))
      orderHistoryData.value = filtered.map((item: any) => mapPartStockRow(item))
      pagination.total = total
      applyServerSummary((result as any)?.data?.summary, orderHistoryData.value)
    } else {
      ElMessage.error('注文履歴の取得に失敗しました')
      orderHistoryData.value = []
      pagination.total = 0
    }
  } catch (error) {
    console.error('注文履歴の取得に失敗しました:', error)
    ElMessage.error('注文履歴の取得に失敗しました')
    orderHistoryData.value = []
    pagination.total = 0
  } finally {
    loading.value = false
  }
}

// 初期在庫管理データを取得 - 部品日別在庫と同じデータソースを使用
const fetchInitialStockData = async () => {
  try {
    loading.value = true
    const apiParams = buildPartStockListParams()
    console.log('初期在庫管理データを取得、パラメータ:', apiParams)

    try {
      const result = await getPartStockList(apiParams)
      const list = (result as any)?.data?.list ?? []
      if ((result as any)?.success !== false && list.length >= 0) {
        const filtered = list.filter((item: any) => excludePartsStatusZero(item))
        initialStockData.value = filtered.map((item: any) => {
          // material_stockデータを初期在庫管理に必要な形式にマッピング
          return {
            ...item,
            // initial_stockフィールドを直接使用、存在しない場合はcurrent_stockをデフォルト値として使用
            initial_stock:
              item.initial_stock !== undefined ? item.initial_stock : item.current_stock || 0,
            // adjustment_quantityフィールドを直接使用
            adjustment_quantity: item.adjustment_quantity || 0,
          }
        })
        pagination.total = (result as any)?.data?.total ?? list.length
        applyServerSummary((result as any)?.data?.summary, filtered)
        console.log('初期在庫管理データ取得成功:', initialStockData.value.length, '件')
      } else {
        ElMessage.error('初期在庫管理データ取得に失敗しました')
      }
    } catch (apiError: any) {
      console.warn(
        '初期在庫管理API呼び出し失敗、部品日別在庫データをバックアップとして使用:',
        apiError,
      )

      try {
        const fallbackResult = await getPartStockList(buildPartStockListParams())
        const fallbackList = (fallbackResult as any)?.data?.list ?? []
        if (fallbackList.length >= 0) {
          const fbFiltered = fallbackList.filter((item: any) => excludePartsStatusZero(item))
          initialStockData.value = fbFiltered.map((item: any) => ({
            ...item,
            // current_stockをinitial_stockの初期値として使用
            initial_stock: item.current_stock || 0,
            // 調整数はデフォルトで0
            adjustment_quantity: 0,
          }))
          pagination.total = (fallbackResult as any)?.data?.total ?? fallbackList.length
          applyServerSummary((fallbackResult as any)?.data?.summary, fbFiltered)
          ElMessage.info('初期在庫管理機能は開発中です。材料在庫データを表示しています。')
          console.log('バックアップデータを使用:', initialStockData.value.length, '件')
        } else {
          throw new Error('バックアップデータ取得も失敗')
        }
      } catch (fallbackError) {
        console.error('バックアップデータ取得も失敗:', fallbackError)
        ElMessage.error(
          '初期在庫管理データ取得に失敗しました。しばらくしてから再試行してください。',
        )
        initialStockData.value = []
        pagination.total = 0
      }
    }
  } catch (error) {
    console.error('初期在庫管理データ取得に失敗しました:', error)
    ElMessage.error('初期在庫管理データ取得に失敗しました')
    initialStockData.value = []
    pagination.total = 0
  } finally {
    loading.value = false
  }
}

const refreshListForActiveTab = () => {
  if (activeTab.value === 'initial') {
    fetchInitialStockData()
  } else if (activeTab.value === 'orderHistory') {
    fetchOrderHistory()
  } else {
    fetchData()
    if (activeTab.value === 'order') loadReorderSuggestions(true)
  }
}

// 仕入先选项来自 /api/material/stock/supplier-names（material_stock.supplier_name 去重、名称排序）。label/value 均为 supplier_name（与列表筛选 suppliers 一致）
const fetchSupplierOptions = async () => {
  try {
    const result = await getPartStockSupplierNames()
    const raw = result?.data ?? []
    supplierOptions.value = raw
      .filter((name): name is string => typeof name === 'string' && !!name.trim())
      .map((name) => ({ label: name, value: name }))
  } catch (error) {
    console.error('仕入先オプションの取得に失敗しました:', error)
    supplierOptions.value = []
  }
}

// 设置日期范围快捷按钮（today=日本时间的当天）
const setDateRange = (days: number) => {
  // days=0 时，无论当前选择什么日期，强制设为「日本时间的今日」
  if (days === 0) {
    const today = getTodayJapanStr()
    searchForm.dateRange = [today, today]
    pagination.page = 1
    refreshListForActiveTab()
    return
  }

  // 获取当前选择的日期，如果没有选择则使用「日本时间」的当天日期
  let currentDate: Date
  if (searchForm.dateRange && searchForm.dateRange.length === 2) {
    // 已选日期时，以当前开始日为基準
    currentDate = new Date(searchForm.dateRange[0])
  } else {
    // 未选日期时，以日本时间的今日为基準
    const now = new Date()
    currentDate = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Tokyo' }))
  }

  // 在当前日期基础上加减天数（单位：日）
  currentDate.setDate(currentDate.getDate() + days)

  // 按 YYYY-MM-DD 组装日期字符串（不使用 toISOString，避免时区偏移导致的前后一天问题）
  const year = currentDate.getFullYear()
  const month = String(currentDate.getMonth() + 1).padStart(2, '0')
  const day = String(currentDate.getDate()).padStart(2, '0')
  const dateStr = `${year}-${month}-${day}`

  searchForm.dateRange = [dateStr, dateStr]
  pagination.page = 1
  refreshListForActiveTab()
}

// 设置日期为当月月初1号（日本时区）
const handleSetMonthStart = () => {
  // 获取日本时区的当前日期
  const now = new Date()
  const japanTime = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Tokyo' }))

  const year = japanTime.getFullYear()
  const month = japanTime.getMonth()

  // 格式化为YYYY-MM-DD格式（当月1号）
  const monthStartStr = `${year}-${String(month + 1).padStart(2, '0')}-01`

  // 设置日期范围为当月1号
  searchForm.dateRange = [monthStartStr, monthStartStr]
  pagination.page = 1

  refreshListForActiveTab()

  ElMessage.success(`日付を当月月初（${monthStartStr}）に設定しました`)
}

const loadPartDropdownOptions = async (query: string) => {
  partSelectLoading.value = true
  try {
    const res = await getPartList({
      keyword: query?.trim() || undefined,
      status: 1,
      page: 1,
      pageSize: 200,
    })
    const list = res?.data?.list ?? []
    partSelectOptions.value = list.map((p) => ({
      value: p.part_cd,
      label: `${p.part_cd} ${p.part_name || ''}`.trim(),
    }))
  } catch {
    partSelectOptions.value = []
  } finally {
    partSelectLoading.value = false
  }
}

const remoteFetchParts = (query: string) => {
  if (partSearchTimer) clearTimeout(partSearchTimer)
  partSearchTimer = setTimeout(() => {
    loadPartDropdownOptions(query || '')
  }, 300)
}

const onPartSelectVisible = (open: boolean) => {
  if (open && partSelectOptions.value.length === 0) {
    loadPartDropdownOptions('')
  }
}

const handlePartFilterChange = () => {
  pagination.page = 1
  refreshListForActiveTab()
}

// 仕入先选择搜索
const handleSupplierSearch = () => {
  pagination.page = 1
  refreshListForActiveTab()
}

// 備考編集処理（部品在庫メイン）
const handleRemarksChange = async (row: any) => {
  if (!guardPurchaseOperation(canEdit)) return

  try {
    console.log('備考更新:', row.id, row.remarks)

    const body = { remarks: row.remarks ?? '' }
    const response = await updatePartStock(row.id, body)

    if ((response as any)?.success) {
      ElMessage.success('備考を更新しました')
    } else {
      ElMessage.error('備考の更新に失敗しました')
    }
  } catch (error) {
    console.error('備考更新失敗:', error)
    ElMessage.error('備考の更新に失敗しました')
  }
}

// 初期在庫変化処理
const handleInitialStockChange = async (row: InitialStockItem) => {
  if (!guardPurchaseOperation(canEdit)) return

  try {
    console.log('初期在庫更新:', row.part_cd, row.initial_stock)

    // 部品日別在庫と同じAPIを使用してデータを更新
    const updateParams: PartQuantityUpdate = {
      part_cd: row.part_cd,
      date: row.date,
      initial_stock: row.initial_stock || 0, // initial_stockフィールドを更新
    }

    try {
      const response = await updatePartQuantities(updateParams)

      if (response && (response as any).success) {
        console.log(`材料 ${row.part_cd} の初期在庫を更新しました`)
        ElMessage.success('初期在庫を更新しました')
      } else {
        const errorMessage = (response as any)?.message || '不明なエラー'
        console.error(`材料 ${row.part_cd} の初期在庫更新失敗:`, errorMessage)
        ElMessage.warning(`保存に失敗しました: ${errorMessage}`)
      }
    } catch (apiError: any) {
      console.warn('初期在庫更新APIは未実装のため代替処理を使用:', apiError)
      ElMessage.info('初期在庫管理機能は開発中です。変更は一時的に保存されています。')
    }
  } catch (error: any) {
    console.error(`材料 ${row.part_cd} の初期在庫更新エラー:`, error)
    ElMessage.error(`保存中にエラーが発生しました: ${error.message || '不明なエラー'}`)
  }
}

// 調整数変更処理
const handleAdjustmentQuantityChange = async (row: InitialStockItem) => {
  if (!guardPurchaseOperation(canEdit)) return

  try {
    console.log('更新調整数:', row.part_cd, row.adjustment_quantity)

    // 部品日別在庫と同じAPIで更新
    const updateParams: PartQuantityUpdate = {
      part_cd: row.part_cd,
      date: row.date,
      adjustment_quantity: row.adjustment_quantity || 0,
    }

    try {
      const response = await updatePartQuantities(updateParams)

      if (response && (response as any).success) {
        console.log(`材料 ${row.part_cd} の調整数を更新しました`)
        ElMessage.success('調整数を更新しました')
      } else {
        const errorMessage = (response as any)?.message || '不明なエラー'
        console.error(`材料 ${row.part_cd} の調整数更新失敗:`, errorMessage)
        ElMessage.warning(`保存に失敗しました: ${errorMessage}`)
      }
    } catch (apiError: any) {
      console.warn('調整数更新APIは未実装のため、代替処理を使用:', apiError)
      ElMessage.info('初期在庫管理機能は開発中です。変更は一時的に保存されています。')
    }
  } catch (error: any) {
    console.error(`更新材料 ${row.part_cd} 的調整数时发生错误:`, error)
    ElMessage.error(`保存中にエラーが発生しました: ${error.message || '不明なエラー'}`)
  }
}

// 日期范围选择搜索
const handleDateRangeSearch = () => {
  pagination.page = 1
  refreshListForActiveTab()
}

const handleSizeChange = (size: number) => {
  pagination.page_size = size
  pagination.page = 1
  refreshListForActiveTab()
}

const handleCurrentChange = (page: number) => {
  pagination.page = page
  refreshListForActiveTab()
}

// Tab切换处理
// 格式化数值，如果为0则不显示
const formatValue = (value: number | null | undefined): string => {
  if (value === null || value === undefined || value === 0) {
    return ''
  }
  return Number(value).toLocaleString('ja-JP')
}

// 統計カード用：0 も表示する千区切り
const formatNumber = (value: number | null | undefined): string => {
  const n = Number(value)
  return (Number.isFinite(n) ? n : 0).toLocaleString('ja-JP')
}

const isNegative = (value: number | string | null | undefined): boolean => {
  const n = Number(value)
  return Number.isFinite(n) && n < 0
}

const comparePartName = (a: { part_name?: string | null }, b: { part_name?: string | null }) =>
  (a.part_name || '').localeCompare(b.part_name || '', 'ja-JP', {
    numeric: true,
    sensitivity: 'base',
  })

// 格式化货币，添加日本円マーク和3位数逗号
const formatCurrency = (num: number): string => {
  return `¥${Math.round(num).toLocaleString('ja-JP')}`
}

/** 部品注文履歴テーブル合計行（表示中ページの行のみ集計） */
const getOrderHistorySummaries = (param: {
  columns: { property?: string }[]
  data: PartOrderItem[]
}) => {
  const { columns, data } = param
  const sums: string[] = []
  columns.forEach((column, index) => {
    const prop = column.property
    if (index === 0) {
      sums[index] = '合計'
      return
    }
    if (prop === 'part_cd') {
      sums[index] = data.length ? `${data.length}件` : ''
      return
    }
    if (prop === 'order_quantity') {
      const t = data.reduce((s, r) => s + (Number(r.order_quantity) || 0), 0)
      sums[index] = t ? t.toLocaleString('ja-JP') : ''
      return
    }
    if (prop === 'order_amount') {
      const t = data.reduce((s, r) => s + Math.round(Number(r.order_amount) || 0), 0)
      sums[index] = t ? formatCurrency(t) : ''
      return
    }
    sums[index] = ''
  })
  return sums
}

const handleTabChange = (tabName: string | number) => {
  activeTab.value = String(tabName)
  refreshListForActiveTab()
}

/** 数字入力: 0 は空欄表示 */
const emptyIfZero = (value: number | null | undefined): number | null => {
  const n = Number(value)
  if (!Number.isFinite(n) || n === 0) return null
  return n
}

/** el-input-number の ↑↓ / PageUp/Down による値改変を防止（手入力のみ） */
const preventNumberSpinnerKeys = (e: Event) => {
  const ke = e as KeyboardEvent
  if (
    ke.key === 'ArrowUp' ||
    ke.key === 'ArrowDown' ||
    ke.key === 'PageUp' ||
    ke.key === 'PageDown'
  ) {
    ke.preventDefault()
    ke.stopPropagation()
  }
}

/** 表内入力欄で Enter → 次の行の同じ列、Shift+Enter → 前の行へフォーカス移動（IME 変換中は無視） */
const handleTableEnterNav = (e: KeyboardEvent) => {
  if (e.isComposing || e.keyCode === 229) return
  const target = e.target as HTMLElement | null
  if (!target || target.tagName !== 'INPUT' || target.closest('.el-select')) return
  const td = target.closest('td.el-table__cell') as HTMLTableCellElement | null
  let tr = td?.parentElement as HTMLTableRowElement | null
  if (!td || !tr || !tr.closest('.el-table__body')) return

  const colIndex = td.cellIndex
  const step = (row: HTMLTableRowElement) =>
    (e.shiftKey ? row.previousElementSibling : row.nextElementSibling) as HTMLTableRowElement | null
  for (tr = step(tr); tr; tr = step(tr)) {
    const input = tr.cells[colIndex]?.querySelector<HTMLInputElement>('input:not([disabled])')
    if (input) {
      input.focus()
      input.select()
      tr.scrollIntoView({ block: 'nearest' })
      return
    }
  }
  target.blur()
}

const commitQty = (val: number | null | undefined): number => {
  if (val === null || val === undefined) return 0
  const n = Number(val)
  return Number.isFinite(n) ? n : 0
}

/** 同一部品の現在在庫を一覧へ反映（手動使用数・注文本数更新後） */
const patchCurrentStockForPart = async (partCd: string) => {
  if (!partCd) return
  try {
    const apiParams: Record<string, unknown> = {
      page: 1,
      pageSize: 500,
      part_cd: partCd,
    }
    if (searchForm.dateRange && searchForm.dateRange.length === 2) {
      apiParams.start_date = searchForm.dateRange[0]
      apiParams.end_date = searchForm.dateRange[1]
    }
    const result = await getPartStockList(apiParams)
    const list = (result as any)?.data?.list ?? []
    if (!Array.isArray(list) || list.length === 0) return
    const byId = new Map<number, any>(list.map((item: any) => [item.id, item]))
    for (const row of tableData.value) {
      const fresh = byId.get(row.id)
      if (!fresh) continue
      if (fresh.current_stock !== undefined) row.current_stock = fresh.current_stock
      if (fresh.stock_trend !== undefined) row.stock_trend = Number(fresh.stock_trend) || 0
    }
  } catch (error) {
    console.warn('現在在庫の再取得に失敗:', error)
  }
}

const handleManualUsageChange = async (row: PartOrderItem, committed?: number | null) => {
  if (!guardPurchaseOperation(canEdit)) return
  const next = commitQty(committed)
  row.manual_usage = next
  if (row.id && lastSavedManualUsage.get(row.id) === next) return

  try {
    const response = await updatePartStock(row.id, { manual_usage: next })
    if ((response as any)?.success) {
      ElMessage.success('手動使用数を更新しました')
      lastSavedManualUsage.set(row.id, next)
      const data = (response as any)?.data
      if (data?.current_stock !== undefined) {
        row.current_stock = data.current_stock
      }
      await patchCurrentStockForPart(row.part_cd)
    } else {
      ElMessage.error('手動使用数の更新に失敗しました')
    }
  } catch (error: any) {
    console.error('手動使用数更新失敗:', error)
    ElMessage.error(`手動使用数の更新に失敗しました: ${error.message || 'ネットワークエラー'}`)
  }
}

const handleOrderQuantityChange = async (row: PartOrderItem) => {
  if (!guardPurchaseOperation(canEdit)) return

  const ppb = Number(row.pieces_per_bundle) || 1
  if (row.order_quantity > 0) {
    row.order_bundle_quantity = row.order_quantity * ppb
    row.order_amount = row.order_bundle_quantity * (Number(row.unit_price) || 0)
  } else {
    row.order_bundle_quantity = 0
    row.order_amount = 0
  }

  await saveQuantityToDatabase(row)
}

// 保存数量到数据库
const saveQuantityToDatabase = async (row: PartOrderItem) => {
  if (!guardPurchaseOperation(canEdit)) return

  try {
    console.log('开始保存数量到数据库:', {
      part_cd: row.part_cd,
      date: row.date,
      usage_quantity: row.usage_quantity || 0,
      order_quantity: row.order_quantity || 0,
      order_bundle_quantity: row.order_bundle_quantity || 0,
      order_amount: row.order_amount || 0,
    })

    const response = await updatePartQuantities({
      part_cd: row.part_cd,
      date: row.date,
      order_quantity: row.order_quantity || 0,
      order_bundle_quantity: row.order_bundle_quantity || 0,
      order_amount: row.order_amount || 0,
    })

    console.log('API响应:', response)

    if (response && response.success) {
      console.log(`成功保存材料 ${row.part_cd} 的数量到数据库`)
      await patchCurrentStockForPart(row.part_cd)
    } else {
      const errorMessage = response?.message || '不明なエラー'
      console.error(`保存材料 ${row.part_cd} 的数量失败:`, errorMessage)
      ElMessage.warning(`保存に失敗しました: ${errorMessage}`)
    }
  } catch (error: any) {
    console.error(`保存材料 ${row.part_cd} 的数量时发生错误:`, error)
    ElMessage.error(`保存中にエラーが発生しました: ${error.message || '不明なエラー'}`)
  }
}

/** 注文取消（行ごと削除されるのは手入力で追加された重複行のみ） */
const handleCancelOrder = async (row: PartOrderItem) => {
  if (!guardPurchaseOperation(canDelete)) return
  try {
    await ElMessageBox.confirm(
      `${row.date}　${row.part_name}（${row.part_cd}）\n注文本数 ${formatNumber(row.order_quantity)} を取り消しますか？`,
      '注文取消確認',
      { confirmButtonText: '取消', cancelButtonText: 'キャンセル', type: 'warning' },
    )
  } catch {
    return
  }
  try {
    const res = await cancelPartStockOrder(row.id)
    const action = res?.data?.action
    ElMessage.success(action === 'deleted' ? '手入力の注文行を削除しました' : '注文を取り消しました')
    await fetchData()
  } catch (error: any) {
    console.error('注文取消に失敗しました:', error)
    ElMessage.error(error?.response?.data?.detail || '注文取消に失敗しました')
  }
}

const addDaysStr = (base: string, days: number): string => {
  const [y, m, d] = base.split('-').map(Number)
  const dt = new Date(y, m - 1, d + days)
  return `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, '0')}-${String(dt.getDate()).padStart(2, '0')}`
}

// ─────────────────────────────────────────────
// 発注提案
// ─────────────────────────────────────────────
type ReorderRow = PartReorderSuggestion & { apply_quantity: number }

const reorderDialogVisible = ref(false)
const reorderLoading = ref(false)
const reorderApplying = ref(false)
const reorderList = ref<ReorderRow[]>([])
const reorderSelection = ref<ReorderRow[]>([])
const reorderTableRef = ref()
const reorderForm = reactive({ baseDate: getTodayJapanStr(), horizonDays: 14 })

const reorderBadge = computed(() => ({
  count: reorderList.value.length,
  urgent: reorderList.value.filter((r) => r.urgent).length,
}))

const reorderAmount = (row: { apply_quantity?: number; pieces_per_bundle?: number; unit_price?: number }) =>
  (row.apply_quantity || 0) * (row.pieces_per_bundle || 1) * (row.unit_price || 0)

const loadReorderSuggestions = async (silent = false) => {
  reorderLoading.value = true
  try {
    const res = await getPartReorderSuggestions({
      base_date: reorderForm.baseDate,
      horizon_days: reorderForm.horizonDays,
      part_cd: searchForm.part_cd?.trim() || undefined,
      suppliers: searchForm.supplier.length ? searchForm.supplier.join(',') : undefined,
    })
    reorderList.value = (res?.data?.list ?? []).map((item) => ({
      ...item,
      apply_quantity: item.suggested_quantity,
    }))
    if (reorderDialogVisible.value) {
      await nextTick()
      reorderList.value.forEach((r) => reorderTableRef.value?.toggleRowSelection(r, true))
    }
  } catch (error) {
    console.error('発注提案の取得に失敗しました:', error)
    if (!silent) ElMessage.error('発注提案の取得に失敗しました')
  } finally {
    reorderLoading.value = false
  }
}

const openReorderDialog = async () => {
  reorderDialogVisible.value = true
  await loadReorderSuggestions()
}

const applyReorderSuggestions = async () => {
  if (!guardPurchaseOperation(canEdit)) return
  const targets = reorderSelection.value.filter((r) => (r.apply_quantity || 0) > 0)
  if (!targets.length) {
    ElMessage.warning('推奨注文数が 0 の行は反映できません')
    return
  }
  try {
    await ElMessageBox.confirm(
      `${targets.length} 件の注文を反映しますか？\n（各部品の欠品予定日の注文本数に加算します）`,
      '発注提案の反映',
      { confirmButtonText: '反映', cancelButtonText: 'キャンセル', type: 'info' },
    )
  } catch {
    return
  }

  reorderApplying.value = true
  let ok = 0
  const failed: string[] = []
  for (const r of targets) {
    const qty = (r.target_order_quantity || 0) + r.apply_quantity
    const ppb = r.pieces_per_bundle || 1
    try {
      await updatePartStock(r.target_row_id, {
        order_quantity: qty,
        order_bundle_quantity: qty * ppb,
        order_amount: qty * ppb * (r.unit_price || 0),
      })
      ok++
    } catch (error) {
      console.error('発注提案の反映に失敗:', r.part_cd, error)
      failed.push(r.part_name || r.part_cd)
    }
  }
  reorderApplying.value = false

  if (ok) ElMessage.success(`${ok} 件の注文を反映しました`)
  if (failed.length) ElMessage.error(`反映に失敗しました: ${failed.join('、')}`)
  await loadReorderSuggestions()
  refreshListForActiveTab()
}

// ─────────────────────────────────────────────
// 部品在庫推移グラフ
// ─────────────────────────────────────────────
interface ChartDay {
  date: string
  rowId: number
  current: number
  trend: number
  usage: number
  plan: number
  order: number
}

interface ChartPart {
  part_cd: string
  part_name: string
  supplier_name?: string
  lead_time?: number
}

const CHART_PRESETS = { short: [-7, 14], mid: [-14, 30], long: [-30, 90] } as const
type ChartPreset = keyof typeof CHART_PRESETS

const chartDrawerVisible = ref(false)
const chartLoading = ref(false)
const chartPart = ref<ChartPart | null>(null)
const chartRange = ref<string[]>([])
const chartPreset = ref<ChartPreset | ''>('mid')
const chartDays = ref<ChartDay[]>([])

const loadPartChart = async () => {
  if (!chartPart.value || chartRange.value?.length !== 2) return
  chartLoading.value = true
  try {
    const res = await getPartStockList({
      part_cd: chartPart.value.part_cd,
      start_date: chartRange.value[0],
      end_date: chartRange.value[1],
      page: 1,
      pageSize: 1000,
    })
    const byDate = new Map<string, ChartDay>()
    for (const item of (res?.data?.list ?? []) as any[]) {
      const d = String(item.date || '').slice(0, 10)
      if (!d) continue
      const day = byDate.get(d) ?? { date: d, rowId: -1, current: 0, trend: 0, usage: 0, plan: 0, order: 0 }
      // 同日に複数行がある場合、累積値（現在在庫・在庫推移）は後に登録された行を採用
      if ((Number(item.id) || 0) > day.rowId) {
        day.rowId = Number(item.id) || 0
        day.current = Number(item.current_stock) || 0
        day.trend = Number(item.stock_trend) || 0
      }
      day.usage += (Number(item.planned_usage) || 0) + (Number(item.manual_usage) || 0)
      day.plan += Number(item.usage_plan_qty) || 0
      day.order += Number(item.order_quantity) || 0
      byDate.set(d, day)
      if (chartPart.value && !chartPart.value.lead_time && item.lead_time) {
        chartPart.value.lead_time = Number(item.lead_time) || 0
      }
    }
    chartDays.value = [...byDate.values()].sort((a, b) => a.date.localeCompare(b.date))
  } catch (error) {
    console.error('在庫推移の取得に失敗しました:', error)
    ElMessage.error('在庫推移の取得に失敗しました')
    chartDays.value = []
  } finally {
    chartLoading.value = false
  }
}

const applyChartPreset = () => {
  if (!chartPreset.value) return
  const [from, to] = CHART_PRESETS[chartPreset.value]
  const today = getTodayJapanStr()
  chartRange.value = [addDaysStr(today, from), addDaysStr(today, to)]
  loadPartChart()
}

const openPartChart = (row: Partial<ChartPart> | null | undefined) => {
  if (!row?.part_cd) return
  chartPart.value = {
    part_cd: row.part_cd,
    part_name: row.part_name || '',
    supplier_name: row.supplier_name,
    lead_time: row.lead_time,
  }
  chartDays.value = []
  chartPreset.value = 'mid'
  chartDrawerVisible.value = true
  applyChartPreset()
}

const handleTableCellClick = (row: any, column: { property?: string }) => {
  if (column?.property === 'part_name') openPartChart(row)
}

const chartKpis = computed(() => {
  const days = chartDays.value
  let minTrend = 0
  let minTrendDate = ''
  days.forEach((d, i) => {
    if (i === 0 || d.trend < minTrend) {
      minTrend = d.trend
      minTrendDate = d.date
    }
  })
  const today = getTodayJapanStr()
  return {
    leadTime: chartPart.value?.lead_time ?? 0,
    minTrend,
    minTrendDate,
    shortageDate: days.find((d) => d.date >= today && d.trend < 0)?.date ?? '',
    totalUsage: days.reduce((s, d) => s + d.usage, 0),
    totalOrder: days.reduce((s, d) => s + d.order, 0),
  }
})

const chartData = computed(() => ({
  labels: chartDays.value.map((d) => d.date.slice(5).replace('-', '/')),
  datasets: [
    {
      type: 'line',
      label: '在庫推移',
      data: chartDays.value.map((d) => d.trend),
      borderColor: '#8b5cf6',
      borderDash: [6, 4],
      borderWidth: 2,
      pointRadius: 0,
      tension: 0.25,
      fill: false,
      yAxisID: 'y',
      order: 0,
    },
    {
      type: 'line',
      label: '現在在庫',
      data: chartDays.value.map((d) => d.current),
      borderColor: '#4f46e5',
      backgroundColor: 'rgba(79, 70, 229, 0.08)',
      borderWidth: 2,
      pointRadius: 2,
      tension: 0.25,
      fill: true,
      yAxisID: 'y',
      order: 1,
    },
    {
      type: 'bar',
      label: '使用数（実績＋手動）',
      data: chartDays.value.map((d) => d.usage),
      backgroundColor: 'rgba(16, 185, 129, 0.55)',
      borderRadius: 3,
      yAxisID: 'y1',
      order: 2,
    },
    {
      type: 'bar',
      label: '使用計画',
      data: chartDays.value.map((d) => d.plan),
      backgroundColor: 'rgba(14, 165, 233, 0.35)',
      borderRadius: 3,
      yAxisID: 'y1',
      order: 3,
    },
    {
      type: 'bar',
      label: '注文本数',
      data: chartDays.value.map((d) => d.order),
      backgroundColor: 'rgba(245, 158, 11, 0.75)',
      borderRadius: 3,
      yAxisID: 'y1',
      order: 4,
    },
  ],
}))

const formatTick = (v: number | string) => Number(v).toLocaleString('ja-JP')

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  plugins: {
    legend: { position: 'bottom', labels: { usePointStyle: true, boxWidth: 8, font: { size: 11 } } },
    tooltip: {
      callbacks: {
        label: (ctx: any) => `${ctx.dataset.label}: ${formatTick(ctx.parsed.y || 0)}`,
      },
    },
  },
  scales: {
    x: { grid: { display: false }, ticks: { font: { size: 10 }, maxRotation: 0, autoSkip: true } },
    y: {
      position: 'left',
      title: { display: true, text: '在庫' },
      grid: {
        color: (ctx: any) => (ctx.tick?.value === 0 ? 'rgba(239, 68, 68, 0.6)' : 'rgba(226, 232, 240, 0.7)'),
      },
      ticks: { callback: formatTick },
    },
    y1: {
      position: 'right',
      beginAtZero: true,
      title: { display: true, text: '数量' },
      grid: { drawOnChartArea: false },
      ticks: { callback: formatTick },
    },
  },
}

// 部品マスタ更新: parts（status=1）→ 既存 part_stock 行のマスタ項目を上書き（期間で絞り可）
const handleSyncPartMaster = async () => {
  if (!guardPurchaseOperation(canCreate)) return

  try {
    if (!searchForm.dateRange || searchForm.dateRange.length !== 2) {
      ElMessage.error('まず日付（期間）を選択してください')
      return
    }
    const startDate = searchForm.dateRange[0]
    const endDate = searchForm.dateRange[1]

    await ElMessageBox.confirm(
      `部品マスタ（parts）の情報を部品在庫（part_stock）に同期しますか？\n\n対象期間: ${startDate} ～ ${endDate}\n\n同期項目: 部品名・分類・単位・単価・仕入先 等（マスタ定義に準拠）`,
      '部品マスタ更新確認',
      {
        confirmButtonText: '実行',
        cancelButtonText: 'キャンセル',
        type: 'warning',
      },
    )

    partMasterSyncLoading.value = true
    const res = await syncPartStockFromMaster({
      start_date: startDate,
      end_date: endDate,
    })
    const updated = (res as any)?.data?.updated_count ?? 0

    ElMessage.success(`部品マスタ更新が完了しました。更新件数: ${updated}件`)

    await fetchData()
  } catch (error: any) {
    if (error !== 'cancel' && error !== 'close') {
      console.error('部品マスタ更新に失敗しました:', error)
      const detail = error?.response?.data?.detail || error?.message || '部品マスタ更新に失敗しました'
      ElMessage.error(detail)
    }
  } finally {
    partMasterSyncLoading.value = false
  }
}

const handleStockCalculation = async () => {
  if (!guardPurchaseOperation(canEdit)) return

  try {
    await ElMessageBox.confirm('在庫計算を実行しますか？', '在庫計算確認', {
      confirmButtonText: '実行',
      cancelButtonText: 'キャンセル',
      type: 'warning',
    })

    stockCalculationLoading.value = true

    // 集計期間は API 側で part_stock（initial>0 錨点日～最大日）に固定。画面の期間は送らない。
    const response = await calculatePartStock()
    const d = response?.data

    if (response?.success !== false) {
      const calculated_count = d?.calculated_count ?? 0
      const updated_count = d?.updated_count ?? 0
      const usage_synced = d?.usage_synced ?? 0
      const usage_plan_synced = d?.usage_plan_synced ?? 0
      const usage_lookup_key_count = d?.usage_lookup_key_count ?? 0
      const sync_window_row_count = d?.sync_window_row_count ?? 0
      const up = d?.usage_period
      const periodLine =
        up?.start_date && up?.end_date
          ? `\n同期期間: ${up.start_date} ～ ${up.end_date}`
          : ''

      ElMessage.success(
        `在庫計算が完了しました。${periodLine}\n使用数集計キー数(受払×BOM): ${usage_lookup_key_count}件 / 同期期間内 part_stock 行: ${sync_window_row_count}件\n使用数を更新した行: ${usage_synced}件\n使用計画を同期した行: ${usage_plan_synced}件\n部品別計算: ${calculated_count}件\n現在庫・在庫推移を更新した行: ${updated_count}件`,
      )

      await fetchData()
    } else {
      ElMessage.error('在庫計算に失敗しました')
    }
  } catch (error: any) {
    if (error !== 'cancel' && error !== 'close') {
      console.error('在庫計算に失敗しました:', error)
      const detail = error?.response?.data?.detail || error?.message || '在庫計算に失敗しました'
      ElMessage.error(detail)
    }
  } finally {
    stockCalculationLoading.value = false
  }
}

// 打印注文書：対象は部品在庫メイン（丸一系仕入先・当日分）
const getMergedOrderData = async () => {
  try {
    return tableData.value.filter(
      (item) =>
        item.order_quantity > 0 &&
        item.date === searchForm.dateRange[0] &&
        (item.supplier_name === '丸一NST' || item.supplier_name === '丸一ﾒﾀﾙｱｸﾄ'),
    )
  } catch (error) {
    console.error('注文データの取得に失敗:', error)
    ElMessage.error('注文データの取得に失敗しました')
    return []
  }
}

const handlePrintOrder = async () => {
  if (!guardPurchaseOperation(canExport)) return

  // 检查是否有选择日期
  if (!searchForm.dateRange || searchForm.dateRange.length === 0) {
    ElMessage.warning('先に日付（期間）を選択してください')
    return
  }

  // 获取合并后的注文数据
  const mergedOrderItems = await getMergedOrderData()

  if (mergedOrderItems.length === 0) {
    ElMessage.warning('対象の注文データがありません（丸一NST・丸一ﾒﾀﾙｱｸﾄ／開始日分）')
    return
  }

  // 印刷確認ダイアログを表示
  printConfirmDialogVisible.value = true
}

// 确认打印
const confirmPrint = async () => {
  if (!guardPurchaseOperation(canExport)) return

  try {
    const mergedOrderItems = await getMergedOrderData()

    if (mergedOrderItems.length === 0) {
      ElMessage.warning('対象の注文データがありません（丸一NST・丸一ﾒﾀﾙｱｸﾄ／開始日分）')
      return
    }

    const deliveryYmd = getNonyuDateYmdForPdf()
    if (!deliveryYmd) {
      ElMessage.error('納入日（日付範囲の開始日）が不正です。日付を選択してください。')
      return
    }

    printPdfSaving.value = true
    const pdfName = `${deliveryYmd}注文書_丸一鋼管.pdf`
    try {
      ElMessage.info('画像PDFを生成し、共有フォルダへ保存しています…')
      const pdfBlob = await generateOrderSheetImagePdfBlob(mergedOrderItems)
      const res = (await saveMaruichiPartOrderPdf(pdfBlob, pdfName)) as {
        success?: boolean
        message?: string
        detail?: string
      }
      if (res?.success === false) {
        ElMessage.error(res?.message || 'PDFの保存に失敗しました')
      } else {
        ElMessage.success(`共有フォルダに保存しました（${pdfName}）`)
      }
    } catch (e: unknown) {
      console.error('丸一注文書PDF保存エラー:', e)
      const ax = e as { response?: { data?: { detail?: string } }; message?: string }
      const detail = ax?.response?.data?.detail || ax?.message || 'PDFの保存に失敗しました'
      ElMessage.error(detail)
    } finally {
      printPdfSaving.value = false
    }

    ElMessage.info('印刷プレビューを生成中...')
    const printContent = generatePrintHtml(mergedOrderItems)
    const printWindow = window.open('', '_blank')
    if (printWindow) {
      printWindow.document.write(`
        <html>
        <head>
          <title>注文書</title>
          <meta charset="UTF-8">
          <style>${MARUICHI_ORDER_SHEET_STYLES}</style>
        </head>
        <body>${printContent}</body>
        </html>
      `)
      printWindow.document.close()

      printWindow.onload = function () {
        printWindow.print()
        setTimeout(function () {
          printWindow.close()
        }, 1000)
      }
    }
  } catch (error) {
    console.error('印刷・PDFエラー:', error)
    ElMessage.error('処理中にエラーが発生しました')
  }

  printConfirmDialogVisible.value = false
}

// 生成打印HTML内容
const generatePrintHtml = (filteredOrderItems: PartOrderItem[]) => {
  // 部品名でソート（旧レスポンス互換で material_name も参照）
  const sortedOrderItems = [...filteredOrderItems].sort((a, b) => {
    const sizeA = a.part_name || a.material_name || ''
    const sizeB = b.part_name || b.material_name || ''
    return sizeA.localeCompare(sizeB, 'ja-JP', { numeric: true, sensitivity: 'base' })
  })

  const totalChumonHonsu = sortedOrderItems.reduce((sum, item) => sum + (item.order_quantity || 0), 0)

  const issuedDateTime = new Date().toLocaleString('ja-JP', {
    timeZone: 'Asia/Tokyo',
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })

  const deliveryDate = searchForm.dateRange[0] || '未指定'

  let tableRowsHtml = ''
  sortedOrderItems.forEach((row) => {
    const size = row.part_name || ''

    // 長さ: 部品名末尾4桁
    const materialName = row.part_name || ''
    const lengthMatch = materialName.match(/(\d{4})$/)
    const length = lengthMatch ? lengthMatch[1] : ''

    tableRowsHtml += `
      <tr>
        <td class="text-center">${row.standard_spec || ''}</td>
        <td class="text-center">${size}</td>
        <td class="text-right">${length}</td>
        <td class="text-center">${row.order_quantity || 0}</td>
        <td>${row.remarks || ''}</td>
      </tr>
    `
  })

  return `
    <div class="order-sheet">
      <div class="order-sheet-main">
      <div class="issued-info">発行日: ${issuedDateTime}</div>

      <div class="title">注 文 書</div>

      <div class="header">
        <div class="recipient-block">
          <div>${printForm.recipientCompany}</div>
          <div>${printForm.recipientPersons}</div>
        </div>

        <div class="sender-block">
          <div>日鉄物産荒井オートモーティブ(株)     </div>
          <div>〒496-0902 愛知県愛西市須依町2189  </div>
          <div>TEL<0567>28-4171</div>
          <div>FAX<0567>26-2281</div>
          <div class="approval-box">
            <table>
              <tr>
                <td>承認</td>
                <td>発行</td>
              </tr>
              <tr>
                <td>${printForm.approver}</td>
                <td>${printForm.issuer}</td>
              </tr>
            </table>
          </div>
        </div>

        <div class="delivery-info">
          <div>納入日 ${deliveryDate}</div>
          <div>(納入場所:長尺材置場)</div>
        </div>
      </div>

      <table>
        <thead>
          <tr>
            <th width="15%">規格</th>
            <th width="22%">サイズ</th>
            <th width="12%">長さ</th>
            <th width="15%">注文本数</th>
            <th width="36%">備考</th>
          </tr>
        </thead>
        <tbody>
          ${tableRowsHtml}
        </tbody>
      </table>

      <div class="summary-row">
        <div class="summary-item">注文本数計  ${totalChumonHonsu}</div>
      </div>
      </div>

      <div class="notes">
        <p>${printForm.note1}</p>
        <p>${printForm.note2}</p>
      </div>
    </div>
  `
}

/** PDF キャプチュラ用：iframe を内容高さに閉じ、余白のないキャンバスにする */
const ORDER_SHEET_CAPTURE_EXTRA_CSS = `
html.sheet-capture-doc, html.sheet-capture-doc body {
  height: auto !important;
  min-height: 0 !important;
}
html.sheet-capture-doc body.order-pdf-capture {
  margin: 3mm !important;
  padding: 0 !important;
}
html.sheet-capture-doc .order-sheet {
  min-height: 277mm !important;
  padding-bottom: 36mm !important;
  position: relative !important;
  /* 捕获时给左右留白，避免 PDF 内容贴到页面左右边缘 */
  padding-left: 6mm !important;
  padding-right: 6mm !important;
  box-sizing: border-box !important;
}
html.sheet-capture-doc .order-sheet .notes {
  position: absolute !important;
  bottom: 0 !important;
  left: 0 !important;
  right: 0 !important;
  margin-top: 0 !important;
}
`

/** html2canvas + jsPDF で画像ベースの PDF を生成（1ページに収まらない場合は複数ページ） */
const generateOrderSheetImagePdfBlob = (mergedOrderItems: PartOrderItem[]): Promise<Blob> => {
  return new Promise((resolve, reject) => {
    const printContent = generatePrintHtml(mergedOrderItems)
    const iframe = document.createElement('iframe')
    iframe.setAttribute('title', 'order-sheet-capture')
    // min-height / 大きな固定高を付けない（body が無駄に伸び、下端空白＋2ページ目が真っ白になる原因）
    iframe.style.cssText =
      'position:fixed;left:-12000px;top:0;width:210mm;border:0;opacity:0;pointer-events:none'
    document.body.appendChild(iframe)
    const doc = iframe.contentDocument
    if (!doc) {
      iframe.remove()
      reject(new Error('iframe document'))
      return
    }
    const html = `<!DOCTYPE html><html class="sheet-capture-doc"><head><meta charset="UTF-8"><style>${MARUICHI_ORDER_SHEET_STYLES}${ORDER_SHEET_CAPTURE_EXTRA_CSS}</style></head><body class="order-pdf-capture">${printContent}</body></html>`
    doc.open()
    doc.write(html)
    doc.close()

    const cleanup = () => {
      iframe.remove()
    }

    const runCapture = async () => {
      if (!guardPurchaseOperation(canEdit)) return

      try {
        const target = doc.querySelector('.order-sheet') as HTMLElement | null
        if (!target) {
          cleanup()
          reject(new Error('.order-sheet not found'))
          return
        }
        await new Promise((r) => setTimeout(r, 280))
        const canvas = await html2canvas(target, {
          scale: 2,
          useCORS: true,
          logging: false,
          backgroundColor: '#ffffff',
        })
        const imgData = canvas.toDataURL('image/jpeg', 0.92)
        const pdf = new jsPDF({ orientation: 'p', unit: 'mm', format: 'a4', compress: true })
        const pageWidth = pdf.internal.pageSize.getWidth()
        const pageHeight = pdf.internal.pageSize.getHeight()
        // キャンバス縦横比から mm 高さを直接算出（JPEG メタデータとの不一致による誤分割を防ぐ）
        const imgWidthMm = pageWidth
        const imgHeightMm = (canvas.height / canvas.width) * imgWidthMm
        const MM_EPS = 0.8
        if (imgHeightMm <= pageHeight + MM_EPS) {
          pdf.addImage(imgData, 'JPEG', 0, 0, imgWidthMm, imgHeightMm, undefined, 'FAST')
        } else {
          let heightLeft = imgHeightMm
          let position = 0
          pdf.addImage(imgData, 'JPEG', 0, position, imgWidthMm, imgHeightMm, undefined, 'FAST')
          heightLeft -= pageHeight
          while (heightLeft > MM_EPS) {
            position = heightLeft - imgHeightMm
            pdf.addPage()
            pdf.addImage(imgData, 'JPEG', 0, position, imgWidthMm, imgHeightMm, undefined, 'FAST')
            heightLeft -= pageHeight
          }
        }
        const blob = pdf.output('blob')
        cleanup()
        resolve(blob)
      } catch (e) {
        cleanup()
        reject(e)
      }
    }

    requestAnimationFrame(() => {
      void runCapture()
    })
  })
}

// データ生成処理
const handleDataGeneration = async () => {
  if (!guardPurchaseOperation(canEdit)) return

  // 重置日期
  dataGenerationStartDate.value = ''
  dataGenerationEndDate.value = ''
  // 显示日期选择对话框
  dataGenerationDialogVisible.value = true
}

// データ生成確認
const confirmDataGeneration = async () => {
  if (!guardPurchaseOperation(canApprove)) return

  try {
    // 验证日期选择
    if (!dataGenerationStartDate.value) {
      ElMessage.error('開始日を選択してください')
      return
    }
    if (!dataGenerationEndDate.value) {
      ElMessage.error('終了日を選択してください')
      return
    }
    if (new Date(dataGenerationStartDate.value) > new Date(dataGenerationEndDate.value)) {
      ElMessage.error('開始日は終了日より前である必要があります')
      return
    }

    const startDate = dataGenerationStartDate.value
    const endDate = dataGenerationEndDate.value

    // 关闭对话框
    dataGenerationDialogVisible.value = false

    // 确认生成
    await ElMessageBox.confirm(
      `⚠️ 以下の期間でデータ生成を実行しますか？\n\n📅 開始日:\n${startDate}\n\n📅 終了日:\n${endDate}`,
      'データ生成確認',
      {
        confirmButtonText: '✅ 実行',
        cancelButtonText: '❌ キャンセル',
        type: 'warning',
        customClass: 'data-generation-confirm-dialog',
        dangerouslyUseHTMLString: false,
        showClose: true,
        closeOnClickModal: false,
        closeOnPressEscape: true,
        center: true,
        roundButton: true,
        buttonSize: 'large',
      },
    )

    dataGenerationLoading.value = true

    const response = await generatePartStockData({
      start_date: startDate,
      end_date: endDate,
      overwrite_existing: false, // 改为false，不覆盖现有数据
    }) as any

    const resData = response?.data ?? response
    if (resData?.success !== false) {
      const payload = resData?.data ?? resData ?? {}
      const generated_count = payload.generated_count ?? 0
      const updated_count = payload.updated_count ?? 0
      const skipped_count = payload.skipped_count ?? 0
      const duplicate_count = payload.duplicate_count ?? 0

      // 結果メッセージを組み立て
      let message = `データ生成が完了しました！\n\n`
      message += `✅ 新規生成: ${generated_count}件\n`
      message += `🔄 更新: ${updated_count}件\n`

      if (duplicate_count > 0) {
        message += `⚠️ 重複データをスキップ: ${duplicate_count}件\n`
      }

      if (skipped_count > 0) {
        message += `⏭️ その他スキップ: ${skipped_count}件`
      }

      // 根据结果类型显示不同的消息
      if (duplicate_count > 0) {
        ElMessage.warning({
          message: message,
          duration: 5000,
          showClose: true,
        })
      } else {
        ElMessage.success({
          message: message,
          duration: 4000,
          showClose: true,
        })
      }

      // 刷新数据
      await fetchData()
    } else {
      ElMessage.error('データ生成に失敗しました')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('データ生成に失敗しました:', error)
      ElMessage.error('データ生成に失敗しました')
    }
  } finally {
    dataGenerationLoading.value = false
  }
}

// 工具方法 - formatCurrency已在上面定义，这里删除重复定义

// 手入力部品注文まわり
const handleAddManualOrder = async () => {
  if (!guardPurchaseOperation(canCreate)) return

  console.log('手入力部品注文ダイアログを開く')

  // 重置表单
  Object.assign(manualOrderForm, {
    date: getTodayJapanStr(),
    part_cd: '',
    part_name: '',
    order_quantity: 0,
    unit: '',
    unit_price: 0,
    supplier_cd: '',
    supplier_name: '',
    standard_spec: '',
    pieces_per_bundle: 0,
    lead_time: 0,
    remarks: 'バラ束', // デフォルト備考
  })

  selectedPart.value = null

  await loadParts()

  manualOrderDialogVisible.value = true
}

const handleCancelManualOrder = () => {
  console.log('手入力部品注文をキャンセル')

  // 关闭对话框
  manualOrderDialogVisible.value = false

  // 重置表单
  if (manualOrderFormRef.value) {
    manualOrderFormRef.value.resetFields()
  }

  // 重置选中的材料
  selectedPart.value = null
  console.log('已重置selectedPart')
}

const loadParts = async () => {
  try {
    partSearchLoading.value = true
    console.log('开始请求材料数据...')

    // 使用正确的API路径
    let response
    try {
      // 使用正确的materials API路径
      response = await request.get('/api/master/parts', {
        params: { page: 1, pageSize: 10000, status: 1 },
      })
      console.log('成功获取材料数据，使用 /api/master/parts')
    } catch (error) {
      console.log('材料データ取得失敗:', error)
      throw error
    }

    console.log('材料データレスポンス:', response)
    // 处理后端响应格式 - axios 返回 { data: 后端body }，后端可能是 { success: true, data: { list, total } } 或 { data: [...] } 或直接数组
    const resBody = (response as any)?.data ?? response
    console.log('响应状态:', resBody?.success)
    console.log('响应数据:', resBody?.data)
    console.log('完整响应对象:', JSON.stringify(response, null, 2))
    if (response) {
      const list = resBody?.data?.list ?? resBody?.data ?? resBody?.list
      if (resBody?.success !== false && Array.isArray(resBody?.data)) {
        // 标准格式: { success: true, data: [...] }
        partOptions.value = resBody.data
        console.log('成功获取材料数据 (标准格式):', partOptions.value.length, '条')
      } else if (Array.isArray(list)) {
        // 格式: { success: true, data: { list: [...] } } 或 { data: { list: [...] } }
        partOptions.value = list
        console.log('成功获取材料数据 (list格式):', partOptions.value.length, '条')
      } else if (Array.isArray(resBody)) {
        // 直接数组格式: [...]
        partOptions.value = resBody
        console.log('成功获取材料数据 (数组格式):', partOptions.value.length, '条')
      } else if (resBody?.data && Array.isArray(resBody.data)) {
        // 其他可能的格式: { data: [...] }
        partOptions.value = resBody.data
        console.log('成功获取材料数据 (data格式):', partOptions.value.length, '条')
      } else {
        console.error('材料数据响应格式错误:', response)
        partOptions.value = []
        return
      }

      partOptions.value = (partOptions.value || []).filter((p: any) => excludePartsStatusZero(p))

      console.log('第一条材料数据示例:', partOptions.value[0])
      console.log('材料字段检查:', {
        part_cd: partOptions.value[0]?.part_cd,
        part_name: partOptions.value[0]?.part_name,
        supplier_name: partOptions.value[0]?.supplier_name,
        standard_spec: partOptions.value[0]?.standard_spec,
        unit_price: partOptions.value[0]?.unit_price,
        pieces_per_bundle: partOptions.value[0]?.pieces_per_bundle,
        unit: partOptions.value[0]?.unit,
        lead_time: partOptions.value[0]?.lead_time,
      })
    } else {
      console.error('响应为空')
      partOptions.value = []
    }
  } catch (error: any) {
    console.error('材料データの取得に失敗しました:', error)
    console.error('错误详情:', error.response || error.message || error)
    partOptions.value = []
  } finally {
    partSearchLoading.value = false
  }
}

const handlePartChange = (partCd: string) => {
  const part = partOptions.value.find((m) => m.part_cd === partCd)

  if (part) {
    selectedPart.value = { ...part }
    manualOrderForm.part_name = part.part_name
    fillPartData(part)
    nextTick(() => {})
  } else {
    selectedPart.value = null
  }
}

const fillPartData = (part: PartMasterOption) => {
  const p = part as PartMasterOption & {
    category?: string
    uom?: string
    standard_spec?: string
    pieces_per_bundle?: number
    lead_time?: number
  }
  manualOrderForm.supplier_cd = p.supplier_cd || ''
  manualOrderForm.supplier_name = p.supplier_name || ''
  manualOrderForm.standard_spec = p.category || p.standard_spec || ''
  manualOrderForm.unit_price = p.unit_price || 0
  manualOrderForm.pieces_per_bundle = p.pieces_per_bundle ?? 1
  manualOrderForm.unit = p.uom || p.unit || ''
  manualOrderForm.lead_time = p.lead_time ?? 0

  console.log('填充后的表单数据:', {
    supplier_cd: manualOrderForm.supplier_cd,
    supplier_name: manualOrderForm.supplier_name,
    standard_spec: manualOrderForm.standard_spec,
    unit_price: manualOrderForm.unit_price,
    pieces_per_bundle: manualOrderForm.pieces_per_bundle,
    unit: manualOrderForm.unit,
    lead_time: manualOrderForm.lead_time,
  })
}

const handleConfirmManualOrder = async () => {
  if (!guardPurchaseOperation(canApprove)) return

  if (!manualOrderFormRef.value) return

  try {
    await manualOrderFormRef.value.validate()

    manualOrderLoading.value = true

    const dateStr =
      typeof manualOrderForm.date === 'string'
        ? manualOrderForm.date
        : (manualOrderForm.date as Date)?.toISOString?.()?.slice(0, 10) ?? ''

    const oq = manualOrderForm.order_quantity ?? 0
    const ppb = manualOrderForm.pieces_per_bundle || 1
    const order_bundle_quantity = oq > 0 ? oq * ppb : 0
    const order_amount = order_bundle_quantity > 0 ? order_bundle_quantity * (manualOrderForm.unit_price ?? 0) : 0

    const orderData = {
      date: dateStr,
      part_cd: manualOrderForm.part_cd || '',
      part_name: manualOrderForm.part_name || '',
      initial_stock: 0,
      current_stock: 0,
      adjustment_quantity: 0,
      unit: manualOrderForm.unit || undefined,
      unit_price: manualOrderForm.unit_price ?? 0,
      supplier_cd: manualOrderForm.supplier_cd || undefined,
      supplier_name: manualOrderForm.supplier_name || undefined,
      lead_time: manualOrderForm.lead_time ?? 0,
      planned_usage: 0,
      manual_usage: 0,
      usage_plan_qty: 0,
      stock_trend: 0,
      order_quantity: oq,
      order_bundle_quantity,
      order_amount,
      standard_spec: manualOrderForm.standard_spec || undefined,
      pieces_per_bundle: manualOrderForm.pieces_per_bundle ?? 0,
      remarks: manualOrderForm.remarks || undefined,
    }

    const result = await createPartStock(orderData) as any
    if (result?.success !== false) {
      ElMessage.success('部品注文が正常に登録されました')
      manualOrderDialogVisible.value = false
      await fetchData()
    } else {
      ElMessage.error('部品注文の登録に失敗しました')
    }
  } catch (error) {
    if (error !== false) {
      console.error('部品注文登録に失敗しました:', error)
      ElMessage.error('部品注文の登録に失敗しました')
    }
  } finally {
    manualOrderLoading.value = false
  }
}

// 生命周期
onMounted(() => {
  loadPartDropdownOptions('')
  fetchData()
  fetchSupplierOptions()
})
</script>

<style scoped>
.part-order-container {
  --po-indigo: #4f46e5;
  --po-violet: #7c3aed;
  --po-sky: #0284c7;
  --po-emerald: #059669;
  --po-amber: #d97706;
  --po-rose: #e11d48;
  --po-ink: #0f172a;
  --po-muted: #64748b;
  --po-line: #e2e8f0;
  padding: 10px 12px;
  background:
    radial-gradient(1200px 380px at 0% 0%, rgba(99, 102, 241, 0.1), transparent 60%),
    radial-gradient(900px 320px at 100% 0%, rgba(139, 92, 246, 0.09), transparent 60%),
    linear-gradient(180deg, #f5f7fc 0%, #eef1f8 100%);
  min-height: 100vh;
  animation: pageFadeIn 0.45s ease-out;
}

@keyframes pageFadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes cardRise {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes headerShine {
  0% { transform: translateX(-120%) skewX(-18deg); }
  60%, 100% { transform: translateX(320%) skewX(-18deg); }
}

/* ページヘッダー */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 18px;
  margin-bottom: 10px;
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 58%, #8b5cf6 100%);
  border-radius: 14px;
  color: white;
  box-shadow:
    0 10px 28px rgba(79, 70, 229, 0.28),
    0 0 0 1px rgba(255, 255, 255, 0.18) inset;
  position: relative;
  overflow: hidden;
  animation: slideDown 0.45s ease-out;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.page-header:hover {
  transform: translateY(-1px);
  box-shadow:
    0 14px 34px rgba(124, 58, 237, 0.32),
    0 0 0 1px rgba(255, 255, 255, 0.22) inset;
}

/* 装飾用の光の円 */
.page-header::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 88% -30%, rgba(255, 255, 255, 0.28) 0, transparent 38%),
    radial-gradient(circle at 62% 140%, rgba(255, 255, 255, 0.16) 0, transparent 34%),
    radial-gradient(circle at 8% 120%, rgba(56, 189, 248, 0.28) 0, transparent 30%);
  pointer-events: none;
}

.page-header::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 30%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.14), transparent);
  animation: headerShine 7s ease-in-out infinite;
  pointer-events: none;
}

.header-left {
  display: flex;
  align-items: center;
  position: relative;
  z-index: 1;
}

.title-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  width: 38px;
  height: 38px;
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.36), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.35);
  border-radius: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  backdrop-filter: blur(10px);
  box-shadow:
    0 6px 14px rgba(30, 27, 75, 0.25),
    inset 0 1px 0 rgba(255, 255, 255, 0.45);
  transition: transform 0.3s ease;
}

.page-header:hover .title-icon {
  transform: rotate(-6deg) scale(1.06);
}

.title-text {
  display: flex;
  flex-direction: column;
}

.main-title {
  font-size: 18px;
  font-weight: 700;
  margin: 0;
  line-height: 1.25;
  letter-spacing: 0.04em;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.12);
}

.subtitle {
  font-size: 11px;
  opacity: 0.88;
  margin: 1px 0 0 0;
  font-weight: 500;
  letter-spacing: 0.03em;
}

.header-actions {
  display: flex;
  gap: 8px;
  position: relative;
  z-index: 1;
}

.action-btn {
  --btn-bg: rgba(255, 255, 255, 0.16);
  --btn-bg-hover: rgba(255, 255, 255, 0.26);
  --btn-glow: rgba(15, 23, 42, 0.25);
  height: 32px;
  padding: 0 14px;
  border-radius: 9px;
  font-weight: 600;
  font-size: 12px;
  color: #fff;
  background: var(--btn-bg);
  border: 1px solid rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(10px);
  box-shadow:
    0 4px 12px rgba(15, 23, 42, 0.14),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

.action-btn:hover,
.action-btn:focus-visible {
  color: #fff;
  background: var(--btn-bg-hover);
  border-color: rgba(255, 255, 255, 0.45);
  transform: translateY(-2px);
  box-shadow:
    0 10px 22px var(--btn-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
}

.action-btn:active {
  transform: translateY(0);
}

.action-btn :deep(.el-icon) {
  margin-right: 4px;
}

.success-btn {
  --btn-bg: linear-gradient(135deg, #34d399 0%, #059669 100%);
  --btn-bg-hover: linear-gradient(135deg, #6ee7b7 0%, #10b981 100%);
  --btn-glow: rgba(5, 150, 105, 0.45);
}

.warning-btn {
  --btn-bg: linear-gradient(135deg, #fbbf24 0%, #d97706 100%);
  --btn-bg-hover: linear-gradient(135deg, #fcd34d 0%, #f59e0b 100%);
  --btn-glow: rgba(217, 119, 6, 0.45);
}

/* 統計カード */
.stats-container {
  margin-bottom: 10px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 10px;
}

.stat-card {
  --card-color: linear-gradient(135deg, #818cf8 0%, #4f46e5 100%);
  --card-solid: #4f46e5;
  --card-soft: rgba(79, 70, 229, 0.08);
  --card-glow: rgba(79, 70, 229, 0.28);
  background:
    linear-gradient(135deg, var(--card-soft) 0%, rgba(255, 255, 255, 0) 55%),
    #ffffff;
  border-radius: 12px;
  padding: 9px 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  border: 1px solid rgba(226, 232, 240, 0.9);
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 4px 14px rgba(15, 23, 42, 0.05);
  transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
  position: relative;
  overflow: hidden;
  min-height: 58px;
  animation: cardRise 0.45s ease-out both;
}

.stat-card:nth-child(1) { animation-delay: 0.02s; }
.stat-card:nth-child(2) { animation-delay: 0.06s; }
.stat-card:nth-child(3) { animation-delay: 0.1s; }
.stat-card:nth-child(4) { animation-delay: 0.14s; }
.stat-card:nth-child(5) { animation-delay: 0.18s; }
.stat-card:nth-child(6) { animation-delay: 0.22s; }

/* 上端のアクセントライン */
.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--card-color);
  opacity: 0.9;
}

/* 右上の装飾バブル */
.stat-card::after {
  content: '';
  position: absolute;
  right: -18px;
  top: -22px;
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: var(--card-color);
  opacity: 0.08;
  transition: transform 0.35s ease, opacity 0.35s ease;
  pointer-events: none;
}

.stat-card:hover {
  transform: translateY(-3px);
  border-color: transparent;
  box-shadow:
    0 12px 26px var(--card-glow),
    0 0 0 1px var(--card-soft);
}

.stat-card:hover::after {
  transform: scale(1.35);
  opacity: 0.14;
}

.stat-card.primary {
  --card-color: linear-gradient(135deg, #818cf8 0%, #4f46e5 100%);
  --card-solid: #4f46e5;
  --card-soft: rgba(79, 70, 229, 0.08);
  --card-glow: rgba(79, 70, 229, 0.22);
}

.stat-card.info {
  --card-color: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%);
  --card-solid: #0284c7;
  --card-soft: rgba(2, 132, 199, 0.08);
  --card-glow: rgba(2, 132, 199, 0.22);
}

.stat-card.warning {
  --card-color: linear-gradient(135deg, #fbbf24 0%, #d97706 100%);
  --card-solid: #d97706;
  --card-soft: rgba(217, 119, 6, 0.08);
  --card-glow: rgba(217, 119, 6, 0.22);
}

.stat-card.success {
  --card-color: linear-gradient(135deg, #34d399 0%, #059669 100%);
  --card-solid: #059669;
  --card-soft: rgba(5, 150, 105, 0.08);
  --card-glow: rgba(5, 150, 105, 0.22);
}

.stat-card.order {
  --card-color: linear-gradient(135deg, #a78bfa 0%, #7c3aed 100%);
  --card-solid: #7c3aed;
  --card-soft: rgba(124, 58, 237, 0.08);
  --card-glow: rgba(124, 58, 237, 0.22);
}

.stat-card.amount {
  --card-color: linear-gradient(135deg, #fb7185 0%, #e11d48 100%);
  --card-solid: #e11d48;
  --card-soft: rgba(225, 29, 72, 0.07);
  --card-glow: rgba(225, 29, 72, 0.2);
}

.stat-card .stat-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: var(--card-color);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 17px;
  box-shadow:
    0 6px 14px var(--card-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.4),
    inset 0 -2px 0 rgba(0, 0, 0, 0.08);
  flex-shrink: 0;
  position: relative;
  z-index: 1;
  transition: transform 0.3s ease;
}

.stat-card:hover .stat-icon {
  transform: translateY(-1px) rotate(-6deg) scale(1.06);
}

.stat-content {
  flex: 1;
  min-width: 0;
  position: relative;
  z-index: 1;
}

.stat-value {
  font-size: 17px;
  font-weight: 800;
  color: var(--po-ink);
  margin-bottom: 1px;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.01em;
}

.stat-value .unit {
  font-size: 11px;
  font-weight: 600;
  color: var(--card-solid);
  margin-left: 3px;
}

.stat-label {
  font-size: 11px;
  color: var(--po-muted);
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: flex;
  align-items: center;
  gap: 5px;
}

.stat-label::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--card-solid);
  box-shadow: 0 0 0 3px var(--card-soft);
  flex-shrink: 0;
}

/* ===== Filter Bar ===== */
.search-section {
  margin-bottom: 8px;
}

.search-container {
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border-radius: 12px;
  padding: 6px 14px;
  border: 1px solid rgba(255, 255, 255, 0.7);
  box-shadow:
    0 4px 20px rgba(79, 70, 229, 0.07),
    0 0 0 1px rgba(99, 102, 241, 0.08);
  transition: box-shadow 0.25s ease;
}

.search-container:hover {
  box-shadow:
    0 8px 26px rgba(79, 70, 229, 0.1),
    0 0 0 1px rgba(99, 102, 241, 0.12);
}

/* 全フィルターアイテムを1行に並べる */
.search-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0;
  align-items: center;
  height: 36px;
}

/* 各フィルターアイテム: ラベル + 入力欄 を横並び */
.filter-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 12px;
  border-right: 1px solid #e5e7eb;
  height: 100%;
}

.filter-item:first-child {
  padding-left: 0;
}

.filter-item:last-child {
  border-right: none;
}

.filter-item.date-group {
  gap: 6px;
  flex-shrink: 0;
}

.filter-item.part-filter-item .part-code-select {
  min-width: 220px;
  width: 240px;
}

.filter-item.supplier-item {
  flex: 0 1 auto;
  min-width: 0;
  width: 240px;
}

.filter-item.supplier-item .filter-select {
  width: 100%;
  width: 240px;
}

/* ラベル: アイコン + テキスト */
.filter-label {
  --label-color: #4f46e5;
  --label-soft: rgba(79, 70, 229, 0.1);
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  font-weight: 700;
  color: #475569;
  white-space: nowrap;
  flex-shrink: 0;
}

.filter-label .el-icon {
  width: 20px;
  height: 20px;
  border-radius: 6px;
  font-size: 12px;
  color: var(--label-color);
  background: var(--label-soft);
}

.part-filter-item .filter-label {
  --label-color: #0284c7;
  --label-soft: rgba(2, 132, 199, 0.1);
}

.supplier-item .filter-label {
  --label-color: #7c3aed;
  --label-soft: rgba(124, 58, 237, 0.1);
}

/* 統一された入力欄スタイル */
.filter-input,
.filter-select {
  min-width: 140px;
}

.filter-input :deep(.el-input__wrapper),
.filter-select :deep(.el-select__wrapper) {
  height: 24px;
  min-height: 24px;
  padding: 0 8px;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
  box-shadow: none;
  transition: all 0.2s ease;
  background: #f8fafc;
}

.filter-input :deep(.el-input__wrapper:hover),
.filter-select :deep(.el-select__wrapper:hover) {
  border-color: #a5b4fc;
  background: white;
}

.filter-input :deep(.el-input__wrapper.is-focus),
.filter-select :deep(.el-select__wrapper.is-focused) {
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.14);
  background: white;
}

.filter-input :deep(.el-input__inner),
.filter-select :deep(.el-select__placeholder),
.filter-select :deep(.el-select__selected-item) {
  font-size: 11px;
  height: 24px;
  line-height: 24px;
}

/* 日付ピッカー */
.filter-date-picker {
  width: 200px;
}

.filter-date-picker :deep(.el-input__wrapper) {
  height: 24px;
  min-height: 24px;
  padding: 0 8px;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
  box-shadow: none;
  background: #f8fafc;
  transition: all 0.2s ease;
}

.filter-date-picker :deep(.el-input__wrapper:hover) {
  border-color: #a5b4fc;
  background: white;
}

.filter-date-picker :deep(.el-input__wrapper.is-active),
.filter-date-picker :deep(.el-range-editor.is-active) {
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.14);
  background: white;
}

.filter-date-picker :deep(.el-range-input) {
  font-size: 11px;
}

.filter-date-picker :deep(.el-range-separator) {
  font-size: 11px;
  color: #94a3b8;
  padding: 0 2px;
}

/* 日付ナビゲーションボタン */
.date-nav-group {
  display: flex;
  gap: 2px;
  align-items: center;
  flex-shrink: 0;
}

.date-nav-btn {
  height: 24px;
  min-height: 24px;
  padding: 0 7px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 500;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  color: #64748b;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.date-nav-btn:hover {
  border-color: #a5b4fc;
  color: #4f46e5;
  background: rgba(99, 102, 241, 0.08);
  transform: translateY(-1px);
}

.date-nav-btn.today-btn {
  background: linear-gradient(135deg, #6366f1 0%, #7c3aed 100%);
  color: white;
  border: none;
  padding: 0 11px;
  font-weight: 700;
  box-shadow:
    0 3px 8px rgba(99, 102, 241, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

.date-nav-btn.today-btn:hover {
  color: white;
  box-shadow:
    0 6px 14px rgba(99, 102, 241, 0.42),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}



/* テーブルエリア */
.table-section {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.7);
  box-shadow:
    0 6px 24px rgba(79, 70, 229, 0.07),
    0 0 0 1px rgba(99, 102, 241, 0.08);
  overflow: hidden;
  animation: cardRise 0.5s ease-out 0.1s both;
}

.table-container {
  padding: 0;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 7px 12px;
  background: linear-gradient(180deg, #fbfcff 0%, #f3f5fb 100%);
  border-bottom: 1px solid #e6e9f4;
}

.table-tabs {
  display: flex;
  gap: 4px;
  padding: 3px;
  border-radius: 11px;
  background: rgba(226, 232, 240, 0.55);
  box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.06);
}

.tab-item {
  --tab-color: #4f46e5;
  --tab-gradient: linear-gradient(135deg, #818cf8 0%, #4f46e5 100%);
  --tab-soft: rgba(79, 70, 229, 0.1);
  --tab-glow: rgba(79, 70, 229, 0.35);
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 13px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  user-select: none;
  transition: transform 0.2s ease, background 0.2s ease, color 0.2s ease, box-shadow 0.2s ease;
  color: #64748b;
  background: transparent;
}

.tab-item .el-icon {
  font-size: 14px;
  color: var(--tab-color);
  transition: color 0.2s ease, transform 0.25s ease;
}

.tab-item:hover {
  background: #ffffff;
  color: var(--tab-color);
  box-shadow: 0 2px 6px rgba(15, 23, 42, 0.06);
}

.tab-item:hover .el-icon {
  transform: scale(1.12);
}

.tab-item.active {
  background: var(--tab-gradient);
  color: white;
  transform: translateY(-1px);
  box-shadow:
    0 6px 14px var(--tab-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(0, 0, 0, 0.08);
}

.tab-item.active .el-icon {
  color: white;
}

.tab-item--initial {
  --tab-color: #0284c7;
  --tab-gradient: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%);
  --tab-glow: rgba(2, 132, 199, 0.35);
}

.tab-item--stock {
  --tab-color: #4f46e5;
  --tab-gradient: linear-gradient(135deg, #818cf8 0%, #4f46e5 100%);
  --tab-glow: rgba(79, 70, 229, 0.35);
}

.tab-item--usage {
  --tab-color: #059669;
  --tab-gradient: linear-gradient(135deg, #34d399 0%, #059669 100%);
  --tab-glow: rgba(5, 150, 105, 0.35);
}

.tab-item--order {
  --tab-color: #d97706;
  --tab-gradient: linear-gradient(135deg, #fbbf24 0%, #d97706 100%);
  --tab-glow: rgba(217, 119, 6, 0.35);
}

.tab-item--history {
  --tab-color: #7c3aed;
  --tab-gradient: linear-gradient(135deg, #a78bfa 0%, #7c3aed 100%);
  --tab-glow: rgba(124, 58, 237, 0.35);
}

.table-actions {
  display: flex;
  gap: 6px;
}

.table-actions :deep(.el-button) {
  height: 30px;
  padding: 0 13px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  border: none;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.table-actions :deep(.el-button .el-icon) {
  margin-right: 4px;
}

.print-btn,
.month-start-btn {
  background: linear-gradient(135deg, #6366f1 0%, #7c3aed 100%);
  box-shadow:
    0 4px 12px rgba(99, 102, 241, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

.print-btn:hover,
.print-btn:focus-visible,
.month-start-btn:hover,
.month-start-btn:focus-visible {
  background: linear-gradient(135deg, #818cf8 0%, #8b5cf6 100%);
  transform: translateY(-1px);
  box-shadow:
    0 8px 18px rgba(99, 102, 241, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

.table-content {
  padding: 0;
}

.modern-table {
  overflow: hidden;
  border: none;
  background: white;
}

.order-history-table :deep(.el-table__footer-wrapper .el-table__cell) {
  padding: 10px 0;
  font-weight: 700;
  color: #0f172a;
  background: #f8fafc;
  border-top: 1px solid #e5e7eb;
}

/* 现代化滚动条样式 */
.modern-table :deep(.el-table__body-wrapper) {
  scrollbar-width: thin;
  scrollbar-color: #cbd5e0 #f7fafc;
}

.modern-table :deep(.el-table__body-wrapper::-webkit-scrollbar) {
  width: 8px;
  height: 8px;
}

.modern-table :deep(.el-table__body-wrapper::-webkit-scrollbar-track) {
  background: #f1f5f9;
  border-radius: 4px;
}

.modern-table :deep(.el-table__body-wrapper::-webkit-scrollbar-thumb) {
  background: linear-gradient(135deg, #cbd5e0 0%, #94a3b8 100%);
  border-radius: 4px;
  border: 1px solid #e2e8f0;
}

.modern-table :deep(.el-table__body-wrapper::-webkit-scrollbar-thumb:hover) {
  background: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
}

/* 表格加载状态优化 */
.modern-table :deep(.el-loading-mask) {
  background-color: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(4px);
}

.modern-table :deep(.el-loading-spinner .path) {
  stroke: #6366f1;
}

.modern-table :deep(.el-loading-spinner .el-loading-text) {
  color: #4f46e5;
}

.modern-table :deep(.el-table__row) {
  transition: background-color 0.2s ease;
}

.pagination-wrapper {
  padding: 7px 16px;
  background: linear-gradient(180deg, #f8f9fd 0%, #f1f4fa 100%);
  border-top: 1px solid #e6e9f4;
  display: flex;
  justify-content: center;
}

.modern-pagination {
  --el-pagination-button-color: #64748b;
  --el-pagination-hover-color: #4f46e5;
}

.modern-pagination :deep(.el-pager li),
.modern-pagination :deep(.btn-prev),
.modern-pagination :deep(.btn-next) {
  border-radius: 7px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  margin: 0 2px;
  font-weight: 600;
  transition: transform 0.2s ease, box-shadow 0.2s ease, color 0.2s ease;
}

.modern-pagination :deep(.el-pager li:hover:not(.is-active)),
.modern-pagination :deep(.btn-prev:hover:not(:disabled)),
.modern-pagination :deep(.btn-next:hover:not(:disabled)) {
  color: #4f46e5;
  border-color: #c7d2fe;
  transform: translateY(-1px);
}

.modern-pagination :deep(.el-pager li.is-active) {
  color: #ffffff;
  border-color: transparent;
  background: linear-gradient(135deg, #6366f1 0%, #7c3aed 100%);
  box-shadow: 0 4px 10px rgba(99, 102, 241, 0.35);
}

.modern-pagination :deep(.el-pagination__total) {
  font-weight: 600;
  color: #475569;
}

/* データ生成ダイアログ - コンパクト */
.data-generation-dialog {
  border-radius: 12px;
  overflow: hidden;
}

.data-generation-dialog :deep(.el-dialog) {
  border-radius: 12px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
}

.data-generation-dialog :deep(.el-dialog__header) {
  padding: 10px 14px;
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  color: white;
  border-bottom: none;
}

.data-generation-dialog :deep(.el-dialog__title) {
  color: white;
  font-weight: 600;
  font-size: 14px;
}

.data-generation-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: white;
  font-size: 16px;
}

.data-generation-dialog :deep(.el-dialog__body) {
  padding: 0;
}

.data-generation-dialog :deep(.el-dialog__footer) {
  padding: 12px 14px;
  background-color: #f8f9fa;
  border-radius: 0 0 12px 12px;
}

.data-generation-content-compact {
  padding: 10px 14px;
}

.data-generation-content-compact .form-sections-compact {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.data-generation-content-compact .form-section-compact {
  background: white;
  border-radius: 5px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  transition: all 0.2s ease;
}

.data-generation-content-compact .form-section-compact:hover {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.06);
  border-color: #6366f1;
}

.data-generation-content-compact .section-header-compact {
  display: flex;
  align-items: center;
  padding: 6px 10px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 1px solid #e5e7eb;
  font-weight: 600;
  color: #334155;
  font-size: 11px;
  gap: 5px;
}

.data-generation-content-compact .section-icon {
  color: #6366f1;
  font-size: 13px;
  flex-shrink: 0;
}

.data-generation-content-compact .section-title {
  font-weight: 600;
  letter-spacing: 0.2px;
}

.data-generation-content-compact .form-fields-compact {
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.data-generation-content-compact .form-field-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.data-generation-content-compact .form-field-row .field-label {
  min-width: 70px;
  font-size: 11px;
  font-weight: 500;
  color: #475569;
  flex-shrink: 0;
}

.date-picker-compact {
  flex: 1;
}

.date-picker-compact :deep(.el-input__wrapper) {
  border-radius: 4px;
  border: 1px solid #d1d5db;
  padding: 2px 7px;
  min-height: 26px;
  transition: all 0.2s ease;
  box-shadow: 0 1px 1px rgba(0, 0, 0, 0.03);
}

.date-picker-compact :deep(.el-input__wrapper:hover) {
  border-color: #9ca3af;
}

.date-picker-compact :deep(.el-input.is-focus .el-input__wrapper) {
  border-color: #6366f1;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1);
}

.date-picker-compact :deep(.el-input__inner) {
  font-size: 11px;
  padding: 0;
  height: auto;
  line-height: 1.3;
}

.info-list-compact {
  margin: 0;
  padding-left: 16px;
  color: #475569;
  font-size: 10px;
  line-height: 1.5;
}

.info-list-compact li {
  margin-bottom: 4px;
}

.info-list-compact li:last-child {
  margin-bottom: 0;
}

.dialog-footer-compact {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.cancel-btn-compact,
.confirm-btn-compact {
  border-radius: 5px;
  padding: 6px 14px;
  font-weight: 500;
  font-size: 11px;
  transition: all 0.2s ease;
  height: 28px;
}

.cancel-btn-compact {
  border: 1px solid #dcdfe6;
  background: white;
}

.cancel-btn-compact:hover {
  border-color: #c0c4cc;
  background: #f5f7fa;
}

.confirm-btn-compact {
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  border: none;
  box-shadow: 0 2px 4px rgba(99, 102, 241, 0.2);
}

.confirm-btn-compact:hover:not(:disabled) {
  box-shadow: 0 4px 8px rgba(99, 102, 241, 0.3);
  transform: translateY(-1px);
}

.confirm-btn-compact:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.cancel-btn-compact :deep(.el-icon),
.confirm-btn-compact :deep(.el-icon) {
  margin-right: 4px;
  font-size: 12px;
}

/* 手入力部品注文ダイアログ - コンパクトUI */
.manual-order-dialog.manual-order-dialog--compact :deep(.el-dialog) {
  border-radius: 12px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12), 0 0 1px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.manual-order-dialog.manual-order-dialog--compact :deep(.el-dialog__header) {
  padding: 12px 16px;
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  color: #fff;
  border: none;
}

.manual-order-dialog.manual-order-dialog--compact :deep(.el-dialog__title) {
  color: #fff;
  font-size: 15px;
  font-weight: 600;
}

.manual-order-dialog.manual-order-dialog--compact :deep(.el-dialog__headerbtn) {
  top: 12px;
  width: 28px;
  height: 28px;
}

.manual-order-dialog.manual-order-dialog--compact :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: rgba(255, 255, 255, 0.9);
  font-size: 16px;
}

.manual-order-dialog.manual-order-dialog--compact :deep(.el-dialog__body) {
  padding: 0;
  max-height: 70vh;
  overflow-y: auto;
}

.manual-order-dialog.manual-order-dialog--compact :deep(.el-dialog__footer) {
  padding: 10px 16px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
}

/* 紧凑头部 */
.manual-order-content--compact {
  padding: 12px 16px 16px;
}

.manual-order-header-compact {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e2e8f0;
}

.manual-order-header-compact__icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.manual-order-header-compact__text h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.manual-order-header-compact__text p {
  margin: 2px 0 0;
  font-size: 12px;
  color: #64748b;
}

/* 表单紧凑 */
.manual-order-form--compact {
  margin-top: 0;
}

.manual-order-form--compact :deep(.el-form-item) {
  margin-bottom: 10px;
}

.manual-order-form--compact :deep(.el-form-item__label) {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
  padding-bottom: 4px;
  line-height: 1.3;
}

.manual-order-grid {
  display: grid;
  gap: 0 12px;
  margin-bottom: 12px;
}

.manual-order-grid--main {
  grid-template-columns: 120px 1fr;
}

.manual-order-grid--main .manual-order-field--span2 {
  grid-column: span 1;
}

.manual-order-grid--order {
  grid-template-columns: 1fr 1fr;
}

.manual-order-grid--order .manual-order-field--full {
  grid-column: 1 / -1;
}

.manual-order-field :deep(.el-input-number),
.manual-order-field :deep(.el-date-editor),
.manual-order-field :deep(.el-select) {
  width: 100%;
}

.manual-order-input :deep(.el-input__wrapper),
.manual-order-input :deep(.el-input__inner),
.manual-order-input :deep(.el-textarea__inner) {
  border-radius: 8px;
  font-size: 13px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.manual-order-input :deep(.el-input__wrapper:hover),
.manual-order-input :deep(.el-textarea__inner:hover) {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.manual-order-input :deep(.el-input__wrapper.is-focus),
.manual-order-input :deep(.el-textarea__inner:focus) {
  box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.25);
}

/* 部品詳細ブロック */
.manual-order-detail {
  margin-top: 12px;
  padding: 10px 12px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.manual-order-detail__title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 8px;
}

.manual-order-detail__title .el-icon {
  font-size: 14px;
  color: #6366f1;
}

.manual-order-detail__summary {
  margin-left: auto;
  font-size: 11px;
  font-weight: 500;
  color: #4f46e5;
}

.manual-order-detail__grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px 12px;
}

.manual-order-detail__item {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.manual-order-detail__label {
  font-size: 10px;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.manual-order-detail__value {
  font-size: 12px;
  color: #334155;
  font-weight: 500;
}

/* フッターボタン */
.manual-order-footer--compact {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.manual-order-btn {
  min-width: 88px;
}

.manual-order-btn :deep(.el-icon) {
  margin-right: 4px;
  font-size: 14px;
}

.manual-order-btn--confirm {
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  border: none;
}

.manual-order-btn--confirm:hover {
  background: linear-gradient(135deg, #4338ca 0%, #6d28d9 100%);
  border: none;
}

/* 旧样式保留兼容（其他可能引用） */
.manual-order-dialog:not(.manual-order-dialog--compact) {
  border-radius: 16px;
  overflow: hidden;
}

.manual-order-dialog:not(.manual-order-dialog--compact) :deep(.el-dialog) {
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
}

.manual-order-dialog:not(.manual-order-dialog--compact) :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  color: white;
  padding: 20px 24px;
  border-radius: 16px 16px 0 0;
}

.manual-order-dialog:not(.manual-order-dialog--compact) :deep(.el-dialog__title) {
  color: white;
  font-weight: 600;
  font-size: 18px;
}

.manual-order-dialog:not(.manual-order-dialog--compact) :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: white;
  font-size: 20px;
}

.manual-order-dialog:not(.manual-order-dialog--compact) :deep(.el-dialog__body) {
  padding: 0;
}

.manual-order-dialog:not(.manual-order-dialog--compact) :deep(.el-dialog__footer) {
  padding: 20px 24px;
  background-color: #f8f9fa;
  border-radius: 0 0 16px 16px;
}

.manual-order-content:not(.manual-order-content--compact) {
  padding: 24px;
}

.manual-order-form:not(.manual-order-form--compact) {
  margin-top: 20px;
}

.manual-order-form:not(.manual-order-form--compact) .form-section {
  background: white;
  border-radius: 12px;
  border: 1px solid #e9ecef;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  margin-bottom: 20px;
}

.manual-order-form:not(.manual-order-form--compact) .section-header {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-bottom: 1px solid #dee2e6;
  font-weight: 600;
  color: #495057;
  font-size: 14px;
}

.manual-order-form:not(.manual-order-form--compact) .section-header .el-icon {
  margin-right: 8px;
  color: #6366f1;
  font-size: 16px;
}

.manual-order-form:not(.manual-order-form--compact) .el-form-item {
  padding: 16px 20px;
  margin-bottom: 0;
  border-bottom: 1px solid #f1f3f4;
}

.manual-order-form:not(.manual-order-form--compact) .el-form-item:last-child {
  border-bottom: none;
}

.manual-order-form:not(.manual-order-form--compact) :deep(.el-form-item__label) {
  font-weight: 600;
  color: #495057;
}

.form-date-picker,
.form-input,
.form-select,
.form-input-number,
.form-textarea {
  width: 100%;
}

.form-date-picker :deep(.el-input__inner),
.form-input :deep(.el-input__inner),
.form-select :deep(.el-input__inner),
.form-textarea :deep(.el-textarea__inner) {
  border-radius: 10px;
  border: 2px solid #e2e8f0;
  padding: 12px 16px;
  font-size: 14px;
  transition: all 0.3s ease;
}

.form-date-picker :deep(.el-input__inner:focus),
.form-input :deep(.el-input__inner:focus),
.form-select :deep(.el-input__inner:focus),
.form-textarea :deep(.el-textarea__inner:focus) {
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.material-info {
  padding: 20px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 8px;
  margin-top: 16px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #dee2e6;
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  font-weight: 600;
  color: #495057;
  min-width: 100px;
}

.info-value {
  color: #2d3748;
  font-weight: 500;
}

.add-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border: none;
  color: white;
  border-radius: 6px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.add-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 5px 16px rgba(16, 185, 129, 0.4);
}

/* データ生成確認ダイアログ */
:deep(.data-generation-confirm-dialog) {
  border-radius: 16px !important;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15) !important;
  overflow: hidden !important;
}

:deep(.data-generation-confirm-dialog .el-message-box__header) {
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
  color: white !important;
  padding: 20px 24px !important;
  border-radius: 16px 16px 0 0 !important;
  border-bottom: none !important;
}

:deep(.data-generation-confirm-dialog .el-message-box__title) {
  color: white !important;
  font-weight: 600 !important;
  font-size: 18px !important;
  display: flex !important;
  align-items: center !important;
  gap: 8px !important;
}

:deep(.data-generation-confirm-dialog .el-message-box__title::before) {
  content: '⚠️' !important;
  font-size: 20px !important;
}

:deep(.data-generation-confirm-dialog .el-message-box__headerbtn) {
  top: 20px !important;
  right: 24px !important;
}

:deep(.data-generation-confirm-dialog .el-message-box__close) {
  color: white !important;
  font-size: 20px !important;
}

:deep(.data-generation-confirm-dialog .el-message-box__content) {
  padding: 24px !important;
  background: #f8f9fa !important;
  font-size: 15px !important;
  line-height: 1.6 !important;
  color: #2d3748 !important;
}

:deep(.data-generation-confirm-dialog .el-message-box__message) {
  white-space: pre-line !important;
  font-family: 'Hiragino Sans', 'Yu Gothic', 'Meiryo', sans-serif !important;
}

:deep(.data-generation-confirm-dialog .el-message-box__btns) {
  padding: 20px 24px !important;
  background: white !important;
  border-radius: 0 0 16px 16px !important;
  display: flex !important;
  justify-content: center !important;
  gap: 12px !important;
}

:deep(.data-generation-confirm-dialog .el-button) {
  border-radius: 10px !important;
  padding: 12px 24px !important;
  font-weight: 600 !important;
  font-size: 14px !important;
  transition: all 0.3s ease !important;
  min-width: 120px !important;
}

:deep(.data-generation-confirm-dialog .el-button--primary) {
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
  border: none !important;
  color: white !important;
}

:deep(.data-generation-confirm-dialog .el-button--primary:hover) {
  transform: translateY(-2px) !important;
  box-shadow: 0 8px 25px rgba(99, 102, 241, 0.4) !important;
}

:deep(.data-generation-confirm-dialog .el-button--default) {
  background: #f8f9fa !important;
  border: 2px solid #e2e8f0 !important;
  color: #6b7280 !important;
}

:deep(.data-generation-confirm-dialog .el-button--default:hover) {
  background: #e9ecef !important;
  border-color: #cbd5e0 !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
}

/* =============================================
   Responsive Design - 5 Breakpoints
   1280px / 1024px / 768px / 640px / 480px
   ============================================= */

/* Large screen: <= 1280px */
@media (max-width: 1280px) {
  .stats-grid {
    grid-template-columns: repeat(6, minmax(0, 1fr));
    gap: 8px;
  }

  .stat-card {
    padding: 8px 10px;
    gap: 8px;
  }

  .stat-card .stat-icon {
    width: 32px;
    height: 32px;
    font-size: 15px;
  }

  .stat-value {
    font-size: 15px;
  }

  .search-group.date-group {
    min-width: 300px;
  }
}

/* Laptop: <= 1024px */
@media (max-width: 1024px) {
  .part-order-container {
    padding: 8px 10px;
  }

  .stats-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 7px;
  }

  .search-row {
    flex-wrap: wrap;
    height: auto;
    gap: 6px;
  }

  .filter-item {
    border-right: none;
    padding: 0 8px 0 0;
  }

  .filter-item.date-group {
    flex-shrink: 1;
  }

  .filter-date-picker {
    width: 160px;
  }

  .tab-item {
    padding: 5px 10px;
    font-size: 11px;
  }

  .tab-item span {
    display: none;
  }

  .tab-item .el-icon {
    font-size: 15px;
  }

  .tab-item.active span {
    display: inline;
  }
}

/* Tablet / Large phone: <= 768px */
@media (max-width: 768px) {
  .part-order-container {
    padding: 6px 8px;
  }

  .page-header {
    flex-direction: column;
    gap: 6px;
    align-items: stretch;
    padding: 8px 12px;
  }

  .header-left {
    justify-content: center;
  }

  .header-actions {
    justify-content: center;
    flex-wrap: wrap;
  }

  .action-btn {
    flex: 1;
    justify-content: center;
    min-width: 100px;
  }

  .stats-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 6px;
  }

  .stat-card {
    padding: 6px 8px;
    min-height: 48px;
    gap: 6px;
  }

  .stat-card .stat-icon {
    width: 26px;
    height: 26px;
    font-size: 12px;
  }

  .stat-value {
    font-size: 13px;
  }

  .stat-label {
    font-size: 9px;
  }

  .search-container {
    padding: 6px 10px;
  }

  .search-row {
    flex-wrap: wrap;
    height: auto;
    gap: 4px;
  }

  .filter-item {
    flex: 1 1 auto;
    border-right: none;
    border-bottom: 1px solid #f0f0f0;
    padding: 4px 0;
    width: 100%;
    min-width: 0;
  }

  .filter-item:last-child {
    border-bottom: none;
  }

  .filter-date-picker {
    flex: 1;
    width: auto;
  }

  .filter-input,
  .filter-select {
    flex: 1;
    min-width: 0;
  }

  .table-header {
    flex-direction: column;
    align-items: stretch;
    gap: 6px;
    padding: 6px 8px;
  }

  .table-tabs {
    flex-wrap: wrap;
    justify-content: flex-start;
  }

  .table-actions {
    justify-content: flex-end;
  }

  .pagination-wrapper {
    padding: 6px 8px;
    overflow-x: auto;
  }

  :deep(.el-pagination) {
    flex-wrap: wrap;
    justify-content: center;
    gap: 4px;
  }

  :deep(.data-generation-confirm-dialog) {
    width: 95% !important;
    margin: 0 auto !important;
  }

  :deep(.data-generation-confirm-dialog .el-message-box__btns) {
    flex-direction: column !important;
    gap: 8px !important;
  }

  :deep(.data-generation-confirm-dialog .el-button) {
    width: 100% !important;
  }

  .summary-card-compact {
    flex-direction: column;
    gap: 6px;
  }

  .summary-item-compact {
    flex-direction: row;
    justify-content: space-between;
  }
}

/* Phone: <= 640px */
@media (max-width: 640px) {
  .stats-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 5px;
  }

  .stat-card {
    padding: 5px 6px;
    min-height: 44px;
    border-radius: 6px;
  }

  .stat-card::before {
    height: 2px;
  }

  .stat-value {
    font-size: 12px;
  }

  .stat-label {
    font-size: 8px;
  }

  .stat-card .stat-icon {
    display: none;
  }

  .main-title {
    font-size: 14px;
  }

  .subtitle {
    display: none;
  }

  .tab-item span {
    display: none;
  }

  .tab-item.active span {
    display: inline;
  }

  .search-btn,
  .reset-btn {
    flex: 1;
    justify-content: center;
  }
}

/* Small phone: <= 480px */
@media (max-width: 480px) {
  .part-order-container {
    padding: 4px 6px;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 5px;
  }

  .stat-card .stat-icon {
    display: flex;
    width: 22px;
    height: 22px;
    font-size: 10px;
  }

  .stat-value {
    font-size: 14px;
  }

  .stat-label {
    font-size: 9px;
  }

  .title-icon {
    display: none;
  }

  .page-header {
    padding: 6px 10px;
  }

  .action-btn {
    font-size: 11px;
    padding: 4px 10px;
  }

  .tab-item span {
    display: none;
  }

  .tab-item.active span {
    display: none;
  }

  .manual-order-dialog :deep(.el-dialog) {
    width: 100% !important;
    margin: 0 !important;
    border-radius: 0 !important;
  }

  .print-confirm-dialog :deep(.el-dialog) {
    width: 100% !important;
    margin: 0 !important;
  }
}

/* テーブル：シンプルスタイル（横罫線のみ・ゆとりある行高） */
:deep(.el-table) {
  --el-table-border-color: transparent;
  --el-table-bg-color: #ffffff;
  --el-table-tr-bg-color: #ffffff;
  --el-table-row-hover-bg-color: #f8fafc;
  --el-table-expanded-cell-bg-color: #fafbfc;
  color: #334155;
}

:deep(.el-table th.el-table__cell) {
  background: #f8fafc;
  color: #64748b;
  font-weight: 600;
  font-size: 12px;
  padding: 10px 0;
  border-bottom: 1px solid #e5e7eb;
  letter-spacing: 0.02em;
}

:deep(.el-table th.el-table__cell .cell) {
  line-height: 20px;
}

:deep(.el-table td.el-table__cell) {
  padding: 8px 0;
  border-bottom: 1px solid #f1f5f9;
  font-size: 13px;
  transition: background-color 0.15s ease;
}

/* 数量列：字号加大一号、粗体 */
:deep(.el-table td.current-stock-column .cell),
:deep(.el-table td.usage-quantity-column .cell),
:deep(.el-table td.order-quantity-column .cell) {
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
}

/* 列の色分けはヘッダー文字色のみで控えめに表現 */
:deep(.el-table th.current-stock-column) {
  color: #4f46e5;
}

:deep(.el-table th.usage-quantity-column) {
  color: #059669;
}

:deep(.el-table th.order-quantity-column) {
  color: #d97706;
}

:deep(.el-table td.usage-quantity-column .el-input-number .el-input__inner),
:deep(.el-table td.order-quantity-column .el-input-number .el-input__inner) {
  font-size: 14px !important;
  font-weight: 700 !important;
}

:deep(.el-table .el-table__body tr:hover > td.el-table__cell) {
  background-color: #f8fafc !important;
}

:deep(.el-input-number) {
  width: 100%;
}

:deep(.el-input-number .el-input__inner) {
  padding: calc(2px * 0.7) calc(6px * 0.7);
  font-size: 12px;
  height: calc(20px * 0.7);
  border-radius: 5px;
  border: none;
  transition: all 0.2s ease;
}

:deep(.el-input-number__increase),
:deep(.el-input-number__decrease) {
  width: calc(24px * 0.7);
  height: calc(14px * 0.7);
  font-size: 10px;
  border-radius: 4px;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  transition: all 0.2s ease;
}

:deep(.el-input-number__increase):hover,
:deep(.el-input-number__decrease):hover {
  background: #6366f1;
  color: white;
  border-color: #6366f1;
}

/* 手動使用数：文字色とフォーカス色のみエメラルド */
:deep(.usage-quantity-input .el-input__inner) {
  color: #047857 !important;
}

:deep(.el-table .usage-quantity-input .el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #6ee7b7 inset;
}

:deep(.el-table .usage-quantity-input .el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #10b981 inset, 0 0 0 3px rgba(16, 185, 129, 0.15);
}

/* 删除按钮样式 */
.delete-btn {
  padding: calc(4px * 0.7) calc(8px * 0.7) !important;
  font-size: 11px !important;
  border-radius: 6px !important;
  transition: all 0.3s ease !important;
  height: calc(24px * 0.7) !important;
  min-height: calc(24px * 0.7) !important;
}

.delete-btn:hover {
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4) !important;
}

/* 表格内输入框统一样式 */
:deep(.el-input) {
  font-size: 12px;
}

:deep(.el-input .el-input__inner) {
  padding: calc(2px * 0.7) calc(6px * 0.7);
  height: calc(20px * 0.7);
  border-radius: 5px;
  border: none;
  transition: all 0.2s ease;
  font-size: 11px;
}

/* 表内入力欄：白地・細い枠線 */
:deep(.el-table .el-input__wrapper) {
  min-height: 28px;
  padding: 0 8px;
  border-radius: 6px;
  background: #ffffff;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
  transition: box-shadow 0.15s ease;
}

:deep(.el-table .el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #cbd5e1 inset;
}

:deep(.el-table .el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #6366f1 inset, 0 0 0 3px rgba(99, 102, 241, 0.12);
}

:deep(.el-table .el-input__inner) {
  height: 26px;
  line-height: 26px;
  font-size: 13px;
}

/* 表格内文本样式 */
:deep(.el-table .cell) {
  padding: 0 12px;
  line-height: 22px;
  font-size: 13px;
}

/* 負数：赤字のみ */
.negative-number {
  color: #dc2626 !important;
  font-weight: 700 !important;
}

.table-section {
  margin-bottom: 8px;
}

/* 注文本数：文字色とフォーカス色のみアンバー */
:deep(.order-quantity-input .el-input__inner) {
  color: #b45309 !important;
}

:deep(.el-table .order-quantity-input .el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #fcd34d inset;
}

:deep(.el-table .order-quantity-input .el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #f59e0b inset, 0 0 0 3px rgba(245, 158, 11, 0.15);
}

/* 负数显示样式 */
.negative-number {
  color: #ef4444 !important;
  font-weight: 700 !important;
}

/* 印刷確認ダイアログ */
.print-confirm-dialog {
  border-radius: 12px;
  overflow: hidden;
}

.print-confirm-dialog :deep(.el-dialog) {
  border-radius: 12px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
}

.print-confirm-dialog :deep(.el-dialog__header) {
  padding: 10px 44px 10px 14px;
  margin-right: 0;
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 58%, #8b5cf6 100%);
  color: #ffffff;
  border-bottom: none;
}

.dialog-header-with-button {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  gap: 12px;
}

.dialog-title {
  font-size: 14px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: 0.03em;
}

.confirm-btn-header {
  border-radius: 8px;
  padding: 5px 14px;
  font-weight: 700;
  font-size: 12px;
  background: linear-gradient(135deg, #34d399 0%, #059669 100%);
  border: 1px solid rgba(255, 255, 255, 0.35);
  color: #ffffff;
  box-shadow:
    0 4px 12px rgba(5, 150, 105, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.confirm-btn-header:hover,
.confirm-btn-header:focus-visible {
  color: #ffffff;
  background: linear-gradient(135deg, #6ee7b7 0%, #10b981 100%);
  border-color: rgba(255, 255, 255, 0.5);
  transform: translateY(-1px);
  box-shadow:
    0 8px 18px rgba(5, 150, 105, 0.45),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
}

.confirm-btn-header :deep(.el-icon) {
  margin-right: 4px;
  font-size: 12px;
}

.print-confirm-dialog :deep(.el-dialog__headerbtn) {
  top: 10px;
  right: 14px;
}

.print-confirm-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: white;
  font-size: 16px;
}

.print-confirm-dialog :deep(.el-dialog__body) {
  padding: 0;
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}

.print-confirm-dialog :deep(.el-dialog__footer) {
  padding: 20px 24px;
  background-color: #f8f9fa;
  border-radius: 0 0 12px 12px;
}

/* 印刷確認ダイアログ - コンパクト */
.print-confirm-content-compact {
  padding: 10px 14px;
}

.form-sections-compact {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-section-compact {
  background: white;
  border-radius: 5px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  transition: all 0.2s ease;
}

.form-section-compact:hover {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.06);
  border-color: #6366f1;
}

.section-header-compact {
  display: flex;
  align-items: center;
  padding: 6px 10px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 1px solid #e5e7eb;
  font-weight: 600;
  color: #334155;
  font-size: 11px;
  gap: 5px;
}

.section-icon {
  color: #6366f1;
  font-size: 13px;
  flex-shrink: 0;
}

.section-title {
  font-weight: 600;
  letter-spacing: 0.2px;
}

.form-fields-compact {
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-field-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-field-row .field-label {
  min-width: 95px;
  font-size: 11px;
  font-weight: 500;
  color: #475569;
  flex-shrink: 0;
}

.form-input-compact,
.form-textarea-compact {
  flex: 1;
}

.form-input-compact :deep(.el-input__wrapper) {
  border-radius: 4px;
  border: 1px solid #d1d5db;
  padding: 2px 7px;
  min-height: 26px;
  transition: all 0.2s ease;
  box-shadow: 0 1px 1px rgba(0, 0, 0, 0.03);
}

.form-input-compact :deep(.el-input__wrapper:hover) {
  border-color: #9ca3af;
}

.form-input-compact :deep(.el-input.is-focus .el-input__wrapper) {
  border-color: #6366f1;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1);
}

.form-input-compact :deep(.el-input__inner) {
  font-size: 11px;
  padding: 0;
  height: auto;
  line-height: 1.3;
}

.form-textarea-compact :deep(.el-textarea__inner) {
  border-radius: 4px;
  border: 1px solid #d1d5db;
  padding: 4px 7px;
  font-size: 10px;
  line-height: 1.3;
  transition: all 0.2s ease;
  resize: vertical;
  min-height: 40px;
  box-shadow: 0 1px 1px rgba(0, 0, 0, 0.03);
}

.form-textarea-compact :deep(.el-textarea__inner:hover) {
  border-color: #9ca3af;
}

.form-textarea-compact :deep(.el-textarea__inner:focus) {
  border-color: #6366f1;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1);
}

/* フィルターボタン */
.filter-buttons {
  margin: 16px 0 12px 0;
  display: flex;
  justify-content: center;
}

.filter-btn {
  font-size: 12px;
  padding: 6px 12px;
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.filter-btn:not(.el-button--primary) {
  background: #f8f9fa;
  border-color: #dee2e6;
  color: #6c757d;
}

.filter-btn:not(.el-button--primary):hover {
  background: #e9ecef;
  border-color: #adb5bd;
  color: #495057;
  transform: translateY(-1px);
}

.filter-btn.el-button--primary {
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  border: none;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
}

/* 紧凑表格样式 */
.compact-table :deep(.el-table__header-wrapper) {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
}

.compact-table :deep(.el-table th) {
  background-color: transparent;
  color: #2d3748;
  font-weight: 600;
  font-size: 13px;
  padding: 6px 4px;
  border-bottom: 2px solid #dee2e6;
}

.compact-table :deep(.el-table td) {
  padding: 4px 4px;
  font-size: 13px;
  border-bottom: 1px solid #f1f3f4;
}

.compact-table :deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background-color: #f7fafc;
}

.compact-table :deep(.el-table__body tr:hover td) {
  background-color: #e3f2fd !important;
}

/* 滚动条样式 */
.compact-table :deep(.el-table__body-wrapper) {
  scrollbar-width: thin;
  scrollbar-color: #cbd5e0 #f7fafc;
}

.compact-table :deep(.el-table__body-wrapper::-webkit-scrollbar) {
  width: 6px;
  height: 6px;
}

.compact-table :deep(.el-table__body-wrapper::-webkit-scrollbar-track) {
  background: #f7fafc;
  border-radius: 3px;
}

.compact-table :deep(.el-table__body-wrapper::-webkit-scrollbar-thumb) {
  background: linear-gradient(135deg, #cbd5e0 0%, #a0aec0 100%);
  border-radius: 3px;
}

.compact-table :deep(.el-table__body-wrapper::-webkit-scrollbar-thumb:hover) {
  background: linear-gradient(135deg, #a0aec0 0%, #718096 100%);
}

.dialog-footer-compact {
  display: flex;
  justify-content: center;
  gap: 8px;
}

/* 初期在庫输入框样式 */
.initial-stock-input {
  width: 100%;
}

.initial-stock-input.positive-stock :deep(.el-input__inner) {
  color: #0369a1;
  font-weight: 700;
}

.initial-stock-input.positive-stock :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #0ea5e9 inset, 0 0 0 3px rgba(14, 165, 233, 0.15);
}

.adjustment-quantity-input :deep(.el-input__inner) {
  font-weight: 600;
  color: #334155;
}

.adjustment-quantity-input.is-negative :deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px #fca5a5 inset;
}

.adjustment-quantity-input.is-negative :deep(.el-input__inner) {
  color: #dc2626;
  font-weight: 700;
}

.stat-value.is-negative {
  color: #dc2626;
}

/* 表ヘッダー：キー操作ヒント */
.table-hint {
  margin-left: auto;
  margin-right: 12px;
  font-size: 11px;
  color: #94a3b8;
  white-space: nowrap;
}

.table-hint kbd {
  display: inline-block;
  padding: 0 5px;
  margin: 0 2px;
  font-family: inherit;
  font-size: 10px;
  line-height: 16px;
  color: #475569;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-bottom-width: 2px;
  border-radius: 4px;
}

/* 部品名セル：クリックで在庫推移グラフ */
:deep(.el-table td.part-name-cell .cell) {
  color: #4338ca;
  cursor: pointer;
}

:deep(.el-table td.part-name-cell:hover .cell) {
  text-decoration: underline;
  text-underline-offset: 3px;
}

.cancel-order-btn {
  font-weight: 600;
}

/* 発注提案ボタン */
.reorder-badge {
  margin-right: 4px;
}

.table-actions .reorder-btn {
  color: #b45309;
  background: #fffbeb;
  box-shadow: 0 0 0 1px #fcd34d inset;
}

.table-actions .reorder-btn:hover,
.table-actions .reorder-btn:focus-visible {
  color: #92400e;
  background: #fef3c7;
  transform: translateY(-1px);
  box-shadow: 0 0 0 1px #f59e0b inset, 0 6px 14px rgba(245, 158, 11, 0.25);
}

/* 発注提案ダイアログ */
.reorder-dialog :deep(.el-dialog) {
  border-radius: 14px;
  overflow: hidden;
}

.reorder-dialog :deep(.el-dialog__header) {
  padding: 12px 16px;
  margin-right: 0;
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
}

.reorder-dialog :deep(.el-dialog__title) {
  color: #ffffff;
  font-size: 15px;
  font-weight: 700;
}

.reorder-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: #ffffff;
}

.reorder-dialog :deep(.el-dialog__body) {
  padding: 14px 16px 6px;
}

.reorder-dialog :deep(.el-dialog__footer) {
  padding: 10px 16px;
  background: #f8fafc;
  border-top: 1px solid #e5e7eb;
}

.reorder-toolbar {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

.reorder-toolbar__field {
  display: flex;
  align-items: center;
  gap: 6px;
}

.reorder-toolbar__label {
  font-size: 12px;
  font-weight: 600;
  color: #475569;
}

.reorder-toolbar__summary {
  margin-left: auto;
  font-size: 13px;
  color: #334155;
}

.reorder-toolbar__urgent {
  color: #dc2626;
  font-weight: 700;
}

.reorder-note {
  margin: 8px 0 10px;
  font-size: 11px;
  line-height: 1.6;
  color: #94a3b8;
}

.reorder-part {
  display: flex;
  flex-direction: column;
  cursor: pointer;
}

.reorder-part__name {
  color: #4338ca;
  font-weight: 600;
  line-height: 18px;
}

.reorder-part:hover .reorder-part__name {
  text-decoration: underline;
  text-underline-offset: 3px;
}

.reorder-part__cd,
.reorder-sub {
  font-size: 11px;
  color: #94a3b8;
  line-height: 16px;
}

.reorder-sub {
  margin-left: 6px;
}

.reorder-tag {
  margin-left: 4px;
}

.reorder-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.reorder-footer__total {
  margin-right: auto;
  font-size: 12px;
  color: #475569;
}

/* 部品在庫推移グラフ */
.part-chart-drawer :deep(.el-drawer__header) {
  margin-bottom: 0;
  padding: 14px 18px;
  color: #0f172a;
  font-weight: 700;
  border-bottom: 1px solid #eef2f7;
}

.part-chart-drawer :deep(.el-drawer__body) {
  padding: 14px 18px;
  background: #fbfcfe;
}

.part-chart {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.part-chart__toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.part-chart__kpis {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
}

.part-chart__kpi {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px 10px;
  background: #ffffff;
  border: 1px solid #eef2f7;
  border-radius: 10px;
}

.part-chart__kpi-label {
  font-size: 11px;
  color: #94a3b8;
}

.part-chart__kpi-value {
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.part-chart__kpi-value small {
  font-size: 11px;
  font-weight: 500;
  color: #94a3b8;
}

.part-chart__canvas {
  min-height: 440px;
  padding: 12px;
  background: #ffffff;
  border: 1px solid #eef2f7;
  border-radius: 12px;
}

.initial-stock-input.positive-stock :deep(.el-input-number__increase),
.initial-stock-input.positive-stock :deep(.el-input-number__decrease) {
  background-color: #e0f2fe;
  color: #0369a1;
  border-color: #0ea5e9;
}

.initial-stock-input.positive-stock :deep(.el-input-number__increase):hover,
.initial-stock-input.positive-stock :deep(.el-input-number__decrease):hover {
  background-color: #bae6fd;
  color: #0284c7;
}

/* 調整数输入框样式 */
.adjustment-quantity-input {
  width: 100%;
}


</style>
