<template>
  <el-dialog v-model="visible" :title="''" width="520px" class="route-dialog" :close-on-click-modal="false"
    @close="handleClose">
    <div class="dialog-title">
      <span class="icon">{{ mode === 'add' ? '📦' : '✏️' }}</span>
      <span>{{ mode === 'add' ? 'ルート追加' : 'ルート編集' }}</span>
    </div>
    <el-form :model="form" :rules="rules" ref="formRef" label-width="120px" class="form-section card-section">
      <el-form-item label="ルートコード" prop="route_cd">
        <el-input v-model="form.route_cd" placeholder="例:R-STD01" :disabled="mode === 'edit'" />
      </el-form-item>
      <el-form-item label="ルート名称" prop="route_name">
        <el-input v-model="form.route_name" />
      </el-form-item>
      <el-form-item label="説明" prop="description">
        <el-input v-model="form.description" type="textarea" :rows="2" />
      </el-form-item>
      <el-form-item label="デフォルト">
        <el-switch v-model="form.is_default" />
      </el-form-item>
    </el-form>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">キャンセル</el-button>
        <el-button type="primary" @click="handleSubmit">保存</el-button>
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
  id: undefined,
  route_cd: '',
  route_name: '',
  description: '',
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
        await createRoute(form)
      } else {
        await updateRoute(form.id!, form)
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
    is_default: false
  })
}
</script>

<style scoped>
.route-dialog :deep(.el-dialog) {
  border-radius: 16px;
}

.dialog-title {
  font-size: 22px;
  font-weight: bold;
  color: #2c3e50;
  padding: 20px 24px 12px;
  border-bottom: 1px solid #ebeef5;
  background: linear-gradient(to right, #e6f7ff, #ffffff);
  border-top-left-radius: 12px;
  border-top-right-radius: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.dialog-title .icon {
  margin-right: 8px;
  font-size: 22px;
}

.card-section {
  background: #fafafa;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
  margin-bottom: 18px;
  padding: 24px 18px 10px 18px;
}

.form-section {
  padding: 0;
}

.dialog-footer {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding-top: 10px;
}

@media (max-width: 600px) {
  .route-dialog :deep(.el-dialog) {
    width: 99vw !important;
    min-width: 0;
  }

  .card-section {
    padding: 6px 2px 4px 2px;
  }

  .dialog-title {
    font-size: 18px;
    padding: 14px 10px 8px 10px;
  }
}
</style>
