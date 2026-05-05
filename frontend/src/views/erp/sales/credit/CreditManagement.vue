<template>
  <div class="credit-management">
    <div class="dynamic-background">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
      <div class="noise-overlay"></div>
    </div>

    <div class="glass-header animate-in">
      <div class="header-content">
        <div class="header-left">
          <div class="header-icon">
            <el-icon size="28"><CreditCard /></el-icon>
          </div>
          <div class="header-text">
            <h1 class="header-title">与信管理</h1>
            <div class="header-subtitle">Credit Management</div>
          </div>
        </div>
        <div class="header-badges">
          <div class="badge">
            <span class="badge-value">{{ tableData.length }}</span>
            <span class="badge-label">顧客数</span>
          </div>
          <div class="badge danger">
            <span class="badge-value">{{ blockedCount }}</span>
            <span class="badge-label">ブロック</span>
          </div>
        </div>
      </div>
    </div>

    <div class="glass-card filter-section animate-in" style="animation-delay:0.08s">
      <el-form :inline="true" class="filter-form" @submit.prevent="fetchData">
        <el-form-item>
          <el-input
            v-model="query.customer_code"
            placeholder="顧客コード / 顧客名"
            clearable
            prefix-icon="Search"
            class="glass-input"
            @keyup.enter="fetchData"
          />
        </el-form-item>
        <el-form-item>
          <el-select v-model="query.risk_level" placeholder="リスクレベル" clearable class="glass-select">
            <el-option label="低リスク" value="low" />
            <el-option label="中リスク" value="medium" />
            <el-option label="高リスク" value="high" />
            <el-option label="ブロック" value="blocked" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-select v-model="query.status" placeholder="ステータス" clearable class="glass-select">
            <el-option label="有効" value="active" />
            <el-option label="停止" value="suspended" />
            <el-option label="ブロック" value="blocked" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchData" class="gradient-btn">
            <el-icon><Search /></el-icon>検索
          </el-button>
          <el-button @click="openDialog()" class="glass-btn">
            <el-icon><Plus /></el-icon>新規登録
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="glass-card table-section animate-in" style="animation-delay:0.14s">
      <el-table
        v-loading="loading"
        :data="tableData"
        stripe
        size="small"
        class="dark-table"
        :header-cell-style="headerStyle"
        :cell-style="cellStyle"
        empty-text="データがありません"
      >
        <el-table-column prop="customer_code" label="顧客コード" width="120" fixed />
        <el-table-column prop="customer_name" label="顧客名" min-width="160" show-overflow-tooltip />
        <el-table-column label="与信限度額" width="140" align="right">
          <template #default="{ row }">
            <span class="mono">¥{{ formatNum(row.credit_limit) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="残高" width="130" align="right">
          <template #default="{ row }">
            <span class="mono">¥{{ formatNum(row.balance) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="利用可能額" width="200">
          <template #default="{ row }">
            <div class="credit-bar-wrap">
              <el-progress
                :percentage="usagePercent(row)"
                :stroke-width="14"
                :color="usageColor(row)"
                :show-text="false"
              />
              <span class="credit-bar-text">
                ¥{{ formatNum(availableCredit(row)) }}
                <span class="credit-bar-pct">({{ usagePercent(row) }}%使用)</span>
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="リスクレベル" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="riskTagType(row.risk_level)" size="small" effect="dark" round>
              {{ riskLabel(row.risk_level) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="ステータス" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small" effect="plain" round>
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="アクション" width="160" align="center" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openDialog(row)">
              <el-icon><Edit /></el-icon>編集
            </el-button>
            <el-button link type="warning" size="small" @click="handleCreditCheck(row)">
              <el-icon><View /></el-icon>与信チェック
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '与信情報編集' : '与信情報登録'"
      width="520px"
      class="glass-dialog"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px" label-position="top">
        <div class="dialog-grid">
          <el-form-item label="顧客コード" prop="customer_code">
            <el-input v-model="form.customer_code" :disabled="isEdit" placeholder="例: C001" />
          </el-form-item>
          <el-form-item label="顧客名" prop="customer_name">
            <el-input v-model="form.customer_name" placeholder="例: 山田製作所" />
          </el-form-item>
          <el-form-item label="与信限度額" prop="credit_limit">
            <el-input-number v-model="form.credit_limit" :min="0" :step="100000" :controls="false" style="width:100%" />
          </el-form-item>
          <el-form-item label="リスクレベル" prop="risk_level">
            <el-select v-model="form.risk_level" style="width:100%">
              <el-option label="低リスク" value="low" />
              <el-option label="中リスク" value="medium" />
              <el-option label="高リスク" value="high" />
              <el-option label="ブロック" value="blocked" />
            </el-select>
          </el-form-item>
        </div>
        <el-form-item label="備考">
          <el-input v-model="form.remarks" type="textarea" :rows="2" placeholder="備考欄" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false" class="glass-btn">キャンセル</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving" class="gradient-btn">保存</el-button>
      </template>
    </el-dialog>

    <el-popover
      :visible="checkPopover.visible"
      :virtual-ref="checkPopover.ref"
      virtual-triggering
      placement="left"
      :width="260"
      popper-class="credit-check-popover"
    >
      <div class="credit-check-result" v-if="checkPopover.data">
        <div class="check-title">与信チェック結果</div>
        <div class="check-row">
          <span>与信限度額</span>
          <strong>¥{{ formatNum(checkPopover.data.credit_limit) }}</strong>
        </div>
        <div class="check-row">
          <span>現在残高</span>
          <strong>¥{{ formatNum(checkPopover.data.balance) }}</strong>
        </div>
        <div class="check-row highlight">
          <span>利用可能額</span>
          <strong class="available">¥{{ formatNum(checkPopover.data.available) }}</strong>
        </div>
        <el-button size="small" @click="checkPopover.visible = false" style="margin-top:8px;width:100%">閉じる</el-button>
      </div>
    </el-popover>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { CreditCard, Search, Plus, Edit, View } from '@element-plus/icons-vue'
import { getCredits, createOrUpdateCredit, checkCredit } from '@/api/erp/sales'

const loading = ref(false)
const saving = ref(false)
const tableData = ref<any[]>([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref<FormInstance>()

const query = reactive({ customer_code: '', risk_level: '', status: '' })

const form = reactive({
  id: null as number | null,
  customer_code: '',
  customer_name: '',
  credit_limit: 0,
  risk_level: 'low',
  remarks: '',
})

const rules: FormRules = {
  customer_code: [{ required: true, message: '顧客コードは必須です', trigger: 'blur' }],
  customer_name: [{ required: true, message: '顧客名は必須です', trigger: 'blur' }],
  credit_limit: [{ required: true, message: '与信限度額は必須です', trigger: 'blur' }],
  risk_level: [{ required: true, message: 'リスクレベルは必須です', trigger: 'change' }],
}

const checkPopover = reactive({
  visible: false,
  ref: null as any,
  data: null as { credit_limit: number; balance: number; available: number } | null,
})

const blockedCount = computed(() => tableData.value.filter(r => r.risk_level === 'blocked' || r.status === 'blocked').length)

const headerStyle = () => ({
  background: 'rgba(255,255,255,0.04)',
  color: 'rgba(255,255,255,0.7)',
  borderColor: 'rgba(255,255,255,0.08)',
  fontSize: '12px',
  fontWeight: '600',
})

const cellStyle = () => ({
  background: 'transparent',
  color: 'rgba(255,255,255,0.85)',
  borderColor: 'rgba(255,255,255,0.06)',
})

function formatNum(v: number | null | undefined): string {
  return (v ?? 0).toLocaleString('ja-JP')
}

function availableCredit(row: any): number {
  return Math.max(0, (row.credit_limit ?? 0) - (row.balance ?? 0))
}

function usagePercent(row: any): number {
  if (!row.credit_limit) return 0
  return Math.min(100, Math.round(((row.balance ?? 0) / row.credit_limit) * 100))
}

function usageColor(row: any): string {
  const pct = usagePercent(row)
  if (pct >= 90) return '#ef4444'
  if (pct >= 70) return '#f59e0b'
  return '#10b981'
}

function riskTagType(level: string) {
  const map: Record<string, string> = { low: 'success', medium: 'warning', high: 'danger', blocked: 'info' }
  return map[level] || 'info'
}

function riskLabel(level: string) {
  const map: Record<string, string> = { low: '低', medium: '中', high: '高', blocked: 'ブロック' }
  return map[level] || level
}

function statusTagType(status: string) {
  const map: Record<string, string> = { active: 'success', suspended: 'warning', blocked: 'danger' }
  return map[status] || 'info'
}

function statusLabel(status: string) {
  const map: Record<string, string> = { active: '有効', suspended: '停止', blocked: 'ブロック' }
  return map[status] || status
}

function openDialog(row?: any) {
  isEdit.value = !!row
  if (row) {
    Object.assign(form, { id: row.id, customer_code: row.customer_code, customer_name: row.customer_name, credit_limit: row.credit_limit, risk_level: row.risk_level, remarks: row.remarks || '' })
  } else {
    Object.assign(form, { id: null, customer_code: '', customer_name: '', credit_limit: 0, risk_level: 'low', remarks: '' })
  }
  dialogVisible.value = true
}

async function handleSave() {
  if (!formRef.value) return
  await formRef.value.validate()
  saving.value = true
  try {
    await createOrUpdateCredit({ ...form })
    ElMessage.success(isEdit.value ? '更新しました' : '登録しました')
    dialogVisible.value = false
    await fetchData()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存に失敗しました')
  } finally {
    saving.value = false
  }
}

async function handleCreditCheck(row: any) {
  try {
    const res: any = await checkCredit(row.customer_code)
    const data = res?.data ?? res
    checkPopover.data = {
      credit_limit: data?.credit_limit ?? row.credit_limit ?? 0,
      balance: data?.balance ?? row.balance ?? 0,
      available: data?.available ?? availableCredit(row),
    }
    checkPopover.visible = true
    setTimeout(() => { checkPopover.visible = false }, 6000)
  } catch {
    ElMessage.info(`利用可能額: ¥${formatNum(availableCredit(row))}`)
  }
}

async function fetchData() {
  loading.value = true
  try {
    const params: any = {}
    if (query.customer_code) params.customer_code = query.customer_code
    if (query.risk_level) params.risk_level = query.risk_level
    if (query.status) params.status = query.status
    const res: any = await getCredits(params)
    tableData.value = res?.data?.items ?? res?.data ?? res?.items ?? (Array.isArray(res) ? res : [])
  } catch {
    tableData.value = []
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>

<style scoped>
.credit-management {
  position: relative;
  min-height: 100vh;
  padding: 16px;
  overflow: hidden;
}

.dynamic-background {
  position: fixed;
  inset: 0;
  z-index: 0;
  background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
}
.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.35;
  animation: float 20s ease-in-out infinite;
}
.orb-1 { width: 400px; height: 400px; top: -100px; left: -100px; background: radial-gradient(circle, #f59e0b, transparent); }
.orb-2 { width: 350px; height: 350px; top: 40%; right: -80px; background: radial-gradient(circle, #8b5cf6, transparent); animation-delay: -7s; }
.orb-3 { width: 300px; height: 300px; bottom: -50px; left: 30%; background: radial-gradient(circle, #06b6d4, transparent); animation-delay: -14s; }
.noise-overlay {
  position: absolute;
  inset: 0;
  background: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E");
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -30px) scale(1.05); }
  66% { transform: translate(-20px, 20px) scale(0.95); }
}

.glass-header {
  position: relative;
  z-index: 1;
  background: rgba(255,255,255,0.08);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 16px;
  padding: 16px 24px;
  margin-bottom: 12px;
}
.header-content { display: flex; align-items: center; justify-content: space-between; }
.header-left { display: flex; align-items: center; gap: 14px; }
.header-icon {
  width: 48px; height: 48px;
  background: linear-gradient(135deg, #f59e0b, #d97706);
  border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  color: #fff;
  box-shadow: 0 4px 20px rgba(245,158,11,0.4);
}
.header-title { font-size: 1.5rem; font-weight: 700; color: #fff; margin: 0; }
.header-subtitle { font-size: 0.8rem; color: rgba(255,255,255,0.55); margin-top: 2px; }
.header-badges { display: flex; gap: 12px; }
.badge {
  display: flex; flex-direction: column; align-items: center;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 10px;
  padding: 6px 16px;
  min-width: 72px;
}
.badge.danger { border-color: rgba(239,68,68,0.3); background: rgba(239,68,68,0.1); }
.badge-value { font-size: 1.2rem; font-weight: 700; color: #fff; }
.badge-label { font-size: 0.68rem; color: rgba(255,255,255,0.5); }

.glass-card {
  position: relative;
  z-index: 1;
  background: rgba(255,255,255,0.06);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 14px;
  padding: 16px;
  margin-bottom: 12px;
}

.filter-section { padding: 12px 16px; }
.filter-form :deep(.el-form-item) { margin-bottom: 0; margin-right: 10px; }
.filter-form :deep(.el-input__wrapper),
.filter-form :deep(.el-select .el-input__wrapper) {
  background: rgba(255,255,255,0.06) !important;
  border-color: rgba(255,255,255,0.12) !important;
  box-shadow: none !important;
  color: #fff;
}
.filter-form :deep(.el-input__inner) { color: #fff !important; }
.filter-form :deep(.el-input__inner::placeholder) { color: rgba(255,255,255,0.35) !important; }
.filter-form :deep(.el-select__placeholder) { color: rgba(255,255,255,0.35) !important; }
.filter-form :deep(.el-select__caret) { color: rgba(255,255,255,0.4) !important; }

.gradient-btn {
  background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
  border: none !important;
  color: #fff !important;
  font-weight: 600;
}
.gradient-btn:hover { opacity: 0.9; transform: translateY(-1px); }
.glass-btn {
  background: rgba(255,255,255,0.08) !important;
  border: 1px solid rgba(255,255,255,0.15) !important;
  color: #fff !important;
}
.glass-btn:hover { background: rgba(255,255,255,0.14) !important; }

.table-section { padding: 0; overflow: hidden; }
.dark-table {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-row-hover-bg-color: rgba(255,255,255,0.04);
  --el-table-header-bg-color: rgba(255,255,255,0.04);
  --el-table-border-color: rgba(255,255,255,0.06);
  --el-table-text-color: rgba(255,255,255,0.85);
  --el-fill-color-lighter: rgba(255,255,255,0.02);
  width: 100%;
}
.dark-table :deep(.el-table__empty-text) { color: rgba(255,255,255,0.4); }
.dark-table :deep(th.el-table__cell) { font-size: 12px; font-weight: 600; }
.dark-table :deep(.el-table__fixed-right::before),
.dark-table :deep(.el-table__fixed::before) { background-color: rgba(255,255,255,0.06); }

.mono { font-family: 'SF Mono', 'Cascadia Code', monospace; font-size: 13px; }

.credit-bar-wrap { display: flex; flex-direction: column; gap: 3px; }
.credit-bar-wrap :deep(.el-progress-bar__outer) { background: rgba(255,255,255,0.08) !important; border-radius: 6px; }
.credit-bar-wrap :deep(.el-progress-bar__inner) { border-radius: 6px; }
.credit-bar-text { font-size: 11px; color: rgba(255,255,255,0.6); }
.credit-bar-pct { font-size: 10px; color: rgba(255,255,255,0.35); margin-left: 4px; }

.dialog-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 16px; }

.animate-in {
  animation: slideIn 0.5s ease forwards;
  opacity: 0;
  transform: translateY(12px);
}
@keyframes slideIn {
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 768px) {
  .credit-management { padding: 10px; }
  .header-content { flex-direction: column; gap: 10px; align-items: flex-start; }
  .dialog-grid { grid-template-columns: 1fr; }
}
</style>

<style>
.glass-dialog .el-dialog {
  background: rgba(15,23,42,0.95) !important;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 16px;
}
.glass-dialog .el-dialog__header { border-bottom: 1px solid rgba(255,255,255,0.08); padding: 16px 20px; }
.glass-dialog .el-dialog__title { color: #fff !important; font-weight: 600; }
.glass-dialog .el-dialog__body { padding: 20px; }
.glass-dialog .el-dialog__footer { border-top: 1px solid rgba(255,255,255,0.08); padding: 12px 20px; }
.glass-dialog .el-form-item__label { color: rgba(255,255,255,0.7) !important; font-size: 12px !important; }
.glass-dialog .el-input__wrapper,
.glass-dialog .el-textarea__inner,
.glass-dialog .el-select .el-input__wrapper {
  background: rgba(255,255,255,0.06) !important;
  border-color: rgba(255,255,255,0.12) !important;
  box-shadow: none !important;
}
.glass-dialog .el-input__inner,
.glass-dialog .el-textarea__inner { color: #fff !important; }
.glass-dialog .el-input-number { width: 100%; }
.glass-dialog .el-dialog__headerbtn .el-dialog__close { color: rgba(255,255,255,0.5); }

.credit-check-popover.el-popover {
  background: rgba(15,23,42,0.95) !important;
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255,255,255,0.15) !important;
  border-radius: 12px;
}
.credit-check-result { color: #fff; }
.check-title { font-size: 13px; font-weight: 700; margin-bottom: 10px; color: #f59e0b; }
.check-row { display: flex; justify-content: space-between; font-size: 12px; padding: 4px 0; color: rgba(255,255,255,0.7); }
.check-row.highlight { border-top: 1px solid rgba(255,255,255,0.1); padding-top: 8px; margin-top: 4px; }
.check-row .available { color: #10b981; font-size: 14px; }
</style>
