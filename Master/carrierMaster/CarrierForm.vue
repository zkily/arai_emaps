<!-- 運送便マスタ用フォーム -->
<template>
  <el-dialog v-model="visible" width="600px" :before-close="handleClose" :destroy-on-close="true" draggable
    class="carrier-dialog">
    <!-- 自定义标题 -->
    <div class="dialog-title">
      <el-icon class="dialog-icon">🚚</el-icon>
      <span>運送便 登録・編集</span>
    </div>

    <el-form :model="form" :rules="rules" ref="formRef" label-width="120px" class="form-body">
      <div class="form-grid">
        <!-- 基本信息 -->
        <div class="form-section">
          <h4 class="section-title">基本情報</h4>
          <el-form-item label="運送便CD" prop="carrier_cd">
            <el-input v-model="form.carrier_cd" placeholder="例：U01" />
          </el-form-item>
          <el-form-item label="運送便名称" prop="carrier_name">
            <el-input v-model="form.carrier_name" />
          </el-form-item>
        </div>
        <!-- 联系方式 -->
        <div class="form-section">
          <h4 class="section-title">連絡先</h4>
          <el-form-item label="連絡人">
            <el-input v-model="form.contact_person" />
          </el-form-item>
          <el-form-item label="電話番号">
            <el-input v-model="form.phone" />
          </el-form-item>
        </div>
        <!-- 其他信息 -->
        <div class="form-section">
          <h4 class="section-title">その他</h4>
          <el-form-item label="出荷時間">
            <el-time-picker v-model="form.shipping_time" placeholder="出荷時間を選択" format="HH:mm" value-format="HH:mm:ss"
              arrow-control />
          </el-form-item>
          <el-form-item label="報告No">
            <el-input v-model="form.report_no" />
          </el-form-item>
          <el-form-item label="備考">
            <el-input v-model="form.note" type="textarea" :rows="2" />
          </el-form-item>
        </div>
      </div>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">キャンセル</el-button>
        <el-button type="primary" @click="submitForm">保存</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { createCarrier, updateCarrier } from '@/api/master/carrierMaster'

const props = withDefaults(defineProps<{
  visible: boolean
  data?: any
}>(), {
  visible: false,
  data: () => null
})

const emit = defineEmits(['update:visible', 'refresh'])

const visible = ref(false)
const formRef = ref()

// 表单初始值
const form = ref({
  id: null,
  carrier_cd: '',
  carrier_name: '',
  contact_person: '',
  phone: '',
  shipping_time: '',
  report_no: '',
  note: ''
})

// 校验规则
const rules = {
  carrier_cd: [{ required: true, message: '運送便CDは必須です', trigger: 'blur' }],
  carrier_name: [{ required: true, message: '運送便名称は必須です', trigger: 'blur' }]
}

// 监听 visible + 回显数据
watch(() => props.visible, (val) => {
  visible.value = val
  if (val && props.data) {
    form.value = { ...props.data }
  } else {
    resetForm()
  }
})

// 表单提交
function submitForm() {
  formRef.value?.validate(async (valid: boolean) => {
    if (!valid) return
    const fn = form.value.id ? updateCarrier : createCarrier
    await fn(form.value)
    ElMessage.success('保存しました')
    emit('update:visible', false)
    emit('refresh')
  })
}

// 关闭表单
function handleClose() {
  emit('update:visible', false)
}

// 重置表单
function resetForm() {
  form.value = {
    id: null,
    carrier_cd: '',
    carrier_name: '',
    contact_person: '',
    phone: '',
    shipping_time: '',
    report_no: '',
    note: ''
  }
}
</script>

<style scoped>
.carrier-dialog :deep(.el-dialog__body) {
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

.dialog-icon {
  font-size: 24px;
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
