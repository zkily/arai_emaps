<template>
  <el-dialog v-model="visible" :title="dialogTitle" width="60%" :close-on-click-modal="false">
    <el-form :model="form" :rules="rules" ref="formRef" label-width="140px">
      <!-- 📝 基本情報 -->
      <el-form-item label="部品コード" prop="component_cd">
        <el-input v-model="form.component_cd" maxlength="20" />
      </el-form-item>
      <el-form-item label="部品名称" prop="component_name">
        <el-input v-model="form.component_name" maxlength="100" />
      </el-form-item>
      <el-form-item label="仕様/型">
        <el-input v-model="form.spec_model" maxlength="100" />
      </el-form-item>
      <el-form-item label="単位">
        <el-input v-model="form.unit" maxlength="10" />
      </el-form-item>

      <!-- ⚙️ 調達情報 -->
      <el-form-item label="調達区分" prop="procurement_type">
        <el-select v-model="form.procurement_type" placeholder="選択">
          <el-option label="内製" value="内製" />
          <el-option label="外製" value="外製" />
          <el-option label="購入" value="購入" />
        </el-select>
      </el-form-item>
      <el-form-item label="仕入先">
        <el-select v-model="form.supplier_cd" placeholder="選択" style="width: 100%">
          <el-option v-for="item in supplierOptions" :key="item.cd" :label="`${item.cd}｜${item.name}`"
            :value="item.cd" />
        </el-select>
      </el-form-item>

      <!-- 💴 コスト情報 -->
      <el-form-item label="リードタイム（日）">
        <el-input-number v-model="form.lead_time_days" :min="0" />
      </el-form-item>
      <el-form-item label="単価 (円)">
        <el-input-number v-model="form.unit_price" :min="0" :precision="4" />
      </el-form-item>
      <el-form-item label="外貨単価">
        <el-input-number v-model="form.foreign_currency_price" :min="0" :precision="4" />
      </el-form-item>
      <el-form-item label="収容数">
        <el-input-number v-model="form.lot_size" :min="1" />
      </el-form-item>
      <el-form-item label="決済種類">
        <el-input v-model="form.payment_type" maxlength="20" />
      </el-form-item>

      <!-- その他 -->
      <el-form-item label="終息">
        <el-switch v-model="form.end_of_life_flag" active-value="1" inactive-value="0" />
      </el-form-item>
      <el-form-item label="備考">
        <el-input type="textarea" v-model="form.remarks" :rows="3" />
      </el-form-item>

      <!-- 🚧 子コンポーネント材料 -->
      <ComponentMaterialEditor :component_cd="editData.component_cd" />
      <el-divider>📋 材料設定</el-divider>
      <div style="text-align:center; color: gray">👉 材料設定機能は次のStepで実装</div>
    </el-form>

    <!-- フッター -->
    <template #footer>
      <el-button @click="visible = false">キャンセル</el-button>
      <el-button type="primary" @click="handleSave">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed, onMounted } from 'vue'
import { ElMessage, FormInstance } from 'element-plus'
import request from '@/utils/request'
import { getSupplierOptions } from '@/api/options'
import type { OptionItem } from '@/types/master'
import ComponentMaterialEditor from './ComponentMaterialEditor.vue'


const props = defineProps<{ visible: boolean; editData: any | null }>()
const emit = defineEmits(['update:visible', 'saved'])

const visible = ref(props.visible)
watch(() => props.visible, val => (visible.value = val))
watch(visible, val => emit('update:visible', val))

const supplierOptions = ref<OptionItem[]>([])

const defaultForm = () => ({
  component_cd: '',
  component_name: '',
  spec_model: '',
  unit: '',
  procurement_type: '',
  supplier_cd: '',
  lead_time_days: 0,
  unit_price: 0,
  foreign_currency_price: 0,
  lot_size: 1,
  payment_type: '',
  end_of_life_flag: 0,
  remarks: ''
})

const form = reactive<any>(defaultForm())

const rules = {
  component_cd: [{ required: true, message: '必須', trigger: 'blur' }],
  component_name: [{ required: true, message: '必須', trigger: 'blur' }],
  procurement_type: [{ required: true, message: '必須', trigger: 'change' }]
}

const formRef = ref<FormInstance>()

watch(() => props.editData, val => {
  Object.assign(form, defaultForm())
  if (val) Object.assign(form, val)
})

const dialogTitle = computed(() => (props.editData ? '🔧 部品編集' : '🆕 部品追加'))

const handleSave = () => {
  formRef.value?.validate(async (valid: boolean) => {
    if (!valid) return
    if (props.editData?.id) {
      await request.put(`/api/master/components/${props.editData.id}`, form)
      ElMessage.success('更新しました')
    } else {
      await request.post('/api/master/components', form)
      ElMessage.success('登録しました')
    }
    emit('saved')
    visible.value = false
  })
}

onMounted(async () => {
  supplierOptions.value = await getSupplierOptions()
})
</script>

<style scoped>
.el-dialog {
  max-width: 700px;
}
</style>
