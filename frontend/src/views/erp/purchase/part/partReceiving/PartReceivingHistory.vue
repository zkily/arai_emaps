<template>
  <div class="part-logs-container pr-modern pb-std">
    <header class="page-hero pb-hero pb-hero--page">
      <div class="hero-fx pb-bubbles" aria-hidden="true" />
      <div class="page-hero__main">
        <div class="page-hero__brand">
          <div class="page-hero__icon" aria-hidden="true">
            <el-icon><Document /></el-icon>
          </div>
          <div class="page-hero__titles">
            <h1 class="page-hero__title pb-hero-title">部品受入履歴</h1>
            <p class="page-hero__sub pb-hero-desc">
              キーワード・期間・仕入先で部品の受入ログを検索し、CSV読取・印刷・列表示を設定
            </p>
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
          <el-button size="small" class="fc-btn fc-btn--clear" @click="clearFilters" icon="Refresh">
            クリア
          </el-button>
          <el-button size="small" class="fc-btn fc-btn--cols" @click="showColumnSettings" icon="Setting">
            列設定
          </el-button>
          <el-button
            size="small"
            class="fc-btn fc-btn--print"
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
            class="fc-btn fc-btn--import"
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
              placeholder="部品名・仕入先・製造番号"
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
                <el-option label="部品名" value="part_name" />
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
          <span>部品ログ一覧</span>
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
            v-if="visibleColumns.part_cd"
            prop="part_cd"
            label="部品CD"
            width="120"
            align="center"
          />
          <el-table-column
            v-if="visibleColumns.part_name"
            prop="part_name"
            label="部品名"
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
            v-if="visibleColumns.part_quality"
            prop="part_quality"
            label="部品規格"
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
            size="small"
            @size-change="handlePageSizeChange"
            @current-change="handlePageChange"
            class="modern-pagination"
          />
        </div>
      </div>
    </section>

    <el-dialog
      v-model="detailVisible"
      title="部品ログ詳細"
      width="520px"
      class="logs-dialog prh-dialog pb-std"
      align-center
      destroy-on-close
      :show-close="false"
    >
      <template #header>
        <div class="ld-hero pb-hero">
          <div class="hero-fx pb-bubbles" aria-hidden="true" />
          <span class="ld-hero__icon"><el-icon><Document /></el-icon></span>
          <div class="ld-hero__copy">
            <span class="ld-hero__title">部品ログ詳細</span>
            <p class="ld-hero__desc">選択した受入ログの内容を確認</p>
          </div>
          <el-icon class="ld-hero__close" @click="detailVisible = false"><Close /></el-icon>
        </div>
      </template>
      <div v-if="selectedLog" class="detail-content">
        <div class="detail-row">
          <label>項目:</label>
          <span>{{ selectedLog.item }}</span>
        </div>
        <div class="detail-row">
          <label>部品CD:</label>
          <span>{{ selectedLog.part_cd }}</span>
        </div>
        <div class="detail-row">
          <label>部品名:</label>
          <span>{{ selectedLog.part_name }}</span>
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
        <el-button class="dlg-btn" @click="detailVisible = false">閉じる</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="columnSettingsVisible"
      title="列表示設定"
      width="480px"
      class="logs-dialog logs-dialog--columns prh-dialog pb-std"
      align-center
      destroy-on-close
      :show-close="false"
    >
      <template #header>
        <div class="ld-hero ld-hero--columns pb-hero">
          <div class="hero-fx pb-bubbles" aria-hidden="true" />
          <span class="ld-hero__icon"><el-icon><Setting /></el-icon></span>
          <div class="ld-hero__copy">
            <span class="ld-hero__title">列表示設定</span>
            <p class="ld-hero__desc">一覧に表示する列を選択（保存するとブラウザに記憶）</p>
          </div>
          <el-icon class="ld-hero__close" @click="columnSettingsVisible = false"><Close /></el-icon>
        </div>
      </template>
      <div class="column-settings">
        <div class="column-group">
          <h4>基本情報</h4>
          <el-checkbox v-model="visibleColumns.log_date">日付</el-checkbox>
          <el-checkbox v-model="visibleColumns.log_time">時間</el-checkbox>
          <el-checkbox v-model="visibleColumns.item">項目</el-checkbox>
          <el-checkbox v-model="visibleColumns.part_cd">部品CD</el-checkbox>
          <el-checkbox v-model="visibleColumns.part_name">部品名</el-checkbox>
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
          <el-checkbox v-model="visibleColumns.part_quality">部品規格</el-checkbox>
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
        <el-button class="dlg-btn dlg-btn--reset" @click="resetColumnSettings">リセット</el-button>
        <el-button class="dlg-btn" @click="columnSettingsVisible = false">キャンセル</el-button>
        <el-button type="primary" class="dlg-btn dlg-btn--save" @click="saveColumnSettings">
          保存
        </el-button>
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
  Setting,
  Close,
} from '@element-plus/icons-vue'
import { getPartLogs, importPartLogsFromCSV, getPartSupplierList } from '@/api/part'
import type { PartLog, PartLogSearchParams } from '@/types/part'
import { usePurchaseOperationPermission } from '@/composables/usePurchaseOperationPermission'
import { guardPurchaseOperation } from '@/utils/purchaseOperationGuard'

const { canCreate, canEdit, canDelete, canExport, canApprove } = usePurchaseOperationPermission()


// 响应式数据
const loading = ref(false)
const importLoading = ref(false)
const printLoading = ref(false)
const tableData = ref<PartLog[]>([])
const totalCount = ref(0)
const dateRange = ref<[string, string] | undefined>(undefined)
const detailVisible = ref(false)
const selectedLog = ref<PartLog | null>(null)
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
  part_cd: false,
  part_name: true,
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
  part_quality: false,
  magnetic: false,
  appearance: false,
  hd_no: false,
  remarks: false,
  note: false,
  created_at: false,
  updated_at: false,
})

// 筛选器
const filters = ref<PartLogSearchParams>({
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
    const result = await getPartSupplierList()
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
    // 处理多选供应商：如果是数组且不为空，转换为逗号分隔的字符串；否则传 undefined 以符合 PartReceivingListParams.supplier (string | undefined)
    const supplierParam: string | undefined =
      Array.isArray(filters.value.supplier) && filters.value.supplier.length > 0
        ? filters.value.supplier.join(',')
        : undefined

    const params: import('@/api/part').PartReceivingListParams = {
      keyword: filters.value.keyword || undefined,
      startDate: filters.value.start_date || undefined,
      endDate: filters.value.end_date || undefined,
      supplier: supplierParam,
      page: pagination.value.page,
      pageSize: pagination.value.pageSize,
    }
    const result = await getPartLogs(params)
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
  if (!guardPurchaseOperation(canExport)) return

  try {
    await ElMessageBox.confirm('CSVファイルから部品ログデータを読み込みますか？', '確認', {
      type: 'info',
      confirmButtonText: 'はい',
      cancelButtonText: 'キャンセル',
    })

    importLoading.value = true
    const result = await importPartLogsFromCSV([]) as { success?: boolean; data?: { fileResults?: { fileName: string; processedCount?: number; success?: boolean; error?: string }[]; totalProcessed?: number }; message?: string }

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

const showDetail = (row: PartLog) => {
  selectedLog.value = row
  detailVisible.value = true
}

const getItemType = (item: string) => {
  switch (item) {
    case '部品受入':
      return 'success'
    case '部品検品':
      return 'warning'
    case '部品出庫':
      return 'info'
    case '部品返品':
      return 'danger'
    default:
      return 'primary'
  }
}

// 印刷機能（現在のフィルター条件に合致する全件を印刷）
const handlePrint = async () => {
  if (!guardPurchaseOperation(canExport)) return

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

    const params: import('@/api/part').PartReceivingListParams = {
      keyword: filters.value.keyword || undefined,
      startDate: filters.value.start_date || undefined,
      endDate: filters.value.end_date || undefined,
      supplier: supplierParam,
      page: 1,
      pageSize: Math.max(totalCount.value, 10000),
    }

    const result = await getPartLogs(params)
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
          <title>部品受入履歴 - 印刷</title>
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
    console.error('部品受入履歴の印刷エラー:', error)
    ElMessage.error('印刷中にエラーが発生しました')
  } finally {
    printLoading.value = false
  }
}

// 印刷用の行データ（APIで返る拡張フィールドを含む）
type PartLogPrint = PartLog & {
  manufacture_no?: string
  outer_diameter1?: string
  outer_diameter2?: string
  supplier?: string
  magnetic?: boolean
  appearance?: boolean
}

const generatePrintHtml = (data: PartLog[]): string => {
  const printDate = new Date().toLocaleString('ja-JP', {
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
  const row = (r: PartLogPrint) => `
    <tr>
      <td>${r.log_date ?? '-'}</td>
      <td>${r.log_time ?? '-'}</td>
      <td class="text-left">${r.item ?? '-'}</td>
      <td class="text-left">${r.part_name ?? '-'}</td>
      <td>${(r as PartLogPrint).manufacture_no ?? '-'}</td>
      <td>${r.quantity ?? '-'}</td>
      <td>${(r as PartLogPrint).outer_diameter1 ?? '-'}</td>
      <td>${(r as PartLogPrint).outer_diameter2 ?? '-'}</td>
      <td class="text-left">${(r as PartLogPrint).supplier ?? '-'}</td>
      <td>${(r as PartLogPrint).magnetic ? '有' : '無'}</td>
      <td>${(r as PartLogPrint).appearance ? '良' : '不良'}</td>
      <td class="text-left">${r.remarks ?? '-'}</td>
    </tr>
  `
  const tbody = data.map((r) => row(r as PartLogPrint)).join('')
  return `
    <div class="print-header">
      <div class="print-title">部品受入履歴</div>
      <div class="print-date">印刷日時: ${printDate}　表示件数: ${data.length}件</div>
    </div>
    <table class="print-table">
      <thead>
        <tr>
          <th>日付</th>
          <th>時間</th>
          <th>項目</th>
          <th>部品名</th>
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
  localStorage.setItem('partLogs_visibleColumns', JSON.stringify(visibleColumns.value))
  columnSettingsVisible.value = false
  ElMessage.success('列表示設定を保存しました')
}

const resetColumnSettings = () => {
  visibleColumns.value = {
    log_date: true,
    log_time: true,
    item: true,
    part_cd: false,
    part_name: true,
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
    part_quality: false,
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
  const saved = localStorage.getItem('partLogs_visibleColumns')
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
.part-logs-container {
  --ml-surface: #ffffff;
  --ml-border: #e2e8f0;
  --ml-muted: #64748b;
  --ml-text: #0f172a;
  --ml-accent: #4f46e5;
  --ml-accent-soft: #eef2ff;
  --ml-radius: 12px;
  --ml-radius-sm: 8px;

  min-height: auto;
  padding: 8px 10px 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  box-sizing: border-box;
  background: linear-gradient(180deg, #eef2ff 0%, #f8fafc 34%, #f8fafc 100%);
}

/* ============================================================ */
/* 页面美化：现代 UI / 颜色区分（部品受入＝インディゴ〜スカイ系）    */
/* ============================================================ */

/* ---------- ヒーロー ---------- */
.page-hero {
  position: relative;
  overflow: hidden;
  border-radius: 14px;
  background: linear-gradient(125deg, #312e81 0%, #4338ca 34%, #4f46e5 62%, #0284c7 100%);
  box-shadow:
    0 12px 28px -18px rgba(79, 70, 229, 0.65),
    0 1px 2px rgba(15, 23, 42, 0.06);
}

.page-hero__main {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px 16px;
}

.page-hero__brand {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.page-hero__icon {
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
    inset 0 -2px 0 rgba(30, 27, 75, 0.3);
}

.page-hero__titles {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  min-width: 0;
}

.page-hero__title {
  margin: 0;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: #fff;
}

.page-hero__sub {
  margin: 0;
  letter-spacing: 0.02em;
  color: rgba(255, 255, 255, 0.86);
}

/* 統計：濃色ヒーロー上の白ピル */
.page-hero__stats {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.stat-pill {
  --sp: #4f46e5;
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 40px;
  padding: 4px 14px 4px 6px;
  box-sizing: border-box;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.9);
  background: linear-gradient(180deg, #ffffff 0%, #f1f5ff 100%);
  box-shadow:
    inset 0 1px 0 #ffffff,
    inset 0 -2px 0 rgba(148, 163, 184, 0.25),
    0 6px 14px -10px rgba(15, 23, 42, 0.45);
}

.stat-pill--total {
  --sp: #6d28d9;
}

.stat-pill--page {
  --sp: #0369a1;
}

.stat-pill__ico {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  padding: 6px;
  box-sizing: border-box;
  border-radius: 999px;
  font-size: 16px;
  color: #fff;
  background: linear-gradient(150deg, color-mix(in srgb, var(--sp) 65%, #fff) 0%, var(--sp) 100%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 color-mix(in srgb, var(--sp) 60%, #000 20%);
}

.stat-pill__text {
  display: flex;
  flex-direction: column;
  line-height: 1.1;
}

.stat-pill__num {
  font-size: 16px;
  font-weight: 800;
  color: var(--sp);
  font-variant-numeric: tabular-nums;
}

.stat-pill__lbl {
  margin-top: 1px;
  font-size: 10px;
  font-weight: 600;
  color: var(--ml-muted);
}

/* ---------- カード共通 ---------- */
.filter-card,
.table-card {
  position: relative;
  overflow: hidden;
  border-radius: var(--ml-radius);
  border: 1px solid #e0e7ff;
  background: var(--ml-surface);
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 10px 24px -20px rgba(67, 56, 202, 0.45);
}

.filter-card::before,
.table-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 2;
  height: 3px;
  background: linear-gradient(90deg, #6366f1 0%, #4f46e5 50%, #0ea5e9 100%);
}

.filter-card__bar,
.table-card__bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px 10px;
  padding: 10px 12px 8px;
  background: linear-gradient(180deg, #f8f9ff 0%, #f3f5ff 100%);
  border-bottom: 1px solid #e0e7ff;
}

.filter-card__title,
.table-card__title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 700;
  color: #312e81;
}

.filter-card__title > .el-icon,
.table-card__title > .el-icon {
  width: 24px;
  height: 24px;
  padding: 5px;
  box-sizing: border-box;
  border-radius: 7px;
  color: #fff;
  background: linear-gradient(135deg, #818cf8, #4f46e5);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(49, 46, 129, 0.3);
}

.table-card__title > .el-icon {
  background: linear-gradient(135deg, #38bdf8, #0284c7);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(7, 89, 133, 0.3);
}

.filter-card__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: flex-end;
}

/* ツールバーボタン（色で役割を区別） */
.fc-btn {
  height: 28px;
  margin: 0;
  padding: 0 12px;
  border-radius: var(--ml-radius-sm);
  font-weight: 700;
}

.fc-btn--clear {
  --k-rgb: 100 116 139;
  color: #475569;
  border: 1px solid #cbd5e1;
  background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%);
}

.fc-btn--clear:not(.is-disabled):hover,
.fc-btn--clear:focus-visible {
  color: #334155;
  border-color: #94a3b8;
  background: #fff;
}

.fc-btn--cols {
  --k-rgb: 79 70 229;
  color: #4338ca;
  border: 1px solid #c7d2fe;
  background: linear-gradient(180deg, #ffffff 0%, #eef2ff 100%);
}

.fc-btn--cols:not(.is-disabled):hover,
.fc-btn--cols:focus-visible {
  color: #3730a3;
  border-color: #a5b4fc;
  background: #fff;
}

.fc-btn--print {
  --k-rgb: 217 119 6;
  color: #fff;
  border: 1px solid #d97706;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #fbbf24, #d97706);
}

.fc-btn--print:not(.is-disabled):hover,
.fc-btn--print:focus-visible {
  color: #fff;
  border-color: #b45309;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.26) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #fcc93a, #e08a0b);
}

.fc-btn--import {
  --k-rgb: 79 70 229;
  color: #fff;
  border: 1px solid #4338ca;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #6366f1, #4338ca);
}

.fc-btn--import:not(.is-disabled):hover,
.fc-btn--import:focus-visible {
  color: #fff;
  border-color: #3730a3;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.26) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #7477f3, #4f46e5);
}

.fc-btn.is-disabled,
.fc-btn.is-disabled:hover {
  color: #94a3b8;
  border-color: #d1d5db;
  background: #e5e7eb;
}

/* ---------- 検索フィールド ---------- */
.filter-card__body {
  padding: 10px 12px 12px;
}

.filter-grid {
  display: grid;
  grid-template-columns:
    minmax(180px, 1.4fr) minmax(220px, 1fr) minmax(160px, 1fr)
    minmax(200px, 0.95fr);
  gap: 8px 10px;
  align-items: end;
}

.filter-field {
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-width: 0;
}

.filter-field--grow {
  min-width: 140px;
}

.filter-field--sort {
  min-width: 200px;
}

.field-label {
  align-self: flex-start;
  height: 20px;
  padding: 0 9px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.01em;
  color: #3730a3;
  background: #eef2ff;
  box-shadow:
    inset 0 1px 0 #ffffff,
    inset 0 -1px 0 #c7d2fe;
}

.field-control,
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

/* 入力枠：枠線は wrapper の内側リングのみ（二重線にしない） */
.filter-card :deep(.el-input__wrapper),
.filter-card :deep(.el-select__wrapper),
.filter-card :deep(.el-range-editor.el-input__wrapper) {
  border-radius: var(--ml-radius-sm);
  background-color: #fff;
  box-shadow: 0 0 0 1px #d6dcf5 inset;
}

.filter-card :deep(.el-input__wrapper:hover),
.filter-card :deep(.el-select__wrapper:hover) {
  box-shadow: 0 0 0 1px #a5b4fc inset;
}

.filter-card :deep(.el-input__wrapper.is-focus),
.filter-card :deep(.el-input__wrapper.is-active),
.filter-card :deep(.el-select__wrapper.is-focused) {
  box-shadow:
    0 0 0 1px #6366f1 inset,
    0 0 0 3px rgba(99, 102, 241, 0.14);
}

.filter-card :deep(.el-select__wrapper.is-disabled) {
  background-color: #f1f5f9;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
}

.filter-card :deep(.el-input__inner) {
  font-size: 12px;
}

/* ---------- テーブル ---------- */
.table-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.table-card__tag {
  margin-left: 2px;
  height: 20px;
  padding: 0 9px;
  border-radius: 999px;
  font-weight: 700;
  color: #0369a1;
  border-color: #bae6fd;
  background: #f0f9ff;
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
  --el-table-border-color: #eef0fb;
  --el-table-row-hover-bg-color: #eef2ff;
  --el-table-current-row-bg-color: #e0e7ff;
}

.modern-table :deep(th.el-table__cell) {
  padding: 7px 8px !important;
  font-size: 12px !important;
  font-weight: 700 !important;
  color: #3730a3 !important;
  background: #f3f5ff !important;
  border-bottom: 1px solid #dfe4fb !important;
}

.modern-table :deep(td.el-table__cell) {
  padding: 5px 8px;
  font-size: 12px;
  color: #1e293b;
  border-bottom-color: #f1f3fb;
}

.modern-table :deep(.el-table__row) {
  cursor: pointer;
}

.modern-table :deep(.el-table__row--striped td.el-table__cell) {
  background: #fafbff;
}

.modern-table :deep(.el-table__body tr:hover > td.el-table__cell) {
  background-color: #eef2ff !important;
}

.modern-table :deep(.el-table__body tr.current-row > td.el-table__cell) {
  background-color: #e0e7ff !important;
}

.modern-table :deep(.el-tag) {
  border-radius: 999px;
  font-weight: 600;
}

/* ---------- ページャー ---------- */
.pagination-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px 12px;
  padding: 8px 12px;
  border-top: 1px solid #e0e7ff;
  background: linear-gradient(180deg, #fafbff 0%, #f3f5ff 100%);
}

.pagination-bar__info {
  font-size: 12px;
  font-weight: 600;
  color: #4338ca;
  font-variant-numeric: tabular-nums;
}

.modern-pagination {
  font-weight: 500;
  flex-wrap: wrap;
  justify-content: flex-end;
  row-gap: 4px;
}

.modern-pagination :deep(.el-pager li),
.modern-pagination :deep(.btn-prev),
.modern-pagination :deep(.btn-next) {
  min-width: 26px;
  height: 26px;
  margin: 0 2px;
  border-radius: 7px;
  font-size: 12px;
  line-height: 26px;
  color: #4338ca;
  border: 1px solid #e0e7ff;
  background: linear-gradient(180deg, #ffffff 0%, #f5f7ff 100%);
}

.modern-pagination :deep(.el-pager li:not(.is-active):hover) {
  border-color: #a5b4fc;
  background: #fff;
}

.modern-pagination :deep(.el-pager li.is-active) {
  color: #fff;
  border-color: #4338ca;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #6366f1, #4338ca);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 0 rgba(49, 46, 129, 0.35),
    0 4px 10px -6px rgba(79, 70, 229, 0.7);
}

.modern-pagination :deep(.btn-prev:disabled),
.modern-pagination :deep(.btn-next:disabled) {
  color: #94a3b8;
  border-color: #d1d5db;
  background: #e5e7eb;
}

/* ---------- ダイアログ ---------- */
.ld-hero {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  background: linear-gradient(125deg, #312e81 0%, #4338ca 40%, #4f46e5 70%, #0284c7 100%);
}

.ld-hero--columns {
  background: linear-gradient(125deg, #3730a3 0%, #4f46e5 40%, #6d28d9 100%);
}

.ld-hero__icon {
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
    inset 0 -2px 0 rgba(30, 27, 75, 0.3);
}

.ld-hero__copy {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.ld-hero__title {
  font-size: 16px;
  font-weight: 800;
  line-height: 1.3;
  letter-spacing: 0.03em;
  color: #fff;
}

.ld-hero__desc {
  margin: 0;
  font-size: 11px;
  line-height: 1.5;
  color: rgba(255, 255, 255, 0.86);
}

.ld-hero__close {
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

.ld-hero__close:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

:global(.el-dialog.prh-dialog) {
  padding: 0;
  overflow: hidden;
  border-radius: 14px;
}

:global(.el-dialog.prh-dialog .el-dialog__header) {
  padding: 0;
  margin: 0;
}

:global(.el-dialog.prh-dialog .el-dialog__body) {
  padding: 12px 16px;
}

:global(.el-dialog.prh-dialog .el-dialog__footer) {
  padding: 10px 16px 14px;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
}

.dlg-btn {
  --k-rgb: 100 116 139;
  height: 30px;
  padding: 0 16px;
  border-radius: var(--ml-radius-sm);
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

.dlg-btn--reset {
  --k-rgb: 217 119 6;
  color: #b45309;
  border-color: #fde68a;
  background: linear-gradient(180deg, #ffffff 0%, #fffbeb 100%);
}

.dlg-btn--reset:hover,
.dlg-btn--reset:focus-visible {
  color: #92400e;
  border-color: #fbbf24;
  background: #fff;
}

.dlg-btn--save {
  --k-rgb: 79 70 229;
  color: #fff;
  border-color: #4338ca;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #6366f1, #4338ca);
}

.dlg-btn--save:hover,
.dlg-btn--save:focus-visible {
  color: #fff;
  border-color: #3730a3;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.26) 0%, rgba(255, 255, 255, 0) 52%),
    linear-gradient(135deg, #7477f3, #4f46e5);
}

.detail-content {
  display: grid;
  grid-template-columns: 1fr;
  gap: 6px;
}

.detail-row {
  position: relative;
  display: grid;
  grid-template-columns: 88px 1fr;
  gap: 8px;
  align-items: start;
  padding: 8px 10px 8px 13px;
  overflow: hidden;
  border-radius: var(--ml-radius-sm);
  border: 1px solid #e0e7ff;
  background: linear-gradient(180deg, #ffffff 0%, #f8f9ff 100%);
}

.detail-row::before {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 3px;
  background: linear-gradient(180deg, #a5b4fc, #4f46e5);
}

.detail-row label {
  font-size: 12px;
  font-weight: 700;
  color: #4338ca;
}

.detail-row span {
  font-size: 13px;
  color: var(--ml-text);
  word-break: break-word;
}

.column-settings {
  max-height: min(58vh, 420px);
  overflow-y: auto;
  padding: 2px 2px 0;
}

.column-group {
  position: relative;
  margin-bottom: 8px;
  padding: 10px 10px 8px;
  overflow: hidden;
  border-radius: 10px;
  border: 1px solid #e0e7ff;
  background: linear-gradient(180deg, #ffffff 0%, #f8f9ff 100%);
}

.column-group::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #818cf8, #6d28d9);
}

.column-group:last-child {
  margin-bottom: 0;
}

.column-group h4 {
  margin: 0 0 6px;
  padding-bottom: 5px;
  font-size: 12px;
  font-weight: 800;
  color: #3730a3;
  border-bottom: 1px dashed #c7d2fe;
}

.column-group :deep(.el-checkbox) {
  display: flex;
  align-items: center;
  height: auto;
  margin: 0;
  padding: 4px 6px;
  border-radius: 6px;
  font-size: 12px;
}

.column-group :deep(.el-checkbox:hover) {
  background: #eef2ff;
}

.column-group :deep(.el-checkbox.is-checked .el-checkbox__label) {
  font-weight: 700;
  color: #3730a3;
}

/* ---------- レスポンシブ ---------- */
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

  .modern-pagination {
    justify-content: center;
  }
}

@media (max-width: 600px) {
  .part-logs-container {
    padding: 6px;
    gap: 6px;
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

  .filter-card__actions .fc-btn {
    flex: 1;
  }
}
</style>
