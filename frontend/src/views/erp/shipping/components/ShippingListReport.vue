<template>
  <div class="shipping-list-report">
    <!-- ヘッダー: 出荷日 | 出荷品リスト(中央・青下線) | 印刷日時 -->
    <div class="report-header">
      <div class="header-content">
        <span class="header-left">出荷日: {{ formatShippingDateSlash(filters.dateRange) }}</span>
        <h1 class="report-title">出荷品リスト</h1>
        <span class="header-right">印刷日時: {{ printDateTime }}</span>
      </div>
    </div>

    <div class="report-body">
      <div
        v-for="(destGroup, index) in groupedData"
        :key="`${destGroup.destination_name}-${index}`"
        class="destination-section"
      >
        <h2 class="destination-title">{{ destGroup.destination_name }}</h2>
        <table class="report-table">
          <thead>
            <tr>
              <th class="col-shipping-no">出荷NO</th>
              <th class="col-product-name">製品名</th>
              <th class="col-product-type">製品種類</th>
              <th class="col-box-type">箱タイプ</th>
              <th class="col-pallet-no">バレNO</th>
              <th class="col-qty">受注数</th>
              <th class="col-units">受注本数</th>
              <th class="col-delivery">納入日</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, itemIndex) in destGroup.items" :key="itemIndex">
              <td class="col-shipping-no">{{ item.shipping_no || '-' }}</td>
              <td class="col-product-name product-name-cell">{{ item.product_name || '-' }}</td>
              <td class="col-product-type">{{ item.product_type || '量産品' }}</td>
              <td class="col-box-type">{{ item.box_type || '-' }}</td>
              <td class="col-pallet-no">{{ item.no || '-' }}</td>
              <td class="col-qty">{{ formatNum(item.quantity) }}</td>
              <td class="col-units">{{ formatNum(item.units) }}</td>
              <td class="col-delivery">{{ formatDateSlash(item.delivery_date) }}</td>
            </tr>
          </tbody>
        </table>
        <div class="destination-summary">
          <span class="summary-label">合計</span>
          <div class="summary-items">
            <span class="summary-item">受注箱数: {{ destGroup.totalQuantity }}</span>
            <span class="summary-item">受注本数: {{ destGroup.totalUnits }}</span>
            <span class="summary-item">出荷パレ数: {{ destGroup.shippingPalletCount }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface ListItem {
  no?: string
  shipping_date?: string
  destination_name?: string
  shipping_no?: string
  product_name?: string
  product_type?: string
  box_type?: string
  quantity?: number
  units?: number | null
  delivery_date?: string | null
}

const props = defineProps<{
  data: ListItem[]
  filters: { dateRange?: string[] }
}>()

const printDateTime = computed(() => {
  return new Date().toLocaleString('ja-JP')
})

function formatShippingDateSlash(dateRange: string[] | undefined) {
  if (!dateRange || dateRange.length !== 2) return 'N/A'
  if (dateRange[0] === dateRange[1]) return formatDateSlash(dateRange[0])
  return `${formatDateSlash(dateRange[0])} ~ ${formatDateSlash(dateRange[1])}`
}

function formatDateSlash(dateStr: string | undefined | null) {
  if (!dateStr) return '-'
  const date = new Date(dateStr + 'T00:00:00+09:00')
  return date.toLocaleDateString('ja-JP', { timeZone: 'Asia/Tokyo', year: 'numeric', month: 'numeric', day: 'numeric' })
}

function formatNum(v: number | undefined | null): string {
  if (v == null || v === undefined) return '-'
  return String(Number(v))
}

const groupedData = computed(() => {
  if (!props.data || props.data.length === 0) return []
  const destMap = new Map<string, ListItem[]>()
  props.data.forEach((item) => {
    const name = item.destination_name || ''
    if (!destMap.has(name)) destMap.set(name, [])
    destMap.get(name)!.push(item)
  })
  const result: Array<{
    destination_name: string
    items: ListItem[]
    totalQuantity: number
    totalUnits: number
    shippingPalletCount: number
  }> = []
  destMap.forEach((items, destination_name) => {
    const sorted = [...items].sort((a, b) => (a.shipping_no || '').localeCompare(b.shipping_no || ''))
    const totalQuantity = sorted.reduce((sum, item) => sum + (Number(item.quantity) || 0), 0)
    const totalUnits = sorted.reduce((sum, item) => sum + (Number(item.units) || 0), 0)
    const palletSet = new Set(sorted.map((item) => item.no || item.shipping_no).filter(Boolean))
    result.push({
      destination_name,
      items: sorted,
      totalQuantity,
      totalUnits,
      shippingPalletCount: palletSet.size,
    })
  })
  result.sort((a, b) => a.destination_name.localeCompare(b.destination_name))
  return result
})
</script>

<style scoped>
.shipping-list-report {
  font-family: 'Yu Gothic', 'Hiragino Sans', 'Meiryo', sans-serif;
  color: #1a1a1a;
  background: #fff;
  padding: 16px;
  line-height: 1.35;
}

/* ========== ヘッダー（画像どおり） ========== */
.report-header {
  border-bottom: 1px solid #333;
  padding: 8px 0 10px 0;
  margin-bottom: 14px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 4px;
  gap: 12px;
}

.header-left {
  flex: 1;
  font-size: 14px;
  font-weight: 700;
  color: #1a1a1a;
  text-align: left;
}

.report-title {
  flex: 0 0 auto;
  font-size: 22px;
  font-weight: 700;
  margin: 0;
  color: #1a1a1a;
  text-align: center;
  padding: 0 16px;
  position: relative;
}

.report-title::after {
  content: '';
  position: absolute;
  left: 50%;
  bottom: -4px;
  transform: translateX(-50%);
  width: 80px;
  height: 2px;
  background: #2563eb;
}

.header-right {
  flex: 1;
  font-size: 11px;
  font-weight: 600;
  color: #555;
  text-align: right;
}

/* ========== 納入先セクション ========== */
.report-body {
  width: 100%;
}

.destination-section {
  margin-bottom: 18px;
  page-break-inside: auto;
}

.destination-title {
  font-size: 14px;
  font-weight: 700;
  margin: 0 0 6px 0;
  padding: 0;
  color: #1a1a1a;
  background: transparent;
}

/* ========== テーブル（薄グレーヘッダー・細線・配置） ========== */
.report-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  margin-bottom: 4px;
}

.report-table thead {
  display: table-header-group;
}

.report-table thead tr {
  border-top: 1px solid #ccc;
  border-bottom: 1px solid #ccc;
}

.report-table th {
  background: #e8e8e8;
  color: #1a1a1a;
  font-weight: 600;
  padding: 6px 8px;
  font-size: 11px;
}

.report-table .col-shipping-no { text-align: left; }
.report-table .col-product-name { text-align: left; }
.report-table .col-product-type { text-align: left; }
.report-table .col-box-type { text-align: left; }
.report-table .col-pallet-no { text-align: center; }
.report-table .col-qty { text-align: right; }
.report-table .col-units { text-align: right; }
.report-table .col-delivery { text-align: left; }

.report-table tbody td {
  padding: 5px 8px;
  border-bottom: 1px solid #eee;
  vertical-align: middle;
}

.report-table tbody tr {
  page-break-inside: avoid;
}

.product-name-cell {
  font-weight: 600;
}

/* ========== 合計行（画像どおり） ========== */
.destination-summary {
  padding: 6px 8px 0 8px;
  font-weight: 700;
  font-size: 12px;
  border-top: 1px solid #ccc;
  display: flex;
  align-items: center;
  gap: 24px;
}

.summary-label {
  flex-shrink: 0;
}

.summary-items {
  display: flex;
  gap: 24px;
  margin-left: auto;
}

.summary-item {
  white-space: nowrap;
}

/* ========== 印刷用 ========== */
@media print {
  @page {
    size: A4;
    margin: 12mm;
  }

  .shipping-list-report {
    padding: 0;
    background: #fff;
  }

  .report-header {
    border-bottom: 1px solid #000;
    margin-bottom: 12px;
    padding: 6px 0 8px 0;
  }

  .report-title::after {
    background: #2563eb;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }

  .report-table thead {
    display: table-header-group;
  }

  .report-table th {
    background: #e8e8e8 !important;
    color: #000 !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }

  .report-table thead tr {
    border-top: 1px solid #999;
    border-bottom: 1px solid #999;
  }

  .report-table tbody td {
    border-bottom: 1px solid #ddd;
  }

  .destination-summary {
    border-top: 1px solid #999;
  }

  .destination-section {
    page-break-inside: auto;
  }
}
</style>
