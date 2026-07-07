<template>
  <div class="bdr-page">
    <div class="page-bg" aria-hidden="true">
      <div class="bg-gradient"></div>
      <div class="bg-orb bg-orb-1"></div>
      <div class="bg-orb bg-orb-2"></div>
      <div class="bg-orb bg-orb-3"></div>
    </div>

    <div class="page-inner">
      <header class="top-bar glass animate-in" style="--delay: 0s">
        <div class="top-bar-main">
          <div class="brand-icon">
            <el-icon :size="22"><WarningFilled /></el-icon>
          </div>
          <div class="top-bar-text">
            <h1 class="page-title">大量廃棄・保留品管理</h1>
            <p class="page-meta">記録登録 · 処理追跡 · 未処理メール通知</p>
          </div>
        </div>
        <div class="top-bar-stats">
          <div class="mini-stat mini-stat--total" title="総件数">
            <el-icon><Document /></el-icon>
            <span class="mini-stat-val">{{ pagination.total.toLocaleString() }}</span>
            <span class="mini-stat-lbl">総件数</span>
          </div>
          <div class="mini-stat mini-stat--pending" title="未処理">
            <el-icon><WarningFilled /></el-icon>
            <span class="mini-stat-val">{{ pendingTotal.toLocaleString() }}</span>
            <span class="mini-stat-lbl">未処理</span>
          </div>
          <div class="mini-stat mini-stat--overdue" title="期限超過">
            <el-icon><Timer /></el-icon>
            <span class="mini-stat-val">{{ overdueTotal.toLocaleString() }}</span>
            <span class="mini-stat-lbl">期限超過</span>
          </div>
          <div class="mini-stat mini-stat--done" title="処理済">
            <el-icon><CircleCheckFilled /></el-icon>
            <span class="mini-stat-val">{{ processedTotal.toLocaleString() }}</span>
            <span class="mini-stat-lbl">処理済</span>
          </div>
        </div>
        <div class="top-bar-actions">
          <el-button class="btn-glass btn-notify" :icon="Message" size="small" @click="openNotifyDialog">
            未処理通知
            <span v-if="pendingTotal > 0" class="notify-badge">{{ pendingTotal > 99 ? '99+' : pendingTotal }}</span>
          </el-button>
          <el-button class="btn-glass btn-primary" type="primary" :icon="Plus" size="small" @click="openCreate">
            新規登録
          </el-button>
        </div>
      </header>

      <section class="filter-panel glass animate-in" style="--delay: 0.04s">
        <div class="filter-toolbar">
          <div class="filter-toolbar-left">
            <el-icon class="filter-icon"><Search /></el-icon>
            <span class="filter-title">検索</span>
            <div class="chip-group">
              <button
                v-for="chip in categoryChips"
                :key="chip.value"
                type="button"
                class="chip"
                :class="[`chip--cat-${chip.key}`, { 'chip--active': filters.report_category === chip.value }]"
                @click="toggleCategoryChip(chip.value)"
              >
                {{ chip.label }}
              </button>
            </div>
            <span class="chip-divider"></span>
            <div class="chip-group">
              <button
                type="button"
                class="chip chip--status-pending"
                :class="{ 'chip--active': filters.handling_status === '未処理' }"
                @click="toggleStatusChip('未処理')"
              >
                未処理
              </button>
              <button
                type="button"
                class="chip chip--status-done"
                :class="{ 'chip--active': filters.handling_status === '処理済' }"
                @click="toggleStatusChip('処理済')"
              >
                処理済
              </button>
              <span class="chip-divider"></span>
              <button
                type="button"
                class="chip chip--overdue"
                :class="{ 'chip--active': showOverdueOnly }"
                @click="showOverdueOnly = !showOverdueOnly"
              >
                期限超過
              </button>
            </div>
          </div>
          <el-button
            v-if="hasActiveFilters"
            link
            type="primary"
            size="small"
            class="clear-filters"
            @click="clearFilters"
          >
            条件クリア
          </el-button>
        </div>
        <el-form :model="filters" class="filter-form" label-position="top" @submit.prevent>
          <div class="filter-grid">
            <el-form-item label="発生日" class="filter-item span-2">
              <el-date-picker
                v-model="filters.date_range"
                type="daterange"
                range-separator="～"
                start-placeholder="開始"
                end-placeholder="終了"
                value-format="YYYY-MM-DD"
                unlink-panels
                size="small"
                class="ctrl-glass"
              />
            </el-form-item>
            <el-form-item label="報告区分" class="filter-item">
              <el-select v-model="filters.report_category" clearable placeholder="全て" size="small" class="ctrl-glass">
                <el-option v-for="item in reportCategoryOptions" :key="item" :label="item" :value="item" />
              </el-select>
            </el-form-item>
            <el-form-item label="発生工程" class="filter-item">
              <el-select v-model="filters.process_name" clearable placeholder="全て" size="small" class="ctrl-glass">
                <el-option v-for="item in processNameOptions" :key="item" :label="item" :value="item" />
              </el-select>
            </el-form-item>
            <el-form-item label="製品" class="filter-item">
              <el-select
                v-model="filters.product_cd"
                placeholder="製品"
                clearable
                filterable
                size="small"
                class="ctrl-glass"
              >
                <el-option
                  v-for="item in productOptions"
                  :key="item.product_cd"
                  :label="`${item.product_cd} - ${item.product_name || ''}`"
                  :value="item.product_cd"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="キーワード" class="filter-item">
              <el-input
                v-model="filters.keyword"
                placeholder="製品名 / 管理No / 備考"
                clearable
                :prefix-icon="Search"
                size="small"
                class="ctrl-glass"
              />
            </el-form-item>
          </div>
        </el-form>
      </section>

      <section class="table-panel glass animate-in" style="--delay: 0.08s">
        <div class="table-toolbar">
          <div class="table-toolbar-left">
            <el-icon><List /></el-icon>
            <span class="table-title">記録一覧</span>
            <span class="table-count">{{ pagination.total }}件</span>
            <span v-if="selectedRows.length" class="selection-pill">選択 {{ selectedRows.length }}</span>
          </div>
        </div>

        <div class="table-wrap">
        <el-table
          :data="recordList"
          v-loading="loading"
          size="small"
          stripe
          border
          class="bdr-table"
          :row-class-name="tableRowClassName"
          highlight-current-row
          @selection-change="handleSelectionChange"
        >
          <el-table-column type="selection" width="38" />
          <el-table-column prop="occurred_date" label="発生日" width="102" sortable>
            <template #default="{ row }">
              <span class="cell-date">{{ row.occurred_date }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="report_category" label="報告区分" width="96">
            <template #default="{ row }">
              <span class="pill" :class="`pill--cat-${categoryKey(row.report_category)}`">
                {{ row.report_category }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="process_name" label="工程" width="76">
            <template #default="{ row }">
              <span class="pill pill--process" :class="`pill--proc-${processKey(row.process_name)}`">
                {{ row.process_name }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="product_name" label="製品名" min-width="150" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="cell-product">{{ row.product_name }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="quantity" label="本数" width="72" align="right">
            <template #default="{ row }">
              <span class="cell-qty">{{ row.quantity?.toLocaleString() }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="handling_status" label="処理" width="84" align="center">
            <template #default="{ row }">
              <span class="pill" :class="row.handling_status === '処理済' ? 'pill--done' : 'pill--pending'">
                {{ row.handling_status }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="processing_deadline_date" label="処理期限" width="100">
            <template #default="{ row }">
              <span
                v-if="row.report_category === '保留品' && row.processing_deadline_date"
                class="cell-deadline"
                :class="{ 'cell-deadline--overdue': row.is_overdue }"
              >
                {{ row.processing_deadline_date }}
              </span>
              <span v-else class="cell-muted">—</span>
            </template>
          </el-table-column>
          <el-table-column prop="processed_date" label="処理日" width="100">
            <template #default="{ row }">
              <span class="cell-muted">{{ row.processed_date || '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="management_no" label="管理No" width="100" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="cell-mgmt">{{ row.management_no || '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="remarks" label="備考" min-width="120" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="cell-muted">{{ row.remarks || '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="108" fixed="right" align="center">
            <template #default="{ row }">
              <div class="row-actions">
                <el-button class="act-btn act-edit" link size="small" :icon="Edit" @click="openEdit(row)" />
                <el-button class="act-btn act-del" link size="small" :icon="Delete" @click="handleDelete(row)" />
              </div>
            </template>
          </el-table-column>
        </el-table>
        </div>

        <div class="pagination-bar">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :total="pagination.total"
            :page-sizes="[20, 50, 100]"
            layout="total, sizes, prev, pager, next"
            background
            size="small"
          />
        </div>
      </section>
    </div>

    <!-- 登録・編集 -->
    <el-dialog
      v-model="editDialogVisible"
      width="520px"
      destroy-on-close
      append-to-body
      align-center
      class="bdr-dialog bdr-dialog--edit"
      :show-close="true"
    >
      <template #header>
        <div class="dlg-header">
          <div class="dlg-header-icon" :class="editMode === 'create' ? 'dlg-header-icon--new' : 'dlg-header-icon--edit'">
            <el-icon :size="18"><component :is="editMode === 'create' ? Plus : Edit" /></el-icon>
          </div>
          <div class="dlg-header-text">
            <h3 class="dlg-title">{{ editMode === 'create' ? '新規登録' : '記録編集' }}</h3>
            <p class="dlg-subtitle">大量廃棄・保留品データ</p>
          </div>
          <span class="dlg-badge" :class="editMode === 'create' ? 'dlg-badge--new' : 'dlg-badge--edit'">
            {{ editMode === 'create' ? 'NEW' : 'EDIT' }}
          </span>
        </div>
      </template>

      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-position="top"
        size="small"
        class="edit-form"
        @submit.prevent
      >
        <!-- 基本情報 -->
        <div class="form-block form-block--basic">
          <div class="block-head">
            <el-icon><Calendar /></el-icon>
            <span>基本情報</span>
          </div>
          <div class="block-body block-body--3col">
            <el-form-item label="発生日" prop="occurred_date">
              <el-date-picker
                v-model="editForm.occurred_date"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="選択"
                class="ctrl-full"
              />
            </el-form-item>
            <el-form-item label="管理No" prop="management_no" class="mgmt-no-item">
              <el-input
                v-model="editForm.management_no"
                placeholder="13桁"
                class="mgmt-no-input"
                maxlength="13"
              />
            </el-form-item>
            <el-form-item label="発生本数" prop="quantity" class="qty-item">
              <el-input
                v-model="quantityDisplay"
                placeholder="0"
                class="qty-input"
                maxlength="5"
                inputmode="numeric"
              />
            </el-form-item>
          </div>
        </div>

        <!-- 報告区分 -->
        <div class="form-block form-block--category">
          <div class="block-head">
            <el-icon><WarningFilled /></el-icon>
            <span>報告区分</span>
          </div>
          <el-form-item prop="report_category" class="block-field-no-margin">
            <div class="chip-row">
              <button
                v-for="item in reportCategoryOptions"
                :key="item"
                type="button"
                class="pick-chip"
                :class="[
                  `pick-chip--cat-${categoryKey(item)}`,
                  { 'pick-chip--active': editForm.report_category === item },
                ]"
                @click="selectReportCategory(item)"
              >
                {{ item }}
              </button>
            </div>
          </el-form-item>
        </div>

        <!-- 保留品：期間内処理期限 -->
        <div
          v-if="editForm.report_category === '保留品'"
          class="form-block form-block--deadline"
        >
          <div class="block-head">
            <el-icon><Timer /></el-icon>
            <span>期間内処理期限</span>
            <span class="block-head-hint">未処理の保留品は必須</span>
          </div>
          <el-form-item prop="processing_deadline_date" class="block-field-no-margin deadline-field">
            <el-date-picker
              v-model="editForm.processing_deadline_date"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="期限日を選択"
              class="deadline-picker"
            />
          </el-form-item>
        </div>

        <!-- 発生工程 -->
        <div class="form-block form-block--process">
          <div class="block-head">
            <el-icon><SetUp /></el-icon>
            <span>発生工程</span>
          </div>
          <el-form-item prop="process_name" class="block-field-no-margin">
            <div class="chip-row chip-row--wrap">
              <button
                v-for="item in processNameOptions"
                :key="item"
                type="button"
                class="pick-chip pick-chip--sm"
                :class="[
                  `pick-chip--proc-${processKey(item)}`,
                  { 'pick-chip--active': editForm.process_name === item },
                ]"
                @click="editForm.process_name = item"
              >
                {{ item }}
              </button>
            </div>
          </el-form-item>
        </div>

        <!-- 製品 -->
        <div class="form-block form-block--product">
          <div class="block-head">
            <el-icon><Goods /></el-icon>
            <span>製品</span>
          </div>
          <el-form-item prop="product_cd" class="block-field-no-margin">
            <el-select
              v-model="editForm.product_cd"
              placeholder="製品を選択"
              filterable
              clearable
              class="ctrl-full"
              @change="handleProductChange"
            >
              <el-option
                v-for="item in productOptions"
                :key="item.product_cd"
                :label="`${item.product_cd} - ${item.product_name || ''}`"
                :value="item.product_cd"
              />
            </el-select>
          </el-form-item>
        </div>

        <!-- 処理 -->
        <div
          class="form-block form-block--status"
          :class="editForm.handling_status === '処理済' ? 'form-block--done' : 'form-block--pending'"
        >
          <div class="block-head">
            <el-icon><CircleCheckFilled /></el-icon>
            <span>処理状態</span>
          </div>
          <div class="block-body block-body--status">
            <el-form-item prop="handling_status" class="block-field-no-margin status-field">
              <div class="chip-row">
                <button
                  type="button"
                  class="pick-chip pick-chip--status-pending"
                  :class="{ 'pick-chip--active': editForm.handling_status === '未処理' }"
                  @click="setHandlingStatus('未処理')"
                >
                  未処理
                </button>
                <button
                  type="button"
                  class="pick-chip pick-chip--status-done"
                  :class="{ 'pick-chip--active': editForm.handling_status === '処理済' }"
                  @click="setHandlingStatus('処理済')"
                >
                  処理済
                </button>
              </div>
            </el-form-item>
            <el-form-item label="処理日付" prop="processed_date" class="processed-date-field">
              <el-date-picker
                v-model="editForm.processed_date"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="処理日"
                class="ctrl-full"
                :disabled="editForm.handling_status !== '処理済'"
              />
            </el-form-item>
          </div>
        </div>

        <!-- 備考 -->
        <div class="form-block form-block--remarks">
          <div class="block-head">
            <el-icon><EditPen /></el-icon>
            <span>備考</span>
          </div>
          <el-form-item prop="remarks" class="block-field-no-margin">
            <el-input v-model="editForm.remarks" type="textarea" :rows="2" placeholder="備考（任意）" resize="none" />
          </el-form-item>
        </div>
      </el-form>

      <template #footer>
        <div class="dlg-footer">
          <el-button class="dlg-btn dlg-btn--cancel" @click="editDialogVisible = false">キャンセル</el-button>
          <el-button class="dlg-btn dlg-btn--save" type="primary" :loading="editLoading" @click="handleSave">
            <el-icon v-if="!editLoading"><CircleCheckFilled /></el-icon>
            保存
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- メール通知 -->
    <el-dialog
      v-model="notifyDialogVisible"
      title="未処理データ メール通知"
      width="720px"
      destroy-on-close
      append-to-body
      align-center
      class="bdr-dialog bdr-dialog--notify"
    >
      <div v-loading="notifyLoading" class="notify-body">
        <div v-if="notifyPreview" class="notify-hero" :class="{ 'notify-hero--warn': !notifyPreview.can_send }">
          <div class="notify-hero-stat">
            <span class="notify-hero-num">{{ notifyPreview.item_count }}</span>
            <span class="notify-hero-unit">件</span>
          </div>
          <div class="notify-hero-meta">
            <p>合計 <strong>{{ notifyPreview.total_quantity }}</strong> 本の未処理データ</p>
            <p
              v-if="notifyPreview.overdue_count && notifyPreview.overdue_count > 0"
              class="notify-deadline-warn"
            >
              ⚠ 処理期限超過 <strong>{{ notifyPreview.overdue_count }}</strong> 件 — メールに重要提醒として記載されます
            </p>
            <p class="notify-hint">
              {{ selectedRows.length > 0 ? '※ 選択中の未処理行のみ通知' : '※ 全未処理データを通知' }}
            </p>
          </div>
        </div>
        <el-alert
          v-if="notifyPreview?.overdue_count && notifyPreview.overdue_count > 0"
          type="error"
          :closable="false"
          show-icon
          class="notify-alert notify-alert--deadline"
        >
          <template #title>
            重要：処理期限超過の保留品が {{ notifyPreview.overdue_count }} 件含まれます
          </template>
          <p class="notify-deadline-detail">
            送信メールには処理期限を強調表示し、至急対応の提醒を自動挿入します。
          </p>
        </el-alert>
        <el-alert
          v-else-if="notifyPreview?.has_deadline_notice"
          type="warning"
          :closable="false"
          show-icon
          title="保留品の処理期限が通知メールに記載されます"
          class="notify-alert notify-alert--deadline"
        />
        <el-alert
          v-if="notifyPreview && !notifyPreview.can_send"
          type="warning"
          :closable="false"
          show-icon
          title="送信条件を満たしていません（未処理データ・SMTP・テンプレートを確認）"
          class="notify-alert"
        />
        <el-form label-width="100px" size="default" class="notify-form">
          <el-form-item label="通知先" required>
            <el-select
              v-model="notifyUserIds"
              multiple
              filterable
              collapse-tags
              collapse-tags-tooltip
              placeholder="ユーザーを選択"
              class="full-width"
            >
              <el-option
                v-for="u in notifyUsers"
                :key="u.id"
                :label="`${u.full_name || u.username} (${u.email || 'メール未設定'})`"
                :value="u.id"
                :disabled="!u.email"
              />
            </el-select>
          </el-form-item>
        </el-form>
        <el-table
          v-if="notifyPreview?.items?.length"
          :data="notifyPreview.items"
          size="small"
          max-height="200"
          class="notify-table"
        >
          <el-table-column prop="occurred_date" label="発生日" width="96" />
          <el-table-column prop="report_category" label="区分" width="84" />
          <el-table-column prop="process_name" label="工程" width="72" />
          <el-table-column prop="product_name" label="製品名" min-width="100" show-overflow-tooltip />
          <el-table-column prop="quantity" label="本数" width="64" align="right" />
          <el-table-column prop="processing_deadline_date" label="処理期限" width="108" align="center">
            <template #default="{ row }">
              <span
                v-if="row.report_category === '保留品' && row.processing_deadline_date"
                class="cell-deadline"
                :class="{ 'cell-deadline--overdue': row.is_overdue }"
              >
                <template v-if="row.is_overdue">⚠ </template>{{ row.processing_deadline_date }}
              </span>
              <span v-else class="cell-muted">—</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button class="btn-glass btn-secondary" @click="notifyDialogVisible = false">キャンセル</el-button>
        <el-button
          class="btn-glass btn-notify-solid"
          type="warning"
          :loading="notifySending"
          :disabled="!notifyPreview?.can_send || notifyUserIds.length === 0"
          @click="handleSendNotify"
        >
          送信
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, watch, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import dayjs from 'dayjs'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  Delete,
  Edit,
  Document,
  Search,
  List,
  Plus,
  Message,
  WarningFilled,
  CircleCheckFilled,
  Calendar,
  SetUp,
  Goods,
  EditPen,
  Timer,
} from '@element-plus/icons-vue'
import { getProductList } from '@/api/master/productMaster'
import { getUsers, type UserListItem } from '@/api/system'
import {
  getBulkDisposalRetentionList,
  getBulkDisposalRetentionOptions,
  createBulkDisposalRetention,
  updateBulkDisposalRetention,
  deleteBulkDisposalRetention,
  previewBulkDisposalRetentionNotification,
  sendBulkDisposalRetentionNotification,
  type BulkDisposalRetentionRecord,
  type BulkDisposalRetentionForm,
  type BulkDisposalRetentionNotifyPreview,
} from '@/api/erp/bulkDisposalRetention'

const route = useRoute()

const reportCategoryOptions = ref<string[]>(['大量廃棄', '保留品', 'その他'])
const processNameOptions = ref<string[]>(['切断', '面取', '成型', 'メッキ', '溶接', '検査', 'その他'])
const handlingStatusOptions = ref<string[]>(['未処理', '処理済'])
const productOptions = ref<Array<{ product_cd: string; product_name?: string }>>([])

const categoryChips = [
  { label: '大量廃棄', value: '大量廃棄', key: 'disposal' },
  { label: '保留品', value: '保留品', key: 'hold' },
  { label: 'その他', value: 'その他', key: 'other' },
]

const loading = ref(false)
const editLoading = ref(false)
const recordList = ref<BulkDisposalRetentionRecord[]>([])
const selectedRows = ref<BulkDisposalRetentionRecord[]>([])
const pendingTotal = ref(0)
const overdueTotal = ref(0)
const showOverdueOnly = ref(false)

const filters = reactive({
  date_range: null as [string, string] | null,
  report_category: '',
  process_name: '',
  handling_status: '',
  product_cd: '',
  keyword: '',
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

const processedTotal = computed(() => Math.max(0, pagination.total - pendingTotal.value))

const hasActiveFilters = computed(
  () =>
    !!filters.date_range ||
    !!filters.report_category ||
    !!filters.process_name ||
    !!filters.handling_status ||
    !!filters.product_cd ||
    !!filters.keyword ||
    showOverdueOnly.value
)

const editDialogVisible = ref(false)
const editMode = ref<'create' | 'edit'>('create')
const editingId = ref<number | null>(null)
const editFormRef = ref<FormInstance>()

const defaultForm = (): BulkDisposalRetentionForm => ({
  occurred_date: dayjs().format('YYYY-MM-DD'),
  report_category: '大量廃棄',
  process_name: '切断',
  product_cd: '',
  product_name: '',
  quantity: 0,
  handling_status: '未処理',
  processed_date: null,
  processing_deadline_date: null,
  management_no: '',
  remarks: '',
})

const editForm = reactive<BulkDisposalRetentionForm>(defaultForm())

const quantityDisplay = computed({
  get: () => String(editForm.quantity ?? 0),
  set: (val: string) => {
    const digits = val.replace(/\D/g, '').slice(0, 5)
    editForm.quantity = digits === '' ? 0 : parseInt(digits, 10)
  },
})

const editRules: FormRules = {
  occurred_date: [{ required: true, message: '発生日を選択してください', trigger: 'change' }],
  report_category: [{ required: true, message: '報告区分を選択してください', trigger: 'change' }],
  process_name: [{ required: true, message: '発生工程を選択してください', trigger: 'change' }],
  product_cd: [{ required: true, message: '製品を選択してください', trigger: 'change' }],
  quantity: [
    { required: true, message: '発生本数を入力してください', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        const n = Number(value)
        if (!Number.isFinite(n) || n < 0) {
          callback(new Error('0以上の数値を入力してください'))
        } else if (n > 99999) {
          callback(new Error('5桁以内で入力してください'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
  handling_status: [{ required: true, message: '処理を選択してください', trigger: 'change' }],
  processing_deadline_date: [
    {
      validator: (_rule, value, callback) => {
        if (editForm.report_category === '保留品' && editForm.handling_status === '未処理') {
          if (!value) {
            callback(new Error('期間内処理期限を入力してください'))
            return
          }
        }
        callback()
      },
      trigger: 'change',
    },
  ],
}

const notifyDialogVisible = ref(false)
const notifyLoading = ref(false)
const notifySending = ref(false)
const notifyPreview = ref<BulkDisposalRetentionNotifyPreview | null>(null)
const notifyUsers = ref<UserListItem[]>([])
const notifyUserIds = ref<number[]>([])

function categoryKey(cat: string) {
  if (cat === '大量廃棄') return 'disposal'
  if (cat === '保留品') return 'hold'
  return 'other'
}

function processKey(proc: string) {
  const map: Record<string, string> = {
    切断: 'cut',
    面取: 'chamfer',
    成型: 'form',
    メッキ: 'plate',
    溶接: 'weld',
    検査: 'inspect',
    その他: 'other',
  }
  return map[proc] || 'other'
}

function tableRowClassName({ row }: { row: BulkDisposalRetentionRecord }) {
  if (row.is_overdue) return 'row-overdue'
  if (row.handling_status === '未処理') return 'row-pending'
  return ''
}

function selectReportCategory(item: string) {
  editForm.report_category = item
  if (item !== '保留品') {
    editForm.processing_deadline_date = null
  }
}

function toggleCategoryChip(value: string) {
  filters.report_category = filters.report_category === value ? '' : value
}

function toggleStatusChip(value: string) {
  filters.handling_status = filters.handling_status === value ? '' : value
}

function clearFilters() {
  filters.date_range = null
  filters.report_category = ''
  filters.process_name = ''
  filters.handling_status = ''
  filters.product_cd = ''
  filters.keyword = ''
  showOverdueOnly.value = false
}

function handleProductChange(productCd: string) {
  const found = productOptions.value.find((p) => p.product_cd === productCd)
  editForm.product_name = found?.product_name || productCd || ''
}

function handleHandlingStatusChange(status: string | number | boolean | undefined) {
  if (status === '処理済' && !editForm.processed_date) {
    editForm.processed_date = dayjs().format('YYYY-MM-DD')
  }
  if (status === '未処理') {
    editForm.processed_date = null
  }
}

function setHandlingStatus(status: '未処理' | '処理済') {
  editForm.handling_status = status
  handleHandlingStatusChange(status)
}

function handleSelectionChange(rows: BulkDisposalRetentionRecord[]) {
  selectedRows.value = rows
}

async function loadOptions() {
  try {
    const res = await getBulkDisposalRetentionOptions()
    if (res?.report_categories?.length) reportCategoryOptions.value = res.report_categories
    if (res?.process_names?.length) processNameOptions.value = res.process_names
    if (res?.handling_statuses?.length) handlingStatusOptions.value = res.handling_statuses
  } catch {
    // fallback
  }
}

async function loadProducts() {
  try {
    const res = await getProductList({ page: 1, pageSize: 5000, status: 'active' })
    const list = res?.data?.list ?? res?.list ?? []
    productOptions.value = list
      .filter((p) => p.product_cd)
      .map((p) => ({ product_cd: p.product_cd, product_name: p.product_name }))
  } catch {
    productOptions.value = []
  }
}

async function loadRecords() {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }
    if (filters.date_range?.[0]) params.occurred_date_from = filters.date_range[0]
    if (filters.date_range?.[1]) params.occurred_date_to = filters.date_range[1]
    if (filters.report_category) params.report_category = filters.report_category
    if (filters.process_name) params.process_name = filters.process_name
    if (filters.handling_status) params.handling_status = filters.handling_status
    if (filters.product_cd) params.product_cd = filters.product_cd
    if (filters.keyword) params.keyword = filters.keyword
    if (showOverdueOnly.value) params.overdue_only = true

    const res = await getBulkDisposalRetentionList(params)
    recordList.value = res?.list ?? []
    pagination.total = res?.total ?? 0
    pendingTotal.value = res?.pending_total ?? 0
    overdueTotal.value = res?.overdue_total ?? 0
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'データ取得に失敗しました'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editMode.value = 'create'
  editingId.value = null
  Object.assign(editForm, defaultForm())
  editDialogVisible.value = true
}

function openEdit(row: BulkDisposalRetentionRecord) {
  editMode.value = 'edit'
  editingId.value = row.id
  Object.assign(editForm, {
    occurred_date: row.occurred_date,
    report_category: row.report_category,
    process_name: row.process_name,
    product_cd: row.product_cd || '',
    product_name: row.product_name,
    quantity: row.quantity,
    handling_status: row.handling_status,
    processed_date: row.processed_date,
    processing_deadline_date: row.processing_deadline_date,
    management_no: row.management_no || '',
    remarks: row.remarks || '',
  })
  editDialogVisible.value = true
}

async function handleSave() {
  if (!editFormRef.value) return
  const valid = await editFormRef.value.validate().catch(() => false)
  if (!valid) return
  if (!editForm.product_name) handleProductChange(editForm.product_cd || '')

  editLoading.value = true
  try {
    const payload = { ...editForm }
    if (editMode.value === 'create') {
      await createBulkDisposalRetention(payload)
      ElMessage.success('登録しました')
    } else if (editingId.value) {
      await updateBulkDisposalRetention(editingId.value, payload)
      ElMessage.success('更新しました')
    }
    editDialogVisible.value = false
    await loadRecords()
  } catch (e: unknown) {
    ElMessage.error(e instanceof Error ? e.message : '保存に失敗しました')
  } finally {
    editLoading.value = false
  }
}

async function handleDelete(row: BulkDisposalRetentionRecord) {
  try {
    await ElMessageBox.confirm(`管理No: ${row.management_no || row.id} を削除しますか？`, '確認', { type: 'warning' })
    await deleteBulkDisposalRetention(row.id)
    ElMessage.success('削除しました')
    await loadRecords()
  } catch {
    // cancelled
  }
}

async function loadNotifyUsers() {
  try {
    const res = await getUsers({ page: 1, page_size: 500, status: 'active' })
    notifyUsers.value = res?.items ?? []
  } catch {
    notifyUsers.value = []
  }
}

async function loadNotifyPreview() {
  notifyLoading.value = true
  try {
    const pendingSelected = selectedRows.value.filter((r) => r.handling_status === '未処理')
    const recordIds = pendingSelected.length > 0 ? pendingSelected.map((r) => r.id).join(',') : undefined
    notifyPreview.value = await previewBulkDisposalRetentionNotification(
      recordIds ? { record_ids: recordIds } : undefined
    )
  } catch (e: unknown) {
    ElMessage.error(e instanceof Error ? e.message : 'プレビュー取得に失敗しました')
    notifyPreview.value = null
  } finally {
    notifyLoading.value = false
  }
}

async function openNotifyDialog() {
  notifyUserIds.value = []
  notifyDialogVisible.value = true
  await Promise.all([loadNotifyUsers(), loadNotifyPreview()])
}

async function handleSendNotify() {
  if (notifyUserIds.value.length === 0) {
    ElMessage.warning('通知先ユーザーを選択してください')
    return
  }
  notifySending.value = true
  try {
    const pendingSelected = selectedRows.value.filter((r) => r.handling_status === '未処理')
    const recordIds = pendingSelected.length > 0 ? pendingSelected.map((r) => r.id) : undefined
    const res = await sendBulkDisposalRetentionNotification({
      user_ids: notifyUserIds.value,
      record_ids: recordIds,
    })
    ElMessage.success(res?.message || '送信しました')
    notifyDialogVisible.value = false
  } catch (e: unknown) {
    ElMessage.error(e instanceof Error ? e.message : '送信に失敗しました')
  } finally {
    notifySending.value = false
  }
}

watch(
  () => [
    filters.date_range,
    filters.report_category,
    filters.process_name,
    filters.handling_status,
    filters.product_cd,
    filters.keyword,
  ],
  () => {
    pagination.page = 1
    loadRecords()
  }
)

watch(() => [pagination.page, pagination.pageSize, showOverdueOnly.value], () => loadRecords())

onMounted(async () => {
  if (route.query.overdue === '1') {
    showOverdueOnly.value = true
    filters.report_category = '保留品'
    filters.handling_status = '未処理'
  }
  await Promise.all([loadOptions(), loadProducts()])
  await loadRecords()
})
</script>

<style scoped>
/* ===== 背景 ===== */
.bdr-page {
  position: relative;
  min-height: 100%;
  overflow: hidden;
  color: #1e293b;
  font-size: 13px;
}

.page-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}

.bg-gradient {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(145deg, #0f172a 0%, #1e293b 38%, #334155 72%, #1e3a5f 100%);
}

.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.55;
  animation: orbFloat 18s ease-in-out infinite;
}

.bg-orb-1 {
  width: 340px;
  height: 340px;
  top: -80px;
  right: -60px;
  background: radial-gradient(circle, rgba(239, 68, 68, 0.45), transparent 70%);
}

.bg-orb-2 {
  width: 280px;
  height: 280px;
  bottom: 10%;
  left: -40px;
  background: radial-gradient(circle, rgba(245, 158, 11, 0.4), transparent 72%);
  animation-delay: -6s;
}

.bg-orb-3 {
  width: 220px;
  height: 220px;
  top: 45%;
  right: 25%;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.35), transparent 70%);
  animation-delay: -12s;
}

@keyframes orbFloat {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(14px, -16px) scale(1.05); }
}

/* ===== 玻璃质感 ===== */
.glass {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.28),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.animate-in {
  animation: fadeInUp 0.45s cubic-bezier(0.22, 1, 0.36, 1) forwards;
  opacity: 0;
  animation-delay: var(--delay, 0s);
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(14px) scale(0.99); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.page-inner {
  position: relative;
  z-index: 1;
  max-width: 1480px;
  margin: 0 auto;
  padding: 8px 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* ===== 顶栏 ===== */
.top-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px 14px;
  padding: 10px 14px;
  border-radius: 14px;
}

.top-bar-main {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex: 1 1 200px;
}

.brand-icon {
  width: 40px;
  height: 40px;
  border-radius: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
  background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);
  box-shadow: 0 6px 20px rgba(239, 68, 68, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.25);
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.brand-icon:hover {
  transform: translateY(-2px) scale(1.03);
  box-shadow: 0 10px 28px rgba(239, 68, 68, 0.5);
}

.page-title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 700;
  color: #fff;
  letter-spacing: -0.02em;
  line-height: 1.2;
}

.page-meta {
  margin: 2px 0 0;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.55);
}

.top-bar-stats {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.mini-stat {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  border-radius: 10px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.75);
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06);
  transition: transform 0.2s ease, background 0.2s ease;
}

.mini-stat:hover {
  transform: translateY(-1px);
  background: rgba(255, 255, 255, 0.1);
}

.mini-stat-val {
  font-size: 15px;
  font-weight: 800;
  color: #fff;
  line-height: 1;
}

.mini-stat-lbl {
  font-size: 10px;
  opacity: 0.8;
}

.mini-stat--total .el-icon { color: #93c5fd; }
.mini-stat--pending .el-icon { color: #fcd34d; }
.mini-stat--overdue .el-icon { color: #fb7185; }
.mini-stat--done .el-icon { color: #6ee7b7; }

.top-bar-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.btn-glass {
  border-radius: 8px;
  font-weight: 600;
  border: 1px solid transparent;
  transition: transform 0.18s ease, filter 0.18s ease, box-shadow 0.18s ease;
}

.btn-glass:hover { transform: translateY(-1px); }

.btn-glass.btn-primary {
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  border-color: rgba(255, 255, 255, 0.2);
  box-shadow: 0 4px 14px rgba(59, 130, 246, 0.4);
}

.btn-glass.btn-notify {
  position: relative;
  background: rgba(245, 158, 11, 0.18);
  color: #fde68a;
  border-color: rgba(245, 158, 11, 0.35);
}

.btn-glass.btn-notify:hover {
  background: rgba(245, 158, 11, 0.28);
  color: #fff;
}

.notify-badge {
  position: absolute;
  top: -6px;
  right: -6px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 8px;
  font-size: 10px;
  font-weight: 700;
  line-height: 16px;
  text-align: center;
  color: #fff;
  background: #ef4444;
  box-shadow: 0 2px 6px rgba(239, 68, 68, 0.5);
}

.btn-glass.btn-secondary {
  background: rgba(255, 255, 255, 0.85);
  color: #475569;
  border-color: rgba(0, 0, 0, 0.08);
}

.btn-glass.btn-notify-solid {
  background: linear-gradient(135deg, #f59e0b, #ef4444);
  border: none;
  box-shadow: 0 4px 14px rgba(245, 158, 11, 0.4);
}

/* ===== 筛选 ===== */
.filter-panel {
  border-radius: 12px;
  padding: 8px 12px 6px;
}

.filter-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.filter-toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  min-width: 0;
}

.filter-icon { color: #fbbf24; font-size: 14px; }
.filter-title { font-weight: 700; font-size: 12px; color: rgba(255, 255, 255, 0.9); }

.chip-group { display: flex; gap: 4px; flex-wrap: wrap; }

.chip {
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.75);
  cursor: pointer;
  transition: all 0.2s ease;
}

.chip:hover {
  background: rgba(255, 255, 255, 0.12);
  transform: translateY(-1px);
}

.chip--active {
  color: #fff;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.25);
}

.chip--cat-disposal.chip--active { background: linear-gradient(135deg, #ef4444, #dc2626); border-color: transparent; }
.chip--cat-hold.chip--active { background: linear-gradient(135deg, #f59e0b, #d97706); border-color: transparent; }
.chip--cat-other.chip--active { background: linear-gradient(135deg, #64748b, #475569); border-color: transparent; }
.chip--status-pending.chip--active { background: linear-gradient(135deg, #f59e0b, #ea580c); border-color: transparent; }
.chip--status-done.chip--active { background: linear-gradient(135deg, #10b981, #059669); border-color: transparent; }
.chip--overdue.chip--active { background: linear-gradient(135deg, #ef4444, #dc2626); border-color: transparent; }

.chip-divider {
  width: 1px;
  height: 18px;
  background: rgba(255, 255, 255, 0.15);
  margin: 0 2px;
}

.clear-filters { color: #93c5fd !important; font-size: 11px; }

.filter-form :deep(.el-form-item) { margin-bottom: 4px; }
.filter-form :deep(.el-form-item__label) {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.55);
  padding-bottom: 1px;
  line-height: 1.2;
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 4px 8px;
}

.filter-item.span-2 { grid-column: span 2; }

.ctrl-glass { width: 100%; }

.ctrl-glass :deep(.el-input__wrapper),
.ctrl-glass :deep(.el-select__wrapper) {
  background: rgba(15, 23, 42, 0.35);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 7px;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.15);
  color: #f1f5f9;
}

.ctrl-glass :deep(.el-input__inner),
.ctrl-glass :deep(.el-select__selected-item) {
  color: #f1f5f9;
}

.ctrl-glass :deep(.el-input__wrapper:hover),
.ctrl-glass :deep(.el-select__wrapper:hover) {
  border-color: rgba(147, 197, 253, 0.4);
}

/* ===== 表格 ===== */
.table-panel {
  border-radius: 12px;
  padding: 8px 10px 6px;
  flex: 1;
}

.table-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
  padding: 0 2px;
}

.table-toolbar-left {
  display: flex;
  align-items: center;
  gap: 6px;
  color: rgba(255, 255, 255, 0.9);
  font-size: 12px;
}

.table-title { font-weight: 700; }
.table-count { font-size: 11px; color: rgba(255, 255, 255, 0.5); }

.selection-pill {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 10px;
  font-weight: 600;
  background: rgba(59, 130, 246, 0.25);
  color: #93c5fd;
  border: 1px solid rgba(59, 130, 246, 0.35);
}

/* 表格浅色底 · 深色字，确保可读性 */
.table-wrap {
  background: #ffffff;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.25);
  box-shadow:
    0 4px 16px rgba(0, 0, 0, 0.18),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.bdr-table {
  --el-table-border-color: #e2e8f0;
  --el-table-header-bg-color: #f1f5f9;
  --el-table-tr-bg-color: #ffffff;
  --el-table-row-hover-bg-color: #eff6ff;
  --el-table-current-row-bg-color: #dbeafe;
  --el-table-text-color: #1e293b;
  --el-table-header-text-color: #475569;
  background: #ffffff;
}

.bdr-table :deep(.el-table__inner-wrapper) {
  border-radius: 0;
}

.bdr-table :deep(th.el-table__cell) {
  font-size: 11px;
  font-weight: 700;
  padding: 7px 0;
  color: #475569 !important;
  background: #f1f5f9 !important;
}

.bdr-table :deep(td.el-table__cell) {
  padding: 6px 0;
  font-size: 12px;
  color: #1e293b !important;
  background: #ffffff;
}

.bdr-table :deep(.el-table__body tr.el-table__row--striped td.el-table__cell) {
  background: #f8fafc !important;
}

.bdr-table :deep(.el-table__body tr:hover > td.el-table__cell) {
  background: #eff6ff !important;
}

.bdr-table :deep(.row-pending td.el-table__cell) {
  background: #fffbeb !important;
}

.bdr-table :deep(.row-pending.el-table__row--striped td.el-table__cell) {
  background: #fef3c7 !important;
}

.bdr-table :deep(.row-pending:hover td.el-table__cell) {
  background: #fde68a !important;
}

.bdr-table :deep(.row-overdue td.el-table__cell) {
  background: #fef2f2 !important;
}

.bdr-table :deep(.row-overdue.el-table__row--striped td.el-table__cell) {
  background: #fee2e2 !important;
}

.bdr-table :deep(.row-overdue:hover td.el-table__cell) {
  background: #fecaca !important;
}

.bdr-table :deep(.el-checkbox__inner) {
  border-color: #94a3b8;
}

.cell-date { font-weight: 600; color: #0f172a; font-variant-numeric: tabular-nums; }
.cell-product { font-weight: 500; color: #1e293b; }
.cell-qty { font-weight: 700; color: #b45309; font-variant-numeric: tabular-nums; }
.cell-mgmt { font-family: ui-monospace, monospace; font-size: 11px; color: #475569; }
.cell-deadline { font-weight: 600; color: #b45309; font-variant-numeric: tabular-nums; }
.cell-deadline--overdue { color: #dc2626; font-weight: 800; }
.cell-muted { color: #94a3b8; font-size: 11px; }

/* 彩色标签（浅色底适配） */
.pill {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 700;
  line-height: 1.5;
  white-space: nowrap;
}

.pill--cat-disposal { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
.pill--cat-hold { background: #fffbeb; color: #d97706; border: 1px solid #fde68a; }
.pill--cat-other { background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; }
.pill--pending { background: #fff7ed; color: #ea580c; border: 1px solid #fed7aa; }
.pill--done { background: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; }

.pill--process { font-size: 10px; padding: 2px 6px; }
.pill--proc-cut { background: #eff6ff; color: #2563eb; border-color: #bfdbfe; }
.pill--proc-chamfer { background: #f0f9ff; color: #0284c7; border-color: #bae6fd; }
.pill--proc-form { background: #faf5ff; color: #7c3aed; border-color: #ddd6fe; }
.pill--proc-plate { background: #fdf2f8; color: #db2777; border-color: #fbcfe8; }
.pill--proc-weld { background: #fff7ed; color: #ea580c; border-color: #fed7aa; }
.pill--proc-inspect { background: #f0fdf4; color: #16a34a; border-color: #bbf7d0; }
.pill--proc-other { background: #f8fafc; color: #64748b; border-color: #e2e8f0; }

.row-actions { display: flex; justify-content: center; gap: 2px; }
.act-btn { padding: 4px !important; border-radius: 6px; transition: background 0.15s; }
.act-edit { color: #2563eb !important; }
.act-edit:hover { background: #eff6ff !important; }
.act-del { color: #dc2626 !important; }
.act-del:hover { background: #fef2f2 !important; }

.pagination-bar {
  display: flex;
  justify-content: flex-end;
  margin-top: 6px;
  padding-top: 4px;
}

.pagination-bar :deep(.el-pagination) {
  --el-pagination-bg-color: #ffffff;
  --el-pagination-text-color: #475569;
  --el-pagination-button-color: #475569;
  --el-pagination-hover-color: #2563eb;
}

/* ===== 编辑对话框 ===== */
.ctrl-full { width: 100%; }

.edit-form {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.edit-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.edit-form :deep(.el-form-item__label) {
  font-size: 10px;
  font-weight: 700;
  color: #64748b;
  padding-bottom: 2px;
  line-height: 1.2;
}

.block-field-no-margin { margin-bottom: 0 !important; }

.form-block {
  border-radius: 10px;
  padding: 7px 10px 8px;
  background: #ffffff;
  border: 1px solid #e8edf3;
  box-shadow:
    0 2px 8px rgba(15, 23, 42, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}

.form-block:hover {
  box-shadow:
    0 4px 14px rgba(15, 23, 42, 0.09),
    inset 0 1px 0 rgba(255, 255, 255, 0.95);
}

.form-block--basic {
  border-left: 3px solid #3b82f6;
  background: linear-gradient(135deg, #ffffff 0%, #f8fbff 100%);
}

.form-block--category {
  border-left: 3px solid #ef4444;
  background: linear-gradient(135deg, #ffffff 0%, #fff8f8 100%);
}

.form-block--process {
  border-left: 3px solid #8b5cf6;
  background: linear-gradient(135deg, #ffffff 0%, #faf8ff 100%);
}

.form-block--product {
  border-left: 3px solid #0ea5e9;
  background: linear-gradient(135deg, #ffffff 0%, #f5fbff 100%);
}

.form-block--status {
  border-left: 3px solid #f59e0b;
}

.form-block--pending {
  background: linear-gradient(135deg, #ffffff 0%, #fffbeb 100%);
  border-left-color: #f59e0b;
}

.form-block--done {
  background: linear-gradient(135deg, #ffffff 0%, #ecfdf5 100%);
  border-left-color: #10b981;
}

.form-block--remarks {
  border-left: 3px solid #94a3b8;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
}

.form-block--deadline {
  border-left: 3px solid #f97316;
  background: linear-gradient(135deg, #ffffff 0%, #fff7ed 100%);
}

.block-head-hint {
  margin-left: auto;
  font-size: 10px;
  font-weight: 600;
  color: #ea580c;
}

.deadline-picker {
  width: 160px;
  max-width: 100%;
}

.block-head {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-bottom: 6px;
  font-size: 11px;
  font-weight: 800;
  color: #334155;
  letter-spacing: 0.02em;
}

.block-head .el-icon {
  font-size: 13px;
  color: #64748b;
}

.block-body {
  display: grid;
  gap: 6px;
}

.block-body--3col {
  grid-template-columns: 1.1fr 0.85fr 0.75fr;
  gap: 8px;
  align-items: start;
}

.block-body--status {
  grid-template-columns: auto 1fr;
  gap: 8px;
  align-items: end;
}

.status-field { min-width: 0; }

.processed-date-field {
  min-width: 0;
}

.mgmt-no-item :deep(.el-form-item__content) {
  flex: 0 0 auto;
}

.mgmt-no-input {
  width: calc(13ch + 28px);
  max-width: 100%;
}

.mgmt-no-input :deep(.el-input__inner) {
  font-family: ui-monospace, 'Consolas', monospace;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.05em;
  font-weight: 600;
}

.qty-item :deep(.el-form-item__content) {
  flex: 0 0 auto;
}

.qty-input {
  width: calc(5ch + 28px);
  max-width: 100%;
}

.qty-input :deep(.el-input__inner) {
  font-family: ui-monospace, 'Consolas', monospace;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.05em;
  font-weight: 700;
  color: #b45309;
  text-align: right;
}

/* 彩色选择 Chip */
.chip-row {
  display: flex;
  gap: 5px;
  flex-wrap: nowrap;
}

.chip-row--wrap {
  flex-wrap: wrap;
}

.pick-chip {
  padding: 4px 11px;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 700;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  color: #64748b;
  cursor: pointer;
  transition: all 0.18s cubic-bezier(0.22, 1, 0.36, 1);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  white-space: nowrap;
}

.pick-chip--sm {
  padding: 3px 8px;
  font-size: 10px;
  border-radius: 6px;
}

.pick-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 3px 8px rgba(15, 23, 42, 0.1);
}

.pick-chip--active {
  color: #fff !important;
  border-color: transparent !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.18);
}

.pick-chip--cat-disposal.pick-chip--active {
  background: linear-gradient(135deg, #ef4444, #dc2626);
}

.pick-chip--cat-hold.pick-chip--active {
  background: linear-gradient(135deg, #f59e0b, #d97706);
}

.pick-chip--cat-other.pick-chip--active {
  background: linear-gradient(135deg, #64748b, #475569);
}

.pick-chip--proc-cut.pick-chip--active { background: linear-gradient(135deg, #3b82f6, #2563eb); }
.pick-chip--proc-chamfer.pick-chip--active { background: linear-gradient(135deg, #0ea5e9, #0284c7); }
.pick-chip--proc-form.pick-chip--active { background: linear-gradient(135deg, #8b5cf6, #7c3aed); }
.pick-chip--proc-plate.pick-chip--active { background: linear-gradient(135deg, #ec4899, #db2777); }
.pick-chip--proc-weld.pick-chip--active { background: linear-gradient(135deg, #f97316, #ea580c); }
.pick-chip--proc-inspect.pick-chip--active { background: linear-gradient(135deg, #22c55e, #16a34a); }
.pick-chip--proc-other.pick-chip--active { background: linear-gradient(135deg, #94a3b8, #64748b); }

.pick-chip--status-pending.pick-chip--active {
  background: linear-gradient(135deg, #f59e0b, #ea580c);
}

.pick-chip--status-done.pick-chip--active {
  background: linear-gradient(135deg, #10b981, #059669);
}

.edit-form :deep(.el-input__wrapper),
.edit-form :deep(.el-select__wrapper),
.edit-form :deep(.el-textarea__inner) {
  border-radius: 7px;
  box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.04);
  transition: border-color 0.15s, box-shadow 0.15s;
}

.edit-form :deep(.el-input__wrapper:hover),
.edit-form :deep(.el-select__wrapper:hover) {
  box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.04), 0 0 0 2px rgba(59, 130, 246, 0.1);
}

.notify-body { min-height: 100px; }

.notify-hero {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 16px;
  margin-bottom: 12px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.12), rgba(239, 68, 68, 0.08));
  border: 1px solid rgba(245, 158, 11, 0.25);
}

.notify-hero--warn {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.08), rgba(239, 68, 68, 0.05));
  border-color: rgba(245, 158, 11, 0.2);
}

.notify-hero-stat {
  display: flex;
  align-items: baseline;
  gap: 2px;
  flex-shrink: 0;
}

.notify-hero-num {
  font-size: 36px;
  font-weight: 800;
  line-height: 1;
  background: linear-gradient(135deg, #f59e0b, #ef4444);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.notify-hero-unit { font-size: 14px; font-weight: 600; color: #94a3b8; }

.notify-hero-meta p { margin: 0 0 4px; font-size: 13px; color: #475569; }
.notify-hint { font-size: 11px !important; color: #94a3b8 !important; }
.notify-deadline-warn {
  margin: 0 0 4px !important;
  font-size: 13px !important;
  font-weight: 700 !important;
  color: #dc2626 !important;
}
.notify-deadline-detail { margin: 4px 0 0; font-size: 12px; line-height: 1.5; }
.notify-alert { margin-bottom: 10px; }
.notify-alert--deadline { border-radius: 8px; }
.notify-form { margin-top: 4px; }
.notify-table { margin-top: 8px; border-radius: 8px; overflow: hidden; }

@media (max-width: 1100px) {
  .filter-grid { grid-template-columns: repeat(3, 1fr); }
  .filter-item.span-2 { grid-column: span 3; }
}

@media (max-width: 768px) {
  .top-bar { flex-direction: column; align-items: stretch; }
  .top-bar-stats { justify-content: space-between; }
  .top-bar-actions { justify-content: flex-end; }
  .filter-grid { grid-template-columns: 1fr 1fr; }
  .filter-item.span-2 { grid-column: span 2; }
  .block-body--3col { grid-template-columns: 1fr; }
  .block-body--status { grid-template-columns: 1fr; }
}
</style>

<style>
/* 对话框全局（append-to-body） */
.bdr-dialog .el-dialog {
  border-radius: 14px;
  overflow: hidden;
  box-shadow:
    0 20px 50px rgba(15, 23, 42, 0.28),
    0 0 0 1px rgba(255, 255, 255, 0.08);
}

.bdr-dialog .el-dialog__header {
  padding: 0;
  margin: 0;
  background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.bdr-dialog .el-dialog__headerbtn {
  top: 12px;
  right: 12px;
  width: 28px;
  height: 28px;
}

.bdr-dialog .el-dialog__headerbtn .el-dialog__close {
  color: rgba(255, 255, 255, 0.65);
  font-size: 16px;
}

.bdr-dialog .el-dialog__headerbtn:hover .el-dialog__close {
  color: #fff;
}

.bdr-dialog .el-dialog__body {
  padding: 10px 12px 6px;
  background: linear-gradient(180deg, #f1f5f9 0%, #e8edf3 100%);
}

.bdr-dialog .el-dialog__footer {
  padding: 8px 12px 12px;
  background: #f1f5f9;
  border-top: 1px solid #e2e8f0;
}

/* 编辑窗体头部 */
.dlg-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 40px 12px 14px;
}

.dlg-header-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.dlg-header-icon--new {
  background: linear-gradient(135deg, #3b82f6, #6366f1);
}

.dlg-header-icon--edit {
  background: linear-gradient(135deg, #f59e0b, #ef4444);
}

.dlg-header-text {
  flex: 1;
  min-width: 0;
}

.dlg-title {
  margin: 0;
  font-size: 15px;
  font-weight: 800;
  color: #f8fafc;
  letter-spacing: -0.01em;
  line-height: 1.2;
}

.dlg-subtitle {
  margin: 2px 0 0;
  font-size: 10px;
  color: rgba(255, 255, 255, 0.5);
  font-weight: 500;
}

.dlg-badge {
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 0.08em;
  flex-shrink: 0;
}

.dlg-badge--new {
  background: rgba(59, 130, 246, 0.25);
  color: #93c5fd;
  border: 1px solid rgba(59, 130, 246, 0.4);
}

.dlg-badge--edit {
  background: rgba(245, 158, 11, 0.2);
  color: #fcd34d;
  border: 1px solid rgba(245, 158, 11, 0.35);
}

/* 编辑窗体底部 */
.dlg-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.dlg-btn {
  border-radius: 8px;
  font-weight: 700;
  font-size: 12px;
  padding: 7px 16px;
  height: auto;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.dlg-btn:hover {
  transform: translateY(-1px);
}

.dlg-btn--cancel {
  background: #fff;
  border: 1px solid #e2e8f0;
  color: #64748b;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
}

.dlg-btn--save {
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  border: none;
  box-shadow: 0 4px 14px rgba(59, 130, 246, 0.4);
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.bdr-dialog--notify .el-dialog__header {
  padding: 14px 18px 10px;
}

.bdr-dialog--notify .el-dialog__title {
  color: #f8fafc;
  font-weight: 700;
  font-size: 15px;
}

.bdr-dialog--notify .el-dialog__body {
  padding: 14px 18px 8px;
  background: #fff;
}
</style>
