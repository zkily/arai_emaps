<template>
  <el-dialog
    class="product-dialog"
    :model-value="visible"
    title="🆕 新規製品登録"
    width="90%"
    top="5vh"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="dialog-title">
      <span class="icon">🆕</span>
      <span>新規製品登録</span>
    </div>
    <el-tabs v-model="activeTab" type="border-card">
      <el-tab-pane label="🧾 基本情報" name="basic">
        <el-form
          :model="form"
          :rules="rules"
          ref="formRef"
          label-width="140px"
          class="form-section card-section"
        >
          <el-row :gutter="20">
            <el-col :md="12">
              <el-form-item label="製品CD" prop="product_cd">
                <el-input v-model="form.product_cd" :disabled="isEdit" placeholder="例:90011" />
              </el-form-item>
            </el-col>
            <el-col :md="12">
              <el-form-item label="製品名称" prop="product_name">
                <el-input v-model="form.product_name" placeholder="例:011B CTR" />
              </el-form-item>
            </el-col>
            <el-col :md="12">
              <el-form-item label="品番">
                <el-input v-model="form.part_number" placeholder="例:71941-X1453" />
              </el-form-item>
            </el-col>
            <el-col :md="12">
              <el-form-item label="別名">
                <el-input v-model="form.product_alias" placeholder="製品の別名" />
              </el-form-item>
            </el-col>
            <el-col :md="12">
              <el-form-item label="製品種別">
                <el-select v-model="form.product_type" placeholder="選択">
                  <el-option label="量産品" value="量産品" />
                  <el-option label="試作品" value="試作品" />
                  <el-option label="補給品" value="補給品" />
                  <el-option label="その他" value="その他" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :md="12">
              <el-form-item label="カテゴリ">
                <el-select v-model="form.category" placeholder="選択">
                  <el-option label="一般" value="一般" />
                  <el-option label="一般溶接" value="一般溶接" />
                  <el-option label="メカ溶接" value="メカ溶接" />
                  <el-option label="自動車" value="自動車" />
                  <el-option label="その他" value="その他" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :md="12">
              <el-form-item label="分類(kind)">
                <el-select v-model="form.kind" clearable placeholder="選択">
                  <el-option label="T" value="T" />
                  <el-option label="N" value="N" />
                  <el-option label="F" value="F" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :md="12">
              <el-form-item label="優先度">
                <el-select v-model="form.priority">
                  <el-option label="高" :value="1" />
                  <el-option label="中" :value="2" />
                  <el-option label="低" :value="3" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :md="12">
              <el-form-item label="ステータス">
                <el-select v-model="form.status">
                  <el-option label="active" value="active" />
                  <el-option label="inactive" value="inactive" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :md="12">
              <el-form-item label="売価（円）">
                <el-input-number v-model="form.unit_price" :min="0" :precision="2" />
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </el-tab-pane>
      <el-tab-pane label="🏭 製造設定" name="manufacture">
        <el-form :model="form" label-width="140px" class="form-section card-section">
          <el-row :gutter="20">
            <el-col :md="12">
              <el-form-item label="工程数">
                <el-input-number v-model="form.process_count" :min="1" />
              </el-form-item>
            </el-col>
            <el-col :md="12">
              <el-form-item label="多段階工程">
                <el-switch v-model="form.is_multistage" />
              </el-form-item>
            </el-col>
            <el-col :md="12">
              <el-form-item label="リードタイム(日)">
                <el-input-number v-model="form.lead_time" :min="0" />
              </el-form-item>
            </el-col>
            <el-col :md="12">
              <el-form-item label="安全在庫日数">
                <el-input-number v-model="form.safety_days" :min="0" />
              </el-form-item>
            </el-col>
            <el-col :md="12">
              <el-form-item label="生産ロット">
                <el-input-number v-model="form.lot_size" :min="1" />
              </el-form-item>
            </el-col>
            <el-col :md="12">
              <el-form-item label="工程ルート">
                <el-select v-model="form.route_cd" filterable placeholder="例:R-STD01">
                  <el-option
                    v-for="item in routeOptions"
                    :key="item.cd"
                    :label="`${item.cd}|${item.name}`"
                    :value="item.cd"
                  />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </el-tab-pane>
      <el-tab-pane label="📦 梱包・物流" name="logistics">
        <el-form :model="form" label-width="140px" class="form-section card-section">
          <el-row :gutter="20">
            <el-col :md="12">
              <el-form-item label="梱包タイプ">
                <el-select v-model="form.box_type" placeholder="選択">
                  <el-option label="小箱" value="小箱" />
                  <el-option label="大箱" value="大箱" />
                  <el-option label="TP箱" value="TP箱" />
                  <el-option label="段ボール" value="段ボール" />
                  <el-option label="加工箱" value="加工箱" />
                  <el-option label="特殊箱" value="特殊箱" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :md="12">
              <el-form-item label="入数/箱">
                <el-input-number v-model="form.unit_per_box" :min="0" />
              </el-form-item>
            </el-col>
            <el-col :md="12">
              <el-form-item label="寸法">
                <el-input v-model="form.dimensions" placeholder="例:14Φx1.0" />
              </el-form-item>
            </el-col>
            <el-col :md="12">
              <el-form-item label="重量 (g)">
                <el-input-number v-model="form.weight" :min="0" />
              </el-form-item>
            </el-col>
            <el-col :md="12">
              <el-form-item label="納入先">
                <el-select
                  v-model="form.destination_cd"
                  filterable
                  placeholder="例:N38|(株)INOAC吉良"
                  popper-class="destination-select-popper"
                >
                  <el-option
                    v-for="item in destinationOptions"
                    :key="item.cd"
                    :label="`${item.cd}|${item.name}`"
                    :value="item.cd"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :md="12">
              <el-form-item label="対応車種">
                <el-input v-model="form.vehicle_model" />
              </el-form-item>
            </el-col>
            <el-col :md="12">
              <el-form-item label="保管場所">
                <el-select v-model="form.location_cd" filterable placeholder="選択">
                  <el-option
                    v-for="item in locationOptions"
                    :key="item.cd"
                    :label="`${item.cd}｜${item.name}`"
                    :value="item.cd"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :md="12">
              <el-form-item label="使用開始日">
                <el-date-picker
                  v-model="startUseDateModel"
                  type="date"
                  placeholder="選択"
                  format="YYYY-MM-DD"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </el-tab-pane>
      <el-tab-pane label="🧱 材料・加工" name="material">
        <el-form :model="form" label-width="140px" class="form-section card-section">
          <el-row :gutter="20">
            <el-col :md="12">
              <el-form-item label="材料">
                <el-select
                  v-model="form.material_cd"
                  filterable
                  placeholder="例:10031|14.0x1.00x4969"
                >
                  <el-option
                    v-for="item in materialOptions"
                    :key="item.cd"
                    :label="`${item.cd}|${item.name}`"
                    :value="item.cd"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :md="12">
              <el-form-item label="切断長 (mm)">
                <el-input-number v-model="form.cut_length" :precision="2" :min="0" />
              </el-form-item>
            </el-col>
            <el-col :md="12">
              <el-form-item label="面取長 (mm)">
                <el-input-number v-model="form.chamfer_length" :precision="2" :min="0" />
              </el-form-item>
            </el-col>
            <el-col :md="12">
              <el-form-item label="展開長 (mm)">
                <el-input-number v-model="form.developed_length" :precision="2" :min="0" />
              </el-form-item>
            </el-col>
            <el-col :md="12">
              <el-form-item label="端材長 (mm)">
                <el-input-number v-model="form.scrap_length" :precision="2" :min="0" />
              </el-form-item>
            </el-col>
            <el-col :md="12">
              <el-form-item label="取り数">
                <el-input-number v-model="form.take_count" :min="0" />
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </el-tab-pane>
      <el-tab-pane label="📝 備考" name="note">
        <el-form :model="form" label-width="140px" class="form-section card-section">
          <el-form-item label="備考">
            <el-input type="textarea" v-model="form.note" :rows="4" placeholder="自由記述欄" />
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">キャンセル</el-button>
        <el-button type="primary" :loading="saving" @click="handleSubmit"> 💾 保存 </el-button>
      </div>
    </template>
  </el-dialog>
</template>
<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { Product, OptionItem } from '@/types/master'
import { getDestinationMasterOptions, getMaterialOptions, getRouteOptions } from '@/api/options'
import { createProduct, updateProduct, getMaxProductCd } from '@/api/master/productMaster'

const props = defineProps<{ visible: boolean; editData?: Product | null }>()
const emit = defineEmits(['update:visible', 'saved'])

const formRef = ref()
const activeTab = ref('basic')
const saving = ref(false)
const isEdit = computed(() => !!props.editData?.id)

const startUseDateModel = computed({
  get: () => {
    const dateValue = form.value.start_use_date
    if (dateValue) {
      if (dateValue instanceof Date) return dateValue
      if (typeof dateValue === 'string') return new Date(dateValue)
    }
    return undefined
  },
  set: (value: Date | undefined) => {
    form.value.start_use_date = value as Date | string | null | undefined
  },
})

const rules = {
  product_cd: [{ required: true, message: '製品CDは必須です', trigger: 'blur' }],
  product_name: [{ required: true, message: '製品名称は必須です', trigger: 'blur' }],
}

const destinationOptions = ref<OptionItem[]>([])
const materialOptions = ref<OptionItem[]>([])
const routeOptions = ref<OptionItem[]>([])
const locationOptions = ref<OptionItem[]>([])

const defaultForm: Product = {
  product_cd: '',
  product_name: '',
  product_type: '',
  part_number: '',
  category: '',
  kind: '',
  priority: 2,
  status: 'active',
  process_count: 1,
  is_multistage: true,
  lead_time: 0,
  lot_size: 1,
  route_cd: '',
  bom_id: undefined,
  box_type: '',
  unit_per_box: 0,
  dimensions: '',
  weight: 0,
  destination_cd: '',
  vehicle_model: '',
  material_cd: '',
  cut_length: 0,
  chamfer_length: 0,
  developed_length: 0,
  scrap_length: 0,
  take_count: 0,
  safety_days: 0,
  unit_price: 0,
  location_cd: '',
  start_use_date: undefined,
  product_alias: '',
  department_id: undefined,
  note: '',
}

const form = ref<Product>({ ...defaultForm })

watch(
  () => props.visible,
  async (val) => {
    if (!val) return
    if (isEdit.value && props.editData) {
      form.value = {
        ...props.editData,
        is_multistage: Boolean(props.editData.is_multistage),
        process_count: Number(props.editData.process_count) || 1,
        lead_time: Number(props.editData.lead_time) || 0,
        lot_size: Number(props.editData.lot_size) || 1,
        priority: Number(props.editData.priority) || 2,
        unit_per_box: Number(props.editData.unit_per_box) || 0,
        weight: Number(props.editData.weight) || 0,
        cut_length: Number(props.editData.cut_length) || 0,
        chamfer_length: Number(props.editData.chamfer_length) || 0,
        developed_length: Number(props.editData.developed_length) || 0,
        scrap_length: Number(props.editData.scrap_length) || 0,
        take_count: Number(props.editData.take_count) || 0,
        safety_days: Number(props.editData.safety_days) || 0,
        unit_price: Number(props.editData.unit_price) || 0,
        start_use_date: props.editData.start_use_date
          ? new Date(props.editData.start_use_date as string)
          : undefined,
      }
    } else {
      form.value = { ...defaultForm }
      const maxCdRaw = await getMaxProductCd()
      const maxCd = Number(maxCdRaw) || 90001
      form.value.product_cd = String(maxCd + 10).padStart(5, '0')
    }
  },
  { immediate: true },
)

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
  } catch {
    ElMessageBox.alert('必須項目が未入力です。入力内容を確認してください。', '⚠️ 入力エラー', {
      confirmButtonText: 'OK',
      type: 'warning',
    })
    return
  }
  try {
    await ElMessageBox.confirm(
      isEdit.value ? 'この製品の情報を更新しますか？' : 'この製品を新規登録しますか？',
      '💾 保存確認',
      { confirmButtonText: 'はい', cancelButtonText: 'キャンセル', type: 'info' },
    )
  } catch {
    return
  }
  saving.value = true
  try {
    const formData = { ...form.value }
    if (formData.start_use_date) {
      if (formData.start_use_date instanceof Date) {
        formData.start_use_date = formData.start_use_date.toISOString().split('T')[0]
      } else if (typeof formData.start_use_date === 'string' && formData.start_use_date) {
        formData.start_use_date = new Date(formData.start_use_date).toISOString().split('T')[0]
      }
    } else {
      formData.start_use_date = undefined
    }
    if (isEdit.value) {
      await updateProduct(formData)
      ElMessage.success('更新しました')
    } else {
      await createProduct(formData)
      ElMessage.success('登録しました')
    }
    form.value = { ...defaultForm }
    emit('update:visible', false)
    emit('saved')
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : '保存に失敗しました'
    ElMessage.error(errorMessage)
  } finally {
    saving.value = false
  }
}

const handleClose = () => {
  formRef.value?.resetFields()
  emit('update:visible', false)
}

onMounted(async () => {
  destinationOptions.value = await getDestinationMasterOptions()
  materialOptions.value = await getMaterialOptions()
  routeOptions.value = await getRouteOptions()
  locationOptions.value = [
    { cd: '製品倉庫', name: '製品倉庫' },
    { cd: '外注倉庫', name: '外注倉庫' },
    { cd: '仮設倉庫', name: '仮設倉庫' },
    { cd: '部品倉庫', name: '部品倉庫' },
    { cd: '材料置場', name: '材料置場' },
    { cd: '仕上倉庫', name: '仕上倉庫' },
    { cd: '工程中間在庫', name: '工程中間在庫' },
    { cd: 'メッキ倉庫', name: 'メッキ倉庫' },
  ]
})
</script>

<style scoped>
.product-dialog :deep(.el-dialog) { border-radius: 16px; }
.dialog-title {
  font-size: 22px; font-weight: bold; color: #2c3e50;
  padding: 20px 24px 12px; border-bottom: 1px solid #ebeef5;
  background: linear-gradient(to right, #e6f7ff, #ffffff);
  border-top-left-radius: 12px; border-top-right-radius: 12px;
  display: flex; align-items: center; gap: 10px;
}
.card-section {
  background: #fafafa; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.05);
  border: 1px solid #f0f0f0; margin-bottom: 18px; padding: 24px 18px 10px 18px;
}
.form-section { padding: 0; }
.dialog-footer { display: flex; justify-content: center; gap: 16px; padding-top: 10px; }
</style>
