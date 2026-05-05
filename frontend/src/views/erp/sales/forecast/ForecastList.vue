<template>
  <div class="forecast-page">
    <div class="dynamic-background">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="noise-overlay"></div>
    </div>

    <div class="glass-header animate-in">
      <div class="header-content">
        <div class="header-left">
          <div class="header-icon">
            <el-icon size="26"><TrendCharts /></el-icon>
          </div>
          <div class="header-text">
            <h1 class="header-title">内示・フォーキャスト</h1>
            <div class="header-subtitle">Demand Forecast Management</div>
          </div>
          <div class="stat-badges">
            <div class="stat-badge"><span class="stat-num">{{ dataList.length }}</span><span class="stat-lbl">件</span></div>
            <div class="stat-badge confirmed"><span class="stat-num">{{ confirmedCount }}</span><span class="stat-lbl">確定</span></div>
          </div>
        </div>
        <el-button type="primary" size="small" class="create-btn" @click="showForm=true;editId=null">+ 新規登録</el-button>
      </div>
    </div>

    <div class="content-area">
      <div class="summary-section animate-in" style="animation-delay:0.08s">
        <div class="summary-grid">
          <div class="summary-card glass-card">
            <div class="sum-label">内示合計</div>
            <div class="sum-value">{{ totalForecast.toLocaleString() }}</div>
          </div>
          <div class="summary-card glass-card">
            <div class="sum-label">確定合計</div>
            <div class="sum-value confirmed-val">{{ totalConfirmed.toLocaleString() }}</div>
          </div>
          <div class="summary-card glass-card">
            <div class="sum-label">達成率</div>
            <div class="sum-value rate-val">{{ achievementRate }}%</div>
          </div>
        </div>
      </div>

      <div class="filter-section glass-card animate-in" style="animation-delay:0.1s">
        <div class="filter-row">
          <el-input v-model="filters.keyword" placeholder="顧客コード・品番で検索" clearable size="small" class="filter-input" @input="fetchData">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-date-picker v-model="filters.month" type="month" size="small" placeholder="予測月" format="YYYY/MM" value-format="YYYY-MM" class="filter-month" @change="fetchData" />
          <el-select v-model="filters.status" placeholder="ステータス" clearable size="small" class="filter-sel" @change="fetchData">
            <el-option label="予測" value="forecast" />
            <el-option label="確定" value="confirmed" />
            <el-option label="修正" value="revised" />
          </el-select>
        </div>
      </div>

      <div class="table-section glass-card animate-in" style="animation-delay:0.15s">
        <el-table :data="dataList" v-loading="loading" size="small" class="dark-table" :header-cell-style="headerStyle" :cell-style="cellStyle">
          <el-table-column prop="customer_code" label="顧客コード" width="110">
            <template #default="{row}"><span class="code-text">{{ row.customer_code }}</span></template>
          </el-table-column>
          <el-table-column prop="customer_name" label="顧客名" min-width="120" show-overflow-tooltip />
          <el-table-column prop="product_code" label="品番" width="110">
            <template #default="{row}"><span class="code-text">{{ row.product_code }}</span></template>
          </el-table-column>
          <el-table-column prop="product_name" label="品名" min-width="120" show-overflow-tooltip />
          <el-table-column prop="forecast_month" label="予測月" width="100" align="center" />
          <el-table-column prop="forecast_quantity" label="内示数量" width="100" align="right">
            <template #default="{row}"><span class="qty-text">{{ (row.forecast_quantity||0).toLocaleString() }}</span></template>
          </el-table-column>
          <el-table-column prop="confirmed_quantity" label="確定数量" width="100" align="right">
            <template #default="{row}"><span class="confirmed-text">{{ (row.confirmed_quantity||0).toLocaleString() }}</span></template>
          </el-table-column>
          <el-table-column label="達成率" width="140" align="center">
            <template #default="{row}">
              <div class="progress-wrap">
                <el-progress :percentage="getRate(row)" :stroke-width="6" :color="getProgressColor(getRate(row))" :show-text="false" />
                <span class="progress-text">{{ getRate(row) }}%</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="ステータス" width="90" align="center">
            <template #default="{row}">
              <el-tag :type="row.status==='confirmed'?'success':row.status==='revised'?'warning':'info'" size="small" effect="dark">
                {{ row.status==='confirmed'?'確定':row.status==='revised'?'修正':'予測' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="アクション" width="150" align="center" fixed="right">
            <template #default="{row}">
              <el-button v-if="row.status==='forecast'" size="small" type="success" plain @click="handleConfirm(row)">確定</el-button>
              <el-button size="small" type="primary" plain @click="openEdit(row)">編集</el-button>
              <el-button size="small" type="danger" plain @click="handleDelete(row)">削除</el-button>
            </template>
          </el-table-column>
          <template #empty>
            <div class="empty-state"><el-icon size="40"><Document /></el-icon><p>フォーキャストデータがありません</p></div>
          </template>
        </el-table>
        <div class="pagination-wrap" v-if="total > pageSize">
          <el-pagination :current-page="page" :page-size="pageSize" :total="total" layout="prev, pager, next" small @current-change="p=>{page=p;fetchData()}" />
        </div>
      </div>
    </div>

    <el-dialog v-model="showForm" :title="editId?'フォーキャスト編集':'フォーキャスト登録'" width="480px" :close-on-click-modal="false">
      <el-form :model="form" label-width="100px" size="small">
        <el-form-item label="顧客コード"><el-input v-model="form.customer_code" /></el-form-item>
        <el-form-item label="顧客名"><el-input v-model="form.customer_name" /></el-form-item>
        <el-form-item label="品番"><el-input v-model="form.product_code" /></el-form-item>
        <el-form-item label="品名"><el-input v-model="form.product_name" /></el-form-item>
        <el-form-item label="予測月"><el-date-picker v-model="form.forecast_month" type="month" format="YYYY-MM" value-format="YYYY-MM" style="width:100%" /></el-form-item>
        <el-form-item label="内示数量"><el-input-number v-model="form.forecast_quantity" :min="0" style="width:100%" /></el-form-item>
        <el-form-item label="確定数量"><el-input-number v-model="form.confirmed_quantity" :min="0" style="width:100%" /></el-form-item>
        <el-form-item label="備考"><el-input v-model="form.remarks" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showForm=false">キャンセル</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { TrendCharts, Search, Document } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'

const loading = ref(false)
const saving = ref(false)
const showForm = ref(false)
const editId = ref<number|null>(null)
const dataList = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(50)
const filters = ref({ keyword: '', month: '', status: '' })
const form = ref({ customer_code: '', customer_name: '', product_code: '', product_name: '', forecast_month: '', forecast_quantity: 0, confirmed_quantity: 0, remarks: '' })

const confirmedCount = computed(() => dataList.value.filter(i => i.status === 'confirmed').length)
const totalForecast = computed(() => dataList.value.reduce((s, i) => s + (i.forecast_quantity || 0), 0))
const totalConfirmed = computed(() => dataList.value.reduce((s, i) => s + (i.confirmed_quantity || 0), 0))
const achievementRate = computed(() => totalForecast.value > 0 ? Math.round(totalConfirmed.value / totalForecast.value * 100) : 0)

const headerStyle = { background: 'linear-gradient(135deg, #06b6d4, #0891b2)', color: '#fff', fontWeight: '600', fontSize: '12px', padding: '6px 10px' }
const cellStyle = { padding: '5px 8px', fontSize: '12px', background: 'rgba(255,255,255,0.03)', color: 'rgba(255,255,255,0.85)', borderColor: 'rgba(255,255,255,0.06)' }

function getRate(row: any) { return row.forecast_quantity > 0 ? Math.min(100, Math.round((row.confirmed_quantity || 0) / row.forecast_quantity * 100)) : 0 }
function getProgressColor(rate: number) { return rate >= 80 ? '#10b981' : rate >= 50 ? '#f59e0b' : '#ef4444' }

async function fetchData() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize.value }
    if (filters.value.status) params.status = filters.value.status
    if (filters.value.month) params.forecast_month = filters.value.month
    if (filters.value.keyword) { params.customer_code = filters.value.keyword; params.product_code = filters.value.keyword }
    const res: any = await request.get('/api/erp/sales/forecasts', { params })
    const data = res?.data ?? res
    dataList.value = data?.items || []
    total.value = data?.total || 0
  } catch { dataList.value = [] }
  finally { loading.value = false }
}

function openEdit(row: any) { editId.value = row.id; form.value = { ...row }; showForm.value = true }

async function handleSave() {
  saving.value = true
  try {
    if (editId.value) { await request.put(`/api/erp/sales/forecasts/${editId.value}`, form.value) }
    else { await request.post('/api/erp/sales/forecasts', form.value) }
    ElMessage.success('保存しました')
    showForm.value = false
    fetchData()
  } catch (e: any) { ElMessage.error(e?.response?.data?.detail || '保存に失敗しました') }
  finally { saving.value = false }
}

async function handleConfirm(row: any) {
  try {
    await ElMessageBox.confirm('このフォーキャストを確定しますか？', '確認')
    await request.post(`/api/erp/sales/forecasts/${row.id}/confirm`)
    ElMessage.success('確定しました')
    fetchData()
  } catch {}
}

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm('このデータを削除しますか？', '確認', { type: 'danger' })
    await request.delete(`/api/erp/sales/forecasts/${row.id}`)
    ElMessage.success('削除しました')
    fetchData()
  } catch {}
}

onMounted(fetchData)
</script>

<style scoped>
.forecast-page { position: relative; min-height: 100vh; padding: 16px; overflow: hidden; }
.dynamic-background { position: fixed; inset: 0; z-index: 0; background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%); }
.gradient-orb { position: absolute; border-radius: 50%; filter: blur(80px); opacity: 0.4; animation: float 20s ease-in-out infinite; }
.orb-1 { width: 350px; height: 350px; top: -80px; left: -80px; background: radial-gradient(circle, #06b6d4, transparent); }
.orb-2 { width: 300px; height: 300px; bottom: -50px; right: -50px; background: radial-gradient(circle, #0891b2, transparent); animation-delay: -10s; }
.noise-overlay { position: absolute; inset: 0; opacity: 0.03; }
@keyframes float { 0%,100%{transform:translate(0,0) scale(1)} 50%{transform:translate(20px,-20px) scale(1.03)} }

.glass-header { position: relative; z-index: 1; background: rgba(255,255,255,0.08); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.12); border-radius: 16px; padding: 14px 20px; margin-bottom: 14px; }
.header-content { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; }
.header-left { display: flex; align-items: center; gap: 12px; }
.header-icon { width: 44px; height: 44px; background: linear-gradient(135deg, #06b6d4, #0891b2); border-radius: 12px; display: flex; align-items: center; justify-content: center; color: #fff; }
.header-title { font-size: 1.4rem; font-weight: 700; color: #fff; margin: 0; }
.header-subtitle { font-size: 0.75rem; color: rgba(255,255,255,0.5); margin-top: 2px; }
.stat-badges { display: flex; gap: 8px; margin-left: 12px; }
.stat-badge { background: rgba(255,255,255,0.1); border-radius: 12px; padding: 3px 10px; display: flex; align-items: center; gap: 4px; }
.stat-badge.confirmed { background: rgba(16,185,129,0.2); }
.stat-num { font-size: 0.9rem; font-weight: 700; color: #fff; }
.stat-lbl { font-size: 0.65rem; color: rgba(255,255,255,0.7); }
.create-btn { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: #fff; }

.content-area { position: relative; z-index: 1; display: flex; flex-direction: column; gap: 12px; }
.glass-card { background: rgba(255,255,255,0.06); backdrop-filter: blur(16px); border: 1px solid rgba(255,255,255,0.1); border-radius: 14px; padding: 14px 16px; }

.summary-section { position: relative; z-index: 1; }
.summary-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.summary-card { text-align: center; padding: 12px; }
.sum-label { font-size: 0.72rem; color: rgba(255,255,255,0.5); margin-bottom: 4px; }
.sum-value { font-size: 1.3rem; font-weight: 700; color: #fff; }
.confirmed-val { color: #10b981; }
.rate-val { color: #06b6d4; }

.filter-row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.filter-input { flex: 1; min-width: 180px; }
.filter-month { width: 130px; }
.filter-sel { width: 120px; }

.code-text { font-family: 'Consolas', monospace; font-weight: 600; color: #22d3ee; font-size: 0.8rem; }
.qty-text { color: rgba(255,255,255,0.8); }
.confirmed-text { color: #10b981; font-weight: 600; }
.progress-wrap { display: flex; align-items: center; gap: 6px; }
.progress-wrap .el-progress { flex: 1; }
.progress-text { font-size: 0.72rem; color: rgba(255,255,255,0.7); min-width: 32px; }
.pagination-wrap { display: flex; justify-content: center; padding-top: 12px; }
.empty-state { padding: 30px; text-align: center; color: rgba(255,255,255,0.4); }
.empty-state p { margin-top: 8px; font-size: 0.85rem; }

:deep(.el-table) { background: transparent; --el-table-bg-color: transparent; --el-table-tr-bg-color: transparent; --el-table-border-color: rgba(255,255,255,0.06); --el-table-header-bg-color: transparent; --el-table-row-hover-bg-color: rgba(255,255,255,0.05); }
:deep(.el-table th), :deep(.el-table td) { border-color: rgba(255,255,255,0.06); }
:deep(.el-table__empty-text) { color: rgba(255,255,255,0.4); }
:deep(.el-progress-bar__outer) { background: rgba(255,255,255,0.1); }

.animate-in { animation: slideIn 0.5s ease forwards; opacity: 0; transform: translateY(12px); }
@keyframes slideIn { to { opacity: 1; transform: translateY(0); } }
@media (max-width: 768px) { .forecast-page { padding: 10px; } .summary-grid { grid-template-columns: 1fr; } .filter-row { flex-direction: column; } .filter-input,.filter-month,.filter-sel { width: 100%; } }
</style>
