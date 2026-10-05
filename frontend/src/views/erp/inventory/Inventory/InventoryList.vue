<template>
  <div class="inventory-list-page il-modern pb-std">
    <div class="page-bg">
      <div class="bg-gradient"></div>
      <div class="bg-orb bg-orb-1"></div>
      <div class="bg-orb bg-orb-2"></div>
      <div class="bg-orb bg-orb-3"></div>
    </div>

    <div class="page-header glass pb-hero pb-hero--page">
      <div class="header-fx pb-bubbles" aria-hidden="true" />
      <div class="header-left">
        <div class="header-icon">
          <el-icon size="24"><List /></el-icon>
        </div>
        <div class="header-text">
          <h1 class="header-title pb-hero-title">仕掛品・製品在庫照会</h1>
          <div class="header-chips">
            <span class="header-chip">
              <el-icon><Calendar /></el-icon>
              {{ headerDateRangeText }}
            </span>
            <span class="header-chip">
              <el-icon><Goods /></el-icon>
              {{ selectedProductName }}
            </span>
            <span class="header-chip header-chip--strong">
              <el-icon><Tickets /></el-icon>
              {{ totalCount }} 件
            </span>
          </div>
        </div>
      </div>
      <div class="header-actions">
        <el-button size="small" class="btn-glass" @click="exportCsv">
          <el-icon><Download /></el-icon>CSV
        </el-button>
        <el-button size="small" type="primary" class="btn-primary-glass" :loading="updatingAll" @click="handleAllUpdate">
          <el-icon><Refresh /></el-icon>在庫更新
        </el-button>
      </div>
    </div>

    <div
      class="stat-cards glass animate-in"
      style="--delay: 0.05s"
      @mousemove="handleStatTilt"
      @mouseleave="resetStatTilt"
    >
      <div
        v-for="(item, i) in statCards"
        :key="item.key"
        class="stat-card"
        :class="`stat-tone-${i}`"
        :style="{ '--i': i }"
      >
        <span class="stat-label">{{ item.label }}</span>
        <span class="stat-value" :class="item.sum < 0 ? 'num-negative' : ''">{{ formatNum(item.sum) }}</span>
        <span class="stat-bar"><i :style="{ width: statBarWidth(item.sum) }" /></span>
      </div>
    </div>

    <div class="toolbar glass animate-in" style="--delay: 0.1s">
      <div class="toolbar-group">
        <span class="toolbar-label">期間</span>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="～"
          start-placeholder="開始日"
          end-placeholder="終了日"
          value-format="YYYY-MM-DD"
          size="small"
          class="date-range-picker"
          @change="onDateChange"
        />
        <div class="date-quick">
          <el-button
            size="small"
            class="date-quick-btn"
            :class="{ 'date-quick-btn--active': isPrevDay }"
            @click="setQuickDate('prev')"
          >
            前日
          </el-button>
          <el-button
            size="small"
            class="date-quick-btn"
            :class="{ 'date-quick-btn--active': isToday }"
            @click="setQuickDate('today')"
          >
            今日
          </el-button>
          <el-button
            size="small"
            class="date-quick-btn"
            :class="{ 'date-quick-btn--active': isNextDay }"
            @click="setQuickDate('next')"
          >
            翌日
          </el-button>
        </div>
      </div>
      <div class="toolbar-group">
        <span class="toolbar-label">製品名</span>
        <el-select
          v-model="filters.productCd"
          placeholder="全て"
          clearable
          filterable
          size="small"
          class="product-select"
          @change="onFilterChange"
        >
          <el-option
            v-for="p in productOptions"
            :key="p.product_cd"
            :label="p.product_name || p.product_cd"
            :value="p.product_cd"
          />
        </el-select>
      </div>
    </div>

    <div class="table-wrap glass animate-in" style="--delay: 0.15s">
      <el-table
        :data="list"
        v-loading="loading"
        stripe
        size="small"
        class="data-table"
        show-summary
        :summary-method="getSummaries"
        :height="tableHeight"
      >
        <el-table-column prop="product_cd" label="製品CD" width="100" fixed />
        <el-table-column prop="product_name" label="製品名" width="130" show-overflow-tooltip />
        <el-table-column prop="date" label="日付" width="105" align="center" />
        <el-table-column prop="day_of_week" label="曜日" width="60" align="center" />
        <el-table-column prop="cutting_inventory" label="切断" width="90" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.cutting_inventory)">{{ formatCellNum(row.cutting_inventory) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="chamfering_inventory" label="面取" width="90" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.chamfering_inventory)">{{ formatCellNum(row.chamfering_inventory) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="molding_inventory" label="成型" width="90" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.molding_inventory)">{{ formatCellNum(row.molding_inventory) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="plating_inventory" label="メッキ" width="90" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.plating_inventory)">{{ formatCellNum(row.plating_inventory) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="welding_inventory" label="溶接" width="90" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.welding_inventory)">{{ formatCellNum(row.welding_inventory) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="inspection_inventory" label="検査" width="90" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.inspection_inventory)">{{ formatCellNum(row.inspection_inventory) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="warehouse_inventory" label="倉庫" width="90" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.warehouse_inventory)">{{ formatCellNum(row.warehouse_inventory) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="outsourced_warehouse_inventory" label="外注倉庫" width="90" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.outsourced_warehouse_inventory)">{{ formatCellNum(row.outsourced_warehouse_inventory) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="outsourced_plating_inventory" label="外注メッキ" width="100" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.outsourced_plating_inventory)">{{ formatCellNum(row.outsourced_plating_inventory) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="outsourced_welding_inventory" label="外注溶接" width="90" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.outsourced_welding_inventory)">{{ formatCellNum(row.outsourced_welding_inventory) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="pre_welding_inspection_inventory" label="溶接前検査" width="100" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.pre_welding_inspection_inventory)">{{ formatCellNum(row.pre_welding_inspection_inventory) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="pre_inspection_inventory" label="支給前" width="90" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.pre_inspection_inventory)">{{ formatCellNum(row.pre_inspection_inventory) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="pre_outsourcing_inventory" label="検査前" width="90" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.pre_outsourcing_inventory)">{{ formatCellNum(row.pre_outsourcing_inventory) }}</span>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 在庫更新確認ダイアログ -->
    <el-dialog
      v-model="showAllUpdateConfirmDialog"
      title="在庫更新確認"
      width="400px"
      :close-on-click-modal="false"
    >
      <p class="confirm-message">在庫を更新しますか？</p>
      <template #footer>
        <el-button class="dlg-btn dlg-btn--ghost" @click="showAllUpdateConfirmDialog = false">キャンセル</el-button>
        <el-button class="dlg-btn dlg-btn--accent" type="primary" @click="confirmAllUpdate">更新</el-button>
      </template>
    </el-dialog>

    <!-- 一括更新進度ダイアログ -->
    <el-dialog
      v-model="showProgressDialog"
      title="在庫更新中"
      width="500px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
    >
      <div class="progress-content">
        <div class="progress-info">
          <el-icon class="progress-icon"><Loading /></el-icon>
          <span class="progress-text">{{ progressText }}</span>
        </div>
        <div class="progress-track">
          <div
            class="progress-fill"
            :class="{ 'progress-fill--success': progressStatus === 'success' }"
            :style="{ width: Math.min(100, Math.round(progressPercentage)) + '%' }"
          />
        </div>
        <span class="progress-percent">{{ Math.round(progressPercentage) }}%</span>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { List, Download, Refresh, Loading, Calendar, Goods, Tickets } from '@element-plus/icons-vue'
import {
  getProductionSummarysList,
  getProductionSummarysProducts,
  acquireBatchUpdateLock,
  releaseBatchUpdateLock,
  updateProductionSummarysFromOrderDaily,
  updateProductionSummarysActual,
  updateProductionSummarysDefect,
  updateProductionSummarysScrap,
  updateProductionSummarysOnHold,
  updateProductionSummarysPlan,
  clearProductionSummarysCalculatedFields,
  updateProductionSummarysInventory,
  updateProductionSummarysTrend,
  updateProductionSummarysSafetyStock,
  type ProductionSummaryInventoryRow,
  type ProductionSummaryProduct
} from '@/api/database'
import { useInventoryOperationPermission } from '@/composables/useInventoryOperationPermission'
import { guardInventoryOperation } from '@/utils/inventoryOperationGuard'

const { canCreate, canEdit, canDelete, canExport, canApprove } = useInventoryOperationPermission()


const loading = ref(false)
const list = ref<ProductionSummaryInventoryRow[]>([])
const productOptions = ref<ProductionSummaryProduct[]>([])
const dateRange = ref<[string, string] | null>(null)

const filters = reactive({
  productCd: ''
})

const totalCount = ref(0)

const showAllUpdateConfirmDialog = ref(false)
const showProgressDialog = ref(false)
const progressPercentage = ref(0)
const progressStatus = ref<'success' | ''>('')
const progressText = ref('')
const updatingAll = ref(false)

const INVENTORY_FIELDS: { key: keyof ProductionSummaryInventoryRow; label: string }[] = [
  { key: 'cutting_inventory', label: '切断' },
  { key: 'chamfering_inventory', label: '面取' },
  { key: 'molding_inventory', label: '成型' },
  { key: 'plating_inventory', label: 'メッキ' },
  { key: 'welding_inventory', label: '溶接' },
  { key: 'inspection_inventory', label: '検査' },
  { key: 'warehouse_inventory', label: '倉庫' },
  { key: 'outsourced_warehouse_inventory', label: '外注倉庫' },
  { key: 'outsourced_plating_inventory', label: '外注メッキ' },
  { key: 'outsourced_welding_inventory', label: '外注溶接' },
  { key: 'pre_welding_inspection_inventory', label: '溶接前検査' },
  { key: 'pre_inspection_inventory', label: '支給前' },
  { key: 'pre_outsourcing_inventory', label: '検査前' }
]

const statCards = computed(() => {
  const data = list.value
  return INVENTORY_FIELDS.map(({ key, label }) => {
    const sum = data.reduce((acc, row) => acc + (Number(row[key]) || 0), 0)
    return { key, label, sum }
  })
})

const statMaxAbs = computed(() =>
  statCards.value.reduce((m, c) => Math.max(m, Math.abs(c.sum)), 0),
)

function statBarWidth(sum: number): string {
  const max = statMaxAbs.value
  if (!max) return '0%'
  return `${Math.max(2, Math.round((Math.abs(sum) / max) * 100))}%`
}

const headerDateRangeText = computed(() => {
  const r = dateRange.value
  if (!r || !r[0]) return '—'
  return r[0] === r[1] ? r[0] : `${r[0]} 〜 ${r[1]}`
})

const selectedProductName = computed(() => {
  const cd = filters.productCd
  if (!cd) return '全製品'
  const p = productOptions.value.find((x) => x.product_cd === cd)
  return p?.product_name || cd
})

function handleStatTilt(e: MouseEvent) {
  const card = (e.target as HTMLElement | null)?.closest<HTMLElement>('.stat-card')
  const host = e.currentTarget as HTMLElement
  host.querySelectorAll<HTMLElement>('.stat-card').forEach((el) => {
    if (el !== card) {
      el.style.removeProperty('--rx')
      el.style.removeProperty('--ry')
    }
  })
  if (!card) return
  const rect = card.getBoundingClientRect()
  const px = (e.clientX - rect.left) / rect.width
  const py = (e.clientY - rect.top) / rect.height
  card.style.setProperty('--rx', `${((0.5 - py) * 16).toFixed(2)}deg`)
  card.style.setProperty('--ry', `${((px - 0.5) * 16).toFixed(2)}deg`)
  card.style.setProperty('--mx', `${(px * 100).toFixed(1)}%`)
  card.style.setProperty('--my', `${(py * 100).toFixed(1)}%`)
}

function resetStatTilt(e: MouseEvent) {
  ;(e.currentTarget as HTMLElement).querySelectorAll<HTMLElement>('.stat-card').forEach((el) => {
    el.style.removeProperty('--rx')
    el.style.removeProperty('--ry')
  })
}

function todayStr() {
  return new Date().toISOString().slice(0, 10)
}

function initDate() {
  if (!dateRange.value || !dateRange.value[0]) {
    const t = todayStr()
    dateRange.value = [t, t]
  }
}

function setQuickDate(which: 'prev' | 'today' | 'next') {
  const base = dateRange.value?.[0] || todayStr()
  const d = new Date(base)
  if (which === 'prev') d.setDate(d.getDate() - 1)
  else if (which === 'next') d.setDate(d.getDate() + 1)
  const s = d.toISOString().slice(0, 10)
  dateRange.value = [s, s]
  doFetch()
}

const isToday = computed(() => {
  const r = dateRange.value
  if (!r || r[0] !== r[1]) return false
  return r[0] === todayStr()
})
const isPrevDay = computed(() => {
  const r = dateRange.value
  if (!r || r[0] !== r[1]) return false
  const d = new Date(todayStr())
  d.setDate(d.getDate() - 1)
  return r[0] === d.toISOString().slice(0, 10)
})
const isNextDay = computed(() => {
  const r = dateRange.value
  if (!r || r[0] !== r[1]) return false
  const d = new Date(todayStr())
  d.setDate(d.getDate() + 1)
  return r[0] === d.toISOString().slice(0, 10)
})

function onDateChange() {
  doFetch()
}

function onFilterChange() {
  doFetch()
}

function getFirstDayOfCurrentMonth(): string {
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  return `${y}-${m}-01`
}

function getRandomUUID(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  const buf = new Uint8Array(16)
  if (typeof crypto !== 'undefined' && crypto.getRandomValues) {
    crypto.getRandomValues(buf)
  } else {
    for (let i = 0; i < 16; i++) buf[i] = Math.floor(Math.random() * 256)
  }
  buf[6] = (buf[6]! & 0x0f) | 0x40
  buf[8] = (buf[8]! & 0x3f) | 0x80
  const hex = Array.from(buf, b => b.toString(16).padStart(2, '0')).join('')
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
}

function handleAllUpdate() {
  if (!guardInventoryOperation(canEdit)) return

  showAllUpdateConfirmDialog.value = true
}

async function confirmAllUpdate() {
  if (!guardInventoryOperation(canApprove)) return

  showAllUpdateConfirmDialog.value = false
  const lockValue = getRandomUUID()
  try {
    await acquireBatchUpdateLock(lockValue)
  } catch (e: unknown) {
    const status = (e as { response?: { status?: number } })?.response?.status
    if (status === 423) {
      ElMessage.warning('他の端末で一括更新が実行中のため、しばらく待ってから再度お試しください。')
      return
    }
    ElMessage.error('ロックの取得に失敗しました。')
    return
  }
  updatingAll.value = true
  showProgressDialog.value = true
  progressStatus.value = ''
  const results: { name: string; success: boolean }[] = []
  const stepNames = [
    '受注データ更新',
    '実績データ更新',
    '不良データ更新',
    '廃棄データ更新',
    '保留データ更新',
    '計画データ更新',
  ]
  const steps = [
    () => updateProductionSummarysFromOrderDaily({ updateMode: 'all' }),
    () => updateProductionSummarysActual(),
    () => updateProductionSummarysDefect(),
    () => updateProductionSummarysScrap(),
    () => updateProductionSummarysOnHold(),
    () => updateProductionSummarysPlan(),
  ]
  try {
    for (let i = 0; i < steps.length; i++) {
      progressPercentage.value = Math.round(((i + 1) / 7) * 90)
      progressText.value = `${stepNames[i]}を実行中... (${i + 1}/7)`
      try {
        await steps[i]()
        results.push({ name: stepNames[i], success: true })
      } catch (_e) {
        results.push({ name: stepNames[i], success: false })
      }
      await new Promise((r) => setTimeout(r, 300))
    }
    const startDate = getFirstDayOfCurrentMonth()
    try {
      await clearProductionSummarysCalculatedFields(startDate)
    } catch (_e) {
      /* ignore */
    }
    progressPercentage.value = 92
    progressText.value = '在庫・推移更新を実行中... (7/7)'
    try {
      await updateProductionSummarysInventory(startDate)
      results.push({ name: '在庫更新', success: true })
    } catch (_e) {
      results.push({ name: '在庫更新', success: false })
    }
    await new Promise((r) => setTimeout(r, 300))
    try {
      await updateProductionSummarysTrend(startDate)
      results.push({ name: '推移更新', success: true })
    } catch (_e) {
      results.push({ name: '推移更新', success: false })
    }
    await new Promise((r) => setTimeout(r, 300))
    progressText.value = '安全在庫を更新中... (8/8)'
    try {
      await updateProductionSummarysSafetyStock(startDate)
      results.push({ name: '安全在庫更新', success: true })
    } catch (_e) {
      results.push({ name: '安全在庫更新', success: false })
    }
    progressPercentage.value = 100
    progressStatus.value = 'success'
    const successCount = results.filter((r) => r.success).length
    const failCount = results.filter((r) => !r.success).length
    const failedNames = results.filter((r) => !r.success).map((r) => r.name)
    progressText.value =
      failCount === 0
        ? '在庫更新が完了しました！'
        : `在庫更新が完了しました（成功 ${successCount} / 失敗 ${failCount}）\n失敗: ${failedNames.join('、')}`
    if (failCount === 0) {
      ElMessage.success('在庫更新が完了しました')
    } else {
      ElMessage.warning(`一部失敗しました: ${failedNames.join('、')}`)
    }
    setTimeout(() => {
      showProgressDialog.value = false
      updatingAll.value = false
      setTimeout(() => doFetch(), 500)
    }, 1500)
  } finally {
    try {
      await releaseBatchUpdateLock(lockValue)
    } catch (_e) {
      /* 解放失敗は無視 */
    }
  }
}

const tableHeight = computed(() => 'calc(100vh - 220px)')

function formatNum(v: number | null | undefined): string {
  if (v == null) return '0'
  return Number(v).toLocaleString()
}

/** テーブル数量：0 / 空は空白表示 */
function formatCellNum(v: number | null | undefined): string {
  if (v == null) return ''
  const n = Number(v)
  if (!Number.isFinite(n) || n === 0) return ''
  return n.toLocaleString()
}

function numClass(v: number | null | undefined): string {
  if (v == null) return ''
  const n = Number(v)
  if (n < 0) return 'num-negative'
  if (n === 0) return 'num-zero'
  return 'num-positive'
}

function getSummaries(param: { columns: { property?: string }[]; data: ProductionSummaryInventoryRow[] }) {
  const { columns, data } = param
  const sums: string[] = []
  const inventoryKeys = [
    'cutting_inventory', 'chamfering_inventory', 'molding_inventory', 'plating_inventory',
    'welding_inventory', 'inspection_inventory', 'warehouse_inventory', 'outsourced_warehouse_inventory',
    'outsourced_plating_inventory', 'outsourced_welding_inventory',
    'pre_welding_inspection_inventory', 'pre_inspection_inventory', 'pre_outsourcing_inventory'
  ] as const

  columns.forEach((col, index) => {
    if (index === 0) {
      sums.push('合計')
      return
    }
    if (index === 1 || index === 2 || index === 3) {
      sums.push('')
      return
    }
    const prop = col.property
    if (prop && inventoryKeys.includes(prop as typeof inventoryKeys[number])) {
      const total = data.reduce((acc, row) => acc + (Number((row as unknown as Record<string, unknown>)[prop]) || 0), 0)
      sums.push(total === 0 ? '' : total.toLocaleString())
    } else {
      sums.push('')
    }
  })
  return sums
}

function doFetch() {
  const t = todayStr()
  const start = dateRange.value?.[0] ?? t
  const end = dateRange.value?.[1] ?? t
  if (!start || !end) return

  loading.value = true
  const params: Record<string, unknown> = {
    page: 1,
    limit: 50000,
    startDate: start,
    endDate: end,
    sortBy: 'product_name',
    sortOrder: 'ASC'
  }
  if (filters.productCd) params.productCd = filters.productCd

  getProductionSummarysList(params)
    .then((res) => {
      const data = res?.data ?? res
      const listData = data?.list ?? data?.data?.list ?? []
      const pag = data?.pagination ?? data?.data?.pagination ?? {}
      list.value = listData as ProductionSummaryInventoryRow[]
      totalCount.value = Number(pag.total ?? listData.length)
    })
    .catch((e) => {
      console.error(e)
      ElMessage.error('データの取得に失敗しました')
      list.value = []
    })
    .finally(() => {
      loading.value = false
    })
}

async function fetchProducts() {
  try {
    const res = await getProductionSummarysProducts()
    const data = res?.data ?? res ?? []
    productOptions.value = Array.isArray(data) ? data : []
  } catch (e) {
    console.error(e)
    productOptions.value = []
  }
}

function exportCsv() {
  if (!guardInventoryOperation(canExport)) return

  const headers = [
    '品番', '品名', '日付', '曜日',
    '切断在庫', '面取在庫', '成型在庫', 'メッキ在庫', '溶接在庫', '検査在庫',
    '倉庫在庫', '外注倉庫在庫', '外注メッキ在庫', '外注溶接在庫',
    '溶接前検査在庫', '外注支給前在庫', '外注検査前在庫'
  ]
  const keys = [
    'product_cd', 'product_name', 'date', 'day_of_week',
    'cutting_inventory', 'chamfering_inventory', 'molding_inventory', 'plating_inventory',
    'welding_inventory', 'inspection_inventory', 'warehouse_inventory', 'outsourced_warehouse_inventory',
    'outsourced_plating_inventory', 'outsourced_welding_inventory',
    'pre_welding_inspection_inventory', 'pre_inspection_inventory', 'pre_outsourcing_inventory'
  ] as const
  const rows = list.value
  if (!rows.length) {
    ElMessage.warning('エクスポートするデータがありません')
    return
  }
  const escape = (v: unknown) => {
    const s = v == null ? '' : String(v)
    if (/[",\n\r]/.test(s)) return `"${s.replace(/"/g, '""')}"`
    return s
  }
  const lines = [headers.map(escape).join(',')]
  for (const row of rows) {
    lines.push(keys.map(k => escape((row as unknown as Record<string, unknown>)[k])).join(','))
  }
  const blob = new Blob(['\uFEFF' + lines.join('\r\n')], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  const [s, e] = dateRange.value || ['', '']
  a.download = `production_summary_inventory_${s || 'start'}_${e || 'end'}.csv`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('CSVをダウンロードしました')
}

onMounted(() => {
  initDate()
  fetchProducts()
  doFetch()
})
</script>

<style scoped>
.inventory-list-page {
  position: relative;
  padding: 14px 18px;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: hidden;
}

/* Background */
.page-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  overflow: hidden;
}

.bg-gradient {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 40%, #334155 100%);
}

.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.35;
  animation: orbFloat 18s ease-in-out infinite;
}

.bg-orb-1 {
  width: 420px;
  height: 420px;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  top: -120px;
  right: -80px;
}

.bg-orb-2 {
  width: 320px;
  height: 320px;
  background: linear-gradient(135deg, #06b6d4, #0ea5e9);
  bottom: 10%;
  left: -100px;
  animation-delay: -6s;
}

.bg-orb-3 {
  width: 240px;
  height: 240px;
  background: linear-gradient(135deg, #6366f1, #a855f7);
  bottom: -60px;
  right: 20%;
  animation-delay: -12s;
}

@keyframes orbFloat {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(20px, -30px) scale(1.05); }
  66% { transform: translate(-15px, 20px) scale(0.98); }
}

/* Glass */
.glass {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

/* Entrance animation */
.animate-in {
  animation: fadeInUp 0.5s ease-out forwards;
  opacity: 0;
  animation-delay: var(--delay, 0s);
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Header */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-radius: 16px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.page-header:hover {
  transform: translateY(-1px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.12);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.header-icon {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  background: linear-gradient(145deg, #6366f1 0%, #4f46e5 45%, #7c3aed 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    0 4px 16px rgba(79, 70, 229, 0.45),
    inset 0 1px 0 rgba(255, 255, 255, 0.22);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.header-icon:hover {
  transform: scale(1.05);
  box-shadow:
    0 8px 24px rgba(79, 70, 229, 0.55),
    inset 0 1px 0 rgba(255, 255, 255, 0.28);
}

.header-title {
  font-size: 20px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  margin: 0;
  letter-spacing: -0.02em;
}

.header-meta {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
  margin-left: 10px;
  font-weight: 500;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.btn-glass {
  border-radius: 10px !important;
  background: linear-gradient(
    145deg,
    rgba(255, 255, 255, 0.14) 0%,
    rgba(6, 182, 212, 0.12) 100%
  ) !important;
  border: 1px solid rgba(103, 232, 249, 0.35) !important;
  color: #ecfeff !important;
  font-weight: 600 !important;
  letter-spacing: 0.02em;
  box-shadow:
    0 2px 12px rgba(6, 182, 212, 0.18),
    inset 0 1px 0 rgba(255, 255, 255, 0.18) !important;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease, background 0.2s ease !important;
}

.btn-glass:hover {
  background: linear-gradient(
    145deg,
    rgba(255, 255, 255, 0.2) 0%,
    rgba(34, 211, 238, 0.22) 100%
  ) !important;
  border-color: rgba(165, 243, 252, 0.55) !important;
  transform: translateY(-1px);
  box-shadow:
    0 6px 20px rgba(6, 182, 212, 0.28),
    inset 0 1px 0 rgba(255, 255, 255, 0.25) !important;
}

.btn-primary-glass {
  border-radius: 10px !important;
  background: linear-gradient(145deg, #6366f1 0%, #4f46e5 48%, #7c3aed 100%) !important;
  border: 1px solid rgba(255, 255, 255, 0.28) !important;
  color: #fff !important;
  font-weight: 600 !important;
  letter-spacing: 0.02em;
  box-shadow:
    0 4px 18px rgba(79, 70, 229, 0.45),
    inset 0 1px 0 rgba(255, 255, 255, 0.22) !important;
  transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease !important;
}

.btn-primary-glass:hover {
  transform: translateY(-1px);
  filter: brightness(1.06);
  box-shadow:
    0 8px 26px rgba(79, 70, 229, 0.55),
    inset 0 1px 0 rgba(255, 255, 255, 0.28) !important;
}

.btn-primary-glass:active {
  transform: translateY(0);
  filter: brightness(0.98);
}

/* Stat cards */
.stat-cards {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 14px 16px;
  border-radius: 16px;
}

.stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 74px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  transition: all 0.25s ease;
  animation: cardIn 0.4s ease-out backwards;
  animation-delay: calc(var(--delay, 0s) + 0.02s * var(--i, 0));
}

.stat-card:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.18);
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

@keyframes cardIn {
  from {
    opacity: 0;
    transform: translateY(8px) scale(0.96);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.stat-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.55);
  margin-bottom: 4px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.stat-value {
  font-size: 15px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  transition: color 0.2s ease;
}

.stat-card .stat-value.num-negative {
  color: #f87171;
  text-shadow: 0 0 20px rgba(248, 113, 113, 0.3);
}

/* Toolbar */
.toolbar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 18px;
  padding: 12px 16px;
  border-radius: 16px;
}

.toolbar-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.toolbar-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.65);
  white-space: nowrap;
  font-weight: 500;
}

.toolbar :deep(.el-date-editor),
.toolbar :deep(.el-select) {
  --el-fill-color-blank: rgba(255, 255, 255, 0.08);
  --el-border-color: rgba(255, 255, 255, 0.15);
  --el-text-color-regular: rgba(255, 255, 255, 0.9);
}

.toolbar :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: none;
  transition: all 0.2s ease;
}

.toolbar :deep(.el-input__wrapper:hover),
.toolbar :deep(.el-input__wrapper.is-focus) {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.25);
}

.date-range-picker {
  width: 240px;
}

.date-quick {
  display: flex;
  gap: 8px;
}

.date-quick-btn {
  min-width: 58px !important;
  border-radius: 999px !important;
  font-weight: 600 !important;
  letter-spacing: 0.02em;
  background: rgba(255, 255, 255, 0.06) !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
  color: rgba(255, 255, 255, 0.72) !important;
  transition: background 0.2s ease, border-color 0.2s ease, color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease !important;
}

.date-quick-btn:hover {
  background: rgba(255, 255, 255, 0.11) !important;
  border-color: rgba(255, 255, 255, 0.22) !important;
  color: #fff !important;
  transform: translateY(-1px);
}

.date-quick-btn--active {
  background: linear-gradient(145deg, rgba(99, 102, 241, 0.55), rgba(6, 182, 212, 0.45)) !important;
  border-color: rgba(255, 255, 255, 0.32) !important;
  color: #fff !important;
  box-shadow:
    0 4px 16px rgba(79, 70, 229, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
}

.date-quick-btn--active:hover {
  background: linear-gradient(145deg, rgba(99, 102, 241, 0.68), rgba(6, 182, 212, 0.52)) !important;
}

.product-select {
  width: 200px;
}

/* Table wrap */
.table-wrap {
  flex: 1;
  min-height: 0;
  padding: 14px 16px;
  border-radius: 16px;
  transition: box-shadow 0.2s ease;
}

.table-wrap:hover {
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

/* 表格：浅色数据区，深色文字，保证可读 */
.data-table {
  font-size: 12px;
  border-radius: 12px;
  overflow: hidden;
  background: #ffffff !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.data-table :deep(.el-table__inner-wrapper) {
  background: #ffffff;
}

.data-table :deep(.el-table__header-wrapper) {
  background: #ffffff;
}

.data-table :deep(.el-table__header th) {
  background: #f1f5f9 !important;
  color: #334155 !important;
  font-weight: 600;
  font-size: 12px;
  padding: 8px 10px;
  border-color: #e2e8f0 !important;
}

.data-table :deep(.el-table__body-wrapper) {
  background: #ffffff;
}

.data-table :deep(.el-table__body tr) {
  transition: background 0.15s ease;
}

.data-table :deep(.el-table__body tr:hover > td) {
  background: #f8fafc !important;
}

.data-table :deep(.el-table__body td) {
  padding: 6px 10px;
  border-color: #e2e8f0 !important;
  background: #ffffff !important;
  color: #1e293b !important;
}

.data-table :deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background: #fafbfc !important;
  color: #1e293b !important;
}

.data-table :deep(.el-table--striped .el-table__body tr.el-table__row--striped:hover > td) {
  background: #f1f5f9 !important;
}

.data-table :deep(.el-table__footer-wrapper) {
  background: #ffffff;
}

.data-table :deep(.el-table__footer td) {
  background: #f1f5f9 !important;
  font-weight: 600;
  padding: 8px 10px;
  font-size: 12px;
  color: #1e293b !important;
  border-color: #e2e8f0 !important;
}

.data-table :deep(.el-table__empty-block) {
  background: #ffffff !important;
}

.num-positive { color: #1e293b; }
.num-zero { color: #64748b; }
.num-negative { color: #dc2626; font-weight: 600; }

/* ダイアログフッター（確認） */
.dlg-btn {
  border-radius: 10px !important;
  font-weight: 600 !important;
  min-width: 96px;
  transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease !important;
}

.dlg-btn--ghost {
  background: #f1f5f9 !important;
  border: 1px solid #e2e8f0 !important;
  color: #475569 !important;
}

.dlg-btn--ghost:hover {
  background: #e2e8f0 !important;
  border-color: #cbd5e1 !important;
  color: #334155 !important;
}

.dlg-btn--accent.el-button--primary {
  background: linear-gradient(145deg, #6366f1 0%, #4f46e5 50%, #7c3aed 100%) !important;
  border: none !important;
  box-shadow: 0 4px 14px rgba(79, 70, 229, 0.4) !important;
}

.dlg-btn--accent.el-button--primary:hover {
  filter: brightness(1.05);
  box-shadow: 0 6px 18px rgba(79, 70, 229, 0.48) !important;
}

/* 在庫更新確認・進度ダイアログ */
.confirm-message { margin: 0; font-size: 14px; color: #334155; }
.progress-content { padding: 8px 0; }
.progress-info { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.progress-icon { font-size: 20px; color: #409eff; }
.progress-text { font-size: 14px; color: #334155; white-space: pre-line; }
.progress-track { height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden; margin-bottom: 8px; }
.progress-fill { height: 100%; background: #409eff; border-radius: 4px; transition: width 0.3s ease; }
.progress-fill--success { background: #67c23a; }
.progress-percent { font-size: 12px; color: #64748b; }

/* 页面美化：現代UI・3D動効・色分け（仕掛品・製品在庫照会 / 在庫 teal→cyan→blue） */
.il-modern {
  --il-c1: #0f766e;
  --il-c2: #0891b2;
  --il-c3: #2563eb;
  --il-edge: #115e59;
}
.il-modern .bg-gradient {
  background:
    radial-gradient(circle at 6% -8%, rgba(13, 148, 136, 0.12), transparent 38%),
    radial-gradient(circle at 100% -12%, rgba(37, 99, 235, 0.1), transparent 34%),
    var(--el-bg-color-page, #f4f7fb);
}
.il-modern .bg-orb {
  opacity: 0.1;
}

/* ---- Hero ヘッダー ---- */
.il-modern .page-header {
  overflow: hidden;
  gap: 12px;
  flex-wrap: wrap;
  border: none;
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
  background: linear-gradient(135deg, #115e59 0%, #0d9488 30%, #0891b2 64%, #2563eb 100%);
  box-shadow:
    0 16px 32px -18px rgba(8, 145, 178, 0.75),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}
.il-modern .page-header:hover {
  transform: none;
  box-shadow:
    0 16px 32px -18px rgba(8, 145, 178, 0.75),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}
.il-modern .header-fx {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}
.il-modern .header-left,
.il-modern .header-actions {
  position: relative;
  z-index: 1;
}
.il-modern .header-icon {
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.34), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.4);
  box-shadow:
    0 10px 18px -8px rgba(4, 47, 46, 0.6),
    inset 0 -3px 0 rgba(4, 47, 46, 0.25),
    inset 0 1px 0 rgba(255, 255, 255, 0.45);
  animation: ilIconFloat 4.5s ease-in-out infinite;
}
.il-modern .header-title {
  color: #fff;
  text-shadow: 0 2px 6px rgba(4, 47, 46, 0.35);
}
.il-modern .header-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 6px;
}
.il-modern .header-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  font-variant-numeric: tabular-nums;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(6px);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2);
}
.il-modern .header-chip--strong {
  background: rgba(255, 255, 255, 0.26);
  border-color: rgba(255, 255, 255, 0.5);
}

/* ---- 3D キーキャップ（ヘッダー・ダイアログ） ---- */
.il-modern .btn-glass,
.il-modern .btn-primary-glass,
.il-modern .dlg-btn {
  border: none !important;
  border-radius: 10px !important;
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease,
    filter 0.15s ease !important;
  box-shadow:
    0 3px 0 var(--k-edge),
    0 10px 18px -8px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.35) !important;
}
.il-modern .btn-glass:not(.is-disabled):hover,
.il-modern .btn-primary-glass:not(.is-disabled):hover,
.il-modern .dlg-btn:not(.is-disabled):hover {
  transform: translateY(-2px);
  filter: brightness(1.05);
  box-shadow:
    0 5px 0 var(--k-edge),
    0 14px 22px -10px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.35) !important;
}
.il-modern .btn-glass:not(.is-disabled):active,
.il-modern .btn-primary-glass:not(.is-disabled):active,
.il-modern .dlg-btn:not(.is-disabled):active {
  transform: translateY(2px);
  box-shadow:
    0 1px 0 var(--k-edge),
    0 4px 8px -6px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.35) !important;
}
.il-modern .btn-glass {
  --k-edge: #5eead4;
  --k-glow: rgba(4, 47, 46, 0.45);
  color: #0f766e !important;
  background: linear-gradient(180deg, #ffffff, #ccfbf1) !important;
}
.il-modern .btn-glass:hover {
  background: linear-gradient(180deg, #ffffff, #ccfbf1) !important;
}
.il-modern .btn-primary-glass {
  --k-edge: #c2410c;
  --k-glow: rgba(234, 88, 12, 0.5);
  color: #fff !important;
  background: linear-gradient(180deg, #fbbf24, #f97316) !important;
}
.il-modern .dlg-btn--ghost {
  --k-edge: #cbd5e1;
  --k-glow: rgba(100, 116, 139, 0.3);
}
.il-modern .dlg-btn--accent.el-button--primary {
  --k-edge: #115e59;
  --k-glow: rgba(13, 148, 136, 0.5);
  background: linear-gradient(180deg, #2dd4bf, #0d9488 55%, #0891b2) !important;
}

/* ---- 集計カード（工程別色分け・3D チルト） ---- */
.il-modern .stat-cards,
.il-modern .toolbar,
.il-modern .table-wrap {
  overflow: hidden;
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
  background: var(--el-bg-color, #fff);
  border: 1px solid color-mix(in srgb, var(--il-c2) 14%, #e2e8f0);
  box-shadow:
    0 12px 26px -20px rgba(8, 145, 178, 0.55),
    0 1px 2px rgba(15, 23, 42, 0.05);
}
.il-modern .stat-cards::before,
.il-modern .toolbar::before,
.il-modern .table-wrap::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--il-c1), var(--il-c2), var(--il-c3));
}
.il-modern .stat-cards {
  perspective: 900px;
  gap: 8px;
}
.il-modern .stat-card {
  --sc: #0d9488;
  position: relative;
  overflow: hidden;
  flex: 1 1 88px;
  min-width: 88px;
  padding: 10px 10px 8px;
  border-radius: 12px;
  background: linear-gradient(160deg, color-mix(in srgb, var(--sc) 10%, #fff), #fff 70%);
  border: 1px solid color-mix(in srgb, var(--sc) 24%, #e2e8f0);
  box-shadow:
    0 3px 0 color-mix(in srgb, var(--sc) 30%, #e2e8f0),
    0 10px 18px -14px color-mix(in srgb, var(--sc) 70%, transparent);
  transform: rotateX(var(--rx, 0deg)) rotateY(var(--ry, 0deg));
  transform-style: preserve-3d;
  transition:
    transform 0.18s ease-out,
    box-shadow 0.2s ease;
}
.il-modern .stat-card::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--sc), color-mix(in srgb, var(--sc) 45%, #fff));
}
.il-modern .stat-card::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.2s ease;
  background: radial-gradient(
    circle at var(--mx, 50%) var(--my, 50%),
    rgba(255, 255, 255, 0.75),
    transparent 60%
  );
}
.il-modern .stat-card:hover {
  background: linear-gradient(160deg, color-mix(in srgb, var(--sc) 16%, #fff), #fff 70%);
  border-color: color-mix(in srgb, var(--sc) 45%, #e2e8f0);
  transform: rotateX(var(--rx, 0deg)) rotateY(var(--ry, 0deg)) translateZ(6px);
  box-shadow:
    0 5px 0 color-mix(in srgb, var(--sc) 40%, #e2e8f0),
    0 16px 26px -14px color-mix(in srgb, var(--sc) 80%, transparent);
}
.il-modern .stat-card:hover::after {
  opacity: 1;
}
.il-modern .stat-label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: color-mix(in srgb, var(--sc) 75%, #1e293b);
  font-weight: 700;
  transform: translateZ(14px);
}
.il-modern .stat-label::before {
  content: '';
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--sc);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--sc) 20%, transparent);
}
.il-modern .stat-value {
  color: #0f172a;
  font-size: 16px;
  font-variant-numeric: tabular-nums;
  transform: translateZ(20px);
}
.il-modern .stat-card .stat-value.num-negative {
  color: #dc2626;
  text-shadow: none;
}
.il-modern .stat-bar {
  display: block;
  width: 100%;
  height: 4px;
  margin-top: 6px;
  border-radius: 4px;
  overflow: hidden;
  background: color-mix(in srgb, var(--sc) 12%, #f1f5f9);
}
.il-modern .stat-bar i {
  display: block;
  height: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, color-mix(in srgb, var(--sc) 55%, #fff), var(--sc));
  transition: width 0.5s ease;
}
.il-modern .stat-tone-0 { --sc: #6366f1; }
.il-modern .stat-tone-1 { --sc: #8b5cf6; }
.il-modern .stat-tone-2 { --sc: #0ea5e9; }
.il-modern .stat-tone-3 { --sc: #d97706; }
.il-modern .stat-tone-4 { --sc: #ef4444; }
.il-modern .stat-tone-5 { --sc: #10b981; }
.il-modern .stat-tone-6 { --sc: #0d9488; }
.il-modern .stat-tone-7 { --sc: #14b8a6; }
.il-modern .stat-tone-8 { --sc: #ca8a04; }
.il-modern .stat-tone-9 { --sc: #f97316; }
.il-modern .stat-tone-10 { --sc: #ec4899; }
.il-modern .stat-tone-11 { --sc: #64748b; }
.il-modern .stat-tone-12 { --sc: #65a30d; }

/* ---- ツールバー ---- */
.il-modern .toolbar-label {
  display: inline-flex;
  align-items: center;
  height: 22px;
  padding: 0 9px;
  border-radius: 999px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, var(--il-c1), var(--il-c2));
  box-shadow: 0 2px 0 var(--il-edge);
}
.il-modern .toolbar :deep(.el-date-editor),
.il-modern .toolbar :deep(.el-select) {
  --el-fill-color-blank: #fff;
  --el-border-color: #cbd5e1;
  --el-text-color-regular: #1e293b;
}
.il-modern .toolbar :deep(.el-input__wrapper),
.il-modern .toolbar :deep(.el-select__wrapper) {
  border-radius: 8px;
  background: #fff;
  border: none;
  box-shadow: 0 0 0 1px #d5dee8 inset;
}
.il-modern .toolbar :deep(.el-input__wrapper:hover),
.il-modern .toolbar :deep(.el-input__wrapper.is-focus),
.il-modern .toolbar :deep(.el-select__wrapper:hover),
.il-modern .toolbar :deep(.el-select__wrapper.is-focused) {
  background: #fff;
  box-shadow:
    0 0 0 1px color-mix(in srgb, var(--il-c2) 60%, transparent) inset,
    0 4px 10px -6px rgba(8, 145, 178, 0.55);
}
.il-modern .toolbar :deep(.el-range-input) {
  color: #1e293b;
  background: transparent;
}
.il-modern .date-quick-btn {
  border: none !important;
  color: #0f766e !important;
  background: linear-gradient(180deg, #ffffff, #f0fdfa) !important;
  box-shadow:
    0 3px 0 #99f6e4,
    0 8px 14px -10px rgba(13, 148, 136, 0.6),
    inset 0 0 0 1px #ccfbf1 !important;
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease !important;
}
.il-modern .date-quick-btn:hover {
  transform: translateY(-2px);
  color: #0f766e !important;
  background: linear-gradient(180deg, #ffffff, #ccfbf1) !important;
  box-shadow:
    0 5px 0 #5eead4,
    0 12px 18px -10px rgba(13, 148, 136, 0.6),
    inset 0 0 0 1px #99f6e4 !important;
}
.il-modern .date-quick-btn:active {
  transform: translateY(2px);
  box-shadow:
    0 1px 0 #5eead4,
    inset 0 0 0 1px #99f6e4 !important;
}
.il-modern .date-quick-btn--active,
.il-modern .date-quick-btn--active:hover {
  color: #fff !important;
  background: linear-gradient(180deg, #2dd4bf, #0d9488 60%, #0891b2) !important;
  box-shadow:
    0 3px 0 var(--il-edge),
    0 10px 18px -8px rgba(13, 148, 136, 0.6),
    inset 0 1px 0 rgba(255, 255, 255, 0.35) !important;
}

/* ---- テーブル ---- */
.il-modern .table-wrap:hover {
  box-shadow:
    0 16px 30px -20px rgba(8, 145, 178, 0.6),
    0 1px 2px rgba(15, 23, 42, 0.05);
}
.il-modern .data-table {
  border: 1px solid color-mix(in srgb, var(--il-c2) 16%, #e2e8f0);
  border-radius: 10px;
}
.il-modern .data-table :deep(.el-table__header th) {
  color: #fff !important;
  background: linear-gradient(180deg, #0d9488 0%, #0f766e 100%) !important;
  border-color: rgba(255, 255, 255, 0.18) !important;
}
.il-modern .data-table :deep(.el-table__header th .cell) {
  color: #fff;
}
.il-modern .data-table :deep(.el-table__header th.el-table__cell:nth-child(n + 5)) {
  background: linear-gradient(180deg, #0891b2 0%, #0e7490 100%) !important;
  box-shadow: inset 0 -3px 0 var(--hd-tone, transparent);
}
.il-modern .data-table :deep(.el-table__header th.el-table__cell:nth-child(5)) { --hd-tone: #a5b4fc; }
.il-modern .data-table :deep(.el-table__header th.el-table__cell:nth-child(6)) { --hd-tone: #c4b5fd; }
.il-modern .data-table :deep(.el-table__header th.el-table__cell:nth-child(7)) { --hd-tone: #7dd3fc; }
.il-modern .data-table :deep(.el-table__header th.el-table__cell:nth-child(8)) { --hd-tone: #fcd34d; }
.il-modern .data-table :deep(.el-table__header th.el-table__cell:nth-child(9)) { --hd-tone: #fca5a5; }
.il-modern .data-table :deep(.el-table__header th.el-table__cell:nth-child(10)) { --hd-tone: #6ee7b7; }
.il-modern .data-table :deep(.el-table__header th.el-table__cell:nth-child(11)) { --hd-tone: #5eead4; }
.il-modern .data-table :deep(.el-table__header th.el-table__cell:nth-child(12)) { --hd-tone: #99f6e4; }
.il-modern .data-table :deep(.el-table__header th.el-table__cell:nth-child(13)) { --hd-tone: #fde047; }
.il-modern .data-table :deep(.el-table__header th.el-table__cell:nth-child(14)) { --hd-tone: #fdba74; }
.il-modern .data-table :deep(.el-table__header th.el-table__cell:nth-child(15)) { --hd-tone: #f9a8d4; }
.il-modern .data-table :deep(.el-table__header th.el-table__cell:nth-child(16)) { --hd-tone: #cbd5e1; }
.il-modern .data-table :deep(.el-table__header th.el-table__cell:nth-child(17)) { --hd-tone: #bef264; }
.il-modern .data-table :deep(.el-table__body tr:hover > td) {
  background: #f0fdfa !important;
}
.il-modern .data-table :deep(.el-table__body tr:hover > td:first-child) {
  box-shadow: inset 3px 0 0 var(--il-c1);
}
.il-modern .data-table :deep(.el-table__body td:first-child .cell) {
  font-weight: 600;
  color: var(--il-c1);
  font-variant-numeric: tabular-nums;
}
.il-modern .data-table :deep(.el-table__footer td) {
  color: var(--il-edge) !important;
  background: linear-gradient(180deg, #f0fdfa, #ccfbf1) !important;
  border-top: 2px solid #5eead4 !important;
  font-variant-numeric: tabular-nums;
}
.il-modern .data-table :deep(.el-table__body-wrapper .el-scrollbar__thumb) {
  background: linear-gradient(180deg, #2dd4bf, #0891b2);
  opacity: 0.7;
}
.il-modern .data-table .num-positive {
  font-variant-numeric: tabular-nums;
}
.il-modern .data-table .num-negative {
  display: inline-block;
  padding: 0 6px;
  border-radius: 6px;
  color: #b91c1c;
  background: #fee2e2;
  box-shadow: inset 0 -1px 0 #fca5a5;
  font-variant-numeric: tabular-nums;
}
.il-modern :deep(.el-loading-spinner .path) {
  stroke: var(--il-c2);
}

/* ---- 在庫更新ダイアログ ---- */
.il-modern .progress-icon {
  color: var(--il-c2);
  animation: ilSpin 1s linear infinite;
}
.il-modern .progress-track {
  height: 10px;
  border-radius: 999px;
  background: #e2e8f0;
  box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.12);
}
.il-modern .progress-fill {
  border-radius: 999px;
  background:
    repeating-linear-gradient(
      45deg,
      rgba(255, 255, 255, 0.22) 0 8px,
      transparent 8px 16px
    ),
    linear-gradient(90deg, #14b8a6, #0891b2, #2563eb);
  background-size:
    22px 22px,
    100% 100%;
  animation: ilStripe 0.8s linear infinite;
}
.il-modern .progress-fill--success {
  background: linear-gradient(90deg, #10b981, #059669);
  animation: none;
}
@keyframes ilIconFloat {
  0%,
  100% {
    transform: perspective(300px) rotateX(10deg) rotateY(-14deg) translateY(0);
  }
  50% {
    transform: perspective(300px) rotateX(-4deg) rotateY(12deg) translateY(-2px);
  }
}
@keyframes ilStripe {
  from {
    background-position:
      0 0,
      0 0;
  }
  to {
    background-position:
      22px 0,
      0 0;
  }
}
@keyframes ilSpin {
  to {
    transform: rotate(360deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .il-modern .header-icon,
  .il-modern .progress-fill,
  .il-modern .progress-icon,
  .il-modern .bg-orb {
    animation: none;
  }
  .il-modern .stat-card,
  .il-modern .stat-card:hover {
    transform: none;
    transition: none;
  }
}
</style>
