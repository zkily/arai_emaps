<template>
  <el-dialog v-model="visible" :title="''" width="520px" class="process-dialog" :close-on-click-modal="false"
    @close="handleClose">
    <div class="dialog-title">
      <span class="icon">{{ mode === 'add' ? '＋' : '✏️' }}</span>
      <span>{{ mode === 'add' ? '工程追加' : '工程編集' }}</span>
    </div>
    <el-form :model="form" :rules="rules" ref="formRef" label-width="120px" class="form-section card-section">
      <el-form-item label="工程コード" prop="process_cd">
        <el-input v-model="form.process_cd" placeholder="例:KT01" />
      </el-form-item>
      <el-form-item label="工程名称" prop="process_name">
        <el-input v-model="form.process_name" />
      </el-form-item>
      <el-form-item label="工程略称" prop="short_name">
        <el-input v-model="form.short_name" />
      </el-form-item>
      <el-form-item label="分類" prop="category">
        <el-select v-model="form.category" placeholder="分類を選択">
          <el-option label="切断" value="cut" />
          <el-option label="面取" value="chamfer" />
          <el-option label="SW" value="swaging" />
          <el-option label="成型" value="forming" />
          <el-option label="メッキ" value="plating" />
          <el-option label="溶接" value="weld" />
          <el-option label="検査" value="inspect" />
          <el-option label="倉庫" value="warehouse" />
        </el-select>
      </el-form-item>
      <el-form-item label="外注" prop="is_outsource">
        <el-switch v-model="form.is_outsource" />
      </el-form-item>
      <el-form-item label="標準サイクル(s)" prop="default_cycle_sec">
        <el-input-number v-model="form.default_cycle_sec" :min="0" :step="0.1" :precision="1" />
      </el-form-item>
      <el-form-item label="歩留(%)" prop="default_yield">
        <el-input-number v-model="form.default_yield" :min="0" :max="100" :step="0.01" :precision="2"
          controls-position="right" style="width: 150px" />
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
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { createProcess, updateProcess } from '@/api/master/processMaster'
import type { ProcessItem } from '@/types/master'


const props = defineProps<{
  visible: boolean
  mode: 'add' | 'edit'
  initialData?: ProcessItem | null
}>()

const emit = defineEmits(['update:visible', 'saved'])

const visible = ref(props.visible)

watch(() => props.visible, (val) => {
  visible.value = val
})
watch(() => props.initialData, (val) => {
  if (props.mode === 'edit' && val) {
    Object.assign(form, val)
  } else {
    resetForm()
  }
})

const formRef = ref<FormInstance>()
const form = reactive({
  id: undefined,
  process_cd: '',
  process_name: '',
  short_name: '',
  category: '',
  is_outsource: false,
  default_cycle_sec: 0,
  default_yield: 100.00
})

const rules: FormRules = {
  process_cd: [{ required: true, message: 'コードを入力してください', trigger: 'blur' }],
  process_name: [{ required: true, message: '名称を入力してください', trigger: 'blur' }],
  category: [{ required: true, message: '分類を選択してください', trigger: 'change' }],
  default_yield: [{ type: 'number', required: true, message: '歩留は必須です', trigger: 'blur' }]
}

const handleSubmit = () => {
  formRef.value?.validate(async (valid) => {
    if (!valid) return
    try {
      if (props.mode === 'add') {
        await createProcess(form)
      } else {
        await updateProcess(form.id!, form)
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
    process_cd: '',
    process_name: '',
    category: '',
    is_outsource: false,
    default_cycle_sec: 0
  })
}
</script>

<style scoped>
.process-dialog :deep(.el-dialog) {
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
  .process-dialog :deep(.el-dialog) {
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
