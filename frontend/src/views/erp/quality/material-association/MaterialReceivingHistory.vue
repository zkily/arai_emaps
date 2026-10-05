<template>
  <div class="material-logs-container mrh-modern pb-std">
    <!-- 页面标题 -->
    <div class="page-header pb-hero pb-hero--page">
      <div class="page-header-fx pb-bubbles" aria-hidden="true" />
      <div class="header-content">
        <div class="title-section">
          <div class="title-icon">
            <el-icon size="24" color="#409eff"><Document /></el-icon>
          </div>
          <div class="title-text">
            <h1 class="pb-hero-title">材料受入履歴</h1>
            <p class="pb-hero-desc">材料の受入・検品を管理します</p>
          </div>
        </div>
        <div class="stats-section">
          <div class="stat-card">
            <div class="stat-icon total">
              <el-icon><DataBoard /></el-icon>
            </div>
            <div class="stat-content">
              <span class="stat-number">{{ totalCount }}</span>
              <span class="stat-label">総件数</span>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon filtered">
              <el-icon><View /></el-icon>
            </div>
            <div class="stat-content">
              <span class="stat-number">{{ filteredCount || 0 }}</span>
              <span class="stat-label">表示件数</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 検索フィルター -->
    <div class="search-panel">
      <div class="search-header">
        <div class="search-title">
          <el-icon><Search /></el-icon>
          <span>検索・フィルター</span>
        </div>
        <div class="search-actions">
          <el-button size="small" class="mrh-btn mrh-btn--clear" @click="clearFilters" icon="Refresh"> クリア </el-button>
          <el-button size="small" class="mrh-btn mrh-btn--cols" @click="showColumnSettings" icon="Setting"> 列設定 </el-button>
          <el-button
            size="small"
            class="mrh-btn mrh-btn--print"
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
            class="mrh-btn mrh-btn--import"
            @click="importCSVData"
            :loading="importLoading"
            icon="Upload"
          >
            データ読取
          </el-button>
        </div>
      </div>

      <div class="search-content">
        <div class="search-grid">
          <div class="search-item mrh-f mrh-f--kw">
            <div class="search-label">
              <el-icon><Search /></el-icon>
              <span>材料名、仕入先、製造番号で検索</span>
            </div>
            <el-input
              v-model="filters.keyword"
              placeholder="材料名・仕入先・製造番号で検索"
              clearable
              @input="handleSearch"
              class="search-input"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>

          <div class="search-item mrh-f mrh-f--date">
            <div class="search-label">
              <el-icon><Calendar /></el-icon>
              <span>期間</span>
            </div>
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="～"
              start-placeholder="開始日"
              end-placeholder="終了日"
              format="YYYY/MM/DD"
              value-format="YYYY-MM-DD"
              @change="handleDateChange"
              class="search-input"
              size="default"
            />
          </div>

          <div class="search-item mrh-f mrh-f--sup">
            <div class="search-label">
              <el-icon><Operation /></el-icon>
              <span>仕入先</span>
            </div>
            <el-select
              v-model="filters.supplier"
              placeholder="仕入先を選択（複数選択可）"
              clearable
              multiple
              collapse-tags
              collapse-tags-tooltip
              @change="handleSearch"
              class="search-input"
            >
              <el-option
                v-for="supplier in supplierList"
                :key="supplier.value"
                :label="supplier.label"
                :value="supplier.value"
              />
            </el-select>
          </div>

          <div class="search-item mrh-f mrh-f--sort">
            <div class="search-label">
              <el-icon><Sort /></el-icon>
              <span>並び順</span>
            </div>
            <div class="sort-controls">
              <el-select
                v-model="sortField"
                placeholder="並び順項目"
                clearable
                @change="handleSortChange"
                class="sort-field-select"
              >
                <el-option label="材料名" value="material_name" />
                <el-option label="日付" value="log_date" />
                <el-option label="製造日" value="manufacture_date" />
                <el-option label="仕入先" value="supplier" />
              </el-select>
              <el-select
                v-model="sortOrder"
                placeholder="順序"
                @change="handleSortChange"
                class="sort-order-select"
                :disabled="!sortField"
              >
                <el-option label="昇順" value="asc" />
                <el-option label="降順" value="desc" />
              </el-select>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- データテーブル -->
    <div class="table-panel">
      <div class="table-header">
        <div class="table-title">
          <el-icon><List /></el-icon>
          <span>材料ログ一覧</span>
          <el-tag v-if="totalCount > 0" type="info" size="small">{{ totalCount }}件</el-tag>
        </div>
      </div>

      <div class="table-content">
        <el-table
          :data="tableData || []"
          v-loading="loading"
          stripe
          highlight-current-row
          @row-click="showDetail"
          class="modern-table"
          size="default"
          :header-cell-style="{
            background: '#f8fafc',
            color: '#374151',
            fontWeight: '600',
            borderBottom: '1px solid #e5e7eb',
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

        <!-- ページネーション -->
        <div class="pagination-section">
          <div class="pagination-info">
            <span class="pagination-text">
              {{ pagination.pageSize * (pagination.page - 1) + 1 }} -
              {{ Math.min(pagination.pageSize * pagination.page, totalCount) }} 件 / 全
              {{ totalCount }} 件
            </span>
          </div>
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="totalCount || 0"
            layout="sizes, prev, pager, next, jumper"
            @size-change="handlePageSizeChange"
            @current-change="handlePageChange"
            class="modern-pagination"
          />
        </div>
      </div>
    </div>

    <!-- 詳細ダイアログ -->
    <el-dialog v-model="detailVisible" title="材料ログ詳細" width="600px">
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

    <!-- 列表示設定ダイアログ -->
    <el-dialog v-model="columnSettingsVisible" title="列表示設定" width="500px">
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
import { useQualityOperationPermission } from '@/composables/useQualityOperationPermission'
import { guardQualityOperation } from '@/utils/qualityOperationGuard'

const { canCreate, canEdit, canDelete, canExport, canApprove } = useQualityOperationPermission()


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
  if (!guardQualityOperation(canExport)) return

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
  if (!guardQualityOperation(canExport)) return

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
/* 现代化样式设计 */
.material-logs-container {
  min-height: 100vh;
  background: linear-gradient(145deg, #f4f7fb 0%, #e9eef6 100%);
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* 页面头部 */
.page-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 10px;
  padding: 12px 16px;
  color: white;
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.24);
  position: relative;
  overflow: hidden;
}

.page-header::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 70%);
  border-radius: 50%;
  transform: translate(50%, -50%);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  z-index: 1;
}

.title-section {
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-icon {
  width: 34px;
  height: 34px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
}

.title-text h1 {
  margin: 0 0 2px 0;
  font-size: 1.2rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.title-text p {
  margin: 0;
  opacity: 0.88;
  font-size: 0.8rem;
}

.stats-section {
  display: flex;
  gap: 8px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  padding: 8px 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 88px;
  transition: transform 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-icon {
  width: 28px;
  height: 28px;
  border-radius: 7px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
}

.stat-icon.total {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon.filtered {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-number {
  font-size: 1.02rem;
  font-weight: 700;
  line-height: 1;
}

.stat-label {
  font-size: 0.7rem;
  opacity: 0.9;
  margin-top: 1px;
}

/* 搜索面板 */
.search-panel {
  background: white;
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
  overflow: hidden;
  border: 1px solid #e5e7eb;
}

.search-header {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  padding: 10px 12px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: #374151;
  font-size: 0.875rem;
}

.search-actions {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.search-content {
  padding: 10px 12px;
}

.search-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 8px;
}

.search-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px;
  border: 1px solid #edf2f7;
  border-radius: 8px;
  background: #fbfdff;
}

.search-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
  margin-bottom: 0;
}

.search-input {
  border-radius: 8px;
}

.sort-controls {
  display: flex;
  gap: 6px;
  align-items: center;
}

.sort-field-select {
  flex: 2;
  min-width: 120px;
}

.sort-order-select {
  flex: 1;
  min-width: 80px;
}

/* 表格面板 */
.table-panel {
  background: white;
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
  overflow: hidden;
  border: 1px solid #e5e7eb;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.table-header {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  padding: 9px 12px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
}

.table-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: #374151;
  font-size: 0.875rem;
}

.table-actions {
  display: flex;
  gap: 8px;
}

.table-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.modern-table {
  flex: 1;
}

.modern-table :deep(.el-table__header-wrapper) {
  background: #f8fafc;
}

.modern-table :deep(.el-table th) {
  padding: 6px 0;
  font-size: 0.82rem;
  background-color: #f8fafc;
  color: #2d3748;
  font-weight: 600;
}

.modern-table :deep(.el-table td) {
  padding: 6px 0;
  font-size: 0.82rem;
}

.modern-table :deep(.el-table__body tr:hover) {
  background-color: #f0f4f8 !important;
}

.modern-table :deep(.el-table__row) {
  transition: all 0.2s ease;
  cursor: pointer;
}

.modern-table :deep(.el-table__row:hover) {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

/* 分页区域 */
.pagination-section {
  padding: 8px 12px;
  border-top: 1px solid #e5e7eb;
  background: #f8fafc;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination-info {
  color: #6b7280;
  font-size: 0.8125rem;
}

.pagination-section :deep(.el-pagination) {
  font-size: 0.875rem;
}

.pagination-section :deep(.el-pagination .el-pagination__sizes),
.pagination-section :deep(.el-pagination .el-pager li),
.pagination-section :deep(.el-pagination .btn-prev),
.pagination-section :deep(.el-pagination .btn-next) {
  height: 28px;
  line-height: 28px;
  font-size: 0.875rem;
}

.modern-pagination :deep(.el-pagination) {
  font-weight: 500;
}

.modern-pagination :deep(.el-pager li) {
  border-radius: 6px;
  margin: 0 2px;
  transition: all 0.2s ease;
}

.modern-pagination :deep(.el-pager li:hover) {
  background-color: #f3f4f6;
}

.modern-pagination :deep(.el-pager li.is-active) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

/* 详细对话框美化 */
.detail-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 8px;
}

.detail-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  transition: all 0.2s ease;
}

.detail-row:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.detail-row label {
  font-weight: 600;
  color: #374151;
  min-width: 80px;
}

.detail-row span {
  color: #1f2937;
  flex: 1;
}

/* 列设置对话框样式 */
.column-settings {
  max-height: 500px;
  overflow-y: auto;
  padding: 8px;
}

.column-group {
  margin-bottom: 8px;
  padding: 10px;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  transition: all 0.2s ease;
}

.column-group:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.column-group h4 {
  margin: 0 0 8px 0;
  color: #1f2937;
  font-size: 0.875rem;
  font-weight: 600;
  border-bottom: 1px solid #d1d5db;
  padding-bottom: 6px;
}

.column-group :deep(.el-checkbox) {
  display: block;
  margin-bottom: 6px;
  margin-right: 0;
  padding: 3px 0;
  transition: all 0.2s ease;
  font-size: 0.875rem;
}

.column-group :deep(.el-checkbox:hover) {
  background-color: rgba(102, 126, 234, 0.1);
  border-radius: 6px;
  padding-left: 8px;
}

.column-group :deep(.el-checkbox:last-child) {
  margin-bottom: 0;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .header-content {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }

  .title-section {
    width: 100%;
  }

  .stats-section {
    width: 100%;
    justify-content: space-between;
  }

  .search-grid {
    grid-template-columns: 1fr;
  }

  .search-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }

  .search-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .pagination-section {
    flex-direction: column;
    gap: 12px;
    text-align: center;
  }
}

@media (max-width: 768px) {
  .material-logs-container {
    padding: 8px;
    gap: 8px;
  }

  .page-header {
    padding: 12px 16px;
  }

  .title-section {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .stats-section {
    flex-direction: column;
    gap: 8px;
  }

  .stat-card {
    min-width: 100%;
  }

  .search-content {
    padding: 12px;
  }

  .search-grid {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .detail-content {
    grid-template-columns: 1fr;
  }

  .pagination-section {
    flex-direction: column;
    gap: 8px;
    padding: 8px 12px;
  }
}

/* 按钮美化 */
:deep(.el-button) {
  border-radius: 7px;
  font-weight: 500;
  transition: all 0.2s ease;
}

:deep(.el-button:hover) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
}

/* 输入框美化 */
:deep(.el-input__wrapper) {
  border-radius: 7px;
  transition: all 0.2s ease;
  padding: 2px 8px;
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

:deep(.el-input__inner) {
  font-size: 0.875rem;
}

/* 选择器美化 */
:deep(.el-select) {
  width: 100%;
}

:deep(.el-select .el-input__wrapper) {
  border-radius: 7px;
  padding: 2px 8px;
}

:deep(.el-select .el-input__inner) {
  font-size: 0.875rem;
}

:deep(.el-button--small) {
  padding: 5px 10px;
  font-size: 0.82rem;
}

/* 标签美化 */
:deep(.el-tag) {
  border-radius: 6px;
  font-weight: 500;
}

/* ============================================================
 * 页面美化：現代UI・3D動効・色分け（材料受入履歴 / ティール・シアン系）
 * ============================================================ */
.mrh-modern {
  --mh-shadow:
    0 18px 36px -18px rgba(15, 118, 110, 0.6),
    0 4px 12px -6px rgba(8, 145, 178, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  --mc-shadow:
    0 10px 24px -18px rgba(15, 118, 110, 0.45),
    0 1px 2px rgba(15, 23, 42, 0.04);
  background: linear-gradient(160deg, #ecfeff 0%, #f0fdfa 42%, #f8fafc 100%);
}

/* ---------- ヘッダー ---------- */
.mrh-modern .page-header {
  isolation: isolate;
  padding: 14px 18px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: linear-gradient(125deg, #134e4a 0%, #0f766e 34%, #0891b2 68%, #22d3ee 100%);
  box-shadow: var(--mh-shadow);
}
.mrh-modern .page-header::before {
  display: none;
}
.mrh-modern .page-header-fx {
  position: absolute;
  inset: 0;
  z-index: -1;
  pointer-events: none;
}
.mrh-modern .title-icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  -webkit-backdrop-filter: none;
  backdrop-filter: none;
  background: linear-gradient(150deg, rgba(255, 255, 255, 0.42), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.45);
  box-shadow:
    0 3px 0 rgba(19, 78, 74, 0.55),
    0 10px 18px -8px rgba(4, 47, 46, 0.55),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
  transform: perspective(300px) rotateX(8deg) rotateY(-10deg);
}
.mrh-modern .title-icon .el-icon {
  color: #fff !important;
}
.mrh-modern .title-text h1 {
  font-size: 20px;
  font-weight: 800;
  letter-spacing: 0.04em;
  text-shadow: 0 2px 6px rgba(4, 47, 46, 0.3);
}
.mrh-modern .title-text p {
  font-size: 12px;
  opacity: 0.9;
}

/* 統計カード：不透明の白キーキャップ（色分け） */
.mrh-modern .stat-card {
  --sc: #7c3aed;
  --sc-edge: #5b21b6;
  --sc-soft: #ddd6fe;
  min-width: 110px;
  padding: 7px 12px 7px 8px;
  border-radius: 11px;
  color: #0f172a;
  -webkit-backdrop-filter: none;
  backdrop-filter: none;
  background: #fff;
  border: 1px solid var(--sc-soft);
  box-shadow:
    0 3px 0 var(--sc-edge),
    0 10px 18px -10px rgba(4, 47, 46, 0.6);
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease;
}
.mrh-modern .stat-card:hover {
  transform: translateY(-2px);
  box-shadow:
    0 5px 0 var(--sc-edge),
    0 14px 22px -10px rgba(4, 47, 46, 0.6);
}
.mrh-modern .stat-card:nth-child(2) {
  --sc: #0284c7;
  --sc-edge: #075985;
  --sc-soft: #bae6fd;
}
.mrh-modern .stat-icon {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  color: #fff;
  background: linear-gradient(150deg, color-mix(in srgb, var(--sc) 70%, #fff), var(--sc));
  box-shadow: 0 2px 0 var(--sc-edge);
}
.mrh-modern .stat-number {
  font-size: 18px;
  font-weight: 800;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
}
.mrh-modern .stat-label {
  font-size: 11px;
  font-weight: 700;
  color: var(--sc-edge);
  opacity: 1;
}

/* ---------- 検索パネル ---------- */
.mrh-modern .search-panel,
.mrh-modern .table-panel {
  border-radius: 12px;
  border: 1px solid #ccecea;
  box-shadow: var(--mc-shadow);
}
.mrh-modern .search-header,
.mrh-modern .table-header {
  background: linear-gradient(90deg, #ccfbf1 0%, #ecfeff 60%, #fff 100%);
  border-bottom: 1px solid #b2ebe4;
}
.mrh-modern .search-title,
.mrh-modern .table-title {
  font-size: 13px;
  font-weight: 800;
  color: #115e59;
}
.mrh-modern .search-title .el-icon,
.mrh-modern .table-title .el-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 7px;
  color: #fff;
  background: linear-gradient(150deg, #2dd4bf, #0d9488);
  box-shadow: 0 2px 0 #115e59;
}
.mrh-modern .table-title :deep(.el-tag) {
  font-weight: 800;
  color: #0f766e;
  background: #fff;
  border-color: #99f6e4;
  box-shadow: 0 2px 0 #99f6e4;
  font-variant-numeric: tabular-nums;
}

/* 操作ボタン（色分けキーキャップ） */
.mrh-modern .mrh-btn {
  --b-bg: #fff;
  --b-fg: #475569;
  --b-bd: #cbd5e1;
  --b-edge: #cbd5e1;
  height: 28px;
  padding: 0 12px;
  border-radius: 8px;
  font-weight: 700;
  color: var(--b-fg);
  background: var(--b-bg);
  border: 1px solid var(--b-bd);
  box-shadow: 0 2px 0 var(--b-edge);
  transition:
    transform 0.12s ease,
    box-shadow 0.12s ease,
    filter 0.12s ease;
}
.mrh-modern .mrh-btn:not(.is-disabled):hover,
.mrh-modern .mrh-btn:not(.is-disabled):focus {
  color: var(--b-fg);
  background: var(--b-bg);
  border-color: var(--b-bd);
}
.mrh-modern .mrh-btn:not(.is-disabled):hover {
  transform: translateY(-1px);
  filter: brightness(1.03);
  box-shadow: 0 3px 0 var(--b-edge);
}
.mrh-modern .mrh-btn:not(.is-disabled):active {
  transform: translateY(1px);
  box-shadow: 0 1px 0 var(--b-edge);
}
.mrh-modern .mrh-btn.is-disabled {
  transform: none;
  box-shadow: none;
}
.mrh-modern .mrh-btn--cols {
  --b-bg: #eef2ff;
  --b-fg: #4338ca;
  --b-bd: #c7d2fe;
  --b-edge: #a5b4fc;
}
.mrh-modern .mrh-btn--print {
  --b-bg: #f5f3ff;
  --b-fg: #6d28d9;
  --b-bd: #ddd6fe;
  --b-edge: #c4b5fd;
}
.mrh-modern .mrh-btn--import {
  --b-bg: linear-gradient(180deg, #14b8a6 0%, #0d9488 100%);
  --b-fg: #fff;
  --b-bd: #0f766e;
  --b-edge: #115e59;
}

/* 検索項目（色分け：キーワード＝teal / 期間＝sky / 仕入先＝violet / 並び順＝amber） */
.mrh-modern .mrh-f--kw {
  --fc: #0d9488;
  --fc-rgb: 13, 148, 136;
  --fc-ink: #115e59;
}
.mrh-modern .mrh-f--date {
  --fc: #0284c7;
  --fc-rgb: 2, 132, 199;
  --fc-ink: #075985;
}
.mrh-modern .mrh-f--sup {
  --fc: #7c3aed;
  --fc-rgb: 124, 58, 237;
  --fc-ink: #5b21b6;
}
.mrh-modern .mrh-f--sort {
  --fc: #d97706;
  --fc-rgb: 217, 119, 6;
  --fc-ink: #92400e;
}
.mrh-modern .search-item.mrh-f {
  border-radius: 10px;
  border: 1px solid rgba(var(--fc-rgb), 0.2);
  background: linear-gradient(180deg, rgba(var(--fc-rgb), 0.06) 0%, #fff 70%);
  box-shadow: inset 3px 0 0 var(--fc);
  transition:
    border-color 0.15s ease,
    box-shadow 0.15s ease;
}
.mrh-modern .search-item.mrh-f:focus-within {
  border-color: rgba(var(--fc-rgb), 0.5);
  box-shadow:
    inset 3px 0 0 var(--fc),
    0 0 0 3px rgba(var(--fc-rgb), 0.1);
}
.mrh-modern .mrh-f .search-label {
  font-size: 12px;
  font-weight: 700;
  color: var(--fc-ink);
}
.mrh-modern .mrh-f .search-label .el-icon {
  color: var(--fc);
}
.mrh-modern .mrh-f :deep(.el-input__wrapper),
.mrh-modern .mrh-f :deep(.el-select__wrapper) {
  border-radius: 8px;
  background-color: #fff;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
  transition: box-shadow 0.15s ease;
}
.mrh-modern .mrh-f :deep(.el-input__wrapper:hover),
.mrh-modern .mrh-f :deep(.el-select__wrapper:hover) {
  box-shadow: 0 0 0 1px rgba(var(--fc-rgb), 0.55) inset;
}
.mrh-modern .mrh-f :deep(.el-input__wrapper.is-focus),
.mrh-modern .mrh-f :deep(.el-input__wrapper.is-active),
.mrh-modern .mrh-f :deep(.el-select__wrapper.is-focused) {
  box-shadow:
    0 0 0 1px var(--fc) inset,
    0 0 0 3px rgba(var(--fc-rgb), 0.15);
}

/* ---------- テーブル ---------- */
.mrh-modern .modern-table :deep(.el-table__header th.el-table__cell) {
  background: linear-gradient(180deg, #f0fdfa 0%, #ccfbf1 100%) !important;
  color: #115e59 !important;
  font-weight: 700 !important;
  box-shadow: inset 0 -2px 0 #5eead4;
}
.mrh-modern .modern-table :deep(.el-table__row:hover) {
  transform: none;
  box-shadow: none;
}
.mrh-modern .modern-table :deep(.el-table__body tr:hover > td.el-table__cell) {
  background: #f0fdfa !important;
}
.mrh-modern .modern-table :deep(.el-table__body tr:hover > td.el-table__cell:first-child) {
  box-shadow: inset 3px 0 0 #0d9488;
}
.mrh-modern .modern-table :deep(.el-table__body tr.current-row > td.el-table__cell) {
  background: #ccfbf1 !important;
}
.mrh-modern .modern-table :deep(.el-table__body td .cell) {
  font-variant-numeric: tabular-nums;
}
.mrh-modern .pagination-section {
  background: linear-gradient(180deg, #f0fdfa 0%, #f8fafc 100%);
  border-top-color: #ccecea;
}
.mrh-modern .modern-pagination :deep(.el-pager li.is-active) {
  color: #fff;
  font-weight: 800;
  background: linear-gradient(180deg, #2dd4bf 0%, #0d9488 100%);
  box-shadow: 0 2px 0 #115e59;
}

@media (prefers-reduced-motion: reduce) {
  .mrh-modern .stat-card:hover,
  .mrh-modern .mrh-btn:not(.is-disabled):hover {
    transform: none;
  }
}
</style>
