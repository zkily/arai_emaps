<!-- 倉庫マスタ用フォーム -->
<template>
  <el-dialog v-model="visible" width="800px" :before-close="handleClose" :destroy-on-close="true" draggable
    class="warehouse-dialog">
    <!-- 自定义标题 -->
    <div class="dialog-title">
      <el-icon class="dialog-icon">🏢</el-icon>
      <span>倉庫 登録・編集</span>
    </div>

    <el-form :model="form" :rules="rules" ref="formRef" label-width="140px" class="form-body">
      <div class="form-grid">
        <!-- 基本情報 -->
        <div class="form-section">
          <h4 class="section-title">基本情報</h4>
          <el-form-item label="倉庫コード" prop="warehouse_code">
            <el-input v-model="form.warehouse_code" placeholder="例：WH001" />
          </el-form-item>
          <el-form-item label="倉庫名称" prop="warehouse_name">
            <el-input v-model="form.warehouse_name" placeholder="倉庫名を入力" />
          </el-form-item>
          <el-form-item label="倉庫タイプ" prop="warehouse_type">
            <el-select v-model="form.warehouse_type" placeholder="タイプを選択" class="full-width">
              <el-option label="内部倉庫" value="internal">
                <el-tag type="primary" size="small">内部</el-tag>
                <span class="option-desc">自社管理倉庫</span>
              </el-option>
              <el-option label="外注倉庫" value="outsourcing">
                <el-tag type="warning" size="small">外注</el-tag>
                <span class="option-desc">外部委託倉庫</span>
              </el-option>
              <el-option label="一時倉庫" value="temporary">
                <el-tag type="info" size="small">一時</el-tag>
                <span class="option-desc">臨時保管倉庫</span>
              </el-option>
              <el-option label="特殊倉庫" value="special">
                <el-tag type="danger" size="small">特殊</el-tag>
                <span class="option-desc">特殊用途倉庫</span>
              </el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="状態" prop="status">
            <el-select v-model="form.status" placeholder="状態を選択" class="full-width">
              <el-option label="有効" value="active">
                <el-tag type="success" size="small">有効</el-tag>
                <span class="option-desc">利用可能</span>
              </el-option>
              <el-option label="無効" value="inactive">
                <el-tag type="info" size="small">無効</el-tag>
                <span class="option-desc">利用停止</span>
              </el-option>
              <el-option label="メンテナンス" value="maintenance">
                <el-tag type="warning" size="small">メンテナンス</el-tag>
                <span class="option-desc">保守中</span>
              </el-option>
            </el-select>
          </el-form-item>
        </div>

        <!-- 所在地・容量情報 -->
        <div class="form-section">
          <h4 class="section-title">所在地・容量</h4>
          <el-form-item label="所在地" prop="location">
            <el-input v-model="form.location" placeholder="住所を入力" />
          </el-form-item>
          <el-form-item label="容量" prop="capacity">
            <el-input-number v-model="form.capacity" :min="0" :precision="2" placeholder="容量" class="full-width" />
          </el-form-item>
          <el-form-item label="現在使用量">
            <el-input-number v-model="form.current_usage" :min="0" :precision="2" placeholder="使用量" class="full-width" />
          </el-form-item>
        </div>

        <!-- 管理者情報 -->
        <div class="form-section">
          <h4 class="section-title">管理者情報</h4>
          <el-form-item label="管理者名" prop="manager_name">
            <el-input v-model="form.manager_name" placeholder="管理者名を入力" />
          </el-form-item>
          <el-form-item label="連絡先" prop="manager_contact">
            <el-input v-model="form.manager_contact" placeholder="電話番号・メールアドレス" />
          </el-form-item>
        </div>

        <!-- 外注倉庫用追加情報 -->
        <div class="form-section" v-if="form.warehouse_type === 'outsourcing'">
          <h4 class="section-title">外注情報</h4>
          <el-form-item label="会社名">
            <el-input v-model="form.company_name" placeholder="外注会社名" />
          </el-form-item>
          <el-form-item label="契約期間">
            <div class="date-range">
              <el-date-picker
                v-model="form.contract_start"
                type="date"
                placeholder="契約開始日"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                class="date-input"
              />
              <span class="date-separator">〜</span>
              <el-date-picker
                v-model="form.contract_end"
                type="date"
                placeholder="契約終了日"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                class="date-input"
              />
            </div>
          </el-form-item>
          <el-form-item label="月額費用">
            <el-input-number v-model="form.monthly_cost" :min="0" :precision="0" placeholder="月額費用" class="full-width" />
          </el-form-item>
        </div>

        <!-- 備考 -->
        <div class="form-section">
          <h4 class="section-title">その他</h4>
          <el-form-item label="備考">
            <el-input v-model="form.notes" type="textarea" :rows="3" placeholder="備考を入力" />
          </el-form-item>
        </div>
      </div>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">キャンセル</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">保存</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { createWarehouse, updateWarehouse, type Warehouse } from '@/api/master/warehouseMaster'

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
const submitting = ref(false)

// 表单初始値
const form = ref<Warehouse>({
  id: undefined,
  warehouse_code: '',
  warehouse_name: '',
  warehouse_type: 'internal',
  status: 'active',
  location: '',
  capacity: 0,
  current_usage: 0,
  manager_name: '',
  manager_contact: '',
  company_name: '',
  contract_start: '',
  contract_end: '',
  monthly_cost: 0,
  notes: ''
})

// 校验规则
const rules = {
  warehouse_code: [{ required: true, message: '倉庫コードは必須です', trigger: 'blur' }],
  warehouse_name: [{ required: true, message: '倉庫名称は必須です', trigger: 'blur' }],
  warehouse_type: [{ required: true, message: '倉庫タイプは必須です', trigger: 'change' }],
  status: [{ required: true, message: '状態は必須です', trigger: 'change' }],
  location: [{ required: true, message: '所在地は必須です', trigger: 'blur' }],
  capacity: [{ required: true, message: '容量は必須です', trigger: 'blur' }],
  manager_name: [{ required: true, message: '管理者名は必須です', trigger: 'blur' }],
  manager_contact: [{ required: true, message: '連絡先は必須です', trigger: 'blur' }]
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

    submitting.value = true
    try {
      const fn = form.value.id ? updateWarehouse : createWarehouse
      await fn(form.value)
      ElMessage.success('保存しました')
      emit('update:visible', false)
      emit('refresh')
    } catch (error) {
      ElMessage.error('保存に失敗しました')
    } finally {
      submitting.value = false
    }
  })
}

// 关闭表单
function handleClose() {
  emit('update:visible', false)
}

// 重置表单
function resetForm() {
  form.value = {
    id: undefined,
    warehouse_code: '',
    warehouse_name: '',
    warehouse_type: 'internal',
    status: 'active',
    location: '',
    capacity: 0,
    current_usage: 0,
    manager_name: '',
    manager_contact: '',
    company_name: '',
    contract_start: '',
    contract_end: '',
    monthly_cost: 0,
    notes: ''
  }
}
</script>

<style scoped>
.warehouse-dialog :deep(.el-dialog__body) {
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
  gap: 8px;
}

.dialog-icon {
  font-size: 24px;
}

.form-body {
  padding: 24px;
  max-height: 70vh;
  overflow-y: auto;
}

.form-grid {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-section {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  background: #fafafa;
}

.section-title {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
  border-bottom: 2px solid #3498db;
  padding-bottom: 8px;
}

.full-width {
  width: 100%;
}

.option-desc {
  margin-left: 8px;
  font-size: 12px;
  color: #999;
}

.date-range {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.date-input {
  flex: 1;
}

.date-separator {
  color: #666;
  font-weight: 500;
}

.dialog-footer {
  padding: 16px 24px;
  border-top: 1px solid #ebeef5;
  background: #f8f9fa;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .warehouse-dialog {
    width: 95% !important;
  }

  .form-body {
    padding: 16px;
  }

  .date-range {
    flex-direction: column;
    align-items: stretch;
  }

  .date-separator {
    text-align: center;
  }
}

/* 表单项样式优化 */
.form-section :deep(.el-form-item) {
  margin-bottom: 18px;
}

.form-section :deep(.el-form-item__label) {
  font-weight: 500;
  color: #555;
}

.form-section :deep(.el-input__wrapper) {
  border-radius: 6px;
}

.form-section :deep(.el-select) {
  width: 100%;
}

.form-section :deep(.el-input-number) {
  width: 100%;
}

.form-section :deep(.el-textarea__inner) {
  border-radius: 6px;
}
</style>
