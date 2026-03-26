<template>
  <el-dialog
    :model-value="modelValue"
    @update:model-value="handleClose"
    :title="isEdit ? '繰越記録編集' : '繰越記録追加'"
    width="600px"
    :close-on-click-modal="false"
    class="edit-dialog"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="120px"
      class="edit-form"
    >
      <el-form-item label="在庫種別" prop="stock_type" required>
        <el-select v-model="formData.stock_type" placeholder="在庫種別を選択" style="width: 100%">
          <el-option label="材料" value="材料" />
          <el-option label="部品" value="部品" />
          <el-option label="製品" value="製品" />
        </el-select>
      </el-form-item>

      <el-form-item label="製品コード" prop="target_cd" required>
        <el-select
          v-model="formData.target_cd"
          placeholder="製品を選択"
          style="width: 100%"
          filterable
          :loading="productLoading"
        >
          <el-option
            v-for="product in productOptions"
            :key="product.value"
            :label="product.label"
            :value="product.value"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="工程CD" prop="process_cd" required>
        <el-select
          v-model="formData.process_cd"
          placeholder="工程を選択"
          style="width: 100%"
          filterable
          :loading="processLoading"
        >
          <el-option
            v-for="process in processOptions"
            :key="process.value"
            :label="process.label"
            :value="process.value"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="数量" prop="quantity" required>
        <el-input-number
          v-model="formData.quantity"
          :min="0"
          :precision="0"
          controls-position="right"
          style="width: 100%"
          placeholder="数量を入力"
        />
      </el-form-item>

      <el-form-item label="単位" prop="unit">
        <el-select v-model="formData.unit" placeholder="単位を選択" style="width: 100%">
          <el-option label="本" value="本" />
          <el-option label="個" value="個" />
          <el-option label="枚" value="枚" />
          <el-option label="kg" value="kg" />
          <el-option label="m" value="m" />
          <el-option label="セット" value="セット" />
        </el-select>
      </el-form-item>

      <el-form-item label="繰越日時" prop="transaction_time" required>
        <el-date-picker
          v-model="formData.transaction_time"
          type="datetime"
          placeholder="繰越日時を選択"
          format="YYYY-MM-DD HH:mm:ss"
          value-format="YYYY-MM-DD HH:mm:ss"
          style="width: 100%"
        />
      </el-form-item>

      <el-form-item label="ロット番号" prop="lot_no">
        <el-input v-model="formData.lot_no" placeholder="ロット番号を入力（任意）" maxlength="30" />
      </el-form-item>

      <el-form-item label="操作者" prop="operator_name">
        <el-input
          v-model="formData.operator_name"
          placeholder="操作者名を入力（任意）"
          maxlength="50"
        />
      </el-form-item>

      <el-form-item label="備考" prop="remarks">
        <el-input
          v-model="formData.remarks"
          type="textarea"
          :rows="3"
          placeholder="備考を入力（任意）"
          maxlength="500"
          show-word-limit
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose" class="cancel-btn">
          <el-icon><Close /></el-icon>
          キャンセル
        </el-button>
        <el-button type="primary" @click="handleSave" :loading="saveLoading" class="save-btn">
          <el-icon><Check /></el-icon>
          {{ isEdit ? '更新' : '追加' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Close, Check } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { getProductList } from '@/api/master/productMaster'
import { fetchProcesses } from '@/api/master/processMaster'
import { getMaterialList } from '@/api/master/materialMaster'
import { getComponentList } from '@/api/master/componentMaster'

// 定义 Props
interface Props {
  modelValue: boolean
  editData?: any
}

const props = withDefaults(defineProps<Props>(), {
  editData: null,
})

// 定义 Emits
const emit = defineEmits(['update:modelValue', 'save'])

// 响应式数据
const formRef = ref<FormInstance>()
const saveLoading = ref(false)

// 判断是否为编辑模式
const isEdit = computed(() => !!props.editData)

// 表单数据
const formData = reactive({
  stock_type: '',
  target_cd: '',
  process_cd: '',
  quantity: 0,
  unit: '',
  transaction_time: '',
  lot_no: '',
  operator_name: '',
  remarks: '',
})

// 工程选项
const processOptions = ref<Array<{ value: string; label: string }>>([])
const processLoading = ref(false)

// 产品选项（支持材料、部品、製品）
const productOptions = ref<Array<{ value: string; label: string }>>([])
const productLoading = ref(false)

// 根据在庫種別加载对应的产品数据
const loadProductOptions = async (stockType: string) => {
  if (!stockType) {
    productOptions.value = []
    return
  }

  productLoading.value = true
  try {
    let response: any = null

    switch (stockType) {
      case '材料':
        response = await getMaterialList({
          keyword: '',
        })
        break
      case '部品':
        // 使用部品API获取数据
        response = await getComponentList({
          keyword: '',
        })
        break
      case '製品':
        response = await getProductList({
          page: 1,
          pageSize: 1000,
        })
        // 过滤掉末尾不是1的产品
        if (response && response.list && Array.isArray(response.list)) {
          // 先打印所有产品代码来调试
          console.log(
            '所有产品代码:',
            response.list.map((p: any) => p.product_cd),
          )

          response.list = response.list.filter((product: any) => {
            return product.product_cd && product.product_cd.endsWith('1')
          })

          console.log(
            '过滤后的产品代码:',
            response.list.map((p: any) => p.product_cd),
          )
        }
        break
      default:
        productOptions.value = []
        return
    }

    // 处理不同的API响应结构
    let dataList: any[] = []
    if (response && response.success && response.data && Array.isArray(response.data)) {
      // 材料API返回 {success: true, data: Array}
      dataList = response.data
    } else if (response && response.list && Array.isArray(response.list)) {
      // 产品API返回 {list: Array}
      dataList = response.list
    }

    if (dataList.length > 0) {
      productOptions.value = dataList.map((item: any) => {
        // 根据不同的在庫種別使用不同的字段
        let code, name
        switch (stockType) {
          case '材料':
            code = item.material_cd
            name = item.material_name
            break
          case '部品':
            code = item.component_cd // 使用部品API的component_cd
            name = item.component_name // 使用部品API的component_name
            break
          case '製品':
            code = item.product_cd
            name = item.product_name
            break
          default:
            code = item.material_cd || item.component_cd || item.product_cd
            name = item.material_name || item.component_name || item.product_name
        }

        return {
          value: code,
          label: `${code} - ${name}`,
        }
      })

      console.log(`${stockType}映射后的选项:`, productOptions.value)
    } else {
      console.error(`${stockType}データ取得エラー:`, response)
      ElMessage.error(`${stockType}データの取得に失敗しました`)
    }
  } catch (error) {
    console.error(`${stockType}データ取得エラー:`, error)
    ElMessage.error(`${stockType}データの取得に失敗しました`)
  } finally {
    productLoading.value = false
  }
}

// 根据在庫種別加载对应的工程数据
const loadProcessOptions = async (stockType: string) => {
  processLoading.value = true
  try {
    const response = await fetchProcesses({
      page: 1,
      pageSize: 1000, // 获取所有工程数据
    })

    if (response && response.list && Array.isArray(response.list)) {
      let filteredProcesses = response.list

      // 根据在庫種別过滤工程
      switch (stockType) {
        case '材料':
          // 材料时只显示KT19
          filteredProcesses = response.list.filter((process: any) => process.process_cd === 'KT19')
          break
        case '部品':
          // 部品时只显示KT18
          filteredProcesses = response.list.filter((process: any) => process.process_cd === 'KT18')
          break
        case '製品':
          // 製品时过滤掉KT18和KT19
          filteredProcesses = response.list.filter(
            (process: any) => process.process_cd !== 'KT18' && process.process_cd !== 'KT19',
          )
          break
        default:
          filteredProcesses = response.list
      }

      processOptions.value = filteredProcesses.map((process: any) => ({
        value: process.process_cd,
        label: `${process.process_cd} - ${process.process_name}`,
      }))
    } else {
      console.error('工程データ取得エラー:', response)
      ElMessage.error('工程データの取得に失敗しました')
    }
  } catch (error) {
    console.error('工程データ取得エラー:', error)
    ElMessage.error('工程データの取得に失敗しました')
  } finally {
    processLoading.value = false
  }
}

// 表单验证规则
const formRules: FormRules = {
  stock_type: [{ required: true, message: '在庫種別を選択してください', trigger: 'change' }],
  target_cd: [{ required: true, message: '製品を選択してください', trigger: 'change' }],
  process_cd: [{ required: true, message: '工程を選択してください', trigger: 'change' }],
  quantity: [
    { required: true, message: '数量を入力してください', trigger: 'blur' },
    {
      validator: (_rule: any, value: any, callback: any) => {
        if (value === null || value === undefined || value === '') {
          callback(new Error('数量を入力してください'))
        } else if (value < 0) {
          callback(new Error('数量は0以上で入力してください'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
  transaction_time: [{ required: true, message: '繰越日時を選択してください', trigger: 'change' }],
  lot_no: [{ max: 30, message: 'ロット番号は30文字以内で入力してください', trigger: 'blur' }],
  operator_name: [{ max: 50, message: '操作者名は50文字以内で入力してください', trigger: 'blur' }],
  remarks: [{ max: 500, message: '備考は500文字以内で入力してください', trigger: 'blur' }],
}

// 重置表单数据
const resetFormData = () => {
  Object.assign(formData, {
    stock_type: '',
    target_cd: '',
    process_cd: '',
    quantity: 0,
    unit: '',
    transaction_time: '',
    lot_no: '',
    operator_name: '',
    remarks: '',
  })
}

// 设置表单数据
const setFormData = (data: any) => {
  if (data) {
    Object.assign(formData, {
      stock_type: data.stock_type || '',
      target_cd: data.target_cd || '',
      process_cd: data.process_cd || '',
      quantity: data.quantity || 0,
      unit: data.unit || '',
      transaction_time: data.transaction_time || '',
      lot_no: data.lot_no || '',
      operator_name: data.operator_name || '',
      remarks: data.remarks || '',
    })
  }
}

// 根据在庫種別自动设置单位
const setUnitByStockType = (stockType: string) => {
  const unitMap: Record<string, string> = {
    材料: '本',
    部品: '個',
    製品: '本',
    仕掛品: '個',
  }
  if (!formData.unit && unitMap[stockType]) {
    formData.unit = unitMap[stockType]
  }
}

// 监听在庫種別变化
watch(
  () => formData.stock_type,
  async (newValue) => {
    if (newValue) {
      setUnitByStockType(newValue)

      // 清空当前选择
      formData.target_cd = ''
      formData.process_cd = ''

      // 根据在庫種別加载对应的数据
      await loadProductOptions(newValue)
      await loadProcessOptions(newValue)

      // 自动设置工程CD
      if (newValue === '材料' && processOptions.value.length > 0) {
        formData.process_cd = 'KT19'
      } else if (newValue === '部品' && processOptions.value.length > 0) {
        formData.process_cd = 'KT18'
      }
    } else {
      // 清空选项
      productOptions.value = []
      processOptions.value = []
      formData.target_cd = ''
      formData.process_cd = ''
    }
  },
)

// 监听编辑数据变化
watch(
  () => props.editData,
  (newData) => {
    if (newData) {
      setFormData(newData)
    } else {
      resetFormData()
    }
  },
  { immediate: true },
)

// 监听对话框显示状态
watch(
  () => props.modelValue,
  (visible) => {
    if (visible) {
      nextTick(() => {
        formRef.value?.clearValidate()
        if (props.editData) {
          setFormData(props.editData)
        } else {
          resetFormData()
          // 设置默认值
          formData.transaction_time = new Date().toISOString().slice(0, 19).replace('T', ' ')
        }
      })
    }
  },
)

// 关闭对话框
const handleClose = () => {
  emit('update:modelValue', false)
}

// 保存数据
const handleSave = async () => {
  if (!formRef.value) return

  try {
    const valid = await formRef.value.validate()
    if (!valid) return

    saveLoading.value = true

    // 构造保存数据
    const saveData = {
      stock_type: formData.stock_type,
      target_cd: formData.target_cd,
      process_cd: formData.process_cd,
      quantity: formData.quantity,
      unit: formData.unit,
      transaction_time: formData.transaction_time,
      lot_no: formData.lot_no || null,
      operator_name: formData.operator_name || null,
      remarks: formData.remarks || null,
      // 根据业务规则设置location_cd和transaction_type
      location_cd: getLocationCdByProcessCd(formData.process_cd),
      transaction_type: '初期',
    }

    emit('save', saveData)
  } catch (error) {
    console.error('表单验证失败:', error)
  } finally {
    saveLoading.value = false
  }
}

// 根据工程CD获取保管场所CD
const getLocationCdByProcessCd = (processCd: string) => {
  const locationMap: Record<string, string> = {
    KT01: '工程中間在庫',
    KT02: '工程中間在庫',
    KT03: '工程中間在庫',
    KT04: '工程中間在庫',
    KT05: '工程中間在庫',
    KT06: '外注倉庫',
    KT07: '工程中間在庫',
    KT08: '外注倉庫',
    KT09: '工程中間在庫',
    KT10: '外注倉庫',
    KT11: '工程中間在庫',
    KT12: '外注倉庫',
    KT13: '製品倉庫',
    KT14: '外注倉庫',
    KT15: '外注倉庫',
    KT16: '工程中間在庫',
    KT17: '工程中間在庫',
    KT18: '部品倉庫',
    KT19: '材料置場',
  }
  return locationMap[processCd] || '工程中間在庫'
}

// 组件挂载
onMounted(() => {
  // 不再自动加载数据，等待用户选择在庫種別
})
</script>

<style lang="scss" scoped>
.edit-dialog {
  :deep(.el-dialog) {
    border-radius: 20px;
    overflow: hidden;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
    backdrop-filter: blur(20px);

    .el-dialog__header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 1rem 1.5rem;
      border-bottom: none;
      position: relative;

      &::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, transparent 100%);
        pointer-events: none;
      }

      .el-dialog__title {
        font-size: 1.2rem;
        font-weight: 700;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      }

      .el-dialog__headerbtn {
        top: 1rem;
        right: 1.5rem;

        .el-dialog__close {
          color: white;
          font-size: 1.1rem;
          transition: all 0.3s ease;

          &:hover {
            color: rgba(255, 255, 255, 0.8);
            transform: scale(1.1);
          }
        }
      }
    }

    .el-dialog__body {
      padding: 1.5rem;
      background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
      position: relative;

      &::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(102, 126, 234, 0.3), transparent);
      }
    }

    .el-dialog__footer {
      background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
      padding: 1rem 1.5rem;
      border-top: 1px solid rgba(102, 126, 234, 0.1);
    }
  }

  .edit-form {
    :deep(.el-form-item) {
      margin-bottom: 1rem;

      .el-form-item__label {
        font-weight: 600;
        color: #374151;
        font-size: 0.9rem;
        margin-bottom: 0.3rem;
      }

      .el-form-item__content {
        .el-input,
        .el-select,
        .el-input-number,
        .el-date-editor {
          width: 100%;

          .el-input__wrapper {
            border-radius: 10px;
            border: 2px solid #e5e7eb;
            transition: all 0.3s ease;
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(10px);

            &:hover {
              border-color: #667eea;
              box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
            }
          }

          &.is-focus .el-input__wrapper {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            background: rgba(255, 255, 255, 0.95);
          }
        }

        .el-textarea {
          .el-textarea__inner {
            border-radius: 10px;
            border: 2px solid #e5e7eb;
            transition: all 0.3s ease;
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(10px);

            &:hover {
              border-color: #667eea;
              box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
            }

            &:focus {
              border-color: #667eea;
              box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
              background: rgba(255, 255, 255, 0.95);
            }
          }
        }
      }
    }
  }

  .dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 0.8rem;

    .cancel-btn {
      background: linear-gradient(135deg, #f3f4f6, #e5e7eb);
      border: 2px solid #d1d5db;
      color: #6b7280;
      border-radius: 10px;
      font-weight: 600;
      transition: all 0.3s ease;

      &:hover {
        background: linear-gradient(135deg, #e5e7eb, #d1d5db);
        border-color: #9ca3af;
        color: #374151;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
      }
    }

    .save-btn {
      background: linear-gradient(135deg, #667eea, #764ba2);
      border: none;
      border-radius: 10px;
      font-weight: 600;
      box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
      transition: all 0.3s ease;

      &:hover:not(:disabled) {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
      }

      &:disabled {
        background: linear-gradient(135deg, #f3f4f6, #e5e7eb);
        color: #9ca3af;
        box-shadow: none;
        transform: none;
      }
    }
  }
}
</style>
