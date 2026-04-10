<template>
  <div class="material-logs-container">
    <header class="page-hero">
      <div class="page-hero__main">
        <div class="page-hero__brand">
          <div class="page-hero__icon" aria-hidden="true">
            <el-icon :size="20"><Document /></el-icon>
          </div>
          <div class="page-hero__titles">
            <h1 class="page-hero__title">材料受入履歴</h1>
            <p class="page-hero__sub">材料の受入・検品を管理します</p>
          </div>
        </div>
        <div class="page-hero__stats" role="status">
          <div class="stat-pill stat-pill--total">
            <el-icon class="stat-pill__ico"><DataBoard /></el-icon>
            <div class="stat-pill__text">
              <span class="stat-pill__num">{{ totalCount }}</span>
              <span class="stat-pill__lbl">総件数</span>
            </div>
          </div>
          <div class="stat-pill stat-pill--page">
            <el-icon class="stat-pill__ico"><View /></el-icon>
            <div class="stat-pill__text">
              <span class="stat-pill__num">{{ filteredCount || 0 }}</span>
              <span class="stat-pill__lbl">表示件数</span>
            </div>
          </div>
        </div>
      </div>
    </header>

    <section class="filter-card">
      <div class="filter-card__bar">
        <div class="filter-card__title">
          <el-icon><Search /></el-icon>
          <span>検索・フィルター</span>
        </div>
        <div class="filter-card__actions">
          <el-button size="small" @click="clearFilters" icon="Refresh">クリア</el-button>
          <el-button size="small" @click="showColumnSettings" icon="Setting">列設定</el-button>
          <el-button
            size="small"
            @click="handlePrint"
            :loading="printLoading"
            :disabled="printLoading || !totalCount"
          >
            <el-icon><Printer /></el-icon>
            印刷
          </el-button>
          <el-button
            type="primary"
            size="small"
            @click="importCSVData"
            :loading="importLoading"
            icon="Upload"
          >
            データ読取
          </el-button>
        </div>
      </div>
      <div class="filter-card__body">
        <div class="filter-grid">
          <div class="filter-field filter-field--grow">
            <label class="field-label">
              <el-icon><Search /></el-icon>
              キーワード
            </label>
            <el-input
              v-model="filters.keyword"
              placeholder="材料名・仕入先・製造番号"
              clearable
              size="small"
              @input="handleSearch"
              class="field-control"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>
          <div class="filter-field">
            <label class="field-label">
              <el-icon><Calendar /></el-icon>
              期間
            </label>
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="～"
              start-placeholder="開始"
              end-placeholder="終了"
              format="YYYY/MM/DD"
              value-format="YYYY-MM-DD"
              @change="handleDateChange"
              class="field-control field-control--date"
              size="small"
            />
          </div>
          <div class="filter-field filter-field--grow">
            <label class="field-label">
              <el-icon><Operation /></el-icon>
              仕入先
            </label>
            <el-select
              v-model="filters.supplier"
              placeholder="複数選択可"
              clearable
              multiple
              collapse-tags
              collapse-tags-tooltip
              size="small"
              @change="handleSearch"
              class="field-control"
            >
              <el-option
                v-for="supplier in supplierList"
                :key="supplier.value"
                :label="supplier.label"
                :value="supplier.value"
              />
            </el-select>
          </div>
          <div class="filter-field filter-field--sort">
            <label class="field-label">
              <el-icon><Sort /></el-icon>
              並び順
            </label>
            <div class="sort-row">
              <el-select
                v-model="sortField"
                placeholder="項目"
                clearable
                size="small"
                @change="handleSortChange"
                class="sort-row__field"
              >
                <el-option label="材料名" value="material_name" />
                <el-option label="日付" value="log_date" />
                <el-option label="製造日" value="manufacture_date" />
                <el-option label="仕入先" value="supplier" />
              </el-select>
              <el-select
                v-model="sortOrder"
                placeholder="順"
                size="small"
                @change="handleSortChange"
                class="sort-row__order"
                :disabled="!sortField"
              >
                <el-option label="昇順" value="asc" />
                <el-option label="降順" value="desc" />
              </el-select>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="table-card">
      <div class="table-card__bar">
        <div class="table-card__title">
          <el-icon><List /></el-icon>
          <span>材料ログ一覧</span>
          <el-tag v-if="totalCount > 0" type="info" effect="plain" size="small" class="table-card__tag">
            {{ totalCount }}件
          </el-tag>
        </div>
      </div>
      <div class="table-card__body">
        <el-table
          :data="tableData || []"
          v-loading="loading"
          stripe
          highlight-current-row
          @row-click="showDetail"
          class="modern-table"
          size="small"
          :header-cell-style="{
            background: '#f1f5f9',
            color: '#334155',
            fontWeight: '600',
            fontSize: '12px',
            borderBottom: '1px solid #e2e8f0',
            padding: '6px 0',
          }"
        >
          <el-table-column
            v-if="visibleColumns.log_date"
            prop="log_date"
            label="日付"
            width="120"
            align="center"
          />
          <el-table-column
            v-if="visibleColumns.log_time"
            prop="log_time"
            label="時間"
            width="100"
            align="center"
          />
          <el-table-column
            v-if="visibleColumns.item"
            prop="item"
            label="項目"
            width="120"
            align="center"
          >
            <template #default="{ row }">
              <el-tag :type="getItemType(row.item)" size="small">{{ row.item }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column
            v-if="visibleColumns.material_cd"
            prop="material_cd"
            label="材料CD"
            width="120"
            align="center"
          />
          <el-table-column
            v-if="visibleColumns.material_name"
            prop="material_name"
            label="材料名"
            min-width="160"
            show-overflow-tooltip
          />
          <el-table-column
            v-if="visibleColumns.process_cd"
            prop="process_cd"
            label="工程CD"
            width="120"
            align="center"
          />
          <el-table-column
            v-if="visibleColumns.manufacture_no"
            prop="manufacture_no"
            label="製造番号"
            width="150"
            align="center"
          />
          <el-table-column
            v-if="visibleColumns.manufacture_date"
            prop="manufacture_date"
            label="製造日"
            width="120"
            align="center"
          />
          <el-table-column
            v-if="visibleColumns.pieces_per_bundle"
            prop="pieces_per_bundle"
            label="束当り枚数"
            width="120"
            align="center"
          />
          <el-table-column
            v-if="visibleColumns.length"
            prop="length"
            label="長さ"
            width="100"
            align="center"
          />
          <el-table-column
            v-if="visibleColumns.quantity"
            prop="quantity"
            label="数量"
            width="100"
            align="center"
          />
          <el-table-column
            v-if="visibleColumns.bundle_quantity"
            prop="bundle_quantity"
            label="束数"
            width="100"
            align="center"
          />
          <el-table-column
            v-if="visibleColumns.outer_diameter1"
            prop="outer_diameter1"
            label="外径1"
            width="100"
            align="center"
          />
          <el-table-column
            v-if="visibleColumns.outer_diameter2"
            prop="outer_diameter2"
            label="外径2"
            width="100"
            align="center"
          />
          <el-table-column
            v-if="visibleColumns.supplier"
            prop="supplier"
            label="仕入先"
            width="150"
            align="center"
          />
          <el-table-column
            v-if="visibleColumns.material_quality"
            prop="material_quality"
            label="材料規格"
            width="150"
            align="center"
          />
          <el-table-column
            v-if="visibleColumns.magnetic"
            prop="magnetic"
            label="磁気"
            width="80"
            align="center"
          >
            <template #default="{ row }">
              <el-tag :type="row.magnetic ? 'success' : 'info'" size="small">
                {{ row.magnetic ? '有' : '無' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            v-if="visibleColumns.appearance"
            prop="appearance"
            label="外観"
            width="80"
            align="center"
          >
            <template #default="{ row }">
              <el-tag :type="row.appearance ? 'success' : 'info'" size="small">
                {{ row.appearance ? '良' : '不良' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            v-if="visibleColumns.hd_no"
            prop="hd_no"
            label="HD番号"
            width="170"
            align="center"
          />
          <el-table-column
            v-if="visibleColumns.remarks"
            prop="remarks"
            label="作業員"
            width="200"
            align="center"
            show-overflow-tooltip
          />
          <el-table-column
            v-if="visibleColumns.note"
            prop="note"
            label="ノート"
            width="200"
            align="center"
            show-overflow-tooltip
          />
          <el-table-column
            v-if="visibleColumns.created_at"
            prop="created_at"
            label="作成日時"
            width="160"
            align="center"
          />
          <el-table-column
            v-if="visibleColumns.updated_at"
            prop="updated_at"
            label="更新日時"
            width="160"
            align="center"
          />
        </el-table>

        <div class="pagination-bar">
          <span class="pagination-bar__info">
            {{ pagination.pageSize * (pagination.page - 1) + 1 }} -
            {{ Math.min(pagination.pageSize * pagination.page, totalCount) }} 件 / 全 {{ totalCount }} 件
          </span>
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="totalCount || 0"
            layout="sizes, prev, pager, next, jumper"
            small
            @size-change="handlePageSizeChange"
            @current-change="handlePageChange"
            class="modern-pagination"
          />
        </div>
      </div>
    </section>

    <el-dialog
      v-model="detailVisible"
      title="材料ログ詳細"
      width="520px"
      class="logs-dialog"
      align-center
      destroy-on-close
    >
      <div v-if="selectedLog" class="detail-content">
        <div class="detail-row">
          <label>項目:</label>
          <span>{{ selectedLog.item }}</span>
        </div>
        <div class="detail-row">
          <label>材料CD:</label>
          <span>{{ selectedLog.material_cd }}</span>
        </div>
        <div class="detail-row">
          <label>材料名:</label>
          <span>{{ selectedLog.material_name }}</span>
        </div>
        <div class="detail-row">
          <label>工程CD:</label>
          <span>{{ selectedLog.process_cd }}</span>
        </div>
        <div class="detail-row">
          <label>日時:</label>
          <span>{{ selectedLog.log_date }} {{ selectedLog.log_time }}</span>
        </div>
        <div class="detail-row">
          <label>数量:</label>
          <span>{{ selectedLog.quantity }}</span>
        </div>
        <div class="detail-row">
          <label>HD番号:</label>
          <span>{{ selectedLog.hd_no || '-' }}</span>
        </div>
        <div class="detail-row">
          <label>備考:</label>
          <span>{{ selectedLog.remarks || '-' }}</span>
        </div>
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">閉じる</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="columnSettingsVisible"
      title="列表示設定"
      width="480px"
      class="logs-dialog logs-dialog--columns"
      align-center
      destroy-on-close
    >
      <div class="column-settings">
        <div class="column-group">
          <h4>基本情報</h4>
          <el-checkbox v-model="visibleColumns.log_date">日付</el-checkbox>
          <el-checkbox v-model="visibleColumns.log_time">時間</el-checkbox>
          <el-checkbox v-model="visibleColumns.item">項目</el-checkbox>
          <el-checkbox v-model="visibleColumns.material_cd">材料CD</el-checkbox>
          <el-checkbox v-model="visibleColumns.material_name">材料名</el-checkbox>
          <el-checkbox v-model="visibleColumns.process_cd">工程CD</el-checkbox>
        </div>

        <div class="column-group">
          <h4>製造情報</h4>
          <el-checkbox v-model="visibleColumns.manufacture_no">製造番号</el-checkbox>
          <el-checkbox v-model="visibleColumns.manufacture_date">製造日</el-checkbox>
          <el-checkbox v-model="visibleColumns.pieces_per_bundle">束当り枚数</el-checkbox>
          <el-checkbox v-model="visibleColumns.length">長さ</el-checkbox>
        </div>

        <div class="column-group">
          <h4>数量・品質</h4>
          <el-checkbox v-model="visibleColumns.quantity">数量</el-checkbox>
          <el-checkbox v-model="visibleColumns.bundle_quantity">束数</el-checkbox>
          <el-checkbox v-model="visibleColumns.outer_diameter1">外径1</el-checkbox>
          <el-checkbox v-model="visibleColumns.outer_diameter2">外径2</el-checkbox>
          <el-checkbox v-model="visibleColumns.magnetic">磁気</el-checkbox>
          <el-checkbox v-model="visibleColumns.appearance">外観</el-checkbox>
        </div>

        <div class="column-group">
          <h4>仕入先・規格</h4>
          <el-checkbox v-model="visibleColumns.supplier">仕入先</el-checkbox>
          <el-checkbox v-model="visibleColumns.material_quality">材料規格</el-checkbox>
        </div>

        <div class="column-group">
          <h4>その他</h4>
          <el-checkbox v-model="visibleColumns.hd_no">HD番号</el-checkbox>
          <el-checkbox v-model="visibleColumns.remarks">備考</el-checkbox>
          <el-checkbox v-model="visibleColumns.note">ノート</el-checkbox>
          <el-checkbox v-model="visibleColumns.created_at">作成日時</el-checkbox>
          <el-checkbox v-model="visibleColumns.updated_at">更新日時</el-checkbox>
        </div>
      </div>
      <template #footer>
        <el-button @click="resetColumnSettings">リセット</el-button>
        <el-button @click="columnSettingsVisible = false">キャンセル</el-button>
        <el-button type="primary" @click="saveColumnSettings">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Document,
  DataBoard,
  View,
  Search,
  Calendar,
  Operation,
  List,
  Sort,
  Printer,
} from '@element-plus/icons-vue'
import { getMaterialLogs, importMaterialLogsFromCSV, getSupplierList } from '@/api/material'
import type { MaterialLog, MaterialLogSearchParams } from '@/types/material'

// 响应式数据
const loading = ref(false)
const importLoading = ref(false)
const printLoading = ref(false)
const tableData = ref<MaterialLog[]>([])
const totalCount = ref(0)
const dateRange = ref<[string, string] | undefined>(undefined)
const detailVisible = ref(false)
const selectedLog = ref<MaterialLog | null>(null)
const columnSettingsVisible = ref(false)
const supplierList = ref<{ label: string; value: string }[]>([])

// 排序控制
const sortField = ref<string>('')
const sortOrder = ref<'asc' | 'desc'>('desc')

// 列显示控制
const visibleColumns = ref({
  log_date: true,
  log_time: true,
  item: true,
  material_cd: false,
  material_name: true,
  process_cd: false,
  manufacture_no: true,
  manufacture_date: false,
  pieces_per_bundle: false,
  length: false,
  quantity: true,
  bundle_quantity: false,
  outer_diameter1: true,
  outer_diameter2: true,
  supplier: true,
  material_quality: false,
  magnetic: false,
  appearance: false,
  hd_no: false,
  remarks: false,
  note: false,
  created_at: false,
  updated_at: false,
})

// 筛选器
const filters = ref<MaterialLogSearchParams>({
  keyword: '',
  start_date: '',
  end_date: '',
  supplier: [],
  page: 1,
  page_size: 20,
})

// 分页
const pagination = ref({
  page: 1,
  pageSize: 20,
})

// 计算属性
const filteredCount = computed(() => tableData.value?.length || 0)

// 方法
const fetchSuppliers = async () => {
  try {
    const result = await getSupplierList()
    const arr = result?.data ?? []
    supplierList.value = arr.map((s: string) => ({ label: s, value: s }))
  } catch (error) {
    console.error('仕入先リストの取得に失敗しました:', error)
    supplierList.value = []
  }
}

const fetchLogs = async () => {
  loading.value = true
  try {
    // 处理多选供应商：如果是数组且不为空，转换为逗号分隔的字符串；否则传 undefined 以符合 ReceivingListParams.supplier (string | undefined)
    const supplierParam: string | undefined =
      Array.isArray(filters.value.supplier) && filters.value.supplier.length > 0
        ? filters.value.supplier.join(',')
        : undefined

    const params: import('@/api/material').ReceivingListParams = {
      keyword: filters.value.keyword || undefined,
      startDate: filters.value.start_date || undefined,
      endDate: filters.value.end_date || undefined,
      supplier: supplierParam,
      page: pagination.value.page,
      pageSize: pagination.value.pageSize,
    }
    const result = await getMaterialLogs(params)
    const data = result?.data
    const list = data?.list ?? (Array.isArray((result as any)?.data) ? (result as any).data : [])
    tableData.value = list
    totalCount.value = data?.total ?? (result as any)?.total ?? 0
  } catch (error: any) {
    console.error('データの取得に失敗しました:', error)
    ElMessage.error(`データの取得に失敗しました: ${error.message}`)
    tableData.value = []
    totalCount.value = 0
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.value.page = 1
  fetchLogs()
}

const handleDateChange = (dates: [string, string] | null) => {
  dateRange.value = dates || undefined
  if (dates && dates.length === 2) {
    filters.value.start_date = dates[0]
    filters.value.end_date = dates[1]
  } else {
    filters.value.start_date = ''
    filters.value.end_date = ''
  }
  handleSearch()
}

const clearFilters = () => {
  filters.value = {
    keyword: '',
    start_date: '',
    end_date: '',
    supplier: [],
    page: 1,
    page_size: 20,
  }
  dateRange.value = undefined
  sortField.value = ''
  sortOrder.value = 'desc'
  pagination.value.page = 1
  fetchLogs()
}

const handleSortChange = () => {
  pagination.value.page = 1
  fetchLogs()
}

const importCSVData = async () => {
  try {
    await ElMessageBox.confirm('CSVファイルから材料ログデータを読み込みますか？', '確認', {
      type: 'info',
      confirmButtonText: 'はい',
      cancelButtonText: 'キャンセル',
    })

    importLoading.value = true
    const result = await importMaterialLogsFromCSV([]) as { success?: boolean; data?: { fileResults?: { fileName: string; processedCount?: number; success?: boolean; error?: string }[]; totalProcessed?: number }; message?: string }

    // 检查响应是否成功
    if (result && result.success === true) {
      // 如果有详细数据，显示详细结果
      if (result.data?.fileResults?.length) {
        let detailMessage = 'データ読取完了:\n'
        result.data.fileResults.forEach(
          (fileResult: {
            fileName: string
            processedCount?: number
            success?: boolean
            error?: string
          }) => {
            if (fileResult.success === false && fileResult.error) {
              detailMessage += `${fileResult.fileName}: エラー - ${fileResult.error}\n`
            } else {
              detailMessage += `${fileResult.fileName}: ${fileResult.processedCount ?? 0}件\n`
            }
          },
        )
        detailMessage += `合計: ${result.data?.totalProcessed ?? 0}件処理`

        ElMessage.success({
          message: detailMessage,
          duration: 5000,
          showClose: true,
        })
      } else {
        // 如果没有详细数据，使用后端返回的消息
        ElMessage.success(result?.message || 'データ読取が完了しました')
      }

      // データ読取後、自動的にテーブルを更新
      fetchLogs()
    } else {
      // 失败情况
      ElMessage.error((result as any)?.message || 'データ読取に失敗しました')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('CSV導入失敗:', error)
      ElMessage.error(`データ読取に失敗しました: ${error.message}`)
    }
  } finally {
    importLoading.value = false
  }
}

const handlePageChange = (page: number) => {
  pagination.value.page = page
  fetchLogs()
}

const handlePageSizeChange = (size: number) => {
  pagination.value.pageSize = size
  pagination.value.page = 1
  fetchLogs()
}

const showDetail = (row: MaterialLog) => {
  selectedLog.value = row
  detailVisible.value = true
}

const getItemType = (item: string) => {
  switch (item) {
    case '材料受入':
      return 'success'
    case '材料検品':
      return 'warning'
    case '材料出庫':
      return 'info'
    case '材料返品':
      return 'danger'
    default:
      return 'primary'
  }
}

// 印刷機能（現在のフィルター条件に合致する全件を印刷）
const handlePrint = async () => {
  if (!totalCount.value) {
    ElMessage.warning('印刷するデータがありません')
    return
  }

  printLoading.value = true
  try {
    // 仕入先パラメータ（複数選択対応: カンマ区切りでAPIに送信）
    const supplierParam: string | undefined =
      Array.isArray(filters.value.supplier) && filters.value.supplier.length > 0
        ? filters.value.supplier.join(',')
        : undefined

    const params: import('@/api/material').ReceivingListParams = {
      keyword: filters.value.keyword || undefined,
      startDate: filters.value.start_date || undefined,
      endDate: filters.value.end_date || undefined,
      supplier: supplierParam,
      page: 1,
      pageSize: Math.max(totalCount.value, 10000),
    }

    const result = await getMaterialLogs(params)
    const allData = result?.data?.list ?? []

    if (!allData.length) {
      ElMessage.warning('印刷するデータがありません')
      return
    }

    const printContent = generatePrintHtml(allData)
    const printWindow = window.open('', '_blank')
    if (printWindow) {
      printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
          <title>材料受入履歴 - 印刷</title>
          <meta charset="UTF-8">
          <style>
            @page { size: A4 landscape; margin: 10mm; }
            body { font-family: 'Meiryo', 'Yu Gothic', sans-serif; margin: 0; padding: 0; font-size: 9pt; }
            .print-header { text-align: center; margin-bottom: 6mm; border-bottom: 1.5px solid #333; padding-bottom: 2mm; }
            .print-title { font-size: 16pt; font-weight: bold; margin-bottom: 1.5mm; }
            .print-date { font-size: 9pt; color: #666; }
            .print-table { width: 100%; border-collapse: collapse; margin-top: 5mm; font-size: 8pt; }
            .print-table th, .print-table td { border: 1px solid #333; padding: 2mm 1mm; text-align: center; }
            .print-table th { background-color: #f5f5f5; font-weight: bold; }
            .print-table .text-left { text-align: left; }
            @media print {
              body { margin: 0; padding: 0; }
              .print-table tr { page-break-inside: avoid; }
              .print-table thead { display: table-header-group; }
            }
          </style>
        </head>
        <body>${printContent}</body>
        </html>
      `)
      printWindow.document.close()
      printWindow.onload = () => {
        printWindow.print()
        setTimeout(() => printWindow.close(), 500)
      }
    } else {
      ElMessage.error('印刷ウィンドウを開けませんでした')
    }
  } catch (error: any) {
    console.error('材料受入履歴の印刷エラー:', error)
    ElMessage.error('印刷中にエラーが発生しました')
  } finally {
    printLoading.value = false
  }
}

// 印刷用の行データ（APIで返る拡張フィールドを含む）
type MaterialLogPrint = MaterialLog & {
  manufacture_no?: string
  outer_diameter1?: string
  outer_diameter2?: string
  supplier?: string
  magnetic?: boolean
  appearance?: boolean
}

const generatePrintHtml = (data: MaterialLog[]): string => {
  const printDate = new Date().toLocaleString('ja-JP', {
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
  const row = (r: MaterialLogPrint) => `
    <tr>
      <td>${r.log_date ?? '-'}</td>
      <td>${r.log_time ?? '-'}</td>
      <td class="text-left">${r.item ?? '-'}</td>
      <td class="text-left">${r.material_name ?? '-'}</td>
      <td>${(r as MaterialLogPrint).manufacture_no ?? '-'}</td>
      <td>${r.quantity ?? '-'}</td>
      <td>${(r as MaterialLogPrint).outer_diameter1 ?? '-'}</td>
      <td>${(r as MaterialLogPrint).outer_diameter2 ?? '-'}</td>
      <td class="text-left">${(r as MaterialLogPrint).supplier ?? '-'}</td>
      <td>${(r as MaterialLogPrint).magnetic ? '有' : '無'}</td>
      <td>${(r as MaterialLogPrint).appearance ? '良' : '不良'}</td>
      <td class="text-left">${r.remarks ?? '-'}</td>
    </tr>
  `
  const tbody = data.map((r) => row(r as MaterialLogPrint)).join('')
  return `
    <div class="print-header">
      <div class="print-title">材料受入履歴</div>
      <div class="print-date">印刷日時: ${printDate}　表示件数: ${data.length}件</div>
    </div>
    <table class="print-table">
      <thead>
        <tr>
          <th>日付</th>
          <th>時間</th>
          <th>項目</th>
          <th>材料名</th>
          <th>製造番号</th>
          <th>数量</th>
          <th>外径1</th>
          <th>外径2</th>
          <th>仕入先</th>
          <th>磁気</th>
          <th>外観</th>
          <th>作業員</th>
        </tr>
      </thead>
      <tbody>${tbody}</tbody>
    </table>
  `
}

// 列显示设置相关方法
const showColumnSettings = () => {
  columnSettingsVisible.value = true
}

const saveColumnSettings = () => {
  // 保存到localStorage
  localStorage.setItem('materialLogs_visibleColumns', JSON.stringify(visibleColumns.value))
  columnSettingsVisible.value = false
  ElMessage.success('列表示設定を保存しました')
}

const resetColumnSettings = () => {
  visibleColumns.value = {
    log_date: true,
    log_time: true,
    item: true,
    material_cd: false,
    material_name: true,
    process_cd: false,
    manufacture_no: true,
    manufacture_date: false,
    pieces_per_bundle: false,
    length: false,
    quantity: true,
    bundle_quantity: false,
    outer_diameter1: true,
    outer_diameter2: true,
    supplier: true,
    material_quality: false,
    magnetic: false,
    appearance: false,
    hd_no: false,
    remarks: false,
    note: false,
    created_at: false,
    updated_at: false,
  }
  ElMessage.info('列表示設定をリセットしました')
}

const loadColumnSettings = () => {
  const saved = localStorage.getItem('materialLogs_visibleColumns')
  if (saved) {
    try {
      visibleColumns.value = JSON.parse(saved)
    } catch (error) {
      console.error('列表示設定の読み込みに失敗しました:', error)
    }
  }
}

// 生命周期
onMounted(() => {
  // 确保初始数据是安全的
  tableData.value = []
  totalCount.value = 0

  // 初始化日期选择器
  if (filters.value.start_date && filters.value.end_date) {
    dateRange.value = [filters.value.start_date, filters.value.end_date]
  }

  // 加载列显示设置
  loadColumnSettings()
  // 获取仕入先列表
  fetchSuppliers()
  fetchLogs()
})
</script>

<style scoped>
.material-logs-container {
  --ml-surface: #ffffff;
  --ml-border: #e2e8f0;
  --ml-muted: #64748b;
  --ml-text: #0f172a;
  --ml-accent: #4f46e5;
  --ml-accent-soft: #eef2ff;
  --ml-radius: 10px;
  --ml-radius-sm: 8px;
  --ml-shadow: 0 1px 2px rgba(15, 23, 42, 0.06), 0 4px 16px rgba(15, 23, 42, 0.06);

  min-height: auto;
  background: #f1f5f9;
  padding: 8px 10px 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  box-sizing: border-box;
}

.page-hero {
  background: var(--ml-surface);
  border-radius: var(--ml-radius);
  border: 1px solid var(--ml-border);
  box-shadow: var(--ml-shadow);
  padding: 10px 14px;
  position: relative;
  overflow: hidden;
}

.page-hero::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: linear-gradient(180deg, var(--ml-accent) 0%, #7c3aed 100%);
  border-radius: var(--ml-radius) 0 0 var(--ml-radius);
}

.page-hero__main {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px 16px;
  position: relative;
  z-index: 1;
}

.page-hero__brand {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.page-hero__icon {
  width: 36px;
  height: 36px;
  border-radius: var(--ml-radius-sm);
  background: var(--ml-accent-soft);
  color: var(--ml-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.page-hero__titles {
  min-width: 0;
}

.page-hero__title {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--ml-text);
  line-height: 1.25;
}

.page-hero__sub {
  margin: 2px 0 0;
  font-size: 12px;
  color: var(--ml-muted);
  line-height: 1.35;
}

.page-hero__stats {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.stat-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid var(--ml-border);
  background: #f8fafc;
  min-height: 36px;
  box-sizing: border-box;
}

.stat-pill__ico {
  font-size: 16px;
  color: var(--ml-muted);
}

.stat-pill--total .stat-pill__ico {
  color: #7c3aed;
}

.stat-pill--page .stat-pill__ico {
  color: #0284c7;
}

.stat-pill__text {
  display: flex;
  flex-direction: column;
  line-height: 1.1;
}

.stat-pill__num {
  font-size: 15px;
  font-weight: 700;
  color: var(--ml-text);
  font-variant-numeric: tabular-nums;
}

.stat-pill__lbl {
  font-size: 11px;
  color: var(--ml-muted);
  margin-top: 1px;
}

.filter-card,
.table-card {
  background: var(--ml-surface);
  border-radius: var(--ml-radius);
  border: 1px solid var(--ml-border);
  box-shadow: var(--ml-shadow);
  overflow: hidden;
}

.filter-card__bar,
.table-card__bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px 10px;
  padding: 8px 12px;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 1px solid var(--ml-border);
}

.filter-card__title,
.table-card__title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #334155;
}

.filter-card__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: flex-end;
}

.filter-card__body {
  padding: 10px 12px 12px;
}

.filter-grid {
  display: grid;
  grid-template-columns: minmax(180px, 1.4fr) minmax(220px, 1fr) minmax(160px, 1fr) minmax(200px, 0.95fr);
  gap: 8px 10px;
  align-items: end;
}

.filter-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.filter-field--grow {
  min-width: 140px;
}

.filter-field--sort {
  min-width: 200px;
}

.field-label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 600;
  color: var(--ml-muted);
  text-transform: none;
  letter-spacing: 0.01em;
}

.field-control {
  width: 100%;
}

.field-control--date {
  width: 100%;
}

.sort-row {
  display: flex;
  gap: 6px;
  align-items: stretch;
}

.sort-row__field {
  flex: 1;
  min-width: 0;
}

.sort-row__order {
  width: 88px;
  flex-shrink: 0;
}

.table-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.table-card__tag {
  margin-left: 2px;
  font-weight: 600;
}

.table-card__body {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 0;
}

.modern-table {
  flex: 1;
  width: 100%;
}

.modern-table :deep(.el-table__header-wrapper) {
  background: #f1f5f9;
}

.modern-table :deep(.el-table th.el-table__cell) {
  padding: 6px 8px;
}

.modern-table :deep(.el-table td.el-table__cell) {
  padding: 5px 8px;
  font-size: 12px;
  color: #1e293b;
}

.modern-table :deep(.el-table__row) {
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.modern-table :deep(.el-table__body tr:hover > td.el-table__cell) {
  background-color: #f8fafc !important;
}

.pagination-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px 12px;
  padding: 8px 12px;
  border-top: 1px solid var(--ml-border);
  background: #f8fafc;
}

.pagination-bar__info {
  font-size: 12px;
  color: var(--ml-muted);
  font-variant-numeric: tabular-nums;
}

.modern-pagination :deep(.el-pagination) {
  font-weight: 500;
  flex-wrap: wrap;
  justify-content: flex-end;
  row-gap: 4px;
}

.modern-pagination :deep(.el-pager li) {
  border-radius: 6px;
  margin: 0 1px;
  min-width: 26px;
  height: 26px;
  line-height: 26px;
  font-size: 12px;
}

.modern-pagination :deep(.el-pager li.is-active) {
  background: var(--ml-accent);
  color: #fff;
}

.detail-content {
  display: grid;
  grid-template-columns: 1fr;
  gap: 6px;
}

.detail-row {
  display: grid;
  grid-template-columns: 88px 1fr;
  gap: 8px;
  align-items: start;
  padding: 8px 10px;
  background: #f8fafc;
  border-radius: var(--ml-radius-sm);
  border: 1px solid var(--ml-border);
}

.detail-row label {
  font-weight: 600;
  color: #475569;
  font-size: 12px;
}

.detail-row span {
  color: var(--ml-text);
  font-size: 13px;
  word-break: break-word;
}

.column-settings {
  max-height: min(58vh, 420px);
  overflow-y: auto;
  padding: 2px 2px 0;
}

.column-group {
  margin-bottom: 8px;
  padding: 8px 10px;
  background: #f8fafc;
  border-radius: var(--ml-radius-sm);
  border: 1px solid var(--ml-border);
}

.column-group:last-child {
  margin-bottom: 0;
}

.column-group h4 {
  margin: 0 0 6px;
  color: var(--ml-text);
  font-size: 12px;
  font-weight: 700;
  padding-bottom: 4px;
  border-bottom: 1px solid var(--ml-border);
}

.column-group :deep(.el-checkbox) {
  display: flex;
  margin: 0;
  padding: 4px 6px;
  border-radius: 6px;
  font-size: 12px;
  height: auto;
  align-items: center;
}

.column-group :deep(.el-checkbox:hover) {
  background: #eef2ff;
}

@media (max-width: 1200px) {
  .filter-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .filter-field--sort {
    grid-column: 1 / -1;
  }

  .sort-row__order {
    width: 100px;
  }
}

@media (max-width: 900px) {
  .filter-grid {
    grid-template-columns: 1fr;
  }

  .page-hero__stats {
    width: 100%;
  }

  .stat-pill {
    flex: 1;
    min-width: calc(50% - 4px);
  }

  .pagination-bar {
    flex-direction: column;
    align-items: stretch;
    text-align: center;
  }

  .modern-pagination :deep(.el-pagination) {
    justify-content: center;
  }
}

@media (max-width: 600px) {
  .material-logs-container {
    padding: 6px;
    gap: 6px;
  }

  .page-hero {
    padding: 8px 12px;
  }

  .stat-pill {
    min-width: 100%;
  }

  .filter-card__bar {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-card__actions {
    justify-content: stretch;
  }

  .filter-card__actions :deep(.el-button) {
    flex: 1;
  }
}

:deep(.el-button) {
  border-radius: var(--ml-radius-sm);
  font-weight: 500;
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  border-color: transparent;
}

:deep(.el-button--primary:hover) {
  filter: brightness(1.05);
}

:deep(.el-input__wrapper),
:deep(.el-select .el-input__wrapper) {
  border-radius: var(--ml-radius-sm);
  box-shadow: none;
}

:deep(.el-input__inner) {
  font-size: 12px;
}

:deep(.el-tag) {
  border-radius: 6px;
  font-weight: 500;
}

.logs-dialog :deep(.el-dialog__header) {
  padding: 12px 16px 8px;
  margin-right: 0;
}

.logs-dialog :deep(.el-dialog__title) {
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
}

.logs-dialog :deep(.el-dialog__body) {
  padding: 8px 16px 12px;
}

.logs-dialog :deep(.el-dialog__footer) {
  padding: 8px 16px 12px;
  border-top: 1px solid #e2e8f0;
}
</style>
