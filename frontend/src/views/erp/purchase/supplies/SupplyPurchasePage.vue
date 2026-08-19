<template>
  <div class="supply-purchase-page">
    <div class="page-header">
      <div class="header-lead">
        <div class="title-icon"><el-icon><Box /></el-icon></div>
        <div>
          <h1>備品購入</h1>
          <p>仕入先を選び、カタログから備品を複数選択して発注します</p>
        </div>
      </div>
      <div class="header-stats">
        <div class="stat-card stat-card--blue">
          <span class="stat-number">{{ items.length }}</span>
          <span class="stat-label">カタログ</span>
        </div>
        <div class="stat-card stat-card--amber">
          <span class="stat-number">{{ cart.length }}</span>
          <span class="stat-label">発注明細</span>
        </div>
        <div class="stat-card stat-card--violet">
          <span class="stat-number">{{ orders.length }}</span>
          <span class="stat-label">履歴</span>
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
          :class="{ 'is-ready': cart.length > 0 }"
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
      class="item-form-dialog"
      align-center
      destroy-on-close
      :close-on-click-modal="false"
    >
      <template #header>
        <div class="item-dialog-header">
          <div class="item-dialog-icon">
            <el-icon><Box /></el-icon>
          </div>
          <div>
            <h3>{{ itemForm.id ? '備品を編集' : '備品を登録' }}</h3>
            <p>{{ itemForm.id ? 'カタログ情報を更新します' : '自動採番のCDで新しい備品を登録します' }}</p>
          </div>
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

    <el-drawer v-model="detailVisible" title="発注明細" size="480px">
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
      class="print-confirm-dialog"
    >
      <template #header>
        <div class="dialog-header-with-button">
          <span class="dialog-title">注文書印刷確認</span>
          <el-button type="primary" size="small" class="confirm-btn-header" :loading="printLoading" @click="confirmPrint">
            <el-icon><Printer /></el-icon>
            印刷実行
          </el-button>
        </div>
      </template>
      <div class="print-confirm-content-compact">
        <div class="form-sections-compact">
          <div class="form-section-compact">
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
          <div class="form-section-compact">
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
          <div class="form-section-compact">
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
import { Box, Check, EditPen, OfficeBuilding, Plus, Printer, Refresh, Search, ShoppingCart, User } from '@element-plus/icons-vue'
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
    radial-gradient(1200px 280px at 8% -10%, rgba(59, 130, 246, 0.16), transparent 55%),
    radial-gradient(900px 240px at 92% 0%, rgba(245, 158, 11, 0.14), transparent 50%),
    linear-gradient(180deg, #eef4ff 0%, #f8fafc 42%, #f1f5f9 100%);
  animation: page-in 0.45s ease;
}
@keyframes page-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 16px;
  background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 42%, #0ea5e9 100%);
  box-shadow:
    0 14px 32px rgba(37, 99, 235, 0.28),
    inset 0 1px 0 rgba(255, 255, 255, 0.28);
  color: #fff;
}
.header-lead {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}
.title-icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.32), rgba(255, 255, 255, 0.08));
  box-shadow:
    0 8px 16px rgba(15, 23, 42, 0.18),
    inset 0 1px 0 rgba(255, 255, 255, 0.45);
  font-size: 20px;
}
.page-header h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
  letter-spacing: 0.02em;
  color: #fff;
}
.page-header p {
  margin: 3px 0 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.82);
}
.header-stats {
  display: flex;
  gap: 8px;
  margin-left: auto;
}
.stat-card {
  min-width: 78px;
  padding: 7px 12px;
  border-radius: 12px;
  text-align: center;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.22);
  backdrop-filter: blur(8px);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.25);
  transition: transform 0.2s ease, background 0.2s ease;
}
.stat-card:hover {
  transform: translateY(-2px);
  background: rgba(255, 255, 255, 0.24);
}
.stat-number {
  display: block;
  font-size: 18px;
  font-weight: 800;
  line-height: 1.1;
}
.stat-label {
  font-size: 11px;
  opacity: 0.88;
}
.stat-card--blue {
  box-shadow: 0 6px 14px rgba(37, 99, 235, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.25);
}
.stat-card--amber {
  background: rgba(251, 191, 36, 0.22);
}
.stat-card--violet {
  background: rgba(167, 139, 250, 0.22);
}
.header-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}
.ghost-btn {
  background: rgba(255, 255, 255, 0.16) !important;
  border: 1px solid rgba(255, 255, 255, 0.35) !important;
  color: #fff !important;
}
.ghost-btn:hover {
  background: rgba(255, 255, 255, 0.28) !important;
}
.order-btn {
  border: none !important;
  background: linear-gradient(135deg, #f59e0b, #ea580c) !important;
  box-shadow: 0 8px 16px rgba(234, 88, 12, 0.32);
}
.order-btn.is-ready {
  animation: cta-pulse 1.8s ease-in-out infinite;
}
@keyframes cta-pulse {
  0%,
  100% {
    box-shadow: 0 8px 16px rgba(234, 88, 12, 0.32);
  }
  50% {
    box-shadow: 0 10px 22px rgba(234, 88, 12, 0.5);
  }
}
.filter-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(191, 219, 254, 0.9);
  border-radius: 14px;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.06);
  backdrop-filter: blur(10px);
}
.filter-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 999px;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 700;
}
.filter-supplier {
  width: 280px;
}
.filter-keyword {
  width: 220px;
}
.search-btn {
  background: linear-gradient(135deg, #2563eb, #0284c7) !important;
  border: none !important;
  color: #fff !important;
  box-shadow: 0 6px 14px rgba(37, 99, 235, 0.25);
}
.work-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.7fr) minmax(280px, 0.9fr);
  gap: 10px;
}
.panel-card {
  border: 0 !important;
  border-radius: 16px !important;
  overflow: hidden;
  background: #fff;
  box-shadow:
    0 12px 28px rgba(15, 23, 42, 0.08),
    0 1px 0 rgba(255, 255, 255, 0.8) inset;
  transition: transform 0.22s ease, box-shadow 0.22s ease;
}
.panel-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 18px 36px rgba(15, 23, 42, 0.12);
}
.catalog-card {
  border-top: 4px solid #3b82f6 !important;
}
.cart-card {
  border-top: 4px solid #f59e0b !important;
}
.history-card {
  border-top: 4px solid #8b5cf6 !important;
}
.catalog-card :deep(.el-card__header),
.cart-card :deep(.el-card__header),
.history-card :deep(.el-card__header) {
  padding: 10px 12px;
  background: linear-gradient(180deg, #ffffff, #f8fafc);
  border-bottom: 1px solid #e2e8f0;
}
.catalog-card :deep(.el-card__body),
.cart-card :deep(.el-card__body),
.history-card :deep(.el-card__body) {
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
.tone-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.16);
}
.tone-dot--blue {
  background: #3b82f6;
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
.add-cart-btn {
  background: linear-gradient(135deg, #2563eb, #0ea5e9) !important;
  border: none !important;
  box-shadow: 0 6px 12px rgba(37, 99, 235, 0.22);
}
.cart-meta {
  margin-bottom: 6px;
  padding: 8px;
  border-radius: 12px;
  background: linear-gradient(180deg, #fffbeb, #fff);
  border: 1px solid #fde68a;
}
.cart-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 260px;
  overflow: auto;
}
.card-head__actions {
  display: flex;
  align-items: center;
  gap: 6px;
}
.cart-row {
  display: grid;
  grid-template-columns: 1fr 110px 72px auto;
  gap: 6px;
  align-items: center;
  padding: 8px;
  background: linear-gradient(180deg, #fff, #fff7ed);
  border: 1px solid #fed7aa;
  border-radius: 10px;
  box-shadow: 0 4px 10px rgba(245, 158, 11, 0.08);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}
.cart-row:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 16px rgba(245, 158, 11, 0.16);
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
  justify-content: space-between;
  margin-top: 10px;
  padding: 10px 12px;
  border-radius: 12px;
  font-size: 13px;
  color: #fff;
  background: linear-gradient(135deg, #ea580c, #f59e0b);
  box-shadow: 0 8px 16px rgba(234, 88, 12, 0.22);
}
.cart-total strong {
  font-size: 16px;
}
.refresh-btn {
  color: #6d28d9 !important;
}
.modern-table :deep(.el-table__row:hover > td) {
  background: rgba(59, 130, 246, 0.06) !important;
}
.detail-table {
  margin-top: 10px;
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

.print-confirm-dialog :deep(.el-dialog__header) {
  padding: 10px 14px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.dialog-header-with-button {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}
.dialog-title {
  font-size: 14px;
  font-weight: 600;
  color: rgb(10, 10, 10);
}
.confirm-btn-header {
  border-radius: 5px;
  padding: 5px 12px;
  font-weight: 600;
  font-size: 11px;
  background: rgba(23, 241, 158, 0.589);
  border: 1px solid rgba(8, 7, 7, 0.774);
  color: rgb(7, 7, 7);
  margin-left: 200px;
}
.print-confirm-dialog :deep(.el-dialog__body) {
  padding: 0;
}
.print-confirm-content-compact {
  padding: 10px 14px;
}
.form-sections-compact {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.form-section-compact {
  background: white;
  border-radius: 5px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
}
.section-header-compact {
  display: flex;
  align-items: center;
  padding: 6px 10px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 1px solid #e5e7eb;
  font-weight: 600;
  color: #334155;
  font-size: 11px;
  gap: 5px;
}
.section-icon {
  color: #667eea;
  font-size: 13px;
}
.form-fields-compact {
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.form-field-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.form-field-row .field-label {
  min-width: 95px;
  font-size: 11px;
  font-weight: 500;
  color: #475569;
  flex-shrink: 0;
}
.form-input-compact,
.form-textarea-compact {
  flex: 1;
}

.item-form-dialog :deep(.el-dialog) {
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 32px 80px rgba(15, 23, 42, 0.28);
}
.item-form-dialog :deep(.el-dialog__header) {
  padding: 18px 20px 16px;
  margin: 0;
  background:
    radial-gradient(circle at 88% -20%, rgba(255, 255, 255, 0.28), transparent 42%),
    linear-gradient(135deg, #1d4ed8 0%, #2563eb 48%, #0ea5e9 100%);
}
.item-form-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: #fff;
  font-size: 18px;
}
.item-form-dialog :deep(.el-dialog__body) {
  padding: 0;
  background: linear-gradient(180deg, #f8fbff, #f1f5f9);
}
.item-form-dialog :deep(.el-dialog__footer) {
  padding: 12px 18px 16px;
  background: #fff;
  border-top: 1px solid #e2e8f0;
}
.item-dialog-header {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #fff;
  padding-right: 24px;
}
.item-dialog-icon {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  background: rgba(255, 255, 255, 0.18);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.4), 0 8px 16px rgba(15, 23, 42, 0.16);
}
.item-dialog-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 800;
  letter-spacing: 0.02em;
}
.item-dialog-header p {
  margin: 4px 0 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.84);
}
.item-dialog-body {
  padding: 16px 16px 10px;
}
.item-cd-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding: 12px 14px;
  border-radius: 16px;
  background: linear-gradient(135deg, #eff6ff 0%, #fff 70%);
  border: 1px solid #bfdbfe;
  box-shadow: 0 10px 22px rgba(37, 99, 235, 0.1);
}
.item-cd-banner__mark {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.06em;
  color: #fff;
  background: linear-gradient(135deg, #2563eb, #0ea5e9);
  box-shadow: 0 8px 16px rgba(37, 99, 235, 0.28);
  flex-shrink: 0;
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
  font-size: 22px;
  letter-spacing: 0.08em;
  color: #1d4ed8;
  font-family: Consolas, Monaco, monospace;
  line-height: 1.1;
}
.form-section {
  margin-bottom: 10px;
  padding: 12px 14px 6px;
  border-radius: 16px;
  background: #fff;
  border: 1px solid #e2e8f0;
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.04);
}
.form-section--amber {
  background: linear-gradient(180deg, #fffbeb, #fff);
  border-color: #fde68a;
}
.form-section--slate {
  background: linear-gradient(180deg, #f8fafc, #fff);
}
.form-section__title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 800;
  color: #334155;
  margin-bottom: 10px;
  letter-spacing: 0.06em;
}
.form-section__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #2563eb;
  box-shadow: 0 0 0 4px #dbeafe;
}
.form-section--amber .form-section__dot {
  background: #f59e0b;
  box-shadow: 0 0 0 4px #fef3c7;
}
.form-section--slate .form-section__dot {
  background: #64748b;
  box-shadow: 0 0 0 4px #e2e8f0;
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
.item-form :deep(.el-input__wrapper),
.item-form :deep(.el-select__wrapper) {
  border-radius: 10px;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
}
.item-form :deep(.el-textarea__inner) {
  border-radius: 10px;
}
.item-form :deep(.el-input-number) {
  width: 100%;
}
.item-form :deep(.el-input-number .el-input__wrapper) {
  border-radius: 10px;
}
.status-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  margin-bottom: 10px;
  border-radius: 12px;
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
.dialog-save {
  min-width: 118px;
  height: 36px;
  border-radius: 10px !important;
  font-weight: 700;
  background: linear-gradient(135deg, #2563eb, #0ea5e9) !important;
  border: none !important;
  box-shadow: 0 8px 16px rgba(37, 99, 235, 0.28);
}
.dialog-cancel {
  height: 36px;
  border-radius: 10px;
}
</style>
