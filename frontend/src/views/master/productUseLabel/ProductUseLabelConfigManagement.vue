<template>
  <div class="pul-page">
    <header class="pul-hero">
      <div class="pul-hero-inner">
        <div class="pul-title-row">
          <span class="pul-title-icon"><el-icon :size="20"><Tickets /></el-icon></span>
          <div>
            <h1 class="pul-title">製品用ラベル設定</h1>
            <p class="pul-subtitle">
              B4横向・通常4×5枚／東北INOAC向け4×4枚。製品マスタから取込後、背番号・バーコード等を編集して印刷します。
            </p>
            <div class="pul-hero-badges">
              <span class="pul-hero-badge">B4 横向 4×5</span>
              <span class="pul-hero-badge pul-hero-badge--inoac">東北INOAC 4×4</span>
            </div>
          </div>
        </div>
        <div class="pul-stat">
          <span class="pul-stat-num">{{ pagination.total }}</span>
          <span class="pul-stat-lbl">登録件数</span>
        </div>
      </div>
    </header>

    <section class="pul-toolbar-card">
      <div class="pul-toolbar">
        <div class="pul-filters">
          <div class="pul-filter-field pul-filter-field--search">
            <label class="pul-field-label">
              <el-icon :size="14"><Search /></el-icon>
              キーワード検索
            </label>
            <el-input
              v-model="filters.keyword"
              placeholder="製品CD・製品名・品番・納入先"
              clearable
              size="small"
              class="pul-search"
              @input="onKeywordInput"
              @clear="onKeywordClear"
            />
          </div>
          <div class="pul-filter-field">
            <label class="pul-field-label">製品</label>
            <el-select
              v-model="filters.product_cd"
              placeholder="すべて"
              clearable
              filterable
              size="small"
              class="pul-filter"
              :loading="loadingFilterOptions"
              @change="onFilterChange"
            >
              <el-option
                v-for="p in filterProductOptions"
                :key="p.product_cd"
                :label="`${p.product_cd} — ${p.product_name || '—'}`"
                :value="p.product_cd"
              />
            </el-select>
          </div>
          <div class="pul-filter-field">
            <label class="pul-field-label">納入先</label>
            <el-select
              v-model="filters.destination_name"
              placeholder="すべて"
              clearable
              filterable
              size="small"
              class="pul-filter pul-filter--dest"
              :loading="loadingFilterOptions"
              @change="onFilterChange"
            >
              <el-option v-for="d in filterDestinationOptions" :key="d" :label="d" :value="d" />
            </el-select>
          </div>
        </div>
        <div class="pul-toolbar-actions">
          <el-button size="small" class="pul-btn pul-btn--refresh" :icon="Refresh" @click="reloadPage">
            再読込
          </el-button>
          <el-button
            size="small"
            class="pul-btn pul-btn--print"
            :icon="Printer"
            :loading="printingAll"
            :disabled="pagination.total === 0"
            @click="openPrintAllDialog"
          >
            一括印刷
          </el-button>
          <el-button
            v-if="canEdit"
            size="small"
            class="pul-btn pul-btn--outsource"
            :icon="Message"
            @click="openOutsourceOrderDialog"
          >
            外注注文
          </el-button>
          <el-button
            v-if="canEdit"
            size="small"
            class="pul-btn pul-btn--sync"
            :icon="Download"
            :loading="syncing"
            @click="handleSyncFromMaster"
          >
            マスタ取込
          </el-button>
          <el-button
            v-if="canCreate"
            size="small"
            class="pul-btn pul-btn--create"
            :icon="Plus"
            @click="openDialog()"
          >
            新規登録
          </el-button>
        </div>
      </div>
    </section>

    <section ref="tableWrapRef" class="pul-table-wrap">
      <div class="pul-result-bar">
        <span class="pul-result-text">{{ pagination.total }} 件中 {{ list.length }} 件を表示</span>
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[20, 50, 100]"
          :layout="paginationLayout"
          size="small"
          background
          @current-change="loadList"
          @size-change="loadList"
        />
      </div>

      <el-table
        v-loading="loading"
        :data="list"
        stripe
        size="small"
        class="pul-table"
        :header-cell-style="headerCellStyle"
        :default-sort="{ prop: 'master_product_name', order: 'ascending' }"
        :height="tableHeight"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="product_cd" label="製品CD" width="72" :fixed="tableFixed" show-overflow-tooltip />
        <el-table-column
          prop="master_product_name"
          label="製品名（マスタ）"
          width="150"
          sortable="custom"
          show-overflow-tooltip
        />
        <el-table-column label="製品用製品名" width="160" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="pul-readonly-val">{{ row.use_label_product_name || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="入数" width="56" align="center">
          <template #default="{ row }">
            <span class="pul-readonly-val">{{ row.unit_qty ?? '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="区分" width="96" align="center">
          <template #default="{ row }">
            <el-switch
              :model-value="normalizeSupplyType(row.supply_type) === '外注'"
              :disabled="!canEdit"
              size="small"
              inline-prompt
              active-text="外注"
              inactive-text="社内"
              @change="(val: boolean) => handleSupplyTypeChange(row, val)"
            />
          </template>
        </el-table-column>
        <el-table-column label="品番" width="120" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="pul-readonly-val">{{ row.part_no || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="納入先名" width="160" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="pul-readonly-val">{{ row.destination_name || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="用紙色" width="118" align="center">
          <template #default="{ row }">
            <div class="pul-table-color-cell">
              <span class="pul-paper-chip" :style="paperChipStyle(row.paper_color)">
                {{ row.paper_color || '白' }}
              </span>
              <el-select
                v-if="canEdit"
                :model-value="row.paper_color || '白'"
                size="small"
                class="pul-table-color-select"
                @change="(val: string) => saveInlineField(row, { paper_color: val })"
              >
                <el-option v-for="c in PAPER_COLOR_OPTIONS" :key="c" :label="c" :value="c">
                  <span class="pul-opt-paper" :style="paperChipStyle(c)">{{ c }}</span>
                </el-option>
              </el-select>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="製品名色" width="128" align="center">
          <template #default="{ row }">
            <div class="pul-table-color-cell">
              <span class="pul-name-color-preview">
                <span class="pul-color-dot" :style="{ background: normalizeNameColor(row.product_name_color) }" />
                <span>{{ productNameColorLabel(row.product_name_color) }}</span>
              </span>
              <el-select
                v-if="canEdit"
                :model-value="normalizeNameColor(row.product_name_color)"
                size="small"
                class="pul-table-color-select"
                @change="(val: string) => saveInlineField(row, { product_name_color: val })"
              >
                <el-option
                  v-for="c in PRODUCT_NAME_COLOR_OPTIONS"
                  :key="c.value"
                  :label="c.label"
                  :value="c.value"
                >
                  <span class="pul-opt-color">
                    <span class="pul-color-dot" :style="{ background: c.value }" />
                    {{ c.label }}
                  </span>
                </el-option>
              </el-select>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="背番1" width="72" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="pul-readonly-val">{{ row.back_no_1 || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="背番2" width="72" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="pul-readonly-val">{{ row.back_no_2 || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="背番3" width="72" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="pul-readonly-val">{{ row.back_no_3 || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="バーコード" width="88" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="pul-readonly-val pul-readonly-val--mono">{{ row.barcode_no || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="終息" width="64" align="center" :fixed="tableFixedRight">
          <template #default="{ row }">
            <el-tag
              v-if="row.is_discontinued"
              type="info"
              size="small"
              effect="plain"
              class="pul-discontinued-tag"
            >
              終息
            </el-tag>
            <span v-else class="pul-readonly-val">—</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="168" :fixed="tableFixedRight" align="center">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openDialog(row)">編集</el-button>
            <el-button
              link
              type="success"
              size="small"
              :loading="printing && printingCd === row.product_cd"
              @click="openPrintDialog(row)"
            >
              印刷
            </el-button>
            <el-button
              v-if="canDelete"
              link
              type="danger"
              size="small"
              @click="handleDelete(row)"
            >
              削除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '製品用ラベル編集' : '製品用ラベル新規登録'"
      :width="editDialogWidth"
      destroy-on-close
      class="pul-dialog"
    >
      <el-form label-position="top" class="pul-edit-form" size="small">
        <div class="pul-edit-section pul-edit-section--accent">
          <div class="pul-edit-section-title">基本情報</div>
          <div class="pul-edit-grid">
            <el-form-item label="製品CD" class="pul-span-full" required>
              <el-select
                v-model="form.product_cd"
                filterable
                :disabled="isEdit"
                placeholder="製品を選択"
                style="width: 100%"
                :loading="loadingProducts"
                @change="onProductCdChange"
              >
                <el-option
                  v-for="p in productOptions"
                  :key="p.product_cd"
                  :label="`${p.product_cd} — ${p.product_name}`"
                  :value="p.product_cd"
                  :disabled="!isEdit && p.configured"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="製品名（マスタ）">
              <el-input :model-value="masterInfo.product_name || '—'" readonly />
            </el-form-item>
            <el-form-item label="製品用製品名">
              <el-input v-model="form.use_label_product_name" placeholder="ラベル印字用の製品名" />
            </el-form-item>
          </div>
        </div>

        <div class="pul-edit-section">
          <div class="pul-edit-section-title pul-edit-section-title--row">
            <span>マスタ参照</span>
            <el-tag v-if="formInoacLayout" type="warning" size="small" effect="plain" class="pul-inoac-tag">
              B4 4×4
            </el-tag>
          </div>
          <div class="pul-edit-grid pul-edit-grid--3">
            <el-form-item label="入数">
              <el-input :model-value="formatMasterQty(form.unit_qty)" readonly />
            </el-form-item>
            <el-form-item label="品番">
              <el-input :model-value="form.part_no || '—'" readonly />
            </el-form-item>
            <el-form-item label="納入先名" class="pul-span-full pul-span-full--sm">
              <el-input :model-value="form.destination_name || '—'" readonly />
            </el-form-item>
          </div>
          <p class="pul-edit-hint">
            入数・品番・納入先は製品マスタから自動取得（マスタ取込で更新）
            <template v-if="formInoacLayout"> · この納入先は 4×4 レイアウトで印刷</template>
          </p>
        </div>

        <div class="pul-edit-section">
          <div class="pul-edit-section-title">印刷設定</div>
          <div class="pul-edit-grid">
            <el-form-item label="区分">
              <el-select v-model="form.supply_type" placeholder="区分を選択" style="width: 100%">
                <el-option v-for="t in SUPPLY_TYPE_OPTIONS" :key="t" :label="t" :value="t" />
              </el-select>
            </el-form-item>
            <el-form-item label="用紙色（確認用）">
              <el-select v-model="form.paper_color" placeholder="用紙色" style="width: 100%">
                <el-option v-for="c in PAPER_COLOR_OPTIONS" :key="c" :label="c" :value="c">
                  <span class="pul-opt-paper" :style="paperChipStyle(c)">{{ c }}</span>
                </el-option>
              </el-select>
            </el-form-item>
            <el-form-item label="製品名色">
              <el-select v-model="form.product_name_color" placeholder="文字色" style="width: 100%">
                <el-option
                  v-for="c in PRODUCT_NAME_COLOR_OPTIONS"
                  :key="c.value"
                  :label="c.label"
                  :value="c.value"
                >
                  <span class="pul-opt-color">
                    <span class="pul-color-dot" :style="{ background: c.value }" />
                    {{ c.label }}
                  </span>
                </el-option>
              </el-select>
            </el-form-item>
          </div>
          <p class="pul-edit-hint">用紙色は印刷時に実用紙の色を確認するための設定です（ラベル背景には印字されません）</p>
        </div>

        <div class="pul-edit-section">
          <div class="pul-edit-section-title">手入力</div>
          <div class="pul-edit-grid pul-edit-grid--3">
            <el-form-item label="背番号1">
              <el-input v-model="form.back_no_1" placeholder="任意" />
            </el-form-item>
            <el-form-item label="背番号2">
              <el-input v-model="form.back_no_2" placeholder="任意" />
            </el-form-item>
            <el-form-item label="背番号3">
              <el-input v-model="form.back_no_3" placeholder="任意" />
            </el-form-item>
          </div>
          <el-form-item label="バーコード番号" class="pul-span-full">
            <el-input v-model="form.barcode_no" placeholder="任意" />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <div class="pul-dialog-footer">
          <el-button size="small" class="pul-btn-cancel" @click="dialogVisible = false">キャンセル</el-button>
          <el-button
            v-if="isEdit && canEdit"
            size="small"
            class="pul-btn-secondary"
            :loading="prefilling"
            @click="handleImportFromMaster"
          >
            マスタ再取込
          </el-button>
          <el-button size="small" type="primary" class="pul-btn-save" :loading="submitting" @click="handleSubmit">
            {{ isEdit ? '更新' : '登録' }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog
      v-model="printDialogVisible"
      title="製品用ラベル印刷"
      :width="printDialogWidth"
      destroy-on-close
      class="pul-print-dialog"
    >
      <div v-if="printTarget" class="pul-print-body">
        <div class="pul-print-product">
          <span class="pul-print-cd">{{ printTarget.product_cd }}</span>
          <strong>{{ printTarget.use_label_product_name || printTarget.master_product_name }}</strong>
          <span class="pul-print-layout">
            {{ printTarget.is_inoac_layout ? 'B4 横向 4×4（東北INOAC）' : 'B4 横向 4×5（標準）' }}
          </span>
        </div>
        <div class="pul-print-settings">
          <div class="pul-print-settings-row">
            <div class="pul-print-settings-item">
              <span class="pul-print-settings-label">用紙色</span>
              <span class="pul-paper-chip pul-print-paper-val" :style="paperChipStyle(printTarget.paper_color)">
                {{ printTarget.paper_color || '白' }}
              </span>
            </div>
            <div class="pul-print-settings-item">
              <span class="pul-print-settings-label">製品名色</span>
              <span class="pul-print-name-color">
                <span
                  class="pul-color-dot"
                  :style="{ background: normalizeNameColor(printTarget.product_name_color) }"
                />
                {{ productNameColorLabel(printTarget.product_name_color) }}
              </span>
            </div>
          </div>
        </div>
        <el-form label-width="100px" size="small">
          <el-form-item label="印刷枚数">
            <el-input-number v-model="printPages" :min="1" :max="50" />
            <span class="pul-print-hint">B4用紙 1枚あたり {{ printPerPage }} 枚（満版）</span>
          </el-form-item>
        </el-form>
        <p class="pul-print-note">用紙色は実用紙の確認用です。製品名色をご確認のうえ、印刷を開始してください。</p>
      </div>
      <template #footer>
        <div class="pul-dialog-footer">
          <el-button size="small" class="pul-btn-cancel" @click="printDialogVisible = false">キャンセル</el-button>
          <el-button size="small" type="primary" class="pul-btn-save" :loading="printing" @click="handlePrint">
            印刷開始
          </el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog
      v-model="printAllDialogVisible"
      title="一括ラベル印刷"
      width="420px"
      destroy-on-close
      class="pul-print-dialog pul-print-dialog--all"
    >
      <p class="pul-print-all-lead">
        一覧の全 <strong>{{ printAllCount }}</strong> 件を、納入先ごとのレイアウト（4×5／4×4）で印刷します。
      </p>
      <el-form label-width="100px" size="small">
        <el-form-item label="印刷枚数">
          <el-input-number v-model="printAllPages" :min="1" :max="20" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="pul-dialog-footer">
          <el-button size="small" class="pul-btn-cancel" @click="printAllDialogVisible = false">キャンセル</el-button>
          <el-button size="small" type="primary" class="pul-btn-save" :loading="printingAll" @click="handlePrintAll">
            印刷開始
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 外注注文ダイアログ -->
    <el-dialog
      v-model="outsourceDialogVisible"
      title="外注製品用ラベル注文"
      :width="outsourceDialogWidth"
      destroy-on-close
      class="pul-dialog pul-outsource-dialog"
    >
      <div v-loading="outsourceLoading" class="pul-outsource-body">
        <p class="pul-outsource-lead">
          区分が<strong>外注</strong>の製品のみ表示。注文数を入力し、メールで注文一覧とラベルPDFを送信できます。
        </p>
        <el-table :data="outsourceOrderRows" stripe border size="small" max-height="360" class="pul-outsource-table">
          <el-table-column prop="product_cd" label="製品CD" width="88" show-overflow-tooltip />
          <el-table-column prop="use_label_product_name" label="製品用製品名" min-width="160" show-overflow-tooltip />
          <el-table-column label="入数" width="72" align="center">
            <template #default="{ row }">{{ row.unit_qty ?? '—' }}</template>
          </el-table-column>
          <el-table-column label="用紙色" width="100" align="center">
            <template #default="{ row }">
              <span class="pul-paper-chip" :style="paperChipStyle(row.paper_color)">
                {{ row.paper_color || '白' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="注文数" width="120" align="center">
            <template #default="{ row }">
              <el-input-number
                v-model="row.order_qty"
                :min="0"
                :max="99999"
                :controls="true"
                size="small"
                style="width: 100%"
              />
            </template>
          </el-table-column>
        </el-table>

        <div class="pul-outsource-mail">
          <div class="pul-outsource-mail-head">
            <span>メール送信</span>
            <span v-if="outsourceOrderSendCount > 0" class="pul-outsource-mail-stat">
              送信対象 {{ outsourceOrderSendCount }} 件 / ラベルPDF 約 {{ outsourceLabelPdfCount }} 枚
            </span>
          </div>
          <el-alert
            v-if="outsourceEmailPreview && !outsourceEmailPreview.can_send"
            type="warning"
            :closable="false"
            show-icon
            title="メール送信の準備ができていません（SMTP・テンプレート・通知設定を確認）"
            class="pul-outsource-alert"
          />
          <el-form label-width="88px" size="small" class="pul-outsource-form">
            <el-form-item label="送信先" required>
              <el-select
                v-model="outsourceUserIds"
                multiple
                filterable
                collapse-tags
                collapse-tags-tooltip
                placeholder="ユーザーを選択"
                style="width: 100%"
              >
                <el-option
                  v-for="u in outsourceUsers"
                  :key="u.id"
                  :label="`${u.full_name || u.username} (${u.email || 'メール未設定'})`"
                  :value="u.id"
                  :disabled="!u.email"
                />
              </el-select>
            </el-form-item>
          </el-form>
        </div>
      </div>
      <template #footer>
        <div class="pul-dialog-footer">
          <el-button size="small" class="pul-btn-cancel" @click="outsourceDialogVisible = false">閉じる</el-button>
          <el-button
            size="small"
            class="pul-btn pul-btn--outsource"
            :icon="Message"
            :loading="outsourceSending"
            :disabled="!canSendOutsourceEmail"
            @click="sendOutsourceOrderEmail"
          >
            メール送信
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, Message, Plus, Printer, Refresh, Search, Tickets } from '@element-plus/icons-vue'
import {
  PAPER_COLOR_OPTIONS,
  PRODUCT_NAME_COLOR_OPTIONS,
  SUPPLY_TYPE_OPTIONS,
  createProductUseLabelConfig,
  deleteProductUseLabelConfig,
  fetchAvailableProductsForUseLabel,
  fetchOutsourceUseLabelOrderEmailPreview,
  fetchOutsourceUseLabelOrders,
  fetchProductUseLabelConfigList,
  fetchProductUseLabelFilterOptions,
  fetchProductUseLabelPrefill,
  importProductUseLabelFromMaster,
  productNameColorLabel,
  sendOutsourceUseLabelOrderEmail,
  syncProductUseLabelFromMaster,
  updateProductUseLabelConfig,
  type AvailableProductForUseLabel,
  type OutsourceOrderEmailPreview,
  type ProductUseLabelConfig,
  type ProductUseLabelFilterProduct,
} from '@/api/master/productUseLabelConfig'
import { getUsers, type UserListItem } from '@/api/system'
import {
  configToPrintInput,
  isInoacDestination,
  printProductUseLabels,
} from '@/views/master/productUseLabel/utils/productUseLabelPrint'
import {
  buildUseLabelEmailAttachments,
  estimateUseLabelPdfPages,
} from '@/views/master/productUseLabel/utils/productUseLabelOutsourceOrderPdf'
import { recordLabelQuantityPrint } from '@/api/master/labelQuantity'
import { useMasterOperationPermission } from '@/composables/useMasterOperationPermission'
import { guardMasterOperation } from '@/utils/masterOperationGuard'

const { canCreate, canEdit, canDelete } = useMasterOperationPermission()

const headerCellStyle = {
  background: 'linear-gradient(180deg, #eef2ff 0%, #e0e7ff 100%)',
  color: '#3730a3',
  fontWeight: '700',
  fontSize: '12px',
  padding: '6px 0',
}

const PAPER_CHIP_STYLES: Record<string, { background: string; border: string; color: string }> = {
  白: { background: '#fff', border: '#cbd5e1', color: '#334155' },
  黄: { background: '#fef9c3', border: '#eab308', color: '#854d0e' },
  ピンク: { background: '#fce7f3', border: '#ec4899', color: '#9d174d' },
  緑: { background: '#dcfce7', border: '#22c55e', color: '#166534' },
  青: { background: '#dbeafe', border: '#3b82f6', color: '#1e40af' },
  オレンジ: { background: '#ffedd5', border: '#f97316', color: '#9a3412' },
}

const loading = ref(false)
const loadingFilterOptions = ref(false)
const submitting = ref(false)
const syncing = ref(false)
const prefilling = ref(false)
const loadingProducts = ref(false)
const printing = ref(false)
const printingCd = ref('')
const printingAll = ref(false)
const dialogVisible = ref(false)
const printDialogVisible = ref(false)
const printAllDialogVisible = ref(false)
const isEdit = ref(false)
const list = ref<ProductUseLabelConfig[]>([])
const availableProducts = ref<AvailableProductForUseLabel[]>([])
const filterProductOptions = ref<ProductUseLabelFilterProduct[]>([])
const filterDestinationOptions = ref<string[]>([])
const printTarget = ref<ProductUseLabelConfig | null>(null)
const printPages = ref(1)
const printAllPages = ref(1)
const printAllRows = ref<ProductUseLabelConfig[]>([])
const printAllCount = computed(() => printAllRows.value.length)

type OutsourceOrderRow = {
  product_cd: string
  use_label_product_name: string
  unit_qty: number | null
  paper_color: string
  order_qty: number
  config: ProductUseLabelConfig
}

const outsourceDialogVisible = ref(false)
const outsourceLoading = ref(false)
const outsourceSending = ref(false)
const outsourceOrderRows = ref<OutsourceOrderRow[]>([])
const outsourceEmailPreview = ref<OutsourceOrderEmailPreview | null>(null)
const outsourceUserIds = ref<number[]>([])
const outsourceUsers = ref<UserListItem[]>([])

const tableWrapRef = ref<HTMLElement | null>(null)
const tableHeight = ref(480)
const viewportWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1280)

const tableFixed = computed<'left' | false>(() => (viewportWidth.value >= 900 ? 'left' : false))
const tableFixedRight = computed<'right' | false>(() => (viewportWidth.value >= 900 ? 'right' : false))
const paginationLayout = computed(() =>
  viewportWidth.value < 768 ? 'prev, pager, next' : 'sizes, prev, pager, next'
)
const editDialogWidth = computed(() => (viewportWidth.value < 768 ? 'min(680px, 96vw)' : '680px'))
const printDialogWidth = computed(() => (viewportWidth.value < 480 ? 'min(400px, 96vw)' : '420px'))
const outsourceDialogWidth = computed(() => (viewportWidth.value < 768 ? 'min(900px, 96vw)' : '900px'))

const outsourceOrderSendRows = computed(() =>
  outsourceOrderRows.value.filter((row) => (row.order_qty || 0) > 0)
)
const outsourceOrderSendCount = computed(() => outsourceOrderSendRows.value.length)
const outsourceLabelPdfCount = computed(() =>
  outsourceOrderSendCount.value > 0
    ? estimateUseLabelPdfPages(outsourceOrderSendRows.value.map((r) => r.config))
    : 0
)
const canSendOutsourceEmail = computed(
  () =>
    !!outsourceEmailPreview.value?.can_send &&
    outsourceOrderSendCount.value > 0 &&
    outsourceUserIds.value.length > 0 &&
    !outsourceSending.value
)

const printPerPage = computed(() => (printTarget.value?.is_inoac_layout ? 16 : 20))

const filters = reactive({ keyword: '', product_cd: '', destination_name: '' })
const pagination = reactive({ page: 1, pageSize: 50, total: 0 })
const sortConfig = reactive({ prop: 'master_product_name', order: 'asc' as 'asc' | 'desc' })

const masterInfo = reactive({ product_name: '' })

const form = reactive({
  id: undefined as number | undefined,
  product_cd: '',
  use_label_product_name: '',
  unit_qty: null as number | null,
  supply_type: '社内' as string,
  part_no: '',
  destination_name: '',
  paper_color: '白',
  product_name_color: '#000000',
  back_no_1: '',
  back_no_2: '',
  back_no_3: '',
  barcode_no: '',
})

const formInoacLayout = computed(() => isInoacDestination(form.destination_name))

const productOptions = computed(() => {
  if (isEdit.value) {
    return availableProducts.value.length
      ? availableProducts.value
      : [{ product_cd: form.product_cd, product_name: masterInfo.product_name, configured: true }]
  }
  return availableProducts.value.filter((p) => !p.configured)
})

let keywordTimer: ReturnType<typeof setTimeout> | null = null

function paperChipStyle(color?: string | null) {
  const s = PAPER_CHIP_STYLES[color || '白'] || PAPER_CHIP_STYLES['白']
  return { background: s.background, border: `1px solid ${s.border}`, color: s.color }
}

function formatMasterQty(qty: number | null | undefined): string {
  if (qty == null) return '—'
  return String(qty)
}

function normalizeNameColor(hex?: string | null): string {
  const v = (hex || '#000000').toLowerCase()
  const found = PRODUCT_NAME_COLOR_OPTIONS.find((o) => o.value.toLowerCase() === v)
  return found?.value ?? '#000000'
}

function normalizeSupplyType(value?: string | null): string {
  const v = (value || '社内').trim()
  return SUPPLY_TYPE_OPTIONS.includes(v as (typeof SUPPLY_TYPE_OPTIONS)[number]) ? v : '社内'
}

function handleSupplyTypeChange(row: ProductUseLabelConfig, isOutsource: boolean) {
  void saveInlineField(row, { supply_type: isOutsource ? '外注' : '社内' })
}

function onKeywordInput() {
  if (keywordTimer) clearTimeout(keywordTimer)
  keywordTimer = setTimeout(() => {
    pagination.page = 1
    void loadList()
  }, 350)
}

function onKeywordClear() {
  if (keywordTimer) clearTimeout(keywordTimer)
  pagination.page = 1
  void loadList()
}

function onFilterChange() {
  pagination.page = 1
  void loadList()
}

function listQueryParams(page = pagination.page, pageSize = pagination.pageSize) {
  return {
    keyword: filters.keyword || undefined,
    product_cd: filters.product_cd || undefined,
    destination_name: filters.destination_name || undefined,
    page,
    page_size: pageSize,
    sort_by: sortConfig.prop,
    sort_order: sortConfig.order,
  }
}

function handleSortChange(payload: { prop: string; order: 'ascending' | 'descending' | null }) {
  if (!payload.order) {
    sortConfig.prop = 'master_product_name'
    sortConfig.order = 'asc'
  } else {
    sortConfig.prop = payload.prop || 'master_product_name'
    sortConfig.order = payload.order === 'descending' ? 'desc' : 'asc'
  }
  pagination.page = 1
  void loadList()
}

function resetForm() {
  form.id = undefined
  form.product_cd = ''
  form.use_label_product_name = ''
  form.unit_qty = null
  form.supply_type = '社内'
  form.part_no = ''
  form.destination_name = ''
  form.paper_color = '白'
  form.product_name_color = '#000000'
  form.back_no_1 = ''
  form.back_no_2 = ''
  form.back_no_3 = ''
  form.barcode_no = ''
  masterInfo.product_name = ''
}

function fillFormFromRow(row: ProductUseLabelConfig) {
  form.id = row.id
  form.product_cd = row.product_cd
  form.use_label_product_name = row.use_label_product_name || ''
  form.unit_qty = row.unit_qty ?? null
  form.supply_type = normalizeSupplyType(row.supply_type)
  form.part_no = row.part_no || ''
  form.destination_name = row.destination_name || ''
  form.paper_color = row.paper_color || '白'
  form.product_name_color = row.product_name_color || '#000000'
  form.back_no_1 = row.back_no_1 || ''
  form.back_no_2 = row.back_no_2 || ''
  form.back_no_3 = row.back_no_3 || ''
  form.barcode_no = row.barcode_no || ''
  masterInfo.product_name = row.master_product_name || ''
}

async function loadFilterOptions() {
  loadingFilterOptions.value = true
  try {
    const res = await fetchProductUseLabelFilterOptions()
    const data = res?.data
    filterProductOptions.value = data?.products || []
    filterDestinationOptions.value = data?.destinations || []
    if (filters.product_cd && !filterProductOptions.value.some((p) => p.product_cd === filters.product_cd)) {
      filters.product_cd = ''
    }
    if (
      filters.destination_name &&
      !filterDestinationOptions.value.includes(filters.destination_name)
    ) {
      filters.destination_name = ''
    }
  } catch {
    ElMessage.error('絞込選択肢の取得に失敗しました')
  } finally {
    loadingFilterOptions.value = false
  }
}

async function loadAvailableProducts() {
  loadingProducts.value = true
  try {
    const res = await fetchAvailableProductsForUseLabel()
    availableProducts.value = res?.data || []
  } finally {
    loadingProducts.value = false
  }
}

async function loadList() {
  loading.value = true
  try {
    const res = await fetchProductUseLabelConfigList(listQueryParams())
    const data = (res as { list?: ProductUseLabelConfig[]; total?: number }) || res
    list.value = data.list || []
    pagination.total = data.total || 0
  } catch {
    ElMessage.error('一覧の取得に失敗しました')
  } finally {
    loading.value = false
    requestAnimationFrame(updateLayoutMetrics)
  }
}

async function fetchAllListForPrint(): Promise<ProductUseLabelConfig[]> {
  const res = await fetchProductUseLabelConfigList(listQueryParams(1, 200))
  const first = (res as { list?: ProductUseLabelConfig[]; total?: number }) || res
  const total = first.total || 0
  const rows = [...(first.list || [])]
  if (total > rows.length) {
    const pages = Math.ceil(total / 200)
    for (let p = 2; p <= pages; p++) {
      const more = await fetchProductUseLabelConfigList(listQueryParams(p, 200))
      const chunk = (more as { list?: ProductUseLabelConfig[] }) || more
      rows.push(...(chunk.list || []))
    }
  }
  return rows
}

function updateLayoutMetrics() {
  const wrap = tableWrapRef.value
  if (!wrap) return
  const top = wrap.getBoundingClientRect().top
  const h = window.innerHeight - top - 24
  tableHeight.value = Math.max(320, Math.min(h, 720))
  viewportWidth.value = window.innerWidth
}

async function openDialog(row?: ProductUseLabelConfig) {
  if (row) {
    if (!guardMasterOperation(canEdit)) return
    isEdit.value = true
    fillFormFromRow(row)
  } else {
    if (!guardMasterOperation(canCreate)) return
    isEdit.value = false
    resetForm()
  }
  await loadAvailableProducts()
  dialogVisible.value = true
}

async function onProductCdChange(cd: string) {
  const found = availableProducts.value.find((p) => p.product_cd === cd)
  masterInfo.product_name = found?.product_name || ''
  try {
    const res = await fetchProductUseLabelPrefill(cd)
    const data = res?.data
    if (data) {
      form.use_label_product_name = data.use_label_product_name || masterInfo.product_name
      form.unit_qty = data.unit_qty ?? null
      form.part_no = data.part_no || ''
      form.destination_name = data.destination_name || ''
    }
  } catch {
    /* ignore */
  }
}

async function handleSubmit() {
  if (!form.product_cd?.trim()) {
    ElMessage.warning('製品CDを選択してください')
    return
  }
  submitting.value = true
  try {
    const payload = {
      product_cd: form.product_cd,
      use_label_product_name: form.use_label_product_name,
      supply_type: form.supply_type,
      paper_color: form.paper_color,
      product_name_color: form.product_name_color,
      back_no_1: form.back_no_1,
      back_no_2: form.back_no_2,
      back_no_3: form.back_no_3,
      barcode_no: form.barcode_no,
    }
    if (isEdit.value && form.id) {
      await updateProductUseLabelConfig(form.id, payload)
      ElMessage.success('更新しました')
    } else {
      await createProductUseLabelConfig(payload)
      ElMessage.success('登録しました')
    }
    dialogVisible.value = false
    await loadList()
    await loadAvailableProducts()
    if (!isEdit.value) {
      await loadFilterOptions()
    }
  } catch {
    ElMessage.error(isEdit.value ? '更新に失敗しました' : '登録に失敗しました')
  } finally {
    submitting.value = false
  }
}

async function saveInlineField(row: ProductUseLabelConfig, patch: Partial<ProductUseLabelConfig>) {
  if (!row.id || !guardMasterOperation(canEdit)) return
  try {
    await updateProductUseLabelConfig(row.id, patch)
    Object.assign(row, patch)
  } catch {
    ElMessage.error('保存に失敗しました')
    void loadList()
  }
}

async function handleImportFromMaster() {
  if (!form.product_cd || !guardMasterOperation(canEdit)) return
  prefilling.value = true
  try {
    const res = await importProductUseLabelFromMaster(form.product_cd)
    const data = (res as ProductUseLabelConfig) || res
    fillFormFromRow(data)
    ElMessage.success('マスタから再取込しました')
  } catch {
    ElMessage.error('マスタ取込に失敗しました')
  } finally {
    prefilling.value = false
  }
}

async function handleSyncFromMaster() {
  if (!guardMasterOperation(canEdit)) return
  try {
    await ElMessageBox.confirm(
      '製品マスタから取込みます。未登録製品は新規追加、登録済み製品は品番・納入先名・入数をマスタの内容で更新します。よろしいですか？',
      'マスタ取込',
      { type: 'info' }
    )
  } catch {
    return
  }
  syncing.value = true
  try {
    const res = await syncProductUseLabelFromMaster()
    const data = (res as { data?: { added?: number; updated?: number } })?.data
    const added = data?.added ?? 0
    const updated = data?.updated ?? 0
    ElMessage.success(`新規 ${added} 件、マスタ項目更新 ${updated} 件`)
    await loadList()
    await loadAvailableProducts()
    await loadFilterOptions()
  } catch {
    ElMessage.error('マスタ取込に失敗しました')
  } finally {
    syncing.value = false
  }
}

async function handleDelete(row: ProductUseLabelConfig) {
  if (!row.id || !guardMasterOperation(canDelete)) return
  try {
    await ElMessageBox.confirm(`製品 ${row.product_cd} の設定を削除しますか？`, '削除確認', {
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await deleteProductUseLabelConfig(row.id)
    ElMessage.success('削除しました')
    await loadList()
    await loadAvailableProducts()
    await loadFilterOptions()
  } catch {
    ElMessage.error('削除に失敗しました')
  }
}

function openPrintDialog(row: ProductUseLabelConfig) {
  printTarget.value = row
  printPages.value = 1
  printDialogVisible.value = true
}

async function handlePrint() {
  if (!printTarget.value) return
  printing.value = true
  printingCd.value = printTarget.value.product_cd
  const productCd = printTarget.value.product_cd
  const pages = Math.max(1, Number(printPages.value) || 1)
  const perPage = printPerPage.value
  try {
    await printProductUseLabels(configToPrintInput(printTarget.value), {
      pages,
      copiesPerPage: perPage,
    })
    printDialogVisible.value = false
    try {
      await recordLabelQuantityPrint({
        label_type: 'product_use',
        items: [
          {
            product_cd: productCd,
            paper_sheets: pages,
            labels_per_sheet: perPage,
            label_count: pages * perPage,
          },
        ],
      })
    } catch (e) {
      console.warn('ラベル枚数管理への印刷履歴反映に失敗:', e)
      ElMessage.warning('印刷は開始しましたが、枚数管理の履歴更新に失敗しました')
    }
  } catch {
    ElMessage.error('印刷の準備に失敗しました')
  } finally {
    printing.value = false
    printingCd.value = ''
  }
}

async function openPrintAllDialog() {
  printingAll.value = true
  try {
    printAllRows.value = await fetchAllListForPrint()
    if (!printAllRows.value.length) {
      ElMessage.info('印刷対象がありません')
      return
    }
    printAllPages.value = 1
    printAllDialogVisible.value = true
  } catch {
    ElMessage.error('印刷データの取得に失敗しました')
  } finally {
    printingAll.value = false
  }
}

async function handlePrintAll() {
  if (!printAllRows.value.length) return
  printingAll.value = true
  const pages = Math.max(1, Number(printAllPages.value) || 1)
  const rows = [...printAllRows.value]
  try {
    await printProductUseLabels(
      rows.map((r) => configToPrintInput(r)),
      { pages, copiesPerPage: 1 }
    )
    printAllDialogVisible.value = false
    try {
      // 一括印刷: 各製品について指定ページ数分を履歴反映（1紙あたりレイアウト枚数）
      await recordLabelQuantityPrint({
        label_type: 'product_use',
        items: rows
          .filter((r) => r.product_cd)
          .map((r) => {
            const perPage = r.is_inoac_layout || isInoacDestination(r.destination_name) ? 16 : 20
            return {
              product_cd: r.product_cd,
              paper_sheets: pages,
              labels_per_sheet: perPage,
              label_count: pages * perPage,
            }
          }),
      })
    } catch (e) {
      console.warn('ラベル枚数管理への印刷履歴反映に失敗:', e)
      ElMessage.warning('印刷は開始しましたが、枚数管理の履歴更新に失敗しました')
    }
  } catch {
    ElMessage.error('一括印刷に失敗しました')
  } finally {
    printingAll.value = false
  }
}

function mapOutsourceOrderRow(config: ProductUseLabelConfig): OutsourceOrderRow {
  return {
    product_cd: config.product_cd,
    use_label_product_name: config.use_label_product_name || config.master_product_name || '',
    unit_qty: config.unit_qty ?? null,
    paper_color: config.paper_color || '白',
    order_qty: 0,
    config,
  }
}

async function loadOutsourceUsers() {
  try {
    const res = await getUsers({ page: 1, page_size: 500, status: 'active' })
    outsourceUsers.value = res?.items ?? []
  } catch {
    outsourceUsers.value = []
  }
}

async function openOutsourceOrderDialog() {
  if (!guardMasterOperation(canEdit)) return
  outsourceDialogVisible.value = true
  outsourceLoading.value = true
  outsourceUserIds.value = []
  try {
    const [ordersRes, previewRes] = await Promise.all([
      fetchOutsourceUseLabelOrders(),
      fetchOutsourceUseLabelOrderEmailPreview(),
      loadOutsourceUsers(),
    ])
    const orders = (ordersRes as { list?: ProductUseLabelConfig[] })?.list || []
    outsourceOrderRows.value = orders.map(mapOutsourceOrderRow)
    outsourceEmailPreview.value = previewRes as OutsourceOrderEmailPreview
    if (orders.length === 0) {
      ElMessage.info('外注区分の設定がありません')
    }
  } catch {
    outsourceOrderRows.value = []
    outsourceEmailPreview.value = null
    ElMessage.error('外注注文データの取得に失敗しました')
  } finally {
    outsourceLoading.value = false
  }
}

async function sendOutsourceOrderEmail() {
  if (!guardMasterOperation(canEdit)) return
  if (outsourceOrderSendCount.value === 0) {
    ElMessage.warning('注文数が1以上の行を入力してください')
    return
  }
  if (outsourceUserIds.value.length === 0) {
    ElMessage.warning('送信先ユーザーを選択してください')
    return
  }

  const sendRows = outsourceOrderSendRows.value
  const missingLabel = sendRows.filter((row) => !row.use_label_product_name?.trim())
  if (missingLabel.length > 0) {
    ElMessage.warning(
      `製品用製品名未設定のためラベル生成できません: ${missingLabel.map((r) => r.product_cd).join(', ')}`
    )
    return
  }

  try {
    await ElMessageBox.confirm(
      `注文 ${sendRows.length} 件をメール送信します（ラベルPDF 約 ${outsourceLabelPdfCount.value} 枚）。よろしいですか？`,
      'メール送信確認',
      { type: 'info' }
    )
  } catch {
    return
  }

  outsourceSending.value = true
  try {
    const printInputs = sendRows.map((row) => configToPrintInput(row.config))
    const attachments = await buildUseLabelEmailAttachments(printInputs)
    const res = await sendOutsourceUseLabelOrderEmail({
      user_ids: outsourceUserIds.value,
      items: sendRows.map((row) => ({
        product_cd: row.product_cd,
        order_qty: row.order_qty,
        use_label_product_name: row.use_label_product_name,
        master_product_name: row.config.master_product_name,
        unit_qty: row.unit_qty,
        paper_color: row.paper_color,
      })),
      attachments,
    })
    ElMessage.success(res?.message || 'メールを送信しました')
    outsourceDialogVisible.value = false
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'メール送信に失敗しました'
    ElMessage.error(msg)
  } finally {
    outsourceSending.value = false
  }
}

onMounted(() => {
  void loadFilterOptions()
  void loadList()
  updateLayoutMetrics()
  window.addEventListener('resize', updateLayoutMetrics)
})

async function reloadPage() {
  await loadFilterOptions()
  await loadList()
}

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateLayoutMetrics)
  if (keywordTimer) clearTimeout(keywordTimer)
})
</script>

<style scoped>
.pul-page {
  padding: 12px 16px 16px;
  min-height: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
  background:
    radial-gradient(ellipse 80% 50% at 8% -8%, rgba(99, 102, 241, 0.14), transparent 55%),
    radial-gradient(ellipse 55% 42% at 96% 2%, rgba(139, 92, 246, 0.1), transparent 50%),
    linear-gradient(165deg, #f1f5f9 0%, #eef2ff 36%, #f8fafc 100%);
}

/* ── ヒーロー ── */
.pul-hero {
  border-radius: 14px;
  padding: 14px 18px;
  background: linear-gradient(135deg, #312e81 0%, #4338ca 42%, #6366f1 72%, #818cf8 100%);
  color: #fff;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.2) inset,
    0 10px 28px rgba(67, 56, 202, 0.38),
    0 2px 8px rgba(15, 23, 42, 0.08);
}

.pul-hero-inner {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.pul-title-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.pul-title-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.28);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.35) inset,
    0 4px 12px rgba(0, 0, 0, 0.15);
  flex-shrink: 0;
}

.pul-title {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
  letter-spacing: 0.03em;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.12);
}

.pul-subtitle {
  margin: 4px 0 0;
  font-size: 11px;
  line-height: 1.5;
  max-width: 640px;
  color: rgba(255, 255, 255, 0.84);
}

.pul-hero-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.pul-hero-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.04em;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.28);
  backdrop-filter: blur(6px);
}

.pul-hero-badge--inoac {
  background: rgba(251, 191, 36, 0.22);
  border-color: rgba(251, 191, 36, 0.45);
  color: #fef3c7;
}

.pul-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 10px 18px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.14);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.22);
  min-width: 88px;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.25) inset,
    0 4px 14px rgba(0, 0, 0, 0.12);
  transition: transform 0.2s ease, background 0.2s ease;
}

.pul-stat:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
}

.pul-stat-num {
  font-size: 24px;
  font-weight: 800;
  line-height: 1.1;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
}

.pul-stat-lbl {
  margin-top: 2px;
  font-size: 10px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.78);
}

/* ── ツールバー ── */
.pul-toolbar-card {
  background: #fff;
  border-radius: 12px;
  border: 1px solid rgba(99, 102, 241, 0.12);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 4px 16px rgba(67, 56, 202, 0.08),
    0 1px 3px rgba(15, 23, 42, 0.04);
  overflow: hidden;
}

.pul-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 12px;
  padding: 12px 14px;
}

.pul-filters {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 10px 12px;
  flex: 1;
  min-width: 0;
}

.pul-filter-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 140px;
}

.pul-filter-field--search {
  flex: 1 1 220px;
  min-width: 200px;
  max-width: 320px;
}

.pul-field-label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 700;
  color: #4338ca;
  letter-spacing: 0.02em;
}

.pul-search,
.pul-filter {
  width: 100%;
}

.pul-filter--dest {
  min-width: 160px;
}

.pul-search :deep(.el-input__wrapper),
.pul-filter :deep(.el-select__wrapper) {
  border-radius: 8px;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.8) inset,
    0 1px 3px rgba(15, 23, 42, 0.06),
    0 0 0 1px rgba(99, 102, 241, 0.12);
  transition: box-shadow 0.2s ease;
}

.pul-search :deep(.el-input__wrapper:hover),
.pul-search :deep(.el-input__wrapper.is-focus),
.pul-filter :deep(.el-select__wrapper.is-hovering),
.pul-filter :deep(.el-select__wrapper.is-focused) {
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 2px 8px rgba(99, 102, 241, 0.14),
    0 0 0 1px rgba(99, 102, 241, 0.35);
}

.pul-toolbar-actions {
  margin-left: auto;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.pul-btn {
  border: none !important;
  border-radius: 8px !important;
  font-weight: 700 !important;
  font-size: 12px !important;
  letter-spacing: 0.02em;
  transition:
    transform 0.12s ease,
    box-shadow 0.12s ease,
    filter 0.12s ease !important;
}

.pul-btn:not(:disabled):hover {
  transform: translateY(-2px);
  filter: brightness(1.05);
}

.pul-btn:not(:disabled):active {
  transform: translateY(1px);
  filter: brightness(0.97);
}

.pul-btn--refresh {
  color: #475569 !important;
  background: linear-gradient(180deg, #fff 0%, #f1f5f9 100%) !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 3px 0 #cbd5e1,
    0 4px 10px rgba(100, 116, 139, 0.18) !important;
}

.pul-btn--print {
  color: #fff !important;
  background: linear-gradient(180deg, #818cf8 0%, #6366f1 45%, #4f46e5 100%) !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.28) inset,
    0 3px 0 #4338ca,
    0 4px 12px rgba(79, 70, 229, 0.38) !important;
}

.pul-btn--outsource {
  color: #fff !important;
  background: linear-gradient(180deg, #c084fc 0%, #a855f7 45%, #9333ea 100%) !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.28) inset,
    0 3px 0 #7e22ce,
    0 4px 12px rgba(147, 51, 234, 0.38) !important;
}

.pul-btn--sync {
  color: #fff !important;
  background: linear-gradient(180deg, #38bdf8 0%, #0ea5e9 45%, #0284c7 100%) !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.3) inset,
    0 3px 0 #0369a1,
    0 4px 12px rgba(2, 132, 199, 0.35) !important;
}

.pul-btn--create {
  color: #fff !important;
  background: linear-gradient(180deg, #a78bfa 0%, #8b5cf6 40%, #7c3aed 100%) !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.32) inset,
    0 4px 0 #6d28d9,
    0 6px 16px rgba(124, 58, 237, 0.42) !important;
  padding-left: 14px !important;
  padding-right: 14px !important;
}

/* ── テーブル ── */
.pul-table-wrap {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 14px;
  border: 1px solid rgba(99, 102, 241, 0.1);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.95) inset,
    0 6px 20px rgba(67, 56, 202, 0.1),
    0 2px 6px rgba(15, 23, 42, 0.04);
  overflow: hidden;
  padding: 0;
}

.pul-result-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px 14px;
  border-bottom: 1px solid #e2e8f0;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
}

.pul-result-text {
  font-size: 11px;
  font-weight: 600;
  color: #475569;
  white-space: nowrap;
}

.pul-table {
  flex: 1;
  min-height: 0;
  padding: 0 10px 10px;
}

.pul-table :deep(.el-table__inner-wrapper) {
  border-radius: 0 0 10px 10px;
}

.pul-table :deep(.el-table__header-wrapper th.el-table__cell) {
  border-bottom: 1px solid #c7d2fe !important;
}

.pul-table :deep(.el-table__row:hover > td) {
  background: #eef2ff !important;
}

.pul-table :deep(.el-table__cell) {
  padding: 6px 0;
  font-size: 12px;
  border-color: #e8ecf4 !important;
}

.pul-table :deep(.el-input__wrapper) {
  border-radius: 6px;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
}

.pul-table :deep(.el-button.is-link) {
  font-weight: 700;
}

.pul-paper-chip {
  display: inline-block;
  padding: 1px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.6;
  border: 1px solid transparent;
}

.pul-color-dot {
  display: inline-block;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 1px solid rgba(0, 0, 0, 0.12);
  vertical-align: middle;
}

.pul-table-color-cell {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  flex-wrap: nowrap;
  max-width: 100%;
}

.pul-name-color-preview {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 600;
  color: #334155;
  white-space: nowrap;
}

.pul-table-color-select {
  width: 28px;
  flex-shrink: 0;
}

.pul-table-color-select :deep(.el-select__wrapper) {
  padding: 0 4px;
  min-height: 24px;
  border-radius: 6px;
}

.pul-table-color-select :deep(.el-select__selected-item),
.pul-table-color-select :deep(.el-select__placeholder) {
  display: none;
}

.pul-opt-paper {
  display: inline-block;
  padding: 0 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.8;
}

.pul-opt-color {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.pul-readonly-val {
  color: #475569;
  font-size: 12px;
  word-break: break-all;
}

.pul-readonly-val--mono {
  font-family: ui-monospace, monospace;
  letter-spacing: 0.02em;
}

.pul-inoac-tag {
  flex-shrink: 0;
  font-weight: 700;
}

.pul-discontinued-tag {
  font-weight: 700;
}

/* ── 編集ダイアログ ── */
.pul-dialog :deep(.el-dialog) {
  border-radius: 14px;
  overflow: hidden;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.15) inset,
    0 20px 50px rgba(15, 23, 42, 0.2),
    0 8px 20px rgba(67, 56, 202, 0.14);
}

.pul-dialog :deep(.el-dialog__header) {
  padding: 12px 16px 10px;
  margin-right: 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.18);
  background: linear-gradient(135deg, #312e81 0%, #4338ca 50%, #6366f1 100%);
}

.pul-dialog :deep(.el-dialog__title) {
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.pul-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: rgba(255, 255, 255, 0.88);
}

.pul-dialog :deep(.el-dialog__body) {
  padding: 10px 12px 6px;
  background: linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
}

.pul-dialog :deep(.el-dialog__footer) {
  padding: 8px 12px 10px;
  background: #fff;
  border-top: 1px solid #e2e8f0;
}

.pul-edit-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.pul-edit-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.pul-edit-form :deep(.el-form-item__label) {
  padding-bottom: 2px;
  line-height: 1.25;
  font-size: 11px;
  font-weight: 700;
  color: #4338ca;
}

.pul-edit-form :deep(.el-input__wrapper),
.pul-edit-form :deep(.el-select__wrapper) {
  border-radius: 8px;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
  transition: box-shadow 0.15s ease;
}

.pul-edit-form :deep(.el-input__wrapper.is-focus),
.pul-edit-form :deep(.el-select__wrapper.is-focused) {
  box-shadow: 0 0 0 1px #a5b4fc inset, 0 0 0 3px rgba(99, 102, 241, 0.12);
}

.pul-edit-form :deep(.el-input.is-disabled .el-input__wrapper) {
  background: #f1f5f9;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
}

.pul-edit-form :deep(.el-input.is-disabled .el-input__inner) {
  color: #475569;
  -webkit-text-fill-color: #475569;
}

.pul-edit-section {
  padding: 10px 12px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.pul-edit-section--accent {
  background: linear-gradient(180deg, #fff 0%, #f5f3ff 100%);
  border-color: #ddd6fe;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.08);
}

.pul-edit-section-title {
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px dashed #cbd5e1;
  font-size: 11px;
  font-weight: 700;
  color: #4338ca;
  letter-spacing: 0.04em;
}

.pul-edit-section-title--row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  border-bottom: none;
  padding-bottom: 0;
  margin-bottom: 6px;
}

.pul-edit-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px 12px;
}

.pul-edit-grid--3 {
  grid-template-columns: repeat(3, 1fr);
}

.pul-span-full {
  grid-column: 1 / -1;
}

.pul-span-full--sm {
  margin-top: 2px;
}

.pul-edit-hint {
  margin: 6px 0 0;
  font-size: 10px;
  line-height: 1.4;
  color: #94a3b8;
}

.pul-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.pul-btn-cancel {
  border-radius: 8px;
  font-weight: 600 !important;
  color: #64748b !important;
  background: linear-gradient(180deg, #fff 0%, #f1f5f9 100%) !important;
  border: none !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 2px 0 #cbd5e1,
    0 3px 8px rgba(100, 116, 139, 0.12) !important;
}

.pul-btn-secondary {
  border-radius: 8px;
  font-weight: 600 !important;
  color: #4338ca !important;
  background: linear-gradient(180deg, #fff 0%, #eef2ff 100%) !important;
  border: 1px solid #c7d2fe !important;
  box-shadow: 0 1px 3px rgba(67, 56, 202, 0.1) !important;
}

.pul-btn-save {
  border-radius: 8px;
  font-weight: 700 !important;
  color: #fff !important;
  background: linear-gradient(180deg, #818cf8 0%, #6366f1 50%, #4f46e5 100%) !important;
  border: none !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.28) inset,
    0 3px 0 #4338ca,
    0 4px 12px rgba(79, 70, 229, 0.32) !important;
}

/* ── 印刷ダイアログ ── */
.pul-print-dialog :deep(.el-dialog) {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 16px 40px rgba(67, 56, 202, 0.2);
}

.pul-print-dialog :deep(.el-dialog__header) {
  padding: 10px 14px;
  margin-right: 0;
  background: linear-gradient(135deg, #4338ca 0%, #6366f1 100%);
}

.pul-print-dialog :deep(.el-dialog__title) {
  color: #fff;
  font-size: 13px;
  font-weight: 700;
}

.pul-print-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: rgba(255, 255, 255, 0.9);
}

.pul-print-dialog :deep(.el-dialog__body) {
  padding: 12px 14px;
  background: #f8fafc;
}

.pul-print-dialog :deep(.el-dialog__footer) {
  padding: 8px 12px 10px;
  border-top: 1px solid #e2e8f0;
  background: #fff;
}

.pul-form-hint--muted {
  color: #94a3b8;
}

.pul-form-hint {
  margin: 4px 0 0;
  font-size: 11px;
  color: #b45309;
}

.pul-print-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.pul-print-settings {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 12px;
  background: linear-gradient(180deg, #fff 0%, #eef2ff 100%);
  border: 1px solid #c7d2fe;
  border-radius: 10px;
}

.pul-print-settings-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.pul-print-settings-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-width: 140px;
}

.pul-print-settings-label {
  font-size: 12px;
  font-weight: 700;
  color: #4338ca;
  white-space: nowrap;
}

.pul-print-paper-val {
  font-size: 14px;
  font-weight: 800;
}

.pul-print-name-color {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 700;
  color: #334155;
}

.pul-print-note {
  margin: 0;
  font-size: 11px;
  color: #64748b;
  line-height: 1.5;
  padding: 8px 10px;
  background: #fff;
  border-radius: 8px;
  border: 1px dashed #cbd5e1;
}

.pul-print-product {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px 14px;
  background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
  border-radius: 10px;
  border: 1px solid #c7d2fe;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.1);
}

.pul-print-product strong {
  font-size: 15px;
  color: #1e1b4b;
}

.pul-print-cd {
  font-size: 11px;
  color: #64748b;
  font-family: ui-monospace, monospace;
}

.pul-print-layout {
  display: inline-flex;
  align-self: flex-start;
  margin-top: 2px;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
  color: #4338ca;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid #c7d2fe;
}

.pul-print-hint {
  margin-left: 8px;
  font-size: 11px;
  color: #94a3b8;
}

.pul-print-all-lead {
  margin: 0 0 12px;
  padding: 10px 12px;
  font-size: 13px;
  color: #334155;
  line-height: 1.55;
  background: #eef2ff;
  border-radius: 8px;
  border: 1px solid #c7d2fe;
}

/* ── 外注注文ダイアログ ── */
.pul-outsource-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.pul-outsource-lead {
  margin: 0;
  font-size: 13px;
  color: #475569;
  line-height: 1.55;
}

.pul-outsource-mail {
  padding: 12px;
  border-radius: 10px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.pul-outsource-mail-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
  font-size: 12px;
  font-weight: 700;
  color: #334155;
}

.pul-outsource-mail-stat {
  font-size: 11px;
  font-weight: 600;
  color: #7c3aed;
}

.pul-outsource-alert {
  margin-bottom: 10px;
}

.pul-outsource-form {
  margin-top: 4px;
}

@media (max-width: 900px) {
  .pul-toolbar-actions {
    margin-left: 0;
    width: 100%;
    justify-content: flex-end;
  }
}

@media (max-width: 640px) {
  .pul-edit-grid,
  .pul-edit-grid--3 {
    grid-template-columns: 1fr;
  }

  .pul-filter-field,
  .pul-filter-field--search {
    flex: 1 1 100%;
    max-width: none;
  }
}
</style>
