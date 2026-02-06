<!-- 月別受注管理 -->

<template>
  <div class="order-monthly-list-container" :class="{ 'animate-in': !pageLoading }">
    <!-- ページ読み込みマスク -->
    <div v-if="pageLoading" class="page-loading-overlay">
      <div class="loading-content">
        <div class="loading-spinner">
          <div class="spinner-ring"></div>
          <div class="spinner-ring"></div>
          <div class="spinner-ring"></div>
        </div>
        <p class="loading-text">月別受注データを読み込み中...</p>
      </div>
    </div>

    <!-- ページヘッダー -->
    <div class="page-header" :class="{ 'animate-in': !pageLoading }">
      <div class="header-content">
        <div class="title-section">
          <h2 class="title">
            <div class="title-icon">
              <el-icon>
                <calendar />
              </el-icon>
            </div>
            <span class="title-text">月別受注管理</span>
          </h2>
          <p class="subtitle">
            月別受注管理ページでは、月次の受注データの閲覧・追加・編集・削除、および日次受注の生成などが行えます
          </p>
        </div>
        <div class="header-decoration">
          <div class="decoration-circle circle-1"></div>
          <div class="decoration-circle circle-2"></div>
          <div class="decoration-circle circle-3"></div>
        </div>
      </div>
    </div>

    <!-- 合計カード -->
    <div class="summary-cards" :class="{ 'animate-in-delay-1': !pageLoading }">
      <el-card class="summary-card modern-card info-card">
        <div class="card-content">
          <div class="card-icon info-icon">
            <el-icon>
              <document />
            </el-icon>
          </div>
          <div class="card-info">
            <div class="summary-title">内示本数</div>
            <div class="summary-value">{{ summary.forecast_units?.toLocaleString() }}</div>
          </div>
        </div>
        <div class="card-decoration"></div>
      </el-card>

      <el-card class="summary-card modern-card success-card">
        <div class="card-content">
          <div class="card-icon success-icon">
            <el-icon>
              <check />
            </el-icon>
          </div>
          <div class="card-info">
            <div class="summary-title">確定本数</div>
            <div class="summary-value">{{ summary.forecast_total_units?.toLocaleString() }}</div>
          </div>
        </div>
        <div class="card-decoration"></div>
      </el-card>

      <el-card class="summary-card modern-card diff-card">
        <div class="card-content">
          <div class="card-icon diff-icon">
            <el-icon><trend-charts /></el-icon>
          </div>
          <div class="card-info">
            <div class="summary-title">内示差異</div>
            <div
              class="summary-value"
              :style="{
                color:
                  summary.forecast_diff < 0
                    ? '#e74c3c'
                    : summary.forecast_diff > 0
                      ? '#2ecc71'
                      : '#606266',
              }"
            >
              {{ summary.forecast_diff?.toLocaleString() }}
            </div>
          </div>
        </div>
        <div class="card-decoration"></div>
      </el-card>

      <el-card class="summary-card modern-card plating-card">
        <div class="card-content">
          <div class="card-icon plating-icon">
            <el-icon>
              <operation />
            </el-icon>
          </div>
          <div class="card-info">
            <div class="summary-title">社内メッキ</div>
            <div class="summary-value">{{ summary.plating_count?.toLocaleString() }}</div>
          </div>
        </div>
        <div class="card-decoration"></div>
      </el-card>

      <el-card class="summary-card modern-card external-plating-card">
        <div class="card-content">
          <div class="card-icon external-plating-icon">
            <el-icon>
              <tools />
            </el-icon>
          </div>
          <div class="card-info">
            <div class="summary-title">外注メッキ</div>
            <div class="summary-value">{{ summary.external_plating_count?.toLocaleString() }}</div>
          </div>
        </div>
        <div class="card-decoration"></div>
      </el-card>

      <el-card class="summary-card modern-card internal-welding-card">
        <div class="card-content">
          <div class="card-icon internal-welding-icon">
            <el-icon>
              <office-building />
            </el-icon>
          </div>
          <div class="card-info">
            <div class="summary-title">社内溶接</div>
            <div class="summary-value">{{ summary.internal_welding_count?.toLocaleString() }}</div>
          </div>
        </div>
        <div class="card-decoration"></div>
      </el-card>

      <el-card class="summary-card modern-card external-welding-card">
        <div class="card-content">
          <div class="card-icon external-welding-icon">
            <el-icon>
              <tools />
            </el-icon>
          </div>
          <div class="card-info">
            <div class="summary-title">外注溶接</div>
            <div class="summary-value">{{ summary.external_welding_count?.toLocaleString() }}</div>
          </div>
        </div>
        <div class="card-decoration"></div>
      </el-card>
    </div>

    <!-- 操作ボタンエリア -->
    <el-card class="action-card modern-card" :class="{ 'animate-in-delay-2': !pageLoading }">
      <div class="button-group">
        <el-button size="large" class="action-button btn-add" @click="handleAddOrder">
          <el-icon>
            <plus />
          </el-icon>
          新規月受注追加
        </el-button>
        <el-button size="large" class="action-button btn-batch" @click="openBatchDialog">
          <el-icon>
            <upload />
          </el-icon>
          月受注一括登録
        </el-button>
        <div class="generate-button-wrapper">
          <el-button
            size="large"
            class="action-button btn-generate"
            @click="handleGenerateDailyOrders"
            :loading="generating"
          >
            <el-icon>
              <calendar />
            </el-icon>
            日受注リスト生成
          </el-button>
          <div class="progress-bar-container" v-if="generating">
            <el-progress
              :percentage="generateProgressPercentage"
              :status="generateProgressStatus"
              :stroke-width="8"
              :show-text="true"
              :format="() => `${generateProgressPercentage}%`"
            />
          </div>
        </div>
        <el-button
          size="large"
          class="action-button btn-update-forecast"
          @click="handleUpdateForecastUnits"
          :loading="updatingForecast"
        >
          <el-icon>
            <refresh />
          </el-icon>
          内示本数更新
        </el-button>
        <el-button
          size="large"
          class="action-button btn-update-fields"
          @click="openUpdateFieldsDialog"
        >
          <el-icon>
            <edit />
          </el-icon>
          製品情報一括更新
        </el-button>
        <el-button
          size="large"
          class="action-button btn-batch-quantity"
          @click="openBatchQuantityDialog"
        >
          <el-icon><edit-pen /></el-icon>
          内示本数一括編集
        </el-button>
        <el-button
          size="large"
          class="action-button btn-daily-manage"
          @click="openDailyOrderDialog"
        >
          <el-icon>
            <list />
          </el-icon>
          日受注管理
        </el-button>
      </div>
    </el-card>

    <!-- フィルターフォーム -->
    <el-card
      class="filter-card modern-card enhanced-filter"
      :class="{ 'animate-in-delay-1': !pageLoading }"
    >
      <div class="filter-content">
        <el-form
          :inline="true"
          :model="filters"
          class="filter-bar enhanced single-row"
          @submit.prevent="fetchList"
        >
          <!-- 単行レイアウト：すべてのフィルターコントロール -->
          <div class="filter-row-unified">
            <!-- 時間選択エリア -->
            <div class="filter-group time-group">
              <div class="group-label">
                <el-icon>
                  <Calendar />
                </el-icon>
                <span>期間</span>
              </div>
              <div class="group-controls">
                <el-form-item label="年" class="inline-form-item">
                  <el-select
                    v-model="filters.year"
                    placeholder="年"
                    class="compact-select year-select"
                    @change="fetchList"
                  >
                    <el-option
                      v-for="year in yearOptions"
                      :key="year"
                      :label="`${year}年`"
                      :value="year"
                    />
                  </el-select>
                </el-form-item>

                <el-form-item label="月" class="inline-form-item">
                  <el-select
                    v-model="filters.month"
                    placeholder="月"
                    class="compact-select month-select"
                    @change="fetchList"
                  >
                    <el-option v-for="m in 12" :key="m" :label="`${m}月`" :value="m" />
                  </el-select>
                </el-form-item>

                <div class="nav-buttons-inline">
                  <el-button class="nav-btn prev-btn" @click="handlePrevMonth" size="small">
                    <el-icon><arrow-left /></el-icon>
                  </el-button>
                  <el-button class="nav-btn current-btn" @click="goToCurrentMonth" size="small">
                    今月
                  </el-button>
                  <el-button class="nav-btn next-btn" @click="handleNextMonth" size="small">
                    <el-icon><arrow-right /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>

            <!-- フィルター条件エリア -->
            <div class="filter-group search-group">
              <div class="group-label">
                <el-icon>
                  <Filter />
                </el-icon>
                <span>条件</span>
              </div>
              <div class="group-controls">
                <el-form-item label="納入先" class="inline-form-item">
                  <el-select
                    v-model="filters.destination_cd"
                    placeholder="全て選択"
                    size="default"
                    filterable
                    clearable
                    class="compact-select destination-select"
                    @change="fetchList"
                  >
                    <el-option
                      v-for="item in destinationOptions"
                      :key="item.cd"
                      :label="`${item.cd} | ${item.name}`"
                      :value="item.cd"
                    />
                  </el-select>
                </el-form-item>

                <el-form-item label="製品検索" class="inline-form-item search-item">
                  <el-input
                    v-model="filters.keyword"
                    placeholder="製品CD・製品名で検索..."
                    clearable
                    class="search-input compact-input"
                    @input="fetchList"
                    @keyup.enter="fetchList"
                  >
                    <template #prefix>
                      <el-icon class="search-icon">
                        <search />
                      </el-icon>
                    </template>
                  </el-input>
                </el-form-item>
              </div>
            </div>

            <!-- 操作ボタンエリア -->
            <div class="filter-group action-group">
              <div class="action-buttons compact">
                <el-button
                  type="primary"
                  @click="fetchList"
                  :loading="loading"
                  class="search-btn modern-btn"
                  size="default"
                >
                  <el-icon>
                    <Search />
                  </el-icon>
                  検索
                </el-button>
                <el-button @click="resetFilters" class="reset-btn modern-btn" size="default">
                  <el-icon>
                    <Refresh />
                  </el-icon>
                  リセット
                </el-button>
              </div>
            </div>
          </div>
        </el-form>
      </div>
    </el-card>

    <!-- データテーブル -->
    <el-card
      class="table-card modern-card no-header"
      :class="{ 'animate-in-delay-4': !pageLoading }"
    >
      <div class="table-header-inline">
        <div class="table-title">
          <el-icon class="table-icon">
            <grid />
          </el-icon>
          <span>受注データ一覧</span>
          <div class="count-badge">
            <el-icon class="count-icon">
              <document />
            </el-icon>
            <span>{{ pagination.total }}件</span>
          </div>
        </div>
      </div>

      <div class="table-wrapper">
        <el-table
          v-if="orderList.length > 0"
          :data="orderList"
          border
          stripe
          v-loading="loading"
          class="modern-table"
          show-summary
          :summary-method="getSummaries"
          element-loading-text="データを読み込み中..."
          element-loading-background="rgba(255, 255, 255, 0.8)"
          @sort-change="handleSortChange"
        >
          <el-table-column label="年" prop="year" width="70" align="center" />
          <el-table-column label="月" prop="month" width="60" align="center" />
          <el-table-column
            label="納入先名"
            prop="destination_name"
            min-width="140"
            sortable="custom"
          >
            <template #default="{ row }">
              <div class="destination-cell">
                <el-icon class="location-icon">
                  <location />
                </el-icon>
                <span>{{ row.destination_name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="製品CD" prop="product_cd" width="90" align="center">
            <template #default="{ row }">
              <el-tag :type="getProductCdTagType(row.product_cd)" effect="plain" size="small">
                {{ row.product_cd }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="製品名" prop="product_name" min-width="130" sortable="custom" />
          <el-table-column label="製品タイプ" prop="product_type" width="120" align="center">
            <template #default="{ row }">
              <el-tag :type="getProductTypeTagType(row.product_type)" effect="dark" size="small">
                {{ row.product_type || '未設定' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="内示本数" prop="forecast_units" align="right" width="110">
            <template #default="{ row }">
              <div class="number-cell">
                <span class="number-value">{{ formatNumber(row.forecast_units) }}</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="確定本数" prop="forecast_total_units" align="right" width="120">
            <template #default="{ row }">
              <div class="number-cell">
                <span class="number-value">{{ formatNumber(row.forecast_total_units) }}</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="内示差異" prop="forecast_diff" width="120" align="center">
            <template #default="{ row }">
              <div class="diff-cell-new">
                <span
                  class="diff-value-simple"
                  :class="{
                    'diff-positive': row.forecast_diff > 0,
                    'diff-negative': row.forecast_diff < 0,
                    'diff-zero': row.forecast_diff === 0,
                  }"
                >
                  {{ row.forecast_diff > 0 ? '+' : '' }}{{ formatNumber(row.forecast_diff) }}
                </span>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="200" fixed="right" align="center">
            <template #default="scope">
              <div class="table-action-buttons">
                <el-tooltip content="日別管理" placement="top">
                  <el-button
                    size="small"
                    type="primary"
                    class="compact-btn primary-btn"
                    @click="handleBatchEdit(scope.row.order_id)"
                  >
                    <el-icon>
                      <calendar />
                    </el-icon>
                  </el-button>
                </el-tooltip>
                <el-tooltip content="編集" placement="top">
                  <el-button
                    size="small"
                    type="success"
                    class="compact-btn success-btn"
                    @click="handleEditOrder(scope.row)"
                  >
                    <el-icon>
                      <Edit />
                    </el-icon>
                  </el-button>
                </el-tooltip>
                <el-tooltip content="削除" placement="top">
                  <el-button
                    size="small"
                    type="danger"
                    class="compact-btn danger-btn"
                    @click="handleDeleteOrder(scope.row)"
                  >
                    <el-icon>
                      <delete />
                    </el-icon>
                  </el-button>
                </el-tooltip>
              </div>
            </template>
          </el-table-column>
        </el-table>
        <template v-else>
          <div class="empty-state">
            <el-icon class="empty-icon">
              <document />
            </el-icon>
            <p class="empty-text">データがありません</p>
          </div>
        </template>
      </div>

      <!-- ページネーション -->
      <div class="pagination-container" v-if="orderList.length > 0">
        <div class="pagination-info">
          <span class="info-text">
            {{ (pagination.page - 1) * pagination.pageSize + 1 }}-{{
              Math.min(pagination.page * pagination.pageSize, pagination.total)
            }}
            / {{ pagination.total }}件
          </span>
        </div>
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          background
          layout="sizes, prev, pager, next, jumper"
          @current-change="fetchList"
          class="modern-pagination"
        />
      </div>
    </el-card>

    <!-- 新規受注追加ダイアログ -->
    <el-dialog
      v-model="addDialogVisible"
      width="600px"
      class="modern-dialog add-dialog"
      :before-close="() => (addDialogVisible = false)"
    >
      <template #header>
        <div class="dialog-header">
          <el-icon class="dialog-icon">
            <Plus />
          </el-icon>
          <span class="dialog-title">新規受注追加</span>
        </div>
      </template>
      <el-form
        :model="addForm"
        :rules="addRules"
        ref="addFormRef"
        label-width="140px"
        class="form-body"
      >
        <el-form-item label="納入先" prop="destination_cd">
          <el-select
            v-model="addForm.destination_cd"
            placeholder="納入先を選択"
            filterable
            clearable
            @change="handleDestinationChange"
          >
            <el-option
              v-for="item in destinationOptions"
              :key="item.cd"
              :label="`${item.cd} | ${item.name}`"
              :value="item.cd"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="年" prop="year">
          <el-input-number v-model="addForm.year" :min="2020" :max="2100" />
        </el-form-item>

        <el-form-item label="月" prop="month">
          <el-input-number v-model="addForm.month" :min="1" :max="12" />
        </el-form-item>

        <el-form-item label="製品CD" prop="product_cd">
          <el-select
            v-model="addForm.product_cd"
            placeholder="製品CDを選択"
            filterable
            clearable
            @change="handleProductCdChangeForAdd"
          >
            <el-option
              v-for="item in addProductOptions"
              :key="item.product_cd"
              :label="`${item.product_cd} | ${item.product_name}`"
              :value="item.product_cd"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="製品名" prop="product_name">
          <el-input v-model="addForm.product_name" disabled />
        </el-form-item>

        <el-form-item label="製品タイプ" prop="product_type">
          <el-select v-model="addForm.product_type" placeholder="選択してください" clearable>
            <el-option v-for="item in productTypeOptions" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>

        <el-form-item label="製品別名">
          <el-input v-model="addForm.product_alias" />
        </el-form-item>

        <el-form-item label="内示本数">
          <el-input-number v-model="addForm.forecast_units" :min="0" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="addDialogVisible = false">
          <el-icon>
            <Close />
          </el-icon>
          キャンセル
        </el-button>
        <el-button type="primary" @click="handleSaveAddOrder">
          <el-icon>
            <Check />
          </el-icon>
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- ✏️ 編集用ダイアログ -->
    <el-dialog
      v-model="editDialogVisible"
      width="600px"
      class="modern-dialog edit-dialog"
      :before-close="() => (editDialogVisible = false)"
      center
    >
      <template #header>
        <div class="dialog-header">
          <el-icon class="dialog-icon">
            <Edit />
          </el-icon>
          <span class="dialog-title">月別受注編集</span>
        </div>
      </template>
      <el-form
        :model="editForm"
        :rules="addRules"
        ref="editFormRef"
        label-width="140px"
        class="form-body"
      >
        <el-form-item label="納入先" prop="destination_cd">
          <el-select
            v-model="editForm.destination_cd"
            placeholder="納入先を選択"
            filterable
            clearable
            disabled
          >
            <el-option
              v-for="item in destinationOptions"
              :key="item.cd"
              :label="`${item.cd} | ${item.name}`"
              :value="item.cd"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="年" prop="year">
          <el-input-number v-model="editForm.year" :min="2020" :max="2100" disabled />
        </el-form-item>

        <el-form-item label="月" prop="month">
          <el-input-number v-model="editForm.month" :min="1" :max="12" disabled />
        </el-form-item>

        <el-form-item label="製品CD" prop="product_cd">
          <el-input v-model="editForm.product_cd" />
        </el-form-item>

        <el-form-item label="製品名" prop="product_name">
          <el-input v-model="editForm.product_name" />
        </el-form-item>

        <el-form-item label="製品タイプ" prop="product_type">
          <el-select v-model="editForm.product_type" placeholder="選択してください" clearable>
            <el-option v-for="item in productTypeOptions" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>

        <el-form-item label="製品別名">
          <el-input v-model="editForm.product_alias" />
        </el-form-item>

        <el-form-item label="内示本数">
          <el-input-number v-model="editForm.forecast_units" :min="0" ref="forecastUnitsInputRef" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="editDialogVisible = false">
          <el-icon>
            <Close />
          </el-icon>
          キャンセル
        </el-button>
        <el-button type="primary" @click="handleSaveEditOrder">
          <el-icon>
            <Check />
          </el-icon>
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 🔥 。。 -->
    <el-dialog
      v-model="batchDialogVisible"
      width="800px"
      destroy-on-close
      center
      class="modern-dialog batch-dialog"
      :before-close="() => (batchDialogVisible = false)"
    >
      <template #header>
        <div class="dialog-header compact-header">
          <el-icon class="dialog-icon">
            <Upload />
          </el-icon>
          <span class="dialog-title">月注文一括登録</span>
        </div>
      </template>
      <div class="batch-form-container">
        <div class="batch-form compact-form">
          <el-form :model="batchForm" :inline="true" class="compact-form-inner batch-form-inline">
            <el-form-item label="年" class="inline-form-item">
              <el-select v-model="batchForm.year" placeholder="年を選択" class="year-select">
                <el-option v-for="y in batchYearOptions" :key="y" :label="`${y}年`" :value="y" />
              </el-select>
            </el-form-item>

            <el-form-item label="月" class="inline-form-item">
              <div class="month-select-with-nav">
                <el-select v-model="batchForm.month" placeholder="月を選択" class="month-select">
                  <el-option v-for="m in 12" :key="m" :label="`${m}月`" :value="m" />
                </el-select>
                <div class="month-nav-buttons">
                  <el-button
                    class="month-nav-btn prev-month-btn"
                    @click="handleBatchPrevMonth"
                    size="small"
                  >
                    <el-icon>
                      <ArrowLeft />
                    </el-icon>
                  </el-button>
                  <el-button
                    class="month-nav-btn current-month-btn"
                    :class="{ active: isBatchCurrentMonth }"
                    @click="handleBatchCurrentMonth"
                    size="small"
                  >
                    今月
                  </el-button>
                  <el-button
                    class="month-nav-btn next-month-btn"
                    @click="handleBatchNextMonth"
                    size="small"
                  >
                    <el-icon>
                      <ArrowRight />
                    </el-icon>
                  </el-button>
                </div>
              </div>
            </el-form-item>

            <el-form-item label="納入先" class="inline-form-item">
              <el-select
                v-model="batchForm.destination_cd"
                filterable
                placeholder="納入先を選択"
                class="destination-select"
              >
                <el-option
                  v-for="item in batchDestinationOptions"
                  :key="item.cd"
                  :label="`${item.cd} | ${item.name}`"
                  :value="item.cd"
                />
              </el-select>
            </el-form-item>

            <el-form-item class="inline-form-item button-item">
              <el-button type="primary" class="load-btn" @click="fetchProducts">
                <el-icon>
                  <Download />
                </el-icon>
                読込
              </el-button>
            </el-form-item>
          </el-form>
          <div class="table-container">
            <el-table
              v-if="batchProducts.length > 0"
              :data="batchProducts"
              class="batch-product-table"
              :loading="batchLoading"
              border
              stripe
              highlight-current-row
            >
              <el-table-column label="製品タイプ" width="110" show-overflow-tooltip>
                <template #default="{ row }">
                  <el-tag
                    :type="getProductTypeTagType(row.product_type)"
                    effect="light"
                    size="small"
                  >
                    {{ row.product_type || '未設定' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="product_cd" label="製品CD" width="90" />
              <el-table-column
                prop="product_name"
                label="製品名"
                min-width="180"
                show-overflow-tooltip
              />

              <el-table-column label="数量" width="120" align="center">
                <template #default="{ row, $index }">
                  <el-input
                    v-model="row.quantity"
                    type="text"
                    class="quantity-input"
                    :class="row.quantity > 0 ? 'normal-cell' : 'warning-cell'"
                    placeholder="数量"
                    @keydown.enter.prevent="handleQuantityEnter($index)"
                    @focus="handleFocus"
                    @input="handleQuantityChange(row, $index)"
                    :id="`quantity-input-${$index}`"
                  />
                </template>
              </el-table-column>
            </el-table>
            <div v-else-if="batchLoading" class="loading-placeholder compact-placeholder">
              <el-icon class="is-loading">
                <loading />
              </el-icon>
              <p>データ読込中...</p>
            </div>
            <div
              v-else-if="!batchForm.destination_cd"
              class="empty-placeholder compact-placeholder"
            >
              <p>納入先を選択し、製品一覧を読み込んでください</p>
            </div>
            <div v-else class="empty-placeholder compact-placeholder">
              <p>製品データがありません</p>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer-compact">
          <el-button @click="batchDialogVisible = false" class="cancel-btn">
            <el-icon>
              <Close />
            </el-icon>
            キャンセル
          </el-button>
          <el-button type="primary" @click="handleBatchRegister" class="register-btn">
            <el-icon>
              <Check />
            </el-icon>
            登録する
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 受注情報一括更新ダイアログ -->
    <el-dialog
      v-model="updateFieldsDialogVisible"
      width="700px"
      destroy-on-close
      center
      class="modern-dialog update-dialog"
      :before-close="() => (updateFieldsDialogVisible = false)"
    >
      <template #header>
        <div class="dialog-header">
          <el-icon class="dialog-icon">
            <Refresh />
          </el-icon>
          <span class="dialog-title">製品情報一括更新</span>
        </div>
      </template>
      <el-form :model="updateFieldsForm" label-width="140px">
        <el-form-item label="開始日">
          <el-date-picker
            v-model="updateFieldsForm.startDate"
            type="date"
            placeholder="開始日を選択"
          />
        </el-form-item>

        <el-form-item label="製品情報を更新">
          <el-checkbox v-model="updateFieldsForm.updateProductInfo"
            >製品情報を最新データに更新</el-checkbox
          >
        </el-form-item>

        <div v-if="updateFieldsForm.updateProductInfo">
          <el-alert
            title="この操作により、月受注の製品情報（製品名・製品別名・製品タイプ）が最新のマスターデータで更新されます。"
            type="info"
            :closable="false"
            style="margin-bottom: 15px"
          />
        </div>

        <el-form-item>
          <el-button type="primary" @click="handleUpdateFields" :loading="updateFieldsLoading">
            <el-icon>
              <Refresh />
            </el-icon>
            更新実行
          </el-button>
          <el-button @click="updateFieldsDialogVisible = false">
            <el-icon>
              <Close />
            </el-icon>
            キャンセル
          </el-button>
        </el-form-item>
      </el-form>
    </el-dialog>

    <!-- 日別受注一括編集 -->
    <OrderDailyBatchEditDialog
      v-model:visible="batchEditDialogVisible"
      :monthlyOrderId="batchEditMonthlyOrderId"
      @saved="fetchList"
    />

    <!-- 内示本数更新进度条弹窗 -->
    <el-dialog
      v-model="updateForecastProgressVisible"
      title="内示本数更新中"
      width="500px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
      class="update-forecast-progress-dialog"
    >
      <div class="progress-content">
        <div class="progress-info">
          <p class="progress-text">{{ updateForecastProgressText }}</p>
          <p class="progress-detail" v-if="updateForecastCurrent > 0">
            処理中: {{ updateForecastCurrent }} / {{ updateForecastTotal }}
          </p>
        </div>
        <el-progress
          :percentage="updateForecastProgressPercentage"
          :status="updateForecastProgressStatus"
          :stroke-width="12"
          :show-text="true"
          :format="() => `${updateForecastProgressPercentage}%`"
        />
        <div
          class="progress-stats"
          v-if="updateForecastStats.updated > 0 || updateForecastStats.cleared > 0"
        >
          <div class="stat-item">
            <span class="stat-label">更新:</span>
            <span class="stat-value updated">{{ updateForecastStats.updated }}件</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">クリア:</span>
            <span class="stat-value cleared">{{ updateForecastStats.cleared }}件</span>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 日別受注編集ダイアログ -->
    <el-dialog
      v-model="dailyOrderDialogVisible"
      width="75%"
      top="2vh"
      destroy-on-close
      class="modern-dialog daily-manage-dialog enhanced-dialog compact-dialog japanese-minimalist"
      :before-close="() => (dailyOrderDialogVisible = false)"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <template #header>
        <div class="dialog-header japanese-header">
          <div class="header-left">
            <el-icon class="dialog-icon japanese-icon">
              <Calendar />
            </el-icon>
            <span class="dialog-title japanese-title">日別受注編集</span>
          </div>
          <div class="header-right">
            <div class="header-badge japanese-badge">
              <span class="badge-text">{{ dailyOrdersList.length }} 件</span>
            </div>
          </div>
        </div>
      </template>

      <!-- 筛选条件 -->
      <el-form
        :inline="true"
        :model="dailyOrderForm"
        class="daily-filter-form japanese-filter-form compact-filter"
      >
        <el-form-item label="日付" class="compact-form-item">
          <el-date-picker
            v-model="dailyOrderForm.date"
            type="date"
            placeholder="日付を選択"
            value-format="YYYY-MM-DD"
            format="YYYY/MM/DD"
            size="small"
            class="compact-input"
            style="width: 120px"
            @change="fetchDailyOrdersList"
          />
          <el-button-group style="margin-left: 4px">
            <el-button size="small" class="nav-day-btn" @click="changeDay(-1)">前日</el-button>
            <el-button size="small" class="nav-day-btn" @click="setToday">今日</el-button>
            <el-button size="small" class="nav-day-btn" @click="changeDay(1)">後日</el-button>
          </el-button-group>
        </el-form-item>

        <el-form-item label="納入先" class="compact-form-item">
          <el-select
            v-model="dailyOrderForm.destination_cd"
            placeholder="納入先を選択"
            size="small"
            filterable
            clearable
            style="width: 200px"
            @change="fetchDailyOrdersList"
          >
            <el-option
              v-for="d in destinationOptions"
              :key="d.cd"
              :label="`${d.cd} | ${d.name}`"
              :value="d.cd"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="ショートカット" class="compact-form-item">
          <el-button
            size="small"
            class="quick-dest-btn"
            @click="quickSelectDailyDestination('(株)タチエス愛知')"
            >愛知</el-button
          >
          <el-button
            size="small"
            class="quick-dest-btn"
            @click="quickSelectDailyDestination('日本発条横浜工場')"
            >横浜</el-button
          >
          <el-button
            size="small"
            class="quick-dest-btn"
            @click="quickSelectDailyDestination('(株)東海化成')"
            >東海</el-button
          >
          <el-button
            size="small"
            class="quick-dest-btn"
            @click="quickSelectDailyDestination('(株)西浦化学')"
            >西浦</el-button
          >
          <el-button
            size="small"
            class="quick-dest-btn"
            @click="quickSelectDailyDestination('(株)INOAC吉良')"
            >吉良</el-button
          >
        </el-form-item>
        <el-form-item class="compact-form-item push-right">
          <el-button
            type="primary"
            size="small"
            :loading="dailyOrdersSaving"
            @click="handleDailyOrdersSave"
            class="compact-button save-cta"
          >
            <el-icon class="small-icon">
              <Check />
            </el-icon>
            一括保存
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 日別受注データテーブル -->
      <el-table
        v-loading="dailyOrdersLoading"
        :data="dailyOrdersList"
        border
        stripe
        show-summary
        :summary-method="getDailySummaries"
        sum-text="合計"
        class="daily-orders-table japanese-table compact-table"
        height="calc(100vh - 280px)"
        size="small"
        :cell-style="{
          padding: '2px 4px',
          fontSize: '11px',
          fontWeight: '400',
          color: '#1f2937',
        }"
        :header-cell-style="{
          padding: '4px 4px',
          fontSize: '11px',
          fontWeight: '600',
          backgroundColor: '#f5f5f5',
          color: '#374151',
          textAlign: 'center',
        }"
      >
        <el-table-column
          label="納入先名"
          prop="destination_name"
          min-width="120"
          show-overflow-tooltip
          align="center"
        >
          <template #default="{ row }">
            <div class="table-cell-content centered">
              <span class="cell-text">{{ row.destination_name }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column
          label="製品名"
          prop="product_name"
          min-width="140"
          show-overflow-tooltip
          align="left"
        >
          <template #default="{ row }">
            <div class="table-cell-content left-aligned">
              <span class="cell-text">{{ row.product_name }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="製品タイプ" prop="product_type" width="100" align="center">
          <template #default="{ row }">
            <div class="table-cell-content centered">
              <span class="cell-text">{{ row.product_type || '-' }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="入数" prop="unit_per_box" width="55" align="center">
          <template #default="{ row }">
            <div class="number-cell">
              <span class="number-value">{{ row.unit_per_box }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="日付" width="85" align="center">
          <template #default="{ row }">
            <div class="date-cell">
              <span class="date-value">{{ formatDateDisplay(row.year, row.month, row.day) }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="曜日" prop="weekday" width="50" align="center">
          <template #default="{ row }">
            <div class="weekday-cell">
              <span class="weekday-value" :class="getWeekdayClass(row.weekday)">{{
                row.weekday
              }}</span>
            </div>
          </template>
        </el-table-column>

        <!-- 確定箱数（編集） -->
        <el-table-column label="確定箱数" prop="confirmed_boxes" width="80" align="center">
          <template #default="{ row, $index }">
            <div class="input-cell">
              <el-input
                size="small"
                class="modern-table-input editable-input"
                :model-value="row.confirmed_boxes === 0 ? '' : row.confirmed_boxes"
                :disabled="dailyOrdersSaving"
                @update:model-value="
                  (val) => {
                    row.confirmed_boxes = val === '' ? 0 : Number(val)
                    handleDailyConfirmedBoxesChange(row)
                  }
                "
                @keydown.enter="focusDailyNextInput($index)"
                :ref="
                  (el) => {
                    if (el && '$el' in el) {
                      dailyConfirmedBoxesInputs[$index] =
                        (el.$el.querySelector('input') as HTMLInputElement) || undefined
                    }
                  }
                "
              />
            </div>
          </template>
        </el-table-column>

        <!-- 確定本数（編集可能） -->
        <el-table-column label="確定本数" prop="confirmed_units" width="80" align="center">
          <template #default="{ row, $index }">
            <div class="input-cell">
              <el-input
                size="small"
                class="modern-table-input editable-input"
                :model-value="row.confirmed_units === 0 ? '' : row.confirmed_units"
                :disabled="dailyOrdersSaving"
                @update:model-value="
                  (val) => {
                    row.confirmed_units = val === '' ? 0 : Number(val)
                    markDailyRowChanged(row)
                  }
                "
                @keydown.enter="focusDailyNextConfirmedUnitsInput($index)"
                :ref="
                  (el) => {
                    if (el && '$el' in el) {
                      dailyConfirmedUnitsInputs[$index] =
                        (el.$el.querySelector('input') as HTMLInputElement) || undefined
                    }
                  }
                "
              />
            </div>
          </template>
        </el-table-column>

        <!-- 内示本数（読み取り専用） -->
        <!-- <el-table-column label="内示本数" prop="forecast_units" min-width="100" align="center">
          <template #default="{ row }">
            <div class="input-cell">
              <el-input
                size="default"
                class="modern-table-input readonly-input"
                :model-value="row.forecast_units === 0 ? '' : row.forecast_units"
                disabled
              />
            </div>
          </template>
        </el-table-column> -->

        <!-- 納入日 -->
        <el-table-column label="納入日" prop="delivery_date" width="85" align="center">
          <template #default="{ row }">
            <div class="date-cell">
              <span class="date-value">{{ formatDate(row.delivery_date) }}</span>
            </div>
          </template>
        </el-table-column>

        <!-- 状態 -->
        <!-- <el-table-column label="状態" prop="status" width="150" align="center">
          <template #default="{ row }">
            <div class="select-cell">
              <el-select
                v-model="row.status"
                placeholder="選択"
                size="default"
                class="modern-status-select"
                @change="markDailyRowChanged(row)"
              >
                <el-option label="未出荷" value="未出荷" />
                <el-option label="出荷済み" value="出荷済み" />
                <el-option label="キャンセル" value="キャンセル" />
              </el-select>
            </div>
          </template>
        </el-table-column> -->
      </el-table>

      <!-- Footer -->
      <template #footer></template>
    </el-dialog>

    <!-- 納入先選択ダイアログ -->
    <DestinationSelectDialog
      v-model="destinationDialogVisible"
      :destinations="destinationOptions.map((d) => ({ value: d.cd, label: `${d.cd} | ${d.name}` }))"
      :current-destination="filters.destination_cd"
      @select="handleDestinationSelect"
    />

    <!-- 日別受注編集ダイアログの納入先選択 -->
    <DestinationSelectDialog
      v-model="dailyDestinationDialogVisible"
      :destinations="destinationOptions.map((d) => ({ value: d.cd, label: `${d.cd} | ${d.name}` }))"
      :current-destination="dailyOrderForm.destination_cd"
      @select="handleDailyDestinationSelect"
    />

    <!-- 内示本数一括編集ダイアログ -->
    <el-dialog
      v-model="batchQuantityDialogVisible"
      width="54%"
      destroy-on-close
      center
      class="modern-dialog batch-quantity-dialog"
      :before-close="() => (batchQuantityDialogVisible = false)"
    >
      <template #header>
        <div class="dialog-header-compact">
          <div class="dialog-header-left">
            <el-icon class="dialog-icon-compact">
              <EditPen />
            </el-icon>
            <span class="dialog-title-compact">内示本数一括編集</span>
          </div>
          <el-button
            type="primary"
            @click="loadBatchEditData"
            :loading="batchDataLoading"
            size="small"
            class="header-load-btn"
          >
            <el-icon>
              <Search />
            </el-icon>
            データ読み込み
          </el-button>
        </div>
      </template>

      <div class="batch-quantity-container">
        <!-- 編集テーブル -->
        <div class="quantity-edit-section">
          <div class="edit-header-compact">
            <h4 class="edit-title-compact">内示本数編集 ({{ batchEditData.length }}件)</h4>
            <div class="edit-stats-compact">
              <span class="stats-text-compact">変更済み: {{ changedRows.size }}件</span>
              <el-button
                type="primary"
                @click="executeBatchQuantityUpdate"
                :loading="batchQuantityUpdating"
                :disabled="changedRows.size === 0"
                size="small"
                class="execute-btn-inline"
              >
                <el-icon>
                  <Check />
                </el-icon>
                一括更新実行 ({{ changedRows.size }}件)
              </el-button>
            </div>
          </div>

          <el-table
            v-loading="batchDataLoading"
            :data="batchEditData"
            border
            stripe
            class="quantity-edit-table"
            height="520px"
            size="small"
            :default-sort="{ prop: 'product_name', order: 'ascending' }"
          >
            <el-table-column label="納入先" prop="destination_name" width="160" />
            <el-table-column label="製品CD" prop="product_cd" width="90" align="center" />
            <el-table-column
              label="製品名"
              prop="product_name"
              width="150"
              show-overflow-tooltip
              sortable
            />
            <el-table-column label="現在の内示本数" width="110" align="right">
              <template #default="{ row }">
                <span class="current-value">{{ formatNumber(row.forecast_units) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="編集内示本数" min-width="140" align="center">
              <template #default="{ row, $index }">
                <el-input-number
                  v-model="row.edited_forecast_units"
                  :min="0"
                  :precision="0"
                  size="small"
                  class="inline-edit-input"
                  :controls="false"
                  @change="markRowChanged(row)"
                  @keydown.enter="focusNextInput($index)"
                  :ref="
                    (el) => {
                      if (el && '$el' in el) {
                        batchEditInputs[$index] =
                          (el.$el.querySelector('input') as HTMLInputElement) || undefined
                      }
                    }
                  "
                />
              </template>
            </el-table-column>
            <el-table-column label="変更" width="100" align="center">
              <template #default="{ row }">
                <el-tag v-if="isRowChanged(row)" type="success" size="small" effect="plain">
                  <el-icon style="margin-right: 2px">
                    <EditPen />
                  </el-icon>
                  変更
                </el-tag>
                <span v-else class="no-change">-</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, nextTick, h, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useMainStore } from '@/store/main'
import {
  Calendar,
  Document,
  Check,
  TrendCharts,
  Tools,
  Plus,
  Upload,
  Edit,
  EditPen,
  List,
  Search,
  ArrowLeft,
  ArrowRight,
  Location,
  Grid,
  ArrowUp,
  ArrowDown,
  Delete,
  Close,
  Download,
  Refresh,
  OfficeBuilding,
  DataAnalysis,
  Filter,
} from '@element-plus/icons-vue'
import {
  generateDailyOrders,
  fetchMonthlyOrders,
  fetchMonthlySummary,
  createMonthlyOrder,
  updateMonthlyOrder,
  deleteMonthlyOrder,
  deleteMonthlyOrderByOrderId,
  checkMonthlyOrderExists,
  checkCombinationExists,
  getProductsByDestination,
  batchCreateMonthlyOrders,
  updateOrderFields,
  fetchDailyOrders,
  batchUpdateDailyOrders,
  batchUpdateMonthlyQuantity,
  fetchDailyOrdersByMonthlyOrderId,
} from '@/api/order/order'
import type { OrderMonthly, OrderDaily, OrderDailyUpdate } from '@/types/order'
import { getDestinationOptions } from '@/api/options'
import type { Destination } from '@/types/master'
import OrderDailyBatchEditDialog from './components/OrderDailyBatchEditDialog.vue'
import dayjs from 'dayjs'
import type { VNode } from 'vue'
import DestinationSelectDialog from './components/DestinationSelectDialog.vue'

// 千分位カンマ
const formatNumber = (value: number | undefined): string => {
  if (typeof value !== 'number') return ''
  return value.toLocaleString('ja-JP')
}

// フィルター条件
const filters = ref({
  year: new Date().getFullYear(),
  month: new Date().getMonth() + 1,
  destination_cd: '',
  keyword: '',
})

// 年オプション（共有）
const yearOptions = Array.from({ length: 6 }, (_, i) => new Date().getFullYear() - 3 + i)

// リストデータ & ページネーション
const orderList = ref<OrderMonthly[]>([])
const loading = ref(false)
const pageLoading = ref(true)
const pagination = ref({ page: 1, pageSize: 25, total: 0 })

// 排序状态
const sortInfo = ref<{ prop: string; order: 'ascending' | 'descending' | null } | null>(null)

// 新規受注ダイアログ
const addDialogVisible = ref(false)
const addForm = ref<OrderMonthly>({
  destination_cd: '',
  destination_name: '',
  year: new Date().getFullYear(),
  month: new Date().getMonth() + 1,
  product_cd: '',
  product_name: '',
  product_type: '',
  product_alias: '',
  forecast_units: 0,
  forecast_total_units: 0,
})
const addFormRef = ref()
const addRules = {
  destination_cd: [{ required: true, message: '納入先CDは必須', trigger: 'change' }],
  product_cd: [{ required: true, message: '製品CDは必須', trigger: 'blur' }],
  product_name: [{ required: true, message: '製品名は必須', trigger: 'blur' }],
  year: [{ required: true, message: '年は必須', trigger: 'change' }],
  month: [{ required: true, message: '月は必須', trigger: 'change' }],
}

// 新規：新規受注追加ダイアログ用の製品オプション
const addProductOptions = ref<{ product_cd: string; product_name: string; product_type: string }[]>(
  [],
)

// 納入先オプション
const destinationOptions = ref<Destination[]>([])
const validDestinationOptions = computed(() =>
  destinationOptions.value.filter((item) => item.cd && item.name),
)

// 选择納入先时带出名称，并联动产品下拉
const handleDestinationChange = async (cd: string) => {
  const selected = destinationOptions.value.find((item) => item.cd === cd)
  if (selected) {
    addForm.value.destination_name = selected.name
  } else {
    addForm.value.destination_name = ''
  }
  // 製品ドロップダウン連動
  addProductOptions.value = []
  addForm.value.product_cd = ''
  addForm.value.product_name = ''
  addForm.value.product_type = ''
  if (!cd) return
  try {
    const products = await getProductsByDestination(cd, addForm.value.year, addForm.value.month)
    addProductOptions.value = (products || [])
      .filter((p: any) => p.status !== 'inactive')
      .sort((a: any, b: any) => (a.product_name || '').localeCompare(b.product_name || ''))
      .map((p: any) => ({
        product_cd: p.product_cd,
        product_name: p.product_name,
        product_type: p.product_type || '',
      }))
  } catch (e) {
    addProductOptions.value = []
  }
}

// 选择製品CD时，自动带出製品名
const handleProductCdChangeForAdd = (cd: string) => {
  const selected = addProductOptions.value.find((item: any) => item.product_cd === cd)
  if (selected) {
    addForm.value.product_name = selected.product_name
    addForm.value.product_type = selected.product_type || ''
  } else {
    addForm.value.product_name = ''
    addForm.value.product_type = ''
  }
}

// カード表示データ
const summaryData = ref({
  forecast_units: 0,
  forecast_total_units: 0,
  forecast_diff: 0,
  plating_count: 0,
  external_plating_count: 0,
  internal_welding_count: 0,
  external_welding_count: 0,
})

// 計算プロパティ
const summary = computed(() => ({
  forecast_units: summaryData.value.forecast_units || 0,
  forecast_total_units: summaryData.value.forecast_total_units || 0,
  forecast_diff: summaryData.value.forecast_diff || 0,
  plating_count: summaryData.value.plating_count || 0,
  external_plating_count: summaryData.value.external_plating_count || 0,
  internal_welding_count: summaryData.value.internal_welding_count || 0,
  external_welding_count: summaryData.value.external_welding_count || 0,
}))

// 合計を取得するメソッド
const fetchSummary = async () => {
  try {
    const params = {
      year: filters.value.year,
      month: filters.value.month,
      destination_cd: filters.value.destination_cd,
      keyword: filters.value.keyword,
    }
    const res = await fetchMonthlySummary(params)
    if (res) {
      summaryData.value = {
        forecast_units: typeof res.forecast_units === 'number' ? res.forecast_units : 0,
        forecast_total_units:
          typeof res.forecast_total_units === 'number' ? res.forecast_total_units : 0,
        forecast_diff: typeof res.forecast_diff === 'number' ? res.forecast_diff : 0,
        plating_count: typeof res.plating_count === 'number' ? res.plating_count : 0,
        external_plating_count:
          typeof res.external_plating_count === 'number' ? res.external_plating_count : 0,
        internal_welding_count:
          typeof res.internal_welding_count === 'number' ? res.internal_welding_count : 0,
        external_welding_count:
          typeof res.external_welding_count === 'number' ? res.external_welding_count : 0,
      }
    }
  } catch (error) {
    console.error('合計データの取得に失敗', error)
    // エラー発生時にデフォルト値を設定
    summaryData.value = {
      forecast_units: 0,
      forecast_total_units: 0,
      forecast_diff: 0,
      plating_count: 0,
      external_plating_count: 0,
      internal_welding_count: 0,
      external_welding_count: 0,
    }
  }
}

// 获取所有分页数据（用于排序）
const fetchAllData = async () => {
  const baseParams = {
    year: filters.value.year,
    month: filters.value.month,
    destination_cd: filters.value.destination_cd,
    keyword: filters.value.keyword,
  }

  const pageSize = 100
  const firstPageParams = {
    ...baseParams,
    page: 1,
    pageSize,
  }
  const firstResponse = await fetchMonthlyOrders(firstPageParams)
  const total = firstResponse.total || 0
  let allData: OrderMonthly[] = [...(firstResponse.list || [])]

  const totalPages = Math.ceil(total / pageSize)
  if (totalPages > 1) {
    const promises: Promise<{ list: OrderMonthly[]; total: number }>[] = []
    for (let page = 2; page <= totalPages; page++) {
      promises.push(
        fetchMonthlyOrders({
          ...baseParams,
          page,
          pageSize,
        }),
      )
    }
    const responses = await Promise.all(promises)
    responses.forEach((response) => {
      if (response.list) {
        allData = allData.concat(response.list)
      }
    })
  }

  return { allData, total }
}

// 排序处理函数
const sortData = (data: OrderMonthly[]) => {
  if (!sortInfo.value || !sortInfo.value.order) {
    return data
  }

  const { prop, order } = sortInfo.value
  const sortedData = [...data]

  sortedData.sort((a: any, b: any) => {
    let aValue = a[prop] || ''
    let bValue = b[prop] || ''

    // 字符串比较（支持日语）
    if (typeof aValue === 'string' && typeof bValue === 'string') {
      const comparison = aValue.localeCompare(bValue, 'ja')
      return order === 'ascending' ? comparison : -comparison
    }

    // 数字比较
    const aNum = Number(aValue)
    const bNum = Number(bValue)
    if (!isNaN(aNum) && !isNaN(bNum)) {
      return order === 'ascending' ? aNum - bNum : bNum - aNum
    }

    // 默认比较
    if (aValue < bValue) return order === 'ascending' ? -1 : 1
    if (aValue > bValue) return order === 'ascending' ? 1 : -1
    return 0
  })

  return sortedData
}

// 列表検索
const fetchList = async () => {
  loading.value = true
  try {
    // 如果有排序，获取所有数据并排序
    if (sortInfo.value && sortInfo.value.order) {
      const { allData, total } = await fetchAllData()
      const sortedData = sortData(allData)
      pagination.value.total = total

      // 分页显示
      const start = (pagination.value.page - 1) * pagination.value.pageSize
      const end = start + pagination.value.pageSize
      orderList.value = sortedData.slice(start, end)
    } else {
      // 没有排序时，正常分页获取
      const params = {
        year: filters.value.year,
        month: filters.value.month,
        destination_cd: filters.value.destination_cd,
        keyword: filters.value.keyword,
        page: pagination.value.page,
        pageSize: pagination.value.pageSize,
      }
      const data = (await fetchMonthlyOrders(params)) as unknown as {
        list: OrderMonthly[]
        total: number
      }
      orderList.value = Array.isArray(data.list) ? data.list : []
      pagination.value.total = typeof data.total === 'number' ? data.total : 0
    }

    // すべてのデータの合計を取得
    await fetchSummary()
  } catch (error) {
    console.error('注文一覧取得失敗', error)
    orderList.value = []
    pagination.value.total = 0
  } finally {
    loading.value = false
  }
}

// 排序变化处理
const handleSortChange = ({ prop, order }: { prop: string; order: string | null }) => {
  if (order) {
    sortInfo.value = {
      prop,
      order: order === 'ascending' ? 'ascending' : 'descending',
    }
  } else {
    sortInfo.value = null
  }
  // 重置到第一页并重新加载
  pagination.value.page = 1
  fetchList()
}

// フィルターリセット
const resetFilter = () => {
  filters.value = {
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1,
    destination_cd: '',
    keyword: '',
  }
  pagination.value.page = 1
  sortInfo.value = null // 清除排序
  fetchList()
}

// 新規受注追加ダイアログを開く
const handleAddOrder = () => {
  addForm.value = {
    destination_cd: '',
    destination_name: '',
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1,
    product_cd: '',
    product_name: '',
    product_type: '',
    product_alias: '',
    forecast_units: 0,
    forecast_total_units: 0,
  }
  addDialogVisible.value = true
}

// 新規受注を保存
const handleSaveAddOrder = async () => {
  try {
    await addFormRef.value.validate()

    // order_idを生成
    const orderId = `${addForm.value.year}${String(addForm.value.month).padStart(2, '0')}${addForm.value.destination_cd}${addForm.value.product_cd}`

    // order_idが存在するかチェック
    const exists = await checkMonthlyOrderExists(orderId)

    if (exists) {
      ElMessage.warning('同じ受注IDが既に存在します。追加できません。')
      return
    }

    // 保存
    await createMonthlyOrder({
      ...addForm.value,
      order_id: orderId,
    })

    ElMessage.success('登録成功！')
    addDialogVisible.value = false
    fetchList()
  } catch (error: any) {
    console.error('handleSaveAddOrderエラー', error)
    ElMessage.error(error.message || '登録失敗しました')
  }
}

// ✏️ 編集用ダイアログ
const editDialogVisible = ref(false)
const editForm = ref<OrderMonthly>({
  id: undefined,
  destination_cd: '',
  destination_name: '',
  year: new Date().getFullYear(),
  month: new Date().getMonth() + 1,
  product_cd: '',
  product_name: '',
  product_type: '',
  product_alias: '',
  forecast_units: 0,
  forecast_total_units: 0,
})
const editFormRef = ref()
const forecastUnitsInputRef = ref()
const handleEditOrder = async (row: OrderMonthly) => {
  editForm.value = { ...row }
  editDialogVisible.value = true
  await nextTick()
  if (forecastUnitsInputRef.value?.focus) {
    forecastUnitsInputRef.value.focus()
  } else if (forecastUnitsInputRef.value?.$el) {
    const inputEl = forecastUnitsInputRef.value.$el.querySelector('input')
    inputEl?.focus()
  }
}
// ✏️ 編集データ保存
const handleSaveEditOrder = async () => {
  await editFormRef.value.validate()
  if (!editForm.value.id) {
    ElMessage.error('編集対象が正しくありません')
    return
  }
  await updateMonthlyOrder(editForm.value.id, editForm.value)
  ElMessage.success('更新成功！')
  editDialogVisible.value = false
  fetchList()
}

// 🗑️ 削除ボタン押下時 - 优化版使用order_id
const handleDeleteOrder = async (row: OrderMonthly) => {
  try {
    const confirmMessage = `
      <div style="text-align: left; line-height: 1.6;">
        <p><strong>削除対象：</strong></p>
        <p>🆔 注文ID: <code style="background: #f0f0f0; padding: 2px 4px; border-radius: 3px;">${row.order_id}</code></p>
        <p>🏢 納入先: ${row.destination_name}</p>
        <p>📦 製品: ${row.product_name}</p>
        <p>📅 期間: ${row.year}年${row.month}月</p>
        <br/>
        <p style="color: #e74c3c; font-weight: bold;">⚠️ この操作により以下のデータが削除されます：</p>
        <ul style="margin: 8px 0; padding-left: 20px;">
          <li>月別受注データ (1件)</li>
          <li>関連する日別受注データ (複数件の可能性)</li>
        </ul>
        <p style="color: #666; font-size: 13px;">※ この操作は元に戻せません</p>
      </div>
    `

    await ElMessageBox.confirm(confirmMessage, '受注データ削除確認', {
      confirmButtonText: '削除実行',
      cancelButtonText: 'キャンセル',
      type: 'warning',
      dangerouslyUseHTMLString: true,
      customClass: 'delete-confirmation-dialog',
      distinguishCancelAndClose: true,
    })

    // 新しいorder_idで削除するAPIを使用
    const result = await deleteMonthlyOrderByOrderId(row.order_id || '')

    // 削除結果を表示
    const deletedInfo = result?.data
    if (deletedInfo) {
      ElMessage.success({
        message: `削除完了！月訂注 1件、関連日訂注 ${deletedInfo.deletedDailyOrders || 0}件を削除しました`,
        duration: 4000,
      })
    } else {
      ElMessage.success('削除成功！')
    }

    fetchList()
  } catch (error: any) {
    if (error !== 'cancel' && error !== 'close') {
      console.error('削除失敗:', error)
      ElMessage.error(error?.message || '削除に失敗しました')
    }
  }
}

// 📈 テーブル合計行計算
const getSummaries = ({ columns, data }: { columns: any[]; data: OrderMonthly[] }) => {
  const sums: (string | VNode)[] = []
  columns.forEach((column, index) => {
    if (index === 0) {
      sums[index] = '合計'
      return
    }

    const prop = column.property

    const formatNumber = (value: number | undefined): string => {
      if (typeof value !== 'number') return ''
      return value.toLocaleString('ja-JP')
    }

    if (prop === 'forecast_units') {
      // 製品名に「加工」を含む品種を除外
      const total = data
        .filter((cur) => !cur.product_name || !cur.product_name.includes('加工'))
        .reduce((acc, cur) => acc + (cur.forecast_units || 0), 0)
      sums[index] = formatNumber(total)
    } else if (prop === 'forecast_total_units') {
      // 製品名に「加工」を含む品種を除外
      const total = data
        .filter((cur) => !cur.product_name || !cur.product_name.includes('加工'))
        .reduce((acc, cur) => acc + (cur.forecast_total_units || 0), 0)
      sums[index] = formatNumber(total)
    } else if (prop === 'forecast_diff') {
      // 製品名に「加工」を含む品種を除外
      const total = data
        .filter((cur) => !cur.product_name || !cur.product_name.includes('加工'))
        .reduce((acc, cur) => acc + (cur.forecast_diff || 0), 0)

      // 🎨 h()を使用して色付きVNodeをレンダリング
      const color = total < 0 ? '#e74c3c' : total > 0 ? '#2ecc71' : '#606266'

      sums[index] = h(
        'span',
        {
          style: {
            color,
            fontWeight: total !== 0 ? 'bold' : 'normal',
          },
        },
        formatNumber(total),
      )
    } else {
      sums[index] = ''
    }
  })

  return sums
}

// 📅 前の月ボタン押下時
const handlePrevMonth = () => {
  if (!filters.value.month) {
    filters.value.month = 1
  }
  if (filters.value.month === 1) {
    filters.value.month = 12
    filters.value.year!--
  } else {
    filters.value.month!--
  }
  fetchList()
}

// 📅 次の月ボタン押下時
const handleNextMonth = () => {
  if (!filters.value.month) {
    filters.value.month = 1
  }
  if (filters.value.month === 12) {
    filters.value.month = 1
    filters.value.year!++
  } else {
    filters.value.month!++
  }
  fetchList()
}

// 📅 今月に戻る
const goToCurrentMonth = () => {
  const now = new Date()
  filters.value.year = now.getFullYear()
  filters.value.month = now.getMonth() + 1
  fetchList()
}

// 🔍 検索クリア
// 🔄 フィルタリセット
const resetFilters = () => {
  const now = new Date()
  filters.value.year = now.getFullYear()
  filters.value.month = now.getMonth() + 1
  filters.value.destination_cd = ''
  filters.value.keyword = ''
  selectedDestination.value = null
  fetchList()
}

// 🔥 一括登録ダイアログ
const batchDialogVisible = ref(false)

// 一括登録ダイアログを開く
const openBatchDialog = async () => {
  // 如果destinationOptions还没有加载，则加载它
  if (destinationOptions.value.length === 0) {
    try {
      destinationOptions.value = await getDestinationOptions()
    } catch (error) {
      ElMessage.error('納入先一覧取得に失敗しました')
      return
    }
  }
  // 一括用にコピー（已加载的数据直接使用）
  batchDestinationOptions.value = [...destinationOptions.value]
  batchDialogVisible.value = true
}

// 🔥 一括登録用のフォーム
const batchForm = ref({
  year: new Date().getFullYear(),
  month: new Date().getMonth() + 1,
  destination_cd: '',
  destination_name: '',
})

// 一括登録ダイアログの月ナビゲーション
const handleBatchPrevMonth = () => {
  if (batchForm.value.month === 1) {
    batchForm.value.month = 12
    batchForm.value.year -= 1
  } else {
    batchForm.value.month -= 1
  }
}

const handleBatchNextMonth = () => {
  if (batchForm.value.month === 12) {
    batchForm.value.month = 1
    batchForm.value.year += 1
  } else {
    batchForm.value.month += 1
  }
}

const handleBatchCurrentMonth = () => {
  const now = new Date()
  batchForm.value.year = now.getFullYear()
  batchForm.value.month = now.getMonth() + 1
}

const isBatchCurrentMonth = computed(() => {
  const now = new Date()
  return batchForm.value.year === now.getFullYear() && batchForm.value.month === now.getMonth() + 1
})

// 🔥 納入先オプション
const batchDestinationOptions = ref<Destination[]>([])

// 年オプション
// 使用共享的 yearOptions
const batchYearOptions = yearOptions

// 🔥 取得した製品一覧
interface BatchProduct {
  product_cd: string
  product_name: string
  product_type: string
  quantity: string | number // 修改类型以允许字符串输入
  exists: boolean
}
const batchProducts = ref<BatchProduct[]>([])

// 🔥 読込中フラグ
const batchLoading = ref(false)

// 🔥 製品一覧読込
const fetchProducts = async () => {
  if (!batchForm.value.destination_cd) {
    ElMessage.warning('納入先を選択してください')
    return
  }

  batchLoading.value = true
  try {
    // APIを呼び出して製品一覧を取得
    const response = await getProductsByDestination(
      batchForm.value.destination_cd,
      batchForm.value.year,
      batchForm.value.month,
    )

    // APIレスポンスデータ構造を処理
    let products: any[] = []
    if (response && Array.isArray(response)) {
      products = response
    } else if (
      response &&
      typeof response === 'object' &&
      'data' in response &&
      Array.isArray((response as any).data)
    ) {
      products = (response as any).data
    } else {
      ElMessage.warning('対象製品が存在しません')
      return
    }

    if (products.length === 0) {
      ElMessage.warning('対象製品が存在しません')
      return
    }

    // 製品タイプでフィルタリング（補給品と試作品を除外）
    const excludedTypes = ['補給品', '試作品']
    const filteredProducts = products.filter((product: any) => {
      const productType = product.product_type || ''
      return !excludedTypes.includes(productType)
    })

    if (filteredProducts.length === 0) {
      ElMessage.warning('対象製品が存在しません（補給品・試作品を除く）')
      batchProducts.value = []
      return
    }

    // 製品データを処理
    batchProducts.value = filteredProducts
      .sort((a: any, b: any) => (a.product_name || '').localeCompare(b.product_name || ''))
      .map(mapProductForDisplay)

    // 取得した製品数を表示
    ElMessage.success(`${batchProducts.value.length}件の製品データを取得しました`)

    // 各製品の存在状態をチェック
    await checkAllProductsExists()
  } catch (error) {
    console.error('製品一覧取得エラー:', error)
    ElMessage.error('製品一覧取得に失敗しました')
    batchProducts.value = []
  } finally {
    batchLoading.value = false
  }
}

// 🔥 すべての製品の存在状態を一括チェック
const checkAllProductsExists = async () => {
  if (batchProducts.value.length === 0) return

  try {
    // 納入先名称を取得
    const selectedDestination = batchDestinationOptions.value.find(
      (item) => item.cd === batchForm.value.destination_cd,
    )
    if (selectedDestination) {
      batchForm.value.destination_name = selectedDestination.name
    }

    console.log('製品存在状態のチェックを開始、製品数:', batchProducts.value.length)

    // すべての製品の存在状態を並行チェック - 新しい組み合わせチェックAPIを使用
    const checkPromises = batchProducts.value.map(async (product, index) => {
      try {
        console.log(
          `製品チェック ${index + 1}/${batchProducts.value.length}: ${product.product_cd}`,
        )

        // 新しい組み合わせチェックAPIを使用
        const exists = await checkCombinationExists(
          batchForm.value.destination_name,
          product.product_name,
          batchForm.value.year,
          batchForm.value.month,
        )

        // 元のオブジェクトのプロパティを直接変更
        batchProducts.value[index].exists = exists

        console.log(`製品 ${product.product_cd} 存在状態: ${exists}`)
        return { product_cd: product.product_cd, exists, index }
      } catch (error) {
        console.error(`製品 ${product.product_cd} 存在状態チェック失敗:`, error)
        batchProducts.value[index].exists = false // エラー時はデフォルトで存在しないとする
        return {
          product_cd: product.product_cd,
          exists: false,
          error: (error as Error).message,
          index,
        }
      }
    })

    const results = await Promise.all(checkPromises)
    console.log('製品存在状態チェック完了:', results)

    // リアクティブ更新を強制トリガー
    batchProducts.value = [...batchProducts.value]

    nextTick(() => {
      console.log(
        '状态检测完成，当前产品状态:',
        batchProducts.value.map((p) => ({
          product_cd: p.product_cd,
          exists: p.exists,
        })),
      )
    })
  } catch (error) {
    console.error('製品存在状態の一括チェック失敗:', error)
    // エラーをスローせず、製品一覧を表示し続ける
  }
}

// 🔥 一括登録処理（0と空値を許可、確認ダイアログなし、保存後に閉じる）
const handleBatchRegister = async () => {
  if (!batchForm.value.destination_cd || batchProducts.value.length === 0) {
    ElMessage.warning('納入先と製品情報を入力してください')
    return
  }

  // 存在状態を再チェック
  await checkAllProductsExists()

  // 登録が必要な製品をフィルタリング（存在しないすべての製品、数量が0または空のものを含むが、製品タイプが'補給品'の製品は除外）
  const newProducts = batchProducts.value.filter((p) => !p.exists && p.product_type !== '補給品')

  if (newProducts.length === 0) {
    // 除外された理由を統計
    const alreadyExists = batchProducts.value.filter((p) => p.exists).length
    const excludedSupplies = batchProducts.value.filter(
      (p) => !p.exists && p.product_type === '補給品',
    ).length

    let message = '登録するデータがありません'
    if (alreadyExists > 0 && excludedSupplies > 0) {
      message += `（${alreadyExists}件は登録済み、${excludedSupplies}件は補給品のため除外）`
    } else if (alreadyExists > 0) {
      message += '（すべて登録済みです）'
    } else if (excludedSupplies > 0) {
      message += '（すべて補給品のため除外されました）'
    }

    ElMessage.info(message)
    return
  }

  try {
    // 直接保存、確認ダイアログなし
    const result = await batchCreateMonthlyOrders({
      year: batchForm.value.year,
      month: batchForm.value.month,
      destination_cd: batchForm.value.destination_cd,
      destination_name: batchForm.value.destination_name,
      products: newProducts.map((p) => ({
        product_cd: p.product_cd,
        product_name: p.product_name,
        product_type: p.product_type || '',
        forecast_units: (() => {
          // 数量を処理：空文字列、null、undefinedはすべて0に変換
          if (p.quantity === '' || p.quantity === null || p.quantity === undefined) {
            return 0
          }
          const quantity = typeof p.quantity === 'string' ? parseFloat(p.quantity) : p.quantity
          return isNaN(quantity) ? 0 : quantity
        })(),
      })),
    })

    // APIが返した結果を処理
    if (result && typeof result === 'object' && 'inserted' in result) {
      const { inserted, total, skipped, message } = result as any
      ElMessage.success(message || `${inserted}件のデータを登録しました！`)
      console.log(`登録結果: ${inserted}件登録, ${skipped}件スキップ, 全${total}件`)
    } else {
      ElMessage.success(`${newProducts.length}件のデータを登録しました！`)
    }

    // メインリストを更新
    fetchList()

    // ダイアログを直接閉じる
    batchProducts.value = []
    batchDialogVisible.value = false
  } catch (error) {
    console.error('登録失敗', error)
    ElMessage.error('登録に失敗しました')
  }
}

// 月別受注から日別受注を生成
const generating = ref(false)
const generateProgressPercentage = ref(0)
const generateProgressStatus = ref<'success' | 'exception' | 'warning' | undefined>(undefined)
// 🚀 轮询检查任务状态的 interval ID
let taskStatusPollInterval: NodeJS.Timeout | null = null

const handleGenerateDailyOrders = async () => {
  try {
    // 月が有効かチェック
    if (!filters.value.year || !filters.value.month) {
      ElMessage.warning('有効な年月を選択してください')
      return
    }

    generating.value = true
    generateProgressPercentage.value = 0
    generateProgressStatus.value = undefined

    // 🚀 清理之前的轮询（如果有）
    if (taskStatusPollInterval) {
      clearInterval(taskStatusPollInterval)
      taskStatusPollInterval = null
    }

    // 🚀 优化：更智能的进度更新，模拟真实进度
    let progressStep = 0
    const progressInterval = setInterval(() => {
      if (generateProgressPercentage.value < 90) {
        // 前90%快速更新，后10%慢速更新
        if (generateProgressPercentage.value < 70) {
          generateProgressPercentage.value += 5
        } else {
          generateProgressPercentage.value += 2
        }
        progressStep++
      }
    }, 500) // 每500ms更新一次

    try {
      await generateDailyOrders({
        year: filters.value.year,
        month: filters.value.month,
        productType: '量産品', // 製品タイプが量産品のレコードのみ生成
      })

      clearInterval(progressInterval)
      // 🚀 清理任务状态轮询（如果存在）
      if (taskStatusPollInterval) {
        clearInterval(taskStatusPollInterval)
        taskStatusPollInterval = null
      }

      generateProgressPercentage.value = 100
      generateProgressStatus.value = 'success'

      // 何が返されても成功を表示（バックエンドの実行は既に成功しているため）
      ElMessage.success('量産品のみの日受注生成成功！')
      fetchList()

      // 延迟隐藏进度条
      setTimeout(() => {
        generating.value = false
        generateProgressPercentage.value = 0
        generateProgressStatus.value = undefined
      }, 1000)
    } catch (error: any) {
      clearInterval(progressInterval)

      // 🚀 优化：处理超时和网络错误，不中断处理
      const isTimeout =
        error.code === 'ECONNABORTED' ||
        error.message?.includes('timeout') ||
        error.message?.includes('タイムアウト')

      const isNetworkError =
        error.code === 'ERR_NETWORK' ||
        error.message?.includes('Network Error') ||
        error.message?.includes('ネットワークエラー') ||
        (error.response === undefined && error.request !== undefined)

      if (isTimeout || isNetworkError) {
        // 超时或网络错误但不中断：显示提示，保持进度条，提示后台正在处理
        generateProgressPercentage.value = 95
        generateProgressStatus.value = 'warning'

        const errorType = isTimeout ? 'タイムアウト' : 'ネットワークエラー'
        ElMessage.warning({
          message: `日受注生成処理で${errorType}が発生しましたが、バックエンドで処理が継続中です。しばらくお待ちください。処理完了後、データを自動更新します。`,
          duration: 15000, // 15秒显示
          showClose: true,
        })

        // 不隐藏进度条，让用户知道还在处理
        console.warn(
          `日受注生成で${errorType}が発生しましたが、バックエンド処理は継続中です`,
          error,
        )

        // 🚀 优化：添加轮询机制，定期检查任务是否完成
        let pollCount = 0
        const maxPollCount = 60 // 最多轮询60次（5分钟）
        const pollInterval = 5000 // 每5秒检查一次

        // 清理之前的轮询（如果有）
        if (taskStatusPollInterval) {
          clearInterval(taskStatusPollInterval)
          taskStatusPollInterval = null
        }

        taskStatusPollInterval = setInterval(async () => {
          pollCount++
          console.log(`タスク状態を確認中... (${pollCount}/${maxPollCount})`)

          try {
            // 刷新列表，检查是否有新的日订单数据
            await fetchList()

            // 如果列表更新成功，可能处理已完成
            if (taskStatusPollInterval) {
              clearInterval(taskStatusPollInterval)
              taskStatusPollInterval = null
            }
            generateProgressPercentage.value = 100
            generateProgressStatus.value = 'success'

            ElMessage.success({
              message: '日受注生成処理が完了しました！',
              duration: 5000,
            })

            // 延迟隐藏进度条
            setTimeout(() => {
              generating.value = false
              generateProgressPercentage.value = 0
              generateProgressStatus.value = undefined
            }, 2000)
          } catch (e) {
            console.error('リスト更新失敗:', e)

            // 如果达到最大轮询次数，停止轮询
            if (pollCount >= maxPollCount) {
              if (taskStatusPollInterval) {
                clearInterval(taskStatusPollInterval)
                taskStatusPollInterval = null
              }
              ElMessage.info({
                message:
                  '長時間処理が継続しています。手動でデータを更新して処理状態を確認してください。',
                duration: 10000,
              })

              // 最终隐藏进度条
              setTimeout(() => {
                generating.value = false
                generateProgressPercentage.value = 0
                generateProgressStatus.value = undefined
              }, 5000)
            }
          }
        }, pollInterval)

        // 如果用户关闭页面或组件卸载，清理轮询
        // 注意：这里需要在组件卸载时清理，但当前代码结构可能需要调整
      } else {
        // 其他错误：正常处理
        generateProgressPercentage.value = 100
        generateProgressStatus.value = 'exception'
        throw error
      }
    }
  } catch (error: any) {
    // 只有非超时错误才会到达这里（超时错误已经在内部catch中处理）
    console.error('日別受注生成時にエラーが発生:', error)

    // 检查是否是超时错误（虽然应该已经在内部处理了，但双重检查）
    const isTimeout =
      error.code === 'ECONNABORTED' ||
      error.message?.includes('timeout') ||
      error.message?.includes('タイムアウト')

    // 超时错误已经在上面处理了，这里只处理其他错误
    if (!isTimeout) {
      ElMessage.error('日受注生成失敗: ' + (error.message || '不明なエラー'))

      // 延迟隐藏进度条以显示错误状态
      setTimeout(() => {
        generating.value = false
        generateProgressPercentage.value = 0
        generateProgressStatus.value = undefined
      }, 2000)
    }
    // 如果是超时错误，已经在内部catch中处理，不需要再次处理
  }
}

// 内示本数更新処理
const updatingForecast = ref(false)
const updateForecastProgressVisible = ref(false)
const updateForecastProgressPercentage = ref(0)
const updateForecastProgressStatus = ref<'success' | 'exception' | 'warning' | undefined>(undefined)
const updateForecastProgressText = ref('処理を開始しています...')
const updateForecastCurrent = ref(0)
const updateForecastTotal = ref(0)
const updateForecastStats = ref({
  updated: 0,
  cleared: 0,
})

const handleUpdateForecastUnits = async () => {
  if (updatingForecast.value) return

  updatingForecast.value = true
  updateForecastProgressVisible.value = true
  updateForecastProgressPercentage.value = 0
  updateForecastProgressStatus.value = undefined
  updateForecastProgressText.value = '日次受注データを取得中...'
  updateForecastCurrent.value = 0
  updateForecastTotal.value = 0
  updateForecastStats.value = { updated: 0, cleared: 0 }

  const today = dayjs()
  const errors: string[] = []
  let totalUpdated = 0
  let totalCleared = 0

  try {
    // 日次受注データを取得
    updateForecastProgressText.value = '日次受注データを取得中...'

    const dailyOrdersParams = {
      page: 1,
      pageSize: 10000,
      all: true,
    }

    const dailyOrdersRes = await fetchDailyOrders(dailyOrdersParams)
    let allDailyOrders: OrderDaily[] = []

    // 处理返回的数据结构
    if (dailyOrdersRes && dailyOrdersRes.data) {
      if (Array.isArray(dailyOrdersRes.data.list)) {
        allDailyOrders = dailyOrdersRes.data.list
      } else if (Array.isArray(dailyOrdersRes.data)) {
        allDailyOrders = dailyOrdersRes.data
      }
    } else if (dailyOrdersRes && Array.isArray(dailyOrdersRes.list)) {
      allDailyOrders = dailyOrdersRes.list
    } else if (Array.isArray(dailyOrdersRes)) {
      allDailyOrders = dailyOrdersRes
    }

    if (allDailyOrders.length === 0) {
      ElMessage.info('更新対象の日次受注がありません')
      updateForecastProgressVisible.value = false
      updatingForecast.value = false
      return
    }

    // ========== 第一步：过去31天到未来31天，confirmed_units > 0 → forecast_units = confirmed_units ==========
    updateForecastProgressText.value = 'ステップ1: 内示本数を更新中...'
    const step1StartDate = today.subtract(31, 'day')
    const step1EndDate = today.add(31, 'day')

    const step1FilteredList = allDailyOrders.filter((row) => {
      if (!row.delivery_date) return false
      try {
        const deliveryDate = dayjs(row.delivery_date)
        if (!deliveryDate.isValid()) return false
        return (
          (deliveryDate.isAfter(step1StartDate) || deliveryDate.isSame(step1StartDate, 'day')) &&
          (deliveryDate.isBefore(step1EndDate) || deliveryDate.isSame(step1EndDate, 'day'))
        )
      } catch {
        return false
      }
    })

    if (step1FilteredList.length > 0) {
      updateForecastTotal.value = step1FilteredList.length
      const step1Updates: OrderDailyUpdate[] = []

      step1FilteredList.forEach((row, index) => {
        if (index % 10 === 0 || index === step1FilteredList.length - 1) {
          updateForecastCurrent.value = index + 1
          const progress = Math.round(((index + 1) / step1FilteredList.length) * 50) // 第一步占50%进度
          updateForecastProgressPercentage.value = progress
          updateForecastProgressText.value = `ステップ1: 内示本数を更新中... (${index + 1}/${step1FilteredList.length})`
        }

        const confirmedUnits = Number(row.confirmed_units ?? 0)
        // 条件1: confirmed_units > 0 → forecast_units = confirmed_units
        if (confirmedUnits > 0) {
          step1Updates.push({
            id: Number(row.id),
            forecast_units: confirmedUnits,
            confirmed_boxes: Number(row.confirmed_boxes ?? 0),
            confirmed_units: confirmedUnits,
            status: row.status ?? '未出荷',
            remarks: row.remarks ?? '',
          })
        }
      })

      // 第一步批量更新
      if (step1Updates.length > 0) {
        updateForecastProgressText.value = 'ステップ1: データを保存中...'
        const batchSize = 100
        const totalBatches = Math.ceil(step1Updates.length / batchSize)

        for (let i = 0; i < step1Updates.length; i += batchSize) {
          const batch = step1Updates.slice(i, i + batchSize)
          const currentBatch = Math.floor(i / batchSize) + 1
          const saveProgress = Math.round((currentBatch / totalBatches) * 25) // 第一步保存占25%进度
          updateForecastProgressPercentage.value = 25 + saveProgress
          updateForecastProgressText.value = `ステップ1: データを保存中... (${currentBatch}/${totalBatches})`

          try {
            await batchUpdateDailyOrders({ list: batch })
            totalUpdated += batch.length
          } catch (error) {
            const errorMsg = `ステップ1バッチ更新に失敗: ${
              error instanceof Error ? error.message : '不明なエラー'
            }`
            errors.push(errorMsg)
            console.error(errorMsg, error)
          }
        }
        updateForecastStats.value.updated = totalUpdated
      }
    }

    // ========== 第二步：过去31天到今天，confirmed_units = 0（或空值） && forecast_units > 0 → forecast_units = 空值 ==========
    updateForecastProgressText.value = 'ステップ2: 内示本数をクリア中...'
    const step2StartDate = today.subtract(31, 'day')
    const step2EndDate = today

    const step2FilteredList = allDailyOrders.filter((row) => {
      if (!row.delivery_date) return false
      try {
        const deliveryDate = dayjs(row.delivery_date)
        if (!deliveryDate.isValid()) return false
        return (
          (deliveryDate.isAfter(step2StartDate) || deliveryDate.isSame(step2StartDate, 'day')) &&
          (deliveryDate.isBefore(step2EndDate) || deliveryDate.isSame(step2EndDate, 'day'))
        )
      } catch {
        return false
      }
    })

    if (step2FilteredList.length > 0) {
      updateForecastTotal.value = step2FilteredList.length
      const step2Updates: OrderDailyUpdate[] = []

      step2FilteredList.forEach((row, index) => {
        if (index % 10 === 0 || index === step2FilteredList.length - 1) {
          updateForecastCurrent.value = index + 1
          const progress = 50 + Math.round(((index + 1) / step2FilteredList.length) * 50) // 第二步占50%进度
          updateForecastProgressPercentage.value = progress
          updateForecastProgressText.value = `ステップ2: 内示本数をクリア中... (${index + 1}/${step2FilteredList.length})`
        }

        // 检查 confirmed_units 是否为 0 或空值（null, undefined, '', 0）
        const confirmedUnitsValue = row.confirmed_units
        const isConfirmedUnitsEmpty =
          confirmedUnitsValue === null ||
          confirmedUnitsValue === undefined ||
          (typeof confirmedUnitsValue === 'string' && confirmedUnitsValue === '') ||
          Number(confirmedUnitsValue) === 0

        const confirmedUnits = isConfirmedUnitsEmpty ? 0 : Number(confirmedUnitsValue)
        const forecastUnits = Number(row.forecast_units ?? 0)

        // 条件2: confirmed_units = 0（或空值） && forecast_units > 0 → forecast_units = null（空值）
        if (isConfirmedUnitsEmpty && forecastUnits > 0) {
          step2Updates.push({
            id: Number(row.id),
            forecast_units: null as any, // 设置为 null 表示空值（数据库中的空值）
            confirmed_boxes: Number(row.confirmed_boxes ?? 0),
            confirmed_units: confirmedUnits,
            status: row.status ?? '未出荷',
            remarks: row.remarks ?? '',
          })
        }
      })

      // 第二步批量更新
      if (step2Updates.length > 0) {
        updateForecastProgressText.value = 'ステップ2: データを保存中...'
        const batchSize = 100
        const totalBatches = Math.ceil(step2Updates.length / batchSize)

        for (let i = 0; i < step2Updates.length; i += batchSize) {
          const batch = step2Updates.slice(i, i + batchSize)
          const currentBatch = Math.floor(i / batchSize) + 1
          const saveProgress = Math.round((currentBatch / totalBatches) * 25) // 第二步保存占25%进度
          updateForecastProgressPercentage.value = 75 + saveProgress
          updateForecastProgressText.value = `ステップ2: データを保存中... (${currentBatch}/${totalBatches})`

          try {
            await batchUpdateDailyOrders({ list: batch })
            totalCleared += batch.length
          } catch (error) {
            const errorMsg = `ステップ2バッチ更新に失敗: ${
              error instanceof Error ? error.message : '不明なエラー'
            }`
            errors.push(errorMsg)
            console.error(errorMsg, error)
          }
        }
        updateForecastStats.value.cleared = totalCleared
      }
    }

    // ========== 第三步：过去31天到各产品confirmed_boxes > 0的最后日期，confirmed_units = 0（或空值） && forecast_units > 0 → forecast_units = 空值 ==========
    updateForecastProgressText.value = 'ステップ3: 製品別に内示本数をクリア中...'
    const step3StartDate = today.subtract(31, 'day')

    // 按产品分组，找到每个产品confirmed_boxes > 0的最后日期
    const productGroups = new Map<
      string,
      { rows: OrderDaily[]; lastPositiveBoxDate: dayjs.Dayjs | null }
    >()

    // 先按产品分组所有数据
    allDailyOrders.forEach((row) => {
      if (!row.delivery_date) return
      const productKey = `${row.destination_cd || ''}_${row.product_cd || ''}_${row.product_name || ''}`

      if (!productGroups.has(productKey)) {
        productGroups.set(productKey, { rows: [], lastPositiveBoxDate: null })
      }

      const group = productGroups.get(productKey)!
      group.rows.push(row)
    })

    // 对每个产品组，找到confirmed_boxes > 0的最后日期
    productGroups.forEach((group, productKey) => {
      let lastDate: dayjs.Dayjs | null = null

      // 按日期排序（从新到旧）
      const sortedRows = [...group.rows].sort((a, b) => {
        const dateA = dayjs(a.delivery_date)
        const dateB = dayjs(b.delivery_date)
        return dateB.isAfter(dateA) ? 1 : -1
      })

      // 找到第一个confirmed_boxes > 0的日期（即最后一个）
      for (const row of sortedRows) {
        const confirmedBoxes = Number(row.confirmed_boxes ?? 0)
        if (confirmedBoxes > 0) {
          const deliveryDate = dayjs(row.delivery_date)
          if (deliveryDate.isValid()) {
            lastDate = deliveryDate
            break
          }
        }
      }

      group.lastPositiveBoxDate = lastDate
    })

    // 过滤出需要处理的数据：过去31天到各产品最后positive box日期
    const step3FilteredList: OrderDaily[] = []

    productGroups.forEach((group, productKey) => {
      if (!group.lastPositiveBoxDate) return // 如果没有找到positive box的日期，跳过该产品

      group.rows.forEach((row) => {
        if (!row.delivery_date) return
        try {
          const deliveryDate = dayjs(row.delivery_date)
          if (!deliveryDate.isValid()) return

          // 日期范围：过去31天到该产品最后positive box日期
          if (
            (deliveryDate.isAfter(step3StartDate) || deliveryDate.isSame(step3StartDate, 'day')) &&
            (deliveryDate.isBefore(group.lastPositiveBoxDate!) ||
              deliveryDate.isSame(group.lastPositiveBoxDate!, 'day'))
          ) {
            step3FilteredList.push(row)
          }
        } catch {
          // 忽略无效日期
        }
      })
    })

    if (step3FilteredList.length > 0) {
      updateForecastTotal.value = step3FilteredList.length
      const step3Updates: OrderDailyUpdate[] = []
      let step3ClearedCount = 0

      step3FilteredList.forEach((row, index) => {
        if (index % 10 === 0 || index === step3FilteredList.length - 1) {
          updateForecastCurrent.value = index + 1
          // 第三步占剩余进度（从75%到100%，即25%）
          const progress = 75 + Math.round(((index + 1) / step3FilteredList.length) * 12.5) // 处理占12.5%
          updateForecastProgressPercentage.value = progress
          updateForecastProgressText.value = `ステップ3: 製品別に内示本数をクリア中... (${index + 1}/${step3FilteredList.length})`
        }

        // 检查 confirmed_units 是否为 0 或空值
        const confirmedUnitsValue = row.confirmed_units
        const isConfirmedUnitsEmpty =
          confirmedUnitsValue === null ||
          confirmedUnitsValue === undefined ||
          (typeof confirmedUnitsValue === 'string' && confirmedUnitsValue === '') ||
          Number(confirmedUnitsValue) === 0

        const confirmedUnits = isConfirmedUnitsEmpty ? 0 : Number(confirmedUnitsValue)
        const forecastUnits = Number(row.forecast_units ?? 0)

        // 条件: confirmed_units = 0（或空值） && forecast_units > 0 → forecast_units = null（空值）
        if (isConfirmedUnitsEmpty && forecastUnits > 0) {
          step3Updates.push({
            id: Number(row.id),
            forecast_units: null as any, // 设置为 null 表示空值
            confirmed_boxes: Number(row.confirmed_boxes ?? 0),
            confirmed_units: confirmedUnits,
            status: row.status ?? '未出荷',
            remarks: row.remarks ?? '',
          })
          step3ClearedCount++
        }
      })

      // 第三步批量更新
      if (step3Updates.length > 0) {
        updateForecastProgressText.value = 'ステップ3: データを保存中...'
        const batchSize = 100
        const totalBatches = Math.ceil(step3Updates.length / batchSize)

        for (let i = 0; i < step3Updates.length; i += batchSize) {
          const batch = step3Updates.slice(i, i + batchSize)
          const currentBatch = Math.floor(i / batchSize) + 1
          const saveProgress = Math.round((currentBatch / totalBatches) * 12.5) // 第三步保存占12.5%进度
          updateForecastProgressPercentage.value = 87.5 + saveProgress // 75% + 12.5%处理 + 12.5%保存
          updateForecastProgressText.value = `ステップ3: データを保存中... (${currentBatch}/${totalBatches})`

          try {
            await batchUpdateDailyOrders({ list: batch })
            totalCleared += batch.length
          } catch (error) {
            const errorMsg = `ステップ3バッチ更新に失敗: ${
              error instanceof Error ? error.message : '不明なエラー'
            }`
            errors.push(errorMsg)
            console.error(errorMsg, error)
          }
        }
        updateForecastStats.value.cleared = totalCleared
      }
    }

    // 進捗を100%に設定
    updateForecastProgressPercentage.value = 100
    updateForecastProgressStatus.value = errors.length > 0 ? 'warning' : 'success'
    updateForecastProgressText.value = '処理が完了しました'

    // 結果を表示
    if (errors.length > 0) {
      ElMessage.warning(
        `${totalUpdated + totalCleared}件の内示本数を更新しましたが、${errors.length}件のエラーが発生しました`,
      )
      console.error('更新エラー:', errors)
    } else if (totalUpdated > 0 || totalCleared > 0) {
      ElMessage.success(
        `内示本数の更新が完了しました（更新: ${totalUpdated}件、クリア: ${totalCleared}件）`,
      )
    } else {
      ElMessage.info('更新対象のデータがありません')
    }

    // データを再読み込み
    await fetchList()
    await fetchSummary()

    // 2秒後に進捗ダイアログを閉じる
    setTimeout(() => {
      updateForecastProgressVisible.value = false
    }, 2000)
  } catch (error) {
    console.error('内示本数更新失敗', error)
    updateForecastProgressStatus.value = 'exception'
    updateForecastProgressText.value = '処理中にエラーが発生しました'
    ElMessage.error('内示本数の更新に失敗しました')
    setTimeout(() => {
      updateForecastProgressVisible.value = false
    }, 3000)
  } finally {
    updatingForecast.value = false
  }
}

//日订单全部同意编辑
const batchEditDialogVisible = ref(false)
const batchEditMonthlyOrderId = ref<string | ''>('')

const handleBatchEdit = (monthlyOrderId: string) => {
  batchEditMonthlyOrderId.value = monthlyOrderId
  batchEditDialogVisible.value = true
}

// 🔥 批量检查存在改为 Promise.all
const checkBatchProductsExists = async () => {
  const checkPromises = batchProducts.value.map(async (product) => {
    try {
      const exists = await checkCombinationExists(
        batchForm.value.destination_name,
        product.product_name,
        batchForm.value.year,
        batchForm.value.month,
      )
      product.exists = exists
    } catch (error) {
      console.error(`检查产品 ${product.product_cd} 存在状态失败:`, error)
      product.exists = false
    }
  })
  await Promise.all(checkPromises)
}

// 数量入力欄のEnterキーを処理
const handleQuantityEnter = (currentIndex: number) => {
  // 最後の入力欄でない場合、次の入力欄に移動
  if (currentIndex < batchProducts.value.length - 1) {
    // DOMが更新されるまで遅延実行
    setTimeout(() => {
      try {
        // document.getElementByIdを使用してより確実に要素を検索
        const nextInputId = `quantity-input-${currentIndex + 1}`
        const nextInputEl = document.getElementById(nextInputId)

        if (nextInputEl) {
          const inputField = nextInputEl.querySelector('.el-input__inner') as HTMLInputElement
          if (inputField) {
            inputField.focus()
            inputField.select()
            return
          }
        }

        // 代替案：querySelectorAllを使用してすべての入力欄を検索
        const allInputs = document.querySelectorAll('.batch-product-table .el-input__inner')
        if (allInputs.length > currentIndex + 1) {
          ;(allInputs[currentIndex + 1] as HTMLInputElement).focus()
        }
      } catch (err) {
        console.error('次の入力欄への移動時にエラーが発生:', err)
      }
    }, 50)
  }
}

// 数量変更を処理し、リアルタイムで状態を更新
const handleQuantityChange = (row: BatchProduct, index: number) => {
  // 状態チェックを遅延実行し、頻繁な呼び出しを回避
  setTimeout(async () => {
    if (row.product_cd && batchForm.value.destination_cd && batchForm.value.destination_name) {
      try {
        const exists = await checkCombinationExists(
          batchForm.value.destination_name,
          row.product_name,
          batchForm.value.year,
          batchForm.value.month,
        )
        row.exists = exists
      } catch (error) {
        console.error(`检查产品 ${row.product_cd} 存在状态失败:`, error)
      }
    }
  }, 300)
}

// 入力欄がフォーカスを取得した際の処理
const handleFocus = (event: any) => {
  // 値が0の場合、入力欄をクリア
  if (event.target.value === '0') {
    event.target.value = ''
  }
}

// map時に0を空文字列に変換
const mapProductForDisplay = (p: any) => {
  return {
    product_cd: p.product_cd,
    product_name: p.product_name,
    product_type: p.product_type || '', // デフォルト値を確保
    quantity: p.forecast_units > 0 ? p.forecast_units : '',
    exists: false, // 初期状態、checkAllProductsExistsで更新される
  }
}

// 製品タイプに応じて異なるタグタイプを返す
const getProductTypeTagType = (
  productType: string,
): 'primary' | 'success' | 'warning' | 'danger' | 'info' => {
  if (!productType) return 'info'

  // 異なる製品タイプに応じて異なる色を返す
  // 実際のニーズに応じて色の割り当てを調整可能
  const typeMap: Record<string, 'primary' | 'success' | 'warning' | 'danger' | 'info'> = {
    量産品: 'success',
    試作品: 'warning',
    その他: 'danger',
    代替品: 'danger',
    補給品: 'info',
    サンプル品: 'primary',
    別注品: 'warning',
    返却品: 'danger',
  }

  return typeMap[productType] || 'info'
}

// 根据製品CD最末尾数字返回颜色类型
const getProductCdTagType = (
  productCd: string,
): 'primary' | 'success' | 'warning' | 'danger' | 'info' => {
  if (!productCd) return 'info'

  // 获取最末尾的数字
  const lastChar = productCd.slice(-1)
  const lastDigit = parseInt(lastChar, 10)

  // 如果不是数字，返回默认颜色
  if (isNaN(lastDigit)) return 'info'

  // 根据末尾数字（0-9）返回不同的颜色类型
  const colorMap: Record<number, 'primary' | 'success' | 'warning' | 'danger' | 'info'> = {
    0: 'info',
    1: 'primary',
    2: 'success',
    3: 'warning',
    4: 'danger',
    5: 'info',
    6: 'primary',
    7: 'success',
    8: 'warning',
    9: 'danger',
  }

  return colorMap[lastDigit] || 'info'
}

// 受注情報一括更新ダイアログ
const updateFieldsDialogVisible = ref(false)
const updateFieldsForm = ref({
  startDate: new Date(),
  updateProductInfo: true,
})
const updateFieldsLoading = ref(false)

// 受注情報一括更新ダイアログを開く
const openUpdateFieldsDialog = () => {
  updateFieldsForm.value = {
    startDate: new Date(),
    updateProductInfo: true,
  }
  updateFieldsDialogVisible.value = true
}

// 一括更新を実行
const handleUpdateFields = async () => {
  if (!updateFieldsForm.value.startDate) {
    ElMessage.warning('開始日を選択してください')
    return
  }

  try {
    await ElMessageBox.confirm(
      '選択した日付以降の受注情報を一括更新します。この操作は元に戻せません。続行しますか？',
      '確認',
      {
        confirmButtonText: 'はい',
        cancelButtonText: 'いいえ',
        type: 'warning',
      },
    )

    updateFieldsLoading.value = true

    const startDate = new Date(updateFieldsForm.value.startDate)
    const formattedDate = `${startDate.getFullYear()}-${String(startDate.getMonth() + 1).padStart(2, '0')}-${String(startDate.getDate()).padStart(2, '0')}`

    const response = await updateOrderFields({
      startDate: formattedDate,
      updateProductInfo: updateFieldsForm.value.updateProductInfo,
    })

    console.log('API response:', response) // デバッグ用

    // updatedCountフィールドに正しくアクセス、様々な可能なレスポンス構造を考慮
    const updatedCount = response?.data?.updatedCount || 0

    ElMessage.success(`更新成功！${updatedCount}件のデータを更新しました`)
    updateFieldsDialogVisible.value = false
    fetchList()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('更新失敗', error)
      ElMessage.error(error.message || '更新に失敗しました')
    }
  } finally {
    updateFieldsLoading.value = false
  }
}

const productTypeOptions = [
  '量産品',
  '試作品',
  '補給品',
  '代替品',
  '別注品',
  'サンプル品',
  'その他',
  '返却品',
]

// 日別受注管理関連変数
const dailyOrderDialogVisible = ref(false)
const dailyOrderForm = ref({
  date: dayjs().format('YYYY-MM-DD'), // デフォルトは今日
  destination_cd: '',
})
const dailyOrdersList = ref<OrderDaily[]>([])
const dailyOrdersLoading = ref(false)
const dailyOrdersSaving = ref(false)
const dailyConfirmedBoxesInputs = ref<(HTMLInputElement | undefined)[]>([])
const dailyConfirmedUnitsInputs = ref<(HTMLInputElement | undefined)[]>([])
const dailyChangedRows = ref<Set<number>>(new Set())

// 日付操作
const setDailyDate = (newDate: string) => {
  dailyOrderForm.value.date = newDate
  fetchDailyOrdersList() // 日付変更後に自動検索
}

const changeDay = (amount: number) => {
  const currentDate = dailyOrderForm.value.date || dayjs().format('YYYY-MM-DD')
  setDailyDate(dayjs(currentDate).add(amount, 'day').format('YYYY-MM-DD'))
}

const setToday = () => {
  setDailyDate(dayjs().format('YYYY-MM-DD'))
}

// 日受注管理 納入先選択
const destinationDialogVisible = ref(false)
const selectedDestination = ref<any>(null)
const destinationDialogCaller = ref<'main' | 'daily'>('main') // 'main' 或 'daily'

const openDestinationDialog = () => {
  destinationDialogCaller.value = 'daily'
  destinationDialogVisible.value = true
}

const selectedDailyDestinationName = computed(() => {
  if (!dailyOrderForm.value.destination_cd) return '納入先を選択'
  const dest = validDestinationOptions.value.find(
    (d) => d.cd === dailyOrderForm.value.destination_cd,
  )
  return dest ? `${dest.cd} | ${dest.name}` : '納入先を選択'
})

const selectDestination = (destinationCd: string) => {
  dailyOrderForm.value.destination_cd = destinationCd
  destinationDialogVisible.value = false
}

// 日別受注編集ダイアログを開く
const openDailyOrderDialog = () => {
  dailyOrderForm.value = {
    date: dayjs().format('YYYY-MM-DD'),
    destination_cd: '',
  }
  dailyOrdersList.value = []
  dailyChangedRows.value.clear()
  dailyOrderDialogVisible.value = true
}

// 日付表示をフォーマット
const formatDateDisplay = (year: number, month: number, day: number): string => {
  return `${year}/${String(month).padStart(2, '0')}/${String(day).padStart(2, '0')}`
}

// 日付をフォーマット
const formatDate = (dateString: string | null | undefined): string => {
  if (!dateString) return '-'
  try {
    const date = new Date(dateString)
    return `${date.getMonth() + 1}/${date.getDate()}`
  } catch (e) {
    return dateString.toString()
  }
}

// 日別受注リストを取得
const fetchDailyOrdersList = async () => {
  if (!dailyOrderForm.value.date) {
    ElMessage.warning('日付を選択してください')
    return
  }

  dailyOrdersLoading.value = true
  try {
    // 日付を解析して年月日を取得
    const dateParts = dailyOrderForm.value.date.split('-')
    const year = parseInt(dateParts[0])
    const month = parseInt(dateParts[1])
    const day = parseInt(dateParts[2])

    const params = {
      specificDate: dailyOrderForm.value.date,
      destination_cd: dailyOrderForm.value.destination_cd,
      page: 1,
      pageSize: 1000,
    }

    const res = await fetchDailyOrders(params)
    console.log('日受注データ取得結果:', res)

    // より柔軟にデータ構造を処理
    let listData: OrderDaily[] = []
    if (res && res.data && Array.isArray(res.data.list)) {
      listData = res.data.list
    } else if (res && Array.isArray(res.list)) {
      listData = res.list
    } else if (res && res.data && Array.isArray(res.data)) {
      listData = res.data
    } else if (Array.isArray(res)) {
      listData = res
    }

    console.log('抽出したリストデータ:', listData.length, '件のレコード')
    // 製品名でソート（日本語対応）
    listData.sort((a: any, b: any) =>
      (a?.product_name || '').localeCompare(b?.product_name || '', 'ja'),
    )
    dailyOrdersList.value = listData
    dailyChangedRows.value.clear()

    // 初期化後に最初の入力欄にフォーカス
    await nextTick()
    if (dailyOrdersList.value.length > 0) {
      const firstInput = document.querySelector('.daily-orders-table .el-input__inner')
      if (firstInput) {
        ;(firstInput as HTMLInputElement).focus()
      }
    }
  } catch (error) {
    console.error('日受注データ取得失敗', error)
    ElMessage.error('日受注データの取得に失敗しました')
    dailyOrdersList.value = []
  } finally {
    dailyOrdersLoading.value = false
  }
}

// 確定箱数変更を処理
const handleDailyConfirmedBoxesChange = (row: OrderDaily) => {
  const unitPerBox = row.unit_per_box ?? 0
  row.confirmed_units = unitPerBox > 0 ? row.confirmed_boxes * unitPerBox : row.confirmed_boxes
  markDailyRowChanged(row)
}

// 行が変更されたことをマーク
const markDailyRowChanged = (row: OrderDaily) => {
  if (row.id) dailyChangedRows.value.add(Number(row.id))
}

// Enterキーで次の入力欄にフォーカス（確定箱数）
const focusDailyNextInput = async (currentIndex: number) => {
  await nextTick()
  const nextInput = dailyConfirmedBoxesInputs.value[currentIndex + 1]
  if (nextInput) {
    nextInput.focus()
    nextInput.select()
  }
}

// Enterキーで次の入力欄にフォーカス（確定本数）
const focusDailyNextConfirmedUnitsInput = async (currentIndex: number) => {
  await nextTick()
  const nextInput = dailyConfirmedUnitsInputs.value[currentIndex + 1]
  if (nextInput) {
    nextInput.focus()
    nextInput.select()
  }
}

// 曜日のスタイルクラスを取得
const getWeekdayClass = (weekday: string) => {
  switch (weekday) {
    case '土':
      return 'weekday-saturday'
    case '日':
      return 'weekday-sunday'
    default:
      return 'weekday-normal'
  }
}

// 日別受注の変更を保存
const handleDailyOrdersSave = async () => {
  if (dailyOrdersSaving.value) return
  if (dailyChangedRows.value.size === 0) {
    ElMessage.warning('変更されたデータがありません')
    return
  }

  dailyOrdersSaving.value = true
  try {
    const updates: OrderDailyUpdate[] = dailyOrdersList.value
      .filter((row) => {
        const id = Number(row.id)
        return Number.isInteger(id) && id > 0 && dailyChangedRows.value.has(id)
      })
      .map((row) => ({
        id: Number(row.id),
        forecast_units: Number(row.forecast_units ?? 0),
        confirmed_boxes: Number(row.confirmed_boxes ?? 0),
        confirmed_units: Number(row.confirmed_units ?? 0),
        status: row.status ?? '未出荷',
        remarks: row.remarks ?? '',
      }))

    if (updates.length === 0) {
      ElMessage.warning('送信データがありません')
      return
    }

    await batchUpdateDailyOrders({ list: updates })

    ElMessage.success('一括保存成功しました！')
    dailyChangedRows.value.clear()
    await fetchDailyOrdersList() // データを再読み込み
  } catch (error) {
    console.error('一括保存失敗', error)
    const errorMessage = error instanceof Error ? error.message : '保存に失敗しました'
    ElMessage.error(errorMessage)
  } finally {
    dailyOrdersSaving.value = false
  }
}

// 日別受注テーブル集計計算
const getDailySummaries = ({ columns, data }: { columns: any[]; data: OrderDaily[] }) => {
  const sums: (string | VNode)[] = []
  columns.forEach((column, index) => {
    if (index === 0) {
      sums[index] = '合計'
      return
    }

    const prop = column.property

    if (prop === 'confirmed_boxes') {
      // 確定箱数合計
      const total = data.reduce((acc, cur) => acc + (cur.confirmed_boxes || 0), 0)
      sums[index] = formatNumber(total)
    } else if (prop === 'confirmed_units') {
      // 確定本数合計 - 計算ロジックを修正
      let total = 0

      // reduceではなくループを使用し、異なる計算状況を処理しやすくする
      for (const item of data) {
        if (item.confirmed_units && item.confirmed_units > 0) {
          // 確定本数が既にある場合、直接使用
          total += item.confirmed_units
        } else if (item.confirmed_boxes > 0 && item.unit_per_box && item.unit_per_box > 0) {
          // 確定本数がないが、確定箱数と入数がある場合、計算して取得
          total += item.confirmed_boxes * (item.unit_per_box || 0)
        }
      }

      sums[index] = formatNumber(total)
    } else if (prop === 'forecast_units') {
      // 内示本数合計
      const total = data.reduce((acc, cur) => acc + (cur.forecast_units || 0), 0)
      sums[index] = formatNumber(total)
    } else {
      sums[index] = ''
    }
  })

  return sums
}

const fetchDestinations = async () => {
  try {
    destinationOptions.value = await getDestinationOptions()
  } catch (err: any) {
    ElMessage.error(err.message || '納入先一覧の取得に失敗しました')
  }
}

onMounted(async () => {
  try {
    // 并行加载数据，加快页面加载速度
    await Promise.all([fetchDestinations(), fetchList()])

    // ページ読み込みをシミュレート
    setTimeout(() => {
      pageLoading.value = false
    }, 1500)
  } catch (err) {
    console.error('onMounted error:', err)
  }
})

// コンポーネントアンマウント時にタイマーをクリーンアップ
onUnmounted(() => {
  // 🚀 清理任务状态轮询
  if (taskStatusPollInterval) {
    clearInterval(taskStatusPollInterval)
    taskStatusPollInterval = null
  }
})

const handleDestinationSelect = (destination: { value: string; label: string } | null) => {
  const destinationCd = destination ? destination.value : ''

  if (destinationDialogCaller.value === 'main') {
    filters.value.destination_cd = destinationCd
    fetchList()
  } else {
    dailyOrderForm.value.destination_cd = destinationCd
    fetchDailyOrdersList()
  }

  destinationDialogVisible.value = false
}

const getDestinationName = computed(() => {
  if (!filters.value.destination_cd) {
    return '全て選択'
  }
  const dest = destinationOptions.value.find((d) => d.cd === filters.value.destination_cd)
  return dest ? `${dest.cd} | ${dest.name}` : '不明な納入先'
})

const refreshData = () => {
  fetchList()
}

const dailyDestinationDialogVisible = ref(false)

const handleDailyDestinationSelect = (destination: { value: string; label: string } | null) => {
  dailyOrderForm.value.destination_cd = destination ? destination.value : ''
  dailyDestinationDialogVisible.value = false
  fetchList()
}

const openMainDestinationDialog = () => {
  destinationDialogCaller.value = 'main'
  destinationDialogVisible.value = true
}

// 日別受注管理 納入先クイック選択（名称でマッチ）
const quickSelectDailyDestination = (destinationName: string) => {
  const dest = validDestinationOptions.value.find((d) => d.name === destinationName)
  if (dest) {
    dailyOrderForm.value.destination_cd = dest.cd
    fetchDailyOrdersList()
  } else {
    ElMessage.warning(`納入先が見つかりません: ${destinationName}`)
  }
}

// 一括数量編集関連変数
const batchQuantityDialogVisible = ref(false)
const batchQuantityForm = ref({
  editTarget: 'filtered', // 'all', 'selected', 'filtered'
})
const batchEditData = ref<any[]>([])
const batchDataLoading = ref(false)
const batchQuantityUpdating = ref(false)
const selectedRows = ref<OrderMonthly[]>([])
const changedRows = ref<Set<number>>(new Set())
const batchEditInputs = ref<(HTMLInputElement | undefined)[]>([])

// 一括数量編集ダイアログを開く
const openBatchQuantityDialog = () => {
  batchQuantityForm.value = {
    editTarget: 'filtered',
  }
  batchEditData.value = []
  changedRows.value.clear()
  batchQuantityDialogVisible.value = true
}

// 編集対象の変更を処理
const handleEditTargetChange = () => {
  batchEditData.value = []
  changedRows.value.clear()
}

// 一括編集データを読み込み
const loadBatchEditData = async () => {
  batchDataLoading.value = true
  try {
    // 現在のフィルター条件で全ページのデータを取得
    const baseParams = {
      year: filters.value.year,
      month: filters.value.month,
      destination_cd: filters.value.destination_cd,
      keyword: filters.value.keyword,
    }

    // まず最初のページを取得して、総件数を確認
    const pageSize = 100 // 1ページあたりの件数
    const firstPageParams = {
      ...baseParams,
      page: 1,
      pageSize,
    }
    const firstResponse = await fetchMonthlyOrders(firstPageParams)
    const total = firstResponse.total || 0
    let targetData: OrderMonthly[] = [...(firstResponse.list || [])]

    // 総ページ数を計算
    const totalPages = Math.ceil(total / pageSize)

    // 2ページ目以降を取得
    if (totalPages > 1) {
      const promises: Promise<{ list: OrderMonthly[]; total: number }>[] = []
      for (let page = 2; page <= totalPages; page++) {
        promises.push(
          fetchMonthlyOrders({
            ...baseParams,
            page,
            pageSize,
          }),
        )
      }

      // すべてのページを並列で取得
      const responses = await Promise.all(promises)
      responses.forEach((response) => {
        if (response.list) {
          targetData = targetData.concat(response.list)
        }
      })
    }

    // 編集データを準備
    batchEditData.value = targetData.map((item) => ({
      ...item,
      edited_forecast_units: item.forecast_units || 0,
    }))

    changedRows.value.clear()
    ElMessage.success(`${batchEditData.value.length}件のデータを読み込みました`)
  } catch (error) {
    console.error('データ読み込み失敗:', error)
    ElMessage.error('データの読み込みに失敗しました')
  } finally {
    batchDataLoading.value = false
  }
}

// 行が変更されたことをマーク
const markRowChanged = (row: any) => {
  if (row.id) {
    const originalValue = row.forecast_units || 0
    const editedValue = row.edited_forecast_units || 0

    if (originalValue !== editedValue) {
      changedRows.value.add(row.id)
    } else {
      changedRows.value.delete(row.id)
    }
  }
}

// 行に変更があるかチェック
const isRowChanged = (row: any) => {
  return row.id && changedRows.value.has(row.id)
}

// 次の入力欄にフォーカス
const focusNextInput = async (currentIndex: number) => {
  await nextTick()
  const nextInput = batchEditInputs.value[currentIndex + 1]
  if (nextInput) {
    nextInput.focus()
  }
}

// 一括数量更新を実行
const executeBatchQuantityUpdate = async () => {
  if (changedRows.value.size === 0) {
    ElMessage.warning('変更されたデータがありません')
    return
  }

  try {
    await ElMessageBox.confirm(
      `${changedRows.value.size}件のデータを一括更新します。この操作は元に戻せません。続行しますか？`,
      '確認',
      {
        confirmButtonText: 'はい',
        cancelButtonText: 'いいえ',
        type: 'warning',
      },
    )

    batchQuantityUpdating.value = true

    // 更新データを準備
    const updates = batchEditData.value
      .filter((row) => isRowChanged(row))
      .map((row) => ({
        id: row.id,
        forecast_units: row.edited_forecast_units,
      }))

    if (updates.length === 0) {
      ElMessage.info('変更されたデータがありません')
      return
    }

    // 一括更新APIを呼び出し
    const response = await batchUpdateMonthlyQuantity({ updates })

    if (response.success) {
      ElMessage.success(response.message || `${updates.length}件の更新が成功しました`)

      // ダイアログを閉じる
      batchQuantityDialogVisible.value = false

      // 編集データをクリア
      batchEditData.value = []
      changedRows.value.clear()

      // メインページのデータを更新
      await fetchList()

      // 集計データを更新
      await fetchSummary()
    } else {
      ElMessage.error(response.message || '更新に失敗しました')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('批量更新失敗:', error)
      ElMessage.error(error.message || '更新に失敗しました')
    }
  } finally {
    batchQuantityUpdating.value = false
  }
}
</script>

<style scoped>
/* 页面背景和基础样式 */
.order-monthly-list-container {
  padding: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
}

.order-monthly-list-container::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background:
    radial-gradient(circle at 20% 20%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 40% 40%, rgba(120, 119, 198, 0.2) 0%, transparent 50%);
  animation: backgroundShift 20s ease-in-out infinite;
  pointer-events: none;
  z-index: 0;
}

@keyframes backgroundShift {
  0%,
  100% {
    opacity: 1;
  }

  50% {
    opacity: 0.8;
  }
}

/* 页面加载遮罩 */
.page-loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  animation: fadeOut 0.5s ease-in-out 1.2s forwards;
}

.loading-content {
  text-align: center;
  color: white;
}

.loading-spinner {
  position: relative;
  width: 80px;
  height: 80px;
  margin: 0 auto 5px;
}

.spinner-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 3px solid transparent;
  border-top: 3px solid rgba(255, 255, 255, 0.8);
  border-radius: 50%;
  animation: spin 1.2s linear infinite;
}

.spinner-ring:nth-child(2) {
  width: 60px;
  height: 60px;
  top: 10px;
  left: 10px;
  animation-delay: -0.4s;
  border-top-color: rgba(255, 255, 255, 0.6);
}

.spinner-ring:nth-child(3) {
  width: 40px;
  height: 40px;
  top: 20px;
  left: 20px;
  animation-delay: -0.8s;
  border-top-color: rgba(255, 255, 255, 0.4);
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

@keyframes fadeOut {
  to {
    opacity: 0;
    visibility: hidden;
  }
}

.loading-text {
  font-size: 18px;
  font-weight: 500;
  margin: 0;
  opacity: 0.9;
}

/* 页面元素进入动画 */
.animate-in {
  animation: slideInFromTop 0.8s ease-out 0.3s both;
}

.animate-in-delay-1 {
  animation: slideInFromLeft 0.8s ease-out 0.6s both;
}

.animate-in-delay-2 {
  animation: slideInFromRight 0.8s ease-out 0.9s both;
}

.animate-in-delay-3 {
  animation: slideInFromLeft 0.8s ease-out 1.2s both;
}

.animate-in-delay-4 {
  animation: slideInFromBottom 0.8s ease-out 1.5s both;
}

@keyframes slideInFromTop {
  from {
    opacity: 0;
    transform: translateY(-50px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideInFromLeft {
  from {
    opacity: 0;
    transform: translateX(-50px);
  }

  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slideInFromRight {
  from {
    opacity: 0;
    transform: translateX(50px);
  }

  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slideInFromBottom {
  from {
    opacity: 0;
    transform: translateY(50px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 页面头部 */
.page-header {
  position: relative;
  z-index: 1;
  margin-bottom: 6px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.15) 0%, rgba(255, 255, 255, 0.05) 100%);
  backdrop-filter: blur(20px);
  border-radius: 12px;
  padding: 8px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
}

.title-section {
  flex: 1;
}

.title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0 0 4px 0;
  color: white;
  font-size: 28px;
  font-weight: 700;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.title-icon {
  width: 55px;
  height: 55px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
  animation: iconPulse 3s ease-in-out infinite;
  position: relative;
  overflow: hidden;
}

.title-icon::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  animation: iconShine 4s ease-in-out infinite;
}

@keyframes iconPulse {
  0%,
  100% {
    transform: scale(1) rotate(0deg);
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
  }

  50% {
    transform: scale(1.08) rotate(2deg);
    box-shadow: 0 12px 35px rgba(102, 126, 234, 0.6);
  }
}

@keyframes iconShine {
  0%,
  100% {
    transform: translateX(-100%) translateY(-100%) rotate(45deg);
  }

  50% {
    transform: translateX(100%) translateY(100%) rotate(45deg);
  }
}

.title-icon .el-icon {
  font-size: 26px;
  color: white;
  z-index: 1;
  position: relative;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}

.title-badge {
  background: linear-gradient(135deg, #ff6b6b, #ee5a52);
  color: white;
  padding: 4px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4);
  animation: badgeFloat 3s ease-in-out infinite;
}

@keyframes badgeFloat {
  0%,
  100% {
    transform: translateY(0);
  }

  50% {
    transform: translateY(-5px);
  }
}

.subtitle {
  color: rgba(255, 255, 255, 0.8);
  font-size: 16px;
  margin: 0;
  font-weight: 400;
}

.header-decoration {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
}

.decoration-circle {
  position: absolute;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
  animation: float 6s ease-in-out infinite;
}

.circle-1 {
  width: 60px;
  height: 60px;
  top: -30px;
  right: 0;
  animation-delay: 0s;
}

.circle-2 {
  width: 45px;
  height: 45px;
  top: 15px;
  right: 45px;
  animation-delay: 2s;
}

.circle-3 {
  width: 30px;
  height: 30px;
  top: -5px;
  right: 90px;
  animation-delay: 4s;
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0) rotate(0deg);
  }

  50% {
    transform: translateY(-20px) rotate(180deg);
  }
}

/* 现代化卡片样式 */
.modern-card {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  margin-bottom: 4px;
}

.modern-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 45px rgba(0, 0, 0, 0.15);
}

/* 合计卡片 */
.summary-cards {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 6px;
  margin-bottom: 4px;
  position: relative;
  z-index: 1;
}

.summary-card {
  position: relative;
  overflow: hidden;
  padding: 0;
  border: none;
}

.summary-card :deep(.el-card__body) {
  padding: 8px 10px;
}

.card-content {
  display: flex;
  align-items: center;
  padding: 0;
  position: relative;
  z-index: 2;
}

.card-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.card-icon::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.6s ease;
}

.card-icon:hover::before {
  left: 100%;
}

.card-icon:hover {
  transform: translateY(-2px) scale(1.03);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
}

.info-icon {
  background: linear-gradient(135deg, #667eea, #764ba2);
  animation: infoGlow 3s ease-in-out infinite alternate;
}

.success-icon {
  background: linear-gradient(135deg, #56ab2f, #a8e6cf);
  animation: successGlow 3s ease-in-out infinite alternate;
}

.diff-icon {
  background: linear-gradient(135deg, #ff6b6b, #ee5a52);
  animation: diffGlow 3s ease-in-out infinite alternate;
}

.plating-icon {
  background: linear-gradient(135deg, #4facfe, #00f2fe);
  animation: platingGlow 3s ease-in-out infinite alternate;
}

.external-plating-icon {
  background: linear-gradient(135deg, #fa709a, #fee140);
  animation: externalPlatingGlow 3s ease-in-out infinite alternate;
}

.internal-welding-icon {
  background: linear-gradient(135deg, #34d399, #059669);
  animation: internalWeldingGlow 3s ease-in-out infinite alternate;
}

.external-welding-icon {
  background: linear-gradient(135deg, #fbbf24, #f97316);
  animation: externalWeldingGlow 3s ease-in-out infinite alternate;
}

@keyframes infoGlow {
  0% {
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3);
  }

  100% {
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5);
  }
}

@keyframes successGlow {
  0% {
    box-shadow: 0 6px 20px rgba(86, 171, 47, 0.3);
  }

  100% {
    box-shadow: 0 8px 25px rgba(86, 171, 47, 0.5);
  }
}

@keyframes diffGlow {
  0% {
    box-shadow: 0 6px 20px rgba(255, 107, 107, 0.3);
  }

  100% {
    box-shadow: 0 8px 25px rgba(255, 107, 107, 0.5);
  }
}

@keyframes platingGlow {
  0% {
    box-shadow: 0 6px 20px rgba(79, 172, 254, 0.3);
  }

  100% {
    box-shadow: 0 8px 25px rgba(79, 172, 254, 0.5);
  }
}

@keyframes externalPlatingGlow {
  0% {
    box-shadow: 0 6px 20px rgba(250, 112, 154, 0.3);
  }

  100% {
    box-shadow: 0 8px 25px rgba(250, 112, 154, 0.5);
  }
}

@keyframes internalWeldingGlow {
  0% {
    box-shadow: 0 6px 20px rgba(52, 211, 153, 0.3);
  }

  100% {
    box-shadow: 0 8px 25px rgba(5, 150, 105, 0.5);
  }
}

@keyframes externalWeldingGlow {
  0% {
    box-shadow: 0 6px 20px rgba(251, 191, 36, 0.3);
  }

  100% {
    box-shadow: 0 8px 25px rgba(249, 115, 22, 0.5);
  }
}

.card-icon .el-icon {
  font-size: 20px;
  color: white;
  z-index: 1;
  position: relative;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
  animation: iconFloat 2s ease-in-out infinite alternate;
}

@keyframes iconFloat {
  0% {
    transform: translateY(0px);
  }

  100% {
    transform: translateY(-2px);
  }
}

.card-info {
  flex: 1;
  min-width: 0;
}

.summary-title {
  font-size: 13px;
  color: #666;
  margin-bottom: 2px;
  font-weight: 500;
  line-height: 1.2;
}

.summary-value {
  font-size: 20px;
  font-weight: 700;
  color: #2c3e50;
  letter-spacing: 0.5px;
  line-height: 1.2;
}

.card-decoration {
  position: absolute;
  top: 0;
  right: 0;
  width: 100px;
  height: 100px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), transparent);
  border-radius: 0 20px 0 100px;
}

/* 操作按钮区域 */
.action-card {
  padding: 1px;
}

.action-card :deep(.el-card__body) {
  padding: 8px 12px;
}

.action-header {
  margin-bottom: 2px;
  padding: 0;
}

.action-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0;
}

.action-icon {
  font-size: 22px;
  color: #667eea;
  animation: actionIconPulse 2s ease-in-out infinite;
}

@keyframes actionIconPulse {
  0%,
  100% {
    color: #667eea;
    transform: scale(1);
  }

  50% {
    color: #764ba2;
    transform: scale(1.1);
  }
}

.button-group {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 0;
  padding: 0;
}

.action-button {
  margin: 0;
  flex-grow: 1;
  font-weight: 600;
  border: 2px solid transparent;
  color: #1f2937;
  /* 深色文字 */
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  padding: 8px 12px;
}

.action-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
}

.action-button .el-icon {
  font-size: 16px;
  transition: all 0.3s ease;
}

.action-button:hover .el-icon {
  transform: scale(1.1) rotate(-5deg);
}

.action-button::before {
  display: none;
  /* 移除闪光效果 */
}

.btn-add {
  border-color: #818cf8;
  background: linear-gradient(135deg, #f5f3ff, #eef2ff);
}

.btn-add .el-icon {
  color: #6366f1;
}

.btn-add:hover {
  border-color: #6366f1;
  background: linear-gradient(135deg, #eef2ff, #e0e7ff);
}

.btn-batch {
  border-color: #6ee7b7;
  background: linear-gradient(135deg, #f0fdf4, #dcfce7);
}

.btn-batch .el-icon {
  color: #22c55e;
}

.btn-batch:hover {
  border-color: #22c55e;
  background: linear-gradient(135deg, #dcfce7, #bbf7d0);
}

.btn-generate {
  border-color: #f9a8d4;
  background: linear-gradient(135deg, #fdf2f8, #fce7f3);
}

.btn-generate .el-icon {
  color: #ec4899;
}

.btn-generate:hover {
  border-color: #ec4899;
  background: linear-gradient(135deg, #fce7f3, #fbcfe8);
}

.generate-button-wrapper {
  display: flex;
  flex-direction: column;
  flex-grow: 1;
  gap: 8px;
}

.progress-bar-container {
  margin-top: 4px;
  padding: 0 4px;
}

.progress-bar-container :deep(.el-progress) {
  margin: 0;
}

.progress-bar-container :deep(.el-progress-bar__outer) {
  background-color: #e5e7eb;
  border-radius: 10px;
  overflow: hidden;
}

.progress-bar-container :deep(.el-progress-bar__inner) {
  border-radius: 10px;
  transition: width 0.3s ease;
}

.progress-bar-container :deep(.el-progress__text) {
  font-size: 14px;
  font-weight: 600;
  color: #2c3e50;
}

.btn-update-fields {
  border-color: #7dd3fc;
  background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
}

.btn-update-fields .el-icon {
  color: #0ea5e9;
}

.btn-update-fields:hover {
  border-color: #0ea5e9;
  background: linear-gradient(135deg, #e0f2fe, #bae6fd);
}

.btn-daily-manage {
  border-color: #fcd34d;
  background: linear-gradient(135deg, #fffbeb, #fef3c7);
}

.btn-daily-manage .el-icon {
  color: #f59e0b;
}

.btn-daily-manage:hover {
  border-color: #f59e0b;
  background: linear-gradient(135deg, #fef3c7, #fde68a);
}

.btn-batch-quantity {
  border-color: #a78bfa;
  background: linear-gradient(135deg, #faf5ff, #f3e8ff);
}

.btn-batch-quantity .el-icon {
  color: #8b5cf6;
}

.btn-batch-quantity:hover {
  border-color: #8b5cf6;
  background: linear-gradient(135deg, #f3e8ff, #e9d5ff);
}

.btn-update-forecast {
  border-color: #f59e0b;
  background: linear-gradient(135deg, #fffbeb, #fef3c7);
}

.btn-update-forecast .el-icon {
  color: #d97706;
}

.btn-update-forecast:hover {
  border-color: #d97706;
  background: linear-gradient(135deg, #fef3c7, #fde68a);
}

.btn-update-forecast:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 筛选卡片 */
.filter-card {
  padding: 0;
}

.filter-card :deep(.el-card__body) {
  padding: 8px 12px;
}

.filter-card.no-header :deep(.el-card__header) {
  display: none;
}

.filter-card.no-header :deep(.el-card__body) {
  padding: 8px 12px;
}

.filter-header-inline {
  margin-bottom: 3px;
  padding-bottom: 3px;
  border-bottom: 1px solid rgba(102, 126, 234, 0.1);
}

.filter-header {
  padding: 3px 5px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.filter-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.filter-icon {
  font-size: 20px;
  color: #667eea;
  animation: filterIconSpin 4s linear infinite;
}

@keyframes filterIconSpin {
  0% {
    transform: rotate(0deg);
    color: #667eea;
  }

  25% {
    transform: rotate(90deg);
    color: #764ba2;
  }

  50% {
    transform: rotate(180deg);
    color: #667eea;
  }

  75% {
    transform: rotate(270deg);
    color: #764ba2;
  }

  100% {
    transform: rotate(360deg);
    color: #667eea;
  }
}

.filter-form {
  padding: 0;
  margin-top: 0;
}

.filter-row {
  margin: 0;
  align-items: flex-end;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.filter-content :deep(.el-form-item) {
  margin-bottom: 0;
}

.filter-content :deep(.el-form-item__label) {
  padding: 0;
  margin: 0;
}

.modern-form-item {
  margin-bottom: 0;
}

.nav-form-item {
  margin-top: 5px;
  /* 对齐导航按钮到其他输入框底部 */
}

.modern-select,
.modern-input {
  width: 100%;
}

/* 特定宽度的选择器 */
.year-select {
  min-width: 100px;
}

.month-select {
  min-width: 90px;
}

.destination-select {
  min-width: 200px;
}

/* 納入先下拉框选项字体缩小，显示更多行 */
.destination-select :deep(.el-select-dropdown__item) {
  font-size: 11px;
  padding: 6px 8px;
  line-height: 1.4;
}

.destination-select :deep(.el-select-dropdown__list) {
  max-height: 400px;
}

.product-search {
  min-width: 180px;
}

.modern-select :deep(.el-input__inner),
.modern-input :deep(.el-input__inner) {
  border-radius: 8px;
  border: 2px solid #e1e8ed;
  transition: all 0.3s ease;
  padding: 10px 12px;
  font-size: 14px;
}

.modern-select :deep(.el-input__inner):focus,
.modern-input :deep(.el-input__inner):focus {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.month-nav-buttons {
  display: flex;
  gap: 8px;
}

.nav-button {
  flex: 1;
  padding: 5px 12px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 13px;
  transition: all 0.3s ease;
  min-width: 70px;
}

.prev-button {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
}

.next-button {
  background: linear-gradient(135deg, #f093fb, #f5576c);
  color: white;
  border: none;
}

.nav-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.search-icon {
  color: #667eea;
  animation: searchIconPulse 2s ease-in-out infinite;
}

@keyframes searchIconPulse {
  0%,
  100% {
    color: #667eea;
    transform: scale(1);
  }

  50% {
    color: #764ba2;
    transform: scale(1.1);
  }
}

/* 表格卡片 */
.table-card {
  padding: 0;
}

.table-card.no-header :deep(.el-card__header) {
  display: none;
}

.table-card.no-header :deep(.el-card__body) {
  padding: 10px 12px;
}

.table-header-inline {
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(102, 126, 234, 0.1);
}

.table-header {
  padding: 15px 20px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.table-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.table-icon {
  font-size: 18px;
  color: #667eea;
  animation: tableIconBounce 2s ease-in-out infinite;
}

@keyframes tableIconBounce {
  0%,
  20%,
  50%,
  80%,
  100% {
    transform: translateY(0);
    color: #667eea;
  }

  40% {
    transform: translateY(-8px);
    color: #764ba2;
  }

  60% {
    transform: translateY(-4px);
    color: #667eea;
  }
}

.count-badge {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 4px;
  box-shadow: 0 3px 8px rgba(102, 126, 234, 0.3);
  animation: badgeGlow 2s ease-in-out infinite alternate;
}

@keyframes badgeGlow {
  0% {
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    transform: scale(1);
  }

  100% {
    box-shadow: 0 6px 18px rgba(102, 126, 234, 0.5);
    transform: scale(1.02);
  }
}

.count-icon {
  font-size: 14px;
  animation: countIconRotate 3s ease-in-out infinite;
}

@keyframes countIconRotate {
  0%,
  100% {
    transform: rotate(0deg);
  }

  50% {
    transform: rotate(180deg);
  }
}

.table-wrapper {
  padding: 0;
  margin-top: 0;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.modern-table {
  border-radius: 15px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.modern-table :deep(.el-table__header) {
  background: linear-gradient(135deg, #f8faf9, #e9ecef);
}

.modern-table :deep(.el-table__header th) {
  background: transparent;
  color: #27292b;
  font-weight: 600;
  border-bottom: 2px solid #dee2e6;
  padding: 4px 6px;
  height: 32px;
}

.modern-table :deep(.el-table__body tr) {
  height: 32px;
}

.modern-table :deep(.el-table__body tr:hover) {
  background-color: rgba(102, 126, 234, 0.05);
}

.modern-table :deep(.el-table__body td) {
  padding: 3px 6px;
  border-bottom: 1px solid #f1f3f4;
}

/* 强制数值列右对齐 */
.modern-table :deep(.el-table__body td.is-right),
.modern-table :deep(.el-table__header th.is-right) {
  text-align: right !important;
}

.modern-table :deep(.el-table__body td.is-right .cell),
.modern-table :deep(.el-table__header th.is-right .cell) {
  text-align: right !important;
  display: flex !important;
  justify-content: flex-end !important;
}

/* 确保number-cell内的内容右对齐 */
.modern-table :deep(.el-table__body td.is-right .number-cell) {
  justify-content: flex-end !important;
  width: 100% !important;
  margin-left: auto;
  margin-right: 0;
}

/* 表格内字体统一（12px）：适用于现代表与日本简约表 */
.modern-table :deep(.el-table),
.modern-table :deep(.el-table th),
.modern-table :deep(.el-table td),
.modern-table :deep(.el-input__inner),
.modern-table :deep(.el-tag),
.modern-table :deep(.el-button),
.japanese-table :deep(.el-table),
.japanese-table :deep(.el-table th),
.japanese-table :deep(.el-table td),
.japanese-table :deep(.el-input__inner),
.japanese-table :deep(.el-tag),
.japanese-table :deep(.el-button) {
  font-size: 12px;
}

/* 确保表格内所有文本元素字体大小一致 */
.modern-table :deep(.el-table__body td),
.modern-table :deep(.el-table__body td span),
.modern-table :deep(.el-table__body td .number-value),
.modern-table :deep(.el-table__body td .diff-value-simple),
.modern-table :deep(.el-table__body td .destination-cell span) {
  font-size: 13px !important;
}

/* 表格单元格样式 */
.destination-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.location-icon {
  color: #667eea;
  font-size: 16px;
  animation: locationIconPulse 2s ease-in-out infinite alternate;
}

@keyframes locationIconPulse {
  0% {
    color: #667eea;
    transform: scale(1);
  }

  100% {
    color: #764ba2;
    transform: scale(1.1);
  }
}

.number-cell {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0;
  width: 100%;
  text-align: right;
  padding-right: 8px;
}

.number-value {
  font-weight: 700;
  color: #2c3e50;
  font-size: 12px;
  text-align: right;
}

.number-unit {
  font-size: 11px;
  color: #667eea;
  font-weight: 600;
  opacity: 0.8;
}

.diff-cell-new {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  width: 100%;
  text-align: right;
}

/* 内示差異字段样式 */
.diff-value-simple {
  font-weight: 700;
  font-size: 12px;
  transition: all 0.3s ease;
}

.diff-value-simple.diff-positive {
  color: #28a745;
}

.diff-value-simple.diff-negative {
  color: #dc3545;
}

.diff-value-simple.diff-zero {
  color: #6c757d;
}

.diff-value-simple:hover {
  transform: scale(1.1);
}

/* 表格操作按钮 */
.table-action-buttons {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 6px;
}

.compact-btn {
  width: 32px;
  height: 32px;
  padding: 0;
  border-radius: 8px;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.compact-btn .el-icon {
  font-size: 14px;
}

.compact-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.5s;
}

.compact-btn:hover::before {
  left: 100%;
}

.compact-btn:hover {
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.primary-btn {
  background: linear-gradient(135deg, #409eff, #337ecc);
  color: white;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}

.primary-btn:hover {
  background: linear-gradient(135deg, #337ecc, #409eff);
  box-shadow: 0 4px 15px rgba(64, 158, 255, 0.5);
}

.warning-btn {
  background: linear-gradient(135deg, #e6a23c, #d4922a);
  color: white;
  box-shadow: 0 2px 8px rgba(230, 162, 60, 0.3);
}

.warning-btn:hover {
  background: linear-gradient(135deg, #d4922a, #e6a23c);
  box-shadow: 0 4px 15px rgba(230, 162, 60, 0.5);
}

.danger-btn {
  background: linear-gradient(135deg, #f56c6c, #e85656);
  color: white;
  box-shadow: 0 2px 8px rgba(245, 108, 108, 0.3);
}

.danger-btn:hover {
  background: linear-gradient(135deg, #e85656, #f56c6c);
  box-shadow: 0 4px 15px rgba(245, 108, 108, 0.5);
}

.compact-btn:active {
  transform: translateY(0) scale(0.95);
}

/* 工具提示样式 */
.table-action-buttons :deep(.el-tooltip__trigger) {
  display: inline-block;
}

:deep(.el-tooltip__popper) {
  background: rgba(0, 0, 0, 0.8);
  color: white;
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 500;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(10px);
}

:deep(.el-tooltip__popper .el-popper__arrow::before) {
  background: rgba(0, 0, 0, 0.8);
  border: none;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  margin-top: 20px;
  color: #6c757d;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.03) 0%, rgba(118, 75, 162, 0.03) 100%);
  border-radius: 12px;
  border: 1px solid rgba(102, 126, 234, 0.1);
}

.empty-icon {
  font-size: 64px;
  color: #dee2e6;
  margin-bottom: 20px;
  animation: emptyIconFloat 3s ease-in-out infinite;
}

@keyframes emptyIconFloat {
  0%,
  100% {
    transform: translateY(0px) scale(1);
    color: #dee2e6;
  }

  50% {
    transform: translateY(-10px) scale(1.05);
    color: #c6c7c8;
  }
}

.empty-text {
  font-size: 18px;
  color: #6c757d;
  margin: 0;
  font-weight: 500;
  opacity: 0.8;
}

/* 分页器 */
.pagination-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0 0 0;
  margin-top: 6px;
  border-top: 1px solid rgba(102, 126, 234, 0.1);
}

.pagination-info {
  color: #6c757d;
  font-size: 12px;
}

.pagination-info .info-text {
  font-size: 12px;
}

.modern-pagination :deep(.el-pagination) {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.modern-pagination :deep(.el-pagination .el-pager li),
.modern-pagination :deep(.el-pagination .btn-prev),
.modern-pagination :deep(.el-pagination .btn-next),
.modern-pagination :deep(.el-pagination .el-pagination__sizes),
.modern-pagination :deep(.el-pagination .el-pagination__jump) {
  font-size: 12px;
}

.modern-pagination :deep(.el-pagination .el-pagination__sizes .el-select .el-input__inner),
.modern-pagination :deep(.el-pagination .el-pagination__jump .el-input__inner) {
  font-size: 12px;
  height: 28px;
  line-height: 28px;
}

.modern-pagination :deep(.el-pagination .el-pager li) {
  border-radius: 8px;
  transition: all 0.3s ease;
}

.modern-pagination :deep(.el-pagination .el-pager li:hover) {
  transform: translateY(-2px);
}

.modern-pagination :deep(.el-pagination .el-pager li.is-active) {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
}

/* 现代化对话框 */
.modern-dialog :deep(.el-dialog) {
  border-radius: 24px;
  box-shadow: 0 25px 80px rgba(0, 0, 0, 0.25);
  border: 1px solid rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(20px);
  overflow: hidden;
}

.modern-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 25px 30px;
  border-radius: 24px 24px 0 0;
  position: relative;
  overflow: hidden;
}

.modern-dialog :deep(.el-dialog__header)::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  animation: headerShine 3s ease-in-out infinite;
}

@keyframes headerShine {
  0%,
  100% {
    left: -100%;
  }

  50% {
    left: 100%;
  }
}

.modern-dialog :deep(.el-dialog__title) {
  color: white;
  font-weight: 700;
  font-size: 20px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  position: relative;
  z-index: 1;
}

.modern-dialog :deep(.el-dialog__headerbtn) {
  position: relative;
  z-index: 1;
}

.modern-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: white;
  font-size: 20px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.modern-dialog :deep(.el-dialog__headerbtn .el-dialog__close):hover {
  background: rgba(255, 255, 255, 0.2);
  transform: scale(1.1);
}

.modern-dialog :deep(.el-dialog__body) {
  padding: 30px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 250, 252, 0.95) 100%);
}

.modern-dialog :deep(.el-dialog__footer) {
  padding: 20px 30px 30px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 250, 252, 0.95) 100%);
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

/* 弹窗头部图标样式 */
.dialog-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.dialog-icon {
  font-size: 24px;
  color: rgb(10, 250, 50);
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  padding: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  animation: iconPulse 2s ease-in-out infinite alternate;
}

@keyframes iconPulse {
  0% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.4);
  }

  100% {
    transform: scale(1.05);
    box-shadow: 0 0 0 10px rgba(255, 255, 255, 0);
  }
}

.dialog-title {
  color: rgb(8, 8, 8);
  font-weight: 700;
  font-size: 20px;
  text-shadow: 0 2px 4px rgba(36, 168, 36, 0.3);
}

/* 不同类型弹窗的图标颜色 */
.add-dialog .dialog-icon {
  background: rgba(103, 194, 58, 0.3);
}

.edit-dialog .dialog-icon {
  background: rgba(255, 193, 7, 0.3);
}

.update-dialog .dialog-icon {
  background: rgba(255, 99, 132, 0.3);
}

.daily-manage-dialog .dialog-icon {
  background: rgba(54, 162, 235, 0.3);
}

/* 弹窗进入动画 */
.modern-dialog :deep(.el-dialog) {
  animation: dialogSlideIn 0.4s ease-out;
}

@keyframes dialogSlideIn {
  0% {
    opacity: 0;
    transform: translate(-50%, -60%) scale(0.8);
  }

  100% {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
  }
}

.modern-dialog :deep(.el-overlay) {
  animation: overlayFadeIn 0.3s ease-out;
}

@keyframes overlayFadeIn {
  0% {
    opacity: 0;
  }

  100% {
    opacity: 1;
  }
}

/* 表单项动画 */
.modern-dialog .form-body :deep(.el-form-item) {
  animation: formItemSlideIn 0.5s ease-out;
  animation-fill-mode: both;
}

.modern-dialog .form-body :deep(.el-form-item:nth-child(1)) {
  animation-delay: 0.1s;
}

.modern-dialog .form-body :deep(.el-form-item:nth-child(2)) {
  animation-delay: 0.15s;
}

.modern-dialog .form-body :deep(.el-form-item:nth-child(3)) {
  animation-delay: 0.2s;
}

.modern-dialog .form-body :deep(.el-form-item:nth-child(4)) {
  animation-delay: 0.25s;
}

.modern-dialog .form-body :deep(.el-form-item:nth-child(5)) {
  animation-delay: 0.3s;
}

.modern-dialog .form-body :deep(.el-form-item:nth-child(6)) {
  animation-delay: 0.35s;
}

.modern-dialog .form-body :deep(.el-form-item:nth-child(7)) {
  animation-delay: 0.4s;
}

.modern-dialog .form-body :deep(.el-form-item:nth-child(8)) {
  animation-delay: 0.45s;
}

@keyframes formItemSlideIn {
  0% {
    opacity: 0;
    transform: translateX(-20px);
  }

  100% {
    opacity: 1;
    transform: translateX(0);
  }
}

/* 按钮图标动画 */
.modern-dialog :deep(.el-dialog__footer .el-button .el-icon) {
  margin-right: 6px;
  transition: transform 0.3s ease;
}

.modern-dialog :deep(.el-dialog__footer .el-button):hover .el-icon {
  transform: scale(1.1);
}

/* 特殊弹窗样式增强 - 已整合到上方紧凑设计中 */

/* 弹窗表单美化 */
.modern-dialog .form-body {
  background: transparent;
}

.modern-dialog .form-body :deep(.el-form-item) {
  margin-bottom: 24px;
}

.modern-dialog .form-body :deep(.el-form-item__label) {
  color: #2c3e50;
  font-weight: 600;
  font-size: 14px;
}

.modern-dialog .form-body :deep(.el-input__wrapper) {
  border-radius: 12px;
  border: 2px solid #e1e8ed;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.modern-dialog .form-body :deep(.el-input__wrapper):hover {
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
}

.modern-dialog .form-body :deep(.el-input__wrapper.is-focus) {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.modern-dialog .form-body :deep(.el-select .el-input__wrapper) {
  border-radius: 12px;
}

.modern-dialog .form-body :deep(.el-input-number .el-input__wrapper) {
  border-radius: 12px;
}

.modern-dialog .form-body :deep(.el-date-editor .el-input__wrapper) {
  border-radius: 12px;
}

/* 弹窗按钮美化 */
.modern-dialog :deep(.el-dialog__footer .el-button) {
  padding: 12px 24px;
  border-radius: 12px;
  font-weight: 600;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.modern-dialog :deep(.el-dialog__footer .el-button)::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.5s;
}

.modern-dialog :deep(.el-dialog__footer .el-button):hover::before {
  left: 100%;
}

.modern-dialog :deep(.el-dialog__footer .el-button--primary) {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.modern-dialog :deep(.el-dialog__footer .el-button--primary):hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5);
}

.modern-dialog :deep(.el-dialog__footer .el-button:not(.el-button--primary)) {
  background: linear-gradient(135deg, #f8f9fa, #e9ecef);
  color: #6c757d;
  border: 2px solid #e1e8ed;
}

.modern-dialog :deep(.el-dialog__footer .el-button:not(.el-button--primary)):hover {
  background: linear-gradient(135deg, #e9ecef, #dee2e6);
  color: #495057;
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

/* 响应式设计 */
/* 大屏幕 (1200px以下) */
@media (max-width: 1200px) {
  .summary-cards {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  }

  /* 表格在中等屏幕上的优化 */
  .table-wrapper {
    overflow-x: auto;
  }

  .modern-table {
    min-width: 900px;
  }
}

@media (max-width: 768px) {
  .order-monthly-list-container {
    padding: 6px;
  }

  .page-header {
    padding: 8px;
    margin-bottom: 8px;
  }

  .title {
    font-size: 24px;
  }

  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }

  .summary-cards {
    grid-template-columns: 1fr;
    gap: 6px;
    margin-bottom: 8px;
  }

  .button-group {
    flex-direction: column;
    gap: 6px;
  }

  .action-button {
    width: 100%;
    justify-content: center;
  }

  .filter-row {
    flex-direction: column;
  }

  .filter-form {
    padding: 12px 15px;
  }

  .month-nav-buttons {
    flex-direction: column;
    gap: 6px;
  }

  .pagination-container {
    flex-direction: column;
    gap: 8px;
    padding: 4px 0 0 0;
    margin-top: 4px;
  }

  .pagination-info {
    font-size: 11px;
  }

  .modern-pagination :deep(.el-pagination) {
    font-size: 11px;
  }

  .modern-card {
    margin-bottom: 12px;
  }

  .table-action-buttons {
    gap: 4px;
    flex-wrap: wrap;
  }

  .compact-btn {
    width: 28px;
    height: 28px;
  }

  .compact-btn .el-icon {
    font-size: 12px;
  }

  /* 表格横向滚动优化 */
  .table-wrapper {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .modern-table {
    min-width: 800px;
  }
}

@media (max-width: 480px) {
  .title {
    font-size: 20px;
  }

  .card-content {
    padding: 12px;
  }

  .card-icon {
    width: 45px;
    height: 45px;
  }

  .card-icon .el-icon {
    font-size: 18px;
  }

  .summary-value {
    font-size: 18px;
  }

  .summary-title {
    font-size: 11px;
  }

  /* 操作按钮在超小屏幕上的优化 */
  .action-button {
    font-size: 12px;
    padding: 8px 12px;
  }

  .action-button .el-icon {
    font-size: 14px;
  }

  /* 表格在超小屏幕上的优化 */
  .modern-table {
    min-width: 700px;
    font-size: 11px;
  }

  .table-wrapper {
    margin: 0 -6px;
  }
}

/* 批量登录弹窗特殊样式 - 紧凑现代化设计 */
.batch-dialog :deep(.el-dialog__header) {
  padding: 10px 16px 8px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.batch-dialog .compact-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0;
}

.batch-dialog .dialog-icon {
  font-size: 16px;
  padding: 4px;
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.15), rgba(102, 126, 234, 0.15));
  border-radius: 6px;
}

.batch-dialog .dialog-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.batch-form-container {
  padding: 0;
}

.batch-form.compact-form {
  background: #fafbfc;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.06);
}

.compact-form-inner :deep(.el-form-item) {
  margin-bottom: 0;
}

.form-row-inline {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  flex-wrap: wrap;
  margin: 0;
}

/* 一括登録ダイアログのインラインフォーム */
.batch-form-inline {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  gap: 8px;
  margin: 0;
  padding: 0;
}

.batch-form-inline :deep(.el-form-item) {
  margin-bottom: 0;
  margin-right: 0;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
}

.batch-form-inline :deep(.el-form-item__label) {
  padding-right: 6px;
  margin-bottom: 0;
  white-space: nowrap;
  width: auto;
  min-width: auto;
  line-height: 28px;
  height: 28px;
}

.batch-form-inline :deep(.el-form-item__content) {
  margin-left: 0 !important;
  flex: 0 0 auto;
}

.batch-form-inline .inline-form-item.button-item {
  margin-left: auto;
}

.form-row-inline .inline-form-item {
  flex-shrink: 0;
  margin-bottom: 0 !important;
}

.form-row-inline .inline-form-item.flex-item {
  flex: 1;
  min-width: 200px;
}

.form-row-inline .inline-form-item.button-item {
  flex-shrink: 0;
  margin-left: auto;
}

.compact-form-inner :deep(.el-form-item__label) {
  color: #4b5563;
  font-weight: 500;
  font-size: 12px;
  padding-right: 6px;
  line-height: 28px;
  margin-bottom: 0;
}

.year-select,
.month-select,
.destination-select {
  width: 100%;
}

.batch-form-inline .year-select {
  width: 90px;
}

.batch-form-inline .month-select {
  width: 85px;
}

.batch-form-inline .destination-select {
  min-width: 180px;
  width: 180px;
}

.load-btn {
  background: linear-gradient(135deg, #409eff, #337ecc);
  border: none;
  color: white;
  padding: 6px 14px;
  border-radius: 6px;
  font-weight: 500;
  font-size: 12px;
  transition: all 0.2s ease;
  box-shadow: 0 2px 6px rgba(64, 158, 255, 0.25);
  height: 28px;
}

.load-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.35);
}

.table-container {
  margin-top: 10px;
}

.batch-product-table {
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(0, 0, 0, 0.06);
}

.batch-product-table :deep(.el-table__header) th {
  padding: 6px 8px;
  font-size: 12px;
}

.batch-product-table :deep(.el-table__body) td {
  padding: 6px 8px;
  font-size: 12px;
}

.batch-product-table :deep(.el-table__row) {
  height: 36px;
}

.dialog-footer-compact {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 8px 16px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}

.cancel-btn,
.register-btn {
  padding: 6px 16px;
  font-weight: 500;
  font-size: 12px;
  border-radius: 6px;
  transition: all 0.2s ease;
  height: 32px;
}

.register-btn {
  background: linear-gradient(135deg, #67c23a, #5daf34);
  border: none;
  color: white;
  box-shadow: 0 2px 8px rgba(103, 194, 58, 0.25);
}

.register-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(103, 194, 58, 0.35);
}

.batch-product-table :deep(.el-table__header) {
  background: #f8f9fa;
}

.batch-product-table :deep(.el-table__header-wrapper) {
  padding: 0;
}

.batch-product-table :deep(.el-table__body-wrapper) {
  padding: 0;
}

.batch-product-table :deep(.el-table__header th) {
  background: transparent;
  color: #374151;
  font-weight: 600;
  font-size: 12px;
  padding: 6px 8px;
  border-bottom: 1px solid #e5e7eb;
  line-height: 1.4;
}

.batch-product-table :deep(.el-table__body td) {
  padding: 6px 8px;
  font-size: 13px;
  line-height: 1.4;
}

.batch-product-table :deep(.el-table__body tr) {
  height: auto;
}

.batch-product-table :deep(.el-table__body tr:hover) {
  background-color: rgba(102, 126, 234, 0.04);
}

/* 表格内所有标签紧凑化 */
.batch-product-table :deep(.el-tag--small) {
  padding: 2px 6px;
  font-size: 11px;
  line-height: 1.3;
  height: auto;
  margin: 0;
}

.quantity-input {
  width: 100%;
  text-align: center;
}

.quantity-input :deep(.el-input__wrapper) {
  border-radius: 6px;
  text-align: center;
  padding: 2px 8px;
  min-height: 28px;
}

.quantity-input :deep(.el-input__inner) {
  text-align: center;
  font-size: 13px;
  font-weight: 500;
  line-height: 1.4;
  height: 24px;
}

.warning-cell :deep(.el-input__wrapper) {
  background-color: #fef2f2;
  border-color: #fca5a5;
}

.normal-cell :deep(.el-input__wrapper) {
  background-color: #f0fdf4;
  border-color: #86efac;
}

.empty-placeholder,
.loading-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px 16px;
  color: #6b7280;
  font-size: 12px;
  background: #f9fafb;
  border-radius: 6px;
  border: 1px dashed #d1d5db;
}

.compact-placeholder {
  padding: 16px 12px;
  margin-top: 0;
}

.loading-placeholder .el-icon {
  font-size: 24px;
  margin-bottom: 10px;
  color: #409eff;
  animation: loadingSpin 1.5s linear infinite;
}

@keyframes loadingSpin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

/* 批量弹窗表格行动画 */
.batch-product-table :deep(.el-table__body tr) {
  animation: tableRowSlideIn 0.4s ease-out;
  animation-fill-mode: both;
}

.batch-product-table :deep(.el-table__body tr:nth-child(odd)) {
  animation-delay: 0.05s;
}

.batch-product-table :deep(.el-table__body tr:nth-child(even)) {
  animation-delay: 0.1s;
}

@keyframes tableRowSlideIn {
  0% {
    opacity: 0;
    transform: translateX(-20px);
  }

  100% {
    opacity: 1;
    transform: translateX(0);
  }
}

/* 状态标签美化 - 紧凑设计 */
.batch-product-table :deep(.el-tag) {
  border-radius: 6px;
  font-weight: 500;
  font-size: 11px;
  padding: 2px 8px;
  border: none;
  transition: all 0.2s ease;
  line-height: 1.3;
  height: auto;
}

.batch-product-table :deep(.el-tag.status-tag) {
  min-width: 56px;
  text-align: center;
  font-weight: 500;
  letter-spacing: 0.3px;
}

.batch-product-table :deep(.el-tag.registered) {
  background: #ef4444 !important;
  color: white !important;
  border: none !important;
}

.batch-product-table :deep(.el-tag.unregistered) {
  background: #10b981 !important;
  color: white !important;
  border: none !important;
}

/* 鼠标悬停效果 */
.batch-product-table :deep(.el-tag.status-tag):hover {
  opacity: 0.9;
  transform: scale(1.02);
}

/* 对话框body优化 */
.batch-dialog :deep(.el-dialog__body) {
  padding: 10px 14px;
  max-height: calc(90vh - 100px);
  overflow-y: auto;
}

.daily-manage-dialog {
  margin-bottom: 0;
}

.daily-manage-dialog :deep(.el-dialog) {
  border-radius: 20px;
  box-shadow: 0 25px 80px rgba(0, 0, 0, 0.2);
}

.daily-manage-dialog :deep(.el-dialog__body) {
  padding: 12px 20px;
}

.daily-filter-form {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
  padding: 6px;
  font-size: 12px;
  border-radius: 8px;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  border: 1px solid rgba(102, 126, 234, 0.1);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
}

.daily-filter-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.daily-filter-form :deep(.el-form-item__label) {
  color: #2c3e50;
  font-weight: 600;
  font-size: 12px;
}

.daily-filter-form :deep(.el-input__wrapper),
.daily-filter-form :deep(.el-date-editor .el-input__wrapper) {
  border-radius: 10px;
  border: 2px solid #e1e8ed;
  transition: all 0.3s ease;
}

.daily-filter-form :deep(.el-input__inner) {
  font-size: 12px;
}

.daily-filter-form .push-right {
  margin-left: auto;
}

.daily-filter-form :deep(.el-input__wrapper):hover,
.daily-filter-form :deep(.el-date-editor .el-input__wrapper):hover {
  border-color: #667eea;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.15);
}

.daily-filter-form :deep(.el-button) {
  padding: 10px 10px;
  border-radius: 10px;
  font-weight: 600;
  transition: all 0.3s ease;
}

/* 納入先快捷按钮 - 简洁扁平 */
.daily-filter-form :deep(.quick-dest-btn) {
  background: #ffffff;
  border: 1px solid #d1d5db;
  color: #374151;
  font-size: 12px;
  padding: 6px 10px;
}

.daily-filter-form :deep(.quick-dest-btn:hover) {
  background: #f9fafb;
  border-color: #9ca3af;
}

.daily-filter-form :deep(.el-button--primary) {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.daily-filter-form :deep(.el-button--primary):hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

/* 一括保存按钮强化为绿色系，与検索区分 */
.daily-filter-form :deep(.save-cta) {
  background: linear-gradient(135deg, #10b981, #059669) !important;
  border: none !important;
  color: #ffffff !important;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25) !important;
}

.daily-filter-form :deep(.save-cta:hover) {
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(16, 185, 129, 0.35) !important;
}

.daily-orders-table {
  margin-top: 10px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.daily-orders-table :deep(.el-table__header) {
  background: linear-gradient(135deg, #f8f9fa, #e9ecef);
}

.daily-orders-table :deep(.el-table__header th) {
  background: transparent;
  color: #495057;
  font-weight: 600;
  border-bottom: 2px solid #dee2e6;
  padding: 8px 6px;
}

.daily-orders-table :deep(.el-table__body tr:hover) {
  background-color: rgba(102, 126, 234, 0.05);
}

.daily-orders-table :deep(.el-table__body td) {
  padding: 6px;
  border-bottom: 1px solid #f1f3f4;
}

.daily-orders-table :deep(.el-input__wrapper) {
  border-radius: 6px;
  border: 1px solid #e1e8ed;
  transition: all 0.3s ease;
}

.daily-orders-table :deep(.el-input__wrapper):focus-within {
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
}

.daily-orders-table :deep(.el-input__wrapper):hover {
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.15);
}

/* 响应式优化 */
@media (max-width: 768px) {
  .modern-dialog :deep(.el-dialog) {
    margin: 20px;
    width: calc(100% - 40px) !important;
    max-width: none;
  }

  .modern-dialog :deep(.el-dialog__body) {
    padding: 20px 15px;
  }

  .batch-form.compact-form {
    padding: 12px;
  }

  .form-row-inline {
    flex-direction: column;
    gap: 10px;
  }

  .form-row-inline .inline-form-item {
    width: 100%;
  }

  .form-row-inline .inline-form-item.button-item {
    margin-left: 0;
    width: 100%;
  }

  .form-row-inline .inline-form-item.button-item .load-btn {
    width: 100%;
  }

  .batch-dialog {
    width: 95% !important;
  }

  .batch-dialog :deep(.el-dialog__body) {
    padding: 12px 16px;
  }

  .daily-filter-form {
    padding: 15px;
    flex-direction: column;
    align-items: stretch;
  }

  .daily-filter-form :deep(.el-form-item) {
    margin-bottom: 15px;
  }
}

/* 日本简约风格对话框 */
.japanese-minimalist {
  --el-dialog-padding-primary: 6px;
}

.japanese-minimalist :deep(.el-dialog) {
  border-radius: 6px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  background: #ffffff;
  border: 1px solid #e0e0e0;
  overflow: hidden;
}

.japanese-minimalist :deep(.el-dialog__header) {
  padding: 6px 10px;
  background: #f5f5f5;
  margin: 0;
  border-bottom: 1px solid #e0e0e0;
}

.japanese-minimalist :deep(.el-dialog__body) {
  padding: 6px 10px;
  background: #ffffff;
}

.japanese-minimalist :deep(.el-dialog__footer) {
  padding: 6px 10px;
  background: #fafafa;
  border-top: 1px solid #e0e0e0;
}

/* 日本简约风格头部 */
.japanese-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0;
}

.japanese-icon {
  color: #555555;
  font-size: 16px;
  margin-right: 6px;
}

.japanese-title {
  color: #1f2937;
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.3px;
}

.japanese-badge {
  background: #f0f0f0;
  border: 1px solid #d0d0d0;
  border-radius: 3px;
  padding: 2px 6px;
}

.japanese-badge .badge-text {
  color: #666666;
  font-size: 11px;
  font-weight: 400;
}

/* 日本简约风格筛选表单 */
.japanese-filter-form {
  background: #f8f8f8;
  padding: 4px 6px;
  border-radius: 4px;
  margin-bottom: 4px;
  border: 1px solid #e0e0e0;
  box-shadow: none;
}

.japanese-filter-form.compact-filter {
  padding: 4px 6px;
  margin-bottom: 4px;
}

.japanese-filter-form :deep(.el-form-item) {
  margin-bottom: 0;
  margin-right: 6px;
}

.japanese-filter-form :deep(.el-form-item__label) {
  color: #4b5563;
  font-size: 11px;
  font-weight: 500;
  margin-right: 6px;
  padding-bottom: 0;
}

.japanese-filter-form :deep(.el-input__wrapper) {
  background: #ffffff;
  border: 1px solid #d1d5db;
  border-radius: 3px;
  box-shadow: none;
  transition: border-color 0.2s ease;
  padding: 0 8px;
  min-height: 24px;
}

.japanese-filter-form :deep(.el-input__wrapper:hover) {
  border-color: #9ca3af;
}

.japanese-filter-form :deep(.el-input__wrapper.is-focus) {
  border-color: #6b7280;
  box-shadow: 0 0 0 1px rgba(107, 114, 128, 0.1);
}

.japanese-filter-form :deep(.el-input__inner) {
  font-size: 11px;
  height: 24px;
  line-height: 24px;
}

.japanese-filter-form :deep(.el-button) {
  background: #ffffff;
  border: 1px solid #d1d5db;
  color: #374151;
  border-radius: 3px;
  font-size: 11px;
  padding: 4px 8px;
  height: 24px;
  transition: all 0.2s ease;
}

.japanese-filter-form :deep(.el-button:hover) {
  background: #f9fafb;
  border-color: #9ca3af;
}

.japanese-filter-form :deep(.el-button--primary) {
  background: #6b7280;
  border-color: #6b7280;
  color: #ffffff;
}

.japanese-filter-form :deep(.el-button--primary:hover) {
  background: #4b5563;
  border-color: #4b5563;
}

.japanese-filter-form :deep(.nav-day-btn) {
  padding: 4px 6px;
  font-size: 10px;
  height: 22px;
}

.japanese-filter-form :deep(.quick-dest-btn) {
  padding: 4px 8px;
  font-size: 10px;
  height: 22px;
  margin-right: 2px;
}

.japanese-filter-form :deep(.save-cta) {
  background: #4b5563 !important;
  border-color: #4b5563 !important;
  color: #ffffff !important;
  padding: 4px 10px;
  height: 24px;
  font-size: 11px;
}

.japanese-filter-form :deep(.save-cta:hover) {
  background: #374151 !important;
  border-color: #374151 !important;
}

/* 日本简约风格表格 */
.japanese-table {
  border-radius: 4px;
  overflow: hidden;
  box-shadow: none;
  border: 1px solid #e0e0e0;
}

.japanese-table.compact-table {
  margin-top: 4px;
}

.japanese-table :deep(.el-table__header) {
  background: #f5f5f5;
}

.japanese-table :deep(.el-table__header th) {
  background: transparent;
  color: #374151;
  font-weight: 600;
  border-bottom: 1px solid #e0e0e0;
  padding: 4px 4px;
  font-size: 11px;
  height: 28px;
}

.japanese-table :deep(.el-table__body tr) {
  background: #ffffff;
  height: 28px;
}

.japanese-table :deep(.el-table__body tr:hover) {
  background-color: #f9fafb;
}

.japanese-table :deep(.el-table__body tr:nth-child(even)) {
  background-color: #fafafa;
}

.japanese-table :deep(.el-table__body td) {
  padding: 2px 4px;
  border-bottom: 1px solid #f0f0f0;
  color: #1f2937;
  font-size: 11px;
  height: 28px;
}

/* 合计行加粗，字体维持11px */
.japanese-table :deep(.el-table__summary-row) {
  font-weight: 700 !important;
  font-size: 11px !important;
  background-color: #f5f5f5 !important;
}

.japanese-table :deep(.el-table__summary-row td) {
  font-weight: 700 !important;
  font-size: 11px !important;
  padding: 4px 4px !important;
  border-top: 1px solid #e0e0e0 !important;
}

.japanese-table :deep(.el-input__wrapper) {
  background: #ffffff;
  border: 1px solid #d0d0d0;
  border-radius: 3px;
  box-shadow: none;
  transition: border-color 0.2s ease;
  padding: 0 6px;
  min-height: 22px;
}

.japanese-table :deep(.el-input__wrapper:hover) {
  border-color: #999999;
}

.japanese-table :deep(.el-input__wrapper.is-focus) {
  border-color: #666666;
  box-shadow: 0 0 0 1px rgba(102, 102, 102, 0.1);
}

.japanese-table :deep(.el-input__inner) {
  color: #333333;
  font-size: 11px;
  height: 22px;
  line-height: 22px;
  padding: 0;
}

/* 表格单元格内容样式 */
.japanese-table .table-cell-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.japanese-table .table-cell-content.centered {
  justify-content: center;
}

.japanese-table .table-cell-content.left-aligned {
  justify-content: flex-start;
}

.japanese-table .cell-text {
  font-size: 11px;
  color: #1f2937;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.japanese-table .number-cell,
.japanese-table .date-cell,
.japanese-table .weekday-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.japanese-table .number-value,
.japanese-table .date-value {
  font-size: 11px;
  color: #1f2937;
}

.japanese-table .weekday-value {
  font-size: 10px;
  color: #4b5563;
  font-weight: 500;
}

.japanese-table .input-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 1px 0;
}

/* 日本简约风格底部 */
.japanese-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid #e8e8e8;
}

.japanese-footer :deep(.el-button) {
  background: #ffffff;
  border: 1px solid #d0d0d0;
  color: #555555;
  border-radius: 4px;
  font-size: 13px;
  padding: 8px 16px;
  transition: all 0.2s ease;
}

.japanese-footer :deep(.el-button:hover) {
  background: #f5f5f5;
  border-color: #999999;
}

.japanese-footer :deep(.el-button--primary) {
  background: #666666;
  border-color: #666666;
  color: #ffffff;
}

.japanese-footer :deep(.el-button--primary:hover) {
  background: #555555;
  border-color: #555555;
}

/* 日本简约风格动画效果 */
.japanese-minimalist :deep(.el-dialog) {
  animation: japaneseSlideIn 0.3s ease-out;
}

@keyframes japaneseSlideIn {
  0% {
    opacity: 0;
    transform: translateY(-10px) scale(0.98);
  }

  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.japanese-table :deep(.el-table__body tr) {
  animation: japaneseRowFadeIn 0.4s ease-out;
  animation-fill-mode: both;
}

.japanese-table :deep(.el-table__body tr:nth-child(1)) {
  animation-delay: 0.05s;
}

.japanese-table :deep(.el-table__body tr:nth-child(2)) {
  animation-delay: 0.1s;
}

.japanese-table :deep(.el-table__body tr:nth-child(3)) {
  animation-delay: 0.15s;
}

.japanese-table :deep(.el-table__body tr:nth-child(4)) {
  animation-delay: 0.2s;
}

.japanese-table :deep(.el-table__body tr:nth-child(5)) {
  animation-delay: 0.25s;
}

@keyframes japaneseRowFadeIn {
  0% {
    opacity: 0;
    transform: translateX(-5px);
  }

  100% {
    opacity: 1;
    transform: translateX(0);
  }
}

.japanese-filter-form :deep(.el-input__wrapper),
.japanese-filter-form :deep(.el-button),
.japanese-table :deep(.el-input__wrapper),
.japanese-footer :deep(.el-button) {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.japanese-filter-form :deep(.el-input__wrapper:hover),
.japanese-filter-form :deep(.el-button:hover),
.japanese-table :deep(.el-input__wrapper:hover),
.japanese-footer :deep(.el-button:hover) {
  transform: translateY(-1px);
}

.japanese-badge {
  transition: all 0.2s ease;
}

.japanese-badge:hover {
  transform: scale(1.02);
}

/* 紧凑型对话框样式 */
.compact-dialog {
  --el-dialog-padding-primary: 12px;
}

.compact-dialog :deep(.el-dialog__body) {
  padding: 6px 12px 8px 12px;
}

.compact-select-button {
  width: 220px;
  justify-content: flex-start;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #374151 !important;
  border-color: #d1d5db !important;
  background: #ffffff !important;
}

.compact-select-button:hover {
  color: #1f2937 !important;
  border-color: #9ca3af !important;
  background: #f9fafb !important;
}

.destination-select-dialog .destination-buttons-container {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  max-height: 60vh;
  overflow-y: auto;
  padding: 10px;
  justify-content: center;
}

.destination-select-dialog .destination-button {
  margin: 5px;
  font-size: 14px;
  flex-basis: 200px;
  flex-grow: 1;
  height: 40px;
}

/* 增强型对话框样式 */
.enhanced-dialog {
  --el-dialog-padding-primary: 0;
}

.enhanced-dialog :deep(.el-dialog) {
  border-radius: 24px;
  box-shadow: 0 30px 100px rgba(0, 0, 0, 0.25);
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border: 2px solid rgba(102, 126, 234, 0.2);
  overflow: hidden;
}

.enhanced-dialog :deep(.el-dialog__header) {
  padding: 25px 35px 20px 35px;
  background: linear-gradient(135deg, #1e40af 0%, #3730a3 50%, #581c87 100%);
  margin: 0;
  position: relative;
}

.enhanced-dialog :deep(.el-dialog__header)::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(45deg, rgba(255, 255, 255, 0.1) 0%, transparent 100%);
  pointer-events: none;
}

.enhanced-dialog :deep(.el-dialog__body) {
  padding: 30px 35px;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
}

.enhanced-dialog :deep(.el-dialog__footer) {
  padding: 25px 35px 30px 35px;
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
  border-top: 2px solid #e5e7eb;
}

.enhanced-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0;
  position: relative;
  z-index: 1;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.enhanced-header .dialog-icon {
  font-size: 28px;
  color: #000000 !important;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(255, 255, 255, 0.7) 100%);
  padding: 12px;
  border-radius: 16px;
  backdrop-filter: blur(15px);
  border: 2px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.enhanced-header .dialog-title {
  font-size: 24px;
  font-weight: 800;
  color: #000000 !important;
  text-shadow: 0 3px 6px rgba(255, 255, 255, 0.8) !important;
  letter-spacing: 0.5px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-badge {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.25) 0%, rgba(255, 255, 255, 0.1) 100%);
  padding: 8px 16px;
  border-radius: 25px;
  backdrop-filter: blur(15px);
  border: 2px solid rgba(255, 255, 255, 0.4);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.header-badge .badge-text {
  color: #000000 !important;
  font-size: 14px;
  font-weight: 700;
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8);
}

.enhanced-form {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  padding: 25px;
  border-radius: 20px;
  margin-bottom: 25px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 20px;
  border: 2px solid #e2e8f0;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
  position: relative;
}

.enhanced-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.enhanced-form :deep(.el-form-item__label) {
  color: #1f2937 !important;
  font-weight: 700;
  font-size: 15px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.enhanced-form :deep(.el-input__wrapper),
.enhanced-form :deep(.el-date-editor .el-input__wrapper) {
  border-radius: 12px;
  border: 2px solid #e1e8ed;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.enhanced-form :deep(.el-input__wrapper):hover,
.enhanced-form :deep(.el-date-editor .el-input__wrapper):hover {
  border-color: #667eea;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.15);
  transform: translateY(-1px);
}

.enhanced-form :deep(.el-button) {
  padding: 12px 20px;
  border-radius: 12px;
  font-weight: 700;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.enhanced-form :deep(.el-button--primary) {
  background: linear-gradient(135deg, #1e40af, #3730a3) !important;
  border: none !important;
  color: #000000 !important;
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8) !important;
  box-shadow: 0 4px 15px rgba(30, 64, 175, 0.4);
}

.enhanced-form :deep(.el-button--primary):hover {
  background: linear-gradient(135deg, #1d4ed8, #4338ca) !important;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(30, 64, 175, 0.5);
}

.enhanced-form :deep(.el-button-group .el-button) {
  padding: 8px 16px;
  font-size: 12px;
  font-weight: 600;
  border-radius: 8px;
  margin: 0 2px;
  transition: all 0.3s ease;
}

.enhanced-form :deep(.el-button-group .el-button) {
  color: #374151 !important;
  border-color: #d1d5db !important;
  background: #ffffff !important;
}

.enhanced-form :deep(.el-button-group .el-button):hover {
  color: #1f2937 !important;
  border-color: #9ca3af !important;
  background: #f9fafb !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.modern-daily-table {
  margin-top: 20px;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(102, 126, 234, 0.1);
}

.modern-daily-table :deep(.el-table__header) {
  background: linear-gradient(135deg, #1e40af 0%, #3730a3 50%, #581c87 100%);
}

.modern-daily-table :deep(.el-table__header th) {
  background: transparent !important;
  color: #000000 !important;
  font-weight: 700;
  border-bottom: none;
  text-shadow: 0 2px 4px rgba(255, 255, 255, 0.8) !important;
}

.modern-daily-table :deep(.el-table__body tr:hover) {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.modern-daily-table :deep(.el-table__body tr:nth-child(even)) {
  background-color: #fafbfc;
}

.modern-daily-table :deep(.el-table__body td) {
  padding: 15px 12px;
  border-bottom: 1px solid #f1f3f4;
  transition: all 0.3s ease;
}

.modern-daily-table :deep(.el-table__summary-row) {
  background: linear-gradient(
    135deg,
    rgba(30, 64, 175, 0.15) 0%,
    rgba(55, 48, 163, 0.15) 100%
  ) !important;
  font-weight: 700;
  color: #1f2937 !important;
}

.modern-daily-table :deep(.el-table__summary-row td) {
  border-top: 3px solid #1e40af !important;
  font-size: 15px;
  font-weight: 700 !important;
  color: #1f2937 !important;
}

.table-cell-content {
  display: flex;
  align-items: center;
  gap: 10px;
}

.table-cell-content.centered {
  justify-content: center;
  text-align: center;
}

.table-cell-content.left-aligned {
  justify-content: flex-start;
  text-align: left;
}

.cell-text {
  font-weight: 700;
  color: #2c3e50;
  font-size: 12px;
}

.date-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.date-value {
  font-weight: 700;
  color: #2c3e50;
  font-size: 12px;
}

.weekday-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.weekday-value {
  font-weight: 700;
  color: #2c3e50;
  font-size: 12px;
}

.weekday-saturday {
  color: #1e40af !important;
  font-weight: 800;
}

.weekday-sunday {
  color: #dc2626 !important;
  font-weight: 800;
}

.weekday-normal {
  color: #2c3e50;
  font-weight: 700;
}

.number-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.number-value {
  font-weight: 600;
  color: #1f2937;
  font-size: 12px;
  padding: 0;
  background: transparent;
  border-radius: 0;
  border: none;
}

.input-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.select-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.modern-table-input {
  width: 70px;
  height: 28px;
  text-align: center;
  vertical-align: middle;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.modern-table-input :deep(.el-input__wrapper) {
  border-radius: 8px;
  text-align: center;
}

.modern-table-input :deep(.el-input__inner) {
  text-align: center;
  font-size: 12px;
  font-weight: 600;
  height: 28px;
  line-height: 28px;
}

.editable-input :deep(.el-input__wrapper) {
  border: 2px solid #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  transition: all 0.3s ease;
}

.editable-input :deep(.el-input__wrapper):hover {
  border-color: #4338ca;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.15);
  transform: translateY(-1px);
}

.editable-input :deep(.el-input__wrapper):focus-within {
  border-color: #3730a3;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.2);
  transform: translateY(-1px);
}

.readonly-input :deep(.el-input__wrapper) {
  border: 1px solid #e5e7eb;
  box-shadow: none;
  background: #f9fafb;
}

.readonly-input :deep(.el-input__inner) {
  color: #6b7280;
  font-weight: 600;
}

.modern-status-select {
  width: 100%;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.modern-status-select :deep(.el-input__wrapper) {
  border-radius: 8px;
  border: 2px solid #e1e8ed;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.modern-status-select :deep(.el-input__wrapper):hover {
  border-color: #667eea;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.15);
  transform: translateY(-1px);
}

.modern-status-select :deep(.el-input__wrapper):focus-within {
  border-color: #4338ca;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
  transform: translateY(-1px);
}

.modern-status-select :deep(.el-input__inner) {
  font-size: 14px;
  font-weight: 600;
  color: #2c3e50;
  height: 36px;
  line-height: 36px;
}

.modern-status-select :deep(.el-popper) {
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(102, 126, 234, 0.1);
}

.modern-status-select :deep(.el-select-dropdown__item) {
  font-weight: 600;
  color: #2c3e50;
  padding: 12px 16px;
  transition: all 0.3s ease;
}

.modern-status-select :deep(.el-select-dropdown__item:hover) {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
  color: #667eea;
}

.modern-status-select :deep(.el-select-dropdown__item.is-selected) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #ffffff;
  font-weight: 700;
}

.enhanced-footer {
  display: flex;
  justify-content: flex-end;
  gap: 6px;
  padding-top: 8px;
  border-top: 1px solid #e5e7eb;
}

.enhanced-cancel-button,
.enhanced-save-button {
  padding: 5px 10px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 13px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 8px;
}

.enhanced-cancel-button {
  color: #6b7280;
  border: 2px solid #d1d5db;
  background: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
}

.enhanced-cancel-button:hover {
  color: #374151;
  border-color: #9ca3af;
  background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.enhanced-save-button {
  background: linear-gradient(135deg, #1e40af 0%, #3730a3 100%) !important;
  border: none !important;
  color: #000000 !important;
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8) !important;
  box-shadow: 0 4px 15px rgba(30, 64, 175, 0.4);
}

.enhanced-save-button:hover {
  background: linear-gradient(135deg, #1d4ed8 0%, #4338ca 100%) !important;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(30, 64, 175, 0.5);
}

.enhanced-save-button:active {
  transform: translateY(0);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.enhanced-cancel-button:disabled,
.enhanced-save-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.enhanced-cancel-button:disabled:hover,
.enhanced-save-button:disabled:hover {
  transform: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.destination-select-button {
  width: 220px;
  justify-content: flex-start;
}

/* 增强筛选样式 */
.enhanced-filter {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border: 1px solid rgba(102, 126, 234, 0.15);
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.1);
}

.enhanced-filter :deep(.el-card__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px 16px 0 0;
  padding: 10px 24px;
  border-bottom: none;
}

.enhanced-filter .filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 0;
  padding: 0;
  border: none;
}

.enhanced-filter .filter-title {
  color: white;
  font-size: 18px;
  font-weight: 700;
}

.enhanced-filter .filter-icon {
  color: white;
  animation: none;
}

.filter-stats .stats-text {
  display: flex;
  align-items: center;
  gap: 6px;
  color: rgba(255, 255, 255, 0.9);
  font-size: 14px;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.1);
  padding: 1px 12px;
  border-radius: 16px;
  backdrop-filter: blur(10px);
}

.filter-content {
  padding: 0;
}

.filter-bar.enhanced {
  margin: 0;
}

.filter-section {
  margin-bottom: 10px;
  padding: 20px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  border: 1px solid rgba(102, 126, 234, 0.1);
}

.filter-section:last-child {
  margin-bottom: 0;
}

.section-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid rgba(102, 126, 234, 0.2);
}

.section-label .el-icon {
  color: #667eea;
  font-size: 18px;
}

.time-controls {
  display: flex;
  gap: 20px;
  align-items: center;
  flex-wrap: wrap;
}

.date-selectors {
  display: flex;
  gap: 12px;
  align-items: center;
}

.compact-form-item {
  margin-bottom: 0;
}

.compact-form-item :deep(.el-form-item__label) {
  font-weight: 600;
  color: #374151;
  font-size: 16px;
}

.compact-select {
  min-width: 100px;
  border-radius: 8px;
}

.compact-select :deep(.el-input__wrapper) {
  border-radius: 8px;
  border: 2px solid #e2e8f0;
  transition: all 0.3s ease;
}

.compact-select :deep(.el-input__wrapper):hover {
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
  transform: translateY(-1px);
}

.month-nav-buttons.enhanced {
  display: flex;
  gap: 8px;
}

.nav-button {
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: 600;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.prev-button {
  background: linear-gradient(135deg, #f87171 0%, #dc2626 100%);
  color: white;
  border: none;
}

.prev-button:hover {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(248, 113, 113, 0.3);
}

.current-button {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
}

.current-button:hover {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.next-button {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  border: none;
}

.next-button:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.search-controls {
  display: flex;
  gap: 20px;
  align-items: flex-end;
  flex-wrap: wrap;
}

.enhanced-form-item {
  margin-bottom: 0;
  flex: 1;
  min-width: 200px;
}

.enhanced-form-item :deep(.el-form-item__label) {
  font-weight: 600;
  color: #374151;
  font-size: 14px;
}

.destination-select-button.enhanced {
  width: 100%;
  min-width: 200px;
  padding: 12px 16px;
  border-radius: 8px;
  border: 2px solid #e2e8f0;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  color: #374151;
  font-weight: 600;
  transition: all 0.3s ease;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.destination-select-button.enhanced:hover {
  border-color: #667eea;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
}

.destination-select-button.enhanced.has-selection {
  border-color: #667eea;
  background: linear-gradient(135deg, #ede9fe 0%, #ddd6fe 100%);
  color: #667eea;
}

.expand-icon {
  color: #9ca3af;
  transition: transform 0.3s ease;
}

.destination-select-button.enhanced:hover .expand-icon {
  transform: rotate(180deg);
  color: #667eea;
}

.enhanced-input {
  border-radius: 8px;
}

.enhanced-input :deep(.el-input__wrapper) {
  border-radius: 8px;
  border: 2px solid #e2e8f0;
  transition: all 0.3s ease;
}

.enhanced-input :deep(.el-input__wrapper):hover {
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
  transform: translateY(-1px);
}

.enhanced-input :deep(.el-input__wrapper):focus-within {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.search-suffix {
  display: flex;
  align-items: center;
}

.clear-search-btn {
  padding: 4px;
  border-radius: 4px;
  color: #9ca3af;
  transition: all 0.3s ease;
}

.clear-search-btn:hover {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.action-form-item {
  margin-bottom: 0;
  flex-shrink: 0;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.search-button.enhanced {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.search-button.enhanced:hover {
  background: linear-gradient(135deg, #5a6fd8 0%, #6a4c93 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.reset-button.enhanced {
  background: linear-gradient(135deg, #9ca3af 0%, #6b7280 100%);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.reset-button.enhanced:hover {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(156, 163, 175, 0.3);
}

/* 单行筛选布局样式 */
.filter-bar.single-row {
  margin: 0;
  padding: 0;
}

.filter-row-unified {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border-radius: 8px;
  border: 1px solid rgba(102, 126, 234, 0.1);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.05);
  transition: all 0.3s ease;
}

/* 主筛选区纳入先下拉：可显示约18字（留有左右内边距余量） */
.filter-row-unified .destination-select {
  width: 28ch;
  min-width: 28ch;
}

.filter-row-unified:hover {
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.1);
  transform: translateY(-1px);
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  margin: 0;
  padding: 0;
}

.filter-group.time-group {
  border-right: 1px solid rgba(102, 126, 234, 0.15);
  padding-right: 12px;
}

.filter-group.search-group {
  flex: 1;
  border-right: 1px solid rgba(102, 126, 234, 0.15);
  padding-right: 12px;
}

.filter-group.action-group {
  flex-shrink: 0;
}

.group-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  white-space: nowrap;
  margin-right: 8px;
}

.group-label .el-icon {
  font-size: 14px;
  color: #667eea;
}

.group-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.inline-form-item {
  margin-bottom: 0 !important;
  margin-right: 0 !important;
}

.inline-form-item :deep(.el-form-item__label) {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
  padding-right: 8px;
  margin-bottom: 0;
}

.compact-select {
  width: 80px;
}

.year-select {
  width: 85px;
}

.month-select {
  width: 75px;
}

.nav-buttons-inline {
  display: flex;
  gap: 4px;
  margin-left: 8px;
}

.nav-btn {
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  transition: all 0.2s ease;
  border: 1px solid #d1d5db;
  background: white;
  color: #6b7280;
}

.nav-btn:hover {
  border-color: #667eea;
  color: #667eea;
  background: rgba(102, 126, 234, 0.05);
  transform: translateY(-1px);
}

.nav-btn.current-btn {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border-color: #667eea;
}

.nav-btn.current-btn:hover {
  background: linear-gradient(135deg, #5a6fd8, #6a4c93);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

/* 一括登録ダイアログの月ナビゲーションボタン */
.month-select-with-nav {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: nowrap;
}

.month-nav-buttons {
  display: flex;
  align-items: center;
  gap: 3px;
  flex-shrink: 0;
}

.month-nav-btn {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  transition: all 0.2s ease;
  border: 1px solid #d1d5db;
  background: white;
  color: #6b7280;
  min-width: 36px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.month-nav-btn:hover {
  border-color: #9ca3af;
  background: #f9fafb;
  color: #374151;
}

.month-nav-btn.prev-month-btn,
.month-nav-btn.next-month-btn {
  padding: 6px 10px;
}

.month-nav-btn.current-month-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: #667eea;
  min-width: 60px;
}

.month-nav-btn.current-month-btn:hover {
  background: linear-gradient(135deg, #5a6fd8 0%, #6a4c93 100%);
  border-color: #5a6fd8;
  color: white;
}

.month-nav-btn.current-month-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.destination-btn {
  padding: 10px 16px;
  border-radius: 6px;
  border: 1px solid #d1d5db;
  background: white;
  color: #374151;
  font-size: 13px;
  transition: all 0.2s ease;
  min-width: 240px;
  max-width: 350px;
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: space-between;
}

.destination-btn:hover {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.05);
  transform: translateY(-1px);
}

.destination-btn.has-selection {
  border-color: #667eea;
  background: linear-gradient(135deg, #ede9fe, #ddd6fe);
  color: #667eea;
  font-weight: 500;
}

.expand-icon {
  font-size: 12px;
  opacity: 0.7;
  transition: transform 0.2s ease;
}

.destination-btn:hover .expand-icon {
  transform: rotate(180deg);
}

.destination-btn-content {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  overflow: hidden;
}

.destination-text {
  flex: 1;
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 500;
}

.search-item {
  flex: 1;
  min-width: 200px;
}

.search-input {
  width: 100%;
}

.search-input :deep(.el-input__wrapper) {
  border-radius: 6px;
  border: 1px solid #d1d5db;
  transition: all 0.2s ease;
}

.search-input :deep(.el-input__wrapper):hover {
  border-color: #667eea;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
}

.search-input :deep(.el-input__wrapper):focus-within {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.search-icon {
  color: #9ca3af;
  font-size: 14px;
}

.action-buttons.compact {
  display: flex;
  gap: 8px;
}

.modern-btn {
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.2s ease;
  border: none;
}

.search-btn {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.search-btn:hover {
  background: linear-gradient(135deg, #5a6fd8, #6a4c93);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.reset-btn {
  background: linear-gradient(135deg, #9ca3af, #6b7280);
  color: white;
  box-shadow: 0 2px 8px rgba(156, 163, 175, 0.3);
}

.reset-btn:hover {
  background: linear-gradient(135deg, #6b7280, #4b5563);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(156, 163, 175, 0.4);
}

/* 内示本数和確定本数列简约无边框样式 */
:deep(.el-table) {
  td:nth-child(7),
  td:nth-child(8) {
    border-left: none !important;
    border-right: none !important;
  }

  th:nth-child(7),
  th:nth-child(8) {
    border-left: none !important;
    border-right: none !important;
    background: rgba(248, 250, 252, 0.8) !important;
  }
}

/* 响应式设计 */
/* 中等屏幕 (平板横屏) */
@media (max-width: 1200px) {
  .filter-row-unified {
    gap: 24px;
    padding: 16px 20px;
  }

  .filter-group.time-group {
    padding-right: 16px;
  }

  .filter-group.search-group {
    padding-right: 16px;
  }

  .destination-btn {
    min-width: 200px;
    max-width: 280px;
  }

  .search-item {
    min-width: 180px;
  }
}

/* 平板设备 */
@media (max-width: 992px) {
  .filter-row-unified {
    flex-wrap: wrap;
    gap: 16px;
    padding: 16px;
  }

  .filter-group.time-group {
    flex: 1 1 auto;
    min-width: 300px;
    border-right: none;
    padding-right: 0;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(102, 126, 234, 0.15);
  }

  .filter-group.search-group {
    flex: 1 1 100%;
    border-right: none;
    padding-right: 0;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(102, 126, 234, 0.15);
  }

  .filter-group.action-group {
    flex: 1 1 100%;
    justify-content: center;
  }

  .group-controls {
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
  }

  /* 时间组在平板上的优化 */
  .time-group .group-controls {
    justify-content: center;
    align-items: center;
  }

  .destination-btn {
    min-width: 180px;
    max-width: 250px;
  }

  .search-item {
    flex: 1;
    min-width: 200px;
  }

  .action-buttons.compact {
    justify-content: center;
  }
}

/* 移动设备 */
@media (max-width: 768px) {
  .enhanced-filter .filter-content {
    padding: 16px;
  }

  /* 移动端单行布局调整 */
  .filter-row-unified {
    flex-direction: column;
    gap: 20px;
    padding: 16px;
  }

  .filter-group {
    width: 100%;
    border-right: none !important;
    padding-right: 0 !important;
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .group-label {
    justify-content: center;
    margin-right: 0;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(102, 126, 234, 0.15);
  }

  .group-controls {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }

  .time-group .group-controls {
    flex-direction: column;
    align-items: stretch;
  }

  /* 时间选择器在移动端的布局 */
  .time-group .group-controls > .inline-form-item {
    display: flex;
    flex-direction: column;
    align-items: stretch;
  }

  .time-group .group-controls > .inline-form-item :deep(.el-form-item__label) {
    text-align: center;
    margin-bottom: 4px;
  }

  .compact-select,
  .year-select,
  .month-select {
    width: 100% !important;
  }

  .nav-buttons-inline {
    margin-left: 0;
    justify-content: center;
    gap: 8px;
  }

  .nav-btn {
    flex: 1;
    padding: 8px 12px;
  }

  .search-group .group-controls {
    align-items: stretch;
  }

  /* 搜索组在移动端的优化 */
  .search-group .inline-form-item {
    display: flex;
    flex-direction: column;
    align-items: stretch;
  }

  .search-group .inline-form-item :deep(.el-form-item__label) {
    text-align: center;
    margin-bottom: 4px;
  }

  .destination-btn {
    min-width: auto;
    max-width: none;
    width: 100%;
    justify-content: space-between;
  }

  .destination-text {
    text-align: center;
  }

  .search-item {
    min-width: auto;
  }

  .search-input {
    width: 100%;
  }

  .action-buttons.compact {
    flex-direction: column;
    gap: 8px;
  }

  .modern-btn {
    width: 100%;
    justify-content: center;
  }

  .filter-section {
    padding: 16px;
    margin-bottom: 16px;
  }

  .time-controls,
  .search-controls {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .date-selectors {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .month-nav-buttons.enhanced {
    flex-direction: column;
    gap: 8px;
  }

  .nav-button {
    width: 100%;
    justify-content: center;
  }

  .enhanced-form-item {
    min-width: 100%;
  }

  .destination-select-button.enhanced {
    min-width: 100%;
  }

  .action-buttons {
    flex-direction: column;
    gap: 8px;
  }

  .search-button.enhanced,
  .reset-button.enhanced {
    width: 100%;
    justify-content: center;
  }
}

/* 超小屏幕 (小手机) */
@media (max-width: 480px) {
  .filter-row-unified {
    padding: 12px;
    gap: 16px;
  }

  .group-label {
    font-size: 12px;
    padding-bottom: 6px;
  }

  .inline-form-item :deep(.el-form-item__label) {
    font-size: 11px;
  }

  .nav-btn {
    padding: 6px 8px;
    font-size: 11px;
  }

  .destination-btn {
    padding: 8px 12px;
    font-size: 12px;
  }

  .search-input :deep(.el-input__inner) {
    font-size: 14px;
  }

  .modern-btn {
    padding: 8px 16px;
    font-size: 12px;
  }
}

/* 极小屏幕优化 */
@media (max-width: 360px) {
  .filter-row-unified {
    padding: 10px;
    gap: 12px;
  }

  .group-label {
    font-size: 11px;
  }

  .nav-buttons-inline {
    gap: 4px;
  }

  .nav-btn {
    padding: 4px 6px;
    font-size: 10px;
    min-width: 0;
  }

  .nav-btn.current-btn {
    padding: 6px 8px;
  }
}

/* 删除确认对话框样式 */
:deep(.delete-confirmation-dialog) {
  .el-message-box {
    border-radius: 16px;
    box-shadow: 0 20px 80px rgba(0, 0, 0, 0.25);
  }

  .el-message-box__header {
    background: linear-gradient(135deg, #ff6b6b 0%, #dc3545 100%);
    color: white;
    padding: 20px 25px;
    border-radius: 16px 16px 0 0;
  }

  .el-message-box__title {
    color: white;
    font-weight: 700;
    font-size: 18px;
  }

  .el-message-box__content {
    padding: 25px;
    background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  }

  .el-message-box__message {
    font-size: 14px;
    line-height: 1.6;
  }

  .el-message-box__btns {
    padding: 20px 25px;
    background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
    border-top: 1px solid #e5e7eb;
    border-radius: 0 0 16px 16px;
  }

  .el-button--primary {
    background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
    border: none;
    color: white;
    font-weight: 600;
    padding: 12px 24px;
    border-radius: 8px;
    transition: all 0.3s ease;
  }

  .el-button--primary:hover {
    background: linear-gradient(135deg, #c82333 0%, #a71e2a 100%);
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(220, 53, 69, 0.4);
  }

  .el-button:not(.el-button--primary) {
    background: linear-gradient(135deg, #6c757d 0%, #5a6268 100%);
    color: white;
    border: none;
    font-weight: 600;
    padding: 12px 24px;
    border-radius: 8px;
    transition: all 0.3s ease;
  }

  .el-button:not(.el-button--primary):hover {
    background: linear-gradient(135deg, #5a6268 0%, #494f54 100%);
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(108, 117, 125, 0.4);
  }
}

/* 批量数量编辑对话框样式 - 紧凑版 */
.batch-quantity-dialog :deep(.el-dialog) {
  max-height: 92vh;
  overflow: hidden;
}

.batch-quantity-dialog :deep(.el-dialog__header) {
  padding: 12px 16px;
  border-bottom: 1px solid #e5e7eb;
}

.batch-quantity-dialog :deep(.el-dialog__body) {
  max-height: calc(92vh - 120px);
  overflow-y: auto;
  padding: 12px 16px;
}

.batch-quantity-dialog :deep(.el-dialog__footer) {
  padding: 10px 16px;
  border-top: 1px solid #e5e7eb;
}

.dialog-header-compact {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 0;
  gap: 12px;
}

.dialog-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.dialog-icon-compact {
  font-size: 18px;
  color: #667eea;
}

.dialog-title-compact {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.header-load-btn {
  flex-shrink: 0;
}

.batch-quantity-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.quantity-filter-section {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  padding: 12px 14px;
  border-radius: 8px;
  border: 1px solid rgba(102, 126, 234, 0.1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.quantity-filter-form {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  margin: 0;
}

.filter-item-compact {
  margin-bottom: 0 !important;
}

.quantity-filter-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.quantity-filter-form :deep(.el-form-item__label) {
  font-weight: 600;
  color: #374151;
  font-size: 13px;
  padding-right: 8px;
  line-height: 28px;
}

.quantity-filter-form :deep(.el-radio-group) {
  display: flex;
  gap: 12px;
}

.quantity-filter-form :deep(.el-radio) {
  margin-right: 0;
}

.quantity-filter-form :deep(.el-radio__label) {
  font-weight: 500;
  color: #374151;
  font-size: 13px;
  padding-left: 4px;
}

.quantity-edit-section {
  background: white;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.edit-header-compact {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.edit-title-compact {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.4;
}

.edit-stats-compact {
  display: flex;
  align-items: center;
  gap: 10px;
}

.stats-text-compact {
  display: inline-flex;
  align-items: center;
  color: rgba(255, 255, 255, 0.95);
  font-size: 12px;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.15);
  padding: 3px 10px;
  border-radius: 12px;
  backdrop-filter: blur(8px);
  white-space: nowrap;
}

.execute-btn-inline {
  background: linear-gradient(135deg, #10b981, #059669) !important;
  border: none !important;
  color: white !important;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
  padding: 4px 12px;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.execute-btn-inline:hover {
  background: linear-gradient(135deg, #059669, #047857) !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
}

.execute-btn-inline:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.quantity-edit-table {
  border-radius: 0;
}

.quantity-edit-table :deep(.el-table__header) {
  background: linear-gradient(135deg, #f8f9fa, #e9ecef);
}

.quantity-edit-table :deep(.el-table__header th) {
  background: transparent;
  color: #495057;
  font-weight: 600;
  font-size: 12px;
  border-bottom: 2px solid #dee2e6;
  padding: 6px 4px;
}

.quantity-edit-table :deep(.el-table__body tr:hover) {
  background-color: rgba(102, 126, 234, 0.05);
}

.quantity-edit-table :deep(.el-table__row) {
  height: auto;
}

.quantity-edit-table :deep(.el-table__cell),
.quantity-edit-table :deep(.el-table__body td) {
  padding: 4px 4px;
  border-bottom: 1px solid #f1f3f4;
  font-size: 12px;
  line-height: 1.3;
}

.quantity-edit-table :deep(.el-table__body tr) {
  height: auto;
}

.current-value {
  font-weight: 600;
  color: #6b7280;
  font-size: 12px;
}

.inline-edit-input {
  width: 110px;
}

.inline-edit-input :deep(.el-input__wrapper) {
  border-radius: 4px;
  border: 1.5px solid #e1e8ed;
  transition: all 0.2s ease;
  background: #ffffff;
  padding: 0 8px;
}

.inline-edit-input :deep(.el-input__wrapper):hover {
  border-color: #667eea;
  box-shadow: 0 1px 4px rgba(102, 126, 234, 0.15);
}

.inline-edit-input :deep(.el-input__wrapper):focus-within {
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
}

/* 内示本数更新进度条弹窗样式 */
.update-forecast-progress-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
  padding: 20px 24px;
  border-radius: 8px 8px 0 0;
}

.update-forecast-progress-dialog :deep(.el-dialog__title) {
  color: white;
  font-weight: 600;
  font-size: 16px;
}

.update-forecast-progress-dialog :deep(.el-dialog__body) {
  padding: 24px;
  background: #fafafa;
}

.progress-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.progress-info {
  text-align: center;
}

.progress-text {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
  margin: 0 0 8px 0;
}

.progress-detail {
  font-size: 12px;
  color: #6b7280;
  margin: 0;
}

.progress-stats {
  display: flex;
  justify-content: center;
  gap: 24px;
  padding-top: 12px;
  border-top: 1px solid #e5e7eb;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-label {
  font-size: 12px;
  color: #6b7280;
}

.stat-value {
  font-size: 14px;
  font-weight: 600;
}

.stat-value.updated {
  color: #10b981;
}

.stat-value.cleared {
  color: #f59e0b;
}

.update-forecast-progress-dialog :deep(.el-progress-bar__outer) {
  background-color: #e5e7eb;
  border-radius: 10px;
}

.update-forecast-progress-dialog :deep(.el-progress-bar__inner) {
  border-radius: 10px;
}

.inline-edit-input :deep(.el-input__inner) {
  text-align: center;
  font-size: 12px;
  font-weight: 600;
  height: 24px;
  line-height: 24px;
  min-width: 0;
  padding: 0 4px;
}

.inline-edit-input :deep(.el-input__wrapper) {
  min-height: 24px;
}

.no-change {
  color: #9ca3af;
  font-style: italic;
  font-size: 12px;
}

.dialog-footer-compact {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 0;
}

.cancel-btn-compact {
  padding: 6px 14px;
  font-size: 13px;
}

.execute-btn-compact {
  background: linear-gradient(135deg, #10b981, #059669) !important;
  border: none !important;
  color: white !important;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
  padding: 6px 14px;
  font-size: 13px;
  font-weight: 600;
}

.execute-btn-compact:hover {
  background: linear-gradient(135deg, #059669, #047857) !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
}

.execute-btn-compact:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .batch-quantity-dialog :deep(.el-dialog) {
    width: 58% !important;
  }

  .batch-quantity-dialog :deep(.el-dialog__body) {
    padding: 10px 12px;
  }

  .dialog-header-compact {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }

  .dialog-header-left {
    width: 100%;
  }

  .header-load-btn {
    width: 100%;
    justify-content: center;
  }

  .edit-header-compact {
    flex-direction: column;
    gap: 8px;
    align-items: stretch;
    padding: 8px 12px;
  }

  .edit-title-compact {
    text-align: center;
    font-size: 13px;
  }

  .edit-stats-compact {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .stats-text-compact {
    font-size: 11px;
    padding: 2px 8px;
    width: 100%;
    justify-content: center;
  }

  .execute-btn-inline {
    width: 100%;
    justify-content: center;
  }

  .inline-edit-input {
    width: 100%;
    max-width: 100px;
  }
}
</style>
