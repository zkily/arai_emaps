<template>
  <el-dialog :model-value="props.visible" @update:modelValue="(val) => emit('update:visible', val)" title="✏️ 日別受注編集"
    width="496px" :before-close="handleClose" destroy-on-close class="order-edit-dialog">
    <div class="dialog-content">
      <!-- 只读信息区域 - 优化布局 -->
      <div class="info-section">
        <div class="info-row">
          <div class="info-group">
            <div class="info-item">
              <span class="info-label">納入先CD</span>
              <span class="info-value">{{ editForm.destination_cd || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">納入先名</span>
              <span class="info-value">{{ editForm.destination_name || '-' }}</span>
            </div>
          </div>
          <div class="info-divider"></div>
          <div class="info-group">
            <div class="info-item">
              <span class="info-label">製品CD</span>
              <span class="info-value">{{ editForm.product_cd || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">製品名</span>
              <span class="info-value">{{ editForm.product_name || '-' }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 编辑表单区域 -->
      <el-form :model="editForm" :rules="rules" ref="formRef" label-width="100px" class="edit-form"
        :inline-message="true">
        <!-- 数量输入区域 -->
        <div class="form-section">
          <div class="section-title">数量情報</div>
          <div class="form-grid">
            <el-form-item label="確定箱数" prop="confirmed_boxes" class="form-item-compact">
              <el-input-number v-model="editForm.confirmed_boxes" :min="0" :disabled="isLocked" :controls="false"
                class="full-width-input" placeholder="0" />
            </el-form-item>

            <el-form-item label="確定本数" prop="confirmed_units" class="form-item-compact">
              <el-input-number v-model="editForm.confirmed_units" :min="0" :disabled="isLocked" :controls="false"
                class="full-width-input" placeholder="0" />
            </el-form-item>
          </div>
        </div>

        <!-- 状态和备注区域 -->
        <div class="form-section">
          <div class="section-title">状態・備考</div>
          <el-form-item label="状態" prop="status" class="form-item-compact">
            <el-select v-model="editForm.status" placeholder="選択してください" :disabled="isLocked" class="full-width-input">
              <el-option label="未出荷" value="未出荷" />
              <el-option label="出荷済" value="出荷済" />
              <el-option label="キャンセル" value="キャンセル" />
            </el-select>
          </el-form-item>

          <el-form-item label="備考" class="form-item-compact">
            <el-input v-model="editForm.remarks" type="textarea" :disabled="isLocked" placeholder="備考を入力してください"
              :autosize="{ minRows: 2, maxRows: 4 }" class="full-width-input" />
          </el-form-item>
        </div>
      </el-form>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose" size="default">キャンセル</el-button>
        <el-button type="primary" @click="handleSave" size="default" :disabled="isLocked">
          保存する
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { updateDailyOrder } from '@/api/order/order'
import { ElMessage } from 'element-plus'
import type { OrderDaily } from '@/types/order'

// 正确声明 props
const props = defineProps<{
  visible: boolean
  order: OrderDaily | null
}>()

// 正确声明 emits
const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (e: 'saved'): void
}>()

// 本地编辑表单
const editForm = ref<Partial<OrderDaily>>({})

// 表单校验规则
const rules = {
  confirmed_boxes: [{ required: true, message: '確定箱数は必須です', trigger: 'blur' }],
  confirmed_units: [{ required: true, message: '確定本数は必須です', trigger: 'blur' }],
  status: [{ required: true, message: '状態は必須です', trigger: 'change' }]
}

// 锁定状态（出荷済时禁止修改）
const isLocked = computed(() => editForm.value.status === '出荷済')

// 表单ref
const formRef = ref()

// 监听传入的props.order，赋值到editForm
watch(() => props.order, (val) => {
  if (val) {
    editForm.value = {
      ...val,
      status: val.status || '未出荷'
    }
  }
}, { immediate: true })


// 保存按钮点击
const handleSave = async () => {
  if (!editForm.value.id) {
    ElMessage.error('対象データが正しくありません')
    return
  }
  try {
    await formRef.value?.validate()
  } catch (validateError) {
    console.error('フォーム検証失敗', validateError)
    ElMessage.error('必須項目を入力してください')
    return
  }

  try {
    await updateDailyOrder(editForm.value.id, editForm.value)
    ElMessage.success('更新成功！')
    emit('saved')
    emit('update:visible', false)
  } catch (error) {
    console.error('更新失敗', error)
    ElMessage.error('更新に失敗しました')
  }
}

// 关闭弹窗
const handleClose = () => {
  emit('update:visible', false)
}
</script>

<style scoped>
.order-edit-dialog :deep(.el-dialog__body) {
  padding: 10px 16px;
}

.dialog-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 只读信息区域 - 优化布局 */
.info-section {
  background: linear-gradient(135deg, #f8f9fa 0%, #f0f2f5 100%);
  border-radius: 10px;
  padding: 6px 20px;
  border: 1px solid #e4e7ed;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.info-row {
  display: flex;
  align-items: flex-start;
  gap: 20px;
}

.info-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-divider {
  width: 1px;
  background: linear-gradient(to bottom, transparent, #dcdfe6, transparent);
  margin: 4px 0;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.info-label {
  font-size: 11px;
  color: #909399;
  font-weight: 600;
  line-height: 1.4;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-value {
  font-size: 14px;
  color: #303133;
  font-weight: 600;
  line-height: 1.6;
  word-break: break-word;
}

/* 编辑表单区域 */
.edit-form {
  margin: 0;
}

/* 表单分组 */
.form-section {
  margin-bottom: 5px;
}

.form-section:last-child {
  margin-bottom: 0;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 14px;
  padding-bottom: 8px;
  border-bottom: 2px solid #e4e7ed;
  letter-spacing: 0.3px;
}

.edit-form :deep(.el-form-item) {
  margin-bottom: 5px;
}

.form-item-compact {
  margin-bottom: 8px !important;
}

.form-item-compact :deep(.el-form-item__label) {
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  line-height: 36px;
  padding-bottom: 0;
}

.form-item-compact :deep(.el-form-item__content) {
  line-height: 36px;
}

.form-item-compact :deep(.el-form-item__error) {
  padding-top: 4px;
  font-size: 12px;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}

.full-width-input {
  width: 100%;
}

/* 输入框样式优化 */
.edit-form :deep(.el-input-number),
.edit-form :deep(.el-select),
.edit-form :deep(.el-input) {
  width: 100%;
}

/* 选择框样式优化 */
.edit-form :deep(.el-select .el-input__wrapper) {
  border-radius: 8px;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  border-color: #dcdfe6;
  height: 36px;
}

.edit-form :deep(.el-select .el-input__wrapper:hover) {
  border-color: #c0c4cc;
}

.edit-form :deep(.el-select.is-focus .el-input__wrapper) {
  border-color: #409eff;
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.12);
}

/* 无控制按钮的数字输入框样式 */
.edit-form :deep(.el-input-number.is-controls-right .el-input__wrapper),
.edit-form :deep(.el-input-number:not(.is-controls-right) .el-input__wrapper) {
  padding-right: 11px;
}

.edit-form :deep(.el-input-number.is-controls-right .el-input__inner),
.edit-form :deep(.el-input-number:not(.is-controls-right) .el-input__inner) {
  text-align: center;
}

.edit-form :deep(.el-input__inner),
.edit-form :deep(.el-input__wrapper) {
  border-radius: 8px;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  border-color: #dcdfe6;
  height: 36px;
}

.edit-form :deep(.el-input__inner):hover,
.edit-form :deep(.el-input__wrapper:hover) {
  border-color: #c0c4cc;
}

.edit-form :deep(.el-input__inner):focus,
.edit-form :deep(.el-input__wrapper.is-focus) {
  border-color: #409eff;
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.12);
}

.edit-form :deep(.el-textarea__inner) {
  border-radius: 8px;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: 13px;
  line-height: 1.6;
  border-color: #dcdfe6;
  padding: 10px 12px;
}

.edit-form :deep(.el-textarea__inner):hover {
  border-color: #c0c4cc;
}

.edit-form :deep(.el-textarea__inner):focus {
  border-color: #409eff;
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.12);
}

/* 禁用状态样式 */
.edit-form :deep(.el-input.is-disabled .el-input__inner),
.edit-form :deep(.el-input-number.is-disabled .el-input__inner),
.edit-form :deep(.el-select.is-disabled .el-input__inner),
.edit-form :deep(.el-textarea.is-disabled .el-textarea__inner) {
  background-color: #f5f7fa;
  border-color: #e4e7ed;
  color: #909399;
  cursor: not-allowed;
}

/* 底部按钮区域 */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 4px;
}

.order-edit-dialog :deep(.el-dialog__footer) {
  padding: 16px 24px 20px;
  border-top: 1px solid #e4e7ed;
  background: #fafafa;
}

.order-edit-dialog :deep(.el-button) {
  padding: 10px 20px;
  font-weight: 500;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.order-edit-dialog :deep(.el-button--primary) {
  box-shadow: 0 2px 4px rgba(64, 158, 255, 0.2);
}

.order-edit-dialog :deep(.el-button--primary:hover) {
  box-shadow: 0 4px 8px rgba(64, 158, 255, 0.3);
  transform: translateY(-1px);
}

/* 响应式调整 */
@media (max-width: 640px) {
  .order-edit-dialog {
    width: 95% !important;
  }

  .order-edit-dialog :deep(.el-dialog__body) {
    padding: 16px 18px;
  }

  .form-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .info-row {
    flex-direction: column;
    gap: 16px;
  }

  .info-divider {
    width: 100%;
    height: 1px;
    background: linear-gradient(to right, transparent, #dcdfe6, transparent);
    margin: 0;
  }

  .form-section {
    margin-bottom: 20px;
  }
}
</style>
