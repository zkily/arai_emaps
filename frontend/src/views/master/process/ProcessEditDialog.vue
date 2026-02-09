<template>
  <el-dialog v-model="visible" :title="''" width="500px" class="process-dialog" :close-on-click-modal="false" @close="handleClose" destroy-on-close>
    <template #header>
      <div class="dialog-header">
        <div class="header-icon">{{ mode === 'add' ? '➕' : '✏️' }}</div>
        <div class="header-text">
          <h3 class="header-title">{{ mode === 'add' ? '工程追加' : '工程編集' }}</h3>
          <p class="header-subtitle">工程情報を入力してください</p>
        </div>
      </div>
    </template>

    <div class="form-container">
      <el-form :model="form" :rules="rules" ref="formRef" label-position="top" class="compact-form">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="工程コード" prop="process_cd">
              <el-input v-model="form.process_cd" placeholder="例: KT01" :disabled="mode === 'edit'" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="略称" prop="short_name">
              <el-input v-model="form.short_name" placeholder="2〜3文字" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="工程名称" prop="process_name">
          <el-input v-model="form.process_name" placeholder="工程名称" />
        </el-form-item>

        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="分類" prop="category">
              <el-select v-model="form.category" placeholder="選択" clearable class="full-width">
                <el-option label="切断" value="cut" /><el-option label="面取" value="chamfer" />
                <el-option label="SW" value="swaging" /><el-option label="成型" value="forming" />
                <el-option label="メッキ" value="plating" /><el-option label="溶接" value="weld" />
                <el-option label="検査" value="inspect" /><el-option label="倉庫" value="warehouse" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="能力単位" prop="capacity_unit">
              <el-select v-model="form.capacity_unit" class="full-width">
                <el-option label="pcs" value="pcs" /><el-option label="kg" value="kg" /><el-option label="m" value="m" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="標準サイクル(秒)" prop="default_cycle_sec">
              <el-input-number v-model="form.default_cycle_sec" :min="0" :step="0.1" :precision="2" controls-position="right" class="full-width" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="歩留(%)" prop="default_yield_percent">
              <el-input-number v-model="form.default_yield_percent" :min="0" :max="100" :step="0.1" :precision="2" controls-position="right" class="full-width" />
            </el-form-item>
          </el-col>
        </el-row>

        <div class="switch-row">
          <span class="switch-label">🏭 外注</span>
          <el-switch v-model="form.is_outsource" active-color="#e74c3c" inactive-color="#e2e8f0" />
        </div>

        <el-form-item label="備考" prop="remark">
          <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="備考（任意）" resize="none" />
        </el-form-item>
      </el-form>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">キャンセル</el-button>
        <el-button type="primary" @click="handleSubmit" class="submit-btn">💾 保存</el-button>
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

const props = defineProps<{ visible: boolean; mode: 'add' | 'edit'; initialData?: ProcessItem | null }>()
const emit = defineEmits(['update:visible', 'saved'])

const visible = ref(props.visible)
const formRef = ref<FormInstance>()
const form = reactive({ id: undefined as number | undefined, process_cd: '', process_name: '', short_name: '', category: '', is_outsource: false, default_cycle_sec: 0, default_yield_percent: 100, capacity_unit: 'pcs', remark: '' })

const rules: FormRules = { process_cd: [{ required: true, message: 'コード必須', trigger: 'blur' }], process_name: [{ required: true, message: '名称必須', trigger: 'blur' }] }

const resetForm = () => { Object.assign(form, { id: undefined, process_cd: '', process_name: '', short_name: '', category: '', is_outsource: false, default_cycle_sec: 0, default_yield_percent: 100, capacity_unit: 'pcs', remark: '' }) }

watch(() => props.visible, (val) => { visible.value = val })
watch(() => props.initialData, (val) => {
  if (props.mode === 'edit' && val) Object.assign(form, { id: val.id, process_cd: val.process_cd, process_name: val.process_name, short_name: val.short_name ?? '', category: val.category ?? '', is_outsource: val.is_outsource ?? false, default_cycle_sec: val.default_cycle_sec ?? 0, default_yield_percent: val.default_yield != null ? Number(val.default_yield) * 100 : 100, capacity_unit: val.capacity_unit ?? 'pcs', remark: val.remark ?? '' })
  else resetForm()
}, { immediate: true })

const handleSubmit = () => {
  formRef.value?.validate(async (valid) => {
    if (!valid) return
    try {
      const payload: Partial<ProcessItem> = { process_cd: form.process_cd, process_name: form.process_name, short_name: form.short_name || undefined, category: form.category || undefined, is_outsource: form.is_outsource, default_cycle_sec: form.default_cycle_sec, default_yield: form.default_yield_percent / 100, capacity_unit: form.capacity_unit, remark: form.remark || undefined }
      if (props.mode === 'add') await createProcess(payload)
      else if (form.id != null) await updateProcess(form.id, payload)
      ElMessage.success('保存成功'); emit('update:visible', false); emit('saved')
    } catch (e) { console.error(e); ElMessage.error('保存失敗') }
  })
}

const handleClose = () => emit('update:visible', false)
</script>

<style scoped>
.process-dialog :deep(.el-dialog) { border-radius: 14px; overflow: hidden; box-shadow: 0 16px 48px rgba(0,0,0,0.12); }
.process-dialog :deep(.el-dialog__header) { padding: 0; margin: 0; }
.process-dialog :deep(.el-dialog__body) { padding: 0; }
.process-dialog :deep(.el-dialog__footer) { padding: 0; }

.dialog-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 12px 18px; display: flex; align-items: center; gap: 12px; }
.header-icon { width: 40px; height: 40px; background: rgba(255,255,255,0.2); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; }
.header-title { margin: 0; font-size: 1.1rem; font-weight: 700; color: #fff; }
.header-subtitle { margin: 2px 0 0; font-size: 0.75rem; color: rgba(255,255,255,0.8); }

.form-container { padding: 14px 16px; background: #fafbfc; }
.compact-form :deep(.el-form-item) { margin-bottom: 12px; }
.compact-form :deep(.el-form-item__label) { font-size: 12px; font-weight: 600; color: #374151; padding-bottom: 3px; }
.full-width { width: 100%; }

.switch-row { display: flex; align-items: center; gap: 12px; background: #fff; border-radius: 10px; padding: 10px 14px; border: 1px solid #e5e7eb; margin-bottom: 12px; }
.switch-label { font-size: 12px; font-weight: 500; color: #4b5563; }

.dialog-footer { display: flex; justify-content: flex-end; gap: 10px; padding: 10px 16px; background: #fff; border-top: 1px solid #f0f0f0; }
.submit-btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none; border-radius: 8px; font-weight: 600; }

@media (max-width: 540px) {
  .process-dialog :deep(.el-dialog) { width: 95vw !important; }
  .dialog-header { padding: 10px 14px; }
  .form-container { padding: 12px; }
  .el-col { margin-bottom: 0; }
}
</style>
