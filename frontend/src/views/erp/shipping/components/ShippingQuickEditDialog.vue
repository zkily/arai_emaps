<template>
  <el-dialog
    v-model="dialogVisible"
    title="数量・箱数 編集"
    width="420px"
    @close="handleClose"
    :close-on-click-modal="false"
    class="quick-edit-dialog"
  >
    <div v-if="!shippingItem" class="loading-container">
      <el-icon class="is-loading">
        <Loading />
      </el-icon>
      <span>ロード中...</span>
    </div>
    <div v-else class="edit-form-container">
      <!-- 只读信息区域 -->
      <div class="readonly-info">
        <div class="info-item">
          <el-icon class="info-icon">
            <Document />
          </el-icon>
          <div class="info-content">
            <span class="info-label">出荷番号</span>
            <span class="info-value">{{ shippingItem.shipping_no }}</span>
          </div>
        </div>
        <div class="info-item">
          <el-icon class="info-icon">
            <Box />
          </el-icon>
          <div class="info-content">
            <span class="info-label">製品CD</span>
            <span class="info-value">{{ shippingItem.product_cd }}</span>
          </div>
        </div>
      </div>

      <!-- 编辑表单区域 -->
      <el-form :model="form" ref="formRef" class="compact-form" label-position="top">
        <el-form-item label="製品名" prop="product_name" class="form-item-compact">
          <el-input v-model="form.product_name" class="modern-input" />
        </el-form-item>
        <el-form-item label="納入日" prop="delivery_date" class="form-item-compact">
          <el-date-picker
            v-model="form.delivery_date"
            type="date"
            placeholder="納入日を選択"
            value-format="YYYY-MM-DD"
            class="modern-date-picker"
            style="width: 100%"
          />
        </el-form-item>
        <div class="number-inputs-row">
          <el-form-item label="箱数" prop="confirmed_boxes" class="form-item-compact number-item">
            <el-input-number
              v-model="form.confirmed_boxes"
              :min="0"
              controls-position="right"
              class="modern-number-input"
            />
          </el-form-item>
          <el-form-item label="数量" prop="confirmed_units" class="form-item-compact number-item">
            <el-input-number
              v-model="form.confirmed_units"
              :min="0"
              controls-position="right"
              class="modern-number-input"
            />
          </el-form-item>
        </div>
      </el-form>
    </div>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose" class="cancel-btn">キャンセル</el-button>
        <el-button type="primary" @click="handleSave" :loading="loading" class="save-btn">
          <el-icon v-if="!loading">
            <Check />
          </el-icon>
          保存
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import request from '@/utils/request'
import { ElMessage } from 'element-plus'
import { Document, Box, Loading, Check } from '@element-plus/icons-vue'

// 出荷アイテムのインターフェース定義
interface ShippingItem {
  shipping_no: string
  product_cd: string
  product_name: string
  delivery_date: string | null
  confirmed_boxes: number
  confirmed_units: number
}

const props = defineProps<{
  modelValue: boolean
  shippingItem: ShippingItem
}>()

const emit = defineEmits(['update:modelValue', 'refresh'])

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})
const loading = ref(false)
const form = ref({
  product_name: '',
  delivery_date: '',
  confirmed_boxes: 0,
  confirmed_units: 0,
})

watch(
  () => props.shippingItem,
  (newItem) => {
    if (newItem) {
      form.value.product_name = newItem.product_name
      form.value.delivery_date = newItem.delivery_date || ''
      form.value.confirmed_boxes = newItem.confirmed_boxes
      form.value.confirmed_units = newItem.confirmed_units
    }
  },
  { immediate: true },
)

const handleClose = () => {
  dialogVisible.value = false
}

const handleSave = async () => {
  loading.value = true
  try {
    const payload = {
      shipping_no: props.shippingItem.shipping_no,
      product_cd: props.shippingItem.product_cd,
      product_name: form.value.product_name,
      delivery_date: form.value.delivery_date || null,
      confirmed_boxes: form.value.confirmed_boxes,
      confirmed_units: form.value.confirmed_units,
    }
    // This API endpoint needs to be created on the backend.
    await request.patch('/api/shipping/quick-update', payload)
    ElMessage.success('更新しました。')
    emit('refresh')
    handleClose()
  } catch (error) {
    ElMessage.error('更新に失敗しました。')
    console.error(error)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* 全局字体设置 */
.quick-edit-dialog,
.quick-edit-dialog * {
  font-family: 'Yu Gothic', 'YuGothic', 'Hiragino Kaku Gothic ProN', 'Hiragino Kaku Gothic Pro',
    'Meiryo', sans-serif;
}

/* 对话框样式 */
:deep(.quick-edit-dialog) {
  border-radius: 12px;
  overflow: hidden;
}

:deep(.quick-edit-dialog .el-dialog) {
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
}

:deep(.quick-edit-dialog .el-dialog__header) {
  background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
  color: white;
  padding: 12px 20px;
  margin: 0;
  border-bottom: none;
}

:deep(.quick-edit-dialog .el-dialog__title) {
  color: white;
  font-weight: 600;
  font-size: 16px;
  letter-spacing: 0.5px;
}

:deep(.quick-edit-dialog .el-dialog__headerbtn) {
  top: 12px;
  right: 16px;
}

:deep(.quick-edit-dialog .el-dialog__close) {
  color: white;
  font-size: 18px;
}

:deep(.quick-edit-dialog .el-dialog__close:hover) {
  color: rgba(255, 255, 255, 0.8);
}

:deep(.quick-edit-dialog .el-dialog__body) {
  padding: 16px 20px;
  background: white;
}

/* 加载容器 */
.loading-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px;
  color: #6b7280;
  font-size: 14px;
}

.loading-container .el-icon {
  font-size: 18px;
}

/* 编辑表单容器 */
.edit-form-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 只读信息区域 */
.readonly-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 12px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.info-icon {
  color: #2563eb;
  font-size: 16px;
  flex-shrink: 0;
}

.info-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.info-label {
  font-size: 11px;
  color: #6b7280;
  font-weight: 500;
  letter-spacing: 0.3px;
}

.info-value {
  font-size: 13px;
  color: #1f2937;
  font-weight: 600;
  letter-spacing: 0.2px;
}

/* 紧凑表单 */
.compact-form {
  margin: 0;
}

.form-item-compact {
  margin-bottom: 12px;
}

.form-item-compact:last-child {
  margin-bottom: 0;
}

:deep(.form-item-compact .el-form-item__label) {
  font-size: 12px;
  font-weight: 600;
  color: #374151;
  padding-bottom: 4px;
  line-height: 1.2;
  margin-bottom: 0;
}

:deep(.form-item-compact .el-form-item__content) {
  line-height: 1;
}

/* 数字输入行 */
.number-inputs-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.number-item {
  margin-bottom: 0;
}

/* 现代输入框 */
.modern-input :deep(.el-input__wrapper) {
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  border: 1px solid #d1d5db;
  transition: all 0.2s ease;
  padding: 6px 12px;
}

.modern-input :deep(.el-input__wrapper:hover) {
  border-color: #2563eb;
  box-shadow: 0 2px 6px rgba(37, 99, 235, 0.15);
}

.modern-input :deep(.el-input__wrapper.is-focus) {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.modern-input :deep(.el-input__inner) {
  font-size: 13px;
  color: #1f2937;
  font-weight: 500;
}

/* 现代日期选择器 */
.modern-date-picker :deep(.el-input__wrapper) {
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  border: 1px solid #d1d5db;
  transition: all 0.2s ease;
  padding: 6px 12px;
}

.modern-date-picker :deep(.el-input__wrapper:hover) {
  border-color: #2563eb;
  box-shadow: 0 2px 6px rgba(37, 99, 235, 0.15);
}

.modern-date-picker :deep(.el-input__wrapper.is-focus) {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.modern-date-picker :deep(.el-input__inner) {
  font-size: 13px;
  color: #1f2937;
  font-weight: 500;
}

.modern-date-picker :deep(.el-input__prefix) {
  color: #6b7280;
}

/* 现代数字输入框 */
.modern-number-input {
  width: 100%;
}

.modern-number-input :deep(.el-input__wrapper) {
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  border: 1px solid #d1d5db;
  transition: all 0.2s ease;
  padding: 6px 12px;
}

.modern-number-input :deep(.el-input__wrapper:hover) {
  border-color: #2563eb;
  box-shadow: 0 2px 6px rgba(37, 99, 235, 0.15);
}

.modern-number-input :deep(.el-input__wrapper.is-focus) {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.modern-number-input :deep(.el-input__inner) {
  font-size: 13px;
  color: #1f2937;
  font-weight: 600;
  text-align: left;
}

.modern-number-input :deep(.el-input-number__increase),
.modern-number-input :deep(.el-input-number__decrease) {
  width: 24px;
  height: 50%;
  border-left: 1px solid #d1d5db;
  background: #f9fafb;
  transition: all 0.2s ease;
}

.modern-number-input :deep(.el-input-number__increase:hover),
.modern-number-input :deep(.el-input-number__decrease:hover) {
  background: #2563eb;
  color: white;
}

/* 对话框底部 */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 0;
}

.cancel-btn {
  border-radius: 6px;
  padding: 6px 16px;
  font-weight: 600;
  font-size: 13px;
  border: 1px solid #d1d5db;
  background: white;
  color: #374151;
  transition: all 0.2s ease;
}

.cancel-btn:hover {
  background: #f3f4f6;
  border-color: #9ca3af;
  color: #1f2937;
}

.save-btn {
  border-radius: 6px;
  padding: 6px 20px;
  font-weight: 600;
  font-size: 13px;
  background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
  border: none;
  color: white;
  box-shadow: 0 2px 6px rgba(37, 99, 235, 0.3);
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 6px;
}

.save-btn:hover {
  background: linear-gradient(135deg, #1d4ed8 0%, #1e3a8a 100%);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
  transform: translateY(-1px);
}

.save-btn:active {
  transform: translateY(0);
}

.save-btn .el-icon {
  font-size: 14px;
}

/* 禁用输入框样式 */
:deep(.el-input.is-disabled .el-input__wrapper) {
  background: #f3f4f6;
  border-color: #e5e7eb;
  cursor: not-allowed;
}

:deep(.el-input.is-disabled .el-input__inner) {
  color: #6b7280;
  -webkit-text-fill-color: #6b7280;
}

/* 响应式设计 */
@media (max-width: 480px) {
  :deep(.quick-edit-dialog .el-dialog) {
    width: 95% !important;
    margin: 5vh auto;
  }

  .number-inputs-row {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .dialog-footer {
    flex-direction: column-reverse;
  }

  .cancel-btn,
  .save-btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
