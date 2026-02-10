<template>
  <div class="production-summary-management">
    <!-- ヘッダー部分 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <div class="page-title-wrapper">
            <h1 class="page-title">
              <el-icon class="title-icon"><TrendCharts /></el-icon>
              生産工程データ管理
            </h1>
          </div>
        </div>
        <div class="header-right">
          <div class="page-meta-row">
            <div class="meta-item">
              <span class="meta-label">最新更新</span>
              <span class="meta-value">{{ lastRefreshTime || '取得中...' }}</span>
            </div>
            <div class="meta-item" v-if="dateRange && dateRange.length === 2">
              <span class="meta-label">表示期間</span>
              <span class="meta-value">{{ dateRange[0] }} ～ {{ dateRange[1] }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- メインコンテンツ -->
    <div class="main-content">
      <el-card class="table-card" shadow="hover">
        <template #header>
          <div class="table-header">
            <div class="table-header-left">
              <el-icon class="table-icon"><Grid /></el-icon>
              <span class="table-title">工程データベース</span>
              <el-tag type="info" size="small" class="record-count">
                {{ total.toLocaleString() }} 件
              </el-tag>
            </div>
            <div class="table-actions">
              <div class="action-row primary-actions">
                <el-dropdown
                  trigger="click"
                  placement="bottom-start"
                  :disabled="
                    generating ||
                    updatingCarryOver ||
                    updatingOrder ||
                    updatingActual ||
                    updatingDefect ||
                    updatingScrap ||
                    updatingOnHold ||
                    updatingProductionDates ||
                    updatingPlan ||
                    updatingInventoryTrend ||
                    updatingProductMaster ||
                    updatingMachine ||
                    updatingAll
                  "
                  class="data-actions-dropdown"
                >
                  <el-button
                    type="primary"
                    size="small"
                    :icon="MoreFilled"
                    :loading="
                      generating ||
                      updatingCarryOver ||
                      updatingOrder ||
                      updatingActual ||
                      updatingDefect ||
                      updatingScrap ||
                      updatingOnHold ||
                      updatingProductionDates ||
                      updatingPlan ||
                      updatingInventoryTrend ||
                      updatingProductMaster ||
                      updatingAll
                    "
                    class="data-actions-btn"
                  >
                    データ操作
                    <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item
                        @click="handleGenerateData"
                        :disabled="generating || updatingCarryOver || updatingOrder || updatingAll"
                        class="dropdown-item generate-item"
                      >
                        <el-icon><DocumentAdd /></el-icon>
                        <span>データ生成</span>
                      </el-dropdown-item>
                      <el-dropdown-item
                        @click="handleUpdateCarryOver"
                        :disabled="generating || updatingCarryOver || updatingOrder || updatingAll"
                        class="dropdown-item carry-over-item"
                      >
                        <el-icon><RefreshRight /></el-icon>
                        <span>繰越データ更新</span>
                      </el-dropdown-item>
                      <el-dropdown-item
                        @click="handleUpdateFromOrderDaily"
                        :disabled="
                          generating ||
                          updatingCarryOver ||
                          updatingOrder ||
                          updatingActual ||
                          updatingAll
                        "
                        class="dropdown-item order-item"
                      >
                        <el-icon><DocumentChecked /></el-icon>
                        <span>受注データ更新</span>
                      </el-dropdown-item>
                      <el-dropdown-item
                        @click="handleUpdateActual"
                        :disabled="
                          generating ||
                          updatingCarryOver ||
                          updatingOrder ||
                          updatingActual ||
                          updatingDefect ||
                          updatingScrap ||
                          updatingOnHold ||
                          updatingAll
                        "
                        class="dropdown-item actual-item"
                      >
                        <el-icon><CircleCheck /></el-icon>
                        <span>実績データ更新</span>
                      </el-dropdown-item>
                      <el-dropdown-item
                        @click="handleUpdateDefect"
                        :disabled="
                          generating ||
                          updatingCarryOver ||
                          updatingOrder ||
                          updatingActual ||
                          updatingDefect ||
                          updatingScrap ||
                          updatingOnHold ||
                          updatingAll
                        "
                        class="dropdown-item defect-item"
                      >
                        <el-icon><Warning /></el-icon>
                        <span>不良データ更新</span>
                      </el-dropdown-item>
                      <el-dropdown-item
                        @click="handleUpdateScrap"
                        :disabled="
                          generating ||
                          updatingCarryOver ||
                          updatingOrder ||
                          updatingActual ||
                          updatingDefect ||
                          updatingScrap ||
                          updatingOnHold ||
                          updatingAll
                        "
                        class="dropdown-item scrap-item"
                      >
                        <el-icon><Delete /></el-icon>
                        <span>廃棄データ更新</span>
                      </el-dropdown-item>
                      <el-dropdown-item
                        @click="handleUpdateOnHold"
                        :disabled="
                          generating ||
                          updatingCarryOver ||
                          updatingOrder ||
                          updatingActual ||
                          updatingDefect ||
                          updatingScrap ||
                          updatingOnHold ||
                          updatingProductionDates ||
                          updatingAll
                        "
                        class="dropdown-item onhold-item"
                      >
                        <el-icon><VideoPause /></el-icon>
                        <span>保留データ更新</span>
                      </el-dropdown-item>
                      <el-dropdown-item
                        @click="handleUpdateProductionDates"
                        :disabled="
                          generating ||
                          updatingCarryOver ||
                          updatingOrder ||
                          updatingActual ||
                          updatingDefect ||
                          updatingScrap ||
                          updatingOnHold ||
                          updatingProductionDates ||
                          updatingPlan ||
                          updatingAll
                        "
                        class="dropdown-item production-dates-item"
                      >
                        <el-icon><Calendar /></el-icon>
                        <span>生産計画日更新</span>
                      </el-dropdown-item>
                      <el-dropdown-item
                        @click="handleUpdatePlan"
                        :disabled="
                          generating ||
                          updatingCarryOver ||
                          updatingOrder ||
                          updatingActual ||
                          updatingDefect ||
                          updatingScrap ||
                          updatingOnHold ||
                          updatingProductionDates ||
                          updatingPlan ||
                          updatingInventoryTrend ||
                          updatingAll
                        "
                        class="dropdown-item plan-item"
                      >
                        <el-icon><Document /></el-icon>
                        <span>計画データ更新</span>
                      </el-dropdown-item>
                      <el-dropdown-item
                        @click="handleInventoryTrendUpdate"
                        :disabled="
                          generating ||
                          updatingCarryOver ||
                          updatingOrder ||
                          updatingActual ||
                          updatingDefect ||
                          updatingScrap ||
                          updatingOnHold ||
                          updatingProductionDates ||
                          updatingPlan ||
                          updatingInventoryTrend ||
                          updatingProductMaster ||
                          updatingAll
                        "
                        class="dropdown-item inventory-trend-item"
                      >
                        <el-icon><TrendCharts /></el-icon>
                        <span>在庫・推移更新</span>
                      </el-dropdown-item>
                      <el-dropdown-item
                        @click="handleUpdateProductMaster"
                        :disabled="
                          generating ||
                          updatingCarryOver ||
                          updatingOrder ||
                          updatingActual ||
                          updatingDefect ||
                          updatingScrap ||
                          updatingOnHold ||
                          updatingProductionDates ||
                          updatingPlan ||
                          updatingInventoryTrend ||
                          updatingProductMaster ||
                          updatingMachine ||
                          updatingAll
                        "
                        class="dropdown-item product-master-item"
                      >
                        <el-icon><Refresh /></el-icon>
                        <span>製品マスタ更新</span>
                      </el-dropdown-item>
                      <el-dropdown-item
                        @click="handleUpdateMachine"
                        :disabled="
                          generating ||
                          updatingCarryOver ||
                          updatingOrder ||
                          updatingActual ||
                          updatingDefect ||
                          updatingScrap ||
                          updatingOnHold ||
                          updatingProductionDates ||
                          updatingPlan ||
                          updatingInventoryTrend ||
                          updatingProductMaster ||
                          updatingMachine ||
                          updatingAll
                        "
                        class="dropdown-item machine-item"
                      >
                        <el-icon><Setting /></el-icon>
                        <span>設備フィールド更新</span>
                      </el-dropdown-item>
                      <el-dropdown-item
                        divided
                        @click="handleOpenBatchActualDialog"
                        class="dropdown-item batch-actual-item"
                      >
                        <el-icon><Edit /></el-icon>
                        <span>実績一括登録</span>
                      </el-dropdown-item>
                      <el-dropdown-item
                        @click="handleOpenInitialStockDialog"
                        class="dropdown-item initial-stock-item"
                      >
                        <el-icon><Edit /></el-icon>
                        <span>初期在庫管理</span>
                      </el-dropdown-item>
                      <el-dropdown-item
                        @click="handleOpenBatchInitialStockDialog"
                        class="dropdown-item batch-initial-stock-item"
                      >
                        <el-icon><Plus /></el-icon>
                        <span>初期在庫一括登録</span>
                      </el-dropdown-item>
                      <el-dropdown-item
                        divided
                        @click="handleAllUpdate"
                        :disabled="
                          generating ||
                          updatingCarryOver ||
                          updatingOrder ||
                          updatingActual ||
                          updatingDefect ||
                          updatingScrap ||
                          updatingOnHold ||
                          updatingProductionDates ||
                          updatingPlan ||
                          updatingInventoryTrend ||
                          updatingProductMaster ||
                          updatingAll
                        "
                        class="dropdown-item all-update-item"
                      >
                        <el-icon><RefreshRight /></el-icon>
                        <span>全部一括更新</span>
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
                <el-button
                  type="success"
                  size="small"
                  :icon="Printer"
                  class="process-print-btn-primary"
                  @click="handleProcessPrint"
                >
                  工程別計画確認印刷
                </el-button>
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
                  :icon="Setting"
                  @click="showColumnSettings = true"
                  class="modern-btn settings-btn"
                >
                  <span>列設定</span>
                </el-button>
              </div>
            </div>
          </div>
          <!-- フィルタ領域 -->
          <div class="filter-section">
            <div class="filter-row">
              <div class="filter-item date-filter-item">
                <label class="filter-label">期間</label>
                <div class="date-inline-controls">
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
                  <div class="date-quick-buttons">
                    <el-button size="small" plain @click="shiftDateRange(-1)">前日</el-button>
                    <el-button size="small" type="primary" plain @click="setTodayRange"
                      >今日</el-button
                    >
                    <el-button size="small" plain @click="shiftDateRange(1)">翌日</el-button>
                  </div>
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
              <div class="filter-item reset-filter-item">
                <el-button
                  type="default"
                  size="small"
                  :icon="RefreshLeft"
                  @click="handleResetFilter"
                  class="reset-filter-btn"
                >
                  リセット
                </el-button>
              </div>
            </div>
          </div>
        </template>

        <div class="table-content">
          <!-- 工程別タブ -->
          <div class="table-tabs-container">
            <el-tabs
              v-model="activeTableTab"
              type="card"
              class="summary-table-tabs"
              :stretch="true"
            >
              <el-tab-pane v-for="tab in tableTabs" :key="tab.key" :name="tab.key">
                <template #label>
                  <div class="tab-label">
                    <span class="tab-icon" :style="{ background: tab.color }">{{ tab.icon }}</span>
                    <div class="tab-text-group">
                      <span class="tab-text">{{ tab.label }}</span>
                    </div>
                  </div>
                </template>
              </el-tab-pane>
            </el-tabs>
          </div>

          <!-- データテーブル -->
          <el-table
            :data="tableData"
            v-loading="loading"
            stripe
            border
            class="modern-table"
            :default-sort="{ prop: 'product_name', order: 'ascending' }"
            :height="'calc(60vh - 60px)'"
            @sort-change="handleSortChange"
            @cell-dblclick="handleCellDoubleClick"
            :cell-style="cellStyleHandler"
            :header-cell-style="headerCellStyle"
            size="small"
            show-summary
            :summary-method="getSummaries"
          >
            <!-- 基本情報 -->
            <el-table-column
              v-if="visibleColumns.id"
              prop="id"
              label="ID"
              width="80"
              fixed="left"
              align="center"
            />
            <el-table-column
              v-if="visibleColumns.date"
              prop="date"
              label="日付"
              width="90"
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
              v-if="visibleColumns.day_of_week"
              prop="day_of_week"
              label="曜日"
              width="60"
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
              v-if="visibleColumns.route_cd"
              prop="route_cd"
              label="工程グループ"
              width="120"
              fixed="left"
              align="center"
            />
            <el-table-column
              v-if="visibleColumns.product_cd"
              prop="product_cd"
              label="製品CD"
              width="70"
              fixed="left"
              align="center"
            />
            <el-table-column
              v-if="visibleColumns.product_name"
              prop="product_name"
              label="製品名"
              width="110"
              fixed="left"
              show-overflow-tooltip
              sortable="custom"
              :sort-orders="['ascending', 'descending']"
            >
              <template #default="{ row }">
                <span class="product-name-cell">{{ row.product_name }}</span>
              </template>
            </el-table-column>

            <!-- 受注・内示 -->
            <el-table-column
              v-if="visibleColumns.order_quantity"
              prop="order_quantity"
              label="受注数"
              width="70"
              align="center"
            >
              <template #default="{ row }">
                <span class="number-cell">{{
                  row.order_quantity && row.order_quantity !== 0
                    ? row.order_quantity.toLocaleString()
                    : ''
                }}</span>
              </template>
            </el-table-column>
            <el-table-column
              v-if="visibleColumns.forecast_quantity"
              prop="forecast_quantity"
              label="内示数"
              width="70"
              align="center"
            >
              <template #default="{ row }">
                <span class="number-cell">{{
                  row.forecast_quantity && row.forecast_quantity !== 0
                    ? row.forecast_quantity.toLocaleString()
                    : ''
                }}</span>
              </template>
            </el-table-column>

            <!-- 動的に表示する工程別カラム -->
            <template v-for="col in dynamicColumns" :key="col.prop">
              <el-table-column
                v-if="visibleColumns[col.prop]"
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
                    {{ row[col.prop] || '-' }}
                  </span>
                  <span
                    v-else
                    class="number-cell"
                    :class="{
                      negative: (row[col.prop] ?? 0) < 0,
                      positive: (row[col.prop] ?? 0) > 0,
                    }"
                  >
                    {{ row[col.prop] && row[col.prop] !== 0 ? row[col.prop].toLocaleString() : '' }}
                  </span>
                </template>
              </el-table-column>
            </template>
          </el-table>

          <!-- ページネーション -->
          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[50, 100, 150, 200]"
              :total="total"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handlePageSizeChange"
              @current-change="handlePageChange"
            />
          </div>
        </div>
      </el-card>
    </div>

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
              <span class="detail-value highlight"
                >{{ generateDateRange.start }} ～ {{ generateDateRange.end }}</span
              >
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
          <el-button @click="showGenerateConfirmDialog = false" class="cancel-btn">
            キャンセル
          </el-button>
          <el-button type="primary" @click="confirmGenerateData" class="confirm-btn">
            生成開始
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 受注データ更新モード選択ダイアログ -->
    <el-dialog
      v-model="showUpdateModeDialog"
      title="受注データ更新モード選択"
      width="500px"
      class="update-mode-dialog"
      :close-on-click-modal="false"
    >
      <div class="update-mode-content">
        <div class="mode-options">
          <div
            class="mode-option"
            :class="{ active: updateMode === 'changed' }"
            @click="updateMode = 'changed'"
          >
            <div class="mode-header">
              <el-icon class="mode-icon"><Check /></el-icon>
              <span class="mode-title">変更されたデータのみ更新（推奨）</span>
            </div>
            <p class="mode-description">
              既存データと比較して、変更されたデータのみ更新します。処理が高速です。
            </p>
          </div>
          <div
            class="mode-option"
            :class="{ active: updateMode === 'all' }"
            @click="updateMode = 'all'"
          >
            <div class="mode-header">
              <el-icon class="mode-icon"><Refresh /></el-icon>
              <span class="mode-title">すべてのデータを強制更新</span>
            </div>
            <p class="mode-description">
              すべてのデータを強制的に更新します。処理に時間がかかる場合があります。
            </p>
          </div>
          <div
            class="mode-option"
            :class="{ active: updateMode === 'recent' }"
            @click="updateMode = 'recent'"
          >
            <div class="mode-header">
              <el-icon class="mode-icon"><Calendar /></el-icon>
              <span class="mode-title">最近N日間のデータを更新</span>
            </div>
            <p class="mode-description">最近のデータのみ更新します。日数を指定してください。</p>
            <div class="days-input-wrapper" v-if="updateMode === 'recent'">
              <label class="days-label">日数:</label>
              <el-input-number
                v-model="updateDays"
                :min="1"
                :max="365"
                size="small"
                class="days-input"
                :disabled="updateMode !== 'recent'"
              />
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showUpdateModeDialog = false" class="cancel-btn">
            キャンセル
          </el-button>
          <el-button type="primary" @click="confirmUpdateMode" class="confirm-btn">
            更新開始
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 在庫・推移更新確認ダイアログ -->
    <el-dialog
      v-model="showInventoryTrendUpdateConfirmDialog"
      title="在庫・推移更新確認"
      width="500px"
      :close-on-click-modal="false"
    >
      <div class="confirm-dialog-content">
        <p>
          在庫・推移データを更新します。
          <br />
          繰越データに基づいて開始日を自動計算し、その日から3ヶ月間のデータを更新します。
        </p>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showInventoryTrendUpdateConfirmDialog = false" class="cancel-btn">
            キャンセル
          </el-button>
          <el-button type="primary" @click="confirmInventoryTrendUpdate" class="confirm-btn">
            更新
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 計画データ更新確認ダイアログ -->
    <el-dialog
      v-model="showPlanConfirmDialog"
      title="計画データ更新確認"
      width="500px"
      :close-on-click-modal="false"
    >
      <div class="confirm-dialog-content">
        <p>
          計画データを更新しますか？
        </p>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showPlanConfirmDialog = false" class="cancel-btn">
            キャンセル
          </el-button>
          <el-button type="primary" @click="confirmUpdatePlan" class="confirm-btn">
            更新
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 全部一括更新確認ダイアログ -->
    <el-dialog
      v-model="showAllUpdateConfirmDialog"
      title="全部一括更新確認"
      width="500px"
      :close-on-click-modal="false"
    >
      <div class="confirm-dialog-content">
        <p>
          以下の順序で全てのデータを一括更新します：
          <br />
          <br />
          1. 受注データ更新
          <br />
          2. 実績データ更新
          <br />
          3. 不良データ更新
          <br />
          4. 廃棄データ更新
          <br />
          5. 保留データ更新
          <br />
          6. 計画データ更新
          <br />
          7. 在庫・推移更新
          <br />
          <br />
          この処理には時間がかかる場合があります。
        </p>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showAllUpdateConfirmDialog = false" class="cancel-btn">
            キャンセル
          </el-button>
          <el-button type="primary" @click="confirmAllUpdate" class="confirm-btn">
            一括更新開始
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 実績一括登録ダイアログ -->
    <el-dialog
      v-model="showBatchActualDialog"
      title="実績一括登録"
      width="900px"
      class="batch-actual-dialog"
      :close-on-click-modal="false"
    >
      <div class="batch-actual-content">
        <div class="batch-actual-date-picker">
          <el-form-item label="日付" required>
            <el-date-picker
              v-model="batchActualDate"
              type="date"
              placeholder="日付を選択"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              :locale="jaLocale"
              style="width: 200px"
              @change="handleBatchActualDateChange"
            />
          </el-form-item>
        </div>
        <el-table
          :data="batchActualTableData"
          border
          stripe
          class="batch-actual-table"
          size="small"
        >
          <el-table-column prop="product_cd" label="製品" width="200">
            <template #default="{ row, $index }">
              <el-select
                v-model="row.product_cd"
                placeholder="製品を選択"
                filterable
                clearable
                style="width: 100%"
                @change="handleProductChange($index, $event)"
              >
                <el-option
                  v-for="product in productList"
                  :key="product.product_cd"
                  :label="`${product.product_cd} - ${product.product_name || ''}`"
                  :value="product.product_cd"
                />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column prop="date" label="日付" width="150">
            <template #default="{ row }">
              <span>{{ row.date || batchActualDate || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="cuttingActual" label="切断実績" width="150">
            <template #default="{ row }">
              <el-input-number
                v-model="row.cuttingActual"
                :precision="0"
                placeholder="0"
                style="width: 100%"
                controls-position="right"
              />
            </template>
          </el-table-column>
          <el-table-column prop="chamferingActual" label="面取実績" width="150">
            <template #default="{ row }">
              <el-input-number
                v-model="row.chamferingActual"
                :precision="0"
                placeholder="0"
                style="width: 100%"
                controls-position="right"
              />
            </template>
          </el-table-column>
          <el-table-column prop="moldingActual" label="成型実績" width="150">
            <template #default="{ row }">
              <el-input-number
                v-model="row.moldingActual"
                :precision="0"
                placeholder="0"
                style="width: 100%"
                controls-position="right"
              />
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleResetBatchActual" class="cancel-btn"> リセット </el-button>
          <el-button @click="showBatchActualDialog = false" class="cancel-btn">
            キャンセル
          </el-button>
          <el-button
            type="primary"
            @click="handleSubmitBatchActual"
            :loading="submittingBatchActual"
            class="confirm-btn"
          >
            保存
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 在庫取引ログ入力ダイアログ -->
    <el-dialog
      v-model="showTransactionInputDialog"
      title="在庫取引ログ入力"
      width="580px"
      class="transaction-input-dialog"
      :close-on-click-modal="false"
    >
      <div v-if="transactionInputInfo" class="transaction-input-info">
        <div class="info-grid">
          <div class="info-item">
            <div class="info-label">日付</div>
            <div class="info-value">{{ transactionInputInfo.date }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">製品CD</div>
            <div class="info-value">{{ transactionInputInfo.productCd }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">製品名</div>
            <div class="info-value">{{ transactionInputInfo.productName }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">工程</div>
            <div class="info-value">
              {{ transactionInputInfo.processName }} ({{ transactionInputInfo.processCd }})
            </div>
          </div>
        </div>
      </div>

      <div class="transaction-form-container">
        <el-form
          :model="transactionForm"
          label-width="80px"
          class="transaction-form"
          size="default"
        >
          <!-- 倉庫工程フィールド -->
          <div v-if="transactionInputInfo?.processCd === 'KT13'" class="form-grid">
            <div class="form-item-card inbound-card">
              <div class="form-item-header">
                <span class="form-item-icon">📥</span>
                <span class="form-item-title">入庫</span>
              </div>
              <el-input
                v-model.number="transactionForm.inbound"
                type="number"
                :min="0"
                class="input-compact"
                placeholder="数量を入力"
              />
            </div>
            <div class="form-item-card outbound-card">
              <div class="form-item-header">
                <span class="form-item-icon">📤</span>
                <span class="form-item-title">出庫</span>
              </div>
              <el-input
                v-model.number="transactionForm.outbound"
                type="number"
                :min="0"
                class="input-compact"
                placeholder="数量を入力"
              />
            </div>
            <div class="form-item-card scrap-card">
              <div class="form-item-header">
                <span class="form-item-icon">🗑</span>
                <span class="form-item-title">廃棄</span>
              </div>
              <el-input
                v-model.number="transactionForm.scrap"
                type="number"
                :min="0"
                class="input-compact"
                placeholder="数量を入力"
              />
            </div>
            <div class="form-item-card onhold-card">
              <div class="form-item-header">
                <span class="form-item-icon">⏸</span>
                <span class="form-item-title">保留</span>
              </div>
              <el-input
                v-model.number="transactionForm.onHold"
                type="number"
                :min="0"
                class="input-compact"
                placeholder="数量を入力"
              />
            </div>
          </div>
          <!-- 外注倉庫工程フィールド -->
          <div v-else-if="transactionInputInfo?.processCd === 'KT15'" class="form-grid">
            <div class="form-item-card inbound-card">
              <div class="form-item-header">
                <span class="form-item-icon">📥</span>
                <span class="form-item-title">入庫</span>
              </div>
              <el-input
                v-model.number="transactionForm.actual"
                type="number"
                :min="0"
                class="input-compact"
                placeholder="数量を入力"
              />
            </div>
            <div class="form-item-card scrap-card">
              <div class="form-item-header">
                <span class="form-item-icon">🗑</span>
                <span class="form-item-title">廃棄</span>
              </div>
              <el-input
                v-model.number="transactionForm.scrap"
                type="number"
                :min="0"
                class="input-compact"
                placeholder="数量を入力"
              />
            </div>
          </div>
          <!-- 通常工程フィールド -->
          <div v-else class="form-grid">
            <div class="form-item-card actual-card">
              <div class="form-item-header">
                <span class="form-item-icon">✓</span>
                <span class="form-item-title">実績</span>
              </div>
              <el-input
                v-model.number="transactionForm.actual"
                type="number"
                :min="0"
                class="input-compact"
                placeholder="数量を入力"
              />
            </div>
            <div class="form-item-card defect-card">
              <div class="form-item-header">
                <span class="form-item-icon">⚠</span>
                <span class="form-item-title">不良</span>
              </div>
              <el-input
                v-model.number="transactionForm.defect"
                type="number"
                :min="0"
                class="input-compact"
                placeholder="数量を入力"
              />
            </div>
            <div class="form-item-card scrap-card">
              <div class="form-item-header">
                <span class="form-item-icon">🗑</span>
                <span class="form-item-title">廃棄</span>
              </div>
              <el-input
                v-model.number="transactionForm.scrap"
                type="number"
                :min="0"
                class="input-compact"
                placeholder="数量を入力"
              />
            </div>
            <div class="form-item-card onhold-card">
              <div class="form-item-header">
                <span class="form-item-icon">⏸</span>
                <span class="form-item-title">保留</span>
              </div>
              <el-input
                v-model.number="transactionForm.onHold"
                type="number"
                :min="0"
                class="input-compact"
                placeholder="数量を入力"
              />
            </div>
          </div>
        </el-form>
      </div>

      <template #footer>
        <div class="dialog-footer-compact">
          <el-button @click="showTransactionInputDialog = false" size="default"
            >キャンセル</el-button
          >
          <el-button
            type="primary"
            @click="handleSubmitTransaction"
            :loading="submittingTransaction"
            size="default"
          >
            登録
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- データ生成進度ダイアログ -->
    <el-dialog
      v-model="showProgressDialog"
      title="データ生成中"
      width="500px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
      class="progress-dialog"
    >
      <div class="progress-content">
        <div class="progress-info">
          <el-icon class="progress-icon"><Loading /></el-icon>
          <span class="progress-text">{{ progressText }}</span>
        </div>
        <el-progress
          :percentage="Math.round(progressPercentage)"
          :status="progressStatus"
          :stroke-width="12"
          class="progress-bar"
        />
        <div class="progress-details">
          <div class="progress-detail-item">
            <span class="detail-label">進捗:</span>
            <span class="detail-value">{{ Math.round(progressPercentage) }}%</span>
          </div>
          <div class="progress-detail-item" v-if="progressInfo.products > 0">
            <span class="detail-label">製品:</span>
            <span class="detail-value"
              >{{ progressInfo.processedProducts }} / {{ progressInfo.products }}</span
            >
          </div>
          <div class="progress-detail-item" v-if="progressInfo.dates > 0">
            <span class="detail-label">日付:</span>
            <span class="detail-value"
              >{{ progressInfo.processedDates }} / {{ progressInfo.dates }}</span
            >
          </div>
          <div
            class="progress-detail-item"
            v-if="progressInfo.inserted > 0 || progressInfo.skipped > 0"
          >
            <span class="detail-label">生成:</span>
            <span class="detail-value success-text">{{
              progressInfo.inserted.toLocaleString()
            }}</span>
          </div>
          <div class="progress-detail-item" v-if="progressInfo.skipped > 0">
            <span class="detail-label">スキップ:</span>
            <span class="detail-value warning-text">{{
              progressInfo.skipped.toLocaleString()
            }}</span>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 列設定ダイアログ -->
    <el-dialog
      v-model="showColumnSettings"
      title="列設定"
      width="700px"
      class="column-settings-dialog"
    >
      <div class="column-settings-content">
        <div class="column-settings-actions">
          <el-button size="small" @click="selectAllColumns">すべて選択</el-button>
          <el-button size="small" @click="deselectAllColumns">すべて解除</el-button>
          <el-button size="small" @click="resetColumnSettings">デフォルトに戻す</el-button>
        </div>
        <div class="column-groups">
          <div v-for="(columns, groupName) in groupedColumns" :key="groupName" class="column-group">
            <div class="group-header">
              <el-checkbox
                :model-value="isGroupAllSelected(groupName)"
                :indeterminate="isGroupIndeterminate(groupName)"
                @change="(val: boolean | string | number) => toggleGroup(groupName, Boolean(val))"
              >
                {{ groupName }}
              </el-checkbox>
            </div>
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
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showColumnSettings = false">閉じる</el-button>
          <el-button type="primary" @click="saveColumnSettings">保存</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 繰越編集ダイアログ -->
    <el-dialog
      v-model="showCarryOverEditDialog"
      title="繰越データ編集"
      width="500px"
      :close-on-click-modal="false"
      class="carry-over-edit-dialog"
    >
      <div class="carry-over-edit-content">
        <div class="edit-info-grid">
          <div class="info-item">
            <span class="info-label">日付</span>
            <span class="info-value">{{ carryOverEditData.date }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">製品</span>
            <span class="info-value"
              >{{ carryOverEditData.productCd }} - {{ carryOverEditData.productName }}</span
            >
          </div>
          <div class="info-item">
            <span class="info-label">工程</span>
            <span class="info-value">{{ carryOverEditData.processName }}</span>
          </div>
        </div>

        <el-form class="edit-form" label-width="100px">
          <el-form-item label="繰越数">
            <el-input-number
              v-model="carryOverEditValue"
              :min="0"
              :precision="0"
              controls-position="right"
              style="width: 100%"
            />
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showCarryOverEditDialog = false">キャンセル</el-button>
          <el-button
            type="primary"
            @click="handleCarryOverEditSubmit"
            :loading="submittingCarryOverEdit"
          >
            更新
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 初期在庫管理ダイアログ -->
    <el-dialog
      v-model="showInitialStockDialog"
      title="初期在庫管理"
      width="60%"
      class="initial-stock-dialog"
      :close-on-click-modal="false"
    >
      <div class="initial-stock-toolbar">
        <div class="toolbar-left">
          <el-date-picker
            v-model="initialStockFilter.month"
            type="month"
            placeholder="月を選択"
            format="YYYY-MM"
            value-format="YYYY-MM"
            style="width: 160px"
            @change="handleInitialStockSearch"
          />
          <el-input
            v-model="initialStockFilter.keyword"
            placeholder="製品CD・製品名で検索"
            clearable
            style="width: 300px; margin-left: 10px"
            @input="handleInitialStockSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-select
            v-model="initialStockFilter.processCd"
            placeholder="工程を選択"
            clearable
            style="width: 200px; margin-left: 10px"
            @change="handleInitialStockSearch"
          >
            <el-option
              v-for="(name, cd) in processCdToName"
              :key="cd"
              :label="`${name} (${cd})`"
              :value="cd"
            />
          </el-select>
        </div>
        <div class="toolbar-right">
          <el-button type="primary" :icon="Refresh" @click="fetchInitialStockData">
            更新
          </el-button>
        </div>
      </div>

      <el-table
        :data="initialStockData"
        v-loading="loadingInitialStock"
        stripe
        border
        class="initial-stock-table"
        :height="500"
        size="small"
        :default-sort="{ prop: 'target_name', order: 'ascending' }"
      >
        <el-table-column
          prop="transaction_time"
          label="取引日時"
          width="120"
          align="center"
          sortable
        >
          <template #default="{ row }">
            {{ formatDateOnly(row.transaction_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="target_cd" label="製品CD" width="100" align="center" sortable />
        <el-table-column
          prop="target_name"
          label="製品名"
          min-width="180"
          show-overflow-tooltip
          sortable
        />
        <el-table-column prop="process_name" label="工程名" width="120" align="center" sortable />
        <el-table-column prop="quantity" label="数量" width="160" align="right" sortable>
          <template #default="{ row }">
            <span v-if="!row.editing" class="quantity-text">{{ row.quantity }}</span>
            <el-input-number
              v-else
              v-model="row.editQuantity"
              :precision="0"
              :min="0"
              size="small"
              style="width: 100%"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" align="center" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button
                v-if="!row.editing"
                type="primary"
                size="small"
                :icon="Edit"
                @click="handleEditInitialStock(row)"
                class="edit-btn"
              >
                編集
              </el-button>
              <template v-else>
                <el-button
                  type="success"
                  size="small"
                  :icon="Check"
                  @click="handleSaveInitialStock(row)"
                  class="save-btn"
                >
                  保存
                </el-button>
                <el-button
                  type="default"
                  size="small"
                  :icon="Close"
                  @click="handleCancelEditInitialStock(row)"
                  class="cancel-btn"
                >
                  取消
                </el-button>
              </template>
              <el-button
                type="danger"
                size="small"
                :icon="Delete"
                @click="handleDeleteInitialStock(row)"
                class="delete-btn"
              >
                削除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="initial-stock-pagination">
        <el-pagination
          v-model:current-page="initialStockPagination.currentPage"
          v-model:page-size="initialStockPagination.pageSize"
          :page-sizes="[50, 100, 150, 200, 300]"
          :total="initialStockPagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleInitialStockSizeChange"
          @current-change="handleInitialStockPageChange"
          background
          small
        />
      </div>
    </el-dialog>

    <!-- 初期在庫一括登録ダイアログ -->
    <el-dialog
      v-model="showBatchInitialStockDialog"
      title="初期在庫一括登録"
      width="58%"
      class="batch-initial-stock-dialog"
      :close-on-click-modal="false"
    >
      <div class="batch-initial-stock-body">
        <div class="batch-initial-stock-toolbar glass-panel compact-panel">
          <div class="toolbar-left">
            <div class="toolbar-field">
              <span class="field-label">対象月</span>
              <el-date-picker
                v-model="batchInitialStockFilter.month"
                type="month"
                placeholder="月を選択"
                format="YYYY-MM"
                value-format="YYYY-MM"
                class="toolbar-control toolbar-date"
                @change="handleBatchInitialStockSearch"
              />
            </div>
            <div class="toolbar-field">
              <span class="field-label">工程</span>
              <el-select
                v-model="batchInitialStockFilter.processCd"
                placeholder="工程を選択"
                clearable
                class="toolbar-control toolbar-process"
                @change="handleBatchInitialStockSearch"
              >
                <el-option
                  v-for="(name, cd) in processCdToName"
                  :key="cd"
                  :label="`${name} (${cd})`"
                  :value="cd"
                />
              </el-select>
            </div>
            <el-button type="primary" :icon="Search" @click="handleBatchInitialStockSearch">
              検索
            </el-button>
          </div>
          <div class="toolbar-right">
            <el-button
              type="success"
              :icon="Check"
              @click="handleSaveBatchInitialStock"
              :loading="submittingBatchInitialStock"
            >
              一括保存
            </el-button>
          </div>
        </div>

        <div class="batch-initial-stock-summary compact-panel">
          <div class="summary-card input-total">
            <div class="summary-label">数量合計</div>
            <div class="summary-value">{{ formatNumber(batchInitialTotals.input) }}</div>
          </div>
          <div class="summary-card existing-total">
            <div class="summary-label">既存数量合計</div>
            <div class="summary-value">{{ formatNumber(batchInitialTotals.existing) }}</div>
          </div>
        </div>

        <el-table
          :data="batchInitialStockData"
          v-loading="loadingBatchInitialStock"
          stripe
          border
          class="batch-initial-stock-table"
          :height="440"
          size="small"
          :default-sort="{ prop: 'product_name', order: 'ascending' }"
        >
          <el-table-column prop="product_cd" label="製品CD" width="110" align="center" sortable />
          <el-table-column
            prop="product_name"
            label="製品名"
            min-width="200"
            show-overflow-tooltip
            sortable
          />
          <el-table-column prop="quantity" label="数量" width="150" align="right" sortable>
            <template #default="{ row }">
              <el-input
                v-model="row.editQuantity"
                type="number"
                placeholder="数量を入力"
                class="plain-number-input compact-input"
                @input="(val: string) => (row.editQuantity = val === '' ? null : Number(val))"
              />
            </template>
          </el-table-column>
          <el-table-column prop="existing_quantity" label="既存数量" width="140" align="right">
            <template #default="{ row }">
              <span
                v-if="row.existing_quantity !== null && row.existing_quantity !== undefined"
                class="existing-quantity-text"
              >
                {{ row.existing_quantity }}
              </span>
              <span v-else class="no-data-text">-</span>
            </template>
          </el-table-column>
          <el-table-column prop="transaction_time" label="既存取引日時" width="150" align="center">
            <template #default="{ row }">
              <span v-if="row.transaction_time">{{ formatDateOnly(row.transaction_time) }}</span>
              <span v-else class="no-data-text">-</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>

    <!-- 工程別印刷日付選択ダイアログ -->
    <el-dialog
      v-model="showPrintDateDialog"
      title="工程別計画確認印刷 - 対象日選択"
      width="450px"
      class="print-date-dialog"
      :close-on-click-modal="false"
    >
      <div class="print-date-content">
        <p class="date-select-description">印刷対象の日付を選択してください</p>
        <el-date-picker
          v-model="printTargetDate"
          type="date"
          placeholder="日付を選択"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          style="width: 100%"
          size="default"
        />
      </div>
      <template #footer>
        <div class="dialog-footer-compact">
          <el-button size="small" @click="showPrintDateDialog = false">キャンセル</el-button>
          <el-button
            type="primary"
            size="small"
            @click="handleConfirmPrintDate"
            :disabled="!printTargetDate"
          >
            印刷
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 製品マスタ更新期間選択ダイアログ -->
    <el-dialog
      v-model="showProductMasterUpdateDialog"
      title="製品マスタ更新"
      width="500px"
      class="product-master-update-dialog"
      :close-on-click-modal="false"
    >
      <div class="product-master-update-content">
        <div class="date-range-section">
          <label class="date-range-label">更新期間:</label>
          <el-date-picker
            v-model="productMasterDateRange"
            type="daterange"
            range-separator="～"
            start-placeholder="開始日"
            end-placeholder="終了日"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            :shortcuts="datePickerShortcuts"
            :locale="jaLocale"
            size="default"
            class="date-range-picker"
          />
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showProductMasterUpdateDialog = false" class="cancel-btn">
            キャンセル
          </el-button>
          <el-button
            type="primary"
            @click="confirmUpdateProductMaster"
            :disabled="!productMasterDateRange || productMasterDateRange.length !== 2"
            class="confirm-btn"
          >
            更新開始
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 機器フィールド更新期間選択ダイアログ -->
    <el-dialog
      v-model="showMachineUpdateDialog"
      title="設備フィールド更新"
      width="500px"
      class="machine-update-dialog"
      :close-on-click-modal="false"
    >
      <div class="machine-update-content">
        <div class="date-range-section">
          <label class="date-range-label">更新期間:</label>
          <el-date-picker
            v-model="machineDateRange"
            type="daterange"
            range-separator="～"
            start-placeholder="開始日"
            end-placeholder="終了日"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            :shortcuts="datePickerShortcuts"
            :locale="jaLocale"
            size="default"
            class="date-range-picker"
          />
        </div>
        <div class="update-description">
          <el-alert
            title="更新内容"
            type="info"
            :closable="false"
            show-icon
          >
            <template #default>
              <div style="font-size: 12px; line-height: 1.6;">
                <p>product_machine_configテーブルから各工程の機器情報を取得し、</p>
                <p>machinesテーブルからmachine_nameを取得してproduction_summarysテーブルを更新します。</p>
                <p>更新対象フィールド:</p>
                <ul style="margin: 8px 0; padding-left: 20px;">
                  <li>cutting_machine (切断機)</li>
                  <li>chamfering_machine (面取機)</li>
                  <li>molding_machine (成型機)</li>
                  <li>plating_machine (メッキ機)</li>
                  <li>welding_machine (溶接機)</li>
                  <li>inspector_machine (検査機)</li>
                  <li>outsourced_plating_machine (外注メッキ機)</li>
                  <li>outsourced_welding_machine (外注溶接機)</li>
                </ul>
              </div>
            </template>
          </el-alert>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showMachineUpdateDialog = false" class="cancel-btn">
            キャンセル
          </el-button>
          <el-button
            type="primary"
            @click="confirmUpdateMachine"
            :disabled="!machineDateRange || machineDateRange.length !== 2"
            class="confirm-btn"
          >
            更新開始
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Search,
  RefreshLeft,
  Refresh,
  Grid,
  Setting,
  Printer,
  TrendCharts,
  DocumentAdd,
  InfoFilled,
  Loading,
  RefreshRight,
  DocumentChecked,
  Check,
  Calendar,
  MoreFilled,
  ArrowDown,
  CircleCheck,
  Warning,
  Delete,
  VideoPause,
  Document,
  Edit,
  Plus,
  Close,
} from '@element-plus/icons-vue'
import {
  getProductionSummarysList,
  getProductionSummarysProducts,
  generateProductionSummarys,
  clearProductionSummarysCarryOver,
  updateProductionSummarysCarryOver,
  updateProductionSummarysActual,
  updateProductionSummarysDefect,
  updateProductionSummarysScrap,
  updateProductionSummarysOnHold,
  clearProductionSummarysCalculatedFields,
  updateProductionSummarysInventory,
  updateProductionSummarysTrend,
  updateProductionSummarysProductionDates,
  updateProductionSummarysPlan,
  updateProductionSummarysFromOrderDaily,
  updateProductionSummarysProductMaster,
  updateProductionSummarysMachine,
} from '@/api/database'
import { getProductRouteSteps } from '@/api/priceManagement'
import request from '@/utils/request'
import { ElMessageBox } from 'element-plus'
import jaLocale from 'element-plus/es/locale/lang/ja'
import dayjs from 'dayjs'
import 'dayjs/locale/ja'

// 设置 dayjs 使用日文语言
dayjs.locale('ja')

// 日本時区ユーティリティ
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

const createDefaultDateRange = () => {
  const { year, month, date } = getCurrentJSTInfo()
  const todayStr = getJSTDateString(year, month, date)
  return [todayStr, todayStr] as [string, string]
}

const formatDateToString = (input: Date) => {
  const year = input.getFullYear()
  const month = String(input.getMonth() + 1).padStart(2, '0')
  const day = String(input.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const parseDateString = (dateStr: string) => {
  const [year, month, day] = dateStr.split('-').map(Number)
  return new Date(year, (month || 1) - 1, day || 1)
}

const createShortcutRange = (days: number) => {
  const now = new Date()
  const end = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const start = new Date(end)
  start.setDate(start.getDate() - (days - 1))
  return [start, end]
}

// 获取月份的第一天和最后一天
const getMonthRange = (year: number, month: number) => {
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  return [firstDay, lastDay]
}

const datePickerShortcuts: Array<{ text: string; value: () => Date[] }> = [
  { text: '過去7日', value: () => createShortcutRange(7) },
  { text: '過去14日', value: () => createShortcutRange(14) },
  { text: '過去30日', value: () => createShortcutRange(30) },
  {
    text: '月初',
    value: () => {
      const now = new Date()
      const firstDay = new Date(now.getFullYear(), now.getMonth(), 1)
      return [firstDay, new Date(firstDay)]
    },
  },
  {
    text: '月末',
    value: () => {
      const now = new Date()
      const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0)
      return [lastDay, new Date(lastDay)]
    },
  },
  {
    text: '前月',
    value: () => {
      const now = new Date()
      const lastMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1)
      return getMonthRange(lastMonth.getFullYear(), lastMonth.getMonth())
    },
  },
  {
    text: '今月',
    value: () => {
      const now = new Date()
      return getMonthRange(now.getFullYear(), now.getMonth())
    },
  },
  {
    text: '翌月',
    value: () => {
      const now = new Date()
      const nextMonth = new Date(now.getFullYear(), now.getMonth() + 1, 1)
      return getMonthRange(nextMonth.getFullYear(), nextMonth.getMonth())
    },
  },
]

// リアクティブデータ
const loading = ref(false)
const tableData = ref<any[]>([])
const currentPage = ref(1)
const pageSize = ref(150)
const total = ref(0)
const lastRefreshTime = ref<string>('')

// 筛选条件
const dateRange = ref<[string, string] | null>(createDefaultDateRange())
const filterProductCd = ref('')
const filterKeyword = ref('')
let keywordFilterTimer: ReturnType<typeof setTimeout> | null = null
const sortBy = ref<string>('product_name')
const sortOrder = ref<'ASC' | 'DESC'>('ASC')

// 製品リスト
const productList = ref<Array<{ product_cd: string; product_name?: string }>>([])

// 列設定
const showColumnSettings = ref(false)

// データ生成
const showGenerateConfirmDialog = ref(false)
const generateDateRange = ref({ start: '', end: '' })
const generating = ref(false)
const showProgressDialog = ref(false)
const progressPercentage = ref(0)
const progressStatus = ref<'success' | 'exception' | 'warning' | ''>('')
const progressText = ref('データ生成を準備中...')
const progressInfo = ref({
  current: 0,
  total: 0,
  products: 0,
  dates: 0,
  processedProducts: 0,
  processedDates: 0,
  inserted: 0,
  skipped: 0,
  currentProduct: '',
  currentDate: '',
})

// 繰越データ更新
const updatingCarryOver = ref(false)

// 受注データ更新
const updatingOrder = ref(false)
const updateMode = ref<'all' | 'changed' | 'recent'>('changed')
const updateDays = ref(30)
const showUpdateModeDialog = ref(false)

// 実績データ更新
const updatingActual = ref(false)

// 不良データ更新
const updatingDefect = ref(false)

// 廃棄データ更新
const updatingScrap = ref(false)

// 保留データ更新
const updatingOnHold = ref(false)

// 在庫・推移更新
const updatingInventoryTrend = ref(false)
const showInventoryTrendUpdateConfirmDialog = ref(false)

// 全部一括更新
const updatingAll = ref(false)
const showAllUpdateConfirmDialog = ref(false)

// 生産計画日更新
const updatingProductionDates = ref(false)

// 計画データ更新
const updatingPlan = ref(false)
const showPlanConfirmDialog = ref(false)

// 製品マスタ更新
const updatingProductMaster = ref(false)
const showProductMasterUpdateDialog = ref(false)
const productMasterDateRange = ref<[string, string] | null>(null)

// 機器フィールド更新
const updatingMachine = ref(false)
const showMachineUpdateDialog = ref(false)
const machineDateRange = ref<[string, string] | null>(null)

// 実績一括登録
const showBatchActualDialog = ref(false)
const submittingBatchActual = ref(false)
const batchActualDate = ref('')
const batchActualTableData = ref([
  {
    product_cd: '',
    product_name: '',
    date: '',
    cuttingActual: null as number | null,
    chamferingActual: null as number | null,
    moldingActual: null as number | null,
  },
  {
    product_cd: '',
    product_name: '',
    date: '',
    cuttingActual: null as number | null,
    chamferingActual: null as number | null,
    moldingActual: null as number | null,
  },
])

// 在庫取引ログ入力
const showTransactionInputDialog = ref(false)
const submittingTransaction = ref(false)
const transactionInputInfo = ref<{
  date: string
  productCd: string
  productName: string
  processCd: string
  processName: string
} | null>(null)

const transactionForm = reactive({
  // 通常工程フィールド
  actual: null as number | null,
  defect: null as number | null,
  scrap: null as number | null,
  onHold: null as number | null,
  // 倉庫工程フィールド
  inbound: null as number | null,
  outbound: null as number | null,
})

// 繰越編集ダイアログ
const showCarryOverEditDialog = ref(false)
const carryOverEditData = ref<{
  date: string
  productCd: string
  productName: string
  processCd: string
  processName: string
  fieldName: string
  currentValue: number | null
  rowId: number
  transactionId?: number | null
}>({
  date: '',
  productCd: '',
  productName: '',
  processCd: '',
  processName: '',
  fieldName: '',
  currentValue: null,
  rowId: 0,
  transactionId: null,
})
const carryOverEditValue = ref<number | null>(null)
const submittingCarryOverEdit = ref(false)

// 初期在庫管理ダイアログ
const showInitialStockDialog = ref(false)
const loadingInitialStock = ref(false)
const initialStockData = ref<any[]>([])
const initialStockFilter = reactive({
  month: null as string | null,
  keyword: '',
  processCd: '',
})
const initialStockPagination = reactive({
  currentPage: 1,
  pageSize: 150,
  total: 0,
})

// 初期在庫一括登録ダイアログ
const showBatchInitialStockDialog = ref(false)
const loadingBatchInitialStock = ref(false)
const batchInitialStockData = ref<any[]>([])
const batchInitialStockFilter = reactive({
  month: null as string | null,
  processCd: '',
})
const submittingBatchInitialStock = ref(false)
const batchInitialTotals = computed(() => {
  return batchInitialStockData.value.reduce(
    (acc, item) => {
      const input = Number(item.editQuantity ?? 0)
      const existing = Number(item.existing_quantity ?? 0)
      if (!isNaN(input)) acc.input += input
      if (!isNaN(existing)) acc.existing += existing
      return acc
    },
    { input: 0, existing: 0 },
  )
})

// 工程別計画確認印刷
const showPrintDateDialog = ref(false)
const printTargetDate = ref<string>('')

// フィールドタイプ別タブ定義
const tableTabs = [
  {
    key: 'custom',
    label: '受注',
    icon: '📝',
    color: 'linear-gradient(135deg, #8b5cf6, #ec4899)',
  },
  {
    key: 'actual',
    label: '実績',
    icon: '✔️',
    color: 'linear-gradient(135deg, #10b981, #34d399)',
  },
  {
    key: 'inventory',
    label: '在庫',
    icon: '📦',
    color: 'linear-gradient(135deg, #f59e0b, #d97706)',
  },
  {
    key: 'trend',
    label: '推移',
    icon: '📈',
    color: 'linear-gradient(135deg, #9333ea, #c026d3)',
  },
  {
    key: 'actual_plan_trend',
    label: '実計推移',
    icon: '📊',
    color: 'linear-gradient(135deg, #6366f1, #ec4899)',
  },
  {
    key: 'defect',
    label: '不良',
    icon: '❌',
    color: 'linear-gradient(135deg, #f59e0b, #fbbf24)',
  },
  {
    key: 'scrap',
    label: '廃棄',
    icon: '🗑️',
    color: 'linear-gradient(135deg, #ef4444, #f87171)',
  },
  {
    key: 'on_hold',
    label: '保留',
    icon: '⏸️',
    color: 'linear-gradient(135deg, #06b6d4, #22d3ee)',
  },
  {
    key: 'plan',
    label: '計画',
    icon: '📅',
    color: 'linear-gradient(135deg, #14b8a6, #0d9488)',
  },
  {
    key: 'carry_over',
    label: '繰越',
    icon: '🔄',
    color: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
  },
]

const activeTableTab = ref<string>('custom')

// 列定義
const columnDefinitions: Record<
  string,
  { label: string; group: string; type?: string; width?: number }
> = {
  id: { label: 'ID', group: '基本情報' },
  date: { label: '日付', group: '基本情報' },
  day_of_week: { label: '曜日', group: '基本情報' },
  route_cd: { label: '工程グループ', group: '基本情報' },
  product_cd: { label: '製品CD', group: '基本情報' },
  product_name: { label: '製品名', group: '基本情報' },
  order_quantity: { label: '受注数', group: '受注・内示' },
  forecast_quantity: { label: '内示数', group: '受注・内示' },
  // 切断工程
  cutting_carry_over: { label: '切断繰越', group: '切断', width: 70 },
  cutting_actual: { label: '切断実績', group: '切断', width: 70 },
  cutting_defect: { label: '切断不良', group: '切断', width: 70 },
  cutting_scrap: { label: '切断廃棄', group: '切断', width: 70 },
  cutting_on_hold: { label: '切断保留品', group: '切断', width: 80 },
  cutting_inventory: { label: '切断在庫', group: '切断', width: 70 },
  cutting_trend: { label: '切断推移', group: '切断', width: 70 },
  cutting_production_date: { label: '切断生産日', group: '切断', type: 'date', width: 90 },
  cutting_machine: { label: '切断機', group: '切断', type: 'text', width: 80 },
  cutting_plan: { label: '切断計画', group: '切断', width: 70 },
  // 面取工程
  chamfering_carry_over: { label: '面取繰越', group: '面取', width: 70 },
  chamfering_actual: { label: '面取実績', group: '面取', width: 70 },
  chamfering_defect: { label: '面取不良', group: '面取', width: 70 },
  chamfering_scrap: { label: '面取廃棄', group: '面取', width: 70 },
  chamfering_on_hold: { label: '面取保留品', group: '面取', width: 80 },
  chamfering_inventory: { label: '面取在庫', group: '面取', width: 70 },
  chamfering_trend: { label: '面取推移', group: '面取', width: 70 },
  chamfering_production_date: { label: '面取生産日', group: '面取', type: 'date', width: 90 },
  chamfering_machine: { label: '面取機', group: '面取', type: 'text', width: 80 },
  chamfering_plan: { label: '面取計画', group: '面取', width: 70 },
  // SW工程
  sw_carry_over: { label: 'SW繰越', group: 'SW', width: 70 },
  sw_actual: { label: 'SW実績', group: 'SW', width: 70 },
  sw_defect: { label: 'SW不良', group: 'SW', width: 70 },
  sw_scrap: { label: 'SW廃棄', group: 'SW', width: 70 },
  sw_on_hold: { label: 'SW保留品', group: 'SW', width: 80 },
  sw_inventory: { label: 'SW在庫', group: 'SW', width: 70 },
  sw_trend: { label: 'SW推移', group: 'SW', width: 70 },
  sw_production_date: { label: 'SW生産日', group: 'SW', type: 'date', width: 90 },
  sw_machine: { label: 'SW機', group: 'SW', type: 'text', width: 80 },
  sw_plan: { label: 'SW計画', group: 'SW', width: 70 },
  // 成型工程
  molding_carry_over: { label: '成型繰越', group: '成型', width: 70 },
  molding_actual: { label: '成型実績', group: '成型', width: 70 },
  molding_defect: { label: '成型不良', group: '成型', width: 70 },
  molding_scrap: { label: '成型廃棄', group: '成型', width: 70 },
  molding_on_hold: { label: '成型保留品', group: '成型', width: 80 },
  molding_inventory: { label: '成型在庫', group: '成型', width: 70 },
  molding_trend: { label: '成型推移', group: '成型', width: 70 },
  molding_production_date: { label: '成型生産日', group: '成型', type: 'date', width: 90 },
  molding_machine: { label: '成型機', group: '成型', type: 'text', width: 80 },
  molding_plan: { label: '成型計画', group: '成型', width: 70 },
  // メッキ工程
  plating_carry_over: { label: 'メッキ繰越', group: 'メッキ', width: 80 },
  plating_actual: { label: 'メッキ実績', group: 'メッキ', width: 80 },
  plating_defect: { label: 'メッキ不良', group: 'メッキ', width: 80 },
  plating_scrap: { label: 'メッキ廃棄', group: 'メッキ', width: 80 },
  plating_on_hold: { label: 'メッキ保留品', group: 'メッキ', width: 90 },
  plating_inventory: { label: 'メッキ在庫', group: 'メッキ', width: 80 },
  plating_trend: { label: 'メッキ推移', group: 'メッキ', width: 80 },
  plating_production_date: { label: 'メッキ生産日', group: 'メッキ', type: 'date', width: 100 },
  plating_machine: { label: 'メッキ治具', group: 'メッキ', type: 'text', width: 85 },
  plating_plan: { label: 'メッキ計画', group: 'メッキ', width: 80 },
  // 溶接工程
  welding_carry_over: { label: '溶接繰越', group: '溶接', width: 70 },
  welding_actual: { label: '溶接実績', group: '溶接', width: 70 },
  welding_defect: { label: '溶接不良', group: '溶接', width: 70 },
  welding_scrap: { label: '溶接廃棄', group: '溶接', width: 70 },
  welding_on_hold: { label: '溶接保留品', group: '溶接', width: 80 },
  welding_inventory: { label: '溶接在庫', group: '溶接', width: 70 },
  welding_trend: { label: '溶接推移', group: '溶接', width: 70 },
  welding_production_date: { label: '溶接生産日', group: '溶接', type: 'date', width: 90 },
  welding_machine: { label: '溶接機', group: '溶接', type: 'text', width: 80 },
  welding_plan: { label: '溶接計画', group: '溶接', width: 70 },
  welding_actual_plan: { label: '溶接実計', group: '溶接', width: 70 },
  welding_actual_plan_trend: { label: '溶接実計推移', group: '溶接', width: 90 },
  // 検査工程
  inspection_carry_over: { label: '検査繰越', group: '検査', width: 70 },
  inspection_actual: { label: '検査実績', group: '検査', width: 70 },
  inspection_defect: { label: '検査不良', group: '検査', width: 70 },
  inspection_scrap: { label: '検査廃棄', group: '検査', width: 70 },
  inspection_on_hold: { label: '検査保留品', group: '検査', width: 80 },
  inspection_inventory: { label: '検査在庫', group: '検査', width: 70 },
  inspection_trend: { label: '検査推移', group: '検査', width: 70 },
  inspection_production_date: { label: '検査生産日', group: '検査', type: 'date', width: 90 },
  inspector_machine: { label: '検査員', group: '検査', type: 'text', width: 70 },
  inspection_plan: { label: '検査計画', group: '検査', width: 70 },
  inspection_actual_plan: { label: '検査実計', group: '検査', width: 70 },
  inspection_actual_plan_trend: { label: '検査実計推移', group: '検査', width: 90 },
  // 倉庫
  warehouse_carry_over: { label: '倉庫繰越', group: '倉庫', width: 70 },
  warehouse_actual: { label: '倉庫実績', group: '倉庫', width: 70 },
  warehouse_defect: { label: '倉庫不良', group: '倉庫', width: 70 },
  warehouse_scrap: { label: '倉庫廃棄', group: '倉庫', width: 70 },
  warehouse_on_hold: { label: '倉庫保留品', group: '倉庫', width: 80 },
  warehouse_inventory: { label: '倉庫在庫', group: '倉庫', width: 70 },
  warehouse_trend: { label: '倉庫推移', group: '倉庫', width: 70 },
  // 外注倉庫
  outsourced_warehouse_carry_over: { label: '外注倉庫繰越', group: '外注倉庫', width: 100 },
  outsourced_warehouse_actual: { label: '外注倉庫実績', group: '外注倉庫', width: 100 },
  outsourced_warehouse_defect: { label: '外注倉庫不良', group: '外注倉庫', width: 100 },
  outsourced_warehouse_scrap: { label: '外注倉庫廃棄', group: '外注倉庫', width: 100 },
  outsourced_warehouse_on_hold: { label: '外注倉庫保留品', group: '外注倉庫', width: 110 },
  outsourced_warehouse_inventory: { label: '外注倉庫在庫', group: '外注倉庫', width: 100 },
  outsourced_warehouse_trend: { label: '外注倉庫推移', group: '外注倉庫', width: 100 },
  // 外注メッキ
  outsourced_plating_carry_over: { label: '外注メッキ繰越', group: '外注メッキ', width: 110 },
  outsourced_plating_actual: { label: '外注メッキ実績', group: '外注メッキ', width: 110 },
  outsourced_plating_defect: { label: '外注メッキ不良', group: '外注メッキ', width: 110 },
  outsourced_plating_scrap: { label: '外注メッキ廃棄', group: '外注メッキ', width: 110 },
  outsourced_plating_on_hold: { label: '外注メッキ保留品', group: '外注メッキ', width: 120 },
  outsourced_plating_inventory: { label: '外注メッキ在庫', group: '外注メッキ', width: 110 },
  outsourced_plating_trend: { label: '外注メッキ推移', group: '外注メッキ', width: 110 },
  outsourced_plating_plan: { label: '外注メッキ計画', group: '外注メッキ', width: 110 },
  outsourced_plating_actual_plan: { label: '外注メッキ実計', group: '外注メッキ', width: 110 },
  outsourced_plating_actual_plan_trend: {
    label: '外注メッキ実計推移',
    group: '外注メッキ',
    width: 130,
  },
  // 外注溶接
  outsourced_welding_carry_over: { label: '外注溶接繰越', group: '外注溶接', width: 100 },
  outsourced_welding_actual: { label: '外注溶接実績', group: '外注溶接', width: 100 },
  outsourced_welding_defect: { label: '外注溶接不良', group: '外注溶接', width: 100 },
  outsourced_welding_scrap: { label: '外注溶接廃棄', group: '外注溶接', width: 100 },
  outsourced_welding_on_hold: { label: '外注溶接保留品', group: '外注溶接', width: 110 },
  outsourced_welding_inventory: { label: '外注溶接在庫', group: '外注溶接', width: 100 },
  outsourced_welding_trend: { label: '外注溶接推移', group: '外注溶接', width: 100 },
  outsourced_welding_plan: { label: '外注溶接計画', group: '外注溶接', width: 100 },
  outsourced_welding_actual_plan: { label: '外注溶接実計', group: '外注溶接', width: 100 },
  outsourced_welding_actual_plan_trend: {
    label: '外注溶接実計推移',
    group: '外注溶接',
    width: 120,
  },
  // 切断 actual_plan_trend
  cutting_actual_plan: { label: '切断実計', group: '切断', width: 70 },
  cutting_actual_plan_trend: { label: '切断実計推移', group: '切断', width: 90 },
  // 面取 actual_plan_trend
  chamfering_actual_plan: { label: '面取実計', group: '面取', width: 70 },
  chamfering_actual_plan_trend: { label: '面取実計推移', group: '面取', width: 90 },
  // SW actual_plan_trend
  sw_actual_plan: { label: 'SW実計', group: 'SW', width: 70 },
  sw_actual_plan_trend: { label: 'SW実計推移', group: 'SW', width: 90 },
  // 成型 actual_plan_trend
  molding_actual_plan: { label: '成型実計', group: '成型', width: 70 },
  molding_actual_plan_trend: { label: '成型実計推移', group: '成型', width: 90 },
  // メッキ actual_plan_trend
  plating_actual_plan: { label: 'メッキ実計', group: 'メッキ', width: 80 },
  plating_actual_plan_trend: { label: 'メッキ実計推移', group: 'メッキ', width: 100 },
  // 溶接前検査
  pre_welding_inspection_carry_over: { label: '溶接前検査繰越', group: '溶接前検査', width: 110 },
  pre_welding_inspection_actual: { label: '溶接前検査実績', group: '溶接前検査', width: 110 },
  pre_welding_inspection_defect: { label: '溶接前検査不良', group: '溶接前検査', width: 110 },
  pre_welding_inspection_scrap: { label: '溶接前検査廃棄', group: '溶接前検査', width: 110 },
  pre_welding_inspection_on_hold: { label: '溶接前検査保留品', group: '溶接前検査', width: 120 },
  pre_welding_inspection_inventory: { label: '溶接前検査在庫', group: '溶接前検査', width: 110 },
  pre_welding_inspection_trend: { label: '溶接前検査推移', group: '溶接前検査', width: 110 },
  // 外注検査前
  pre_inspection_carry_over: { label: '外注検査前繰越', group: '外注検査前', width: 110 },
  pre_inspection_actual: { label: '外注検査前実績', group: '外注検査前', width: 110 },
  pre_inspection_scrap: { label: '外注検査前廃棄', group: '外注検査前', width: 110 },
  pre_inspection_inventory: { label: '外注検査前在庫', group: '外注検査前', width: 110 },
  pre_inspection_trend: { label: '外注検査前推移', group: '外注検査前', width: 110 },
  // 外注支給前
  pre_outsourcing_carry_over: { label: '外注支給前繰越', group: '外注支給前', width: 110 },
  pre_outsourcing_actual: { label: '外注支給前実績', group: '外注支給前', width: 110 },
  pre_outsourcing_scrap: { label: '外注支給前廃棄', group: '外注支給前', width: 110 },
  pre_outsourcing_inventory: { label: '外注支給前在庫', group: '外注支給前', width: 110 },
  pre_outsourcing_trend: { label: '外注支給前推移', group: '外注支給前', width: 110 },
}

const columnKeys = Object.keys(columnDefinitions)

// デフォルト表示列（受注タブ用：日付、製品CD、製品名、受注数、内示数）
const defaultVisibleColumns: Record<string, boolean> = {
  id: false,
  date: true,
  day_of_week: false,
  route_cd: false,
  product_cd: true,
  product_name: true,
  order_quantity: true,
  forecast_quantity: true,
  // その他はデフォルトで非表示
  ...Object.fromEntries(
    columnKeys
      .filter(
        (k) =>
          ![
            'id',
            'date',
            'day_of_week',
            'route_cd',
            'product_cd',
            'product_name',
            'order_quantity',
            'forecast_quantity',
          ].includes(k),
      )
      .map((k) => [k, false]),
  ),
}

const visibleColumns = ref<Record<string, boolean>>({ ...defaultVisibleColumns })

// フィールドタイプに応じた列の動的計算
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

// 各工程のプレフィックス
const processPrexies = [
  'cutting',
  'chamfering',
  'sw',
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

  // フィールドタイプに応じたラベルのクリーンアップ関数
  const cleanLabel = (originalLabel: string, fieldType: string): string => {
    // フィールドタイプに対応する日本語キーワード
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

    const keywords = fieldTypeKeywords[fieldType]
    if (!keywords) return originalLabel

    let cleanedLabel = originalLabel
    // キーワードを削除（最も長いものから順に）
    keywords
      .sort((a, b) => b.length - a.length)
      .forEach((keyword) => {
        cleanedLabel = cleanedLabel.replace(keyword, '')
      })

    return cleanedLabel.trim()
  }

  // 自由選択モードの場合、visibleColumnsで選択されたすべての列を返す
  if (activeFieldType === 'custom') {
    const cols: Array<{ prop: string; label: string; width?: number; type?: string }> = []

    // 基本列は除外（固定列として表示されるため）
    const baseColumns = [
      'id',
      'date',
      'day_of_week',
      'route_cd',
      'product_cd',
      'product_name',
      'order_quantity',
      'forecast_quantity',
    ]

    // columnKeysの順序で列を取得（順序を保持、SW関連フィールドを除外）
    columnKeys.forEach((key) => {
      // SW関連フィールドを除外
      if (key.startsWith('sw_')) {
        return
      }
      if (visibleColumns.value[key] && !baseColumns.includes(key)) {
        const def = columnDefinitions[key]
        if (def) {
          cols.push({
            prop: key,
            label: def.label,
            width: def.width || (def.type === 'date' ? 100 : def.type === 'text' ? 90 : 80),
            type: def.type,
          })
        }
      }
    })

    return cols
  }

  const suffix = fieldTypeMapping[activeFieldType]
  const cols: Array<{ prop: string; label: string; width?: number; type?: string }> = []

  if (!suffix) return cols

  // 各工程のフィールドタイプに対応する列を取得（SW工程を除外）
  processPrexies.forEach((process) => {
    // SW工程を除外
    if (process === 'sw') {
      return
    }
    const key = `${process}${suffix}`
    const def = columnDefinitions[key]
    if (def) {
      // ラベルからフィールドタイプを削除
      const cleanedLabel = cleanLabel(def.label, activeFieldType)

      cols.push({
        prop: key,
        label: cleanedLabel,
        width: def.width || (def.type === 'date' ? 100 : def.type === 'text' ? 90 : 80),
        type: def.type,
      })
    }
  })

  return cols
})

// 列のグループ化
const groupedColumns = computed(() => {
  const groups: Record<string, Record<string, { label: string; group?: string }>> = {}
  Object.entries(columnDefinitions).forEach(([key, column]) => {
    // SWグループを除外
    if (column.group === 'SW') {
      return
    }
    const groupName = column.group || 'その他'
    if (!groups[groupName]) {
      groups[groupName] = {}
    }
    groups[groupName][key] = column
  })
  return groups
})

const isGroupAllSelected = (groupName: string) => {
  const columns = groupedColumns.value[groupName]
  if (!columns) return false
  return Object.keys(columns).every((key) => visibleColumns.value[key])
}

const isGroupIndeterminate = (groupName: string) => {
  const columns = groupedColumns.value[groupName]
  if (!columns) return false
  const selectedCount = Object.keys(columns).filter((key) => visibleColumns.value[key]).length
  return selectedCount > 0 && selectedCount < Object.keys(columns).length
}

const toggleGroup = (groupName: string, checked: boolean) => {
  const columns = groupedColumns.value[groupName]
  if (!columns) return
  Object.keys(columns).forEach((key) => {
    visibleColumns.value[key] = checked
  })
}

const resetColumnSettings = () => {
  visibleColumns.value = { ...defaultVisibleColumns }
}

const selectAllColumns = () => {
  columnKeys.forEach((key) => {
    visibleColumns.value[key] = true
  })
}

const deselectAllColumns = () => {
  columnKeys.forEach((key) => {
    visibleColumns.value[key] = false
  })
}

const saveColumnSettings = () => {
  try {
    localStorage.setItem('productionSummaryMgmtColumns', JSON.stringify(visibleColumns.value))
    ElMessage.success('列設定を保存しました')
    showColumnSettings.value = false
  } catch {
    ElMessage.error('列設定の保存に失敗しました')
  }
}

// 日付フォーマット
const formatDate = (dateValue: string | Date | null) => {
  if (!dateValue) return '-'
  if (typeof dateValue === 'string') {
    return dateValue.split('T')[0]
  }
  const date = new Date(dateValue)
  return formatDateToString(date)
}

// 曜日タイプ
const getWeekdayType = (dayOfWeek: string) => {
  if (dayOfWeek === '土') return 'primary'
  if (dayOfWeek === '日') return 'danger'
  return 'info'
}

// ヘッダースタイル
const headerCellStyle = {
  background: 'linear-gradient(135deg, #eef2ff, #e0e7ff)',
  color: '#0f172a',
  fontWeight: 700,
  fontSize: '0.65rem',
  padding: '6px 10px',
  borderBottom: '1px solid #c7d2fe',
}

// セルスタイル
const cellStyleHandler = ({
  row,
  column,
}: {
  row: Record<string, any>
  column: { property?: string }
}) => {
  const prop = column?.property
  if (!prop) return {}
  const value = row[prop]
  if (typeof value === 'number') {
    if (value < 0) return { color: '#dc2626', fontWeight: 700 }
    if (value > 0) return { color: '#047857', fontWeight: 700 }
  }
  return {}
}

// 合計計算
const getSummaries = (param: { columns: any[]; data: any[] }) => {
  const { columns, data } = param
  const sums: string[] = []
  const numericFields = new Set([
    'order_quantity',
    'forecast_quantity',
    ...columnKeys.filter(
      (k) =>
        k.endsWith('_carry_over') ||
        k.endsWith('_actual') ||
        k.endsWith('_defect') ||
        k.endsWith('_scrap') ||
        k.endsWith('_on_hold') ||
        k.endsWith('_inventory') ||
        k.endsWith('_trend') ||
        k.endsWith('_plan'),
    ),
  ])

  columns.forEach((column, index) => {
    if (index === 0) {
      sums[index] = '合計'
      return
    }
    const prop = column.property
    if (!prop || !numericFields.has(prop)) {
      sums[index] = ''
      return
    }
    const values = data.map((item) => Number(item[prop]) || 0)
    const sum = values.reduce((prev, curr) => prev + curr, 0)
    sums[index] = sum.toLocaleString()
  })

  return sums
}

// データ取得
const fetchData = async () => {
  loading.value = true
  try {
    const params: any = {
      page: currentPage.value,
      limit: pageSize.value,
    }

    if (dateRange.value && dateRange.value.length === 2) {
      params.startDate = dateRange.value[0]
      params.endDate = dateRange.value[1]
    }

    if (filterProductCd.value) {
      params.productCd = filterProductCd.value
    }
    if (filterKeyword.value.trim()) {
      params.keyword = filterKeyword.value.trim()
    }

    if (sortBy.value) {
      params.sortBy = sortBy.value
      params.sortOrder = sortOrder.value
    }

    const response: any = await getProductionSummarysList(params)
    lastRefreshTime.value = new Date().toLocaleString('ja-JP', { hour12: false })

    if (response?.data?.list) {
      tableData.value = response.data.list
      total.value = response.data.pagination?.total || 0
    } else if (Array.isArray(response)) {
      tableData.value = response
      total.value = response.length
    } else {
      tableData.value = []
      total.value = 0
    }
  } catch (error: any) {
    ElMessage.error('データの取得に失敗しました')
    tableData.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 製品リスト取得
const fetchProductList = async () => {
  try {
    const response: any = await getProductionSummarysProducts()
    const sortByName = (list: Array<{ product_cd: string; product_name?: string }>) =>
      [...list].sort((a, b) => {
        const nameA = (a.product_name || '').trim()
        const nameB = (b.product_name || '').trim()
        if (nameA && nameB) return nameA.localeCompare(nameB)
        if (!nameA && nameB) return 1
        if (nameA && !nameB) return -1
        return (a.product_cd || '').localeCompare(b.product_cd || '')
      })

    if (response?.data) {
      productList.value = sortByName(response.data)
    } else if (Array.isArray(response)) {
      productList.value = sortByName(response)
    }
  } catch (error: any) {
    console.error('製品リストの取得に失敗しました:', error)
  }
}

// イベントハンドラー
const handleFilterChange = () => {
  currentPage.value = 1
  fetchData()
}

const handleKeywordInput = () => {
  if (keywordFilterTimer) {
    clearTimeout(keywordFilterTimer)
  }
  keywordFilterTimer = setTimeout(() => {
    handleFilterChange()
  }, 400)
}

const handleKeywordClear = () => {
  if (keywordFilterTimer) {
    clearTimeout(keywordFilterTimer)
    keywordFilterTimer = null
  }
  handleFilterChange()
}

const handleResetFilter = () => {
  dateRange.value = createDefaultDateRange()
  filterProductCd.value = ''
  filterKeyword.value = ''
  sortBy.value = 'product_name'
  sortOrder.value = 'ASC'
  currentPage.value = 1
  fetchData()
}

const shiftDateRange = (offset: number) => {
  const currentRange =
    dateRange.value && dateRange.value.length === 2 ? dateRange.value : createDefaultDateRange()
  const [startStr, endStr] = currentRange
  const startDate = parseDateString(startStr)
  const endDate = parseDateString(endStr)
  startDate.setDate(startDate.getDate() + offset)
  endDate.setDate(endDate.getDate() + offset)
  dateRange.value = [formatDateToString(startDate), formatDateToString(endDate)]
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

// 繰越データ更新ハンドラー
const handleCarryOverEditSubmit = async () => {
  if (submittingCarryOverEdit.value) return

  try {
    submittingCarryOverEdit.value = true

    const { date, productCd, processCd, transactionId } = carryOverEditData.value
    const processCdValue = processFieldToProcessCd[processCd] || ''

    if (!productCd || !processCdValue) {
      throw new Error('製品CDまたは工程CDが不足しています')
    }

    // stock_transaction_logsに保存または更新
    try {
      console.log('繰越データ更新開始:', {
        transactionId,
        hasTransactionId: !!transactionId,
        transactionIdType: typeof transactionId,
        productCd,
        processCdValue,
        quantity: carryOverEditValue.value,
        date,
        carryOverEditData: carryOverEditData.value,
      })

      // transactionId が存在し、有効な数値であることを確認
      const hasValidTransactionId =
        transactionId && transactionId !== null && transactionId !== undefined

      if (hasValidTransactionId) {
        // 既存データを更新（inventory APIを使用）
        console.log('stock_transaction_logsを更新します（既存データ）:', {
          transactionId,
          productCd,
          processCdValue,
          quantity: carryOverEditValue.value,
          date,
        })

        const updateResponse = await request.put(
          `/api/inventory/carryover-history/${transactionId}`,
          {
            stock_type: processCdValue === 'KT13' || processCdValue === 'KT15' ? '製品' : '仕掛品',
            target_cd: productCd,
            process_cd: processCdValue,
            quantity: carryOverEditValue.value || 0,
            transaction_time: `${date} 00:00:00`,
            location_cd:
              processCdValue === 'KT13'
                ? '製品倉庫'
                : processCdValue === 'KT15'
                  ? '外注倉庫'
                  : '工程中間在庫',
            unit: '本',
          },
        )

        if (!updateResponse?.success) {
          console.error('stock_transaction_logs更新失敗:', updateResponse)
          throw new Error(updateResponse?.message || 'stock_transaction_logsの更新に失敗しました')
        }

        console.log('stock_transaction_logs更新成功（既存データを更新）:', {
          transactionId,
          response: updateResponse,
        })
      } else {
        // 新規作成
        console.log('stock_transaction_logsを新規作成します（transactionIdなし）:', {
          productCd,
          processCdValue,
          quantity: carryOverEditValue.value,
          date,
        })

        const createResponse = await request.post('/api/stock/transaction', {
          target_cd: productCd,
          process_cd: processCdValue,
          transaction_type: '初期',
          quantity: carryOverEditValue.value || 0,
          transaction_time: `${date} 00:00:00`,
          stock_type: processCdValue === 'KT13' || processCdValue === 'KT15' ? '製品' : '仕掛品',
          location_cd:
            processCdValue === 'KT13'
              ? '製品倉庫'
              : processCdValue === 'KT15'
                ? '外注倉庫'
                : '工程中間在庫',
          unit: '本',
        })

        if (!createResponse?.success) {
          console.error('stock_transaction_logs作成失敗:', createResponse)
          throw new Error(createResponse?.message || 'stock_transaction_logsの作成に失敗しました')
        }

        console.log('stock_transaction_logs作成成功（新規データを作成）:', {
          response: createResponse,
        })
      }
    } catch (stockError: any) {
      console.error('stock_transaction_logs更新/作成エラー:', stockError)
      throw new Error(
        `stock_transaction_logsの更新に失敗しました: ${stockError?.response?.data?.message || stockError.message}`,
      )
    }

    // production_summarysテーブルも更新
    // 字段名を検証（SQLインジェクション防止）
    const allowedCarryOverFields = [
      'cutting_carry_over',
      'chamfering_carry_over',
      'molding_carry_over',
      'plating_carry_over',
      'welding_carry_over',
      'inspection_carry_over',
      'warehouse_carry_over',
      'outsourced_plating_carry_over',
      'outsourced_welding_carry_over',
      'pre_welding_inspection_carry_over',
      'pre_inspection_carry_over',
      'pre_outsourcing_carry_over',
    ]

    if (!allowedCarryOverFields.includes(carryOverEditData.value.fieldName)) {
      throw new Error(`無効なフィールド名: ${carryOverEditData.value.fieldName}`)
    }

    console.log('production_summarysを更新します:', {
      product_cd: carryOverEditData.value.productCd,
      date: carryOverEditData.value.date,
      field_name: carryOverEditData.value.fieldName,
      field_value: carryOverEditValue.value,
    })

    // 直接SQL更新を実行（カスタムエンドポイントを使用）
    const updateResponse = await request.post(
      '/api/database/production-summarys/update-single-field',
      {
        product_cd: carryOverEditData.value.productCd,
        date: carryOverEditData.value.date,
        field_name: carryOverEditData.value.fieldName,
        field_value: carryOverEditValue.value || 0,
      },
    )

    console.log('production_summarys更新成功:', updateResponse)

    ElMessage.success(
      '繰越データを更新しました（stock_transaction_logsとproduction_summarys両方を更新）',
    )
    showCarryOverEditDialog.value = false

    // データを再取得
    await fetchData()
  } catch (error: any) {
    console.error('繰越データ更新エラー:', error)
    const errorMessage =
      error?.response?.data?.message || error?.message || '繰越データの更新に失敗しました'
    ElMessage.error(errorMessage)
    // エラーが発生した場合、stock_transaction_logsとproduction_summarysの整合性が取れない可能性があるため、
    // ユーザーに確認を促す
    if (errorMessage.includes('stock_transaction_logs')) {
      console.warn(
        '警告: stock_transaction_logsの更新に失敗しましたが、production_summarysは更新されている可能性があります',
      )
    }
  } finally {
    submittingCarryOverEdit.value = false
  }
}

const handlePageSizeChange = () => {
  currentPage.value = 1
  fetchData()
}

const handlePageChange = () => {
  fetchData()
}

const handleRefresh = () => {
  fetchData()
}

// 获取所有筛选后的数据（用于打印）
const fetchAllFilteredData = async (): Promise<any[]> => {
  try {
    const params: any = {
      page: 1,
      limit: 10000, // 全データを取得
    }

    if (dateRange.value && dateRange.value.length === 2) {
      params.startDate = dateRange.value[0]
      params.endDate = dateRange.value[1]
    }

    if (filterProductCd.value) {
      params.productCd = filterProductCd.value
    }
    if (filterKeyword.value.trim()) {
      params.keyword = filterKeyword.value.trim()
    }

    if (sortBy.value) {
      params.sortBy = sortBy.value
      params.sortOrder = sortOrder.value
    }

    const response: any = await getProductionSummarysList(params)

    if (response?.data?.list) {
      return response.data.list
    } else if (Array.isArray(response)) {
      return response
    } else {
      return []
    }
  } catch (error: any) {
    console.error('データ取得エラー:', error)
    ElMessage.error('データの取得に失敗しました')
    return []
  }
}

// 格式化打印单元格值
const formatPrintCellValue = (value: unknown, colType?: string) => {
  if (value === null || value === undefined || value === '') return '-'
  if (colType === 'date' && typeof value === 'string') {
    return formatDate(value)
  }
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value.toLocaleString()
  }
  if (typeof value === 'string') {
    return value
  }
  return String(value)
}

// 印刷用HTMLを構築
const buildTablePrintHtml = (printData: any[]) => {
  const now = new Date().toLocaleString('ja-JP', { hour12: false })
  const filters: string[] = []
  if (dateRange.value && dateRange.value.length === 2) {
    filters.push(`期間: ${dateRange.value[0]} ～ ${dateRange.value[1]}`)
  }
  if (filterProductCd.value) {
    const product = productList.value.find((item) => item.product_cd === filterProductCd.value)
    filters.push(
      `製品: ${product ? `${product.product_cd} ${product.product_name || ''}` : filterProductCd.value}`,
    )
  }
  if (filterKeyword.value) {
    filters.push(`キーワード: ${filterKeyword.value}`)
  }

  // 获取当前显示的列
  const columns = dynamicColumns.value
    .filter((col) => visibleColumns.value[col.prop])
    .map((col) => ({
      prop: col.prop,
      label: col.label,
      type: col.type,
    }))

  // 基本列
  const baseColumns = [
    { prop: 'date', label: '日付', type: 'date' },
    { prop: 'product_cd', label: '製品CD', type: 'text' },
    { prop: 'product_name', label: '製品名', type: 'text' },
  ]

  // 合并基本列和动态列
  const allColumns = [...baseColumns.filter((col) => visibleColumns.value[col.prop]), ...columns]

  const headerCells = allColumns.map((col) => `<th>${col.label}</th>`).join('')
  const bodyRows = printData
    .map((row) => {
      const cells = allColumns
        .map((col) => {
          const value = row[col.prop as keyof typeof row]
          const formattedValue = formatPrintCellValue(value, col.type)
          return `<td>${formattedValue}</td>`
        })
        .join('')
      return `<tr>${cells}</tr>`
    })
    .join('')

  return `
    <!DOCTYPE html>
    <html lang="ja">
      <head>
        <meta charset="UTF-8" />
        <title>工程別計画作成管理 - 表示内容</title>
        <style>
          @page { size: A4 landscape; margin: 12mm; }
          body { font-family: 'Segoe UI','Hiragino Sans','Noto Sans JP',sans-serif; margin: 0; padding: 24px; color: #0f172a; background: #fff; }
          h1 { margin: 0 0 4px; font-size: 22px; font-weight: 700; }
          .print-meta { font-size: 12px; color: #475569; margin-bottom: 18px; line-height: 1.6; }
          table { width: 100%; border-collapse: collapse; font-size: 11px; }
          th, td { border: 1px solid #e2e8f0; padding: 6px 8px; text-align: center; }
          th { background: #eef2ff; font-weight: 600; color: #1e293b; }
          tr:nth-child(even) { background: #f8fafc; }
          tr:hover { background: #f1f5f9; }
          @media print {
            body { padding: 0; }
            table { font-size: 10px; }
            th, td { padding: 4px 6px; }
          }
        </style>
      </head>
      <body>
        <h1>工程別計画作成管理 - 表示内容</h1>
        <div class="print-meta">
          出力時間: ${now}<br/>
          フィルター: ${filters.length ? filters.join(' / ') : '全件'}<br/>
          データ件数: ${printData.length}件
        </div>
        <table>
          <thead><tr>${headerCells}</tr></thead>
          <tbody>${bodyRows}</tbody>
        </table>
      </body>
    </html>
  `
}

const handlePrint = async () => {
  if (!tableData.value.length) {
    ElMessage.warning('印刷できるデータがありません')
    return
  }

  try {
    // ローディングメッセージを表示
    const loadingMessage = ElMessage({
      message: 'データを取得中...',
      type: 'info',
      duration: 0,
    })

    // 全フィルタ後のデータを取得
    const allData = await fetchAllFilteredData()

    loadingMessage.close()

    if (!allData.length) {
      ElMessage.warning('印刷できるデータがありません')
      return
    }

    // 印刷用HTMLを構築
    const html = buildTablePrintHtml(allData)

    // 新しいウィンドウを開く
    const printWindow = window.open('', '_blank')
    if (!printWindow) {
      ElMessage.error('ポップアップがブロックされました。ブラウザ設定を確認してください。')
      return
    }

    const doc = printWindow.document
    doc.open()
    doc.write(html)
    doc.close()

    // コンテンツの読み込み完了後に印刷
    const handlePrint = () => {
      printWindow.focus()
      const printPromise = new Promise<void>((resolve) => {
        const listener = () => {
          printWindow.removeEventListener('afterprint', listener)
          resolve()
        }
        printWindow.addEventListener('afterprint', listener)
      })

      printWindow.print()
      printPromise
        .then(() => {
          setTimeout(() => {
            try {
              printWindow.close()
            } catch (err) {
              console.warn('印刷ウィンドウのクローズに失敗:', err)
            }
          }, 300)
        })
        .catch(() => {
          setTimeout(() => {
            try {
              printWindow.close()
            } catch (err) {
              console.warn('印刷ウィンドウのクローズに失敗:', err)
            }
          }, 300)
        })
    }

    if (printWindow.document.readyState === 'complete') {
      handlePrint()
    } else {
      printWindow.addEventListener('load', handlePrint)
    }
  } catch (error: any) {
    console.error('印刷エラー:', error)
    ElMessage.error('印刷に失敗しました')
  }
}

// データ生成
const handleGenerateData = async () => {
  try {
    // 日付範囲を計算：当月月初から4ヶ月後月末まで（日本時区）
    const jstInfo = getCurrentJSTInfo()
    const year = jstInfo.year
    const month = jstInfo.month

    // 当月月初
    const startDateStr = getJSTDateString(year, month, 1)
    // 4ヶ月後月末（翌月の0日 = 前月の最終日）
    const endYear = month + 4 >= 12 ? year + Math.floor((month + 4) / 12) : year
    const endMonth = (month + 4) % 12
    const endDate = new Date(endYear, endMonth + 1, 0) // 月末日を取得
    const endDateStr = getJSTDateString(
      endDate.getFullYear(),
      endDate.getMonth(),
      endDate.getDate(),
    )

    // 日付範囲を設定して確認ダイアログを表示
    generateDateRange.value = {
      start: startDateStr,
      end: endDateStr,
    }
    showGenerateConfirmDialog.value = true
  } catch (error: any) {
    console.error('データ生成準備時にエラーが発生:', error)
    ElMessage.error('データ生成準備に失敗しました')
  }
}

// データ生成を確認
const confirmGenerateData = async () => {
  showGenerateConfirmDialog.value = false

  const startDateStr = generateDateRange.value.start
  const endDateStr = generateDateRange.value.end

  try {
    // 進捗を初期化
    generating.value = true
    showProgressDialog.value = true
    progressPercentage.value = 0
    progressStatus.value = ''
    progressText.value = '製品情報を取得中...'
    progressInfo.value = {
      current: 0,
      total: 0,
      products: 0,
      dates: 0,
      processedProducts: 0,
      processedDates: 0,
      inserted: 0,
      skipped: 0,
      currentProduct: '',
      currentDate: '',
    }

    // 日付数を計算
    const startDateObj = new Date(startDateStr)
    const endDateObj = new Date(endDateStr)
    let dateCount = 0
    const tempDate = new Date(startDateObj)
    while (tempDate <= endDateObj) {
      dateCount++
      tempDate.setDate(tempDate.getDate() + 1)
    }

    // まず製品数を取得（進捗計算用）
    try {
      progressText.value = '製品情報を取得中...'
      progressPercentage.value = 5

      // APIを呼び出して製品情報を取得（生成APIの応答を通じて）
      const generatePromise = generateProductionSummarys({
        startDate: startDateStr,
        endDate: endDateStr,
      })

      // 進捗更新をシミュレート（既知の日付と製品数に基づく）
      const estimatedProducts = 50 // 初期推定値
      const totalItems = dateCount * estimatedProducts
      let processedItems = 0

      const progressInterval = setInterval(() => {
        if (progressPercentage.value < 95) {
          // 根据时间估算进度（假设每100ms处理1个产品）
          processedItems += Math.floor(Math.random() * 3) + 1
          if (processedItems > totalItems * 0.95) {
            processedItems = Math.floor(totalItems * 0.95)
          }
          progressPercentage.value = Math.min(5 + (processedItems / totalItems) * 90, 95)

          // 更新详细信息
          const estimatedProcessedProducts = Math.floor(processedItems / dateCount)
          const estimatedProcessedDates = Math.floor(processedItems / estimatedProducts)

          progressInfo.value.processedProducts = estimatedProcessedProducts
          progressInfo.value.processedDates = estimatedProcessedDates
          progressInfo.value.products = estimatedProducts
          progressInfo.value.dates = dateCount

          progressText.value = `データを生成中... (${estimatedProcessedProducts}/${estimatedProducts} 製品)`
        }
      }, 200)

      // 等待API完成
      const response: any = await generatePromise

      // 从响应中获取实际数据
      if (response?.data) {
        const data = response.data
        progressInfo.value.products = data.products || estimatedProducts
        progressInfo.value.dates = data.dates || dateCount
        progressInfo.value.inserted = data.generated || 0
        progressInfo.value.skipped = data.skipped || 0
        progressInfo.value.processedProducts = data.products || estimatedProducts
        progressInfo.value.processedDates = data.dates || dateCount
      }

      // 完成进度
      clearInterval(progressInterval)
      progressPercentage.value = 100
      progressStatus.value = 'success'
      progressText.value = 'データ生成が完了しました！'
      progressInfo.value.currentProduct = ''
      progressInfo.value.currentDate = ''

      // 進捗ダイアログを遅延クローズ
      setTimeout(() => {
        showProgressDialog.value = false
        ElMessage.success('production_summarysデータの生成が成功しました！')
        fetchData()
      }, 1500)
    } catch (error: any) {
      progressPercentage.value = 100
      progressStatus.value = 'exception'
      progressText.value = 'データ生成に失敗しました'

      setTimeout(() => {
        showProgressDialog.value = false
        ElMessage.error(error?.response?.data?.message || 'データ生成に失敗しました')
      }, 2000)
    } finally {
      generating.value = false
    }
  } catch (error: any) {
    console.error('データ生成時にエラーが発生:', error)
    showProgressDialog.value = false
    ElMessage.error(error?.response?.data?.message || 'データ生成に失敗しました')
    generating.value = false
  }
}

// 繰越データ更新
const handleUpdateCarryOver = async () => {
  try {
    const confirmed = await ElMessageBox.confirm(`繰越データを更新します。`, '繰越データ更新確認', {
      confirmButtonText: '更新',
      cancelButtonText: 'キャンセル',
      type: 'info',
    }).catch(() => false)

    if (!confirmed) return

    updatingCarryOver.value = true
    showProgressDialog.value = true
    progressPercentage.value = 0
    progressStatus.value = ''
    progressText.value = '繰越フィールドをクリア中...'

    // まず全繰越フィールドをクリア
    progressPercentage.value = 10
    try {
      await clearProductionSummarysCarryOver()
      console.log('繰越フィールドをクリアしました')
    } catch (error: any) {
      console.warn('繰越フィールドのクリアでエラーが発生しましたが、続行します:', error)
      // クリア失敗は後続の更新に影響せず、続行
    }

    progressText.value = '繰越データを取得中...'
    progressPercentage.value = 40
    progressInfo.value = {
      current: 0,
      total: 0,
      products: 0,
      dates: 0,
      processedProducts: 0,
      processedDates: 0,
      inserted: 0,
      skipped: 0,
      currentProduct: '',
      currentDate: '',
    }

    // 進捗をシミュレート
    const progressInterval = setInterval(() => {
      if (progressPercentage.value < 90) {
        progressPercentage.value += Math.random() * 15
        if (progressPercentage.value > 90) {
          progressPercentage.value = 90
        }
        progressText.value = '繰越データを更新中...'
      }
    }, 300)

    try {
      const response: any = await updateProductionSummarysCarryOver()

      clearInterval(progressInterval)
      progressPercentage.value = 100
      progressStatus.value = 'success'
      progressText.value = '繰越データ更新が完了しました！'

      // 応答からデータを取得
      let updatedCount = 0
      let skippedCount = 0

      if (response?.data) {
        updatedCount = response.data.updated || 0
        skippedCount = response.data.skipped || 0
      }

      progressInfo.value.inserted = updatedCount
      progressInfo.value.skipped = skippedCount

      let successMessage = `繰越データの更新が成功しました！\n更新: ${updatedCount}件`
      if (skippedCount > 0) {
        successMessage += `\nスキップ: ${skippedCount}件`
      }

      setTimeout(() => {
        showProgressDialog.value = false
        ElMessage.success(successMessage)
        // データを遅延リフレッシュ
        setTimeout(() => {
          fetchData().catch((err) => {
            console.warn('データ更新後のリフレッシュに失敗:', err)
          })
        }, 500)
      }, 1500)
    } catch (error: any) {
      clearInterval(progressInterval)
      progressPercentage.value = 100
      progressStatus.value = 'exception'
      progressText.value = '繰越データ更新に失敗しました'

      setTimeout(() => {
        showProgressDialog.value = false
        ElMessage.error(error?.response?.data?.message || '繰越データ更新に失敗しました')
      }, 2000)
    } finally {
      updatingCarryOver.value = false
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('繰越データ更新時にエラーが発生:', error)
      showProgressDialog.value = false
      ElMessage.error(error?.response?.data?.message || '繰越データ更新に失敗しました')
    }
    updatingCarryOver.value = false
  }
}

// 受注データ更新
const handleUpdateFromOrderDaily = async () => {
  try {
    // 显示更新模式选择对话框
    showUpdateModeDialog.value = true
  } catch (error: any) {
    console.error('更新モード選択時にエラーが発生:', error)
  }
}

const confirmUpdateMode = async () => {
  showUpdateModeDialog.value = false

  const updateModeText =
    updateMode.value === 'changed'
      ? '変更されたデータのみ更新'
      : updateMode.value === 'all'
        ? 'すべてのデータを強制更新'
        : `最近${updateDays.value}日間のデータを更新`

  try {
    const confirmed = await ElMessageBox.confirm(`受注データを更新します。`, '受注データ更新確認', {
      confirmButtonText: '更新',
      cancelButtonText: 'キャンセル',
      type: 'info',
    }).catch(() => false)

    if (!confirmed) return

    updatingOrder.value = true
    showProgressDialog.value = true
    progressPercentage.value = 0
    progressStatus.value = ''
    progressText.value = '受注データを取得中...'

    // 模拟进度
    const progressInterval = setInterval(() => {
      if (progressPercentage.value < 90) {
        progressPercentage.value += Math.random() * 10
        if (progressPercentage.value > 90) {
          progressPercentage.value = 90
        }
        progressText.value = '受注データを更新中...'
      }
    }, 300)

    try {
      const response: any = await updateProductionSummarysFromOrderDaily({
        updateMode: updateMode.value,
        days: updateDays.value,
        clearBeforeUpdate: false,
      })

      clearInterval(progressInterval)
      progressPercentage.value = 100
      progressStatus.value = 'success'
      progressText.value = '受注データ更新が完了しました！'

      // 从响应中获取数据
      let updatedCount = 0
      let skippedCount = 0
      let unchangedCount = 0

      if (response?.data) {
        updatedCount = response.data.updated || 0
        skippedCount = response.data.skipped || 0
        unchangedCount = response.data.unchanged || 0
      }

      progressInfo.value.inserted = updatedCount
      progressInfo.value.skipped = skippedCount

      let successMessage = `受注データの更新が成功しました！\n更新: ${updatedCount}件`
      if (unchangedCount > 0) {
        successMessage += `\n変更なし: ${unchangedCount}件`
      }
      if (skippedCount > 0) {
        successMessage += `\nスキップ: ${skippedCount}件`
      }

      setTimeout(() => {
        showProgressDialog.value = false
        ElMessage.success(successMessage)
        // データを遅延リフレッシュ
        setTimeout(() => {
          fetchData().catch((err) => {
            console.warn('データ更新後のリフレッシュに失敗:', err)
          })
        }, 500)
      }, 1500)
    } catch (error: any) {
      clearInterval(progressInterval)
      progressPercentage.value = 100
      progressStatus.value = 'exception'
      progressText.value = '受注データ更新に失敗しました'

      setTimeout(() => {
        showProgressDialog.value = false
        ElMessage.error(error?.response?.data?.message || '受注データ更新に失敗しました')
      }, 2000)
    } finally {
      updatingOrder.value = false
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('受注データ更新時にエラーが発生:', error)
      showProgressDialog.value = false
      ElMessage.error(error?.response?.data?.message || '受注データ更新に失敗しました')
    }
    updatingOrder.value = false
  }
}

// 実績データ更新
const handleUpdateActual = async () => {
  try {
    const confirmed = await ElMessageBox.confirm(`実績データを更新します。`, '実績データ更新確認', {
      confirmButtonText: '更新',
      cancelButtonText: 'キャンセル',
      type: 'info',
    }).catch(() => false)

    if (!confirmed) return

    updatingActual.value = true
    showProgressDialog.value = true
    progressPercentage.value = 0
    progressStatus.value = ''
    progressText.value = '実績データを取得中...'

    progressInfo.value = {
      current: 0,
      total: 0,
      products: 0,
      dates: 0,
      processedProducts: 0,
      processedDates: 0,
      inserted: 0,
      skipped: 0,
      currentProduct: '',
      currentDate: '',
    }

    // 模拟进度
    const progressInterval = setInterval(() => {
      if (progressPercentage.value < 90) {
        progressPercentage.value += Math.random() * 10
        if (progressPercentage.value > 90) {
          progressPercentage.value = 90
        }
        progressText.value = '実績データを更新中...'
      }
    }, 300)

    try {
      const response: any = await updateProductionSummarysActual()

      clearInterval(progressInterval)
      progressPercentage.value = 100
      progressStatus.value = 'success'
      progressText.value = '実績データ更新が完了しました！'

      // 从响应中获取数据
      // 注意：request拦截器对于production-summarys API会返回res.data，所以response已经是data部分
      let updatedCount = 0
      let skippedCount = 0
      let clearedCount = 0

      // 兼容两种响应格式：直接数据对象或包含data字段的对象
      const responseData = response?.data || response
      if (responseData) {
        updatedCount = responseData.updated || 0
        skippedCount = responseData.skipped || 0
        clearedCount = responseData.cleared || 0
      }

      progressInfo.value.inserted = updatedCount
      progressInfo.value.skipped = skippedCount

      let successMessage = `実績データの更新が成功しました！\n更新: ${updatedCount}件`
      if (clearedCount > 0) {
        successMessage += `\nクリア: ${clearedCount}件（当月開始）`
      }
      if (skippedCount > 0) {
        successMessage += `\nスキップ: ${skippedCount}件`
      }

      setTimeout(() => {
        showProgressDialog.value = false
        ElMessage.success(successMessage)
        // データを遅延リフレッシュ
        setTimeout(() => {
          fetchData().catch((err) => {
            console.warn('データ更新後のリフレッシュに失敗:', err)
          })
        }, 500)
      }, 1500)
    } catch (error: any) {
      clearInterval(progressInterval)
      progressPercentage.value = 100
      progressStatus.value = 'exception'
      progressText.value = '実績データ更新に失敗しました'

      setTimeout(() => {
        showProgressDialog.value = false
        ElMessage.error(error?.response?.data?.message || '実績データ更新に失敗しました')
      }, 2000)
    } finally {
      updatingActual.value = false
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('実績データ更新時にエラーが発生:', error)
      showProgressDialog.value = false
      ElMessage.error(error?.response?.data?.message || '実績データ更新に失敗しました')
    }
    updatingActual.value = false
  }
}

// 不良データ更新
const handleUpdateDefect = async () => {
  try {
    const confirmed = await ElMessageBox.confirm(`不良データを更新します。`, '不良データ更新確認', {
      confirmButtonText: '更新',
      cancelButtonText: 'キャンセル',
      type: 'warning',
    }).catch(() => false)

    if (!confirmed) return

    updatingDefect.value = true
    showProgressDialog.value = true
    progressPercentage.value = 0
    progressStatus.value = ''
    progressText.value = '不良データを取得中...'

    progressInfo.value = {
      current: 0,
      total: 0,
      products: 0,
      dates: 0,
      processedProducts: 0,
      processedDates: 0,
      inserted: 0,
      skipped: 0,
      currentProduct: '',
      currentDate: '',
    }

    // 模拟进度
    const progressInterval = setInterval(() => {
      if (progressPercentage.value < 90) {
        progressPercentage.value += Math.random() * 10
        if (progressPercentage.value > 90) {
          progressPercentage.value = 90
        }
        progressText.value = '不良データを更新中...'
      }
    }, 300)

    try {
      const response: any = await updateProductionSummarysDefect()

      clearInterval(progressInterval)
      progressPercentage.value = 100
      progressStatus.value = 'success'
      progressText.value = '不良データ更新が完了しました！'

      // 从响应中获取数据
      let updatedCount = 0
      let skippedCount = 0

      if (response?.data) {
        updatedCount = response.data.updated || 0
        skippedCount = response.data.skipped || 0
      }

      progressInfo.value.inserted = updatedCount
      progressInfo.value.skipped = skippedCount

      let successMessage = `不良データの更新が成功しました！\n更新: ${updatedCount}件`
      if (skippedCount > 0) {
        successMessage += `\nスキップ: ${skippedCount}件`
      }

      setTimeout(() => {
        showProgressDialog.value = false
        ElMessage.success(successMessage)
        // データを遅延リフレッシュ
        setTimeout(() => {
          fetchData().catch((err) => {
            console.warn('データ更新後のリフレッシュに失敗:', err)
          })
        }, 500)
      }, 1500)
    } catch (error: any) {
      clearInterval(progressInterval)
      progressPercentage.value = 100
      progressStatus.value = 'exception'
      progressText.value = '不良データ更新に失敗しました'

      setTimeout(() => {
        showProgressDialog.value = false
        ElMessage.error(error?.response?.data?.message || '不良データ更新に失敗しました')
      }, 2000)
    } finally {
      updatingDefect.value = false
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('不良データ更新時にエラーが発生:', error)
      showProgressDialog.value = false
      ElMessage.error(error?.response?.data?.message || '不良データ更新に失敗しました')
    }
    updatingDefect.value = false
  }
}

// 廃棄データ更新
const handleUpdateScrap = async () => {
  try {
    const confirmed = await ElMessageBox.confirm(`廃棄データを更新します。`, '廃棄データ更新確認', {
      confirmButtonText: '更新',
      cancelButtonText: 'キャンセル',
      type: 'warning',
    }).catch(() => false)

    if (!confirmed) return

    updatingScrap.value = true
    showProgressDialog.value = true
    progressPercentage.value = 0
    progressStatus.value = ''
    progressText.value = '廃棄データを取得中...'

    progressInfo.value = {
      current: 0,
      total: 0,
      products: 0,
      dates: 0,
      processedProducts: 0,
      processedDates: 0,
      inserted: 0,
      skipped: 0,
      currentProduct: '',
      currentDate: '',
    }

    // 模拟进度
    const progressInterval = setInterval(() => {
      if (progressPercentage.value < 90) {
        progressPercentage.value += Math.random() * 10
        if (progressPercentage.value > 90) {
          progressPercentage.value = 90
        }
        progressText.value = '廃棄データを更新中...'
      }
    }, 300)

    try {
      const response: any = await updateProductionSummarysScrap()

      clearInterval(progressInterval)
      progressPercentage.value = 100
      progressStatus.value = 'success'
      progressText.value = '廃棄データ更新が完了しました！'

      // 从响应中获取数据
      let updatedCount = 0
      let skippedCount = 0

      if (response?.data) {
        updatedCount = response.data.updated || 0
        skippedCount = response.data.skipped || 0
      }

      progressInfo.value.inserted = updatedCount
      progressInfo.value.skipped = skippedCount

      let successMessage = `廃棄データの更新が成功しました！\n更新: ${updatedCount}件`
      if (skippedCount > 0) {
        successMessage += `\nスキップ: ${skippedCount}件`
      }

      setTimeout(() => {
        showProgressDialog.value = false
        ElMessage.success(successMessage)
        // データを遅延リフレッシュ
        setTimeout(() => {
          fetchData().catch((err) => {
            console.warn('データ更新後のリフレッシュに失敗:', err)
          })
        }, 500)
      }, 1500)
    } catch (error: any) {
      clearInterval(progressInterval)
      progressPercentage.value = 100
      progressStatus.value = 'exception'
      progressText.value = '廃棄データ更新に失敗しました'

      setTimeout(() => {
        showProgressDialog.value = false
        ElMessage.error(error?.response?.data?.message || '廃棄データ更新に失敗しました')
      }, 2000)
    } finally {
      updatingScrap.value = false
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('廃棄データ更新時にエラーが発生:', error)
      showProgressDialog.value = false
      ElMessage.error(error?.response?.data?.message || '廃棄データ更新に失敗しました')
    }
    updatingScrap.value = false
  }
}

// 保留データ更新
const handleUpdateOnHold = async () => {
  try {
    const confirmed = await ElMessageBox.confirm(`保留データを更新します。`, '保留データ更新確認', {
      confirmButtonText: '更新',
      cancelButtonText: 'キャンセル',
      type: 'info',
    }).catch(() => false)

    if (!confirmed) return

    updatingOnHold.value = true
    showProgressDialog.value = true
    progressPercentage.value = 0
    progressStatus.value = ''
    progressText.value = '保留データを取得中...'

    progressInfo.value = {
      current: 0,
      total: 0,
      products: 0,
      dates: 0,
      processedProducts: 0,
      processedDates: 0,
      inserted: 0,
      skipped: 0,
      currentProduct: '',
      currentDate: '',
    }

    // 模拟进度
    const progressInterval = setInterval(() => {
      if (progressPercentage.value < 90) {
        progressPercentage.value += Math.random() * 10
        if (progressPercentage.value > 90) {
          progressPercentage.value = 90
        }
        progressText.value = '保留データを更新中...'
      }
    }, 300)

    try {
      const response: any = await updateProductionSummarysOnHold()

      clearInterval(progressInterval)
      progressPercentage.value = 100
      progressStatus.value = 'success'
      progressText.value = '保留データ更新が完了しました！'

      // 从响应中获取数据
      let updatedCount = 0
      let skippedCount = 0

      if (response?.data) {
        updatedCount = response.data.updated || 0
        skippedCount = response.data.skipped || 0
      }

      progressInfo.value.inserted = updatedCount
      progressInfo.value.skipped = skippedCount

      let successMessage = `保留データの更新が成功しました！\n更新: ${updatedCount}件`
      if (skippedCount > 0) {
        successMessage += `\nスキップ: ${skippedCount}件`
      }

      setTimeout(() => {
        showProgressDialog.value = false
        ElMessage.success(successMessage)
        // データを遅延リフレッシュ
        setTimeout(() => {
          fetchData().catch((err) => {
            console.warn('データ更新後のリフレッシュに失敗:', err)
          })
        }, 500)
      }, 1500)
    } catch (error: any) {
      clearInterval(progressInterval)
      progressPercentage.value = 100
      progressStatus.value = 'exception'
      progressText.value = '保留データ更新に失敗しました'

      setTimeout(() => {
        showProgressDialog.value = false
        ElMessage.error(error?.response?.data?.message || '保留データ更新に失敗しました')
      }, 2000)
    } finally {
      updatingOnHold.value = false
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('保留データ更新時にエラーが発生:', error)
      showProgressDialog.value = false
      ElMessage.error(error?.response?.data?.message || '保留データ更新に失敗しました')
    }
    updatingOnHold.value = false
  }
}

// 生産計画日更新
const handleUpdateProductionDates = async () => {
  try {
    const confirmed = await ElMessageBox.confirm(
      `各工程の生産計画日を営業日換算で更新します。`,
      '生産計画日更新確認',
      {
        confirmButtonText: '更新',
        cancelButtonText: 'キャンセル',
        type: 'info',
      },
    ).catch(() => false)

    if (!confirmed) return

    updatingProductionDates.value = true
    showProgressDialog.value = true
    progressPercentage.value = 0
    progressStatus.value = ''
    progressText.value = '生産計画日データを取得中...'

    progressInfo.value = {
      current: 0,
      total: 0,
      products: 0,
      dates: 0,
      processedProducts: 0,
      processedDates: 0,
      inserted: 0,
      skipped: 0,
      currentProduct: '',
      currentDate: '',
    }

    // 模拟进度
    const progressInterval = setInterval(() => {
      if (progressPercentage.value < 90) {
        progressPercentage.value += Math.random() * 15
        if (progressPercentage.value > 90) {
          progressPercentage.value = 90
        }
        progressText.value = '生産計画日データを更新中...'
      }
    }, 300)

    try {
      const response: any = await updateProductionSummarysProductionDates()

      clearInterval(progressInterval)
      progressPercentage.value = 100
      progressStatus.value = 'success'
      progressText.value = '生産計画日更新が完了しました！'

      // 从响应中获取数据
      let updatedCount = 0
      let skippedCount = 0

      if (response?.data) {
        updatedCount = response.data.updated || 0
        skippedCount = response.data.skipped || 0
      }

      progressInfo.value.inserted = updatedCount
      progressInfo.value.skipped = skippedCount

      let successMessage = `生産計画日データの更新が成功しました！\n更新: ${updatedCount}件`
      if (skippedCount > 0) {
        successMessage += `\nスキップ: ${skippedCount}件`
      }

      setTimeout(() => {
        showProgressDialog.value = false
        ElMessage.success(successMessage)
        // データを遅延リフレッシュ
        setTimeout(() => {
          fetchData().catch((err) => {
            console.warn('データ更新後のリフレッシュに失敗:', err)
          })
        }, 500)
      }, 1500)
    } catch (error: any) {
      clearInterval(progressInterval)
      progressPercentage.value = 100
      progressStatus.value = 'exception'
      progressText.value = '生産計画日更新に失敗しました'

      setTimeout(() => {
        showProgressDialog.value = false
        ElMessage.error(error?.response?.data?.message || '生産計画日更新に失敗しました')
      }, 2000)
    } finally {
      updatingProductionDates.value = false
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('生産計画日更新時にエラーが発生:', error)
      showProgressDialog.value = false
      ElMessage.error(error?.response?.data?.message || '生産計画日更新に失敗しました')
    }
    updatingProductionDates.value = false
  }
}

// 製品マスタ更新
const handleUpdateProductMaster = async () => {
  try {
    // 初期化：現在の日付範囲を設定
    if (dateRange.value && dateRange.value.length === 2) {
      productMasterDateRange.value = [dateRange.value[0], dateRange.value[1]]
    } else {
      const defaultRange = createDefaultDateRange()
      productMasterDateRange.value = [defaultRange[0], defaultRange[1]]
    }
    showProductMasterUpdateDialog.value = true
  } catch (error: any) {
    console.error('製品マスタ更新準備時にエラーが発生:', error)
    ElMessage.error('製品マスタ更新準備に失敗しました')
  }
}

// 製品マスタ更新を確認
const confirmUpdateProductMaster = async () => {
  if (!productMasterDateRange.value || productMasterDateRange.value.length !== 2) {
    ElMessage.warning('更新期間を選択してください')
    return
  }

  const [startDate, endDate] = productMasterDateRange.value

  try {
    const confirmed = await ElMessageBox.confirm(
      `製品マスタを更新します。\n期間: ${startDate} ～ ${endDate}`,
      '製品マスタ更新確認',
      {
        confirmButtonText: '更新',
        cancelButtonText: 'キャンセル',
        type: 'info',
      },
    ).catch(() => false)

    if (!confirmed) return

    showProductMasterUpdateDialog.value = false
    updatingProductMaster.value = true
    showProgressDialog.value = true
    progressPercentage.value = 0
    progressStatus.value = ''
    progressText.value = '製品マスタデータを更新中...'

    // 模拟进度
    const progressInterval = setInterval(() => {
      if (progressPercentage.value < 90) {
        progressPercentage.value += Math.random() * 10
        if (progressPercentage.value > 90) {
          progressPercentage.value = 90
        }
      }
    }, 300)

    try {
      const response: any = await updateProductionSummarysProductMaster({
        startDate,
        endDate,
      })

      clearInterval(progressInterval)
      progressPercentage.value = 100
      progressStatus.value = 'success'
      progressText.value = '製品マスタ更新が完了しました！'

      // 从响应中获取数据
      let updatedCount = 0
      let skippedCount = 0

      if (response?.data) {
        updatedCount = response.data.updated || 0
        skippedCount = response.data.skipped || 0
      }

      progressInfo.value.inserted = updatedCount
      progressInfo.value.skipped = skippedCount

      let successMessage = `製品マスタの更新が成功しました！\n更新: ${updatedCount}件`
      if (skippedCount > 0) {
        successMessage += `\nスキップ: ${skippedCount}件`
      }

      setTimeout(() => {
        showProgressDialog.value = false
        ElMessage.success(successMessage)
        // データを遅延リフレッシュ
        setTimeout(() => {
          fetchData().catch((err) => {
            console.warn('データ更新後のリフレッシュに失敗:', err)
          })
        }, 500)
      }, 1500)
    } catch (error: any) {
      clearInterval(progressInterval)
      progressPercentage.value = 100
      progressStatus.value = 'exception'
      progressText.value = '製品マスタ更新に失敗しました'

      setTimeout(() => {
        showProgressDialog.value = false
        ElMessage.error(error?.response?.data?.message || '製品マスタ更新に失敗しました')
      }, 2000)
    } finally {
      updatingProductMaster.value = false
    }
  } catch (error: any) {
    console.error('製品マスタ更新時にエラーが発生:', error)
    ElMessage.error('製品マスタ更新に失敗しました')
    updatingProductMaster.value = false
  }
}

// 機器フィールド更新
const handleUpdateMachine = async () => {
  try {
    // 初期化：現在の日付範囲を設定
    if (dateRange.value && dateRange.value.length === 2) {
      machineDateRange.value = [dateRange.value[0], dateRange.value[1]]
    } else {
      const defaultRange = createDefaultDateRange()
      machineDateRange.value = [defaultRange[0], defaultRange[1]]
    }
    showMachineUpdateDialog.value = true
  } catch (error: any) {
    console.error('機器フィールド更新準備時にエラーが発生:', error)
    ElMessage.error('機器フィールド更新準備に失敗しました')
  }
}

// 機器フィールド更新を確認
const confirmUpdateMachine = async () => {
  if (!machineDateRange.value || machineDateRange.value.length !== 2) {
    ElMessage.warning('更新期間を選択してください')
    return
  }

  const [startDate, endDate] = machineDateRange.value

  try {
    const confirmed = await ElMessageBox.confirm(
      `機器フィールドを更新します。\n期間: ${startDate} ～ ${endDate}`,
      '機器フィールド更新確認',
      {
        confirmButtonText: '更新',
        cancelButtonText: 'キャンセル',
        type: 'info',
      },
    ).catch(() => false)

    if (!confirmed) return

    showMachineUpdateDialog.value = false
    updatingMachine.value = true
    showProgressDialog.value = true
    progressPercentage.value = 0
    progressStatus.value = ''
    progressText.value = '機器フィールドデータを更新中...'

    // 模拟进度
    const progressInterval = setInterval(() => {
      if (progressPercentage.value < 90) {
        progressPercentage.value += Math.random() * 10
        if (progressPercentage.value > 90) {
          progressPercentage.value = 90
        }
      }
    }, 300)

    try {
      const response: any = await updateProductionSummarysMachine({
        startDate,
        endDate,
      })

      clearInterval(progressInterval)
      progressPercentage.value = 100
      progressStatus.value = 'success'
      progressText.value = '機器フィールド更新が完了しました！'

      // 从响应中获取数据
      let updatedCount = 0
      let skippedCount = 0

      if (response?.data) {
        updatedCount = response.data.updated || 0
        skippedCount = response.data.skipped || 0
      }

      progressInfo.value.inserted = updatedCount
      progressInfo.value.skipped = skippedCount

      let successMessage = `機器フィールドの更新が成功しました！\n更新: ${updatedCount}件`
      if (skippedCount > 0) {
        successMessage += `\nスキップ: ${skippedCount}件`
      }

      setTimeout(() => {
        showProgressDialog.value = false
        ElMessage.success(successMessage)
        // データを遅延リフレッシュ
        setTimeout(() => {
          fetchData().catch((err) => {
            console.warn('データ更新後のリフレッシュに失敗:', err)
          })
        }, 500)
      }, 1500)
    } catch (error: any) {
      clearInterval(progressInterval)
      progressPercentage.value = 100
      progressStatus.value = 'exception'
      progressText.value = '機器フィールド更新に失敗しました'

      setTimeout(() => {
        showProgressDialog.value = false
        ElMessage.error(error?.response?.data?.message || '機器フィールド更新に失敗しました')
      }, 2000)
    } finally {
      updatingMachine.value = false
    }
  } catch (error: any) {
    console.error('機器フィールド更新時にエラーが発生:', error)
    ElMessage.error('機器フィールド更新に失敗しました')
    updatingMachine.value = false
  }
}

// 計画データ更新
const handleUpdatePlan = async () => {
  try {
    // 確認ダイアログを表示
    showPlanConfirmDialog.value = true
  } catch (error: any) {
    console.error('計画データ更新準備時にエラーが発生:', error)
    ElMessage.error('計画データ更新準備に失敗しました')
  }
}

// 計画データ更新を確認
const confirmUpdatePlan = async () => {
  showPlanConfirmDialog.value = false

  try {
    updatingPlan.value = true
    showProgressDialog.value = true
    progressPercentage.value = 0
    progressStatus.value = ''

    // 開始日を計算
    const startDate = calculateStartDate()
    if (startDate) {
      progressText.value = `開始日: ${startDate} を計算中...`
      await new Promise((resolve) => setTimeout(resolve, 300))

      // 開始日以降の計算フィールドをクリア
      progressText.value = '計算フィールドをクリア中...'
      try {
        const response: any = await clearProductionSummarysCalculatedFields(startDate)
        const cleared = response?.data?.cleared ?? response?.data?.data?.cleared ?? 0
        console.log(`計算フィールドをクリアしました: ${cleared}件 (開始日: ${startDate})`)
      } catch (error: any) {
        console.warn('計算フィールドのクリアでエラーが発生しましたが、続行します:', error)
        // 清空失败不影响后续更新，继续执行
      }
    }

    progressText.value = '計画データを取得中...'
    progressInfo.value = {
      current: 0,
      total: 0,
      products: 0,
      dates: 0,
      processedProducts: 0,
      processedDates: 0,
      inserted: 0,
      skipped: 0,
      currentProduct: '',
      currentDate: '',
    }

    const progressInterval = setInterval(() => {
      if (progressPercentage.value < 90) {
        progressPercentage.value += Math.random() * 15
        if (progressPercentage.value > 90) {
          progressPercentage.value = 90
        }
        progressText.value = '計画データを更新中...'
      }
    }, 300)

    try {
      const response: any = await updateProductionSummarysPlan()

      clearInterval(progressInterval)
      progressPercentage.value = 100
      progressStatus.value = 'success'
      progressText.value = '計画データ更新が完了しました！'

      let updatedCount = 0
      let skippedCount = 0

      if (response?.data) {
        updatedCount = response.data.updated || 0
        skippedCount = response.data.skipped || 0
      }

      progressInfo.value.inserted = updatedCount
      progressInfo.value.skipped = skippedCount

      let successMessage = `計画データの更新が成功しました！\n更新: ${updatedCount}件`
      if (skippedCount > 0) {
        successMessage += `\nスキップ: ${skippedCount}件`
      }

      setTimeout(() => {
        showProgressDialog.value = false
        ElMessage.success(successMessage)
        setTimeout(() => {
          fetchData().catch((err) => {
            console.warn('データ更新後のリフレッシュに失敗:', err)
          })
        }, 500)
      }, 1500)
    } catch (error: any) {
      clearInterval(progressInterval)
      progressPercentage.value = 100
      progressStatus.value = 'exception'
      progressText.value = '計画データ更新に失敗しました'

      setTimeout(() => {
        showProgressDialog.value = false
        ElMessage.error(error?.response?.data?.message || '計画データ更新に失敗しました')
      }, 2000)
    } finally {
      updatingPlan.value = false
    }
  } catch (error: any) {
    console.error('計画データ更新時にエラーが発生:', error)
    showProgressDialog.value = false
    ElMessage.error(error?.response?.data?.message || '計画データ更新に失敗しました')
    updatingPlan.value = false
  }
}

// 计算开始日期：找到所有工程繰越字段最后一个大于0的日期中的最早日期
const calculateStartDate = (): string | undefined => {
  if (!tableData.value || tableData.value.length === 0) {
    return undefined
  }

  // 所有繰越字段名称
  const carryOverFields = [
    'cutting_carry_over',
    'chamfering_carry_over',
    'molding_carry_over',
    'plating_carry_over',
    'welding_carry_over',
    'inspection_carry_over',
    'warehouse_carry_over',
    'outsourced_warehouse_carry_over',
    'outsourced_plating_carry_over',
    'outsourced_welding_carry_over',
    'pre_welding_inspection_carry_over',
    'pre_inspection_carry_over',
    'pre_outsourcing_carry_over',
  ]

  // 按日期分组数据
  const dataByDate = new Map<string, any[]>()
  tableData.value.forEach((row) => {
    const date = row.date
    if (date) {
      if (!dataByDate.has(date)) {
        dataByDate.set(date, [])
      }
      dataByDate.get(date)!.push(row)
    }
  })

  // 获取所有日期并排序（从新到旧）
  const sortedDates = Array.from(dataByDate.keys()).sort((a, b) => {
    return new Date(b).getTime() - new Date(a).getTime()
  })

  // 找到每个工程最后一个大于0的日期（从最新日期开始查找，找到的第一个就是最新的）
  const lastDatesWithCarryOver: Map<string, string> = new Map() // field -> date

  for (const field of carryOverFields) {
    // 从最新日期开始查找
    for (const date of sortedDates) {
      const rowsForDate = dataByDate.get(date) || []
      // 检查该日期是否有任何行的该字段大于0
      const hasCarryOver = rowsForDate.some((row) => {
        const value = row[field]
        return value !== null && value !== undefined && Number(value) > 0
      })

      if (hasCarryOver) {
        lastDatesWithCarryOver.set(field, date)
        break // 找到该工程的最后一个大于0的日期，继续下一个工程
      }
    }
  }

  // 如果找到任何日期，返回最早的日期
  if (lastDatesWithCarryOver.size > 0) {
    const dates = Array.from(lastDatesWithCarryOver.values())
    const earliestDate = dates.sort((a, b) => {
      return new Date(a).getTime() - new Date(b).getTime()
    })[0]

    // 输出详细日志
    console.log('=== 繰越データ分析 ===')
    console.log('各工程の最後の繰越データ>0の日付:')
    lastDatesWithCarryOver.forEach((date, field) => {
      const fieldLabel = columnDefinitions[field]?.label || field
      console.log(`  ${fieldLabel}: ${date}`)
    })
    console.log(`計算開始日: ${earliestDate}`)
    console.log('==================')

    return earliestDate
  }

  console.log('繰越データが見つかりませんでした。全期間を計算します。')
  return undefined
}

// 工程フィールドから工程CDへのマッピング
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
  pre_inspection: 'KT17',
  pre_outsourcing: 'KT16',
}

// 工程名称マッピング
const processCdToName: Record<string, string> = {
  KT01: '切断',
  KT02: '面取',
  KT04: '成型',
  KT05: 'メッキ',
  KT07: '溶接',
  KT09: '検査',
  KT13: '倉庫',
  KT06: '外注メッキ',
  KT08: '外注溶接',
  KT15: '外注倉庫',
  KT11: '溶接前検査',
  KT17: '外注検査前',
  KT16: '外注支給前',
}

// セルダブルクリックイベントを処理
const handleCellDoubleClick = async (row: any, column: any, cell: any, event: Event) => {
  console.log('セルダブルクリックイベント:', { row, column, cell })

  // 列属性名を取得
  const columnProp = column.property
  console.log('列属性名:', columnProp)

  // 繰越フィールドの双击弹窗功能已移除

  // 基本情報列をスキップ（id, date, product_cd, product_nameなど）
  const basicColumns = [
    'id',
    'date',
    'day_of_week',
    'route_cd',
    'product_cd',
    'product_name',
    'order_quantity',
    'forecast_quantity',
  ]
  if (basicColumns.includes(columnProp)) {
    return
  }

  // 工程フィールドを解析（例：cutting_actual -> cutting）
  const fieldParts = columnProp.split('_')
  if (fieldParts.length < 2) {
    return
  }

  // 最長の工程フィールドプレフィックスをマッチング（outsourced_weldingなどの多段命名に対応）
  let processFieldKey = ''
  for (let len = fieldParts.length - 1; len >= 1; len--) {
    const candidate = fieldParts.slice(0, len).join('_')
    if (processFieldToProcessCd[candidate]) {
      processFieldKey = candidate
      break
    }
  }

  if (!processFieldKey) {
    ElMessage.warning(`該当する工程が見つかりません: ${columnProp}`)
    return
  }

  // process_cdを取得
  const processCd = processFieldToProcessCd[processFieldKey]
  if (!processCd) {
    ElMessage.warning(`該当する工程が見つかりません: ${columnProp}`)
    return
  }

  // 製品がこの工程に属するかチェック（倉庫工程KT13を除く、すべての製品が倉庫工程を持つことができる）
  const productCd = row.product_cd || ''
  if (!productCd) {
    ElMessage.warning('製品CDが取得できませんでした')
    return
  }

  // 倉庫工程（KT13）はチェック不要、すべての製品がこの工程を持つことができる
  if (processCd !== 'KT13') {
    try {
      // 製品の工程ルートステップを取得
      const response: any = await getProductRouteSteps(productCd)

      // API応答形式を処理：配列、{data: []}、または{success: true, data: []}の可能性がある
      let routeSteps: any[] = []
      if (Array.isArray(response)) {
        routeSteps = response
      } else if (response?.data) {
        routeSteps = Array.isArray(response.data) ? response.data : []
      } else if (response?.success && response?.data) {
        routeSteps = Array.isArray(response.data) ? response.data : []
      }

      if (routeSteps.length === 0) {
        console.warn(`製品「${productCd}」の工程ルート情報が見つかりません`)
        // ルート情報がない場合でも続行を許可（新製品のルートがまだ設定されていない可能性がある）
      } else {
        // その工程が製品ルートに含まれているかチェック
        const hasProcess = routeSteps.some((step: any) => step.process_cd === processCd)

        if (!hasProcess) {
          const processName = processCdToName[processCd] || processCd
          ElMessage.warning(
            `製品「${row.product_name || productCd}」は工程「${processName}(${processCd})」に属していません。`,
          )
          return
        }
      }
    } catch (error: any) {
      console.error('工程チェックエラー:', error)
      // API呼び出しが失敗した場合でも続行を許可（ネットワーク問題による操作阻止を回避）
      console.warn('工程チェックに失敗しましたが、続行します')
    }
  }

  // ダイアログ情報を設定
  transactionInputInfo.value = {
    date: row.date || '',
    productCd: productCd,
    productName: row.product_name || '',
    processCd: processCd,
    processName: processCdToName[processCd] || processCd,
  }

  // フォームをリセット
  transactionForm.actual = null
  transactionForm.defect = null
  transactionForm.scrap = null
  transactionForm.onHold = null
  transactionForm.inbound = null
  transactionForm.outbound = null

  // ダイアログを表示
  showTransactionInputDialog.value = true
}

// 提交在庫取引ログ数据
const handleSubmitTransaction = async () => {
  if (!transactionInputInfo.value) {
    return
  }

  const { date, productCd, processCd } = transactionInputInfo.value
  const isWarehouse = processCd === 'KT13'
  const isOutsourcedWarehouse = processCd === 'KT15'

  // 少なくとも1つの数量入力があるかチェック（工程タイプに応じて異なるフィールドをチェック）
  let hasAnyValue = false
  if (isWarehouse) {
    // 倉庫工程：入庫、出庫、廃棄、保留
    hasAnyValue =
      (transactionForm.inbound !== null && transactionForm.inbound !== 0) ||
      (transactionForm.outbound !== null && transactionForm.outbound !== 0) ||
      (transactionForm.scrap !== null && transactionForm.scrap !== 0) ||
      (transactionForm.onHold !== null && transactionForm.onHold !== 0)
  } else if (isOutsourcedWarehouse) {
    // 外注倉庫工程：入庫（actualフィールドを使用）、廃棄
    hasAnyValue =
      (transactionForm.actual !== null && transactionForm.actual !== 0) ||
      (transactionForm.scrap !== null && transactionForm.scrap !== 0)
  } else {
    // 通常工程：実績、不良、廃棄、保留
    hasAnyValue =
      (transactionForm.actual !== null && transactionForm.actual !== 0) ||
      (transactionForm.defect !== null && transactionForm.defect !== 0) ||
      (transactionForm.scrap !== null && transactionForm.scrap !== 0) ||
      (transactionForm.onHold !== null && transactionForm.onHold !== 0)
  }

  if (!hasAnyValue) {
    ElMessage.warning('少なくとも1つの数量を入力してください')
    return
  }

  submittingTransaction.value = true

  try {
    const now = new Date()
    const transactionTime = `${date} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`

    // 操作種別マッピング - 工程タイプに応じて異なるマッピングを使用
    const transactionTypes = []

    if (isWarehouse) {
      // 倉庫工程：入庫、出庫、廃棄、保留
      if (transactionForm.inbound !== null && transactionForm.inbound !== 0) {
        transactionTypes.push({ type: '入庫', value: transactionForm.inbound })
      }
      if (transactionForm.outbound !== null && transactionForm.outbound !== 0) {
        transactionTypes.push({ type: '出庫', value: transactionForm.outbound })
      }
      if (transactionForm.scrap !== null && transactionForm.scrap !== 0) {
        transactionTypes.push({ type: '廃棄', value: transactionForm.scrap })
      }
      if (transactionForm.onHold !== null && transactionForm.onHold !== 0) {
        transactionTypes.push({ type: '保留', value: transactionForm.onHold })
      }
    } else if (isOutsourcedWarehouse) {
      // 外注倉庫工程：入庫（actualフィールドを使用）、廃棄
      if (transactionForm.actual !== null && transactionForm.actual !== 0) {
        transactionTypes.push({ type: '入庫', value: transactionForm.actual })
      }
      if (transactionForm.scrap !== null && transactionForm.scrap !== 0) {
        transactionTypes.push({ type: '廃棄', value: transactionForm.scrap })
      }
    } else {
      // 通常工程：実績、不良、廃棄、保留
      if (transactionForm.actual !== null && transactionForm.actual !== 0) {
        transactionTypes.push({ type: '実績', value: transactionForm.actual })
      }
      if (transactionForm.defect !== null && transactionForm.defect !== 0) {
        transactionTypes.push({ type: '不良', value: transactionForm.defect })
      }
      if (transactionForm.scrap !== null && transactionForm.scrap !== 0) {
        transactionTypes.push({ type: '廃棄', value: transactionForm.scrap })
      }
      if (transactionForm.onHold !== null && transactionForm.onHold !== 0) {
        transactionTypes.push({ type: '保留', value: transactionForm.onHold })
      }
    }

    // 工程タイプに応じてstock_typeを決定：倉庫工程と検査工程は"製品"、その他の工程は"仕掛品"
    const stockType =
      processCd === 'KT13' || processCd === 'KT09' || isOutsourcedWarehouse ? '製品' : '仕掛品'

    // processNameまたはprocessCdに'倉庫'が含まれているかどうかでlocation_cdの値を決定
    const processName = transactionInputInfo.value?.processName || processCdToName[processCd] || ''
    const hasWarehouse = processName.includes('倉庫') || processCd.includes('倉庫')
    const locationCd = isOutsourcedWarehouse ? '外注倉庫' : hasWarehouse ? '製品' : '工程中間在庫'

    // 工程タイプに応じてunitを決定：検査工程は"本"、その他はnull
    const unit = processCd === 'KT09' ? '本' : null

    const insertPromises = transactionTypes.map((item) => {
      return request.post('/api/stock/transaction', {
        stock_type: stockType,
        target_cd: productCd,
        location_cd: locationCd,
        transaction_type: item.type,
        quantity: item.value!,
        unit: unit,
        process_cd: processCd,
        base_qty: null,
        lot_no: null,
        related_doc_type: null,
        related_doc_no: null,
        operator_name: null,
        remarks: null,
        transaction_time: transactionTime,
        machine_cd: null,
      })
    })

    await Promise.all(insertPromises)

    ElMessage.success('在庫取引ログを登録しました')
    showTransactionInputDialog.value = false

    // データをリフレッシュ
    setTimeout(() => {
      fetchData().catch((err) => {
        console.warn('データ更新後のリフレッシュに失敗:', err)
      })
    }, 500)
  } catch (error: any) {
    console.error('在庫取引ログ登録エラー:', error)
    const errorMessage =
      error?.response?.data?.message || error?.message || '在庫取引ログの登録に失敗しました'
    ElMessage.error(errorMessage)
  } finally {
    submittingTransaction.value = false
  }
}

// 実績一括登録 - ダイアログを開く
const handleOpenBatchActualDialog = () => {
  handleResetBatchActual()
  showBatchActualDialog.value = true
}

// 実績一括登録 - 日付変更処理
const handleBatchActualDateChange = (date: string) => {
  batchActualTableData.value.forEach((row) => {
    row.date = date
  })
}

// 実績一括登録 - 製品変更処理
const handleProductChange = (index: number, productCd: string) => {
  const product = productList.value.find((p) => p.product_cd === productCd)
  if (product) {
    batchActualTableData.value[index].product_name = product.product_name || ''
  } else {
    batchActualTableData.value[index].product_name = ''
  }
}

// 実績一括登録 - リセット
const handleResetBatchActual = () => {
  batchActualDate.value = ''
  batchActualTableData.value = [
    {
      product_cd: '',
      product_name: '',
      date: '',
      cuttingActual: null,
      chamferingActual: null,
      moldingActual: null,
    },
    {
      product_cd: '',
      product_name: '',
      date: '',
      cuttingActual: null,
      chamferingActual: null,
      moldingActual: null,
    },
  ]
}

// 格式化日期（仅日期部分）
const formatDateOnly = (dateStr: string | null | undefined) => {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  } catch {
    return dateStr
  }
}

// 格式化数字
const formatNumber = (num: number | null | undefined) => {
  if (num === null || num === undefined || isNaN(num)) return '0'
  return num.toLocaleString('ja-JP')
}

// 获取初期在庫数据
const fetchInitialStockData = async () => {
  loadingInitialStock.value = true
  try {
    const params: any = {
      transaction_type: '初期',
      page: initialStockPagination.currentPage,
      pageSize: initialStockPagination.pageSize,
    }

    if (initialStockFilter.keyword) {
      params.keyword = initialStockFilter.keyword
    }
    if (initialStockFilter.processCd) {
      params.process_cd = initialStockFilter.processCd
    }

    // 月份筛选：将月份转换为该月1号的日期范围
    if (initialStockFilter.month) {
      const firstDay = `${initialStockFilter.month}-01`
      params.date_range = [firstDay, firstDay]
    }

    const response: any = await request.get('/api/stock/logs', { params })

    let list: any[] = []
    let total = 0
    if (response?.data?.list) {
      list = response.data.list
      total = response.data.total || 0
    } else if (response?.list) {
      list = response.list
      total = response.total || 0
    } else if (Array.isArray(response)) {
      list = response
      total = response.length
    }

    // 編集状態を追加し、製品名でソート（デフォルトは昇順）
    const sortedList = list.sort((a: any, b: any) => {
      const nameA = (a.target_name || a.target_cd || '').toString().trim()
      const nameB = (b.target_name || b.target_cd || '').toString().trim()
      return nameA.localeCompare(nameB, 'ja', { numeric: true })
    })

    initialStockData.value = sortedList.map((item: any) => ({
      ...item,
      editing: false,
      editQuantity: item.quantity,
    }))

    initialStockPagination.total = total
  } catch (error: any) {
    console.error('初期在庫データ取得エラー:', error)
    ElMessage.error('初期在庫データの取得に失敗しました')
    initialStockData.value = []
    initialStockPagination.total = 0
  } finally {
    loadingInitialStock.value = false
  }
}

// 初期在庫検索
const handleInitialStockSearch = () => {
  initialStockPagination.currentPage = 1 // 重置到第一页
  fetchInitialStockData()
}

// 分页变化处理
const handleInitialStockPageChange = (page: number) => {
  initialStockPagination.currentPage = page
  fetchInitialStockData()
}

const handleInitialStockSizeChange = (size: number) => {
  initialStockPagination.pageSize = size
  initialStockPagination.currentPage = 1
  fetchInitialStockData()
}

// 編集初期在庫
const handleEditInitialStock = (row: any) => {
  row.editing = true
  row.editQuantity = row.quantity
}

// 保存初期在庫
const handleSaveInitialStock = async (row: any) => {
  if (row.editQuantity === null || row.editQuantity === undefined) {
    ElMessage.warning('数量を入力してください')
    return
  }

  try {
    // 使用 production-actual 的更新API，需要发送所有必填字段
    await request.put(`/api/production-actual/stock-logs/${row.id}`, {
      transaction_time:
        row.transaction_time || new Date().toISOString().slice(0, 19).replace('T', ' '),
      transaction_type: row.transaction_type || '初期',
      target_cd: row.target_cd,
      quantity: row.editQuantity,
      stock_type: row.stock_type || (row.process_cd === 'KT13' ? '製品' : '仕掛品'),
      location_cd: row.location_cd || row.process_cd,
      machine_cd: row.machine_cd || null,
      related_doc_no: row.related_doc_no || null,
    })

    row.quantity = row.editQuantity
    row.editing = false
    ElMessage.success('更新しました')
  } catch (error: any) {
    console.error('初期在庫更新エラー:', error)
    ElMessage.error(error?.response?.data?.message || '更新に失敗しました')
  }
}

// 取消編集
const handleCancelEditInitialStock = (row: any) => {
  row.editing = false
  row.editQuantity = row.quantity
}

// 削除初期在庫
const handleDeleteInitialStock = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `初期在庫を削除しますか？\n製品: ${row.target_name || row.target_cd}\n工程: ${row.process_name || row.process_cd}\n数量: ${row.quantity}`,
      '確認',
      {
        confirmButtonText: '削除',
        cancelButtonText: 'キャンセル',
        type: 'warning',
      },
    )

    // 使用 stock 的删除API
    await request.delete(`/api/stock/logs/${row.id}`)
    ElMessage.success('削除しました')
    await fetchInitialStockData()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('初期在庫削除エラー:', error)
      ElMessage.error(error?.response?.data?.message || '削除に失敗しました')
    }
  }
}

// 弹窗打开时加载数据
const handleOpenInitialStockDialog = () => {
  showInitialStockDialog.value = true
  // 默认设置为当前月份
  if (!initialStockFilter.month) {
    const now = new Date()
    const year = now.getFullYear()
    const month = String(now.getMonth() + 1).padStart(2, '0')
    initialStockFilter.month = `${year}-${month}`
  }
  fetchInitialStockData()
}

// 初期在庫一括登録ダイアログを開く
const handleOpenBatchInitialStockDialog = () => {
  showBatchInitialStockDialog.value = true
  // 默认设置为当前月份
  if (!batchInitialStockFilter.month) {
    const now = new Date()
    const year = now.getFullYear()
    const month = String(now.getMonth() + 1).padStart(2, '0')
    batchInitialStockFilter.month = `${year}-${month}`
  }
  handleBatchInitialStockSearch()
}

// 初期在庫一括登録検索
const handleBatchInitialStockSearch = async () => {
  if (!batchInitialStockFilter.month || !batchInitialStockFilter.processCd) {
    ElMessage.warning('月と工程を選択してください')
    return
  }

  loadingBatchInitialStock.value = true
  try {
    // 根据工程获取产品列表
    let products: any[] = []
    try {
      const processProductsResponse: any = await request.get('/api/inventory/products-by-process', {
        params: { process_cd: batchInitialStockFilter.processCd },
        timeout: 15000,
      })

      const processProducts = processProductsResponse?.data || processProductsResponse || []

      if (processProducts.length > 0) {
        // 从工程产品API获取的产品CD列表
        const productCds = processProducts.map((p: any) => p.product_cd)

        // 获取这些产品的完整信息（包括product_type, status等）
        const productsResponse: any = await request.get('/api/products')
        let allProducts: any[] = []
        if (productsResponse?.data) {
          allProducts = Array.isArray(productsResponse.data)
            ? productsResponse.data
            : productsResponse.data.list || []
        } else if (Array.isArray(productsResponse)) {
          allProducts = productsResponse
        }

        // 创建产品CD到产品信息的映射
        const productMap = new Map<string, any>()
        allProducts.forEach((product: any) => {
          const productCd = String(
            product.product_cd || product.product_code || product.code || '',
          ).trim()
          if (productCd) {
            productMap.set(productCd, product)
          }
        })

        // 只保留属于该工程的产品，并合并工程产品API返回的产品名称
        products = productCds
          .map((productCd: string) => {
            const fullProduct = productMap.get(productCd)
            const processProduct = processProducts.find((p: any) => p.product_cd === productCd)

            if (fullProduct) {
              // 如果有完整产品信息，使用它，但优先使用工程产品API返回的产品名称
              return {
                ...fullProduct,
                product_name: processProduct?.product_name || fullProduct.product_name || productCd,
              }
            } else if (processProduct) {
              // 如果没有完整产品信息，使用工程产品API返回的信息
              return {
                product_cd: productCd,
                product_name: processProduct.product_name || productCd,
                product_type: null,
                status: null,
                is_active: null,
              }
            }
            return null
          })
          .filter((p: any) => p !== null)

        console.log(`工程 ${batchInitialStockFilter.processCd} の製品数: ${products.length}`)
      } else {
        console.warn(
          `工程 ${batchInitialStockFilter.processCd} に該当する製品が見つかりませんでした`,
        )
        ElMessage.warning(
          `工程 ${batchInitialStockFilter.processCd} に該当する製品が見つかりませんでした`,
        )
        batchInitialStockData.value = []
        return
      }
    } catch (error: any) {
      console.error('工程別製品取得エラー:', error)
      // 如果工程产品API失败，回退到获取所有产品
      const productsResponse: any = await request.get('/api/products')
      if (productsResponse?.data) {
        products = Array.isArray(productsResponse.data)
          ? productsResponse.data
          : productsResponse.data.list || []
      } else if (Array.isArray(productsResponse)) {
        products = productsResponse
      }
      ElMessage.warning('工程別製品の取得に失敗しました。すべての製品を表示します。')
    }

    console.log('元の製品数:', products.length)
    if (products.length > 0) {
      console.log('最初の製品例:', products[0])
    }

    // 製品リストをフィルタリング（工程フィルタは既に適用済み）
    const filteredProducts = products.filter((product: any) => {
      try {
        // 1. 製品CDフィルタ：製品コードの最後の文字が1でない製品を除外
        const productCd = String(
          product.product_cd || product.product_code || product.code || '',
        ).trim()
        if (!productCd || productCd.length === 0) {
          // 製品コードがない場合、除外
          return false
        }
        const lastChar = productCd[productCd.length - 1]
        if (lastChar !== '1') {
          return false
        }

        // 2. 製品名フィルタ：製品名に「加工」または「アーチ」を含む製品を除外
        const productName = String(
          product.product_name || product.name || product.productName || '',
        ).trim()
        if (productName && (productName.includes('加工') || productName.includes('アーチ'))) {
          return false
        }

        // 3. Statusフィルタ：statusフィールドがinactiveの製品を除外
        let statusSource = ''
        if (product.status !== undefined && product.status !== null && product.status !== '') {
          statusSource = String(product.status).trim()
        } else if (product.is_active !== undefined && product.is_active !== null) {
          statusSource = String(product.is_active).trim()
        }
        const status = statusSource.toLowerCase()
        if (status === 'inactive' || status === '0' || status === 'false') {
          return false
        }

        // 4. Product Typeフィルタ：product_typeが「量産品」または「試作品」の製品のみ保持
        const productType = String(
          product.product_type || product.type || product.productType || '',
        ).trim()
        if (productType && productType !== '量産品' && productType !== '試作品') {
          return false
        }

        return true
      } catch (error) {
        console.error('製品フィルタエラー:', error, product)
        return false
      }
    })

    console.log('元の製品数:', products.length)
    console.log('フィルタ後の製品数:', filteredProducts.length)
    if (filteredProducts.length === 0 && products.length > 0) {
      console.warn('すべての製品がフィルタされました。フィルタ条件を確認してください')
      console.log('最初の製品例:', products[0])
    }
    products = filteredProducts

    // この月と工程の既存初期在庫データを取得
    const firstDay = `${batchInitialStockFilter.month}-01`
    const existingLogsResponse: any = await request.get('/api/stock/logs', {
      params: {
        transaction_type: '初期',
        process_cd: batchInitialStockFilter.processCd,
        date_range: [firstDay, firstDay],
        page: 1,
        pageSize: 5000, // 初期在庫は件数が多いため大きめに取得
      },
    })

    let existingLogs: any[] = []
    if (existingLogsResponse?.data?.list) {
      existingLogs = existingLogsResponse.data.list
    } else if (existingLogsResponse?.list) {
      existingLogs = existingLogsResponse.list
    } else if (Array.isArray(existingLogsResponse)) {
      existingLogs = existingLogsResponse
    }

    // 既存データのマッピングを作成（product_cdをキーとして）
    const existingMap = new Map<string, any>()
    existingLogs.forEach((log: any) => {
      existingMap.set(log.target_cd, {
        quantity: log.quantity,
        transaction_time: log.transaction_time,
        id: log.id,
      })
    })

    // 製品リストと既存データをマージ
    batchInitialStockData.value = products.map((product: any) => {
      const existing = existingMap.get(product.product_cd)
      return {
        product_cd: product.product_cd,
        product_name: product.product_name || product.product_cd,
        editQuantity: existing ? existing.quantity : null,
        existing_quantity: existing ? existing.quantity : null,
        transaction_time: existing ? existing.transaction_time : null,
        existing_id: existing ? existing.id : null,
      }
    })

    // 製品名でソート
    batchInitialStockData.value.sort((a: any, b: any) => {
      const nameA = (a.product_name || a.product_cd || '').toString().trim()
      const nameB = (b.product_name || b.product_cd || '').toString().trim()
      return nameA.localeCompare(nameB, 'ja', { numeric: true })
    })
  } catch (error: any) {
    console.error('初期在庫一括登録データ取得エラー:', error)
    ElMessage.error('データの取得に失敗しました')
    batchInitialStockData.value = []
  } finally {
    loadingBatchInitialStock.value = false
  }
}

// 初期在庫一括保存
const handleSaveBatchInitialStock = async () => {
  if (!batchInitialStockFilter.month || !batchInitialStockFilter.processCd) {
    ElMessage.warning('月と工程を選択してください')
    return
  }

  submittingBatchInitialStock.value = true
  try {
    const firstDay = `${batchInitialStockFilter.month}-01`
    const transactionTime = `${firstDay} 00:00:00`

    // 根据process_cd自动设置在庫種別、保管場所、単位
    let stockType = '仕掛品'
    let locationCd = '工程中間在庫'
    const unit = '本'

    if (
      batchInitialStockFilter.processCd === 'KT13' ||
      batchInitialStockFilter.processCd === 'KT15'
    ) {
      stockType = '製品'
    }

    if (batchInitialStockFilter.processCd === 'KT13') {
      locationCd = '製品倉庫'
    } else if (batchInitialStockFilter.processCd === 'KT15') {
      locationCd = '外注倉庫'
    }

    // 一括挿入と更新のデータを準備
    const insertPromises: Promise<any>[] = []
    const updatePromises: Promise<any>[] = []
    let updateCount = 0
    let insertCount = 0

    for (const item of batchInitialStockData.value) {
      // 新数量と既存数量を取得し、数値に変換して比較
      const newQuantity =
        item.editQuantity === null || item.editQuantity === undefined
          ? 0
          : Number(item.editQuantity)
      const existingQuantity =
        item.existing_quantity === null || item.existing_quantity === undefined
          ? 0
          : Number(item.existing_quantity)

      // 数量フィールドと既存数量が異なる場合のみ更新または追加
      if (newQuantity !== existingQuantity) {
        if (item.existing_id) {
          // 既存レコードを更新（数量が0でも更新）
          updatePromises.push(
            request.put(`/api/production-actual/stock-logs/${item.existing_id}`, {
              transaction_time: transactionTime,
              transaction_type: '初期',
              target_cd: item.product_cd,
              quantity: newQuantity,
              stock_type: stockType,
              location_cd: locationCd,
              unit: unit,
              machine_cd: null,
              related_doc_no: null,
            }),
          )
          updateCount++
        } else {
          // 新規レコードを挿入（数量が0より大きい場合のみ挿入）
          if (newQuantity > 0) {
            insertPromises.push(
              request.post('/api/stock/transaction', {
                stock_type: stockType,
                target_cd: item.product_cd,
                location_cd: locationCd,
                transaction_type: '初期',
                quantity: newQuantity,
                unit: unit,
                process_cd: batchInitialStockFilter.processCd,
                base_qty: null,
                lot_no: null,
                related_doc_type: null,
                related_doc_no: null,
                operator_name: null,
                remarks: null,
                transaction_time: transactionTime,
                machine_cd: null,
              }),
            )
            insertCount++
          }
        }
      }
    }

    // 检查是否有数据需要保存
    if (insertPromises.length === 0 && updatePromises.length === 0) {
      ElMessage.info('変更されたデータがありません')
      submittingBatchInitialStock.value = false
      return
    }

    // 执行所有操作
    await Promise.all([...insertPromises, ...updatePromises])

    const message = `初期在庫を一括保存しました（更新: ${updateCount}件、追加: ${insertCount}件）`
    ElMessage.success(message)

    // 重新加载数据
    await handleBatchInitialStockSearch()

    // 如果初期在庫管理ダイアログ正在打开，同步刷新该列表
    if (showInitialStockDialog.value) {
      await fetchInitialStockData()
    }
  } catch (error: any) {
    console.error('初期在庫一括保存エラー:', error)
    ElMessage.error(error?.response?.data?.message || '保存に失敗しました')
  } finally {
    submittingBatchInitialStock.value = false
  }
}

// 工程別計画確認印刷 - データ取得
const fetchPrintData = async (targetDate: string): Promise<any[]> => {
  try {
    // 選択日付を基準に十分な日付範囲でデータを取得（過去90日〜未来90日）
    // production_dateフィールドで筛选するため、広い範囲を取得
    const target = new Date(targetDate)
    const startDate = new Date(target)
    startDate.setDate(startDate.getDate() - 90)
    const endDate = new Date(target)
    endDate.setDate(endDate.getDate() + 90)

    const formatDateStr = (d: Date) => d.toISOString().split('T')[0]

    const params: any = {
      page: 1,
      limit: 50000, // 十分な件数を取得
      startDate: formatDateStr(startDate),
      endDate: formatDateStr(endDate),
    }

    const response: any = await getProductionSummarysList(params)

    if (response?.data?.list) {
      return response.data.list
    } else if (Array.isArray(response)) {
      return response
    }
    return []
  } catch (error) {
    console.error('印刷用データ取得エラー:', error)
    return []
  }
}

// 工程別印刷機能
const buildProcessPrintHtml = (allData: any[], targetDate: string) => {
  const now = new Date().toLocaleString('ja-JP', { hour12: false })
  const today = targetDate // ユーザーが選択した日付を使用

  // 日付フォーマット関数（内部使用）
  const formatDateForFilter = (dateValue: any): string | null => {
    if (!dateValue) return null
    if (typeof dateValue === 'string') {
      return dateValue.split('T')[0]
    }
    if (dateValue instanceof Date) {
      return dateValue.toISOString().split('T')[0]
    }
    return null
  }

  // 4つの工程の設定
  const processConfigs = [
    {
      name: '成型工程',
      color: '#6366f1',
      columns: [
        { key: 'product_name', label: '製品名', width: '28%' },
        { key: 'molding_production_date', label: '推奨成型生産日', width: '18%' },
        { key: 'molding_trend', label: '成型推移', width: '12%' },
        { key: 'molding_plan', label: '成型計画', width: '12%' },
        { key: '_plan_status', label: '計画状態', width: '18%', planField: 'molding_plan' },
        { key: '_confirm', label: '確認', width: '12%', isCheckbox: true },
      ],
      trendField: 'molding_trend',
      productionDateField: 'molding_production_date',
    },
    {
      name: 'メッキ工程',
      color: '#f59e0b',
      columns: [
        { key: 'product_name', label: '製品名', width: '28%' },
        { key: 'plating_production_date', label: '推奨メッキ生産日', width: '18%' },
        { key: 'plating_trend', label: 'メッキ推移', width: '12%' },
        { key: 'plating_plan', label: 'メッキ計画', width: '12%' },
        { key: '_plan_status', label: '計画状態', width: '18%', planField: 'plating_plan' },
        { key: '_confirm', label: '確認', width: '12%', isCheckbox: true },
      ],
      trendField: 'plating_trend',
      productionDateField: 'plating_production_date',
    },
    {
      name: '溶接工程',
      color: '#10b981',
      columns: [
        { key: 'product_name', label: '製品名', width: '28%' },
        { key: 'welding_production_date', label: '推奨溶接生産日', width: '18%' },
        { key: 'welding_trend', label: '溶接推移', width: '12%' },
        { key: 'welding_plan', label: '溶接計画', width: '12%' },
        { key: '_plan_status', label: '計画状態', width: '18%', planField: 'welding_plan' },
        { key: '_confirm', label: '確認', width: '12%', isCheckbox: true },
      ],
      trendField: 'welding_trend',
      productionDateField: 'welding_production_date',
    },
    {
      name: '倉庫',
      color: '#8b5cf6',
      columns: [
        { key: 'product_name', label: '製品名', width: '40%' },
        { key: 'inspection_inventory', label: '検査在庫', width: '20%' },
        { key: 'warehouse_inventory', label: '倉庫在庫', width: '25%' },
        { key: '_confirm', label: '確認', width: '15%', isCheckbox: true },
      ],
      trendField: 'warehouse_inventory',
      productionDateField: 'date',
    },
  ]

  // 当日日付（date字段）のデータをproduct_cdでマッピング（計画値取得用）
  const todayDataMap = new Map<string, any>()
  allData.forEach((row) => {
    const rowDate = formatDateForFilter(row.date)
    if (rowDate === today && row.product_cd) {
      todayDataMap.set(row.product_cd, row)
    }
  })

  // 各工程のproduction_date === 選択日のデータをproduct_cdでマッピング（trend値取得用）
  // 同じproduct_cdが複数ある場合、trend < 0 のレコードを優先して保持
  const processDataMaps = new Map<string, Map<string, any[]>>()
  processConfigs.forEach((config) => {
    if (config.productionDateField && config.trendField) {
      const processMap = new Map<string, any[]>()
      allData.forEach((row) => {
        const prodDate = row[config.productionDateField as keyof typeof row]
        const prodDateStr = formatDateForFilter(prodDate)
        if (prodDateStr === today && row.product_cd) {
          // 同じproduct_cdの全てのレコードを保持
          if (!processMap.has(row.product_cd)) {
            processMap.set(row.product_cd, [])
          }
          processMap.get(row.product_cd)!.push(row)
        }
      })
      processDataMaps.set(config.name, processMap)
    }
  })

  // 各工程のセクションを生成（分页なし、上から下へ配置）
  const pages = processConfigs
    .map((config) => {
      // 各工程独立にデータをフィルタリング
      // 方法：production_date === 選択日のレコードを全て取得し、その中でtrend < 0のものを表示
      let filteredData: any[] = []

      if (
        config.productionDateField &&
        config.productionDateField !== 'date' &&
        config.trendField
      ) {
        // 成型、メッキ、溶接工程：production_date === 選択日のレコードから、trend < 0のものを取得
        const processMap = processDataMaps.get(config.name)
        if (processMap) {
          // processDataMapsには既にproduction_date === 選択日のレコードが入っている（配列形式）
          processMap.forEach((processRows) => {
            // 同じproduct_cdの全てのレコードからtrend < 0のものを探す
            for (const processRow of processRows) {
              const trendValue = processRow[config.trendField as keyof typeof processRow] as number
              if (typeof trendValue === 'number' && trendValue < 0) {
                // production_date === 選択日 かつ trend < 0 のレコードを使用
                filteredData.push(processRow)
                break // 1つ見つかったらそのproduct_cdは終了
              }
            }
          })
        }
      } else if (config.productionDateField === 'date' && config.trendField) {
        // 倉庫工程：date === 選択日 かつ trend < 0
        filteredData = allData.filter((row) => {
          const rowDate = formatDateForFilter(row.date)
          if (rowDate !== today) return false
          const trendValue = row[config.trendField as keyof typeof row] as number
          return typeof trendValue === 'number' && trendValue < 0
        })
      }

      // 同じproduct_cdの重複を除去（product_cdで一意にする）
      // 優先順位：trend < 0 のレコードを優先
      const uniqueDataMap = new Map<string, any>()
      filteredData.forEach((row) => {
        if (row.product_cd) {
          if (!uniqueDataMap.has(row.product_cd)) {
            uniqueDataMap.set(row.product_cd, row)
          } else {
            // 既存のレコードと比較して、trend < 0 のレコードを優先
            const existingRow = uniqueDataMap.get(row.product_cd)
            if (config.trendField) {
              const existingTrend = existingRow[
                config.trendField as keyof typeof existingRow
              ] as number
              const currentTrend = row[config.trendField as keyof typeof row] as number
              // 現在のレコードのtrend値がより小さい（より負の値）場合、置き換え
              if (
                typeof currentTrend === 'number' &&
                typeof existingTrend === 'number' &&
                currentTrend < existingTrend
              ) {
                uniqueDataMap.set(row.product_cd, row)
              }
            }
          }
        }
      })
      filteredData = Array.from(uniqueDataMap.values())

      const headerCells = config.columns
        .map((col: any) => `<th style="width: ${col.width || 'auto'}">${col.label}</th>`)
        .join('')
      const bodyRows = filteredData
        .map((row) => {
          // 当日日付（date字段）のデータから計画値を取得
          const todayRow = todayDataMap.get(row.product_cd) || row
          // 各工程のproduction_date === 選択日のデータからtrend値を取得
          // filteredDataには既にtrend < 0の正しいレコードが入っているため、rowをそのまま使用
          const processRow = row

          const cells = config.columns
            .map((col: any) => {
              // 確認フィールド（チェックボックス）
              if (col.isCheckbox) {
                return `<td class="checkbox-cell"><span class="checkbox-box"></span></td>`
              }
              // 計画状態フィールド（当日日付のplan > 0 なら「生産計画あり」、それ以外は「確認必要」）
              if (col.planField) {
                const planValue = todayRow[col.planField as keyof typeof todayRow]
                const hasPlan = typeof planValue === 'number' && planValue > 0
                if (hasPlan) {
                  return `<td class="plan-status has-plan">生産計画あり</td>`
                } else {
                  return `<td class="plan-status need-confirm">確認必要</td>`
                }
              }
              // 計画フィールド（当日日付のデータから取得）
              if (col.key.includes('_plan') && !col.key.startsWith('_')) {
                const planValue = todayRow[col.key as keyof typeof todayRow]
                if (typeof planValue === 'number') {
                  return `<td>${planValue.toLocaleString()}</td>`
                }
                return `<td>${formatPrintCellValue(planValue)}</td>`
              }
              // trendフィールド（各工程のproduction_date === 選択日のデータから取得）
              if (col.key === config.trendField) {
                let trendValue: any = null
                if (processRow) {
                  trendValue = processRow[col.key as keyof typeof processRow]
                }
                // 取得できない場合は現在のレコードから取得
                if (trendValue === null || trendValue === undefined) {
                  trendValue = row[col.key as keyof typeof row]
                }
                if (typeof trendValue === 'number') {
                  return `<td class="${trendValue < 0 ? 'negative' : ''}">${trendValue.toLocaleString()}</td>`
                }
                return `<td>${formatPrintCellValue(trendValue)}</td>`
              }
              let value = row[col.key as keyof typeof row]
              // 日付フィールドのフォーマット
              if (col.key.includes('production_date') && value) {
                if (typeof value === 'string') {
                  value = formatDate(value)
                } else if (value instanceof Date) {
                  value = formatDate(value.toISOString())
                }
              }
              // 数値フィールドのフォーマット
              if (typeof value === 'number') {
                return `<td class="${value < 0 ? 'negative' : ''}">${value.toLocaleString()}</td>`
              }
              return `<td>${formatPrintCellValue(value)}</td>`
            })
            .join('')
          return `<tr>${cells}</tr>`
        })
        .join('')

      return `
      <div class="process-section">
        <div class="process-header" style="background: ${config.color};">
          <h2>${config.name}</h2>
        </div>
        <div class="process-meta">
          対象日: ${today} | 件数: ${filteredData.length}件 (${config.name === '倉庫' ? '在庫' : '推移'} < 0)
        </div>
        <table>
          <thead><tr>${headerCells}</tr></thead>
          <tbody>${bodyRows.length > 0 ? bodyRows : '<tr><td colspan="' + config.columns.length + '">該当データなし</td></tr>'}</tbody>
        </table>
      </div>
    `
    })
    .join('')

  return `
    <!DOCTYPE html>
    <html lang="ja">
      <head>
        <meta charset="UTF-8" />
        <title>工程別生産サマリー印刷</title>
        <style>
          @page { size: A4 portrait; margin: 10mm; }
          * { box-sizing: border-box; }
          body {
            font-family: 'Segoe UI','Hiragino Sans','Noto Sans JP',sans-serif;
            margin: 0;
            padding: 12px;
            color: #1e293b;
            background: #fff;
            font-size: 11px;
          }
          .print-title {
            text-align: center;
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 8px;
            color: #1e293b;
          }
          .print-time {
            text-align: center;
            font-size: 10px;
            color: #64748b;
            margin-bottom: 16px;
          }
          .process-section {
            margin-bottom: 16px;
          }
          .process-header {
            color: white;
            padding: 6px 12px;
            border-radius: 4px 4px 0 0;
            margin-bottom: 0;
          }
          .process-header h2 {
            margin: 0;
            font-size: 14px;
            font-weight: 600;
          }
          .process-meta {
            background: #f1f5f9;
            padding: 4px 12px;
            font-size: 9px;
            color: #475569;
            border-bottom: 1px solid #e2e8f0;
          }
          table {
            width: 100%;
            border-collapse: collapse;
            font-size: 9px;
            margin-bottom: 0;
            table-layout: fixed;
          }
          th, td {
            border: 1px solid #e2e8f0;
            padding: 4px 6px;
            text-align: center;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }
          th {
            background: #f8fafc;
            font-weight: 600;
            color: #334155;
          }
          td:first-child {
            text-align: left;
            padding-left: 8px;
          }
          tr:nth-child(even) { background: #fafafa; }
          .negative {
            color: #dc2626;
            font-weight: 600;
          }
          .checkbox-cell {
            text-align: center;
          }
          .checkbox-box {
            display: inline-block;
            width: 14px;
            height: 14px;
            border: 2px solid #64748b;
            border-radius: 3px;
            background: #fff;
            vertical-align: middle;
          }
          .plan-status {
            font-weight: 600;
            font-size: 8px;
          }
          .plan-status.has-plan {
            color: #059669;
            background: #d1fae5;
          }
          .plan-status.need-confirm {
            color: #dc2626;
            background: #fee2e2;
          }
          @media print {
            body { padding: 0; }
          }
        </style>
      </head>
      <body>
        <div class="print-title">工程別生産計画確認サマリー(成型、メッキ、溶接、倉庫)</div>
        <div class="print-time">出力時間: ${now}</div>
        ${pages}
      </body>
    </html>
  `
}

// 工程別計画確認印刷
const handleProcessPrint = () => {
  // 日付選択ダイアログを表示
  const today = new Date().toISOString().split('T')[0]
  printTargetDate.value = today
  showPrintDateDialog.value = true
}

const handleConfirmPrintDate = async () => {
  if (!printTargetDate.value) {
    ElMessage.warning('日付を選択してください。')
    return
  }

  const selectedDate = printTargetDate.value
  showPrintDateDialog.value = false

  // 独立してデータを取得（画面のフィルタに依存しない）
  const loadingMessage = ElMessage.info({
    message: '印刷データを取得中...',
    duration: 0,
  })

  try {
    const allData = await fetchPrintData(selectedDate)
    loadingMessage.close()

    if (!allData.length) {
      ElMessage.warning('印刷できるデータがありません。')
      return
    }

    const printWindow = window.open('', '_blank')
    if (!printWindow) {
      ElMessage.error('ポップアップがブロックされました。ブラウザ設定を確認してください。')
      return
    }
    const html = buildProcessPrintHtml(allData, selectedDate)
    const doc = printWindow.document
    doc.open()
    doc.write(html)
    doc.close()

    const cleanup = () => {
      try {
        printWindow.close()
      } catch (err) {
        console.warn('印刷ウィンドウのクローズに失敗:', err)
      }
    }

    const handlePrint = () => {
      printWindow.focus()
      const printPromise = new Promise<void>((resolve) => {
        const listener = () => {
          printWindow.removeEventListener('afterprint', listener)
          resolve()
        }
        printWindow.addEventListener('afterprint', listener)
      })

      printWindow.print()
      printPromise
        .then(() => {
          setTimeout(cleanup, 300)
        })
        .catch(() => {
          setTimeout(cleanup, 300)
        })
    }

    if (printWindow.document.readyState === 'complete') {
      handlePrint()
    } else {
      printWindow.onload = handlePrint
    }
  } catch (error) {
    loadingMessage.close()
    console.error('印刷処理エラー:', error)
    ElMessage.error('印刷データの取得に失敗しました。')
  }
}

// 実績一括登録 - 登録
const handleSubmitBatchActual = async () => {
  // バリデーション
  if (!batchActualDate.value) {
    ElMessage.warning('日付を選択してください')
    return
  }

  const validRows = batchActualTableData.value.filter(
    (row) => row.product_cd && row.product_cd.trim() !== '',
  )

  if (validRows.length === 0) {
    ElMessage.warning('少なくとも1つの製品を選択してください')
    return
  }

  // 少なくとも1つの実績値があるかチェック（負数を許可）
  let hasActual = false
  validRows.forEach((row) => {
    if (
      (row.cuttingActual !== null && row.cuttingActual !== 0) ||
      (row.chamferingActual !== null && row.chamferingActual !== 0) ||
      (row.moldingActual !== null && row.moldingActual !== 0)
    ) {
      hasActual = true
    }
  })

  if (!hasActual) {
    ElMessage.warning('少なくとも1つの実績を入力してください')
    return
  }

  try {
    submittingBatchActual.value = true

    // 挿入するデータを構築
    const transactions: any[] = []
    const transactionTime = `${batchActualDate.value} 00:00:00`

    validRows.forEach((row) => {
      // 切断実績 (KT01) - 負数を許可
      if (row.cuttingActual !== null && row.cuttingActual !== 0) {
        transactions.push({
          product_cd: row.product_cd,
          process_cd: 'KT01',
          quantity: row.cuttingActual,
          transaction_time: transactionTime,
        })
      }
      // 面取実績 (KT02) - 負数を許可
      if (row.chamferingActual !== null && row.chamferingActual !== 0) {
        transactions.push({
          product_cd: row.product_cd,
          process_cd: 'KT02',
          quantity: row.chamferingActual,
          transaction_time: transactionTime,
        })
      }
      // 成型実績 (KT04) - 負数を許可
      if (row.moldingActual !== null && row.moldingActual !== 0) {
        transactions.push({
          product_cd: row.product_cd,
          process_cd: 'KT04',
          quantity: row.moldingActual,
          transaction_time: transactionTime,
        })
      }
    })

    if (transactions.length === 0) {
      ElMessage.warning('登録する実績データがありません')
      return
    }

    // APIを呼び出し
    const response: any = await request.post('/api/stock/batch-actual', {
      transactions,
    })

    ElMessage.success(`実績データを${transactions.length}件登録しました`)
    showBatchActualDialog.value = false

    // フォームをリセット
    handleResetBatchActual()

    // データをリフレッシュ
    setTimeout(() => {
      fetchData().catch((err) => {
        console.warn('データ更新後のリフレッシュに失敗:', err)
      })
    }, 500)
  } catch (error: any) {
    console.error('実績一括登録エラー:', error)
    const errorMessage =
      error?.response?.data?.message || error?.message || '実績データの登録に失敗しました'
    ElMessage.error(errorMessage)
  } finally {
    submittingBatchActual.value = false
  }
}

// 全部一括更新
const handleAllUpdate = async () => {
  try {
    showAllUpdateConfirmDialog.value = true
  } catch (error: any) {
    console.error('全部一括更新準備時にエラーが発生:', error)
    ElMessage.error('全部一括更新準備に失敗しました')
  }
}

const confirmAllUpdate = async () => {
  showAllUpdateConfirmDialog.value = false

  const updateSteps = [
    {
      name: '受注データ更新',
      api: () =>
        updateProductionSummarysFromOrderDaily({
          updateMode: 'all',
          days: 0,
          clearBeforeUpdate: false,
        }),
    },
    { name: '実績データ更新', api: () => updateProductionSummarysActual() },
    { name: '不良データ更新', api: () => updateProductionSummarysDefect() },
    { name: '廃棄データ更新', api: () => updateProductionSummarysScrap() },
    { name: '保留データ更新', api: () => updateProductionSummarysOnHold() },
    { name: '計画データ更新', api: () => updateProductionSummarysPlan() },
  ]

  try {
    updatingAll.value = true
    showProgressDialog.value = true
    progressPercentage.value = 0
    progressStatus.value = ''
    progressText.value = '全部一括更新を開始します...'

    const results: any[] = []
    const totalSteps = updateSteps.length + 1 // +1 for 在庫・推移更新

    // 最初の6つの更新ステップを実行
    for (let i = 0; i < updateSteps.length; i++) {
      const step = updateSteps[i]
      const stepProgress = Math.floor((i / totalSteps) * 100)
      progressPercentage.value = stepProgress
      progressText.value = `${step.name}を実行中... (${i + 1}/${totalSteps})`

      try {
        const response: any = await step.api()
        results.push({
          step: step.name,
          success: true,
          data: response?.data,
        })
        console.log(`${step.name}完了`)
      } catch (error: any) {
        console.error(`${step.name}エラー:`, error)
        results.push({
          step: step.name,
          success: false,
          error: error?.response?.data?.message || error.message,
        })
        // 後続ステップを続行、中断しない
      }

      // 短暂延迟，让用户看到进度
      await new Promise((resolve) => setTimeout(resolve, 300))
    }

    // 在庫・推移更新を実行（特別な処理が必要）
    progressPercentage.value = Math.floor((updateSteps.length / totalSteps) * 100)
    progressText.value = `在庫・推移更新を実行中... (${updateSteps.length + 1}/${totalSteps})`

    // 開始日を計算
    const startDate = calculateStartDate()
    if (startDate) {
      progressText.value = `開始日: ${startDate} を計算中...`
      await new Promise((resolve) => setTimeout(resolve, 300))

      // 開始日以降の計算フィールドをクリア
      progressText.value = '計算フィールドをクリア中...'
      try {
        await clearProductionSummarysCalculatedFields(startDate)
        console.log(`計算フィールドをクリアしました: 開始日: ${startDate}`)
      } catch (error: any) {
        console.warn('計算フィールドのクリアでエラーが発生しましたが、続行します:', error)
      }
    }

    // 更新在庫
    progressText.value = '在庫データを更新中...'
    try {
      const inventoryResponse: any = await updateProductionSummarysInventory(startDate)
      results.push({
        step: '在庫更新',
        success: true,
        data: inventoryResponse?.data,
      })
      console.log('在庫更新完了')
    } catch (error: any) {
      console.error('在庫更新エラー:', error)
      results.push({
        step: '在庫更新',
        success: false,
        error: error?.response?.data?.message || error.message,
      })
    }

    // 更新推移
    progressText.value = '推移データを更新中...'
    try {
      const trendResponse: any = await updateProductionSummarysTrend(startDate)
      results.push({
        step: '推移更新',
        success: true,
        data: trendResponse?.data,
      })
      console.log('推移更新完了')
    } catch (error: any) {
      console.error('推移更新エラー:', error)
      results.push({
        step: '推移更新',
        success: false,
        error: error?.response?.data?.message || error.message,
      })
    }

    // 完成
    progressPercentage.value = 100
    progressStatus.value = 'success'
    progressText.value = '全部一括更新が完了しました！'

    // 统计结果
    const successCount = results.filter((r) => r.success).length
    const failCount = results.filter((r) => !r.success).length

    let successMessage = `全部一括更新が完了しました！\n成功: ${successCount}件`
    if (failCount > 0) {
      successMessage += `\n失敗: ${failCount}件`
      const failedSteps = results
        .filter((r) => !r.success)
        .map((r) => r.step)
        .join('、')
      successMessage += `\n失敗した項目: ${failedSteps}`
    }

    setTimeout(() => {
      showProgressDialog.value = false
      if (failCount > 0) {
        ElMessage.warning(successMessage)
      } else {
        ElMessage.success(successMessage)
      }
      setTimeout(() => {
        fetchData().catch((err) => {
          console.warn('データ更新後のリフレッシュに失敗:', err)
        })
      }, 500)
    }, 1500)
  } catch (error: any) {
    console.error('全部一括更新時にエラーが発生:', error)
    progressPercentage.value = 100
    progressStatus.value = 'exception'
    progressText.value = '全部一括更新に失敗しました'

    setTimeout(() => {
      showProgressDialog.value = false
      ElMessage.error(error?.response?.data?.message || '全部一括更新に失敗しました')
    }, 2000)
  } finally {
    updatingAll.value = false
  }
}

// 在庫・推移更新
const handleInventoryTrendUpdate = async () => {
  try {
    showInventoryTrendUpdateConfirmDialog.value = true
  } catch (error: any) {
    console.error('在庫・推移更新準備時にエラーが発生:', error)
    ElMessage.error('在庫・推移更新準備に失敗しました')
  }
}

const confirmInventoryTrendUpdate = async () => {
  showInventoryTrendUpdateConfirmDialog.value = false

  const inventoryResult = {
    updated: 0,
    skipped: 0,
  }

  const trendResult = {
    updated: 0,
    skipped: 0,
  }

  // 计算开始日期（在try块外部定义，以便在成功消息中使用）
  let startDate: string | undefined = undefined
  let formattedStartDate: string = ''

  try {
    updatingInventoryTrend.value = true
    showProgressDialog.value = true
    progressPercentage.value = 0
    progressStatus.value = ''
    progressText.value = '開始日を計算中...'

    // 计算开始日期
    startDate = calculateStartDate()
    if (startDate) {
      const dateObj = new Date(startDate)
      formattedStartDate = `${dateObj.getFullYear()}/${String(dateObj.getMonth() + 1).padStart(2, '0')}/${String(dateObj.getDate()).padStart(2, '0')}`

      // 计算结束日期（开始日期+3个月）
      const endDateObj = new Date(dateObj)
      endDateObj.setMonth(endDateObj.getMonth() + 3)
      const formattedEndDate = `${endDateObj.getFullYear()}/${String(endDateObj.getMonth() + 1).padStart(2, '0')}/${String(endDateObj.getDate()).padStart(2, '0')}`

      console.log(`繰越データに基づく開始日: ${formattedStartDate} (${startDate})`)
      console.log(`計算期間: ${formattedStartDate} から ${formattedEndDate} まで（3ヶ月間）`)
      progressText.value = `開始日: ${formattedStartDate} から ${formattedEndDate} まで（3ヶ月間）計算します...`
    } else {
      console.log('繰越データが見つかりませんでした。全期間を計算します。')
      progressText.value = '繰越データが見つかりませんでした。全期間を計算します...'
    }

    await new Promise((resolve) => setTimeout(resolve, 800)) // 短暂延迟以显示开始日期

    // 构建步骤数组
    const steps: Array<{ label: string; action: () => Promise<void> }> = []

    // 如果有开始日期，先清空从开始日期之后的所有在庫、推移、実計推移字段
    if (startDate) {
      const clearStartDate = startDate // 保存到局部变量，确保类型正确
      steps.push({
        label: '計算フィールドをクリア中...',
        action: async () => {
          try {
            const response: any = await clearProductionSummarysCalculatedFields(clearStartDate)
            const cleared = response?.data?.cleared ?? response?.data?.data?.cleared ?? 0
            console.log(`計算フィールドをクリアしました: ${cleared}件`)
          } catch (error: any) {
            console.warn('計算フィールドのクリアでエラーが発生しましたが、続行します:', error)
            // クリア失敗は後続の計算に影響せず、続行
          }
        },
      })
    }

    // 在庫データ更新
    steps.push({
      label: '在庫データを更新中...',
      action: async () => {
        const response: any = await updateProductionSummarysInventory(startDate)
        const updated = response?.data?.updated ?? response?.data?.data?.updated ?? 0
        const skipped = response?.data?.skipped ?? response?.data?.data?.skipped ?? 0
        inventoryResult.updated = updated
        inventoryResult.skipped = skipped
      },
    })

    // 推移データ更新
    steps.push({
      label: '推移データを更新中...',
      action: async () => {
        const response: any = await updateProductionSummarysTrend(startDate)
        const updated = response?.data?.data?.updated ?? response?.data?.updated ?? 0
        const skipped = response?.data?.data?.skipped ?? response?.data?.skipped ?? 0
        trendResult.updated = updated
        trendResult.skipped = skipped
      },
    })

    const increment = 100 / steps.length

    for (let i = 0; i < steps.length; i++) {
      progressText.value = steps[i].label
      await steps[i].action()
      progressPercentage.value = Math.min(100, (i + 1) * increment)
    }

    progressStatus.value = 'success'
    progressText.value = '在庫・推移データの更新が完了しました！'

    setTimeout(() => {
      showProgressDialog.value = false

      let successMessage = '在庫・推移データの更新が成功しました！'
      if (startDate && formattedStartDate) {
        // 计算结束日期（开始日期+3个月）
        const dateObj = new Date(startDate)
        const endDateObj = new Date(dateObj)
        endDateObj.setMonth(endDateObj.getMonth() + 3)
        const formattedEndDate = `${endDateObj.getFullYear()}/${String(endDateObj.getMonth() + 1).padStart(2, '0')}/${String(endDateObj.getDate()).padStart(2, '0')}`
        successMessage += `\n計算期間: ${formattedStartDate} ～ ${formattedEndDate}（3ヶ月間）`
      }
      successMessage += `\n在庫: 更新 ${inventoryResult.updated}件`
      if (inventoryResult.skipped > 0) {
        successMessage += ` / スキップ ${inventoryResult.skipped}件`
      }
      successMessage += `\n推移: 更新 ${trendResult.updated}件`
      if (trendResult.skipped > 0) {
        successMessage += ` / スキップ ${trendResult.skipped}件`
      }

      ElMessage.success(successMessage)
      setTimeout(() => {
        fetchData().catch((err) => {
          console.warn('データ更新後のリフレッシュに失敗:', err)
        })
      }, 500)
    }, 1500)
  } catch (error: any) {
    console.error('在庫・推移更新時にエラーが発生:', error)
    progressStatus.value = 'exception'

    let errorMessage = '在庫・推移データ更新に失敗しました'
    if (error?.code === 'ECONNABORTED' || error?.message?.includes('timeout')) {
      errorMessage = 'リクエストがタイムアウトしました。しばらく待ってから再度お試しください。'
    } else if (error?.response?.data?.message) {
      errorMessage = error.response.data.message
    } else if (error?.message) {
      errorMessage = error.message
    }

    progressText.value = errorMessage
    setTimeout(() => {
      showProgressDialog.value = false
      ElMessage.error(errorMessage)
    }, 2000)
  } finally {
    updatingInventoryTrend.value = false
  }
}

// タブ切り替え時に列を更新
watch(activeTableTab, (newTab) => {
  // 受注タブの場合、日付、製品CD、製品名、受注数、内示数のみ表示
  if (newTab === 'custom') {
    const orderColumns = [
      'date',
      'product_cd',
      'product_name',
      'order_quantity',
      'forecast_quantity',
    ]
    columnKeys.forEach((key) => {
      if (orderColumns.includes(key)) {
        visibleColumns.value[key] = true
      } else {
        visibleColumns.value[key] = false
      }
    })
    return
  }

  const suffix = fieldTypeMapping[newTab]

  // 基本列は常に表示
  const baseColumns = ['date', 'product_cd', 'product_name']

  columnKeys.forEach((key) => {
    if (baseColumns.includes(key)) {
      visibleColumns.value[key] = true
    } else {
      // フィールドタイプに関連する列のみ表示
      const isRelated = suffix ? key.endsWith(suffix) : false
      visibleColumns.value[key] = isRelated
    }
  })
})

// 初期化
onMounted(() => {
  // 保存された列設定を復元
  try {
    const savedColumns = localStorage.getItem('productionSummaryMgmtColumns')
    if (savedColumns) {
      visibleColumns.value = { ...defaultVisibleColumns, ...JSON.parse(savedColumns) }
    }
  } catch {
    // ignore
  }

  fetchProductList()
  fetchData()
})
</script>

<style scoped>
.production-summary-management {
  min-height: 100vh;
  padding: 0.4rem;
  background: linear-gradient(135deg, #e0e7ff 0%, #f3f4f6 50%, #e0f2fe 100%);
  position: relative;
}

.production-summary-management::before,
.production-summary-management::after {
  content: '';
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.25;
  pointer-events: none;
  z-index: 0;
}

.production-summary-management::before {
  width: 320px;
  height: 320px;
  background: linear-gradient(135deg, #818cf8, #6366f1);
  top: -100px;
  right: -80px;
}

.production-summary-management::after {
  width: 280px;
  height: 280px;
  background: linear-gradient(135deg, #60a5fa, #3b82f6);
  bottom: -90px;
  left: -60px;
}

/* ヘッダー */
.page-header {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  padding: 0.5rem 1rem;
  margin-bottom: 0.4rem;
  border-radius: 0.75rem;
  box-shadow:
    0 8px 24px rgba(99, 102, 241, 0.12),
    0 2px 6px rgba(0, 0, 0, 0.04);
  position: relative;
  z-index: 1;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 100%;
  margin: 0 auto;
  gap: 1rem;
  flex-wrap: wrap;
}

.header-left {
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 0;
}

.header-right {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.page-title-wrapper {
  display: flex;
  align-items: center;
}

.page-title {
  font-size: 1.25rem;
  font-weight: 800;
  background: linear-gradient(135deg, #4f46e5 0%, #6366f1 50%, #818cf8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  letter-spacing: -0.02em;
  white-space: nowrap;
}

.title-icon {
  font-size: 1.4rem;
  color: #6366f1;
  filter: drop-shadow(0 2px 4px rgba(99, 102, 241, 0.3));
}

.page-meta-row {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
}

.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
  border: 1px solid rgba(99, 102, 241, 0.2);
  font-size: 0.7rem;
  box-shadow: 0 1px 3px rgba(99, 102, 241, 0.08);
}

.meta-label {
  color: #6366f1;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.meta-value {
  color: #1e293b;
  font-weight: 700;
}

/* メインコンテンツ */
.main-content {
  max-width: 100%;
  margin: 0 auto;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  position: relative;
  z-index: 1;
}

/* テーブルカード */
.table-card {
  border-radius: 0.75rem;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow:
    0 10px 40px rgba(99, 102, 241, 0.15),
    0 4px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  position: relative;
  background: linear-gradient(135deg, #ffffff 0%, #fafbff 100%);
}

.table-card :deep(.el-card__header) {
  padding: 0.6rem 1rem 0.4rem;
  border-bottom: 2px solid transparent;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-image: linear-gradient(90deg, #6366f1, #818cf8, #a5b4fc) 1;
}

.table-card :deep(.el-card__body) {
  padding: 0 0.75rem 0.75rem;
  background: #ffffff;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 700;
  color: #0f172a;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.table-header-left {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.table-icon {
  font-size: 1.1rem;
  color: #6366f1;
  filter: drop-shadow(0 1px 2px rgba(99, 102, 241, 0.3));
}

.table-title {
  font-size: 1rem;
  font-weight: 700;
}

.record-count {
  margin-left: 0.5rem;
}

.table-actions {
  display: flex;
  gap: 0.5rem;
}

/* フィルター */
/* フィルタ領域 - 现代紧凑设计 */
.filter-section {
  margin-top: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: linear-gradient(135deg, #fafbfc 0%, #f5f7fa 100%);
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  position: relative;
  overflow: hidden;
}

.filter-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%);
  opacity: 0.6;
  animation: filterGradient 8s ease infinite;
  background-size: 200% 100%;
}

@keyframes filterGradient {
  0%,
  100% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
}

.filter-item {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: #ffffff;
  padding: 0.35rem 0.6rem;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  height: 28px;
}

.filter-item::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.02) 0%, rgba(139, 92, 246, 0.02) 100%);
  opacity: 0;
  transition: opacity 0.2s ease;
  pointer-events: none;
}

.filter-item:hover::after {
  opacity: 1;
}

.filter-item:hover {
  border-color: #a5b4fc;
  box-shadow: 0 2px 6px rgba(99, 102, 241, 0.1);
  transform: translateY(-1px);
}

.date-filter-item {
  flex: 1;
  min-width: 0;
  padding: 0.35rem 0.65rem;
  height: auto;
}

.filter-label {
  font-size: 0.7rem;
  font-weight: 700;
  color: #64748b;
  white-space: nowrap;
  letter-spacing: 0.01em;
  line-height: 1;
  display: flex;
  align-items: center;
  gap: 0.25rem;
  position: relative;
  z-index: 1;
  min-width: fit-content;
}

.date-inline-controls {
  display: flex;
  gap: 0.4rem;
  align-items: center;
  flex: 1;
}

.date-quick-buttons {
  display: flex;
  gap: 0.2rem;
  background: #f8fafc;
  padding: 0.2rem;
  border-radius: 5px;
  border: 1px solid #e2e8f0;
}

.date-quick-buttons :deep(.el-button) {
  height: 24px;
  padding: 0 0.6rem;
  font-size: 0.65rem;
  border-radius: 4px;
  font-weight: 600;
  border: 1px solid transparent;
  background: transparent;
  color: #475569;
  transition: all 0.15s ease;
  line-height: 1;
}

.date-quick-buttons :deep(.el-button:hover) {
  background: #ffffff;
  border-color: #cbd5e1;
  color: #1e293b;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.date-quick-buttons :deep(.el-button.is-plain) {
  background: transparent;
  border: 1px solid transparent;
}

.date-quick-buttons :deep(.el-button--primary.is-plain) {
  background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
  border: none;
  color: #ffffff;
  font-weight: 700;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
}

.date-quick-buttons :deep(.el-button--primary.is-plain:hover) {
  background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
  transform: translateY(-1px);
  box-shadow: 0 3px 6px rgba(59, 130, 246, 0.3);
}

.filter-select {
  width: 180px;
}

.filter-select :deep(.el-input__wrapper) {
  box-shadow: none !important;
  border: none !important;
  background: transparent !important;
  padding: 0 !important;
  height: auto !important;
}

.filter-select :deep(.el-input__inner) {
  font-size: 0.7rem;
  font-weight: 500;
  color: #1e293b;
  transition: all 0.2s ease;
  height: auto !important;
  line-height: 1.2;
}

.filter-select :deep(.el-input__inner:focus) {
  color: #0f172a;
  font-weight: 600;
}

.keyword-filter-item {
  flex: 0 1 auto;
}

.keyword-filter-input {
  width: 180px;
}

.keyword-filter-input :deep(.el-input__wrapper) {
  box-shadow: none !important;
  border: none !important;
  background: transparent !important;
  padding: 0 !important;
  height: auto !important;
}

.keyword-filter-input :deep(.el-input__inner) {
  font-size: 0.7rem;
  font-weight: 500;
  color: #1e293b;
  transition: all 0.2s ease;
  height: auto !important;
  line-height: 1.2;
}

.keyword-filter-input :deep(.el-input__inner:focus) {
  color: #0f172a;
  font-weight: 600;
}

.filter-date-picker {
  flex: 1;
}

.filter-date-picker :deep(.el-input__wrapper) {
  box-shadow: none !important;
  border: none !important;
  background: transparent !important;
  padding: 0 !important;
}

.filter-date-picker :deep(.el-input__inner) {
  font-size: 0.75rem;
  font-weight: 500;
  color: #1e293b;
  transition: all 0.2s ease;
}

.filter-date-picker :deep(.el-input__inner:focus) {
  color: #0f172a;
  font-weight: 600;
}

.filter-date-picker :deep(.el-range-separator) {
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 600;
}

.filter-date-picker :deep(.el-input__prefix) {
  color: #6366f1;
}

.filter-select :deep(.el-input__prefix),
.keyword-filter-input :deep(.el-input__prefix) {
  color: #6366f1;
  font-size: 0.875rem;
}

.filter-select :deep(.el-input__suffix),
.keyword-filter-input :deep(.el-input__suffix) {
  color: #94a3b8;
}

.filter-select :deep(.el-input__inner::placeholder),
.keyword-filter-input :deep(.el-input__inner::placeholder),
.filter-date-picker :deep(.el-input__inner::placeholder) {
  color: #94a3b8;
  font-weight: 400;
  font-size: 0.7rem;
}

.reset-filter-item {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
}

.reset-filter-item:hover {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}

.reset-filter-btn {
  height: 32px !important;
  padding: 0 1rem !important;
  font-size: 0.7rem !important;
  font-weight: 600 !important;
  border-radius: 0.5rem !important;
  background: linear-gradient(135deg, #ef4444 0%, #f87171 100%) !important;
  border: none !important;
  color: #fff !important;
  transition: all 0.2s ease !important;
  box-shadow: 0 2px 4px rgba(239, 68, 68, 0.2) !important;
}

.reset-filter-btn:hover {
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 8px rgba(239, 68, 68, 0.3) !important;
  background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%) !important;
}

/* タブ */
.table-tabs-container {
  margin-bottom: 0.5rem;
  padding: 0.3rem;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(248, 250, 252, 0.95) 100%);
  backdrop-filter: blur(10px);
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow:
    0 4px 16px rgba(99, 102, 241, 0.08),
    0 2px 4px rgba(0, 0, 0, 0.04);
}

.summary-table-tabs :deep(.el-tabs__header) {
  margin-bottom: 0;
  background: transparent;
  border: none;
}

.summary-table-tabs :deep(.el-tabs__nav) {
  border: none;
  display: flex;
  gap: 0.35rem;
}

.summary-table-tabs :deep(.el-tabs__item) {
  padding: 6px 12px;
  height: auto;
  border: 1px solid rgba(226, 232, 240, 0.8) !important;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border-radius: 8px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
}

.summary-table-tabs :deep(.el-tabs__item::before) {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(139, 92, 246, 0.05) 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

.summary-table-tabs :deep(.el-tabs__item:hover) {
  border-color: rgba(99, 102, 241, 0.3) !important;
  transform: translateY(-2px);
  box-shadow:
    0 6px 16px rgba(99, 102, 241, 0.15),
    0 2px 4px rgba(0, 0, 0, 0.06);
}

.summary-table-tabs :deep(.el-tabs__item:hover::before) {
  opacity: 1;
}

.summary-table-tabs :deep(.el-tabs__item.is-active) {
  border: 1px solid rgba(99, 102, 241, 0.4) !important;
  background: linear-gradient(135deg, #ffffff 0%, #faf5ff 100%);
  box-shadow:
    0 8px 20px rgba(99, 102, 241, 0.2),
    0 4px 8px rgba(139, 92, 246, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
  transform: translateY(-3px);
}

.summary-table-tabs :deep(.el-tabs__item.is-active::before) {
  opacity: 1;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(139, 92, 246, 0.08) 100%);
}

.summary-table-tabs :deep(.el-tabs__item.is-active::after) {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 60%;
  height: 3px;
  background: linear-gradient(90deg, transparent, #6366f1, transparent);
  border-radius: 2px 2px 0 0;
  box-shadow: 0 -2px 8px rgba(99, 102, 241, 0.4);
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  position: relative;
  z-index: 1;
}

.tab-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 6px;
  font-size: 0.75rem;
  color: #fff;
  box-shadow:
    0 4px 8px rgba(0, 0, 0, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.tab-icon::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transform: rotate(45deg);
  transition: all 0.6s ease;
}

.summary-table-tabs :deep(.el-tabs__item:hover) .tab-icon {
  transform: scale(1.1) rotate(5deg);
  box-shadow:
    0 6px 12px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

.summary-table-tabs :deep(.el-tabs__item:hover) .tab-icon::before {
  left: 150%;
}

.summary-table-tabs :deep(.el-tabs__item.is-active) .tab-icon {
  transform: scale(1.15);
  box-shadow:
    0 8px 16px rgba(0, 0, 0, 0.25),
    inset 0 2px 0 rgba(255, 255, 255, 0.3);
  animation: pulse-icon 2s ease-in-out infinite;
}

@keyframes pulse-icon {
  0%,
  100% {
    box-shadow:
      0 8px 16px rgba(0, 0, 0, 0.25),
      inset 0 2px 0 rgba(255, 255, 255, 0.3);
  }
  50% {
    box-shadow:
      0 8px 20px rgba(0, 0, 0, 0.3),
      inset 0 2px 0 rgba(255, 255, 255, 0.4);
  }
}

.tab-text-group {
  display: flex;
  flex-direction: column;
}

.tab-text {
  font-weight: 600;
  font-size: 0.8rem;
  color: #475569;
  transition: all 0.3s ease;
  letter-spacing: 0.01em;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.summary-table-tabs :deep(.el-tabs__item:hover) .tab-text {
  color: #1e293b;
  transform: translateX(2px);
}

.summary-table-tabs :deep(.el-tabs__item.is-active) .tab-text {
  color: #0f172a;
  font-weight: 700;
  text-shadow: 0 1px 3px rgba(99, 102, 241, 0.2);
}

/* テーブル */
.modern-table {
  font-size: 0.7rem;
}

.modern-table :deep(.el-table__header-wrapper th) {
  white-space: nowrap;
}

.modern-table :deep(.el-table__header-wrapper .cell) {
  white-space: nowrap;
  overflow: visible;
  text-overflow: clip;
  font-size: 0.6rem;
  min-width: 4.5em;
}

.modern-table :deep(.el-table__row) {
  transition: background-color 0.2s;
}

.modern-table :deep(.el-table__row:hover) {
  background-color: #f0f9ff !important;
}

.date-cell {
  font-weight: 600;
  color: #0f172a;
}

.product-name-cell {
  font-weight: 600;
  color: #1e293b;
}

.number-cell {
  font-weight: 600;
}

.number-cell.negative {
  color: #dc2626;
}

.number-cell.positive {
  color: #047857;
}

.date-text {
  color: #475569;
}

.text-cell {
  color: #374151;
}

/* ページネーション */
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  padding: 1rem 0 0;
}

/* 列設定ダイアログ */
.column-settings-content {
  max-height: 60vh;
  overflow-y: auto;
}

.column-settings-actions {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #e5e7eb;
}

.column-groups {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.column-group {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 0.75rem;
}

.group-header {
  font-weight: 700;
  margin-bottom: 0.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #f3f4f6;
}

.group-columns {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 0.25rem;
}

.column-checkbox {
  font-size: 0.8rem;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

/* データ操作ドロップダウンボタン */
.data-actions-dropdown {
  margin-right: 0.3rem;
  display: inline-flex;
  align-items: center;
}

/* データ操作按钮颜色样式 */
.data-actions-dropdown :deep(.el-button) {
  background: linear-gradient(135deg, #6366f1 0%, #818cf8 100%);
  border-color: rgba(99, 102, 241, 0.3) !important;
  color: #fff;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.25) !important;
}

.data-actions-dropdown :deep(.el-button:hover:not(:disabled)) {
  background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%);
  border-color: #4f46e5 !important;
  box-shadow: 0 6px 16px rgba(99, 102, 241, 0.4) !important;
}

.data-actions-dropdown :deep(.el-button .el-icon--right) {
  margin-left: 0.3rem;
  margin-right: 0;
  font-size: 0.7rem;
}

/* ドロップダウンメニュー */
.data-actions-dropdown :deep(.el-dropdown-menu) {
  border-radius: 10px;
  box-shadow:
    0 8px 24px rgba(0, 0, 0, 0.12),
    0 2px 8px rgba(0, 0, 0, 0.08);
  padding: 6px 0;
  min-width: 220px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  margin-top: 4px;
}

/* ドロップダウンメニューアイテム */
.data-actions-dropdown :deep(.el-dropdown-menu__item) {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  transition: all 0.2s ease;
  font-size: 13px;
  font-weight: 500;
  color: #374151;
  position: relative;
}

.data-actions-dropdown :deep(.el-dropdown-menu__item:first-child) {
  border-top-left-radius: 10px;
  border-top-right-radius: 10px;
}

.data-actions-dropdown :deep(.el-dropdown-menu__item:last-child) {
  border-bottom-left-radius: 10px;
  border-bottom-right-radius: 10px;
}

.data-actions-dropdown :deep(.el-dropdown-menu__item:hover:not(.is-disabled)) {
  background-color: #f9fafb;
}

.data-actions-dropdown :deep(.generate-item:hover:not(.is-disabled)) {
  background: linear-gradient(90deg, #d1fae5 0%, #ecfdf5 100%);
  color: #047857;
}

.data-actions-dropdown :deep(.carry-over-item:hover:not(.is-disabled)) {
  background: linear-gradient(90deg, #fef3c7 0%, #fffbeb 100%);
  color: #b45309;
}

.data-actions-dropdown :deep(.order-item:hover:not(.is-disabled)) {
  background: linear-gradient(90deg, #dbeafe 0%, #eff6ff 100%);
  color: #1e40af;
}

.data-actions-dropdown :deep(.actual-item:hover:not(.is-disabled)) {
  background: linear-gradient(90deg, #dcfce7 0%, #f0fdf4 100%);
  color: #166534;
}

.data-actions-dropdown :deep(.defect-item:hover:not(.is-disabled)) {
  background: linear-gradient(90deg, #fee2e2 0%, #fef2f2 100%);
  color: #991b1b;
}

.data-actions-dropdown :deep(.scrap-item:hover:not(.is-disabled)) {
  background: linear-gradient(90deg, #fef3c7 0%, #fffbeb 100%);
  color: #92400e;
}

.data-actions-dropdown :deep(.onhold-item:hover:not(.is-disabled)) {
  background: linear-gradient(90deg, #e0e7ff 0%, #eef2ff 100%);
  color: #3730a3;
}

.data-actions-dropdown :deep(.production-dates-item:hover:not(.is-disabled)) {
  background: linear-gradient(90deg, #fef3c7 0%, #fffbeb 100%);
  color: #92400e;
}

.data-actions-dropdown :deep(.plan-item:hover:not(.is-disabled)) {
  background: linear-gradient(90deg, #dbeafe 0%, #eff6ff 100%);
  color: #1e40af;
}

.data-actions-dropdown :deep(.inventory-trend-item:hover:not(.is-disabled)) {
  background: linear-gradient(90deg, #e0e7ff 0%, #eef2ff 100%);
  color: #4338ca;
}

.data-actions-dropdown :deep(.batch-actual-item:hover:not(.is-disabled)) {
  background: linear-gradient(90deg, #dbeafe 0%, #eff6ff 100%);
  color: #1e40af;
}

.data-actions-dropdown :deep(.initial-stock-item:hover:not(.is-disabled)) {
  background: linear-gradient(90deg, #fef3c7 0%, #fffbeb 100%);
  color: #b45309;
}

.data-actions-dropdown :deep(.batch-initial-stock-item:hover:not(.is-disabled)) {
  background: linear-gradient(90deg, #d1fae5 0%, #ecfdf5 100%);
  color: #047857;
}

.data-actions-dropdown :deep(.all-update-item:hover:not(.is-disabled)) {
  background: linear-gradient(90deg, #fef3c7 0%, #fde68a 100%);
  color: #92400e;
  font-weight: 600;
}

/* 在庫取引ログ入力ダイアログ */
.transaction-input-dialog :deep(.el-dialog) {
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
}

.transaction-input-dialog :deep(.el-dialog__header) {
  padding: 1.5rem 1.5rem 1rem;
  border-bottom: 1px solid #f0f0f0;
}

.transaction-input-dialog :deep(.el-dialog__title) {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
}

.transaction-input-dialog :deep(.el-dialog__body) {
  padding: 1.5rem;
}

.transaction-input-info {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.info-label {
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.info-value {
  font-size: 0.875rem;
  color: #1f2937;
  font-weight: 600;
}

.transaction-form-container {
  margin-top: 1rem;
}

.transaction-form {
  width: 100%;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin-top: 1rem;
}

.form-item-card {
  padding: 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.form-item-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #667eea, #764ba2);
  transform: scaleX(0);
  transition: transform 0.3s ease;
}

.form-item-card:focus-within::before {
  transform: scaleX(1);
}

.form-item-card:hover {
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
}

.form-item-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.form-item-icon {
  font-size: 1.25rem;
}

.form-item-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
}

.input-compact {
  width: 100%;
}

.input-compact :deep(.el-input__wrapper) {
  border-radius: 6px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.input-compact :deep(.el-input__wrapper:hover) {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.input-compact :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
}

.dialog-footer-compact {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

/* 工程別カラー */
.actual-card {
  border-color: #10b981;
}

.actual-card:hover {
  border-color: #059669;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.15);
}

.defect-card {
  border-color: #f59e0b;
}

.defect-card:hover {
  border-color: #d97706;
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.15);
}

.scrap-card {
  border-color: #ef4444;
}

.scrap-card:hover {
  border-color: #dc2626;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.15);
}

.onhold-card {
  border-color: #6366f1;
}

.onhold-card:hover {
  border-color: #4f46e5;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15);
}

.inbound-card {
  border-color: #3b82f6;
}

.inbound-card:hover {
  border-color: #2563eb;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
}

.outbound-card {
  border-color: #8b5cf6;
}

.outbound-card:hover {
  border-color: #7c3aed;
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.15);
}

.data-actions-dropdown :deep(.el-dropdown-menu__item.is-disabled) {
  opacity: 0.5;
  cursor: not-allowed;
  background-color: transparent !important;
}

.data-actions-dropdown :deep(.el-dropdown-menu__item .el-icon) {
  font-size: 16px;
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.data-actions-dropdown :deep(.el-dropdown-menu__item span) {
  flex: 1;
  white-space: nowrap;
}

/* 受注データ更新モード選択ダイアログ */
.update-mode-dialog :deep(.el-dialog) {
  border-radius: 12px;
}

.update-mode-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #3b82f6, #60a5fa);
  color: #fff;
  padding: 1rem 1.5rem;
}

.update-mode-dialog :deep(.el-dialog__title) {
  color: #fff;
  font-weight: 700;
}

.update-mode-content {
  padding: 1rem 0;
}

.mode-options {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.mode-option {
  padding: 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #fff;
}

.mode-option:hover {
  border-color: #3b82f6;
  background: #f0f9ff;
}

.mode-option.active {
  border-color: #3b82f6;
  background: #eff6ff;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
}

.mode-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.mode-icon {
  font-size: 1.2rem;
  color: #3b82f6;
}

.mode-title {
  font-weight: 700;
  font-size: 1rem;
  color: #1f2937;
}

.mode-description {
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0.5rem 0 0 0;
  line-height: 1.5;
}

.days-input-wrapper {
  margin-top: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.days-label {
  font-weight: 600;
  color: #374151;
  font-size: 0.875rem;
}

.days-input {
  width: 120px;
}

/* データ生成確認ダイアログ */
.generate-confirm-dialog :deep(.el-dialog) {
  border-radius: 12px;
  overflow: hidden;
}

.generate-confirm-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #10b981, #34d399);
  color: #fff;
  padding: 1rem 1.5rem;
}

.generate-confirm-dialog :deep(.el-dialog__title) {
  color: #fff;
  font-weight: 700;
  font-size: 1.1rem;
}

.generate-confirm-dialog :deep(.el-dialog__body) {
  padding: 1.5rem;
}

.generate-confirm-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.confirm-icon-wrapper {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #10b981, #34d399);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.5rem;
}

.confirm-icon {
  font-size: 2rem;
  color: #fff;
}

.confirm-info {
  text-align: center;
  width: 100%;
}

.confirm-title {
  font-size: 1.2rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 1rem 0;
}

.confirm-details {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  text-align: left;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid #e5e7eb;
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-label {
  font-weight: 600;
  color: #6b7280;
  font-size: 0.9rem;
}

.detail-value {
  color: #1f2937;
  font-weight: 500;
  font-size: 0.9rem;
}

.detail-value.highlight {
  color: #10b981;
  font-weight: 700;
}

/* データ生成進度ダイアログ */
.progress-dialog :deep(.el-dialog) {
  border-radius: 12px;
}

.progress-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
  padding: 1rem 1.5rem;
}

.progress-dialog :deep(.el-dialog__title) {
  color: #fff;
  font-weight: 700;
}

.progress-content {
  padding: 1.5rem;
}

.progress-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.progress-icon {
  font-size: 1.5rem;
  color: #6366f1;
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.progress-text {
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
}

.progress-bar {
  margin-bottom: 1.5rem;
}

.progress-details {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
  margin-top: 1rem;
}

.progress-detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  background: #f9fafb;
  border-radius: 6px;
}

.progress-detail-item .detail-label {
  font-size: 0.85rem;
  color: #6b7280;
  font-weight: 600;
}

.progress-detail-item .detail-value {
  font-size: 0.9rem;
  color: #1f2937;
  font-weight: 700;
}

.success-text {
  color: #10b981;
}

.warning-text {
  color: #f59e0b;
}

/* 统一按钮样式 - 所有操作按钮 */
.modern-btn :deep(.el-button),
.data-actions-dropdown :deep(.el-button) {
  font-weight: 700 !important;
  font-size: 0.75rem !important;
  height: 28px !important;
  padding: 0.4rem 0.85rem !important;
  border-radius: 0.5rem !important;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 0.3rem !important;
  border: 1px solid transparent !important;
  line-height: 1 !important;
  margin: 0 !important;
}

.modern-btn :deep(.el-icon),
.data-actions-dropdown :deep(.el-button .el-icon) {
  font-size: 0.875rem !important;
  width: 0.875rem !important;
  height: 0.875rem !important;
  margin: 0 !important;
}

.modern-btn :deep(span),
.data-actions-dropdown :deep(.el-button span) {
  font-size: 0.75rem !important;
  line-height: 1 !important;
}

.modern-btn :deep(.el-button:hover:not(:disabled)),
.data-actions-dropdown :deep(.el-button:hover:not(:disabled)) {
  transform: translateY(-2px) !important;
}

.modern-btn :deep(.el-button:disabled),
.data-actions-dropdown :deep(.el-button:disabled) {
  opacity: 0.6 !important;
  cursor: not-allowed !important;
  transform: none !important;
}

/* 再取得按钮 */
.refresh-btn,
.refresh-btn :deep(.el-button) {
  background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
  border-color: #3b82f6 !important;
  color: #fff;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.25) !important;
}

.refresh-btn:hover:not(:disabled),
.refresh-btn :deep(.el-button:hover:not(:disabled)) {
  background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
  border-color: #2563eb !important;
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4) !important;
}

/* 印刷按钮 */
.print-btn,
.print-btn :deep(.el-button) {
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
  border-color: #10b981 !important;
  color: #fff;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.25) !important;
}

.print-btn:hover:not(:disabled),
.print-btn :deep(.el-button:hover:not(:disabled)) {
  background: linear-gradient(135deg, #059669 0%, #10b981 100%);
  border-color: #059669 !important;
  box-shadow: 0 6px 16px rgba(16, 185, 129, 0.4) !important;
}

/* 列設定按钮 */
.settings-btn,
.settings-btn :deep(.el-button) {
  background: linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%);
  border-color: #f59e0b !important;
  color: #fff;
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.25) !important;
}

.settings-btn:hover:not(:disabled),
.settings-btn :deep(.el-button:hover:not(:disabled)) {
  background: linear-gradient(135deg, #d97706 0%, #f59e0b 100%);
  border-color: #d97706 !important;
  box-shadow: 0 6px 16px rgba(245, 158, 11, 0.4) !important;
}

/* 実績一括登録ボタン */
.batch-actual-btn,
.batch-actual-btn :deep(.el-button) {
  background: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%);
  border-color: #8b5cf6 !important;
  color: #fff;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.25) !important;
}

.batch-actual-btn:hover:not(:disabled),
.batch-actual-btn :deep(.el-button:hover:not(:disabled)) {
  background: linear-gradient(135deg, #7c3aed 0%, #8b5cf6 100%);
  border-color: #7c3aed !important;
  box-shadow: 0 6px 16px rgba(139, 92, 246, 0.4) !important;
}

/* 実績一括登録ダイアログ */
.batch-actual-dialog :deep(.el-dialog) {
  border-radius: 0.75rem;
  box-shadow: 0 12px 48px rgba(139, 92, 246, 0.18);
}

.batch-actual-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%);
  color: #fff;
  padding: 1rem 1.5rem;
  border-radius: 0.75rem 0.75rem 0 0;
}

.batch-actual-dialog :deep(.el-dialog__title) {
  color: #fff;
  font-weight: 700;
  font-size: 1.1rem;
}

.batch-actual-dialog :deep(.el-dialog__body) {
  padding: 1.5rem;
}

.batch-actual-content {
  padding: 0.5rem 0;
}

.batch-actual-date-picker {
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.batch-actual-date-picker :deep(.el-form-item) {
  margin-bottom: 0;
}

.batch-actual-date-picker :deep(.el-form-item__label) {
  font-weight: 600;
  color: #374151;
  margin-right: 0.5rem;
}

.batch-actual-table {
  margin-top: 1rem;
}

.batch-actual-table :deep(.el-table__header-wrapper) {
  background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
}

.batch-actual-table :deep(th) {
  background: transparent !important;
  color: #1e293b;
  font-weight: 700;
  font-size: 0.8rem;
  text-align: center;
}

.batch-actual-table :deep(.el-table__row) {
  transition: background-color 0.2s;
}

.batch-actual-table :deep(.el-table__row:hover) {
  background-color: #f8fafc !important;
}

.batch-actual-table :deep(.el-input-number) {
  width: 100%;
}

.batch-actual-table :deep(.el-input-number .el-input__inner) {
  text-align: center;
}

/* データ操作下拉按钮 */
.data-actions-dropdown :deep(.el-button) {
  background: linear-gradient(135deg, #6366f1 0%, #818cf8 100%);
  border-color: rgba(99, 102, 241, 0.3);
  color: #fff;
}

.data-actions-dropdown :deep(.el-button:hover:not(:disabled)) {
  background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%);
  border-color: #4f46e5;
}

/* 响应式设计 - フィルタ領域 */
@media (max-width: 1400px) {
  .filter-row {
    gap: 0.625rem;
  }

  .date-filter-item {
    min-width: 100%;
  }

  .filter-select {
    width: 180px;
  }

  .keyword-filter-input {
    width: 180px;
  }
}

@media (max-width: 1200px) {
  .filter-section {
    padding: 0.75rem 0.875rem;
  }

  .filter-item {
    padding: 0.4rem 0.625rem;
  }

  .date-filter-item {
    padding: 0.4rem 0.75rem;
  }
}

@media (max-width: 768px) {
  .filter-section {
    padding: 0.625rem 0.75rem;
  }

  .filter-row {
    gap: 0.5rem;
  }

  .filter-item {
    flex: 1 1 100%;
    min-width: 100%;
  }

  .date-inline-controls {
    flex-direction: column;
    align-items: stretch;
    gap: 0.5rem;
  }

  .filter-select,
  .keyword-filter-input {
    width: 100%;
  }

  .date-quick-buttons {
    justify-content: stretch;
  }

  .date-quick-buttons :deep(.el-button) {
    flex: 1;
  }
}

/* 印刷用スタイル */
@media print {
  .page-header,
  .filter-section,
  .table-actions,
  .table-tabs-container,
  .pagination-wrapper {
    display: none !important;
  }

  .production-summary-management {
    padding: 0;
    background: #fff;
  }

  .production-summary-management::before,
  .production-summary-management::after {
    display: none !important;
  }

  .table-card {
    box-shadow: none;
    border: none;
  }
}

/* 繰越編集ダイアログ */
.carry-over-edit-dialog :deep(.el-dialog) {
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(99, 102, 241, 0.15);
}

.carry-over-edit-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: #fff;
  padding: 1rem 1.5rem;
  border-radius: 12px 12px 0 0;
}

.carry-over-edit-dialog :deep(.el-dialog__title) {
  color: #fff;
  font-weight: 700;
  font-size: 1.1rem;
}

.carry-over-edit-content {
  padding: 1rem 0;
}

.edit-info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.edit-info-grid .info-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.edit-info-grid .info-item:nth-child(2) {
  grid-column: span 2;
}

.edit-info-grid .info-label {
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 600;
}

.edit-info-grid .info-value {
  font-size: 0.875rem;
  color: #1f2937;
  font-weight: 700;
}

.edit-form {
  margin-top: 1rem;
}

.carry-over-edit-dialog :deep(.el-input-number) {
  width: 100%;
}

.carry-over-edit-dialog :deep(.el-input-number .el-input__inner) {
  text-align: left;
  font-weight: 600;
  font-size: 1rem;
}

/* 初期在庫管理ダイアログ样式 */
.initial-stock-dialog {
  :deep(.el-dialog) {
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 25px 80px rgba(0, 0, 0, 0.15);
    max-width: 95vw;
  }

  :deep(.el-dialog__header) {
    padding: 6px 10px 8px;
    border-bottom: none;
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    margin: 0;
    position: relative;
  }

  :deep(.el-dialog__header::after) {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  }

  :deep(.el-dialog__title) {
    color: #ffffff;
    font-weight: 700;
    font-size: 15px;
    letter-spacing: 0.5px;
    text-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  }

  :deep(.el-dialog__headerbtn) {
    top: 6px;
    right: 10px;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.15);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  :deep(.el-dialog__headerbtn:hover) {
    background: rgba(255, 255, 255, 0.25);
    transform: scale(1.1) rotate(90deg);
  }

  :deep(.el-dialog__headerbtn .el-dialog__close) {
    color: #ffffff;
    font-size: 16px;
    font-weight: bold;
  }

  :deep(.el-dialog__body) {
    padding: 8px 10px;
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  }

  .initial-stock-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 8px;
    background: linear-gradient(135deg, #ffffff 0%, #fafbfc 100%);
    border-radius: 8px;
    border: 1px solid rgba(226, 232, 240, 0.8);
    box-shadow:
      0 6px 20px rgba(0, 0, 0, 0.08),
      inset 0 1px 0 rgba(255, 255, 255, 0.9);
    margin-bottom: 8px;
    backdrop-filter: blur(10px);
  }

  .toolbar-left {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .toolbar-right {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .toolbar-left :deep(.el-input),
  .toolbar-left :deep(.el-date-editor),
  .toolbar-left :deep(.el-select) {
    --el-input-height: 32px;
    --el-input-border-radius: 8px;
    --el-input-bg-color: #ffffff;
    --el-input-border-color: #e2e8f0;
    --el-input-hover-border-color: #f59e0b;
    --el-input-focus-border-color: #f59e0b;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    transition: all 0.3s ease;
  }

  .toolbar-left :deep(.el-input:hover),
  .toolbar-left :deep(.el-date-editor:hover),
  .toolbar-left :deep(.el-select:hover) {
    box-shadow: 0 4px 12px rgba(245, 158, 11, 0.15);
    transform: translateY(-1px);
  }

  .toolbar-right .el-button {
    height: 32px;
    padding: 6px 12px;
    font-size: 13px;
    border-radius: 8px;
    font-weight: 600;
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
    border: none;
    color: white;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    transition: all 0.3s ease;
  }

  .toolbar-right .el-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
  }

  .initial-stock-table {
    background: #ffffff;
    border-radius: 16px;
    overflow: hidden;
    box-shadow:
      0 8px 30px rgba(0, 0, 0, 0.12),
      inset 0 1px 0 rgba(255, 255, 255, 0.9);
    border: 1px solid rgba(229, 231, 235, 0.8);
    backdrop-filter: blur(10px);
  }

  .initial-stock-table :deep(.el-table__header) {
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  }

  .initial-stock-table :deep(.el-table__header th) {
    background: transparent;
    color: #1f2937;
    font-weight: 700;
    font-size: 12px;
    padding: 12px 10px;
    border-bottom: 3px solid #e5e7eb;
    text-align: center;
    letter-spacing: 0.3px;
    text-transform: uppercase;
    font-size: 11px;
  }

  .initial-stock-table :deep(.el-table__header th:first-child) {
    border-top-left-radius: 16px;
  }

  .initial-stock-table :deep(.el-table__header th:last-child) {
    border-top-right-radius: 16px;
  }

  .initial-stock-table :deep(.el-table__body) {
    font-size: 12px;
  }

  .initial-stock-table :deep(.el-table__body td) {
    padding: 4px 10px;
    font-size: 12px;
    vertical-align: middle;
    border-bottom: 1px solid #f3f4f6;
  }

  .initial-stock-table :deep(.el-table__row) {
    height: 32px;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .initial-stock-table :deep(.el-table__row:hover) {
    background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(245, 158, 11, 0.15);
  }

  .initial-stock-table :deep(.el-table__row.el-table__row--striped) {
    background: #fafbfc;
  }

  .initial-stock-table :deep(.el-table__row.el-table__row--striped:hover) {
    background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  }

  .initial-stock-table :deep(.el-table__fixed-right) {
    box-shadow: -3px 0 12px rgba(0, 0, 0, 0.1);
    background: #ffffff;
  }

  .quantity-text {
    font-weight: 700;
    color: #059669;
    font-family: 'Courier New', monospace;
    font-size: 13px;
    padding: 2px 6px;
    background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
    border-radius: 6px;
    display: inline-block;
    min-width: 50px;
    text-align: right;
  }

  .action-buttons {
    display: flex;
    gap: 6px;
    justify-content: center;
    align-items: center;
    flex-wrap: wrap;
  }

  .action-buttons .el-button {
    padding: 5px 10px;
    font-size: 11px;
    border-radius: 8px;
    font-weight: 600;
    min-width: auto;
    border: none;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .edit-btn {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
    color: white;
  }

  .edit-btn:hover {
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(59, 130, 246, 0.4);
  }

  .save-btn {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: white;
  }

  .save-btn:hover {
    background: linear-gradient(135deg, #059669 0%, #047857 100%);
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(16, 185, 129, 0.4);
  }

  .cancel-btn {
    background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
    color: white;
  }

  .cancel-btn:hover {
    background: linear-gradient(135deg, #4b5563 0%, #374151 100%);
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(107, 114, 128, 0.4);
  }

  .delete-btn {
    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    color: white;
  }

  .delete-btn:hover {
    background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(239, 68, 68, 0.4);
  }

  .initial-stock-pagination {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-top: 24px;
    padding: 18px 20px;
    background: linear-gradient(135deg, #ffffff 0%, #fafbfc 100%);
    border-radius: 14px;
    box-shadow:
      0 6px 20px rgba(0, 0, 0, 0.08),
      inset 0 1px 0 rgba(255, 255, 255, 0.9);
    border: 1px solid rgba(229, 231, 235, 0.8);
    backdrop-filter: blur(10px);
  }

  .initial-stock-pagination :deep(.el-pagination) {
    --el-pagination-font-size: 12px;
    --el-pagination-button-width: 30px;
    --el-pagination-button-height: 30px;
  }

  .initial-stock-pagination :deep(.el-pagination .btn-prev),
  .initial-stock-pagination :deep(.el-pagination .btn-next),
  .initial-stock-pagination :deep(.el-pagination .el-pager li) {
    border-radius: 8px;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    border: 1px solid #e5e7eb;
    font-weight: 600;
  }

  .initial-stock-pagination :deep(.el-pagination .btn-prev:hover),
  .initial-stock-pagination :deep(.el-pagination .btn-next:hover),
  .initial-stock-pagination :deep(.el-pagination .el-pager li:hover) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(245, 158, 11, 0.25);
    border-color: #f59e0b;
    background: #fffbf0;
  }

  .initial-stock-pagination :deep(.el-pagination .el-pager li.is-active) {
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    color: white;
    border: none;
    box-shadow: 0 4px 16px rgba(245, 158, 11, 0.4);
    transform: translateY(-1px);
  }

  .initial-stock-pagination :deep(.el-pagination .el-pagination__total),
  .initial-stock-pagination :deep(.el-pagination .el-pagination__jump) {
    font-weight: 500;
    color: #374151;
  }
}

/* 初期在庫一括登録ダイアログ样式 */
.batch-initial-stock-dialog {
  .batch-initial-stock-body {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  :deep(.el-dialog) {
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 30px 100px rgba(0, 0, 0, 0.2);
    max-width: 95vw;
    border: 1px solid rgba(16, 185, 129, 0.2);
  }

  :deep(.el-dialog__header) {
    padding: 6px 10px 8px;
    border-bottom: none;
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    margin: 0;
    position: relative;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  }

  :deep(.el-dialog__header::after) {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  }

  :deep(.el-dialog__title) {
    color: #ffffff;
    font-weight: 700;
    font-size: 15px;
    letter-spacing: 0.5px;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.25);
  }

  :deep(.el-dialog__headerbtn) {
    top: 6px;
    right: 10px;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.2);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    backdrop-filter: blur(10px);
  }

  :deep(.el-dialog__headerbtn:hover) {
    background: rgba(255, 255, 255, 0.35);
    transform: scale(1.15) rotate(90deg);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  }

  :deep(.el-dialog__headerbtn .el-dialog__close) {
    color: #ffffff;
    font-size: 16px;
    font-weight: bold;
  }

  :deep(.el-dialog__body) {
    padding: 8px 10px;
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    min-height: 400px;
  }

  .batch-initial-stock-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 8px;
    background: linear-gradient(135deg, #ffffff 0%, #fafbfc 100%);
    border-radius: 8px;
    border: 1px solid rgba(226, 232, 240, 0.8);
    box-shadow:
      0 6px 20px rgba(0, 0, 0, 0.08),
      inset 0 1px 0 rgba(255, 255, 255, 0.9);
    margin-bottom: 6px;
    backdrop-filter: blur(10px);
  }

  .batch-initial-stock-summary {
    display: flex;
    gap: 8px;
    margin: 0 0 6px 0;
  }

  .batch-initial-stock-table {
    margin-top: 0;
  }

  .batch-initial-stock-summary .summary-card {
    flex: 1;
    background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
    border-radius: 8px;
    padding: 6px 10px;
    border: 1px solid rgba(16, 185, 129, 0.3);
    box-shadow: 0 3px 10px rgba(16, 185, 129, 0.12);
  }

  .batch-initial-stock-summary .summary-card.existing-total {
    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
    border: 1px solid rgba(59, 130, 246, 0.3);
    box-shadow: 0 3px 10px rgba(59, 130, 246, 0.12);
  }

  .batch-initial-stock-summary .summary-label {
    font-size: 11px;
    color: #4b5563;
    margin-bottom: 2px;
  }

  .batch-initial-stock-summary .summary-value {
    font-size: 15px;
    font-weight: 700;
    color: #065f46;
    letter-spacing: 0.5px;
  }

  .batch-initial-stock-summary .existing-total .summary-value {
    color: #1e3a8a;
  }

  .toolbar-left {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .toolbar-right {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .glass-panel {
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(226, 232, 240, 0.7);
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
    border-radius: 8px;
  }

  .compact-panel {
    padding: 6px 8px;
  }

  .toolbar-field {
    display: flex;
    align-items: center;
    gap: 6px;
    background: rgba(248, 250, 252, 0.8);
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 4px 8px;
  }

  .field-label {
    font-size: 11px;
    color: #475569;
    font-weight: 600;
    letter-spacing: 0.3px;
    min-width: 55px;
  }

  .toolbar-left :deep(.el-input),
  .toolbar-left :deep(.el-date-editor),
  .toolbar-left :deep(.el-select) {
    --el-input-height: 32px;
    --el-input-border-radius: 8px;
    --el-input-bg-color: #ffffff;
    --el-input-border-color: #e2e8f0;
    --el-input-hover-border-color: #10b981;
    --el-input-focus-border-color: #10b981;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    transition: all 0.3s ease;
  }

  .toolbar-left :deep(.el-input:hover),
  .toolbar-left :deep(.el-date-editor:hover),
  .toolbar-left :deep(.el-select:hover) {
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.15);
    transform: translateY(-1px);
  }

  .toolbar-control {
    width: 150px;
  }

  .toolbar-process {
    width: 190px;
  }

  .toolbar-right .el-button {
    height: 32px;
    padding: 6px 12px;
    font-size: 13px;
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.3s ease;
  }

  .toolbar-right .el-button--success {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    border: none;
    color: white;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
  }

  .toolbar-right .el-button--success:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
  }

  .batch-initial-stock-table {
    background: #ffffff;
    border-radius: 8px;
    overflow: hidden;
    box-shadow:
      0 8px 30px rgba(0, 0, 0, 0.12),
      inset 0 1px 0 rgba(255, 255, 255, 0.9);
    border: 1px solid rgba(229, 231, 235, 0.8);
    backdrop-filter: blur(10px);
  }

  .batch-initial-stock-table :deep(.el-table__header) {
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  }

  .batch-initial-stock-table :deep(.el-table__header th) {
    background: transparent;
    color: #1f2937;
    font-weight: 700;
    font-size: 11px;
    padding: 6px 8px;
    border-bottom: 2px solid #e5e7eb;
    text-align: center;
    letter-spacing: 0.25px;
    text-transform: uppercase;
  }

  .batch-initial-stock-table :deep(.el-table__body) {
    font-size: 12px;
  }

  .batch-initial-stock-table :deep(.el-table__body td) {
    padding: 3px 8px;
    font-size: 12px;
    vertical-align: middle;
    border-bottom: 1px solid #f3f4f6;
  }

  .batch-initial-stock-table :deep(.el-table__row) {
    height: 32px;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .batch-initial-stock-table :deep(.el-table__row:hover) {
    background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.15);
  }

  .batch-initial-stock-table :deep(.el-table__row.el-table__row--striped) {
    background: #fafbfc;
  }

  .batch-initial-stock-table :deep(.el-table__row.el-table__row--striped:hover) {
    background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
  }

  .compact-input {
    width: 110px;
  }

  .plain-number-input :deep(.el-input__wrapper) {
    padding: 2px 8px;
    border-radius: 8px;
    box-shadow: none;
    border: 1px solid #d1d5db;
  }

  .plain-number-input :deep(input[type='number']) {
    -moz-appearance: textfield;
    appearance: textfield;
  }

  .plain-number-input :deep(input::-webkit-outer-spin-button),
  .plain-number-input :deep(input::-webkit-inner-spin-button) {
    -webkit-appearance: none;
    margin: 0;
  }

  .existing-quantity-text {
    font-weight: 700;
    color: #059669;
    font-family: 'Courier New', monospace;
    font-size: 13px;
    padding: 2px 6px;
    background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
    border-radius: 6px;
    display: inline-block;
    min-width: 50px;
    text-align: right;
  }

  .no-data-text {
    color: #9ca3af;
    font-style: italic;
  }
}

/* 工程別印刷日付選択ダイアログ样式 */
.print-date-dialog :deep(.el-dialog) {
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
}

.print-date-dialog :deep(.el-dialog__header) {
  padding: 1.5rem 1.5rem 1rem;
  border-bottom: 1px solid #f0f0f0;
}

.print-date-dialog :deep(.el-dialog__title) {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
}

.print-date-dialog :deep(.el-dialog__body) {
  padding: 1.5rem;
}

.print-date-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.date-select-description {
  margin: 0;
  font-size: 0.9rem;
  color: #6b7280;
}

/* 工程別計画確認印刷ボタン样式 */
.process-print-btn-primary {
  background: linear-gradient(135deg, #10b981 0%, #059669 50%, #047857 100%);
  border: none;
  border-radius: 0.5rem;
  padding: 0.375rem 0.875rem;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
  transition: all 0.3s ease;
  font-size: 0.875rem;
  margin-right: 0.5rem;
  color: #fff;
  position: relative;
  overflow: hidden;
}

.process-print-btn-primary::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.5s;
}

.process-print-btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(16, 185, 129, 0.5);
  background: linear-gradient(135deg, #059669 0%, #047857 50%, #065f46 100%);
}

.process-print-btn-primary:hover::before {
  left: 100%;
}
</style>
