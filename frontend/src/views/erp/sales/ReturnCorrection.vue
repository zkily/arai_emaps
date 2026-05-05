<template>
  <div class="return-correction-page">
    <div class="dynamic-background">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="noise-overlay"></div>
    </div>

    <div class="glass-header animate-in">
      <div class="header-content">
        <div class="header-left">
          <div class="header-icon">
            <el-icon size="26"><RefreshLeft /></el-icon>
          </div>
          <div class="header-text">
            <h1 class="header-title">赤黒訂正処理</h1>
            <div class="header-subtitle">Credit/Debit Note Correction</div>
          </div>
        </div>
        <el-button type="primary" size="small" class="create-btn" @click="showCreateDialog = true">
          + 新規訂正
        </el-button>
      </div>
    </div>

    <div class="content-area">
      <div class="filter-section glass-card animate-in" style="animation-delay: 0.1s">
        <div class="filter-row">
          <el-input v-model="filters.keyword" placeholder="伝票番号・顧客名で検索" clearable size="small" class="filter-input" @input="handleSearch">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-select v-model="filters.type" placeholder="訂正種別" clearable size="small" class="filter-sel" @change="handleSearch">
            <el-option label="赤伝票（マイナス）" value="credit" />
            <el-option label="黒伝票（プラス）" value="debit" />
          </el-select>
          <el-select v-model="filters.status" placeholder="ステータス" clearable size="small" class="filter-sel" @change="handleSearch">
            <el-option label="下書き" value="draft" />
            <el-option label="承認済" value="approved" />
            <el-option label="計上済" value="posted" />
          </el-select>
          <el-date-picker v-model="filters.dateRange" type="daterange" size="small" range-separator="〜" start-placeholder="開始日" end-placeholder="終了日" format="YYYY/MM/DD" value-format="YYYY-MM-DD" class="filter-date" @change="handleSearch" />
        </div>
      </div>

      <div class="table-section glass-card animate-in" style="animation-delay: 0.15s">
        <el-table :data="corrections" v-loading="loading" size="small" class="dark-table" :header-cell-style="tableHeaderStyle" :cell-style="tableCellStyle">
          <el-table-column prop="correction_no" label="訂正番号" width="140">
            <template #default="{ row }">
              <span class="code-text">{{ row.correction_no }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="original_no" label="元伝票番号" width="140" show-overflow-tooltip />
          <el-table-column prop="customer_name" label="顧客名" min-width="140" show-overflow-tooltip />
          <el-table-column prop="correction_date" label="訂正日" width="110" align="center" />
          <el-table-column prop="type" label="種別" width="120" align="center">
            <template #default="{ row }">
              <el-tag :type="row.type === 'credit' ? 'danger' : 'success'" size="small" effect="dark">
                {{ row.type === 'credit' ? '赤伝票' : '黒伝票' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="amount" label="金額" width="120" align="right">
            <template #default="{ row }">
              <span :class="row.type === 'credit' ? 'amount-negative' : 'amount-positive'">
                {{ row.type === 'credit' ? '-' : '+' }}¥{{ Math.abs(row.amount || 0).toLocaleString() }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="reason" label="理由" min-width="160" show-overflow-tooltip />
          <el-table-column prop="status" label="ステータス" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.status === 'draft' ? 'info' : row.status === 'approved' ? 'warning' : 'success'" size="small">
                {{ row.status === 'draft' ? '下書き' : row.status === 'approved' ? '承認済' : '計上済' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="アクション" width="140" align="center" fixed="right">
            <template #default="{ row }">
              <el-button v-if="row.status === 'draft'" size="small" type="warning" plain @click="approveCorrection(row)">承認</el-button>
              <el-button v-if="row.status === 'approved'" size="small" type="success" plain @click="postCorrection(row)">計上</el-button>
              <el-button v-if="row.status === 'draft'" size="small" type="danger" plain @click="deleteCorrection(row)">削除</el-button>
            </template>
          </el-table-column>
          <template #empty>
            <div class="empty-state">
              <el-icon size="40"><Document /></el-icon>
              <p>訂正データがありません</p>
            </div>
          </template>
        </el-table>
      </div>
    </div>

    <el-dialog v-model="showCreateDialog" title="赤黒訂正作成" width="560px" :close-on-click-modal="false" class="dark-dialog">
      <el-form :model="form" label-width="100px" size="small">
        <el-form-item label="元伝票番号">
          <el-input v-model="form.original_no" placeholder="元の受注番号または請求番号" />
        </el-form-item>
        <el-form-item label="訂正種別">
          <el-radio-group v-model="form.type">
            <el-radio value="credit">赤伝票（マイナス訂正）</el-radio>
            <el-radio value="debit">黒伝票（プラス訂正）</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="顧客コード">
          <el-input v-model="form.customer_code" placeholder="顧客コード" />
        </el-form-item>
        <el-form-item label="顧客名">
          <el-input v-model="form.customer_name" placeholder="顧客名" />
        </el-form-item>
        <el-form-item label="訂正日">
          <el-date-picker v-model="form.correction_date" type="date" format="YYYY/MM/DD" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="金額">
          <el-input-number v-model="form.amount" :min="0" :precision="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="理由">
          <el-input v-model="form.reason" type="textarea" :rows="3" placeholder="訂正理由を入力" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">キャンセル</el-button>
        <el-button type="primary" @click="createCorrection">作成</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Search, RefreshLeft, Document } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const showCreateDialog = ref(false)
const filters = ref({ keyword: '', type: '', status: '', dateRange: null as any })

interface Correction {
  id: number
  correction_no: string
  original_no: string
  customer_code: string
  customer_name: string
  correction_date: string
  type: 'credit' | 'debit'
  amount: number
  reason: string
  status: 'draft' | 'approved' | 'posted'
}

const corrections = ref<Correction[]>([])
const form = ref({ original_no: '', type: 'credit' as 'credit' | 'debit', customer_code: '', customer_name: '', correction_date: '', amount: 0, reason: '' })

const tableHeaderStyle = { background: 'linear-gradient(135deg, #f97316, #ea580c)', color: '#fff', fontWeight: '600', fontSize: '12px', padding: '6px 10px' }
const tableCellStyle = { padding: '5px 8px', fontSize: '12px', background: 'rgba(255,255,255,0.03)', color: 'rgba(255,255,255,0.85)', borderColor: 'rgba(255,255,255,0.06)' }

function handleSearch() {}

function createCorrection() {
  ElMessage.info('赤黒訂正機能は準備中です')
  showCreateDialog.value = false
}

function approveCorrection(_row: Correction) {
  ElMessageBox.confirm('この訂正を承認しますか？', '確認', { type: 'warning' }).then(() => {
    ElMessage.info('承認機能は準備中です')
  }).catch(() => {})
}

function postCorrection(_row: Correction) {
  ElMessageBox.confirm('この訂正を計上しますか？', '確認', { type: 'warning' }).then(() => {
    ElMessage.info('計上機能は準備中です')
  }).catch(() => {})
}

function deleteCorrection(_row: Correction) {
  ElMessageBox.confirm('この訂正を削除しますか？', '確認', { type: 'danger' }).then(() => {
    ElMessage.info('削除機能は準備中です')
  }).catch(() => {})
}
</script>

<style scoped>
.return-correction-page { position: relative; min-height: 100vh; padding: 16px; overflow: hidden; }
.dynamic-background { position: fixed; inset: 0; z-index: 0; background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%); }
.gradient-orb { position: absolute; border-radius: 50%; filter: blur(80px); opacity: 0.4; animation: float 20s ease-in-out infinite; }
.orb-1 { width: 350px; height: 350px; top: -80px; right: -80px; background: radial-gradient(circle, #f97316, transparent); }
.orb-2 { width: 300px; height: 300px; bottom: -50px; left: -50px; background: radial-gradient(circle, #ef4444, transparent); animation-delay: -10s; }
.noise-overlay { position: absolute; inset: 0; opacity: 0.03; }
@keyframes float { 0%,100%{transform:translate(0,0) scale(1)} 50%{transform:translate(20px,-20px) scale(1.03)} }

.glass-header { position: relative; z-index: 1; background: rgba(255,255,255,0.08); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.12); border-radius: 16px; padding: 14px 20px; margin-bottom: 14px; }
.header-content { display: flex; align-items: center; justify-content: space-between; }
.header-left { display: flex; align-items: center; gap: 12px; }
.header-icon { width: 44px; height: 44px; background: linear-gradient(135deg, #f97316, #ea580c); border-radius: 12px; display: flex; align-items: center; justify-content: center; color: #fff; }
.header-title { font-size: 1.4rem; font-weight: 700; color: #fff; margin: 0; }
.header-subtitle { font-size: 0.75rem; color: rgba(255,255,255,0.5); margin-top: 2px; }
.create-btn { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: #fff; }
.create-btn:hover { background: rgba(255,255,255,0.15); }

.content-area { position: relative; z-index: 1; display: flex; flex-direction: column; gap: 12px; }
.glass-card { background: rgba(255,255,255,0.06); backdrop-filter: blur(16px); border: 1px solid rgba(255,255,255,0.1); border-radius: 14px; padding: 14px 16px; }

.filter-row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.filter-input { flex: 1; min-width: 180px; }
.filter-sel { width: 140px; }
.filter-date { width: 240px; }

.code-text { font-family: 'Consolas', monospace; font-weight: 600; color: #f97316; font-size: 0.8rem; }
.amount-negative { color: #ef4444; font-weight: 600; }
.amount-positive { color: #10b981; font-weight: 600; }

.empty-state { padding: 30px; text-align: center; color: rgba(255,255,255,0.4); }
.empty-state p { margin-top: 8px; font-size: 0.85rem; }

:deep(.el-table) { background: transparent; --el-table-bg-color: transparent; --el-table-tr-bg-color: transparent; --el-table-border-color: rgba(255,255,255,0.06); --el-table-header-bg-color: transparent; --el-table-row-hover-bg-color: rgba(255,255,255,0.05); }
:deep(.el-table th), :deep(.el-table td) { border-color: rgba(255,255,255,0.06); }
:deep(.el-table__empty-text) { color: rgba(255,255,255,0.4); }

.animate-in { animation: slideIn 0.5s ease forwards; opacity: 0; transform: translateY(12px); }
@keyframes slideIn { to { opacity: 1; transform: translateY(0); } }

@media (max-width: 768px) { .return-correction-page { padding: 10px; } .filter-row { flex-direction: column; } .filter-input, .filter-sel, .filter-date { width: 100%; } }
</style>
