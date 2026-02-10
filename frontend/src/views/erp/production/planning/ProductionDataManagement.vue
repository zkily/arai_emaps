<template>
  <div class="production-data-management">
    <div class="page-header-row">
      <div class="title-group">
        <h1 class="page-title">生産データ管理</h1>
        <el-tag type="info" size="small" class="record-count">
          {{ total.toLocaleString() }} 件
        </el-tag>
      </div>
      <div class="header-actions">
        <el-dropdown
          trigger="click"
          placement="bottom-start"
          :disabled="generating || updatingCarryOver || updatingOrder || updatingAll"
          class="others-dropdown"
        >
          <el-button
            size="small"
            :icon="MoreFilled"
            :loading="generating || updatingCarryOver || updatingOrder || updatingAll || updatingFromOrderDaily"
            class="modern-btn others-btn"
          >
            その他
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
                @click="handleUpdateFromOrderDaily"
                :disabled="updatingFromOrderDaily"
                class="dropdown-item update-order-item"
              >
                <el-icon><Refresh /></el-icon>
                <span>受注データ更新</span>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
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
              width="80"
              fixed="left"
              align="center"
            />
            <el-table-column
              v-if="activeTableTab === 'custom' ? visibleColumns.date : true"
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
              v-if="activeTableTab === 'custom' && visibleColumns.day_of_week"
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
              v-if="activeTableTab === 'custom' && visibleColumns.route_cd"
              prop="route_cd"
              label="工程グループ"
              width="120"
              fixed="left"
              align="center"
            />
            <el-table-column
              v-if="activeTableTab === 'custom' && visibleColumns.product_cd"
              prop="product_cd"
              label="製品CD"
              width="70"
              fixed="left"
              align="center"
            />
            <el-table-column
              v-if="activeTableTab === 'custom' ? visibleColumns.product_name : true"
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
            <el-table-column
              v-if="activeTableTab === 'custom' && visibleColumns.order_quantity"
              prop="order_quantity"
              label="受注数"
              width="70"
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
              width="70"
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
                    {{ row[col.prop] != null && row[col.prop] !== 0 ? Number(row[col.prop]).toLocaleString() : '' }}
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
          <span class="detail-label">進捗:</span>
          <span class="detail-value">{{ Math.round(progressPercentage) }}%</span>
        </div>
      </div>
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
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, Setting, Printer, MoreFilled, ArrowDown, DocumentAdd, InfoFilled, Loading } from '@element-plus/icons-vue'
import { getProductionSummarysList, getProductionSummarysProducts, generateProductionSummarys, updateProductionSummarysFromOrderDaily } from '@/api/database'
import jaLocale from 'element-plus/es/locale/lang/ja'

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

// データ生成
const generating = ref(false)
const updatingFromOrderDaily = ref(false)
const updatingCarryOver = ref(false)
const updatingOrder = ref(false)
const updatingAll = ref(false)
const showGenerateConfirmDialog = ref(false)
const generateDateRange = ref({ start: '', end: '' })
const showProgressDialog = ref(false)
const progressPercentage = ref(0)
const progressStatus = ref<'success' | 'exception' | 'warning' | ''>('')
const progressText = ref('データ生成を準備中...')

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
  // 基本情報
  id: { label: 'ID', group: '基本情報' },
  date: { label: '日付', group: '基本情報' },
  day_of_week: { label: '曜日', group: '基本情報' },
  route_cd: { label: '工程グループ', group: '基本情報' },
  product_cd: { label: '製品CD', group: '基本情報' },
  product_name: { label: '製品名', group: '基本情報' },
  order_quantity: { label: '受注数', group: '受注・内示' },
  forecast_quantity: { label: '内示数', group: '受注・内示' },

  // 切断
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
  cutting_actual_plan: { label: '切断実計', group: '切断', width: 70 },
  cutting_actual_plan_trend: { label: '切断実計推移', group: '切断', width: 90 },

  // 面取
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
  chamfering_actual_plan: { label: '面取実計', group: '面取', width: 70 },
  chamfering_actual_plan_trend: { label: '面取実計推移', group: '面取', width: 90 },

  // 成型
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
  molding_actual_plan: { label: '成型実計', group: '成型', width: 70 },
  molding_actual_plan_trend: { label: '成型実計推移', group: '成型', width: 90 },

  // メッキ
  plating_carry_over: { label: 'メッキ繰越', group: 'メッキ', width: 80 },
  plating_actual: { label: 'メッキ実績', group: 'メッキ', width: 80 },
  plating_defect: { label: 'メッキ不良', group: 'メッキ', width: 80 },
  plating_scrap: { label: 'メッキ廃棄', group: 'メッキ', width: 80 },
  plating_on_hold: { label: 'メッキ保留品', group: 'メッキ', width: 80 },
  plating_inventory: { label: 'メッキ在庫', group: 'メッキ', width: 80 },
  plating_trend: { label: 'メッキ推移', group: 'メッキ', width: 80 },
  plating_production_date: { label: 'メッキ生産日', group: 'メッキ', type: 'date', width: 90 },
  plating_machine: { label: 'メッキ治具', group: 'メッキ', type: 'text', width: 90 },
  plating_plan: { label: 'メッキ計画', group: 'メッキ', width: 80 },
  plating_actual_plan: { label: 'メッキ実計', group: 'メッキ', width: 80 },
  plating_actual_plan_trend: { label: 'メッキ実計推移', group: 'メッキ', width: 90 },

  // 溶接
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

  // 検査
  inspection_carry_over: { label: '検査繰越', group: '検査', width: 70 },
  inspection_actual: { label: '検査実績', group: '検査', width: 70 },
  inspection_defect: { label: '検査不良', group: '検査', width: 70 },
  inspection_scrap: { label: '検査廃棄', group: '検査', width: 70 },
  inspection_on_hold: { label: '検査保留品', group: '検査', width: 80 },
  inspection_inventory: { label: '検査在庫', group: '検査', width: 70 },
  inspection_trend: { label: '検査推移', group: '検査', width: 70 },
  inspection_production_date: { label: '検査生産日', group: '検査', type: 'date', width: 90 },
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
  ...Object.fromEntries(
    columnKeys
      .filter(
        (k) =>
          !['id', 'date', 'day_of_week', 'route_cd', 'product_cd', 'product_name', 'order_quantity', 'forecast_quantity'].includes(k)
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
    const baseColumns = ['id', 'date', 'day_of_week', 'route_cd', 'product_cd', 'product_name', 'order_quantity', 'forecast_quantity']
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
const getSummaries = (param: { columns: any[]; data: any[] }) => {
  const { columns, data } = param
  const sums: string[] = []
  columns.forEach((column, index) => {
    if (index === 0) {
      sums.push('合計')
      return
    }
    const prop = column.property
    if (!prop || !numericFields.has(prop)) {
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
    const { data } = await updateProductionSummarysFromOrderDaily({
      updateMode: 'changed',
      days: 30,
      clearBeforeUpdate: false,
    })
    const info = data?.data || {}
    const msg =
      data?.message ||
      `${info.updated ?? 0}件の受注データを反映しました（変更なし ${info.unchanged ?? 0} 件 / スキップ ${info.skipped ?? 0} 件）`
    ElMessage.success(msg)
    await fetchData()
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.message || '受注データ更新に失敗しました')
  } finally {
    updatingFromOrderDaily.value = false
  }
}

const confirmGenerateData = async () => {
  showGenerateConfirmDialog.value = false
  const startDateStr = generateDateRange.value.start
  const endDateStr = generateDateRange.value.end
  if (!startDateStr || !endDateStr) return
  generating.value = true
  showProgressDialog.value = true
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
const handlePageSizeChange = () => fetchData()
const handlePageChange = () => fetchData()
const handleRefresh = () => fetchData()

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
  const win = window.open('', '_blank')
  if (!win) return
  win.document.write(`
    <!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"/><title>生産データ管理</title>
    <style>table{border-collapse:collapse;width:100%;font-size:11px}th,td{border:1px solid #e2e8f0;padding:6px 8px;text-align:center}th{background:#eef2ff;font-weight:600}</style>
    </head><body><h1>生産データ管理</h1><p>${dateRange.value ? dateRange.value.join(' ～ ') : ''} / ${printData.length}件</p>
    <table><thead><tr><th>${thead}</th></tr></thead><tbody>${tbody}</tbody></table></body></html>`)
  win.document.close()
  win.print()
  win.close()
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
})
</script>

<style scoped>
.production-data-management {
  padding: 0.5rem;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  min-height: 100%;
}
.page-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}
.title-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.page-title {
  margin: 0;
  font-size: 1.35rem;
  font-weight: 700;
  color: #0f172a;
}
.title-group :deep(.record-count.el-tag) {
  font-size: 0.75rem;
  height: 28px;
  line-height: 26px;
  padding: 0 8px;
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}
.header-actions :deep(.el-button) {
  font-size: 0.75rem;
  height: 28px;
  padding: 0 10px;
}
/* 内容区域：统一字体 0.75rem，组件高度 28px */
.table-card {
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  font-size: 0.75rem;
}
.table-card :deep(.el-card__header) {
  padding: 0.35rem 0.6rem;
}
.table-card :deep(.el-card__body) {
  padding: 0.35rem 0.6rem;
}
.filter-section {
  margin-top: 0.35rem;
  padding: 0.35rem 0.5rem;
  background: #fafbfc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  align-items: center;
}
.filter-item {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  background: #fff;
  padding: 0 0.5rem;
  border-radius: 4px;
  border: 1px solid #e5e7eb;
  height: 28px;
}
.filter-label {
  font-size: 0.75rem;
  font-weight: 700;
  color: #64748b;
  white-space: nowrap;
}
.date-filter-item {
  height: 28px;
}
.date-quick-item {
  height: 28px;
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
  min-height: 26px;
  padding: 0 8px;
}
.table-card :deep(.filter-section .el-date-editor) {
  width: 240px;
}
.date-quick-buttons {
  display: flex;
  gap: 0.15rem;
  align-items: center;
  background: #f8fafc;
  padding: 0 4px;
  border-radius: 4px;
  border: 1px solid #e2e8f0;
  height: 26px;
}
.date-quick-buttons :deep(.el-button) {
  font-size: 0.75rem;
  height: 22px;
  padding: 0 6px;
}
.filter-select {
  width: 160px;
}
.keyword-filter-input {
  width: 160px;
}
.summary-table-tabs {
  margin-bottom: 0;
}
.summary-table-tabs :deep(.el-tabs__header) {
  margin-bottom: 0;
  border: none;
}
.summary-table-tabs :deep(.el-tabs__content) {
  padding: 0;
  overflow: visible;
}
.summary-table-tabs :deep(.el-tab-pane) {
  padding: 0;
}
.summary-table-tabs :deep(.el-tabs__item) {
  padding: 0 10px;
  height: 28px;
  line-height: 28px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  margin-right: 0.25rem;
  font-size: 0.75rem;
}
.summary-table-tabs :deep(.el-tabs__item.is-active) {
  border-color: rgba(99, 102, 241, 0.4);
  background: #faf5ff;
}
.tab-text {
  font-weight: 600;
  font-size: 0.75rem;
  color: #475569;
}
/* テーブル：字体与区域统一 0.75rem */
.modern-table {
  font-size: 0.75rem;
}
.modern-table :deep(.el-table) {
  --el-table-border-color: #e5e7eb;
  --el-table-header-bg-color: #f8fafc;
  --el-table-row-hover-bg-color: #f1f5f9;
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

/* データ生成進度ダイアログ */
.progress-content {
  padding: 0.35rem 0;
}
.progress-info {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  margin-bottom: 0.6rem;
}
.progress-icon {
  font-size: 1.1rem;
  color: #6366f1;
}
.progress-text {
  font-size: 0.8rem;
  color: #475569;
}
.progress-bar {
  margin-bottom: 0.5rem;
}
.progress-details {
  font-size: 0.75rem;
  color: #64748b;
}
.progress-details .detail-value {
  margin-left: 0.35rem;
  font-weight: 600;
}

/* ========== 响应式 ========== */
@media (max-width: 992px) {
  .production-data-management {
    padding: 0.4rem;
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
  .page-title {
    font-size: 1.15rem;
  }
  .page-header-row {
    flex-direction: column;
    align-items: stretch;
    gap: 0.35rem;
    margin-bottom: 0.35rem;
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
</style>
