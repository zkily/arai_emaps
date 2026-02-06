<template>
  <el-dialog v-model="visible" width="700px" :close-on-click-modal="false" class="supplier-dialog">
    <div class="dialog-title">
      <span class="icon">🔧</span>
      <span>{{ dialogTitle }}</span>
    </div>
    <el-form :model="form" :rules="rules" ref="formRef" label-width="120px" class="form-body">
      <div class="form-grid">
        <!-- 基本信息 -->
        <div class="form-section">
          <h4 class="section-title">基本情報</h4>
          <el-form-item label="仕入先CD" prop="supplier_cd">
            <el-input v-model="form.supplier_cd" maxlength="20" />
          </el-form-item>
          <el-form-item label="仕入先名" prop="supplier_name">
            <el-input v-model="form.supplier_name" maxlength="100" />
          </el-form-item>
          <el-form-item label="仕入先カナ">
            <el-input v-model="form.supplier_kana" maxlength="100" />
          </el-form-item>
        </div>
        <!-- 联系方式 -->
        <div class="form-section">
          <h4 class="section-title">連絡先</h4>
          <el-form-item label="担当者">
            <el-input v-model="form.contact_person" maxlength="100" />
          </el-form-item>
          <el-form-item label="電話番号">
            <el-input v-model="form.phone" maxlength="20" />
          </el-form-item>
          <el-form-item label="FAX番号">
            <el-input v-model="form.fax" maxlength="20" />
          </el-form-item>
          <el-form-item label="メールアドレス">
            <el-input v-model="form.email" maxlength="100" />
          </el-form-item>
        </div>
        <!-- 地址 -->
        <div class="form-section">
          <h4 class="section-title">住所</h4>
          <el-form-item label="郵便番号">
            <el-input v-model="form.postal_code" maxlength="10" />
          </el-form-item>
          <el-form-item label="住所1">
            <el-input v-model="form.address1" maxlength="200" />
          </el-form-item>
          <el-form-item label="住所2">
            <el-input v-model="form.address2" maxlength="200" />
          </el-form-item>
        </div>
        <!-- 财务信息 -->
        <div class="form-section">
          <h4 class="section-title">支払・通貨</h4>
          <el-form-item label="支払条件">
            <el-input v-model="form.payment_terms" maxlength="50" />
          </el-form-item>
          <el-form-item label="通貨">
            <el-input v-model="form.currency" maxlength="10" placeholder="例：JPY, USD" />
          </el-form-item>
        </div>
        <!-- 备注 -->
        <div class="form-section">
          <h4 class="section-title">備考</h4>
          <el-form-item label="備考">
            <el-input type="textarea" v-model="form.remarks" :rows="3" />
          </el-form-item>
        </div>
      </div>
    </el-form>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visible = false">キャンセル</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const props = defineProps<{
  visible: boolean
  editData: any | null
}>()
const emit = defineEmits(['update:visible', 'saved'])

const visible = ref(props.visible)
watch(() => props.visible, val => visible.value = val)
watch(visible, val => emit('update:visible', val))

const form = reactive<any>({
  supplier_cd: '',
  supplier_name: '',
  supplier_kana: '',
  contact_person: '',
  phone: '',
  fax: '',
  email: '',
  postal_code: '',
  address1: '',
  address2: '',
  payment_terms: '',
  currency: 'JPY',
  remarks: ''
})

const rules = {
  supplier_cd: [{ required: true, message: '必須', trigger: 'blur' }],
  supplier_name: [{ required: true, message: '必須', trigger: 'blur' }]
}

const formRef = ref()

const dialogTitle = computed(() => props.editData ? '仕入先編集' : '仕入先追加')

watch(() => props.editData, val => {
  if (val) Object.assign(form, val)
  else Object.assign(form, {
    supplier_cd: '',
    supplier_name: '',
    supplier_kana: '',
    contact_person: '',
    phone: '',
    fax: '',
    email: '',
    postal_code: '',
    address1: '',
    address2: '',
    payment_terms: '',
    currency: 'JPY',
    remarks: ''
  })
})

const handleSave = () => {
  formRef.value.validate(async (valid: boolean) => {
    if (!valid) return
    if (props.editData?.id) {
      await request.put(`/api/master/suppliers/${props.editData.id}`, form)
      ElMessage.success('更新しました')
    } else {
      await request.post('/api/master/suppliers', form)
      ElMessage.success('登録しました')
    }
    emit('saved')
    visible.value = false
  })
}
</script>

<style scoped>
.supplier-dialog :deep(.el-dialog__body) {
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

.form-body {
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

  .form-body {
    padding: 12px 2px 2px 2px;
  }
}
</style>
