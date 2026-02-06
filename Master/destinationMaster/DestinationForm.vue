<!-- 納入先マスタ用フォーム -->
<template>
  <el-dialog v-model="visible" width="650px" :before-close="handleClose" :destroy-on-close="true" :draggable="true"
    :modal="true" :close-on-click-modal="false" class="destination-dialog" transition="dialog-fade-zoom">
    <div class="dialog-title">
      <span class="icon">🚚</span>
      納入先情報の{{ isEdit ? '編集' : '登録' }}
    </div>

    <el-form :model="form" :rules="rules" ref="formRef" label-width="140px" class="dialog-form" :disabled="loading">
      <div class="form-grid">
        <!-- 基本情報セクション -->
        <div class="form-section">
          <h4 class="section-title">
            <el-icon>
              <Document />
            </el-icon>
            基本情報
          </h4>

          <el-form-item label="納入先CD" prop="destination_cd" required>
            <el-input v-model="form.destination_cd" placeholder="例: DEST001" :prefix-icon="Money" maxlength="20"
              show-word-limit />
          </el-form-item>

          <el-form-item label="納入先名" prop="destination_name" required>
            <el-input v-model="form.destination_name" placeholder="納入先の名称を入力" :prefix-icon="Location" maxlength="50"
              show-word-limit />
          </el-form-item>

          <el-form-item label="顧客CD">
            <el-select v-model="form.customer_cd" placeholder="顧客を選択" filterable class="full-width"
              :loading="optionsLoading">
              <el-option v-for="c in customerOptions" :key="c.cd" :label="`${c.cd} | ${c.name}`" :value="c.cd">
                <div class="option-item">
                  <el-icon>
                    <User />
                  </el-icon>
                  <span class="option-label">{{ c.cd }}</span>
                  <span class="option-name">{{ c.name }}</span>
                </div>
              </el-option>
            </el-select>
          </el-form-item>
        </div>

        <!-- 配送情報セクション -->
        <div class="form-section">
          <h4 class="section-title">
            <el-icon>
              <Van />
            </el-icon>
            配送情報
          </h4>

          <el-form-item label="運送便CD">
            <el-select v-model="form.carrier_cd" placeholder="運送会社を選択" filterable class="full-width"
              :loading="optionsLoading">
              <el-option v-for="c in carrierOptions" :key="c.cd" :label="`${c.cd} | ${c.name}`" :value="c.cd">
                <div class="option-item">
                  <el-icon>
                    <Van />
                  </el-icon>
                  <span class="option-label">{{ c.cd }}</span>
                  <span class="option-name">{{ c.name }}</span>
                </div>
              </el-option>
            </el-select>
          </el-form-item>

          <el-form-item label="納入リードタイム">
            <el-input-number v-model="form.delivery_lead_time" :min="0" :max="365" class="lead-time-input">
              <template #suffix>日</template>
            </el-input-number>
          </el-form-item>

          <el-form-item label="発行区分">
            <el-radio-group v-model="form.issue_type" class="issue-radio-group">
              <el-radio-button :value="1">
                <el-tooltip content="自動発行" placement="top">
                  <span>1</span>
                </el-tooltip>
              </el-radio-button>
              <el-radio-button :value="2">
                <el-tooltip content="手動発行" placement="top">
                  <span>2</span>
                </el-tooltip>
              </el-radio-button>
              <el-radio-button :value="3">
                <el-tooltip content="その他" placement="top">
                  <span>3</span>
                </el-tooltip>
              </el-radio-button>
              <el-radio-button :value="4">
                <el-tooltip content="特殊発行" placement="top">
                  <span>4</span>
                </el-tooltip>
              </el-radio-button>
            </el-radio-group>
          </el-form-item>
        </div>

        <!-- 連絡先セクション -->
        <div class="form-section">
          <h4 class="section-title">
            <el-icon>
              <Phone />
            </el-icon>
            連絡先情報
          </h4>

          <el-form-item label="電話番号">
            <el-input v-model="form.phone" placeholder="例: 03-1234-5678" :prefix-icon="Phone" />
          </el-form-item>

          <el-form-item label="住所">
            <el-input v-model="form.address" type="textarea" :rows="3" placeholder="住所を入力" maxlength="200"
              show-word-limit />
          </el-form-item>
        </div>
      </div>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose" :disabled="loading">
          キャンセル
        </el-button>
        <el-button type="primary" @click="submitForm" :loading="loading">
          保存
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { createDestination, updateDestination } from '@/api/master/destinationMaster'
import { getCustomerOptions, getCarrierOptions } from '@/api/options'
import {
  Check,
  Close,
  Van,
  Money,
  Location,
  Document,
  Phone,
  User,
} from '@element-plus/icons-vue'

// 定义组件名称
defineOptions({
  name: 'DestinationFormDialog'
});

// 类型定义
interface CustomerOption {
  cd: string
  name: string
}

interface CarrierOption {
  cd: string
  name: string
}

interface DestinationForm {
  id: number | null
  destination_cd: string
  destination_name: string
  customer_cd: string
  carrier_cd: string
  delivery_lead_time: number
  issue_type: number
  phone: string
  address: string
}

// 状态数据
const customerOptions = ref<CustomerOption[]>([])
const carrierOptions = ref<CarrierOption[]>([])
const optionsLoading = ref(false)
const loading = ref(false)

// Props定义
const props = withDefaults(defineProps<{
  visible: boolean
  data?: any
}>(), {
  visible: false,
  data: () => null,
})

// 发出事件
const emit = defineEmits(['update:visible', 'refresh'])

// 表单引用和数据
const visible = ref(props.visible)
const formRef = ref()
const form = ref<DestinationForm>({
  id: null,
  destination_cd: '',
  destination_name: '',
  customer_cd: '',
  carrier_cd: '',
  delivery_lead_time: 0,
  issue_type: 1,
  phone: '',
  address: '',
})

// 计算属性 - 是否编辑模式
const isEdit = computed(() => !!form.value.id)

// 表单验证规则
const rules = {
  destination_cd: [
    { required: true, message: '納入先CDは必須です', trigger: 'blur' },
    { pattern: /^[A-Za-z0-9_-]+$/, message: '英数字、ハイフン、アンダースコアのみ使用可能です', trigger: 'blur' }
  ],
  destination_name: [
    { required: true, message: '納入先名は必須です', trigger: 'blur' },
    { min: 1, max: 50, message: '50文字以内で入力してください', trigger: 'blur' }
  ],
}

// 监听弹窗显示状态和数据变化
watch(() => props.visible, (val) => {
  visible.value = val
  if (val) {
    if (props.data) {
      form.value = { ...props.data }
    } else {
      resetForm()
    }
    loadOptions()
  }
})

// 加载选项数据
async function loadOptions() {
  if (customerOptions.value.length > 0 && carrierOptions.value.length > 0) return

  optionsLoading.value = true
  try {
    const [customers, carriers] = await Promise.all([
      getCustomerOptions(),
      getCarrierOptions()
    ])
    customerOptions.value = customers
    carrierOptions.value = carriers
  } catch (error) {
    ElMessage.error('マスターデータの読み込みに失敗しました')
  } finally {
    optionsLoading.value = false
  }
}

// 提交表单
async function submitForm() {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    loading.value = true

    const fn = form.value.id ? updateDestination : createDestination
    await fn(form.value)

    ElMessage({
      type: 'success',
      message: `納入先を${form.value.id ? '更新' : '登録'}しました`,
      duration: 3000
    })

    emit('update:visible', false)
    emit('refresh')
  } catch (error: any) {
    if (error?.message) {
      ElMessage.error(error.message)
    }
  } finally {
    loading.value = false
  }
}

// 关闭弹窗
function handleClose() {
  emit('update:visible', false)
  resetForm()
}

// 重置表单
function resetForm() {
  form.value = {
    id: null,
    destination_cd: '',
    destination_name: '',
    customer_cd: '',
    carrier_cd: '',
    delivery_lead_time: 0,
    issue_type: 1,
    phone: '',
    address: '',
  }
}

// 页面初始化
onMounted(async () => {
  if (visible.value) {
    loadOptions()
  }
})

// 对外暴露方法
defineExpose({ resetForm })
</script>

<style scoped>
.destination-dialog :deep(.el-dialog__body) {
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
}

.dialog-title .icon {
  margin-right: 12px;
  font-size: 24px;
}

.dialog-form {
  padding: 24px;
}

.form-grid {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-section {
  background-color: #fafafa;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  border: 1px solid #f0f0f0;
}

.form-section:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border-color: #e0e0e0;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #409EFF;
  margin: 0 0 16px 0;
  padding-bottom: 12px;
  border-bottom: 1px solid #eaeaea;
}

/* 选项样式 */
.option-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.option-label {
  font-family: monospace;
  font-weight: 500;
  color: #409EFF;
}

.option-name {
  color: #606266;
}

/* 表单控件 */
.full-width {
  width: 100%;
}

.lead-time-input {
  width: 180px;
}

.issue-radio-group {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

/* 底部按钮 */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 10px;
}

/* 自定义动画（淡入+缩放） */
@keyframes fadeZoomIn {
  0% {
    opacity: 0;
    transform: scale(0.95);
  }

  100% {
    opacity: 1;
    transform: scale(1);
  }
}

:deep(.dialog-fade-zoom) {
  animation: fadeZoomIn 0.3s ease-out;
}

/* 响应式样式 */
@media (max-width: 768px) {
  .dialog-title {
    font-size: 18px;
    padding: 16px 20px 10px;
  }

  .dialog-form {
    padding: 16px;
  }

  .form-section {
    padding: 16px;
  }

  .lead-time-input {
    width: 100%;
  }

  .issue-radio-group {
    justify-content: space-between;
  }
}
</style>
