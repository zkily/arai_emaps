<template>
  <div class="page-container">
    <div class="header-section">
      <div class="header-content">
        <div class="header-icon">
          <el-icon size="32"><Box /></el-icon>
        </div>
        <div class="header-text">
          <h1 class="page-title">材料在庫管理</h1>
          <p class="page-subtitle">入出庫登録システム</p>
        </div>
      </div>
    </div>

    <el-card class="form-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="card-title">📦 在庫登録フォーム</span>
        </div>
      </template>

      <el-form
        :model="form"
        :rules="rules"
        ref="formRef"
        label-width="120px"
        class="modern-form"
        label-position="top"
      >
        <!-- 材料CD -->
        <div class="form-section">
          <el-form-item label="材料" prop="target_cd">
            <el-select
              v-model="form.target_cd"
              filterable
              placeholder="材料を選択してください"
              size="large"
              class="modern-select"
            >
              <template #prefix>
                <el-icon><Grid /></el-icon>
              </template>
              <el-option
                v-for="item in materialOptions"
                :key="item.cd"
                :label="`${item.cd} | ${item.name}`"
                :value="item.cd"
              />
            </el-select>
          </el-form-item>
        </div>

        <!-- 保管場所 -->
        <div class="form-section">
          <el-form-item label="保管場所" prop="location_cd">
            <el-radio-group v-model="form.location_cd" class="modern-radio-group location-group">
              <el-radio-button
                v-for="loc in locationOptions"
                :key="loc.cd"
                :label="loc.cd"
                class="modern-radio-button"
              >
                {{ loc.name }}
              </el-radio-button>
            </el-radio-group>
          </el-form-item>
        </div>

        <!-- 操作種別 -->
        <div class="form-section">
          <el-form-item label="操作種別" prop="transaction_type">
            <el-radio-group
              v-model="form.transaction_type"
              class="modern-radio-group transaction-group"
            >
              <el-radio-button value="入庫" class="modern-radio-button type-in"
                >📥 入庫</el-radio-button
              >
              <el-radio-button value="出庫" class="modern-radio-button type-out"
                >📤 出庫</el-radio-button
              >
              <el-radio-button value="調整" class="modern-radio-button type-adjust"
                >⚖️ 調整</el-radio-button
              >
              <el-radio-button value="廃棄" class="modern-radio-button type-dispose"
                >🗑️ 廃棄</el-radio-button
              >
              <el-radio-button value="保留" class="modern-radio-button type-hold"
                >⏸️ 保留</el-radio-button
              >
              <el-radio-button value="初期" class="modern-radio-button type-initial"
                >🔄 初期</el-radio-button
              >
            </el-radio-group>
          </el-form-item>
        </div>

        <!-- 数量 + 単位 -->
        <div class="form-section">
          <el-form-item label="数量" prop="quantity">
            <div class="quantity-unit-container">
              <el-input-number
                v-model="form.quantity"
                :min="0"
                :step="1"
                size="large"
                class="modern-input-number"
                placeholder="数量を入力"
              />
              <el-select
                v-model="form.unit"
                placeholder="単位を選択"
                size="large"
                class="modern-select unit-select"
              >
                <template #prefix>
                  <el-icon><Aim /></el-icon>
                </template>
                <el-option label="束" value="束" />
                <el-option label="kg" value="kg" />
                <el-option label="m" value="m" />
                <el-option label="枚" value="枚" />
                <el-option label="個" value="個" />
                <el-option label="本" value="本" />
                <el-option label="箱" value="箱" />
                <el-option label="その他" value="その他" />
              </el-select>
            </div>
          </el-form-item>
        </div>

        <!-- 束本数 -->
        <div class="form-section">
          <el-form-item label="束本数" prop="base_qty">
            <div class="base-qty-container">
              <el-input-number
                v-model="form.base_qty"
                :min="0"
                :step="1"
                size="large"
                class="modern-input-number"
                placeholder="束あたりの本数"
              />
              <span class="unit-label">本/束</span>
            </div>
          </el-form-item>
        </div>

        <!-- 伝票情報 -->
        <div class="form-section">
          <el-form-item label="関連伝票">
            <div class="document-row">
              <el-input
                v-model="form.related_doc_type"
                placeholder="伝票種別"
                size="large"
                class="modern-input doc-type"
              >
                <template #prefix>
                  <el-icon><Document /></el-icon>
                </template>
              </el-input>
              <el-input
                v-model="form.related_doc_no"
                placeholder="伝票番号"
                size="large"
                class="modern-input doc-no"
              >
                <template #prefix>
                  <el-icon><Tickets /></el-icon>
                </template>
              </el-input>
            </div>
          </el-form-item>
        </div>

        <div class="form-section">
          <el-form-item label="備考">
            <el-input
              v-model="form.remarks"
              type="textarea"
              :rows="3"
              placeholder="備考を入力してください..."
              class="modern-textarea"
              resize="none"
            />
          </el-form-item>
        </div>

        <!-- 操作日時 -->
        <div class="form-section">
          <el-form-item label="操作日時" prop="transaction_time">
            <el-date-picker
              v-model="form.transaction_time"
              type="datetime"
              value-format="YYYY-MM-DD HH:mm:ss"
              placeholder="日時を選択してください"
              size="large"
              class="modern-date-picker"
            >
              <template #default-icon>
                <el-icon><Calendar /></el-icon>
              </template>
            </el-date-picker>
          </el-form-item>
        </div>

        <!-- 操作 -->
        <div class="form-actions">
          <el-button
            type="primary"
            size="large"
            class="submit-button"
            @click="submit"
            :loading="false"
          >
            <el-icon class="mr-2"><Check /></el-icon>
            登録する
          </el-button>
          <el-button size="large" class="reset-button" @click="resetForm">
            <el-icon class="mr-2"><RefreshLeft /></el-icon>
            リセット
          </el-button>
        </div>
      </el-form>
    </el-card>

    <!-- 登録した材料一覧 -->
    <el-card v-if="todayLoggedMaterials.length" class="result-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="card-title">📊 本日の登録履歴</span>
          <el-tag type="info" size="small">{{ todayLoggedMaterials.length }}件</el-tag>
        </div>
      </template>

      <el-table
        :data="todayLoggedMaterials"
        class="modern-table"
        :header-cell-style="{ background: '#f8fafc', color: '#374151', fontWeight: '600' }"
        :row-style="{ transition: 'all 0.3s ease' }"
      >
        <el-table-column prop="cd" label="材料CD" width="120" align="center" />
        <el-table-column prop="name" label="材料名称" show-overflow-tooltip />
        <el-table-column prop="transaction_type" label="操作種別" width="100" align="center">
          <template #default="{ row }">
            <el-tag
              :type="getTransactionTypeColor(row.transaction_type)"
              size="small"
              effect="light"
            >
              {{ row.transaction_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="quantity" label="数量" width="80" align="center" />
        <el-table-column prop="unit" label="単位" width="80" align="center" />
      </el-table>
    </el-card>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Box,
  Grid,
  Aim,
  Document,
  Tickets,
  Calendar,
  Check,
  RefreshLeft,
} from '@element-plus/icons-vue'
import request from '@/utils/request'
import { getMaterialOptions } from '@/api/options'
import type { OptionItem } from '@/types/master'
import { createMaterialLog } from '@/api/material'

interface MaterialStockForm {
  target_cd: string
  location_cd: string
  transaction_type: string
  quantity: number
  unit: string
  base_qty: number
  related_doc_type: string
  related_doc_no: string
  remarks: string
  transaction_time: string
}

interface LoggedMaterial extends OptionItem {
  transaction_type: string
  quantity: number
  unit: string
}

function getLocalDateTimeString() {
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  const hh = String(now.getHours()).padStart(2, '0')
  const mm = String(now.getMinutes()).padStart(2, '0')
  const ss = String(now.getSeconds()).padStart(2, '0')
  return `${y}-${m}-${d} ${hh}:${mm}:${ss}`
}

const createInitialForm = (): MaterialStockForm => ({
  target_cd: '',
  location_cd: '材料置場',
  transaction_type: '',
  quantity: 0,
  unit: '束',
  base_qty: 0,
  related_doc_type: '',
  related_doc_no: '',
  remarks: '',
  transaction_time: getLocalDateTimeString(),
})

const formRef = ref<InstanceType<typeof import('element-plus').ElForm>>()
const form = ref<MaterialStockForm>(createInitialForm())

const rules = {
  target_cd: [{ required: true, message: '材料を選択してください', trigger: 'change' }],
  location_cd: [{ required: true, message: '保管場所を選択してください', trigger: 'change' }],
  transaction_type: [{ required: true, message: '操作種別を選択してください', trigger: 'change' }],
  quantity: [{ required: true, message: '数量を入力してください', trigger: 'blur' }],
  unit: [{ required: true, message: '単位を選択してください', trigger: 'change' }],
  base_qty: [{ required: true, message: '束本数を入力してください', trigger: 'blur' }],
  transaction_time: [{ required: true, message: '操作日時を選択してください', trigger: 'change' }],
}

const materialOptions = ref<OptionItem[]>([])
const locationOptions = ref<OptionItem[]>([
  { cd: '材料置場', name: '材料置場' },
  { cd: 'その他', name: 'その他' },
])

const todayLoggedMaterials = ref<LoggedMaterial[]>([])

onMounted(async () => {
  materialOptions.value = await getMaterialOptions()
})

const submit = async () => {
  try {
    await formRef.value!.validate()
  } catch {
    ElMessage.warning('必須項目を確認してください')
    return
  }

  try {
    // 创建库存交易记录
    await request.post('/api/stock/transaction', {
      stock_type: '材料',
      ...form.value,
      process_cd: 'KT19',
    })

    // 创建材料日志记录
    const materialItem = materialOptions.value.find((m) => m.cd === form.value.target_cd)
    const itemMap: Record<string, string> = {
      入庫: '材料受入',
      出庫: '材料出庫',
      検品: '材料検品',
      返品: '材料返品',
      調整: '在庫調整',
      廃棄: '材料廃棄',
    }

    await createMaterialLog({
      item: itemMap[form.value.transaction_type] || form.value.transaction_type,
      material_cd: form.value.target_cd,
      material_name: materialItem?.name || form.value.target_cd,
      process_cd: 'KT19',
      transaction_type: form.value.transaction_type,
      quantity: form.value.quantity,
      pieces_per_bundle: form.value.base_qty || 1,
      hd_no: form.value.related_doc_no,
      remarks: form.value.remarks,
    } as any)

    ElMessage.success('在庫履歴を登録しました')

    // 当日の登録のみ記录
    const today = new Date()
    const y = today.getFullYear()
    const m = String(today.getMonth() + 1).padStart(2, '0')
    const d = String(today.getDate()).padStart(2, '0')
    const todayYMD = `${y}-${m}-${d}`
    const loggedDate = form.value.transaction_time.slice(0, 10)

    if (loggedDate === todayYMD) {
      const base = materialOptions.value.find((m) => m.cd === form.value.target_cd)
      if (
        base &&
        !todayLoggedMaterials.value.some(
          (x) =>
            x.cd === base.cd &&
            x.transaction_type === form.value.transaction_type &&
            x.quantity === form.value.quantity &&
            x.unit === form.value.unit,
        )
      ) {
        todayLoggedMaterials.value.push({
          cd: base.cd,
          name: base.name,
          transaction_type: form.value.transaction_type,
          quantity: form.value.quantity,
          unit: form.value.unit,
        })
      }
    }

    resetForm()
  } catch {
    ElMessage.error('登録に失敗しました')
  }
}

const resetForm = () => {
  formRef.value!.resetFields()
  form.value = createInitialForm()
}

const getTransactionTypeColor = (
  type: string,
): 'primary' | 'success' | 'warning' | 'info' | 'danger' => {
  const colorMap: Record<string, 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
    入庫: 'success',
    出庫: 'warning',
    調整: 'info',
    廃棄: 'danger',
    保留: 'warning',
    初期: 'primary',
  }
  return colorMap[type] || 'info'
}
</script>

<style scoped>
/* 页面容器 */
.page-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 12px;
  position: relative;
}

.page-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    radial-gradient(circle at 20% 80%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 40% 40%, rgba(120, 119, 198, 0.2) 0%, transparent 50%);
  pointer-events: none;
}

/* 头部区域 */
.header-section {
  position: relative;
  z-index: 1;
  margin-bottom: 16px;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  max-width: 800px;
  margin: 0 auto;
}

.header-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  color: #667eea;
}

.header-text {
  text-align: center;
}

.page-title {
  font-size: 2rem;
  font-weight: 700;
  color: #ffffff;
  margin: 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  letter-spacing: -0.025em;
}

.page-subtitle {
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.8);
  margin: 4px 0 0 0;
  font-weight: 400;
}

/* 卡片样式 */
.form-card,
.result-card {
  max-width: 800px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.result-card {
  margin-top: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0;
}

.card-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 表单样式 */
.modern-form {
  padding: 4px;
}

.form-section {
  margin-bottom: 16px;
  padding: 16px;
  background: rgba(248, 250, 252, 0.5);
  border-radius: 12px;
  border: 1px solid rgba(226, 232, 240, 0.5);
  transition: all 0.3s ease;
}

.form-section:hover {
  background: rgba(248, 250, 252, 0.8);
  border-color: rgba(99, 102, 241, 0.2);
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.modern-form :deep(.el-form-item__label) {
  font-weight: 600;
  color: #374151;
  font-size: 0.8rem;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* 选择器样式 */
.modern-select :deep(.el-input__wrapper) {
  border-radius: 8px;
  border: 1.5px solid #e5e7eb;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  background: #ffffff;
}

.modern-select :deep(.el-input__wrapper:hover) {
  border-color: #6366f1;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.15);
}

.modern-select :deep(.el-input__wrapper.is-focus) {
  border-color: #6366f1;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1);
}

/* 单选按钮组样式 */
.modern-radio-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.modern-radio-group :deep(.el-radio-button) {
  margin: 0;
}

.modern-radio-group :deep(.el-radio-button__inner) {
  border-radius: 8px !important;
  padding: 8px 16px;
  background: #ffffff;
  color: #6b7280;
  border: 1.5px solid #e5e7eb;
  font-weight: 500;
  min-width: 80px;
  text-align: center;
  transition: all 0.3s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.modern-radio-group :deep(.el-radio-button__inner:hover) {
  border-color: #6366f1;
  color: #6366f1;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.15);
}

.modern-radio-group :deep(.el-radio-button__orig-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: #ffffff;
  border-color: #6366f1;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
  transform: translateY(-1px);
}

/* 操作类型特殊样式 */
.transaction-group :deep(.type-in.el-radio-button__orig-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border-color: #10b981;
}

.transaction-group :deep(.type-out.el-radio-button__orig-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  border-color: #f59e0b;
}

.transaction-group
  :deep(.type-adjust.el-radio-button__orig-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border-color: #3b82f6;
}

.transaction-group
  :deep(.type-dispose.el-radio-button__orig-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  border-color: #ef4444;
}

/* 数量和单位容器 */
.quantity-unit-container {
  display: flex;
  gap: 12px;
  align-items: center;
}

.modern-input-number {
  flex: 1;
  max-width: 200px;
}

.modern-input-number :deep(.el-input__wrapper) {
  border-radius: 8px;
  border: 1.5px solid #e5e7eb;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.modern-input-number :deep(.el-input__wrapper:hover) {
  border-color: #6366f1;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.15);
}

.unit-select {
  flex: 0 0 140px;
}

/* 束本数容器 */
.base-qty-container {
  display: flex;
  align-items: center;
  gap: 8px;
}

.unit-label {
  color: #6b7280;
  font-weight: 500;
  font-size: 0.8rem;
  background: #f3f4f6;
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

/* 文档输入行 */
.document-row {
  display: flex;
  gap: 12px;
}

.doc-type {
  flex: 1;
}

.doc-no {
  flex: 1.2;
}

.modern-input :deep(.el-input__wrapper) {
  border-radius: 8px;
  border: 1.5px solid #e5e7eb;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.modern-input :deep(.el-input__wrapper:hover) {
  border-color: #6366f1;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.15);
}

.modern-input :deep(.el-input__wrapper.is-focus) {
  border-color: #6366f1;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1);
}

/* 文本域样式 */
.modern-textarea :deep(.el-textarea__inner) {
  border-radius: 8px;
  border: 1.5px solid #e5e7eb;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  font-family: inherit;
}

.modern-textarea :deep(.el-textarea__inner:hover) {
  border-color: #6366f1;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.15);
}

.modern-textarea :deep(.el-textarea__inner:focus) {
  border-color: #6366f1;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1);
}

/* 日期选择器样式 */
.modern-date-picker {
  width: 100%;
}

.modern-date-picker :deep(.el-input__wrapper) {
  border-radius: 8px;
  border: 1.5px solid #e5e7eb;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.modern-date-picker :deep(.el-input__wrapper:hover) {
  border-color: #6366f1;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.15);
}

/* 按钮样式 */
.form-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  padding: 20px 16px 16px;
  margin-top: 16px;
}

.submit-button {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border: none;
  border-radius: 8px;
  padding: 12px 24px;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
  transition: all 0.3s ease;
}

.submit-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.4);
}

.reset-button {
  background: #ffffff;
  border: 1.5px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px 24px;
  font-weight: 600;
  color: #6b7280;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.reset-button:hover {
  border-color: #6366f1;
  color: #6366f1;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.15);
}

/* 表格样式 */
.modern-table {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.modern-table :deep(.el-table__header) {
  background: #f8fafc;
}

.modern-table :deep(.el-table__row:hover) {
  background: #f8fafc;
  transform: scale(1.005);
}

.modern-table :deep(.el-table td) {
  border-bottom: 1px solid #f1f5f9;
  padding: 12px 8px;
}

.modern-table :deep(.el-table th) {
  border-bottom: 2px solid #e2e8f0;
  padding: 12px 8px;
}

/* 工具类 */
.mr-2 {
  margin-right: 6px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-container {
    padding: 8px;
  }

  .header-content {
    flex-direction: column;
    text-align: center;
  }

  .page-title {
    font-size: 2rem;
  }

  .form-card,
  .result-card {
    margin: 0 auto;
  }

  .modern-radio-group {
    justify-content: center;
  }

  .quantity-unit-container,
  .document-row {
    flex-direction: column;
    gap: 8px;
  }

  .form-actions {
    flex-direction: column;
    align-items: center;
  }

  .submit-button,
  .reset-button {
    width: 100%;
    max-width: 200px;
  }
}
</style>
