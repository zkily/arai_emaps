<template>
  <el-dialog
    v-model="visible"
    width="520px"
    :before-close="handleClose"
    destroy-on-close
    :close-on-click-modal="false"
    class="machine-dialog"
  >
    <template #header>
      <div class="dialog-header">
        <div class="header-icon">🛠️</div>
        <div class="header-text">
          <h3 class="header-title">{{ dialogTitle }}</h3>
          <p class="header-subtitle">{{ t('master.machine.dialogSubtitle') }}</p>
        </div>
      </div>
    </template>

    <div class="form-container">
      <el-form
        :model="form"
        :rules="rules"
        ref="formRef"
        label-position="top"
        class="compact-form"
        :disabled="loading"
      >
        <div class="form-section">
          <div class="section-header">
            <el-icon><List /></el-icon><span>{{ t('master.common.basicInfo') }}</span>
          </div>
          <el-row :gutter="10">
            <el-col :span="12">
              <el-form-item :label="t('master.machine.machineCD')" prop="machine_cd">
                <el-input v-model="form.machine_cd" placeholder="例: M01" :disabled="isEdit" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="t('master.machine.machineName')" prop="machine_name">
                <el-input v-model="form.machine_name" :placeholder="t('master.machine.machineName')" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="10">
            <el-col :span="12">
              <el-form-item :label="t('master.machine.machineType')">
                <el-select
                  v-model="form.machine_type"
                  :placeholder="t('master.common.select')"
                  clearable
                  class="full-width"
                >
                  <el-option :label="t('master.machine.typeCutting')" value="切断" />
                  <el-option :label="t('master.machine.typeChamfering')" value="面取" />
                  <el-option :label="t('master.machine.typeSW')" value="SW" />
                  <el-option :label="t('master.machine.typeMolding')" value="成型" />
                  <el-option :label="t('master.machine.typeWelding')" value="溶接" />
                  <el-option :label="t('master.machine.typePlating')" value="メッキ" />
                  <el-option :label="t('master.machine.typeInspection')" value="検査" />
                  <el-option :label="t('master.machine.typePreWeld')" value="溶接前検査" />
                  <el-option :label="t('master.machine.typeOutCut')" value="外注切断" />
                  <el-option :label="t('master.machine.typeOutMold')" value="外注成型" />
                  <el-option :label="t('master.machine.typeOutPlating')" value="外注メッキ" />
                  <el-option :label="t('master.machine.typeOutWeld')" value="外注溶接" />
                  <el-option :label="t('master.machine.typeOutInsp')" value="外注検査" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="t('master.common.status')">
                <el-select v-model="form.status" :placeholder="t('master.common.select')" class="full-width">
                  <el-option :label="t('master.machine.statusActive')" value="active" />
                  <el-option :label="t('master.machine.statusMaintenance')" value="maintenance" />
                  <el-option :label="t('master.machine.statusInactive')" value="inactive" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="10">
            <el-col :span="12">
              <el-form-item :label="t('master.machine.efficiency')">
                <el-input-number
                  v-model="form.efficiency"
                  :min="0"
                  :max="300"
                  :step="1"
                  class="full-width"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="使用可能数">
                <el-input-number v-model="form.available_qty" :min="0" :step="1" class="full-width" />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <div class="form-section">
          <div class="section-header">
            <el-icon><Timer /></el-icon><span>{{ t('master.machine.availableTime') }}</span>
          </div>
          <el-row :gutter="10">
            <el-col :span="12">
              <el-form-item :label="t('master.machine.availableFrom')">
                <el-time-picker
                  v-model="form.available_from"
                  placeholder="08:00"
                  format="HH:mm"
                  value-format="HH:mm:ss"
                  class="full-width"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="t('master.machine.availableTo')">
                <el-time-picker
                  v-model="form.available_to"
                  placeholder="17:00"
                  format="HH:mm"
                  value-format="HH:mm:ss"
                  class="full-width"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <div class="form-section">
          <div class="section-header">
            <el-icon><Document /></el-icon><span>{{ t('master.common.other') }}</span>
          </div>
          <el-form-item :label="t('master.machine.note')">
            <el-input v-model="form.note" type="textarea" :rows="2" :placeholder="t('master.machine.note')" />
          </el-form-item>
        </div>
      </el-form>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose" :disabled="loading">{{ t('master.common.cancel') }}</el-button>
        <el-button type="primary" @click="submitForm" :loading="loading" class="submit-btn">
          💾 {{ t('master.common.save') }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { List, Timer, Document } from '@element-plus/icons-vue'
import { createMachine, updateMachine } from '@/api/master/machineMaster'
import type { MachineItem } from '@/types/master'

const { t } = useI18n()

const props = withDefaults(defineProps<{ visible: boolean; data?: MachineItem | null }>(), { visible: false, data: undefined })
const emit = defineEmits(['update:visible', 'refresh'])

const visible = ref(props.visible)
const formRef = ref<FormInstance>()
const form = reactive({
  id: undefined as number | undefined,
  machine_cd: '',
  machine_name: '',
  machine_type: '',
  status: 'active',
  available_from: '' as string | undefined,
  available_to: '' as string | undefined,
  calendar_id: undefined as number | undefined,
  efficiency: 100,
  available_qty: 0,
  note: '',
})

const rules: FormRules = {
  machine_cd: [{ required: true, message: () => t('master.common.requiredCode'), trigger: 'blur' }],
  machine_name: [{ required: true, message: () => t('master.common.requiredName'), trigger: 'blur' }],
}

const loading = ref(false)
const isEdit = computed(() => !!form.id)
const modeText = computed(() =>
  isEdit.value ? t('master.common.formEdit') : t('master.common.formRegister'),
)
const dialogTitle = computed(() => {
  const raw = t('master.machine.dialogTitle', { mode: modeText.value })
  if (raw.includes('{{ mode }}')) return raw.replace('{{ mode }}', modeText.value)
  if (raw.includes('{mode}')) return raw.replace('{mode}', modeText.value)
  return raw
})

function resetForm() {
  Object.assign(form, {
    id: undefined,
    machine_cd: '',
    machine_name: '',
    machine_type: '',
    status: 'active',
    available_from: '',
    available_to: '',
    calendar_id: undefined,
    efficiency: 100,
    available_qty: 0,
    note: '',
  })
}

watch(() => props.visible, (val) => {
  visible.value = val
  if (val) {
    if (props.data) {
      Object.assign(form, {
        id: props.data.id,
        machine_cd: props.data.machine_cd ?? '',
        machine_name: props.data.machine_name ?? '',
        machine_type: props.data.machine_type ?? '',
        status: props.data.status ?? 'active',
        available_from: props.data.available_from ?? '',
        available_to: props.data.available_to ?? '',
        calendar_id: props.data.calendar_id,
        efficiency: props.data.efficiency ?? 100,
        available_qty: props.data.available_qty ?? 0,
        note: props.data.note ?? '',
      })
    } else {
      resetForm()
    }
  }
})

async function submitForm() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
    loading.value = true
    const payload: Partial<MachineItem> = {
      machine_cd: form.machine_cd,
      machine_name: form.machine_name,
      machine_type: form.machine_type || undefined,
      status: form.status,
      available_from: form.available_from || undefined,
      available_to: form.available_to || undefined,
      calendar_id: form.calendar_id,
      efficiency: form.efficiency,
      available_qty: form.available_qty,
      note: form.note || undefined,
    }
    if (form.id != null) {
      await updateMachine({ ...payload, id: form.id })
    } else {
      await createMachine(payload)
    }
    ElMessage.success(form.id ? t('master.common.updateSuccess') : t('master.common.saveSuccess'))
    emit('update:visible', false)
    emit('refresh')
  } catch (e: unknown) {
    if (e !== false) ElMessage.error(t('master.common.saveFailed'))
  } finally {
    loading.value = false
  }
}

function handleClose() {
  emit('update:visible', false)
  resetForm()
}
</script>

<style scoped>
.machine-dialog :deep(.el-dialog) {
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 20px 48px rgba(2, 132, 199, 0.2);
  border: 1px solid #cfe9ff;
}
.machine-dialog :deep(.el-dialog__header) { padding: 0; margin: 0; }
.machine-dialog :deep(.el-dialog__body) { padding: 0; }
.machine-dialog :deep(.el-dialog__footer) { padding: 0; }

.dialog-header {
  background: linear-gradient(135deg, #0284c7 0%, #06b6d4 62%, #22d3ee 100%);
  padding: 10px 14px;
  display: flex;
  align-items: center;
  gap: 10px;
}
.header-icon {
  width: 34px;
  height: 34px;
  background: rgba(255, 255, 255, 0.22);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  border: 1px solid rgba(255, 255, 255, 0.34);
}
.header-title { margin: 0; font-size: 1rem; font-weight: 700; color: #fff; line-height: 1.3; }
.header-subtitle { margin: 1px 0 0; font-size: 0.72rem; color: rgba(255, 255, 255, 0.9); }

.form-container {
  padding: 10px 10px 8px;
  background: linear-gradient(145deg, #f8fbff 0%, #f3f9ff 100%);
  max-height: 70vh;
  overflow-y: auto;
}
.compact-form :deep(.el-form-item) { margin-bottom: 8px; }
.compact-form :deep(.el-form-item__label) {
  font-size: 11px;
  font-weight: 600;
  color: #334155;
  padding-bottom: 1px;
}
.full-width { width: 100%; }

.form-section {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 10px;
  padding: 9px 10px;
  border: 1px solid #dbeafe;
  margin-bottom: 8px;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
}
.section-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 700;
  color: #0284c7;
  margin-bottom: 8px;
  padding-bottom: 5px;
  border-bottom: 1px solid #eaf3ff;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 8px 12px;
  background: #fff;
  border-top: 1px solid #eaf3ff;
}
.submit-btn {
  background: linear-gradient(135deg, #0284c7 0%, #06b6d4 100%);
  border: none;
  border-radius: 8px;
  font-weight: 600;
  min-width: 92px;
}
:deep(.el-button) {
  padding: 7px 12px;
}
:deep(.el-input__wrapper),
:deep(.el-select__wrapper),
:deep(.el-textarea__inner),
:deep(.el-input-number .el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 0 0 1px #dbeafe inset;
}
:deep(.el-textarea__inner) {
  min-height: 56px !important;
}

@media (max-width: 620px) {
  .machine-dialog :deep(.el-dialog) { width: 94vw !important; }
  .dialog-header { padding: 9px 10px; }
  .form-container { padding: 8px; }
  .form-section { padding: 8px; }
  :deep(.el-col) { max-width: 100%; flex: 0 0 100%; }
}
</style>
