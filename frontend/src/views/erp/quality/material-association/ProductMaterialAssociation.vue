<template>
  <div class="pma">
    <header class="pma-bar">
      <div class="pma-bar__left">
        <div class="pma-bar__icon" aria-hidden="true">
          <el-icon :size="22"><Box /></el-icon>
        </div>
        <div class="pma-bar__titles">
          <h1 class="pma-bar__title">製品材料照会</h1>
          <p class="pma-bar__hint">カンバン発行と切断・受入ログを突合して照会します</p>
        </div>
      </div>
      <div class="pma-bar__right">
        <span class="pma-pill">{{ total.toLocaleString() }} 件</span>
        <el-button class="pma-btn pma-btn--help" size="small" :icon="Reading" @click="goToHelp">
          操作説明
        </el-button>
        <el-button
          class="pma-btn pma-btn--print"
          size="small"
          :icon="Printer"
          :loading="printLoading"
          :disabled="printLoading || !total"
          @click="handlePrint"
        >
          印刷
        </el-button>
        <el-button
          class="pma-btn pma-btn--refresh"
          type="success"
          size="small"
          :icon="Refresh"
          :loading="loading"
          @click="fetchList"
        >
          再読込
        </el-button>
      </div>
    </header>

    <section class="pma-filters" aria-label="検索条件">
      <el-input
        v-model="keyword"
        placeholder="キーワード（CD・名・材料・管理コード・看板No）"
        clearable
        :prefix-icon="Search"
        size="small"
        class="pma-filters__kw"
        @keyup.enter="onSearch"
      />
      <el-select
        v-model="filters.product_cd"
        placeholder="製品"
        clearable
        filterable
        size="small"
        class="pma-filters__prod"
        @change="onSearch"
      >
        <el-option
          v-for="p in productOptions"
          :key="p.product_cd"
          :label="`${p.product_cd} ${p.product_name || ''}`"
          :value="p.product_cd"
        />
      </el-select>
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="～"
        start-placeholder="切断開始（開始）"
        end-placeholder="切断開始（終了）"
        value-format="YYYY-MM-DD"
        size="small"
        class="pma-filters__date"
      />
      <el-button class="pma-btn pma-btn--search" type="primary" size="small" :icon="Search" @click="onSearch">
        検索
      </el-button>
      <el-button class="pma-btn pma-btn--clear" size="small" @click="onClear">クリア</el-button>
    </section>

    <div class="pma-table-shell">
      <el-table
        class="pma-table"
        :data="list"
        v-loading="loading"
        border
        stripe
        size="small"
        :height="tableHeight"
      >
        <el-table-column label="製品CD" prop="product_cd" width="70" show-overflow-tooltip />
        <el-table-column label="製品名" prop="product_name" width="120" show-overflow-tooltip />
        <el-table-column label="ライン" prop="production_line" width="70" show-overflow-tooltip />
        <el-table-column label="切断機" prop="cutting_machine" width="70" show-overflow-tooltip />
        <el-table-column label="原材料" prop="material_name" width="128" show-overflow-tooltip />
        <el-table-column label="規格" prop="standard_specification" width="88" show-overflow-tooltip />
        <el-table-column label="管理コード" prop="management_code" width="150" show-overflow-tooltip />
        <el-table-column label="材料製造番号" width="120" show-overflow-tooltip>
          <template #default="{ row }">
            {{ toPlainCodeDisplay(row.cutting_log_manufacture_no) }}
          </template>
        </el-table-column>
        <el-table-column label="切断開始日" prop="cutting_log_date" width="100" />
        <el-table-column label="切断開始時刻" prop="cutting_log_time" width="100" />
        <el-table-column label="材料製造日" prop="material_log_manufacture_date" width="100" />
        <el-table-column label="仕入先" prop="material_log_supplier" width="100" show-overflow-tooltip />
        <el-table-column label="看板発行日" prop="issue_date" width="100" />
        <el-table-column label="生産数" prop="actual_production_quantity" width="70" align="right" />
      </el-table>
      <div class="pma-pager">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[20, 50, 100, 200, 500]"
          layout="total, sizes, prev, pager, next"
          small
          background
          @current-change="fetchList"
          @size-change="onSizeChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Box, Printer, Reading, Refresh, Search } from '@element-plus/icons-vue'
import {
  getProductMaterialAssociation,
  getProductMaterialProducts,
  type ProductMaterialAssociationParams,
} from '@/api/material'
import type { ProductMaterialAssociationItem } from '@/types/material'
import { toPlainCodeDisplay } from '@/utils/plainCodeDisplay'

/**
 * 打印表格宽度怎么改（製品材料照会）：
 * 1. 可打印区域变宽：改 `PRINT_DOCUMENT_STYLES` 里 `@page { margin: … }`（边距越小，表越宽）。
 * 2. 表占页面宽度：改 `.print-table { width: … }`（如 100%、98%）。
 * 3. 各列比例：改下面 `PRINT_TABLE_COLGROUP` 每个 col 的 width %（合计建议 100%，与 table-layout:fixed 配合）。
 */
const PRINT_TABLE_COLGROUP = `
  <colgroup>
    <col style="width:5%" />
    <col style="width:9%" />
    <col style="width:4%" />
    <col style="width:5%" />
    <col style="width:10%" />
    <col style="width:7%" />
    <col style="width:12%" />
    <col style="width:9%" />
    <col style="width:6%" />
    <col style="width:6%" />
    <col style="width:6%" />
    <col style="width:8%" />
    <col style="width:6%" />
    <col style="width:5%" />
  </colgroup>`

const PRINT_DOCUMENT_STYLES = `
    @page { size: A4 landscape; margin: 8mm; }
    body { font-family: 'Meiryo', 'Yu Gothic', 'Microsoft YaHei', sans-serif; margin: 0; padding: 0; font-size: 8pt; }
    .print-header { text-align: center; margin-bottom: 4mm; border-bottom: 1.5px solid #333; padding-bottom: 2mm; }
    .print-title { font-size: 14pt; font-weight: bold; }
    .print-date { font-size: 8pt; color: #666; margin-top: 1mm; }
    .print-table { width: 100%; border-collapse: collapse; margin-top: 3mm; font-size: 7pt; table-layout: fixed; }
    .print-table th, .print-table td { border: 1px solid #333; padding: 1.2mm 0.8mm; text-align: center; word-wrap: break-word; overflow-wrap: break-word; }
    .print-table th { background: #f0f0f0; font-weight: bold; }
    .print-table .text-left { text-align: left; }
    .print-table .num { text-align: right; }
    @media print {
      body { margin: 0; padding: 0; }
      .print-table tr { page-break-inside: avoid; }
      .print-table thead { display: table-header-group; }
    }
`

const router = useRouter()

const goToHelp = () => {
  router.push({ name: 'QualityProductMaterialAssociationHelp' })
}

const loading = ref(false)
const printLoading = ref(false)
const keyword = ref('')
const dateRange = ref<[string, string] | null>(null)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const list = ref<ProductMaterialAssociationItem[]>([])
const productOptions = ref<{ product_cd: string; product_name?: string }[]>([])

/** ヘッダー＋検索＋余白を除いたテーブル高さ（画面を有効活用） */
const tableHeight = computed(() => 'calc(100vh - 158px)')

const filters = reactive({
  product_cd: '' as string,
})

const fetchList = async () => {
  loading.value = true
  try {
    const [startDate, endDate] = dateRange.value ?? [undefined, undefined]
    const params: ProductMaterialAssociationParams = {
      page: page.value,
      pageSize: pageSize.value,
      keyword: keyword.value.trim() || undefined,
      product_cd: filters.product_cd || undefined,
      startDate,
      endDate,
    }
    const res = await getProductMaterialAssociation(params)
    list.value = res?.data?.list ?? []
    total.value = res?.data?.total ?? 0
  } catch (e: unknown) {
    const msg =
      e && typeof e === 'object' && 'response' in e
        ? String((e as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? '')
        : ''
    ElMessage.error(msg || '一覧の取得に失敗しました')
  } finally {
    loading.value = false
  }
}

const fetchProducts = async () => {
  try {
    const res = await getProductMaterialProducts()
    productOptions.value = res?.data ?? []
  } catch {
    /* noop */
  }
}

const onSearch = () => {
  page.value = 1
  fetchList()
}

const onSizeChange = () => {
  page.value = 1
  fetchList()
}

const onClear = () => {
  keyword.value = ''
  dateRange.value = null
  filters.product_cd = ''
  onSearch()
}

function escHtml(s: unknown): string {
  if (s == null || s === '') return '-'
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function buildListParamsForPrint(): ProductMaterialAssociationParams {
  const [startDate, endDate] = dateRange.value ?? [undefined, undefined]
  return {
    keyword: keyword.value.trim() || undefined,
    product_cd: filters.product_cd || undefined,
    startDate,
    endDate,
    page: 1,
    pageSize: Math.min(Math.max(total.value, 1), 20000),
  }
}

function generatePrintHtml(data: ProductMaterialAssociationItem[]): string {
  const printDate = new Date().toLocaleString('ja-JP', {
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
  const rows = data
    .map(
      (r) => `
    <tr>
      <td>${escHtml(r.product_cd)}</td>
      <td class="text-left">${escHtml(r.product_name)}</td>
      <td>${escHtml(r.production_line)}</td>
      <td>${escHtml(r.cutting_machine)}</td>
      <td class="text-left">${escHtml(r.material_name)}</td>
      <td class="text-left">${escHtml(r.standard_specification)}</td>
      <td class="text-left">${escHtml(r.management_code)}</td>
      <td class="text-left">${escHtml(toPlainCodeDisplay(r.cutting_log_manufacture_no))}</td>
      <td>${escHtml(r.cutting_log_date)}</td>
      <td>${escHtml(r.cutting_log_time)}</td>
      <td>${escHtml(r.material_log_manufacture_date)}</td>
      <td class="text-left">${escHtml(r.material_log_supplier)}</td>
      <td>${escHtml(r.issue_date)}</td>
      <td class="num">${r.actual_production_quantity ?? ''}</td>
    </tr>`,
    )
    .join('')
  return `
    <div class="print-header">
      <div class="print-title">製品材料照会</div>
      <div class="print-date">印刷日時: ${escHtml(printDate)}　件数: ${data.length}件（切断開始日付・時間の昇順）</div>
    </div>
    <table class="print-table">
      ${PRINT_TABLE_COLGROUP}
      <thead>
        <tr>
          <th>製品CD</th>
          <th>製品名</th>
          <th>ライン</th>
          <th>切断機</th>
          <th>原材料</th>
          <th>規格</th>
          <th>管理コード</th>
          <th>製造番号</th>
          <th>切断開始日付</th>
          <th>切断開始時間</th>
          <th>材料製造日</th>
          <th>仕入先</th>
          <th>看板発行日</th>
          <th>生産数</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>`
}

const handlePrint = async () => {
  if (!total.value) {
    ElMessage.warning('印刷するデータがありません')
    return
  }
  if (total.value > 20000) {
    ElMessage.warning('件数が20,000件を超えています。先頭20,000件のみ印刷します。')
  }
  printLoading.value = true
  try {
    const params = buildListParamsForPrint()
    const res = await getProductMaterialAssociation(params)
    const allData = res?.data?.list ?? []
    if (!allData.length) {
      ElMessage.warning('印刷するデータがありません')
      return
    }
    const printContent = generatePrintHtml(allData)
    const printWindow = window.open('', '_blank')
    if (printWindow) {
      printWindow.document.write(`<!DOCTYPE html>
<html>
<head>
  <title>製品材料照会 - 印刷</title>
  <meta charset="UTF-8" />
  <style>${PRINT_DOCUMENT_STYLES}</style>
</head>
<body>${printContent}</body>
</html>`)
      printWindow.document.close()
      printWindow.onload = () => {
        printWindow.print()
        setTimeout(() => printWindow.close(), 500)
      }
    } else {
      ElMessage.error('印刷ウィンドウを開けませんでした')
    }
  } catch {
    ElMessage.error('印刷中にエラーが発生しました')
  } finally {
    printLoading.value = false
  }
}

onMounted(() => {
  fetchProducts()
  fetchList()
})
</script>

<style scoped>
.pma {
  --pma-surface: #ffffff;
  --pma-border: #e2e8f0;
  --pma-muted: #64748b;
  --pma-accent: #0ea5e9;
  --pma-accent-soft: #e0f2fe;
  padding: 6px 8px 8px;
  min-height: 100%;
  box-sizing: border-box;
  background: linear-gradient(160deg, #f1f5f9 0%, #e8eef5 48%, #f8fafc 100%);
}

.pma-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px 12px;
  padding: 8px 12px;
  margin-bottom: 6px;
  background: var(--pma-surface);
  border: 1px solid var(--pma-border);
  border-radius: 10px;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 4px 12px rgba(15, 23, 42, 0.05);
}

.pma-bar__left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.pma-bar__icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: linear-gradient(145deg, #38bdf8 0%, #0ea5e9 55%, #0284c7 100%);
  color: #fff;
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.35);
}

.pma-bar__titles {
  min-width: 0;
}

.pma-bar__title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.03em;
  color: #0f172a;
  line-height: 1.25;
}

.pma-bar__hint {
  margin: 2px 0 0;
  font-size: 11px;
  line-height: 1.35;
  color: var(--pma-muted);
}

.pma-bar__right {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

/* ツールバー・検索行のボタン（役割ごとに色分け） */
.pma-btn {
  font-weight: 600;
  border-radius: 8px;
  transition:
    transform 0.12s ease,
    box-shadow 0.12s ease,
    filter 0.12s ease;
}

.pma-btn:not(:disabled):active {
  transform: translateY(1px);
}

.pma-btn--help.el-button {
  --el-button-bg-color: transparent;
  --el-button-border-color: #a5b4fc;
  --el-button-text-color: #4338ca;
  --el-button-hover-bg-color: #eef2ff;
  --el-button-hover-border-color: #818cf8;
  --el-button-hover-text-color: #3730a3;
  --el-button-active-border-color: #6366f1;
  background: linear-gradient(180deg, #f5f7ff 0%, #eef2ff 100%);
  border-width: 1px;
  box-shadow: 0 1px 2px rgba(67, 56, 202, 0.08);
}

.pma-btn--help.el-button:hover {
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.18);
}

.pma-btn--print.el-button {
  --el-button-bg-color: #ffffff;
  --el-button-border-color: #cbd5e1;
  --el-button-text-color: #475569;
  --el-button-hover-bg-color: #f8fafc;
  --el-button-hover-border-color: #94a3b8;
  --el-button-hover-text-color: #334155;
  --el-button-disabled-bg-color: #f1f5f9;
  --el-button-disabled-border-color: #e2e8f0;
  --el-button-disabled-text-color: #94a3b8;
  border-width: 1px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
}

.pma-btn--print.el-button:hover:not(.is-disabled) {
  box-shadow: 0 2px 6px rgba(15, 23, 42, 0.08);
}

.pma-btn--refresh.el-button {
  --el-button-bg-color: #0d9488;
  --el-button-border-color: #0f766e;
  --el-button-hover-bg-color: #0f766e;
  --el-button-hover-border-color: #115e59;
  --el-button-active-bg-color: #115e59;
  --el-button-active-border-color: #134e4a;
  background: linear-gradient(165deg, #14b8a6 0%, #0d9488 45%, #0f766e 100%);
  border-width: 1px;
  box-shadow: 0 2px 8px rgba(13, 148, 136, 0.35);
}

.pma-btn--refresh.el-button:hover:not(.is-disabled) {
  filter: brightness(1.05);
  box-shadow: 0 3px 12px rgba(13, 148, 136, 0.4);
}

.pma-btn--refresh.el-button.is-disabled {
  filter: none;
  box-shadow: none;
  opacity: 0.65;
}

.pma-btn--search.el-button {
  background: linear-gradient(165deg, #38bdf8 0%, #0ea5e9 48%, #0284c7 100%);
  border-width: 1px;
  border-color: #0369a1;
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.35);
}

.pma-btn--search.el-button:hover:not(.is-disabled) {
  filter: brightness(1.04);
  box-shadow: 0 3px 12px rgba(14, 165, 233, 0.42);
}

.pma-btn--search.el-button.is-disabled {
  filter: none;
  box-shadow: none;
  opacity: 0.65;
}

.pma-btn--clear.el-button {
  --el-button-bg-color: #fffbeb;
  --el-button-border-color: #fcd34d;
  --el-button-text-color: #b45309;
  --el-button-hover-bg-color: #fef3c7;
  --el-button-hover-border-color: #fbbf24;
  --el-button-hover-text-color: #92400e;
  --el-button-active-border-color: #d97706;
  border-width: 1px;
  box-shadow: 0 1px 2px rgba(180, 83, 9, 0.08);
}

.pma-btn--clear.el-button:hover {
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.2);
}

.pma-pill {
  display: inline-flex;
  align-items: center;
  padding: 3px 11px;
  font-size: 12px;
  font-weight: 600;
  color: #0369a1;
  background: var(--pma-accent-soft);
  border-radius: 999px;
  border: 1px solid rgba(14, 165, 233, 0.22);
  margin-right: 2px;
}

.pma-filters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  margin-bottom: 6px;
  background: var(--pma-surface);
  border: 1px solid var(--pma-border);
  border-radius: 10px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.pma-filters__kw {
  flex: 1 1 180px;
  min-width: 160px;
  max-width: 320px;
}

.pma-filters__prod {
  width: 200px;
}

.pma-filters__date {
  width: 248px;
}

.pma-table-shell {
  background: var(--pma-surface);
  border: 1px solid var(--pma-border);
  border-radius: 10px;
  overflow: hidden;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 4px 14px rgba(15, 23, 42, 0.06);
}

.pma-pager {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 4px 8px 6px;
  border-top: 1px solid #f1f5f9;
  background: #fafbfc;
}

.pma-table :deep(.el-table__header th) {
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%) !important;
  color: #334155 !important;
  font-weight: 600 !important;
  font-size: 12px !important;
  padding: 6px 4px !important;
}

.pma-table :deep(.el-table__body td) {
  font-size: 12px !important;
  padding: 4px 6px !important;
}

.pma-table :deep(.el-table__row) {
  --el-table-row-hover-bg-color: #f0f9ff;
}
</style>
