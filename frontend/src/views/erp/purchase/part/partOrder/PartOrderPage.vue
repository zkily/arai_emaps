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
          </div>
        </div>
      </div>
      <div class="header-actions">
        <el-button
          class="action-btn"
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
            <el-icon><Box /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.totalParts || 0 }}</div>
            <div class="stat-label">総部品種類数</div>
          </div>
        </div>

        <div class="stat-card info">
          <div class="stat-icon">
            <el-icon><Box /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">
              {{ stats.totalCurrentStock || 0 }}<span class="unit">束</span>
            </div>
            <div class="stat-label">在庫数合計</div>
          </div>
        </div>

        <div class="stat-card warning">
          <div class="stat-icon">
            <el-icon><Money /></el-icon>
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
            <el-icon><Operation /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">
              {{ stats.totalUsageQuantity || 0 }}
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
              {{ stats.totalOrderQuantity || 0 }}
            </div>
            <div class="stat-label">注文本数</div>
          </div>
        </div>

        <div class="stat-card amount">
          <div class="stat-icon">
            <el-icon><Money /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ formatCurrency(stats.totalOrderValue || 0) }}</div>
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
      <div class="table-container">
        <div class="table-header">
          <div class="table-tabs">
            <div
              class="tab-item"
              :class="{ active: activeTab === 'initial' }"
              @click="handleTabChange('initial')"
            >
              <el-icon><Box /></el-icon>
              <span>初期在庫管理</span>
            </div>
            <div
              class="tab-item"
              :class="{ active: activeTab === 'stock' }"
              @click="handleTabChange('stock')"
            >
              <el-icon><Box /></el-icon>
              <span>部品日別在庫</span>
            </div>
            <div
              class="tab-item"
              :class="{ active: activeTab === 'usage' }"
              @click="handleTabChange('usage')"
            >
              <el-icon><Operation /></el-icon>
              <span>部品使用管理</span>
            </div>
            <div
              class="tab-item"
              :class="{ active: activeTab === 'order' }"
              @click="handleTabChange('order')"
            >
              <el-icon><ShoppingCart /></el-icon>
              <span>部品注文</span>
            </div>
            <div
              class="tab-item"
              :class="{ active: activeTab === 'orderHistory' }"
              @click="handleTabChange('orderHistory')"
            >
              <el-icon><List /></el-icon>
              <span>部品注文履歴</span>
            </div>
          </div>
          <div class="table-actions" v-if="activeTab === 'order'">
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
            stripe
            border
            class="modern-table"
            :default-sort="{ prop: 'date', order: 'ascending' }"
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
                <span class="usage-quantity-readonly">{{ formatValue(row.usage_quantity) }}</span>
              </template>
            </el-table-column>
            <el-table-column
              label="使用計画"
              width="110"
              align="center"
              class-name="usage-quantity-column"
            >
              <template #default="{ row }">
                <span class="usage-quantity-readonly">{{ formatValue(row.usage_plan_qty) }}</span>
              </template>
            </el-table-column>
            <el-table-column
              label="在庫推移"
              width="110"
              align="center"
              class-name="usage-quantity-column"
            >
              <template #default="{ row }">
                <span class="usage-quantity-readonly">{{ formatValue(row.stock_trend) }}</span>
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
            stripe
            border
            class="modern-table"
            :default-sort="{ prop: 'date', order: 'ascending' }"
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
                <span class="usage-quantity-readonly">{{ formatValue(row.usage_quantity) }}</span>
              </template>
            </el-table-column>
            <el-table-column
              label="使用計画"
              width="110"
              align="center"
              class-name="usage-quantity-column"
            >
              <template #default="{ row }">
                <span class="usage-quantity-readonly">{{ formatValue(row.usage_plan_qty) }}</span>
              </template>
            </el-table-column>
            <el-table-column
              label="在庫推移"
              width="110"
              align="center"
              class-name="usage-quantity-column"
            >
              <template #default="{ row }">
                <span class="usage-quantity-readonly">{{ formatValue(row.stock_trend) }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 部品注文テーブル -->
        <div class="table-content" v-if="activeTab === 'order'">
          <el-table
            v-loading="loading"
            :data="filteredTableData"
            stripe
            border
            class="modern-table"
            :default-sort="{ prop: 'date', order: 'ascending' }"
            height="calc(100vh - 280px)"
            :max-height="800"
          >
            <el-table-column prop="date" label="日付" width="120" align="center" sortable />
            <el-table-column prop="part_cd" label="部品CD" width="120" align="center" />
            <el-table-column
              prop="part_name"
              label="部品名"
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
          </el-table>
        </div>

        <!-- 部品注文履歴（期間・キーワードで注文数>0の material_stock のみ、参照専用） -->
        <div class="table-content" v-if="activeTab === 'orderHistory'">
          <el-table
            v-loading="loading"
            :data="filteredTableData"
            stripe
            border
            class="modern-table order-history-table"
            :default-sort="{ prop: 'date', order: 'ascending' }"
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
                {{ formatValue(row.order_quantity) }}
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
            stripe
            border
            class="modern-table"
            :default-sort="{ prop: 'date', order: 'ascending' }"
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
                  class="adjustment-quantity-input"
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

    <!-- 受注確認ダイアログ -->
    <el-dialog
      v-model="orderConfirmDialogVisible"
      title="受注確認"
      width="800px"
      :destroy-on-close="true"
    >
      <div class="order-confirm-content">
        <div class="order-summary">
          <h3>受注サマリー</h3>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="受注材料数">
              {{ selectedOrderItems.length }}件
            </el-descriptions-item>
            <el-descriptions-item label="注文本数合計">
              {{ totalOrderQuantity }}
            </el-descriptions-item>
            <el-descriptions-item label="総受注金額">
              {{ formatCurrency(totalOrderValue) }}
            </el-descriptions-item>
            <el-descriptions-item label="受注日">
              {{ new Date().toLocaleDateString('ja-JP', { timeZone: 'Asia/Tokyo' }) }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <div class="order-details">
          <h3>受注詳細</h3>
          <el-table
            :data="selectedOrderItems"
            border
            size="small"
            :default-sort="{ prop: 'part_name', order: 'ascending' }"
          >
            <el-table-column prop="part_cd" label="部品CD" width="120" />
            <el-table-column prop="part_name" label="部品名" min-width="150" sortable />
            <el-table-column prop="order_quantity" label="注文本数" width="100" align="center" />
            <el-table-column prop="unit" label="単位" width="80" align="center" />
            <el-table-column prop="unit_price" label="単価" width="100" align="right">
              <template #default="{ row }">
                {{ formatCurrency(row.unit_price) }}
              </template>
            </el-table-column>
            <el-table-column label="金額" width="120" align="right">
              <template #default="{ row }">
                {{ formatCurrency((row.order_quantity || 0) * (row.unit_price || 0)) }}
              </template>
            </el-table-column>
            <el-table-column prop="supplier_name" label="仕入先" width="150" />
          </el-table>
        </div>

        <div class="order-notes">
          <el-form-item label="備考">
            <el-input
              v-model="orderNotes"
              type="textarea"
              :rows="3"
              placeholder="受注に関する備考を入力してください"
            />
          </el-form-item>
        </div>
      </div>

      <template #footer>
        <el-button @click="orderConfirmDialogVisible = false">キャンセル</el-button>
        <el-button type="primary" @click="handleConfirmOrder" :loading="orderLoading">
          受注確定
        </el-button>
      </template>
    </el-dialog>

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
                  placeholder="支払期日・支払方法・検査完了期日・有償支給原材料代金の決済期日及び方法については、令和8年1月1日の「支払方法等について」によります。"
                  class="form-textarea-compact"
                  size="small"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
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
} from '@element-plus/icons-vue'
import request from '@/utils/request'
import {
  syncPartStockFromMaster,
  getPartStockSupplierNames,
  getPartStockList,
  updatePartStock,
  createPartStock,
  saveMaruichiPartOrderPdf,
} from '@/api/part'
import { getPartList } from '@/api/master/partMaster'
import html2canvas from 'html2canvas'
import { jsPDF } from 'jspdf'
import { MARUICHI_ORDER_SHEET_STYLES } from '@/utils/maruichiOrderSheetStyles'
import { calculatePartStock } from '@/api/partStockCalculation'
import { generatePartStockData } from '@/api/partDataGeneration'
import { updatePartQuantities } from '@/api/partStockUpdate'
import type { PartQuantityUpdate } from '@/api/partStockUpdate'

// 定义类型接口
interface PartOrderItem {
  id: number
  part_cd: string
  part_name: string
  date: string
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
const orderLoading = ref(false)
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
const initialStockData = ref<InitialStockItem[]>([])
/** 部品注文履歴タブ用（期間・キーワードで material_stock かつ注文数>0） */
const orderHistoryData = ref<PartOrderItem[]>([])
const orderConfirmDialogVisible = ref(false)
const orderNotes = ref('')
const activeTab = ref('stock') // デフォルトは部品日別在庫タブ
const partMasterSyncLoading = ref(false)

// 统计数据
const stats = ref({
  totalParts: 0,
  totalCurrentStock: 0,
  averageUnitPrice: 0,
  totalUsageQuantity: 0,
  totalOrderQuantity: 0,
  totalOrderValue: 0,
})

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
    '2.支払期日・支払方法・検査完了期日・有償支給原材料代金の決済期日及び方法については、令和8年1月1日の「支払方法等について」によります。',
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

// 注文があるデータをフィルタリング
const selectedOrderItems = computed(() => {
  return tableData.value.filter((row) => row.order_quantity && row.order_quantity > 0)
})

// 総材料数：フィルタリングされたデータの材料数（ページネーション総数を使用、現在ページのデータではない）
const totalParts = computed(() => {
  return pagination.total
})

// 在庫数合計：一覧表示中データの現在在庫合計
const totalCurrentStock = computed(() => {
  return tableData.value.reduce((total, row) => total + (row.current_stock || 0), 0)
})

// 受注予定：注文本数（order_quantity）合計
const totalOrderQuantity = computed(() => {
  return selectedOrderItems.value.reduce((total, row) => total + (row.order_quantity || 0), 0)
})

// 受注予定金額：统计注文金額
const totalOrderValue = computed(() => {
  return selectedOrderItems.value.reduce((total, row) => total + (row.order_amount || 0), 0)
})

// 平均単価：统计unit_price字段的平均值
const averageUnitPrice = computed(() => {
  if (tableData.value.length === 0) return 0
  const totalPrice = tableData.value.reduce((total, row) => total + (row.unit_price || 0), 0)
  return totalPrice / tableData.value.length
})

// 使用数合計：当前一覧（tableData）の usage_quantity 合計
const totalUsageQuantity = computed(() => {
  return tableData.value.reduce((total, row) => total + (row.usage_quantity || 0), 0)
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
      tableData.value = list.map((item: any) => mapPartStockRow(item))
      pagination.total = total
      updateStats()
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
      orderHistoryData.value = list.map((item: any) => mapPartStockRow(item))
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
        initialStockData.value = list.map((item: any) => {
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
        updateStats()
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
          initialStockData.value = fallbackList.map((item: any) => ({
            ...item,
            // current_stockをinitial_stockの初期値として使用
            initial_stock: item.current_stock || 0,
            // 調整数はデフォルトで0
            adjustment_quantity: 0,
          }))
          pagination.total = (fallbackResult as any)?.data?.total ?? fallbackList.length
          updateStats()
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
  }
}

const updateStats = () => {
  stats.value.totalParts = totalParts.value
  stats.value.totalCurrentStock = totalCurrentStock.value
  stats.value.averageUnitPrice = averageUnitPrice.value
  stats.value.totalUsageQuantity = totalUsageQuantity.value
  stats.value.totalOrderQuantity = totalOrderQuantity.value
  stats.value.totalOrderValue = totalOrderValue.value
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
  return value.toString()
}

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
      sums[index] = t ? String(t) : ''
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

const handleOrderQuantityChange = async (row: PartOrderItem) => {
  const ppb = Number(row.pieces_per_bundle) || 1
  if (row.order_quantity > 0) {
    row.order_bundle_quantity = row.order_quantity * ppb
    row.order_amount = row.order_bundle_quantity * (Number(row.unit_price) || 0)
  } else {
    row.order_bundle_quantity = 0
    row.order_amount = 0
  }

  updateStats()
  await saveQuantityToDatabase(row)
}

// 保存数量到数据库
const saveQuantityToDatabase = async (row: PartOrderItem) => {
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
      usage_quantity: row.usage_quantity || 0,
      order_quantity: row.order_quantity || 0,
      order_bundle_quantity: row.order_bundle_quantity || 0,
      order_amount: row.order_amount || 0,
    })

    console.log('API响应:', response)

    if (response && response.success) {
      console.log(`成功保存材料 ${row.part_cd} 的数量到数据库`)
    } else {
      const errorMessage = response?.message || '不明なエラー'
      console.error(`保存材料 ${row.part_cd} 的数量失败:`, errorMessage)
      ElMessage.warning(`保存失败: ${errorMessage}`)
    }
  } catch (error: any) {
    console.error(`保存材料 ${row.part_cd} 的数量时发生错误:`, error)
    ElMessage.error(`保存中にエラーが発生しました: ${error.message || '不明なエラー'}`)
  }
}

const handleConfirmOrder = async () => {
  if (selectedOrderItems.value.length === 0) {
    ElMessage.warning('受注数量を入力してください')
    return
  }

  try {
    orderLoading.value = true

    const orderData = {
      items: selectedOrderItems.value.map((item) => ({
        part_cd: item.part_cd,
        part_name: item.part_name,
        order_quantity: item.order_quantity,
        unit_price: item.unit_price,
        supplier_cd: item.supplier_cd,
        supplier_name: item.supplier_name,
      })),
      notes: orderNotes.value,
      total_quantity: totalOrderQuantity.value,
      total_value: totalOrderValue.value,
    }

    const response = await request.post('/api/part-order/create', orderData) as any

    if (response?.data?.success ?? response?.success) {
      ElMessage.success('受注が確定されました')
      orderConfirmDialogVisible.value = false
      orderNotes.value = ''

      // 清空受注数量
      tableData.value.forEach((row) => {
        row.order_quantity = 0
        row.order_bundle_quantity = 0
        row.order_amount = 0
      })
      updateStats()
    } else {
      ElMessage.error('受注の確定に失敗しました')
    }
  } catch (error) {
    console.error('受注の確定に失敗しました:', error)
    ElMessage.error('受注の確定に失敗しました')
  } finally {
    orderLoading.value = false
  }
}

// 部品マスタ更新: parts（status=1）→ 既存 part_stock 行のマスタ項目を上書き（期間で絞り可）
const handleSyncPartMaster = async () => {
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
  try {
    const hasRange = searchForm.dateRange && searchForm.dateRange.length === 2
    const rangeExplain = hasRange
      ? `・使用数・使用計画の同期期間: 画面の期間 ${searchForm.dateRange![0]} ～ ${searchForm.dateRange![1]}（同一区間の両項目を更新）\n`
      : '・使用数・使用計画の同期期間: 未選択のため「計算開始日～part_stock のデータ最終日」（同一区間の両項目を更新）\n'
    await ElMessageBox.confirm(
      '在庫計算を実行しますか？\n\n' +
        '・計算開始日（現在庫・推移のローリング起点）: part_stock 全体で initial_stock>0 の行のうち最も遅い日付\n' +
        rangeExplain +
        '・使用数: production_summarys（welding_actual + welding_defect）× BOM → planned_usage\n' +
        '・使用計画: production_summarys.welding_actual_plan × BOM → usage_plan_qty\n' +
        '・現在庫: initial+調整+注文−使用数+前日現在庫\n' +
        '・在庫推移: initial+調整+注文−使用計画+前日在庫推移',
      '在庫計算確認',
      {
        confirmButtonText: '実行',
        cancelButtonText: 'キャンセル',
        type: 'warning',
      },
    )

    stockCalculationLoading.value = true

    const calcParams =
      hasRange
        ? { start_date: searchForm.dateRange![0], end_date: searchForm.dateRange![1] }
        : undefined

    const response = await calculatePartStock(calcParams)
    const d = response?.data

    if (response?.success !== false) {
      const calculated_count = d?.calculated_count ?? 0
      const updated_count = d?.updated_count ?? 0
      const usage_synced = d?.usage_synced ?? 0
      const usage_plan_synced = d?.usage_plan_synced ?? 0
      const up = d?.usage_period
      const periodLine =
        up?.start_date && up?.end_date
          ? `\n同期期間: ${up.start_date} ～ ${up.end_date}`
          : ''

      ElMessage.success(
        `在庫計算が完了しました。${periodLine}\n使用数を同期した行: ${usage_synced}件\n使用計画を同期した行: ${usage_plan_synced}件\n部品別計算: ${calculated_count}件\n現在庫・在庫推移を更新した行: ${updated_count}件`,
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
  // 检查是否有选择日期
  if (!searchForm.dateRange || searchForm.dateRange.length === 0) {
    ElMessage.warning('请先选择日期范围')
    return
  }

  // 获取合并后的注文数据
  const mergedOrderItems = await getMergedOrderData()

  if (mergedOrderItems.length === 0) {
    ElMessage.warning('没有找到符合条件的注文数据')
    return
  }

  // 印刷確認ダイアログを表示
  printConfirmDialogVisible.value = true
}

// 确认打印
const confirmPrint = async () => {
  try {
    const mergedOrderItems = await getMergedOrderData()

    if (mergedOrderItems.length === 0) {
      ElMessage.warning('没有找到符合条件的注文数据')
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
  /* 捕获时给左右留白，避免 PDF 内容贴到页面左右边缘 */
  padding-left: 6mm !important;
  padding-right: 6mm !important;
  box-sizing: border-box !important;
}
html.sheet-capture-doc .order-sheet .notes {
  margin-top: 5mm !important;
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
  // 重置日期
  dataGenerationStartDate.value = ''
  dataGenerationEndDate.value = ''
  // 显示日期选择对话框
  dataGenerationDialogVisible.value = true
}

// データ生成確認
const confirmDataGeneration = async () => {
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
      response = await request.get('/api/master/parts')
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
  padding: 10px 12px;
  background: linear-gradient(135deg, #eef2f7 0%, #dce4f0 100%);
  min-height: 100vh;
}

/* 页面头部样式 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 18px;
  margin-bottom: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 10px;
  color: white;
  box-shadow: 0 4px 18px rgba(102, 126, 234, 0.35);
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
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="rgba(255,255,255,0.1)"/><circle cx="75" cy="75" r="1" fill="rgba(255,255,255,0.1)"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
  opacity: 0.1;
}

.header-left {
  display: flex;
  align-items: center;
  z-index: 1;
}

.title-section {
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-icon {
  width: 34px;
  height: 34px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  backdrop-filter: blur(10px);
}

.title-text {
  display: flex;
  flex-direction: column;
}

.main-title {
  font-size: 18px;
  font-weight: 700;
  margin: 0;
  letter-spacing: 0.5px;
}

.subtitle {
  font-size: 11px;
  opacity: 0.85;
  margin: 2px 0 0 0;
  font-weight: 400;
}

.header-actions {
  display: flex;
  gap: 8px;
  z-index: 1;
}

.action-btn {
  padding: 6px 14px;
  border-radius: 7px;
  font-weight: 600;
  font-size: 12px;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.success-btn {
  background: rgba(67, 233, 123, 0.9);
  color: white;
}

.success-btn:hover {
  background: rgba(67, 233, 123, 1);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(67, 233, 123, 0.4);
}

.warning-btn {
  background: rgba(250, 173, 20, 0.9);
  color: white;
}

.warning-btn:hover {
  background: rgba(250, 173, 20, 1);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(250, 173, 20, 0.4);
}

/* 统计卡片样式 */
.stats-container {
  margin-bottom: 8px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 8px;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: 8px 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.07);
  transition: all 0.25s ease;
  border: 1px solid rgba(0, 0, 0, 0.05);
  position: relative;
  overflow: hidden;
  min-height: 56px;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 3px;
  height: 100%;
  background: var(--card-color);
  transition: width 0.3s ease;
}

.stat-card:hover::before {
  width: 5px;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.11);
}

.stat-card.primary {
  --card-color: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-card.info {
  --card-color: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-card.warning {
  --card-color: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}

.stat-card.success {
  --card-color: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-card.order {
  --card-color: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
}

.stat-card.bundle {
  --card-color: linear-gradient(135deg, #d299c2 0%, #fef9d7 100%);
}

.stat-card.weight {
  --card-color: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
}

.stat-card.amount {
  --card-color: linear-gradient(135deg, #a8caba 0%, #5d4e75 100%);
}

.stat-card .stat-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: var(--card-color);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 14px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  flex-shrink: 0;
}

.stat-content {
  flex: 1;
  min-width: 0;
}

.stat-value {
  font-size: 16px;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 2px;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stat-value .unit {
  font-size: 11px;
  font-weight: 500;
  color: #718096;
  margin-left: 2px;
}

.stat-label {
  font-size: 10px;
  color: #718096;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ===== Filter Bar ===== */
.search-section {
  margin-bottom: 8px;
}

.search-container {
  background: white;
  border-radius: 10px;
  padding: 6px 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.07);
  border: 1px solid rgba(102, 126, 234, 0.1);
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
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  white-space: nowrap;
  flex-shrink: 0;
}

.filter-label .el-icon {
  font-size: 12px;
  color: #667eea;
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
  border-color: #667eea;
  background: white;
}

.filter-input :deep(.el-input__wrapper.is-focus),
.filter-select :deep(.el-select__wrapper.is-focused) {
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.12);
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
  border-color: #667eea;
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
  border-color: #667eea;
  color: #667eea;
  background: rgba(102, 126, 234, 0.06);
}

.date-nav-btn.today-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 0 10px;
}

.date-nav-btn.today-btn:hover {
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4);
  transform: translateY(-1px);
}



/* 表格区域样式 */
.table-section {
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.07);
  border: 1px solid rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.table-container {
  padding: 0;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-bottom: 1px solid #dee2e6;
}

.table-tabs {
  display: flex;
  gap: 3px;
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 14px;
  border-radius: 7px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s ease;
  color: #6b7280;
  background: transparent;
}

.tab-item:hover {
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
}

.tab-item.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 3px 10px rgba(102, 126, 234, 0.3);
}

.table-actions {
  display: flex;
  gap: 6px;
}

.print-btn {
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.table-content {
  padding: 0;
}

.modern-table {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid #e2e8f0;
  background: white;
}

.order-history-table :deep(.el-table__footer-wrapper .el-table__cell) {
  font-weight: 600;
  background: #f8fafc;
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

.modern-table :deep(.el-loading-spinner) {
  color: #667eea;
}

/* 表格行间距优化 */
.modern-table :deep(.el-table__row) {
  transition: all 0.2s ease;
}

.modern-table :deep(.el-table__row):hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.pagination-wrapper {
  padding: 8px 16px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-top: 1px solid #dee2e6;
  display: flex;
  justify-content: center;
}

.modern-pagination {
  --el-pagination-button-color: #6b7280;
  --el-pagination-hover-color: #667eea;
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
  border-color: #667eea;
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
  color: #667eea;
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
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  box-shadow: 0 2px 4px rgba(102, 126, 234, 0.2);
}

.confirm-btn-compact:hover:not(:disabled) {
  box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
  color: #667eea;
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
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  border: none !important;
  color: white !important;
}

:deep(.data-generation-confirm-dialog .el-button--primary:hover) {
  transform: translateY(-2px) !important;
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4) !important;
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
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
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
    grid-template-columns: repeat(4, 1fr);
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
    grid-template-columns: repeat(4, 1fr);
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
    grid-template-columns: repeat(4, 1fr);
    gap: 5px;
  }

  .stat-card {
    padding: 5px 6px;
    min-height: 44px;
    border-radius: 6px;
  }

  .stat-card::before {
    width: 2px;
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

/* ElementPlus现代化覆盖样式（行高约 70%：内边距与行高调小约 30%） */
:deep(.el-table) {
  --el-table-border-color: #e2e8f0;
  --el-table-bg-color: #ffffff;
  --el-table-tr-bg-color: #ffffff;
  --el-table-expanded-cell-bg-color: #fafbfc;
}

:deep(.el-table th.el-table__cell) {
  background: linear-gradient(135deg, #f8fafc 0%, #edf2f7 100%);
  color: #2d3748;
  font-weight: 700;
  font-size: 13px;
  padding: calc(8px * 0.7) calc(6px * 0.7);
  line-height: calc(1.3 * 0.7);
  border-bottom: 2px solid #cbd5e0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  position: relative;
}

:deep(.el-table th.el-table__cell::after) {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  opacity: 0.6;
}

:deep(.el-table td.el-table__cell) {
  padding: calc(4px * 0.7) calc(6px * 0.7);
  border-bottom: 1px solid #f1f5f9;
  font-size: 13px;
  line-height: calc(1.3 * 0.7);
  transition: all 0.2s ease;
}

/* 現在在庫：字号加大一号、粗体、纯黑（行高压缩时略放大行距以免裁字） */
:deep(.el-table td.current-stock-column) {
  font-size: 14px;
  font-weight: bold;
  color: #000000;
  line-height: 1.1;
}

:deep(.el-table td.current-stock-column .cell) {
  font-size: 14px;
  font-weight: bold;
  color: #000000;
  line-height: 1.1;
}

/* 使用数・注文本数：字号加大一号、粗体、纯黑（与現在在庫一致） */
:deep(.el-table td.usage-quantity-column) {
  font-size: 14px;
  font-weight: bold;
  color: #000000;
  line-height: 1.1;
}

:deep(.el-table td.usage-quantity-column .cell) {
  font-size: 14px;
  font-weight: bold;
  color: #000000;
  line-height: 1.1;
}

:deep(.el-table td.order-quantity-column) {
  font-size: 14px;
  font-weight: bold;
  color: #000000;
  line-height: 1.1;
}

:deep(.el-table td.order-quantity-column .cell) {
  font-size: 14px;
  font-weight: bold;
  color: #000000;
  line-height: 1.1;
}

:deep(.el-table td.usage-quantity-column .el-input-number .el-input__inner),
:deep(.el-table td.order-quantity-column .el-input-number .el-input__inner) {
  font-size: 14px !important;
  font-weight: bold !important;
  color: #000000 !important;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background-color: #f8fafc;
}

:deep(.el-table__body tr:hover td) {
  background-color: #e0f2fe !important;
  transform: scale(1.001);
}

:deep(.el-input-number) {
  width: 100%;
}

:deep(.el-input-number .el-input__inner) {
  padding: calc(2px * 0.7) calc(6px * 0.7);
  font-size: 12px;
  height: calc(20px * 0.7);
  border-radius: 5px;
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;
}

:deep(.el-input-number .el-input__inner):focus {
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
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
  background: #667eea;
  color: white;
  border-color: #667eea;
}

:deep(.usage-quantity-input .el-input__inner) {
  background-color: #e0f2fe !important;
  border-color: #0ea5e9 !important;
  font-weight: 600;
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
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;
  font-size: 11px;
}

:deep(.el-input .el-input__inner):focus {
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
}

/* 表格内文本样式优化 */
:deep(.el-table .cell) {
  padding: calc(2px * 0.7) calc(6px * 0.7);
  line-height: calc(1.3 * 0.7);
  font-size: 12px;
}

/* 数值显示样式优化 */
.negative-number {
  color: #ef4444 !important;
  font-weight: 700 !important;
  background-color: #fef2f2;
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid #fecaca;
}

/* 表格容器优化 */
.table-section {
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.07);
  border: 1px solid rgba(0, 0, 0, 0.05);
  overflow: hidden;
  margin-bottom: 8px;
}

/* 表格头部优化 */
.table-header {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-bottom: 1px solid #dee2e6;
  padding: 8px 12px;
}

/* 分页样式优化 */
.pagination-wrapper {
  padding: 8px 16px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-top: 1px solid #dee2e6;
  display: flex;
  justify-content: center;
}

:deep(.order-quantity-column) {
  background-color: #fef3c7 !important;
}

:deep(.order-quantity-column .cell) {
  background-color: #fef3c7 !important;
  padding: 4px !important;
}

:deep(.order-quantity-input .el-input__inner) {
  background-color: #fde68a !important;
  border-color: #f59e0b !important;
  font-weight: 600;
}

/* 对话框样式 */
.order-confirm-content {
  padding: 20px 0;
}

.order-summary,
.order-details {
  margin-bottom: 24px;
}

.order-summary h3,
.order-details h3 {
  margin: 0 0 16px;
  color: #2d3748;
  font-size: 1.1rem;
  font-weight: 600;
}

.order-notes {
  margin-top: 20px;
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
  padding: 10px 14px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: rgb(8, 8, 8);
  border-bottom: none;
}

.dialog-header-with-button {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.dialog-title {
  font-size: 14px;
  font-weight: 600;
  color: rgb(10, 10, 10);
}

.confirm-btn-header {
  border-radius: 5px;
  padding: 5px 12px;
  font-weight: 600;
  font-size: 11px;
  background: rgba(23, 241, 158, 0.589);
  border: 1px solid rgba(8, 7, 7, 0.774);
  color: rgb(7, 7, 7);
  transition: all 0.2s ease;
  backdrop-filter: blur(10px);
  margin-left: 200px;
}

.confirm-btn-header:hover {
  background: rgba(210, 230, 103, 0.3);
  border-color: rgba(5, 180, 28, 0.5);
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
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
  border-color: #667eea;
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
  color: #667eea;
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
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
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
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
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
  background-color: #f0f9ff;
  border-color: #0ea5e9;
  color: #0369a1;
  font-weight: 600;
}

.initial-stock-input.positive-stock :deep(.el-input__inner):focus {
  border-color: #0284c7;
  box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.2);
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
