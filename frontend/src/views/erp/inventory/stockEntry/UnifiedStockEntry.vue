<template>
  <div
    class="unified-stock-page"
    v-loading="pageLoading"
    element-loading-text="システム初期化中..."
    element-loading-background="rgba(248, 250, 252, 0.8)"
  >
    <!-- 现代渐变背景 -->
    <div class="bg-gradient"></div>
    <div class="bg-pattern"></div>

    <!-- 现代页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-main">
          <div class="header-icon">
            <el-icon size="28">
              <Box />
            </el-icon>
          </div>
          <div class="header-text">
            <h1 class="main-title">在庫取引登録</h1>
            <p class="subtitle">製品・材料・部品・仕掛品の入出庫一元管理</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="content-container">
      <!-- 紧凑型库存类型选择器 -->
      <transition name="fade-scale" appear>
        <div class="stock-type-selector hover-lift">
          <div class="selector-header">
            <h3 class="selector-title">在庫種別</h3>
          </div>
          <div class="stock-types">
            <div
              v-for="type in stockTypes"
              :key="type.value"
              :class="['stock-type-chip', { active: form.stock_type === type.value }]"
              @click="selectStockType(type.value)"
            >
              <div class="chip-icon" :style="{ color: type.color }">
                <el-icon size="18">
                  <component :is="type.icon" />
                </el-icon>
              </div>
              <div class="chip-content">
                <span class="chip-title">{{ type.label }}</span>
              </div>
              <div v-if="form.stock_type === type.value" class="chip-indicator">
                <el-icon size="14">
                  <Check />
                </el-icon>
              </div>
            </div>
          </div>
        </div>
      </transition>

      <!-- 现代表单卡片 -->
      <transition name="slide-in" mode="out-in">
        <div v-if="form.stock_type" class="form-card hover-lift" :key="form.stock_type">
          <div class="form-header">
            <div class="form-title">
              <el-icon class="title-icon" :style="{ color: getCurrentStockType()?.color }">
                <component :is="getCurrentStockType()?.icon" />
              </el-icon>
              <span>{{ getCurrentStockType()?.label }}登録</span>
            </div>
          </div>

          <el-form
            :model="form"
            :rules="rules"
            ref="formRef"
            label-width="100px"
            class="modern-form"
            label-position="left"
          >
            <!-- 紧凑布局 -->
            <div class="form-grid">
              <!-- 左侧主要信息 -->
              <div class="form-left">
                <div class="form-group">
                  <el-form-item label="対象" prop="target_cd">
                    <el-select
                      v-model="form.target_cd"
                      filterable
                      placeholder="対象を選択"
                      class="modern-select"
                      clearable
                    >
                      <el-option
                        v-for="item in filteredTargetOptions"
                        :key="item.cd"
                        :label="`${item.cd} | ${item.name}`"
                        :value="item.cd"
                      />
                    </el-select>
                  </el-form-item>

                  <el-form-item label="保管場所" prop="location_cd">
                    <el-select
                      v-model="form.location_cd"
                      placeholder="保管場所"
                      class="modern-select"
                    >
                      <el-option
                        v-for="loc in locationOptions"
                        :key="loc.cd"
                        :label="loc.name"
                        :value="loc.cd"
                      />
                    </el-select>
                  </el-form-item>

                  <!-- 仕掛品工程选择 -->
                  <el-form-item v-if="form.stock_type === '仕掛品'" label="工程" prop="process_cd">
                    <el-select
                      v-model="form.process_cd"
                      placeholder="工程を選択"
                      class="modern-select"
                    >
                      <el-option
                        v-for="p in processOptions"
                        :key="p.cd"
                        :label="p.name"
                        :value="p.cd"
                      />
                    </el-select>
                  </el-form-item>

                  <!-- 仕掛品設備选择 -->
                  <el-form-item v-if="form.stock_type === '仕掛品'" label="設備" prop="machine_cd">
                    <el-select
                      v-model="form.machine_cd"
                      placeholder="設備を選択"
                      class="modern-select"
                      clearable
                    >
                      <el-option
                        v-for="m in machineOptions"
                        :key="m.cd"
                        :label="m.name"
                        :value="m.cd"
                      />
                    </el-select>
                  </el-form-item>
                </div>
              </div>

              <!-- 右侧操作信息 -->
              <div class="form-right">
                <div class="form-group">
                  <el-form-item label="操作種別" prop="transaction_type">
                    <el-select
                      v-model="form.transaction_type"
                      placeholder="操作種別"
                      class="modern-select"
                    >
                      <el-option
                        v-for="type in getTransactionTypes()"
                        :key="type.value"
                        :label="type.label"
                        :value="type.value"
                      />
                    </el-select>
                  </el-form-item>

                  <div class="quantity-row">
                    <el-form-item label="数量" prop="quantity" class="quantity-item">
                      <el-input-number
                        v-model="form.quantity"
                        :step="1"
                        :precision="0"
                        class="modern-number"
                        placeholder="数量"
                      />
                    </el-form-item>
                    <el-form-item label="単位" class="unit-item">
                      <el-select v-model="form.unit" class="modern-select unit-select">
                        <el-option
                          v-for="unit in getUnitOptions()"
                          :key="unit.value"
                          :label="unit.label"
                          :value="unit.value"
                        />
                      </el-select>
                    </el-form-item>
                  </div>

                  <!-- 材料束本数 -->
                  <el-form-item v-if="form.stock_type === '材料'" label="束本数" prop="base_qty">
                    <el-input-number
                      v-model="form.base_qty"
                      :step="1"
                      class="modern-number"
                      placeholder="束本数"
                    />
                  </el-form-item>

                  <el-form-item label="操作日時" prop="transaction_time">
                    <el-date-picker
                      v-model="form.transaction_time"
                      type="datetime"
                      value-format="YYYY-MM-DD HH:mm:ss"
                      placeholder="操作日時"
                      class="modern-date"
                    />
                  </el-form-item>
                </div>
              </div>
            </div>

            <!-- 可选信息 -->
            <el-collapse class="optional-info" v-model="expandedPanels">
              <el-collapse-item title="詳細情報" name="details">
                <div class="detail-form">
                  <el-form-item label="関連伝票">
                    <div class="document-row">
                      <el-input
                        v-model="form.related_doc_type"
                        placeholder="伝票種別"
                        class="doc-type"
                      />
                      <el-input
                        v-model="form.related_doc_no"
                        placeholder="伝票番号"
                        class="doc-no"
                      />
                    </div>
                  </el-form-item>
                  <el-form-item label="備考">
                    <el-input
                      v-model="form.remarks"
                      type="textarea"
                      :rows="2"
                      placeholder="備考..."
                      maxlength="200"
                      show-word-limit
                    />
                  </el-form-item>
                </div>
              </el-collapse-item>
            </el-collapse>

            <!-- 操作按钮 -->
            <div class="action-bar">
              <el-button @click="resetForm" class="reset-btn">
                <el-icon><Refresh /></el-icon>
                リセット
              </el-button>
              <el-button type="primary" @click="submit" class="submit-btn" :loading="submitLoading">
                <el-icon><Check /></el-icon>
                {{ submitButtonText }}
              </el-button>
            </div>
          </el-form>
        </div>
      </transition>

      <!-- 紧凑历史记录 -->
      <transition name="slide-up" appear>
        <div v-if="todayLoggedTransactions.length" class="history-card hover-lift">
          <div class="history-header">
            <div class="history-title">
              <el-icon><Document /></el-icon>
              <span>本日履歴</span>
              <el-badge :value="filteredTransactions.length" class="history-badge" />
            </div>
            <div class="history-filters">
              <el-button-group size="small">
                <el-button
                  v-for="type in stockTypes"
                  :key="type.value"
                  :type="historyFilter === type.value ? 'primary' : 'default'"
                  @click="historyFilter = historyFilter === type.value ? '' : type.value"
                >
                  {{ type.label }}
                </el-button>
              </el-button-group>
            </div>
          </div>

          <div class="history-table">
            <el-table :data="filteredTransactions" stripe class="compact-table" max-height="300">
              <el-table-column prop="stock_type" label="種別" width="70" align="center">
                <template #default="scope">
                  <el-tag
                    :type="
                      getStockTypeTagType(scope.row.stock_type) as
                        | 'success'
                        | 'warning'
                        | 'primary'
                        | 'info'
                        | 'danger'
                    "
                    effect="light"
                    size="small"
                    round
                  >
                    {{ scope.row.stock_type }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="cd" label="コード" width="100" />
              <el-table-column prop="name" label="名称" min-width="120" show-overflow-tooltip />
              <el-table-column prop="location_cd" label="場所" width="110" />
              <el-table-column
                v-if="showProcessColumn"
                prop="process_name"
                label="工程"
                width="80"
              />
              <el-table-column prop="transaction_type" label="操作" width="70">
                <template #default="scope">
                  <el-tag
                    :type="
                      getTransactionTypeTagType(scope.row.transaction_type) as
                        | 'success'
                        | 'warning'
                        | 'primary'
                        | 'info'
                        | 'danger'
                    "
                    effect="dark"
                    size="small"
                    round
                  >
                    {{ scope.row.transaction_type }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column width="80" align="right">
                <template #default="scope">
                  <span class="quantity-display">{{ scope.row.quantity }}{{ scope.row.unit }}</span>
                </template>
              </el-table-column>
              <el-table-column label="" width="60" align="center">
                <template #default="scope">
                  <el-button
                    text
                    size="small"
                    @click="duplicateTransaction(scope.row)"
                    class="copy-btn"
                  >
                    <el-icon><DocumentCopy /></el-icon>
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'
import {
  getProductOptions,
  getMaterialOptions,
  getComponentOptions,
  getProcessOptions,
  getMachineOptions,
} from '@/api/options'
import type { OptionItem } from '@/types/master'
import {
  Box,
  Document,
  Check,
  Refresh,
  Menu,
  Grid,
  Setting,
  Tools,
  DocumentCopy,
} from '@element-plus/icons-vue'

interface StockTransactionForm {
  stock_type: string
  target_cd: string
  location_cd: string
  transaction_type: string
  quantity: number
  unit: string
  process_cd: string
  machine_cd: string
  base_qty?: number
  related_doc_type: string
  related_doc_no: string
  remarks: string
  transaction_time: string
}

interface LoggedTransaction {
  stock_type: string
  cd: string
  name: string
  location_cd: string
  process_name?: string
  transaction_type: string
  quantity: number
  unit: string
}

// 获取本地时间字符串，格式：YYYY-MM-DD HH:mm:ss
function getLocalDateTimeString() {
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  const hh = String(now.getHours()).padStart(2, '0')
  const mm = String(now.getMinutes()).padStart(2, '0')
  const ss = String(now.getSeconds()).padStart(2, '0')
  return `${y}-${m}-${d} ${hh}:${mm}:${ss}`
}

const createInitialForm = (): StockTransactionForm => ({
  stock_type: '',
  target_cd: '',
  location_cd: '',
  transaction_type: '',
  quantity: 0,
  unit: '本',
  process_cd: '',
  machine_cd: '',
  base_qty: 0,
  related_doc_type: '',
  related_doc_no: '',
  remarks: '',
  transaction_time: getLocalDateTimeString(),
})

const formRef = ref<InstanceType<typeof import('element-plus').ElForm>>()
const form = ref<StockTransactionForm>(createInitialForm())
const submitLoading = ref(false)
const pageLoading = ref(false)
const historyFilter = ref('')
const expandedPanels = ref([''])

const rules = {
  target_cd: [{ required: true, message: '対象を選択してください', trigger: 'change' }],
  location_cd: [{ required: true, message: '保管場所を選択してください', trigger: 'change' }],
  transaction_type: [{ required: true, message: '操作種別を選択してください', trigger: 'change' }],
  quantity: [{ required: true, message: '数量を入力してください', trigger: 'blur' }],
  transaction_time: [{ required: true, message: '操作日時を選択してください', trigger: 'change' }],
  process_cd: [
    {
      validator: (rule: any, value: any, callback: any) => {
        if (form.value.stock_type === '仕掛品' && !value) {
          callback(new Error('工程を選択してください'))
        } else {
          callback()
        }
      },
      trigger: 'change',
    },
  ],
  machine_cd: [
    {
      validator: (rule: any, value: any, callback: any) => {
        // 設備字段可以为空，不进行必填验证
        callback()
      },
      trigger: 'change',
    },
  ],
  base_qty: [
    {
      validator: (rule: any, value: any, callback: any) => {
        if (form.value.stock_type === '材料' && (!value || value <= 0)) {
          callback(new Error('束本数を入力してください'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

// 库存类型定义
const stockTypes = [
  {
    value: '製品',
    label: '製品',
    description: '完成品の在庫管理',
    icon: Box,
    color: '#409eff',
    symbol: '🏺',
  },
  {
    value: '材料',
    label: '材料',
    description: '原材料の在庫管理',
    icon: Setting,
    color: '#67c23a',
    symbol: '🧪',
  },
  {
    value: '部品',
    label: '部品',
    description: '部品・パーツの在庫管理',
    icon: Grid,
    color: '#e6a23c',
    symbol: '🧩',
  },
  {
    value: '仕掛品',
    label: '仕掛品',
    description: '工程間の仕掛品管理',
    icon: Tools,
    color: '#f56c6c',
    symbol: '⚙️',
  },
]

const targetOptions = ref<OptionItem[]>([])
const processOptions = ref<OptionItem[]>([])
const machineOptions = ref<OptionItem[]>([])
const locationOptions = [
  { cd: '製品倉庫', name: '製品倉庫' },
  { cd: '仮設倉庫', name: '仮設倉庫' },
  { cd: '部品倉庫', name: '部品倉庫' },
  { cd: '仕上倉庫', name: '仕上倉庫' },
  { cd: 'メッキ倉庫', name: 'メッキ倉庫' },
  { cd: '工程中間在庫', name: '工程中間在庫' },
  { cd: '材料置場', name: '材料置場' },
  { cd: '外注倉庫', name: '外注倉庫' },
  { cd: 'その他', name: 'その他' },
]

const todayLoggedTransactions = ref<LoggedTransaction[]>([])

// 计算属性
const getCurrentStockType = () => {
  return stockTypes.find((type) => type.value === form.value.stock_type)
}

const submitButtonText = computed(() => {
  const stockType = getCurrentStockType()
  return stockType ? `${stockType.label}登録` : '登録'
})

const filteredTransactions = computed(() => {
  if (!historyFilter.value) return todayLoggedTransactions.value
  return todayLoggedTransactions.value.filter((t) => t.stock_type === historyFilter.value)
})

const showProcessColumn = computed(() => {
  return filteredTransactions.value.some((t) => t.process_name)
})

// 过滤対象选项 - 製品和仕掛品过滤CD末位不是1的
const filteredTargetOptions = computed(() => {
  if (form.value.stock_type === '製品' || form.value.stock_type === '仕掛品') {
    return targetOptions.value.filter((item) => {
      // 过滤製品CD末位不是1的
      const lastChar = item.cd.slice(-1)
      return lastChar === '1'
    })
  }
  return targetOptions.value
})

// 方法
const selectStockType = (type: string) => {
  if (form.value.stock_type !== type) {
    // 重置表单但保留时间
    const currentTime = form.value.transaction_time
    form.value = createInitialForm()
    form.value.stock_type = type
    form.value.transaction_time = currentTime

    // 设置默认保管场所
    setDefaultLocation(type)
  }
}

const setDefaultLocation = (stockType: string) => {
  const defaultLocations: { [key: string]: string } = {
    製品: '製品倉庫',
    材料: '材料置場',
    部品: '部品倉庫',
    仕掛品: '工程中間在庫',
  }
  form.value.location_cd = defaultLocations[stockType] || ''
}

const getTransactionTypes = () => {
  const baseTypes = [
    { value: '入庫', label: '入庫', class: 'type-in' },
    { value: '出庫', label: '出庫', class: 'type-out' },
    { value: '調整', label: '調整', class: 'type-adjust' },
    { value: '廃棄', label: '廃棄', class: 'type-dispose' },
    { value: '保留', label: '保留', class: 'type-hold' },
    { value: '初期', label: '初期', class: 'type-init' },
  ]

  // 仕掛品特有的操作类型
  if (form.value.stock_type === '仕掛品') {
    return [
      { value: '実績', label: '実績', class: 'type-result' },
      { value: '不良', label: '不良', class: 'type-defect' },
      ...baseTypes,
    ]
  }

  return baseTypes
}

const getUnitOptions = () => {
  if (form.value.stock_type === '材料') {
    return [
      { value: '束', label: '束' },
      { value: 'kg', label: 'kg' },
      { value: 'm', label: 'm' },
      { value: '枚', label: '枚' },
    ]
  }

  return [
    { value: '本', label: '本' },
    { value: '個', label: '個' },
    { value: '枚', label: '枚' },
    { value: 'kg', label: 'kg' },
    { value: 'm', label: 'm' },
    { value: '束', label: '束' },
    { value: '箱', label: '箱' },
    { value: 'セット', label: 'セット' },
  ]
}

const getStockTypeTagType = (type: string) => {
  const typeMap: { [key: string]: string } = {
    製品: 'primary',
    材料: 'success',
    部品: 'warning',
    仕掛品: 'info',
  }
  return typeMap[type] || 'default'
}

const getTransactionTypeTagType = (type: string) => {
  const typeMap: { [key: string]: string } = {
    入庫: 'success',
    出庫: 'info',
    調整: 'warning',
    廃棄: 'danger',
    保留: 'info',
    実績: 'success',
    不良: 'danger',
    初期: 'primary',
  }
  return typeMap[type] || 'default'
}

// 监听库存类型变化，加载对应的选项
watch(
  () => form.value.stock_type,
  async (type) => {
    form.value.target_cd = ''
    form.value.process_cd = ''
    form.value.machine_cd = ''

    if (type === '製品') {
      targetOptions.value = await getProductOptions()
      form.value.unit = '本'
    } else if (type === '材料') {
      targetOptions.value = await getMaterialOptions()
      form.value.unit = '束'
      form.value.base_qty = 0
    } else if (type === '部品') {
      targetOptions.value = await getComponentOptions()
      form.value.unit = '個'
    } else if (type === '仕掛品') {
      targetOptions.value = await getProductOptions()
      processOptions.value = await getProcessOptions()
      machineOptions.value = await getMachineOptions()
      form.value.unit = '本'
    } else {
      targetOptions.value = []
    }
  },
)

// 材料选择变化时自动获取束本数
watch(
  () => form.value.target_cd,
  async (newTargetCd) => {
    if (form.value.stock_type === '材料' && newTargetCd) {
      try {
        const response = await request.get(`/api/materials/${newTargetCd}`)
        if (response.data.success) {
          form.value.base_qty = response.data.data.pieces_per_bundle || 0
        }
      } catch (error) {
        console.warn('获取材料信息失败:', error)
      }
    }
  },
)

const submit = async () => {
  try {
    await formRef.value!.validate()
  } catch {
    ElMessage.warning('必須項目を確認してください')
    return
  }

  submitLoading.value = true

  // 添加加载动画
  const loadingInstance = ElMessage({
    message: '登録中...',
    type: 'info',
    duration: 0,
    showClose: false,
  })

  try {
    // 根据库存种别设置process_cd
    if (form.value.stock_type === '製品') {
      form.value.process_cd = 'KT13'
    } else if (form.value.stock_type === '材料') {
      form.value.process_cd = 'KT19'
    } else if (form.value.stock_type === '部品') {
      form.value.process_cd = 'KT16'
    }

    const body = {
      stock_type: form.value.stock_type,
      transaction_type: form.value.transaction_type,
      target_cd: form.value.target_cd,
      location_cd: form.value.location_cd,
      quantity: form.value.quantity,
      unit: form.value.unit,
      transaction_time: form.value.transaction_time,
      process_cd: form.value.process_cd || undefined,
      machine_cd: form.value.machine_cd || undefined,
      remarks: form.value.remarks || undefined,
      order_no: form.value.related_doc_no || undefined,
      source_file: '手入力',
    }
    await request.post('/api/erp/stock-transaction-logs', body)

    loadingInstance.close()
    ElMessage.success({
      message: '在庫履歴を登録しました',
      type: 'success',
      duration: 3000,
      showClose: true,
    })

    // 记录当日登录
    addToTodayLog()
    resetForm()
  } catch {
    loadingInstance.close()
    ElMessage.error({
      message: '登録に失敗しました。再度お試しください。',
      type: 'error',
      duration: 5000,
      showClose: true,
    })
  } finally {
    submitLoading.value = false
  }
}

const addToTodayLog = () => {
  const today = new Date().toISOString().slice(0, 10)
  if (form.value.transaction_time.startsWith(today)) {
    const base = targetOptions.value.find((t) => t.cd === form.value.target_cd)
    const proc = processOptions.value.find((p) => p.cd === form.value.process_cd)

    const entry: LoggedTransaction = {
      stock_type: form.value.stock_type,
      cd: form.value.target_cd,
      name: base?.name || '',
      location_cd: form.value.location_cd,
      process_name: proc?.name,
      transaction_type: form.value.transaction_type,
      quantity: form.value.quantity,
      unit: form.value.unit,
    }

    const exists = todayLoggedTransactions.value.some(
      (x) =>
        x.stock_type === entry.stock_type &&
        x.cd === entry.cd &&
        x.process_name === entry.process_name &&
        x.quantity === entry.quantity &&
        x.unit === entry.unit,
    )

    if (!exists) {
      todayLoggedTransactions.value.unshift(entry)
    }
  }
}

const duplicateTransaction = (transaction: LoggedTransaction) => {
  // 复制交易记录到表单
  form.value.stock_type = transaction.stock_type
  form.value.target_cd = transaction.cd
  form.value.location_cd = transaction.location_cd
  form.value.transaction_type = transaction.transaction_type
  form.value.quantity = transaction.quantity
  form.value.unit = transaction.unit

  if (transaction.process_name && processOptions.value.length) {
    const proc = processOptions.value.find((p) => p.name === transaction.process_name)
    if (proc) form.value.process_cd = proc.cd
  }

  form.value.transaction_time = getLocalDateTimeString()
  form.value.remarks = ''

  ElMessage.success('取引を複製しました')
}

const resetForm = () => {
  const currentStockType = form.value.stock_type
  const currentTime = getLocalDateTimeString()

  formRef.value?.resetFields()
  form.value = createInitialForm()
  form.value.stock_type = currentStockType
  form.value.transaction_time = currentTime

  if (currentStockType) {
    setDefaultLocation(currentStockType)
  }
}

onMounted(async () => {
  pageLoading.value = true

  // 模拟加载过程，增加用户体验
  setTimeout(() => {
    pageLoading.value = false
  }, 800)

  // 初始化时不自动选择任何库存类型，让用户主动选择
})
</script>

<style scoped>
/* 现代页面布局 */
.unified-stock-page {
  min-height: 100vh;
  background: #f8fafc;
  position: relative;
  padding: 16px;
}

.bg-gradient {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 300px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  z-index: 0;
  opacity: 0.08;
}

.bg-pattern {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 300px;
  background:
    radial-gradient(circle at 25% 25%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 75% 75%, rgba(99, 102, 241, 0.1) 0%, transparent 50%);
  z-index: 1;
}

/* 现代页面头部 */
.page-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 24px 28px;
  margin-bottom: 24px;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.1),
    0 2px 8px rgba(0, 0, 0, 0.06);
  position: relative;
  z-index: 2;
  max-width: 1200px;
  margin: 0 auto 24px auto;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
}

.header-main {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6, #ec4899);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 8px 20px rgba(99, 102, 241, 0.3);
  position: relative;
  overflow: hidden;
}

.header-icon::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.header-icon:hover::before {
  left: 100%;
}

.header-text {
  flex: 1;
}

.main-title {
  font-size: 1.75rem;
  font-weight: 700;
  background: linear-gradient(135deg, #1e293b, #6366f1);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 6px 0;
  letter-spacing: -0.025em;
}

.subtitle {
  font-size: 0.9rem;
  color: #64748b;
  margin: 0 0 8px 0;
  font-weight: 400;
  line-height: 1.4;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
}

.indicator-dot {
  width: 8px;
  height: 8px;
  background: #22c55e;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.status-text {
  font-size: 0.75rem;
  color: #22c55e;
  font-weight: 500;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.quick-stats {
  display: flex;
  gap: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.1));
  border-radius: 12px;
  border: 1px solid rgba(99, 102, 241, 0.2);
  backdrop-filter: blur(10px);
}

.stat-icon {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.stat-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1e293b;
  line-height: 1;
}

.stat-label {
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 500;
}

.stat-card {
  text-align: center;
  padding: 12px 16px;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  min-width: 60px;
}

.stat-value {
  display: block;
  font-size: 1.25rem;
  font-weight: 600;
  color: #6366f1;
  line-height: 1;
}

.stat-label {
  display: block;
  font-size: 0.75rem;
  color: #64748b;
  margin-top: 4px;
  font-weight: 500;
}

/* 主要内容区域 */
.content-container {
  max-width: 1200px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 紧凑型库存类型选择器 */
.stock-type-selector {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 24px;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.1),
    0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.2);
  position: relative;
  z-index: 2;
}

.selector-header {
  margin-bottom: 16px;
}

.selector-title {
  font-weight: 700;
  color: #1e293b;
  font-size: 1.1rem;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.selector-title::before {
  content: '';
  width: 4px;
  height: 20px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-radius: 2px;
}

.stock-types {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.stock-type-chip {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: rgba(248, 250, 252, 0.8);
  border: 2px solid rgba(226, 232, 240, 0.8);
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 140px;
  position: relative;
  overflow: hidden;
}

.stock-type-chip::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.6s;
}

.stock-type-chip:hover {
  background: rgba(241, 245, 249, 0.9);
  border-color: rgba(203, 213, 225, 0.8);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.stock-type-chip:hover::before {
  left: 100%;
}

.stock-type-chip.active {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(99, 102, 241, 0.1));
  border-color: #8b5cf6;
  box-shadow:
    0 8px 25px rgba(139, 92, 246, 0.25),
    0 0 0 1px rgba(139, 92, 246, 0.1);
  transform: translateY(-2px);
}

.chip-icon {
  width: 28px;
  height: 28px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.chip-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.chip-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: #1e293b;
  letter-spacing: -0.01em;
}

.chip-count {
  font-size: 0.75rem;
  color: #64748b;
}

.chip-indicator {
  color: #8b5cf6;
}

/* 现代表单卡片 */
.form-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 28px;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.1),
    0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.2);
  position: relative;
  z-index: 2;
  overflow: hidden;
}

.form-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #6366f1, #8b5cf6, #ec4899, #f59e0b);
  z-index: 1;
}

.form-header {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e2e8f0;
}

.form-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #1e293b;
  font-size: 1.125rem;
}

.title-icon {
  font-size: 20px;
}

/* 现代表单样式 */
.modern-form {
  margin: 0;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
  margin-bottom: 24px;
}

.form-left,
.form-right {
  display: flex;
  flex-direction: column;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group :deep(.el-form-item) {
  margin-bottom: 0;
}

.form-group :deep(.el-form-item__label) {
  color: #374151;
  font-weight: 500;
  font-size: 0.875rem;
  margin-bottom: 6px;
}

.modern-select,
.modern-number,
.modern-date {
  width: 100%;
}

.modern-select :deep(.el-input__wrapper),
.modern-number :deep(.el-input__wrapper),
.modern-date :deep(.el-input__wrapper) {
  border-radius: 12px;
  border: 1.5px solid #e2e8f0;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow:
    0 2px 4px rgba(0, 0, 0, 0.05),
    0 0 0 0 rgba(99, 102, 241, 0);
}

.modern-select :deep(.el-input__wrapper):hover,
.modern-number :deep(.el-input__wrapper):hover,
.modern-date :deep(.el-input__wrapper):hover {
  border-color: #cbd5e1;
  box-shadow:
    0 4px 8px rgba(0, 0, 0, 0.1),
    0 0 0 0 rgba(99, 102, 241, 0);
  transform: translateY(-1px);
}

.modern-select :deep(.el-input__wrapper.is-focus),
.modern-number :deep(.el-input__wrapper.is-focus),
.modern-date :deep(.el-input__wrapper.is-focus) {
  border-color: #6366f1;
  box-shadow:
    0 4px 12px rgba(0, 0, 0, 0.1),
    0 0 0 4px rgba(99, 102, 241, 0.15);
  transform: translateY(-1px);
}

.quantity-row {
  display: flex;
  gap: 12px;
  align-items: end;
}

.quantity-item {
  flex: 2;
}

.unit-item {
  flex: 1;
}

.unit-select {
  min-width: 80px;
}

/* 折叠面板样式 */
.optional-info {
  margin-top: 24px;
  border: none;
  background: rgba(248, 250, 252, 0.6);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  border: 1px solid rgba(226, 232, 240, 0.5);
}

.optional-info :deep(.el-collapse-item__header) {
  background: transparent;
  border: none;
  padding: 16px 20px;
  font-weight: 500;
  color: #64748b;
  font-size: 0.875rem;
}

.optional-info :deep(.el-collapse-item__content) {
  padding: 0 20px 20px;
  background: transparent;
}

.detail-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.document-row {
  display: flex;
  gap: 12px;
}

.doc-type {
  flex: 1;
}

.doc-no {
  flex: 2;
}

/* 操作按钮 */
.action-bar {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 32px;
  padding-top: 20px;
  border-top: 1px solid #e2e8f0;
}

.reset-btn,
.submit-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border-radius: 12px;
  font-weight: 600;
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  position: relative;
  overflow: hidden;
  min-width: 120px;
  justify-content: center;
}

.reset-btn {
  background: rgba(255, 255, 255, 0.9);
  border: 1.5px solid #e2e8f0;
  color: #374151;
  backdrop-filter: blur(10px);
}

.reset-btn:hover {
  background: rgba(249, 250, 251, 0.95);
  border-color: #cbd5e1;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.submit-btn {
  background: linear-gradient(135deg, #6366f1, #8b5cf6, #ec4899);
  border: none;
  color: white;
  box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
  position: relative;
  overflow: hidden;
}

.submit-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.6s;
}

.submit-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(99, 102, 241, 0.4);
}

.submit-btn:hover::before {
  left: 100%;
}

/* 历史记录卡片 */
.history-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 24px;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.1),
    0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.2);
  position: relative;
  z-index: 2;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e2e8f0;
}

.history-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #1e293b;
  font-size: 1rem;
}

.history-badge {
  margin-left: 8px;
}

.history-filters {
  display: flex;
  gap: 8px;
}

.history-table {
  border-radius: 8px;
  overflow: hidden;
}

.compact-table {
  border-radius: 8px;
}

.compact-table :deep(.el-table__header) {
  background: #f8fafc;
}

.compact-table :deep(.el-table__header th) {
  background: transparent;
  color: #64748b;
  font-weight: 500;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid #e2e8f0;
  padding: 8px;
}

.compact-table :deep(.el-table__body td) {
  padding: 8px;
  font-size: 0.875rem;
}

.compact-table :deep(.el-table__body tr) {
  transition: all 0.2s ease;
}

.compact-table :deep(.el-table__body tr:hover) {
  background: linear-gradient(135deg, rgba(248, 250, 252, 0.8), rgba(241, 245, 249, 0.8));
  transform: scale(1.005);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.compact-table :deep(.el-table__body tr.el-table__row--striped) {
  background: rgba(248, 250, 252, 0.5);
}

.quantity-display {
  font-weight: 500;
  color: #1e293b;
}

.copy-btn {
  color: #6366f1;
  padding: 6px;
  border-radius: 8px;
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  position: relative;
  overflow: hidden;
}

.copy-btn:hover {
  background: linear-gradient(135deg, #ede9fe, #ddd6fe);
  color: #5b21b6;
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(91, 33, 182, 0.2);
}

/* 高级过渡动画 */
.slide-in-enter-active {
  transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.slide-in-leave-active {
  transition: all 0.3s cubic-bezier(0.55, 0.055, 0.675, 0.19);
}

.slide-in-enter-from {
  opacity: 0;
  transform: translateX(30px) scale(0.95);
  filter: blur(4px);
}

.slide-in-leave-to {
  opacity: 0;
  transform: translateX(-30px) scale(0.95);
  filter: blur(4px);
}

.slide-up-enter-active {
  transition: all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.slide-up-leave-active {
  transition: all 0.3s cubic-bezier(0.55, 0.055, 0.675, 0.19);
}

.slide-up-enter-from {
  opacity: 0;
  transform: translateY(40px) scale(0.9);
  filter: blur(8px);
}

.slide-up-leave-to {
  opacity: 0;
  transform: translateY(-20px) scale(0.95);
  filter: blur(4px);
}

/* 新增浮现动画 */
.fade-scale-enter-active {
  transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.fade-scale-leave-active {
  transition: all 0.3s cubic-bezier(0.55, 0.055, 0.675, 0.19);
}

.fade-scale-enter-from {
  opacity: 0;
  transform: scale(0.8);
  filter: blur(10px);
}

.fade-scale-leave-to {
  opacity: 0;
  transform: scale(1.1);
  filter: blur(5px);
}

/* 微妙的悬停动画 */
.hover-lift {
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.hover-lift:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
}

/* 加载状态美化 */
:deep(.el-loading-mask) {
  background-color: rgba(248, 250, 252, 0.9) !important;
  backdrop-filter: blur(8px);
}

:deep(.el-loading-spinner) {
  top: 50%;
  margin-top: -40px;
}

:deep(.el-loading-spinner .el-loading-text) {
  color: #6366f1;
  font-weight: 500;
  margin-top: 16px;
  font-size: 0.875rem;
}

:deep(.el-loading-spinner .circular) {
  width: 50px;
  height: 50px;
  animation: loading-rotate 2s linear infinite;
}

:deep(.el-loading-spinner .path) {
  stroke: #6366f1;
  stroke-width: 3;
  stroke-dasharray: 90, 150;
  stroke-dashoffset: 0;
  stroke-linecap: round;
  animation: loading-dash 1.5s ease-in-out infinite;
}

@keyframes loading-rotate {
  100% {
    transform: rotate(360deg);
  }
}

@keyframes loading-dash {
  0% {
    stroke-dasharray: 1, 200;
    stroke-dashoffset: 0;
  }
  50% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: -40;
  }
  100% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: -120;
  }
}

/* 优化移动端交互 */
@media (hover: none) {
  .hover-lift:hover {
    transform: none;
    box-shadow: none;
  }

  .stock-type-chip:hover {
    transform: none;
  }

  .copy-btn:hover {
    transform: none;
  }

  .submit-btn:hover {
    transform: none;
  }

  .reset-btn:hover {
    transform: none;
  }
}

/* 触摸设备优化 */
@media (pointer: coarse) {
  .stock-type-chip {
    padding: 16px 20px;
    min-height: 48px;
  }

  .reset-btn,
  .submit-btn {
    min-height: 44px;
    padding: 12px 24px;
  }

  .copy-btn {
    min-width: 44px;
    min-height: 44px;
  }
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .header-actions {
    display: none;
  }

  .form-grid {
    grid-template-columns: 1fr;
    gap: 24px;
  }
}

@media (max-width: 768px) {
  .unified-stock-page {
    padding: 8px;
  }

  .page-header {
    padding: 16px 20px;
    margin-bottom: 16px;
    border-radius: 16px;
  }

  .header-content {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }

  .header-main {
    justify-content: center;
  }

  .main-title {
    font-size: 1.375rem;
  }

  .subtitle {
    font-size: 0.825rem;
  }

  .stock-types {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }

  .stock-type-chip {
    min-width: auto;
    padding: 14px 16px;
  }

  .form-card {
    padding: 20px;
    border-radius: 16px;
  }

  .form-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  .quantity-row {
    flex-direction: column;
    gap: 12px;
  }

  .document-row {
    flex-direction: column;
    gap: 12px;
  }

  .action-bar {
    flex-direction: column-reverse;
    gap: 8px;
  }

  .history-header {
    flex-direction: column;
    gap: 12px;
    text-align: center;
  }

  .history-filters {
    justify-content: center;
  }

  .history-card {
    padding: 16px;
    border-radius: 16px;
  }

  .stock-type-selector {
    padding: 20px;
    border-radius: 16px;
  }
}

@media (max-width: 480px) {
  .unified-stock-page {
    padding: 4px;
  }

  .main-title {
    font-size: 1.25rem;
  }

  .subtitle {
    font-size: 0.8rem;
  }

  .stock-types {
    grid-template-columns: 1fr;
    gap: 8px;
  }

  .stock-type-chip {
    padding: 12px 14px;
    gap: 10px;
  }

  .chip-title {
    font-size: 0.85rem;
  }

  .form-card {
    padding: 16px;
    border-radius: 12px;
  }

  .form-header {
    margin-bottom: 16px;
    padding-bottom: 12px;
  }

  .form-title {
    font-size: 1rem;
  }

  .history-card {
    padding: 12px;
    border-radius: 12px;
  }

  .stock-type-selector {
    padding: 16px;
    border-radius: 12px;
  }

  .page-header {
    padding: 12px 16px;
    border-radius: 12px;
  }

  .header-icon {
    width: 40px;
    height: 40px;
    border-radius: 12px;
  }

  .reset-btn,
  .submit-btn {
    padding: 10px 20px;
    font-size: 0.875rem;
  }

  .compact-table {
    font-size: 0.8rem;
  }

  .compact-table :deep(.el-table__header th) {
    padding: 6px;
    font-size: 0.7rem;
  }

  .compact-table :deep(.el-table__body td) {
    padding: 6px;
    font-size: 0.8rem;
  }
}
</style>
