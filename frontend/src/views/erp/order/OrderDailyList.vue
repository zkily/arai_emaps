<template>
  <div class="order-daily-page">
    <!-- 动态背景 -->
    <div class="dynamic-background">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
    </div>

    <!-- 页面加载遮罩 -->
    <div v-if="pageLoading" class="page-loading-overlay">
      <div class="loading-container">
        <div class="custom-loader">
          <div class="loader-ring"></div>
          <div class="loader-ring"></div>
          <div class="loader-ring"></div>
        </div>
        <div class="loading-text">データ読み込み中...</div>
        <div class="loading-dots">
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
        </div>
      </div>
    </div>

    <!-- 现代化页面头部 -->
    <div class="modern-header">
      <div class="header-content">
        <div class="header-left">
          <div class="header-icon">
            <el-icon size="32">
              <Calendar />
            </el-icon>
          </div>
          <div class="header-text">
            <h1 class="header-title">日別受注管理</h1>
            <div class="header-subtitle" v-if="filters.day">
              {{ filters.year }}/{{ filters.month }}/{{ filters.day }}
            </div>
          </div>
          <div class="header-badge">
            <span class="badge-count">{{ pagination.total }}</span>
            <span class="badge-label">件</span>
          </div>
        </div>
        <div class="header-right">
          <div class="floating-circles">
            <div class="circle circle-1"></div>
            <div class="circle circle-2"></div>
            <div class="circle circle-3"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 美化统计卡片 -->
    <div class="summary-cards-row">
      <div class="summary-card-item boxes modern-card">
        <div class="card-content">
          <div class="summary-title">確定箱数</div>
          <div class="summary-value animated-count">{{ totalConfirmedBoxes.toLocaleString() }}</div>
        </div>
        <div class="card-decoration"></div>
      </div>
      <div class="summary-card-item units modern-card">
        <div class="card-content">
          <div class="summary-title">確定本数</div>
          <div class="summary-value animated-count">{{ totalConfirmedUnits.toLocaleString() }}</div>
        </div>
        <div class="card-decoration"></div>
      </div>
      <div class="summary-card-item forecast modern-card">
        <div class="card-content">
          <div class="summary-title">内示本数</div>
          <div class="summary-value animated-count">{{ totalForecastUnits.toLocaleString() }}</div>
        </div>
        <div class="card-decoration"></div>
      </div>
      <div class="summary-card-item status modern-card">
        <div class="card-content">
          <div class="summary-title">出荷状態</div>
          <div class="summary-value-split">
            <div class="split-item">
              <span class="split-label">出荷済:</span>
              <span class="split-value">{{ shippedOrdersCount }}</span>
            </div>
            <div class="split-item">
              <span class="split-label">未出荷:</span>
              <span class="split-value">{{ unshippedOrdersCount }}</span>
            </div>
          </div>
        </div>
        <div class="card-decoration"></div>
      </div>
      <div class="summary-card-item confirm modern-card">
        <div class="card-content">
          <div class="summary-title">確認状態</div>
          <div class="summary-value-split">
            <div class="split-item">
              <span class="split-label">確認済:</span>
              <span class="split-value">{{ confirmedOrdersCount }}</span>
            </div>
            <div class="split-item">
              <span class="split-label">未確認:</span>
              <span class="split-value">{{ unconfirmedOrdersCount }}</span>
            </div>
          </div>
        </div>
        <div class="card-decoration"></div>
      </div>
    </div>

    <!-- 美化操作按钮区域 -->
    <div class="action-buttons-section modern-card">
      <div class="section-header">
        <el-icon>
          <Operation />
        </el-icon>
        <span>操作メニュー</span>
      </div>
      <div class="action-buttons-grid">
        <el-button type="primary" class="modern-btn primary-btn" @click="syncToday">
          <el-icon>
            <Calendar />
          </el-icon>
          <span>本日出荷同期</span>
          <div class="btn-shine"></div>
        </el-button>
        <el-button type="info" class="modern-btn info-btn" @click="syncAll">
          <el-icon>
            <FolderOpened />
          </el-icon>
          <span>全期間出荷補完</span>
          <div class="btn-shine"></div>
        </el-button>
        <el-button type="success" class="modern-btn success-btn" @click="openBatchConfirmDialog">
          <el-icon>
            <Check />
          </el-icon>
          <span>一括注文確認</span>
          <div class="btn-shine"></div>
        </el-button>
        <el-button type="warning" class="modern-btn warning-btn" @click="showBatchImportDialog">
          <el-icon>
            <Upload />
          </el-icon>
          <span>日別注文取込</span>
          <div class="btn-shine"></div>
        </el-button>
        <el-button type="success" class="modern-btn success-btn" @click="showAddDialog">
          <el-icon>
            <Plus />
          </el-icon>
          <span>新規追加</span>
          <div class="btn-shine"></div>
        </el-button>
      </div>
    </div>

    <!-- 美化筛选区域 -->
    <div class="filter-section modern-card">
      <div class="section-header">
        <el-icon>
          <Filter />
        </el-icon>
        <span>検索フィルター</span>
      </div>

      <el-form :inline="true" :model="filters" class="modern-filter-form">
        <!-- 第一行：期間、納入先、製品検索 -->
        <div class="filter-row main-filters">
          <el-form-item label="期間" class="modern-form-item">
            <div class="date-filter-group">
              <el-select
                v-model="filters.year"
                placeholder="年"
                class="modern-select"
                @change="handleYearMonthChange"
              >
                <el-option
                  v-for="year in yearOptions"
                  :key="year"
                  :label="`${year}年`"
                  :value="year"
                />
              </el-select>
              <el-select
                v-model="filters.month"
                placeholder="月"
                class="modern-select"
                @change="handleYearMonthChange"
              >
                <el-option v-for="m in 12" :key="m" :label="`${m}月`" :value="m" />
              </el-select>
              <el-select
                v-model="filters.day"
                placeholder="日"
                class="modern-select"
                @change="handleDayChange"
                clearable
              >
                <el-option v-for="d in daysInMonth" :key="d" :label="`${d}日`" :value="d" />
              </el-select>
              <div class="date-nav-buttons">
                <el-tooltip content="前日" placement="top">
                  <el-button size="small" class="nav-btn" @click="handlePrevDay">
                    <el-icon>
                      <ArrowLeft /> </el-icon
                    >日
                  </el-button>
                </el-tooltip>
                <el-tooltip content="今日" placement="top">
                  <el-button
                    size="small"
                    type="primary"
                    class="nav-btn today-btn"
                    @click="handleToday"
                    >今日</el-button
                  >
                </el-tooltip>
                <el-tooltip content="翌日" placement="top">
                  <el-button size="small" class="nav-btn" @click="handleNextDay">
                    日<el-icon>
                      <ArrowRight />
                    </el-icon>
                  </el-button>
                </el-tooltip>
                <el-tooltip content="前月" placement="top">
                  <el-button size="small" class="nav-btn" @click="handlePrevMonth">
                    <el-icon>
                      <ArrowLeft /> </el-icon
                    >月
                  </el-button>
                </el-tooltip>
                <el-tooltip content="翌月" placement="top">
                  <el-button size="small" class="nav-btn" @click="handleNextMonth">
                    月<el-icon>
                      <ArrowRight />
                    </el-icon>
                  </el-button>
                </el-tooltip>
              </div>
            </div>
          </el-form-item>

          <el-form-item label="納入先" class="modern-form-item">
            <el-select
              v-model="filters.destination_cd"
              filterable
              placeholder="納入先を選択"
              clearable
              class="modern-select destination-select"
              @change="refreshData"
            >
              <el-option
                v-for="item in validDestinationOptions"
                :key="item.cd"
                :label="`${item.cd} | ${item.name}`"
                :value="item.cd"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="製品検索" class="modern-form-item">
            <el-input
              v-model="filters.keyword"
              placeholder="製品名"
              clearable
              class="modern-input"
              @input="debounceSearch"
            >
              <template #prefix>
                <el-icon>
                  <Search />
                </el-icon>
              </template>
            </el-input>
          </el-form-item>
        </div>

        <!-- 第二行：一括状態更新和指定日検索 -->
        <div class="filter-row secondary-filters">
          <div class="batch-update-section">
            <el-form-item label="一括状態更新" class="modern-form-item">
              <div class="batch-controls">
                <el-date-picker
                  v-model="batchUpdateDate"
                  type="date"
                  placeholder="対象日"
                  format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD"
                  class="modern-date-picker"
                />
                <el-select v-model="batchUpdateStatus" placeholder="状態" class="modern-select">
                  <el-option label="未出荷" value="未出荷" />
                  <el-option label="出荷済" value="出荷済" />
                  <el-option label="キャンセル" value="キャンセル" />
                </el-select>
                <el-button
                  type="success"
                  @click="handleBatchStatusUpdate"
                  class="modern-btn update-btn"
                >
                  <el-icon>
                    <Refresh />
                  </el-icon>
                  更新
                </el-button>
              </div>
            </el-form-item>
          </div>

          <div class="specific-date-section">
            <el-form-item label="指定日検索" class="modern-form-item">
              <div class="specific-date-group">
                <el-date-picker
                  v-model="searchSpecificDate"
                  type="date"
                  placeholder="検索日付"
                  format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD"
                  class="modern-date-picker"
                  @change="refreshData"
                />
                <el-button
                  type="primary"
                  @click="handleSearchByDate"
                  class="modern-btn search-btn"
                  :loading="searchLoading"
                >
                  <el-icon>
                    <Search />
                  </el-icon>
                  {{ searchLoading ? '検索中...' : '検索' }}
                </el-button>
              </div>
            </el-form-item>
          </div>

          <div class="utility-buttons">
            <el-button type="info" plain class="modern-btn reset-btn" @click="resetFilter">
              <el-icon>
                <Refresh />
              </el-icon>
              リセット
            </el-button>
            <el-button type="success" plain class="modern-btn print-btn" @click="handlePrint">
              <el-icon>
                <Printer />
              </el-icon>
              印刷
            </el-button>
          </div>
        </div>
      </el-form>
    </div>

    <!-- 美化表格区域 -->
    <div class="table-section modern-card">
      <div class="table-header">
        <div class="table-title">
          <el-icon>
            <List />
          </el-icon>
          <span>注文一覧</span>
          <div class="table-count-badge">
            <span class="count">{{ pagination.total }}</span>
            <span class="label">件</span>
          </div>
        </div>
      </div>

      <div class="table-wrapper">
        <el-table :data="orderList" border stripe v-loading="loading" class="modern-table">
          <el-table-column label="年" prop="year" width="70" align="center">
            <template #default="{ row }">
              <div class="table-cell-content">
                <el-icon size="14">
                  <Calendar />
                </el-icon>
                <span>{{ row.year }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="月" prop="month" width="50" align="center">
            <template #default="{ row }">
              <span class="month-cell">{{ row.month }}</span>
            </template>
          </el-table-column>
          <el-table-column label="日" prop="day" width="50" align="center">
            <template #default="{ row }">
              <span class="day-cell">{{ row.day }}</span>
            </template>
          </el-table-column>
          <el-table-column label="曜日" prop="weekday" width="60" align="center">
            <template #default="{ row }">
              <el-tag size="small" :type="getWeekdayTagType(row.weekday)">
                {{ row.weekday }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="納入日" prop="delivery_date" width="70" align="center">
            <template #default="{ row }">
              <div class="table-cell-content">
                <el-icon size="14">
                  <Promotion />
                </el-icon>
                <span>{{ formatDate(row.delivery_date) }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="納入先名" prop="destination_name" min-width="180">
            <template #default="{ row }">
              <div class="table-cell-content">
                <el-icon size="14">
                  <Shop />
                </el-icon>
                <span>{{ row.destination_name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="製品名" prop="product_name" min-width="150">
            <template #default="{ row }">
              <div class="table-cell-content">
                <el-icon size="14">
                  <Goods />
                </el-icon>
                <span>{{ row.product_name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="製品タイプ" prop="product_type" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="getProductTypeTagType(row.product_type)" class="animated-tag">
                {{ row.product_type || '未分類' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="入数" prop="unit_per_box" width="55" align="center">
            <template #default="{ row }">
              <span class="number-cell">{{ row.unit_per_box }}</span>
            </template>
          </el-table-column>
          <el-table-column label="確定箱数" prop="confirmed_boxes" width="85" align="center">
            <template #default="{ row }">
              <span class="number-cell highlight-number">
                {{ row.confirmed_boxes > 0 ? row.confirmed_boxes : '' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="確定本数" prop="confirmed_units" width="85" align="center">
            <template #default="{ row }">
              <span class="number-cell highlight-number">
                {{ row.confirmed_units > 0 ? row.confirmed_units : '' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="状態" prop="status" width="100" align="center">
            <template #default="{ row }">
              <el-tag
                :type="
                  row.status === '出荷済'
                    ? 'success'
                    : row.status === 'キャンセル'
                      ? 'danger'
                      : 'info'
                "
                class="status-tag animated-tag"
              >
                <el-icon size="12">
                  <Check v-if="row.status === '出荷済'" />
                  <Close v-else-if="row.status === 'キャンセル'" />
                  <Clock v-else />
                </el-icon>
                {{ row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="確認状態" prop="confirmed" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.confirmed ? 'success' : 'info'" class="confirm-tag animated-tag">
                <el-icon size="12">
                  <CircleCheck v-if="row.confirmed" />
                  <Clock v-else />
                </el-icon>
                {{ row.confirmed ? '確認済' : '未確認' }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="190" fixed="right" align="center">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-tooltip content="編集" placement="top">
                  <el-button
                    size="small"
                    type="primary"
                    class="action-btn edit-btn"
                    @click="handleEdit(row)"
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
                    class="action-btn delete-btn"
                    @click="handleDelete(row)"
                  >
                    <el-icon>
                      <Delete />
                    </el-icon>
                  </el-button>
                </el-tooltip>
                <el-tooltip content="確認" placement="top">
                  <el-button
                    size="small"
                    type="success"
                    class="action-btn confirm-btn"
                    :disabled="!!row.confirmed"
                    @click="handleConfirm(row)"
                  >
                    <el-icon>
                      <Check />
                    </el-icon>
                    確認
                  </el-button>
                </el-tooltip>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 美化分页组件 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          class="modern-pagination"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>

      <!-- 数据总计 -->
      <div class="data-summary">
        <el-icon>
          <DataLine />
        </el-icon>
        <span
          >合計 <strong>{{ pagination.total }}</strong> 件の注文データ</span
        >
      </div>
    </div>

    <!-- 编辑弹窗 -->
    <OrderDailyEditDialog
      :visible="editDialogVisible"
      :order="currentOrder"
      class="modern-dialog"
      @update:visible="(val) => (editDialogVisible = val)"
      @saved="handleEditSaved"
    />

    <!-- 批量编辑弹窗 -->
    <OrderDailyBatchEditDialog
      v-if="batchDialogVisible"
      v-model:visible="batchDialogVisible"
      class="modern-dialog"
      :monthlyOrderId="selectedMonthlyOrderId"
      @saved="handleBatchEditSaved"
    />

    <OrderDailyBatchImportDialog
      v-model:visible="batchImportDialogVisible"
      class="modern-dialog"
      :destination_cd="filters.destination_cd"
      @imported="refreshData"
    />

    <OrderDailyAddDialog
      v-model:visible="addDialogVisible"
      class="modern-dialog"
      @saved="handleAddSaved"
    />

    <!-- 批量确认弹窗 -->
    <el-dialog
      v-model="batchConfirmDialogVisible"
      title="一括注文確認"
      width="50%"
      class="modern-dialog"
    >
      <div class="batch-confirm-header">
        <el-form inline class="batch-confirm-form">
          <el-form-item label="日付">
            <el-date-picker
              v-model="batchConfirmDate"
              type="date"
              placeholder="日付を選択"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              class="modern-date-picker"
            />
          </el-form-item>
          <el-form-item label="納入先">
            <el-select
              v-model="batchConfirmDestination"
              filterable
              placeholder="納入先を選択"
              class="modern-select"
              style="width: 220px"
            >
              <el-option
                v-for="item in validDestinationOptions"
                :key="item.cd"
                :label="`${item.cd} | ${item.name}`"
                :value="item.cd"
              />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button
              type="primary"
              @click="fetchBatchConfirmOrders"
              :loading="batchConfirmLoading"
              class="modern-btn"
            >
              <el-icon>
                <Search />
              </el-icon>
              注文検索
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <div v-if="batchConfirmOrderList.length > 0" class="batch-confirm-stats">
        <div class="stats-item">
          <span class="stats-label">合計</span>
          <span class="stats-value">{{ batchConfirmOrderList.length }}</span>
          <span class="stats-unit">件の注文</span>
        </div>
        <div class="stats-item">
          <span class="stats-label">選択済</span>
          <span class="stats-value highlight">{{ batchConfirmSelected.length }}</span>
          <span class="stats-unit">件</span>
        </div>
        <div class="stats-buttons">
          <el-button
            type="default"
            size="small"
            class="modern-btn"
            @click="selectAllBatchConfirmOrders"
            >全選択</el-button
          >
          <el-button
            type="default"
            size="small"
            class="modern-btn"
            @click="unselectAllBatchConfirmOrders"
            >選択解除</el-button
          >
        </div>
      </div>

      <el-table
        ref="batchConfirmTableRef"
        :data="batchConfirmOrderList"
        class="modern-table"
        @selection-change="batchConfirmSelected = $event"
        height="350px"
        border
        v-loading="batchConfirmLoading"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column label="積込日" width="100">
          <template #default="{ row }">
            <div class="table-cell-content">
              <el-icon size="14">
                <Calendar />
              </el-icon>
              <span>{{ `${row.year}-${row.month}-${row.day}` }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="納入日" width="80">
          <template #default="{ row }">
            <div class="table-cell-content">
              <el-icon size="14">
                <Promotion />
              </el-icon>
              <span>{{ formatDate(row.delivery_date) }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="製品名" prop="product_name" min-width="150">
          <template #default="{ row }">
            <div class="table-cell-content">
              <el-icon size="14">
                <Goods />
              </el-icon>
              <span>{{ row.product_name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="確定箱数" prop="confirmed_boxes" width="90" align="right">
          <template #default="{ row }">
            <span class="number-cell">{{ row.confirmed_boxes }}</span>
          </template>
        </el-table-column>
        <el-table-column label="確定本数" prop="confirmed_units" width="90" align="right">
          <template #default="{ row }">
            <span class="number-cell">{{ row.confirmed_units }}</span>
          </template>
        </el-table-column>
        <el-table-column label="確認状態" prop="confirmed" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.confirmed ? 'success' : 'info'" class="animated-tag">
              <el-icon size="12">
                <CircleCheck v-if="row.confirmed" />
                <Clock v-else />
              </el-icon>
              {{ row.confirmed ? '確認済' : '未確認' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <el-empty
        v-if="batchConfirmOrderList.length === 0 && batchConfirmSearched && !batchConfirmLoading"
        description="確認が必要な注文はありません"
      />

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="batchConfirmDialogVisible = false" class="modern-btn"
            >キャンセル</el-button
          >
          <el-button
            type="success"
            @click="handleBatchConfirm"
            :disabled="batchConfirmSelected.length === 0"
            :loading="batchConfirmSubmitting"
            class="modern-btn"
          >
            <el-icon>
              <Check />
            </el-icon>
            一括確認 ({{ batchConfirmSelected.length }})
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox, ElLoading, ElNotification } from 'element-plus'
import {
  Search,
  Check,
  Refresh,
  Printer,
  Calendar,
  Box,
  Goods,
  Van,
  CircleCheck,
  Operation,
  Filter,
  Plus,
  Upload,
  FolderOpened,
  ArrowLeft,
  ArrowRight,
  List,
  Promotion,
  Shop,
  Clock,
  Close,
  Edit,
  Delete,
  DataLine,
} from '@element-plus/icons-vue'
import { jsPDF } from 'jspdf'
import html2canvas from 'html2canvas'
// 引入字体
import { createApp } from 'vue'

import OrderDailyEditDialog from './components/OrderDailyEditDialog.vue'
import OrderDailyBatchEditDialog from './components/OrderDailyBatchEditDialog.vue'
import OrderDailyBatchImportDialog from './components/OrderDailyBatchImportDialog.vue'
import OrderDailyAddDialog from './components/OrderDailyAddDialog.vue'

import {
  fetchDailyOrders,
  updateOrderDailyStatus,
  fetchDailyOrdersByDate,
  syncShippingLog,
  deleteDailyOrder,
  confirmOrder,
} from '@/api/order/order'
import { getDestinationOptions } from '@/api/options'
import type { OrderDaily, FetchDailyOrdersParams } from '@/types/order'
import type { Destination } from '@/types/master'

// 页面加载状态
const pageLoading = ref(true)
const searchLoading = ref(false)

// 获取日本时区的当前日期
const getJapanDate = (): Date => {
  const now = new Date()
  // 使用Intl.DateTimeFormat获取日本时区的日期和时间组件
  const formatter = new Intl.DateTimeFormat('en-US', {
    timeZone: 'Asia/Tokyo',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  })

  const parts = formatter.formatToParts(now)
  const year = parseInt(parts.find((p) => p.type === 'year')?.value || '0')
  const month = parseInt(parts.find((p) => p.type === 'month')?.value || '0')
  const day = parseInt(parts.find((p) => p.type === 'day')?.value || '0')
  const hour = parseInt(parts.find((p) => p.type === 'hour')?.value || '0')
  const minute = parseInt(parts.find((p) => p.type === 'minute')?.value || '0')
  const second = parseInt(parts.find((p) => p.type === 'second')?.value || '0')

  // 返回日本时区的Date对象（使用本地时区，但值来自日本时区）
  return new Date(year, month - 1, day, hour, minute, second)
}

// 获取日本时区的当前日期字符串（YYYY-MM-DD格式）
const getJapanDateString = (): string => {
  const now = new Date()
  // 使用Intl.DateTimeFormat获取日本时区的日期部分
  const formatter = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Tokyo',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
  return formatter.format(now)
}

// 日期格式化函数（使用日本时区）
const formatDate = (dateString: string | null | undefined): string => {
  if (!dateString) return '-'
  try {
    // 将日期字符串转换为日本时区的日期
    const date = new Date(dateString)
    const japanDate = new Date(date.toLocaleString('en-US', { timeZone: 'Asia/Tokyo' }))
    return `${japanDate.getMonth() + 1}/${japanDate.getDate()}`
  } catch (e) {
    return dateString.toString()
  }
}

// 获取曜日标签类型
const getWeekdayTagType = (weekday: string) => {
  switch (weekday) {
    case '土':
      return 'info'
    case '日':
      return 'danger'
    default:
      return undefined
  }
}

// 📌 筛选条件（使用日本时区）
const japanDate = getJapanDate()
const filters = ref({
  year: japanDate.getFullYear(),
  month: japanDate.getMonth() + 1,
  day: japanDate.getDate(), // 设置为当天日期（日本时区）
  destination_cd: '',
  keyword: '',
  dateRange: [],
})

// 📌 年份下拉（使用日本时区）
const yearOptions = Array.from({ length: 6 }, (_, i) => japanDate.getFullYear() - 3 + i)

// 计算当前月份的天数
const daysInMonth = computed(() => {
  const year = filters.value.year
  const month = filters.value.month
  if (!year || !month) return 31
  return new Date(year, month, 0).getDate()
})

// 📌 纳入先下拉列表
const destinationOptions = ref<Destination[]>([])
const validDestinationOptions = computed(() =>
  destinationOptions.value.filter((item) => item.cd && item.name),
)

// 📌 订单列表 & 加载状态
const orderList = ref<OrderDaily[]>([])
const loading = ref(false)
const allStats = ref({
  totalConfirmedBoxes: 0,
  totalConfirmedUnits: 0,
  totalForecastUnits: 0,
  shipped: 0,
  unshipped: 0,
  confirmed: 0,
  unconfirmed: 0,
})

// 📌 分页状态
const pagination = ref({
  page: 1,
  pageSize: 20, // 默认每页显示20条
  total: 0,
})

// 防抖搜索函数
let searchTimeout: number | null = null
const debounceSearch = () => {
  if (searchTimeout !== null) {
    clearTimeout(searchTimeout)
  }
  searchTimeout = window.setTimeout(() => {
    refreshData()
  }, 500)
}

// 📌 获取日受注列表
const fetchList = async () => {
  loading.value = true
  try {
    const params: FetchDailyOrdersParams = {
      year: filters.value.year,
      month: filters.value.month,
      day: filters.value.day ? Number(filters.value.day) : undefined,
      destination_cd: filters.value.destination_cd,
      keyword: filters.value.keyword,
      specificDate: searchSpecificDate.value,
      page: pagination.value.page,
      pageSize: pagination.value.pageSize,
    }
    const data = (await fetchDailyOrders(params)) as unknown as {
      list: OrderDaily[]
      total: number
    }
    orderList.value = Array.isArray(data.list) ? data.list : []
    pagination.value.total =
      typeof data.total === 'number' ? data.total : orderList.value.length || 0
  } catch (error) {
    orderList.value = []
    pagination.value.total = 0
  } finally {
    loading.value = false
  }
}

// 获取全部数据用于统计
const fetchAllStats = async () => {
  try {
    const params: FetchDailyOrdersParams = {
      year: filters.value.year,
      month: filters.value.month,
      day: filters.value.day ? Number(filters.value.day) : undefined,
      destination_cd: filters.value.destination_cd,
      keyword: filters.value.keyword,
      specificDate: searchSpecificDate.value,
      // 不传page/pageSize
    }
    const res = await fetchDailyOrders(params)
    let list: OrderDaily[] = []

    // 更灵活地处理各种响应结构
    if (res && res.data && Array.isArray(res.data.list)) {
      list = res.data.list
    } else if (res && Array.isArray(res.list)) {
      list = res.list
    } else if (res && res.data && Array.isArray(res.data)) {
      list = res.data
    } else if (Array.isArray(res)) {
      list = res
    }

    // 计算统计数据
    allStats.value.totalConfirmedBoxes = list.reduce(
      (sum, order) => sum + (Number(order.confirmed_boxes) || 0),
      0,
    )
    allStats.value.totalConfirmedUnits = list.reduce(
      (sum, order) => sum + (Number(order.confirmed_units) || 0),
      0,
    )
    allStats.value.totalForecastUnits = list.reduce(
      (sum, order) => sum + (Number(order.forecast_units) || 0),
      0,
    )
    allStats.value.shipped = list.filter((order) => order.status === '出荷済').length
    allStats.value.unshipped = list.filter((order) => order.status === '未出荷').length
    allStats.value.confirmed = list.filter((order) => !!order.confirmed).length
    allStats.value.unconfirmed = list.filter((order) => !order.confirmed).length
  } catch (e) {
    console.error('统计数据获取失败', e)
    allStats.value = {
      totalConfirmedBoxes: 0,
      totalConfirmedUnits: 0,
      totalForecastUnits: 0,
      shipped: 0,
      unshipped: 0,
      confirmed: 0,
      unconfirmed: 0,
    }
  }
}

// 在筛选条件变化时获取数据（现在fetchList已包含总计计算）
const refreshData = async () => {
  await Promise.all([fetchList(), fetchAllStats()])
}

// 📌 纳入先列表取得
const fetchDestinationList = async () => {
  try {
    destinationOptions.value = await getDestinationOptions()
  } catch (error) {
    console.error('納入先オプションの取得に失敗しました', error)
  }
}

// 📌 重置筛选（使用日本时区）
const resetFilter = () => {
  const japanDate = getJapanDate()
  filters.value = {
    year: japanDate.getFullYear(),
    month: japanDate.getMonth() + 1,
    day: japanDate.getDate(),
    destination_cd: '',
    keyword: '',
    dateRange: [],
  }
  searchSpecificDate.value = ''
  pagination.value.page = 1 // 重置页码
  refreshData()
}

// 📌 前の月・次の月处理
const handlePrevMonth = () => {
  if (filters.value.month === 1) {
    filters.value.year--
    filters.value.month = 12
  } else {
    filters.value.month--
  }
  refreshData()
}

const handleNextMonth = () => {
  if (filters.value.month === 12) {
    filters.value.year++
    filters.value.month = 1
  } else {
    filters.value.month++
  }
  refreshData()
}

// 出荷履歴一括同期
// const doBatchShippingSync = async () => {
//   try {
//     const res = await request.post('/api/order/batch-shipping-sync')
//     if (res && res.message) {
//       ElMessage.success(res.message)
//     } else {
//       ElMessage.success('出荷履歴同期が完了しました')
//     }
//     fetchList()
//   } catch (e) {
//     ElMessage.error((e as Error).message ?? '同期失敗')
//   }
// }
const syncToday = async () => {
  try {
    // 添加确认对话框
    await ElMessageBox.confirm(
      '本日分の出荷データを同期しますか？\n(状態が「出荷済」かつ確定本数>0の注文を在庫流水表に同期します)',
      '確認',
      {
        confirmButtonText: '実行',
        cancelButtonText: 'キャンセル',
        type: 'info',
      },
    )

    const loading = ElLoading.service({
      lock: true,
      text: '本日データ同期中...',
      background: 'rgba(0, 0, 0, 0.7)',
    })

    try {
      // 1. 先将今天的订单状态更新为"出荷済"（使用日本时区）
      const today = getJapanDateString()
      const statusUpdateResult = await updateOrderDailyStatus({
        date: today,
        status: '出荷済',
      })

      // 如果更新了订单状态，显示通知
      if (statusUpdateResult && statusUpdateResult.updated > 0) {
        ElMessage.success(`${statusUpdateResult.updated}件の注文状態を「出荷済」に更新しました`)
      }

      // 2. 然后执行同步操作
      const res = await syncShippingLog('today')

      // 详细信息通知
      if (res.data) {
        const { inserted, skipped, errors, totalRecords } = res.data

        // 处理无数据情况
        if (totalRecords === 0) {
          ElMessage({
            message: '本日の対象データがありません（状態が「出荷済」かつ確定本数>0の注文）',
            type: 'warning',
            duration: 5000,
          })
          return
        }

        const resultMessage =
          res.data.message ||
          `${inserted}件の注文を同期しました（${skipped}件スキップ、${errors}件エラー）`

        // 弹出一个带有详细信息的通知
        ElNotification({
          title: '本日分同期完了',
          message: `総計: ${totalRecords}件\n同期: ${inserted}件\nスキップ: ${skipped}件\nエラー: ${errors}件`,
          type: 'success',
          duration: 5000,
          position: 'bottom-right',
        })

        // 同时显示一个简短的消息
        ElMessage({
          message: resultMessage,
          type: 'success',
          duration: 3000,
        })
      } else {
        ElMessage.success(res.message || '本日分の確定本数>0の注文を在庫流水表に同期しました')
      }

      // 刷新数据
      await refreshData()
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : '同期に失敗しました'
      console.error('同期エラー:', errorMessage)
      ElMessage.error(errorMessage)
    } finally {
      loading.close()
    }
  } catch (err) {
    if (err !== 'cancel') {
      const errorMessage = err instanceof Error ? err.message : '同期に失敗しました'
      console.error('同期エラー:', errorMessage)
      ElMessage.error(errorMessage)
    }
  }
}

const syncAll = async () => {
  const loading = ElLoading.service({
    lock: true,
    text: '全期間データ同期中...',
    background: 'rgba(0, 0, 0, 0.7)',
  })

  try {
    await ElMessageBox.confirm(
      'すべての過去データを補完しますか？\n(確定本数>0の注文を在庫流水表に同期します)',
      '確認',
      {
        confirmButtonText: '実行',
        cancelButtonText: 'キャンセル',
        type: 'warning',
      },
    )

    const res = await syncShippingLog('all')

    // 详细信息通知
    if (res.data) {
      const { inserted, skipped, errors, totalRecords } = res.data
      const resultMessage =
        res.data.message ||
        `${inserted}件の注文を同期しました（${skipped}件スキップ、${errors}件エラー）`

      // 弹出一个带有详细信息的通知
      ElNotification({
        title: '同期完了',
        message: `総計: ${totalRecords}件\n同期: ${inserted}件\nスキップ: ${skipped}件\nエラー: ${errors}件`,
        type: 'success',
        duration: 10000,
        position: 'bottom-right',
      })

      // 同时显示一个简短的消息
      ElMessage({
        message: resultMessage,
        type: 'success',
        duration: 5000,
      })
    } else {
      ElMessage({
        message: '全期間の確定本数>0の注文を在庫流水表に同期しました',
        type: 'success',
        duration: 5000,
      })
    }
  } catch (err: unknown) {
    if (err !== 'cancel') {
      const errorMessage = err instanceof Error ? err.message : '同期に失敗しました'
      console.error('同期エラー:', errorMessage)
      ElMessage.error(errorMessage)
    }
  } finally {
    loading.close()
  }
}

// ✏️ 単品編集弹窗控制
const editDialogVisible = ref(false)
const currentOrder = ref<OrderDaily | null>(null)

const handleEdit = (row: OrderDaily) => {
  currentOrder.value = { ...row }
  editDialogVisible.value = true
}

// 处理编辑保存后的刷新
const handleEditSaved = async () => {
  await refreshData()
}

// 📋 まとめ編集控制（保留，尚未启用）
const batchDialogVisible = ref(false)
const selectedMonthlyOrderId = ref('')

const handleBatchEditSaved = async () => {
  batchDialogVisible.value = false
  await refreshData()
}

const batchUpdateDate = ref<string>('') // 対象日
const batchUpdateStatus = ref<string>('') // 要更新的状态

// 一括出荷済更新処理
const handleBatchStatusUpdate = async () => {
  if (!batchUpdateDate.value || !batchUpdateStatus.value) {
    ElMessage.warning('対象日と状態を選択してください')
    return
  }

  try {
    const result = await updateOrderDailyStatus({
      date: batchUpdateDate.value,
      status: batchUpdateStatus.value,
    })

    ElMessage.success(`${result.updated} 件の状態を「${batchUpdateStatus.value}」に更新しました`)
    await refreshData()
  } catch {
    ElMessage.error('状態の更新に失敗しました')
  }
}

//只是日期索引
const searchSpecificDate = ref<string>('')

const handleSearchByDate = async () => {
  if (!searchSpecificDate.value) {
    ElMessage.warning('検索対象の日付を選択してください')
    return
  }

  searchLoading.value = true
  loading.value = true
  try {
    const result = await fetchDailyOrdersByDate({ date: searchSpecificDate.value })

    orderList.value = Array.isArray(result) ? result : []
    pagination.value.page = 1
    pagination.value.total = result.length
  } catch (error) {
    console.error('指定日検索に失敗しました', error)
    ElMessage.error('検索に失敗しました')
    orderList.value = []
    pagination.value.total = 0

    // 错误时总计清零
    allStats.value.totalConfirmedBoxes = 0
    allStats.value.totalConfirmedUnits = 0
  } finally {
    searchLoading.value = false
    loading.value = false
  }
}

// 📥 批量导入
const batchImportDialogVisible = ref(false)
const showBatchImportDialog = () => {
  if (!filters.value.destination_cd) {
    ElMessage.warning('先に納入先を選択してください')
    return
  }
  batchImportDialogVisible.value = true
}

// 🔁 初始化加载
onMounted(async () => {
  try {
    await Promise.all([refreshData(), fetchDestinationList()])
  } finally {
    // 页面加载完成后隐藏加载遮罩
    setTimeout(() => {
      pageLoading.value = false
    }, 1000)
  }
})

const getProductTypeTagType = (type: string) => {
  switch (type) {
    case '量産品':
      return 'success' // 绿色
    case '試作品':
      return 'warning' // 橙色
    case '補給品':
      return 'info' // 蓝色
    case '代替品':
      return 'danger' // 红色
    case '別注品':
      return 'warning' // 橙色
    case 'サンプル品':
      return 'danger' // 红色
    case '返却品':
      return 'danger' // 红色
    case 'その他':
      return 'info' // 灰色（用info代替default）
    default:
      return 'info' // 默认也用info
  }
}

const addDialogVisible = ref(false)
const showAddDialog = () => {
  addDialogVisible.value = true
}

const handleDelete = async (row: OrderDaily) => {
  try {
    await ElMessageBox.confirm('本当に削除しますか？', '確認', { type: 'warning' })
    await deleteDailyOrder(row.id)
    ElMessage.success('削除しました')
    await refreshData() // 使用refreshData替代fetchList
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('削除に失敗しました')
  }
}

// 卡片统计用computed
const totalConfirmedBoxes = computed(() => allStats.value.totalConfirmedBoxes)
const totalConfirmedUnits = computed(() => allStats.value.totalConfirmedUnits)
const totalForecastUnits = computed(() => allStats.value.totalForecastUnits)
const shippedOrdersCount = computed(() => allStats.value.shipped)
const unshippedOrdersCount = computed(() => allStats.value.unshipped)
const confirmedOrdersCount = computed(() => allStats.value.confirmed)
const unconfirmedOrdersCount = computed(() => allStats.value.unconfirmed)

// 新增确认方法
const handleConfirm = async (row: OrderDaily) => {
  try {
    await ElMessageBox.confirm('この注文を確認しますか？', '確認', { type: 'warning' })
    await confirmOrder({ id: row.id })
    ElMessage.success('注文を確認しました')
    await refreshData()
  } catch (e: any) {
    if (e === 'cancel') return // 用户取消操作

    // 特定的错误处理
    if (e.response && e.response.status === 403) {
      // Token错误已在confirmOrder中处理，这里不需要重复处理
      console.error('認証エラー:', e.response.data?.message || '認証に失敗しました')
    } else {
      console.error('確認失敗', e)
      ElMessage.error('確認に失敗しました。もう一度お試しください')
    }
  }
}

// 批量确认相关变量
const batchConfirmDialogVisible = ref(false)
const batchConfirmDate = ref('')
const batchConfirmDestination = ref('')
const batchConfirmOrderList = ref<OrderDaily[]>([])
const batchConfirmSelected = ref<OrderDaily[]>([])
const batchConfirmLoading = ref(false)
const batchConfirmSearched = ref(false)
const batchConfirmSubmitting = ref(false)
const batchConfirmTableRef = ref<any>(null) // 添加表格引用

// 获取批量确认订单列表
const fetchBatchConfirmOrders = async () => {
  if (!batchConfirmDate.value || !batchConfirmDestination.value) {
    ElMessage.warning('日付と納入先を選択してください')
    return
  }

  batchConfirmLoading.value = true
  batchConfirmSearched.value = true
  batchConfirmSelected.value = [] // 重置选择

  try {
    const dateParts = batchConfirmDate.value.split('-')
    const year = Number(dateParts[0])
    const month = Number(dateParts[1])
    const day = Number(dateParts[2])

    const params: FetchDailyOrdersParams = {
      year,
      month,
      day,
      destination_cd: batchConfirmDestination.value,
      page: 1,
      pageSize: 1000, // 假设不会超过1000条
    }

    const res = await fetchDailyOrders(params)

    // 分别处理两种可能的响应结构
    let orderList: OrderDaily[] = []
    if (res && Array.isArray(res)) {
      orderList = res
    } else if (res && typeof res === 'object') {
      if (res.data && Array.isArray(res.data.list)) {
        orderList = res.data.list
      } else if (Array.isArray(res.list)) {
        orderList = res.list
      } else if (res.data && Array.isArray(res.data)) {
        orderList = res.data
      }
    }

    // 过滤掉已确认的订单
    batchConfirmOrderList.value = orderList.filter((order) => !order.confirmed)

    if (batchConfirmOrderList.value.length === 0) {
      ElMessage.info('確認が必要な注文はありません')
    } else {
      ElMessage.success(`${batchConfirmOrderList.value.length} 件の未確認注文が見つかりました`)
    }
  } catch (error) {
    console.error('注文検索失敗', error)
    ElMessage.error('注文の検索に失敗しました')
    batchConfirmOrderList.value = []
  } finally {
    batchConfirmLoading.value = false
  }
}

// 全选/取消全选
const selectAllBatchConfirmOrders = () => {
  if (batchConfirmTableRef.value) {
    // 设置所有行为选中状态
    batchConfirmOrderList.value.forEach((row) => {
      batchConfirmTableRef.value.toggleRowSelection(row, true)
    })
    // 更新选中数组
    batchConfirmSelected.value = [...batchConfirmOrderList.value]
  } else {
    batchConfirmSelected.value = [...batchConfirmOrderList.value]
  }
}

const unselectAllBatchConfirmOrders = () => {
  if (batchConfirmTableRef.value) {
    // 清除所有选择
    batchConfirmTableRef.value.clearSelection()
  }
  batchConfirmSelected.value = []
}

// 执行批量确认
const handleBatchConfirm = async () => {
  if (batchConfirmSelected.value.length === 0) {
    ElMessage.warning('注文を選択してください')
    return
  }

  try {
    await ElMessageBox.confirm(
      `選択した ${batchConfirmSelected.value.length} 件の注文を一括確認しますか？`,
      '一括確認',
      { type: 'warning' },
    )

    batchConfirmSubmitting.value = true

    // 提取ID列表
    const ids = batchConfirmSelected.value.map((order) => order.id)

    await confirmOrder({ ids })

    ElMessage.success(`${ids.length} 件の注文を確認しました`)
    batchConfirmDialogVisible.value = false

    // 刷新主列表和总计
    await refreshData()
  } catch (error: any) {
    if (error === 'cancel') return

    // 特定的错误处理已在confirmOrder中进行，这里只需处理其他错误
    if (!(error.response && error.response.status === 403)) {
      console.error('一括確認失敗', error)
      ElMessage.error('一括確認に失敗しました。もう一度お試しください')
    }
  } finally {
    batchConfirmSubmitting.value = false
  }
}

// 打开批量确认弹窗（使用日本时区）
const openBatchConfirmDialog = () => {
  // 重置状态
  batchConfirmDate.value = getJapanDateString() // 默认今天（日本时区）
  batchConfirmDestination.value = filters.value.destination_cd || '' // 使用当前筛选的納入先
  batchConfirmOrderList.value = []
  batchConfirmSelected.value = []
  batchConfirmSearched.value = false
  batchConfirmDialogVisible.value = true

  // 如果已经选择了納入先，自动查询
  if (batchConfirmDestination.value) {
    fetchBatchConfirmOrders()
  }
}

// 监听弹窗关闭事件，重置选择状态
watch(
  () => batchConfirmDialogVisible.value,
  (newVal) => {
    if (!newVal) {
      // 弹窗关闭时
      batchConfirmSelected.value = []
      if (batchConfirmTableRef.value) {
        batchConfirmTableRef.value.clearSelection()
      }
    }
  },
)

// 监听筛选条件变化，自动更新总计数据
// 已移除对筛选条件变化的监听，因为现在获取数据时会自动计算总计

// 处理新增保存后的刷新
const handleAddSaved = async () => {
  await refreshData()
}

// 处理年月变化，重新筛选数据
const handleYearMonthChange = () => {
  // 如果月份变化了，需要检查当前选择的日是否超出了该月的最大天数
  if (filters.value.day > daysInMonth.value) {
    filters.value.day = daysInMonth.value
  }
  refreshData()
}

// 处理日期变化，特殊处理清除日期的情况
const handleDayChange = () => {
  refreshData()
}

// 📌 前の日・次の日处理
const handlePrevDay = () => {
  if (!filters.value.day) {
    // 如果没有选择日期，默认选择当月最后一天
    filters.value.day = daysInMonth.value
    refreshData()
    return
  }

  if (filters.value.day === 1) {
    // 如果是1号，需要切换到上个月的最后一天
    if (filters.value.month === 1) {
      filters.value.year--
      filters.value.month = 12
    } else {
      filters.value.month--
    }
    // 计算上个月的最后一天
    filters.value.day = new Date(filters.value.year, filters.value.month, 0).getDate()
  } else {
    filters.value.day--
  }
  refreshData()
}

const handleNextDay = () => {
  if (!filters.value.day) {
    // 如果没有选择日期，默认选择当月1号
    filters.value.day = 1
    refreshData()
    return
  }

  // 获取当前月的最后一天
  const lastDayOfMonth = new Date(filters.value.year, filters.value.month, 0).getDate()

  if (filters.value.day === lastDayOfMonth) {
    // 如果是月末，需要切换到下个月的1号
    if (filters.value.month === 12) {
      filters.value.year++
      filters.value.month = 1
    } else {
      filters.value.month++
    }
    filters.value.day = 1
  } else {
    filters.value.day++
  }
  refreshData()
}

// 设置为当天（使用日本时区）
const handleToday = () => {
  const japanDate = getJapanDate()
  filters.value.year = japanDate.getFullYear()
  filters.value.month = japanDate.getMonth() + 1
  filters.value.day = japanDate.getDate()
  refreshData()
}

// 打印功能 - 按納入先分组，通过HTML渲染
const handlePrint = () => {
  if (orderList.value.length === 0) {
    ElMessage.warning('印刷するデータがありません')
    return
  }

  // 创建一个打印专用的HTML页面
  const printWindow = window.open('', '_blank')
  if (!printWindow) {
    ElMessage.error(
      'ポップアップがブロックされました。印刷するには、ポップアップを許可してください。',
    )
    return
  }

  // 按納入先分组数据，只包含确定箱数大于0的订单
  const groupedByDestination: Record<string, { name: string; orders: OrderDaily[] }> = {}
  orderList.value
    .filter((order) => order.confirmed_boxes > 0)
    .forEach((order) => {
      const destKey = order.destination_cd
      if (!groupedByDestination[destKey]) {
        groupedByDestination[destKey] = {
          name: order.destination_name,
          orders: [],
        }
      }
      groupedByDestination[destKey].orders.push(order)
    })

  // 创建HTML内容（使用日本时区）
  const title = `日別受注一覧表 ${filters.value.year}/${filters.value.month}/${filters.value.day || '全月'}`
  const japanDate = getJapanDate()
  const printDate = japanDate.toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' })

  // 打印样式
  const style = `
    <style>
      body {
        font-family: "Hiragino Sans", "Hiragino Kaku Gothic ProN", "MS Gothic", Meiryo, sans-serif;
        padding: 20px;
      }
      .page-header { text-align: center; margin-bottom: 20px; }
      h1 { font-size: 24px; margin-bottom: 5px; }
      .print-date { font-size: 14px; color: #666; }
      .destination-header {
        font-size: 18px;
        margin: 20px 0 10px 0;
        padding: 5px;
        background-color: #f5f5f5;
        border-left: 5px solid #409EFF;
      }
      table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 30px;
        font-size: 12px;
      }
      th {
        background-color: #409EFF;
        color: white;
        padding: 8px;
        text-align: left;
        font-weight: normal;
      }
      td { padding: 8px; border-bottom: 1px solid #ddd; }
      tr:nth-child(even) { background-color: #f9f9f9; }
      .no-data { text-align: center; color: #999; padding: 20px; }

      @media print {
        @page { margin: 0.5cm; }
        .page-break { page-break-after: always; }
        body { margin: 0; padding: 0.5cm; }
        table { page-break-inside: avoid; }
      }
      .print-btn {
        display: block;
        margin: 20px auto;
        padding: 10px 20px;
        background-color: #409EFF;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 16px;
      }
      .print-btn:hover {
        background-color: #337ecc;
      }
    </style>
  `

  // 页面内容
  let content = ''
  content += `
    <div class="page-header">
      <h1>${title}</h1>
      <div class="print-date">印刷日時: ${printDate}</div>
    </div>
  `

  // 为每个纳入先创建表格
  Object.entries(groupedByDestination).forEach(
    ([destCd, data]: [string, { name: string; orders: OrderDaily[] }], index) => {
      if (index > 0) {
        content += '<div class="page-break"></div>'
      }

      content += `
      <div class="destination-header">納入先: ${destCd} - ${data.name}</div>
      <table>
        <thead>
          <tr>
            <th>積込日</th>
            <th>曜日</th>
            <th>納入日</th>
            <th>製品タイプ</th>
            <th>製品名</th>
            <th>入数</th>
            <th>確定箱数</th>
            <th>確定本数</th>
          </tr>
        </thead>
        <tbody>
    `

      if (data.orders.length === 0) {
        content += '<tr><td colspan="8" class="no-data">データがありません</td></tr>'
      } else {
        data.orders.forEach((order: OrderDaily) => {
          content += `
          <tr>
            <td>${order.year}/${order.month}/${order.day}</td>
            <td>${order.weekday || ''}</td>
            <td>${formatDate(order.delivery_date)}</td>
            <td>${order.product_type || ''}</td>
            <td>${order.product_name}</td>
            <td>${order.unit_per_box || ''}</td>
            <td>${order.confirmed_boxes}</td>
            <td>${order.confirmed_units > 0 ? order.confirmed_units : ''}</td>
          </tr>
        `
        })
      }

      content += `
        </tbody>
      </table>
    `
    },
  )

  // 添加打印按钮
  content += `
    <button class="print-btn" onclick="window.print()">印刷する</button>
  `

  // 组合完整HTML
  const html = `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>${title}</title>
      ${style}
    </head>
    <body>
      ${content}
    </body>
    </html>
  `

  // 写入HTML到新窗口并打印
  printWindow.document.open()
  printWindow.document.write(html)
  printWindow.document.close()
}

// 处理每页条数变化
const handleSizeChange = (val: number) => {
  pagination.value.pageSize = val
  refreshData()
}

// 处理页码变化
const handleCurrentChange = (val: number) => {
  pagination.value.page = val
  refreshData()
}
</script>

<style scoped>
.order-daily-page {
  padding: 12px;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow-x: hidden;
}

/* 动态背景 */
.dynamic-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -1;
  overflow: hidden;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  background: linear-gradient(45deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
  animation: float 20s ease-in-out infinite;
}

.orb-1 {
  width: 300px;
  height: 300px;
  top: -150px;
  right: -150px;
  animation-delay: -5s;
}

.orb-2 {
  width: 200px;
  height: 200px;
  bottom: -100px;
  left: -100px;
  animation-delay: -10s;
}

.orb-3 {
  width: 250px;
  height: 250px;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation-delay: -15s;
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0px) rotate(0deg);
  }

  33% {
    transform: translateY(-30px) rotate(120deg);
  }

  66% {
    transform: translateY(30px) rotate(240deg);
  }
}

/* 页面加载遮罩 */
.page-loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.95), rgba(118, 75, 162, 0.95));
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
  backdrop-filter: blur(20px);
  animation: fadeIn 0.3s ease-out;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  animation: slideUp 0.5s ease-out;
}

.custom-loader {
  position: relative;
  width: 80px;
  height: 80px;
}

.loader-ring {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: 3px solid transparent;
  border-radius: 50%;
  animation: spin 2s linear infinite;
}

.loader-ring:nth-child(1) {
  border-top: 3px solid #409eff;
  animation-delay: 0s;
}

.loader-ring:nth-child(2) {
  border-right: 3px solid #67c23a;
  animation-delay: -0.5s;
  animation-duration: 1.5s;
}

.loader-ring:nth-child(3) {
  border-bottom: 3px solid #e6a23c;
  animation-delay: -1s;
  animation-duration: 1s;
}

.loading-text {
  color: white;
  font-size: 18px;
  font-weight: 600;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  animation: textPulse 2s ease-in-out infinite;
}

.loading-dots {
  display: flex;
  gap: 8px;
}

.dot {
  width: 8px;
  height: 8px;
  background: white;
  border-radius: 50%;
  animation: dotBounce 1.4s ease-in-out infinite;
}

.dot:nth-child(1) {
  animation-delay: -0.32s;
}

.dot:nth-child(2) {
  animation-delay: -0.16s;
}

.dot:nth-child(3) {
  animation-delay: 0s;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }

  to {
    opacity: 1;
  }
}

@keyframes slideUp {
  from {
    transform: translateY(30px);
    opacity: 0;
  }

  to {
    transform: translateY(0);
    opacity: 1;
  }
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

@keyframes textPulse {
  0%,
  100% {
    opacity: 1;
  }

  50% {
    opacity: 0.7;
  }
}

@keyframes dotBounce {
  0%,
  80%,
  100% {
    transform: scale(0.8);
    opacity: 0.5;
  }

  40% {
    transform: scale(1.2);
    opacity: 1;
  }
}

/* 现代化页面头部 */
.modern-header {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
  backdrop-filter: blur(20px);
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  position: relative;
  overflow: hidden;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  z-index: 2;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, #409eff, #67c23a);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.25);
  flex-shrink: 0;
}

.header-text {
  flex: 1;
}

.header-title {
  font-size: 24px;
  font-weight: 700;
  color: #2c3e50;
  margin: 0 0 4px 0;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
  line-height: 1.2;
}

.header-subtitle {
  font-size: 14px;
  color: #2c3e50;
  font-weight: 600;
  background: linear-gradient(135deg, #409eff, #67c23a);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.header-badge {
  background: linear-gradient(135deg, #e74c3c, #f39c12);
  color: white;
  padding: 6px 12px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 3px;
  box-shadow: 0 2px 8px rgba(231, 76, 60, 0.25);
  animation: pulse 2s ease-in-out infinite;
  flex-shrink: 0;
}

.badge-count {
  font-size: 16px;
  font-weight: 700;
}

.badge-label {
  font-size: 12px;
  opacity: 0.9;
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
  }

  50% {
    transform: scale(1.05);
  }
}

.floating-circles {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
}

.circle {
  position: absolute;
  border-radius: 50%;
  background: linear-gradient(45deg, rgba(64, 158, 255, 0.2), rgba(103, 194, 58, 0.2));
  animation: float 3s ease-in-out infinite;
}

.circle-1 {
  width: 20px;
  height: 20px;
  top: -10px;
  right: 0;
}

.circle-2 {
  width: 15px;
  height: 15px;
  top: 10px;
  right: 25px;
  animation-delay: -1s;
}

.circle-3 {
  width: 12px;
  height: 12px;
  top: -5px;
  right: 45px;
  animation-delay: -2s;
}

/* 现代化卡片基础样式 */
.modern-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

.modern-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

.modern-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
}

/* 统计卡片样式 */
.summary-cards-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
  margin-bottom: 12px;
}

.summary-card-item {
  padding: 14px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 80px;
  position: relative;
}

.card-icon {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.boxes .card-icon {
  background: linear-gradient(135deg, #409eff, #67c23a);
}

.units .card-icon {
  background: linear-gradient(135deg, #67c23a, #85ce61);
}

.forecast .card-icon {
  background: linear-gradient(135deg, #3a8de0, #6fb3ff);
}

.status .card-icon {
  background: linear-gradient(135deg, #e6a23c, #f7ba2a);
}

.confirm .card-icon {
  background: linear-gradient(135deg, #9254de, #b37feb);
}

.card-content {
  flex: 1;
}

.summary-title {
  font-size: 12px;
  color: #8492a6;
  margin-bottom: 6px;
  font-weight: 500;
  line-height: 1.2;
}

.summary-value {
  font-size: 22px;
  font-weight: 700;
  color: #2c3e50;
  line-height: 1.1;
}

.animated-count {
  animation: countUp 0.8s ease-out;
}

@keyframes countUp {
  from {
    transform: scale(0.8);
    opacity: 0;
  }

  to {
    transform: scale(1);
    opacity: 1;
  }
}

.summary-value-split {
  display: flex;
  flex-direction: row;
  gap: 16px;
  align-items: center;
  justify-content: flex-start;
  flex-wrap: wrap;
}

.split-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.split-label {
  font-size: 11px;
  color: #8492a6;
  font-weight: 500;
}

.split-value {
  font-size: 16px;
  font-weight: 700;
  color: #2c3e50;
}

.card-decoration {
  position: absolute;
  top: -20px;
  right: -20px;
  width: 40px;
  height: 40px;
  background: linear-gradient(45deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
  border-radius: 50%;
}

/* 操作按钮区域 */
.action-buttons-section {
  padding: 14px 16px;
  margin-bottom: 12px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 600;
  color: #2c3e50;
}

.action-buttons-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 10px;
}

/* 现代化按钮样式 */
.modern-btn {
  position: relative;
  overflow: hidden;
  border-radius: 8px;
  font-weight: 600;
  transition: all 0.2s ease;
  border: none;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  font-size: 13px;
}

.modern-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.primary-btn {
  background: linear-gradient(135deg, #409eff, #67c23a);
  color: white;
}

.info-btn {
  background: linear-gradient(135deg, #909399, #b1b3b8);
  color: white;
}

.success-btn {
  background: linear-gradient(135deg, #67c23a, #85ce61);
  color: white;
}

.warning-btn {
  background: linear-gradient(135deg, #e6a23c, #f7ba2a);
  color: white;
}

.btn-shine {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.5s;
}

.modern-btn:hover .btn-shine {
  left: 100%;
}

/* 筛选区域样式 */
.filter-section {
  padding: 14px 16px;
  margin-bottom: 12px;
}

.modern-filter-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: end;
}

.main-filters {
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.modern-form-item {
  margin-bottom: 0;
}

.modern-select,
.modern-input,
.modern-date-picker {
  border-radius: 8px;
  border: 1px solid #dcdfe6;
  transition: all 0.3s ease;
}

.modern-select:hover,
.modern-input:hover,
.modern-date-picker:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.destination-select {
  width: 200px;
}

.date-filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.date-filter-group .modern-select:nth-child(1) {
  width: 100px;
  /* 年选择器 */
}

.date-filter-group .modern-select:nth-child(2) {
  width: 80px;
  /* 月选择器 */
}

.date-filter-group .modern-select:nth-child(3) {
  width: 80px;
  /* 日选择器 */
}

.date-nav-buttons {
  display: flex;
  gap: 4px;
  margin-left: 8px;
}

.nav-btn {
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 12px;
  border: 1px solid #dcdfe6;
  background: white;
  transition: all 0.3s ease;
}

.nav-btn:hover {
  border-color: #409eff;
  color: #409eff;
}

.today-btn {
  background: #409eff;
  color: white;
  border-color: #409eff;
}

.batch-controls,
.specific-date-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.utility-buttons {
  display: flex;
  gap: 12px;
  margin-left: auto;
}

/* 表格区域样式 */
.table-section {
  padding: 14px 16px;
  margin-bottom: 12px;
}

.table-header {
  margin-bottom: 12px;
}

.table-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 15px;
  font-weight: 600;
  color: #2c3e50;
}

.table-count-badge {
  background: linear-gradient(135deg, #409eff, #67c23a);
  color: white;
  padding: 3px 10px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  margin-left: 8px;
  animation: pulse 2s ease-in-out infinite;
}

.table-wrapper {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.modern-table {
  border-radius: 8px;
  overflow: hidden;
}

.table-cell-content {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
}

.month-cell,
.day-cell,
.number-cell {
  font-weight: 600;
  color: #2c3e50;
  font-size: 13px;
}

.highlight-number {
  color: #409eff;
  font-weight: 700;
  font-size: 13px;
}

.animated-tag {
  animation: tagSlideIn 0.3s ease-out;
  display: flex;
  align-items: center;
  gap: 4px;
}

@keyframes tagSlideIn {
  from {
    transform: translateX(-10px);
    opacity: 0;
  }

  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.status-tag {
  animation: statusPulse 2s ease-in-out infinite;
}

@keyframes statusPulse {
  0%,
  100% {
    opacity: 1;
  }

  50% {
    opacity: 0.8;
  }
}

.action-buttons {
  display: flex;
  gap: 6px;
  justify-content: center;
  flex-wrap: wrap;
}

.action-btn {
  border-radius: 6px;
  padding: 5px 10px;
  border: none;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 12px;
}

.action-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
}

.edit-btn {
  background: linear-gradient(135deg, #409eff, #67c23a);
}

.delete-btn {
  background: linear-gradient(135deg, #f56c6c, #ff7875);
}

.confirm-btn {
  background: linear-gradient(135deg, #67c23a, #85ce61);
}

/* 分页样式 */
.pagination-container {
  margin-top: 12px;
  padding: 12px;
  display: flex;
  justify-content: center;
  background: rgba(248, 249, 250, 0.6);
  border-radius: 8px;
  backdrop-filter: blur(10px);
}

.modern-pagination {
  border-radius: 6px;
  overflow: hidden;
}

.data-summary {
  margin-top: 12px;
  text-align: center;
  color: #8492a6;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px;
  background: rgba(248, 249, 250, 0.4);
  border-radius: 6px;
}

/* 对话框样式 */
.modern-dialog {
  border-radius: 10px;
  overflow: hidden;
}

.batch-confirm-header {
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.1), rgba(103, 194, 58, 0.1));
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 12px;
}

.batch-confirm-stats {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.05), rgba(103, 194, 58, 0.05));
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 12px;
}

.stats-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stats-label {
  color: #8492a6;
  font-size: 14px;
}

.stats-value {
  font-weight: 700;
  color: #2c3e50;
  font-size: 16px;
}

.stats-value.highlight {
  color: #409eff;
}

.stats-unit {
  color: #8492a6;
  font-size: 14px;
}

.stats-buttons {
  display: flex;
  gap: 8px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .action-buttons-grid {
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  }

  .summary-cards-row {
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  }
}

@media (max-width: 992px) {
  .header-content {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }

  .filter-row {
    flex-direction: column;
    align-items: stretch;
  }

  .utility-buttons {
    margin-left: 0;
    justify-content: center;
  }
}

@media (max-width: 768px) {
  .order-daily-page {
    padding: 10px;
  }

  .modern-header {
    padding: 12px 16px;
  }

  .header-title {
    font-size: 20px;
  }

  .summary-cards-row {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .action-buttons-grid {
    grid-template-columns: 1fr;
    gap: 8px;
  }

  .date-filter-group {
    flex-wrap: wrap;
  }

  .date-filter-group .modern-select:nth-child(1) {
    width: 90px;
  }

  .date-filter-group .modern-select:nth-child(2) {
    width: 70px;
  }

  .date-filter-group .modern-select:nth-child(3) {
    width: 70px;
  }

  .date-nav-buttons {
    flex-wrap: wrap;
  }
}

@media (max-width: 480px) {
  .modern-btn {
    padding: 8px 12px;
    font-size: 12px;
  }

  .table-section,
  .filter-section,
  .action-buttons-section {
    padding: 12px;
  }

  .batch-controls,
  .specific-date-group {
    flex-direction: column;
    align-items: stretch;
  }

  .date-filter-group .modern-select:nth-child(1) {
    width: 85px;
  }

  .date-filter-group .modern-select:nth-child(2) {
    width: 65px;
  }

  .date-filter-group .modern-select:nth-child(3) {
    width: 65px;
  }
}

/* 自定义滚动条 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #409eff, #67c23a);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #337ecc, #529b2e);
}

/* 通知样式美化 */
:deep(.el-notification) {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

:deep(.el-notification.success) {
  background: linear-gradient(135deg, rgba(103, 194, 58, 0.1), rgba(133, 206, 97, 0.1));
}

:deep(.el-notification.warning) {
  background: linear-gradient(135deg, rgba(230, 162, 60, 0.1), rgba(247, 186, 42, 0.1));
}

:deep(.el-notification.error) {
  background: linear-gradient(135deg, rgba(245, 108, 108, 0.1), rgba(255, 120, 117, 0.1));
}

/* 表格行动画 */
:deep(.el-table__row) {
  animation: tableRowSlideIn 0.3s ease-out;
}

@keyframes tableRowSlideIn {
  from {
    transform: translateX(-20px);
    opacity: 0;
  }

  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* 表格紧凑样式 */
:deep(.el-table) {
  font-size: 13px;
}

:deep(.el-table th) {
  padding: 8px 0;
  font-size: 12px;
  font-weight: 600;
}

:deep(.el-table td) {
  padding: 8px 0;
}

:deep(.el-table .cell) {
  padding: 0 8px;
  line-height: 1.4;
}

/* 旧样式保留 */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: var(--el-fill-color-lighter);
  padding: 3px 5px;
  border-radius: 12px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}

.title {
  font-size: 24px;
  font-weight: bold;
}

.current-date {
  font-size: 18px;
  color: #409eff;
  margin-left: 10px;
  font-weight: normal;
}

.header-buttons {
  display: flex;
  gap: 5px;
}

.filter-form {
  margin: 6px 0 15px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px 10px;
  background-color: #f8fafc;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  border: 1px solid #e6e8eb;
}

.filter-section {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.main-filters {
  padding-bottom: 10px;
  border-bottom: 1px dashed #e0e6ed;
  justify-content: flex-start;
}

.secondary-filters {
  padding-top: 5px;
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
}

.date-filter-group {
  display: flex;
  align-items: center;
  gap: 5px;
}

.date-nav-buttons {
  display: flex;
  gap: 3px;
  margin-left: 3px;
}

.specific-date-group {
  display: flex;
  align-items: center;
  gap: 5px;
}

.search-btn {
  min-width: 55px;
  padding: 0 8px;
}

.batch-update-section,
.specific-date-section {
  display: flex;
  align-items: center;
}

.batch-title-item,
.destination-item,
.product-search-item,
.specific-date-item,
.date-filter-item {
  margin-bottom: 0;
  margin-right: 0;
}

.batch-controls {
  display: flex;
  gap: 8px;
  align-items: center;
}

.update-btn {
  min-width: 55px;
  height: 30px;
  padding: 0 8px;
  margin-right: 60px;
}

.reset-filter-btn,
.print-btn {
  margin-left: 10px;
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 0 10px;
}

.print-btn {
  background-color: #42b983;
  border-color: #42b983;
  color: white;
}

.print-btn:hover {
  background-color: #3da776;
  border-color: #3da776;
}

.table-card {
  background-color: #fff;
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  padding: 10px;
  display: flex;
  justify-content: center;
  background-color: #fff;
  border-top: 1px solid #f0f0f0;
}

:deep(.el-pagination) {
  justify-content: center;
  padding: 0;
}

:deep(.el-pagination .el-select .el-input) {
  width: 100px;
}

:deep(.el-pagination .el-pagination__total) {
  margin-right: 16px;
}

:deep(.el-pagination .el-pagination__sizes) {
  margin-right: 16px;
}

.action-buttons {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.el-table .cell {
  font-size: 14px;
}

.el-table .el-table__row:hover {
  background-color: #f3faff;
}

.shipping-sync-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 20px;
}

.summary-cards-row {
  display: flex;
  gap: 18px;
  margin-bottom: 20px;
}

.summary-card-item {
  flex: 1;
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
  text-align: center;
  padding: 18px 0;
  height: 100px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.summary-card-item .summary-title {
  font-size: 15px;
  color: #888;
  margin-bottom: 6px;
}

.summary-card-item .summary-value {
  font-size: 26px;
  font-weight: bold;
  letter-spacing: 1px;
}

.summary-card-item.boxes .summary-value {
  color: #409eff;
}

.summary-card-item.units .summary-value {
  color: #67c23a;
}

.summary-card-item.forecast .summary-value {
  color: #1f85ff;
}

.summary-card-item.status .summary-value-split,
.summary-card-item.confirm .summary-value-split {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.split-item {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
}

.split-label {
  color: #888;
  font-size: 14px;
  width: 60px;
  text-align: right;
}

.split-value {
  font-size: 20px;
  font-weight: bold;
  color: #2c3e50;
}

.summary-card-item.status .split-value {
  color: #e6a23c;
}

.summary-card-item.confirm .split-value {
  color: #9254de;
}

.batch-confirm-header {
  margin-bottom: 16px;
  background-color: #f8f9fa;
  padding: 12px;
  border-radius: 8px;
}

.batch-confirm-form {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.batch-confirm-stats {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #ecf5ff;
  padding: 10px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.highlight {
  font-weight: bold;
  color: #409eff;
  margin: 0 4px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* 确认状态标签颜色 */
.el-tag--success {
  background-color: #f0f9eb;
}

.el-tag--info {
  background-color: #f4f4f5;
}

/* 空状态美化 */
:deep(.el-empty__description) {
  margin-top: 10px;
  color: #909399;
}
</style>
