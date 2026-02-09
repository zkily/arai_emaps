<template>
  <el-dialog v-model="visible" width="580px" :before-close="handleClose" destroy-on-close :close-on-click-modal="false" class="destination-dialog">
    <template #header>
      <div class="dialog-header">
        <div class="header-icon">🚚</div>
        <div class="header-text">
          <h3 class="header-title">{{ t('master.destination.dialogTitle', { mode: isEdit ? t('master.common.formEdit') : t('master.common.formRegister') }) }}</h3>
          <p class="header-subtitle">{{ t('master.destination.dialogSubtitle') }}</p>
        </div>
      </div>
    </template>

    <div class="form-container">
      <el-form :model="form" :rules="rules" ref="formRef" label-position="top" class="compact-form" :disabled="loading">
        <div class="form-section">
          <div class="section-header"><el-icon><Document /></el-icon><span>{{ t('master.common.basicInfo') }}</span></div>
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item :label="t('master.destination.destinationCD')" prop="destination_cd">
                <el-input v-model="form.destination_cd" placeholder="例: DEST001" :disabled="isEdit" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="t('master.destination.customerCD')">
                <el-select v-model="form.customer_cd" :placeholder="t('master.common.select')" filterable clearable class="full-width" :loading="optionsLoading">
                  <el-option v-for="c in customerOptions" :key="c.cd" :label="`${c.cd}｜${c.name}`" :value="c.cd" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item :label="t('master.destination.destinationName')" prop="destination_name">
            <el-input v-model="form.destination_name" :placeholder="t('master.destination.destinationName')" />
          </el-form-item>
        </div>

        <div class="form-section">
          <div class="section-header"><el-icon><Van /></el-icon><span>{{ t('master.destination.shippingInfo') }}</span></div>
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item :label="t('master.destination.carrierCD')">
                <el-select v-model="form.carrier_cd" :placeholder="t('master.common.select')" filterable clearable class="full-width" :loading="optionsLoading">
                  <el-option v-for="c in carrierOptions" :key="c.cd" :label="`${c.cd}｜${c.name}`" :value="c.cd" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item :label="t('master.destination.deliveryLeadTime')">
                <el-input-number v-model="form.delivery_lead_time" :min="0" :max="365" controls-position="right" class="full-width" />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item :label="t('master.destination.issueType')">
                <el-select v-model="form.issue_type" class="full-width">
                  <el-option :label="t('master.destination.issueAuto')" value="自動" /><el-option label="1" value="1" /><el-option label="2" value="2" /><el-option label="3" value="3" /><el-option label="4" value="4" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <div class="form-section">
          <div class="section-header"><el-icon><Phone /></el-icon><span>{{ t('master.common.contact') }}</span></div>
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item :label="t('master.customer.phone')">
                <el-input v-model="form.phone" placeholder="03-1234-5678" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="t('master.customer.address')">
                <el-input v-model="form.address" :placeholder="t('master.customer.address')" />
              </el-form-item>
            </el-col>
          </el-row>
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
import { ref, reactive, watch, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Document, Van, Phone } from '@element-plus/icons-vue'
import { createDestination, updateDestination } from '@/api/master/destinationMaster'
import { getCustomerOptions, getCarrierOptions } from '@/api/options'
import type { DestinationItem, OptionItem } from '@/types/master'

const { t } = useI18n()

const props = withDefaults(defineProps<{ visible: boolean; data?: DestinationItem | null }>(), { visible: false, data: undefined })
const emit = defineEmits(['update:visible', 'refresh'])

const visible = ref(props.visible)
const formRef = ref<FormInstance>()
const form = reactive({ id: undefined as number | undefined, destination_cd: '', destination_name: '', customer_cd: '', carrier_cd: '', delivery_lead_time: 0, issue_type: '自動', phone: '', address: '', status: 1 })

const rules: FormRules = {
  destination_cd: [
    { required: true, message: () => t('master.common.requiredCode'), trigger: 'blur' },
    { pattern: /^[A-Za-z0-9_-]+$/, message: () => t('master.common.codeAlphanumericOnly'), trigger: 'blur' },
  ],
  destination_name: [{ required: true, message: () => t('master.common.requiredName'), trigger: 'blur' }],
}

const customerOptions = ref<OptionItem[]>([])
const carrierOptions = ref<OptionItem[]>([])
const optionsLoading = ref(false)
const loading = ref(false)
const isEdit = computed(() => !!form.id)

function resetForm() { Object.assign(form, { id: undefined, destination_cd: '', destination_name: '', customer_cd: '', carrier_cd: '', delivery_lead_time: 0, issue_type: '自動', phone: '', address: '', status: 1 }) }

async function loadOptions() {
  optionsLoading.value = true
  try { const [c, k] = await Promise.all([getCustomerOptions(), getCarrierOptions()]); customerOptions.value = c; carrierOptions.value = k }
  catch { ElMessage.error(t('master.common.loadError')) }
  finally { optionsLoading.value = false }
}

watch(() => props.visible, (val) => {
  visible.value = val
  if (val) {
    if (props.data) Object.assign(form, { id: props.data.id, destination_cd: props.data.destination_cd ?? '', destination_name: props.data.destination_name ?? '', customer_cd: props.data.customer_cd ?? '', carrier_cd: props.data.carrier_cd ?? '', delivery_lead_time: props.data.delivery_lead_time ?? 0, issue_type: props.data.issue_type ?? '自動', phone: props.data.phone ?? '', address: props.data.address ?? '', status: props.data.status ?? 1 })
    else resetForm()
    loadOptions()
  }
})

async function submitForm() {
  if (!formRef.value) return
  try {
    await formRef.value.validate(); loading.value = true
    const payload: Partial<DestinationItem> = { destination_cd: form.destination_cd, destination_name: form.destination_name, customer_cd: form.customer_cd || undefined, carrier_cd: form.carrier_cd || undefined, delivery_lead_time: form.delivery_lead_time, issue_type: form.issue_type, phone: form.phone || undefined, address: form.address || undefined, status: form.status }
    if (form.id != null) await updateDestination({ ...payload, id: form.id })
    else await createDestination(payload)
    ElMessage.success(form.id ? t('master.common.updateSuccess') : t('master.common.saveSuccess'))
    emit('update:visible', false)
    emit('refresh')
  } catch (e: unknown) {
    if (e !== false) ElMessage.error(t('master.common.saveFailed'))
  }
  finally { loading.value = false }
}

function handleClose() { emit('update:visible', false); resetForm() }
onMounted(() => { if (visible.value) loadOptions() })
</script>

<style scoped>
.destination-dialog :deep(.el-dialog) { border-radius: 14px; overflow: hidden; box-shadow: 0 16px 48px rgba(0,0,0,0.12); }
.destination-dialog :deep(.el-dialog__header) { padding: 0; margin: 0; }
.destination-dialog :deep(.el-dialog__body) { padding: 0; }
.destination-dialog :deep(.el-dialog__footer) { padding: 0; }

.dialog-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 12px 18px; display: flex; align-items: center; gap: 12px; }
.header-icon { width: 40px; height: 40px; background: rgba(255,255,255,0.2); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.3rem; }
.header-title { margin: 0; font-size: 1.1rem; font-weight: 700; color: #fff; }
.header-subtitle { margin: 2px 0 0; font-size: 0.75rem; color: rgba(255,255,255,0.8); }

.form-container { padding: 14px 16px; background: #fafbfc; max-height: 65vh; overflow-y: auto; }
.compact-form :deep(.el-form-item) { margin-bottom: 10px; }
.compact-form :deep(.el-form-item__label) { font-size: 11px; font-weight: 600; color: #374151; padding-bottom: 2px; }
.full-width { width: 100%; }

.form-section { background: #fff; border-radius: 10px; padding: 12px 14px; border: 1px solid #e5e7eb; margin-bottom: 10px; }
.section-header { display: flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 600; color: #667eea; margin-bottom: 10px; padding-bottom: 6px; border-bottom: 1px solid #f0f0f0; }

.dialog-footer { display: flex; justify-content: flex-end; gap: 10px; padding: 10px 16px; background: #fff; border-top: 1px solid #f0f0f0; }
.submit-btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none; border-radius: 8px; font-weight: 600; }

@media (max-width: 620px) {
  .destination-dialog :deep(.el-dialog) { width: 95vw !important; }
  .dialog-header { padding: 10px 14px; }
  .form-container { padding: 12px; }
}
</style>
