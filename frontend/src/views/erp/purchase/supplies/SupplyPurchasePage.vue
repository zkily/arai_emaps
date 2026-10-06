<template>
  <div class="supply-purchase-page pb-std">
    <div class="page-header pb-hero pb-hero--page">
      <div class="page-header-fx pb-bubbles" aria-hidden="true" />
      <div class="header-lead">
        <div class="title-icon"><el-icon><Box /></el-icon></div>
        <div class="title-copy">
          <h1 class="pb-hero-title">備品購入</h1>
          <p class="pb-hero-desc">仕入先を選び、カタログから備品を複数選択して発注します</p>
        </div>
      </div>
      <div class="header-stats">
        <div class="stat-card stat-card--blue">
          <span class="stat-number">{{ items.length }}</span>
          <span class="stat-label"><i class="stat-dot" />カタログ</span>
        </div>
        <div class="stat-card stat-card--amber">
          <span class="stat-number">{{ cart.length }}</span>
          <span class="stat-label"><i class="stat-dot" />発注明細</span>
        </div>
        <div class="stat-card stat-card--violet">
          <span class="stat-number">{{ orders.length }}</span>
          <span class="stat-label"><i class="stat-dot" />履歴</span>
        </div>
      </div>
      <div class="header-actions">
        <el-button
          v-if="canCreateMaster"
          size="small"
          class="ghost-btn"
          :icon="Plus"
          :disabled="!supplierCd"
          @click="openItemDialog()"
        >
          備品登録
        </el-button>
        <el-button
          type="primary"
          size="small"
          class="order-btn"
          :icon="ShoppingCart"
          :loading="orderSubmitting"
          :disabled="cart.length === 0"
          @click="submitOrder"
        >
          発注する
        </el-button>
      </div>
    </div>

    <div class="filter-bar">
      <div class="filter-chip">
        <el-icon><OfficeBuilding /></el-icon>
        <span>仕入先</span>
      </div>
      <el-select
        v-model="supplierCd"
        filterable
        clearable
        placeholder="仕入先を選択"
        size="small"
        class="filter-supplier"
        :loading="suppliersLoading"
        @change="onSupplierChange"
      >
        <el-option
          v-for="s in suppliers"
          :key="s.supplier_cd"
          :label="`${s.supplier_cd} ${s.supplier_name}`"
          :value="s.supplier_cd"
        />
      </el-select>
      <el-input
        v-model="keyword"
        size="small"
        clearable
        placeholder="備品CD・名称・規格"
        class="filter-keyword"
        :disabled="!supplierCd"
        @keyup.enter="loadItems"
      >
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-checkbox v-model="includeDiscontinued" :disabled="!supplierCd" @change="loadItems">
        終息を含む
      </el-checkbox>
      <el-button size="small" class="search-btn" :icon="Search" :disabled="!supplierCd" @click="loadItems">
        検索
      </el-button>
    </div>

    <div class="work-grid">
      <el-card shadow="never" class="panel-card catalog-card">
        <template #header>
          <div class="card-head">
            <div class="card-head__title">
              <span class="tone-dot tone-dot--blue" />
              <span>仕入先カタログ</span>
            </div>
            <div class="card-head__actions">
              <el-tag size="small" type="primary" effect="plain" round>{{ items.length }} 件</el-tag>
              <el-tag v-if="selectedItems.length" size="small" type="warning" effect="dark" round>
                選択 {{ selectedItems.length }}
              </el-tag>
              <el-button
                size="small"
                type="primary"
                class="add-cart-btn"
                :disabled="selectedItems.length === 0"
                @click="addSelectedToCart"
              >
                選択を追加
              </el-button>
            </div>
          </div>
        </template>
        <el-empty v-if="!supplierCd" description="先に仕入先を選択してください" :image-size="72" />
        <el-table
          v-else
          ref="tableRef"
          v-loading="itemsLoading"
          :data="items"
          size="small"
          stripe
          highlight-current-row
          class="modern-table"
          height="420"
          row-key="id"
          :header-cell-style="{ background: '#eff6ff', fontWeight: '600', color: '#1e3a8a' }"
          @selection-change="onSelectionChange"
        >
          <el-table-column type="selection" width="42" :selectable="canSelectItem" />
          <el-table-column prop="item_cd" label="備品CD" width="110" show-overflow-tooltip />
          <el-table-column prop="item_name" label="品名" min-width="140" show-overflow-tooltip />
          <el-table-column prop="specification" label="規格" min-width="110" show-overflow-tooltip />
          <el-table-column prop="unit" label="単位" width="64" align="center" />
          <el-table-column prop="pack_qty" label="個数" width="70" align="right" />
          <el-table-column prop="order_lot" label="注文ロット" width="90" align="right" />
          <el-table-column label="単価" width="90" align="right">
            <template #default="{ row }">{{ formatMoney(row.unit_price) }}</template>
          </el-table-column>
          <el-table-column label="終息" width="64" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.is_discontinued" size="small" type="info" effect="dark" round>終息</el-tag>
              <span v-else class="muted">—</span>
            </template>
          </el-table-column>
          <el-table-column v-if="canEditMaster || canDeleteMaster" label="" width="88" align="center">
            <template #default="{ row }">
              <el-button v-if="canEditMaster" link type="primary" size="small" @click="openItemDialog(row)">編集</el-button>
              <el-button v-if="canDeleteMaster" link type="danger" size="small" @click="removeItem(row)">削除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card shadow="never" class="panel-card cart-card">
        <template #header>
          <div class="card-head">
            <div class="card-head__title">
              <span class="tone-dot tone-dot--amber" />
              <span>発注明細</span>
            </div>
            <el-tag size="small" type="warning" effect="plain" round>{{ cart.length }} 品目</el-tag>
          </div>
        </template>
        <el-form label-width="72px" size="small" class="cart-meta">
          <el-form-item label="発注日">
            <el-date-picker v-model="orderDate" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
          </el-form-item>
          <el-form-item label="納入日">
            <el-date-picker v-model="deliveryDate" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
          </el-form-item>
          <el-form-item label="備考">
            <el-input v-model="orderRemarks" type="textarea" :rows="2" />
          </el-form-item>
        </el-form>
        <el-empty v-if="cart.length === 0" description="カタログから複数選択" :image-size="56" />
        <TransitionGroup v-else name="cart-item" tag="div" class="cart-list">
          <div v-for="row in cart" :key="row.id" class="cart-row">
            <div class="cart-row__name">
              <strong>{{ row.item_cd }}</strong>
              <span>{{ row.item_name }}</span>
            </div>
            <el-input-number
              v-model="row.order_qty"
              size="small"
              :min="1"
              :step="Math.max(1, row.order_lot)"
              controls-position="right"
            />
            <div class="cart-row__amt">{{ formatMoney(row.order_qty * row.unit_price) }}</div>
            <el-button link type="danger" size="small" @click="removeFromCart(row.id)">削除</el-button>
          </div>
        </TransitionGroup>
        <div class="cart-total">
          <span>合計</span>
          <strong>{{ formatMoney(cartTotal) }}</strong>
        </div>
      </el-card>
    </div>

    <el-card shadow="never" class="panel-card history-card">
      <template #header>
        <div class="card-head">
          <div class="card-head__title">
            <span class="tone-dot tone-dot--violet" />
            <span>発注履歴</span>
          </div>
          <el-button size="small" text class="refresh-btn" :icon="Refresh" @click="loadOrders">再取得</el-button>
        </div>
      </template>
      <el-table
        v-loading="ordersLoading"
        :data="orders"
        size="small"
        stripe
        highlight-current-row
        class="modern-table"
        height="240"
        :header-cell-style="{ background: '#f5f3ff', fontWeight: '600', color: '#4c1d95' }"
      >
        <el-table-column prop="order_no" label="発注番号" width="150" />
        <el-table-column prop="order_date" label="発注日" width="110" />
        <el-table-column prop="delivery_date" label="納入日" width="110" />
        <el-table-column prop="supplier_name" label="仕入先" min-width="140" show-overflow-tooltip />
        <el-table-column label="金額" width="110" align="right">
          <template #default="{ row }">{{ formatMoney(row.total_amount) }}</template>
        </el-table-column>
        <el-table-column label="状態" width="88" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status === 'cancelled' ? 'info' : 'success'" effect="dark" round>
              {{ row.status === 'cancelled' ? 'キャンセル' : '発注済' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="" width="150" align="center">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openOrderDetail(row)">明細</el-button>
            <el-button link type="primary" size="small" @click="openPrintDialog(row)">印刷</el-button>
            <el-button
              v-if="row.status !== 'cancelled'"
              link
              type="danger"
              size="small"
              @click="onCancelOrder(row)"
            >
              取消
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog
      v-model="itemDialogVisible"
      width="600px"
      class="spb-item-dialog pb-std"
      align-center
      destroy-on-close
      :show-close="false"
      :close-on-click-modal="false"
    >
      <template #header>
        <div class="item-dialog-header pb-hero" :class="itemForm.id ? 'is-edit' : 'is-new'">
          <div class="pb-bubbles" aria-hidden="true" />
          <div class="item-dialog-icon">
            <el-icon><Box /></el-icon>
          </div>
          <div class="item-dialog-copy">
            <h3>{{ itemForm.id ? '備品を編集' : '備品を登録' }}</h3>
            <p>{{ itemForm.id ? 'カタログ情報を更新します' : '自動採番のCDで新しい備品を登録します' }}</p>
          </div>
          <el-icon class="spb-close" @click="itemDialogVisible = false"><Close /></el-icon>
        </div>
      </template>
      <div class="item-dialog-body">
        <div class="item-cd-banner">
          <div class="item-cd-banner__mark">CD</div>
          <div class="item-cd-banner__meta">
            <span class="item-cd-banner__label">備品コード</span>
            <strong class="item-cd-banner__value">{{ itemForm.item_cd || '採番中…' }}</strong>
          </div>
          <el-tag size="small" effect="dark" round type="primary">自動採番</el-tag>
        </div>
        <el-form :model="itemForm" label-position="top" class="item-form">
          <section class="form-section">
            <header class="form-section__title">
              <span class="form-section__dot" />
              基本情報
            </header>
            <el-form-item label="品名" required>
              <el-input v-model="itemForm.item_name" placeholder="品名を入力" maxlength="200" />
            </el-form-item>
            <el-form-item label="規格">
              <el-input v-model="itemForm.specification" placeholder="規格・型番" maxlength="200" />
            </el-form-item>
          </section>
          <section class="form-section form-section--amber">
            <header class="form-section__title">
              <span class="form-section__dot" />
              発注条件
            </header>
            <div class="form-grid">
              <el-form-item label="単位">
                <el-input v-model="itemForm.unit" maxlength="20" placeholder="個" />
              </el-form-item>
              <el-form-item label="個数">
                <el-input-number v-model="itemForm.pack_qty" :min="1" controls-position="right" style="width: 100%" />
              </el-form-item>
              <el-form-item label="注文ロット">
                <el-input-number v-model="itemForm.order_lot" :min="1" controls-position="right" style="width: 100%" />
              </el-form-item>
              <el-form-item label="単価">
                <el-input-number
                  v-model="itemForm.unit_price"
                  :min="0"
                  :precision="2"
                  :step="0.01"
                  controls-position="right"
                  style="width: 100%"
                />
              </el-form-item>
            </div>
          </section>
          <section class="form-section form-section--slate">
            <header class="form-section__title">
              <span class="form-section__dot" />
              その他
            </header>
            <div class="status-row">
              <div>
                <div class="status-row__title">終息フラグ</div>
                <p class="status-row__hint">終息すると購買カタログから除外されます</p>
              </div>
              <el-switch v-model="itemForm.is_discontinued" inline-prompt active-text="終息" inactive-text="有効" />
            </div>
            <el-form-item label="備考">
              <el-input v-model="itemForm.remarks" type="textarea" :rows="2" placeholder="備考があれば入力" />
            </el-form-item>
          </section>
        </el-form>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button class="dialog-cancel" @click="itemDialogVisible = false">キャンセル</el-button>
          <el-button type="primary" class="dialog-save" :loading="itemSaving" @click="saveItem">
            <el-icon><Check /></el-icon>
            保存する
          </el-button>
        </div>
      </template>
    </el-dialog>

    <el-drawer
      v-model="detailVisible"
      size="480px"
      :show-close="false"
      class="spb-drawer pb-std"
    >
      <template #header>
        <div class="spb-drawer-hero pb-hero">
          <div class="pb-bubbles" aria-hidden="true" />
          <span class="spb-hero-icon"><el-icon><Tickets /></el-icon></span>
          <div class="spb-hero-copy">
            <span class="spb-hero-title">発注明細</span>
            <p class="spb-hero-desc">{{ orderDetail?.order_no || '—' }}・{{ orderDetail?.supplier_name || '' }}</p>
          </div>
          <el-icon class="spb-close" @click="detailVisible = false"><Close /></el-icon>
        </div>
      </template>
      <template v-if="orderDetail">
        <el-descriptions :column="1" size="small" border>
          <el-descriptions-item label="発注番号">{{ orderDetail.order_no }}</el-descriptions-item>
          <el-descriptions-item label="発注日">{{ orderDetail.order_date }}</el-descriptions-item>
          <el-descriptions-item label="納入日">{{ orderDetail.delivery_date || '—' }}</el-descriptions-item>
          <el-descriptions-item label="仕入先">
            {{ orderDetail.supplier_cd }} {{ orderDetail.supplier_name }}
          </el-descriptions-item>
          <el-descriptions-item label="合計">{{ formatMoney(orderDetail.total_amount) }}</el-descriptions-item>
        </el-descriptions>
        <el-table :data="orderDetail.lines || []" size="small" border class="detail-table">
          <el-table-column prop="item_cd" label="CD" width="90" />
          <el-table-column prop="item_name" label="品名" min-width="120" />
          <el-table-column prop="order_qty" label="数量" width="70" align="right" />
          <el-table-column label="金額" width="90" align="right">
            <template #default="{ row }">{{ formatMoney(row.amount) }}</template>
          </el-table-column>
        </el-table>
      </template>
    </el-drawer>

    <el-dialog
      v-model="printConfirmDialogVisible"
      width="650px"
      :close-on-click-modal="false"
      :show-close="false"
      class="spb-print-dialog pb-std"
    >
      <template #header>
        <div class="dialog-header-with-button pcd-hero pb-hero">
          <div class="pcd-hero-fx pb-bubbles" aria-hidden="true" />
          <span class="pcd-hero-icon"><el-icon><Printer /></el-icon></span>
          <div class="pcd-hero-copy">
            <span class="dialog-title">注文書印刷確認</span>
            <p class="pcd-hero-desc">{{ printTarget?.order_no || '—' }}・{{ printTarget?.supplier_name || '' }}</p>
          </div>
          <el-button size="small" class="confirm-btn-header" :loading="printLoading" @click="confirmPrint">
            <el-icon><Printer /></el-icon>
            印刷実行
          </el-button>
          <el-icon class="spb-close" @click="printConfirmDialogVisible = false"><Close /></el-icon>
        </div>
      </template>
      <div class="print-confirm-content-compact">
        <div class="form-sections-compact">
          <div class="form-section-compact pcd-sec pcd-sec--to">
            <div class="section-header-compact">
              <el-icon class="section-icon"><User /></el-icon>
              <span class="section-title">受注先情報</span>
            </div>
            <div class="form-fields-compact">
              <div class="form-field-row">
                <label class="field-label">納入日</label>
                <el-date-picker
                  v-model="printForm.deliveryDate"
                  type="date"
                  value-format="YYYY-MM-DD"
                  class="form-input-compact"
                  size="small"
                  style="width: 100%"
                />
              </div>
              <div class="form-field-row">
                <label class="field-label">受注先会社名</label>
                <el-input v-model="printForm.recipientCompany" class="form-input-compact" size="small" />
              </div>
              <div class="form-field-row">
                <label class="field-label">受注先担当者</label>
                <el-input v-model="printForm.recipientPersons" class="form-input-compact" size="small" />
              </div>
            </div>
          </div>
          <div class="form-section-compact pcd-sec pcd-sec--approve">
            <div class="section-header-compact">
              <el-icon class="section-icon"><EditPen /></el-icon>
              <span class="section-title">承認・発行情報</span>
            </div>
            <div class="form-fields-compact">
              <div class="form-field-row">
                <label class="field-label">承認者</label>
                <el-input v-model="printForm.approver" class="form-input-compact" size="small" />
              </div>
              <div class="form-field-row">
                <label class="field-label">発行者</label>
                <el-input v-model="printForm.issuer" class="form-input-compact" size="small" />
              </div>
            </div>
          </div>
          <div class="form-section-compact pcd-sec pcd-sec--note">
            <div class="section-header-compact">
              <el-icon class="section-icon"><Box /></el-icon>
              <span class="section-title">備考・注意事項</span>
            </div>
            <div class="form-fields-compact">
              <div class="form-field-row">
                <label class="field-label">備考1</label>
                <el-input v-model="printForm.note1" type="textarea" :rows="2" class="form-textarea-compact" size="small" />
              </div>
              <div class="form-field-row">
                <label class="field-label">備考2</label>
                <el-input v-model="printForm.note2" type="textarea" :rows="2" class="form-textarea-compact" size="small" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type TableInstance } from 'element-plus'
import {
  Box,
  Check,
  Close,
  EditPen,
  OfficeBuilding,
  Plus,
  Printer,
  Refresh,
  Search,
  ShoppingCart,
  Tickets,
  User,
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { getSupplierList } from '@/api/master/supplierMaster'
import {
  cancelSupplyOrder,
  createSupplyItem,
  createSupplyOrder,
  deleteSupplyItem,
  fetchNextSupplyItemCd,
  fetchSupplyItems,
  fetchSupplyOrder,
  fetchSupplyOrders,
  updateSupplyItem,
  type SupplyItem,
  type SupplyPurchaseOrder,
} from '@/api/supplyPurchase'
import { MARUICHI_ORDER_SHEET_STYLES } from '@/utils/maruichiOrderSheetStyles'
import { usePurchaseOperationPermission } from '@/composables/usePurchaseOperationPermission'
import { guardPurchaseOperation } from '@/utils/purchaseOperationGuard'
import { useMasterOperationPermission } from '@/composables/useMasterOperationPermission'
import { guardMasterOperation } from '@/utils/masterOperationGuard'

const { canCreate, canDelete } = usePurchaseOperationPermission()
const {
  canCreate: canCreateMaster,
  canEdit: canEditMaster,
  canDelete: canDeleteMaster,
} = useMasterOperationPermission()

interface CartRow extends SupplyItem {
  order_qty: number
}

const suppliers = ref<{ supplier_cd: string; supplier_name: string }[]>([])
const suppliersLoading = ref(false)
const supplierCd = ref('')
const keyword = ref('')
const includeDiscontinued = ref(false)
const items = ref<SupplyItem[]>([])
const itemsLoading = ref(false)
const tableRef = ref<TableInstance>()
const selectedItems = ref<SupplyItem[]>([])
const cart = ref<CartRow[]>([])
const orderDate = ref(dayjs().format('YYYY-MM-DD'))
const deliveryDate = ref(dayjs().format('YYYY-MM-DD'))
const orderRemarks = ref('')
const orderSubmitting = ref(false)
const orders = ref<SupplyPurchaseOrder[]>([])
const ordersLoading = ref(false)
const itemDialogVisible = ref(false)
const itemSaving = ref(false)
const detailVisible = ref(false)
const orderDetail = ref<SupplyPurchaseOrder | null>(null)
const printConfirmDialogVisible = ref(false)
const printLoading = ref(false)
const printTarget = ref<SupplyPurchaseOrder | null>(null)
const printForm = reactive({
  recipientCompany: '',
  recipientPersons: '',
  deliveryDate: '',
  approver: '篠田',
  issuer: '趙',
  note1: '1.支払期日には法定税率による消費税額及び地方消費税分を加算して支払います。',
  note2:
    '2.支払期日・支払方法・検査完了期日・有償支給原材料代金の決済期日及び方法については、令和8年7月1日の「支払方法等について」によります。',
})

const itemForm = reactive({
  id: 0,
  item_cd: '',
  item_name: '',
  specification: '',
  unit: '個',
  pack_qty: 1,
  order_lot: 1,
  unit_price: 0,
  is_discontinued: false,
  remarks: '',
})

const cartTotal = computed(() =>
  cart.value.reduce((sum, r) => sum + Number(r.order_qty || 0) * Number(r.unit_price || 0), 0),
)

function formatMoney(v: number) {
  return Number(v || 0).toLocaleString('ja-JP', { style: 'currency', currency: 'JPY' })
}

function canSelectItem(row: SupplyItem) {
  return !row.is_discontinued
}

function onSelectionChange(rows: SupplyItem[]) {
  selectedItems.value = rows
}

function addSelectedToCart() {
  const existing = new Set(cart.value.map((r) => r.id))
  let added = 0
  for (const r of selectedItems.value) {
    if (r.is_discontinued || existing.has(r.id)) continue
    cart.value.push({
      ...r,
      order_qty: Math.max(1, Number(r.order_lot || 1)),
    })
    existing.add(r.id)
    added += 1
  }
  if (added === 0) {
    ElMessage.info('追加できる品目がありません（終息または追加済み）')
    return
  }
  tableRef.value?.clearSelection()
}

function removeFromCart(id: number) {
  cart.value = cart.value.filter((r) => r.id !== id)
}

async function loadSuppliers() {
  suppliersLoading.value = true
  try {
    const res = await getSupplierList({ page: 1, pageSize: 5000 })
    suppliers.value = (res.data?.list ?? res.list ?? []).map((s) => ({
      supplier_cd: s.supplier_cd,
      supplier_name: s.supplier_name,
    }))
  } catch {
    ElMessage.error('仕入先一覧の取得に失敗しました')
  } finally {
    suppliersLoading.value = false
  }
}

async function loadItems() {
  if (!supplierCd.value) {
    items.value = []
    cart.value = []
    return
  }
  itemsLoading.value = true
  try {
    const res = await fetchSupplyItems({
      supplierCd: supplierCd.value,
      keyword: keyword.value || undefined,
      includeDiscontinued: includeDiscontinued.value,
      pageSize: 500,
    })
    items.value = res.list
  } catch {
    ElMessage.error('備品一覧の取得に失敗しました')
  } finally {
    itemsLoading.value = false
  }
}

async function loadOrders() {
  ordersLoading.value = true
  try {
    const res = await fetchSupplyOrders({
      supplierCd: supplierCd.value || undefined,
      pageSize: 50,
    })
    orders.value = res.list
  } catch {
    ElMessage.error('発注履歴の取得に失敗しました')
  } finally {
    ordersLoading.value = false
  }
}

function onSupplierChange() {
  cart.value = []
  selectedItems.value = []
  tableRef.value?.clearSelection()
  void loadItems()
  void loadOrders()
}

async function openItemDialog(row?: SupplyItem) {
  if (row ? !guardMasterOperation(canEditMaster) : !guardMasterOperation(canCreateMaster)) return
  if (!supplierCd.value) {
    ElMessage.warning('仕入先を選択してください')
    return
  }
  itemForm.id = row?.id ?? 0
  itemForm.item_cd = row?.item_cd ?? ''
  itemForm.item_name = row?.item_name ?? ''
  itemForm.specification = row?.specification ?? ''
  itemForm.unit = row?.unit || '個'
  itemForm.pack_qty = row?.pack_qty ?? 1
  itemForm.order_lot = row?.order_lot ?? 1
  itemForm.unit_price = row?.unit_price ?? 0
  itemForm.is_discontinued = row?.is_discontinued ?? false
  itemForm.remarks = row?.remarks ?? ''
  itemDialogVisible.value = true
  if (!row) {
    try {
      itemForm.item_cd = await fetchNextSupplyItemCd()
    } catch {
      itemForm.item_cd = 'B0001'
    }
  }
}

async function saveItem() {
  if (!itemForm.item_cd.trim() || !itemForm.item_name.trim()) {
    ElMessage.warning('備品CDと品名を入力してください')
    return
  }
  itemSaving.value = true
  try {
    const payload = {
      item_cd: itemForm.item_cd.trim(),
      item_name: itemForm.item_name.trim(),
      specification: itemForm.specification,
      unit: itemForm.unit,
      pack_qty: itemForm.pack_qty,
      order_lot: itemForm.order_lot,
      unit_price: itemForm.unit_price,
      supplier_cd: supplierCd.value,
      is_discontinued: itemForm.is_discontinued,
      remarks: itemForm.remarks,
    }
    if (itemForm.id) {
      await updateSupplyItem(itemForm.id, payload)
    } else {
      await createSupplyItem(payload)
    }
    ElMessage.success('保存しました')
    itemDialogVisible.value = false
    await loadItems()
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(typeof detail === 'string' ? detail : '保存に失敗しました')
  } finally {
    itemSaving.value = false
  }
}

async function removeItem(row: SupplyItem) {
  if (!guardMasterOperation(canDeleteMaster)) return
  try {
    await ElMessageBox.confirm(`「${row.item_cd} ${row.item_name}」を削除しますか？`, '確認', {
      type: 'warning',
    })
    await deleteSupplyItem(row.id)
    ElMessage.success('削除しました')
    await loadItems()
  } catch {
    /* cancel */
  }
}

async function submitOrder() {
  if (!guardPurchaseOperation(canCreate)) return
  if (!supplierCd.value || cart.value.length === 0) return
  if (!deliveryDate.value) {
    ElMessage.warning('納入日を指定してください')
    return
  }
  const notLot = cart.value.filter(
    (r) => r.order_lot > 1 && r.order_qty % r.order_lot !== 0,
  )
  if (notLot.length > 0) {
    try {
      await ElMessageBox.confirm(
        `注文ロットの倍数でない明細があります。このまま発注しますか？`,
        '確認',
        { type: 'warning' },
      )
    } catch {
      return
    }
  }
  orderSubmitting.value = true
  try {
    const created = await createSupplyOrder({
      supplier_cd: supplierCd.value,
      order_date: orderDate.value,
      delivery_date: deliveryDate.value,
      remarks: orderRemarks.value || undefined,
      lines: cart.value.map((r) => ({ item_id: r.id, order_qty: r.order_qty })),
    })
    ElMessage.success(`発注しました（${created.order_no}）`)
    cart.value = []
    tableRef.value?.clearSelection()
    orderRemarks.value = ''
    await loadOrders()
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(typeof detail === 'string' ? detail : '発注に失敗しました')
  } finally {
    orderSubmitting.value = false
  }
}

async function openOrderDetail(row: SupplyPurchaseOrder) {
  try {
    orderDetail.value = await fetchSupplyOrder(row.id)
    detailVisible.value = true
  } catch {
    ElMessage.error('明細の取得に失敗しました')
  }
}

async function onCancelOrder(row: SupplyPurchaseOrder) {
  if (!guardPurchaseOperation(canDelete)) return
  try {
    await ElMessageBox.confirm(`発注 ${row.order_no} をキャンセルしますか？`, '確認', { type: 'warning' })
    await cancelSupplyOrder(row.id)
    ElMessage.success('キャンセルしました')
    await loadOrders()
  } catch {
    /* cancel */
  }
}

async function openPrintDialog(row: SupplyPurchaseOrder) {
  try {
    printTarget.value = await fetchSupplyOrder(row.id)
    const name = printTarget.value.supplier_name || printTarget.value.supplier_cd
    printForm.recipientCompany = name ? `${name} 御中` : ''
    printForm.deliveryDate = printTarget.value.delivery_date || printTarget.value.order_date || ''
    printConfirmDialogVisible.value = true
  } catch {
    ElMessage.error('印刷データの取得に失敗しました')
  }
}

function escapeHtml(value: unknown) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function formatPrintMoney(v: number) {
  return Number(v || 0).toLocaleString('ja-JP', {
    style: 'currency',
    currency: 'JPY',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function generatePrintHtml(detail: SupplyPurchaseOrder) {
  const issuedDateTime = new Date().toLocaleString('ja-JP', {
    timeZone: 'Asia/Tokyo',
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
  const lines = detail.lines || []
  const tableRowsHtml = lines
    .map(
      (ln) => `
      <tr>
        <td>${escapeHtml(ln.item_name)}</td>
        <td class="text-center">${escapeHtml(ln.specification || '')}</td>
        <td class="text-center">${escapeHtml(ln.unit)}</td>
        <td class="text-right">${escapeHtml(ln.order_qty)}</td>
        <td class="text-right">${escapeHtml(formatPrintMoney(ln.unit_price))}</td>
        <td class="text-right">${escapeHtml(formatPrintMoney(ln.amount))}</td>
      </tr>`,
    )
    .join('')

  return `
    <div class="order-sheet">
      <div class="order-sheet-main">
      <div class="issued-info">発行日: ${escapeHtml(issuedDateTime)}</div>

      <div class="title">注 文 書</div>

      <div class="header">
        <div class="recipient-block">
          <div>${escapeHtml(printForm.recipientCompany)}</div>
          <div>${escapeHtml(printForm.recipientPersons)}</div>
        </div>

        <div class="sender-block">
          <div>日鉄物産荒井オートモーティブ(株)     </div>
          <div>〒496-0902 愛知県愛西市須依町2189  </div>
          <div>TEL<0567>28-4171</div>
          <div>FAX<0567>26-2281</div>
          <div class="approval-box">
            <table>
              <tr>
                <td>承認</td>
                <td>発行</td>
              </tr>
              <tr>
                <td>${escapeHtml(printForm.approver)}</td>
                <td>${escapeHtml(printForm.issuer)}</td>
              </tr>
            </table>
          </div>
        </div>

        <div class="delivery-info">
          <div>納入日 ${escapeHtml(printForm.deliveryDate || detail.delivery_date || '')}</div>
          <div>(納入場所:製品倉庫)</div>
        </div>
      </div>

      <table>
        <thead>
          <tr>
            <th width="26%">品名</th>
            <th width="18%">規格</th>
            <th width="10%">単位</th>
            <th width="12%">数量</th>
            <th width="16%">単価</th>
            <th width="18%">金額</th>
          </tr>
        </thead>
        <tbody>
          ${tableRowsHtml}
        </tbody>
      </table>

      <div class="summary-row">
        <div class="summary-item">品目数  ${lines.length}</div>
        <div class="summary-item">合計金額  ${escapeHtml(formatPrintMoney(detail.total_amount))}</div>
      </div>
      </div>

      <div class="notes">
        <p>${escapeHtml(printForm.note1)}</p>
        <p>${escapeHtml(printForm.note2)}</p>
      </div>
    </div>
  `
}

const MATERIAL_ORDER_SHEET_SIDE_MARGIN_EXTRA_CSS = `
  body {
    margin-left: 0.7cm !important;
    margin-right: 0.7cm !important;
  }
  @page {
    margin-left: 0.7cm;
    margin-right: 0.7cm;
  }
  .sender-block {
    margin-top: calc(-12mm + 30px) !important;
  }
`

async function confirmPrint() {
  const detail = printTarget.value
  if (!detail) return
  printLoading.value = true
  try {
    const printContent = generatePrintHtml(detail)
    const printWindow = window.open('', '_blank')
    if (!printWindow) {
      ElMessage.warning('ポップアップがブロックされました')
      return
    }
    printWindow.document.write(`
      <html>
      <head>
        <title>注文書</title>
        <meta charset="UTF-8">
        <style>${MARUICHI_ORDER_SHEET_STYLES}${MATERIAL_ORDER_SHEET_SIDE_MARGIN_EXTRA_CSS}</style>
      </head>
      <body>${printContent}</body>
      </html>
    `)
    printWindow.document.close()
    printWindow.onload = function () {
      printWindow.print()
      setTimeout(function () {
        printWindow.close()
      }, 1000)
    }
    printConfirmDialogVisible.value = false
  } catch {
    ElMessage.error('印刷プレビューの生成に失敗しました')
  } finally {
    printLoading.value = false
  }
}

onMounted(async () => {
  await loadSuppliers()
  await loadOrders()
})
</script>

<style scoped>
.supply-purchase-page {
  padding: 10px 12px 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 100%;
  background:
    radial-gradient(1200px 280px at 8% -10%, rgba(59, 130, 246, 0.1), transparent 55%),
    radial-gradient(900px 240px at 92% 0%, rgba(245, 158, 11, 0.08), transparent 50%),
    linear-gradient(180deg, #f1f6ff 0%, #f8fafc 42%, #f5f7fb 100%);
}

/* ---------- タイトル領域 ---------- */
.page-header {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border-radius: 14px;
  color: #fff;
  background: linear-gradient(125deg, #1d4ed8 0%, #2563eb 40%, #0ea5e9 78%, #38bdf8 100%);
  box-shadow:
    0 10px 24px -14px rgba(37, 99, 235, 0.55),
    inset 0 1px 0 rgba(255, 255, 255, 0.25);
}
.header-lead {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}
.title-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: #fff;
  background: linear-gradient(150deg, rgba(255, 255, 255, 0.36), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.42);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.4),
    inset 0 -2px 0 rgba(30, 58, 138, 0.28);
}
.title-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.page-header h1 {
  font-weight: 800;
  letter-spacing: 0.03em;
  color: #fff;
}
.page-header p {
  color: rgba(255, 255, 255, 0.88);
}

/* 統計：白ピル＋同色ドット */
.header-stats {
  display: flex;
  gap: 8px;
  margin-left: auto;
}
.stat-card {
  --accent: #2563eb;
  min-width: 78px;
  padding: 5px 12px;
  border-radius: 12px;
  text-align: center;
  background: linear-gradient(180deg, #ffffff 0%, #f5f9ff 100%);
  border: 1px solid rgba(255, 255, 255, 0.9);
  box-shadow:
    inset 0 -2px 0 color-mix(in srgb, var(--accent) 16%, transparent),
    0 4px 10px -6px rgba(15, 23, 42, 0.35);
}
.stat-card--amber {
  --accent: #d97706;
}
.stat-card--violet {
  --accent: #7c3aed;
}
.stat-number {
  display: block;
  font-weight: 800;
  color: color-mix(in srgb, var(--accent) 82%, #0f172a);
  font-variant-numeric: tabular-nums;
}
.stat-label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-weight: 600;
  color: #475569;
}
.stat-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--accent) 20%, transparent);
}
.header-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

/* 備品登録：ヒーロー上の白ピル */
.ghost-btn {
  --k-rgb: 37 99 235;
  height: 30px;
  padding: 0 14px;
  border-radius: 999px;
  font-weight: 700;
  color: #1d4ed8;
  border: 1px solid rgba(255, 255, 255, 0.9);
  background: linear-gradient(180deg, #ffffff 0%, #eef5ff 100%);
}
.ghost-btn:not(.is-disabled):hover,
.ghost-btn:not(.is-disabled):focus-visible {
  color: #1e40af;
  border-color: #fff;
  background: #fff;
}

/* 発注する：アンバーの立体ボタン */
.order-btn {
  --k-rgb: 234 88 12;
  height: 30px;
  padding: 0 16px;
  border-radius: 999px;
  font-weight: 800;
  color: #fff;
  border: 1px solid #c2410c;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.24) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #fbbf24, #ea580c);
}
.order-btn:not(.is-disabled):hover,
.order-btn:not(.is-disabled):focus-visible {
  color: #fff;
  border-color: #9a3412;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.28) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #fcd34d, #f97316);
}
.supply-purchase-page .ghost-btn.is-disabled,
.supply-purchase-page .order-btn.is-disabled,
.supply-purchase-page .search-btn.is-disabled,
.supply-purchase-page .add-cart-btn.is-disabled {
  color: #94a3b8;
  border-color: #d1d5db;
  background: #e5e7eb;
}

/* ---------- 絞り込み ---------- */
.filter-bar {
  position: relative;
  overflow: hidden;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 10px 12px 10px 15px;
  background: #fff;
  border: 1px solid #dbe7fb;
  border-radius: 12px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}
.filter-bar::before {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 3px;
  background: linear-gradient(180deg, #60a5fa, #2563eb);
}
.filter-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 700;
  box-shadow:
    inset 0 1px 0 #fff,
    inset 0 -1px 0 #bfdbfe;
}
.filter-supplier {
  width: 280px;
}
.filter-keyword {
  width: 220px;
}
.filter-bar :deep(.el-input__wrapper),
.filter-bar :deep(.el-select__wrapper),
.cart-meta :deep(.el-input__wrapper),
.cart-meta :deep(.el-textarea__inner) {
  border-radius: 8px;
  background-color: #fff;
  box-shadow: 0 0 0 1px #d6e2f5 inset;
}
.filter-bar :deep(.el-input__wrapper:hover),
.filter-bar :deep(.el-select__wrapper:hover),
.cart-meta :deep(.el-input__wrapper:hover),
.cart-meta :deep(.el-textarea__inner:hover) {
  box-shadow: 0 0 0 1px #93c5fd inset;
}
.filter-bar :deep(.el-input__wrapper.is-focus),
.filter-bar :deep(.el-select__wrapper.is-focused),
.cart-meta :deep(.el-input__wrapper.is-focus),
.cart-meta :deep(.el-textarea__inner:focus) {
  box-shadow:
    0 0 0 1px #2563eb inset,
    0 0 0 3px rgba(37, 99, 235, 0.14);
}
.filter-bar :deep(.el-input.is-disabled .el-input__wrapper) {
  background-color: #f1f5f9;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
}
.search-btn,
.add-cart-btn {
  --k-rgb: 37 99 235;
  border-radius: 8px;
  font-weight: 700;
  color: #fff;
  border: 1px solid #1d4ed8;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #3b82f6, #1d4ed8);
}
.search-btn:not(.is-disabled):hover,
.search-btn:not(.is-disabled):focus-visible,
.add-cart-btn:not(.is-disabled):hover,
.add-cart-btn:not(.is-disabled):focus-visible {
  color: #fff;
  border-color: #1e40af;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.26) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #60a5fa, #2563eb);
}

/* ---------- パネル ---------- */
.work-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.7fr) minmax(280px, 0.9fr);
  gap: 10px;
}
.panel-card {
  --accent: #3b82f6;
  position: relative;
  border: 1px solid #e2e8f0 !important;
  border-radius: 12px !important;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}
.panel-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  z-index: 1;
  background: linear-gradient(90deg, var(--accent), color-mix(in srgb, var(--accent) 35%, #fff));
}
.cart-card {
  --accent: #f59e0b;
}
.history-card {
  --accent: #8b5cf6;
}
.panel-card :deep(.el-card__header) {
  padding: 10px 12px 9px;
  background: linear-gradient(180deg, color-mix(in srgb, var(--accent) 6%, #fff), #fff);
  border-bottom: 1px solid color-mix(in srgb, var(--accent) 14%, #e2e8f0);
}
.panel-card :deep(.el-card__body) {
  padding: 10px 12px;
}
.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 750;
  font-size: 13px;
  color: #0f172a;
}
.card-head__title {
  display: flex;
  align-items: center;
  gap: 8px;
}
.card-head__actions {
  display: flex;
  align-items: center;
  gap: 6px;
}
.tone-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.16);
}
.tone-dot--amber {
  background: #f59e0b;
  box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.18);
}
.tone-dot--violet {
  background: #8b5cf6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.18);
}
.muted {
  color: #94a3b8;
}

/* 表：淡色・行ホバーのみ */
.modern-table {
  border-radius: 8px;
  overflow: hidden;
  --el-table-border-color: #e8eef7;
}
.modern-table :deep(.el-table__row:hover > td) {
  background: rgba(59, 130, 246, 0.06) !important;
}
.history-card .modern-table :deep(.el-table__row:hover > td) {
  background: rgba(139, 92, 246, 0.06) !important;
}

/* 行操作：小さなピル */
.modern-table :deep(.el-button.is-link),
.cart-row :deep(.el-button.is-link) {
  height: 22px;
  padding: 0 8px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  border: 1px solid #bfdbfe;
  background: #eff6ff;
  color: #1d4ed8;
  transition:
    background-color 0.15s ease,
    border-color 0.15s ease;
}
.modern-table :deep(.el-button.is-link + .el-button.is-link) {
  margin-left: 4px;
}
.modern-table :deep(.el-button--primary.is-link:hover) {
  background: #dbeafe;
  border-color: #93c5fd;
  color: #1e40af;
}
.modern-table :deep(.el-button--danger.is-link),
.cart-row :deep(.el-button--danger.is-link) {
  border-color: #fecaca;
  background: #fef2f2;
  color: #dc2626;
}
.modern-table :deep(.el-button--danger.is-link:hover),
.cart-row :deep(.el-button--danger.is-link:hover) {
  border-color: #fca5a5;
  background: #fee2e2;
  color: #b91c1c;
}

/* ---------- 発注明細（カート） ---------- */
.cart-meta {
  margin-bottom: 8px;
  padding: 8px 8px 0;
  border-radius: 10px;
  background: linear-gradient(180deg, #fffbeb, #fff);
  border: 1px solid #fde68a;
}
.cart-meta :deep(.el-form-item) {
  margin-bottom: 8px;
}
.cart-meta :deep(.el-form-item__label) {
  font-weight: 700;
  color: #92400e;
}
.cart-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 260px;
  overflow: auto;
}
.cart-row {
  position: relative;
  overflow: hidden;
  display: grid;
  grid-template-columns: 1fr 110px 72px auto;
  gap: 6px;
  align-items: center;
  padding: 7px 8px 7px 11px;
  background: #fff;
  border: 1px solid #fde4c3;
  border-radius: 9px;
}
.cart-row::before {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 3px;
  background: linear-gradient(180deg, #fcd34d, #f59e0b);
}
.cart-item-enter-active,
.cart-item-leave-active {
  transition: all 0.22s ease;
}
.cart-item-enter-from,
.cart-item-leave-to {
  opacity: 0;
  transform: translateX(12px);
}
.cart-row__name {
  display: flex;
  flex-direction: column;
  min-width: 0;
  font-size: 12px;
}
.cart-row__name strong {
  color: #0f172a;
}
.cart-row__name span {
  color: #64748b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.cart-row__amt {
  text-align: right;
  font-variant-numeric: tabular-nums;
  font-size: 12px;
  font-weight: 700;
  color: #c2410c;
}
.cart-total {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 10px;
  padding: 9px 12px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 700;
  color: #9a3412;
  background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%);
  border: 1px solid #fdba74;
  box-shadow:
    inset 0 1px 0 #fff,
    inset 0 -2px 0 rgba(234, 88, 12, 0.12);
}
.cart-total strong {
  font-size: 17px;
  font-weight: 800;
  color: #c2410c;
  font-variant-numeric: tabular-nums;
}

.refresh-btn.el-button {
  height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  font-weight: 700;
  color: #6d28d9;
  border: 1px solid #ddd6fe;
  background: #f5f3ff;
}
.refresh-btn.el-button:hover {
  color: #5b21b6;
  border-color: #c4b5fd;
  background: #ede9fe;
}

@media (max-width: 1100px) {
  .work-grid {
    grid-template-columns: 1fr;
  }
  .page-header {
    flex-wrap: wrap;
  }
  .header-stats {
    margin-left: 0;
  }
}

/* ============================================================
 * 共通：ダイアログ／ドロワーのヒーローと閉じるボタン
 * （append 先で scope 属性が付かないため外枠は :global で指定）
 * ============================================================ */
.spb-close {
  flex-shrink: 0;
  width: 30px;
  height: 30px;
  padding: 6px;
  box-sizing: border-box;
  border-radius: 9px;
  font-size: 18px;
  color: #fff;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.25);
  transition:
    transform 0.2s ease,
    background 0.2s ease;
}
.spb-close:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

/* ---------- 備品登録／編集ダイアログ ---------- */
:global(.el-dialog.spb-item-dialog) {
  padding: 0;
  border-radius: 14px;
  overflow: hidden;
  box-shadow:
    0 24px 48px -16px rgba(30, 58, 138, 0.4),
    0 0 0 1px rgba(37, 99, 235, 0.1);
}
:global(.el-dialog.spb-item-dialog .el-dialog__header) {
  padding: 0;
  margin: 0;
}
:global(.el-dialog.spb-item-dialog .el-dialog__body) {
  padding: 0;
  background: linear-gradient(180deg, #f8fbff, #f5f7fb);
}
:global(.el-dialog.spb-item-dialog .el-dialog__footer) {
  padding: 12px 18px 14px;
  background: #fff;
  border-top: 1px solid #e2e8f0;
}
.item-dialog-header {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  color: #fff;
  background: linear-gradient(125deg, #1d4ed8 0%, #2563eb 40%, #0ea5e9 78%, #38bdf8 100%);
}
.item-dialog-header.is-edit {
  background: linear-gradient(125deg, #b45309 0%, #d97706 40%, #f59e0b 76%, #fbbf24 100%);
}
.item-dialog-icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  background: linear-gradient(150deg, rgba(255, 255, 255, 0.36), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.42);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(15, 23, 42, 0.18);
}
.item-dialog-copy {
  flex: 1;
  min-width: 0;
}
.item-dialog-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 800;
  line-height: 1.3;
  letter-spacing: 0.03em;
}
.item-dialog-header p {
  margin: 3px 0 0;
  overflow: hidden;
  font-size: 11px;
  white-space: nowrap;
  text-overflow: ellipsis;
  color: rgba(255, 255, 255, 0.88);
}
.item-dialog-body {
  padding: 14px 16px 6px;
}
.item-cd-banner {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
  padding: 10px 14px 10px 17px;
  border-radius: 12px;
  background: linear-gradient(135deg, #eff6ff 0%, #fff 70%);
  border: 1px solid #bfdbfe;
}
.item-cd-banner::before {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 3px;
  background: linear-gradient(180deg, #60a5fa, #2563eb);
}
.item-cd-banner__mark {
  flex-shrink: 0;
  width: 38px;
  height: 38px;
  border-radius: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.06em;
  color: #fff;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #3b82f6, #1d4ed8);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(30, 58, 138, 0.3);
}
.item-cd-banner__meta {
  flex: 1;
  min-width: 0;
}
.item-cd-banner__label {
  display: block;
  font-size: 11px;
  color: #64748b;
  font-weight: 600;
}
.item-cd-banner__value {
  display: block;
  margin-top: 2px;
  font-size: 20px;
  letter-spacing: 0.08em;
  color: #1d4ed8;
  font-family: Consolas, Monaco, monospace;
  line-height: 1.1;
}
.form-section {
  --accent: #2563eb;
  position: relative;
  overflow: hidden;
  margin-bottom: 10px;
  padding: 12px 14px 4px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid color-mix(in srgb, var(--accent) 18%, #e2e8f0);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}
.form-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--accent), color-mix(in srgb, var(--accent) 30%, #fff));
}
.form-section--amber {
  --accent: #f59e0b;
}
.form-section--slate {
  --accent: #64748b;
}
.form-section__title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.06em;
  color: #334155;
}
.form-section__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 20%, transparent);
}
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 12px;
}
.item-form :deep(.el-form-item) {
  margin-bottom: 12px;
}
.item-form :deep(.el-form-item__label) {
  font-weight: 700;
  color: #475569;
  margin-bottom: 4px !important;
}
.item-form :deep(.el-input-number) {
  width: 100%;
}
.item-form :deep(.el-input__wrapper),
.item-form :deep(.el-select__wrapper),
.item-form :deep(.el-textarea__inner) {
  border-radius: 8px;
  box-shadow: 0 0 0 1px #d6e2f5 inset;
}
.item-form :deep(.el-input__wrapper:hover),
.item-form :deep(.el-select__wrapper:hover),
.item-form :deep(.el-textarea__inner:hover) {
  box-shadow: 0 0 0 1px #93c5fd inset;
}
.item-form :deep(.el-input__wrapper.is-focus),
.item-form :deep(.el-select__wrapper.is-focused),
.item-form :deep(.el-textarea__inner:focus) {
  box-shadow:
    0 0 0 1px #2563eb inset,
    0 0 0 3px rgba(37, 99, 235, 0.14);
}
.status-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 9px 12px;
  margin-bottom: 10px;
  border-radius: 10px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}
.status-row__title {
  font-size: 13px;
  font-weight: 700;
  color: #334155;
}
.status-row__hint {
  margin: 2px 0 0;
  font-size: 11px;
  color: #94a3b8;
}
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
.dialog-cancel {
  --k-rgb: 100 116 139;
  height: 34px;
  border-radius: 9px;
  font-weight: 700;
  color: #475569;
  border: 1px solid #d6dde8;
  background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%);
}
.dialog-save {
  --k-rgb: 37 99 235;
  min-width: 118px;
  height: 34px;
  border-radius: 9px;
  font-weight: 800;
  color: #fff;
  border: 1px solid #1d4ed8;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #3b82f6, #1d4ed8);
}
.dialog-save:not(.is-disabled):hover,
.dialog-save:not(.is-disabled):focus-visible {
  color: #fff;
  border-color: #1e40af;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.26) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #60a5fa, #2563eb);
}
.dialog-save .el-icon {
  margin-right: 4px;
}

/* ---------- 発注明細ドロワー（violet） ---------- */
:global(.el-drawer.spb-drawer .el-drawer__header) {
  margin: 0;
  padding: 0;
}
:global(.el-drawer.spb-drawer .el-drawer__body) {
  padding: 14px 16px;
  background: #f8fafc;
}
:global(.el-drawer.spb-drawer .el-descriptions__label) {
  width: 96px;
  font-weight: 700;
  color: #5b21b6 !important;
  background: #f5f3ff !important;
}
:global(.el-drawer.spb-drawer .el-descriptions__body) {
  border-radius: 10px;
  overflow: hidden;
}
:global(.el-drawer.spb-drawer .detail-table th.el-table__cell) {
  font-weight: 700;
  color: #4c1d95;
  background: #f5f3ff;
}
.spb-drawer-hero {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  color: #fff;
  background: linear-gradient(125deg, #4c1d95 0%, #6d28d9 38%, #8b5cf6 72%, #a78bfa 100%);
}
.spb-hero-icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  background: linear-gradient(150deg, rgba(255, 255, 255, 0.36), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.42);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(46, 16, 101, 0.3);
}
.spb-hero-copy {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.spb-hero-title {
  font-size: 16px;
  font-weight: 800;
  line-height: 1.3;
  letter-spacing: 0.03em;
}
.spb-hero-desc {
  margin: 0;
  overflow: hidden;
  font-size: 11px;
  white-space: nowrap;
  text-overflow: ellipsis;
  color: rgba(255, 255, 255, 0.88);
}
.detail-table {
  margin-top: 10px;
  border-radius: 10px;
  overflow: hidden;
}

/* ---------- 注文書印刷確認ダイアログ（violet） ---------- */
:global(.el-dialog.spb-print-dialog) {
  padding: 0;
  border-radius: 14px;
  overflow: hidden;
  box-shadow:
    0 24px 48px -16px rgba(46, 16, 101, 0.42),
    0 0 0 1px rgba(124, 58, 237, 0.12);
}
:global(.el-dialog.spb-print-dialog .el-dialog__header) {
  padding: 0;
  margin: 0;
}
:global(.el-dialog.spb-print-dialog .el-dialog__body) {
  padding: 0;
  background: linear-gradient(180deg, #faf5ff 0%, #f8fafc 100%);
}
.pcd-hero {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 14px 18px;
  background: linear-gradient(125deg, #4c1d95 0%, #6d28d9 38%, #8b5cf6 72%, #a78bfa 100%);
}
.pcd-hero-icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: #fff;
  background: linear-gradient(150deg, rgba(255, 255, 255, 0.36), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.42);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(46, 16, 101, 0.3);
}
.pcd-hero-copy {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.pcd-hero .dialog-title {
  font-size: 16px;
  font-weight: 800;
  line-height: 1.3;
  letter-spacing: 0.03em;
  color: #fff;
  white-space: nowrap;
}
.pcd-hero-desc {
  margin: 0;
  overflow: hidden;
  font-size: 11px;
  white-space: nowrap;
  text-overflow: ellipsis;
  color: rgba(255, 255, 255, 0.88);
}

/* 印刷実行：ヒーロー上の白ピル */
.pcd-hero .confirm-btn-header {
  --k-rgb: 124 58 237;
  flex-shrink: 0;
  height: 30px;
  padding: 0 14px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  color: #6d28d9;
  border: 1px solid rgba(255, 255, 255, 0.9);
  background: linear-gradient(180deg, #ffffff 0%, #f5f3ff 100%);
}
.pcd-hero .confirm-btn-header:hover,
.pcd-hero .confirm-btn-header:focus-visible {
  color: #5b21b6;
  border-color: #fff;
  background: #fff;
}
.pcd-hero .confirm-btn-header .el-icon {
  margin-right: 4px;
}

.print-confirm-content-compact {
  padding: 12px 14px 14px;
}
.form-sections-compact {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* セクション色分け（受注先＝sky / 承認・発行＝violet / 備考＝amber） */
.pcd-sec--to {
  --sc: #0ea5e9;
  --sc-rgb: 14, 165, 233;
}
.pcd-sec--approve {
  --sc: #8b5cf6;
  --sc-rgb: 139, 92, 246;
}
.pcd-sec--note {
  --sc: #f59e0b;
  --sc-rgb: 245, 158, 11;
}
.pcd-sec {
  position: relative;
  overflow: hidden;
  border-radius: 10px;
  background: #fff;
  border: 1px solid rgba(var(--sc-rgb), 0.22);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}
.pcd-sec::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  z-index: 1;
  background: linear-gradient(90deg, var(--sc) 0%, rgba(var(--sc-rgb), 0.25) 100%);
}
.pcd-sec:focus-within {
  border-color: rgba(var(--sc-rgb), 0.5);
  box-shadow: 0 0 0 3px rgba(var(--sc-rgb), 0.1);
}
.section-header-compact {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 12px 7px;
  font-size: 12px;
  font-weight: 700;
  color: #1e293b;
  background: linear-gradient(90deg, rgba(var(--sc-rgb), 0.1) 0%, rgba(var(--sc-rgb), 0.02) 100%);
  border-bottom: 1px solid rgba(var(--sc-rgb), 0.16);
}
.section-icon {
  width: 22px;
  height: 22px;
  padding: 4px;
  box-sizing: border-box;
  border-radius: 6px;
  font-size: 13px;
  color: #fff;
  background: linear-gradient(135deg, rgba(var(--sc-rgb), 0.7) 0%, var(--sc) 100%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(15, 23, 42, 0.16);
}
.section-title {
  letter-spacing: 0.03em;
}
.form-fields-compact {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 12px;
}
.form-field-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.form-field-row .field-label {
  flex-shrink: 0;
  min-width: 95px;
  font-size: 11px;
  font-weight: 700;
  color: #475569;
}
.form-input-compact,
.form-textarea-compact {
  flex: 1;
}
.pcd-sec :deep(.el-input__wrapper),
.pcd-sec :deep(.el-select__wrapper),
.pcd-sec :deep(.el-textarea__inner) {
  border-radius: 8px;
  background-color: #fff;
  box-shadow: 0 0 0 1px #dfe3f0 inset;
}
.pcd-sec :deep(.el-textarea__inner) {
  font-size: 11px;
}
.pcd-sec :deep(.el-input__wrapper:hover),
.pcd-sec :deep(.el-select__wrapper:hover),
.pcd-sec :deep(.el-textarea__inner:hover) {
  box-shadow: 0 0 0 1px rgba(var(--sc-rgb), 0.55) inset;
}
.pcd-sec :deep(.el-input__wrapper.is-focus),
.pcd-sec :deep(.el-select__wrapper.is-focused),
.pcd-sec :deep(.el-textarea__inner:focus) {
  box-shadow:
    0 0 0 1px var(--sc) inset,
    0 0 0 3px rgba(var(--sc-rgb), 0.15);
}
</style>
