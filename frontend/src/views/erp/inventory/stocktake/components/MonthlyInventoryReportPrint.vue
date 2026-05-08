<template>
  <div class="mir-page">
    <!-- Header -->
    <div class="mir-header">
      <div class="mir-title">棚卸統合報告書</div>
      <div class="mir-subtitle">{{ data.meta.month_label }} 月末実在庫基準</div>
    </div>
    <div class="mir-meta">
      <span>対象日: {{ data.meta.as_of }}</span>
      <span v-if="data.meta.exchange_rate && !data.parts_meka.rows.length">為替レート: {{ data.meta.exchange_rate }}</span>
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

    <!-- 2. 分類別（一般/一般溶接/メカ溶接） -->
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
      <div class="mir-section-title mir-section-title--row">
        <span class="mir-section-title__label">部品（メカ）</span>
        <span v-if="data.meta.exchange_rate" class="mir-section-title__extra">為替レート: {{ data.meta.exchange_rate }}</span>
      </div>
      <table>
        <thead>
          <tr>
            <th class="w-kind">種別</th>
            <th class="w-cd">部品CD</th>
            <th class="w-name">部品名</th>
            <th class="w-unit">単価(ドル)</th>
            <th>本数</th>
            <th>金額</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, idx) in data.parts_meka.rows" :key="idx">
            <td class="center">{{ row.kind }}</td>
            <td class="left">{{ row.part_cd }}</td>
            <td class="left">{{ row.part_name }}</td>
            <td>{{ fmt(row.unit_price, 2) }}</td>
            <td>{{ fmt(row.qty, 0) }}</td>
            <td>{{ fmt(row.amount) }}</td>
          </tr>
          <tr class="total-row">
            <td class="center" colspan="3">合計</td>
            <td class="center">—</td>
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

    <div class="mir-footer">※ 本報告書は （実在庫）口径に基づきます</div>
  </div>
</template>

<script lang="ts" setup>
import type { MonthlyInventoryReportData } from '@/api/inventoryValue'

defineProps<{ data: MonthlyInventoryReportData }>()

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
  padding: 14px 16px 12px;
  font-family: 'Meiryo', 'Yu Gothic', 'Hiragino Kaku Gothic ProN', sans-serif;
  font-size: 12px;
  line-height: 1.45;
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
  margin-bottom: 10px;
}

.mir-title {
  font-size: 19px;
  font-weight: 700;
  letter-spacing: 2px;
  color: #0b3a67;
}

.mir-subtitle {
  font-size: 12px;
  color: #5f6f85;
  margin-top: 4px;
}

.mir-meta {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px 14px;
  font-size: 11px;
  color: #3f4f68;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: #eef5ff;
  border: 1px solid #d6e5f7;
  border-radius: 8px;
}

.mir-section {
  margin-bottom: 14px;
  border: 1px solid #d7e2ef;
  border-radius: 8px;
  overflow: hidden;
  background: #fff;
}

.mir-section-title {
  font-size: 13px;
  font-weight: 700;
  color: #0c4a7d;
  background: linear-gradient(90deg, #e8f3ff 0%, #f4f9ff 100%);
  padding: 8px 12px;
  border-left: 4px solid #2b79c2;
  border-bottom: 1px solid #d7e2ef;
}

.mir-section-title--row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.mir-section-title__extra {
  margin-left: auto;
  font-weight: 600;
  color: #334155;
  font-size: 12px;
}

.mir-section-title__label {
  flex: 0 1 auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12.5px;
  font-variant-numeric: tabular-nums;
}

th,
td {
  border: 1px solid #d8e1ec;
  /* 前回よりさらに約 +15%（12×1.15 / 11×1.15 / lh×1.15） */
  padding: 14px 13px;
  line-height: 1.834;
  vertical-align: middle;
}

th {
  background: #f3f8fd;
  font-weight: 600;
  text-align: center;
  white-space: nowrap;
  font-size: 12px;
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

.w-unit {
  width: 92px;
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
  font-size: 10px;
  color: #6b7f95;
  margin-top: 8px;
  padding-top: 6px;
  border-top: 1px solid #e2e8f0;
}
</style>

<!-- 印刷：html/body のレイアウトは scoped では当たらないためグローバル -->
<style>
@media print {
  /* A4 縦 1 枚・分割なし：適度な行高で読みやすく、ページ立ち上がり〜フッタまで縦を使う */
  @page {
    size: A4 portrait;
    /* 上 2cm · 下 1cm · 左右 8mm */
    margin: 2cm 8mm 1cm 8mm;
  }

  html {
    zoom: 1.0;
    height: 100%;
  }

  body {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  .mir-page {
    flex: 1 1 auto;
    display: flex;
    flex-direction: column;
    max-width: none;
    width: 100%;
    /* A4 縦 297mm − 上20mm − 下10mm ≒ 印字可能高さ */
    min-height: 267mm;
    border: 0;
    border-radius: 0;
    box-shadow: none;
    background: #fff;
    padding: 2mm 0 3mm;
    box-sizing: border-box;
    page-break-after: avoid;
    page-break-inside: avoid;
    break-inside: avoid;
  }

  .mir-header {
    flex-shrink: 0;
    margin-bottom: 6px;
  }

  .mir-title {
    font-size: 17px;
    letter-spacing: 1px;
  }

  .mir-subtitle {
    font-size: 10.5px;
    margin-top: 2px;
    line-height: 1.4;
  }

  .mir-meta {
    flex-shrink: 0;
    gap: 6px 10px;
    font-size: 10px;
    margin-bottom: 8px;
    padding: 6px 10px;
    border-radius: 6px;
    line-height: 1.4;
  }

  .mir-section {
    flex-shrink: 0;
    margin-bottom: 8px;
    border-radius: 6px;
    page-break-inside: auto;
    break-inside: auto;
  }

  .mir-section-title {
    font-size: 11.5px;
    padding: 6px 10px;
    border-left-width: 3px;
    line-height: 1.35;
  }

  .mir-section-title--row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }

  .mir-section-title__extra {
    margin-left: auto;
    font-weight: 600;
    color: #334155;
    font-size: 10px;
  }

  .mir-page table {
    font-size: 10.5px;
  }

  .mir-page th,
  .mir-page td {
    padding: 9px 10px;
    line-height: 1.834;
  }

  .mir-page th {
    font-size: 10px;
  }

  .mir-footer {
    flex-shrink: 0;
    margin-top: auto;
    font-size: 9px;
    padding-top: 8px;
    margin-bottom: 0;
    border-top: 1px solid #e2e8f0;
    line-height: 1.4;
  }
}
</style>
