<template>
  <div class="inventory-entry-form">
    <el-card class="form-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <h3 class="form-title">棚卸登録</h3>
          <el-tag :type="getItemTypeColor(formData.item)" effect="dark" class="item-type-display">
            {{ formData.item || 'タイプを選択' }}
          </el-tag>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-width="120px"
        class="entry-form"
        @submit.prevent="handleSubmit"
      >
        <!-- 項目类型选择 -->
        <el-form-item label="項目タイプ" prop="item" required>
          <el-radio-group v-model="formData.item" @change="handleItemTypeChange">
            <el-radio-button label="材料">
              <el-icon><Box /></el-icon>
              材料
            </el-radio-button>
            <el-radio-button label="部品">
              <el-icon><Tools /></el-icon>
              部品
            </el-radio-button>
            <el-radio-button label="ステー">
              <el-icon><Grid /></el-icon>
              ステー
            </el-radio-button>
          </el-radio-group>
        </el-form-item>

        <!-- 製品CD -->
        <el-form-item label="製品CD" prop="product_cd" required>
          <el-select
            v-model="formData.product_cd"
            placeholder="製品CDを選択してください"
            clearable
            filterable
            @change="handleProductChange"
            style="width: 100%"
            :loading="loading"
          >
            <!-- ステー选项 -->
            <el-option
              v-if="formData.item === 'ステー'"
              v-for="product in productOptions"
              :key="product.product_cd"
              :label="`${product.product_name} (${product.product_cd})`"
              :value="product.product_cd"
            >
              <div style="display: flex; align-items: center; gap: 8px">
                <span style="font-weight: 600; color: #2c3e50">{{ product.product_name }}</span>
                <span style="font-size: 12px; color: #909399">({{ product.product_cd }})</span>
              </div>
            </el-option>

            <!-- 材料选项 -->
            <el-option
              v-if="formData.item === '材料'"
              v-for="material in materialOptions"
              :key="material.material_cd"
              :label="`${material.material_name} (${material.material_cd})`"
              :value="material.material_cd"
            >
              <div style="display: flex; align-items: center; gap: 8px">
                <span style="font-weight: 600; color: #2c3e50">{{ material.material_name }}</span>
                <span style="font-size: 12px; color: #909399">({{ material.material_cd }})</span>
              </div>
            </el-option>

            <!-- 部品选项 -->
            <el-option
              v-if="formData.item === '部品'"
              v-for="component in componentOptions"
              :key="component.component_cd"
              :label="`${component.component_name} (${component.component_cd})`"
              :value="component.component_cd"
            >
              <div style="display: flex; align-items: center; gap: 8px">
                <span style="font-weight: 600; color: #2c3e50">{{ component.component_name }}</span>
                <span style="font-size: 12px; color: #909399">({{ component.component_cd }})</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <!-- 製品名 -->
        <el-form-item label="製品名" prop="product_name" required>
          <el-input
            v-model="formData.product_name"
            placeholder="製品名"
            readonly
            :disabled="!formData.product_cd"
          >
            <template #prefix>
              <el-icon><Goods /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <!-- 工程CD和工程名 -->
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="工程CD" prop="process_cd" required>
              <el-select
                v-model="formData.process_cd"
                placeholder="工程を選択してください"
                clearable
                @change="handleProcessChange"
                :disabled="formData.item === '材料' || formData.item === '部品'"
              >
                <el-option
                  v-for="process in processOptions"
                  :key="process.process_cd"
                  :label="`${process.process_name} (${process.process_cd})`"
                  :value="process.process_cd"
                >
                  <el-tag :type="getProcessTypeColor(process.process_cd)" size="small">
                    {{ process.process_name }}
                  </el-tag>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="工程名" prop="process_name">
              <el-input
                v-model="formData.process_name"
                placeholder="工程名"
                readonly
                :disabled="
                  !formData.process_cd || formData.item === '材料' || formData.item === '部品'
                "
              />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 日期和时间 -->
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="日付" prop="log_date" required>
              <el-date-picker
                v-model="formData.log_date"
                type="date"
                placeholder="日付を選択"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="時間" prop="log_time" required>
              <el-time-picker
                v-model="formData.log_time"
                placeholder="時間を選択"
                format="HH:mm:ss"
                value-format="HH:mm:ss"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- HD番号 -->
        <el-form-item label="HD番号" prop="hd_no">
          <el-input v-model="formData.hd_no" placeholder="手入力" readonly disabled>
            <template #prefix>
              <el-icon><Document /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <!-- 数量相关 -->
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="入数" prop="pack_qty">
              <el-input-number
                v-model="formData.pack_qty"
                :min="0"
                :max="99999"
                placeholder="入数"
                style="width: 100%"
                :controls="false"
                @change="calculateQuantity"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="ケース数" prop="case_qty">
              <el-input-number
                v-model="formData.case_qty"
                :min="0"
                :max="99999"
                placeholder="ケース数"
                style="width: 100%"
                :controls="false"
                @change="calculateQuantity"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="数量" prop="quantity" required>
              <el-input-number
                v-model="formData.quantity"
                :min="0"
                :max="99999"
                placeholder="総数量"
                style="width: 100%"
                :controls="false"
                :class="getQuantityClass(formData.quantity)"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 作業者 -->
        <el-form-item label="作業者" prop="remarks" required>
          <el-select
            v-model="formData.remarks"
            placeholder="作業者を選択してください"
            clearable
            filterable
            style="width: 100%"
            :loading="loading"
          >
            <el-option
              v-for="user in userOptions"
              :key="user.username"
              :label="`${user.name} (${user.username})`"
              :value="user.username"
            >
              <div class="user-option">
                <span class="user-name">{{ user.name }}</span>
                <span class="user-username">({{ user.username }})</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <!-- 操作按钮 -->
        <el-form-item class="form-actions">
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            <el-icon><Check /></el-icon>
            保存
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            リセット
          </el-button>
          <el-button @click="handleCancel">
            <el-icon><Close /></el-icon>
            キャンセル
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Box,
  Tools,
  Grid,
  Document,
  Goods,
  Check,
  Refresh,
  Close,
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import {
  getProducts,
  getMaterials,
  getComponents,
  getProcesses,
  getUsers,
  type Product,
  type Material,
  type Component,
  type Process,
  type User as UserType,
} from '@/api/stocktake/common'

// 定义props
interface Props {
  initialData?: any
  submitting?: boolean
}

// 定义emits
interface Emits {
  (e: 'submit', data: any): void
  (e: 'cancel'): void
}

const props = withDefaults(defineProps<Props>(), {
  initialData: () => ({}),
  submitting: false,
})

const emit = defineEmits<Emits>()

// 表单引用
const formRef = ref()

// 数据加载状态
const loading = ref(false)

// 表单数据 - 与数据库表结构匹配
const formData = reactive({
  item: '', // 項目
  product_cd: '', // 製品CD
  product_name: '', // 製品名
  process_cd: '', // 工程CD
  process_name: '', // 工程名
  log_date: dayjs().format('YYYY-MM-DD'), // 日付
  log_time: dayjs().format('HH:mm:ss'), // 時間
  hd_no: '手入力', // HD番号 - 固定值
  pack_qty: null as number | null, // 入数
  case_qty: null as number | null, // ケース数
  quantity: 0, // 数量
  remarks: '', // 作業者/备注
})

// 製品选项
const productOptions = ref<Product[]>([])
const materialOptions = ref<Material[]>([])
const componentOptions = ref<Component[]>([])

// 工程选项
const processOptions = ref<Process[]>([])

// 作業者选项
const userOptions = ref<UserType[]>([])

// 工程选项 - 根据ステー类型添加切断、面取等工程
// const processOptions = [
//   { value: 'KT01', label: '切断' },
//   { value: 'KT02', label: '面取' },
//   { value: 'KT03', label: 'SW' },
//   { value: 'KT04', label: '成形' },
//   { value: 'KT05', label: 'めっき' },
//   { value: 'KT06', label: '外注めっき' },
//   { value: 'KT07', label: '溶接' },
//   { value: 'KT08', label: '外注溶接' },
//   { value: 'KT09', label: '検査' },
//   { value: 'KT10', label: '外注前検査' },
//   { value: 'KT11', label: '溶接前検査' },
//   { value: 'KT13', label: '倉庫' },
// ]

// 表单验证规则
const rules = {
  item: [{ required: true, message: '項目タイプを選択してください', trigger: 'change' }],
  product_cd: [{ required: true, message: '製品CDを選択してください', trigger: 'change' }],
  product_name: [
    { required: true, message: '製品名を入力してください', trigger: 'blur' },
    { min: 1, max: 255, message: '製品名は1〜255文字で入力してください', trigger: 'blur' },
  ],
  process_cd: [{ required: true, message: '工程を選択してください', trigger: 'change' }],
  log_date: [{ required: true, message: '日付を選択してください', trigger: 'change' }],
  log_time: [{ required: true, message: '時間を選択してください', trigger: 'change' }],
  quantity: [
    { required: true, message: '数量を入力してください', trigger: 'blur' },
    {
      type: 'number' as const,
      min: 0,
      message: '数量は0以上である必要があります',
      trigger: 'blur',
    },
  ],
  remarks: [{ required: true, message: '作業者を選択してください', trigger: 'change' }],
}

// 获取項目类型颜色
const getItemTypeColor = (type: string): 'success' | 'warning' | 'info' | 'primary' | 'danger' => {
  switch (type) {
    case '材料':
      return 'success'
    case '部品':
      return 'warning'
    case 'ステー':
      return 'primary'
    default:
      return 'info'
  }
}

// 获取工程CD颜色
const getProcessTypeColor = (
  processCd: string,
): 'success' | 'warning' | 'info' | 'primary' | 'danger' => {
  switch (processCd) {
    case 'KT01':
      return 'success'
    case 'KT02':
      return 'warning'
    case 'KT03':
      return 'primary'
    case 'KT04':
      return 'danger'
    case 'KT05':
      return 'success'
    case 'KT06':
      return 'warning'
    case 'KT07':
      return 'primary'
    case 'KT08':
      return 'danger'
    case 'KT09':
      return 'success'
    case 'KT10':
      return 'warning'
    case 'KT11':
      return 'primary'
    case 'KT13':
      return 'info'
    default:
      return 'info'
  }
}

// 获取数量样式类
const getQuantityClass = (quantity: number): string => {
  if (quantity <= 0) return 'out-of-stock'
  if (quantity <= 10) return 'low-stock'
  return 'normal-stock'
}

// 处理製品CD变化
const handleProductChange = (value: string) => {
  let product: Product | Material | Component | undefined

  switch (formData.item) {
    case 'ステー':
      product = productOptions.value.find((p: Product) => p.product_cd === value)
      if (product) {
        formData.product_name = (product as Product).product_name
      }
      break
    case '材料':
      product = materialOptions.value.find((m: Material) => m.material_cd === value)
      if (product) {
        formData.product_name = (product as Material).material_name
      }
      break
    case '部品':
      product = componentOptions.value.find((c: Component) => c.component_cd === value)
      if (product) {
        formData.product_name = (product as Component).component_name
      }
      break
  }

  if (!product) {
    formData.product_name = ''
  }
}

// 处理工程变化
const handleProcessChange = (value: string) => {
  const process = processOptions.value.find((p: Process) => p.process_cd === value)
  if (process) {
    formData.process_name = process.process_name
  } else {
    formData.process_name = ''
  }
}

// 计算数量
const calculateQuantity = () => {
  if (formData.pack_qty && formData.case_qty) {
    formData.quantity = formData.pack_qty * formData.case_qty
  }
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value.validate()

    // 根据項目タイプ设置item值
    let itemValue = ''
    switch (formData.item) {
      case '材料':
        itemValue = '材料棚卸'
        break
      case '部品':
        itemValue = '部品棚卸'
        break
      case 'ステー':
        itemValue = '製品棚卸'
        break
      default:
        itemValue = formData.item
    }

    const submitData = {
      ...formData,
      item: itemValue, // 使用转换后的item值
      // 确保数量字段为数字
      pack_qty: formData.pack_qty || null,
      case_qty: formData.case_qty || null,
      quantity: Number(formData.quantity) || 0,
    }

    emit('submit', submitData)
  } catch (error) {
    ElMessage.error('フォームの入力内容を確認してください')
  }
}

// 重置表单
const handleReset = () => {
  ElMessageBox.confirm('フォームをリセットしますか？', '確認', {
    confirmButtonText: '確定',
    cancelButtonText: 'キャンセル',
    type: 'warning',
  }).then(() => {
    formRef.value.resetFields()
    Object.assign(formData, {
      item: '',
      product_cd: '',
      product_name: '',
      process_cd: '',
      process_name: '',
      log_date: dayjs().format('YYYY-MM-DD'),
      log_time: dayjs().format('HH:mm:ss'),
      hd_no: '手入力', // 保持固定值
      pack_qty: null,
      case_qty: null,
      quantity: 0,
      remarks: '',
    })
    ElMessage.success('フォームがリセットされました')
  })
}

// 取消操作
const handleCancel = () => {
  emit('cancel')
}

// 加载产品数据
const loadProducts = async () => {
  try {
    loading.value = true
    console.log('开始加载产品数据...')
    const response = await getProducts()
    console.log('API响应:', response)

    // 过滤掉製品CD最后一位不是1的产品
    const filteredProducts = response.filter((product: Product) => product.product_cd.endsWith('1'))

    // 按照製品名排序
    const sortedProducts = filteredProducts.sort((a: Product, b: Product) =>
      a.product_name.localeCompare(b.product_name),
    )

    productOptions.value = sortedProducts
    console.log('产品数据加载成功:', productOptions.value.length, '个产品')
    console.log('产品数据:', productOptions.value)
  } catch (error: any) {
    console.error('製品データ取得エラー:', error)
    console.error('错误详情:', error.response?.data || error.message)
    ElMessage.error('製品データの取得に失敗しました')
  } finally {
    loading.value = false
  }
}

// 加载材料数据
const loadMaterials = async () => {
  try {
    loading.value = true
    const response = await getMaterials()

    // 按照材料名排序
    const sortedMaterials = response.sort((a: Material, b: Material) =>
      a.material_name.localeCompare(b.material_name),
    )

    materialOptions.value = sortedMaterials
  } catch (error: any) {
    console.error('材料データ取得エラー:', error)
    ElMessage.error('材料データの取得に失敗しました')
  } finally {
    loading.value = false
  }
}

// 加载部品数据
const loadComponents = async () => {
  try {
    loading.value = true
    const response = await getComponents()

    // 按照部品名排序
    const sortedComponents = response.sort((a: Component, b: Component) =>
      a.component_name.localeCompare(b.component_name),
    )

    componentOptions.value = sortedComponents
  } catch (error: any) {
    console.error('部品データ取得エラー:', error)
    ElMessage.error('部品データの取得に失敗しました')
  } finally {
    loading.value = false
  }
}

// 加载工程数据
const loadProcesses = async () => {
  try {
    loading.value = true
    const response = await getProcesses()

    // 按照工程名排序
    const sortedProcesses = response.sort((a: Process, b: Process) =>
      a.process_name.localeCompare(b.process_name),
    )

    processOptions.value = sortedProcesses
  } catch (error: any) {
    console.error('工程データ取得エラー:', error)
    ElMessage.error('工程データの取得に失敗しました')
  } finally {
    loading.value = false
  }
}

// 加载用户数据
const loadUsers = async () => {
  try {
    loading.value = true
    const response = await getUsers()
    // 直接使用返回的数组数据
    userOptions.value = response
  } catch (error: any) {
    console.error('ユーザーデータ取得エラー:', error)
    ElMessage.error('ユーザーデータの取得に失敗しました')
  } finally {
    loading.value = false
  }
}

// 根据項目タイプ加载对应数据
const loadDataByItemType = async (itemType: string) => {
  // 清空当前选择
  formData.product_cd = ''
  formData.product_name = ''
  formData.pack_qty = null

  switch (itemType) {
    case 'ステー':
      await loadProducts()
      await loadProcesses() // 加载工程数据
      break
    case '材料':
      await loadMaterials()
      break
    case '部品':
      await loadComponents()
      break
    default:
      break
  }
}

// 处理項目类型变化
const handleItemTypeChange = (value: string | number | boolean | undefined) => {
  if (typeof value === 'string') {
    console.log('項目类型变化:', value)

    // 根据項目类型设置固定的工程CD和工程名
    switch (value) {
      case '材料':
        formData.process_cd = 'KT19'
        formData.process_name = '材料'
        break
      case '部品':
        formData.process_cd = 'KT18'
        formData.process_name = '部品'
        break
      case 'ステー':
        // ステー类型需要用户手动选择工程
        formData.process_cd = ''
        formData.process_name = ''
        break
    }

    loadDataByItemType(value)
  }
}

// 监听 initialData 变化，自动填充表单
watch(
  () => props.initialData,
  (newData) => {
    if (newData && Object.keys(newData).length > 0) {
      console.log('自动填充表单数据:', newData)
      // 更新表单数据
      Object.assign(formData, {
        item: newData.item || '',
        product_cd: newData.product_cd || '',
        product_name: newData.product_name || '',
        process_cd: newData.process_cd || '',
        process_name: newData.process_name || '',
        remarks: newData.remarks || '',
        // 保持当前时间
        log_date: newData.log_date || dayjs().format('YYYY-MM-DD'),
        log_time: newData.log_time || dayjs().format('HH:mm:ss'),
        hd_no: '手入力',
        pack_qty: newData.pack_qty || null,
        case_qty: newData.case_qty || null,
        quantity: newData.quantity || 0,
      })

      // 如果项目类型变化，需要重新加载对应的选项数据
      if (newData.item && newData.item !== formData.item) {
        handleItemTypeChange(newData.item)
      }
    }
  },
  { immediate: true, deep: true },
)

// 组件挂载时加载数据
onMounted(() => {
  loadProducts()
  loadUsers()
})
</script>

<style scoped>
/* 动画定义 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-10px);
  }
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

.inventory-entry-form {
  max-width: 900px;
  margin: 0 auto;
  padding: 16px;
  min-height: 100vh;
  background: linear-gradient(
    135deg,
    rgba(102, 126, 234, 0.05) 0%,
    rgba(118, 75, 162, 0.05) 50%,
    rgba(255, 154, 158, 0.05) 100%
  );
  position: relative;
  overflow: hidden;
}

.inventory-entry-form::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(102, 126, 234, 0.1) 0%, transparent 70%);
  animation: float 6s ease-in-out infinite;
  pointer-events: none;
}

.form-card {
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.1),
    0 2px 8px rgba(0, 0, 0, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  animation: fadeInUp 0.8s ease-out;
  position: relative;
  overflow: hidden;
}

.form-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.form-card:hover::before {
  left: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 32px 16px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  border-radius: 20px 20px 0 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  position: relative;
}

.form-title {
  margin: 0;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.item-type-display {
  font-weight: 600;
  padding: 8px 16px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(230, 3, 71, 0.979), rgb(206, 2, 97));
  border: 1px solid rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  animation: pulse 2s ease-in-out infinite;
}

.item-type-display:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.entry-form {
  padding: 32px;
  background: rgba(255, 255, 255, 0.4);
  border-radius: 0 0 20px 20px;
  backdrop-filter: blur(10px);
}

.entry-form :deep(.el-form-item) {
  margin-bottom: 24px;
  animation: fadeInUp 0.6s ease-out;
  animation-fill-mode: both;
}

.entry-form :deep(.el-form-item:nth-child(1)) {
  animation-delay: 0.1s;
}
.entry-form :deep(.el-form-item:nth-child(2)) {
  animation-delay: 0.2s;
}
.entry-form :deep(.el-form-item:nth-child(3)) {
  animation-delay: 0.3s;
}
.entry-form :deep(.el-form-item:nth-child(4)) {
  animation-delay: 0.4s;
}
.entry-form :deep(.el-form-item:nth-child(5)) {
  animation-delay: 0.5s;
}
.entry-form :deep(.el-form-item:nth-child(6)) {
  animation-delay: 0.6s;
}
.entry-form :deep(.el-form-item:nth-child(7)) {
  animation-delay: 0.7s;
}
.entry-form :deep(.el-form-item:nth-child(8)) {
  animation-delay: 0.8s;
}
.entry-form :deep(.el-form-item:nth-child(9)) {
  animation-delay: 0.9s;
}

.entry-form :deep(.el-form-item__label) {
  font-weight: 600;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: 14px;
  letter-spacing: 0.3px;
}

.entry-form :deep(.el-input__wrapper) {
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(10px);
  box-shadow:
    0 4px 12px rgba(0, 0, 0, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.5);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.entry-form :deep(.el-input__wrapper:hover) {
  transform: translateY(-2px);
  box-shadow:
    0 8px 25px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
  border-color: rgba(102, 126, 234, 0.3);
}

.entry-form :deep(.el-input__wrapper.is-focus) {
  transform: translateY(-2px);
  box-shadow:
    0 0 0 3px rgba(102, 126, 234, 0.15),
    0 8px 25px rgba(102, 126, 234, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
  border-color: #667eea;
}

.entry-form :deep(.el-select) {
  width: 100%;
}

.entry-form :deep(.el-select__wrapper) {
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(10px);
  box-shadow:
    0 4px 12px rgba(0, 0, 0, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.5);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.entry-form :deep(.el-select__wrapper:hover) {
  transform: translateY(-2px);
  box-shadow:
    0 8px 25px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
  border-color: rgba(102, 126, 234, 0.3);
}

.entry-form :deep(.el-select__wrapper.is-focused) {
  transform: translateY(-2px);
  box-shadow:
    0 0 0 3px rgba(102, 126, 234, 0.15),
    0 8px 25px rgba(102, 126, 234, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
  border-color: #667eea;
}

.entry-form :deep(.el-radio-group) {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.entry-form :deep(.el-radio-button) {
  margin: 0;
}

.entry-form :deep(.el-radio-button__inner) {
  border-radius: 12px;
  padding: 12px 20px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-weight: 600;
  color: #667eea;
  display: flex;
  align-items: center;
  gap: 8px;
}

.entry-form :deep(.el-radio-button__inner:hover) {
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.2);
  background: rgba(255, 255, 255, 0.95);
}

.entry-form :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-color: #667eea;
  color: white;
  transform: translateY(-3px);
  box-shadow:
    0 8px 25px rgba(102, 126, 234, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.entry-form :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner .el-icon) {
  color: white;
}

/* 日期时间选择器样式 */
.entry-form :deep(.el-date-editor) {
  width: 100%;
}

.entry-form :deep(.el-date-editor .el-input__wrapper) {
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(10px);
  box-shadow:
    0 4px 12px rgba(0, 0, 0, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.5);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.entry-form :deep(.el-date-editor .el-input__wrapper:hover) {
  transform: translateY(-2px);
  box-shadow:
    0 8px 25px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
  border-color: rgba(102, 126, 234, 0.3);
}

.entry-form :deep(.el-date-editor .el-input__wrapper.is-focus) {
  transform: translateY(-2px);
  box-shadow:
    0 0 0 3px rgba(102, 126, 234, 0.15),
    0 8px 25px rgba(102, 126, 234, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
  border-color: #667eea;
}

/* 数量输入框样式 */
.entry-form :deep(.el-input-number) {
  width: 100%;
}

.entry-form :deep(.el-input-number .el-input__wrapper) {
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(10px);
  box-shadow:
    0 4px 12px rgba(0, 0, 0, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.5);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.entry-form :deep(.el-input-number .el-input__wrapper:hover) {
  transform: translateY(-2px);
  box-shadow:
    0 8px 25px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
  border-color: rgba(102, 126, 234, 0.3);
}

.entry-form :deep(.el-input-number .el-input__wrapper.is-focus) {
  transform: translateY(-2px);
  box-shadow:
    0 0 0 3px rgba(102, 126, 234, 0.15),
    0 8px 25px rgba(102, 126, 234, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
  border-color: #667eea;
}

.entry-form :deep(.el-input-number.normal-stock .el-input__inner) {
  color: #67c23a;
  font-weight: 600;
}

.entry-form :deep(.el-input-number.low-stock .el-input__inner) {
  color: #e6a23c;
  font-weight: 600;
}

.entry-form :deep(.el-input-number.out-of-stock .el-input__inner) {
  color: #f56c6c;
  font-weight: 600;
}

/* 操作按钮样式 */
.form-actions {
  margin-top: 40px;
  text-align: center;
  padding: 24px 0;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 16px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.form-actions :deep(.el-button) {
  margin: 0 12px;
  border-radius: 12px;
  padding: 14px 28px;
  font-weight: 600;
  font-size: 14px;
  letter-spacing: 0.5px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  border: none;
}

.form-actions :deep(.el-button::before) {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.5s;
}

.form-actions :deep(.el-button:hover::before) {
  left: 100%;
}

.form-actions :deep(.el-button:hover) {
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
}

.form-actions :deep(.el-button--primary) {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.form-actions :deep(.el-button--primary:hover) {
  background: linear-gradient(135deg, #5a6fd8, #6a4190);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
}

.form-actions :deep(.el-button:not(.el-button--primary)) {
  background: rgba(255, 255, 255, 0.8);
  color: #667eea;
  border: 1px solid rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.form-actions :deep(.el-button:not(.el-button--primary):hover) {
  background: rgba(255, 255, 255, 0.95);
  color: #5a6fd8;
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
}

/* 下拉框选项样式 */
.product-option {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px 12px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.product-option:hover {
  background: rgba(102, 126, 234, 0.1);
}

.product-cd {
  font-weight: 600;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.product-name {
  font-size: 12px;
  color: #606266;
}

.user-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.user-option:hover {
  background: rgba(102, 126, 234, 0.1);
}

.user-name {
  font-weight: 600;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.user-username {
  font-size: 12px;
  color: #909399;
}

/* 下拉框面板样式 */
.entry-form :deep(.el-select-dropdown) {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.entry-form :deep(.el-select-dropdown__item) {
  border-radius: 8px;
  margin: 4px 8px;
  transition: all 0.3s ease;
}

.entry-form :deep(.el-select-dropdown__item:hover) {
  background: rgba(102, 126, 234, 0.1);
  transform: translateX(4px);
}

.entry-form :deep(.el-select-dropdown__item.selected) {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.2));
  color: #667eea;
  font-weight: 600;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .inventory-entry-form {
    max-width: 800px;
    padding: 12px;
  }

  .form-card {
    border-radius: 16px;
  }

  .card-header {
    padding: 20px 24px 12px;
  }

  .form-title {
    font-size: 20px;
  }

  .entry-form {
    padding: 24px;
  }
}

@media (max-width: 768px) {
  .inventory-entry-form {
    padding: 8px;
    background: linear-gradient(
      135deg,
      rgba(102, 126, 234, 0.08) 0%,
      rgba(118, 75, 162, 0.08) 50%,
      rgba(255, 154, 158, 0.08) 100%
    );
  }

  .form-card {
    border-radius: 12px;
  }

  .card-header {
    padding: 16px 20px 12px;
  }

  .form-title {
    font-size: 18px;
  }

  .entry-form {
    padding: 20px;
  }

  .entry-form :deep(.el-form-item) {
    margin-bottom: 20px;
  }

  .entry-form :deep(.el-form-item__label) {
    font-size: 13px;
  }

  .entry-form :deep(.el-radio-group) {
    gap: 8px;
  }

  .entry-form :deep(.el-radio-button__inner) {
    padding: 10px 16px;
    font-size: 13px;
  }

  .form-actions {
    margin-top: 32px;
    padding: 20px 0;
  }

  .form-actions :deep(.el-button) {
    margin: 0 8px;
    padding: 12px 24px;
    font-size: 13px;
  }
}

@media (max-width: 480px) {
  .inventory-entry-form {
    padding: 4px;
  }

  .card-header {
    flex-direction: column;
    gap: 12px;
    padding: 12px 16px 8px;
  }

  .form-title {
    font-size: 16px;
  }

  .item-type-display {
    padding: 6px 12px;
    font-size: 12px;
  }

  .entry-form {
    padding: 16px;
  }

  .entry-form :deep(.el-form-item) {
    margin-bottom: 16px;
  }

  .entry-form :deep(.el-form-item__label) {
    font-size: 12px;
    width: 80px !important;
  }

  .entry-form :deep(.el-radio-group) {
    flex-direction: column;
    gap: 6px;
  }

  .entry-form :deep(.el-radio-button__inner) {
    padding: 8px 12px;
    font-size: 12px;
    width: 100%;
    justify-content: center;
  }

  .form-actions {
    margin-top: 24px;
    padding: 16px 0;
  }

  .form-actions :deep(.el-button) {
    margin: 4px;
    padding: 10px 20px;
    font-size: 12px;
    width: calc(50% - 8px);
  }

  .form-actions :deep(.el-button:last-child) {
    width: 100%;
    margin-top: 8px;
  }
}
</style>
