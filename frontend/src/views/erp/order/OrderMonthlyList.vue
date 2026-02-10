<template>
  <div class="order-monthly-list">
    <div class="page-toolbar">
      <div class="toolbar-left">
        <h1 class="toolbar-title">{{ t('orderMonthly.title') }}</h1>
      </div>
      <div class="toolbar-right">
        <el-button class="tb-btn tb-btn-blue" :loading="generating" @click="openGenerateDailyConfirmDialog">
          <el-icon><DocumentAdd /></el-icon>
          <span class="tb-label">{{ t('orderMonthly.btnGenerateDaily') }}</span>
        </el-button>
        <el-button class="tb-btn tb-btn-teal" :loading="updatingForecast" @click="forecastUpdateConfirmVisible = true">
          <el-icon><Refresh /></el-icon>
          <span class="tb-label">{{ t('orderMonthly.btnUpdateForecast') }}</span>
        </el-button>
        <el-button class="tb-btn tb-btn-amber" @click="openUpdateFieldsDialog">
          <el-icon><Box /></el-icon>
          <span class="tb-label">{{ t('orderMonthly.btnUpdateProduct') }}</span>
        </el-button>
        <el-button class="tb-btn tb-btn-indigo" @click="openDailyOrderDialog">
          <el-icon><Calendar /></el-icon>
          <span class="tb-label">{{ t('orderMonthly.btnDailyOrder') }}</span>
        </el-button>
        <el-button class="tb-btn tb-btn-rose" @click="openEdiImportDialog">
          <el-icon><Upload /></el-icon>
          <span class="tb-label">{{ t('orderMonthly.btnEdiImport') }}</span>
        </el-button>
        <el-button class="tb-btn tb-btn-green" @click="openBatchDialog">
          <el-icon><Files /></el-icon>
          <span class="tb-label">{{ t('orderMonthly.btnBatchRegister') }}</span>
        </el-button>
      </div>
    </div>

    <div v-show="progressVisible" class="progress-section">
      <el-progress
        :percentage="progressPercent"
        :status="progressStatus"
        :stroke-width="12"
      />
    </div>

    <!-- 日受注リスト生成 確認 -->
    <el-dialog
      v-model="generateDailyConfirmVisible"
      width="420px"
      class="generate-daily-confirm-dialog"
      align-center
      :show-close="false"
    >
      <template #header>
        <div class="gd-confirm-header">
          <div class="gd-confirm-icon-wrap">
            <el-icon class="gd-confirm-icon"><DocumentAdd /></el-icon>
          </div>
          <div class="gd-confirm-title-wrap">
            <span class="gd-confirm-title">{{ t('orderMonthly.generateDailyConfirmTitle') }}</span>
            <span class="gd-confirm-subtitle">{{ t('orderMonthly.generateDailyConfirmSubtitle') }}</span>
          </div>
        </div>
      </template>
      <div class="gd-confirm-body">
        <div class="gd-confirm-card">
          <div class="gd-confirm-row">
            <span class="gd-confirm-label">{{ t('orderMonthly.targetYearMonth') }}</span>
            <span class="gd-confirm-value">{{ generateDailyConfirmYear }}年 {{ generateDailyConfirmMonth }}月</span>
          </div>
          <div class="gd-confirm-row">
            <span class="gd-confirm-label">{{ t('orderMonthly.productType') }}</span>
            <span class="gd-confirm-value gd-tag">{{ t('orderMonthly.productTypeMass') }}</span>
          </div>
          <div class="gd-confirm-row">
            <span class="gd-confirm-label">{{ t('orderMonthly.destination') }}</span>
            <span class="gd-confirm-value gd-dest">{{ generateDailyConfirmDestinationLabel }}</span>
          </div>
        </div>
        <p class="gd-confirm-ask">{{ t('orderMonthly.confirmAsk') }}</p>
      </div>
      <template #footer>
        <div class="gd-confirm-footer">
          <el-button class="gd-btn-cancel" @click="generateDailyConfirmVisible = false">{{ t('orderMonthly.cancel') }}</el-button>
          <el-button type="primary" class="gd-btn-submit" @click="confirmGenerateDailyOrders">{{ t('orderMonthly.generate') }}</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 内示本数更新の確認 -->
    <el-dialog
      v-model="forecastUpdateConfirmVisible"
      width="400px"
      class="forecast-update-confirm-dialog"
      align-center
      :show-close="false"
    >
      <template #header>
        <div class="fuc-header">
          <div class="fuc-icon-wrap">
            <el-icon class="fuc-icon"><Refresh /></el-icon>
          </div>
          <div class="fuc-title-wrap">
            <span class="fuc-title">{{ t('orderMonthly.forecastUpdateConfirmTitle') }}</span>
          </div>
        </div>
      </template>
      <div class="fuc-body">
        <p class="fuc-msg">{{ t('orderMonthly.forecastUpdateConfirmMsg') }}</p>
      </div>
      <template #footer>
        <div class="fuc-footer">
          <el-button class="fuc-btn-cancel" @click="forecastUpdateConfirmVisible = false">{{ t('orderMonthly.cancel') }}</el-button>
          <el-button type="primary" class="fuc-btn-submit" :loading="updatingForecast" @click="confirmForecastUpdate">{{ t('orderMonthly.execute') }}</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 製品情報一括更新 -->
    <el-dialog
      v-model="updateFieldsDialogVisible"
      width="440px"
      class="update-fields-dialog"
      destroy-on-close
      align-center
      :show-close="false"
      @close="resetUpdateFieldsForm"
    >
      <template #header>
        <div class="ufd-header">
          <div class="ufd-icon-wrap">
            <el-icon class="ufd-icon"><Box /></el-icon>
          </div>
          <div class="ufd-title-wrap">
            <span class="ufd-title">{{ t('orderMonthly.updateFieldsTitle') }}</span>
            <span class="ufd-subtitle">{{ t('orderMonthly.updateFieldsSubtitle') }}</span>
          </div>
        </div>
      </template>
      <div class="ufd-body">
        <el-form ref="updateFieldsFormRef" :model="updateFieldsForm" :rules="updateFieldsRules" label-width="80px" size="default" class="ufd-form">
          <div class="ufd-card">
            <el-form-item :label="t('orderMonthly.startDate')" prop="startDate" required class="ufd-item">
              <el-date-picker
                v-model="updateFieldsForm.startDate"
                type="date"
                :placeholder="t('orderMonthly.select')"
                value-format="YYYY-MM-DD"
                style="width: 100%"
                class="ufd-date-picker"
              />
            </el-form-item>
            <el-form-item class="ufd-item ufd-check-item">
              <el-checkbox v-model="updateFieldsForm.updateProductInfo" class="ufd-checkbox">{{ t('orderMonthly.updateProductInfoCheck') }}</el-checkbox>
            </el-form-item>
            <div v-if="updateFieldsForm.updateProductInfo" class="ufd-note">
              <el-icon><InfoFilled /></el-icon>
              <span>{{ t('orderMonthly.updateProductInfoNote') }}</span>
            </div>
          </div>
        </el-form>
      </div>
      <template #footer>
        <div class="ufd-footer">
          <el-button class="ufd-btn-cancel" @click="updateFieldsDialogVisible = false">{{ t('orderMonthly.cancel') }}</el-button>
          <el-button type="primary" class="ufd-btn-submit" :loading="updateFieldsSubmitting" @click="submitUpdateFields">{{ t('orderMonthly.updateExecute') }}</el-button>
        </div>
      </template>
    </el-dialog>

    <div class="filter-bar">
      <div class="filter-inline">
        <div class="fi-group">
          <el-icon class="fi-icon"><Calendar /></el-icon>
          <el-select v-model="filters.year" :placeholder="t('orderMonthly.filterYear')" clearable class="fi-select fi-year">
            <el-option v-for="y in yearOptions" :key="y" :label="`${y}年`" :value="y" />
          </el-select>
          <el-select v-model="filters.month" :placeholder="t('orderMonthly.filterMonth')" clearable class="fi-select fi-month">
            <el-option v-for="m in 12" :key="m" :label="`${m}月`" :value="m" />
          </el-select>
          <div class="fi-nav">
            <el-button class="fi-nav-btn" :icon="ArrowLeft" circle size="small" @click="goPrevPeriod" />
            <el-button class="fi-now-btn" size="small" @click="goCurrentMonth">{{ t('orderMonthly.thisMonth') }}</el-button>
            <el-button class="fi-nav-btn" :icon="ArrowRight" circle size="small" @click="goNextPeriod" />
          </div>
        </div>
        <div class="fi-sep"></div>
        <div class="fi-group">
          <el-select v-model="filters.destination_cd" :placeholder="t('orderMonthly.destination')" clearable filterable class="fi-select fi-dest" popper-class="destination-select-popper">
            <el-option v-for="d in destinationOptions" :key="d.cd" :label="`${d.cd} | ${d.name}`" :value="d.cd" />
          </el-select>
        </div>
        <div class="fi-group">
          <el-input v-model="filters.keyword" :placeholder="t('orderMonthly.productSearch')" clearable class="fi-search" size="default">
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
      </div>
    </div>

    <!-- 合計カード -->
    <div class="summary-cards" :class="{ 'animate-in-delay-1': !pageLoading }">
      <el-card class="summary-card modern-card info-card">
        <div class="card-content">
          <div class="card-icon info-icon">
            <el-icon>
              <Document />
            </el-icon>
          </div>
          <div class="card-info">
            <div class="summary-title">{{ t('orderMonthly.summaryForecastUnits') }}</div>
            <div class="summary-value">{{ summary.forecast_units?.toLocaleString() }}</div>
          </div>
        </div>
        <div class="card-decoration"></div>
      </el-card>

      <el-card class="summary-card modern-card success-card">
        <div class="card-content">
          <div class="card-icon success-icon">
            <el-icon>
              <Check />
            </el-icon>
          </div>
          <div class="card-info">
            <div class="summary-title">{{ t('orderMonthly.summaryConfirmedUnits') }}</div>
            <div class="summary-value">{{ summary.forecast_total_units?.toLocaleString() }}</div>
          </div>
        </div>
        <div class="card-decoration"></div>
      </el-card>

      <el-card class="summary-card modern-card diff-card">
        <div class="card-content">
          <div class="card-icon diff-icon">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="card-info">
            <div class="summary-title">{{ t('orderMonthly.summaryForecastDiff') }}</div>
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
              <Operation />
            </el-icon>
          </div>
          <div class="card-info">
            <div class="summary-title">{{ t('orderMonthly.summaryPlating') }}</div>
            <div class="summary-value">{{ summary.plating_count?.toLocaleString() }}</div>
          </div>
        </div>
        <div class="card-decoration"></div>
      </el-card>

      <el-card class="summary-card modern-card external-plating-card">
        <div class="card-content">
          <div class="card-icon external-plating-icon">
            <el-icon>
              <Tools />
            </el-icon>
          </div>
          <div class="card-info">
            <div class="summary-title">{{ t('orderMonthly.summaryExternalPlating') }}</div>
            <div class="summary-value">{{ summary.external_plating_count?.toLocaleString() }}</div>
          </div>
        </div>
        <div class="card-decoration"></div>
      </el-card>

      <el-card class="summary-card modern-card internal-welding-card">
        <div class="card-content">
          <div class="card-icon internal-welding-icon">
            <el-icon>
              <OfficeBuilding />
            </el-icon>
          </div>
          <div class="card-info">
            <div class="summary-title">{{ t('orderMonthly.summaryInternalWelding') }}</div>
            <div class="summary-value">{{ summary.internal_welding_count?.toLocaleString() }}</div>
          </div>
        </div>
        <div class="card-decoration"></div>
      </el-card>

      <el-card class="summary-card modern-card external-welding-card">
        <div class="card-content">
          <div class="card-icon external-welding-icon">
            <el-icon>
              <Tools />
            </el-icon>
          </div>
          <div class="card-info">
            <div class="summary-title">{{ t('orderMonthly.summaryExternalWelding') }}</div>
            <div class="summary-value">{{ summary.external_welding_count?.toLocaleString() }}</div>
          </div>
        </div>
        <div class="card-decoration"></div>
      </el-card>

      <el-card class="summary-card modern-card internal-inspection-card">
        <div class="card-content">
          <div class="card-icon internal-inspection-icon">
            <el-icon>
              <View />
            </el-icon>
          </div>
          <div class="card-info">
            <div class="summary-title">{{ t('orderMonthly.summaryInternalInspection') }}</div>
            <div class="summary-value">{{ summary.internal_inspection_count?.toLocaleString() }}</div>
          </div>
        </div>
        <div class="card-decoration"></div>
      </el-card>

      <el-card class="summary-card modern-card external-inspection-card">
        <div class="card-content">
          <div class="card-icon external-inspection-icon">
            <el-icon>
              <Monitor />
            </el-icon>
          </div>
          <div class="card-info">
            <div class="summary-title">{{ t('orderMonthly.summaryExternalInspection') }}</div>
            <div class="summary-value">{{ summary.external_inspection_count?.toLocaleString() }}</div>
          </div>
        </div>
        <div class="card-decoration"></div>
      </el-card>
    </div>

    <div class="table-section">
      <el-table :data="list" v-loading="loading" stripe border size="small" class="data-table">
        <el-table-column prop="destination_name" :label="t('orderMonthly.tableDestinationName')" min-width="120" show-overflow-tooltip />
        <el-table-column prop="year" :label="t('orderMonthly.tableYear')" width="70" align="center" />
        <el-table-column prop="month" :label="t('orderMonthly.tableMonth')" width="60" align="center" />
        <el-table-column prop="product_cd" :label="t('orderMonthly.tableProductCd')" width="100" />
        <el-table-column prop="product_name" :label="t('orderMonthly.tableProductName')" min-width="120" show-overflow-tooltip />
        <el-table-column prop="product_type" :label="t('orderMonthly.tableType')" width="90" />
        <el-table-column prop="forecast_units" :label="t('orderMonthly.tableForecastUnits')" width="90" align="right" />
        <el-table-column prop="forecast_total_units" :label="t('orderMonthly.tableDailyForecastTotal')" width="100" align="right" />
        <el-table-column prop="forecast_diff" :label="t('orderMonthly.tableForecastDiff')" width="90" align="right">
          <template #default="{ row }">
            <span :class="{ 'cell-negative': Number(row.forecast_diff) < 0 }">{{ row.forecast_diff }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="t('orderMonthly.tableActions')" width="180" fixed="right" align="center">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="openDailyDialog(row)">{{ t('orderMonthly.actionDailyOrder') }}</el-button>
            <el-button size="small" type="primary" link @click="openDialog(row)">{{ t('orderMonthly.actionEdit') }}</el-button>
            <el-button size="small" type="danger" link @click="handleDelete(row)">{{ t('orderMonthly.actionDelete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          layout="total, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
          background
        />
      </div>
    </div>

    <el-dialog v-model="dialogVisible" :title="editId ? t('orderMonthly.editDialogTitleEdit') : t('orderMonthly.editDialogTitleCreate')" width="520px" destroy-on-close @close="resetForm" class="monthly-edit-dialog">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="70px" size="default" class="me-form">
        <div class="me-section">
          <div class="me-section-hd"><el-icon class="me-icon"><Document /></el-icon><span>{{ t('orderMonthly.sectionBasic') }}</span></div>
          <div class="me-section-bd">
            <el-row :gutter="12">
              <el-col :span="12">
                <el-form-item :label="t('orderMonthly.destination')" prop="destination_cd" class="me-item">
                  <el-select v-model="form.destination_cd" :placeholder="t('orderMonthly.select')" filterable style="width:100%" popper-class="destination-select-popper" @change="onDestinationChange">
                    <el-option v-for="d in destinationOptions" :key="d.cd" :label="`${d.cd} ${d.name}`" :value="d.cd" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item :label="t('orderMonthly.product')" prop="product_cd" class="me-item">
                  <el-select v-model="form.product_cd" :placeholder="t('orderMonthly.select')" filterable style="width:100%" @change="onProductChange">
                    <el-option v-for="p in productOptions" :key="p.cd" :label="`${p.cd} ${p.name}`" :value="p.cd" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="12">
              <el-col :span="8">
                <el-form-item :label="t('orderMonthly.filterYear')" prop="year" class="me-item">
                  <el-select v-model="form.year" :placeholder="t('orderMonthly.filterYear')" style="width:100%">
                    <el-option v-for="y in yearOptions" :key="y" :label="String(y)" :value="y" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item :label="t('orderMonthly.filterMonth')" prop="month" class="me-item">
                  <el-select v-model="form.month" :placeholder="t('orderMonthly.filterMonth')" style="width:100%">
                    <el-option v-for="m in 12" :key="m" :label="String(m)" :value="m" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item :label="t('orderMonthly.type')" prop="product_type" class="me-item">
                  <el-select v-model="form.product_type" :placeholder="t('orderMonthly.select')" style="width:100%">
                    <el-option :label="t('orderMonthly.productTypeMass')" value="量産品" />
                    <el-option :label="t('orderMonthly.productTypeTrial')" value="試作品" />
                    <el-option :label="t('orderMonthly.productTypeSpecial')" value="別注品" />
                    <el-option :label="t('orderMonthly.productTypeSupply')" value="補給品" />
                    <el-option :label="t('orderMonthly.productTypeSample')" value="サンプル品" />
                    <el-option :label="t('orderMonthly.productTypeAlt')" value="代替品" />
                    <el-option :label="t('orderMonthly.productTypeReturn')" value="返却品" />
                    <el-option :label="t('orderMonthly.productTypeOther')" value="その他" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
          </div>
        </div>
        <div class="me-section">
          <div class="me-section-hd"><el-icon class="me-icon"><Box /></el-icon><span>{{ t('orderMonthly.sectionQuantity') }}</span></div>
          <div class="me-section-bd">
            <el-row :gutter="12">
              <el-col :span="8">
                <el-form-item :label="t('orderMonthly.forecast')" prop="forecast_units" class="me-item">
                  <el-input-number v-model="form.forecast_units" :min="0" style="width:100%" :controls="false" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item :label="t('orderMonthly.dailyTotal')" prop="forecast_total_units" class="me-item">
                  <el-input-number v-model="form.forecast_total_units" :min="0" style="width:100%" :controls="false" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item :label="t('orderMonthly.diff')" prop="forecast_diff" class="me-item">
                  <el-input-number v-model="form.forecast_diff" style="width:100%" :controls="false" />
                </el-form-item>
              </el-col>
            </el-row>
          </div>
        </div>
      </el-form>
      <template #footer>
        <div class="modern-dialog-ft">
          <el-button @click="dialogVisible = false">{{ t('orderMonthly.cancel') }}</el-button>
          <el-button type="primary" class="btn-accent" :loading="saving" @click="submitForm">{{ t('orderMonthly.save') }}</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- Batch Registration Dialog -->
    <el-dialog v-model="batchDialogVisible" width="900px" destroy-on-close @close="resetBatchForm">
      <template #header>
        <div class="dialog-header compact-header">
          <el-icon class="dialog-icon">
            <Upload />
          </el-icon>
          <span class="dialog-title">{{ t('orderMonthly.batchDialogTitle') }}</span>
        </div>
      </template>
      <div class="batch-form-container">
        <div class="batch-form compact-form">
          <el-form :model="batchForm" :inline="true" class="compact-form-inner batch-form-inline">
            <el-form-item :label="t('orderMonthly.filterYear')" class="inline-form-item">
              <el-select v-model="batchForm.year" :placeholder="t('orderMonthly.yearSelect')" class="year-select">
                <el-option v-for="y in batchYearOptions" :key="y" :label="`${y}年`" :value="y" />
              </el-select>
            </el-form-item>

            <el-form-item :label="t('orderMonthly.filterMonth')" class="inline-form-item">
              <div class="month-select-with-nav">
                <el-select v-model="batchForm.month" :placeholder="t('orderMonthly.monthSelect')" class="month-select">
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
                    {{ t('orderMonthly.thisMonth') }}
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

            <el-form-item :label="t('orderMonthly.destination')" class="inline-form-item">
              <el-select
                v-model="batchForm.destination_cd"
                filterable
                :placeholder="t('orderMonthly.destinationSelect')"
                class="destination-select"
                popper-class="destination-select-popper"
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
                {{ t('orderMonthly.load') }}
              </el-button>
            </el-form-item>
          </el-form>
          <div class="table-container">
            <div v-if="filteredBatchProducts.length > 0" class="table-info">
              <span class="info-text">
                {{ t('orderMonthly.batchTableShowing', { n: filteredBatchProducts.length }) }}
              </span>
            </div>
            <el-table
              v-if="filteredBatchProducts.length > 0"
              :data="filteredBatchProducts"
              class="batch-product-table"
              :loading="batchLoading"
              border
              stripe
              highlight-current-row
              max-height="350"
            >
              <el-table-column :label="t('orderMonthly.batchTableProductType')" width="110" show-overflow-tooltip>
                <template #default="{ row }">
                  <el-tag
                    :type="getProductTypeTagType(row.product_type)"
                    effect="light"
                    size="small"
                  >
                    {{ row.product_type || t('orderMonthly.unset') }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="product_cd" :label="t('orderMonthly.batchTableProductCd')" width="90" />
              <el-table-column
                prop="product_name"
                :label="t('orderMonthly.batchTableProductName')"
                min-width="180"
                show-overflow-tooltip
              />
              <el-table-column :label="t('orderMonthly.batchTableStatus')" width="100" align="center">
                <template #default="{ row }">
                  <el-tag :type="row.exists ? 'info' : 'success'" size="small" effect="plain">
                    {{ row.exists ? t('orderMonthly.statusRegistered') : t('orderMonthly.statusNew') }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column :label="t('orderMonthly.quantity')" width="120" align="center">
                <template #default="{ row, $index }">
                  <el-input
                    v-model="row.quantity"
                    type="text"
                    class="quantity-input"
                    :class="hasQuantity(row.quantity) ? 'normal-cell' : 'warning-cell'"
                    :placeholder="t('orderMonthly.quantity')"
                    @keydown.enter.prevent="handleQuantityEnter($index)"
                    @focus="handleFocus"
                    @input="handleQuantityChange(row)"
                    :id="`quantity-input-${$index}`"
                  />
                </template>
              </el-table-column>
            </el-table>
            <div v-else-if="batchLoading" class="loading-placeholder compact-placeholder">
              <el-icon class="is-loading">
                <LoadingIcon />
              </el-icon>
              <p>{{ t('orderMonthly.batchLoading') }}</p>
            </div>
            <div
              v-else-if="!batchForm.destination_cd"
              class="empty-placeholder compact-placeholder"
            >
              <p>{{ t('orderMonthly.batchEmptySelectDestination') }}</p>
            </div>
            <div v-else class="empty-placeholder compact-placeholder">
              <p>{{ t('orderMonthly.batchEmptyNoData') }}</p>
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
            {{ t('orderMonthly.cancel') }}
          </el-button>
          <el-button type="primary" @click="handleBatchRegister" class="register-btn">
            <el-icon>
              <Check />
            </el-icon>
            {{ t('orderMonthly.batchRegister') }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 日別管理弹窗（月订单维度） -->
    <OrderDailyBatchEditDialog
      v-model:visible="dailyDialogVisible"
      :monthly-order-id="dailyDialogMonthlyOrderId"
      @saved="loadList"
    />

    <!-- 日受注管理弹窗（按日付+納入先） -->
    <OrderDailyManageDialog
      v-model:visible="dailyManageDialogVisible"
      @saved="loadList"
    />

    <!-- EDI取込弹窗 -->
    <el-dialog
      v-model="ediImportDialogVisible"
      :title="t('orderMonthly.btnEdiImport')"
      width="90%"
      class="edi-import-dialog"
      destroy-on-close
    >
      <EdiImport embedded />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import OrderDailyBatchEditDialog from './OrderDailyBatchEditDialog.vue'
import OrderDailyManageDialog from './OrderDailyManageDialog.vue'
import EdiImport from './EdiImport.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Calendar, Search, ArrowLeft, ArrowRight, Upload, Download, Close, Check, Loading as LoadingIcon, Refresh, Document, DocumentAdd, Files, Box, InfoFilled, TrendCharts, Operation, Tools, OfficeBuilding, View, Monitor } from '@element-plus/icons-vue'
import { getDestinationOptions } from '@/api/master/destinationMaster'
import { getProductOptions } from '@/api/options'
import {
  getOrderProducts,
  checkCombinationExists,
  batchCreateMonthly,
  generateDailyOrders,
  updateOrderFields,
} from '@/api/erp/orderBatch'
import {
  fetchOrderMonthlyList,
  fetchMonthlySummary,
  createOrderMonthly,
  updateOrderMonthly,
  deleteOrderMonthly,
  type OrderMonthlyItem,
  type OrderMonthlyCreate,
  type OrderMonthlyFilters,
  type OrderMonthlySummary,
} from '@/api/erp/orderMonthly'
import { fetchOrderDailyList } from '@/api/erp/orderDaily'
import { batchUpdateDailyOrders } from '@/api/order/order'
import type { OrderDailyItem } from '@/api/erp/orderDaily'

const { t } = useI18n()

// 日本時区の現在日付を取得
function getJapanDate(): Date {
  return new Date(new Date().toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' }))
}

const loading = ref(false)
const list = ref<OrderMonthlyItem[]>([])
const now = getJapanDate()
const filters = reactive<OrderMonthlyFilters>({
  year: now.getFullYear(),
  month: now.getMonth() + 1,
})

// 合計カード用（リストと同じ条件で GET /api/order/monthly/summary）
const summary = reactive<OrderMonthlySummary>({
  forecast_units: 0,
  forecast_total_units: 0,
  forecast_diff: 0,
  plating_count: 0,
  external_plating_count: 0,
  internal_welding_count: 0,
  external_welding_count: 0,
  internal_inspection_count: 0,
  external_inspection_count: 0,
})
const pageLoading = computed(() => loading.value)

// 日受注リスト生成
const generating = ref(false)
const progressVisible = ref(false)
const progressPercent = ref(0)
const progressStatus = ref<'success' | 'warning' | 'exception' | undefined>(undefined)
let progressInterval: ReturnType<typeof setInterval> | null = null
let pollTimerId: ReturnType<typeof setInterval> | null = null
let pollCount = 0
const POLL_INTERVAL_MS = 5000
const POLL_MAX = 60

const generateDailyConfirmVisible = ref(false)
const generateDailyConfirmYear = ref<number>(0)
const generateDailyConfirmMonth = ref<number>(0)
const generateDailyConfirmDestinationLabel = ref('')
const destinationOptions = ref<{ cd: string; name: string }[]>([])

// 内示本数更新
const forecastUpdateConfirmVisible = ref(false)
const updatingForecast = ref(false)
const BATCH_SIZE = 100

// 製品情報一括更新
const updateFieldsDialogVisible = ref(false)
const updateFieldsFormRef = ref<FormInstance>()
const updateFieldsSubmitting = ref(false)
const updateFieldsForm = reactive({
  startDate: '' as string,
  updateProductInfo: true,
})
const updateFieldsRules = computed<FormRules>(() => ({
  startDate: [{ required: true, message: t('orderMonthly.validateStartDate'), trigger: 'change' }],
}))
const productOptions = ref<{ cd: string; name: string }[]>([])

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

const yearOptions = computed(() => {
  const y = getJapanDate().getFullYear()
  return [y + 1, y, y - 1, y - 2]
})

async function loadOptions() {
  try {
    const [d, p] = await Promise.all([getDestinationOptions(), getProductOptions()])
    destinationOptions.value = d.map((x) => ({ cd: x.cd, name: x.name }))
    productOptions.value = p.map((x) => ({ cd: x.cd, name: x.name }))
  } catch {
    destinationOptions.value = []
    productOptions.value = []
  }
}

async function loadList() {
  loading.value = true
  try {
    const [allData, summaryRes] = await Promise.all([
      fetchOrderMonthlyList(filters),
      fetchMonthlySummary(filters),
    ])
    pagination.total = allData.length
    const start = (pagination.page - 1) * pagination.pageSize
    const end = start + pagination.pageSize
    list.value = allData.slice(start, end)
    Object.assign(summary, summaryRes)
  } finally {
    loading.value = false
  }
}

function handlePageChange(page: number) {
  pagination.page = page
  loadList()
}

function handleSizeChange(size: number) {
  pagination.pageSize = size
  pagination.page = 1
  loadList()
}

function goPrevPeriod() {
  const japanNow = getJapanDate()
  const y = filters.year ?? japanNow.getFullYear()
  const m = filters.month ?? japanNow.getMonth() + 1
  if (m <= 1) {
    filters.month = 12
    filters.year = y - 1
  } else {
    filters.month = m - 1
    filters.year = y
  }
  loadList()
}

function goNextPeriod() {
  const japanNow = getJapanDate()
  const y = filters.year ?? japanNow.getFullYear()
  const m = filters.month ?? japanNow.getMonth() + 1
  if (m >= 12) {
    filters.month = 1
    filters.year = y + 1
  } else {
    filters.month = m + 1
    filters.year = y
  }
  loadList()
}

function goCurrentMonth() {
  const d = getJapanDate()
  filters.year = d.getFullYear()
  filters.month = d.getMonth() + 1
  loadList()
}

// 自動篩選：期間・納入先変更時は即時、キーワードは 300ms デバウンス
let keywordDebounceTimer: ReturnType<typeof setTimeout> | null = null
watch(
  () => ({ year: filters.year, month: filters.month, destination_cd: filters.destination_cd }),
  () => {
    pagination.page = 1
    loadList()
  },
  { deep: true }
)
watch(
  () => filters.keyword,
  () => {
    if (keywordDebounceTimer) clearTimeout(keywordDebounceTimer)
    keywordDebounceTimer = setTimeout(() => {
      pagination.page = 1
      loadList()
      keywordDebounceTimer = null
    }, 300)
  }
)

const dialogVisible = ref(false)
const formRef = ref<FormInstance>()
const saving = ref(false)
const editId = ref<number | null>(null)

const form = reactive<OrderMonthlyCreate & { destination_name?: string; product_name?: string }>({
  destination_cd: '',
  destination_name: '',
  year: getJapanDate().getFullYear(),
  month: getJapanDate().getMonth() + 1,
  product_cd: '',
  product_name: '',
  product_alias: '',
  product_type: '量産品',
  forecast_units: 0,
  forecast_total_units: 0,
  forecast_diff: 0,
})

const rules = computed<FormRules>(() => ({
  destination_cd: [{ required: true, message: t('orderMonthly.msgSelectDestination'), trigger: 'change' }],
  destination_name: [{ required: true, message: t('orderMonthly.validateDestinationName'), trigger: 'blur' }],
  year: [{ required: true, message: t('orderMonthly.validateYear'), trigger: 'change' }],
  month: [{ required: true, message: t('orderMonthly.validateMonth'), trigger: 'change' }],
  product_cd: [{ required: true, message: t('orderMonthly.validateProduct'), trigger: 'change' }],
  product_name: [{ required: true, message: t('orderMonthly.validateProductName'), trigger: 'blur' }],
}))

function onDestinationChange(cd: string) {
  const d = destinationOptions.value.find((x) => x.cd === cd)
  if (d) form.destination_name = d.name
}

function onProductChange(cd: string) {
  const p = productOptions.value.find((x) => x.cd === cd)
  if (p) form.product_name = p.name
}

function openDialog(row?: OrderMonthlyItem) {
  editId.value = row?.id ?? null
  if (row) {
    form.destination_cd = row.destination_cd
    form.destination_name = row.destination_name
    form.year = row.year
    form.month = row.month
    form.product_cd = row.product_cd
    form.product_name = row.product_name
    form.product_alias = row.product_alias ?? ''
    form.product_type = row.product_type
    form.forecast_units = row.forecast_units
    form.forecast_total_units = row.forecast_total_units
    form.forecast_diff = row.forecast_diff
  } else {
    resetForm()
  }
  dialogVisible.value = true
}

function resetForm() {
  editId.value = null
  form.destination_cd = ''
  form.destination_name = ''
  form.year = getJapanDate().getFullYear()
  form.month = getJapanDate().getMonth() + 1
  form.product_cd = ''
  form.product_name = ''
  form.product_alias = ''
  form.product_type = '量産品'
  form.forecast_units = 0
  form.forecast_total_units = 0
  form.forecast_diff = 0
}

async function submitForm() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  saving.value = true
  try {
    const payload: OrderMonthlyCreate = {
      destination_cd: form.destination_cd,
      destination_name: form.destination_name!,
      year: form.year!,
      month: form.month!,
      product_cd: form.product_cd,
      product_name: form.product_name!,
      product_alias: form.product_alias || undefined,
      product_type: form.product_type,
      forecast_units: form.forecast_units ?? 0,
      forecast_total_units: form.forecast_total_units ?? 0,
      forecast_diff: form.forecast_diff ?? 0,
    }
    if (editId.value != null) {
      await updateOrderMonthly(editId.value, payload)
      ElMessage.success(t('orderMonthly.msgUpdated'))
    } else {
      await createOrderMonthly(payload)
      ElMessage.success(t('orderMonthly.msgCreated'))
    }
    dialogVisible.value = false
    loadList()
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: OrderMonthlyItem) {
  try {
    await ElMessageBox.confirm(t('orderMonthly.confirmDelete', { id: String(row.order_id) }), t('orderMonthly.confirm'), { type: 'warning' })
    await deleteOrderMonthly(row.id)
    ElMessage.success(t('orderMonthly.msgDeleted'))
    loadList()
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error(e?.message || t('orderMonthly.msgDeleteFailed'))
  }
}

function stopProgressInterval() {
  if (progressInterval) {
    clearInterval(progressInterval)
    progressInterval = null
  }
}

function hideProgressAfterDelay() {
  stopProgressInterval()
  setTimeout(() => {
    progressVisible.value = false
    progressPercent.value = 0
    progressStatus.value = undefined
    generating.value = false
  }, 1000)
}

function stopPolling() {
  if (pollTimerId) {
    clearInterval(pollTimerId)
    pollTimerId = null
  }
}

function startPolling() {
  stopPolling()
  pollCount = 0
  const doPoll = async () => {
    pollCount += 1
    if (pollCount > POLL_MAX) {
      stopPolling()
      return
    }
    try {
      await loadList()
      stopPolling()
      ElMessage.success(t('orderMonthly.msgGenerateDailyComplete'))
      progressPercent.value = 100
      progressStatus.value = 'success'
      hideProgressAfterDelay()
    } catch {
      // 次回 5s 後に再試行
    }
  }
  doPoll()
  pollTimerId = setInterval(doPoll, POLL_INTERVAL_MS)
}

function openGenerateDailyConfirmDialog() {
  const year = filters.year
  const month = filters.month
  if (year == null || month == null) {
    ElMessage.warning(t('orderMonthly.msgInvalidYearMonth'))
    return
  }
  generateDailyConfirmYear.value = year
  generateDailyConfirmMonth.value = month
  if (filters.destination_cd) {
    const d = destinationOptions.value.find((x) => x.cd === filters.destination_cd)
    generateDailyConfirmDestinationLabel.value = d ? `${d.cd} | ${d.name}` : filters.destination_cd
  } else {
    generateDailyConfirmDestinationLabel.value = '全納入先'
  }
  generateDailyConfirmVisible.value = true
}

function confirmGenerateDailyOrders() {
  generateDailyConfirmVisible.value = false
  handleGenerateDailyOrders()
}

async function handleGenerateDailyOrders() {
  const year = filters.year
  const month = filters.month
  if (year == null || month == null) {
    ElMessage.warning(t('orderMonthly.msgInvalidYearMonth'))
    return
  }
  generating.value = true
  progressVisible.value = true
  progressPercent.value = 0
  progressStatus.value = undefined
  stopProgressInterval()
  progressInterval = setInterval(() => {
    if (progressPercent.value < 90) {
      progressPercent.value = Math.min(90, progressPercent.value + 5)
    }
  }, 500)
  try {
    await generateDailyOrders({
      year,
      month,
      productType: '量産品',
      ...(filters.destination_cd ? { destination_cd: filters.destination_cd } : {}),
    })
    stopProgressInterval()
    progressPercent.value = 100
    progressStatus.value = 'success'
    ElMessage.success(t('orderMonthly.msgGenerateDailySuccess'))
    await loadList()
    hideProgressAfterDelay()
  } catch (e: any) {
    stopProgressInterval()
    const isTimeoutOrNetwork =
      e?.code === 'ECONNABORTED' ||
      e?.message?.includes('timeout') ||
      e?.message?.includes('Network Error')
    if (isTimeoutOrNetwork) {
      progressPercent.value = 95
      progressStatus.value = 'warning'
      ElMessage.warning(t('orderMonthly.msgBackendProcessing'))
      startPolling()
    } else {
      progressPercent.value = 100
      progressStatus.value = 'exception'
      const msg = e?.response?.data?.detail ?? e?.message ?? '不明なエラー'
      ElMessage.error(`${t('orderMonthly.msgGenerateDailyFailed')}: ${typeof msg === 'string' ? msg : JSON.stringify(msg)}`)
      hideProgressAfterDelay()
    }
  }
}

/** 日付を YYYY-MM-DD に（日本時間の日のみ） */
function formatDateStr(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

/** 納期の日付文字列を正規化（YYYY-MM-DD）。比較は文字列で行いタイムゾーンずれを防ぐ */
function normDate(s: string | null | undefined): string {
  if (!s) return ''
  const part = String(s).trim().slice(0, 10)
  return part.match(/^\d{4}-\d{2}-\d{2}$/) ? part : ''
}

function confirmForecastUpdate() {
  forecastUpdateConfirmVisible.value = false
  runUpdateForecastUnits()
}

/** 内示本数更新：三步ルールで日订单を一括更新（GET daily + POST batch-update） */
async function runUpdateForecastUnits() {
  if (updatingForecast.value) return
  updatingForecast.value = true
  progressVisible.value = true
  progressPercent.value = 0
  progressStatus.value = undefined
  const today = getJapanDate()
  const todayStr = formatDateStr(today)
  const day31Ms = 31 * 24 * 60 * 60 * 1000
  const dMin = new Date(today.getTime() - day31Ms)
  const dMax = new Date(today.getTime() + day31Ms)
  const startDate = formatDateStr(dMin)
  const endDate = formatDateStr(dMax)
  const params: { start_date: string; end_date: string; destination_cd?: string } = {
    start_date: startDate,
    end_date: endDate,
  }
  if (filters.destination_cd) params.destination_cd = filters.destination_cd
  let allRows: OrderDailyItem[] = []
  try {
    allRows = await fetchOrderDailyList(params)
    progressPercent.value = 10
  } catch (e: any) {
    ElMessage.error(e?.message ?? t('orderMonthly.msgDailyDataFetchFailed'))
    updatingForecast.value = false
    progressVisible.value = false
    progressPercent.value = 0
    return
  }
  // 日付は YYYY-MM-DD 文字列で比較し、タイムゾーンによるずれを防ぐ

  const chunk = <T>(arr: T[], size: number): T[][] => {
    const out: T[][] = []
    for (let i = 0; i < arr.length; i += size) out.push(arr.slice(i, i + size))
    return out
  }

  let totalSent = 0
  let totalReflected = 0

  // Step1: 納期が今日±31日 かつ confirmed_units > 0 かつ 内示≠確定 の行のみ → forecast_units = confirmed_units（既に一致している行は送らない）
  const step1List = allRows.filter((r) => {
    const d = normDate(r.delivery_date)
    const cu = Number(r.confirmed_units ?? 0)
    const fu = Number(r.forecast_units ?? 0)
    return d && d >= startDate && d <= endDate && cu > 0 && fu !== cu
  })
  const step1Payloads = step1List.map((r) => ({
    id: r.id,
    forecast_units: Number(r.confirmed_units ?? 0),
    confirmed_boxes: r.confirmed_boxes,
    confirmed_units: r.confirmed_units,
    status: r.status ?? undefined,
    remarks: r.remarks ?? undefined,
  }))
  for (const batch of chunk(step1Payloads, BATCH_SIZE)) {
    totalSent += batch.length
    const res = await batchUpdateDailyOrders({ list: batch })
    totalReflected += res?.updated ?? batch.length
  }
  progressPercent.value = 30

  // Step2: 納期が過去31日～今日 かつ confirmed_units が 0 または空 かつ forecast_units > 0 → 内示クリア
  const step2List = allRows.filter((r) => {
    const d = normDate(r.delivery_date)
    const cu = Number(r.confirmed_units ?? 0)
    const fu = Number(r.forecast_units ?? 0)
    return d && d >= startDate && d <= todayStr && cu <= 0 && fu > 0
  })
  const step2Payloads = step2List.map((r) => ({
    id: r.id,
    forecast_units: 0,
    confirmed_boxes: r.confirmed_boxes,
    confirmed_units: r.confirmed_units,
    status: r.status ?? undefined,
    remarks: r.remarks ?? undefined,
  }))
  for (const batch of chunk(step2Payloads, BATCH_SIZE)) {
    totalSent += batch.length
    const res = await batchUpdateDailyOrders({ list: batch })
    totalReflected += res?.updated ?? batch.length
  }
  progressPercent.value = 50

  // Step3: 製品ごとに「最後に confirmed_boxes > 0 の日」までで、納期 過去31日～その日、確定本数0・内示>0 をクリア（Step2で既に更新したIDは除く）
  const step2Ids = new Set(step2List.map((r) => r.id))
  const byProductLastDate = new Map<string, string>()
  for (const r of allRows) {
    const key = r.product_cd || String(r.id)
    const d = normDate(r.delivery_date)
    const cb = Number(r.confirmed_boxes ?? 0)
    if (cb > 0 && d && d >= startDate && d <= todayStr) {
      const prev = byProductLastDate.get(key) ?? ''
      if (d > prev) byProductLastDate.set(key, d)
    }
  }
  const step3List = allRows.filter((r) => {
    if (step2Ids.has(r.id)) return false
    const key = r.product_cd || String(r.id)
    const lastD = byProductLastDate.get(key)
    if (!lastD) return false
    const d = normDate(r.delivery_date)
    const cu = Number(r.confirmed_units ?? 0)
    const fu = Number(r.forecast_units ?? 0)
    return d && d >= startDate && d <= lastD && cu <= 0 && fu > 0
  })
  const step3Payloads = step3List.map((r) => ({
    id: r.id,
    forecast_units: 0,
    confirmed_boxes: r.confirmed_boxes,
    confirmed_units: r.confirmed_units,
    status: r.status ?? undefined,
    remarks: r.remarks ?? undefined,
  }))
  for (const batch of chunk(step3Payloads, BATCH_SIZE)) {
    totalSent += batch.length
    const res = await batchUpdateDailyOrders({ list: batch })
    totalReflected += res?.updated ?? batch.length
  }
  progressPercent.value = 70

  // Step4: 製品ごとに「その製品で最後に確定本数>0の日付」Lを求め、その日より前のデータで確定<=0・内示>0の行は内示クリア。その製品に確定>0が無い場合は当日を基準に当日以前で確定<=0の行を内示クリア（Step2/Step3で既に送ったIDは除く）
  const step2And3Ids = new Set([...step2List.map((r) => r.id), ...step3List.map((r) => r.id)])
  const lastConfirmedDateByProduct = new Map<string, string>()
  for (const r of allRows) {
    const cu = Number(r.confirmed_units ?? 0)
    if (cu <= 0) continue
    const key = r.product_cd || String(r.id)
    const d = normDate(r.delivery_date)
    if (!d) continue
    const prev = lastConfirmedDateByProduct.get(key) ?? ''
    if (d > prev) lastConfirmedDateByProduct.set(key, d)
  }
  const step4List = allRows.filter((r) => {
    if (step2And3Ids.has(r.id)) return false
    const d = normDate(r.delivery_date)
    const cu = Number(r.confirmed_units ?? 0)
    const fu = Number(r.forecast_units ?? 0)
    if (cu > 0 || fu <= 0) return false
    const key = r.product_cd || String(r.id)
    const lastDate = lastConfirmedDateByProduct.get(key)
    if (lastDate) return d && d < lastDate
    // この製品に確定>0が無い → 当日を基準に、納期が当日以前で確定<=0なら内示クリア
    return d && d <= todayStr
  })
  const step4Payloads = step4List.map((r) => ({
    id: r.id,
    forecast_units: 0,
    confirmed_boxes: r.confirmed_boxes,
    confirmed_units: r.confirmed_units,
    status: r.status ?? undefined,
    remarks: r.remarks ?? undefined,
  }))
  for (const batch of chunk(step4Payloads, BATCH_SIZE)) {
    totalSent += batch.length
    const res = await batchUpdateDailyOrders({ list: batch })
    totalReflected += res?.updated ?? batch.length
  }
  progressPercent.value = 100
  progressStatus.value = 'success'

  updatingForecast.value = false
  const step1Count = step1Payloads.length
  const step2Count = step2Payloads.length
  const step3Count = step3Payloads.length
  const step4Count = step4Payloads.length
  const totalCount = step1Count + step2Count + step3Count + step4Count
  const msg =
    totalCount === 0
      ? '更新対象がありませんでした（条件に該当する日次データがありません）'
      : `内示本数更新完了（Step1: ${step1Count}件、Step2: ${step2Count}件、Step3: ${step3Count}件、Step4: ${step4Count}件、計 ${totalReflected}件を反映）`
  ElMessage.success(msg)
  await loadList()
  setTimeout(() => {
    progressVisible.value = false
    progressPercent.value = 0
    progressStatus.value = undefined
  }, 1200)
}

function openUpdateFieldsDialog() {
  resetUpdateFieldsForm()
  updateFieldsDialogVisible.value = true
}

function resetUpdateFieldsForm() {
  updateFieldsForm.startDate = ''
  updateFieldsForm.updateProductInfo = true
  updateFieldsFormRef.value?.clearValidate()
}

async function submitUpdateFields() {
  if (!updateFieldsFormRef.value) return
  await updateFieldsFormRef.value.validate().catch(() => {})
  if (!updateFieldsForm.startDate) {
    ElMessage.warning(t('orderMonthly.validateStartDate'))
    return
  }
  try {
    await ElMessageBox.confirm(
      t('orderMonthly.confirmUpdateFields'),
      t('orderMonthly.confirm'),
      { confirmButtonText: t('orderMonthly.execute'), cancelButtonText: t('orderMonthly.cancel'), type: 'warning' }
    )
  } catch {
    return
  }
  updateFieldsSubmitting.value = true
  try {
    const res = await updateOrderFields({
      startDate: updateFieldsForm.startDate,
      updateProductInfo: updateFieldsForm.updateProductInfo,
    })
    const count = res?.updatedCount ?? 0
    ElMessage.success(t('orderMonthly.msgUpdateSuccess', { count: String(count) }))
    updateFieldsDialogVisible.value = false
    await loadList()
  } catch (e: any) {
    const msg = e?.response?.data?.detail ?? e?.message ?? '更新に失敗しました'
    ElMessage.error(typeof msg === 'string' ? msg : JSON.stringify(msg))
  } finally {
    updateFieldsSubmitting.value = false
  }
}

// 日別管理弹窗
const dailyDialogVisible = ref(false)
const dailyDialogMonthlyOrderId = ref('')

function openDailyDialog(row: OrderMonthlyItem) {
  dailyDialogMonthlyOrderId.value = row.order_id
  dailyDialogVisible.value = true
}

// 日受注管理弹窗（按日付+納入先）
const dailyManageDialogVisible = ref(false)

function openDailyOrderDialog() {
  dailyManageDialogVisible.value = true
}

const ediImportDialogVisible = ref(false)

function openEdiImportDialog() {
  ediImportDialogVisible.value = true
}

// Batch registration state
const batchDialogVisible = ref(false)
const batchLoading = ref(false)
const batchForm = reactive({
  year: getJapanDate().getFullYear(),
  month: getJapanDate().getMonth() + 1,
  destination_cd: '',
})
const batchProducts = ref<any[]>([])
const batchDestinationOptions = ref<{ cd: string; name: string }[]>([])

const filteredBatchProducts = computed(() => {
  return [...batchProducts.value].sort((a, b) => {
    const nameA = a.product_name || ''
    const nameB = b.product_name || ''
    return nameA.localeCompare(nameB, 'ja')
  })
})

const batchYearOptions = computed(() => {
  const y = getJapanDate().getFullYear()
  return [y + 1, y, y - 1, y - 2]
})

const isBatchCurrentMonth = computed(() => {
  const now = getJapanDate()
  return batchForm.year === now.getFullYear() && batchForm.month === now.getMonth() + 1
})

function openBatchDialog() {
  batchDialogVisible.value = true
  batchDestinationOptions.value = destinationOptions.value
  const now = getJapanDate()
  batchForm.year = now.getFullYear()
  batchForm.month = now.getMonth() + 1
  batchForm.destination_cd = ''
  batchProducts.value = []
}

watch(
  () => batchForm.destination_cd,
  () => {
    if (batchDialogVisible.value && batchForm.destination_cd) batchProducts.value = []
  }
)

function resetBatchForm() {
  batchForm.year = getJapanDate().getFullYear()
  batchForm.month = getJapanDate().getMonth() + 1
  batchForm.destination_cd = ''
  batchProducts.value = []
}

function handleBatchPrevMonth() {
  if (batchForm.month <= 1) {
    batchForm.month = 12
    batchForm.year = batchForm.year - 1
  } else {
    batchForm.month = batchForm.month - 1
  }
}

function handleBatchCurrentMonth() {
  const now = getJapanDate()
  batchForm.year = now.getFullYear()
  batchForm.month = now.getMonth() + 1
}

function handleBatchNextMonth() {
  if (batchForm.month >= 12) {
    batchForm.month = 1
    batchForm.year = batchForm.year + 1
  } else {
    batchForm.month = batchForm.month + 1
  }
}

/** 并发限制：每批最多同时请求数，避免阻塞服务器 */
const BATCH_CHECK_CONCURRENCY = 20

/** 将数组按批执行 async 操作，每批并发 BATCH_CHECK_CONCURRENCY 个 */
async function runInChunks<T, R>(
  items: T[],
  chunkSize: number,
  fn: (item: T, index: number) => Promise<R>
): Promise<R[]> {
  const results: R[] = []
  for (let i = 0; i < items.length; i += chunkSize) {
    const chunk = items.slice(i, i + chunkSize)
    const chunkResults = await Promise.all(
      chunk.map((item, j) => fn(item, i + j))
    )
    results.push(...chunkResults)
  }
  return results
}

async function fetchProducts() {
  if (!batchForm.destination_cd) {
    ElMessage.warning(t('orderMonthly.msgSelectDestination'))
    return
  }
  batchLoading.value = true
  try {
    const res = await getOrderProducts({
      destination_cd: batchForm.destination_cd,
      year: batchForm.year,
      month: batchForm.month,
    })
    const list = res?.data ?? []
    // 補給品・試作品を除外
    const filtered = list.filter(
      (p: { product_type?: string }) =>
        p.product_type !== '補給品' && p.product_type !== '試作品'
    )
    const destinationName =
      batchDestinationOptions.value.find((d) => d.cd === batchForm.destination_cd)?.name || ''
    batchProducts.value = filtered.map((p: { product_cd: string; product_name: string; product_type: string; forecast_units: number }) => ({
      product_cd: p.product_cd,
      product_name: p.product_name,
      product_type: p.product_type || '量産品',
      forecast_units: p.forecast_units,
      quantity: String(p.forecast_units || ''),
      exists: false as boolean,
      orderMonthlyId: null as number | null,
    }))
    // 批量并发检查「组合是否存在」，每批 BATCH_CHECK_CONCURRENCY 个，显著缩短読込时间
    const checkResults = await runInChunks(
      batchProducts.value,
      BATCH_CHECK_CONCURRENCY,
      async (row) => {
        const r = await checkCombinationExists({
          destination_name: destinationName,
          product_name: row.product_name,
          year: batchForm.year,
          month: batchForm.month,
        })
        return r
      }
    )
    checkResults.forEach((r, i) => {
      const row = batchProducts.value[i]
      if (!row) return
      row.exists = r?.exists ?? false
      if (r?.exists && r.id != null) {
        row.orderMonthlyId = r.id
        if (r.forecast_units != null) row.forecast_units = r.forecast_units
      }
    })
  } catch (error: any) {
    ElMessage.error(error?.message || t('orderMonthly.msgProductFetchFailed'))
  } finally {
    batchLoading.value = false
  }
}

function getProductTypeTagType(type: string): 'success' | 'warning' | 'info' | 'primary' | 'danger' {
  const typeMap: Record<string, 'success' | 'warning' | 'info' | 'primary' | 'danger'> = {
    量産品: 'success',
    試作品: 'warning',
    別注品: 'info',
    補給品: 'primary',
    サンプル品: 'info',
    代替品: 'info',
    返却品: 'danger',
    その他: 'info',
  }
  return typeMap[type] || 'info'
}

function handleQuantityEnter(index: number) {
  const nextIndex = index + 1
  if (nextIndex < batchProducts.value.length) {
    const nextInput = document.getElementById(`quantity-input-${nextIndex}`)
    if (nextInput) {
      nextInput.focus()
      ;(nextInput as HTMLInputElement).select()
    }
  }
}

function handleFocus(event: FocusEvent) {
  const input = event.target as HTMLInputElement
  input.select()
}

function handleQuantityChange(row: any) {
  // Ensure numeric value
  const value = row.quantity
  if (value && !/^\d*$/.test(value)) {
    row.quantity = value.replace(/\D/g, '')
  }
}

function hasQuantity(v: any): boolean {
  if (v === '' || v == null) return false
  const n = Number(v)
  return !Number.isNaN(n) && n > 0
}

async function handleBatchRegister() {
  // 新規：不存在且非補給品且数量有效
  const itemsToCreate = batchProducts.value.filter(
    (p) => !p.exists && p.product_type !== '補給品' && hasQuantity(p.quantity)
  )
  // 更新：已存在且数量有变更
  const itemsToUpdate = batchProducts.value.filter(
    (p) =>
      p.exists &&
      p.orderMonthlyId != null &&
      hasQuantity(p.quantity) &&
      Number(p.quantity) !== p.forecast_units
  )
  if (itemsToCreate.length === 0 && itemsToUpdate.length === 0) {
    ElMessage.warning(t('orderMonthly.msgNoBatchTarget'))
    return
  }

  try {
    const createCount = itemsToCreate.length
    const updateCount = itemsToUpdate.length
    const batchConfirmParts: string[] = []
    if (createCount) batchConfirmParts.push(t('orderMonthly.batchConfirmNew', { n: createCount }))
    if (updateCount) batchConfirmParts.push(t('orderMonthly.batchConfirmUpdate', { n: updateCount }))
    await ElMessageBox.confirm(
      batchConfirmParts.join('、') + ' ' + t('orderMonthly.batchConfirmAsk'),
      t('orderMonthly.confirm'),
      { type: 'info' }
    )

    batchLoading.value = true
    const destinationName =
      batchDestinationOptions.value.find((d) => d.cd === batchForm.destination_cd)?.name || ''

    if (itemsToCreate.length > 0) {
      const res = await batchCreateMonthly({
        year: batchForm.year,
        month: batchForm.month,
        destination_cd: batchForm.destination_cd,
        destination_name: destinationName,
        products: itemsToCreate.map((p) => ({
          product_cd: p.product_cd,
          forecast_units: Number(p.quantity) || 0,
        })),
      })
      ElMessage.success(res?.message ?? t('orderMonthly.msgBatchCreated', { n: res?.inserted ?? 0 }))
    }
    for (const p of itemsToUpdate) {
      await updateOrderMonthly(p.orderMonthlyId!, {
        forecast_units: Number(p.quantity) || 0,
      })
    }
    if (itemsToUpdate.length > 0) {
      ElMessage.success(t('orderMonthly.msgBatchUpdated', { n: itemsToUpdate.length }))
    }
    batchDialogVisible.value = false
    loadList()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e?.message || t('orderMonthly.msgBatchFailed'))
    }
  } finally {
    batchLoading.value = false
  }
}

onMounted(() => {
  loadOptions()
  loadList()
})
</script>

<style scoped>
/* ======================================================
   Modern Glassmorphism UI — Compact & Responsive
   ====================================================== */

/* --- Base --- */
.order-monthly-list {
  padding: 12px;
  min-height: 100vh;
  background: linear-gradient(160deg, #f0f4ff 0%, #e8ecf8 40%, #f5f0ff 100%);
}

/* --- Toolbar --- */
.page-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, rgba(99,102,241,0.88) 0%, rgba(139,92,246,0.92) 50%, rgba(168,85,247,0.88) 100%);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  border: 1px solid rgba(255,255,255,0.25);
  border-radius: 14px;
  padding: 10px 18px;
  margin-bottom: 10px;
  box-shadow:
    0 4px 24px rgba(99,102,241,0.25),
    inset 0 1px 0 rgba(255,255,255,0.2);
}
.toolbar-title {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.5px;
  text-shadow: 0 1px 4px rgba(0,0,0,0.15);
}
.toolbar-right {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
}

/* --- Toolbar Buttons (Glass + Color Differentiation) --- */
.tb-btn {
  border-radius: 8px;
  padding: 5px 11px;
  font-size: 12px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border: 1px solid rgba(255,255,255,0.2);
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  color: #fff;
  text-shadow: 0 1px 2px rgba(0,0,0,0.12);
  position: relative;
  overflow: hidden;
}
.tb-btn::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 8px;
  background: linear-gradient(135deg, rgba(255,255,255,0.18) 0%, rgba(255,255,255,0.05) 100%);
  pointer-events: none;
}
.tb-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.15);
  color: #fff;
}
.tb-btn:active {
  transform: translateY(0);
}

/* Blue - 日受注生成 */
.tb-btn-blue {
  background: linear-gradient(135deg, rgba(59,130,246,0.85) 0%, rgba(37,99,235,0.9) 100%);
  box-shadow: 0 2px 10px rgba(59,130,246,0.3);
}
.tb-btn-blue:hover {
  background: linear-gradient(135deg, rgba(59,130,246,1) 0%, rgba(37,99,235,1) 100%);
  box-shadow: 0 4px 18px rgba(59,130,246,0.45);
  color: #fff;
}

/* Teal - 内示更新 */
.tb-btn-teal {
  background: linear-gradient(135deg, rgba(20,184,166,0.85) 0%, rgba(13,148,136,0.9) 100%);
  box-shadow: 0 2px 10px rgba(20,184,166,0.3);
}
.tb-btn-teal:hover {
  background: linear-gradient(135deg, rgba(20,184,166,1) 0%, rgba(13,148,136,1) 100%);
  box-shadow: 0 4px 18px rgba(20,184,166,0.45);
  color: #fff;
}

/* Amber - 製品更新 */
.tb-btn-amber {
  background: linear-gradient(135deg, rgba(245,158,11,0.85) 0%, rgba(217,119,6,0.9) 100%);
  box-shadow: 0 2px 10px rgba(245,158,11,0.3);
}
.tb-btn-amber:hover {
  background: linear-gradient(135deg, rgba(245,158,11,1) 0%, rgba(217,119,6,1) 100%);
  box-shadow: 0 4px 18px rgba(245,158,11,0.45);
  color: #fff;
}

/* Indigo - 日受注 */
.tb-btn-indigo {
  background: linear-gradient(135deg, rgba(99,102,241,0.85) 0%, rgba(79,70,229,0.9) 100%);
  box-shadow: 0 2px 10px rgba(99,102,241,0.3);
}
.tb-btn-indigo:hover {
  background: linear-gradient(135deg, rgba(99,102,241,1) 0%, rgba(79,70,229,1) 100%);
  box-shadow: 0 4px 18px rgba(99,102,241,0.45);
  color: #fff;
}

/* Rose - EDI取込 */
.tb-btn-rose {
  background: linear-gradient(135deg, rgba(244,63,94,0.85) 0%, rgba(225,29,72,0.9) 100%);
  box-shadow: 0 2px 10px rgba(244,63,94,0.3);
}
.tb-btn-rose:hover {
  background: linear-gradient(135deg, rgba(244,63,94,1) 0%, rgba(225,29,72,1) 100%);
  box-shadow: 0 4px 18px rgba(244,63,94,0.45);
  color: #fff;
}

/* Green - 一括登録 */
.tb-btn-green {
  background: linear-gradient(135deg, rgba(16,185,129,0.9) 0%, rgba(5,150,105,0.95) 100%);
  box-shadow: 0 2px 10px rgba(16,185,129,0.35);
  font-weight: 600;
}
.tb-btn-green:hover {
  background: linear-gradient(135deg, rgba(16,185,129,1) 0%, rgba(5,150,105,1) 100%);
  box-shadow: 0 4px 18px rgba(16,185,129,0.5);
  color: #fff;
}

/* --- Progress --- */
.progress-section {
  margin-bottom: 8px;
  padding: 8px 14px;
  background: rgba(255,255,255,0.75);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 10px;
  border: 1px solid rgba(255,255,255,0.6);
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

/* --- Filter Bar (Glass) --- */
.filter-bar {
  background: rgba(255,255,255,0.65);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.05);
  border: 1px solid rgba(255,255,255,0.7);
  padding: 8px 12px;
  margin-bottom: 10px;
}
.filter-inline {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.fi-group {
  display: flex;
  align-items: center;
  gap: 5px;
}
.fi-icon { font-size: 15px; color: #6366f1; }
.fi-year { width: 92px; }
.fi-month { width: 78px; }
.fi-dest { width: 195px; min-width: 150px; }
.fi-search { width: 195px; min-width: 150px; }
.fi-nav {
  display: flex;
  align-items: center;
  gap: 3px;
}
.fi-nav-btn {
  width: 26px; height: 26px; padding: 0;
  border-radius: 6px;
  border: 1px solid rgba(0,0,0,0.08);
  background: rgba(255,255,255,0.8);
  backdrop-filter: blur(4px);
  transition: all 0.2s;
}
.fi-nav-btn:hover {
  border-color: #6366f1;
  color: #6366f1;
  background: rgba(99,102,241,0.08);
}
.fi-now-btn {
  background: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%);
  border: none; color: #fff;
  border-radius: 6px;
  padding: 3px 10px; font-size: 11px;
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(139,92,246,0.25);
  transition: all 0.2s;
}
.fi-now-btn:hover { opacity: 0.9; color: #fff; transform: translateY(-1px); }
.fi-sep { width: 1px; height: 22px; background: rgba(0,0,0,0.08); }

/* --- Summary Cards (Glass) --- */
.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(148px, 1fr));
  gap: 8px;
  margin-bottom: 10px;
}
.summary-cards.animate-in-delay-1 {
  animation: fadeSlideUp 0.45s cubic-bezier(0.4, 0, 0.2, 1);
}
@keyframes fadeSlideUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
.summary-card.modern-card {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.65);
  background: rgba(255,255,255,0.55);
  backdrop-filter: blur(14px) saturate(160%);
  -webkit-backdrop-filter: blur(14px) saturate(160%);
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
  transition: all 0.28s cubic-bezier(0.4, 0, 0.2, 1);
}
.summary-card.modern-card:hover {
  transform: translateY(-3px) scale(1.01);
  box-shadow: 0 8px 24px rgba(0,0,0,0.1);
  border-color: rgba(99,102,241,0.2);
}
.summary-card :deep(.el-card__body) {
  padding: 10px 12px;
  position: relative;
  overflow: hidden;
}
.card-content {
  display: flex;
  align-items: center;
  gap: 8px;
  overflow: hidden;
}
.card-icon {
  width: 34px;
  height: 34px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
  font-size: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.12);
}
.card-icon.info-icon { background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); }
.card-icon.success-icon { background: linear-gradient(135deg, #10b981 0%, #059669 100%); }
.card-icon.diff-icon { background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); }
.card-icon.plating-icon { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); }
.card-icon.external-plating-icon { background: linear-gradient(135deg, #ec4899 0%, #db2777 100%); }
.card-icon.internal-welding-icon { background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%); }
.card-icon.external-welding-icon { background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); }
.card-icon.internal-inspection-icon { background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%); }
.card-icon.external-inspection-icon { background: linear-gradient(135deg, #a855f7 0%, #9333ea 100%); }
.card-info {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}
.summary-title {
  font-size: 10.5px;
  color: #64748b;
  margin-bottom: 1px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
  letter-spacing: 0.2px;
}
.summary-value {
  font-size: 17px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
}
.card-decoration {
  position: absolute;
  right: -8px;
  bottom: -8px;
  width: 52px;
  height: 52px;
  background: linear-gradient(135deg, rgba(99,102,241,0.08) 0%, transparent 100%);
  border-radius: 50%;
  pointer-events: none;
}

/* --- Table Section (Glass) --- */
.table-section {
  background: rgba(255,255,255,0.6);
  backdrop-filter: blur(14px) saturate(160%);
  -webkit-backdrop-filter: blur(14px) saturate(160%);
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.65);
  box-shadow: 0 2px 12px rgba(0,0,0,0.05);
  padding: 10px;
}
/* --- 表格美化：纯黑字体，负数红色 --- */
.data-table { width: 100%; }
.data-table :deep(.el-table__header-wrapper th) {
  background: rgba(248,250,252,0.95) !important;
  color: #000;
  font-weight: 600;
  font-size: 12px;
  border-bottom: 1px solid rgba(0,0,0,0.08);
}
.data-table :deep(.el-table__body-wrapper td.el-table__cell) {
  color: #000;
  font-size: 13px;
}
.data-table :deep(.el-table__row) {
  transition: background-color 0.2s;
}
.data-table :deep(.el-table__row:hover > td) {
  background: rgba(99,102,241,0.05) !important;
}
.data-table .cell-negative {
  color: #c62828;
  font-weight: 600;
}
.pagination-container {
  display: flex; justify-content: flex-end;
  margin-top: 8px; padding: 4px 0;
  font-size: 60%; /* 缩小 40% */
}
.pagination-container :deep(.el-pagination) {
  font-size: inherit;
}
.pagination-container :deep(.el-pagination__total),
.pagination-container :deep(.el-pagination__sizes),
.pagination-container :deep(.el-pager),
.pagination-container :deep(.el-pagination__jump) {
  font-size: inherit;
}
.pagination-container :deep(.el-pagination button),
.pagination-container :deep(.el-pagination .el-pager li) {
  font-size: inherit;
  min-width: 1.6em;
  height: 1.6em;
  line-height: 1.6em;
}
.pagination-container :deep(.el-select .el-input__inner) {
  font-size: inherit;
}
.pagination-container :deep(.el-input__inner) {
  font-size: inherit;
}

/* --- 日受注リスト生成の確認 弹窗美化 --- */
.generate-daily-confirm-dialog :deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 24px 64px rgba(0,0,0,0.18), 0 0 0 1px rgba(255,255,255,0.5) inset;
  border: 1px solid rgba(255,255,255,0.4);
}
.generate-daily-confirm-dialog :deep(.el-dialog__header) {
  padding: 0;
  margin: 0;
}
.generate-daily-confirm-dialog :deep(.el-dialog__body) {
  padding: 0 24px 20px;
  background: linear-gradient(180deg, #fafbff 0%, #f5f6fb 100%);
}
.generate-daily-confirm-dialog :deep(.el-dialog__footer) {
  padding: 14px 24px 20px;
  border-top: 1px solid rgba(0,0,0,0.06);
  background: #fff;
}
.gd-confirm-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 20px 24px;
  background: linear-gradient(135deg, rgba(59,130,246,0.92) 0%, rgba(99,102,241,0.95) 50%, rgba(139,92,246,0.92) 100%);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255,255,255,0.2);
}
.gd-confirm-icon-wrap {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: rgba(255,255,255,0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.gd-confirm-icon {
  font-size: 22px;
  color: #fff;
}
.gd-confirm-title-wrap {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.gd-confirm-title {
  font-size: 16px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.3px;
  line-height: 1.3;
}
.gd-confirm-subtitle {
  font-size: 12px;
  color: rgba(255,255,255,0.88);
  font-weight: 500;
}
.gd-confirm-body {
  padding-top: 18px;
}
.gd-confirm-card {
  background: rgba(255,255,255,0.85);
  backdrop-filter: blur(8px);
  border-radius: 12px;
  padding: 14px 16px;
  border: 1px solid rgba(0,0,0,0.06);
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
}
.gd-confirm-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 8px;
  transition: background 0.2s;
}
.gd-confirm-row:nth-child(odd) {
  background: rgba(99,102,241,0.03);
}
.gd-confirm-row + .gd-confirm-row {
  margin-top: 4px;
}
.gd-confirm-label {
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
}
.gd-confirm-value {
  font-size: 13px;
  color: #000;
  font-weight: 600;
  text-align: right;
  max-width: 60%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.gd-confirm-value.gd-tag {
  background: linear-gradient(135deg, rgba(16,185,129,0.12) 0%, rgba(5,150,105,0.1) 100%);
  color: #047857;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  white-space: nowrap;
}
.gd-confirm-value.gd-dest {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 65%;
}
.gd-confirm-ask {
  margin: 14px 0 0;
  font-size: 13px;
  color: #475569;
  font-weight: 500;
  text-align: center;
}
.gd-confirm-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
.gd-btn-cancel {
  border-radius: 10px;
  padding: 8px 18px;
  font-weight: 500;
  border: 1px solid rgba(0,0,0,0.12);
  color: #475569;
  transition: all 0.2s;
}
.gd-btn-cancel:hover {
  background: #f1f5f9;
  border-color: rgba(0,0,0,0.18);
  color: #000;
}
.gd-btn-submit {
  border-radius: 10px;
  padding: 8px 20px;
  font-weight: 600;
  background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%) !important;
  border: none !important;
  box-shadow: 0 4px 14px rgba(99,102,241,0.35);
  transition: all 0.2s;
}
.gd-btn-submit:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(99,102,241,0.45);
}

/* --- 内示本数更新の確認 弹窗 --- */
.forecast-update-confirm-dialog :deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 24px 64px rgba(0,0,0,0.18), 0 0 0 1px rgba(255,255,255,0.5) inset;
  border: 1px solid rgba(255,255,255,0.4);
}
.forecast-update-confirm-dialog :deep(.el-dialog__header) { padding: 0; margin: 0; }
.forecast-update-confirm-dialog :deep(.el-dialog__body) {
  padding: 0 24px 24px;
  background: linear-gradient(180deg, #f0fdf4 0%, #ecfdf5 100%);
}
.forecast-update-confirm-dialog :deep(.el-dialog__footer) {
  padding: 14px 24px 20px;
  border-top: 1px solid rgba(0,0,0,0.06);
  background: #fff;
}
.fuc-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 20px 24px;
  background: linear-gradient(135deg, rgba(20,184,166,0.92) 0%, rgba(13,148,136,0.95) 100%);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255,255,255,0.2);
}
.fuc-icon-wrap {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: rgba(255,255,255,0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.fuc-icon { font-size: 22px; color: #fff; }
.fuc-title-wrap { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.fuc-title {
  font-size: 16px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.3px;
  line-height: 1.3;
}
.fuc-body { padding-top: 8px; }
.fuc-msg {
  margin: 0;
  font-size: 15px;
  color: #0f766e;
  font-weight: 500;
  line-height: 1.6;
  text-align: center;
}
.fuc-footer { display: flex; justify-content: flex-end; gap: 10px; }
.fuc-btn-cancel {
  border-radius: 10px;
  padding: 8px 18px;
  font-weight: 500;
  border: 1px solid rgba(0,0,0,0.12);
  color: #475569;
  transition: all 0.2s;
}
.fuc-btn-cancel:hover {
  background: #f1f5f9;
  border-color: rgba(0,0,0,0.18);
  color: #000;
}
.fuc-btn-submit {
  border-radius: 10px;
  padding: 8px 20px;
  font-weight: 600;
  background: linear-gradient(135deg, #14b8a6 0%, #0d9488 100%) !important;
  border: none !important;
  box-shadow: 0 4px 14px rgba(20,184,166,0.35);
  transition: all 0.2s;
}
.fuc-btn-submit:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(20,184,166,0.45);
}

/* --- 製品情報一括更新 弹窗 --- */
.update-fields-dialog :deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 24px 64px rgba(0,0,0,0.18), 0 0 0 1px rgba(255,255,255,0.5) inset;
  border: 1px solid rgba(255,255,255,0.4);
}
.update-fields-dialog :deep(.el-dialog__header) { padding: 0; margin: 0; }
.update-fields-dialog :deep(.el-dialog__body) {
  padding: 0 24px 24px;
  background: linear-gradient(180deg, #fffbeb 0%, #fef3c7 100%);
}
.update-fields-dialog :deep(.el-dialog__footer) {
  padding: 14px 24px 20px;
  border-top: 1px solid rgba(0,0,0,0.06);
  background: #fff;
}
.ufd-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 20px 24px;
  background: linear-gradient(135deg, rgba(245,158,11,0.92) 0%, rgba(217,119,6,0.95) 100%);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255,255,255,0.25);
}
.ufd-icon-wrap {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: rgba(255,255,255,0.28);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.ufd-icon { font-size: 22px; color: #fff; }
.ufd-title-wrap { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.ufd-title {
  font-size: 16px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.3px;
  line-height: 1.3;
}
.ufd-subtitle {
  font-size: 12px;
  color: rgba(255,255,255,0.9);
  font-weight: 500;
}
.ufd-body { padding-top: 16px; }
.ufd-form { padding: 0; }
.ufd-form :deep(.el-form-item) { margin-bottom: 14px; }
.ufd-form :deep(.el-form-item:last-child) { margin-bottom: 0; }
.ufd-card {
  background: rgba(255,255,255,0.9);
  backdrop-filter: blur(8px);
  border-radius: 12px;
  padding: 16px 18px;
  border: 1px solid rgba(245,158,11,0.2);
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
}
.ufd-item :deep(.el-form-item__label) {
  font-size: 13px;
  color: #78350f;
  font-weight: 500;
}
.ufd-item :deep(.el-input__wrapper),
.update-fields-dialog :deep(.el-date-editor) {
  border-radius: 8px;
  box-shadow: 0 0 0 1px rgba(0,0,0,0.08);
}
.ufd-check-item { margin-bottom: 8px !important; }
.ufd-checkbox :deep(.el-checkbox__label) {
  font-size: 13px;
  color: #92400e;
  font-weight: 500;
}
.ufd-note {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  margin-top: 4px;
  background: linear-gradient(135deg, rgba(254,243,199,0.9) 0%, rgba(253,230,138,0.5) 100%);
  border-radius: 8px;
  border-left: 3px solid #d97706;
  font-size: 12px;
  color: #92400e;
  line-height: 1.5;
}
.ufd-note .el-icon { margin-top: 2px; color: #d97706; flex-shrink: 0; }
.ufd-footer { display: flex; justify-content: flex-end; gap: 10px; }
.ufd-btn-cancel {
  border-radius: 10px;
  padding: 8px 18px;
  font-weight: 500;
  border: 1px solid rgba(0,0,0,0.12);
  color: #475569;
  transition: all 0.2s;
}
.ufd-btn-cancel:hover {
  background: #f1f5f9;
  border-color: rgba(0,0,0,0.18);
  color: #000;
}
.ufd-btn-submit {
  border-radius: 10px;
  padding: 8px 20px;
  font-weight: 600;
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%) !important;
  border: none !important;
  box-shadow: 0 4px 14px rgba(245,158,11,0.35);
  transition: all 0.2s;
}
.ufd-btn-submit:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(245,158,11,0.45);
}

/* --- Modern Confirm Dialog (Glass) - 其他确认弹窗 --- */
.modern-confirm-dialog :deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0,0,0,0.15);
  border: 1px solid rgba(255,255,255,0.3);
}
.modern-confirm-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
  padding: 12px 20px; margin: 0;
}
.modern-confirm-dialog :deep(.el-dialog__title) { color: #fff; font-size: 14px; font-weight: 600; }
.modern-confirm-dialog :deep(.el-dialog__headerbtn .el-dialog__close) { color: rgba(255,255,255,0.85); }
.modern-confirm-dialog :deep(.el-dialog__body) { padding: 14px 18px; }
.confirm-msg { margin: 0 0 10px; color: #606266; font-size: 13px; line-height: 1.5; }
.confirm-detail {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 10px;
  padding: 10px 14px;
  border: 1px solid rgba(0,0,0,0.05);
}
.confirm-row {
  display: flex; justify-content: space-between;
  padding: 4px 0; font-size: 12.5px;
}
.confirm-row + .confirm-row { border-top: 1px solid rgba(0,0,0,0.05); }
.confirm-key { color: #94a3b8; font-weight: 500; }
.confirm-val { color: #1e293b; font-weight: 600; }
.update-note {
  display: flex; align-items: flex-start; gap: 6px;
  padding: 8px 10px;
  background: linear-gradient(135deg, rgba(59,130,246,0.06) 0%, rgba(99,102,241,0.06) 100%);
  border-radius: 8px; border-left: 3px solid #6366f1;
  font-size: 11.5px; color: #4338ca; margin-top: 4px;
}
.update-note .el-icon { margin-top: 2px; color: #6366f1; }
.modern-dialog-ft { display: flex; justify-content: flex-end; gap: 8px; }
.btn-accent {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border: none; color: #fff; border-radius: 8px; font-weight: 500;
  box-shadow: 0 2px 10px rgba(99,102,241,0.25);
  transition: all 0.2s;
}
.btn-accent:hover {
  opacity: 0.92; color: #fff;
  box-shadow: 0 4px 16px rgba(99,102,241,0.35);
  transform: translateY(-1px);
}

/* --- Monthly Edit Dialog (Glass) --- */
.monthly-edit-dialog :deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0,0,0,0.15);
}
.monthly-edit-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
  padding: 12px 20px; margin: 0;
}
.monthly-edit-dialog :deep(.el-dialog__title) { color: #fff; font-size: 14px; font-weight: 600; }
.monthly-edit-dialog :deep(.el-dialog__headerbtn .el-dialog__close) { color: rgba(255,255,255,0.85); }
.monthly-edit-dialog :deep(.el-dialog__body) { padding: 0; background: #f8fafc; }
.me-form { padding: 0; }
.me-section {
  background: rgba(255,255,255,0.85);
  backdrop-filter: blur(8px);
  margin: 8px; border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 6px rgba(0,0,0,0.04);
  border: 1px solid rgba(0,0,0,0.05);
}
.me-section-hd {
  display: flex; align-items: center; gap: 6px;
  padding: 7px 12px;
  background: linear-gradient(135deg, rgba(99,102,241,0.06) 0%, rgba(139,92,246,0.06) 100%);
  border-bottom: 1px solid rgba(99,102,241,0.1);
  font-size: 12.5px; font-weight: 600; color: #334155;
}
.me-icon { font-size: 15px; color: #6366f1; }
.me-section-bd { padding: 10px; }
.me-item { margin-bottom: 8px !important; }
.me-item:last-child { margin-bottom: 0 !important; }
.me-item :deep(.el-form-item__label) {
  font-size: 12px; padding-right: 4px; line-height: 30px;
}

/* --- Batch Dialog (Glass) --- */
.dialog-header.compact-header { display: flex; align-items: center; gap: 8px; padding: 2px 0; }
.dialog-icon { font-size: 20px; color: #10b981; }
.dialog-title {
  font-size: 15px; font-weight: 600;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
}
.batch-form-container { padding: 0; }
.batch-form.compact-form {
  background: linear-gradient(135deg, rgba(248,250,252,0.9) 0%, rgba(241,245,249,0.9) 100%);
  border-radius: 10px;
  padding: 10px;
}
.batch-form-inline {
  display: flex; flex-wrap: wrap; gap: 8px;
  align-items: flex-end; margin-bottom: 10px;
}
.inline-form-item { margin-bottom: 0 !important; margin-right: 0 !important; }
.inline-form-item .year-select { width: 92px; }
.inline-form-item .month-select { width: 78px; }
.inline-form-item .destination-select { width: 195px; }
.month-select-with-nav { display: flex; align-items: center; gap: 5px; }
.month-nav-buttons { display: flex; gap: 2px; }
.month-nav-btn { padding: 3px 7px; border-radius: 6px; font-size: 11px; }
.month-nav-btn.current-month-btn {
  background: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%);
  border: none; color: #fff;
  box-shadow: 0 2px 6px rgba(139,92,246,0.25);
}
.month-nav-btn.current-month-btn.active {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  box-shadow: 0 2px 6px rgba(16,185,129,0.25);
}
.month-nav-btn.current-month-btn:hover { opacity: 0.9; color: #fff; }
.load-btn {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border: none; border-radius: 8px; color: #fff;
  padding: 5px 12px; font-size: 12px;
  box-shadow: 0 2px 8px rgba(59,130,246,0.25);
  transition: all 0.2s;
}
.load-btn:hover { opacity: 0.9; color: #fff; transform: translateY(-1px); }
.table-container {
  background: rgba(255,255,255,0.8);
  backdrop-filter: blur(8px);
  border-radius: 10px;
  padding: 8px;
}
.table-info {
  display: flex; justify-content: space-between; align-items: center;
  padding: 5px 10px; margin-bottom: 6px;
  background: linear-gradient(135deg, rgba(59,130,246,0.06) 0%, rgba(99,102,241,0.04) 100%);
  border-radius: 8px; border-left: 3px solid #6366f1;
}
.info-text { font-size: 11.5px; color: #4338ca; font-weight: 500; }
.batch-product-table { width: 100%; }
.quantity-input { text-align: center; }
.quantity-input.normal-cell :deep(.el-input__inner) {
  background: rgba(16,185,129,0.08); border-color: rgba(16,185,129,0.3); color: #166534; font-weight: 500;
}
.quantity-input.warning-cell :deep(.el-input__inner) {
  background: rgba(245,158,11,0.08); border-color: rgba(245,158,11,0.3); color: #854d0e;
}
.loading-placeholder.compact-placeholder,
.empty-placeholder.compact-placeholder {
  text-align: center; padding: 24px 14px; color: #94a3b8;
}
.loading-placeholder .is-loading { font-size: 26px; margin-bottom: 8px; }
.empty-placeholder p { margin: 0; font-size: 12.5px; }
.dialog-footer-compact { display: flex; justify-content: flex-end; gap: 8px; }
.cancel-btn { border-radius: 8px; padding: 5px 14px; }
.register-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border: none; border-radius: 8px; padding: 5px 14px; color: #fff;
  box-shadow: 0 2px 10px rgba(16,185,129,0.25);
  transition: all 0.2s;
}
.register-btn:hover { opacity: 0.92; color: #fff; transform: translateY(-1px); }

/* --- EDI Import Dialog --- */
.edi-import-dialog :deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
}

/* --- Global Element Plus Overrides (scoped) --- */
.order-monthly-list :deep(.el-select .el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 0 0 1px rgba(0,0,0,0.08) inset;
  transition: all 0.2s;
}
.order-monthly-list :deep(.el-select .el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px rgba(99,102,241,0.3) inset;
}
.order-monthly-list :deep(.el-select .el-input.is-focus .el-input__wrapper) {
  box-shadow: 0 0 0 1px rgba(99,102,241,0.5) inset, 0 0 0 3px rgba(99,102,241,0.08);
}
.order-monthly-list :deep(.el-input__wrapper) {
  border-radius: 8px;
  transition: all 0.2s;
}
.order-monthly-list :deep(.el-table) {
  --el-table-border-color: rgba(0,0,0,0.08);
  --el-table-header-bg-color: rgba(248,250,252,0.95);
  --el-table-text-color: #000;
  --el-table-row-hover-bg-color: rgba(99,102,241,0.05);
  border-radius: 10px;
  overflow: hidden;
}
.order-monthly-list :deep(.el-table th.el-table__cell) {
  font-size: 12px;
  font-weight: 600;
  color: #000;
}
.order-monthly-list :deep(.el-table td.el-table__cell) {
  font-size: 13px;
  color: #000;
}

/* --- Responsive --- */
@media (max-width: 1200px) {
  .summary-cards {
    grid-template-columns: repeat(auto-fill, minmax(136px, 1fr));
    gap: 6px;
  }
}
@media (max-width: 768px) {
  .order-monthly-list { padding: 8px; }
  .page-toolbar {
    flex-direction: column;
    gap: 8px;
    padding: 10px 12px;
    border-radius: 12px;
  }
  .toolbar-right { justify-content: flex-start; }
  .tb-label { display: none; }
  .tb-btn { padding: 6px 8px; border-radius: 8px; }
  .filter-bar { padding: 6px 10px; }
  .filter-inline { gap: 5px; }
  .fi-dest, .fi-search { width: 140px; min-width: 110px; }
  .fi-sep { display: none; }
  .summary-cards {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 5px;
  }
  .summary-card :deep(.el-card__body) { padding: 8px 10px; }
  .card-icon { width: 30px; height: 30px; font-size: 14px; }
  .summary-title { font-size: 10px; }
  .summary-value { font-size: 14px; }
  .table-section { padding: 6px; border-radius: 10px; }
}
@media (max-width: 480px) {
  .order-monthly-list { padding: 6px; }
  .toolbar-title { font-size: 14px; }
  .toolbar-right { gap: 3px; }
  .tb-btn { padding: 5px 7px; font-size: 11px; }
  .fi-year { width: 78px; }
  .fi-month { width: 68px; }
  .fi-nav-btn { width: 24px; height: 24px; }
  .fi-now-btn { padding: 2px 8px; font-size: 10px; }
  .summary-cards {
    grid-template-columns: repeat(3, 1fr);
    gap: 4px;
  }
  .card-content { gap: 5px; }
  .card-icon { width: 26px; height: 26px; border-radius: 7px; font-size: 12px; }
  .summary-value { font-size: 13px; }
  .pagination-container {
    flex-wrap: wrap;
    justify-content: center;
  }
}
</style>
