<template>
  <el-dialog 
    v-model="visible" 
    :title="''" 
    width="480px" 
    class="route-dialog" 
    :close-on-click-modal="false"
    @close="handleClose"
    destroy-on-close
  >
    <!-- Dialog Header -->
    <template #header>
      <div class="dialog-header">
        <div class="header-icon">{{ mode === 'add' ? '➕' : '✏️' }}</div>
        <div class="header-text">
          <h3 class="header-title">{{ mode === 'add' ? 'ルート追加' : 'ルート編集' }}</h3>
          <p class="header-subtitle">工程ルート情報を入力してください</p>
        </div>
      </div>
    </template>

    <!-- Form Content -->
    <div class="form-container">
      <el-form :model="form" :rules="rules" ref="formRef" label-position="top" class="compact-form">
        <el-form-item label="ルートコード" prop="route_cd">
          <el-input 
            v-model="form.route_cd" 
            placeholder="例: R-STD01" 
            :disabled="mode === 'edit'"
            :prefix-icon="'🔑'"
            class="styled-input"
          />
        </el-form-item>

        <el-form-item label="ルート名称" prop="route_name">
          <el-input 
            v-model="form.route_name" 
            placeholder="ルート名を入力"
            :prefix-icon="'📛'"
            class="styled-input"
          />
        </el-form-item>

        <el-form-item label="説明" prop="description">
          <el-input 
            v-model="form.description" 
            type="textarea" 
            :rows="2" 
            placeholder="ルートの説明を入力（任意）"
            class="styled-textarea"
            resize="none"
          />
        </el-form-item>

        <div class="switch-row">
          <div class="switch-item">
            <span class="switch-label">
              <el-icon>⚡</el-icon> 使用
            </span>
            <el-switch 
              v-model="form.is_active"
              active-color="#10b981"
              inactive-color="#e2e8f0"
            />
          </div>
          <div class="switch-item">
            <span class="switch-label">
              <el-icon>⭐</el-icon> デフォルト
            </span>
            <el-switch 
              v-model="form.is_default"
              active-color="#667eea"
              inactive-color="#e2e8f0"
            />
          </div>
        </div>
      </el-form>
    </div>

    <!-- Footer -->
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose" class="cancel-btn">
          キャンセル
        </el-button>
        <el-button type="primary" @click="handleSubmit" class="submit-btn">
          💾 保存
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { createRoute, updateRoute } from '@/api/master/processRouterMaster'
import type { RouteItem } from '@/types/master'

const props = defineProps<{
  visible: boolean
  mode: 'add' | 'edit'
  initialData?: RouteItem | null
}>()

const emit = defineEmits(['update:visible', 'saved'])

const visible = ref(props.visible)
watch(() => props.visible, (val) => (visible.value = val))

const formRef = ref<FormInstance>()
const form = reactive({
  id: undefined as number | undefined,
  route_cd: '',
  route_name: '',
  description: '',
  is_active: true,
  is_default: false
})

watch(() => props.initialData, (val) => {
  if (props.mode === 'edit' && val) {
    Object.assign(form, val)
  } else {
    resetForm()
  }
})

const rules: FormRules = {
  route_cd: [{ required: true, message: 'コードを入力してください', trigger: 'blur' }],
  route_name: [{ required: true, message: '名称を入力してください', trigger: 'blur' }]
}

const handleSubmit = () => {
  formRef.value?.validate(async (valid) => {
    if (!valid) return
    try {
      if (props.mode === 'add') {
        await createRoute({ route_cd: form.route_cd, route_name: form.route_name, description: form.description, is_active: form.is_active, is_default: form.is_default })
      } else {
        if (form.id == null) return
        await updateRoute(form.id, { route_cd: form.route_cd, route_name: form.route_name, description: form.description, is_active: form.is_active, is_default: form.is_default })
      }
      ElMessage.success('保存成功')
      emit('update:visible', false)
      emit('saved')
    } catch (err) {
      console.error(err)
    }
  })
}

const handleClose = () => {
  emit('update:visible', false)
}

const resetForm = () => {
  Object.assign(form, {
    id: undefined,
    route_cd: '',
    route_name: '',
    description: '',
    is_active: true,
    is_default: false
  })
}
</script>

<style scoped>
.route-dialog :deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.route-dialog :deep(.el-dialog__header) {
  padding: 0;
  margin: 0;
}

.route-dialog :deep(.el-dialog__body) {
  padding: 0;
}

.route-dialog :deep(.el-dialog__footer) {
  padding: 0;
}

/* Header */
.dialog-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 16px 20px;
  display: flex;
  align-items: center;
  gap: 14px;
}

.header-icon {
  width: 44px;
  height: 44px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.4rem;
}

.header-text {
  flex: 1;
}

.header-title {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 700;
  color: #fff;
}

.header-subtitle {
  margin: 2px 0 0;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.8);
}

/* Form Container */
.form-container {
  padding: 16px 20px;
  background: #fafbfc;
}

.compact-form :deep(.el-form-item) {
  margin-bottom: 14px;
}

.compact-form :deep(.el-form-item__label) {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  padding-bottom: 4px;
}

.styled-input :deep(.el-input__wrapper) {
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  border: 1px solid #e5e7eb;
  transition: all 0.3s;
}

.styled-input :deep(.el-input__wrapper:focus-within) {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.styled-textarea :deep(.el-textarea__inner) {
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  transition: all 0.3s;
}

.styled-textarea :deep(.el-textarea__inner:focus) {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

/* Switch Row */
.switch-row {
  display: flex;
  gap: 20px;
  background: #fff;
  border-radius: 12px;
  padding: 12px 16px;
  border: 1px solid #e5e7eb;
}

.switch-item {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.switch-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
  color: #4b5563;
}

/* Footer */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 12px 20px;
  background: #fff;
  border-top: 1px solid #f0f0f0;
}

.cancel-btn {
  border-radius: 10px;
  padding: 8px 20px;
  font-weight: 500;
}

.submit-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 10px;
  padding: 8px 24px;
  font-weight: 600;
  box-shadow: 0 4px 14px rgba(102, 126, 234, 0.3);
  transition: all 0.3s;
}

.submit-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

/* Responsive */
@media (max-width: 520px) {
  .route-dialog :deep(.el-dialog) {
    width: 95vw !important;
    margin: 10px auto;
  }
  
  .dialog-header {
    padding: 12px 16px;
  }
  
  .header-icon {
    width: 38px;
    height: 38px;
    font-size: 1.2rem;
  }
  
  .header-title {
    font-size: 1.1rem;
  }
  
  .form-container {
    padding: 12px 16px;
  }
  
  .switch-row {
    flex-direction: column;
    gap: 12px;
  }
  
  .dialog-footer {
    padding: 10px 16px;
  }
}
</style>
