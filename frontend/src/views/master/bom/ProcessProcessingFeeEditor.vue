<template>
  <div class="ppf-page">
    <header class="ppf-hero">
      <div class="ppf-hero__accent" aria-hidden="true" />
      <div class="ppf-hero__inner">
        <div class="ppf-hero__brand">
          <div class="ppf-hero__icon">
            <el-icon :size="20"><Operation /></el-icon>
          </div>
          <div class="ppf-hero__text">
            <h1 class="ppf-hero__title">工程加工費マスタ</h1>
            <p class="ppf-hero__sub">工程×加工方法の単価を登録 · 明細BOMの加工費プルダウンに使用</p>
          </div>
        </div>
      </div>
    </header>

    <el-card class="ppf-toolbar-card" shadow="never">
      <div class="ppf-toolbar">
        <el-form :inline="true" class="ppf-filter-form" @submit.prevent>
          <el-form-item label="工程">
            <el-select
              v-model="filterProcessCd"
              filterable
              clearable
              placeholder="全工程"
              class="ppf-filt-select"
              size="small"
              :loading="processLoading"
            >
              <el-option
                v-for="p in processOptions"
                :key="p.process_cd"
                :label="`${p.process_cd} — ${p.process_name || ''}`"
                :value="p.process_cd"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="キーワード">
            <el-input
              v-model="filterKeyword"
              placeholder="方法CD/名称"
              clearable
              size="small"
              class="ppf-filt-input"
              @keyup.enter="loadList"
            />
          </el-form-item>
          <el-form-item label="状態">
            <el-select v-model="filterStatus" clearable placeholder="全て" class="ppf-filt-status" size="small">
              <el-option label="有効" value="active" />
              <el-option label="履歴" value="historical" />
            </el-select>
          </el-form-item>
          <el-form-item class="ppf-toolbar__btns">
            <el-button type="primary" size="small" :icon="Search" @click="loadList">検索</el-button>
            <el-button size="small" @click="resetFilter">クリア</el-button>
            <el-button type="primary" size="small" :icon="Plus" plain @click="openCreate">新規</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>

    <el-card class="ppf-data-card" shadow="never">
      <template #header>
        <div class="ppf-data-cap">
          <span class="ppf-data-cap__dot" />
          <span class="ppf-data-cap__title">登録一覧</span>
          <span class="ppf-data-cap__meta">{{ total }} 件</span>
        </div>
      </template>
      <el-table
        v-loading="loading"
        class="ppf-table"
        :data="rows"
        stripe
        style="width: 100%"
        max-height="calc(100vh - 280px)"
      >
        <el-table-column prop="process_cd" label="工程CD" width="120" />
        <el-table-column prop="process_name" label="工程名" min-width="140" show-overflow-tooltip />
        <el-table-column prop="method_cd" label="加工方法CD" width="130" />
        <el-table-column prop="method_name" label="加工方法名" min-width="160" show-overflow-tooltip />
        <el-table-column prop="unit_price" label="加工費単価" width="130" align="right">
          <template #default="{ row }">{{ formatPrice(row.unit_price) }}</template>
        </el-table-column>
        <el-table-column prop="charge_uom" label="課金単位" width="100" align="center" />
        <el-table-column prop="currency" label="通貨" width="80" align="center" />
        <el-table-column prop="effective_from" label="有効開始" width="110" />
        <el-table-column prop="effective_to" label="有効終了" width="110" />
        <el-table-column prop="status" label="状態" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
              {{ row.status === 'active' ? '有効' : '履歴' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="128" fixed="right" align="center">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="openEdit(row)">編集</el-button>
            <el-popconfirm title="削除しますか？" width="200" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button size="small" type="danger" link>削除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      <div class="ppf-pagination">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          small
          layout="total, prev, pager, next"
          @current-change="loadList"
        />
      </div>
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      width="600px"
      destroy-on-close
      align-center
      class="ppf-form-dialog"
      :show-close="true"
      :close-on-click-modal="false"
      append-to-body
    >
      <template #header>
        <div class="ppf-dlg-header">
          <div class="ppf-dlg-header__accent" aria-hidden="true" />
          <div class="ppf-dlg-header__main">
            <div class="ppf-dlg-header__icon" :class="{ 'ppf-dlg-header__icon--edit': isEdit }">
              <el-icon :size="20">
                <component :is="isEdit ? EditPen : CirclePlus" />
              </el-icon>
            </div>
            <div class="ppf-dlg-header__text">
              <h3 class="ppf-dlg-header__title">{{ isEdit ? '工程加工費を編集' : '工程加工費を新規登録' }}</h3>
              <p class="ppf-dlg-header__desc">工程×加工方法で単価を定義（明細BOMに反映）</p>
            </div>
          </div>
        </div>
      </template>

      <div class="ppf-dlg-body">
        <el-form ref="formRef" :model="form" :rules="rules" label-position="top" class="ppf-dlg-form" require-asterisk-position="right">
          <section class="ppf-section">
            <div class="ppf-section__head">
              <span class="ppf-section__badge">01</span>
              <span class="ppf-section__label">基本情報</span>
            </div>
            <el-form-item label="工程" prop="process_cd">
              <el-select
                v-model="form.process_cd"
                filterable
                placeholder="工程を選択"
                class="ppf-input-full"
                :loading="processLoading"
              >
                <el-option
                  v-for="p in processOptions"
                  :key="p.process_cd"
                  :label="`${p.process_cd} — ${p.process_name || ''}`"
                  :value="p.process_cd"
                />
              </el-select>
            </el-form-item>
            <el-row :gutter="12">
              <el-col :xs="24" :sm="12">
                <el-form-item label="加工方法CD" prop="method_cd">
                  <el-input v-model="form.method_cd" placeholder="例: CUT-LASER" clearable />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="加工方法名">
                  <el-input v-model="form.method_name" placeholder="例: レーザー切断" clearable />
                </el-form-item>
              </el-col>
            </el-row>
          </section>

          <section class="ppf-section ppf-section--price">
            <div class="ppf-section__head">
              <span class="ppf-section__badge ppf-section__badge--accent">02</span>
              <span class="ppf-section__label">単価・課金</span>
            </div>
            <el-form-item label="加工費単価" prop="unit_price" class="ppf-form-item--price">
              <div class="ppf-price-field">
                <span class="ppf-price-field__prefix">¥</span>
                <el-input-number
                  v-model="form.unit_price"
                  :min="0"
                  :precision="2"
                  :step="1"
                  class="ppf-price-field__input"
                  controls-position="right"
                />
              </div>
            </el-form-item>
            <el-row :gutter="12">
              <el-col :xs="24" :sm="12">
                <el-form-item label="課金単位">
                  <el-input v-model="form.charge_uom" placeholder="式 / 個 / H" clearable />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="通貨">
                  <el-input v-model="form.currency" placeholder="JPY" maxlength="8" show-word-limit clearable />
                </el-form-item>
              </el-col>
            </el-row>
          </section>

          <section class="ppf-section">
            <div class="ppf-section__head">
              <span class="ppf-section__badge">03</span>
              <span class="ppf-section__label">有効期間・状態</span>
            </div>
            <el-row :gutter="12">
              <el-col :xs="24" :sm="12">
                <el-form-item label="有効開始">
                  <el-date-picker
                    v-model="form.effective_from"
                    type="date"
                    value-format="YYYY-MM-DD"
                    placeholder="未指定可"
                    class="ppf-input-full"
                  />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="有効終了">
                  <el-date-picker
                    v-model="form.effective_to"
                    type="date"
                    value-format="YYYY-MM-DD"
                    placeholder="未指定可"
                    class="ppf-input-full"
                  />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="状態">
              <el-radio-group v-model="form.status" class="ppf-status-rg" size="default">
                <el-radio-button value="active">有効</el-radio-button>
                <el-radio-button value="historical">履歴</el-radio-button>
              </el-radio-group>
            </el-form-item>
          </section>

          <section class="ppf-section ppf-section--remarks">
            <div class="ppf-section__head">
              <span class="ppf-section__badge">04</span>
              <span class="ppf-section__label">備考</span>
            </div>
            <el-form-item label="メモ（任意）" class="ppf-remarks-item">
              <el-input
                v-model="form.remarks"
                type="textarea"
                :rows="2"
                placeholder="補足・契約番号など"
                resize="none"
                maxlength="500"
                show-word-limit
              />
            </el-form-item>
          </section>
        </el-form>
      </div>

      <template #footer>
        <div class="ppf-dlg-footer">
          <el-button size="small" round @click="dialogVisible = false">キャンセル</el-button>
          <el-button type="primary" size="small" round :loading="saving" @click="submitForm">
            <el-icon class="ppf-btn-icon"><Check /></el-icon>
            {{ isEdit ? '更新する' : '登録する' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search, CirclePlus, EditPen, Check, Operation } from '@element-plus/icons-vue'
import {
  getProcessProcessingFees,
  createProcessProcessingFee,
  updateProcessProcessingFee,
  deleteProcessProcessingFee,
  type ProcessProcessingFeeRow,
  type ProcessProcessingFeePayload,
} from '@/api/master/processProcessingFee'
import { getProcessList } from '@/api/master/processMaster'
import type { ProcessItem } from '@/types/master'

const loading = ref(false)
const processLoading = ref(false)
const rows = ref<ProcessProcessingFeeRow[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 30

const filterProcessCd = ref('')
const filterKeyword = ref('')
const filterStatus = ref('active')

const processOptions = ref<ProcessItem[]>([])

const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const formRef = ref<FormInstance>()

/** 新規時の有効期間デフォルト */
const DEFAULT_EFFECTIVE_FROM = '2026-04-01'
const DEFAULT_EFFECTIVE_TO = '2030-03-31'

const form = reactive<ProcessProcessingFeePayload>({
  process_cd: '',
  method_cd: '',
  method_name: '',
  unit_price: 0,
  currency: 'JPY',
  charge_uom: '式',
  effective_from: DEFAULT_EFFECTIVE_FROM,
  effective_to: DEFAULT_EFFECTIVE_TO,
  status: 'active',
  remarks: '',
})

const rules: FormRules = {
  process_cd: [{ required: true, message: '工程を選択してください', trigger: 'change' }],
  method_cd: [{ required: true, message: '加工方法CDを入力してください', trigger: 'blur' }],
  unit_price: [{ required: true, message: '単価を入力してください', trigger: 'change' }],
}

function formatPrice(n: number | undefined) {
  const v = Number(n) || 0
  return `¥${v.toLocaleString('ja-JP', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

async function loadProcesses() {
  processLoading.value = true
  try {
    const res = await getProcessList({ page: 1, pageSize: 5000 })
    const list = res?.data?.list ?? res?.list ?? []
    processOptions.value = list as ProcessItem[]
  } catch {
    processOptions.value = []
  } finally {
    processLoading.value = false
  }
}

async function loadList() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: page.value, limit: pageSize }
    if (filterProcessCd.value) params.process_cd = filterProcessCd.value
    if (filterKeyword.value) params.keyword = filterKeyword.value
    if (filterStatus.value) params.status = filterStatus.value
    const res = await getProcessProcessingFees(params)
    const d = (res as any)?.data ?? res
    rows.value = d?.list ?? []
    total.value = d?.total ?? 0
  } catch {
    ElMessage.error('一覧の取得に失敗しました')
    rows.value = []
  } finally {
    loading.value = false
  }
}

function resetFilter() {
  filterProcessCd.value = ''
  filterKeyword.value = ''
  filterStatus.value = 'active'
  page.value = 1
  loadList()
}

function resetForm() {
  Object.assign(form, {
    process_cd: '',
    method_cd: '',
    method_name: '',
    unit_price: 0,
    currency: 'JPY',
    charge_uom: '式',
    effective_from: DEFAULT_EFFECTIVE_FROM,
    effective_to: DEFAULT_EFFECTIVE_TO,
    status: 'active',
    remarks: '',
  })
}

function openCreate() {
  isEdit.value = false
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: ProcessProcessingFeeRow) {
  isEdit.value = true
  editingId.value = row.id
  Object.assign(form, {
    process_cd: row.process_cd,
    method_cd: row.method_cd,
    method_name: row.method_name ?? '',
    unit_price: row.unit_price,
    currency: row.currency ?? 'JPY',
    charge_uom: row.charge_uom ?? '式',
    effective_from: row.effective_from ?? null,
    effective_to: row.effective_to ?? null,
    status: row.status ?? 'active',
    remarks: row.remarks ?? '',
  })
  dialogVisible.value = true
}

async function submitForm() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  saving.value = true
  try {
    if (isEdit.value && editingId.value != null) {
      await updateProcessProcessingFee(editingId.value, { ...form })
      ElMessage.success('更新しました')
    } else {
      await createProcessProcessingFee({ ...form })
      ElMessage.success('登録しました')
    }
    dialogVisible.value = false
    loadList()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存に失敗しました')
  } finally {
    saving.value = false
  }
}

async function handleDelete(id: number) {
  try {
    await deleteProcessProcessingFee(id)
    ElMessage.success('削除しました')
    loadList()
  } catch {
    ElMessage.error('削除に失敗しました')
  }
}

onMounted(() => {
  loadProcesses()
  loadList()
})
</script>

<style scoped>
.ppf-page {
  min-height: 100vh;
  padding: 10px 12px 12px;
  background:
    radial-gradient(ellipse 90% 60% at 0% -10%, rgba(99, 102, 241, 0.1), transparent 45%),
    linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
}

/* ページヘッダー */
.ppf-hero {
  position: relative;
  border-radius: 12px;
  margin-bottom: 10px;
  overflow: hidden;
  box-shadow: 0 8px 24px -8px rgba(15, 23, 42, 0.2);
}

.ppf-hero__accent {
  height: 3px;
  background: linear-gradient(90deg, #6366f1, #8b5cf6, #0ea5e9);
}

.ppf-hero__inner {
  display: flex;
  align-items: center;
  padding: 10px 14px;
  background: linear-gradient(135deg, #1e1b4b 0%, #3730a3 55%, #4f46e5 100%);
}

.ppf-hero__brand {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.ppf-hero__icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.ppf-hero__title {
  margin: 0 0 2px;
  font-size: 1.05rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: #fff;
  line-height: 1.2;
}

.ppf-hero__sub {
  margin: 0;
  font-size: 11px;
  line-height: 1.35;
  color: rgba(226, 232, 240, 0.88);
}

/* フィルタ */
.ppf-toolbar-card {
  margin-bottom: 10px;
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.22);
  box-shadow: 0 2px 12px rgba(15, 23, 42, 0.05);
}

.ppf-toolbar-card :deep(.el-card__body) {
  padding: 8px 12px;
}

.ppf-toolbar {
  width: 100%;
}

.ppf-filter-form {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 8px;
}

.ppf-filter-form :deep(.el-form-item) {
  margin-bottom: 0;
  margin-right: 0;
}

.ppf-filter-form :deep(.el-form-item__label) {
  padding-right: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
}

.ppf-filt-select {
  width: 200px;
}

.ppf-filt-input {
  width: 160px;
}

.ppf-filt-status {
  width: 100px;
}

.ppf-toolbar__btns :deep(.el-button + .el-button) {
  margin-left: 6px;
}

.ppf-toolbar__btns :deep(.el-button--primary.is-plain) {
  --el-button-bg-color: #eef2ff;
  --el-button-border-color: rgba(99, 102, 241, 0.35);
  --el-button-text-color: #4f46e5;
}

/* 一覧カード */
.ppf-data-card {
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  box-shadow: 0 4px 18px rgba(15, 23, 42, 0.05);
  overflow: hidden;
}

.ppf-data-card :deep(.el-card__header) {
  padding: 8px 12px;
  border-bottom: 1px solid #e2e8f0;
  background: linear-gradient(180deg, #fafbfc, #f8fafc);
}

.ppf-data-cap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ppf-data-cap__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #0ea5e9);
}

.ppf-data-cap__title {
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
}

.ppf-data-cap__meta {
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
}

.ppf-data-card :deep(.el-card__body) {
  padding: 0;
}

.ppf-table {
  font-size: 12px;
}

.ppf-table :deep(.el-table th.el-table__cell) {
  font-size: 11px;
  font-weight: 700;
  color: #334155;
  padding: 6px 0;
  background: linear-gradient(180deg, #f8fafc, #f1f5f9) !important;
}

.ppf-table :deep(.el-table td.el-table__cell) {
  padding: 5px 0;
}

.ppf-table :deep(.el-table__row:hover > td.el-table__cell) {
  background-color: rgba(99, 102, 241, 0.04) !important;
}

.ppf-pagination {
  display: flex;
  justify-content: flex-end;
  padding: 6px 10px;
  border-top: 1px solid #f1f5f9;
  background: #fafbfc;
}

/* —— 新規／編集ダイアログ（コンパクト） —— */
:deep(.ppf-form-dialog.el-dialog) {
  border-radius: 14px;
  overflow: hidden;
  box-shadow:
    0 20px 44px -12px rgba(15, 23, 42, 0.28),
    0 0 0 1px rgba(15, 23, 42, 0.06);
}

:deep(.ppf-form-dialog .el-dialog__header) {
  margin: 0;
  padding: 0;
  border-bottom: none;
}

:deep(.ppf-form-dialog .el-dialog__body) {
  padding: 0;
  background: linear-gradient(180deg, #eef2f7 0%, #e2e8f0 100%);
}

:deep(.ppf-form-dialog .el-dialog__footer) {
  padding: 0;
  border-top: none;
  background: #fff;
}

.ppf-dlg-header {
  position: relative;
  background: linear-gradient(180deg, #fff 0%, #f8fafc 100%);
}

.ppf-dlg-header__accent {
  height: 3px;
  width: 100%;
  background: linear-gradient(90deg, #6366f1, #8b5cf6, #0ea5e9);
}

.ppf-dlg-header__main {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding: 12px 40px 10px 14px;
}

.ppf-dlg-header__icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: linear-gradient(145deg, #4f46e5 0%, #6366f1 100%);
  box-shadow: 0 6px 16px rgba(79, 70, 229, 0.35);
}

.ppf-dlg-header__icon--edit {
  background: linear-gradient(145deg, #7c3aed 0%, #6366f1 100%);
  box-shadow: 0 6px 16px rgba(124, 58, 237, 0.32);
}

.ppf-dlg-header__text {
  min-width: 0;
  padding-top: 1px;
}

.ppf-dlg-header__title {
  margin: 0 0 4px;
  font-size: 1rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: #0f172a;
  line-height: 1.25;
}

.ppf-dlg-header__desc {
  margin: 0;
  font-size: 11px;
  line-height: 1.45;
  color: #64748b;
}

.ppf-dlg-body {
  padding: 10px 12px 6px;
  max-height: min(58vh, 480px);
  overflow-y: auto;
}

.ppf-dlg-form :deep(.el-form-item) {
  margin-bottom: 12px;
}

.ppf-dlg-form :deep(.el-form-item__label) {
  font-weight: 600;
  font-size: 11px;
  color: #475569;
  margin-bottom: 4px !important;
}

.ppf-section {
  background: #fff;
  border-radius: 10px;
  padding: 10px 12px 2px;
  margin-bottom: 10px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
}

.ppf-section--price {
  background: linear-gradient(180deg, #fff 0%, #f8fafc 100%);
  border-color: rgba(99, 102, 241, 0.22);
}

.ppf-section--remarks {
  margin-bottom: 2px;
}

.ppf-section__head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e2e8f0;
}

.ppf-section__badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 20px;
  padding: 0 6px;
  font-size: 10px;
  font-weight: 700;
  color: #64748b;
  background: #f1f5f9;
  border-radius: 5px;
}

.ppf-section__badge--accent {
  color: #fff;
  background: linear-gradient(135deg, #4f46e5, #6366f1);
}

.ppf-section__label {
  font-size: 12px;
  font-weight: 700;
  color: #334155;
}

.ppf-input-full {
  width: 100%;
}

.ppf-price-field {
  display: flex;
  align-items: stretch;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid rgba(99, 102, 241, 0.28);
  background: #fff;
  box-shadow: 0 1px 6px rgba(79, 70, 229, 0.08);
}

.ppf-price-field__prefix {
  display: flex;
  align-items: center;
  padding: 0 10px;
  font-size: 1rem;
  font-weight: 700;
  color: #4f46e5;
  background: linear-gradient(180deg, #eef2ff 0%, #e0e7ff 100%);
  border-right: 1px solid rgba(99, 102, 241, 0.2);
}

.ppf-price-field__input {
  flex: 1;
  min-width: 0;
  display: flex;
}

.ppf-price-field__input :deep(.el-input-number) {
  flex: 1;
  width: auto !important;
  min-width: 0;
}

.ppf-price-field__input :deep(.el-input__wrapper) {
  box-shadow: none !important;
  border-radius: 0;
  padding-left: 10px;
}

.ppf-form-item--price :deep(.el-form-item__content) {
  line-height: normal;
}

.ppf-status-rg :deep(.el-radio-button__inner) {
  padding: 6px 16px;
  font-weight: 600;
  font-size: 12px;
}

.ppf-remarks-item :deep(.el-textarea__inner) {
  border-radius: 8px;
  font-size: 12px;
}

.ppf-dlg-footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
  padding: 10px 14px 12px;
  border-top: 1px solid #e2e8f0;
  background: linear-gradient(180deg, #fafbfc 0%, #fff 100%);
}

.ppf-dlg-footer :deep(.el-button--primary) {
  border: none;
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  box-shadow: 0 2px 10px rgba(79, 70, 229, 0.3);
}

.ppf-btn-icon {
  margin-right: 4px;
  vertical-align: middle;
}

:deep(.ppf-form-dialog .el-dialog__headerbtn) {
  top: 10px;
  right: 10px;
  font-size: 16px;
}

@media (max-width: 640px) {
  .ppf-filt-select,
  .ppf-filt-input {
    width: 100%;
  }
}
</style>
