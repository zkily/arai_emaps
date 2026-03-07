<template>
  <el-dialog v-model="visible" width="560px" :before-close="handleClose" destroy-on-close :close-on-click-modal="false" class="carrier-dialog">
    <template #header>
      <div class="dialog-header">
        <div class="header-icon">🚚</div>
        <div class="header-text">
          <h3 class="header-title">{{ t('master.carrier.dialogTitle', { mode: isEdit ? t('master.common.formEdit') : t('master.common.formRegister') }) }}</h3>
          <p class="header-subtitle">{{ t('master.carrier.dialogSubtitle') }}</p>
        </div>
      </div>
    </template>

    <div class="form-container">
      <el-form :model="form" :rules="rules" ref="formRef" label-position="top" class="compact-form" :disabled="loading">
        <div class="form-section">
          <div class="section-header"><el-icon><List /></el-icon><span>{{ t('master.common.basicInfo') }}</span></div>
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item :label="t('master.carrier.carrierCD')" prop="carrier_cd">
                <el-input v-model="form.carrier_cd" placeholder="例: U01" :disabled="isEdit" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="t('master.carrier.carrierName')" prop="carrier_name">
                <el-input v-model="form.carrier_name" :placeholder="t('master.carrier.carrierName')" />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <div class="form-section">
          <div class="section-header"><el-icon><Phone /></el-icon><span>{{ t('master.common.contact') }}</span></div>
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item :label="t('master.carrier.contactPerson')">
                <el-input v-model="form.contact_person" :placeholder="t('master.carrier.contactPerson')" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="t('master.customer.phone')">
                <el-input v-model="form.phone" placeholder="03-1234-5678" />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <div class="form-section">
          <div class="section-header"><el-icon><Timer /></el-icon><span>{{ t('master.common.other') }}</span></div>
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item :label="t('master.carrier.shippingTime')">
                <el-time-picker v-model="form.shipping_time" :placeholder="t('master.carrier.shippingTime')" format="HH:mm" value-format="HH:mm:ss" class="full-width" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="t('master.carrier.reportNo')">
                <el-input v-model="form.report_no" :placeholder="t('master.carrier.reportNo')" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item :label="t('master.carrier.note')">
            <el-input v-model="form.note" type="textarea" :rows="2" :placeholder="t('master.carrier.note')" />
          </el-form-item>
        </div>
      </el-form>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose" :disabled="loading">{{ t('master.common.cancel') }}</el-button>
        <el-button type="primary" @click="submitForm" :loading="loading" class="submit-btn">💾 {{ t('master.common.save') }}</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { List, Phone, Timer } from '@element-plus/icons-vue'
import { createCarrier, updateCarrier } from '@/api/master/carrierMaster'
import type { CarrierItem } from '@/types/master'

const { t } = useI18n()

const props = withDefaults(defineProps<{ visible: boolean; data?: CarrierItem | null }>(), { visible: false, data: undefined })
const emit = defineEmits(['update:visible', 'refresh'])

const visible = ref(props.visible)
const formRef = ref<FormInstance>()
const form = reactive({
  id: undefined as number | undefined,
  carrier_cd: '',
  carrier_name: '',
  contact_person: '',
  phone: '',
  shipping_time: '' as string | undefined,
  report_no: '',
  note: '',
  status: 1,
})

const rules: FormRules = {
  carrier_cd: [{ required: true, message: () => t('master.common.requiredCode'), trigger: 'blur' }],
  carrier_name: [{ required: true, message: () => t('master.common.requiredName'), trigger: 'blur' }],
}

const loading = ref(false)
const isEdit = computed(() => !!form.id)

function resetForm() {
  Object.assign(form, {
    id: undefined,
    carrier_cd: '',
    carrier_name: '',
    contact_person: '',
    phone: '',
    shipping_time: '',
    report_no: '',
    note: '',
    status: 1,
  })
}

watch(() => props.visible, (val) => {
  visible.value = val
  if (val) {
    if (props.data) {
      Object.assign(form, {
        id: props.data.id,
        carrier_cd: props.data.carrier_cd ?? '',
        carrier_name: props.data.carrier_name ?? '',
        contact_person: props.data.contact_person ?? '',
        phone: props.data.phone ?? '',
        shipping_time: props.data.shipping_time ?? '',
        report_no: props.data.report_no ?? '',
        note: props.data.note ?? '',
        status: props.data.status ?? 1,
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
    const payload: Partial<CarrierItem> = {
      carrier_cd: form.carrier_cd,
      carrier_name: form.carrier_name,
      contact_person: form.contact_person || undefined,
      phone: form.phone || undefined,
      shipping_time: form.shipping_time || undefined,
      report_no: form.report_no || undefined,
      note: form.note || undefined,
      status: form.status,
    }
    if (form.id != null) {
      await updateCarrier({ ...payload, id: form.id })
    } else {
      await createCarrier(payload)
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
.carrier-dialog :deep(.el-dialog) { border-radius: 14px; overflow: hidden; box-shadow: 0 16px 48px rgba(0,0,0,0.12); }
.carrier-dialog :deep(.el-dialog__header) { padding: 0; margin: 0; }
.carrier-dialog :deep(.el-dialog__body) { padding: 0; }
.carrier-dialog :deep(.el-dialog__footer) { padding: 0; }

.dialog-header { background: linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%); padding: 12px 18px; display: flex; align-items: center; gap: 12px; }
.header-icon { width: 40px; height: 40px; background: rgba(255,255,255,0.2); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.3rem; }
.header-title { margin: 0; font-size: 1.1rem; font-weight: 700; color: #fff; }
.header-subtitle { margin: 2px 0 0; font-size: 0.75rem; color: rgba(255,255,255,0.8); }

.form-container { padding: 14px 16px; background: #fafbfc; max-height: 65vh; overflow-y: auto; }
.compact-form :deep(.el-form-item) { margin-bottom: 10px; }
.compact-form :deep(.el-form-item__label) { font-size: 11px; font-weight: 600; color: #374151; padding-bottom: 2px; }
.full-width { width: 100%; }

.form-section { background: #fff; border-radius: 10px; padding: 12px 14px; border: 1px solid #e5e7eb; margin-bottom: 10px; }
.section-header { display: flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 600; color: #0ea5e9; margin-bottom: 10px; padding-bottom: 6px; border-bottom: 1px solid #f0f0f0; }

.dialog-footer { display: flex; justify-content: flex-end; gap: 10px; padding: 10px 16px; background: #fff; border-top: 1px solid #f0f0f0; }
.submit-btn { background: linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%); border: none; border-radius: 8px; font-weight: 600; }

@media (max-width: 620px) {
  .carrier-dialog :deep(.el-dialog) { width: 95vw !important; }
  .dialog-header { padding: 10px 14px; }
  .form-container { padding: 12px; }
}
</style>
