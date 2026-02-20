<template>
  <div class="outsourcing-receiving-page">
    <!-- 页面头部 -->
    <div class="page-header plating-header">
      <div class="header-content">
        <div class="title-section">
          <h2 class="title">
            <div class="title-icon">
              <el-icon><Download /></el-icon>
            </div>
            <span class="title-text">外注メッキ受入</span>
            <div class="title-badge">
              <span class="badge-text">{{ receivingList.length }}</span>
            </div>
          </h2>
          <p class="subtitle">外注メッキ品の受入検収処理を行います</p>
        </div>
        <div class="header-stats">
          <div class="stat-item">
            <span class="stat-value">{{ pendingCount }}</span>
            <span class="stat-label">未検収</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ todayCount }}</span>
            <span class="stat-label">本日入庫</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 検索フィルター -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filters" class="filter-form">
        <!-- 期間フィルタ -->
        <div class="filter-group">
          <span class="filter-label">期間</span>
          <div class="date-filter-container">
            <el-date-picker
              v-model="filters.dateRange"
              type="daterange"
              range-separator="〜"
              start-placeholder="開始日"
              end-placeholder="終了日"
              value-format="YYYY-MM-DD"
              class="date-picker"
              @change="handleSearch"
            />
            <div class="date-quick-btns">
              <el-button size="small" @click="setDatePrev" class="quick-btn">
                <el-icon><ArrowLeft /></el-icon>
              </el-button>
              <el-button
                size="small"
                @click="setDateToday"
                type="primary"
                class="quick-btn today-btn"
              >
                今日
              </el-button>
              <el-button size="small" @click="setDateNext" class="quick-btn">
                <el-icon><ArrowRight /></el-icon>
              </el-button>
              <el-button size="small" @click="setDateThisMonth" class="quick-btn month-btn">
                今月
              </el-button>
            </div>
          </div>
        </div>

        <!-- 外注先フィルタ -->
        <div class="filter-group">
          <span class="filter-label">外注先</span>
          <el-select
            v-model="filters.supplier"
            placeholder="全て"
            clearable
            filterable
            class="supplier-select"
            @change="handleSearch"
          >
            <el-option
              v-for="s in supplierOptions"
              :key="s.value"
              :label="s.label"
              :value="s.value"
            />
          </el-select>
        </div>

        <!-- 製品フィルタ -->
        <div class="filter-group">
          <span class="filter-label">製品</span>
          <el-select
            v-model="filters.productName"
            placeholder="全て"
            clearable
            filterable
            class="product-select"
            @change="handleSearch"
          >
            <el-option v-for="name in productNameOptions" :key="name" :label="name" :value="name" />
          </el-select>
        </div>

        <!-- キーワードフィルタ -->
        <div class="filter-group">
          <span class="filter-label">キーワード</span>
          <el-input
            v-model="filters.keyword"
            placeholder="製品名で検索..."
            clearable
            class="keyword-input"
            @input="debouncedSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>

        <!-- 検収状態フィルタ -->
        <div class="filter-group">
          <span class="filter-label">状態</span>
          <el-select
            v-model="filters.status"
            placeholder="全て"
            clearable
            class="status-select"
            @change="handleSearch"
          >
            <el-option label="未検収" value="未検収" />
            <el-option label="一部検収" value="一部検収" />
            <el-option label="検収済" value="検収済" />
          </el-select>
        </div>

        <!-- リセットボタン -->
        <div class="filter-group filter-actions">
          <el-button @click="resetFilters" class="reset-btn">
            <el-icon><Refresh /></el-icon>
            リセット
          </el-button>
        </div>
      </el-form>
    </el-card>

    <!-- 操作按钮栏 -->
    <div class="action-bar">
      <div class="left-actions">
        <el-button type="primary" @click="openReceivingDialog">
          <el-icon><Plus /></el-icon>受入登録
        </el-button>
        <el-button type="warning" @click="handlePrint">
          <el-icon><Printer /></el-icon>印刷
        </el-button>
      </div>
      <div class="right-actions">
        <el-tag type="success" size="large" class="total-tag">
          <el-icon><Box /></el-icon>
          本日入庫: {{ todayQuantity.toLocaleString() }} 個
        </el-tag>
      </div>
    </div>

    <!-- 数据表格 -->
    <el-card class="table-card">
      <el-table
        ref="tableRef"
        :data="receivingList"
        v-loading="loading"
        stripe
        border
        highlight-current-row
        class="data-table"
        size="small"
        :header-cell-style="{ background: '#f5f7fa', color: '#606266', fontWeight: '600' }"
        :row-class-name="tableRowClassName"
      >
        <el-table-column prop="receivingNo" label="受入番号" width="130" fixed="left">
          <template #default="{ row }">
            <el-link type="primary" @click="viewDetail(row)">{{ row.receivingNo }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="receivingDate" label="受入予定日" width="100" />
        <el-table-column prop="orderNo" label="注文番号" width="140">
          <template #default="{ row }">
            <el-link type="info" @click="viewOrder(row)">{{ row.orderNo }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="supplier" label="外注先" width="140">
          <template #default="{ row }">
            <span :class="getSupplierColorClass(row.supplier)" class="supplier-text">
              {{ row.supplier }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="productCode" label="製品CD" width="90" />
        <el-table-column prop="productName" label="製品名" min-width="130" show-overflow-tooltip />
        <!-- <el-table-column prop="platingType" label="メッキ種類" width="100" /> -->
        <el-table-column prop="orderQty" label="注文数" width="80" align="right">
          <template #default="{ row }">
            {{ row.orderQty.toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column prop="receivingQty" label="受入数" width="80" align="right">
          <template #default="{ row }">
            <span class="receiving-qty">{{ row.receivingQty.toLocaleString() }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="goodQty" label="良品数" width="80" align="right">
          <template #default="{ row }">
            <span class="good-qty">{{ row.goodQty.toLocaleString() }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="defectQty" label="不良数" width="80" align="right">
          <template #default="{ row }">
            <span :class="{ 'defect-qty': row.defectQty > 0 }">{{
              row.defectQty.toLocaleString()
            }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="検収状態" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row)" size="small" effect="plain">
              {{ getStatusLabel(row) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="inspector" label="検収者" width="80" />
        <el-table-column label="操作" width="70" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="editReceiving(row)" :icon="Edit" />
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[20, 50, 100, 200]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSearch"
          @current-change="handleSearch"
        />
      </div>
    </el-card>

    <!-- 新建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="836px"
      destroy-on-close
      class="receiving-dialog"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="85px"
        class="compact-form receiving-form"
      >
        <!-- 基本信息区域 -->
        <div class="form-section form-section-primary">
          <div class="section-header">
            <span class="section-icon">📋</span>
            <span class="section-title">基本情報</span>
          </div>
          <el-row :gutter="10">
            <el-col :span="12">
              <el-form-item label="注文番号" prop="orderNo" class="form-item-primary">
                <el-select
                  v-model="formData.orderNo"
                  placeholder="注文を選択"
                  filterable
                  style="width: 100%"
                  :disabled="isEdit"
                  @change="handleOrderChange"
                >
                  <el-option
                    v-for="o in orderOptions"
                    :key="o.orderNo"
                    :label="`${o.orderNo} ${o.productName}（残: ${o.remainQty}）`"
                    :value="o.orderNo"
                  >
                    <div style="display: flex; justify-content: space-between; align-items: center">
                      <span style="font-weight: 500">{{ o.orderNo }}</span>
                      <span style="color: #606266; font-size: 12px; margin-left: 8px"
                        >{{ o.productName }}（残: {{ o.remainQty }}）</span
                      >
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="受入予定" prop="receivingDate" class="form-item-primary">
                <el-date-picker
                  v-model="formData.receivingDate"
                  type="date"
                  value-format="YYYY-MM-DD"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="10">
            <el-col :span="8">
              <el-form-item label="外注先" class="form-item-info">
                <el-input v-model="formData.supplier" disabled />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="製品CD" class="form-item-info">
                <el-input v-model="formData.productCode" disabled />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="製品名" class="form-item-info">
                <el-input v-model="formData.productName" disabled />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 数量信息区域 -->
        <div class="form-section form-section-warning">
          <div class="section-header">
            <span class="section-icon">📊</span>
            <span class="section-title">数量情報</span>
          </div>
          <el-row :gutter="10">
            <el-col :span="6">
              <el-form-item label="注文数" class="form-item-warning">
                <el-input :model-value="formData.orderQty?.toLocaleString()" disabled />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="既納数" class="form-item-info">
                <el-input :model-value="formData.deliveredQty?.toLocaleString()" disabled />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="残数" class="form-item-danger">
                <el-input
                  :model-value="formData.remainQty?.toLocaleString()"
                  disabled
                  class="remain-input"
                />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="メッキ種類" class="form-item-info">
                <el-input v-model="formData.platingType" disabled />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 検収情報区域 -->
        <div class="form-section form-section-success">
          <div class="section-header">
            <span class="section-icon">✅</span>
            <span class="section-title">検収情報</span>
          </div>
          <el-row :gutter="10">
            <el-col :span="8">
              <el-form-item label="受入数" prop="receivingQty" class="form-item-success">
                <el-input-number
                  v-model="formData.receivingQty"
                  :min="1"
                  :max="formData.orderQty || 99999"
                  style="width: 100%"
                  @change="handleQtyChange"
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="良品数" prop="goodQty" class="form-item-success">
                <el-input-number
                  v-model="formData.goodQty"
                  :min="0"
                  :max="
                    Math.min(formData.orderQty || 0, formData.receivingQty || 0) ||
                    formData.orderQty ||
                    0
                  "
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="不良数" class="form-item-danger">
                <el-input-number
                  v-model="formData.defectQty"
                  :min="0"
                  style="width: 100%"
                  disabled
                />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="10">
            <el-col :span="12">
              <el-form-item label="不良理由" class="form-item-danger">
                <el-select
                  v-model="formData.defectReason"
                  placeholder="選択"
                  clearable
                  style="width: 100%"
                  :disabled="formData.defectQty === 0"
                >
                  <el-option label="メッキ不良" value="plating_defect" />
                  <el-option label="傷・打痕" value="scratch" />
                  <el-option label="変形" value="deform" />
                  <el-option label="寸法不良" value="dimension" />
                  <el-option label="その他" value="other" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="検収者" prop="inspector" class="form-item-primary">
                <el-select
                  v-model="formData.inspector"
                  placeholder="検収者を選択"
                  filterable
                  style="width: 100%"
                  clearable
                >
                  <el-option
                    v-for="user in inspectorOptions"
                    :key="user.value"
                    :label="user.label"
                    :value="user.value"
                  />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item label="備考" class="form-item-info">
            <el-input
              v-model="formData.remarks"
              type="textarea"
              :rows="2"
              placeholder="備考を入力"
            />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false" size="default">キャンセル</el-button>
          <el-button type="primary" @click="submitForm" :loading="submitLoading" size="default">
            {{ isEdit ? '更新' : '登録' }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="受入詳細" width="680px" class="detail-dialog">
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="受入番号">{{ detailData.receivingNo }}</el-descriptions-item>
        <el-descriptions-item label="受入日">{{ detailData.receivingDate }}</el-descriptions-item>
        <el-descriptions-item label="注文番号">{{ detailData.orderNo }}</el-descriptions-item>
        <el-descriptions-item label="外注先">{{ detailData.supplier }}</el-descriptions-item>
        <el-descriptions-item label="品番">{{ detailData.productCode }}</el-descriptions-item>
        <el-descriptions-item label="品名">{{ detailData.productName }}</el-descriptions-item>
        <el-descriptions-item label="メッキ種類">{{ detailData.platingType }}</el-descriptions-item>
        <el-descriptions-item label="注文数">{{
          detailData.orderQty?.toLocaleString()
        }}</el-descriptions-item>
        <el-descriptions-item label="受入数">{{
          detailData.receivingQty?.toLocaleString()
        }}</el-descriptions-item>
        <el-descriptions-item label="良品数">{{
          detailData.goodQty?.toLocaleString()
        }}</el-descriptions-item>
        <el-descriptions-item label="不良数">
          <span :class="{ 'text-danger': (detailData.defectQty || 0) > 0 }">
            {{ (detailData.defectQty || 0).toLocaleString() }}
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="検収状態">
          <el-tag :type="getStatusType(detailData as ReceivingItem)" size="small">{{
            getStatusLabel(detailData as ReceivingItem)
          }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="検収者">{{
          detailData.inspector || '-'
        }}</el-descriptions-item>
        <el-descriptions-item label="備考" :span="2">{{
          detailData.remarks || '-'
        }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- 订单详情对话框 -->
    <el-dialog v-model="orderDetailVisible" title="注文詳細" width="700px" class="detail-dialog">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="注文番号">{{ orderDetailData.orderNo }}</el-descriptions-item>
        <el-descriptions-item label="注文日">{{ orderDetailData.orderDate }}</el-descriptions-item>
        <el-descriptions-item label="外注先">{{ orderDetailData.supplier }}</el-descriptions-item>
        <el-descriptions-item label="品番">{{ orderDetailData.productCode }}</el-descriptions-item>
        <el-descriptions-item label="品名" :span="2">{{
          orderDetailData.productName
        }}</el-descriptions-item>
        <el-descriptions-item label="メッキ種類">{{
          orderDetailData.platingType
        }}</el-descriptions-item>
        <el-descriptions-item label="数量">{{
          formatNumber(orderDetailData.quantity)
        }}</el-descriptions-item>
        <el-descriptions-item label="単価">
          {{ formatCurrency(orderDetailData.unitPrice) }}
        </el-descriptions-item>
        <el-descriptions-item label="金額">
          {{ formatCurrency(orderDetailData.amount) }}
        </el-descriptions-item>
        <el-descriptions-item label="納期">{{ orderDetailData.deliveryDate }}</el-descriptions-item>
        <el-descriptions-item label="入庫数">{{
          formatNumber(orderDetailData.receivedQty)
        }}</el-descriptions-item>
        <el-descriptions-item label="状態">
          <el-tag :type="getOrderStatusType(orderDetailData as OrderItem)">{{
            getOrderStatusLabel(orderDetailData as OrderItem)
          }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="備考" :span="2">{{
          orderDetailData.remarks || '-'
        }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Refresh,
  Plus,
  Download,
  Edit,
  Box,
  ArrowLeft,
  ArrowRight,
  Printer,
  EditPen,
  Check,
  Close,
} from '@element-plus/icons-vue'
import {
  getPlatingReceivings,
  createPlatingReceiving,
  updatePlatingReceiving,
  getPendingPlatingOrders,
  getPlatingOrdersByOrderNo,
  type PlatingReceiving,
} from '@/api/outsourcing'
import { getSuppliers, type OutsourcingSupplier } from '@/api/outsourcing'
import request from '@/utils/request'

interface ReceivingItem {
  id: number
  receivingNo: string
  receivingDate: string
  orderNo: string
  orderId: number
  supplier: string
  supplierId?: number
  productCode: string
  productName: string
  platingType: string
  orderQty: number
  receivingQty: number
  goodQty: number
  defectQty: number
  defectReason?: string
  status: string
  inspector: string
  remarks?: string
  remainQty?: number
}

interface OrderOption {
  id: number
  orderNo: string
  productCode: string
  productName: string
  supplier: string
  supplierId?: number
  platingType: string
  orderQty: number
  deliveredQty: number
  remainQty: number
}

interface OrderItem {
  id: number
  orderNo: string
  orderDate: string
  supplier: string
  supplierId?: number
  supplierCd?: string
  productCode: string
  productName: string
  platingType: string
  quantity: number
  unitPrice: number
  amount: number
  deliveryDate: string
  receivedQty: number
  status: string
  remarks?: string
  deliveryLocation?: string
  category?: string
  content?: string
  specification?: string
}

// 数据转换：后端snake_case -> 前端camelCase
const convertReceivingFromBackend = (item: any): ReceivingItem => {
  return {
    id: item.id,
    receivingNo: item.receiving_no || item.receivingNo,
    receivingDate: item.receiving_date || item.receivingDate,
    orderNo: item.order_no || item.orderNo,
    orderId: item.order_id || item.orderId,
    supplier: item.supplier_name || item.supplier || '',
    supplierId: item.supplier_id || item.supplierId,
    productCode: item.product_cd || item.productCode,
    productName: item.product_name || item.productName,
    platingType: item.plating_type || item.platingType,
    orderQty: item.order_qty || item.orderQty || 0,
    receivingQty: item.receiving_qty || item.receivingQty || 0,
    goodQty: item.good_qty || item.goodQty || 0,
    defectQty: item.defect_qty || item.defectQty || 0,
    defectReason: item.defect_reason || item.defectReason,
    status: item.status || 'pending',
    inspector: item.inspector || '',
    remarks: item.remarks || '',
  }
}

const loading = ref(false)
const submitLoading = ref(false)
const dialogVisible = ref(false)
const detailVisible = ref(false)
const isEdit = ref(false)
const tableRef = ref()

const filters = reactive({
  dateRange: [] as string[],
  supplier: '',
  productName: '',
  keyword: '',
  status: '',
})

// 产品名称选项列表
const productNameOptions = ref<string[]>([])

// 防抖搜索定时器
let searchTimer: ReturnType<typeof setTimeout> | null = null

// 防抖搜索函数
const debouncedSearch = () => {
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
  searchTimer = setTimeout(() => {
    handleSearch()
  }, 300)
}

// 日期快捷操作方法
const setDateToday = () => {
  const today = formatDate(getJapanDate())
  filters.dateRange = [today, today]
  handleSearch()
}

const setDatePrev = () => {
  if (filters.dateRange && filters.dateRange.length === 2) {
    const start = new Date(filters.dateRange[0])
    const end = new Date(filters.dateRange[1])
    start.setDate(start.getDate() - 1)
    end.setDate(end.getDate() - 1)
    filters.dateRange = [formatDate(start), formatDate(end)]
  } else {
    const yesterday = new Date(getJapanDate())
    yesterday.setDate(yesterday.getDate() - 1)
    filters.dateRange = [formatDate(yesterday), formatDate(yesterday)]
  }
  handleSearch()
}

const setDateNext = () => {
  if (filters.dateRange && filters.dateRange.length === 2) {
    const start = new Date(filters.dateRange[0])
    const end = new Date(filters.dateRange[1])
    start.setDate(start.getDate() + 1)
    end.setDate(end.getDate() + 1)
    filters.dateRange = [formatDate(start), formatDate(end)]
  } else {
    const tomorrow = new Date(getJapanDate())
    tomorrow.setDate(tomorrow.getDate() + 1)
    filters.dateRange = [formatDate(tomorrow), formatDate(tomorrow)]
  }
  handleSearch()
}

const setDateThisMonth = () => {
  const now = getJapanDate()
  const firstDay = new Date(now.getFullYear(), now.getMonth(), 1)
  const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0)
  filters.dateRange = [formatDate(firstDay), formatDate(lastDay)]
  handleSearch()
}

// 加载产品名称列表
const loadProductNames = async () => {
  try {
    const res = await request.get('/api/outsourcing/plating/receivings/products')
    if (res?.success && Array.isArray(res.data)) {
      productNameOptions.value = res.data
    } else if (Array.isArray(res)) {
      productNameOptions.value = res
    }
  } catch (error) {
    console.error('製品名一覧取得エラー:', error)
  }
}

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

const formRef = ref()
const formData = reactive({
  id: 0, // 受入ID（编辑时使用）
  orderId: 0,
  orderNo: '',
  receivingDate: '',
  supplier: '',
  supplierId: 0,
  productCode: '',
  productName: '',
  platingType: '',
  orderQty: 0,
  deliveredQty: 0,
  remainQty: 0,
  receivingQty: 0,
  goodQty: 0,
  defectQty: 0,
  defectReason: '',
  inspector: '',
  remarks: '',
})

const formRules = {
  orderNo: [{ required: true, message: '注文を選択してください', trigger: 'change' }],
  receivingDate: [{ required: true, message: '受入日を選択してください', trigger: 'change' }],
  receivingQty: [{ required: true, message: '受入数を入力してください', trigger: 'blur' }],
  goodQty: [{ required: true, message: '良品数を入力してください', trigger: 'blur' }],
  inspector: [{ required: true, message: '検収者を入力してください', trigger: 'blur' }],
}

const detailData = ref<Partial<ReceivingItem>>({})
const orderDetailVisible = ref(false)
const orderDetailData = ref<Partial<OrderItem>>({})

const receivingList = ref<ReceivingItem[]>([])

const supplierOptions = ref<Array<{ value: number; label: string }>>([])

const orderOptions = ref<OrderOption[]>([])

const inspectorOptions = ref<Array<{ value: string; label: string; name: string }>>([])

// 获取日本时区的当前日期
const getJapanDate = (): Date => {
  const now = new Date()
  const japanTime = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Tokyo' }))
  return japanTime
}

// 格式化日期为 YYYY-MM-DD
const formatDate = (date: Date): string => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// 加载外注先列表
const loadSuppliers = async () => {
  try {
    const res = await getSuppliers({ type: 'plating', isActive: true })
    let suppliers: any[] = []

    if (Array.isArray(res)) {
      suppliers = res
    } else if (res?.data && Array.isArray(res.data)) {
      suppliers = res.data
    } else if (res?.success && Array.isArray(res.data)) {
      suppliers = res.data
    }

    supplierOptions.value = suppliers.map((s) => {
      const supplierId = s.id
      const supplierName = s.supplier_name || s.name || ''
      const supplierCd = s.supplier_cd || s.code || ''
      return {
        value: supplierId,
        label: supplierCd ? `${supplierCd} - ${supplierName}` : supplierName,
      }
    })
  } catch (error) {
    console.error('外注先取得エラー:', error)
    ElMessage.error('外注先データの取得に失敗しました')
  }
}

// 加载用户列表（用于検収者下拉框）
const loadInspectors = async () => {
  try {
    const res = await request.get('/api/master/users')
    let users: any[] = []

    if (res?.success && Array.isArray(res.data)) {
      users = res.data
    } else if (Array.isArray(res)) {
      users = res
    } else if (res?.data && Array.isArray(res.data)) {
      users = res.data
    }

    // 过滤出 username 以 "1" 开头的用户
    const filteredUsers = users.filter((u: any) => {
      const username = u.username || ''
      return username.startsWith('1')
    })

    inspectorOptions.value = filteredUsers.map((u: any) => {
      const username = u.username || ''
      const name = u.name || ''
      const displayName = name ? `${username} - ${name}` : username
      return {
        value: username, // 使用 username 作为值（用于选择）
        label: displayName, // 显示 username - name
        name: name, // 保存 name 字段
      }
    })
  } catch (error) {
    console.error('検収者一覧取得エラー:', error)
    ElMessage.error('検収者データの取得に失敗しました')
  }
}

// 加载未完成订单列表（用于新建受入）
const loadPendingOrders = async () => {
  try {
    const res = await getPendingPlatingOrders()
    let orders: any[] = []

    // 处理不同的响应格式
    if (res?.success && Array.isArray(res.data)) {
      orders = res.data
    } else if (res?.data && Array.isArray(res.data)) {
      orders = res.data
    } else if (Array.isArray(res)) {
      orders = res
    }

    console.log('加载的订单数据:', orders)

    orderOptions.value = orders
      .map((o: any) => {
        const order = {
          id: o.id,
          orderNo: o.order_no || o.orderNo,
          productCode: o.product_cd || o.productCode,
          productName: o.product_name || o.productName,
          supplier: o.supplier_name || o.supplier || '',
          supplierId: o.supplier_id || o.supplierId,
          platingType: o.plating_type || o.platingType,
          orderQty: o.quantity || o.orderQty || 0,
          deliveredQty: o.received_qty || o.receivedQty || 0,
          remainQty: o.remaining_qty || o.remainQty || 0,
        }
        console.log('映射后的订单:', order)
        return order
      })
      .filter((order) => {
        // 过滤掉注文番号为 "os-004" 的订单
        if (order.orderNo === 'os-004') {
          return false
        }
        // 过滤掉产品名开头为 "900" 的订单
        if (order.productName && order.productName.startsWith('900')) {
          return false
        }
        return true
      })

    console.log('订单选项列表:', orderOptions.value)
  } catch (error) {
    console.error('未完了注文取得エラー:', error)
    ElMessage.error('未完了注文データの取得に失敗しました')
  }
}

const pendingCount = computed(
  () => receivingList.value.filter((i) => calculateStatus(i) === '未検収').length,
)
const todayCount = computed(() => {
  const today = formatDate(getJapanDate())
  return receivingList.value.filter((i) => i.receivingDate === today).length
})
const todayQuantity = computed(() => {
  const today = formatDate(getJapanDate())
  return receivingList.value
    .filter((i) => i.receivingDate === today)
    .reduce((sum, i) => sum + i.receivingQty, 0)
})
const dialogTitle = computed(() => (isEdit.value ? '受入編集' : '新規受入'))

watch(
  () => formData.receivingQty,
  (val) => {
    if (val && formData.goodQty > val) {
      formData.goodQty = val
    }
    formData.defectQty = (val || 0) - (formData.goodQty || 0)
  },
)

watch(
  () => formData.goodQty,
  (val) => {
    formData.defectQty = (formData.receivingQty || 0) - (val || 0)
  },
)

// 根据受入数和注文数计算検収状態
const calculateStatus = (row: ReceivingItem): string => {
  const receivingQty = row.receivingQty || 0
  const orderQty = row.orderQty || 0

  if (receivingQty === 0) {
    return '未検収'
  } else if (receivingQty === orderQty) {
    return '検収済'
  } else if (receivingQty > 0 && receivingQty < orderQty) {
    return '一部検収'
  } else {
    return '未検収'
  }
}

const getStatusType = (
  row: ReceivingItem,
): 'success' | 'info' | 'warning' | 'primary' | 'danger' => {
  const status = calculateStatus(row)
  const types: Record<string, 'success' | 'info' | 'warning' | 'primary' | 'danger'> = {
    未検収: 'warning',
    検収済: 'success',
    一部検収: 'info',
  }
  return types[status] || 'info'
}

const getStatusLabel = (row: ReceivingItem) => {
  return calculateStatus(row)
}

// 日本数字格式化
const formatNumber = (value: number | null | undefined): string => {
  if (value == null || isNaN(value)) return '0'
  return value.toLocaleString('ja-JP')
}

// 日本货币格式化
const formatCurrency = (value: number | null | undefined): string => {
  if (value == null || isNaN(value)) return '¥0'
  return `¥${value.toLocaleString('ja-JP')}`
}

// 订单状态计算
const calculateOrderStatus = (row: OrderItem): string => {
  const receivedQty = row.receivedQty || 0
  const quantity = row.quantity || 0

  if (receivedQty === 0) {
    return '未発注'
  } else if (receivedQty === quantity) {
    return '受入完'
  } else if (receivedQty > 0 && receivedQty < quantity) {
    return '一部受入'
  } else {
    return '発注済'
  }
}

// 订单状态类型
const getOrderStatusType = (
  row: OrderItem,
): 'success' | 'info' | 'warning' | 'primary' | 'danger' => {
  const status = calculateOrderStatus(row)
  const types: Record<string, 'success' | 'info' | 'warning' | 'primary' | 'danger'> = {
    未発注: 'info',
    発注済: 'warning',
    一部受入: 'primary',
    受入完: 'success',
  }
  return types[status] || 'info'
}

const getOrderStatusLabel = (row: OrderItem) => {
  return calculateOrderStatus(row)
}

// 根据外注先名称生成颜色类
const getSupplierColorClass = (supplier: string | undefined): string => {
  if (!supplier) return 'supplier-color-0'

  // 使用简单的hash函数生成稳定的颜色索引
  let hash = 0
  for (let i = 0; i < supplier.length; i++) {
    hash = supplier.charCodeAt(i) + ((hash << 5) - hash)
  }
  // 生成0-7之间的索引，对应8种不同的颜色
  const colorIndex = Math.abs(hash) % 8
  return `supplier-color-${colorIndex}`
}

const tableRowClassName = ({ row }: { row: ReceivingItem }) => {
  const status = calculateStatus(row)
  if (status === '未検収') return 'pending-row'
  if (row.defectQty > 0) return 'defect-row'
  return ''
}

const handleSearch = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      pageSize: pagination.pageSize,
    }

    if (filters.dateRange && filters.dateRange.length === 2) {
      params.startDate = filters.dateRange[0]
      params.endDate = filters.dateRange[1]
    }

    if (filters.supplier) {
      params.supplierId = filters.supplier
    }

    if (filters.productName) {
      params.productName = filters.productName
    }

    if (filters.keyword) {
      params.keyword = filters.keyword
    }

    // 注意：状态筛选在前端进行，因为状态是根据受入数和注文数计算的
    // 不向后端传递状态筛选参数

    const res = await getPlatingReceivings(params)
    let data: any[] = []
    let total = 0

    if (res?.success && res.data) {
      data = Array.isArray(res.data) ? res.data : []
      total = res.total || 0
    } else if (Array.isArray(res)) {
      data = res
    } else if (res?.data && Array.isArray(res.data)) {
      data = res.data
      total = res.total || data.length
    }

    receivingList.value = data.map(convertReceivingFromBackend)

    // 如果筛选条件中有状态，需要根据计算的状态进行过滤
    if (filters.status) {
      receivingList.value = receivingList.value.filter((item) => {
        const status = calculateStatus(item)
        return status === filters.status
      })
      // 更新总数（筛选后的数量）
      total = receivingList.value.length
    }

    pagination.total = total
  } catch (error: any) {
    console.error('受入一覧取得エラー:', error)
    ElMessage.error(error?.message || '受入一覧の取得に失敗しました')
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  const today = formatDate(getJapanDate())
  Object.assign(filters, {
    dateRange: [today, today],
    supplier: '',
    productName: '',
    keyword: '',
    status: '',
  })
  handleSearch()
}

const openReceivingDialog = async () => {
  isEdit.value = false
  await loadInspectors() // 确保検収者选项已加载
  Object.assign(formData, {
    orderId: 0,
    orderNo: '',
    receivingDate: formatDate(getJapanDate()),
    supplier: '',
    supplierId: 0,
    productCode: '',
    productName: '',
    platingType: '',
    orderQty: 0,
    deliveredQty: 0,
    remainQty: 0,
    receivingQty: 0,
    goodQty: 0,
    defectQty: 0,
    defectReason: '',
    inspector: '',
    remarks: '',
  })
  await loadPendingOrders()
  dialogVisible.value = true
}

const handleOrderChange = (orderNo: string) => {
  console.log('选择的订单号:', orderNo)
  console.log('可用的订单选项:', orderOptions.value)
  const order = orderOptions.value.find((o) => o.orderNo === orderNo)
  if (order) {
    console.log('找到的订单:', order)
    formData.orderId = order.id
    formData.supplier = order.supplier
    formData.supplierId = order.supplierId || 0
    formData.productCode = order.productCode
    formData.productName = order.productName
    formData.platingType = order.platingType
    formData.orderQty = order.orderQty
    formData.deliveredQty = order.deliveredQty
    formData.remainQty = order.remainQty
    // 编辑模式下不修改受入数、良品数等字段，保持原有值
    if (!isEdit.value) {
      formData.receivingQty = order.remainQty
      formData.goodQty = order.remainQty
    }
    console.log('更新后的表单数据:', formData)
  } else {
    console.error('未找到订单:', orderNo)
    ElMessage.warning('選択した注文が見つかりません')
  }
}

const handleQtyChange = (val: number | undefined) => {
  if (val !== undefined) {
    formData.goodQty = val
  }
}

const editReceiving = async (row: ReceivingItem) => {
  isEdit.value = true
  const remainQty = row.remainQty || row.orderQty - row.receivingQty

  await loadInspectors() // 确保 inspectorOptions 已加载，再做映射

  // 根据 name 找到对应的 username（因为数据库中存储的是 name）
  const getInspectorUsername = (name: string | null | undefined): string => {
    if (!name) return ''
    const inspector = inspectorOptions.value.find((opt) => opt.name === name)
    return inspector?.value || ''
  }

  // 保存原始的受入数和良品数，确保在编辑模式下不会被重置
  const originalReceivingQty = row.receivingQty || 0
  const originalGoodQty = row.goodQty || 0
  const originalDefectQty = row.defectQty || 0

  Object.assign(formData, {
    id: row.id, // 受入ID
    orderId: row.orderId,
    orderNo: row.orderNo,
    receivingDate: row.receivingDate,
    supplier: row.supplier,
    supplierId: row.supplierId || 0,
    productCode: row.productCode,
    productName: row.productName,
    platingType: row.platingType,
    orderQty: row.orderQty,
    deliveredQty: row.orderQty - remainQty,
    remainQty: remainQty,
    receivingQty: originalReceivingQty,
    goodQty: originalGoodQty,
    defectQty: originalDefectQty,
    defectReason: row.defectReason || '',
    inspector: getInspectorUsername(row.inspector), // 根据 name 找到 username
    remarks: row.remarks || '',
  })
  await loadPendingOrders()
  // 在加载订单列表后，重新确保受入数等字段保持原值（防止被重置）
  formData.receivingQty = originalReceivingQty
  formData.goodQty = originalGoodQty
  formData.defectQty = originalDefectQty
  await loadInspectors() // 确保 inspectorOptions 已加载
  dialogVisible.value = true
}

const viewDetail = (row: ReceivingItem) => {
  detailData.value = row
  detailVisible.value = true
}

// 数据转换：后端snake_case -> 前端camelCase（订单）
const convertOrderFromBackend = (item: any): OrderItem => {
  return {
    id: item.id,
    orderNo: item.order_no || item.orderNo,
    orderDate: item.order_date || item.orderDate,
    supplier: item.supplier_name || item.supplier || '',
    supplierId: item.supplier_id || item.supplierId,
    supplierCd: item.supplier_cd || item.supplierCd,
    productCode: item.product_cd || item.productCode,
    productName: item.product_name || item.productName,
    platingType: item.plating_type || item.platingType,
    quantity: item.quantity || 0,
    unitPrice: Number(item.unit_price || item.unitPrice || 0),
    amount: Number(item.amount || 0),
    deliveryDate: item.delivery_date || item.deliveryDate,
    receivedQty: item.received_qty || item.receivedQty || 0,
    status: item.status || 'pending',
    remarks: item.remarks || '',
    deliveryLocation: item.delivery_location || item.deliveryLocation,
    category: item.category,
    content: item.content,
    specification: item.specification,
  }
}

const viewOrder = async (row: ReceivingItem) => {
  try {
    loading.value = true
    const res = await getPlatingOrdersByOrderNo(row.orderNo)

    let orders: any[] = []
    if (Array.isArray(res)) {
      orders = res
    } else if (res?.data && Array.isArray(res.data)) {
      orders = res.data
    } else if (res?.success && Array.isArray(res.data)) {
      orders = res.data
    }

    if (orders.length === 0) {
      ElMessage.warning('注文データが見つかりません')
      return
    }

    // 使用第一条记录作为详情（如果有多条，可以后续扩展为列表显示）
    const order = convertOrderFromBackend(orders[0])
    orderDetailData.value = order
    orderDetailVisible.value = true
  } catch (error: any) {
    console.error('注文取得エラー:', error)
    ElMessage.error('注文データの取得に失敗しました')
  } finally {
    loading.value = false
  }
}

const submitForm = async () => {
  const valid = await formRef.value?.validate()
  if (!valid) return

  // 验证订单ID
  if (!formData.orderId || formData.orderId === 0) {
    ElMessage.warning('注文を選択してください')
    return
  }

  // 数量上限校验：受入数、良品数均不得超过注文数，且良品数不得超过受入数
  const orderQty = formData.orderQty || 0
  if (formData.receivingQty > orderQty) {
    ElMessage.warning('受入数は注文数以下にしてください')
    return
  }
  if (formData.goodQty > orderQty) {
    ElMessage.warning('良品数は注文数以下にしてください')
    return
  }
  if (formData.goodQty > formData.receivingQty) {
    ElMessage.warning('良品数は受入数以下にしてください')
    return
  }

  submitLoading.value = true
  try {
    // 将空字符串转换为 null，避免后端处理 undefined
    const safeValue = (value: any) => (value === '' || value === undefined ? null : value)

    // 根据选择的 username 找到对应的 name
    const getInspectorName = (username: string | null | undefined): string | null => {
      if (!username) return null
      const inspector = inspectorOptions.value.find((opt) => opt.value === username)
      return inspector?.name || null
    }

    if (isEdit.value) {
      // 编辑受入
      if (!formData.id || formData.id === 0) {
        ElMessage.warning('受入IDが見つかりません')
        return
      }
      const data = {
        receiving_date: formData.receivingDate,
        receiving_qty: formData.receivingQty,
        good_qty: formData.goodQty,
        defect_qty: formData.defectQty,
        defect_reason: safeValue(formData.defectReason),
        inspector: safeValue(getInspectorName(formData.inspector)),
        remarks: safeValue(formData.remarks),
      }
      console.log('更新的受入数据:', data)
      await updatePlatingReceiving(formData.id, data)
      ElMessage.success('更新しました')
      dialogVisible.value = false
      handleSearch()
    } else {
      // 新規受入（实际上是更新已存在的受入记录）
      const data = {
        order_id: formData.orderId,
        receiving_date: formData.receivingDate,
        receiving_qty: formData.receivingQty,
        good_qty: formData.goodQty,
        defect_qty: formData.defectQty,
        defect_reason: safeValue(formData.defectReason),
        inspector: safeValue(getInspectorName(formData.inspector)),
        remarks: safeValue(formData.remarks),
      }
      console.log('提交的受入数据:', data)
      await createPlatingReceiving(data)
      ElMessage.success('更新しました')
      dialogVisible.value = false
      handleSearch()
    }
  } catch (error: any) {
    console.error('受入登録エラー:', error)
    const errorMsg = error?.response?.data?.message || error?.message || 'エラーが発生しました'
    ElMessage.error(errorMsg)
  } finally {
    submitLoading.value = false
  }
}

// 打印功能
const handlePrint = () => {
  if (receivingList.value.length === 0) {
    ElMessage.warning('印刷するデータがありません')
    return
  }

  // 生成打印内容
  const printContent = generatePrintHtml(receivingList.value)

  // 创建打印窗口
  const printWindow = window.open('', '_blank')
  if (printWindow) {
    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>外注メッキ受入一覧</title>
        <meta charset="UTF-8">
        <style>
          @page {
            size: A4 portrait;
            margin: 12mm;
          }
          body {
            font-family: 'Meiryo', 'Yu Gothic', sans-serif;
            margin: 0;
            padding: 0;
            font-size: 9pt;
            line-height: 1.2;
          }
          .print-header {
            text-align: center;
            margin-bottom: 6mm;
            border-bottom: 1.5px solid #333;
            padding-bottom: 2mm;
          }
          .print-title {
            font-size: 16pt;
            font-weight: bold;
            margin-bottom: 1.5mm;
          }
          .print-date {
            font-size: 9pt;
            color: #666;
          }
          .print-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 5mm;
            font-size: 8pt;
          }
          .print-table th,
          .print-table td {
            border: 1px solid #333;
            padding: 2mm 1mm;
            text-align: left;
          }
          .print-table th {
            background-color: #f5f5f5;
            font-weight: bold;
            text-align: center;
          }
          .print-table td {
            text-align: center;
          }
          .print-table .text-left {
            text-align: left;
          }
          .print-table .text-right {
            text-align: right;
          }
          .status-tag {
            display: inline-block;
            padding: 1px 6px;
            border-radius: 2px;
            font-size: 7pt;
            font-weight: 500;
          }
          .status-warning {
            background-color: #fef0c0;
            color: #e6a23c;
          }
          .status-success {
            background-color: #f0f9ff;
            color: #67c23a;
          }
          .status-info {
            background-color: #f4f4f5;
            color: #909399;
          }
          @media print {
            body {
              margin: 0;
              padding: 0;
            }
            .print-table {
              page-break-inside: auto;
            }
            .print-table tr {
              page-break-inside: auto;
              page-break-after: auto;
            }
            .print-table thead {
              display: table-header-group;
            }
            .print-table tfoot {
              display: table-footer-group;
            }
            .group-header-row {
              page-break-after: avoid;
            }
          }
        </style>
      </head>
      <body>
        ${printContent}
      </body>
      </html>
    `)
    printWindow.document.close()

    // 等待页面加载完成后打印
    printWindow.onload = function () {
      printWindow.print()
      // 打印完成后延迟关闭窗口
      setTimeout(function () {
        printWindow.close()
      }, 1000)
    }
  }
}

// 生成打印HTML内容
const generatePrintHtml = (data: ReceivingItem[]): string => {
  const now = getJapanDate()
  const printDate = now.toLocaleString('ja-JP', {
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })

  // 按検収状態分组
  const groupedData = new Map<string, ReceivingItem[]>()
  data.forEach((row) => {
    const status = calculateStatus(row)
    if (!groupedData.has(status)) {
      groupedData.set(status, [])
    }
    groupedData.get(status)!.push(row)
  })

  // 定义状态显示顺序
  const statusOrder = ['未検収', '一部検収', '検収済']

  // 对每个分组内的数据进行排序：先按受入予定日升序，再按製品名升序
  const sortedGroups = statusOrder
    .filter((status) => groupedData.has(status))
    .map((status) => {
      const groupData = groupedData.get(status)!
      return {
        status,
        data: groupData.sort((a, b) => {
          // 首先按受入予定日排序
          const dateA = a.receivingDate || ''
          const dateB = b.receivingDate || ''
          if (dateA !== dateB) {
            return dateA.localeCompare(dateB, 'ja-JP')
          }
          // 如果受入予定日相同，则按製品名排序
          const nameA = a.productName || ''
          const nameB = b.productName || ''
          return nameA.localeCompare(nameB, 'ja-JP', { numeric: true, sensitivity: 'base' })
        }),
      }
    })

  // 生成表头
  let tableRows = `
    <thead>
      <tr>
        <th style="width: 14%;">受入予定日</th>
        <th style="width: 17%;">外注先</th>
        <th style="width: 13%;">製品名</th>
        <th style="width: 9%;">注文数</th>
        <th style="width: 9%;">受入数</th>
        <th style="width: 9%;">良品数</th>
        <th style="width: 9%;">不良数</th>
        <th style="width: 10%;">検収状態</th>
      </tr>
    </thead>
    <tbody>
  `

  // 按分组生成表格行
  sortedGroups.forEach((group) => {
    const status = group.status
    const statusClass =
      status === '未検収'
        ? 'status-warning'
        : status === '検収済'
          ? 'status-success'
          : 'status-info'

    // 添加分组标题行
    tableRows += `
      <tr class="group-header-row" style="background-color: #f0f0f0; font-weight: bold;">
        <td colspan="8" style="padding: 2mm 1mm; font-size: 9pt;">
          <span class="status-tag ${statusClass}">${status}</span>
        </td>
      </tr>
    `

    // 生成该分组的数据行
    group.data.forEach((row) => {
      tableRows += `
        <tr>
          <td class="text-center">${row.receivingDate || '-'}</td>
          <td class="text-left">${row.supplier || '-'}</td>
          <td class="text-left">${row.productName || '-'}</td>
          <td class="text-right">${(row.orderQty || 0).toLocaleString('ja-JP')}</td>
          <td class="text-right">${(row.receivingQty || 0).toLocaleString('ja-JP')}</td>
          <td class="text-right">${(row.goodQty || 0).toLocaleString('ja-JP')}</td>
          <td class="text-right">${(row.defectQty || 0).toLocaleString('ja-JP')}</td>
          <td>
            <span class="status-tag ${statusClass}">${status}</span>
          </td>
        </tr>
      `
    })
  })

  tableRows += '</tbody>'

  // 生成总计行（所有数据的总计）
  const totalOrderQty = data.reduce((sum, row) => sum + (row.orderQty || 0), 0)
  const totalReceivingQty = data.reduce((sum, row) => sum + (row.receivingQty || 0), 0)
  const totalGoodQty = data.reduce((sum, row) => sum + (row.goodQty || 0), 0)
  const totalDefectQty = data.reduce((sum, row) => sum + (row.defectQty || 0), 0)

  tableRows += `
    <tfoot>
      <tr style="font-weight: bold; background-color: #f5f5f5;">
        <td colspan="3" class="text-right">合計</td>
        <td class="text-right">${totalOrderQty.toLocaleString('ja-JP')}</td>
        <td class="text-right">${totalReceivingQty.toLocaleString('ja-JP')}</td>
        <td class="text-right">${totalGoodQty.toLocaleString('ja-JP')}</td>
        <td class="text-right">${totalDefectQty.toLocaleString('ja-JP')}</td>
        <td></td>
      </tr>
    </tfoot>
  `

  return `
    <div class="print-header">
      <div class="print-title">外注メッキ受入一覧</div>
      <div class="print-date">印刷日時: ${printDate}</div>
    </div>
    <table class="print-table">
      ${tableRows}
    </table>
  `
}

onMounted(async () => {
  // 初始化日期为当天
  const today = formatDate(getJapanDate())
  filters.dateRange = [today, today]

  await loadSuppliers()
  await loadInspectors()
  await loadProductNames()
  await handleSearch()
})
</script>

<style scoped>
.outsourcing-receiving-page {
  padding: 10px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ed 100%);
  min-height: 100vh;
}

.page-header {
  border-radius: 8px;
  padding: 14px 18px;
  margin-bottom: 10px;
  color: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.plating-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 3px 15px rgba(102, 126, 234, 0.35);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-section {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  line-height: 1.2;
}

.title-icon {
  width: 38px;
  height: 38px;
  background: rgba(255, 255, 255, 0.25);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  backdrop-filter: blur(10px);
}

.title-badge {
  background: rgba(255, 255, 255, 0.3);
  padding: 3px 10px;
  border-radius: 16px;
  font-size: 13px;
  font-weight: 600;
  backdrop-filter: blur(10px);
}

.subtitle {
  margin: 0;
  font-size: 12px;
  opacity: 0.95;
  line-height: 1.3;
}

.header-stats {
  display: flex;
  gap: 12px;
}

.stat-item {
  text-align: center;
  padding: 8px 14px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  min-width: 65px;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

.stat-item:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateY(-1px);
}

.stat-value {
  display: block;
  font-size: 18px;
  font-weight: 700;
  line-height: 1.2;
}

.stat-label {
  font-size: 10px;
  opacity: 0.95;
  margin-top: 2px;
}

.filter-card {
  margin-bottom: 10px;
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(102, 126, 234, 0.08);
  border: 1px solid rgba(102, 126, 234, 0.12);
  background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
}

.filter-card :deep(.el-card__body) {
  padding: 12px 16px;
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.filter-label {
  font-size: 12px;
  font-weight: 600;
  color: #606266;
  white-space: nowrap;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.date-filter-container {
  display: flex;
  align-items: center;
  gap: 6px;
}

.date-picker {
  width: 220px;
}

.date-picker :deep(.el-input__wrapper) {
  border-radius: 6px;
  box-shadow: 0 0 0 1px rgba(102, 126, 234, 0.2) inset;
  transition: all 0.2s;
}

.date-picker :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #667eea inset;
}

.date-quick-btns {
  display: flex;
  gap: 2px;
}

.quick-btn {
  padding: 6px 8px;
  font-size: 12px;
  border-radius: 4px;
  border: 1px solid rgba(102, 126, 234, 0.3);
  background: white;
  color: #667eea;
  transition: all 0.2s;
}

.quick-btn:hover {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: transparent;
  transform: translateY(-1px);
}

.quick-btn :deep(.el-icon) {
  font-size: 12px;
}

.today-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: transparent;
  color: white;
  font-weight: 600;
}

.today-btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.month-btn {
  background: rgba(102, 126, 234, 0.1);
  border-color: rgba(102, 126, 234, 0.3);
}

.supplier-select {
  width: 208px;
}

.supplier-select :deep(.el-input__wrapper) {
  border-radius: 6px;
  box-shadow: 0 0 0 1px rgba(102, 126, 234, 0.2) inset;
}

.supplier-select :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #667eea inset;
}

.product-select {
  width: 180px;
}

.product-select :deep(.el-input__wrapper) {
  border-radius: 6px;
  box-shadow: 0 0 0 1px rgba(102, 126, 234, 0.2) inset;
}

.product-select :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #667eea inset;
}

.keyword-input {
  width: 160px;
}

.keyword-input :deep(.el-input__wrapper) {
  border-radius: 6px;
  box-shadow: 0 0 0 1px rgba(102, 126, 234, 0.2) inset;
}

.keyword-input :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #667eea inset;
}

.keyword-input :deep(.el-input__prefix) {
  color: #667eea;
}

.status-select {
  width: 100px;
}

.status-select :deep(.el-input__wrapper) {
  border-radius: 6px;
  box-shadow: 0 0 0 1px rgba(102, 126, 234, 0.2) inset;
}

.status-select :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #667eea inset;
}

.filter-actions {
  margin-left: auto;
}

.reset-btn {
  padding: 6px 12px;
  font-size: 12px;
  border-radius: 6px;
  border: 1px solid rgba(102, 126, 234, 0.3);
  background: white;
  color: #667eea;
  transition: all 0.2s;
}

.reset-btn:hover {
  background: rgba(102, 126, 234, 0.1);
  border-color: #667eea;
}

.reset-btn :deep(.el-icon) {
  margin-right: 4px;
}

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding: 10px 14px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.04);
}

.left-actions {
  display: flex;
  gap: 8px;
}

.left-actions :deep(.el-button) {
  padding: 8px 16px;
  font-size: 13px;
  border-radius: 6px;
  font-weight: 500;
}

.total-tag {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  font-size: 13px;
  border-radius: 6px;
}

.table-card {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.table-card :deep(.el-card__body) {
  padding: 0;
}

.data-table {
  border-radius: 8px;
}

.data-table :deep(.el-table__header-wrapper) {
  border-radius: 8px 8px 0 0;
}

.data-table :deep(.el-table__header th) {
  font-weight: 600;
  padding: 6px 0;
  height: 36px;
  font-size: 12px;
  background: linear-gradient(to bottom, #fafbfc 0%, #f5f7fa 100%);
  border-bottom: 2px solid #ebeef5;
}

.data-table :deep(.el-table__body td) {
  padding: 4px 0;
  height: 36px;
  font-size: 12px;
  border-bottom: 1px solid #f0f2f5;
}

.data-table :deep(.el-table__body tr) {
  height: 36px;
  transition: background-color 0.2s;
}

.data-table :deep(.el-table__body tr:hover) {
  background-color: #f5f7fa;
}

.data-table :deep(.el-table .cell) {
  padding: 0 8px;
  line-height: 1.4;
}

.data-table :deep(.el-link) {
  font-size: 12px;
  font-weight: 500;
}

.data-table :deep(.el-button--small) {
  padding: 4px 10px;
  font-size: 12px;
  border-radius: 4px;
}

.data-table :deep(.el-button--small .el-icon) {
  font-size: 14px;
}

.data-table :deep(.el-tag) {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.data-table :deep(.pending-row) {
  background-color: #fef9e7;
}

.data-table :deep(.pending-row:hover) {
  background-color: #fef5d7;
}

.data-table :deep(.defect-row) {
  background-color: #fdecea;
}

.data-table :deep(.defect-row:hover) {
  background-color: #fce2e0;
}

.receiving-qty {
  font-weight: 600;
  color: #667eea;
  font-size: 12px;
}

.good-qty {
  font-weight: 600;
  color: #67c23a;
  font-size: 12px;
}

.defect-qty {
  font-weight: 600;
  color: #f56c6c;
  font-size: 12px;
}

.supplier-text {
  font-weight: 500;
  padding: 2px 6px;
  border-radius: 4px;
  display: inline-block;
  font-size: 12px;
}

.supplier-color-0 {
  color: #667eea;
  background-color: #e8ecff;
}

.supplier-color-1 {
  color: #67c23a;
  background-color: #e8f5e9;
}

.supplier-color-2 {
  color: #e6a23c;
  background-color: #fef5e7;
}

.supplier-color-3 {
  color: #f56c6c;
  background-color: #fdecea;
}

.supplier-color-4 {
  color: #909399;
  background-color: #f4f4f5;
}

.supplier-color-5 {
  color: #409eff;
  background-color: #e1f3ff;
}

.supplier-color-6 {
  color: #9c27b0;
  background-color: #f3e5f5;
}

.supplier-color-7 {
  color: #00bcd4;
  background-color: #e0f7fa;
}

.text-danger {
  color: #f56c6c;
  font-weight: 500;
}

.pagination-wrapper {
  padding: 10px 14px;
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid #ebeef5;
  background: #fafbfc;
}

.pagination-wrapper :deep(.el-pagination) {
  font-size: 12px;
}

.pagination-wrapper :deep(.el-pagination .el-pager li),
.pagination-wrapper :deep(.el-pagination .btn-prev),
.pagination-wrapper :deep(.el-pagination .btn-next) {
  min-width: 28px;
  height: 28px;
  line-height: 28px;
  font-size: 12px;
}

.receiving-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 50%, #ff8c42 100%);
  color: white;
  margin: 0;
  padding: 10px 16px;
  border-radius: 8px 8px 0 0;
  box-shadow: 0 2px 6px rgba(255, 107, 107, 0.2);
}

.receiving-dialog :deep(.el-dialog__title) {
  color: white;
  font-weight: 600;
  font-size: 15px;
}

.receiving-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: white;
  font-size: 18px;
}

.receiving-dialog :deep(.el-dialog__headerbtn:hover .el-dialog__close) {
  color: rgba(255, 255, 255, 0.8);
}

.receiving-dialog :deep(.el-dialog__body) {
  padding: 12px 16px;
  background: #f5f7fa;
}

.receiving-form {
  background: transparent;
  padding: 0;
}

.remain-input :deep(.el-input__inner) {
  color: #f56c6c;
  font-weight: 700;
  background: linear-gradient(to right, #fef0f0 0%, #fff 50%);
}

/* 表单区域分组 */
.form-section {
  background: #fff;
  border-radius: 6px;
  padding: 8px 10px;
  margin-bottom: 7px;
  border-left: 3px solid;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: all 0.2s ease;
}

.form-section:hover {
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
}

.form-section-primary {
  border-left-color: #409eff;
  background: linear-gradient(to right, #ecf5ff 0%, #fff 10%);
}

.form-section-warning {
  border-left-color: #e6a23c;
  background: linear-gradient(to right, #fdf6ec 0%, #fff 10%);
}

.form-section-success {
  border-left-color: #67c23a;
  background: linear-gradient(to right, #f0f9ff 0%, #fff 10%);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 7px;
  padding-bottom: 5px;
  border-bottom: 1px solid #ebeef5;
}

.section-icon {
  font-size: 13px;
}

.section-title {
  font-size: 12px;
  font-weight: 700;
  color: #303133;
  letter-spacing: 0.3px;
}

.compact-form :deep(.el-form-item) {
  margin-bottom: 5px;
}

.receiving-dialog :deep(.el-form-item) {
  margin-bottom: 5px;
}

.receiving-dialog :deep(.el-form-item__label) {
  font-size: 12px;
  font-weight: 600;
  color: #606266;
  line-height: 26px;
  padding-right: 6px;
  height: 26px;
}

/* 不同字段类型的颜色区分 */
.form-item-primary :deep(.el-form-item__label) {
  color: #409eff;
}

.form-item-success :deep(.el-form-item__label) {
  color: #67c23a;
}

.form-item-warning :deep(.el-form-item__label) {
  color: #e6a23c;
}

.form-item-danger :deep(.el-form-item__label) {
  color: #f56c6c;
}

.form-item-info :deep(.el-form-item__label) {
  color: #909399;
}

.receiving-dialog :deep(.el-input__wrapper),
.receiving-dialog :deep(.el-select .el-input__wrapper),
.receiving-dialog :deep(.el-textarea__inner) {
  border-radius: 4px;
  transition: all 0.2s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  border: 1px solid #dcdfe6;
  height: 26px;
  padding: 0 8px;
}

.receiving-dialog :deep(.el-input__inner) {
  height: 26px;
  line-height: 26px;
  font-size: 13px;
}

.receiving-dialog :deep(.el-input__wrapper:hover),
.receiving-dialog :deep(.el-select .el-input__wrapper:hover) {
  border-color: #c0c4cc;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.receiving-dialog :deep(.el-input.is-focus .el-input__wrapper),
.receiving-dialog :deep(.el-select.is-focus .el-input__wrapper) {
  border-color: #ff6b6b;
  box-shadow: 0 0 0 2px rgba(255, 107, 107, 0.1);
}

/* 不同类型输入框的颜色 */
.form-item-primary :deep(.el-input.is-focus .el-input__wrapper),
.form-item-primary :deep(.el-select.is-focus .el-input__wrapper) {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.1);
}

.form-item-success :deep(.el-input.is-focus .el-input__wrapper),
.form-item-success :deep(.el-select.is-focus .el-input__wrapper),
.form-item-success :deep(.el-input-number.is-focus .el-input__wrapper) {
  border-color: #67c23a;
  box-shadow: 0 0 0 2px rgba(103, 194, 58, 0.1);
}

.form-item-warning :deep(.el-input.is-focus .el-input__wrapper) {
  border-color: #e6a23c;
  box-shadow: 0 0 0 2px rgba(230, 162, 60, 0.1);
}

.form-item-danger :deep(.el-input.is-focus .el-input__wrapper),
.form-item-danger :deep(.el-select.is-focus .el-input__wrapper) {
  border-color: #f56c6c;
  box-shadow: 0 0 0 2px rgba(245, 108, 108, 0.1);
}

.receiving-dialog :deep(.el-input-number) {
  width: 100%;
}

.receiving-dialog :deep(.el-input-number .el-input__wrapper) {
  height: 26px;
  border-radius: 4px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  border: 1px solid #dcdfe6;
}

.receiving-dialog :deep(.el-input-number .el-input__inner) {
  height: 26px;
  line-height: 26px;
  font-size: 13px;
}

.receiving-dialog :deep(.el-input-number .el-input__wrapper:hover) {
  border-color: #c0c4cc;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.receiving-dialog :deep(.el-input-number.is-focus .el-input__wrapper) {
  border-color: #ff6b6b;
  box-shadow: 0 0 0 2px rgba(255, 107, 107, 0.1);
}

.receiving-dialog :deep(.el-date-editor) {
  height: 26px;
}

.receiving-dialog :deep(.el-date-editor .el-input__wrapper) {
  height: 26px;
}

.receiving-dialog :deep(.el-date-editor .el-input__inner) {
  height: 26px;
  line-height: 26px;
  font-size: 13px;
}

.receiving-dialog :deep(.el-textarea__inner) {
  min-height: 50px;
  padding: 5px 8px;
  border-radius: 4px;
  font-size: 13px;
}

.receiving-dialog :deep(.el-dialog__footer) {
  padding: 10px 16px;
  border-top: 1px solid #ebeef5;
  background: #fff;
  border-radius: 0 0 8px 8px;
}

.receiving-dialog :deep(.el-button) {
  padding: 7px 16px;
  font-size: 13px;
  border-radius: 4px;
  font-weight: 500;
  transition: all 0.2s ease;
  height: 30px;
}

.receiving-dialog :deep(.el-button--primary) {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
  border: none;
  box-shadow: 0 2px 4px rgba(255, 107, 107, 0.25);
}

.receiving-dialog :deep(.el-button--primary:hover) {
  background: linear-gradient(135deg, #ff5252 0%, #e63946 100%);
  box-shadow: 0 3px 8px rgba(255, 107, 107, 0.35);
  transform: translateY(-1px);
}

.receiving-dialog :deep(.el-button--default:hover) {
  border-color: #ff6b6b;
  color: #ff6b6b;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.receiving-dialog :deep(.el-input.is-disabled .el-input__wrapper) {
  background-color: #f5f7fa;
  cursor: not-allowed;
  border-color: #e4e7ed;
  color: #909399;
}

.receiving-dialog :deep(.el-select.is-disabled .el-input__wrapper) {
  background-color: #f5f7fa;
  cursor: not-allowed;
  border-color: #e4e7ed;
}

/* 数量输入框特殊样式 */
.form-item-success :deep(.el-input-number__increase),
.form-item-success :deep(.el-input-number__decrease) {
  background-color: #f0f9ff;
  color: #67c23a;
  border-color: #c2e7b0;
}

.form-item-success :deep(.el-input-number__increase:hover),
.form-item-success :deep(.el-input-number__decrease:hover) {
  background-color: #e1f3d8;
  color: #529b2e;
}

.form-item-danger :deep(.el-input-number__increase),
.form-item-danger :deep(.el-input-number__decrease) {
  background-color: #fef0f0;
  color: #f56c6c;
  border-color: #fbc4c4;
}

.detail-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  margin: 0;
  padding: 14px 18px;
  border-radius: 8px 8px 0 0;
}

.detail-dialog :deep(.el-dialog__title) {
  color: white;
  font-weight: 600;
  font-size: 16px;
}

.detail-dialog :deep(.el-dialog__body) {
  padding: 16px 18px;
}

.detail-dialog :deep(.el-descriptions__label) {
  font-size: 12px;
  font-weight: 600;
  color: #606266;
  width: 100px;
}

.detail-dialog :deep(.el-descriptions__content) {
  font-size: 12px;
  color: #303133;
}

.detail-dialog :deep(.el-descriptions__table) {
  margin: 0;
}

.detail-dialog :deep(.el-descriptions__table td),
.detail-dialog :deep(.el-descriptions__table th) {
  padding: 8px 12px;
}

@media (max-width: 768px) {
  .outsourcing-receiving-page {
    padding: 8px;
  }
  .page-header {
    padding: 12px;
  }
  .title {
    font-size: 18px;
  }
  .header-stats {
    display: none;
  }
  .action-bar {
    flex-direction: column;
    gap: 10px;
  }
  .left-actions {
    flex-wrap: wrap;
    justify-content: center;
  }
}
</style>
