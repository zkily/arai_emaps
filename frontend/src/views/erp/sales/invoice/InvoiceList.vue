<template>
  <div class="invoice-page">
    <div class="dynamic-background">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="noise-overlay"></div>
    </div>

    <div class="glass-header animate-in">
      <div class="header-content">
        <div class="header-left">
          <div class="header-icon">
            <el-icon size="26"><Money /></el-icon>
          </div>
          <div class="header-text">
            <h1 class="header-title">請求書発行</h1>
            <div class="header-subtitle">Invoice Management</div>
          </div>
          <div class="stat-badges">
            <div class="stat-badge"><span class="stat-num">{{ invoiceList.length }}</span><span class="stat-lbl">件</span></div>
            <div class="stat-badge warn"><span class="stat-num">{{ unpaidCount }}</span><span class="stat-lbl">未入金</span></div>
          </div>
        </div>
        <el-button type="primary" size="small" class="create-btn" @click="showCreate = true">+ 新規請求書</el-button>
      </div>
    </div>

    <div class="content-area">
      <div class="filter-section glass-card animate-in" style="animation-delay:0.1s">
        <div class="filter-row">
          <el-input v-model="filters.keyword" placeholder="請求番号・顧客名で検索" clearable size="small" class="filter-input" @input="fetchData">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-select v-model="filters.status" placeholder="ステータス" clearable size="small" class="filter-sel" @change="fetchData">
            <el-option label="下書き" value="draft" />
            <el-option label="発行済" value="issued" />
            <el-option label="入金済" value="paid" />
            <el-option label="期限超過" value="overdue" />
            <el-option label="キャンセル" value="cancelled" />
          </el-select>
          <el-date-picker v-model="filters.dateRange" type="daterange" size="small" range-separator="〜" start-placeholder="開始日" end-placeholder="終了日" format="YYYY/MM/DD" value-format="YYYY-MM-DD" class="filter-date" @change="fetchData" />
        </div>
      </div>

      <div class="table-section glass-card animate-in" style="animation-delay:0.15s">
        <el-table :data="invoiceList" v-loading="loading" size="small" class="dark-table" :header-cell-style="headerStyle" :cell-style="cellStyle">
          <el-table-column prop="invoice_no" label="請求番号" width="140">
            <template #default="{row}"><span class="code-text">{{ row.invoice_no }}</span></template>
          </el-table-column>
          <el-table-column prop="order_no" label="受注番号" width="130" show-overflow-tooltip />
          <el-table-column prop="customer_name" label="顧客名" min-width="140" show-overflow-tooltip />
          <el-table-column prop="invoice_date" label="請求日" width="110" align="center" />
          <el-table-column prop="due_date" label="支払期限" width="110" align="center">
            <template #default="{row}">
              <span :class="{'overdue-date': isOverdue(row)}">{{ row.due_date }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="total_amount" label="請求金額" width="120" align="right">
            <template #default="{row}"><span class="amount-text">¥{{ (row.total_amount||0).toLocaleString() }}</span></template>
          </el-table-column>
          <el-table-column prop="paid_amount" label="入金額" width="110" align="right">
            <template #default="{row}"><span class="paid-text">¥{{ (row.paid_amount||0).toLocaleString() }}</span></template>
          </el-table-column>
          <el-table-column prop="status" label="ステータス" width="100" align="center">
            <template #default="{row}">
              <el-tag :type="statusType(row.status)" size="small" effect="dark">{{ statusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="アクション" width="180" align="center" fixed="right">
            <template #default="{row}">
              <el-button v-if="row.status==='draft'" size="small" type="warning" plain @click="issueInv(row)">発行</el-button>
              <el-button v-if="row.status==='issued'" size="small" type="success" plain @click="openPayment(row)">入金</el-button>
              <el-button v-if="row.status==='draft'" size="small" type="danger" plain @click="deleteInv(row)">削除</el-button>
            </template>
          </el-table-column>
          <template #empty>
            <div class="empty-state"><el-icon size="40"><Document /></el-icon><p>請求データがありません</p></div>
          </template>
        </el-table>
        <div class="pagination-wrap" v-if="total > pageSize">
          <el-pagination :current-page="page" :page-size="pageSize" :total="total" layout="prev, pager, next" small @current-change="p => { page = p; fetchData() }" />
        </div>
      </div>
    </div>

    <el-dialog v-model="showCreate" title="請求書作成" width="600px" :close-on-click-modal="false">
      <el-form :model="form" label-width="100px" size="small">
        <el-form-item label="受注番号"><el-input v-model="form.order_no" placeholder="関連する受注番号" /></el-form-item>
        <el-form-item label="顧客コード"><el-input v-model="form.customer_code" /></el-form-item>
        <el-form-item label="顧客名"><el-input v-model="form.customer_name" /></el-form-item>
        <el-form-item label="請求日"><el-date-picker v-model="form.invoice_date" type="date" format="YYYY/MM/DD" value-format="YYYY-MM-DD" style="width:100%" /></el-form-item>
        <el-form-item label="支払期限"><el-date-picker v-model="form.due_date" type="date" format="YYYY/MM/DD" value-format="YYYY-MM-DD" style="width:100%" /></el-form-item>
        <el-form-item label="備考"><el-input v-model="form.remarks" type="textarea" :rows="2" /></el-form-item>
        <el-divider>明細</el-divider>
        <div v-for="(item, idx) in form.items" :key="idx" class="item-row">
          <el-input v-model="item.product_code" placeholder="品番" style="width:100px" size="small" />
          <el-input v-model="item.product_name" placeholder="品名" style="width:140px" size="small" />
          <el-input-number v-model="item.quantity" :min="1" placeholder="数量" style="width:90px" size="small" />
          <el-input-number v-model="item.unit_price" :min="0" placeholder="単価" style="width:100px" size="small" />
          <span class="item-amount">¥{{ ((item.quantity||0)*(item.unit_price||0)).toLocaleString() }}</span>
          <el-button size="small" type="danger" text @click="form.items.splice(idx,1)">✕</el-button>
        </div>
        <el-button size="small" type="primary" text @click="form.items.push({product_code:'',product_name:'',quantity:1,unit_price:0})">+ 明細追加</el-button>
      </el-form>
      <template #footer>
        <el-button @click="showCreate=false">キャンセル</el-button>
        <el-button type="primary" @click="handleCreate" :loading="saving">作成</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showPayment" title="入金記録" width="400px">
      <el-form label-width="80px" size="small">
        <el-form-item label="入金額"><el-input-number v-model="paymentAmount" :min="0" style="width:100%" /></el-form-item>
        <el-form-item label="入金方法">
          <el-select v-model="paymentMethod" style="width:100%">
            <el-option label="銀行振込" value="bank_transfer" />
            <el-option label="手形" value="bill" />
            <el-option label="現金" value="cash" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPayment=false">キャンセル</el-button>
        <el-button type="primary" @click="handlePayment">記録</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Money, Search, Document } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'

const loading = ref(false)
const saving = ref(false)
const showCreate = ref(false)
const showPayment = ref(false)
const invoiceList = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(50)
const filters = ref({ keyword: '', status: '', dateRange: null as any })
const form = ref({ order_no: '', customer_code: '', customer_name: '', invoice_date: '', due_date: '', remarks: '', items: [{ product_code: '', product_name: '', quantity: 1, unit_price: 0 }] })
const paymentAmount = ref(0)
const paymentMethod = ref('bank_transfer')
const selectedInvoice = ref<any>(null)

const unpaidCount = computed(() => invoiceList.value.filter(i => i.status === 'issued' || i.status === 'overdue').length)

const headerStyle = { background: 'linear-gradient(135deg, #6366f1, #4f46e5)', color: '#fff', fontWeight: '600', fontSize: '12px', padding: '6px 10px' }
const cellStyle = { padding: '5px 8px', fontSize: '12px', background: 'rgba(255,255,255,0.03)', color: 'rgba(255,255,255,0.85)', borderColor: 'rgba(255,255,255,0.06)' }

function statusType(s: string) { return s === 'draft' ? 'info' : s === 'issued' ? 'warning' : s === 'paid' ? 'success' : s === 'overdue' ? 'danger' : 'info' }
function statusLabel(s: string) { return { draft: '下書き', issued: '発行済', paid: '入金済', overdue: '期限超過', cancelled: 'キャンセル' }[s] || s }
function isOverdue(row: any) { return row.status === 'overdue' || (row.status === 'issued' && row.due_date && row.due_date < new Date().toISOString().slice(0, 10)) }

async function fetchData() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize.value }
    if (filters.value.status) params.status = filters.value.status
    if (filters.value.keyword) params.customer_code = filters.value.keyword
    if (filters.value.dateRange) { params.start_date = filters.value.dateRange[0]; params.end_date = filters.value.dateRange[1] }
    const res: any = await request.get('/api/erp/sales/invoices', { params })
    const data = res?.data ?? res
    invoiceList.value = data?.items || []
    total.value = data?.total || 0
  } catch { invoiceList.value = [] }
  finally { loading.value = false }
}

async function handleCreate() {
  saving.value = true
  try {
    await request.post('/api/erp/sales/invoices', form.value)
    ElMessage.success('請求書を作成しました')
    showCreate.value = false
    fetchData()
  } catch (e: any) { ElMessage.error(e?.response?.data?.detail || '作成に失敗しました') }
  finally { saving.value = false }
}

async function issueInv(row: any) {
  try {
    await ElMessageBox.confirm('この請求書を発行しますか？', '確認')
    await request.post(`/api/erp/sales/invoices/${row.id}/issue`)
    ElMessage.success('発行しました')
    fetchData()
  } catch {}
}

function openPayment(row: any) { selectedInvoice.value = row; paymentAmount.value = (row.total_amount || 0) - (row.paid_amount || 0); showPayment.value = true }

async function handlePayment() {
  if (!selectedInvoice.value) return
  try {
    await request.post(`/api/erp/sales/invoices/${selectedInvoice.value.id}/mark-paid`, { amount: paymentAmount.value, payment_method: paymentMethod.value })
    ElMessage.success('入金を記録しました')
    showPayment.value = false
    fetchData()
  } catch (e: any) { ElMessage.error(e?.response?.data?.detail || '入金記録に失敗しました') }
}

async function deleteInv(row: any) {
  try {
    await ElMessageBox.confirm('この請求書を削除しますか？', '確認', { type: 'danger' })
    await request.delete(`/api/erp/sales/invoices/${row.id}`)
    ElMessage.success('削除しました')
    fetchData()
  } catch {}
}

onMounted(fetchData)
</script>

<style scoped>
.invoice-page { position: relative; min-height: 100vh; padding: 16px; overflow: hidden; }
.dynamic-background { position: fixed; inset: 0; z-index: 0; background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%); }
.gradient-orb { position: absolute; border-radius: 50%; filter: blur(80px); opacity: 0.4; animation: float 20s ease-in-out infinite; }
.orb-1 { width: 350px; height: 350px; top: -80px; left: -80px; background: radial-gradient(circle, #6366f1, transparent); }
.orb-2 { width: 300px; height: 300px; bottom: -50px; right: -50px; background: radial-gradient(circle, #4f46e5, transparent); animation-delay: -10s; }
.noise-overlay { position: absolute; inset: 0; opacity: 0.03; }
@keyframes float { 0%,100%{transform:translate(0,0) scale(1)} 50%{transform:translate(20px,-20px) scale(1.03)} }

.glass-header { position: relative; z-index: 1; background: rgba(255,255,255,0.08); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.12); border-radius: 16px; padding: 14px 20px; margin-bottom: 14px; }
.header-content { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; }
.header-left { display: flex; align-items: center; gap: 12px; }
.header-icon { width: 44px; height: 44px; background: linear-gradient(135deg, #6366f1, #4f46e5); border-radius: 12px; display: flex; align-items: center; justify-content: center; color: #fff; }
.header-title { font-size: 1.4rem; font-weight: 700; color: #fff; margin: 0; }
.header-subtitle { font-size: 0.75rem; color: rgba(255,255,255,0.5); margin-top: 2px; }
.stat-badges { display: flex; gap: 8px; margin-left: 12px; }
.stat-badge { background: rgba(255,255,255,0.1); border-radius: 12px; padding: 3px 10px; display: flex; align-items: center; gap: 4px; }
.stat-badge.warn { background: rgba(245,158,11,0.2); }
.stat-num { font-size: 0.9rem; font-weight: 700; color: #fff; }
.stat-lbl { font-size: 0.65rem; color: rgba(255,255,255,0.7); }
.create-btn { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: #fff; }

.content-area { position: relative; z-index: 1; display: flex; flex-direction: column; gap: 12px; }
.glass-card { background: rgba(255,255,255,0.06); backdrop-filter: blur(16px); border: 1px solid rgba(255,255,255,0.1); border-radius: 14px; padding: 14px 16px; }

.filter-row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.filter-input { flex: 1; min-width: 180px; }
.filter-sel { width: 130px; }
.filter-date { width: 240px; }

.code-text { font-family: 'Consolas', monospace; font-weight: 600; color: #818cf8; font-size: 0.8rem; }
.amount-text { font-weight: 600; color: #fff; }
.paid-text { color: #10b981; }
.overdue-date { color: #ef4444; font-weight: 600; }

.pagination-wrap { display: flex; justify-content: center; padding-top: 12px; }
.empty-state { padding: 30px; text-align: center; color: rgba(255,255,255,0.4); }
.empty-state p { margin-top: 8px; font-size: 0.85rem; }

.item-row { display: flex; gap: 6px; align-items: center; margin-bottom: 8px; flex-wrap: wrap; }
.item-amount { font-size: 0.85rem; font-weight: 600; color: #6366f1; min-width: 80px; text-align: right; }

:deep(.el-table) { background: transparent; --el-table-bg-color: transparent; --el-table-tr-bg-color: transparent; --el-table-border-color: rgba(255,255,255,0.06); --el-table-header-bg-color: transparent; --el-table-row-hover-bg-color: rgba(255,255,255,0.05); }
:deep(.el-table th), :deep(.el-table td) { border-color: rgba(255,255,255,0.06); }
:deep(.el-table__empty-text) { color: rgba(255,255,255,0.4); }

.animate-in { animation: slideIn 0.5s ease forwards; opacity: 0; transform: translateY(12px); }
@keyframes slideIn { to { opacity: 1; transform: translateY(0); } }
@media (max-width: 768px) { .invoice-page { padding: 10px; } .filter-row { flex-direction: column; } .filter-input,.filter-sel,.filter-date { width: 100%; } }
</style>
