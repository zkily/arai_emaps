<template>
  <div class="part-order-container po-modern pb-std" :class="`po-tab-${activeTab}`">
    <!-- ページヘッダー -->
    <div class="page-header pb-hero pb-hero--page">
      <div class="page-header-fx pb-bubbles" aria-hidden="true" />
      <div class="header-left">
        <div class="title-section">
          <div class="title-icon">
            <el-icon><ShoppingCart /></el-icon>
          </div>
          <div class="title-text">
            <h1 class="main-title pb-hero-title">部品在庫管理(発注・使用)</h1>
            <p class="subtitle pb-hero-desc">部品の在庫推移・使用実績・発注を一元管理</p>
            <div class="header-chips">
              <span class="header-chip">
                <el-icon><Calendar /></el-icon>
                {{ headerDateRangeText }}
              </span>
              <span class="header-chip">
                <el-icon><Shop /></el-icon>
                仕入先 {{ searchForm.supplier.length ? `${searchForm.supplier.length}社` : '全て' }}
              </span>
              <span v-if="searchForm.part_cd" class="header-chip">
                <el-icon><Search /></el-icon>
                部品 {{ searchForm.part_cd }}
              </span>
            </div>
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
              label="使用数調整"
              width="140"
              align="center"
              class-name="usage-quantity-column"
            >
              <template #default="{ row }">
                <el-input-number
                  :key="`manual-usage-${row.id}`"
                  :model-value="emptyIfZero(row.manual_usage)"
                  :min="-999999"
                  :max="999999"
                  :precision="0"
                  :controls="false"
                  :value-on-clear="null"
                  size="small"
                  :class="['usage-quantity-input', { 'is-negative': isNegative(row.manual_usage) }]"
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
              label="使用数調整"
              width="140"
              align="center"
              class-name="usage-quantity-column"
            >
              <template #default="{ row }">
                <el-input-number
                  :key="`manual-usage-${row.id}`"
                  :model-value="emptyIfZero(row.manual_usage)"
                  :min="-999999"
                  :max="999999"
                  :precision="0"
                  :controls="false"
                  :value-on-clear="null"
                  size="small"
                  :class="['usage-quantity-input', { 'is-negative': isNegative(row.manual_usage) }]"
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
              prop="stock_trend"
              label="在庫推移"
              width="100"
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

    <!-- 注文書発行ダイアログ（納入日×仕入先ごとに発行） -->
    <el-dialog
      v-model="printConfirmDialogVisible"
      width="960px"
      align-center
      :close-on-click-modal="false"
      :show-close="false"
      class="order-sheet-dialog"
    >
      <template #header="{ close, titleId }">
        <div class="osd-head">
          <div class="osd-head__icon"><el-icon><Printer /></el-icon></div>
          <div class="osd-head__text">
            <h3 :id="titleId" class="osd-head__title">注文書発行</h3>
            <p class="osd-head__sub">対象月・仕入先ごとに注文書を作成し、印刷・PDF保存します</p>
          </div>
          <button type="button" class="osd-close" aria-label="閉じる" @click="close">
            <el-icon><Close /></el-icon>
          </button>
        </div>
      </template>

      <div class="osd-body">
        <div class="osd-target">
          <div class="osd-field">
            <label class="osd-label">対象月</label>
            <el-date-picker
              v-model="printForm.month"
              type="month"
              format="YYYY年MM月"
              value-format="YYYY-MM"
              :clearable="false"
              size="small"
              style="width: 140px"
              @change="loadPrintOrders"
            />
          </div>
          <div class="osd-field">
            <label class="osd-label">納入期間</label>
            <span class="osd-period">{{ printPeriod.start }} ～ {{ printPeriod.end }}</span>
          </div>
          <div class="osd-field osd-field--grow">
            <label class="osd-label">仕入先（画面の絞り込み）</label>
            <el-select
              v-model="printForm.supplier"
              size="small"
              placeholder="仕入先を選択"
              :loading="printLoading"
              :disabled="printSupplierGroups.length <= 1"
              @change="onPrintSupplierChange"
            >
              <el-option
                v-for="g in printSupplierGroups"
                :key="g.supplier"
                :label="`${g.supplier}（${g.items.length}件）`"
                :value="g.supplier"
              />
            </el-select>
          </div>
        </div>

        <div class="osd-grid">
          <div class="osd-section">
            <div class="osd-section__title"><el-icon><User /></el-icon>宛先</div>
            <div class="osd-field">
              <label class="osd-label">会社名</label>
              <el-input v-model="printForm.recipientCompany" size="small" placeholder="〇〇株式会社 御中" />
            </div>
            <div class="osd-field">
              <label class="osd-label">担当者</label>
              <el-input v-model="printForm.recipientPersons" size="small" placeholder="担当者名（任意）" />
            </div>
          </div>
          <div class="osd-section">
            <div class="osd-section__title"><el-icon><EditPen /></el-icon>発行情報</div>
            <div class="osd-row">
              <div v-for="role in ORDER_SHEET_PERSON_ROLES" :key="role.key" class="osd-field">
                <label class="osd-label">{{ role.label }}</label>
                <el-select
                  v-model="printForm[role.key]"
                  size="small"
                  filterable
                  allow-create
                  default-first-option
                  clearable
                  :reserve-keyword="false"
                  placeholder="選択 または 入力して Enter で追加"
                  popper-class="osd-person-popper"
                  @change="(v: string) => onOrderSheetPersonChange(role.key, v)"
                >
                  <el-option
                    v-for="name in orderSheetPeople[role.key]"
                    :key="name"
                    :label="name"
                    :value="name"
                  >
                    <span class="osd-person-option">
                      <span>{{ name }}</span>
                      <el-icon
                        class="osd-person-option__del"
                        title="候補から削除"
                        @click.stop="removeOrderSheetPerson(role.key, name)"
                      >
                        <Close />
                      </el-icon>
                    </span>
                  </el-option>
                </el-select>
              </div>
            </div>
            <div class="osd-field">
              <label class="osd-label">納入場所</label>
              <el-input v-model="printForm.deliveryPlace" size="small" placeholder="例：部品置場（任意）" />
            </div>
          </div>
        </div>

        <div class="osd-section">
          <div class="osd-section__title">
            <el-icon><List /></el-icon>明細プレビュー
            <span v-if="printItems.length" class="osd-section__meta">
              {{ printItems.length }}件 ／ 注文数計 {{ formatNumber(printTotals.qty) }} ／ 合計 {{ formatCurrency(printTotals.amount) }}
            </span>
            <span v-if="printSheetInfo" class="osd-section__meta osd-section__meta--sheet">
              注文書：{{ printSheetInfo.parts }}品目 ／ A4横 {{ printSheetInfo.pages }}ページ{{
                printSheetInfo.tierCount > 1 ? `（${printSheetInfo.tierCount}段表示）` : ''
              }}
            </span>
          </div>
          <el-table
            v-loading="printLoading"
            :data="printItems"
            size="small"
            max-height="230"
            class="osd-table"
            empty-text="対象の注文がありません"
          >
            <el-table-column type="index" label="No" width="48" align="center" />
            <el-table-column prop="date" label="納入日" width="96" align="center" />
            <el-table-column prop="part_name" label="部品名" min-width="160" show-overflow-tooltip />
            <el-table-column prop="standard_spec" label="規格" width="100" show-overflow-tooltip />
            <el-table-column prop="part_material" label="材料" width="90" show-overflow-tooltip />
            <el-table-column label="収容数" width="70" align="right">
              <template #default="{ row }">{{ row.capacity_qty ? formatNumber(row.capacity_qty) : '' }}</template>
            </el-table-column>
            <el-table-column prop="settlement_type" label="区分" width="80" align="center" />
            <el-table-column label="注文数" width="80" align="right">
              <template #default="{ row }">{{ formatNumber(row.order_quantity) }}</template>
            </el-table-column>
            <el-table-column label="単価" width="90" align="right">
              <template #default="{ row }">{{ formatCurrency(Number(row.unit_price) || 0) }}</template>
            </el-table-column>
            <el-table-column label="金額" width="110" align="right">
              <template #default="{ row }">{{ formatCurrency(orderSheetAmount(row)) }}</template>
            </el-table-column>
          </el-table>
        </div>

        <div class="osd-section">
          <div class="osd-section__title"><el-icon><InfoFilled /></el-icon>備考・注意事項</div>
          <div class="osd-notes">
            <el-input v-model="printForm.note1" type="textarea" :rows="2" size="small" />
            <el-input v-model="printForm.note2" type="textarea" :rows="2" size="small" />
          </div>
        </div>
      </div>

      <template #footer>
        <div class="osd-footer">
          <span v-if="printFileName" class="osd-footer__file">
            <el-icon><Document /></el-icon>{{ printFileName }}
          </span>
          <el-button size="small" @click="printConfirmDialogVisible = false">キャンセル</el-button>
          <el-button
            type="primary"
            size="small"
            class="osd-footer__print"
            :loading="printPdfSaving"
            :disabled="!printItems.length"
            @click="confirmPrint"
          >
            <el-icon><Printer /></el-icon>印刷・PDF保存
          </el-button>
        </div>
      </template>
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
      :show-close="false"
    >
      <template #header="{ close, titleId }">
        <div class="pcd-head">
          <div class="pcd-head__main">
            <div class="pcd-head__icon"><el-icon><DataLine /></el-icon></div>
            <div class="pcd-head__text">
              <div class="pcd-head__eyebrow">在庫推移チャート</div>
              <h3 :id="titleId" class="pcd-head__title">{{ chartPart?.part_name || '在庫推移' }}</h3>
              <div class="pcd-head__chips">
                <span v-if="chartPart?.part_cd" class="pcd-chip pcd-chip--code">{{ chartPart.part_cd }}</span>
                <span class="pcd-chip">
                  <el-icon><Shop /></el-icon>{{ chartPart?.supplier_name || '仕入先未設定' }}
                </span>
                <span class="pcd-chip">
                  <el-icon><Timer /></el-icon>LT {{ chartKpis.leadTime }} 日
                </span>
              </div>
            </div>
          </div>
          <div class="pcd-head__side">
            <span
              v-if="chartDays.length"
              :class="['pcd-status', chartKpis.shortageDate ? 'is-danger' : 'is-safe']"
            >
              <i class="pcd-status__dot" />
              {{ chartKpis.shortageDate ? '欠品予測あり' : '在庫安定' }}
            </span>
            <button type="button" class="pcd-close" aria-label="閉じる" @click="close">
              <el-icon><Close /></el-icon>
            </button>
          </div>
        </div>
      </template>

      <div class="pcd-body">
        <div class="pcd-toolbar">
          <div class="pcd-toolbar__label"><el-icon><Calendar /></el-icon>表示期間</div>
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
            class="pcd-toolbar__range"
            @change="onChartRangeChange"
          />
          <div class="pcd-month">
            <button type="button" class="pcd-month__btn" @click="shiftChartMonth(-1)">
              <el-icon><ArrowLeft /></el-icon>前月
            </button>
            <button
              type="button"
              :class="['pcd-month__btn', 'pcd-month__btn--current', { 'is-active': chartMonthOffset !== null }]"
              @click="shiftChartMonth(0)"
            >
              {{ chartMonthOffset !== null ? chartMonthLabel : '今月' }}
            </button>
            <button type="button" class="pcd-month__btn" @click="shiftChartMonth(1)">
              次月<el-icon><ArrowRight /></el-icon>
            </button>
          </div>
          <div class="pcd-segment">
            <button
              v-for="p in chartPresetOptions"
              :key="p.value"
              type="button"
              :class="['pcd-segment__item', { 'is-active': chartPreset === p.value }]"
              @click="chartPreset = p.value; chartMonthOffset = null; applyChartPreset()"
            >
              {{ p.label }}
            </button>
          </div>
        </div>

        <div class="pcd-kpis">
          <div :class="['pcd-kpi', chartKpis.minTrend < 0 ? 'pcd-kpi--rose' : 'pcd-kpi--violet']">
            <div class="pcd-kpi__icon"><el-icon><DataLine /></el-icon></div>
            <div class="pcd-kpi__body">
              <div class="pcd-kpi__label">最小在庫推移</div>
              <div class="pcd-kpi__value" :class="{ 'is-negative': chartKpis.minTrend < 0 }">
                {{ formatNumber(chartKpis.minTrend) }}
              </div>
              <div class="pcd-kpi__sub">{{ chartKpis.minTrendDate || '—' }}</div>
            </div>
          </div>
          <div :class="['pcd-kpi', chartKpis.shortageDate ? 'pcd-kpi--rose' : 'pcd-kpi--emerald']">
            <div class="pcd-kpi__icon">
              <el-icon>
                <WarningFilled v-if="chartKpis.shortageDate" />
                <CircleCheckFilled v-else />
              </el-icon>
            </div>
            <div class="pcd-kpi__body">
              <div class="pcd-kpi__label">欠品予定日</div>
              <div class="pcd-kpi__value" :class="{ 'is-negative': !!chartKpis.shortageDate }">
                {{ chartKpis.shortageDate ? chartKpis.shortageDate.slice(5).replace('-', '/') : 'なし' }}
              </div>
              <div class="pcd-kpi__sub">{{ chartKpis.shortageDate ? '在庫推移がマイナス' : '期間内は欠品なし' }}</div>
            </div>
          </div>
          <div class="pcd-kpi pcd-kpi--sky">
            <div class="pcd-kpi__icon"><el-icon><TrendCharts /></el-icon></div>
            <div class="pcd-kpi__body">
              <div class="pcd-kpi__label">期間内 使用数</div>
              <div class="pcd-kpi__value" :class="{ 'is-negative': chartKpis.totalUsage < 0 }">
                {{ formatNumber(chartKpis.totalUsage) }}
              </div>
              <div class="pcd-kpi__sub">実績＋調整</div>
            </div>
          </div>
          <div class="pcd-kpi pcd-kpi--amber">
            <div class="pcd-kpi__icon"><el-icon><ShoppingCart /></el-icon></div>
            <div class="pcd-kpi__body">
              <div class="pcd-kpi__label">期間内 注文本数</div>
              <div class="pcd-kpi__value">{{ formatNumber(chartKpis.totalOrder) }}</div>
              <div class="pcd-kpi__sub">発注済み合計</div>
            </div>
          </div>
        </div>

        <div class="pcd-chart">
          <div class="pcd-chart__head">
            <span class="pcd-chart__title">日別推移</span>
            <div class="pcd-chart__tools">
              <span class="pcd-chart__hint">左軸：在庫 ／ 右軸：数量</span>
              <label class="pcd-chart__switch">
                <el-switch v-model="chartShowValues" size="small" />
                <span>数値表示</span>
              </label>
            </div>
          </div>
          <div v-loading="chartLoading" class="pcd-chart__canvas">
            <ChartWrapper
              v-if="chartDays.length"
              :data="chartData"
              :options="chartOptions"
              height="400px"
            />
            <el-empty v-else-if="!chartLoading" description="期間内のデータがありません" />
          </div>
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
  Check,
  Document,
  List,
  DataLine,
  TrendCharts,
  Shop,
  Timer,
  WarningFilled,
  CircleCheckFilled,
  Bell,
} from '@element-plus/icons-vue'
import {
  syncPartStockFromMaster,
  getPartStockSupplierNames,
  getPartStockList,
  updatePartStock,
  savePartOrderPdf,
  cancelPartStockOrder,
  getPartReorderSuggestions,
} from '@/api/part'
import type { PartReorderSuggestion } from '@/api/part'
import ChartWrapper from '@/components/ChartWrapper.vue'
import { Chart as ChartJS } from 'chart.js'
import { getPartList } from '@/api/master/partMaster'
import html2canvas from 'html2canvas'
import { jsPDF } from 'jspdf'
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
  /** 部品マスタ：部品材料・収容数・決済種類（一覧 API で付与） */
  part_material?: string | null
  capacity_qty?: number | null
  settlement_type?: string | null
  /** 旧材料 API 等との混在レスポンス互換 */
  material_name?: string
  material_cd?: string
}

interface SupplierOption {
  label: string
  value: string
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
const printLoading = ref(false)
/** 注文書発行ダイアログ：対象月・画面で絞り込んだ仕入先の注文 */
const printOrders = ref<PartOrderItem[]>([])
/** ダイアログを開いた時点の画面の仕入先絞り込み */
const printSuppliers = ref<string[]>([])
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

const searchForm = reactive({
  /** 空＝全件。部品マスタから選択（部品CD） */
  part_cd: '',
  dateRange: [getTodayJapanStr(), getTodayJapanStr()] as string[], // デフォルトは日本時間の当日
  supplier: [] as string[],
})

const headerDateRangeText = computed(() => {
  const [start, end] = searchForm.dateRange || []
  if (!start && !end) return '期間 全て'
  if (start === end) return start
  return `${start || '—'} 〜 ${end || '—'}`
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

// 注文書の承認者・発行者候補（ブラウザの localStorage に保持）
type OrderSheetPersonRole = 'approver' | 'issuer'
const ORDER_SHEET_PERSON_ROLES: { key: OrderSheetPersonRole; label: string }[] = [
  { key: 'approver', label: '承認者' },
  { key: 'issuer', label: '発行者' },
]
const ORDER_SHEET_PEOPLE_STORAGE_KEY = 'smart-emaps:part-order-sheet-people:v2'

const loadOrderSheetPeople = () => {
  const state = {
    approver: ['小森'],
    issuer: ['孫'],
    last: { approver: '小森', issuer: '孫' } as Record<OrderSheetPersonRole, string>,
  }
  try {
    const saved = JSON.parse(localStorage.getItem(ORDER_SHEET_PEOPLE_STORAGE_KEY) || 'null')
    for (const { key } of ORDER_SHEET_PERSON_ROLES) {
      if (Array.isArray(saved?.[key])) state[key] = saved[key].filter((n: unknown) => typeof n === 'string')
      if (typeof saved?.last?.[key] === 'string') state.last[key] = saved.last[key]
    }
  } catch {
    // 破損データは既定値で上書き
  }
  return state
}

const initialOrderSheetPeople = loadOrderSheetPeople()
const orderSheetPeople = reactive<Record<OrderSheetPersonRole, string[]>>({
  approver: initialOrderSheetPeople.approver,
  issuer: initialOrderSheetPeople.issuer,
})

const saveOrderSheetPeople = () => {
  try {
    localStorage.setItem(
      ORDER_SHEET_PEOPLE_STORAGE_KEY,
      JSON.stringify({
        approver: orderSheetPeople.approver,
        issuer: orderSheetPeople.issuer,
        last: { approver: printForm.approver, issuer: printForm.issuer },
      }),
    )
  } catch {
    // localStorage 不可の環境では保持しない
  }
}

const onOrderSheetPersonChange = (role: OrderSheetPersonRole, value: string) => {
  const name = (value || '').trim()
  printForm[role] = name
  if (name && !orderSheetPeople[role].includes(name)) {
    orderSheetPeople[role].push(name)
    ElMessage.success(`「${name}」を${role === 'approver' ? '承認者' : '発行者'}候補に追加しました`)
  }
  saveOrderSheetPeople()
}

const removeOrderSheetPerson = (role: OrderSheetPersonRole, name: string) => {
  orderSheetPeople[role] = orderSheetPeople[role].filter((n) => n !== name)
  if (printForm[role] === name) printForm[role] = ''
  saveOrderSheetPeople()
}

// 注文書発行フォーム（宛先は選択した仕入先から自動入力）
const printForm = reactive({
  /** 対象月 YYYY-MM（納入日がこの月の注文を対象） */
  month: '',
  supplier: '',
  recipientCompany: '',
  recipientPersons: '',
  approver: initialOrderSheetPeople.last.approver,
  issuer: initialOrderSheetPeople.last.issuer,
  deliveryPlace: '',
  note1: '1.支払期日には法定税率による消費税額及び地方消費税分を加算して支払います。',
  note2:
    '2.支払期日・支払方法・検査完了期日・有償支給原材料代金の決済期日及び方法については、令和8年7月1日の「支払方法等について」によります。',
})

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

/** 同一部品の現在在庫を一覧へ反映（使用数調整・注文本数更新後） */
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
      ElMessage.success('使用数調整を更新しました')
      lastSavedManualUsage.set(row.id, next)
      const data = (response as any)?.data
      if (data?.current_stock !== undefined) {
        row.current_stock = data.current_stock
      }
      await patchCurrentStockForPart(row.part_cd)
    } else {
      ElMessage.error('使用数調整の更新に失敗しました')
    }
  } catch (error: any) {
    console.error('使用数調整更新失敗:', error)
    ElMessage.error(`使用数調整の更新に失敗しました: ${error.message || 'ネットワークエラー'}`)
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
const chartPresetOptions: { value: ChartPreset; label: string }[] = [
  { value: 'short', label: '前1週〜後2週' },
  { value: 'mid', label: '前2週〜後1ヶ月' },
  { value: 'long', label: '前1ヶ月〜後3ヶ月' },
]

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

/** 月表示：今月からのオフセット（null は月表示以外） */
const chartMonthOffset = ref<number | null>(null)

const chartMonthStart = (offset: number) => {
  const [y, m] = getTodayJapanStr().split('-').map(Number)
  return new Date(y, m - 1 + offset, 1)
}

const chartMonthLabel = computed(() => {
  if (chartMonthOffset.value === null) return ''
  const d = chartMonthStart(chartMonthOffset.value)
  return `${d.getFullYear()}年${d.getMonth() + 1}月`
})

/** 前月(-1)・次月(+1) は表示中の月から1ヶ月ずつ移動、今月(0)は当月へ戻す */
const shiftChartMonth = (delta: -1 | 0 | 1) => {
  const offset = delta === 0 ? 0 : (chartMonthOffset.value ?? 0) + delta
  const first = chartMonthStart(offset)
  const fmt = (d: Date) =>
    `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  chartMonthOffset.value = offset
  chartPreset.value = ''
  chartRange.value = [fmt(first), fmt(new Date(first.getFullYear(), first.getMonth() + 1, 0))]
  loadPartChart()
}

const onChartRangeChange = () => {
  chartPreset.value = ''
  chartMonthOffset.value = null
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
  chartMonthOffset.value = null
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

/** Chart.js scriptable color: チャート領域の高さに合わせた縦グラデーション */
const verticalGradient =
  (top: string, bottom: string, fallback: string) =>
  (ctx: any) => {
    const area = ctx.chart?.chartArea
    if (!area) return fallback
    const g = ctx.chart.ctx.createLinearGradient(0, area.top, 0, area.bottom)
    g.addColorStop(0, top)
    g.addColorStop(1, bottom)
    return g
  }

/**
 * データセットごとの数値ラベル設定（dataset.valueLabel）。
 * keyIndices は常に候補、それ以外は minGap(px) 間隔で間引き。優先度順に配置し重なるものは省略する。
 */
interface ValueLabelCfg {
  color: string
  position?: 'above' | 'below'
  keyIndices?: number[]
  keyPriority: number
  basePriority: number
  minGap: number
  skipZero?: boolean
}

const partChartValueLabelsPlugin = {
  id: 'partChartValueLabels',
  afterDatasetsDraw(chart: any, _args: unknown, opts: { display?: boolean }) {
    if (!opts?.display) return
    const area = chart.chartArea
    const count = chart.data?.labels?.length ?? 0
    if (!area || !count) return
    const spacing = area.width / count
    const ctx: CanvasRenderingContext2D = chart.ctx
    const cands: { x: number; y: number; text: string; color: string; priority: number }[] = []

    chart.data.datasets.forEach((ds: any, di: number) => {
      const cfg: ValueLabelCfg | undefined = ds.valueLabel
      if (!cfg || !chart.isDatasetVisible(di)) return
      const meta = chart.getDatasetMeta(di)
      const keys = new Set(cfg.keyIndices ?? [])
      const step = Math.max(1, Math.ceil(cfg.minGap / spacing))
      ;(ds.data as number[]).forEach((raw, i) => {
        const v = Number(raw) || 0
        if (cfg.skipZero && v === 0) return
        const isKey = keys.has(i)
        if (!isKey && i % step !== 0) return
        const el = meta.data[i]
        if (!el) return
        const below = cfg.position === 'below' || (meta.type === 'bar' && v < 0)
        cands.push({
          x: el.x,
          y: below ? el.y + 13 : el.y - 6,
          text: v.toLocaleString('ja-JP'),
          color: v < 0 ? '#dc2626' : cfg.color,
          priority: isKey ? cfg.keyPriority : cfg.basePriority,
        })
      })
    })
    if (!cands.length) return

    ctx.save()
    ctx.font = '700 10px "Segoe UI", "Hiragino Sans", "Meiryo", sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'bottom'
    ctx.lineJoin = 'round'
    ctx.lineWidth = 3
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.95)'
    const placed: { l: number; r: number; t: number; b: number }[] = []
    cands.sort((a, b) => b.priority - a.priority || a.x - b.x)
    for (const c of cands) {
      const w = ctx.measureText(c.text).width
      const box = { l: c.x - w / 2 - 2, r: c.x + w / 2 + 2, t: c.y - 12, b: c.y + 1 }
      if (box.l < area.left - 4 || box.r > area.right + 4 || box.t < 0 || box.b > area.bottom) continue
      if (placed.some((p) => box.l < p.r && box.r > p.l && box.t < p.b && box.b > p.t)) continue
      placed.push(box)
      ctx.strokeText(c.text, c.x, c.y)
      ctx.fillStyle = c.color
      ctx.fillText(c.text, c.x, c.y)
    }
    ctx.restore()
  },
}
ChartJS.register(partChartValueLabelsPlugin)

/** 折れ線の代表点：先頭・末尾・最小・最大・当日・正負の切替点 */
const lineKeyIndices = (values: number[], todayIndex: number): number[] => {
  if (!values.length) return []
  const keys = new Set<number>([0, values.length - 1])
  let min = 0
  let max = 0
  values.forEach((v, i) => {
    if (v < values[min]) min = i
    if (v > values[max]) max = i
    if (i > 0 && values[i - 1] >= 0 !== v >= 0) keys.add(i)
  })
  keys.add(min)
  keys.add(max)
  if (todayIndex >= 0) keys.add(todayIndex)
  return [...keys]
}

const maxIndexOf = (values: number[]): number[] => {
  let idx = -1
  values.forEach((v, i) => {
    if (v > 0 && (idx < 0 || v > values[idx])) idx = i
  })
  return idx < 0 ? [] : [idx]
}

const chartShowValues = ref(true)

const chartData = computed(() => {
  const days = chartDays.value
  const today = getTodayJapanStr()
  const todayIndex = days.findIndex((d) => d.date >= today)
  const trend = days.map((d) => d.trend)
  const current = days.map((d) => d.current)
  const usage = days.map((d) => d.usage)
  const plan = days.map((d) => d.plan)
  const order = days.map((d) => d.order)
  const labelCfg: Record<string, ValueLabelCfg> = {
    trend: { color: '#7c3aed', position: 'below', keyIndices: lineKeyIndices(trend, todayIndex), keyPriority: 100, basePriority: 20, minGap: 46 },
    current: { color: '#4338ca', keyIndices: lineKeyIndices(current, todayIndex), keyPriority: 90, basePriority: 25, minGap: 46 },
    order: { color: '#b45309', keyIndices: order.flatMap((v, i) => (v ? [i] : [])), keyPriority: 95, basePriority: 0, minGap: 0, skipZero: true },
    usage: { color: '#047857', keyIndices: maxIndexOf(usage), keyPriority: 60, basePriority: 12, minGap: 36, skipZero: true },
    plan: { color: '#0369a1', keyIndices: maxIndexOf(plan), keyPriority: 40, basePriority: 5, minGap: 44, skipZero: true },
  }
  return {
    labels: days.map((d) => d.date.slice(5).replace('-', '/')),
    datasets: [
      {
        type: 'line',
        label: '在庫推移',
        data: trend,
        valueLabel: labelCfg.trend,
        borderColor: '#8b5cf6',
        borderDash: [6, 4],
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 5,
        pointHoverBackgroundColor: '#8b5cf6',
        pointHoverBorderColor: '#fff',
        pointHoverBorderWidth: 2,
        tension: 0.35,
        fill: false,
        yAxisID: 'y',
        order: 0,
      },
      {
        type: 'line',
        label: '現在在庫',
        data: current,
        valueLabel: labelCfg.current,
        borderColor: '#4f46e5',
        backgroundColor: verticalGradient('rgba(79, 70, 229, 0.32)', 'rgba(79, 70, 229, 0.02)', 'rgba(79, 70, 229, 0.08)'),
        borderWidth: 2.5,
        pointRadius: 0,
        pointHoverRadius: 5,
        pointHoverBackgroundColor: '#4f46e5',
        pointHoverBorderColor: '#fff',
        pointHoverBorderWidth: 2,
        tension: 0.35,
        fill: 'origin',
        yAxisID: 'y',
        order: 1,
      },
      {
        type: 'bar',
        label: '使用数（実績＋調整）',
        data: usage,
        valueLabel: labelCfg.usage,
        backgroundColor: verticalGradient('rgba(16, 185, 129, 0.85)', 'rgba(16, 185, 129, 0.35)', 'rgba(16, 185, 129, 0.55)'),
        borderRadius: 4,
        borderSkipped: false,
        maxBarThickness: 14,
        yAxisID: 'y1',
        order: 2,
      },
      {
        type: 'bar',
        label: '使用計画',
        data: plan,
        valueLabel: labelCfg.plan,
        backgroundColor: verticalGradient('rgba(14, 165, 233, 0.55)', 'rgba(14, 165, 233, 0.18)', 'rgba(14, 165, 233, 0.35)'),
        borderRadius: 4,
        borderSkipped: false,
        maxBarThickness: 14,
        yAxisID: 'y1',
        order: 3,
      },
      {
        type: 'bar',
        label: '注文本数',
        data: order,
        valueLabel: labelCfg.order,
        backgroundColor: verticalGradient('rgba(245, 158, 11, 0.95)', 'rgba(245, 158, 11, 0.45)', 'rgba(245, 158, 11, 0.75)'),
        borderRadius: 4,
        borderSkipped: false,
        maxBarThickness: 14,
        yAxisID: 'y1',
        order: 4,
      },
    ],
  }
})

const formatTick = (v: number | string) => Number(v).toLocaleString('ja-JP')

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  animation: { duration: 700, easing: 'easeOutQuart' },
  interaction: { mode: 'index', intersect: false },
  layout: { padding: { top: 14 } },
  plugins: {
    partChartValueLabels: { display: chartShowValues.value },
    legend: {
      position: 'bottom',
      labels: { usePointStyle: true, pointStyle: 'circle', boxWidth: 8, padding: 14, color: '#475569', font: { size: 11 } },
    },
    tooltip: {
      backgroundColor: 'rgba(15, 23, 42, 0.92)',
      titleColor: '#e2e8f0',
      bodyColor: '#f8fafc',
      titleFont: { size: 12, weight: 'bold' },
      bodyFont: { size: 12 },
      padding: 10,
      cornerRadius: 10,
      boxPadding: 4,
      usePointStyle: true,
      callbacks: {
        label: (ctx: any) => ` ${ctx.dataset.label}: ${formatTick(ctx.parsed.y || 0)}`,
      },
    },
  },
  scales: {
    x: {
      grid: { display: false },
      border: { display: false },
      ticks: { color: '#94a3b8', font: { size: 10 }, maxRotation: 0, autoSkip: true },
    },
    y: {
      position: 'left',
      title: { display: true, text: '在庫', color: '#64748b', font: { size: 11, weight: 'bold' } },
      border: { display: false },
      grid: {
        color: (ctx: any) => (ctx.tick?.value === 0 ? 'rgba(239, 68, 68, 0.65)' : 'rgba(226, 232, 240, 0.7)'),
        lineWidth: (ctx: any) => (ctx.tick?.value === 0 ? 1.5 : 1),
      },
      grace: '10%',
      ticks: { color: '#94a3b8', font: { size: 10 }, callback: formatTick },
    },
    y1: {
      position: 'right',
      beginAtZero: true,
      title: { display: true, text: '数量', color: '#64748b', font: { size: 11, weight: 'bold' } },
      border: { display: false },
      grid: { drawOnChartArea: false },
      grace: '12%',
      ticks: { color: '#94a3b8', font: { size: 10 }, callback: formatTick },
    },
  },
}))

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
        (up?.start_date && up?.end_date ? `\n同期期間: ${up.start_date} ～ ${up.end_date}` : '') +
        (up?.trend_switch_date ? `\n在庫推移の使用計画切替日: ${up.trend_switch_date}` : '')

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

// ─────────────────────────────────────────────
// 注文書発行（対象月 × 仕入先ごと）
// ─────────────────────────────────────────────
/** 対象月（YYYY-MM）→ 月初〜月末 */
const printPeriod = computed(() => {
  const m = (printForm.month || '').match(/^(\d{4})-(\d{2})$/)
  if (!m) return { start: '', end: '' }
  const lastDay = new Date(Number(m[1]), Number(m[2]), 0).getDate()
  return { start: `${m[1]}-${m[2]}-01`, end: `${m[1]}-${m[2]}-${String(lastDay).padStart(2, '0')}` }
})

const printSupplierGroups = computed(() =>
  printSuppliers.value.map((supplier) => ({
    supplier,
    items: printOrders.value.filter((row) => (row.supplier_name || '').trim() === supplier),
  })),
)

/** 納入日 → 部品名の順 */
const printItems = computed(() =>
  [...(printSupplierGroups.value.find((g) => g.supplier === printForm.supplier)?.items ?? [])].sort(
    (a, b) => (a.date || '').localeCompare(b.date || '') || comparePartName(a, b),
  ),
)

/** 数量 = 注文本数 × 入数（束本数） */
const orderSheetQty = (row: Partial<PartOrderItem>) =>
  (Number(row.order_quantity) || 0) * (Number(row.pieces_per_bundle) || 1)
const orderSheetAmount = (row: Partial<PartOrderItem>) => orderSheetQty(row) * (Number(row.unit_price) || 0)

const printTotals = computed(() => ({
  qty: printItems.value.reduce((s, r) => s + (Number(r.order_quantity) || 0), 0),
  amount: printItems.value.reduce((s, r) => s + orderSheetAmount(r), 0),
}))

const printFileName = computed(() => {
  if (!printForm.month || !printForm.supplier) return ''
  const safe = printForm.supplier.replace(/[\\/:*?"<>|]/g, '_').trim().slice(0, 80) || '仕入先'
  return `${printForm.month.replace('-', '')}注文書_${safe}.pdf`
})

const onPrintSupplierChange = () => {
  printForm.recipientCompany = printForm.supplier ? `${printForm.supplier} 御中` : ''
  printForm.recipientPersons = ''
}

const loadPrintOrders = async () => {
  const { start, end } = printPeriod.value
  if (!start || printSuppliers.value.length === 0) return
  printLoading.value = true
  try {
    const res = await getPartStockList({
      start_date: start,
      end_date: end,
      suppliers: printSuppliers.value.join(','),
      order_only: true,
      page: 1,
      pageSize: 10000,
    })
    printOrders.value = ((res?.data?.list ?? []) as any[])
      .filter((item) => excludePartsStatusZero(item))
      .map((item) => mapPartStockRow(item))
      .filter((row) => row.order_quantity > 0)
  } catch (error) {
    console.error('注文データの取得に失敗:', error)
    ElMessage.error('注文データの取得に失敗しました')
    printOrders.value = []
  } finally {
    printLoading.value = false
  }
}

const handlePrintOrder = async () => {
  if (!guardPurchaseOperation(canExport)) return
  const suppliers = (searchForm.supplier ?? []).map((s) => s.trim()).filter(Boolean)
  if (suppliers.length === 0) {
    ElMessage.warning('仕入先を選択してください（注文書は仕入先ごとに発行します）')
    return
  }
  printSuppliers.value = suppliers
  printForm.month = (searchForm.dateRange?.[0] || getTodayJapanStr()).slice(0, 7)
  printForm.supplier = suppliers[0]
  onPrintSupplierChange()
  printOrders.value = []
  printConfirmDialogVisible.value = true
  await loadPrintOrders()
}

const confirmPrint = async () => {
  if (!guardPurchaseOperation(canExport)) return
  const items = printItems.value
  if (items.length === 0) {
    ElMessage.warning('対象の注文がありません')
    return
  }
  const fileName = printFileName.value

  printPdfSaving.value = true
  try {
    const pdfBlob = await generateOrderSheetImagePdfBlob(items)
    const res = await savePartOrderPdf(pdfBlob, fileName)
    if (res?.skipped) {
      ElMessage.info('PDF保存先が未設定のため、印刷のみ行います')
    } else if (res?.success === false) {
      ElMessage.error(res?.message || 'PDFの保存に失敗しました')
    } else {
      ElMessage.success(`共有フォルダに保存しました（${fileName}）`)
    }
  } catch (e: unknown) {
    console.error('部品注文書PDF保存エラー:', e)
    const ax = e as { response?: { data?: { detail?: string } }; message?: string }
    ElMessage.error(ax?.response?.data?.detail || ax?.message || 'PDFの保存に失敗しました')
  } finally {
    printPdfSaving.value = false
  }

  const printWindow = window.open('', '_blank')
  if (printWindow) {
    printWindow.document.write(`
      <html>
      <head>
        <title>注文書</title>
        <meta charset="UTF-8">
        <style>${PART_ORDER_SHEET_STYLES}</style>
      </head>
      <body>${generatePrintHtml(items)}</body>
      </html>
    `)
    printWindow.document.close()
    printWindow.onload = function () {
      printWindow.print()
      setTimeout(function () {
        printWindow.close()
      }, 1000)
    }
  } else {
    ElMessage.error('ポップアップがブロックされました。ブラウザの設定を確認してください')
  }

  printConfirmDialogVisible.value = false
}

/** 部品注文書（月間・部品×日付マトリクス / A4横）の印刷・キャプチャ共通スタイル */
const PART_ORDER_SHEET_STYLES = `
@page { size: A4 landscape; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: #fff; }
body {
  font-family: 'Meiryo', 'Yu Gothic', 'Hiragino Sans', sans-serif;
  color: #0f172a;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
.os-page {
  position: relative;
  width: 297mm;
  height: 210mm;
  padding: 7mm 8mm 6mm;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #fff;
  page-break-after: always;
  break-after: page;
}
.os-page:last-child { page-break-after: auto; break-after: auto; }

.os-head {
  flex-shrink: 0;
  height: 32mm;
  margin-bottom: 2.5mm;
  padding-bottom: 2mm;
  display: grid;
  grid-template-columns: 1fr 78mm 1fr;
  gap: 6mm;
  align-items: start;
  border-bottom: 0.6mm solid #312e81;
  overflow: hidden;
}
.os-to {
  display: inline-block;
  margin-top: 1mm;
  padding: 0 8mm 0.8mm 0;
  font-size: 15pt;
  font-weight: 800;
  border-bottom: 0.3mm solid #0f172a;
}
.os-to-sub { margin-top: 1mm; font-size: 9pt; }
.os-lead { margin-top: 2.5mm; font-size: 9pt; }
.os-meta { margin-top: 1.5mm; display: flex; flex-direction: column; gap: 1mm; font-size: 9pt; }
.os-meta b {
  display: inline-block;
  min-width: 16mm;
  margin-right: 2mm;
  padding: 0.3mm 1.5mm;
  font-size: 7.5pt;
  color: #fff;
  text-align: center;
  background: #4338ca;
  border-radius: 1mm;
}
.os-head__center { text-align: center; }
.os-title {
  padding-left: 6mm;
  font-size: 22pt;
  font-weight: 800;
  letter-spacing: 6mm;
  color: #1e1b4b;
}
.os-month { margin-top: 0.5mm; font-size: 10pt; font-weight: 700; color: #4338ca; }
.os-total {
  margin-top: 2.5mm;
  display: flex;
  border: 0.4mm solid #312e81;
  border-radius: 1.5mm;
  overflow: hidden;
}
.os-total span {
  display: flex;
  align-items: center;
  padding: 1.5mm 2.5mm;
  font-size: 8pt;
  color: #fff;
  white-space: nowrap;
  background: #312e81;
}
.os-total strong {
  flex: 1;
  padding: 0.8mm 3mm;
  font-size: 14pt;
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.os-head__right { display: flex; flex-direction: column; align-items: flex-end; gap: 1.5mm; }
.os-no { font-size: 8pt; line-height: 1.5; text-align: right; color: #334155; }
.os-from { display: flex; align-items: flex-start; gap: 2.5mm; }
.os-from__text { font-size: 7.5pt; line-height: 1.5; text-align: right; }
.os-from__text b { font-size: 9pt; }
.os-stamp { border-collapse: collapse; }
.os-stamp th, .os-stamp td { width: 13mm; border: 0.3mm solid #334155; text-align: center; }
.os-stamp th { height: 4mm; font-size: 7pt; font-weight: 700; background: #eef2ff; }
.os-stamp td { height: 11mm; font-size: 9pt; font-weight: 700; }

.os-grid { flex-shrink: 0; width: 100%; border-collapse: collapse; table-layout: fixed; }
.os-grid th, .os-grid td {
  padding: 0 0.6mm;
  font-size: 7pt;
  line-height: 1.15;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  vertical-align: middle;
  border: 0.2mm solid #94a3b8;
}
.os-grid thead th {
  height: 4.5mm;
  font-size: 6.8pt;
  font-weight: 700;
  text-align: center;
  color: #1e1b4b;
  background: #e0e7ff;
}
.os-grid thead th small { margin-left: 0.4mm; font-size: 5.8pt; font-weight: 400; }
.os-grid thead th.is-sat { color: #1d4ed8; background: #dbeafe; }
.os-grid thead th.is-sun { color: #be123c; background: #ffe4e6; }
.os-grid tbody td { height: 6.6mm; }
.os-grid.is-multi-tier tbody td { height: 5.2mm; }
.os-grid tr.is-alt td { background: #f8fafc; }
.os-grid td.q {
  padding: 0;
  font-size: 6.8pt;
  font-weight: 700;
  text-align: center;
  text-overflow: clip;
  font-variant-numeric: tabular-nums;
}
.os-grid:not(.is-multi-tier) td.q.d3 { font-size: 5.6pt; letter-spacing: -0.1mm; }
.os-grid td.q.is-sat { background: #eff6ff; }
.os-grid td.q.is-sun { background: #fff1f2; }
.os-grid .is-void { background: #f1f5f9 !important; }
.os-grid td.c { text-align: center; }
.os-grid td.name { font-size: 8pt; font-weight: 700; }
.os-grid td.spec { color: #334155; }
.os-grid thead th .hsub {
  display: block;
  margin-top: 0.3mm;
  font-size: 5.8pt;
  font-weight: 600;
  color: #6366f1;
}
.os-grid td.stack { line-height: 1.05; }
.os-grid td.stack .l1, .os-grid td.stack .l2 {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.os-grid td.stack .l2 { margin-top: 0.2mm; font-size: 5.6pt; color: #6366f1; }
.os-grid td.st { padding: 0 0.3mm; text-overflow: clip; }
.os-grid td.st span {
  display: inline-block;
  padding: 0.2mm 0.8mm;
  font-size: 5.8pt;
  font-weight: 700;
  line-height: 1.2;
  border-radius: 0.8mm;
}
.os-grid .st-paid { color: #4338ca; background: #eef2ff; }
.os-grid .st-free { color: #047857; background: #ecfdf5; }
.os-grid .st-self { color: #b45309; background: #fffbeb; }
.os-grid .st-other { color: #475569; background: #f1f5f9; }
.os-grid .ppb { margin-left: 1mm; font-size: 6pt; color: #4f46e5; }
.os-grid td.num { text-align: right; font-variant-numeric: tabular-nums; }
.os-grid td.sum {
  font-weight: 800;
  text-align: right;
  background: #eef2ff;
  font-variant-numeric: tabular-nums;
}
.os-grid td.amt { font-weight: 700; }
.os-grid.is-compact td.q { font-size: 6pt; letter-spacing: -0.08mm; }
.os-grid tr.tier-top td.q, .os-grid tr.tier-mid td.q { border-bottom: 0.2mm dashed #cbd5e1; }
.os-grid tr.tier-mid td.q, .os-grid tr.tier-bottom td.q { border-top: 0.2mm dashed #cbd5e1; }
.os-grid tr.tier-bottom td { border-bottom-color: #64748b; }

.os-spacer { flex: 1; min-height: 1mm; }
.os-foot { flex-shrink: 0; height: 14mm; margin-top: 2mm; display: flex; align-items: stretch; gap: 5mm; }
.os-notes {
  flex: 1;
  padding: 1.5mm 3mm;
  font-size: 7pt;
  line-height: 1.5;
  color: #334155;
  background: #f8fafc;
  border-left: 0.8mm solid #6366f1;
  border-radius: 1mm;
  overflow: hidden;
}
.os-notes p { margin: 0; }
.os-summary { display: flex; border: 0.3mm solid #312e81; border-radius: 1.5mm; overflow: hidden; }
.os-summary div {
  min-width: 24mm;
  padding: 1mm 4mm;
  display: flex;
  flex-direction: column;
  justify-content: center;
  text-align: right;
  border-left: 0.2mm solid #c7d2fe;
}
.os-summary div:first-child { border-left: 0; }
.os-summary span { font-size: 6.5pt; color: #475569; }
.os-summary b { font-size: 11pt; font-variant-numeric: tabular-nums; }
.os-summary .is-total { color: #fff; background: #312e81; }
.os-summary .is-total span { color: #c7d2fe; }
.os-pagefoot {
  flex-shrink: 0;
  height: 4mm;
  margin-top: 1.2mm;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  font-size: 6.5pt;
  color: #64748b;
}
`

interface OrderSheetMatrixRow {
  part_cd: string
  part_name: string
  standard_spec: string
  part_material: string
  capacity_qty: number
  settlement_type: string
  pieces_per_bundle: number
  unit_price: number
  /** 日（1〜31）→ 注文数 */
  daily: Record<number, number>
  total: number
  amount: number
}

/** 部品（＋単価）単位に集約し、日別の注文数を持たせる */
const buildOrderSheetMatrix = (items: PartOrderItem[]): OrderSheetMatrixRow[] => {
  const map = new Map<string, OrderSheetMatrixRow>()
  for (const r of items) {
    const unitPrice = Number(r.unit_price) || 0
    const key = `${r.part_cd}__${unitPrice}`
    let row = map.get(key)
    if (!row) {
      row = {
        part_cd: r.part_cd,
        part_name: r.part_name,
        standard_spec: r.standard_spec || '',
        part_material: (r.part_material || '').trim(),
        capacity_qty: Number(r.capacity_qty) || 0,
        settlement_type: (r.settlement_type || '').trim(),
        pieces_per_bundle: Number(r.pieces_per_bundle) || 1,
        unit_price: unitPrice,
        daily: {},
        total: 0,
        amount: 0,
      }
      map.set(key, row)
    }
    const day = Number((r.date || '').slice(8, 10))
    const qty = Number(r.order_quantity) || 0
    if (day) row.daily[day] = (row.daily[day] || 0) + qty
    row.total += qty
    row.amount += orderSheetAmount(r)
  }
  return [...map.values()].sort(comparePartName)
}

/** 最終ページに last 行以下が残るまで normal 行ずつ詰める（最終ページは必ず1行以上） */
function paginateRows<T>(list: T[], normal: number, last: number): T[][] {
  const pages: T[][] = []
  let rest = list
  while (rest.length > last) {
    const take = Math.min(normal, rest.length - 1)
    pages.push(rest.slice(0, take))
    rest = rest.slice(take)
  }
  pages.push(rest)
  return pages
}

const OS_WEEKDAYS = ['日', '月', '火', '水', '木', '金', '土']
/** 部品マスタの決済種類 → 区分表示の色 */
const OS_SETTLEMENT_CLASS: Record<string, string> = {
  有償支給: 'st-paid',
  無償支給: 'st-free',
  自給: 'st-self',
}

/** A4横の寸法（mm）。行高を CSS と合わせて固定し、ページあたりの行数を算出する */
const OS_LAYOUT = {
  /** 表見出し上端（41.6mm）〜ページフッター（198.8mm）− 余裕 1.7mm */
  tableH: 155.5,
  /** 見出し1行の高さ（1段表示は日付＋曜日の2行） */
  headRowH: 4.5,
  /** 1段表示の行高 / 複数段表示の1段あたりの行高 */
  rowH: 6.6,
  tierRowH: 5.2,
  /** 最終ページの備考・合計欄 */
  footH: 16,
}

/**
 * 1日あたりの列幅に収まる桁数から段数を決める
 * - 1段（31列・約4.6mm）：3桁まで
 * - 2段（1〜15日／16日〜末日、約9mm）：それ以上
 *   5桁以上は文字を詰めた「コンパクト表示」にする
 */
const OS_SINGLE_TIER_MAX = 999
const OS_COMPACT_MAX = 9999
/** 段ごとの区切り日（この日までを1段目…） */
const OS_TIER_SPLITS: Record<number, number[]> = { 1: [], 2: [15] }

const buildOrderSheetLayout = (items: PartOrderItem[], month: string) => {
  const rows = buildOrderSheetMatrix(items)
  const [y, m] = month.split('-').map(Number)
  const daysInMonth = y && m ? new Date(y, m, 0).getDate() : 31
  const days = Array.from({ length: daysInMonth }, (_, i) => i + 1)
  const maxCell = Math.max(0, ...rows.flatMap((r) => Object.values(r.daily)))
  const tierCount = maxCell <= OS_SINGLE_TIER_MAX ? 1 : 2
  const compact = maxCell > OS_COMPACT_MAX

  const rowH = tierCount === 1 ? OS_LAYOUT.rowH : OS_LAYOUT.tierRowH * tierCount
  const headH = OS_LAYOUT.headRowH * Math.max(2, tierCount)
  const bodyH = OS_LAYOUT.tableH - headH
  const normal = Math.max(1, Math.floor(bodyH / rowH))
  const last = Math.max(1, Math.floor((bodyH - OS_LAYOUT.footH) / rowH))
  return {
    y,
    m,
    days,
    rows,
    tierCount,
    compact,
    pages: paginateRows(rows, normal, last),
  }
}

const printSheetInfo = computed(() => {
  if (!printItems.value.length || !printForm.month) return null
  const layout = buildOrderSheetLayout(printItems.value, printForm.month)
  return { parts: layout.rows.length, pages: layout.pages.length, tierCount: layout.tierCount }
})

const escapeHtml = (value: unknown) =>
  String(value ?? '').replace(
    /[&<>"']/g,
    (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c] as string,
  )

const generatePrintHtml = (items: PartOrderItem[]) => {
  const { y, m, days, rows, tierCount, compact, pages } = buildOrderSheetLayout(
    items,
    printForm.month,
  )
  const multiTier = tierCount > 1
  const num = (n: number) => n.toLocaleString('ja-JP')
  const yen = (n: number, digits = 0) =>
    `¥${n.toLocaleString('ja-JP', { maximumFractionDigits: digits })}`
  const dow = (d: number) => new Date(y, m - 1, d).getDay()
  const dayCls = (d?: number) => {
    if (!d) return 'is-void'
    const w = dow(d)
    return w === 0 ? 'is-sun' : w === 6 ? 'is-sat' : ''
  }

  // 段ごとに日付を分け、2段表示は31日月に合わせて16列に揃え、空きセルで埋める
  const bounds = [0, ...OS_TIER_SPLITS[tierCount], days.length]
  const rawTiers = bounds.slice(1).map((b, i) => days.slice(bounds[i], b))
  const tierCols = multiTier ? 16 : days.length
  const tiers: (number | undefined)[][] = rawTiers.map((t) => [
    ...t,
    ...Array<undefined>(Math.max(0, tierCols - t.length)).fill(undefined),
  ])
  // No・部品名・規格／材料・収容数・区分。コンパクト表示は日付列を広げるため部品名・規格を詰める
  const fixedW = compact ? [6, 36, 18, 9, 11] : [6, 38, 24, 9, 11]
  const tailW = [15, 15, 21]
  const dayW = (281 - [...fixedW, ...tailW].reduce((s, w) => s + w, 0)) / tiers[0].length
  const colgroup = `<colgroup>${[...fixedW, ...tiers[0].map(() => dayW), ...tailW]
    .map((w) => `<col style="width:${w.toFixed(2)}mm">`)
    .join('')}</colgroup>`

  const totalQty = rows.reduce((s, r) => s + r.total, 0)
  const totalAmount = Math.round(rows.reduce((s, r) => s + r.amount, 0))

  const headCells = (tier: (number | undefined)[], withDow: boolean) =>
    tier
      .map((d) =>
        d
          ? `<th class="${dayCls(d)}">${d}${withDow ? `<small>${OS_WEEKDAYS[dow(d)]}</small>` : ''}</th>`
          : '<th class="is-void"></th>',
      )
      .join('')
  const qtyCells = (tier: (number | undefined)[], get: (d: number) => number | undefined) =>
    tier
      .map((d) => {
        const q = d ? get(d) : undefined
        return `<td class="q ${dayCls(d)}${q && q >= 100 ? ' d3' : ''}">${q ? num(q) : ''}</td>`
      })
      .join('')

  const headSpan = ` rowspan="${Math.max(2, tierCount)}"`
  const headLead = ['No', '部品名', '規格<span class="hsub">材料</span>', '収容数', '区分']
    .map((t) => `<th${headSpan}>${t}</th>`)
    .join('')
  const headTail = ['月計', '単価', '金額'].map((t) => `<th${headSpan}>${t}</th>`).join('')
  const thead = multiTier
    ? tiers
        .map((t, i) => `<tr>${i === 0 ? headLead : ''}${headCells(t, true)}${i === 0 ? headTail : ''}</tr>`)
        .join('')
    : `<tr>${headLead}${headCells(days, false)}${headTail}</tr><tr>${days
        .map((d) => `<th class="${dayCls(d)}">${OS_WEEKDAYS[dow(d)]}</th>`)
        .join('')}</tr>`

  /** 複数段表示：1段目に固定列（rowspan）、各段に日別セル */
  const tierRows = (
    cls: string,
    lead: string,
    tail: string,
    get: (d: number) => number | undefined,
  ) =>
    tiers
      .map((t, i) => {
        const pos = i === 0 ? 'tier-top' : i === tiers.length - 1 ? 'tier-bottom' : 'tier-mid'
        return `<tr class="${pos}${cls}">${i === 0 ? lead : ''}${qtyCells(t, get)}${i === 0 ? tail : ''}</tr>`
      })
      .join('')

  const span = multiTier ? ` rowspan="${tierCount}"` : ''
  const bodyRow = (r: OrderSheetMatrixRow, no: number) => {
    const alt = no % 2 === 0 ? ' is-alt' : ''
    const ppb = r.pieces_per_bundle !== 1 ? `<span class="ppb">入数${num(r.pieces_per_bundle)}</span>` : ''
    /** 上段：規格、下段：部品マスタの部品材料 */
    const stack = (main: string, sub: string) =>
      `<div class="l1">${main}</div>${sub ? `<div class="l2">${sub}</div>` : ''}`
    const stCls = OS_SETTLEMENT_CLASS[r.settlement_type] || 'st-other'
    const lead =
      `<td${span} class="c">${no}</td>` +
      `<td${span} class="name">${escapeHtml(r.part_name)}</td>` +
      `<td${span} class="spec stack">${stack(escapeHtml(r.standard_spec) + ppb, escapeHtml(r.part_material))}</td>` +
      `<td${span} class="num">${r.capacity_qty ? num(r.capacity_qty) : ''}</td>` +
      `<td${span} class="c st">${r.settlement_type ? `<span class="${stCls}">${escapeHtml(r.settlement_type)}</span>` : ''}</td>`
    const tail =
      `<td${span} class="sum">${num(r.total)}</td>` +
      `<td${span} class="num">${yen(r.unit_price, 2)}</td>` +
      `<td${span} class="num amt">${yen(Math.round(r.amount))}</td>`
    const get = (d: number) => r.daily[d]
    return multiTier
      ? tierRows(alt, lead, tail, get)
      : `<tr class="${alt}">${lead}${qtyCells(days, get)}${tail}</tr>`
  }
  const today = getTodayJapanStr().replace(/-/g, '/')
  const supplierCd = items.find((r) => r.supplier_cd)?.supplier_cd || ''
  const orderNo = `${printForm.month.replace('-', '')}${supplierCd ? `-${supplierCd}` : ''}`
  const { start, end } = printPeriod.value

  const headHtml = `
    <header class="os-head">
      <div>
        <div class="os-to">${escapeHtml(printForm.recipientCompany)}</div>
        ${printForm.recipientPersons ? `<div class="os-to-sub">${escapeHtml(printForm.recipientPersons)}</div>` : ''}
        <div class="os-lead">下記の通り注文いたします。</div>
        <div class="os-meta">
          <span><b>納入期間</b>${escapeHtml(start.replace(/-/g, '/'))} ～ ${escapeHtml(end.replace(/-/g, '/'))}</span>
          ${printForm.deliveryPlace ? `<span><b>納入場所</b>${escapeHtml(printForm.deliveryPlace)}</span>` : ''}
        </div>
      </div>
      <div class="os-head__center">
        <div class="os-title">注文書</div>
        <div class="os-month">${y}年${m}月分</div>
        <div class="os-total"><span>ご注文金額（税抜）</span><strong>${yen(totalAmount)}</strong></div>
      </div>
      <div class="os-head__right">
        <div class="os-no">注文番号　${escapeHtml(orderNo)}<br>発行日　${today}</div>
        <div class="os-from">
          <div class="os-from__text">
            <b>日鉄物産荒井オートモーティブ(株)</b>
            <div>〒496-0902 愛知県愛西市須依町2189</div>
            <div>TEL (0567) 28-4171 ／ FAX (0567) 26-2281</div>
          </div>
          <table class="os-stamp">
            <tr><th>承認</th><th>発行</th></tr>
            <tr><td>${escapeHtml(printForm.approver)}</td><td>${escapeHtml(printForm.issuer)}</td></tr>
          </table>
        </div>
      </div>
    </header>`

  const footHtml = `
    <div class="os-foot">
      <div class="os-notes">
        <p>${escapeHtml(printForm.note1)}</p>
        <p>${escapeHtml(printForm.note2)}</p>
      </div>
      <div class="os-summary">
        <div><span>品目数</span><b>${num(rows.length)}</b></div>
        <div><span>注文数計</span><b>${num(totalQty)}</b></div>
        <div class="is-total"><span>合計金額（税抜）</span><b>${yen(totalAmount)}</b></div>
      </div>
    </div>`

  let no = 0
  return pages
    .map((pageRows, pi) => {
      const isLast = pi === pages.length - 1
      const body = pageRows.map((r) => bodyRow(r, ++no)).join('')
      return `
    <section class="os-page">
      ${headHtml}
      <table class="os-grid${multiTier ? ' is-multi-tier' : ''}${compact ? ' is-compact' : ''}">${colgroup}<thead>${thead}</thead><tbody>${body}</tbody></table>
      <div class="os-spacer"></div>
      ${isLast ? footHtml : ''}
      <div class="os-pagefoot">
        <span>※ 表中の数値は各納入日の注文数。土曜は青、日曜は赤で表示</span>
        <span>${escapeHtml(printForm.supplier)} ／ ${pi + 1} / ${pages.length}</span>
      </div>
    </section>`
    })
    .join('')
}

/** html2canvas + jsPDF で画像ベースの PDF を生成（.os-page ごとに A4横1ページ） */
const generateOrderSheetImagePdfBlob = async (orderItems: PartOrderItem[]): Promise<Blob> => {
  const iframe = document.createElement('iframe')
  iframe.setAttribute('title', 'order-sheet-capture')
  iframe.style.cssText =
    'position:fixed;left:-12000px;top:0;width:297mm;border:0;opacity:0;pointer-events:none'
  document.body.appendChild(iframe)
  try {
    const doc = iframe.contentDocument
    if (!doc) throw new Error('iframe document')
    doc.open()
    doc.write(
      `<!DOCTYPE html><html><head><meta charset="UTF-8"><style>${PART_ORDER_SHEET_STYLES}</style></head><body>${generatePrintHtml(orderItems)}</body></html>`,
    )
    doc.close()
    await new Promise((r) => requestAnimationFrame(() => setTimeout(r, 280)))

    const pages = Array.from(doc.querySelectorAll<HTMLElement>('.os-page'))
    if (pages.length === 0) throw new Error('.os-page not found')
    const pdf = new jsPDF({ orientation: 'l', unit: 'mm', format: 'a4', compress: true })
    const pageWidth = pdf.internal.pageSize.getWidth()
    const pageHeight = pdf.internal.pageSize.getHeight()
    for (let i = 0; i < pages.length; i++) {
      const canvas = await html2canvas(pages[i], {
        scale: 2,
        useCORS: true,
        logging: false,
        backgroundColor: '#ffffff',
      })
      if (i > 0) pdf.addPage('a4', 'l')
      pdf.addImage(canvas.toDataURL('image/jpeg', 0.92), 'JPEG', 0, 0, pageWidth, pageHeight, undefined, 'FAST')
    }
    return pdf.output('blob')
  } finally {
    iframe.remove()
  }
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
  .search-group.date-group {
    min-width: 300px;
  }
}

/* Laptop: <= 1024px */
@media (max-width: 1024px) {
  .part-order-container {
    padding: 8px 10px;
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

/* 使用数調整：文字色とフォーカス色のみエメラルド */
:deep(.usage-quantity-input .el-input__inner) {
  color: #047857 !important;
}

:deep(.el-table .usage-quantity-input .el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #6ee7b7 inset;
}

:deep(.el-table .usage-quantity-input .el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #10b981 inset, 0 0 0 3px rgba(16, 185, 129, 0.15);
}

/* 使用数調整がマイナス（戻し・返却）のときは赤字 */
:deep(.el-table .usage-quantity-input.is-negative .el-input__wrapper) {
  box-shadow: 0 0 0 1px #fca5a5 inset;
}

:deep(.el-table .usage-quantity-input.is-negative .el-input__inner) {
  color: #dc2626 !important;
  font-weight: 700;
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

/* ============================================================
 * 页面美化：現代UI・3D動効・色分け（部品在庫管理 / indigo→violet・タブ連動カラー）
 * ============================================================ */
.po-modern {
  --po-tab: #4f46e5;
  --po-tab-2: #818cf8;
  --po-tab-edge: #3730a3;
}
.po-modern.po-tab-initial {
  --po-tab: #0284c7;
  --po-tab-2: #38bdf8;
  --po-tab-edge: #075985;
}
.po-modern.po-tab-usage {
  --po-tab: #059669;
  --po-tab-2: #34d399;
  --po-tab-edge: #065f46;
}
.po-modern.po-tab-order {
  --po-tab: #d97706;
  --po-tab-2: #fbbf24;
  --po-tab-edge: #92400e;
}
.po-modern.po-tab-orderHistory {
  --po-tab: #7c3aed;
  --po-tab-2: #a78bfa;
  --po-tab-edge: #5b21b6;
}

/* ---------- ヒーローヘッダー ---------- */
.po-modern .page-header {
  padding: 12px 18px;
  border-radius: 16px;
  background: linear-gradient(135deg, #3730a3 0%, #4f46e5 32%, #7c3aed 70%, #a855f7 100%);
  box-shadow:
    0 18px 36px -18px rgba(76, 29, 149, 0.65),
    0 4px 12px -6px rgba(79, 70, 229, 0.4),
    0 0 0 1px rgba(255, 255, 255, 0.18) inset;
}
.po-modern .page-header:hover {
  transform: none;
}
.po-modern .page-header-fx {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}
.po-modern .title-icon {
  width: 42px;
  height: 42px;
  border-radius: 13px;
  font-size: 21px;
  box-shadow:
    0 10px 20px -8px rgba(30, 27, 75, 0.6),
    0 2px 0 rgba(255, 255, 255, 0.35) inset,
    0 -3px 0 rgba(67, 56, 202, 0.4) inset;
  animation: poIconFloat 5.5s ease-in-out infinite;
}
.po-modern .page-header:hover .title-icon {
  transform: none;
}
.po-modern .main-title {
  font-size: 20px;
  font-weight: 800;
  text-shadow: 0 2px 6px rgba(30, 27, 75, 0.3);
}
.po-modern .header-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 6px;
}
.po-modern .header-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 22px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 650;
  color: #fff;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 6px 14px -8px rgba(30, 27, 75, 0.55);
  -webkit-backdrop-filter: blur(6px);
  backdrop-filter: blur(6px);
}

/* ---------- ヘッダー操作：3Dキーキャップ ---------- */
.po-modern .action-btn {
  --btn-edge: rgba(30, 27, 75, 0.45);
  height: 34px;
  border-radius: 10px;
  box-shadow:
    0 3px 0 var(--btn-edge),
    0 10px 18px -8px var(--btn-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease,
    background 0.2s ease;
}
.po-modern .action-btn.success-btn {
  --btn-edge: #047857;
  border-color: rgba(255, 255, 255, 0.35);
}
.po-modern .action-btn.warning-btn {
  --btn-edge: #b45309;
  border-color: rgba(255, 255, 255, 0.35);
}
.po-modern .action-btn:hover,
.po-modern .action-btn:focus-visible {
  transform: translateY(-2px);
  box-shadow:
    0 5px 0 var(--btn-edge),
    0 14px 22px -8px var(--btn-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
}
.po-modern .action-btn:active {
  transform: translateY(2px);
  box-shadow:
    0 1px 0 var(--btn-edge),
    0 4px 8px -4px var(--btn-glow);
}

/* ---------- 検索バー ---------- */
.po-modern .search-container {
  position: relative;
  overflow: hidden;
  border-radius: 14px;
}
.po-modern .search-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 14px;
  right: 14px;
  height: 3px;
  border-radius: 0 0 3px 3px;
  background: linear-gradient(90deg, #6366f1 0%, #0ea5e9 50%, #8b5cf6 100%);
  pointer-events: none;
}
.po-modern .filter-label .el-icon {
  box-shadow:
    0 2px 0 color-mix(in srgb, var(--label-color) 35%, #ffffff),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
  transition: transform 0.2s ease;
}
.po-modern .filter-item:hover .filter-label .el-icon {
  transform: translateY(-1px) rotate(-6deg);
}
.po-modern .date-nav-btn {
  box-shadow: 0 2px 0 #e2e8f0;
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease,
    color 0.15s ease,
    background 0.15s ease;
}
.po-modern .date-nav-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 3px 0 #c7d2fe;
}
.po-modern .date-nav-btn:active {
  transform: translateY(1px);
  box-shadow: 0 1px 0 #c7d2fe;
}
.po-modern .date-nav-btn.today-btn {
  box-shadow:
    0 2px 0 #3730a3,
    0 6px 12px -6px rgba(99, 102, 241, 0.6),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
}
.po-modern .date-nav-btn.today-btn:hover {
  box-shadow:
    0 3px 0 #3730a3,
    0 10px 16px -6px rgba(99, 102, 241, 0.6),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
}
.po-modern .date-nav-btn.today-btn:active {
  box-shadow:
    0 1px 0 #3730a3,
    0 3px 6px -3px rgba(99, 102, 241, 0.5);
}

/* ---------- テーブルエリア：タブ連動アクセント ---------- */
.po-modern .table-section {
  position: relative;
  border-radius: 16px;
  box-shadow:
    0 18px 36px -26px color-mix(in srgb, var(--po-tab) 70%, transparent),
    0 2px 6px rgba(15, 23, 42, 0.05),
    0 0 0 1px color-mix(in srgb, var(--po-tab) 14%, transparent);
  transition: box-shadow 0.3s ease;
}
.po-modern .table-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  z-index: 3;
  background: linear-gradient(90deg, var(--po-tab-2) 0%, var(--po-tab) 60%, var(--po-tab-edge) 100%);
  pointer-events: none;
  transition: background 0.3s ease;
}
.po-modern .table-header {
  background: linear-gradient(
    180deg,
    #ffffff 0%,
    color-mix(in srgb, var(--po-tab) 5%, #f8fafc) 100%
  );
  border-bottom-color: color-mix(in srgb, var(--po-tab) 16%, #e6e9f4);
}

/* タブ：3Dキーキャップ */
.po-modern .table-tabs {
  gap: 6px;
  padding: 4px 4px 6px;
}
.po-modern .tab-item {
  --tab-edge: #3730a3;
  transition:
    transform 0.18s ease,
    background 0.2s ease,
    color 0.2s ease,
    box-shadow 0.18s ease;
}
.po-modern .tab-item--initial {
  --tab-edge: #075985;
}
.po-modern .tab-item--usage {
  --tab-edge: #065f46;
}
.po-modern .tab-item--order {
  --tab-edge: #92400e;
}
.po-modern .tab-item--history {
  --tab-edge: #5b21b6;
}
.po-modern .tab-item:not(.active):hover {
  transform: translateY(-2px);
  box-shadow:
    0 3px 0 #e2e8f0,
    0 8px 14px -8px var(--tab-glow);
}
.po-modern .tab-item.active {
  transform: translateY(-2px);
  box-shadow:
    0 3px 0 var(--tab-edge),
    0 10px 18px -8px var(--tab-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
}
.po-modern .tab-item.active .el-icon {
  animation: poTabIcon 0.5s ease-out;
}
.po-modern .tab-item:active {
  transform: translateY(1px);
}

/* キー操作ヒント：立体キー */
.po-modern .table-hint kbd {
  border-bottom-width: 1px;
  box-shadow:
    0 2px 0 #cbd5e1,
    inset 0 1px 0 #ffffff;
  background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%);
}

/* テーブル操作ボタン：キーキャップ */
.po-modern .table-actions .print-btn,
.po-modern .table-actions .month-start-btn,
.po-modern .table-actions .reorder-btn {
  --k-edge: #3730a3;
  --k-glow: rgba(99, 102, 241, 0.5);
  box-shadow:
    0 3px 0 var(--k-edge),
    0 10px 18px -8px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease,
    background 0.2s ease;
}
.po-modern .table-actions .reorder-btn {
  --k-edge: #fcd34d;
  --k-glow: rgba(245, 158, 11, 0.45);
  box-shadow:
    0 0 0 1px #fcd34d inset,
    0 3px 0 var(--k-edge),
    0 10px 18px -8px var(--k-glow);
}
.po-modern .table-actions .print-btn:hover,
.po-modern .table-actions .month-start-btn:hover {
  transform: translateY(-2px);
  box-shadow:
    0 5px 0 var(--k-edge),
    0 14px 22px -8px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
}
.po-modern .table-actions .reorder-btn:hover {
  transform: translateY(-2px);
  box-shadow:
    0 0 0 1px #f59e0b inset,
    0 5px 0 #f59e0b,
    0 14px 22px -8px var(--k-glow);
}
.po-modern .table-actions .print-btn:active,
.po-modern .table-actions .month-start-btn:active,
.po-modern .table-actions .reorder-btn:active {
  transform: translateY(2px);
  box-shadow:
    0 1px 0 var(--k-edge),
    0 4px 8px -4px var(--k-glow);
}

/* 表ヘッダー：タブ色の淡いグラデーション（列別文字色は維持） */
.po-modern :deep(.el-table th.el-table__cell) {
  background: linear-gradient(
    180deg,
    #ffffff 0%,
    color-mix(in srgb, var(--po-tab) 7%, #f8fafc) 100%
  );
  border-bottom: 2px solid color-mix(in srgb, var(--po-tab) 30%, #e5e7eb);
}
.po-modern .table-section :deep(.el-table .el-table__body tr:hover > td.el-table__cell:first-child) {
  box-shadow: inset 3px 0 0 var(--po-tab);
}
.po-modern .modern-table :deep(.el-table__body-wrapper::-webkit-scrollbar-thumb) {
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--po-tab-2) 70%, #ffffff) 0%,
    color-mix(in srgb, var(--po-tab) 70%, #ffffff) 100%
  );
  border-color: #f1f5f9;
}
.po-modern .modern-table :deep(.el-table__body-wrapper::-webkit-scrollbar-thumb:hover) {
  background: linear-gradient(180deg, var(--po-tab-2) 0%, var(--po-tab) 100%);
}
.po-modern .modern-table :deep(.el-loading-spinner .path) {
  stroke: var(--po-tab);
}

/* ページネーション：キーキャップ */
.po-modern .pagination-wrapper {
  background: linear-gradient(
    180deg,
    #ffffff 0%,
    color-mix(in srgb, var(--po-tab) 5%, #f8fafc) 100%
  );
}
.po-modern .modern-pagination :deep(.el-pager li),
.po-modern .modern-pagination :deep(.btn-prev),
.po-modern .modern-pagination :deep(.btn-next) {
  box-shadow: 0 2px 0 #e2e8f0;
}
.po-modern .modern-pagination :deep(.el-pager li.is-active) {
  background: linear-gradient(135deg, var(--po-tab-2) 0%, var(--po-tab) 100%);
  box-shadow:
    0 2px 0 var(--po-tab-edge),
    0 6px 12px -6px var(--po-tab);
  transform: translateY(-1px);
}

/* ---------- キーフレーム ---------- */
@keyframes poIconFloat {
  0%,
  100% {
    transform: perspective(300px) rotateX(0deg) rotateY(0deg) translateY(0);
  }
  50% {
    transform: perspective(300px) rotateX(10deg) rotateY(-14deg) translateY(-2px);
  }
}
@keyframes poTabIcon {
  0% {
    transform: perspective(200px) rotateY(0deg) scale(1);
  }
  60% {
    transform: perspective(200px) rotateY(200deg) scale(1.15);
  }
  100% {
    transform: perspective(200px) rotateY(360deg) scale(1);
  }
}

@media (prefers-reduced-motion: reduce) {
  .po-modern .title-icon,
  .po-modern .tab-item.active .el-icon {
    animation: none;
  }
  .po-modern .tab-item,
  .po-modern .action-btn {
    transition: none;
  }
}


</style>

<!-- 部品在庫推移ドロワー：el-drawer 内部要素には scoped 属性が付かないため別ブロック -->
<style>
@keyframes pcdRise {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes pcdShine {
  0% { transform: translateX(-140%) skewX(-18deg); }
  55%, 100% { transform: translateX(360%) skewX(-18deg); }
}

@keyframes pcdPulse {
  0%, 100% { box-shadow: 0 0 0 0 currentColor; }
  50% { box-shadow: 0 0 0 5px transparent; }
}

.part-chart-drawer.el-drawer {
  overflow: hidden;
  border-radius: 18px 0 0 18px;
  background:
    radial-gradient(900px 300px at 100% 0%, rgba(139, 92, 246, 0.08), transparent 60%),
    linear-gradient(180deg, #f6f7fd 0%, #eef1f8 100%);
  box-shadow:
    -24px 0 60px -12px rgba(30, 27, 75, 0.35),
    -1px 0 0 rgba(255, 255, 255, 0.6) inset;
}

.part-chart-drawer .el-drawer__header {
  margin: 0;
  padding: 0;
}

.part-chart-drawer .el-drawer__body {
  padding: 16px 20px 20px;
}

/* ヘッダー */
.pcd-head {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 20px 16px;
  color: #fff;
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 58%, #8b5cf6 100%);
  box-shadow: 0 10px 26px -10px rgba(79, 70, 229, 0.55);
}

.pcd-head::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 92% -40%, rgba(255, 255, 255, 0.3) 0, transparent 40%),
    radial-gradient(circle at 70% 150%, rgba(255, 255, 255, 0.16) 0, transparent 36%),
    radial-gradient(circle at 4% 130%, rgba(56, 189, 248, 0.32) 0, transparent 32%);
  pointer-events: none;
}

.pcd-head::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 28%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.16), transparent);
  animation: pcdShine 6s ease-in-out infinite;
  pointer-events: none;
}

.pcd-head__main,
.pcd-head__side {
  position: relative;
  z-index: 1;
}

.pcd-head__main {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  min-width: 0;
}

.pcd-head__icon {
  flex-shrink: 0;
  width: 46px;
  height: 46px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  border-radius: 14px;
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.38), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.38);
  backdrop-filter: blur(10px);
  box-shadow:
    0 8px 18px rgba(30, 27, 75, 0.28),
    inset 0 1px 0 rgba(255, 255, 255, 0.5);
  transition: transform 0.3s ease;
}

.pcd-head:hover .pcd-head__icon {
  transform: rotate(-6deg) scale(1.06);
}

.pcd-head__text {
  min-width: 0;
}

.pcd-head__eyebrow {
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.14em;
  color: rgba(255, 255, 255, 0.72);
}

.pcd-head__title {
  margin: 2px 0 8px;
  font-size: 19px;
  font-weight: 800;
  line-height: 1.25;
  letter-spacing: 0.02em;
  color: #fff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pcd-head__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.pcd-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 22px;
  padding: 0 9px;
  font-size: 11.5px;
  font-weight: 600;
  color: #fff;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.26);
  backdrop-filter: blur(6px);
}

.pcd-chip .el-icon {
  font-size: 12px;
}

.pcd-chip--code {
  font-family: 'JetBrains Mono', Consolas, 'Courier New', monospace;
  color: #4338ca;
  background: rgba(255, 255, 255, 0.92);
  border-color: transparent;
}

.pcd-head__side {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.pcd-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 26px;
  padding: 0 11px;
  font-size: 12px;
  font-weight: 700;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 6px 14px rgba(30, 27, 75, 0.22);
}

.pcd-status__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
  animation: pcdPulse 1.8s ease-in-out infinite;
}

.pcd-status.is-danger {
  color: #e11d48;
}

.pcd-status.is-safe {
  color: #059669;
}

.pcd-close {
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: #fff;
  cursor: pointer;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.28);
  background: rgba(255, 255, 255, 0.14);
  transition: background 0.2s ease, transform 0.25s ease;
}

.pcd-close:hover {
  background: rgba(255, 255, 255, 0.28);
  transform: rotate(90deg);
}

/* 本体 */
.pcd-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.pcd-toolbar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(226, 232, 240, 0.9);
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
  animation: pcdRise 0.4s ease-out both;
}

.pcd-toolbar__label {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  font-weight: 700;
  color: #475569;
}

.pcd-toolbar__label .el-icon {
  width: 22px;
  height: 22px;
  padding: 4px;
  font-size: 14px;
  color: #4f46e5;
  border-radius: 7px;
  background: rgba(79, 70, 229, 0.1);
}

.pcd-toolbar__range.el-date-editor {
  width: 250px;
}

.pcd-toolbar .el-range-editor.el-input__wrapper {
  border-radius: 9px;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
}

.pcd-toolbar .el-range-editor.el-input__wrapper.is-active,
.pcd-toolbar .el-range-editor.el-input__wrapper:hover {
  box-shadow: 0 0 0 1px #a5b4fc inset;
}

.pcd-month {
  display: inline-flex;
  align-items: center;
  padding: 3px;
  gap: 2px;
  border-radius: 11px;
  background: #fff;
  box-shadow:
    0 0 0 1px #e2e8f0 inset,
    0 2px 6px rgba(15, 23, 42, 0.04);
}

.pcd-month__btn {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  height: 26px;
  padding: 0 10px;
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
  border: none;
  border-radius: 8px;
  background: transparent;
  transition: color 0.2s ease, background 0.2s ease, transform 0.15s ease, box-shadow 0.2s ease;
}

.pcd-month__btn .el-icon {
  font-size: 12px;
}

.pcd-month__btn:hover {
  color: #4f46e5;
  background: #eef2ff;
}

.pcd-month__btn:active {
  transform: scale(0.96);
}

.pcd-month__btn--current {
  min-width: 88px;
  justify-content: center;
  font-variant-numeric: tabular-nums;
}

.pcd-month__btn--current.is-active {
  color: #fff;
  background: linear-gradient(135deg, #6366f1, #7c3aed);
  box-shadow: 0 4px 10px rgba(99, 102, 241, 0.35);
}

.pcd-segment {
  display: inline-flex;
  gap: 2px;
  margin-left: auto;
  padding: 3px;
  border-radius: 11px;
  background: #eef1f8;
  box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.06);
}

.pcd-segment__item {
  height: 26px;
  padding: 0 11px;
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  cursor: pointer;
  border: none;
  border-radius: 8px;
  background: transparent;
  transition: color 0.2s ease, background 0.2s ease, box-shadow 0.2s ease;
}

.pcd-segment__item:hover {
  color: #4f46e5;
}

.pcd-segment__item.is-active {
  color: #fff;
  background: linear-gradient(135deg, #6366f1, #7c3aed);
  box-shadow: 0 4px 10px rgba(99, 102, 241, 0.35);
}

/* KPI カード */
.pcd-kpis {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.pcd-kpi {
  --k-grad: linear-gradient(135deg, #a78bfa, #7c3aed);
  --k-soft: rgba(124, 58, 237, 0.08);
  --k-glow: rgba(124, 58, 237, 0.25);
  --k-solid: #7c3aed;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 14px;
  background:
    linear-gradient(135deg, var(--k-soft) 0%, rgba(255, 255, 255, 0) 60%),
    #fff;
  border: 1px solid rgba(226, 232, 240, 0.9);
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 6px 16px rgba(15, 23, 42, 0.05);
  transition: transform 0.25s ease, box-shadow 0.25s ease;
  animation: pcdRise 0.45s ease-out both;
}

.pcd-kpi:nth-child(1) { animation-delay: 0.05s; }
.pcd-kpi:nth-child(2) { animation-delay: 0.1s; }
.pcd-kpi:nth-child(3) { animation-delay: 0.15s; }
.pcd-kpi:nth-child(4) { animation-delay: 0.2s; }

.pcd-kpi::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--k-grad);
}

.pcd-kpi::after {
  content: '';
  position: absolute;
  right: -22px;
  top: -26px;
  width: 84px;
  height: 84px;
  border-radius: 50%;
  background: var(--k-grad);
  opacity: 0.08;
  transition: transform 0.35s ease, opacity 0.35s ease;
  pointer-events: none;
}

.pcd-kpi:hover {
  transform: translateY(-3px);
  box-shadow:
    0 14px 28px var(--k-glow),
    0 0 0 1px var(--k-soft);
}

.pcd-kpi:hover::after {
  transform: scale(1.35);
  opacity: 0.14;
}

.pcd-kpi--violet {
  --k-grad: linear-gradient(135deg, #a78bfa, #7c3aed);
  --k-soft: rgba(124, 58, 237, 0.08);
  --k-glow: rgba(124, 58, 237, 0.22);
  --k-solid: #7c3aed;
}

.pcd-kpi--rose {
  --k-grad: linear-gradient(135deg, #fb7185, #e11d48);
  --k-soft: rgba(225, 29, 72, 0.07);
  --k-glow: rgba(225, 29, 72, 0.22);
  --k-solid: #e11d48;
}

.pcd-kpi--emerald {
  --k-grad: linear-gradient(135deg, #34d399, #059669);
  --k-soft: rgba(5, 150, 105, 0.08);
  --k-glow: rgba(5, 150, 105, 0.22);
  --k-solid: #059669;
}

.pcd-kpi--sky {
  --k-grad: linear-gradient(135deg, #38bdf8, #0284c7);
  --k-soft: rgba(2, 132, 199, 0.08);
  --k-glow: rgba(2, 132, 199, 0.22);
  --k-solid: #0284c7;
}

.pcd-kpi--amber {
  --k-grad: linear-gradient(135deg, #fbbf24, #d97706);
  --k-soft: rgba(217, 119, 6, 0.08);
  --k-glow: rgba(217, 119, 6, 0.22);
  --k-solid: #d97706;
}

.pcd-kpi__icon {
  position: relative;
  z-index: 1;
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 19px;
  color: #fff;
  border-radius: 12px;
  background: var(--k-grad);
  box-shadow:
    0 8px 16px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.45),
    inset 0 -2px 0 rgba(0, 0, 0, 0.08);
  transition: transform 0.3s ease;
}

.pcd-kpi:hover .pcd-kpi__icon {
  transform: translateY(-1px) rotate(-6deg) scale(1.06);
}

.pcd-kpi__body {
  position: relative;
  z-index: 1;
  min-width: 0;
}

.pcd-kpi__label {
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  white-space: nowrap;
}

.pcd-kpi__value {
  margin: 1px 0;
  font-size: 20px;
  font-weight: 800;
  line-height: 1.2;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pcd-kpi__value.is-negative {
  color: #dc2626;
}

.pcd-kpi__sub {
  font-size: 10.5px;
  font-weight: 600;
  color: var(--k-solid);
  opacity: 0.85;
  white-space: nowrap;
}

/* グラフカード */
.pcd-chart {
  overflow: hidden;
  border-radius: 16px;
  background: #fff;
  border: 1px solid rgba(226, 232, 240, 0.9);
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 10px 28px rgba(15, 23, 42, 0.06);
  animation: pcdRise 0.5s ease-out 0.25s both;
}

.pcd-chart__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 11px 16px;
  border-bottom: 1px solid #f1f5f9;
  background: linear-gradient(180deg, #fafbff, #fff);
}

.pcd-chart__title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 700;
  color: #1e293b;
}

.pcd-chart__title::before {
  content: '';
  width: 4px;
  height: 14px;
  border-radius: 2px;
  background: linear-gradient(180deg, #6366f1, #8b5cf6);
}

.pcd-chart__hint {
  font-size: 11px;
  color: #94a3b8;
}

.pcd-chart__tools {
  display: flex;
  align-items: center;
  gap: 14px;
}

.pcd-chart__switch {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 2px 10px 2px 6px;
  font-size: 11.5px;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
  border-radius: 999px;
  background: #f1f5f9;
  transition: background 0.2s ease;
}

.pcd-chart__switch:hover {
  background: #e0e7ff;
}

.pcd-chart__switch .el-switch {
  --el-switch-on-color: #6366f1;
}

.pcd-chart__canvas {
  min-height: 420px;
  padding: 14px 14px 8px;
}

@media (max-width: 1280px) {
  .pcd-kpis {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .pcd-segment {
    margin-left: 0;
  }
}

/* ─────────── 注文書発行ダイアログ ─────────── */
.order-sheet-dialog.el-dialog {
  padding: 0;
  overflow: hidden;
  border-radius: 16px;
  background: linear-gradient(180deg, #f6f7fd 0%, #eef1f8 100%);
  box-shadow:
    0 28px 64px -16px rgba(30, 27, 75, 0.4),
    0 0 0 1px rgba(255, 255, 255, 0.6) inset;
}

.order-sheet-dialog .el-dialog__header {
  margin: 0;
  padding: 0;
}

.order-sheet-dialog .el-dialog__body {
  padding: 14px 18px 4px;
  max-height: calc(100vh - 220px);
  overflow-y: auto;
}

.order-sheet-dialog .el-dialog__footer {
  padding: 10px 18px 14px;
}

.osd-head {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  color: #fff;
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 58%, #8b5cf6 100%);
  box-shadow: 0 10px 26px -10px rgba(79, 70, 229, 0.55);
}

.osd-head::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 92% -40%, rgba(255, 255, 255, 0.3) 0, transparent 40%),
    radial-gradient(circle at 4% 130%, rgba(56, 189, 248, 0.32) 0, transparent 32%);
  pointer-events: none;
}

.osd-head::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 28%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.16), transparent);
  animation: pcdShine 6s ease-in-out infinite;
  pointer-events: none;
}

.osd-head__icon,
.osd-head__text,
.osd-close {
  position: relative;
  z-index: 1;
}

.osd-head__icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  border-radius: 12px;
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.38), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.38);
  box-shadow:
    0 8px 18px rgba(30, 27, 75, 0.28),
    inset 0 1px 0 rgba(255, 255, 255, 0.5);
  transition: transform 0.3s ease;
}

.osd-head:hover .osd-head__icon {
  transform: rotate(-6deg) scale(1.06);
}

.osd-head__text {
  flex: 1;
  min-width: 0;
}

.osd-head__title {
  margin: 0;
  font-size: 17px;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: #fff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.15);
}

.osd-head__sub {
  margin: 2px 0 0;
  font-size: 11.5px;
  color: rgba(255, 255, 255, 0.78);
}

.osd-close {
  flex-shrink: 0;
  width: 30px;
  height: 30px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  color: #fff;
  cursor: pointer;
  border-radius: 9px;
  border: 1px solid rgba(255, 255, 255, 0.28);
  background: rgba(255, 255, 255, 0.14);
  transition: background 0.2s ease, transform 0.25s ease;
}

.osd-close:hover {
  background: rgba(255, 255, 255, 0.28);
  transform: rotate(90deg);
}

.osd-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.osd-body > * {
  animation: pcdRise 0.35s ease both;
}

.osd-body > *:nth-child(2) { animation-delay: 0.05s; }
.osd-body > *:nth-child(3) { animation-delay: 0.1s; }
.osd-body > *:nth-child(4) { animation-delay: 0.15s; }

.osd-target {
  display: flex;
  align-items: flex-end;
  gap: 14px;
  padding: 12px 14px;
  border-radius: 12px;
  background: linear-gradient(135deg, #eef2ff 0%, #f5f3ff 100%);
  border: 1px solid #e0e7ff;
  box-shadow: 0 6px 16px -10px rgba(79, 70, 229, 0.45);
}

.osd-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.osd-field--grow {
  flex: 1;
}

.osd-field .el-select {
  width: 100%;
}

.osd-label {
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
  letter-spacing: 0.04em;
}

.osd-period {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 10px;
  font-size: 12px;
  font-weight: 700;
  color: #4338ca;
  white-space: nowrap;
  border-radius: 6px;
  background: #fff;
  border: 1px solid #c7d2fe;
  font-variant-numeric: tabular-nums;
}

.osd-person-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.osd-person-option__del {
  font-size: 12px;
  color: #94a3b8;
  border-radius: 4px;
  opacity: 0;
  transition: opacity 0.15s ease, color 0.15s ease, background 0.15s ease;
}

.osd-person-popper .el-select-dropdown__item:hover .osd-person-option__del,
.osd-person-popper .el-select-dropdown__item.is-hovering .osd-person-option__del {
  opacity: 1;
}

.osd-person-option__del:hover {
  color: #e11d48;
  background: #ffe4e6;
}

.osd-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.osd-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.osd-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px 14px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #e8ebf3;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04), 0 8px 20px -14px rgba(30, 27, 75, 0.25);
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}

.osd-section:hover {
  border-color: #c7d2fe;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04), 0 12px 26px -14px rgba(79, 70, 229, 0.35);
}

.osd-section__title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12.5px;
  font-weight: 800;
  color: #1e1b4b;
}

.osd-section__title .el-icon {
  color: #6366f1;
  font-size: 14px;
}

.osd-section__meta {
  margin-left: auto;
  font-size: 11.5px;
  font-weight: 600;
  color: #4338ca;
  padding: 2px 10px;
  border-radius: 999px;
  background: #eef2ff;
  font-variant-numeric: tabular-nums;
}

.osd-section__meta + .osd-section__meta {
  margin-left: 6px;
}

.osd-section__meta--sheet {
  color: #047857;
  background: #ecfdf5;
}

.osd-table.el-table {
  --el-table-header-bg-color: #f8fafc;
  border-radius: 8px;
  font-size: 12px;
}

.osd-table.el-table th.el-table__cell {
  color: #475569;
  font-weight: 700;
}

.osd-table.el-table td.el-table__cell {
  font-variant-numeric: tabular-nums;
}

.osd-notes {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.osd-notes .el-textarea__inner {
  font-size: 11.5px;
}

.osd-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.osd-footer__file {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-right: auto;
  max-width: 55%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 11.5px;
  color: #64748b;
}

.osd-footer__print.el-button--primary {
  border: none;
  font-weight: 700;
  background: linear-gradient(135deg, #6366f1 0%, #7c3aed 100%);
  box-shadow: 0 6px 16px -6px rgba(99, 102, 241, 0.7);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.osd-footer__print.el-button--primary:not(.is-disabled):hover {
  transform: translateY(-1px);
  background: linear-gradient(135deg, #818cf8 0%, #8b5cf6 100%);
  box-shadow: 0 10px 22px -6px rgba(99, 102, 241, 0.75);
}

.osd-footer__print .el-icon {
  margin-right: 4px;
}

@media (max-width: 768px) {
  .osd-grid,
  .osd-target {
    grid-template-columns: 1fr;
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
