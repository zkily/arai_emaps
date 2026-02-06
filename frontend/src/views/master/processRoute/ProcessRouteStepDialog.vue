<template>
  <el-dialog class="route-step-dialog" v-model="visible" :title="''" width="520px" top="10vh"
    :close-on-click-modal="false" @close="onClose">
    <div class="dialog-title">
      <span class="icon">{{ mode === 'add' ? '📦' : '✏️' }}</span>
      <span>{{ mode === 'add' ? 'ステップ追加' : 'ステップ編集' }}</span>
    </div>
    <el-form :model="form" :rules="rules" ref="formRef" label-width="160px" class="form-section card-section">
      <el-row :gutter="10">
        <el-col :span="24">
          <el-form-item label="🔢 順番" prop="step_no">
            <el-input-number v-model="form.step_no" :min="1" />
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="🛠️ 工程" prop="process_cd">
            <el-select v-model="form.process_cd" placeholder="工程を選択" clearable filterable>
              <el-option v-for="item in processOptions" :key="item.cd" :label="`${item.cd}｜${item.name}`"
                :value="item.cd" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="設備ID" prop="machine_id">
            <el-input v-model="form.machine_id" placeholder="設備ID（任意）" />
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="⏱️ 標準サイクルタイム(秒)" prop="standard_cycle_time">
            <el-input-number v-model="form.standard_cycle_time" :min="0" :precision="2" placeholder="工程選択で自動"
              style="width: 100%" />
            <div class="field-hint">※ 工程選択時に自動設定されます</div>
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="段取り時間(秒)" prop="setup_time">
            <el-input-number v-model="form.setup_time" :min="0" :precision="2" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="💬 備考">
            <el-input v-model="form.remarks" type="textarea" :rows="2" placeholder="補足情報など" />
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="onClose">❌ キャンセル</el-button>
        <el-button type="primary" :loading="saving" @click="handleSubmit">💾 保存</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { createRouteStep, updateRouteStep } from '@/api/master/processRouterMaster'
import { getProcessOptions, getProcessDetails } from '@/api/options'
import type { OptionItem } from '@/types/master'
import type { RouteStepItem } from '@/types/master'

const props = defineProps<{
  visible: boolean
  routeCd: string
  productCd: string
  mode: 'add' | 'edit'
  initialData?: Partial<RouteStepItem>
}>()
const emit = defineEmits(['update:visible', 'saved'])

const visible = ref(props.visible)
watch(() => props.visible, (val) => {
  visible.value = val
  if (val) initialize()
})

const formRef = ref()
const form = reactive({
  id: undefined as number | undefined,
  product_cd: '' as string,
  route_cd: '' as string,
  step_no: 1,
  process_cd: '' as string,
  machine_id: '' as string,
  standard_cycle_time: undefined as number | undefined,
  setup_time: undefined as number | undefined,
  remarks: ''
})

const processOptions = ref<OptionItem[]>([])
const saving = ref(false)

watch(() => form.process_cd, async (newProcessCd, oldProcessCd) => {
  if (props.mode === 'add' && newProcessCd && newProcessCd !== oldProcessCd) {
    try {
      const response = await getProcessDetails(newProcessCd)
      if (response.success && response.data?.default_cycle_sec != null) {
        form.standard_cycle_time = response.data.default_cycle_sec
        ElMessage.success({
          message: `工程「${response.data.process_name ?? newProcessCd}」の標準サイクルを設定しました`,
          duration: 2000
        })
      }
    } catch {
      // ignore
    }
  }
})

const initialize = async () => {
  processOptions.value = await getProcessOptions()
  if (props.mode === 'edit' && props.initialData) {
    Object.assign(form, props.initialData)
  } else {
    Object.assign(form, {
      id: undefined,
      product_cd: props.productCd,
      route_cd: props.routeCd,
      step_no: 1,
      process_cd: '',
      machine_id: '',
      standard_cycle_time: undefined,
      setup_time: undefined,
      remarks: ''
    })
  }
}

const rules = {
  step_no: [{ required: true, message: '順番は必須です', trigger: 'blur' }],
  process_cd: [{ required: true, message: '工程を選択してください', trigger: 'change' }]
}

const handleSubmit = () => {
  formRef.value?.validate(async (valid: boolean) => {
    if (!valid) return
    saving.value = true
    try {
      if (props.mode === 'add') {
        await createRouteStep(props.routeCd, {
          product_cd: props.productCd,
          route_cd: props.routeCd,
          step_no: form.step_no,
          process_cd: form.process_cd,
          machine_id: form.machine_id || undefined,
          standard_cycle_time: form.standard_cycle_time,
          setup_time: form.setup_time,
          remarks: form.remarks || undefined
        })
      } else {
        if (form.id == null) return
        await updateRouteStep(form.id, {
          step_no: form.step_no,
          process_cd: form.process_cd,
          machine_id: form.machine_id || undefined,
          standard_cycle_time: form.standard_cycle_time,
          setup_time: form.setup_time,
          remarks: form.remarks || undefined
        })
      }
      ElMessage.success('保存成功')
      emit('update:visible', false)
      emit('saved')
    } catch (err: unknown) {
      const msg = (err && typeof err === 'object' && 'message' in err) ? String((err as { message: string }).message) : '保存失敗'
      ElMessage.error(msg)
    } finally {
      saving.value = false
    }
  })
}

const onClose = () => {
  emit('update:visible', false)
}
</script>

<style scoped>
.route-step-dialog :deep(.el-dialog) { border-radius: 16px; }

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

.dialog-title .icon { margin-right: 8px; font-size: 22px; }

.card-section {
  background: #fafafa;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
  margin-bottom: 18px;
  padding: 24px 18px 10px 18px;
}

.form-section { padding: 0; }

.dialog-footer {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding-top: 10px;
}

.field-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.2;
}

@media (max-width: 600px) {
  .route-step-dialog :deep(.el-dialog) { width: 99vw !important; min-width: 0; }
  .card-section { padding: 6px 2px 4px 2px; }
  .dialog-title { font-size: 18px; padding: 14px 10px 8px 10px; }
}
</style>
