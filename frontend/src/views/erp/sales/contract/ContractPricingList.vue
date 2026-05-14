<template>
  <div class="contract-page">
    <div class="dynamic-background">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="noise-overlay"></div>
    </div>

    <div class="glass-header animate-in">
      <div class="header-content">
        <div class="header-left">
          <div class="header-icon">
            <el-icon size="26"><PriceTag /></el-icon>
          </div>
          <div class="header-text">
            <h1 class="header-title">契約単価管理</h1>
            <div class="header-subtitle">Contract Pricing Management</div>
          </div>
          <div class="stat-badges">
            <div class="stat-badge"><span class="stat-num">{{ dataList.length }}</span><span class="stat-lbl">件</span></div>
            <div class="stat-badge active"><span class="stat-num">{{ activeCount }}</span><span class="stat-lbl">有効</span></div>
          </div>
        </div>
        <el-button type="primary" size="small" class="create-btn" @click="showForm = true; editId = null">+ 新規登録</el-button>
      </div>
    </div>

    <div class="content-area">
      <div class="filter-section glass-card animate-in" style="animation-delay:0.1s">
        <div class="filter-row">
          <el-input v-model="filters.keyword" placeholder="顧客コード・品番で検索" clearable size="small" class="filter-input" @input="fetchData">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-select v-model="filters.status" placeholder="ステータス" clearable size="small" class="filter-sel" @change="fetchData">
            <el-option label="有効" value="active" />
            <el-option label="期限切れ" value="expired" />
            <el-option label="キャンセル" value="cancelled" />
          </el-select>
        </div>
      </div>

      <div class="table-section glass-card animate-in" style="animation-delay:0.15s">
        <el-table :data="dataList" v-loading="loading" size="small" class="dark-table" :header-cell-style="headerStyle" :cell-style="cellStyle">
          <el-table-column prop="customer_code" label="顧客コード" width="110">
            <template #default="{row}"><span class="code-text">{{ row.customer_code }}</span></template>
          </el-table-column>
          <el-table-column prop="customer_name" label="顧客名" min-width="130" show-overflow-tooltip />
          <el-table-column prop="product_code" label="品番" width="110">
            <template #default="{row}"><span class="code-text">{{ row.product_code }}</span></template>
          </el-table-column>
          <el-table-column prop="product_name" label="品名" min-width="130" show-overflow-tooltip />
          <el-table-column prop="contract_price" label="契約単価" width="110" align="right">
            <template #default="{row}"><span class="price-text">¥{{ (row.contract_price||0).toLocaleString() }}</span></template>
          </el-table-column>
          <el-table-column prop="standard_price" label="標準単価" width="110" align="right">
            <template #default="{row}"><span class="std-price">¥{{ (row.standard_price||0).toLocaleString() }}</span></template>
          </el-table-column>
          <el-table-column prop="discount_rate" label="割引率" width="90" align="center">
            <template #default="{row}">
              <span :class="['discount', { active: row.discount_rate > 0 }]">{{ row.discount_rate || 0 }}%</span>
            </template>
          </el-table-column>
          <el-table-column label="有効期間" width="180" align="center">
            <template #default="{row}">
              <span class="date-range">{{ row.valid_from }} 〜 {{ row.valid_until }}</span>
              <el-tag v-if="isExpiringSoon(row)" type="warning" size="small" class="expiry-tag">期限間近</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="ステータス" width="100" align="center">
            <template #default="{row}">
              <el-tag :type="row.status==='active'?'success':row.status==='expired'?'info':'danger'" size="small" effect="dark">
                {{ row.status==='active'?'有効':row.status==='expired'?'期限切れ':'キャンセル' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="アクション" width="120" align="center" fixed="right">
            <template #default="{row}">
              <el-button size="small" type="primary" plain @click="openEdit(row)">編集</el-button>
              <el-button size="small" type="danger" plain @click="handleDelete(row)">削除</el-button>
            </template>
          </el-table-column>
          <template #empty>
            <div class="empty-state"><el-icon size="40"><Document /></el-icon><p>契約単価データがありません</p></div>
          </template>
        </el-table>
        <div class="pagination-wrap" v-if="total > pageSize">
          <el-pagination :current-page="page" :page-size="pageSize" :total="total" layout="prev, pager, next" size="small" @current-change="p=>{page=p;fetchData()}" />
        </div>
      </div>
    </div>

    <el-dialog v-model="showForm" :title="editId ? '契約単価編集' : '契約単価登録'" width="500px" :close-on-click-modal="false">
      <el-form :model="form" label-width="100px" size="small">
        <el-form-item label="顧客コード"><el-input v-model="form.customer_code" /></el-form-item>
        <el-form-item label="顧客名"><el-input v-model="form.customer_name" /></el-form-item>
        <el-form-item label="品番"><el-input v-model="form.product_code" /></el-form-item>
        <el-form-item label="品名"><el-input v-model="form.product_name" /></el-form-item>
        <el-form-item label="契約単価"><el-input-number v-model="form.contract_price" :min="0" style="width:100%" /></el-form-item>
        <el-form-item label="標準単価"><el-input-number v-model="form.standard_price" :min="0" style="width:100%" /></el-form-item>
        <el-form-item label="割引率(%)"><el-input-number v-model="form.discount_rate" :min="0" :max="100" style="width:100%" /></el-form-item>
        <el-form-item label="有効開始日"><el-date-picker v-model="form.valid_from" type="date" format="YYYY/MM/DD" value-format="YYYY-MM-DD" style="width:100%" /></el-form-item>
        <el-form-item label="有効終了日"><el-date-picker v-model="form.valid_until" type="date" format="YYYY/MM/DD" value-format="YYYY-MM-DD" style="width:100%" /></el-form-item>
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
import { PriceTag, Search, Document } from '@element-plus/icons-vue'
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
const filters = ref({ keyword: '', status: '' })
const form = ref({ customer_code: '', customer_name: '', product_code: '', product_name: '', contract_price: 0, standard_price: 0, discount_rate: 0, valid_from: '', valid_until: '', remarks: '' })

const activeCount = computed(() => dataList.value.filter(i => i.status === 'active').length)
const headerStyle = { background: 'linear-gradient(135deg, #10b981, #059669)', color: '#fff', fontWeight: '600', fontSize: '12px', padding: '6px 10px' }
const cellStyle = { padding: '5px 8px', fontSize: '12px', background: 'rgba(255,255,255,0.03)', color: 'rgba(255,255,255,0.85)', borderColor: 'rgba(255,255,255,0.06)' }

function isExpiringSoon(row: any) {
  if (!row.valid_until || row.status !== 'active') return false
  const diff = new Date(row.valid_until).getTime() - Date.now()
  return diff > 0 && diff < 30 * 24 * 3600 * 1000
}

async function fetchData() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize.value }
    if (filters.value.status) params.status = filters.value.status
    if (filters.value.keyword) { params.customer_code = filters.value.keyword; params.product_code = filters.value.keyword }
    const res: any = await request.get('/api/erp/sales/contract-pricing', { params })
    const data = res?.data ?? res
    dataList.value = data?.items || []
    total.value = data?.total || 0
  } catch { dataList.value = [] }
  finally { loading.value = false }
}

function openEdit(row: any) {
  editId.value = row.id
  form.value = { ...row }
  showForm.value = true
}

async function handleSave() {
  saving.value = true
  try {
    if (editId.value) {
      await request.put(`/api/erp/sales/contract-pricing/${editId.value}`, form.value)
    } else {
      await request.post('/api/erp/sales/contract-pricing', form.value)
    }
    ElMessage.success('保存しました')
    showForm.value = false
    fetchData()
  } catch (e: any) { ElMessage.error(e?.response?.data?.detail || '保存に失敗しました') }
  finally { saving.value = false }
}

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm('この契約単価を削除しますか？', '確認', { type: 'danger' })
    await request.delete(`/api/erp/sales/contract-pricing/${row.id}`)
    ElMessage.success('削除しました')
    fetchData()
  } catch {}
}

onMounted(fetchData)
</script>

<style scoped>
.contract-page { position: relative; min-height: 100vh; padding: 16px; overflow: hidden; }
.dynamic-background { position: fixed; inset: 0; z-index: 0; background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%); }
.gradient-orb { position: absolute; border-radius: 50%; filter: blur(80px); opacity: 0.4; animation: float 20s ease-in-out infinite; }
.orb-1 { width: 350px; height: 350px; top: -80px; left: -80px; background: radial-gradient(circle, #10b981, transparent); }
.orb-2 { width: 300px; height: 300px; bottom: -50px; right: -50px; background: radial-gradient(circle, #059669, transparent); animation-delay: -10s; }
.noise-overlay { position: absolute; inset: 0; opacity: 0.03; }
@keyframes float { 0%,100%{transform:translate(0,0) scale(1)} 50%{transform:translate(20px,-20px) scale(1.03)} }

.glass-header { position: relative; z-index: 1; background: rgba(255,255,255,0.08); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.12); border-radius: 16px; padding: 14px 20px; margin-bottom: 14px; }
.header-content { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; }
.header-left { display: flex; align-items: center; gap: 12px; }
.header-icon { width: 44px; height: 44px; background: linear-gradient(135deg, #10b981, #059669); border-radius: 12px; display: flex; align-items: center; justify-content: center; color: #fff; }
.header-title { font-size: 1.4rem; font-weight: 700; color: #fff; margin: 0; }
.header-subtitle { font-size: 0.75rem; color: rgba(255,255,255,0.5); margin-top: 2px; }
.stat-badges { display: flex; gap: 8px; margin-left: 12px; }
.stat-badge { background: rgba(255,255,255,0.1); border-radius: 12px; padding: 3px 10px; display: flex; align-items: center; gap: 4px; }
.stat-badge.active { background: rgba(16,185,129,0.2); }
.stat-num { font-size: 0.9rem; font-weight: 700; color: #fff; }
.stat-lbl { font-size: 0.65rem; color: rgba(255,255,255,0.7); }
.create-btn { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: #fff; }

.content-area { position: relative; z-index: 1; display: flex; flex-direction: column; gap: 12px; }
.glass-card { background: rgba(255,255,255,0.06); backdrop-filter: blur(16px); border: 1px solid rgba(255,255,255,0.1); border-radius: 14px; padding: 14px 16px; }
.filter-row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.filter-input { flex: 1; min-width: 180px; }
.filter-sel { width: 130px; }

.code-text { font-family: 'Consolas', monospace; font-weight: 600; color: #34d399; font-size: 0.8rem; }
.price-text { font-weight: 700; color: #10b981; }
.std-price { color: rgba(255,255,255,0.5); font-size: 0.8rem; }
.discount { color: rgba(255,255,255,0.4); }
.discount.active { color: #10b981; font-weight: 600; }
.date-range { font-size: 0.75rem; color: rgba(255,255,255,0.7); }
.expiry-tag { margin-left: 4px; }
.pagination-wrap { display: flex; justify-content: center; padding-top: 12px; }
.empty-state { padding: 30px; text-align: center; color: rgba(255,255,255,0.4); }
.empty-state p { margin-top: 8px; font-size: 0.85rem; }

:deep(.el-table) { background: transparent; --el-table-bg-color: transparent; --el-table-tr-bg-color: transparent; --el-table-border-color: rgba(255,255,255,0.06); --el-table-header-bg-color: transparent; --el-table-row-hover-bg-color: rgba(255,255,255,0.05); }
:deep(.el-table th), :deep(.el-table td) { border-color: rgba(255,255,255,0.06); }
:deep(.el-table__empty-text) { color: rgba(255,255,255,0.4); }

.animate-in { animation: slideIn 0.5s ease forwards; opacity: 0; transform: translateY(12px); }
@keyframes slideIn { to { opacity: 1; transform: translateY(0); } }
@media (max-width: 768px) { .contract-page { padding: 10px; } .filter-row { flex-direction: column; } .filter-input,.filter-sel { width: 100%; } }
</style>
