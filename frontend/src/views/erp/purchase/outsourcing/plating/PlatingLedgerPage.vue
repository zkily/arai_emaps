<template>
  <div class="plating-ledger-page pl-modern pb-std">
    <div class="page-header pb-hero pb-hero--page">
      <div class="head-fx pb-bubbles" aria-hidden="true" />
      <div class="header-left">
        <div class="title-icon"><el-icon><Brush /></el-icon></div>
        <div class="title-text">
          <h2 class="title pb-hero-title">外注メッキ</h2>
          <p class="subtitle pb-hero-desc">
            日付×外注先×製品の行を先に生成し、注文数・受入数・不良数・初期在庫を入力します。現在庫は外注先手元です。
          </p>
        </div>
      </div>
      <div class="header-actions">
        <el-button class="head-btn head-btn--link" @click="openPage('OutsourcingSuppliers')">
          <el-icon><OfficeBuilding /></el-icon>
          外注先マスタ
        </el-button>
        <el-button class="head-btn head-btn--link" @click="openPage('OutsourcingProcessProducts')">
          <el-icon><Goods /></el-icon>
          外注加工製品
        </el-button>
        <span class="head-divider" aria-hidden="true" />
        <el-button
          v-if="canCreate"
          class="head-btn head-btn--gen"
          :loading="generating"
          @click="openGenerate"
        >
          <el-icon><DocumentAdd /></el-icon>
          データ生成
        </el-button>
        <el-button
          v-if="canEdit"
          class="head-btn head-btn--master"
          :loading="refreshing"
          @click="openRefreshMaster"
        >
          <el-icon><Refresh /></el-icon>
          マスタ反映
        </el-button>
        <el-button
          v-if="canEdit"
          class="head-btn head-btn--calc"
          :loading="calculating"
          @click="runCalculate"
        >
          <el-icon><Operation /></el-icon>
          在庫計算
        </el-button>
      </div>
    </div>

    <div class="filter-card">
      <div class="filter-fields">
        <div v-show="activeTab !== 'initial' && activeTab !== 'stock'" class="filter-field filter-field--date">
          <span class="filter-label">
            <el-icon><Calendar /></el-icon>{{ activeTab === 'receivingHistory' ? '受入日' : '注文日' }}
          </span>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            value-format="YYYY-MM-DD"
            range-separator="〜"
            start-placeholder="開始日"
            end-placeholder="終了日"
            :clearable="false"
            class="filter-control"
          />
          <el-button-group class="month-shortcuts">
            <el-button class="month-btn" @click="shiftDay(-1)">
              <el-icon><ArrowLeft /></el-icon>前日
            </el-button>
            <el-button
              class="month-btn"
              :class="{ 'is-active': isToday }"
              :type="isToday ? 'primary' : 'default'"
              @click="setToday"
            >
              今日
            </el-button>
            <el-button class="month-btn" @click="shiftDay(1)">
              翌日<el-icon class="el-icon--right"><ArrowRight /></el-icon>
            </el-button>
          </el-button-group>
          <el-button-group class="month-shortcuts">
            <el-button class="month-btn" @click="shiftMonth(-1)">
              <el-icon><ArrowLeft /></el-icon>前月
            </el-button>
            <el-button
              class="month-btn"
              :class="{ 'is-active': isCurrentMonth }"
              :type="isCurrentMonth ? 'primary' : 'default'"
              @click="setCurrentMonth"
            >
              今月
            </el-button>
            <el-button class="month-btn" @click="shiftMonth(1)">
              翌月<el-icon class="el-icon--right"><ArrowRight /></el-icon>
            </el-button>
          </el-button-group>
        </div>
        <div class="filter-field">
          <span class="filter-label"><el-icon><OfficeBuilding /></el-icon>外注先</span>
          <el-select
            v-model="supplierCd"
            placeholder="すべて"
            clearable
            filterable
            class="filter-control"
          >
            <el-option
              v-for="s in supplierOptions"
              :key="s.value"
              :label="s.label"
              :value="s.value"
            />
          </el-select>
        </div>
        <div class="filter-field filter-field--product">
          <span class="filter-label"><el-icon><Goods /></el-icon>製品名</span>
          <el-select
            v-model="productCd"
            placeholder="すべて"
            clearable
            filterable
            class="filter-control"
          >
            <el-option
              v-for="p in productOptions"
              :key="p.value"
              :label="p.label"
              :value="p.value"
            >
              <div class="product-option">
                <span class="product-option__name">{{ p.name }}</span>
                <span class="product-option__cd">{{ p.value }}</span>
              </div>
            </el-option>
          </el-select>
        </div>
        <div v-if="activeTab === 'order' || activeTab === 'receiving'" class="filter-field">
          <el-switch
            v-model="onlyNonZero"
            inline-prompt
            active-text="入力あり"
            inactive-text="全行"
            class="nonzero-switch"
          />
          <span class="nonzero-hint">{{ nonZeroHint }}</span>
        </div>
      </div>
    </div>

    <div ref="tableWrapRef" class="table-wrap" :class="`tab-${activeTab}`">
      <div class="tabs-row">
      <el-tabs v-model="activeTab" class="ledger-tabs">
        <el-tab-pane name="ledger">
          <template #label>
            <span class="ledger-tab-label ledger-tab-label--ledger"><el-icon><Tickets /></el-icon>台帳</span>
          </template>
        </el-tab-pane>
        <el-tab-pane name="order">
          <template #label>
            <span class="ledger-tab-label ledger-tab-label--outorder"><el-icon><ShoppingCart /></el-icon>外注注文</span>
          </template>
        </el-tab-pane>
        <el-tab-pane name="receiving">
          <template #label>
            <span class="ledger-tab-label ledger-tab-label--outrecv"><el-icon><Download /></el-icon>外注受入</span>
          </template>
        </el-tab-pane>
        <el-tab-pane name="initial">
          <template #label>
            <span class="ledger-tab-label ledger-tab-label--initial"><el-icon><Box /></el-icon>初期在庫</span>
          </template>
        </el-tab-pane>
        <el-tab-pane name="orderHistory">
          <template #label>
            <span class="ledger-tab-label ledger-tab-label--order"><el-icon><Document /></el-icon>注文履歴</span>
          </template>
        </el-tab-pane>
        <el-tab-pane name="receivingHistory">
          <template #label>
            <span class="ledger-tab-label ledger-tab-label--recv"><el-icon><Finished /></el-icon>受入履歴</span>
          </template>
        </el-tab-pane>
        <el-tab-pane name="stock">
          <template #label>
            <span class="ledger-tab-label ledger-tab-label--stock"><el-icon><Coin /></el-icon>現在庫</span>
          </template>
        </el-tab-pane>
      </el-tabs>
      <div v-if="activeTab === 'initial'" class="initial-bar">
        <span class="filter-label"><el-icon><Calendar /></el-icon>対象月</span>
        <el-date-picker
          v-model="initialMonth"
          type="month"
          value-format="YYYY-MM"
          format="YYYY年M月"
          placeholder="対象月"
          :clearable="false"
          size="small"
          class="filter-control initial-month"
        />
      </div>
      <div v-else-if="activeTab === 'stock'" class="initial-bar">
        <span class="filter-label"><el-icon><Calendar /></el-icon>基準日</span>
        <el-date-picker
          v-model="stockAsOf"
          type="date"
          value-format="YYYY-MM-DD"
          format="YYYY/MM/DD"
          placeholder="基準日"
          :clearable="false"
          size="small"
          class="filter-control initial-month"
        />
      </div>
      <div v-else-if="isHistoryTab" class="initial-bar">
        <el-radio-group v-model="historyView" size="small" class="view-switch">
          <el-radio-button value="list">
            <el-icon><List /></el-icon>一覧
          </el-radio-button>
          <el-radio-button value="pivot">
            <el-icon><Grid /></el-icon>二次元表
          </el-radio-button>
        </el-radio-group>
      </div>
      <div v-else-if="activeTab === 'order'" class="initial-bar">
        <PlatingOrderSheetIssuer
          :default-date="dateRange[0]"
          :default-supplier-cd="supplierCd"
          @issued="applyAffected"
        />
      </div>
      </div>
      <el-table
        v-if="isLedgerTable"
        :key="activeTab"
        v-loading="loading"
        :data="rows"
        border
        stripe
        height="calc(100vh - 335px)"
        size="small"
      >
        <el-table-column label="注文日" width="136" align="center" fixed="left">
          <template #default="{ row }">
            <span class="date-cell" :class="weekendClass(row.order_date)">
              {{ row.order_date }}<small>{{ weekdayLabel(row.order_date) }}</small>
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="supplier_name" label="外注先" width="160" show-overflow-tooltip />
        <el-table-column prop="product_cd" label="製品CD" width="86" align="center" class-name="col-code" />
        <el-table-column prop="product_name" label="製品名" min-width="160" show-overflow-tooltip />
        <el-table-column
          v-if="activeTab !== 'receiving'"
          label="注文数"
          width="108"
          :align="activeTab === 'order' ? 'center' : 'right'"
          class-name="col-order"
        >
          <template #default="{ row, $index }">
            <el-input-number
              v-if="activeTab === 'order'"
              :model-value="emptyIfZero(row.order_qty)"
              :min="0"
              :max="9999999"
              :precision="0"
              :controls="false"
              :value-on-clear="null"
              size="small"
              :disabled="!canEdit"
              class="qty-input qty-input--order"
              :data-nav-row="$index"
              data-nav-col="0"
              @change="(val) => saveField(row as PlatingLedgerRow, 'order_qty', val)"
              @keydown.capture="(e: KeyboardEvent) => onCellKeydown(e, $index, 0)"
              @wheel.prevent
            />
            <span v-else class="qty-view qty-view--order">{{ blankIfZero(row.order_qty) }}</span>
          </template>
        </el-table-column>
        <template v-if="activeTab !== 'receiving'">
          <el-table-column label="単価" width="80" align="right" class-name="col-order">
            <template #default="{ row }"><span class="num-muted">{{ formatNum(row.unit_price) }}</span></template>
          </el-table-column>
          <el-table-column prop="delivery_date" label="納期" width="104" align="center" class-name="col-order" />
          <el-table-column label="金額" width="112" align="right" class-name="col-order">
            <template #default="{ row }">
              <span :class="row.order_amount ? 'num-strong' : 'num-muted'">{{ formatNum(row.order_amount) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="注文番号" width="176" align="center" class-name="col-order">
            <template #default="{ row }">
              <span v-if="row.order_no" class="no-chip no-chip--order">{{ row.order_no }}</span>
            </template>
          </el-table-column>
          <el-table-column label="注文書" width="92" align="center" class-name="col-order">
            <template #default="{ row }">
              <template v-if="row.order_qty > 0">
                <el-tooltip
                  v-if="row.order_sheet_issued_at"
                  :content="`${row.order_sheet_issued_at} ${row.order_sheet_issued_by || ''}`"
                  placement="top"
                >
                  <span class="issue-tag issue-tag--done">発行済</span>
                </el-tooltip>
                <span v-else class="issue-tag issue-tag--todo">未発行</span>
              </template>
            </template>
          </el-table-column>
        </template>
        <el-table-column
          v-if="activeTab !== 'order'"
          label="受入数"
          width="108"
          :align="activeTab === 'receiving' ? 'center' : 'right'"
          class-name="col-recv"
        >
          <template #default="{ row, $index }">
            <el-input-number
              v-if="activeTab === 'receiving'"
              :model-value="emptyIfZero(row.receiving_qty)"
              :min="0"
              :max="9999999"
              :precision="0"
              :controls="false"
              :value-on-clear="null"
              size="small"
              :disabled="!canEdit"
              class="qty-input qty-input--recv"
              :class="{ 'is-over': isOverStock(row as PlatingLedgerRow) }"
              :data-nav-row="$index"
              data-nav-col="0"
              @change="(val) => saveField(row as PlatingLedgerRow, 'receiving_qty', val)"
              @keydown.capture="(e: KeyboardEvent) => onCellKeydown(e, $index, 0)"
              @wheel.prevent
            />
            <span v-else class="qty-view qty-view--recv">{{ blankIfZero(row.receiving_qty) }}</span>
          </template>
        </el-table-column>
        <el-table-column
          v-if="activeTab !== 'order'"
          label="不良数"
          width="108"
          :align="activeTab === 'receiving' ? 'center' : 'right'"
          class-name="col-defect"
        >
          <template #default="{ row, $index }">
            <el-input-number
              v-if="activeTab === 'receiving'"
              :model-value="emptyIfZero(row.defect_qty)"
              :min="0"
              :max="9999999"
              :precision="0"
              :controls="false"
              :value-on-clear="null"
              size="small"
              :disabled="!canEdit"
              class="qty-input qty-input--defect"
              :class="{ 'is-over': isOverStock(row as PlatingLedgerRow) }"
              :data-nav-row="$index"
              data-nav-col="1"
              @change="(val) => saveField(row as PlatingLedgerRow, 'defect_qty', val)"
              @keydown.capture="(e: KeyboardEvent) => onCellKeydown(e, $index, 1)"
              @wheel.prevent
            />
            <span v-else class="qty-view qty-view--defect">{{ blankIfZero(row.defect_qty) }}</span>
          </template>
        </el-table-column>
        <el-table-column
          v-if="activeTab !== 'order'"
          label="現在庫"
          width="100"
          align="right"
          class-name="col-stock"
        >
          <template #default="{ row }">
            <span class="stock-badge" :class="stockClass(row.current_stock)">{{ formatNum(row.current_stock) }}</span>
          </template>
        </el-table-column>
      </el-table>
      <el-table
        v-else-if="activeTab === 'initial'"
        v-loading="loading"
        :data="rows"
        border
        stripe
        height="calc(100vh - 335px)"
        size="small"
      >
        <el-table-column label="対象月" width="124" align="center" fixed="left">
          <template #default="{ row }">
            <span class="month-chip">{{ formatMonth(row.order_date) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="order_date" label="注文日" width="104" align="center" />
        <el-table-column prop="supplier_name" label="外注先" width="160" show-overflow-tooltip />
        <el-table-column prop="product_cd" label="製品CD" width="86" align="center" class-name="col-code" />
        <el-table-column prop="product_name" label="製品名" min-width="200" show-overflow-tooltip />
        <el-table-column label="初期在庫" width="130" align="center" class-name="col-initial">
          <template #default="{ row, $index }">
            <el-input-number
              :model-value="emptyIfZero(row.initial_stock)"
              :min="0"
              :max="9999999"
              :precision="0"
              :controls="false"
              :value-on-clear="null"
              size="small"
              :disabled="!canEdit"
              class="qty-input qty-input--initial"
              :data-nav-row="$index"
              data-nav-col="0"
              @change="(val) => saveField(row as PlatingLedgerRow, 'initial_stock', val)"
              @keydown.capture="(e: KeyboardEvent) => onCellKeydown(e, $index, 0)"
              @wheel.prevent
            />
          </template>
        </el-table-column>
        <el-table-column label="現在庫" width="100" align="right" class-name="col-stock">
          <template #default="{ row }">
            <span class="stock-badge" :class="stockClass(row.current_stock)">{{ formatNum(row.current_stock) }}</span>
          </template>
        </el-table-column>
        <template #empty>
          <span>この月の1日の行がありません。データ生成でこの月の1日を含む期間を作成してください。</span>
        </template>
      </el-table>
      <PlatingStockPanel
        v-else-if="activeTab === 'stock'"
        :as-of="stockAsOf"
        :supplier-cd="supplierCd"
        :product-cd="productCd"
      />
      <PlatingHistoryPanel
        v-else
        :kind="activeTab === 'orderHistory' ? 'order' : 'receiving'"
        :view="historyView"
        :start-date="dateRange[0]"
        :end-date="dateRange[1]"
        :supplier-cd="supplierCd"
        :product-cd="productCd"
      />
      <div v-if="!isPanelTab" class="pager">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :page-sizes="[50, 100, 200, 500]"
          :total="total"
          layout="total, sizes, prev, pager, next"
          size="small"
          @current-change="load"
          @size-change="search"
        />
      </div>
    </div>

    <el-dialog
      v-model="generateVisible"
      title="データ生成期間設定"
      width="440px"
      class="pll-dialog pb-std"
      :close-on-click-modal="false"
      :show-close="false"
    >
      <template #header>
        <div class="gen-hero pb-hero">
          <div class="head-fx pb-bubbles" aria-hidden="true" />
          <span class="gen-hero__icon"><el-icon><DocumentAdd /></el-icon></span>
          <div class="gen-hero__copy">
            <span class="gen-hero__title">データ生成期間設定</span>
            <p class="gen-hero__desc">外注先×製品の日次行をまとめて作成</p>
          </div>
          <el-icon class="gen-hero__close" @click="generateVisible = false"><Close /></el-icon>
        </div>
      </template>
      <el-form label-width="72px" class="gen-form">
        <el-form-item label="開始日">
          <el-date-picker v-model="genStart" type="date" value-format="YYYY-MM-DD" placeholder="開始日" style="width: 100%" />
        </el-form-item>
        <el-form-item label="終了日">
          <el-date-picker v-model="genEnd" type="date" value-format="YYYY-MM-DD" placeholder="終了日" style="width: 100%" />
        </el-form-item>
      </el-form>
      <ul class="gen-notes">
        <li>有効な外注メッキ製品ごとに、1日1行を作ります。</li>
        <li>すでにある行はスキップし、入力済みの数量は残します。</li>
        <li>納期は外注先のリードタイムで、土日と会社休を飛ばして計算します。</li>
        <li>注文番号は注文数を入れたときに付きます。</li>
      </ul>
      <template #footer>
        <el-button class="dlg-btn" @click="generateVisible = false">キャンセル</el-button>
        <el-button
          type="primary"
          class="dlg-btn dlg-btn--run"
          :disabled="!genStart || !genEnd"
          :loading="generating"
          @click="runGenerate"
        >
          生成実行
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="refreshVisible"
      title="マスタ反映"
      width="460px"
      class="pll-dialog pb-std"
      :close-on-click-modal="false"
      :show-close="false"
    >
      <template #header>
        <div class="gen-hero pb-hero">
          <div class="head-fx pb-bubbles" aria-hidden="true" />
          <span class="gen-hero__icon"><el-icon><Refresh /></el-icon></span>
          <div class="gen-hero__copy">
            <span class="gen-hero__title">マスタ反映</span>
            <p class="gen-hero__desc">単価・納期・名称を現在の外注先／製品マスタで更新</p>
          </div>
          <el-icon class="gen-hero__close" @click="refreshVisible = false"><Close /></el-icon>
        </div>
      </template>
      <el-form label-width="72px" class="gen-form">
        <el-form-item label="開始日">
          <el-date-picker v-model="refreshStart" type="date" value-format="YYYY-MM-DD" placeholder="開始日" style="width: 100%" />
        </el-form-item>
        <el-form-item label="終了日">
          <el-date-picker v-model="refreshEnd" type="date" value-format="YYYY-MM-DD" placeholder="終了日" style="width: 100%" />
        </el-form-item>
        <el-form-item label="対象">
          <el-checkbox v-model="refreshIncludeOrdered">注文済みでも注文書未発行の行を含める</el-checkbox>
        </el-form-item>
      </el-form>
      <ul class="gen-notes">
        <li>既定では未注文（注文数 0）の行だけを更新します。</li>
        <li>注文書を発行済みの行は更新しません。</li>
        <li>注文済みの行を含めた場合、金額も新しい単価で再計算します。</li>
        <li>絞り込み中の外注先・製品名があれば、その範囲だけが対象です。</li>
      </ul>
      <template #footer>
        <el-button class="dlg-btn" @click="refreshVisible = false">キャンセル</el-button>
        <el-button
          type="primary"
          class="dlg-btn dlg-btn--run"
          :disabled="!refreshStart || !refreshEnd"
          :loading="refreshing"
          @click="runRefreshMaster"
        >
          反映実行
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft,
  ArrowRight,
  Box,
  Brush,
  Calendar,
  Close,
  Coin,
  Download,
  ShoppingCart,
  Document,
  DocumentAdd,
  Finished,
  Goods,
  Grid,
  List,
  OfficeBuilding,
  Operation,
  Refresh,
  Tickets,
} from '@element-plus/icons-vue'
import {
  calculatePlatingLedger,
  generatePlatingLedger,
  getPlatingLedger,
  getPlatingLedgerOptions,
  refreshPlatingLedgerMaster,
  updatePlatingLedger,
  type PlatingLedgerOption,
  type PlatingLedgerRow,
} from '@/api/outsourcing'
import { usePurchaseOperationPermission } from '@/composables/usePurchaseOperationPermission'
import { notifyLedgerError } from './ledgerError'
import PlatingHistoryPanel from './PlatingHistoryPanel.vue'
import PlatingOrderSheetIssuer from './PlatingOrderSheetIssuer.vue'
import PlatingStockPanel from './PlatingStockPanel.vue'

const { canCreate, canEdit } = usePurchaseOperationPermission()

const router = useRouter()

function openPage(name: 'OutsourcingSuppliers' | 'OutsourcingProcessProducts') {
  void router.push({ name })
}

type QtyField = 'order_qty' | 'receiving_qty' | 'defect_qty' | 'initial_stock'

function monthRange(base: Date = new Date()): [string, string] {
  const y = base.getFullYear()
  const m = String(base.getMonth() + 1).padStart(2, '0')
  const last = new Date(y, base.getMonth() + 1, 0).getDate()
  return [`${y}-${m}-01`, `${y}-${m}-${String(last).padStart(2, '0')}`]
}

function toYmd(d: Date): string {
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${m}-${day}`
}

const dateRange = ref<[string, string]>([toYmd(new Date()), toYmd(new Date())])

const isToday = computed(() => {
  const today = toYmd(new Date())
  return dateRange.value[0] === today && dateRange.value[1] === today
})

function shiftDay(offset: number) {
  const [y, m, d] = (dateRange.value?.[0] || toYmd(new Date())).split('-').map(Number)
  const next = toYmd(new Date(y, m - 1, d + offset))
  dateRange.value = [next, next]
}

function setToday() {
  const today = toYmd(new Date())
  dateRange.value = [today, today]
}

const isCurrentMonth = computed(() => {
  const [start, end] = monthRange()
  return dateRange.value[0] === start && dateRange.value[1] === end
})

function shiftMonth(offset: number) {
  const [y, m] = (dateRange.value?.[0] || monthRange()[0]).split('-').map(Number)
  dateRange.value = monthRange(new Date(y, m - 1 + offset, 1))
}

function setCurrentMonth() {
  dateRange.value = monthRange()
}
const activeTab = ref<
  'ledger' | 'order' | 'receiving' | 'initial' | 'orderHistory' | 'receivingHistory' | 'stock'
>('ledger')
// 台帳（表示のみ）・外注注文（注文数を入力）・外注受入（受入数・不良数を入力）は同じ台帳データ・同じ表
const isLedgerTable = computed(() =>
  ['ledger', 'order', 'receiving'].includes(activeTab.value),
)
const isHistoryTab = computed(
  () => activeTab.value === 'orderHistory' || activeTab.value === 'receivingHistory',
)
// 独自に読み込むパネル系タブ（台帳のページングを使わない）
const isPanelTab = computed(() => isHistoryTab.value || activeTab.value === 'stock')
const stockAsOf = ref(toYmd(new Date()))
const historyView = ref<'list' | 'pivot'>('list')
const initialMonth = ref(monthRange()[0].slice(0, 7))
const supplierCd = ref('')
const productCd = ref('')
const filterOptions = ref<PlatingLedgerOption[]>([])
const rows = ref<PlatingLedgerRow[]>([])
const loading = ref(false)
const generating = ref(false)
const calculating = ref(false)
const tableWrapRef = ref<HTMLElement | null>(null)
const page = ref(1)
const pageSize = ref(100)
const total = ref(0)

const generateVisible = ref(false)
const genStart = ref('')
const genEnd = ref('')

const refreshVisible = ref(false)
const refreshing = ref(false)
const refreshStart = ref('')
const refreshEnd = ref('')
const refreshIncludeOrdered = ref(false)

// 数量のある行だけ表示（外注注文・外注受入のみ。台帳は常に全行）
const onlyNonZero = ref(false)
const nonZeroParam = computed<'order' | 'receiving' | undefined>(() => {
  if (!onlyNonZero.value) return undefined
  if (activeTab.value === 'order') return 'order'
  if (activeTab.value === 'receiving') return 'receiving'
  return undefined
})
const nonZeroHint = computed(() =>
  activeTab.value === 'order' ? '注文数のある行' : '受入数・不良数のある行',
)

function emptyIfZero(value: number | null | undefined): number | null {
  if (value == null || value === 0) return null
  return value
}

function blankIfZero(value: number | null | undefined): string {
  return value ? Number(value).toLocaleString() : ''
}

function formatNum(value: number | null | undefined): string {
  const n = Number(value || 0)
  return n.toLocaleString()
}

function formatMonth(ymd: string | null | undefined): string {
  if (!ymd) return ''
  const [y, m] = ymd.split('-')
  return `${y}年${Number(m)}月`
}

const WEEKDAYS = ['日', '月', '火', '水', '木', '金', '土']

function dayOfWeek(ymd: string | null | undefined): number {
  if (!ymd) return -1
  const [y, m, d] = ymd.split('-').map(Number)
  return new Date(y, m - 1, d).getDay()
}

function weekdayLabel(ymd: string | null | undefined): string {
  const wd = dayOfWeek(ymd)
  return wd < 0 ? '' : `(${WEEKDAYS[wd]})`
}

function weekendClass(ymd: string | null | undefined): string {
  const wd = dayOfWeek(ymd)
  if (wd === 0) return 'is-sun'
  if (wd === 6) return 'is-sat'
  return ''
}

function stockClass(value: number | null | undefined): string {
  const n = Number(value || 0)
  if (n < 0) return 'is-neg'
  if (n === 0) return 'is-zero'
  return 'is-pos'
}

// 受入数＋不良数の出庫で外注先在庫がマイナスになった行
function isOverStock(row: PlatingLedgerRow): boolean {
  return (row.current_stock || 0) < 0 && (row.receiving_qty || 0) + (row.defect_qty || 0) > 0
}

function applyAffected(affected: PlatingLedgerRow[]) {
  const byId = new Map(affected.map((r) => [r.id, r]))
  rows.value = rows.value.map((row) => {
    const fresh = byId.get(row.id)
    if (!fresh) return row
    const merged = { ...fresh }
    for (const edit of pendingEdits.values()) {
      if (edit.id === row.id) merged[edit.field] = edit.value
    }
    return merged
  })
}

const supplierOptions = computed(() => {
  const source = productCd.value
    ? filterOptions.value.filter((o) => o.product_cd === productCd.value)
    : filterOptions.value
  const map = new Map<string, string>()
  for (const o of source) {
    if (!map.has(o.supplier_cd)) map.set(o.supplier_cd, o.supplier_name || o.supplier_cd)
  }
  return [...map.entries()]
    .map(([value, label]) => ({ value, label }))
    .sort((a, b) => a.label.localeCompare(b.label, 'ja'))
})

const productOptions = computed(() => {
  const source = supplierCd.value
    ? filterOptions.value.filter((o) => o.supplier_cd === supplierCd.value)
    : filterOptions.value
  const map = new Map<string, string>()
  for (const o of source) {
    if (!map.has(o.product_cd)) map.set(o.product_cd, o.product_name || o.product_cd)
  }
  return [...map.entries()]
    .map(([value, name]) => ({ value, name, label: `${name}（${value}）` }))
    .sort((a, b) => a.name.localeCompare(b.name, 'ja'))
})

async function loadFilterOptions() {
  try {
    const res = await getPlatingLedgerOptions()
    filterOptions.value = Array.isArray(res?.data) ? res.data : []
  } catch {
    filterOptions.value = []
  }
}

let loadSeq = 0

async function load() {
  if (isPanelTab.value) return
  const isInitial = activeTab.value === 'initial'
  if (isInitial ? !initialMonth.value : !dateRange.value || dateRange.value.length !== 2) return
  const [startDate, endDate] = isInitial
    ? [`${initialMonth.value}-01`, `${initialMonth.value}-01`]
    : dateRange.value
  const seq = ++loadSeq
  loading.value = true
  try {
    const res = await getPlatingLedger({
      startDate,
      endDate,
      supplierCd: supplierCd.value || undefined,
      productCd: productCd.value || undefined,
      firstDayOnly: isInitial || undefined,
      nonZero: isInitial ? undefined : nonZeroParam.value,
      page: page.value,
      pageSize: pageSize.value,
    })
    if (seq !== loadSeq) return
    rows.value = res?.data || []
    total.value = res?.total || 0
  } catch (error: any) {
    if (seq !== loadSeq) return
    notifyLedgerError(error, '取得に失敗しました')
    rows.value = []
    total.value = 0
  } finally {
    if (seq === loadSeq) loading.value = false
  }
}

function search() {
  page.value = 1
  void load()
}

watch(supplierCd, () => {
  if (productCd.value && !productOptions.value.some((p) => p.value === productCd.value)) {
    productCd.value = ''
    return
  }
  search()
})

watch(productCd, search)

watch(dateRange, search, { deep: true })

const LEDGER_TABS = ['ledger', 'order', 'receiving']

// 台帳・外注注文・外注受入は同じデータなので、絞り込みが無ければタブ切替で再取得しない
watch(activeTab, (tab, prev) => {
  if (LEDGER_TABS.includes(tab) && LEDGER_TABS.includes(prev) && !onlyNonZero.value) return
  search()
})

watch(onlyNonZero, search)

watch(initialMonth, () => {
  if (activeTab.value === 'initial') search()
})

function openGenerate() {
  genStart.value = dateRange.value?.[0] || ''
  genEnd.value = dateRange.value?.[1] || ''
  generateVisible.value = true
}

async function runGenerate() {
  if (!genStart.value || !genEnd.value) return
  generating.value = true
  try {
    const res = await generatePlatingLedger(genStart.value, genEnd.value)
    const data = res?.data
    ElMessage.success(`生成 ${data?.generated_count ?? 0} 件、スキップ ${data?.skipped_count ?? 0} 件`)
    generateVisible.value = false
    void loadFilterOptions()
    const sameRange = dateRange.value[0] === genStart.value && dateRange.value[1] === genEnd.value
    dateRange.value = [genStart.value, genEnd.value]
    if (sameRange) search()
  } catch (error: any) {
    notifyLedgerError(error, '生成に失敗しました')
  } finally {
    generating.value = false
  }
}

function openRefreshMaster() {
  refreshStart.value = dateRange.value?.[0] || ''
  refreshEnd.value = dateRange.value?.[1] || ''
  refreshIncludeOrdered.value = false
  refreshVisible.value = true
}

async function runRefreshMaster() {
  if (!refreshStart.value || !refreshEnd.value) return
  refreshing.value = true
  try {
    const res = await refreshPlatingLedgerMaster({
      start_date: refreshStart.value,
      end_date: refreshEnd.value,
      supplier_cd: supplierCd.value || undefined,
      product_cd: productCd.value || undefined,
      include_ordered: refreshIncludeOrdered.value,
    })
    const data = res?.data
    const missing = data?.missing_count ? `、マスタ無し ${data.missing_count} 件` : ''
    ElMessage.success(`マスタを反映しました（更新 ${data?.updated_count ?? 0} 件${missing}）`)
    refreshVisible.value = false
    await load()
  } catch (error: any) {
    notifyLedgerError(error, 'マスタ反映に失敗しました')
  } finally {
    refreshing.value = false
  }
}

async function runCalculate() {
  calculating.value = true
  try {
    const res = await calculatePlatingLedger()
    ElMessage.success(`在庫を再計算しました（変更 ${res?.data?.calculated_count ?? 0} 行）`)
    await load()
  } catch (error: any) {
    notifyLedgerError(error, '在庫計算に失敗しました')
  } finally {
    calculating.value = false
  }
}

// 保存は順番に実行し、未送信の入力値はレスポンス反映時に上書きしない
let saveChain: Promise<void> = Promise.resolve()
const pendingEdits = new Map<string, { id: number; field: QtyField; value: number }>()

function saveField(row: PlatingLedgerRow, field: QtyField, val: number | null | undefined) {
  const next = val == null ? 0 : Number(val)
  if (next === (row[field] || 0)) return
  const id = row.id
  const prev = row[field]
  const key = `${id}:${field}`
  row[field] = next
  pendingEdits.set(key, { id, field, value: next })
  saveChain = saveChain.then(async () => {
    try {
      const res = await updatePlatingLedger(id, { [field]: next })
      if (pendingEdits.get(key)?.value === next) pendingEdits.delete(key)
      // affected は現在庫が変わった行のみなので、保存した行自体も反映する
      const saved = res?.data?.row
      applyAffected([...(saved ? [saved] : []), ...(res?.data?.affected || [])])
      if (
        saved &&
        (field === 'receiving_qty' || field === 'defect_qty') &&
        next > 0 &&
        saved.current_stock < 0
      ) {
        ElMessage.warning(
          `受入数＋不良数が外注先の在庫を超えています（${saved.order_date} ${saved.product_name}：現在庫 ${saved.current_stock.toLocaleString()}）`,
        )
      }
    } catch (error: any) {
      if (pendingEdits.get(key)?.value === next) {
        pendingEdits.delete(key)
        const current = rows.value.find((r) => r.id === id)
        if (current) current[field] = prev
      }
      notifyLedgerError(error, '保存に失敗しました')
    }
  })
}

const NAV_KEYS = ['Enter', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight']

function focusCell(rowIndex: number, col: number): boolean {
  const input = tableWrapRef.value?.querySelector<HTMLInputElement>(
    `[data-nav-row="${rowIndex}"][data-nav-col="${col}"] input`,
  )
  if (!input || input.disabled) return false
  input.focus()
  input.select()
  input.scrollIntoView({ block: 'nearest', inline: 'nearest' })
  return true
}

function onCellKeydown(e: KeyboardEvent, rowIndex: number, col: number) {
  if (!NAV_KEYS.includes(e.key) || e.isComposing) return
  const input = e.target as HTMLInputElement
  const len = input.value.length
  const start = input.selectionStart ?? 0
  const end = input.selectionEnd ?? 0
  const allSelected = start === 0 && end === len
  if (e.key === 'ArrowLeft' && !allSelected && !(start === 0 && end === 0)) return
  if (e.key === 'ArrowRight' && !allSelected && !(start === len && end === len)) return
  // input-number 本体の上下キー増減を止める
  e.preventDefault()
  e.stopPropagation()
  if (e.key === 'Enter') {
    const target = e.shiftKey ? rowIndex - 1 : rowIndex + 1
    if (!focusCell(target, col)) input.blur()
    return
  }
  if (e.key === 'ArrowUp') focusCell(rowIndex - 1, col)
  else if (e.key === 'ArrowDown') focusCell(rowIndex + 1, col)
  else if (e.key === 'ArrowLeft') focusCell(rowIndex, col - 1)
  else focusCell(rowIndex, col + 1)
}

onMounted(() => {
  void loadFilterOptions()
  void load()
})
</script>

<style scoped>
.plating-ledger-page {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 12px 14px;
  box-sizing: border-box;
  min-height: 100%;
  background: linear-gradient(180deg, #e6f7f6 0%, #f8fafc 30%, #f8fafc 100%);
}

/* ============================================================ */
/* 页面美化：现代 UI / 颜色区分（外注メッキ＝ティール〜ブルー系）    */
/* ============================================================ */

/* ---------- ヒーロー ---------- */
.page-header {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  border-radius: 14px;
  color: #fff;
  background: linear-gradient(125deg, #0f766e 0%, #0d9488 34%, #0891b2 66%, #2563eb 100%);
  box-shadow:
    0 12px 28px -18px rgba(13, 148, 136, 0.7),
    0 1px 2px rgba(15, 23, 42, 0.06);
}

.header-left {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  font-size: 20px;
  color: #fff;
  background: linear-gradient(150deg, rgba(255, 255, 255, 0.36), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.42);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(19, 78, 74, 0.3);
}

.title-text {
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.title {
  margin: 0;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: #fff;
}

.subtitle {
  margin: 0;
  letter-spacing: 0.02em;
  color: rgba(255, 255, 255, 0.88);
}

.header-actions {
  flex-shrink: 0;
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

/* ヒーロー上の白ピル（文字色で役割を区別） */
.head-btn {
  --hb-fg: #047857;
  --hb-fg-h: #065f46;
  --hb-bg: #ecfdf5;
  height: 30px;
  margin: 0;
  padding: 0 14px;
  border-radius: 999px;
  font-weight: 700;
  color: var(--hb-fg);
  border: 1px solid rgba(255, 255, 255, 0.9);
  background: linear-gradient(180deg, #ffffff 0%, var(--hb-bg) 100%);
}

.head-btn:not(.is-disabled):hover,
.head-btn:focus-visible {
  color: var(--hb-fg-h);
  border-color: #fff;
  background: #fff;
}

.head-btn .el-icon {
  margin-right: 4px;
}

.head-btn--gen {
  --k-rgb: 5 150 105;
}

/* 関連マスタへのリンク（半透明で操作ボタンと区別） */
.head-btn--link {
  color: #fff;
  border-color: rgba(255, 255, 255, 0.45);
  background: rgba(255, 255, 255, 0.14);
}

.head-btn--link:not(.is-disabled):hover,
.head-btn--link:focus-visible {
  color: #0f766e;
  border-color: #fff;
  background: #fff;
}

.head-divider {
  align-self: center;
  width: 1px;
  height: 20px;
  margin: 0 2px;
  background: rgba(255, 255, 255, 0.4);
}

.head-btn--master {
  --k-rgb: 37 99 235;
  --hb-fg: #1d4ed8;
  --hb-fg-h: #1e40af;
  --hb-bg: #eff6ff;
}

.head-btn--calc {
  --k-rgb: 217 119 6;
  --hb-fg: #b45309;
  --hb-fg-h: #92400e;
  --hb-bg: #fffbeb;
}

.head-btn.is-disabled {
  color: #94a3b8;
  border-color: #d1d5db;
  background: #e5e7eb;
}

/* ---------- 絞り込みカード ---------- */
.filter-card {
  position: relative;
  overflow: hidden;
  padding: 12px 16px 10px;
  border-radius: 12px;
  border: 1px solid #ccebe8;
  background: linear-gradient(180deg, #ffffff 0%, #f6fcfb 100%);
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 10px 24px -20px rgba(15, 118, 110, 0.45);
}

.filter-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #0d9488 0%, #0891b2 55%, #3b82f6 100%);
}

.filter-fields {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px 20px;
}

.filter-field {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-field .filter-control {
  width: 190px;
}

.filter-field--date .filter-control,
.filter-field--product .filter-control {
  width: 260px;
}

.filter-label {
  flex-shrink: 0;
  height: 22px;
  padding: 0 10px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
  color: #115e59;
  background: #e6f7f5;
  box-shadow:
    inset 0 1px 0 #ffffff,
    inset 0 -1px 0 #99e0d8;
}

.filter-label .el-icon {
  color: #0d9488;
}

/* 入力枠：枠線は wrapper の内側リングのみ（二重線にしない） */
.filter-control :deep(.el-input__wrapper),
.filter-control :deep(.el-select__wrapper) {
  border-radius: 8px;
  background-color: #fff;
  box-shadow: 0 0 0 1px #cfe6e3 inset;
  transition: box-shadow 0.2s ease;
}

.filter-control :deep(.el-input__wrapper:hover),
.filter-control :deep(.el-select__wrapper:hover) {
  box-shadow: 0 0 0 1px #7dd3c8 inset;
}

.filter-control :deep(.el-input__wrapper.is-focus),
.filter-control :deep(.el-select__wrapper.is-focused) {
  box-shadow:
    0 0 0 1px #0d9488 inset,
    0 0 0 3px rgba(13, 148, 136, 0.14);
}

.filter-control.el-range-editor {
  border-radius: 8px;
  box-shadow: 0 0 0 1px #cfe6e3 inset;
}

.filter-control.el-range-editor:hover {
  box-shadow: 0 0 0 1px #7dd3c8 inset;
}

.filter-control.el-range-editor.is-active {
  box-shadow:
    0 0 0 1px #0d9488 inset,
    0 0 0 3px rgba(13, 148, 136, 0.14);
}

/* 月ショートカット：セグメント */
.month-shortcuts {
  display: inline-flex;
  gap: 2px;
  padding: 2px;
  border-radius: 10px;
  background: #e6f4f2;
  box-shadow: inset 0 1px 2px rgba(15, 118, 110, 0.1);
}

.month-shortcuts .month-btn {
  --k-rgb: 13 148 136;
  height: 28px;
  margin: 0;
  padding: 0 10px;
  border-radius: 8px !important;
  font-weight: 700;
  color: #0f766e;
  border: 1px solid #cdeae6 !important;
  background: linear-gradient(180deg, #ffffff 0%, #f3fbfa 100%);
}

.month-shortcuts .month-btn:hover,
.month-shortcuts .month-btn:focus-visible {
  color: #115e59;
  border-color: #7dd3c8 !important;
  background: #fff;
}

.month-shortcuts .month-btn.is-active {
  color: #fff;
  border-color: #0f766e !important;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #14b8a6, #0f766e);
}

.month-shortcuts .month-btn.is-active:hover,
.month-shortcuts .month-btn.is-active:focus-visible {
  color: #fff;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.26) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #2dd4bf, #0d9488);
}

.nonzero-switch {
  --el-switch-on-color: #0d9488;
  --el-switch-off-color: #cbd5e1;
}

.nonzero-hint {
  font-size: 12px;
  color: #64748b;
  white-space: nowrap;
}

.product-option {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.product-option__name {
  overflow: hidden;
  text-overflow: ellipsis;
}

.product-option__cd {
  flex-shrink: 0;
  font-size: 12px;
  color: #909399;
}

/* ---------- テーブル ---------- */
.table-wrap {
  /* タブごとのアクセント色 */
  --accent: #0d9488;
  --accent-2: #0891b2;
  --accent-deep: #0f766e;
  --accent-soft: #e6f7f5;
  --accent-ring: rgba(13, 148, 136, 0.18);
  position: relative;
  overflow: hidden;
  padding: 10px 10px 8px;
  border-radius: 14px;
  border: 1px solid #dbe7ef;
  background: #fff;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 14px 30px -24px rgba(15, 23, 42, 0.35);
  transition: border-color 0.25s ease;
}

.table-wrap.tab-initial {
  --accent: #d97706;
  --accent-2: #f59e0b;
  --accent-deep: #b45309;
  --accent-soft: #fff7e6;
  --accent-ring: rgba(217, 119, 6, 0.18);
}

.table-wrap.tab-orderHistory {
  --accent: #4f46e5;
  --accent-2: #6366f1;
  --accent-deep: #3730a3;
  --accent-soft: #eef2ff;
  --accent-ring: rgba(79, 70, 229, 0.18);
}

.table-wrap.tab-receivingHistory {
  --accent: #059669;
  --accent-2: #10b981;
  --accent-deep: #047857;
  --accent-soft: #ecfdf5;
  --accent-ring: rgba(5, 150, 105, 0.18);
}

.table-wrap.tab-order {
  --accent: #2563eb;
  --accent-2: #3b82f6;
  --accent-deep: #1d4ed8;
  --accent-soft: #eff6ff;
  --accent-ring: rgba(37, 99, 235, 0.18);
}

.table-wrap.tab-receiving {
  --accent: #0891b2;
  --accent-2: #06b6d4;
  --accent-deep: #0e7490;
  --accent-soft: #ecfeff;
  --accent-ring: rgba(8, 145, 178, 0.18);
}

.table-wrap.tab-stock {
  --accent: #7c3aed;
  --accent-2: #8b5cf6;
  --accent-deep: #6d28d9;
  --accent-soft: #f5f3ff;
  --accent-ring: rgba(124, 58, 237, 0.18);
}

.table-wrap::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 5;
  height: 3px;
  background: linear-gradient(90deg, var(--accent) 0%, var(--accent-2) 60%, #60a5fa 100%);
  transition: background 0.25s ease;
}

.table-wrap :deep(.el-table) {
  border-radius: 10px;
  --el-table-border-color: #e6edf3;
  --el-table-row-hover-bg-color: #f1f7fb;
}

.table-wrap :deep(th.el-table__cell) {
  font-weight: 700 !important;
  color: #334155 !important;
  background: #f5f8fb !important;
  border-bottom: 1px solid #dbe4ec !important;
}

.table-wrap :deep(td.el-table__cell) {
  color: #1e293b;
}

/* セル内は折り返さない */
.table-wrap :deep(.el-table .cell) {
  white-space: nowrap;
  word-break: keep-all;
}

.table-wrap :deep(.el-table__row--striped td.el-table__cell) {
  background: #fbfcfe;
}

/* 列グループの色分け：注文=インディゴ / 受入=エメラルド / 不良=ローズ / 初期在庫=アンバー / 現在庫=バイオレット */
.table-wrap :deep(.el-table__header th.col-order) {
  color: #3730a3 !important;
  background: #eef2ff !important;
  box-shadow: inset 0 3px 0 #818cf8;
}

.table-wrap :deep(.el-table__header th.col-recv) {
  color: #047857 !important;
  background: #ecfdf5 !important;
  box-shadow: inset 0 3px 0 #34d399;
}

.table-wrap :deep(.el-table__header th.col-defect) {
  color: #be123c !important;
  background: #fff1f2 !important;
  box-shadow: inset 0 3px 0 #fb7185;
}

.table-wrap :deep(.el-table__header th.col-initial) {
  color: #b45309 !important;
  background: #fffbeb !important;
  box-shadow: inset 0 3px 0 #fbbf24;
}

.table-wrap :deep(.el-table__header th.col-stock) {
  color: #6d28d9 !important;
  background: #f5f3ff !important;
  box-shadow: inset 0 3px 0 #a78bfa;
}

.table-wrap :deep(.el-table__body td.col-order) {
  background: #fafbff;
}

.table-wrap :deep(.el-table__body td.col-recv) {
  background: #f7fdfa;
}

.table-wrap :deep(.el-table__body td.col-defect) {
  background: #fffafa;
}

.table-wrap :deep(.el-table__body td.col-initial) {
  background: #fffdf6;
}

.table-wrap :deep(.el-table__body td.col-stock) {
  background: #fbfaff;
}

.table-wrap :deep(td.col-code .cell) {
  font-family: ui-monospace, 'SFMono-Regular', Consolas, monospace;
  font-size: 12px;
  color: #475569;
}

.table-wrap :deep(.el-table__body tr:hover > td.el-table__cell) {
  background-color: #eef5fb !important;
}

/* 合計行 */
.table-wrap :deep(.el-table__footer-wrapper td.el-table__cell) {
  font-weight: 800;
  color: var(--accent-deep);
  background: var(--accent-soft) !important;
  border-top: 2px solid var(--accent-2);
}

/* セル内の表示部品 */
.date-cell {
  display: inline-flex;
  align-items: baseline;
  gap: 3px;
  font-variant-numeric: tabular-nums;
  color: #334155;
}

.date-cell small {
  font-size: 11px;
  color: #94a3b8;
}

.date-cell.is-sat,
.date-cell.is-sat small {
  color: #2563eb;
}

.date-cell.is-sun,
.date-cell.is-sun small {
  color: #dc2626;
}

.num-muted {
  color: #64748b;
  font-variant-numeric: tabular-nums;
}

.num-strong {
  font-weight: 700;
  color: #3730a3;
  font-variant-numeric: tabular-nums;
}

/* 台帳（表示のみ）の数量 */
.qty-view {
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.qty-view--order {
  color: #3730a3;
}

.qty-view--recv {
  color: #047857;
}

.qty-view--defect {
  color: #be123c;
}

.no-chip {
  display: inline-block;
  max-width: 100%;
  padding: 1px 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: middle;
  border-radius: 6px;
  font-family: ui-monospace, 'SFMono-Regular', Consolas, monospace;
  font-size: 11.5px;
  font-weight: 600;
}

.no-chip--order {
  color: #3730a3;
  background: #e0e7ff;
  border: 1px solid #c7d2fe;
}

.issue-tag {
  display: inline-block;
  padding: 0 8px;
  border-radius: 999px;
  font-size: 11.5px;
  font-weight: 700;
  line-height: 20px;
}

.issue-tag--done {
  color: #047857;
  background: #d1fae5;
  border: 1px solid #a7f3d0;
  cursor: default;
}

.issue-tag--todo {
  color: #b45309;
  background: #fef3c7;
  border: 1px solid #fde68a;
}

.month-chip {
  display: inline-block;
  padding: 1px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  color: #b45309;
  background: #fef3c7;
  border: 1px solid #fde68a;
}

.stock-badge {
  display: inline-block;
  min-width: 44px;
  padding: 1px 8px;
  border-radius: 999px;
  text-align: right;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.stock-badge.is-pos {
  color: #5b21b6;
  background: #ede9fe;
}

.stock-badge.is-zero {
  color: #94a3b8;
  background: #f1f5f9;
}

.stock-badge.is-neg {
  color: #be123c;
  background: #ffe4e6;
}

/* 入力セル：枠を淡く、フォーカスで強調 */
.qty-input {
  width: 88px;
}

/* 項目ごとの入力色（列グループと同系色） */
.qty-input {
  --qi-bg: #fffdf5;
  --qi-line: #f3e2b3;
  --qi-hover: #e9c46a;
  --qi-focus: #d97706;
  --qi-ring: rgba(217, 119, 6, 0.16);
}

.qty-input--order {
  --qi-bg: #f8f9ff;
  --qi-line: #c7d2fe;
  --qi-hover: #818cf8;
  --qi-focus: #4f46e5;
  --qi-ring: rgba(79, 70, 229, 0.16);
}

.qty-input--recv {
  --qi-bg: #f4fdf8;
  --qi-line: #a7f3d0;
  --qi-hover: #34d399;
  --qi-focus: #059669;
  --qi-ring: rgba(5, 150, 105, 0.16);
}

.qty-input--defect {
  --qi-bg: #fff8f8;
  --qi-line: #fecdd3;
  --qi-hover: #fb7185;
  --qi-focus: #e11d48;
  --qi-ring: rgba(225, 29, 72, 0.16);
}

.qty-input :deep(.el-input__wrapper) {
  border-radius: 7px;
  background-color: var(--qi-bg);
  box-shadow: 0 0 0 1px var(--qi-line) inset;
  transition:
    box-shadow 0.15s ease,
    background-color 0.15s ease;
}

.qty-input :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--qi-hover) inset;
}

.qty-input :deep(.el-input__wrapper.is-focus) {
  background-color: #fff;
  box-shadow:
    0 0 0 1.5px var(--qi-focus) inset,
    0 0 0 3px var(--qi-ring);
}

.qty-input--defect :deep(.el-input__inner) {
  color: #be123c;
}

.qty-input :deep(.el-input__inner) {
  font-weight: 700;
  color: #1e293b;
  font-variant-numeric: tabular-nums;
}

/* 外注先在庫を超える受入・不良 */
.qty-input.is-over :deep(.el-input__wrapper) {
  background-color: #fff1f2;
  box-shadow:
    0 0 0 1.5px #f43f5e inset,
    0 0 0 3px rgba(244, 63, 94, 0.14);
}

.qty-input.is-disabled :deep(.el-input__wrapper) {
  background-color: #f1f5f9;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
}

/* ---------- タブ ---------- */
.ledger-tabs {
  margin-bottom: 6px;
}

.ledger-tabs :deep(.el-tabs__header) {
  margin: 0;
}

.ledger-tabs :deep(.el-tabs__nav-wrap::after) {
  height: 1px;
  background-color: #e2e8f0;
}

.ledger-tabs :deep(.el-tabs__item) {
  height: 38px;
  padding: 0 6px !important;
  font-weight: 600;
  color: #64748b;
}

.ledger-tabs :deep(.el-tabs__item:first-child) {
  padding-left: 0 !important;
}

.ledger-tabs :deep(.el-tabs__active-bar) {
  height: 3px;
  border-radius: 3px;
  background: linear-gradient(90deg, var(--accent) 0%, var(--accent-2) 100%);
}

/* タブラベル：タブごとの色。選択中は同系色のピル */
.ledger-tab-label {
  --tl: #0d9488;
  --tl-soft: #e6f7f5;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 28px;
  padding: 0 12px;
  border-radius: 8px;
  transition:
    background-color 0.2s ease,
    color 0.2s ease;
}

.ledger-tab-label .el-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 6px;
  font-size: 13px;
  color: var(--tl);
  background: var(--tl-soft);
}

.ledger-tab-label--initial {
  --tl: #d97706;
  --tl-soft: #fff1d6;
}

.ledger-tab-label--order {
  --tl: #4f46e5;
  --tl-soft: #e0e7ff;
}

.ledger-tab-label--recv {
  --tl: #059669;
  --tl-soft: #d1fae5;
}

.ledger-tab-label--outorder {
  --tl: #2563eb;
  --tl-soft: #dbeafe;
}

.ledger-tab-label--outrecv {
  --tl: #0891b2;
  --tl-soft: #cffafe;
}

.ledger-tab-label--stock {
  --tl: #7c3aed;
  --tl-soft: #ede9fe;
}

.ledger-tabs :deep(.el-tabs__item:hover) .ledger-tab-label {
  color: var(--tl);
  background: #f8fafc;
}

.ledger-tabs :deep(.el-tabs__item.is-active) .ledger-tab-label {
  color: var(--tl);
  font-weight: 700;
  background: var(--tl-soft);
}

.ledger-tabs :deep(.el-tabs__item.is-active) .ledger-tab-label .el-icon {
  color: #fff;
  background: var(--tl);
  box-shadow: 0 3px 8px -3px var(--tl);
}

.tabs-row {
  position: relative;
}

.initial-bar {
  position: absolute;
  top: 0;
  right: 4px;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 8px;
  height: 36px;
}

.view-switch {
  padding: 2px;
  border-radius: 9px;
  background: var(--accent-soft);
}

.view-switch :deep(.el-radio-button__inner) {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 26px;
  padding: 0 12px;
  border: none !important;
  border-radius: 7px !important;
  font-weight: 600;
  color: var(--accent-deep);
  background: transparent;
  box-shadow: none !important;
}

.view-switch :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  color: #fff;
  background: linear-gradient(135deg, var(--accent-2), var(--accent));
  box-shadow: 0 4px 10px -5px var(--accent) !important;
}

.initial-bar .filter-label {
  color: var(--accent-deep);
  background: var(--accent-soft);
  box-shadow: inset 0 -1px 0 var(--accent-ring);
}

.initial-bar .filter-label .el-icon {
  color: var(--accent);
}

.initial-bar .initial-month {
  width: 140px;
}

/* ---------- ページャー ---------- */
.pager {
  display: flex;
  justify-content: flex-end;
  padding: 8px 4px 0;
}

.pager :deep(.el-pagination__total) {
  font-weight: 700;
  color: #115e59;
}

.pager :deep(.el-pager li),
.pager :deep(.btn-prev),
.pager :deep(.btn-next) {
  min-width: 26px;
  height: 26px;
  margin: 0 2px;
  border-radius: 7px;
  color: #0f766e;
  border: 1px solid #ccebe8;
  background: linear-gradient(180deg, #ffffff 0%, #f3fbfa 100%);
}

.pager :deep(.el-pager li:not(.is-active):hover) {
  border-color: #7dd3c8;
  background: #fff;
}

.pager :deep(.el-pager li.is-active) {
  color: #fff;
  border-color: #0f766e;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #14b8a6, #0f766e);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(19, 78, 74, 0.35),
    0 4px 10px -6px rgba(13, 148, 136, 0.7);
}

.pager :deep(.btn-prev:disabled),
.pager :deep(.btn-next:disabled) {
  color: #94a3b8;
  border-color: #d1d5db;
  background: #e5e7eb;
}

/* ---------- データ生成ダイアログ ---------- */
.gen-hero {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  background: linear-gradient(125deg, #0f766e 0%, #0d9488 34%, #0891b2 66%, #2563eb 100%);
}

.gen-hero__icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 11px;
  font-size: 18px;
  color: #fff;
  background: linear-gradient(150deg, rgba(255, 255, 255, 0.36), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.42);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(19, 78, 74, 0.3);
}

.gen-hero__copy {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.gen-hero__title {
  font-size: 16px;
  font-weight: 800;
  line-height: 1.3;
  letter-spacing: 0.03em;
  color: #fff;
}

.gen-hero__desc {
  margin: 0;
  font-size: 11px;
  line-height: 1.5;
  color: rgba(255, 255, 255, 0.88);
}

.gen-hero__close {
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

.gen-hero__close:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

:global(.el-dialog.pll-dialog) {
  padding: 0;
  overflow: hidden;
  border-radius: 14px;
}

:global(.el-dialog.pll-dialog .el-dialog__header) {
  padding: 0;
  margin: 0;
}

:global(.el-dialog.pll-dialog .el-dialog__body) {
  padding: 16px 18px 12px;
}

:global(.el-dialog.pll-dialog .el-dialog__footer) {
  padding: 10px 18px 14px;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
}

.gen-form :deep(.el-form-item__label) {
  font-weight: 700;
  color: #115e59;
}

.gen-form :deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 0 0 1px #cfe6e3 inset;
}

.gen-form :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #7dd3c8 inset;
}

.gen-form :deep(.el-input__wrapper.is-focus) {
  box-shadow:
    0 0 0 1px #0d9488 inset,
    0 0 0 3px rgba(13, 148, 136, 0.14);
}

.gen-notes {
  position: relative;
  margin: 4px 0 0;
  padding: 10px 12px 10px 30px;
  overflow: hidden;
  border-radius: 10px;
  font-size: 12.5px;
  line-height: 1.7;
  color: #334155;
  border: 1px solid #ccebe8;
  background: linear-gradient(180deg, #f6fcfb 0%, #eef9f7 100%);
}

.gen-notes::before {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 3px;
  background: linear-gradient(180deg, #5eead4, #0d9488);
}

.gen-notes li::marker {
  color: #0d9488;
}

.dlg-btn {
  --k-rgb: 100 116 139;
  min-width: 88px;
  height: 32px;
  border-radius: 8px;
  font-weight: 700;
  color: #475569;
  border: 1px solid #cbd5e1;
  background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%);
}

.dlg-btn:hover,
.dlg-btn:focus-visible {
  color: #334155;
  border-color: #94a3b8;
  background: #fff;
}

.dlg-btn--run {
  --k-rgb: 13 148 136;
  color: #fff;
  border-color: #0f766e;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #14b8a6, #0f766e);
}

.dlg-btn--run:hover,
.dlg-btn--run:focus-visible {
  color: #fff;
  border-color: #115e59;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.26) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #2dd4bf, #0d9488);
}

.dlg-btn--run.is-disabled,
.dlg-btn--run.is-disabled:hover {
  color: #94a3b8;
  border-color: #d1d5db;
  background: #e5e7eb;
}

/* ---------- レスポンシブ ---------- */
@media (max-width: 900px) {
  .page-header {
    flex-wrap: wrap;
  }

  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .filter-field,
  .filter-field .filter-control,
  .filter-field--date .filter-control,
  .filter-field--product .filter-control {
    width: 100%;
  }

  .filter-field--date {
    flex-wrap: wrap;
  }
}
</style>
