<template>
  <div class="production-data-management">
    <div class="page-header-shell">
      <div class="page-header-row">
      <div class="title-group">
        <div class="page-title-mark" aria-hidden="true">
          <el-icon :size="22"><DataBoard /></el-icon>
        </div>
        <div class="title-text-block">
          <h1 class="page-title">生産データ管理</h1>
          <p class="page-subtitle">受注・実績・在庫を一元管理</p>
        </div>
        <el-tag type="info" size="small" class="record-count">
          {{ total.toLocaleString() }} 件
        </el-tag>
      </div>
      <div class="header-actions">
        <!-- PC: ドロップダウン / スマホ・タブレット: ボタンで Drawer を開く -->
        <template v-if="!isSmallScreen">
          <el-dropdown
            trigger="click"
            placement="bottom-start"
            :disabled="generating || updatingCarryOver || updatingOrder || updatingAll || updatingActual || updatingDefect || updatingScrap || updatingOnHold || updatingProductionDates || updatingPlan || updatingInventoryTrend || updatingProductMaster || updatingMachine"
            class="others-dropdown"
            @command="handleDropdownCommand"
          >
            <el-button
              size="small"
              :icon="RefreshRight"
              :loading="generating || updatingCarryOver || updatingOrder || updatingAll || updatingFromOrderDaily || updatingActual || updatingDefect || updatingScrap || updatingOnHold || updatingProductionDates || updatingPlan || updatingInventoryTrend || updatingProductMaster || updatingMachine"
              class="modern-btn others-btn"
            >
              各種更新機能
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item
                  command="generate"
                  :disabled="generating || updatingCarryOver || updatingOrder || updatingAll"
                  class="dropdown-item generate-item"
                >
                  <el-icon><DocumentAdd /></el-icon>
                  <span>データ生成</span>
                </el-dropdown-item>
                <el-dropdown-item
                  command="all-update"
                  :disabled="generating || updatingCarryOver || updatingOrder || updatingAll"
                  class="dropdown-item all-update-item"
                >
                  <el-icon><Operation /></el-icon>
                  <span>全部一括更新</span>
                </el-dropdown-item>
                <el-dropdown-item
                  command="update-order"
                  :disabled="updatingFromOrderDaily"
                  class="dropdown-item update-order-item"
                >
                  <el-icon><Refresh /></el-icon>
                  <span>受注データ更新</span>
                </el-dropdown-item>
                <el-dropdown-item
                  command="batch-initial"
                  class="dropdown-item batch-initial-item"
                >
                  <el-icon><DocumentCopy /></el-icon>
                  <span>初期在庫一括登録</span>
                </el-dropdown-item>
                <el-dropdown-item
                  command="carry-over"
                  :disabled="generating || updatingCarryOver || updatingOrder || updatingAll"
                  class="dropdown-item carry-over-item"
                >
                  <el-icon><RefreshRight /></el-icon>
                  <span>繰越データ更新</span>
                </el-dropdown-item>
                <el-dropdown-item
                  command="actual"
                  :disabled="generating || updatingCarryOver || updatingOrder || updatingAll"
                  class="dropdown-item actual-item"
                >
                  <el-icon><Refresh /></el-icon>
                  <span>実績データ更新</span>
                </el-dropdown-item>
                <el-dropdown-item
                  command="defect"
                  :disabled="generating || updatingCarryOver || updatingOrder || updatingAll"
                  class="dropdown-item defect-item"
                >
                  <el-icon><WarningFilled /></el-icon>
                  <span>不良データ更新</span>
                </el-dropdown-item>
                <el-dropdown-item
                  command="scrap"
                  :disabled="generating || updatingCarryOver || updatingOrder || updatingAll"
                  class="dropdown-item scrap-item"
                >
                  <el-icon><Delete /></el-icon>
                  <span>廃棄データ更新</span>
                </el-dropdown-item>
                <el-dropdown-item
                  command="on-hold"
                  :disabled="generating || updatingCarryOver || updatingOrder || updatingAll"
                  class="dropdown-item on-hold-item"
                >
                  <el-icon><Clock /></el-icon>
                  <span>保留データ更新</span>
                </el-dropdown-item>
                <el-dropdown-item
                  command="production-dates"
                  :disabled="generating || updatingCarryOver || updatingOrder || updatingAll"
                  class="dropdown-item production-dates-item"
                >
                  <el-icon><Calendar /></el-icon>
                  <span>生産計画日更新</span>
                </el-dropdown-item>
                <el-dropdown-item
                  command="plan"
                  :disabled="generating || updatingCarryOver || updatingOrder || updatingAll"
                  class="dropdown-item plan-item"
                >
                  <el-icon><DocumentCopy /></el-icon>
                  <span>計画データ更新</span>
                </el-dropdown-item>
                <el-dropdown-item
                  command="inventory-trend"
                  :disabled="generating || updatingCarryOver || updatingOrder || updatingAll"
                  class="dropdown-item inventory-trend-item"
                >
                  <el-icon><Refresh /></el-icon>
                  <span>在庫・推移更新</span>
                </el-dropdown-item>
                <el-dropdown-item
                  command="product-master"
                  :disabled="generating || updatingCarryOver || updatingOrder || updatingAll || updatingProductMaster"
                  class="dropdown-item product-master-item"
                >
                  <el-icon><Goods /></el-icon>
                  <span>製品マスタ更新</span>
                </el-dropdown-item>
                <el-dropdown-item
                  command="machine"
                  :disabled="generating || updatingCarryOver || updatingOrder || updatingAll || updatingMachine"
                  class="dropdown-item machine-update-item"
                >
                  <el-icon><Monitor /></el-icon>
                  <span>設備フィールド更新</span>
                </el-dropdown-item>
                <el-dropdown-item
                  command="batch-actual"
                  :disabled="generating || updatingCarryOver || updatingOrder || updatingAll"
                  class="dropdown-item batch-actual-item"
                >
                  <el-icon><DocumentCopy /></el-icon>
                  <span>実績一括登録</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
        <template v-else>
          <el-button
            size="small"
            :icon="RefreshRight"
            :loading="generating || updatingCarryOver || updatingOrder || updatingAll || updatingFromOrderDaily || updatingActual || updatingDefect || updatingScrap || updatingOnHold || updatingProductionDates || updatingPlan || updatingInventoryTrend || updatingProductMaster || updatingMachine"
            :disabled="generating || updatingCarryOver || updatingOrder || updatingAll || updatingActual || updatingDefect || updatingScrap || updatingOnHold || updatingProductionDates || updatingPlan || updatingInventoryTrend || updatingProductMaster || updatingMachine"
            class="modern-btn others-btn"
            @click="showOthersDrawer = true"
          >
            その他
          </el-button>
          <el-drawer
            v-model="showOthersDrawer"
            title="その他"
            direction="btt"
            size="auto"
            class="others-drawer"
          >
            <div class="others-drawer-list">
              <div
                class="others-drawer-item"
                :class="{ 'is-disabled': generating || updatingCarryOver || updatingOrder || updatingAll }"
                @click="!(generating || updatingCarryOver || updatingOrder || updatingAll) && onOthersDrawerSelect('generate')"
              >
                <el-icon><DocumentAdd /></el-icon>
                <span>データ生成</span>
              </div>
              <div
                class="others-drawer-item"
                :class="{ 'is-disabled': generating || updatingCarryOver || updatingOrder || updatingAll }"
                @click="!(generating || updatingCarryOver || updatingOrder || updatingAll) && onOthersDrawerSelect('all-update')"
              >
                <el-icon><Operation /></el-icon>
                <span>全部一括更新</span>
              </div>
              <div
                class="others-drawer-item"
                :class="{ 'is-disabled': updatingFromOrderDaily }"
                @click="!updatingFromOrderDaily && onOthersDrawerSelect('update-order')"
              >
                <el-icon><Refresh /></el-icon>
                <span>受注データ更新</span>
              </div>
              <div class="others-drawer-item" @click="onOthersDrawerSelect('batch-initial')">
                <el-icon><DocumentCopy /></el-icon>
                <span>初期在庫一括登録</span>
              </div>
              <div
                class="others-drawer-item"
                :class="{ 'is-disabled': generating || updatingCarryOver || updatingOrder || updatingAll }"
                @click="!(generating || updatingCarryOver || updatingOrder || updatingAll) && onOthersDrawerSelect('carry-over')"
              >
                <el-icon><RefreshRight /></el-icon>
                <span>繰越データ更新</span>
              </div>
              <div
                class="others-drawer-item"
                :class="{ 'is-disabled': generating || updatingCarryOver || updatingOrder || updatingAll }"
                @click="!(generating || updatingCarryOver || updatingOrder || updatingAll) && onOthersDrawerSelect('actual')"
              >
                <el-icon><Refresh /></el-icon>
                <span>実績データ更新</span>
              </div>
              <div
                class="others-drawer-item"
                :class="{ 'is-disabled': generating || updatingCarryOver || updatingOrder || updatingAll }"
                @click="!(generating || updatingCarryOver || updatingOrder || updatingAll) && onOthersDrawerSelect('defect')"
              >
                <el-icon><WarningFilled /></el-icon>
                <span>不良データ更新</span>
              </div>
              <div
                class="others-drawer-item"
                :class="{ 'is-disabled': generating || updatingCarryOver || updatingOrder || updatingAll }"
                @click="!(generating || updatingCarryOver || updatingOrder || updatingAll) && onOthersDrawerSelect('scrap')"
              >
                <el-icon><Delete /></el-icon>
                <span>廃棄データ更新</span>
              </div>
              <div
                class="others-drawer-item"
                :class="{ 'is-disabled': generating || updatingCarryOver || updatingOrder || updatingAll }"
                @click="!(generating || updatingCarryOver || updatingOrder || updatingAll) && onOthersDrawerSelect('on-hold')"
              >
                <el-icon><Clock /></el-icon>
                <span>保留データ更新</span>
              </div>
              <div
                class="others-drawer-item"
                :class="{ 'is-disabled': generating || updatingCarryOver || updatingOrder || updatingAll }"
                @click="!(generating || updatingCarryOver || updatingOrder || updatingAll) && onOthersDrawerSelect('production-dates')"
              >
                <el-icon><Calendar /></el-icon>
                <span>生産計画日更新</span>
              </div>
              <div
                class="others-drawer-item"
                :class="{ 'is-disabled': generating || updatingCarryOver || updatingOrder || updatingAll }"
                @click="!(generating || updatingCarryOver || updatingOrder || updatingAll) && onOthersDrawerSelect('plan')"
              >
                <el-icon><DocumentCopy /></el-icon>
                <span>計画データ更新</span>
              </div>
              <div
                class="others-drawer-item"
                :class="{ 'is-disabled': generating || updatingCarryOver || updatingOrder || updatingAll }"
                @click="!(generating || updatingCarryOver || updatingOrder || updatingAll) && onOthersDrawerSelect('inventory-trend')"
              >
                <el-icon><Refresh /></el-icon>
                <span>在庫・推移更新</span>
              </div>
              <div
                class="others-drawer-item"
                :class="{ 'is-disabled': generating || updatingCarryOver || updatingOrder || updatingAll || updatingProductMaster }"
                @click="!(generating || updatingCarryOver || updatingOrder || updatingAll || updatingProductMaster) && onOthersDrawerSelect('product-master')"
              >
                <el-icon><Goods /></el-icon>
                <span>製品マスタ更新</span>
              </div>
              <div
                class="others-drawer-item"
                :class="{ 'is-disabled': generating || updatingCarryOver || updatingOrder || updatingAll || updatingMachine }"
                @click="!(generating || updatingCarryOver || updatingOrder || updatingAll || updatingMachine) && onOthersDrawerSelect('machine')"
              >
                <el-icon><Monitor /></el-icon>
                <span>設備フィールド更新</span>
              </div>
              <div
                class="others-drawer-item"
                :class="{ 'is-disabled': generating || updatingCarryOver || updatingOrder || updatingAll }"
                @click="!(generating || updatingCarryOver || updatingOrder || updatingAll) && onOthersDrawerSelect('batch-actual')"
              >
                <el-icon><DocumentCopy /></el-icon>
                <span>実績一括登録</span>
              </div>
              <div class="others-drawer-item" @click="onOthersDrawerSelect('print-rec-plating')">
                <el-icon><Printer /></el-icon>
                <span>メッキ推奨生産日（印刷）</span>
              </div>
              <div class="others-drawer-item" @click="onOthersDrawerSelect('print-rec-molding')">
                <el-icon><Printer /></el-icon>
                <span>成型推奨生産日（印刷）</span>
              </div>
              <div class="others-drawer-item" @click="onOthersDrawerSelect('print-rec-molding-plan')">
                <el-icon><Printer /></el-icon>
                <span>成型計画推奨生産日（印刷）</span>
              </div>
            </div>
          </el-drawer>
        </template>
        <el-button
          size="small"
          :icon="Refresh"
          @click="handleRefresh"
          :loading="loading"
          class="modern-btn refresh-btn"
        >
          <span>再取得</span>
        </el-button>
        <el-button
          size="small"
          :icon="Printer"
          @click="handlePrint"
          class="modern-btn print-btn"
        >
          <span>印刷</span>
        </el-button>
        <el-button
          size="small"
          :icon="Printer"
          @click="handleProcessPrint"
          class="modern-btn process-print-btn-primary"
        >
          <span>工程別計画確認印刷</span>
        </el-button>
        <el-dropdown
          trigger="click"
          placement="bottom-start"
          class="recommended-print-dropdown"
          @command="handleRecommendedPrintCommand"
        >
          <el-button size="small" :icon="Printer" class="modern-btn recommended-print-dropdown-btn">
            <span>推奨生産日印刷</span>
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="print-rec-plating">メッキ推奨生産日</el-dropdown-item>
              <el-dropdown-item command="print-rec-molding">成型推奨生産日</el-dropdown-item>
              <el-dropdown-item command="print-rec-molding-plan">成型計画推奨生産日</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-dropdown
          trigger="click"
          placement="bottom-start"
          class="production-plan-dropdown"
          @command="handleProductionPlanCommand"
        >
          <el-button size="small" :icon="DocumentAdd" class="modern-btn production-plan-dropdown-btn">
            <span>生産計画印刷</span>
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="molding-plan-create">成型計画作成</el-dropdown-item>
              <el-dropdown-item command="welding-plan-create" disabled>溶接計画作成</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button
          size="small"
          :icon="Setting"
          @click="showColumnSettings = true"
          class="modern-btn settings-btn"
        >
          <span>列設定</span>
        </el-button>
      </div>
      </div>
    </div>
    <el-card class="table-card" shadow="hover">
      <template #header>
        <div class="filter-section">
          <div class="filter-item date-filter-item">
            <label class="filter-label">期間</label>
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="～"
              start-placeholder="開始日"
              end-placeholder="終了日"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              :shortcuts="datePickerShortcuts"
              :locale="jaLocale"
              size="small"
              class="filter-date-picker"
              @change="handleFilterChange"
            />
          </div>
          <div class="filter-item date-quick-item">
            <div class="date-quick-buttons">
              <el-button size="small" plain @click="shiftDateRange(-1)">前日</el-button>
              <el-button size="small" type="primary" plain @click="setTodayRange">今日</el-button>
              <el-button size="small" plain @click="shiftDateRange(1)">翌日</el-button>
            </div>
          </div>
          <div class="filter-item">
            <label class="filter-label">製品</label>
            <el-select
              v-model="filterProductCd"
              placeholder="製品名を選択"
              size="small"
              clearable
              filterable
              class="filter-select"
              @change="handleFilterChange"
              @clear="handleFilterChange"
            >
              <el-option
                v-for="product in productList"
                :key="product.product_cd"
                :label="`${product.product_cd} - ${product.product_name || ''}`"
                :value="product.product_cd"
              />
            </el-select>
          </div>
          <div class="filter-item keyword-filter-item">
            <label class="filter-label">検索</label>
            <el-input
              v-model="filterKeyword"
              placeholder="製品名キーワード"
              size="small"
              clearable
              class="filter-input keyword-filter-input"
              :prefix-icon="Search"
              @input="handleKeywordInput"
              @keyup.enter="handleFilterChange"
              @clear="handleKeywordClear"
            />
          </div>
        </div>
      </template>

      <el-tabs v-model="activeTableTab" type="card" class="summary-table-tabs" :stretch="true">
              <el-tab-pane v-for="tab in tableTabs" :key="tab.key" :name="tab.key">
                <template #label>
                  <span class="tab-text">{{ tab.label }}</span>
                </template>
        </el-tab-pane>
      </el-tabs>

      <el-table
            :data="tableData"
            v-loading="loading"
            stripe
            border
            class="modern-table"
            :default-sort="{ prop: 'product_name', order: 'ascending' }"
            :height="'calc(72vh - 60px)'"
            @sort-change="handleSortChange"
            @cell-dblclick="handleCellDoubleClick"
            :cell-style="cellStyleHandler"
            :header-cell-style="headerCellStyle"
            size="small"
            show-summary
            :summary-method="getSummaries"
          >
            <el-table-column
              v-if="activeTableTab === 'custom' && visibleColumns.id"
              prop="id"
              label="ID"
              :width="columnDefinitions.id?.width ?? 80"
              fixed="left"
              align="center"
            />
            <el-table-column
              v-if="activeTableTab === 'custom' ? visibleColumns.date : true"
              prop="date"
              label="日付"
              :width="columnDefinitions.date?.width ?? 90"
              fixed="left"
              align="center"
              sortable="custom"
              :sort-orders="['ascending', 'descending']"
            >
              <template #default="{ row }">
                <div class="date-cell">{{ formatDate(row.date) }}</div>
              </template>
            </el-table-column>
            <el-table-column
              v-if="activeTableTab === 'custom' && visibleColumns.day_of_week"
              prop="day_of_week"
              label="曜日"
              :width="columnDefinitions.day_of_week?.width ?? 60"
              fixed="left"
              align="center"
            >
              <template #default="{ row }">
                <el-tag size="small" :type="getWeekdayType(row.day_of_week)">
                  {{ row.day_of_week }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column
              v-if="activeTableTab === 'custom' && visibleColumns.route_cd"
              prop="route_cd"
              label="工程グループ"
              :width="columnDefinitions.route_cd?.width ?? 120"
              fixed="left"
              align="center"
            />
            <el-table-column
              v-if="activeTableTab === 'custom' && visibleColumns.product_cd"
              prop="product_cd"
              label="製品CD"
              :width="columnDefinitions.product_cd?.width ?? 90"
              fixed="left"
              align="center"
            />
            <el-table-column
              v-if="activeTableTab === 'custom' ? visibleColumns.product_name : true"
              prop="product_name"
              label="製品名"
              :width="columnDefinitions.product_name?.width ?? 110"
              fixed="left"
              show-overflow-tooltip
              sortable="custom"
              :sort-orders="['ascending', 'descending']"
            >
              <template #default="{ row }">
                <span class="product-name-cell">{{ row.product_name }}</span>
              </template>
            </el-table-column>
            <el-table-column
              v-if="activeTableTab === 'custom' && visibleColumns.order_quantity"
              prop="order_quantity"
              label="受注数"
              :width="columnDefinitions.order_quantity?.width ?? 70"
              align="center"
            >
              <template #default="{ row }">
                <span class="number-cell">{{
                  row.order_quantity != null && row.order_quantity !== 0
                    ? Number(row.order_quantity).toLocaleString()
                    : ''
                }}</span>
              </template>
            </el-table-column>
            <el-table-column
              v-if="activeTableTab === 'custom' && visibleColumns.forecast_quantity"
              prop="forecast_quantity"
              label="内示数"
              :width="columnDefinitions.forecast_quantity?.width ?? 70"
              align="center"
            >
              <template #default="{ row }">
                <span class="number-cell">{{
                  row.forecast_quantity != null && row.forecast_quantity !== 0
                    ? Number(row.forecast_quantity).toLocaleString()
                    : ''
                }}</span>
              </template>
            </el-table-column>
            <el-table-column
              v-if="activeTableTab === 'custom' && visibleColumns.safety_stock"
              prop="safety_stock"
              label="安全在庫"
              :width="columnDefinitions.safety_stock?.width ?? 90"
              align="center"
            >
              <template #default="{ row }">
                <span class="number-cell">{{
                  row.safety_stock != null && row.safety_stock !== 0
                    ? Number(row.safety_stock).toLocaleString()
                    : ''
                }}</span>
              </template>
            </el-table-column>
            <template v-for="col in dynamicColumns" :key="col.prop">
              <el-table-column
                v-if="activeTableTab === 'custom' ? visibleColumns[col.prop] : true"
                :prop="col.prop"
                :label="col.label"
                :width="col.width || 90"
                align="center"
              >
                <template #default="{ row }">
                  <span v-if="col.type === 'date'" class="date-text">
                    {{ row[col.prop] ? formatDate(row[col.prop]) : '-' }}
                  </span>
                  <span v-else-if="col.type === 'text'" class="text-cell">
                    {{
                      col.prop === 'pre_plating_prev_process' || col.prop === 'pre_molding_prev_process'
                        ? formatPrePlatingPrevKey(row[col.prop])
                        : (row[col.prop] || '-')
                    }}
                  </span>
                  <span
                    v-else
                    class="number-cell"
                    :class="{
                      negative:
                        col.prop !== 'pre_plating_inventory' &&
                        col.prop !== 'pre_molding_inventory' &&
                        (row[col.prop] ?? 0) < 0,
                      positive:
                        col.prop !== 'pre_plating_inventory' &&
                        col.prop !== 'pre_molding_inventory' &&
                        (row[col.prop] ?? 0) > 0,
                    }"
                  >
                    <template
                      v-if="
                        (col.prop === 'pre_plating_inventory' && row.pre_plating_inventory == null) ||
                        (col.prop === 'pre_molding_inventory' && row.pre_molding_inventory == null)
                      "
                    >
                      —
                    </template>
                    <template v-else>{{
                      row[col.prop] != null && row[col.prop] !== 0 ? Number(row[col.prop]).toLocaleString() : ''
                    }}</template>
                  </span>
                </template>
              </el-table-column>
            </template>
          </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="handlePageChange"
          class="pagination-compact"
        />
      </div>
    </el-card>

    <!-- データ生成確認ダイアログ -->
    <el-dialog
      v-model="showGenerateConfirmDialog"
      title="データ生成確認"
      width="550px"
      class="generate-confirm-dialog"
      :close-on-click-modal="false"
    >
      <div class="generate-confirm-content">
        <div class="confirm-icon-wrapper">
          <el-icon class="confirm-icon"><InfoFilled /></el-icon>
        </div>
        <div class="confirm-info">
          <h3 class="confirm-title">データ生成を実行しますか？</h3>
          <div class="confirm-details">
            <div class="detail-row">
              <span class="detail-label">期間:</span>
              <span class="detail-value highlight">{{ generateDateRange.start }} ～ {{ generateDateRange.end }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">説明:</span>
              <span class="detail-value">既存のデータはスキップされます</span>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showGenerateConfirmDialog = false" class="cancel-btn">キャンセル</el-button>
          <el-button type="primary" @click="confirmGenerateData" class="confirm-btn">生成開始</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 計画データ更新確認ダイアログ -->
    <el-dialog
      v-model="showPlanConfirmDialog"
      title="計画データ更新確認"
      width="550px"
      class="plan-confirm-dialog"
      :close-on-click-modal="false"
    >
      <div class="generate-confirm-content">
        <div class="confirm-icon-wrapper">
          <el-icon class="confirm-icon"><InfoFilled /></el-icon>
        </div>
        <div class="confirm-info">
          <h3 class="confirm-title">計画データを更新しますか？</h3>
          <div class="confirm-details">
            <div class="detail-row">
              <span class="detail-value">当月月初～+3ヶ月の plan 列をいったんクリアしたうえで、production_plan_updates の集計を production_summarys の plan 列に反映し、actual_plan を更新します。続けて、該当範囲の sw_plan・chamfering_plan・cutting_plan をいったんクリアし、ルートに切断工程(KT01)がある行のみ cutting_plan、面取工程(KT02)がある行のみ chamfering_plan、product_machine_config に sw_machine が設定されている製品のみ sw_plan を molding_actual_plan で更新します。</span>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showPlanConfirmDialog = false" class="cancel-btn">キャンセル</el-button>
          <el-button type="primary" @click="confirmUpdatePlan" class="confirm-btn">更新</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 在庫取引ログ入力（表格双击） -->
    <el-dialog
      v-model="showTransactionInputDialog"
      title="在庫取引ログ入力"
      width="580px"
      class="transaction-log-dialog"
      :close-on-click-modal="false"
      @close="showTransactionInputDialog = false"
    >
      <div v-if="transactionInputInfo.date" class="transaction-input-info">
        <div class="transaction-info-grid">
          <div class="transaction-info-item">
            <div class="transaction-info-label">日付</div>
            <div class="transaction-info-value">{{ transactionInputInfo.date }}</div>
          </div>
          <div class="transaction-info-item">
            <div class="transaction-info-label">製品CD</div>
            <div class="transaction-info-value">{{ transactionInputInfo.productCd }}</div>
          </div>
          <div class="transaction-info-item">
            <div class="transaction-info-label">製品名</div>
            <div class="transaction-info-value">{{ transactionInputInfo.productName }}</div>
          </div>
          <div class="transaction-info-item">
            <div class="transaction-info-label">工程</div>
            <div class="transaction-info-value">{{ transactionInputInfo.processName }} ({{ transactionInputInfo.processCd }})</div>
          </div>
        </div>
      </div>
      <div class="transaction-panels">
        <template v-if="transactionInputInfo.processCd === 'KT13'">
          <div class="transaction-panel transaction-panel--green">
            <div class="transaction-panel-head">
              <el-icon class="transaction-panel-icon"><CircleCheck /></el-icon>
              <span class="transaction-panel-label">入庫</span>
            </div>
            <el-input-number v-model="transactionForm.inbound" :min="0" :precision="0" placeholder="数量を入力" class="transaction-panel-input" />
          </div>
          <div class="transaction-panel transaction-panel--orange">
            <div class="transaction-panel-head">
              <el-icon class="transaction-panel-icon"><WarningFilled /></el-icon>
              <span class="transaction-panel-label">出庫</span>
            </div>
            <el-input-number v-model="transactionForm.outbound" :min="0" :precision="0" placeholder="数量を入力" class="transaction-panel-input" />
          </div>
          <div class="transaction-panel transaction-panel--red">
            <div class="transaction-panel-head">
              <el-icon class="transaction-panel-icon"><Delete /></el-icon>
              <span class="transaction-panel-label">廃棄</span>
            </div>
            <el-input-number v-model="transactionForm.scrap" :min="0" :precision="0" placeholder="数量を入力" class="transaction-panel-input" />
          </div>
          <div class="transaction-panel transaction-panel--blue">
            <div class="transaction-panel-head">
              <el-icon class="transaction-panel-icon"><Clock /></el-icon>
              <span class="transaction-panel-label">保留</span>
            </div>
            <el-input-number v-model="transactionForm.onHold" :min="0" :precision="0" placeholder="数量を入力" class="transaction-panel-input" />
          </div>
        </template>
        <template v-else-if="transactionInputInfo.processCd === 'KT15'">
          <div class="transaction-panel transaction-panel--green">
            <div class="transaction-panel-head">
              <el-icon class="transaction-panel-icon"><CircleCheck /></el-icon>
              <span class="transaction-panel-label">入庫</span>
            </div>
            <el-input-number v-model="transactionForm.actual" :precision="0" placeholder="数量を入力（負数可）" class="transaction-panel-input" />
          </div>
          <div class="transaction-panel transaction-panel--red">
            <div class="transaction-panel-head">
              <el-icon class="transaction-panel-icon"><Delete /></el-icon>
              <span class="transaction-panel-label">廃棄</span>
            </div>
            <el-input-number v-model="transactionForm.scrap" :min="0" :precision="0" placeholder="数量を入力" class="transaction-panel-input" />
          </div>
          <div class="transaction-panel transaction-panel--empty"></div>
          <div class="transaction-panel transaction-panel--empty"></div>
        </template>
        <template v-else>
          <div class="transaction-panel transaction-panel--green">
            <div class="transaction-panel-head">
              <el-icon class="transaction-panel-icon"><CircleCheck /></el-icon>
              <span class="transaction-panel-label">実績</span>
            </div>
            <el-input-number v-model="transactionForm.actual" :precision="0" placeholder="数量を入力（負数可）" class="transaction-panel-input" />
          </div>
          <div class="transaction-panel transaction-panel--orange">
            <div class="transaction-panel-head">
              <el-icon class="transaction-panel-icon"><WarningFilled /></el-icon>
              <span class="transaction-panel-label">不良</span>
            </div>
            <el-input-number v-model="transactionForm.defect" :min="0" :precision="0" placeholder="数量を入力" class="transaction-panel-input" />
          </div>
          <div class="transaction-panel transaction-panel--red">
            <div class="transaction-panel-head">
              <el-icon class="transaction-panel-icon"><Delete /></el-icon>
              <span class="transaction-panel-label">廃棄</span>
            </div>
            <el-input-number v-model="transactionForm.scrap" :min="0" :precision="0" placeholder="数量を入力" class="transaction-panel-input" />
          </div>
          <div class="transaction-panel transaction-panel--blue">
            <div class="transaction-panel-head">
              <el-icon class="transaction-panel-icon"><Clock /></el-icon>
              <span class="transaction-panel-label">保留</span>
            </div>
            <el-input-number v-model="transactionForm.onHold" :min="0" :precision="0" placeholder="数量を入力" class="transaction-panel-input" />
          </div>
        </template>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showTransactionInputDialog = false">キャンセル</el-button>
          <el-button type="primary" :loading="submittingTransaction" @click="handleSubmitTransaction">登録</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 在庫・推移更新確認ダイアログ -->
    <el-dialog
      v-model="showInventoryTrendUpdateConfirmDialog"
      title="在庫・推移更新確認"
      width="550px"
      class="inventory-trend-confirm-dialog"
      :close-on-click-modal="false"
    >
      <div class="generate-confirm-content">
        <div class="confirm-icon-wrapper">
          <el-icon class="confirm-icon"><InfoFilled /></el-icon>
        </div>
        <div class="confirm-info">
          <h3 class="confirm-title">在庫・推移を更新しますか？</h3>
          <div class="confirm-details">
            <div class="detail-row">
              <span class="detail-value">当月月初から先の在庫・推移・安全在庫フィールドをクリアしてから、在庫→推移→安全在庫の順で再計算します（在庫は当月月初～+3ヶ月、推移は当月月初～表末。安全在庫は製品マスタの安全在庫日数×将来30営業日の平均内示数）。</span>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showInventoryTrendUpdateConfirmDialog = false" class="cancel-btn">キャンセル</el-button>
          <el-button type="primary" @click="confirmInventoryTrendUpdate" class="confirm-btn">更新</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 製品マスタ更新ダイアログ -->
    <el-dialog
      v-model="showProductMasterUpdateDialog"
      title="製品マスタ更新"
      width="550px"
      class="product-master-update-dialog"
      :close-on-click-modal="false"
    >
      <div class="generate-confirm-content">
        <div class="confirm-icon-wrapper">
          <el-icon class="confirm-icon"><InfoFilled /></el-icon>
        </div>
        <div class="confirm-info">
          <h3 class="confirm-title">製品マスタを更新しますか？</h3>
          <div class="confirm-details">
            <div class="detail-row">
              <span class="detail-label">更新期間</span>
            </div>
            <div class="detail-row" style="margin-top: 8px;">
              <el-date-picker
                v-model="productMasterDateRange"
                type="daterange"
                range-separator="～"
                start-placeholder="開始日"
                end-placeholder="終了日"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                style="width: 100%;"
              />
            </div>
            <div class="detail-row" style="margin-top: 8px;">
              <span class="detail-value">products の route_cd, product_name を production_summarys に同期します。</span>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showProductMasterUpdateDialog = false" class="cancel-btn">キャンセル</el-button>
          <el-button type="primary" @click="confirmUpdateProductMaster" class="confirm-btn">更新</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 設備フィールド更新ダイアログ -->
    <el-dialog
      v-model="showMachineUpdateDialog"
      title="設備フィールド更新"
      width="550px"
      class="machine-update-dialog"
      :close-on-click-modal="false"
    >
      <div class="generate-confirm-content">
        <div class="confirm-icon-wrapper">
          <el-icon class="confirm-icon"><InfoFilled /></el-icon>
        </div>
        <div class="confirm-info">
          <h3 class="confirm-title">機器フィールドを更新しますか？</h3>
          <div class="confirm-details">
            <div class="detail-row">
              <span class="detail-label">更新期間</span>
            </div>
            <div class="detail-row" style="margin-top: 8px;">
              <el-date-picker
                v-model="machineDateRange"
                type="daterange"
                range-separator="～"
                start-placeholder="開始日"
                end-placeholder="終了日"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                style="width: 100%;"
              />
            </div>
            <div class="detail-row" style="margin-top: 8px;">
              <span class="detail-value">product_machine_config と machines から production_summarys の各工程設備名を同期します。sw機は product_machine_config の sw_machine（機器CD）を machines の machine_name（例：面取07）に変換して反映します。</span>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showMachineUpdateDialog = false" class="cancel-btn">キャンセル</el-button>
          <el-button type="primary" @click="confirmUpdateMachine" class="confirm-btn">更新</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 全部一括更新確認ダイアログ -->
    <el-dialog
      v-model="showAllUpdateConfirmDialog"
      title="全部一括更新確認"
      width="520px"
      class="all-update-confirm-dialog"
      :close-on-click-modal="false"
    >
      <div class="generate-confirm-content">
        <div class="confirm-icon-wrapper">
          <el-icon class="confirm-icon"><InfoFilled /></el-icon>
        </div>
        <div class="confirm-info">
          <h3 class="confirm-title">以下の順で一括更新します</h3>
          <div class="confirm-details">
            <ol class="all-update-steps-list">
              <li>受注データ更新</li>
              <li>実績データ更新</li>
              <li>不良データ更新</li>
              <li>廃棄データ更新</li>
              <li>保留データ更新</li>
              <li>計画データ更新</li>
              <li>在庫・推移・安全在庫更新</li>
            </ol>
            <div class="detail-row" style="margin-top: 10px;">
              <span class="detail-value">この処理には時間がかかる場合があります。</span>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showAllUpdateConfirmDialog = false" class="cancel-btn">キャンセル</el-button>
          <!-- 本番ビルドで teleport 内の el-button @click が効かないため、原生 button で実行 -->
          <button type="button" class="el-button el-button--primary confirm-btn" @click="onAllUpdateConfirmClick">
            一括更新開始
          </button>
        </div>
      </template>
    </el-dialog>

    <!-- 工程別計画確認印刷 - 対象日選択 -->
    <el-dialog
      v-model="showPrintDateDialog"
      title="工程別計画確認印刷 - 対象日選択"
      width="420px"
      class="process-print-date-dialog"
      :close-on-click-modal="false"
    >
      <div class="generate-confirm-content">
        <p class="detail-value" style="margin-bottom: 12px;">印刷対象の日付を選択してください。</p>
        <el-date-picker
          v-model="printTargetDate"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="日付を選択"
          style="width: 100%;"
        />
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showPrintDateDialog = false">キャンセル</el-button>
          <el-button type="primary" :disabled="!printTargetDate" @click="handleConfirmPrintDate">印刷</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 成型計画作成ダイアログ -->
    <el-dialog
      v-model="showMoldingPlanDialog"
      width="1100px"
      :close-on-click-modal="false"
      destroy-on-close
      class="molding-plan-dialog"
      align-center
    >
      <template #header>
        <div class="molding-plan-dlg-header">
          <div class="molding-plan-dlg-header__mark" aria-hidden="true">
            <el-icon><DocumentAdd /></el-icon>
          </div>
          <div class="molding-plan-dlg-header__meta">
            <span class="molding-plan-dlg-header__title">成型計画作成</span>
            <span class="molding-plan-dlg-header__sub">条件入力・計画クリア・計算結果</span>
          </div>
        </div>
      </template>
      <div class="molding-plan-inner">
        <div class="molding-plan-panel">
          <div class="molding-plan-panel__title">条件</div>
          <el-form
            :inline="true"
            label-position="right"
            label-width="90px"
            size="small"
            class="molding-plan-form-grid molding-plan-form-grid--cond-row"
          >
            <el-form-item label="生産計画月">
              <el-date-picker
                v-model="moldingPlanMonth"
                type="month"
                format="YYYY-MM"
                value-format="YYYY-MM"
                placeholder="月選択"
                class="molding-plan-field--month"
                :style="moldingPlanMonthPickerStyle"
                @change="onMoldingPlanMonthChange"
              />
            </el-form-item>
            <el-form-item label="基準日">
              <el-date-picker
                v-model="moldingPlanBaseDate"
                type="date"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                placeholder="翌月1日"
                class="molding-plan-field--base"
                :style="moldingPlanBaseDatePickerStyle"
              />
            </el-form-item>
            <el-form-item label="稼働日">
              <el-input-number
                v-model="moldingPlanWorkingDays"
                :min="1"
                :max="31"
                controls-position="right"
                class="molding-plan-field molding-plan-field--num"
              />
            </el-form-item>
            <el-form-item label="加工減耗係数">
              <el-input-number
                v-model="moldingPlanCoefficient"
                :min="1"
                :max="2"
                :step="0.001"
                :precision="3"
                controls-position="right"
                class="molding-plan-field molding-plan-field--coef"
              />
            </el-form-item>
          </el-form>
          <div class="molding-plan-actions">
            <el-button class="molding-plan-btn molding-plan-btn--secondary" @click="openMoldingMachineConfigDialog">
              <el-icon><Monitor /></el-icon>
              <span>成型機器設定</span>
            </el-button>
            <el-button class="molding-plan-btn molding-plan-btn--secondary" @click="openMoldingBomDialog">
              <el-icon><Setting /></el-icon>
              <span>製品工程BOM</span>
            </el-button>
            <el-button
              class="molding-plan-btn molding-plan-btn--primary"
              :loading="moldingPlanLoading"
              @click="executeMoldingPlanCreate"
            >
              <el-icon><DocumentAdd /></el-icon>
              <span>成型計画作成</span>
            </el-button>
          </div>
          <div class="molding-plan-clear-panel">
            <div class="molding-plan-panel__title molding-plan-panel__title--sub">計画クリア</div>
            <p class="molding-plan-clear-hint">
              指定日以降の生産サマリーで molding_plan / molding_actual_plan を 0 にクリアします。
            </p>
            <div class="molding-plan-clear-row">
              <el-form :inline="true" label-position="right" label-width="120px" size="small" class="molding-plan-form-grid molding-plan-form-grid--tight">
                <el-form-item label="計画クリア開始日">
                  <el-date-picker
                    v-model="moldingPlanClearFromDate"
                    type="date"
                    format="YYYY-MM-DD"
                    value-format="YYYY-MM-DD"
                    placeholder="開始日を選択"
                    class="molding-plan-field molding-plan-field--wide"
                  />
                </el-form-item>
              </el-form>
              <el-button
                class="molding-plan-btn molding-plan-btn--warn"
                :loading="moldingPlanClearLoading"
                :disabled="!moldingPlanClearFromDate"
                @click="executeMoldingPlanClear"
              >
                <el-icon><Delete /></el-icon>
                <span>計画クリア実行</span>
              </el-button>
              <el-button
                class="molding-plan-btn molding-plan-btn--sync"
                :loading="moldingPlanInventoryTrendLoading"
                :disabled="moldingPlanClearLoading || moldingPlanInventoryTrendLoading || updatingInventoryTrend"
                @click="executeMoldingPlanInventoryTrend"
              >
                <el-icon><Refresh /></el-icon>
                <span>在庫・推移更新</span>
              </el-button>
            </div>
            <p class="molding-plan-clear-hint molding-plan-clear-hint--sub">
              在庫・推移は当月月初基準（メニューと同じ）。計画クリア開始日とは連動しません。
            </p>
          </div>
        </div>

        <div v-if="moldingPlanResult.length" class="molding-plan-result-panel">
          <div class="molding-plan-result__head">
            <div class="molding-plan-result__head-left">
              <span class="molding-plan-result__title">計算結果</span>
              <el-tag type="primary" size="small" effect="light" round class="molding-plan-result__tag">
                {{ moldingPlanResult.length }} 件
              </el-tag>
            </div>
            <el-button
              size="small"
              type="primary"
              plain
              class="molding-plan-result__print"
              @click="printMoldingPlanResult"
            >
              <el-icon><Printer /></el-icon>
              印刷
            </el-button>
          </div>
          <el-table
            :data="moldingPlanResult"
            border
            stripe
            size="small"
            max-height="460"
            class="molding-plan-table"
            :default-sort="{ prop: 'molding_machine', order: 'ascending' }"
            highlight-current-row
          >
            <el-table-column prop="lookup_date" label="対応日" width="112" align="center" sortable />
            <el-table-column
              prop="molding_machine"
              label="成型機"
              min-width="120"
              align="center"
              sortable
              show-overflow-tooltip
            />
            <el-table-column prop="product_name" label="製品名" min-width="168" show-overflow-tooltip />
            <el-table-column prop="product_cd" label="製品CD" width="104" align="center" sortable />
            <el-table-column prop="trend_raw" label="実計推移" width="100" align="right" sortable>
              <template #default="{ row }">
                <span :class="{ 'molding-plan-num--neg': row.trend_raw < 0 }">{{ row.trend_raw }}</span>
              </template>
            </el-table-column>
            <el-table-column label="必要数" width="104" align="right" sortable>
              <template #default="{ row }">{{ formatMoldingPlanInt(row.required_qty) }}</template>
            </el-table-column>
            <el-table-column label="ロットサイズ" width="112" align="right" sortable>
              <template #default="{ row }">{{ formatMoldingPlanInt(row.lot_size) }}</template>
            </el-table-column>
            <el-table-column prop="lot_count" label="ロット数" width="92" align="right" sortable />
            <el-table-column label="計画数" width="108" align="right" sortable>
              <template #default="{ row }">
                <span class="molding-plan-batch">{{ formatMoldingPlanInt(row.batch_qty) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="日当り" width="96" align="right" sortable>
              <template #default="{ row }">{{ formatMoldingPlanInt(row.daily_qty) }}</template>
            </el-table-column>
          </el-table>
        </div>
      </div>
      <template #footer>
        <div class="molding-plan-footer">
          <el-button class="molding-plan-btn molding-plan-btn--close" @click="showMoldingPlanDialog = false">閉じる</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 成型機器設定（product_machine_config：成型機のみ） -->
    <el-dialog
      v-model="showMoldingMachineConfigDialog"
      width="720px"
      align-center
      class="molding-machine-config-dialog"
      destroy-on-close
      :close-on-click-modal="false"
    >
      <template #header>
        <div class="molding-machine-config-dlg-header">
          <div class="molding-machine-config-dlg-header__mark" aria-hidden="true">
            <el-icon><Monitor /></el-icon>
          </div>
          <div class="molding-machine-config-dlg-header__meta">
            <span class="molding-machine-config-dlg-header__eyebrow">product_machine_config</span>
            <span class="molding-machine-config-dlg-header__title">成型機器設定</span>
            <span class="molding-machine-config-dlg-header__sub">成型機を変更すると自動保存されます</span>
          </div>
        </div>
      </template>
      <div v-loading="moldingMachineConfigLoading" class="molding-machine-config-body">
        <el-table
          :data="moldingMachineConfigRows"
          border
          stripe
          size="small"
          max-height="480"
          class="molding-machine-config-table"
          :default-sort="{ prop: 'product_name', order: 'ascending' }"
          empty-text="データがありません"
        >
          <el-table-column prop="product_cd" label="製品CD" width="112" align="center" sortable />
          <el-table-column prop="product_name" label="製品名" min-width="160" sortable show-overflow-tooltip />
          <el-table-column label="成型機" min-width="220" align="left">
            <template #default="{ row }">
              <el-select
                :model-value="row.molding_machine ?? ''"
                filterable
                clearable
                placeholder="成型機を選択"
                class="molding-machine-config-select"
                :loading="moldingMachineConfigSavingId === row.id"
                @update:model-value="(v) => onMoldingMachineConfigUpdate(row, v)"
              >
                <el-option
                  v-for="opt in moldingMachineSelectOptionsWithLegacy"
                  :key="opt.value"
                  :label="opt.label"
                  :value="opt.value"
                />
              </el-select>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button class="molding-plan-btn molding-plan-btn--close" @click="showMoldingMachineConfigDialog = false">
          閉じる
        </el-button>
      </template>
    </el-dialog>

    <!-- 成型計画作成：製品工程BOM（簡易編集） -->
    <el-dialog
      v-model="showMoldingBomDialog"
      width="680px"
      align-center
      class="molding-bom-compact-dialog"
      destroy-on-close
      :close-on-click-modal="false"
      @closed="clearMoldingBomSaveTimers"
    >
      <template #header>
        <div class="molding-bom-dlg-header">
          <div class="molding-bom-dlg-header__mark" aria-hidden="true">
            <el-icon><Setting /></el-icon>
          </div>
          <div class="molding-bom-dlg-header__meta">
            <span class="molding-bom-dlg-header__eyebrow">product_process_bom</span>
            <span class="molding-bom-dlg-header__title">製品工程BOM</span>
            <span class="molding-bom-dlg-header__sub">安全在庫日数・成型リードタイム</span>
          </div>
        </div>
      </template>
      <div v-loading="moldingBomLoading" class="molding-bom-dialog-body">
        <div class="molding-bom-panel">
          <p class="molding-bom-dialog-hint">
            セルを編集すると自動保存されます。対象フィールドを選んで +1 / -1 で一括更新できます。
          </p>
          <div class="molding-bom-bulk-bar">
            <span class="molding-bom-bulk-bar__label">一括対象</span>
            <el-select
              v-model="moldingBomBulkField"
              size="small"
              class="molding-bom-bulk-field-select"
              :teleported="false"
            >
              <el-option label="安全在庫日数" value="safety" />
              <el-option label="成型LT" value="forming" />
              <el-option label="両方" value="both" />
            </el-select>
            <el-button
              size="small"
              type="primary"
              plain
              :loading="moldingBomBulkLoading"
              :disabled="moldingBomBulkLoading"
              @click="applyMoldingBomBulkDelta(1)"
            >
              選択行 +1
            </el-button>
            <el-button
              size="small"
              type="warning"
              plain
              :loading="moldingBomBulkLoading"
              :disabled="moldingBomBulkLoading"
              @click="applyMoldingBomBulkDelta(-1)"
            >
              選択行 -1
            </el-button>
          </div>
          <div class="molding-bom-table-wrap">
            <el-table
              ref="moldingBomTableRef"
              :data="moldingBomList"
              border
              stripe
              size="small"
              max-height="400"
              row-key="product_cd"
              class="molding-bom-table"
              highlight-current-row
              :default-sort="{ prop: 'product_name', order: 'ascending' }"
            >
              <el-table-column type="selection" width="46" align="center" fixed />
              <el-table-column prop="product_cd" label="製品CD" width="96" align="center" fixed />
              <el-table-column prop="product_name" label="製品名" min-width="200" sortable show-overflow-tooltip />
              <el-table-column label="安全在庫日数" width="132" align="center">
                <template #default="{ row, $index }">
                  <div
                    class="molding-bom-nav-cell"
                    :data-row="$index"
                    data-col="0"
                    @keydown.capture="(e) => onMoldingBomInputKeydown(e, $index, 0)"
                  >
                    <el-input-number
                      v-model="row.safety_stock_days"
                      :min="0"
                      :max="9999"
                      :controls="false"
                      size="small"
                      class="molding-bom-input-num"
                      @change="onMoldingBomFieldChange(row)"
                    />
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="成型LT" width="116" align="center">
                <template #default="{ row, $index }">
                  <div
                    class="molding-bom-nav-cell"
                    :data-row="$index"
                    data-col="1"
                    @keydown.capture="(e) => onMoldingBomInputKeydown(e, $index, 1)"
                  >
                    <el-input-number
                      v-model="row.forming_process_lt"
                      :min="0"
                      :max="9999"
                      :controls="false"
                      size="small"
                      class="molding-bom-input-num"
                      @change="onMoldingBomFieldChange(row)"
                    />
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="molding-bom-footer">
          <el-button type="primary" plain round @click="showMoldingBomDialog = false">閉じる</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- データ生成・一括更新進度ダイアログ（在庫不足管理と同様のスタイル） -->
    <el-dialog
      v-model="showProgressDialog"
      :title="progressDialogTitle"
      width="500px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
      class="progress-dialog progress-dialog--styled"
    >
      <div class="progress-content">
        <div class="progress-info">
          <div class="progress-icon-wrap">
            <el-icon class="progress-icon"><Loading /></el-icon>
          </div>
          <span class="progress-text">{{ progressText }}</span>
        </div>
        <div class="progress-track">
          <div
            class="progress-fill"
            :class="{ 'progress-fill--success': progressStatus === 'success' }"
            :style="{ width: Math.min(100, Math.round(progressPercentage)) + '%' }"
          >
            <span class="progress-shine" />
          </div>
        </div>
        <div class="progress-details">
          <span class="detail-label">進捗</span>
          <span class="detail-value progress-percent">{{ Math.round(progressPercentage) }}%</span>
        </div>
      </div>
    </el-dialog>

    <!-- 初期在庫一括登録ダイアログ -->
    <el-dialog
      v-model="showBatchInitialStockDialog"
      title="初期在庫一括登録"
      width="720px"
      class="batch-initial-stock-dialog"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <div class="batch-initial-filter">
        <div class="filter-row">
          <label class="filter-label">月（必須）</label>
          <el-date-picker
            v-model="batchInitialStockMonth"
            type="month"
            value-format="YYYY-MM"
            placeholder="月を選択"
            size="small"
            class="month-picker"
          />
        </div>
        <div class="filter-row">
          <label class="filter-label">工程（必須）</label>
          <el-select
            v-model="batchInitialStockProcessCd"
            placeholder="工程を選択"
            size="small"
            clearable
            filterable
            class="process-select"
          >
            <el-option
              v-for="p in processOptions"
              :key="p.cd"
              :label="`${p.cd} - ${p.name}`"
              :value="p.cd"
            />
          </el-select>
        </div>
        <div class="filter-actions">
          <el-button type="primary" size="small" :loading="batchInitialStockLoading" @click="handleBatchInitialStockSearch">
            検索
          </el-button>
          <el-button type="success" size="small" :loading="batchInitialStockSaving" :disabled="!batchInitialStockData.length" @click="handleSaveBatchInitialStock">
            一括保存
          </el-button>
        </div>
      </div>
      <div class="batch-initial-table-wrap">
        <el-table
          :data="batchInitialStockData"
          stripe
          border
          size="small"
          max-height="360"
          show-summary
          :summary-method="batchInitialStockSummaryMethod"
        >
          <el-table-column prop="product_cd" label="製品CD" width="100" align="center" />
          <el-table-column prop="product_name" label="製品名" min-width="140" show-overflow-tooltip />
          <el-table-column label="初期在庫数量" width="140" align="center">
            <template #default="{ row, $index }">
              <el-input-number
                :ref="(el: any) => setBatchQtyInputRef($index, el)"
                v-model="row.editQuantity"
                :min="0"
                :controls="true"
                size="small"
                class="qty-input"
                @keydown.enter.prevent="focusBatchInitialRow($index + 1)"
                @keydown.down.prevent="focusBatchInitialRow($index + 1)"
                @keydown.up.prevent="focusBatchInitialRow($index - 1)"
              />
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>

    <!-- 実績一括登録ダイアログ -->
    <el-dialog
      v-model="showBatchActualDialog"
      title="実績一括登録"
      width="780px"
      class="batch-actual-dialog"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <div class="batch-actual-filter">
        <div class="filter-row">
          <label class="filter-label">日付（必須）</label>
          <el-date-picker
            v-model="batchActualDate"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="日付を選択"
            size="small"
            style="width: 160px;"
            @change="handleBatchActualDateChange"
          />
        </div>
      </div>
      <div class="batch-actual-table-wrap">
        <el-table :data="batchActualTableData" stripe border size="small" max-height="320">
          <el-table-column label="製品" min-width="180">
            <template #default="{ row }">
              <el-select
                v-model="row.product_cd"
                placeholder="製品を選択"
                size="small"
                filterable
                clearable
                style="width: 100%;"
                @change="(val: string) => handleBatchActualProductChange(row, val)"
              >
                <el-option
                  v-for="p in productList"
                  :key="p.product_cd"
                  :label="p.product_name ? `${p.product_cd} - ${p.product_name}` : p.product_cd"
                  :value="p.product_cd"
                />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="日付" width="120" align="center">
            <template #default="{ row }">
              {{ row.date || batchActualDate || '—' }}
            </template>
          </el-table-column>
          <el-table-column label="切断実績" width="120" align="center">
            <template #default="{ row }">
              <el-input-number
                v-model="row.cuttingActual"
                :controls="true"
                size="small"
                style="width: 100%;"
              />
            </template>
          </el-table-column>
          <el-table-column label="面取実績" width="120" align="center">
            <template #default="{ row }">
              <el-input-number
                v-model="row.chamferingActual"
                :controls="true"
                size="small"
                style="width: 100%;"
              />
            </template>
          </el-table-column>
          <el-table-column label="成型実績" width="120" align="center">
            <template #default="{ row }">
              <el-input-number
                v-model="row.moldingActual"
                :controls="true"
                size="small"
                style="width: 100%;"
              />
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleResetBatchActual" class="cancel-btn">リセット</el-button>
          <el-button @click="showBatchActualDialog = false">キャンセル</el-button>
          <el-button type="primary" :loading="batchActualSaving" @click="handleSubmitBatchActual" class="confirm-btn">保存</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 列設定ダイアログ -->
    <el-dialog
      v-model="showColumnSettings"
      title="列表示設定"
      width="600px"
      class="column-settings-dialog"
      :close-on-click-modal="false"
    >
      <div class="column-settings-content">
        <div class="column-settings-actions">
          <el-button size="small" @click="selectAllColumns">すべて選択</el-button>
          <el-button size="small" @click="deselectAllColumns">すべて解除</el-button>
          <el-button size="small" @click="resetColumnSettings">デフォルトに戻す</el-button>
        </div>
        <div class="column-settings-hint">
          ※ 列表示設定は「受注」タブにのみ適用されます（他のタブは自動レイアウト）。
        </div>
        <div v-for="(columns, groupName) in groupedColumns" :key="groupName" class="column-group">
          <div class="group-header">{{ groupName }}</div>
          <div class="group-columns">
            <el-checkbox
              v-for="(column, key) in columns"
              :key="key"
              v-model="visibleColumns[key]"
              class="column-checkbox"
            >
              {{ column.label }}
            </el-checkbox>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showColumnSettings = false">キャンセル</el-button>
          <el-button type="primary" @click="saveColumnSettings">保存</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Search,
  Refresh,
  Setting,
  Printer,
  ArrowDown,
  DocumentAdd,
  InfoFilled,
  Loading,
  DocumentCopy,
  RefreshRight,
  WarningFilled,
  Delete,
  Clock,
  Calendar,
  Goods,
  Monitor,
  Operation,
  CircleCheck,
  DataBoard,
} from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import {
  getProductionSummarysList,
  getProductionSummarysProducts,
  generateProductionSummarys,
  updateProductionSummarysFromOrderDaily,
  acquireBatchUpdateLock,
  releaseBatchUpdateLock,
  clearProductionSummarysCarryOver,
  updateProductionSummarysCarryOver,
  updateProductionSummarysActual,
  updateProductionSummarysDefect,
  updateProductionSummarysScrap,
  updateProductionSummarysOnHold,
  updateProductionSummarysProductionDates,
  clearProductionSummarysCalculatedFields,
  clearProductionSummarysPlanFields,
  clearProductionSummarysMoldingPlan,
  updateProductionSummarysPlan,
  updateProductionSummarysInventory,
  updateProductionSummarysTrend,
  updateProductionSummarysSafetyStock,
  updateProductionSummarysProductMaster,
  updateProductionSummarysMachine,
} from '@/api/database'
import request from '@/utils/request'
import { fetchProductProcessBOMList, updateProductProcessBOM } from '@/api/master/productProcessBomMaster'
import {
  fetchProductMachineConfigList,
  updateProductMachineConfig,
  type ProductMachineConfig,
} from '@/api/master/productMachineConfigMaster'
import { fetchMachines } from '@/api/master/machineMaster'
import jaLocale from 'element-plus/es/locale/lang/ja'

const STOCK_LOGS_BASE = '/api/erp/stock-transaction-logs'
const INVENTORY_BASE = '/api/erp/inventory'

const getJSTDateString = (year: number, month: number, day: number) => {
  const monthStr = String(month + 1).padStart(2, '0')
  const dayStr = String(day).padStart(2, '0')
  return `${year}-${monthStr}-${dayStr}`
}
const getCurrentJSTInfo = () => {
  const now = new Date()
  const jstOffset = 9 * 60 * 60 * 1000
  const jstTime = new Date(now.getTime() + jstOffset)
  return {
    year: jstTime.getUTCFullYear(),
    month: jstTime.getUTCMonth(),
    date: jstTime.getUTCDate(),
  }
}
const createDefaultDateRange = (): [string, string] => {
  const { year, month, date } = getCurrentJSTInfo()
  const todayStr = getJSTDateString(year, month, date)
  return [todayStr, todayStr]
}
const formatDateToString = (input: Date) => {
  const y = input.getFullYear()
  const m = String(input.getMonth() + 1).padStart(2, '0')
  const d = String(input.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}
const parseDateString = (dateStr: string) => {
  const [y, m, d] = dateStr.split('-').map(Number)
  return new Date(y, (m || 1) - 1, d || 1)
}
const createShortcutRange = (days: number) => {
  const end = new Date()
  const start = new Date(end)
  start.setDate(start.getDate() - (days - 1))
  return [start, end]
}
const getMonthRange = (year: number, month: number) => {
  return [new Date(year, month, 1), new Date(year, month + 1, 0)]
}

const datePickerShortcuts: Array<{ text: string; value: () => Date[] }> = [
  { text: '過去7日', value: () => createShortcutRange(7) },
  { text: '過去14日', value: () => createShortcutRange(14) },
  { text: '過去30日', value: () => createShortcutRange(30) },
  {
    text: '今月',
    value: () => {
      const now = new Date()
      return getMonthRange(now.getFullYear(), now.getMonth())
    },
  },
]

const loading = ref(false)
const tableData = ref<any[]>([])
const currentPage = ref(1)
const pageSize = ref(150)
const total = ref(0)
const lastRefreshTime = ref<string>('')
const dateRange = ref<[string, string] | null>(createDefaultDateRange())
const filterProductCd = ref('')
const filterKeyword = ref('')
let keywordFilterTimer: ReturnType<typeof setTimeout> | null = null
const sortBy = ref<string>('product_name')
const sortOrder = ref<'ASC' | 'DESC'>('ASC')
const productList = ref<Array<{ product_cd: string; product_name?: string }>>([])
const showColumnSettings = ref(false)
const activeTableTab = ref<string>('custom')

// 初期在庫一括登録
const showBatchInitialStockDialog = ref(false)
const batchInitialStockMonth = ref<string>('')
const batchInitialStockProcessCd = ref<string>('')
const batchInitialStockData = ref<
  Array<{
    product_cd: string
    product_name: string
    editQuantity: number | null
    existing_id?: number
    existing_quantity?: number
    transaction_time?: string
  }>
>([])
const processOptions = ref<Array<{ cd: string; name: string }>>([])
const batchInitialStockLoading = ref(false)
const batchInitialStockSaving = ref(false)
const batchQtyInputRefs = ref<Array<any>>([])

// データ生成
const generating = ref(false)
const updatingFromOrderDaily = ref(false)
const updatingCarryOver = ref(false)
const updatingOrder = ref(false)
const updatingAll = ref(false)
const updatingActual = ref(false)
const updatingDefect = ref(false)
const updatingScrap = ref(false)
const updatingOnHold = ref(false)
const updatingProductionDates = ref(false)
const updatingPlan = ref(false)
const updatingInventoryTrend = ref(false)
const updatingProductMaster = ref(false)
const showInventoryTrendUpdateConfirmDialog = ref(false)
const showPlanConfirmDialog = ref(false)
const showProductMasterUpdateDialog = ref(false)
const productMasterDateRange = ref<[string, string] | null>(null)
const updatingMachine = ref(false)
const showMachineUpdateDialog = ref(false)
const machineDateRange = ref<[string, string] | null>(null)
const showAllUpdateConfirmDialog = ref(false)
// その他メニュー（スマホ・タブレットは Drawer で表示）
const isSmallScreen = ref(false)
const showOthersDrawer = ref(false)
let othersDrawerMql: MediaQueryList | null = null
let othersDrawerMqlHandler: (() => void) | null = null
// 実績一括登録
const showBatchActualDialog = ref(false)
const batchActualDate = ref<string>('')
const batchActualTableData = ref<
  Array<{
    product_cd: string
    product_name: string
    date: string
    cuttingActual: number | null
    chamferingActual: number | null
    moldingActual: number | null
  }>
>([])
const batchActualSaving = ref(false)
// 在庫取引ログ入力（表格双击弹窗）
const showTransactionInputDialog = ref(false)
const submittingTransaction = ref(false)
const transactionInputInfo = ref<{
  date: string
  productCd: string
  productName: string
  processCd: string
  processName: string
}>({ date: '', productCd: '', productName: '', processCd: '', processName: '' })
const transactionForm = ref<{
  actual: number | null
  defect: number | null
  scrap: number | null
  onHold: number | null
  inbound: number | null
  outbound: number | null
}>({ actual: null, defect: null, scrap: null, onHold: null, inbound: null, outbound: null })
// 工程別計画確認印刷
const showPrintDateDialog = ref(false)
const printTargetDate = ref<string>('')
const showGenerateConfirmDialog = ref(false)
const generateDateRange = ref({ start: '', end: '' })
const showProgressDialog = ref(false)
const progressPercentage = ref(0)
const progressStatus = ref<'success' | 'exception' | 'warning' | ''>('')
const progressText = ref('データ生成を準備中...')
const progressDialogTitle = ref('処理中')

const tableTabs = [
  { key: 'custom', label: '受注', icon: '📝', color: 'linear-gradient(135deg, #8b5cf6, #ec4899)' },
  { key: 'actual', label: '実績', icon: '✔️', color: 'linear-gradient(135deg, #10b981, #34d399)' },
  { key: 'inventory', label: '在庫', icon: '📦', color: 'linear-gradient(135deg, #f59e0b, #d97706)' },
  { key: 'trend', label: '推移', icon: '📈', color: 'linear-gradient(135deg, #9333ea, #c026d3)' },
  { key: 'actual_plan_trend', label: '実計推移', icon: '📊', color: 'linear-gradient(135deg, #6366f1, #ec4899)' },
  { key: 'defect', label: '不良', icon: '❌', color: 'linear-gradient(135deg, #f59e0b, #fbbf24)' },
  { key: 'scrap', label: '廃棄', icon: '🗑️', color: 'linear-gradient(135deg, #ef4444, #f87171)' },
  { key: 'on_hold', label: '保留', icon: '⏸️', color: 'linear-gradient(135deg, #06b6d4, #22d3ee)' },
  { key: 'plan', label: '計画', icon: '📅', color: 'linear-gradient(135deg, #14b8a6, #0d9488)' },
  { key: 'carry_over', label: '繰越', icon: '🔄', color: 'linear-gradient(135deg, #6366f1, #8b5cf6)' },
]

const columnDefinitions: Record<string, { label: string; group: string; type?: string; width?: number }> = {
  // 基本情報（width = 固定列幅）
  id: { label: 'ID', group: '基本情報', width: 20 },
  date: { label: '日付', group: '基本情報', width: 100 },
  day_of_week: { label: '曜日', group: '基本情報', width: 60 },
  route_cd: { label: '工程グループ', group: '基本情報', width: 120 },
  product_cd: { label: '製品CD', group: '基本情報', width: 90 },
  product_name: { label: '製品名', group: '基本情報', width: 110 },
  order_quantity: { label: '受注数', group: '受注・内示', width: 70 },
  forecast_quantity: { label: '内示数', group: '受注・内示', width: 70 },
  safety_stock: { label: '安全在庫', group: '受注・内示', width: 90 },

  // 切断
  cutting_carry_over: { label: '切断繰越', group: '切断', width: 70 },
  cutting_actual: { label: '切断実績', group: '切断', width: 70 },
  cutting_defect: { label: '切断不良', group: '切断', width: 70 },
  cutting_scrap: { label: '切断廃棄', group: '切断', width: 70 },
  cutting_on_hold: { label: '切断保留品', group: '切断', width: 80 },
  cutting_inventory: { label: '切断在庫', group: '切断', width: 70 },
  cutting_trend: { label: '切断推移', group: '切断', width: 70 },
  cutting_production_date: { label: '切断生産日', group: '切断', type: 'date', width: 100 },
  cutting_machine: { label: '切断機', group: '切断', type: 'text', width: 80 },
  cutting_plan: { label: '切断計画', group: '切断', width: 70 },
  cutting_actual_plan: { label: '切断実計', group: '切断', width: 70 },
  cutting_actual_plan_trend: { label: '切断実計推移', group: '切断', width: 90 },

  // 面取
  chamfering_carry_over: { label: '面取繰越', group: '面取', width: 85 },
  chamfering_actual: { label: '面取実績', group: '面取', width: 85 },
  chamfering_defect: { label: '面取不良', group: '面取', width: 85 },
  chamfering_scrap: { label: '面取廃棄', group: '面取', width: 70 },
  chamfering_on_hold: { label: '面取保留品', group: '面取', width: 80 },
  chamfering_inventory: { label: '面取在庫', group: '面取', width: 85 },
  chamfering_trend: { label: '面取推移', group: '面取', width: 85 },
  chamfering_production_date: { label: '面取生産日', group: '面取', type: 'date', width: 100 },
  chamfering_machine: { label: '面取機', group: '面取', type: 'text', width: 80 },
  sw_machine: { label: 'sw機', group: '面取', type: 'text', width: 80 },
  sw_plan: { label: 'sw計画', group: '面取', width: 80 },
  chamfering_plan: { label: '面取計画', group: '面取', width: 85 },
  chamfering_actual_plan: { label: '面取実計', group: '面取', width: 85 },
  chamfering_actual_plan_trend: { label: '面取実計推移', group: '面取', width: 110 },

  // 成型
  molding_carry_over: { label: '成型繰越', group: '成型', width: 70 },
  molding_actual: { label: '成型実績', group: '成型', width: 70 },
  molding_defect: { label: '成型不良', group: '成型', width: 70 },
  molding_scrap: { label: '成型廃棄', group: '成型', width: 70 },
  molding_on_hold: { label: '成型保留品', group: '成型', width: 80 },
  molding_inventory: { label: '成型在庫', group: '成型', width: 70 },
  molding_trend: { label: '成型推移', group: '成型', width: 90 },
  molding_production_date: { label: '成型生産日', group: '成型', type: 'date', width: 100 },
  molding_machine: { label: '成型機', group: '成型', type: 'text', width: 80 },
  molding_plan: { label: '成型計画', group: '成型', width: 85 },
  molding_actual_plan: { label: '成型実計', group: '成型', width: 85 },
  molding_actual_plan_trend: { label: '成型実計推移', group: '成型', width: 110 },
  /** API 計算: ルート上成型の直前工程の在庫列の値 */
  pre_molding_inventory: { label: '成型前在庫', group: '成型', width: 88 },
  pre_molding_prev_process: { label: '成型直前工程', group: '成型', type: 'text', width: 100 },

  // メッキ
  plating_carry_over: { label: 'メッキ繰越', group: 'メッキ', width: 80 },
  plating_actual: { label: 'メッキ実績', group: 'メッキ', width: 80 },
  plating_defect: { label: 'メッキ不良', group: 'メッキ', width: 80 },
  plating_scrap: { label: 'メッキ廃棄', group: 'メッキ', width: 80 },
  plating_on_hold: { label: 'メッキ保留品', group: 'メッキ', width: 80 },
  plating_inventory: { label: 'メッキ在庫', group: 'メッキ', width: 80 },
  plating_trend: { label: 'メッキ推移', group: 'メッキ', width: 100 },
  plating_production_date: { label: 'メッキ生産日', group: 'メッキ', type: 'date', width: 110 },
  plating_machine: { label: 'メッキ治具', group: 'メッキ', type: 'text', width: 110 },
  plating_plan: { label: 'メッキ計画', group: 'メッキ', width: 80 },
  plating_actual_plan: { label: 'メッキ実計', group: 'メッキ', width: 80 },
  plating_actual_plan_trend: { label: 'メッキ実計推移', group: 'メッキ', width: 90 },
  /** API 計算: ルート上メッキ/外注メッキ直前工程の在庫列の値 */
  pre_plating_inventory: { label: 'メッキ前在庫', group: 'メッキ', width: 88 },
  pre_plating_prev_process: { label: 'メッキ直前工程', group: 'メッキ', type: 'text', width: 100 },

  // 溶接
  welding_carry_over: { label: '溶接繰越', group: '溶接', width: 70 },
  welding_actual: { label: '溶接実績', group: '溶接', width: 70 },
  welding_defect: { label: '溶接不良', group: '溶接', width: 70 },
  welding_scrap: { label: '溶接廃棄', group: '溶接', width: 70 },
  welding_on_hold: { label: '溶接保留品', group: '溶接', width: 80 },
  welding_inventory: { label: '溶接在庫', group: '溶接', width: 70 },
  welding_trend: { label: '溶接推移', group: '溶接', width: 70 },
  welding_production_date: { label: '溶接生産日', group: '溶接', type: 'date', width: 100 },
  welding_machine: { label: '溶接機', group: '溶接', type: 'text', width: 80 },
  welding_plan: { label: '溶接計画', group: '溶接', width: 70 },
  welding_actual_plan: { label: '溶接実計', group: '溶接', width: 70 },
  welding_actual_plan_trend: { label: '溶接実計推移', group: '溶接', width: 90 },

  // 検査
  inspection_carry_over: { label: '検査繰越', group: '検査', width: 70 },
  inspection_actual: { label: '検査実績', group: '検査', width: 70 },
  inspection_defect: { label: '検査不良', group: '検査', width: 70 },
  inspection_scrap: { label: '検査廃棄', group: '検査', width: 70 },
  inspection_on_hold: { label: '検査保留品', group: '検査', width: 80 },
  inspection_inventory: { label: '検査在庫', group: '検査', width: 85 },
  inspection_trend: { label: '検査推移', group: '検査', width: 70 },
  inspection_production_date: { label: '検査生産日', group: '検査', type: 'date', width: 100 },
  inspector_machine: { label: '検査員', group: '検査', type: 'text', width: 80 },
  inspection_plan: { label: '検査計画', group: '検査', width: 70 },
  inspection_actual_plan: { label: '検査実計', group: '検査', width: 70 },
  inspection_actual_plan_trend: { label: '検査実計推移', group: '検査', width: 90 },

  // 倉庫
  warehouse_carry_over: { label: '倉庫繰越', group: '倉庫', width: 70 },
  warehouse_actual: { label: '倉庫実績', group: '倉庫', width: 70 },
  warehouse_defect: { label: '倉庫不良', group: '倉庫', width: 70 },
  warehouse_scrap: { label: '倉庫廃棄', group: '倉庫', width: 70 },
  warehouse_on_hold: { label: '倉庫保留品', group: '倉庫', width: 80 },
  warehouse_inventory: { label: '倉庫在庫', group: '倉庫', width: 90 },
  warehouse_trend: { label: '倉庫推移', group: '倉庫', width: 70 },

  // 外注倉庫
  outsourced_warehouse_carry_over: { label: '外注倉庫繰越', group: '外注倉庫', width: 100 },
  outsourced_warehouse_actual: { label: '外注倉庫実績', group: '外注倉庫', width: 100 },
  outsourced_warehouse_defect: { label: '外注倉庫不良', group: '外注倉庫', width: 100 },
  outsourced_warehouse_scrap: { label: '外注倉庫廃棄', group: '外注倉庫', width: 100 },
  outsourced_warehouse_on_hold: { label: '外注倉庫保留品', group: '外注倉庫', width: 110 },
  outsourced_warehouse_inventory: { label: '外注倉庫在庫', group: '外注倉庫', width: 120 },
  outsourced_warehouse_trend: { label: '外注倉庫推移', group: '外注倉庫', width: 100 },

  // 外注メッキ
  outsourced_plating_carry_over: { label: '外注メッキ繰越', group: '外注メッキ', width: 110 },
  outsourced_plating_actual: { label: '外注メッキ実績', group: '外注メッキ', width: 110 },
  outsourced_plating_defect: { label: '外注メッキ不良', group: '外注メッキ', width: 110 },
  outsourced_plating_scrap: { label: '外注メッキ廃棄', group: '外注メッキ', width: 110 },
  outsourced_plating_on_hold: { label: '外注メッキ保留品', group: '外注メッキ', width: 110 },
  outsourced_plating_inventory: { label: '外注メッキ在庫', group: '外注メッキ', width: 110 },
  outsourced_plating_production_date: { label: '外注メッキ生産日', group: '外注メッキ', type: 'date', width: 110 },
  outsourced_plating_trend: { label: '外注メッキ推移', group: '外注メッキ', width: 110 },
  outsourced_plating_machine: { label: '外注メッキ先', group: '外注メッキ', type: 'text', width: 120 },
  outsourced_plating_plan: { label: '外注メッキ計画', group: '外注メッキ', width: 110 },
  outsourced_plating_actual_plan: { label: '外注メッキ実計', group: '外注メッキ', width: 110 },
  outsourced_plating_actual_plan_trend: { label: '外注メッキ実計推移', group: '外注メッキ', width: 120 },

  // 外注溶接
  outsourced_welding_carry_over: { label: '外注溶接繰越', group: '外注溶接', width: 100 },
  outsourced_welding_actual: { label: '外注溶接実績', group: '外注溶接', width: 100 },
  outsourced_welding_defect: { label: '外注溶接不良', group: '外注溶接', width: 100 },
  outsourced_welding_scrap: { label: '外注溶接廃棄', group: '外注溶接', width: 100 },
  outsourced_welding_on_hold: { label: '外注溶接保留品', group: '外注溶接', width: 110 },
  outsourced_welding_inventory: { label: '外注溶接在庫', group: '外注溶接', width: 100 },
  outsourced_welding_production_date: { label: '外注溶接生産日', group: '外注溶接', type: 'date', width: 110 },
  outsourced_welding_trend: { label: '外注溶接推移', group: '外注溶接', width: 100 },
  outsourced_welding_machine: { label: '外注溶接先', group: '外注溶接', type: 'text', width: 120 },
  outsourced_welding_plan: { label: '外注溶接計画', group: '外注溶接', width: 100 },
  outsourced_welding_actual_plan: { label: '外注溶接実計', group: '外注溶接', width: 100 },
  outsourced_welding_actual_plan_trend: { label: '外注溶接実計推移', group: '外注溶接', width: 120 },

  // 溶接前検査
  pre_welding_inspection_carry_over: { label: '溶接前検査繰越', group: '溶接前検査', width: 110 },
  pre_welding_inspection_actual: { label: '溶接前検査実績', group: '溶接前検査', width: 110 },
  pre_welding_inspection_defect: { label: '溶接前検査不良', group: '溶接前検査', width: 110 },
  pre_welding_inspection_scrap: { label: '溶接前検査廃棄', group: '溶接前検査', width: 110 },
  pre_welding_inspection_on_hold: { label: '溶接前検査保留品', group: '溶接前検査', width: 120 },
  pre_welding_inspection_inventory: { label: '溶接前検査在庫', group: '溶接前検査', width: 120 },
  pre_welding_inspection_trend: { label: '溶接前検査推移', group: '溶接前検査', width: 110 },

  // 外注支給前
  pre_inspection_carry_over: { label: '外注支給前繰越', group: '外注支給前', width: 110 },
  pre_inspection_actual: { label: '外注支給前実績', group: '外注支給前', width: 110 },
  pre_inspection_scrap: { label: '外注支給前廃棄', group: '外注支給前', width: 110 },
  pre_inspection_inventory: { label: '外注支給前在庫', group: '外注支給前', width: 110 },
  pre_inspection_trend: { label: '外注支給前推移', group: '外注支給前', width: 110 },

  // 外注検査前
  pre_outsourcing_carry_over: { label: '外注検査前繰越', group: '外注検査前', width: 110 },
  pre_outsourcing_actual: { label: '外注検査前実績', group: '外注検査前', width: 110 },
  pre_outsourcing_scrap: { label: '外注検査前廃棄', group: '外注検査前', width: 110 },
  pre_outsourcing_inventory: { label: '外注検査前在庫', group: '外注検査前', width: 110 },
  pre_outsourcing_trend: { label: '外注検査前推移', group: '外注検査前', width: 110 },
}

/** 双击不弹窗的列（基本情報等） */
const basicColumns = new Set([
  'id', 'date', 'day_of_week', 'route_cd', 'product_cd', 'product_name',
  'order_quantity', 'forecast_quantity', 'safety_stock',
])
/** 列字段前缀 → 工程CD（双击弹窗用） */
const processFieldToProcessCd: Record<string, string> = {
  cutting: 'KT01',
  chamfering: 'KT02',
  molding: 'KT04',
  plating: 'KT05',
  welding: 'KT07',
  inspection: 'KT09',
  warehouse: 'KT13',
  outsourced_plating: 'KT06',
  outsourced_welding: 'KT08',
  outsourced_warehouse: 'KT15',
  pre_welding_inspection: 'KT11',
  pre_inspection: 'KT16',
  pre_outsourcing: 'KT17',
}

const columnKeys = Object.keys(columnDefinitions)
const defaultVisibleColumns: Record<string, boolean> = {
  id: false,
  date: true,
  day_of_week: false,
  route_cd: false,
  product_cd: true,
  product_name: true,
  order_quantity: true,
  forecast_quantity: true,
  safety_stock: true,
  ...Object.fromEntries(
    columnKeys
      .filter(
        (k) =>
          !['id', 'date', 'day_of_week', 'route_cd', 'product_cd', 'product_name', 'order_quantity', 'forecast_quantity', 'safety_stock'].includes(k)
      )
      .map((k) => [k, false])
  ),
}

const visibleColumns = ref<Record<string, boolean>>({ ...defaultVisibleColumns })

const fieldTypeMapping: Record<string, string> = {
  carry_over: '_carry_over',
  actual: '_actual',
  defect: '_defect',
  scrap: '_scrap',
  on_hold: '_on_hold',
  inventory: '_inventory',
  trend: '_trend',
  plan: '_plan',
  actual_plan_trend: '_actual_plan_trend',
}
const processPrefixes = [
  'cutting',
  'chamfering',
  'molding',
  'plating',
  'welding',
  'inspection',
  'warehouse',
  'outsourced_warehouse',
  'outsourced_plating',
  'outsourced_welding',
  'pre_welding_inspection',
  'pre_inspection',
  'pre_outsourcing',
]

const dynamicColumns = computed(() => {
  const activeFieldType = activeTableTab.value
  if (activeFieldType === 'custom') {
    const baseColumns = ['id', 'date', 'day_of_week', 'route_cd', 'product_cd', 'product_name', 'order_quantity', 'forecast_quantity', 'safety_stock']
    const cols: Array<{ prop: string; label: string; width?: number; type?: string }> = []
    columnKeys.forEach((key) => {
      if (visibleColumns.value[key] && !baseColumns.includes(key)) {
        const def = columnDefinitions[key]
        if (def)
          cols.push({
            prop: key,
            label: def.label,
            width: def.width ?? (def.type === 'date' ? 100 : def.type === 'text' ? 90 : 80),
            type: def.type,
          })
      }
    })
    return cols
  }
  const suffix = fieldTypeMapping[activeFieldType]
  const cols: Array<{ prop: string; label: string; width?: number; type?: string }> = []
  if (!suffix) return cols
  const fieldTypeKeywords: Record<string, string[]> = {
    carry_over: ['繰越'],
    actual: ['実績'],
    defect: ['不良'],
    scrap: ['廃棄'],
    on_hold: ['保留品', '保留'],
    inventory: ['在庫'],
    trend: ['推移'],
    plan: ['計画'],
    actual_plan_trend: ['実計推移'],
  }
  processPrefixes.forEach((process) => {
    const key = `${process}${suffix}`
    const def = columnDefinitions[key]
    if (def) {
      const keywords = fieldTypeKeywords[activeFieldType] || []
      let cleanedLabel = def.label
      keywords.sort((a, b) => b.length - a.length).forEach((kw) => (cleanedLabel = cleanedLabel.replace(kw, '')))
      cols.push({
        prop: key,
        label: cleanedLabel.trim(),
        width: def.width ?? (def.type === 'date' ? 100 : def.type === 'text' ? 90 : 80),
        type: def.type,
      })
    }
  })
  return cols
})

const groupedColumns = computed(() => {
  const groups: Record<string, Record<string, { label: string }>> = {}
  Object.entries(columnDefinitions).forEach(([key, column]) => {
    const groupName = column.group || 'その他'
    if (!groups[groupName]) groups[groupName] = {}
    groups[groupName][key] = column
  })
  return groups
})

const numericFields = new Set(
  columnKeys.filter((k) => {
    const def = columnDefinitions[k]
    return def && def.type !== 'date' && def.type !== 'text'
  })
)

const formatDate = (dateValue: string | Date | null) => {
  if (!dateValue) return '-'
  if (typeof dateValue === 'string') return dateValue.split('T')[0]
  return formatDateToString(new Date(dateValue))
}

/** pre_plating_prev_process（API の工程 key）を短い表示用ラベルに */
const prePlatingPrevLabels: Record<string, string> = {
  cutting: '切断',
  chamfering: '面取',
  molding: '成型',
  plating: 'メッキ',
  welding: '溶接',
  inspection: '検査',
  warehouse: '倉庫',
  outsourced_warehouse: '外注倉庫',
  outsourced_plating: '外注メッキ',
  outsourced_welding: '外注溶接',
  pre_welding_inspection: '溶接前検査',
  pre_inspection: '外注支給前',
  pre_outsourcing: '外注検査前',
}
function formatPrePlatingPrevKey(v: string | null | undefined) {
  if (v == null || v === '') return '—'
  return prePlatingPrevLabels[v] || v
}
const getWeekdayType = (dayOfWeek: string) => {
  if (dayOfWeek === '土') return 'primary'
  if (dayOfWeek === '日') return 'danger'
  return 'info'
}
const headerCellStyle = {
  background: '#f8fafc',
  color: '#475569',
  fontWeight: 600,
  fontSize: '0.65rem',
  padding: '4px 8px',
  borderBottom: '1px solid #e5e7eb',
}
const cellStyleHandler = ({ row, column }: { row: Record<string, any>; column: { property?: string } }) => {
  const prop = column?.property
  if (!prop) return {}
  const value = row[prop]
  if (typeof value === 'number') {
    if (value < 0) return { color: '#dc2626', fontWeight: 700 }
    if (value > 0) return { color: '#047857', fontWeight: 700 }
  }
  return {}
}
/** 安全在庫列の合計：product_cd ごとに最新日付の行の safety_stock のみを取って合算 */
function sumSafetyStockByLatestDatePerProduct(data: any[]): number {
  const byProduct = new Map<string, { date: string; safety_stock: number }>()
  for (const row of data) {
    const pc = (row.product_cd ?? '').toString().trim()
    if (!pc) continue
    const d = row.date ? (typeof row.date === 'string' ? row.date.slice(0, 10) : String(row.date).slice(0, 10)) : ''
    const val = Number(row.safety_stock) || 0
    const cur = byProduct.get(pc)
    if (!cur || d > cur.date) byProduct.set(pc, { date: d, safety_stock: val })
  }
  return Array.from(byProduct.values()).reduce((a, b) => a + b.safety_stock, 0)
}

const getSummaries = (param: { columns: any[]; data: any[] }) => {
  const { columns, data } = param
  const sums: string[] = []
  columns.forEach((column, index) => {
    if (index === 0) {
      sums.push('合計')
      return
    }
    const prop = column.property
    if (!prop) {
      sums[index] = ''
      return
    }
    if (prop === 'safety_stock') {
      sums[index] = sumSafetyStockByLatestDatePerProduct(data).toLocaleString()
      return
    }
    if (!numericFields.has(prop)) {
      sums[index] = ''
      return
    }
    const values = data.map((item) => Number(item[prop]) || 0)
    sums[index] = values.reduce((a, b) => a + b, 0).toLocaleString()
  })
  return sums
}

/** データ生成用：当月1日 ～ 当月起算4ヶ月後の月末（日本時区） */
const getGenerateDateRange = (): { start: string; end: string } => {
  const { year, month } = getCurrentJSTInfo()
  const start = getJSTDateString(year, month, 1)
  let endYear = year
  let endMonth = month + 4
  if (endMonth >= 12) {
    endYear += Math.floor(endMonth / 12)
    endMonth = endMonth % 12
  }
  const lastDay = new Date(endYear, endMonth + 1, 0).getDate()
  const end = getJSTDateString(endYear, endMonth, lastDay)
  return { start, end }
}

const handleGenerateData = () => {
  const range = getGenerateDateRange()
  generateDateRange.value = range
  showGenerateConfirmDialog.value = true
}

const handleUpdateFromOrderDaily = async () => {
  try {
    updatingFromOrderDaily.value = true
    const res = await updateProductionSummarysFromOrderDaily({
      updateMode: 'recent',
      days: 10,
      clearBeforeUpdate: true,
    }) as { data?: { updated?: number; unchanged?: number; skipped?: number; total?: number }; message?: string }
    const info = (res?.data ?? res ?? {}) as { updated?: number; unchanged?: number; skipped?: number; total?: number }
    const msg =
      res?.message ??
      `${info.updated ?? 0}件の受注データを反映しました（変更なし ${info.unchanged ?? 0} 件 / スキップ ${info.skipped ?? 0} 件）`
    ElMessage.success(msg)
    await fetchData()
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.message || '受注データ更新に失敗しました')
  } finally {
    updatingFromOrderDaily.value = false
  }
}

const handleUpdateCarryOver = async () => {
  try {
    await ElMessageBox.confirm('繰越データを更新します。', '繰越データ更新確認', {
      confirmButtonText: '実行',
      cancelButtonText: 'キャンセル',
      type: 'info',
    })
  } catch {
    return
  }
  updatingCarryOver.value = true
  showProgressDialog.value = true
  progressPercentage.value = 0
  progressStatus.value = ''
  progressText.value = '繰越フィールドをクリア中...'
  let progressTimer: ReturnType<typeof setInterval> | null = null
  try {
    try {
      await clearProductionSummarysCarryOver()
    } catch (e) {
      console.warn('clear-carry-over:', e)
    }
    progressText.value = '繰越データを更新中...'
    if (progressTimer) clearInterval(progressTimer)
    progressTimer = setInterval(() => {
      if (progressPercentage.value < 90) progressPercentage.value = Math.min(progressPercentage.value + 8, 90)
    }, 200)
    const res = await updateProductionSummarysCarryOver() as { data?: { updated?: number; skipped?: number; total?: number }; message?: string }
    if (progressTimer) clearInterval(progressTimer)
    progressTimer = null
    progressPercentage.value = 100
    progressStatus.value = 'success'
    const info = (res?.data ?? res ?? {}) as { updated?: number; skipped?: number; total?: number }
    const msg = res?.message ?? `更新 ${info.updated ?? 0} 件、スキップ ${info.skipped ?? 0} 件`
    progressText.value = msg
    ElMessage.success(msg)
    setTimeout(() => {
      showProgressDialog.value = false
      setTimeout(() => fetchData(), 500)
    }, 1500)
  } catch (error: any) {
    if (progressTimer) clearInterval(progressTimer)
    progressPercentage.value = 100
    progressStatus.value = 'exception'
    progressText.value = '繰越データ更新に失敗しました'
    ElMessage.error(error?.response?.data?.detail ?? error?.response?.data?.message ?? error?.message ?? '繰越データ更新に失敗しました')
    setTimeout(() => { showProgressDialog.value = false }, 2000)
  } finally {
    updatingCarryOver.value = false
  }
}

/**
 * 実績データ更新 — 算法总结与字段对应
 * =============================================================================
 * 一、前端流程（本画面）
 * -----------------------------------------------------------------------------
 * 1. 入口：「その他」→「実績データ更新」→ 确认对话框「実績データ更新確認」→ 点击「実行」
 * 2. API：POST /production-summarys/update-actual（无请求体）
 * 3. 返回：{ data: { updated, skipped, cleared, clearPeriod }, message }；成功后自动 fetchData() 刷新表
 *
 * 二、后端算法概要
 * -----------------------------------------------------------------------------
 * 1. 数据来源：stock_transaction_logs（在庫取引履歴）
 * 2. 产品码换算：target_cd 取前 4 位 + '1' → product_cd（与 production_summarys.product_cd 对应）
 * 3. 日期：DATE(transaction_time) → production_summarys.date
 * 4. 处理范围：当月 1 日～今日（日本时区）；先对该范围内所有「実績列」清零，再按日志重新汇总写回
 *
 * 三、数据分类与计算方式
 * -----------------------------------------------------------------------------
 * （A）一般工程（12 个 process_cd）
 *     - 条件：transaction_type IN ('実績', '不良')，且 process_cd 在 GENERAL_PROCESS_CDS 内
 *     - 数量：按 (product_cd, date, process_cd) 分组，SUM(quantity)
 *     - 写回：见下「字段对应表」的 process_cd → production_summarys 列
 *
 * （B）製品倉庫（KT13）
 *     - 条件：transaction_type IN ('入庫','出庫')，process_cd = 'KT13'
 *     - 数量：入庫 quantity 为正、出庫为负，按 (product_cd, date) 分组 SUM
 *     - 写回：production_summarys.warehouse_actual
 *
 * （C）外注倉庫（KT15）
 *     - 条件：transaction_type IN ('入庫','出庫')，process_cd = 'KT15'
 *     - 数量：同上，入庫−出庫
 *     - 写回：production_summarys.outsourced_warehouse_actual
 *
 * 四、字段对应表（stock_transaction_logs.process_cd → production_summarys 列）
 * -----------------------------------------------------------------------------
 * | process_cd | production_summarys 列（実績） | 画面表示名     |
 * |------------|----------------------------------|----------------|
 * | KT01       | cutting_actual                   | 切断実績        |
 * | KT02       | chamfering_actual                 | 面取実績        |
 * | KT04       | molding_actual                    | 成型実績        |
 * | KT05       | plating_actual                    | メッキ実績      |
 * | KT06       | outsourced_plating_actual         | 外注メッキ実績  |
 * | KT07       | welding_actual                   | 溶接実績        |
 * | KT08       | outsourced_welding_actual         | 外注溶接実績    |
 * | KT09       | inspection_actual                 | 検査実績        |
 * | KT11       | pre_welding_inspection_actual     | 溶接前検査実績  |
 * | KT16       | pre_inspection_actual             | 外注支給前実績  |
 * | KT17       | pre_outsourcing_actual            | 外注検査前実績  |
 * | KT13       | （非 process 汇总）入出庫净额 → warehouse_actual           | 倉庫実績        |
 * | KT15       | （非 process 汇总）入出庫净额 → outsourced_warehouse_actual | 外注倉庫実績    |
 *
 * 五、被清零的列（ACTUAL_CLEAR_COLUMNS，当月 1 日～今日）
 * -----------------------------------------------------------------------------
 * cutting_actual, chamfering_actual, molding_actual, plating_actual, welding_actual,
 * inspection_actual, warehouse_actual, outsourced_plating_actual, outsourced_welding_actual,
 * pre_welding_inspection_actual, pre_inspection_actual, pre_outsourcing_actual,
 * outsourced_warehouse_actual
 */
const handleUpdateActual = async () => {
  try {
    await ElMessageBox.confirm('実績データを更新します。', '実績データ更新確認', {
      confirmButtonText: '実行',
      cancelButtonText: 'キャンセル',
      type: 'info',
    })
  } catch {
    return
  }
  updatingActual.value = true
  showProgressDialog.value = true
  progressPercentage.value = 0
  progressStatus.value = ''
  progressText.value = '実績データを取得中...'
  let progressTimer: ReturnType<typeof setInterval> | null = null
  try {
    progressTimer = setInterval(() => {
      if (progressPercentage.value < 90) progressPercentage.value = Math.min(progressPercentage.value + 8, 90)
    }, 200)
    progressText.value = '実績データを更新中...'
    const res = await updateProductionSummarysActual()
    if (progressTimer) clearInterval(progressTimer)
    progressTimer = null
    progressPercentage.value = 100
    progressStatus.value = 'success'
    const body = (res as any)?.data ?? {}
    const d = body?.data ?? body
    const msg =
      body?.message ??
      `更新 ${d?.updated ?? 0} 件、クリア ${d?.cleared ?? 0} 件（当月開始）、スキップ ${d?.skipped ?? 0} 件`
    progressText.value = msg
    ElMessage.success(msg)
    setTimeout(() => {
      showProgressDialog.value = false
      setTimeout(() => fetchData(), 500)
    }, 1500)
  } catch (error: any) {
    if (progressTimer) clearInterval(progressTimer)
    progressPercentage.value = 100
    progressStatus.value = 'exception'
    progressText.value = '実績データ更新に失敗しました'
    ElMessage.error(error?.response?.data?.detail ?? error?.response?.data?.message ?? error?.message ?? '実績データ更新に失敗しました')
    setTimeout(() => { showProgressDialog.value = false }, 2000)
  } finally {
    updatingActual.value = false
  }
}

const handleUpdateDefect = async () => {
  try {
    await ElMessageBox.confirm('不良データを更新します。', '不良データ更新確認', {
      confirmButtonText: '実行',
      cancelButtonText: 'キャンセル',
      type: 'warning',
    })
  } catch {
    return
  }
  updatingDefect.value = true
  showProgressDialog.value = true
  progressPercentage.value = 0
  progressStatus.value = ''
  progressText.value = '不良データを取得中...'
  let progressTimer: ReturnType<typeof setInterval> | null = null
  try {
    progressTimer = setInterval(() => {
      if (progressPercentage.value < 90) progressPercentage.value = Math.min(progressPercentage.value + 8, 90)
    }, 200)
    progressText.value = '不良データを更新中...'
    const res = await updateProductionSummarysDefect()
    if (progressTimer) clearInterval(progressTimer)
    progressTimer = null
    progressPercentage.value = 100
    progressStatus.value = 'success'
    const body = (res as any)?.data ?? {}
    const d = body?.data ?? body
    const msg = body?.message ?? `更新 ${d?.updated ?? 0} 件、スキップ ${d?.skipped ?? 0} 件`
    progressText.value = msg
    ElMessage.success(msg)
    setTimeout(() => {
      showProgressDialog.value = false
      setTimeout(() => fetchData(), 500)
    }, 1500)
  } catch (error: any) {
    if (progressTimer) clearInterval(progressTimer)
    progressPercentage.value = 100
    progressStatus.value = 'exception'
    progressText.value = '不良データ更新に失敗しました'
    ElMessage.error(error?.response?.data?.detail ?? error?.response?.data?.message ?? error?.message ?? '不良データ更新に失敗しました')
    setTimeout(() => { showProgressDialog.value = false }, 2000)
  } finally {
    updatingDefect.value = false
  }
}

const handleUpdateScrap = async () => {
  try {
    await ElMessageBox.confirm('廃棄データを更新します。', '廃棄データ更新確認', {
      confirmButtonText: '実行',
      cancelButtonText: 'キャンセル',
      type: 'warning',
    })
  } catch {
    return
  }
  updatingScrap.value = true
  showProgressDialog.value = true
  progressPercentage.value = 0
  progressStatus.value = ''
  progressText.value = '廃棄データを取得中...'
  let progressTimer: ReturnType<typeof setInterval> | null = null
  try {
    progressTimer = setInterval(() => {
      if (progressPercentage.value < 90) progressPercentage.value = Math.min(progressPercentage.value + 8, 90)
    }, 200)
    progressText.value = '廃棄データを更新中...'
    const res = await updateProductionSummarysScrap()
    if (progressTimer) clearInterval(progressTimer)
    progressTimer = null
    progressPercentage.value = 100
    progressStatus.value = 'success'
    const body = (res as any)?.data ?? {}
    const d = body?.data ?? body
    const msg = body?.message ?? `更新 ${d?.updated ?? 0} 件、スキップ ${d?.skipped ?? 0} 件`
    progressText.value = msg
    ElMessage.success(msg)
    setTimeout(() => {
      showProgressDialog.value = false
      setTimeout(() => fetchData(), 500)
    }, 1500)
  } catch (error: any) {
    if (progressTimer) clearInterval(progressTimer)
    progressPercentage.value = 100
    progressStatus.value = 'exception'
    progressText.value = '廃棄データ更新に失敗しました'
    ElMessage.error(error?.response?.data?.detail ?? error?.response?.data?.message ?? error?.message ?? '廃棄データ更新に失敗しました')
    setTimeout(() => { showProgressDialog.value = false }, 2000)
  } finally {
    updatingScrap.value = false
  }
}

const handleUpdateOnHold = async () => {
  try {
    await ElMessageBox.confirm('保留データを更新します。', '保留データ更新確認', {
      confirmButtonText: '実行',
      cancelButtonText: 'キャンセル',
      type: 'info',
    })
  } catch {
    return
  }
  updatingOnHold.value = true
  showProgressDialog.value = true
  progressPercentage.value = 0
  progressStatus.value = ''
  progressText.value = '保留データを取得中...'
  let progressTimer: ReturnType<typeof setInterval> | null = null
  try {
    progressTimer = setInterval(() => {
      if (progressPercentage.value < 90) progressPercentage.value = Math.min(progressPercentage.value + 8, 90)
    }, 200)
    progressText.value = '保留データを更新中...'
    const res = await updateProductionSummarysOnHold()
    if (progressTimer) clearInterval(progressTimer)
    progressTimer = null
    progressPercentage.value = 100
    progressStatus.value = 'success'
    const body = (res as any)?.data ?? {}
    const d = body?.data ?? body
    const msg = body?.message ?? `更新 ${d?.updated ?? 0} 件、スキップ ${d?.skipped ?? 0} 件`
    progressText.value = msg
    ElMessage.success(msg)
    setTimeout(() => {
      showProgressDialog.value = false
      setTimeout(() => fetchData(), 500)
    }, 1500)
  } catch (error: any) {
    if (progressTimer) clearInterval(progressTimer)
    progressPercentage.value = 100
    progressStatus.value = 'exception'
    progressText.value = '保留データ更新に失敗しました'
    ElMessage.error(error?.response?.data?.detail ?? error?.response?.data?.message ?? error?.message ?? '保留データ更新に失敗しました')
    setTimeout(() => { showProgressDialog.value = false }, 2000)
  } finally {
    updatingOnHold.value = false
  }
}

const handleUpdateProductionDates = async () => {
  try {
    await ElMessageBox.confirm('各工程の生産計画日を営業日換算で更新します。', '生産計画日更新確認', {
      confirmButtonText: '実行',
      cancelButtonText: 'キャンセル',
      type: 'info',
    })
  } catch {
    return
  }
  updatingProductionDates.value = true
  showProgressDialog.value = true
  progressPercentage.value = 0
  progressStatus.value = ''
  progressText.value = '生産計画日データを取得中...'
  let progressTimer: ReturnType<typeof setInterval> | null = null
  try {
    progressTimer = setInterval(() => {
      if (progressPercentage.value < 90) progressPercentage.value = Math.min(progressPercentage.value + 8, 90)
    }, 200)
    progressText.value = '生産計画日データを更新中...'
    const res = await updateProductionSummarysProductionDates()
    if (progressTimer) clearInterval(progressTimer)
    progressTimer = null
    progressPercentage.value = 100
    progressStatus.value = 'success'
    const body = (res as any)?.data ?? {}
    const d = body?.data ?? body
    const msg = body?.message ?? `更新 ${d?.updated ?? 0} 件、スキップ ${d?.skipped ?? 0} 件`
    progressText.value = msg
    ElMessage.success(msg)
    setTimeout(() => {
      showProgressDialog.value = false
      setTimeout(() => fetchData(), 500)
    }, 1500)
  } catch (error: any) {
    if (progressTimer) clearInterval(progressTimer)
    progressPercentage.value = 100
    progressStatus.value = 'exception'
    progressText.value = '生産計画日更新に失敗しました'
    ElMessage.error(error?.response?.data?.detail ?? error?.response?.data?.message ?? error?.message ?? '生産計画日更新に失敗しました')
    setTimeout(() => { showProgressDialog.value = false }, 2000)
  } finally {
    updatingProductionDates.value = false
  }
}

/**
 * 在庫更新（在庫・推移更新中的「在庫」部分）— 计算方法详细总结
 * =============================================================================
 * 一、前端流程（本画面）
 * -----------------------------------------------------------------------------
 * 1. 入口：「その他」→「在庫・推移更新」→ 确认对话框「在庫・推移更新確認」→ 点击「更新」
 * 2. 开始日：当月月初 getFirstDayOfCurrentMonth()（当月1日 YYYY-MM-DD）。计算前先清空「当月月初之后」的在庫・推移字段，再在该范围内重新计算。
 *    - 清空：POST clear-calculated-fields(当月月初) → 范围 当月月初～当月月初+3ヶ月 的计算字段置 0
 *    - 在庫：POST update-inventory(当月月初) → 同上区间按公式重算
 *    - 推移：POST update-trend(当月月初) → 当月月初～表内最大日
 * 3. 执行顺序：先 clear-calculated-fields(当月月初)，再 update-inventory(当月月初)，再 update-trend(当月月初)
 * 4. 计算期间说明：在庫・清空＝当月月初～当月月初+3ヶ月；推移＝当月月初～表内最大日
 *
 * 二、后端在庫更新范围与数据准备
 * -----------------------------------------------------------------------------
 * - 有 startDate：全局开始日 = startDate，结束日 = startDate + 3 个月；只处理 date ∈ [globalStart, globalEnd] 的行
 * - 无 startDate：按产品取「任意 carry_over 列 > 0 的行的 MAX(date)」作为该产品 start_date，结束日 = start_date + 3 个月；只处理该产品在该区间内的行
 * - 先对范围内行的「所有在庫列」一次性置 0，再按 product_cd、date 升序逐行计算并批量 UPDATE
 *
 * 三、工程顺序（sequence）
 * -----------------------------------------------------------------------------
 * - route_cd：优先 production_summarys.route_cd，空则用 products.route_cd
 * - 顺序来源：ProcessRoute.description 用分隔符（⇒ / → / , / 空白 / -> / => / ｜ / |）分割，按关键词最长匹配得到 key 序列（切断→面取→…→倉庫 或 外注倉庫）；无 description 时用 process_route_steps 按 step_no 的 process_cd 映射（KT13=倉庫, KT15=外注倉庫）；再无则用默认顺序（最后工程=倉庫）
 *
 * 四、一般工程在庫公式（_compute_inventory_updates）
 * -----------------------------------------------------------------------------
 * 对 sequence 中除「外注倉庫」外的每个工程：
 *   当工程在庫 = 繰越(carry) + 実績(actual) - 不良(defect) - 廃棄(scrap) - 保留(on_hold) - 下一工程実績(next_actual) + 前日当工程在庫(previous_inventory)
 * - 起算日当天：前日当工程在庫 = 0
 * - 下一工程：若下一项为「外注倉庫」则 next_actual = outsourced_warehouse_actual；否则为下一项的 actual 列
 * - 外注倉庫在庫不在此函数中计算，由倉庫/外注倉庫单独公式处理
 *
 * 五、倉庫在庫（仅当 sequence 最后工程 = 倉庫 时）
 * -----------------------------------------------------------------------------
 * 倉庫在庫 = 倉庫繰越 + 倉庫実績 - 倉庫廃棄 - 倉庫保留品 - 扣除数 + 前日倉庫在庫
 * - 起算日当天前日倉庫在庫 = 0
 * - 扣除数（见下）
 *
 * 六、外注倉庫在庫（仅当 sequence 最后工程 = 外注倉庫 时）
 * -----------------------------------------------------------------------------
 * 外注倉庫在庫 = 外注倉庫繰越 + 外注倉庫実績 - 外注倉庫廃棄 - 扣除数 + 前日外注倉庫在庫
 * - 起算日当天前日外注倉庫在庫 = 0
 * - 扣除数（见下）
 *
 * 七、扣除数（qty_subtract）规则
 * -----------------------------------------------------------------------------
 * - 先按产品计算 lastOrderQuantityDate = 该产品在本次处理行中「order_quantity > 0」的日期的最大值
 * - 对每一行：若存在 lastOrderQuantityDate 且 当前行 date <= lastOrderQuantityDate 且 当前行 order_quantity > 0，则 扣除数 = order_quantity（受注）；否则 扣除数 = forecast_quantity（内示）
 *
 * 八、递推与写回
 * -----------------------------------------------------------------------------
 * - 同一产品内按 date 升序处理；previous_inv / prev_warehouse / prev_outsourced_wh 分别记录「上一行（前日）」的同工程在庫，供下一行使用
 * - 每 100 行一批，用 CASE id WHEN ... THEN value ... 批量 UPDATE production_summarys 的在庫列
 * - 允许在庫为负数（不做 floor 到 0）
 */

/**
 * 安全在庫更新（在庫・推移更新に含まれる）— 算法总结
 * -----------------------------------------------------------------------------
 * 公式: 安全在庫 = ceil(将来30営業日の平均日出荷数 × 製品マスタの safety_days)
 * - 対象: 製品マスタで safety_days IS NOT NULL AND safety_days > 0 の製品のみ
 * - 平均日出荷数: production_summarys の内示数(forecast_quantity)を、当該行の翌日から30営業日分で平均
 * - 安全在庫列の合計: product_cd ごとに「最新日付の行」の safety_stock のみを合算（表の合計行）
 */

/**
 * 推移更新（在庫・推移更新中的「推移」部分）— 算法总结
 * =============================================================================
 * 一、前端与执行顺序
 * -----------------------------------------------------------------------------
 * - 入口同「在庫・推移更新」；开始日 = 当月月初 getFirstDayOfCurrentMonth()
 * - 执行顺序：先 clear（当月月初～+3ヶ月 含 trend 列）→ 在庫更新 → 推移更新
 * - 推移 API：POST update-trend(startDate)，startDate 指定时后端处理 date >= startDate 的全行（无结束日上限）
 *
 * 二、后端处理范围与数据准备
 * -----------------------------------------------------------------------------
 * - 有 startDate：只处理 date >= startDate 的行（終了日なし、表内最大日まで）
 * - 无 startDate：按产品起算日（任意 carry_over > 0 的 MAX(date)），处理 date >= 该产品 start_date 的行
 * - 先对范围内行的「所有 *_trend、*_actual_plan_trend 列」一次性置 0，再按 product_cd、date 升序逐行计算并累加后写回
 *
 * 三、工程顺序（sequence）
 * -----------------------------------------------------------------------------
 * - 与在庫更新相同：route_cd（production_summarys / products）、ProcessRoute.description 或 process_route_steps，KT13=倉庫 / KT15=外注倉庫
 *
 * 四、当日 trend 增量公式（_compute_trend_updates）
 * -----------------------------------------------------------------------------
 * 对 sequence 中每个有 trend 字段的工程（含倉庫・外注倉庫）：
 *   当日 trend 增量 = 当工程繰越(carry)
 *                  + 后续工程繰越之和(subsequentCarryOverSum)
 *                  + 当工程実績(actual)
 *                  - 当工程不良(defect) - 廃棄(scrap) - 保留(on_hold)
 *                  - 需要数(forecast_quantity)
 *                  - 后续工程不良之和(subsequentDefectSum)
 *                  - 后续工程廃棄之和(subsequentScrapSum)
 *                  - 后续工程保留之和(subsequentOnHoldSum)
 * 即：trend_daily = carry + sub_carry + actual - defect - scrap - on_hold - forecast - sub_defect - sub_scrap - sub_on_hold
 * 「后续」= sequence 中该工程之后的所有工程（carry/defect/scrap/on_hold 分别求和）
 *
 * 五、最终 trend 写回（累加前日）
 * -----------------------------------------------------------------------------
 * 对每一行：最终 trend = 当日 trend 增量(day_trends) + 前日 trend(prev_trends[key])
 * 起算日（该产品第一行）时前日 = 0。同一产品内按 date 升序，prev_trends 记录上一行写回后的各工程 trend，供下一行使用。
 *
 * 六、实计推移 actual_plan_trend（_compute_actual_plan_trend_updates）
 * -----------------------------------------------------------------------------
 * - 仅对 6 工程计算：cutting, chamfering, molding, plating, welding, inspection（TREND_PREFIXES）
 * - 公式与 trend 相同，但「当工程実績」改为「当工程実計」*_actual_plan；carry / defect / scrap / on_hold / forecast / 后续 carry・defect・scrap・on_hold 不变
 * - 写回：当日 actual_plan_trend 增量 + 前日 actual_plan_trend，prev_actual_plan_trends 递推
 *
 * 七、批处理与写回
 * -----------------------------------------------------------------------------
 * - 每 100 行一批，用 CASE id 批量 UPDATE 各 *_trend、*_actual_plan_trend 列
 * - 允许 trend 为负数
 */

/** 当月月初（当月1日）YYYY-MM-DD。在庫・推移更新では「当月月初以降」を清空してから再計算する。 */
function getFirstDayOfCurrentMonth(): string {
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  return `${y}-${m}-01`
}

/** 在庫→推移→安全在庫（計算フィールドクリア後）。メニュー「在庫・推移更新」と同一処理 */
async function runInventoryTrendUpdateSequence(startDate: string) {
  try {
    await clearProductionSummarysCalculatedFields(startDate)
  } catch (_e) {
    console.warn('計算フィールドのクリアに失敗しました', _e)
  }
  showProgressDialog.value = true
  progressPercentage.value = 0
  progressStatus.value = ''
  progressText.value = '在庫・推移データを取得中...'
  let progressTimer: ReturnType<typeof setInterval> | null = null
  try {
    progressTimer = setInterval(() => {
      if (progressPercentage.value < 90) progressPercentage.value = Math.min(progressPercentage.value + 4, 90)
    }, 200)
    progressText.value = '在庫データを更新中...'
    const invRes = await updateProductionSummarysInventory(startDate)
    progressPercentage.value = 50
    progressText.value = '推移データを更新中...'
    const trendRes = await updateProductionSummarysTrend(startDate)
    progressPercentage.value = 75
    progressText.value = '安全在庫を更新中...'
    const safetyRes = await updateProductionSummarysSafetyStock(startDate)
    if (progressTimer) clearInterval(progressTimer)
    progressTimer = null
    progressPercentage.value = 100
    progressStatus.value = 'success'
    const invBody = (invRes as any)?.data ?? {}
    const invD = invBody?.data ?? invBody
    const trendBody = (trendRes as any)?.data ?? {}
    const trendD = trendBody?.data ?? trendBody
    const safetyBody = (safetyRes as any)?.data ?? {}
    const safetyD = safetyBody?.data ?? safetyBody
    const calcPeriod = `計算期間: ${startDate}～（当月月初から）`
    const msg = `${calcPeriod}\n在庫: 更新 ${invD?.updated ?? 0} 件\n推移: 更新 ${trendD?.updated ?? 0} 件\n安全在庫: 更新 ${safetyD?.updated ?? 0} 件`
    progressText.value = msg
    ElMessage.success('在庫・推移の更新が完了しました')
    setTimeout(() => {
      showProgressDialog.value = false
      setTimeout(() => fetchData(), 500)
    }, 1500)
  } catch (error: any) {
    if (progressTimer) clearInterval(progressTimer)
    progressPercentage.value = 100
    progressStatus.value = 'exception'
    progressText.value = '在庫・推移更新に失敗しました'
    ElMessage.error(error?.response?.data?.detail ?? error?.response?.data?.message ?? error?.message ?? '在庫・推移更新に失敗しました')
    setTimeout(() => {
      showProgressDialog.value = false
    }, 2000)
    throw error
  }
}

const handleUpdatePlan = () => {
  showPlanConfirmDialog.value = true
}

const confirmUpdatePlan = async () => {
  showPlanConfirmDialog.value = false
  updatingPlan.value = true
  const startDate = getFirstDayOfCurrentMonth()
  try {
    await clearProductionSummarysCalculatedFields(startDate)
  } catch (_e) {
    console.warn('計算フィールドのクリアに失敗しました', _e)
  }
  try {
    await clearProductionSummarysPlanFields(startDate)
  } catch (_e) {
    console.warn('計画列のクリアに失敗しました', _e)
  }
  showProgressDialog.value = true
  progressPercentage.value = 0
  progressStatus.value = ''
  progressText.value = '計画データを取得中...'
  let progressTimer: ReturnType<typeof setInterval> | null = null
  try {
    progressTimer = setInterval(() => {
      if (progressPercentage.value < 90) progressPercentage.value = Math.min(progressPercentage.value + 8, 90)
    }, 200)
    progressText.value = '計画データを更新中...'
    const res = await updateProductionSummarysPlan(startDate)
    if (progressTimer) clearInterval(progressTimer)
    progressTimer = null
    progressPercentage.value = 100
    progressStatus.value = 'success'
    const body = (res as any)?.data ?? {}
    const d = body?.data ?? body
    const msg = body?.message ?? `更新 ${d?.updated ?? 0} 件、スキップ ${d?.skipped ?? 0} 件`
    progressText.value = msg
    ElMessage.success(msg)
    setTimeout(() => {
      showProgressDialog.value = false
      setTimeout(() => fetchData(), 500)
    }, 1500)
  } catch (error: any) {
    if (progressTimer) clearInterval(progressTimer)
    progressPercentage.value = 100
    progressStatus.value = 'exception'
    progressText.value = '計画データ更新に失敗しました'
    ElMessage.error(error?.response?.data?.detail ?? error?.response?.data?.message ?? error?.message ?? '計画データ更新に失敗しました')
    setTimeout(() => { showProgressDialog.value = false }, 2000)
  } finally {
    updatingPlan.value = false
  }
}

const handleInventoryTrendUpdate = () => {
  showInventoryTrendUpdateConfirmDialog.value = true
}

const confirmInventoryTrendUpdate = async () => {
  showInventoryTrendUpdateConfirmDialog.value = false
  updatingInventoryTrend.value = true
  const startDate = getFirstDayOfCurrentMonth()
  try {
    await runInventoryTrendUpdateSequence(startDate)
  } catch (_e) {
    /* runInventoryTrendUpdateSequence 内でメッセージ表示済み */
  } finally {
    updatingInventoryTrend.value = false
  }
}

// ── 製品マスタ更新 ─────────────────────
const handleUpdateProductMaster = () => {
  // 初期期間：表示中の dateRange があればそれを使う、なければ createDefaultDateRange
  if (dateRange.value && dateRange.value.length === 2) {
    productMasterDateRange.value = [dateRange.value[0], dateRange.value[1]]
  } else {
    productMasterDateRange.value = createDefaultDateRange()
  }
  showProductMasterUpdateDialog.value = true
}

const confirmUpdateProductMaster = async () => {
  if (!productMasterDateRange.value || productMasterDateRange.value.length !== 2) {
    ElMessage.warning('更新期間を選択してください')
    return
  }
  const startDate = productMasterDateRange.value[0]
  const endDate = productMasterDateRange.value[1]
  try {
    await ElMessageBox.confirm(
      `製品マスタを更新します。\n期間: ${startDate} ～ ${endDate}`,
      '製品マスタ更新確認',
      { confirmButtonText: '更新', cancelButtonText: 'キャンセル', type: 'info' },
    )
  } catch {
    return
  }
  showProductMasterUpdateDialog.value = false
  updatingProductMaster.value = true
  showProgressDialog.value = true
  progressPercentage.value = 0
  progressStatus.value = ''
  progressText.value = '製品マスタデータを更新中...'
  let progressTimer: ReturnType<typeof setInterval> | null = null
  try {
    progressTimer = setInterval(() => {
      if (progressPercentage.value < 90) progressPercentage.value = Math.min(progressPercentage.value + 5, 90)
    }, 200)
    const res = await updateProductionSummarysProductMaster({ startDate, endDate })
    if (progressTimer) clearInterval(progressTimer)
    progressTimer = null
    progressPercentage.value = 100
    progressStatus.value = 'success'
    const body = (res as any)?.data ?? {}
    const d = body?.data ?? body
    const updated = d?.updated ?? 0
    const skipped = d?.skipped ?? 0
    const elapsed = d?.elapsedTime ?? 0
    progressText.value = `更新 ${updated} 件 / スキップ ${skipped} 件\n期間: ${startDate} ～ ${endDate}\n処理時間: ${elapsed}s`
    ElMessage.success(`製品マスタの更新が完了しました（${updated}件）`)
    setTimeout(() => {
      showProgressDialog.value = false
      setTimeout(() => fetchData(), 500)
    }, 1500)
  } catch (error: any) {
    if (progressTimer) clearInterval(progressTimer)
    progressPercentage.value = 100
    progressStatus.value = 'exception'
    progressText.value = '製品マスタ更新に失敗しました'
    ElMessage.error(error?.response?.data?.detail ?? error?.response?.data?.message ?? error?.message ?? '製品マスタ更新に失敗しました')
    setTimeout(() => { showProgressDialog.value = false }, 2000)
  } finally {
    updatingProductMaster.value = false
  }
}

// ── 設備フィールド更新 ─────────────────────
const handleUpdateMachine = () => {
  if (dateRange.value && dateRange.value.length === 2) {
    machineDateRange.value = [dateRange.value[0], dateRange.value[1]]
  } else {
    machineDateRange.value = createDefaultDateRange()
  }
  showMachineUpdateDialog.value = true
}

const confirmUpdateMachine = async () => {
  if (!machineDateRange.value || machineDateRange.value.length !== 2) {
    ElMessage.warning('更新期間を選択してください')
    return
  }
  const startDate = machineDateRange.value[0]
  const endDate = machineDateRange.value[1]
  try {
    await ElMessageBox.confirm(
      `機器フィールドを更新します。\n期間: ${startDate} ～ ${endDate}`,
      '機器フィールド更新確認',
      { confirmButtonText: '更新', cancelButtonText: 'キャンセル', type: 'info' },
    )
  } catch {
    return
  }
  showMachineUpdateDialog.value = false
  updatingMachine.value = true
  showProgressDialog.value = true
  progressPercentage.value = 0
  progressStatus.value = ''
  progressText.value = '機器フィールドデータを更新中...'
  let progressTimer: ReturnType<typeof setInterval> | null = null
  try {
    progressTimer = setInterval(() => {
      if (progressPercentage.value < 90) progressPercentage.value = Math.min(progressPercentage.value + 5, 90)
    }, 200)
    const res = await updateProductionSummarysMachine({ startDate, endDate })
    if (progressTimer) clearInterval(progressTimer)
    progressTimer = null
    progressPercentage.value = 100
    progressStatus.value = 'success'
    const body = (res as any)?.data ?? {}
    const d = body?.data ?? body
    const updated = d?.updated ?? 0
    const skipped = d?.skipped ?? 0
    const elapsed = d?.elapsedTime ?? 0
    progressText.value = `更新 ${updated} 件 / スキップ ${skipped} 件\n期間: ${startDate} ～ ${endDate}\n処理時間: ${elapsed}s`
    ElMessage.success(`機器フィールドの更新が完了しました（${updated}件）`)
    setTimeout(() => {
      showProgressDialog.value = false
      setTimeout(() => fetchData(), 500)
    }, 1500)
  } catch (error: any) {
    if (progressTimer) clearInterval(progressTimer)
    progressPercentage.value = 100
    progressStatus.value = 'exception'
    progressText.value = '機器フィールド更新に失敗しました'
    ElMessage.error(error?.response?.data?.detail ?? error?.response?.data?.message ?? error?.message ?? '機器フィールド更新に失敗しました')
    setTimeout(() => { showProgressDialog.value = false }, 2000)
  } finally {
    updatingMachine.value = false
  }
}

// スマホ・タブレット用「その他」Drawer で項目選択時
const onOthersDrawerSelect = (command: string) => {
  showOthersDrawer.value = false
  handleDropdownCommand(command)
}

// ── その他ドロップダウン（command で実行。本番ビルドで @click が効かない問題を回避） ──
const handleDropdownCommand = (command: string) => {
  switch (command) {
    case 'generate':
      handleGenerateData()
      break
    case 'all-update':
      handleAllUpdate()
      break
    case 'update-order':
      handleUpdateFromOrderDaily()
      break
    case 'batch-initial':
      openBatchInitialStockDialog()
      break
    case 'carry-over':
      handleUpdateCarryOver()
      break
    case 'actual':
      handleUpdateActual()
      break
    case 'defect':
      handleUpdateDefect()
      break
    case 'scrap':
      handleUpdateScrap()
      break
    case 'on-hold':
      handleUpdateOnHold()
      break
    case 'production-dates':
      handleUpdateProductionDates()
      break
    case 'plan':
      handleUpdatePlan()
      break
    case 'inventory-trend':
      handleInventoryTrendUpdate()
      break
    case 'product-master':
      handleUpdateProductMaster()
      break
    case 'machine':
      handleUpdateMachine()
      break
    case 'batch-actual':
      handleOpenBatchActualDialog()
      break
    case 'print-rec-plating':
      handleRecommendedProductionPrint('plating')
      break
    case 'print-rec-molding':
      handleRecommendedProductionPrint('molding')
      break
    case 'print-rec-molding-plan':
      handleRecommendedProductionPrint('molding', {
        trendKeyOverride: 'molding_actual_plan_trend',
        titleOverride: '成型計画推奨生産日リスト',
        pickDateKeyOverride: 'molding_production_date',
        hidePreInventoryColumns: true,
      })
      break
    default:
      break
  }
}

const handleRecommendedPrintCommand = (command: string) => {
  if (command === 'print-rec-plating') handleRecommendedProductionPrint('plating')
  else if (command === 'print-rec-molding') handleRecommendedProductionPrint('molding')
  else if (command === 'print-rec-molding-plan') {
    handleRecommendedProductionPrint('molding', {
      trendKeyOverride: 'molding_actual_plan_trend',
      titleOverride: '成型計画推奨生産日リスト',
      pickDateKeyOverride: 'molding_production_date',
      hidePreInventoryColumns: true,
    })
  }
}

// ── 全部一括更新 ─────────────────────
const handleAllUpdate = () => {
  showAllUpdateConfirmDialog.value = true
}

// 全部一括更新確認ダイアログの「一括更新開始」用（本番ビルドで el-button @click が効かないため原生 button から呼ぶ）
const onAllUpdateConfirmClick = () => {
  confirmAllUpdate()
}

// crypto.randomUUID が無い環境（古いブラウザ・非 HTTPS 等）用のフォールバック
function getRandomUUID(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  const buf = new Uint8Array(16)
  if (typeof crypto !== 'undefined' && crypto.getRandomValues) {
    crypto.getRandomValues(buf)
  } else {
    for (let i = 0; i < 16; i++) buf[i] = Math.floor(Math.random() * 256)
  }
  buf[6] = (buf[6]! & 0x0f) | 0x40
  buf[8] = (buf[8]! & 0x3f) | 0x80
  const hex = Array.from(buf, b => b.toString(16).padStart(2, '0')).join('')
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
}

const confirmAllUpdate = async () => {
  showAllUpdateConfirmDialog.value = false
  const lockValue = getRandomUUID()
  try {
    await acquireBatchUpdateLock(lockValue)
  } catch (e: unknown) {
    const status = (e as { response?: { status?: number } })?.response?.status
    if (status === 423) {
      ElMessage.warning('他の端末で一括更新が実行中のため、しばらく待ってから再度お試しください。')
      return
    }
    ElMessage.error('ロックの取得に失敗しました。')
    return
  }
  updatingAll.value = true
  showProgressDialog.value = true
  progressStatus.value = ''
  progressDialogTitle.value = '一括更新中'
  const results: { name: string; success: boolean }[] = []
  const stepNames = [
    '受注データ更新',
    '実績データ更新',
    '不良データ更新',
    '廃棄データ更新',
    '保留データ更新',
    '計画データ更新',
  ]
  const steps = [
    () => updateProductionSummarysFromOrderDaily({ updateMode: 'all' }),
    () => updateProductionSummarysActual(),
    () => updateProductionSummarysDefect(),
    () => updateProductionSummarysScrap(),
    () => updateProductionSummarysOnHold(),
    async () => {
      const startDate = getFirstDayOfCurrentMonth()
      try {
        await clearProductionSummarysPlanFields(startDate)
      } catch (_e) {
        // クリア失敗時も更新を継続
      }
      await updateProductionSummarysPlan(startDate)
    },
  ]
  try {
    for (let i = 0; i < steps.length; i++) {
      progressPercentage.value = Math.round(((i + 1) / 7) * 90)
      progressText.value = `${stepNames[i]}を実行中... (${i + 1}/7)`
      try {
        await steps[i]()
        results.push({ name: stepNames[i], success: true })
      } catch (_e) {
        results.push({ name: stepNames[i], success: false })
      }
      await new Promise(r => setTimeout(r, 300))
    }
    // 步骤 7: 在庫・推移更新（当月月初以降をクリアしてから再計算）
    const startDate = getFirstDayOfCurrentMonth()
    try {
      await clearProductionSummarysCalculatedFields(startDate)
    } catch (_e) {
      // 清空失败不记入 results，继续执行在庫・推移
    }
    progressPercentage.value = 92
    progressText.value = '在庫・推移更新を実行中... (7/7)'
    try {
      await updateProductionSummarysInventory(startDate)
      results.push({ name: '在庫更新', success: true })
    } catch (_e) {
      results.push({ name: '在庫更新', success: false })
    }
    await new Promise(r => setTimeout(r, 300))
    try {
      await updateProductionSummarysTrend(startDate)
      results.push({ name: '推移更新', success: true })
    } catch (_e) {
      results.push({ name: '推移更新', success: false })
    }
    await new Promise(r => setTimeout(r, 300))
    progressText.value = '安全在庫を更新中...'
    try {
      await updateProductionSummarysSafetyStock(startDate)
      results.push({ name: '安全在庫更新', success: true })
    } catch (_e) {
      results.push({ name: '安全在庫更新', success: false })
    }
    progressPercentage.value = 100
    progressStatus.value = 'success'
    const successCount = results.filter(r => r.success).length
    const failCount = results.filter(r => !r.success).length
    const failedNames = results.filter(r => !r.success).map(r => r.name)
    progressText.value = failCount === 0
      ? '全部一括更新が完了しました！'
      : `全部一括更新が完了しました（成功 ${successCount} / 失敗 ${failCount}）\n失敗: ${failedNames.join('、')}`
    if (failCount === 0) {
      ElMessage.success('全部一括更新が完了しました')
    } else {
      ElMessage.warning(`一部失敗しました: ${failedNames.join('、')}`)
    }
    setTimeout(() => {
      showProgressDialog.value = false
      updatingAll.value = false
      setTimeout(() => fetchData(), 500)
    }, 1500)
  } finally {
    try {
      await releaseBatchUpdateLock(lockValue)
    } catch (_e) {
      /* 解放失敗は無視（ロックは有効期限で自動解放） */
    }
  }
}

const confirmGenerateData = async () => {
  showGenerateConfirmDialog.value = false
  const startDateStr = generateDateRange.value.start
  const endDateStr = generateDateRange.value.end
  if (!startDateStr || !endDateStr) return
  generating.value = true
  showProgressDialog.value = true
  progressDialogTitle.value = 'データ生成中'
  progressPercentage.value = 0
  progressStatus.value = ''
  progressText.value = 'データ生成中...'
  let progressTimer: ReturnType<typeof setInterval> | null = null
  try {
    progressTimer = setInterval(() => {
      if (progressPercentage.value < 95) {
        progressPercentage.value = Math.min(progressPercentage.value + Math.random() * 8 + 4, 95)
      }
    }, 300)
    await generateProductionSummarys({ startDate: startDateStr, endDate: endDateStr })
    if (progressTimer) clearInterval(progressTimer)
    progressTimer = null
    progressPercentage.value = 100
    progressStatus.value = 'success'
    progressText.value = 'データ生成が完了しました！'
    setTimeout(() => {
      showProgressDialog.value = false
      ElMessage.success('データ生成が完了しました')
      fetchData()
    }, 1500)
  } catch (error: any) {
    if (progressTimer) clearInterval(progressTimer)
    progressPercentage.value = 100
    progressStatus.value = 'exception'
    progressText.value = 'データ生成に失敗しました'
    setTimeout(() => {
      showProgressDialog.value = false
      ElMessage.error(error?.response?.data?.detail || error?.message || 'データ生成に失敗しました')
    }, 2000)
  } finally {
    generating.value = false
  }
}

const fetchData = async () => {
  loading.value = true
  try {
    const params: any = {
      page: currentPage.value,
      limit: pageSize.value,
      sortBy: sortBy.value,
      sortOrder: sortOrder.value,
    }
    if (dateRange.value && dateRange.value.length === 2) {
      params.startDate = dateRange.value[0]
      params.endDate = dateRange.value[1]
    }
    if (filterProductCd.value) params.productCd = filterProductCd.value
    if (filterKeyword.value.trim()) params.keyword = filterKeyword.value.trim()

    const response: any = await getProductionSummarysList(params)
    lastRefreshTime.value = new Date().toLocaleString('ja-JP', { hour12: false })

    if (response?.data?.list) {
      tableData.value = response.data.list
      total.value = response.data.pagination?.total ?? 0
    } else {
      tableData.value = []
      total.value = 0
    }
  } catch {
    ElMessage.error('データの取得に失敗しました')
    tableData.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

const fetchProductList = async () => {
  try {
    const response: any = await getProductionSummarysProducts()
    const list = response?.data ?? (Array.isArray(response) ? response : [])
    const sortByName = (arr: Array<{ product_cd: string; product_name?: string }>) =>
      [...arr].sort((a, b) => (a.product_name || '').localeCompare(b.product_name || '') || (a.product_cd || '').localeCompare(b.product_cd || ''))
    productList.value = sortByName(list)
  } catch {
    productList.value = []
  }
}

// ---------- 実績一括登録 ----------
function getEmptyBatchActualRow() {
  return {
    product_cd: '',
    product_name: '',
    date: '',
    cuttingActual: null as number | null,
    chamferingActual: null as number | null,
    moldingActual: null as number | null,
  }
}
function handleResetBatchActual() {
  batchActualTableData.value = [
    { ...getEmptyBatchActualRow() },
    { ...getEmptyBatchActualRow() },
  ]
  if (batchActualDate.value) {
    batchActualTableData.value.forEach((r) => { r.date = batchActualDate.value })
  }
}
function handleOpenBatchActualDialog() {
  if (!batchActualDate.value) {
    batchActualDate.value = createDefaultDateRange()[0]
  }
  handleResetBatchActual()
  showBatchActualDialog.value = true
}
function handleBatchActualDateChange() {
  const d = batchActualDate.value || ''
  batchActualTableData.value.forEach((r) => { r.date = d })
}
function handleBatchActualProductChange(row: { product_cd: string; product_name: string }, productCd: string) {
  const p = productList.value.find((x) => x.product_cd === productCd)
  row.product_name = p?.product_name ?? ''
}
async function handleSubmitBatchActual() {
  if (!batchActualDate.value) {
    ElMessage.warning('日付を選択してください')
    return
  }
  const validRows = batchActualTableData.value.filter((r) => r.product_cd && r.product_cd.trim())
  if (validRows.length === 0) {
    ElMessage.warning('少なくとも1つの製品を選択してください')
    return
  }
  const hasAnyActual = validRows.some(
    (r) =>
      (r.cuttingActual != null && Number(r.cuttingActual) !== 0) ||
      (r.chamferingActual != null && Number(r.chamferingActual) !== 0) ||
      (r.moldingActual != null && Number(r.moldingActual) !== 0),
  )
  if (!hasAnyActual) {
    ElMessage.warning('少なくとも1つの実績を入力してください')
    return
  }
  const transactionTime = `${batchActualDate.value} 00:00:00`
  const transactions: Array<{ product_cd: string; process_cd: string; quantity: number; transaction_time: string }> = []
  for (const row of validRows) {
    if (row.cuttingActual != null && Number(row.cuttingActual) !== 0) {
      transactions.push({
        product_cd: row.product_cd,
        process_cd: 'KT01',
        quantity: Number(row.cuttingActual),
        transaction_time: transactionTime,
      })
    }
    if (row.chamferingActual != null && Number(row.chamferingActual) !== 0) {
      transactions.push({
        product_cd: row.product_cd,
        process_cd: 'KT02',
        quantity: Number(row.chamferingActual),
        transaction_time: transactionTime,
      })
    }
    if (row.moldingActual != null && Number(row.moldingActual) !== 0) {
      transactions.push({
        product_cd: row.product_cd,
        process_cd: 'KT04',
        quantity: Number(row.moldingActual),
        transaction_time: transactionTime,
      })
    }
  }
  if (transactions.length === 0) {
    ElMessage.warning('登録する実績データがありません')
    return
  }
  batchActualSaving.value = true
  try {
    const res = await request.post<{ message?: string; data?: { success?: number; failed?: number } }>(
      `${STOCK_LOGS_BASE}/batch-actual`,
      { transactions },
    )
    const data = (res as any)?.data ?? res
    const msg = data?.message ?? `実績データを${transactions.length}件登録しました`
    ElMessage.success(msg)
    showBatchActualDialog.value = false
    handleResetBatchActual()
    setTimeout(() => fetchData(), 500)
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail ?? error?.response?.data?.message ?? error?.message ?? '実績一括登録に失敗しました')
  } finally {
    batchActualSaving.value = false
  }
}

const PRODUCT_ROUTE_BASE = '/api/master/product/process/routes'
/** 取得製品工程ルートステップ（工程校验用） */
async function getProductRouteSteps(productCd: string): Promise<Array<{ process_cd: string }>> {
  try {
    const raw = await request.get<{ route_cd?: string }>(`${PRODUCT_ROUTE_BASE}/${encodeURIComponent(productCd)}`)
    const info = (raw as any)?.data ?? raw
    const routeCd = (info as { route_cd?: string })?.route_cd
    if (!routeCd) return []
    const steps = await request.get<Array<{ process_cd: string }>>(
      `${PRODUCT_ROUTE_BASE}/${encodeURIComponent(productCd)}/${encodeURIComponent(routeCd)}`
    )
    return Array.isArray(steps) ? steps : (steps as any)?.data ?? []
  } catch {
    return []
  }
}

function getProcessName(processCd: string): string {
  const opt = processOptions.value.find((p) => p.cd === processCd)
  return opt?.name ?? processCd
}

async function ensureProcessOptions() {
  if (processOptions.value.length > 0) return
  try {
    const res = await request.get<Array<{ cd: string; name: string }>>('/api/master/processes/options')
    processOptions.value = Array.isArray(res) ? res : (res as { data?: Array<{ cd: string; name: string }> })?.data ?? []
  } catch {
    processOptions.value = []
  }
}

function handleCellDoubleClick(
  row: Record<string, any>,
  column: { property?: string },
  _cell: HTMLElement,
  _event: MouseEvent
) {
  const prop = column?.property
  if (!prop || basicColumns.has(prop)) return
  if (
    prop === 'pre_plating_inventory' ||
    prop === 'pre_plating_prev_process' ||
    prop === 'pre_molding_inventory' ||
    prop === 'pre_molding_prev_process'
  )
    return
  const parts = prop.split('_')
  let processCd: string | null = null
  for (let i = 1; i <= parts.length; i++) {
    const prefix = parts.slice(0, i).join('_')
    if (processFieldToProcessCd[prefix]) {
      processCd = processFieldToProcessCd[prefix]
      break
    }
  }
  if (!processCd) {
    ElMessage.warning('該当する工程が見つかりません')
    return
  }
  const productCd = (row.product_cd ?? '').toString().trim()
  if (!productCd) return
  if (processCd !== 'KT13') {
    getProductRouteSteps(productCd).then((steps) => {
      const hasProcess = steps.some((s) => (s.process_cd || '').trim() === processCd)
      if (steps.length > 0 && !hasProcess) {
        ElMessage.warning('製品は工程に属していません')
        return
      }
      openTransactionDialog(row, processCd)
    }).catch(() => openTransactionDialog(row, processCd))
  } else {
    openTransactionDialog(row, processCd)
  }
}

function openTransactionDialog(row: Record<string, any>, processCd: string) {
  const dateVal = row.date
  const dateStr = dateVal
    ? (typeof dateVal === 'string' ? dateVal.slice(0, 10) : String(dateVal).slice(0, 10))
    : ''
  ensureProcessOptions()
  transactionInputInfo.value = {
    date: dateStr,
    productCd: (row.product_cd ?? '').toString().trim(),
    productName: (row.product_name ?? '').toString().trim(),
    processCd,
    processName: getProcessName(processCd),
  }
  transactionForm.value = {
    actual: null,
    defect: null,
    scrap: null,
    onHold: null,
    inbound: null,
    outbound: null,
  }
  showTransactionInputDialog.value = true
}

function getTransactionTime(dateStr: string): string {
  const now = new Date()
  const h = String(now.getHours()).padStart(2, '0')
  const m = String(now.getMinutes()).padStart(2, '0')
  const s = String(now.getSeconds()).padStart(2, '0')
  return `${dateStr} ${h}:${m}:${s}`
}

async function handleSubmitTransaction() {
  const info = transactionInputInfo.value
  const form = transactionForm.value
  const processCd = info.processCd
  const dateStr = info.date
  if (!dateStr || !info.productCd) {
    ElMessage.warning('日付・製品が設定されていません')
    return
  }
  const transactionTime = getTransactionTime(dateStr)
  if (processCd === 'KT13') {
    const hasQty =
      (form.inbound != null && Number(form.inbound) !== 0) ||
      (form.outbound != null && Number(form.outbound) !== 0) ||
      (form.scrap != null && Number(form.scrap) !== 0) ||
      (form.onHold != null && Number(form.onHold) !== 0)
    if (!hasQty) {
      ElMessage.warning('少なくとも1つの数量を入力してください')
      return
    }
  } else if (processCd === 'KT15') {
    const hasQty =
      (form.actual != null && Number(form.actual) !== 0) || (form.scrap != null && Number(form.scrap) !== 0)
    if (!hasQty) {
      ElMessage.warning('少なくとも1つの数量を入力してください')
      return
    }
  } else {
    const hasQty =
      (form.actual != null && Number(form.actual) !== 0) ||
      (form.defect != null && Number(form.defect) !== 0) ||
      (form.scrap != null && Number(form.scrap) !== 0) ||
      (form.onHold != null && Number(form.onHold) !== 0)
    if (!hasQty) {
      ElMessage.warning('少なくとも1つの数量を入力してください')
      return
    }
  }
  const insertPromises: Promise<unknown>[] = []
  const stockType =
    processCd === 'KT13' || processCd === 'KT09' || processCd === 'KT15' ? '製品' : '仕掛品'
  const locationCd =
    processCd === 'KT15'
      ? '外注倉庫'
      : (info.processName || '').includes('倉庫')
        ? '製品倉庫'
        : '工程中間在庫'
  const unit = processCd === 'KT09' ? '本' : null
  const baseBody: Record<string, any> = {
    target_cd: info.productCd,
    process_cd: processCd,
    transaction_time: transactionTime,
    source_file: '生産データ管理',
  }
  if (processCd === 'KT13') {
    const add = (type: string, qty: number | null) => {
      if (qty == null || Number(qty) === 0) return
      insertPromises.push(
        request.post(STOCK_LOGS_BASE, {
          ...baseBody,
          stock_type: stockType,
          location_cd: locationCd,
          transaction_type: type,
          quantity: Number(qty),
          unit: unit ?? undefined,
        })
      )
    }
    add('入庫', form.inbound)
    add('出庫', form.outbound)
    add('廃棄', form.scrap)
    add('保留', form.onHold)
  } else if (processCd === 'KT15') {
    if (form.actual != null && Number(form.actual) !== 0) {
      insertPromises.push(
        request.post(STOCK_LOGS_BASE, {
          ...baseBody,
          stock_type: stockType,
          location_cd: '外注倉庫',
          transaction_type: '入庫',
          quantity: Number(form.actual),
          unit: unit ?? undefined,
        })
      )
    }
    if (form.scrap != null && Number(form.scrap) !== 0) {
      insertPromises.push(
        request.post(STOCK_LOGS_BASE, {
          ...baseBody,
          stock_type: stockType,
          location_cd: '外注倉庫',
          transaction_type: '廃棄',
          quantity: Number(form.scrap),
          unit: unit ?? undefined,
        })
      )
    }
  } else {
    const add = (type: string, qty: number | null) => {
      if (qty == null || Number(qty) === 0) return
      insertPromises.push(
        request.post(STOCK_LOGS_BASE, {
          ...baseBody,
          stock_type: stockType,
          location_cd: locationCd,
          transaction_type: type,
          quantity: Number(qty),
          unit: unit ?? undefined,
        })
      )
    }
    add('実績', form.actual)
    add('不良', form.defect)
    add('廃棄', form.scrap)
    add('保留', form.onHold)
  }
  if (insertPromises.length === 0) {
    ElMessage.warning('少なくとも1つの数量を入力してください')
    return
  }
  submittingTransaction.value = true
  try {
    await Promise.all(insertPromises)
    ElMessage.success('在庫取引ログを登録しました')
    showTransactionInputDialog.value = false
    setTimeout(() => fetchData(), 500)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail ?? e?.response?.data?.message ?? e?.message ?? '登録に失敗しました')
  } finally {
    submittingTransaction.value = false
  }
}

const handleFilterChange = () => {
  currentPage.value = 1
  fetchData()
}
const handleKeywordInput = () => {
  if (keywordFilterTimer) clearTimeout(keywordFilterTimer)
  keywordFilterTimer = setTimeout(handleFilterChange, 400)
}
const handleKeywordClear = () => {
  if (keywordFilterTimer) clearTimeout(keywordFilterTimer)
  keywordFilterTimer = null
  handleFilterChange()
}
const shiftDateRange = (offset: number) => {
  const current = dateRange.value && dateRange.value.length === 2 ? dateRange.value : createDefaultDateRange()
  const start = parseDateString(current[0])
  const end = parseDateString(current[1])
  start.setDate(start.getDate() + offset)
  end.setDate(end.getDate() + offset)
  dateRange.value = [formatDateToString(start), formatDateToString(end)]
  handleFilterChange()
}
const setTodayRange = () => {
  dateRange.value = createDefaultDateRange()
  handleFilterChange()
}
const handleSortChange = ({ prop, order }: { prop: string; order: string | null }) => {
  if (prop && order) {
    sortBy.value = prop
    sortOrder.value = order === 'ascending' ? 'ASC' : 'DESC'
  } else {
    sortBy.value = 'product_name'
    sortOrder.value = 'ASC'
  }
  fetchData()
}
const handlePageChange = () => fetchData()
const handleRefresh = () => fetchData()

/** プレビュー用ウィンドウに HTML を描画した後、短い遅延で print() する（描画→印刷ダイアログの順） */
const PRINT_PREVIEW_BEFORE_DIALOG_MS = 400

/** 印刷ダイアログ／プレビューを閉じたあと子 window を閉じる（子 document 内で確実に afterprint 等を取る） */
function appendAutoClosePrintWindowScript(html: string): string {
  const snippet =
    '<script>(function(){var done=0;function z(){if(done)return;done=1;setTimeout(function(){try{window.close()}catch(e){}},100);}' +
    'window.addEventListener("afterprint",z);window.onafterprint=z;' +
    'try{var mq=window.matchMedia("print");var saw=0;var q=function(){if(mq.matches)saw=1;else if(saw){z();mq.removeEventListener("change",q);}};' +
    '(mq.addEventListener?mq.addEventListener("change",q):mq.addListener(q));}catch(e){}' +
    'var bp=0;window.addEventListener("beforeprint",function(){bp=1});' +
    'document.addEventListener("visibilitychange",function(){if(done)return;if(bp&&document.visibilityState==="visible")setTimeout(z,500);});' +
    '})();<\\/script>'
  if (/<\/body>\s*<\/html>/i.test(html)) {
    return html.replace(/<\/body>\s*<\/html>/i, `${snippet}</body></html>`)
  }
  if (/<\/body>/i.test(html)) {
    return html.replace(/<\/body>/i, `${snippet}</body>`)
  }
  return html + snippet
}

function openPrintPreviewThenDialog(html: string, options?: { closeAfterPrint?: boolean }): Window | null {
  const closeAfter = options?.closeAfterPrint !== false
  const w = window.open('', '_blank')
  if (!w) return null
  const htmlWithClose = closeAfter ? appendAutoClosePrintWindowScript(html) : html
  w.document.open()
  w.document.write(htmlWithClose)
  w.document.close()

  let printScheduled = false
  const schedulePrint = () => {
    if (printScheduled) return
    printScheduled = true
    window.setTimeout(() => {
      try {
        w.focus()
        w.print()
      } catch {
        /* ignore */
      }
    }, PRINT_PREVIEW_BEFORE_DIALOG_MS)
  }

  w.addEventListener('load', schedulePrint, { once: true })
  window.setTimeout(() => {
    try {
      if (w.document.readyState === 'complete') schedulePrint()
    } catch {
      schedulePrint()
    }
  }, 0)

  if (closeAfter) {
    let popupCloseDone = false
    const closePopup = () => {
      if (popupCloseDone) return
      popupCloseDone = true
      window.setTimeout(() => {
        try {
          if (!w.closed) w.close()
        } catch {
          /* ignore */
        }
      }, 150)
    }
    // 印刷実行・キャンセルいずれもダイアログ閉後に発火（Chromium / Firefox 想定）
    w.addEventListener('afterprint', closePopup)
    w.onafterprint = closePopup

    // 補助: 子窓の matchMedia（親でも登録。子の inline スクリプトと二重だが close は冪等）
    try {
      const mq = w.matchMedia('print')
      let sawPrintMedia = false
      const onPrintMq = () => {
        if (mq.matches) {
          sawPrintMedia = true
        } else if (sawPrintMedia) {
          closePopup()
          if (typeof mq.removeEventListener === 'function') {
            mq.removeEventListener('change', onPrintMq)
          } else {
            mq.removeListener(onPrintMq as (this: MediaQueryList, ev: MediaQueryListEvent) => void)
          }
        }
      }
      if (typeof mq.addEventListener === 'function') {
        mq.addEventListener('change', onPrintMq)
      } else {
        mq.addListener(onPrintMq as (this: MediaQueryList, ev: MediaQueryListEvent) => void)
      }
    } catch {
      /* ignore */
    }

    let sawBeforePrint = false
    try {
      w.addEventListener('beforeprint', () => {
        sawBeforePrint = true
      })
      w.document.addEventListener('visibilitychange', () => {
        if (popupCloseDone || !sawBeforePrint) return
        if (w.document.visibilityState === 'visible') {
          window.setTimeout(closePopup, 600)
        }
      })
    } catch {
      /* ignore */
    }
  }
  return w
}

const handlePrint = () => {
  const printData = tableData.value
  const baseCols = [
    { prop: 'date', label: '日付', type: 'date' },
    { prop: 'product_cd', label: '製品CD', type: 'text' },
    { prop: 'product_name', label: '製品名', type: 'text' },
  ]
  const dynCols = dynamicColumns.value.filter((c) => visibleColumns.value[c.prop]).map((c) => ({ prop: c.prop, label: c.label, type: c.type }))
  const allCols = [...baseCols.filter((c) => visibleColumns.value[c.prop]), ...dynCols]
  const thead = allCols.map((c) => c.label).join('</th><th>')
  const tbody = printData
    .map((row) => {
      const cells = allCols.map((c) => {
        let v = row[c.prop]
        if (v == null || v === '') return '-'
        if (c.type === 'date' && typeof v === 'string') return formatDate(v)
        if (typeof v === 'number') return v.toLocaleString()
        return String(v)
      })
      return '<tr><td>' + cells.join('</td><td>') + '</td></tr>'
    })
    .join('')
  const html = `
    <!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"/><title>生産データ管理</title>
    <style>table{border-collapse:collapse;width:100%;font-size:11px}th,td{border:1px solid #e2e8f0;padding:6px 8px;text-align:center}th{background:#eef2ff;font-weight:600}</style>
    </head><body><h1>生産データ管理</h1><p>${dateRange.value ? dateRange.value.join(' ～ ') : ''} / ${printData.length}件</p>
    <table><thead><tr><th>${thead}</th></tr></thead><tbody>${tbody}</tbody></table></body></html>`
  const win = openPrintPreviewThenDialog(html)
  if (!win) {
    ElMessage.warning('ポップアップがブロックされました。ブラウザの設定でポップアップを許可してください。')
  }
}

// ---------- 工程別計画確認印刷 ----------
function handleProcessPrint() {
  printTargetDate.value = new Date().toISOString().split('T')[0]
  showPrintDateDialog.value = true
}

function addDays(dateStr: string, days: number): string {
  const d = new Date(dateStr + 'T12:00:00')
  d.setDate(d.getDate() + days)
  return d.toISOString().split('T')[0]
}

function buildProcessPrintHtml(allData: any[], targetDate: string): string {
  const toStr = (v: any) => (v == null || v === '' ? '' : typeof v === 'string' ? v : String(v))
  const dateStr = (row: any, key: string) => {
    const v = row[key]
    if (v == null) return '—'
    if (typeof v === 'string') return v.substring(0, 10)
    return toStr(v)
  }
  const num = (v: any) => (v != null && v !== '' ? Number(v) : null as number | null)
  const now = new Date().toLocaleString('ja-JP', { dateStyle: 'medium', timeStyle: 'short' })

  /** 同一製品で推移が最小の行を保つ（同値なら後に見つかった行＝従来の reduce と同じ） */
  const pickMinTrendRow = (prev: any | undefined, row: any, trendKey: string): any => {
    if (!prev) return row
    const tr = num(row[trendKey])
    const tp = num(prev[trendKey])
    if (tr == null) return prev
    if (tp == null) return row
    return tp < tr ? prev : row
  }

  const todayDataMap = new Map<string, any>()
  const moldingBest = new Map<string, any>()
  const platingBest = new Map<string, any>()
  const weldingBest = new Map<string, any>()
  const warehouseRows: any[] = []
  const warehouseSeen = new Set<string>()

  for (const row of allData) {
    const pid = row.product_cd
    const calD = row.date != null ? (typeof row.date === 'string' ? row.date.substring(0, 10) : toStr(row.date)) : ''

    if (pid && calD === targetDate) {
      todayDataMap.set(pid, row)
      const inv = num(row.warehouse_inventory) ?? num(row.inspection_inventory)
      if (inv != null && inv < 0 && !warehouseSeen.has(pid)) {
        warehouseSeen.add(pid)
        warehouseRows.push(row)
      }
    }

    if (!pid) continue

    if (dateStr(row, 'molding_production_date') === targetDate) {
      const tr = num(row.molding_trend)
      if (tr != null && tr < 0) moldingBest.set(pid, pickMinTrendRow(moldingBest.get(pid), row, 'molding_trend'))
    }
    if (dateStr(row, 'plating_production_date') === targetDate) {
      const tr = num(row.plating_trend)
      if (tr != null && tr < 0) platingBest.set(pid, pickMinTrendRow(platingBest.get(pid), row, 'plating_trend'))
    }
    if (dateStr(row, 'welding_production_date') === targetDate) {
      const tr = num(row.welding_trend)
      if (tr != null && tr < 0) weldingBest.set(pid, pickMinTrendRow(weldingBest.get(pid), row, 'welding_trend'))
    }
  }

  const bestRowsByProcessKey: Record<string, Map<string, any>> = {
    molding_production_date: moldingBest,
    plating_production_date: platingBest,
    welding_production_date: weldingBest,
  }

  const processConfigs = [
    {
      name: '成型工程',
      color: '#6366f1',
      productionDateKey: 'molding_production_date',
      trendKey: 'molding_trend',
      planKey: 'molding_plan',
      dateLabel: '推奨成型生産日',
      trendLabel: '成型推移',
      planLabel: '成型計画',
      hasPlan: true,
    },
    {
      name: 'メッキ工程',
      color: '#f59e0b',
      productionDateKey: 'plating_production_date',
      trendKey: 'plating_trend',
      planKey: 'plating_plan',
      dateLabel: '推奨メッキ生産日',
      trendLabel: 'メッキ推移',
      planLabel: 'メッキ計画',
      hasPlan: true,
    },
    {
      name: '溶接工程',
      color: '#10b981',
      productionDateKey: 'welding_production_date',
      trendKey: 'welding_trend',
      planKey: 'welding_plan',
      dateLabel: '推奨溶接生産日',
      trendLabel: '溶接推移',
      planLabel: '溶接計画',
      hasPlan: true,
    },
    {
      name: '倉庫',
      color: '#8b5cf6',
      productionDateKey: null,
      trendKey: null,
      planKey: null,
      dateLabel: '',
      trendLabel: '',
      planLabel: '',
      hasPlan: false,
    },
  ] as const

  let tablesHtml = ''
  for (const cfg of processConfigs) {
    let rows: any[] = []
    if (cfg.hasPlan && cfg.productionDateKey && cfg.trendKey) {
      rows = Array.from(bestRowsByProcessKey[cfg.productionDateKey].values())
    } else {
      rows = warehouseRows
    }
    rows = rows.sort((a, b) => (toStr(a.product_name || a.product_cd)).localeCompare(toStr(b.product_name || b.product_cd)))

    if (cfg.hasPlan && cfg.productionDateKey && cfg.trendKey && cfg.planKey) {
      tablesHtml += `<div class="process-block" style="margin-bottom:20px;break-inside:avoid;"><h2 style="color:${cfg.color};font-size:14px;margin:0 0 8px 0;">${cfg.name}</h2>
<table class="print-table"><thead><tr><th>製品名</th><th>${cfg.dateLabel}</th><th>${cfg.trendLabel}</th><th>${cfg.planLabel}</th><th>計画状態</th><th>確認</th></tr></thead><tbody>`
      for (const row of rows) {
        const todayRow = todayDataMap.get(row.product_cd)
        const planVal = todayRow ? num(todayRow[cfg.planKey]) : null
        const planState = planVal != null && planVal > 0 ? '生産計画あり' : '確認必要'
        const planClass = planVal != null && planVal > 0 ? 'plan-ok' : 'plan-warn'
        const trendVal = num(row[cfg.trendKey])
        const trendClass = trendVal != null && trendVal < 0 ? 'negative' : ''
        tablesHtml += `<tr><td>${escapeHtml(toStr(row.product_name || row.product_cd))}</td><td>${dateStr(row, cfg.productionDateKey!)}</td><td class="${trendClass}">${trendVal != null ? trendVal : '—'}</td><td>${row[cfg.planKey] != null ? row[cfg.planKey] : '—'}</td><td class="${planClass}">${planState}</td><td class="check-cell">□</td></tr>`
      }
      tablesHtml += '</tbody></table></div>'
    } else {
      tablesHtml += `<div class="process-block" style="margin-bottom:20px;break-inside:avoid;"><h2 style="color:${cfg.color};font-size:14px;margin:0 0 8px 0;">${cfg.name}</h2>
<table class="print-table"><thead><tr><th>製品名</th><th>検査在庫</th><th>倉庫在庫</th><th>確認</th></tr></thead><tbody>`
      for (const row of rows) {
        const inv = row.inspection_inventory != null ? Number(row.inspection_inventory) : '—'
        const wh = row.warehouse_inventory != null ? Number(row.warehouse_inventory) : '—'
        const invClass = typeof inv === 'number' && inv < 0 ? 'negative' : ''
        const whClass = typeof wh === 'number' && wh < 0 ? 'negative' : ''
        tablesHtml += `<tr><td>${escapeHtml(toStr(row.product_name || row.product_cd))}</td><td class="${invClass}">${inv}</td><td class="${whClass}">${wh}</td><td class="check-cell">□</td></tr>`
      }
      tablesHtml += '</tbody></table></div>'
    }
  }

  function escapeHtml(s: string) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
  }

  return `<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"/><title>工程別生産計画確認サマリー</title>
<style>
body{font-family: sans-serif; padding: 12px; font-size: 12px;}
@media print { body { padding: 0; } }
h1{font-size:16px;margin:0 0 4px 0;}
.subtitle{font-size:11px;color:#64748b;margin-bottom:16px;}
.print-table{border-collapse:collapse;width:100%;margin-bottom:8px;}
.print-table th,.print-table td{border:1px solid #cbd5e1;padding:6px 8px;text-align:left;}
.print-table th{background:#f1f5f9;font-weight:600;}
.print-table td.negative{color:#dc2626;}
.print-table td.plan-ok{background:#dcfce7;}
.print-table td.plan-warn{background:#fee2e2;}
.print-table td.check-cell{text-align:center;}
.process-block{page-break-inside:avoid;}
</style>
</head><body>
<h1>工程別生産計画確認サマリー(成型、メッキ、溶接、倉庫)</h1>
<p class="subtitle">対象日: ${targetDate} / 出力時間: ${now}</p>
${tablesHtml}
</body></html>`
}

async function fetchPrintData(targetDate: string) {
  const startDate = addDays(targetDate, -90)
  const endDate = addDays(targetDate, 90)
  const res = await getProductionSummarysList({ page: 1, limit: 50000, startDate, endDate })
  const data = (res as any)?.data ?? res
  const list = data?.list ?? (Array.isArray(res) ? res : [])
  return list
}

async function handleConfirmPrintDate() {
  if (!printTargetDate.value) {
    ElMessage.warning('日付を選択してください')
    return
  }
  const selectedDate = printTargetDate.value
  showPrintDateDialog.value = false
  showProgressDialog.value = true
  progressPercentage.value = 0
  progressStatus.value = ''
  progressText.value = '印刷データを取得中...'
  try {
    const allData = await fetchPrintData(selectedDate)
    if (!allData || allData.length === 0) {
      ElMessage.warning('印刷できるデータがありません。')
      return
    }
    const html = buildProcessPrintHtml(allData, selectedDate)
    const printWindow = openPrintPreviewThenDialog(html)
    if (!printWindow) {
      ElMessage.warning('ポップアップがブロックされました。ブラウザの設定でポップアップを許可してください。')
      return
    }
    ElMessage.success('プレビューを表示しました。しばらくして印刷ダイアログが開きます')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail ?? e?.message ?? '印刷データの取得に失敗しました')
  } finally {
    showProgressDialog.value = false
  }
}

/** 日別行のカレンダー日付 YYYY-MM-DD */
function rowCalendarDateStr(row: any): string {
  const v = row?.date
  if (v == null) return ''
  if (typeof v === 'string') return v.slice(0, 10)
  return String(v).slice(0, 10)
}

function numForRecommendedPrint(v: any): number | null {
  return v != null && v !== '' ? Number(v) : null
}

function escapeHtmlRecommended(s: string) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}

/** YYYY-MM-DD 比較用（空は最後） */
function productionDateYmdKey(row: any, prop: string): string {
  const v = row[prop]
  if (v == null || v === '') return '\uffff'
  if (typeof v === 'string') return v.slice(0, 10)
  return String(v).slice(0, 10)
}

function pickYmdForRecommendedPick(row: any, key: string): string {
  if (key === 'date') return rowCalendarDateStr(row) || '\uffff'
  return productionDateYmdKey(row, key)
}

/**
 * 推奨行 1 件に絞る（同一製品）：
 * - 过滤后的候选行里，先按「主キー」（最早日期）对比
 * - 主キー相同再按「副キー」对比
 * - 仍相同则按 trend 的更小值（更负）优先
 */
function pickBetterRecommendedRow(
  prev: any,
  row: any,
  trendKey: string,
  primaryDateKeyForPick: string,
  secondaryDateKeyForPick: string,
): any {
  const pa = pickYmdForRecommendedPick(row, primaryDateKeyForPick)
  const pb = pickYmdForRecommendedPick(prev, primaryDateKeyForPick)
  if (pa < pb) return row
  if (pb < pa) return prev

  const sa = pickYmdForRecommendedPick(row, secondaryDateKeyForPick)
  const sb = pickYmdForRecommendedPick(prev, secondaryDateKeyForPick)
  if (sa < sb) return row
  if (sb < sa) return prev

  const ta = numForRecommendedPrint(prev[trendKey]) ?? 0
  const tb = numForRecommendedPrint(row[trendKey]) ?? 0
  return ta <= tb ? prev : row
}

/**
 * 当月月初（JST）～取得終了日までの日別行から、製品ごとに trend&lt;0 の行から1行を選ぶ。
 * メッキ・成型とも **日付列 date が最も早い**行（同日内なら当工程 production_date 昇順、同順なら推移がより小さい方＝先勝ち）。
 */
function collectRecommendedProductionRows(
  allData: any[],
  monthStart: string,
  trendKey: string,
  kind: 'plating' | 'molding',
  options?: { primaryDateKeyForPick?: string },
): any[] {
  const productionDateKey = kind === 'plating' ? 'plating_production_date' : 'molding_production_date'
  const primaryDateKeyForPick = options?.primaryDateKeyForPick ?? 'date'
  const secondaryDateKeyForPick = primaryDateKeyForPick === 'date' ? productionDateKey : 'date'
  const bestByProduct = new Map<string, any>()
  for (const row of allData) {
    if (!row.product_cd) continue
    const d = rowCalendarDateStr(row)
    if (!d || d < monthStart) continue
    const trendVal = numForRecommendedPrint(row[trendKey])
    if (trendVal == null || trendVal >= 0) continue
    const pid = row.product_cd
    const prev = bestByProduct.get(pid)
    if (!prev) {
      bestByProduct.set(pid, row)
      continue
    }
    bestByProduct.set(
      pid,
      pickBetterRecommendedRow(prev, row, trendKey, primaryDateKeyForPick, secondaryDateKeyForPick),
    )
  }
  return Array.from(bestByProduct.values())
}

/** 治具／成型機名 → 推奨生産日 の順（メッキ・成型で同一ルール） */
function sortRecommendedPrintRows(rows: any[], kind: 'plating' | 'molding'): any[] {
  const machineKey = kind === 'plating' ? 'plating_machine' : 'molding_machine'
  const dateKey = kind === 'plating' ? 'plating_production_date' : 'molding_production_date'
  const dateKeyForSort = (row: any, key: string) => {
    const v = row[key]
    if (v == null || v === '') return '\uffff'
    if (typeof v === 'string') return v.slice(0, 10)
    return String(v).slice(0, 10)
  }
  const sortMachine = (m: string) => (m === '' ? '\uffff' : m)
  const copy = [...rows]
  copy.sort((a, b) => {
    const ma = sortMachine(String(a[machineKey] ?? '').trim())
    const mb = sortMachine(String(b[machineKey] ?? '').trim())
    const c = ma.localeCompare(mb, 'ja')
    if (c !== 0) return c
    const da = dateKeyForSort(a, dateKey)
    const db = dateKeyForSort(b, dateKey)
    return da.localeCompare(db)
  })
  return copy
}

function buildRecommendedProductionPrintHtml(
  rows: any[],
  kind: 'plating' | 'molding',
  monthStart: string,
  rangeEnd: string,
  options?: { titleOverride?: string; hidePreInventoryColumns?: boolean },
): string {
  const now = new Date().toLocaleString('ja-JP', { dateStyle: 'medium', timeStyle: 'short' })
  const pc =
    kind === 'plating'
      ? {
          title: 'メッキ推奨生産日リスト',
          machineHeading: 'メッキ治具',
          machineKey: 'plating_machine' as const,
          dateKey: 'plating_production_date' as const,
          dateLabel: '推奨生産日',
          preInvField: 'pre_plating_inventory' as const,
          prePrevField: 'pre_plating_prev_process' as const,
          invColHeader: 'メッキ前在庫',
          sumLabel: 'メッキ前在庫合計',
          footNote:
            'メッキ前在庫・直前工程は、工程ルート上でメッキ（または外注メッキ）の直前工程の前日15時の集計在庫です（一覧と同じ計算）。',
        }
      : {
          title: '成型推奨生産日リスト',
          machineHeading: '成型機',
          machineKey: 'molding_machine' as const,
          dateKey: 'molding_production_date' as const,
          dateLabel: '推奨生産日',
          preInvField: 'pre_molding_inventory' as const,
          prePrevField: 'pre_molding_prev_process' as const,
          invColHeader: '成型前在庫',
          sumLabel: '成型前在庫合計',
          footNote:
            '成型前在庫・直前工程は、工程ルート上で成型の直前工程の集計在庫です（一覧・メッキ前在庫と同じ算出方式）。',
        }

  const sheetTitle = options?.titleOverride ?? pc.title
  const hidePreInvCols = options?.hidePreInventoryColumns === true

  const dateCellPlain = (row: any, key: string) => {
    const v = row[key]
    if (v == null || v === '') return '—'
    if (typeof v === 'string') return escapeHtmlRecommended(v.substring(0, 10))
    return escapeHtmlRecommended(String(v))
  }

  const recommendedProdDateYmd = (row: any, key: string): string | null => {
    const v = row[key]
    if (v == null || v === '') return null
    if (typeof v === 'string') return v.length >= 10 ? v.slice(0, 10) : null
    const s = String(v)
    return s.length >= 10 ? s.slice(0, 10) : null
  }
  const todayJstYmdForPrint = (): string => {
    const { year, month, date } = getCurrentJSTInfo()
    return getJSTDateString(year, month, date)
  }
  const isRecommendedDateDueOrPast = (row: any, key: string): boolean => {
    const d = recommendedProdDateYmd(row, key)
    if (!d || d.length !== 10) return false
    return d <= todayJstYmdForPrint()
  }

  const sharedPageCss = `
@page { size: A4 portrait; margin: 10mm; }
*{box-sizing:border-box;}
body{font-family:sans-serif;margin:0;padding:12px;font-size:10.5pt;-webkit-print-color-adjust:exact;print-color-adjust:exact;}
@media print{body{padding:0;}}
h1.sheet-title{font-size:14pt;margin:0 0 6px 0;font-weight:700;}
p.subtitle{font-size:9pt;color:#64748b;margin:0 0 12px 0;}
`

  const printGridColumns = hidePreInvCols
    ? 'minmax(0, 1.25fr) 70px'
    : 'minmax(0, 1.25fr) 70px 70px 5.0em'

  const preInvPlain = (row: any) => {
    const v = row[pc.preInvField]
    if (v == null || v === '') return '—'
    const n = Number(v)
    if (Number.isNaN(n)) return '—'
    return escapeHtmlRecommended(n.toLocaleString('ja-JP'))
  }
  const prePrevPlain = (row: any) =>
    escapeHtmlRecommended(formatPrePlatingPrevKey(row[pc.prePrevField]))

  let blocks = ''
  let prevGroupKey: string | null = null
  for (const row of rows) {
    const mRaw = String(row[pc.machineKey] ?? '').trim()
    const groupKey = mRaw || '__empty__'
    if (groupKey !== prevGroupKey) {
      if (prevGroupKey !== null) {
        blocks += '</div></section>'
      }
      prevGroupKey = groupKey
      const mHeading = mRaw || '（未設定）'
      blocks += `<section class="machine-group"><header class="machine-title">${pc.machineHeading}: ${escapeHtmlRecommended(mHeading)}</header>`
      blocks += `<div class="machine-body">`
      blocks += `<div class="col-head"><span class="ch-pname">製品名</span><span class="ch-date">${pc.dateLabel}</span>`
      if (!hidePreInvCols) {
        blocks += `<span class="ch-inv">${pc.invColHeader}</span><span class="ch-prev">直前工程</span>`
      }
      blocks += `</div>`
    }
    const pname = row.product_name || row.product_cd || ''
    const dateDueClass = isRecommendedDateDueOrPast(row, pc.dateKey) ? ' cell-date--due' : ''
    blocks += `<div class="item-row"><span class="cell-pname">${escapeHtmlRecommended(String(pname))}</span>`
    blocks += `<span class="cell-date${dateDueClass}">${dateCellPlain(row, pc.dateKey)}</span>`
    if (!hidePreInvCols) {
      blocks += `<span class="cell-inv">${preInvPlain(row)}</span><span class="cell-prev">${prePrevPlain(row)}</span>`
    }
    blocks += `</div>`
  }
  if (prevGroupKey !== null) {
    blocks += '</div></section>'
  }

  if (!rows.length) {
    blocks = '<p class="empty-msg">該当データがありません</p>'
  }

  const preInvSum = rows.reduce((sum, row) => {
    const v = row[pc.preInvField]
    if (v == null || v === '') return sum
    const n = Number(v)
    return Number.isNaN(n) ? sum : sum + n
  }, 0)
  const preInvSumStr = preInvSum.toLocaleString('ja-JP')

  return `<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"/><title>${sheetTitle}</title>
<style>${sharedPageCss}
.print-meta-row{display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px 20px;margin:0 0 10px 0;}
.print-meta-row .subtitle{flex:1;min-width:220px;margin:0;}
.subtitle-total{margin:0;padding-top:1px;font-size:9pt;color:#334155;text-align:right;white-space:nowrap;}
.subtitle-total strong{font-variant-numeric:tabular-nums;font-size:10pt;color:#0f172a;}
.columns-wrap{column-count:2;column-gap:14px;column-fill:auto;}
.machine-group{break-inside:avoid-page;page-break-inside:avoid;margin-bottom:12px;}
.machine-title{font-weight:700;background:#e2e8f0;padding:5px 8px;border:1px solid #94a3b8;border-bottom:none;}
.machine-body{padding:4px 8px 6px 14px;border:1px solid #cbd5e1;border-top:none;background:#fff;}
.col-head,.item-row{display:grid;grid-template-columns:${printGridColumns};column-gap:6px;row-gap:2px;font-size:9pt;}
.col-head{align-items:end;padding:2px 0 4px;border-bottom:1px solid #e2e8f0;margin-bottom:2px;font-size:8pt;color:#475569;font-weight:600;}
.item-row{align-items:center;padding:3px 0;border-bottom:1px solid #f1f5f9;font-size:9.5pt;}
.item-row:last-child{border-bottom:none;}
.ch-pname,.cell-pname{text-align:left;min-width:0;word-break:break-word;overflow-wrap:anywhere;}
.ch-date,.ch-inv,.ch-prev{text-align:center;justify-self:stretch;}
.ch-inv,.ch-prev{font-size:8.5pt;}
.cell-date,.cell-inv,.cell-prev{text-align:right;font-variant-numeric:tabular-nums;justify-self:stretch;}
.cell-date.cell-date--due{color:#dc2626;font-weight:700;}
.empty-msg{color:#64748b;font-size:10pt;}
.print-note{font-size:8pt;color:#64748b;margin:4px 0 0 0;line-height:1.35;}
</style></head><body>
<h1 class="sheet-title">${sheetTitle}</h1>
<div class="print-meta-row">
<p class="subtitle">対象期間: ${monthStart} ～ ${rangeEnd} / 出力: ${now}</p>
${hidePreInvCols ? '' : `<p class="subtitle-total">${pc.sumLabel}: <strong>${preInvSumStr}</strong></p>`}
</div>
${hidePreInvCols ? '' : `<p class="print-note">${pc.footNote}</p>`}
<div class="columns-wrap">${blocks}</div>
</body></html>`
}

async function handleRecommendedProductionPrint(
  kind: 'plating' | 'molding',
  options?: {
    trendKeyOverride?: string
    titleOverride?: string
    pickDateKeyOverride?: string
    hidePreInventoryColumns?: boolean
  },
) {
  const { start: monthStart, end: rangeEnd } = getGenerateDateRange()
  const prevTitle = progressDialogTitle.value
  showProgressDialog.value = true
  progressPercentage.value = 0
  progressStatus.value = ''
  progressDialogTitle.value = '推奨生産日'
  progressText.value = 'リスト用データを取得しています...'
  try {
    const res = await getProductionSummarysList({
      page: 1,
      limit: 50000,
      startDate: monthStart,
      endDate: rangeEnd,
    })
    const data = (res as any)?.data ?? res
    const list = data?.list ?? []
    const trendKey = options?.trendKeyOverride ?? (kind === 'plating' ? 'plating_trend' : 'molding_trend')
    const rawRows = collectRecommendedProductionRows(list, monthStart, trendKey, kind, {
      primaryDateKeyForPick: options?.pickDateKeyOverride,
    })
    const rows = sortRecommendedPrintRows(rawRows, kind)
    const html = buildRecommendedProductionPrintHtml(rows, kind, monthStart, rangeEnd, {
      titleOverride: options?.titleOverride,
      hidePreInventoryColumns: options?.hidePreInventoryColumns,
    })
    const printWindow = openPrintPreviewThenDialog(html)
    if (!printWindow) {
      ElMessage.warning('ポップアップがブロックされました。ブラウザの設定でポップアップを許可してください。')
      return
    }
    ElMessage.success(
      rows.length
        ? `プレビューを表示しました（${rows.length} 件）。しばらくして印刷ダイアログが開きます`
        : '該当行はありません。プレビュー後に印刷ダイアログが開きます',
    )
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail ?? e?.message ?? 'データの取得に失敗しました')
  } finally {
    progressDialogTitle.value = prevTitle
    showProgressDialog.value = false
  }
}

// ---------- 生産計画印刷（成型計画作成 / 溶接計画作成） ----------

const handleProductionPlanCommand = (command: string) => {
  if (command === 'molding-plan-create') openMoldingPlanDialog()
}

const showMoldingPlanDialog = ref(false)
const moldingPlanBaseDate = ref('')
const moldingPlanMonth = ref('')
const moldingPlanWorkingDays = ref(20)
const moldingPlanCoefficient = ref(1.043)
const moldingPlanLoading = ref(false)
const moldingPlanClearFromDate = ref('')
const moldingPlanClearLoading = ref(false)
const moldingPlanInventoryTrendLoading = ref(false)

/** 成型機器設定（product_machine_config）ダイアログ */
const showMoldingMachineConfigDialog = ref(false)
const moldingMachineConfigLoading = ref(false)
const moldingMachineConfigRows = ref<ProductMachineConfig[]>([])
const moldingMachineCdOptions = ref<Array<{ label: string; value: string }>>([])
const moldingMachineConfigSavingId = ref<number | null>(null)

function extractProductMachineConfigListResponse(response: any): ProductMachineConfig[] {
  if (!response) return []
  if (response.success && response.data?.list) return response.data.list
  if (Array.isArray(response.list)) return response.list
  if (Array.isArray(response)) return response
  return []
}

function extractMachinesListResponse(response: any): any[] {
  if (!response) return []
  if (Array.isArray(response)) return response
  if (Array.isArray(response.data?.list)) return response.data.list
  if (Array.isArray(response.list)) return response.list
  if (Array.isArray(response.data)) return response.data
  return []
}

const moldingMachineSelectOptionsWithLegacy = computed(() => {
  const base = moldingMachineCdOptions.value
  const seen = new Set(base.map((o) => o.value))
  const extra: { label: string; value: string }[] = []
  for (const r of moldingMachineConfigRows.value) {
    const v = (r.molding_machine ?? '').trim()
    if (v && !seen.has(v)) {
      seen.add(v)
      extra.push({ label: `${v}（マスタ外）`, value: v })
    }
  }
  return [...base, ...extra]
})

async function loadMoldingMachineConfigDialogData() {
  moldingMachineConfigLoading.value = true
  try {
    const [cfgRes, machRes] = await Promise.all([
      fetchProductMachineConfigList({ limit: 99999 }),
      fetchMachines(),
    ])
    const cfgList = extractProductMachineConfigListResponse(cfgRes)
    cfgList.sort((a, b) =>
      (a.product_name || '').localeCompare(b.product_name || '', 'ja', { sensitivity: 'base' }),
    )
    moldingMachineConfigRows.value = cfgList
    const machineList = extractMachinesListResponse(machRes)
    moldingMachineCdOptions.value = machineList
      .map((m: any) => ({
        label: `${m.machine_name || ''} (${m.machine_cd || ''})`,
        value: String(m.machine_cd || '').trim(),
      }))
      .filter((o: { value: string }) => o.value)
  } catch (e: any) {
    console.error(e)
    ElMessage.error(e?.response?.data?.detail ?? e?.message ?? 'データの取得に失敗しました')
    moldingMachineConfigRows.value = []
    moldingMachineCdOptions.value = []
  } finally {
    moldingMachineConfigLoading.value = false
  }
}

async function openMoldingMachineConfigDialog() {
  showMoldingMachineConfigDialog.value = true
  await loadMoldingMachineConfigDialogData()
}

async function onMoldingMachineConfigUpdate(row: ProductMachineConfig, val: string | null | undefined) {
  if (row.id == null) return
  const prev = row.molding_machine ?? ''
  const next = val == null || val === '' ? '' : String(val)
  if (next === prev) return
  row.molding_machine = next
  moldingMachineConfigSavingId.value = row.id
  try {
    await updateProductMachineConfig(row.id, { molding_machine: next || undefined })
    ElMessage.success('成型機を保存しました')
  } catch (e: any) {
    row.molding_machine = prev
    ElMessage.error(e?.response?.data?.detail ?? e?.message ?? '保存に失敗しました')
  } finally {
    moldingMachineConfigSavingId.value = null
  }
}

/** 日付ピッカー幅（変更はここ。scoped だけだと dialog teleport で効かないことがあるため inline style 併用） */
const MOLDING_PLAN_PICKER_W_MONTH = '112px'
const MOLDING_PLAN_PICKER_W_BASE = '132px'
const moldingPlanMonthPickerStyle = {
  width: MOLDING_PLAN_PICKER_W_MONTH,
  maxWidth: MOLDING_PLAN_PICKER_W_MONTH,
  minWidth: '0',
}
const moldingPlanBaseDatePickerStyle = {
  width: MOLDING_PLAN_PICKER_W_BASE,
  maxWidth: MOLDING_PLAN_PICKER_W_BASE,
  minWidth: '0',
}

interface MoldingPlanRow {
  lookup_date: string
  molding_machine: string
  product_cd: string
  product_name: string
  trend_raw: number
  required_qty: number
  lot_size: number
  lot_count: number
  batch_qty: number
  daily_qty: number
}
const moldingPlanResult = ref<MoldingPlanRow[]>([])

/** 成型計画ダイアログ内：製品工程BOM 簡易行 */
interface MoldingBomRow {
  product_cd: number
  product_name: string
  safety_stock_days: number
  forming_process_lt: number
}

const showMoldingBomDialog = ref(false)
const moldingBomList = ref<MoldingBomRow[]>([])
const moldingBomLoading = ref(false)
const moldingBomTableRef = ref<InstanceType<typeof import('element-plus').ElTable> | null>(null)
const moldingBomBulkField = ref<'safety' | 'forming' | 'both'>('safety')
const moldingBomBulkLoading = ref(false)
const moldingBomSaveTimers = new Map<number, ReturnType<typeof setTimeout>>()

function clearMoldingBomSaveTimers() {
  for (const t of moldingBomSaveTimers.values()) clearTimeout(t)
  moldingBomSaveTimers.clear()
}

/** products 全件から product_cd → type/status（製品工程BOM 絞り込み用） */
async function fetchProductsTypeStatusMap(): Promise<Map<string, { product_type?: string; status?: string }>> {
  const map = new Map<string, { product_type?: string; status?: string }>()
  const pageSize = 10000
  let page = 1
  let total = 0
  do {
    const prodRes: any = await request.get('/api/master/products', {
      params: { page, pageSize },
    })
    const payload = prodRes?.data
    const list: any[] = payload?.list ?? []
    total = Number(payload?.total ?? 0) || list.length
    for (const p of list) {
      if (p.product_cd == null) continue
      const cd = String(p.product_cd).trim()
      if (!cd) continue
      map.set(cd, { product_type: p.product_type, status: p.status })
    }
    if (list.length < pageSize) break
    if (total > 0 && page * pageSize >= total) break
    page += 1
  } while (true)
  return map
}

/** 製品工程BOM 一覧の表示条件（製品CD 末尾1・名称除外・量産品かつ active） */
function filterMoldingBomRows(
  rows: MoldingBomRow[],
  productMap: Map<string, { product_type?: string; status?: string }>,
): MoldingBomRow[] {
  const out: MoldingBomRow[] = []
  for (const r of rows) {
    const cdStr = String(r.product_cd).trim()
    if (!cdStr) continue
    if (!cdStr.endsWith('1')) continue
    const name = r.product_name ?? ''
    if (name.includes('加工') || name.includes('アーチ')) continue
    const p = productMap.get(cdStr)
    if (!p) continue
    if (String(p.product_type ?? '') !== '量産品') continue
    if (String(p.status ?? '') !== 'active') continue
    out.push(r)
  }
  out.sort((a, b) => (a.product_name || '').localeCompare(b.product_name || '', 'ja'))
  return out
}

async function openMoldingBomDialog() {
  showMoldingBomDialog.value = true
  moldingBomLoading.value = true
  moldingBomList.value = []
  try {
    const [productMap, rawRows] = await Promise.all([
      fetchProductsTypeStatusMap(),
      (async () => {
        const limit = 100
        const rows: MoldingBomRow[] = []
        let page = 1
        while (true) {
          const res = (await fetchProductProcessBOMList({
            page,
            limit,
            sort_by: 'product_name',
            sort_order: 'asc',
          })) as any
          const list = res?.data?.list ?? []
          for (const r of list) {
            rows.push({
              product_cd: r.product_cd,
              product_name: r.product_name != null ? String(r.product_name) : '',
              safety_stock_days: Number(r.safety_stock_days ?? 0),
              forming_process_lt: Number(r.forming_process_lt ?? 0),
            })
          }
          if (!list.length || list.length < limit) break
          page += 1
        }
        return rows
      })(),
    ])
    moldingBomList.value = filterMoldingBomRows(rawRows, productMap)
    nextTick(() => moldingBomTableRef.value?.clearSelection?.())
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail ?? e?.message ?? '読み込みに失敗しました')
    showMoldingBomDialog.value = false
  } finally {
    moldingBomLoading.value = false
  }
}

function clampMoldingBomNum(n: number): number {
  return Math.min(9999, Math.max(0, Math.round(Number(n)) || 0))
}

async function saveMoldingBomRowImmediate(row: MoldingBomRow) {
  const cd = row.product_cd
  const prev = moldingBomSaveTimers.get(cd)
  if (prev) clearTimeout(prev)
  moldingBomSaveTimers.delete(cd)
  await updateProductProcessBOM(cd, {
    safety_stock_days: row.safety_stock_days,
    forming_process_lt: row.forming_process_lt,
  })
}

async function applyMoldingBomBulkDelta(delta: 1 | -1) {
  const table = moldingBomTableRef.value
  const selected = (table?.getSelectionRows?.() ?? []) as MoldingBomRow[]
  if (!selected.length) {
    ElMessage.warning('行を選択してください')
    return
  }
  const field = moldingBomBulkField.value
  const clamp = clampMoldingBomNum
  for (const row of selected) {
    if (field === 'safety' || field === 'both') {
      row.safety_stock_days = clamp(row.safety_stock_days + delta)
    }
    if (field === 'forming' || field === 'both') {
      row.forming_process_lt = clamp(row.forming_process_lt + delta)
    }
  }
  moldingBomBulkLoading.value = true
  try {
    const results = await Promise.allSettled(selected.map((row) => saveMoldingBomRowImmediate(row)))
    const failed = results.filter((r) => r.status === 'rejected').length
    if (failed === 0) {
      ElMessage.success(`${selected.length}件を更新しました`)
    } else {
      ElMessage.warning(`一部失敗: 成功 ${selected.length - failed} / 失敗 ${failed}`)
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail ?? e?.message ?? '一括更新に失敗しました')
  } finally {
    moldingBomBulkLoading.value = false
  }
}

function onMoldingBomFieldChange(row: MoldingBomRow) {
  const cd = row.product_cd
  const prev = moldingBomSaveTimers.get(cd)
  if (prev) clearTimeout(prev)
  const t = setTimeout(async () => {
    try {
      await updateProductProcessBOM(cd, {
        safety_stock_days: row.safety_stock_days,
        forming_process_lt: row.forming_process_lt,
      })
      ElMessage.success({ message: '保存しました', duration: 1500, showClose: false })
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.detail ?? e?.message ?? '保存に失敗しました')
    } finally {
      moldingBomSaveTimers.delete(cd)
    }
  }, 600)
  moldingBomSaveTimers.set(cd, t)
}

const MOLDING_BOM_COL_SAFETY = 0
const MOLDING_BOM_COL_FORMING = 1

function focusMoldingBomCell(rowIndex: number, colIndex: number) {
  nextTick(() => {
    const wrap = document.querySelector(
      `.molding-bom-table-wrap .molding-bom-nav-cell[data-row="${rowIndex}"][data-col="${colIndex}"]`,
    ) as HTMLElement | null
    const input = wrap?.querySelector('input') as HTMLInputElement | undefined
    if (input) {
      input.focus()
      input.select?.()
    }
  })
}

function onMoldingBomInputKeydown(e: KeyboardEvent, rowIndex: number, colIndex: number) {
  const list = moldingBomList.value
  const n = list.length
  if (n === 0) return

  const keys = ['Enter', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight']
  if (!keys.includes(e.key)) return

  e.preventDefault()
  e.stopPropagation()

  const lastRow = n - 1

  if (e.key === 'Enter' || e.key === 'ArrowDown') {
    if (rowIndex < lastRow) focusMoldingBomCell(rowIndex + 1, colIndex)
    return
  }

  if (e.key === 'ArrowUp') {
    if (rowIndex > 0) focusMoldingBomCell(rowIndex - 1, colIndex)
    return
  }

  if (e.key === 'ArrowRight') {
    if (colIndex === MOLDING_BOM_COL_SAFETY) {
      focusMoldingBomCell(rowIndex, MOLDING_BOM_COL_FORMING)
    } else if (rowIndex < lastRow) {
      focusMoldingBomCell(rowIndex + 1, MOLDING_BOM_COL_SAFETY)
    }
    return
  }

  if (e.key === 'ArrowLeft') {
    if (colIndex === MOLDING_BOM_COL_FORMING) {
      focusMoldingBomCell(rowIndex, MOLDING_BOM_COL_SAFETY)
    } else if (rowIndex > 0) {
      focusMoldingBomCell(rowIndex - 1, MOLDING_BOM_COL_FORMING)
    }
  }
}

/** 基準日から n 営業日後（土日除く）。database/api の _subtract_business_days と対称。 */
function addBusinessDays(dateStr: string, days: number): string {
  if (!dateStr || days <= 0) return dateStr
  const parts = dateStr.split('-').map(Number)
  const d = new Date(parts[0]!, parts[1]! - 1, parts[2]!)
  let remaining = Math.floor(days)
  while (remaining > 0) {
    d.setDate(d.getDate() + 1)
    const wd = d.getDay()
    if (wd !== 0 && wd !== 6) remaining -= 1
  }
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function summaryRowDateStr(row: any): string {
  const v = row?.date
  if (v == null) return ''
  if (typeof v === 'string') return v.slice(0, 10)
  return String(v).slice(0, 10)
}

/** product_process_bom 全件（ページング limit=100） */
async function fetchAllProductProcessBomRows(): Promise<any[]> {
  const limit = 100
  const all: any[] = []
  let page = 1
  while (true) {
    const res: any = await request.get('/api/master/product-process-bom', { params: { page, limit } })
    const list: any[] = res?.data?.list ?? []
    if (!list.length) break
    all.push(...list)
    if (list.length < limit) break
    page += 1
  }
  return all
}

function calcWorkingDays(yearMonth: string): number {
  const [y, m] = yearMonth.split('-').map(Number)
  const daysInMonth = new Date(y, m, 0).getDate()
  let count = 0
  for (let d = 1; d <= daysInMonth; d++) {
    const dow = new Date(y, m - 1, d).getDay()
    if (dow !== 0 && dow !== 6) count++
  }
  return count
}

/** 生産計画月の「月末＋1日」＝翌月1日（例: 2026-04 → 2026-05-01） */
function baseDateFromPlanMonth(yearMonth: string): string {
  if (!yearMonth || !/^\d{4}-\d{2}$/.test(yearMonth.trim())) return ''
  const [y, mm] = yearMonth.split('-').map(Number)
  const d = new Date(y, mm, 1)
  const yy = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${yy}-${m}-${day}`
}

function onMoldingPlanMonthChange() {
  if (moldingPlanMonth.value) {
    moldingPlanBaseDate.value = baseDateFromPlanMonth(moldingPlanMonth.value)
    moldingPlanWorkingDays.value = calcWorkingDays(moldingPlanMonth.value)
    moldingPlanClearFromDate.value = moldingPlanBaseDate.value
  }
}

function openMoldingPlanDialog() {
  const { year, month } = getCurrentJSTInfo()
  const mStr = `${year}-${String(month + 1).padStart(2, '0')}`
  moldingPlanMonth.value = mStr
  moldingPlanBaseDate.value = baseDateFromPlanMonth(mStr)
  moldingPlanWorkingDays.value = calcWorkingDays(mStr)
    moldingPlanCoefficient.value = 1.043
    moldingPlanResult.value = []
  moldingPlanClearFromDate.value = baseDateFromPlanMonth(mStr)
  showMoldingPlanDialog.value = true
}

function formatMoldingPlanInt(n: number): string {
  if (n == null || Number.isNaN(Number(n))) return '—'
  return Number(n).toLocaleString('ja-JP')
}

/** 計算結果テーブルを印刷（画面のデフォルト並び：成型機昇順に合わせる） */
function printMoldingPlanResult() {
  const rows = moldingPlanResult.value
  if (!rows.length) {
    ElMessage.warning('印刷するデータがありません')
    return
  }
  const sorted = [...rows].sort((a, b) => {
    const ma = (a.molding_machine || '\uffff').localeCompare(b.molding_machine || '\uffff', 'ja')
    if (ma !== 0) return ma
    return String(a.product_cd || '').localeCompare(String(b.product_cd || ''), 'ja')
  })
  const now = new Date().toLocaleString('ja-JP', { dateStyle: 'medium', timeStyle: 'short' })
  const metaLine = [
    `生産計画月：${moldingPlanMonth.value || '—'}`,
    `基準日：${moldingPlanBaseDate.value || '—'}`,
    `稼働日：${moldingPlanWorkingDays.value ?? '—'}`,
    `加工減耗係数：${moldingPlanCoefficient.value ?? '—'}`,
  ].join('　')
  const totalPlanQty = sorted.reduce((sum, r) => {
    const n = Number(r.batch_qty)
    return Number.isNaN(n) ? sum : sum + n
  }, 0)
  let body = ''
  let prevMachine = ''
  for (const r of sorted) {
    const machineName = String(r.molding_machine || '').trim() || '（未設定）'
    if (machineName !== prevMachine) {
      if (prevMachine) body += '</tbody></table></section>'
      body += `<section class="machine-group">
<h2 class="machine-title">成型機：${escapeHtmlRecommended(machineName)}</h2>
<table>
<thead><tr><th>対応日</th><th>製品名</th><th>必要数</th><th>ロットサイズ</th><th>ロット数</th><th>計画数</th></tr></thead>
<tbody>`
      prevMachine = machineName
    }
    body += `<tr>
      <td class="indent">${escapeHtmlRecommended(String(r.lookup_date || ''))}</td>
      <td>${escapeHtmlRecommended(String(r.product_name || ''))}</td>
      <td class="num">${escapeHtmlRecommended(formatMoldingPlanInt(Number(r.required_qty)))}</td>
      <td class="num">${escapeHtmlRecommended(formatMoldingPlanInt(Number(r.lot_size)))}</td>
      <td class="num">${escapeHtmlRecommended(String(r.lot_count ?? ''))}</td>
      <td class="num batch">${escapeHtmlRecommended(formatMoldingPlanInt(Number(r.batch_qty)))}</td>
    </tr>`
  }
  if (prevMachine) body += '</tbody></table></section>'
  const html = `<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"/><title>成型計画計算結果</title>
<style>
@page { size: A4 portrait; margin: 10mm; }
body{font-family:sans-serif;margin:0;padding:12px;font-size:9pt;-webkit-print-color-adjust:exact;print-color-adjust:exact;}
h1{font-size:13pt;margin:0 0 6px;font-weight:700;}
.meta{color:#475569;font-size:8.5pt;margin:0 0 8px;line-height:1.45;}
.sub{font-size:8pt;color:#64748b;margin:0 0 10px;}
table{border-collapse:collapse;width:100%;}
th,td{border:1px solid #cbd5e1;padding:4px 6px;}
th{background:#f1f5f9;font-weight:600;text-align:center;font-size:8pt;}
td.num{text-align:right;font-variant-numeric:tabular-nums;}
td.batch{font-weight:700;}
.machine-group{margin-bottom:10px;break-inside:avoid-page;page-break-inside:avoid;}
.machine-title{font-size:10pt;margin:0;padding:6px 8px;background:#e2e8f0;border:1px solid #cbd5e1;border-bottom:none;}
td.indent{padding-left:16px;}
</style></head><body>
<h1>成型計画作成 — 計算結果</h1>
<p class="meta">${escapeHtmlRecommended(metaLine)}</p>
<p class="sub">計画数合計：<strong>${escapeHtmlRecommended(formatMoldingPlanInt(totalPlanQty))}</strong>　／　出力：${escapeHtmlRecommended(now)}　／　${sorted.length} 件</p>
${body || '<p class="sub">印刷対象データがありません。</p>'}
</body></html>`
  const win = openPrintPreviewThenDialog(html)
  if (!win) {
    ElMessage.warning('ポップアップがブロックされました。ブラウザでポップアップを許可してください。')
    return
  }
  ElMessage.success('印刷プレビューを表示しました')
}

async function executeMoldingPlanClear() {
  const d = moldingPlanClearFromDate.value
  if (!d) {
    ElMessage.warning('計画クリア開始日を選択してください')
    return
  }
  try {
    await ElMessageBox.confirm(
      `<p>この日付以降の<strong>成型計画（molding_plan）</strong>および<strong>実績計画（molding_actual_plan）</strong>をすべて 0 にクリアします。</p><p>開始日：<strong>${d}</strong></p>
<p style="margin-top:8px;color:#64748b;font-size:12px;">※ 他工程の計画列は変更しません。再集計が必要な場合は「計画データ更新」を実行してください。</p>`,
      '計画クリアの確認',
      {
        confirmButtonText: '実行',
        cancelButtonText: 'キャンセル',
        type: 'warning',
        dangerouslyUseHTMLString: true,
      },
    )
  } catch {
    return
  }
  moldingPlanClearLoading.value = true
  try {
    const res: any = await clearProductionSummarysMoldingPlan(d)
    const cleared = res?.data?.cleared
    const msg = res?.message ?? `成型計画をクリアしました（${cleared ?? 0}件）`
    ElMessage.success(msg)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail ?? e?.message ?? 'クリアに失敗しました')
  } finally {
    moldingPlanClearLoading.value = false
  }
}

async function executeMoldingPlanInventoryTrend() {
  const startDate = getFirstDayOfCurrentMonth()
  try {
    await ElMessageBox.confirm(
      `<p>当月月初から先の在庫・推移・安全在庫フィールドをクリアしてから、在庫→推移→安全在庫の順で再計算します（在庫は当月月初～+3ヶ月、推移は当月月初～表末。安全在庫は製品マスタの安全在庫日数×将来30営業日の平均内示数）。</p><p style="margin-top:10px">計算開始日（月初）：<strong>${startDate}</strong></p>`,
      '在庫・推移更新の確認',
      {
        confirmButtonText: '更新',
        cancelButtonText: 'キャンセル',
        type: 'info',
        dangerouslyUseHTMLString: true,
      },
    )
  } catch {
    return
  }
  moldingPlanInventoryTrendLoading.value = true
  updatingInventoryTrend.value = true
  try {
    await runInventoryTrendUpdateSequence(startDate)
  } catch (_e) {
    /* runInventoryTrendUpdateSequence 内でメッセージ表示済み */
  } finally {
    moldingPlanInventoryTrendLoading.value = false
    updatingInventoryTrend.value = false
  }
}

async function executeMoldingPlanCreate() {
  if (!moldingPlanBaseDate.value) {
    ElMessage.warning('基準日を選択してください')
    return
  }
  moldingPlanLoading.value = true
  try {
    const baseDate = moldingPlanBaseDate.value
    const coeff = moldingPlanCoefficient.value
    const workDays = moldingPlanWorkingDays.value

    const bomRows = await fetchAllProductProcessBomRows()
    if (!bomRows.length) {
      ElMessage.info('製品工程BOMのデータがありません')
      moldingPlanResult.value = []
      return
    }

    /** 対応日 = 基準日 + forming_process_lt + safety_stock_days（営業日加算、土日除く） */
    const lookups: { product_cd: string; product_name: string; lookup_date: string; biz_days: number }[] = []
    for (const bom of bomRows) {
      const cd = bom.product_cd != null ? String(bom.product_cd).trim() : ''
      if (!cd) continue
      const formingLt = Number(bom.forming_process_lt ?? 0) || 0
      const safety = Number(bom.safety_stock_days ?? 0) || 0
      const bizDays = formingLt + safety
      const lookupDate = addBusinessDays(baseDate, bizDays)
      lookups.push({
        product_cd: cd,
        product_name: (bom.product_name as string) ?? '',
        lookup_date: lookupDate,
        biz_days: bizDays,
      })
    }

    const dates = [...new Set(lookups.map((l) => l.lookup_date))].filter(Boolean).sort()
    if (!dates.length) {
      moldingPlanResult.value = []
      return
    }
    const minD = dates[0]!
    const maxD = dates[dates.length - 1]!

    const res = await getProductionSummarysList({
      page: 1,
      limit: 50000,
      startDate: minD,
      endDate: maxD,
    })
    const data = (res as any)?.data ?? res
    const summaryRows: any[] = data?.list ?? []

    const summaryByDateProduct = new Map<string, any>()
    for (const row of summaryRows) {
      const pcd = row.product_cd != null ? String(row.product_cd).trim() : ''
      if (!pcd) continue
      const ds = summaryRowDateStr(row)
      if (!ds) continue
      summaryByDateProduct.set(`${ds}|${pcd}`, row)
    }

    const lotSizeMap = new Map<string, number>()
    const pageSize = 10000
    let page = 1
    let total = 0
    do {
      const prodRes: any = await request.get('/api/master/products', {
        params: { page, pageSize },
      })
      const payload = prodRes?.data
      const prodList: any[] = payload?.list ?? []
      total = Number(payload?.total ?? 0) || prodList.length
      for (const p of prodList) {
        if (p.product_cd != null) lotSizeMap.set(String(p.product_cd).trim(), Number(p.lot_size) || 1)
      }
      if (prodList.length < pageSize) break
      if (total > 0 && page * pageSize >= total) break
      page += 1
    } while (true)

    const result: MoldingPlanRow[] = []
    for (const L of lookups) {
      const row = summaryByDateProduct.get(`${L.lookup_date}|${L.product_cd}`)
      if (!row) continue
      const trend = Number(row.molding_actual_plan_trend ?? 0)
      if (trend >= 0) continue
      const reqRaw = Math.abs(trend) * coeff
      const requiredQty = Math.round(reqRaw)
      const lotSize = lotSizeMap.get(L.product_cd) ?? 1
      const lotCount = lotSize > 0 ? Math.ceil(requiredQty / lotSize) : requiredQty
      const batchQty = lotCount * lotSize
      const dailyQty = workDays > 0 ? Math.ceil(batchQty / workDays) : batchQty

      result.push({
        lookup_date: L.lookup_date,
        molding_machine: row.molding_machine ?? '',
        product_cd: L.product_cd,
        product_name: row.product_name || L.product_name || '',
        trend_raw: trend,
        required_qty: requiredQty,
        lot_size: lotSize,
        lot_count: lotCount,
        batch_qty: batchQty,
        daily_qty: dailyQty,
      })
    }

    /** 成型機 昇順 → 対応日 → 製品名 */
    result.sort((a, b) => {
      const ma = (a.molding_machine || '\uffff').localeCompare(b.molding_machine || '\uffff', 'ja')
      if (ma !== 0) return ma
      const da = a.lookup_date.localeCompare(b.lookup_date)
      if (da !== 0) return da
      return (a.product_name || '').localeCompare(b.product_name || '', 'ja')
    })

    moldingPlanResult.value = result
    if (!result.length) {
      ElMessage.info(
        '対象データがありません（対応日の production_summarys 行なし、または molding_actual_plan_trend が 0 以上）',
      )
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail ?? e?.message ?? '計算に失敗しました')
  } finally {
    moldingPlanLoading.value = false
  }
}

const selectAllColumns = () => {
  columnKeys.forEach((k) => (visibleColumns.value[k] = true))
}
const deselectAllColumns = () => {
  columnKeys.forEach((k) => (visibleColumns.value[k] = false))
}
const resetColumnSettings = () => {
  visibleColumns.value = { ...defaultVisibleColumns }
}
const saveColumnSettings = () => {
  try {
    localStorage.setItem('productionDataMgmtColumns', JSON.stringify(visibleColumns.value))
    ElMessage.success('列設定を保存しました')
    showColumnSettings.value = false
  } catch {
    ElMessage.error('列設定の保存に失敗しました')
  }
}

// ---------- 初期在庫一括登録 ----------
function setBatchQtyInputRef(index: number, el: any) {
  if (el != null) {
    batchQtyInputRefs.value[index] = el
  }
}

function focusBatchInitialRow(targetIndex: number) {
  const len = batchInitialStockData.value.length
  if (len === 0) return
  const idx = Math.max(0, Math.min(targetIndex, len - 1))
  nextTick(() => {
    const ref = batchQtyInputRefs.value[idx]
    if (ref?.focus) ref.focus()
    else if (ref?.$el?.querySelector) ref.$el.querySelector('input')?.focus()
  })
}

function openBatchInitialStockDialog() {
  const { year, month } = getCurrentJSTInfo()
  batchInitialStockMonth.value = getJSTDateString(year, month, 1).slice(0, 7)
  batchInitialStockProcessCd.value = ''
  batchInitialStockData.value = []
  batchQtyInputRefs.value = []
  if (!processOptions.value.length) {
    request.get<Array<{ cd: string; name: string }>>('/api/master/processes/options').then((res: unknown) => {
      processOptions.value = Array.isArray(res) ? res : (res as { data?: Array<{ cd: string; name: string }> })?.data ?? []
    }).catch(() => { processOptions.value = [] })
  }
  showBatchInitialStockDialog.value = true
}

/** 製品フィルタ: 末位1、加工・アーチ除外、active、量産品/試作品 */
function filterProductsForInitial(products: Array<{ product_cd: string; product_name?: string; product_type?: string; status?: string }>) {
  const allowedTypes = ['量産品', '試作品']
  return products.filter((p) => {
    const cd = (p.product_cd || '').trim()
    if (!cd || cd.slice(-1) !== '1') return false
    const name = (p.product_name || '')
    if (name.includes('加工') || name.includes('アーチ')) return false
    const status = (p.status ?? '').toString().toLowerCase()
    if (status === 'inactive' || status === '0' || status === 'false') return false
    const pt = (p.product_type || '').trim()
    if (pt && !allowedTypes.includes(pt)) return false
    return true
  })
}

async function handleBatchInitialStockSearch() {
  const month = (batchInitialStockMonth.value || '').trim()
  const processCd = (batchInitialStockProcessCd.value || '').trim()
  if (!month || !processCd) {
    ElMessage.warning('月と工程を選択してください')
    return
  }
  batchInitialStockLoading.value = true
  try {
    let products: Array<{ product_cd: string; product_name?: string; product_type?: string; status?: string }> = []
    try {
      const res = await request.get<Array<{ product_cd: string; product_name?: string; product_type?: string; status?: string }>>(
        `${INVENTORY_BASE}/products-by-process`,
        { params: { process_cd: processCd } }
      )
      products = Array.isArray(res) ? res : (res as { data?: typeof products })?.data ?? []
    } catch {
      const fallback = await getProductionSummarysProducts()
      const list = (fallback as { data?: typeof products })?.data ?? (Array.isArray(fallback) ? fallback : [])
      products = list.map((p: { product_cd: string; product_name?: string }) => ({ product_cd: p.product_cd, product_name: p.product_name }))
    }
    const filtered = filterProductsForInitial(products)
    const monthFirst = `${month}-01`
    const dateStart = `${monthFirst} 00:00:00`
    let existingList: Array<{ id: number; target_cd: string; quantity: number; transaction_time?: string }> = []
    try {
      const logRes = await request.get(
        STOCK_LOGS_BASE,
        {
          params: {
            transaction_type: '初期',
            process_cd: processCd,
            date_start: dateStart,
            date_end: monthFirst,
            page: 1,
            pageSize: 5000,
          },
        }
      ) as { list?: typeof existingList; data?: { list?: typeof existingList } }
      const body = 'data' in logRes && logRes.data != null ? logRes.data : logRes
      existingList = body?.list ?? []
    } catch {
      existingList = []
    }
    const existingMap = new Map<string, { quantity: number; transaction_time?: string; id: number }>()
    for (const log of existingList) {
      existingMap.set((log.target_cd || '').trim(), {
        quantity: Number(log.quantity) || 0,
        transaction_time: log.transaction_time,
        id: log.id,
      })
    }
    const rows = filtered.map((p) => {
      const cd = (p.product_cd || '').trim()
      const ex = existingMap.get(cd)
      return {
        product_cd: cd,
        product_name: (p.product_name || '').trim(),
        editQuantity: ex ? ex.quantity : null,
        existing_id: ex?.id,
        existing_quantity: ex?.quantity,
        transaction_time: ex?.transaction_time,
      }
    })
    rows.sort((a, b) => (a.product_name || '').localeCompare(b.product_name || '') || a.product_cd.localeCompare(b.product_cd))
    batchQtyInputRefs.value = []
    batchInitialStockData.value = rows
  } catch (e) {
    ElMessage.error('検索に失敗しました')
    console.error(e)
  } finally {
    batchInitialStockLoading.value = false
  }
}

function batchInitialStockSummaryMethod({ data }: { data: Array<{ editQuantity?: number | null }> }) {
  const total = data.reduce((s, row) => s + (Number(row.editQuantity) || 0), 0)
  return ['', '', `合計: ${total.toLocaleString()}`]
}

async function handleSaveBatchInitialStock() {
  const month = (batchInitialStockMonth.value || '').trim()
  const processCd = (batchInitialStockProcessCd.value || '').trim()
  if (!month || !processCd) {
    ElMessage.warning('月と工程を選択してください')
    return
  }
  const transactionTime = `${month}-01 00:00:00`
  const updatePromises: Promise<unknown>[] = []
  const insertPromises: Promise<unknown>[] = []
  for (const row of batchInitialStockData.value) {
    const newQty = Number(row.editQuantity)
    const existingQty = Number(row.existing_quantity ?? 0)
    if (newQty === existingQty) continue
    if (row.existing_id != null) {
      updatePromises.push(
        request.put(`${STOCK_LOGS_BASE}/${row.existing_id}`, {
          transaction_time: transactionTime,
          transaction_type: '初期',
          target_cd: row.product_cd,
          quantity: newQty,
          stock_type: processCd === 'KT13' ? '製品' : processCd === 'KT15' ? '製品' : '仕掛品',
          location_cd: processCd === 'KT13' ? '製品倉庫' : processCd === 'KT15' ? '外注倉庫' : '工程中間在庫',
          unit: '本',
          source_file: '生産データ管理',
        })
      )
    } else {
      if (newQty <= 0) continue
      insertPromises.push(
        request.post(STOCK_LOGS_BASE, {
          stock_type: processCd === 'KT13' ? '製品' : processCd === 'KT15' ? '製品' : '仕掛品',
          target_cd: row.product_cd,
          location_cd: processCd === 'KT13' ? '製品倉庫' : processCd === 'KT15' ? '外注倉庫' : '工程中間在庫',
          transaction_type: '初期',
          quantity: newQty,
          unit: '本',
          process_cd: processCd,
          transaction_time: transactionTime,
          source_file: '生産データ管理',
        })
      )
    }
  }
  if (updatePromises.length === 0 && insertPromises.length === 0) {
    ElMessage.info('変更がありません')
    return
  }
  batchInitialStockSaving.value = true
  try {
    await Promise.all([...insertPromises, ...updatePromises])
    ElMessage.success(`更新 ${updatePromises.length} 件、追加 ${insertPromises.length} 件`)
    await handleBatchInitialStockSearch()
  } catch (e) {
    ElMessage.error('一括保存に失敗しました')
    console.error(e)
  } finally {
    batchInitialStockSaving.value = false
  }
}

onMounted(() => {
  const saved = localStorage.getItem('productionDataMgmtColumns')
  if (saved) {
    try {
      const parsed = JSON.parse(saved)
      visibleColumns.value = { ...defaultVisibleColumns, ...parsed }
    } catch {
      /**/
    }
  }
  fetchProductList()
  fetchData()
  // スマホ・タブレットで「その他」を Drawer 表示にする
  othersDrawerMql = window.matchMedia('(max-width: 992px)')
  othersDrawerMqlHandler = () => { isSmallScreen.value = othersDrawerMql!.matches }
  othersDrawerMqlHandler()
  othersDrawerMql.addEventListener('change', othersDrawerMqlHandler)
})

onUnmounted(() => {
  clearMoldingBomSaveTimers()
  if (othersDrawerMql && othersDrawerMqlHandler) {
    othersDrawerMql.removeEventListener('change', othersDrawerMqlHandler)
    othersDrawerMql = null
    othersDrawerMqlHandler = null
  }
})
</script>

<style scoped>
.production-data-management {
  padding: 0.65rem 0.75rem 1rem;
  min-height: 100%;
  background:
    radial-gradient(1200px 480px at 10% -8%, rgba(99, 102, 241, 0.09), transparent 55%),
    radial-gradient(900px 400px at 100% 0%, rgba(14, 165, 233, 0.07), transparent 50%),
    linear-gradient(165deg, #f1f5f9 0%, #e8eef5 45%, #f8fafc 100%);
}
.page-header-shell {
  margin-bottom: 0.65rem;
  padding: 0.65rem 0.85rem;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(226, 232, 240, 0.95);
  box-shadow:
    0 4px 24px -10px rgba(15, 23, 42, 0.14),
    0 0 0 1px rgba(255, 255, 255, 0.65) inset;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}
.page-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.65rem;
}
.title-group {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  min-width: 0;
}
.page-title-mark {
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  color: #fff;
  background: linear-gradient(145deg, #6366f1 0%, #4f46e5 48%, #4338ca 100%);
  box-shadow: 0 8px 22px -10px rgba(79, 70, 229, 0.65);
}
.title-text-block {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  min-width: 0;
}
.page-title {
  margin: 0;
  font-size: 1.28rem;
  font-weight: 800;
  letter-spacing: 0.02em;
  color: #0f172a;
  line-height: 1.2;
}
.page-subtitle {
  margin: 0;
  font-size: 0.7rem;
  font-weight: 500;
  color: #64748b;
  letter-spacing: 0.04em;
}
.title-group :deep(.record-count.el-tag) {
  font-size: 0.72rem;
  height: 28px;
  line-height: 26px;
  padding: 0 10px;
  border: none;
  font-weight: 600;
  background: linear-gradient(180deg, #eef2ff 0%, #e0e7ff 100%);
  color: #4338ca;
}
.header-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.4rem;
}
.header-actions :deep(.el-button) {
  font-size: 0.75rem;
  height: 30px;
  padding: 0 12px;
  border-radius: 10px;
  font-weight: 600;
  letter-spacing: 0.02em;
  transition:
    background 0.18s ease,
    border-color 0.18s ease,
    box-shadow 0.18s ease,
    transform 0.12s ease;
}
.header-actions :deep(.el-button:not(.is-disabled):active) {
  transform: translateY(1px);
}
/* ツールバー：操作別カラー */
.header-actions :deep(.others-btn.el-button) {
  color: #fff;
  background: linear-gradient(180deg, #6366f1 0%, #4f46e5 100%);
  border-color: #4338ca;
  box-shadow: 0 2px 8px -2px rgba(67, 56, 202, 0.55);
}
.header-actions :deep(.others-btn.el-button:hover:not(.is-disabled)) {
  background: linear-gradient(180deg, #818cf8 0%, #6366f1 100%);
  border-color: #4f46e5;
}
.header-actions :deep(.refresh-btn.el-button) {
  color: #fff;
  background: linear-gradient(180deg, #38bdf8 0%, #0ea5e9 100%);
  border-color: #0284c7;
  box-shadow: 0 2px 8px -2px rgba(14, 165, 233, 0.5);
}
.header-actions :deep(.refresh-btn.el-button:hover:not(.is-disabled)) {
  background: linear-gradient(180deg, #7dd3fc 0%, #38bdf8 100%);
  border-color: #0ea5e9;
}
.header-actions :deep(.print-btn.el-button) {
  color: #f8fafc;
  background: linear-gradient(180deg, #64748b 0%, #475569 100%);
  border-color: #334155;
  box-shadow: 0 2px 6px -2px rgba(51, 65, 85, 0.45);
}
.header-actions :deep(.print-btn.el-button:hover:not(.is-disabled)) {
  background: linear-gradient(180deg, #94a3b8 0%, #64748b 100%);
}
.header-actions :deep(.process-print-btn-primary.el-button) {
  color: #fff;
  background: linear-gradient(180deg, #34d399 0%, #059669 100%);
  border-color: #047857;
  box-shadow: 0 2px 10px -2px rgba(5, 150, 105, 0.5);
}
.header-actions :deep(.process-print-btn-primary.el-button:hover:not(.is-disabled)) {
  background: linear-gradient(180deg, #6ee7b7 0%, #10b981 100%);
  border-color: #059669;
}
.header-actions :deep(.recommended-print-dropdown-btn.el-button) {
  color: #fff;
  background: linear-gradient(180deg, #fbbf24 0%, #d97706 100%);
  border-color: #b45309;
  box-shadow: 0 2px 10px -2px rgba(217, 119, 6, 0.45);
}
.header-actions :deep(.recommended-print-dropdown-btn.el-button:hover:not(.is-disabled)) {
  background: linear-gradient(180deg, #fcd34d 0%, #f59e0b 100%);
  border-color: #d97706;
}
.header-actions :deep(.production-plan-dropdown-btn.el-button) {
  color: #fff;
  background: linear-gradient(180deg, #a78bfa 0%, #7c3aed 100%);
  border-color: #6d28d9;
  box-shadow: 0 2px 10px -2px rgba(124, 58, 237, 0.45);
}
.header-actions :deep(.production-plan-dropdown-btn.el-button:hover:not(.is-disabled)) {
  background: linear-gradient(180deg, #c4b5fd 0%, #8b5cf6 100%);
  border-color: #7c3aed;
}
.header-actions :deep(.settings-btn.el-button) {
  color: #334155;
  background: #fff;
  border-color: #cbd5e1;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.9) inset;
}
.header-actions :deep(.settings-btn.el-button:hover:not(.is-disabled)) {
  color: #0f172a;
  background: #f8fafc;
  border-color: #94a3b8;
}
.header-actions :deep(.el-button.is-disabled) {
  opacity: 0.52;
  filter: grayscale(0.15);
}
/* 内容区域：统一字体 0.75rem，组件高度 28px */
.table-card {
  border-radius: 14px;
  border: 1px solid rgba(226, 232, 240, 0.95);
  overflow: hidden;
  font-size: 0.75rem;
  background: rgba(255, 255, 255, 0.92);
  box-shadow:
    0 12px 40px -18px rgba(15, 23, 42, 0.12),
    0 0 0 1px rgba(255, 255, 255, 0.8) inset;
}
.table-card :deep(.el-card__header) {
  padding: 0.45rem 0.65rem;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.98) 0%, rgba(241, 245, 249, 0.65) 100%);
  border-bottom: 1px solid rgba(226, 232, 240, 0.85);
}
.table-card :deep(.el-card__body) {
  padding: 0.45rem 0.65rem;
  background: linear-gradient(180deg, #fafbfc 0%, #fff 32%);
}
.filter-section {
  margin-top: 0.35rem;
  padding: 0.45rem 0.55rem;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  align-items: center;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
}
.filter-item {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background: #fff;
  padding: 0 0.55rem;
  border-radius: 10px;
  border: 1px solid rgba(226, 232, 240, 0.95);
  height: 30px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}
.filter-label {
  font-size: 0.75rem;
  font-weight: 700;
  color: #64748b;
  white-space: nowrap;
}
.date-filter-item {
  height: 30px;
}
.date-quick-item {
  height: 30px;
  display: inline-flex;
  align-items: center;
}
.date-quick-item .date-quick-buttons {
  margin: 0;
}
.table-card :deep(.filter-section .el-date-editor),
.table-card :deep(.filter-section .el-select),
.table-card :deep(.filter-section .el-input) {
  font-size: 0.75rem;
}
.table-card :deep(.filter-section .el-date-editor .el-input__wrapper),
.table-card :deep(.filter-section .el-select .el-input__wrapper),
.table-card :deep(.filter-section .el-input .el-input__wrapper) {
  min-height: 28px;
  border-radius: 8px;
  padding: 0 8px;
}
.table-card :deep(.filter-section .el-date-editor) {
  width: 240px;
}
.date-quick-buttons {
  display: flex;
  gap: 0.2rem;
  align-items: center;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  padding: 0 5px;
  border-radius: 10px;
  border: 1px solid rgba(226, 232, 240, 0.95);
  height: 28px;
}
.date-quick-buttons :deep(.el-button) {
  font-size: 0.72rem;
  height: 24px;
  padding: 0 8px;
  border-radius: 8px;
  font-weight: 600;
}
.date-quick-buttons :deep(.el-button--primary.is-plain) {
  color: #fff;
  background: linear-gradient(180deg, #38bdf8 0%, #0ea5e9 100%);
  border-color: #0284c7;
}
.date-quick-buttons :deep(.el-button--primary.is-plain:hover) {
  background: linear-gradient(180deg, #7dd3fc 0%, #38bdf8 100%);
  border-color: #0ea5e9;
  color: #fff;
}
.filter-select {
  width: 160px;
}
.keyword-filter-input {
  width: 160px;
}
.summary-table-tabs {
  margin-bottom: 0;
  padding: 0.15rem 0 0;
}
.summary-table-tabs :deep(.el-tabs__header) {
  margin-bottom: 0;
  border: none;
}
.summary-table-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}
.summary-table-tabs :deep(.el-tabs__content) {
  padding: 0;
  overflow: visible;
}
.summary-table-tabs :deep(.el-tab-pane) {
  padding: 0;
}
.summary-table-tabs :deep(.el-tabs__item) {
  padding: 0 12px;
  height: 30px;
  line-height: 30px;
  border: 1px solid rgba(226, 232, 240, 0.95);
  border-radius: 10px;
  margin-right: 0.35rem;
  font-size: 0.74rem;
  background: rgba(255, 255, 255, 0.65);
  transition:
    background 0.15s ease,
    border-color 0.15s ease,
    color 0.15s ease;
}
.summary-table-tabs :deep(.el-tabs__item:hover) {
  border-color: rgba(99, 102, 241, 0.35);
  color: #4338ca;
}
.summary-table-tabs :deep(.el-tabs__item.is-active) {
  border-color: rgba(99, 102, 241, 0.55);
  background: linear-gradient(180deg, #eef2ff 0%, #e0e7ff 100%);
  color: #4338ca;
  font-weight: 700;
  box-shadow: 0 2px 8px -4px rgba(79, 70, 229, 0.45);
}
.tab-text {
  font-weight: inherit;
  font-size: 0.74rem;
  color: inherit;
}
/* テーブル：字体与区域统一 0.75rem */
.modern-table {
  font-size: 0.75rem;
}
.modern-table :deep(.el-table) {
  --el-table-border-color: #e5e7eb;
  --el-table-header-bg-color: #f1f5f9;
  --el-table-row-hover-bg-color: #f1f5f9;
  border-radius: 10px;
  overflow: hidden;
}
.modern-table :deep(.el-table__header-wrapper th) {
  white-space: nowrap;
  padding: 0;
}
.modern-table :deep(.el-table__body-wrapper td) {
  padding: 0;
}
.modern-table :deep(.el-table .cell) {
  padding: 3px 8px;
  line-height: 1.35;
  font-size: 0.75rem;
}
.modern-table :deep(.el-table__header .cell) {
  padding: 4px 8px;
  line-height: 1.3;
  font-weight: 600;
  font-size: 0.75rem;
  color: #475569;
}
.modern-table :deep(.el-table__row:hover) {
  background-color: #f1f5f9 !important;
}
.modern-table :deep(.el-table--border .el-table__cell) {
  border-color: #e5e7eb;
}
.date-cell,
.product-name-cell,
.number-cell,
.date-text,
.text-cell {
  font-size: 0.75rem;
  font-weight: 500;
}
.date-cell {
  color: #0f172a;
}
.product-name-cell {
  color: #1e293b;
}
.number-cell.negative {
  color: #dc2626;
}
.number-cell.positive {
  color: #047857;
}
.date-text {
  color: #64748b;
}
.text-cell {
  color: #374151;
}
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 0.5rem 0 0;
}
.pagination-compact {
  font-size: 0.75rem;
}
.pagination-compact :deep(.el-pagination__total),
.pagination-compact :deep(.el-pagination__jump),
.pagination-compact :deep(.el-pager li),
.pagination-compact :deep(.btn-prev),
.pagination-compact :deep(.btn-next) {
  font-size: 0.75rem;
}
.pagination-compact :deep(.el-pager li),
.pagination-compact :deep(.btn-prev),
.pagination-compact :deep(.btn-next) {
  min-width: 28px;
  height: 28px;
  line-height: 28px;
}
.column-settings-content {
  max-height: 60vh;
  overflow-y: auto;
}
.column-settings-actions {
  display: flex;
  gap: 0.35rem;
  margin-bottom: 0.6rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #e5e7eb;
}
.column-settings-hint {
  font-size: 0.7rem;
  color: #6b7280;
  margin-bottom: 0.5rem;
}
.column-group {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 0.5rem;
  margin-bottom: 0.5rem;
}
.group-header {
  font-weight: 700;
  margin-bottom: 0.35rem;
  padding-bottom: 0.35rem;
  border-bottom: 1px solid #f3f4f6;
  font-size: 0.85rem;
}
.group-columns {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 0.2rem;
}
.column-checkbox {
  font-size: 0.8rem;
}
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

/* その他ドロップダウン */
.others-dropdown {
  margin-right: 0.3rem;
}
.others-btn {
  margin-right: 0.25rem;
}

/* その他 Drawer（スマホ・タブレット） */
.others-drawer-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 0 0 12px 0;
  max-height: 70vh;
  overflow-y: auto;
}
.others-drawer-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  font-size: 14px;
  color: #303133;
  cursor: pointer;
  border-radius: 8px;
  transition: background 0.15s;
  -webkit-tap-highlight-color: transparent;
  min-height: 44px;
  box-sizing: border-box;
}
.others-drawer-item:hover {
  background: #f5f7fa;
}
.others-drawer-item:active {
  background: #e4e7ed;
}
.others-drawer-item.is-disabled {
  color: #c0c4cc;
  cursor: not-allowed;
  pointer-events: none;
}
.others-drawer-item .el-icon {
  font-size: 18px;
  flex-shrink: 0;
}
.process-print-btn-primary {
  margin-left: 0.25rem;
}

/* データ生成確認ダイアログ */
.generate-confirm-content {
  display: flex;
  gap: 0.6rem;
  align-items: flex-start;
}
.confirm-icon-wrapper {
  flex-shrink: 0;
}
.confirm-icon {
  font-size: 1.5rem;
  color: #6366f1;
}
.confirm-info {
  flex: 1;
}
.confirm-title {
  margin: 0 0 0.5rem 0;
  font-size: 0.9rem;
  color: #1e293b;
}
.confirm-details {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}
.detail-row {
  display: flex;
  gap: 0.35rem;
  font-size: 0.8rem;
}
.detail-label {
  color: #64748b;
  min-width: 4em;
}
.detail-value.highlight {
  font-weight: 600;
  color: #0f172a;
}
/* 在庫取引ログ入力ダイアログ */
.transaction-log-dialog .el-dialog__body {
  padding: 16px 20px 20px;
}
.transaction-input-info {
  margin-bottom: 1.25rem;
  padding: 12px 14px;
  background: #f1f5f9;
  border-radius: 8px;
}
.transaction-info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px 24px;
}
.transaction-info-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.transaction-info-label {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
}
.transaction-info-value {
  font-size: 14px;
  color: #1e293b;
  font-weight: 600;
}
.transaction-panels {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.transaction-panel {
  border-radius: 8px;
  border: 2px solid;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.transaction-panel--green {
  border-color: #22c55e;
  background: rgba(34, 197, 94, 0.04);
}
.transaction-panel--orange {
  border-color: #f59e0b;
  background: rgba(245, 158, 11, 0.04);
}
.transaction-panel--red {
  border-color: #ef4444;
  background: rgba(239, 68, 68, 0.04);
}
.transaction-panel--blue {
  border-color: #3b82f6;
  background: rgba(59, 130, 246, 0.04);
}
.transaction-panel--empty {
  border: none;
  background: transparent;
  visibility: hidden;
  padding: 0;
  min-height: 0;
}
.transaction-panel-head {
  display: flex;
  align-items: center;
  gap: 8px;
}
.transaction-panel--green .transaction-panel-icon { color: #22c55e; }
.transaction-panel--orange .transaction-panel-icon { color: #f59e0b; }
.transaction-panel--red .transaction-panel-icon { color: #ef4444; }
.transaction-panel--blue .transaction-panel-icon { color: #3b82f6; }
.transaction-panel-icon {
  font-size: 18px;
}
.transaction-panel-label {
  font-size: 14px;
  font-weight: 600;
  color: #334155;
}
.transaction-panel-input {
  width: 100%;
}
.transaction-panel-input :deep(.el-input__wrapper) {
  background-color: #f8fafc;
  border-radius: 6px;
}
.transaction-panel--green .transaction-panel-input :deep(.el-input__wrapper) { box-shadow: 0 0 0 1px #86efac; }
.transaction-panel--orange .transaction-panel-input :deep(.el-input__wrapper) { box-shadow: 0 0 0 1px #fcd34d; }
.transaction-panel--red .transaction-panel-input :deep(.el-input__wrapper) { box-shadow: 0 0 0 1px #fca5a5; }
.transaction-panel--blue .transaction-panel-input :deep(.el-input__wrapper) { box-shadow: 0 0 0 1px #93c5fd; }
.transaction-panel--green .transaction-panel-input :deep(.el-input__wrapper:hover),
.transaction-panel--green .transaction-panel-input :deep(.el-input__wrapper.is-focus) { box-shadow: 0 0 0 1px #22c55e; }
.transaction-panel--orange .transaction-panel-input :deep(.el-input__wrapper:hover),
.transaction-panel--orange .transaction-panel-input :deep(.el-input__wrapper.is-focus) { box-shadow: 0 0 0 1px #f59e0b; }
.transaction-panel--red .transaction-panel-input :deep(.el-input__wrapper:hover),
.transaction-panel--red .transaction-panel-input :deep(.el-input__wrapper.is-focus) { box-shadow: 0 0 0 1px #ef4444; }
.transaction-panel--blue .transaction-panel-input :deep(.el-input__wrapper:hover),
.transaction-panel--blue .transaction-panel-input :deep(.el-input__wrapper.is-focus) { box-shadow: 0 0 0 1px #3b82f6; }
.transaction-log-dialog .dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
.all-update-steps-list {
  margin: 0;
  padding-left: 1.25rem;
  font-size: 0.85rem;
  color: #334155;
  line-height: 1.6;
}

/* データ生成・一括更新進度ダイアログ（在庫不足管理と同様のスタイル） */
.progress-dialog--styled .el-dialog__body {
  padding: 20px 24px 24px;
}
.progress-content {
  padding: 4px 0;
}
.progress-info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.progress-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.15);
  animation: progress-icon-pulse 1.5s ease-in-out infinite;
}
.progress-icon {
  font-size: 20px;
  color: #6366f1;
  animation: progress-icon-spin 0.9s linear infinite;
}
.progress-text {
  font-size: 14px;
  color: #334155;
  font-weight: 500;
  transition: opacity 0.25s ease;
}
.progress-track {
  height: 14px;
  border-radius: 999px;
  background: #f1f5f9;
  overflow: hidden;
  margin-bottom: 12px;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.04);
}
.progress-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
  background-size: 200% 100%;
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  box-shadow: 0 0 12px rgba(99, 102, 241, 0.4);
}
.progress-fill--success {
  background: linear-gradient(90deg, #10b981 0%, #34d399 100%);
  box-shadow: 0 0 12px rgba(16, 185, 129, 0.4);
}
.progress-shine {
  position: absolute;
  top: 0;
  left: -100%;
  width: 60%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.35) 50%,
    transparent 100%
  );
  animation: progress-shine 1.8s ease-in-out infinite;
}
.progress-details {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #64748b;
}
.progress-details .detail-label {
  font-weight: 500;
}
.progress-details .detail-value {
  font-weight: 700;
  color: #6366f1;
  font-variant-numeric: tabular-nums;
  transition: transform 0.2s ease, color 0.3s ease;
}
.progress-details .detail-value.progress-percent {
  min-width: 2.5em;
  text-align: right;
}
.progress-dialog--styled .progress-content:has(.progress-fill--success) .detail-value {
  color: #059669;
}
@keyframes progress-icon-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
@keyframes progress-icon-pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.05); opacity: 0.9; }
}
@keyframes progress-shine {
  0% { left: -100%; }
  60%, 100% { left: 100%; }
}

/* 初期在庫一括登録ダイアログ */
.batch-initial-stock-dialog :deep(.el-dialog__body) {
  padding: 0.6rem 1rem;
}
.batch-initial-filter {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.6rem 1rem;
  margin-bottom: 0.6rem;
  padding-bottom: 0.6rem;
  border-bottom: 1px solid #e5e7eb;
}
.batch-initial-filter .filter-row {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}
.batch-initial-filter .filter-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748b;
  white-space: nowrap;
}
.batch-initial-filter .month-picker {
  width: 140px;
}
.batch-initial-filter .process-select {
  width: 200px;
}
.batch-initial-filter .filter-actions {
  margin-left: auto;
  display: flex;
  gap: 0.35rem;
}
.batch-initial-table-wrap {
  font-size: 0.75rem;
}
.batch-initial-table-wrap .qty-input {
  width: 100%;
}
.batch-initial-table-wrap :deep(.el-input-number) {
  width: 120px;
}

/* 実績一括登録ダイアログ */
.batch-actual-filter {
  margin-bottom: 0.75rem;
}
.batch-actual-table-wrap {
  font-size: 0.8rem;
}

/* ========== 响应式 ========== */
@media (max-width: 992px) {
  .production-data-management {
    padding: 0.4rem;
  }
  .page-header-shell {
    padding: 0.55rem 0.65rem;
    border-radius: 14px;
  }
  .page-header-row {
    gap: 0.4rem;
  }
  .header-actions {
    flex-wrap: wrap;
  }
  .filter-section {
    gap: 0.4rem;
  }
  .filter-item {
    flex: 1 1 auto;
    min-width: 140px;
  }
  .date-filter-item {
    flex: 1 1 100%;
    min-width: 0;
  }
  .date-quick-item {
    flex: 0 0 auto;
  }
  .table-card :deep(.filter-section .el-date-editor) {
    width: 100%;
    max-width: 280px;
  }
}

@media (max-width: 768px) {
  .production-data-management {
    padding: 0.35rem;
  }
  .page-subtitle {
    display: none;
  }
  .page-title {
    font-size: 1.12rem;
  }
  .page-title-mark {
    width: 38px;
    height: 38px;
    border-radius: 12px;
  }
  .page-title-mark :deep(.el-icon) {
    font-size: 18px;
  }
  .page-header-shell {
    padding: 0.5rem 0.55rem;
  }
  .page-header-row {
    flex-direction: column;
    align-items: stretch;
    gap: 0.35rem;
  }
  .title-group {
    justify-content: space-between;
  }
  .header-actions {
    flex-wrap: wrap;
    justify-content: flex-start;
    gap: 0.25rem;
  }
  .header-actions :deep(.el-button) {
    height: 26px;
    padding: 0 8px;
    font-size: 0.7rem;
  }
  .header-actions :deep(.el-button span) {
    display: inline;
  }
  .table-card :deep(.el-card__header),
  .table-card :deep(.el-card__body) {
    padding: 0.3rem 0.4rem;
  }
  .filter-section {
    flex-direction: column;
    align-items: stretch;
    padding: 0.4rem;
    gap: 0.4rem;
  }
  .filter-item {
    flex: none;
    width: 100%;
    min-width: 0;
  }
  .filter-item .filter-label {
    min-width: 3.5em;
  }
  .date-filter-item {
    flex: none;
    width: 100%;
  }
  .date-quick-item {
    width: 100%;
  }
  .date-quick-buttons {
    justify-content: flex-start;
  }
  .table-card :deep(.filter-section .el-date-editor) {
    width: 100%;
    max-width: none;
  }
  .filter-select,
  .keyword-filter-input {
    width: 100%;
  }
  .summary-table-tabs :deep(.el-tabs__item) {
    padding: 0 8px;
    font-size: 0.7rem;
  }
  .modern-table :deep(.el-table .cell),
  .modern-table :deep(.el-table__header .cell) {
    padding: 2px 6px;
    font-size: 0.7rem;
  }
  .pagination-wrapper {
    padding: 0.35rem 0 0;
    flex-wrap: wrap;
    justify-content: center;
  }
  .column-group {
    padding: 0.4rem;
  }
  .group-columns {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 576px) {
  .production-data-management {
    padding: 0.25rem;
  }
  .page-title {
    font-size: 1rem;
  }
  .title-group :deep(.record-count.el-tag) {
    font-size: 0.7rem;
    height: 24px;
    line-height: 22px;
    padding: 0 6px;
  }
  .header-actions :deep(.el-button) {
    height: 24px;
    padding: 0 6px;
    font-size: 0.65rem;
  }
  .table-card :deep(.el-card__header),
  .table-card :deep(.el-card__body) {
    padding: 0.25rem 0.3rem;
  }
  .filter-section {
    padding: 0.3rem;
  }
  .filter-item,
  .date-filter-item,
  .date-quick-item {
    height: 26px;
  }
  .table-card :deep(.filter-section .el-date-editor .el-input__wrapper),
  .table-card :deep(.filter-section .el-select .el-input__wrapper),
  .table-card :deep(.filter-section .el-input .el-input__wrapper) {
    min-height: 24px;
  }
  .date-quick-buttons {
    height: 24px;
  }
  .date-quick-buttons :deep(.el-button) {
    height: 20px;
    padding: 0 4px;
    font-size: 0.65rem;
  }
  .summary-table-tabs :deep(.el-tabs__item) {
    height: 26px;
    line-height: 26px;
    padding: 0 6px;
    font-size: 0.65rem;
  }
  .modern-table :deep(.el-table) {
    font-size: 0.65rem;
  }
  .modern-table :deep(.el-table .cell),
  .modern-table :deep(.el-table__header .cell) {
    padding: 2px 4px;
    font-size: 0.65rem;
  }
  .pagination-compact :deep(.el-pager li),
  .pagination-compact :deep(.btn-prev),
  .pagination-compact :deep(.btn-next) {
    min-width: 24px;
    height: 24px;
    line-height: 24px;
    font-size: 0.65rem;
  }
}

/* 成型計画作成（本体は下のグローバルブロックで teleport 対応） */
.molding-plan-inner {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.molding-plan-panel {
  padding: 10px 12px 12px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
}
.molding-plan-panel__title {
  font-size: 0.6875rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: #64748b;
  text-transform: uppercase;
  margin-bottom: 6px;
}
.molding-plan-form-grid {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 2px 10px;
}
/** 条件4項目を1行に（狭い画面は横スクロール） */
.molding-plan-form-grid--cond-row {
  flex-wrap: nowrap;
  gap: 4px 8px;
  overflow-x: auto;
  overflow-y: hidden;
  padding-bottom: 2px;
  -webkit-overflow-scrolling: touch;
}
.molding-plan-form-grid--cond-row :deep(.el-form-item) {
  flex: 0 0 auto;
  margin-bottom: 0;
}
.molding-plan-form-grid--tight {
  gap: 2px 8px;
}
.molding-plan-form-grid :deep(.el-form-item) {
  margin-bottom: 4px;
  margin-right: 0;
}
.molding-plan-form-grid :deep(.el-form-item__label) {
  font-size: 0.75rem;
  font-weight: 600;
  color: #475569;
}
.molding-plan-field {
  width: 122px;
}
/** 生産計画月・基準日（幅は script の MOLDING_PLAN_PICKER_W_* とグローバル .molding-plan-dialog 内ルールと揃える） */
.molding-plan-field--month {
  width: 112px;
  max-width: 112px;
  min-width: 0;
  flex-shrink: 0;
}
.molding-plan-field--month :deep(.el-date-editor),
.molding-plan-field--month :deep(.el-input__wrapper) {
  width: 100% !important;
  max-width: 100%;
  min-width: 0 !important;
}
.molding-plan-field--base {
  width: 132px;
  max-width: 132px;
  min-width: 0;
  flex-shrink: 0;
}
.molding-plan-field--base :deep(.el-date-editor),
.molding-plan-field--base :deep(.el-input__wrapper) {
  width: 100% !important;
  max-width: 100%;
  min-width: 0 !important;
}
.molding-plan-field--wide {
  width: 168px;
}
.molding-plan-field--num {
  width: 96px;
}
.molding-plan-field--coef {
  width: 112px;
}
.molding-plan-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #e2e8f0;
}
.molding-plan-panel__title--sub {
  margin-top: 2px;
}
.molding-plan-clear-panel {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #cbd5e1;
}
.molding-plan-clear-hint {
  margin: 0 0 6px 0;
  font-size: 0.6875rem;
  line-height: 1.4;
  color: #64748b;
}
.molding-plan-clear-hint--sub {
  margin-top: 6px;
  margin-bottom: 0;
  font-size: 0.65rem;
  color: #94a3b8;
}
.molding-plan-clear-row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 8px;
}
.molding-plan-result-panel {
  padding: 8px 10px 10px;
  border-radius: 10px;
  border: 1px solid #c7d2fe;
  background: #fff;
  box-shadow: 0 1px 3px rgba(79, 70, 229, 0.06);
}
.molding-plan-result__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}
.molding-plan-result__head-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.molding-plan-result__print {
  flex-shrink: 0;
}
.molding-plan-result__title {
  font-size: 0.8125rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: 0.02em;
}
.molding-plan-result__tag {
  font-weight: 600;
}
.molding-plan-table :deep(.el-table__header th) {
  background: #f1f5f9 !important;
  color: #334155;
  font-weight: 600;
  font-size: 0.72rem;
}
.molding-plan-table :deep(.el-table__body td) {
  font-size: 0.78rem;
}
.molding-plan-table :deep(.el-table__row:hover > td) {
  background: #f8fafc !important;
}
.molding-plan-batch {
  font-weight: 700;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
}
.molding-plan-num--neg {
  color: #dc2626;
  font-weight: 700;
}
.molding-bom-dialog-body {
  padding: 0;
}
.molding-bom-panel {
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
  overflow: hidden;
}
.molding-bom-dialog-hint {
  margin: 0;
  padding: 12px 16px 10px;
  font-size: 0.8125rem;
  font-weight: 500;
  line-height: 1.55;
  letter-spacing: 0.01em;
  color: #475569;
  border-bottom: 1px solid #f1f5f9;
  background: rgba(248, 250, 252, 0.85);
}
.molding-bom-bulk-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px 12px;
  padding: 10px 14px;
  border-bottom: 1px solid #e2e8f0;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
}
.molding-bom-bulk-bar__label {
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #475569;
}
.molding-bom-bulk-field-select {
  width: 148px;
}
.molding-bom-table-wrap {
  padding: 0;
}
.molding-bom-input-num {
  width: 100%;
  max-width: 104px;
}
.molding-bom-input-num :deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
  transition: box-shadow 0.15s ease;
}
.molding-bom-input-num :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #cbd5e1 inset;
}
.molding-bom-input-num :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #6366f1 inset, 0 0 0 3px rgba(99, 102, 241, 0.15);
}
</style>

<style lang="scss">
/* 成型計画作成ダイアログ：teleport 先にも効くようグローバル */
.molding-plan-dialog.el-dialog {
  max-width: calc(100vw - 20px);
  border-radius: 14px;
  overflow: hidden;
  box-shadow:
    0 25px 50px -12px rgba(15, 23, 42, 0.2),
    0 0 0 1px rgba(148, 163, 184, 0.12);
}
.molding-plan-dialog .el-dialog__header {
  margin: 0;
  padding: 0;
  border-bottom: 1px solid rgba(226, 232, 240, 0.95);
  background: linear-gradient(125deg, #f8fafc 0%, #eef2ff 45%, #f5f3ff 100%);
}
.molding-plan-dialog .el-dialog__headerbtn {
  top: 10px;
  right: 10px;
  width: 34px;
  height: 34px;
  border-radius: 9px;
  transition: background 0.15s ease;
}
.molding-plan-dialog .el-dialog__headerbtn:hover {
  background: rgba(255, 255, 255, 0.7);
}
.molding-plan-dlg-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px 12px 14px;
  padding-right: 44px;
}
.molding-plan-dlg-header__mark {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: linear-gradient(145deg, #4f46e5 0%, #4338ca 100%);
  color: #fff;
  font-size: 20px;
  box-shadow: 0 6px 16px -4px rgba(79, 70, 229, 0.55);
}
.molding-plan-dlg-header__meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.molding-plan-dlg-header__title {
  font-size: 1rem;
  font-weight: 700;
  letter-spacing: 0.03em;
  color: #0f172a;
  line-height: 1.25;
}
.molding-plan-dlg-header__sub {
  font-size: 0.6875rem;
  font-weight: 500;
  color: #64748b;
  letter-spacing: 0.02em;
}
.molding-plan-dialog .el-dialog__body {
  padding: 10px 12px 8px;
  background: linear-gradient(180deg, #eef2ff 0%, #e2e8f0 100%);
}
/* 条件フォーム日付：Teleport 先でも効くようグローバル。EP .el-date-editor の既定幅を上書き */
.molding-plan-dialog .molding-plan-field--month.el-date-editor.el-input,
.molding-plan-dialog .molding-plan-field--month.el-input {
  width: 112px !important;
  min-width: 0 !important;
  max-width: 112px !important;
}
.molding-plan-dialog .molding-plan-field--base.el-date-editor.el-input,
.molding-plan-dialog .molding-plan-field--base.el-input {
  width: 132px !important;
  min-width: 0 !important;
  max-width: 132px !important;
}
.molding-plan-dialog .molding-plan-form-grid--cond-row.el-form--inline .el-form-item__content {
  min-width: 0 !important;
}
.molding-plan-dialog .el-dialog__footer {
  padding: 0;
  border-top: none;
}
.molding-plan-footer {
  padding: 8px 12px 10px;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
}
/* 统一按钮：高度・圆角・字重 */
.molding-plan-dialog .molding-plan-btn {
  height: 32px;
  padding: 0 12px;
  border-radius: 8px;
  font-size: 0.8125rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  border-width: 1px;
  transition:
    background 0.15s ease,
    border-color 0.15s ease,
    color 0.15s ease,
    box-shadow 0.15s ease;
}
.molding-plan-dialog .molding-plan-btn .el-icon {
  margin-right: 4px;
}
.molding-plan-dialog .molding-plan-btn--secondary {
  color: #334155;
  background: #fff;
  border-color: #cbd5e1;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.8) inset;
}
.molding-plan-dialog .molding-plan-btn--secondary:hover {
  color: #1e293b;
  background: #f8fafc;
  border-color: #94a3b8;
}
.molding-plan-dialog .molding-plan-btn--primary {
  color: #fff;
  background: linear-gradient(180deg, #4f46e5 0%, #4338ca 100%);
  border-color: #4338ca;
  box-shadow: 0 1px 2px rgba(67, 56, 202, 0.35);
}
.molding-plan-dialog .molding-plan-btn--primary:hover {
  background: linear-gradient(180deg, #6366f1 0%, #4f46e5 100%);
  border-color: #4f46e5;
}
.molding-plan-dialog .molding-plan-btn--warn {
  color: #9a3412;
  background: #fffbeb;
  border-color: #fcd34d;
}
.molding-plan-dialog .molding-plan-btn--warn:hover {
  background: #fef3c7;
  border-color: #fbbf24;
}
.molding-plan-dialog .molding-plan-btn--warn.is-disabled {
  opacity: 0.55;
}
.molding-plan-dialog .molding-plan-btn--sync {
  color: #0f766e;
  background: #f0fdfa;
  border-color: #5eead4;
}
.molding-plan-dialog .molding-plan-btn--sync:hover {
  background: #ccfbf1;
  border-color: #2dd4bf;
}
.molding-plan-dialog .molding-plan-btn--sync.is-disabled {
  opacity: 0.55;
}
.molding-plan-dialog .molding-plan-btn--close {
  min-width: 88px;
  color: #475569;
  background: #fff;
  border-color: #cbd5e1;
}
.molding-plan-dialog .molding-plan-btn--close:hover {
  color: #1e293b;
  background: #f8fafc;
  border-color: #94a3b8;
}

/* 成型機器設定ダイアログ（product_machine_config） */
.molding-machine-config-dialog.el-dialog {
  max-width: calc(100vw - 24px);
  border-radius: 14px;
  overflow: hidden;
  box-shadow:
    0 25px 50px -12px rgba(15, 23, 42, 0.2),
    0 0 0 1px rgba(148, 163, 184, 0.12);
}
.molding-machine-config-dialog .el-dialog__header {
  margin: 0;
  padding: 0;
  border-bottom: 1px solid rgba(226, 232, 240, 0.95);
  background: linear-gradient(125deg, #f8fafc 0%, #ecfeff 40%, #eef2ff 100%);
}
.molding-machine-config-dialog .el-dialog__headerbtn {
  top: 10px;
  right: 10px;
  width: 34px;
  height: 34px;
  border-radius: 9px;
}
.molding-machine-config-dialog .el-dialog__headerbtn:hover {
  background: rgba(255, 255, 255, 0.7);
}
.molding-machine-config-dlg-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px 12px 14px;
  padding-right: 44px;
}
.molding-machine-config-dlg-header__mark {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: linear-gradient(145deg, #0d9488 0%, #0f766e 100%);
  color: #fff;
  font-size: 20px;
  box-shadow: 0 6px 16px -4px rgba(13, 148, 136, 0.45);
}
.molding-machine-config-dlg-header__meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.molding-machine-config-dlg-header__eyebrow {
  font-size: 0.625rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #94a3b8;
}
.molding-machine-config-dlg-header__title {
  font-size: 1rem;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.25;
}
.molding-machine-config-dlg-header__sub {
  font-size: 0.6875rem;
  font-weight: 500;
  color: #64748b;
}
.molding-machine-config-dialog .el-dialog__body {
  padding: 12px 16px 10px;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
}
.molding-machine-config-dialog .el-dialog__footer {
  padding: 0;
  border-top: none;
}
.molding-machine-config-dialog .molding-plan-btn--close {
  margin: 8px 12px 10px;
}
.molding-machine-config-body {
  min-height: 120px;
}
.molding-machine-config-table.el-table {
  border-radius: 10px;
  overflow: hidden;
}
.molding-machine-config-select {
  width: 100%;
}

.molding-bom-compact-dialog.el-dialog {
  max-width: calc(100vw - 32px);
  border-radius: 16px;
  overflow: hidden;
  box-shadow:
    0 25px 50px -12px rgba(15, 23, 42, 0.2),
    0 0 0 1px rgba(148, 163, 184, 0.12);
}
.molding-bom-compact-dialog .el-dialog__header {
  margin: 0;
  padding: 0;
  border-bottom: 1px solid rgba(226, 232, 240, 0.95);
  background: linear-gradient(125deg, #f8fafc 0%, #eef2ff 45%, #f5f3ff 100%);
}
.molding-bom-compact-dialog .el-dialog__headerbtn {
  top: 14px;
  right: 14px;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  transition: background 0.15s ease;
}
.molding-bom-compact-dialog .el-dialog__headerbtn:hover {
  background: rgba(255, 255, 255, 0.65);
}
.molding-bom-compact-dialog .el-dialog__body {
  padding: 16px 20px 12px;
  background: linear-gradient(180deg, #f1f5f9 0%, #e2e8f0 100%);
}
.molding-bom-compact-dialog .el-dialog__footer {
  padding: 0;
  border-top: none;
}
.molding-bom-dlg-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 48px 18px 20px;
}
.molding-bom-dlg-header__mark {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: linear-gradient(145deg, #6366f1 0%, #4f46e5 100%);
  color: #fff;
  font-size: 22px;
  box-shadow: 0 8px 20px -6px rgba(79, 70, 229, 0.55);
}
.molding-bom-dlg-header__meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}
.molding-bom-dlg-header__eyebrow {
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #64748b;
  font-family: ui-monospace, 'Cascadia Code', 'Segoe UI', sans-serif;
}
.molding-bom-dlg-header__title {
  font-size: 1.125rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: #0f172a;
  line-height: 1.3;
}
.molding-bom-dlg-header__sub {
  font-size: 0.8125rem;
  font-weight: 500;
  color: #475569;
  line-height: 1.35;
}
.molding-bom-footer {
  padding: 14px 20px 16px;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  border-top: 1px solid #e2e8f0;
}
.molding-bom-compact-dialog .molding-bom-table.el-table {
  font-size: 0.8125rem;
  --el-table-header-text-color: #334155;
}
.molding-bom-compact-dialog .molding-bom-table .el-table__header th {
  font-weight: 700;
  font-size: 0.75rem;
  letter-spacing: 0.03em;
  background: linear-gradient(180deg, #f1f5f9 0%, #e8eef5 100%) !important;
  color: #334155 !important;
}
.molding-bom-compact-dialog .molding-bom-table .el-table__body td {
  font-weight: 500;
  color: #1e293b;
}
.molding-bom-compact-dialog .molding-bom-table .el-table__row:hover > td {
  background: rgba(238, 242, 255, 0.65) !important;
}
.molding-bom-compact-dialog .molding-bom-table .el-table__body tr.current-row > td {
  background: rgba(224, 231, 255, 0.5) !important;
}
</style>
