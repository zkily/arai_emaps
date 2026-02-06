<template>
  <el-dialog v-model="visible" :title="mode === 'add' ? '＋ 新規構成追加' : '🛠️ 構成編集'" width="550px"
    :before-close="handleClose" destroy-on-close :close-on-click-modal="false">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="120px" label-position="left" :disabled="loading">
      <!-- 製品選択 -->
      <el-form-item label="製品" prop="product_id">
        <el-select v-model="form.product_id" placeholder="製品を選択" filterable style="width: 100%"
          :loading="loadingOptions">
          <el-option v-for="p in productOptions" :key="p.id" :label="`${p.product_cd} - ${p.product_name}`"
            :value="p.id">
            <span style="float: left">{{ p.product_cd }}</span>
            <span style="float: right; color: #8492a6; font-size: 13px">{{ p.product_name }}</span>
          </el-option>
        </el-select>
      </el-form-item>

      <!-- 部品選択 -->
      <el-form-item label="部品" prop="component_id">
        <el-select v-model="form.component_id" placeholder="部品を選択" filterable style="width: 100%"
          :loading="loadingOptions">
          <el-option v-for="c in componentOptions" :key="c.id" :label="`${c.component_cd} - ${c.component_name}`"
            :value="c.id">
            <span style="float: left">{{ c.component_cd }}</span>
            <span style="float: right; color: #8492a6; font-size: 13px">{{ c.component_name }}</span>
          </el-option>
        </el-select>
      </el-form-item>

      <!-- 数量 -->
      <el-form-item label="数量" prop="quantity">
        <el-input-number v-model="form.quantity" :min="0.01" :precision="2" :step="1" style="width: 180px" />
      </el-form-item>

      <!-- 単価 -->
      <el-form-item label="単価">
        <el-input-number v-model="form.unit_price" :min="0" :precision="2" :step="10" style="width: 180px">
          <template #prefix>¥</template>
        </el-input-number>
      </el-form-item>

      <!-- 備考 -->
      <el-form-item label="備考">
        <el-input v-model="form.note" type="textarea" :rows="3" placeholder="備考があれば入力してください" maxlength="200"
          show-word-limit />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose" :disabled="loading">キャンセル</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="loading">
          {{ mode === 'add' ? '追加' : '更新' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  createBomItem,
  updateBomItem,
  fetchProductOptions,
  fetchComponentOptions
} from '@/api/master'
// @ts-ignore
import type { BomItem, ProductOption, ComponentOption } from '@/types/master'

const props = defineProps<{
  visible: boolean
  mode: 'add' | 'edit'
  initialData: BomItem | null
}>()

const emit = defineEmits(['update:visible', 'saved'])

// ダイアログ表示状態
const visible = ref(props.visible)
watch(() => props.visible, v => (visible.value = v))
watch(() => visible.value, v => emit('update:visible', v))

// フォーム参照とデータ
const formRef = ref()
const form = ref<BomItem>({
  product_id: 0,
  component_id: 0,
  quantity: 1,
  unit_price: 0,
  note: ''
})

// 状態
const loading = ref(false)
const loadingOptions = ref(false)

// オプションデータ
const productOptions = ref<ProductOption[]>([])
const componentOptions = ref<ComponentOption[]>([])

// バリデーションルール
const rules = {
  product_id: [{ required: true, message: '製品を選択してください', trigger: 'change' }],
  component_id: [{ required: true, message: '部品を選択してください', trigger: 'change' }],
  quantity: [
    { required: true, message: '数量は必須です', trigger: 'blur' },
    { type: 'number' as const, min: 0.01, message: '数量は0より大きい値を入力してください', trigger: 'blur' }
  ]
}

// 初期データの設定
watch(() => props.initialData, (data) => {
  if (data) {
    form.value = { ...data }
  } else {
    form.value = {
      product_id: 0,
      component_id: 0,
      quantity: 1,
      unit_price: 0,
      note: ''
    }
  }
}, { immediate: true })

// 選択肢データの取得
const fetchOptions = async () => {
  loadingOptions.value = true
  try {
    const [products, components] = await Promise.all([
      fetchProductOptions(),
      fetchComponentOptions()
    ])
    productOptions.value = products
    componentOptions.value = components
  } catch (err) {
    ElMessage.error('選択肢データの取得に失敗しました')
  } finally {
    loadingOptions.value = false
  }
}

// 送信処理
const handleSubmit = () => {
  formRef.value?.validate(async (valid: boolean) => {
    if (!valid) return

    loading.value = true
    try {
      if (props.mode === 'add') {
        await createBomItem(form.value)
        ElMessage.success('構成を追加しました')
      } else {
        await updateBomItem(form.value.id!, form.value)
        ElMessage.success('構成を更新しました')
      }
      emit('saved')
      visible.value = false
    } catch (err) {
      ElMessage.error('保存に失敗しました')
    } finally {
      loading.value = false
    }
  })
}

// 閉じる処理
const handleClose = () => {
  if (loading.value) return
  visible.value = false
}

// コンポーネント初期化時に選択肢データを取得
onMounted(fetchOptions)
</script>

<style scoped>
:deep(.el-form-item) {
  margin-bottom: 22px;
}

:deep(.el-select .el-select__tags) {
  max-width: calc(100% - 30px);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 10px;
}

:deep(.el-input-number .el-input__wrapper) {
  padding-left: 11px;
}
</style>
