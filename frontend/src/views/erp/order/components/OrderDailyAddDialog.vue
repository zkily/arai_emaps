<template>
  <el-dialog v-model="visible" width="560px" :close-on-click-modal="false" class="modern-order-dialog"
    :show-close="false">
    <!-- 自定义头部 -->
    <template #header>
      <div class="dialog-header">
        <div class="header-left">
          <div class="header-icon">
            <el-icon>
              <Plus />
            </el-icon>
          </div>
          <div class="header-content">
            <h3 class="dialog-title">新規受注追加(試作品・補給品等)</h3>
          </div>
        </div>
        <el-button class="close-btn" circle size="small" @click="visible = false">
          <el-icon>
            <Close />
          </el-icon>
        </el-button>
      </div>
    </template>

    <!-- 表单内容 -->
    <div class="dialog-content">
      <el-form :model="form" label-width="100px" :rules="rules" ref="formRef" class="modern-form">
        <!-- 日期信息卡片 -->
        <div class="form-section">
          <div class="section-header">
            <el-icon class="section-icon">
              <Calendar />
            </el-icon>
            <span class="section-title">日付情報</span>
          </div>
          <div class="section-content">
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="出荷日" prop="date">
                  <el-date-picker v-model="form.date" type="date" value-format="YYYY-MM-DD" format="YYYY/MM/DD"
                    @change="onDateChange" style="width: 100%" placeholder="出荷日を選択" class="modern-date-picker" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="納入日" prop="delivery_date">
                  <el-date-picker v-model="form.delivery_date" type="date" value-format="YYYY-MM-DD" format="YYYY/MM/DD"
                    style="width: 100%" placeholder="納入日を選択" clearable @change="handleDeliveryDateChange"
                    class="modern-date-picker" />
                </el-form-item>
              </el-col>
            </el-row>
          </div>
        </div>

        <!-- 基本情報卡片 -->
        <div class="form-section">
          <div class="section-header">
            <el-icon class="section-icon">
              <Shop />
            </el-icon>
            <span class="section-title">基本情報</span>
          </div>
          <div class="section-content">
            <el-form-item label="納入先" prop="destination_cd">
              <el-select v-model="form.destination_cd" @change="onDestinationChange" filterable style="width: 100%"
                placeholder="納入先を選択" class="modern-select">
                <el-option v-for="item in destinationOptions" :key="item.cd" :label="`${item.cd} | ${item.name}`"
                  :value="item.cd" />
              </el-select>
            </el-form-item>

            <el-form-item label="製品" prop="product_cd">
              <el-select v-model="form.product_cd" @change="onProductChange" filterable style="width: 100%"
                placeholder="製品を選択" class="modern-select">
                <el-option v-for="item in filteredProductOptions" :key="item.product_cd"
                  :label="`${item.product_cd} | ${item.product_name}`" :value="item.product_cd" />
              </el-select>
            </el-form-item>

            <el-form-item label="製品タイプ" prop="product_type">
              <el-select v-model="form.product_type" style="width: 100%" placeholder="製品タイプを選択" class="modern-select"
                @change="onProductTypeChange">
                <el-option label="量産品" value="量産品">
                  <div class="option-item">
                    <el-icon>
                      <Box />
                    </el-icon>
                    <span>量産品</span>
                  </div>
                </el-option>
                <el-option label="別注品" value="別注品">
                  <div class="option-item">
                    <el-icon>
                      <Tools />
                    </el-icon>
                    <span>別注品</span>
                  </div>
                </el-option>
                <el-option label="試作品" value="試作品">
                  <div class="option-item">
                    <el-icon>
                      <Operation />
                    </el-icon>
                    <span>試作品</span>
                  </div>
                </el-option>
                <el-option label="補給品" value="補給品">
                  <div class="option-item">
                    <el-icon>
                      <RefreshRight />
                    </el-icon>
                    <span>補給品</span>
                  </div>
                </el-option>
                <el-option label="サンプル品" value="サンプル品">
                  <div class="option-item">
                    <el-icon>
                      <DataAnalysis />
                    </el-icon>
                    <span>サンプル品</span>
                  </div>
                </el-option>
                <el-option label="返却品" value="返却品">
                  <div class="option-item">
                    <el-icon>
                      <RefreshLeft />
                    </el-icon>
                    <span>返却品</span>
                  </div>
                </el-option>
                <el-option label="代替品" value="代替品">
                  <div class="option-item">
                    <el-icon>
                      <Switch />
                    </el-icon>
                    <span>代替品</span>
                  </div>
                </el-option>
                <el-option label="その他" value="その他">
                  <div class="option-item">
                    <el-icon>
                      <More />
                    </el-icon>
                    <span>その他</span>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
          </div>
        </div>

        <!-- 数量情報卡片 -->
        <div class="form-section">
          <div class="section-header">
            <el-icon class="section-icon">
              <DataLine />
            </el-icon>
            <span class="section-title">数量情報</span>
          </div>
          <div class="section-content">
            <!-- 第一行：入数和確定箱数 -->
            <el-row :gutter="16" class="input-row">
              <el-col :xs="24" :sm="12" :md="12">
                <el-form-item label="入数" prop="unit_per_box" class="number-form-item">
                  <el-input v-model="form.unit_per_box" type="text" placeholder="入数を入力"
                    @input="(value) => handleNumericInput(value, 'unit_per_box')" class="modern-input number-input" />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12" :md="12">
                <el-form-item label="箱数" prop="confirmed_boxes" class="number-form-item">
                  <el-input v-model="form.confirmed_boxes" type="text" placeholder="箱数を入力" @input="handleBoxesInput"
                    class="modern-input number-input" />
                </el-form-item>
              </el-col>
            </el-row>

            <!-- 第二行：確定本数（全宽） -->
            <el-row class="input-row">
              <el-col :span="24">
                <el-form-item label="確定本数" prop="confirmed_units" class="number-form-item calculated-form-item">
                  <el-input v-model="form.confirmed_units" type="text" placeholder="自動計算 (本)"
                    class="modern-input calculated-field number-input" readonly />
                </el-form-item>
              </el-col>
            </el-row>

            <div class="calculation-hint">
              <el-icon>
                <InfoFilled />
              </el-icon>
              <span>確定本数は入数×確定箱数で自動計算されます</span>
            </div>
          </div>
        </div>
      </el-form>
    </div>

    <!-- 自定义底部 -->
    <template #footer>
      <div class="dialog-footer">
        <el-button class="cancel-btn" @click="visible = false">
          <el-icon>
            <Close />
          </el-icon>
          キャンセル
        </el-button>
        <el-button type="primary" class="save-btn" @click="handleSave" :loading="saving">
          <el-icon v-if="!saving">
            <Check />
          </el-icon>
          <el-icon v-else>
            <Loading />
          </el-icon>
          {{ saving ? '保存中...' : '保存' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import {
  Plus,
  Close,
  Calendar,
  Shop,
  Box,
  Tools,
  Operation,
  RefreshRight,
  RefreshLeft,
  DataAnalysis,
  More,
  DataLine,
  InfoFilled,
  Check,
  Loading,
  Switch,
} from '@element-plus/icons-vue'
import { getDestinationOptions } from '@/api/options'
import {
  addOrderDaily,
  getProductsByDestination,
  checkMonthlyOrderExists,
  createMonthlyOrder,
} from '@/api/order/order'
import dayjs from 'dayjs'

const props = defineProps<{ visible: boolean }>()
const emit = defineEmits(['update:visible', 'saved'])

const visible = ref(props.visible)
watch(
  () => props.visible,
  (v) => {
    visible.value = v
    if (v) {
      // 当对话框打开时重置表单
      resetForm()
      // 设置默认日期为今天
      const today = dayjs().format('YYYY-MM-DD')
      form.value.date = today
      onDateChange(today)
    }
  },
)
watch(visible, (v) => emit('update:visible', v))

const formRef = ref<FormInstance>()
const saving = ref(false)

// 表单数据类型声明
interface FormData {
  date: string
  delivery_date: string
  year: number
  month: number
  day: number
  weekday: string
  destination_cd: string
  destination_name: string
  product_cd: string
  product_name: string
  product_type: string
  unit_per_box: string | number
  confirmed_boxes: string | number
  confirmed_units: string | number
  monthly_order_id?: string // 添加月度订单ID字段
  [key: string]: any // 用于处理动态字段访问
}

const form = ref<FormData>({
  date: '',
  delivery_date: '',
  year: 0,
  month: 0,
  day: 0,
  weekday: '',
  destination_cd: '',
  destination_name: '',
  product_cd: '',
  product_name: '',
  product_type: '',
  unit_per_box: '',
  confirmed_boxes: '',
  confirmed_units: '',
})

// 表单验证规则
const rules = reactive<FormRules>({
  date: [{ required: true, message: '出荷日を入力してください', trigger: 'change' }],
  delivery_date: [{ required: true, message: '納入日を入力してください', trigger: 'change' }],
  destination_cd: [{ required: true, message: '納入先を選択してください', trigger: 'change' }],
  product_cd: [{ required: true, message: '製品を選択してください', trigger: 'change' }],
})

const destinationOptions = ref<any[]>([])
const productOptions = ref<any[]>([])
const filteredProductOptions = computed(() => {
  return [...productOptions.value].sort((a, b) => {
    return (a.product_name || '').localeCompare(b.product_name || '')
  })
})

// 处理出荷日变更
const onDateChange = (val: string) => {
  if (!val) {
    // 清空年月日
    form.value.year = 0
    form.value.month = 0
    form.value.day = 0
    form.value.weekday = ''
    return
  }

  const d = dayjs(val)
  form.value.year = d.year()
  form.value.month = d.month() + 1
  form.value.day = d.date()
  form.value.weekday = ['日', '月', '火', '水', '木', '金', '土'][d.day()]

  console.log('出荷日変更:', val, '→ 年月日:', form.value.year, form.value.month, form.value.day)

  // 如果没有设置纳入日，默认设置为与出荷日相同
  if (!form.value.delivery_date) {
    form.value.delivery_date = val
  }
}

// 处理纳入日变更
const handleDeliveryDateChange = (val: string) => {
  console.log('納入日変更:', val)
  // 直接设置到表单中，确保值被正确更新
  form.value.delivery_date = val || ''
}

const onDestinationChange = async () => {
  form.value.product_cd = ''
  form.value.product_name = ''
  form.value.unit_per_box = ''
  form.value.destination_name = ''
  if (!form.value.destination_cd) return
  // 获取当前年月，或使用表单中已选择的年月
  const year = form.value.year || new Date().getFullYear()
  const month = form.value.month || new Date().getMonth() + 1
  try {
    const products = await getProductsByDestination(form.value.destination_cd, year, month)
    productOptions.value = products
    // 自动带出 destination_name
    const dest = destinationOptions.value.find(
      (d) => d.cd === form.value.destination_cd || d.destination_cd === form.value.destination_cd,
    )
    if (dest) {
      form.value.destination_name = dest.name || dest.destination_name || ''
    }
  } catch (error) {
    console.error('製品情報の取得に失敗しました', error)
    productOptions.value = []
    ElMessage.warning('製品情報の取得に失敗しました')
  }
}

const onProductChange = () => {
  const prod = productOptions.value.find((p) => p.product_cd === form.value.product_cd)
  if (prod) {
    // 只有当产品类型为空时才从后端数据获取，避免覆盖用户的手动选择
    if (!form.value.product_type) {
      form.value.product_type = prod.product_type || ''
    }
    form.value.unit_per_box = prod.unit_per_box ? String(prod.unit_per_box) : ''
    form.value.product_name = prod.product_name || ''
    // 当产品改变时，重新计算本数
    calculateUnits()
  } else {
    form.value.product_type = ''
    form.value.unit_per_box = ''
    form.value.product_name = ''
    form.value.confirmed_units = ''
  }
}

// 处理产品类型变更
const onProductTypeChange = (value: string) => {
  console.log('产品类型手动变更:', value) // 调试信息
  form.value.product_type = value
}

// 处理数字输入
const handleNumericInput = (value: string, field: string) => {
  // 只允许输入数字
  const numericValue = value.replace(/[^0-9]/g, '')

  // 更新表单字段
  form.value[field] = numericValue === '' ? '' : numericValue
}

// 处理箱数输入（包含自动计算）
const handleBoxesInput = (value: string) => {
  handleNumericInput(value, 'confirmed_boxes')
  calculateUnits()
}

// 根据箱数和入数自动计算本数
const calculateUnits = () => {
  const unitPerBox = parseInt(String(form.value.unit_per_box), 10) || 0
  const confirmedBoxes = parseInt(String(form.value.confirmed_boxes), 10) || 0

  if (unitPerBox > 0 && confirmedBoxes > 0) {
    form.value.confirmed_units = String(unitPerBox * confirmedBoxes)
  } else {
    form.value.confirmed_units = ''
  }
}

const resetForm = () => {
  form.value = {
    date: '',
    delivery_date: '',
    year: 0,
    month: 0,
    day: 0,
    weekday: '',
    destination_cd: '',
    destination_name: '',
    product_cd: '',
    product_name: '',
    product_type: '',
    unit_per_box: '',
    confirmed_boxes: '',
    confirmed_units: '',
  }
}

const fetchOptions = async () => {
  try {
    destinationOptions.value = await getDestinationOptions()
  } catch (error) {
    console.error('获取纳入先失败', error)
    destinationOptions.value = []
    ElMessage.warning('納入先情報の取得に失敗しました')
  }
}

const handleSave = async () => {
  if (!formRef.value) return

  saving.value = true
  try {
    await formRef.value.validate()

    // 确保年月日字段已设置
    if (!form.value.year || !form.value.month || !form.value.day) {
      ElMessage.warning('日付が正しく設定されていません')
      saving.value = false
      return
    }

    // 检查纳入日是否已设置，如果没有则不提交
    if (!form.value.delivery_date) {
      ElMessage.warning('納入日を入力してください')
      saving.value = false
      return
    }

    // 检查是否填写了确定箱数和入数
    if (!form.value.confirmed_boxes || !form.value.unit_per_box) {
      ElMessage.warning('確定箱数と入数を入力してください')
      saving.value = false
      return
    }

    // 根据产品类型获取后缀
    let typeSuffix = '0' // 默认量产品
    switch (form.value.product_type) {
      case '試作品':
        typeSuffix = '1'
        break
      case '別注品':
        typeSuffix = '2'
        break
      case '補給品':
        typeSuffix = '3'
        break
      case 'サンプル品':
        typeSuffix = '4'
        break
      case '代替品':
        typeSuffix = '5'
        break
      case '返却品':
        typeSuffix = '6'
        break
      case 'その他':
        typeSuffix = '7'
        break
      default:
        typeSuffix = '0' // 量産品
    }

    // 构造月度订单ID: 年月+納入先CD+製品CD+类型后缀
    const monthlyOrderId = `${form.value.year}${form.value.month.toString().padStart(2, '0')}${form.value.destination_cd}${form.value.product_cd}${typeSuffix}`

    // 检查月订单是否存在
    let exists = false
    try {
      exists = await checkMonthlyOrderExists(monthlyOrderId)
    } catch (e) {
      console.error('月次注文の確認に失敗しました:', e)
      ElMessage.error('月次注文の確認に失敗しました')
      saving.value = false
      return
    }

    // 如果月订单不存在，创建新的月订单
    if (!exists) {
      const monthlyOrder = {
        order_id: monthlyOrderId,
        destination_cd: form.value.destination_cd,
        destination_name: form.value.destination_name,
        year: form.value.year,
        month: form.value.month,
        product_cd: form.value.product_cd,
        product_name: form.value.product_name,
        product_type: form.value.product_type,
        product_alias: '',
        forecast_units: Number(form.value.confirmed_units) || 0,
        forecast_total_units: Number(form.value.confirmed_units) || 0,
      }

      try {
        await createMonthlyOrder(monthlyOrder)
        ElMessage.success('月次注文が自動作成されました')
      } catch (e) {
        console.error('创建月订单失败:', e)
        ElMessage.error('月次注文の作成に失敗しました')
        saving.value = false
        return
      }
    }

    // 构造日订单数据
    const rawPostData = {
      monthly_order_id: monthlyOrderId,
      year: form.value.year,
      month: form.value.month,
      day: form.value.day,
      weekday: form.value.weekday,
      destination_cd: form.value.destination_cd,
      destination_name: form.value.destination_name,
      product_cd: form.value.product_cd,
      product_name: form.value.product_name,
      product_type: form.value.product_type,
      unit_per_box: Number(form.value.unit_per_box) || 0,
      confirmed_boxes: Number(form.value.confirmed_boxes) || 0,
      confirmed_units: Number(form.value.confirmed_units) || 0,
      delivery_date: form.value.delivery_date,
      status: '未出荷' as const,
    }

    // 保存日订单
    try {
      await addOrderDaily(rawPostData)
      ElMessage.success('追加成功しました')
      visible.value = false
      emit('saved')
      resetForm()
    } catch (e) {
      console.error('日次注文の追加に失敗しました:', e)
      ElMessage.error('日次注文の追加に失敗しました')
    }
  } catch (e: any) {
    if (e?.message) {
      ElMessage.error(e.message)
    } else {
      console.error('保存失败', e)
      ElMessage.error('追加に失敗しました')
    }
  } finally {
    saving.value = false
  }
}

fetchOptions()
</script>

<style scoped>
/* 对话框整体样式 */
.modern-order-dialog {
  border-radius: 16px;
  overflow: hidden;
}

:deep(.el-dialog) {
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.12);
  background: linear-gradient(135deg, #fafbfc 0%, #f8fafc 100%);
  border: 1px solid rgba(255, 255, 255, 0.8);
}

:deep(.el-dialog__header) {
  padding: 0;
  margin: 0;
  border: none;
}

:deep(.el-dialog__body) {
  padding: 0;
}

:deep(.el-dialog__footer) {
  padding: 0;
  margin: 0;
}

/* 自定义头部样式 */
.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 5px 6px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  position: relative;
}

.dialog-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  z-index: -1;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon {
  width: 30px;
  height: 30px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  backdrop-filter: blur(10px);
}

.header-content {
  display: flex;
  flex-direction: column;
}

.dialog-title {
  font-size: 18px;
  font-weight: 700;
  margin: 0;
  color: white;
  line-height: 1.2;
}

.close-btn {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.05);
}

/* 内容区域样式 */
.dialog-content {
  padding: 5px 10px 10px 10px;
  max-height: 70vh;
  overflow-y: auto;
}

/* 表单分组样式 */
.form-section {
  margin-bottom: 5px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 12px;
  border: 1px solid rgba(226, 232, 240, 0.5);
  backdrop-filter: blur(10px);
  overflow: hidden;
  transition: all 0.3s ease;
}

.form-section:hover {
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 5px 10px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.08), rgba(118, 75, 162, 0.08));
  border-bottom: 1px solid rgba(226, 232, 240, 0.5);
}

.section-icon {
  font-size: 16px;
  color: #667eea;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.section-content {
  padding: 6px;
}

/* 表单样式 */
.modern-form :deep(.el-form-item__label) {
  font-weight: 600;
  color: #374151;
  font-size: 13px;
  padding-bottom: 4px;
}

.modern-form :deep(.el-form-item) {
  margin-bottom: 6px;
}

/* 输入框样式 */
.modern-input :deep(.el-input__wrapper),
.modern-select :deep(.el-input__wrapper),
.modern-date-picker :deep(.el-input__wrapper) {
  border-radius: 8px;
  border: 1.5px solid #e5e7eb;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  transition: all 0.2s ease;
  background: rgba(255, 255, 255, 0.9);
  min-height: 36px;
}

.modern-input :deep(.el-input__wrapper:hover),
.modern-select :deep(.el-input__wrapper:hover),
.modern-date-picker :deep(.el-input__wrapper:hover) {
  border-color: #667eea;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.12);
}

.modern-input :deep(.el-input__wrapper.is-focus),
.modern-select :deep(.el-input__wrapper.is-focus),
.modern-date-picker :deep(.el-input__wrapper.is-focus) {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.modern-input :deep(.el-input__inner),
.modern-select :deep(.el-input__inner),
.modern-date-picker :deep(.el-input__inner) {
  font-weight: 500;
  color: #374151;
  font-size: 14px;
}

/* 数字输入框专用样式 */
.number-input :deep(.el-input__inner) {
  font-size: 13px;
  font-weight: 600;
  text-align: center;
  padding: 8px 12px;
  letter-spacing: 0.5px;
  font-family: 'Courier New', monospace;
}

.number-input :deep(.el-input__wrapper) {
  min-height: 36px;
}

/* 数字表单项样式 */
.number-form-item {
  margin-bottom: 10px;
}

.number-form-item :deep(.el-form-item__label) {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  line-height: 1.5;
}

/* 计算字段表单项样式 */
.calculated-form-item {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.05), rgba(5, 150, 105, 0.05));
  border: 1px solid rgba(16, 185, 129, 0.2);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
}

.calculated-form-item :deep(.el-form-item__label) {
  color: #059669;
  font-weight: 700;
}

/* 输入行间距 */
.input-row {
  margin-bottom: 4px;
}

.input-row:last-of-type {
  margin-bottom: 12px;
}

/* 计算字段样式 */
.calculated-field :deep(.el-input__wrapper) {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.05), rgba(5, 150, 105, 0.05));
  border-color: #10b981;
}

.calculated-field :deep(.el-input__inner) {
  color: #059669;
  font-weight: 600;
}

/* 选择框选项样式 */
.option-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.option-item .el-icon {
  font-size: 16px;
  color: #667eea;
}

/* 计算提示样式 */
.calculation-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  padding: 8px 12px;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.08), rgba(37, 99, 235, 0.08));
  border: 1px solid rgba(59, 130, 246, 0.15);
  border-radius: 8px;
  font-size: 12px;
  color: #3b82f6;
}

.calculation-hint .el-icon {
  font-size: 14px;
  color: #3b82f6;
}

/* 底部按钮样式 */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 0 20px 10px 20px;
  background: transparent;
  border: none;
}

.cancel-btn {
  border-radius: 8px;
  border: 1.5px solid #e5e7eb;
  background: rgba(255, 255, 255, 0.9);
  color: #6b7280;
  font-weight: 600;
  padding: 8px 20px;
  transition: all 0.2s ease;
  font-size: 12px;
}

.cancel-btn:hover {
  border-color: #d1d5db;
  background: rgba(255, 255, 255, 1);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.save-btn {
  border-radius: 8px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  color: white;
  font-weight: 600;
  padding: 8px 20px;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.25);
  transition: all 0.2s ease;
  font-size: 12px;
}

.save-btn:hover {
  background: linear-gradient(135deg, #5a67d8, #6b46c1);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.35);
}

.save-btn:active {
  transform: translateY(0);
}

/* 下拉选项样式 */
:deep(.el-select-dropdown) {
  border-radius: 8px;
  border: 1px solid rgba(226, 232, 240, 0.5);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
}

:deep(.el-select-dropdown__item) {
  padding: 10px 14px;
  transition: all 0.2s ease;
  border-radius: 6px;
  margin: 2px 6px;
  font-size: 14px;
}

:deep(.el-select-dropdown__item:hover) {
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
}

:deep(.el-select-dropdown__item.selected) {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.15), rgba(118, 75, 162, 0.15));
  color: #667eea;
  font-weight: 600;
}

/* 日期选择器样式 */
:deep(.el-date-editor .el-input__prefix) {
  color: #667eea;
}

/* 响应式设计 */
@media (max-width: 992px) {
  .modern-order-dialog {
    width: 90vw !important;
    margin: 5vh auto !important;
  }
}

@media (max-width: 768px) {
  .modern-order-dialog {
    width: 95vw !important;
    margin: 5vh auto !important;
  }

  .dialog-header {
    padding: 14px 20px;
  }

  .header-icon {
    width: 36px;
    height: 36px;
    font-size: 18px;
  }

  .dialog-title {
    font-size: 16px;
  }

  .dialog-content {
    padding: 16px 18px;
  }

  .section-header {
    padding: 10px 14px;
  }

  .section-content {
    padding: 14px;
  }

  .dialog-footer {
    padding: 0 18px 10px 18px;
    flex-direction: column;
    background: transparent;
    border: none;
  }

  .cancel-btn,
  .save-btn {
    width: 100%;
    justify-content: center;
  }

  /* 移动端数字输入框调整 */
  .number-input :deep(.el-input__inner) {
    font-size: 16px;
    padding: 10px 14px;
  }

  .number-input :deep(.el-input__wrapper) {
    min-height: 40px;
  }

  /* 移动端表单项间距调整 */
  .number-form-item {
    margin-bottom: 14px;
  }

  .calculated-form-item {
    padding: 10px;
    margin-bottom: 10px;
  }

  .input-row {
    margin-bottom: 4px;
  }
}

/* 滚动条样式 */
.dialog-content::-webkit-scrollbar {
  width: 6px;
}

.dialog-content::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 3px;
}

.dialog-content::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 3px;
}

.dialog-content::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #5a67d8, #6b46c1);
}

/* 动画效果 */
@keyframes dialogSlideIn {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }

  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

:deep(.el-dialog) {
  animation: dialogSlideIn 0.3s ease-out;
}

/* 表单验证错误样式 */
:deep(.el-form-item.is-error .el-input__wrapper) {
  border-color: #f56565 !important;
  box-shadow: 0 0 0 4px rgba(245, 101, 101, 0.1) !important;
}

:deep(.el-form-item__error) {
  color: #f56565;
  font-size: 12px;
  font-weight: 500;
  margin-top: 4px;
}
</style>
