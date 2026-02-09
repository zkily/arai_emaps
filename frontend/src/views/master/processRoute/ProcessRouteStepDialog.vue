<template>
  <el-dialog class="route-step-dialog" v-model="visible" :title="''" width="500px" top="8vh"
    :close-on-click-modal="false" @close="onClose" destroy-on-close>
    <template #header>
      <div class="dialog-header">
        <div class="header-icon">{{ mode === 'add' ? '➕' : '✏️' }}</div>
        <div class="header-text">
          <h3 class="header-title">{{ mode === 'add' ? 'ステップ追加' : 'ステップ編集' }}</h3>
          <p class="header-subtitle">工程ステップ情報を設定</p>
        </div>
      </div>
    </template>

    <div class="form-container">
      <el-form :model="form" :rules="rules" ref="formRef" label-position="top" class="compact-form">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="順番" prop="step_no">
              <el-input-number v-model="form.step_no" :min="1" controls-position="right" class="full-width" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="歩留率(%)" prop="yield_percent">
              <el-input-number v-model="form.yield_percent" :min="0" :max="100" :precision="2" controls-position="right" class="full-width" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="工程" prop="process_cd">
          <el-select v-model="form.process_cd" placeholder="工程を選択" clearable filterable class="full-width">
            <el-option v-for="item in processOptions" :key="item.cd" :label="`${item.cd}｜${item.name}`" :value="item.cd" />
          </el-select>
        </el-form-item>

        <el-form-item label="標準サイクル(秒)" prop="cycle_sec">
          <el-input-number v-model="form.cycle_sec" :min="0" :precision="2" controls-position="right" class="full-width" />
          <div class="field-hint">💡 工程選択時に自動設定</div>
        </el-form-item>

        <el-form-item label="備考">
          <el-input v-model="form.remarks" type="textarea" :rows="2" placeholder="補足情報など" resize="none" />
        </el-form-item>
      </el-form>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="onClose">キャンセル</el-button>
        <el-button type="primary" :loading="saving" @click="handleSubmit" class="submit-btn">💾 保存</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { createRouteStep, updateRouteStep } from '@/api/master/processRouterMaster'
import { getProcessOptions, getProcessDetails } from '@/api/options'
import type { OptionItem, RouteStepItem } from '@/types/master'

const props = defineProps<{ visible: boolean; routeCd: string; mode: 'add' | 'edit'; initialData?: Partial<RouteStepItem> }>()
const emit = defineEmits(['update:visible', 'saved'])

const visible = ref(props.visible)
watch(() => props.visible, (val) => { visible.value = val; if (val) initialize() })

const formRef = ref()
const form = reactive({ id: undefined as number | undefined, route_cd: '', step_no: 1, process_cd: '', yield_percent: 100, cycle_sec: 0, remarks: '' })
const processOptions = ref<OptionItem[]>([])
const saving = ref(false)

watch(() => form.process_cd, async (newCd, oldCd) => {
  if (props.mode === 'add' && newCd && newCd !== oldCd) {
    try {
      const res = await getProcessDetails(newCd)
      if (res.success && res.data?.default_cycle_sec != null) {
        form.cycle_sec = res.data.default_cycle_sec
        ElMessage.success({ message: `工程「${res.data.process_name ?? newCd}」の標準サイクルを設定`, duration: 2000 })
      }
    } catch { /* ignore */ }
  }
})

const initialize = async () => {
  processOptions.value = await getProcessOptions()
  if (props.mode === 'edit' && props.initialData) Object.assign(form, props.initialData)
  else Object.assign(form, { id: undefined, route_cd: props.routeCd, step_no: 1, process_cd: '', yield_percent: 100, cycle_sec: 0, remarks: '' })
}

const rules = { step_no: [{ required: true, message: '順番は必須', trigger: 'blur' }], process_cd: [{ required: true, message: '工程を選択', trigger: 'change' }] }

const handleSubmit = () => {
  formRef.value?.validate(async (valid: boolean) => {
    if (!valid) return
    saving.value = true
    try {
      if (props.mode === 'add') await createRouteStep(props.routeCd, { route_cd: props.routeCd, step_no: form.step_no, process_cd: form.process_cd, yield_percent: form.yield_percent, cycle_sec: form.cycle_sec, remarks: form.remarks || undefined })
      else { if (form.id == null) return; await updateRouteStep(form.id, { step_no: form.step_no, process_cd: form.process_cd, yield_percent: form.yield_percent, cycle_sec: form.cycle_sec, remarks: form.remarks || undefined }) }
      ElMessage.success('保存成功'); emit('update:visible', false); emit('saved')
    } catch (e: unknown) { ElMessage.error((e && typeof e === 'object' && 'message' in e) ? String((e as { message: string }).message) : '保存失敗') }
    finally { saving.value = false }
  })
}

const onClose = () => emit('update:visible', false)
</script>

<style scoped>
.route-step-dialog :deep(.el-dialog) { border-radius: 14px; overflow: hidden; box-shadow: 0 16px 48px rgba(0,0,0,0.12); }
.route-step-dialog :deep(.el-dialog__header) { padding: 0; margin: 0; }
.route-step-dialog :deep(.el-dialog__body) { padding: 0; }
.route-step-dialog :deep(.el-dialog__footer) { padding: 0; }

.dialog-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 12px 18px; display: flex; align-items: center; gap: 12px; }
.header-icon { width: 40px; height: 40px; background: rgba(255,255,255,0.2); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; }
.header-title { margin: 0; font-size: 1.1rem; font-weight: 700; color: #fff; }
.header-subtitle { margin: 2px 0 0; font-size: 0.75rem; color: rgba(255,255,255,0.8); }

.form-container { padding: 14px 16px; background: #fafbfc; }
.compact-form :deep(.el-form-item) { margin-bottom: 12px; }
.compact-form :deep(.el-form-item__label) { font-size: 12px; font-weight: 600; color: #374151; padding-bottom: 3px; }
.full-width { width: 100%; }
.field-hint { font-size: 11px; color: #94a3b8; margin-top: 3px; }

.dialog-footer { display: flex; justify-content: flex-end; gap: 10px; padding: 10px 16px; background: #fff; border-top: 1px solid #f0f0f0; }
.submit-btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none; border-radius: 8px; font-weight: 600; }

@media (max-width: 540px) {
  .route-step-dialog :deep(.el-dialog) { width: 95vw !important; }
  .dialog-header { padding: 10px 14px; }
  .form-container { padding: 12px; }
}
</style>
