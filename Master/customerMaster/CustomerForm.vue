<!-- 顧客マスタ用フォーム -->
<template>
  <el-dialog v-model="visible" width="500px" :before-close="handleClose" :show-close="false" class="customer-dialog"
    :draggable="true" :modal="true" :close-on-click-modal="false" :destroy-on-close="true"
    transition="dialog-fade-zoom">
    <div class="dialog-title">
      <span class="icon">📋</span>
      顧客情報の登録・編集
    </div>

    <el-form :model="form" :rules="rules" ref="formRef" label-width="100px" class="dialog-form">
      <div class="form-grid">
        <div class="form-section">
          <h4 class="section-title">基本情報</h4>
          <el-form-item label="顧客CD" prop="customer_cd">
            <el-input v-model="form.customer_cd" placeholder="例：C01" />
          </el-form-item>
          <el-form-item label="顧客名" prop="customer_name">
            <el-input v-model="form.customer_name" />
          </el-form-item>
        </div>
        <div class="form-section">
          <h4 class="section-title">連絡先</h4>
          <el-form-item label="電話番号">
            <el-input v-model="form.phone" />
          </el-form-item>
          <el-form-item label="住所">
            <el-input v-model="form.address" />
          </el-form-item>
        </div>
        <div class="form-section">
          <h4 class="section-title">顧客種別</h4>
          <el-form-item label="顧客種別">
            <el-select v-model="form.customer_type" placeholder="選択してください">
              <el-option label="法人" value="法人" />
              <el-option label="個人" value="個人" />
              <el-option label="代理店" value="代理店" />
            </el-select>
          </el-form-item>
        </div>
      </div>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">キャンセル</el-button>
        <el-button type="primary" :loading="loading" @click="submitForm">保存</el-button>
      </div>
    </template>
  </el-dialog>
</template>
<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { createCustomer, updateCustomer } from '@/api/master/customerMaster'
import type { Customer } from '@/types/master'

const props = withDefaults(defineProps<{ visible: boolean, data?: Customer | null }>(), {
  visible: false,
  data: null,
})
const emit = defineEmits(['update:visible', 'refresh'])
const visible = ref(props.visible)
const loading = ref(false)
const formRef = ref()
const form = ref<Partial<Customer>>({
  customer_cd: '',
  customer_name: '',
  customer_type: 'corporate',
  phone: '',
  address: '',
})

const rules = {
  customer_cd: [{ required: true, message: '顧客CDは必須です', trigger: 'blur' }],
  customer_name: [{ required: true, message: '顧客名は必須です', trigger: 'blur' }],
}

watch(() => props.visible, (val) => {
  visible.value = val
  if (val && props.data) form.value = { ...props.data }
  else resetForm()
})

function resetForm() {
  form.value = {
    customer_cd: '',
    customer_name: '',
    customer_type: 'corporate',
    phone: '',
    address: '',
  }
}
function handleClose() {
  emit('update:visible', false)
  resetForm()
}

async function submitForm() {
  await formRef.value?.validate(async (valid: boolean) => {
    if (!valid) return
    loading.value = true
    const fn = form.value.id ? updateCustomer : createCustomer
    await fn(form.value as Customer)
    ElMessage.success('保存しました')
    emit('update:visible', false)
    emit('refresh')
    loading.value = false
  })
}

defineExpose({ resetForm })
</script>
<style scoped>
.customer-dialog :deep(.el-dialog__body) {
  padding-top: 0;
}

.dialog-title {
  font-size: 22px;
  font-weight: bold;
  color: #2c3e50;
  padding: 20px 24px 12px;
  border-bottom: 1px solid #ebeef5;
  background: linear-gradient(to right, #e6f7ff, #ffffff);
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.dialog-title .icon {
  margin-right: 8px;
  font-size: 22px;
}

.dialog-form {
  padding: 24px 8px 8px 8px;
}

.form-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
}

.form-section {
  flex: 1 1 220px;
  min-width: 220px;
  background: #fafafa;
  border-radius: 12px;
  padding: 18px 16px 10px 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
  margin-bottom: 12px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #409EFF;
  margin: 0 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid #eaeaea;
}

.dialog-footer {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding-top: 10px;
}

@media (max-width: 768px) {
  .form-grid {
    flex-direction: column;
    gap: 10px;
  }

  .form-section {
    min-width: 0;
    padding: 12px 8px 8px 8px;
  }

  .dialog-title {
    font-size: 18px;
    padding: 14px 10px 8px 10px;
  }

  .dialog-form {
    padding: 12px 2px 2px 2px;
  }
}
</style>
