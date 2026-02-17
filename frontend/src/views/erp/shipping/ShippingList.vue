<template>
  <div
    class="shipping-list-container"
    v-loading="pageLoading"
    element-loading-text="ページを読み込み中..."
    element-loading-background="rgba(255, 255, 255, 0.9)"
  >
    <!-- 页面头部 -->
    <div class="page-header" :class="{ 'page-loaded': !pageLoading }">
      <div class="header-content">
        <div class="title-section">
          <h2 class="title">
            <div class="title-icon">
              <el-icon>
                <Van />
              </el-icon>
            </div>
            <span class="title-text">{{ t('shipping.compositionTitle') }}</span>
          </h2>
        </div>
        <div class="header-decoration">
          <div class="decoration-circle circle-1"></div>
          <div class="decoration-circle circle-2"></div>
          <div class="decoration-circle circle-3"></div>
        </div>
      </div>
    </div>

    <!-- フィルター -->
    <el-card class="filter-card modern-card">
      <template #header>
      </template>
      <el-form :inline="true" :model="filters" class="filter-bar">
        <!-- 基本検索条件 -->
        <div class="compact-filter-row">
          <div class="filter-group date-group">
            <label class="filter-label">期間</label>
            <div class="date-range-container">
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                range-separator="〜"
                start-placeholder="開始日"
                end-placeholder="終了日"
                value-format="YYYY-MM-DD"
                :editable="false"
                @change="handleDateRangeChange"
                @focus="preventKeyboardOnFocus"
                class="modern-date-picker"
                style="width: 240px"
              />
              <div class="date-quick-buttons">
                <el-button @click="adjustDate(-1)" class="date-btn">
                  <el-icon>
                    <ArrowLeft />
                  </el-icon>
                </el-button>
                <el-button @click="setToday" class="date-btn today-btn"> 今日 </el-button>
                <el-button @click="adjustDate(1)" class="date-btn">
                  <el-icon>
                    <ArrowRight />
                  </el-icon>
                </el-button>
              </div>
            </div>
          </div>

          <div class="filter-group destination-group">
            <div class="group-controls">
              <el-select
                v-model="selectedGroupFilter"
                placeholder="グループ"
                clearable
                class="group-filter-dropdown"
                style="width: 120px"
                @change="handleGroupFilterChange"
                @focus="preventKeyboardOnFocus"
              >
                <el-option
                  v-for="(group, index) in availableGroups"
                  :key="group.id || index"
                  :label="group.groupName"
                  :value="index"
                >
                  <div class="group-option">
                    <span class="group-name">{{ group.groupName }}</span>
                    <span class="group-count">({{ group.destinations.length }})</span>
                  </div>
                </el-option>
              </el-select>
              <el-button @click="showGroupManager = true" class="group-manage-button">
                <el-icon>
                  <Setting />
                </el-icon>
                <span>グループ管理</span>
              </el-button>
            </div>
            <div class="destination-controls">
              <label class="filter-label filter-label-inline">納入先</label>

              <!-- 纳入先选择下拉框 -->
              <el-select
                v-model="singleDestination"
                placeholder="納入先を選択"
                clearable
                filterable
                class="destination-select-dropdown"
                style="width: 200px"
                @change="handleSingleDestinationChange"
                @focus="preventKeyboardOnFocus"
              >
                <el-option
                  v-for="dest in sortedDestinationOptions"
                  :key="dest.value"
                  :label="dest.label"
                  :value="dest.value"
                >
                  <div class="destination-option">
                    <span class="destination-code">{{ dest.value }}</span>
                    <span class="destination-name">{{ dest.name }}</span>
                  </div>
                </el-option>
              </el-select>

              <!-- 快捷按钮 -->
              <div class="destination-quick-buttons">
                <el-button
                  v-for="quick in destinationQuickButtons"
                  :key="quick.code"
                  @click="selectQuickDestination(quick.code)"
                  class="destination-quick-btn"
                  :class="{ active: singleDestination === quick.code }"
                  size="small"
                >
                  {{ quick.name }}
                </el-button>
              </div>
            </div>
          </div>

        </div>

        <!-- 活跃分组显示 -->
        <div v-if="activeGroups.length > 0" class="active-groups-display">
          <div class="groups-header">
            <span class="groups-title">
              <el-icon>
                <Collection />
              </el-icon>
              選択中のグループ
            </span>
            <el-button
              size="small"
              type="danger"
              link
              @click="clearAllGroups"
              class="clear-groups-btn"
            >
              全てクリア
            </el-button>
          </div>
          <div class="groups-list">
            <div v-for="(group, index) in activeGroups" :key="index" class="group-tag">
              <span class="group-name">{{ group.name }}</span>
              <span class="group-count">{{ group.destinations.length }}件</span>
              <el-button
                size="small"
                type="danger"
                circle
                @click="removeGroup(index)"
                class="remove-group-btn"
              >
                <el-icon>
                  <Close />
                </el-icon>
              </el-button>
            </div>
          </div>
        </div>
      </el-form>
    </el-card>

    <!-- 操作按钮行（筛选区域下方单独一行） -->
    <div class="action-buttons-row">
      <el-button type="primary" @click="openCreateDialog" class="action-button create-button">
        <el-icon>
          <Plus />
        </el-icon>
        出荷構成表作成
      </el-button>
      <el-button
        type="warning"
        @click="printSelected"
        :disabled="allSelectedIds.size === 0"
        class="action-button print-button"
      >
        <el-icon>
          <Printer />
        </el-icon>
        選択印刷
        <span class="button-badge" v-if="totalSelectedCount > 0">{{
          totalSelectedCount
        }}</span>
      </el-button>
      <el-button
        type="danger"
        @click="cancelSelected"
        :disabled="allSelectedIds.size === 0"
        :loading="actionLoading"
        class="action-button delete-button"
      >
        <el-icon>
          <Close />
        </el-icon>
        選択削除
        <span class="button-badge" v-if="totalSelectedCount > 0">{{
          totalSelectedCount
        }}</span>
      </el-button>
      <el-button
        type="info"
        @click="columnSelectVisible = true"
        class="action-button setting-button"
      >
        <el-icon>
          <Setting />
        </el-icon>
        列表示設定
      </el-button>
      <el-button
        type="success"
        @click="openExportConfirmDialog"
        :loading="exportLoading"
        class="action-button export-button"
      >
        <el-icon>
          <Download />
        </el-icon>
        ピッキング出力
      </el-button>
    </div>

    <!-- 一覧表 -->
    <el-card class="table-card modern-card">
      <template #header>
        <div class="table-header">
          <div class="table-title">
            <el-icon class="table-icon">
              <Document />
            </el-icon>
            <span>出荷リスト</span>
            <div class="count-badge" :class="{ 'animate-count': searchAnimating }">
              <el-icon class="count-icon">
                <Document />
              </el-icon>
              <span>{{ shippingList.length }}件</span>
            </div>
            <div v-if="totalSelectedCount > 0" class="selected-badge">
              <el-icon class="selected-icon">
                <Select />
              </el-icon>
              <span>{{ totalSelectedCount }}件選択中</span>
            </div>
          </div>
        </div>
      </template>

      <div class="table-wrapper">
        <el-table
          ref="tableRef"
          :data="displayedList"
          border
          highlight-current-row
          v-loading="loading"
          element-loading-text="データを読み込み中..."
          element-loading-background="rgba(255, 255, 255, 0.8)"
          class="modern-table"
          :style="{ width: '100%' }"
          :empty-text="emptyText"
          @row-click="handleRowClick"
          :row-class-name="tableRowClassName"
          @selection-change="handleSelectionChange"
          @select="handleSelectRow"
          @select-all="handleSelectAll"
          :key="tableKey"
        >
          <el-table-column type="selection" width="50" align="center" />
          <el-table-column
            label="出荷番号"
            prop="shipping_no"
            width="105"
            show-overflow-tooltip
            v-if="columnVisible.shipping_no"
            key="shipping_no"
          >
            <template #default="{ row }">
              <div class="shipping-no-cell">
                <el-tag type="info" effect="light" size="small">
                  {{ row.shipping_no }}
                </el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column
            label="出荷日"
            prop="shipping_date"
            width="120"
            sortable
            v-if="columnVisible.shipping_date"
            key="shipping_date"
          >
            <template #default="{ row }">
              <div class="date-cell">
                <el-icon class="date-icon">
                  <Calendar />
                </el-icon>
                {{ formatDate(row.shipping_date) }}
              </div>
            </template>
          </el-table-column>
          <el-table-column
            label="納入日"
            prop="delivery_date"
            width="120"
            sortable
            v-if="columnVisible.delivery_date"
            key="delivery_date"
          >
            <template #default="{ row }">
              <div class="date-cell">
                <el-icon class="date-icon">
                  <Calendar />
                </el-icon>
                {{ formatDate(row.delivery_date) }}
              </div>
            </template>
          </el-table-column>
          <el-table-column
            label="納入先"
            prop="destination_name"
            min-width="120"
            show-overflow-tooltip
            v-if="columnVisible.destination_name"
            key="destination_name"
          >
            <template #default="{ row }">
              <el-tooltip
                :content="`${row.destination_cd} - ${row.destination_name}`"
                placement="top"
                :show-after="500"
                effect="light"
              >
                <div class="destination-cell">
                  <el-icon class="location-icon">
                    <Location />
                  </el-icon>
                  <span>{{ row.destination_name }}</span>
                </div>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column
            label="製品CD"
            prop="product_cd"
            width="80"
            show-overflow-tooltip
            v-if="columnVisible.product_cd"
            key="product_cd"
          >
            <template #default="{ row }">
              <el-tooltip
                :content="row.product_name"
                placement="top"
                :show-after="500"
                effect="light"
              >
                <el-tag type="primary" effect="plain" size="small">
                  {{ row.product_cd }}
                </el-tag>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column
            label="製品名"
            prop="product_name"
            min-width="120"
            show-overflow-tooltip
            v-if="columnVisible.product_name"
            key="product_name"
          >
            <template #default="{ row }">
              <div class="product-name-cell">
                <span>{{ row.product_name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column
            label="箱数"
            prop="confirmed_boxes"
            width="60"
            align="right"
            v-if="columnVisible.confirmed_boxes"
            key="confirmed_boxes"
          >
            <template #default="{ row }">
              <div class="number-cell">
                <span class="number-value">{{ (row.confirmed_boxes || 0).toLocaleString() }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column
            label="数量"
            prop="confirmed_units"
            width="90"
            align="right"
            v-if="columnVisible.confirmed_units"
            key="confirmed_units"
          >
            <template #default="{ row }">
              <div class="number-cell">
                <span class="number-value">{{ (row.confirmed_units || 0).toLocaleString() }}</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column
            label="箱タイプ"
            prop="box_type"
            width="90"
            v-if="columnVisible.box_type"
            key="box_type"
          >
            <template #default="{ row }">
              <el-tag size="small" :type="getBoxTypeTagType(row.box_type)" effect="dark">
                {{ row.box_type || '未設定' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="コード" width="120" v-if="columnVisible.code" key="code">
            <template #default="{ row }">
              <el-tooltip
                :content="`${row.shipping_no}_${row.product_cd}`"
                placement="top"
                :show-after="500"
                effect="light"
              >
                <el-tag :type="statusColor(row.status)" effect="light" class="code-tag">
                  {{ row.shipping_no.substring(0, 6) }}_{{ row.product_cd }}
                </el-tag>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column label="状態" width="80" v-if="columnVisible.status" key="status">
            <template #default="{ row }">
              <el-tag :type="statusColor(row.status)" effect="dark" class="status-tag">
                <el-icon v-if="row.status === '発行済'" class="status-icon">
                  <Check />
                </el-icon>
                <el-icon v-else-if="row.status === '未発行'" class="status-icon">
                  <Clock />
                </el-icon>
                <el-icon v-else-if="row.status === 'キャンセル'" class="status-icon">
                  <Close />
                </el-icon>
                {{ row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            label="操作"
            width="170"
            fixed="right"
            header-align="center"
            align="center"
            key="actions"
          >
            <template #default="{ row }">
              <div class="action-buttons">
                <el-tooltip content="編集" placement="top" :show-after="500">
                  <el-button
                    size="small"
                    @click.stop="editShipping(row)"
                    type="primary"
                    class="table-action-button icon-only"
                    circle
                  >
                    <el-icon>
                      <Edit />
                    </el-icon>
                  </el-button>
                </el-tooltip>
                <el-tooltip content="印刷" placement="top" :show-after="500">
                  <el-button
                    size="small"
                    type="success"
                    @click.stop="printShipping(row)"
                    :loading="actionLoading"
                    class="table-action-button icon-only"
                    circle
                  >
                    <el-icon>
                      <Printer />
                    </el-icon>
                  </el-button>
                </el-tooltip>
                <el-tooltip
                  content="取消"
                  placement="top"
                  :show-after="500"
                  v-if="row.status !== 'キャンセル'"
                >
                  <el-button
                    size="small"
                    type="danger"
                    @click.stop="cancel(row)"
                    :loading="actionLoading"
                    class="table-action-button icon-only"
                    circle
                  >
                    <el-icon>
                      <Close />
                    </el-icon>
                  </el-button>
                </el-tooltip>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- ページネーション -->
      <div class="pagination-container" v-if="shippingList.length">
        <div class="pagination-info">
          <span class="info-text">
            {{ (currentPage - 1) * pageSize + 1 }}-{{
              Math.min(currentPage * pageSize, shippingList.length)
            }}
            / {{ shippingList.length }}件
          </span>
        </div>
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="sizes, prev, pager, next"
          :total="shippingList.length"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          class="modern-pagination"
        />
      </div>
    </el-card>

    <!-- 詳細ダイアログ -->
    <ShippingDetailDialog
      v-if="detailVisible && selectedItem"
      :shippingItem="selectedItem"
      @close="detailVisible = false"
      @refresh="fetchData"
    />

    <!-- 数量・箱数 簡易編集ダイアログ -->
    <ShippingQuickEditDialog
      v-if="quickEditVisible && selectedItem"
      v-model="quickEditVisible"
      :shipping-item="selectedItem!"
      @refresh="fetchData"
    />
    <ShippingCreateDialog
      v-if="createDialogVisible"
      @close="createDialogVisible = false"
      @submitted="handleShippingCreated"
    />

    <!-- 納入先グループ管理ダイアログ -->
    <DestinationGroupManager
      v-model="showGroupManager"
      page-key="destination_groups_list"
      @groups-updated="handleGroupsUpdated"
    />

    <!-- ピッキング出力确认对话框 -->
    <el-dialog
      v-model="exportConfirmVisible"
      title=""
      width="420px"
      class="modern-dialog export-confirm-dialog"
      :close-on-click-modal="false"
      :close-on-press-escape="true"
      :show-close="true"
      align-center
    >
      <div class="export-confirm-content">
        <div class="confirm-icon-wrapper">
          <div class="confirm-icon-circle">
            <el-icon class="confirm-icon">
              <Download />
            </el-icon>
          </div>
        </div>
        <div class="confirm-title">ピッキングデータエクスポート</div>
        <div class="confirm-message">
          <p class="message-main">ピッキングデータを、CSVファイルとして、フォルダに保存します。</p>
          <p class="message-sub">この処理には時間がかかる場合があります。</p>
        </div>
        <div class="confirm-features">
          <div class="feature-item">
            <el-icon class="feature-icon">
              <Check />
            </el-icon>
            <span>CSV形式でエクスポート</span>
          </div>
          <div class="feature-item">
            <el-icon class="feature-icon">
              <Check />
            </el-icon>
            <span>詳細な進捗状況を表示</span>
          </div>
          <div class="feature-item">
            <el-icon class="feature-icon">
              <Check />
            </el-icon>
            <span>処理結果の詳細を確認</span>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="confirm-footer">
          <el-button @click="exportConfirmVisible = false" class="cancel-button">
            <el-icon>
              <Close />
            </el-icon>
            キャンセル
          </el-button>
          <el-button
            type="primary"
            @click="handleExportConfirm"
            :loading="exportLoading"
            class="confirm-button"
          >
            <el-icon v-if="!exportLoading">
              <Download />
            </el-icon>
            <el-icon v-else>
              <Loading />
            </el-icon>
            {{ exportLoading ? '処理中...' : '実行' }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- ピッキング出力进度对话框 -->
    <el-dialog
      v-model="exportProgressVisible"
      width="450px"
      class="modern-dialog export-progress-dialog"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
    >
      <template #header>
        <div class="progress-dialog-header">
          <span class="progress-dialog-title">ピッキングデータエクスポート</span>
          <el-button
            v-if="!exportLoading"
            @click="exportProgressVisible = false"
            class="progress-close-button"
            circle
            size="small"
            text
          >
            <el-icon>
              <Close />
            </el-icon>
          </el-button>
        </div>
      </template>
      <div class="export-progress-content">
        <div class="progress-status">
          <el-icon class="status-icon" :class="{ spinning: exportLoading }">
            <Loading v-if="exportLoading" />
            <Check v-else-if="exportProgressStatus === 'success'" />
            <Warning v-else-if="exportProgressStatus === 'warning'" />
            <Close v-else-if="exportProgressStatus === 'exception'" />
          </el-icon>
          <span class="status-text">{{ exportProgressMessage }}</span>
        </div>

        <div class="progress-bar-container" v-if="exportLoading || exportProgressStatus">
          <el-progress
            :percentage="exportProgressPercentage"
            :status="exportProgressStatus"
            :stroke-width="8"
            :show-text="true"
            :format="() => `${exportProgressPercentage}%`"
          />
        </div>

        <div class="progress-details" v-if="exportProgressDetails.length > 0">
          <div class="details-title">処理詳細:</div>
          <div class="details-list">
            <div v-for="(detail, index) in exportProgressDetails" :key="index" class="detail-item">
              <el-icon class="detail-icon">
                <Check v-if="detail.status === 'success'" />
                <Loading v-else-if="detail.status === 'processing'" />
                <Close v-else-if="detail.status === 'error'" />
                <InfoFilled v-else />
              </el-icon>
              <span class="detail-text">{{ detail.message }}</span>
              <span v-if="detail.count !== undefined" class="detail-count">
                ({{ detail.count }}件)
              </span>
            </div>
          </div>
        </div>

        <div class="progress-summary" v-if="exportProgressSummary">
          <div class="summary-title">処理結果:</div>
          <div class="summary-content">
            <div class="summary-item">
              <span class="summary-label">新規データ:</span>
              <span class="summary-value">{{ exportProgressSummary.copiedCount }}件</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">総データ数:</span>
              <span class="summary-value">{{ exportProgressSummary.totalDataCount }}件</span>
            </div>
            <div class="summary-item" v-if="exportProgressSummary.fileName">
              <span class="summary-label">ファイル名:</span>
              <span class="summary-value">{{ exportProgressSummary.fileName }}</span>
            </div>
            <div class="summary-item" v-if="exportProgressSummary.exportTime">
              <span class="summary-label">出力日時:</span>
              <span class="summary-value">{{ exportProgressSummary.exportTime }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 列表示設定ダイアログ -->
    <el-dialog
      v-model="columnSelectVisible"
      title="列表示設定"
      width="600px"
      class="modern-dialog"
      :before-close="() => (columnSelectVisible = false)"
    >
      <div class="column-select-container">
        <div class="column-select-description">表示する列を選択してください</div>
        <div class="checkbox-grid">
          <el-checkbox v-model="columnVisible.shipping_no" class="modern-checkbox" size="large">
            出荷番号
          </el-checkbox>
          <el-checkbox v-model="columnVisible.shipping_date" class="modern-checkbox" size="large">
            出荷日
          </el-checkbox>
          <el-checkbox v-model="columnVisible.delivery_date" class="modern-checkbox" size="large">
            納入日
          </el-checkbox>
          <el-checkbox
            v-model="columnVisible.destination_name"
            class="modern-checkbox"
            size="large"
          >
            納入先
          </el-checkbox>
          <el-checkbox v-model="columnVisible.product_cd" class="modern-checkbox" size="large">
            製品CD
          </el-checkbox>
          <el-checkbox v-model="columnVisible.product_name" class="modern-checkbox" size="large">
            製品名
          </el-checkbox>
          <el-checkbox v-model="columnVisible.confirmed_boxes" class="modern-checkbox" size="large">
            箱数
          </el-checkbox>
          <el-checkbox v-model="columnVisible.confirmed_units" class="modern-checkbox" size="large">
            数量
          </el-checkbox>
          <el-checkbox v-model="columnVisible.box_type" class="modern-checkbox" size="large">
            箱タイプ
          </el-checkbox>
          <el-checkbox v-model="columnVisible.code" class="modern-checkbox" size="large">
            コード
          </el-checkbox>
          <el-checkbox v-model="columnVisible.status" class="modern-checkbox" size="large">
            状態
          </el-checkbox>
        </div>
        <div class="dialog-footer">
          <el-button @click="resetColumnVisibility" class="reset-button" size="default">
            <el-icon>
              <Refresh />
            </el-icon>
            デフォルトに戻す
          </el-button>
          <el-button
            type="primary"
            @click="columnSelectVisible = false"
            class="confirm-button"
            size="default"
          >
            <el-icon>
              <Check />
            </el-icon>
            確定
          </el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import request from '@/utils/request'
import { getJSTToday as getJSTTodayUtil, formatDateJST, formatDateWithWeekdayJST, localeForIntl } from '@/utils/dateFormat'
import ShippingDetailDialog from './ShippingDetailDialog.vue'
import ShippingCreateDialog from './ShippingCreateDialog.vue'
import ShippingQuickEditDialog from './components/ShippingQuickEditDialog.vue'
import DestinationGroupManager from './components/DestinationGroupManager.vue'
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus'
import {
  Refresh,
  Document,
  Check,
  Close,
  Van,
  Plus,
  Edit,
  Printer,
  Setting,
  ArrowLeft,
  ArrowRight,
  Download,
  Calendar,
  Location,
  Clock,
  Loading,
  InfoFilled,
  Select,
  Collection,
  Warning,
} from '@element-plus/icons-vue'
import QRCode from 'qrcode'
import { exportPickingCSV } from '@/api/shipping/pickingExport'

// 定义接口
interface ShippingItem {
  id: number
  shipping_no: string
  shipping_date: string
  delivery_date: string | null
  destination_cd: string
  destination_name: string
  product_cd: string
  product_name: string
  product_alias: string | null
  box_type: string | null
  confirmed_boxes: number
  confirmed_units: number
  unit: string
  status: string
  remarks: string | null
  created_at: string
  updated_at: string
  [key: string]: any
}

interface FilterOptions {
  shipping_date: string
  delivery_date: string
  destination_cd: string
  product_cd: string
  product_name: string
  box_type: string
  status: string
  shipping_no: string
  end_date: string
}

const { t, locale } = useI18n()
const getJSTToday = getJSTTodayUtil

// 状態
const today = getJSTToday()

const filters = ref<FilterOptions>({
  shipping_date: today,
  delivery_date: '',
  destination_cd: '',
  product_cd: '',
  product_name: '',
  box_type: '',
  status: '',
  shipping_no: '',
  end_date: today,
})

const dateRange = ref<[string, string]>([today, today])
const shippingList = ref<ShippingItem[]>([])
const detailVisible = ref(false)
const createDialogVisible = ref(false)
const selectedItem = ref<ShippingItem | null>(null)
const quickEditVisible = ref(false)
const selectedRows = ref<ShippingItem[]>([])
const allSelectedIds = ref<Set<number>>(new Set()) // 跟踪所有选中项目的ID
const isSelectAllOperation = ref(false) // 标记是否正在进行全选操作
const loading = ref(false)
const actionLoading = ref(false)
const exportLoading = ref(false)
const pageLoading = ref(true)
const searchAnimating = ref(false)
const emptyText = computed(() => (loading.value ? '' : 'データがありません'))

// ピッキング出力确认对话框状态
const exportConfirmVisible = ref(false)

// ピッキング出力进度相关状态
const exportProgressVisible = ref(false)
const exportProgressPercentage = ref(0)
const exportProgressStatus = ref<'success' | 'exception' | 'warning' | ''>('')
const exportProgressMessage = ref('')
const exportProgressDetails = ref<
  Array<{ message: string; status: 'success' | 'processing' | 'error' | 'info'; count?: number }>
>([])
const exportProgressSummary = ref<{
  copiedCount: number
  totalDataCount: number
  fileName?: string
  csvFilePath?: string | null
  exportTime?: string
} | null>(null)

// 表格更新键，用于强制重新渲染
const tableKey = ref(0)

// 納入先選択
const destinationOptions = ref<{ value: string; label: string }[]>([])
const selectedDestinations = ref<string[]>([])

// 新的分组管理状态
const showGroupManager = ref(false)
const availableGroups = ref<any[]>([])

// 单选納入先
const singleDestination = ref<string>('')

// 納入先快捷按钮
const destinationQuickButtons = [
  { name: '愛知', code: 'N12' },
  { name: '東海', code: 'N18' },
  { name: '横浜', code: 'N39' },
  { name: '吉良', code: 'N38' },
]

// 快捷选择納入先
function selectQuickDestination(code: string): void {
  singleDestination.value = code
  handleSingleDestinationChange(code)
}

// 活跃的分组 (此功能将被简化或移除，因为新的管理器不直接支持多组筛选)
const activeGroups = ref<any[]>([])

// 用于保存拖拽分组结果的临时状态
const destinationGroups = ref<any[]>([])

// 分组筛选选择
const selectedGroupFilter = ref<number | undefined>(undefined)

// 按名字排序的纳入先选项（用于下拉框）
const sortedDestinationOptions = computed(() => {
  if (!destinationOptions.value || destinationOptions.value.length === 0) {
    return []
  }

  // 创建包含名字的选项数组
  const options = destinationOptions.value.map((dest) => {
    // 从label中提取名字（格式：cd - name）
    const parts = dest.label.split(' - ')
    return {
      value: dest.value,
      label: dest.label,
      name: parts.length > 1 ? parts[1] : parts[0],
    }
  })

  // 按名字排序（日文排序）
  options.sort((a, b) => {
    return a.name.localeCompare(b.name, 'ja')
  })

  return options
})

// 分组更新后的处理
function handleGroupsUpdated(updatedGroups: any[]) {
  availableGroups.value = updatedGroups.map((group) => ({
    ...group,
    groupName: group.group_name,
  }))

  // 如果当前选中的分组不存在了，重置筛选
  if (
    selectedGroupFilter.value !== undefined &&
    !availableGroups.value[selectedGroupFilter.value]
  ) {
    selectedGroupFilter.value = undefined
    handleGroupFilterChange(undefined)
  }

  ElMessage.success('グループ設定が更新されました。')
}

// 处理拖拽分组确认
const handleDestinationGroupsConfirm = (groups: any[], allSelected: string[]) => {
  destinationGroups.value = groups
  selectedDestinations.value = allSelected

  // 更新活跃分组（只显示有内容的分组）
  activeGroups.value = groups.filter((group) => group.destinations && group.destinations.length > 0)

  // 保存分组到localStorage并更新可用分组列表
  try {
    localStorage.setItem('destination_groups_list', JSON.stringify(groups))
    loadSavedGroups() // 重新加载可用分组
  } catch (error) {
    console.error('保存分组失败:', error)
  }

  // 更新筛选条件
  if (allSelected.length === 0) {
    filters.value.destination_cd = ''
  } else if (allSelected.length === 1) {
    filters.value.destination_cd = allSelected[0]
  } else {
    // 多选时，将所有选中的纳入先用逗号连接
    filters.value.destination_cd = allSelected.join(',')
  }

  // 自动执行搜索
  fetchData()

  ElMessage.success(
    `${activeGroups.value.length}個のグループから${allSelected.length}件の納入先を選択しました`,
  )
}

// 处理单选納入先变化
const handleSingleDestinationChange = (value: string) => {
  if (value) {
    // 单选納入先被选择
    selectedDestinations.value = [value]
    activeGroups.value = []
    selectedGroupFilter.value = undefined // 清除分组筛选下拉框的选择

    filters.value.destination_cd = value
    fetchData()
  } else {
    // 单选納入先被清除
    selectedDestinations.value = []
    filters.value.destination_cd = ''
    fetchData()
  }
}

// 清空所有分组
const clearAllGroups = () => {
  activeGroups.value = []
  selectedDestinations.value = []
  filters.value.destination_cd = ''

  ElMessage.success('全てのグループをクリアしました')
  fetchData()
}

// 移除单个分组
const removeGroup = (index: number) => {
  const removedGroup = activeGroups.value[index]
  activeGroups.value.splice(index, 1)

  // 重新计算选中的納入先
  const allSelected = activeGroups.value.reduce((acc: string[], group) => {
    return acc.concat(group.destinations.map((dest: any) => dest.value))
  }, [])

  selectedDestinations.value = allSelected

  // 更新筛选条件
  if (allSelected.length === 0) {
    filters.value.destination_cd = ''
  } else if (allSelected.length === 1) {
    filters.value.destination_cd = allSelected[0]
  } else {
    filters.value.destination_cd = allSelected.join(',')
  }

  ElMessage.success(`${removedGroup.name} を削除しました`)
  fetchData()
}

// 处理分组筛选变化
const handleGroupFilterChange = (groupIndex: number | undefined) => {
  if (groupIndex !== undefined && availableGroups.value[groupIndex]) {
    const selectedGroup = availableGroups.value[groupIndex]
    const groupDestinations = selectedGroup.destinations.map((dest: any) => dest.value)

    // 更新选择状态
    singleDestination.value = ''
    selectedDestinations.value = groupDestinations
    activeGroups.value = [] // 不再使用多组活跃状态

    // 更新筛选条件 - 让fetchData能够正确处理
    if (groupDestinations.length > 0) {
      filters.value.destination_cd = groupDestinations.join(',')
    } else {
      filters.value.destination_cd = ''
    }

    // 自动执行搜索
    fetchData()

    if (groupDestinations.length > 0) {
      ElMessage.success(
        `グループ「${selectedGroup.groupName ?? ''}」で絞り込みました（${groupDestinations.length}件）`,
      )
    }
  } else {
    // 清除分组筛选
    selectedDestinations.value = []
    filters.value.destination_cd = ''
    fetchData()
  }
}

// 加载保存的分组
const loadSavedGroups = () => {
  try {
    const savedGroups = localStorage.getItem('destination_groups_list')
    if (savedGroups) {
      const groups = JSON.parse(savedGroups)
      // 只显示有内容的分组
      availableGroups.value = groups.filter(
        (group: any) => group.destinations && group.destinations.length > 0,
      )
    }
  } catch (error) {
    console.error('加载已保存分组失败:', error)
    availableGroups.value = []
  }
}

// 日期快捷操作相关

// 计算选中的出荷番号数量 - 基于所有选中的项目
const selectedShippingNos = computed(() => {
  const selectedItems = shippingList.value.filter((item) => allSelectedIds.value.has(item.id))
  const uniqueShippingNos = new Set(selectedItems.map((row) => row.shipping_no))
  return uniqueShippingNos.size
})

// 计算当前分页中已选中的项目
const currentPageSelectedRows = computed(() => {
  return displayedList.value.filter((item) => allSelectedIds.value.has(item.id))
})

// 计算总选中项目数量
const totalSelectedCount = computed(() => {
  return allSelectedIds.value.size
})

// 页面加载动画
const handlePageLoad = async () => {
  pageLoading.value = true
  await nextTick()
  setTimeout(() => {
    pageLoading.value = false
  }, 800)
}

// ページネーション
const currentPage = ref(1)
const pageSize = ref(20)
const displayedList = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return shippingList.value.slice(start, end)
})

// 箱タイプのリスト
const boxTypes = ref(['小箱', '大箱', 'TP箱', '特殊'])

// QRコードのキャッシュ
const qrCodeCache: Record<string, string> = {}

// QRコード生成関数
async function generateQRCodeAsync(text: string): Promise<string> {
  try {
    if (qrCodeCache[text]) {
      return qrCodeCache[text]
    }
    const dataUrl = await QRCode.toDataURL(text, {
      width: 100,
      margin: 1,
      errorCorrectionLevel: 'M',
    })
    qrCodeCache[text] = dataUrl
    return dataUrl
  } catch (err) {
    console.error('QRコード生成エラー:', err)
    return ''
  }
}

// 箱タイプのタグカラー（el-tag type 用）
type ElTagType = 'success' | 'warning' | 'info' | 'danger' | 'primary'
function getBoxTypeTagType(boxType: string): ElTagType {
  if (!boxType || boxType === '未設定') return 'info'
  switch (boxType) {
    case '小箱':
      return 'success'
    case '大箱':
      return 'warning'
    case 'TP箱':
      return 'info'
    case '特殊':
      return 'danger'
    default:
      return 'primary'
  }
}

// ステータス色（el-tag type 用）
function statusColor(status: string): ElTagType {
  if (!status) return 'info'
  switch (status) {
    case '未発行':
      return 'info'
    case '発行済':
      return 'success'
    case '出荷済':
      return 'warning'
    case 'キャンセル':
      return 'danger'
    default:
      return 'info'
  }
}

// 行スタイル
function tableRowClassName({ row }: { row: ShippingItem }): string {
  if (row.status === 'キャンセル') {
    return 'canceled-row'
  }
  return ''
}

const intlLocale = computed(() => localeForIntl(locale.value))

function formatDate(dateStr: string | null): string {
  if (!dateStr) return ''
  return formatDateJST(dateStr, intlLocale.value).replace(/\//g, '-')
}

function formatDateWithWeekday(dateStr: string | null): string {
  if (!dateStr) return ''
  return formatDateWithWeekdayJST(dateStr, intlLocale.value).replace(/\//g, '-').replace(/\s/g, ' ')
}

// 行クリック - 避免与选择冲突，只在非选择列区域触发
function handleRowClick(row: ShippingItem, column: any): void {
  // 如果点击的是选择列，不触发编辑
  if (column && column.type === 'selection') {
    return
  }
  editShipping(row)
}

// ページサイズ変更
function handleSizeChange(newSize: number): void {
  pageSize.value = newSize
  currentPage.value = 1
  // 分页大小变更后，同步当前分页的选择状态
  nextTick(() => {
    syncCurrentPageSelection()
  })
}

// 同步当前分页的选择状态
function syncCurrentPageSelection(): void {
  if (!tableRef.value) return

  displayedList.value.forEach((row) => {
    const isSelected = allSelectedIds.value.has(row.id)
    tableRef.value?.toggleRowSelection(row, isSelected)
  })
}

// ページ変更
function handleCurrentChange(newPage: number): void {
  currentPage.value = newPage
  // 分页切换后，同步当前分页的选择状态
  nextTick(() => {
    syncCurrentPageSelection()
  })
}

// 選択された行の処理 - 出荷番号でグループ化
function handleSelectionChange(rows: ShippingItem[]): void {
  selectedRows.value = rows

  // 只在不是全选操作时更新全局选中状态
  if (!isSelectAllOperation.value) {
    // 先移除当前分页中所有项目的选中状态
    displayedList.value.forEach((item) => {
      allSelectedIds.value.delete(item.id)
    })

    // 然后添加当前选中项目的ID
    rows.forEach((item) => {
      allSelectedIds.value.add(item.id)
    })
  }
}

// 表格引用
const tableRef = ref()

// 手动选择处理 - 支持按出荷番号分组选择
function handleSelectRow(selection: ShippingItem[], row: ShippingItem): void {
  const isSelected = selection.some((item) => item.id === row.id)

  // 获取所有相同出荷番号的行（包括不在当前分页的）
  const sameShippingNoRows = shippingList.value.filter(
    (item) => item.shipping_no === row.shipping_no,
  )

  // 获取当前分页中相同出荷番号的行
  const currentPageSameRows = displayedList.value.filter(
    (item) => item.shipping_no === row.shipping_no,
  )

  if (isSelected) {
    // 如果当前行被选中，则选中所有相同出荷番号的行（包括其他分页的）
    sameShippingNoRows.forEach((item) => {
      allSelectedIds.value.add(item.id)
    })

    // 同步当前分页的选择状态
    currentPageSameRows.forEach((item) => {
      if (!selection.some((selected) => selected.id === item.id)) {
        tableRef.value?.toggleRowSelection(item, true)
      }
    })

    // 如果同一出荷番号有多个产品，显示提示
    if (sameShippingNoRows.length > 1) {
      ElMessage({
        message: `出荷番号 ${row.shipping_no} の${sameShippingNoRows.length}件の製品を選択しました`,
        type: 'info',
        duration: 2000,
        showClose: true,
      })
    }
  } else {
    // 如果当前行被取消选中，则取消选中所有相同出荷番号的行（包括其他分页的）
    sameShippingNoRows.forEach((item) => {
      allSelectedIds.value.delete(item.id)
    })

    // 同步当前分页的选择状态
    currentPageSameRows.forEach((item) => {
      tableRef.value?.toggleRowSelection(item, false)
    })

    // 如果同一出荷番号有多个产品，显示提示
    if (sameShippingNoRows.length > 1) {
      ElMessage({
        message: `出荷番号 ${row.shipping_no} の${sameShippingNoRows.length}件の製品の選択を解除しました`,
        type: 'info',
        duration: 2000,
        showClose: true,
      })
    }
  }
}

// 全选处理 - 选择所有筛选结果
function handleSelectAll(selection: ShippingItem[]): void {
  isSelectAllOperation.value = true // 标记开始全选操作

  const isAllCurrentPageSelected = selection.length === displayedList.value.length

  if (isAllCurrentPageSelected) {
    // 当前分页全选时，选中所有筛选结果
    shippingList.value.forEach((item) => {
      allSelectedIds.value.add(item.id)
    })

    ElMessage({
      message: `全ての検索結果 ${shippingList.value.length}件を選択しました`,
      type: 'success',
      duration: 3000,
      showClose: true,
    })
  } else {
    // 取消全选时，清空所有选择
    allSelectedIds.value.clear()

    ElMessage({
      message: '全ての選択を解除しました',
      type: 'info',
      duration: 2000,
      showClose: true,
    })
  }

  // 重置标志
  nextTick(() => {
    isSelectAllOperation.value = false
  })
}

// 防止期间/納入先等下拉点击时弹出虚拟键盘（移动端）
function preventKeyboardOnFocus(e: FocusEvent): void {
  const target = e.target as HTMLElement
  const input =
    target?.tagName === 'INPUT' ? target : target?.querySelector?.('input')
  if (input) {
    input.setAttribute('inputmode', 'none')
  }
}

// 日付範囲の変更処理（自动筛选）
function handleDateRangeChange(range: [string, string] | null): void {
  if (range && range.length === 2) {
    filters.value.shipping_date = range[0]
    // 明示的にend_dateを設定しない（fetchData内で処理するため）
  } else {
    filters.value.shipping_date = ''
  }
  fetchData()
}

// フィルターリセット
function resetFilters(): void {
  dateRange.value = [today, today]
  filters.value = {
    shipping_date: today,
    delivery_date: '',
    destination_cd: '',
    product_cd: '',
    product_name: '',
    box_type: '',
    status: '',
    shipping_no: '',
    end_date: today,
  }
  selectedDestinations.value = []
  activeGroups.value = []
  singleDestination.value = ''
  selectedGroupFilter.value = undefined
  fetchData()
}

// データ取得
async function fetchData(): Promise<void> {
  loading.value = true
  searchAnimating.value = true

  try {
    // 添加搜索动画延迟
    await new Promise((resolve) => setTimeout(resolve, 300))

    // 构建查询参数，移除空值
    const queryParams = Object.entries(filters.value).reduce(
      (acc: Record<string, string>, [key, value]) => {
        if (value && value.toString().trim() !== '') {
          // 确保所有值都被转换为字符串
          acc[key] = value.toString()
        }
        return acc
      },
      {},
    )

    // 如果有日期范围，添加结束日期
    if (dateRange.value && dateRange.value.length === 2 && dateRange.value[1]) {
      queryParams.end_date = dateRange.value[1]
    }

    // shipping_itemsテーブルからデータを取得
    const res = await request.get('/api/shipping/items', { params: queryParams })

    // データの整形処理
    shippingList.value = Array.isArray(res)
      ? res.map((item: any) => {
          // 各フィールドの存在確認とデフォルト値設定
          return {
            ...item,
            // 基本字段确保存在
            id: item.id || 0,
            shipping_no: item.shipping_no || '',
            shipping_date: item.shipping_date || '',
            destination_cd: item.destination_cd || '',
            destination_name: item.destination_name || '',
            product_cd: item.product_cd || '',
            // 納入日がnullの場合は空文字列を設定
            delivery_date: item.delivery_date || '',
            // 箱タイプがnullの場合は「未設定」を設定
            box_type: item.box_type || '未設定',
            // 箱数がnullの場合は0を設定
            confirmed_boxes: Number(item.confirmed_boxes) || 0,
            // 数量确保是数字
            confirmed_units: Number(item.confirmed_units) || 0,
            // 状態が設定されていない場合は「未発行」を設定
            status: item.status || '未発行',
            // 製品名が設定されていない場合は製品CDを使用
            product_name: item.product_name || item.product_cd || '',
            // 単位が設定されていない場合は「本」を設定
            unit: item.unit || '本',
            // 備考がnullの場合は空文字列を設定
            remarks: item.remarks || '',
            // 时间戳字段
            created_at: item.created_at || '',
            updated_at: item.updated_at || '',
          }
        })
      : []

    // 初始ページに戻す
    currentPage.value = 1

    // 强制更新表格
    tableKey.value++

    // 清空选择状态（因为数据已更新）
    allSelectedIds.value.clear()
    selectedRows.value = []

    // 使用通知而不是消息，提供更好的视觉反馈
    if (shippingList.value.length === 0) {
      ElNotification({
        title: '検索結果',
        message: '検索条件に一致する出荷データはありません',
        type: 'info',
        duration: 3000,
        position: 'top-right',
      })
    } else {
      ElNotification({
        title: '検索完了',
        message: `${shippingList.value.length}件の出荷データを取得しました`,
        type: 'success',
        duration: 3000,
        position: 'top-right',
      })
    }
  } catch (error) {
    console.error('出荷データの取得に失敗しました:', error)
    ElNotification({
      title: 'エラー',
      message: '出荷データの取得に失敗しました',
      type: 'error',
      duration: 4000,
      position: 'top-right',
    })
    shippingList.value = []
  } finally {
    loading.value = false
    searchAnimating.value = false
  }
}

// 編集処理
function editShipping(row: ShippingItem): void {
  // 检查编辑权限
  if (row.status === 'キャンセル') {
    ElMessage.warning('キャンセル済みの出荷は編集できません')
    return
  }
  selectedItem.value = { ...row }
  quickEditVisible.value = true
}

// 発行処理
async function issue(row: ShippingItem): Promise<void> {
  try {
    actionLoading.value = true
    await ElMessageBox.confirm('この出荷を発行しますか？', '確認', {
      confirmButtonText: '発行',
      cancelButtonText: 'キャンセル',
      type: 'info',
    })

    try {
      // 出荷番号を発行
      await request.post(`/api/shipping/${row.shipping_no}/issue`)

      ElMessage.success('出荷番号を発行しました')
      await fetchData() // データを再取得
    } catch (apiError) {
      console.error('API呼び出しエラー:', apiError)
      ElMessage.error('発行処理に失敗しました')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('発行処理に失敗しました:', error)
      ElMessage.error('発行処理に失敗しました')
    }
  } finally {
    actionLoading.value = false
  }
}

// 单个出荷データを印刷 - 同一出荷番号の全ての製品を印刷
async function printShipping(row: ShippingItem): Promise<void> {
  actionLoading.value = true
  try {
    // 同じ出荷番号の全ての製品を取得
    const sameShippingNoItems = shippingList.value.filter(
      (item) => item.shipping_no === row.shipping_no,
    )

    // 事前にQRコードを生成
    await prepareQRCodes(sameShippingNoItems)

    // 印刷用のHTMLを生成
    const printContent = generatePrintHTML(sameShippingNoItems)

    // 印刷用のiframeを作成
    const printFrame = document.createElement('iframe')
    printFrame.style.position = 'absolute'
    printFrame.style.top = '-1000px'
    printFrame.style.left = '-1000px'
    document.body.appendChild(printFrame)

    // iframe内にHTMLを書き込み
    const frameDoc = printFrame.contentDocument || printFrame.contentWindow?.document
    if (frameDoc) {
      frameDoc.open()
      frameDoc.write(printContent)
      frameDoc.close()

      // 印刷処理
      setTimeout(() => {
        printFrame.contentWindow?.print()
        // 印刷ダイアログが閉じられた後にiframeを削除
        setTimeout(() => {
          document.body.removeChild(printFrame)
        }, 1000)
      }, 500)
    }

    // 印刷記録をデータベースに保存し、状態を更新
    try {
      await request.post('/api/shipping/print-record', {
        shipping_numbers: [row.shipping_no],
      })

      ElMessage.success(
        `出荷番号: ${row.shipping_no} (${sameShippingNoItems.length}件の製品) を印刷し、記録を保存しました`,
      )

      // データを再取得して最新状態を反映
      await fetchData()
    } catch (recordError) {
      console.error('印刷記録の保存に失敗しました:', recordError)
      ElMessage.warning(
        `印刷は完了しましたが、記録の保存に失敗しました: ${(recordError as any)?.message || '不明なエラー'}`,
      )
    }
  } catch (error) {
    console.error('印刷処理に失敗しました:', error)
    ElMessage.error('印刷処理に失敗しました')
  } finally {
    actionLoading.value = false
  }
}

// キャンセル処理
async function cancel(row: ShippingItem): Promise<void> {
  try {
    actionLoading.value = true
    await ElMessageBox.confirm(
      'この出荷データを削除しますか？\n注意：選択したデータのみが削除されます。',
      '確認',
      {
        confirmButtonText: '削除',
        cancelButtonText: '戻る',
        type: 'warning',
      },
    )

    try {
      // 選択した行のIDを使用して、該当する出荷データのみをキャンセル
      await request.post(`/api/shipping/items/${row.id}/cancel`)

      // 成功メッセージを表示して、データを再取得
      ElMessage.success('選択した出荷データのキャンセル処理が完了しました')
      await fetchData()
    } catch (apiError) {
      console.error('API呼び出しエラー:', apiError)
      ElMessage.error('キャンセル処理に失敗しました')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('キャンセル処理に失敗しました:', error)
      ElMessage.error('キャンセル処理に失敗しました')
    }
  } finally {
    actionLoading.value = false
  }
}

// 批量删除选中的出荷数据
async function cancelSelected(): Promise<void> {
  if (allSelectedIds.value.size === 0) {
    ElMessage.warning('削除する出荷データを選択してください')
    return
  }

  try {
    actionLoading.value = true

    // 获取所有选中的项目
    const selectedItems = shippingList.value.filter((item) => allSelectedIds.value.has(item.id))

    await ElMessageBox.confirm(
      `選択した${selectedItems.length}件の出荷データを削除しますか？\n注意：選択したデータのみが削除されます。`,
      '確認',
      {
        confirmButtonText: '削除',
        cancelButtonText: '戻る',
        type: 'warning',
      },
    )

    try {
      // 批量删除：循环调用删除API
      const deletePromises = selectedItems.map((item) =>
        request.post(`/api/shipping/items/${item.id}/cancel`).catch((error) => {
          console.error(`删除项目 ${item.id} 失败:`, error)
          return { error: true, id: item.id }
        }),
      )

      const results = await Promise.all(deletePromises)

      // 检查是否有失败的删除（接口返回 data 体，可能含 error）
      const failedItems = results.filter((result: unknown) => result != null && typeof result === 'object' && 'error' in result && (result as { error?: boolean }).error)

      if (failedItems.length > 0) {
        ElMessage.warning(
          `${selectedItems.length - failedItems.length}件の削除が成功しましたが、${failedItems.length}件の削除に失敗しました`,
        )
      } else {
        ElMessage.success(`${selectedItems.length}件の出荷データのキャンセル処理が完了しました`)
      }

      // 清空选择状态
      allSelectedIds.value.clear()
      selectedRows.value = []

      // データを再取得
      await fetchData()
    } catch (apiError) {
      console.error('API呼び出しエラー:', apiError)
      ElMessage.error('キャンセル処理に失敗しました')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('キャンセル処理に失敗しました:', error)
      ElMessage.error('キャンセル処理に失敗しました')
    }
  } finally {
    actionLoading.value = false
  }
}

// 出荷単作成ダイアログを開く
function openCreateDialog(): void {
  createDialogVisible.value = true
}

// 出荷単作成完了処理
function handleShippingCreated(): void {
  ElNotification({
    title: '作成完了',
    message: '出荷単を作成しました',
    type: 'success',
    duration: 3000,
    position: 'top-right',
  })
  fetchData()
}

// 選択された出荷データを印刷 - 出荷番号でグループ化
async function printSelected(): Promise<void> {
  if (allSelectedIds.value.size === 0) {
    ElMessage.warning('印刷する出荷データを選択してください')
    return
  }

  actionLoading.value = true
  try {
    // 获取所有选中的项目
    const selectedItems = shippingList.value.filter((item) => allSelectedIds.value.has(item.id))

    // 選択された行から出荷番号を取得
    const selectedShippingNumbers = new Set(selectedItems.map((row) => row.shipping_no))

    // 各出荷番号の全ての製品を取得
    const allItemsToPrint: ShippingItem[] = []
    selectedShippingNumbers.forEach((shippingNo) => {
      const itemsForShipping = shippingList.value.filter((item) => item.shipping_no === shippingNo)
      allItemsToPrint.push(...itemsForShipping)
    })

    // 事前にQRコードを生成
    await prepareQRCodes(allItemsToPrint)

    // 印刷用のHTMLを生成
    const printContent = generatePrintHTML(allItemsToPrint)

    // 印刷用のiframeを作成
    const printFrame = document.createElement('iframe')
    printFrame.style.position = 'absolute'
    printFrame.style.top = '-1000px'
    printFrame.style.left = '-1000px'
    document.body.appendChild(printFrame)

    // iframe内にHTMLを書き込み
    const frameDoc = printFrame.contentDocument || printFrame.contentWindow?.document
    if (frameDoc) {
      frameDoc.open()
      frameDoc.write(printContent)
      frameDoc.close()

      // 印刷処理
      setTimeout(() => {
        printFrame.contentWindow?.print()
        // 印刷ダイアログが閉じられた後にiframeを削除
        setTimeout(() => {
          document.body.removeChild(printFrame)
        }, 1000)
      }, 500)
    }

    // 印刷記録をデータベースに保存し、状態を更新
    try {
      await request.post('/api/shipping/print-record', {
        shipping_numbers: Array.from(selectedShippingNumbers),
      })

      ElMessage.success(
        `${selectedShippingNumbers.size}件の出荷番号 (計${allItemsToPrint.length}製品) を印刷し、記録を保存しました`,
      )

      // データを再取得して最新状態を反映
      await fetchData()
    } catch (recordError) {
      console.error('印刷記録の保存に失敗しました:', recordError)
      ElMessage.warning(
        `印刷は完了しましたが、記録の保存に失敗しました: ${(recordError as any)?.message || '不明なエラー'}`,
      )
    }
  } catch (error) {
    console.error('印刷処理に失敗しました:', error)
    ElMessage.error('印刷処理に失敗しました')
  } finally {
    actionLoading.value = false
  }
}

// 同步的にQRコードを生成する関数
function generateQRCode(text: string): string {
  try {
    // キャッシュにあれば、それを使用
    if (qrCodeCache[text]) {
      return qrCodeCache[text].split(',')[1] // Base64部分のみ取得
    }
    // なければ空の画像を返す（非同期処理の結果を待てないため）
    return ''
  } catch (err) {
    console.error('QRコード生成エラー:', err)
    return ''
  }
}

// 印刷前にすべてのQRコードを事前生成
async function prepareQRCodes(items: ShippingItem[]): Promise<void> {
  const qrTexts: string[] = []

  // 必要なQRコードのテキストを収集
  items.forEach((item) => {
    const qrText = `${item.shipping_no}_${item.product_cd}`
    if (!qrCodeCache[qrText]) {
      qrTexts.push(qrText)
    }
  })

  // 並列で生成
  await Promise.all(
    qrTexts.map(async (text) => {
      qrCodeCache[text] = await generateQRCodeAsync(text)
    }),
  )
}

// 印刷用HTMLの生成
function generatePrintHTML(items: ShippingItem[]): string {
  const title = '出荷リスト'
  const date = new Date().toLocaleDateString('ja-JP', { timeZone: 'Asia/Tokyo' })

  // 同じ出荷番号ごとにグループ化
  const groupedByShippingNo: Record<string, ShippingItem[]> = {}

  items.forEach((item) => {
    if (!groupedByShippingNo[item.shipping_no]) {
      groupedByShippingNo[item.shipping_no] = []
    }
    groupedByShippingNo[item.shipping_no].push(item)
  })

  // 出荷番号ごとに1ページずつ印刷するための設定

  let html = `
    <!DOCTYPE html>
    <html>
    <head>
      <title>${title}</title>
      <meta charset="utf-8">
      <style>
        @page {
          size: A4;
          margin: 10mm;
          margin-top: 2cm;
        }
        body {
          font-family: '游ゴシック','Arial', 'Hiragino Sans', 'Meiryo', sans-serif;
          margin: 0;
          padding: 0;
          background-color: white;
          color: black;
        }
        .page {
          page-break-after: always;
          page-break-inside: avoid;
          padding: 20px;
          position: relative;
          min-height: 257mm; /* A4サイズから余白を引いた高さ */
          display: flex;
          flex-direction: column;
          margin-top: 0;
          box-sizing: border-box;
        }
        .page:first-child {
          margin-top: 0;
        }

        /* 上部スタイル */
        .page-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          padding-bottom: 15px;
          border-bottom: 1px solid #000;
          margin-bottom: 20px;
        }
        .shipping-no-left {
          font-size: 13px;
          font-weight: normal;
          display: flex;
          flex-direction: column;
          align-items: flex-start;
          gap: 10px;
        }

        .shipping-date-right {
          font-size: 33px;
          font-weight: bold;
          text-align: right;
          line-height: 1.2;
        }

        /* 中部スタイル */
        .page-content {
          flex: 1;
        }
        .section {
        text-align: right;
          margin-bottom: 20px;
        }
        .section-title {
          font-size: 16px;
          font-weight: bold;
          text-align: left;
          margin-top: 5px;
          margin-bottom: 10px;
          padding: 5px;
          background-color: #f2f2f2;
          border-left: 5px solid #333;
        }
        .destination-section {
          margin-bottom: 20px;
        }
        .destination-name {
          font-size: 50px;
          font-weight: bold;
          text-align: center;
          margin-bottom: 5px;
        }
        .destination-code {
          font-size: 14px;
        }
        .company-section {
          margin-bottom: 20px;
        }
        .company-name {
          font-weight: bold;
          font-size: 16px;
          margin-bottom: 5px;
        }
        .company-address, .company-tel {
          font-size: 14px;
          margin-bottom: 3px;
        }
        .delivery-section {
          margin-bottom: 1px;
        }
        .delivery-date {
          font-size: 16px;
          font-weight: bold;
        }
        .products-title {
          margin-top: 25px;
          margin-bottom: 10px;
        }

        /* テーブルスタイル */
        table {
          width: 100%;
          border-collapse: collapse;
          margin: 5px 0 5px 0;
        }
        th, td {
          border: 1px solid #000;
          padding: 4px;
          text-align: left;
          font-size: 14px;
          font-weight: bold;

        }
        .product-name-cell {
          position: relative;
        }
        .product-type {
          position: absolute;
          top: 2px;
          right: 4px;
          font-size: 10px;
          font-weight: normal;
          color: #666;
        }
        th {
          background-color: #f2f2f2;
          font-weight: bold;
          text-align: center;
        }
          td{
          font-size: 30px;
          }
        .text-right {
          text-align: center;
        }
        .text-center {
          text-align: center;
        }

        /* 合計セクション */
        .totals-section {
          display: table;
          width: 100%;
          margin: 0;
          padding: 0;
        }
        .totals-row {
          display: table-row;
        }
        .total-cell {
          display: table-cell;
          border: 1px solid #000;
          padding: 2px;
          text-align: center;
          font-size: 30px;
          font-weight: bold;

          vertical-align: middle;
        }
        .total-cell.product-name {
          text-align: center;
          font-size: 30px;
          font-weight: bold;

          font-weight: bold;
        }
        .total-cell.code {
          font-size: 16px;
        }
        .total-cell.code.confirm-text {
          color: #999;
        }

        /* 下部スタイル */
        .page-footer {
          display: flex;
          justify-content: space-between;
          border-top: 1px solid #000;
          padding-top: 10px;
          margin-top: 20px;
          font-size: 12px;
        }
        .shipping-no-suffix {
          font-weight: bold;
          font-size: 16px;
        }

        /* QRコード */
        .qrcode-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
        }
        .qrcode-text {
          font-size: 10px;
          margin-top: 5px;
          word-break: break-all;
        }
        .status-cell {
          width: 80px;
        }
        .status-tag {
          padding: 3px 8px;
          border-radius: 4px;
          font-weight: bold;
          display: inline-block;
        }
        .status-issued {
          background-color: #67c23a;
          color: white;
        }
        .status-not-issued {
          background-color: #909399;
          color: white;
        }
        @media print {
          body {
            padding: 0;
            margin: 0;
          }
          .no-print {
            display: none;
          }
          .page {
            page-break-after: always;
            page-break-before: auto;
            page-break-inside: avoid;
            margin-top: 0 !important;
            padding-top: 20px !important;
          }
          .page:first-child {
            page-break-before: avoid;
          }
        }
      </style>
    </head>
    <body>
  `

  // 出荷番号ごとにページを作成
  Object.entries(groupedByShippingNo).forEach(([shippingNo, groupItems]) => {
    // 各グループの最初のアイテムから情報を取得
    const firstItem = groupItems[0]

    // 合計箱数と本数を計算
    let totalBoxes = 0
    let totalUnits = 0
    groupItems.forEach((item) => {
      totalBoxes += item.confirmed_boxes || 0
      totalUnits += item.confirmed_units
    })

    // 現在の日時を取得
    const now = new Date()
    // 使用日本时区获取时间
    const jstDate = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Tokyo' }))
    const currentDateTime =
      jstDate.toLocaleDateString('ja-JP') +
      ' ' +
      jstDate.getHours().toString().padStart(2, '0') +
      ':' +
      jstDate.getMinutes().toString().padStart(2, '0')

    // 出荷番号の後ろ3桁
    const shippingNoLast3 = shippingNo.slice(-2)

    // 状態の判定（発行履歴があれば「発行済」）
    const status = firstItem.status || '未発行'

    html += `
      <div class="page">
        <!-- 上部 -->
        <div class="page-header">
          <div class="shipping-no-left">
            <div>管理番号: ${shippingNo}</div>
          </div>
          <div class="shipping-date-right">出荷日: ${formatDateWithWeekday(firstItem.shipping_date)}</div>
        </div>

        <!-- 中部 -->
        <div class="page-content">
          <!-- 第1層: 納入先 -->
          <div class="section destination-section">
            <div class="section-title">納入先</div>
            <div class="destination-name">${firstItem.destination_name} 御中</div>

          </div>

          <!-- 第2層: 会社情報 -->
          <div class="section company-section">
            <div class="company-name">日鉄物産荒井オートモーティブ(株)</div>
            <div class="company-address">〒496-0902 愛知県愛西市須依町2189</div>
            <div class="company-tel">TEL: 0567-28-4171 FAX: 0567-28-2281</div>
          </div>

          <!-- 第3層: 納入日 -->
          <div class="section delivery-section">
            <div class="shipping-date-right">納入日: ${formatDateWithWeekday(firstItem.delivery_date)}</div>
          </div>

          <!-- 第4層: 出荷構成品タイトル -->
          <div class="section-title products-title">出荷構成品</div>

          <!-- 第5層: 製品リスト -->
          <table>
            <thead>
              <tr>
              <th>製品名</th>
              <th class="text-right">箱数</th>
              <th class="text-right">数量</th>
              <th>コード</th>
              </tr>
            </thead>
            <tbody>
    `

    // 同じ出荷番号の製品を表示
    groupItems.forEach((item) => {
      html += `
        <tr>

          <td class="product-name-cell">${item.product_name}<span class="product-type">${item.product_type || ''}</span></td>
          <td class="text-right">${(item.confirmed_boxes || 0).toLocaleString()}</td>
          <td class="text-right">${item.confirmed_units.toLocaleString()}</td>

          <td class="text-center">
            <div class="qrcode-container">
              <img src="data:image/png;base64,${generateQRCode(`${shippingNo}_${item.product_cd}`)}" alt="QRコード" width="40" height="40" />

            </div>
          </td>

        </tr>
      `
    })

    html += `
          </tbody>
        </table>
        </div>

        <!-- 第6層: 合計 -->
        <div class="totals-section">
          <div class="totals-row">
            <div class="total-cell product-name">合計</div>
            <div class="total-cell">${totalBoxes.toLocaleString()}箱</div>
            <div class="total-cell">${totalUnits.toLocaleString()}本</div>
            <div class="total-cell code confirm-text">確認</div>
          </div>
        </div>

        <!-- 下部 -->
        <div class="page-footer">
          <div class="print-datetime">発行日時: ${currentDateTime}</div>
          <div class="shipping-no-suffix">パレット番号${shippingNoLast3}</div>
        </div>
      </div>
    `
  })

  html += `
      <div class="no-print">
        <button onclick="window.print()">印刷</button>
        <button onclick="window.close()">閉じる</button>
      </div>
    </body>
    </html>
  `

  return html
}

// 初期データ取得
onMounted(async () => {
  await handlePageLoad()
  await fetchDestinations()
  await loadDestinationGroups() // 加载分组
  await fetchData()
})

// 納入先データ取得
async function fetchDestinations(): Promise<void> {
  try {
    const response = await request.get('/api/master/destinations/options') as
      | unknown[]
      | { success?: boolean; data?: unknown[] }

    // 处理两种可能的响应格式（request 拦截器返回 response.data）
    let dataArray: any[] = []

    if (Array.isArray(response)) {
      // 直接返回数组的情况
      dataArray = response
    } else if (response && response.success === true && Array.isArray(response.data)) {
      // 返回对象包含data字段的情况
      dataArray = response.data
    } else if (response && Array.isArray(response.data)) {
      // 返回对象包含data字段但没有success字段的情况
      dataArray = response.data
    } else {
      console.error('納入先データ格式不正确:', response)
      ElMessage.error('納入先データの取得に失敗しました')
      return
    }

    // 按名字排序后再映射
    dataArray.sort((a, b) => {
      return (a.name || '').localeCompare(b.name || '', 'ja')
    })

    destinationOptions.value = dataArray.map((item: any) => ({
      value: item.cd,
      label: `${item.cd} - ${item.name}`,
    }))
  } catch (error) {
    console.error('获取納入先失败:', error)
    ElMessage.error('納入先データの取得に失敗しました')
  }
}

// 列表示設定
const columnSelectVisible = ref(false)
const columnVisible = ref(loadColumnVisibility())

// 列表示設定の読み込み
function loadColumnVisibility(): Record<string, boolean> {
  try {
    const savedSettings = localStorage.getItem('shippingListColumnSettings')
    if (savedSettings) {
      return JSON.parse(savedSettings)
    }
  } catch (error) {
    // 設定読み込み失敗時はデフォルト設定を使用
  }

  // デフォルト設定
  return {
    shipping_no: true,
    shipping_date: true,
    delivery_date: true,
    destination_name: true,
    product_cd: true,
    product_name: true,
    confirmed_boxes: true,
    confirmed_units: true,
    box_type: true,
    code: true,
    status: true,
  }
}

// 列表示設定の保存
function saveColumnVisibility(): void {
  try {
    localStorage.setItem('shippingListColumnSettings', JSON.stringify(columnVisible.value))
  } catch (error) {
    // 設定保存失敗時は無視
  }
}

// 列表示設定をデフォルトに戻す
function resetColumnVisibility(): void {
  columnVisible.value = {
    shipping_no: true,
    shipping_date: true,
    delivery_date: true,
    destination_name: true,
    product_cd: true,
    product_name: true,
    confirmed_boxes: true,
    confirmed_units: true,
    box_type: true,
    code: true,
    status: true,
  }
  saveColumnVisibility()
}

// 列表示設定が変更されたら保存
watch(
  columnVisible,
  () => {
    saveColumnVisibility()
  },
  { deep: true },
)

// 监听分页数据变化，同步选择状态
watch(
  displayedList,
  () => {
    nextTick(() => {
      syncCurrentPageSelection()
    })
  },
  { flush: 'post' },
)

// 日期快捷操作函数
function adjustDate(days: number): void {
  const currentStart = dateRange.value[0] ? new Date(dateRange.value[0]) : new Date()
  const currentEnd = dateRange.value[1] ? new Date(dateRange.value[1]) : new Date()

  currentStart.setDate(currentStart.getDate() + days)
  currentEnd.setDate(currentEnd.getDate() + days)

  dateRange.value = [
    currentStart.toISOString().split('T')[0],
    currentEnd.toISOString().split('T')[0],
  ]

  handleDateRangeChange(dateRange.value)
}

function setToday(): void {
  const todayJST = getJSTToday()
  dateRange.value = [todayJST, todayJST]
  handleDateRangeChange(dateRange.value)
}

// 納入先選択関連函数
function getDestinationLabel(code: string): string {
  const dest = destinationOptions.value.find((d) => d.value === code)
  return dest ? `${dest.value} - ${dest.label}` : code
}

// 打开ピッキング出力确认对话框
function openExportConfirmDialog(): void {
  exportConfirmVisible.value = true
}

// 确认执行导出
async function handleExportConfirm(): Promise<void> {
  exportConfirmVisible.value = false
  await exportPickingCSVData()
}

// ピッキングCSV导出功能
async function exportPickingCSVData(): Promise<void> {
  try {
    exportLoading.value = true

    // 初始化进度状态
    exportProgressVisible.value = true
    exportProgressPercentage.value = 0
    exportProgressStatus.value = ''
    exportProgressMessage.value = 'エクスポート処理を開始しています...'
    exportProgressDetails.value = []
    exportProgressSummary.value = null

    // 添加初始进度详情
    addProgressDetail('エクスポート処理を開始', 'info')
    addProgressDetail('データを取得中...', 'processing')

    // 模拟进度更新（因为后端可能不支持实时进度）
    // 使用更平滑的进度更新逻辑
    let currentProgress = 0
    const targetProgress = 85 // 在API完成前最多到85%
    const progressInterval = setInterval(() => {
      if (currentProgress < targetProgress) {
        // 使用指数衰减，使进度更新越来越慢
        const remaining = targetProgress - currentProgress
        const increment = Math.max(remaining * 0.08, 0.3) // 每次至少增加0.3%，更慢的进度更新
        currentProgress = Math.min(currentProgress + increment, targetProgress)
        exportProgressPercentage.value = Math.round(currentProgress)
      }
    }, 500) // 增加更新间隔，使进度更平滑

    try {
      // 仕様: 更新文案 → 追加详情（60分注意）→ 呼び出し
      updateProgressMessage('サーバーにリクエストを送信中...')
      addProgressDetail(
        '注意: データ量が多い場合、処理に時間がかかる場合があります（最大60分）',
        'info',
      )

      const response = await exportPickingCSV()

      // 清除进度更新定时器
      clearInterval(progressInterval)

      // 更新进度到100%
      exportProgressPercentage.value = 100
      exportProgressStatus.value = 'success'
      updateProgressMessage('エクスポート処理が完了しました！')

      // 更新进度详情
      updateProgressDetail('データを取得中...', 'データ取得完了', 'success')
      addProgressDetail('CSVファイルを生成中...', 'processing')
      setTimeout(() => {
        updateProgressDetail('CSVファイルを生成中...', 'CSVファイル生成完了', 'success')
        addProgressDetail('ファイルを保存中...', 'processing')
        setTimeout(() => {
          updateProgressDetail('ファイルを保存中...', 'ファイル保存完了', 'success')
        }, 300)
      }, 300)

      // 拦截器返回 response.data（API 成功時の body）
      const data = response as unknown as {
        copiedCount: number
        totalDataCount: number
        fileName?: string
        csvFilePath?: string | null
        exportTime?: string
      }
      const { copiedCount, totalDataCount, fileName, csvFilePath, exportTime } = data

      // 设置摘要信息（仕様: copiedCount, totalDataCount, fileName, exportTime）
      exportProgressSummary.value = {
        copiedCount,
        totalDataCount,
        fileName: fileName ?? undefined,
        csvFilePath: csvFilePath ?? undefined,
        exportTime,
      }

      // 添加成功详情
      addProgressDetail(
        `エクスポート完了: ${copiedCount}件の新規データ、合計${totalDataCount}件`,
        'success',
        totalDataCount,
      )
    } catch (apiError: any) {
      // 清除进度更新定时器
      clearInterval(progressInterval)

      // 更新进度状态为错误
      exportProgressPercentage.value = Math.min(exportProgressPercentage.value, 90)
      exportProgressStatus.value = 'exception'
      updateProgressMessage('エクスポート処理中にエラーが発生しました')

      // 处理超时错误 - 即使超时也提示用户可能仍在处理中
      if (apiError.code === 'ECONNABORTED' || apiError.message?.includes('timeout')) {
        addProgressDetail(
          'リクエストがタイムアウトしましたが、サーバー側で処理が継続している可能性があります',
          'error',
        )
        updateProgressMessage(
          'リクエストがタイムアウトしました。\nただし、サーバー側で処理が継続している可能性があります。\nしばらく待ってから、サーバーのログまたは出力フォルダを確認してください。',
        )
        // 不抛出错误，让用户知道可能仍在处理
        exportProgressStatus.value = 'warning'
      } else {
        addProgressDetail(`エラーが発生しました: ${apiError.message || '不明なエラー'}`, 'error')
        throw apiError // 重新抛出其他错误
      }
    } finally {
      exportLoading.value = false
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('ピッキングCSV导出エラー:', error)

      // 如果对话框还没显示，显示它
      if (!exportProgressVisible.value) {
        exportProgressVisible.value = true
        exportProgressPercentage.value = 0
        exportProgressStatus.value = 'exception'
      }

      // 根据错误类型显示不同的消息
      let errorMessage = 'エクスポート処理中にエラーが発生しました'
      if (error.message) {
        if (error.message.includes('timeout') || error.message.includes('タイムアウト')) {
          errorMessage =
            'エクスポート処理がタイムアウトしました。データ量が多い場合は時間がかかる場合があります。'
        } else if (error.message.includes('Network') || error.message.includes('ネットワーク')) {
          errorMessage = 'ネットワークエラーが発生しました。接続を確認してください。'
        } else {
          errorMessage = `エクスポート処理中にエラーが発生しました: ${error.message}`
        }
      }

      updateProgressMessage(errorMessage)
      addProgressDetail(errorMessage, 'error')
    } else {
      // 用户取消，关闭对话框
      exportProgressVisible.value = false
    }
  } finally {
    exportLoading.value = false
  }
}

// 添加进度详情
function addProgressDetail(
  message: string,
  status: 'success' | 'processing' | 'error' | 'info',
  count?: number,
): void {
  exportProgressDetails.value.push({ message, status, count })
}

// 更新进度详情
function updateProgressDetail(
  oldMessage: string,
  newMessage: string,
  status: 'success' | 'processing' | 'error' | 'info',
  count?: number,
): void {
  const index = exportProgressDetails.value.findIndex((d) => d.message === oldMessage)
  if (index !== -1) {
    exportProgressDetails.value[index] = { message: newMessage, status, count }
  }
}

// 更新进度消息
function updateProgressMessage(message: string): void {
  exportProgressMessage.value = message
}

// 加载分组
async function loadDestinationGroups() {
  try {
    const response = await request.get('/api/shipping/destination-groups/destination_groups_list')
    if (Array.isArray(response)) {
      availableGroups.value = response.map((group) => ({
        ...group,
        groupName: group.group_name,
      }))
    } else {
      availableGroups.value = []
    }
  } catch (error) {
    console.error('加载分组失败:', error)
    availableGroups.value = []
  }
}
</script>

<style scoped>
/* 全局字体设置 */
.shipping-list-container,
.shipping-list-container * {
  font-family:
    'Yu Gothic', 'YuGothic', 'Hiragino Kaku Gothic ProN', 'Hiragino Kaku Gothic Pro', 'Meiryo',
    sans-serif;
}

.shipping-list-container {
  padding: 2px;
  max-width: 100%;
  margin: 0 auto;
  background: #f5f7fa;
  min-height: 100vh;
  position: relative;
  overflow: hidden;
  font-family:
    '游ゴシック', 'Yu Gothic', 'YuGothic', 'Hiragino Kaku Gothic ProN', 'Hiragino Kaku Gothic Pro',
    'Meiryo', sans-serif;
}

.shipping-list-container::before {
  display: none;
}

@keyframes shippingBackgroundShift {
  0%,
  100% {
    opacity: 0.8;
    transform: scale(1) rotate(0deg);
  }

  25% {
    opacity: 1;
    transform: scale(1.05) rotate(90deg);
  }

  50% {
    opacity: 0.9;
    transform: scale(0.95) rotate(180deg);
  }

  75% {
    opacity: 1;
    transform: scale(1.02) rotate(270deg);
  }
}

.page-header {
  margin-bottom: 4px;
  background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
  border-radius: 12px;
  padding: 2px 16px;
  box-shadow: 0 2px 8px rgba(30, 58, 138, 0.15);
  color: white;
  position: relative;
  overflow: hidden;
  opacity: 0;
  transform: translateY(-30px);
  animation: slideInFromTop 0.6s ease-out 0.1s forwards;
  border: none;
}

.page-header.page-loaded {
  opacity: 1;
  transform: translateY(0);
}

@keyframes slideInFromTop {
  from {
    opacity: 0;
    transform: translateY(-30px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.page-header::before {
  display: none;
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0px) rotate(0deg);
  }

  50% {
    transform: translateY(-20px) rotate(180deg);
  }
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  z-index: 1;
}

.title-section {
  flex: 1;
}

.title {
  display: flex;
  align-items: center;
  gap: 10px;
  color: white;
  margin-bottom: 4px;
  font-size: 20px;
  font-weight: 600;
  text-shadow: none;
}

.title-icon {
  background: rgba(255, 255, 255, 0.15);
  padding: 4px;
  border-radius: 8px;
  font-size: 18px;
  backdrop-filter: blur(10px);
}

.title-text {
  font-weight: 700;
  letter-spacing: 1px;
}

.title-badge {
  background: rgba(16, 185, 129, 0.9);
  color: white;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  box-shadow: 0 2px 6px rgba(16, 185, 129, 0.3);
  border: none;
}

@keyframes shippingPulse {
  0% {
    transform: scale(1);
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
  }

  50% {
    transform: scale(1.08);
    box-shadow: 0 6px 16px rgba(16, 185, 129, 0.6);
  }

  100% {
    transform: scale(1);
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
  }
}

.badge-text {
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.subtitle {
  color: rgba(255, 255, 255, 0.85);
  font-size: 12px;
  margin: 0;
  font-weight: 400;
}

.header-decoration {
  display: flex;
  gap: 8px;
}

.decoration-circle {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  animation: bounce 2s infinite;
}

.circle-1 {
  background: rgba(255, 255, 255, 0.6);
  animation-delay: 0s;
}

.circle-2 {
  background: rgba(255, 255, 255, 0.4);
  animation-delay: 0.2s;
}

.circle-3 {
  background: rgba(255, 255, 255, 0.2);
  animation-delay: 0.4s;
}

@keyframes bounce {
  0%,
  20%,
  50%,
  80%,
  100% {
    transform: translateY(0);
  }

  40% {
    transform: translateY(-10px);
  }

  60% {
    transform: translateY(-5px);
  }
}

.modern-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  transition: all 0.2s ease;
  opacity: 0;
  transform: translateY(20px);
  animation: slideInFromBottom 0.5s ease-out forwards;
}

.filter-card {
  margin-bottom: 6px;
  animation-delay: 0.2s;
}

.table-card {
  animation-delay: 0.3s;
}

.modern-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #d1d5db;
}

@keyframes slideInFromBottom {
  from {
    opacity: 0;
    transform: translateY(30px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.filter-card {
  margin-bottom: 8px;
}

.filter-card :deep(.el-card__body) {
  padding: 6px 12px !important;
}

.filter-card :deep(.el-card__header) {
  padding: 6px 12px !important;
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0;
}

.filter-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #2c3e50;
  font-size: 14px;
}

.filter-icon {
  font-size: 16px;
  color: #3498db;
}

.filter-row {
  margin-bottom: 0;
  width: 100%;
}

.filter-actions {
  display: flex;
  justify-content: flex-end;
  align-items: flex-end;
  height: 100%;
  gap: 12px;
}

.filter-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 0;
  margin: 0;
}

.modern-form-item {
  margin-bottom: 10px;
}

.modern-form-item :deep(.el-form-item__label) {
  color: #2c3e50;
  font-weight: 600;
  font-size: 14px;
}

.modern-input,
.modern-select,
.modern-date-picker {
  border-radius: 8px;
  transition: all 0.3s ease;
}

.modern-input:hover,
.modern-select:hover,
.modern-date-picker:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(52, 152, 219, 0.2);
}

.search-button {
  background: #2563eb;
  border: none;
  border-radius: 6px;
  padding: 4px 8px;
  font-weight: 600;
  font-size: 13px;
  letter-spacing: 0;
  text-shadow: none;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(37, 99, 235, 0.2);
  border: none;
  min-height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.search-button:hover {
  background: #1d4ed8;
  box-shadow: 0 2px 6px rgba(37, 99, 235, 0.3);
}

.search-button.searching {
  animation: searchPulse 1.5s infinite;
  position: relative;
}

.search-button.searching::after {
  content: '';
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  background: linear-gradient(45deg, #3498db, #2980b9, #3498db);
  border-radius: 10px;
  z-index: -1;
  animation: searchGlow 2s linear infinite;
}

@keyframes searchPulse {
  0%,
  100% {
    transform: scale(1);
  }

  50% {
    transform: scale(1.02);
  }
}

@keyframes searchGlow {
  0% {
    background-position: 0% 50%;
  }

  50% {
    background-position: 100% 50%;
  }

  100% {
    background-position: 0% 50%;
  }
}

.reset-button {
  background: #6b7280;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 4px 8px;
  font-weight: 600;
  font-size: 13px;
  letter-spacing: 0;
  text-shadow: none;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(107, 114, 128, 0.2);
  border: none;
  min-height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.reset-button:hover {
  background: #4b5563;
  box-shadow: 0 2px 6px rgba(107, 114, 128, 0.3);
}

.table-card {
  margin-bottom: 8px;
}

.table-card :deep(.el-card__header) {
  padding: 4px 12px !important;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 2px 0;
  border-bottom: none;
}

.table-title {
  display: flex;
  align-items: center;
  gap: 4px;
  font-weight: 600;
  color: #1f2937;
  font-size: 14px;
}

.table-icon {
  font-size: 18px;
  color: #3498db;
  background: rgba(52, 152, 219, 0.1);
  padding: 4px;
  border-radius: 4px;
}

.count-badge {
  background: #3b82f6;
  color: white;
  padding: 4px 10px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  box-shadow: 0 1px 3px rgba(59, 130, 246, 0.2);
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
  border: none;
  min-width: 50px;
  justify-content: center;
}

.count-icon {
  font-size: 10px;
  opacity: 0.8;
}

@keyframes countUpdate {
  0% {
    transform: scale(1);
  }

  50% {
    transform: scale(1.1);
    background: linear-gradient(135deg, #27ae60, #2ecc71);
  }

  100% {
    transform: scale(1);
  }
}

.count-badge::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.6s;
}

.count-badge:hover::before {
  left: 100%;
}

.count-badge.animate-count {
  animation: countUpdate 0.8s ease-out;
}

.selected-badge {
  background: #f59e0b;
  color: white;
  padding: 4px 10px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  box-shadow: 0 1px 3px rgba(245, 158, 11, 0.2);
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
  border: none;
  min-width: 70px;
  justify-content: center;
}

.selected-badge::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.6s;
}

.selected-badge:hover::before {
  left: 100%;
}

.selected-icon {
  font-size: 10px;
  opacity: 0.8;
}

@keyframes selectedPulse {
  0% {
    transform: scale(1);
    box-shadow: 0 4px 12px rgba(243, 156, 18, 0.3);
  }

  50% {
    transform: scale(1.05);
    box-shadow: 0 6px 16px rgba(243, 156, 18, 0.5);
  }

  100% {
    transform: scale(1);
    box-shadow: 0 4px 12px rgba(243, 156, 18, 0.3);
  }
}

.header-buttons {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

/* 操作按钮行（筛选区域下方单独一行，同行居中） */
.action-buttons-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 4px;
  padding: 2px 0;
}

.action-button {
  border-radius: 6px;
  padding: 4px 20px;
  font-weight: 600;
  font-size: 13px;
  letter-spacing: 0;
  text-shadow: none;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
  min-height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  color: #000000 !important;
}

.action-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.action-button :deep(.el-icon) {
  color: #000000 !important;
}

.action-button :deep(span) {
  color: #000000 !important;
}

.action-button:hover::before {
  left: 100%;
}

.action-button:hover {
  opacity: 0.9;
}

.create-button {
  background: #10b981;
  border: none;
  box-shadow: 0 1px 3px rgba(16, 185, 129, 0.2);
}

.create-button:hover {
  background: #059669;
  box-shadow: 0 2px 6px rgba(16, 185, 129, 0.3);
}

.print-button {
  background: #f59e0b;
  border: none;
  box-shadow: 0 1px 3px rgba(245, 158, 11, 0.2);
  position: relative;
}

.print-button:hover {
  background: #d97706;
  box-shadow: 0 2px 6px rgba(245, 158, 11, 0.3);
}

.delete-button {
  background: #ef4444;
  border: none;
  box-shadow: 0 1px 3px rgba(239, 68, 68, 0.2);
  position: relative;
}

.delete-button:hover:not(:disabled) {
  background: #dc2626;
  box-shadow: 0 2px 6px rgba(239, 68, 68, 0.3);
}

.delete-button:disabled {
  background: #fca5a5;
  cursor: not-allowed;
  opacity: 0.6;
}

.button-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: #ef4444;
  color: white;
  border-radius: 50%;
  min-width: 18px;
  height: 18px;
  font-size: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  border: 2px solid white;
  box-shadow: 0 1px 4px rgba(239, 68, 68, 0.3);
  padding: 0 3px;
  z-index: 10;
}

.setting-button {
  background: #8b5cf6;
  border: none;
  box-shadow: 0 1px 3px rgba(139, 92, 246, 0.2);
}

.setting-button:hover {
  background: #7c3aed;
  box-shadow: 0 2px 6px rgba(139, 92, 246, 0.3);
}

.export-button {
  background: #06b6d4;
  border: none;
  box-shadow: 0 1px 3px rgba(6, 182, 212, 0.2);
}

.export-button:hover {
  background: #0891b2;
  box-shadow: 0 2px 6px rgba(6, 182, 212, 0.3);
}

.unpicked-button {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  border: none;
  box-shadow: 0 4px 16px rgba(245, 158, 11, 0.3);
  border: 2px solid rgba(255, 255, 255, 0.1);
}

.unpicked-button:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(245, 158, 11, 0.5);
}

.table-wrapper {
  border-radius: 12px;
  overflow: hidden;
  background: white;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.modern-table {
  background: white;
}

.pagination-container {
  margin-top: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0 2px 0;
  border-top: 1px solid #e5e7eb;
}

.pagination-info {
  color: #7f8c8d;
  font-weight: 500;
}

.info-text {
  background: #f3f4f6;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
}

.modern-pagination {
  display: flex;
  justify-content: flex-end;
}

/* 表格单元格样式 */
.shipping-no-cell {
  display: flex;
  align-items: center;
  padding: 2px 0;
}

.date-cell {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  padding: 1px 0;
}

.date-icon {
  color: #3498db;
  font-size: 12px;
}

.destination-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  padding: 1px 0;
}

.location-icon {
  color: #e74c3c;
  font-size: 12px;
}

.product-name-cell {
  font-weight: 500;
  color: #2c3e50;
  font-size: 13px;
  line-height: 1.2;
  padding: 1px 0;
}

.number-cell {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  padding: 1px 0;
}

.number-value {
  font-weight: 600;
  color: #2c3e50;
  font-size: 14px;
  line-height: 1.2;
}

.number-unit {
  font-size: 10px;
  color: #7f8c8d;
  margin-top: -2px;
}

.code-tag {
  font-family:
    '游ゴシック', 'Yu Gothic', 'YuGothic', 'Hiragino Kaku Gothic ProN', 'Hiragino Kaku Gothic Pro',
    'Meiryo', sans-serif;
  font-size: 11px;
  padding: 2px 6px !important;
  height: auto !important;
  line-height: 1.2 !important;
}

.status-tag {
  display: flex;
  align-items: center;
  gap: 3px;
  font-weight: 600;
  font-size: 11px;
  padding: 3px 8px !important;
  height: auto !important;
  line-height: 1.2 !important;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}

.status-tag::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  transition: left 0.5s;
}

.status-tag:hover::before {
  left: 100%;
}

.status-tag:hover {
  transform: scale(1.05);
}

.status-icon {
  font-size: 10px;
  animation: statusPulse 2s infinite;
}

@keyframes statusPulse {
  0%,
  100% {
    opacity: 1;
  }

  50% {
    opacity: 0.7;
  }
}

.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: center;
  align-items: center;
  padding: 4px 2px;
}

.table-action-button {
  border-radius: 6px;
  font-size: 13px;
  padding: 6px 5px !important;
  height: 25px !important;
  font-weight: 700;
  letter-spacing: 0.3px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  min-width: 50px;
}

.table-action-button.icon-only {
  width: 34px !important;
  height: 34px !important;
  min-width: 34px !important;
  padding: 0 !important;
  border-radius: 50% !important;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}

.table-action-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  font-weight: 800;
}

.table-action-button.icon-only:hover {
  transform: translateY(-2px) scale(1.1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

/* Element Plus 深度样式覆盖 */
:deep(.el-table) {
  border-radius: 12px;
  overflow: hidden;
  --el-table-border-color: rgba(52, 152, 219, 0.1);
  --el-table-header-bg-color: linear-gradient(135deg, #f8f9fa, #e9ecef);
  --el-table-row-hover-bg-color: rgba(52, 152, 219, 0.05);
  --el-table-header-text-color: #2c3e50;
  font-size: 13px;
  font-family:
    '游ゴシック', 'Yu Gothic', 'YuGothic', 'Hiragino Kaku Gothic ProN', 'Hiragino Kaku Gothic Pro',
    'Meiryo', sans-serif;
}

/* 按钮字体增强 */
:deep(.el-button) {
  font-family:
    '游ゴシック', 'Yu Gothic', 'YuGothic', 'Hiragino Kaku Gothic ProN', 'Hiragino Kaku Gothic Pro',
    'Meiryo', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}

:deep(.el-button span) {
  font-weight: inherit;
  letter-spacing: inherit;
}

:deep(.el-table .cell) {
  padding: 2px 8px;
  line-height: 1.2;
}

:deep(.el-table__header) {
  background: linear-gradient(135deg, #f8f9fa, #e9ecef);
  font-weight: 600;
}

:deep(.el-table__header th) {
  border-bottom: 1px solid #d1d5db;
  color: #374151;
  font-size: calc(12px * 0.9);
  padding: 4px 0;
  height: 30px;
}

:deep(.el-table__header .cell) {
  padding: 0 8px;
  font-weight: 600;
  white-space: nowrap;
  font-size: inherit;
}

:deep(.el-table__body) {
  font-size: 13px;
}

:deep(.el-table__row) {
  cursor: pointer;
  transition: all 0.2s ease;
  animation: fadeInUp 0.4s ease-out;
  height: 32px;
}

:deep(.el-table__row td) {
  padding: 1px 0;
  border-bottom: 1px solid #e5e7eb;
}

:deep(.el-table__row:hover) {
  background: #f3f4f6;
}

:deep(.el-table__fixed-right) {
  height: auto !important;
  z-index: 3;
  overflow: hidden;
}

:deep(.el-table__fixed-right .el-table__header th),
:deep(.el-table__fixed-right .el-table__body td) {
  background: #fff !important;
}

:deep(.el-table__fixed-right .el-table__header),
:deep(.el-table__fixed-right .el-table__body) {
  overflow: hidden;
}

:deep(.el-table__fixed-right .el-table__header th .cell),
:deep(.el-table__fixed-right .el-table__body td .cell) {
  overflow: hidden;
  text-overflow: ellipsis;
}

:deep(.el-table--border .el-table__cell) {
  border-right: 1px solid rgba(52, 152, 219, 0.08);
}

:deep(.el-table__empty-block) {
  min-height: 200px;
}

:deep(.el-table__empty-text) {
  color: #909399;
  font-size: 14px;
}

/* 工具提示美化 */
:deep(.el-tooltip__popper) {
  background: linear-gradient(135deg, #2c3e50, #34495e);
  border: none;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(10px);
}

:deep(.el-tooltip__popper .el-tooltip__arrow) {
  border-top-color: #2c3e50;
}

/* 通知样式美化 */
:deep(.el-notification) {
  border-radius: 12px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.15);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

:deep(.el-notification.el-notification--success) {
  background: linear-gradient(135deg, rgba(39, 174, 96, 0.95), rgba(46, 204, 113, 0.95));
  color: white;
}

:deep(.el-notification.el-notification--info) {
  background: linear-gradient(135deg, rgba(52, 152, 219, 0.95), rgba(41, 128, 185, 0.95));
  color: white;
}

:deep(.el-notification.el-notification--error) {
  background: linear-gradient(135deg, rgba(231, 76, 60, 0.95), rgba(192, 57, 43, 0.95));
  color: white;
}

:deep(.el-table__header) {
  background: linear-gradient(135deg, #f8f9fa, #e9ecef);
  font-weight: 600;
}

:deep(.el-table__header th) {
  border-bottom: 2px solid rgba(52, 152, 219, 0.2);
  color: #2c3e50;
  font-size: calc(14px * 0.9);
}

:deep(.el-table__row) {
  cursor: pointer;
  transition: all 0.3s ease;
  animation: fadeInUp 0.6s ease-out;
}

:deep(.el-table__row:hover) {
  background: rgba(52, 152, 219, 0.05);
  transform: scale(1.001);
  box-shadow: 0 4px 12px rgba(52, 152, 219, 0.1);
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

:deep(.canceled-row) {
  background: linear-gradient(135deg, #fef0f0, #fde2e2);
  color: #f56c6c;
  text-decoration: line-through;
  opacity: 0.7;
}

:deep(.el-tag) {
  font-weight: 600;
  border-radius: 4px;
  border: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  font-size: 11px;
  padding: 2px 6px;
  height: auto;
  line-height: 1.3;
}

:deep(.el-tag--small) {
  font-size: 10px;
  padding: 1px 4px;
  height: auto;
}

:deep(.el-tag--info) {
  background-color: #909399;
  color: white;
}

:deep(.el-tag--primary) {
  background-color: #3498db;
  color: white;
}

:deep(.el-tag--success) {
  background-color: #27ae60;
  color: white;
}

:deep(.el-tag--warning) {
  background-color: #f39c12;
  color: white;
}

:deep(.el-tag--danger) {
  background-color: #e74c3c;
  color: white;
}

:deep(.el-pagination) {
  font-weight: 500;
  font-size: 12px;
}

:deep(.el-pagination .el-select .el-input__inner),
:deep(.el-pagination .el-pager li),
:deep(.el-pagination .btn-prev),
:deep(.el-pagination .btn-next) {
  font-size: 12px;
}

:deep(.el-pagination .el-pager li) {
  border-radius: 6px;
  margin: 0 2px;
  transition: all 0.3s ease;
}

:deep(.el-pagination .el-pager li:hover) {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(52, 152, 219, 0.3);
}

:deep(.el-pagination .btn-prev),
:deep(.el-pagination .btn-next) {
  border-radius: 6px;
  transition: all 0.3s ease;
}

:deep(.el-pagination .btn-prev:hover),
:deep(.el-pagination .btn-next:hover) {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(52, 152, 219, 0.3);
}

/* 自定义加载动画 */
:deep(.el-loading-mask) {
  background-color: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
}

:deep(.el-loading-spinner) {
  font-size: 28px;
}

:deep(.el-loading-spinner .circular) {
  width: 50px;
  height: 50px;
  animation: loading-rotate 2s linear infinite;
}

:deep(.el-loading-spinner .path) {
  stroke: #3498db;
  stroke-width: 3;
  stroke-dasharray: 90, 150;
  stroke-dashoffset: 0;
  stroke-linecap: round;
  animation: loading-dash 1.5s ease-in-out infinite;
}

@keyframes loading-rotate {
  100% {
    transform: rotate(360deg);
  }
}

@keyframes loading-dash {
  0% {
    stroke-dasharray: 1, 150;
    stroke-dashoffset: 0;
  }

  50% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: -35;
  }

  100% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: -124;
  }
}

/* 自定义滚动条 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #3498db, #2980b9);
  border-radius: 4px;
  transition: all 0.3s ease;
}

::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #2980b9, #21618c);
}

:deep(.el-table .cell) {
  padding-left: 12px;
  padding-right: 12px;
}

:deep(.el-table__fixed-right) {
  height: auto !important;
  z-index: 3;
  overflow: hidden;
}

:deep(.el-table__fixed-right .el-table__header th),
:deep(.el-table__fixed-right .el-table__body td) {
  background: #fff !important;
}

:deep(.el-table__fixed-right .el-table__header),
:deep(.el-table__fixed-right .el-table__body) {
  overflow: hidden;
}

:deep(.el-table__fixed-right .el-table__header th .cell),
:deep(.el-table__fixed-right .el-table__body td .cell) {
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 对话框样式 */
.modern-dialog {
  border-radius: 16px;
  overflow: hidden;
}

.modern-dialog :deep(.el-dialog) {
  border-radius: 16px;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.2);
  background: linear-gradient(135deg, #ffffff, #f8f9fa);
}

.modern-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  padding: 20px 24px;
  margin: 0;
}

.modern-dialog :deep(.el-dialog__title) {
  color: white;
  font-weight: 600;
  font-size: 18px;
}

.modern-dialog :deep(.el-dialog__headerbtn) {
  top: 20px;
  right: 20px;
}

.modern-dialog :deep(.el-dialog__close) {
  color: white;
  font-size: 18px;
}

.modern-dialog :deep(.el-dialog__body) {
  padding: 24px;
}

/* 列表示设定对話框樣式 */
.column-select-container {
  padding: 16px;
}

.column-select-description {
  margin-bottom: 20px;
  color: #2c3e50;
  font-size: 16px;
  font-weight: 500;
  text-align: center;
}

.checkbox-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.modern-checkbox {
  margin: 0;
  padding: 12px 16px;
  border-radius: 8px;
  border: 2px solid rgba(52, 152, 219, 0.1);
  transition: all 0.3s ease;
  background: white;
  cursor: pointer;
}

.modern-checkbox:hover {
  background: rgba(52, 152, 219, 0.05);
  border-color: rgba(52, 152, 219, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(52, 152, 219, 0.2);
}

.modern-checkbox :deep(.el-checkbox__input.is-checked + .el-checkbox__label) {
  color: #3498db;
  font-weight: 600;
}

.dialog-footer {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid rgba(52, 152, 219, 0.1);
}

.reset-button {
  background: linear-gradient(135deg, #909399, #7d7d7d);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(144, 147, 153, 0.3);
}

.reset-button:hover {
  background: linear-gradient(135deg, #7d7d7d, #6a6a6a);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(144, 147, 153, 0.4);
}

.confirm-button {
  background: linear-gradient(135deg, #409eff, #337ecc);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.confirm-button:hover {
  background: linear-gradient(135deg, #337ecc, #2d6db3);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(64, 158, 255, 0.4);
}

/* 紧凑筛选行样式 */
.compact-filter-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  padding: 0;
  background: transparent;
  border-radius: 0;
  margin: 0;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.filter-label {
  font-size: 12px;
  font-weight: 600;
  color: #374151;
  white-space: nowrap;
  margin: 0;
  min-width: fit-content;
}

.date-group {
  flex: 0 0 auto;
}

.destination-group {
  flex: 0 0 auto;
}

.group-controls {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
}

.status-group {
  flex: 0 0 auto;
}

.actions-group {
  flex: 0 0 auto;
  margin-left: auto;
}

/* 日期范围容器样式 */
.date-range-container {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: nowrap;
}

.date-quick-buttons {
  display: flex;
  gap: 2px;
  flex-shrink: 0;
}

.date-quick-buttons .date-btn,
.date-quick-buttons :deep(.el-button) {
  margin: 0;
}
.date-quick-buttons :deep(.el-button + .el-button) {
  margin-left: 0;
}

.date-btn {
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0;
  padding: 4px 8px;
  border-radius: 5px;
  transition: all 0.2s ease;
  border: 1px solid #d1d5db;
  background: white;
  color: #4b5563;
  min-width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.date-btn:hover {
  background: #f0f9ff;
  border-color: #3498db;
  color: #3498db;
  transform: translateY(-1px);
}

.today-btn {
  background: #2563eb;
  color: white;
  border-color: #2563eb;
  font-weight: 600;
  text-shadow: none;
  letter-spacing: 0;
}

.today-btn:hover {
  background: #1d4ed8;
  border-color: #1d4ed8;
  box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);
}

/* 紧凑按钮样式 */
.compact-btn {
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  padding: 8px 16px;
  height: 36px;
  line-height: 1;
  border-radius: 6px;
}

/* 納入先控制区域样式 */
.destination-controls {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}

.destination-controls .filter-label-inline {
  margin-left: 4px;
  margin-right: 0;
}

.destination-select-dropdown {
  flex-shrink: 0;
}

.destination-quick-buttons {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
}

.destination-quick-btn {
  padding: 4px 10px !important;
  height: 28px !important;
  font-size: 11px !important;
  font-weight: 600 !important;
  border-radius: 4px !important;
  border: 1px solid #d1d5db !important;
  background: #ffffff !important;
  color: #374151 !important;
  transition: all 0.2s ease !important;
  min-width: auto !important;
}

.destination-quick-btn:hover:not(:disabled) {
  background: #f3f4f6 !important;
  border-color: #2563eb !important;
  color: #2563eb !important;
  transform: translateY(-1px);
}

.destination-quick-btn.active {
  background: #2563eb !important;
  border-color: #2563eb !important;
  color: #ffffff !important;
  box-shadow: 0 1px 3px rgba(37, 99, 235, 0.2) !important;
}

.destination-quick-btn:disabled {
  background: #f3f4f6 !important;
  border-color: #e5e7eb !important;
  color: #9ca3af !important;
  cursor: not-allowed !important;
  opacity: 0.6 !important;
}

.destination-option {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.destination-option .destination-code {
  font-weight: 600;
  color: #374151;
  font-size: 12px;
  min-width: 60px;
}

.destination-option .destination-name {
  color: #6b7280;
  font-size: 12px;
  flex: 1;
}

.group-filter-dropdown {
  flex-shrink: 0;
}

.group-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.group-name {
  font-weight: 600;
  color: #2c3e50;
  font-size: 12px;
}

.group-count {
  font-size: 10px;
  color: #7f8c8d;
  margin-left: 8px;
}

.group-manage-button {
  display: flex;
  align-items: center;
  gap: 4px;
  background: #8b5cf6;
  color: white;
  border: none;
  border-radius: 5px;
  padding: 5px 10px;
  transition: all 0.2s ease;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0;
  text-shadow: none;
  height: 32px;
  box-shadow: 0 1px 3px rgba(139, 92, 246, 0.2);
}

.group-manage-button:hover:not(:disabled) {
  background: #7c3aed;
  box-shadow: 0 2px 6px rgba(139, 92, 246, 0.3);
}

.group-manage-button:disabled {
  background: #c0c4cc;
  color: #a8abb2;
  cursor: not-allowed;
  box-shadow: none;
}

/* 活跃分组显示区域 */
.active-groups-display {
  margin-top: 6px;
  padding: 6px 10px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  animation: slideInDown 0.3s ease-out;
}

@keyframes slideInDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.groups-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.groups-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #2c3e50;
}

.clear-groups-btn {
  font-size: 11px;
  color: #e74c3c;
  transition: all 0.3s ease;
}

.clear-groups-btn:hover {
  color: #c0392b;
  transform: scale(1.05);
}

.groups-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.group-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  background: #8b5cf6;
  color: white;
  padding: 4px 10px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
  box-shadow: 0 1px 3px rgba(139, 92, 246, 0.2);
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

.group-tag::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.group-tag:hover::before {
  left: 100%;
}

.group-tag:hover {
  background: #7c3aed;
  box-shadow: 0 2px 6px rgba(139, 92, 246, 0.3);
}

.group-name {
  font-weight: 600;
}

.group-count {
  background: rgba(255, 255, 255, 0.2);
  padding: 2px 6px;
  border-radius: 10px;
  font-size: 10px;
  font-weight: 700;
}

.remove-group-btn {
  width: 20px !important;
  height: 20px !important;
  min-width: 20px !important;
  padding: 0 !important;
  background: rgba(231, 76, 60, 0.8) !important;
  border: none !important;
  border-radius: 50% !important;
  color: white !important;
  font-size: 10px !important;
  transition: all 0.3s ease;
}

.remove-group-btn:hover {
  background: rgba(192, 57, 43, 0.9) !important;
  transform: scale(1.1);
}

/* 納入先拖拽分组选择相关样式已移至DestinationDragFilter组件 */

/* 筛选区域响应式 */
@media (max-width: 1400px) {
  .compact-filter-row {
    flex-wrap: wrap;
    gap: 10px;
  }

  .filter-group {
    flex: 1 1 auto;
    min-width: 180px;
  }

  .filter-group.destination-group {
    flex: 1 1 100%;
    min-width: 0;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .date-range-container {
    flex-wrap: wrap;
  }

  .group-controls {
    flex-wrap: wrap;
    gap: 6px;
  }

  .destination-controls {
    flex-wrap: wrap;
    gap: 6px;
  }
}

@media (max-width: 1200px) {
  .shipping-list-container {
    padding: 12px;
  }

  .page-header {
    padding: 16px;
  }

  .title {
    font-size: 22px;
  }

  .header-buttons,
  .action-buttons-row {
    flex-wrap: wrap;
    gap: 8px;
  }

  .action-button {
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.5px;
    padding: 8px 16px;
    min-height: 36px;
  }

  .compact-filter-row {
    gap: 10px;
  }

  .filter-group.destination-group {
    flex: 1 1 100%;
  }

  .destination-controls {
    flex-wrap: wrap;
    gap: 8px;
  }

  .destination-quick-buttons {
    flex-wrap: wrap;
    gap: 4px;
  }

  .group-controls {
    gap: 6px;
  }

  /* 表格列优化 */
  :deep(.el-table) {
    font-size: 12px;
  }

  :deep(.el-table .cell) {
    padding: 2px 6px;
  }
}

@media (max-width: 992px) {
  .shipping-list-container {
    padding: 8px;
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  }

  .page-header {
    padding: 12px 16px;
    margin-bottom: 8px;
  }

  .header-content {
    flex-direction: column;
    gap: 12px;
    text-align: center;
  }

  .title {
    font-size: 20px;
    justify-content: center;
  }

  .subtitle {
    font-size: 12px;
  }

  .filter-card {
    margin-bottom: 8px;
  }

  .filter-bar {
    gap: 10px;
    padding: 8px 0;
  }

  .compact-filter-row {
    gap: 12px;
    row-gap: 12px;
  }

  .filter-group.date-group {
    flex: 1 1 100%;
    min-width: 0;
  }

  .filter-group.destination-group {
    flex: 1 1 100%;
    min-width: 0;
  }

  .date-range-container {
    flex-wrap: wrap;
    gap: 8px;
  }

  .group-controls {
    flex-wrap: wrap;
    gap: 8px;
  }

  .destination-controls .filter-label-inline {
    margin-left: 0;
    width: 100%;
  }

  .header-buttons,
  .action-buttons-row {
    flex-direction: row;
    flex-wrap: wrap;
    width: 100%;
    gap: 6px;
    justify-content: center;
  }

  .action-buttons-row .action-button {
    flex: 0 0 auto;
    min-width: 120px;
    max-width: 200px;
    justify-content: center;
    font-size: 12px;
    padding: 6px 12px;
  }

  .table-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }

  .table-title {
    font-size: 14px;
  }

  .pagination-container {
    flex-direction: column;
    gap: 12px;
    align-items: center;
  }

  /* 表格横向滚动 */
  .table-wrapper {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  :deep(.el-table) {
    min-width: 800px;
  }

  /* 响应式：操作列固定右侧、不透明，表头与内容在操作列内裁剪避免重叠 */
  :deep(.el-table__fixed-right) {
    z-index: 3;
    overflow: hidden;
  }

  :deep(.el-table__fixed-right .el-table__header th),
  :deep(.el-table__fixed-right .el-table__body td) {
    background: #fff !important;
  }

  :deep(.el-table__fixed-right .el-table__header),
  :deep(.el-table__fixed-right .el-table__body) {
    overflow: hidden;
  }

  :deep(.el-table__fixed-right .el-table__header th .cell),
  :deep(.el-table__fixed-right .el-table__body td .cell) {
    overflow: hidden;
    text-overflow: ellipsis;
  }

  /* 隐藏部分列在中等屏幕 */
  :deep(.el-table__body-wrapper) {
    overflow-x: auto;
  }
}

@media (max-width: 768px) {
  .shipping-list-container {
    padding: 4px;
  }

  .page-header {
    padding: 10px 12px;
    border-radius: 10px;
    margin-bottom: 6px;
  }

  .title {
    font-size: 18px;
    gap: 8px;
  }

  .title-icon {
    padding: 6px;
    font-size: 16px;
  }

  .title-text {
    font-size: 18px;
  }

  .subtitle {
    font-size: 11px;
  }

  .filter-card {
    margin-bottom: 6px;
  }

  .filter-card :deep(.el-card__body) {
    padding: 8px 10px !important;
  }

  .filter-card :deep(.el-card__header) {
    padding: 6px 10px !important;
  }

  .filter-bar {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  /* 移动端紧凑筛选行样式 */
  .compact-filter-row {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
    padding: 10px;
  }

  .filter-group {
    flex-direction: column;
    align-items: stretch;
    gap: 6px;
    width: 100%;
  }

  .filter-group.date-group .filter-label {
    margin-bottom: 4px;
  }

  .filter-label {
    font-size: 12px;
    margin-bottom: 4px;
  }

  .filter-group.destination-group {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }

  .group-controls {
    width: 100%;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
  }

  .group-controls .group-filter-dropdown {
    flex: 1;
    min-width: 120px;
  }

  .group-controls .group-manage-button {
    flex-shrink: 0;
  }

  /* 移动端日期快捷按钮样式 */
  .date-range-container {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .modern-date-picker {
    width: 100% !important;
  }

  .date-quick-buttons {
    justify-content: space-between;
    width: 100%;
  }

  .date-btn {
    flex: 1;
    min-width: 60px;
    height: 32px;
    font-size: 12px;
    font-weight: 600;
  }

  /* 移动端納入先控制区域样式 */
  .destination-controls {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .destination-controls .filter-label-inline {
    margin-left: 0;
    margin-bottom: 4px;
  }

  .destination-select-dropdown {
    width: 100% !important;
  }

  .destination-quick-buttons {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 2px;
    width: 100%;
  }

  .destination-quick-btn {
    width: 100% !important;
    justify-content: center;
  }

  .group-filter-dropdown {
    width: 100% !important;
  }

  .group-manage-button {
    width: 100% !important;
    justify-content: center;
    height: 32px;
    font-size: 12px;
    font-weight: 600;
  }

  /* 移动端活跃分组显示 */
  .active-groups-display {
    margin-top: 6px;
    padding: 8px 10px;
  }

  .groups-header {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
  }

  .groups-title {
    font-size: 12px;
  }

  .groups-list {
    margin-top: 6px;
  }

  .group-tag {
    padding: 6px 10px;
    font-size: 11px;
  }

  .group-count {
    font-size: 9px;
  }

  .remove-group-btn {
    width: 20px !important;
    height: 20px !important;
    min-width: 20px !important;
  }

  /* 表格区域 */
  .table-card {
    margin-bottom: 6px;
  }

  .table-header {
    flex-direction: column;
    gap: 10px;
    padding: 8px 0;
  }

  .table-title {
    font-size: 14px;
  }

  .header-buttons,
  .action-buttons-row {
    flex-direction: column;
    align-items: center;
    width: 100%;
    gap: 6px;
    margin-bottom: 6px;
    padding: 2px 0;
  }

  .action-buttons-row .action-button {
    width: 100%;
    max-width: 280px;
    justify-content: center;
    font-size: 12px;
    padding: 6px 12px;
    min-height: 34px;
  }

  .table-wrapper {
    border-radius: 8px;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  :deep(.el-table) {
    min-width: 900px;
    font-size: 11px;
  }

  :deep(.el-table .cell) {
    padding: 2px 4px;
    font-size: 11px;
  }

  :deep(.el-table__header th) {
    font-size: calc(11px * 0.9);
    padding: 4px 0;
    height: 28px;
  }

  :deep(.el-table__row) {
    height: 30px;
  }

  :deep(.el-table__row td) {
    padding: 1px 0;
  }

  .action-buttons {
    flex-direction: row;
    gap: 4px;
    flex-wrap: wrap;
  }

  .table-action-button {
    min-width: 32px;
    width: auto;
    justify-content: center;
  }

  .pagination-container {
    flex-direction: column;
    gap: 10px;
    padding: 8px 0 2px 0;
  }

  :deep(.el-pagination) {
    flex-wrap: wrap;
    justify-content: center;
    font-size: 12px;
  }

  :deep(.el-pagination .el-pager li),
  :deep(.el-pagination .btn-prev),
  :deep(.el-pagination .btn-next) {
    min-width: 28px;
    height: 28px;
    line-height: 28px;
    font-size: 12px;
  }

  /* 对话框 */
  .checkbox-grid {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .dialog-footer {
    flex-direction: column;
    gap: 10px;
  }

  .reset-button,
  .confirm-button {
    width: 100%;
    padding: 10px;
  }
}

@media (max-width: 480px) {
  .shipping-list-container {
    padding: 2px;
    min-height: auto;
  }

  .page-header {
    padding: 8px 10px;
    margin-bottom: 4px;
    border-radius: 8px;
  }

  .title {
    font-size: 16px;
    flex-direction: row;
    gap: 6px;
    text-align: left;
    flex-wrap: wrap;
  }

  .title-icon {
    padding: 4px;
    font-size: 14px;
  }

  .title-text {
    font-size: 16px;
  }

  .title-badge {
    padding: 2px 8px;
    font-size: 10px;
  }

  .subtitle {
    font-size: 10px;
    margin-top: 2px;
  }

  .modern-card {
    border-radius: 8px;
    margin-bottom: 4px;
  }

  .filter-card {
    margin-bottom: 4px;
  }

  .filter-card :deep(.el-card__body) {
    padding: 6px 8px !important;
  }

  .filter-card :deep(.el-card__header) {
    padding: 4px 8px !important;
  }

  .filter-header {
    flex-direction: row;
    gap: 8px;
    align-items: center;
  }

  .filter-title {
    font-size: 12px;
  }

  .filter-icon {
    font-size: 14px;
  }

  /* 超小屏幕的紧凑筛选行样式 */
  .compact-filter-row {
    gap: 8px;
    padding: 8px;
  }

  .filter-group {
    gap: 4px;
  }

  .filter-label {
    font-size: 11px;
    margin-bottom: 3px;
  }

  .date-range-container {
    gap: 4px;
  }

  .modern-date-picker {
    width: 100% !important;
  }

  .date-quick-buttons {
    gap: 0;
  }

  .date-btn {
    min-width: 50px;
    height: 30px;
    padding: 3px 6px;
    font-size: 11px;
    font-weight: 600;
  }

  .filter-group.destination-group {
    gap: 8px;
  }

  .group-controls {
    gap: 6px;
    flex-wrap: wrap;
  }

  .destination-controls {
    gap: 6px;
  }

  .destination-quick-buttons {
    grid-template-columns: repeat(2, 1fr);
    gap: 2px;
  }

  .destination-quick-btn {
    height: 26px !important;
    font-size: 10px !important;
    padding: 3px 8px !important;
  }

  .group-manage-button {
    height: 30px;
    font-size: 11px;
    padding: 4px 8px;
  }

  .search-button,
  .reset-button {
    height: 30px;
    padding: 6px 10px;
    font-size: 12px;
  }

  .compact-btn {
    font-size: 12px;
    font-weight: 600;
    padding: 6px 10px;
    height: 30px;
  }

  /* 表格区域 */
  .table-card {
    margin-bottom: 4px;
  }

  .table-header {
    padding: 6px 0;
    gap: 8px;
  }

  .table-title {
    font-size: 13px;
  }

  .count-badge,
  .selected-badge {
    padding: 2px 6px;
    font-size: 10px;
    min-width: auto;
  }

  .header-buttons,
  .action-buttons-row {
    gap: 4px;
  }

  .action-buttons-row .action-button {
    font-size: 11px;
    font-weight: 600;
    padding: 5px 10px;
    min-height: 32px;
    gap: 3px;
  }

  .button-badge {
    min-width: 16px;
    height: 16px;
    font-size: 9px;
    top: -3px;
    right: -3px;
  }

  .table-wrapper {
    border-radius: 6px;
  }

  :deep(.el-table) {
    min-width: 800px;
    font-size: 10px;
  }

  :deep(.el-table .cell) {
    padding: 1px 3px;
    font-size: 10px;
  }

  :deep(.el-table__header th) {
    font-size: calc(10px * 0.9);
    padding: 3px 0;
    height: 26px;
  }

  :deep(.el-table__header .cell) {
    padding: 0 4px;
  }

  :deep(.el-table__row) {
    height: 28px;
  }

  :deep(.el-table__row td) {
    padding: 1px 0;
  }

  .action-buttons {
    gap: 3px;
  }

  .table-action-button.icon-only {
    width: 30px !important;
    height: 30px !important;
    min-width: 30px !important;
    font-size: 14px;
  }

  .pagination-container {
    padding: 6px 0 2px 0;
    gap: 8px;
  }

  .pagination-info {
    font-size: 11px;
  }

  .info-text {
    padding: 3px 8px;
    font-size: 11px;
  }

  :deep(.el-pagination) {
    font-size: 11px;
  }

  :deep(.el-pagination .el-pager li),
  :deep(.el-pagination .btn-prev),
  :deep(.el-pagination .btn-next) {
    min-width: 26px;
    height: 26px;
    line-height: 26px;
    font-size: 11px;
    margin: 0 1px;
  }

  /* 对话框 */
  .column-select-container {
    padding: 12px;
  }

  .column-select-description {
    font-size: 14px;
    margin-bottom: 12px;
  }

  .checkbox-grid {
    gap: 8px;
  }

  .modern-checkbox {
    padding: 8px 12px;
    font-size: 12px;
  }

  .dialog-footer {
    gap: 8px;
    margin-top: 16px;
    padding-top: 16px;
  }

  .reset-button,
  .confirm-button {
    padding: 8px 16px;
    font-size: 12px;
  }
}

/* 超小屏幕（小于360px） */
@media (max-width: 360px) {
  .shipping-list-container {
    padding: 2px;
  }

  .page-header {
    padding: 6px 8px;
  }

  .title {
    font-size: 14px;
  }

  .title-text {
    font-size: 14px;
  }

  .subtitle {
    font-size: 9px;
  }

  .filter-card :deep(.el-card__body) {
    padding: 4px 6px !important;
  }

  .filter-card :deep(.el-card__header) {
    padding: 3px 6px !important;
  }

  .compact-filter-row {
    padding: 6px;
    gap: 8px;
  }

  .filter-group.destination-group {
    gap: 6px;
  }

  .group-controls {
    gap: 4px;
  }

  .destination-controls {
    gap: 4px;
  }

  .date-btn {
    min-width: 45px;
    height: 28px;
    font-size: 10px;
  }

  .destination-quick-btn {
    height: 24px !important;
    font-size: 9px !important;
    padding: 2px 6px !important;
  }

  .action-buttons-row .action-button {
    font-size: 10px;
    padding: 4px 8px;
    min-height: 30px;
  }

  :deep(.el-table) {
    min-width: 700px;
    font-size: 9px;
  }

  :deep(.el-table .cell) {
    padding: 1px 2px;
    font-size: 9px;
  }

  :deep(.el-table__header th) {
    font-size: calc(9px * 0.9);
    height: 24px;
  }

  :deep(.el-table__row) {
    height: 26px;
  }
}

/* 编辑确认对话框样式 */
:deep(.edit-confirm-dialog) {
  .el-message-box__content {
    text-align: left;
    white-space: pre-line;
  }

  .el-message-box__message {
    margin: 0;
    line-height: 1.6;
  }
}

/* --------------------------- */
/* 统一検索条件卡片控件高度 */
/* --------------------------- */
.compact-filter-row :deep(.el-input__wrapper),
.compact-filter-row :deep(.el-date-editor),
.compact-filter-row :deep(.el-select .el-input__wrapper),
.compact-filter-row .date-btn,
.compact-filter-row .destination-select-button,
.compact-filter-row .group-filter-dropdown .el-input__wrapper,
.compact-filter-row .group-manage-button,
.compact-filter-row .search-button,
.compact-filter-row .reset-button,
.compact-filter-row .compact-btn {
  height: 32px !important;
  line-height: 32px !important;
}

.compact-filter-row .search-button,
.compact-filter-row .reset-button {
  min-height: 32px !important;
  padding: 5px 12px !important;
}

.modern-input,
.modern-select,
.modern-date-picker {
  border-radius: 8px;
  transition: all 0.3s ease;
}

.modern-input:hover,
.modern-select:hover,
.modern-date-picker:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(52, 152, 219, 0.2);
}

.filter-card :deep(.el-input__wrapper),
.filter-card :deep(.el-select__wrapper) {
  background-color: #ffffff;
  border-radius: 8px !important;
  border: 1px solid #dcdfe6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.filter-card :deep(.el-input__wrapper:hover),
.filter-card :deep(.el-select__wrapper:hover) {
  border-color: #3498db;
}

.filter-card :deep(.el-input__wrapper.is-focus),
.filter-card :deep(.el-select__wrapper.is-focused) {
  border-color: #3498db;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.2);
}

/* ピッキング出力确认对话框样式 */
.export-confirm-dialog :deep(.el-dialog) {
  border-radius: 24px;
  box-shadow:
    0 25px 70px rgba(0, 0, 0, 0.25),
    0 0 0 1px rgba(6, 182, 212, 0.1);
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  overflow: hidden;
  border: none;
  position: relative;
}

.export-confirm-dialog :deep(.el-dialog)::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #06b6d4 0%, #0891b2 50%, #0e7490 100%);
  z-index: 1;
}

.export-confirm-dialog :deep(.el-dialog__header) {
  display: none;
}

.export-confirm-dialog :deep(.el-dialog__body) {
  padding: 0;
}

.export-confirm-dialog :deep(.el-dialog__footer) {
  padding: 12px 20px;
  background: #f9fafb;
  border-top: 1px solid #e5e7eb;
}

.export-confirm-content {
  padding: 24px 24px 20px;
  text-align: center;
  position: relative;
}

.confirm-icon-wrapper {
  margin-bottom: 16px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.confirm-icon-circle {
  width: 70px;
  height: 70px;
  border-radius: 50%;
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 50%, #0e7490 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    0 8px 20px rgba(6, 182, 212, 0.3),
    0 0 0 4px rgba(6, 182, 212, 0.1);
  position: relative;
  animation: iconPulse 2s ease-in-out infinite;
  transition: all 0.3s ease;
}

.confirm-icon-circle::before {
  content: '';
  position: absolute;
  width: 85px;
  height: 85px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(8, 145, 178, 0.2));
  animation: iconRipple 2s ease-out infinite;
}

@keyframes iconPulse {
  0%,
  100% {
    transform: scale(1);
    box-shadow: 0 8px 24px rgba(6, 182, 212, 0.3);
  }
  50% {
    transform: scale(1.05);
    box-shadow: 0 12px 32px rgba(6, 182, 212, 0.4);
  }
}

@keyframes iconRipple {
  0% {
    transform: scale(0.8);
    opacity: 1;
  }
  100% {
    transform: scale(1.2);
    opacity: 0;
  }
}

.confirm-icon {
  font-size: 32px;
  color: white;
  z-index: 1;
  position: relative;
}

.confirm-title {
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 12px;
  letter-spacing: 0.3px;
  animation: titleFadeIn 0.6s ease-out;
}

@keyframes titleFadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.confirm-message {
  margin-bottom: 18px;
  text-align: center;
  animation: messageFadeIn 0.8s ease-out;
}

@keyframes messageFadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-main {
  font-size: 14px;
  color: #374151;
  line-height: 1.5;
  margin: 0 0 8px 0;
  font-weight: 500;
}

.message-sub {
  font-size: 12px;
  color: #6b7280;
  line-height: 1.4;
  margin: 0;
  font-style: italic;
}

.confirm-features {
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
  border-radius: 12px;
  padding: 14px 16px;
  margin-top: 16px;
  border: 2px solid rgba(16, 185, 129, 0.25);
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.1);
  position: relative;
  overflow: hidden;
  animation: featuresFadeIn 1s ease-out;
}

@keyframes featuresFadeIn {
  from {
    opacity: 0;
    transform: translateY(15px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.confirm-features::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #10b981 0%, #059669 100%);
}

.feature-item {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 8px;
  padding: 6px 0;
  font-size: 13px;
  color: #374151;
  font-weight: 600;
  transition: all 0.2s ease;
  border-radius: 6px;
  padding-left: 6px;
  margin: 0 -6px;
}

.feature-item:hover {
  background: rgba(16, 185, 129, 0.05);
  transform: translateX(4px);
}

.feature-item:not(:last-child) {
  border-bottom: 1px solid rgba(16, 185, 129, 0.1);
}

.feature-icon {
  font-size: 16px;
  color: #10b981;
  font-weight: bold;
  flex-shrink: 0;
}

.confirm-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  width: 100%;
}

.confirm-footer .cancel-button {
  background: #f3f4f6;
  color: #6b7280;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 8px 18px;
  font-weight: 600;
  font-size: 13px;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 5px;
}

.confirm-footer .cancel-button:hover {
  background: #e5e7eb;
  color: #374151;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.confirm-footer .confirm-button {
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  padding: 8px 24px;
  font-weight: 700;
  font-size: 14px;
  transition: all 0.3s ease;
  box-shadow: 0 3px 12px rgba(6, 182, 212, 0.3);
  display: flex;
  align-items: center;
  gap: 6px;
  letter-spacing: 0.3px;
}

.confirm-footer .confirm-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #0891b2 0%, #0e7490 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(6, 182, 212, 0.4);
}

.confirm-footer .confirm-button:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(6, 182, 212, 0.3);
}

.confirm-footer .confirm-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .export-confirm-dialog :deep(.el-dialog) {
    width: 90% !important;
    margin: 5vh auto;
  }

  .export-confirm-content {
    padding: 32px 24px 24px;
  }

  .confirm-icon-circle {
    width: 80px;
    height: 80px;
  }

  .confirm-icon {
    font-size: 40px;
  }

  .confirm-title {
    font-size: 20px;
  }

  .message-main {
    font-size: 15px;
  }

  .message-sub {
    font-size: 13px;
  }

  .confirm-features {
    padding: 16px;
  }

  .feature-item {
    font-size: 13px;
    padding: 8px 0;
  }

  .confirm-footer {
    flex-direction: column;
  }

  .confirm-footer .cancel-button,
  .confirm-footer .confirm-button {
    width: 100%;
    justify-content: center;
  }
}

/* ピッキング出力进度对话框样式 */
.export-progress-dialog :deep(.el-dialog) {
  border-radius: 16px;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.2);
  background: linear-gradient(135deg, #ffffff, #f8f9fa);
}

.export-progress-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #06b6d4, #0891b2);
  color: white;
  padding: 12px 20px;
  margin: 0;
  border-radius: 16px 16px 0 0;
}

.progress-dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.progress-dialog-title {
  color: rgb(2, 187, 33);
  font-weight: 600;
  font-size: 16px;
  flex: 1;
}

.progress-close-button {
  color: rgb(39, 11, 11) !important;
  background: rgba(255, 255, 255, 0.1) !important;
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
  transition: all 0.3s ease;
  width: 28px;
  height: 28px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.progress-close-button:hover {
  background: rgba(255, 255, 255, 0.2) !important;
  border-color: rgba(255, 255, 255, 0.3) !important;
  transform: scale(1.1);
}

.progress-close-button :deep(.el-icon) {
  font-size: 16px;
  color: rgb(255, 1, 1);
}

.export-progress-dialog :deep(.el-dialog__title) {
  display: none;
}

.export-progress-dialog :deep(.el-dialog__body) {
  padding: 18px 20px;
}

.export-progress-content {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.progress-status {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: #f3f4f6;
  border-radius: 6px;
  border-left: 3px solid #06b6d4;
}

.status-icon {
  font-size: 20px;
  color: #06b6d4;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.status-icon.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.status-icon.success {
  color: #10b981;
}

.status-icon.error {
  color: #ef4444;
}

.status-text {
  font-size: 14px;
  font-weight: 600;
  color: #2c3e50;
  flex: 1;
  line-height: 1.4;
}

.progress-bar-container {
  margin: 4px 0;
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

.progress-details {
  margin-top: 4px;
}

.details-title {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid #e5e7eb;
}

.details-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 160px;
  overflow-y: auto;
  padding-right: 4px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: #f9fafb;
  border-radius: 5px;
  border-left: 2px solid #d1d5db;
  transition: all 0.2s ease;
}

.detail-item:hover {
  background: #f3f4f6;
  transform: translateX(2px);
}

.detail-icon {
  font-size: 14px;
  flex-shrink: 0;
}

.detail-item:has(.detail-icon.success) {
  border-left-color: #10b981;
}

.detail-item:has(.detail-icon.error) {
  border-left-color: #ef4444;
}

.detail-item:has(.detail-icon.processing) {
  border-left-color: #06b6d4;
}

.detail-icon.success {
  color: #10b981;
}

.detail-icon.error {
  color: #ef4444;
}

.detail-icon.processing {
  color: #06b6d4;
  animation: spin 1s linear infinite;
}

.detail-icon.info {
  color: #6b7280;
}

.detail-text {
  font-size: 12px;
  color: #374151;
  flex: 1;
  line-height: 1.3;
}

.detail-count {
  font-size: 11px;
  font-weight: 600;
  color: #06b6d4;
  background: rgba(6, 182, 212, 0.1);
  padding: 2px 6px;
  border-radius: 10px;
}

.progress-summary {
  margin-top: 8px;
  padding: 12px 14px;
  background: linear-gradient(135deg, #f0fdf4, #dcfce7);
  border-radius: 8px;
  border: 2px solid #10b981;
}

.summary-title {
  font-size: 13px;
  font-weight: 700;
  color: #059669;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 5px;
}

.summary-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 0;
  border-bottom: 1px solid rgba(16, 185, 129, 0.2);
}

.summary-item:last-child {
  border-bottom: none;
}

.summary-label {
  font-size: 12px;
  font-weight: 600;
  color: #374151;
}

.summary-value {
  font-size: 12px;
  font-weight: 700;
  color: #059669;
  background: white;
  padding: 3px 10px;
  border-radius: 5px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

/* 滚动条样式 */
.details-list::-webkit-scrollbar {
  width: 6px;
}

.details-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.details-list::-webkit-scrollbar-thumb {
  background: #06b6d4;
  border-radius: 3px;
}

.details-list::-webkit-scrollbar-thumb:hover {
  background: #0891b2;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .export-progress-dialog :deep(.el-dialog) {
    width: 90% !important;
    margin: 5vh auto;
  }

  .export-progress-dialog :deep(.el-dialog__body) {
    padding: 16px;
  }

  .progress-status {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .status-text {
    font-size: 14px;
  }

  .details-list {
    max-height: 150px;
  }

  .summary-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}
</style>
