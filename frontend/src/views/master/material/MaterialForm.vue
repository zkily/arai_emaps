<!-- MaterialEditDialog.vue -->
<template>
  <el-dialog
    v-model="visibleLocal"
    width="900px"
    :before-close="handleClose"
    :destroy-on-close="true"
    :draggable="true"
    :close-on-click-modal="false"
    class="material-dialog"
    transition="dialog-fade-zoom"
  >
    <div class="dialog-title"><span class="icon">🧱</span> 材料情報の登録・編集</div>

    <el-tabs v-model="activeTab" class="dialog-tabs">
      <el-tab-pane label="基本情報" name="basic">
        <div class="tab-content">
          <el-form
            :model="form"
            :rules="rules"
            ref="formRef"
            label-width="130px"
            class="dialog-form"
          >
            <el-form-item label="材料CD" prop="material_cd">
              <el-input v-model="form.material_cd" placeholder="材料コードを入力" />
            </el-form-item>
            <el-form-item label="材料名" prop="material_name">
              <el-input v-model="form.material_name" placeholder="材料名を入力" />
            </el-form-item>
            <el-form-item label="材料種類">
              <el-select v-model="form.material_type" placeholder="選択してください">
                <el-option label="鋼材" value="鋼材" />
                <el-option label="鋼管" value="鋼管" />
                <el-option label="樹脂" value="樹脂" />
                <el-option label="アルミ" value="アルミ" />
                <el-option label="その他" value="その他" />
              </el-select>
            </el-form-item>
            <el-form-item label="規格">
              <el-input v-model="form.standard_spec" placeholder="規格を入力" />
            </el-form-item>
            <el-form-item label="用途">
              <el-select v-model="form.usegae" placeholder="選択してください">
                <el-option label="生産用" value="生産用" />
                <el-option label="試作用" value="試作用" />
                <el-option label="支給用" value="支給用" />
                <el-option label="その他" value="その他" />
              </el-select>
            </el-form-item>
            <el-form-item label="代表品種">
              <el-input v-model="form.representative_model" placeholder="代表品種を入力" />
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>

      <el-tab-pane label="寸法・仕様" name="specs">
        <div class="tab-content">
          <el-form :model="form" label-width="130px" class="dialog-form">
            <el-form-item label="単位" prop="unit">
              <el-select v-model="form.unit" placeholder="選択してください">
                <el-option label="kg" value="kg" />
                <el-option label="本" value="本" />
                <el-option label="m" value="m" />
                <el-option label="枚" value="枚" />
                <el-option label="個" value="個" />
                <el-option label="セット" value="セット" />
              </el-select>
            </el-form-item>
            <el-form-item label="直径（mm）">
              <el-input-number
                v-model="form.diameter"
                :min="0"
                :step="0.1"
                :precision="2"
                placeholder="直径"
              />
            </el-form-item>
            <el-form-item label="厚さ（mm）">
              <el-input-number
                v-model="form.thickness"
                :min="0"
                :step="0.01"
                :precision="3"
                placeholder="厚さ"
              />
            </el-form-item>
            <el-form-item label="長さ（mm）">
              <el-input-number
                v-model="form.length"
                :min="0"
                :step="1"
                :precision="0"
                placeholder="長さ"
              />
            </el-form-item>
            <el-form-item label="束本数">
              <el-input-number
                v-model="form.pieces_per_bundle"
                :min="0"
                :step="1"
                :precision="0"
                placeholder="束本数"
              />
            </el-form-item>
            <el-form-item label="長尺単重（kg/本）">
              <el-input-number
                v-model="form.long_weight"
                :min="0"
                :step="0.001"
                :precision="5"
                placeholder="長尺単重"
              />
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>

      <el-tab-pane label="仕入・在庫" name="purchase">
        <div class="tab-content">
          <el-form :model="form" label-width="130px" class="dialog-form">
            <el-form-item label="支給区分">
              <el-select v-model="form.supply_classification" placeholder="選択してください">
                <el-option label="自給" value="自給" />
                <el-option label="有償" value="有償" />
                <el-option label="無償" value="無償" />
              </el-select>
            </el-form-item>
            <el-form-item label="仕入先CD">
              <el-select v-model="form.supplier_cd" placeholder="選択してください" filterable>
                <el-option
                  v-for="item in supplierOptions"
                  :key="item.cd"
                  :label="`${item.cd}｜${item.name}`"
                  :value="item.cd"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="単重単価（円/kg）">
              <el-input-number
                v-model="form.unit_price"
                :min="0"
                :step="0.01"
                :precision="2"
                placeholder="単重単価"
              />
            </el-form-item>
            <el-form-item label="一本単価（円）">
              <el-input-number
                v-model="form.single_price"
                :min="0"
                :step="0.01"
                :precision="2"
                placeholder="一本単価"
              />
            </el-form-item>
            <el-form-item label="安全在庫">
              <el-input-number
                v-model="form.safety_stock"
                :min="0"
                :step="1"
                :precision="0"
                placeholder="安全在庫"
              />
            </el-form-item>
            <el-form-item label="リードタイム（日）">
              <el-input-number
                v-model="form.lead_time"
                :min="0"
                :step="1"
                :precision="0"
                placeholder="リードタイム"
              />
            </el-form-item>
            <el-form-item label="保管場所">
              <el-input v-model="form.storage_location" placeholder="保管場所を入力" />
            </el-form-item>
            <el-form-item label="状態">
              <el-switch
                v-model="form.status"
                :active-value="1"
                :inactive-value="0"
                active-text="有効"
                inactive-text="無効"
              />
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>

      <el-tab-pane label="公差・範囲" name="tolerance">
        <div class="tab-content">
          <el-form :model="form" label-width="130px" class="dialog-form tolerance-form">
            <!-- 第一行：公差範囲、公差１、公差２ -->
            <div class="form-row">
              <el-form-item label="公差範囲" class="form-row-item">
                <el-input v-model="form.tolerance_range" placeholder="公差範囲を入力" />
              </el-form-item>
              <el-form-item label="公差１" class="form-row-item">
                <el-input-number
                  v-model="form.tolerance_1"
                  :step="0.01"
                  :precision="2"
                  placeholder="公差１"
                />
              </el-form-item>
              <el-form-item label="公差２" class="form-row-item">
                <el-input-number
                  v-model="form.tolerance_2"
                  :step="0.01"
                  :precision="2"
                  placeholder="公差２"
                />
              </el-form-item>
            </div>

            <!-- 第二行：範囲、最小値、最大値 -->
            <div class="form-row">
              <el-form-item label="範囲" class="form-row-item">
                <el-input v-model="form.range_value" placeholder="範囲を入力" />
              </el-form-item>
              <el-form-item label="最小値" class="form-row-item">
                <el-input-number
                  v-model="form.min_value"
                  :step="0.01"
                  :precision="2"
                  placeholder="最小値"
                />
              </el-form-item>
              <el-form-item label="最大値" class="form-row-item">
                <el-input-number
                  v-model="form.max_value"
                  :step="0.01"
                  :precision="2"
                  placeholder="最大値"
                />
              </el-form-item>
            </div>

            <!-- 第三行：実力値１、実力値２、実力値３ -->
            <div class="form-row">
              <el-form-item label="実力値１" class="form-row-item">
                <el-input-number
                  v-model="form.actual_value_1"
                  :step="0.001"
                  :precision="3"
                  placeholder="実力値１"
                />
              </el-form-item>
              <el-form-item label="実力値２" class="form-row-item">
                <el-input-number
                  v-model="form.actual_value_2"
                  :step="0.001"
                  :precision="3"
                  placeholder="実力値２"
                />
              </el-form-item>
              <el-form-item label="実力値３" class="form-row-item">
                <el-input-number
                  v-model="form.actual_value_3"
                  :step="0.001"
                  :precision="3"
                  placeholder="実力値３"
                />
              </el-form-item>
            </div>
          </el-form>
        </div>
      </el-tab-pane>

      <el-tab-pane label="備考" name="note">
        <div class="tab-content">
          <el-form :model="form" label-width="130px" class="dialog-form">
            <el-form-item label="備考">
              <el-input
                type="textarea"
                v-model="form.note"
                :rows="8"
                placeholder="備考を入力してください"
              />
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>
    </el-tabs>

    <template #footer>
      <div class="dialog-footer">
        <el-button class="cancel-btn" @click="handleClose">キャンセル</el-button>
        <el-button class="save-btn" type="primary" :loading="loading" @click="submitForm"
          >保存</el-button
        >
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  createMaterial,
  updateMaterial,
  getMaxMaterialCd,
  getMaterialById,
} from '@/api/master/materialMaster'
import type { Material, OptionItem } from '@/types/master'
import { getSupplierOptions } from '@/api/options'

function createEmptyMaterial(): Material {
  return {
    id: 0,
    material_cd: '',
    material_name: '',
    material_type: '',
    standard_spec: '',
    unit: '',
    diameter: 0,
    thickness: 0,
    length: 0,
    supply_classification: '',
    pieces_per_bundle: 0,
    usegae: '',
    supplier_cd: '',
    unit_price: 0,
    long_weight: 0,
    single_price: 0,
    safety_stock: 0,
    lead_time: 0,
    storage_location: '',
    status: 1,
    tolerance_range: '',
    tolerance_1: 0,
    tolerance_2: 0,
    range_value: '',
    min_value: 0,
    max_value: 0,
    actual_value_1: 0,
    actual_value_2: 0,
    actual_value_3: 0,
    representative_model: '',
    note: '',
    created_at: '',
    updated_at: '',
  }
}

const props = defineProps<{ visible: boolean; dataId?: number | null }>()
const emit = defineEmits(['update:visible', 'refresh'])

const visibleLocal = ref(false)
watch(
  () => props.visible,
  (val) => {
    visibleLocal.value = val
  },
)
watch(visibleLocal, (val) => {
  emit('update:visible', val)
})

const activeTab = ref('basic')
const supplierOptions = ref<OptionItem[]>([])
const loading = ref(false)
const formRef = ref()
const form = ref<Material>(createEmptyMaterial())

// 表单验证规则
const rules = ref({
  material_cd: [
    { required: true, message: '材料コードを入力してください', trigger: 'blur' },
    { min: 1, max: 20, message: '材料コードは1-20文字で入力してください', trigger: 'blur' },
  ],
  material_name: [
    { required: true, message: '材料名を入力してください', trigger: 'blur' },
    { min: 1, max: 100, message: '材料名は1-100文字で入力してください', trigger: 'blur' },
  ],
})

function resetForm() {
  form.value = createEmptyMaterial()
  activeTab.value = 'basic'
}

function handleClose() {
  emit('update:visible', false)
  // 延迟重置表单，避免在保存成功后立即清空
  setTimeout(() => {
    resetForm()
  }, 100)
}

watch(
  () => props.visible,
  async (val) => {
    if (!val) return
    console.log('Form visible changed, initializing form...')

    if (props.dataId != null) {
      // 编辑模式 - 先重置表单，然后加载数据
      console.log('Edit mode - loading material data for ID:', props.dataId)
      resetForm()
      try {
        const data = await getMaterialById(props.dataId)
        console.log('Loaded material data:', data)
        const empty = createEmptyMaterial()
        Object.keys(empty).forEach((key) => {
          // @ts-expect-error 动态赋值Material字段，类型检查可忽略
          form.value[key] = data[key] !== undefined ? data[key] : empty[key]
        })
        console.log('Form data populated:', form.value)
      } catch (error) {
        console.error('Failed to load material data:', error)
        ElMessage.error('材料データの読み込みに失敗しました')
      }
    } else {
      // 新规模式 - 重置表单并生成新代码
      console.log('New mode - generating material code...')
      resetForm()
      try {
        const res = await getMaxMaterialCd()
        const maxCd = Number(res.max_code ?? 0)
        form.value.material_cd = String(maxCd + 1).padStart(5, '0')
        console.log('Generated material code:', form.value.material_cd)
      } catch (error) {
        console.error('Failed to get max material code:', error)
        form.value.material_cd = '10001'
      }
    }
  },
  { immediate: true },
)

async function submitForm() {
  if (!formRef.value) {
    console.error('Form ref is not available')
    return
  }

  try {
    // 先进行表单验证，添加超时处理
    console.log('Starting form validation...')
    const validationPromise = formRef.value.validate()
    const timeoutPromise = new Promise((_, reject) =>
      setTimeout(() => reject(new Error('Validation timeout')), 5000),
    )

    const valid = await Promise.race([validationPromise, timeoutPromise])
    if (!valid) {
      console.log('Form validation failed')
      return
    }

    loading.value = true
    console.log('Form validation passed, starting save...')

    // 确保表单数据是正确格式
    const formData = { ...form.value }
    console.log('提交的表单数据:', formData)

    // 验证必要字段
    if (!formData.material_cd || !formData.material_name) {
      ElMessage.error('材料コードと材料名は必須です')
      return
    }

    // 清理数据，移除空字符串和无效值，以及数据库中不存在的字段
    const validFields = [
      'id',
      'material_cd',
      'material_name',
      'material_type',
      'standard_spec',
      'unit',
      'diameter',
      'thickness',
      'length',
      'supply_classification',
      'pieces_per_bundle',
      'usegae',
      'supplier_cd',
      'unit_price',
      'long_weight',
      'single_price',
      'safety_stock',
      'lead_time',
      'storage_location',
      'status',
      'tolerance_range',
      'tolerance_1',
      'tolerance_2',
      'range_value',
      'min_value',
      'max_value',
      'actual_value_1',
      'actual_value_2',
      'actual_value_3',
      'representative_model',
      'note',
    ]

    const cleanedData: any = {}
    validFields.forEach((key) => {
      if (
        (formData as any)[key] !== undefined &&
        (formData as any)[key] !== '' &&
        (formData as any)[key] !== null
      ) {
        cleanedData[key] = (formData as any)[key]
      }
    })

    // 移除id字段，因为新规登録时不应该包含id
    if (!form.value.id) {
      delete cleanedData.id
    }

    console.log('清理后的表单数据:', cleanedData)

    const fn = form.value.id ? updateMaterial : createMaterial
    console.log('Calling API function:', form.value.id ? 'updateMaterial' : 'createMaterial')

    // 添加API调用超时处理
    const apiPromise = fn(cleanedData as Material)
    const apiTimeoutPromise = new Promise((_, reject) =>
      setTimeout(() => reject(new Error('API call timeout')), 10000),
    )

    const result = await Promise.race([apiPromise, apiTimeoutPromise])
    console.log('API call successful:', result)

    if (!form.value.id) {
      // 新规登録の場合
      ElMessage.success('材料情報を登録しました')
      emit('update:visible', false)
    } else {
      // 更新の場合
      ElMessage.success('材料情報を更新しました')
    }
    emit('refresh')
  } catch (error: any) {
    console.error('Save error:', error)
    if (error.message === 'Validation timeout') {
      ElMessage.error('フォーム検証がタイムアウトしました')
    } else if (error.message === 'API call timeout') {
      ElMessage.error('API呼び出しがタイムアウトしました')
    } else {
      ElMessage.error('保存に失敗しました')
    }
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    console.log('MaterialForm mounted, loading supplier options...')
    supplierOptions.value = await getSupplierOptions()
    console.log('Supplier options loaded:', supplierOptions.value.length)
  } catch (error) {
    console.error('Failed to load supplier options:', error)
    ElMessage.warning('仕入先情報の読み込みに失敗しました')
  }
})
</script>

<style scoped>
.material-dialog .el-dialog__body {
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

.dialog-tabs {
  padding: 0 10px;
}

.tab-content {
  background: #f8fafc;
  border-radius: 14px;
  box-shadow: 0 2px 12px rgba(41, 128, 185, 0.08);
  padding: 24px 18px 10px 18px;
  margin: 18px 0 8px 0;
}

.dialog-form {
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 18px 24px;
}

.el-form-item {
  flex: 1 1 320px;
  min-width: 180px;
  margin-bottom: 0;
}

.el-form-item[data-full-width] {
  flex: 1 1 100%;
}

.el-input,
.el-select,
.el-input-number {
  width: 100%;
  font-size: 15px;
  border-radius: 8px;
  transition: box-shadow 0.2s;
}

.el-input:focus-within,
.el-select:focus-within,
.el-input-number:focus-within {
  box-shadow: 0 0 0 2px #2980b933;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #ebeef5;
  background: #fafbfc;
}

.cancel-btn {
  border-radius: 8px;
  background: #f5f7fa;
  color: #2980b9;
  border: 1px solid #2980b9;
  font-weight: 600;
  padding: 10px 24px;
  transition: all 0.2s;
}

.cancel-btn:hover {
  background: #eaf6fb;
  color: #1a5a7a;
  transform: translateY(-1px);
}

.save-btn {
  border-radius: 8px;
  background: linear-gradient(90deg, #27ae60 0%, #2980b9 100%);
  color: #fff;
  font-weight: 700;
  border: none;
  padding: 10px 24px;
  box-shadow: 0 2px 8px rgba(41, 128, 185, 0.13);
  transition: all 0.2s;
}

.save-btn:hover {
  background: linear-gradient(90deg, #2980b9 0%, #27ae60 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(41, 128, 185, 0.2);
}

/* 公差・範囲タブの特別なスタイル */
.tolerance-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-row {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.form-row-item {
  flex: 1;
  margin-bottom: 0;
  min-width: 0;
}

.form-row-item .el-form-item__label {
  width: 100px !important;
  text-align: left;
  font-size: 14px;
  font-weight: 500;
  color: #2c3e50;
}

.form-row-item .el-form-item__content {
  margin-left: 100px !important;
}

.tab-content:has(.tolerance-form) {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
}

/* 数値入力フィールドのスタイル */
.el-input-number {
  width: 100%;
}

.el-input-number .el-input__inner {
  text-align: right;
}

/* テキストエリアのスタイル */
.el-textarea .el-textarea__inner {
  border-radius: 8px;
  font-family: inherit;
  line-height: 1.5;
}

/* スイッチのスタイル */
.el-switch {
  --el-switch-on-color: #2980b9;
}

/* レスポンシブデザイン */
@media (max-width: 1000px) {
  .material-dialog .el-dialog {
    width: 95vw !important;
    max-width: 95vw;
  }

  .dialog-form {
    flex-direction: column;
    gap: 12px;
  }

  .el-form-item {
    min-width: 120px;
    flex: 1 1 100%;
  }

  .tab-content {
    padding: 14px 6px 6px 6px;
  }

  .form-row {
    flex-direction: column;
    gap: 12px;
  }

  .form-row-item .el-form-item__label {
    width: 120px !important;
  }

  .form-row-item .el-form-item__content {
    margin-left: 120px !important;
  }
}

@media (max-width: 600px) {
  .material-dialog .el-dialog {
    width: 98vw !important;
    margin: 0;
  }

  .dialog-title {
    font-size: 18px;
    padding: 12px 10px 8px;
  }

  .tab-content {
    margin: 8px 0;
    padding: 12px 8px;
  }

  .dialog-footer {
    padding: 12px 16px;
    flex-direction: column;
  }

  .cancel-btn,
  .save-btn {
    width: 100%;
    margin: 0;
  }

  .form-row {
    flex-direction: column;
    gap: 8px;
  }

  .form-row-item .el-form-item__label {
    width: 100px !important;
    font-size: 13px;
  }

  .form-row-item .el-form-item__content {
    margin-left: 100px !important;
  }
}

/* アニメーション */
.dialog-fade-zoom-enter-active,
.dialog-fade-zoom-leave-active {
  transition: all 0.3s ease;
}

.dialog-fade-zoom-enter-from,
.dialog-fade-zoom-leave-to {
  opacity: 0;
  transform: scale(0.9);
}

/* フォーカス状態の改善 */
.el-form-item:focus-within .el-form-item__label {
  color: #2980b9;
  font-weight: 600;
}

/* 必須フィールドのスタイル */
.el-form-item.is-required .el-form-item__label::before {
  color: #e74c3c;
  font-weight: bold;
}

/* エラー状態のスタイル */
.el-form-item.is-error .el-input__inner,
.el-form-item.is-error .el-select .el-input__inner {
  border-color: #e74c3c;
  box-shadow: 0 0 0 2px rgba(231, 76, 60, 0.1);
}
</style>
