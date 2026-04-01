<template>
  <el-dialog
    v-model="dialogVisible"
    title="一括棚卸登録"
    width="min(1040px, 92vw)"
    top="5vh"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    class="batch-entry-dialog"
    modal-class="custom-batch-modal"
  >
    <div class="batch-entry-content">
      <header class="batch-toolbar">
        <div class="batch-toolbar-brand">
          <div class="batch-brand-icon">
            <el-icon :size="20"><Box /></el-icon>
          </div>
          <div class="batch-toolbar-text">
            <h2 class="batch-title">一括棚卸登録</h2>
            <p class="batch-subtitle">タイプ選択 → 製品選択 → 数量入力</p>
          </div>
        </div>
      </header>

      <div class="content-wrapper">
        <!-- 第一步：选择类型和工程 -->
        <div v-if="currentStep === 1" class="step-content">
          <div class="step-header">
            <el-steps :active="currentStep" finish-status="success" simple class="batch-steps">
              <el-step title="タイプ選択" />
              <el-step title="製品選択" />
              <el-step title="数量入力" />
            </el-steps>
          </div>

          <div class="type-selection">
            <h3 class="section-heading">棚卸タイプを選択</h3>
            <div class="type-options">
              <el-card
                v-for="type in itemTypes"
                :key="type.value"
                shadow="never"
                class="type-card"
                :class="{ active: selectedType === type.value }"
                @click="selectType(type.value)"
              >
                <div class="type-icon">
                  <el-icon :size="22">
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
              <h4 class="process-heading">工程を選択</h4>
              <el-select
                v-model="selectedProcess"
                placeholder="工程を選択"
                size="small"
                clearable
                filterable
                class="process-select-full"
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
            <el-steps :active="currentStep" finish-status="success" simple class="batch-steps">
              <el-step title="タイプ選択" />
              <el-step title="製品選択" />
              <el-step title="数量入力" />
            </el-steps>
          </div>

          <div class="product-selection">
            <div class="selection-header">
              <h3 class="section-heading">製品を選択</h3>
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
                size="small"
                v-loading="loading"
                :height="300"
                @selection-change="handleSelectionChange"
                class="batch-data-table"
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
            <el-steps :active="currentStep" finish-status="success" simple class="batch-steps">
              <el-step title="タイプ選択" />
              <el-step title="製品選択" />
              <el-step title="数量入力" />
            </el-steps>
          </div>

          <div class="quantity-input">
            <div class="input-header">
              <h3 class="section-heading">数量を入力</h3>
              <div class="input-info">
                <el-tag type="info" effect="plain">
                  入力数量1 合計: {{ batchAuxQty1Sum }}
                </el-tag>
                <el-tag type="info" effect="plain">
                  入力数量2 合計: {{ batchAuxQty2Sum }}
                </el-tag>
                <el-tag type="success" effect="plain">
                  数量合計: {{ batchQuantitySum }}
                </el-tag>
                <el-tag type="info" effect="plain">
                  選択済み: {{ selectedProducts.length }}件
                </el-tag>
                <el-button @click="goBack" size="small">
                  <el-icon><ArrowLeft /></el-icon>
                  戻る
                </el-button>
              </div>
            </div>

            <div class="quantity-table-wrap" @keydown.capture="onQtyTableKeydown">
              <el-table
                :data="quantityData"
                border
                stripe
                size="small"
                :height="280"
                class="batch-data-table"
              >
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
                <el-table-column label="入力数量1" width="108" align="center">
                  <template #default="scope">
                    <div class="qty-nav-cell" :data-row="scope.$index" data-col="1">
                      <el-input
                        :model-value="qtyCellDisplay(scope.row.aux_qty1)"
                        placeholder="数量1"
                        size="small"
                        class="qty-text-input"
                        maxlength="6"
                        inputmode="numeric"
                        autocomplete="off"
                        style="width: 100%"
                        @update:model-value="(v) => onQtyCellInput(scope.row, 'aux_qty1', v)"
                      />
                    </div>
                  </template>
                </el-table-column>
                <el-table-column label="入力数量2" width="108" align="center">
                  <template #default="scope">
                    <div class="qty-nav-cell" :data-row="scope.$index" data-col="2">
                      <el-input
                        :model-value="qtyCellDisplay(scope.row.aux_qty2)"
                        placeholder="数量2"
                        size="small"
                        class="qty-text-input"
                        maxlength="6"
                        inputmode="numeric"
                        autocomplete="off"
                        style="width: 100%"
                        @update:model-value="(v) => onQtyCellInput(scope.row, 'aux_qty2', v)"
                      />
                    </div>
                  </template>
                </el-table-column>
                <el-table-column label="数量合計" width="120" align="center">
                  <template #default="scope">
                    <span :class="getQuantityClass(scope.row.quantity)" class="qty-total-cell">
                      {{ scope.row.quantity }}
                    </span>
                  </template>
                </el-table-column>
              </el-table>
            </div>

            <!-- 作業者和日期选择 -->
            <div class="worker-date-selection">
              <div class="selection-row">
                <el-form-item label="作業者" required class="compact-form-item">
                  <el-select
                    v-model="selectedWorker"
                    placeholder="作業者を選択"
                    size="small"
                    clearable
                    filterable
                    class="worker-select"
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

                <el-form-item label="棚卸日" required class="compact-form-item">
                  <el-date-picker
                    v-model="selectedDate"
                    type="date"
                    placeholder="日付を選択"
                    format="YYYY-MM-DD"
                    value-format="YYYY-MM-DD"
                    size="small"
                    class="date-picker-compact"
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
        <el-button size="small" @click="handleCancel" v-if="currentStep === 1">キャンセル</el-button>
        <el-button size="small" @click="goBack" v-if="currentStep > 1">
          <el-icon><ArrowLeft /></el-icon>
          戻る
        </el-button>
        <el-button
          type="primary"
          size="small"
          @click="handleNext"
          :disabled="!canProceed"
          :loading="submitting"
        >
          <el-icon><ArrowRight /></el-icon>
          {{ currentStep === 3 ? '保存' : '次へ' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
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

/** ERP 在庫ルータ配下（/api/erp/inventory） */
const ERP_INVENTORY_BASE = '/api/erp/inventory'

/** 製品名昇順（日本語ロケール） */
function sortByProductNameAsc<T extends { product_name?: string }>(rows: T[]): T[] {
  return [...rows].sort((a, b) =>
    String(a.product_name ?? '').localeCompare(String(b.product_name ?? ''), 'ja'),
  )
}

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

/** 行の補助数量を数値化（未入力は 0） */
function rowAuxNum(v: unknown): number {
  if (v == null || v === '') return 0
  const n = Number(v)
  return Number.isFinite(n) ? n : 0
}

/** 一括入力：入力数量1 の全行合計 */
const batchAuxQty1Sum = computed(() =>
  quantityData.value.reduce((sum, item) => sum + rowAuxNum(item.aux_qty1), 0),
)

/** 一括入力：入力数量2 の全行合計 */
const batchAuxQty2Sum = computed(() =>
  quantityData.value.reduce((sum, item) => sum + rowAuxNum(item.aux_qty2), 0),
)

/** 一括入力：各行の数量合計（1+2）の全行合計 */
const batchQuantitySum = computed(() =>
  quantityData.value.reduce((sum, item) => sum + (Number(item.quantity) || 0), 0),
)

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

// 计算总数量（aux は null / 数値、0 は合算時のみ使用）
const calculateTotal = (row: any) => {
  const auxQty1 = row.aux_qty1 == null || row.aux_qty1 === '' ? 0 : Number(row.aux_qty1) || 0
  const auxQty2 = row.aux_qty2 == null || row.aux_qty2 === '' ? 0 : Number(row.aux_qty2) || 0
  row.quantity = auxQty1 + auxQty2
}

/** テキスト框表示：未入力・0 は空文字（0 を表示しない） */
function qtyCellDisplay(v: unknown): string {
  if (v == null || v === '') return ''
  const n = Number(v)
  if (!Number.isFinite(n) || n === 0) return ''
  return String(Math.trunc(n))
}

function onQtyCellInput(row: any, key: 'aux_qty1' | 'aux_qty2', raw: string) {
  const digits = String(raw ?? '').replace(/\D/g, '')
  if (digits === '') {
    row[key] = null
    calculateTotal(row)
    return
  }
  let n = parseInt(digits, 10)
  if (!Number.isFinite(n)) n = 0
  n = Math.min(99999, Math.max(0, n))
  row[key] = n
  calculateTotal(row)
}

/** 数量入力：指定セル（入力数量1 / 2）にフォーカス */
function focusQtyInput(row: number, col: 1 | 2) {
  nextTick(() => {
    const wrap = document.querySelector(
      `.quantity-table-wrap .qty-nav-cell[data-row="${row}"][data-col="${col}"]`,
    ) as HTMLElement | null
    const input = wrap?.querySelector('input') as HTMLInputElement | undefined
    input?.focus()
    input?.select()
  })
}

function focusWorkerField() {
  nextTick(() => {
    const el = document.querySelector(
      '.worker-date-selection .worker-select .el-input__inner',
    ) as HTMLInputElement | null
    el?.focus()
  })
}

/** Enter・矢印キーでセル間移動（テーブル内キャプチャ） */
function onQtyTableKeydown(e: KeyboardEvent) {
  if (currentStep.value !== 3) return
  if (e.isComposing || e.key === 'Process') return

  const target = e.target as HTMLElement | null
  if (!target) return
  const cell = target.closest('.qty-nav-cell') as HTMLElement | null
  if (!cell) return

  const row = Number(cell.dataset.row)
  const col = Number(cell.dataset.col)
  if (Number.isNaN(row) || (col !== 1 && col !== 2)) return

  const maxRow = quantityData.value.length - 1
  if (maxRow < 0) return

  const navKeys = ['Enter', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight']
  if (!navKeys.includes(e.key)) return

  if (e.key === 'Enter') {
    e.preventDefault()
    if (row < maxRow) focusQtyInput(row + 1, 1)
    else focusWorkerField()
    return
  }

  if (e.key === 'ArrowDown') {
    e.preventDefault()
    if (row < maxRow) focusQtyInput(row + 1, col as 1 | 2)
    return
  }
  if (e.key === 'ArrowUp') {
    e.preventDefault()
    if (row > 0) focusQtyInput(row - 1, col as 1 | 2)
    return
  }
  if (e.key === 'ArrowRight') {
    e.preventDefault()
    if (col === 1) focusQtyInput(row, 2)
    else if (row < maxRow) focusQtyInput(row + 1, 1)
    return
  }
  if (e.key === 'ArrowLeft') {
    e.preventDefault()
    if (col === 2) focusQtyInput(row, 1)
    else if (row > 0) focusQtyInput(row - 1, 2)
    return
  }
}

watch(currentStep, (s) => {
  if (s === 3) {
    nextTick(() => {
      if (quantityData.value.length > 0) focusQtyInput(0, 1)
    })
  }
})

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
        productList.value = sortByProductNameAsc(
          materialOptions.value.map((material) => ({
            product_cd: material.material_cd,
            product_name: material.material_name,
            type: 'material',
          })),
        )
        break
      case '部品':
        productList.value = sortByProductNameAsc(
          componentOptions.value.map((component) => ({
            product_cd: component.component_cd,
            product_name: component.component_name,
            type: 'component',
          })),
        )
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
    const response = await request.get(`${ERP_INVENTORY_BASE}/products-by-process`, {
      params: { process_cd: selectedProcess.value },
      timeout: 15000,
    })

    const raw = Array.isArray(response)
      ? response
      : (response as { data?: unknown })?.data ?? []
    const products = Array.isArray(raw) ? raw : []

    if (products.length > 0) {
      productList.value = sortByProductNameAsc(
        products.map((product: any) => ({
          product_cd: product.product_cd,
          product_name: product.product_name,
          type: 'product',
        })),
      )
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
  productList.value = sortByProductNameAsc(
    productOptions.value.map((product) => ({
      product_cd: product.product_cd,
      product_name: product.product_name,
      type: 'product',
    })),
  )
  console.log(`✅ 加载了 ${productList.value.length} 个产品`)
}

// 准备数量数据
const prepareQuantityData = () => {
  quantityData.value = sortByProductNameAsc(
    selectedProducts.value.map((product) => ({
      product_cd: product.product_cd,
      product_name: product.product_name,
      aux_qty1: null as number | null,
      aux_qty2: null as number | null,
      quantity: 0,
    })),
  )
}

// 提交数据
const handleSubmit = async () => {
  if (!selectedWorker.value) {
    ElMessage.error('作業者を選択してください')
    return
  }

  if (!selectedDate.value) {
    ElMessage.error('棚卸日を選択してください')
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
  background: rgba(15, 23, 42, 0.45) !important;
  backdrop-filter: blur(6px) !important;
}

.batch-entry-dialog {
  --be-surface: rgba(255, 255, 255, 0.96);
  --be-border: rgba(15, 23, 42, 0.08);
  --be-accent: #0ea5e9;
  --be-muted: #64748b;
  --el-dialog-border-radius: 12px;
}

.batch-entry-dialog :deep(.el-dialog) {
  border-radius: 12px;
  background: var(--be-surface);
  border: 1px solid var(--be-border);
  box-shadow: 0 22px 50px rgba(15, 23, 42, 0.14);
  overflow: hidden;
  position: relative;
  max-width: min(1040px, 92vw);
  margin: 0 auto;
}

.batch-entry-dialog :deep(.el-dialog::before) {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #0ea5e9, #38bdf8, #22d3ee);
  background-size: 200% 100%;
  animation: be-shimmer 4s ease-in-out infinite;
}

@keyframes be-shimmer {
  0%,
  100% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
}

.batch-entry-dialog :deep(.el-dialog__header) {
  display: none;
}

.batch-entry-dialog :deep(.el-dialog__body) {
  padding: 0;
}

.batch-entry-dialog :deep(.el-dialog__footer) {
  padding: 10px 14px;
  border-top: 1px solid var(--be-border);
  background: #f8fafc;
  border-radius: 0 0 12px 12px;
}

.batch-entry-content {
  display: flex;
  flex-direction: column;
  max-height: min(82vh, 760px);
}

.batch-toolbar {
  flex-shrink: 0;
  padding: 10px 14px;
  border-bottom: 1px solid var(--be-border);
  background: linear-gradient(180deg, rgba(14, 165, 233, 0.05), transparent);
}

.batch-toolbar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.batch-brand-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(145deg, #0ea5e9, #0284c7);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 3px 10px rgba(14, 165, 233, 0.35);
}

.batch-title {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.02em;
}

.batch-subtitle {
  margin: 2px 0 0;
  font-size: 12px;
  color: var(--be-muted);
}

.content-wrapper {
  flex: 1;
  overflow-y: auto;
  padding: 10px 14px 12px;
  background: #f8fafc;
}

.step-header {
  margin-bottom: 10px;
  padding: 8px 10px;
  background: #fff;
  border: 1px solid var(--be-border);
  border-radius: 10px;
}

.batch-steps :deep(.el-step__title) {
  font-size: 12px !important;
  font-weight: 600;
  color: #64748b !important;
}

.batch-steps :deep(.el-step__title.is-process),
.batch-steps :deep(.el-step__title.is-finish) {
  color: #0f172a !important;
}

.batch-steps :deep(.el-step__icon) {
  width: 22px;
  height: 22px;
  font-size: 12px;
  border-width: 1px;
}

.step-content {
  background: #fff;
  border: 1px solid var(--be-border);
  border-radius: 10px;
  padding: 12px 14px;
  animation: be-fade-in 0.35s ease-out;
}

@keyframes be-fade-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.section-heading {
  margin: 0 0 10px;
  font-size: 0.9375rem;
  font-weight: 700;
  color: #0f172a;
  text-align: left;
}

.type-selection .section-heading {
  text-align: center;
  margin-bottom: 12px;
}

.type-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}

.type-card {
  cursor: pointer;
  border-radius: 10px;
  border: 1px solid var(--be-border) !important;
  background: #fff !important;
  padding: 14px 12px !important;
  text-align: center;
  transition:
    border-color 0.2s,
    box-shadow 0.2s,
    background 0.2s;
}

.type-card :deep(.el-card__body) {
  padding: 0 !important;
}

.type-card:hover {
  border-color: rgba(14, 165, 233, 0.45) !important;
  box-shadow: 0 4px 14px rgba(14, 165, 233, 0.12);
}

.type-card.active {
  border-color: #0ea5e9 !important;
  background: rgba(14, 165, 233, 0.06) !important;
  box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.15);
}

.type-icon {
  margin-bottom: 8px;
  color: var(--be-accent);
}

.type-info h4 {
  margin: 0 0 4px;
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
}

.type-info p {
  margin: 0;
  font-size: 12px;
  color: var(--be-muted);
  line-height: 1.4;
}

.process-selection {
  margin-top: 10px;
  padding: 10px 12px;
  background: #f1f5f9;
  border-radius: 8px;
  border: 1px solid var(--be-border);
}

.process-heading {
  margin: 0 0 8px;
  font-size: 13px;
  font-weight: 600;
  color: #334155;
}

.process-select-full {
  width: 100%;
}

.selection-header,
.input-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 10px;
  padding: 8px 10px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid var(--be-border);
}

.selection-header .section-heading,
.input-header .section-heading {
  margin: 0;
}

.selection-info,
.input-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.product-list,
.quantity-table-wrap {
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--be-border);
}

.quantity-table-wrap:focus-within {
  outline: none;
}

.qty-nav-cell {
  width: 100%;
  min-width: 0;
}

.qty-nav-cell :deep(.qty-text-input) {
  width: 100%;
}

.qty-text-input :deep(.el-input__wrapper) {
  padding-left: 8px;
  padding-right: 8px;
}

.batch-data-table {
  --el-table-border-color: var(--be-border);
  --el-table-header-bg-color: #f1f5f9;
}

.batch-data-table :deep(.el-table__header th) {
  font-size: 12px;
  font-weight: 600;
  color: #334155;
  padding: 8px 10px !important;
  background: #f1f5f9 !important;
}

.batch-data-table :deep(.el-table td) {
  padding: 6px 10px !important;
  font-size: 13px;
}

.batch-data-table :deep(.el-table__row:hover > td) {
  background: rgba(14, 165, 233, 0.06) !important;
}


.worker-date-selection {
  margin-top: 10px;
  padding: 10px 12px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid var(--be-border);
}

.selection-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 20px;
  align-items: flex-end;
}

.compact-form-item {
  margin-bottom: 0 !important;
}

.compact-form-item :deep(.el-form-item__label) {
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  padding-bottom: 4px;
}

.worker-select {
  width: min(260px, 100%);
}

.date-picker-compact {
  width: 160px;
}

.user-option {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 0;
}

.user-name {
  font-weight: 600;
  color: #0f172a;
}

.user-username {
  font-size: 12px;
  color: var(--be-muted);
}

.out-of-stock {
  color: #dc2626;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(254, 226, 226, 0.85);
}

.low-stock {
  color: #d97706;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(254, 243, 199, 0.85);
}

.normal-stock {
  color: #059669;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(209, 250, 229, 0.85);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
}

@media (max-width: 768px) {
  .batch-entry-dialog :deep(.el-dialog) {
    width: min(100%, 96vw) !important;
    max-width: 96vw !important;
    margin: 12px auto !important;
  }

  .type-options {
    grid-template-columns: 1fr;
  }

  .selection-header,
  .input-header {
    flex-direction: column;
    align-items: stretch;
  }

  .selection-info,
  .input-info {
    width: 100%;
    justify-content: space-between;
  }

  .worker-select,
  .date-picker-compact {
    width: 100%;
  }

  .dialog-footer :deep(.el-button) {
    flex: 1;
    min-width: 0;
  }
}
</style>

