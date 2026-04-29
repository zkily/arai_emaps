<template>
  <div class="inventory-value-table">
    <!-- 製品タブのみ：工程をボタンで絞り込み -->
    <div v-if="isProductTab" class="process-filter">
      <span class="process-filter__label">工程</span>
      <div class="process-filter__btns">
        <el-button
          v-for="opt in processFilterOptions"
          :key="opt.value"
          size="small"
          class="process-filter__btn"
          :class="{ 'process-filter__btn--active': localProcessCd === opt.value }"
          @click="setProductProcess(opt.value)"
        >
          {{ opt.label }}
        </el-button>
      </div>
    </div>
    <div class="table-container">
      <el-table
        ref="tableRef"
        :data="tableData"
        v-loading="loading"
        :height="tableHeight"
        :default-sort="{ prop: 'product_name', order: 'ascending' }"
        @sort-change="handleSortChange"
        @selection-change="handleSelectionChange"
        @row-click="handleRowClick"
        class="value-table"
        stripe
        border
      >
        <!-- 选择列 -->
        <el-table-column
          type="selection"
          width="55"
          :selectable="(row) => row.item_type !== 'summary'"
          v-if="columnSettings.selection"
        />

        <!-- 序号列 -->
        <el-table-column
          type="index"
          label="No."
          width="60"
          :index="getRowIndex"
          v-if="columnSettings.index"
        />

        <!-- 项目类型 -->
        <el-table-column
          prop="item_type"
          label="項目タイプ"
          width="100"
          v-if="columnSettings.item_type"
        >
          <template #default="{ row }">
            <el-tag
              :type="getItemTypeTagType(row.item_type)"
              :effect="row.item_type === 'summary' ? 'plain' : 'dark'"
              class="item-type-tag"
            >
              {{ getItemTypeLabel(row.item_type) }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 代码 -->
        <el-table-column
          prop="product_cd"
          label="コード"
          width="80"
          v-if="columnSettings.product_cd"
        >
          <template #default="{ row }">
            <span class="code-text">{{ row.product_cd }}</span>
          </template>
        </el-table-column>

        <!-- 名称 -->
        <el-table-column
          prop="product_name"
          label="品名"
          width="160"
          sortable="custom"
          show-overflow-tooltip
          v-if="columnSettings.product_name"
        >
          <template #default="{ row }">
            <span class="name-text">{{ row.product_name || row.product_cd || '—' }}</span>
          </template>
        </el-table-column>

        <!-- 部品：parts.kind（マスタ種別 T/N/F 等） -->
        <el-table-column
          prop="kind"
          label="種別"
          width="80"
          align="center"
          sortable="custom"
          show-overflow-tooltip
          v-if="props.itemType === '部品'"
        >
          <template #default="{ row }">
            <span class="code-text">{{ row.kind || '—' }}</span>
          </template>
        </el-table-column>

        <!-- 製品：products.kind（分類） -->
        <el-table-column
          prop="kind"
          label="分類"
          width="84"
          align="center"
          sortable="custom"
          show-overflow-tooltip
          v-if="props.itemType === '製品'"
        >
          <template #default="{ row }">
            <span class="code-text">{{ row.kind || '—' }}</span>
          </template>
        </el-table-column>

        <!-- 工程 -->
        <el-table-column
          prop="process_name"
          label="工程"
          width="100"
          v-if="columnSettings.process_name"
        >
          <template #default="{ row }">
            <span v-if="row.process_name" class="process-text">
              {{ row.process_name }}
            </span>
            <span v-else class="no-data">-</span>
          </template>
        </el-table-column>

        <!-- 数量 -->
        <el-table-column
          prop="quantity"
          label="数量"
          width="80"
          align="right"
          v-if="columnSettings.quantity"
        >
          <template #default="{ row }">
            <span class="quantity-text">
              {{ formatNumber(row.quantity, 0) }}
            </span>
          </template>
        </el-table-column>

        <!-- 材料在庫：束本数・束重量（material_stock） -->
        <el-table-column
          prop="bundle_quantity"
          label="束本数"
          width="88"
          align="right"
          v-if="props.itemType === '材料'"
        >
          <template #default="{ row }">
            <span class="quantity-text">{{ formatNumber(row.bundle_quantity, 0) }}</span>
          </template>
        </el-table-column>
        <el-table-column
          prop="bundle_weight"
          label="束重量(kg)"
          width="110"
          align="right"
          v-if="props.itemType === '材料'"
        >
          <template #default="{ row }">
            <span class="quantity-text">{{ formatNumber(row.bundle_weight, 2) }}</span>
          </template>
        </el-table-column>

        <!-- 单位 -->
        <el-table-column
          prop="unit"
          label="単位"
          width="80"
          align="center"
          v-if="columnSettings.unit"
        >
          <template #default="{ row }">
            <span class="unit-text">{{ row.unit || 'pcs' }}</span>
          </template>
        </el-table-column>

        <!-- 单价 -->
        <el-table-column
          prop="unit_price"
          label="単価"
          width="120"
          align="right"
          v-if="columnSettings.unit_price"
        >
          <template #default="{ row }">
            <span v-if="row.unit_price == null" class="price-text">—</span>
            <span v-else class="price-text">¥{{ formatNumber(row.unit_price, 2) }}</span>
          </template>
        </el-table-column>

        <!-- 金额 -->
        <el-table-column
          prop="total_value"
          label="金額"
          width="140"
          align="right"
          v-if="columnSettings.total_value"
        >
          <template #default="{ row }">
            <span v-if="row.total_value == null" class="value-text">—</span>
            <span
              v-else
              class="value-text"
              :class="{
                'summary-value': row.item_type === 'summary',
                'high-value': row.total_value > 1000000,
                'medium-value': row.total_value > 100000 && row.total_value <= 1000000,
              }"
            >
              ¥{{ formatNumber(row.total_value) }}
            </span>
          </template>
        </el-table-column>

        <!-- 棚卸日 -->
        <el-table-column
          prop="inventory_date"
          label="棚卸日"
          width="120"
          sortable="custom"
          v-if="columnSettings.inventory_date"
        >
          <template #default="{ row }">
            <span class="date-text">
              {{ formatDate(row.inventory_date) }}
            </span>
          </template>
        </el-table-column>

        <!-- 更新日时 -->
        <el-table-column
          prop="updated_at"
          label="更新日時"
          width="140"
          sortable="custom"
          v-if="columnSettings.updated_at"
        >
          <template #default="{ row }">
            <span class="datetime-text">
              {{ formatDateTime(row.updated_at) }}
            </span>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div v-if="isProductTab" class="product-summary">
      <span class="product-summary__item">
        件数
        <strong>{{ formatNumber(totalCount, 0) }}</strong>
      </span>
      <span class="product-summary__item">
        数量合計
        <strong>{{ formatNumber(productQuantityTotal, 0) }}</strong>
      </span>
      <span class="product-summary__item">
        金額合計
        <strong class="product-summary__amount">¥{{ formatNumber(productTotalValueSummary, 0) }}</strong>
      </span>
    </div>

    <!-- 分页 -->
    <div class="pagination-container">
      <div class="pagination-info">
        <span class="info-text">
          全{{ totalCount }}件中 {{ (currentPage - 1) * pageSize + 1 }} -
          {{ Math.min(currentPage * pageSize, totalCount) }}件を表示
        </span>
        <span class="selected-info" v-if="selectedRows.length > 0">
          {{ selectedRows.length }}件選択中
        </span>
      </div>
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[20, 50, 100, 200]"
        :total="totalCount"
        layout="sizes, prev, pager, next"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        class="table-pagination"
      />
    </div>

    <!-- 详情弹窗 -->
    <el-dialog
      v-model="showDetailDialog"
      :title="detailDialogTitle"
      width="800px"
      class="detail-dialog"
    >
      <div class="detail-content" v-loading="detailLoading">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="項目タイプ">
            <el-tag :type="getItemTypeTagType(detailData.item_type)">
              {{ getItemTypeLabel(detailData.item_type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="コード">
            {{ detailData.product_cd }}
          </el-descriptions-item>
          <el-descriptions-item label="名称">
            {{ detailData.product_name }}
          </el-descriptions-item>
          <el-descriptions-item label="工程">
            {{ detailData.process_name || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="数量">
            {{ formatNumber(detailData.quantity, 0) }} {{ detailData.unit || 'pcs' }}
          </el-descriptions-item>
          <el-descriptions-item label="単価">
            <span v-if="detailData.unit_price == null">—</span>
            <span v-else>¥{{ formatNumber(detailData.unit_price, 2) }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="金額">
            <span v-if="detailData.total_value == null">—</span>
            <span v-else class="detail-value">¥{{ formatNumber(detailData.total_value) }}</span>
          </el-descriptions-item>
          <el-descriptions-item v-if="detailData.bundle_quantity != null" label="束本数">
            {{ formatNumber(detailData.bundle_quantity, 0) }}
          </el-descriptions-item>
          <el-descriptions-item v-if="detailData.bundle_weight != null" label="束重量(kg)">
            {{ formatNumber(detailData.bundle_weight, 2) }}
          </el-descriptions-item>
          <el-descriptions-item label="棚卸日">
            {{ formatDate(detailData.inventory_date) }}
          </el-descriptions-item>
          <el-descriptions-item label="作成日時" :span="2">
            {{ formatDateTime(detailData.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="更新日時" :span="2">
            {{ formatDateTime(detailData.updated_at) }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showDetailDialog = false">閉じる</el-button>
          <el-button
            type="primary"
            @click="editPrice(detailData)"
            v-if="hasEditPermission && !detailData.stock_panel_row"
          >
            <Edit class="btn-icon" />
            単価編集
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 单价编辑弹窗 -->
    <el-dialog v-model="showEditDialog" title="単価編集" width="600px" class="edit-dialog">
      <div class="edit-content">
        <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="120px">
          <el-form-item label="項目タイプ">
            <el-tag :type="getItemTypeTagType(editForm.item_type)">
              {{ getItemTypeLabel(editForm.item_type) }}
            </el-tag>
          </el-form-item>
          <el-form-item label="コード">
            <span>{{ editForm.product_cd }}</span>
          </el-form-item>
          <el-form-item label="名称">
            <span>{{ editForm.product_name }}</span>
          </el-form-item>
          <el-form-item label="現在の単価">
            <span class="current-price">¥{{ formatNumber(editForm.current_price, 2) }}</span>
          </el-form-item>
          <el-form-item label="新しい単価" prop="new_price">
            <el-input-number
              v-model="editForm.new_price"
              :precision="2"
              :min="0"
              :max="9999999.99"
              controls-position="right"
              class="price-input"
            />
          </el-form-item>
          <el-form-item label="適用開始日" prop="effective_date">
            <el-date-picker
              v-model="editForm.effective_date"
              type="date"
              placeholder="適用開始日を選択"
              format="YYYY/MM/DD"
              value-format="YYYY-MM-DD"
              class="date-picker"
            />
          </el-form-item>
          <el-form-item label="変更理由" prop="reason">
            <el-input
              v-model="editForm.reason"
              type="textarea"
              :rows="3"
              placeholder="単価変更の理由を入力してください"
              maxlength="200"
              show-word-limit
            />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showEditDialog = false">キャンセル</el-button>
          <el-button type="primary" @click="savePrice" :loading="saving">保存</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 材料：棚卸入力ダイアログ（数量編集・束本数手入力・金額再計算） -->
    <el-dialog
      v-model="showMaterialPrintDialog"
      width="1040px"
      class="material-print-dialog"
      destroy-on-close
      append-to-body
      :show-close="true"
      align-center
      @closed="onMaterialPrintDialogClosed"
    >
      <template #header>
        <div class="material-print-dialog__header">
          <div class="material-print-dialog__header-main">
            <span class="material-print-dialog__title">材料棚卸</span>
            <span v-if="materialPrintAsOfLabel" class="material-print-dialog__date-chip">
              対象日 {{ materialPrintAsOfLabel }}
            </span>
          </div>
          <span class="material-print-dialog__sub">
            数量・束本数(手入力)を編集すると金額が再計算されます
          </span>
        </div>
      </template>
      <div v-loading="materialPrintLoading" class="material-print-root">
        <div class="material-print-capture">
          <el-table
            :data="materialPrintRows"
            border
            stripe
            size="small"
            class="material-print-table"
            :max-height="materialPrintTableMaxH"
          >
            <el-table-column type="index" label="No." width="50" align="center" />
            <el-table-column prop="product_cd" label="材料CD" width="78" show-overflow-tooltip />
            <el-table-column
              prop="product_name"
              label="材料名"
              min-width="120"
              show-overflow-tooltip
            />
            <el-table-column label="束本数" width="96" align="right">
              <template #default="{ row }">
                {{ formatNumber(row.bundle_quantity, 0) }}
              </template>
            </el-table-column>
            <el-table-column label="束重量(kg)" width="92" align="right">
              <template #default="{ row }">
                {{ formatNumber(row.bundle_weight, 2) }}
              </template>
            </el-table-column>
            <el-table-column label="単価(kg/円)" width="95" align="right">
              <template #default="{ row }">¥{{ formatNumber(row.unit_price, 2) }}</template>
            </el-table-column>
            <el-table-column label="数量" width="108" align="center">
              <template #default="{ row }">
                <el-input-number
                  v-model="row.editQuantity"
                  :min="0"
                  :max="999999999"
                  :step="1"
                  :controls="true"
                  size="small"
                  class="material-print-input-num"
                />
              </template>
            </el-table-column>
            <el-table-column label="束本数(手入力)" width="118" align="center">
              <template #default="{ row }">
                <el-input-number
                  v-model="row.manualBundlePieces"
                  :min="0"
                  :max="999999999"
                  :step="1"
                  :precision="0"
                  :controls="true"
                  size="small"
                  class="material-print-input-num"
                />
              </template>
            </el-table-column>
            <el-table-column label="金額" width="112" align="right">
              <template #default="{ row }">
                <span class="material-print-amount">
                  ¥{{ formatNumber(calcMaterialPrintAmount(row), 2) }}
                </span>
              </template>
            </el-table-column>
          </el-table>
          <div class="material-print-summary">
            <span class="material-print-summary__label">合計金額</span>
            <strong class="material-print-summary__amt">
              ¥{{ formatNumber(materialPrintTotalAmount, 2) }}
            </strong>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="material-print-footer">
          <el-button size="small" @click="showMaterialPrintDialog = false">閉じる</el-button>
          <div class="material-print-footer__actions">
            <el-button
              type="success"
              size="small"
              plain
              @click="handleExportMaterialData"
              :loading="materialExportLoading"
              :disabled="materialPrintLoading || !materialPrintRows.length"
            >
              <el-icon><Download /></el-icon>
              エクスポート
            </el-button>
            <el-button
              type="primary"
              size="small"
              @click="handleMaterialPrint"
              :disabled="materialPrintLoading || !materialPrintRows.length"
            >
              <el-icon><Printer /></el-icon>
              印刷
            </el-button>
          </div>
        </div>
      </template>
    </el-dialog>

    <!-- 部品：棚卸印刷ダイアログ（実在庫数量は参照のみ・印刷／エクスポート） -->
    <el-dialog
      v-model="showPartPrintDialog"
      width="960px"
      class="material-print-dialog"
      destroy-on-close
      append-to-body
      :show-close="true"
      align-center
      @closed="onPartPrintDialogClosed"
    >
      <template #header>
        <div class="material-print-dialog__header">
          <div class="material-print-dialog__header-main">
            <span class="material-print-dialog__title">部品棚卸</span>
            <span v-if="partPrintAsOfLabel" class="material-print-dialog__date-chip">
              対象日 {{ partPrintAsOfLabel }}
            </span>
          </div>
          <span class="material-print-dialog__sub">
            数量・金額は実在庫データに基づきます（変更不可）
          </span>
        </div>
      </template>
      <div v-loading="partPrintLoading" class="material-print-root">
        <div class="material-print-capture part-print-capture">
          <div
            class="part-print-groups-scroll"
            :style="{ maxHeight: `${materialPrintTableMaxH}px`, overflowY: 'auto' }"
          >
            <div v-for="grp in partPrintGrouped" :key="grp.kindKey" class="part-print-kind-block">
              <div class="part-print-kind-block__title">種別：{{ grp.kindDisplay }}</div>
              <el-table :data="grp.rows" border stripe size="small" class="material-print-table">
                <el-table-column
                  prop="product_cd"
                  label="部品CD"
                  width="100"
                  show-overflow-tooltip
                />
                <el-table-column
                  prop="product_name"
                  label="部品名"
                  min-width="200"
                  show-overflow-tooltip
                />
                <el-table-column label="数量" width="96" align="right">
                  <template #default="{ row }">
                    <span class="quantity-text">{{ formatNumber(row.quantity, 0) }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="単価" width="108" align="right">
                  <template #default="{ row }">¥{{ formatNumber(row.unit_price, 2) }}</template>
                </el-table-column>
                <el-table-column label="金額" width="112" align="right">
                  <template #default="{ row }">
                    <span class="material-print-amount">
                      ¥{{ formatNumber(calcPartPrintAmountYen(row), 0) }}
                    </span>
                  </template>
                </el-table-column>
              </el-table>
              <div class="part-print-kind-block__subtotal">
                <span class="part-print-kind-block__subtotal-item">
                  数量合計
                  <strong>{{ formatNumber(sumPartPrintGroupQuantity(grp.rows), 0) }}</strong>
                </span>
                <span class="part-print-kind-block__subtotal-item">
                  金額合計
                  <strong class="material-print-amount">
                    ¥{{ formatNumber(sumPartPrintGroupAmountYen(grp.rows), 0) }}
                  </strong>
                </span>
              </div>
            </div>
          </div>
          <div class="material-print-summary">
            <span class="material-print-summary__label">合計金額</span>
            <strong class="material-print-summary__amt">
              ¥{{ formatNumber(partPrintTotalAmount, 0) }}
            </strong>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="material-print-footer">
          <el-button size="small" @click="showPartPrintDialog = false">閉じる</el-button>
          <div class="material-print-footer__actions">
            <el-button
              type="success"
              size="small"
              plain
              @click="handleExportPartData"
              :loading="partExportLoading"
              :disabled="partPrintLoading || !partPrintRows.length"
            >
              <el-icon><Download /></el-icon>
              エクスポート
            </el-button>
            <el-button
              type="primary"
              size="small"
              @click="handlePartPrint"
              :disabled="partPrintLoading || !partPrintRows.length"
            >
              <el-icon><Printer /></el-icon>
              印刷
            </el-button>
          </div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Edit, Printer, Download } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'
import { inventoryValueApi } from '@/api/inventoryValue'
import { getProcessList } from '@/api/master/processMaster'
import { getProductList } from '@/api/master/productMaster'
import { useUserStore } from '@/modules/auth/stores/user'

// NOTE: inventoryValueApi は暫定プレースホルダ実装のため、厳密型を避ける。
type TableRow = any

interface EditForm {
  item_type: string
  product_cd: string
  product_name: string
  current_price: number
  new_price: number
  effective_date: string
  reason: string
}

// Props
interface Props {
  dateRange?: string[]
  itemType?: string
  /** 親画面の製品マスタ絞込（stock-panel の product_cd クエリ） */
  productCdFilter?: string
}

const props = withDefaults(defineProps<Props>(), {
  dateRange: () => [],
  itemType: 'all',
  productCdFilter: '',
})

// Emits
interface Emits {
  /** sumTotalValue: 材料／部品タブ stock-panel の金額合計（API sum_total_value） */
  'data-updated': [data: { total: number; data: any[]; sumTotalValue?: number }]
  'selection-change': [selection: any]
}

const emit = defineEmits<Emits>()

// 用户权限
const userStore = useUserStore()
const hasEditPermission = computed(() => {
  return userStore.hasPermission('inventory_value_edit')
})

const isProductTab = computed(() => props.itemType === '製品')

/** 材料／部品／製品タブは material_stock / part_stock / production_summarys を直接参照 */
const usesStockPanelSource = computed(() =>
  ['材料', '部品', '製品'].includes(String(props.itemType ?? '')),
)

/** 製品タブ工程ボタンから除外する名称／コード（工程名または工程コードが一致する行） */
const PRODUCT_TAB_EXCLUDED_PROCESS_LABELS = [
  '外注検査',
  '外注成型',
  '外注切断',
  '部品',
  '材料',
  '外注溶接前工程',
] as const

function isProductTabExcludedProcess(p: { process_cd?: string; process_name?: string }): boolean {
  const cd = String(p.process_cd ?? '').trim()
  const nm = String(p.process_name ?? '').trim()
  if (!cd && !nm) return false
  const cdUpper = cd.toUpperCase()
  if (cdUpper === 'SW' || nm === 'SW') return true
  for (const label of PRODUCT_TAB_EXCLUDED_PROCESS_LABELS) {
    if (nm === label || cd === label) return true
  }
  return false
}

/** 製品タブ：API / run 解決用の工程（「全部」は未指定） */
const localProcessCd = ref<string>('all')
const processFilterList = ref<{ process_cd: string; process_name: string }[]>([])

const effectiveProcessParam = computed(() => {
  if (!isProductTab.value) return undefined
  return localProcessCd.value !== 'all' ? localProcessCd.value : undefined
})

const processFilterOptions = computed(() => {
  const opts = [{ value: 'all', label: '全部' }]
  for (const p of processFilterList.value) {
    if (p.process_cd) opts.push({ value: p.process_cd, label: p.process_name || p.process_cd })
  }
  return opts
})

async function ensureProcessFilterList() {
  if (!isProductTab.value || processFilterList.value.length > 0) return
  try {
    const res = await getProcessList({ page: 1, pageSize: 5000 })
    const list =
      (
        res as {
          data?: { list?: { process_cd: string; process_name: string }[] }
          list?: { process_cd: string; process_name: string }[]
        }
      ).data?.list ??
      (res as { list?: { process_cd: string; process_name: string }[] }).list ??
      []
    const raw = Array.isArray(list) ? list : []
    processFilterList.value = raw.filter((p) => !isProductTabExcludedProcess(p))
    if (
      localProcessCd.value !== 'all' &&
      !processFilterList.value.some((p) => p.process_cd === localProcessCd.value)
    ) {
      localProcessCd.value = 'all'
    }
  } catch {
    processFilterList.value = []
  }
}

function setProductProcess(cd: string) {
  if (localProcessCd.value === cd) return
  localProcessCd.value = cd
  currentPage.value = 1
  loadTableData()
}

// 响应式数据
const loading = ref(false)
const saving = ref(false)
const detailLoading = ref(false)

/** 材料印刷ダイアログ：数量・手入力束本数から金額を再計算 */
interface MaterialPrintRow extends Record<string, unknown> {
  product_cd?: string
  product_name?: string
  bundle_quantity?: number
  bundle_weight?: number
  unit_price?: number
  editQuantity: number
  manualBundlePieces: number
}

const showMaterialPrintDialog = ref(false)
const materialPrintLoading = ref(false)
const materialExportLoading = ref(false)
const materialPrintRows = ref<MaterialPrintRow[]>([])
const materialPrintAsOfLabel = ref('')

/** 棚卸ダイアログ内テーブル最大高（画面に応じて詰める） */
const materialPrintTableMaxH = computed(() => {
  if (typeof window === 'undefined') return 420
  return Math.min(520, Math.max(260, Math.floor(window.innerHeight * 0.48)))
})

const tableRef = ref<any>()
const editFormRef = ref<any>()

const tableData = ref<any[]>([])
const selectedRows = ref<any[]>([])
const currentPage = ref(1)
const pageSize = ref(50)
const totalCount = ref(0)
const productTotalValueFromApi = ref<number | null>(null)
const tableHeight = ref(600)

// 排序
const sortField = ref('product_name')
const sortOrder = ref('asc')

const productQuantityTotal = computed(() =>
  tableData.value.reduce((sum, row) => sum + (Number(row?.quantity) || 0), 0),
)

const productTotalValueByPage = computed(() =>
  tableData.value.reduce((sum, row) => sum + (Number(row?.total_value) || 0), 0),
)

const productTotalValueSummary = computed(() => {
  if (!isProductTab.value) return 0
  return productTotalValueFromApi.value ?? productTotalValueByPage.value
})

// 列设置
const columnLabels = {
  selection: '選択',
  index: '番号',
  item_type: '項目タイプ',
  product_cd: 'コード',
  product_name: '名称',
  process_name: '工程',
  quantity: '数量',
  unit: '単位',
  unit_price: '単価',
  total_value: '金額',
  inventory_date: '棚卸日',
  updated_at: '更新日時',
}

const selectedColumns = ref<string[]>(Object.keys(columnLabels))
const columnSettings = computed<Record<string, boolean>>(() => {
  const settings: Record<string, boolean> = {}
  Object.keys(columnLabels).forEach((key) => {
    settings[key] = selectedColumns.value.includes(key)
  })
  return settings
})

// 详情弹窗
const showDetailDialog = ref(false)
const detailDialogTitle = ref('')
const detailData = ref<TableRow>({})

// 编辑弹窗
const showEditDialog = ref(false)
const editForm = reactive<EditForm>({
  item_type: '',
  product_cd: '',
  product_name: '',
  current_price: 0,
  new_price: 0,
  effective_date: '',
  reason: '',
})

const editRules: any = {
  new_price: [
    { required: true, message: '新しい単価を入力してください', trigger: 'blur' },
    { type: 'number', min: 0, message: '単価は0以上で入力してください', trigger: 'blur' },
  ],
  effective_date: [{ required: true, message: '適用開始日を選択してください', trigger: 'change' }],
  reason: [
    { required: true, message: '変更理由を入力してください', trigger: 'blur' },
    { min: 5, message: '変更理由は5文字以上で入力してください', trigger: 'blur' },
  ],
}

// 方法
const formatNumber = (value: any, decimals = 0) => {
  if (!value && value !== 0) return '0'
  return Number(value).toLocaleString('ja-JP', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

/**
 * 印刷用金額（材料）:
 * 数量×束重量×単価 + (束重量/束本数マスタ)×束本数手入力×単価
 * 束本数マスタが0のとき第2項は0
 */
function calcMaterialPrintAmount(row: MaterialPrintRow): number {
  const qty = Number(row.editQuantity) || 0
  const bw = Number(row.bundle_weight) || 0
  const up = Number(row.unit_price) || 0
  const bq = Number(row.bundle_quantity) || 0
  const manual = Number(row.manualBundlePieces) || 0
  const part1 = qty * bw * up
  const perUnitBundle = bq > 0 ? bw / bq : 0
  const part2 = perUnitBundle * manual * up
  return Math.round((part1 + part2) * 100) / 100
}

const materialPrintTotalAmount = computed(() =>
  materialPrintRows.value.reduce((sum, row) => sum + calcMaterialPrintAmount(row), 0),
)

/** 部品印刷ダイアログ：API の数量・単価に基づく金額（編集なし） */
interface PartPrintRow extends Record<string, unknown> {
  product_cd?: string
  product_name?: string
  kind?: string | null
  unit?: string
  unit_price?: number
  quantity?: number
}

interface PartPrintKindGroup {
  kindKey: string
  kindDisplay: string
  rows: PartPrintRow[]
}

function getPartPrintKindGroups(rows: PartPrintRow[]): PartPrintKindGroup[] {
  const byKind = new Map<string, PartPrintRow[]>()
  for (const row of rows) {
    const raw = String(row.kind ?? '').trim()
    const key = raw.length ? raw : '__none__'
    if (!byKind.has(key)) byKind.set(key, [])
    byKind.get(key)!.push(row)
  }
  const keys = [...byKind.keys()].sort((a, b) => {
    if (a === '__none__') return 1
    if (b === '__none__') return -1
    return a.localeCompare(b, 'ja', { sensitivity: 'base' })
  })
  for (const k of keys) {
    byKind
      .get(k)!
      .sort((a, b) =>
        String(a.product_name ?? a.product_cd ?? '').localeCompare(
          String(b.product_name ?? b.product_cd ?? ''),
          'ja',
          { sensitivity: 'base' },
        ),
      )
  }
  return keys.map((kindKey) => ({
    kindKey,
    kindDisplay: kindKey === '__none__' ? '—' : kindKey,
    rows: byKind.get(kindKey)!,
  }))
}

/** 金額は円単位で四捨五入（小数なし） */
function calcPartPrintAmountYen(row: PartPrintRow): number {
  const qty = Number(row.quantity) || 0
  const up = Number(row.unit_price) || 0
  return Math.round(qty * up)
}

function sumPartPrintGroupQuantity(rows: PartPrintRow[]): number {
  return rows.reduce((acc, r) => acc + (Number(r.quantity) || 0), 0)
}

function sumPartPrintGroupAmountYen(rows: PartPrintRow[]): number {
  return rows.reduce((acc, r) => acc + calcPartPrintAmountYen(r), 0)
}

const showPartPrintDialog = ref(false)
const partPrintLoading = ref(false)
const partExportLoading = ref(false)
const partPrintRows = ref<PartPrintRow[]>([])
const partPrintAsOfLabel = ref('')

const partPrintGrouped = computed(() => getPartPrintKindGroups(partPrintRows.value))

const partPrintTotalAmount = computed(() =>
  partPrintRows.value.reduce((sum, row) => sum + calcPartPrintAmountYen(row), 0),
)

function buildPartPrintDocumentHtml(): string {
  const asOf = materialPrintEscapeHtml(partPrintAsOfLabel.value)
  const groups = getPartPrintKindGroups(partPrintRows.value)
  const totalAmt = partPrintRows.value.reduce((sum, row) => sum + calcPartPrintAmountYen(row), 0)
  const totalStr = formatNumber(totalAmt, 0)

  const kindHeadStyle = `
    /* 部品棚卸（印刷）数字列：より判読しやすいラテン数字フォントを優先 */
    .mpt-num,
    .mpt-amt,
    .mpt-summary strong,
    .mpt-subtotal-num,
    .mpt-subtotal-amt {
      font-family: 'Arial', 'Helvetica Neue', 'Segoe UI', 'Roboto', 'Noto Sans', sans-serif;
      font-variant-numeric: tabular-nums;
      letter-spacing: 0.01em;
    }
    h2.mpt-kind-head {
      margin: 14px 0 6px;
      font-size: 13px;
      font-weight: 700;
      color: #334155;
    }
    h2.mpt-kind-head:first-of-type { margin-top: 0; }
    table.mpt tfoot td.mpt-subtotal-label {
      font-weight: 700;
      background: #f1f5f9;
      color: #334155;
    }
    table.mpt tfoot td.mpt-subtotal-num,
    table.mpt tfoot td.mpt-subtotal-amt {
      font-weight: 700;
      background: #f1f5f9;
    }
    table.mpt tfoot td.mpt-subtotal-empty { background: #f1f5f9; }
  `

  const blocks = groups
    .map((grp) => {
      const thead = `<thead><tr>
        <th style="width:14%">部品CD</th>
        <th style="width:42%">部品名</th>
        <th style="width:12%">数量</th>
        <th style="width:16%">単価</th>
        <th style="width:16%">金額</th>
      </tr></thead>`
      const tbody = grp.rows
        .map((row) => {
          const amt = calcPartPrintAmountYen(row)
          return `<tr>
      <td class="mpt-left">${materialPrintEscapeHtml(row.product_cd)}</td>
      <td class="mpt-left">${materialPrintEscapeHtml(row.product_name)}</td>
      <td class="mpt-num">${formatNumber(row.quantity, 0)}</td>
      <td class="mpt-num">¥${formatNumber(row.unit_price, 2)}</td>
      <td class="mpt-amt">¥${formatNumber(amt, 0)}</td>
    </tr>`
        })
        .join('')
      const qtySum = sumPartPrintGroupQuantity(grp.rows)
      const amtSum = sumPartPrintGroupAmountYen(grp.rows)
      const tfoot = `<tfoot><tr class="mpt-subtotal-row">
      <td colspan="2" class="mpt-left mpt-subtotal-label">小計（数量合計・金額合計）</td>
      <td class="mpt-num mpt-subtotal-num">${formatNumber(qtySum, 0)}</td>
      <td class="mpt-subtotal-empty"></td>
      <td class="mpt-amt mpt-subtotal-amt">¥${formatNumber(amtSum, 0)}</td>
    </tr></tfoot>`
      return `<h2 class="mpt-kind-head">種別：${materialPrintEscapeHtml(grp.kindDisplay)}</h2>
    <table class="mpt">${thead}<tbody>${tbody}</tbody>${tfoot}</table>`
    })
    .join('')

  return `<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"/><title>部品棚卸</title><style>${PART_PRINT_DOCUMENT_STYLES}${kindHeadStyle}</style></head><body>
    <div class="mpt-page">
    <h1 class="mpt-title">部品棚卸</h1>
    <p class="mpt-meta">対象日: ${asOf}</p>
    ${blocks}
    <div class="mpt-summary"><span>合計金額</span><strong>¥${totalStr}</strong></div>
    </div>
  </body></html>`
}

async function openPartPrintDialog() {
  if (props.itemType !== '部品') {
    ElMessage.warning('部品タブでご利用ください')
    return
  }
  const endDate = props.dateRange?.[1]
  if (!endDate) {
    ElMessage.warning('対象月（月末日）を選択してください')
    return
  }
  partPrintAsOfLabel.value = String(endDate).slice(0, 10)
  showPartPrintDialog.value = true
  partPrintLoading.value = true
  partPrintRows.value = []
  const asOf = partPrintAsOfLabel.value
  try {
    const merged: PartPrintRow[] = []
    let page = 1
    const limit = 500
    let total = 0
    for (let guard = 0; guard < 200; guard += 1) {
      const resp = await inventoryValueApi.getStockPanel({
        tab: 'part',
        as_of: asOf,
        product_cd: props.productCdFilter?.trim() || undefined,
        page,
        limit,
        sort_by: 'product_name',
        sort_order: 'asc',
      })
      const inner = (resp as { data?: { list?: any[]; total?: number } })?.data ?? {}
      total = Number(inner.total ?? 0)
      const list = inner.list ?? []
      for (const raw of list) {
        merged.push({ ...raw } as PartPrintRow)
      }
      if (list.length < limit || merged.length >= total) break
      page += 1
    }
    partPrintRows.value = merged
    if (!merged.length) {
      ElMessage.info('この条件ではデータがありません')
    }
  } catch {
    ElMessage.error('データの取得に失敗しました')
    showPartPrintDialog.value = false
  } finally {
    partPrintLoading.value = false
  }
}

function onPartPrintDialogClosed() {
  partPrintRows.value = []
  partPrintAsOfLabel.value = ''
}

async function handlePartPrint() {
  if (!partPrintRows.value.length) return
  const html = buildPartPrintDocumentHtml()
  const iframe = document.createElement('iframe')
  iframe.setAttribute('title', 'part-stock-print')
  iframe.style.cssText = PART_PRINT_IFRAME_STYLE
  document.body.appendChild(iframe)
  const doc = iframe.contentDocument
  if (!doc) {
    iframe.remove()
    ElMessage.error('印刷の準備に失敗しました')
    return
  }
  doc.open()
  doc.write(html)
  doc.close()
  await new Promise((r) => setTimeout(r, 220))

  const cleanup = () => {
    if (iframe.parentNode) iframe.remove()
  }

  const win = iframe.contentWindow
  if (!win) {
    cleanup()
    return
  }
  win.addEventListener('afterprint', cleanup, { once: true })
  setTimeout(cleanup, 120_000)
  try {
    win.focus()
    win.print()
  } catch (e) {
    console.error(e)
    cleanup()
    ElMessage.error('印刷を開始できませんでした')
  }
}

function handleExportPartData() {
  if (!partPrintRows.value.length) {
    ElMessage.warning('エクスポートするデータがありません')
    return
  }
  partExportLoading.value = true
  try {
    const totalAmt = partPrintRows.value.reduce((s, row) => s + calcPartPrintAmountYen(row), 0)
    type ExportCell = string | number
    const exportRows: Record<string, ExportCell>[] = []
    for (const grp of partPrintGrouped.value) {
      exportRows.push({
        部品CD: `【種別: ${grp.kindDisplay}】`,
        部品名: '',
        数量: '',
        単価: '',
        金額: '',
      })
      for (const row of grp.rows) {
        exportRows.push({
          部品CD: row.product_cd ?? '',
          部品名: String(row.product_name ?? ''),
          数量: Number(row.quantity) || 0,
          単価: Number(row.unit_price) || 0,
          金額: calcPartPrintAmountYen(row),
        })
      }
      exportRows.push({
        部品CD: '',
        部品名: '【種別小計】',
        数量: sumPartPrintGroupQuantity(grp.rows),
        単価: '',
        金額: sumPartPrintGroupAmountYen(grp.rows),
      })
      exportRows.push({
        部品CD: '',
        部品名: '',
        数量: '',
        単価: '',
        金額: '',
      })
    }
    exportRows.push({
      部品CD: '',
      部品名: '【合計】',
      数量: '',
      単価: '',
      金額: totalAmt,
    })

    const ws = XLSX.utils.json_to_sheet(exportRows)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, '部品棚卸')
    const d = partPrintAsOfLabel.value.replace(/[^\d-]/g, '') || 'export'
    XLSX.writeFile(wb, `部品棚卸_${d}.xlsx`)
    ElMessage.success('エクスポートしました')
  } catch (e) {
    console.error(e)
    ElMessage.error('エクスポートに失敗しました')
  } finally {
    partExportLoading.value = false
  }
}

function materialPrintEscapeHtml(text: unknown): string {
  return String(text ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

/** 印刷・PDF で同一のキャンバス幅（A4 横向き）＝レイアウト一致 */
const MATERIAL_PRINT_IFRAME_STYLE =
  'position:fixed;left:-12000px;top:0;width:297mm;min-height:210mm;border:0;opacity:0;pointer-events:none'

/** 印刷・PDF 共通スタイル（Element Plus 系テーブルに近い見た目） */
const MATERIAL_PRINT_DOCUMENT_STYLES = `
    @page { size: A4 landscape; margin: 8mm; }
    * { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; background: #fff; }
    body {
      font-family: 'Hiragino Sans','Hiragino Kaku Gothic ProN','Yu Gothic UI','Yu Gothic','Meiryo','MS PGothic',sans-serif;
      color: #606266;
      font-size: 12px;
      line-height: 1.45;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }
    .mpt-page { width: 100%; max-width: 297mm; margin: 0 auto; padding: 10px 12px 14px; }
    h1.mpt-title {
      margin: 0 0 8px;
      font-size: 16px;
      font-weight: 700;
      color: #303133;
      letter-spacing: 0.04em;
    }
    .mpt-meta { margin: 0 0 12px; color: #909399; font-size: 12px; }
    table.mpt {
      width: 100%;
      border-collapse: collapse;
      table-layout: fixed;
      border: 1px solid #ebeef5;
      font-size: 12px;
    }
    table.mpt th,
    table.mpt td {
      border: 1px solid #ebeef5;
      padding: 6px 8px;
      vertical-align: middle;
      word-break: break-word;
    }
    table.mpt thead th {
      background: #fafafa;
      color: #909399;
      font-weight: 600;
      text-align: center;
      font-size: 12px;
    }
    table.mpt tbody td { color: #606266; }
    table.mpt tbody tr:nth-child(even) { background: #fafafa; }
    table.mpt td.mpt-num { text-align: right; font-variant-numeric: tabular-nums; }
    table.mpt td.mpt-left { text-align: left; }
    table.mpt td.mpt-amt { text-align: right; font-weight: 600; color: #0c4a6e; font-variant-numeric: tabular-nums; }
    .mpt-summary {
      margin-top: 14px;
      padding: 10px 12px;
      text-align: right;
      font-size: 13px;
      color: #303133;
      background: #fafafa;
      border: 1px solid #ebeef5;
      border-radius: 4px;
    }
    .mpt-summary strong { font-size: 16px; margin-left: 10px; letter-spacing: 0.02em; }
`

/** 部品棚卸印刷：プレビュー iframe を A4 縦（210×297mm）に合わせる */
const PART_PRINT_IFRAME_STYLE =
  'position:fixed;left:-12000px;top:0;width:210mm;min-height:297mm;border:0;opacity:0;pointer-events:none'

/** 部品棚卸印刷：@page A4 縦向き・本文 max-width 210mm */
const PART_PRINT_DOCUMENT_STYLES = MATERIAL_PRINT_DOCUMENT_STYLES.replace(
  'A4 landscape',
  'A4 portrait',
).replace('max-width: 297mm', 'max-width: 210mm')

/** 印刷・PDF 用：ダイアログ内の行データ（編集後の数量・手入力束本数・計算金額）のみを HTML にした独立ドキュメント */
function buildMaterialPrintDocumentHtml(): string {
  const asOf = materialPrintEscapeHtml(materialPrintAsOfLabel.value)
  const rows = materialPrintRows.value
  const totalAmt = rows.reduce((sum, row) => sum + calcMaterialPrintAmount(row), 0)
  const totalStr = formatNumber(totalAmt, 2)

  const tbody = rows
    .map((row, idx) => {
      const amt = calcMaterialPrintAmount(row)
      return `<tr>
      <td class="mpt-num">${idx + 1}</td>
      <td class="mpt-left">${materialPrintEscapeHtml(row.product_cd)}</td>
      <td class="mpt-left">${materialPrintEscapeHtml(row.product_name)}</td>
      <td class="mpt-num">${formatNumber(row.bundle_quantity, 0)}</td>
      <td class="mpt-num">${formatNumber(row.bundle_weight, 2)}</td>
      <td class="mpt-num">¥${formatNumber(row.unit_price, 2)}</td>
      <td class="mpt-num">${formatNumber(row.editQuantity, 0)}</td>
      <td class="mpt-num">${formatNumber(row.manualBundlePieces, 0)}</td>
      <td class="mpt-amt">¥${formatNumber(amt, 2)}</td>
    </tr>`
    })
    .join('')

  return `<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"/><title>材料棚卸</title><style>${MATERIAL_PRINT_DOCUMENT_STYLES}</style></head><body>
    <div class="mpt-page">
    <h1 class="mpt-title">材料棚卸</h1>
    <p class="mpt-meta">対象日: ${asOf}</p>
    <table class="mpt">
      <thead><tr>
        <th style="width:4%">No.</th>
        <th style="width:9%">CD</th>
        <th style="width:24%">名称</th>
        <th style="width:9%">束本数</th>
        <th style="width:9%">束重量(kg)</th>
        <th style="width:10%">単価(kg/)</th>
        <th style="width:8%">数量</th>
        <th style="width:10%">束本数(手入力)</th>
        <th style="width:11%">金額</th>
      </tr></thead>
      <tbody>${tbody}</tbody>
    </table>
    <div class="mpt-summary"><span>合計金額</span><strong>¥${totalStr}</strong></div>
    </div>
  </body></html>`
}

async function openMaterialPrintDialog() {
  const endDate = props.dateRange?.[1]
  if (!endDate) {
    ElMessage.warning('対象月（月末日）を選択してください')
    return
  }
  materialPrintAsOfLabel.value = String(endDate).slice(0, 10)
  showMaterialPrintDialog.value = true
  materialPrintLoading.value = true
  materialPrintRows.value = []
  const asOf = materialPrintAsOfLabel.value
  try {
    const merged: MaterialPrintRow[] = []
    let page = 1
    const limit = 500
    let total = 0
    for (let guard = 0; guard < 200; guard += 1) {
      const resp = await inventoryValueApi.getStockPanel({
        tab: 'material',
        as_of: asOf,
        product_cd: props.productCdFilter?.trim() || undefined,
        page,
        limit,
        sort_by: 'product_name',
        sort_order: 'asc',
      })
      const inner = (resp as { data?: { list?: any[]; total?: number } })?.data ?? {}
      total = Number(inner.total ?? 0)
      const list = inner.list ?? []
      for (const raw of list) {
        const q = Number(raw.quantity) || 0
        merged.push({
          ...raw,
          editQuantity: q,
          manualBundlePieces: 0,
        } as MaterialPrintRow)
      }
      if (list.length < limit || merged.length >= total) break
      page += 1
    }
    materialPrintRows.value = merged
    if (!merged.length) {
      ElMessage.info('この条件ではデータがありません')
    }
  } catch {
    ElMessage.error('データの取得に失敗しました')
    showMaterialPrintDialog.value = false
  } finally {
    materialPrintLoading.value = false
  }
}

function onMaterialPrintDialogClosed() {
  materialPrintRows.value = []
  materialPrintAsOfLabel.value = ''
}

/** 親ページではなく、表データのみを iframe 内で印刷 */
async function handleMaterialPrint() {
  if (!materialPrintRows.value.length) return
  const html = buildMaterialPrintDocumentHtml()
  const iframe = document.createElement('iframe')
  iframe.setAttribute('title', 'material-stock-print')
  iframe.style.cssText = MATERIAL_PRINT_IFRAME_STYLE
  document.body.appendChild(iframe)
  const doc = iframe.contentDocument
  if (!doc) {
    iframe.remove()
    ElMessage.error('印刷の準備に失敗しました')
    return
  }
  doc.open()
  doc.write(html)
  doc.close()
  await new Promise((r) => setTimeout(r, 220))

  const cleanup = () => {
    if (iframe.parentNode) iframe.remove()
  }

  const win = iframe.contentWindow
  if (!win) {
    cleanup()
    return
  }
  win.addEventListener('afterprint', cleanup, { once: true })
  setTimeout(cleanup, 120_000)
  try {
    win.focus()
    win.print()
  } catch (e) {
    console.error(e)
    cleanup()
    ElMessage.error('印刷を開始できませんでした')
  }
}

/** ダイアログ内の表データ（編集後の数量・手入力束本数・計算金額）を Excel にエクスポート */
function handleExportMaterialData() {
  if (!materialPrintRows.value.length) {
    ElMessage.warning('エクスポートするデータがありません')
    return
  }
  materialExportLoading.value = true
  try {
    const totalAmt = materialPrintRows.value.reduce((s, row) => s + calcMaterialPrintAmount(row), 0)
    type ExportCell = string | number
    const exportRows: Record<string, ExportCell>[] = materialPrintRows.value.map((row, idx) => ({
      No: idx + 1,
      CD: row.product_cd ?? '',
      名称: String(row.product_name ?? ''),
      束本数: Number(row.bundle_quantity) || 0,
      '束重量(kg)': Number(row.bundle_weight) || 0,
      '単価(kg/円)': Number(row.unit_price) || 0,
      数量: Number(row.editQuantity) || 0,
      '束本数(手入力)': Number(row.manualBundlePieces) || 0,
      金額: calcMaterialPrintAmount(row),
    }))
    exportRows.push({
      No: '',
      CD: '',
      名称: '【合計】',
      束本数: '',
      '束重量(kg)': '',
      '単価(kg/円)': '',
      数量: '',
      '束本数(手入力)': '',
      金額: Math.round(totalAmt * 100) / 100,
    })

    const ws = XLSX.utils.json_to_sheet(exportRows)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, '材料棚卸')
    const d = materialPrintAsOfLabel.value.replace(/[^\d-]/g, '') || 'export'
    XLSX.writeFile(wb, `材料棚卸_${d}.xlsx`)
    ElMessage.success('エクスポートしました')
  } catch (e) {
    console.error(e)
    ElMessage.error('エクスポートに失敗しました')
  } finally {
    materialExportLoading.value = false
  }
}

const formatDate = (dateString: any) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('ja-JP')
}

const formatDateTime = (dateString: any) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('ja-JP')
}

const getItemTypeLabel = (type: string) => {
  const t = String(type ?? '')
  if (t.includes('製品')) return '製品'
  if (t.includes('ステー')) return '製品'
  const labels: Record<string, string> = {
    material: '材料',
    component: '部品',
    stay: '製品',
    product: '製品',
    summary: '合計',
  }
  return labels[type] || type
}

type TagType = 'primary' | 'success' | 'warning' | 'info' | 'danger'
const getItemTypeTagType = (type: string): TagType => {
  const t = String(type ?? '')
  if (t.includes('材料')) return 'primary'
  if (t.includes('部品')) return 'success'
  if (t.includes('製品') || t.includes('ステー')) return 'warning'
  const types: Record<string, TagType> = {
    material: 'primary',
    component: 'success',
    stay: 'warning',
    product: 'warning',
    summary: 'info',
  }
  return types[type] || 'info'
}

const getRowIndex = (index: number) => {
  return (currentPage.value - 1) * pageSize.value + index + 1
}

// 获取查询参数
let processNameByCd: Record<string, string> = {}
let productNameByCd: Record<string, string> = {}
let lastResolvedRunId: number | null = null

async function ensureProcessNameMap() {
  if (Object.keys(processNameByCd).length > 0) return
  try {
    const res = await getProcessList({ page: 1, pageSize: 5000 })
    const list =
      (
        res as {
          data?: { list?: { process_cd: string; process_name: string }[] }
          list?: { process_cd: string; process_name: string }[]
        }
      ).data?.list ??
      (res as { list?: { process_cd: string; process_name: string }[] }).list ??
      []
    processNameByCd = Object.fromEntries(list.map((p) => [p.process_cd, p.process_name]))
  } catch {
    processNameByCd = {}
  }
}

async function ensureProductNameMap() {
  if (Object.keys(productNameByCd).length > 0) return
  try {
    const res = await getProductList({ page: 1, pageSize: 5000 })
    const list =
      (
        res as {
          data?: { list?: { product_cd: string; product_name: string }[] }
          list?: { product_cd: string; product_name: string }[]
        }
      ).data?.list ??
      (res as { list?: { product_cd: string; product_name: string }[] }).list ??
      []
    productNameByCd = Object.fromEntries(
      list.map((p) => [String(p.product_cd ?? ''), String(p.product_name ?? '')]),
    )
  } catch {
    productNameByCd = {}
  }
}

function sortRows(rows: any[], prop: string, order: string) {
  if (!prop || !rows.length) return rows
  const dir = order === 'asc' ? 1 : -1
  return [...rows].sort((a, b) => {
    if (prop === 'product_name') {
      const sa = String(a.product_name ?? a.product_cd ?? '').trim()
      const sb = String(b.product_name ?? b.product_cd ?? '').trim()
      return sa.localeCompare(sb, 'ja', { sensitivity: 'base' }) * dir
    }
    let av: number | string = a[prop]
    let bv: number | string = b[prop]
    if (['total_value', 'quantity', 'unit_price'].includes(prop)) {
      av = Number(av) || 0
      bv = Number(bv) || 0
    } else {
      av = String(av ?? '')
      bv = String(bv ?? '')
    }
    if (av < bv) return -1 * dir
    if (av > bv) return 1 * dir
    return 0
  })
}

const matchesItemType = (rawItemType: unknown, expectedType: string | undefined): boolean => {
  if (!expectedType || expectedType === 'all') return true
  const value = String(rawItemType ?? '')
  if (expectedType === '材料') return value.includes('材料')
  if (expectedType === '部品') return value.includes('部品')
  if (expectedType === '製品') return value.includes('ステー') || value.includes('製品')
  return value === expectedType
}

const resolveRunIdByFilters = async (): Promise<number | undefined> => {
  const [startDate, endDate] = props.dateRange ?? []
  const processCode = effectiveProcessParam.value

  const hasDateFilter = Boolean(startDate && endDate)
  if (!hasDateFilter && !processCode) return undefined

  try {
    const runsResp = await inventoryValueApi.getRuns({ page: 1, limit: 100 })
    const runs = ((runsResp as any)?.data?.list ?? []) as Array<{
      id: number
      start_date?: string | null
      end_date?: string | null
      process_cd?: string | null
    }>

    const matched = runs.find((run) => {
      const runStart = run.start_date || ''
      const runEnd = run.end_date || ''
      const runProcess = run.process_cd || undefined
      const dateMatched = hasDateFilter ? runStart === startDate && runEnd === endDate : true
      // 現在の計算実行は「全工程」で run.process_cd が null のため、
      // 工程フィルタ選択時でも null run を許容して同一期間の run を採用する。
      const processMatched = processCode ? !runProcess || runProcess === processCode : true
      return dateMatched && processMatched
    })

    if (matched?.id) {
      lastResolvedRunId = matched.id
      return matched.id
    }
    return undefined
  } catch {
    return lastResolvedRunId ?? undefined
  }
}

// 加载表格数据
const loadTableData = async () => {
  try {
    loading.value = true
    if (isProductTab.value) await ensureProcessFilterList()
    await ensureProcessNameMap()
    await ensureProductNameMap()

    if (usesStockPanelSource.value) {
      const endDate = props.dateRange?.[1]
      if (!endDate) {
        tableData.value = []
        totalCount.value = 0
        emit('data-updated', {
          total: 0,
          data: [],
          sumTotalValue: props.itemType === '材料' || props.itemType === '部品' ? 0 : undefined,
        })
        return
      }
      const tabMap: Record<string, 'material' | 'part' | 'product'> = {
        材料: 'material',
        部品: 'part',
        製品: 'product',
      }
      const tab = tabMap[String(props.itemType ?? '')]
      if (!tab) {
        tableData.value = []
        totalCount.value = 0
        emit('data-updated', {
          total: 0,
          data: [],
          sumTotalValue: props.itemType === '材料' || props.itemType === '部品' ? 0 : undefined,
        })
        return
      }
      const resp = await inventoryValueApi.getStockPanel({
        tab,
        as_of: String(endDate).slice(0, 10),
        process_cd: isProductTab.value ? localProcessCd.value : undefined,
        product_cd: props.productCdFilter?.trim() || undefined,
        page: currentPage.value,
        limit: pageSize.value,
        sort_by: sortField.value,
        sort_order: sortOrder.value,
      })
      const inner =
        (resp as { data?: { list?: any[]; total?: number; sum_total_value?: number } })?.data ?? {}
      const list = inner.list ?? []
      totalCount.value = Number(inner.total ?? 0)
      tableData.value = list
      productTotalValueFromApi.value = isProductTab.value
        ? inner.sum_total_value != null
          ? Number(inner.sum_total_value)
          : null
        : null
      const sumTotalValue =
        props.itemType === '材料' || props.itemType === '部品'
          ? Number(inner.sum_total_value ?? 0)
          : undefined
      emit('data-updated', { total: totalCount.value, data: tableData.value, sumTotalValue })
      return
    }

    const runId = await resolveRunIdByFilters()
    const baseParams = {
      run_id: runId,
      process_cd: effectiveProcessParam.value,
    }
    const limitPerRequest = 500
    const maxPages = 20
    let page = 1
    let totalFromApi = 0
    let mergedRows: any[] = []

    do {
      const response = await inventoryValueApi.getValueList({
        ...baseParams,
        page,
        limit: limitPerRequest,
      })
      const pageRows = (response.data.list ?? []).map((row: any) => ({
        ...row,
        // 部品：API の product_name（parts.part_name）を優先
        product_name:
          row.product_name ?? productNameByCd[String(row.product_cd ?? '')] ?? row.product_cd ?? '',
        process_name: row.process_name ?? processNameByCd[row.process_cd] ?? row.process_cd ?? '',
      }))
      totalFromApi = Number(response.data.total ?? 0)
      mergedRows = mergedRows.concat(pageRows)
      if (!pageRows.length || mergedRows.length >= totalFromApi) break
      page += 1
    } while (page <= maxPages)

    let rows = mergedRows
    rows = rows.filter((row: any) => matchesItemType(row.item_type, props.itemType))
    rows = sortRows(rows, sortField.value, sortOrder.value)
    totalCount.value = rows.length
    const start = (currentPage.value - 1) * pageSize.value
    tableData.value = rows.slice(start, start + pageSize.value)

    emit('data-updated', {
      total: totalCount.value,
      data: tableData.value,
    })
  } catch (error) {
    console.error('表格数据加载失败:', error)
    ElMessage.error('データの読み込みに失敗しました')
  } finally {
    loading.value = false
  }
}

// 刷新表格
const refreshTable = () => {
  loadTableData()
}

// 排序处理
const handleSortChange = ({ prop, order }: any) => {
  sortField.value = prop
  sortOrder.value = order === 'ascending' ? 'asc' : 'desc'
  loadTableData()
}

// 选择处理
const handleSelectionChange = (selection: any) => {
  selectedRows.value = selection
  emit('selection-change', selection)
}

// 行点击处理
const handleRowClick = (row: any) => {
  if (row.item_type !== 'summary') {
    viewDetail(row)
  }
}

// 分页处理
const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadTableData()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  loadTableData()
}

const resetColumnSettings = () => {
  selectedColumns.value = [
    'item_type',
    'product_cd',
    'product_name',
    'process_name',
    'quantity',
    'unit_price',
    'total_value',
    'inventory_date',
  ]
}

// 查看详情
const viewDetail = async (row: any) => {
  try {
    detailLoading.value = true
    detailDialogTitle.value = `詳細情報 - ${row.product_name}`

    if (row.stock_panel_row) {
      detailData.value = { ...row }
      showDetailDialog.value = true
      return
    }

    const response = await inventoryValueApi.getValueDetail(row.id)
    const payload = (response as { data?: Record<string, any> })?.data ?? {}
    detailData.value = {
      ...row,
      ...payload,
    }

    showDetailDialog.value = true
  } catch (error) {
    console.error('详情加载失败:', error)
    ElMessage.error('詳細情報の読み込みに失敗しました')
  } finally {
    detailLoading.value = false
  }
}

// 编辑单价
const editPrice = (row: any) => {
  Object.assign(editForm, {
    item_type: row.item_type,
    product_cd: row.product_cd,
    product_name: row.product_name,
    current_price: row.unit_price,
    new_price: row.unit_price,
    effective_date: new Date().toISOString().slice(0, 10),
    reason: '',
  })

  showEditDialog.value = true
  showDetailDialog.value = false
}

// 保存单价
const savePrice = async () => {
  try {
    const valid = await editFormRef.value.validate()
    if (!valid) return

    saving.value = true

    const params = {
      itemType: editForm.item_type,
      productCode: editForm.product_cd,
      newPrice: editForm.new_price,
      effectiveDate: editForm.effective_date,
      reason: editForm.reason,
    }

    await inventoryValueApi.updatePrice(params)

    ElMessage.success('単価を更新しました')
    showEditDialog.value = false
    await loadTableData()
  } catch (error) {
    console.error('单价保存失败:', error)
    ElMessage.error('単価の更新に失敗しました')
  } finally {
    saving.value = false
  }
}

// 计算表格高度
const calculateTableHeight = () => {
  nextTick(() => {
    const windowHeight = window.innerHeight
    const headerHeight = 200 // 估算的头部高度
    const paginationHeight = 80 // 分页高度
    const margin = 100 // 边距

    tableHeight.value = windowHeight - headerHeight - paginationHeight - margin
  })
}

// 监听props变化
watch(
  () => [props.dateRange, props.itemType, localProcessCd.value, props.productCdFilter],
  () => {
    currentPage.value = 1
    loadTableData()
  },
  { deep: true },
)

// 生命周期
onMounted(() => {
  // 从本地存储恢复列设置
  const savedColumns = localStorage.getItem('inventory_value_columns')
  if (savedColumns) {
    selectedColumns.value = JSON.parse(savedColumns)
  } else {
    resetColumnSettings()
  }

  calculateTableHeight()
  loadTableData()

  window.addEventListener('resize', calculateTableHeight)
})

// 暴露方法给父组件
defineExpose({
  refreshTable,
  getSelectedRows: () => selectedRows.value,
  clearSelection: () => tableRef.value?.clearSelection(),
  openMaterialPrintDialog,
  openPartPrintDialog,
})
</script>

<style scoped>
.inventory-value-table {
  --iv-table-space: 12px;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 0;
  gap: var(--iv-table-space);
}

.material-print-dialog :deep(.el-overlay-dialog) {
  display: flex;
  align-items: center;
  justify-content: center;
}

.material-print-dialog :deep(.el-dialog) {
  margin: 0 !important;
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow:
    0 24px 48px rgba(15, 23, 42, 0.14),
    0 0 0 1px rgba(255, 255, 255, 0.6) inset;
  background: linear-gradient(165deg, #ffffff 0%, #f8fafc 100%);
}

.material-print-dialog :deep(.el-dialog__header) {
  margin: 0;
  padding: 0;
  border-bottom: none;
}

.material-print-dialog :deep(.el-dialog__headerbtn) {
  top: 10px;
  right: 10px;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.04);
}

.material-print-dialog :deep(.el-dialog__headerbtn:hover) {
  background: rgba(14, 165, 233, 0.12);
}

.material-print-dialog :deep(.el-dialog__body) {
  padding: 0 12px 10px;
  max-height: calc(100vh - 200px);
  overflow: hidden;
}

.material-print-dialog__header {
  padding: 12px 40px 10px 14px;
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.12) 0%, rgba(99, 102, 241, 0.08) 100%);
  border-bottom: 1px solid rgba(148, 163, 184, 0.28);
}

.material-print-dialog__header-main {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
}

.material-print-dialog__title {
  font-size: 16px;
  font-weight: 800;
  letter-spacing: 0.06em;
  color: #0f172a;
}

.material-print-dialog__date-chip {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  color: #0369a1;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(14, 165, 233, 0.35);
}

.material-print-dialog__sub {
  display: block;
  margin-top: 4px;
  font-size: 11px;
  color: #64748b;
  line-height: 1.35;
}

.material-print-capture {
  box-sizing: border-box;
  padding: 0;
  background: transparent;
  color: #0f172a;
  font-family:
    'Hiragino Sans', 'Hiragino Kaku Gothic ProN', 'Yu Gothic UI', 'Yu Gothic', 'Meiryo',
    'MS PGothic', sans-serif;
}

.material-print-root {
  max-height: none;
  overflow: visible;
}

.material-print-capture :deep(.el-table),
.material-print-capture :deep(.el-table th),
.material-print-capture :deep(.el-table td) {
  font-family: inherit;
  font-size: 12px;
}

.material-print-table :deep(.el-table__header th) {
  padding: 4px 6px !important;
  font-size: 11px !important;
  font-weight: 700 !important;
  color: #475569 !important;
  background: linear-gradient(180deg, #f1f5f9, #e2e8f0) !important;
}

.material-print-table :deep(.el-table__body td) {
  padding: 3px 6px !important;
}

.material-print-table :deep(.el-table__body .cell) {
  line-height: 1.35;
}

.material-print-table :deep(.el-table) {
  --el-table-border-color: rgba(148, 163, 184, 0.35);
  border-radius: 10px;
  overflow: hidden;
}

.material-print-summary {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
  padding: 8px 12px;
  background: linear-gradient(90deg, rgba(241, 245, 249, 0.5), rgba(224, 242, 254, 0.65));
  border: 1px solid rgba(14, 165, 233, 0.22);
  border-radius: 10px;
}

.material-print-summary__label {
  font-size: 12px;
  font-weight: 700;
  color: #475569;
}

.material-print-summary__amt {
  font-size: 17px;
  font-weight: 800;
  color: #0c4a6e;
  letter-spacing: 0.02em;
  font-variant-numeric: tabular-nums;
}

.material-print-amount {
  font-weight: 700;
  color: #0369a1;
  font-variant-numeric: tabular-nums;
  font-size: 12px;
}

.material-print-input-num {
  width: 100% !important;
  max-width: 102px;
}

.material-print-input-num :deep(.el-input__wrapper) {
  padding-left: 6px;
  padding-right: 6px;
  border-radius: 8px;
}

.material-print-footer {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
  padding: 2px 0 0;
}

.material-print-footer__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.material-print-dialog :deep(.el-dialog__footer) {
  padding: 8px 14px 12px;
  border-top: 1px solid rgba(148, 163, 184, 0.22);
  background: rgba(248, 250, 252, 0.75);
}

.part-print-groups-scroll {
  padding: 0 2px;
}

.part-print-kind-block {
  margin-bottom: 14px;
}

.part-print-kind-block:last-child {
  margin-bottom: 4px;
}

.part-print-kind-block__title {
  margin: 0 0 6px;
  font-size: 12px;
  font-weight: 700;
  color: #475569;
  letter-spacing: 0.03em;
}

.part-print-kind-block__subtotal {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  align-items: center;
  gap: 18px 24px;
  margin-top: 6px;
  padding: 7px 12px;
  font-size: 12px;
  color: #475569;
  background: linear-gradient(90deg, rgba(241, 245, 249, 0.65), rgba(224, 242, 254, 0.55));
  border: 1px solid rgba(148, 163, 184, 0.28);
  border-radius: 8px;
}

.part-print-kind-block__subtotal-item strong {
  margin-left: 6px;
  font-weight: 800;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
}

.process-filter {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  background: linear-gradient(
    135deg,
    rgba(248, 250, 252, 0.96) 0%,
    rgba(255, 251, 235, 0.55) 45%,
    rgba(254, 243, 199, 0.4) 100%
  );
  border: 1px solid rgba(245, 158, 11, 0.2);
  border-radius: 10px;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.8) inset,
    0 3px 10px rgba(15, 23, 42, 0.05);
  animation: iv-process-strip-in 0.45s cubic-bezier(0.22, 1, 0.36, 1) both;
  transition:
    box-shadow 0.35s cubic-bezier(0.22, 1, 0.36, 1),
    border-color 0.3s ease;
}

.process-filter:hover {
  border-color: rgba(245, 158, 11, 0.3);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.88) inset,
    0 6px 20px rgba(245, 158, 11, 0.1);
}

.process-filter__label {
  display: inline-flex;
  align-items: center;
  font-size: 11px;
  font-weight: 800;
  color: #92400e;
  letter-spacing: 0.05em;
  flex-shrink: 0;
  padding: 4px 8px;
  line-height: 1.25;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.45);
  border: 1px solid rgba(245, 158, 11, 0.18);
}

.process-filter__btns {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  flex: 1;
  min-width: 0;
}

/* 与棚卸金額管理标题行 .header-action-btn 同高：padding 8×16、12px 字、行高 1.3、圆角 11 */
.process-filter__btn {
  font-weight: 700 !important;
  font-size: 12px !important;
  line-height: 1.3 !important;
  letter-spacing: 0.03em;
  border-radius: 11px !important;
  padding: 8px 16px !important;
  border-width: 1px !important;
  margin: 0 !important;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
  transition:
    transform 0.22s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.28s ease,
    border-color 0.22s ease,
    background 0.22s ease,
    color 0.22s ease !important;
}

.process-filter__btn:not(.process-filter__btn--active) {
  color: #92400e !important;
  background: linear-gradient(
    165deg,
    rgba(255, 255, 255, 0.98),
    rgba(255, 251, 235, 0.72)
  ) !important;
  border-color: rgba(245, 158, 11, 0.38) !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.88) inset,
    0 2px 8px rgba(245, 158, 11, 0.1);
}

.process-filter__btn:not(.process-filter__btn--active):hover {
  color: #7c2d12 !important;
  border-color: rgba(217, 119, 6, 0.48) !important;
  background: linear-gradient(165deg, #fff, rgba(254, 243, 199, 0.88)) !important;
  box-shadow:
    0 1px 0 #fff inset,
    0 8px 20px rgba(245, 158, 11, 0.18);
  transform: translateY(-2px);
}

.process-filter__btn--active {
  color: #fff !important;
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 42%, #d97706 100%) !important;
  border-color: rgba(217, 119, 6, 0.55) !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.35) inset,
    0 6px 18px rgba(245, 158, 11, 0.38);
}

.process-filter__btn--active:hover {
  color: #fff !important;
  border-color: rgba(180, 83, 9, 0.65) !important;
  background: linear-gradient(135deg, #fcd34d 0%, #f59e0b 40%, #b45309 100%) !important;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.4) inset,
    0 10px 26px rgba(245, 158, 11, 0.42);
  transform: translateY(-2px);
}

.process-filter__btn:active {
  transform: translateY(0);
}

.process-filter__btn:focus-visible {
  outline: 2px solid rgba(245, 158, 11, 0.45);
  outline-offset: 2px;
}

/* 表格样式 */
.table-container {
  flex: 1;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.99) 0%, rgba(248, 250, 252, 0.96) 100%);
  backdrop-filter: blur(18px);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 12px;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.85) inset,
    0 8px 24px rgba(15, 23, 42, 0.08);
  overflow: hidden;
  animation: iv-table-surface-in 0.5s cubic-bezier(0.22, 1, 0.36, 1) both;
  transition:
    box-shadow 0.4s cubic-bezier(0.22, 1, 0.36, 1),
    border-color 0.35s ease;
}

.table-container:hover {
  border-color: rgba(14, 165, 233, 0.18);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 12px 32px rgba(15, 23, 42, 0.1);
}

@keyframes iv-process-strip-in {
  from {
    opacity: 0;
    transform: translateY(-4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes iv-table-surface-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.value-table {
  background: transparent;
}

.value-table :deep(.el-table) {
  background: transparent;
  --el-table-header-bg-color: transparent;
  --el-table-row-hover-bg-color: rgba(14, 165, 233, 0.08);
}

.value-table :deep(.el-table .cell) {
  padding-top: 4px;
  padding-bottom: 4px;
  line-height: 1.2;
}

.value-table :deep(.el-table__header-wrapper) {
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.95), rgba(241, 245, 249, 0.88));
}

.value-table :deep(.el-table__header th) {
  background: transparent;
  color: #334155;
  font-weight: 700;
  font-size: 11px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.3);
  padding-top: 3px;
  padding-bottom: 3px;
}

.value-table :deep(.el-table__header-wrapper th.el-table__cell .cell) {
  text-align: center;
  justify-content: center;
}

.value-table :deep(.el-table__body tr) {
  background: transparent;
  transition:
    background-color 0.22s ease,
    transform 0.22s ease;
}

.value-table :deep(.el-table__body tr:hover) {
  background: rgba(14, 165, 233, 0.09);
  cursor: pointer;
}

.value-table :deep(.el-table__body tr:hover > td) {
  transition: color 0.2s ease;
}

.value-table :deep(.el-table__body tr.el-table__row--striped) {
  background: rgba(248, 250, 252, 0.55);
}

.value-table :deep(.el-table__body td) {
  border-bottom: 1px solid rgba(226, 232, 240, 0.5);
  color: #374151;
  font-size: 11px;
  padding-top: 3px;
  padding-bottom: 3px;
}

/* 表格内容样式 */
.item-type-tag {
  font-weight: 600;
  border-radius: 999px;
  padding: 0 7px;
  height: 19px;
  line-height: 17px;
  font-size: 10px;
}

.code-text {
  font-family: inherit;
  font-weight: 500;
  color: #0f172a;
}

.name-text {
  font-weight: 500;
  color: #1f2937;
}

.process-text {
  color: #b45309;
  font-weight: 600;
}

.quantity-text {
  font-family: inherit;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.unit-text {
  color: #64748b;
  font-size: 12px;
}

.price-text {
  font-family: inherit;
  font-weight: 600;
  color: #059669;
  font-variant-numeric: tabular-nums;
}

.value-text {
  font-family: inherit;
  font-weight: 700;
  color: #2563eb;
}

.value-text.summary-value {
  color: #f59e0b;
  font-size: 16px;
}

.value-text.high-value {
  color: #ef4444;
}

.value-text.medium-value {
  color: #f59e0b;
}

.date-text,
.datetime-text {
  font-family: inherit;
  color: #475569;
  font-size: 11px;
}

.no-data {
  color: #94a3b8;
  font-style: italic;
}

.btn-icon {
  font-size: 14px;
}

/* 分页样式 */
.pagination-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--iv-table-space);
  padding: var(--iv-table-space);
  margin-top: 0;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.95) 0%, rgba(241, 245, 249, 0.88) 100%);
  border-radius: 12px;
  backdrop-filter: blur(12px);
  border: 1px solid rgba(148, 163, 184, 0.22);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.75) inset;
  animation: iv-pagination-in 0.45s cubic-bezier(0.22, 1, 0.36, 1) 0.08s both;
  transition:
    box-shadow 0.35s ease,
    border-color 0.3s ease;
}

.product-summary {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 20px;
  padding: 8px 12px;
  margin-top: 0;
  border: 1px solid rgba(245, 158, 11, 0.25);
  border-radius: 10px;
  background: linear-gradient(90deg, rgba(255, 251, 235, 0.8), rgba(254, 243, 199, 0.55));
  color: #7c2d12;
}

.product-summary__item {
  font-size: 12px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.product-summary__item strong {
  color: #1f2937;
  font-size: 14px;
  font-variant-numeric: tabular-nums;
}

.product-summary__amount {
  color: #b45309 !important;
}

.pagination-container:hover {
  border-color: rgba(14, 165, 233, 0.2);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.85) inset,
    0 4px 14px rgba(14, 165, 233, 0.08);
}

.pagination-info {
  display: flex;
  align-items: center;
  gap: var(--iv-table-space);
}

@keyframes iv-pagination-in {
  from {
    opacity: 0;
    transform: translateY(4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.info-text {
  color: #475569;
  font-size: 9px;
}

.selected-info {
  color: #3b82f6;
  font-weight: 600;
  font-size: 10px;
}

.table-pagination :deep(.el-pagination) {
  color: #374151;
  background: transparent;
  --el-pagination-font-size: 10px;
}

.table-pagination :deep(.el-pagination .el-select .el-input__inner),
.table-pagination :deep(.el-pagination .el-input__inner),
.table-pagination :deep(.el-pagination .el-select__placeholder),
.table-pagination :deep(.el-pagination__sizes .el-select .el-select__wrapper) {
  font-size: 10px !important;
}

.table-pagination :deep(.el-pagination .el-pager li) {
  background: rgba(255, 255, 255, 0.95);
  color: #374151;
  border: 1px solid rgba(203, 213, 225, 0.85);
  border-radius: 8px;
  margin: 0 3px;
  min-width: 24px;
  height: 24px;
  line-height: 22px;
  font-weight: 600;
  transition:
    background 0.25s ease,
    border-color 0.25s ease,
    transform 0.2s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.25s ease;
}

.table-pagination :deep(.el-pagination .el-pager li:hover) {
  background: rgba(14, 165, 233, 0.12);
  border-color: rgba(14, 165, 233, 0.45);
  transform: translateY(-1px);
  box-shadow: 0 3px 10px rgba(14, 165, 233, 0.15);
}

.table-pagination :deep(.el-pagination .el-pager li.is-active) {
  background: linear-gradient(135deg, #0ea5e9, #0284c7);
  color: white;
  border-color: transparent;
}

.table-pagination :deep(.btn-prev),
.table-pagination :deep(.btn-next) {
  min-width: 22px;
  height: 22px;
}

/* 弹窗样式 */
.column-settings-dialog :deep(.el-dialog),
.detail-dialog :deep(.el-dialog),
.edit-dialog :deep(.el-dialog) {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(148, 163, 184, 0.24);
  border-radius: 12px;
  box-shadow: 0 16px 38px rgba(15, 23, 42, 0.14);
}

.column-settings-dialog :deep(.el-dialog__header),
.detail-dialog :deep(.el-dialog__header),
.edit-dialog :deep(.el-dialog__header) {
  background: rgba(248, 250, 252, 0.8);
  border-bottom: 1px solid rgba(226, 232, 240, 0.5);
  padding: 14px 18px;
}

.column-settings-dialog :deep(.el-dialog__title),
.detail-dialog :deep(.el-dialog__title),
.edit-dialog :deep(.el-dialog__title) {
  color: #374151;
  font-weight: 600;
}

.column-settings-dialog :deep(.el-dialog__body),
.detail-dialog :deep(.el-dialog__body),
.edit-dialog :deep(.el-dialog__body) {
  padding: 14px 16px;
  color: #374151;
}

/* 详情内容 */
.detail-content {
  color: #374151;
}

.detail-content :deep(.el-descriptions) {
  background: transparent;
}

.detail-content :deep(.el-descriptions__header) {
  background: rgba(248, 250, 252, 0.8);
  color: #374151;
}

.detail-content :deep(.el-descriptions__body) {
  background: transparent;
}

.detail-content :deep(.el-descriptions__table) {
  border-color: rgba(226, 232, 240, 0.5);
}

.detail-content :deep(.el-descriptions__cell) {
  border-color: rgba(226, 232, 240, 0.3);
}

.detail-content :deep(.el-descriptions__label) {
  background: rgba(248, 250, 252, 0.8);
  color: #64748b;
  font-weight: 500;
}

.detail-content :deep(.el-descriptions__content) {
  background: rgba(255, 255, 255, 0.7);
  color: #374151;
}

.detail-value {
  font-size: 18px;
  font-weight: 600;
  color: #3b82f6;
}

/* 编辑表单 */
.edit-content {
  color: #374151;
}

.edit-content :deep(.el-form-item__label) {
  color: #374151;
}

.edit-content :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.8);
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.edit-content :deep(.el-input__wrapper:hover) {
  border-color: #667eea;
}

.edit-content :deep(.el-input__wrapper.is-focus) {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.edit-content :deep(.el-input__inner) {
  color: #374151;
}

.edit-content :deep(.el-textarea__inner) {
  background: rgba(255, 255, 255, 0.8);
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  color: #374151;
  transition: all 0.3s ease;
}

.edit-content :deep(.el-textarea__inner:hover) {
  border-color: #667eea;
}

.edit-content :deep(.el-textarea__inner:focus) {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.current-price {
  font-size: 16px;
  font-weight: 600;
  color: #10b981;
}

.price-input {
  width: 200px;
}

.date-picker {
  width: 200px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 10px 16px;
  background: rgba(248, 250, 252, 0.8);
  border-top: 1px solid rgba(226, 232, 240, 0.5);
  backdrop-filter: blur(10px);
}

/* Element Plus 组件样式覆盖 */
:deep(.el-button) {
  border-radius: 10px;
  font-weight: 500;
  transition: all 0.3s ease;
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
}

:deep(.el-button--primary:hover) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

/* 响应式设计 */
@media (max-width: 1200px) {
}

@media (max-width: 768px) {
  .pagination-container {
    flex-direction: column;
    gap: var(--iv-table-space);
    padding: var(--iv-table-space);
  }

  .pagination-info {
    flex-direction: column;
    gap: var(--iv-table-space);
    text-align: center;
  }
}

@media (max-width: 480px) {
}

@media (prefers-reduced-motion: reduce) {
  .process-filter,
  .table-container,
  .pagination-container,
  .process-filter__btn,
  .value-table :deep(.el-table__body tr),
  .table-pagination :deep(.el-pagination .el-pager li) {
    animation: none !important;
    transition: none !important;
  }

  .process-filter__btn:hover,
  .process-filter__btn:active,
  .table-pagination :deep(.el-pagination .el-pager li:hover) {
    transform: none;
  }
}
</style>
