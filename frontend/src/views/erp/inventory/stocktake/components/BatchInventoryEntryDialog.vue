<template>
  <el-dialog
    v-model="dialogVisible"
    title="一括棚卸登録"
    width="95%"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    class="batch-entry-dialog"
    :modal-class="'custom-batch-modal'"
  >
    <div class="batch-entry-content">
      <div class="dialog-header">
        <div class="header-glow"></div>
        <div class="header-icon">
          <div class="icon-ring"></div>
          <el-icon :size="32">
            <Box />
          </el-icon>
        </div>
        <div class="header-text">
          <h2 class="dialog-title">一括棚卸登録</h2>
          <p class="dialog-subtitle">効率的な在庫管理のための一括登録システム</p>
        </div>
      </div>

      <div class="content-wrapper">
        <!-- 第一步：选择类型和工程 -->
        <div v-if="currentStep === 1" class="step-content">
          <div class="step-header">
            <el-steps :active="currentStep" finish-status="success" simple>
              <el-step title="タイプ選択" />
              <el-step title="製品選択" />
              <el-step title="数量入力" />
            </el-steps>
          </div>

          <div class="type-selection">
            <h3>棚卸タイプを選択してください</h3>
            <div class="type-options">
              <el-card
                v-for="type in itemTypes"
                :key="type.value"
                class="type-card"
                :class="{ active: selectedType === type.value }"
                @click="selectType(type.value)"
              >
                <div class="type-icon">
                  <el-icon :size="32">
                    <component :is="type.icon" />
                  </el-icon>
                </div>
                <div class="type-info">
                  <h4>{{ type.label }}</h4>
                  <p>{{ type.description }}</p>
                </div>
              </el-card>
            </div>

            <!-- ステー工程选择 -->
            <div v-if="selectedType === 'ステー'" class="process-selection">
              <h3>工程を選択してください</h3>
              <el-select
                v-model="selectedProcess"
                placeholder="工程を選択"
                clearable
                filterable
                style="width: 100%"
                @change="handleProcessChange"
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
            </div>
          </div>
        </div>

        <!-- 第二步：选择产品 -->
        <div v-if="currentStep === 2" class="step-content">
          <div class="step-header">
            <el-steps :active="currentStep" finish-status="success" simple>
              <el-step title="タイプ選択" />
              <el-step title="製品選択" />
              <el-step title="数量入力" />
            </el-steps>
          </div>

          <div class="product-selection">
            <div class="selection-header">
              <h3>製品を選択してください</h3>
              <div class="selection-info">
                <el-tag type="info" effect="plain">
                  {{
                    selectedType === 'ステー'
                      ? `工程: ${getProcessName(selectedProcess)}`
                      : selectedType
                  }}
                </el-tag>
                <el-button @click="goBack" size="small">
                  <el-icon><ArrowLeft /></el-icon>
                  戻る
                </el-button>
              </div>
            </div>

            <div class="product-list">
              <el-table
                :data="productList"
                border
                stripe
                v-loading="loading"
                @selection-change="handleSelectionChange"
                class="product-table"
              >
                <el-table-column type="selection" width="55" />
                <el-table-column label="製品CD" prop="product_cd" width="120" align="center" />
                <el-table-column label="製品名" prop="product_name" min-width="200" />
                <el-table-column
                  v-if="selectedType === 'ステー'"
                  label="工程"
                  width="150"
                  align="center"
                >
                  <template #default>
                    <el-tag :type="getProcessTypeColor(selectedProcess)" size="small">
                      {{ getProcessName(selectedProcess) }}
                    </el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </div>

        <!-- 第三步：输入数量 -->
        <div v-if="currentStep === 3" class="step-content">
          <div class="step-header">
            <el-steps :active="currentStep" finish-status="success" simple>
              <el-step title="タイプ選択" />
              <el-step title="製品選択" />
              <el-step title="数量入力" />
            </el-steps>
          </div>

          <div class="quantity-input">
            <div class="input-header">
              <h3>数量を入力してください</h3>
              <div class="input-info">
                <el-tag type="info" effect="plain">
                  選択済み: {{ selectedProducts.length }}件
                </el-tag>
                <el-button @click="goBack" size="small">
                  <el-icon><ArrowLeft /></el-icon>
                  戻る
                </el-button>
              </div>
            </div>

            <div class="quantity-table">
              <el-table :data="quantityData" border stripe class="quantity-table">
                <el-table-column label="製品CD" prop="product_cd" width="120" align="center" />
                <el-table-column label="製品名" prop="product_name" min-width="200" />
                <el-table-column
                  v-if="selectedType === 'ステー'"
                  label="工程"
                  width="100"
                  align="center"
                >
                  <template #default>
                    <el-tag :type="getProcessTypeColor(selectedProcess)" size="small">
                      {{ getProcessName(selectedProcess) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="入力数量1" width="120" align="center">
                  <template #default="scope">
                    <el-input-number
                      v-model="scope.row.aux_qty1"
                      :min="0"
                      :max="99999"
                      placeholder="入力数量1"
                      style="width: 100%"
                      :controls="false"
                      @change="calculateTotal(scope.row)"
                    />
                  </template>
                </el-table-column>
                <el-table-column label="入力数量2" width="120" align="center">
                  <template #default="scope">
                    <el-input-number
                      v-model="scope.row.aux_qty2"
                      :min="0"
                      :max="99999"
                      placeholder="入力数量2"
                      style="width: 100%"
                      :controls="false"
                      @change="calculateTotal(scope.row)"
                    />
                  </template>
                </el-table-column>
                <el-table-column label="数量" width="120" align="center">
                  <template #default="scope">
                    <span :class="getQuantityClass(scope.row.quantity)">
                      {{ scope.row.quantity }}
                    </span>
                  </template>
                </el-table-column>
              </el-table>
            </div>

            <!-- 作業者和日期选择 -->
            <div class="worker-date-selection">
              <div class="selection-row">
                <el-form-item label="作業者" required>
                  <el-select
                    v-model="selectedWorker"
                    placeholder="作業者を選択してください"
                    clearable
                    filterable
                    style="width: 300px"
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

                <el-form-item label="录入日期" required>
                  <el-date-picker
                    v-model="selectedDate"
                    type="date"
                    placeholder="录入日期を選択してください"
                    format="YYYY-MM-DD"
                    value-format="YYYY-MM-DD"
                    style="width: 200px"
                    :disabled-date="(time: Date) => time.getTime() > Date.now()"
                  />
                </el-form-item>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleCancel" v-if="currentStep === 1"> キャンセル </el-button>
        <el-button @click="goBack" v-if="currentStep > 1">
          <el-icon><ArrowLeft /></el-icon>
          戻る
        </el-button>
        <el-button type="primary" @click="handleNext" :disabled="!canProceed" :loading="submitting">
          <el-icon><ArrowRight /></el-icon>
          {{ currentStep === 3 ? '保存' : '次へ' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
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
import { createInventoryEntry } from '@/api/inventory'
import request from '@/utils/request'

// 定义props
interface Props {
  visible: boolean
}

// 定义emits
interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 弹窗显示状态
const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value),
})

// 当前步骤
const currentStep = ref(1)

// 加载状态
const loading = ref(false)
const submitting = ref(false)

// 选择的类型
const selectedType = ref('')

// 选择的工程（仅ステー类型）
const selectedProcess = ref('')

// 选择的产品
const selectedProducts = ref<any[]>([])

// 选择的作業者
const selectedWorker = ref('')

// 选择的录入日期
const selectedDate = ref('')

// 数量数据
const quantityData = ref<any[]>([])

// 选项数据
const productOptions = ref<Product[]>([])
const materialOptions = ref<Material[]>([])
const componentOptions = ref<Component[]>([])
const processOptions = ref<Process[]>([])
const userOptions = ref<UserType[]>([])

// 产品列表（根据类型和工程筛选）
const productList = ref<any[]>([])

// 項目类型选项
const itemTypes = [
  {
    value: '材料',
    label: '材料',
    description: '原材料の棚卸登録',
    icon: 'Box',
  },
  {
    value: '部品',
    label: '部品',
    description: '部品の棚卸登録',
    icon: 'Tools',
  },
  {
    value: 'ステー',
    label: 'ステー',
    description: '半製品の棚卸登録（工程別）',
    icon: 'Grid',
  },
]

// 是否可以继续下一步
const canProceed = computed(() => {
  switch (currentStep.value) {
    case 1:
      if (selectedType.value === 'ステー') {
        return selectedType.value && selectedProcess.value
      }
      return selectedType.value
    case 2:
      return selectedProducts.value.length > 0
    case 3:
      return (
        selectedWorker.value &&
        selectedDate.value &&
        quantityData.value.some((item) => item.quantity > 0)
      )
    default:
      return false
  }
})

// 获取工程类型颜色
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

// 获取工程名称
const getProcessName = (processCd: string): string => {
  const process = processOptions.value.find((p) => p.process_cd === processCd)
  return process ? process.process_name : processCd
}

// 获取数量样式类
const getQuantityClass = (quantity: number): string => {
  if (quantity <= 0) return 'out-of-stock'
  if (quantity <= 10) return 'low-stock'
  return 'normal-stock'
}

// 选择类型
const selectType = (type: string) => {
  selectedType.value = type
  if (type !== 'ステー') {
    selectedProcess.value = ''
  }
}

// 处理工程变化
const handleProcessChange = async () => {
  if (selectedType.value === 'ステー' && selectedProcess.value) {
    await loadProductsByProcess()
  }
}

// 处理产品选择变化
const handleSelectionChange = (selection: any[]) => {
  selectedProducts.value = selection
}

// 计算总数量
const calculateTotal = (row: any) => {
  const auxQty1 = row.aux_qty1 || 0
  const auxQty2 = row.aux_qty2 || 0
  row.quantity = auxQty1 + auxQty2
}

// 下一步
const handleNext = async () => {
  if (currentStep.value === 1) {
    await loadProductList()
    currentStep.value = 2
  } else if (currentStep.value === 2) {
    prepareQuantityData()
    currentStep.value = 3
  } else if (currentStep.value === 3) {
    await handleSubmit()
  }
}

// 返回上一步
const goBack = () => {
  if (currentStep.value > 1) {
    currentStep.value--
  }
}

// 取消操作
const handleCancel = () => {
  resetDialog()
  dialogVisible.value = false
}

// 重置弹窗
const resetDialog = () => {
  currentStep.value = 1
  selectedType.value = ''
  selectedProcess.value = ''
  selectedProducts.value = []
  selectedWorker.value = ''
  selectedDate.value = ''
  quantityData.value = []
  productList.value = []
}

// 加载产品列表
const loadProductList = async () => {
  loading.value = true
  try {
    switch (selectedType.value) {
      case 'ステー':
        await loadProductsByProcess()
        break
      case '材料':
        productList.value = materialOptions.value.map((material) => ({
          product_cd: material.material_cd,
          product_name: material.material_name,
          type: 'material',
        }))
        break
      case '部品':
        productList.value = componentOptions.value.map((component) => ({
          product_cd: component.component_cd,
          product_name: component.component_name,
          type: 'component',
        }))
        break
    }
  } catch (error) {
    console.error('产品列表加载失败:', error)
    ElMessage.error('製品リストの読み込みに失敗しました')
  } finally {
    loading.value = false
  }
}

// 根据工程加载产品
const loadProductsByProcess = async () => {
  if (!selectedProcess.value) return

  try {
    const response = await request.get(`/api/inventory/products-by-process`, {
      params: { process_cd: selectedProcess.value },
      timeout: 15000,
    })

    // 简化响应处理逻辑
    const products = response?.data || response || []

    if (products.length > 0) {
      productList.value = products.map((product: any) => ({
        product_cd: product.product_cd,
        product_name: product.product_name,
        type: 'product',
      }))
      console.log(`✅ 成功加载 ${products.length} 个产品`)
    } else {
      ElMessage.warning('該工程の製品が見つかりませんでした。すべての製品を表示します。')
      loadAllProducts()
    }
  } catch (error: any) {
    console.error('工程产品加载失败:', error)

    const isTimeout = error.code === 'ECONNABORTED' || error.message?.includes('timeout')
    ElMessage.warning(
      isTimeout
        ? '工程別製品の読み込みがタイムアウトしました。すべての製品を表示します。'
        : '工程製品の読み込みに失敗しました。すべての製品を表示します。',
    )
    loadAllProducts()
  }
}

// 加载所有产品作为备选方案
const loadAllProducts = () => {
  // productOptions.value 已经过滤并排序过了，直接使用
  productList.value = productOptions.value.map((product) => ({
    product_cd: product.product_cd,
    product_name: product.product_name,
    type: 'product',
  }))
  console.log(`✅ 加载了 ${productOptions.value.length} 个产品`)
}

// 准备数量数据
const prepareQuantityData = () => {
  quantityData.value = selectedProducts.value.map((product) => ({
    product_cd: product.product_cd,
    product_name: product.product_name,
    aux_qty1: 0,
    aux_qty2: 0,
    quantity: 0,
  }))
}

// 提交数据
const handleSubmit = async () => {
  if (!selectedWorker.value) {
    ElMessage.error('作業者を選択してください')
    return
  }

  if (!selectedDate.value) {
    ElMessage.error('录入日期を選択してください')
    return
  }

  const validItems = quantityData.value.filter((item) => item.quantity > 0)
  if (validItems.length === 0) {
    ElMessage.error('数量を入力してください')
    return
  }

  submitting.value = true
  try {
    // 根据項目タイプ设置item值
    let itemValue = ''
    switch (selectedType.value) {
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
        itemValue = selectedType.value
    }

    // 批量创建记录
    const promises = validItems.map((item) => {
      const data = {
        item: itemValue,
        product_cd: item.product_cd,
        product_name: item.product_name,
        process_cd:
          selectedType.value === 'ステー'
            ? selectedProcess.value
            : selectedType.value === '材料'
              ? 'KT19'
              : 'KT18',
        process_name:
          selectedType.value === 'ステー'
            ? getProcessName(selectedProcess.value)
            : selectedType.value === '材料'
              ? '材料'
              : '部品',
        log_date: selectedDate.value,
        log_time: dayjs().format('HH:mm:ss'),
        hd_no: '手入力',
        pack_qty: undefined,
        case_qty: undefined,
        quantity: item.quantity,
        remarks: selectedWorker.value,
      }
      return createInventoryEntry(data)
    })

    await Promise.all(promises)

    ElMessage.success(`${validItems.length}件の棚卸記録を保存しました`)
    emit('success')
    handleCancel()
  } catch (error: any) {
    console.error('批量保存失败:', error)
    ElMessage.error('保存に失敗しました: ' + (error.message || error))
  } finally {
    submitting.value = false
  }
}

// 加载基础数据
const loadBaseData = async () => {
  try {
    loading.value = true

    // 并行加载所有数据
    const [productsRes, materialsRes, componentsRes, processesRes, usersRes] = await Promise.all([
      getProducts(),
      getMaterials(),
      getComponents(),
      getProcesses(),
      getUsers(),
    ])

    // 简化响应数据处理
    const products = (productsRes as any)?.data || productsRes || []
    const materials = (materialsRes as any)?.data || materialsRes || []
    const components = (componentsRes as any)?.data || componentsRes || []
    const processes = (processesRes as any)?.data || processesRes || []
    const users = (usersRes as any)?.data || usersRes || []

    // 过滤产品（只保留製品CD最后一位为1的）并按产品名排序
    const filteredProducts = products.filter((product: Product) => product.product_cd.endsWith('1'))
    productOptions.value = filteredProducts.sort((a: Product, b: Product) =>
      a.product_name.localeCompare(b.product_name),
    )

    // 排序
    materialOptions.value = materials.sort((a: Material, b: Material) =>
      a.material_name.localeCompare(b.material_name),
    )
    componentOptions.value = components.sort((a: Component, b: Component) =>
      a.component_name.localeCompare(b.component_name),
    )
    // 过滤掉材料和部品相关的工程，只保留ステー相关的工程
    const filteredProcesses = processes.filter((process: Process) => {
      // 排除材料工程 (KT19) 和部品工程 (KT18)
      return process.process_cd !== 'KT18' && process.process_cd !== 'KT19'
    })

    processOptions.value = filteredProcesses.sort((a: Process, b: Process) =>
      a.process_cd.localeCompare(b.process_cd),
    )
    userOptions.value = users
  } catch (error: any) {
    console.error('基础数据加载失败:', error)
    ElMessage.error('データの読み込みに失敗しました')
  } finally {
    loading.value = false
  }
}

// 监听弹窗显示状态
const watchVisible = () => {
  if (props.visible) {
    resetDialog()
    loadBaseData()
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadBaseData()
})

// 监听visible变化
watch(() => props.visible, watchVisible)
</script>

<style scoped>
.custom-batch-modal {
  background: rgba(0, 0, 0, 0.6) !important;
  backdrop-filter: blur(8px) !important;
}

.batch-entry-dialog {
  --el-dialog-border-radius: 28px;
}

.batch-entry-dialog :deep(.el-dialog) {
  border-radius: 28px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(255, 255, 255, 0.95));
  backdrop-filter: blur(25px);
  border: 2px solid rgba(255, 255, 255, 0.3);
  box-shadow:
    0 35px 80px rgba(0, 0, 0, 0.2),
    0 20px 40px rgba(0, 0, 0, 0.15),
    0 8px 16px rgba(0, 0, 0, 0.1),
    inset 0 2px 0 rgba(255, 255, 255, 0.9);
  overflow: hidden;
  position: relative;
}

.batch-entry-dialog :deep(.el-dialog::before) {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #0ea5e9, #38bdf8, #7dd3fc, #38bdf8, #0ea5e9);
  background-size: 200% 100%;
  animation: shimmer 3s ease-in-out infinite;
}

.batch-entry-dialog :deep(.el-dialog__header) {
  display: none;
}

.batch-entry-dialog :deep(.el-dialog__body) {
  padding: 0;
  background: transparent;
}

.batch-entry-dialog :deep(.el-dialog__footer) {
  background: rgba(255, 255, 255, 0.8);
  border-radius: 0 0 28px 28px;
  border-top: 2px solid rgba(14, 165, 233, 0.1);
  padding: 24px 32px;
  backdrop-filter: blur(10px);
}

.dialog-header {
  position: relative;
  padding: 40px 48px 32px;
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.08), rgba(56, 189, 248, 0.05));
  border-bottom: 2px solid rgba(14, 165, 233, 0.1);
  display: flex;
  align-items: center;
  gap: 24px;
  overflow: hidden;
}

.header-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(45deg, transparent, rgba(14, 165, 233, 0.05), transparent);
  animation: glow 3s ease-in-out infinite;
}

.header-icon {
  position: relative;
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #0ea5e9, #38bdf8);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow:
    0 12px 32px rgba(14, 165, 233, 0.4),
    0 6px 16px rgba(56, 189, 248, 0.3),
    inset 0 2px 0 rgba(255, 255, 255, 0.3);
  animation: iconPulse 3s ease-in-out infinite;
}

.icon-ring {
  position: absolute;
  top: -4px;
  left: -4px;
  right: -4px;
  bottom: -4px;
  border: 2px solid rgba(14, 165, 233, 0.3);
  border-radius: 24px;
  animation: iconPulse 3s ease-in-out infinite;
}

.header-text {
  flex: 1;
  z-index: 1;
}

.dialog-title {
  font-size: 32px;
  font-weight: 800;
  background: linear-gradient(135deg, #0ea5e9, #38bdf8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 8px 0;
  letter-spacing: -0.5px;
}

.dialog-subtitle {
  font-size: 16px;
  color: #64748b;
  margin: 0;
  font-weight: 500;
  line-height: 1.5;
}

@keyframes glow {
  0%,
  100% {
    opacity: 0.5;
    transform: translateX(-100%);
  }
  50% {
    opacity: 1;
    transform: translateX(100%);
  }
}

@keyframes iconPulse {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

.batch-entry-content {
  min-height: 400px;
}

.content-wrapper {
  padding: 32px 48px;
  background: rgba(255, 255, 255, 0.4);
}

.step-header {
  margin-bottom: 40px;
  padding: 32px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0.8));
  backdrop-filter: blur(15px);
  border-radius: 20px;
  border: 2px solid rgba(14, 165, 233, 0.15);
  box-shadow:
    0 8px 32px rgba(14, 165, 233, 0.1),
    0 4px 16px rgba(0, 0, 0, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
  position: relative;
  overflow: hidden;
}

.step-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #0ea5e9, #38bdf8, #7dd3fc, #38bdf8, #0ea5e9);
}

.step-header :deep(.el-steps) {
  position: relative;
  z-index: 1;
}

.step-header :deep(.el-step__title) {
  font-weight: 700;
  color: #0ea5e9;
  font-size: 16px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.step-header :deep(.el-step__title.is-finish) {
  color: #10b981;
  font-weight: 800;
}

.step-header :deep(.el-step__title.is-process) {
  color: #0ea5e9;
  font-weight: 800;
  font-size: 17px;
}

.step-header :deep(.el-step__icon) {
  border: 3px solid currentColor;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.2);
}

.step-header :deep(.el-step__icon.is-process) {
  background: linear-gradient(135deg, #0ea5e9, #38bdf8);
  color: white;
  box-shadow: 0 6px 20px rgba(14, 165, 233, 0.4);
}

.step-header :deep(.el-step__icon.is-finish) {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
}

.step-content {
  animation: fadeInUp 0.6s ease-out;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.8), rgba(255, 255, 255, 0.7));
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 40px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  box-shadow:
    0 12px 40px rgba(0, 0, 0, 0.1),
    0 6px 20px rgba(0, 0, 0, 0.06),
    inset 0 2px 0 rgba(255, 255, 255, 0.9);
  position: relative;
  overflow: hidden;
}

.step-content::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, #10b981, #059669, #047857, #059669, #10b981);
}

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

.type-selection h3,
.product-selection h3,
.quantity-input h3 {
  margin: 0 0 32px 0;
  background: linear-gradient(135deg, #1e293b, #475569);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: 24px;
  font-weight: 800;
  text-align: center;
  letter-spacing: -0.5px;
}

.type-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.type-card {
  cursor: pointer;
  border-radius: 20px;
  border: 2px solid rgba(14, 165, 233, 0.15);
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0.8));
  backdrop-filter: blur(15px);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 32px;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.type-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(14, 165, 233, 0.1), transparent);
  transition: left 0.6s ease;
}

.type-card:hover {
  transform: translateY(-6px) scale(1.02);
  box-shadow:
    0 12px 40px rgba(14, 165, 233, 0.25),
    0 6px 20px rgba(14, 165, 233, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
  border-color: rgba(14, 165, 233, 0.4);
}

.type-card:hover::before {
  left: 100%;
}

.type-card.active {
  border-color: #0ea5e9;
  background: linear-gradient(145deg, rgba(14, 165, 233, 0.12), rgba(56, 189, 248, 0.08));
  box-shadow:
    0 16px 50px rgba(14, 165, 233, 0.35),
    0 8px 25px rgba(14, 165, 233, 0.25),
    inset 0 2px 0 rgba(255, 255, 255, 0.9);
  transform: translateY(-4px) scale(1.01);
}

.type-card.active::before {
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  animation: shimmer 2s ease-in-out infinite;
}

.type-icon {
  margin-bottom: 20px;
  color: #0ea5e9;
  position: relative;
  z-index: 1;
}

.type-card.active .type-icon {
  color: #0284c7;
  animation: iconPulse 2s ease-in-out infinite;
}

.type-info h4 {
  margin: 0 0 12px 0;
  font-size: 18px;
  font-weight: 800;
  color: #1e293b;
  position: relative;
  z-index: 1;
}

.type-card.active .type-info h4 {
  color: #0284c7;
}

.type-info p {
  margin: 0;
  font-size: 15px;
  color: #64748b;
  line-height: 1.5;
  position: relative;
  z-index: 1;
  font-weight: 500;
}

.type-card.active .type-info p {
  color: #475569;
}

.process-selection {
  margin-top: 32px;
  padding: 24px;
  background: rgba(14, 165, 233, 0.05);
  border-radius: 16px;
  border: 1px solid rgba(14, 165, 233, 0.1);
}

.process-selection h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.selection-header,
.input-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 16px 20px;
  background: rgba(14, 165, 233, 0.05);
  border-radius: 12px;
  border: 1px solid rgba(14, 165, 233, 0.1);
}

.selection-info,
.input-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.product-table,
.quantity-table {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(14, 165, 233, 0.1);
  box-shadow: 0 4px 16px rgba(14, 165, 233, 0.05);
}

.product-table :deep(.el-table__header),
.quantity-table :deep(.el-table__header) {
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.08) 0%, rgba(56, 189, 248, 0.05) 100%);
}

.product-table :deep(.el-table__header th),
.quantity-table :deep(.el-table__header th) {
  background: transparent;
  color: #0ea5e9;
  font-weight: 700;
  font-size: 14px;
  border-bottom: 2px solid rgba(14, 165, 233, 0.2);
  padding: 16px 12px;
}

.product-table :deep(.el-table__row),
.quantity-table :deep(.el-table__row) {
  transition: all 0.3s ease;
  border-bottom: 1px solid rgba(14, 165, 233, 0.05);
}

.product-table :deep(.el-table__row:hover),
.quantity-table :deep(.el-table__row:hover) {
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.06) 0%, rgba(56, 189, 248, 0.04) 100%);
  transform: scale(1.001);
}

.product-table :deep(.el-table td),
.quantity-table :deep(.el-table td) {
  padding: 14px 12px;
  border-bottom: 1px solid rgba(14, 165, 233, 0.05);
}

.quantity-table :deep(.el-input-number) {
  width: 100%;
}

.quantity-table :deep(.el-input-number .el-input__wrapper) {
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(14, 165, 233, 0.2);
  transition: all 0.3s ease;
}

.quantity-table :deep(.el-input-number .el-input__wrapper:hover) {
  border-color: rgba(14, 165, 233, 0.4);
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.1);
}

.quantity-table :deep(.el-input-number .el-input__wrapper.is-focus) {
  border-color: #0ea5e9;
  box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.1);
}

/* 数量样式 */
.out-of-stock {
  color: #ef4444;
  font-weight: 700;
  background: rgba(239, 68, 68, 0.1);
  padding: 4px 8px;
  border-radius: 6px;
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.low-stock {
  color: #f59e0b;
  font-weight: 700;
  background: rgba(245, 158, 11, 0.1);
  padding: 4px 8px;
  border-radius: 6px;
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.normal-stock {
  color: #10b981;
  font-weight: 700;
  background: rgba(16, 185, 129, 0.1);
  padding: 4px 8px;
  border-radius: 6px;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.worker-date-selection {
  margin-top: 24px;
  padding: 20px;
  background: rgba(14, 165, 233, 0.05);
  border-radius: 12px;
  border: 1px solid rgba(14, 165, 233, 0.1);
}

.selection-row {
  display: flex;
  gap: 24px;
  align-items: flex-end;
}

.worker-date-selection :deep(.el-form-item__label) {
  font-weight: 600;
  color: #0ea5e9;
}

.worker-date-selection :deep(.el-select) {
  width: 100%;
}

.worker-date-selection :deep(.el-select .el-input__wrapper) {
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(14, 165, 233, 0.2);
  transition: all 0.3s ease;
}

.worker-date-selection :deep(.el-select .el-input__wrapper:hover) {
  border-color: rgba(14, 165, 233, 0.4);
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.1);
}

.worker-date-selection :deep(.el-select .el-input__wrapper.is-focus) {
  border-color: #0ea5e9;
  box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.1);
}

.worker-date-selection :deep(.el-date-editor) {
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(14, 165, 233, 0.2);
  transition: all 0.3s ease;
}

.worker-date-selection :deep(.el-date-editor:hover) {
  border-color: rgba(14, 165, 233, 0.4);
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.1);
}

.worker-date-selection :deep(.el-date-editor.is-active) {
  border-color: #0ea5e9;
  box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.1);
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
  background: rgba(14, 165, 233, 0.1);
}

.user-name {
  font-weight: 600;
  color: #0ea5e9;
}

.user-username {
  font-size: 12px;
  color: #64748b;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 16px;
}

.dialog-footer :deep(.el-button) {
  border-radius: 12px;
  padding: 12px 24px;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.3s ease;
}

.dialog-footer :deep(.el-button--primary) {
  background: linear-gradient(135deg, #0ea5e9 0%, #38bdf8 100%);
  border: none;
  box-shadow: 0 4px 16px rgba(14, 165, 233, 0.3);
}

.dialog-footer :deep(.el-button--primary:hover) {
  background: linear-gradient(135deg, #0284c7 0%, #0ea5e9 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(14, 165, 233, 0.4);
}

.dialog-footer :deep(.el-button:not(.el-button--primary)) {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(14, 165, 233, 0.2);
  color: #0ea5e9;
}

.dialog-footer :deep(.el-button:not(.el-button--primary):hover) {
  background: rgba(14, 165, 233, 0.1);
  border-color: rgba(14, 165, 233, 0.3);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.2);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .batch-entry-dialog :deep(.el-dialog) {
    width: 95% !important;
    margin: 20px auto;
  }

  .batch-entry-dialog :deep(.el-dialog__body) {
    padding: 20px;
  }

  .type-options {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .type-card {
    padding: 20px;
  }

  .selection-header,
  .input-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }

  .selection-info,
  .input-info {
    width: 100%;
    justify-content: space-between;
  }

  .worker-date-selection {
    padding: 16px;
  }

  .selection-row {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }

  .dialog-footer {
    flex-direction: column;
    gap: 12px;
  }

  .dialog-footer :deep(.el-button) {
    width: 100%;
  }
}
</style>
