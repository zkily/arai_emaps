<template>
  <div class="inventory-list-page">
    <div class="page-bg">
      <div class="bg-gradient"></div>
      <div class="bg-orb bg-orb-1"></div>
      <div class="bg-orb bg-orb-2"></div>
      <div class="bg-orb bg-orb-3"></div>
    </div>

    <div class="page-header glass animate-in">
      <div class="header-left">
        <div class="header-icon">
          <el-icon size="24"><List /></el-icon>
        </div>
        <div class="header-text">
          <h1 class="header-title">在庫一覧</h1>
          <span class="header-meta">{{ totalCount }} 件</span>
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

    <div class="stat-cards glass animate-in" style="--delay: 0.05s">
      <div
        v-for="(item, i) in statCards"
        :key="item.key"
        class="stat-card"
        :style="{ '--i': i }"
      >
        <span class="stat-label">{{ item.label }}</span>
        <span class="stat-value" :class="item.sum < 0 ? 'num-negative' : ''">{{ formatNum(item.sum) }}</span>
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
          <el-button size="small" :type="isPrevDay ? 'primary' : ''" @click="setQuickDate('prev')">前日</el-button>
          <el-button size="small" :type="isToday ? 'primary' : ''" @click="setQuickDate('today')">今日</el-button>
          <el-button size="small" :type="isNextDay ? 'primary' : ''" @click="setQuickDate('next')">翌日</el-button>
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
            <span :class="numClass(row.cutting_inventory)">{{ formatNum(row.cutting_inventory) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="chamfering_inventory" label="面取" width="90" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.chamfering_inventory)">{{ formatNum(row.chamfering_inventory) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="molding_inventory" label="成型" width="90" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.molding_inventory)">{{ formatNum(row.molding_inventory) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="plating_inventory" label="メッキ" width="90" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.plating_inventory)">{{ formatNum(row.plating_inventory) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="welding_inventory" label="溶接" width="90" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.welding_inventory)">{{ formatNum(row.welding_inventory) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="inspection_inventory" label="検査" width="90" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.inspection_inventory)">{{ formatNum(row.inspection_inventory) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="warehouse_inventory" label="倉庫" width="90" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.warehouse_inventory)">{{ formatNum(row.warehouse_inventory) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="outsourced_warehouse_inventory" label="外注倉庫" width="90" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.outsourced_warehouse_inventory)">{{ formatNum(row.outsourced_warehouse_inventory) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="outsourced_plating_inventory" label="外注メッキ" width="100" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.outsourced_plating_inventory)">{{ formatNum(row.outsourced_plating_inventory) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="outsourced_welding_inventory" label="外注溶接" width="90" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.outsourced_welding_inventory)">{{ formatNum(row.outsourced_welding_inventory) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="pre_welding_inspection_inventory" label="溶接前検査" width="100" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.pre_welding_inspection_inventory)">{{ formatNum(row.pre_welding_inspection_inventory) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="pre_inspection_inventory" label="支給前" width="90" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.pre_inspection_inventory)">{{ formatNum(row.pre_inspection_inventory) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="pre_outsourcing_inventory" label="検査前" width="90" align="right">
          <template #default="{ row }">
            <span :class="numClass(row.pre_outsourcing_inventory)">{{ formatNum(row.pre_outsourcing_inventory) }}</span>
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
        <el-button @click="showAllUpdateConfirmDialog = false">キャンセル</el-button>
        <el-button type="primary" @click="confirmAllUpdate">更新</el-button>
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
import { List, Download, Refresh, Loading } from '@element-plus/icons-vue'
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
  showAllUpdateConfirmDialog.value = true
}

async function confirmAllUpdate() {
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
      sums.push(total.toLocaleString())
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
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.9), rgba(99, 102, 241, 0.9));
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 14px rgba(59, 130, 246, 0.4);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.header-icon:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.5);
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
  background: rgba(255, 255, 255, 0.12) !important;
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
  color: rgba(255, 255, 255, 0.95) !important;
  transition: all 0.2s ease !important;
}

.btn-glass:hover {
  background: rgba(255, 255, 255, 0.2) !important;
  border-color: rgba(255, 255, 255, 0.3) !important;
  transform: translateY(-1px);
}

.btn-primary-glass {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.9), rgba(99, 102, 241, 0.9)) !important;
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
  box-shadow: 0 4px 14px rgba(59, 130, 246, 0.35) !important;
  transition: all 0.2s ease !important;
}

.btn-primary-glass:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.5) !important;
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
  gap: 6px;
}

.date-quick .el-button {
  min-width: 56px;
  transition: all 0.2s ease;
}

.date-quick .el-button:not(.is-plain):hover {
  transform: translateY(-1px);
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
</style>
