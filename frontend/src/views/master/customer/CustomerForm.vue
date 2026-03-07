<template>
  <el-dialog v-model="visible" width="560px" :before-close="handleClose" destroy-on-close :close-on-click-modal="false" class="customer-dialog">
    <template #header>
      <div class="dialog-header">
        <div class="header-icon">👤</div>
        <div class="header-text">
          <h3 class="header-title">{{ t('master.customer.dialogTitle', { mode: isEdit ? t('master.common.formEdit') : t('master.common.formRegister') }) }}</h3>
          <p class="header-subtitle">{{ t('master.customer.dialogSubtitle') }}</p>
        </div>
      </div>
    </template>

    <div class="form-container">
      <el-form :model="form" :rules="rules" ref="formRef" label-position="top" class="compact-form" :disabled="loading">
        <div class="form-section">
          <div class="section-header"><el-icon><User /></el-icon><span>{{ t('master.common.basicInfo') }}</span></div>
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item :label="t('master.customer.customerCD')" prop="customer_cd">
                <el-input v-model="form.customer_cd" placeholder="例: C001" :disabled="isEdit" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="t('master.customer.type')">
                <el-select v-model="form.customer_type" :placeholder="t('master.common.select')" clearable class="full-width">
                  <el-option :label="t('master.customer.typeCorp')" value="法人" /><el-option :label="t('master.customer.typePerson')" value="個人" /><el-option :label="t('master.customer.typeAgency')" value="代理店" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item :label="t('master.customer.customerName')" prop="customer_name">
            <el-input v-model="form.customer_name" :placeholder="t('master.customer.customerName')" />
          </el-form-item>
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
import { ref, reactive, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { User, Phone } from '@element-plus/icons-vue'
import { createCustomer, updateCustomer } from '@/api/master/customerMaster'
import type { CustomerItem } from '@/types/master'

const { t } = useI18n()

const props = withDefaults(defineProps<{ visible: boolean; data?: CustomerItem | null }>(), { visible: false, data: undefined })
const emit = defineEmits(['update:visible', 'refresh'])

const visible = ref(props.visible)
const formRef = ref<FormInstance>()
const form = reactive({
  id: undefined as number | undefined,
  customer_cd: '',
  customer_name: '',
  phone: '',
  address: '',
  customer_type: '',
  status: 1,
})

const rules: FormRules = {
  customer_cd: [{ required: true, message: () => t('master.common.requiredCode'), trigger: 'blur' }],
  customer_name: [{ required: true, message: () => t('master.common.requiredName'), trigger: 'blur' }],
}

const loading = ref(false)
const isEdit = computed(() => !!form.id)

function resetForm() {
  Object.assign(form, {
    id: undefined,
    customer_cd: '',
    customer_name: '',
    phone: '',
    address: '',
    customer_type: '',
    status: 1,
  })
}

watch(() => props.visible, (val) => {
  visible.value = val
  if (val) {
    if (props.data) {
      Object.assign(form, {
        id: props.data.id,
        customer_cd: props.data.customer_cd ?? '',
        customer_name: props.data.customer_name ?? '',
        phone: props.data.phone ?? '',
        address: props.data.address ?? '',
        customer_type: props.data.customer_type ?? '',
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
    const payload: Partial<CustomerItem> = {
      customer_cd: form.customer_cd,
      customer_name: form.customer_name,
      phone: form.phone || undefined,
      address: form.address || undefined,
      customer_type: form.customer_type || undefined,
      status: form.status,
    }
    if (form.id != null) {
      await updateCustomer({ ...payload, id: form.id })
    } else {
      await createCustomer(payload)
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
.customer-dialog :deep(.el-dialog) { border-radius: 14px; overflow: hidden; box-shadow: 0 16px 48px rgba(0,0,0,0.12); }
.customer-dialog :deep(.el-dialog__header) { padding: 0; margin: 0; }
.customer-dialog :deep(.el-dialog__body) { padding: 0; }
.customer-dialog :deep(.el-dialog__footer) { padding: 0; }

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
  .customer-dialog :deep(.el-dialog) { width: 95vw !important; }
  .dialog-header { padding: 10px 14px; }
  .form-container { padding: 12px; }
}
</style>
