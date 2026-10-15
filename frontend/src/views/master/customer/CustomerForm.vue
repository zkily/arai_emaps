<template>
  <el-dialog
    v-model="visible"
    width="560px"
    :before-close="handleClose"
    destroy-on-close
    align-center
    :show-close="false"
    :close-on-click-modal="false"
    class="customer-dialog pb-std"
  >
    <template #header>
      <div class="dialog-header" :class="isEdit ? 'dialog-header--edit' : 'dialog-header--new'">
        <div class="header-icon">
          <el-icon :size="20"><User /></el-icon>
        </div>
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
        <el-button class="dlg-btn dlg-btn--cancel" @click="handleClose" :disabled="loading">
          {{ t('master.common.cancel') }}
        </el-button>
        <el-button class="dlg-btn dlg-btn--save" :loading="loading" @click="submitForm">
          {{ t('master.common.save') }}
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
.customer-dialog :deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 50px rgba(15, 23, 42, 0.22);
}
.customer-dialog :deep(.el-dialog__header) {
  padding: 0;
  margin: 0;
}
.customer-dialog :deep(.el-dialog__body) {
  padding: 0;
}
.customer-dialog :deep(.el-dialog__footer) {
  padding: 0;
}

.dialog-header {
  padding: 12px 18px;
  display: flex;
  align-items: center;
  gap: 12px;
  background: linear-gradient(125deg, #831843 0%, #9d174d 40%, #db2777 100%);
}
.dialog-header--edit {
  background: linear-gradient(125deg, #9d174d 0%, #be185d 45%, #db2777 100%);
}
.dialog-header--new {
  background: linear-gradient(125deg, #047857 0%, #059669 45%, #10b981 100%);
}
.header-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.35);
  background: linear-gradient(150deg, rgba(255, 255, 255, 0.28), rgba(255, 255, 255, 0.1));
}
.header-title {
  margin: 0;
  font-size: 15px;
  font-weight: 800;
  color: #fff;
}
.header-subtitle {
  margin: 2px 0 0;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.86);
}

.form-container {
  padding: 14px 16px;
  background: linear-gradient(180deg, #fdf2f8 0%, #f8fafc 100%);
  max-height: 65vh;
  overflow-y: auto;
}
.compact-form :deep(.el-form-item) {
  margin-bottom: 10px;
}
.compact-form :deep(.el-form-item__label) {
  font-size: 11px;
  font-weight: 600;
  color: #374151;
  padding-bottom: 2px;
}
.full-width {
  width: 100%;
}

.form-section {
  background: #fff;
  border-radius: 10px;
  padding: 12px 14px;
  border: 1px solid #fbcfe8;
  margin-bottom: 10px;
}
.section-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 700;
  color: #be185d;
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid #fce7f3;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 10px 16px;
  background: #fff;
  border-top: 1px solid #fce7f3;
}
.dlg-btn {
  border-radius: 999px;
  font-weight: 700;
  font-size: 12px;
  padding: 7px 16px;
  height: auto;
}
.dlg-btn--cancel {
  background: #fff;
  border: 1px solid #e2e8f0;
  color: #64748b;
}
.dlg-btn--save {
  background: linear-gradient(135deg, #db2777, #9d174d);
  border: none;
  color: #fff;
}

@media (max-width: 620px) {
  .customer-dialog :deep(.el-dialog) {
    width: 95vw !important;
  }
  .dialog-header {
    padding: 10px 14px;
  }
  .form-container {
    padding: 12px;
  }
}
</style>
