<template>
  <div class="mir-page">
    <!-- Header -->
    <div class="mir-header">
      <div class="mir-title">棚卸統合報告書</div>
      <div class="mir-subtitle">{{ data.meta.month_label }} 月末実在庫基準</div>
    </div>
    <div class="mir-meta">
      <span>対象日: {{ data.meta.as_of }}</span>
      <span v-if="data.meta.exchange_rate">為替レート: {{ data.meta.exchange_rate }}</span>
      <span>印刷: {{ data.meta.printed_at }}</span>
    </div>

    <!-- 1. 総括（種別: T/N/F） -->
    <div class="mir-section">
      <div class="mir-section-title">総括（種別別）</div>
      <table>
        <thead>
          <tr>
            <th class="w-label">種別</th>
            <th>仕掛品 本数</th>
            <th>仕掛品 金額</th>
            <th>製品 本数</th>
            <th>製品 金額</th>
            <th>合計 本数</th>
            <th>合計 金額</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in data.overview_by_kind.rows" :key="row.label">
            <td class="center">{{ row.label }}</td>
            <td>{{ fmt(row.wip_qty, 0) }}</td>
            <td>{{ fmt(row.wip_amount) }}</td>
            <td>{{ fmt(row.product_qty, 0) }}</td>
            <td>{{ fmt(row.product_amount) }}</td>
            <td>{{ fmt(row.total_qty, 0) }}</td>
            <td>{{ fmt(row.total_amount) }}</td>
          </tr>
          <tr class="total-row">
            <td class="center">合計</td>
            <td>{{ fmt(data.overview_by_kind.totals.wip_qty, 0) }}</td>
            <td>{{ fmt(data.overview_by_kind.totals.wip_amount) }}</td>
            <td>{{ fmt(data.overview_by_kind.totals.product_qty, 0) }}</td>
            <td>{{ fmt(data.overview_by_kind.totals.product_amount) }}</td>
            <td>{{ fmt(data.overview_by_kind.totals.total_qty, 0) }}</td>
            <td>{{ fmt(data.overview_by_kind.totals.total_amount) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 2. 分類別（一般/溶接/メカ溶接/その他） -->
    <div class="mir-section">
      <div class="mir-section-title">分類別</div>
      <table>
        <thead>
          <tr>
            <th class="w-label">分類</th>
            <th>仕掛品 本数</th>
            <th>仕掛品 金額</th>
            <th>製品 本数</th>
            <th>製品 金額</th>
            <th>合計 本数</th>
            <th>合計 金額</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in data.overview_by_category.rows" :key="row.label">
            <td class="center">{{ row.label }}</td>
            <td>{{ fmt(row.wip_qty, 0) }}</td>
            <td>{{ fmt(row.wip_amount) }}</td>
            <td>{{ fmt(row.product_qty, 0) }}</td>
            <td>{{ fmt(row.product_amount) }}</td>
            <td>{{ fmt(row.total_qty, 0) }}</td>
            <td>{{ fmt(row.total_amount) }}</td>
          </tr>
          <tr class="total-row">
            <td class="center">合計</td>
            <td>{{ fmt(data.overview_by_category.totals.wip_qty, 0) }}</td>
            <td>{{ fmt(data.overview_by_category.totals.wip_amount) }}</td>
            <td>{{ fmt(data.overview_by_category.totals.product_qty, 0) }}</td>
            <td>{{ fmt(data.overview_by_category.totals.product_amount) }}</td>
            <td>{{ fmt(data.overview_by_category.totals.total_qty, 0) }}</td>
            <td>{{ fmt(data.overview_by_category.totals.total_amount) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 3. 部品（メカ）明細 -->
    <div v-if="data.parts_meka.rows.length" class="mir-section">
      <div class="mir-section-title">部品（メカ）</div>
      <table>
        <thead>
          <tr>
            <th class="w-kind">種別</th>
            <th class="w-cd">部品CD</th>
            <th class="w-name">部品名</th>
            <th>本数</th>
            <th>金額</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, idx) in data.parts_meka.rows" :key="idx">
            <td class="center">{{ row.kind }}</td>
            <td class="left">{{ row.part_cd }}</td>
            <td class="left">{{ row.part_name }}</td>
            <td>{{ fmt(row.qty, 0) }}</td>
            <td>{{ fmt(row.amount) }}</td>
          </tr>
          <tr class="total-row">
            <td class="center" colspan="3">合計</td>
            <td>{{ fmt(data.parts_meka.totals.qty, 0) }}</td>
            <td>{{ fmt(data.parts_meka.totals.amount) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 4. 部品（メカ以外）種別集計 -->
    <div v-if="data.parts_non_meka.rows.length" class="mir-section">
      <div class="mir-section-title">部品（メカ以外）</div>
      <table>
        <thead>
          <tr>
            <th class="w-label">種別</th>
            <th>本数</th>
            <th>金額</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in data.parts_non_meka.rows" :key="row.kind">
            <td class="center">{{ row.kind }}</td>
            <td>{{ fmt(row.qty, 0) }}</td>
            <td>{{ fmt(row.amount) }}</td>
          </tr>
          <tr class="total-row">
            <td class="center">合計</td>
            <td>{{ fmt(data.parts_non_meka.totals.qty, 0) }}</td>
            <td>{{ fmt(data.parts_non_meka.totals.amount) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 5. 総合計 -->
    <div class="mir-section">
      <div class="mir-section-title">総合計</div>
      <table>
        <thead>
          <tr>
            <th class="w-label">区分</th>
            <th>金額（円）</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td class="left">製品（仕掛品＋製品）</td>
            <td>{{ fmt(data.overview_by_kind.totals.total_amount) }}</td>
          </tr>
          <tr>
            <td class="left">部品（メカ）</td>
            <td>{{ fmt(data.parts_meka.totals.amount) }}</td>
          </tr>
          <tr>
            <td class="left">部品（メカ以外）</td>
            <td>{{ fmt(data.parts_non_meka.totals.amount) }}</td>
          </tr>
          <tr class="total-row">
            <td class="left">棚卸金額合計</td>
            <td>{{ fmt(grandTotal) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="mir-footer">※ 本報告書は （実在庫）口径に基づきます</div>
  </div>
</template>

<script lang="ts" setup>
import { computed } from 'vue'
import type { MonthlyInventoryReportData } from '@/api/inventoryValue'

const props = defineProps<{ data: MonthlyInventoryReportData }>()

const grandTotal = computed(() => {
  const prod = props.data.overview_by_kind.totals.total_amount
  const meka = props.data.parts_meka.totals.amount
  const nonMeka = props.data.parts_non_meka.totals.amount
  return Math.round((prod + meka + nonMeka) * 100) / 100
})

function fmt(value: number | undefined | null, decimals = 0): string {
  if (value == null) return '0'
  return Number(value).toLocaleString('ja-JP', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}
</script>

<style scoped>
.mir-page {
  width: 100%;
  max-width: 188mm;
  margin: 0 auto;
  padding: 8px 10px 6px;
  font-family: 'Meiryo', 'Yu Gothic', 'Hiragino Kaku Gothic ProN', sans-serif;
  font-size: 11px;
  color: #0f172a;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  border: 1px solid #d9e3f0;
  border-radius: 8px;
  box-shadow:
    0 10px 26px rgba(15, 23, 42, 0.06),
    0 1px 0 rgba(255, 255, 255, 0.96) inset;
}

.mir-header {
  text-align: center;
  margin-bottom: 3px;
}

.mir-title {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 2px;
  color: #0b3a67;
}

.mir-subtitle {
  font-size: 11px;
  color: #5f6f85;
  margin-top: 1px;
}

.mir-meta {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 4px 10px;
  font-size: 10px;
  color: #3f4f68;
  margin-bottom: 6px;
  padding: 4px 6px;
  background: #eef5ff;
  border: 1px solid #d6e5f7;
  border-radius: 8px;
}

.mir-section {
  margin-bottom: 6px;
  border: 1px solid #d7e2ef;
  border-radius: 6px;
  overflow: hidden;
  background: #fff;
  page-break-inside: avoid;
}

.mir-section-title {
  font-size: 12px;
  font-weight: 700;
  color: #0c4a7d;
  background: linear-gradient(90deg, #e8f3ff 0%, #f4f9ff 100%);
  padding: 4px 8px;
  border-left: 4px solid #2b79c2;
  border-bottom: 1px solid #d7e2ef;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11.5px;
  font-variant-numeric: tabular-nums;
}

th,
td {
  border: 1px solid #d8e1ec;
  padding: 7px 8px;
}

th {
  background: #f3f8fd;
  font-weight: 600;
  text-align: center;
  white-space: nowrap;
  font-size: 11px;
  color: #334155;
}

td {
  text-align: right;
  background: #fff;
}

td.left {
  text-align: left;
}

td.center {
  text-align: center;
}

.w-label {
  width: 86px;
}

.w-kind {
  width: 52px;
}

.w-cd {
  width: 98px;
}

.w-name {
  width: 164px;
}

.total-row {
  background: #edf6ff;
  font-weight: 700;
}

.total-row td {
  border-top: 2px solid #3d86cc;
  background: #edf6ff;
  color: #0f3f6e;
}

.mir-footer {
  text-align: right;
  font-size: 9px;
  color: #6b7f95;
  margin-top: 3px;
}

@media print {
  .mir-page {
    max-width: none;
    border: 0;
    border-radius: 0;
    box-shadow: none;
    background: #fff;
    padding: 0;
  }
}
</style>
