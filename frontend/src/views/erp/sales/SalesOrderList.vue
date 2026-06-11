<template>
  <div class="page-root">
    <div class="dynamic-background">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
      <div class="noise-overlay"></div>
    </div>

    <!-- Header -->
    <div class="glass-header animate-in">
      <div class="header-content">
        <div class="header-left">
          <div class="header-icon">
            <el-icon size="26"><List /></el-icon>
          </div>
          <div class="header-text">
            <h1 class="header-title">受注一覧</h1>
            <span class="header-subtitle">Sales Order List</span>
          </div>
        </div>
        <div class="header-badges">
          <span class="badge badge-total">合計 <b>{{ pagination.total }}</b></span>
          <span class="badge badge-pending">承認待ち <b>{{ pendingCount }}</b></span>
        </div>
      </div>
    </div>

    <!-- Filter -->
    <div class="glass-card filter-bar animate-in" style="animation-delay:.08s">
      <el-select
        v-model="query.destination_cd"
        placeholder="納入先"
        clearable
        filterable
        class="dark-input filter-select-dest"
        popper-class="destination-select-popper"
        @change="fetchData"
      >
        <el-option
          v-for="d in destinationOptions"
          :key="d.cd"
          :label="`${d.cd} | ${d.name}`"
          :value="d.cd"
        />
      </el-select>
      <el-select
        v-model="query.status"
        placeholder="ステータス"
        clearable
        class="dark-input filter-select"
        @change="fetchData"
      >
        <el-option label="下書き" value="draft" />
        <el-option label="承認待ち" value="pending" />
        <el-option label="承認済" value="approved" />
        <el-option label="一部納品" value="partial_delivered" />
        <el-option label="完了" value="completed" />
        <el-option label="キャンセル" value="cancelled" />
      </el-select>
      <el-date-picker
        v-model="query.dateRange"
        type="daterange"
        range-separator="〜"
        start-placeholder="開始日"
        end-placeholder="終了日"
        value-format="YYYY-MM-DD"
        class="dark-input filter-date"
        @change="fetchData"
      />
      <el-button class="gradient-btn" :icon="Search" @click="fetchData">検索</el-button>
      <el-button class="gradient-btn sync-btn" :icon="Upload" :loading="syncing" @click="handleSyncFromOrderDaily">
        日別受注取込
      </el-button>
      <el-button class="gradient-btn create-btn" :icon="Plus" @click="openDialog()">新規作成</el-button>
    </div>

    <!-- Table -->
    <div class="glass-card table-card animate-in" style="animation-delay:.14s">
      <el-table
        v-loading="loading"
        :data="tableData"
        stripe
        class="dark-table"
        :header-cell-style="headerStyle"
        :row-style="rowStyle"
        empty-text="データがありません"
      >
        <el-table-column prop="order_no" label="受注番号" min-width="140" />
        <el-table-column label="納入先名" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">{{ displayDestinationName(row) }}</template>
        </el-table-column>
        <el-table-column prop="order_date" label="受注日" width="115" />
        <el-table-column prop="expected_delivery_date" label="納期" width="115" />
        <el-table-column label="合計金額" width="140" align="right">
          <template #default="{ row }">{{ formatYen(row.total_amount) }}</template>
        </el-table-column>
        <el-table-column label="入金状況" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="paymentType(row.payment_status)" size="small" effect="dark" round>
              {{ paymentLabel(row.payment_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="ステータス" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small" effect="dark" round>
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="アクション" width="200" align="center" fixed="right">
          <template #default="{ row }">
            <el-button link size="small" class="action-link" @click="openDialog(row)">詳細</el-button>
            <el-button link size="small" class="action-link" @click="goToOrderDaily(row)">日別受注</el-button>
            <el-button
              v-if="row.status === 'pending'"
              link size="small" class="action-link approve"
              @click="handleApprove(row)"
            >承認</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          background
          @size-change="fetchData"
          @current-change="fetchData"
        />
      </div>
    </div>

    <!-- Create / Detail Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :width="isViewMode ? '860px' : '780px'"
      destroy-on-close
      class="sales-order-dialog"
      :class="{ 'sales-order-dialog--view': isViewMode }"
      :show-close="false"
      :close-on-click-modal="false"
      align-center
    >
      <template #header>
        <div class="so-dialog-header">
          <div class="so-dialog-header__left">
            <span class="so-dialog-header__icon" :class="{ 'so-dialog-header__icon--create': !isViewMode }">
              <el-icon :size="20"><Document v-if="isViewMode" /><Plus v-else /></el-icon>
            </span>
            <div class="so-dialog-header__text">
              <h2 class="so-dialog-header__title">{{ isViewMode ? '受注詳細' : '新規受注作成' }}</h2>
              <p v-if="isViewMode && detailMeta" class="so-dialog-header__sub">
                <span class="mono">{{ detailMeta.orderNo }}</span>
              </p>
              <p v-else class="so-dialog-header__sub">販売受注の新規登録</p>
            </div>
          </div>
          <div v-if="isViewMode && detailMeta" class="so-dialog-header__tags">
            <el-tag :type="statusType(detailMeta.status)" size="small" effect="dark" round>
              {{ statusLabel(detailMeta.status) }}
            </el-tag>
            <el-tag :type="paymentType(detailMeta.paymentStatus)" size="small" effect="plain" round class="so-tag-payment">
              {{ paymentLabel(detailMeta.paymentStatus) }}
            </el-tag>
          </div>
          <el-icon class="so-dialog-header__close" @click="dialogVisible = false"><Close /></el-icon>
        </div>
      </template>

      <div v-loading="detailLoading" class="so-dialog-body">
        <!-- 詳細: サマリー KPI -->
        <div v-if="isViewMode && detailMeta" class="so-kpi-strip">
          <div class="so-kpi so-kpi--amount">
            <span class="so-kpi__label">合計金額</span>
            <span class="so-kpi__value">{{ formatYen(detailMeta.totalAmount) }}</span>
          </div>
          <div class="so-kpi so-kpi--date">
            <span class="so-kpi__label">受注日</span>
            <span class="so-kpi__value">{{ form.order_date || '—' }}</span>
          </div>
          <div class="so-kpi so-kpi--delivery">
            <span class="so-kpi__label">希望納期</span>
            <span class="so-kpi__value">{{ form.expected_delivery_date || '—' }}</span>
          </div>
          <div class="so-kpi so-kpi--lines">
            <span class="so-kpi__label">明細行</span>
            <span class="so-kpi__value">{{ form.items.length }}</span>
          </div>
        </div>

        <el-form
          ref="formRef"
          :model="form"
          :rules="formRules"
          :label-width="isViewMode ? '0' : '100px'"
          class="so-form"
          :class="{ 'so-form--view': isViewMode }"
        >
          <!-- 基本情報 -->
          <section class="so-section so-section--compact">
            <div class="so-section__head so-section__head--compact">
              <el-icon class="so-section__icon"><User /></el-icon>
              <span class="so-section__title">基本情報</span>
            </div>
            <div class="so-section__body so-section__body--compact">
              <template v-if="isViewMode">
                <div class="so-basic-bar">
                  <div class="so-basic-dest">
                    <span class="so-basic-dest-cd">{{ form.destination_cd || form.customer_code || '—' }}</span>
                    <span class="so-basic-dest-name">{{ displayDestinationName(form) }}</span>
                  </div>
                  <span class="so-basic-sep" aria-hidden="true"></span>
                  <div class="so-basic-field">
                    <span class="so-basic-field-label">営業担当</span>
                    <span class="so-basic-field-value">{{ form.sales_person || '—' }}</span>
                  </div>
                  <template v-if="form.remarks">
                    <span class="so-basic-sep" aria-hidden="true"></span>
                    <div class="so-basic-field so-basic-field--remarks">
                      <span class="so-basic-field-label">備考</span>
                      <span class="so-basic-field-value" :title="form.remarks">{{ form.remarks }}</span>
                    </div>
                  </template>
                </div>
              </template>
              <div v-else class="so-edit-grid so-edit-grid--compact">
                <el-form-item label="納入先CD" prop="destination_cd">
                  <el-input v-model="form.destination_cd" placeholder="納入先CD" />
                </el-form-item>
                <el-form-item label="納入先名" prop="destination_name">
                  <el-input v-model="form.destination_name" placeholder="納入先名" />
                </el-form-item>
                <el-form-item label="受注日" prop="order_date">
                  <el-date-picker v-model="form.order_date" type="date" value-format="YYYY-MM-DD" placeholder="受注日" style="width:100%" />
                </el-form-item>
                <el-form-item label="希望納期" prop="expected_delivery_date">
                  <el-date-picker v-model="form.expected_delivery_date" type="date" value-format="YYYY-MM-DD" placeholder="希望納期" style="width:100%" />
                </el-form-item>
                <el-form-item label="営業担当">
                  <el-input v-model="form.sales_person" placeholder="営業担当" />
                </el-form-item>
                <el-form-item label="備考" class="so-edit-remarks">
                  <el-input v-model="form.remarks" type="textarea" :rows="2" placeholder="備考" />
                </el-form-item>
              </div>
            </div>
          </section>

          <!-- 明細 -->
          <section class="so-section">
            <div class="so-section__head">
              <el-icon class="so-section__icon so-section__icon--goods"><Goods /></el-icon>
              <span class="so-section__title">受注明細</span>
              <span v-if="isViewMode" class="so-section__badge">{{ form.items.length }} 行</span>
              <el-button
                v-if="isViewMode"
                size="small"
                class="so-section__action so-print-btn"
                :icon="Printer"
                @click="printOrderItems"
              >
                印刷
              </el-button>
              <el-button v-if="!isViewMode" size="small" class="gradient-btn so-section__action" :icon="Plus" @click="addItem">
                行追加
              </el-button>
            </div>
            <div class="so-section__body so-section__body--flush">
              <el-table
                v-if="isViewMode"
                :data="form.items"
                size="small"
                stripe
                class="so-detail-table"
                empty-text="明細がありません"
              >
                <el-table-column type="index" label="#" width="56" align="center" />
                <el-table-column prop="product_name" label="品名" min-width="160" show-overflow-tooltip />
                <el-table-column prop="quantity" label="数量(本)" width="88" align="right">
                  <template #default="{ row }">
                    <span class="num">{{ row.quantity?.toLocaleString('ja-JP') }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="confirmed_boxes" label="確定箱数" width="88" align="right">
                  <template #default="{ row }">
                    <span class="num">{{ (row.confirmed_boxes ?? 0).toLocaleString('ja-JP') }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="単価" width="110" align="right">
                  <template #default="{ row }">{{ formatYen(row.unit_price) }}</template>
                </el-table-column>
                <el-table-column label="金額" width="120" align="right">
                  <template #default="{ row }">
                    <span class="so-amount-cell">{{ formatYen(row.amount) }}</span>
                  </template>
                </el-table-column>
              </el-table>
              <el-table v-else :data="form.items" border size="small" class="so-edit-table dark-table" :header-cell-style="headerStyle">
                <el-table-column type="index" label="#" width="56" align="center" />
                <el-table-column label="品番" min-width="120">
                  <template #default="{ row }">
                    <el-input v-model="row.product_code" size="small" placeholder="品番" />
                  </template>
                </el-table-column>
                <el-table-column label="品名" min-width="130">
                  <template #default="{ row }">
                    <el-input v-model="row.product_name" size="small" placeholder="品名" />
                  </template>
                </el-table-column>
                <el-table-column label="数量" width="100">
                  <template #default="{ row }">
                    <el-input-number v-model="row.quantity" size="small" :min="0" controls-position="right" style="width:100%" @change="calcAmount(row)" />
                  </template>
                </el-table-column>
                <el-table-column label="単価" width="115">
                  <template #default="{ row }">
                    <el-input-number v-model="row.unit_price" size="small" :min="0" :precision="2" controls-position="right" style="width:100%" @change="calcAmount(row)" />
                  </template>
                </el-table-column>
                <el-table-column label="金額" width="110" align="right">
                  <template #default="{ row }">{{ formatYen(row.amount) }}</template>
                </el-table-column>
                <el-table-column label="" width="48" align="center">
                  <template #default="{ $index }">
                    <el-button link size="small" class="action-link danger" @click="removeItem($index)">
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
              <div class="so-total-bar">
                <span v-if="isViewMode && detailMeta" class="so-total-bar__tax">
                  税額 {{ formatYen(detailMeta.taxAmount) }}
                </span>
                <span class="so-total-bar__main">
                  合計 <strong>{{ formatYen(isViewMode && detailMeta ? detailMeta.totalAmount : itemsTotal) }}</strong>
                </span>
              </div>
            </div>
          </section>

          <!-- 関連日別受注 -->
          <section v-if="isViewMode" class="so-section">
            <div class="so-section__head">
              <el-icon class="so-section__icon so-section__icon--daily"><Calendar /></el-icon>
              <span class="so-section__title">関連日別受注</span>
              <span class="so-section__badge so-section__badge--cyan">{{ relatedDailyList.length }} 件</span>
              <el-button size="small" class="gradient-btn so-section__action" @click="goToOrderDaily()">
                <el-icon><Right /></el-icon>
                日受注管理
              </el-button>
            </div>
            <div class="so-section__body so-section__body--flush">
              <el-table
                v-loading="relatedDailyLoading"
                :data="relatedDailyList"
                size="small"
                stripe
                class="so-detail-table so-detail-table--daily"
                :max-height="220"
                empty-text="該当期間・品番に一致する日別受注がありません"
              >
                <el-table-column prop="date" label="出荷日" width="108" />
                <el-table-column prop="product_cd" label="製品CD" width="96">
                  <template #default="{ row }">
                    <span class="mono">{{ row.product_cd }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="product_name" label="製品名" min-width="120" show-overflow-tooltip />
                <el-table-column prop="confirmed_units" label="確定本数" width="88" align="right">
                  <template #default="{ row }">
                    <span class="num">{{ row.confirmed_units?.toLocaleString('ja-JP') }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="confirmed_boxes" label="確定箱数" width="88" align="right">
                  <template #default="{ row }">
                    <span class="num">{{ row.confirmed_boxes?.toLocaleString('ja-JP') }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="status" label="状態" width="96" align="center">
                  <template #default="{ row }">
                    <el-tag size="small" effect="plain" round class="so-status-tag">{{ row.status || '—' }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="delivery_date" label="納入日" width="108" />
              </el-table>
            </div>
          </section>
        </el-form>
      </div>

      <template #footer>
        <div class="so-dialog-footer">
          <el-button class="so-btn so-btn--ghost" @click="dialogVisible = false">
            <el-icon><Close /></el-icon>
            <span>閉じる</span>
          </el-button>
          <el-button v-if="!isViewMode" type="primary" class="so-btn so-btn--save gradient-btn" :loading="saving" @click="handleSave">
            <el-icon><Check /></el-icon>
            <span>保存</span>
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import {
  List,
  Search,
  Plus,
  Delete,
  Upload,
  Document,
  User,
  Calendar,
  Goods,
  Close,
  Check,
  Right,
  Printer,
} from '@element-plus/icons-vue'
import {
  getSalesOrders,
  getSalesOrderById,
  createSalesOrder,
  approveSalesOrder,
  syncSalesOrdersFromOrderDaily,
  type SyncFromOrderDailyResult,
} from '@/api/erp/sales'
import { fetchOrderDailyList, type OrderDailyItem } from '@/api/erp/orderDaily'
import { getDestinationOptions } from '@/api/master/destinationMaster'
import { useSalesOperationPermission } from '@/composables/useSalesOperationPermission'
import { guardSalesOperation } from '@/utils/salesOperationGuard'

const { canCreate, canEdit, canDelete, canExport, canApprove } = useSalesOperationPermission()


interface OrderItem {
  product_code: string
  product_name: string
  quantity: number
  confirmed_boxes?: number
  item_order_no?: string
  unit_price: number
  amount: number
}

const router = useRouter()
const loading = ref(false)
const saving = ref(false)
const syncing = ref(false)
const detailLoading = ref(false)
const relatedDailyLoading = ref(false)
const dialogVisible = ref(false)
const isViewMode = ref(false)
const currentOrder = ref<Record<string, unknown> | null>(null)
const relatedDailyList = ref<OrderDailyItem[]>([])
const formRef = ref<FormInstance>()

const tableData = ref<any[]>([])
const destinationOptions = ref<{ cd: string; name: string }[]>([])
const pendingCount = computed(() => tableData.value.filter(r => r.status === 'pending').length)

const query = reactive({
  destination_cd: '',
  status: '',
  dateRange: null as [string, string] | null,
})

const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const emptyItem = (): OrderItem => ({ product_code: '', product_name: '', quantity: 0, unit_price: 0, amount: 0 })

const form = reactive({
  customer_code: '',
  customer_name: '',
  destination_cd: '',
  destination_name: '',
  order_date: '',
  expected_delivery_date: '',
  sales_person: '',
  remarks: '',
  items: [emptyItem()] as OrderItem[],
})

const formRules: FormRules = {
  destination_cd: [{ required: true, message: '納入先CDは必須です', trigger: 'blur' }],
  destination_name: [{ required: true, message: '納入先名は必須です', trigger: 'blur' }],
  order_date: [{ required: true, message: '受注日は必須です', trigger: 'change' }],
  expected_delivery_date: [{ required: true, message: '希望納期は必須です', trigger: 'change' }],
}

function displayDestinationName(row: Record<string, unknown>): string {
  const name = row.destination_name ?? row.customer_name
  return name ? String(name) : '—'
}

const itemsTotal = computed(() => form.items.reduce((s, i) => s + (i.amount || 0), 0))

const itemsSubtotal = computed(() =>
  form.items.reduce((s, i) => s + (Number(i.amount) || 0), 0)
)

const detailMeta = computed(() => {
  const o = currentOrder.value
  if (!o) return null
  const headerTotal = Number(o.total_amount ?? 0)
  const lineSub = itemsSubtotal.value
  const taxRate = Number(o.tax_rate ?? 10)
  const useLines = headerTotal <= 0 && lineSub > 0
  const subtotal = useLines ? lineSub : Number(o.subtotal ?? lineSub)
  const taxAmount = useLines ? lineSub * taxRate / 100 : Number(o.tax_amount ?? 0)
  const totalAmount = useLines ? subtotal + taxAmount : (headerTotal > 0 ? headerTotal : subtotal + taxAmount)
  return {
    orderNo: String(o.order_no ?? '—'),
    status: String(o.status ?? ''),
    paymentStatus: String(o.payment_status ?? ''),
    totalAmount,
    subtotal,
    taxAmount,
  }
})

const headerStyle = () => ({
  background: 'linear-gradient(135deg, rgba(139,92,246,.25), rgba(59,130,246,.18))',
  color: '#e2e8f0',
  borderBottom: '1px solid rgba(255,255,255,.08)',
  fontSize: '12px',
  padding: '8px 0',
})

const rowStyle = () => ({
  background: 'transparent',
  color: '#cbd5e1',
  fontSize: '13px',
})

function formatYen(n: number | undefined): string {
  if (n == null) return '¥0'
  return `¥${Number(n).toLocaleString('ja-JP')}`
}

function escapePrintHtml(raw: string): string {
  return raw
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function printOrderItems() {
  if (!guardSalesOperation(canExport)) return

  if (!form.items.length) {
    ElMessage.warning('印刷する明細がありません')
    return
  }

  const printWindow = window.open('', '_blank')
  if (!printWindow) {
    ElMessage.error('ポップアップがブロックされています。ブラウザの設定を確認してください。')
    return
  }

  const meta = detailMeta.value
  const destCd = form.destination_cd || form.customer_code || '—'
  const destName = displayDestinationName(form as unknown as Record<string, unknown>)
  const orderNo = meta?.orderNo ?? '—'
  const taxAmount = meta?.taxAmount ?? 0
  const totalAmount = meta?.totalAmount ?? itemsSubtotal.value
  const printedAt = new Date().toLocaleString('ja-JP')

  const htmlParts: string[] = []
  htmlParts.push('<!DOCTYPE html>')
  htmlParts.push('<html><head><meta charset="UTF-8"><title>受注明細</title><style>')
  htmlParts.push('@page { size: A4 portrait; margin: 12mm; }')
  htmlParts.push('* { margin: 0; padding: 0; box-sizing: border-box; }')
  htmlParts.push(
    'body { font-family: "游ゴシック", "Yu Gothic", "YuGothic", "Meiryo", "メイリオ", sans-serif; padding: 12px; color: #1e293b; }',
  )
  htmlParts.push(
    '.print-header { margin-bottom: 14px; padding-bottom: 10px; border-bottom: 2px solid #4338ca; }',
  )
  htmlParts.push('.print-title { font-size: 20px; font-weight: 700; margin-bottom: 8px; }')
  htmlParts.push('.print-meta { font-size: 12px; color: #475569; line-height: 1.7; }')
  htmlParts.push('.print-meta strong { color: #1e293b; }')
  htmlParts.push(
    '.print-table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 11px; }',
  )
  htmlParts.push(
    '.print-table th { background: #f1f5f9; border: 1px solid #cbd5e1; padding: 7px 6px; text-align: center; font-weight: 600; }',
  )
  htmlParts.push('.print-table td { border: 1px solid #cbd5e1; padding: 6px 5px; color: #334155; }')
  htmlParts.push('.print-table tr:nth-child(even) td { background: #f8fafc; }')
  htmlParts.push('.print-table .col-no { width: 36px; text-align: center; }')
  htmlParts.push('.print-table .col-name { text-align: left; }')
  htmlParts.push('.print-table .col-num { text-align: right; white-space: nowrap; }')
  htmlParts.push(
    '.print-footer { margin-top: 12px; display: flex; justify-content: flex-end; gap: 24px; font-size: 13px; }',
  )
  htmlParts.push('.print-footer strong { font-size: 15px; color: #4338ca; }')
  htmlParts.push('.print-date { margin-top: 10px; font-size: 10px; color: #94a3b8; text-align: right; }')
  htmlParts.push(
    '@media print { body { padding: 0; } .print-table { font-size: 10px; } .print-table th, .print-table td { padding: 5px 4px; } }',
  )
  htmlParts.push('</style></head><body>')

  htmlParts.push('<div class="print-header">')
  htmlParts.push('<div class="print-title">受注明細</div>')
  htmlParts.push('<div class="print-meta">')
  htmlParts.push(`<div><strong>受注番号：</strong>${escapePrintHtml(orderNo)}</div>`)
  htmlParts.push(
    `<div><strong>納入先：</strong>${escapePrintHtml(destCd)}　${escapePrintHtml(destName)}</div>`,
  )
  htmlParts.push(
    `<div><strong>受注日：</strong>${escapePrintHtml(form.order_date || '—')}　<strong>希望納期：</strong>${escapePrintHtml(form.expected_delivery_date || '—')}</div>`,
  )
  if (form.sales_person) {
    htmlParts.push(`<div><strong>営業担当：</strong>${escapePrintHtml(form.sales_person)}</div>`)
  }
  if (form.remarks) {
    htmlParts.push(`<div><strong>備考：</strong>${escapePrintHtml(form.remarks)}</div>`)
  }
  htmlParts.push('</div></div>')

  htmlParts.push('<table class="print-table"><thead><tr>')
  htmlParts.push('<th class="col-no">#</th>')
  htmlParts.push('<th class="col-name">品名</th>')
  htmlParts.push('<th class="col-num">数量(本)</th>')
  htmlParts.push('<th class="col-num">確定箱数</th>')
  htmlParts.push('<th class="col-num">単価</th>')
  htmlParts.push('<th class="col-num">金額</th>')
  htmlParts.push('</tr></thead><tbody>')

  form.items.forEach((row, idx) => {
    htmlParts.push('<tr>')
    htmlParts.push(`<td class="col-no">${idx + 1}</td>`)
    htmlParts.push(`<td class="col-name">${escapePrintHtml(row.product_name || '—')}</td>`)
    htmlParts.push(`<td class="col-num">${Number(row.quantity ?? 0).toLocaleString('ja-JP')}</td>`)
    htmlParts.push(
      `<td class="col-num">${Number(row.confirmed_boxes ?? 0).toLocaleString('ja-JP')}</td>`,
    )
    htmlParts.push(`<td class="col-num">${escapePrintHtml(formatYen(row.unit_price))}</td>`)
    htmlParts.push(`<td class="col-num">${escapePrintHtml(formatYen(row.amount))}</td>`)
    htmlParts.push('</tr>')
  })

  htmlParts.push('</tbody></table>')
  htmlParts.push('<div class="print-footer">')
  if (meta) {
    htmlParts.push(`<span>税額 ${escapePrintHtml(formatYen(taxAmount))}</span>`)
  }
  htmlParts.push(`<span>合計 <strong>${escapePrintHtml(formatYen(totalAmount))}</strong></span>`)
  htmlParts.push('</div>')
  htmlParts.push(`<div class="print-date">印刷日時：${escapePrintHtml(printedAt)}</div>`)

  htmlParts.push('<script>')
  htmlParts.push('window.onload = function() {')
  htmlParts.push('setTimeout(function() {')
  htmlParts.push('window.print();')
  htmlParts.push('window.onafterprint = function() { window.close(); };')
  htmlParts.push('}, 300);')
  htmlParts.push('};')
  htmlParts.push('<' + '/script>')
  htmlParts.push('</body></html>')

  printWindow.document.write(htmlParts.join('\n'))
  printWindow.document.close()
  ElMessage.success('印刷プレビューを開きました')
}

const STATUS_MAP: Record<string, { label: string; type: string }> = {
  draft: { label: '下書き', type: 'info' },
  pending: { label: '承認待ち', type: 'warning' },
  approved: { label: '承認済', type: 'success' },
  partial_delivered: { label: '一部納品', type: '' },
  completed: { label: '完了', type: 'success' },
  cancelled: { label: 'キャンセル', type: 'danger' },
}
function statusLabel(s: string) { return STATUS_MAP[s]?.label ?? s }
function statusType(s: string) { return (STATUS_MAP[s]?.type ?? 'info') as any }

const PAYMENT_MAP: Record<string, { label: string; type: string }> = {
  unpaid: { label: '未入金', type: 'danger' },
  partial_paid: { label: '一部入金', type: 'warning' },
  paid: { label: '入金済', type: 'success' },
}
function paymentLabel(s: string) { return PAYMENT_MAP[s]?.label ?? s ?? '—' }
function paymentType(s: string) { return (PAYMENT_MAP[s]?.type ?? 'info') as any }

function calcAmount(row: OrderItem) {
  row.amount = (row.quantity || 0) * (row.unit_price || 0)
}
function addItem() {
  if (!guardSalesOperation(canCreate)) return
 form.items.push(emptyItem()) }
function removeItem(idx: number) {
  if (!guardSalesOperation(canDelete)) return
 form.items.splice(idx, 1) }

function resetForm() {
  Object.assign(form, {
    customer_code: '',
    customer_name: '',
    destination_cd: '',
    destination_name: '',
    order_date: '',
    expected_delivery_date: '',
    sales_person: '',
    remarks: '',
    items: [emptyItem()],
  })
  isViewMode.value = false
  currentOrder.value = null
  relatedDailyList.value = []
}

function applyOrderToForm(order: Record<string, unknown>) {
  if (!guardSalesOperation(canEdit)) return

  const items = order.items as OrderItem[] | undefined
  Object.assign(form, {
    customer_code: (order.customer_code as string) ?? '',
    customer_name: (order.customer_name as string) ?? '',
    destination_cd: (order.destination_cd as string) ?? (order.customer_code as string) ?? '',
    destination_name: (order.destination_name as string) ?? (order.customer_name as string) ?? '',
    order_date: (order.order_date as string) ?? '',
    expected_delivery_date: (order.expected_delivery_date as string) ?? '',
    sales_person: (order.sales_person as string) ?? '',
    remarks: (order.remarks as string) ?? '',
    items: items?.length
      ? items.map((i) => ({
          product_code: i.product_code ?? '',
          product_name: i.product_name ?? '',
          quantity: Number(i.quantity) || 0,
          confirmed_boxes: Number(i.confirmed_boxes) || 0,
          item_order_no: (i as { item_order_no?: string }).item_order_no ?? '',
          unit_price: Number(i.unit_price) || 0,
          amount: Number(i.amount) || 0,
        }))
      : [emptyItem()],
  })
}

async function loadRelatedDailyOrders(order: Record<string, unknown>) {
  const start = order.order_date as string | undefined
  const end = (order.expected_delivery_date as string | undefined) || start
  if (!start || !end) {
    relatedDailyList.value = []
    return
  }
  const productCodes = new Set(
    ((order.items as { product_code?: string }[]) || [])
      .map((i) => i.product_code)
      .filter((cd): cd is string => Boolean(cd))
  )
  relatedDailyLoading.value = true
  try {
    const rows = await fetchOrderDailyList({ start_date: start, end_date: end })
    relatedDailyList.value =
      productCodes.size > 0 ? rows.filter((r) => productCodes.has(r.product_cd)) : rows
  } catch {
    relatedDailyList.value = []
  } finally {
    relatedDailyLoading.value = false
  }
}

function goToOrderDaily(source?: Record<string, unknown>) {
  const order = source ?? currentOrder.value
  if (!order) return
  const query: Record<string, string> = {}
  const start = order.order_date as string | undefined
  const end = (order.expected_delivery_date as string | undefined) || start
  if (start) query.start_date = start
  if (end) query.end_date = end
  const destCd =
    (order.destination_cd as string | undefined) ||
    (order.customer_code as string | undefined)
  if (destCd) query.destination_cd = destCd
  router.push({ path: '/erp/order/daily', query })
}

async function openDialog(row?: Record<string, unknown>) {
  resetForm()
  if (!row?.id) {
    dialogVisible.value = true
    return
  }
  isViewMode.value = true
  dialogVisible.value = true
  detailLoading.value = true
  try {
    const res: unknown = await getSalesOrderById(row.id as number)
    const wrapped = res as { data?: Record<string, unknown> }
    const order = wrapped?.data ?? (res as Record<string, unknown>)
    currentOrder.value = order
    applyOrderToForm(order)
    await loadRelatedDailyOrders(order)
  } catch {
    ElMessage.error('受注詳細の取得に失敗しました')
    dialogVisible.value = false
    resetForm()
  } finally {
    detailLoading.value = false
  }
}

async function handleSyncFromOrderDaily() {
  if (!guardSalesOperation(canCreate)) return

  if (!query.dateRange?.[0] || !query.dateRange?.[1]) {
    ElMessage.warning('取込期間を指定してください（開始日〜終了日）')
    return
  }
  const [start_date, end_date] = query.dateRange
  try {
    await ElMessageBox.confirm(
      `${start_date} 〜 ${end_date} の日別受注（確定箱数>0）を販売受注へ取込します。既に取込済みの行はスキップされます。`,
      '日別受注取込',
      { type: 'info', confirmButtonText: '取込', cancelButtonText: 'キャンセル' }
    )
  } catch {
    return
  }
  syncing.value = true
  try {
    const res: unknown = await syncSalesOrdersFromOrderDaily({ start_date, end_date })
    const data = (res as { data?: SyncFromOrderDailyResult })?.data ?? (res as SyncFromOrderDailyResult)
    ElMessage.success(
      `取込完了: 新規受注 ${data.created_orders} 件、明細 ${data.created_items} 行` +
        `（重複スキップ ${data.skipped_duplicate}、数量不可 ${data.skipped_invalid_qty}、確定済受注 ${data.skipped_locked_order}）`
    )
    fetchData()
  } catch (e: unknown) {
    const msg =
      (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
      (e instanceof Error ? e.message : '取込に失敗しました')
    ElMessage.error(typeof msg === 'string' ? msg : '取込に失敗しました')
  } finally {
    syncing.value = false
  }
}

async function loadDestinationOptions() {
  if (!guardSalesOperation(canCreate)) return

  try {
    destinationOptions.value = await getDestinationOptions()
  } catch {
    destinationOptions.value = []
  }
}

async function fetchData() {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }
    if (query.destination_cd) params.destination_cd = query.destination_cd
    if (query.status) params.status = query.status
    if (query.dateRange?.[0]) params.start_date = query.dateRange[0]
    if (query.dateRange?.[1]) params.end_date = query.dateRange[1]

    const res: any = await getSalesOrders(params)
    const data = res?.data ?? res
    tableData.value = data?.items ?? data?.records ?? data?.list ?? (Array.isArray(data) ? data : [])
    pagination.total = data?.total ?? tableData.value.length
  } catch (e: any) {
    console.error('Failed to fetch sales orders', e)
    tableData.value = []
    pagination.total = 0
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  if (!guardSalesOperation(canEdit)) return

  if (!formRef.value) return
  await formRef.value.validate()
  saving.value = true
  try {
    const payload = {
      ...form,
      customer_code: form.destination_cd || form.customer_code,
      customer_name: form.destination_name || form.customer_name,
      destination_cd: form.destination_cd,
      destination_name: form.destination_name,
      total_amount: itemsTotal.value,
    }
    await createSalesOrder(payload)
    ElMessage.success('受注を作成しました')
    dialogVisible.value = false
    fetchData()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '保存に失敗しました'
    ElMessage.error(msg)
  } finally {
    saving.value = false
  }
}

async function handleApprove(row: any) {
  if (!guardSalesOperation(canApprove)) return

  await ElMessageBox.confirm(`受注 ${row.order_no} を承認しますか？`, '確認', { type: 'info' })
  try {
    await approveSalesOrder(row.id)
    ElMessage.success('承認しました')
    fetchData()
  } catch (e: any) {
    ElMessage.error(e?.message || '承認に失敗しました')
  }
}

onMounted(() => {
  loadDestinationOptions()
  fetchData()
})
</script>

<style scoped>
/* ===== Layout ===== */
.page-root {
  position: relative;
  min-height: 100vh;
  padding: 16px;
  overflow: hidden;
}

/* ===== Animated background (matches Sales.vue) ===== */
.dynamic-background {
  position: fixed;
  inset: 0;
  z-index: 0;
  background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
}
.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.4;
  animation: float 20s ease-in-out infinite;
}
.orb-1 { width: 400px; height: 400px; top: -100px; left: -100px; background: radial-gradient(circle, #8b5cf6, transparent); }
.orb-2 { width: 350px; height: 350px; top: 40%; right: -80px; background: radial-gradient(circle, #3b82f6, transparent); animation-delay: -7s; }
.orb-3 { width: 300px; height: 300px; bottom: -50px; left: 30%; background: radial-gradient(circle, #06b6d4, transparent); animation-delay: -14s; }
.noise-overlay {
  position: absolute;
  inset: 0;
  background: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E");
}
@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -30px) scale(1.05); }
  66% { transform: translate(-20px, 20px) scale(0.95); }
}

/* ===== Glass card base ===== */
.glass-card {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 14px;
  margin-bottom: 12px;
}

/* ===== Header ===== */
.glass-header {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 16px;
  padding: 14px 22px;
  margin-bottom: 12px;
}
.header-content { display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.header-left { display: flex; align-items: center; gap: 12px; }
.header-icon {
  width: 46px; height: 46px;
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  border-radius: 13px;
  display: flex; align-items: center; justify-content: center;
  color: #fff;
  box-shadow: 0 4px 20px rgba(139, 92, 246, 0.4);
}
.header-title { font-size: 1.35rem; font-weight: 700; color: #fff; margin: 0; }
.header-subtitle { font-size: 0.75rem; color: rgba(255, 255, 255, 0.55); }
.header-badges { display: flex; gap: 8px; }
.badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.75rem;
  color: #e2e8f0;
  border: 1px solid rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(8px);
}
.badge b { font-weight: 700; margin-left: 2px; }
.badge-total { background: rgba(139, 92, 246, 0.2); }
.badge-pending { background: rgba(245, 158, 11, 0.2); }

/* ===== Filter bar ===== */
.filter-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  flex-wrap: wrap;
}
.filter-input { width: 200px; }
.filter-input-sm { width: 160px; }
.filter-select { width: 150px; }
.filter-select-dest { width: 220px; min-width: 180px; }
.filter-date { width: 260px; }

/* ===== Dark input overrides ===== */
:deep(.dark-input .el-input__wrapper),
:deep(.dark-input .el-select__wrapper),
:deep(.dark-form .el-input__wrapper),
:deep(.dark-form .el-textarea__inner),
:deep(.dark-form .el-select__wrapper) {
  background: rgba(255, 255, 255, 0.07) !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
  box-shadow: none !important;
  border-radius: 8px;
  color: #e2e8f0;
}
:deep(.dark-input .el-input__inner),
:deep(.dark-form .el-input__inner) {
  color: #e2e8f0 !important;
}
:deep(.dark-input .el-input__inner::placeholder),
:deep(.dark-form .el-input__inner::placeholder),
:deep(.dark-form .el-textarea__inner::placeholder) {
  color: rgba(255, 255, 255, 0.35);
}
:deep(.dark-form .el-form-item__label) {
  color: rgba(255, 255, 255, 0.7) !important;
  font-size: 13px;
}
:deep(.dark-form .el-textarea__inner) {
  color: #e2e8f0 !important;
}

/* ===== Gradient buttons ===== */
.gradient-btn {
  background: linear-gradient(135deg, #8b5cf6, #6366f1) !important;
  border: none !important;
  color: #fff !important;
  border-radius: 8px;
  font-weight: 600;
  transition: transform 0.2s, box-shadow 0.2s;
}
.gradient-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.45);
}
.create-btn {
  background: linear-gradient(135deg, #10b981, #059669) !important;
}
.create-btn:hover {
  box-shadow: 0 4px 16px rgba(16, 185, 129, 0.45);
}
.sync-btn {
  background: linear-gradient(135deg, #0ea5e9, #0284c7) !important;
}
.sync-btn:hover {
  box-shadow: 0 4px 16px rgba(14, 165, 233, 0.45);
}

/* ===== Table ===== */
.table-card { padding: 0; overflow: hidden; }
:deep(.dark-table) {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-row-hover-bg-color: rgba(255, 255, 255, 0.05);
  --el-table-header-bg-color: transparent;
  --el-table-border-color: rgba(255, 255, 255, 0.06);
  --el-table-text-color: #cbd5e1;
  --el-table-header-text-color: #e2e8f0;
  --el-fill-color-lighter: rgba(255, 255, 255, 0.03);
  background: transparent !important;
}
:deep(.dark-table .el-table__inner-wrapper::before),
:deep(.dark-table .el-table__border-left-patch) {
  display: none;
}
:deep(.dark-table th.el-table__cell) {
  font-weight: 600;
}
:deep(.dark-table td.el-table__cell) {
  padding: 6px 0;
  border-color: rgba(255, 255, 255, 0.05);
}
:deep(.dark-table .el-table__empty-block) {
  background: transparent;
  color: rgba(255, 255, 255, 0.4);
}

.action-link { color: #60a5fa !important; font-weight: 500; }
.action-link.approve { color: #34d399 !important; }
.action-link.danger { color: #f87171 !important; }

/* ===== Pagination ===== */
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  padding: 12px 16px;
}
:deep(.el-pagination) {
  --el-pagination-bg-color: transparent;
  --el-pagination-text-color: rgba(255, 255, 255, 0.6);
  --el-pagination-button-bg-color: rgba(255, 255, 255, 0.06);
  --el-pagination-button-color: rgba(255, 255, 255, 0.7);
  --el-pagination-hover-color: #a78bfa;
}
:deep(.el-pagination .is-active) {
  background: linear-gradient(135deg, #8b5cf6, #6366f1) !important;
  color: #fff !important;
  border-radius: 6px;
}
:deep(.el-pagination button:disabled) { color: rgba(255, 255, 255, 0.2) !important; }

/* ===== Sales order dialog（高对比・浅色ガラス：一覧の紫アクセントと整合） ===== */
:deep(.sales-order-dialog.el-dialog),
:deep(.sales-order-dialog .el-dialog) {
  background: #f8fafc !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 16px !important;
  box-shadow:
    0 24px 48px rgba(15, 23, 42, 0.18),
    0 8px 16px rgba(15, 23, 42, 0.08) !important;
  overflow: hidden;
}
:deep(.sales-order-dialog .el-dialog__header) {
  margin: 0;
  padding: 0;
  border: none;
}
:deep(.sales-order-dialog .el-dialog__body) {
  padding: 0 16px 12px !important;
  max-height: min(72vh, 680px);
  overflow-y: auto;
  background: #f1f5f9 !important;
  color: #0f172a;
}
:deep(.sales-order-dialog .el-dialog__footer) {
  padding: 0;
  border: none;
  background: #fff !important;
}

.so-dialog-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  border-bottom: none;
  background: linear-gradient(135deg, #6366f1 0%, #7c3aed 55%, #6d28d9 100%);
}
.so-dialog-header__left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}
.so-dialog-header__icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: linear-gradient(135deg, #8b5cf6, #6366f1);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.45);
  flex-shrink: 0;
}
.so-dialog-header__icon--create {
  background: linear-gradient(135deg, #10b981, #059669);
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
}
.so-dialog-header__title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: #f8fafc;
  letter-spacing: -0.02em;
}
.so-dialog-header__sub {
  margin: 2px 0 0;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.88);
}
.so-dialog-header__sub .mono {
  color: #fff;
  font-weight: 600;
}
.so-dialog-header__tags {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}
.so-dialog-header__tags :deep(.el-tag) {
  font-weight: 700;
  border: none;
}
.so-tag-payment {
  background: rgba(255, 255, 255, 0.95) !important;
  color: #b45309 !important;
}
.so-dialog-header__close {
  font-size: 20px;
  color: rgba(255, 255, 255, 0.9);
  cursor: pointer;
  padding: 6px;
  border-radius: 8px;
  transition: color 0.15s, background 0.15s;
  flex-shrink: 0;
}
.so-dialog-header__close:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.22);
}

.so-dialog-body {
  min-height: 120px;
}

.so-kpi-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
  margin: 8px 0 8px;
}
.so-kpi {
  padding: 8px 10px;
  border-radius: 8px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-left: 4px solid #94a3b8;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
}
.so-kpi--amount {
  border-left-color: #7c3aed;
  background: linear-gradient(135deg, #ede9fe 0%, #fff 100%);
}
.so-kpi--amount .so-kpi__value {
  color: #5b21b6;
}
.so-kpi--date { border-left-color: #2563eb; }
.so-kpi--delivery { border-left-color: #059669; }
.so-kpi--lines { border-left-color: #d97706; }
.so-kpi__label {
  display: block;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #64748b;
  margin-bottom: 4px;
}
.so-kpi__value {
  font-size: 15px;
  font-weight: 800;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.02em;
}

.so-section {
  margin-bottom: 10px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.05);
}
.so-section__head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 12px;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 1px solid #e2e8f0;
}
.so-section__icon {
  font-size: 16px;
  color: #6366f1;
}
.so-section__icon--goods { color: #2563eb; }
.so-section__icon--daily { color: #0891b2; }
.so-section__title {
  font-size: 13px;
  font-weight: 800;
  color: #0f172a;
  flex: 1;
  letter-spacing: -0.02em;
}
.so-section__badge {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 20px;
  background: #ede9fe;
  color: #6d28d9;
}
.so-section__badge--cyan {
  background: #cffafe;
  color: #0e7490;
}
.so-section__action {
  margin-left: auto;
}
.so-print-btn {
  border-color: #c7d2fe;
  color: #4338ca;
  background: #eef2ff;
}
.so-print-btn:hover {
  border-color: #a5b4fc;
  color: #3730a3;
  background: #e0e7ff;
}
.so-section__body {
  padding: 12px;
}
.so-section__body--flush {
  padding: 0;
}
.so-section__body--flush .so-total-bar {
  margin: 0;
  border-radius: 0 0 11px 11px;
}

.so-section--compact {
  margin-bottom: 8px;
}
.so-section__head--compact {
  padding: 6px 10px;
}
.so-section__body--compact {
  padding: 8px 10px;
}

/* 基本情報：1行コンパクトバー */
.so-basic-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 10px;
  min-height: 0;
}
.so-basic-dest {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex: 1 1 200px;
}
.so-basic-dest-cd {
  flex-shrink: 0;
  padding: 2px 8px;
  border-radius: 6px;
  font-family: ui-monospace, 'Cascadia Code', 'Consolas', monospace;
  font-size: 12px;
  font-weight: 700;
  color: #4338ca;
  background: #eef2ff;
  border: 1px solid #c7d2fe;
  letter-spacing: 0.02em;
}
.so-basic-dest-name {
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.so-basic-sep {
  width: 1px;
  height: 22px;
  background: #e2e8f0;
  flex-shrink: 0;
}
.so-basic-field {
  display: inline-flex;
  align-items: baseline;
  gap: 6px;
  min-width: 0;
  flex: 0 1 auto;
}
.so-basic-field--remarks {
  flex: 1 1 160px;
  max-width: 100%;
}
.so-basic-field-label {
  flex-shrink: 0;
  font-size: 10px;
  font-weight: 700;
  color: #94a3b8;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.so-basic-field-value {
  font-size: 12px;
  font-weight: 600;
  color: #334155;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.so-basic-field--remarks .so-basic-field-value {
  font-weight: 500;
  color: #64748b;
}

.so-edit-grid--compact :deep(.el-form-item) {
  margin-bottom: 8px;
}
.so-edit-grid--compact :deep(.el-form-item__label) {
  padding-bottom: 2px;
  line-height: 1.2;
  font-size: 12px;
}

.so-edit-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 12px;
}
.so-edit-remarks {
  grid-column: 1 / -1;
}

.mono {
  font-family: ui-monospace, 'Cascadia Code', 'Consolas', monospace;
  font-size: 0.92em;
  letter-spacing: 0.02em;
  color: #1e293b;
}
.num {
  font-variant-numeric: tabular-nums;
  font-weight: 700;
  color: #0f172a;
}

:deep(.sales-order-dialog .so-detail-table) {
  --el-table-bg-color: #fff;
  --el-table-tr-bg-color: #fff;
  --el-table-header-bg-color: #f8fafc;
  --el-table-row-hover-bg-color: #f5f3ff;
  --el-table-border-color: #e2e8f0;
  --el-table-text-color: #1e293b;
  --el-table-header-text-color: #475569;
  --el-fill-color-lighter: #f8fafc;
  width: 100%;
}
:deep(.sales-order-dialog .so-detail-table th.el-table__cell) {
  font-size: 11px;
  font-weight: 800;
  padding: 9px 8px;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%) !important;
  color: #475569 !important;
  border-bottom: 1px solid #e2e8f0 !important;
}
:deep(.sales-order-dialog .so-detail-table td.el-table__cell) {
  font-size: 13px;
  font-weight: 500;
  padding: 8px;
  color: #1e293b !important;
  border-color: #f1f5f9;
}
:deep(.sales-order-dialog .so-detail-table .el-table__row--striped td.el-table__cell) {
  background: #fafbfc !important;
}
:deep(.sales-order-dialog .so-detail-table .el-table__inner-wrapper::before) {
  display: none;
}
:deep(.sales-order-dialog .so-detail-table .el-table__empty-text) {
  color: #64748b;
}
.so-amount-cell {
  font-weight: 800;
  color: #6d28d9;
}

.so-total-bar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 16px;
  padding: 11px 14px;
  background: linear-gradient(90deg, #ede9fe 0%, #f5f3ff 100%);
  border-top: 1px solid #ddd6fe;
}
.so-total-bar__tax {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
}
.so-total-bar__main {
  font-size: 14px;
  font-weight: 600;
  color: #334155;
}
.so-total-bar__main strong {
  font-size: 1.2rem;
  font-weight: 800;
  color: #5b21b6;
  margin-left: 6px;
  font-variant-numeric: tabular-nums;
}

.so-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 12px 18px 16px;
  border-top: 1px solid #e2e8f0;
  background: #fff;
}
.so-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border-radius: 9px !important;
  font-weight: 700;
  font-size: 13px;
  padding: 9px 18px !important;
}
.so-btn--ghost {
  background: #fff !important;
  border: 1px solid #cbd5e1 !important;
  color: #334155 !important;
}
.so-btn--ghost:hover {
  background: #f8fafc !important;
  border-color: #94a3b8 !important;
  color: #0f172a !important;
}
.so-btn--primary {
  background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
  border: none !important;
  color: #fff !important;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.35);
}
.so-btn--primary:hover {
  box-shadow: 0 4px 14px rgba(37, 99, 235, 0.45);
}
.so-btn--save {
  min-width: 100px;
}

:deep(.sales-order-dialog .so-form--view .el-form-item) {
  margin-bottom: 0;
}
:deep(.sales-order-dialog .so-form .el-form-item__label) {
  color: #475569 !important;
  font-size: 12px;
  font-weight: 600;
}
:deep(.sales-order-dialog .so-form .el-input__wrapper),
:deep(.sales-order-dialog .so-form .el-textarea__inner),
:deep(.sales-order-dialog .so-form .el-select__wrapper) {
  background: #fff !important;
  border: 1px solid #cbd5e1 !important;
  box-shadow: none !important;
  color: #0f172a !important;
}
:deep(.sales-order-dialog .so-edit-table) {
  --el-table-text-color: #1e293b;
  --el-table-header-text-color: #475569;
  --el-table-border-color: #e2e8f0;
  --el-table-header-bg-color: #f8fafc;
}
:deep(.sales-order-dialog .so-edit-table .el-input__inner) {
  color: #0f172a !important;
}

:deep(.sales-order-dialog .so-status-tag) {
  font-weight: 700;
  color: #0369a1 !important;
  background: #e0f2fe !important;
  border-color: #7dd3fc !important;
}

@media (max-width: 768px) {
  .so-kpi-strip {
    grid-template-columns: repeat(2, 1fr);
  }
  .so-basic-sep {
    display: none;
  }
  .so-basic-bar {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }
  .so-basic-dest {
    flex: 1 1 100%;
    width: 100%;
  }
  .so-basic-field--remarks .so-basic-field-value {
    white-space: normal;
  }
  .so-edit-grid {
    grid-template-columns: 1fr;
  }
  .so-dialog-header__tags {
    display: none;
  }
}

/* ===== Animations ===== */
.animate-in {
  animation: slideIn 0.45s ease forwards;
  opacity: 0;
  transform: translateY(10px);
}
@keyframes slideIn {
  to { opacity: 1; transform: translateY(0); }
}

/* ===== Responsive ===== */
@media (max-width: 768px) {
  .page-root { padding: 10px; }
  .filter-bar { flex-direction: column; }
  .filter-input, .filter-input-sm, .filter-select, .filter-select-dest, .filter-date { width: 100%; }
  .so-edit-grid { grid-template-columns: 1fr; }
  .header-badges { margin-top: 6px; }
}
</style>
